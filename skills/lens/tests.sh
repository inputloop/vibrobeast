#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# tests.sh --- scripts/ferry_core.py (the spine lens.py stands on) against files in a temp dir,
# plus the kit's own selftests, so they are one command and the kit (bin/gd1ck) finds them.
#
#   sh tests.sh              ferry_core keeps its docstring's promises; lens.py and doubled_nine.py
#                            pass `selftest` and `selftest --prove-red`
#   sh tests.sh --prove-red  the above, then break ferry_core.py seven ways in a temp copy of
#                            scripts/; exit 0 only if the real kit is green AND every break goes red
#
# What ferry_core.py promises (its docstring and each function's): sha256 is the identity, for a
# file of any size; a receipt is TS<TAB>op<TAB>status<TAB>k=v...<TAB>tail with TS in UTC, second
# precision, Z-suffixed, the fields in the order given, tail "landed" unless told otherwise;
# receipts are appended, never overwritten (nothing here deletes; callers append), and the log's
# folder is made if absent; a missing TSV reads as ([], []); a leading '# ' on the header line is
# tolerated on read and written on write, so a manifest round-trips; upsert replaces by key and
# says 'replace', or appends and says 'insert', so a re-run of unchanged bytes never grows the
# ledger; run as a script with a FILE it prints "sha256 <hex> FILE".
# Why this exists: lens.py's own selftest leaves three of these promises unwatched (a ferry_core
# that always inserts, hashes only the first 64 KiB, or writes the header without '# ' still
# passes it), so the spine gets its own check.
# Written in sh on purpose: ferry_core is Python, so the harness is in a second language; each
# probe is a one-line call into the module.  Needs: python3 (sha256sum, if present, is a second
# witness for the hash).  Exit: 0 all good · 1 a case failed, or (--prove-red) a break went
# unnoticed · 77 python3 missing (said)

set -u
here=$(cd "$(dirname "$0")" && pwd)
PY=$(command -v python3) || { echo "tests.sh: python3 not found; the lens kit is Python, nothing can be checked" >&2; exit 77; }
[ -f "$here/scripts/ferry_core.py" ] || { echo "tests.sh: missing $here/scripts/ferry_core.py" >&2; exit 1; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lens-tests.XXXXXX") || exit 1
trap 'rm -rf "$tmp"' EXIT
trap 'exit 1' INT TERM

ok() { if [ "$2" = 0 ]; then pass=$((pass + 1)); echo "PASS  $1"; else fail=$((fail + 1)); echo "FAIL  $1${3:+ -- $3}"; fi; }

suite() { # suite SCRIPTS_DIR
	s=$1; pass=0 fail=0 w=$tmp/w; rm -rf "$w"; mkdir -p "$w"
	fc() { (cd "$w" && "$PY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import ferry_core as fc; $1" "$s" "$w" 2>&1); }

	printf 'hello, garden\n' >"$w/small"
	"$PY" -c 'import sys; open(sys.argv[1], "wb").write(bytes(range(256)) * 1025)' "$w/big"   # 262400 bytes, > 4 chunks
	for f in small big; do
		want=$("$PY" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$w/$f")
		got=$(fc "print(fc.sha256_file(sys.argv[2] + '/$f'))")
		[ -n "$want" ] && [ "$got" = "$want" ]; ok "sha256_file is the sha256 of the whole file ($f)" $? "got $got"
		if command -v sha256sum >/dev/null 2>&1; then
			[ "$got" = "$(sha256sum "$w/$f" | cut -d' ' -f1)" ]; ok "...and sha256sum agrees ($f)" $?
		else
			echo "SKIPPED  sha256sum as a second witness ($f) -- sha256sum not on PATH"
		fi
	done
	[ "$(fc "print(fc.sha256_bytes(b'hello, garden\n'))")" = "$(fc "print(fc.sha256_file(sys.argv[2] + '/small'))")" ]
	ok "sha256_bytes and sha256_file agree on the same bytes" $?
	line=$(fc "print(fc.receipt_line('ferry', 'OK', {'src': 'a', 'dest': 'b', 'sha': 'f00'}, ts='2026-09-28T01:02:03Z'))")
	[ "$line" = "$(printf '2026-09-28T01:02:03Z\tferry\tOK\tsrc=a\tdest=b\tsha=f00\tlanded')" ]
	ok "a receipt is TS op status k=v... tail, tab-joined, fields in order, tail 'landed'" $? "$line"
	line=$(fc "print(fc.receipt_line('ferry', 'OK', tail=''))")
	printf '%s\n' "$line" | grep -q "$(printf '\tferry\tOK$')"; ok "an empty tail is left off" $? "$line"
	ts=$(fc "print(fc.now_iso())")
	printf '%s\n' "$ts" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$'; ok "now_iso is UTC, second precision, Z-suffixed" $? "$ts"
	fc "fc.append_receipt(sys.argv[2] + '/new/dir/receipts.log', 'a', 'OK', ts='T1'); fc.append_receipt(sys.argv[2] + '/new/dir/receipts.log', 'b', 'OK', ts='T2')" >/dev/null
	[ "$(cut -f1,2 "$w/new/dir/receipts.log" 2>/dev/null | tr '\t\n' ': ')" = "T1:a T2:b " ]
	ok "append_receipt makes the folder and appends: two calls, two lines, in order" $? "$(cat "$w/new/dir/receipts.log" 2>&1)"
	[ "$(fc "print(fc.read_tsv(sys.argv[2] + '/absent.tsv'))")" = "([], [])" ]; ok "a missing TSV reads as ([], [])" $?
	printf '# sha\tpath\tnote\nabc\tx.md\tfirst\ndef\ty.md\n' >"$w/m.tsv"
	got=$(fc "h, r = fc.read_tsv(sys.argv[2] + '/m.tsv'); print(h, r)")
	[ "$got" = "['sha', 'path', 'note'] [{'sha': 'abc', 'path': 'x.md', 'note': 'first'}, {'sha': 'def', 'path': 'y.md', 'note': ''}]" ]
	ok "read_tsv tolerates '# ' on the header and pads a short row" $? "$got"
	fc "fc.write_tsv(sys.argv[2] + '/out/w.tsv', ['sha', 'path'], [{'sha': 'abc', 'path': 'x.md'}])" >/dev/null
	[ "$(head -1 "$w/out/w.tsv" 2>/dev/null)" = "$(printf '# sha\tpath')" ]; ok "write_tsv writes the header with a leading '# '" $? "$(head -1 "$w/out/w.tsv" 2>&1)"
	got=$(fc "p = sys.argv[2] + '/out/w.tsv'; h, r = fc.read_tsv(p); fc.write_tsv(p, h, r); print(fc.read_tsv(p) == (h, r), h)")
	[ "$got" = "True ['sha', 'path']" ]; ok "a manifest written and read back round-trips" $? "$got"
	got=$(fc "rows = []; a = fc.upsert(rows, 'sha', {'sha': 'abc', 'p': '1'}); b = fc.upsert(rows, 'sha', {'sha': 'abc', 'p': '2'}); c = fc.upsert(rows, 'sha', {'sha': 'def', 'p': '3'}); print(a, b, c, rows)")
	[ "$got" = "insert replace insert [{'sha': 'abc', 'p': '2'}, {'sha': 'def', 'p': '3'}]" ]
	ok "upsert: insert, then replace by key in place (the ledger does not grow), then insert" $? "$got"
	got=$(cd "$w" && "$PY" -B "$s/ferry_core.py" "$w/small" 2>&1 | head -1)
	[ "$got" = "sha256 $(fc "print(fc.sha256_file(sys.argv[2] + '/small'))") $w/small" ]; ok "run with a FILE it prints 'sha256 <hex> FILE'" $? "$got"
	# the kit's own selftests, on the same scripts/ (a broken spine may also turn these red)
	(cd "$w" && "$PY" -B "$s/lens.py" selftest) >"$tmp/st.log" 2>&1; ok "lens.py selftest" $? "$(tail -1 "$tmp/st.log")"
	(cd "$w" && "$PY" -B "$s/lens.py" selftest --prove-red) >"$tmp/st.log" 2>&1; ok "lens.py selftest --prove-red" $? "$(tail -1 "$tmp/st.log")"
	(cd "$w" && "$PY" -B "$s/doubled_nine.py" selftest) >"$tmp/st.log" 2>&1; ok "doubled_nine.py selftest" $? "$(tail -1 "$tmp/st.log")"
	(cd "$w" && "$PY" -B "$s/doubled_nine.py" selftest --prove-red) >"$tmp/st.log" 2>&1; ok "doubled_nine.py selftest --prove-red" $? "$(tail -1 "$tmp/st.log")"
	echo "$pass/$((pass + fail)) pass, $fail fail"
	[ $fail = 0 ]
}

mutants() { # NAME<TAB>old<TAB>new -- old must occur exactly once; \n in old/new is a newline
	cat <<'M'
upsert always inserts	            rows[i] = record\n            return "replace"	            pass
receipts overwrite the log	open(logpath, "a"	open(logpath, "w"
the '# ' header is not tolerated on read	c.lstrip("# ").strip() if i == 0 else c	c
the tail is dropped	    if tail:\n        parts.append(tail)	    pass
only the first 64 KiB is hashed	        for chunk in iter(lambda: fh.read(CHUNK), b""):\n            h.update(chunk)	        h.update(fh.read(CHUNK))
the header is written without '# '	out_header = ["# " + out_header[0]] + out_header[1:]	pass
the timestamp is local and unmarked	strftime("%Y-%m-%dT%H:%M:%SZ")	strftime("%Y-%m-%d %H:%M:%S")
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
	echo "== ferry_core.py and the lens kit keep their promises =="
	suite "$here/scripts"; exit $?
	;;
--prove-red)
	echo "== controls: the real scripts/ =="
	suite "$here/scripts" || { echo "PROVE-RED NOT OK -- the real kit is not green; a red here proves nothing"; exit 1; }
	echo; echo "== planted breaks in ferry_core.py: each must turn the suite red =="
	n=0 caught=0 tab=$(printf '\t'); m=$tmp/mut; mkdir -p "$m"; cp "$here"/scripts/*.py "$m/"
	while IFS=$tab read -r mname old new; do
		n=$((n + 1))
		if ! mutate "$old" "$new" "$here/scripts/ferry_core.py" "$m/ferry_core.py"; then
			echo "BREAK NOT PLANTED  $mname -- ferry_core.py changed shape; update mutants()"; continue
		fi
		if suite "$m" >"$tmp/mutant.log" 2>&1; then
			echo "MISSED  $mname -- the suite stayed green on a broken spine"
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
