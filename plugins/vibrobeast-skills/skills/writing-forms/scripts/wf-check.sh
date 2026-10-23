#!/bin/sh
# wf-check.sh — given a filename, say which writing form it is, whether its prefix is in the
# register c/wf, and whether the pair the register expects sits beside it. Measures; never
# repairs; never fills a verdict it cannot derive from the name and the directory listing.
#
# usage: sh scripts/wf-check.sh PATH            one report, exit 0 OK / 1 RED / 2 usage or no register
#        sh scripts/wf-check.sh --prove-red     the mutants: an unregistered prefix must go RED, a CARD
#                                               without its -brief must go RED, and the green controls
#                                               must stay green; exit 0 only if every case behaves
#                                               (it brings its own fixture register; C4 not needed)
#        env WF_REGISTER=... WF_DESC=...         point at another register / descriptor
#
# The register is a C4 register: TSV, no header row, columns named in d/c/wf (resolved by NAME here,
# order free). PAIRS grammar, as the register writes it:
#   -          no pair expected
#   -brief     same stem + -brief.md beside it (a brief precedes its output; a brief alone is fine)
#   .EXT       same stem, that extension, beside it (.txt twin of a VIEW, .tsv of a HYPOTHESIS, ...)
#   WORD       a file with that FORM prefix beside it (a SEAL's SCORE, a DISS's REVIEW) — reported,
#              pending until it lands; a SCORE with no SEAL beside it is RED (it scored nothing sealed)
#   d/         a register's descriptor at ../d/c/<name>
#
# Copyright 2026 Corwin Brust <corwin@bru.st> — GPLv3-or-later. Authored by Fable (Mentat/Vibrobeast)
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# 2026-09-11 for the writing-forms skill. POSIX sh + awk/grep/sed only.
set -u
LC_ALL=C; export LC_ALL

here=$(cd "$(dirname "$0")/.." && pwd)
# the register lives at the C4 root (c4/c/wf); this skill may be minted under skills-mint/<date>/,
# so resolve: $WF_REGISTER, then $C4_ROOT/c/wf, then the nearest ancestor of this script that has c/wf
findroot() { d=$here; while [ "$d" != / ]; do [ -r "$d/c/wf" ] && { printf '%s\n' "$d"; return 0; }; d=$(dirname "$d"); done; return 1; }
ROOT=${C4_ROOT:-$(findroot 2>/dev/null || printf '%s' "$here")}
REG=${WF_REGISTER:-"$ROOT/c/wf"}
DESC=${WF_DESC:-"$ROOT/d/c/wf"}

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

# cell COLUMN FORM — print one cell of the register, columns resolved by name from the descriptor
cell() {
  awk -F'\t' -v want="$1" -v form="$2" '
    NR==FNR { col[$0]=FNR; ncol=FNR; next }
    FNR==1 && !(want in col) { print "NOCOL"; exit }
    $col["FORM"]==form { print $col[want]; exit }
  ' "$DESC" "$REG"
}

say() { printf '%-10s %s\n' "$1" "$2"; }

# check PATH — the one report; sets $verdict; returns 0 OK, 1 RED
check() {
  f=$1
  [ -r "$REG" ] && [ -r "$DESC" ] || { say 'register:' "NOT READABLE — $REG / $DESC"; return 2; }
  base=$(basename "$f"); dir=$(dirname "$f"); pdir=$(basename "$dir")
  say 'file:' "$base"
  form=""; prefix=""; stem=${base%.*}; ext=""
  case "$base" in *.*) ext=".${base##*.}";; esac
  case "$base" in
    *.deck.md) form=DECK; prefix='(none: .deck.md)'; stem=${base%.deck.md};;
    # the GNU release forms carry no prefix: GNU names the file, so the name is the form (2026-10-20)
    NEWS|NEWS.md|NEWS.org) form=NEWS; prefix='(none: the GNU name)';;
    ChangeLog|CHANGELOG|CHANGELOG.md) form=CHANGELOG; prefix='(none: the GNU name)';;
    INSTALL|INSTALL.md) form=INSTALL; prefix='(none: the GNU name)';;
    *.texi) form=MANUAL; prefix='(none: a Texinfo manual)';;
  esac
  if [ -z "$form" ] && [ "$pdir" = c ];     then form=REGISTER; prefix='(none: under c/)'; fi
  if [ -z "$form" ] && [ "$pdir" = facts ]; then form=FACT;     prefix='(none: under facts/)'; fi
  if [ -z "$form" ]; then
    prefix=$(printf '%s\n' "$base" | sed -n 's/^\([A-Z][A-Z]*[0-9]*\)-.*/\1/p')
    if [ -z "$prefix" ]; then
      say 'prefix:' 'NONE — no FORM-date-slug shape (a deliverable picks one form and says so in its filename)'
      say 'verdict:' 'RED (unshaped name)'
      return 1
    fi
    rest=${base#"$prefix"-}
    if ! printf '%s\n' "$rest" | grep -Eq '^([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{8}T[0-9]{4}Z|[0-9]{8}([-.]|$))'; then
      say 'prefix:' "$prefix"
      say 'date:' "NONE after the prefix (want YYYY-MM-DD, YYYYMMDD or YYYYMMDDTHHMMZ; got '$rest')"
      say 'verdict:' 'RED (no date after the prefix)'
      return 1
    fi
    form=$prefix
  fi
  say 'prefix:' "$prefix"
  answers=$(cell ANSWERS "$form")
  if [ "$answers" = NOCOL ]; then say 'register:' "descriptor $DESC lacks ANSWERS"; return 2; fi
  if [ -z "$answers" ]; then
    stripped=$(printf '%s' "$form" | sed 's/[0-9]*$//')
    if [ "$stripped" != "$form" ]; then
      answers=$(cell ANSWERS "$stripped")
      [ -n "$answers" ] && { say 'digit:' "$form → $stripped (the digit rides the prefix)"; form=$stripped; }
    fi
  fi
  if [ -z "$answers" ]; then
    say 'form:' "$form — UNREGISTERED (no row in $REG; a second use earns a row, never a rival prefix for the same question)"
    say 'verdict:' 'RED (unregistered prefix)'
    return 1
  fi
  say 'form:' "$form — registered"
  say 'answers:' "$answers"
  pairs=$(cell PAIRS "$form"); [ "$pairs" = NOCOL ] && { say 'register:' "descriptor lacks PAIRS"; return 2; }
  say 'pair rule:' "$pairs"
  case "$pairs" in
    -)
      say 'pair:' 'none expected'
      say 'verdict:' 'OK'; return 0;;
    -brief)
      if [ "$ext" != .md ]; then
        say 'pair:' "not checked — the -brief rule is for .md; this is '$ext'"
        say 'verdict:' 'OK'; return 0
      fi
      case "$stem" in
        *-brief)
          want="$dir/${stem%-brief}.md"
          if [ -e "$want" ]; then say 'pair:' "$(basename "$want") PRESENT (the output this brief is for)"
          else say 'pair:' "$(basename "$want") ABSENT — expected until the output lands; a brief precedes its output"; fi
          say 'verdict:' 'OK'; return 0;;
        *)
          want="$dir/$stem-brief.md"
          if [ -e "$want" ]; then say 'pair:' "$(basename "$want") PRESENT"; say 'verdict:' 'OK'; return 0; fi
          say 'pair:' "$(basename "$want") ABSENT — a $form is born beside its -brief"
          say 'verdict:' 'RED (pair absent)'; return 1;;
      esac;;
    .*)
      if [ "$ext" = "$pairs" ]; then
        found=""
        for e in .md .html .json; do [ -e "$dir/$stem$e" ] && { found="$stem$e"; break; }; done
        if [ -n "$found" ]; then say 'pair:' "$found PRESENT (this file is the twin)"; say 'verdict:' 'OK'; return 0; fi
        say 'pair:' "no primary ($stem.md/.html/.json) beside this twin"
        say 'verdict:' 'RED (twin without its primary)'; return 1
      fi
      want="$dir/$stem$pairs"
      if [ -e "$want" ]; then say 'pair:' "$(basename "$want") PRESENT"; say 'verdict:' 'OK'; return 0; fi
      say 'pair:' "$(basename "$want") ABSENT — a $form has its $pairs twin beside it"
      say 'verdict:' 'RED (pair absent)'; return 1;;
    d/)
      want="$(dirname "$dir")/d/c/$base"
      if [ -e "$want" ]; then say 'pair:' "d/c/$base PRESENT (the descriptor)"; say 'verdict:' 'OK'; return 0; fi
      say 'pair:' "d/c/$base ABSENT — a register keeps its columns in a descriptor"
      say 'verdict:' 'RED (pair absent)'; return 1;;
    [A-Z]*)
      found=$(ls "$dir"/"$pairs"-* 2>/dev/null | head -1)
      if [ -n "$found" ]; then say 'pair:' "$(basename "$found") PRESENT"; say 'verdict:' 'OK'; return 0; fi
      if [ "$form" = SCORE ]; then
        say 'pair:' "no $pairs-* beside it — a SCORE opens a SEAL; nothing sealed sits here"
        say 'verdict:' 'RED (pair absent)'; return 1
      fi
      verb=$(printf '%s' "$pairs" | tr 'A-Z' 'a-z'); case $verb in *e) verb="${verb}d" ;; *) verb="${verb}ed" ;; esac
      say 'pair:' "no $pairs-* beside it yet — pending (a $form is $verb later, not at birth)"
      say 'verdict:' 'PENDING'; return 0;;
    *)
      say 'pair:' "rule '$pairs' not understood by this script — register and script disagree"
      say 'verdict:' 'RED (unknown pair rule)'; return 1;;
  esac
}

# prove_red — every mutant must go RED for the named reason; every control must stay green
prove_red() {
  t=${TMPDIR:-/tmp}/wf-check.$$; mkdir -p "$t" || exit 2
  bad=0
  # The proof tests this script, not the house register, so it brings its own small register
  # (rows copied in shape from C4's c/wf) and runs the same outside C4. Normal checks still read
  # the real register.
  mkdir -p "$t/.reg/c" "$t/.reg/d/c"
  printf '%s\n' FORM ANSWERS FIRST_SECTION SHAPE FIELDS PAIRS COUNT EXAMPLE NOTE > "$t/.reg/d/c/wf"
  tab=$(printf '\t')
  while IFS='|' read -r f p; do
    printf '%s\n' "$f${tab}fixture answer${tab}-${tab}-${tab}-${tab}$p${tab}-${tab}-${tab}-"
  done > "$t/.reg/c/wf" <<'ROWS'
NOTE|-
CARD|-brief
VIEW|.txt
WAVE|-brief
SEAL|SCORE
SCORE|SEAL
REGISTER|d/
NEWS|-
CHANGELOG|-
INSTALL|-
MANUAL|-
ROWS
  REG="$t/.reg/c/wf"; DESC="$t/.reg/d/c/wf"
  case_() {  # case_ LABEL WANT-EXIT WANT-TEXT PATH
    out=$(check "$4" 2>&1); rc=$?
    if [ "$rc" -eq "$2" ] && printf '%s\n' "$out" | grep -q -- "$3"; then r=ok; else r=FAIL; bad=$((bad+1)); fi
    printf '%-4s %-44s exit %s (want %s), text '\''%s'\'' %s\n' "$r" "$1" "$rc" "$2" "$3" "$( printf '%s\n' "$out" | grep -q -- "$3" && echo found || echo MISSING)"
  }
  : > "$t/BOGUS-2026-09-11-a-rival-prefix.md"
  case_ 'mutant: unregistered prefix' 1 'UNREGISTERED' "$t/BOGUS-2026-09-11-a-rival-prefix.md"
  : > "$t/CARD-20260911T1150Z-caseworker-vibrobeast.md"
  case_ 'mutant: CARD without its -brief' 1 'ABSENT' "$t/CARD-20260911T1150Z-caseworker-vibrobeast.md"
  : > "$t/CARD-20260911T1150Z-caseworker-vibrobeast-brief.md"
  case_ 'control: CARD with its -brief' 0 'PRESENT' "$t/CARD-20260911T1150Z-caseworker-vibrobeast.md"
  : > "$t/CARD-20260911T1150Z-parents-c4-actual-brief.md"
  case_ 'control: a brief alone (output comes later)' 0 'a brief precedes its output' "$t/CARD-20260911T1150Z-parents-c4-actual-brief.md"
  : > "$t/VIEW-20260911T1200Z-on1gw.html"
  case_ 'mutant: VIEW without its .txt twin' 1 'ABSENT' "$t/VIEW-20260911T1200Z-on1gw.html"
  : > "$t/VIEW-20260911T1200Z-on1gw.txt"
  case_ 'control: VIEW with its .txt twin' 0 'PRESENT' "$t/VIEW-20260911T1200Z-on1gw.html"
  : > "$t/WAVE1-20260910T1013Z-apprentice-c4-actual-brief.md"
  case_ 'control: WAVE1 resolves to WAVE (digit)' 0 'the digit rides the prefix' "$t/WAVE1-20260910T1013Z-apprentice-c4-actual-brief.md"
  : > "$t/NOTE-fn.md"
  case_ 'mutant: prefix with no date' 1 'no date after the prefix' "$t/NOTE-fn.md"
  mkdir -p "$t/seal" "$t/score"
  : > "$t/score/SCORE-2026-09-11-sealed-hypotheses.md"
  case_ 'mutant: SCORE with no SEAL beside it' 1 'nothing sealed' "$t/score/SCORE-2026-09-11-sealed-hypotheses.md"
  : > "$t/seal/SEAL-2026-09-09-hypothesis-c4actual.sha256"
  case_ 'control: SEAL scored later (pending)' 0 'PENDING' "$t/seal/SEAL-2026-09-09-hypothesis-c4actual.sha256"
  : > "$t/seal/SCORE-2026-09-11-sealed-hypotheses.md"
  case_ 'control: SEAL with its SCORE beside it' 0 'PRESENT' "$t/seal/SEAL-2026-09-09-hypothesis-c4actual.sha256"
  : > "$t/NOTE-20261020-advice-ledger-date.md"
  case_ 'control: a YYYYMMDD date, as the advice ledger writes it' 0 'verdict:   OK' "$t/NOTE-20261020-advice-ledger-date.md"
  : > "$t/NOTE-2026102-seven-digits.md"
  case_ 'mutant: seven digits are not a date' 1 'no date after the prefix' "$t/NOTE-2026102-seven-digits.md"
  mkdir -p "$t/gnu/doc"; : > "$t/gnu/NEWS"; : > "$t/gnu/ChangeLog"; : > "$t/gnu/INSTALL"; : > "$t/gnu/doc/g.texi"
  case_ 'control: NEWS is the NEWS form' 0 'the GNU name' "$t/gnu/NEWS"
  case_ 'control: ChangeLog is the CHANGELOG form' 0 'the GNU name' "$t/gnu/ChangeLog"
  case_ 'control: INSTALL is the INSTALL form' 0 'the GNU name' "$t/gnu/INSTALL"
  case_ 'control: a .texi is the MANUAL form' 0 'a Texinfo manual' "$t/gnu/doc/g.texi"
  mkdir -p "$t/c" "$t/d/c"; : > "$t/c/p"
  case_ 'mutant: register without its descriptor' 1 'ABSENT' "$t/c/p"
  : > "$t/d/c/p"
  case_ 'control: register with d/c/ descriptor' 0 'PRESENT' "$t/c/p"
  rm -rf "$t"
  if [ "$bad" -eq 0 ]; then echo "prove-red: every mutant went RED and every control stayed green"; return 0; fi
  echo "prove-red: $bad case(s) misbehaved"; return 1
}

[ $# -ge 1 ] || usage
case "$1" in
  -h|--help) usage;;
  --prove-red) prove_red; exit $?;;
  --*) usage;;
  *) check "$1"; exit $?;;
esac
