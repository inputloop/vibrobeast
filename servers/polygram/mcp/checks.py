# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""checks -- the on-open panel: what seat_mode and span_start report beside their own answer.

Each check is behind a preference (prefs.KNOWN), on by default, and each is cheap: freshness reads
two MANIFESTs, soft skills lists a few directories. A check that cannot run says why in one line
rather than failing the call that carries it -- these ride along; they never gate.
"""

from __future__ import annotations

from . import prefs as _prefs


def run() -> dict:
    out: dict = {}
    try:
        if _prefs.on("freshness.auto"):
            from . import freshness as _f
            shelf = _prefs.get("freshness.shelf").strip() or None
            r = _f.report({"shelf": shelf} if shelf else {})
            out["freshness"] = r["say"] if r["verdict"] != "UNKNOWN" else "UNKNOWN: " + r["say"].removeprefix("UNKNOWN: ")
        else:
            out["freshness"] = "off (pref freshness.auto)"
    except Exception as exc:                               # noqa: BLE001 -- a check never sinks its carrier
        out["freshness"] = f"could not run: {exc}"
    try:
        if _prefs.on("softskills.auto"):
            from . import softskills as _s
            out["soft_skills"] = _s.summary()
        else:
            out["soft_skills"] = "off (pref softskills.auto)"
    except Exception as exc:                               # noqa: BLE001
        out["soft_skills"] = f"could not run: {exc}"
    return out
