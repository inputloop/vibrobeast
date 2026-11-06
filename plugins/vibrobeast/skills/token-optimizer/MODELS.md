# Minimum suitable model: the ledger

What token-optimizer means by "the smallest model that is good enough", as data, not opinion. Each row is
one task given, word for word, to several model sizes on one brief; the verdict says which was the
smallest that did the job right, and what the others missed. Corwin asked for this ledger on 2026-11-01
("to further grow our collection of data as to minimum suitable model (that should be in token
optimizer)").

How to add a row: run the same brief on at least two sizes at once (background helpers), keep each
output unedited beside the brief, then judge against the person's exact words, not against each other.
Tokens are mostly the shared context, so time and fidelity tell more than token counts.

| Date | Task kind | Brief and outputs | Tried | Smallest suitable | What the others missed |
|---|---|---|---|---|---|
| 2026-11-01 | plan a UI feature from a written brief (the tone d-pad) | c4 q/2026-11-01-dpad/ (PROMPT.md, plans/, TRIAL.md) | Haiku 157k tok 1m46s; Sonnet 126k 1m00s; Opus 146k 3m01s; Fable failed (no credits) | **Sonnet** | Haiku normalised away the unusual ask (moved the wrong pads); Opus added accessibility edge cases and a byte-equal phase, worth it for the merge |

Working rule from the rows so far: plan with the smallest model that passed; merge and judge against the
person's words with the larger one.
