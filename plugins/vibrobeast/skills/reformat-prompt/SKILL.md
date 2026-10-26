---
name: reformat-prompt
description: >
  Land Corwin's (reformat-prompt) / (rewrite-prompt) pairs the C4 way — verbatim + bettered reading into h/REFORMAT-*, HEAL named not smoothed, taxonomy hand-turn check, stingy pinning. Trigger on either marker in a prompt, or "reformat my prompt", "rewrite this prompt the C4 way", "land this in the vein". Also the glove: hold what a prompt still owes, coming in (reads, tool and MCP calls) and going out (writes, commits, pushes), until each string is pulled with a receipt or relaxed with a reason; on "powerglove", "the strings", "what does this prompt still owe", "close the prompt", or when drift says done or bail.
---

# reformat-prompt — land the pair in the vein

DRAFT v0.1, Claude-minted 2026-08-06 from the practiced discipline, home ruling baked 2026-08-08;
wants Corwin's look and skill-sign before it counts as more than scaffolding. In-tree twin:
h/SKILL-reformat-prompt-v0.md (the tree's copy is the accountable one; this library copy is reach).

## The standing meaning

When a Corwin prompt carries the marker `(reformat-prompt)` or `(rewrite-prompt)` — both stand,
per his ruling Q333: "forever is a little strong (but until we change it, forever is quite
fair)" — the prompt itself is cargo, not just instruction. The job: make the prompt easy for
Claude to read, and LAND THE PAIR — his verbatim AND the bettered reading — in C4.
Standing order (Corwin, 2026-08-06): every pair lands, every time; the pair-corpus is THE RICH
VEIN. This is never an editing service.

## With or without C4

The discipline (verbatim, reading, HEAL, taxonomy check) needs no C4. With a C4 tree in reach it lands
there, as below. Without one, land the pair in the working project's own `h/REFORMAT-YYYY-MM-DD-slug.md`
(and the raw capture in its `q/`, if it keeps one), and say where it went; the taxonomy check then
sorts terms against that project's own glossary, or marks every term HAND-TURNING.

## Home and shape

RULED Q334 (2026-08-08) — both homes, by role, different moments of the same prompt:
- `q/` holds RAW VERBATIM CAPTURES — the capture moment.
- `h/REFORMAT-YYYY-MM-DD-slug.md` holds the WORKED PAIRS — verbatim + bettered, the worked
  moment. Same-day later prompts append as §2 unless the prompt opens a campaign (own file,
  cross-linked).

Four parts, in order, every time:

1. **VERBATIM (canonical).** His words exactly, typos and all, blockquoted. The reading below
   loses to this on any conflict. Long is fine; the vein wants the whole ore.
2. **THE READING (derived).** Faithful decomposition: context, the ask operationalized, method,
   constraints, exits he offered. Name OPENINGS as eagerly as gotchas.
3. **HEAL — differences named, not smoothed.** Every slip healed is listed with its correction.
   A word that might be deliberate is NOT healed — flag it for his pin (precedent: compossible,
   RULED standing). Low-confidence readings say so. Unclosed brackets get read, reading stated.
4. **TAXONOMY CHECK — the hand-turn pass.** Sort every hand-turned term: PINNED (cite) ·
   HAND-TURNING (flag toward k/v; his pin, not ours) · EPHEMERAL. Default stingy. Unresolvables
   go to the bank as Qnnn rows, never a guess.

## The handoffs

- Pins belong to Corwin: questions ride the bank (evidence/question-bank-iTNH.tsv) dealt via
  the worksheet lane (w0sh renders; RULING Qnnn in chat), WHERE/TOOL/ACT/RECEIPT-shaped.
  Never re-ask a paid debt; a receipt found means silence.
- Recurring terms land toward evidence/terms-of-art.tsv with definer CORWIN (baseline
  instrument) vs Corwin (the man) kept distinct.
- Files are DRAFT-unsigned at mint; signing is Corwin's ritual, never prompted.

## The glove: every string pulled or relaxed

Landing the pair is half the job. The other half is everything the prompt leaves owed: the reads and
calls it needs coming in, the writes, commits and pushes it needs going out. Missed, each one is a
tangle the next session trips on (2026-10-15: a rule sat unread in the project's own memory for days,
because only the account's preferences load by themselves). The glove holds them as **strings**:

```
sh scripts/pg1lv open q/<date>-<slug>/STRINGS q/PROMPT-<date>-<slug>.md   the defaults, all taut
sh scripts/pg1lv owe   LEDGER out "tell Bryant"                          a string this prompt adds
sh scripts/pg1lv pull  LEDGER 5 file:h/REFORMAT-<date>-<slug>.md         done, and where it shows
sh scripts/pg1lv relax LEDGER 9 "c4 has no remote"                       let go, and why
sh scripts/pg1lv state LEDGER                                            what is taut; the next one
sh scripts/pg1lv close LEDGER                                            only when nothing is taut
sh scripts/pg1lv bail  LEDGER "the session ran out"                      the honest other ending
```

A receipt is `file:PATH`, `git:REPO@SHA`, `q:SLUG` (checked when the ledger closes) or `said:TEXT`
(counted, never claimed as checked). `close` succeeds only when no string is taut and every checkable
receipt holds: nothing further to write or read for this prompt. `bail` marks each string still owed,
with the reason, so a stop is never silent. The defaults (`assets/strings.default`) are the strings any
prompt owes; edit them for your shop. Without C4, keep the ledger beside the pair in the project's `h/`
and write `# root: .` at its top.

**Drift reports here.** When a drift page says the work is done, `close` the prompt's ledger; when it
says bail, `bail` it. `pg1lv drift LEDGER...` gives the line a page cites for each prompt in its window.

Names he offered for the glove (2026-10-15): powerglove, `prompt-recycler`, `speedboxer`. The skill
keeps its name until he chooses (Q601), since a rename changes what every user types.

## Refusals

Never paraphrase-then-discard the original. Never smooth silently. Never pin on his behalf.
When in doubt whether a prompt is load-bearing, land it.


## How this skill can fail (falsifiers)

- **The verbatim drifted.** fails if the VERBATIM block differs from the prompt as sent by even one character; check: diff the blockquote, `> ` stripped, against the prompt text in the session transcript.
- **A slip smoothed silently.** fails if a word in the reading differs from the verbatim with no HEAL line naming it; check: for each changed word you find, one HEAL line names it.
- **A pin taken on his behalf.** fails if a term is PINNED with no cited ruling; check: every PINNED term cites a RULING Qnnn you can find in the bank.
- **A pair not landed.** fails if a marked prompt has no `h/REFORMAT-<date>-*.md` entry that day; check: `ls h/REFORMAT-$(date +%F)-*` and grep for the prompt's first words.

- **A string left taut.** fails if a prompt's work is reported finished while its ledger is open or
  holds a taut string; check: `pg1lv drift q/*/STRINGS` and read every line that is not closed or bailed.
- **A receipt that does not hold.** fails if a pulled string names a file, commit or capture that is
  not there; check: `pg1lv close`, which re-reads every checkable receipt; `sh tests.sh --prove-red`
  plants six faults and catches each.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.2 on 2026-10-15; spine: 2026-08-06.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
