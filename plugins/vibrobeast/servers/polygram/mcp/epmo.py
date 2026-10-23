# polygram -- epmo: the capability lens over MCP, a second reader of C4's r/epmo (Python beside bin/ep1mo's sh+awk).
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
"""EPMO (2026-10-19). Corwin: EPMO is "an infact transforming component in C4 (the REGISTRY under C4_ROOT)"
that can "effect the same transformations in context a stream of C4 ASSY to implement tokenization concerns
(via meantcached, for us, but nominally anywhere C4 is written/spoken)".

So: the tokenization runs here, where the memory server already sits. A stream of text comes in; every word
that is a placed project key comes back with its lens placement (who cares, how much, why, whose runtime, what
change costs) and its ASSY line. This module READS ``r/epmo/PLACEMENTS.tsv`` itself, in Python, and writes the
ASSY line the same way C4's ``bin/ep1mo assy`` does, so the two readers can be held to agree (the seams law:
agreement is evidence, either one alone is data). It writes nothing.

ROOT: ``EPMO_DIR`` names the data folder; else the C4 root that ``words.root()`` finds, and its ``r/epmo``.
Two tools: ``epmo_place`` and ``epmo_tokens``. Both read-only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import words as _words
from .rpc import ToolError

COLS = ["key", "who", "cares", "stance", "band", "layer", "coupling", "frame", "conf", "basis", "horizon"]
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def data_dir() -> tuple[Path | None, str]:
    """The r/epmo folder in play, and where the choice came from."""
    env = (os.environ.get("EPMO_DIR") or "").strip()
    if env:
        p = Path(env).expanduser()
        return (p, "$EPMO_DIR") if (p / "PLACEMENTS.tsv").is_file() else (None, f"$EPMO_DIR {p} has no PLACEMENTS.tsv")
    c4, why = _words.root()
    if c4 is None:
        return None, why
    p = c4 / "r" / "epmo"
    return (p, f"{why} -> r/epmo") if (p / "PLACEMENTS.tsv").is_file() else (None, f"{c4} has no r/epmo/PLACEMENTS.tsv")


def placements(d: Path) -> dict[str, dict]:
    """Every placement row, keyed by project. A row of the wrong width is skipped, never guessed at."""
    out: dict[str, dict] = {}
    for line in (d / "PLACEMENTS.tsv").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("key\t"):
            continue
        cells = line.split("\t")
        if len(cells) != len(COLS):
            continue
        out[cells[0]] = dict(zip(COLS, cells))
    return out


def assy_line(p: dict) -> str:
    """The same line bin/ep1mo assy prints: m/t TERMs, each followed by its lens value."""
    return (f"PROJECT {p['key']} REGISTRY epmo TAG {p['who']} MEASURE {p['stance']} "
            f"MODEL {p['band']} OBJECT {p['layer']} ROUTER {p['frame']}")


def _need() -> tuple[Path, dict[str, dict], str]:
    d, why = data_dir()
    if d is None:
        raise ToolError(f"NOT CHECKED: no EPMO data ({why})")
    return d, placements(d), why


def place(args: dict) -> dict:
    key = (args.get("key") or "").strip()
    if not key:
        raise ToolError("epmo_place needs a key (a rostered project, e.g. pmo)")
    d, pl, why = _need()
    if key not in pl:
        return {"key": key, "placed": False, "root": str(d), "say": f"{key}: no placement in {d} ({len(pl)} placed)"}
    p = pl[key]
    return {"key": key, "placed": True, "root": str(d), "from": why, "assy": assy_line(p),
            **{k: p[k] for k in COLS if k != "key"}}


def tokens(args: dict) -> dict:
    """A stream of text, tokenized: the placed project keys in it, in order of first use, each with its ASSY line."""
    text = args.get("text") or ""
    d, pl, why = _need()
    seen: list[str] = []
    words = WORD.findall(text)
    for w in words:
        k = w.lower().rstrip(".-")
        if k in pl and k not in seen:
            seen.append(k)
    return {"root": str(d), "from": why, "words": len(words), "placed": len(seen),
            "lines": [assy_line(pl[k]) for k in seen],
            "tags": [{"key": k, "who": pl[k]["who"], "stance": pl[k]["stance"], "band": pl[k]["band"],
                      "frame": pl[k]["frame"], "horizon": pl[k]["horizon"]} for k in seen],
            "say": f"{len(seen)} placed project(s) in {len(words)} words; placements are judged, never measures"}


def register(srv, by: str) -> None:   # noqa: ARG001 -- read-only; by is kept for the common signature
    @srv.tool("epmo_place",
              "Where one project sits on the EPMO capability lens (C4's r/epmo): who cares, how much, why, "
              "whose runtime, what change costs, and its C4 ASSY line. Read-only; the POSIX twin is c4/bin/ep1mo place.",
              {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]})
    def _place(args):
        return place(args or {})

    @srv.tool("epmo_tokens",
              "Tokenize a stream of text for EPMO: every placed project key in it, in order of first use, with "
              "its lens tags and its C4 ASSY line (the same line c4/bin/ep1mo assy prints). Read-only.",
              {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]})
    def _tokens(args):
        return tokens(args or {})
