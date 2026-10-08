# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""softskills -- the dynaloader: skills served live from folders, no install ceremony.

Corwin, 2026-09-23: *"a dynaloader so that we can use simple folders with a predictable name that
happen to be landed in a SOFT-SKILLS folder (which will share a format with the design for skills
for now, to keep things simple). I'm not inclined to deal with extra ceremony dancing around with
desktop."*

THE SHAPE.  ``SOFT-SKILLS/<name>/SKILL.md`` -- the same folder-and-frontmatter format as
``skills/`` -- under one or more roots.  Nothing is installed anywhere: ``soft_skills_list`` scans
the roots NOW, every call, and ``soft_skill_read`` hands back the SKILL.md (or one of the files
beside it) as text.  Drop a folder in and it is there on the next call; edit it and the next read
is the edit.  That is the whole loader.

ROOTS, in order: the ``softskills.roots`` preference, else ``$SOFT_SKILLS`` (os.pathsep-separated),
else ``~/.mentcached/SOFT-SKILLS`` and ``<seat>/../SOFT-SKILLS`` when ``MENTCACHED_SEAT`` is set;
and, read LAST on every branch, the running plugin's own ``SOFT-SKILLS/`` (a sized edition's, or the
author tree's), so a preference set elsewhere never hides them (ERRATA E1, 2026-09-29).
Only roots that exist are used, and every answer says which were looked in.  Two roots naming the
same skill: the first root wins, and the list says who is shadowed.

WHAT IT REFUSES.  Reading outside a skill's own folder (``..``, absolute paths, symlinks out), a
file that is not text, and a file over 256 KB -- each with the reason.  Nothing here writes.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

from . import prefs as _prefs
from .rpc import ToolError

MAX_BYTES = 256 * 1024


def _own_soft() -> Path | None:
    """The running plugin's own SOFT-SKILLS folder.  In a minted plugin this file is
    <plugin>/servers/polygram/mcp/softskills.py, beside <plugin>/servers/launch.py; in the author's
    tree it is <tree>/polygram/mcp/softskills.py.  None when neither has the folder."""
    here = Path(__file__).resolve().parent
    root = here.parents[2] if (here.parents[1] / "launch.py").is_file() else here.parents[1]
    d = root / "SOFT-SKILLS"
    return d if d.is_dir() else None


OWN: Path | None = _own_soft()   # tests set this; None reads nothing extra
_TEXT_SUFFIXES = {".md", ".txt", ".sh", ".py", ".pl", ".awk", ".tsv", ".csv", ".json", ".yaml", ".yml",
                  ".toml", ".org", ".html", ".css", ".js", ".el", ".mk", ".cfg", ".ini", ""}


def roots() -> list[tuple[Path, str, bool]]:
    """[(path, how, exists)] in lookup order."""
    out: list[tuple[Path, str, bool]] = []
    try:
        pref = _prefs.get("softskills.roots").strip()
    except Exception:            # noqa: BLE001 -- prefs unreadable is not a reason to hide skills
        pref = ""
    if pref:
        for p in pref.split(os.pathsep):
            if p.strip():
                out.append((Path(p.strip()).expanduser(), "pref softskills.roots", False))
    else:
        env = (os.environ.get("SOFT_SKILLS") or "").strip()
        if env and "${" not in env:
            for p in env.split(os.pathsep):
                if p.strip():
                    out.append((Path(p.strip()).expanduser(), "$SOFT_SKILLS", False))
        else:
            out.append((Path.home() / ".mentcached" / "SOFT-SKILLS", "default beside the seat", False))
            seat = (os.environ.get("MENTCACHED_SEAT") or "").strip()
            if seat and "${" not in seat:
                out.append((Path(seat).expanduser().parent / "SOFT-SKILLS", "beside MENTCACHED_SEAT", False))
    if OWN is not None:
        def _same(a: Path, b: Path) -> bool:
            try:
                return a.resolve() == b.resolve()
            except OSError:
                return False
        if not any(_same(p, OWN) for p, _, _ in out):
            out.append((OWN, "the running plugin's own", False))
    return [(p, how, p.is_dir()) for p, how, _ in out]


def _frontmatter(text: str) -> dict[str, str]:
    """name/description out of the same frontmatter skills/ uses; folded (>-) and literal (|) blocks joined."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, str] = {}
    key = None; buf: list[str] = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ln[:1] not in (" ", "\t") and ":" in ln:
            if key:
                fm[key] = " ".join(" ".join(buf).split())
            key, _, val = ln.partition(":")
            key = key.strip(); val = val.strip()
            buf = [] if val in (">", ">-", "|", "|-") else [val]
        elif key is not None:
            buf.append(ln.strip())
    if key:
        fm[key] = " ".join(" ".join(buf).split())
    return fm


def scan() -> dict:
    seen: dict[str, dict] = {}
    shadowed: list[str] = []
    looked = []
    for root, how, exists in roots():
        looked.append({"root": str(root), "how": how, "exists": exists})
        if not exists:
            continue
        for d in sorted(root.iterdir()):
            sk = d / "SKILL.md"
            if not d.is_dir() or d.name.startswith(".") or not sk.is_file():
                continue
            if d.name in seen:
                shadowed.append(f"{d.name} in {root} (shadowed by {seen[d.name]['root']})")
                continue
            try:
                fm = _frontmatter(sk.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                fm = {}
            files = [p for p in d.rglob("*") if p.is_file() and not any(x.startswith(".") for x in p.relative_to(d).parts)]
            seen[d.name] = {"name": d.name, "root": str(root), "dir": str(d),
                            "description": fm.get("description", ""), "declared_name": fm.get("name", ""),
                            "files": len(files), "mtime": int(sk.stat().st_mtime)}
    return {"skills": list(seen.values()), "roots": looked, "shadowed": shadowed}


def summary() -> str:
    s = scan()
    live = [r["root"] for r in s["roots"] if r["exists"]]
    if not live:
        return "no SOFT-SKILLS root exists (looked: " + ", ".join(r["root"] for r in s["roots"]) + ")"
    return f"{len(s['skills'])} soft skill(s) loadable from " + ", ".join(live) + (
        f"; {len(s['shadowed'])} shadowed" if s["shadowed"] else "")


def _jail(base: Path, rel: str) -> Path:
    if not rel or rel.startswith(("/", "\\")) or ".." in Path(rel).parts or ":" in rel[:2]:
        raise ToolError(f"file must be a path inside the skill folder, got {rel!r}")
    p = (base / rel).resolve()
    if base.resolve() not in p.parents and p != base.resolve():
        raise ToolError(f"{rel!r} resolves outside {base} -- refused")
    return p


# THE USAGE LEDGER (2026-09-24). "Skills stay soft until they demonstrate they are getting used"
# (Corwin). Every soft_skill_read appends one line -- ts<TAB>name<TAB>root<TAB>file -- to
# $MENTCACHED_SOFTSKILLS_USAGE, else ~/.mentcached/softskills-usage.tsv. Append-only, never read
# here; bin/ss2gr reads it and reports reads and distinct days per soft skill, so graduation into
# skills/ is a hand-turn on evidence, not a guess. A ledger that cannot be written is not a reason
# to refuse the read: the skill is served either way, and the miss is noted in the answer.
USAGE_PATH = Path.home() / ".mentcached" / "softskills-usage.tsv"


def usage_path() -> Path:
    raw = (os.environ.get("MENTCACHED_SOFTSKILLS_USAGE") or "").strip()
    return Path(raw).expanduser() if raw and not raw.startswith("$") else USAGE_PATH


def _note_use(name: str, root: str, rel: str) -> None:
    try:
        up = usage_path()
        up.parent.mkdir(parents=True, exist_ok=True)
        new = not up.exists()
        with up.open("a", encoding="utf-8", newline="\n") as fh:
            if new:
                fh.write("ts\tname\troot\tfile\n")
            fh.write(f"{_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\t{name}\t{root}\t{rel}\n")
    except OSError:
        pass


def read(args: dict) -> dict:
    name = (args.get("name") or "").strip()
    if not name:
        raise ToolError("name is required (see soft_skills_list)")
    s = scan()
    hit = next((k for k in s["skills"] if k["name"] == name), None)
    if hit is None:
        raise ToolError(f"no soft skill {name!r} in any root (looked: "
                        + ", ".join(r["root"] for r in s["roots"]) + ")")
    d = Path(hit["dir"])
    rel = (args.get("file") or "SKILL.md").replace("\\", "/")
    p = _jail(d, rel)
    if not p.is_file():
        raise ToolError(f"{rel!r} is not a file in {d}")
    if p.suffix.lower() not in _TEXT_SUFFIXES:
        raise ToolError(f"{rel!r} does not look like text ({p.suffix}); this loader serves text only")
    size = p.stat().st_size
    if size > MAX_BYTES:
        raise ToolError(f"{rel!r} is {size} bytes; over the {MAX_BYTES} byte limit -- read it on the host")
    text = p.read_text(encoding="utf-8", errors="replace")
    _note_use(name, hit["root"], rel)
    others = sorted(str(q.relative_to(d)).replace("\\", "/") for q in d.rglob("*")
                    if q.is_file() and q != d / "SKILL.md" and not any(x.startswith(".") for x in q.relative_to(d).parts))
    return {"name": name, "file": rel, "dir": str(d), "root": hit["root"], "bytes": size,
            "description": hit["description"], "text": text,
            "files": others if rel == "SKILL.md" else [],
            "say": f"{name}/{rel} ({size} bytes) from {hit['root']}"
                   + (f"; {len(others)} other file(s) beside it" if rel == "SKILL.md" and others else "")}


def register(srv) -> None:
    @srv.tool("soft_skills_list",
              "Every soft skill loadable RIGHT NOW: a folder with a SKILL.md under a SOFT-SKILLS root, "
              "same format as installed skills, nothing installed. Scans on every call; a folder "
              "dropped in is listed on the next one. Says which roots it looked in.")
    def _list(_args):
        s = scan()
        return {**s, "say": summary()}

    @srv.tool("soft_skill_read",
              "The SKILL.md of a soft skill (or one file beside it, by relative path) as text, read "
              "from disk now. Use it the way you would use an installed skill's instructions.",
              {"type": "object",
               "properties": {"name": {"type": "string"},
                              "file": {"type": "string", "description": "relative path inside the skill folder; default SKILL.md"}},
               "required": ["name"]})
    def _read(args):
        return read(args or {})
