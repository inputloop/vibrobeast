#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- scripts/check_principles.py against a small memory + skills tree planted in a temp dir.
#
#   sh tests.sh              a clean tree reads all PASS; each planted fault raises its own guard
#   sh tests.sh --prove-red  the above, then break check_principles.py eight ways in a temp copy;
#                            exit 0 only if the real script is green AND every break goes red
#
# What check_principles.py promises (its header; SKILL.md "The two passes"): RISK guards
# memory-present, principles-present, truncation, duplication, drift, description-length each
# NOTICE their own fault; OPPORTUNITY guards skill-themes, share-plugin, value-gaps each OPPTY
# their own opening; notes in a memory/ subdir are swept too; it is read-only; it always exits 0.
# A guard is judged by its own line, so a NOTICE raised by the wrong guard does not count.
# Needs: python3.  Exit: 0 all good · 1 a case failed, or (--prove-red) a break went unnoticed · 2 setup

set -u
here=$(cd "$(dirname "$0")" && pwd)
CP=$here/scripts/check_principles.py
PY=$(command -v python3) || { echo "tests.sh: python3 not found" >&2; exit 2; }
[ -f "$CP" ] || { echo "tests.sh: missing $CP" >&2; exit 2; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/cp-tests.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT
trap 'exit 2' INT TERM

# --- the clean tree: every guard should PASS on it -----------------------------------------------
setup() {
	c=$tmp/clean; mkdir -p "$c/mem" "$c/skills/alpha" "$c/skills/beta"
	printf '# index\n- principles.md\n- garden.md\n' >"$c/mem/MEMORY.md"
	cat >"$c/mem/principles.md" <<'N'
---
name: principles
---
Decision order: universalism and egalitarianism, then the four freedoms, then the
software-freedom movement, then the broader technical community. Transparency is owed to
every person the system touches; free software is the default, never the exception.
N
	cat >"$c/mem/garden.md" <<'N'
---
name: garden
---
The garden keeps its tools small and plain so a stranger can read them, change them and pass
them along; every tool carries a test that can fail, and every test says how to run it, and
where its fixtures live.
N
	cat >"$c/skills/alpha/SKILL.md" <<'N'
---
name: alpha
description: A short description well under the load limit.
---
Alpha puts the four freedoms, software freedom, universalism, egalitarian decisions,
transparency and free software into practice, for the garden and its tools.
N
	cat >"$c/skills/beta/SKILL.md" <<'N'
---
name: beta
description: Another short description.
---
Beta keeps notes on decision order, movement, community, person, system, default, exception,
stranger, change, pass, along, carries, test, fail, says, name, index, principles, where,
fixtures, live.
N
	printf '# attested lines\nthen the four freedoms, then the\n' >"$c/attest.txt"
}
fresh() { rm -rf "$tmp/t"; cp -R "$tmp/clean" "$tmp/t"; T=$tmp/t; }
run() { "$PY" -B "$cp" --memory "$T/mem" --skills "$T/skills" --expect "$T/attest.txt" "$@"; }

# line NAME VERDICT GUARD TEXT -- the guard's own line carries VERDICT (and TEXT, if given)
line() {
	name=$1 v=$2 g=$3 text=$4
	l=$(printf '%s\n' "$out" | grep -E "^  \[$v *\] $g ")
	if [ -n "$l" ] && printf '%s' "$l" | grep -F -q -- "$text" && [ "$rc" = 0 ]; then
		pass=$((pass + 1)); echo "PASS  $name"
	else
		fail=$((fail + 1)); echo "FAIL  $name -- exit $rc; want [$v] $g ${text:+($text)}; got: $(printf '%s\n' "$out" | grep -E "\] $g " | sed 's/^ *//')"
	fi
}
ok() { if [ "$2" = 0 ]; then pass=$((pass + 1)); echo "PASS  $1"; else fail=$((fail + 1)); echo "FAIL  $1"; fi; }
snap() { (cd "$1" && find . -type f -exec cksum {} + | sort; find . | sort); }

suite() { # suite CHECK_PRINCIPLES_PATH
	cp=$1; pass=0 fail=0
	fresh; before=$(snap "$T"); out=$(run 2>&1); rc=$?
	for g in memory-present principles-present truncation duplication drift description-length \
		skill-themes share-plugin value-gaps; do line "control: $g is PASS on the clean tree" PASS "$g" ""; done
	[ "$before" = "$(snap "$T")" ]; ok "control: read-only (tree byte-identical after the run)" $?

	fresh; rm "$T/mem/MEMORY.md"; out=$(run 2>&1); rc=$?
	line "MEMORY.md missing" NOTICE memory-present "index is missing"
	fresh; : >"$T/mem/MEMORY.md"; out=$(run 2>&1); rc=$?
	line "MEMORY.md empty" NOTICE memory-present "empty"
	fresh; rm "$T/mem/principles.md"; out=$(run 2>&1); rc=$?
	line "no principles note" NOTICE principles-present "No PRINCIPLES"
	fresh; printf 'cut mid-wri' >>"$T/mem/garden.md"; out=$(run 2>&1); rc=$?
	line "note cut mid-write (no trailing newline)" NOTICE truncation "garden.md (no trailing newline)"
	fresh; printf -- '---\nname: half\nbody that never closes its frontmatter\n' >"$T/mem/half.md"; out=$(run 2>&1); rc=$?
	line "unterminated frontmatter" NOTICE truncation "half.md (unterminated frontmatter)"
	fresh; mkdir "$T/mem/memory"; printf 'split layout note cut mid-wri' >"$T/mem/memory/deep.md"; out=$(run 2>&1); rc=$?
	line "a note in the memory/ subdir is swept too" NOTICE truncation "deep.md"
	fresh; cp "$T/mem/garden.md" "$T/mem/garden-copy.md"; out=$(run 2>&1); rc=$?
	line "two notes share one body" NOTICE duplication "garden-copy.md"
	fresh; printf 'forgotten\n' >"$T/mem/principles.md"; out=$(run 2>&1); rc=$?
	line "an attested line is gone from memory" NOTICE drift "then the four freedoms"
	fresh; rm "$T/attest.txt"; out=$(run 2>&1); rc=$?
	line "--expect file missing" NOTICE drift "not found"
	fresh; long=$("$PY" -c 'print("x" * 1100)')
	printf -- '---\nname: gamma\ndescription: %s\n---\nGamma.\n' "$long" >"$T/skills/alpha/SKILL.md"; out=$(run 2>&1); rc=$?
	line "a description over 1024 chars" NOTICE description-length "alpha (1100>1024)"
	fresh; for k in 1 2 3; do printf 'The zygotes note number %s.\n' $k >"$T/mem/z$k.md"; done; out=$(run 2>&1); rc=$?
	line "a theme in 3 notes no skill covers" OPPTY skill-themes "zygotes"
	fresh; printf 'This could become a shareable plugin.\n' >>"$T/skills/beta/SKILL.md"; out=$(run 2>&1); rc=$?
	line "a skill that says it could become a plugin" OPPTY share-plugin "beta"
	fresh; printf -- '---\nname: alpha\ndescription: d\n---\nAlpha, the garden and its tools.\n' >"$T/skills/alpha/SKILL.md"
	out=$(run 2>&1); rc=$?
	line "a stated value no skill carries" OPPTY value-gaps "four freedoms"
	T=$tmp/absent; out=$("$PY" -B "$cp" --memory "$tmp/absent" 2>&1); rc=$?
	printf '%s' "$out" | grep -q 'CANNOT READ MEMORY' && [ $rc = 0 ]; ok "memory dir missing: says CANNOT READ MEMORY, exit 0" $?

	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once; @NL@ stands for a newline
	cat <<'M'
trailing-newline check off	if t and not t.endswith("\n"):	if False:
duplication check off	if sig in seen: dups.append	if False: dups.append
drift compares nothing	and ln.strip() not in hay]	and False]
memory/ subdir not swept	if sub.is_dir():	if False:
description limit off	if len(val)>limit:	if False:
plugin opening reported as PASS	return ("OPPTY","skills that self-describe	return ("PASS","skills that self-describe
guard writes into memory	    skills = Path(a.skills) if a.skills else None	    skills = Path(a.skills) if a.skills else None; (mem / ".touched").write_text("x")
exit code tracks notices	    return 0@NL@@NL@if __name__	    return n_notice@NL@@NL@if __name__
M
}
mutate() {
	"$PY" - "$@" <<'PYEOF'
import sys
old, new, src, dst = (a.replace("@NL@", "\n") for a in sys.argv[1:5])  # @NL@ = newline
t = open(src, encoding="utf-8").read()
if t.count(old) != 1:
    sys.exit("cannot plant: %d occurrences of %r" % (t.count(old), old))
open(dst, "w", encoding="utf-8").write(t.replace(old, new))
PYEOF
}

setup
case ${1:-} in
"")
	echo "== check_principles.py: clean tree PASS, each planted fault raises its own guard =="
	suite "$CP"; exit $?
	;;
--prove-red)
	echo "== controls: the real check_principles.py =="
	suite "$CP" || { echo "PROVE-RED NOT OK -- the real script is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t')
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$CP" "$tmp/mutant.py"; then
			echo "BREAK NOT PLANTED  $mname -- check_principles.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/mutant.py" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken guard"
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
