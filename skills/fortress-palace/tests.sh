#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- buckets.sh against the oracle: exit code, invariant verdict, stop verdict.
#
#   sh tests.sh              every fixture
#   sh tests.sh --prove-red  plant a wrong expectation and PROVE the harness reports it
#
# Exit: 0 all good · 1 a check failed, or (in --prove-red) the harness could NOT fail.

set -u

here=$(dirname "$0")
tool=$here/scripts/buckets.sh
fx=$here/fixtures
oracle=$fx/expected.tsv

[ -f "$tool" ] || { echo "tests.sh: missing $tool" >&2; exit 2; }
[ -f "$oracle" ] || { echo "tests.sh: missing $oracle" >&2; exit 2; }

check() { # check NAME WANT_EXIT WANT_INV WANT_STOP -> prints PASS/FAIL lines, returns fail count
	name=$1; wexit=$2; winv=$3; wstop=$4
	out=$(sh "$tool" "$fx/$name.tsv" 2>&1); gexit=$?
	f=0

	[ "$gexit" = "$wexit" ] &&
		printf 'PASS  exit       %-14s %s\n' "$name" "$gexit" ||
		{ printf 'FAIL  exit       %-14s expected %s got %s\n' "$name" "$wexit" "$gexit"; f=$((f + 1)); }

	ginv=$(printf '%s\n' "$out" | awk '/^INVARIANT/ { print ($2 == "VIOLATED") ? "VIOLATED" : "held" }')
	[ "$ginv" = "$winv" ] &&
		printf 'PASS  invariant  %-14s %s\n' "$name" "$ginv" ||
		{ printf 'FAIL  invariant  %-14s expected %s got %s\n' "$name" "$winv" "${ginv:-none}"; f=$((f + 1)); }

	gstop=$(printf '%s\n' "$out" | awk '/^STOP/ { print (/NOT MET/) ? "NOT MET" : "MET" }')
	[ "$gstop" = "$wstop" ] &&
		printf 'PASS  stop       %-14s %s\n' "$name" "$gstop" ||
		{ printf 'FAIL  stop       %-14s expected %s got %s\n' "$name" "$wstop" "${gstop:-none}"; f=$((f + 1)); }

	return $f
}

run_case() { # run_case ORACLE
	pass=0; fail=0
	# shellcheck disable=SC2162
	while IFS='	' read -r name wexit winv wstop; do
		case ${name:-} in '' | '#'* | fixture) continue ;; esac
		[ -f "$fx/$name.tsv" ] || { echo "FAIL  fixture    $name  missing"; fail=$((fail + 1)); continue; }
		check "$name" "$wexit" "$winv" "$wstop"
		f=$?
		fail=$((fail + f))
		pass=$((pass + 3 - f))
	done <"$1"
	printf '\n%d/%d pass, %d fail\n' "$pass" "$((pass + fail))" "$fail"
	[ "$fail" -eq 0 ]
}

case ${1:-} in
--prove-red)
	tmp=${TMPDIR:-/tmp}/buckets-prove-red.$$
	awk -F '\t' -v OFS='\t' '{ if ($1 == "violated" && NF >= 4) $3 = "held"; print }' "$oracle" >"$tmp" ||
		{ echo "tests.sh: could not stage the planted oracle" >&2; exit 2; }
	echo "== PROVE-RED: the violated fixture's invariant expectation changed VIOLATED -> held =="
	if run_case "$tmp"; then
		rm -f "$tmp"
		echo
		echo "HARNESS FAULT: a deliberately wrong expectation did not produce a FAIL."
		echo "Until this reports red, treat every green run as unproven."
		exit 1
	fi
	rm -f "$tmp"
	echo
	echo "PROVE-RED OK -- the harness reported the planted wrong expectation."
	exit 0
	;;
"")
	echo "== buckets.sh vs the oracle =="
	run_case "$oracle"
	;;
*)
	echo "usage: sh tests.sh [--prove-red]" >&2
	exit 2
	;;
esac
