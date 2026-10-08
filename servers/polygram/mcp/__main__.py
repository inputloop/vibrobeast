# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""Run one of the servers, or prove they can fail.

    python -m polygram.mcp mentcached        speak JSON-RPC on stdio
    python -m polygram.mcp persona
    python -m polygram.mcp skillx
    python -m polygram.mcp llamabridge       off until the llamabridge.on preference is set
    python -m polygram.mcp tavernface        Bryant's Tavern; off until the tavern.on preference is set
    python -m polygram.mcp c4face            C4's own MCP server, from your C4 tree (c4.root), run with node
    python -m polygram.mcp --list            each server, and its tools
    python -m polygram.mcp --prove-red       every refusal, fired on purpose
"""

from __future__ import annotations

import sys

from . import SERVERS


def _prove_red() -> int:
    """A harness that cannot fail is not running.

    Fire each refusal deliberately and require it. If any of these stops
    refusing, the guard it belongs to has quietly stopped guarding.
    """
    import io
    import json
    import tempfile
    from pathlib import Path

    from . import mentcached, persona, skillx, store as _store

    failures: list[str] = []

    def want(label: str, cond: bool, why: str) -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            failures.append(f"{label}: {why}")

    print("prove-red: firing every refusal on purpose")

    with tempfile.TemporaryDirectory() as td:
        seat = Path(td) / "nowhere" / "deep" / "seat"
        jail = Path(td) / "jail"
        jail.mkdir(parents=True)

        # R1 -- a write while JAILED is refused unless asked for.
        srv = mentcached.build(by="prove-red", seat=Path(td) / "gone" / "x" / "y" / "z",
                               jail=jail)
        # Force the jail: the seat root's parent does not exist, so mode()
        # falls to the jail.
        try:
            srv.call("seat_append", {"seam": "red", "text": "x",
                                     "source": "them", "would_change": "y"})
            want("JAILED write refused", False, "it was allowed")
        except Exception as exc:                                   # noqa: BLE001
            want("JAILED write refused", "JAILED" in str(exc),
                 f"refused for the wrong reason: {exc}")

        # R2 -- the same write, asked for, lands AND is stamped JAILED.
        out = srv.call("seat_append", {"seam": "red", "text": "x",
                                       "source": "them", "would_change": "y",
                                       "allow_jailed": True})
        want("allowed JAILED write is stamped", out.get("mode") == _store.JAILED,
             f"mode was {out.get('mode')!r}")
        got = srv.call("seat_read", {"seam": "red"})
        want("JAILED is in the bytes forever",
             "mode: JAILED" in (got.get("note") or ""),
             "the generation does not carry mode: JAILED")

        # R3 -- an unsourced note is refused.
        try:
            srv.call("seat_append", {"seam": "r3", "text": "x", "source": "",
                                     "would_change": "y", "allow_jailed": True})
            want("unsourced note refused", False, "it was allowed")
        except Exception as exc:                                   # noqa: BLE001
            want("unsourced note refused", "source" in str(exc), str(exc))

        # R4 -- an unfalsifiable note is refused.
        try:
            srv.call("seat_append", {"seam": "r4", "text": "x", "source": "them",
                                     "would_change": "", "allow_jailed": True})
            want("unfalsifiable note refused", False, "it was allowed")
        except Exception as exc:                                   # noqa: BLE001
            want("unfalsifiable note refused", "would_change" in str(exc), str(exc))

        # R5 -- a bare absolute path FAULTs.
        lk = srv.call("link_check", {"text": "see /f/claude/c4/h/x.md for this"})
        want("bare host path FAULTs", lk.get("verdict") == "FAULT",
             f"verdict was {lk.get('verdict')!r}")
        lk2 = srv.call("link_check", {"text": "see c4:/h/x.md and [[two-columns]]"})
        want("schemed + wiki links pass", lk2.get("verdict") == "OK",
             f"verdict was {lk2.get('verdict')!r}")

        # R6 -- lowering a semaphore without the ceremony is refused.
        srv.call("semaphore_raise", {"name": "red", "why": "prove-red"})
        try:
            srv.call("semaphore_lower", {"name": "red", "ceremony": ""})
            want("silent semaphore lower refused", False, "it was allowed")
        except Exception as exc:                                   # noqa: BLE001
            want("silent semaphore lower refused", "ceremony" in str(exc), str(exc))

        # R7 -- persona is never minted on absence.
        p = persona.build(by="prove-red", root=Path(td) / "p", jail=None)
        res = p.call("persona_resolve", {"name": "nobody"})
        want("absent persona is a FAULT, not a mint",
             "NOT SERVED" in res.get("say", ""), res.get("say", ""))
        want("no sheet was created",
             not (Path(td) / "p" / "notes" / "nobody").exists(),
             "a directory appeared for a persona that does not exist")

        # R8 -- a mutation with no evidence is refused.
        try:
            p.call("persona_mutate", {"name": "x", "entry": "I grew.",
                                      "evidence": "", "would_change": "z"})
            want("storyless-evidence mutation refused", False, "it was allowed")
        except Exception as exc:                                   # noqa: BLE001
            want("storyless-evidence mutation refused", "evidence" in str(exc), str(exc))

        # R9 -- skillx refuses, and says whose blocker it is.
        x = skillx.build()
        try:
            x.call("skillx_offer", {"skill": "a", "party": "b"})
            want("skillx refuses to offer", False, "it offered")
        except Exception as exc:                                   # noqa: BLE001
            want("skillx refuses to offer",
                 "B1" in str(exc) and "B2" in str(exc) and "B3" in str(exc), str(exc))

        # R10 -- a tool that forgets the mode word cannot return.
        from .rpc import Server as _S
        bad = _S(name="bad", version="0", require_mode=True, mode_fn=None)
        bad.tool("naked", "returns nothing about the seat")(lambda a: {"x": 1})
        try:
            bad.call("naked", {})
            want("modeless result refused", False, "it was returned")
        except Exception as exc:                                   # noqa: BLE001
            want("modeless result refused", "mode" in str(exc), str(exc))

        # R12 -- a stop with nothing open is refused; R13 -- a second stop too.
        import os as _os
        from . import spans as _spans
        _keep = _spans.DEFAULT_LEDGER
        _spans.DEFAULT_LEDGER = Path(td) / "stats" / "spans.tsv"
        _os.environ.pop("MENTCACHED_STATS", None)
        try:
            srv2 = mentcached.build(by="prove-red", seat=Path(td) / "seat2", jail=None)
            try:
                srv2.call("span_stop", {})
                want("stop with nothing open refused", False, "it stopped nothing")
            except Exception as exc:                               # noqa: BLE001
                want("stop with nothing open refused", "span_start first" in str(exc), str(exc))
            sp = srv2.call("span_start", {"label": "red"})
            srv2.call("span_stop", {"span": sp["span"]})
            try:
                srv2.call("span_stop", {"span": sp["span"]})
                want("second stop refused", False, "it stopped twice")
            except Exception as exc:                               # noqa: BLE001
                want("second stop refused", "already stopped" in str(exc), str(exc))
        finally:
            _spans.DEFAULT_LEDGER = _keep

        # R14 -- freshness never says CURRENT about a shelf that is not a plugin tree,
        # and never says CURRENT from a source tree.
        from . import freshness as _fresh
        fr = _fresh.report({"shelf": td})
        want("freshness refuses a non-plugin shelf", fr.get("verdict") == "UNKNOWN", fr.get("say", ""))

        # R15 -- an unknown preference key is refused; R16 -- the loader never reads outside a skill.
        from . import prefs as _prefs, softskills as _ss
        _kp = _prefs.DEFAULT_PATH; _prefs.DEFAULT_PATH = Path(td) / "prefs.tsv"
        _os.environ.pop("MENTCACHED_PREFS", None); _os.environ["SOFT_SKILLS"] = str(Path(td) / "SS")
        try:
            try:
                _prefs.set_("nobody.reads.this", "x", "prove-red", "")
                want("unknown preference refused", False, "it was written")
            except Exception as exc:                               # noqa: BLE001
                want("unknown preference refused", "unknown preference" in str(exc), str(exc))
            (Path(td) / "SS" / "s").mkdir(parents=True)
            (Path(td) / "SS" / "s" / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\nb\n", encoding="utf-8", newline="\n")
            (Path(td) / "secret").write_text("no", encoding="utf-8", newline="\n")
            try:
                _ss.read({"name": "s", "file": "../secret"})
                want("loader refuses a path outside the skill", False, "it read it")
            except Exception as exc:                               # noqa: BLE001
                want("loader refuses a path outside the skill", "inside the skill folder" in str(exc), str(exc))
        finally:
            _prefs.DEFAULT_PATH = _kp; _os.environ.pop("SOFT_SKILLS", None)

        # R11 -- the initialize handshake actually answers.
        buf = io.StringIO()
        srv.serve(stdin=io.StringIO(
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}) + "\n"),
            stdout=buf)
        want("initialize answers", '"protocolVersion"' in buf.getvalue(),
             buf.getvalue()[:200])

    print()
    if failures:
        print(f"prove-red FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("prove-red PASS: every refusal fired on purpose")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    if argv[0] == "--list":
        import importlib
        for name in SERVERS:
            s = importlib.import_module(f".{name}", __package__).build()
            print(f"{s.name:<12} v{s.version:<8} {len(s.tools)} tools")
            for t in s.tools:
                print(f"    {t.name}")
        return 0
    if argv[0] == "--prove-red":
        return _prove_red()
    name = argv[0]
    if name not in SERVERS:
        print(f"unknown server: {name} (have: {', '.join(SERVERS)})", file=sys.stderr)
        return 2
    import importlib
    mod = importlib.import_module(f".{name}", __package__)
    return mod.main(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
