#!/bin/sh
# check.sh -- verify this plugin's bytes against its MANIFEST.
# No gpg, no network, no python: sha256sum and awk. GPL-3.0-or-later.
#
# Three defects an adversarial read found in earlier versions, all fixed:
#
#  * It wrote /tmp/.vb_e.$$ -- a guessable name another user can pre-create as
#    a symlink, so running the check overwrote whatever that link pointed at
#    (CWE-377). There are no temp files now.
#  * Its skip patterns were unanchored, so `servers/check.sh` and
#    `servers/MANIFEST` were invisible to the unlisted-file pass. They are
#    anchored to the plugin root now.
#  * `find . -type f` skipped SYMLINKS, so a *.py symlink planted under
#    servers/ -- which is on PYTHONPATH -- was in no MANIFEST line and in no
#    find line, and therefore invisible to both passes. `store.strays()` was
#    given exactly this fix; this was not.
#  * It split MANIFEST lines on single spaces, so any path containing a space
#    was truncated and reported MISSING. The digest is a fixed 64 hex
#    characters followed by exactly two spaces, so the path is simply
#    everything from column 67 -- no splitting at all.
#
# __pycache__ is NOT skipped. `.mcp.json` sets PYTHONDONTWRITEBYTECODE=1, so
# this plugin should never contain any; anything there was put there by
# something else, and it is the one directory python executes without being
# asked. A planted .pyc runs arbitrary code on import.
set -eu
cd "$(dirname "$0")"
[ -f MANIFEST ] || { echo "no MANIFEST beside check.sh"; exit 2; }
if command -v sha256sum >/dev/null 2>&1; then H() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then H() { shasum -a 256 "$1" | cut -d' ' -f1; }
else echo "need sha256sum or shasum"; exit 2; fi

bad=0; n=0
while IFS= read -r line; do
  [ -n "$line" ] || continue
  want=$(printf '%s' "$line" | cut -c1-64)
  path=$(printf '%s' "$line" | cut -c67-)
  [ -n "$path" ] || continue
  n=$((n+1))
  if [ ! -f "$path" ]; then printf 'MISSING  %s\n' "$path"; bad=$((bad+1)); continue; fi
  got=$(H "$path")
  [ "$got" = "$want" ] || { printf 'CHANGED  %s\n' "$path"; bad=$((bad+1)); }
done < MANIFEST

# Unlisted files, compared in awk so no field-splitting touches a path, and
# with the two skips ANCHORED to the plugin root.
unlisted=$(
  find . \( -type f -o -type l \) ! -path './MANIFEST' ! -path './check.sh' \
  | awk 'NR==FNR { if (length($0) > 66) listed[substr($0, 67)] = 1; next }
         { if (!($0 in listed)) print $0 }' MANIFEST -
) || { echo 'FAULT  could not enumerate files'; exit 1; }

if [ -n "$unlisted" ]; then
  printf 'UNLISTED\n%s\n' "$unlisted"
  if printf '%s' "$unlisted" | grep -q '__pycache__\|\.pyc$'; then
    printf '\nSome of those are python bytecode. This plugin sets\n'
    printf 'PYTHONDONTWRITEBYTECODE=1, so it should never write any, and\n'
    printf '__pycache__ is the one directory python executes without being\n'
    printf 'asked. Treat a .pyc you did not put there as hostile.\n'
  fi
  bad=$((bad + 1))
fi

if [ "$bad" -eq 0 ]; then
  printf 'OK  %s file(s) match MANIFEST\n' "$n"
  printf 'This proves the bytes are the ones that were minted. It does NOT\n'
  printf 'prove who minted them -- that needs a signature against a pinned key.\n'
else
  printf 'FAULT  %s problem(s) across %s listed file(s)\n' "$bad" "$n"; exit 1
fi
