#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests-validators.sh --- scripts/validators.py against small files planted in a temp dir.
#
#   sh tests-validators.sh              good files pass, broken files fail, the rest SKIP
#   sh tests-validators.sh --prove-red  the above, then break validators.py in a temp copy;
#                                       exit 0 only if the real module is green AND every break
#                                       that can run on this box goes red
#
# What validators.py promises (its header; SKILL.md "Verify before promote"): .py must compile,
# .html/.htm must carry </html>, .el must byte-compile; a MISSING toolchain is SKIP, never FAIL;
# an unknown extension is SKIP; and a validation pass leaves nothing behind beside the file
# (no .elc, no __pycache__ -- on the flaky mount a leftover is a fresh stale shadow).
# Needs: python3.  The .el cases run only where emacs is on PATH, and say SKIP otherwise.
# Exit: 0 all good · 1 a case failed, or (--prove-red) a break went unnoticed · 2 setup

set -u
here=$(cd "$(dirname "$0")" && pwd)
MOD=$here/scripts/validators.py
PY=$(command -v python3) || { echo "tests-validators.sh: python3 not found" >&2; exit 2; }
[ -f "$MOD" ] || { echo "tests-validators.sh: missing $MOD" >&2; exit 2; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/val-tests.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT
trap 'exit 2' INT TERM
haveemacs=0; command -v emacs >/dev/null 2>&1 && haveemacs=1

# validate MODULE_DIR FILE [PATH] -> prints "status detail"; never writes bytecode for the module
validate() {
	env PYTHONDONTWRITEBYTECODE=1 PATH="${3:-$PATH}" "$PY" -c '
import sys
sys.path.insert(0, sys.argv[1])
import validators
s, d = validators.validate(sys.argv[2])
print(s, " | ".join(d.splitlines()))' "$1" "$2"
}

expect() { # expect NAME WANT_STATUS MODULE_DIR FILE [PATH]
	name=$1 want=$2; shift 2
	got=$(validate "$@" 2>&1 | tail -1); st=${got%% *}
	if [ "$st" = "$want" ]; then pass=$((pass + 1)); echo "PASS  $name"
	else fail=$((fail + 1)); echo "FAIL  $name -- want $want, got: $got"; fi
}
nothing_left() { # nothing_left NAME DIR -- only the planted files may remain
	extra=$(cd "$2" && ls -A | grep -v -x -e 'f\..*' | tr '\n' ' ')
	if [ -z "$extra" ]; then pass=$((pass + 1)); echo "PASS  $1"
	else fail=$((fail + 1)); echo "FAIL  $1 -- left behind: $extra"; fi
}
skip() { skipped=$((skipped + 1)); echo "SKIP  $1"; }

case_dir() { rm -rf "$tmp/c"; mkdir -p "$tmp/c"; }

suite() { # suite MODULE_DIR
	m=$1; pass=0 fail=0 skipped=0
	mkdir -p "$tmp/nobin"
	case_dir; printf 'def f(x):\n    return x + 1\n' >"$tmp/c/f.py"
	expect "control: good .py is ok" ok "$m" "$tmp/c/f.py"
	nothing_left "good .py: nothing left beside it (no __pycache__)" "$tmp/c"
	case_dir; printf 'def f(x:\n    return x\n' >"$tmp/c/f.py"
	expect "broken .py fails" fail "$m" "$tmp/c/f.py"
	case_dir; printf 'def f(x):\n    return (x +\n' >"$tmp/c/f.py"
	expect "truncated .py fails" fail "$m" "$tmp/c/f.py"
	nothing_left "broken .py: nothing left beside it" "$tmp/c"
	case_dir; printf '<html><body>hi</body></html>\n' >"$tmp/c/f.html"
	expect "control: good .html is ok" ok "$m" "$tmp/c/f.html"
	case_dir; printf '<HTML><BODY>hi</BODY></HTML>\n' >"$tmp/c/f.htm"
	expect "control: .htm, upper-case tag, is ok" ok "$m" "$tmp/c/f.htm"
	case_dir; printf '<html><body>hi</bo' >"$tmp/c/f.html"
	expect "truncated .html fails" fail "$m" "$tmp/c/f.html"
	case_dir; printf 'plain\n' >"$tmp/c/f.txt"
	expect "unknown extension is skip" skip "$m" "$tmp/c/f.txt"
	case_dir; printf '(message "hi")\n' >"$tmp/c/f.el"
	expect "no emacs on PATH: .el is skip, not fail" skip "$m" "$tmp/c/f.el" "$tmp/nobin"
	case_dir; printf 'def f(:\n' >"$tmp/c/f.py"
	expect "no python3 on PATH: .py is skip, not fail" skip "$m" "$tmp/c/f.py" "$tmp/nobin"
	if [ $haveemacs = 1 ]; then
		case_dir; printf ';;; f.el --- t  -*- lexical-binding: t -*-\n(defun f-x () 1)\n' >"$tmp/c/f.el"
		expect "control: good .el is ok" ok "$m" "$tmp/c/f.el"
		nothing_left "good .el: no .elc left beside it" "$tmp/c"
		case_dir; printf '(defun f-x () (1\n' >"$tmp/c/f.el"
		expect "broken .el fails" fail "$m" "$tmp/c/f.el"
	else
		skip "good .el / broken .el / no .elc left -- emacs not on PATH"
	fi
	echo "$pass/$((pass + fail)) pass, $fail fail, $skipped skipped"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>NEEDS<TAB>old<TAB>new  (NEEDS: - or emacs)
	cat <<'M'
.html closing-tag check off	-	if "</html>" not in text.lower():	if False:
.py compile result ignored	-	return ("ok", "py_compile clean") if code == 0 else ("fail", out[-400:])	return ("ok", "py_compile clean")
missing toolchain becomes FAIL	-	return "skip", "emacs not found"	return "fail", "emacs not found"
unknown extension passes	-	return "skip", "no validator for {}"	return "ok", "no validator for {}"
__pycache__ written beside the file	-	PYTHONPYCACHEPREFIX=cache	PYTHONPYCACHEPREFIX_OFF=cache
.elc left behind	emacs	os.remove(elc)	pass
M
}
mutate() {
	"$PY" - "$@" <<'PYEOF'
import sys
old, new, src, dst = sys.argv[1:5]
t = open(src, encoding="utf-8").read()
if t.count(old) != 1:
    sys.exit("cannot plant: %d occurrences of %r" % (t.count(old), old))
open(dst, "w", encoding="utf-8").write(t.replace(old, new))
PYEOF
}

case ${1:-} in
"")
	echo "== validators.py: good files pass, broken files fail, missing tools skip =="
	suite "$here/scripts"; exit $?
	;;
--prove-red)
	echo "== controls: the real validators.py =="
	suite "$here/scripts" || { echo "PROVE-RED NOT OK -- the real module is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 notrun=0 tab=$(printf '\t')
	mkdir -p "$tmp/mut"
	while IFS=$tab read -r mname needs old new; do
		if [ "$needs" = emacs ] && [ $haveemacs = 0 ]; then
			notrun=$((notrun + 1)); echo "NOT RUN  $mname -- needs emacs"; continue
		fi
		n=$((n + 1))
		if ! mutate "$old" "$new" "$MOD" "$tmp/mut/validators.py"; then
			echo "BREAK NOT PLANTED  $mname -- validators.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/mut" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken module"
		else
			caught=$((caught + 1)); echo "CAUGHT  $mname -- $(grep '^FAIL' "$tmp/mutant.log" | head -1)"
		fi
	done <<M2
$(mutants)
M2
	echo
	if [ $caught = $n ] && [ $n -gt 0 ]; then
		echo "PROVE-RED OK -- controls green, $caught/$n planted breaks caught ($notrun not runnable here)"; exit 0
	fi
	echo "PROVE-RED NOT OK -- $caught/$n planted breaks caught"; exit 1
	;;
*) echo "usage: sh tests-validators.sh [--prove-red]" >&2; exit 2 ;;
esac
