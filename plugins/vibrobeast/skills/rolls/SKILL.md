---
name: rolls
description: >-
  Draft and render report kinds over a tree that keeps its work in registers or folders — the
  session close/roll report, the intake report, the situation report, and the dashboard. Use
  whenever a report is written or asked for — "close the session", "roll report", "what did we
  touch", "intake this drop", "show dashboard", "situation report", "summarize what changed" —
  even when "report" is never said. Four guards ride along: a report tool never fills its own
  verdicts; UNSET verdicts are counted in the totals; status is never hue-only, contrast is quoted;
  the house structure is electable. STUB / carrier seed. Not session-rotate, not instrument-panel,
  not pmo, not verify-say (signature/verification wording and state vocabulary — this skill
  delegates every signing-shaped sentence to it by name: SIGN/DETACH/NOSIG/FURNITURE, PANEL-FAULT).
metadata:
  stub: true
  cut: "2026-08-10"
  origin: "C4 · eclipse verdict .eclipse-increments/2026-08-10-rolls"
  replant: "toward poly, after the local ON turn and AS4CE/AC4CE0001"
  revision: "1.2 — 2026-08-17, at Corwin's request: same extraction as 1.1, but guards 3 and 4 name verify-say's vocabulary inline (SIGN/DETACH/NOSIG/FURNITURE + PANEL-FAULT) rather than pointing at it in the abstract, and the kinds table gains a worked example. Deeper interlock than 1.1; pick this one only if you also land verify-say v2 (the version that carries that vocabulary), or the inline names will dangle."
  self_test: "scripts/check_vocab_sync.py — read-only; run against verify-say's SKILL.md to catch state-name drift before it goes stale silently. Added 2026-08-17 at Corwin's request."
  revision_1_3: "1.3 — 2026-09-11 (o73, c/en): the kinds table gains the report card (QA) kind and names its generator, c4/bin/et1cd. Text otherwise byte-identical to the installed 1.2; this file is now the source of record on the tree (c4/skills-mint/2026-09-11/rolls), since 1.2's source was not on any mounted folder."
---

# rolls — report kinds, and the four guards that keep them honest

**This is a STUB.** It is a carrier seed: the transplantable part of a discipline that grew in one
shop (C4) and is meant to be replanted elsewhere. It carries structure and guards; it does not carry
that shop's vocabulary, and it deliberately does not claim a finished lane. Cut 2026-08-10 from four
receipts, under an eclipse pass whose four required softenings are all visible below.

## Why a report kind is worth a skill at all

A report is where work becomes *legible to someone who was not there* — a keeper coming back, a
collaborator receiving a drop, a stranger auditing later. That makes it the place where a small
dishonesty does the most damage: an unverified thing described as verified, a silence that reads as
a pass, a color that carries meaning to people who can see it and nothing to people who cannot.

The four guards below all exist because each one was violated somewhere first. They are cheap to
keep and expensive to have skipped.

## The four guards

### 1. A report tool never fills its own verdicts

If the thing that gathers the evidence also scores it, the score is worth nothing. Census, counts,
hashes, presence, sizes — mechanical, and a tool should do all of it. Judgment — is this good, is
this safe, do we accept it — belongs to a person or to an independent seat, and the report should
leave those slots **UNSET** rather than guess.

*Why this is not laziness:* a forensic tool that scored its own evidence would be inadmissible, and
release pipelines have shipped broken artifacts precisely because a wrapper quietly certified itself.
The blank is the honest output.

### 2. Count the UNSET verdicts in the totals

The obvious failure of guard 1 is that UNSET ships unfilled forever. So make the emptiness visible:
report *"4 of 4 verdicts UNSET"* in the same summary that reports file counts. A silence that gets
counted stops being a silence.

### 3. Never claim a check you did not run — say what you attempted

Distinguish, always, between **absent**, **present but unverified**, and **verified**, for any check
a report references without having run it. Write what state you found, write `NOT ATTEMPTED` for the
check itself, and print the exact command the reader can run to settle it themselves.

**When the check is a signature or attestation**, don't improvise the wording here — use
`verify-say`'s vocabulary directly: `SIGN` / `DETACH` / `NOSIG` / `FURNITURE` for anything on a
governed shelf, the generic three states otherwise, and `PANEL-FAULT` (never a bare "verified") if
the checker itself hasn't cleared its own canary check first. This skill does not carry that
vocabulary — it names it so a writer reaches for the right skill instead of re-deriving it.

**Drift guard.** Naming those tokens inline is a coupling, not a footnote: if verify-say ever
renames or drops one, this file goes stale and nothing says so — unless you run
`scripts/check_vocab_sync.py`, which greps verify-say's SKILL.md for exactly the five tokens named
above and exits non-zero (loud, not silent) the moment any go missing. Read-only, measures only,
never repairs — same discipline as shelf-check and instrument-panel. Not wired to any hook; you (or
a run-card, or a CI step) have to actually invoke it.

This generalizes past signatures: whenever a report cannot check something, print the *attempt* and
the *reason*, never the assumption. "I could not see this" is a finding; "this is fine" is a claim.

### 4. Measured color, and never status by hue alone

If the report renders (HTML, a page, a dashboard), compute the contrast ratios rather than eyeballing
them, and **quote the numbers in the artifact itself** — a comment in the stylesheet is enough. A
number is reviewable; a vibe is not. Consult the `color-theory` skill for the math; this skill does
not reimplement it.

And every colored status token also carries its **word** — `[ UNSET ]`, or for a signing token,
whichever of `verify-say`'s named states applies — because roughly one reader in twelve will not
receive the hue at all. Add a dark palette that is *measured*, not inverted, and a
`prefers-contrast: more` step. Forcing light on a reader who asked for dark is its own barrier.

## The structure — a default you may elect against

The house shape is: **by-container touch summary first, weight/impact close last.**

- **Part A — by container.** One section per register, folder, or artifact class touched, each with
  its rule or its pending state. Repeat as needed. This comes first because *where* something landed
  is what a returning reader needs before *how much* of it there was.
- **Part B — the close.** Files, weight (lines or bytes), and impact, as a table, plus the receipts:
  what verified, what ran green, what is owed.
- **Openings as well as hazards.** Reserve a section for what became *possible*, not only what went
  wrong. A report that only ever names risk trains its readers to dread it.

**This structure is electable.** It has survived exactly two report kinds so far; that is a
transfer test, not a canon. If a kind fits better another way, use the other way and say why —
adoption nobody mandated is the only evidence that would ever earn the word canon.

## Kinds this seed already covers

| kind | answers | first section |
|---|---|---|
| close / roll | what did *we* touch this session? | by register |
| intake | what *arrived*, what does it claim, what does it ask of us? | by artifact class |
| situation | where do things stand right now? | by open question |
| dashboard | what should I look at first? | by urgency |
| report card (QA) | is this thing someone made sound, and what exactly did I check? | files under review (sha/bytes), then OBSERVED apart from JUDGED |

The report-card kind has a generator: `c4/bin/et1cd FINDINGS.tsv` (columns by name from
`c4/d/qa`; `--template` for an empty sheet, `--prove-red` for its mutants). Added 2026-09-11 after
the same card was hand-set three times on 2026-09-04 (`AS4CE0001/h/QA-2026-09-04-*.md`). It keeps
the four guards mechanically: GRADE is copied never filled, UNSET and NOT-ATTEMPTED are counted,
the files table prints the command it ran, and a `[MINE]` row graded `block` is refused.

Worked example (guard 3 + 4 together): a session-close report over a signed shelf says, per file,
one of `SIGN` / `DETACH` / `NOSIG` / `FURNITURE` — never a bare "signed" — with the word rendered
next to its color, and the exact `sign.sh check-shelf` invocation printed once at the top so the
reader can re-run the whole sweep themselves.

An intake report has one extra duty: the drop belongs to someone else, so findings about it are
things to say *to them*, plainly and early — as an opening, not a gotcha — with the command that
lets them check it themselves.

## Replanting notes (read before growing this past a stub)

- **Reconcile with the incumbent.** Most trees already have *something* that renders status. Find it
  first; folding into it is usually better than a rival. This seed was cut in a shop where a
  situation-report script already existed, and that reconciliation is still owed.
- **Bundle the script once you have two.** The moment two kinds share rendering code, that code
  belongs in `scripts/` here rather than being rewritten per kind.
- **Give every positive control a negative twin.** If the report has a self-test, "a known-good case
  passes" is only half of it; "a known-bad case fails" is what proves the test can fail at all.

## What moved, for anyone diffing against v1

Guard 3 and guard 4's signature examples were extracted to `verify-say` (see 1.1's changelog for the
verbatim move). This 1.2 goes one step further than 1.1: instead of a generic pointer, it names
`verify-say`'s specific states (`SIGN`/`DETACH`/`NOSIG`/`FURNITURE`, `PANEL-FAULT`) inline, and adds
a worked example. That's a tighter coupling — if `verify-say`'s state names ever change, this file
needs a matching edit. 1.1 doesn't have that exposure; pick 1.1 if you'd rather rolls stayed
loosely coupled to whatever vocabulary verify-say lands on.

1.3 (2026-09-11) adds one row to the kinds table — the report card (QA) — and the paragraph naming
its generator. Nothing else moved; `diff` against the installed 1.2 shows those lines only.

## How this skill can fail (falsifiers)

- **The vocabulary drifted.** fails if verify-say drops or renames a token named here; check: `python3 scripts/check_vocab_sync.py` prints 5 of 5 and exits 0.
- **The gatherer filled its own verdicts.** fails if a report's judgment slots are filled by the tool that gathered the evidence; check: the totals line counts the UNSET verdicts ("N of N verdicts UNSET").
- **A check claimed, not run.** fails if a report says verified with no command output behind it; check: each such line has a receipt, or reads `NOT ATTEMPTED` with the command.
- **Status by hue alone.** fails if a colored status token carries no word; check: read the rendered status tokens with color off, and quote the contrast ratios from `color-theory`.
- **The sync check went quiet.** fails if `sh tests.sh --prove-red` does not end `PROVE-RED OK`; it plants drifted verify-say pages (a dropped token, SIGN renamed SIGNED) and breaks the script five ways.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-10.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
