# When Context Guesses

A small, exploratory experiment: **when the same amount of a word is missing, does a language model reconstruct predictable sentences more accurately than grammatical but unexpected ones?** And a follow-up: **when it guesses wrong, does it know it might be wrong?**

## Why

While volunteering at a camp, I misunderstood a camper whose speech was affected by dysarthria after a stroke. I had guessed the word I expected instead of the word he said. That made me wonder whether language models, which are increasingly used to help decode speech, do the same thing: fill gaps faithfully, or swap unexpected wording for more predictable wording.

**What this project is not.** It uses synthetic written sentences with letters replaced by underscores. It is not a neural speech decoder, not a simulation of dysarthria, and not evidence about how any clinical speech device performs.

## Method

**Dataset** (`data/sentence_pairs.csv`). 12 matched pairs of short sentences. In each pair the two sentences are identical except for one target word:

| condition | example |
|---|---|
| predictable | I brushed my **teeth** before going to bed. |
| unexpected | I brushed my **horse** before going to bed. |

- Target words in a pair have the same length, so identical letter positions can be hidden.
- "Predictable" and "unexpected" are **my own subjective labels**, not measured probabilities.
- The dataset is frozen (`data/dataset_freeze.json` records its SHA-256 hash) before any real run, and real runs refuse to start if the file has changed. Any later change must be logged with a reason.

**Inputs.** Every sentence is sent twice:

1. **Intact** (control): the full sentence.
2. **Masked**: half of the target word's letters (rounded down) replaced with `_`. Positions come from a fixed seed combined with the pair ID, so both sentences in a pair have the same hidden positions. Nothing else in the sentence changes.

Example (P01): `I brushed my te_t_ before going to bed.` vs `I brushed my ho_s_ before going to bed.`

**Model requests.** One prompt template is used for every item (see `wcg/prompts.py`). The model is asked to reconstruct the sentence and keep every visible character. It returns JSON, enforced with the API's structured-output setting:

```json
{"reconstruction": "...", "confident": true, "other_possible_words": ["..."]}
```

Each request is separate, with no conversation history. The model never sees the original sentence, the condition label, or the paired sentence. Every item is sent **3 times** as independent requests, because current Claude models don't accept a temperature setting and answers can vary. 12 pairs × 2 conditions × 2 input types × 3 repeats = **144 requests**.

**Scoring** (`wcg/scoring.py`, `wcg/responses.py`).
- *Exact match*: the word at the target position, ignoring capitalization and surrounding punctuation, must be spelled exactly like the target. Synonyms count as wrong.
- *Visible-character violation*: the reconstruction changed a visible character, changed the length, or filled a blank with a non-letter. This is recorded separately from correctness.
- *Failures* (API error, refusal, truncation, unparseable output) are counted separately and left out of accuracy denominators.
- *Repeats*: accuracy tables count every request. For pair outcomes, an item counts as "recovered" when the target was exact in more than half of its scored repeats (2 or 3 of 3). This rule was fixed before any real run.
- *Pair outcomes*: for each pair, whether **both**, **neither**, **predictable only**, or **unexpected only** was recovered.
- *Stated uncertainty*: for masked inputs, a breakdown of right/wrong × confident/unsure, and how often a wrong answer still listed the true word as an alternative. This is the model's own statement, not a measured probability.
- *Letter-pattern difficulty*: for each masked word, how many of the 50,000 most common English words (from the `wordfreq` frequency list) fit the visible letters, ignoring the sentence. This shows how much the letters alone narrow the answer, separately from context.
- *Sign test*: an exact two-sided test on the pairs where only one version was recovered. It was chosen before running. With 12 pairs it has very little statistical power, so it is descriptive only.
- *Manual review*: every error is listed in `error_table.csv` with an empty column where I record whether the error looks like a substitution of a more conventional word. Errors are **not** automatically labeled as "predictability bias".

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...   # never commit this; .env is git-ignored
```

Optional: `WCG_MODEL` and `WCG_EFFORT` (or `--model` / `--effort`) override the defaults in `wcg/config.py`.

## Running

```bash
python -m wcg show                      # validate the dataset and print every masked input
python -m pytest                        # tests for masking, scoring, response handling

python -m wcg pilot --mock              # test the whole pipeline with no API calls
python -m wcg report --mock --scope pilot

python -m wcg freeze --note "Reviewed pairs before any real run"   # once, after reviewing the dataset
python -m wcg pilot                     # 3-pair pilot (36 real requests)
python -m wcg full                      # all 12 pairs (reuses cached pilot responses)
python -m wcg report                    # tables, plot, and Markdown report
```

Each run prints how many requests it plans to send and asks for confirmation. Responses are cached in `results/real/cache/`, so rerunning the report never repeats paid requests. Every attempt (including errors) is logged in `results/real/attempts.jsonl`, and each run writes a manifest in `results/real/runs/` with the dataset hash, seed, prompt, model settings, and timestamps.

Mock results go to `results/mock/` (git-ignored). The mock fills every blank with the letter "e". It is not a language model and its numbers mean nothing.

## Model and settings

| setting | value |
|---|---|
| provider | Anthropic Messages API (`anthropic` Python SDK) |
| model | `claude-opus-5-5` (default; the real run's manifest records the exact model used) |
| effort | `medium` |
| max_tokens | 16000 |
| output format | JSON schema `{"reconstruction": string, "confident": boolean, "other_possible_words": [string]}` |
| repeats | 3 independent requests per item |
| temperature | not settable on current Claude models, so answers can vary. The 3 repeats show how much, and all of them are cached and reported. |

The model reasons internally before answering (its thinking cannot be turned off on this model). Refusal fallbacks to other models are deliberately **not** enabled, so every response comes from the configured model.

## Results

_No real results yet. This section will be filled in after the frozen dataset is run, using `results/real/report_full/report.md`._

## Limitations

- **Small and subjective.** 12 pairs written and labeled by one person. The "predictable" and "unexpected" labels were not measured.
- **One model, one run, one prompt.** Outputs are not deterministic. A different model, prompt, or day could give different answers.
- **The visible letters differ between pairs.** The hidden positions match, but the letters left showing are different (`te_t_` vs `ho_s_`). Some patterns allow only one common word (`u__r__la`) while others allow dozens (`_a_er`), so differences in accuracy may come from letter patterns rather than predictability. The pattern-difficulty table measures this but cannot remove it.
- **Self-reported confidence is not calibration.** A model saying "not confident" is different from the probability scores a real decoder produces.
- **Exact match is strict.** It cannot tell a reasonable alternative from an unreasonable one; that is what the manual review column is for.
- **Text is not speech.** Written blanks with known length and known positions are very different from noisy audio or neural signals. These results cannot be transferred directly to speech decoding or to people with dysarthria.

## Repository layout

```
data/sentence_pairs.csv     editable dataset
wcg/                        experiment code (masking, prompts, API client, runner, scoring, report)
tests/                      pytest tests
results/real/               real responses, run manifests, and reports (committed)
docs/lab_notebook.md        my own notes, decisions, and interpretation
AI_ASSISTANCE.md            what the AI assistant did vs. what I did
```

## AI assistance

This project was built with help from Claude Code. See [AI_ASSISTANCE.md](AI_ASSISTANCE.md) for an exact account.
