---
name: powerglove
description: Wear a prompt from intake to hand-back so nothing it asked for is dropped, even across a compaction -- lay the egg (the prompt captured verbatim and hashed before any work), hold its strings (every read and call owed coming in, every write, commit and push owed going out) until each is pulled with a receipt or relaxed with a reason, and close only when none is taut. Use for any long or many-part prompt, on "powerglove", "prompt-recycler", "speedboxer", "wear the glove", "what is still owed", "pick up after compaction", or when drift says done or bail; and at the hand-back, for its "Did you ...?" questions (did you leave anything behind, did you commit and clean up, did you say what drifted), each delegated to a skill and answered by a named check.
---

# powerglove — one prompt, worn from intake to hand-back

reformat-prompt works by the session: capture at the start, update as you go, rotate at the end into
the project's versioned model. That frame is fine, and it has a limit: a big or long session gets
compacted, and what was owed by a prompt from three hours ago lives only in a summary. The glove works
by the **prompt**, and keeps everything it needs on disk, so a compaction costs nothing.

```
sh scripts/pg1lv open   LEDGER PROMPT      the egg: the capture's hash, and the strings, all taut
sh scripts/pg1lv owe    LEDGER out WHAT    a string this prompt adds
sh scripts/pg1lv pull   LEDGER N RECEIPT   done: file:PATH, git:REPO@SHA, q:SLUG (checked) or said:TEXT
sh scripts/pg1lv relax  LEDGER N WHY       let go on purpose
sh scripts/pg1lv resume                    after a compaction: every open ledger, its next string
sh scripts/pg1lv close  LEDGER             the egg unchanged, nothing taut, every receipt holds
sh scripts/pg1lv bail   LEDGER WHY         the honest other ending
sh scripts/pg1lv ask    LEDGER             the hand-back as questions: "Did you ...?", and who holds each
sh scripts/pg1lv check  LEDGER [--pull]    run the named checks; --pull pulls what they answer OK
```

In C4 the capture is `bin/prompt-file prompt DATE SLUG FILE` and the ledger is
`q/<date>-<slug>/STRINGS`. Without C4, keep both beside the work and write `# root: .` in the ledger.

## The hand, after Bryant's

Bryant's power-glove (v1.5, his Gauntlet Nexus) is a shell, not a brain: a glove that holds tools in
slots instead of growing one tool forever. Its cuff, caterpillar, is the intake glove this frame
follows: the egg is laid before the first step that transforms the ask; a late capture says late; a
reconstruction says NOT VERBATIM; a hand-off is done when the far side reports the same hash.

| his | ours |
|---|---|
| Cuff (caterpillar): egg at intake, cocoon at the exit | `pg1lv open` lays the egg; `close` refuses a capture changed after intake |
| Ring (ground-truth): verify a value at its source before trusting it | `close` re-reads every checkable receipt; `said:` is counted, never claimed |
| Tag (colophon): terms on what leaves | C4's commit guard (`bin/cm1gd`): no claude.ai link, the declared trailer frame |
| Other hand (kid-glove, Corwin's) | the same kid-glove, worn in a house we do not keep |
| — | drift reports done or bail to the ledger; `resume` is the way back in |

Where his glove routes a result on to its next proper handling (Alfred need not receive it back), ours
is responsible for the opposite guarantee: that no further write or read is left demanded. A string is
pulled (ratcheted) or relaxed, never left hanging.

## The hand-back, as questions (wired 2026-10-16)

A string may carry its question, the skills it delegates to, and the checks that can answer it:

    out  everything read from an inbox, or written outside its home, has its disposition ...
         ? Did you leave anything behind for someone else to ask about?
         @inculcat-boxer  @run-card  !debris  !strays  !layout  !home

(one line in the ledger; wrapped here). `pg1lv ask` reads the taut strings back as questions, each with
the skills that hold it; `pg1lv check` runs the named checks and says OK, ASK (a person decides; it may
be another session's work) or FAULT. A check that says OK can pull its string, and the receipt
`check:NAME` is run again at close, so a fix undone after the pull stops the close. A ledger can only
*name* a check: the checks live in `assets/handback-checks.sh` with the tool, and a name that is not
lowercase letters, digits and dashes is refused before anything runs.

| Did you ... ? | delegates to | checked by |
|---|---|---|
| read the project's memory and preferences, not only what loaded? | mentat-skill, kid-glove | (said) |
| lay the egg before the first step that changed anything? | powerglove, reformat-prompt | the egg's hash at close |
| write down what the next session will need? | mentat-skill | (said) |
| commit, and leave no lock or temp file in `.git`? | sandboxer | `!debris` |
| leave anything behind for someone else to ask about? | **inculcat-boxer**, run-card | `!debris` `!strays` `!layout` `!home` |
| say what drifted, and why? | drift, lens | `pg1lv drift` on the page |

Why: on 2026-10-16 a session left seven temporary git files and a gc lock, and three other sessions
left queues in a scratch folder; somebody else found them and asked the keeper what to do with them.
Each of those is now a question this frame asks before the hand-back, and a check that answers it.

## The default strings

`assets/strings.default` holds what any prompt owes: read the project's own memory and preferences
(not only what loads by itself), load the tools the work will call, capture verbatim, note what is
memory-shaped; then land the pair, sort the terms, write memory where the next session reads it,
commit, push, and finish or let go of every call that asked for a confirmation. Edit it for your shop.

## Names

He offered powerglove, `prompt-recycler` and `speedboxer` (2026-10-15, Q601): this is the frame,
under the first name, worn beside reformat-prompt's session-wise one until he chooses which to wear.

## Tests

`python3 tests.py` (30 cases; `--prove-red` plants twelve faults). The same file is C4's
`t/pg1lv-spec.py`; C4's `bin/dp1rc` keeps this copy, the tool and the strings the same as C4's.

## How this skill can fail (falsifiers)

- **The egg laid late, unsaid.** fails if a ledger's prompt was captured after work began and the
  ledger does not say so; check: `# egg: none (... captured late?)` appears, or the capture predates
  the first commit the ledger cites.
- **A string dropped by a compaction.** fails if a prompt's work is reported finished while
  `pg1lv resume` still lists its ledger; check: run it at every hand-back.
- **A receipt that does not hold.** check: `pg1lv close`, which re-reads each one.

## Credits

Bryant Frankford: power-glove and caterpillar, the glove that holds tools and the egg laid at intake
(Gauntlet Nexus, 2026-10-05). Corwin, 2026-10-15 13:46 and 14:03: "work toward hardening reformat
prompt to be our POWERGLOVE", and "Compaction we can work around a slightly more robust way following
Bryants 'intake glove' model".

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-16; spine: 2026-10-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
