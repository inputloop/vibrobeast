#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# rotate_session.sh — the end-of-session rotation ritual for a model.md project.
# Steps: (1) snapshot model.md -> .models/model-<date>.md, (2) bump the version
# in the model's rotation header, (3) archive prior .last-prompt.md /
# last-response.md into .sessions/<date>/, (4) drop fresh continuity templates.
#
# DEFAULTS TO DRY-RUN: prints the plan and writes nothing. Pass --apply to write.
# Every write is read-back-verified on the real disk (sandboxer discipline) —
# the success message is never trusted on its own.
#
# Exit 0 = plan clean (dry-run) or all writes verified (apply); non-zero = a
# problem (missing model, unverified write, undetectable version); 5 = the close
# check refused the apply (no receipt, a receipt that does not verify, or more owed).
set -eu

PROJECT=""; MODEL="model.md"; SETVER=""; APPLY=0; FRESH=1; BUMP=1; AFTER=""; C4DIR=""; UNGATED=""; COMMIT=1   # COMMIT: a verified apply commits its own files where there is git (2026-10-15, ENHANCE 12)
while [ $# -gt 0 ]; do
  case "$1" in
    --project)     PROJECT="$2"; shift 2;;
    --model)       MODEL="$2"; shift 2;;
    --set-version) SETVER="$2"; shift 2;;
    --apply)       APPLY=1; shift;;
    --no-fresh)    FRESH=0; shift;;
    --after)       AFTER="$2"; shift 2;;     # the close check's receipt (c4 bin/ow1ed --receipt)
    --c4)          C4DIR="$2"; shift 2;;     # where ow1ed lives, when it is not found by itself
    --ungated)     UNGATED="$2"; shift 2;;   # why the close check cannot run here; written down
    --no-commit)   COMMIT=0; shift;;  # leave the rotate's files uncommitted
    --no-bump)     BUMP=0; shift;;   # 2026-09-25: for a model that declares no session-close
                                     # step (c4): snapshot + continuity only, version untouched
    -h|--help)
      echo "usage: rotate_session.sh --project DIR [--model FILE] [--set-version N] [--apply [--after RECEIPT [--c4 DIR] | --ungated WHY]] [--no-fresh] [--no-bump] [--no-commit]"
      exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

[ -n "$PROJECT" ] || { echo "PARK: --project DIR is required" >&2; exit 2; }
[ -d "$PROJECT" ] || { echo "PARK: no such project dir: $PROJECT" >&2; exit 2; }
MODELPATH="$PROJECT/$MODEL"
[ -f "$MODELPATH" ] || { echo "PARK: no $MODEL in $PROJECT (ritual does not apply -- offer to create one)" >&2; exit 2; }

DATE=$(date +%Y-%m-%d)
STAMP=$(date +%Y-%m-%d_%H%M%S)
MODELSDIR="$PROJECT/.models"
SESSDIR="$PROJECT/.sessions/$DATE"
# 2026-09-25, found by rolling three times in a row: a second roll the same day overwrote the first
# roll's archived continuity files, and a third roll in the same second overwrote the second's
# snapshot. "Never clobber" now holds for any number of rolls: take the next free name.
free() {   # free PATH [SUFFIX] -> PATH, or PATH-2, PATH-3 ... (before SUFFIX) -- the first that is absent
  fb=$1; fs=${2:-}; fn=1; fp="$fb$fs"
  while [ -e "$fp" ]; do fn=$((fn + 1)); fp="$fb-$fn$fs"; done
  printf '%s' "$fp"
}
if [ -e "$SESSDIR/.last-prompt.md" ] || [ -e "$SESSDIR/last-response.md" ]; then SESSDIR=$(free "$PROJECT/.sessions/$STAMP"); fi
LASTP="$PROJECT/.last-prompt.md"
LASTR="$PROJECT/last-response.md"

# --- detect current version -------------------------------------------------
CUR=""
if [ -n "$SETVER" ]; then
  CUR="$SETVER"
else
  CUR=$(head -20 "$MODELPATH" \
        | grep -iE 'version|rotate' \
        | grep -oiE 'v[0-9]+' | head -1 | tr -dc '0-9' || true)
fi
if [ "$BUMP" -eq 0 ]; then CUR=""; fi
if [ -z "$CUR" ] && [ "$BUMP" -eq 1 ]; then
  echo "PARK: could not detect a version (looked for a 'vN' on a version/rotate" >&2
  echo "      header line in the first 20 lines of $MODEL). Add one, pass --set-version, or --no-bump\n      for a model that declares no session-close step (its version is then left alone)." >&2
  exit 3
fi
NEXT=$(( ${CUR:-0} + 1 ))

# --- snapshot target (never clobber) ---------------------------------------
SNAP="$MODELSDIR/model-$DATE.md"
[ -e "$SNAP" ] && SNAP=$(free "$MODELSDIR/model-$STAMP" .md)

MODE="DRY-RUN (nothing written -- pass --apply to write)"
[ "$APPLY" -eq 1 ] && MODE="APPLY"
echo "session-rotate -- $MODE"
echo "  project : $PROJECT"
if [ "$BUMP" -eq 1 ]; then echo "  model   : $MODEL  (v$CUR -> v$NEXT)"; else echo "  model   : $MODEL  (version untouched: --no-bump)"; fi
echo
echo "  PLAN:"
if [ -n "$AFTER" ]; then gate_note="--after: the receipt is verified before anything is written"
elif [ -n "$UNGATED" ]; then gate_note="--ungated: NOT RUN, and the reason is written into the archive"
else gate_note="needs --after RECEIPT (sh <c4>/bin/ow1ed --receipt --pressure FILE) or --ungated WHY"; fi
echo "   0. the close check: $gate_note"
echo "   1. snapshot $MODEL -> ${SNAP#$PROJECT/}"
if [ "$BUMP" -eq 1 ]; then echo "   2. bump header version v$CUR -> v$NEXT (in $MODEL)"; else echo "   2. (skipped: --no-bump)"; fi
if [ -f "$LASTP" ]; then p_note=""; else p_note=" (none yet)"; fi
if [ -f "$LASTR" ]; then r_note=""; else r_note=" (none yet)"; fi
echo "   3. archive .last-prompt.md -> ${SESSDIR#$PROJECT/}/.last-prompt.md$p_note"
echo "      archive last-response.md -> ${SESSDIR#$PROJECT/}/last-response.md$r_note"
if [ "$FRESH" -eq 1 ]; then
  echo "   4. write fresh .last-prompt.md and last-response.md templates"
else
  echo "   4. (skipped: --no-fresh)"
fi
if [ "$COMMIT" -eq 1 ]; then echo "   5. commit the rotate's own files (where the project is a git repository)"; else echo "   5. (skipped: --no-commit)"; fi

# --- the close check: step 0, held by the tool, not by the prose (2026-10-15) ---------------------------
# An apply needs ow1ed's RECEIPT (a token only a run of ow1ed can make; ow1ed --verify re-runs it), and
# ow1ed must owe nothing but the rotate itself.  The one way round is --ungated WHY, which is written
# into the archive.  His rule: guard in the tool, so the check cannot be simulated or skipped.
c4_dir() {
  for d in "$C4DIR" "${C4_ROOT:-}" /f/claude/c4 "$HOME/mnt/c4" "$PROJECT/../c4"; do
    [ -n "$d" ] && [ -f "$d/bin/ow1ed" ] && { printf '%s\n' "$d"; return 0; }
  done; return 1; }

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "Dry-run complete. Re-run with --apply to perform the rotation."
  exit 0
fi

if [ -n "$AFTER" ]; then
  C4=$(c4_dir) || { echo "REFUSED: --after names a receipt, but C4's bin/ow1ed is not found; name it with --c4 DIR" >&2; exit 5; }
  vrc=0; vout=$(sh "$C4/bin/ow1ed" --verify "$AFTER" 2>&1) || vrc=$?
  if [ "$vrc" -ne 0 ]; then
    echo "REFUSED (the close check): the receipt did not verify -- nothing was written." >&2
    printf '%s\n' "$vout" | grep '^RECEIPT' >&2 || printf '%s\n' "$vout" | tail -2 >&2
    exit 5
  fi
  others=$(printf '%s\n' "$vout" | grep '^OWED' | grep -v 'a rotate is owed' || true)
  if [ -n "$others" ]; then
    echo "REFUSED (the close check): ow1ed owes more than the rotate -- write these first; nothing was written." >&2
    printf '%s\n' "$others" >&2
    exit 5
  fi
  GATELINE="close check: ow1ed receipt $AFTER verified at $(date -u +%Y-%m-%dT%H:%M:%SZ); it owed the rotate only"
elif [ -n "$UNGATED" ]; then
  GATELINE="close check: NOT RUN (--ungated) -- $UNGATED"
else
  echo "REFUSED: an apply needs the close check's receipt -- run  sh <c4>/bin/ow1ed --receipt --pressure FILE" >&2
  echo "         and pass its token with --after; or say why it cannot run here with --ungated 'WHY'." >&2
  exit 5
fi

# --- verify helper: read the bytes back on the real disk --------------------
verify() { # verify FILE "must-contain"
  f="$1"; needle="$2"
  [ -f "$f" ] || { echo "UNVERIFIED: $f does not exist after write" >&2; exit 4; }
  if [ -n "$needle" ] && ! grep -qF "$needle" "$f"; then
    echo "UNVERIFIED: $f is missing expected content after write" >&2; exit 4
  fi
}

echo
echo "  APPLYING:"

# 1. snapshot
mkdir -p "$MODELSDIR"
cp "$MODELPATH" "$SNAP"
verify "$SNAP" "$(head -1 "$MODELPATH")"
echo "   [ok] snapshot -> ${SNAP#$PROJECT/}"

if [ "$BUMP" -eq 1 ]; then
# 2. bump version -- only on version/rotate header lines, only the vN token,
#    and refresh a YYYY-MM-DD date on that line to today.
tmp="$MODELPATH.rotate.$$"
# 2026-09-25: a header like "v13 · <date> (prior v12 rotated to .models/model-<date>.md)" kept
# "prior v12" after the bump; and "v1" also matched inside "v13". Each vN is now replaced only as a
# whole token, "prior vN" follows the bump, and the snapshot named is the one actually written.
awk -v cur="$CUR" -v nxt="$NEXT" -v today="$DATE" -v snap="${SNAP##*/}" '
  function tok(s, from, to,   out, i, c) {   # replace v<from> only where it is a whole token
    out = ""
    while ((i = index(s, "v" from)) > 0) {
      c = substr(s, i + length(from) + 1, 1)
      if ((i == 1 || substr(s, i - 1, 1) !~ /[A-Za-z0-9]/) && c !~ /[0-9]/) out = out substr(s, 1, i - 1) "v" to
      else out = out substr(s, 1, i + length(from))
      s = substr(s, i + length(from) + 1)
    }
    return out s
  }
  NR<=20 && tolower($0) ~ /version|rotate/ && !done && tok($0, cur, "#") != $0 {
    had_prior = ($0 ~ ("prior v" (cur - 1) "([^0-9]|$)"))
    $0 = tok($0, cur, nxt)
    if (had_prior) $0 = tok($0, cur - 1, cur)
    gsub(/\.models\/model-[^ )]*\.md/, ".models/" snap)
    gsub(/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/, today)
    done = 1
  }
  { print }
' "$MODELPATH" > "$tmp"
mv "$tmp" "$MODELPATH"
verify "$MODELPATH" "v$NEXT"
echo "   [ok] bumped v$CUR -> v$NEXT"
else
  echo "   [--] version untouched (--no-bump)"
fi

# 3. archive prior continuity files (if any)
mkdir -p "$SESSDIR"
for pair in ".last-prompt.md:$LASTP" "last-response.md:$LASTR"; do
  name=${pair%%:*}; src=${pair#*:}
  if [ -f "$src" ]; then
    cp "$src" "$SESSDIR/$name"
    verify "$SESSDIR/$name" "$(head -1 "$src" 2>/dev/null || true)"
    echo "   [ok] archived $name -> ${SESSDIR#$PROJECT/}/$name"
  else
    echo "   [--] no $name to archive"
  fi
done
printf '%s\n' "$GATELINE" >> "$SESSDIR/GATE.txt"
verify "$SESSDIR/GATE.txt" "$GATELINE"
echo "   [ok] the close check recorded -> ${SESSDIR#$PROJECT/}/GATE.txt"

# 4. fresh templates
if [ "$FRESH" -eq 1 ]; then
  {
    echo "# last prompt -- $STAMP"
    echo
    echo "<!-- paste the prompt that opens the next working turn here -->"
  } > "$LASTP"
  verify "$LASTP" "last prompt -- $STAMP"
  {
    echo "# last response -- $STAMP  ($( [ "$BUMP" -eq 1 ] && echo "model now v$NEXT" || echo "model version untouched"))"
    echo
    echo "<!-- summarize what this session did, so the next opens cold and resumes -->"
  } > "$LASTR"
  [ "$BUMP" -eq 1 ] && verify "$LASTR" "model now v$NEXT" || verify "$LASTR" "last response"
  echo "   [ok] fresh .last-prompt.md and last-response.md written"
fi

# 5. hook to version control (2026-10-15, his ENHANCE 12): commit the rotate's own files, nothing else
if [ "$COMMIT" -eq 1 ] && git -C "$PROJECT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  paths="$MODEL ${SNAP#$PROJECT/} ${SESSDIR#$PROJECT/}"
  [ "$FRESH" -eq 1 ] && paths="$paths .last-prompt.md last-response.md"
  if [ "$BUMP" -eq 1 ]; then what="$MODEL v$CUR -> v$NEXT"; else what="$MODEL snapshot (version untouched)"; fi
  cerr=$(mktemp)
  if ( cd "$PROJECT" && git add -- $paths && git commit -q -m "rotate: $what" -m "$GATELINE" -- $paths ) 2>"$cerr"; then
    echo "   [ok] committed $(git -C "$PROJECT" log -1 --format=%h): the snapshot, the archive, GATE.txt$( [ "$FRESH" -eq 1 ] && echo ', the fresh continuity files')"
  else
    echo "   [!!] NOT COMMITTED: $(head -2 "$cerr" | tr '\n' ' ')"
    echo "        the rotation itself is done and verified; commit these by hand: $paths"
  fi
  rm -f "$cerr"
elif [ "$COMMIT" -eq 1 ]; then echo "   [--] not a git repository: ${SNAP#$PROJECT/} is the kept copy"
else echo "   [--] not committed (--no-commit)"; fi

echo
if [ "$BUMP" -eq 1 ]; then echo "Rotation complete and verified: $MODEL is now v$NEXT; snapshot at ${SNAP#$PROJECT/}."; else echo "Rotation complete and verified: $MODEL version untouched (--no-bump); snapshot at ${SNAP#$PROJECT/}."; fi
echo "Remember to fill the fresh continuity files with the real prompt/response."
exit 0
