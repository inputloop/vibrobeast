---
name: posix-gotchas
description: "The POSIX-sh footguns that a passing test suite cannot see, plus a checker measured against a real corpus so it does not cry wolf. Use ALONGSIDE the `posix` skill whenever a shell script or shell tool is being AUTHORED, patched, or reviewed — especially a tool that will be committed, installed, or shipped, and doubly so when it embeds awk/sed or defines shell functions. Fires on: writing any .sh or bin/ tool, \"is this POSIX\", \"review this script\", an unexplained \"Illegal number\" / \"integer expression expected\" / \"Bad substitution\" / \"parameter not set\", a --prove-red that passes while the tool misbehaves, or a linter reporting many findings you are tempted to skim past. Not for running shell commands as a means to other work."
---

# posix-gotchas — the footguns a green suite cannot see

Companion to `posix` (which owns the review loop and house idiom). This skill owns one
narrow thing: **POSIX-sh failure modes that pass every normal test and surface later, in
anger** — and a checker tuned against a real corpus rather than against intuition.

## Measured, not asserted

| corpus | conventional bashism lint | `sh1ck` (bundled) |
|---|---|---|
| 4 clean hand-written tools | **14 findings, all false positives** | 0 |
| 3 planted real bugs | **0 of 3** | **3 of 3** |
| 167 real shop shell files | — | 0 FN-COLLIDE · 10 GREP-C-ZERO · 30 PIPE-STATUS |
| 666 shop shell files, 2026-10-26 (c4 + AS4CE0001) | — | PIPE-STATUS 201 → 186 after the `$( )` narrowing; the 15 dropped were all output tests, none a lost bug · TEE-STATUS 3, exactly the three live ones in build-tree-sitter.sh |

All 14 false positives were inside **embedded awk** — `while ((getline`, `function esc(s, t)`
— read as bash arithmetic and the bash `function` keyword. **A checker with a high
false-positive rate teaches the author to skim past it, and then it cannot help when it is
right.** Suppressing embedded languages is not a nicety; it is what makes the rest usable.

**The narrowing is the lesson.** FN-COLLIDE first reported **66** hits on the shop corpus —
almost all the *deliberate* harness idiom `pass=0; ok() { pass=$((pass+1)); }`. A function
setting a global on purpose is not a bug. Narrowed to the shape that actually bites — a
**command substitution** landing in a name the top level does **arithmetic** on — it reports
**0** there and still catches the real one. Measure, narrow, re-measure.

## The ledger

### 1 · FN-COLLIDE — POSIX sh has no local variables

A name assigned inside a function **is** the caller's name (`local` is not POSIX).

    got=0                                  # a counter
    digest() { got=$(sha256sum "$1"); }    # the SAME name, now a 64-char hex
    echo $(( got + 1 ))                    # -> "Illegal number: 06bb815e..."

Silent until arithmetic touches it. Harmless when a function sets a global on purpose;
dangerous when a **string from a command** meets a name used as a **number**.

### 2 · PIPE-STATUS — POSIX sh has no `pipefail`

`cmd | sort` reports **sort's** status; a refusal inside `cmd` is swallowed and `set -e`
never fires. Vicious because it can make a `--prove-red` report PASS while the tool accepts
input it just refused. **Fix:** materialise first — `awk … > "$tmp"` then `sort "$tmp"`.

**Not when the pipeline sits inside `$( … )`.** In `if [ "$(a | b)" = x ]` or
`if [[ $(ls | wc -l) -gt 0 ]]` the test reads the substitution's *output*, not the pipeline's
status, so `sh1ck` no longer reports it (2026-10-26: 5 of 5 such hits on Corwin's Windows CI
were false; on the shop corpus the narrowing dropped 15, every one an output test).

### 2b · TEE-STATUS — `$?` after `| tee` is tee's

    make 2>&1 | tee -a "$log"
    RC=$?                         # tee's status: a failed build is announced OK

The logging shape of PIPE-STATUS, and a live bug the day it was named: build-tree-sitter.sh
(lines 61-62, 78-79, 81-82) reported failed grammars as OK; a test proved it. Under
`#!/bin/sh` there is no fix in the pipeline — write the log another way (`cmd >"$tmp" 2>&1;
RC=$?; cat "$tmp" >>"$log"`). Under bash, see the bash paragraph below.

### 3 · GREP-C-ZERO — `grep -c` prints its count *and* exits non-zero

    n=$(grep -c PAT f || echo 0)   # no match: grep prints "0" AND exits 1 -> n is "0\n0"
    [ "$n" -ge 3 ]                 # -> "Illegal number" / "integer expression expected"

**The defensive addition is the bug.** Worked example from a real tree: a genre-detector had
`[ "$(grep -c '|' "$b")" -ge 3 ]` (correct — `grep -c` prints `0` by itself) beside
`[ "$(grep -cP '\t' "$b" 2>/dev/null || echo 0)" -ge 3 ]`. The `|| echo 0` was added because
`grep -P` may not exist — and it broke the ordinary no-match case, misclassifying every
tab-less file *and* spewing to stderr, on a path used constantly.

**Fix:** `n=$(grep -c PAT f 2>/dev/null || true); [ "${n:-0}" -ge 3 ]`. `|| true` is safe;
`|| echo 0` is not. The difference is whether the fallback **prints**.

**Triage rule:** a hit landing in `printf %s` is latent (ugly output); a hit landing in
`-eq/-ge/-lt` or `$(( ))` is live.

### 4 · QUOTE-IN-COMMENT — an apostrophe in prose closes a single-quoted block

A comment saying `the caller's name` inside a single-quoted `awk` block **terminates the
shell quote**, producing a syntax error tens of lines away. The mirror image bites any
line-based shell parser: it must drop whole-line comments *before* counting quotes, or a
prose apostrophe opens a phantom string that swallows everything after it.
**`sh -n` catches this — run it.**

### 5 · FN-COLLIDE's Perl twin — `while (<$h>)` writes the global `$_`

A Perl helper that reads with `while (<$h>)` assigns the global `$_`. Called from inside a
caller's `grep`/`map`/`for`, where `$_` is an alias for the list element, it overwrites the
caller's list: the list silently fills with undef. Receipt: check-warn-new.pl `complete()`,
2026-10-26 — the lane's previous log came back as "none" until `local $_;`. **Fix:** `local $_;`
at the top of the sub, or `while (my $l = <$h>)`. Same lesson as FN-COLLIDE: a name you did not
declare is the caller's.

## Under `#!/bin/bash` (most of Corwin's CI is)

The checks above are written for POSIX sh, and the fixes say so. A bash script has the real
fix for pipeline status: `${PIPESTATUS[0]}` read immediately after the pipeline (before any
other command resets it), or `set -o pipefail` for the script. `sh1ck`'s PIPE-STATUS and
TEE-STATUS stay quiet on the `${PIPESTATUS[0]}` form. Syntax-check a bash script with
`bash -n`; `dash -n` does not apply there (it rejects bash on purpose).

## The move

1. **`sh -n` first**, from fresh bytes (a stale read syntax-fails good code).
2. **Run `sh1ck`** on everything you authored or edited (bundled beside this file; the
   skill's base directory is given to you when it loads):

       sh <skill-dir>/sh1ck FILE...        report findings
       sh <skill-dir>/sh1ck --prove-red    each check must fire on a planted bug,
                                           and stay quiet on clean code

   Exit 0 clean · 1 findings · 2 usage. POSIX sh + awk, no dependencies.
3. **A finding is a question, not a verdict.** Read the line. A finding inside an embedded
   program is the checker's bug, not yours.
4. **Adding a check means adding two fixtures** — a planted bug proving it fires, and clean
   code proving it stays quiet. One without the other is decoration.
5. **Assert your patches.** A `str.replace()` that matches nothing is a silent no-op; the
   same family of failure as everything above.

## What `sh1ck` reports

| code | meaning |
|---|---|
| `FN-COLLIDE` | a command substitution inside a function lands in a name the top level does arithmetic on |
| `PIPE-STATUS` | a pipeline's exit status is being consumed by `if`/`while`/`until` (not one wholly inside `$( )`) |
| `TEE-STATUS` | `$?` read on the same line after `\| tee`, or on the next line — it is tee's status |
| `GREP-C-ZERO` | `grep -c … \|\| echo 0` — two lines where one was wanted |

## Limits, stated

- Heuristic and line-based. It recognises shapes; it does not parse shell.
- `PIPE-STATUS` still reports where a pipeline's status is consumed even when the author
  meant it. Read the line.
- It says nothing about **spacing, quoting, brace nesting, word/line splitting, or
  indirection** — the genuinely hard parts. Those want their own treatment and belong to
  the `posix` review loop until then.
- One house convention worth knowing: spaces "always where they must, never where they
  can" — with deliberate exceptions around riskier operations such as closing a sub-shell.
  Spacing that looks inconsistent may be carrying meaning.
- Unsigned. `sh1ck` is also kept at `c4/h/sh1ck`; the two agree in code (the copy here adds the licence
  header), and the copy here needs no C4 to run.

## How this skill can fail (falsifiers)

- **A check went quiet.** fails if any check stops firing on its planted bug; check: `sh sh1ck --prove-red` ends `prove-red OK`.
- **The two copies drifted.** fails if the shipped `sh1ck` and C4's `h/sh1ck` differ in code; check: `cmp sh1ck "$C4_ROOT/h/sh1ck"`. (Observed 2026-09-27: they differ, by the licence header lines 7-12 only.)
- **Embedded code flagged.** fails if a finding lands inside an awk program or a heredoc; check: read the reported line. If it sits inside one, it is the checker's bug.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-23.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
