"""Command-line entry point: python -m wcg <command>."""

import argparse
import sys

from . import config
from .dataset import DatasetError, build_items, load_dataset


def show_dataset() -> None:
    from .masking import mask_word
    from .patterns import english_words, pattern_info

    sentences = load_dataset(config.DATASET_PATH)
    words = english_words(config.WORDLIST_SIZE)
    print(f"Dataset OK: {len(sentences)} sentences. Masked inputs with seed {config.SEED}.")
    print("'fits' = how many common English words match the visible letters, ignoring context.\n")
    for item in build_items(sentences, config.SEED):
        if item.input_type == "masked":
            info = pattern_info(mask_word(item.target_word.lower(), item.mask_positions), item.target_word, words)
            print(f"{item.pair_id} {item.condition:<12} {item.model_input:<58} "
                  f"target: {item.target_word:<9} fits: {info['candidate_count']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m wcg", description="When Context Guesses experiment")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="validate the dataset and print every masked input")
    freeze = sub.add_parser("freeze", help="record the reviewed dataset version before real runs")
    freeze.add_argument("--note", required=True, help="why this version is being frozen")

    for name, text in (("pilot", f"run the 3-pair pilot ({', '.join(config.PILOT_PAIRS)})"),
                       ("full", "run all pairs"),
                       ("report", "analyze cached responses and write the report")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--mock", action="store_true", help="use the mock model (separate results folder)")
        p.add_argument("--model", help=f"model ID (default {config.DEFAULT_MODEL} or $WCG_MODEL)")
        p.add_argument("--effort", help=f"effort level (default {config.DEFAULT_EFFORT} or $WCG_EFFORT)")
        if name == "report":
            p.add_argument("--scope", choices=["pilot", "full"], default="full")
        else:
            p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")

    args = parser.parse_args(argv)
    try:
        if args.command == "show":
            show_dataset()
        elif args.command == "freeze":
            from .runner import freeze as do_freeze

            do_freeze(args.note)
        elif args.command in ("pilot", "full"):
            from .runner import run

            run(args.command, args.mock, config.load_settings(args.model, args.effort, args.mock), args.yes)
        elif args.command == "report":
            from .report import build_report

            path = build_report(args.scope, args.mock, config.load_settings(args.model, args.effort, args.mock))
            print(f"Report written to {path.relative_to(config.ROOT)}")
    except DatasetError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
