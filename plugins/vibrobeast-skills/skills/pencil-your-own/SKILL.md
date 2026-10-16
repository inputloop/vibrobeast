---
name: pencil-your-own
description: >
  A design rule for the move that recurs wherever judgment meets a record — own-error-is-the-relaxable-layer: make the layer most likely to be YOUR error the one that relaxes, gets marked, or gets made explicit; never the layer you defend hardest. Ink the world's facts; pencil your own reasoning. Use it before you block, gate, sign, correct, or caution on your own inference; when a claim has no independent second witness; when deciding what a dial or review may relax; when a "concern" is about to stop work; and on "whose rule is this", "is that my error or the world's", "should I flag or proceed", "mark it or hold it", "pencil it", "HOLD not HARM", "single-sourced", "am I over-blocking". The three refusals keep it honest: pencil only what is YOURS, never another party's ink, never the safety floor — it relaxes CONFIDENCE, not the floor. Not a license to be less careful. Not eclipse-pass (stress-tests a claim); not consent-gate (verifies authority).
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-09-04
  c4_source: c4/q/retention/palace/pins-flip-the-script.md (own-error-is-the-relaxable-layer)
  c4_born_of: the 2026-09-03 Planning-Palace crawl; five rooms, one move
  c4_ships_tool: scripts/pencil.sh + fixtures.tsv + tests.sh (doctrine does not ship without its tool)
---

# pencil-your-own — the layer that relaxes is the one most likely to be yours

**One line:** *Ink the world's facts; pencil your own reasoning.*

The instinct, when you have reasoned carefully, is to defend that reasoning hardest — it cost the
most, so it feels the most load-bearing. That instinct is backwards. Of everything in a record, your
own inference is the class **most likely to be the error**: the world's facts have witnesses, a
stated rule has an author, a domain law has a literature — your inference has you. So the cheapest
safety available is to make **your own layer** the soft one: the layer that a dial can relax, that a
mark can flag, that a reader can falsify.

This is Corwin's "floor we are standing upside-down on," read right-side-up. The
[[governance-lineage-walk]] says *ground an objection in a traceable lineage*. This says **and the
rung you relax first is your own.**

## Why it earns a skill: five rooms, one move

The move was not designed — it was **found**, converging independently in five unrelated pieces of
work in one crawl (2026-09-03). That convergence is the evidence; a rule invented once is a
preference, a rule that five separate problems arrive at is structure.

| face | what gets penciled | what it relaxes | witnesses |
|---|---|---|---|
| **m0ve's ink levels** | your analytic claims | a *tension* stops gating once reality `r < 1 − level` | 2 — `h/m0ve-ink.tsv` + `h/DESIGN-2026-08-29-m0ve.md` |
| **The Sweep Rule, clause 3** | a concern tagged `[MINE]` | it *offers*, never blocks — proceed-and-name | 1† — `standalone-answer.md`; † the second witness, the installed global CLAUDE.md, was removed 2026-09-23; its text is kept at `c4/tmp/2026-09-23-keep/global-CLAUDE.md` and the rule now rides as a door part under `c4/d/door/` |
| **values-baseline** | your grounds for exclusion | excludes **behaviors, never identities**; disclosed-but-unenforced reads **HOLD, not HARM**, and stays reopenable | 2 — the skill + its canon deck |
| **edrx / signage** | the structure you were holding implicitly | made **explicit and reachable**, so a stranger can falsify it | 1 † — session only |
| **two-source dagger** | a claim with no independent second witness | marked `†` rather than stated with earned confidence | 1 † — session only |
| **the scale is data** | the instrument's own thresholds | levels live in a **file the operator edits**, not a regex inside the tool | 2 — `h/m0ve-ink.tsv` header + `h/claim-words.tsv` |

`†` marks a face I could source only from a session transcript, not from a file on disk. That is the
skill obeying its own rule in its own front matter: I did not upgrade my confidence to hide that the
witness is single. If you find the file, strike the dagger.

**The sixth face is the sharpest and the easiest to miss.** From the `m0ve-ink.tsv` header, in the
shop's own words: *"if I picked the scale inside the instrument I would be committing the fault the
instrument measures."* A tool that hard-codes its own thresholds has quietly inked its author's
judgment — the one layer that should have stayed in pencil. So the scale is a data file the operator
can strike a row from, and neither the addition nor the strike needs the tool's agreement.

## The discriminator — is it yours, or is it the world's?

Everything turns on this, and it is the step people skip. Before you relax anything, answer **who
holds the ink**:

- **The world's** — a measurement, a command's output, a file's bytes, a published law of the
  domain. It has a witness that is not you. *Ink it.*
- **Another party's** — Corwin's stated rule, a signed record, a third party's data, a skill's
  written canon. Not yours to soften. *Ink it, and route the question to whoever owns it.*
- **Yours** — an inference, a threshold you chose, a pattern you noticed, a caution you feel, a
  correction you are about to make. *Pencil it.*

The tell that you have mis-sorted: you find yourself defending a rule you cannot cite. Provenance
says **who to ask**, never **what the answer is** — so if the trace ends at you, that is not a
weaker claim, it is a claim with a different disposition: it proceeds and it gets named.

## The three refusals (the fence that keeps this honest)

A move that relaxes things is one bad step from an excuse. These are what stop it, and they are the
reason this skill is safe to install:

1. **Only what is yours.** You may pencil your own inference. You may **never** pencil another
   party's ink — not Corwin's rule, not a signed record, not a domain law. Softening someone else's
   claim so your work can proceed is the exact abuse this move enables, and it is refused.
2. **Never the floor.** The enumerated safety floor does not relax at any reality level, for any
   source tag, ever. `[MINE]`-never-blocks governs concerns about *quality, policy, taste, and
   rigor* — it says nothing about the safety floor, which is always-on and not electable
   ([[tool-lifecycle]]'s guard-sorting). A `[MINE]` tag on a floor item is a mis-sort, not a licence.
3. **Marked, not deleted.** Penciling is a *disposition*, not a disappearance. The claim stays in
   the record, carrying its mark, so a reader can pick it up later. A relaxation that leaves no
   trace is just a silent drop, and silent generalization is the miss, not the safeguard.

If you cannot say which of the three you checked, you have not applied this skill — you have used
its name to feel better about proceeding.

## Proving you applied it (the XX pair)

Per [[prove-a-promise]], one universal check times one implementation-specific check:

- **Universal — the relaxation is recorded.** Diff the record before and after. Every item you
  relaxed still appears, now carrying its mark (`†`, `pencil`, `[MINE]`, `HOLD`). If an item is
  *gone* rather than *marked*, refusal 3 fired and the pass failed.
- **Specific — a negative control that goes red.** Run a case where the move's advice is *wrong* and
  confirm the check refuses it. If nothing in your fixtures can go red, you have a slogan, not a
  check. Three reliable red cases ship with this skill: a floor item tagged `[MINE]`, an item whose
  owner is not you, and a numeric literal where a level word belongs.

## The check that ships with it

Doctrine does not ship here without its tool. `scripts/pencil.sh` is POSIX `sh`, stdlib only, and it
**never fills its own verdict** — you declare the facts about a concern, it applies the rule and
prints the disposition with the sentence that produced it.

```
sh scripts/pencil.sh fixtures.tsv          # verdicts for every row
sh scripts/pencil.sh fixtures.tsv -r 0.5   # at half reality: which tensions stop gating
sh scripts/pencil.sh --rules               # print the rule ladder, in order
sh tests.sh                                # 1 run: fixtures vs expected verdicts
sh tests.sh --prove-red                    # prove the harness itself can FAIL
```

**Record shape** — one concern per row in `fixtures.tsv` (tab-separated):

| column | values | meaning |
|---|---|---|
| `id` | any token | how you cite this concern |
| `source` | `HIS` `DOMAIN` `SKILL` `MINE` | the lineage rung it traces to |
| `owner` | `me` `corwin` `third-party` `world` | who holds the ink |
| `floor` | `yes` `no` | does it trace to an enumerated safety floor? |
| `witnesses` | integer | independent sources, **not counting you** |
| `level` | a word from `levels.tsv` | how firmly it is drawn — **a word, never a number** |
| `falsifier` | text, or `-` | the one check that would dissolve it |
| `note` | text | what it costs and buys |

**The rule ladder** (first match wins — the order is the whole design):

1. `floor = yes` → **FLOOR** · does not relax, at any reality, for any source tag. Refusal 2.
2. `owner ≠ me` → **NOT-YOURS** · another party's ink. Route it; do not soften it. Refusal 1.
3. `source ≠ MINE` → **HOLD** · the record is yours, the claim is not. A law you restated is still
   the law, and it may legitimately stop the work. Ask the party the tag names.
4. `falsifier = -` → **FEELING** · no check that could fail it. Label it and move.
5. `witnesses ≥ 2` → **STANDS** · two independent witnesses, not counting you. Nothing of yours is
   left to relax; state it plainly, without the dagger.
6. otherwise → **PENCIL** · yours, single-sourced. Proceed and name it in one specific line, marked
   `†`. This is the common case, and it is the one the reflex gets wrong.

**Why FLOOR is checked first, and FEELING fourth.** The obvious ordering — "is it even a concern?"
before anything else — is a trap: it lets a safety-floor item be dismissed as a *feeling* merely
because nobody had named a falsifier for it yet. Absence of a falsifier is a fact about your
paperwork, not about the floor. So the floor is settled before the ladder is allowed to dismiss
anything, and `FEELING` is reachable only for claims that are already established as yours. The
first draft of this skill had the two reversed; running the fixtures is what caught it.

**Why a word and never a number in `level`.** `levels.tsv` carries the scale and the tool refuses a
numeric literal, telling you which word you meant. This is the sixth face applied to this tool: the
scale is data the operator edits, so my choice of thresholds is never quietly inked into the
instrument. Strike a row and a level disappears; add one and it appears; neither needs my agreement.

## When *not* to reach for this

- **You are stress-testing whether a claim holds at all** → [[eclipse-pass]]. This skill sorts a
  concern's disposition; it does not test the claim's truth.
- **You are asking whether an action is authorized** → [[consent-gate]]. Authority is never
  penciled.
- **Two representations disagree and you need to know which is evidence** → [[seams]].
- **You want the wording for a signature or verification claim** → [[verify-say]].
- **The concern is about a person rather than a behavior** → [[values-baseline]]; exclusion that
  names a person is the thing we refuse to build, and no amount of penciling changes that.

## Interlocks

- [[ethicsminions]] — the watch that raises concerns; this skill sorts which of them may stop work.
  The minions' notices are `[MINE]` by construction unless they cite a rung, so this is where their
  output lands.
- [[values-baseline]] — supplies the behavior-not-identity face and the HOLD-not-HARM disposition.
- [[eclipse-pass]] — its "keep the losing models" is this move in the critique register: the losers
  stay in the drawing (`faint`), they are not erased.
- [[prove-a-promise]] — the XX pair above.
- [[tool-lifecycle]] — guard-sorting; supplies the always-on safety floor that refusal 2 protects.
- [[seams]] — the two-source dagger's parent law.
- [[mentat-skill]] — where a penciled item's mark gets written down so it survives the session.

## Provenance

Found, not designed: the convergence was noticed on the 2026-09-03 Planning-Palace crawl and logged
as the strongest ENHANCE candidate in `c4/q/retention/skilltank-candidates.md`. The GOV face is
detailed in `c4/q/retention/palace/pins-flip-the-script.md`, the PROVE face in
`palace/pins-prove.md`, and the SEAM sits in `palace/semaphores.md` with
`governance-lineage-walk` as its came-from. **Mint status: unblessed.** No live skill was edited to
create this; the proposed ENHANCE patches for `ethicsminions`, `values-baseline`, and `eclipse-pass`
sit beside it in `ENHANCE-NOTES.md`, unapplied, for Corwin to take or strike.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-29.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
