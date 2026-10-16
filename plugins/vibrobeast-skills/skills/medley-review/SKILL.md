---
name: medley-review
description: >-
  Review and propose patches for Bob Proulx's medley and the
  savannah-medley-scripts deploy config (the software that configures GNU
  Savannah hosts). Use whenever reviewing, hardening, or patching these repos,
  or matching their "house idiom" in new code. Covers the concrete medley/
  Savannah shell + Perl conventions to replicate, the rule that classic-Perl and
  terse-shell style are intentional (match, never modernize), treating in-code
  TODOs as maintainer reminders rather than a worklist, and a threat-model-first
  gate that must clear before any change is proposed as a security/privacy
  "improvement". Triggers on "review medley", "medley patch", "savannah-medley",
  "match the house style", "harden this script", "is this a real vuln".
---

# Medley review & house idiom

A *method and conventions* guide for reviewing and patching **medley**
(`https://www.proulx.com/git/medley.git`) and **savannah-medley-scripts**
(`https://git.savannah.gnu.org/git/administration/savannah-medley-scripts.git`).
These configure GNU Savannah hosts; they are load-bearing Free Software infra.
The maintainer is **Bob Proulx** (`rwp`). Calibrate to the maintainer: frame
every disagreement in terms of his likely rationale, never as a flat override.

The value of this work is *reviewable, testable, well-tracked* improvements, not
volume. A change that is clever locally but wrong in context is a regression.

## Match the house idiom — don't modernize it

The thing maintainers value most here is that new code is indistinguishable from
existing code. Before writing a patch, read the surrounding file and replicate
its idiom. The established medley/Savannah idioms include:

- **Capability probe:** `(cmd --version) >/dev/null 2>&1` to test for a tool,
  not `command -v` rewrites.
- **Atomic writes:** write to a same-directory temp file then `mv` into place
  (e.g. `*.tmp.$$~`), rather than writing in place.
- **Explicit cleanup:** `trap`-based removal of temp files/dirs on exit.
- **`--help`/`--version` placed *before* the root/dependency checks** so they
  work for any user and so help2man can drive them at build time.
- Section-8 man pages (these are `sbin` commands), `dist`-distributed.

When a style is consistent across the tree, assume it is a **deliberate house
choice**, not an oversight:

- **Classic-style Perl is intentional.** The upstream maintainer has settled
  this; don't relitigate it. Never propose modernizing the Perl idiom.
- **Terse, unquoted shell (`$cnf`, `$0`, `$dst`)** is the house style.
  `shellcheck` flags it as SC2086, but where the paths are fixed and space-free
  these are *style, not bugs*. Report such findings as **advisory only, no
  patch** — that posture has been explicitly approved. Run shellcheck, then
  triage: separate real defects from style the maintainer already owns.

Wording/`--help`-text rewrites are fine to suggest but are preferences: label
them **optional**, kept separate from substantive fixes, with the reason stated.
Housekeeping that has an objective source is welcome (e.g. bumping a copyright
year derived from `git log`).

## TODOs are reminders, not a worklist

In-code `TODO` comments are the maintainer reminding *himself* to revisit
something. They are **not** a backlog for the reviewer to clear. Surface them in
the review for the maintainer to prioritize; do **not** auto-generate a patch
for each one. (Corwin may strip TODOs from a tree before a re-run precisely so
they aren't mistaken for low-hanging fruit.)

## Threat-model-first gate (run before proposing any hardening)

The most common and most costly review error here is proposing defensive or
"peephole" hardening without the whole-system threat model — which is rarely
visible in a single file. Before flagging or patching anything as a
security/privacy improvement, every item must clear ALL of:

1. **Threat actor & reach.** Who is the adversary, and can they actually reach
   this code path? (e.g. a `ps`-snooping local user does not exist on a
   single-purpose, pristine VM doing a one-time setup with no other processes.)
2. **Existing layers.** Is this already protected by a layer above? Bob's design
   is intentionally redundant; "fixing" the 3rd layer of a 3-deep defense adds
   nothing.
3. **Consistency across the tree.** Is the same pattern accepted elsewhere? If
   plain `mktemp`→`/tmp` is fine in other scripts, flagging it in one spot is
   inconsistent and a sign of lost context. (Note `/tmp` is safe via the sticky
   bit; Bob also codes defensively against guessed-filename attacks.)
4. **Operator impact.** Could this break a downstream operator or process?
   **Auth mechanisms are off-limits to silently change.** medley/Savannah
   *require* passwords in places (downstream processes depend on them); do not
   disable password auth, flip `PermitRootLogin`, or remove a working
   credential path. This is the failure that must not recur.
5. **Explain the why.** State the threat model in the review note, not just the
   diff. If a change is sound only as a *general* idiom (e.g. moving wget
   credentials from the command line into a private `WGETRC`), say so and mark
   it as a nice-to-have, not a fix for a live exposure.

Anything that clears the gate is still presented as a **proposed, advisory**
change with the threat model stated — never a fait accompli, especially on
production Savannah config.

## Delivery conventions

- **Git off the Windows mount.** Do all git work (clone, diff, `format-patch`)
  in VM-local storage; the Windows mount (`F:\claude\bob\Medley` on the author's
  machine) desyncs git's
  lock/rename writes. Deliver plain `git format-patch` mailbox files under
  `patches/<repo>/`, ready for the FSF/Savannah email-patch workflow.
- **Cold-review gate.** Run proposed patches past an independent cold-review
  subagent before treating them as done, particularly for production config.
- **Never** force-push or rewrite Savannah history; flag live-host tests
  (`sshd -t`, real fetch/auth checks) the maintainer must run before rollout.
- Persist findings in `model.md` + a per-iteration `MODEL-FIXED-<label>.md` and
  a maintainer-facing `REVIEW-*.md`; track in the PMO `medley` project.
- Validate as far as the sandbox allows (`sh -n`, `perl -c` with stubs, a
  help2man stand-in) and call out anything that needs the real toolchain or a
  live host.

## GNU style

GPLv3-or-later; follow the GNU coding standards and Maintainers manual. Match
the file's existing license-notice convention rather than imposing a new one.


## How this skill can fail (falsifiers)

- **Hardening without a threat model.** fails if a proposed security change's review note lacks the gate's answers; check: each `REVIEW-*.md` item names the threat actor, the existing layers and the operator impact.
- **An auth path touched.** fails if a patch disables password auth, flips `PermitRootLogin` or removes a working credential path; check: `grep -nE '^\+.*(PasswordAuthentication|PermitRootLogin)' patches/<repo>/*.patch` finds nothing.
- **Style shipped as a bug.** fails if an SC2086 hit on a fixed, space-free path became a patch; check: it appears only as an advisory line in the REVIEW file.
- **git on the mount.** fails if a patch came from a clone on the Windows mount; check: `git -C <clone> rev-parse --show-toplevel` prints a VM-local path.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-23.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
