#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- tool.py against pairs whose WCAG 2.1 ratios are known, and pair files in a temp dir.
#
#   sh tests.sh              the three falsifiers in SKILL.md hold, and audit reads what it is given
#   sh tests.sh --prove-red  the above, then break tool.py seven ways in a temp copy; exit 0 only
#                            if the real tool is green AND every break goes red
#
# What tool.py promises (its docstring; SKILL.md "How this skill can fail"): white on black is
# 21.00:1; #777777 on #ffffff is 4.48:1 and fails AA normal text (passes AA large, 3.0); swapping
# foreground and background never changes the ratio; `suggest BG --level AA` returns a colour that
# clears 4.5:1 on BG, and says so and exits 1 when neither black nor white can; a 3- or 6-digit hex
# is a colour and anything else is an error (exit 2); `audit` reads "FG BG" pairs from a file or
# stdin, a comment is '#' + whitespace while '#rrggbb' is data, and it exits 1 on any AA-FAIL or
# unreadable line; `selftest` passes.
# Written in sh on purpose: the tool is Python, so the check is in a second language.
# Needs: python3.  Exit: 0 all good · 1 a case failed, or (--prove-red) a break went unnoticed ·
# 77 python3 missing (said)

set -u
here=$(cd "$(dirname "$0")" && pwd)
TOOL=$here/tool.py
PY=$(command -v python3) || { echo "tests.sh: python3 not found; tool.py is Python, nothing can be checked" >&2; exit 77; }
[ -f "$TOOL" ] || { echo "tests.sh: missing $TOOL" >&2; exit 1; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/ct-tests.XXXXXX") || exit 1
trap 'rm -rf "$tmp"' EXIT
trap 'exit 1' INT TERM

ok() { if [ "$2" = 0 ]; then pass=$((pass + 1)); echo "PASS  $1"; else fail=$((fail + 1)); echo "FAIL  $1${3:+ -- $3}"; fi; }
ratio() { sed -n 's/.*contrast ratio \([0-9.]*\):1.*/\1/p'; }

suite() { # suite TOOL_PATH
	t=$1; pass=0 fail=0
	ct() { "$PY" -B "$t" "$@" 2>&1; }
	out=$(ct contrast "#ffffff" "#000000"); rc=$?
	[ $rc = 0 ] && [ "$(printf '%s\n' "$out" | ratio)" = 21.00 ]; ok "white on black is 21.00:1, exit 0" $? "exit $rc: $out"
	out=$(ct contrast "#777777" "#ffffff")
	[ "$(printf '%s\n' "$out" | ratio)" = 4.48 ] && printf '%s\n' "$out" | grep -q '\[FAIL\] AA normal' && printf '%s\n' "$out" | grep -q '\[PASS\] AA large'
	ok "#777777 on #ffffff is 4.48:1: fails AA normal, passes AA large" $? "$(printf '%s' "$out" | tr '\n' ' ')"
	a=$(ct contrast "#1e2a78" "#f0c808" | ratio); b=$(ct contrast "#f0c808" "#1e2a78" | ratio)
	[ -n "$a" ] && [ "$a" = "$b" ]; ok "swapping foreground and background keeps the ratio" $? "$a vs $b"
	[ "$(ct contrast "#fff" "#000" | ratio)" = 21.00 ]; ok "a 3-digit hex is the same colour as its 6-digit form" $?
	out=$(ct contrast "#12345" "#ffffff"); rc=$?
	[ $rc = 2 ] && printf '%s\n' "$out" | grep -q 'error: not a 3- or 6-digit hex'; ok "a bad hex is an error, exit 2" $? "exit $rc"
	for bg in "#1e2a78" "#f0c808" "#808080" "#ffffff"; do
		out=$(ct suggest "$bg" --level AA); rc=$?
		pick=$(printf '%s\n' "$out" | sed -n 's/.*use \(#[0-9a-f]\{6\}\) .*/\1/p')
		r=$(ct contrast "$pick" "$bg" | ratio)
		[ $rc = 0 ] && [ -n "$pick" ] && "$PY" -c "import sys; sys.exit(0 if float(sys.argv[1]) >= 4.5 else 1)" "${r:-0}"
		ok "suggest $bg --level AA: the colour it names clears 4.5:1 when fed back" $? "exit $rc, $pick, $r"
	done
	out=$(ct suggest "#777777" --level AAA); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'no pure black/white reaches AAA'; ok "suggest when nothing can clear the level: said, exit 1" $? "exit $rc"
	printf '# the palette\n#000000 #ffffff\n\n#ffffff #1e2a78\n#\n' >"$tmp/good.txt"
	out=$(ct audit "$tmp/good.txt"); rc=$?
	[ $rc = 0 ] && [ "$(printf '%s\n' "$out" | grep -c 'AA-pass')" = 2 ]; ok "audit: comments skipped, both '#rrggbb' pairs read, all pass, exit 0" $? "exit $rc: $out"
	printf '# the palette\n#000000 #ffffff\n#777777 #ffffff\n' >"$tmp/bad.txt"
	out=$(ct audit "$tmp/bad.txt"); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q '#777777 on #ffffff:  4.48:1  AA-FAIL'; ok "audit: a failing pair is AA-FAIL, exit 1" $? "exit $rc: $out"
	out=$(printf '#777777 #ffffff\n' | "$PY" -B "$t" audit 2>&1); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q 'AA-FAIL'; ok "audit reads stdin too" $? "exit $rc"
	out=$(printf '#000000\n#000000 #fffffg\n' | "$PY" -B "$t" audit 2>&1); rc=$?
	[ $rc = 1 ] && printf '%s\n' "$out" | grep -q "line 1: expected 'FG BG'" && printf '%s\n' "$out" | grep -q 'line 2: not a 3- or 6-digit hex'
	ok "audit: an unreadable line is named by number and fails the audit" $? "exit $rc: $out"
	out=$(printf '# only comments\n\n' | "$PY" -B "$t" audit 2>&1); rc=$?
	[ $rc = 2 ] && printf '%s\n' "$out" | grep -q 'NOT CHECKED: no .FG BG. pairs were read'; ok "audit that reads no pairs is NOT CHECKED, exit 2 (from Bryant's 1.1)" $? "exit $rc: $out"
	out=$(ct audit "$tmp/good.txt"); printf '%s\n' "$out" | grep -q 'audit: 2 pair(s) read, 0 failed'; ok "audit says how many pairs it read" $? "$out"
	ct selftest >/dev/null; ok "selftest passes" $?
	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once; \n in old/new is a newline
	cat <<'M'
the AA normal floor moved to 4.4	"AA":  {"normal": 4.5	"AA":  {"normal": 4.4
the sRGB curve exponent is wrong	** 2.4	** 2.2
fg/bg order changes the ratio	hi, lo = max(l1, l2), min(l1, l2)	hi, lo = l1, l2
every '#' line is a comment again	return line == "#" or line[:1] == "#" and line[1:2].isspace()	return line.startswith("#")
an AA-FAIL does not fail the audit	            if not aa:\n                failures += 1	            if not aa:\n                pass
suggest picks the weaker colour	if r >= target and (best is None or r > best[1]):	if best is None or r < best[1]:
3-digit hex is not expanded	    if len(h) == 3:\n        h = "".join(c * 2 for c in h)	    if False:\n        pass
an empty audit passes again	    if pairs == 0 and not failures:	    if False:
M
}
mutate() {
	"$PY" - "$@" <<'PYEOF'
import sys
old, new = (a.replace("\\n", "\n") for a in sys.argv[1:3])
src, dst = sys.argv[3:5]
t = open(src, encoding="utf-8").read()
if t.count(old) != 1:
    sys.exit("cannot plant: %d occurrences of %r" % (t.count(old), old))
open(dst, "w", encoding="utf-8").write(t.replace(old, new))
PYEOF
}

case ${1:-} in
"")
	echo "== tool.py: the WCAG math and the audit keep their promises =="
	suite "$TOOL"; exit $?
	;;
--prove-red)
	echo "== controls: the real tool.py =="
	suite "$TOOL" || { echo "PROVE-RED NOT OK -- the real tool is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t')
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$TOOL" "$tmp/tool.py"; then
			echo "BREAK NOT PLANTED  $mname -- tool.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/tool.py" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken tool"
		else
			caught=$((caught + 1)); echo "CAUGHT  $mname -- $(grep '^FAIL' "$tmp/mutant.log" | head -1)"
		fi
	done <<M2
$(mutants)
M2
	echo
	if [ $caught = $n ] && [ $n -gt 0 ]; then
		echo "PROVE-RED OK -- controls green, $caught/$n planted breaks caught"; exit 0
	fi
	echo "PROVE-RED NOT OK -- $caught/$n planted breaks caught"; exit 1
	;;
*) echo "usage: sh tests.sh [--prove-red]" >&2; exit 2 ;;
esac
