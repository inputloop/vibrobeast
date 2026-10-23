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

"""mentcached-mcp -- the memory seat, served.

The drawing's centre word, glossed in Corwin's own hand underneath it:
**MEM CHECKED ENV**.  That is what this is -- an environment in which a memory
claim has been checked before it is served, rather than a cache that hands back
whatever it was given.

Tool names are plain English, not house names, because strangers read them.

Roots, in order:
  ``$MENTCACHED_SEAT``   the semaphored, multi-consumer seat
  ``$MENTCACHED_JAIL``   the project-local fallback.  Using it is JAILED, and
                         every result says so, and a write there is refused
                         unless the caller asks for it in so many words.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import store as _store
from . import dl2, verify
from . import shipdate as _shipdate
from . import metrics as _metrics
from . import spans as _spans
from . import freshness as _freshness
from . import prefs as _prefs
from . import softskills as _softskills
from . import words as _words
from . import checks as _checks
from .rpc import Server, ToolError

VERSION = "0.1.0"


#: Where a seat goes when nobody said. Chosen, not guessed -- see _roots.
DEFAULT_SEAT = Path.home() / ".mentcached" / "seat"


def _roots() -> tuple[Path, Path | None, bool]:
    """Resolve the seat, and say whether WE chose it or the user did.

    That third value is the whole point, and it exists because of a real
    first-run failure: the plugin shipped `MENTCACHED_SEAT` as an unexpanded
    literal, so a stranger's first "remember this" answered NOTVISIBLE, and the
    only escape -- `seat_open {create: true}` -- created a store at
    ``<whatever directory the MCP process happened to start in>/memory``.
    Launched from `/`, that is `/memory`. Nobody asked for a store there and
    nobody will find it again.

    Two things were wrong and they pull in opposite directions:

      * A RELATIVE default is never right. Where the host starts a subprocess
        is not a decision the user made, so a store placed there is a store
        placed by accident. DEFAULT_SEAT is absolute.
      * ``store.mode()`` deliberately answers NOTVISIBLE for a seat that does
        not exist, because a typo and a first run look identical from inside
        and guessing wrong means serving an empty store as though it were your
        memory. That rule is right and stays.

    The resolution is that those two cases are not actually identical, and the
    difference is WHO NAMED THE PATH:

        we chose it   -> there is no typo to be wrong about, so creating it is
                         safe and a first run just works
        you chose it  -> a missing directory might be your memory with a
                         mistyped name, and we will not invent a substitute

    So: **we may create a path we chose; we may never create a path you chose.**
    An unexpanded ``${VAR}`` counts as nobody having said -- it is a host that
    did not substitute, not a user who typed braces.
    """
    seat = (os.environ.get("MENTCACHED_SEAT") or "").strip()
    jail = (os.environ.get("MENTCACHED_JAIL") or "").strip()
    ours = False
    if not seat or "${" in seat or "%" in seat or seat.startswith("$"):
        seat, ours = str(DEFAULT_SEAT), True
    if jail and ("${" in jail or "%" in jail or jail.startswith("$")):
        jail = ""
    return Path(seat).expanduser(), (Path(jail).expanduser() if jail else None), ours


def _unit_arg(args):
    """The neutral-buoyancy mark, DECLARED by the caller (chainspec U1).

    Absent means "inherit, or 1" -- never "work it out from the text".
    Nothing here may look at the body to choose this number: that would be
    the store forming an opinion about what a note is about, wearing
    arithmetic, which is exactly store rule 4.
    """
    if "unit" not in args or args["unit"] in (None, ""):
        return None
    try:
        u = int(args["unit"])
    except (TypeError, ValueError):
        raise ToolError(
            "unit must be a whole number: it is how many points of meaning "
            "you had mapped to context when you decided how to write this "
            "item. 1 is the honest answer when you had none.") from None
    if u < 1:
        raise ToolError(
            "unit must be at least 1 (chainspec U2). 0 would divide, and "
            "it also claims an item with no neutral point, which this line "
            "cannot express.")
    return u


#: Who is citing, when nobody said. NOT the process id -- see build().
DEFAULT_BY = "claude"


def build(by: str | None = None, seat: Path | None = None,
          jail: Path | None = None) -> Server:
    dseat, djail, ours = _roots()
    # The citer identity must be STABLE across restarts. It used to default to
    # f"mentcached-mcp/{os.getpid()}", which meant every launch of the app was
    # a brand-new consumer: the `citers` list grew without bound, every note's
    # provenance byline recorded a process id, and -- worst -- `buoyancy`
    # ranks each seam against the worlds that cite it, so a store whose citers
    # are all worlds-of-one scores every seam at parity and the orthogonality
    # is silently gone. A default that changes every restart is not an
    # identity; it is a timestamp wearing one.
    st = _store.Store(root=seat or dseat,
                      by=by or (os.environ.get("MENTCACHED_BY") or "").strip()
                      or DEFAULT_BY,
                      jail_root=jail if jail is not None else djail)
    st.seat_is_ours = ours if seat is None else False
    ver = verify.Verifier()
    srv = Server(name="mentcached", version=VERSION, mode_fn=st.mode)

    # `seam` is the required key of most of these tools and was defined in no
    # schema, no description and no README line -- house vocabulary leaking
    # into the one field a stranger must fill in first.
    _SEAM = {"type": "string",
             "description": ("the note's name -- whatever you would call it "
                             "when looking for it again. Any language. Two "
                             "names that differ only in punctuation or case "
                             "are the same note, on purpose, so 'Build notes' "
                             "and 'build-notes' do not quietly become two.")}
    S = {"type": "object", "properties": {"seam": _SEAM}, "required": ["seam"]}

    # SPEC (F1, pass 2, P5 J7, cards 06/12): seat_mode is the session open, so its status line
    # quotes the preferences in force in words (prefs.quote()): a person's own person./room. rows
    # and every seatkeeper "no", shown at their first turn.  With turn, a person sees only their
    # own person.<turn>.* rows, never a third party's.
    def _prefs_line(turn=""):
        try:
            from . import prefs as _prefs
            q = _prefs.quote(turn) #guard:quote
            k, how = _prefs.keeper_and_how()
        except Exception as e:      # noqa: BLE001 -- the seat answers either way
            return f" Preferences could not be read ({e})."
        kl = f" The keeper is {k} (from {how})."     # whose say decides what is kept about people
        return kl + (f" Preferences in force: {q}." if q else " No person, room or declared preferences "
                     "are set, and no folder has a seatkeeper no.")

    @srv.tool("seat_mode",
              "Say plainly whether the seat is SEATED, JAILED or NOTVISIBLE, "
              "and which root produced that answer, and quote the preferences in "
              "force (your own rows and every seatkeeper no). Call this first; every "
              "other result also carries the word. turn: whose first turn this is.",
              {"type": "object",
               "properties": {"turn": {"type": "string",
                                       "description": "the person this session opens for, by name; "
                                                      "they see only their own person rows"}}})
    def _mode(_args):
        _args = _args or {}
        pl = _prefs_line(_args.get("turn") or "")
        m = st.mode()
        if m == _store.NOTVISIBLE and getattr(st, "seat_is_ours", False):
            return {
                "mode": m, "root": str(st.root),
                "jail_root": str(st.jail_root or ""),
                "chosen_by": "this server (nobody set MENTCACHED_SEAT)",
                "checks": _checks.run(),
                "say": ("nothing is stored here yet. This is the DEFAULT "
                        "location, which this server chose rather than you, so "
                        "there is no mistyped path to be wrong about: your "
                        "first note will create it. If you meant a seat "
                        "somewhere else, set MENTCACHED_SEAT and restart -- a "
                        "path YOU name is never created for you, because a "
                        "typo and a first run look identical from here.") + pl,
            }
        say = {
            _store.SEATED: "the semaphored seat is reachable and writable",
            _store.JAILED: ("THE SEAT IS NOT REACHABLE. Only the project-local "
                            "fallback is. Reads are served from the fallback; "
                            "writes are REFUSED unless you pass allow_jailed."),
            _store.NOTVISIBLE: ("neither the seat nor a fallback is reachable "
                                "from here. Nothing can be read or written, and "
                                "no substitute has been chosen for you."),
        }[m]
        return {"mode": m, "root": str(st.root), "jail_root": str(st.jail_root or ""),
                "say": say + "." + pl if not say.endswith(".") else say + pl, "checks": _checks.run()}

    @srv.tool("seat_open",
              "Open the seat, creating it only if you say so. A seat root that "
              "does not exist is NOTVISIBLE, never SEATED -- a typo and a first "
              "run look identical from here, and guessing wrong means serving "
              "an empty store as though it were your memory.",
              {"type": "object",
               "properties": {"create": {"type": "boolean"}}})
    def _open(args):
        create = bool(args.get("create"))
        try:
            st.ensure(create=create)
        except _store.StoreError as exc:
            raise ToolError(str(exc)) from exc
        return {"mode": st.mode(), "root": str(st.active),
                "seams": len(st.seams()),
                "say": f"seat open at {st.active} ({st.mode()})"}

    @srv.tool("seat_list",
              "List the seams in the store, with generation count, citation "
              "pressure and verdict. prefix filters by seam slug.",
              {"type": "object", "properties": {"prefix": {"type": "string"}}})
    def _list(args):
        pref = (args.get("prefix") or "").strip()
        rows = [r for r in st.buoyancy() if r["seam"].startswith(pref)]
        return {"count": len(rows), "seams": rows}

    @srv.tool("seat_read",
              "Read a note. Default is the head generation; pass gen for an "
              "older one -- every generation is still on disk, because this "
              "store never overwrites. Returns first-seen, last-cited and the "
              "citation pressure between them.",
              {"type": "object",
               "properties": {"seam": {"type": "string"},
                              "gen": {"type": "number"}},
               "required": ["seam"]})
    def _read(args):
        seam = args.get("seam") or ""
        if not seam:
            raise ToolError("seat_read needs a seam")
        gen = args.get("gen")
        return st.read(seam, int(gen) if gen is not None else None)

    @srv.tool("seat_append",
              "Mint a NEW generation of a note. Never edits an existing file: "
              "a second session can only add, which is the fence made "
              "structural. 'source' and 'would_change' are required -- a note "
              "that cannot say where it came from is a guess, and a note "
              "nothing could falsify is an opinion.",
              {"type": "object",
               "properties": {
                   "seam": _SEAM,
                   "text": {"type": "string"},
                   "source": {"type": "string",
                              "description": "you | them | a named source | a guess"},
                   "would_change": {"type": "string",
                                    "description": "the one thing that would make this wrong"},
                   "triggers": {"type": "array", "items": {"type": "string"}},
                   "came_from": {"type": "array", "items": {"type": "string"}},
                   "leads_to": {"type": "array", "items": {"type": "string"}},
                   "unit": {"type": "integer", "minimum": 1,
                            "description":
                                "neutral-buoyancy mark: how many points of "
                                "meaning you had mapped to context when you "
                                "decided how to write this item. 1 for a plain "
                                "term (acts at 2 citations); 4 for a "
                                "double-balanced C4 item (acts at 8). Omit to "
                                "inherit the previous generation's mark. This "
                                "is DECLARED, never inferred from your text."},
                   "allow_jailed": {"type": "boolean"}},
               "required": ["seam", "text", "source", "would_change"]})
    def _append(args):
        # 2026-09-27: the explanation now fits the field that is missing (a
        # missing 'seam' used to be told why 'source' matters).
        why = {
            "seam": "'seam' names the thread this note belongs to, so the next "
                    "reader can find it and see what it replaced.",
            "text": "'text' is the note itself.",
            "source": "This is not paperwork: 'source' is what separates a "
                      "fact from a guess. A store full of unsourced notes is "
                      "confident-sounding text, not memory.",
            "would_change": "This is not paperwork: 'would_change' is what "
                            "separates a note from an opinion -- name what "
                            "would make you revise it.",
        }
        for k in ("seam", "text", "source", "would_change"):
            if not str(args.get(k) or "").strip():
                raise ToolError(f"seat_append needs {k!r}. {why[k]}")
        # A seat at the DEFAULT location was chosen by this server, so a first
        # write may create it. A seat the user named is never created for them
        # -- see _roots(). This is what makes the plugin work out of the box
        # without ever inventing a substitute for somebody's real memory.
        if getattr(st, "seat_is_ours", False) and st.mode() == _store.NOTVISIBLE:
            try:
                st.ensure(create=True, make_parents=True)
            except _store.StoreError as exc:
                raise ToolError(
                    f"could not create the default seat at {st.root}: {exc}"
                ) from exc
        try:
            return st.append(
                args["seam"], args["text"], frm=args["source"],
                would_change=args["would_change"],
                triggers=list(args.get("triggers") or []),
                came_from=list(args.get("came_from") or []),
                leads_to=list(args.get("leads_to") or []),
                unit=_unit_arg(args),
                allow_jailed=bool(args.get("allow_jailed")))
        except _store.Jailed as exc:
            raise ToolError(str(exc)) from exc
        except _store.SemaphoreBusy as exc:
            raise ToolError(
                f"{exc}\nThis is the multi-consumer semaphore doing its job. "
                "Another consumer holds the seam; retry, or raise a semaphore "
                "and say what you are waiting on.") from exc

    @srv.tool("seat_cite",
              "Record that a note was cited, and where. This is the second "
              "column: it sets last-cited and moves the note's pressure. "
              "Citing costs one appended line and never mints a generation, "
              "which is why the two columns are kept in different places.",
              {"type": "object",
               "properties": {"seam": {"type": "string"},
                              "where": {"type": "string"}},
               "required": ["seam", "where"]})
    def _cite(args):
        if not args.get("seam"):
            raise ToolError("seat_cite needs a seam")
        # The citer is THIS SERVER's identity (MENTCACHED_BY), never a value
        # the caller supplies. That is deliberate and it is load-bearing now
        # that buoyancy ranks a seam against the worlds that cite it: a
        # caller-supplied `by` would let anything manufacture a private world
        # of one and float whatever it liked to the top of the compaction
        # queue. Who you are is not an argument.
        #
        # The consequence, said plainly rather than discovered later: a store
        # with ONE server has ONE citer, so lift degenerates to the absolute
        # pressure order. That is the correct no-op, not a broken feature --
        # orthogonality is worth something only where there really are several
        # consumers, which is what MENTCACHED_BY is for.
        if "by" in args and args["by"] != st.by:
            raise ToolError(
                f"seat_cite records who is CITING, and that is this server "
                f"({st.by!r}), not a value you pass. Buoyancy ranks each seam "
                f"against the worlds that cite it, so a caller-chosen citer "
                f"would be a way to float anything to the top of the "
                f"compaction queue. Set MENTCACHED_BY when you launch the "
                f"server if this consumer needs its own identity.")
        return st.cite(args["seam"], st.by, args.get("where") or "unsaid")

    @srv.tool("seat_chain",
              "Walk a note's generations and check the hash chain with TWO "
              "independent verifiers (Python and POSIX shell). Agreement is "
              "evidence; disagreement STOPS and neither side wins. Also "
              "reports where authorship changed hands.", S)
    def _chain(args):
        seam = args.get("seam") or ""
        if not seam:
            raise ToolError("seat_chain needs a seam")
        d = st.notes / dl2.slugify(seam)
        if not d.is_dir():
            return {"seam": seam, "found": False, "rows": []}
        try:
            r = ver.verify(d)
        except verify.ChainSplit as exc:
            raise ToolError(str(exc)) from exc
        return {"seam": seam, "found": True, "verified_by": r.by,
                "chain": "OK" if r.ok else "BROKEN",
                "broken_at": r.broken_at, "detail": r.detail,
                "generations": r.gens, "rows": st.chain(seam)}

    @srv.tool("seat_index",
              "Rebuild the forward index from the note files alone and report "
              "it. The index is a cache: deleting it loses nothing, because "
              "every backward pointer is in the bytes as a hash chain.")
    def _index(_args):
        return st.rebuild_index()

    @srv.tool("seat_buoyancy",
              "The compaction queue, most buoyant first. Buoyancy is citation "
              "pressure measured against the worlds that cite each seam, NOT "
              "against the whole store -- so the most leaned-on note in a "
              "small consumer's world floats even when a busy consumer's "
              "ordinary traffic dwarfs it in absolute terms. High floats "
              "(stays on the loaded page); zero may sink to a continuation "
              "page. Sinking is never deletion; the floor is still the store. "
              "This tool REPORTS and compacts nothing.",
              {"type": "object",
               "properties": {"by": {"type": "string",
                                     "enum": ["lift", "pressure"]}}})
    def _buoy(args):
        by = (args or {}).get("by") or "lift"
        if by not in ("lift", "pressure"):
            raise ToolError("by must be 'lift' (default) or 'pressure'")
        rows = st.buoyancy(by=by)
        return {
            "count": len(rows), "ordered_by": by, "queue": rows,
            "say": (
                "compaction is triggered by the loaded page nearing its cap, "
                "or by buoyancy -- never by tidiness. THIS TOOL COMPACTS "
                "NOTHING. Every row carries the arithmetic that produced it "
                "(pressure, scale, by) so you can disagree with the order."),
            "how_to_read": (
                "pressure  = citations recorded since this seam's head "
                "generation was written. An absolute count.\n"
                "lift_milli = pressure measured against the median of the "
                "worlds that actually cite this seam, in thousandths. 1000 "
                "means 'exactly the median of the most favourable world that "
                "cites it'; 3000 means three times that.\n"
                "scale / by = which citer's world supplied the median, so the "
                "number can be checked by hand.\n"
                "Ordering by lift rather than pressure is what stops a busy "
                "consumer's ordinary traffic from sinking a quiet consumer's "
                "entire world. Pass by='pressure' for the absolute order.\n"
                "A second reader, bin/dl2-lift.awk, computes the same numbers "
                "from the same prose spec (chainspec.py, L1-L5). If it "
                "disagrees with this one, neither answer is evidence."),
        }

    @srv.tool("seat_bless",
              "Endorse a note you did NOT write, naming what you checked. "
              "Rule 5: nothing is canonical because it was written -- it "
              "becomes canonical when a SECOND party blesses the exact bytes. "
              "Refuses the note's own author, and refuses a bless that does "
              "not say what was checked. Blessing does not inherit forward: a "
              "later generation is not blessed because an earlier one was.",
              {"type": "object",
               "properties": {"seam": _SEAM,
                              "checked": {"type": "string",
                                          "description":
                                              "what you actually checked, in "
                                              "words. 'I read it' is not a "
                                              "check."},
                              "gen": {"type": "integer", "minimum": 1}},
               "required": ["seam", "checked"]})
    def _bless(args):
        if not str(args.get("seam") or "").strip():
            raise ToolError("seat_bless needs a seam")
        try:
            return st.bless(args["seam"], st.by, args.get("checked") or "",
                            gen=args.get("gen"))
        except _store.StoreError as exc:
            raise ToolError(str(exc)) from exc

    @srv.tool("seat_blessings",
              "Every bless recorded for a seam. A blessing whose bytes are no "
              "longer on disk is reported STALE rather than dropped -- "
              "somebody having blessed bytes that have since gone is worth "
              "more than a tidy list.", S)
    def _blessings(args):
        if not str(args.get("seam") or "").strip():
            raise ToolError("seat_blessings needs a seam")
        rows = st.blessings(args["seam"])
        return {"mode": st.mode(), "seam": args["seam"], "count": len(rows),
                "blessings": rows,
                "say": ("unblessed -- which is not suspect, most notes never "
                        "are; it means nobody has checked these bytes"
                        if not rows else
                        f"{len(rows)} blessing(s); "
                        f"{sum(1 for r in rows if r['state'] == 'STALE')} stale")}

    @srv.tool("seat_date",
              "The SHIPBOARD DATE: the date this context is at, held in a "
              "file, moving forward like a version's high-water mark. Every "
              "stamp this store writes comes from it, not from the host "
              "clock. Call with no argument to read it; pass `to` to advance "
              "it. It never moves backward, and reading never moves it.",
              {"type": "object",
               "properties": {"to": {"type": "string",
                                     "description": "YYYYMMDDTHHMMSSZ"},
                              "why": {"type": "string"}}})
    def _date(args):
        args = args or {}
        if not args.get("to"):
            s, source = _shipdate.read(st.active)
            return {"mode": st.mode(), "date": s or "(unset)", "source": source,
                    "file": str(_shipdate.path_for(st.active)),
                    "say": ("this context has not declared a date; the first "
                            "write will populate it from the host clock and "
                            "leave a receipt saying so"
                            if source == "UNSET" else
                            f"this context is at {s}, declared in a file")}
        try:
            return {"mode": st.mode(),
                    **_shipdate.advance(st.active, args["to"], by=st.by,
                                        why=args.get("why") or "")}
        except _shipdate.ShipdateError as exc:
            raise ToolError(str(exc)) from exc

    @srv.tool("link_check",
              "Check every link in a block of text for host-invariance. A bare "
              "absolute path FAULTs: it is right on one machine and "
              "unresolvable elsewhere, and the bytes do not say which machine. "
              "Schemes seat: c4: ws: resolve per host; host:path is legal when "
              "the host is named on purpose.",
              {"type": "object", "properties": {"text": {"type": "string"}},
               "required": ["text"]})
    def _links(args):
        rows = []
        for kind, target in dl2.links_in(args.get("text") or ""):
            v, why = dl2.check_link(kind, target)
            rows.append({"kind": kind, "target": target, "verdict": v, "why": why})
        faults = [r for r in rows if r["verdict"] == "FAULT"]
        return {"links": rows, "faults": len(faults),
                "verdict": "FAULT" if faults else "OK"}

    SEM = {"type": "object",
           "properties": {"name": {"type": "string"}, "why": {"type": "string"},
                          "ceremony": {"type": "string"}},
           "required": ["name"]}

    @srv.tool("semaphore_raise",
              "Raise a named signal. Cheap, and anyone may do it.", SEM)
    def _raise(args):
        if not args.get("why"):
            raise ToolError("raising is cheap but never silent: say why")
        return st.semaphore(args["name"]).raise_(args["why"], st.by)

    @srv.tool("semaphore_lower",
              "Lower a named signal. Requires the ceremony word that "
              "discharges it, so a passing session cannot clear a signal by "
              "accident.", SEM)
    def _lower(args):
        try:
            return st.semaphore(args["name"]).lower(args.get("ceremony") or "", st.by)
        except _store.StoreError as exc:
            raise ToolError(str(exc)) from exc

    @srv.tool("semaphore_state", "The state and full log of a named signal.", SEM)
    def _state(args):
        return st.semaphore(args["name"]).state()

    _metrics.register(srv)   # read-only view of the skill-metrics store (2026-09-22)
    _spans.register(srv, by=st.by)   # time + tokens per span, on-start/on-stop (2026-09-23)
    _freshness.register(srv)         # installed plugin vs the shelf mint (2026-09-23)
    _prefs.register(srv, by=st.by)   # the switches, by default on (2026-09-23)
    _softskills.register(srv)        # the dynaloader: SOFT-SKILLS folders served live (2026-09-23)
    _words.register(srv, by=st.by)   # the word-path registry, a second reader of C4's g/<word>/ (2026-09-24)
    from . import epmo as _epmo
    _epmo.register(srv, by=st.by)    # EPMO: the capability lens, tokenization over r/epmo (2026-10-19)
    from . import keys as _keys
    _keys.register(srv)              # the keys you keep, the names they answer to, key_run (2026-10-12)
    from . import mode as _mode
    _mode.register(srv, by=st.by)    # LAB or WORKSHOP: the settings page's default, a bounded switch from chat (2026-10-23)
    from . import orglimits as _org
    _org.register(srv)               # a group's ORG.md: what it limits here, read only (2026-10-23)
    return srv


def main(argv=None) -> int:
    srv = build()
    srv.serve()
    return 0
