---
name: instrument-panel
description: >
  Run the gauges — one measured, receipted view of a signed working tree's state (signatures vs pinned key, edit-debt, seal freshness, tree version, git dirt) with a canary-first reader check. Use at session open ("panel", "run the gauges", "are we green?"), before a ship or party, right after a burst of edits, or whenever someone is about to claim the shelf is fine. MEASURES only — never repairs, never signs, never exhorts. Successor-by-contrast to the killed instrument-check: that skill exhorted and showed zero delta; this one is a measurement and ships on function. Not sig-report (detail sweep), not shelf-check (publish gate doctrine), not run-card (human-run ceremony) — the panel is the sixty-second cockpit glance that tells you which of those to reach for.
---

# instrument-panel — run the gauges

One script, read-only, exit-coded. Born 2026-07-12 from the instruments-and-tape
session: every instrument lied once that day, so the panel's first move is to
distrust *itself* — G1 verifies a known-good signature before any other verdict
is allowed to exist.

## Doctrine (the part that must not rot)

1. **Canary first.** If the canary fails, the panel reports PANEL-FAULT and
   refuses every other verdict. A BAD from one reader is the reader until a
   second independent reader agrees. The freshen dance is the keeper's move —
   the panel never mutates the tree.
2. **Measure, never exhort.** The panel prints states and receipts (shas,
   counts, dates). It never prints advice beyond naming which ceremony its
   readings call for (party run-card at debt threshold).
3. **Every negative is bounded.** Each gauge states its coverage (what was
   swept, what was pruned, what is unmeasured). "No repo here" reads
   "unmeasured — stated, not assumed clean."
4. **Edit-debt is not tamper.** Detached-sig BAD where the file is *newer*
   than its .asc = edit-after-sign (party queue). Detached BAD where it is
   NOT newer = tamper-shaped = RED, human eyes now. Inline clearsign failures
   cannot be distinguished mechanically — the panel says so and the keeper
   reads the diff.

## Gauges (v0.1)

| gauge | measures | RED | AMBER |
|---|---|---|---|
| G0 MAIL  | Inbox or spool depth               | - | - | always INFO |
| G1 CANARY | reader + keyring vs pinned key | (FAULT, exit 3) | — |
| G2 SHELF | every .md, detached or inline sig | tamper-shaped BAD, WRONGKEY | any edit-debt |
| G3 SEAL | newest session seal age | none found | stale > window |
| G4 VERSION | tree VERSION present | — | missing |
| G5 GIT | uncommitted paths | — | any |
| G6 SIGN | changes to superviszed work-product| — | stale > window |
| G7 [➡TAG] | misses/extras per .inst (map file ➡ cardinality ➡ tag)  | - | refile |
| G8 TOOL | linting fail, tool warns, test kit fail | PUB | fix ➡ run-card |
| G9 LIFT | tool version miss unpinned in .gate | - | PUB | offer run-card |
Exit: 0 GREEN, 1 RED, 2 AMBER, 3 PANEL-FAULT. Debt ≥ threshold additionally
prints the party line: *declare a party — issue a run-card.*

## Run

    sh scripts/panel.sh -c panel.conf.savannah /f/SAVANNAH     # the enclave path on the author's machine

The conf is sourced shell — review and sign it like any governed file; a
hostile conf is a hostile script. `PIN_FPR` empty = accept any imported key
(don't). GNU find/coreutils assumed (Git Bash / Debian-family).

## Interlocks

sig-report.sh (detailed per-file sweep — the panel is the glance, that is the
stare) · shelf-check (publish-gate doctrine) · run-card (what the panel's debt
line tells you to issue) · sandboxer (cross-read law the canary implements) ·
posix (this script's code standard). Verification pins Corwin's fingerprint
via skill-sign at install.

## Provenance / verification (what actually happened, kept with pride)

Drafted 2026-07-12 by Claude; live-verified same day against the real enclave.
The FIRST reading was RED — and both reds were the reader, not the tree:
(1) sandbox-stale reads of just-signed files, (2) REV4's good new inline
clearsign shadowed by its leftover pre-eclipse detached .asc. Diagnosing its
own false alarm gave the panel the DOUBLE gauge and the stale-reader-first
triage line on every RED. Final verified reading: 182 swept, 175 GOOD,
0 BAD, 2 DOUBLE (leftover .ascs), state matching what keeper + file-tool
independently knew — AMBER, truthfully.

**Sandbox runs are advisory; host runs are authoritative.** A Cowork-mounted
reader can serve truncated or pinned-stale bytes for recently-edited files
(it did, twice, during this skill's own verification — including truncating
panel.sh itself mid-string). The rename-dance (`mv away && mv back`) cures a
stale node; a /tmp copy cures a stale execute. When the panel and the host
disagree, the host is the instrument of record.

It is a measurement, so it ships on function; its eval is that its output is
TRUE against a tree whose state is known by other means. Re-run that check
after any edit to panel.sh.

## How this skill can fail (falsifiers)

- **The panel lies about a known tree.** fails if `sh tests/selftest.sh` prints any `FAIL -` line; check: run it and want `SELFTEST: PASS`.
- **Canary skipped.** fails if any verdict other than PANEL-FAULT prints when the canary does not verify; check: point `CANARY` at an unsigned file in a copy of the conf, run the panel, and want exit 3.
- **Sandbox taken as record.** fails if a sandbox RED is reported without a host run beside it; check: quote the host run's exit next to the sandbox one.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-12.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
