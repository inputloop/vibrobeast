#!/usr/bin/env python3
# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.  It comes with ABSOLUTELY NO WARRANTY.  You should have
# received a copy of the licence with this program -- see COPYING at the top
# of this plugin; if not, see <https://www.gnu.org/licenses/>.
"""launch.py -- start one of this plugin's MCP servers, owing the host nothing.

Until 2026-09-23 the default mint launched ``python3 -m polygram.mcp NAME``
and told the app where the package was with an ``env`` block,
``PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/servers``.  Claude Desktop refuses to
prepare a plugin server whose env names PYTHONPATH (its log: ``env declares
reserved variable name "PYTHONPATH"``), and the reader sees only
``not_started / could_not_prepare``.

This file exists so that nothing has to be carried by an env block.  A python
file always knows where it is -- ``__file__`` -- so it puts its own directory
on ``sys.path`` and sets ``sys.dont_write_bytecode`` itself, then hands over
to the same entry point ``-m polygram.mcp`` uses.  The default mint names this
file as ``${CLAUDE_PLUGIN_ROOT}/servers/launch.py`` in ``args``; the
``--self-locating`` mint names it by absolute path so that no ``${...}`` is
left anywhere.

    python3 <this file> mentcached     the server, on stdio
    python3 <this file> --list         every server and its tools

It is not cleverness for its own sake.  Three servers have reported
``not_started / could_not_prepare`` on the keeper's desktop since 2026-09-16;
the two causes the mint could name have both been eliminated, with receipts,
and one host-expanded substitution was left.  This is the arm that removes it,
so that installing it says something either way.
"""

import os
import sys

# FIRST, before anything beside us is imported.  The default mint says this in
# .mcp.json as PYTHONDONTWRITEBYTECODE=1; this mint has no env block at all, so
# the launcher has to say it itself.  __pycache__ is the one directory python
# executes without being asked, and check.sh is right to treat a .pyc it did
# not mint as hostile -- which it cannot do if we leave one lying about.
sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from polygram.mcp.__main__ import main   # noqa: E402 -- after sys.path, on purpose

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
