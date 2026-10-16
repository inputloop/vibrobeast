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
preference when the person set it, else the first agent already in the Tavern's ``config.json``
under this machine's first person whose model is claude (``claudewin`` in Corwin's Tavern), else
``claude`` -- so a plugin session does not register a second name beside the one already there
(lane B, 2026-10-10; SPEC row F6).  When no Tavern is found, ``tavern_status`` says so and what to do.

Every answer says which roads need gp.1 (the garden-pony build) and that Wire acts go direct
meanwhile; with a Tavern found it names the build of the tavern.py beside the data folder (stock
2.3.1, gp.1, or what its VERSION line says) and the Tavern by its own name before its address
(SPEC row F5).  It reads only tavern_name, humans, agents and api_port from config.json, and never
says the join code, the Tavern id, the address in the room, or a token.
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
CARRIES = ("This plugin carries stock Tavern 2.3.1, byte for byte as Bryant Frankford published it. When "
           "the Tavern on this computer runs the garden-pony build (2.3.1+gp.N, github.com/inputloop/"
           "tavern), the plugin speaks through that Tavern's own tavern.py instead, so Claude gets the "
           "same tools the room has (the tool registry, tavern_tools, among them); the preference "
           "tavern.face=bundled keeps the stock copy.")
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
    from .rpc import env_switch
    sw = env_switch("TAVERN_ON")
    if sw is not None:
        return sw
    return _pref("tavern.on").lower() in ("on", "1", "true", "yes")


#: Which roads wait for the garden-pony build (gp.1), said in every tavern_status answer (F5).
ROADS_STOCK = ("Wire acts go direct (by recipe), not through a Tavern room. The roads that need gp.1, "
               "which this Tavern does not run: the room road for Wire acts, the tool registry "
               "(tavern_tools), Tavern-written receipts, board-claimed local-model jobs and Tavern drops "
               "as a road for files.")
ROADS_GP = ("This Tavern runs the garden-pony build, so the tool registry and Tavern-written receipts are "
            "there. Wire acts still go direct (by recipe): the room road for Wire acts, board-claimed "
            "local-model jobs and drops as a road wait for a later edition of this plugin, which will "
            "need gp.1 for them.")
#: The pinned sha256 of Bryant's stock 2.3.1 (the same pin NOTICE-tavern and the tests carry).
STOCK_SHA256 = "6ffaa56681406aa55073cb9c5ae296edd6659730ff8d73793c5655a77483e78c"


def _pref_set(key: str) -> str:
    """The preference only when the person set it (a row in the file), never its default."""
    try:
        from . import prefs
        cur = prefs.current().get(key) or {}
        return (cur.get("value") or "").strip() if cur.get("source") == "file" else ""
    except Exception:
        return ""


def _cfg(data) -> dict:
    """The few config.json keys tavern_status uses; never join_code, tavern_id, ip or a token."""
    import json
    try:
        raw = json.loads((Path(data) / "config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out = {k: raw.get(k) for k in ("tavern_name", "humans", "agents", "api_port")}
    return out


def _owner_agent(data) -> str:
    """F6: the first agent, by name, under this machine's first person, whose model is claude."""
    if data is None:
        return ""
    c = _cfg(data)
    humans = c.get("humans") if isinstance(c.get("humans"), list) else []
    owner = str(humans[0]).strip() if humans else ""
    agents = c.get("agents") if isinstance(c.get("agents"), dict) else {}
    if not owner:
        return ""
    for name in sorted(agents):
        v = agents[name] if isinstance(agents[name], dict) else {}
        if v.get("owner", "") == owner and str(v.get("model", "")).strip().lower() == "claude":
            return str(name)
    return ""


def agent_and_source(data=None) -> tuple[str, str]:
    """(name, where it came from): TAVERN_AS, the tavern.as the person set, an agent already in
    config.json under the same owner, else claude (F6)."""
    env = os.environ.get("TAVERN_AS", "").strip()
    if env:
        return env, "TAVERN_AS"
    mine = _pref_set("tavern.as")
    if mine:
        return mine, "preference tavern.as"
    found = _owner_agent(data)
    if found:
        return found, "config.json: the agent already there under this machine's person, model claude"
    return "claude", "the default (no agent of this machine's person with model claude in config.json)"


def agent_name(data=None) -> str:
    return agent_and_source(data)[0]


def build_of(data) -> str:
    """F5: which Tavern build the tavern.py beside the data folder is, in words."""
    if data is None:
        return "not known: no Tavern data folder found"
    py = Path(data).parent / "tavern.py"
    if not py.is_file():
        return "not known: no tavern.py beside the data folder"
    import hashlib
    import re
    try:
        b = py.read_bytes()
    except OSError:
        return "not known: tavern.py beside the data folder could not be read"
    if hashlib.sha256(b).hexdigest() == STOCK_SHA256:
        return "stock 2.3.1 (as published, pinned)"
    m = re.search(rb'^VERSION = "([^"]+)"', b, re.M)
    ver = m.group(1).decode("ascii", "replace") if m else ""
    if "+gp." in ver:     # any garden-pony build (gp.1, gp.8, ...); "gp.1" alone missed gp.2 and later
        return ver + " (the garden-pony build)"
    if ver:
        return ver + " (not the pinned stock bytes, not garden-pony)"
    return "not known: tavern.py has no VERSION line"


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
                "roads": ROADS_STOCK, "talks_to": "nothing; while it is off this is the only tool"}
    if sys.version_info < NEED:
        return {"state": "ON, BUT THIS PYTHON IS TOO OLD",
                "say": "Tavern needs Python %d.%d or newer; the plugin was started with %d.%d. "
                       "Install Python 3.10 or newer (python.org, or MSYS2's python; Tavern-Setup.bat "
                       "also offers one), then restart Claude. On Windows the plugin finds the newer "
                       "Python by itself; nothing needs editing." % (NEED + tuple(sys.version_info[:2])),
                "carries": CARRIES, "roads": ROADS_STOCK, "talks_to": "nothing"}
    f = find_data()
    if f["dir"] is None:
        return {"state": "ON, BUT NO TAVERN FOUND ON THIS COMPUTER",
                "say": "Tavern is turned on, but no Tavern data folder was found. Start Tavern once "
                       "(Tavern.bat, the desktop icon, or `python tavern.py`); it makes a "
                       "tavern-data folder beside tavern.py. Then restart Claude. If Tavern lives "
                       "somewhere unusual, tell Claude the folder and it will set the preference "
                       "tavern.data for you.",
                "looked_in": f["tried"], "notes": f["named_missing"], "carries": CARRIES,
                "roads": ROADS_STOCK, "talks_to": "nothing"}
    c = _cfg(f["dir"])
    name = str(c.get("tavern_name") or "").strip()
    port = c.get("api_port")
    bld = build_of(f["dir"])
    who, who_from = agent_and_source(f["dir"])
    where = str(f["dir"]) + (", API port %s" % port if port else "")
    say = (("Tavern \u201c%s\u201d, at %s" % (name, where)) if name else ("an unnamed Tavern, at " + where))
    say += ". Build: %s. Claude would join it as %s (%s)." % (bld, who, who_from)
    return {"state": "ON", "say": say, "tavern": name, "build": bld,
            "roads": ROADS_GP if "garden-pony" in bld else ROADS_STOCK, "carries": CARRIES,
            "face": face_of(f["dir"])[1],
            "data": str(f["dir"]), "found_by": f["from"], "running": f["running"],
            "as": who, "as_from": who_from}


def face_of(data):
    """Which tavern.py speaks for Claude, and that in words (inputloop/tavern#8). The Tavern's own, when the
    tavern.py beside the data folder is a garden-pony build: then Claude's tools are the room's tools
    (tavern_tools, error ids, tavern-wide limits). Otherwise, or with the preference tavern.face=bundled,
    the stock 2.3.1 this plugin carries. Returns (path or None, words)."""
    if _pref("tavern.face").lower() == "bundled":
        return None, "the stock 2.3.1 this plugin carries (preference tavern.face=bundled)"
    bld = build_of(data)
    if data is not None and "garden-pony" in bld:
        py = Path(data).parent / "tavern.py"
        import hashlib
        return py, "this Tavern's own tavern.py, %s, sha256 %s" % (bld.split(" (")[0],
                                                                     hashlib.sha256(py.read_bytes()).hexdigest()[:16])
    return None, "the stock 2.3.1 this plugin carries (this Tavern is %s)" % bld


def _load_face(py):
    """Import a Tavern's own tavern.py by path, under a name of its own, writing no bytecode beside it."""
    import importlib.util
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("tavern_local_face", str(py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build():
    """The server whenever Tavern's own face is not running: one tool, which says why."""
    from .rpc import Server
    srv = Server(name="tavernface", version=VERSION, require_mode=False)

    @srv.tool("tavern_status",
              "Whether the Tavern (a common room for people and agents) is on, what turning "
              "it on means, how to turn it on by asking Claude, and which Tavern this plugin "
              "carries (stock 2.3.1), and which roads need the garden-pony build (gp.1). "
              "While it is off, this is the only tool, and nothing is sent anywhere.")
    def _status(_args):
        return status()
    return srv


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    st = status()
    if st["state"] != "ON":
        build().serve()
        return 0
    py, _words = face_of(st["data"])
    if py is not None:
        face = _load_face(py)
    else:
        from . import tavern_upstream as face
    return int(face.main(["mcp", "--as", st["as"], "--model", "claude", "--data", st["data"]] + argv) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
