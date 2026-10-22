# Claude's Prediction (AI-generated, not the author's)

Written by Claude Code on 2026-10-22, before any real results existed, at the author's request. It is kept separate from `lab_notebook.md` so it doesn't replace the author's own prediction. It is a guess, not evidence.

1. **Masked sentences:** Both conditions near ceiling (10–12 of 12 pairs recovered each), with no clear difference: 0–1 more "predictable only" than "unexpected only" pairs. Reason: the visible letters leave very few possible words for most unexpected targets (`_r_vy`, `_wor_`, `__oe`), which offsets any pull toward predictable words.
2. **Intact sentences:** The model returns all 24 unchanged in every repeat.
3. **Confidence:** Mostly "confident". Any wrong answers will more likely be confident than unsure, and will often not list the right word as an alternative.
4. **Most likely misses:** Patterns with many common fits where the true word is odd, such as P04 `__rn` (corn). A predictable word could also miss where a more common word fits, such as P03 `__est` (guest, chest).
5. **What would surprise me:** The model changing an intact unexpected sentence, or a gap of 3 or more pairs in either direction.
