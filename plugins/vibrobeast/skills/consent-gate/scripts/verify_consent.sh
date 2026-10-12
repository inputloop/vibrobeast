#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# verify_consent.sh — automate gates G1,G2,G3,G7 of the consent gate.
# G4 (dual-source fetch), G5 (per-party), G6 (prohibited-category judgment)
# are printed as MANUAL — the agent completes them with web_fetch + the record.
# Read-only. Never writes credentials anywhere. Exit 0 = auto-gates pass (pending
# manual); non-zero = a hard park.
set -eu

# --prove-red: a valid fixture record must pass the auto gates; each mutant
# (blanket grant, rushed reconfirm, expired window) must park.
prove_red() {
  self=$0
  t=${TMPDIR:-/tmp}/verify-consent.$$
  mkdir -p "$t" || exit 2
  bad=0
  now=$(date +%s)
  ts() { date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -r "$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
         || perl -MPOSIX -e 'print strftime("%Y-%m-%dT%H:%M:%SZ", gmtime($ARGV[0])), "\n"' "$1"; }
  rec() {  # rec FILE ISSUED RECONFIRMED EXPIRES ACTION
    cat > "$1" <<EOR
-----BEGIN CONSENT PAYLOAD-----
record_id:        prove-red-fixture
schema:           consent-record/v1
issued:           $(ts "$2")
reconfirmed:      $(ts "$3")
expires:          $(ts "$4")
issuer:
  name:           Fixture Keeper
  principal:      keeper@example.org
grant:
  action:         $5
  target_host:    fixture-host
  mode:           read-only
affirmation:      "Specific, not blanket. Unrushed and uncoerced."
-----END CONSENT PAYLOAD-----
EOR
  }
  case_() {  # case_ LABEL WANT-EXIT WANT-TEXT FILE
    set +e; out=$(sh "$self" --record "$4" 2>&1); rc=$?; set -e
    if [ "$rc" -eq "$2" ] && printf '%s\n' "$out" | grep -Eq "$3"; then
      echo "  ok    $1 (exit $rc)"
    else
      echo "  FAIL  $1 (exit $rc, want $2 and /$3/)"; bad=$((bad+1))
    fi
  }
  rec "$t/good.rec"    $((now-3600)) $((now-2400)) $((now+3600)) 'read one log file'
  rec "$t/all.rec"     $((now-3600)) $((now-2400)) $((now+3600)) 'ALL'
  rec "$t/rushed.rec"  $((now-3600)) $((now-3300)) $((now+3600)) 'read one log file'
  rec "$t/expired.rec" $((now-7200)) $((now-6000)) $((now-600))  'read one log file'
  echo "verify_consent --prove-red"
  case_ 'control: valid specific fresh record'   0 'auto-gates PASS'          "$t/good.rec"
  case_ 'mutant:  blanket grant "ALL"'           1 'FAIL.*G1/G7'              "$t/all.rec"
  case_ 'mutant:  reconfirmed < issued+10m'      1 'FAIL.*G2 fresh.*rushed'   "$t/rushed.rec"
  case_ 'mutant:  expired window'                1 'FAIL.*G2 fresh.*outside'  "$t/expired.rec"
  case_ 'mutant:  no record'                     2 'PARK: no record'          "$t/missing.rec"
  # G3: a correctly bound hash passes; a wrong one fails
  cp "$t/good.rec" "$t/bound.rec"
  h=$(REC="$t/bound.rec"; awk '/-----BEGIN CONSENT PAYLOAD-----/{f=1;next} /-----END CONSENT PAYLOAD-----/{f=0} f' "$t/bound.rec" \
      | grep -vE '^[[:space:]]*payload_sha256:' | { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; } | cut -d' ' -f1)
  sed "s/^-----END CONSENT PAYLOAD-----\$/payload_sha256:   $h\n-----END CONSENT PAYLOAD-----/" "$t/bound.rec" > "$t/bound.tmp" && mv "$t/bound.tmp" "$t/bound.rec"
  sed "s/^payload_sha256:   .*/payload_sha256:   $(printf '%064d' 0)/" "$t/bound.rec" > "$t/wrong.rec"
  case_ 'control: payload_sha256 bound correctly' 0 'PASS.*G3 sha-bind'      "$t/bound.rec"
  # G2 on a box whose date has no -d (BSD/macOS): a shim refuses -d; freshness must still parse
  mkdir -p "$t/bsd"; real=$(command -v date)
  printf '#!/bin/sh\nfor a; do [ "$a" = -d ] && { echo "date: illegal option -- d" >&2; exit 1; }; done\nexec %s "$@"\n' "$real" > "$t/bsd/date"; chmod +x "$t/bsd/date"
  set +e; out=$(PATH="$t/bsd:$PATH" sh "$self" --record "$t/good.rec" 2>&1); rc=$?; set -e
  if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q 'PASS.*G2 fresh'; then echo "  ok    control: freshness parses without GNU date -d (exit 0)"
  else echo "  FAIL  control: freshness parses without GNU date -d (exit $rc)"; bad=$((bad+1)); fi
  case_ 'mutant:  payload_sha256 wrong'           1 'FAIL.*G3 sha-bind'      "$t/wrong.rec"
  rm -rf "$t"
  if [ "$bad" -eq 0 ]; then
    echo "prove-red: every mutant parked and the control passed"; return 0
  fi
  echo "prove-red: $bad case(s) misbehaved"; return 1
}
[ "${1:-}" = --prove-red ] && { prove_red; exit $?; }
REC=""; SIG=""; ALLOW=""
while [ $# -gt 0 ]; do
  case "$1" in
    --record) REC="$2"; shift 2;;
    --sig) SIG="$2"; shift 2;;
    --allowed-signers) ALLOW="$2"; shift 2;;
    *) echo "usage: verify_consent.sh --record FILE [--sig FILE --allowed-signers FILE] | --prove-red" >&2; exit 2;;
  esac
done
[ -n "$REC" ] && [ -f "$REC" ] || { echo "PARK: no record"; exit 2; }

payload() { awk '/-----BEGIN CONSENT PAYLOAD-----/{f=1;next} /-----END CONSENT PAYLOAD-----/{f=0} f' "$REC"; }
field()   { payload | grep -E "^[[:space:]]*$1:" | head -1 | sed -E "s/^[[:space:]]*$1:[[:space:]]*//"; }

fail=0
note() { printf '  [%-4s] %-22s %s\n' "$1" "$2" "$3"; }

echo "verify_consent — $REC"
echo
echo " AUTO GATES:"

# G1 / G7 — blanket-grant scan over the whole record (case-insensitive, word-ish)
if grep -iE '\b(all|any|everything|whatever|full use|carte ?blanche|noconfirm)\b' "$REC" \
     | grep -ivE 'not blanket|ALL gates|no lift' >/dev/null; then
  note FAIL "G1/G7 specific" "blanket/override term found — auto-park"; fail=1
else
  note PASS "G1/G7 specific" "no blanket or override terms"
fi

# G2 — freshness: issued <= now <= expires, reconfirmed >= issued+600s
now=$(date +%s)
# ISO-8601 UTC -> epoch seconds. GNU date first, then BSD/macOS date, then perl (2026-09-27: GNU's
# `date -d` alone made every record fail freshness on a BSD box -- closed, but never passable).
iso() {
  date -u -d "$1" +%s 2>/dev/null && return
  date -j -u -f '%Y-%m-%dT%H:%M:%SZ' "$1" +%s 2>/dev/null && return
  perl -MTime::Local -e '@t = $ARGV[0] =~ /^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z$/ or exit 1;
    print timegm($t[5], $t[4], $t[3], $t[2], $t[1] - 1, $t[0]), "\n"' "$1" 2>/dev/null && return
  echo ""
}
is=$(iso "$(field issued)"); ex=$(iso "$(field expires)"); rc=$(iso "$(field reconfirmed)")
if [ -z "$is" ] || [ -z "$ex" ]; then note FAIL "G2 fresh" "issued/expires unparseable"; fail=1
elif [ "$now" -lt "$is" ] || [ "$now" -gt "$ex" ]; then note FAIL "G2 fresh" "now outside [issued,expires]"; fail=1
elif [ -n "$rc" ] && [ $((rc - is)) -lt 600 ]; then note FAIL "G2 fresh" "reconfirmed < issued+10m (rushed)"; fail=1
else note PASS "G2 fresh" "within window; reconfirm gap ok"; fi

# G3 — payload sha256 binding + signature
# The hash covers the payload WITHOUT its own payload_sha256 line (a line cannot carry its own hash;
# before 2026-09-27 it was included, so a filled record could never pass G3). The signature still
# covers the whole payload, that line included.
sha_of() { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi | cut -d' ' -f1; }
bound() { payload | grep -vE '^[[:space:]]*payload_sha256:'; }
calc=$(bound | sha_of)
stated=$(field payload_sha256)
case $stated in "<"*) stated= ;; esac   # a template placeholder is "not filled"
if [ -n "$stated" ]; then
  [ "$calc" = "$stated" ] && note PASS "G3 sha-bind" "payload_sha256 matches" \
                          || { note FAIL "G3 sha-bind" "payload_sha256 MISMATCH"; fail=1; }
else note WARN "G3 sha-bind" "payload_sha256 not filled (template/unsigned)"; fi
if [ -n "$SIG" ] && [ -n "$ALLOW" ]; then
  if payload | ssh-keygen -Y verify -f "$ALLOW" -I "$(field principal)" -n consent-record -s "$SIG" >/dev/null 2>&1; then
    note PASS "G3 signature" "ssh-keygen -Y verify OK"
  else note FAIL "G3 signature" "signature verify FAILED"; fail=1; fi
else note WARN "G3 signature" "no --sig/--allowed-signers given (crypto check skipped)"; fi

echo
echo " MANUAL GATES (agent must complete before unblock):"
note TODO "G4 dual-source" "web_fetch both identity_urls; need 2/2 same key, independent origins"
note TODO "G5 per-party"   "each affected party out-of-scope OR own signed record; family parked"
note TODO "G6 prohibited"  "prohibited_category_decision explicit; agent-held => park-lift on record"
echo
if [ "$fail" -ne 0 ]; then echo "RESULT: CLAUD_QA_HOLD (parked) — an auto gate failed."; exit 1; fi
echo "RESULT: auto-gates PASS — pending G4/G5/G6. Action stays parked until those clear."; exit 0
