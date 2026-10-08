# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""freshness -- is the plugin this server is running from the one on the shelf?

Corwin, 2026-09-23: *"What changed in the plugin that I need to reinstall it?"*  A question that
should be answered by a command, not by a diff pasted at handback -- because the pipe between the
shelf (``dist/vibrobeast`` in the workspace) and the app is a manual upload, by his hand, on
purpose, and the only thing that makes that ceremony cheap is knowing exactly when it matters.

WHAT IT COMPARES.  Two ``MANIFEST`` files, nothing else: the one beside the code this server was
started from (the INSTALLED copy -- the server finds its own root by walking up from ``__file__``,
or from ``$CLAUDE_PLUGIN_ROOT`` when the app exports it), and the one on the SHELF (the ``shelf``
argument, else the ``freshness.shelf`` preference, else ``$POLYGRAM_DIST``, else a guess beside the seat,
said out loud as a guess).  A
manifest is one line per shipped file, ``<sha256>  ./path``; the diff of two of them is the list of
files that would change on reinstall, sorted into ``servers/``, ``skills/<name>`` and the rest.

WHAT IT DOES NOT DO.  It does not hash the installed tree (that is ``check.sh``, 42 s on his F:
mount), does not fetch, does not install, and does not decide for him: the verdict is CURRENT,
BEHIND or UNKNOWN, and ``reinstall`` says in words what a reinstall would buy.

Also a command, for the same answer from a shell::

    python3 -m polygram.mcp.freshness --shelf dist/vibrobeast [--installed DIR]
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from .rpc import ToolError

_HERE = Path(__file__).resolve()


def _is_plugin_root(p: Path) -> bool:
    return (p / "MANIFEST").is_file() and (p / ".claude-plugin" / "plugin.json").is_file()


def installed_root() -> tuple[Path | None, str]:
    """(root, how) for the plugin tree this code runs from; (None, why) when it is a source tree."""
    pr = (os.environ.get("CLAUDE_PLUGIN_ROOT") or "").strip()
    if pr and "${" not in pr and _is_plugin_root(Path(pr)):
        return Path(pr).resolve(), "CLAUDE_PLUGIN_ROOT"
    for up in _HERE.parents:
        if _is_plugin_root(up):
            return up, "walked up from " + _HERE.name
    return None, ("not running from an installed plugin (no MANIFEST above "
                  f"{_HERE}); this is a source tree")


def shelf_root(given: str | None) -> tuple[Path | None, str]:
    """(root, how) for the shelf copy: the argument, the env, or a guess beside the seat."""
    if given:
        p = Path(str(given)).expanduser()
        if p.is_file() and p.name == "MANIFEST":
            p = p.parent
        return (p.resolve(), "given") if _is_plugin_root(p) else (None, f"{p} is not a plugin tree (no MANIFEST + .claude-plugin/plugin.json)")
    try:                                   # the pref, so the tool and checks.run agree (2026-09-24)
        from . import prefs as _prefs
        pref = _prefs.get("freshness.shelf").strip()
    except Exception:                      # noqa: BLE001 -- unreadable prefs fall through to env
        pref = ""
    if pref:
        p = Path(pref).expanduser()
        if p.is_file() and p.name == "MANIFEST":
            p = p.parent
        if _is_plugin_root(p):
            return p.resolve(), "pref freshness.shelf"
    env = (os.environ.get("POLYGRAM_DIST") or "").strip()
    if env and _is_plugin_root(Path(env).expanduser()):
        return Path(env).expanduser().resolve(), "POLYGRAM_DIST"
    seat = (os.environ.get("MENTCACHED_SEAT") or "").strip()
    if seat and "${" not in seat:
        guess = Path(seat).expanduser().parent / "dist" / "vibrobeast"
        if _is_plugin_root(guess):
            return guess.resolve(), "GUESSED beside the seat (MENTCACHED_SEAT/../dist/vibrobeast)"
    return None, "no shelf given: pass `shelf`, or set POLYGRAM_DIST to the minted tree"


def read_manifest(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in (root / "MANIFEST").read_text(encoding="utf-8").splitlines():
        if len(ln) > 66 and ln[64:66] == "  ":
            out[ln[66:].removeprefix("./")] = ln[:64]
    return out


def mint_id(root: Path) -> str:
    """16 hex of the MANIFEST bytes: the same bytes on both sides mean the same mint."""
    return hashlib.sha256((root / "MANIFEST").read_bytes()).hexdigest()[:16]


def plugin_zip_sha16(root: Path) -> str | None:
    z = root.parent / f"{root.name}.plugin"
    return hashlib.sha256(z.read_bytes()).hexdigest()[:16] if z.is_file() else None


def _area(rel: str) -> tuple[str, str]:
    parts = rel.split("/")
    if parts[0] == "servers":
        return "servers", "servers"
    if parts[0] == "skills" and len(parts) > 1:
        return "skills", parts[1]
    return "other", rel


def compare_roots(installed: Path, shelf: Path) -> dict:
    a, b = read_manifest(installed), read_manifest(shelf)
    only_i = sorted(set(a) - set(b)); only_s = sorted(set(b) - set(a))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    touched = only_i + only_s + changed
    skills: dict[str, int] = {}; servers = 0; other: list[str] = []
    for rel in touched:
        area, name = _area(rel)
        if area == "servers": servers += 1
        elif area == "skills": skills[name] = skills.get(name, 0) + 1
        else: other.append(rel)
    same = mint_id(installed) == mint_id(shelf)
    verdict = "CURRENT" if same else "BEHIND"
    if same:
        reinstall = "no: the installed plugin IS the shelf mint"
    elif servers:
        reinstall = f"yes: {servers} server file(s) differ -- the running servers are not the shelf's"
    elif skills:
        reinstall = ("only if you want that skill text live: " + ", ".join(sorted(skills))
                     + " changed; no server file did")
    else:
        reinstall = "only for the record: " + ", ".join(other[:6]) + (" ..." if len(other) > 6 else "") + " differ; no server or skill did"
    say = (f"installed mint {mint_id(installed)} vs shelf mint {mint_id(shelf)}: "
           + ("identical manifests" if same else
              f"{len(touched)} file(s) differ ({len(changed)} changed, {len(only_s)} new on the shelf, "
              f"{len(only_i)} only installed)") + f". Reinstall: {reinstall}")
    return {"verdict": verdict, "installed_mint": mint_id(installed), "shelf_mint": mint_id(shelf),
            "shelf_plugin_sha16": plugin_zip_sha16(shelf),
            "servers_changed": servers, "skills_changed": sorted(skills), "other_changed": other,
            "changed": changed, "only_shelf": only_s, "only_installed": only_i,
            "counts": {"installed": len(a), "shelf": len(b)}, "reinstall": reinstall, "say": say}


def report(args: dict | None, *, installed: Path | None = None) -> dict:
    args = args or {}
    if installed is None:
        inst, how_i = installed_root()
    else:
        inst, how_i = (installed.resolve(), "given") if _is_plugin_root(installed) else (None, f"{installed} is not a plugin tree")
    sh, how_s = shelf_root(args.get("shelf"))
    base = {"installed_root": str(inst) if inst else None, "installed_how": how_i,
            "shelf_root": str(sh) if sh else None, "shelf_how": how_s}
    if inst is None:
        return {**base, "verdict": "UNKNOWN", "reinstall": "cannot say",
                "say": f"UNKNOWN: {how_i}. Ask this from the installed plugin, or pass --installed on the command line."}
    if sh is None:
        return {**base, "verdict": "UNKNOWN", "installed_mint": mint_id(inst), "reinstall": "cannot say",
                "say": f"UNKNOWN: installed mint {mint_id(inst)} at {inst}; {how_s}"}
    return {**base, **compare_roots(inst, sh)}


SCHEMA = {"type": "object",
          "properties": {"shelf": {"type": "string",
                                   "description": ("the minted tree on the shelf, e.g. F:/claude/AS4CE/AS4CE0001/dist/vibrobeast "
                                                   "(or its MANIFEST). Omit to use the freshness.shelf preference, else $POLYGRAM_DIST, else a guess beside the seat.")}}}


def register(srv) -> None:
    srv.tool("plugin_freshness",
             "Is the plugin this server runs from the one on the shelf? Compares the two MANIFESTs and "
             "says CURRENT / BEHIND / UNKNOWN, which files would change on reinstall (servers, which "
             "skills, other), and in words whether a reinstall buys anything. Read-only; hashes nothing.",
             SCHEMA)(lambda a: report(a))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    shelf = None; inst = None
    while argv:
        a = argv.pop(0)
        if a == "--shelf" and argv: shelf = argv.pop(0)
        elif a == "--installed" and argv: inst = Path(argv.pop(0))
        else:
            print(__doc__.split("Also a command")[1].strip(), file=sys.stderr); return 2
    r = report({"shelf": shelf}, installed=inst)
    print(r["say"])
    for k in ("changed", "only_shelf", "only_installed"):
        for rel in r.get(k) or []:
            print(f"  {k:<14} {rel}")
    if r["verdict"] == "UNKNOWN":
        print(f"  installed: {r.get('installed_root')} ({r['installed_how']})")
        print(f"  shelf:     {r.get('shelf_root')} ({r['shelf_how']})")
    return {"CURRENT": 0, "BEHIND": 1}.get(r["verdict"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
