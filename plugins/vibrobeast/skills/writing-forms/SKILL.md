---
name: writing-forms
description: >-
  Which writing form a dated deliverable takes in the shop, and the five techniques every form
  shares. Use whenever someone is about to write a dated deliverable — "which form is this?",
  "write it up", "land a note / card / model / lens", "what shape does a … take", "is there a form
  for this", or when a new PREFIX-date-slug filename is about to be minted. Carries the rule that a
  deliverable picks ONE form and says so in its filename, points at the register c/wf (columns
  d/c/wf) as the source of truth, names the most-used forms and the GNU release forms (a manual,
  NEWS, a ChangeLog, INSTALL, --help and --version), the six cross-cutting techniques (two piles ·
  cite at the act · a falsifier on every concern · the pair rule · his words · the reader's gain
  first), how a new form is born, and the fence on notes other sessions wrote. Not rolls (report kinds and their guards), not
  reformat-prompt (the REFORMAT pair), not run-card (the RUNCARD), not skill-creator (skills).
  Owns the FORM, not the content.
metadata:
  origin: "o63, Corwin's words 2026-09-11: 'generalizing the writing forms and techniques into a SKILL'; the register c/wf was collected first because the o63 blocker read 'the forms need collecting into one register before a skill can carry them'"
  version: "0.1 — DRAFT-unsigned, minted 2026-09-11 by Fable (Mentat/Vibrobeast); wants Corwin's look and skill-sign before it counts as more than scaffolding"
---

# writing-forms — one form per deliverable, said in the filename

The shop keeps its prose in dated, prefixed files, `<FORM>-<date>-<slug>.md`, filed where their
subject lives: a project's own folder, the seat's `advice/` ledger for ENHANCE queues and retro
records, facts under `facts/`, doctrine under `decks/`, rows under `c/` with their columns in `d/`.
Not piled in the seat's `h/`: its INDEX names `h/` the keeper's scratch-pad, not a home, and
skilltank says the same ("Never `h/`"). Each form
answers one question and opens with its own first section, so a reader who knows the prefix knows
what the file will do for them before opening it. This skill is the discipline that keeps that
true: it makes a writer choose a form before writing, name it in the filename, and open with the
section that form owns. It does not tell you what to say. It tells you which shape the saying takes.

## The rule — pick one form and say so in the filename

A deliverable takes exactly one form, and the filename carries it:

    <FORM>-<date>-<slug>.<ext>          NOTE-2026-08-09-fn.md
    <FORM>-<stamp>-<slug>-<arm>.<ext>   CARD-20260911T1150Z-caseworker-vibrobeast.md

- `FORM` is an upper-case prefix from the register (below). One prefix, never two joined by a
  hyphen: `MEMORY-SORT-2026-09-11.md` reads as prefix `MEMORY` with no date after it, and the check
  script says so.
- The date is `YYYY-MM-DD`, or `YYYYMMDD` where the form's home already writes it that way (the
  advice ledger's `ENHANCE-20261020-…` and `20261018-retro-…` records, as skilltank names them).
  Both are kept and the check accepts both: two homes each had a rule, and the house default for a
  tension where both work is to support both (his preference, 2026-10-09). Dispatched work (a card, a wave brief, a rendered view) uses the stamp
  form `YYYYMMDDTHHMMZ` so parallel arms cannot overwrite each other.
- The slug says what, in a few lowercase words. Dispatched work adds the arm at the end.
- The H1 repeats the form and the date in words, and the first section is the one the register's
  FIRST_SECTION column names for that form. A LENS opens with his hypothesis verbatim; a READ opens
  with the reader's stance and then the verdict; a FIX opens with what was wrong.
- If you cannot say which form it is, you are not ready to write it. Read the register's ANSWERS
  column until one question is yours.

## The register is the source of truth

The forms live in `c/wf` — a C4 register: TSV, no header row, one row per form, columns named in
`d/c/wf`: `FORM ANSWERS FIRST_SECTION SHAPE FIELDS PAIRS COUNT EXAMPLE NOTE`. Read it with the
columns by name (`paste d/c/wf` beside a row, or `awk -F'\t'`). This skill does not duplicate the
table. It lists the most-used forms and the one question each answers:

| form | answers |
|---|---|
| **NOTE** | What was ruled or learned this session, and what that changes |
| **LENS** | Does his hypothesis bear out when looked at through one deliberately chosen way of seeing |
| **CARD** | What one seat sees, or what one pair of hands must do, said small enough to hand across |
| **MODEL** | How does this thing work, drawn so a stranger can act on it before it runs |
| **PAPER** | What did we prove, and where did we fail to prove it |
| **DIAGRAM** | What does this structure look like as a picture, drawn from data rather than by hand |
| **WAVE** | What one dispatched arm is to do this wave, and what it must return to the runner |
| **VIEW** | What does a register look like right now, rendered for eyes |
| **DESIGN** | What should this thing be, written where a tool can find it, before it is built |
| **QAPLAN** | What would have to hold for this build to be done, written BEFORE the build |
| **TESTMANIFEST** | Which promises of this work have been shown able to fail, and which only pass (PROVISIONAL) |
| **PROMPT** | What exactly is pasted to start a run, so the run can be repeated |
| **CHARACTER** | Who is this actor, as possessed and shown, not claimed |
| **DIFF** | What replacement prose is proposed, against which readings, and why |

The rest — HYPOTHESIS, DELTAS, READ, PLAN, REFORMAT, FOLD, REPASS, RESEARCH, SWING, REVIEW, LEDGER,
CHECKPOINT, FIX, CITATIONS, DISS, SCORE, SEAL, QA, ENHANCE, and the thin ones — are rows in `c/wf`,
each with its SHAPE (frontmatter, headed-prose, table, tsv, json, mixed), its usual FIELDS, its
PAIRS, and a NOTE for anything load-bearing. Three forms carry no prefix and the register says so:
a **FACT** is named as its question under `facts/`; a **DECK** ends in `.deck.md`; a **REGISTER**
is `c/<name>` with its columns in `d/c/<name>`. Rows whose NOTE begins `[MINE]` were shaped from
the filename alone, not from an opened exemplar; treat them as proposals and fix them on the
form's next use.

## The GNU release forms (no prefix: GNU names the file)

A program meant for free-software readers ships five forms they already know how to read, and the
register has a row for each: **MANUAL** (a Texinfo manual in `doc/NAME.texi`: how a person uses the
thing, start to finish), **NEWS** (what changed for the people who use it, release by release),
**CHANGELOG** (what changed, file by file, written before each commit), **INSTALL** (how to build it,
install it with DESTDIR and take it off again), and **CLI** (what `--help` and `--version` say; not a
file, the program's own output). Like a FACT or a DECK, they carry no prefix and no date: the name is
the form, and `wf-check.sh` reads `NEWS`, `ChangeLog`, `INSTALL` and any `.texi` that way. The
examples are theseus's own (`doc/theseus.texi`, `NEWS`, `ChangeLog`, `INSTALL`, `python recipe.py
--help`). The nongnu-steward soft skill says what each must contain for a GNU review; kid-glove's kit
has the matching topics (manual, cli, install) for a house that has none.

## Six techniques that cut across every form

1. **Two piles.** Keep OBSERVED (what a source says, quoted, with its path and line or the command
   that produced it) apart from JUDGED (your reading, saying in words whose it is and citing its
   source; the old bracket tags, `[HIS]` `[DOMAIN]` `[SKILL]` `[PLATFORM]` `[MINE]`, were retired on
   2026-09-24). A MODEL says it in one line — "OBSERVED carries its command; JUDGED says whose it
   is" — and a QA card counts a JUDGED row that says neither as a silence. A concern that is only
   your own never blocks: offer it, name it in one line, and move on.
2. **Cite at the act.** Every claim names its source where the claim is made — `path:line` and the
   line quoted verbatim — not in a bibliography after. A CITATIONS floor opens every forward link
   during the pass; a DIFF re-verifies every tree-fact against the tree rather than taking the
   reader's word; a LEDGER row without a receipt says `[MINE]` and is a proposal, not a finding.
3. **A falsifier on every concern.** No concern without the one check that would dissolve it. A
   HYPOTHESIS has a check per row that can fail; a SWING has a falsifier per leg; a QA card renders
   a JUDGED row with no falsifier as "a feeling, labelled" and counts it. A concern you cannot
   falsify is still worth writing — as a feeling, labelled — but it does not gate anything.
4. **The pair rule.** Some forms are born beside another file, and the register's PAIRS column
   says which: a brief beside its output (a CARD or WAVE output has a `-brief.md` with the same
   stem, and the brief lands first), a twin beside a view (a VIEW `.html` has its `.txt` twin for a
   reader without a browser), a score beside a seal (a SEAL is opened by a SCORE; a SCORE with no
   SEAL beside it scored nothing sealed), a descriptor beside a register (`d/c/<name>`), a
   companion TSV beside a HYPOTHESIS, a `.sha256` manifest beside a DELTAS, a `.svg` beside a
   DIAGRAM. When you land one half, say where the other half is or when it will come.
5. **His words.** Where a deliverable carries Corwin's words, the record keeps them verbatim
   (typos and all, quoted, with where they came from), and any new wording sits beside them as a
   labelled reading, never in their place. New writing that builds on them may smooth and blend his
   wording; that is acceptable and often preferred. The licence stops at personal writing: text
   written *as* a person rather than about the work goes under a persona distinct from his, for
   contrast, so his own model stays something you can mention, illustrate, and begin to control for
   bias against. His ruling (execute-brief-lens-D5 = A, 2026-09-27), verbatim:
   > Note here is that smoothing my wording and belding it as we write new information is
   > acceptable, often preferred.  That assumes we aren't writing as personal however: there we
   > have the idea of stimulating a persona unique from mine for enhanced contrast and to make my
   > personal model more effective to mention, illustrate and perhaps even begin to control for bais.

   A prompt of his gets the full REFORMAT pair (reformat-prompt); this technique is the general rule
   that pair is one case of. Building the contrast persona itself is persona work, not a form.
   **Spelling: count the laps; fix it and park it.** A dated quote of a person is lap 0 and is kept
   byte for byte. Every later lap is ours: his words carried into our own prose, an identifier we
   minted, text we typed into someone else's file. Ours is fixed without asking. Asking is earned
   once, never several times, and only when the spelling is a live identifier others reference (a
   file, host or domain name, a tag), or the person defined or reused it on purpose. Interest never
   keeps an error in place without evidence of intent: fix it, and park the suggestive reading, with
   its source, in a parking lot (`advice/<run>/PARKING-LOT.md`). Spelling is an accessibility point
   first. His rulings, verbatim (2026-10-09 18:26, `c4 spells/extension/chapters/01-his-words.md`
   line 31, opening; and 2026-10-24 09:32, blessing the lap rule of `c4 h/NOTE-2026-10-24-spelling-laps.md`):
   > * fix the spelling, this is a point of accessibility as we have discussed a few times: absolutely critical to get that right in this context.

   > proposal loos very good: fix it and part is is perfect, allowing me to go full Dr. Sues *later*, when it isn't in the way of clarity toward an instruction that is actionable.  It make perfect sense to me that the writing-forms skill hosts the most strongly famed and each sharper of refinement around spelling and inventiveness.

   The second quote is lap 0 and shows the rule at work: it stays as typed here, and a reading beside
   it says "fix it and park it is perfect". Falsifier: a `git grep` of a parked spelling finds it in
   our own prose outside a quote.

6. **The reader's gain first.** Lead with what the reader can do with the thing; put who made it at
   the credits depth (copyright notices, AUTHORS, THANKS, a footer, a colophon). His words of
   2026-10-18: the work "should sing about itself (what readers gain), not about its makers". It can
   be measured: the kiosk's voice gauge, `tools/vo1ga` in c4-draw-kiosk (its words in
   `door/data/voice-words.tsv`, `tests/voice-peer.py` its second reader), counts the words a reader
   meets before the first thing they can press, and how often our own names appear. A page rewritten
   by this technique reads lower on both; one that reads no lower than before was not rewritten by it. The seam with kid-glove: its kit puts a
   persona line in the footer, and that is the credits depth, so the two agree on where; the person
   now outranks both, as kid-glove's order says.

## How a new form is born

- **Second use, then a row.** The first time a shape appears, it is a one-off and may carry any
  honest prefix. The second time the same question is answered the same way, it earns a row in
  `c/wf` — FORM, its one question, its first section, its shape, its fields, its pair — and the
  row is the moment the form exists. The tree already keeps this rule for other things ("Second
  use met", "Named on its third real instance").
- **Never a rival prefix for the same question.** Before minting a prefix, read the ANSWERS column.
  If a row already answers your question, use its FORM, even when your slug would read better with
  a new word. READ and READING both name a reader's report; the register marks the older one as the
  candidate rival, and the next reader's report is a READ.
- **Amend the row, do not fork it.** When a form's shape moves (a new usual field, a new pair), edit
  its row and say so in the file that moved it. The register is the atom; a VIEW of it is derived.
- **Thin rows are honest rows.** A form whose ANSWERS could not be derived gets a row with `-` in
  the columns nobody could fill and a `[MINE]` NOTE, or it is listed as absent in the CHANGES that
  built the register. A guessed cell is marked; an empty cell is never silently filled.

## The fence — notes other sessions wrote

Never edit a note another session wrote. Append a dated note instead, or write a new file that
names the old one and supersedes it. The shop found this fence mechanically — the memory seat
refuses a later session's append to exactly the notes other sessions wrote — and keeps it by
habit everywhere else: a PAPER v2 leaves v1 unedited as the record; a REPASS does not touch the
original and carries a receipt saying so; an ENHANCE tree reclasses the queue but does not replace
it, because editing the queue would break the DELTAS manifest that hashed it; a CHECKPOINT is
self-contained rather than appended to the shared ledger, to avoid a parallel-session collision;
a RUNCARD is superseded, never edited. A signed file (`.asc` beside it) does not freeze it either:
edit the full text, write down that you did (the express manifest, a SIGN-QUEUE row), and say nothing
more — whether it is re-signed is decided at the door, by him, when a named reader relies on it; a
stale `.asc` beside an edited file is the honest state, and *the general answer to signature drift is
a gauge, not a guard on every edit* (his norm, 2026-09-10). The fence is about authorship, not
signatures.

## The check — `scripts/wf-check.sh`

    sh scripts/wf-check.sh h/CARD-20260911T1150Z-caseworker-vibrobeast.md
    sh scripts/wf-check.sh --prove-red

Given a path, it prints the prefix, the form and its ANSWERS, the register's pair rule, and whether
the pair sits beside the file — then a verdict: `OK`, `PENDING` (a pair that lands later, such as a
SEAL's SCORE), or `RED` with the reason (unshaped name, no date after the prefix, unregistered
prefix, pair absent). Exit 0, 0, 1; exit 2 when the register cannot be read. `WAVE1` resolves to
`WAVE` because the digit rides that prefix. `--prove-red` runs the mutants and the green controls
together: an unregistered prefix must go RED, a CARD without its `-brief` must go RED, a VIEW
without its `.txt` twin must go RED, and the controls beside each must stay green; it exits 0 only
when every case behaves. Point `WF_REGISTER` / `WF_DESC` at another copy of the register to check
a different shop. The script measures and never repairs: it does not rename, does not create the
missing half, and does not add a row.

## Who else touches this and how it divides

- **rolls** owns the report kinds (close/roll, intake, situation, dashboard) and their four guards;
  its "kind · answers · first section" table is where this register's ANSWERS and FIRST_SECTION
  columns come from. INGEST and CLOSE rows point back to it.
- **reformat-prompt** owns the REFORMAT pair (verbatim + reading + heal + taxonomy); the row here
  only says that form exists and what it opens with. Technique 5 is the general rule; the pair is
  its worked form for a prompt.
- **run-card** owns RUNCARD; **skill-creator** owns skills; **eclipse-pass** owns the PASS ritual.
  This skill names the form and hands over.
- **verify-say** owns the words for any claim that a file is signed or verified; a SEAL or SCORE row
  says the hash is checked, verify-say says how to say it.
- **posix** owns the shell discipline the check script follows (`dash -n`, a `--prove-red` with a
  negative twin for every positive control).

## How this skill can fail (falsifiers)

- A dated deliverable lands with a prefix that is not in `c/wf` and nobody notices: run
  `sh scripts/wf-check.sh` on the file — `RED (unregistered prefix)` means the skill did not fire
  or was ignored.
- Two rows in `c/wf` answer the same question in different words: `cut -f2 c/wf | sort` and read
  neighbours — a duplicate means the "never a rival prefix" rule did not hold and the rows should
  merge.
- A form's first section drifts from FIRST_SECTION for three files in a row (`head -15` of each):
  either the register row is stale and should be amended, or the skill is being applied without
  reading the register.
- The skill fires on a file that is not a dated deliverable (a tool, a fact, a register row) and
  demands a prefix: the check script's `RED (unshaped name)` on `ferry_core.py` is correct only if
  that file was meant to be a deliverable — for tooling it is noise, and the skill should not have
  fired.
- His words drift: a deliverable quotes him, and the quote does not match its source byte for byte
  (`grep -F` the quoted line in the cited file), or a smoothed wording stands where the record
  should hold his. Either means technique 5 was skipped.
- A manual, NEWS, ChangeLog or INSTALL lands in a tree nongnu-steward tends and `wf-check.sh` cannot
  name its form: the GNU rows or their name rules are missing (this was the case until 2026-10-20).
- Off-switch: say "no form, just write it" (or "scratch") — the skill applies to prefixed, dated
  files, to the GNU release forms by their names, and to `facts/`, `decks/` and `c/`, and to nothing
  else.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.3: edition revised from 1.2 on 2026-10-24; spine: 2026-08-09.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
