"""Plan, confirm, and execute a run, caching every response on disk."""

import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .client import FatalAPIError, make_client, utc_now
from .dataset import Item, build_items, dataset_sha256, load_dataset
from .prompts import PROMPT_TEMPLATE, PROMPT_VERSION, build_prompt


def scope_pairs(scope: str) -> tuple[str, ...] | None:
    return config.PILOT_PAIRS if scope == "pilot" else None


def load_scope_items(scope: str) -> list[Item]:
    sentences = load_dataset(config.DATASET_PATH)
    return build_items(sentences, config.SEED, scope_pairs(scope), config.REPEATS)


def cache_key(item: Item, settings: config.ModelSettings) -> str:
    """Identical prompt + identical settings = identical key, so a paid request is never repeated."""
    payload = {
        "settings": settings.as_dict(),
        "prompt_version": PROMPT_VERSION,
        "prompt": build_prompt(item.model_input),
        "repeat": item.repeat,  # repeats share a prompt but are separate requests
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def cache_path(mock: bool, key: str) -> Path:
    return config.mode_dir(mock) / "cache" / f"{key}.json"


def load_cached(mock: bool, key: str) -> dict | None:
    path = cache_path(mock, key)
    return json.loads(path.read_text()) if path.exists() else None


def check_freeze() -> str:
    """Real runs require the dataset to be frozen first, so sentences can't be swapped after seeing results."""
    current = dataset_sha256(config.DATASET_PATH)
    if not config.FREEZE_PATH.exists():
        sys.exit("The dataset is not frozen. Review the pairs, then run: python -m wcg freeze --note \"...\"")
    versions = json.loads(config.FREEZE_PATH.read_text())["versions"]
    if versions[-1]["sha256"] != current:
        sys.exit(
            "data/sentence_pairs.csv changed since it was frozen.\n"
            "If the change is intentional, record why with: python -m wcg freeze --note \"reason\""
        )
    return current


def run(scope: str, mock: bool, settings: config.ModelSettings, assume_yes: bool) -> None:
    dataset_hash = dataset_sha256(config.DATASET_PATH) if mock else check_freeze()
    items = load_scope_items(scope)

    planned = []
    for item in items:
        key = cache_key(item, settings)
        cached = load_cached(mock, key)
        planned.append((item, key, cached is not None and cached["status"] == "ok"))
    to_send = [(item, key) for item, key, done in planned if not done]

    label = "MOCK (no API calls, results are meaningless)" if mock else "REAL API"
    print(f"Mode:      {label}")
    print(f"Scope:     {scope} ({len({i.pair_id for i in items})} pairs x 2 conditions x 2 input types "
          f"x {config.REPEATS} repeats = {len(items)} requests)")
    print(f"Model:     {settings.model}   effort: {settings.effort}   max_tokens: {settings.max_tokens}")
    print(f"Dataset:   sha256 {dataset_hash[:16]}...   seed: {config.SEED}   prompt: {PROMPT_VERSION}")
    print(f"Cached:    {len(items) - len(to_send)}")
    print(f"Planned requests to send now: {len(to_send)}")
    if not to_send:
        print("Nothing to send. Run the report command to analyze.")
        return
    if not assume_yes and input("Proceed? [y/N] ").strip().lower() != "y":
        print("Cancelled; nothing was sent.")
        return

    client = make_client(settings, mock)
    started = utc_now()
    out_dir = config.mode_dir(mock)
    (out_dir / "cache").mkdir(parents=True, exist_ok=True)
    attempts_log = out_dir / "attempts.jsonl"
    counts = {"ok": 0, "api_error": 0}
    stopped_early = None

    for n, (item, key) in enumerate(to_send, start=1):
        try:
            record = client.send(build_prompt(item.model_input))
        except FatalAPIError as e:
            stopped_early = str(e)
            print(f"\nStopping: {e}")
            break
        record.update({"item": asdict(item), "cache_key": key, "settings": settings.as_dict(),
                       "prompt_version": PROMPT_VERSION, "dataset_sha256": dataset_hash, "seed": config.SEED})
        with open(attempts_log, "a") as f:
            f.write(json.dumps(record) + "\n")
        # Only successful API calls are cached. API errors are logged and retried on the
        # next run; a successful call is never re-sampled, even if its answer is wrong.
        if record["status"] == "ok":
            cache_path(mock, key).write_text(json.dumps(record, indent=2))
        counts[record["status"]] += 1
        print(f"[{n}/{len(to_send)}] {item.item_id}: {record['status']}")

    manifest = {
        "mode": "mock" if mock else "real",
        "scope": scope,
        "started_at": started,
        "finished_at": utc_now(),
        "settings": settings.as_dict(),
        "seed": config.SEED,
        "repeats": config.REPEATS,
        "dataset_sha256": dataset_hash,
        "prompt_version": PROMPT_VERSION,
        "prompt_template": PROMPT_TEMPLATE,
        "items_in_scope": len(items),
        "requests_attempted": sum(counts.values()),
        "counts": counts,
        "stopped_early": stopped_early,
        "cache_keys": {item.item_id: key for item, key, _ in planned},
    }
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (runs_dir / f"{stamp}_{scope}.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone: {counts}. Manifest saved in {runs_dir.relative_to(config.ROOT)}/")


def freeze(note: str) -> None:
    sha = dataset_sha256(config.DATASET_PATH)
    load_dataset(config.DATASET_PATH)  # refuse to freeze an invalid dataset
    data = json.loads(config.FREEZE_PATH.read_text()) if config.FREEZE_PATH.exists() else {"versions": []}
    if data["versions"] and data["versions"][-1]["sha256"] == sha:
        print("Dataset already frozen at this version.")
        return
    data["versions"].append({"version": len(data["versions"]) + 1, "sha256": sha, "frozen_at": utc_now(), "note": note})
    config.FREEZE_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Froze dataset version {len(data['versions'])} (sha256 {sha[:16]}...).")
