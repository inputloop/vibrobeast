#!/usr/bin/env python3
# fake_ollama -- a stand-in Ollama server that answers the calls Llama Bridge makes and writes down
# every request it gets, so you can see what the bridge sends before you have a GPU, a model, or
# the patience to wait for one.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.  It is distributed WITHOUT ANY
# WARRANTY; see <https://www.gnu.org/licenses/>.
"""fake_ollama -- a stand-in Ollama for trying Llama Bridge, stdlib only.

  python3 fake_ollama.py [--port 11435] [--log requests.jsonl] [--delay SECONDS]
                         [--models models.json] [--spill MODEL=PERCENT]
  then:  OLLAMA_HOST=http://127.0.0.1:11435  (for the bridge, or bridge_smoke.py --host ...)

It answers /api/version, /api/tags, /api/ps, /api/show, /api/generate (plain and streamed),
/api/pull and /api/delete.  Answers are made up: a JSON answer when the request asks for JSON,
otherwise a sentence that echoes the prompt.  A model that "can think" sends thinking text back
unless the request says think: false, the way Ollama does.  Every request is printed in one line
of words on stderr and, with --log, kept as one JSON object per line.

What it does NOT do: run a model, measure a GPU, or know how fast anything will be.  /api/ps says
a model is all in GPU memory unless you tell it otherwise with --spill MODEL=PERCENT, so you can
see what the bridge says about a model that spilled.  The model table (MODELS below, or
--models FILE with the same shape) is invented for testing: sizes and windows are close to the
real gemma4:12b and a small model, not read from anywhere.
"""
import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS = {
    "gemma4:12b": {"size": 7_700_000_000, "family": "gemma4", "param": "11.9B",
                   "capabilities": ["completion", "vision", "thinking"],
                   "context_length": 262144, "parameters": ""},
    "gemma4:12b-8k": {"size": 7_700_000_000, "family": "gemma4", "param": "11.9B",
                      "capabilities": ["completion", "vision", "thinking"],
                      "context_length": 262144, "parameters": "num_ctx 8192"},
    "llama3.2:3b": {"size": 2_000_000_000, "family": "llama", "param": "3.2B",
                    "capabilities": ["completion", "tools"],
                    "context_length": 131072, "parameters": ""},
}


class FakeOllama(BaseHTTPRequestHandler):
    """The handler.  Class attributes are the server's state; tests read and reset them."""
    models = MODELS
    log = []            # every request body, in order
    log_file = None
    delay = 0.0
    spill = {}          # model -> percent of it in GPU memory
    active = 0
    peak = 0            # most generate calls in flight at once
    loaded = {}         # model -> num_ctx of its last load
    lock = threading.Lock()
    quiet = False

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _note(self, path, body):
        rec = dict(body, _path=path, _ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with FakeOllama.lock:
            FakeOllama.log.append(body)
            if FakeOllama.log_file:
                with open(FakeOllama.log_file, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
        if not FakeOllama.quiet:
            o = body.get("options") or {}
            sys.stderr.write("fake_ollama: %s %s%s%s%s\n" % (
                path, body.get("model", ""),
                "" if "think" not in body else " think=%s" % json.dumps(body["think"]),
                "" if "num_ctx" not in o else " num_ctx=%s" % o["num_ctx"],
                "" if not body.get("format") else " format=%s" % body["format"]))

    def do_GET(self):
        if self.path == "/api/version":
            return self._send({"version": "0.0.0-fake"})
        if self.path == "/api/tags":
            return self._send({"models": [
                {"name": n, "model": n, "size": m["size"],
                 "details": {"family": m["family"], "parameter_size": m["param"]}}
                for n, m in self.models.items()]})
        if self.path == "/api/ps":
            out = []
            for n, ctx in sorted(FakeOllama.loaded.items()):
                size = self.models.get(n, {}).get("size", 1)
                pct = FakeOllama.spill.get(n, 100)
                out.append({"name": n, "model": n, "size": size,
                            "size_vram": int(size * pct / 100), "context_length": ctx})
            return self._send({"models": out})
        return self._send({"error": "not found"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        name = body.get("model") or body.get("name")
        m = self.models.get(name)
        if self.path == "/api/show":
            if not m:
                return self._send({"error": "model '%s' not found" % name}, 404)
            return self._send({"capabilities": m["capabilities"],
                               "model_info": {"%s.context_length" % m["family"]: m["context_length"]},
                               "parameters": m["parameters"]})
        if self.path == "/api/delete":
            self._note(self.path, body)
            return self._send({}) if m else self._send({"error": "not found"}, 404)
        if self.path == "/api/pull":
            self._note(self.path, body)
            return self._send({"status": "success"})
        if self.path != "/api/generate":
            return self._send({"error": "not found"}, 404)
        self._note(self.path, body)
        if not m:
            return self._send({"error": "model '%s' not found" % name}, 404)
        think = body.get("think")
        if think is not None and "thinking" not in m["capabilities"]:
            return self._send({"error": "\"%s\" does not support thinking" % name}, 400)
        with FakeOllama.lock:
            FakeOllama.active += 1
            FakeOllama.peak = max(FakeOllama.peak, FakeOllama.active)
            own = None
            for ln in m["parameters"].splitlines():
                if ln.split()[:1] == ["num_ctx"]:
                    own = int(ln.split()[1])
            FakeOllama.loaded[name] = (body.get("options") or {}).get("num_ctx") or own \
                or m["context_length"]
        try:
            time.sleep(FakeOllama.delay)
            prompt = body.get("prompt") or ""
            if body.get("format") == "json":
                answer = json.dumps({"ok": True, "echo": prompt[:40]})
            else:
                answer = "A made-up answer to: %s" % prompt[:60] if prompt else ""
            thinking = ""
            if "thinking" in m["capabilities"] and think is not False and prompt:
                thinking = "Thinking it over. " * (40 if think in (None, True, "high") else 10)
            out = {"model": name, "response": answer, "done": True, "done_reason": "stop",
                   "prompt_eval_count": max(1, len(prompt.split())),
                   "eval_count": max(1, len((thinking + answer).split())),
                   "eval_duration": 10 ** 8}
            if thinking:
                out["thinking"] = thinking
            if body.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                for w in answer.split(" "):
                    self.wfile.write((json.dumps({"response": w + " ", "done": False}) + "\n").encode())
                self.wfile.write((json.dumps(dict(out, response="")) + "\n").encode())
                return None
            return self._send(out)
        finally:
            with FakeOllama.lock:
                FakeOllama.active -= 1


def start(port=0, models=None, delay=0.0, log_file=None, spill=None, quiet=True):
    """Start in a thread; return (server, base_url).  For tests and bridge_smoke.py."""
    FakeOllama.models = models or MODELS
    FakeOllama.delay, FakeOllama.log_file, FakeOllama.quiet = delay, log_file, quiet
    FakeOllama.spill = dict(spill or {})
    FakeOllama.log, FakeOllama.loaded, FakeOllama.peak = [], {}, 0
    srv = ThreadingHTTPServer(("127.0.0.1", port), FakeOllama)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def main(argv=None):
    ap = argparse.ArgumentParser(description="A stand-in Ollama for trying Llama Bridge.")
    ap.add_argument("--port", type=int, default=11435)
    ap.add_argument("--log", default=None, help="append each request as a JSON line here")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds each generate takes")
    ap.add_argument("--models", default=None, help="a JSON file shaped like MODELS")
    ap.add_argument("--spill", action="append", default=[], help="MODEL=PERCENT in GPU memory")
    a = ap.parse_args(argv)
    models = json.load(open(a.models, encoding="utf-8")) if a.models else MODELS
    spill = {}
    for s in a.spill:
        k, _, v = s.rpartition("=")
        spill[k] = int(v)
    srv, url = start(a.port, models, a.delay, a.log, spill, quiet=False)
    sys.stderr.write("fake_ollama: listening at %s (models: %s); Ctrl-C stops it\n"
                     % (url, ", ".join(models)))
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
