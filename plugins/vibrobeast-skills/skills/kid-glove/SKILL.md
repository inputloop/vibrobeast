---
name: kid-glove
description: >-
  Arrive gently in a project, garden or machine someone else keeps: find the house rules first
  (instruction files such as CLAUDE.md, installed skills and soft skills, stated preferences and
  values, the licence, ChangeLog and test conventions), follow them, and fill only the gaps, from the
  Corwin + Bryant garden first and then from flagship conventions (GNU Coding Standards, GNU Kind
  Communications Guidelines, GNU's terms, LibreJS, ScanCode and REUSE). Disagreements between the
  house and the kit are logged once and quietly, never nagged; before hand-back, re-check that
  nothing in the house was trampled and hand back drift-style. Use when starting work in a repo or
  environment you did not set up, before applying our conventions somewhere else, when one of our
  skills might override a person's own, or when asked to "defer to their rules", "go kid glove",
  "don't trample", or "what are the house rules here". The other hand of power-glove.
---

# Kid glove

Power-glove drives; kid glove receives.  It asks what already governs a place before offering
anything, fills only the gaps, keeps its disagreements quiet and written down, and checks before
hand-back that it trampled nothing.

## The order (who wins)

1. What the person says now.
2. The house: instruction files in the project, then the person's own skills, soft skills and stated
   preferences.
3. Our kit (the Corwin + Bryant garden).
4. The flagship conventions the kit names.
5. Your own defaults.

A lower layer fills a gap and never overrides a higher one.  When the house and the kit disagree,
the house wins; write the disagreement down once (step 3).  This is Bryant's yield rule for a map
of the house, said for the whole house: "the skill's own file wins, and a disagreement means the map
is stale and is said out loud."

## 1 Defer

Run `scripts/kg1sc scan ROOT` before the first change.  Read every house rule it names before you
act.  It writes nothing inside ROOT; its state lives under `~/.local/state/kid-glove/` (`KG_STATE`
moves it).

## 2 Fill

For each gap the scan names, take ours first, then the flagship.  In the hand-back, say which layer
each choice came from, for example "ChangeLog: house; JavaScript labels: flagship (LibreJS);
licence: HOLD, asked the owners".  Where neither has a rule, say "no rule here; chose X"; do not
invent a house rule.

Two kinds of missing are not gaps, and the kit fills neither:

- HOLD: the licence.  It is large and cannot be undone, so it is the owners' to choose, in any house.
  Ask them; add no licence line, header or file until they have.
- NOT CHECKED: skills and preferences.  The person's own may live in their account, not in this
  tree.  Ask; never fill them from ours.

The scan reads a licence from its text and, the REUSE way, from SPDX ids (REUSE.toml, .reuse/dep5,
and the file names under LICENSES/).

## 3 Track, don't nag

- The scan logs the conflicts it can see (the licence family, the ChangeLog's form).  When you
  notice another (a preference of theirs that one of our skills would contradict), log it:
  `scripts/kg1sc note ROOT TOPIC "what the house says; what the kit says; chose house"`.
- When the house keeps ENHANCE notes, lines are tagged CONFLICT so its ENHANCE stays its own;
  otherwise they are tagged ENHANCE in the kid glove's sandbox.
- A line is written once.  In your reply, one count line ("2 conflicts, house chose; ledger at
  PATH"), never the list again, and never a question about something the house already decided.
- Put a gate only where the act is large and cannot be undone.  Reversible doors stay wide, with the
  ledger as the audit trail.  Bryant: "for every gate to adoption the amount of adoption goes down."

## 4 Re-check before hand-back

Run `scripts/kg1sc recheck ROOT`.  Against the scan's baseline it names:

- TOUCHED: a house rule file changed during the work, or a licence line (SPDX) was added to,
  changed in or taken out of a file the house already had, whatever the house licence.  Say whether
  you changed it and why.
- TRAMPLE: a new or changed file whose licence id fights the house's.  Fix it, or name it plainly.
- NOT CHECKED: a comparison that could not run: a licence line where the house names no licence (or
  one the scan could not read), or no git baseline to list the changes.  It is never a pass.
- GAP: files changed that the house's ChangeLog does not record yet.

A second reader (`scripts/kg1sc.py`, in Python) reads the same baseline and tree, and the re-check
says whether it agrees.  When it disagrees the re-check is NOT CHECKED; when it is absent, the
verdicts come from one reader, and the re-check says so.

It exits 1 on a TRAMPLE, otherwise 2 on anything NOT CHECKED, otherwise 0.

## 5 Hand back, drift-style

The re-check ends with one checkpoint line in the drift form (on-bearing? still-arguing?
pushed-back).  Paste it into the hand-back.  Where the drift skill is present, its page carries the
line and links each claim to its source.

## The kit, and the checks

`scripts/kg1sc topics` reads the kit back in words: per topic, what the house is probed for, what
ours offers, and the flagship.  `tests/kid-glove-tests.sh` runs the tool against made-up houses;
`kg1sc.py` is a second reader in another language and must agree, on the scan and on the re-check;
`--prove-red` plants one fault per check (among them the kit before the house, a repeated nag,
footprints in the house, a licence filled from the kit, REUSE unread, and a licence line read as
clean where the house names no licence) and expects each to go red.  Disable the tool with
`KG1SC=0`.

## Credits

Bryant Frankford: power-glove, the map-of-the-house yield rule, the consent-gate design inputs, and
the skill-integrity checks this file passes.  With thanks; his work shares our licence.
Alfred (for Bryant): the findings of 2026-10-05 behind the licence HOLD, the NOT CHECKED re-check and
its second reader, and the scan that sees Bryant's house and reads REUSE.
The flagship conventions belong to their projects (GNU, LibreJS, AboutCode's ScanCode, the FSFE's
REUSE); the kit points at them and copies nothing.

## How this skill can fail (falsifiers)

- **The kit trampled a house rule.** Check: `kg1sc recheck` names a TRAMPLE and exits 1.
- **A conflict was raised twice.** Check: a second `kg1sc scan` of the same house says the conflict is
  known, not new (the tests' "the second scan does not nag").
- **A licence was filled from the kit.** Check: the scan says HOLD for the licence and the re-check finds
  no licence file the owners did not choose.
- **A form the house keeps was read as a gap.** A manual, NEWS, a ChangeLog, INSTALL or `--version` text
  that a free-software reader expects, with no topic to find it. Check: `kg1sc scan TREE --raw` on a
  GNU-form tree says FOUND for each (the manual, cli and install topics came from such a miss, theseus,
  2026-10-18).
- **One reader decided alone.** Check: the re-check says the second reader (`kg1sc.py`) agreed, or it
  says NOT CHECKED.
- Off-switch: `KG1SC=0`.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-20; spine: 2026-10-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-mythos-5-1)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
