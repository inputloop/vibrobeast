---
name: countable-gauge
description: >
  Measure, don't assert. Cheap standing ratios that catch analysis wearing a write-up jacket — a document that mentions frameworks 58 times and hands the reader zero things to try. Use it before calling a document, report, guide, README, review, or skill "useful", "accurate", "careful", "thorough" or "improved"; when comparing a draft to its rebuild and wanting the delta as a number, not a feeling; on "is this doc any good", "did that rewrite actually help", "prove it's better", "how would we measure that", "measure don't assert", "what's the ratio", "is this analysis or is it advice". Also for a claim with no second witness (dagger it), or when you'd be grading your own writing by re-reading it. Ships gauge.sh + a gauges.tsv you edit; it prints counts and ratios, never a verdict or threshold — a threshold picked-not-validated is the same fault the gauge exists to catch. Not a linter or readability score — it counts what you told it to and leaves judgement to you.
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-09-04
  c4_source: c4/q/retention/palace/pins-prove.md (countable-gauge, two-source-dagger)
  c4_born_of: the drift-dashboard and TrueNAS rooms, 2026-09-03 palace crawl
  c4_ships_tool: scripts/gauge.sh + gauges.tsv + fixtures/ + tests.sh
---

# countable-gauge — turn a vibe into a number before you spend it

The failure this exists for has a shape you can see once and never unsee: a document that
**explains** at length and **affords** nothing. It names the framework, the model, the paradigm, the
architecture — and never once tells the reader a thing to do. It reads as rigorous. It is analysis
wearing a write-up jacket, and re-reading it will not tell you, because re-reading is exactly the
instrument that was fooled the first time.

The measured case: one document scored **58 framework-mentions per reader-affordance** (58 mentions,
zero "Try this"). The rebuild scored **3.0**. Nobody's opinion changed between those two numbers —
the document did.

## The move

Before you assert a document is useful, accurate, careful, or improved: **name the ratio that would
show it, then print the ratio.** If you cannot name one, the assertion is a feeling, and you should
say so rather than dress it up.

This is `tools-prove` made portable, and it is the PROVE face of
[[pencil-your-own]] — your own read of your own draft is the class most likely to be your error, so
it is the layer that gets a number put under it.

## What the tool refuses to do

`gauge.sh` prints counts and ratios. It does **not** print a verdict, a grade, a pass/fail, or a
threshold — and that refusal is load-bearing, not modesty:

- **A threshold picked-not-validated is a smell**, and it is the *same* smell the gauge exists to
  catch. If I baked "under 5.0 is good" into the tool, I would have inked my own guess into the
  instrument that measures guesses.
- **The scale is data.** `gauges.tsv` holds every pattern. Strike a row and a gauge disappears; add
  one and it appears; neither needs the tool's agreement. Borrowed straight from
  `h/m0ve-ink.tsv`'s own reasoning.
- **A number is not a conclusion.** 58.0 is not "bad" — it is *58 mentions and no affordances*, and
  what that means depends on whether you were writing a reference or a guide. The tool hands you the
  fact; you keep the judgement.

## Using it

```
sh scripts/gauge.sh DOC.md                 every gauge: numerator, denominator, ratio
sh scripts/gauge.sh --compare OLD.md NEW.md   the delta, which is the number you actually wanted
sh scripts/gauge.sh --list                 the gauges currently in force
sh tests.sh                                fixtures vs expected counts
sh tests.sh --prove-red                    prove the harness can fail
```

**`INF` is the interesting result, not an error.** A denominator of zero means the document affords
the reader *nothing at all* on that axis. That is the 58/0 case, and it is the loudest thing this
tool can tell you — so it prints `INF` and marks the row, rather than hiding a division.

## The gauges that ship

Each is a pair of counted patterns. All four came from real rooms, not from imagination:

| gauge | numerator | denominator | what a high number means |
|---|---|---|---|
| `framework-per-affordance` | framework / model / paradigm / architecture / methodology mentions | things to *do* — "Try this", a fenced block, a numbered step, a shell prompt | you are describing a system to someone who wanted to use one |
| `claim-per-citation` | asserting sentences (is / are / must / always / never / will) | citations — a path, a URL, a year, a backticked file | confidence outrunning its sources |
| `believed-per-observed` | `BELIEVED` / "I think" / "presumably" / "should be" | `OBSERVED` / "I ran" / "the output was" / a command receipt | judgement entering the record in an observation's clothes |
| `unwitnessed-claim` | single-sourced marks (`†`, "single-sourced", "only source") | independent second witnesses ("confirmed by", "second source", "cross-read") | claims standing on one leg — mark them or find the witness |

The last one is the **two-source dagger** as a countable thing: when most of a document's claims have
no second witness, mark them `†` rather than implying earned confidence. A wrong correction is worse
than the original error, so a correction must itself clear the two-source bar.

## Reading a comparison honestly

`--compare` is the mode that earns its keep, because a single number has no scale but a **delta**
does. Two cautions worth keeping in your head, both learned the hard way:

- **A gauge you can game is a gauge you will game.** If you know the tool counts "Try this", you can
  sprinkle "Try this" and move the number without helping anyone. The gauge is a smoke alarm, not a
  grade — its job is to make you *look*, and it cannot make you honest.
- **A gauge that never moves is telling you something too.** If a rewrite you believe improved a
  document leaves every ratio flat, either the improvement was elsewhere (fine — say where), or it
  was a feeling (also fine — say that).

## Interlocks

- [[pencil-your-own]] — the trait this is the PROVE face of; `unwitnessed-claim` is its dagger,
  counted.
- [[seams]] — the parent law for the two-source rule: one representation of one truth that can
  silently split.
- [[prove-a-promise]] — a gauge is the *specific* half of an XX pair when the universal half is a
  round-trip.
- [[eclipse-pass]] — run a gauge before and after a pass; a critique that moves no number is a
  critique you should be suspicious of.
- [[verify-say]] — owns the wording once you have the number.

## Provenance

The gauge family was noticed on the 2026-09-03 palace crawl and logged in
`c4/q/retention/palace/pins-prove.md`. The 58.0 → 3.0 measurement is from the drift-dashboard room;
the two-source dagger from the TrueNAS/David review. **Both of those are single-sourced from session
transcripts — no file on disk witnesses them**, which is why this skill's own claim about its origins
carries the dagger it ships. Mint status: unblessed, nothing installed.

## Land it before you show it

Write the result to a file before showing it, and head the file with one line:
`produced-by: countable-gauge · subject: <path or name> · sha256: <the subject's> · <UTC date>`. Used alone,
that line is a comment and nothing more; a shop that indexes its work can find the result by it
(ERRATA E19, 2026-09-29).

## How this skill can fail (falsifiers)

- **A verdict crept in.** fails if `gauge.sh` prints PASS, FAIL, good, bad or a threshold; check: `sh scripts/gauge.sh fixtures/jacket.md | grep -Eic 'pass|fail|good|bad'` prints 0.
- **Counts drifted.** fails if a fixture's counts differ from `fixtures/expected.tsv`; check: `sh tests.sh`, then `sh tests.sh --prove-red`.
- **INF hidden.** fails if a document with no affordances prints a finite ratio or an error; check: `printf 'The framework and the model.\n' > /tmp/x.md; sh scripts/gauge.sh /tmp/x.md` shows `INF`.
- **Gamed.** fails if a rewrite moves `framework-per-affordance` while a reader finds nothing new to do; check: `--compare OLD NEW`, then read the new affordances by hand.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-03.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
