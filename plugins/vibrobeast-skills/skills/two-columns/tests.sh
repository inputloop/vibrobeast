#!/bin/sh
# tests.sh -- fixtures vs expected verdicts for the two-columns gauge.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
#   sh tests.sh              run the suite
#   sh tests.sh --prove-red  prove the suite can fail
set -eu
here=$(dirname "$0")
DL=$here/scripts/dl1nk
fail=0
pass=0

ok() { pass=$((pass+1)); printf '  PASS  %s\n' "$1"; }
no() { fail=$((fail+1)); printf '  FAIL  %s\n    %s\n' "$1" "${2:-}"; }

t=$(mktemp -d) || exit 2
trap 'rm -rf "$t"' EXIT

printf 'two-columns: verdicts\n'
sh "$DL" --prove-red || fail=$((fail+1))

printf '\ntwo-columns: pressure\n'

mkdir -p "$t/cited"
cat > "$t/notes.md" <<'X'
Pricing — how we set the list price (comes up when: price, quote)
From: a document (2026-Q3-pricing.md)
Would-change: finance publishing a new list
first-seen: notes:/pricing/g0001.md
last-cited: 2026-09-14 — the vendor email

Cadence — we ship on Fridays (comes up when: release, deploy)
From: someone else (Sam)
Would-change: a release landing on any other day
first-seen: notes:/cadence/g0001.md
last-cited: 2026-08-02 — the runbook
X

printf '2026-09-10 — a\n2026-09-12 — b\n2026-09-14 — c\n' > "$t/cited/Pricing.txt"
: > "$t/cited/Cadence.txt"

out=$(sh "$DL" "$t/notes.md" --cited "$t/cited")

got=$(printf '%s\n' "$out" | awk '$3=="Pricing" {print $2}')
[ "$got" = "3" ] && ok "pressure counts citation lines (Pricing=3)" \
                 || no "pressure counts citation lines" "wanted 3, got '$got'"

got=$(printf '%s\n' "$out" | awk '$3=="Cadence" {print $2}')
[ "$got" = "0" ] && ok "an empty citation list is pressure 0" \
                 || no "an empty citation list is pressure 0" "wanted 0, got '$got'"

got=$(printf '%s\n' "$out" | awk '$3=="Unheard" {print $2}')
[ -z "$got" ] && ok "a note that is not in the file is not reported" \
              || no "phantom note reported" "$got"

# A note with no citation file at all must read 0, not blank and not an error.
cat > "$t/fresh.md" <<'X'
Brandnew — written just now (comes up when: new)
From: me
Would-change: finding I had written it before
first-seen: notes:/brandnew/g0001.md
last-cited: 2026-09-14 — this test
X
got=$(sh "$DL" "$t/fresh.md" --cited "$t/cited" | awk '$3=="Brandnew" {print $2}')
[ "$got" = "0" ] && ok "a note with no citation file reads 0, not an error" \
                 || no "missing citation file" "wanted 0, got '$got'"

# Without --cited the column is '-', not a fabricated zero.  A gauge that
# invents a number when it cannot measure is worse than one that says so.
got=$(sh "$DL" "$t/fresh.md" | awk '$3=="Brandnew" {print $2}')
[ "$got" = "-" ] && ok "no --cited means '-', never a fabricated 0" \
                 || no "unmeasured pressure" "wanted '-', got '$got'"

printf '\ntwo-columns: a notes file is untrusted input\n'

# A notes file travels between people and assistants. Gauging one must never
# be able to execute anything or read outside the citations directory.
rm -f "/tmp/dl1nk-pwned-$$" 2>/dev/null || true
cat > "$t/evil.md" <<EVIL
Pricing\$(touch /tmp/dl1nk-pwned-$$) — how we set the price (comes up when: p)
From: a document (x.md)
Would-change: a new list
first-seen: notes:/p/g0001.md
last-cited: 2026-09-14 — here
EVIL
sh "$DL" "$t/evil.md" --cited "$t/cited" >/dev/null 2>&1 || true
if [ -e "/tmp/dl1nk-pwned-$$" ]; then
  no "command substitution in a seam name does not execute" "it executed"
  rm -f "/tmp/dl1nk-pwned-$$"
else
  ok "command substitution in a seam name does not execute"
fi

# Grep-for-a-string would be a false positive here: dl1nk PRINTS the seam name,
# so the marker appears in the output whether or not anything ran. Use a marker
# that can only exist if a command executed.
rm -f "/tmp/dl1nk-quote-$$" 2>/dev/null || true
cat > "$t/evil2.md" <<EVIL2
Pricing"; touch /tmp/dl1nk-quote-$$; echo " — x (comes up when: p)
From: a document (x.md)
Would-change: a new list
first-seen: notes:/p/g0001.md
last-cited: 2026-09-14 — here
EVIL2
sh "$DL" "$t/evil2.md" --cited "$t/cited" >/dev/null 2>&1 || true
if [ -e "/tmp/dl1nk-quote-$$" ]; then
  no "quote-breaking in a seam name does not execute" "it executed"
  rm -f "/tmp/dl1nk-quote-$$"
else
  ok "quote-breaking in a seam name does not execute"
fi

mkdir -p "$t/outside" && printf 'a\nb\nc\nd\ne\n' > "$t/outside/secret.txt"
cat > "$t/trav.md" <<'TRAV'
../outside/secret — traversal attempt (comes up when: t)
From: me
Would-change: x
first-seen: notes:/t.md
last-cited: now
TRAV
got=$(sh "$DL" "$t/trav.md" --cited "$t/cited" | awk 'NR==2 {print $2}')
[ "$got" = "0" ] && ok "a seam name cannot read outside the citations dir" \
                 || no "path traversal" "read $got lines from outside"

printf '\ntwo-columns: every note in the file is counted\n'
cat > "$t/keyhead.md" <<'KH'
Alpha — one (comes up when: a)
From: me
Would-change: x
first-seen: notes:/a.md
last-cited: now

Beta: two — a head that looks like a key (comes up when: b)
From: me
Would-change: y
first-seen: notes:/b.md
last-cited: now
KH
got=$(sh "$DL" "$t/keyhead.md" | awk '/note\(s\)/ {print $1}')
[ "$got" = "2" ] && ok "a key-shaped head is still a note" \
                 || no "a key-shaped head is still a note" "counted $got of 2"

printf '\ntwo-columns: the paste-in file\n'
A=$here/assets/TWO-COLUMNS.md
if [ -f "$A" ]; then
  ok "assets/TWO-COLUMNS.md exists"
  # The give-away file must carry no house vocabulary: that is the only
  # property that makes it work in a stranger's assistant.
  if grep -qiE 'seam|semaphore|pocket-mentat|fortress|palace|c4|polygram|mentcached|keeper|\[\[' "$A"; then
    no "paste-in file is free of house jargon" \
       "$(grep -inoE 'seam|semaphore|pocket-mentat|fortress|palace|c4|polygram|mentcached|keeper|\[\[' "$A" | head -5 | tr '\n' ' ')"
  else
    ok "paste-in file is free of house jargon"
  fi
  # It must also be self-contained: no path into a tree the reader lacks.
  if grep -qE '(/f/claude|F:\\|AS4CE|~/\.claude)' "$A"; then
    no "paste-in file is self-contained" "it names a path only this house has"
  else
    ok "paste-in file is self-contained"
  fi
else
  no "assets/TWO-COLUMNS.md exists" "missing"
fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"

if [ "${1:-}" = "--prove-red" ]; then
  printf '\nprove-red: break a fixture and require the suite to notice\n'
  cat > "$t/broken.md" <<'X'
Pricing — how we set the list price (comes up when: price)
From: a document (x.md)
Would-change: a new list
first-seen: notes:/pricing/g0001.md
last-cited: 2026-09-14 — here
X
  # Claim the wrong verdict on purpose; the comparison must reject it.
  got=$(sh "$DL" "$t/broken.md" | awk 'NR==2 {print $1}')
  if [ "$got" = "UNSOURCED" ]; then
    printf 'prove-red FAILED: a sound note was called UNSOURCED\n'; exit 1
  fi
  if [ "$got" != "OK" ]; then
    printf 'prove-red FAILED: expected OK, got %s\n' "$got"; exit 1
  fi
  # And the inverse: strip the source and require the verdict to move.
  sed '/^From:/d' "$t/broken.md" > "$t/broken2.md"
  got2=$(sh "$DL" "$t/broken2.md" | awk 'NR==2 {print $1}')
  if [ "$got2" = "$got" ]; then
    printf 'prove-red FAILED: removing From: did not change the verdict\n'; exit 1
  fi
  printf 'prove-red PASS: verdict moved %s -> %s when the source was removed\n' \
    "$got" "$got2"
fi

[ "$fail" -eq 0 ] || exit 1
