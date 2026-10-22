# Lab Notebook

My own notes, in my own words. The AI assistant created this blank template; everything below the headings is mine.

## 1. Dataset review (before any real run)

Which pairs did I keep, change, or replace, and why? Which labels was I unsure about?

## 2. Predictions (written before seeing real results)

What do I expect to happen, and why? What result would surprise me?

_Written 2026-10-22, before any real results. Typed by me in chat and pasted here verbatim by Claude Code._

1. Masked: I predict it will get more predictable words right because the surrounding sentence makes those words easier to guess. Unexpected words might get replaced with something more familiar.
2. Intact: I expect it to preserve most intact sentences, but it might occasionally “correct” unexpected wording even though nothing is missing.
3. Confidence: I think it will sometimes be wrong and confident, especially when its guess fits the context well.
4. Letters: Yes. If the visible letters strongly point to the unexpected word, I expect the gap in accuracy to shrink. A familiar word that does not fit those letters should be easier to rule out.
5. Surprise: I would be most surprised if it repeatedly chose predictable words that contradicted the visible letters and still reported high confidence.

## 3. Pilot observations

Did the pipeline work? Anything unexpected in the raw responses? (I won't change sentences based on pilot answers. Any pipeline fix gets logged here.)

## 4. Full-run results

The numbers, copied from `results/real/report_full/report.md`.

## 5. Manual review of errors

For each error: did the model substitute a more conventional word, a different plausible word, or something else? What made it hard to decide?

## 6. Interpretation

What can and can't I conclude from 12 pairs and one model run?

## 7. Mistakes and changes in my approach

## 8. My next question
