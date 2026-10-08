# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""rpc -- a dependency-free MCP stdio floor, stdlib only.

Deliberately the same shape as ``c4/mcp/c4-mcp.js``: JSON-RPC 2.0 over stdio,
newline-delimited, ``initialize`` / ``tools/list`` / ``tools/call``, protocol
version ``2024-11-05``, notifications swallowed, ``-32601`` otherwise.  Two
servers in one house that speak the protocol differently is a seam nobody
needs; this one is a Python transliteration of the Node one that already works.

No ``mcp`` package, no pip.  A server the keeper can read in one sitting and
run with the python that is already on the machine is worth more here than one
that needs a package manager to start.

Every tool result carries the store's ``mode`` word.  That is enforced at this
layer -- ``Server.call`` refuses to return a result that does not say what mode
produced it -- so a tool author cannot forget, and a silent JAILED result
cannot reach a caller even by accident.
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass, field
from typing import Callable

__all__ = ["Tool", "Server", "ToolError"]

PROTOCOL_VERSION = "2024-11-05"


class ToolError(RuntimeError):
    """A tool refused.  The message is shown to the caller verbatim."""


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    fn: Callable[[dict], dict]


@dataclass
class Server:
    name: str
    version: str
    tools: list[Tool] = field(default_factory=list)
    mode_fn: Callable[[], str] | None = None
    require_mode: bool = True

    def tool(self, name: str, description: str, schema: dict | None = None):
        def deco(fn):
            self.tools.append(Tool(name, description,
                                   schema or {"type": "object", "properties": {}},
                                   fn))
            return fn
        return deco

    # ----------------------------------------------------------- dispatch
    def list_tools(self) -> dict:
        return {"tools": [{"name": t.name, "description": t.description,
                           "inputSchema": t.schema} for t in self.tools]}

    def call(self, name: str, args: dict) -> dict:
        tool = next((t for t in self.tools if t.name == name), None)
        if tool is None:
            raise ToolError(f"no such tool: {name}")
        result = tool.fn(args or {})
        if not isinstance(result, dict):
            result = {"result": result}
        if self.require_mode and "mode" not in result:
            if self.mode_fn is None:
                raise ToolError(
                    f"{name} returned no mode and the server has no mode "
                    "source. Refusing: a result that does not say whether the "
                    "seat was SEATED, JAILED or NOTVISIBLE is the silent "
                    "fallback this server exists to prevent.")
            result["mode"] = self.mode_fn()
        return result

    # ------------------------------------------------------------- stdio
    def _handle(self, msg: dict) -> dict | None:
        mid = msg.get("id")
        method = msg.get("method", "")
        if not isinstance(method, str):
            # Valid JSON, invalid request. This raised AttributeError on the
            # next line, serve() swallowed it, and the client hung on an id
            # that was never answered -- the same silence the malformed-JSON
            # fix was written against, reached through well-formed JSON.
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32600,
                              "message": f"[mode: {self._mode()}] invalid "
                                         f"request: method must be a string, "
                                         f"got {type(method).__name__}"}}
        if method.startswith("notifications/"):
            return None
        if method == "initialize":
            return self._ok(mid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "tools/list":
            return self._ok(mid, self.list_tools())
        if method == "tools/call":
            params = msg.get("params") or {}
            try:
                out = self.call(params.get("name", ""), params.get("arguments") or {})
                text = json.dumps(out, indent=2, sort_keys=True, default=str)
                return self._ok(mid, {"content": [{"type": "text", "text": text}]})
            except ToolError as exc:
                return self._err(mid, f"REFUSED: {exc}")
            except Exception as exc:                      # noqa: BLE001
                return self._err(mid, f"{type(exc).__name__}: {exc}")
        # Even a protocol-level error says what state the store was in. This
        # path used to return a bare JSON-RPC error with no mode word, which is
        # the one thing this layer is supposed to make impossible.
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601,
                          "message": f"[mode: {self._mode()}] "
                                     f"method not found: {method}"}}

    def _mode(self) -> str:
        if self.mode_fn is None:
            return "NOTVISIBLE"
        try:
            return self.mode_fn()
        except Exception:                                  # noqa: BLE001
            return "NOTVISIBLE"

    @staticmethod
    def _ok(mid, result) -> dict:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def _err(self, mid, text: str) -> dict:
        """An error result, carrying the mode word like every other result.

        ``call`` enforced the mode word and these two handlers built their
        results themselves, so every exception path reached the wire with no
        mode at all -- and an exception is exactly when a caller most needs to
        know whether the seat was there. Found by an adversarial read,
        2026-09-14: a seat root that was a regular file produced a bare
        NotADirectoryError with nothing to say what state the store was in.
        """
        mode = self._mode()
        return self._ok(mid, {
            "isError": True,
            "content": [{"type": "text", "text": f"[mode: {mode}] {text}"}],
        })

    def serve(self, stdin=None, stdout=None) -> None:
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                # Answer, do not swallow. A client with an outstanding id used
                # to hang forever on a malformed line, which looks exactly like
                # a server that has died.
                stdout.write(json.dumps({
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700,
                              "message": f"parse error: {exc}"}}) + "\n")
                stdout.flush()
                continue
            if not isinstance(msg, dict):
                stdout.write(json.dumps({
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32600,
                              "message": "invalid request: not an object"}}) + "\n")
                stdout.flush()
                continue
            try:
                out = self._handle(msg)
            except Exception:                              # noqa: BLE001
                traceback.print_exc(file=sys.stderr)
                continue
            if out is not None:
                stdout.write(json.dumps(out) + "\n")
                stdout.flush()
