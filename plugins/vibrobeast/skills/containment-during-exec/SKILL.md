---
name: containment-during-exec
description: >
  A design rule for bounding what EXECUTED code does WHILE it runs — the gap that before/after
  checks (tumblers, round-trips, attestation) leave open once you actually run transacted or client
  code that can change a real system. Enforcement-first options + guards: CAPABILITY-SCOPED exec
  (every real-world reach default-denied, each grant its own consent tumbler; the bound is the
  capability set, not trust in the code); an OBSERVE-ONLY boundary-view of what the run touched
  (honest, never deceitful); SANDBOX-REAL-vs-THEATER (only a boundary the code can't escape counts —
  name which you have); TWO-KEY for irreversible reaches (a live during-run consent, never a blanket
  pre-grant). Kept losers: "attest and check after" is proof-after in disguise; "forbid running code"
  is the boundary someone crosses anyway. Use it when you'll run untrusted or transacted code that can
  change a real system, or when "sandboxed" must be a real control, not a hope.
metadata:
  c4_deck: gf-02-containment-during-exec
  c4_source_deck: decks/gf-02-containment-during-exec.deck.md
  c4_source_sha256: 4d8fb3c19128a4540b56fa51366b06f5c39dcae218f32fbd43f78d54250115ca
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon (design deck — options, not a single pinned answer)
---

# Bounding code while it runs

## The gap

Round-trips, attestations, and consent-tumblers are proof *before* (may I enter this run-level?) and
proof *after* (did the result round-trip?). Neither bounds what code does **mid-run**. The hazard
isn't the escalation — it's the long quiet afternoon at the top run-level. "However sandboxed" is a
concession that the sandbox isn't yet the control. This deck holds the options for closing that gap;
it's a design space, not one pinned answer.

## Two options (enforcement-first)

- **Capability-scoped exec.** Every real-world reach — network, filesystem, a named system interface
  — is default-denied, and each grant is its own consent-bearing tumbler. The bound is the *set of
  granted capabilities*, never a trust in the code's good behavior. It's the during-run analog of
  run-levels: a capability is a fine-grained tumbler.
- **Observe-only boundary-view.** Emit an honest view of what the run *touched* — which capabilities
  it exercised, volumes, which interfaces — never the payload, never deceitful. This makes a violation
  *visible*; it doesn't by itself *prevent* one, so it complements capability-scoping, doesn't replace it.

## Two guards

- **Sandbox: real vs theater.** Distinguish a boundary the code genuinely cannot escape (enforced
  below the code — kernel/OS/jail) from a convention it could ignore. Only the former counts; name
  which one you actually have. "However sandboxed" must resolve to a named, enforced boundary or it's
  a hope, not a bound.
- **Two-key for irreversible.** An irreversible or high-blast reach mid-run — delete, send money,
  exfiltrate, mutate production — takes a live during-run consent at the moment of the reach, never a
  blanket pre-grant. A blanket that lets code do anything irreversible is the coerced-consent smell.

## Two kept losers

- **"Attest and check after."** Proof-after wearing containment's clothes — the exact gap. Attestation
  is necessary, never sufficient: a lie or a bug isn't bounded by a post-hoc check.
- **"Forbid running code."** The boundary condition — but someone will run it anyway, so make it safe
  or warn them off rather than pretend the limit holds.

*Refined from the C4 canon deck `gf-02-containment-during-exec.deck.md` (see `metadata`). This is the
enforcement-first family; it COMPOSES with the observation-first ladder (layered-assurance) — real
jail as the strong core where it exists, observation wrapping the cases where it doesn't.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
