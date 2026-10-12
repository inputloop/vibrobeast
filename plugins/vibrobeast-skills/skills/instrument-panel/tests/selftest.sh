#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# selftest.sh — instrument-panel test kit: build a scratch tree whose state is
# KNOWN, run the panel, assert every classification. The panel's eval is that
# its output is TRUE against a tree known by other means — this makes that
# check mechanical. Needs: gpg, GNU coreutils. Touches only its own tmpdir.
# Exit 0 = all assertions hold; 1 = a classification lied; 3 = kit fault.

set -u
command -v gpg >/dev/null 2>&1 || { echo "KIT-FAULT: gpg not found" >&2; exit 3; }

HERE=$(cd "$(dirname "$0")" && pwd)
PANEL=$HERE/../scripts/panel.sh
[ -f "$PANEL" ] || { echo "KIT-FAULT: panel.sh not found at $PANEL" >&2; exit 3; }

T=$(mktemp -d) || exit 3
trap 'rm -rf "$T"' EXIT INT TERM
export GNUPGHOME=$T/gnupg
mkdir -p "$GNUPGHOME"; chmod 700 "$GNUPGHOME"

# throwaway key (no passphrase, transient)
gpg -q --batch --pinentry-mode loopback --passphrase '' \
    --quick-generate-key "panel-selftest <selftest@invalid>" ed25519 sign never \
    2>/dev/null || { echo "KIT-FAULT: keygen failed" >&2; exit 3; }
FPR=$(gpg --list-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')
gpg -q --export --armor "$FPR" > "$T/key.asc"

R=$T/tree
mkdir -p "$R/sessions"
sign_inline() { gpg -q --batch --pinentry-mode loopback --passphrase '' \
  --clearsign --local-user "$FPR" -o "$1.tmp" "$1" && mv "$1.tmp" "$1"; }
sign_detach() { gpg -q --batch --pinentry-mode loopback --passphrase '' \
  --detach-sign --armor --local-user "$FPR" -o "$1.asc" "$1"; }

# CANARY + fixtures, one per classification
echo "canary content"    > "$R/CANARY.md";  sign_inline "$R/CANARY.md"
echo "good inline"       > "$R/g-inline.md"; sign_inline "$R/g-inline.md"
echo "good detached"     > "$R/g-detach.md"; sign_detach "$R/g-detach.md"
echo "no signature here" > "$R/nosig.md"
echo "double ceremony"   > "$R/double.md";  sign_detach "$R/double.md"; sign_inline "$R/double.md"
echo "edit debt"         > "$R/debt.md";    sign_detach "$R/debt.md"
  sleep 1; echo "edited after signing" >> "$R/debt.md"          # file newer than .asc -> DEBT
echo "inline then edited" > "$R/idebt.md";  sign_inline "$R/idebt.md"
  # corrupt a byte INSIDE the signed body (trailing appends are ignored by gpg);
  # no detached companion -> inline verify fails -> IDEBT
  sed -i 's/inline then edited/inline then EDITED/' "$R/idebt.md"
echo "tamper shaped"     > "$R/tamper.md";  sign_detach "$R/tamper.md"
  # content swapped, then .asc touched NEWER than the file: the mtime heuristic
  # cannot excuse it as edit-after-sign -> tamper-shaped BAD (the RED we must never miss)
  printf 'silently swapped\n' > "$R/tamper.md"
  sleep 1; touch "$R/tamper.md.asc"
echo "seal body" > "$R/sessions/2026-01-01-end-session-test.md"
echo "9.9.99" > "$R/VERSION"
mkdir -p "$R/Inbox"; echo x > "$R/Inbox/drop1"

cat > "$T/conf" <<EOF
PIN_FPR=$FPR
KEY_ASC=$T/key.asc
CANARY=CANARY.md
SEAL_GLOB="sessions/*end-session*.md"
MAX_SEAL_AGE_DAYS=99999
DEBT_PARTY_AT=2
MAIL_DIRS="Inbox outbox"
PRUNE=".git"
EOF

OUT=$T/out
# panel resets GNUPGHOME to its own tmp and imports KEY_ASC — as in real runs
sh "$PANEL" -c "$T/conf" "$R" > "$OUT" 2>&1
rc=$?

fail=0
expect() { # expect PATTERN DESCRIPTION
  if grep -q "$1" "$OUT"; then echo "ok   - $2"
  else echo "FAIL - $2 (wanted: $1)"; fail=1; fi
}
expect "G0 MAIL     : Inbox/ holds 1"                    "G0 counts the drop"
expect "G1 CANARY   : GOOD"                              "G1 canary proves reader"
expect "GOOD=3 "                                         "G2 goods (canary+inline+detach)"
expect "NOSIG=2 "                                        "G2 nosig (nosig.md + the unsigned seal fixture)"
expect "DOUBLE=1 "                                       "G2 double ceremony"
expect "EDIT-DEBT=1 "                                    "G2 edit-after-sign debt"
expect "INLINE-DEBT=1 "                                  "G2 inline debt"
expect "BAD=1 "                                          "G2 tamper-shaped BAD"
expect "dbl  ./double.md"                                "DOUBLE names the file"
expect "RED ./tamper.md"                                 "BAD names the file"
expect "G3 SEAL     : sessions/2026-01-01-end-session-test.md (fresh" "G3 finds the seal"
expect "G4 VERSION  : 9.9.99"                            "G4 reads VERSION"
expect "signing pressure: DEBT=2 >= 2"                   "party line fires at threshold"
expect "PANEL: RED"                                      "verdict RED (BAD present)"
[ "$rc" -eq 1 ] && echo "ok   - exit code 1 (RED)" || { echo "FAIL - exit code (got $rc, wanted 1)"; fail=1; }

if [ "$fail" -eq 0 ]; then echo "SELFTEST: PASS (all classifications proven)"; exit 0
else echo "SELFTEST: FAIL — panel output kept at $OUT for reading"; trap - EXIT; exit 1; fi
