---
name: layered-assurance
description: >
  A design rule for assurance when you CANNOT fully enforce or inspect what code does — the
  observation-first answer to "however sandboxed." A cumulative ladder: L1 count-the-cards (diff or
  re-hash what you declared must-not-change — a weak-but-honest floor); L2 pin the brutally-simple
  pieces (awk/sed) to a known-good release and declare your moves out loud; L3 expose every run-level
  of the real lifecycle (configure / make / install / setup / self-test / enablement) as signals;
  L4 substitute your own implementation to optimize or test. Use it whenever you can't sandbox
  something completely and need a real (if weak) guarantee; when proving nothing changed that
  shouldn't have (diff two trees, re-hash a manifest); when deciding how much assurance to layer on;
  or when a tool never "graduates" toward more assurance — that non-graduation is itself a smell.
metadata:
  c4_deck: gf-02-layered-assurance
  c4_source_deck: decks/gf-02-layered-assurance.deck.md
  c4_source_sha256: f176abced170bb5a5668376e4babb1abf9f6f1861312823cf71e7b2b19ea3234
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Layered assurance — the observation-first ladder

When you can't put a real jail around code — it ducks into library spaces you don't see, or the
sandbox is more theater than control — you don't get enforcement, but you're not helpless. You get a
*ladder* of increasingly strong, increasingly honest observation. This is the answer to "however
sandboxed": stop pretending the sandbox is the control, and instead account for what actually
happened, at whatever layer you can reach.

## The ladder (each rung includes the ones below it)

**L1 — count the cards.** Concede you can't syntactically guard the ins and outs of unknown code.
Instead, *look*: diff what you declared must-not-change against a second copy, or re-hash a manifest.
It's a **weak** guarantee — it only proves the shape didn't change in ways you already knew to watch
— but it's honest, and it's real. (The "feel for unexpected changes" path needs a dedicated
change-detector; without one, count-the-cards is what you have.)

**L2 — pin, and declare.** Wire the brutally-simple pieces (awk, sed, tiny scripts) to a *known-good
release*, and patch them to declare their moves out loud where your tooling can hear. Now the floor
has provenance and the first signals.

**L3 — expose the run-levels.** Not just the abstract 0..4, but the real lifecycle an operator walks:
configure, make, install, personalization/setup, self-test, enablement. Emit each as a signal. The
whole lifecycle declares itself, so you can see the shape of what ran without reading its contents.

**L4 — substitute to optimize or test.** Because a hook is to knowledge, not unique function, you may
drop in your own implementation to make a rung faster or to cross-check it — provided you re-home any
verification that rode on what you replaced.

## The smell: non-graduation

When an important tool — or someone's use bound to a tool — sits at a layer and shows no sign of
climbing toward the others, treat that as a **signal**, not neutral. A thing that never earns more
assurance, when it could, is telling you something.

## It complements enforcement, doesn't compete

Where a real jail exists, use it (that's the enforcement-first answer). This ladder is what you stack
*around* that core — and what you rely on entirely when no real jail is available. Weak-but-honest at
the bottom beats strong-but-absent.

*Refined from the C4 canon deck `gf-02-layered-assurance.deck.md` (see `metadata`; `c4_source_sha256`
names the exact canon version, re-hash to vouch). Candidate canon (Corwin's theory T2).*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
