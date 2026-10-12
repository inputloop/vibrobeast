# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""hub -- the seven servers behind one stdio door, for the Claude Desktop extension.

A desktop extension (.mcpb) carries ONE server.  The plugin carries seven.  Rather than write a
further server that does what the seven do, the hub starts each of the seven exactly as the plugin
does (``python -m polygram.mcp NAME``), asks each for its tools, and answers ``tools/list`` with
all of them.  A ``tools/call`` goes to the server that listed that tool, and its answer comes back
byte for byte.  So the extension and the plugin run the same code, and the parity test is a
comparison, not a hope.

    python -m polygram.mcp hub              serve the seven on stdio
    python -m polygram.mcp hub --list       each server, its state, and its tools; then exit

The switches.  The extension's settings page fills environment variables (TAVERN_ON, C4_ON,
LLAMABRIDGE_ON, TAVERN_DATA, ...).  A field left empty can reach us as an empty string or as the
template text itself (``${user_config.tavern_data}``); the specification does not say which.  The
hub drops both before any server sees them, so an unset field means "find it yourself", which is
what the servers already do.  A switch set to off (``false``) is OFF even when prefs.tsv says on:
the settings page is the one place the extension's owner looks.

One tool is the hub's own: ``vibrobeast_status`` says which servers started, how many tools each
gave, any tool name two servers both claimed (the first keeps it), and which switches it saw.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from . import SERVERS
from .rpc import PROTOCOL_VERSION

VERSION = "1.0"
#: Settings-page variables the hub cleans before a server sees them.
SWITCH_VARS = ("TAVERN_ON", "C4_ON", "LLAMABRIDGE_ON", "GW_ON", "GW_LOOKUPS", "GW_LOOKUPS_ALWAYS",
               "GW_KNOWN_HOSTS", "GW_KNOWN_HOSTS_ALWAYS")
#: Reported as "set" only, like the paths; GW_PASSWORD and VIBROBEAST_API_TOKEN are secrets.
PATH_VARS = ("VIBROBEAST_SSH_KEY", "VIBROBEAST_API_TOKEN", "GW_HOSTS", "GW_DOMAIN", "GW_METHOD",
             "GW_PORT", "GW_AUTH", "GW_USER", "GW_PASSWORD", "GW_AUTH_METHOD", "GW_REFRESH",
             "GW_HOSTS_FILE",
             "TAVERN_DATA", "TAVERN_AS", "C4_ROOT", "MENTCACHED_SEAT", "OLLAMA_HOST",
             "PERSONA_ROOT", "MENTCACHED_PREFS")
START_TIMEOUT = float(os.environ.get("VIBROBEAST_HUB_START_TIMEOUT", "30"))
CALL_TIMEOUT = float(os.environ.get("VIBROBEAST_HUB_CALL_TIMEOUT", "900"))


def unset_template(value: str | None) -> bool:
    """True when a settings field was left empty: missing, blank, or the template text itself."""
    v = (value or "").strip()
    return not v or "${" in v


def clean_env(env: dict | None = None) -> tuple[dict, dict]:
    """The environment the seven servers get, and a report of what was dropped and why."""
    env = dict(os.environ if env is None else env)
    seen: dict = {}
    for k in SWITCH_VARS + PATH_VARS:
        if k not in env:
            continue
        if unset_template(env[k]):
            seen[k] = "unset (dropped)"
            del env[k]
        else:
            seen[k] = env[k] if k in SWITCH_VARS else "set"
    here = str(Path(__file__).resolve().parents[2])
    pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = here + (os.pathsep + pp if pp else "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env, seen


class Child:
    """One of the seven, started as the plugin starts it, spoken to over pipes."""

    def __init__(self, name: str, env: dict):
        self.name = name
        self.tools: list[dict] = []
        self.state = "starting"
        self.why = ""
        self._next = 0
        self._lock = threading.Lock()
        self._waiting: dict = {}
        try:
            self.proc = subprocess.Popen(
                [sys.executable, "-m", "polygram.mcp", name], env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None,
                encoding="utf-8", bufsize=1)
        except OSError as exc:
            self.proc = None
            self.state, self.why = "failed", f"could not start: {exc}"
            return
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue                     # a stray print; the servers log to stderr
            q = self._waiting.pop(msg.get("id"), None) if isinstance(msg, dict) else None
            if q is not None:
                q.put(msg)
        self.state = "exited" if self.state != "failed" else self.state
        for q in list(self._waiting.values()):
            q.put(None)
        self._waiting.clear()

    def request(self, method: str, params: dict | None, timeout: float) -> dict | None:
        if self.proc is None or self.proc.poll() is not None:
            return None
        with self._lock:
            self._next += 1
            mid = f"hub-{self._next}"
            q: queue.Queue = queue.Queue(1)
            self._waiting[mid] = q
            try:
                self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": mid, "method": method,
                                                  "params": params or {}}) + "\n")
                self.proc.stdin.flush()
            except (OSError, ValueError):
                self._waiting.pop(mid, None)
                return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            self._waiting.pop(mid, None)
            return {"error": {"message": f"{self.name} did not answer {method} in {timeout:g}s"}}

    def notify(self, method: str) -> None:
        try:
            self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError, AttributeError):
            pass

    def start(self) -> None:
        if self.proc is None:
            return
        r = self.request("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                                        "clientInfo": {"name": "vibrobeast-hub", "version": VERSION}},
                         START_TIMEOUT)
        if not r or "result" not in r:
            self.state = "failed"
            self.why = (r or {}).get("error", {}).get("message", "") or "no answer to initialize"
            return
        self.notify("notifications/initialized")
        r = self.request("tools/list", {}, START_TIMEOUT)
        if not r or "result" not in r:
            self.state = "failed"
            self.why = (r or {}).get("error", {}).get("message", "") or "no answer to tools/list"
            return
        self.tools = list(r["result"].get("tools") or [])
        self.state = "running"

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:                                   # noqa: BLE001
            self.proc.kill()


STATUS_TOOL = {
    "name": "vibrobeast_status",
    "description": ("Which of the extension's servers started, how many tools each gave, any "
                    "tool name two servers both claimed, and which settings-page switches were seen. "
                    "Sends nothing anywhere."),
    "inputSchema": {"type": "object", "properties": {}},
}


class Hub:
    def __init__(self, names=SERVERS, env: dict | None = None):
        self.env, self.seen = clean_env(env)
        self.children = [Child(n, self.env) for n in names]
        threads = [threading.Thread(target=c.start) for c in self.children]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.route: dict = {}
        self.clashes: list = []
        for c in self.children:
            for t in c.tools:
                if t["name"] in self.route or t["name"] == STATUS_TOOL["name"]:
                    self.clashes.append({"tool": t["name"], "kept_by": self.route.get(t["name"], "hub").name
                                         if t["name"] in self.route else "hub", "also": c.name})
                    continue
                self.route[t["name"]] = c

    def tools(self) -> list:
        out = [STATUS_TOOL]
        for c in self.children:
            out += [t for t in c.tools if self.route.get(t["name"]) is c]
        return out

    def status(self) -> dict:
        return {"servers": [{"name": c.name, "state": c.state, "tools": len(c.tools),
                             **({"why": c.why} if c.why else {})} for c in self.children],
                "clashes": self.clashes, "switches_seen": self.seen,
                "tools_total": len(self.tools())}

    def handle(self, msg: dict) -> dict | None:
        mid, method = msg.get("id"), msg.get("method")
        if not isinstance(method, str):
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32600, "message": "invalid request"}}
        if method.startswith("notifications/"):
            return None
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
                "serverInfo": {"name": "vibrobeast", "version": VERSION}}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": mid, "result": {"tools": self.tools()}}
        if method == "tools/call":
            p = msg.get("params") or {}
            name = p.get("name", "")
            if name == STATUS_TOOL["name"]:
                text = json.dumps(self.status(), indent=2, sort_keys=True)
                return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}}
            c = self.route.get(name)
            if c is None:
                return {"jsonrpc": "2.0", "id": mid, "result": {"isError": True, "content": [
                    {"type": "text", "text": f"REFUSED: no such tool: {name}"}]}}
            r = c.request("tools/call", {"name": name, "arguments": p.get("arguments") or {}}, CALL_TIMEOUT)
            if r is None:
                return {"jsonrpc": "2.0", "id": mid, "result": {"isError": True, "content": [
                    {"type": "text", "text": f"the {c.name} server has stopped; restart the extension"}]}}
            out = {"jsonrpc": "2.0", "id": mid}
            if "result" in r:
                out["result"] = r["result"]
            else:
                out["error"] = r.get("error") or {"code": -32603, "message": "no result"}
            return out
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}

    def serve(self, stdin=None, stdout=None) -> None:
        stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
        lock = threading.Lock()

        def answer(msg):
            out = self.handle(msg)
            if out is not None:
                with lock:
                    stdout.write(json.dumps(out) + "\n")
                    stdout.flush()

        workers = []
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                with lock:
                    stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {
                        "code": -32700, "message": f"parse error: {exc}"}}) + "\n")
                    stdout.flush()
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("method") == "tools/call":
                # a long delegate_task must not hold up a quick seat_read behind it
                t = threading.Thread(target=answer, args=(msg,), daemon=True)
                t.start()
                workers.append(t)
            else:
                answer(msg)
        for t in workers:
            t.join(timeout=CALL_TIMEOUT)
        for c in self.children:
            c.stop()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    hub = Hub()
    if argv and argv[0] == "--list":
        st = hub.status()
        print(json.dumps(st, indent=2, sort_keys=True))
        for t in hub.tools():
            print(f"    {t['name']}")
        for c in hub.children:
            c.stop()
        return 0 if all(s["state"] == "running" for s in st["servers"]) else 1
    hub.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
