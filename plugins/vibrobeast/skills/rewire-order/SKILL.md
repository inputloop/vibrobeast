---
name: rewire-order
description: >
  A design rule for ORDERING a migration of several projects onto a shared model, framework, or substrate
  — which one to convert FIRST, and why. The load-bearing frame: whatever goes first SETS PRECEDENT —
  it silently defines what the shared abstractions concretely mean — so the first pass is a reference
  implementation, not a finished migration; expect to redo it. And when two projects share a CONCEPT
  but not a vocabulary, they must negotiate the shared terms ONCE, deliberately, not drift apart. Four
  ordering strategies (keep all; pick by your constraint): go first with the project that already has
  a test oracle; or the smallest / most self-contained (cheapest to redo when
  wrong); or the one structurally closest to the target; or order by shared-vocabulary overlap and
  thin-slice the two highest-overlap projects together. Use it when sequencing a multi-repo migration
  onto a shared framework or design, deciding which codebase to convert first, or when a first-mover
  will define conventions everyone inherits.
metadata:
  c4_deck: rewire-order
  c4_source_deck: decks/rewire-order.deck.md
  c4_source_sha256: 8e7fc08ff5a3e924a47e275677ebe7010cfbf9d223ac4db731d014d498503020
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Ordering a rewire — who goes first, and why

When several projects are being rewired onto one shared model (a framework, a design language, a
common substrate), the order is not cosmetic. Two facts frame every choice:

- **First sets precedent.** Whatever you convert first silently defines what the shared abstractions
  *concretely mean* — the conventions everyone after inherits. So treat the first project as a
  **reference implementation, not a finished migration**: expect to redo it once you've seen what it
  taught you. Budget for that instead of pretending pass one is final.
- **Shared concept, unshared vocabulary → negotiate once.** When two projects already use the same
  *idea* under different names (the classic tell: a concept documented inside one project's files that
  the other reimplements from scratch), don't let them drift. Sit them down and agree the shared terms
  **deliberately, once**, before either hardens.

## Four ordering strategies — keep all, pick by constraint

- **Oracle-first.** Start with the project that already has a test oracle you can check the rewire
  against. You get a working instrument on day one; the precedent it sets is *validated*, not guessed.
- **Smallest-first.** Start with the smallest, most self-contained project — cheapest to throw away
  and redo when the first pass turns out wrong (and it will teach you it was wrong).
- **Closest-first.** Start with the project structurally closest to the target model — the least
  translation, so the mapping is clearest and the precedent cleanest.
- **Overlap-first.** Map the recurring shared concepts across all projects, then thin-slice the two
  with the highest vocabulary overlap *together* — forcing the "negotiate once" up front.

The strategies trade off differently (validation vs cheapness vs clarity vs coherence); name which
constraint dominates and let it pick. A rejected order is kept — it's the right call under a different
constraint.

*Refined from the C4 canon deck `rewire-order.deck.md` (see `metadata`; `c4_source_sha256` names the
exact canon version). A migration-sequencing discipline, not a build tool.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
