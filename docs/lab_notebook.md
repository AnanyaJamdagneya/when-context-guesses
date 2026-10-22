# Lab Notebook

Project notes. Sections 1–2 contain ChatGPT-authored review, recommendations, and predictions copied from chat. Sections 4–8 below are ChatGPT drafts based on the committed results, awaiting Ananya's review; they should not be described as independently written personal reflections.

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

*ChatGPT draft based on the committed full report; pending author review.*

The full report contains 144 scored requests and no API or parsing failures. On masked inputs, predictable targets were correct in 36/36 requests and unexpected targets in 35/36. All 72 intact targets were correct, with no visible-character violations. Using the majority of three repeats, both words were recovered in every pair. The secondary analysis excluding P04, P05, and P10 had 100% accuracy in all four condition/input groups.

For masked predictable words, all 36 answers were correct and confident. For masked unexpected words, 18 were correct and confident, 17 were correct but unsure, and one was wrong and unsure. There were no wrong-and-confident answers.

## 5. Manual review of errors

*ChatGPT review; pending author review.*

The only error was P10-unexpected-masked-r2. The input was “After the long hike, we were very _u_io_s.” The target was “curious,” but the model returned “furious.” It reported that it was not confident and listed “curious” and “dubious” as alternatives.

“Furious” fits every visible letter. This is a different plausible completion, but the report does not establish that it is more conventional in this context. It is therefore not clear evidence of a shift toward predictable wording. The other two repeats recovered “curious.”

## 6. Interpretation

*ChatGPT interpretation; pending author review.*

Predictable targets had slightly higher request-level accuracy, but the entire difference came from one response. There was no difference in majority-based pair recovery, and the secondary analysis had no errors. These results do not establish a general predictability advantage or show that the conditions are equivalent.

The earlier ChatGPT prediction of occasional confident errors was not observed. The one wrong answer was marked unsure and included the target as an alternative. However, one error is too little evidence to judge whether stated uncertainty reliably identifies mistakes. Uncertainty was also common among correct unexpected answers.

Visible letters may have made this task easy. The report's word list contains only one candidate for the P10 predictable pattern and four for its unexpected pattern. That difference could contribute to the error. The task cannot isolate contextual predictability from letter-pattern ambiguity or word familiarity, and it provides no direct evidence about speech or neural decoding.

## 7. Mistakes and changes in the approach

*ChatGPT audit notes; pending author review.*

Matching word length and mask positions was initially described too strongly. It controls how many characters are missing, but does not equalize recovery difficulty. The report documents candidate counts and word frequency, although these measurements do not remove the confounds.

ChatGPT also incorrectly said that “paper” does not fit “_a_er.” It does fit, so that earlier correction was wrong.

Earlier notebook labels described ChatGPT-written predictions and dataset review as the author's own writing. Those labels have been corrected. These new entries are also labeled as AI drafts. No experiment results or pre-specified pair exclusions were changed for this update.

## 8. Next question

*ChatGPT-suggested next experiment; pending author review.*

When the visible letters allow several plausible answers, does changing only the surrounding context change which word the model chooses?

A follow-up could use the same target word and mask in two different sentence contexts, with independent ratings of how expected that target is in each context. This would hold the word, its frequency, and its visible-letter pattern constant. A larger dataset could then test whether context changes reconstruction accuracy and stated uncertainty.
