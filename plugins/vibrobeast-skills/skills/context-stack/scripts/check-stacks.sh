#!/bin/sh
# check-stacks.sh -- a second reader for stacks.py's files, in sh + awk: doubly linked, thresholds, the dial's direction.
#   Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  Authored by Mentat (for Corwin).
#   SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# usage: sh check-stacks.sh OUTDIR DIAL       S1-S3 on one built tree
#        sh check-stacks.sh --dial-sweep PILE  build at dials 1 2 4 9 17 and check the file count never grows (S4)
#        sh check-stacks.sh --prove-red
#   S1  every boulder links back to SEMAPHORE.md, and SEMAPHORE.md links forward to every boulder file that exists
#   S2  a mountain file exists only where its boulder links up to it, and links back down to that boulder
#   S3  each boulder's stated pressure is at least DIAL; each mountain's at least DIAL x DIAL
#   S4  turning the dial up never makes more files
LC_ALL=C; export LC_ALL
here=$(cd "$(dirname "$0")" && pwd)

check() {
  o=$1; d=$2; f=0
  for b in "$o"/boulders/*.md; do
    [ -f "$b" ] || continue; bn=$(basename "$b")
    grep -q '](../SEMAPHORE.md#' "$b" || { echo "FAIL S1 $bn has no link back to the pile"; f=$((f+1)); }
    grep -q "](boulders/$bn)" "$o/SEMAPHORE.md" || { echo "FAIL S1 the pile does not link to boulders/$bn"; f=$((f+1)); }
    p=$(sed -n 's/.*Pressure \([0-9]*\) (the dial is.*/\1/p' "$b" | head -1)
    [ -n "$p" ] && [ "$p" -ge "$d" ] || { echo "FAIL S3 boulders/$bn pressure ${p:-?} below the dial $d"; f=$((f+1)); }
  done
  for m in "$o"/mountains/*.md; do
    [ -f "$m" ] || continue; bn=$(basename "$m")
    grep -q "](../boulders/$bn)" "$m" || { echo "FAIL S2 mountains/$bn does not link down to its boulder"; f=$((f+1)); }
    grep -q "](../mountains/$bn)" "$o/boulders/$bn" 2>/dev/null || { echo "FAIL S2 boulders/$bn does not link up to its mountain"; f=$((f+1)); }
    p=$(sed -n 's/.*Pressure \([0-9]*\), at least the dial squared.*/\1/p' "$m" | head -1)
    [ -n "$p" ] && [ "$p" -ge $((d*d)) ] || { echo "FAIL S3 mountains/$bn pressure ${p:-?} below $((d*d))"; f=$((f+1)); }
  done
  # a forward link from the pile must land on a file that exists
  for l in $(grep -o '](boulders/[^)]*)' "$o/SEMAPHORE.md" | sed 's/](//;s/)$//'); do [ -f "$o/$l" ] || { echo "FAIL S1 the pile links to $l, which is missing"; f=$((f+1)); }; done
  echo "check-stacks: $o at dial $d: $f fault(s)"; [ $f = 0 ]
}

sweep() {
  t=${TMPDIR:-/tmp}/stk.$$; mkdir -p "$t"; prev=999999; f=0
  for d in 1 2 4 9 17; do
    python3 "$here/stacks.py" "$1" "$t/d$d" --dial $d --today 2026-10-11 > /dev/null || f=$((f+1))
    c=$(find "$t/d$d" -name '*.md' | wc -l); check "$t/d$d" $d > /dev/null || f=$((f+1))
    printf 'dial %-2s %3s file(s)\n' $d $c; [ "$c" -le "$prev" ] || { echo "FAIL S4 dial $d made more files ($c) than the dial below it ($prev)"; f=$((f+1)); }; prev=$c
  done
  rm -rf "$t"; echo "check-stacks --dial-sweep: $f fault(s)"; [ $f = 0 ]
}

prove_red() {
  t=${TMPDIR:-/tmp}/stkred.$$; mkdir -p "$t"; pass=0; n=0
  printf 'a\tx\t3\t2026-10-01\tone\nb\tx\t1\t2026-09-01\ttwo\nd\tz,x\t12\t2026-10-05\tfour\n' > "$t/p.tsv"
  python3 "$here/stacks.py" "$t/p.tsv" "$t/o" --dial 4 --today 2026-10-11 > /dev/null
  n=$((n+1)); check "$t/o" 4 > /dev/null && pass=$((pass+1))                               # clean reads clean
  cp -r "$t/o" "$t/a"; sed -i 's#](../SEMAPHORE.md#](../ELSEWHERE.md#g' "$t/a/boulders/z.md"
  n=$((n+1)); check "$t/a" 4 > /dev/null || pass=$((pass+1))                               # S1 back link cut
  cp -r "$t/o" "$t/b"; sed -i 's#](../mountains/x.md)#](nowhere)#' "$t/b/boulders/x.md"
  n=$((n+1)); check "$t/b" 4 > /dev/null || pass=$((pass+1))                               # S2 up link cut
  n=$((n+1)); check "$t/o" 5 > /dev/null || pass=$((pass+1))                               # S3 read at a higher dial
  cp -r "$t/o" "$t/c"; rm "$t/c/boulders/z.md"
  n=$((n+1)); check "$t/c" 4 > /dev/null || pass=$((pass+1))                               # S1 forward link to a missing file
  rm -rf "$t"; echo "check-stacks --prove-red: $pass/$n planted cases read as planted"; [ $pass = $n ]
}

case "${1:-}" in
  --prove-red) prove_red ;;
  --dial-sweep) sweep "$2" ;;
  "") sed -n '2,12p' "$0" ;;
  *) check "$1" "${2:-4}" ;;
esac
