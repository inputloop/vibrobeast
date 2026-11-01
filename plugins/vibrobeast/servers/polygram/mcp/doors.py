# polygram -- gated agent-skill synthesis.
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# This file is part of polygram.  It is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version; or, at your choice, the GNU Lesser
# General Public License, version 3 or later.  It is distributed WITHOUT ANY WARRANTY; see
# <https://www.gnu.org/licenses/>.

"""doors -- every way this plugin reaches out, lets something in, keeps your words, or loads a file that
can carry instructions, in one table, said in words.

Corwin, 2026-10-28 23:32 (the F3 ruling): change the defaults themselves; make them swappable at run time
and at build time; offer them the way Emacs does -- TRAMP shows you the host before a new connection, Org
asks before a #+SETUPFILE from a URL it has not opened before, and an unsafe file-local variable is shown
with its value before it is applied -- so a person sees the context with the offer.  Broad and fine
settings up front, for whoever wants to set once or drill in; the same words in every settings surface;
where our control ends, said plainly; each door linked to its writings, our own docs, the policy and the
governance, so a disclosure always leads back to the terms it rests on.

Who decides, in order (stricter wins at the top):
  1. ``doors.profile`` (each | local | closed).  closed shuts every door; local shuts the doors that reach
     another machine.  Nothing below opens what this shuts.
  2. An explicit environment switch (the settings page of the desktop extension, or a runner's env).
  3. The person's own row in prefs.tsv.
  4. The default: house (prefs.KNOWN) < build (defaults.tsv beside prefs.py) < runner ($VIBROBEAST_DEFAULTS).
     A runner's file may only shut (his ruling, 2026-10-29 03:02, "close only for now"): prefs refuses a row
     there that would open a door or name a folder to load from, and door_list shows the refusal.

``door_list`` (mentcached) shows all of it.  Second reader: tests/doors-reader.awk lists the .on keys from
prefs.py's own text; DOORS must hold exactly those .on keys (tests/test_doors.py).
"""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse

#: The writings each door links to, by name; every shipped plugin carries these files beside its README.
DOCS = {"privacy": "PRIVACY.md", "terms": "TERMS-OF-SERVICE.md", "readme": "README.md",
        "security": "SECURITY.md"}

#: key -> what the door is.  kind: out (we connect to something), keep (we keep your words on disk),
#: load (we run or read something that can carry instructions).  reach: this-computer | other-machines |
#: depends (said in `reach_now`).  limit: where our control ends, in words.
DOORS: dict[str, dict] = {
    "llamabridge.on": {
        "env": "LLAMABRIDGE_ON", "kind": "out", "reach": "depends",
        "what": "Llama Bridge (Bryant Frankford's) sends the prompts Claude delegates to an Ollama server.",
        "context": "Where they would go now: OLLAMA_HOST, else http://127.0.0.1:11434 (this computer).",
        "limit": "We choose whether the bridge starts and where it sends; what the Ollama server does with a "
                 "prompt is that server's, not ours.",
        "docs": ["privacy", "readme"], "words": ["door", "delegate", "local model"]},
    "llamabridge.keep_prompts": {
        "env": "", "kind": "keep", "reach": "this-computer",
        "what": "Whether Llama Bridge's log keeps the words of each delegated prompt and its answer.",
        "context": "The log is ~/.mentcached/llama-bridge.db, made 0600 where the system has modes.",
        "limit": "Off keeps no prompt or answer text in the event log or the answer cache from then on; an "
                 "async job's answer is kept in the jobs table, since delegate_result reads it from there, "
                 "and the plugin does not clear it. Rows written before are left as they were, never "
                 "cleared in silence: door_list counts them.",
        "docs": ["privacy"], "words": ["keep", "log", "prompt"]},
    "llamabridge.stored_host": {
        "env": "", "kind": "out", "reach": "depends",
        "what": "An ollama_host row stored in Llama Bridge's own database, which would send prompts elsewhere.",
        "context": "Like an unsafe file-local variable in Emacs: shown, not applied, until you say use -- "
                   "including a row written while the bridge runs.",
        "limit": "We read the row and decide whether it is used; we do not delete it (it is Bryant's "
                 "program's own setting).",
        "docs": ["privacy"], "words": ["door", "stored setting"], "values": ("ask", "use")},
    "tavern.on": {
        "env": "TAVERN_ON", "kind": "out", "reach": "other-machines",
        "what": "Claude reads and posts in your Tavern rooms (Bryant Frankford's Tavern).",
        "context": "What is posted is copied to the disk of every member machine of that Tavern.",
        "limit": "The plugin runs only Tavern's own MCP face, talking to the Tavern on this computer; it never "
                 "starts the Tavern's peer listener. That listener, its address (Tavern's config.json 'bind', "
                 "0.0.0.0 by Tavern's own default) and any resident agent's calls to api.anthropic.com belong "
                 "to the Tavern you run; tavern_status says the address it listens on.",
        "docs": ["privacy", "readme"], "words": ["door", "room", "tavern"]},
    "gw.on": {
        "env": "GW_ON", "kind": "out", "reach": "other-machines",
        "what": "Claude asks your listed ghostwheel hosts how they are, and draws the status icon.",
        "context": "Each name lookup and each new host key is asked first unless you said always.",
        "limit": "We decide which hosts are asked and pin their keys; the hosts' answers are theirs.",
        "docs": ["privacy", "readme"], "words": ["door", "host", "ghostwheel"]},
    "c4.on": {
        "env": "C4_ON", "kind": "load", "reach": "this-computer",
        "what": "Claude uses your C4 work surface by running C4's own server (node) from your C4 folder.",
        "context": "Code from your own C4 folder runs, after a check at every start, with a trimmed environment.",
        "limit": "We check what we start and what it is handed; what C4's server then does is C4's.",
        "docs": ["privacy", "readme"], "words": ["door", "c4"]},
    "usage.capture": {
        "env": "", "kind": "keep", "reach": "this-computer",
        "what": "Two token counts per prompt, and the preferences and questions you log, kept in the frame.",
        "context": "~/.mentcached/stats/fr; FRAME.md says each column.",
        "limit": "Kept on this computer only; nothing sends it anywhere.",
        "docs": ["privacy"], "words": ["keep", "usage"]},
}

LOOPBACK_NAMES = ("localhost",)


def _is_loopback(url: str) -> bool:
    host = (urlparse(url if "://" in url else "http://" + url).hostname or "").strip("[]").lower()
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def reach_now(key: str) -> str:
    """this-computer or other-machines, for this door as things stand now."""
    d = DOORS[key]
    if d["reach"] != "depends":
        return d["reach"]
    if key == "llamabridge.on":
        return "this-computer" if _is_loopback(os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434") \
            else "other-machines"
    if key == "llamabridge.stored_host":
        h = stored_host()
        return "this-computer" if (not h or _is_loopback(h)) else "other-machines"
    return "other-machines"


def _prefs():
    from . import prefs
    return prefs


def profile() -> tuple[str, str]:
    """(each|local|closed, where it came from)."""
    p = _prefs()
    cur = p.current().get("doors.profile", {})
    v = (cur.get("value") or "each").strip().lower()
    if v not in ("each", "local", "closed"):
        v = "closed"     # a value nobody reads is not a yes: an unreadable broad setting shuts
    src = "your row" if cur.get("source") == "file" else f"default ({cur.get('default_from', 'house')})"
    return v, src


def state(key: str) -> dict:
    """The door's state and who decided it: {open, value, decided_by, said}."""
    from .rpc import env_switch
    p = _prefs()
    d = DOORS[key]
    prof, prof_src = profile()
    cur = p.current().get(key, {})
    value = (cur.get("value") or "").strip().lower()
    if d.get("values"):
        want_open = value == d["values"][1]
    else:
        want_open = value in ("on", "1", "true", "yes")
    decided = "your row in prefs.tsv" if cur.get("source") == "file" else \
        f"the {cur.get('default_from', 'house')} default"
    if cur.get("source") != "file" and cur.get("default_from") in ("build", "runner"):
        lay = p.default_layers()[0].get(key) or {}
        decided += f" ({lay.get('file', '?')}, line {lay.get('line', '?')})"   # which file opened it, said
    sw = env_switch(d["env"]) if d.get("env") else None
    if sw is not None:
        want_open, decided = sw, f"the environment ({d['env']})"
    if prof == "closed" and want_open:
        return {"open": False, "value": value, "decided_by": f"doors.profile=closed ({prof_src})",
                "said": "shut by the broad setting, though " + decided + " says open"}
    if prof == "local" and want_open and reach_now(key) == "other-machines":
        return {"open": False, "value": value, "decided_by": f"doors.profile=local ({prof_src})",
                "said": "shut: it would reach another machine, and the broad setting is local"}
    return {"open": bool(want_open), "value": value, "decided_by": decided,
            "said": ("open" if want_open else "shut") + ", by " + decided}


def is_open(key: str) -> bool:
    try:
        return state(key)["open"]
    except Exception:                                    # noqa: BLE001 -- a door we cannot read stays shut
        return False


def stored_host(db=None) -> str:
    """The ollama_host row in Llama Bridge's database, read-only, or '' (no db, no row, unreadable)."""
    import sqlite3
    from pathlib import Path
    db = Path(db) if db else Path.home() / ".mentcached" / "llama-bridge.db"
    if not db.is_file():
        return ""
    try:
        c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            row = c.execute("SELECT value FROM config WHERE key='ollama_host'").fetchone()
        finally:
            c.close()
        return (row[0] or "").strip() if row else ""
    except Exception:                                    # noqa: BLE001
        return ""


def kept_rows(db=None) -> dict:
    """How many rows of Llama Bridge's log already hold prompt or answer words (read-only), and how to clear them."""
    import sqlite3
    from pathlib import Path
    db = Path(db) if db else Path.home() / ".mentcached" / "llama-bridge.db"
    if not db.is_file():
        return {"rows": 0, "file": str(db), "exists": False}
    note = "(not kept: keep_prompts is off)"   # llama_bridge.NOT_KEPT
    try:
        c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            ev = c.execute("SELECT COUNT(*) FROM events WHERE (prompt IS NOT NULL AND prompt != ?) "
                           "OR (response IS NOT NULL AND response != ?)", (note, note)).fetchone()[0]
            ca = c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            jb = c.execute("SELECT COUNT(*) FROM jobs WHERE (prompt IS NOT NULL AND prompt != ? AND prompt != '') "
                           "OR result IS NOT NULL", (note,)).fetchone()[0]
        finally:
            c.close()
    except Exception as e:                               # noqa: BLE001
        return {"rows": None, "file": str(db), "exists": True, "unread": str(e)}
    n = ev + ca + jb
    return {"rows": n, "events": ev, "cache": ca, "jobs": jb, "file": str(db), "exists": True,
            "clear": ("the file is yours: delete it with the plugin stopped, or ask Claude to clear the rows "
                      "with you watching") if n else ""}


def listing() -> dict:
    """What door_list answers: the broad setting first, then each door, then the layers and links."""
    p = _prefs()
    prof, prof_src = profile()
    lay, refused = p.default_layers()
    rows = []
    for k, d in DOORS.items():
        st = state(k)
        row = {"key": k, "open": st["open"], "said": st["said"], "kind": d["kind"], "reaches": reach_now(k),
               "what": d["what"], "context": d["context"], "where_our_control_ends": d["limit"],
               "read_more": [DOCS[x] for x in d["docs"]], "words": d["words"],
               "set_it": f"pref_set {k} " + ("|".join(d["values"]) if d.get("values") else "on|off")
                         + (f", or {d['env']} in the environment" if d.get("env") else "")}
        if k == "llamabridge.keep_prompts":
            row["words_already_kept"] = kept_rows()
        if k == "llamabridge.stored_host":
            h = stored_host()
            row["stored_row"] = h or "(none)"
            row["applies"] = bool(h) and st["open"]
        rows.append(row)
    return {"broad": {"key": "doors.profile", "value": prof, "from": prof_src,
                      "choices": {"each": "every door by its own key (the default)",
                                  "local": "doors that reach another machine stay shut",
                                  "closed": "every door shut, whatever else says open"}},
            "doors": rows,
            "defaults": {"order": "house < build < runner; your row beats them; the environment beats your row; "
                                  "doors.profile closed or local beats all",
                         "set_by_layers": {k: {"value": v["value"], "from": v["from"], "file": v["file"]}
                                           for k, v in lay.items()},
                         "refused": refused,
                         "runner_file": "VIBROBEAST_DEFAULTS names it; build file: defaults.tsv beside prefs.py"},
            "say": "Broad: doors.profile=" + prof + f" ({prof_src}). "
                   + "; ".join(f"{r['key']} {'OPEN' if r['open'] else 'shut'} ({r['said']})" for r in rows)
                   + ". Each door's read_more names the files beside the README that say more."}


def register(srv) -> None:
    @srv.tool("door_list",
              "Every door this plugin has -- what reaches out, what keeps your words, what loads code -- with "
              "the broad setting first (doors.profile), then each door: open or shut, who decided, what it "
              "reaches, where our control ends, and which files say more. Read-only.")
    def _list(_args):
        return listing()

# Copyright 2026 INPUTLOOP; GPL-3.0-or-later OR LGPL-3.0-or-later; https://github.com/inputloop
# Mentat (for Corwin, claude-opus-5-5)
