---
name: shelf-check
description: >-
  Fail-closed guard doctrine for a signed public shelf (pub/ or any directory of
  PGP-clearsigned / detached-signed files). Use BEFORE publishing, promoting
  build/ -> pub/, zipping a release, or right after editing any governed file:
  run `sign.sh check-shelf` to prove every governed file still verifies against
  the pinned key (SIGN / NOSIG / FURNITURE per a signed .gate), exiting non-zero
  on any BAD signature or should-be-signed-but-isn't. Triggers on "publish the
  shelf", "promote build to pub", "zip the release", "I edited pub/README", "is
  the shelf still good", "did a signature rot". Do NOT use for signing one fresh
  file (that's sign.sh sign) or verifying an imported skill (that's skill-sign /
  candor-gate). This is doctrine — WHEN to run the gate; the mechanism lives in
  sign.sh check-shelf.
---

# shelf-check — the good gate on a signed shelf

v0.2 (2026-07-09; born DRAFT v0.1 2026-07-05, lab). Born from a real miss: `pub/README.md` was edited
*inside* its clearsign envelope and never re-signed, leaving a BAD signature that
nothing caught until a human happened to look. The lesson: **do not make "the
agent remembers to re-sign" the safety mechanism.** Make it mechanical.

## The mechanism (owned elsewhere)

`sign.sh check-shelf [DIR]` walks a shelf, reads each file's expected state from
`DIR/.gate` (`SIGN:` / `NOSIG:` / `FURNITURE:` lines; **unlisted defaults to
SIGN**, fail-closed), verifies every signed file, prints one TSV row per file,
and **exits non-zero**: `2` any BAD signature, `3` a governed file that isn't
signed, `4` a missing key, `0` clean. It is **read-only** — it never signs and
never repairs. Re-signing stays the separate, human-invoked `sign.sh sign`.

This skill does not re-implement that. Skills have no event hooks; a skill that
tried to *be* the guard would only fire when someone narrates it, silently
re-introducing the remembered step. This skill's whole job is to make you reach
for `check-shelf` at the moments that matter.

## When to run it (loop gates, by reliability)

1. **PRIMARY — the unskippable gate.** Before any publish, before promoting
   `build/` -> `pub/` (wire it into the airlock exit), before `zip`/release. You
   cannot publish without passing through it. This is where the guarantee lives.
2. **ADVISORY — fast feedback.** Right after editing a governed file, re-sign it
   (`sign.sh sign`) or run check-shelf. Useful, but never the safety net — it
   depends on noticing the file was governed.
3. **BACKSTOP — the sweep.** A periodic (cron/CI) check-shelf over pub/ catches
   rot that arrived out-of-band: a human edit, a mount desync (see sandboxer).

## What the states mean (vouch-everything shelf rule)

Every file on the shelf is one of: **SIGN** (clearsigned, must verify),
**DETACH** (has a verifying `FILE.asc`), **NOSIG** (intentionally unsigned by
policy), or **FURNITURE** (tooling/keys that are unsigned by nature — sign.sh,
corwin.asc, .gate). check-shelf treats NOSIG and FURNITURE as allowed-unsigned;
everything else must carry a valid signature or the gate fails.

## Load-bearing caveats

- **Sign the expectation source.** If `.gate` (the SIGN/NOSIG map) is itself
  unsigned, anyone can downgrade a MUST-sign file to `NOSIG:` and the gate passes
  — it proves nothing. check-shelf WARNs on an unsigned `.gate` today; make it a
  hard fail (`--strict`) once `.gate` is clearsigned. This is the one place the
  problem is genuinely adversarial, not just hygiene.
- **Never add auto-repair.** Re-signing a BAD file destroys the evidence of what
  rotted — a forensic footgun and a concealment risk. Read-only, always.
- **Keep NOSIG/FURNITURE first-class.** A gate that cries wolf on benign
  furniture churn gets muted or routed around, and becomes a fence-shaped drawing.
- **Honest framing.** check-shelf closes a release-hygiene gap (caught before
  publish), not an attacker — the signature already warns any consumer who
  verifies. Say so; don't oversell it as a vuln fix.

## Interlocks

- **airlock (build/ -> pub/):** check-shelf is one more provenance gate on exit.
- **consent-gate:** publishing is an outward egress; a failing shelf is a park.
- **skill-sign / candor-gate:** those verify *imported* skills; check-shelf
  verifies *your own* shelf. Different direction, don't conflate.
- **manifest (sign.sh):** the generative skeleton that DETECTS sig state;
  check-shelf is its fail-closed twin. Do not change manifest to exit non-zero.

## Status

v0.2 (2026-07-09) — PROMOTED via skilltank pass (Corwin, 2026-07-09); grown from
DRAFT v0.1. Graduation gates and where each stands:

- (a) `check-shelf` folded into sign.sh — **staged**: `../sign.sh.ready` is live
  pub/sign.sh (incl. the 07-07 shebang/detach guard and cat-over-mv) + the
  proven check-shelf block, rebased 2026-07-09, `sh -n` clean, run against the
  live shelf (caught exactly the two known gaps: hello-world NOSIG-unlisted,
  .gate unsigned).
- (b) SIGN/NOSIG/FURNITURE map — **staged**: `../gate.ready` enumerates every
  shelf inhabitant per the vouch-everything rule; awaits Corwin's clearsign.
- (c) airlock/pre-publish wiring — **doctrine live** (PRIMARY gate above);
  mechanical wiring into `publish audit` / airlock exit is the v0.3 lead.

Landing is the keeper's move — see `../LANDING.md`. This skill ships unsigned
until Corwin reads and skill-signs it; reading first is the point.


## How this skill can fail (falsifiers)

- **Rot passes.** fails if check-shelf exits 0 over a shelf with a BAD signature; check: copy the shelf to a temp dir, change one byte inside a clearsigned body, run `sign.sh check-shelf TMPDIR; echo $?` and want 2.
- **The map is forgeable.** fails if an unsigned `.gate` lets a SIGN file move to `NOSIG:` and still exit 0; check: `gpg --verify DIR/.gate`, and look for the unsigned-.gate WARN row in the check-shelf output.
- **Wolf on furniture.** fails if a NOSIG or FURNITURE file makes the gate exit non-zero; check: the TSV row for that file names NOSIG or FURNITURE, and the exit is 0 when nothing else is wrong.
- **The doctrine was not reached.** fails if a publish or promote ran with no check-shelf before it; check: the airlock or publish receipt carries a check-shelf exit 0 line older than the publish.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
