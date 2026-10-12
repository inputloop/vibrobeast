#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# gauge.sh --- count what you told it to count. Print the ratio. Stop.
#
# It prints NO verdict, NO grade, NO threshold. That refusal is the design: a threshold
# picked-not-validated is the same fault these gauges exist to catch, so the tool that measures
# guesses does not get to ink one of its own. The scale lives in gauges.tsv, which you edit.
#
# Usage:
#   sh gauge.sh DOC                     every gauge over DOC
#   sh gauge.sh --compare OLD NEW       both, plus the delta -- the number you actually wanted
#   sh gauge.sh --list                  the gauges currently in force
#   sh gauge.sh -g FILE DOC             use a different gauges file
#
# INF means the denominator is zero: the document affords the reader nothing on that axis. It is
# a result, not an error. Exit is 0 whenever the run completed; a gauge never fails a document.
#
# POSIX sh + grep + awk. Part of the countable-gauge mint (2026-09-04, unblessed).

set -u

prog=${0##*/}
here=$(dirname "$0")
gauges=${GAUGE_FILE:-$here/../gauges.tsv}
mode=one
a=
b=

usage() {
	cat <<EOF
usage: $prog [-g GAUGES] DOC
       $prog [-g GAUGES] --compare OLD NEW
       $prog [-g GAUGES] --list
EOF
}

while [ $# -gt 0 ]; do
	case $1 in
	-g | --gauges)
		[ $# -ge 2 ] || { echo "$prog: $1 needs a value" >&2; exit 2; }
		gauges=$2; shift 2 ;;
	--compare) mode=compare; shift ;;
	--list) mode=list; shift ;;
	--tsv) mode=tsv; shift ;;
	-h | --help) usage; exit 0 ;;
	-*) echo "$prog: unknown option $1" >&2; usage >&2; exit 2 ;;
	*)
		if [ -z "$a" ]; then a=$1; else b=$1; fi
		shift ;;
	esac
done

[ -f "$gauges" ] || { echo "$prog: cannot read gauges file $gauges" >&2; exit 2; }

if [ "$mode" = list ]; then
	printf '%-26s %s\n' "GAUGE" "A HIGH RATIO MEANS"
	printf '%-26s %s\n' "-----" "------------------"
	grep -v '^#' "$gauges" | awk -F '\t' 'NF>=4 && $1!="name" { printf "%-26s %s\n", $1, $4 }'
	exit 0
fi

# count PATTERN FILE -> integer. grep -o so repeats on one line each count once, which is what
# "mentions" means; -i because a heading and a sentence spell the same word differently.
count() {
	grep -oEi -- "$1" "$2" 2>/dev/null | wc -l | tr -d ' '
}

# ratio NUM DEN -> printed ratio, or INF when DEN is zero.
ratio() {
	awk -v n="$1" -v d="$2" 'BEGIN{ if (d+0==0) print "INF"; else printf "%.2f", n/d }'
}

measure() { # measure FILE -> lines of "name num den ratio"
	grep -v '^#' "$gauges" | while IFS='	' read -r name num den meaning; do
		[ -n "${name:-}" ] || continue
		[ "$name" != "name" ] || continue
		[ -n "${den:-}" ] || continue
		n=$(count "$num" "$1")
		d=$(count "$den" "$1")
		printf '%s\t%s\t%s\t%s\n' "$name" "$n" "$d" "$(ratio "$n" "$d")"
	done
}

[ -n "$a" ] || { usage >&2; exit 2; }
[ -f "$a" ] || { echo "$prog: cannot read $a" >&2; exit 2; }

if [ "$mode" = compare ]; then
	[ -n "$b" ] || { echo "$prog: --compare needs two documents" >&2; exit 2; }
	[ -f "$b" ] || { echo "$prog: cannot read $b" >&2; exit 2; }
	tmpa=${TMPDIR:-/tmp}/gauge-a.$$
	tmpb=${TMPDIR:-/tmp}/gauge-b.$$
	measure "$a" >"$tmpa"
	measure "$b" >"$tmpb"
	printf '%-26s %12s %12s %10s\n' "GAUGE" "OLD" "NEW" "DELTA"
	printf '%-26s %12s %12s %10s\n' "-----" "---" "---" "-----"
	join -t '	' -j 1 "$tmpa" "$tmpb" 2>/dev/null | awk -F '\t' '
	{
		old = $4; new = $7
		if (old == "INF" || new == "INF") d = "--"
		else d = sprintf("%+.2f", new - old)
		printf "%-26s %12s %12s %10s\n", $1, old " (" $2 "/" $3 ")", new " (" $5 "/" $6 ")", d
	}'
	rm -f "$tmpa" "$tmpb"
	echo
	echo "A delta of 0.00 across every gauge is a result too: either the improvement was somewhere"
	echo "these gauges do not look (say where), or it was a feeling (say that)."
	exit 0
fi

# --tsv: name, num, den, ratio and nothing else. The human view below carries a prose footer,
# which makes it unparseable -- so the composable form is its own mode rather than something a
# caller has to strip with awk and get subtly wrong.
if [ "$mode" = tsv ]; then
	measure "$a"
	exit 0
fi

printf '%-26s %8s %8s %8s  %s\n' "GAUGE" "NUM" "DEN" "RATIO" "A HIGH RATIO MEANS"
printf '%-26s %8s %8s %8s  %s\n' "-----" "---" "---" "-----" "------------------"
measure "$a" | while IFS='	' read -r name n d r; do
	mark=""
	[ "$r" = INF ] && mark="  <- affords nothing on this axis"
	m=$(grep -v '^#' "$gauges" | awk -F '\t' -v k="$name" 'NF>=4 && $1==k { print $4 }')
	printf '%-26s %8s %8s %8s  %s%s\n' "$name" "$n" "$d" "$r" "$m" "$mark"
done
echo
echo "No verdict printed, by design. Name what the number would have to be for the claim you want"
echo "to make, then say whether it is."
