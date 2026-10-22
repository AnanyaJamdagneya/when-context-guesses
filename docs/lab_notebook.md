# Lab Notebook

Project notes. Sections 1–2 contain review, recommendations, and predictions copied from ChatGPT. Sections 4–8 are blank for the author's own entries.

## 1. Dataset review (before any real run)

Which pairs did I keep, change, or replace, and why? Which labels was I unsure about?

_Written 2026-10-22, before any real results. Written by ChatGPT in chat and copied here._

These are a reasonable starting dataset, but the explanation overstates how fair the comparison is. Matching word length and hiding the same positions controls the amount of missing text. It doesn’t make the words equally difficult to recover.

* P04, cash/corn: Paying with corn needs an unusual barter situation. It’s interpretable, but more strained than most examples.
* P05, building/aquarium: An aquarium can be a building, and firefighters entering a burning aquarium makes sense. This may be a relatively weak contrast.
* P10, thirsty/curious: Both work, but “curious” leaves you wondering about what. That makes it slightly less natural.
* The other pairs: Reasonable to keep for an exploratory experiment. Their “predictable” and “unexpected” labels are still your judgments unless you independently measure predictability.

You cannot say an error is caused only by unexpectedness. Word frequency and how strongly the remaining letters identify the answer could also explain it.

**Decision (2026-10-22, before any real results; ChatGPT recommendation copied from chat):**

I recommend keeping all 12 and documenting those weaknesses. Before seeing results, specify that you’ll report:

* The main comparison using all 12 pairs.
* A secondary comparison excluding P04, P05, and P10.

Report both even if they disagree. This preserves the original dataset while checking whether the overall pattern depends on those three pairs. The visible-letter ambiguity remains a limitation in both analyses.

## 2. Predictions (written before seeing real results)

What do I expect to happen, and why? What result would surprise me?

_Written 2026-10-22, before any real results. Written by ChatGPT in chat and copied here._

1. Masked: I predict it will get more predictable words right because the surrounding sentence makes those words easier to guess. Unexpected words might get replaced with something more familiar.
2. Intact: I expect it to preserve most intact sentences, but it might occasionally “correct” unexpected wording even though nothing is missing.
3. Confidence: I think it will sometimes be wrong and confident, especially when its guess fits the context well.
4. Letters: Yes. If the visible letters strongly point to the unexpected word, I expect the gap in accuracy to shrink. A familiar word that does not fit those letters should be easier to rule out.
5. Surprise: I would be most surprised if it repeatedly chose predictable words that contradicted the visible letters and still reported high confidence.

**Update (2026-10-22, after reviewing the letter-pattern counts, still before any results):** this dataset strengthens the caveat in answer 4: I still predict better accuracy for predictable words overall, but distinctive visible letters could shrink or even reverse that difference for some pairs. That would be an interesting result worth reporting.

## 3. Pilot observations

Did the pipeline work? Anything unexpected in the raw responses? (I won't change sentences based on pilot answers. Any pipeline fix gets logged here.)

## 4. Full-run results

## 5. Manual review of errors

## 6. Interpretation

## 7. Mistakes and changes in my approach

## 8. My next question
