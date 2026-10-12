#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""
check_vocab_sync.py — read-only guard for rolls-v1.2's tight coupling to verify-say.

rolls-v1.2 hardcodes verify-say's state tokens inline (guards 3 and 4) instead of
pointing at verify-say in the abstract, per its own revision note:

    "if verify-say's state names ever change, this file needs a matching edit."

Nothing else catches that drift automatically — rolls does not `import` verify-say,
it just names tokens in prose. This script is the cheap CI-shaped signal that turns
"someday-surprise" into a loud, immediate failure, per tool-lifecycle's guidance
that a cross-check like this should outlive either skill's internal rewording.

MEASURES ONLY. Never edits either SKILL.md. Never repairs. Same discipline as
shelf-check and instrument-panel: read, report, exit non-zero, stop.

Exit codes:
  0  clean — every required token is present in verify-say's SKILL.md
  2  drift — verify-say's SKILL.md exists but is missing one or more tokens
  3  fault — verify-say's SKILL.md could not be found or read at all
             (per verify-say's own canary-first rule: refuse a verdict rather
             than silently pass when the thing being checked is unreachable)

Usage:
  python3 check_vocab_sync.py [--verify-say PATH]

If --verify-say is omitted, tries common install locations in order and reports
which one it used (or that none were found) — never guesses silently.
"""

from __future__ import annotations  # `str | None` below must not break Python < 3.10

import argparse
import re
import sys
from pathlib import Path

# The exact tokens rolls-v1.2 names inline. Keep this list byte-for-byte in sync
# with rolls-v1.2/SKILL.md's own guard 3 / guard 4 prose — if you add a token
# there, add it here in the same edit.
REQUIRED_TOKENS = ["SIGN", "DETACH", "NOSIG", "FURNITURE", "PANEL-FAULT"]

DEFAULT_CANDIDATES = [
    "/mnt/skills/user/verify-say/SKILL.md",
    "../verify-say/SKILL.md",
    "../../verify-say/SKILL.md",
]


def find_verify_say(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    for cand in DEFAULT_CANDIDATES:
        p = Path(cand)
        if p.is_file():
            return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--verify-say", dest="verify_say", default=None,
                     help="explicit path to verify-say's SKILL.md")
    args = ap.parse_args()

    target = find_verify_say(args.verify_say)

    if target is None:
        print("check_vocab_sync: FAULT — verify-say/SKILL.md not found")
        print("  tried (in order):")
        if args.verify_say:
            print(f"    --verify-say {args.verify_say}")
        else:
            for c in DEFAULT_CANDIDATES:
                print(f"    {c}")
        print("  attempted command you can re-run once you know the real path:")
        print("    python3 check_vocab_sync.py --verify-say /path/to/verify-say/SKILL.md")
        print("  NOT ATTEMPTED: token check (nothing to check against)")
        return 3

    text = target.read_text(encoding="utf-8", errors="replace")
    # Whole words only: SIGNED or DETACHED on the page must not stand in for SIGN or DETACH.
    missing = [t for t in REQUIRED_TOKENS
               if not re.search(r"(?<![A-Za-z0-9_-])" + re.escape(t) + r"(?![A-Za-z0-9_-])", text)]

    print(f"check_vocab_sync: checked {target}")
    print(f"  required tokens: {', '.join(REQUIRED_TOKENS)}")

    if missing:
        print(f"  DRIFT — missing {len(missing)} of {len(REQUIRED_TOKENS)}: {', '.join(missing)}")
        print("  rolls-v1.2/SKILL.md guards 3 and 4 name these tokens inline.")
        print("  Either verify-say renamed/dropped a state, or this list is stale.")
        print("  Fix: reconcile rolls-v1.2's prose and this REQUIRED_TOKENS list together,")
        print("  in the same edit, against whatever verify-say now actually says.")
        return 2

    print(f"  CLEAN — {len(REQUIRED_TOKENS)} of {len(REQUIRED_TOKENS)} tokens present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
