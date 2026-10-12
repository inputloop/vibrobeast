#!/bin/sh
# skill-lint.sh --- check a skill is LOADABLE before it is signed.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program comes with ABSOLUTELY NO WARRANTY; see the GNU GPL v3
# or later <https://www.gnu.org/licenses/> for details.
#
# Why this exists (2026-07-13): a fold left sandboxer's description at
# 1633 chars, over the 1024-char load limit. The BODY was correct and the
# skill was still useless — an over-length description does not load, so
# the router never sees it, so the skill never fires. A skill that cannot
# be found is a skill that does not exist. Signing it would have minted
# durable provenance for a dead artifact.
#
# The hook is deliberate: SIGN is the gate everything passes through, and
# a signature is a promise that the thing works. So the lint is fail-closed
# at sign time (skill-sign.sh sign runs it; -f overrides, loudly).
#
# usage: skill-lint.sh [-q] SKILL_DIR...
#   -q  quiet: print findings only, no OK lines
# exit: 0 clean · 1 findings · 2 usage
#
# Checks (each names the failure mode it prevents):
#   L1 frontmatter fenced by --- ... ---        (unparsable = never loads)
#   L2 name: present, matches the directory     (router looks up by name)
#   L3 description: present                     (no description = no trigger)
#   L4 description <= 1024 chars                (over = silently not loaded)
#   L6 SKILL.md is not clearsigned              (PGP header breaks the fence)
#   L7 no CRLF line endings                     (frontmatter parse hazard)
#   L8 no NUL bytes                             (a padded/truncated write; candor-gate 2026-09-11 shipped 79)
#
# NOTE on L5, and it is a lesson: the first draft FAILED any description
# that continued onto a second line. That was a FALSE BAD — YAML block
# scalars (>- and |) and plain multi-line scalars are legal and load fine,
# and seven shipped skills use them. A guard that fails good artifacts is
# worse than no guard: it teaches people to pass -f. The check was deleted;
# the parser now ASSEMBLES multi-line descriptions and measures the whole.
# (Caught by running the lint across the tree before hooking it. A guard is
# credited only when a measurement shows it changes behavior — correctly.)

set -eu

LIMIT=1024
quiet=
case "${1:-}" in
    -q) quiet=1; shift ;;
    -h|--help) sed -n '18,32p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) printf 'skill-lint.sh: unknown option: %s\n' "$1" >&2; exit 2 ;;
esac
[ $# -ge 1 ] || { printf 'usage: skill-lint.sh [-q] SKILL_DIR...\n' >&2; exit 2; }

rc=0
say() { [ -n "$quiet" ] || printf '%s\n' "$*"; }
bad() { printf '%s\n' "$*" >&2; rc=1; }

for dir in "$@"; do
    dir=${dir%/}
    md=$dir/SKILL.md
    base=$(basename "$dir")
    [ -f "$md" ] || { bad "$base: FAIL no SKILL.md"; continue; }

    # L8 — NUL bytes: a file-system pad or a torn write. The text before the first NUL may be
    # whole (candor-gate's was: its sentinel line stood before 79 NULs), but a loader may not
    # agree, and a signature over the padded bytes signs the pad.
    n=$(tr -d -c '\000' < "$md" | wc -c | tr -d ' ')
    if [ "${n:-0}" -gt 0 ]; then
        bad "$base: FAIL L8 $n NUL byte(s) in SKILL.md (a padded or torn write; strip them and re-sign)"
        continue
    fi

    # L7 — CRLF (check first: it breaks every check below it)
    if head -c 4096 "$md" | tr -d '\n' | grep -q "$(printf '\r')"; then
        bad "$base: FAIL L7 CRLF line endings (frontmatter will not parse)"
        continue
    fi

    # L6 — clearsigned SKILL.md (the house idiom: detach runnables/parsed files)
    if head -1 "$md" | grep -q 'BEGIN PGP SIGNED MESSAGE'; then
        bad "$base: FAIL L6 SKILL.md is clearsigned — the PGP header breaks the
    YAML fence and gpg dash-escapes '---'. Use a detached .asc instead."
        continue
    fi

    # L1 — frontmatter fence
    if [ "$(head -1 "$md")" != '---' ]; then
        bad "$base: FAIL L1 first line is not '---' (no frontmatter fence)"
        continue
    fi
    close=$(awk 'NR>1 && /^---[[:space:]]*$/ { print NR; exit }' "$md")
    if [ -z "$close" ]; then
        bad "$base: FAIL L1 frontmatter is never closed by '---'"
        continue
    fi

    # L2 — name present and matching the directory
    name=$(awk -v end="$close" 'NR<end && sub(/^name:[[:space:]]*/,"")' "$md" | head -1)
    if [ -z "$name" ]; then
        bad "$base: FAIL L2 no name: in frontmatter"
    elif [ "$name" != "$base" ]; then
        bad "$base: FAIL L2 name: '$name' does not match directory '$base'"
    fi

    # L3/L4 — the description: present, and within the load limit.
    # ASSEMBLE it first: YAML allows the value on one line, or as a block
    # scalar (>- / |) continued on indented lines, or a plain multi-line
    # scalar. All three load; all three must be measured whole.
    desc=$(awk -v end="$close" '
        NR >= end { exit }
        /^description:[[:space:]]*/ {
            v = $0
            sub(/^description:[[:space:]]*/, "", v)
            sub(/^[>|][-+]?[[:space:]]*$/, "", v)   # a bare block indicator
            out = v
            collecting = 1
            next
        }
        collecting {
            if ($0 ~ /^[[:space:]]/ && $0 !~ /^[[:space:]]*$/) {
                line = $0
                sub(/^[[:space:]]+/, "", line)
                out = (out == "" ? line : out " " line)   # folded: joined by a space
                next
            }
            collecting = 0
        }
        END { print out }
    ' "$md")

    if [ -z "$desc" ]; then
        bad "$base: FAIL L3 no description: in frontmatter — the skill cannot trigger"
        continue
    fi

    # L4 — the limit that started all this. Count CHARACTERS, not bytes:
    # em-dashes and curly quotes are multibyte, and the loader counts characters.
    n=$(printf '%s' "$desc" | wc -m | tr -d ' ')
    if [ "$n" -gt "$LIMIT" ]; then
        bad "$base: FAIL L4 description is $n chars (limit $LIMIT) — over by $((n - LIMIT)).
    An over-length description is NOT LOADED: the skill will never fire."
    else
        say "$base: ok — description $n/$LIMIT chars, name matches, frontmatter clean"
    fi
done

exit $rc
