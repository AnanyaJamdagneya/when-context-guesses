# AI Assistance Note

This project was built with Claude Code (an AI coding assistant made by Anthropic). This file records what the assistant produced and what I did, so the project can be described accurately.

## What I contributed (before the AI was involved)

- The original observation from volunteering, and the research question.
- The experiment specification: matched pairs, intact vs. half-masked target words, identical mask positions within pairs, exact-match scoring, the requirement for manual review of errors, and the rules against cherry-picking and invented results.

## What Claude Code generated (first session)

- All Python code in `wcg/` and `tests/`, plus `requirements.txt`, `.gitignore`, and `.env.example`.
- The **first draft** of all 12 sentence pairs in `data/sentence_pairs.csv`, including the initial predictable/unexpected labels.
- The prompt wording in `wcg/prompts.py`.
- Design choices I had not specified: rounding "half" down, seeding masks with the pair ID, requiring a dataset freeze before real runs, excluding failures from accuracy denominators, using an exact sign test, and the default model settings.
- The first drafts of `README.md`, this file, and the template in `docs/lab_notebook.md`.

The assistant did not run the real experiment and did not write any results or conclusions.

## Contribution log

Add a row whenever either of us changes something meaningful. Be specific; this is the record I'll rely on when I describe the project.

| date | who | what changed | why |
|---|---|---|---|
| 2026-10-22 | Claude Code | Generated code, tests, docs, and draft dataset | Initial build from my specification |
| | me | | |
