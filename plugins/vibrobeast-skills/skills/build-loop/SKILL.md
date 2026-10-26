---
name: build-loop
description: >-
  A counted build discipline: Plan-Do-Check-Act (the Deming cycle) with a budget of QA passes, one
  allowed redesign, and a final swing that can be backed out; and, for several tasks at once, the
  multitask swing, which runs every task's QA checks together and contrasts the checks they share.
  Use when starting any build task (code, a document, a tool, a site) that should be designed and
  QA-planned before it is built, or when one review's fixes fall into several tasks worked together;
  on "build loop", "design then QA plan", "how many QA passes", "final swing", "should I redesign",
  "PDCA", "sw1ng", "multitask swing", "sw1mt", "work these tasks together". Ships scripts/sw1ng
  (counts the passes), scripts/sw1mt (runs and contrasts several tasks' checks) and
  assets/BUILD-LOOP.md, the same rules as a paste-in for any CLAUDE.md. Electable: choosing the loop
  is optional; once chosen, every step is required.
---

# build-loop — PDCA with a counted budget and a backed-out last try

The wider field calls the shape **Plan-Do-Check-Act** (the Deming or Shewhart cycle). Writing the test
plan together with the design, before building, is the **V-model**'s habit. Backing out a last attempt
that made things worse is a **rollback to the last known good**. What this skill adds is the counting:
how many passes, when a redesign is allowed, and when the last try is owed.

## Choosing it, and declining it

**Choosing this loop is optional. Once chosen for a task, every step below is required** — a loop you
can skip steps of is not a loop, and the counter means nothing. The one number in it (three passes) is a
stated default you may change per task. To decline: do not open a loop for the task, and say so.

## The loop

1. **Design, then a QA plan.** Write both before building. Set the QA counter to **0** and the redesign
   indicator to **NO**. The maximum number of QA passes per cycle is **3** unless you set another.
2. **Build.** If the design is wrong, this is the cheap moment to redesign.
3. **QA pass.** Run the **whole** QA plan, even after the first issue turns up. Then add 1 to the
   counter. While the counter is below the maximum, fix what the pass found (bigger things first;
   warnings can wait for the final swing), then run the whole plan again.
4. **Design opportunity — once.** Leaving the QA loop because you found a better way to meet the
   requirements may take the cycle counter up by one and send you back to build (update the QA plan
   if the design moved).
5. **Redesign — once.** If a pass shows the design itself is wrong and the indicator is still NO: set
   it to YES first, go back to design, write a **new** QA plan, and reset the counter to 0.
6. **Another round.** If the maximum is spent, the plan is not met, and any correction was made in
   that cycle, you may take another full round of passes (the cycle counter goes up by one). With
   nothing corrected, there is no further round.
7. **Clean, or the final swing.** If a pass comes back clean (no issues, no warnings), you are done and
   the final swing is skipped. Otherwise, when the rounds are spent, the **final swing** is owed:
   snapshot what it will touch, close what is left — unmet requirements, reachable fixes, cheap
   improvements, warnings — and in this swing only, **not undoing earlier fixes comes first**. If it
   made things worse, restore the snapshot.

## Counting it: `scripts/sw1ng`

POSIX sh, no dependencies beyond awk and sha256sum. The state lives in a `SWING` file beside the work.

```
sh scripts/sw1ng open TASK --design DESIGN.md --qaplan QAPLAN.md [--max 3]
sh scripts/sw1ng next                        # what the loop says to do now -- ask, don't remember
sh scripts/sw1ng qa --issues N --warnings W  # after each WHOLE pass
sh scripts/sw1ng redesign --design D2.md --qaplan QAPLAN2.md   # once; the plan's bytes must change
sh scripts/sw1ng opportunity 'NOTE'          # once: cycle +1, back to build
sh scripts/sw1ng complete                    # only after a clean pass
sh scripts/sw1ng final open FILE...          # snapshot, then the final swing
sh scripts/sw1ng final close --kept|--worse  # keep it, or restore the snapshot (hash-checked)
sh scripts/sw1ng --prove-red                 # every refusal planted and shown firing
```

What it measures and what it takes on your word are declared in its header: the issue and warning
counts are **your word** — the tool counts passes, it does not run your QA plan.

## With no shell at all

`assets/BUILD-LOOP.md` is the same loop with no tool and no house words. Paste it into a CLAUDE.md,
a README, or a message, **verbatim**. It works in any assistant, or on paper.

## The question it carried, ruled (2026-10-04)

"The counter may go up by one, up to one time" read two honest ways: **once in total** (the design
opportunity and the extra round share it, so cycles cap at 2) or **once per cause** (only the
opportunity is limited; the extra round is bounded by the one redesign and the final swing). Until
2026-10-04 `sw1ng` computed both and refused with exit 9 where they disagreed, so the author would
rule. He ruled: "I intended to redesign once as once per cause but final swing only once per try at
the full build-loop." So `sw1ng` now decides per cause, still computes the strict cap, and says in
`next` when the strict reading would have stopped. The final swing is once per try at the loop: a
closed loop takes no further swings.

### Iterating, and the swing at other scales

A loop may be repeated iteratively, or interactively with stops for questions; both are possible.
His caution: most people using an AI will not expect extra stops, and need to be shown why a stop for
a question is worth it. Within one loop, a sub-agent taking part in a critique does not weigh the other
sub-agents' work, unless a later LENS, plaid or bubble-chamber pass has made that its context.

He sees the swing, by default, as an accessibility lens over one context, scaling with the LENS and
multiplexing the same way across larger "sky-scrapers" of function: recomposing whole frameworks under
each application so cross-cutting concerns in our own domains are each handled with care, then
stitching back up. Working arm to arm with a cross-cutting goal (accessibility) binds one iteration to
the next; a LENS-like comparison of approaches works as well, above all where a C4-like approach
requires several complete, competing implementations to contrast. How that plays out is left to be
seen: a LENS, or at least a MICROSCOPE, opportunity (his words of 2026-10-04, spelling corrected).

## Write, then build: where the loop meets the shop's forms

The loop's first step is writing, and the writing has forms (the `writing-forms` skill; register
`c/wf`). A loop opened in the shop names two files that already exist and pass `wf-check.sh`:

- **DESIGN** — *what should this thing be, written where a tool can find it, before it is built*;
  opens with a status line, then what the source asked for **in their words**.
- **QAPLAN** — *what would have to hold for this build to be done, written BEFORE the build*.

`sw1ng open` checks only that the two files exist; `wf-check.sh` is the check that they are the
right forms. Run both at open. **A SEAM to know about:** `sw1ng` keeps its counters in
`h/SWING-<date>-<task>` (no extension). The SWING *form* in `c/wf` answers another question (the
legs toward a big swing). Same prefix, two meanings; `sw1ng state` reads the first, a reader reads
the second. Neither is renamed here; the register row says so.

When the thing built is a tool, `tool-lifecycle` rides the final swing: *test is not optimization*.
A tool that replaces another must show it still catches what the old one caught (run the old one's
positive controls against the new one) or keep the old check as an explicit second; that is the
final swing's "earlier findings first" rule applied to tools.

### His sentence on pressure (2026-09-26, verbatim), and how the loop reads it

> when installing each operating fact first plan the memory write path and references impacts to
> the taxonomy from m/t back toward the minimum bearably smooth word set to describe context, then
> update the context mountain, when designing choose first where you can create additional ballace
> by linking a new word then where you can create new meaning for additional context by writing
> meaning upward toward the context pressures (right side, usually, in design context); in
> build/run contexts follow context pressure until it inverts to ballanced pressure asserting the
> result matches the reversed guard (typically evaluated second or separately in case of
> instrumenting/proving/etc/virtualized move rather than effecting -e.g.- a disc/stream write).

My reading of his words, for Corwin to rule on; it stands until he does:

| his words | where it lands in the loop |
|---|---|
| plan the memory write path and taxonomy impact first | before `open`: name where the result will be recorded (MEMORY, a fact, a register row) and which m/t words it touches |
| design: balance by linking a new word, then write meaning upward toward the pressures | the DESIGN file: link to words the tree already has before coining one; a coined word gets its register row the same turn |
| build/run: follow the pressure until it inverts to balance | the QA passes: keep running the whole plan while findings come back; balance is a clean pass |
| the result matches the reversed guard, evaluated second or separately | `--prove-red` and the planted-fault controls: the guard is proven by making it fire on a copy, never by the write itself |

## What the passes climb: the swing-dome

His words (2026-09-28, c4 `q/2026-09-28-front-door-spellball/PROMPT.md`): "our beloved accessibly
swing-dome (up the teetering tower of feature to see what might be possible, down the ladder to scaffold
for all access we might offer, carefully confess our weakness where signage is apposite, bring the roof
over in terms of hardening our own channel (ingress/egress, brokering) concerns, repeat the pattern to
handle breakage in peering etc. interop, working with the remotes to balance concerns ... finally bring
the dome over such as to establish our system feels not less well cared for in terms of handing the right
signals well and etc not so happy paths modulo context". Approved into this skill the same evening ("Swing
dome: we want the improvements, yes"; `AS4CE0001/ERRATA` E12).

The loop counts passes; the dome says what the passes must climb. A QA plan names at least one check on
each rung, or says which rung it declines and why (a declined rung is a line, not a silence):

1. **TOWER**   up the teetering tower: the feature at full reach, what might be possible (the design's
               own acceptance checks).
2. **LADDER**  down to scaffold for all access we can offer: keyboard, screen reader, reduced motion,
               contrast, a path that needs no picture.
3. **SIGNAGE** confess the weakness where it is apt, in the product at the door, not only in the notes.
4. **ROOF**    harden our own channel: what is read, what travels, what is brokered, what never ships
               (the `egress` soft skill rides here).
5. **PEERING** the same pattern at the interop edge: a peer, a format or a host that answers wrong.
6. **REMOTES** balance concerns with the things we also make or steward, against the harder-to-change
               expectations of actors we do not.
7. **DOME**    over all of it: the system feels no less cared for on the not-happy paths (errors said
               plainly, a blocked store survived, a refusal explained, motion off honoured).

Worked example: c4 `showroom/views/spellball/QAPLAN-2026-09-28-spell-ball.md` (rungs 1-4 and 7; 5 and 6
declined there: no peer, no remote) and c4 `showroom/views/spellball/ACCESSIBILITY-2026-09-28-spell-ball.md` (rungs 2 and 3).

**When trouble repeats.** A QA plan also says whether the build owes a TESTMANIFEST (`manifest: none owed`
is the usual answer). One is owed only when a problem class has recurred across two works or tools, a check
was caught passing over a real fault, or he says so; the soft skill `grand-test-manifest` and the spell
c4 `spells/ratchet/` decide it, and c4 `bin/as1te state` then gives `sw1ng qa` its counts (RED and BLIND
are issues, OWED and OPEN warnings) as a tool's word rather than yours. Provisional: Q534-Q542.

## Landing: the disk is the work

Learned the hard way on 2026-09-28 (`AS4CE0001/ERRATA` E13; c4
`q/2026-09-28-front-door-spellball/PROMPT-2-review-harden.md`): a widget's source lived only in a context
that was compacted and was lost; three sub-agent reports reached the session only as messages and were
recovered from transcripts by luck; the one screenshot that showed a finding was overwritten and came back
only because he had saved it from the chat. Copies to disk were not always the same bytes. So, while the
loop runs:

1. **WRITE BEFORE SHOW**  anything shown (a widget, a page, a draft) is written to disk first; what is
                          shown is a view of that file.
2. **SOURCES LAND**       a sub-agent's report, or any outside reading the design rests on, lands on disk
                          verbatim, with its brief, as it arrives, beside the work.
3. **EVIDENCE IS KEPT**   screenshots and receipts are named by pass and never overwritten.
4. **HASH EVERY COMMIT**  a file copied to disk is hashed on both sides; images by content, since PNGs
                          gain a C2PA stamp in transit (c4 `check-landing.py hash` sets it aside).
5. **PATHS RESOLVE**      before a hand-back names paths, `check-landing.py refs` runs over it; what does
                          not resolve is fixed, or said to be intentional.
6. **WAITING IS WORKING** while a permission or an answer is pending, land what is done.
7. **POINT AT THE DISK**  a file that has landed is named by its path on his disk; a chat attachment is
                          only for a download he asked for (an attachment opens from the session's copy,
                          which sends him through Drive or Downloads to read it).

## Several tasks at once: the multitask swing

Composed from the 2026-09-29 turn (c4 `h/BUILD-LOOP-2026-09-29-plaid.md`; his words there: "implementing a
multitask swing to work tasks and contrast results"). `sw1ng` stays the loop for one task; this is the loop
around several, for when one review turns up fixes that fall into more than one task. Choosing it is
optional; once chosen, every rule is required.

1. **BUILD EACH**   one `sw1ng` loop per task, as ever: a design and a QA plan before building.
2. **READ TWICE**   a first set of readers reads the work, at least two to a row; a second set, woven
                    across the first, asks not what is wrong with the work but what the first set missed,
                    and how independent its readers were (the same tool, the same persona, the same source).
3. **FOLD**         one list of findings, each naming the readers that found it; a finding that only
                    readers sharing a tool or a persona found is marked as having one route (check it
                    another way before acting on it); the list is grouped into tasks. A last look names risks and openings over it all, and fixes nothing.
4. **CHECK LINES**  each task's QA plan marks its runnable checks: `CHECK:` (a failure is an issue) and
                    `WARN:` (a failure is a warning), each a command run from the tree root.
5. **ONE RUN**      one run executes every plan's checks and prints a row per task; `--record` writes each
                    task's pass through `sw1ng`.
6. **SAME OUTCOME** a check two plans share is run under both and must come out the same; if it does not,
                    it is a SPLIT, an issue for both.
7. **SAY WHERE**    a plan says where each check was run; a check too slow for one call (the device shell's
                    limit is three minutes) runs elsewhere, and the plan says so.
8. **CLOSE EACH**   each task closes on a clean pass. A check found wrong is an issue: fix the check, and
                    say in the plan that the check was fixed, not the work.

```
sh scripts/sw1mt open PLAN             # one sw1ng loop per row: TASK SWING DESIGN QAPLAN, tab-separated
sh scripts/sw1mt run PLAN [--record]   # every CHECK:/WARN: line of every plan, run from the current folder
sh scripts/sw1mt --prove-red           # the planted faults, each shown firing; holds from any folder
```

Run it from the root of the tree the checks name; it finds `sw1ng` beside itself. It uses awk, and held
under GNU awk 5.1 and mawk 1.3.4 (2026-09-29); a check that itself uses awk says which awk it ran under
(the two part ways on some patterns: c4 `h/FOLD-2026-09-29-plaid.md`). Worked example: c4
`p/C4/fold/PLAN-2026-09-29.tsv` (four tasks, seventeen fixes, two shared checks, both the same).

What it does not do yet: run one task's checks against another task's files (a wider contrast), or keep a
ledger of findings across turns (c4 `h/ENHANCE-2026-09-29-fold.md`, items 1 and 6). Whether the second
reading (rule 2) becomes a skill of its own pends ENHANCE in the usual way; his remark that it was not yet
one was an observation, not a direction (2026-09-29).

## How this skill can fail (falsifiers)

- A task closes with warnings still open and no final swing: `sw1ng complete` should have refused.
- A redesign keeps the old QA plan: `sw1ng redesign` should have refused on unchanged bytes.
- The paste-in and `SKILL.md` disagree on a step: diff the numbered lists; one of them drifted.
- A seat without a shell cannot follow the loop from `assets/BUILD-LOOP.md` alone.
- `scripts/sw1ng` drifts from `c4/bin/sw1ng` (the canon copy): their sha256 must match; when c4's
  moves, this copy is refreshed from it, never edited here.
- A DESIGN or QAPLAN named at `open` reads RED in `wf-check.sh`: the loop opened on the wrong form.
- A QA plan names neither a check nor a declining line for some rung of the swing-dome: the plan
  skipped a rung silently.
- The seven rungs, the seven landing rules, or the eight multitask rules differ between this file and
  `assets/BUILD-LOOP.md` (compare the numbered lines): one of them drifted.
- `scripts/sw1mt` drifts from `c4/bin/sw1mt` (the canon copy): their sha256 must match; when c4's moves,
  this copy is refreshed from it, never edited here.
- `sh scripts/sw1mt --prove-red`, run from any folder with the skill as it ships, does not end "all held,
  all fired" (before 2026-09-29 the canon, copied here, ran 4 RED: it looked for sw1ng under ../bin).
- A check two plans share comes out differently under them and no SPLIT is printed.
- A hand-back names a path that `check-landing.py refs` cannot resolve, or a landed file whose
  both-sides hash was never taken.

Off-switch: do not open a loop, or say "no build loop on this".

Staged 2026-09-22 in c4/skills-mint/2026-09-22/build-loop/ (the tank verdict: a NEW skill that carries sw1ng); landed here 2026-09-26 because it had never reached a session.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.2: edition revised from 1.1.0 on 2026-10-10; spine: 2026-09-22.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
