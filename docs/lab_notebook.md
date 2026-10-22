# Lab Notebook

My own notes, in my own words. The AI assistant created this blank template; everything below the headings is mine.

## 1. Dataset review (before any real run)

Which pairs did I keep, change, or replace, and why? Which labels was I unsure about?

_Written 2026-10-22, before any real results. Typed by me in chat and pasted here verbatim by Claude Code._

These are a reasonable starting dataset, but the explanation overstates how fair the comparison is. Matching word length and hiding the same positions controls the amount of missing text. It doesn’t make the words equally difficult to recover.

* P04, cash/corn: Paying with corn needs an unusual barter situation. It’s interpretable, but more strained than most examples.
* P05, building/aquarium: An aquarium can be a building, and firefighters entering a burning aquarium makes sense. This may be a relatively weak contrast.
* P10, thirsty/curious: Both work, but “curious” leaves you wondering about what. That makes it slightly less natural.
* The other pairs: Reasonable to keep for an exploratory experiment. Their “predictable” and “unexpected” labels are still your judgments unless you independently measure predictability.

You cannot say an error is caused only by unexpectedness. Word frequency and how strongly the remaining letters identify the answer could also explain it.

**Decision (2026-10-22, before any real results; typed by me in chat and pasted verbatim):**

I recommend keeping all 12 and documenting those weaknesses. Before seeing results, specify that you’ll report:

* The main comparison using all 12 pairs.
* A secondary comparison excluding P04, P05, and P10.

Report both even if they disagree. This preserves the original dataset while checking whether the overall pattern depends on those three pairs. The visible-letter ambiguity remains a limitation in both analyses.

## 2. Predictions (written before seeing real results)

What do I expect to happen, and why? What result would surprise me?

_Written 2026-10-22, before any real results. Typed by me in chat and pasted here verbatim by Claude Code._

1. Masked: I predict it will get more predictable words right because the surrounding sentence makes those words easier to guess. Unexpected words might get replaced with something more familiar.
2. Intact: I expect it to preserve most intact sentences, but it might occasionally “correct” unexpected wording even though nothing is missing.
3. Confidence: I think it will sometimes be wrong and confident, especially when its guess fits the context well.
4. Letters: Yes. If the visible letters strongly point to the unexpected word, I expect the gap in accuracy to shrink. A familiar word that does not fit those letters should be easier to rule out.
5. Surprise: I would be most surprised if it repeatedly chose predictable words that contradicted the visible letters and still reported high confidence.

**Update (2026-10-22, after reviewing the letter-pattern counts, still before any results):** this dataset strengthens the caveat in answer 4: I still predict better accuracy for predictable words overall, but distinctive visible letters could shrink or even reverse that difference for some pairs. That would be an interesting result worth reporting.

## 3. Pilot observations

Did the pipeline work? Anything unexpected in the raw responses? (I won't change sentences based on pilot answers. Any pipeline fix gets logged here.)

## 4. Full-run results

The numbers, copied from `results/real/report_full/report.md`.

_Written by me after the full run. Typed in chat and pasted here verbatim by Claude Code._

All responses came from one AI model, `claude-opus-5-5`. Accuracy was close to ceiling in every condition. The model completed all 36 masked predictable items correctly (100%), 35 of 36 masked unexpected items (97.2%), and all 72 intact items (100%). Overall, 143 of 144 responses were correct (99.3%). With P04, P05, and P10 excluded, accuracy was 100% in every condition. The one incorrect response was in the masked unexpected condition, and the model had marked it as unsure.

The model's confidence ratings differed much more than its accuracy did. It marked 18 of 36 masked unexpected answers as unsure and none of the 36 masked predictable answers. The doubt didn't simply follow how many words fit the letters: *curious* (4 possible fits) was marked unsure on all three runs, while predictable masks with many fits were never doubted.

## 5. Manual review of errors

For each error: did the model substitute a more conventional word, a different plausible word, or something else? What made it hard to decide?

_Written by me after the full run. Typed in chat and pasted here verbatim by Claude Code._

The only error was on `_u_io_s`, where the target was *curious* and the model answered *furious*. Both words fit every visible letter, so the mask itself did not decide between them. I don't think *furious* is more expected after a hike. A hiking context most strongly suggests words like *tired*, *exhausted*, or *hungry*, and neither *curious* nor *furious* follows naturally from it. *Furious* is better described as another possible answer that the mask allowed, not a completion the context pushed the model toward. The model's ratings fit this reading. It marked this item unsure on all three runs, and in the run where it answered *furious*, it listed *curious* as an alternative. It wasn't the only item the model doubted, since it marked 18 answers unsure and 17 of those were correct. But this was one of the items where its doubt was most consistent, and the one where that doubt turned out to be justified. The error therefore looks like a product of stimulus ambiguity, not a failure to use context.

## 6. Interpretation

What can and can't I conclude from 12 pairs and one model run?

_Written by me after the full run. Typed in chat and pasted here verbatim by Claude Code._

I expected the masked unexpected condition to be harder than the masked predictable condition. The single error did fall there, but one error out of 36 is far too little to show a difference in accuracy. The near-perfect scores mean accuracy could not separate the two conditions.

This doesn't mean the task failed to show any effect of context. The clearest evidence comes from `__rn` and `for__`. Of the 23 common words that fit `__rn`, *corn* is only the 7th most frequent, and *turn* is more common. Of the 15 that fit `for__`, *forks* is 8th, behind words like *force*. Yet the model answered *corn* and *forks* correctly on all three runs of each. A guesser that relied only on word frequency would have picked the more common words, so the sentence must have done the work. Other ambiguous masks are weaker evidence. `_a_er` fits 53 words and `__sh` fits 31, but *water* and *cash* are the 1st and 2nd most common fits. A frequency-only guesser would also have chosen them, so their correct answers don't by themselves show that context helped. Overall, context clearly helped on at least some items. What the ceiling hides is whether a predictable context helped more than an unexpected one.

The confidence ratings partly fill that gap. Accuracy was nearly identical across the two conditions, but the model was unsure about half of its unexpected answers and none of its predictable ones. Its doubt seemed to follow what the letters and the context together left open, not the letters alone. This bears directly on whether a decoder could know when not to guess. With one model and a small item set, this is a pattern worth testing, not a settled result.

## 7. Mistakes and changes in my approach

_Written by me after the full run. Typed in chat and pasted here verbatim by Claude Code._

The main lesson is that difficulty isn't controlled just by hiding the same number of letters in every word. How hard a masked word is depends on how many real words fit the remaining letters, which letters are hidden, and how common the target and its competitors are. Several masks left very few possible words, and for *umbrella* and *thirsty* only one word fit, so those items were effectively unmasked. Other masks allowed dozens of words. I now see that each mask needs to be checked against a word list for the number of valid completions. The predictable and unexpected conditions also need to be matched on that number. Otherwise, any difference between conditions could come from the masks rather than from the sentence context. I also learned that collecting confidence ratings was worthwhile, because they showed a difference that accuracy alone missed.

## 8. My next question

_Written by me after the full run. Typed in chat and pasted here verbatim by Claude Code._

Next I would test masks that are deliberately ambiguous, with at least two common words fitting the visible letters. I would place them in sentences that favor one completion, the other, or neither. That would push accuracy below ceiling and show directly whether context steers which word the model chooses. The `curious`/`furious` item is a good model for this kind of stimulus. I would also test the confidence pattern more directly by checking whether the model's "unsure" ratings predict its errors once errors are frequent enough to measure. Finally, running the same items with another model would show whether these patterns are specific to `claude-opus-5-5` or hold more generally.
