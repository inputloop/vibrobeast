#!/bin/sh
# tests.sh -- context-stack's tools held by a second language (sh reading the Python builds).
# usage: sh tests.sh [--prove-red]     --prove-red runs each dropped tool's own planted faults, from here
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
set -u
here=$(cd "$(dirname "$0")" && pwd); S=$here/scripts
pass=0 fail=0
ok() { if eval "$2"; then pass=$((pass + 1)); echo "  ok    $1"; else fail=$((fail + 1)); echo "  FAIL  $1"; [ -n "${3:-}" ] && eval "$3" 2>&1 | sed 's/^/        /'; fi; }   # $3: a command that shows why
if [ "${1:-}" = --prove-red ]; then
  w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
  ok "stacks.py's own planted faults, run from this skill" '(cd "$S" && python3 stacks.py --prove-red >"$w/a" 2>&1)' 'cat "$w/a"'
  ok "check-stacks.sh's own planted faults, run from this skill" '(cd "$S" && sh check-stacks.sh --prove-red >"$w/b" 2>&1)' 'cat "$w/b"'
  echo "context-stack --prove-red: $pass ok, $fail failed"; [ "$fail" -eq 0 ]; exit; fi
w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
c() { printf '%s\n' "$@" | python3 "$S/cstk.py"; }
out=$(c "push a first" "cite a 3" "cite a 1" "cite a 5")
ok "S1 a rock is forced out as a boulder at 4 and a mountain at 9" 'printf "%s\n" "$out" | grep -qx "promote a BOULDER" && printf "%s\n" "$out" | grep -qx "promote a MOUNTAIN"' 'printf "%s\\n" "$out"'
out=$(c "push a" "push b" "cite b 2" "fort a" "fort b" "floor" "floors")
ok "S2 floor orders the fort by pressure and records a generation" 'printf "%s\n" "$out" | grep -qx "floor g1 b a" && printf "%s\n" "$out" | grep -qx "floors 1"' 'printf "%s\\n" "$out"'
out=$(c "push a" "tension a held/raised=0.5 said/asked=-0.25" "suspended" "pin t1" "suspended")
ok "S3 a tension starts suspended and pin settles it" 'printf "%s\n" "$out" | grep -q "^tension a t1 SUSPENDED" && printf "%s\n" "$out" | tail -1 | grep -qx "suspended 0"' 'printf "%s\\n" "$out"'
out=$(c "push a" "remove nothing" "pin t9" "fly")
ok "S4 a refusal is printed, never a crash" 'printf "%s\n" "$out" | grep -q "^refuse remove nothing" && printf "%s\n" "$out" | grep -qx "refuse fly: unknown command"' 'printf "%s\\n" "$out"'
printf 'r1\tpalace\t3\t2026-10-01\tthe floor\nr2\tpalace\t2\t2026-10-10\tmeaning both ways\nr3\twords\t2\t2026-10-12\tseam\n' > "$w/PILE.tsv"
python3 "$S/stacks.py" "$w/PILE.tsv" "$w/out" --dial 2 --today 2026-10-15 > "$w/log" 2>&1
ok "S5 the file layer writes the pile's semaphore and a boulder for a group at the dial" '[ -f "$w/out/SEMAPHORE.md" ] && [ -f "$w/out/boulders/palace.md" ] && [ -f "$w/out/boulders/words.md" ]' 'cat "$w/log"'
ok "S6 and a mountain for a group at the dial twice over (2 x 2 = 4: palace carries 5, words only 2)" '[ -f "$w/out/mountains/palace.md" ] && [ ! -f "$w/out/mountains/words.md" ]' 'ls -R "$w/out"'
ok "S7 the second reader holds the files doubly linked (check-stacks.sh)" 'sh "$S/check-stacks.sh" "$w/out" 2 >"$w/chk" 2>&1' 'cat "$w/chk"'
ok "S8 the file layer refuses a folder that already holds a pile" '! python3 "$S/stacks.py" "$w/PILE.tsv" "$w/out" --dial 2 >/dev/null 2>&1'
echo "context-stack: $pass ok, $fail failed"; [ "$fail" -eq 0 ]
