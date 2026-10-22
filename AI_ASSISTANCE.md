# AI Assistance Note

I built this project with help from Claude Code, an AI coding assistant made by Anthropic. This note records who did what, so I can describe the project accurately.

## What I did

- Came up with the question, from misunderstanding a camper's speech while volunteering.
- Wrote the experiment specification: matched sentence pairs, intact vs. half-masked target words, identical mask positions within each pair, exact-match scoring, manual review of every error, and rules against cherry-picking or inventing results.
- Chose which improvements to add (stated uncertainty, letter-pattern counts, repeats).
- Reviewed all 12 sentence pairs and flagged three weaker ones (P04, P05, P10).
- Caught an overclaim in the AI's explanation: pairing controls the amount of missing text, but it does not make the two words equally easy to recover. I also pointed out word frequency as a confound.
- Decided to keep all 12 pairs and set up, before any results, a main analysis (all pairs) and a secondary analysis (without the three flagged pairs).
- Wrote my prediction before the real run.
- Ran the pilot and the full experiment on my own computer with my own API key, and pushed the repository to GitHub.
- Reviewed the results and the per-item confidence breakdown. My own interpretation goes in `docs/lab_notebook.md`.
- Wrote almost all of the Python code (`wcg/`), the tests (`tests/`), and the setup files (`requirements.txt`, `.gitignore`, `.env.example`).

## What Claude Code did

- Wrote some of the Python code.
- Drafted the 12 sentence pairs and their initial "predictable"/"unexpected" labels. I reviewed them afterward.
- Wrote the prompt sent to the model.
- Made design choices I hadn't specified: rounding "half" down, seeding the masks by pair, requiring a dataset freeze before real runs, leaving failures out of accuracy denominators, using an exact sign test, and the default model settings.
- After reading my essay draft, suggested adding stated uncertainty, letter-pattern counts, and repeats, then built the ones I chose.
- Drafted the README, this note, and the lab-notebook template.
- Wrote a separate, labeled prediction of its own (`docs/claude_prediction.md`).


Claude Code did not run the real experiment, did not change any results, and did not write my interpretation.


