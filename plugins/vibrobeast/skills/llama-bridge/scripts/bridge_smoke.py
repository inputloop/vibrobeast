#!/usr/bin/env python3
# bridge_smoke -- does Llama Bridge work here?  Run it before tuning anything.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.  It is distributed WITHOUT ANY
# WARRANTY; see <https://www.gnu.org/licenses/>.
"""bridge_smoke -- try Llama Bridge end to end, in words, before tuning anything.

  python3 bridge_smoke.py --bridge PATH/llama_bridge.py            # against fake_ollama (default)
  python3 bridge_smoke.py --bridge PATH/llama_bridge.py --host http://127.0.0.1:11434 [--model M]

With no --host it starts fake_ollama.py (beside this file) on a free port, so it needs no GPU and
no model: it shows the bridge's own path works, and prints what the bridge sent.  With --host it
does the same against a real Ollama, with a short prompt, and reports what the bridge decided
(think, window, speed).  It keeps its log in a throwaway database, never the bridge's own.

Steps: reach Ollama; list models; one checked delegation (JSON, think false where the model can
think); one background job polled to the end; on the fake, the requests it saw.
exit: 0 every step passed; 1 a step failed; 2 could not start (no bridge file, no Ollama).
"""
import argparse
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def load_bridge(path):
    loader = importlib.machinery.SourceFileLoader("llama_bridge_smoke", path)
    spec = importlib.util.spec_from_loader("llama_bridge_smoke", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description="Does Llama Bridge work here?")
    root = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    found = [p for p in (os.path.join(root, "servers", "polygram", "mcp", "llama_bridge.py"),
                         os.path.join(root, "polygram", "mcp", "llama_bridge.py"))
             if os.path.isfile(p)]   # in the plugin, then in the garden's source tree
    ap.add_argument("--bridge", default=(found or ["llama_bridge.py"])[0])
    ap.add_argument("--host", default=None, help="a real Ollama; default: start fake_ollama")
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)
    if not os.path.isfile(a.bridge):
        print("NOT CHECKED: no bridge at %s (pass --bridge PATH/llama_bridge.py)" % a.bridge)
        return 2
    lb = load_bridge(a.bridge)
    fake = None
    if a.host:
        host = a.host.rstrip("/")
    else:
        sys.path.insert(0, HERE)
        import fake_ollama
        fake = fake_ollama
        _srv, host = fake_ollama.start()
    lb.CFG["db"] = os.path.join(tempfile.mkdtemp(prefix="bridge-smoke-"), "smoke.db")
    lb.CFG["ollama"] = host
    lb.init_db()
    vb = "-vb." in getattr(lb, "VERSION", "")
    print("bridge %s against %s%s" % (getattr(lb, "VERSION", "?"), host,
                                      " (fake_ollama: nothing real runs)" if fake else ""))
    bad = 0

    def step(ok, what, detail=""):
        nonlocal bad
        print("%s  %s%s" % ("PASS" if ok else "FAIL", what, (": " + detail) if detail else ""))
        if not ok:
            bad = 1
        return ok

    text, err = lb.mcp_call_tool("ollama_status", {})
    if not step("is up" in text[0]["text"], "reach Ollama", text[0]["text"]):
        return 2
    models = lb.ollama_tags()
    if not step(bool(models), "list models", ", ".join(m["name"] for m in models) or "none"):
        return 2
    model = a.model
    if not model:
        thinkers = [m["name"] for m in models if lb.ollama_show(m["name"]).get("thinking")] \
            if hasattr(lb, "ollama_show") else []
        model = (thinkers or [models[0]["name"]])[0]
    t0 = time.time()
    kw = {"checks": {"require_json": True}, "no_cache": True}
    if vb:
        kw["think"] = False
    r = lb.do_delegate(model, 'Reply with JSON: {"word": a common fruit}', source="smoke", **kw)
    secs = time.time() - t0
    detail = "%s in %.1f s" % (model, secs)
    if vb and r.get("ok"):
        detail += "; think %s; window %s%s; %s tok/s" % (
            r.get("think"), r.get("num_ctx") or "model default",
            " (auto)" if r.get("num_ctx_auto") else "", r.get("tok_per_sec") or "?")
    step(r.get("ok") and r.get("verified"), "one checked delegation", detail
         if r.get("ok") else r.get("error"))
    text, err = lb.mcp_call_tool("delegate_async", {"model": model, "prompt": "Say hello.",
                                                    "no_cache": True})
    jid = text[0]["text"].split()[3].rstrip(".")
    deadline, state = time.time() + (600 if a.host else 30), ""
    while time.time() < deadline:
        state = lb.mcp_call_tool("delegate_result", {"job_id": jid})[0][0]["text"]
        if "queued" not in state and "still running" not in state:
            break
        time.sleep(0.5)
    step("failed" not in state and "queued" not in state and "still running" not in state,
         "a background job, polled to the end", "job %s" % jid)
    if fake:
        sent = [b for b in fake.FakeOllama.log if "prompt" in b and b.get("prompt")]
        first = sent[0] if sent else {}
        if vb:
            step(first.get("think") is False and (first.get("options") or {}).get("num_ctx"),
                 "what the bridge sent", "think=%s, num_ctx=%s" % (
                     json.dumps(first.get("think")), (first.get("options") or {}).get("num_ctx")))
        else:
            print("NOTE  this bridge is not vb.1: it sends no think and no window; the fake saw %s"
                  % json.dumps({k: first.get(k) for k in ("model", "format", "keep_alive")}))
    print("smoke: %s" % ("every step passed" if not bad else "a step FAILED"))
    return bad


if __name__ == "__main__":
    sys.exit(main())
