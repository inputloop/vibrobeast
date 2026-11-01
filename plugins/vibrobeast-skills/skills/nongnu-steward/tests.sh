#!/bin/sh
# tests.sh -- the nongnu-steward suite: the three scripts go red on demand, the skill tends its own
# tree, the manifest is well-formed and its snapshots match their hashes, every citation in the model
# resolves to a manifest row, the dynaloader serves the skill.  Run from anywhere.
# tier: smoke
# usage: sh tests.sh | --prove-red
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of nongnu-steward.  It is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.  Authored by Mentat
# (for Corwin).
set -u
LC_ALL=C; export LC_ALL
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
seat=$(CDPATH= cd -- "$here/../.." && pwd)
S=$here/scripts
t=$(mktemp -d 2>/dev/null) || { t=${TMPDIR:-/tmp}/ns-tests.$$; mkdir -p "$t"; }
trap 'rm -rf "$t"' EXIT INT TERM
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "ok   $1"; }
bad() { fail=$((fail+1)); echo "FAIL $1 -- $2"; }
has() { if grep -q -e "$2" "$3"; then ok "$1"; else bad "$1" "no /$2/ in: $(head -3 "$3" | tr '\n' '|')"; fi; }
unset NONGNU_STEWARD_PREFS; export MENTCACHED_PREFS=/dev/null   # no seat ledger leaks into the fixtures (4a names its own)

# 1. the description loads: <= 1024 characters after assembling the folded block
lint=$seat/skills/skill-sign/scripts/skill-lint.sh
if [ -f "$lint" ]; then sh "$lint" -q "$here" > "$t/o" 2>&1 && ok "skill-lint: description within 1024 chars, name matches" || bad "skill-lint" "$(cat "$t/o")"
else n=$(awk '/^description:/{f=1;next} f&&/^[^ ]/{exit} f{print}' "$here/SKILL.md" | tr '\n' ' ' | wc -m); [ "$n" -le 1024 ] && ok "description $n chars (no skill-lint here)" || bad "description" "$n chars"; fi

# 1b. an option that needs a value, given none, is a usage error (exit 2), not an unbound-variable crash
#     (Corwin's msys2 transcript, 2026-09-23: `ns1hd --suggest` -> "line 46: $2: unbound variable")
for c in "ns1hd --suggest" "ns1hd --root" "ns2ld --compat" "ns2cn --diff" "ns2cn --mint" "ns1op --root"; do
  sh "$S/${c%% *}" ${c#* } > "$t/o" 2>&1; rc=$?
  [ $rc -eq 2 ] && grep -q 'needs a value' "$t/o" && ok "$c (no value) -> usage, exit 2" || bad "$c (no value)" "rc=$rc: $(head -1 "$t/o")"
done

# 2. each script proves red
for s in ns1hd ns2hw ns2ld ns2cn; do sh "$S/$s" --prove-red > "$t/o" 2>&1 && ok "$s --prove-red" || bad "$s --prove-red" "$(tail -3 "$t/o")"; done

# 3. the steward tends its own tree
sh "$S/ns1hd" --root "$here" > "$t/o" 2>&1; rc=$?
[ $rc -eq 0 ] && ok "ns1hd on the skill folder: no findings" || bad "self-audit" "rc=$rc $(grep -Ev '^(OK|README-COVERS)' "$t/o" | head -3 | tr '\n' '|')"
has "COPYING ships (GPLv3 text)" 'GNU GENERAL PUBLIC LICENSE' "$here/COPYING"
grep -c 'Version 3, 29 June 2007' "$here/COPYING" | grep -q '^1$' && ok "COPYING is the v3 text" || bad "COPYING" "not the v3 text"

# 4. preferences change the audit: a project dotfile lowers the threshold
mkdir -p "$t/p"; printf 'a\nb\nc\nd\ne\n' > "$t/p/five.txt"; printf 'Copyright (C) 2026 X\n' > "$t/p/COPYING"
sh "$S/ns1hd" --root "$t/p" --tsv > "$t/o" 2>&1; has "5-line file is trivial by default" '^OK	five.txt	5	trivial' "$t/o"
printf 'steward.threshold 3\n' > "$t/p/.nongnu-steward"
sh "$S/ns1hd" --root "$t/p" --tsv > "$t/o" 2>&1; has ".nongnu-steward threshold 3 makes it nontrivial" '^NO-NOTICES	five.txt	5' "$t/o"
printf 'steward.threshold 9\n' > "$t/np"; NONGNU_STEWARD_PREFS=$t/np sh "$S/ns1hd" --root "$t/p" --tsv > "$t/o" 2>&1
has "\$NONGNU_STEWARD_PREFS overrides the project file" '^OK	five.txt	5	trivial' "$t/o"
# 4a. the mentcached ledger is the floor: honoured with no dotfile, beaten by any dotfile
mkdir -p "$t/q"; printf 'a\nb\nc\nd\ne\n' > "$t/q/five.txt"; printf 'Copyright (C) 2026 X\n' > "$t/q/COPYING"
printf 'ts\tkey\tvalue\tby\twhy\n1\tsteward.threshold\t3\tt\tseat\n' > "$t/ledger.tsv"
MENTCACHED_PREFS=$t/ledger.tsv sh "$S/ns1hd" --root "$t/q" --tsv > "$t/o" 2>&1; has "ledger row lowers the threshold with no dotfile" '^NO-NOTICES	five.txt	5' "$t/o"
printf 'steward.threshold 9\n' > "$t/q/.nongnu-steward"
MENTCACHED_PREFS=$t/ledger.tsv sh "$S/ns1hd" --root "$t/q" --tsv > "$t/o" 2>&1; has "a dotfile beats the ledger" '^OK	five.txt	5	trivial' "$t/o"

# 4b. the open: one line per audit, findings as rows, canon bounded, off-switch honoured
printf 'a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\n' > "$t/p/twelve.txt"; rm -f "$t/p/.nongnu-steward"
sh "$S/ns1op" --root "$t/p" --no-canon > "$t/o" 2>&1; rc=$?
[ $rc -eq 1 ] && ok "ns1op exits 1 on findings" || bad "ns1op rc" "$rc: $(cat "$t/o")"
has "ns1op: headers line with its command" '^steward: headers  1 finding(s)   (sh scripts/ns1hd --quiet --root' "$t/o"
has "ns1op: deps line says how to start a ledger" '^steward: deps     no LICENSE-DEPS.tsv yet' "$t/o"
has "ns1op: canon line honours --no-canon" '^steward: canon    not checked (--no-canon)' "$t/o"
has "ns1op: the finding row is printed" '^NO-NOTICES	twelve.txt	12' "$t/o"
printf 'steward.auto off\n' > "$t/p/.nongnu-steward"; sh "$S/ns1op" --root "$t/p" > "$t/o" 2>&1; rc=$?
[ $rc -eq 0 ] && has "ns1op: steward.auto off -> one line, exit 0" '^steward: off (steward.auto)' "$t/o" || bad "ns1op off" "rc=$rc"
rm -f "$t/p/.nongnu-steward"
sh "$S/ns1op" --root "$t/p" > "$t/o" 2>&1; has "ns1op: without --force-canon the canon line only reports pins and the command (no network)" '^steward: canon    [0-9]* rows pinned, oldest 20.*sh scripts/ns2cn --check' "$t/o"

# 5. the manifest: shape, hashes, stamps, snapshots
M=$here/references/canon.tsv
head -1 "$M" | awk -F'\t' '{exit NF==13?0:1}' && ok "canon.tsv header has 13 columns" || bad "canon.tsv header" "$(head -1 "$M")"
awk -F'\t' 'NR>1 && NF!=13 {print NR": "NF" cols"; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every manifest row has 13 columns ($(($(wc -l < "$M")-1)) rows)" || bad "row shape" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && ($6=="200" || $6=="ok" || $6=="pinned-no-body") && ($7 !~ /^[0-9a-f]{64}$/ || $8 !~ /^[0-9a-f]{64}$/) {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every fetched row carries two 64-hex shas" || bad "shas" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && $4=="git" && $6=="ok" && ($10 !~ /^[0-9a-f]{40}$/ || $11 !~ /^[0-9a-f]{40}$/) {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every fetched git row carries a commit id and a blob id" || bad "git ids" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && $4=="git" && $6=="pinned-no-body" && ($10 !~ /^[0-9a-f]{40}$/ || $11 != "-" || $12 != "-") {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every commit-level pin carries a commit id and no blob/body" || bad "pin-only ids" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && $4=="curl" {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "no row scrapes a per-request generated page (no FETCH=curl)" || bad "curl rows" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && $9 !~ /^20[0-9][0-9]-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z$/ {print $1": "$9; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every row carries an ISO-8601 Z clock stamp" || bad "stamps" "$(cat "$t/o")"
awk -F'\t' 'NR>1 && ($4=="browser" || $4=="inquire") && $6!=$4"-only" {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "browser/inquire rows are marked *-only, never fetched" || bad "browser/inquire rows" "$(cat "$t/o")"
snapbad=0; for slug in $(awk -F'\t' 'NR>1 && $5=="yes" && $6!="pinned-no-body" {print $1}' "$M"); do
  f=$here/references/canon/$slug.txt; want=$(awk -F'\t' -v s="$slug" '$1==s {print $12}' "$M")
  [ -f "$f" ] || { snapbad=$((snapbad+1)); echo "missing $f" >> "$t/snap"; continue; }
  got=$(sha256sum "$f" 2>/dev/null | cut -c1-64); [ "$got" = "$want" ] || { snapbad=$((snapbad+1)); echo "$slug: $got != $want" >> "$t/snap"; }
done
[ $snapbad -eq 0 ] && ok "every SNAP=yes snapshot exists and matches its manifest sha ($(awk -F'\t' 'NR>1 && $5=="yes" && $6!="pinned-no-body"' "$M" | wc -l | tr -d ' ') rows; commit-level pins excepted)" || bad "snapshots" "$(head -3 "$t/snap" | tr '\n' '|')"
extra=$(ls "$here/references/canon"/*.txt | while read -r f; do b=$(basename "$f" .txt); awk -F'\t' -v s="$b" '$1==s && $5=="yes"' "$M" | grep -q . || echo "$b"; done)
[ -z "$extra" ] && ok "no snapshot without a SNAP=yes row" || bad "orphan snapshots" "$extra"
has "the snapshot README covers the directory" '^covers: \*' "$here/references/canon/README"
awk -F'\t' 'NR>1 && ($6=="200" || $6=="ok") && $5!="no" && $12 !~ /^[0-9a-f]{64}$/ {print $1; bad=1} END{exit bad?1:0}' "$M" > "$t/o" && ok "every fetched yes/sha row carries a body-text sha" || bad "body shas" "$(cat "$t/o")"
[ -f "$here/references/INQUIRE.md" ] && for s in $(awk -F'\t' 'NR>1 && ($4=="browser" || $4=="inquire") {print $1}' "$M"); do grep -q "$s" "$here/references/INQUIRE.md" || echo "$s" >> "$t/noinq"; done
[ ! -s "$t/noinq" ] && ok "every browser/inquire row is on INQUIRE.md" || bad "INQUIRE" "$(cat "$t/noinq" | tr '\n' ' ')"

# 6. every citation in the model resolves to a manifest row; every E-rule the checklist names exists
grep -o '\[\(SV\|GNU\|FLAG\):[a-z0-9-]*\]' "$here/references/MODEL-steward.md" | sed 's/.*://; s/\]//' | sort -u > "$t/tags"
: > "$t/dangling"; while read -r slug; do awk -F'\t' -v s="$slug" '$1==s' "$M" | grep -q . || echo "$slug" >> "$t/dangling"; done < "$t/tags"
[ ! -s "$t/dangling" ] && ok "all $(wc -l < "$t/tags" | tr -d ' ') distinct citations in MODEL resolve to canon.tsv rows" || bad "dangling citations" "$(tr '\n' ' ' < "$t/dangling")"
: > "$t/noE"; for e in $(grep -o 'E[0-9][0-9]*' "$here/references/checklist.md" | sort -u); do grep -q "^\*\*$e " "$here/references/MODEL-steward.md" || echo "$e" >> "$t/noE"; done
[ ! -s "$t/noE" ] && ok "every E-rule the checklist cites is defined in MODEL" || bad "E-rules" "$(tr '\n' ' ' < "$t/noE")"
uncited=$(awk -F'\t' 'NR>1 && $1 !~ /^(gnu-evaluation|gnu-license-list|gnulib-.*)$/ {print $1}' "$M" | while read -r s; do grep -q ":$s\]" "$here/references/MODEL-steward.md" || echo "$s"; done)
[ -z "$uncited" ] && ok "every rule-bearing manifest row is cited in MODEL" || bad "uncited rows" "$uncited"

# 7. the suggested header is the recommended form, and notices.md carries it verbatim
sh "$S/ns1hd" --suggest x.c --holder "A. Person" --license GPL-3.0-or-later > "$t/o" 2>&1
has "--suggest x.c: C comment opener" '^/\*' "$t/o"; has "--suggest: the gpl-howto sentence" 'as published by the Free Software Foundation, either version 3 of the' "$t/o"
has "notices.md: the multi-file template" 'This file is part of NAME' "$here/references/notices.md"
sh "$S/ns1hd" --suggest x.js --holder "A. Person" --license GPL-3.0-or-later > "$t/o" 2>&1
has "--suggest x.js: the LibreJS label first, named by its SPDX id" '^// @license magnet:.*gpl-3.0.txt GPL-3.0-or-later$' "$t/o"
has "--suggest x.js: asks for @license-end at the end" '@license-end' "$t/o"
has "notices.md: the LibreJS combined form" '// @license-end' "$here/references/notices.md"
has "notices.md: the all-permissive notice" 'Copying and distribution of this file, with or without modification' "$here/references/notices.md"

# 8. what SKILL.md names exists
for f in references/MODEL-steward.md references/notices.md references/checklist.md references/PERSONA-template-steward.md references/INQUIRE.md references/canon-seed.tsv references/canon.tsv scripts/nslib.sh scripts/ns1op scripts/ns1hd scripts/ns2hw scripts/ns2ld scripts/ns2cn tests/spec.pl; do
  [ -f "$here/$f" ] && ok "ships $f" || bad "ships $f" "absent"; done

# 9. the dynaloader serves it (both readers, when present)
if [ -f "$seat/bin/ss1ls" ]; then sh "$seat/bin/ss1ls" --cat nongnu-steward "$here/.." > "$t/o" 2>&1; has "bin/ss1ls --cat serves SKILL.md" '^# nongnu-steward' "$t/o"; fi
if [ -d "$seat/polygram/mcp" ]; then
  (cd "$seat" && SOFT_SKILLS="$here/.." PYTHONDONTWRITEBYTECODE=1 python3 -c '
import sys; sys.path.insert(0, ".")
from polygram.mcp import softskills as s
r = s.read({"name": "nongnu-steward", "file": "references/MODEL-steward.md"})
assert r["text"].startswith("# MODEL-steward"), r["say"]
assert any(f == "references/canon.tsv" for f in s.read({"name": "nongnu-steward"})["files"])
print("served", r["bytes"], "bytes")' > "$t/o" 2>&1) && ok "polygram softskills.read serves the model ($(cat "$t/o"))" || bad "softskills.read" "$(tail -2 "$t/o")"
fi

# 10. persona template gauges with no FAULT where cs1gk exists
if [ -f "$seat/bin/cs1gk" ]; then python3 "$seat/bin/cs1gk" "$here/references/PERSONA-template-steward.md" > "$t/o" 2>&1; has "cs1gk: template has FAULT 0" 'FAULT 0' "$t/o"; fi

if [ "${1:-}" = --prove-red ]; then
  before=$fail; has "PLANTED (must FAIL)" 'this text is not there' "$here/SKILL.md" >/dev/null
  if [ $fail -gt $before ]; then echo "PASS: harness correctly went red under a planted bad expectation"; exit 0; fi
  echo "FAIL: harness could not go red"; exit 1
fi
echo "TOTAL pass=$pass fail=$fail"; [ $fail -eq 0 ]
