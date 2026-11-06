"""housenames -- the three names of the house persona, read from the settings page's Character Names section.

outward: where people read it (the Tavern, chat, web pages, formal writing); never git or GitHub.
inward:  our own records (notes, memory, bylines).          host: where a host or tool talks to it.
His word 2026-11-05 11:32 (wire-name), verbatim in c4 q/2026-11-05-gums/PROMPT-2026-11-05-1132.md.

Copyright 2026 INPUTLOOP; GPL-3.0-or-later OR LGPL-3.0-or-later.  Mentat (for Corwin, claude-opus-5-5)
"""
import os

DEFAULTS = {"inward": "Mentat", "host": "Vibrobeast"}


def name(which: str) -> tuple[str, str]:
    """(name, where it came from) for outward, inward or host."""
    if which == "outward":
        from polygram.mcp import tavernface
        return tavernface.agent_and_source()
    var = {"inward": "VIBROBEAST_HOUSE_INWARD", "host": "VIBROBEAST_HOUSE_HOST"}[which]
    v = os.environ.get(var, "").strip()
    return (v, var) if v else (DEFAULTS[which], "the default (Character Names: house persona, %s, left empty)" % which)
