---
name: signing-model
description: >
  A design rule for signing artifacts and what "signed" and "versioned" MEAN. One discriminator: does
  sign-time context equal verify-time context? Read-in-place → clearsign; tooling will move, rename,
  or recompose it → DETACHED signature over a canonical content hash. Signed ≠ blessed; higher
  version ≠ canon. Two-warden seam: poly owns signing (the exit gate); c4cs is the bytes-changed
  warden at mint. comply≈faked holds ONLY inside a trust boundary, never without its fence:
  byte-match is one source, signature-to-identity the independent second — observation-purposed
  surfaces (assessment, review, audit) are outside by construction. A leg is real only when a second
  authority re-runs it on the SAME canonical content (currency + aim stamps). Single-operator work
  is honest latency, never an "independently verified" claim; exit gates need the second leg
  actually run. Use when choosing how to sign, when a signed file moves, when "signed" reads as
  "blessed", or when verification legs collapse into one hand.
metadata:
  c4_deck: signing-model
  c4_source_deck: decks/signing-model.deck.md
  c4_source_sha256: 67d119329eee30a7e635557fc844a122e594e4c4d8339adaa9dc10b21b53bc1d
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-28
  c4_status: refined-from-canon (deck ROLLED 2026-07-28, keeper's detached sig; divergence card single-operator OPEN by the keeper's choice)
---

# The signing model — sign the content, mean the word

## Clearsign vs detached: one discriminator

Don't choose by file type (prose vs code). Choose by whether **sign-time context equals verify-time
context**:

- **Read-in-place → clearsign.** A human reads and verifies the artifact where it sits, with nothing
  else on hand. Clearsign's one virtue is self-containedness; use it for prose, READMEs, cards.
- **Handled-by-tooling → detach over a canonical content hash.** If anything will move, rename,
  recompose, or virtualize the artifact between signing and verifying, a signature bound to the file
  breaks or misleads. A detached signature over the content's canonical hash follows the *content* —
  it survives a transform exactly when the canonical content is preserved (which is what a
  prove-a-promise round-trip check asserts). The trigger to go detached is the first transform
  between sign-time and verify-time. (Observed live: clearsign WRAPS — dash-escapes and armor change
  the bytes — so never clearsign a body whose recorded content-hash tooling re-checks.)

Detached signatures over hashes are also *collectable* into a provenance graph — a guarded-visibility
layer showing who signed what, where, without opening the payload.

## Two load-bearing words, kept honest

- **"signed" ≠ blessed.** A signature proves a key authorized specific bytes at a time. It does not
  prove the content is accurate, or that a human comprehended it, or that it's a safe baseline for
  later review. Signing is an accountability ACK, not a quality seal.
- **higher version ≠ more canonical.** Canon is set by the source-of-truth and the keeper's roll,
  never by an integer. Encode a version into a *name* only at archive time, if at all.

## The two-warden dimension (ROLLED 2026-07-28)

- **poly owns the exit gate.** Signing is where trust is handed to strangers; own it as expert
  knowledge — implement wholly, vet what's borrowed, or document conventional use so a reader can SEE
  there are no tricks up the sleeve.
- **c4cs is the bytes-changed warden**, upstream at mint. Poly's siloed view implies byte-provenance
  (minted-then-signed = unchanged bytes; changed = the keeper's edit) — the warden exists for the
  writer that view can't see: anything reaching the artifact out-of-sight (a tool, a transformer, a
  flattened render).
- **comply ≈ successfully-faked is domain-scoped, never blanket.** Inside a trust boundary,
  indistinguishable byproducts ARE compliance (hand-repro is fine if every hook fires as the normal
  mechanism would). It travels ONLY with its fence: byte-indistinguishability is the attacker's goal
  too, so the contract needs one leg the permitted party cannot forge — byte-match (c4cs) is one
  source, signature-to-identity (poly) the independent second. The boundary is per-GATE and per
  party-AND-PURPOSE: surfaces whose purpose is observing the work are outside by construction;
  default-outside on uncertainty.
- **Legs bind or they lie.** A leg never re-run by a second authority is decoration; a leg aimed at
  the wrong representation is confidence. Every leg carries a CURRENCY stamp (source + upstream +
  time) and an AIM stamp (which canonical content it binds).
- **The layering inverts with use — and only if it executes.** c4cs upstream at production
  (mint → sign), downstream at verification (sig first, THEN the byte check). Inversion, not
  substitution: sig-only lazy-verify is one leg, not an inversion. Direction is a property of the
  named pipeline, not the tools.
- **Single-operator is a claim problem (card OPEN by the keeper's choice).** In the shop, working
  alone is honest latency — measured, stamped, never criminalized ("all but a few" users compose at
  a single prompt). The violation is claiming "independently verified" beyond the ceremony, or
  crossing an exit-gate juncture without the second authority having actually run.
- **Hand-edits: account, don't forbid.** Layer-Zero shape — record consents over paths, rectify,
  speak in incident terms; residual disclosure-disconnect is tech debt that emits PMO/EPMO signal.

## Two corollaries

- **Dependencies:** track a referenced dependency by a rolling ref for convenience, but freeze it to a
  **durable version-pin** the moment an operation binds provenance to altered artifacts — a rolling
  ref inside a signed provenance claim is the "signed = blessed" drift wearing a dependency's clothes.
- **Sign-ready:** what you hand someone to sign should already be correct — no placeholders to strip,
  no self-description to fix. Their signature is a mechanical ACK, never a hand-edit.

*Refined from the C4 canon deck `signing-model.deck.md` (see `metadata`; `c4_source_sha256` names the
exact ROLLED canon version — 18 cards incl. the eclipse-joint amendments). Workflow-layer sibling:
the rolled `okgo-vs-runcard` deck (OKGO wardens intent; the run-card wardens doing). Interlocks with
prove-a-promise and the asset registry (try / add / supplant / retire).*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-28.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
