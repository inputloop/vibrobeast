#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# sig-fresh - verify a detached signature from FRESH bytes on a flaky mount.
#
# The stale-reader bug serves old bytes to shell readers on layered mounts;
# a signature check over stale bytes yields a false BAD (MODEL-readers-and-
# mounts, reflex 8: the stale reader slanders good signatures). This tool
# freshens both nodes (the rename dance) BEFORE verifying, so the ceremony
# judges the real disk - and a BAD that survives freshening is worth alarm.
#
# Usage: sig-fresh.sh FILE [SIGFILE]     (SIGFILE defaults to FILE.asc)
# Exit:  0 GOOD - 1 verify failed on fresh bytes - 2 usage/missing input
# Verdict on stdout; advisory notes on stderr. POSIX sh; gpg required.
# Pinning is the caller's keyring discipline: "verifies" means "verifies
# against a key YOU imported on purpose", nothing looser.

f=${1-} ; s=${2-${1-}.asc}
test -n "$f" || { echo "usage: $(basename "$0") FILE [SIGFILE]" >&2 ; exit 2 ; }
test -r "$f" || { echo "sig-fresh: cannot read $f" >&2 ; exit 2 ; }
test -r "$s" || { echo "sig-fresh: no signature at $s" >&2 ; exit 2 ; }
command -v gpg >/dev/null || { echo "sig-fresh: gpg not on PATH" >&2 ; exit 2 ; }

# Freshen both nodes: same-directory rename away and back forces the
# bridge to re-resolve. Cheap, atomic, preserves the inode's content view.
for p in "$f" "$s" ; do
  t=$p.fresh.$$
  if mv -- "$p" "$t" 2>/dev/null && mv -- "$t" "$p" 2>/dev/null ; then
    :
  else
    echo "sig-fresh: NOTE freshen failed for $p (held open?); verifying anyway" >&2
  fi
done

if gpg --verify -- "$s" "$f" >/dev/null 2>&1 ; then
  echo "GOOD $f (verified from fresh bytes)"
  exit 0
fi

echo "BAD $f (bytes were freshened first - this is NOT the stale-reader bug)"
echo "sig-fresh: next moves, in order:" >&2
echo "  1. cross-read via a second tool-path (reflex 1) before crying tamper" >&2
echo "  2. compare the sig timestamp against the file's edit history -" >&2
echo "     edit-after-sign is the common benign cause" >&2
echo "  3. only then treat as tamper; keep both artifacts for the record" >&2
exit 1
