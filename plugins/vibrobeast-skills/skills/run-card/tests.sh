#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- scripts/rc1rn against a small card planted in a temp dir.
#
#   sh tests.sh              the runner keeps every promise in its header, on a three-step card
#   sh tests.sh --prove-red  the above, then break rc1rn seven ways in a temp copy; exit 0 only if
#                            the real runner is green AND every break goes red
#
# What rc1rn promises (its header): FACTS are shown first and a NEED that does not hold stops the
# run before any step, saying what was seen and what was needed; `status` shows [x] done / [>] next
# / [ ] later and runs nothing; `next` runs only the first step whose DONE test fails, so running
# again is always safe; a step with a confirm question runs only on the answer yes; `run` goes on
# to the end; every step runs in WORKDIR; a failing step stops with its exit; a step that runs
# clean but whose DONE test still fails stops and says the card is wrong; every run appends a
# RECEIPT to <card>.log beside the card, and every invocation and answer is written down (the
# 2026-09-25 note); exit 0 ok, 1 a step stopped, 2 usage or no such card.
# This is the garden's own spec for its shipped copy. C4's tests/rc1rn-tests.sh covers C4's copy;
# the drift check against it runs only when C4_ROOT points at a C4 tree, and says SKIPPED if not.
# Needs: sh, grep, sed, awk.  Exit: 0 all good · 1 a case failed, or (--prove-red) a break went
# unnoticed · 77 a needed tool is missing (said)

set -u
here=$(cd "$(dirname "$0")" && pwd)
RC=$here/scripts/rc1rn
for tool in grep sed awk mktemp; do
	command -v "$tool" >/dev/null 2>&1 || { echo "tests.sh: $tool not found; cannot run the card runner's checks" >&2; exit 77; }
done
# a broken runner can loop for ever (a mutant that never marks a step done): every call is bounded
T=''; command -v timeout >/dev/null 2>&1 && T='timeout 20'
[ -f "$RC" ] || { echo "tests.sh: missing $RC" >&2; exit 1; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/rc1rn-tests.XXXXXX") || exit 1
trap 'rm -rf "$tmp"' EXIT
trap 'exit 1' INT TERM

ok() { if [ "$2" = 0 ]; then pass=$((pass + 1)); echo "PASS  $1"; else fail=$((fail + 1)); echo "FAIL  $1${3:+ -- $3}"; fi; }

card() { # card DIR -- a three-step card: plant, water, harvest (harvest asks first)
	mkdir -p "$1/bed"
	cat >"$1/garden.rc" <<CARD
CARD='RUNCARD-TEST-bed'
PURPOSE='Plant, water and harvest one bed.'
WORKDIR='$1/bed'
facts() { fact 'seed packet' "\$( [ -f seeds ] && echo here || echo gone)"; need 'trowel' "\$( [ -f trowel ] && echo yes || echo no)" yes; }
STEPS='plant water harvest'
plant_about='put the seed in'
plant_done() { [ -f planted ]; }
plant_run()  { echo plant >> ran; pwd > where; : > planted; }
water_about='water it'
water_done() { [ -f wet ]; }
water_run()  { echo water >> ran; : > wet; }
harvest_about='pick it (cannot be put back)'
harvest_confirm='This picks the plant. Ready?'
harvest_done() { [ -f picked ]; }
harvest_run()  { echo harvest >> ran; : > picked; }
CARD
}

suite() { # suite RC1RN_PATH
	r=$1; pass=0 fail=0
	d=$tmp/s.$$; rm -rf "$d"; mkdir -p "$d"; card "$d"; C=$d/garden.rc; B=$d/bed; L=$d/garden.log
	# run from inside the temp dir: a planted break that ignores WORKDIR then writes here, never into
	# the caller's folder (2026-10-04: one left `runs` and `cleaned` in the repo root)
	cd "$d" || return 1
	run() { TMPDIR=$d $T sh "$r" "$@" </dev/null 2>&1; }

	out=$(run "$C" next); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'trowel .*no   STOP: needed yes' && printf '%s\n' "$out" | grep -q 'STOPPED before any step' && [ ! -f "$B/ran" ]
	ok "a need that does not hold stops before any step, with saw and needed" $? "exit $rc"
	f1=$(printf '%s\n' "$out" | grep -n 'what this machine shows' | cut -d: -f1); s1=$(printf '%s\n' "$out" | grep -n -- '-- steps --' | cut -d: -f1)
	[ -n "$f1" ] && [ -n "$s1" ] && [ "$f1" -lt "$s1" ]; ok "facts are shown before the steps" $?
	: >"$B/trowel"
	out=$(run "$C"); rc=$?
	[ $rc = 0 ] && printf '%s\n' "$out" | grep -q '\[>\] plant' && printf '%s\n' "$out" | grep -q '\[ \] water' && [ ! -f "$B/ran" ]
	ok "status shows [>] next and [ ] later, exits 0, runs nothing" $? "exit $rc"
	run "$C" next >/dev/null; rc=$?
	[ $rc = 0 ] && [ "$(cat "$B/ran" 2>/dev/null)" = plant ]; ok "next runs one step, the first not done" $? "exit $rc ran=$(cat "$B/ran" 2>/dev/null)"
	[ "$(cat "$B/where" 2>/dev/null)" = "$(cd "$B" && pwd)" ]; ok "the step ran in WORKDIR" $? "ran in $(cat "$B/where" 2>/dev/null)"
	run "$C" next >/dev/null
	[ "$(tr '\n' ' ' <"$B/ran")" = "plant water " ]; ok "a done step is skipped: the second next runs the second step" $? "ran: $(tr '\n' ' ' <"$B/ran")"
	out=$(run "$C"); printf '%s\n' "$out" | grep -q '\[x\] plant' && printf '%s\n' "$out" | grep -q '\[x\] water' && printf '%s\n' "$out" | grep -q '\[>\] harvest'
	ok "done steps show [x]" $?
	out=$(printf 'no\n' | TMPDIR=$d $T sh "$r" "$C" next 2>&1); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'This picks the plant' && [ ! -f "$B/picked" ]
	ok "a confirm question: any answer but yes runs nothing, exit 1" $? "exit $rc"
	out=$(printf 'yes\n' | TMPDIR=$d $T sh "$r" "$C" run 2>&1); rc=$?
	[ $rc = 0 ] && [ -f "$B/picked" ] && printf '%s\n' "$out" | grep -q 'ALL DONE'
	ok "yes runs it; run goes on to ALL DONE, exit 0" $? "exit $rc"
	run "$C" run >/dev/null; rc=$?
	[ $rc = 0 ] && [ "$(wc -l <"$B/ran" | tr -d ' ')" = 3 ]; ok "running it all again repeats nothing" $? "exit $rc, $(wc -l <"$B/ran" | tr -d ' ') runs"
	[ -f "$L" ] && grep -q 'plant DONE' "$L" && grep -q 'harvest ASKED' "$L" && grep -q 'harvest DECLINED (answer: no)' "$L" && grep -q 'harvest CONFIRMED' "$L" && grep -q 'OPEN status' "$L" && grep -q 'STOP need-not-met' "$L"
	ok "the receipt log beside the card holds every invocation, question and answer" $?
	out=$(run "$C" log); [ $? = 0 ] && printf '%s\n' "$out" | grep -q 'harvest DONE'; ok "log mode prints the receipts" $?
	cat >>"$C" <<'CARD'
STEPS='plant water harvest weed mulch'
weed_about='pull the weeds'; weed_done() { [ -f weeded ]; }; weed_run() { echo 'no gloves'; return 4; }
mulch_about='mulch it'; mulch_done() { [ -f mulched ]; }; mulch_run() { :; }
CARD
	out=$(run "$C" next); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'step weed failed (exit 4)' && printf '%s\n' "$out" | grep -q 'no gloves' && grep -q 'weed FAILED exit=4' "$L"
	ok "a failing step stops, shows its output, logs its exit" $? "exit $rc"
	sed 's/weed_run() { echo .no gloves.; return 4; }/weed_run() { : > weeded; }/' "$C" >"$C.new" && mv "$C.new" "$C"
	run "$C" next >/dev/null; out=$(run "$C" next); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'done-test still says not done' && grep -q 'mulch RAN-NOT-DONE' "$L"
	ok "a step that runs clean but misses its effect stops and blames the card" $? "exit $rc"
	printf "CARD='x'\nSTEPS='a'\nWORKDIR='%s/nowhere'\na_done() { false; }; a_run() { :; }\n" "$d" >"$d/lost.rc"
	out=$(run "$d/lost.rc" next); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'STOP: no such folder'; ok "a WORKDIR that is not on this machine stops the run" $? "exit $rc"
	run "$d/nope.rc" >/dev/null; ok "no such card: exit 2" "$([ $? = 2 ]; echo $?)"
	printf "PURPOSE='no name'\n" >"$d/bare.rc"; run "$d/bare.rc" >/dev/null; ok "a card without CARD and STEPS: exit 2" "$([ $? = 2 ]; echo $?)"
	run --help | grep -q 'RUNCARD 1 RUN'; ok "--help prints the header" $?
	# 2026-10-04 (C4's 2026-09-28 guard, carried here): a card whose last step undoes its first looped
	# under `run`.  One `run` runs each step at most once, says why it stopped, and writes it down.
	mkdir -p "$d/loop"
	printf "CARD='loop'\nWORKDIR='%s/loop'\nSTEPS='make clean'\nmake_done() { [ -f made ]; }\nmake_run() { echo made >> runs; : > made; }\nclean_done() { [ -f cleaned ]; }\nclean_run() { echo cleaned >> runs; rm -f made; : > cleaned; }\n" "$d" >"$d/loop.rc"
	out=$(run "$d/loop.rc" run); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'would run a second time' && [ "$(cat "$d/loop/runs" 2>/dev/null)" = "$(printf 'made\ncleaned')" ] && grep -q 'make WOULD-RUN-TWICE' "$d/loop.log"
	ok "run never runs a step twice: a card whose last step undoes its first stops, once" $? "exit $rc"
	left=$(ls "$d" | grep '^rc1rn\.' | tr '\n' ' '); [ -z "$left" ]; ok "no scratch files left behind in TMPDIR" $? "left: $left"
	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once
	cat <<'M'
done steps are not skipped	do isdone "$s" || { printf	do false || { printf
a need that fails is ignored	[ "$NEEDFAIL" = 0 ] || { printf 'STOPPED before any step	true || { printf 'STOPPED before any step
the confirm question is not honoured	[ "$ans" = yes ] || {	true || {
WORKDIR is ignored	inwd() { if [ -n "$WORKDIR" ]; then cd "$WORKDIR" 2>/dev/null || return 3; fi; }	inwd() { :; }
receipts are not written	say_log() { printf '%s %s\n' "$(stamp)" "$*" >> "$LOG" 2>/dev/null || :; }	say_log() { :; }
a failed step is not reported	if [ "$rc" != 0 ]; then printf 'STOPPED: step	if false; then printf 'STOPPED: step
a step may run twice in one run	  case $RAN in *" $s "*)	  case $RAN in *" never-a-step "*)
M
}
mutate() { # mutate OLD NEW SRC DST, with awk (no python needed): OLD must occur exactly once
	# OLD and NEW travel in the environment: awk -v would turn their backslashes into escapes
	MUT_OLD=$1 MUT_NEW=$2 awk 'BEGIN { RS = "\001"; old = ENVIRON["MUT_OLD"]; new = ENVIRON["MUT_NEW"] } {
		n = 0; s = $0; o = ""
		while ((i = index(s, old)) > 0) { n++; o = o substr(s, 1, i - 1) new; s = substr(s, i + length(old)) }
		if (n != 1) { print "cannot plant: " n " occurrences" > "/dev/stderr"; exit 3 }
		printf "%s%s", o, s }' "$3" >"$4"
}

case ${1:-} in
"")
	echo "== rc1rn: the card runner keeps its header's promises =="
	suite "$RC"; r=$?
	echo "== ja1md: the job aid maker catches its own planted faults =="
	sh "$here/scripts/ja1md" --prove-red >"$tmp/ja1md.log" 2>&1; ok "ja1md --prove-red (a step without a why or a check is refused; words are escaped)" $?
	[ $fail = 0 ] || r=1
	if [ -n "${C4_ROOT:-}" ] && [ -f "$C4_ROOT/bin/rc1rn" ]; then
		cmp -s "$RC" "$C4_ROOT/bin/rc1rn"; ok "scripts/rc1rn is byte-equal to C4's bin/rc1rn (SKILL.md falsifier)" $?
		[ $fail = 0 ] || r=1
	else
		echo "SKIPPED  drift check against C4's bin/rc1rn -- set C4_ROOT to a C4 tree to run it"
	fi
	exit $r
	;;
--prove-red)
	[ -n "$T" ] || { echo "tests.sh: timeout not found; a planted break can hang the runner, so --prove-red needs it" >&2; exit 77; }
	echo "== controls: the real rc1rn =="
	suite "$RC" || { echo "PROVE-RED NOT OK -- the real runner is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t')
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$RC" "$tmp/rc1rn.mut"; then
			echo "BREAK NOT PLANTED  $mname -- rc1rn changed shape; update mutants()"; continue
		fi
		if suite "$tmp/rc1rn.mut" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken runner"
		else
			caught=$((caught + 1)); echo "CAUGHT  $mname -- $(grep '^FAIL' "$tmp/mutant.log" | head -1)"
		fi
	done <<M2
$(mutants)
M2
	echo
	echo "== ja1md: its own planted faults =="
	if sh "$here/scripts/ja1md" --prove-red >"$tmp/ja1md.log" 2>&1; then echo "CAUGHT  ja1md: $(tail -1 "$tmp/ja1md.log")"; else echo "MISSED  ja1md: $(grep FAIL "$tmp/ja1md.log" | head -1)"; n=$((n + 1)); fi
	if [ $caught = $n ] && [ $n -gt 0 ]; then
		echo "PROVE-RED OK -- controls green, $caught/$n planted breaks caught"; exit 0
	fi
	echo "PROVE-RED NOT OK -- $caught/$n planted breaks caught"; exit 1
	;;
*) echo "usage: sh tests.sh [--prove-red]" >&2; exit 2 ;;
esac
