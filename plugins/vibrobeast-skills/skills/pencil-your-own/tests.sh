#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- run fixtures.tsv against pencil.sh and compare to the oracle column.
#
#   sh tests.sh              every fixture row: expected verdict vs actual
#   sh tests.sh --prove-red  plant a wrong expectation and PROVE the harness reports it
#
# The second mode is the point. Corwin's law: if you cannot demonstrate the check going red, it
# is not a check. A green suite that cannot go red is indistinguishable from a suite that is not
# running, so this harness ships with a way to show its own teeth.
#
# Exit: 0 all good · 1 a fixture failed, or (in --prove-red) the harness could NOT fail.

set -u

here=$(dirname "$0")
pencil=$here/scripts/pencil.sh
fixtures=$here/fixtures.tsv

[ -f "$pencil" ] || { echo "tests.sh: missing $pencil" >&2; exit 2; }
[ -f "$fixtures" ] || { echo "tests.sh: missing $fixtures" >&2; exit 2; }

run_case() {
	sh "$pencil" "$1" 2>/dev/null | awk -v FX="$1" '
	BEGIN {
		while ((getline line < FX) > 0) {
			if (line ~ /^#/ || line ~ /^[ \t]*$/) continue
			n = split(line, f, "\t")
			if (f[1] == "id" || n < 8) continue
			want[f[1]] = f[8]
		}
		close(FX)
	}
	$1 in want {
		tot++
		if ($2 == want[$1]) { pass++; printf "PASS  %-22s %s\n", $1, $2 }
		else { fail++; printf "FAIL  %-22s expected %-16s got %s\n", $1, want[$1], $2 }
	}
	END {
		printf "\n%d/%d pass, %d fail\n", pass + 0, tot + 0, fail + 0
		if (tot == 0) { print "no fixtures matched -- the harness is not running" ; exit 1 }
		exit (fail > 0) ? 1 : 0
	}'
}

case ${1:-} in
--prove-red)
	tmp=${TMPDIR:-/tmp}/pencil-prove-red.$$
	awk -F '\t' -v OFS='\t' '{ if ($1 == "mine-single" && NF >= 8) $8 = "STANDS"; print }' \
		"$fixtures" >"$tmp" || { echo "tests.sh: could not stage the planted fixture" >&2; exit 2; }
	echo "== PROVE-RED: mine-single's expectation deliberately changed PENCIL -> STANDS =="
	if run_case "$tmp"; then
		rm -f "$tmp"
		echo
		echo "HARNESS FAULT: a deliberately wrong expectation did not produce a FAIL."
		echo "Until this reports red, treat every green run above as unproven."
		exit 1
	fi
	rm -f "$tmp"
	echo
	echo "PROVE-RED OK -- the harness reported the planted wrong expectation."
	exit 0
	;;
"")
	echo "== fixtures vs oracle =="
	run_case "$fixtures"
	;;
*)
	echo "usage: sh tests.sh [--prove-red]" >&2
	exit 2
	;;
esac
