---
name: md-org-canonicity
description: >
  A design rule for deciding WHICH format is the source of truth when one document lives in two forms —
  classically Markdown ↔ Org, but any pair (md / org / html / rst). Three stances: PER-USER (the
  format THIS user hand-edits is canonical, chosen by their freedom-vs-consent lean — a
  freedom-caring user keeps the format they edit; a consent-qualified user doesn't care, so the
  tool's native format wins); ORG-NATIVE (Org is authoritative, Markdown an imported/exported view);
  MD-NATIVE (Markdown is canonical, Org a derived rendering). The reconciliation is itself a
  transformer with a prove-a-promise obligation: md → org → edit → org → md must round-trip to
  identity, and a load-bearing change rides a durable/local semaphore (files, git-as-transport),
  never a wire. Use it when deciding whether Org or Markdown (or another format) should be the source
  of truth, when a tool wants one format but the user edits another, or when round-tripping two
  formats without losing structure.
metadata:
  c4_deck: md-org-canonicity
  c4_source_deck: decks/md-org-canonicity.deck.md
  c4_source_sha256: 666971f1dc95833e2330a9732bd13c4f8165799b8bf7635a5c5ea3ad5640cc66
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Which format is canonical?

When one document lives in two forms — Markdown and Org are the classic pair, but it's any two — the
load-bearing question isn't "how do we convert?" It's **which one is the source of truth**, and the
answer is a *choice*, not a default.

## Three stances (keep all three; the loser is right for someone)

- **Per-user (the lean-winner).** The canonical format is the one *this* user hand-edits, chosen by
  their freedom-vs-consent lean. A freedom-caring user keeps editing the format they chose (org or
  md), and it stays authoritative and editable. A consent-qualified user doesn't care — Org is
  plumbing, the browser/Markdown is their surface — so the tool's native format is canonical for
  them. Same promise, two contexts.
- **Org-native.** Org is the authoritative writer; Markdown is an imported/exported view. Clean when
  a single tool owns the structure — but imposing Org on an md-native user brushes
  don't-eat-the-whole-tool. Kept: the right default for the consent-qualified user.
- **Md-native.** Markdown is canonical; Org is a derived rendering under the hood. Meets the
  md-writing world where it is and hides Org entirely — but makes the authoritative structure
  derived, harder to round-trip. Kept: right for a pure-md user who never wants Org.

## The reconciliation is a transformer — prove it

Whichever wins, treat the two-way conversion as a C4 transformer with an entry/return promise:
**md → org → (edit) → org → md must round-trip to identity** under a stated normalization. Don't
assume faithfulness; check it (a prove-a-promise round-trip).

## Load-bearing change is a durable semaphore

A change that actually matters rides a **durable, local semaphore** — files, git-as-transport — never
a wire-like live device, regardless of which format won for a given user. The source of truth is a
thing on disk you can read and re-hash, not a message in flight.

*Refined from the C4 canon deck `md-org-canonicity.deck.md` (see `metadata`; `c4_source_sha256` names
the exact canon version). Interlocks with prove-a-promise, signing-model, and org-vm / org-c4.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
