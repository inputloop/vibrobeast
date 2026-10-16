---
name: drift
description: >-
  Make a drift page: what happened in a window of work and where it drifted from its principles,
  pulled by formula from what the logs already say (git, the ChangeLog, ENHANCE notes, DRIFT.log
  checkpoints, the kid glove's ledger), every sentence citing its sources and every source listing
  the sentences that cite it. Pages are regenerated, never hand-edited; each edition is recorded as
  a mutation and the one it replaced is kept. Pairs with alto (a line on the return tail per page)
  and the wire (a capsule under the 32 KB cap), and each can check the others. Use at hand-back,
  at a session close, for "drift report", "what drifted", "write the drift page", "on-bearing?",
  "what happened this week", or when a reader needs the story of the work with its sources.
---

# Drift

A drift page says what happened and where the work drifted, and it says where each claim came
from.  It is made by formula, so two runs over the same logs give the same page.

## Make the page

    scripts/dr1pg ROOT --since YYYY-MM-DD [--until YYYY-MM-DD] --out PAGE.md \
        [--drift-log DRIFT.log] [--ledger KID-GLOVE-LEDGER] [--alto TAIL] [--capsule CAPSULE.txt]

It reads git, the ChangeLog and ENHANCE notes from ROOT, and any DRIFT.log or kid glove ledger you
name (`kg1sc where ROOT` prints the ledger's folder).  A source that is not there is named NOT
CHECKED on the page; a window with no checkpoint says so, which is not the same as "no drift".

## Check it

    scripts/dr1ck PAGE.md [--root ROOT --since D --until D] [--alto TAIL] [--capsule CAPSULE.txt]

The second reader, in another language: every `[R#]` resolves; every source's "cited by" is true;
every commit in the window is cited; the alto tail names the page's hash; the capsule's hash is the
one recorded.  Exit 1 on any break, 2 when it could not look.

## The rules

- Never edit a page by hand.  If a sentence is wrong, fix what it was pulled from (a ChangeLog
  entry, a checkpoint line) and pull the page again.  The old edition is kept in `.drift/archive/`
  and the change is a line in `.drift/MUTATIONS`.
- Say NOT CHECKED for a source that was not read.  Never let silence read as a clean bill.
- When the page says the work is done, close the prompt's strings (`pg1lv close`, reformat-prompt's
  glove); when it says bail, `pg1lv bail` with the reason.  `pg1lv drift LEDGER...` gives the line the
  page cites for each prompt in its window.
- Put the page's checkpoint line in the hand-back; put its capsule on the wire when a peer should
  see it; let alto carry the one-line notice.
- The capsule is 7-bit ASCII (the page's pilcrow becomes P, so P1 is the page's first paragraph;
  other marks are written plainly or escaped), so the wire cannot mangle it into a hash that reads
  as tampered.  A capsule from before 0.2 still checks by its hash, with a NOTE: pull it again
  before it goes on the wire.

*Version 0.2: edition revised from 0.1 on 2026-10-05; spine: 2026-10-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
