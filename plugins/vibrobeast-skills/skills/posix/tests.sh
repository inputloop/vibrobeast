#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- tool.py against small shell files planted in a temp dir.
#
#   sh tests.sh              a clean POSIX script reads OK; each planted smell is reported
#   sh tests.sh --prove-red  the above, then break tool.py seven ways in a temp copy;
#                            exit 0 only if the real tool is green AND every break goes red
#
# What tool.py promises (its header; SKILL.md): under #!/bin/sh it names each bashism by line;
# it does not flag bashisms in a #!/bin/bash file or inside a comment; it reports CRLF, NUL
# bytes and a missing final newline; it notes a missing shebang and a missing set -e/-u; it runs
# sh -n / bash -n and reports SYNTAX on failure; it is read-only; it ALWAYS exits 0 (advisory).
# Needs: python3 and sh.  Exit: 0 all good · 1 a case failed / a break went unnoticed · 2 setup

set -u
here=$(cd "$(dirname "$0")" && pwd)
TOOL=$here/tool.py
PY=$(command -v python3) || { echo "tests.sh: python3 not found" >&2; exit 2; }
[ -f "$TOOL" ] || { echo "tests.sh: missing $TOOL" >&2; exit 2; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/px-tests.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT
trap 'exit 2' INT TERM

setup() {
	f=$tmp/f; mkdir -p "$f"
	printf '#!/bin/sh\nset -eu\n# a comment may say [[ or source freely\nx="a # not a comment"\nprintf "%%s\\n" "$x"\n' >"$f/clean.sh"
	# one bashism per line, lines 2..13, in the order tool.py lists them
	cat >"$f/bashy.sh" <<'B'
#!/bin/sh
if [[ -n "$1" ]]; then :; fi
function f { :; }
g() { local v=1; }
arr=(a b)
x=$'tab\t'
source ./lib.sh
n=$RANDOM
y=${x//a/b}
: &> /dev/null
echo -n hi
cat <<< "$x"
(( n++ ))
set -u
B
	cp "$f/bashy.sh" "$f/bashy.bash"; sed '1s|.*|#!/bin/bash|' "$f/bashy.sh" >"$f/bashy.bash"
	printf '#!/bin/sh\r\nset -eu\r\n:\r\n' >"$f/crlf.sh"
	printf '#!/bin/sh\nset -eu\n: \000\n' >"$f/nul.sh"
	printf '#!/bin/sh\nset -eu\n:' >"$f/nonl.sh"
	printf 'set -eu\n:\n' >"$f/noshebang.sh"
	printf '#!/bin/sh\n:\n' >"$f/noset.sh"
	printf '#!/bin/sh\nset -eu\nif then fi fi\n' >"$f/syntax.sh"
}

expect() { # expect NAME FILE WANT_PRESENT[|...] [WANT_ABSENT]
	name=$1 file=$2 want=$3 absent=${4:-}
	out=$("$PY" -B "$tool" "$f/$file" 2>&1); rc=$?
	good=1; [ "$rc" = 0 ] || good=0
	old_ifs=$IFS; IFS='|'
	for w in $want; do printf '%s\n' "$out" | grep -F -q -- "$w" || { good=0; miss=$w; }; done
	IFS=$old_ifs
	if [ -n "$absent" ] && printf '%s\n' "$out" | grep -F -q -- "$absent"; then good=0; miss="(unwanted) $absent"; fi
	if [ $good = 1 ]; then pass=$((pass + 1)); echo "PASS  $name"
	else fail=$((fail + 1)); echo "FAIL  $name -- exit $rc; missing: ${miss:-exit 0}"; fi
	miss=""
}

suite() { # suite TOOL_PATH
	tool=$1; pass=0 fail=0 miss=""
	before=$(cd "$f" && cksum ./* | sort)
	expect "control: clean script is sh -n clean; a comment's [[ and source are not bashisms" clean.sh "[OK] sh -n clean" "[BASHISM]"
	expect "control: clean script has no smell" clean.sh "[OK]" "[SMELL]"
	expect "control: clean script (shebang, set -eu) draws no note" clean.sh "[OK]" "[NOTE]"
	expect "every bashism under #!/bin/sh is named by line" bashy.sh \
"line 2: [[|line 3: 'function'|line 4: 'local'|line 5: array|line 6: \$'...'|line 7: 'source'|line 8: \$RANDOM|line 9: bash parameter|line 10: &>|line 11: echo -e/-n|line 12: here-string|line 13: (( arithmetic"
	expect "the same text under #!/bin/bash is not a bashism" bashy.bash "bash -n" "[BASHISM]"
	expect "CRLF line endings are a smell" crlf.sh "[SMELL] CRLF"
	expect "NUL bytes are a smell" nul.sh "[SMELL] 1 NUL bytes"
	expect "a missing final newline is a smell" nonl.sh "[SMELL] no final newline"
	expect "no shebang is noted" noshebang.sh "[NOTE] no shebang"
	expect "no set -e/-u is noted" noset.sh "[NOTE] no set -e/-u"
	expect "a syntax error is reported" syntax.sh "[SYNTAX] sh -n"
	expect "a file that is not there: READ, still exit 0" absent.sh "[READ] cannot read"
	after=$(cd "$f" && cksum ./* | sort)
	[ "$before" = "$after" ] && { pass=$((pass + 1)); echo "PASS  read-only: every planted file byte-identical after"; } ||
		{ fail=$((fail + 1)); echo "FAIL  read-only: a planted file changed"; }
	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once; @NL@ stands for a newline
	cat <<'M'
[[ dropped from the bashism table	    (re.compile(r'(^|\s)\[\['), "[[ ... ]] test"),@NL@	
bashisms also flagged under bash	    if is_sh:@NL@        for n, raw	    if is_sh or is_bash:@NL@        for n, raw
comments no longer stripped	        elif ch == '#' and (i == 0 or line[i - 1] in ' \t;'):	        elif False:
CRLF check off	    if b'\r\n' in data:	    if False:
final-newline check off	    if data and not data.endswith(b'\n'):	    if False:
syntax failure called clean	        if r.returncode == 0:	        if True:
advisory tool exits non-zero	    return 0  # advisory, always	    return 1  # advisory, always
M
}
mutate() {
	"$PY" - "$@" <<'PYEOF'
import sys
old, new, src, dst = (a.replace("@NL@", "\n") for a in sys.argv[1:5])
t = open(src, encoding="utf-8").read()
if t.count(old) != 1:
    sys.exit("cannot plant: %d occurrences of %r" % (t.count(old), old))
open(dst, "w", encoding="utf-8").write(t.replace(old, new))
PYEOF
}

setup
case ${1:-} in
"")
	echo "== tool.py: clean script reads OK, each planted smell is reported =="
	suite "$TOOL"; exit $?
	;;
--prove-red)
	echo "== controls: the real tool.py =="
	suite "$TOOL" || { echo "PROVE-RED NOT OK -- the real tool is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t')
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$TOOL" "$tmp/mutant.py"; then
			echo "BREAK NOT PLANTED  $mname -- tool.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/mutant.py" >"$tmp/mutant.log" 2>&1; then
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
