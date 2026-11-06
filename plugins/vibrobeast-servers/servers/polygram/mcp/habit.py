# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""habit -- the one permissions-shaped row on the settings page: "Habit: Extra Checks for potentially unsafe things".

Corwin, 2026-11-04 (c4 q/2026-11-04-wedrince): *"putting that habit BACK as the principle remaining 'permissions'
shaped control left in the panel.  Mostly we want people to just type ... 'Habit: Extra Checks for potentially
unsafe things' (With this set, Your Agent (Claude, or as set above), asks extra questions, preplans complex
sequences as scripted actions where possible, and uses integrated permissions controls.  Let's go ahead and
default it on."*

Why it is a row and not a habit of the agent's own: can-pony (c4 bin/can-pony) found that an extra question whose
only home is the agent's habit is the one rule a compaction never loses, and the one that is nobody's choice.
Put on the page, the habit is the person's: chosen, visible, and undone by one switch.

ON (the default, and whatever the page does not say plainly):
  * key_run asks for a confirmation code the person sees, run by run, as before (the integrated controls);
  * the plan door is open: a written plan is approved once, with a code, and its steps then run with none
    (plans.py; keys.plans on or off still decides, when the keeper has set it);
  * the Ghostwheel asks before a name lookup or a new host key (GW_LOOKUPS_ALWAYS, GW_KNOWN_HOSTS_ALWAYS
    still say "without asking" for one machine's own configuration).
OFF (the person's own act, on the settings page and only there):
  * key_run runs with no code of ours: the app's own approval of each key_run call is the yes, and the
    result names the habit as what let it run.  Still: a push goes through the push door, a group's ORG.md
    "must not" on standing yeses brings the code back, a refused shape is refused, and the key's usage
    constraints are said in every result;
  * the plan door is moot (nothing asks a code to cover);
  * the Ghostwheel looks names up and takes a host's first key without asking; a pinned key that does not
    match is refused, as always.
Neither the platform's own asks of the agent (a download, sending a message, a purchase, a permanent delete)
nor a rule the person gave in words is touched by this row: it governs only the extension's own checks.

THE WRITER.  Only the page writes it (VIBROBEAST_HABIT_CHECKS, a boolean field).  No preference, defaults
file or chat turn reads or sets it: a habit a conversation could switch off is the habit a prompt could
switch off.  A value that is not plainly on or off reads as on, and says so.
"""

from __future__ import annotations

import os
import sys

ENV = "VIBROBEAST_HABIT_CHECKS"
TITLE = "Habit: Extra Checks for potentially unsafe things"
ON_WORDS = ("true", "1", "on", "yes")
OFF_WORDS = ("false", "0", "off", "no")


def state(environ: dict | None = None) -> tuple[bool, str]:
    """(on, where that came from, in words)."""
    env = os.environ if environ is None else environ
    raw = env.get(ENV)
    if raw is None or not raw.strip() or raw.strip().startswith("${"):
        return True, "on (its default: the settings page left it as it ships)"
    v = raw.strip().lower()
    if v in OFF_WORDS:
        return False, "off (the settings page)"
    if v in ON_WORDS:
        return True, "on (the settings page)"
    return True, f"on (the settings page said {raw.strip()!r}, which is not plainly on or off, so it reads as on)"


def on(environ: dict | None = None) -> bool:
    return state(environ)[0]


def words(environ: dict | None = None) -> str:
    """One sentence for status tools: what the row is, its state, and what that state does here."""
    is_on, where = state(environ)
    if is_on:
        does = ("key_run asks for a code you see, a written plan can be approved once (the plan door), and the "
                "Ghostwheel asks before a lookup or a new host key")
    else:
        does = ("key_run runs on the app's own approval of each call, with no code of ours (a push still goes "
                "through the push door, and a group's ORG.md can bring the code back); the Ghostwheel does not ask "
                "before a lookup or a new host key")
    return f"{TITLE}: {where}. {does}."


def ran_without_code() -> str:
    """What a key_run result says when the habit, not a code, let it run."""
    return ("habit-off yes (the settings page's Habit row is off: no code of ours; the app's own approval of this "
            "key_run call was the yes)")


def _main(argv: list[str]) -> int:
    """python3 -m polygram.mcp.habit --state   ON or OFF, a tab, and where that came from, for this environment.
    python3 -m polygram.mcp.habit --table   the same for each value read from stdin, one per line, in order; the
                                            line (unset) means the variable is not set, (empty) that it is set to
                                            nothing (tests/habit-spec.pl reads the table)."""
    if argv[1:] == ["--state"]:
        is_on, where = state()
        print(("ON" if is_on else "OFF") + "\t" + where)
        return 0
    if argv[1:] == ["--table"]:
        for line in sys.stdin.read().split("\n"):
            if line == "":
                continue
            is_on, where = state({} if line == "(unset)" else {ENV: "" if line == "(empty)" else line})
            print(("ON" if is_on else "OFF") + "\t" + where)
        return 0
    if argv[1:] in ([], ["--words"]):
        print(words())
        return 0
    print("usage: python3 -m polygram.mcp.habit [--state | --table | --words]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
