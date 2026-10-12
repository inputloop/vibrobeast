#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- pmnotes.sh against the oracle, plus a coverage check.
#
#   sh tests.sh              verdict per note + every verdict reachable
#   sh tests.sh --prove-red  plant a wrong expectation and PROVE the harness reports it
#
# The coverage check is the second leg: exact verdicts catch a regression, but they would still
# pass if the checker quietly lost the ability to REACH a verdict that no fixture exercises.
# Asserting that all six appear keeps the fixture set honest as the checker grows.
#
# Exit: 0 all good · 1 a check failed, or (in --prove-red) the harness could NOT fail.

set -u

here=$(dirname "$0")
tool=$here/scripts/pmnotes.sh
fx=$here/fixtures
oracle=$fx/expected.tsv
notes=$fx/notes.md

[ -f "$tool" ] || { echo "tests.sh: missing $tool" >&2; exit 2; }
[ -f "$oracle" ] || { echo "tests.sh: missing $oracle" >&2; exit 2; }
[ -f "$notes" ] || { echo "tests.sh: missing $notes" >&2; exit 2; }

run_case() { # run_case ORACLE
	sh "$tool" --tsv "$notes" | awk -F '\t' -v O="$1" '
	BEGIN {
		while ((getline l < O) > 0) {
			if (l ~ /^#/) continue
			n = split(l, f, "\t")
			if (n < 2 || f[1] == "verdict") continue
			want[f[2]] = f[1]
		}
		close(O)
		split("OK GUESS NO-TRIGGERS UNNAMED-SOURCE UNSOURCED UNFALSIFIABLE", all, " ")
	}
	{
		seam = $2; got = $1
		tot++
		s = (length(seam) > 44) ? substr(seam, 1, 41) "..." : seam
		if (!(seam in want)) { fail++; printf "FAIL  verdict   %-46s no oracle row\n", s; next }
		if (got == want[seam]) { pass++; printf "PASS  verdict   %-46s %s\n", s, got }
		else { fail++; printf "FAIL  verdict   %-46s expected %s got %s\n", s, want[seam], got }
		seen[got] = 1
	}
	END {
		for (i = 1; i <= 6; i++) {
			tot++
			if (all[i] in seen) { pass++; printf "PASS  coverage  %-46s reachable\n", all[i] }
			else { fail++; printf "FAIL  coverage  %-46s no fixture reaches it\n", all[i] }
		}
		printf "\n%d/%d pass, %d fail\n", pass + 0, tot + 0, fail + 0
		if (tot == 0) { print "no checks ran -- the harness is not running"; exit 1 }
		exit (fail > 0) ? 1 : 0
	}'
}

case ${1:-} in
--prove-red)
	tmp=${TMPDIR:-/tmp}/pmnotes-prove-red.$$
	awk -F '\t' -v OFS='\t' '{ if ($1 == "UNNAMED-SOURCE") $1 = "OK"; print }' "$oracle" >"$tmp" ||
		{ echo "tests.sh: could not stage the planted oracle" >&2; exit 2; }
	echo "== PROVE-RED: the UNNAMED-SOURCE expectation changed to OK =="
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
	echo "== pmnotes.sh vs the oracle, plus verdict coverage =="
	run_case "$oracle"
	;;
*)
	echo "usage: sh tests.sh [--prove-red]" >&2
	exit 2
	;;
esac
