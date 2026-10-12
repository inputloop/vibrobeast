#!/bin/sh
# skill-sign.sh --- sign and verify skills with durable PGP provenance.
# Companion to sign.sh; augments it for skill directories and bundles.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program comes with ABSOLUTELY NO WARRANTY; see the GNU GPL v3
# or later <https://www.gnu.org/licenses/> for details.
#
# Lineage: Haiku's draft (2026-07-03, FreshLocalGossip), adopted with
# fixes per QA-7 (2026-07-04): the WHOLE tree is signed via manifest
# (not SKILL.md alone), verify pins the key (not "any key I know"),
# bundles actually carry the signature (dotfiles), temps live outside
# the tree (the sedx44W4d lesson).
#
# usage:
#   skill-sign.sh sign SKILL_DIR...    write .skill-manifest (sha256 per
#                                      file) + .signature.asc over it
#   skill-sign.sh verify SKILL_DIR...  rebuild manifest, compare, verify —
#                                      TIERED, see below
#   skill-sign.sh bundle SKILL_DIR...  create <name>.skill (zip) with
#                                      manifest + signature + check.sh +
#                                      SAYS-SO included
#   skill-sign.sh unbundle FILE.skill  extract (zip-slip guarded)
#   skill-sign.sh show-sig SKILL_DIR   print the embedded signature
#   skill-sign.sh manifest SKILL_DIR.. the EXPRESS manifest (2026-09-24): write
#                                      .skill-manifest only, no key needed; a
#                                      .signature.asc the new manifest would
#                                      orphan is moved to .arc/<YYYY-MM>/ and
#                                      said aloud, so verify reads TIER 1
#                                      (UNVERIFIED-AUTHOR), never BAD. .arc/ is
#                                      outside the manifest (history, not the
#                                      skill; the mint prunes it too). The
#                                      tool that sweeps a skill calls this.
#
# Key selection: $PUB_SIGN_KEY overrides the default (same as sign.sh).
#
# The signature covers a manifest of EVERY file in the skill (SKILL.md
# canonicalized: LF, no trailing whitespace; other files as raw bytes).
# "Signature valid" therefore means: no file in this skill — including
# scripts — changed since Corwin signed it.
#
# verify is TIERED (2026-09-04) — gpg is required only when a signature is
# actually being checked, never just to hash-check bytes:
#   .skill-manifest missing         -> unsigned, cannot even hash-check
#   .skill-manifest present, no     -> TIER 1: sha256sum only, no gpg.
#     .signature.asc                   Files match what the manifest says.
#                                       Prints UNVERIFIED-AUTHOR and exits
#                                       0 — a real floor, not a failure.
#   both present                    -> TIER 2: the pinned-fingerprint
#                                       check above, unchanged.
# check.sh (beside this script) is the standalone, no-gpg tier-1 checker
# that rides inside every bundle — see its own header for details.
#
# HARDENING (2026-09-27, audit B1 N1 B6 N11 B9 B3):
#   * bundle refuses a skill holding any symlink (zip would ship its
#     target), leaves out .git/ .arc/ __pycache__/ (what the manifest
#     prunes), and stores links as links (zip -y) as a second fence.
#   * The check.sh + SAYS-SO a bundle adds at the skill root are HELPERS,
#     added after signing, so the signature does not cover them. verify
#     leaves them out of the tree it compares when the manifest does not
#     list them, and reports each one on its own line against the copy
#     beside this script: same bytes is said; different bytes fail
#     (rc=1, "do not run it"). A skill's OWN check.sh, listed in its
#     manifest, is covered like any other file.
#   * sign's "nothing to do" is decided by content alone (the manifest the
#     files would make equals the signed one, and the signature verifies);
#     an mtime never decides it.
#   * verify says "key not in keyring" (and how to import it) when the
#     pinned key is absent, instead of SIGNATURE FAILED.
#   * sha256sum, else shasum -a 256, else a plain refusal.
#   * bundle stops when no secrets checker is found, like a hit: pass it
#     on the record with SKILL_SIGN_ACCEPT_SECRET='why'. SB1RN=PATH names
#     the checker outright (set but not a file = none found).

set -eu

KEY="${PUB_SIGN_KEY:-ECE77CF417C76C1ACFCE7C2B5B6135511580F007}"
MAN='.skill-manifest'
SIG='.signature.asc'

die() { printf 'skill-sign.sh: %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "$1 not found on PATH"; }

# sha256 of a file ($1) or of stdin, hex only. sha256sum (GNU), else shasum -a 256 (Perl; macOS, BSD).
if command -v sha256sum >/dev/null 2>&1; then SHA256='sha256sum'
elif command -v shasum >/dev/null 2>&1; then SHA256='shasum -a 256'
else SHA256=''; fi
need_sha256() { [ -n "$SHA256" ] || die 'no sha256 tool on PATH: install sha256sum (GNU coreutils) or shasum (Perl)'; }
hash256() { $SHA256 "$@" | cut -d' ' -f1; }

# Fingerprint in groups of four, the way a key page prints it.
fpr_spaced() { printf '%s' "$1" | sed 's/..../& /g; s/ $//'; }

canonical_skill_content() {
    # SKILL.md canonical form: LF endings, no trailing ws/blank lines.
    awk '{ sub(/\r$/, ""); sub(/[ \t]+$/, ""); a[NR] = $0 }
         END { n = NR; while (n > 0 && a[n] == "") n--
               for (i = 1; i <= n; i++) print a[i] }' "$1"
}

skill_name_from_dir() {
    grep '^name:' "$1/SKILL.md" 2>/dev/null | head -1 \
      | sed 's/^name:[ \t]*//' | tr -d '"'"'"
}

build_manifest() { # $1 = skill dir; $2 = root-level names to leave out (verify's helpers); text on stdout
    # Prunes .arc (the mirror-tree archive), .git and __pycache__ -- the same
    # three names polygram/dist.py's _JUNK_DIRS skips, kept in step by hand
    # across the python/shell boundary (tests/arc-never-ships.pl checks both).
    skip=" ${2:-} "
    ( CDPATH= cd -- "$1" &&
      find . \( -name .arc -o -name .git -o -name __pycache__ \) -prune -o \
             -type f ! -name "$MAN" ! -name "$SIG" -print \
        | LC_ALL=C sort \
        | while IFS= read -r p; do
            case $skip in *" ${p#./} "*) continue ;; esac
            if [ "$p" = "./SKILL.md" ]; then
                h=$(canonical_skill_content SKILL.md | hash256)
            else
                h=$(hash256 "$p")
            fi
            printf '%s  %s\n' "$h" "$p"
          done )
}

verify_pinned() { # $1 = sig, $2 = signed file; true iff VALIDSIG on $KEY
    gpg --batch --status-fd 1 --verify "$1" "$2" 2>/dev/null \
      | grep -q "^\[GNUPG:\] VALIDSIG .* $KEY\$"
}

cmd_sign() {
    # -f lowers the loadability gate. Say so out loud; a silent override is
    # how a gate becomes decoration.
    force=
    if [ "${1:-}" = '-f' ]; then force=1; shift; fi
    [ $# -ge 1 ] || die 'sign: need at least one SKILL_DIR'
    need gpg; need_sha256
    # WHO HEARS ABOUT A NO-OP (Corwin, 2026-09-26): naming ONE skill is a strong signal the caller
    # wants to hear back even when no work was done; a sweep over many should stay quiet about
    # no-ops unless the shop is gauged to want it (SKILL_SIGN_VERBOSE=1), and end with one count.
    many=0; [ $# -gt 1 ] && many=1
    [ "${SKILL_SIGN_VERBOSE:-0}" = 1 ] && many=0
    current=0
    for skilldir in "$@"; do
        [ -d "$skilldir" ] || die "$skilldir: not a directory"
        [ -f "$skilldir/SKILL.md" ] || die "$skilldir: no SKILL.md found"

        # LOADABILITY GATE (2026-07-13) — fail-closed before the key is used.
        # A signature is a promise that the artifact works; an over-length or
        # malformed description never loads, so signing it would mint durable
        # provenance for a skill that can never fire. No lint pass, no signature.
        lint="$(dirname "$0")/skill-lint.sh"
        if [ -x "$lint" ] || [ -f "$lint" ]; then
            if ! sh "$lint" -q "$skilldir"; then
                if [ -n "$force" ]; then
                    printf '%s: NOTE lint failed — signing anyway under -f (keeper override)\n' \
                        "$skilldir" >&2
                else
                    die "$skilldir: lint failed — not signed.
  Fix the finding above, or sign with -f to override (and say why in the commit).
  Rationale: a skill that cannot be loaded cannot be found; signing it would
  promise a stranger that a dead artifact works."
                fi
            fi
        else
            printf '%s: WARNING skill-lint.sh not found beside skill-sign.sh — signing UNLINTED\n' \
                "$skilldir" >&2
        fi

        # THE KEEPER'S PEN (2026-09-24, C4 t/TAXONOMY/seam/document/signed): a skill already
        # signed by ANOTHER key is another keeper's; re-signing it with ours would put our name
        # over their work. Refuse unless -f (and then say so). Own key, or no signature: proceed.
        if [ -f "$skilldir/$SIG" ]; then
            issuer=$(gpg --list-packets "$skilldir/$SIG" 2>/dev/null | sed -n 's/.*keyid \([0-9A-F]*\).*/\1/p' | head -1)
            case "$KEY" in
                *"$issuer") ;;
                *) if [ -n "$force" ]; then
                       printf '%s: NOTE existing signature is by %s, not %s -- re-signing anyway under -f\n' "$skilldir" "$issuer" "$KEY" >&2
                   else
                       printf '%s: SKIPPED -- signed by another keeper (%s); the pen is theirs. -f overrides.\n' "$skilldir" "${issuer:-unknown key}"
                       continue
                   fi ;;
            esac
        fi
        # NOTHING TO SIGN (Corwin, 2026-09-26): "avoid resign when the signature is the newest
        # asset; changes to the signable package implicitly must already have occurred." Our own
        # signature that verifies AND covers exactly these bytes is left alone: no key, no prompt.
        # 2026-09-27 (audit B6): decided by CONTENT only. It used to take "the signature is newer
        # than every file" as enough, and tar, unzip and cp -p all set old mtimes on new bytes --
        # sign said current while verify said TREE CHANGED. The mtime now only picks the wording.
        if [ -z "$force" ] && [ -f "$skilldir/$SIG" ] && [ -f "$skilldir/$MAN" ] \
           && verify_pinned "$skilldir/$SIG" "$skilldir/$MAN" \
           && build_manifest "$skilldir" | cmp -s - "$skilldir/$MAN"; then
            newer=$( cd "$skilldir" && find . \( -name .arc -o -name .git -o -name __pycache__ \) -prune -o \
                       -type f ! -name "$MAN" ! -name "$SIG" -newer "$SIG" -print | head -1 )
            if [ -z "$newer" ]; then why='the signature is newer than every file it covers, and they are the bytes it signed'
            else why='the files are the bytes it signed (touched, not edited)'
            fi
            current=$((current + 1))
            [ "$many" = 1 ] || printf '%s: already signed and current -- %s; nothing to do\n' "$skilldir" "$why"
            continue
        fi
        tmp=$(mktemp -d) || die 'mktemp failed'
        trap 'rm -rf "$tmp"' EXIT
        build_manifest "$skilldir" > "$tmp/manifest" \
          || die "$skilldir: manifest build failed"
        gpg --yes --batch --armor --local-user "$KEY" \
            --detach-sign --output "$tmp/sig" "$tmp/manifest" \
          || die "$skilldir: gpg sign failed"
        verify_pinned "$tmp/sig" "$tmp/manifest" \
          || die "$skilldir: post-sign pinned verify failed"
        cp "$tmp/manifest" "$skilldir/$MAN"
        cp "$tmp/sig" "$skilldir/$SIG"
        rm -rf "$tmp"; trap - EXIT
        n=$(grep -c . "$skilldir/$MAN")
        printf '%s: signed — %s files in manifest (%s)\n' "$skilldir" "$n" "$KEY"
    done
    [ "$many" = 1 ] && [ "$current" -gt 0 ] && printf 'skill-sign.sh: %d already signed and current; nothing to do for them\n' "$current"
    return 0
}

cmd_manifest() {
    # The express manifest: the honest state after an edit, written by the
    # tool that edited (ns2hw --write calls this for every skill it touched).
    # No lint gate here -- a manifest is a byte record, not a promise that the
    # skill works; the promise is the signature, and that still gates on lint.
    [ $# -ge 1 ] || die 'manifest: need at least one SKILL_DIR'
    need_sha256
    for skilldir in "$@"; do
        [ -d "$skilldir" ] || die "$skilldir: not a directory"
        [ -f "$skilldir/SKILL.md" ] || die "$skilldir: no SKILL.md found"
        tmp=$(mktemp -d) || die 'mktemp failed'
        build_manifest "$skilldir" > "$tmp/manifest" || { rm -rf "$tmp"; die "$skilldir: manifest build failed"; }
        if [ -f "$skilldir/$MAN" ] && cmp -s "$tmp/manifest" "$skilldir/$MAN"; then
            rm -rf "$tmp"; printf '%s: manifest unchanged\n' "$skilldir"; continue
        fi
        if [ -f "$skilldir/$SIG" ]; then
            arc="$skilldir/.arc/$(date -u +%Y-%m)"; mkdir -p "$arc"
            stamp=$(date -u +%Y-%m-%d_%H%M%SZ)
            mv "$skilldir/$SIG" "$arc/signature-${stamp}_pre-manifest.asc"
            [ -f "$skilldir/$MAN" ] && cp "$skilldir/$MAN" "$arc/skill-manifest-${stamp}_pre-manifest"
            printf '%s: NOTE the old signature would not cover the new manifest -- moved to %s (re-sign to restore tier 2)\n' \
                "$skilldir" "$arc/signature-${stamp}_pre-manifest.asc" >&2
            # .arc/ is pruned by build_manifest (2026-09-24, with dist.py's _JUNK_DIRS): the
            # archive is the skill's history, not the skill, so the manifest above already stands.
        fi
        cp "$tmp/manifest" "$skilldir/$MAN"; rm -rf "$tmp"
        n=$(grep -c . "$skilldir/$MAN")
        printf '%s: manifest written -- %s files (unsigned: verify reads UNVERIFIED-AUTHOR until a key signs it)\n' "$skilldir" "$n"
    done
}

cmd_verify() {
    # TIERED (2026-09-04): gpg is only ever required for tier 2, and only
    # for the skill(s) that actually reach it — never up front. A stranger
    # with no gpg on PATH can still run tier 1 on every skill below.
    [ $# -ge 1 ] || die 'verify: need at least one SKILL_DIR'
    need_sha256
    tmpldir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    rc=0
    for skilldir in "$@"; do
        [ -d "$skilldir" ] || die "$skilldir: not a directory"

        if [ ! -f "$skilldir/$MAN" ]; then
            printf '%s: unsigned (no %s — cannot even hash-check)\n' \
                "$skilldir" "$MAN" >&2
            rc=1; continue
        fi

        # HELPERS (2026-09-27, audit N1): bundle adds check.sh + SAYS-SO at the root AFTER the
        # signature, so they are not in it. A root helper the manifest does not list is left out of
        # the compared tree and judged below against the copy beside this script. Listed = covered.
        helpers=''
        for hf in check.sh SAYS-SO; do
            [ -f "$skilldir/$hf" ] || continue
            awk -v p="./$hf" 'substr($0, 67) == p { f = 1 } END { exit !f }' "$skilldir/$MAN" && continue
            helpers="$helpers $hf"
        done

        tmp=$(mktemp -d) || die 'mktemp failed'
        trap 'rm -rf "$tmp"' EXIT
        build_manifest "$skilldir" "$helpers" > "$tmp/manifest"

        if ! diff -q "$tmp/manifest" "$skilldir/$MAN" >/dev/null 2>&1; then
            printf '%s: TREE CHANGED since manifest was written — files differ:\n' \
                "$skilldir" >&2
            diff "$skilldir/$MAN" "$tmp/manifest" >&2 || true
            rc=1
            rm -rf "$tmp"; trap - EXIT
            continue
        fi

        for hf in $helpers; do
            if [ ! -f "$tmpldir/$hf" ]; then
                printf '%s: helper (not covered by the signature): %s -- no copy beside this verifier to compare; do not trust it\n' \
                    "$skilldir" "$hf" >&2
            elif cmp -s "$tmpldir/$hf" "$skilldir/$hf"; then
                printf '%s: helper (not covered by the signature): %s -- same bytes as the copy beside this verifier\n' \
                    "$skilldir" "$hf"
            else
                printf '%s: helper (not covered by the signature): %s -- DIFFERS from the copy beside this verifier (%s); do not run it. Remove it to verify the skill alone, or re-bundle.\n' \
                    "$skilldir" "$hf" "$tmpldir/$hf" >&2
                rc=1
            fi
        done

        if [ ! -f "$skilldir/$SIG" ]; then
            # TIER 1: bytes match the manifest. Nobody's signature backs
            # WHO wrote that manifest — say so plainly, and exit clean:
            # a hash-only match is a real, weaker floor, not a failure.
            printf '%s: UNVERIFIED-AUTHOR — files match %s, no %s present (hash-only, no gpg used)\n' \
                "$skilldir" "$MAN" "$SIG"
            rm -rf "$tmp"; trap - EXIT
            continue
        fi

        # TIER 2: manifest matches AND a signature claims it — gpg earns
        # its keep here, and only here.
        need gpg
        if verify_pinned "$skilldir/$SIG" "$skilldir/$MAN"; then
            printf '%s: signature valid (pinned %s)\n' "$skilldir" "$KEY"
        elif ! gpg --batch --list-keys "$KEY" >/dev/null 2>&1; then
            # 2026-09-27 (audit N11): an absent key is not a failed signature; say which, and how.
            if [ "$KEY" = ECE77CF417C76C1ACFCE7C2B5B6135511580F007 ]; then
                printf '%s: key not in keyring: import skills/%s.asc (fingerprint %s)\n' \
                    "$skilldir" "$KEY" "$(fpr_spaced "$KEY")" >&2
            else
                printf '%s: key not in keyring: import the public key for %s (fingerprint %s), or unset PUB_SIGN_KEY\n' \
                    "$skilldir" "$KEY" "$(fpr_spaced "$KEY")" >&2
            fi
            rc=1
        else
            printf '%s: SIGNATURE FAILED against pinned key %s (the key is in your keyring: this signature is not its, or the manifest changed after signing)\n' "$skilldir" "$KEY" >&2
            rc=1
        fi
        rm -rf "$tmp"; trap - EXIT
    done
    exit $rc
}

cmd_bundle() {
    [ $# -ge 1 ] || die 'bundle: need at least one SKILL_DIR'
    need zip
    tmpldir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    for skilldir in "$@"; do
        [ -d "$skilldir" ] || die "$skilldir: not a directory"
        [ -f "$skilldir/$SIG" ] || die "$skilldir: unsigned (run: skill-sign.sh sign)"
        skillname=$(skill_name_from_dir "$skilldir")
        [ -n "$skillname" ] || die "$skilldir: skill name empty"
        case $skillname in
            */*|*..*|.*) die "$skilldir: unsafe skill name: $skillname" ;;
        esac
        # 2026-09-27 (audit B1): a symlink is refused, not followed. The secrets scan skips links and
        # zip -r follows them, so a link to an outside file shipped its target unscanned.
        lk=$( CDPATH= cd -- "$skilldir" && find . \( -name .arc -o -name .git -o -name __pycache__ \) -prune -o -type l -print | head -1 )
        [ -z "$lk" ] || die "$skilldir: symlink in skill -- refusing (zip would ship its target): $lk"
        tmp=$(mktemp -d) || die 'mktemp failed'
        trap 'rm -rf "$tmp"' EXIT
        mkdir -p "$tmp/$skillname"
        cp -r "$skilldir/." "$tmp/$skillname/" \
          || die "$skilldir: staging copy failed"      # "/." carries dotfiles
        [ -f "$tmp/$skillname/$SIG" ] || die "$skilldir: signature failed to stage"
        # What the manifest prunes never travels: .git/ (config can hold tokens; the scan prunes it
        # too), .arc/ (history), __pycache__/ -- the same three names as build_manifest and dist.py.
        find "$tmp/$skillname" \( -name .arc -o -name .git -o -name __pycache__ \) -prune -exec rm -rf {} +
        lk=$( find "$tmp/$skillname" -type l -print | head -1 )
        [ -z "$lk" ] || die "$skilldir: symlink in skill -- refusing (zip would ship its target): ${lk#"$tmp/"}"
        # Bundle template: check.sh + SAYS-SO ride along so a stranger with
        # no gpg can still hash-check the bytes (tier 1). Never clobber a
        # skill that already ships its own file of either name.
        for tf in check.sh SAYS-SO; do
            if [ -f "$tmpldir/$tf" ] && [ ! -e "$tmp/$skillname/$tf" ]; then
                cp "$tmpldir/$tf" "$tmp/$skillname/$tf"
            fi
        done
        # Secrets at this boundary (Corwin 2026-09-26): a bundle travels, so what is in it is scanned
        # first with C4's sb1rn when it is on this host. It prints file, line and kind, never the secret.
        # Where: SB1RN names it outright (set, not a file = none); else C4, then this garden's own
        # bin/ (skills/skill-sign/scripts -> ../../../bin), where sb1aw/sb1pl/sb1rn get vendored.
        sbrn=''
        if [ -n "${SB1RN+x}" ]; then
            [ -f "$SB1RN" ] && sbrn=$SB1RN
        else
            for sbd in "${C4_ROOT:+$C4_ROOT/bin}" /f/claude/c4/bin "$HOME/mnt/c4/bin" "$tmpldir/../../../bin"; do
                [ -n "$sbd" ] && [ -f "$sbd/sb1rn" ] && { sbrn=$sbd/sb1rn; break; }
            done
        fi
        # 2026-09-27 (audit B3): no checker is treated like a hit -- a bundle travels, and in a
        # garden with no C4 the gate was open. Stops here unless passed on the record.
        if [ -z "$sbrn" ]; then
            printf '%s: no secrets checker found (sb1rn: $SB1RN, C4_ROOT, /f/claude/c4, ~/mnt/c4, the garden bin/)\n' "$skillname" >&2
            [ -n "${SKILL_SIGN_ACCEPT_SECRET:-}" ] \
              || die "$skilldir: secrets NOT checked, so not bundled. Put sb1rn where it is looked for (or SB1RN=path), or pass it on the record: SKILL_SIGN_ACCEPT_SECRET='why'"
            printf 'Bundled with secrets NOT checked (no sb1rn found), by the keeper'"'"'s choice: %s\n' \
                "$SKILL_SIGN_ACCEPT_SECRET" > "$tmp/SECRETS-ACCEPTED"
            printf '%s: secrets NOT checked, accepted on the record (%s.skill.SECRETS-ACCEPTED beside the bundle)\n' "$skillname" "$skillname" >&2
        fi
        if [ -n "$sbrn" ]; then
            # Always runs, always reported; passable by the keeper on the record: SKILL_SIGN_ACCEPT_SECRET=WHY
            # writes the reason and the hits BESIDE the bundle as <name>.skill.SECRETS-ACCEPTED -- beside, not
            # inside, so the signed manifest still covers exactly what was signed (honest-boundaries design).
            if ! sbo=$( CDPATH= cd -- "$tmp" && sh "$sbrn" "$skillname" 2>/dev/null ); then
                printf '%s\n' "$sbo" >&2
                [ -n "${SKILL_SIGN_ACCEPT_SECRET:-}" ] \
                  || die "$skilldir: secret-shaped text would travel in $skillname.skill (above); fix it, mark a documentation line sb:allow, or pass it on the record: SKILL_SIGN_ACCEPT_SECRET='why'"
                { printf 'Bundled with secret-shaped text, by the keeper'"'"'s choice: %s\n' "$SKILL_SIGN_ACCEPT_SECRET"
                  printf '%s\n' "$sbo" | grep '^HIT '; } > "$tmp/SECRETS-ACCEPTED"
                printf '%s: secret-shaped text accepted on the record (%s.skill.SECRETS-ACCEPTED beside the bundle)\n' "$skillname" "$skillname" >&2
            fi
        fi
        ( CDPATH= cd -- "$tmp" && zip -r -y "$skillname.skill" "$skillname/" >/dev/null ) \
          || die "failed to create $skillname.skill"
        mv "$tmp/$skillname.skill" "./$skillname.skill"
        [ -f "$tmp/SECRETS-ACCEPTED" ] && mv "$tmp/SECRETS-ACCEPTED" "./$skillname.skill.SECRETS-ACCEPTED"
        rm -rf "$tmp"; trap - EXIT
        printf '%s.skill: bundled (manifest + signature + check.sh + SAYS-SO included)\n' "$skillname"
    done
}

cmd_unbundle() {
    [ $# -eq 1 ] || die 'unbundle: exactly one FILE.skill'
    bundle=$1
    [ -f "$bundle" ] || die "$bundle: not found"
    need unzip
    # zip-slip guard: refuse absolute or parent-escaping entries
    unzip -Z1 "$bundle" 2>/dev/null | grep -Eq '^/|(^|/)\.\.(/|$)' \
      && die "$bundle: unsafe paths in archive — refusing"
    skillname=$(unzip -Z1 "$bundle" 2>/dev/null | head -1 | cut -d/ -f1)
    [ -n "$skillname" ] || die "$bundle: could not infer skill name"
    [ ! -e "$skillname" ] || die "$skillname: already exists (remove it first)"
    unzip -q "$bundle" || die "$bundle: unzip failed"
    printf '%s/: extracted from %s — now run: skill-sign.sh verify %s/ (the check.sh + SAYS-SO a bundle adds are reported apart: not signed)\n' \
      "$skillname" "$bundle" "$skillname"
}

cmd_show_sig() {
    [ $# -eq 1 ] || die 'show-sig: exactly one SKILL_DIR'
    [ -f "$1/$SIG" ] || die "$1: no $SIG"
    cat "$1/$SIG"
}

case "${1:-help}" in
    sign)     shift; cmd_sign "$@" ;;
    verify)   shift; cmd_verify "$@" ;;
    bundle)   shift; cmd_bundle "$@" ;;
    unbundle) shift; cmd_unbundle "$@" ;;
    show-sig) shift; cmd_show_sig "$@" ;;
    manifest) shift; cmd_manifest "$@" ;;
    help|--help|-h) sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//' ;;
    *) die "unknown command: $1 (try: skill-sign.sh help)" ;;
esac
