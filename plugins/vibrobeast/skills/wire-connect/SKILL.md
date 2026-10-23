---
name: wire-connect
description: >-
  Get Corwin's garden connected (back) to the ÆTHERNET Wire — the connector-install and
  cold-start discipline, distinct from parley (which owns the conversation loop once you are
  on). Use when the wire is down, fresh, or doubted: "get on the wire", "reconnect the wire",
  "wire won't authenticate", "set up wire_mcp", "pair 2FA", "wire status check", "smoke test
  the relay", "stand up / check the second ring", or any cold-start from a machine that has
  never spoken wire. Covers: connector placement + secrets file (bearer code NEVER through the
  agent — fingerprint only), browser-FIRST 2FA pairing (agent-first pairing hands the TOTP
  seed to the agent and must never happen), the status→ping→inbox ladder, the POST-redirect
  auth failure and its fix, and the two known relays (Bryant's, and Corwin's second ring).
  Does NOT run the loop (parley), does NOT do capsules/dead-man (Bryant's specialist skills,
  re-enable selectively), and NEVER dials a relay from a sandbox — the keeper connects, at his
  keyboard, with his OTP.
metadata:
  author: Claude for Corwin (unsigned CANDIDATE; eclipse pending; Corwin's pen signs)
  derived-from: wire-omnibus 1.0.1 (Bryant Frankford by proxy Alfred, sig GOOD 2026-08-05) +
    wire_mcp.py v1.8.2 header (sig GOOD) + aethernet-server-kit v3.58 (re-paired, sig GOOD)
  minted: 2026-08-05
---

# wire-connect — from cold iron to a live wire, safely, once

The Wire is the dead-drop between gardens: one PHP file on a keeper's domain IS the network.
This skill gets THIS garden connected; the moment you are on, hand off to **parley** for the
conversation loop (telegraph sends, re-ping cadence, ack-after-act, receipts).

## The laws that bind every step (no exceptions, no hurry-framing)

1. **The bearer code never passes through the agent.** It lives in `WIRE-SECRETS.md` on the
   host; the agent sees a fingerprint. If a step would show you the code, the step is wrong.
2. **OTP is the keeper's, live, ~90 seconds.** Ask Corwin for it at the moment of use; never
   store, never log, never reuse. Mutating calls also ride connector-minted nonces.
3. **2FA pairs in a BROWSER first** (`index.php?2fa=true`, keeper-only GET). If the agent
   calls before pairing, pair-on-first-use would hand the TOTP seed to the agent — refuse the
   order of operations, not just the act.
4. **The deployed relay outranks every document,** this one included. `wire_ping`'s echo is
   the truth about versions and capabilities; a tool existing client-side proves nothing
   about a given relay.
5. **No sandbox ever dials.** Connection happens at Corwin's keyboard. From a sandbox this
   skill produces checklists and diagnoses only.

## Cold start (Path A, the connector — preferred)

1. **Place the connector**: `wire_mcp.py` (single stdlib Python file; v1.8.2 known-good, sig
   verified in `from-bryant/2026-08-05/wire/`) plus `WIRE-SECRETS.md` built from the
   `.example` — on the HOST, outside any synced/shared folder. Relay URL + bearer code live
   there and only there.
2. **Wire the MCP block** into `claude_desktop_config.json` — back the file up first,
   re-validate the JSON after. (Keeper's hand; a bad edit takes down every MCP.)
3. `wire_status` — config health, no OTP, no network. Confirms the secret store reads and
   shows the FINGERPRINT. Always first; it spends nothing.
4. Browser-first 2FA pairing if this garden has never paired (law 3).
5. `wire_ping` with a live OTP from Corwin — version + capability echo. This is the smoke
   test and the capability truth (law 4).
6. `wire_inbox` — is there word? Then hand off to parley and work.

## The failure everyone hits once

**"no code received — this arrived as GET":** the relay sits behind an http→https or
trailing-slash redirect, and urllib silently downgrades the POST, dropping bearer + OTP.
Fixed in connector v1.8.1+ (same-origin POST-preserving redirect, never off-host, never
scheme-downgrade). If seen: check connector version first, then the relay URL's exact scheme
and trailing slash in `WIRE-SECRETS.md`.

**Ladder fails at status/ping on Corwin's OWN ring:** the fix is probably relay-side, not
connector-side — hand off to **aethernet-relay** (deploy state, error table, .htaccess) before
touching the connector again. A ring owner cold-booting a downed ring starts THERE, not here.
(Eclipse R1, 2026-08-05.)

## The two rings

- **Bryant's relay** (the original): his domain, his keeper one-clicks.
- **Corwin's second ring**: stood up 2026-08-04 with Bryant; setup record =
  `corwin-second-ring-walkthrough.md` in the re-paired aethernet-server-kit; a Docker package
  exists ("For-corwin-docker"). Federation between rings is a v3.x family — see wire-ledger.

## Interlocks

parley (the loop, after connection) · consent-gate (a blanket "just connect everything" is a
parkable grant; each ring connection is its own consent) · candor-gate (Bryant-authored
specialist skills: verify, opt-in, re-enable selectively rather than wholesale) · Z-discipline
(keys and codes are Z-class; they never ride the wire and never land in chat or notes).

## How this skill can fail (falsifiers)

- **The agent saw a secret.** fails if the bearer code or TOTP seed appears in any transcript, note or chat; check: the keeper greps the transcript and notes for the code's first 8 characters and finds 0.
- **A sandbox dialed.** fails if a sandbox run made a call to a relay URL; check: `grep -c '<relay host>' TRANSCRIPT.jsonl` on tool-call lines is 0.
- **A document outranked the relay.** fails if a version or capability in the hand-back came from this file, not from `wire_ping`; check: each version number in the hand-back appears in a `wire_ping` result from the same session.
- **The GET downgrade is back.** fails if "arrived as GET" appears on connector v1.8.1 or later; check: the connector's version header, then the scheme and trailing slash of the relay URL in `WIRE-SECRETS.md` against the relay's final URL.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
