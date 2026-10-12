#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# panel.sh — instrument-panel v0.1: run the gauges, report state, exit by color.
#
# MEASURES ONLY. Never repairs, never mutates the tree (temp keyring aside).
# Canary first: prove the reader + keyring on a known-good signature before
# believing any BAD. Every negative states its coverage. The panel states;
# the keeper judges.
#
# Usage: panel.sh [-c CONF] [ROOT]
# Exit: 0 GREEN | 1 RED | 2 AMBER | 3 PANEL-FAULT (instrument unusable)
#
# GNU find/coreutils assumed (Git Bash / Debian-family), per house default.
# set -u only, deliberately: grep -c and test exit codes are data here, not
# errors; -e would turn honest zero-counts into silent death mid-gauge.

set -u
command -v gpg >/dev/null 2>&1 || { echo "PANEL-FAULT: gpg not found" >&2; exit 3; }

CONF=
while getopts c: o; do case $o in
  c) CONF=$OPTARG;;
  *) echo "usage: panel.sh [-c conf] [root]" >&2; exit 3;;
esac; done
shift $((OPTIND-1))
ROOT=${1:-.}

# --- defaults; override in CONF (CONF is sourced shell: review it, sign it)
PIN_FPR=
KEY_ASC=
CANARY=
SEAL_GLOB="sessions/*end-session*.md"
MAX_SEAL_AGE_DAYS=4
DEBT_PARTY_AT=5
MAIL_DIRS="Inbox outbox"
PRUNE="archive .git .eclipse-increments .saved-coms .transcripts Inbox outbox"

[ -n "$CONF" ] && . "$CONF"

cd "$ROOT" 2>/dev/null || { echo "PANEL-FAULT: cannot cd to $ROOT" >&2; exit 3; }

GNUPGHOME=$(mktemp -d) || { echo "PANEL-FAULT: mktemp failed" >&2; exit 3; }
export GNUPGHOME
chmod 700 "$GNUPGHOME"
trap 'rm -rf "$GNUPGHOME"' EXIT INT TERM

if [ -n "$KEY_ASC" ]; then
  gpg -q --import "$KEY_ASC" 2>/dev/null \
    || { echo "PANEL-FAULT: cannot import $KEY_ASC" >&2; exit 3; }
fi

# verify_one FILE -> GOOD | DOUBLE | BAD | NOSIG | WRONGKEY
# DOUBLE = good inline clearsign shadowed by a leftover detached .asc
# (the "double ceremony" class, 07-07 sweep / REV4 07-12): report, never rm.
verify_one() {
  vf=$1 st= inline=0
  if head -n 1 -- "$vf" 2>/dev/null \
     | grep -q '^-----BEGIN PGP SIGNED MESSAGE-----'; then inline=1; fi
  if [ "$inline" -eq 1 ]; then
    st=$(gpg --status-fd 1 --verify "$vf" 2>/dev/null)
    case $st in
      *"VALIDSIG $PIN_FPR"*)
        if [ -f "$vf.asc" ]; then echo DOUBLE; else echo GOOD; fi; return ;;
      *GOODSIG*)
        if [ -n "$PIN_FPR" ]; then echo WRONGKEY; return; fi
        if [ -f "$vf.asc" ]; then echo DOUBLE; else echo GOOD; fi; return ;;
    esac
    # inline fails; a detached companion may still hold
    if [ -f "$vf.asc" ]; then
      st=$(gpg --status-fd 1 --verify "$vf.asc" "$vf" 2>/dev/null)
      case $st in
        *"VALIDSIG $PIN_FPR"*) echo GOOD; return ;;
        *GOODSIG*) if [ -n "$PIN_FPR" ]; then echo WRONGKEY; else echo GOOD; fi; return ;;
      esac
    fi
    echo BAD; return
  fi
  if [ -f "$vf.asc" ]; then
    st=$(gpg --status-fd 1 --verify "$vf.asc" "$vf" 2>/dev/null)
    case $st in
      *"VALIDSIG $PIN_FPR"*) echo GOOD ;;
      *GOODSIG*) if [ -n "$PIN_FPR" ]; then echo WRONGKEY; else echo GOOD; fi ;;
      *) echo BAD ;;
    esac
    return
  fi
  echo NOSIG
}

echo "== instrument-panel v0.1  $(date -u +%Y-%m-%dT%H:%M:%SZ)  root: $(pwd)"

# ---- G0 MAIL: drop/spool depth (always INFO, never colors the verdict) ----
for d in $MAIL_DIRS; do
  if [ -d "$d" ]; then
    mc=$(find "$d" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "G0 MAIL     : $d/ holds $mc file(s) (INFO — read them, don't trust this count for content)"
  else
    echo "G0 MAIL     : $d/ absent (unmeasured)"
  fi
done

# ---- G1 CANARY: prove the instrument before trusting it -------------------
if [ -z "$CANARY" ]; then
  echo "G1 CANARY   : PANEL-FAULT — no canary configured; refusing to report BADs blind"
  exit 3
fi
c=$(verify_one "$CANARY")
if [ "$c" != GOOD ]; then
  echo "G1 CANARY   : $c on $CANARY — READER OR KEYRING SUSPECT."
  echo "              Trust NO verdict below. Do not re-sign anything on this reading."
  echo "              Cross-read from a second independent reader; the freshen dance"
  echo "              (mv away && mv back) is the KEEPER'S move, made by a human."
  exit 3
fi
echo "G1 CANARY   : GOOD ($CANARY vs pinned ${PIN_FPR:-<any imported key>})"

# ---- G2 SHELF: signature sweep, coverage stated ----------------------------
pr=
for d in $PRUNE; do pr="$pr -name $d -prune -o"; done
RES=$GNUPGHOME/results
: > "$RES"
eval "find . $pr -type f -name '*.md' -print" | sort | while IFS= read -r f; do
  r=$(verify_one "$f")
  if [ "$r" = BAD ]; then
    if [ -f "$f.asc" ] && [ "$f" -nt "$f.asc" ]; then r=DEBT
    elif [ ! -f "$f.asc" ]; then r=IDEBT
    fi
  fi
  printf '%s\t%s\n' "$r" "$f" >> "$RES"
done
n=$(grep -c . "$RES")
good=$(grep -c '^GOOD'  "$RES"); nosig=$(grep -c '^NOSIG' "$RES")
debt=$(grep -c '^DEBT'  "$RES"); idebt=$(grep -c '^IDEBT' "$RES")
bad=$(grep -c '^BAD'    "$RES"); wrong=$(grep -c '^WRONGKEY' "$RES")
dbl=$(grep -c '^DOUBLE' "$RES")
echo "G2 SHELF    : swept $n .md files under $(pwd) (pruned: $PRUNE)"
echo "              GOOD=$good NOSIG=$nosig EDIT-DEBT=$debt INLINE-DEBT=$idebt DOUBLE=$dbl BAD=$bad WRONGKEY=$wrong"
grep '^DOUBLE'   "$RES" | while IFS='	' read -r _ f; do
  echo "              dbl  $f (inline GOOD + leftover detached .asc — rm the stale .asc at next party)"; done
grep '^BAD'      "$RES" | while IFS='	' read -r _ f; do
  echo "              RED $f sha256=$(sha256sum "$f" | cut -c1-16)... (all signatures fail — tamper-shaped. FIRST: if edited recently or reading via a sandbox mount, suspect a STALE READER: cross-read a second path / keeper freshens, re-run. Only then human alarm.)"; done
grep '^WRONGKEY' "$RES" | while IFS='	' read -r _ f; do
  echo "              RED $f — good signature, WRONG KEY vs pin (human eyes NOW)"; done
grep '^DEBT'     "$RES" | while IFS='	' read -r _ f; do
  echo "              debt $f (file newer than .asc — edit-after-sign; queue for party)"; done
grep '^IDEBT'    "$RES" | while IFS='	' read -r _ f; do
  echo "              debt $f (inline clearsign fails — edit-after-sign OR tamper; panel cannot distinguish, keeper reads the diff)"; done

# ---- G3 SEAL: newest session seal + age ------------------------------------
seal_stale=0
newest=$(ls -t $SEAL_GLOB 2>/dev/null | head -n 1)
if [ -z "$newest" ]; then
  echo "G3 SEAL     : NONE matching $SEAL_GLOB"
  seal_stale=1
else
  fresh=$(find "$newest" -mtime -"$MAX_SEAL_AGE_DAYS" 2>/dev/null)
  if [ -n "$fresh" ]; then
    echo "G3 SEAL     : $newest (fresh; window ${MAX_SEAL_AGE_DAYS}d)"
  else
    echo "G3 SEAL     : $newest (STALE >${MAX_SEAL_AGE_DAYS}d — roll or note why)"
    seal_stale=1
  fi
fi

# ---- G4 VERSION / G5 GIT ----------------------------------------------------
ver_missing=0
if [ -f VERSION ]; then
  echo "G4 VERSION  : $(head -n 1 VERSION) (tree)"
else
  echo "G4 VERSION  : missing"; ver_missing=1
fi
dirty=0
if [ -d .git ]; then
  # --no-optional-locks: a plain status takes .git/index.lock and, on a mount that refuses deletes,
  # leaves it behind (sandboxer, 2026-09-29).  The panel measures; it must not make the fault it reports.
  dirty=$(git --no-optional-locks status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  echo "G5 GIT      : ${dirty:-?} uncommitted paths (commit is a HOST move)"
  [ -e .git/index.lock ] && echo "G5 GIT LOCK : .git/index.lock is present; if no git is running, remove it on the host (sandboxer)"
else
  echo "G5 GIT      : no repo here (unmeasured — stated, not assumed clean)"
fi

# ---- verdict ----------------------------------------------------------------
verdict=GREEN code=0
if [ "$bad" -gt 0 ] || [ "$wrong" -gt 0 ]; then
  verdict=RED code=1
elif [ "$debt" -gt 0 ] || [ "$idebt" -gt 0 ] || [ "$dbl" -gt 0 ] \
  || [ "$seal_stale" -eq 1 ] || [ "$ver_missing" -eq 1 ] \
  || [ "${dirty:-0}" -gt 0 ]; then
  verdict=AMBER code=2
fi
tot_debt=$((debt + idebt))
if [ "$tot_debt" -ge "$DEBT_PARTY_AT" ]; then
  echo "** signing pressure: DEBT=$tot_debt >= $DEBT_PARTY_AT — declare a party: issue a run-card."
fi
echo "PANEL: $verdict"
exit $code
