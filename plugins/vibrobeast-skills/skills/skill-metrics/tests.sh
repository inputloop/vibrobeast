#!/bin/sh
# tests.sh -- the skill-metrics suite: sk2mt against SPEC.md, plus the second reader.
#
#   sh tests.sh              run every check (shell), then tests/test_spec.py (python, if present)
#   sh tests.sh --prove-red  plant a wrong expectation; PASS only if the harness reports it
#
# Exit: 0 all good · 1 a check failed (or, with --prove-red, the harness could NOT fail).
# Copyright 2026 Corwin Brust <corwin@bru.st> -- GPLv3-or-later. Authored by Mentat (for Corwin).
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
set -u
LC_ALL=C; export LC_ALL
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
S="sh $here/scripts/sk2mt"
t=$(mktemp -d 2>/dev/null) || { t=${TMPDIR:-/tmp}/sk2mt-tests.$$; mkdir -p "$t"; }
trap 'rm -rf "$t"' EXIT INT TERM
pass=0; fail=0; RED=${1:-}
ok()  { pass=$((pass+1)); echo "ok   $1"; }
bad() { fail=$((fail+1)); echo "FAIL $1 -- $2"; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "want [$3] got [$2]"; fi; }
R="$S -C $t/m"; D=--date; T1=2026-09-01T00:00:00Z; T2=2026-09-02T00:00:00Z

# S2 -- a named root is never created
$R state >/dev/null 2>&1; eq "S2 missing root is NOTVISIBLE (3)" $? 3
[ -d "$t/m" ]; eq "S2 missing root was not created" $? 1
$R init >/dev/null; eq "S2 init creates" "$(sed -n 1p "$t/m/log")" "ITEM STATE CUR LAST DATE NOTE"
$R init >/dev/null; eq "S2 init twice keeps one header" "$(wc -l < "$t/m/log" | tr -d ' ')" 1

# S1 -- validation
$R set 'bad/name' OK >/dev/null 2>&1; eq "S1 ITEM with / refused" $? 2
$R set .hidden OK >/dev/null 2>&1;    eq "S1 ITEM with leading . refused" $? 2
$R set x 'TWO WORDS' >/dev/null 2>&1; eq "S1 STATE with space refused" $? 2
$R set x OK $D yesterday >/dev/null 2>&1; eq "S3 bad DATE refused" $? 2
eq "S1 refusals wrote nothing" "$(wc -l < "$t/m/log" | tr -d ' ')" 1

# S4 -- writing
$R set polygram GREEN $D $T1 --note 'first  run	tab' >/dev/null
eq "S4 first row" "$(sed -n 2p "$t/m/log")" "polygram GREEN NONE NONE $T1 first run tab"
eq "S4 item file holds STATE only" "$(cat "$t/m/skill-metrics/polygram")" GREEN
out=$($R set polygram GREEN $D $T2); case $out in UNCHANGED*) ok "S4 same state, no file -> UNCHANGED";; *) bad "S4 unchanged" "$out";; esac
eq "S4 unchanged wrote no row" "$(wc -l < "$t/m/log" | tr -d ' ')" 2
printf 'v1\n' > "$t/SKILL.md"; $R set polygram GREEN $D $T2 --file "$t/SKILL.md" >/dev/null
c1=$($R cur polygram)
case $c1 in archive/polygram/????????????????-SKILL.md) ok "S2 archive name is H16-NAME";; *) bad "S2 archive name" "$c1";; esac
eq "S4 new constituent -> LAST=NONE on first archive" "$($R last polygram)" NONE
$R set polygram GREEN $D $T2 --file "$t/SKILL.md" >/dev/null
eq "S4 same bytes again -> no row" "$(wc -l < "$t/m/log" | tr -d ' ')" 3
printf 'v2\n' > "$t/SKILL.md"; $R set polygram RED $D $T2 --file "$t/SKILL.md" >/dev/null
eq "S4 changed bytes -> LAST is old CUR" "$($R last polygram)" "$c1"
$R set polygram RED $D $T2 >/dev/null; eq "S4 no --file carries CUR" "$(wc -l < "$t/m/log" | tr -d ' ')" 4
$R set polygram RED $D $T2 --force >/dev/null; eq "S4 --force writes anyway" "$(wc -l < "$t/m/log" | tr -d ' ')" 5
$R set 'we ird' OK >/dev/null 2>&1; printf 'x y\n' > "$t/a b.md"; $R set card-games.el OK $D $T1 --file "$t/a b.md" >/dev/null
case $($R cur card-games.el) in archive/card-games.el/*-a_b.md) ok "S2 NAME chars outside set become _";; *) bad "S2 name squeeze" "$($R cur card-games.el)";; esac

# S5 -- reading, POSIX grep semantics over names
$R set gf-02-layered-assurance OK $D $T1 >/dev/null; $R set layered FAULT $D $T1 >/dev/null
eq "S5 one exact name -> bare value" "$($R state polygram)" RED
eq "S5 exact names are -F -x (no substring)" "$($R state layered)" FAULT
eq "S5 two names -> labelled, C order" "$($R state polygram layered | tr '\n' '|')" "layered FAULT|polygram RED|"
eq "S5 -e is BRE substring" "$($R items -e layered | tr '\n' ' ')" "gf-02-layered-assurance layered "
eq "S5 -x whole name" "$($R items -x -e layered)" layered
eq "S5 -E alternation" "$($R items -E -e '^(poly|card)' | tr '\n' ' ')" "card-games.el polygram "
eq "S5 -F fixed dot" "$($R items -F -e .el)" card-games.el
eq "S5 -i" "$($R items -i POLYGRAM)" polygram
eq "S5 -v" "$($R items -v -e e | tr '\n' ' ')" "polygram "
eq "S5 -c" "$($R state -c -e e)" 3
$R state -q nosuch; eq "S5 no match exits 1" $? 1
$R state -w layered >/dev/null 2>&1; eq "S5 GNU -w refused" $? 2
$R state -e x polygram >/dev/null 2>&1; eq "S5 names + patterns refused" $? 2
$R state polygram -e x >/dev/null 2>&1; eq "S5 option after a name refused (POSIX order)" $? 2
printf 'poly\n^card\n' > "$t/pats"; eq "S5 -f FILE" "$($R items -f "$t/pats" | tr '\n' ' ')" "card-games.el polygram "
eq "S5 --state filters by last STATE" "$($R items --state OK | tr '\n' ' ')" "card-games.el gf-02-layered-assurance "
eq "S5 -e matches names, not states" "$($R items -e RED)" ""
eq "S5 --state composes with a pattern" "$($R items --state OK -e gf)" gf-02-layered-assurance
eq "S5 note view" "$($R note layered)" -
eq "S5 date view" "$($R date layered)" $T1
eq "S5 log view shows history" "$($R log polygram | wc -l | tr -d ' ')" 5
case $($R say polygram) in "polygram is RED, last changed 2026-09-02 at 00:00 UTC (4 events logged). The current copy"*) ok "S5 say is a sentence";; *) bad "S5 say" "$($R say polygram)";; esac

# S6 -- the check
$R check >/dev/null; eq "S6 clean store passes" $? 0
echo GREEN > "$t/m/skill-metrics/polygram"; $R check >/dev/null; eq "S6 item file drift faults" $? 1
echo RED > "$t/m/skill-metrics/polygram"
echo tampered >> "$t/m/$($R cur polygram)"; $R check >/dev/null; eq "S6 tampered archive faults" $? 1

# --prove-red: a planted wrong expectation must be reported
if [ "$RED" = --prove-red ]; then
  before=$fail; eq "PLANTED (must FAIL)" "$($R state polygram)" GREEN >/dev/null
  if [ $fail -gt $before ]; then echo "prove-red: harness went red on the planted expectation -- PASS"; exit 0
  else echo "prove-red: harness could NOT fail -- FAIL"; exit 1; fi
fi

if [ -f "$here/tests/test_spec.py" ] && command -v python3 >/dev/null 2>&1; then
  if python3 "$here/tests/test_spec.py" >"$t/py.out" 2>&1; then ok "second reader (python, from SPEC.md): $(tail -1 "$t/py.out")"
  else bad "second reader (python)" "$(tail -5 "$t/py.out")"; fi
fi
echo "TOTAL pass=$pass fail=$fail"
[ $fail -eq 0 ]
