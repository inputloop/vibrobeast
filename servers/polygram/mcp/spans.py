# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""spans -- time and tokens per piece of work, from on-start / on-stop MCP calls.

Corwin, 2026-09-23: *"we need good tracking for time and tokens based on on-start,
on-stop MCP calls."*  These four tools are that, on the always-on server.

WHAT THE SERVER KNOWS AND WHAT IT IS TOLD.  Time is the server's: every row is stamped
from the host clock, in UTC, when the call arrives, and no argument can backdate one.
Tokens are the caller's: an MCP server cannot see the model's usage, so the caller reports
the one figure it can see -- ``tokens_left``, the running budget its harness shows it -- at
start, at each mark, and at stop.  The server subtracts; it never estimates.  A span with no
token figures reports time only and says so in words.

THE LEDGER.  One TSV, append-only, ONE ROW PER EVENT, never per span, so nothing is ever
rewritten and a crash mid-span leaves a start row that ``span_report`` lists as open::

    ts  event  span  label  tokens_left  by  note        (event: start | mark | stop)

Every view rebuilds from the events.  Where it lives: ``$MENTCACHED_STATS`` (a file path)
if set, else ``~/.mentcached/stats/spans.tsv``.  The default is a path this server chose,
so it may create it; a path YOU named it never will (the seat's own rule), so a
``MENTCACHED_STATS`` pointing into a directory that does not exist is refused with the path.

WHY HERE AND NOT A FOURTH SERVER.  mentcached is the server that is always on and already
speaks for this identity (``MENTCACHED_BY`` is the ``by`` column).  A fourth server would be
one more thing to prepare, announce and fail; four tools on the one that already works is a
smaller surface.  A POSIX twin, ``bin/sp1rp``, reads the same file with awk so the report can
be checked in a second language.
"""

from __future__ import annotations

import datetime as _dt
import os
import secrets
from pathlib import Path

from .rpc import ToolError

DEFAULT_LEDGER = Path.home() / ".mentcached" / "stats" / "spans.tsv"
HEADER = "ts\tevent\tspan\tlabel\ttokens_left\tby\tnote"
EVENTS = ("start", "mark", "stop")


def ledger_path() -> tuple[Path, bool]:
    """(path, ours) -- ours is True when nobody named it, so we may create it."""
    raw = (os.environ.get("MENTCACHED_STATS") or "").strip()
    if not raw or "${" in raw or "%" in raw or raw.startswith("$"):
        return DEFAULT_LEDGER, True
    return Path(raw).expanduser(), False


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _stamp(t: _dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> _dt.datetime:
    return _dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)


def _clean(s) -> str:
    """One field, one line: tabs and newlines would break the row."""
    return " ".join(str(s if s is not None else "").split())


def _tokens(args: dict, key: str = "tokens_left"):
    v = args.get(key)
    if v is None or v == "":
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ToolError(f"{key} must be a whole number of tokens, got {v!r}") from None
    if n < 0:
        raise ToolError(f"{key} cannot be negative ({n})")
    return n


class Ledger:
    def __init__(self, path: Path, ours: bool, by: str):
        self.path, self.ours, self.by = path, ours, by

    # ---------------------------------------------------------------- io
    def rows(self) -> list[dict]:
        if not self.path.is_file():
            return []
        out = []
        for ln in self.path.read_text(encoding="utf-8").splitlines():
            if not ln.strip() or ln.startswith("ts\t"):
                continue
            f = ln.split("\t")
            if len(f) < 7 or f[1] not in EVENTS:
                continue      # a foreign or damaged line is skipped, never guessed at
            out.append({"ts": f[0], "event": f[1], "span": f[2], "label": f[3],
                        "tokens_left": int(f[4]) if f[4] else None, "by": f[5],
                        "note": "\t".join(f[6:])})
        return out

    def append(self, event: str, span: str, label: str, tokens_left, note: str) -> dict:
        if not self.path.exists():
            if not self.ours:
                raise ToolError(
                    f"MENTCACHED_STATS names {self.path}, which does not exist. A path you "
                    "named this server never creates: unset it to use the default, or "
                    "create the file yourself (an empty file is fine).")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(HEADER + "\n", encoding="utf-8", newline="\n")
        ts = _stamp(_now())
        row = [ts, event, span, _clean(label), "" if tokens_left is None else str(tokens_left),
               _clean(self.by), _clean(note)]
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write("\t".join(row) + "\n")
        return {"ts": ts, "event": event, "span": span, "label": _clean(label),
                "tokens_left": tokens_left, "by": self.by, "note": _clean(note)}

    # ------------------------------------------------------------ views
    def spans(self) -> list[dict]:
        """Rebuild every span from its events, in start order."""
        seen: dict[str, dict] = {}
        for r in self.rows():
            if r["event"] == "start":
                seen[r["span"]] = {"span": r["span"], "label": r["label"], "by": r["by"],
                                   "started": r["ts"], "stopped": None,
                                   "tokens_start": r["tokens_left"], "tokens_stop": None,
                                   "marks": [], "notes": [r["note"]] if r["note"] else [],
                                   "outcome": None}
                continue
            s = seen.get(r["span"])
            if s is None:
                continue      # a mark/stop with no start: kept in the file, not in the view
            if r["event"] == "mark":
                s["marks"].append({"ts": r["ts"], "tokens_left": r["tokens_left"],
                                   "note": r["note"]})
            elif r["event"] == "stop" and s["stopped"] is None:
                s["stopped"] = r["ts"]; s["tokens_stop"] = r["tokens_left"]
                s["outcome"] = r["note"]
        out = []
        for s in seen.values():
            end = _parse(s["stopped"]) if s["stopped"] else _now()
            s["seconds"] = int((end - _parse(s["started"])).total_seconds())
            s["open"] = s["stopped"] is None
            last_tokens = s["tokens_stop"]
            if last_tokens is None and s["marks"]:
                last_tokens = next((m["tokens_left"] for m in reversed(s["marks"])
                                    if m["tokens_left"] is not None), None)
            s["tokens_used"] = (s["tokens_start"] - last_tokens
                                if s["tokens_start"] is not None and last_tokens is not None
                                else None)
            s["tokens_note"] = ("" if s["tokens_used"] is not None else
                                "no token figures on both ends of this span; time only")
            out.append(s)
        return out

    def open_spans(self) -> list[dict]:
        return [s for s in self.spans() if s["open"]]

    def pick(self, span_id: str | None) -> dict:
        """The span a mark or stop means: the named one, or the most recent open one."""
        opens = self.open_spans()
        if span_id:
            for s in self.spans():
                if s["span"] == span_id:
                    return s
            raise ToolError(f"no span {span_id!r} in {self.path}")
        if not opens:
            raise ToolError("nothing is open: span_start first (or name the span)")
        if len(opens) > 1:
            raise ToolError("more than one span is open (" + ", ".join(
                f"{s['span']} {s['label']!r}" for s in opens)
                + "); say which with `span`")
        return opens[0]


def _new_id(t: _dt.datetime) -> str:
    return t.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(2)


def _summary(s: dict) -> dict:
    return {k: s[k] for k in ("span", "label", "started", "stopped", "seconds",
                              "tokens_start", "tokens_stop", "tokens_used", "open", "by")} | {
        "marks": len(s["marks"]), "outcome": s["outcome"],
        "say": (f"{s['label']}: {_hms(s['seconds'])}"
                + (f", {s['tokens_used']:,} tokens" if s["tokens_used"] is not None
                   else " (time only)") + (" -- still open" if s["open"] else ""))}


def _hms(sec: int) -> str:
    h, rem = divmod(int(sec), 3600); m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m{s:02d}s" if h else (f"{m}m{s:02d}s" if m else f"{s}s")


_TOK = {"type": "integer", "minimum": 0,
        "description": ("the token budget you can see RIGHT NOW (e.g. the harness's "
                        "'N tokens left'). Report it; the server subtracts. Omit if you "
                        "cannot see one -- the span then reports time only.")}
_NOTE = {"type": "string", "description": "one line; tabs and newlines are folded"}
_SPAN = {"type": "string", "description": "a span id from span_start; omit for the one open span"}


def register(srv, by: str) -> None:
    lp, ours = ledger_path()
    L = Ledger(lp, ours, by)

    @srv.tool("span_start",
              "Open a span: the clock starts NOW (server time, UTC) and the token budget "
              "you report is its baseline. Call this when a piece of work begins -- a "
              "session, a task, a build -- and span_stop when it ends. One row is appended "
              "to the ledger; nothing is ever rewritten.",
              {"type": "object",
               "properties": {"label": {"type": "string",
                                        "description": "what this span is (task, session, build ...)"},
                              "tokens_left": _TOK, "note": _NOTE},
               "required": ["label"]})
    def _start(args):
        label = _clean(args.get("label"))
        if not label:
            raise ToolError("label is required: a span nobody can name cannot be reported")
        opens = L.open_spans()
        sid = _new_id(_now())
        row = L.append("start", sid, label, _tokens(args), args.get("note") or "")
        from . import checks as _checks
        return {"span": sid, "label": label, "started": row["ts"],
                "tokens_left": row["tokens_left"], "ledger": str(L.path),
                "also_open": [f"{s['span']} {s['label']}" for s in opens],
                "checks": _checks.run(),
                "say": f"span {sid} open for {label!r}"
                       + (f"; {len(opens)} other span(s) still open" if opens else "")}

    @srv.tool("span_mark",
              "A checkpoint inside an open span: elapsed and tokens since the start and "
              "since the last mark. Use it between steps so the report can say where the "
              "time and tokens went.",
              {"type": "object",
               "properties": {"span": _SPAN, "tokens_left": _TOK, "note": _NOTE}})
    def _mark(args):
        s = L.pick(args.get("span"))
        if not s["open"]:
            raise ToolError(f"span {s['span']} is already stopped; marks go in open spans")
        tl = _tokens(args)
        prev = s["marks"][-1] if s["marks"] else {"ts": s["started"], "tokens_left": s["tokens_start"]}
        row = L.append("mark", s["span"], s["label"], tl, args.get("note") or "")
        since_prev = int((_parse(row["ts"]) - _parse(prev["ts"])).total_seconds())
        since_start = int((_parse(row["ts"]) - _parse(s["started"])).total_seconds())
        tok_prev = (prev["tokens_left"] - tl if prev["tokens_left"] is not None and tl is not None else None)
        tok_start = (s["tokens_start"] - tl if s["tokens_start"] is not None and tl is not None else None)
        return {"span": s["span"], "label": s["label"], "mark": len(s["marks"]) + 1, "ts": row["ts"],
                "seconds_since_start": since_start, "seconds_since_last": since_prev,
                "tokens_since_start": tok_start, "tokens_since_last": tok_prev,
                "say": f"mark {len(s['marks']) + 1} on {s['label']!r}: {_hms(since_prev)} since last"
                       + (f", {tok_prev:,} tokens" if tok_prev is not None else "")}

    @srv.tool("span_stop",
              "Close a span: the clock stops NOW and the token budget you report is the "
              "other end of the subtraction. Returns the span's summary. Refuses when "
              "nothing is open, and refuses to stop a span twice.",
              {"type": "object",
               "properties": {"span": _SPAN, "tokens_left": _TOK,
                              "outcome": {"type": "string",
                                          "description": "one word or line: done, handed back, abandoned ..."},
                              "note": _NOTE}})
    def _stop(args):
        s = L.pick(args.get("span"))
        if not s["open"]:
            raise ToolError(f"span {s['span']} ({s['label']!r}) was already stopped at {s['stopped']}")
        note = _clean(args.get("outcome") or "") or _clean(args.get("note") or "")
        L.append("stop", s["span"], s["label"], _tokens(args), note)
        closed = next(x for x in L.spans() if x["span"] == s["span"])
        return {**_summary(closed), "ledger": str(L.path)}

    @srv.tool("span_report",
              "Every span in the ledger with its time and tokens, totals, a rollup per "
              "label, and which spans are still open. `since` (YYYY-MM-DD) and `label` "
              "narrow it; `limit` caps the list (newest last).",
              {"type": "object",
               "properties": {"since": {"type": "string", "description": "YYYY-MM-DD, inclusive"},
                              "label": {"type": "string", "description": "exact label"},
                              "limit": {"type": "integer", "minimum": 1}}})
    def _report(args):
        args = args or {}
        spans = L.spans()
        if args.get("since"):
            spans = [s for s in spans if s["started"][:10] >= str(args["since"])[:10]]
        if args.get("label"):
            spans = [s for s in spans if s["label"] == _clean(args["label"])]
        by_label: dict[str, dict] = {}
        for s in spans:
            b = by_label.setdefault(s["label"], {"label": s["label"], "spans": 0, "seconds": 0,
                                                 "tokens": 0, "tokens_known": 0})
            b["spans"] += 1; b["seconds"] += s["seconds"]
            if s["tokens_used"] is not None:
                b["tokens"] += s["tokens_used"]; b["tokens_known"] += 1
        tot_sec = sum(s["seconds"] for s in spans)
        tok_known = [s["tokens_used"] for s in spans if s["tokens_used"] is not None]
        shown = spans[-int(args["limit"]):] if args.get("limit") else spans
        return {"ledger": str(L.path), "exists": L.path.is_file(),
                "count": len(spans), "open": [s["span"] for s in spans if s["open"]],
                "seconds": tot_sec, "tokens": sum(tok_known), "tokens_known_for": len(tok_known),
                "by_label": sorted(by_label.values(), key=lambda b: -b["seconds"]),
                "spans": [_summary(s) for s in shown],
                "say": (f"{len(spans)} span(s), {_hms(tot_sec)} in all"
                        + (f", {sum(tok_known):,} tokens across the {len(tok_known)} with figures"
                           if tok_known else ", no token figures yet")
                        + (f"; {sum(1 for s in spans if s['open'])} still open"
                           if any(s["open"] for s in spans) else "")) if spans else
                       f"no spans yet in {L.path}"}
