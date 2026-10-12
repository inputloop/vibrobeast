#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# buckets.sh --- count the GIVENS buckets, check the invariant, report the stop rule.
#
# The method's real failure is declaring a stop you have not reached, and the person counting
# their own buckets is the one reader who cannot catch that -- the count and the fatigue arrive
# together. So this does the counting, and nothing else. It does not tell you what to walk next
# and it does not grade an entry: a tool that filled its own verdicts here would be deciding the
# plan rather than checking it.
#
# Usage:
#   sh buckets.sh BUCKETS.tsv     fill state + INVARIANT + STOP
#   sh buckets.sh --template      an empty buckets file with the nine shapes
#
# Input is TAB-separated: grp <TAB> entry <TAB> note   (grp is one of a..i; one row per entry)
# Comment lines (#) and a `grp` header row are ignored.
#
# Exit: 0 stop met and invariant held · 1 stop not met · 2 invariant violated or bad input.
# Exit 1 is not a failure -- an unmet stop is the normal state of a walk in progress.
#
# POSIX sh + awk. Part of the fortress-palace mint (2026-09-04, unblessed).

set -u

prog=${0##*/}

template() {
	cat <<'EOF'
# GIVENS buckets. One row per entry. grp <TAB> entry <TAB> note
# Walk i -> a, hardest first. First open group whose SHAPE it fits. No reassigns, no saving.
# No SECOND entry in any group until EVERY group has one.
# Stop: all-but-two groups filled twice, OR no unique ideation left in the local folders.
#
#   (i) intersects >=2x as many as (h), or >=8 without naming (h)
#   (h) intersects >=3 other problems
#   (g) x/y, locking, race condition or similar
#   (f) large technical, formal-study-rich area
#   (e) IRL consequence, contrived or in due course
#   (d) a logic / word problem
#   (c) statically modelled info MUTATED since last introduction
#   (b) statically modelled new input to session
#   (a) unmodelled significant new input, new to session
grp	entry	note
EOF
}

case ${1:-} in
--template) template; exit 0 ;;
-h | --help) echo "usage: $prog BUCKETS.tsv | $prog --template" ; exit 0 ;;
"") echo "usage: $prog BUCKETS.tsv | $prog --template" >&2; exit 2 ;;
esac

file=$1
[ -f "$file" ] || { echo "$prog: cannot read $file" >&2; exit 2; }

awk -F '\t' '
BEGIN {
	split("i h g f e d c b a", ord, " ")
	for (k = 1; k <= 9; k++) n[ord[k]] = 0
	shape["i"] = "intersects >=2x (h), or >=8 unnamed"
	shape["h"] = "intersects >=3 other problems"
	shape["g"] = "x/y, locking, race condition"
	shape["f"] = "large technical, study-rich"
	shape["e"] = "IRL consequence"
	shape["d"] = "logic / word problem"
	shape["c"] = "modelled, MUTATED since"
	shape["b"] = "modelled new input"
	shape["a"] = "unmodelled new input"
}
/^#/ { next }
/^[ \t]*$/ { next }
$1 == "grp" { next }
{
	g = $1
	gsub(/[()[:space:]]/, "", g)
	if (!(g in shape)) { printf "BAD-GROUP  row %d names `%s`, which is not one of a..i\n", NR, $1; badrow++; next }
	n[g]++
	order[++seq] = g          # arrival order, so the invariant can be checked as it happened
	label[g, n[g]] = $2
}
END {
	if (badrow) { print ""; print "input rejected"; exit 2 }

	# INVARIANT, checked against arrival order: at the moment a group took its SECOND entry,
	# was any group still empty? Checking only the final counts would miss this entirely --
	# a walk can end well-shaped and still have been filed wrong.
	for (k = 1; k <= 9; k++) live[ord[k]] = 0
	viol = 0
	for (s = 1; s <= seq; s++) {
		g = order[s]
		live[g]++
		if (live[g] == 2) {
			empties = ""
			for (k = 1; k <= 9; k++) if (live[ord[k]] == 0) empties = empties (empties ? "," : "") ord[k]
			if (empties != "") {
				viol++
				if (viol == 1) firstviol = sprintf("(%s) took a second entry while (%s) stood empty", g, empties)
			}
		}
	}

	printf "%-5s %-34s %6s  %s\n", "GRP", "SHAPE", "FILL", "ENTRIES"
	printf "%-5s %-34s %6s  %s\n", "---", "-----", "----", "-------"
	doubled = 0; singles = ""; empty = ""
	for (k = 1; k <= 9; k++) {
		g = ord[k]
		e = ""
		for (j = 1; j <= n[g]; j++) e = e (e ? " | " : "") label[g, j]
		mark = (n[g] >= 2) ? "**" : (n[g] == 1 ? "* " : "  ")
		printf "(%s)   %-34s %4d%s  %s\n", g, shape[g], n[g], mark, e
		if (n[g] >= 2) doubled++
		else if (n[g] == 1) singles = singles (singles ? "," : "") g
		else empty = empty (empty ? "," : "") g
	}

	print ""
	if (viol) {
		printf "INVARIANT  VIOLATED -- %s\n", firstviol
		print  "           No second entry belongs in any group until every group has one; this is"
		print  "           what keeps the walk a sample rather than a curated argument."
	} else {
		print "INVARIANT  held -- no group took a second entry while another stood empty"
	}

	if (empty != "") printf "EMPTY      (%s) -- the walk is not finished\n", empty
	if (singles != "") printf "AT ONE     (%s)\n", singles

	printf "STOP       %d of 9 groups filled twice -- ", doubled
	if (doubled >= 7) {
		print "MET (all but two)"
		print "           Met ON THIS CORPUS, never absolutely. Record what you actually walked"
		print "           beside this verdict, or it is a stop nobody can check."
		if (singles != "" && singles != "h,i" && singles != "i,h")
			printf "           Note: the two left at one are (%s). Leaving (h)/(i) single is the honest\n           choice -- padding the floor with a weak second entry fakes it.\n", singles
	} else {
		printf "NOT MET (need %d more)\n", 7 - doubled
	}

	if (viol) exit 2
	exit (doubled >= 7) ? 0 : 1
}
' "$file"
