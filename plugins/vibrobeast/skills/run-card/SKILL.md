---
name: run-card
description: The door for "help me run this": a job aid for steps at a screen, a paste card for a shell, or a .rc file the machine runs, picked by who is at the keyboard and what cannot be undone. Use before work runs against a real host, a production database, someone else's data, a backup, a log, a portal or settings page, or anywhere a mistake is expensive or a false conclusion could ship, and especially when the person at the keyboard did not write the steps. Triggers on "help me run this", "step us through this", "walk us through", "walk me through this", "let's get on the box and look", "a job aid", "a checklist we can follow together", "write a run card", "card this", "no card no run", "how do I run this safely", "sweep the logs for X", "check whether Y ever happened", "is that host clean", "what would I paste", "can a volunteer do this". Also when a run just finished and its results need reading in the right order, or before anyone reports a CLEAN result from a sweep.
---

# run-card — the credential-free door

## Help me run this: the door, and the three shapes behind it

"Help me run this" lands here first. Ask two things, then pick a shape:
- who is at the keyboard;
- what can go wrong that cannot be undone.

| shape | for | made with |
|---|---|---|
| **job aid** | people doing steps at a screen: a web portal, a settings page, an installer, often two people on a call | `scripts/ja1md` |
| **paste card** | someone at a shell on a machine with no c4 on it | the furniture and read-order below |
| **.rc card** | anything with more than one step that a machine can run and re-run | `scripts/rc1rn` |

A job aid is a checklist with context. Each step says four things:
- **do**: the screen, the button, the words to type;
- **why**: one line, so the people doing it know what they are doing as they do it;
- **check**: what they see when it worked;
- **stop**: what means stop, where a step can go wrong in a way that matters.

It is written in one plain-text file, which anyone can edit, and rendered two ways:

    sh scripts/ja1md check AID.txt    every step has a why and a check, or it is not ready
    sh scripts/ja1md md AID.txt       markdown, for the repository
    sh scripts/ja1md html AID.txt     a checklist page with boxes, on the egad palette, light and dark

The job aid keeps the card's discipline, said for a screen:
- The why and the check carry the read-order.
- The stop lines are the ABORT.
- Anything only a person may do (a promise, a key, making something public) is named as theirs in its step.

To be sure a job aid covers everything that was asked, grind the request with monocle-stack first:
- each first-layer question becomes a step, or an answered line;
- `mn1sk gaps` shows that none was dropped.

The first one, 2026-10-18: Corwin and Bryant's directory submission, 14 steps in three sections. Its source,
markdown, page and monocle stack are in c4-draw-kiosk `writing/directory/`.

## Since 2026-09-25: the card is a file the machine runs

A study of 47 of our own cards (`c4/h/RESEARCH-2026-09-25-run-cards.md`) found five failure modes:
- **Asserted, not observed.** 9 of 11 re-issues came from something the author asserted about the
  machine and never observed there (a path, a tool's arguments, a config location).
- **Unsafe to re-run.** A step did harm when run twice, and nothing told the driver which step
  they were on.
- **Scope.** The one card spanning three repos flopped.
- **Paste.** Pasting mangled commands.
- **Results lost.** Most results never came home.

So a card with more than one step is now a `.rc` file, run by `rc1rn` (C4's `bin/rc1rn`, shipped
here as `scripts/rc1rn`, which needs nothing else; when the two differ, read the diff and carry the fix
across on purpose, in whichever direction it runs -- 2026-10-04 carried C4's run-once guard here):

    sh scripts/rc1rn CARD.rc          # where am I: the facts, then [x] done / [>] next / [ ] later
    sh scripts/rc1rn CARD.rc next     # do the next step; run it again whenever unsure

No runner? Run the card's steps by hand, facts first.

The discipline below is still the whole point; the runner is where it lives now:
- **Coverage first** becomes `facts()`. Every `fact` and `need` is probed on the driver's machine
  at run time and printed before anything runs. A `need` that doesn't hold stops the run with what
  was seen and what was needed. Never write a path or a tool's usage from memory: probe it, or
  make it a `need`.
- **Idempotence** is a `<step>_done` test that runs before its step. A done step is skipped, so
  re-running is always safe and `status` always knows the place. A step that runs clean but misses
  its effect is reported as the card's fault, not the driver's.
- **ABORT** is a failing step or an unmet need. Anything that can't be undone gets a
  `<step>_confirm` question and runs only on the word yes.
- **One purpose per card.** A turn that touches three repos is three cards, or one card with one
  step per repo, never one step doing all three.
- **Disposition** is a step like any other (unset the token, remove the bag), with its own
  done-test.
- **The return trip** is `<card>.log`, beside the card on the shared folder. The runner writes it;
  the author reads it. The driver's "tell me" shrinks to "done", or to the one STOP line.
- **Rehearse before handing over.** Run the card in the sandbox against a copy of the tree (a local
  bare repo for pushes, a mock for any API) until `status` reads ALL DONE, then hand it over.

A paste card (the rest of this page) is still right for a machine with no c4 on it. It keeps the
read-order, the observable per step, and the ABORT line, and it is rehearsed like any other.

A run-card is what lets someone who did not write the steps run them **correctly, on a real
system, without you standing behind them.** It asks for time and care. It does not ask for
genius, seniority, or a credential. That is the whole point of it — a card is a door that
anyone willing to be careful can walk through.

It exists because of a specific, repeated discovery: **the operator is rarely the weak
part.** The weak part is a step whose result gets read in the wrong order, an absence
reported as a clean bill of health, an instrument pointed at the wrong window, or a
conclusion that travels without the bound it was born with. A card is not a reminder to be
careful. **A card is a measurement scheduled in advance** — it names the instrument, fixes
the order the answers are read in, and states what stops the run.

## The one thing to internalize

> **A card never says "be careful." It says: run this; here is what the answer means; here is
> what stops you.**

If you find yourself writing exhortation into a card, you have written a sermon. Delete it and
write a step with an observable instead.

## The furniture (paste this into the session FIRST)

Every card opens with a field block, **comment-prefixed so it pastes into the shell.** This is
not decoration. The transcript is the evidence — and a tape that shows *commands* but not
their *authorization* cannot be tied back to the card that licensed them. With the furniture
in the shell history, **the tape itself proves what the run was permitted to do**, and a cold
reviewer never has to go looking for the card. Card and trail become one artifact.

    # ============================================================================
    # CARD ID    : RUNCARD-<date>-<nn>-<slug>     (supersede, never edit)
    # PURPOSE    : one sentence — the QUESTION this run answers
    # GATE       : what authorizes this (whose ruling, when) — or "none", said plainly
    # DRIVER     : the human at the keyboard
    # SIGNER     : who signs which output, on whose machine (keys never travel)
    # PRECOND    : what must already be true, checked aloud before step 1
    # WRITES     : EVERY write this card makes, named. "Read-only" must MEAN it —
    #              your own scratch dir is a write, and it gets declared, not assumed
    # TRAIL      : the label comment each step opens with
    # BAG        : one dated dir; everything tees into it; MANIFEST before the hop
    # HOMECOMING : pile-then-one-hop, or quick-turns — DECIDED HERE, with the reason
    # DISPOSITION: what gets DESTROYED, when, and who records it
    # ABORT      : the conditions that stop the run (park it; do not argue with it)
    # ============================================================================

## The read-order, and it is the load-bearing rule

When a step sweeps for something, the card **states the order the output is read in**:

> ### COVERAGE → POSITIVE CONTROL → TARGETS. Always. In that order.

**Coverage first.** What window does the instrument actually see? Retention, scope, host list,
date range. State it *before* the result, where it cannot be skipped.

**Positive control second.** Did the sweep find something it *should* have found? A search that
returns nothing proves nothing unless the same search demonstrably finds a thing you know is
there. **Zero on the control means the instrument is blind — the sweep is VOID, not clean.**

**Targets last.** Only now does a hit or a miss mean anything at all.

**The worked example, and it is why this rule exists.** A sweep of a host's authentication logs
for two suspect SSH keys returned `(no hits)`, `(no hits)`, `(no hits)`. The positive control
was gorgeous — 74,103 accepted logins by real, named users. The instrument was perfect.

Read targets-first, and you write *"host clean — the bound widens to five hosts"* into a
security finding going to a national foundation.

Read coverage-first, and the **very first line** says the logs only reach back six weeks — and
the events under investigation are **five weeks before that**. The sweep is *clean and silent*.
It is a working instrument pointed at a window that does not contain the events. It proves
nothing, and the honest card says so and **does not count that host toward the negative.**

The coverage line was the only thing standing between a careful team and a false claim in a
published report. **That is what the ordering is for.**

## What a card must REFUSE to claim

This is the part that makes a card trustworthy rather than merely tidy:

- **An absence is not a clean result.** "We didn't find it" is only a finding if you *looked*,
  and it is only *worth* something if you say where you looked. **Bound every negative** — in
  the artifact, not in your head.
- **An unreachable host is a gap, not a clean host.** Write the gap into the output.
- **A hash is the start of reading, not a substitute for it.** Verifying a checksum proves the
  bytes didn't change. It says nothing about what they *say*. (A patch report can pass its
  checksum perfectly and still say the rollout failed and two internet-facing hosts are
  unpatched. Read the file.)
- **A note about a check is not the check.** "We swept, it was clean" written in a summary is a
  *claim about* evidence. It is not evidence. If you cannot name the run that produced a fact,
  the fact is data.
- **A bare numeric ID is never a safe search term.** It will match ports, PIDs, and the
  fractional-seconds field of a timestamp, and hand you a phantom incident. Anchor on the name.
- **Prefer the interface that decides over the file you think it reads.** Ask `sshd -T`, not a
  regex over the config that will miss a tab.

## Steps

Numbered. Paste-ready. **Absolute paths** — `~` is not a path, it is an assumption about who
you are, and it will resolve differently for root. Syntax-check every multi-line block before
you hand it to a driver; a card must be *pasteable*, not *interpretable*.

Each step names **the observable that proves it ran** — and each step opens with a label
comment, so the shell history reads back as a narrative. Shell history is evidence. Write it on
purpose.

**Gate steps.** Where a later step's meaning *depends* on an earlier answer, say so, and make
the gate **readable at the keyboard** — put the expected value right there on the card so the
driver can decide without phoning anyone. A gate that requires a round-trip is not a gate; it's
a bottleneck.

## Disposition — the field people forget, and the one that protects strangers

Every run leaves residue: extracted archives, working copies, staging directories, a bag on a
host that isn't yours. And the residue is very often **not about your question and not yours to
keep** — a single system's auth log carries the login records of *every person who ever used
it*.

So the card says, in advance:

1. **What is transacted** — the raw material, most of which is other people's.
2. **What must not travel** — *the analysis runs where the data lands; only the ANSWER comes
   home.* Bring the counts, the hit/no-hit, the hashes. Not the log.
3. **What is destroyed, when, and who writes it down** — with a trigger ("after the outputs are
   verified, and not before") and a receipt.

Preserve-before-act governs the **evidence**. It does not license leaving a fleet's user data on
personal infrastructure. **A run with no disposition step is not finished. It is abandoned.**

## Tone at the keyboard

A card is often being run by someone newer than you, on a system that scares them a little. The
register matters — a door that makes people feel stupid is not a door.

Warmth on a passing gate: *"nice — that's the disk continuity proved, keep going."* A cadence
instruction when the output needs thinking about rather than scrolling past: *"Okay, stop for a
moment. Let's read what we're actually seeing."*

**But the mood colors the encouragement, never the verdict.** Warmth attached to a *failing*
check is poison. A STOP is a STOP, and it is never softened to spare anyone's feelings —
including your own.

## When the run comes back

Read it. **All of it.** A hash that verifies is not a file that has been read, and a faithful
transcript of an artifact is not the artifact — those are *two sources*, and agreement between
them is what makes a thing evidence rather than data.

Then say what it closed, what it **didn't**, and what is still open — **titled, with an owner.**
An unfinished thread handed on *with* a road-map is discharged. Handed on *without* one, it is
dropped, and it is wearing a park's clothing.

## The rule that governs all of it

**No card, no run.** Not because ceremony is good, but because the card is the thing that lets
the next person — a volunteer, a stranger, you in three weeks with none of this in your head —
do the work correctly and prove that they did.

## How this skill can fail (falsifiers)

- **The runner drifted from its source.** fails if `scripts/rc1rn` differs from C4's `bin/rc1rn`; check: `cmp scripts/rc1rn "$C4_ROOT/bin/rc1rn"`, then C4's `sh tests/rc1rn-tests.sh` and `--prove-red` (12/12 and PASS on 2026-09-27).
- **A void sweep counted clean.** fails if a card reports a negative when its control found zero or its coverage window misses the event dates; check: the step's output reads COVERAGE, then CONTROL above 0, then TARGETS.
- **An undeclared write.** fails if the run wrote anywhere not named under WRITES; check: compare the bag's MANIFEST and `find <dirs> -newer <card>.log` against the WRITES field.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.0 on 2026-10-19; spine: 2026-09-23.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
