# polygram -- gated agent-skill synthesis.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later; https://github.com/inputloop.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""llamabridge -- Bryant Frankford's Llama Bridge, served from the vibrobeast plugin, off until
you turn it on.

Llama Bridge (llama_bridge.py beside this file, 1.4.0-vb.2: Bryant's 1.4.0 with the changes NOTICE-llama_bridge
names, for him to merge back as he thinks best) hands subtasks Claude delegates to local Ollama models.  That is an outward
path for whatever is in the prompt, so this plugin does not open it on install: until the
preference ``llamabridge.on`` is ``on`` (``pref_set llamabridge.on on``, then restart the plugin)
or ``LLAMABRIDGE_ON=1`` is in the environment, this server answers one tool, ``llamabridge_status``,
which says it is off and what turning it on means, and sends nothing anywhere.

When on, it runs Llama Bridge's own MCP mode, with its log database at
``~/.mentcached/llama-bridge.db`` (not inside the plugin folder, which may be read-only), and
Ollama at ``OLLAMA_HOST`` (default ``http://127.0.0.1:11434``).  Point OLLAMA_HOST at another
machine and the prompts go there: that is your choice, and the Privacy Policy says so.

Field notes from using it (2026-10-04): a delegation that takes longer than the desktop bridge's
call limit (about a minute) cannot come back through ``delegate_task``; use ``delegate_async``
and poll ``delegate_result``.  The same day showed the other half: a session that waits on
the model in silence has stopped working with its person.  Say what goes before it goes, never
two polls without a line to the person, and write each job id where the next session can find
it (the altorewired skill, grown 03).  And a third: Llama Bridge gives each generate call 600 s
(``ollama_generate``), and on one GPU Ollama runs background jobs one after another, so four
48-word batches sent at once all timed out, the queued ones while still waiting their turn.  Send
one job at a time, sized to finish well inside 600 s on the slowest model you use.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

VERSION = "0.1.0"
DB = Path.home() / ".mentcached" / "llama-bridge.db"


def is_on() -> bool:
    """Open only when doors.py says so: the broad setting (doors.profile), then the environment, then the
    person's row, then the layered default (2026-10-29, F3)."""
    from . import doors
    return doors.is_open("llamabridge.on")


def build():
    """The server while it is off: one tool, which says so and sends nothing."""
    from .rpc import Server
    srv = Server(name="llamabridge", version=VERSION, require_mode=False)

    @srv.tool("llamabridge_status",
              "Whether Llama Bridge is on, and what turning it on means. While it is off, "
              "this is the only tool, and nothing is sent anywhere.")
    def _status(_args):
        return {"state": "OFF",
                "why": "Llama Bridge sends the prompts Claude delegates to an Ollama server. "
                       "This plugin does not open that path on install.",
                "turn_on": "pref_set llamabridge.on on (the mentcached server), then restart "
                           "the plugin; or set LLAMABRIDGE_ON=1 in the environment",
                "when_on": "prompts go to OLLAMA_HOST (default http://127.0.0.1:11434, this "
                           "computer); the log is kept in ~/.mentcached/llama-bridge.db, without the words "
                           "of prompts or answers unless llamabridge.keep_prompts is on",
                "doors": "door_list (the mentcached server) shows this door beside every other one",
                "sent": "nothing"}
    return srv




def keep_prompts() -> bool:
    from . import doors
    return doors.is_open("llamabridge.keep_prompts")


def guard(lb, keep: bool | None = None, stored: str | None = None, log=None) -> dict:
    """Set Llama Bridge's own two switches from the doors (2026-10-29).  Since 1.4.0-vb.2 the switches live in
    Bryant's module (KEEP_PROMPTS, STORED_HOST, read through CFG at every call), so the plugin no longer
    patches around his functions: it says what the person chose, and his code does the rest.

    (1) keep_prompts: the event log, the jobs' prompts and the answer cache keep words only when the door
        llamabridge.keep_prompts is open.  An async job's answer stays in the jobs table, since
        delegate_result reads it from there.  Rows written before are left as they were; door_list counts them.
    (2) stored_host: an ollama_host row in the bridge's own database is used only when the door
        llamabridge.stored_host is open ("use"); otherwise prompts go to OLLAMA_HOST, even for a row
        written while the bridge runs.
    Returns what was done, in words, for the caller and the tests."""
    from . import doors
    keep = keep_prompts() if keep is None else keep
    use = doors.is_open("llamabridge.stored_host")
    lb.CFG["keep_prompts"] = bool(keep)
    lb.CFG["stored_host"] = "use" if use else "ask"
    done = {"keep_prompts": bool(keep), "stored_host": "", "stored_host_used": False}
    stored = lb.cfg_get("ollama_host") if stored is None else stored
    env_host = lb.CFG["ollama"].rstrip("/")
    if stored and stored.rstrip("/") != env_host:
        done["stored_host"] = stored
        done["stored_host_used"] = use
        if not use and log:
            log(f"llamabridge: a stored ollama_host row points at {stored}; not used (llamabridge.stored_host "
                f"is ask). Prompts go to {env_host}. door_list says more.")
    return done

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # --ollama-host on the command line is OLLAMA_HOST by another name: fold it in before the door is read, so
    # doors.profile=local sees where prompts would go (the 2026-10-29 independent read, item 5)
    for i, a in enumerate(argv):
        if a == "--ollama-host" and i + 1 < len(argv):
            os.environ["OLLAMA_HOST"] = argv[i + 1]
        elif a.startswith("--ollama-host="):
            os.environ["OLLAMA_HOST"] = a.split("=", 1)[1]
    if not is_on():
        build().serve()
        return 0
    # Two things the wrapper sets around Bryant's code, which stays byte for byte (the 2026-10-19 audit, HOLD
    # item 9).  (a) A loopback Ollama is reached directly: with HTTP_PROXY set, urllib on Linux/3.13 did not
    # bypass the proxy for 127.0.0.1, so delegated prompts could leave for the proxy.  no_proxy names the
    # loopback here, for this process only.  (b) The log keeps whole prompts and answers; it is the person's
    # own file and is made 0600 before the bridge opens it, where the platform has modes.
    for k in ("no_proxy", "NO_PROXY"):
        have = [x for x in os.environ.get(k, "").split(",") if x]
        for lo in ("127.0.0.1", "localhost", "::1"):
            if lo not in have:
                have.append(lo)
        os.environ[k] = ",".join(have)
    from . import llama_bridge
    DB.parent.mkdir(parents=True, exist_ok=True)
    try:
        DB.touch(mode=0o600, exist_ok=True)
        os.chmod(DB, 0o600)
    except OSError:
        pass   # Windows has no such mode; the folder under the profile is the person's own
    sys.argv = ["llama_bridge", "mcp", "--db", str(DB)] + argv
    # Bryant's main() reads --db and sets CFG before the first query; set CFG here too, so guard() reads
    # the same database main() will use.
    llama_bridge.CFG["db"] = str(DB)
    guard(llama_bridge, log=lambda m: sys.stderr.write(m + "\n"))
    llama_bridge.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
