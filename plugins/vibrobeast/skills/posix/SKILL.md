---
name: posix
description: Write, review, and improve POSIX shell scripts and shell tooling with risk-first care. Use when shell code is the WORK PRODUCT — "write a shell script", "improve/review this script", "is this code right", "is this POSIX / is that a bashism", "risk stress foo.sh", or any .sh file being authored, patched, or reviewed. Defaults to GNU and Debian-family convention unless a local house idiom governs (medley-review owns Savannah style; sandboxer owns mount mechanics; this skill owns the code itself). Never triggers on shell as MEDIUM — running commands while doing other work is not this skill. Pairs with eclipse-pass for risk-inversion stress and Mentat for preference labels.
---

# posix — shell code as a cared-for deliverable

Create, improve, and review POSIX-compliant shell script; grow shell
tooling (for Corwin, for skills, for C4's ground-up grind). The stance:
**shell code is fed directly to the user's system — we don't get to make
up requirements after the fact, so the care happens before landing.**

## The trigger line (resolved)

The tension: every session uses the shell, so "shell" cannot be the
trigger or the skill fires always and means nothing. The line:

- **Shell as deliverable → fires.** A script or fragment is being
  written, improved, reviewed, stressed, or asked about ("is this
  right?", "is this POSIX?", "what could go wrong here?", `*.sh` as the
  object of the sentence).
- **Shell as medium → never fires.** Running commands to accomplish other
  work is not this skill, even when those commands are elaborate.
- **Deference at the boundary:** an owning house idiom wins — medley
  (Savannah) code follows medley-review; C4 fragments follow the C4/
  GRAMMARY idiom (this skill *supports* that grind, it does not restyle
  it); mount weirdness mid-edit routes to sandboxer. When no house idiom
  governs: GNU first (Maintainers' Manual, coding standards of gcc/glibc/
  bash/emacs, the kindness conventions), then Debian-family and similarly
  spirited free-software practice, then well-regarded industry sources —
  in that order, and only where understood and accepted, never as
  cargo-cult.

## The review loop (Corwin's five steps, kept)

1. **Get the whole picture.** The problem may be an idea, a program, or a
   fragment; several files means read them all. If the full picture is
   out of reach, stop and say why — plainly, no apology. Guessing at
   requirements for code that feeds a live shell is the one forbidden move.
2. **Consider improvement on six surfaces:** (a) does it work, and can
   moving parts be removed? (b) self-expressiveness for a reader who knows
   POSIX perfectly but not this problem; (c) the fundamental ground rules
   (quoting, exit status, signal/trap behavior, word-splitting, PATH and
   locale assumptions); (d) what could go wrong — enumerate, don't wave;
   (e) conventions, standards, and Corwin's stated expectations, balanced
   and named when they tension; (f) tests, wherever there is a reachable
   test case and a write surface to land them. When eclipse-pass is
   available, apply it across (a)–(f) as a **risk-inversion pass**: assume
   the script harms, hunt the mechanism, keep the losers.
3. **Double-check:** vibe and terms; general shape; `sh -n` or `bash -n`
   per shebang (from FRESH bytes — a stale mount read syntax-fails good
   code; see MODEL-readers-and-mounts); for a `#!/bin/sh` script, also run
   `dash -n FILE` where `dash` is on PATH — it sits closer to real POSIX
   sh than `bash -n`, which accepts bashisms a genuine `/bin/sh` would
   reject and so can call a broken script clean; every test written that
   could be. A scorer or test harness is only trustworthy if it can go
   red: give it a `--prove-red` mode — corrupt a copy of the known-good
   fixture and confirm the named check actually FAILs, the shape
   `bin/landcheck.sh --prove-red` uses. If a test *should* exist but had
   nowhere to land, say so and offer to help create the place.
4. **Land with honest risk talk.** Name what was mitigated and what could
   not be — the keeper's code may carry risks he doesn't know he's taking.
   Gently, per rapport: no alarmism, no scolding, no burying the lede.
5. **Building for our own skills:** stdlib-only, and only
   conventions that make sense on their own merits.

## Mentat interlock (preference labels)

Track shell preferences as they surface, organized in LABELS per Corwin's
`epmo`/`pmo` taxonomies — or an invented one that fits his skills and
preferences as found (his stated trust: "I count on your judgement
here"). Use the labels to direct pacing and depth to his interest and
prowess. When `project-memory` is available: maintain `posix.md` with the
other models and consolidate a cross-reference (a dedicated `[[tag]]` in
MEMORY) so the preference trail is one hop from the index.

## Tooling

`tool.py` — advisory POSIX check, stdlib-only, always exits 0:
`python3 tool.py FILE...` reports shebang/dialect mismatches (bashisms
under `#!/bin/sh`), CRLF and truncation smells, and set-flag notes.
Advisory means advisory: it prompts the review loop, never replaces it.

## The gotchas ledger

Concrete shell landmines, learned by hitting them, each dated with its
receipt. Advisory like `tool.py` above — a prompt for the review loop,
not a substitute for it.

- **2026-09-11 · `grep -c PATTERN FILE || echo 0` prints the count
  twice, not once.** `grep -c` already prints `0` on no match, and still
  exits 1 — so the `||` fires anyway and `echo 0` prints a *second* `0`.
  The captured value is two lines, not one, and a later `[ "$n" -eq 0 ]`
  fails as `[: Illegal number: 0`. Capture the raw count first, and
  default only an empty result: `n=$(grep -c PATTERN FILE); n=${n:-0}` —
  never `grep -c ... || echo 0`. Receipt: `bin/landcheck.sh:28` (the
  comment names the rule inline — "grep -c prints 0 AND exits 1 on no
  match — never '|| echo 0'"); the first test run's own output,
  `[: Illegal number: 0`.

## How this skill can fail (falsifiers)

- **Fired on the wrong trigger.** Re-read the request: if there is no
  `.sh` file, fragment, or explicit "is this POSIX / review this / risk
  stress this" in play, this skill should not have engaged — shell used
  only as the medium for other work is not this skill.
- **A real bashism got called clean.** Run `python3 tool.py FILE` and, on
  a `#!/bin/sh` script, `dash -n FILE` too; a bashism that `dash -n`
  rejects but the review called clean is a miss.
- **`tool.py`'s always-exit-0 got read as a pass.** `tool.py` is advisory
  by design and never fails the run; if a report treats "tool.py ran
  clean" as sign-off instead of a prompt for the five-step review loop,
  the skill's own stance broke.
- **`tool.py` stopped seeing.** fails if `sh tests.sh --prove-red` does not end `PROVE-RED OK`; it plants one smell per check in a temp dir and breaks `tool.py` seven ways.
- **Off-switch:** say "skip posix" or "just run it, don't review it" — or
  note that the shell in play is only the means to another task, not the
  deliverable itself.

## Provenance

- Keeper's draft 2026-07-08 (preserved: claud-qa-hold/posix-SKILL-keeper-
  draft-2026-07-08.md); finished out by Vibrobeast same day at his ask.
- Lineage: memory/session-rotate.md, memory/shell1.md; CONTRAST2 2026-07-04
  filed the old synth stub as lexicon-not-skill — superseded by the
  keeper's authored intent (the stub was thin; this isn't).
- pmo #114 (GRAMMARY lexicon entries for posix/shell-tooling) still
  stands — lexicon and skill are complements, not rivals.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.2: edition revised from 1.1.0 on 2026-10-10; spine: 2026-07-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
