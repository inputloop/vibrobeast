# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
# SPDX-License-Identifier: GPL-3.0-or-later
"""scrub -- the output scrubbers key_run may use, one of which is chosen when the package is minted.

Why (2026-10-22, his 22:49 answer): "output scrubbing adaptor is build time fixed (but not absolutely
required to be an inline thing: look at how we treated `he2ma` in allowing indirection away from
RECIPE and README ...)".  The emacs recipe's tools carry what they were BUILT against (c4mark's
EXPECT, a hash) and check the document beside them at run time, degrading on a ladder.  The same
shape here:

  at mint      polygram.mcpb writes server/polygram/mcp/SCRUBBER: the chosen scrubber's NAME and the
               sha256 of this file as it was minted (VIBROBEAST_SCRUBBER picks the name; default
               "spellings").
  at run       keys.scrubber() reads SCRUBBER beside it:
                 present, the name known, this file's bytes the minted ones  -> that scrubber (minted)
                 present, but the name unknown or this file changed         -> the FLOOR, and says why
                 absent (a source checkout, the tests)                      -> DEFAULT (source)
  the FLOOR    keys.py's own masking of every spelling, kept inline on purpose.  The recipe's
               back-check may go quiet when its document is moved away (an opt-out, by design); a
               scrubber that went quiet would print a key, so here the ladder never ends in nothing.

A scrubber is mask(text, secrets, label) -> text.  Add one by name below; choose it at mint.
"""

from __future__ import annotations

from urllib.parse import quote, quote_plus

DEFAULT = "spellings"


def spellings(s: str) -> list[str]:
    """The ways a value can come back in a program's output: as given, with forward slashes, with
    backslashes doubled (a program quoting it), with backslashes for slashes.  Longest first."""
    v = {s, s.replace("\\", "/"), s.replace("\\", "\\\\"), s.replace("/", "\\")}
    return sorted((x for x in v if len(x) >= 4), key=len, reverse=True)


def mask_spellings(text: str, secrets: list[str], label: str) -> str:
    for s in secrets:
        for sp in spellings(s or ""):
            text = text.replace(sp, label)
    return text


def mask_spellings_and_url(text: str, secrets: list[str], label: str) -> str:
    """spellings, and each value as a URL would carry it (a program echoing the URL it fetched)."""
    more = [x for s in secrets if s for x in (quote_plus(s), quote(s, safe=""))]
    return mask_spellings(text, [*secrets, *more], label)


SCRUBBERS = {"spellings": mask_spellings, "spellings+url": mask_spellings_and_url}
