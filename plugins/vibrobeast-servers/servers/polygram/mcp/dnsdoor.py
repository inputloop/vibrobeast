# polygram -- gated agent-skill synthesis.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later OR LGPL-3.0-or-later; https://github.com/inputloop.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# This file is part of polygram.  It is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version; or, at your choice, the GNU Lesser
# General Public License, version 3 or later.  It is distributed WITHOUT ANY WARRANTY; see
# <https://www.gnu.org/licenses/>.
# Written by Mentat (for Corwin, claude-sonnet via subagent), 2026-11-01.

"""dnsdoor -- DNS provider orchestration, served by gwstatus, routed through C4.

Tools (listed only while the ``dns.on`` door is open; off by default):

  dns_zones  PROVIDER                     the domains this key may touch
  dns_ping   PROVIDER                     the key is set (never shown), the provider answers
  dns_list   PROVIDER DOMAIN [counts]     the live records, or counts by type
  dns_plan   PROVIDER DOMAIN DESIRED      desired records (text, the dn1or desired-file format) -> a diff in words
                                          and a plan file; read-only at the provider
  dns_apply  PROVIDER PLAN [confirm]      the plan in words and a code; the second call, with the code, applies it

Every tool runs C4's own tool (``<c4>/bin/dn1or``, found as c4face finds C4, or DNS_TOOL) through the
SAME door key_run uses (keys.run): the key's value is bound by keys.py to the one program ``python``, never
returned, never an argument, scrubbed from the output; the first call returns the confirmation (the key's name,
the command, its usage constraints) and a code, and the second call with that code runs it once.  The usage line
handed to the tool is the register row's own, not the caller's.  A plan file may be applied only from under the
tool's own record folder (``<c4>/d/dns``), and dn1or checks its checksum, the key's domain bounds, and that every
step still holds; it never removes a record the plan does not name, and never touches NS or SOA unless the plan
was made with allow_ns.  Writes happen only through dns_apply.

Providers: porkbun (register row dnsporkbun, binds PORKBUN_KEYS) and dreamhost (dnsdreamhost, binds
DREAMHOST_API_KEY).  A key is found by the variable it binds, or named with ``key``.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

VERSION = "0.1.0"
BINDS = {"porkbun": ("PORKBUN_KEYS", "PORKBUN_API_KEY"), "dreamhost": ("DREAMHOST_API_KEY",)}
#: tests set this to ["--mock", DIR] so the real tool runs against recorded replies; production leaves it empty.
TOOL_EXTRA: list = []
DESIRED_MAX = 20000


def is_on() -> bool:
    from . import doors
    return doors.is_open("dns.on")


def tool_path() -> Path:
    t = (os.environ.get("DNS_TOOL") or "").strip()
    if t and "${" not in t:
        return Path(t)
    from . import c4face
    c4 = c4face.find_c4()["dir"]
    if c4 is None:
        raise RuntimeError("C4 was not found: set the c4.root preference (or C4_ROOT); dn1or lives in <c4>/bin")
    return Path(c4) / "bin" / "dn1or"


def record_root() -> Path:
    r = (os.environ.get("DNS_RECORD_DIR") or "").strip()
    return Path(r) if r else tool_path().parent.parent / "d" / "dns"


def pick_key(provider: str, named: str = ""):
    """(row, lex, problem)."""
    from . import keys
    if provider not in BINDS:
        return None, None, "provider must be porkbun or dreamhost"
    lex = keys.lexicon()
    rows, _ = keys.keys(lex=lex)
    if named:
        row = rows.get(named)
        return (row, lex, "") if row else (None, lex, f"no key named {named!r} in key_list")
    hits = [r for r in rows.values() if set(BINDS[provider]) & set(r["binds_list"])]
    if len(hits) == 1:
        return hits[0], lex, ""
    if not hits:
        return None, lex, (f"no registered key binds {' or '.join(BINDS[provider])}; add the {provider} row to the "
                           "key register (see c4/d/dns/README.md)")
    return None, lex, "several keys bind that name: " + ", ".join(r["name"] for r in hits) + "; pass key"


def _run(provider: str, args: list, confirm: str, named: str = "") -> dict:
    from . import keys
    row, lex, why = pick_key(provider, named)
    if row is None:
        return {"ok": False, "say": why}
    try:
        tool = tool_path()
    except RuntimeError as e:
        return {"ok": False, "say": str(e)}
    argv = ["python", str(tool), "--provider", provider, "--recdir", str(record_root()), *TOOL_EXTRA]
    if row.get("usage"):
        argv += ["--usage", row["usage"]]
    argv += args
    # porkbun's secret half is a second key (binds PORKBUN_SECRET_API_KEY), handed on the program's INPUT only
    # (key_run's stdin_key), never an argument or an environment variable.
    feed = None
    if provider == "porkbun":
        rows, _ = keys.keys(lex=lex)
        feed = next((r for r in rows.values() if r["name"] != row["name"] and "PORKBUN_SECRET_API_KEY" in r["binds_list"]), None)
    return keys.run(row, argv, str(tool.parent), confirm, lex, stdin_row=feed)


def _clean(args: dict, name: str, pat: str, what: str) -> str:
    v = (args.get(name) or "").strip()
    if not re.fullmatch(pat, v):
        raise ValueError(f"{name}: {what}")
    return v


def plan_in_words(planfile: Path) -> list[str]:
    """The plan file read back, offline, as the dn1or words (no key, no network)."""
    out = []
    try:
        lines = planfile.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ["(the plan file could not be read)"]
    hdr = {}
    for l in lines:
        c = l.split("\t")
        if c[0] == "op" and len(c) == 8:
            kind, name, typ, ttl, val, old, oldttl = c[1:]
            if kind == "add":
                out.append(f"ADD {name} {typ} {val}")
            elif kind == "change":
                out.append(f"CHANGE {name} {typ}: {old} -> {val}")
            else:
                out.append(f"REMOVE {name} {typ} {val}")
            if typ == "MX":
                out.append("*** WARNING: MX CHANGE -- MAIL ROUTING ***")
        elif len(c) == 2:
            hdr[c[0]] = c[1]
    if hdr.get("allow_ns") == "1":
        out.append("(made with allow_ns: NS records may be named)")
    return out or ["(no steps)"]


def register(srv) -> None:
    if not is_on():
        return
    from .rpc import ToolError
    PROV = {"type": "string", "enum": ["porkbun", "dreamhost"]}
    KEY = {"type": "string", "description": "a key's name, when more than one binds the provider's variable"}

    def prov_of(a):
        p = (a.get("provider") or "").strip().lower()
        if p not in BINDS:
            raise ToolError("provider must be porkbun or dreamhost")
        return p

    @srv.tool("dns_zones", "The domains the DNS key for a provider may touch (from the key's usage line; for porkbun, the "
              "account's own list). Runs C4's dn1or through the key door: the first call returns a confirmation and a "
              "code to show the person; call again with confirm set to the code to run it.",
              {"type": "object", "required": ["provider"], "properties": {"provider": PROV, "key": KEY, "confirm": {"type": "string"}}})
    def _zones(a):
        return _run(prov_of(a), ["zones"], a.get("confirm") or "", a.get("key") or "")

    @srv.tool("dns_ping", "Whether the provider's DNS door opens with the bound key (the key is never shown). Same two-call "
              "confirmation as key_run.",
              {"type": "object", "required": ["provider"], "properties": {"provider": PROV, "key": KEY, "confirm": {"type": "string"}}})
    def _ping(a):
        return _run(prov_of(a), ["whoami"], a.get("confirm") or "", a.get("key") or "")

    @srv.tool("dns_list", "The live DNS records of one domain (name, type, ttl, value), or counts by type only (counts=true). "
              "Refused for a domain outside the key's usage line. Same two-call confirmation as key_run.",
              {"type": "object", "required": ["provider", "domain"],
               "properties": {"provider": PROV, "domain": {"type": "string"}, "counts": {"type": "boolean"}, "key": KEY,
                              "confirm": {"type": "string"}}})
    def _list(a):
        try:
            dom = _clean(a, "domain", r"[A-Za-z0-9.-]{3,253}", "a domain name")
        except ValueError as e:
            raise ToolError(str(e))
        return _run(prov_of(a), ["list", dom] + (["--counts"] if a.get("counts") else []), a.get("confirm") or "", a.get("key") or "")

    @srv.tool("dns_plan", "Plan DNS changes for one domain, read-only at the provider: DESIRED is text, one directive per line "
              "(add NAME TYPE TTL VALUE | set NAME TYPE TTL VALUE | absent NAME TYPE [VALUE]; # comments; NAME is @ or a label; "
              "MX values start with the priority). Returns the diff in words (ADD / CHANGE / REMOVE, MX flagged loudly) and the "
              "plan file to give dns_apply. Records the plan does not name are never touched. NS only with allow_ns; SOA never. "
              "Same two-call confirmation as key_run.",
              {"type": "object", "required": ["provider", "domain", "desired"],
               "properties": {"provider": PROV, "domain": {"type": "string"}, "desired": {"type": "string"},
                              "allow_ns": {"type": "boolean"}, "key": KEY, "confirm": {"type": "string"}}})
    def _plan(a):
        try:
            dom = _clean(a, "domain", r"[A-Za-z0-9.-]{3,253}", "a domain name")
        except ValueError as e:
            raise ToolError(str(e))
        text = a.get("desired") or ""
        if not text.strip() or len(text) > DESIRED_MAX:
            raise ToolError(f"desired: text of 1..{DESIRED_MAX} characters")
        h = hashlib.sha256((dom + "\n" + text).encode("utf-8")).hexdigest()[:12]
        base = record_root() / dom.lower()
        want, out = base / "desired" / f"{h}.want", base / "plans" / f"{h}.plan"
        want.parent.mkdir(parents=True, exist_ok=True)
        if not want.is_file() or want.read_text(encoding="utf-8") != text:
            want.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")
        args = ["plan", dom, str(want), "--out", str(out)] + (["--allow-ns"] if a.get("allow_ns") else [])
        r = _run(prov_of(a), args, a.get("confirm") or "", a.get("key") or "")
        r["plan_file"] = str(out)
        return r

    @srv.tool("dns_apply", "Apply a plan made by dns_plan -- the ONLY tool that writes at a provider. The first call returns the "
              "plan in words and a confirmation with a code: show the person the words (MX flagged) and the key's usage "
              "constraints; call again with confirm set to the code only if they agree. The plan must be under C4's d/dns folder. "
              "dn1or re-checks the plan's checksum, the domain bound, and that every step still holds, then writes a dated record "
              "of each change and the provider's reply.",
              {"type": "object", "required": ["provider", "plan"],
               "properties": {"provider": PROV, "plan": {"type": "string"}, "key": KEY, "confirm": {"type": "string"}}})
    def _apply(a):
        plan = Path((a.get("plan") or "").strip())
        root = record_root().resolve()
        try:
            rp = plan.resolve()
            rp.relative_to(root)
        except (ValueError, OSError):
            raise ToolError(f"plan: only a plan file under {root} may be applied")
        if rp.suffix != ".plan" or not rp.is_file():
            raise ToolError("plan: a .plan file made by dns_plan")
        r = _run(prov_of(a), ["apply", str(rp), "--yes"], a.get("confirm") or "", a.get("key") or "")
        if r.get("ok") is None:
            r["plan_in_words"] = plan_in_words(rp)
            r["say"] = ("Show the person the plan in words (plan_in_words) and this confirmation. " + r.get("say", ""))
        return r
