# polygram -- words: the word-path registry (C4 g/<word>/<leaf>) served over MCP, a second reader.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This file is part of vibrobeast.  Authored by Mentat (for Corwin).  It is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.  It is distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""WORDS (2026-09-24). Corwin, mid-turn: "We have defined memory, maybe we need words ... the
complexity of managing all those words in all that documentation across all those different lookup
tables of how different persona intersections could play out as aspect and trait to select word
choice ... at run time, it gets to look like a lot."

So: one lookup, at run time, over MCP. This module is the PYTHON reader of the registry C4's
``bin/wd1nn`` (POSIX sh) reads -- ``$C4_ROOT/g/<word>/<leaf>`` where the leaf's NAME is the nearest
well-known place toward ``m/t`` (``t z s e d g f c h m``, origin order; ``z`` = private canon in
another root, the enclave, cited by path) and its body is
``key<TAB>value`` lines (neighbor, meaning, since, by). Two readers in two languages over one
registry is the seams law applied to meaning: agreement is evidence, and either one alone is data.

ROOT: the ``words.root`` preference, else ``$C4_ROOT``, else the first of ``/f/claude/c4`` and
``~/mnt/c4`` that carries ``m/t``. Every answer says which root it read and whether a word is a
proper gap (nothing on the short list holds it) -- the gap footnote, mechanical.

Two tools: ``word_where`` (read) and ``word_register`` (write one leaf; never overwrites; the
neighbour must exist under the root unless the leaf is ``m``). Nothing else here writes.
"""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

from . import prefs as _prefs
from .rpc import ToolError

ORDER = ["t", "z", "s", "e", "d", "g", "f", "c", "h", "m"]
PLACES = {
    "t": "m/t (the register table)",
    "z": "private canon in another root (the SAVANNAH enclave: PRINCIPLES, CHARTERS -- NOTATION's z/*; cited by path, never copied; the values canon itself lives on the pub shelf, canon/principles/, since 2026-09-29)",
    "s": "evidence/scalars.tsv (a registered scalar or pattern name)",
    "e": "evidence/terms-of-art.tsv (a term of art: definer, status)",
    "d": "a document on a registry shelf (d/ gen0/ governance/ decks/ q/)",
    "g": "another G graph (g/TAXONOMY/<term>/ or g/DISCOVERY/<word>/)",
    "f": "facts/<slug>",
    "c": "context/<file>",
    "h": "h/<file> (a dated working model; a word whose only home is here is a candidate)",
    "m": "memory (a copy elsewhere, never the origin)",
}


def root() -> tuple[Path | None, str]:
    """The C4 root in play and where the choice came from."""
    try:
        pref = _prefs.get("words.root").strip()
    except Exception:            # noqa: BLE001 -- prefs unreadable is not a reason to hide words
        pref = ""
    cands = []
    if pref:
        cands.append((Path(pref).expanduser(), "pref words.root"))
    env = (os.environ.get("C4_ROOT") or "").strip()
    if env and not env.startswith("$"):
        cands.append((Path(env).expanduser(), "$C4_ROOT"))
    cands.append((Path("/f/claude/c4"), "default /f/claude/c4"))
    cands.append((Path.home() / "mnt" / "c4", "default ~/mnt/c4"))
    for p, why in cands:
        if (p / "m" / "t").is_file():
            return p, why
    return None, "no candidate root carries m/t (looked: " + ", ".join(f"{p} [{w}]" for p, w in cands) + ")"


def _slug(word: str) -> str:
    w = (word or "").strip().lower()
    if not w or "/" in w or "\\" in w or w.startswith(".") or any(c.isspace() for c in w):
        raise ToolError(f"not a word: {word!r} (letters, digits, hyphens; a phrase is hyphenated)")
    return w


def _leaf(path: Path) -> dict:
    out = {}
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "\t" in ln:
            k, v = ln.split("\t", 1)
            out.setdefault(k.strip(), v.strip())
    return out


def is_word_dir(d: Path) -> bool:
    return d.is_dir() and any((d / l).is_file() for l in ORDER)


def live(c4: Path, w: str) -> list[dict]:
    """The short list, checked live, whether or not a leaf exists. Seven places (h/ and analysis/ by
    file name only); memory is not searched (a word whose only home is there is a copy)."""
    hits = []
    W = w.upper().replace("-", "_")
    mt = c4 / "m" / "t"
    found = ""
    if mt.is_file():
        for ln in mt.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = ln.split()
            if len(parts) > 1 and W in parts[1:]:
                found = f"{parts[0]} col{parts.index(W)}"
                break
    hits.append({"place": "t", "hit": bool(found), "what": found or "m/t"})

    def tsv_rows(rel: str, col: int) -> str:
        """EVERY matching row, with its row number -- a term may carry two rows (ring: row 8
        practice/hand-turning, row 125 Corwin-verbatim/pinned) and the first is not the answer."""
        p = c4 / rel
        if not p.is_file():
            return ""
        out = []
        for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ln.startswith("#") or "\t" not in ln:
                continue
            f = ln.split("\t")
            if f[0].strip().lower() == w:
                out.append(f"row {i}: " + " · ".join(x for x in f[1:col + 1] if x))
        return " ; ".join(out)
    s = tsv_rows("evidence/scalars.tsv", 1)
    hits.append({"place": "s", "hit": bool(s), "what": s or "evidence/scalars.tsv"})
    e = tsv_rows("evidence/terms-of-art.tsv", 2)
    hits.append({"place": "e", "hit": bool(e), "what": e or "evidence/terms-of-art.tsv"})
    g = []
    for graph in ("TAXONOMY", "DISCOVERY"):
        d = c4 / "g" / graph / w
        if d.is_dir():
            g.append(f"g/{graph}/{w}/ ({' '.join(sorted(x.name for x in d.iterdir()))})")
    hits.append({"place": "g", "hit": bool(g), "what": " · ".join(g) or f"g/TAXONOMY/{w} g/DISCOVERY/{w}"})
    fd = c4 / "facts"
    f = sorted(x.name for x in fd.iterdir() if fd.is_dir() and x.is_file() and w in x.name.lower().split("-")) if fd.is_dir() else []
    hits.append({"place": "f", "hit": bool(f), "what": " ".join(f[:3]) or "facts/ (by slug)"})
    cd = c4 / "context"
    c = sorted(x.name for x in cd.iterdir() if x.is_file() and w in x.name.lower()) if cd.is_dir() else []
    hits.append({"place": "c", "hit": bool(c), "what": " ".join(c[:3]) or "context/ (by name)"})
    # h/ and analysis/ by FILE NAME only: the least settled neighbour, and where the 2026-09-24
    # miss lived (h/METHOD-lens-and-granule-ring.md). Token match on - _ . boundaries, as wd1nn.
    import re as _re
    pat = _re.compile(r"(^|[-_.])" + _re.escape(w) + r"([-_.]|$)", _re.I)
    names = []
    hd = c4 / "h"
    if hd.is_dir():
        names += sorted(x.name for x in hd.iterdir() if pat.search(x.name))
    ad = c4 / "analysis"
    if ad.is_dir():
        names += sorted(str(x.relative_to(c4)).replace("\\", "/") for x in ad.rglob("*") if x.is_file() and pat.search(x.name))
    hits.append({"place": "h", "hit": bool(names), "what": " ".join(names[:4]) or "h/ analysis/ (by name)"})
    return hits


def where(args: dict) -> dict:
    w = _slug(args.get("name", ""))
    c4, why = root()
    if c4 is None:
        raise ToolError(why)
    d = c4 / "g" / w
    leaves = []
    if is_word_dir(d):
        for l in ORDER:
            if (d / l).is_file():
                leaves.append({"leaf": l, "place": PLACES[l], **_leaf(d / l)})
    lv = live(c4, w)
    nhits = sum(1 for h in lv if h["hit"])
    gap = not leaves and nhits == 0
    nearest = leaves[0]["leaf"] if leaves else next((h["place"] for h in lv if h["hit"]), None)
    say = (f"{w}: " + (f"{len(leaves)} leaf(s) under g/{w}/ (nearest {leaves[0]['leaf']} -> {leaves[0].get('neighbor', '?')})" if leaves else f"no g/{w}/ leaf")
           + f"; live: {nhits}/7 places hold it" + ("; two leaves = a seam this word carries" if len(leaves) > 1 else "")
           + ("; A PROPER GAP -- nothing on the short list holds it (h/ and memory not searched)" if gap else ""))
    return {"word": w, "root": str(c4), "root_from": why, "leaves": leaves, "live": lv, "nearest": nearest,
            "gap": gap, "places": PLACES, "say": say}


def register_word(args: dict, by: str) -> dict:
    w = _slug(args.get("name", ""))
    leaf = (args.get("leaf") or "").strip()
    nb = (args.get("neighbor") or "").strip()
    mn = (args.get("meaning") or "").strip()
    if leaf not in ORDER:
        raise ToolError(f"leaf {leaf!r} is not on the short list ({' '.join(ORDER)})")
    if not nb or not mn:
        raise ToolError("neighbor and meaning are both required")
    c4, why = root()
    if c4 is None:
        raise ToolError(why)
    looks_like_path = ("/" in nb or nb.endswith((".md", ".tsv"))) and not (len(nb) > 2 and nb[0].isupper() and nb[1] == " ")
    if leaf not in ("m", "z") and looks_like_path and not (c4 / nb).exists():
        raise ToolError(f"neighbor {nb!r} is not under {c4} -- a neighbour must exist to be near (leaf m is exempt)")
    g = c4 / "g"
    up = g / w.upper()
    if w != w.upper() and up.exists() and not is_word_dir(up):
        raise ToolError(f"g/{w.upper()} is a graph (uppercase by convention); on a case-folding filesystem {w!r} cannot be a word dir beside it")
    d = g / w
    if d.exists() and not is_word_dir(d) and (not d.is_dir() or any(d.iterdir())):
        raise ToolError(f"g/{w} exists and is not a word dir; refusing to mix")
    if (d / leaf).is_file():
        raise ToolError(f"g/{w}/{leaf} already registered:\n" + (d / leaf).read_text(encoding="utf-8", errors="replace"))
    d.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    body = f"neighbor\t{nb}\nmeaning\t{mn}\nsince\t{stamp}\nby\t{by}\n"
    tmp = d / f"{leaf}.tmp"
    tmp.write_text(body, encoding="utf-8", newline="\n")
    tmp.replace(d / leaf)
    return {"word": w, "leaf": leaf, "path": str(d / leaf), "root": str(c4), "say": f"g/{w}/{leaf} -> {nb}"}


def register(srv, by: str) -> None:
    @srv.tool("word_where",
              "Where does this word's meaning live? The C4 word-path registry (g/<word>/<leaf>, the leaf "
              "named for the nearest well-known place toward m/t) plus a live check of the short list of "
              "places one must always look (m/t, scalars, terms-of-art, the G graphs, facts, context). "
              "Says when a word is a proper gap. Read-only; the POSIX twin is c4/bin/wd1nn.",
              {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]})
    def _where(args):
        return where(args or {})

    @srv.tool("word_register",
              "Register where a word's meaning lives: one leaf under g/<word>/ (leaf = t s e d g f c h m; "
              "neighbor = a path under the C4 root or a register reference like 'T col2'; meaning = one "
              "sentence in this context). Never overwrites; a second leaf on a word is a seam, kept.",
              {"type": "object",
               "properties": {"name": {"type": "string"}, "leaf": {"type": "string"},
                              "neighbor": {"type": "string"}, "meaning": {"type": "string"}},
               "required": ["name", "leaf", "neighbor", "meaning"]})
    def _reg(args):
        return register_word(args or {}, by)
