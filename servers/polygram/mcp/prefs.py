# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""prefs -- the few switches this server honours, kept where he can read them.

Corwin, 2026-09-23: *"let's get such checks behind preference, by default on."*  So: a known
list of keys, each with a default and one line saying what it changes; a file that holds what
he set, append-only (last row per key wins, and the row says who and why); two tools, one to
list and one to set.  A key not on the list is refused -- a preference nobody reads is a note,
and it belongs in the seat, not here.

Where: ``$MENTCACHED_PREFS`` (must exist; a path you named is never created), else
``~/.mentcached/prefs.tsv`` (this server's choice, so it may create it).  Rows are
``ts  key  value  by  why``.  ``sh bin/pr1ef`` in the workspace reads the same file with awk.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

from .rpc import ToolError

DEFAULT_PATH = Path.home() / ".mentcached" / "prefs.tsv"
HEADER = "ts\tkey\tvalue\tby\twhy"

#: key -> (default, what it changes).  Add a row here when a check grows a switch.
KNOWN: dict[str, tuple[str, str]] = {
    "freshness.auto": ("on", "seat_mode and span_start report whether the installed plugin is the shelf's mint"),
    "freshness.shelf": ("", "the minted tree on the shelf; else $POLYGRAM_DIST, else a guess beside the seat"),
    "softskills.auto": ("on", "seat_mode and span_start report how many soft skills are loadable, and from where"),
    "softskills.roots": ("", "SOFT-SKILLS roots, os.pathsep-separated; else $SOFT_SKILLS, else ~/.mentcached/SOFT-SKILLS and <seat>/../SOFT-SKILLS"),
    "steward.auto": ("on", "nongnu-steward: ns1op runs its header + ledger audit at session open in a tree carrying .nongnu-steward"),
    "persona.sheets": ("", "folders holding persona sheets and person models, os.pathsep-separated, earlier wins a name; a file is a sheet by what its own first lines say (actor:, a sheet heading, or model front matter); else $PERSONA_SHEETS, else guessed from softskills.roots and words.root"),
    "words.root": ("", "the C4 root the word-path registry (word_where / word_register) reads: else $C4_ROOT, else /f/claude/c4, else ~/mnt/c4 -- whichever carries m/t"),
    "llamabridge.on": ("off", "llamabridge: off until set to on; when on, prompts Claude delegates go to the Ollama server at OLLAMA_HOST (default http://127.0.0.1:11434, this computer). Restart the plugin after changing it"),
    "tavern.on": ("off", "tavern: off until set to on; when on, Claude can read and post in your Tavern rooms, and what is posted is copied to every member machine's disk. Restart the plugin after changing it"),
    "tavern.as": ("claude", "tavern: the agent name Claude uses in the Tavern (Tavern adds this machine's address, e.g. claude-10.8.0.2)"),
    "tavern.data": ("", "tavern: the Tavern data folder, when it is not where Tavern's installer or a download would put it; else $TAVERN_DATA, else found by itself"),
    "c4.on": ("off", "c4face: off until set to on; when on, Claude can use your C4 work surface by running C4's own server (mcp/c4-mcp.js in your C4 folder) with node, after a check at every start. Restart the plugin after changing it"),
    "c4.root": ("", "c4face: your C4 folder (the one holding mcp/c4-mcp.js), when it is not found by itself; else $C4_ROOT, else words.root, else a c4 folder near the seat or the shelf, else the usual places"),
    "steward.canon": ("on", "nongnu-steward: ns1op reports the canon pins' age and the check command at session open; it never fetches unasked"),
}


def path() -> tuple[Path, bool]:
    raw = (os.environ.get("MENTCACHED_PREFS") or "").strip()
    if not raw or "${" in raw or raw.startswith("$"):
        return DEFAULT_PATH, True
    return Path(raw).expanduser(), False


def _rows(p: Path) -> list[list[str]]:
    if not p.is_file():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("ts\t"):
            continue
        f = ln.split("\t")
        if len(f) >= 3:
            out.append(f + [""] * (5 - len(f)))
    return out


def current() -> dict[str, dict]:
    """key -> {value, source, by, ts} for every known key."""
    p, _ = path()
    got: dict[str, list[str]] = {}
    for f in _rows(p):
        if f[1] in KNOWN:
            got[f[1]] = f
    out = {}
    for k, (default, _what) in KNOWN.items():
        if k in got:
            out[k] = {"value": got[k][2], "source": "file", "by": got[k][3], "ts": got[k][0]}
        else:
            out[k] = {"value": default, "source": "default", "by": "", "ts": ""}
    return out


def get(key: str) -> str:
    if key not in KNOWN:
        raise KeyError(key)
    return current()[key]["value"]


def on(key: str) -> bool:
    return get(key).strip().lower() in ("on", "1", "true", "yes")


def set_(key: str, value: str, by: str, why: str) -> dict:
    if key not in KNOWN:
        raise ToolError(f"unknown preference {key!r}; known: {', '.join(KNOWN)}. A preference "
                        "nobody reads is a note -- put it in the seat instead")
    p, ours = path()
    if not p.exists():
        if not ours:
            raise ToolError(f"MENTCACHED_PREFS names {p}, which does not exist; a path you named is "
                            "never created. Unset it, or create the file (empty is fine).")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(HEADER + "\n", encoding="utf-8", newline="\n")
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = [ts, key, " ".join(str(value).split()), " ".join(str(by).split()), " ".join(str(why or "").split())]
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(row) + "\n")
    return {"key": key, "value": row[2], "file": str(p), "ts": ts, "say": f"{key} = {row[2]!r}"}


def register(srv, by: str) -> None:
    @srv.tool("pref_list",
              "Every preference this server honours: its current value, whether that came from "
              "the file or the default, and one line on what it changes.")
    def _list(_args):
        p, ours = path()
        cur = current()
        return {"file": str(p), "file_exists": p.is_file(), "chosen_by": "this server" if ours else "MENTCACHED_PREFS",
                "prefs": [{"key": k, **cur[k], "default": d, "what": w} for k, (d, w) in KNOWN.items()],
                "say": "; ".join(f"{k}={cur[k]['value'] or '(unset)'}" + ("" if cur[k]["source"] == "file" else " (default)")
                                 for k in KNOWN)}

    @srv.tool("pref_set",
              "Set one preference (append-only; the last row wins and says who and why). Only keys "
              "pref_list shows are accepted.",
              {"type": "object",
               "properties": {"key": {"type": "string"}, "value": {"type": "string"},
                              "why": {"type": "string", "description": "one line"}},
               "required": ["key", "value"]})
    def _set(args):
        cur = current().get(args.get("key", ""), {}).get("value")
        out = set_(args.get("key", ""), args.get("value", ""), by, args.get("why") or "")
        out["was"] = cur
        out["say"] = f"{out['key']} = {out['value']!r} (was {cur!r})"
        return out
