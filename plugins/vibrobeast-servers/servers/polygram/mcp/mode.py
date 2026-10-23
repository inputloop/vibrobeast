# polygram -- gated agent-skill synthesis.
# Copyright 2026 Corwin Brust <corwin@bru.st> and Bryant Frankford <nathanielfrankford@gmail.com> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
"""mode -- LAB or WORKSHOP: how much checking and measuring a task gets (2026-10-23).

Corwin, 11:04: a LAB is "more checks, more measurement, each run being a chance to learn from to improve
calibration"; a WORKSHOP assumes the calibration is valid and confirms against the baselines.  Two strokes
on the settings page: the default (``mode_default``, MENTCACHED_MODE: workshop or lab; empty is workshop),
and whether chat may switch it for a while (``mode_chat``, MENTCACHED_MODE_CHAT: off by default, which
means only the settings page changes it).

One log, append-only: ``~/.mentcached/mode.tsv`` (MENTCACHED_MODE_LOG names another), one row per change,
``ts event mode chat until keeper turn why``.  ``settings`` rows record the settings page as this server saw
it at start; ``set`` rows are mode_set (until is epoch seconds); ``clear`` rows are mode_clear.  The answer
(``answer()``): the last settings row gives the default, whether chat may switch, and who the keeper is;
the last set/clear row overrides only if it is a set, chat is allowed, its turn is that keeper, and now is
before its until.  bin/md1rd reads the same log in sh (a shell never sees the settings page; this server
writes it out), and tests/mode-reader.tcl holds the two to one answer.  The default is never written by a
tool: a settings row comes only from the settings page.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
import time
from pathlib import Path

from .rpc import ToolError, env_switch

MODES = ("workshop", "lab")
HEADER = "ts\tevent\tmode\tchat\tuntil\tkeeper\tturn\twhy"
HOURS_DEFAULT = 9     # house number: a working day
HOURS_MAX = 17        # house number: never past the next morning


def log_path() -> Path:
    raw = os.environ.get("MENTCACHED_MODE_LOG", "").strip()
    return Path(raw).expanduser() if raw and "${" not in raw else Path.home() / ".mentcached" / "mode.tsv"


def settings_now() -> dict:
    """The settings page as this process sees it: default, chat, keeper."""
    raw = (os.environ.get("MENTCACHED_MODE") or "").strip().lower()
    default = raw if raw in MODES else "workshop"
    chat = "allowed" if env_switch("MENTCACHED_MODE_CHAT") is True else "settings-only"
    from . import prefs, orglimits
    lim = orglimits.chat_switch()
    out = {"mode": default, "chat": chat, "keeper": prefs.keeper(), "page_chat": chat, "org": None}
    if lim is not None:
        out["org"] = lim                         # an ORG.md can only narrow: must not closes the switch
        if lim["strength"] == "must not":
            out["chat"] = "settings-only"
    return out


def rows(p: Path | None = None) -> list[list[str]]:
    p = p or log_path()
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        f = line.split("\t")
        if len(f) == 8:
            out.append(f)
    return out


def answer(rs: list[list[str]], now: float | None = None) -> dict:
    """{mode, default, chat, keeper, source, say} from the log's rows."""
    now = time.time() if now is None else now
    s = next((r for r in reversed(rs) if r[1] == "settings"), None)
    default = s[2] if s and s[2] in MODES else "workshop"
    chat = s[3] if s and s[3] in ("allowed", "settings-only") else "settings-only"
    keeper = s[5] if s and s[5] != "-" else ""   # "-" is how the log writes "nobody named"
    o = next((r for r in reversed(rs) if r[1] in ("set", "clear")), None)
    base = {"default": default, "chat": chat, "keeper": keeper}
    if o and o[1] == "set" and o[2] in MODES:
        try:
            until = int(o[4])
        except ValueError:
            until = 0
        why_not = ("chat may not switch the mode (settings-only)" if chat != "allowed"
                   else "set on someone else's turn" if o[6].lower() != keeper.lower() or not keeper
                   else "it ran out" if now >= until else "")
        if not why_not:
            left = int((until - now) // 60)
            return {**base, "mode": o[2], "source": "chat", "until": until,
                    "say": f"{o[2]} for this task, set on {o[6]}'s turn ({left} min left); the default is {default}"}
        return {**base, "mode": default, "source": "settings",
                "say": f"{default} (the settings page); a {o[2]} override is not in force: {why_not}"}
    return {**base, "mode": default, "source": "settings" if s else "none",
            "say": f"{default} (the settings page)" if s else "workshop (nothing recorded yet)"}


def _append(row: list[str], p: Path | None = None) -> None:
    p = p or log_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(HEADER + "\n", encoding="utf-8", newline="\n")
    one = lambda x: " ".join(str(x).split()) or "-"   # noqa: E731
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(one(x) for x in row) + "\n")


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_settings(p: Path | None = None) -> dict:
    """Write a settings row when the page differs from the last one recorded; return the page."""
    s = settings_now()
    last = next((r for r in reversed(rows(p)) if r[1] == "settings"), None)
    why = "the settings page" + (f"; chat narrowed by ORG.md {s['org']['hash'][:16]}"
                                 if s["org"] and s["chat"] != s["page_chat"] else "")
    if not last or (last[2], last[3], last[5]) != (s["mode"], s["chat"], s["keeper"]):
        _append([_ts(), "settings", s["mode"], s["chat"], "-", s["keeper"], "-", why], p)
    return s


def set_mode(mode: str, turn: str, why: str = "", hours: float = HOURS_DEFAULT, task: str = "",
             p: Path | None = None) -> dict:
    s = record_settings(p)
    m = (mode or "").strip().lower()
    if m not in MODES:
        raise ToolError(f"the mode is workshop or lab, not {mode!r}")
    if s["chat"] != "allowed":
        from . import orglimits
        if s["org"] and s["page_chat"] == "allowed":
            raise ToolError(orglimits.say(s["org"]) + f" So the working mode is not switched from chat; it stays "
                            f"{s['mode']}. The settings page still sets it.")
        raise ToolError("The working mode is changed only on the settings page here (You: chat may switch "
                        f"the working mode is off). It stays {s['mode']}.")
    if (turn or "").strip().lower() != s["keeper"].lower():
        raise ToolError(f"Only the keeper ({s['keeper']}) switches the mode, on their own turn; "
                        f"this turn says {turn or 'nobody'}.")
    h = max(0.1, min(float(hours or HOURS_DEFAULT), HOURS_MAX))
    until = int(time.time() + h * 3600)
    _append([_ts(), "set", m, "-", until, s["keeper"], turn.strip().lower(),
             (f"task {task}: " if task else "") + (why or "")], p)
    a = answer(rows(p))
    if s["org"]:                                  # prefer not: it proceeds, and the group's sentence is said
        from . import orglimits
        a = {**a, "org": orglimits.say(s["org"]), "say": a["say"] + ". " + orglimits.say(s["org"])}
    return a


def clear_mode(turn: str, why: str = "", p: Path | None = None) -> dict:
    s = record_settings(p)
    if s["chat"] != "allowed":
        raise ToolError("The working mode is changed only on the settings page here; there is nothing to clear from chat.")
    if (turn or "").strip().lower() != s["keeper"].lower():
        raise ToolError(f"Only the keeper ({s['keeper']}) clears the mode, on their own turn.")
    _append([_ts(), "clear", "-", "-", "-", s["keeper"], turn.strip().lower(), why or ""], p)
    return answer(rows(p))


def register(srv, by: str = "") -> None:
    try:
        record_settings()
    except Exception:   # noqa: BLE001 -- a log we cannot write must not stop the server; mode_get says so
        pass

    @srv.tool("mode_get",
              "The working mode now: workshop (trust the calibrations, confirm against baselines, say only "
              "what falls outside range) or lab (more checks and measurement, prove it first, research before a "
              "build loop when options differ in energy cost, accessibility or fitness for the people served). "
              "Says where it came from: the settings page, or a bounded switch from chat.")
    def _get(_args):
        s = record_settings()
        a = answer(rows())
        if s["org"]:
            from . import orglimits
            a = {**a, "org": orglimits.say(s["org"])}
        return {**a, "log": str(log_path())}

    @srv.tool("mode_set",
              "Switch the working mode for this task or session, for a bounded time (default 9 hours, at most "
              "17). Only when the settings page allows chat to switch it, and only on the keeper's own turn; "
              "never changes the default. Every switch is a row in the mode log.",
              {"type": "object",
               "properties": {"mode": {"type": "string", "enum": list(MODES)},
                              "turn": {"type": "string", "description": "whose turn asked for this, by name"},
                              "task": {"type": "string", "description": "the task or session, in a few words"},
                              "hours": {"type": "number"},
                              "why": {"type": "string", "description": "one line"}},
               "required": ["mode", "turn"]})
    def _set(args):
        return set_mode(args.get("mode", ""), args.get("turn", ""), args.get("why") or "",
                        args.get("hours") or HOURS_DEFAULT, args.get("task") or "")

    @srv.tool("mode_clear",
              "End a switch made from chat: the settings page's default applies again. Keeper's turn only.",
              {"type": "object",
               "properties": {"turn": {"type": "string"}, "why": {"type": "string"}},
               "required": ["turn"]})
    def _clear(args):
        return clear_mode(args.get("turn", ""), args.get("why") or "")


def _main(argv: list[str]) -> int:
    """``--answer FILE [--now EPOCH]``: print the one word, as bin/md1rd does (for the tests)."""
    if len(argv) not in (2, 4) or argv[0] != "--answer" or (len(argv) == 4 and argv[2] != "--now"):
        print("usage: python3 -m polygram.mcp.mode --answer FILE [--now EPOCH]", file=sys.stderr)
        return 2
    now = float(argv[3]) if len(argv) == 4 else None
    print(answer(rows(Path(argv[1])), now)["mode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
