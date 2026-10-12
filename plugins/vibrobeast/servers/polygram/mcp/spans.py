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

RESETS (extension edition, 2026-10-10; spec S-R1, R17).  *A rising token figure is a reset, never a
negative count.*  The caller's figure goes UP when a new prompt begins, and the app's own
housekeeping can raise it too; the server cannot see which.  So a leg whose figure rose returns
``tokens_since_last: null`` and ``reset: true``, is left out of every total, and the report says
"N resets seen" in words.  Spend is the sum of the falling legs.  The Tcl spec
``tests/spans-reset-spec.tcl`` checks this file and ``bin/sp1rp`` against the same bytes.

THE FRAME (extension edition; ``FRAME.md`` says each column in words).  When the preference
``usage.capture`` is ``on`` -- it is ``off`` by default -- ``span_start`` writes one ``start`` row
(the count at start) and every reset, or a mark the caller calls a prompt, writes one ``prompt`` row
(the count after a prompt) into the frame: a headerless TSV, one row per event, append-only, its
column names one path over in ``d/fr`` beside it.  Those rows carry TS, KIND, SESSION, TOKENS_LEFT
and BY and nothing else: no label, no note, no content.  Off means no row and no file.
``question_log`` (F1, pass 2) writes the question rows the question gauge ``bin/qg1ck`` reads:
KIND ``gauge``, KEY ``question`` with LABEL, LIKELIHOOD, CONFIDENCE and NOTE (the question's words),
and later KEY ``second_needed``.  Those rows do carry words -- the question asked -- and are written
only when capture is on.
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

#: The frame's twelve columns, in order (FRAME.md says each in words; d/fr holds this line).
FRAME_COLUMNS = ("TS", "KIND", "SESSION", "SPAN", "LABEL", "TOKENS_LEFT", "BY", "KEY", "VALUE",
                 "LIKELIHOOD", "CONFIDENCE", "NOTE")
FRAME_KINDS = ("start", "mark", "stop", "prompt", "checkpoint", "gauge", "tone", "pref")
DEFAULT_FRAME = Path.home() / ".mentcached" / "stats" / "fr"


def _is_reset(prev, now) -> bool:
    """S-R1: a figure that ROSE since the last known one is a reset (a new prompt, or the app's
    own housekeeping), never a negative spend."""
    return prev is not None and now is not None and now > prev


def _legs(figures) -> tuple[int, int]:
    """(spent, resets) over token figures in order; None figures are skipped.  Spend is the sum
    of the falling legs; a rising leg is counted as a reset and left out."""
    spent = resets = 0
    prev = None
    for f in figures:
        if f is None:
            continue
        if _is_reset(prev, f):
            resets += 1
        elif prev is not None:
            spent += prev - f
        prev = f
    return spent, resets


def _resets_words(n: int) -> str:
    return (f"{n} reset{'' if n == 1 else 's'} seen, so {n} new prompt{'' if n == 1 else 's'} "
            "(counted from resets; the app's own housekeeping can add a reset, so this count may "
            "run high); the legs across a reset are left out of the totals")


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
            figs = [s["tokens_start"]] + [m["tokens_left"] for m in s["marks"]] + [s["tokens_stop"]]
            spent, s["resets"] = _legs(figs)
            s["tokens_used"] = (spent if s["tokens_start"] is not None and last_tokens is not None
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


def frame_path() -> tuple[Path, bool]:
    """(path, ours) for the frame: ``$MENTCACHED_FRAME`` if set (never created), else
    ``~/.mentcached/stats/fr`` (this server's choice, so it may create it)."""
    raw = (os.environ.get("MENTCACHED_FRAME") or "").strip()
    if not raw or "${" in raw or "%" in raw or raw.startswith("$"):
        return DEFAULT_FRAME, True
    return Path(raw).expanduser(), False


def frame_names_path(fp: Path) -> Path:
    """The column names live one path over: ``<dir>/d/<name>`` beside ``<dir>/<name>``."""
    return fp.parent / "d" / fp.name


class Frame:
    """The usage frame's writer for the two counts (``start`` and ``prompt`` rows).  It writes
    only when ``usage.capture`` is on; off (the default, and the answer when the preference
    cannot be read) means no row and no file."""

    def __init__(self, by: str):
        self.by = by

    @staticmethod
    def capture_on() -> bool:
        try:
            from . import prefs as _prefs
            return _prefs.on("usage.capture")
        except Exception:                      # noqa: BLE001 -- unreadable or missing key = default off
            return False

    def _row(self, kind: str, session: str, tokens_left, key: str = "", value: str = "",
             label: str = "", likelihood: str = "", confidence: str = "", note: str = "") -> str:
        """A start or prompt row fills only TS, KIND, SESSION, TOKENS_LEFT and BY; a pref row
        fills TS, KIND, BY, KEY and VALUE; a question (``gauge``) row also fills LABEL,
        LIKELIHOOD, CONFIDENCE and NOTE.  The rest stay blank."""
        cells = dict.fromkeys(FRAME_COLUMNS, "")
        cells.update(TS=_stamp(_now()), KIND=kind, SESSION=_clean(session),
                     TOKENS_LEFT="" if tokens_left is None else str(int(tokens_left)),
                     BY=_clean(self.by), KEY=_clean(key), VALUE=_clean(value),
                     LABEL=_clean(label), LIKELIHOOD=_clean(likelihood),
                     CONFIDENCE=_clean(confidence), NOTE=_clean(note))
        return "\t".join(cells[c] for c in FRAME_COLUMNS)

    def write(self, kind: str, session: str, tokens_left, key: str = "", value: str = "",
              **more) -> str:
        """Append one row when capture is on.  Returns, in words, what happened."""
        if not self.capture_on():
            return "usage.capture is off: no frame row written"
        fp, ours = frame_path()
        if not fp.exists():
            if not ours:
                return (f"MENTCACHED_FRAME names {fp}, which does not exist; a path you named is "
                        "never created, so no frame row was written")
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.touch()
        names = frame_names_path(fp)
        if ours and not names.exists():
            names.parent.mkdir(parents=True, exist_ok=True)
            names.write_text("\t".join(FRAME_COLUMNS) + "\n", encoding="utf-8", newline="\n")
        with fp.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(self._row(kind, session, tokens_left, key, value, **more) + "\n")
        if kind == "gauge":
            return f"one gauge row ({key}: {value}) written to {fp}"
        return (f"one {kind} row (a date and a count) written to {fp}" if kind != "pref"
                else f"one pref row (a date, the key and its value) written to {fp}")

    def start(self, session: str, tokens_left) -> str:
        return self.write("start", session, tokens_left)

    def pref(self, key: str, value: str) -> str:
        """A preference set, mirrored as one ``pref`` row (TS, KIND, BY, KEY, VALUE) when capture
        is on (card 22: the preference acts; the mirror is only counted, by qg1ck and the drift
        page).  prefs.py never sends a third party's ``person.<other>.*`` row here."""
        return self.write("pref", "", None, key=key, value=value)

    def prompt(self, session: str, tokens_left) -> str:
        if tokens_left is None:
            return "no count given, so no prompt row"
        return self.write("prompt", session, tokens_left)

    # SPEC (F1, pass 2, P6 O4/J3, card 14): the frame has a writer for the question rows qg1ck
    # reads.  question() writes KIND=gauge KEY=question LABEL=<id> VALUE=one|two
    # LIKELIHOOD=<guess> CONFIDENCE=<number, fraction or percent> NOTE=<the question>;
    # second_needed() writes KIND=gauge KEY=second_needed LABEL=<id> VALUE=yes|no|unasked.
    # Both write only when usage.capture is on, like every frame row.
    def question(self, qid: str, frame: str, question: str, likelihood: str = "",
                 confidence: str = "", session: str = "") -> str:
        qid, frame = _clean(qid), _clean(frame)
        if not qid:
            raise ToolError("question_id is required: a question nobody can name cannot be counted")
        if frame not in QUESTION_FRAMES:
            raise ToolError(f"frame must be one of {', '.join(QUESTION_FRAMES)} (got {frame!r})")
        confidence = _clean(confidence)
        if confidence and confidence_value(confidence) is None:
            raise ToolError(f"confidence must be a number, a fraction (0.17) or a percent (17%); "
                            f"got {confidence!r}")
        # SPEC (F3, pass 3, P6b J3): a bare number above 1 is a slip for a percent; refuse it at
        # write and teach the form, so qg1ck never files a fault that is really a typing slip.
        if confidence and not confidence.endswith("%") and confidence_value(confidence) > 1:
            v = confidence_value(confidence)
            raise ToolError(f"confidence {confidence} is a bare number above 1: write "
                            f"{confidence}% or {v / 100:g} (nothing was written)")
        return self.write("gauge", session, None, key="question", value=frame, label=qid,
                          likelihood=_clean(likelihood), confidence=confidence,
                          note=_clean(question))

    def second_needed(self, qid: str, answer: str, session: str = "") -> str:
        qid, answer = _clean(qid), _clean(answer)
        if not qid:
            raise ToolError("question_id is required")
        if answer not in SECOND_ANSWERS:
            raise ToolError(f"second_needed must be one of {', '.join(SECOND_ANSWERS)} (got {answer!r})")
        # SPEC (F3, pass 3, P6b J4): an answer names a question that was logged.  Checked only
        # while capture is on (off writes nothing either way, so there is nothing to orphan).
        if self.capture_on() and not self.logged(qid):
            raise ToolError(f"question {qid!r} was never logged: log it first (question_log with "
                            "frame and question), then its second_needed (nothing was written)")
        return self.write("gauge", session, None, key="second_needed", value=answer, label=qid)

    @staticmethod
    def logged(qid: str) -> bool:
        """True when the frame holds a ``gauge``/``question`` row whose LABEL is ``qid``."""
        fp, _ours = frame_path()
        try:
            text = fp.read_text(encoding="utf-8")
        except OSError:
            return False
        k, key, label = (FRAME_COLUMNS.index(c) for c in ("KIND", "KEY", "LABEL"))
        for ln in text.splitlines():
            c = ln.split("\t")
            if len(c) > max(k, key, label) and c[k] == "gauge" and c[key] == "question" and c[label] == qid:
                return True
        return False


QUESTION_FRAMES = ("one", "two")
SECOND_ANSWERS = ("yes", "no", "unasked")


def confidence_value(s):
    """A confidence as a fraction: ``0.17`` -> 0.17, ``17%`` -> 0.17 (his own form, SPELL.md:41
    "17% or less"); None when it is not a number.  A bare number above 1 is NOT read as a
    percent: write ``17%``."""
    import re as _re
    s = (s or "").strip()
    m = _re.fullmatch(r"(\d*\.?\d+)(%?)", s)
    if not m:
        return None
    v = float(m.group(1))
    return v / 100.0 if m.group(2) else v


def _new_id(t: _dt.datetime) -> str:
    return t.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(2)


def _summary(s: dict) -> dict:
    return {k: s[k] for k in ("span", "label", "started", "stopped", "seconds",
                              "tokens_start", "tokens_stop", "tokens_used", "open", "by")} | {
        "marks": len(s["marks"]), "outcome": s["outcome"], "resets": s.get("resets", 0),
        "say": (f"{s['label']}: {_hms(s['seconds'])}"
                + (f", {s['tokens_used']:,} tokens" if s["tokens_used"] is not None
                   else " (time only)")
                + (f"; {_resets_words(s['resets'])}" if s.get("resets") else "")
                + (" -- still open" if s["open"] else ""))}


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
    F = Frame(by)

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
        frame = F.start(sid, row["tokens_left"])
        from . import checks as _checks
        return {"span": sid, "label": label, "started": row["ts"],
                "tokens_left": row["tokens_left"], "ledger": str(L.path), "frame": frame,
                "also_open": [f"{s['span']} {s['label']}" for s in opens],
                "checks": _checks.run(),
                "say": f"span {sid} open for {label!r}"
                       + (f"; {len(opens)} other span(s) still open" if opens else "")}

    @srv.tool("span_mark",
              "A checkpoint inside an open span: elapsed and tokens since the start and "
              "since the last mark. Use it between steps so the report can say where the "
              "time and tokens went.",
              {"type": "object",
               "properties": {"span": _SPAN, "tokens_left": _TOK, "note": _NOTE,
                              "prompt": {"type": "boolean",
                                         "description": ("true when this mark is the count after a "
                                                         "prompt; with usage.capture on it writes one "
                                                         "prompt row (a date and the count) to the frame")}}})
    def _mark(args):
        s = L.pick(args.get("span"))
        if not s["open"]:
            raise ToolError(f"span {s['span']} is already stopped; marks go in open spans")
        tl = _tokens(args)
        prev = s["marks"][-1] if s["marks"] else {"ts": s["started"], "tokens_left": s["tokens_start"]}
        row = L.append("mark", s["span"], s["label"], tl, args.get("note") or "")
        since_prev = int((_parse(row["ts"]) - _parse(prev["ts"])).total_seconds())
        since_start = int((_parse(row["ts"]) - _parse(s["started"])).total_seconds())
        figs = [s["tokens_start"]] + [m["tokens_left"] for m in s["marks"]]
        last_known = next((f for f in reversed(figs) if f is not None), None)
        reset = _is_reset(last_known, tl)
        tok_prev = (None if reset else
                    prev["tokens_left"] - tl if prev["tokens_left"] is not None and tl is not None else None)
        tok_start = (_legs(figs + [tl])[0]
                     if s["tokens_start"] is not None and tl is not None else None)
        frame = (F.prompt(s["span"], tl) if reset or args.get("prompt")
                 else "no prompt seen at this mark: no frame row")
        return {"span": s["span"], "label": s["label"], "mark": len(s["marks"]) + 1, "ts": row["ts"],
                "seconds_since_start": since_start, "seconds_since_last": since_prev,
                "tokens_since_start": tok_start, "tokens_since_last": tok_prev, "reset": reset,
                "frame": frame,
                "say": f"mark {len(s['marks']) + 1} on {s['label']!r}: {_hms(since_prev)} since last"
                       + (f", {tok_prev:,} tokens" if tok_prev is not None else "")
                       + ("; reset seen: the token figure rose (a new prompt, or the app's own "
                          "housekeeping), so this leg is not counted" if reset else "")}

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
        tl = _tokens(args)
        figs = [s["tokens_start"]] + [m["tokens_left"] for m in s["marks"]]
        last_known = next((f for f in reversed(figs) if f is not None), None)
        L.append("stop", s["span"], s["label"], tl, note)
        frame = (F.prompt(s["span"], tl) if _is_reset(last_known, tl)
                 else "no prompt seen at this stop: no frame row")
        closed = next(x for x in L.spans() if x["span"] == s["span"])
        return {**_summary(closed), "ledger": str(L.path), "frame": frame}

    @srv.tool("question_log",
              "Log one question put to a person, for the question gauge (bin/qg1ck). Give "
              "question_id, frame (one, or two when a second question rides with it), the "
              "question's words, a likelihood guess and the confidence that the second could be "
              "skipped (0.17 or 17%; his bar: two together only at 17% or less). After the answer, "
              "call again with question_id and second_needed (yes, no or unasked). Writes one "
              "gauge row to the usage frame only when usage.capture is on; nothing otherwise.",
              {"type": "object",
               "properties": {"question_id": {"type": "string", "description": "a short id for the question"},
                              "frame": {"type": "string", "enum": list(QUESTION_FRAMES)},
                              "question": {"type": "string", "description": "the question's words, one line"},
                              "likelihood": {"type": "string",
                                             "description": "guessed likelihood the second is needed: low, medium, high or a number"},
                              "confidence": {"type": "string",
                                             "description": "confidence the second could be skipped: 0.17 or 17%"},
                              "second_needed": {"type": "string", "enum": list(SECOND_ANSWERS),
                                                "description": "after the answer: was the second question needed?"},
                              "span": _SPAN},
               "required": ["question_id"]})
    def _question(args):
        qid = args.get("question_id")
        sess = _clean(args.get("span") or "")
        if args.get("second_needed"):
            frame = F.second_needed(qid, args["second_needed"], sess)
            return {"question_id": _clean(qid), "frame": frame,
                    "say": f"question {_clean(qid)}: second needed = {args['second_needed']}; {frame}"}
        if not args.get("frame") or not _clean(args.get("question") or ""):
            raise ToolError("give frame and question (or second_needed, after the answer)")
        frame = F.question(qid, args["frame"], args["question"], args.get("likelihood") or "",
                           str(args.get("confidence") or ""), sess)
        c = confidence_value(str(args.get("confidence") or ""))
        warn = ("" if args["frame"] != "two" else
                "; no confidence number: qg1ck will count this two-question frame as a fault" if c is None else
                f"; confidence {c:.2f} is above his bar 0.17: qg1ck will count this as a fault" if c > 0.17 + 1e-9 else
                "")
        return {"question_id": _clean(qid), "frame": frame,
                "say": f"question {_clean(qid)} ({args['frame']}) logged: {frame}{warn}"}

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
        resets = sum(s.get("resets", 0) for s in spans)
        shown = spans[-int(args["limit"]):] if args.get("limit") else spans
        return {"ledger": str(L.path), "exists": L.path.is_file(),
                "count": len(spans), "open": [s["span"] for s in spans if s["open"]],
                "seconds": tot_sec, "tokens": sum(tok_known), "tokens_known_for": len(tok_known),
                "resets": resets,
                "by_label": sorted(by_label.values(), key=lambda b: -b["seconds"]),
                "spans": [_summary(s) for s in shown],
                "say": (f"{len(spans)} span(s), {_hms(tot_sec)} in all"
                        + (f", {sum(tok_known):,} tokens across the {len(tok_known)} with figures"
                           if tok_known else ", no token figures yet")
                        + (f"; {_resets_words(resets)}" if resets else "")
                        + (f"; {sum(1 for s in spans if s['open'])} still open"
                           if any(s["open"] for s in spans) else "")) if spans else
                       f"no spans yet in {L.path}"}
