---
name: prove-a-promise
description: >
  A design rule for PROVING a transformer, converter, or pipeline kept its promise — not just claiming
  it. The XX pair: a universal check (round-trip to identity — data in equals data out after
  there-and-back — plus a checkable attestation of which conventions it honored) TIMES one
  implementation-specific second check (idempotence, consent, provenance, or coverage). Use it
  whenever a transform must be demonstrably faithful, not merely "looks right": encode/decode,
  serialize/deserialize, import/export, md↔org↔html, a data migration, a build or codegen step, any
  there-and-back. Reach for it when someone says "does this round-trip?", "prove the migration didn't
  drop rows", "verify this converter is lossless", "how do I test this pipeline preserved X", or when
  a component asserts an entry/return behavior you'd rather check than trust.
metadata:
  c4_source_deck: decks/prove-a-promise.deck.md
  c4_source_sha256: 7b1713757bf216a5dcf3d85b27957bd083e3afb69aba1ddaac177a4cc2f8000d
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Prove a promise, don't make one

A component doesn't get to *claim* it kept a promise about how data goes in and comes back out — it
has to *prove* it. "Looks right" is not a proof; a round-trip that lands back on the original is.
This is the discipline for any transformer with an entry/return promise: converters, serializers,
importers/exporters, migrations, build steps, codegen.

## The XX pair — two checks, not one

A promise is proven by a **pair** of assertion contexts, and both must hold:

**1. The universal check** (same for every transformer):
- **Round-trip to identity.** Take the thing there and back — `md → org → md`, `encode → decode`,
  `export → import` — and assert the result equals the original (under a stated normalization). Data
  in equals data out, or the promise is broken.
- **Attestation.** The transformer carries a checkable statement of *which conventions it honored*
  (a structured note, a manifest), so a reader can verify the claim rather than take it on faith.

**2. One implementation-specific second check** — pick the one that matters for this transformer:
- **idempotence** — running it twice changes nothing the second time;
- **consent** — a state-moving step got the agreement it required;
- **provenance** — the output names the exact input it came from (e.g. a content hash);
- **coverage** — every case the promise covers was actually exercised.

Universal × specific is why it's "XX": one axis proves *faithfulness*, the other proves the *thing
this particular transformer is responsible for*.

## Keep the losing proof-modes

When you choose the second check, the modes you *didn't* pick aren't wrong — they're kept. A mode
that loses for this transformer is often exactly right for the next one; discarding it throws away
the map of what proof even looks like here.

## When this fires

- "How do I test this converter?" → round-trip it to identity; don't eyeball the output.
- "Did the migration lose anything?" → round-trip + a provenance/coverage second check.
- "This step says it's safe to re-run." → that's an idempotence claim; prove it.
- A pipeline that *asserts* a property → make it *attest* the property, checkably.

*Refined from the C4 canon deck `prove-a-promise.deck.md` (see `metadata`; `c4_source_sha256` names
the exact canon version). In the C4 lab the executable form is `bin/c4prove` (roundtrip / attest /
promise verbs).*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
