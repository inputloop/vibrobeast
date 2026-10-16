#!/bin/sh
# tests-pl1nk.sh -- this skill's copy of pl1nk, held by C4's spec (t/pl1nk-spec.py, python3), which a second
# author wrote.  A skill travels without C4; where C4 is not in reach this says NOT RUN, never ok.
# usage: sh tests-pl1nk.sh [--prove-red]
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
here=$(cd "$(dirname "$0")" && pwd)
for c in "${C4_ROOT:-}" "$here/../../../c4" "$here/../../../../c4" /f/claude/c4 "$HOME/mnt/c4"; do
  [ -n "$c" ] && [ -f "$c/t/pl1nk-spec.py" ] && { C4=$c; break; }; done
[ -n "${C4:-}" ] || { echo "fortress-palace: NOT RUN -- C4's t/pl1nk-spec.py is not in reach (set C4_ROOT)"; exit 77; }   # 77: skipped, never passed
PL1NK_TOOL="$here/scripts/pl1nk" exec python3 "$C4/t/pl1nk-spec.py" "$@"
