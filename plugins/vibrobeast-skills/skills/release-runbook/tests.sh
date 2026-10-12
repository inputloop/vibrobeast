#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- scripts/verify_dist.py against small dists planted in a temp dir.
#
#   sh tests.sh              one clean dist (must pass) + ten planted faults (each must fail)
#   sh tests.sh --prove-red  the above, then break verify_dist.py five ways in a temp copy;
#                            exit 0 only if the real script is green AND every break goes red
#
# What verify_dist.py promises (its header, and SKILL.md "The verifier"): every artifact of a
# version exists, each has a detached .asc, each .asc verifies AND was made by the pinned key,
# the MANIFEST lists no sed-strays, and any failure exits non-zero.  Without gpg it warns loudly.
#
# Needs: python3 and gpg.  A throwaway keyring is made under ${TMPDIR:-/tmp} and removed after;
# your own keyring is never read or written.  Without gpg the signature cases are SKIPPED and
# said so; the run then cannot count as a full pass (exit 3).
# Exit: 0 all good · 1 a case failed, or (--prove-red) a break went unnoticed · 2 setup · 3 partial

set -u
here=$(cd "$(dirname "$0")" && pwd)
VD=$here/scripts/verify_dist.py
PY=$(command -v python3) || { echo "tests.sh: python3 not found" >&2; exit 2; }
[ -f "$VD" ] || { echo "tests.sh: missing $VD" >&2; exit 2; }

tmp=$(mktemp -d "${TMPDIR:-/tmp}/vd-tests.XXXXXX") || exit 2
cleanup() {
	[ -d "$tmp/gnupg" ] && gpgconf --homedir "$tmp/gnupg" --kill gpg-agent >/dev/null 2>&1
	rm -rf "$tmp"
}
trap cleanup EXIT
trap 'exit 2' INT TERM

havegpg=0; command -v gpg >/dev/null 2>&1 && havegpg=1
V=9.9.9
P=polygram-curation-$V

# --- fixtures ---------------------------------------------------------------------------------
setup() {
	mkdir -p "$tmp/clean" "$tmp/nogpg-bin"
	printf 'tar bytes\n' >"$tmp/clean/$P.tar.gz"
	printf 'zip bytes\n' >"$tmp/clean/$P.zip"
	printf '%s  ./skills/a/SKILL.md\n' 0000000000000000000000000000000000000000000000000000000000000000 \
		>"$tmp/clean/$P.MANIFEST"
	if [ $havegpg = 1 ]; then
		mkdir -m 700 "$tmp/gnupg"
		GNUPGHOME=$tmp/gnupg; export GNUPGHOME
		for who in pin other; do
			gpg --batch --quiet --passphrase '' --pinentry-mode loopback \
				--quick-gen-key "vd-test-$who <$who@invalid>" ed25519 sign never >/dev/null 2>&1 ||
				{ echo "tests.sh: could not make a throwaway $who key" >&2; exit 2; }
		done
		PIN=$(gpg --batch --with-colons --list-keys pin@invalid 2>/dev/null | awk -F: '/^fpr/ { print $10; exit }')
		OTHER=$(gpg --batch --with-colons --list-keys other@invalid 2>/dev/null | awk -F: '/^fpr/ { print $10; exit }')
		for k in tar.gz zip MANIFEST; do sign "$PIN" "$tmp/clean/$P.$k"; done
	else
		PIN=0000000000000000000000000000000000000000; OTHER=$PIN
		for k in tar.gz zip MANIFEST; do printf 'not a signature\n' >"$tmp/clean/$P.$k.asc"; done
	fi
}
sign() { gpg --batch --yes --quiet --local-user "$1" --armor --detach-sign -o "$2.asc" "$2" 2>/dev/null ||
	{ echo "tests.sh: could not sign $2" >&2; exit 2; }; }
fresh() { rm -rf "$tmp/d"; cp -R "$tmp/clean" "$tmp/d"; }   # every case starts from the clean dist

# --- one case: expect NAME RC TEXT -- CMD...   (RC "!0" means any non-zero) --------------------
expect() {
	name=$1 want=$2 text=$3; shift 4
	out=$("$@" 2>&1); rc=$?
	case $want in '!0') [ "$rc" -ne 0 ]; okrc=$? ;; *) [ "$rc" = "$want" ]; okrc=$? ;; esac
	if [ $okrc = 0 ] && printf '%s\n' "$out" | grep -F -q -- "$text"; then
		pass=$((pass + 1)); echo "PASS  $name"
	else
		fail=$((fail + 1)); echo "FAIL  $name -- exit $rc (want $want), wanted text: $text"
	fi
}
skip() { skipped=$((skipped + 1)); echo "SKIP  $1 -- no gpg"; }

suite() { # suite VERIFY_DIST_PATH
	vd=$1; pass=0 fail=0 skipped=0
	run() { "$PY" "$vd" --fpr "$PIN" "$@"; }
	nogpg() { env PATH="$tmp/nogpg-bin" "$PY" "$vd" "$@"; }

	if [ $havegpg = 1 ]; then
		fresh; expect "control: clean dist, pinned key, passes" 0 "all checks passed" -- run --dist "$tmp/d"
		fresh; printf 'tampered\n' >>"$tmp/d/$P.tar.gz"
		expect "artifact changed after signing" 1 "signature does not verify" -- run --dist "$tmp/d"
		fresh; sign "$OTHER" "$tmp/d/$P.zip"
		expect "signed by a key that is not the pin" 1 "NOT by pinned key" -- run --dist "$tmp/d"
		fresh; printf '%s  ./skills/a/sedAb12Cd\n' 1111111111111111111111111111111111111111111111111111111111111111 \
			>>"$tmp/d/$P.MANIFEST"; sign "$PIN" "$tmp/d/$P.MANIFEST"
		expect "MANIFEST lists a sed-stray (signed fine)" 1 "sed-stray" -- run --dist "$tmp/d"
	else
		skip "control: clean dist"; skip "artifact changed"; skip "not the pin"; skip "sed-stray"
	fi
	fresh; rm "$tmp/d/$P.MANIFEST.asc"
	expect "MANIFEST unsigned (the 0.5.4 hole)" 1 "UNSIGNED: $P.MANIFEST" -- run --dist "$tmp/d"
	fresh; rm "$tmp/d/$P.zip"
	expect "an artifact is missing" 1 "missing artifact: $P.zip" -- run --dist "$tmp/d"
	fresh; cp "$tmp/d/$P.tar.gz" "$tmp/d/polygram-curation-9.9.8.tar.gz"
	expect "a second, incomplete version is also judged" 1 "missing artifact: polygram-curation-9.9.8.zip" -- run --dist "$tmp/d"
	fresh; expect "--version names a version not present" 1 "missing artifact: polygram-curation-1.2.3.tar.gz" -- run --dist "$tmp/d" --version 1.2.3
	mkdir -p "$tmp/empty"
	expect "no artifacts at all" '!0' "no polygram-curation-* artifacts found" -- run --dist "$tmp/empty"
	fresh; expect "no gpg: warns loudly, still judges coverage" 0 "WARN   gpg not found" -- nogpg --dist "$tmp/d"
	fresh; rm "$tmp/d/$P.zip.asc"
	expect "no gpg: an unsigned artifact still fails" 1 "UNSIGNED: $P.zip" -- nogpg --dist "$tmp/d"

	echo "$pass/$((pass + fail)) pass, $fail fail, $skipped skipped"
	[ $fail = 0 ] || return 1
	[ $skipped = 0 ] || return 3
	return 0
}

# --- the breaks --prove-red plants: NAME<TAB>python-literal-old<TAB>new ------------------------
mutants() {
	cat <<'M'
pin check removed	if not m or not m.group(1).endswith(fpr[-16:]):	if False:
verify result ignored	if r.returncode != 0 or not good:	if False:
missing .asc tolerated	if not os.path.isfile(asc):	if False:
sed-stray scan off	if STRAY.search(text):	if False:
gate goes quiet (exit 0 on failure)	        sys.exit(1)	        sys.exit(0)
M
}
mutate() { # mutate OLD NEW SRC DST -- exactly one occurrence, or the break cannot be planted
	"$PY" - "$@" <<'PYEOF'
import sys
old, new, src, dst = sys.argv[1:5]
t = open(src, encoding="utf-8").read()
if t.count(old) != 1:
    sys.exit("cannot plant: %d occurrences of %r" % (t.count(old), old))
open(dst, "w", encoding="utf-8").write(t.replace(old, new))
PYEOF
}

setup
case ${1:-} in
"")
	echo "== verify_dist.py: one clean dist, ten planted faults =="
	suite "$VD"; exit $?
	;;
--prove-red)
	echo "== controls: the real verify_dist.py =="
	suite "$VD"; rc=$?
	[ $rc = 0 ] || { echo "PROVE-RED NOT OK -- the real script is not green (exit $rc); a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t')
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$VD" "$tmp/mutant.py"; then
			echo "BREAK NOT PLANTED  $mname -- verify_dist.py changed shape; update mutants()"; continue
		fi
		if suite "$tmp/mutant.py" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken verifier"
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
