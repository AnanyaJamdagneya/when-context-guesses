"""Analyze cached responses and write tables, a plot, and a Markdown report.

The report only describes what happened. Interpretation is left to the author.
"""

import csv
import json
from pathlib import Path

from . import config
from .dataset import CONDITIONS, INPUT_TYPES, Item, dataset_sha256
from .prompts import PROMPT_TEMPLATE, PROMPT_VERSION
from .responses import parse_response_text, visible_character_violations
from .runner import cache_key, load_cached, load_scope_items
from .scoring import exact_sign_test, extract_target, is_exact_match

REVIEW_COLUMNS = ["reviewer_more_conventional_substitution", "reviewer_notes"]


def evaluate_item(item: Item, record: dict | None) -> dict:
    """Score one item. 'failure' is set when there is no usable reconstruction to score."""
    row = {
        "item_id": item.item_id,
        "pair_id": item.pair_id,
        "condition": item.condition,
        "input_type": item.input_type,
        "original": item.original,
        "model_input": item.model_input,
        "target_word": item.target_word,
        "reconstruction": "",
        "recovered_word": "",
        "target_correct": "",
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
    row.update(
        reconstruction=parsed.reconstruction,
        recovered_word=recovered or "",
        target_correct=is_exact_match(recovered, item.target_word),
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


def pair_outcomes(rows: list[dict], input_type: str) -> list[dict]:
    by_pair: dict[str, dict[str, dict]] = {}
    for r in rows:
        if r["input_type"] == input_type:
            by_pair.setdefault(r["pair_id"], {})[r["condition"]] = r
    outcomes = []
    for pair_id in sorted(by_pair):
        p, u = by_pair[pair_id].get("predictable"), by_pair[pair_id].get("unexpected")
        if not p or not u or p["failure"] or u["failure"]:
            outcome = "incomplete (failure)"
        elif p["target_correct"] and u["target_correct"]:
            outcome = "both"
        elif not p["target_correct"] and not u["target_correct"]:
            outcome = "neither"
        elif p["target_correct"]:
            outcome = "predictable only"
        else:
            outcome = "unexpected only"
        outcomes.append(
            {
                "pair_id": pair_id,
                "predictable_target": p["target_word"] if p else "",
                "predictable_recovered": p["recovered_word"] if p else "",
                "unexpected_target": u["target_word"] if u else "",
                "unexpected_recovered": u["recovered_word"] if u else "",
                "outcome": outcome,
            }
        )
    return outcomes


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
    outcomes = {t: pair_outcomes(rows, t) for t in INPUT_TYPES}
    masked = outcomes["masked"]
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
        f"- Items in scope: {len(items)} ({len({i.pair_id for i in items})} pairs x 2 conditions x 2 input types)",
    ]
    if not_run:
        lines += [f"- **{not_run} item(s) have no response yet.** Run the experiment before interpreting."]
    lines += [
        "",
        "Timestamps, raw responses, and errors are in `cache/`, `attempts.jsonl`, and `runs/` in this mode's folder.",
        "",
        "## Target-word exact-match accuracy",
        "",
        "Capitalization and surrounding punctuation are ignored; synonyms and misspellings count as wrong. "
        "Items with an API, refusal, truncation, or parsing failure are excluded from the denominator and counted separately.",
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
        _md_table(masked, ["pair_id", "predictable_target", "predictable_recovered", "unexpected_target",
                           "unexpected_recovered", "outcome"]),
        "",
        f"Pairs where only the predictable version was recovered: **{b}**. "
        f"Only the unexpected version: **{c}**. "
        f"Exact two-sided sign test on these discordant pairs: p = {exact_sign_test(b, c):.3f}. "
        "With so few pairs this test can miss real differences, so a large p-value does not show the conditions are equal.",
        "",
        "## Pair outcomes (intact control)",
        "",
        _md_table(outcomes["intact"], ["pair_id", "predictable_recovered", "unexpected_recovered", "outcome"]),
        "",
        "## Items for manual review",
        "",
        "Every item with a wrong target word, a visible-character violation, or a failure. "
        "A wrong answer is not automatically a 'predictability bias': record your judgment in the "
        "`reviewer_more_conventional_substitution` column of `error_table.csv` (kept when the report is regenerated).",
        "",
        _md_table(errors, ["item_id", "model_input", "reconstruction", "target_word", "recovered_word",
                           "target_correct", "visible_char_violation", "failure", "reviewer_more_conventional_substitution"])
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
