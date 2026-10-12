# sh1lib.sh -- the house shell library: common concerns, written once.
#
# Source it; do not run it:   . "$dir/sh1lib.sh"
# POSIX sh only (tested under dash). No bashisms, no GNU-only flags.
#
# WHY A LIBRARY. Every tool in this garden had re-grown the same five helpers -- die, a hash that
# works on Linux, macOS and msys2, a UTC stamp, a word check, and an atomic write. Each copy drifted
# a little. This file is the one copy; tools source it from here, and a skill that must travel alone
# carries this file beside its scripts (the skill-metrics skill does).
#
# NAMING. Every function starts with sl_ so a sourcing script can see at a glance what came from here.
#
# Copyright 2026 Corwin Brust <corwin@bru.st> -- GPLv3-or-later. Authored by Mentat (for Corwin).
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

SL_PROG=${SL_PROG:-${0##*/}}

sl_die()  { printf '%s: %s\n' "$SL_PROG" "$*" >&2; exit 2; }
sl_warn() { printf '%s: %s\n' "$SL_PROG" "$*" >&2; }
sl_have() { command -v "$1" >/dev/null 2>&1; }

# sl_hash FILE -> full sha256 hex on stdout. Tries sha256sum, shasum, openssl, in that order.
sl_hash() {
  [ -f "$1" ] || { sl_warn "cannot hash (not a file): $1"; return 1; }
  if sl_have sha256sum; then sha256sum < "$1" | cut -d' ' -f1
  elif sl_have shasum; then shasum -a 256 < "$1" | cut -d' ' -f1
  elif sl_have openssl; then openssl dgst -sha256 < "$1" | sed 's/^.*= *//'
  else sl_warn "need sha256sum, shasum or openssl"; return 1
  fi
}

# sl_utc -> 2026-09-23T02:14:19Z
sl_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# sl_epoch -> seconds since 1970 (POSIX date has no %s; awk srand() returns the time it seeded with)
sl_epoch() { awk 'BEGIN { srand(); print srand() }'; }

# sl_match ERE VALUE -> true when the WHOLE value matches. Uses grep -E -x (POSIX), never [[ ]].
# A value containing a newline never matches: fields here are one line by definition.
sl_match() {
  case $2 in *'
'*) return 1 ;; esac
  printf '%s\n' "$2" | grep -E -x -q -e "$1"
}

# sl_write_atomic FILE -> copy stdin to FILE through a sidecar in the same directory, then rename.
# A crash mid-write leaves the old FILE whole, never a truncated one.
sl_write_atomic() {
  _t="$1.tmp.$$"
  cat > "$_t" && mv -f "$_t" "$1" || { rm -f "$_t"; return 1; }
}

# sl_tally NAME -> increment a counter variable by name (for gauges that report OK/FAULT counts).
sl_tally() { eval "$1=\$(( \${$1:-0} + 1 ))"; }

# sl_rel ROOT PATH -> PATH with a leading ROOT/ removed (for printing short, stable paths).
sl_rel() { case $2 in "$1"/*) printf '%s\n' "${2#"$1"/}" ;; *) printf '%s\n' "$2" ;; esac; }
