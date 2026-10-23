---
name: skill-sign
description: >-
  Sign, verify, and bundle skills with durable PGP provenance via
  scripts/skill-sign.sh. Use when signing a skill directory before sharing,
  verifying a received skill or .skill bundle, or packaging a signed skill
  for distribution — "sign this skill", "verify this skill", "is this
  really from Corwin?", "bundle it for sharing". The signature covers a
  manifest of EVERY file in the skill (scripts included), and verification
  pins Corwin's fingerprint — "valid" means "nothing in this skill changed
  since Corwin signed it", not "someone I know signed something". Companion
  to sign.sh (files/releases) and bin/release (aggregate archives); this is
  the per-skill layer.
metadata:
  lineage: Haiku draft 2026-07-03 (FreshLocalGossip); adopted with fixes QA-7 2026-07-04
---

# Skill Sign — provenance discipline for skills

A skill's signature is a statement of custody: "I, Corwin, took
responsibility for this skill, and no file in it has changed since."
That claim is only honest if the signature covers the *whole* skill —
so it does: `sign` writes a `.skill-manifest` (sha256 per file; SKILL.md
canonicalized to LF/no-trailing-whitespace, other files as raw bytes)
and a detached `.signature.asc` over that manifest.

## Signature form follows artifact class (the house idiom)

The choice is not taste — it is decided by *who reads the file next*:

- **Machine-parsed or executable artifacts** — `SKILL.md` (YAML frontmatter),
  scripts (shebangs), manifests, bundles — take a **detached** signature
  (`FILE.asc`) or a whole-tree manifest. Clearsign inserts a header and
  dash-escapes lines beginning with `-`, which breaks a YAML fence and a
  shebang alike, and the verifier's round-trip is **not byte-idempotent**
  (gpg's text canonicalization appends a trailing `0x0a`), so a clearsigned
  runnable will drift from its own manifest hash. House-verified, twice.
- **Prose meant for human reading** — records, records of decisions, journal
  entries, models — take a **clearsign**, so the words and the signature
  travel as one file that a stranger can read without tooling.

Corollary, learned the expensive way: **a detached signature goes stale the
instant the file changes.** A `BAD` on a file whose bytes still match a
signed whole-tree manifest is a *stale signature artifact*, not tampering —
diagnose before you alarm, then re-sign (see `seams` S12).

## The three workflows

**Sign** — at the door, not after every edit. His rule (door part `his-signing-baseline`, 2026-08-03,
and the top block's *when to sign*): *sign at the door, not in the drawer — only where a named reader
relies on it (a human reading your proud name, or a comrade verifying your bytes across a boundary).
Everywhere else, unsigned is the honest default.* *Anything signed is his pen — never me, and never as
a default.* For a skill in this tree the door is `make dist`, which signs every skill as its first act
and mints the plugin as its second — one ceremony, whole cargo. After editing a skill, write the
express manifest (`manifest`, below) and queue the change in SIGN-QUEUE; do not ask for the pen. The
command `make dist` runs, per skill:

    scripts/skill-sign.sh sign my-skill/

**Bundle and share** (signature and manifest travel inside):

    scripts/skill-sign.sh bundle my-skill/     # -> my-skill.skill

Bundle refuses a skill that holds a symlink (zip would ship its target), leaves out
`.git/`, `.arc/` and `__pycache__/` (what the manifest prunes), and scans for secrets with
C4's `sb1rn` (looked for in C4, then the garden's own `bin/`; `SB1RN=path` names it). No
checker found stops the bundle like a hit does; pass it on the record with
`SKILL_SIGN_ACCEPT_SECRET='why'`, which writes the reason beside the bundle.

**Receive and verify** (the gate for anything that arrives):

    scripts/skill-sign.sh unbundle their-skill.skill
    scripts/skill-sign.sh verify their-skill/

Verify answers one pinned question — did key
`ECE77CF417C76C1ACFCE7C2B5B6135511580F007` sign exactly this tree?
A different signer or a changed file (including scripts) fails loudly,
with a diff of what moved. Override the pin with `PUB_SIGN_KEY` only
when you *mean* to trust a different signer. A pinned key missing from
your keyring reads "key not in keyring" and says what to import; it is
not called a failed signature.

The `check.sh` and `SAYS-SO` that bundle adds at the skill root are
helpers, added after signing, so the signature does not cover them.
verify reports each on its own line — "helper (not covered by the
signature)" — and compares it with the copy beside the verifier: the
same bytes are said; different bytes fail (do not run it). A skill that
ships its own root `check.sh` has it in its manifest, covered like any
other file.

## What the signature proves — and doesn't

Proves: identity (pinned key), integrity (every file), provenance
(survives re-sharing). Does NOT prove: freshness (no timestamp
authority), trustworthiness of the code (review still applies — this
tool exists because its own first delivery arrived unsigned with a
mismatched payload), or revocation state.

## Rules of the discipline

- Sign before offering; verify before trusting. No exceptions for
  friendly sources — the QA-7 intake caught a wrapper/payload mismatch
  from a *cooperating* author.
- Sign at the door (above). A signature that is ours, verifies, and covers exactly these bytes is
  left alone: `sign` says "already signed and current" and uses no key (Corwin, 2026-09-26: changes
  to the package must already have occurred). Content decides, never the clock: tar, unzip and
  `cp -p` put old mtimes on new bytes (2026-09-27). One
  skill named gets that message; a sweep over many reports only a closing count, unless
  `SKILL_SIGN_VERBOSE=1`. `-f` re-signs anyway. verify still tells you when the tree drifted.
- Unbundle refuses archives with absolute or parent-escaping paths.
- First-time recipients: `gpg --import skills/ECE77CF417C76C1ACFCE7C2B5B6135511580F007.asc`
  (fingerprint `ECE7 7CF4 17C7 6C1A CFCE 7C2B 5B61 3551 1580 F007`), and check it against a
  second source: keys.openpgp.org serves the same fingerprint, and the public repo
  code.bru.st/corwin/vibrobeast carries it as `corwin.asc` — two agreeing sources, per the
  #86 pattern.

## Related

**sign.sh** (files/releases, the lower layer) · **bin/release**
(aggregate dist archives + Forgejo) · **skill-creator** (sign what you
finish) · **consent-gate** (custody of *actions*, as this is custody of
*artifacts*) · **mentat-skill** (note patterns you spot).

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-03.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
