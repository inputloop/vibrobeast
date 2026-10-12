#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- gauge.sh against the oracle, on two independent checks.
#
#   sh tests.sh              COUNTS (exact) + ORDERING (discriminating power)
#   sh tests.sh --prove-red  plant a wrong expectation and PROVE the harness reports it
#
# Why two checks and not one: exact counts catch a regression in a pattern, but they would still
# pass if someone "fixed" the gauges into something that no longer separates a jacket document
# from a rebuilt one. The ordering check is what says the gauge still has teeth. A suite that
# only checks counts can go green on a gauge that has stopped measuring anything.
#
# Exit: 0 all good · 1 a check failed, or (in --prove-red) the harness could NOT fail.

set -u

here=$(dirname "$0")
gauge=$here/scripts/gauge.sh
fx=$here/fixtures
oracle=$fx/expected.tsv

[ -f "$gauge" ] || { echo "tests.sh: missing $gauge" >&2; exit 2; }
[ -f "$oracle" ] || { echo "tests.sh: missing $oracle" >&2; exit 2; }

actual() { # actual ORACLE -> doc \t gauge \t num \t den \t ratio, for docs the oracle names
	awk -F '\t' '!/^#/ && $1 != "doc" && NF >= 5 { print $1 }' "$1" | sort -u |
		while read -r d; do
			[ -f "$fx/$d.md" ] || { echo "MISSING-FIXTURE	$d" ; continue; }
			sh "$gauge" --tsv "$fx/$d.md" | sed "s/^/$d	/"
		done
}

run_case() { # run_case ORACLE
	o=$1
	actual "$o" | awk -F '\t' -v O="$o" '
	BEGIN {
		while ((getline l < O) > 0) {
			if (l ~ /^#/) continue
			n = split(l, f, "\t")
			if (n < 5 || f[1] == "doc") continue
			key = f[1] SUBSEP f[2]
			want[key] = f[3] "/" f[4] "/" f[5]
		}
		close(O)
		# INF sorts above every finite ratio, which is what "affords nothing" should mean.
		BIG = 1e9
	}
	{
		key = $1 SUBSEP $2
		got = $3 "/" $4 "/" $5
		tot++
		if (!(key in want)) { fail++; printf "FAIL  counts    %-10s %-26s no oracle row\n", $1, $2; next }
		if (got == want[key]) { pass++; printf "PASS  counts    %-10s %-26s %s\n", $1, $2, got }
		else { fail++; printf "FAIL  counts    %-10s %-26s expected %s got %s\n", $1, $2, want[key], got }
		r[$2, $1] = ($5 == "INF") ? BIG : $5 + 0
		seen[$2] = 1
	}
	END {
		for (g in seen) {
			if (!((g, "jacket") in r) || !((g, "middling") in r) || !((g, "rebuilt") in r)) continue
			tot++
			if (r[g, "jacket"] >= r[g, "middling"] && r[g, "middling"] >= r[g, "rebuilt"]) {
				pass++; printf "PASS  ordering  %-37s jacket >= middling >= rebuilt\n", g
			} else {
				fail++
				printf "FAIL  ordering  %-37s %.2f / %.2f / %.2f -- gauge no longer discriminates\n", \
					g, r[g, "jacket"], r[g, "middling"], r[g, "rebuilt"]
			}
		}
		printf "\n%d/%d pass, %d fail\n", pass + 0, tot + 0, fail + 0
		if (tot == 0) { print "no checks ran -- the harness is not running"; exit 1 }
		exit (fail > 0) ? 1 : 0
	}'
}

case ${1:-} in
--prove-red)
	tmp=${TMPDIR:-/tmp}/gauge-prove-red.$$
	awk -F '\t' -v OFS='\t' '{ if ($1 == "middling" && $2 == "claim-per-citation" && NF >= 5) $5 = "9.99"; print }' \
		"$oracle" >"$tmp" || { echo "tests.sh: could not stage the planted oracle" >&2; exit 2; }
	echo "== PROVE-RED: middling/claim-per-citation expectation changed 2.33 -> 9.99 =="
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
	echo "== gauge.sh vs the oracle: exact counts + discriminating power =="
	run_case "$oracle"
	;;
*)
	echo "usage: sh tests.sh [--prove-red]" >&2
	exit 2
	;;
esac
