#!/bin/sh
# check.sh --- hash-only, no-gpg check for a bundled skill.
#
# Companion to skill-sign.sh: same manifest format, same SKILL.md
# canonicalization, deliberately zero non-POSIX dependencies beyond
# sha256sum (or shasum -a 256 where that is what the host has) -- so a
# stranger with no gpg on PATH can still unpack a .skill bundle and see
# whether the bytes match what shipped.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program comes with ABSOLUTELY NO WARRANTY; see the GNU GPL v3
# or later <https://www.gnu.org/licenses/> for details.
#
# usage:
#   sh check.sh [DIR]        check DIR (default: this script's own
#                             directory) against DIR/.skill-manifest.
#                             Prints OK/CHANGED/MISSING per file, then one
#                             64-hex-char line (sha256 of .skill-manifest
#                             itself) to eyeball or compare elsewhere.
#                             Exits 0 iff every entry is OK.
#   sh check.sh --prove-red  self-test: copy this skill to a scratch dir,
#                             flip one byte in a real (manifested) file,
#                             and confirm the checker reports it CHANGED.
#                             Exits non-zero if the checker fails to
#                             notice -- i.e. if the red-proof itself fails.
#                             Run it from a SKILL ROOT (an unpacked bundle,
#                             where .skill-manifest sits beside check.sh).
#                             In skill-sign's own scripts/ there is no
#                             manifest beside it, so it stops and says so.
#
# This is a HASH check only. "OK" means the bytes match what
# .skill-manifest recorded -- it says nothing about who wrote that
# manifest. For authorship, look for .signature.asc beside this script
# and run: skill-sign.sh verify <this dir>  (needs gpg + the pinned key).
# This script and SAYS-SO are added to a bundle AFTER signing: the
# signature does not cover them. verify compares them to its own copy.

set -eu

MAN='.skill-manifest'

die() { printf 'check.sh: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 not found on PATH"; }

# sha256 hex of a file ($1) or stdin: sha256sum, else shasum -a 256, else refuse.
if command -v sha256sum >/dev/null 2>&1; then SHA256='sha256sum'
elif command -v shasum >/dev/null 2>&1; then SHA256='shasum -a 256'
else SHA256=''; fi
hash256() { $SHA256 "$@" | cut -d' ' -f1; }

# Identical to skill-sign.sh's canonical_skill_content: LF endings, no
# trailing whitespace per line, no trailing blank lines. Kept as a literal
# duplicate (not a shared include) on purpose -- this script must stand
# alone inside an unpacked bundle with nothing else from the skill-sign
# tree in scope.
canonical_skill_content() {
    awk '{ sub(/\r$/, ""); sub(/[ \t]+$/, ""); a[NR] = $0 }
         END { n = NR; while (n > 0 && a[n] == "") n--
               for (i = 1; i <= n; i++) print a[i] }' "$1"
}

do_check() { # $1 = skill dir; OK/CHANGED/MISSING lines + summary on stdout
    dir=$1
    man="$dir/$MAN"
    [ -f "$man" ] || die "$dir: no $MAN -- nothing to check against"
    bad=0
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        h=${line%%  *}
        p=${line#*  }
        f="$dir/${p#./}"
        if [ ! -f "$f" ]; then
            printf 'MISSING  %s\n' "$p"
            bad=1
            continue
        fi
        if [ "$p" = "./SKILL.md" ]; then
            actual=$(canonical_skill_content "$f" | hash256)
        else
            actual=$(hash256 "$f")
        fi
        if [ "$actual" = "$h" ]; then
            printf 'OK       %s\n' "$p"
        else
            printf 'CHANGED  %s\n' "$p"
            bad=1
        fi
    done < "$man"
    summary=$(hash256 "$man")
    printf '%s\n' "$summary"
    printf '(sha256 of %s -- eyeball it, or compare against a separately-published copy)\n' "$MAN"
    return $bad
}

prove_red() {
    here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    [ -f "$here/$MAN" ] || die "--prove-red: no $MAN beside check.sh to copy (run it from a skill root, e.g. an unpacked bundle)"
    tmp=$(mktemp -d) || die 'mktemp failed'
    trap 'rm -rf "$tmp"' EXIT
    cp -r "$here/." "$tmp/" || die '--prove-red: staging copy failed'

    # Sanity leg first: the untouched copy must check clean, or the
    # red-proof below means nothing (see prove-red-discipline).
    if ! do_check "$tmp" >/dev/null 2>&1; then
        die '--prove-red: untouched copy already fails -- fix the real check first'
    fi

    # Corrupt the first real file the manifest names (never the manifest
    # itself -- that would just look like MISSING/short-circuit, not a
    # detected content change).
    target=$(grep -v '^$' "$tmp/$MAN" | head -1 | sed -e 's/^[^ ]*  //' -e 's#^\./##')
    [ -n "$target" ] || die '--prove-red: manifest has no entries to corrupt'
    printf 'X' >> "$tmp/$target"

    if do_check "$tmp" >/dev/null 2>&1; then
        printf 'FAIL: check.sh did NOT go red after corrupting %s\n' "$target" >&2
        rm -rf "$tmp"; trap - EXIT
        exit 1
    fi
    printf 'PASS: check.sh correctly reports CHANGED after corrupting %s\n' "$target"
    rm -rf "$tmp"; trap - EXIT
}

[ -n "$SHA256" ] || die 'no sha256 tool on PATH: install sha256sum (GNU coreutils) or shasum (Perl)'

case "${1:-}" in
    --prove-red) prove_red ;;
    -h|--help) sed -n '2,37p' "$0" | sed 's/^# \{0,1\}//' ;;
    *)
        dir=${1:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}
        do_check "$dir"
        ;;
esac
