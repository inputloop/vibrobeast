# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""metrics -- the skill-metrics store, served read-only over MCP.

ONE IMPLEMENTATION. The store's reader/writer is ``skills/skill-metrics/scripts/sk2mt``
(POSIX sh). This module does not parse the store; it runs that script and hands back what
it printed. A second parser here would be a second copy of the format to drift -- the skill
exists precisely so nothing repeats it.

THE COST OF THAT CHOICE, named rather than hidden: it needs an ``sh`` the MCP process can
find. On a Windows host the desktop app may launch servers without msys2 on PATH. When no
``sh`` is found the tool REFUSES and says so -- a refusing tool is a checkable statement of
what is owed; a silently empty one teaches nothing.

WHERE THE STORE IS: ``$SKILL_METRICS_ROOT``. Nothing is guessed and nothing is created: an
unset or missing root answers NOTVISIBLE with the path it was given.

READ ONLY. Writing stays with ``bin/gd1ck --record`` and ``sk2mt set`` on the host, where
the tests run. A metrics row written from a chat is a claim with no run behind it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .rpc import ToolError

VIEWS = ("say", "state", "cur", "last", "date", "note", "row", "items", "log", "table", "check")
_HERE = Path(__file__).resolve()


def script() -> Path | None:
    """sk2mt beside the skill: repo layout (polygram/mcp -> root) or plugin layout
    (servers/polygram/mcp -> plugin root), or under $CLAUDE_PLUGIN_ROOT."""
    cands = [_HERE.parents[2], _HERE.parents[3] if len(_HERE.parents) > 3 else None]
    pr = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if pr:
        cands.insert(0, Path(pr))
    for base in cands:
        if base is None:
            continue
        p = base / "skills" / "skill-metrics" / "scripts" / "sk2mt"
        if p.is_file():
            return p
    return None


def find_sh() -> str | None:
    return os.environ.get("SKILL_METRICS_SH") or shutil.which("sh")


def read(args: dict) -> dict:
    view = args.get("view") or "say"
    if view not in VIEWS:
        raise ToolError(f"view must be one of: {', '.join(VIEWS)}")
    root = (os.environ.get("SKILL_METRICS_ROOT") or "").strip()
    if not root:
        return {"metrics_mode": "NOTVISIBLE",
                "say": "SKILL_METRICS_ROOT is not set, so there is no store to read. "
                       "Set it to the directory holding log and skill-metrics/ "
                       "(in AS4CE0001 that is the metrics/ folder) and restart."}
    sk, sh = script(), find_sh()
    if sk is None:
        raise ToolError("cannot find skills/skill-metrics/scripts/sk2mt beside this server; "
                        "the plugin was minted without the skill-metrics skill")
    if sh is None:
        raise ToolError("no `sh` on this server's PATH, and the one implementation of the "
                        "store is a POSIX sh script. Set SKILL_METRICS_SH to an sh "
                        "(e.g. C:/msys64/usr/bin/sh.exe) or put msys2's usr/bin on PATH.")
    argv = [sh, str(sk), "-C", root, view]
    if view != "check":
        for flag, key in (("-E", "extended"), ("-i", "ignore_case"), ("-v", "invert"), ("-x", "whole")):
            if args.get(key):
                argv.append(flag)
        if args.get("state"):
            argv += ["--state", str(args["state"])]
        pat = args.get("pattern")
        names = args.get("names") or []
        if pat and names:
            raise ToolError("give names OR a pattern, not both (the store follows POSIX grep)")
        if pat:
            argv += ["-e", str(pat)]
        for n in names:
            if str(n).startswith("-"):
                raise ToolError(f"a name cannot start with '-': {n}")
            argv.append(str(n))
    p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                       env=dict(os.environ, LC_ALL="C"))
    modes = {0: "FOUND", 1: "NONE-SELECTED", 2: "ERROR", 3: "NOTVISIBLE"}
    return {"metrics_mode": modes.get(p.returncode, f"EXIT-{p.returncode}"),
            "root": root, "view": view, "exit": p.returncode,
            "text": p.stdout, "stderr": p.stderr.strip()}


SCHEMA = {
    "type": "object",
    "properties": {
        "view": {"type": "string", "enum": list(VIEWS),
                 "description": "what to show: say (plain sentences, the default), a field "
                                "(state cur last date note row), items, log (history), "
                                "table, or check (is the store self-consistent)"},
        "names": {"type": "array", "items": {"type": "string"},
                  "description": "exact item names, e.g. [\"polygram\", \"skill-sign\"]"},
        "pattern": {"type": "string",
                    "description": "a POSIX grep pattern over item names (BRE; set extended for ERE)"},
        "state": {"type": "string",
                  "description": "keep only items whose last STATE is this word, e.g. RED. "
                                 "(pattern and names select on item NAMES, never on states)"},
        "extended": {"type": "boolean"}, "ignore_case": {"type": "boolean"},
        "invert": {"type": "boolean"}, "whole": {"type": "boolean"},
    },
}


def register(srv) -> None:
    srv.tool("metrics_read",
             "Read the garden's skill-metrics store (what state each skill, tool and package "
             "was last seen in, when it changed, and the archived current/previous copy). "
             "Read-only; results come from the store's one implementation, sk2mt. Say "
             "view='say' for plain sentences.", SCHEMA)(read)
