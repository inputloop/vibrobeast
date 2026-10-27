# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""llamabridge -- Bryant Frankford's Llama Bridge, served from the vibrobeast plugin, off until
you turn it on.

Llama Bridge (llama_bridge.py beside this file, v1.4.0, byte for byte as Bryant published it; see
NOTICE-llama_bridge) hands subtasks Claude delegates to local Ollama models.  That is an outward
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
    from .rpc import env_switch
    sw = env_switch("LLAMABRIDGE_ON")
    if sw is not None:
        return sw
    try:
        from . import prefs
        return prefs.on("llamabridge.on")
    except Exception:
        return False


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
                           "computer); the log is kept in ~/.mentcached/llama-bridge.db",
                "sent": "nothing"}
    return srv


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not is_on():
        build().serve()
        return 0
    # Two things the wrapper sets around Bryant's code, which stays byte for byte (the 2026-10-19 audit, HOLD
    # item 9).  (a) A loopback Ollama is reached directly: with HTTP_PROXY set, urllib on Linux/3.13 did not
    # bypass the proxy for 127.0.0.1, so delegated prompts could leave for the proxy.  no_proxy names the
    # loopback here, for this process only.  (b) The log keeps whole prompts and answers; it is the person's
    # own file and is made 0600 before the bridge opens it, where the platform has modes.
    import os
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
    llama_bridge.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
