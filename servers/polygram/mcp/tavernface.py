# polygram -- gated agent-skill synthesis.
# Copyright 2026 Bryant Frankford <nathanielfrankford@gmail.com> and Corwin Brust <corwin@bru.st>
# and Contributors.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# This file is part of polygram.  It is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version; or, at your choice, the
# GNU Lesser General Public License, version 3 or later.  It is distributed WITHOUT ANY WARRANTY;
# see <https://www.gnu.org/licenses/>.
# Written by Mentat (for Corwin; claude-opus-5-5), around Tavern, written with Alfred (for Bryant;
# claude-opus-5-5).

"""tavernface -- Bryant Frankford's Tavern, served from the vibrobeast plugin, off until you turn
it on, with nothing to edit by hand.

Tavern (tavern_upstream.py beside this file, 2.3.1, byte for byte as Bryant published it; see
NOTICE-tavern) is a common room for people and AI agents.  Everything said there is copied to the
disk of every member machine, so this plugin does not open the door on install.  Until the
preference ``tavern.on`` is ``on`` -- ask Claude to turn the Tavern on: it sets that with the
plugin's own ``pref_set`` tool (mentcached server), then the plugin is restarted -- or
``TAVERN_ON=1`` is in the environment, this server answers one tool, ``tavern_status``, which says
it is off, what turning it on means, and how, and talks to nothing.

When on, it finds this computer's Tavern by itself (``find_data``): ``TAVERN_DATA``, else the
``tavern.data`` preference, else the places Tavern's own installer puts it (``cmd_install`` in
tavern_upstream.py writes tavern.py into the folder Tavern-Setup.bat was run from, or into
``~/Tavern`` when that was a temporary folder, with ``tavern-data`` beside it), else the usual
folders a download lands in.  It then runs Tavern's own MCP face in this process, as
``tavern.py mcp --as NAME --model claude --data DIR`` would, with NAME from the ``tavern.as``
preference (default ``claude``).  When no Tavern is found, ``tavern_status`` says so and what to do.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

VERSION = "0.1.0"
NEED = (3, 10)              # Tavern refuses older pythons (tavern_upstream.py, line 175)

MEANS = ("Turning the Tavern on lets Claude read and post in your Tavern rooms as an agent. "
         "Everything posted there, by you or by Claude, is copied to the disk of every member "
         "machine of that Tavern; treat it as public to the members.")
#: Which Tavern this is, said in every tavern_status answer (QA1 row 18): the shop also builds a
#: patched one, and a person should not think they have it.
CARRIES = ("This plugin carries Bryant's stock Tavern 2.3.1, byte for byte as he published it. It "
           "does not have the garden-pony changes: no tool registry (tavern_tools), and no marking "
           "of receipt lines an agent typed itself (\"typed by the agent, not a Tavern receipt\"). "
           "That patched build, 2.3.1+gp.1, is offered to Bryant as patches; it lives in "
           "projects/garden-pony on the author's machine now, and will be at "
           "github.com/inputloop/tavern once published.")
HOW_ON = ("Ask Claude: \"turn the Tavern on\". Claude sets the preference tavern.on to on with the "
          "plugin's pref_set tool; then restart Claude (or the vibrobeast plugin). Nothing to edit "
          "by hand. To turn it off again, ask Claude to set tavern.on to off.")


def _pref(key: str) -> str:
    try:
        from . import prefs
        return (prefs.get(key) or "").strip()
    except Exception:
        return ""


def is_on() -> bool:
    if os.environ.get("TAVERN_ON", "").strip() == "1":
        return True
    return _pref("tavern.on").lower() in ("on", "1", "true", "yes")


def agent_name() -> str:
    return (os.environ.get("TAVERN_AS", "").strip() or _pref("tavern.as") or "claude")


def _named(raw: str):
    if not raw or "${" in raw or raw.startswith("$"):
        return None
    return Path(raw).expanduser()


def candidates() -> list[tuple[str, Path]]:
    """(where the guess came from, folder) in the order they are tried."""
    out: list[tuple[str, Path]] = []
    for why, raw in (("TAVERN_DATA", os.environ.get("TAVERN_DATA", "")),
                     ("preference tavern.data", _pref("tavern.data"))):
        p = _named(raw.strip())
        if p is not None:
            out.append((why, p))
    home = Path.home()
    # The installer's own fallback first (cmd_install: a temp folder becomes ~/Tavern).
    out.append(("Tavern's installer folder", home / "Tavern" / "tavern-data"))
    for sub in ("Downloads", "Desktop", "Documents", "OneDrive/Desktop", "OneDrive/Documents", ""):
        base = home / sub if sub else home
        out.append(("beside a tavern.py in " + (sub or "your home folder"), base / "tavern-data"))
        out.append(("beside a tavern.py in " + ((sub + "/Tavern") if sub else "~/Tavern"),
                    base / "Tavern" / "tavern-data"))
    seen, uniq = set(), []
    for why, p in out:
        k = str(p)
        if k not in seen:
            seen.add(k)
            uniq.append((why, p))
    return uniq


def _is_tavern(p: Path) -> bool:
    try:
        return p.is_dir() and any((p / f).is_file() for f in ("agent.json", "node.key", "config.json"))
    except OSError:
        return False


def find_data() -> dict:
    """{'dir': Path or None, 'from': str, 'running': bool, 'tried': [...], 'named_missing': [...]}.
    A folder Tavern is running in (agent.json present) wins over one it is not."""
    tried, named_missing, first = [], [], None
    for why, p in candidates():
        tried.append(str(p))
        if not _is_tavern(p):
            if why in ("TAVERN_DATA", "preference tavern.data"):
                named_missing.append(f"{why} names {p}, which is not a Tavern data folder")
            continue
        if (p / "agent.json").is_file():
            return {"dir": p, "from": why, "running": True, "tried": tried, "named_missing": named_missing}
        if first is None:
            first = (why, p)
    if first:
        return {"dir": first[1], "from": first[0], "running": False, "tried": tried,
                "named_missing": named_missing}
    return {"dir": None, "from": "", "running": False, "tried": tried, "named_missing": named_missing}


def status() -> dict:
    if not is_on():
        return {"state": "OFF", "means": MEANS, "turn_on": HOW_ON, "carries": CARRIES,
                "talks_to": "nothing; while it is off this is the only tool"}
    if sys.version_info < NEED:
        return {"state": "ON, BUT THIS PYTHON IS TOO OLD",
                "say": "Tavern needs Python %d.%d or newer; the plugin was started with %d.%d. "
                       "Install Python 3.10 or newer (python.org, or MSYS2's python; Tavern-Setup.bat "
                       "also offers one), then restart Claude. On Windows the plugin finds the newer "
                       "Python by itself; nothing needs editing." % (NEED + tuple(sys.version_info[:2])),
                "carries": CARRIES, "talks_to": "nothing"}
    f = find_data()
    if f["dir"] is None:
        return {"state": "ON, BUT NO TAVERN FOUND ON THIS COMPUTER",
                "say": "Tavern is turned on, but no Tavern data folder was found. Start Tavern once "
                       "(Tavern.bat, the desktop icon, or `python tavern.py`); it makes a "
                       "tavern-data folder beside tavern.py. Then restart Claude. If Tavern lives "
                       "somewhere unusual, tell Claude the folder and it will set the preference "
                       "tavern.data for you.",
                "looked_in": f["tried"], "notes": f["named_missing"], "carries": CARRIES, "talks_to": "nothing"}
    return {"state": "ON", "carries": CARRIES, "data": str(f["dir"]), "found_by": f["from"], "running": f["running"],
            "as": agent_name()}


def build():
    """The server whenever Tavern's own face is not running: one tool, which says why."""
    from .rpc import Server
    srv = Server(name="tavernface", version=VERSION, require_mode=False)

    @srv.tool("tavern_status",
              "Whether the Tavern (Bryant's common room for people and agents) is on, what turning "
              "it on means, how to turn it on by asking Claude, and which Tavern this plugin "
              "carries (Bryant's stock 2.3.1). While it is off, this is the only tool, and nothing "
              "is sent anywhere.")
    def _status(_args):
        return status()
    return srv


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    st = status()
    if st["state"] != "ON":
        build().serve()
        return 0
    from . import tavern_upstream
    return int(tavern_upstream.main(["mcp", "--as", st["as"], "--model", "claude",
                                     "--data", st["data"]] + argv) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
