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
    python -m polygram.mcp hub               all six behind one stdio door (the desktop extension)
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

    def want(label: str, cond: bool, why: str = "") -> None:
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

        # R17 -- a reset never yields a negative count (lane A, extension edition).
        from . import spans as _sp17
        _l17 = _sp17.Ledger(Path(td) / "r17.tsv", True, "prove-red")
        _l17.append("start", "r17", "r17", 1000, "")
        _l17.append("mark", "r17", "r17", 400, "")
        _l17.append("mark", "r17", "r17", 5000, "")          # the figure rose: a new prompt
        _l17.append("stop", "r17", "r17", 4900, "")
        _s17 = next(s for s in _l17.spans() if s["span"] == "r17")
        want("a reset never yields a negative count",
             _s17["tokens_used"] == 700 and _s17["resets"] == 1,
             f"tokens_used={_s17['tokens_used']} resets={_s17.get('resets')}")
        # R18 -- capture off writes no row (lane A, extension edition).
        _kp18 = _prefs.DEFAULT_PATH; _prefs.DEFAULT_PATH = Path(td) / "r18-prefs.tsv"
        _fr18 = Path(td) / "r18-fr"; _fr18.write_text("", encoding="utf-8", newline="\n")
        _old18 = _os.environ.get("MENTCACHED_FRAME"); _os.environ["MENTCACHED_FRAME"] = str(_fr18)
        _os.environ.pop("MENTCACHED_PREFS", None)
        try:
            _f18 = _sp17.Frame("prove-red")
            _f18.start("r18", 1000); _f18.prompt("r18", 5000); _f18.pref("tone.show", "words")
            want("capture off writes no row", _fr18.read_text(encoding="utf-8") == "",
                 f"{len(_fr18.read_text(encoding='utf-8').splitlines())} row(s) written")
        finally:
            _prefs.DEFAULT_PATH = _kp18
            if _old18 is None:
                _os.environ.pop("MENTCACHED_FRAME", None)
            else:
                _os.environ["MENTCACHED_FRAME"] = _old18

        # R19 -- a PERSONA-less actor still speaks (lane B, card 11).
        import os as _os19
        _ks = _os19.environ.get("PERSONA_SHEETS")
        (Path(td) / "no-sheets").mkdir(exist_ok=True)
        _os19.environ["PERSONA_SHEETS"] = str(Path(td) / "no-sheets")
        try:
            r19 = persona.build(by="prove-red", root=Path(td) / "p19", jail=None).call(
                "persona_resolve", {"name": "nobody"})
            dv = r19.get("default_voice") or {}
            want("a persona-less actor still speaks",
                 "NOT SERVED" in r19.get("say", "") and dv.get("voice") == "plain"
                 and bool(str(dv.get("line", "")).strip()) and "\n" not in dv.get("line", ""),
                 repr(r19)[:200])
        finally:
            if _ks is None:
                _os19.environ.pop("PERSONA_SHEETS", None)
            else:
                _os19.environ["PERSONA_SHEETS"] = _ks
        # R20 -- the ledger states nothing that no sheet says (lane B, card 19).
        import os as _os20
        _ks = _os20.environ.get("PERSONA_SHEETS")
        d20 = Path(td) / "sheets20"; d20.mkdir(exist_ok=True)
        (d20 / "CHARACTER-alpha.md").write_text(
            "# CHARACTER SHEET -- alpha\nactor: system\n" + "x\n" * 16
            + "R20-BODY-LINE\n\n## Whose inverse I carry\n\n- nobodyr20 : a name no sheet is\n",
            encoding="utf-8", newline="\n")
        _os20.environ["PERSONA_SHEETS"] = str(d20)
        try:
            l20 = persona.ledger([])
            want("the ledger states nothing that no sheet says",
                 not l20["edges"] and any(f["name"] == "nobodyr20" for f in l20["faults"])
                 and "R20-BODY-LINE" not in l20["markdown"],
                 l20.get("say", "")[:200])
        finally:
            if _ks is None:
                _os20.environ.pop("PERSONA_SHEETS", None)
            else:
                _os20.environ["PERSONA_SHEETS"] = _ks

        # R21 -- a prose file with a code licence is refused at release (bin/lc1ck).
        # R22 -- no NEWS entry and no reason line refuses the release (bin/release).
        import shutil as _sh, subprocess as _sp
        _bin = Path(__file__).resolve().parents[2] / "bin"
        if (_bin / "lc1ck").is_file() and (_bin / "release").is_file() and _sh.which("sh"):
            _md = Path(td) / "r21" / "notes.md"; _md.parent.mkdir(parents=True)
            _md.write_text("# n\n\nprose\n\nSPDX-License-Identifier: GPL-3.0-or-later\n", encoding="utf-8", newline="\n")
            _r = _sp.run(["sh", str(_bin / "lc1ck"), str(_md)], capture_output=True, text=True, encoding="utf-8")
            want("prose with a code licence refused", _r.returncode == 1 and "code licence on prose" in _r.stdout,
                 f"rc={_r.returncode} {_r.stdout[-200:]}")
            _g = Path(td) / "r22"
            for _d in ("bin", "polygram", "dist/vibrobeast"):
                (_g / _d).mkdir(parents=True, exist_ok=True)
            _sh.copy(_bin / "release", _g / "bin" / "release"); _sh.copy(_bin / "lc1ck", _g / "bin" / "lc1ck")
            (_g / "polygram" / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8", newline="\n")
            (_g / "NEWS").write_text("polygram NEWS\n\nVersion 9.9.8\n\n- older.\n", encoding="utf-8", newline="\n")
            _r = _sp.run(["sh", str(_g / "bin" / "release"), "--prose-gates"], capture_output=True, text=True, encoding="utf-8")
            want("no NEWS and no reason refuses the release", _r.returncode != 0 and "NEWS has no entry" in (_r.stdout + _r.stderr),
                 f"rc={_r.returncode} {(_r.stdout + _r.stderr)[-200:]}")
        else:
            print("  NOT CHECKED  R21/R22: no bin/lc1ck or bin/release here (a minted plugin); not counted")

        # R24 -- br1in never writes into a drop (lane D, extension edition).
        import subprocess as _sub24
        _br24 = Path(__file__).resolve().parents[2] / "bin" / "br1in"
        if _br24.exists():
            _d24 = Path(td) / "r24" / "from" / "2026-01-02"; _d24.mkdir(parents=True)
            (_d24 / "NOTE.txt").write_text("r24\n", encoding="utf-8", newline="\n")
            _b24 = sorted(str(p) for p in _d24.rglob("*"))
            _rc24 = _sub24.run(["sh", str(_br24), "--no-also", "--out", str(_d24 / "reports"), str(_d24)],
                               capture_output=True).returncode
            _a24 = sorted(str(p) for p in _d24.rglob("*"))
            want("br1in never writes into a drop", _rc24 == 3 and _b24 == _a24,
                 f"exit={_rc24}, entries {len(_b24)} -> {len(_a24)}")

        # R25 -- the frame has a writer for question rows (fix lane F1, pass 2).
        from polygram.mcp import spans as _sp25
        _r25 = _sp25.Frame("r25")._row("gauge", "s", None, key="question", value="two", label="q1",
                                       likelihood="medium", confidence="17%", note="go on?").split("\t")
        _c25 = dict(zip(_sp25.FRAME_COLUMNS, _r25))
        want("the frame writes a question row qg1ck can read",
             (_c25["KEY"], _c25["LABEL"], _c25["CONFIDENCE"], _c25["NOTE"]) == ("question", "q1", "17%", "go on?")
             and _sp25.confidence_value("17%") == _sp25.confidence_value("0.17") == 0.17,
             f"row {_c25}")
        # R26 -- a room rule is not anyone's to write (fix lane F1, pass 2).
        from polygram.mcp import prefs as _pf26
        _w26 = _pf26.writer("room.garden.quiet", "stranger", "", names=["corwin", "bryant"], room="garden")
        _k26 = _pf26.writer("room.garden.quiet", _pf26.keeper(), "", names=["corwin", "bryant"])
        _b26 = _pf26.writer("room.garden.quiet", "bryant", "", names=["corwin", "bryant"], room="garden")
        want("a room.<tavern> row is written only by the keeper or a named participant in that room",
             bool(_w26) and _k26 == "" and _b26 == "", f"stranger={_w26!r} keeper={_k26!r} bryant={_b26!r}")

        # R27 -- "17" is a slip for 17%: refused at write, with the form to use (fix lane F3, pass 3).
        from polygram.mcp import spans as _sp27
        from polygram.mcp.rpc import ToolError as _TE27
        try:
            _sp27.Frame("r27").question("q17", "two", "go on?", "medium", "17")
            _m27 = ""
        except _TE27 as e:
            _m27 = str(e)
        want("a bare number above 1 is refused as a confidence, saying how to write it",
             "write 17% or 0.17" in _m27, f"got {_m27!r}")
        # R28 -- an answer names a question that was logged (fix lane F3, pass 3).
        import os as _os28
        from pathlib import Path as _P28
        from polygram.mcp import spans as _sp28
        from polygram.mcp.rpc import ToolError as _TE28
        _fr28 = _P28(td) / "r28-fr"
        _fr28.write_text("\t".join(["2026-10-10T00:00:00Z", "gauge", "", "", "q1", "", "r28", "question",
                                    "one", "", "", "go on?"]) + "\n", encoding="utf-8", newline="\n")
        _old28 = _os28.environ.get("MENTCACHED_FRAME"); _os28.environ["MENTCACHED_FRAME"] = str(_fr28)
        _cap28 = _sp28.Frame.capture_on; _sp28.Frame.capture_on = staticmethod(lambda: True)
        try:
            try:
                _sp28.Frame("r28").second_needed("never", "yes"); _m28 = ""
            except _TE28 as e:
                _m28 = str(e)
            _ok28 = _sp28.Frame("r28").second_needed("q1", "no")
            want("second_needed for an id never logged is refused; a logged one is written",
                 "never logged" in _m28 and "written" in _ok28
                 and _fr28.read_text(encoding="utf-8").count("second_needed") == 1,
                 f"never={_m28!r} logged={_ok28!r}")
        finally:
            _sp28.Frame.capture_on = _cap28
            if _old28 is None:
                _os28.environ.pop("MENTCACHED_FRAME", None)
            else:
                _os28.environ["MENTCACHED_FRAME"] = _old28

        # R29 / R30 -- the garden view (lane G, turn 2): build into td, recount in awk, then plant a fault.
        import subprocess as _sp29, os as _os29
        _root29 = _os29.path.dirname(_os29.path.dirname(_os29.path.abspath(__import__("polygram").__file__)))
        _out29 = _os29.path.join(td, "garden-view")
        _b29 = _sp29.run(["python3", _os29.path.join(_root29, "bin", "gv1mt"), "build", "--root", _root29,
                          "--out", _out29, "--at", "2026-10-10T00:00:00Z"], capture_output=True, text=True, encoding="utf-8")
        _awk29 = _os29.path.join(_root29, "tests", "gv1mt-recount.awk")
        _r29 = _sp29.run(["awk", "-f", _awk29, _os29.path.join(_out29, "data.json"),
                          _os29.path.join(_out29, "garden-view.facts"), _os29.path.join(_out29, "index.html")],
                         capture_output=True, text=True, encoding="utf-8")
        want("the garden view builds and its awk recount agrees with its counts",
             _b29.returncode == 0 and _r29.returncode == 0 and "GREEN" in _r29.stdout)
        _f30 = _os29.path.join(_out29, "garden-view.facts")
        with open(_f30, encoding="utf-8") as _h30:
            _ls30 = _h30.read().splitlines(True)
        _cut30 = next(i for i, l in enumerate(_ls30) if l.startswith("NODE "))
        with open(_f30, "w", encoding="utf-8", newline="") as _h30:
            _h30.writelines(_ls30[:_cut30] + _ls30[_cut30 + 1:])
        _r30 = _sp29.run(["awk", "-f", _awk29, _os29.path.join(_out29, "data.json"), _f30,
                          _os29.path.join(_out29, "index.html")], capture_output=True, text=True, encoding="utf-8")
        want("the garden view's recount goes red when a NODE line is missing",
             _r30.returncode == 1 and "MISMATCH" in _r30.stdout)

        # R37 -- a quoted soft-skill name reads without its quotes (lane B, turn 2).
        from polygram.mcp import softskills as _ss37
        _f37 = _ss37._frontmatter('---\nname: "parallax"\ndescription: \'it\'\'s "his"\'\n---\n')
        want("a YAML-quoted soft-skill name reads without its quotes",
             _f37.get("name") == "parallax" and _f37.get("description") == 'it\'s "his"', repr(_f37))
        # R38 -- tg1rs answers WORD for an unknown cast and exits 0 (lane B, turn 2).
        import subprocess as _sub38
        _tg38 = Path(__file__).resolve().parents[2] / "bin" / "tg1rs"
        if _tg38.exists():
            _c38 = Path(td) / "r38-casts.tsv"
            _c38.write_text("# cast\ttable\tkey\tkind\tby\n", encoding="utf-8", newline="\n")
            _r38 = _sub38.run(["sh", str(_tg38), "--casts", str(_c38), "resolve", "[r38 (nosuch)x]"],
                              capture_output=True, text=True, encoding="utf-8")
            want("an unknown cast answers WORD and keeps the tag",
                 _r38.returncode == 0 and _r38.stdout.startswith("WORD\t") and "[r38 (nosuch)x]" in _r38.stdout,
                 f"rc={_r38.returncode} {_r38.stdout[:160]!r}")
        else:
            print("  NOT CHECKED  R38: no bin/tg1rs here (a minted plugin); not counted")

        # R41 -- garden family-cut holds are well formed (lane D, turn 2).
        _root41 = Path(__file__).resolve().parents[2]
        _h41 = _root41 / "conventions" / "FAMILY-HOLDS.tsv"
        _rows41 = [l.split("\t") for l in _h41.read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.startswith("#")] if _h41.exists() else []
        want("every garden family-cut hold has four fields and a class of BLIND, LOCAL or NEVER",
             _h41.exists() and all(len(r) >= 4 and r[1] in ("BLIND", "LOCAL", "NEVER") and r[2] and r[3]
                                   for r in _rows41), repr(_rows41[:2]))
        # R42 -- reviewed secret lines are bound (lane D, turn 2).
        import re as _re42
        _s42 = Path(__file__).resolve().parents[2] / "conventions" / "SECRET-REVIEWED.tsv"
        _rows42 = [l.split("\t") for l in _s42.read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.startswith("#")] if _s42.exists() else []
        want("every reviewed secret line is bound to a path, a line number and a 16-hex line hash",
             all(len(r) >= 5 and r[1].isdigit() and _re42.fullmatch(r"[0-9a-f]{16}", r[2]) for r in _rows42),
             repr(_rows42[:1]))

        # R43 -- the desktop extension (2026-10-11): a settings field the server reads but the
        # manifest does not declare is refused, and so is a declared field nothing reads.
        import copy as _cp43
        from .. import mcpb as _mb43
        _m43 = _mb43.manifest()
        want("an extension manifest as minted has no problems", _mb43.problems(_m43) == [],
             repr(_mb43.problems(_m43)))
        _b43 = _cp43.deepcopy(_m43)
        del _b43["user_config"]["c4_root"]
        want("a ${user_config.x} with no declared field is refused",
             any("c4_root" in x for x in _mb43.problems(_b43)), repr(_mb43.problems(_b43)))
        _b43 = _cp43.deepcopy(_m43)
        _b43["user_config"]["orphan"] = {"type": "string", "title": "orphan"}
        want("a declared settings field nothing reads is refused",
             any("orphan" in x for x in _mb43.problems(_b43)), repr(_mb43.problems(_b43)))

        # R44 -- the settings page's off is OFF; an unfilled template says nothing.
        import os as _os44
        from .rpc import env_switch as _sw44
        _old44 = _os44.environ.get("C4_ON")
        try:
            _os44.environ["C4_ON"] = "false"
            want("C4_ON=false reads as off, not as unset", _sw44("C4_ON") is False)
            _os44.environ["C4_ON"] = "${user_config.c4_on}"
            want("an unfilled settings template reads as unset", _sw44("C4_ON") is None)
        finally:
            if _old44 is None:
                _os44.environ.pop("C4_ON", None)
            else:
                _os44.environ["C4_ON"] = _old44

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
    if name == "hub":
        from . import hub
        return hub.main(argv[1:])
    if name not in SERVERS:
        print(f"unknown server: {name} (have: {', '.join(SERVERS)})", file=sys.stderr)
        return 2
    import importlib
    mod = importlib.import_module(f".{name}", __package__)
    return mod.main(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
