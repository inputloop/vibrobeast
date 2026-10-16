---
name: values-baseline
description: >
  A design rule for the VALUES-baseline test — the strict inverse of a permissive "does this fit?"
  baseline. Where an inclusive baseline (CORWIN) is competent only at INCLUSION (it says yes when
  SOME reading traces to principle), the values-baseline is competent at EXCLUSION: it passes only
  when a native reader, holding ONLY the stated principles and the fully disclosed trail — no
  withheld ingredient — can independently retrace the thing to a named principle. If the trace needs
  something the author kept back, it reads HOLD/HARM, not OK. Use it whenever deciding whether to
  trust or admit a persona, a custom config, a values statement, a governance or policy change, or
  any "it aligns with our principles" claim you'd rather verify than accept; when you need to catch
  who or what will NOT get along, not just confirm who fits; or when an approval rests on a
  charitable reading you want to stress with an adversarial one.
metadata:
  c4_deck: values-baseline
  c4_source_deck: decks/values-baseline.deck.md
  c4_source_sha256: 11c3d274a1a6477657689f3e75ebac5d16b01f157a802f727609e803ac768618
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# The values-baseline — competent at exclusion

An inclusive baseline is built to say *yes*: it admits anything for which *some* reading traces back
to principle. That's the right shape for a universal welcome — but it can't tell you who won't get
along, because no finite set of readings proves that *no* good reading exists. The values-baseline is
its inverse. It exists to find the cases the welcome can't screen.

## The inversion: ∃ → ∀

- Inclusive baseline (∃): passes if **some** trace to principle exists. Blind spot: false positives —
  reads OK when it shouldn't.
- Values-baseline (∀): passes only if a trace to principle is reachable with **no withheld
  ingredient** — nothing the author had to keep back to make it look aligned.

The tell is the *invertible-as-used* case: a transform of a load-bearing thing can read OK through
the permissive baseline, yet HOLD/HARM to a native reader who can't get back to principle without an
ingredient that was withheld.

## The XX pair for values

Prove it with two checks:
1. **A withheld-ingredient probe** (universal) — try to retrace to a named principle using only what
   was disclosed. Outcome on failure is **HOLD, with a name** for what's missing — not a silent FAIL.
2. **A native-reader oracle** (the impl-specific half) — the retrace is done by a reader holding only
   the principles + trail, *not the author*. You can't grade your own homework; alignment you assert
   isn't alignment a stranger can reach.

## The fenced loss (keep it restricted)

A *published refusal condition* is the direct fix for the inclusive baseline's blind spot — and it's
exactly the mechanism a welcome-first design must be careful minting. So fence it: it may rest on
**behavior and traceability, never identity**, and it closes **no permanent exclusion** and no avenue
to re-prove a claim. Exclusion that names a behavior and stays reopenable is a guard; exclusion that
names a person is the thing we refuse to build.

*Refined from the C4 canon deck `values-baseline.deck.md` (see `metadata`; `c4_source_sha256` names
the exact canon version). The inverse-twin of the CORWIN inclusive baseline (Q3 canon).*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
