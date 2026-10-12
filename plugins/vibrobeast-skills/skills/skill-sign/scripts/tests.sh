#!/bin/sh
# tests.sh --- fixtures + expected verdicts for skill-sign.sh's tiered
# `verify` (2026-09-04) and its check.sh companion.
#
# Self-contained (prove-a-promise: opens itself, ships what it needs,
# proves itself): generates its own throwaway gpg key in a scratch
# GNUPGHOME, so tier-2 is exercised for real without touching Corwin's
# actual key or keyring. Nothing here reads or writes outside $tmp.
#
# usage:
#   sh tests.sh              run the fixture suite; exit 0 iff all pass
#   sh tests.sh --prove-red  plant a deliberately wrong expectation and
#                            confirm THIS suite reports it as a failure
#                            (prove-red-discipline: a green suite that
#                            can't go red is indistinguishable from one
#                            that isn't running)
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SIGN="$here/skill-sign.sh"
CHECK="$here/check.sh"

# --prove-red: plant ONE deliberately wrong expectation (a rc this fixture
# can never actually produce) and confirm the suite reports it. Mirrors
# check.sh's own --prove-red one level up: proves THIS harness, not just
# the tool it tests, can go red.
prove_red=0
[ "${1:-}" = '--prove-red' ] && prove_red=1
nomanifest_want_rc=1
[ "$prove_red" = 1 ] && nomanifest_want_rc=99   # impossible -- forces a FAIL

pass=0
fail=0

# report NAME EXPECTED_RC ACTUAL_RC NEEDLE ACTUAL_OUTPUT
#   EXPECTED_RC may be a number, or "any" to skip the rc check.
#   NEEDLE may be empty to skip the substring check.
report() {
    name=$1; erc=$2; arc=$3; needle=$4; out=$5
    ok=1
    if [ "$erc" != any ] && [ "$arc" != "$erc" ]; then ok=0; fi
    if [ -n "$needle" ] && ! printf '%s' "$out" | grep -qF -- "$needle"; then
        ok=0
    fi
    if [ "$ok" = 1 ]; then
        pass=$((pass + 1))
        printf 'ok   %s\n' "$name"
    else
        fail=$((fail + 1))
        printf 'FAIL %s (rc=%s want=%s, looked for: %s)\n' \
            "$name" "$arc" "$erc" "$needle" >&2
        printf '     --- output ---\n%s\n     --------------\n' "$out" >&2
    fi
}

# report_not NAME NEEDLE ACTUAL_OUTPUT -- passes iff NEEDLE is ABSENT
report_not() {
    if printf '%s' "$3" | grep -qF -- "$2"; then
        fail=$((fail + 1)); printf 'FAIL %s (must not say: %s)\n     --- output ---\n%s\n' "$1" "$2" "$3" >&2
    else pass=$((pass + 1)); printf 'ok   %s\n' "$1"; fi
}

# _path DIR NAME... -- DIR holds links to every NAME found on PATH (a PATH with chosen tools only)
_path() {
    pd=$1; shift; mkdir -p "$pd"
    for b in "$@"; do
        p=$(command -v "$b" 2>/dev/null) || continue
        ln -s "$p" "$pd/$b" 2>/dev/null || true
    done
}

# _skill NAME -- makes $tmp/NAME with a SKILL.md + tool.sh, prints the path
_skill() {
    d="$tmp/$1"; mkdir -p "$d"
    printf -- '---\nname: %s\n---\n# %s\n' "$1" "$1" > "$d/SKILL.md"
    printf 'echo hi\n' > "$d/tool.sh"
    printf '%s' "$d"
}

# _verify DIR KEY -- verify DIR pinned against KEY; sets $RC and $OUT
_verify() {
    if OUT=$(PUB_SIGN_KEY="$2" sh "$SIGN" verify "$1" 2>&1); then RC=0
    else RC=$?; fi
}

tmp=$(mktemp -d) || { echo 'tests.sh: mktemp failed' >&2; exit 1; }
trap 'rm -rf "$tmp"' EXIT
GNUPGHOME="$tmp/gpghome"; mkdir -m 700 "$GNUPGHOME"; export GNUPGHOME

echo '# generating a throwaway signer key (never Corwin''s) ...'
gpg --batch --passphrase '' --quick-gen-key \
    'tests.sh throwaway <throwaway@example.invalid>' default default 0 \
    >"$tmp/genkey.log" 2>&1 \
  || { cat "$tmp/genkey.log" >&2; echo 'tests.sh: gpg key generation failed' >&2; exit 1; }
KEYID=$(gpg --batch --list-secret-keys --with-colons \
  | awk -F: '$1=="fpr"{print $10; exit}')
[ -n "$KEYID" ] || { echo 'tests.sh: could not read generated fingerprint' >&2; exit 1; }
echo "# throwaway key: $KEYID"
echo

# ---- fixture: no manifest at all -----------------------------------
d=$(_skill nomanifest)
_verify "$d" "$KEYID"
report 'no-manifest -> unsigned, cannot hash-check (rc=1)' \
    "$nomanifest_want_rc" "$RC" 'cannot even hash-check' "$OUT"

# ---- fixture: manifest present, no signature (TIER 1) ---------------
d=$(_skill tier1)
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
rm -f "$d/.signature.asc"
_verify "$d" "$KEYID"
report 'manifest only -> UNVERIFIED-AUTHOR, no gpg needed (rc=0)' \
    0 "$RC" 'UNVERIFIED-AUTHOR' "$OUT"

# same fixture, but prove tier 1 truly never touches gpg: point PATH at
# a directory with no gpg binary and confirm verify still succeeds.
noGpgPath="$tmp/no-gpg-path"; mkdir -p "$noGpgPath"
for b in sh sha256sum diff mktemp grep awk cat sed cut printf \
         find sort rm cp ln mkdir; do
    p=$(command -v "$b" 2>/dev/null) || continue
    ln -s "$p" "$noGpgPath/$b" 2>/dev/null || true
done
if OUT2=$(PATH="$noGpgPath" PUB_SIGN_KEY="$KEYID" sh "$SIGN" verify "$d" 2>&1)
then RC2=0; else RC2=$?; fi
report 'tier 1 works with NO gpg on PATH at all (rc=0)' \
    0 "$RC2" 'UNVERIFIED-AUTHOR' "$OUT2"

# ---- fixture: manifest + valid signature (TIER 2) --------------------
d=$(_skill tier2)
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
_verify "$d" "$KEYID"
report 'manifest + valid signature -> signature valid (rc=0)' \
    0 "$RC" 'signature valid' "$OUT"

# ---- fixture: tree changed since signing -----------------------------
d=$(_skill drift)
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
printf '\n# edited after signing\n' >> "$d/tool.sh"
_verify "$d" "$KEYID"
report 'tree changed after signing -> TREE CHANGED (rc=1)' \
    1 "$RC" 'TREE CHANGED' "$OUT"

report_not 'a tree that only drifted gets no key-import hint' 'import' "$OUT"

# ---- fixture: signature present, pinned key NOT in the keyring (N11) -----
d=$(_skill wrongkey)
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
_verify "$d" '0000000000000000000000000000000000000000'
report 'pinned key absent from the keyring -> key not in keyring (rc=1)' \
    1 "$RC" 'key not in keyring' "$OUT"
report_not '...and not called a failed signature' 'SIGNATURE FAILED' "$OUT"
_verify "$d" ECE77CF417C76C1ACFCE7C2B5B6135511580F007
report "Corwin's key absent -> names the .asc file and the fingerprint" \
    1 "$RC" 'key not in keyring: import skills/ECE77CF417C76C1ACFCE7C2B5B6135511580F007.asc (fingerprint ECE7 7CF4 17C7 6C1A CFCE 7C2B 5B61 3551 1580 F007)' "$OUT"

# ---- fixture: pinned key IS in the keyring, but did not sign --------------
gpg --batch --passphrase '' --quick-gen-key \
    'tests.sh second <second@example.invalid>' default default 0 >/dev/null 2>&1
KEY2=$(gpg --batch --list-secret-keys --with-colons | awk -F: -v k="$KEYID" '$1=="fpr" && $10!=k {print $10; exit}')
_verify "$d" "$KEY2"
report 'pinned key present but not the signer -> SIGNATURE FAILED (rc=1)' \
    1 "$RC" 'SIGNATURE FAILED' "$OUT"

# ---- fixture: new bytes with an OLD mtime are not "current" (B6) --------
# (no -f here: -f skips the shortcut under test, so this skill must pass the lint gate)
d=$(_skill oldmtime)
printf -- '---\nname: oldmtime\ndescription: >-\n  A small skill used only to test signing. Use it when a test needs a signable skill with a\n  valid description and nothing else.\n---\n# oldmtime\n\nBody.\n' > "$d/SKILL.md"
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign "$d" >/dev/null 2>&1
printf 'echo changed\n' > "$d/tool.sh"; touch -t 202001010000 "$d/tool.sh"
if OUT=$(PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign "$d" 2>&1); then RC=0; else RC=$?; fi
report 'edited bytes + an old mtime (as tar/unzip/cp -p leave) -> signed again' 0 "$RC" ': signed' "$OUT"
report_not '...never "already signed and current"' 'already signed and current' "$OUT"
_verify "$d" "$KEYID"
report '...and verify agrees' 0 "$RC" 'signature valid' "$OUT"

# ---- fixture: sha256sum absent, shasum present; neither (B9) --------------
if command -v shasum >/dev/null 2>&1; then
    d=$(_skill shasumonly)
    PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1; rm -f "$d/.signature.asc"
    _path "$tmp/p-shasum" sh shasum perl diff mktemp grep awk cat sed cut find sort rm cp mkdir cmp head dirname tr
    if OUT=$(PATH="$tmp/p-shasum" PUB_SIGN_KEY="$KEYID" sh "$SIGN" verify "$d" 2>&1); then RC=0; else RC=$?; fi
    report 'no sha256sum, shasum present -> verify still hash-checks (rc=0)' 0 "$RC" 'UNVERIFIED-AUTHOR' "$OUT"
    cp "$CHECK" "$d/check.sh"
    if OUT=$(cd "$d" && PATH="$tmp/p-shasum" sh check.sh 2>&1); then RC=0; else RC=$?; fi
    report '...and check.sh too (rc=0)' 0 "$RC" 'OK       ./SKILL.md' "$OUT"
else
    printf 'skip shasum-only leg (no shasum on this host)\n'
fi
d=$(_skill nohash)
_path "$tmp/p-nohash" sh diff mktemp grep awk cat sed cut find sort rm cp mkdir cmp head dirname tr
if OUT=$(PATH="$tmp/p-nohash" sh "$SIGN" verify "$d" 2>&1); then RC=0; else RC=$?; fi
report 'neither sha256 tool -> a plain refusal naming both (rc=1)' 1 "$RC" 'install sha256sum (GNU coreutils) or shasum (Perl)' "$OUT"
cp "$CHECK" "$d/check.sh"
if OUT=$(cd "$d" && PATH="$tmp/p-nohash" sh check.sh 2>&1); then RC=0; else RC=$?; fi
report '...check.sh too (rc=1)' 1 "$RC" 'install sha256sum (GNU coreutils) or shasum (Perl)' "$OUT"

# ---- bundle fixtures (B1, B3): need zip + unzip ------------------------
if command -v zip >/dev/null 2>&1 && command -v unzip >/dev/null 2>&1; then
    bout="$tmp/bundles"; mkdir -p "$bout"
    # a symlink to an outside file (holding a planted token-shaped line) is refused
    printf 'GH=%s_%s\n' ghp aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5bC > "$tmp/outside.txt"
    d=$(_skill linky); ln -s "$tmp/outside.txt" "$d/notes.md"
    PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
    if OUT=$(cd "$bout" && SB1RN= SKILL_SIGN_ACCEPT_SECRET='tests.sh fixture' sh "$SIGN" bundle "$d" 2>&1); then RC=0; else RC=$?; fi
    report 'bundle: a symlink in the skill is refused (rc=1)' 1 "$RC" 'symlink in skill -- refusing (zip would ship its target)' "$OUT"
    [ ! -e "$bout/linky.skill" ] && report '...and no .skill is written' 0 0 '' '' \
        || report '...and no .skill is written' 0 1 '' "$(ls -l "$bout")"
    # .git/ .arc/ __pycache__/ never travel
    d=$(_skill pruned); mkdir -p "$d/.git" "$d/.arc/2026-09" "$d/sub/__pycache__"
    cp "$tmp/outside.txt" "$d/.git/config"; printf 'old\n' > "$d/.arc/2026-09/x"; printf 'pyc\n' > "$d/sub/__pycache__/m.pyc"
    PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
    if OUT=$(cd "$bout" && SB1RN= SKILL_SIGN_ACCEPT_SECRET='tests.sh fixture' sh "$SIGN" bundle "$d" 2>&1); then RC=0; else RC=$?; fi
    L=$(unzip -Z1 "$bout/pruned.skill" 2>&1 || true)
    report 'bundle: a skill with .git/ .arc/ __pycache__/ still bundles (rc=0)' 0 "$RC" 'pruned.skill: bundled' "$OUT"
    report_not '...with no .git/ in the zip' '/.git/' "$L"
    report_not '...no .arc/' '/.arc/' "$L"
    report_not '...no __pycache__/' '__pycache__' "$L"
    # no secrets checker: refused unless passed on the record, and the record lands beside the bundle
    d=$(_skill nochecker); PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
    if OUT=$(cd "$bout" && SB1RN= SKILL_SIGN_ACCEPT_SECRET= sh "$SIGN" bundle "$d" 2>&1); then RC=0; else RC=$?; fi
    report 'bundle: no secrets checker -> refused (rc=1)' 1 "$RC" 'secrets NOT checked, so not bundled' "$OUT"
    if OUT=$(cd "$bout" && SB1RN= SKILL_SIGN_ACCEPT_SECRET='no C4 on this host' sh "$SIGN" bundle "$d" 2>&1); then RC=0; else RC=$?; fi
    R=$(cat "$bout/nochecker.skill.SECRETS-ACCEPTED" 2>/dev/null || true)
    report '...with SKILL_SIGN_ACCEPT_SECRET: bundles (rc=0)' 0 "$RC" 'nochecker.skill: bundled' "$OUT"
    report '...and the reason is written beside the bundle' 0 0 'secrets NOT checked (no sb1rn found), by the keeper'"'"'s choice: no C4 on this host' "$R"
    # a garden with no C4: the checker vendored in the garden's own bin/ is found and run
    if [ -f /f/claude/c4/bin/sb1rn ]; then
        printf 'skip garden-bin leg (/f/claude/c4 on this host would be found first)\n'
    else
        g="$tmp/garden"; mkdir -p "$g/skills/skill-sign/scripts" "$g/bin"
        cp "$here"/skill-sign.sh "$here"/check.sh "$here"/SAYS-SO "$here"/skill-lint.sh "$g/skills/skill-sign/scripts/" 2>/dev/null || true
        printf '#!/bin/sh\n: > "%s/ran"\necho "HIT %%s:1 planted-kind" "$1"\nexit 1\n' "$tmp" > "$g/bin/sb1rn"
        d=$(_skill gardened); PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
        if OUT=$(cd "$bout" && unset SB1RN && HOME="$tmp/nohome" C4_ROOT= sh "$g/skills/skill-sign/scripts/skill-sign.sh" bundle "$d" 2>&1); then RC=0; else RC=$?; fi
        [ -f "$tmp/ran" ] && ran=yes || ran=no
        report 'bundle, no C4: the garden bin/sb1rn is found and its hit stops the bundle (rc=1)' 1 "$RC" 'secret-shaped text would travel' "$OUT ran=$ran"
        report '...it really ran' 0 0 'ran=yes' "ran=$ran"
    fi
else
    printf 'skip bundle legs (zip/unzip not on PATH)\n'
fi

# ---- fixture: check.sh (tier-1 companion) agrees, cold ---------------
d=$(_skill checksh)
PUB_SIGN_KEY="$KEYID" sh "$SIGN" sign -f "$d" >/dev/null 2>&1
cp "$CHECK" "$d/check.sh"
if OUT=$(cd "$d" && sh check.sh 2>&1); then RC=0; else RC=$?; fi
report 'check.sh on a clean signed skill (rc=0)' 0 "$RC" 'OK       ./SKILL.md' "$OUT"

printf '\n%d passed, %d failed\n' "$pass" "$fail"

if [ "$prove_red" = 1 ]; then
    if [ "$fail" -ge 1 ]; then
        printf 'PASS: tests.sh correctly went red under a planted bad expectation\n'
        exit 0
    fi
    printf 'FAIL: tests.sh did NOT go red under a planted bad expectation (rc=99 for no-manifest)\n' >&2
    exit 1
fi

[ "$fail" -eq 0 ]
