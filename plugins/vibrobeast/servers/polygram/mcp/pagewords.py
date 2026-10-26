# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""pagewords -- the settings page's own words, for the agent, with the same force they have for you.

Why (Corwin and Bryant, 2026-10-26 05:32): Bryant's agent read "user: (empty)" from the servers
and had to be sent to the README to learn what the page already said, "Left empty: each host's
short name (gw7 logs in as gw7)".  "If you show me text on that page with a certain meaning (field
or label) you need to have exactly that same meaning in mind, not just so you implement but also so
you explain."

So the meaning is read from the bytes the page is drawn from, never retyped: the extension's own
manifest.json (installed beside server/), else, in a source tree, polygram.mcpb.manifest().  For
each field this says its title and description word for word, whether it was filled in, and, when it
was not, the page's own "Left empty" (or "Off/On by default") sentence as what applies.  A value is
repeated only when the field is a plain word or number; secrets and paths are said as set.
Standard library only.  Mentat (for Corwin, claude-opus-5-5)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

#: The words that open what a field means when it is left as it came.
EMPTY_OPENERS = ("Left empty", "Off by default", "On by default")
RULE = ("These are the settings page's own words.  When a field is left empty, the sentence under "
        "'applies' is what it means, with the same force as a value typed in: say it that way, and "
        "act on it.  Never report an empty field as missing, unknown or unset without its sentence.")


def manifest_path() -> Path | None:
    """The installed extension's manifest.json (<ext>/server/polygram/mcp/pagewords.py -> <ext>)."""
    p = Path(__file__).resolve().parents[3] / "manifest.json"
    return p if p.is_file() else None


def user_config() -> tuple[dict, str]:
    """(user_config, where it was read from): the page's bytes, as the page has them."""
    p = manifest_path()
    if p is not None:
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(m.get("user_config"), dict):
                return m["user_config"], str(p)
        except (OSError, ValueError):
            pass
    try:
        from polygram import mcpb
        m = mcpb.manifest()
        return m["user_config"], "polygram/mcpb.py (source tree)"
    except Exception as e:                                          # noqa: BLE001
        return {}, f"not found ({e.__class__.__name__}): no manifest.json beside the server, no mcpb"


def env_names(uc: dict | None = None) -> dict:
    """field -> environment variable, from the manifest's own mcp_config env when it is there."""
    p = manifest_path()
    out: dict = {}
    if p is not None:
        try:
            env = json.loads(p.read_text(encoding="utf-8"))["server"]["mcp_config"]["env"]
            for var, tmpl in env.items():
                m = re.fullmatch(r"\$\{user_config\.([A-Za-z0-9_]+)\}", tmpl or "")
                if m:
                    out[m.group(1)] = var
        except (OSError, ValueError, KeyError, TypeError):
            out = {}
    if not out:
        try:
            from polygram import mcpb
            out = {k: var for k, (var, _f) in mcpb.USER_CONFIG.items()}
        except Exception:                                           # noqa: BLE001
            out = {}
    return out


def sentences(text: str) -> list[str]:
    """Split at a full stop followed by a space or the end, never inside brackets (gw7.bru.st holds)."""
    out, cur, depth = [], "", 0
    for i, ch in enumerate(text):
        cur += ch
        depth += ch == "("
        depth -= ch == ")" and depth > 0
        if ch == "." and depth == 0 and (i + 1 == len(text) or text[i + 1] == " "):
            out.append(cur.strip())
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def empty_sentence(description: str) -> str:
    """The page's sentence for a field left as it came: from its opener to the sentence's end."""
    for s in sentences(description or ""):
        for o in EMPTY_OPENERS:
            at = s.find(o)
            if at >= 0:
                return s[at:]
    return ""


def is_empty(v) -> bool:
    v = "" if v is None else str(v).strip()
    return not v or "${" in v


def explain(env: dict | None = None, fields: tuple | list | None = None) -> dict:
    """Each field: its title and description word for word, filled in or not, and what applies."""
    env = os.environ if env is None else env
    uc, src = user_config()
    names = env_names(uc)
    rows = []
    for key, f in uc.items():
        if fields and key not in fields:
            continue
        var = names.get(key, "")
        raw = env.get(var) if var else None
        kind = f.get("type", "string")
        row = {"field": key, "title": f.get("title", ""), "page_says": f.get("description", ""),
               "variable": var}
        if is_empty(raw):
            row["filled_in"] = False
            said = empty_sentence(f.get("description", ""))
            if kind == "boolean" and "default" in f:
                row["applies"] = said or ("on" if f["default"] else "off") + " (the page's default)"
                row["value"] = bool(f["default"])
            else:
                row["applies"] = said or "the page says nothing for empty; ask the keeper"
        else:
            row["filled_in"] = True
            if f.get("sensitive"):
                row["applies"] = "your value (a secret: set, never shown)"
            elif kind in ("file", "directory"):
                row["applies"] = "your value (a path: set)"
            else:
                row["applies"] = f"your value: {str(raw).strip()}"
                row["value"] = str(raw).strip()
        rows.append(row)
    return {"rule": RULE, "read_from": src, "fields": rows}


def problems(uc: dict | None = None) -> list[str]:
    """A field the agent could not say the meaning of when empty is a page fault (cf. mcpb L4)."""
    uc = user_config()[0] if uc is None else uc
    out = []
    for key, f in uc.items():
        if f.get("type") == "boolean" and "default" in f:
            continue
        if not empty_sentence(f.get("description", "")):
            out.append(f"{key}: the page says nothing an agent can repeat for an empty field")
    return out
