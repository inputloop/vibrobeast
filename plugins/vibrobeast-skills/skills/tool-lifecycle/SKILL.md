---
name: tool-lifecycle
description: >
  A design rule for HOW a capability is made, delivered, and governed. Four ideas: (1) make tools
  OPPORTUNISTICALLY — the moment reuse is proven, or rework/error-catching justifies it, mint it
  locally. (2) Deliver via TIERS — Layer 0 the filesystem, then persona / skill /
  tool-CLI / bespoke-UI — same knowledge, different reach for different people. (3) TEST ≠
  OPTIMIZATION — when a tool doubles as a cross-check, its lifeline must never hook to "valid if
  correct and more efficient"; cut hard on speed, but never retire a check because a faster path
  arrived, and re-home the check on any swap. (4) GUARD-SORTING — "I review and approve" rules split
  into SAFETY (always on, never electable) vs persona-electable (someday, with a consider-opposing-
  views stricture); enumerate and harden the safety floor first. Use it when deciding whether to
  build a tool vs stay generative, how to ship a capability, whether something is a skill or a tool,
  or which of your checks are mandatory vs which are optional.
metadata:
  c4_deck: tool-lifecycle
  c4_source_deck: decks/tool-lifecycle.deck.md
  c4_source_sha256: 821ef07e2c5ec85ec1e23f390e1dc98e17031501d30939af1536816c66a17905
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Tool lifecycle — made, delivered, governed

## 1. Make tools opportunistically

Don't wait for a mandate. The moment reuse is proven, or building the thing would save rework or
catch a class of error, mint it — locally, small, library-shaped. The back-and-forth that surfaced
the need can itself be the signal to harden. (Don't over-build ahead of proof, either; a stand-in
that both does the job and tests it is the sweet spot.)

## 2. Deliver via tiers — same knowledge, different reach

One capability can reach different people through different doors:
- **Layer 0 — the filesystem.** The always-given physical surface everything else sits on; hardening
  lands here first, and trusted hands will act here directly, without your UI.
- **Persona** — a magic-word trait (an installed canon skill *is* this).
- **Skill** — for people working through an AI.
- **Tool / CLI** — for people who think in packages and have a favorite editor or IDE.
- **Bespoke UI** — for people for whom this may be a first taste of non-vendor-demanded UI and of
  collaborative governance at all. This tier is the freedom-broadening opening, not an afterthought.

**A build says what it made, on the machine that made it.** Whatever mints a deliverable also writes a
small ignored record beside the tree — when, which host, which version, the hash of each thing made, and
the validator's word — so "is what's on the shelf the last thing built here?" is answered by reading, not
remembering. The tracked history (a release record) and this untracked note are different things: one
belongs to the version, the other to the machine. In this garden: `.last-build`, written by
`polygram/mcpb.py`, read by `sh bin/lb1ld` (2026-10-14).

## 3. Test is not optimization

When a tool doubles as a cross-check, guard its *lifeline*. You may swing the axe hard on the
optimization question — smaller, faster, cheaper is good — but a check's reason to exist is the
coverage it gives, never its efficiency. So: never retire a cross-check just because a faster path
arrived, and when you substitute the code a check rode on, **re-home the check** or keep it as an
explicit second one. A faster tool that silently drops a verification is a regression wearing a win.

## 4. Governance: sort the guards

The "I review and approve" rules you accumulate are not all equal. Sort them:
- **Safety** — always implemented, everywhere they can bear, **never** persona-electable.
- **Persona-electable** — could become selectable per persona someday, sometimes with a stricture
  tied to the ability to consider opposing views.

To offer any of this to others, the bookkeeping has to "just happen" — but **enumerate and harden
the safety floor first**, or "electable" quietly erodes it. And a meta-move worth keeping in view:
tools can reflect on tools, factoring shared parts back to their home addresses — do that as a
candidate once the pieces are proven, not as a framework minted ahead of the proof.

*Refined from the C4 canon deck `tool-lifecycle.deck.md` (see `metadata`; `c4_source_sha256` names
the exact canon version). Interlocks with hooks-to-knowledge, magic-words-persona, and the guard-floor.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.0.1 on 2026-10-15; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
