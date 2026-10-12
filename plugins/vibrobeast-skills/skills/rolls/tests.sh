#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- scripts/check_vocab_sync.py against small verify-say pages planted in a temp dir.
#
#   sh tests.sh              a page with all five tokens is CLEAN; each planted drift is caught
#   sh tests.sh --prove-red  the above, then break check_vocab_sync.py five ways in a temp copy;
#                            exit 0 only if the real script is green AND every break goes red
#
# What check_vocab_sync.py promises (its header; SKILL.md guards 3 and 4): exit 0 only when every
# one of SIGN, DETACH, NOSIG, FURNITURE, PANEL-FAULT is on verify-say's page; exit 2 naming each
# missing token; exit 3 (never a pass) when the page cannot be found; say which page it read;
# never write.  A token counts only as a whole word: SIGNED on the page is not SIGN.
# Also checked here, against this skill's own SKILL.md: every token the script requires is one
# rolls names (the other half of the coupling the script exists for).
# Needs: python3.  Exit: 0 all good · 1 a case failed, or (--prove-red) a break went unnoticed · 2 setup

set -u
here=$(cd "$(dirname "$0")" && pwd)
CV=$here/scripts/check_vocab_sync.py
PY=$(command -v python3) || { echo "tests.sh: python3 not found" >&2; exit 2; }
[ -f "$CV" ] || { echo "tests.sh: missing $CV" >&2; exit 2; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/cv-tests.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT
trap 'exit 2' INT TERM

ALL='States: `SIGN`, `DETACH`, `NOSIG`, `FURNITURE`, and PANEL-FAULT when the panel is down.'
page() { mkdir -p "$tmp/p"; rm -rf "$tmp/p/$1"; mkdir -p "$tmp/p/$1"; printf '# verify-say\n\n%s\n' "$2" >"$tmp/p/$1/SKILL.md"; }

expect() { # expect NAME RC TEXT -- CMD...
	name=$1 want=$2 text=$3; shift 4
	out=$(cd "${CWD:-$tmp}" && "$@" 2>&1); rc=$?
	if [ "$rc" = "$want" ] && printf '%s\n' "$out" | grep -F -q -- "$text"; then
		pass=$((pass + 1)); echo "PASS  $name"
	else
		fail=$((fail + 1)); echo "FAIL  $name -- exit $rc (want $want), wanted text: $text"
	fi
}
ok() { if [ "$2" = 0 ]; then pass=$((pass + 1)); echo "PASS  $1"; else fail=$((fail + 1)); echo "FAIL  $1${3:+ -- $3}"; fi; }

suite() { # suite CHECK_VOCAB_SYNC_PATH
	cv=$1; pass=0 fail=0
	run() { "$PY" -B "$cv" "$@"; }
	page clean "$ALL"; before=$(cksum <"$tmp/p/clean/SKILL.md")
	expect "control: all five tokens, CLEAN, exit 0" 0 "CLEAN — 5 of 5" -- run --verify-say "$tmp/p/clean/SKILL.md"
	[ "$before" = "$(cksum <"$tmp/p/clean/SKILL.md")" ]; ok "control: the page is not written" $?
	page one "$(printf '%s' "$ALL" | sed 's/`FURNITURE`, //')"
	expect "one token dropped is DRIFT, named" 2 "missing 1 of 5: FURNITURE" -- run --verify-say "$tmp/p/one/SKILL.md"
	page none "No state names here at all."
	expect "every token dropped is DRIFT, all named" 2 "missing 5 of 5: SIGN, DETACH, NOSIG, FURNITURE, PANEL-FAULT" -- run --verify-say "$tmp/p/none/SKILL.md"
	page renamed "$(printf '%s' "$ALL" | sed 's/`SIGN`/`SIGNED`/')"
	expect "SIGN renamed SIGNED is DRIFT (whole words only)" 2 "missing 1 of 5: SIGN" -- run --verify-say "$tmp/p/renamed/SKILL.md"
	page lower "$(printf '%s' "$ALL" | sed 's/`NOSIG`/`nosig`/')"
	expect "a token in the wrong case is DRIFT" 2 "missing 1 of 5: NOSIG" -- run --verify-say "$tmp/p/lower/SKILL.md"
	expect "explicit page not there is FAULT, exit 3" 3 "FAULT" -- run --verify-say "$tmp/p/absent/SKILL.md"
	mkdir -p "$tmp/p/garden/rolls" "$tmp/p/garden/verify-say"; cp "$tmp/p/clean/SKILL.md" "$tmp/p/garden/verify-say/"
	CWD=$tmp/p/garden/rolls expect "found beside rolls without --verify-say, says which page" 0 "checked ../verify-say/SKILL.md" -- run
	if [ -e /mnt/skills/user/verify-say/SKILL.md ]; then
		echo "SKIP  nothing to find is FAULT -- /mnt/skills/user/verify-say exists on this box"
	else
		mkdir -p "$tmp/p/lonely/a/b"
		CWD=$tmp/p/lonely/a/b expect "nothing to find is FAULT, lists what it tried" 3 "../../verify-say/SKILL.md" -- run
	fi
	# Python older than 3.10 (e.g. a Mac's system python3) cannot evaluate `str | None` at def time.
	"$PY" -B -c 'import sys, typing; sys.path.insert(0, sys.argv[1]); import check_vocab_sync as m
a = m.find_verify_say.__annotations__
sys.exit(0 if all(isinstance(v, str) for v in a.values()) else 1)' "$(dirname "$cv")" 2>/dev/null
	ok "runs on Python < 3.10 (annotations are not evaluated at definition time)" $?
	toks=$("$PY" -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import check_vocab_sync as m; print(" ".join(m.REQUIRED_TOKENS))' "$(dirname "$cv")")
	gap=""; for t in $toks; do grep -q -- "$t" "$here/SKILL.md" || gap="$gap $t"; done
	[ -n "$toks" ] && [ -z "$gap" ]; ok "every required token is one rolls' own SKILL.md names" $? "not named by rolls:$gap"

	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once
	cat <<'M'
drift exits 0	        return 2	        return 0
not-found passes	        return 3	        return 0
a token dropped from the list	"FURNITURE", 	
substring match again	if not re.search(r"(?<![A-Za-z0-9_-])" + re.escape(t) + r"(?![A-Za-z0-9_-])", text)]	if t not in text]
explicit path trusted unchecked	return p if p.is_file() else None	return p
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
	echo "== check_vocab_sync.py: CLEAN page passes, planted drift is caught =="
	suite "$CV"; exit $?
	;;
--prove-red)
	echo "== controls: the real check_vocab_sync.py =="
	suite "$CV" || { echo "PROVE-RED NOT OK -- the real script is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t'); mkdir -p "$tmp/mut"
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$CV" "$tmp/mut/check_vocab_sync.py"; then
			echo "BREAK NOT PLANTED  $mname -- check_vocab_sync.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/mut/check_vocab_sync.py" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken check"
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
