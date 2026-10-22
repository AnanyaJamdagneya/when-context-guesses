"""Analyze cached responses and write tables, a plot, and a Markdown report.

The report only describes what happened. Interpretation is left to the author.
"""

import csv
import json
from pathlib import Path

from . import config
from .dataset import CONDITIONS, INPUT_TYPES, Item, dataset_sha256
from .masking import mask_word
from .patterns import english_words, pattern_info
from .prompts import PROMPT_TEMPLATE, PROMPT_VERSION
from .responses import parse_response_text, visible_character_violations
from .runner import cache_key, load_cached, load_scope_items
from .scoring import exact_sign_test, extract_target, is_exact_match, normalize_word

REVIEW_COLUMNS = ["reviewer_more_conventional_substitution", "reviewer_notes"]


def evaluate_item(item: Item, record: dict | None) -> dict:
    """Score one item. 'failure' is set when there is no usable reconstruction to score."""
    row = {
        "item_id": item.item_id,
        "base_id": item.base_id,
        "repeat": item.repeat,
        "pair_id": item.pair_id,
        "condition": item.condition,
        "input_type": item.input_type,
        "original": item.original,
        "model_input": item.model_input,
        "target_word": item.target_word,
        "reconstruction": "",
        "recovered_word": "",
        "target_correct": "",
        "confident": "",
        "other_possible_words": "",
        "target_in_other_words": "",
        "visible_char_violation": "",
        "violation_detail": "",
        "failure": "",
        "failure_detail": "",
    }
    if record is None:
        row["failure"] = "not_run"
        return row
    if record["status"] != "ok":
        row["failure"], row["failure_detail"] = "api_error", record.get("error", "")
        return row
    if record.get("stop_reason") == "refusal":
        row["failure"], row["failure_detail"] = "refusal", json.dumps(record.get("stop_details"))
        return row
    if record.get("stop_reason") == "max_tokens":
        row["failure"], row["failure_detail"] = "truncated", "response hit max_tokens"
        return row

    parsed = parse_response_text(record.get("raw_text"))
    if parsed.error:
        row["failure"], row["failure_detail"] = "parse_error", parsed.error
        return row

    recovered = extract_target(parsed.reconstruction, item.target_position)
    violations = visible_character_violations(item.model_input, parsed.reconstruction)
    others = [normalize_word(w) for w in parsed.other_possible_words]
    row.update(
        reconstruction=parsed.reconstruction,
        recovered_word=recovered or "",
        target_correct=is_exact_match(recovered, item.target_word),
        confident=parsed.confident,
        other_possible_words=", ".join(others),
        target_in_other_words=item.target_word.lower() in others,
        visible_char_violation=bool(violations),
        violation_detail="; ".join(violations[:3]),
    )
    return row


def accuracy_table(rows: list[dict]) -> list[dict]:
    """Exact-match accuracy per input type x condition, plus intact/masked totals."""
    groups = [(t, c) for t in INPUT_TYPES for c in CONDITIONS] + [(t, "all") for t in INPUT_TYPES]
    table = []
    for input_type, condition in groups:
        subset = [r for r in rows if r["input_type"] == input_type and condition in ("all", r["condition"])]
        usable = [r for r in subset if not r["failure"]]
        correct = sum(1 for r in usable if r["target_correct"] is True)
        table.append(
            {
                "input_type": input_type,
                "condition": condition,
                "correct": correct,
                "scored": len(usable),
                "failures": len(subset) - len(usable),
                "percent": (100 * correct / len(usable)) if usable else None,
            }
        )
    return table


def item_stability(rows: list[dict]) -> dict[str, dict]:
    """Collapse repeats: how many of an item's scored repeats recovered the target.

    An item counts as "recovered" when the target was exact in more than half of its
    scored repeats (2 or 3 out of 3). This rule was fixed before any real run.
    """
    stability: dict[str, dict] = {}
    for r in rows:
        s = stability.setdefault(r["base_id"], {"correct": 0, "scored": 0, "rows": []})
        s["rows"].append(r)
        if not r["failure"]:
            s["scored"] += 1
            s["correct"] += r["target_correct"] is True
    for s in stability.values():
        s["recovered"] = None if s["scored"] == 0 else s["correct"] * 2 > s["scored"]
        s["recovered_words"] = ", ".join(r["recovered_word"] or "-" for r in s["rows"])
    return stability


def pair_outcomes(stability: dict[str, dict], pair_ids: list[str], input_type: str) -> list[dict]:
    outcomes = []
    for pair_id in pair_ids:
        p = stability.get(f"{pair_id}-predictable-{input_type}")
        u = stability.get(f"{pair_id}-unexpected-{input_type}")
        if not p or not u or p["recovered"] is None or u["recovered"] is None:
            outcome = "incomplete (failure)"
        elif p["recovered"] and u["recovered"]:
            outcome = "both"
        elif not p["recovered"] and not u["recovered"]:
            outcome = "neither"
        elif p["recovered"]:
            outcome = "predictable only"
        else:
            outcome = "unexpected only"
        outcomes.append(
            {
                "pair_id": pair_id,
                "predictable_target": p["rows"][0]["target_word"] if p else "",
                "predictable_answers": p["recovered_words"] if p else "",
                "predictable_correct": f"{p['correct']}/{p['scored']}" if p else "",
                "unexpected_target": u["rows"][0]["target_word"] if u else "",
                "unexpected_answers": u["recovered_words"] if u else "",
                "unexpected_correct": f"{u['correct']}/{u['scored']}" if u else "",
                "outcome": outcome,
            }
        )
    return outcomes


def uncertainty_table(rows: list[dict]) -> list[dict]:
    """For masked inputs: did the model's stated confidence line up with being right?"""
    table = []
    for condition in CONDITIONS:
        usable = [r for r in rows if r["input_type"] == "masked" and r["condition"] == condition and not r["failure"]]
        wrong = [r for r in usable if r["target_correct"] is False]
        table.append(
            {
                "condition": condition,
                "right_and_confident": sum(r["target_correct"] is True and r["confident"] is True for r in usable),
                "right_but_unsure": sum(r["target_correct"] is True and r["confident"] is False for r in usable),
                "wrong_but_confident": sum(r["target_correct"] is False and r["confident"] is True for r in wrong),
                "wrong_and_unsure": sum(r["target_correct"] is False and r["confident"] is False for r in wrong),
                "wrong_but_target_listed_as_alternative": f"{sum(r['target_in_other_words'] is True for r in wrong)}/{len(wrong)}",
            }
        )
    return table


def pattern_table(items: list[Item], stability: dict[str, dict]) -> list[dict]:
    words = english_words(config.WORDLIST_SIZE)
    table, seen = [], set()
    for item in items:
        if item.input_type != "masked" or item.base_id in seen:
            continue
        seen.add(item.base_id)
        info = pattern_info(mask_word(item.target_word.lower(), item.mask_positions), item.target_word, words)
        s = stability.get(item.base_id)
        table.append(
            {
                "item": item.base_id.removesuffix("-masked"),
                "target_word": item.target_word,
                "word_frequency_zipf": info["target_zipf_frequency"],
                "pattern": info["pattern"],
                "words_that_fit": info["candidate_count"],
                "target_frequency_rank": info["target_frequency_rank"] or "not in list",
                "most_frequent_fits": ", ".join(info["most_frequent_candidates"]),
                "model_correct": f"{s['correct']}/{s['scored']}" if s else "",
            }
        )
    return table


def secondary_analysis(rows: list[dict], outcomes: list[dict]) -> str:
    """The same accuracy and pair-outcome summary, without the pairs flagged in review."""
    excluded = set(config.SECONDARY_EXCLUDED_PAIRS)
    kept_rows = [r for r in rows if r["pair_id"] not in excluded]
    kept_outcomes = [o for o in outcomes if o["pair_id"] not in excluded]
    table = accuracy_table(kept_rows)
    b = sum(o["outcome"] == "predictable only" for o in kept_outcomes)
    c = sum(o["outcome"] == "unexpected only" for o in kept_outcomes)
    counts = {k: sum(o["outcome"] == k for o in kept_outcomes)
              for k in ("both", "neither", "predictable only", "unexpected only", "incomplete (failure)")}
    return "\n".join([
        f"Excludes {', '.join(sorted(excluded))} ({len(kept_outcomes)} pairs remain). "
        "This was specified before any real results and is reported regardless of whether it agrees with the main analysis.",
        "",
        _md_table(
            [{**r, "accuracy": f"{r['correct']}/{r['scored']} ({_pct(r)})"} for r in table],
            ["input_type", "condition", "accuracy", "failures"],
        ),
        "",
        "Masked pair outcomes: " + ", ".join(f"{k}: {v}" for k, v in counts.items()) + ". "
        f"Exact two-sided sign test on discordant pairs ({b} vs {c}): p = {exact_sign_test(b, c):.3f}.",
    ])


def needs_review(row: dict) -> bool:
    return bool(row["failure"]) or row["target_correct"] is False or row["visible_char_violation"] is True


def load_existing_review(path: Path) -> dict[str, dict]:
    """Keep the author's manual notes when the report is regenerated."""
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {r["item_id"]: {c: r.get(c, "") for c in REVIEW_COLUMNS} for r in csv.DictReader(f)}


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def plot_accuracy(table: list[dict], path: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"predictable": "#2a78d6", "unexpected": "#eb6834"}
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=150)
    width = 0.36
    for offset, condition in ((-width / 2, "predictable"), (width / 2, "unexpected")):
        for x, input_type in enumerate(INPUT_TYPES):
            cell = next(r for r in table if r["input_type"] == input_type and r["condition"] == condition)
            height = cell["percent"] or 0
            ax.bar(x + offset, height, width - 0.03, color=colors[condition],
                   label=condition if x == 0 else None)
            ax.text(x + offset, height + 1.5, f"{cell['correct']}/{cell['scored']}",
                    ha="center", va="bottom", fontsize=9, color="#0b0b0b")
    ax.set_xticks(range(len(INPUT_TYPES)), [f"{t} input" for t in INPUT_TYPES])
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 25))
    ax.set_ylabel("Target word exactly recovered (%)", color="#52514e")
    ax.set_title(title, fontsize=11, loc="left")
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, colors="#52514e")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncols=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _md_cell(value) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _md_table(rows: list[dict], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(_md_cell(r.get(c, "")) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def _pct(cell: dict) -> str:
    return "n/a" if cell["percent"] is None else f"{cell['percent']:.0f}%"


def build_report(scope: str, mock: bool, settings: config.ModelSettings) -> Path:
    items = load_scope_items(scope)
    rows = [evaluate_item(item, load_cached(mock, cache_key(item, settings))) for item in items]
    out_dir = config.mode_dir(mock) / f"report_{scope}"
    out_dir.mkdir(parents=True, exist_ok=True)

    table = accuracy_table(rows)
    stability = item_stability(rows)
    pair_ids = sorted({i.pair_id for i in items})
    outcomes = {t: pair_outcomes(stability, pair_ids, t) for t in INPUT_TYPES}
    masked = outcomes["masked"]
    uncertainty = uncertainty_table(rows)
    patterns = pattern_table(items, stability)
    intact_usable = [r for r in rows if r["input_type"] == "intact" and not r["failure"]]
    intact_unsure = sum(r["confident"] is False for r in intact_usable)
    b = sum(o["outcome"] == "predictable only" for o in masked)
    c = sum(o["outcome"] == "unexpected only" for o in masked)

    review_path = out_dir / "error_table.csv"
    existing = load_existing_review(review_path)
    errors = [{**r, **existing.get(r["item_id"], {c: "" for c in REVIEW_COLUMNS})} for r in rows if needs_review(r)]
    columns = list(rows[0].keys())
    write_csv(out_dir / "all_items.csv", rows, columns)
    write_csv(review_path, errors, columns + REVIEW_COLUMNS)
    write_csv(out_dir / "pair_outcomes.csv", [{"input_type": t, **o} for t in INPUT_TYPES for o in outcomes[t]],
              ["input_type"] + list(masked[0].keys()))
    write_csv(out_dir / "pattern_difficulty.csv", patterns, list(patterns[0].keys()))

    label = "MOCK RESULTS (pipeline test only; not a language model)" if mock else "Real model results"
    plot_accuracy(table, out_dir / "accuracy.png", f"{label}\n{scope} run, model: {settings.model}")

    not_run = sum(r["failure"] == "not_run" for r in rows)
    lines = []
    if mock:
        lines += ["> **MOCK MODE. These numbers come from a placeholder that fills every blank with 'e'.",
                  "> They test the pipeline and say nothing about any language model.**", ""]
    lines += [
        f"# When Context Guesses: {scope} results",
        "",
        f"- Mode: {'mock' if mock else 'real API'}",
        f"- Model: `{settings.model}` (effort `{settings.effort}`, max_tokens {settings.max_tokens})",
        f"- Dataset sha256: `{dataset_sha256(config.DATASET_PATH)}`",
        f"- Seed: {config.SEED}; prompt version: {PROMPT_VERSION}",
        f"- Requests in scope: {len(items)} ({len(pair_ids)} pairs x 2 conditions x 2 input types x {config.REPEATS} repeats)",
    ]
    if not_run:
        lines += [f"- **{not_run} item(s) have no response yet.** Run the experiment before interpreting."]
    lines += [
        "",
        "Timestamps, raw responses, and errors are in `cache/`, `attempts.jsonl`, and `runs/` in this mode's folder.",
        "",
        "## Main analysis: target-word exact-match accuracy (all pairs)",
        "",
        "Capitalization and surrounding punctuation are ignored; synonyms and misspellings count as wrong. "
        "Counts are over individual requests (each repeat counts once). "
        "Requests with an API, refusal, truncation, or parsing failure are excluded from the denominator and counted separately.",
        "",
        _md_table(
            [{**r, "accuracy": f"{r['correct']}/{r['scored']} ({_pct(r)})"} for r in table],
            ["input_type", "condition", "accuracy", "failures"],
        ),
        "",
        "![Accuracy plot](accuracy.png)",
        "",
        "## Pair outcomes (masked input)",
        "",
        f"An item counts as recovered when the target was exact in more than half of its {config.REPEATS} repeats. "
        "The answers column lists the word given in each repeat.",
        "",
        _md_table(masked, ["pair_id", "predictable_target", "predictable_answers", "predictable_correct",
                           "unexpected_target", "unexpected_answers", "unexpected_correct", "outcome"]),
        "",
        f"Pairs where only the predictable version was recovered: **{b}**. "  # majority across repeats
        f"Only the unexpected version: **{c}**. "
        f"Exact two-sided sign test on these discordant pairs: p = {exact_sign_test(b, c):.3f}. "
        "With so few pairs this test can miss real differences, so a large p-value does not show the conditions are equal.",
        "",
        "## Secondary analysis: excluding pairs flagged in review",
        "",
        secondary_analysis(rows, masked),
        "",
        "The visible-letter and word-frequency differences described below remain limitations in both analyses.",
        "",
        "## Pair outcomes (intact control)",
        "",
        _md_table(outcomes["intact"], ["pair_id", "predictable_answers", "unexpected_answers", "outcome"]),
        "",
        f"Intact requests where the model said it was not confident: {intact_unsure}/{len(intact_usable)}.",
        "",
        "## Did the model know when it might be wrong? (masked input)",
        "",
        "The model reported `confident` (true/false) and `other_possible_words` with every answer. "
        "This is the model's own statement, not a measured probability.",
        "",
        _md_table(uncertainty, list(uncertainty[0].keys())),
        "",
        "## Word familiarity and letter patterns",
        "",
        f"Number of words among the {config.WORDLIST_SIZE:,} most common English words (wordfreq list) that fit each "
        "blank pattern, ignoring the sentence. Rank 1 means the target is the most common word that fits. "
        "`word_frequency_zipf` is how common the target word is in general (about 3 = uncommon, 5 = very common). "
        "The list includes some names and abbreviations, so counts are approximate.",
        "",
        _md_table(patterns, list(patterns[0].keys())),
        "",
        "## Items for manual review",
        "",
        "Every item with a wrong target word, a visible-character violation, or a failure. "
        "A wrong answer is not automatically a 'predictability bias': record your judgment in the "
        "`reviewer_more_conventional_substitution` column of `error_table.csv` (kept when the report is regenerated).",
        "",
        _md_table(errors, ["item_id", "model_input", "reconstruction", "target_word", "recovered_word",
                           "target_correct", "confident", "other_possible_words", "visible_char_violation", "failure",
                           "reviewer_more_conventional_substitution"])
        if errors else "_No items need review._",
        "",
        "## Failures and violations",
        "",
        f"- Visible-character violations: {sum(r['visible_char_violation'] is True for r in rows)}",
        f"- API errors: {sum(r['failure'] == 'api_error' for r in rows)}",
        f"- Refusals: {sum(r['failure'] == 'refusal' for r in rows)}",
        f"- Truncated responses: {sum(r['failure'] == 'truncated' for r in rows)}",
        f"- Parsing failures: {sum(r['failure'] == 'parse_error' for r in rows)}",
        "",
        "## Prompt (identical for every item)",
        "",
        "```text",
        PROMPT_TEMPLATE,
        "```",
        "",
        "## Interpretation",
        "",
        "This report is generated and contains no conclusions. The author's interpretation is in "
        "`docs/lab_notebook.md`. Twelve author-labeled pairs and one run of one model cannot establish a general "
        "finding, and this text task does not transfer directly to neural speech decoding.",
        "",
    ]
    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
