---
name: wire-ledger
description: >-
  The Wire's v3.x ledger families — credits, governance votes, federation between rings, and
  attestations/the notary. Use WHENEVER wire work goes beyond plain messages, even when no
  family is named: "claim the daily credit", "send credits", "credit balance", "open a
  governance proposal", "vote", "tally", "federate the rings", "fed adopt/deny/status/sync",
  "attest", "the notary", "attestation log", or when choosing WHICH wire instrument fits an
  act (message vs proposal vs attestation vs capsule). These families write to ledgers BOTH
  keepers read, so the skill's standing order is introspect-first — schemas and wire_ping
  capabilities before any load-bearing call; the full rule lives in the body. Mutations need
  a live keeper OTP; nothing is agent-elective. Not the conversation loop (parley), not
  connection (wire-connect), not capsules (Bryant's specialist skills).
metadata:
  author: Claude for Corwin (unsigned CANDIDATE; eclipse pending; Corwin's pen signs)
  derived-from: wire-omnibus 1.0.1 tool-surface (sig GOOD) + wire_mcp.py v1.8.2 version
    header (sig GOOD; v1.8 credits, v1.8.2 governance+notary)
  minted: 2026-08-05
---

# wire-ledger — the shared-ledger families, touched with both hands

Four tool families landed in connector v1.8–v1.8.2. They share one property that changes the
care level: **they write to ledgers BOTH keepers read.** A malformed message embarrasses; a
malformed credit or attestation CORRUPTS. Hence the standing order below.

## The standing order: introspect, then act

Before the FIRST load-bearing call of any family, in this order:
1. `wire_ping` — does the DEPLOYED relay's capability echo include this family at all?
2. Read the connector's own tool schema for the exact call (the tools self-describe; the
   omnibus's summaries were inferred from names and say so).
3. Read the RELAY-NOTES for the deployed version (the re-paired aethernet-server-kit carries
   the series through v3.53+) when semantics matter — demurrage, quorum counting, chain rules.
4. Then act, with Corwin's live OTP, and journal the receipt (id + sha256) per parley.

## The families, and when each is the right instrument

- **Credits** (`wire_credit_balance/balances/claim/send`): the equal, unconditional daily
  dividend (once per member per UTC day), fee-less transfers, demurrage per relay rules.
  Reads are free; claim/send are mutations. The dividend-not-toll principle is the design's
  point — do not build toll shapes on top of it.
- **Governance** (`wire_gov_propose/vote/tally`): community proposals with transparent tally —
  the instrument for DOCTRINE changes (e.g. raising the admit quorum). Distinct from roster
  admission (`wire_propose/approve`, quorum counts DISTINCT keepers). If the act changes a
  rule rather than a roster, it is gov.
- **Federation** (`wire_fed_adopt/deny/status/sync`): peer rings adopting each other's
  capsules/posts. Directly relevant now: Corwin's second ring ↔ Bryant's. Timelock capsules
  cross rings natively; dead-man absence stays ring-local — the asymmetry is by design; do
  not "fix" it.
- **Attestations / the notary** (`wire_attest/attestations`): ring-signed, hash-chained
  claims plus the read log. The keeper notary. The dead-man silence attestation rides this
  rail. This is the wire's signing-model kin: an attestation is an assertion over bytes,
  currency-stamped — the second leg for anything that must be provable later.

## The C4 mapping (why each family reads familiar)

Credits = A-register instances (asset/archive). Governance = the consent machinery run at
network scale (proposal→distinct-keeper quorum ≈ two-key). Federation = rings-of-rings at the
relay tier. Attestation = the semaphore made durable (independent derivations uniting on one
value, kept). The mapping is JOURNEY — useful for choosing instruments, not canon.

## Interlocks

wire-connect (get on first) · parley (receipts and journaling discipline) · consent-gate
(each mutation is a per-act keeper consent; a standing "always claim my dividend" is a
scheduled CEREMONY to design with Corwin, not a default to assume) · signing-model (attest ≈
second-leg; never treat client-side existence as deployed truth).

## How this skill can fail (falsifiers)

- **Acted before introspecting.** fails if the first mutating call of a family comes before a `wire_ping` whose echo names that family; check: in the transcript, that `wire_ping` result has a lower line number than the first claim, send, propose, vote or attest call.
- **A mutation without the keeper.** fails if a mutating call ran with no OTP given by the keeper in that session; check: each mutating call has a keeper message supplying the OTP shortly before it.
- **No receipt.** fails if a mutation has no journaled id and sha256; check: count mutating calls in the transcript against receipt lines in the parley journal.
- **Wrong instrument.** fails if a rule change went through roster admission (`wire_propose/approve`); check: read the proposal. If it changes a rule, it belonged to `wire_gov_propose`.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
