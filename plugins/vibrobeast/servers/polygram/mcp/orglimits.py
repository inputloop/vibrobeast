# polygram -- gated agent-skill synthesis.
# Copyright 2026 Corwin Brust <corwin@bru.st> and Bryant Frankford <nathanielfrankford@gmail.com> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
"""orglimits -- a group's ORG.md, read so it can only narrow (2026-10-23).

Corwin, 12:14, blessing options 1 and 2 of c4 h/RESEARCH-2026-10-23-org-md-and-declared-limits.md: a group
writes its limits for its members' assistants in its own words (the ORGLIMITS writing form, a row in c4's
c/wf), and the extension reads that file and narrows two settings only: the chat switch for the working mode
(mode.py) and standing yeses (keys.py's keys.standing).  It never loosens either and never writes prefs.

Where an ORG.md is found: the settings field "You: your group's ORG.md" (MENTCACHED_ORG_MD: the file, or a
folder that holds ORG.md); and, for key_run only, the nearest ORG.md at the run's folder or a parent,
stopping at the first folder that holds .git.  Every file found applies; the strongest limit wins.

The Limits lines (the rest of the file is for people):

    - limit <setting> [program=<p>] [host=<h>] | <strength> | <the group's sentence> | <sources>

setting: mode.chat_switch or keys.standing.  strength: must not, prefer not, allowed.  sources:
"source: ..." (the group's own organ) or "sources: a; b" (two or more), else the rule is UNSOURCED: it still
narrows, and the person is told the rule cites no source.  `allowed` is read and ignored: this file cannot
loosen.  A `- limit` line that does not parse, or a file that cannot be read, fails closed: it narrows both
settings as `must not`, with a sentence that names the line.  tests/orglimits.awk is the second reader.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

SETTINGS = ("mode.chat_switch", "keys.standing")
STRENGTHS = ("must not", "prefer not", "allowed")
RANK = {"must not": 2, "prefer not": 1, "allowed": 0}
NAME = "ORG.md"
_LIMIT = re.compile(r"^\s*-\s*limit\b(.*)$")


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sourced(field: str) -> bool:
    f = field.strip()
    if f.lower().startswith("source:"):
        return bool(f[7:].strip())
    if f.lower().startswith("sources:"):
        return len([s for s in f[8:].split(";") if s.strip()]) >= 2
    return False


def _fault(path: str, digest: str, line: int, why: str) -> list[dict]:
    """Fail closed: narrow both settings, saying which line could not be read."""
    s = (f"line {line} of this ORG.md could not be read ({why}), so it fails closed" if line
         else f"this ORG.md could not be read ({why}), so it fails closed")
    return [{"setting": st, "program": "", "host": "", "strength": "must not", "sentence": s,
             "sourced": False, "file": path, "hash": digest, "line": line, "fault": True} for st in SETTINGS]


def parse(text: str, path: str = NAME, digest: str = "") -> list[dict]:
    out: list[dict] = []
    for n, raw in enumerate(text.splitlines(), 1):
        m = _LIMIT.match(raw)
        if not m:
            continue
        parts = [p.strip() for p in m.group(1).split("|")]
        if len(parts) < 3:
            out += _fault(path, digest, n, "it needs setting | strength | sentence")
            continue
        head = parts[0].split()
        setting = head[0] if head else ""
        scope = {"program": "", "host": ""}
        bad = setting not in SETTINGS
        for word in head[1:]:
            k, _, v = word.partition("=")
            if k in scope and v and setting == "keys.standing":
                scope[k] = v
            else:
                bad = True
        strength = " ".join(parts[1].lower().split())
        sentence = parts[2]
        if bad or strength not in STRENGTHS or not sentence:
            out += _fault(path, digest, n, "unknown setting, scope, strength, or an empty sentence")
            continue
        out.append({"setting": setting, **scope, "strength": strength, "sentence": sentence,
                    "sourced": _sourced(parts[3]) if len(parts) > 3 else False,
                    "file": path, "hash": digest, "line": n, "fault": False})
    return out


def read(path: Path) -> list[dict]:
    try:
        b = path.read_bytes()
    except OSError as e:
        return _fault(str(path), "-", 0, type(e).__name__)
    digest = _hash(b)
    try:
        text = b.decode("utf-8")
    except UnicodeDecodeError:
        return _fault(str(path), digest, 0, "not UTF-8")
    return parse(text, str(path), digest)


def _setting_path() -> Path | None:
    raw = (os.environ.get("MENTCACHED_ORG_MD") or "").strip()
    if not raw or "${" in raw:
        return None
    p = Path(raw).expanduser()
    return p / NAME if p.is_dir() else p


def _walk(cwd: str) -> Path | None:
    try:
        d = Path(cwd).expanduser().resolve()
    except (OSError, ValueError):
        return None
    for here in [d, *d.parents]:
        if (here / NAME).is_file():
            return here / NAME
        if (here / ".git").exists():
            return None
    return None


def files(cwd: str | None = None) -> list[Path]:
    out = []
    s = _setting_path()
    if s is not None:
        out.append(s)          # named on the settings page: read even if missing, so a vanished file fails closed
    if cwd:
        w = _walk(cwd)
        if w is not None and all(w.resolve() != o.resolve() for o in out if o.exists()):
            out.append(w)
    return out


def limits(cwd: str | None = None) -> list[dict]:
    return [lim for f in files(cwd) for lim in read(f)]


def _strongest(ls: list[dict]) -> dict | None:
    ls = [x for x in ls if x["strength"] != "allowed"]
    return max(ls, key=lambda x: RANK[x["strength"]]) if ls else None


def chat_switch(ls: list[dict] | None = None) -> dict | None:
    """The limit on switching the working mode from chat, or None."""
    ls = limits() if ls is None else ls
    return _strongest([x for x in ls if x["setting"] == "mode.chat_switch"])


def _host_of(target: str) -> str:
    return target.rsplit("@", 1)[-1].split(":", 1)[0]


def standing(program: str, target: str, ls: list[dict] | None = None, cwd: str | None = None) -> dict | None:
    """The limit on a standing yes for this program and target, or None."""
    ls = limits(cwd) if ls is None else ls
    host = _host_of(target)
    return _strongest([x for x in ls if x["setting"] == "keys.standing"
                       and (not x["program"] or x["program"] == program)
                       and (not x["host"] or x["host"] in (host, target))])


def say(lim: dict) -> str:
    s = (f"Your group's ORG.md ({lim['file']}, sha256 {lim['hash'][:16]}) says: \"{lim['sentence']}\" "
         f"({lim['strength']}).")
    if not lim["sourced"]:
        s += " It cites no source for this rule."
    return s


def register(srv) -> None:
    @srv.tool("org_limits",
              "What your group's ORG.md limits here, read only: the file(s) found (the settings page's 'your "
              "group's ORG.md', and for a folder, the nearest ORG.md up to its repository), each file's sha256, "
              "and each limit in the group's own words. An ORG.md can only narrow (the chat switch for the "
              "working mode, standing yeses); it never loosens anything.",
              {"type": "object", "properties": {"cwd": {"type": "string", "description": "a folder, to include its ORG.md"}}})
    def _limits(args):
        cwd = args.get("cwd") or None
        ls = limits(cwd)
        return {"files": [str(f) for f in files(cwd)], "limits": ls,
                "chat_switch": say(c) if (c := chat_switch(ls)) else "not limited by a group",
                "say": "no ORG.md applies here" if not ls else f"{len(ls)} limit line(s) read"}

