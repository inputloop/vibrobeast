#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# eclipse_pass.sh — mechanical parts of a eclipse pass: a seeded-reproducible
# random pull of projects to grind a target against, and (with --apply) the
# .eclipse-increments/ scaffold that keeps both winners and losers.
#
# Writes nothing unless --apply. On --apply, every scaffolded file is read-back
# verified on the real disk (sandboxer discipline).
#
# Exit 0 = pick printed (dry) or scaffold verified (apply); non-zero = a problem.
set -eu

TARGET=""; FROM=""; PICK=3; SEED=""; OUT="."; APPLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="$2"; shift 2;;
    --from)   FROM="$2"; shift 2;;
    --pick)   PICK="$2"; shift 2;;
    --seed)   SEED="$2"; shift 2;;
    --out)    OUT="$2"; shift 2;;
    --apply)  APPLY=1; shift;;
    -h|--help)
      echo "usage: eclipse_pass.sh --target NAME --from PATH [--pick N] [--seed S] [--out DIR] [--apply]"; echo "  PATH: the project roster (e.g. /f/claude/projects/pmo/projects.tsv), a list of names, or a dir of project sub-dirs"
      exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

[ -n "$TARGET" ] || { echo "PARK: --target NAME is required" >&2; exit 2; }
[ -n "$FROM" ]   || { echo "PARK: --from PATH is required (a file of candidates, or a dir of project sub-dirs)" >&2; exit 2; }

# --- build candidate list ---------------------------------------------------
tmpc=$(mktemp)
trap 'rm -f "$tmpc"' EXIT
if [ -f "$FROM" ]; then
  # A list of names, one per line -- or a roster TSV such as pmo/projects.tsv, whose first column is
  # the project key and whose header row starts with "key": take column 1, skip the header. Without
  # this a TSV handed over whole rows (and its header) as "projects" (found 2026-09-25).
  grep -vE '^[[:space:]]*(#|$)' "$FROM" | cut -f1 | awk 'NR==1 && $0=="key" {next} {print}' > "$tmpc" || true
elif [ -d "$FROM" ]; then
  find "$FROM" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort > "$tmpc"
else
  echo "PARK: --from is neither a file nor a directory: $FROM" >&2; exit 2
fi

N=$(grep -c . "$tmpc" || true)
[ "$N" -ge 1 ] || { echo "PARK: no candidate projects found in $FROM" >&2; exit 3; }
if [ "$PICK" -gt "$N" ]; then
  echo "note: only $N candidates available; picking all $N." >&2
  PICK="$N"
fi

# seed: explicit, or date-derived (printed so a pick can be reproduced)
if [ -z "$SEED" ]; then SEED=$(date +%Y%m%d); fi

# seeded reproducible shuffle -> take PICK
PICKED=$(awk -v s="$SEED" 'BEGIN{srand(s)} {print rand()"\t"$0}' "$tmpc" \
         | sort -n | cut -f2- | head -n "$PICK")

DATE=$(date +%Y-%m-%d)
INCROOT="$OUT/.eclipse-increments"
INCDIR="$INCROOT/$DATE-$TARGET"

echo "eclipse-pass — target: $TARGET"
echo "  (the narrow rung of the reflection family: LENS / MICROSCOPE / BUBBLE CHAMBER / ECLIPSE — keep-the-losers)"
echo "  candidates: $N   pick: $PICK   seed: $SEED  (pass the same --seed to reproduce)"
echo
echo "  GRIND MATRIX (each claim about '$TARGET' x each project):"
# a roster with a `home` column (pmo/projects.tsv) also says where each pick lives
HOMECOL=0
[ -f "$FROM" ] && HOMECOL=$(head -n 1 "$FROM" | awk -F'\t' '$1=="key"{for(i=1;i<=NF;i++) if($i=="home") print i}')
echo "$PICKED" | while IFS= read -r p; do
  [ -n "$p" ] || continue
  h=""; [ "${HOMECOL:-0}" -gt 0 ] && h=$(awk -F'\t' -v k="$p" -v c="$HOMECOL" '$1==k{print $c; exit}' "$FROM")
  if [ -n "$h" ]; then echo "   - $TARGET  vs  $p    (home: $h)"; else echo "   - $TARGET  vs  $p"; fi
done

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "Dry pick complete. Re-run with --apply to scaffold $INCDIR/ (keeps winners AND losers)."
  exit 0
fi

# --- scaffold (never clobber an existing increment dir; atomic, race-safe) --
# Fixed 2026-09-12 (eclipse-pass Lane A1 finding, 4x4 QA-stresstest matrix): the
# prior check-then-act ("if [ -e "$INCDIR" ]" then "mkdir -p") is a TOCTOU race --
# two arms launched in the same wall-clock second can both pass the existence
# check before either mkdir runs, and mkdir -p never errors on an existing dir,
# so both silently write into one directory. mkdir (bare, no -p) is atomic per
# POSIX: it either creates the dir or fails if it exists, with no window between
# the check and the act. Loop on failure, appending time+PID+a counter, so two
# arms in the same second still land in two different directories every time.
mkdir -p "$INCROOT"
_n=0
while ! mkdir "$INCDIR" 2>/dev/null; do
  _n=$((_n+1))
  INCDIR="$INCROOT/$DATE-$TARGET-$(date +%H%M%S)-$$-$_n"
done

PASS="$INCDIR/pass.md"
VERDICT="$INCDIR/verdict.md"

{
  echo "# eclipse pass — $TARGET ($DATE, seed $SEED)"
  echo
  echo "## 1. Claims under test (make them falsifiable)"
  echo "- [ ] claim 1 ..."
  echo "- [ ] claim 2 ..."
  echo
  echo "## 2. Seeded random grind"
  echo "Projects pulled (reproduce with --seed $SEED):"
  echo "$PICKED" | while IFS= read -r p; do [ -n "$p" ] && echo "- $p"; done
  echo
  echo "Grind each claim against each project; note where a claim breaks."
  echo
  echo "## 3a. Minions before persona"
  echo "- [ ] ethicsminions released on the target BEFORE any persona-colored pass"
  echo
  echo "## 3. Two opposed biases"
  echo "### doubt-first (assume it fails — why?)"
  echo "- ..."
  echo "### reward-first (assume it wins — why?)"
  echo "- ..."
  echo "### convergence (what BOTH passes agree on = the stable result)"
  echo "- ..."
  echo
  echo "## 4. Debugger ON — keep the losers"
  echo "Park discarded/contrast models below (do not delete them):"
  echo "- losing model A: ... (why it lost; what it'd take to revive)"
} > "$PASS"
verify_needle="eclipse pass — $TARGET"
grep -qF "$verify_needle" "$PASS" || { echo "UNVERIFIED: $PASS did not land" >&2; exit 4; }

{
  echo "# verdict — $TARGET ($DATE)"
  echo
  echo "RESULT: PASS | FAIL   (delete one)"
  echo
  echo "- Load-bearing pillar (survived every strip): ..."
  echo "- Broke on: <claim> @ <project> -> reframe: ..."
  echo "- Kept contrast increments: see pass.md section 4"
} > "$VERDICT"
grep -qF "verdict — $TARGET" "$VERDICT" || { echo "UNVERIFIED: $VERDICT did not land" >&2; exit 4; }

echo
echo "Scaffolded and verified: ${INCDIR}/  (pass.md + verdict.md)"
echo "Fill the claims, run both biases, and keep the losers before you call the verdict."
exit 0
