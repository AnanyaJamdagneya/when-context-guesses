# AI Assistance Note

I built this project with help from Claude Code, an AI coding assistant made by Anthropic. This note records who did what, so I can describe the project accurately.

## What I did

- Came up with the question, from misunderstanding a camper's speech while volunteering.
- Wrote the experiment specification: matched sentence pairs, intact vs. half-masked target words, identical mask positions within each pair, exact-match scoring, manual review of every error, and rules against cherry-picking or inventing results.
- Chose which improvements to add (stated uncertainty, letter-pattern counts, repeats).
- Ran the pilot and the full experiment on my own computer with my own API key, and pushed the repository to GitHub.
- Notebook sections 4–8 are blank for my own results review and interpretation.
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



## What ChatGPT did

- Wrote the dataset review flagging P04, P05, and P10, and explained the word-frequency and visible-letter confounds.
- Recommended keeping all 12 pairs and reporting a secondary analysis excluding those three pairs before results were shared in the chat.
- Wrote the predictions copied into notebook section 2 and the later caveat about visible letters.
- Read the committed report. Its proposed notebook entries for sections 4–8 were removed at the author's request; these sections are now blank.
- Filled the README Results section from the report and corrected the notebook's attribution of earlier ChatGPT text.
- Corrected its earlier mistaken claim: “paper” does fit “_a_er.”

ChatGPT did not run the experiment or modify its raw results. This update verifies the ChatGPT contributions from the visible conversation, not the earlier claims about who wrote the Python code or ran the experiment.
