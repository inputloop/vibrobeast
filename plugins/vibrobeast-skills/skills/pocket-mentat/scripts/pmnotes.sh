#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# pmnotes.sh --- check a Pocket Mentat notes file for form.
#
# It exists so that "I have been keeping good notes" is something you can SHOW rather than assert.
# It checks form, never content: it cannot tell you a note is true, only that it says where it came
# from and what would prove it wrong. Those two are the whole design, so those two are what a
# missing-field report is loudest about.
#
# Usage:
#   sh pmnotes.sh NOTES.md      per-note verdict
#   sh pmnotes.sh --format      the format reminder
#
# A note is a block of consecutive non-blank lines, so both shapes in the paste-in file work:
# the one-liner and the indented block.
#
# Exit: 0 every note OK or GUESS · 1 at least one note is UNSOURCED or UNFALSIFIABLE · 2 bad input.
# NO-TRIGGERS and UNNAMED-SOURCE are hygiene: reported, but they do not fail the file.
#
# POSIX sh + awk. Part of the pocket-mentat mint (2026-09-04, unblessed).

set -u

prog=${0##*/}

if [ "${1:-}" = "--format" ]; then
	cat <<'EOF'
SEAM — PIN (triggers: …) — From: … — Would-change: …

  SEAM             the thing itself; the handle you grab it by
  PIN              what it means, plus trigger words that bring it back
  From:            you | them | a source (NAME IT) | a guess
  Would-change:    the one thing that would make this note wrong
  came-from:       optional -- the note this grew out of
  leads-to:        optional -- where it points next

A note that cannot say where it came from is a guess; label it one.
A note nothing could falsify is an opinion; label it one.
EOF
	exit 0
fi

tsv=0
if [ "${1:-}" = "--tsv" ]; then tsv=1; shift; fi

case ${1:-} in
"" | -h | --help) echo "usage: $prog [--tsv] NOTES.md | $prog --format" >&2; [ -n "${1:-}" ] && exit 0 || exit 2 ;;
esac

[ -f "$1" ] || { echo "$prog: cannot read $1" >&2; exit 2; }

# --tsv: verdict <TAB> full seam, no truncation and no prose footer. The human view truncates
# long seams to stay readable, which makes it unjoinable -- so the composable form is its own
# mode rather than something a caller has to reconstruct.
awk -v TSV="$tsv" 'BEGIN { RS = ""; FS = "\n" }
{
	block = $0
	if (block ~ /^[[:space:]]*#/) next          # a comment paragraph is not a note

	# --- seam: after "SEAM:" if labelled, else the text before the first dash-separator.
	seam = ""
	if (match(block, /SEAM:[[:space:]]*[^\n]+/)) {
		seam = substr(block, RSTART + 5, RLENGTH - 5)
		sub(/[[:space:]]*[—-][—-]?[[:space:]].*$/, "", seam)
	} else {
		seam = block
		sub(/\n.*$/, "", seam)
		sub(/[[:space:]]*(—|--)[[:space:]].*$/, "", seam)
	}
	gsub(/^[[:space:]]+|[[:space:]]+$/, "", seam)
	if (seam == "") next
	# A paragraph with none of the markers is prose, not a malformed note. Only judge things
	# that are trying to be notes -- otherwise every heading in a file reads as a violation.
	if (block !~ /From:/ && block !~ /Would-change:/ && block !~ /SEAM/) next

	hasfrom  = (block ~ /From:[[:space:]]*[^[:space:]]/)
	haswould = (block ~ /Would-change:[[:space:]]*[^[:space:]]/)
	hastrig  = (block ~ /triggers:[[:space:]]*[^[:space:]]/)

	src = ""
	if (match(block, /From:[[:space:]]*[^\n|]+/)) {
		src = substr(block, RSTART + 5, RLENGTH - 5)
		# The one-line shape separates fields with an em-dash, not a pipe, so the capture above
		# runs straight on into Would-change:. Without this trim, `From: a source — Would-change:
		# …` never matches "unnamed" and the UNNAMED-SOURCE case silently reads as OK.
		sub(/[[:space:]]*(—|--|\|).*$/, "", src)
		gsub(/^[[:space:]]+|[[:space:]]+$/, "", src)
	}
	isguess = (src ~ /^a guess/)
	# "a source" with nothing after it is a citation that cites nothing.
	unnamed = (src ~ /^a source[[:space:]]*$/ || src ~ /^a source[[:space:]]*\([[:space:]]*\)/ || src ~ /^source[[:space:]]*$/)

	if (!hasfrom)       { v = "UNSOURCED";      why = "no From: -- a guess wearing the clothes of a fact"; bad++ }
	else if (!haswould) { v = "UNFALSIFIABLE";  why = "no Would-change: -- an opinion filed as a note"; bad++ }
	else if (unnamed)   { v = "UNNAMED-SOURCE"; why = "says `a source` without naming it"; warn++ }
	else if (isguess)   { v = "GUESS";          why = "labelled a guess -- valid, and the label is the point" }
	else if (!hastrig)  { v = "NO-TRIGGERS";    why = "usable, but it will not come back on its own"; warn++ }
	else                { v = "OK";             why = "seam, meaning, triggers, source and falsifier all present" }

	n++
	if (TSV + 0 == 1) { printf "%s\t%s\n", v, seam; next }
	if (length(seam) > 40) seam = substr(seam, 1, 37) "..."
	printf "%-16s %-42s %s\n", v, seam, why
}
END {
	if (TSV + 0 == 1) { if (n == 0) exit 2; exit (bad ? 1 : 0) }
	printf "\n%d note(s): %d failing, %d hygiene\n", n + 0, bad + 0, warn + 0
	if (n == 0) { print "no notes found -- nothing was checked"; exit 2 }
	if (bad) {
		print "UNSOURCED and UNFALSIFIABLE are the two that matter: without them a handoff exports"
		print "confident-sounding text rather than memory."
		exit 1
	}
	exit 0
}' "$1"
