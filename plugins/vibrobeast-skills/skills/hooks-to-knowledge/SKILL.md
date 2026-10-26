---
name: hooks-to-knowledge
description: >
  A design rule for integration & substitution decisions: a hook — an adapter, wrapper, shim, plugin
  point, or integration seam — is to KNOWLEDGE, not to unique function. Because a hook only *knows*
  what is happening (it doesn't own the behavior), you may substitute your own implementation to
  OPTIMIZE or to TEST, and you must re-home any cross-check that was riding on the code you swap.
  Use this whenever deciding whether to replace, wrap, reimplement, or optimize a dependency or
  integration point; when someone claims a library/hook "owns" behavior that can't be swapped out; when someone wants to *require* others to accept our shim or pay to verify it — a lever, not a hook;
  when a test or verification is entangled with code about to be refactored, supplanted, or
  replaced by a faster path; or when weighing build-vs-reuse at a seam. Reach for it even if the
  word "hook" is never said — anytime substitution, adapters, wrappers, shims, drop-in replacements,
  or "can we just swap this piece" come up.
metadata:
  c4_source_deck: decks/hooks-to-knowledge.deck.md
  c4_source_sha256: 9d7241cc1ff54226c24f786860e43b18b928c76505578399695033e8d89827c9
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Hooks are to knowledge, not unique function

A hook is a place where two things meet and one can *see* the other: an adapter, a wrapper, a shim,
a plugin point, an integration seam. The load-bearing observation is that a hook's value is the
**knowledge** it exposes — what is flowing, when, in what shape — not any behavior it uniquely owns.
Behavior can always be re-implemented; knowledge is the thing the seam actually holds.

That single reframe unlocks three moves. Apply them when a substitution, swap, or optimization at an
integration point is on the table.

## 1. You may substitute, at your option, to optimize or to test

If a hook only knows and does not uniquely own, then dropping in your own implementation behind it is
not a violation — it's the natural right of whoever holds the seam. Two legitimate reasons to do it:

- **Optimize** — a smaller, faster, or more auditable implementation that keeps the same promise.
- **Test** — a stand-in that exercises the same seam so you can compare, or that *is* a cross-check
  (a second independent path to the same answer).

The reason to write the *why* down when you substitute: a swap that keeps the entry/return promise is
safe; a swap that quietly changes it is a bug. Name which one you're making.

## 2. Substitution is *your* option — never a demand on anyone else

The right to re-implement behind a seam you hold does not extend to *requiring* others to accept your
substitution, or to spend their compute proving it. The moment a hook forces others to take your
implementation (or to pay to verify it), it has stopped being a knowledge-point and become a lever.
Offer substitutions; don't impose them. This keeps "hooks are to knowledge" from curdling into
coercion — verification and swaps are available, not mandatory, except where multiple parties have
already agreed to bear the cost together.

## 3. Re-home the test when you swap the code it rode on

The dangerous case: an implementation that was *also* serving as a cross-check gets optimized away,
and the check silently dies with it. Because the hook's value was the knowledge (the check), that
knowledge must survive the swap. So when you supplant code that carried a test:

- move the test onto the substitute, or
- keep it as an explicit, separate second check —

never let it vanish just because the code it lived in went away. A concrete tell: any
supplant/replace operation on code that had a verification attached should be *forced* to account for
where that verification now lives.

---

## When this fires

- "Can we just swap out X for a lighter version?" → yes, if the promise holds (rule 1); write down
  whether it's a pure optimize or a behavior change.
- "This library owns the behavior, we can't replace it." → challenge it: does it own the *function*,
  or just sit at the *seam*? Usually the latter (rule 1).
- "Let's optimize this adapter" where the adapter also validated something → make sure the validation
  is re-homed before the optimization lands (rule 3).
- "Require clients to run our verifier / accept our shim." → that's a lever, not a hook; make it an
  offer instead (rule 2).

*Refined from the C4 canon deck `hooks-to-knowledge.deck.md` (see `c4_provenance` — the
`source_sha256` names the exact canon version; a re-hash of the source deck vouches it). Minted by
c4cs, refined by skill-creator.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
