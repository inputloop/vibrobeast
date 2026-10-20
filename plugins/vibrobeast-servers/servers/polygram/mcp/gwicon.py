# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""gwicon -- the Python twin of gwicon.js: the ghostwheel status icon, same model, same bytes.

The model (glyphs, sizes, the name pattern) lives once, in gwicon.js between its STATIC MODEL
marker lines; this file reads it from there, so there is one model and two renderers written
apart.  tests/test_gwstatus.py runs both on the same input and requires identical output.

    render(letter, [(host, [(category, value), ...]), ...]) -> (svg, uri)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

JS = Path(__file__).with_name("gwicon.js")
_BEGIN = "// --- STATIC MODEL"
_END = "// --- END STATIC MODEL ---"


def load_model(js: Path = JS) -> dict:
    text = js.read_text(encoding="utf-8")
    seg = text[text.index(_BEGIN):text.index(_END)]
    return json.loads(seg[seg.index("`") + 1:seg.rindex("`")])


MODEL = load_model()
NAME = re.compile(MODEL["name"])


_SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")


def encode_uri_component(s: str) -> str:
    """JavaScript's encodeURIComponent, by hand (no urllib here: bin/tp2mt's claim that no server
    but the network ones imports a network library stays exact)."""
    return "".join(chr(b) if b in _SAFE else "%%%02X" % b for b in s.encode("utf-8"))


def _i32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


def hue(category: str) -> int:
    h = 0
    for ch in category:
        h = _i32(ord(ch) + (_i32(h << 5) - h))
    return abs(h) % 360


def _fill(pair) -> str:
    c = MODEL["config"]
    light = c["lightMin"] + (pair[1] * c["lightSpan"]) // 100
    return f"hsl({hue(pair[0])},{c['saturation']}%,{light}%)"


def _check(host: str, pairs) -> list:
    if pairs and isinstance(pairs[0], str):
        pairs = [pairs]
    pairs = [tuple(p) for p in pairs or []]
    if not pairs:
        raise ValueError(f"{host}: the callback gave no category/value pair")
    for cat, val in pairs:
        if not isinstance(cat, str) or not NAME.match(cat):
            raise ValueError(f"{host}: a pair must be [category, value] with a category matching {MODEL['name']}")
        if isinstance(val, bool) or not isinstance(val, int) or not 0 <= val <= 100:
            raise ValueError(f"{host}: value for {cat} must be a whole number 0..100")
    return pairs


def render(letter: str, hosts: list) -> tuple[str, str]:
    c = MODEL["config"]
    L = letter.upper() if isinstance(letter, str) and len(letter) == 1 else c["fallback"]
    glyph = MODEL["glyphs"].get(L) or MODEL["glyphs"][c["fallback"]]
    if not hosts:
        raise ValueError("give at least one host")
    names = [h for h, _ in hosts]
    for h in names:
        if not isinstance(h, str) or not NAME.match(h):
            raise ValueError(f"host {json.dumps(h)} does not match {MODEL['name']}")
    if len(set(names)) != len(names):
        dup = next(h for h in names if names.count(h) > 1)
        raise ValueError(f"host {dup} is listed twice")
    data = [_check(h, p) for h, p in hosts]

    lit = [(x, y) for y in range(c["gridY"]) for x in range(c["gridX"]) if glyph[y][x]]
    size = {1: (c["leaf"], c["leaf"])}
    for d in range(2, c["depth"] + 2):
        size[d] = (size[d - 1][0] * c["gridX"], size[d - 1][1] * c["gridY"])

    memo: set = set()
    defs: list = []

    def block(d: int, h: int) -> str:            # d >= 2; the id of the drawn block
        bid = f"g{d}-{h}"
        if bid in memo:
            return bid
        pairs = data[h]
        w, hh = size[d - 1]
        s = c["leaf"] - c["gap"]
        parts = []
        for i, (x, y) in enumerate(lit):
            if d == 2:
                parts.append(f'<rect x="{x * w}" y="{y * hh}" width="{s}" height="{s}" rx="1" '
                             f'fill="{_fill(pairs[i % len(pairs)])}"/>')
            else:
                parts.append(f'<use href="#{block(d - 1, h)}" x="{x * w}" y="{y * hh}"/>')
        defs.append(f'<g id="{bid}">' + "".join(parts) + "</g>")
        memo.add(bid)
        return bid

    w, hh = size[c["depth"]]
    body = "".join(f'<use href="#{block(c["depth"], i % len(hosts))}" x="{x * w}" y="{y * hh}"/>'
                   for i, (x, y) in enumerate(lit))
    W, H = size[c["depth"] + 1]
    words = "; ".join(h + " " + " ".join(f"{cat}:{val}" for cat, val in data[i])
                      for i, h in enumerate(names))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           f"<title>{L}: {words}</title><defs>{''.join(defs)}</defs>{body}</svg>")
    return svg, "data:image/svg+xml;utf8," + encode_uri_component(svg)
