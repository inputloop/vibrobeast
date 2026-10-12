#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# pencil.sh --- sort a concern's DISPOSITION under own-error-is-the-relaxable-layer.
#
# What it is: a deterministic rule applied to facts YOU declare. Every input is a column you
# wrote and can strike; the scale lives in levels.tsv, not in here. The tool composes a verdict
# from the ladder and prints the sentence that produced it -- it does not weigh, rank, score, or
# decide anything you did not already write down. If it printed a bare verdict with no sentence,
# it would be a machine making a judgement it will not defend.
#
# Usage:
#   sh pencil.sh FILE                 verdicts for every concern row in FILE
#   sh pencil.sh FILE -r 0.5          same, evaluated at reality 0.5
#   sh pencil.sh --rules              print the rule ladder, in order
#   sh pencil.sh --levels-table       print the ink scale currently in force
#
# Exit: 0 all rows resolved · 1 one or more rows REFUSED · 2 usage or unreadable input.
#
# POSIX sh + awk, no dependencies. Part of the pencil-your-own mint (2026-09-04, unblessed).

set -u

prog=${0##*/}
here=$(dirname "$0")
levels=${PENCIL_LEVELS:-$here/../levels.tsv}
reality=1.0
file=

usage() {
	cat <<EOF
usage: $prog [-r REALITY] [-l LEVELS] FILE
       $prog --rules
       $prog --levels-table

  -r, --reality N   evaluate gating at reality N in [0,1] (default 1.0)
  -l, --levels F    ink scale to use (default \$PENCIL_LEVELS or ../levels.tsv)

A concern row is TAB-separated: id, source, owner, floor, witnesses, level, falsifier.
Columns past the seventh are ignored, so an oracle file with an expect column reads fine here.
EOF
}

rules() {
	cat <<'EOF'
THE RULE LADDER --- first match wins. The order is the whole design.

  1  floor = yes            FLOOR       the safety floor does not relax, at any reality, for any
                                        source tag. It is checked FIRST so that a floor item with
                                        no named falsifier can never be dismissed as a feeling.
  2  owner != me            NOT-YOURS   another party holds this ink. Route it to them. Softening
                                        someone else's claim so your work can proceed is the abuse
                                        this whole move enables, and it is refused.
  3  source != MINE         HOLD        the record is yours, the claim is not. A law you restated
                                        is still the law; it may legitimately stop the work.
  4  falsifier = -          FEELING     no check that could fail it. Label it and move. Only
                                        reachable for claims that are actually yours.
  5  witnesses >= 2         STANDS      two independent witnesses, not counting you. There is
                                        nothing of yours left to relax; state it plainly.
  6  otherwise              PENCIL      yours, single-sourced. Proceed and NAME it in one specific
                                        line, marked single-sourced. This is the common case, and
                                        it is the one the reflex gets wrong.

GATING --- a concern of ink k gates while reality r >= 1 - k. Fully inked gates everywhere; an
uninked line gates only under a full reality check. The scale is in levels.tsv, by words.
EOF
}

while [ $# -gt 0 ]; do
	case $1 in
	-r | --reality)
		[ $# -ge 2 ] || { echo "$prog: $1 needs a value" >&2; exit 2; }
		reality=$2
		shift 2
		;;
	-l | --levels)
		[ $# -ge 2 ] || { echo "$prog: $1 needs a value" >&2; exit 2; }
		levels=$2
		shift 2
		;;
	--rules)
		rules
		exit 0
		;;
	--levels-table)
		[ -f "$levels" ] || { echo "$prog: cannot read $levels" >&2; exit 2; }
		grep -v '^#' "$levels"
		exit 0
		;;
	-h | --help)
		usage
		exit 0
		;;
	-*)
		echo "$prog: unknown option $1" >&2
		usage >&2
		exit 2
		;;
	*)
		file=$1
		shift
		;;
	esac
done

[ -n "$file" ] || { usage >&2; exit 2; }
[ -f "$file" ] || { echo "$prog: cannot read $file" >&2; exit 2; }
[ -f "$levels" ] || { echo "$prog: cannot read levels file $levels" >&2; exit 2; }

awk -F '\t' -v R="$reality" -v LV="$levels" '
BEGIN {
	while ((getline line < LV) > 0) {
		if (line ~ /^#/ || line ~ /^[ \t]*$/) continue
		n = split(line, f, "\t")
		if (n < 2 || f[1] == "name") continue
		lvl[f[1]] = f[2] + 0
		byval[sprintf("%.4f", f[2] + 0)] = f[1]
		words = words (words ? ", " : "") f[1]
	}
	close(LV)
	if (words == "") { print "pencil.sh: levels file held no rows" > "/dev/stderr"; exit 2 }
	printf "%-22s %-16s %-18s %s\n", "ID", "VERDICT", "GATE", "WHY"
	printf "%-22s %-16s %-18s %s\n", "----", "-------", "----", "---"
}
/^#/ { next }
/^[ \t]*$/ { next }
$1 == "id" { next }
{
	id = $1; src = $2; own = $3; flr = $4; wit = $5 + 0; lev = $6; fal = $7
	gate = "-"
	if (lev ~ /^[0-9]*\.?[0-9]+$/) {
		w = byval[sprintf("%.4f", lev + 0)]
		verdict = "REFUSED-LITERAL"
		why = "file by words: a row carries the name, never the level" \
		      (w ? " -- you meant `" w "`" : " -- no word in the scale has level " lev)
		bad++
	} else if (!(lev in lvl)) {
		verdict = "REFUSED-UNKNOWN"
		why = "no row for level `" lev "` in the scale; known words: " words
		bad++
	} else {
		stop = 1 - lvl[lev]
		gate = sprintf("r>=%.2f %s", stop, (R + 0 >= stop) ? "GATING" : "relaxed")
		if (flr == "yes") {
			verdict = "FLOOR"
			# The level arithmetic must NOT be printed here. A floor item carries an ink
			# word like any other row, but rule 1 says it gates at every reality -- so
			# showing its 1-level stop would advertise a relaxation the ladder refuses.
			# The gate column has to agree with the verdict or the tool is lying quietly.
			gate = "always"
			why = "rule 1 -- the safety floor does not relax, at any reality, for any source"
		} else if (own != "me") {
			verdict = "NOT-YOURS"
			why = "rule 2 -- ink held by `" own "`; route it, do not soften it"
		} else if (src != "MINE") {
			verdict = "HOLD"
			why = "rule 3 -- traces to [" src "]; my record, not my claim"
		} else if (fal == "-" || fal == "") {
			verdict = "FEELING"
			why = "rule 4 -- no check that could fail it; label it and move"
		} else if (wit >= 2) {
			verdict = "STANDS"
			why = "rule 5 -- " wit " independent witnesses; nothing of mine left to relax"
		} else {
			verdict = "PENCIL"
			why = "rule 6 -- mine, " wit " outside witness(es); proceed and name it, marked single-sourced"
		}
	}
	count[verdict]++
	rows++
	printf "%-22s %-16s %-18s %s\n", id, verdict, gate, why
}
END {
	printf "\n== %d rows at reality %.2f ==\n", rows, R + 0
	split("FLOOR NOT-YOURS HOLD FEELING STANDS PENCIL REFUSED-LITERAL REFUSED-UNKNOWN", order, " ")
	for (i = 1; i <= 8; i++) {
		v = order[i]
		if (count[v]) printf "%-18s %d\n", v, count[v]
	}
	if (bad) {
		printf "REFUSED %d row(s) -- the scale is data; fix the row or edit the levels file.\n", bad
		exit 1
	}
	exit 0
}
' "$file"
