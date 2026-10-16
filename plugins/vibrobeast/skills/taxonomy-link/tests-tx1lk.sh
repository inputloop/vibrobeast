#!/bin/sh
# tests-tx1lk.sh -- this skill's copy of tx1lk, held by C4's spec (t/tx1lk-spec.pl, perl), which a second
# author wrote.  A skill travels without C4; where C4 is not in reach this says NOT RUN, never ok.
# usage: sh tests-tx1lk.sh [--prove-red]
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
here=$(cd "$(dirname "$0")" && pwd)
for c in "${C4_ROOT:-}" "$here/../../../c4" "$here/../../../../c4" /f/claude/c4 "$HOME/mnt/c4"; do
  [ -n "$c" ] && [ -f "$c/t/tx1lk-spec.pl" ] && { C4=$c; break; }; done
[ -n "${C4:-}" ] || { echo "taxonomy-link: NOT RUN -- C4's t/tx1lk-spec.pl is not in reach (set C4_ROOT)"; exit 77; }   # 77: skipped, never passed
TX1LK_TOOL="$here/scripts/tx1lk" exec perl "$C4/t/tx1lk-spec.pl" "$@"
