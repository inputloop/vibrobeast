---
name: release-runbook
description: >
  The polygram release turnaround — mint, gate, sign, tag, publish to Forgejo — as one blessed path with runnable verification. Use whenever a release is being cut, checked, or discussed for the AS4CE/polygram foundry (or a project following its discipline): "cut a release", "release 0.7", "run the release", "sign the dist", "are the artifacts signed?", "verify the dist", "push the tag", "publish to code.bru.st / Forgejo", "certification sweep", "is 0.6.0 fully signed?". Also use when auditing PAST releases for signature coverage, or when anyone proposes a hand-rolled signing wrapper — the runbook exists because a wrapper once silently skipped the MANIFEST. Covers the sandbox/host split (the sandbox cannot push; bin/release runs on the HOST). Not for per-skill signing (that is skill-sign) or session close-out (that is session-rotate).
---

# Release Runbook — one blessed path

A release is made of commits, gates, and signatures — in that order, every
time. `bin/release` automates the middle; this runbook is the whole turnaround
plus the *why*, so the discipline survives a cold session or a hurried one.

## The cautionary tale (why one path)

Before `bin/release --apply` existed, a hand-rolled loop signed the dist:

```sh
for f in polygram-curation-*.{MANIFST,tar.gz,zip} ; do sign.sh sign $f ; done
```

`MANIFST` is a typo. The glob never matched, no error surfaced, and manifests
shipped unsigned — the 0.5.4 artifacts in `dist/` still have no `.asc`. That
is the whole argument: signing is a ceremony with one blessed path, because
wrappers fail silently and ceremony failures look exactly like success.
If you feel the urge to write a helper around signing, the runbook is missing
something — fix the runbook, don't fork the ceremony.

## Where things run (the split brain)

- **Sandbox (Cowork):** can read the repo, run tests, mint dist, and verify
  signatures. It **cannot push** — code.bru.st SSH host-key fails — and git
  must not run against the mounted repo (writes desync).
- **Host (Corwin's machine, MINGW64 is fine):** where `bin/release` runs.
  Commits, tags, and pushes happen here, by hand. `$FORGEJO_TOKEN` only ever
  lives in the host environment; it is never stored anywhere.

The practical consequence: Claude prepares and verifies; Corwin applies and
pushes. Don't fight this; it's a feature — the keys stay where the keeper is.

## The turnaround

1. **Story first.** Write the `NEWS` entry (`Version X.Y.Z ...`). The release
   gate requires it, and it becomes the Forgejo release body verbatim.
2. **Mint.** `bin/polygram dist` produces the three artifacts in `dist/`:
   `polygram-curation-VERSION.{tar.gz,zip,MANIFEST}`. Dist in-signs what it
   is responsible for — do not sign around it.
3. **Dry-run the gates.** `bin/release` (no flags) is read-only and prints
   the plan. Gates: clean work tree · artifacts present · MANIFEST stray-free
   · NEWS entry · tests green · tag free. A red gate is an answer, not an
   obstacle.
4. **Read before signing.** The operator reads what is about to carry their
   signature. Time to read is bought with a pause, never with a REJECT
   (see skilltank's reading room). The signing itself is the moment that
   confers the dignity.
5. **Apply.** `bin/release VERSION --apply` — detached `.asc` per artifact
   (pinned key `ECE77CF4...F007`), each verified immediately, then the
   signed tag `vVERSION`. Host only.
6. **Publish.** `bin/release VERSION --push` — pushes the signed tag; that is
   the release. It resumes after `--apply`. `bin/gtmode` picks the transport:
   no `$FORGEJO_TOKEN` → SSH as git is already set up; `$FORGEJO_TOKEN` set →
   HTTPS with the token for that run only, SSH switched off. With a token it
   also creates the Forgejo release page (NEWS body, 6 assets); a page failure
   after the tag is up is a warning with a retry line, not a failed release.
   The whole turnaround runs as `c4/runcards/RUNCARD-2026-09-25-02-release.rc`
   under `rc1rn` (C4's `bin/rc1rn`, shipped in `run-card/scripts`; facts first,
   re-running is safe).
7. **Verify from the outside.** Run the verifier (below) against `dist/`;
   spot-check the Forgejo release page carries all 6 assets.
8. **Certification sweep.** installed == bundle == MANIFEST == repo, for
   every curated skill. (0.6.0 shipped 13/13; that is the bar.)
9. **Close out.** Memory note with version + date; session-rotate if the
   session is ending.

## The verifier

```
python3 scripts/verify_dist.py --dist DIST_DIR [--version X.Y.Z] [--fpr FPR]
```

stdlib-only; uses `gpg` if present, otherwise degrades to coverage checks
with a loud warning. For each version found (or the one named): all three
artifacts exist, each has a `.asc`, each signature verifies against the
pinned fingerprint, and the MANIFEST is sed-stray-free. **Exits non-zero on
any failure — this one is a gate, not advisory.** Run it after every
`--apply`, and any time someone asks "is release X actually signed?"

It would have caught 0.5.4.

## Neighbors

- **skill-sign** — per-skill provenance (whole-tree manifest, pinned key).
  This runbook is the aggregate layer above it; `bin/release` is its
  release-side companion.
- **skilltank** — the reading room and promotion etiquette that feed the
  "read before signing" step.
- **session-rotate** — close-out after the release lands.


## How this skill can fail (falsifiers)

- **The verifier misses a gap.** fails if `verify_dist.py` exits 0 on a dist copy with one `.asc` removed; check: `cp -r dist /tmp/d && rm /tmp/d/*.MANIFEST.asc && python3 scripts/verify_dist.py --dist /tmp/d; echo $?` and want non-zero.
- **A quiet degrade.** fails if the verifier runs without gpg and prints no warning; check: `env PATH=/nonexistent /usr/bin/python3 scripts/verify_dist.py --dist dist` prints the `WARN   gpg not found` line.
- **A release without its story.** fails if a pushed tag `vX.Y.Z` has no NEWS entry; check: `grep -n '^Version X.Y.Z' NEWS`.
- **Certification short.** fails if the step-8 sweep counts fewer matches than curated skills; check: the sweep line reads N/N (0.6.0 read 13/13).
- **The verifier's own check went quiet.** fails if `sh tests.sh --prove-red` does not end `PROVE-RED OK`; it builds a clean dist and ten planted faults in a throwaway keyring, then breaks `verify_dist.py` five ways and must catch each.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-11.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
