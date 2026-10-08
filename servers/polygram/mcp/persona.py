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

"""persona-mcp -- row 0 of the resolution order, finally occupied.

``bin/mt1pl`` -- the persona link resolver, written 2026-09-13 -- documents six
sources in priority order and puts a hole at the top:

    | 0 | *(a thick client would put MCP here)* | a persona served globally,
        per-account. Named, not faked -- we are a literate wrapper. |

This server is that row.  It does not replace ``mt1pl``; it becomes the source
``mt1pl`` was already reserving space for, and it keeps ``mt1pl``'s four
refusals verbatim because they are the reason the row was left empty rather
than guessed at.

Persona sheets are stored through the same ``Store`` as memory, so the archive
rule reaches them without a second implementation: **a sheet is never edited,
only regenerated**, and its generations are a hash chain like any other note.
That is Corwin's requirement -- *"we must archive, not simplify overwrite or
delete, memory and person(a) (and schema and whatever sets ... end up in the
MEMORY semaphoring MCP server)"* -- satisfied by reuse rather than by a parallel
set of rules that could drift.

A persona mutation is therefore a generation, and the in-character journal
entry is its body.  You cannot record a mutation without writing the journal
entry, because the generation IS the journal entry.  The discipline that R4 of
the 2026-09-13 rules had to ask for in prose is here a property of the layout.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import store as _store
from . import dl2, verify
from . import mentcached as _mentcached
from . import prefs as _prefs
from .rpc import Server, ToolError

VERSION = "0.1.0"

#: Who is citing, when nobody said. Mirrors mentcached.DEFAULT_BY -- this
#: server used to default to f"persona-mcp/{os.getpid()}", the exact bug
#: mentcached fixed for the same reason: a citer identity that changes on
#: every restart is a timestamp wearing one, and persona_list's buoyancy()
#: reads citer identity the same way seat_append's does.
DEFAULT_BY = "claude"

# The refusals.  bin/mt1pl states three in its own words (never creates a sheet,
# never edits one, never chooses a persona when no layer declared one); they are
# 1 and 3 here.  2, 4 and 5 come from the persona-link design
# (c4/h/PERSONA-LINK-2026-09-13.md).  Where the two overlap and differ, mt1pl
# wins -- it is the older and the signed one.  The persona-engine skill carries
# all five (skills/persona-engine).
REFUSALS = [
    "Never mints a persona. A declaration pointing at a file that does not "
    "exist is a FAULT, never a cue to write that file.",
    "Never writes the persona's voice. It may draft a skeleton; the journal "
    "entry is the persona's own.",
    "Never edits a sheet another session wrote, except by appending to that "
    "sheet's own log -- the fence, unchanged.",
    "Never takes the rights. The byline says *for* somebody, always.",
    "A persona's voice may not be the place a defect is explained. If the "
    "sentence that makes a flaw acceptable is in the persona's register, the "
    "flaw is unfixed and the voice is doing work it must not do. Fix the thing "
    "first. Then the persona may say whatever it likes about it.",
]

# mt1pl's resolution order.  Row 0 is this server; rows 1-6 are mt1pl's and are
# reported, not re-implemented -- this server says what it can see and names
# mt1pl as the authority for the rest.
ORDER = [
    (0, "persona-mcp", "a persona served over MCP, per-account"),
    (1, "$MENTAT_PERSONA", "an explicit path, this session only"),
    (2, "Persona: in the project's CLAUDE.md", "the shop door speaks for the shop"),
    (3, "PERSONA.md at the project root", "the exact-name file"),
    (4, ".persona at the project root", "one line: a path"),
    (5, "persona: in the store's MEMORY.md", "store-level default"),
    (6, "nothing", "Mentat is the voice. Documented default, not a gap."),
]


def _root() -> tuple[Path, Path | None, bool]:
    """Resolve the persona root, and say whether WE chose it or Corwin did.

    Mirrors mentcached._roots() -- same class of bug, same fix.  The previous
    default here was ``Path.cwd() / "memory" / "persona"``: cwd is decided by
    whatever spawns this MCP process, not by Corwin, and on the desktop that
    is not AS4CE0001 -- so persona_list answered NOTVISIBLE from the very
    install where mentcached's seat_mode answered SEATED from the same
    MENTCACHED_SEAT-less environment.

    This module's own docstring promises persona sheets are "stored through
    the same Store as memory" -- so the un-set default is mentcached's own
    DEFAULT_SEAT with "persona" appended, IMPORTED rather than copied so the
    two constants cannot drift apart (a parallel set of rules is exactly what
    that docstring says this design avoids).
    """
    root = (os.environ.get("PERSONA_ROOT") or "").strip()
    jail = (os.environ.get("PERSONA_JAIL") or "").strip()
    ours = False
    if not root or "${" in root or root.startswith("$"):
        seat = (os.environ.get("MENTCACHED_SEAT") or "").strip()
        if not seat or "${" in seat or seat.startswith("$"):
            seat, ours = str(_mentcached.DEFAULT_SEAT), True
        root = str(Path(seat).expanduser() / "persona")
    if jail and ("${" in jail or jail.startswith("$")):
        jail = ""
    return (Path(root).expanduser(),
            (Path(jail).expanduser() if jail else None), ours)


# --- the shelf: sheets already written, served where they lie -------------------
#
# Corwin, 2026-09-24: "no idea why I would want anything other than to have the
# work we already did show up."  The generation store above starts empty on every
# new install, so persona_list answered NOTVISIBLE with the three sheets sitting in
# h/persona the whole time.  The shelf serves those files READ-ONLY, the way
# softskills serves SOFT-SKILLS: nothing copied, nothing installed, nothing
# rewritten -- a sheet is a file a persona wrote, and refusal 3 fences it.
# A name present in both places is read from the store (it is chained and newer by
# construction) and the shelf copy is reported as shadowed, never hidden.

MAX_SHEET_BYTES = 512 * 1024
HEAD_LINES = 15

#: A sheet says what it is in its own first lines; the file name is only an address.
#: One rule for every kind (Corwin, 2026-09-24: "make sure that everyone can be found
#: by the same systemic means"):
#:   * an ``actor:`` line, or a heading that names a sheet (CHARACTER / ITEM SHEET,
#:     PERSONA) -- the gw7/cs1gk shape: instrument, place, host, fiction;
#:   * or YAML front matter with ``name:`` whose status/description calls it a persona
#:     or a model -- the modelthisbook shape: CORWIN, BRYANT, a seed, MERLIN.
#: A file whose name carries SECRET is never read past its name.
_HEADING = re.compile(r"^#\s+(CHARACTER SHEET|ITEM SHEET|PERSONA)\b", re.I)
_MODEL_WORD = re.compile(r"\b(persona|model)\b", re.I)


def _guess_roots() -> list[tuple[Path, str]]:
    """Where this shop keeps sheets, derived from the two roots it already names
    (softskills.roots -> the seat; words.root -> the C4 tree).  Said aloud as a guess."""
    out: list[tuple[Path, str]] = []
    seats: list[Path] = []
    try:
        from . import softskills as _ss
        seats = [r.parent for r, _how, _ok in _ss.roots()]
    except Exception:                      # noqa: BLE001
        pass
    for seat in seats:
        out += [(seat / "h" / "persona", "GUESSED <seat>/h/persona"),
                (seat / "book", "GUESSED <seat>/book")]
    c4 = ""
    try:
        c4 = _prefs.get("words.root").strip()
    except Exception:                      # noqa: BLE001
        pass
    if c4:
        c = Path(c4).expanduser()
        out += [(c / "h" / "persona", "GUESSED <c4>/h/persona"),
                (c / "h" / "cast", "GUESSED <c4>/h/cast"),
                (c / "q" / "words", "GUESSED <c4>/q/words"),
                (c.parent / "pub" / "method" / "h", "GUESSED <c4>/../pub/method/h"),
                (c.parent / "modelthisbook", "GUESSED <c4>/../modelthisbook")]
    return out


def shelf_roots() -> list[tuple[Path, str, bool]]:
    """[(path, how, exists)] in lookup order: pref persona.sheets, else
    $PERSONA_SHEETS, else the guesses above.  Earlier roots win a name."""
    out: list[tuple[Path, str]] = []
    try:
        pref = _prefs.get("persona.sheets").strip()
    except Exception:                      # noqa: BLE001 -- unreadable prefs must not hide sheets
        pref = ""
    env = (os.environ.get("PERSONA_SHEETS") or "").strip()
    if pref:
        out = [(Path(x.strip()).expanduser(), "pref persona.sheets")
               for x in pref.split(os.pathsep) if x.strip()]
    elif env and "${" not in env and not env.startswith("$"):
        out = [(Path(x.strip()).expanduser(), "$PERSONA_SHEETS")
               for x in env.split(os.pathsep) if x.strip()]
    else:
        out = _guess_roots()
    seen, uniq = set(), []
    for p, how in out:
        k = str(p)
        if k not in seen:
            seen.add(k); uniq.append((p, how))
    return [(p, how, p.is_dir()) for p, how in uniq]


def _stem_name(path: Path) -> str:
    """CHARACTER-2026-09-06-mentat.md -> mentat; PERSONA-gw7.md -> gw7; ILUNGA.md -> ilunga."""
    stem = path.stem
    for pre in ("CHARACTER-", "PERSONA-"):
        if stem.startswith(pre):
            stem = stem[len(pre):]
            break
    parts = stem.split("-")
    if len(parts) > 3 and all(x.isdigit() for x in parts[:3]):
        stem = "-".join(parts[3:])
    return dl2.slugify(stem)


def classify(path: Path) -> dict | None:
    """{name, kind, actor, title} when the file says it is a sheet, else None."""
    if "SECRET" in path.name.upper() or path.suffix.lower() != ".md":
        return None
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            head = [fh.readline() for _ in range(HEAD_LINES)]
    except OSError:
        return None
    title = actor = fm_name = bare_name = ""
    fm_says_model = False
    in_fm = bool(head) and head[0].strip() == "---"
    for i, raw in enumerate(head):
        t = raw.strip()
        if in_fm and i > 0 and t == "---":
            in_fm = False
            continue
        low = t.lower()
        if not title and _HEADING.match(t):
            title = t.lstrip("#").strip()
        elif not actor and low.startswith("actor:"):
            actor = t.split(":", 1)[1].strip().split(" ", 1)[0]
        elif in_fm and low.startswith("name:") and not fm_name:
            fm_name = t.split(":", 1)[1].strip()
        elif not in_fm and low.startswith("name:") and not bare_name:
            # A sheet may say its own name (2026-09-25: gw7 the node, gh7 the host persona --
            # the file keeps its address, the sheet says who it is). First word only.
            bare_name = (t.split(":", 1)[1].strip().split() or [""])[0]
        elif in_fm and (low.startswith("status:") or low.startswith("description:")):
            # "Model This Book" is the project's name, not a claim to be a model
            if _MODEL_WORD.search(re.sub(r"model\s+this\s+book", "", t, flags=re.I)):
                fm_says_model = True
            if not actor and "synthetic" in low:
                actor = "synthetic"
    if actor or title:
        name = dl2.slugify(bare_name) if bare_name else _stem_name(path)
        if not title:   # no sheet heading in the head: the file's first H1 names it
            title = next((h[2:].strip() for h in head if h.startswith("# ")), "")
        return {"name": name, "kind": "sheet", "actor": actor, "title": title}
    if fm_name and fm_says_model:
        return {"name": dl2.slugify(fm_name), "kind": "model", "actor": actor or "person-model",
                "title": fm_name}
    return None


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shelf_sheets() -> tuple[dict[str, dict], list[dict], list[dict]]:
    """(name -> row, other copies of served names, roots report).  First root wins a
    name; every other copy is reported with whether its bytes AGREE or DIFFER, so
    drift between trees is said out loud rather than resolved by this server."""
    seen: dict[str, dict] = {}
    others: list[dict] = []
    report = []
    for root, how, ok in shelf_roots():
        n = 0
        if ok:
            for f in sorted(root.iterdir()):
                if not f.is_file():
                    continue
                c = classify(f)
                if not c:
                    continue
                n += 1
                st = f.stat()
                row = {**c, "source": "shelf", "file": str(f), "bytes": st.st_size,
                       "mtime": int(st.st_mtime), "sha256": _sha(f)}
                if c["name"] in seen:
                    first = seen[c["name"]]
                    others.append({**row, "copy_of": first["file"],
                                   "bytes_agree": row["sha256"] == first["sha256"]})
                else:
                    seen[c["name"]] = row
        report.append({"root": str(root), "how": how, "exists": ok, "sheets": n})
    return seen, others, report


def build(by: str | None = None, root: Path | None = None,
          jail: Path | None = None) -> Server:
    droot, djail, ours = _root()
    st = _store.Store(root=root or droot,
                      by=by or (os.environ.get("PERSONA_BY") or "").strip()
                      or DEFAULT_BY,
                      jail_root=jail if jail is not None else djail)
    st.seat_is_ours = ours if root is None else False
    ver = verify.Verifier()
    def _mode() -> str:
        # The store's own word, except for one case: a root this server CHOSE (the default under the
        # mentcached seat), not created yet because nothing has been written, under a seat that exists
        # and is writable. That root is reachable -- the first persona_mutate creates it -- so SEATED
        # is the true word, and NOTVISIBLE beside sixteen served sheets read as a fault (2026-09-25).
        # A root Corwin NAMED that is absent still says NOTVISIBLE: a path he named is never created.
        m = st.mode()
        par = Path(st.root).parent
        if (m == _store.NOTVISIBLE and getattr(st, "seat_is_ours", False)
                and not Path(st.root).exists() and par.is_dir() and os.access(par, os.W_OK)):
            return _store.SEATED
        return m

    srv = Server(name="persona", version=VERSION, mode_fn=_mode)

    N = {"type": "object", "properties": {"name": {"type": "string"}},
         "required": ["name"]}

    @srv.tool("persona_resolve",
              "Which persona is at the desk, and which layer said so. Row 0 is "
              "this server; rows 1-6 belong to bin/mt1pl and are named, not "
              "re-implemented -- two resolvers disagreeing about who is "
              "speaking is the worst seam in the house. First hit wins and the "
              "winner is always said aloud.",
              {"type": "object", "properties": {"name": {"type": "string"}}})
    def _resolve(args):
        want = (args.get("name") or "").strip()
        served = st.seams()
        if want:
            slug = dl2.slugify(want)
            if slug in served:
                return {"resolved": slug, "row": 0, "source": "persona-mcp",
                        "order": [list(r) for r in ORDER],
                        "say": f"row 0: {slug} is served by this server"}
            shelf, _sh, _roots = shelf_sheets()
            if slug in shelf:
                return {"resolved": slug, "row": 0, "source": "persona-mcp (shelf)",
                        "file": shelf[slug]["file"],
                        "order": [list(r) for r in ORDER],
                        "say": f"row 0: {slug} is served by this server from the shelf, "
                               f"read-only: {shelf[slug]['file']}"}
            return {"resolved": "", "row": None, "source": "",
                    "order": [list(r) for r in ORDER],
                    "say": (f"NOT SERVED HERE: no sheet named {slug!r}. This is "
                            "a FAULT, not a cue to mint one -- refusal 1. Fall "
                            "through to bin/mt1pl for rows 1-6.")}
        shelf, _sh, _roots = shelf_sheets()
        served = sorted(set(served) | set(shelf))
        return {"resolved": "", "row": None, "served": served,
                "order": [list(r) for r in ORDER],
                "say": "name a persona, or read rows 1-6 with bin/mt1pl"}

    @srv.tool("persona_read",
              "Read a persona sheet at its current generation. Older "
              "generations are all still on disk; pass gen for one.",
              {"type": "object",
               "properties": {"name": {"type": "string"}, "gen": {"type": "number"}},
               "required": ["name"]})
    def _read(args):
        name = args.get("name") or ""
        if not name:
            raise ToolError("persona_read needs a name")
        gen = args.get("gen")
        out = ({"found": False} if st.mode() == _store.NOTVISIBLE
               else st.read(name, int(gen) if gen is not None else None))
        # A sheet on the shelf and its mutation journal in the store are two things, not rivals
        # (2026-09-25): with no `gen`, a shelf sheet is what the name means, and any chained
        # generations ride beside it as `journal`. Asking for a `gen` reads the journal itself.
        if gen is None:
            shelf, _sh, _roots = shelf_sheets()
            row = shelf.get(dl2.slugify(name))
            if row:
                p = Path(row["file"])
                if row["bytes"] > MAX_SHEET_BYTES:
                    raise ToolError(f"{p} is {row['bytes']} bytes, over the "
                                    f"{MAX_SHEET_BYTES}-byte read cap")
                sheet = {**row, "found": True, "gen": None,
                         "note": p.read_text(encoding="utf-8", errors="replace"),
                         "say": f"{row['name']}: read from the shelf, read-only "
                                f"({p}); not a chained generation -- its gauge is bin/cs1gk"}
                if out.get("found"):
                    sheet["journal"] = {"generations": out.get("generations"),
                                        "head_gen": out.get("gen"), "head": out.get("note"),
                                        "file": out.get("file")}
                    sheet["say"] += (f"; its mutation journal has {out.get('generations')} "
                                     "generation(s) -- pass gen to read one")
                return sheet
        if not out.get("found"):
            out["say"] = (f"no sheet named {name!r}. Refusal 1: this server "
                          "never mints a persona. Absence is a FAULT to report, "
                          "not a gap to fill.")
        return out

    @srv.tool("persona_mutate",
              "Record a generation of a sheet. The in-character journal entry "
              "IS the generation body -- there is no way to record a mutation "
              "without writing the entry, and no way to write the entry "
              "without it being dated and chained. 'evidence' names the bytes "
              "a stranger can diff; 'would_change' is the falsifier.",
              {"type": "object",
               "properties": {
                   "name": {"type": "string"},
                   "entry": {"type": "string",
                             "description": "the journal entry, in the persona's own voice"},
                   "evidence": {"type": "string",
                                "description": "bytes a stranger can diff -- a file, a commit, a named draft sentence"},
                   "would_change": {"type": "string"},
                   "allow_jailed": {"type": "boolean"}},
               "required": ["name", "entry", "evidence", "would_change"]})
    def _mutate(args):
        for k in ("name", "entry", "evidence", "would_change"):
            if not str(args.get(k) or "").strip():
                raise ToolError(
                    f"persona_mutate needs {k!r}. A generation with a story and "
                    "no evidence is a persona being charming about a defect, "
                    "which is refusal 5. A generation with evidence and no "
                    "story is a diff, not a mutation.")
        # A persona root at the DEFAULT location was chosen by this server,
        # so a first write may create it -- the same rule as
        # mentcached.seat_append: we may create a path we chose, never a path
        # Corwin named (see _root()).
        if getattr(st, "seat_is_ours", False) and st.mode() == _store.NOTVISIBLE:
            try:
                st.ensure(create=True, make_parents=True)
            except _store.StoreError as exc:
                raise ToolError(
                    f"could not create the default persona root at {st.root}: "
                    f"{exc}") from exc
        try:
            return st.append(args["name"], args["entry"],
                             frm=args["evidence"],
                             would_change=args["would_change"],
                             triggers=["persona", dl2.slugify(args["name"])],
                             allow_jailed=bool(args.get("allow_jailed")))
        except _store.Jailed as exc:
            raise ToolError(str(exc)) from exc

    @srv.tool("persona_byline",
              "The byline and the rights line for anything this persona "
              "authors. Copyright vests in the principal; the persona is the "
              "writer and never the rights-holder. Printed on every "
              "resolution because it is the part that must not erode.",
              {"type": "object",
               "properties": {"name": {"type": "string"},
                              "principal": {"type": "string"},
                              "owns": {"type": "string",
                                       "description": "e.g. 'rules' -- produces the split line"}},
               "required": ["name", "principal"]})
    def _byline(args):
        name, principal = args["name"], args["principal"]
        owns = (args.get("owns") or "").strip()
        out = {
            "byline": f"Author: {name} (for {principal})",
            "rights": f"Copyright (C) 2026 {principal}",
            "say": "the persona is the writer and never the rights-holder",
        }
        if owns:
            out["split"] = f"{principal} ({owns}), transcribed & formalized by {name}"
        return out

    @srv.tool("persona_chain",
              "Walk a sheet's generations with two independent verifiers. A "
              "sheet whose chain is broken is a sheet somebody edited, which "
              "this store makes structurally impossible -- so a BROKEN result "
              "means the files were touched outside the tooling.", N)
    def _chain(args):
        name = args.get("name") or ""
        d = st.notes / dl2.slugify(name)
        if not d.is_dir():
            shelf, _sh, _roots = shelf_sheets()
            row = shelf.get(dl2.slugify(name))
            if row:
                return {"name": name, "found": True, "chain": "NONE", "rows": [],
                        "source": "shelf", "file": row["file"],
                        "say": "a shelf sheet is a plain file, not a chain; check it with "
                               "bin/cs1gk (sh tests/cs1gk-tests.sh has --prove-red)"}
            return {"name": name, "found": False, "rows": []}
        try:
            r = ver.verify(d)
        except verify.ChainSplit as exc:
            raise ToolError(str(exc)) from exc
        return {"name": name, "found": True, "verified_by": r.by,
                "chain": "OK" if r.ok else "BROKEN", "detail": r.detail,
                "generations": r.gens, "rows": st.chain(name)}

    @srv.tool("persona_refusals",
              "The five refusals, served so a caller can read them before "
              "asking for something this server will not do.")
    def _refusals(_args):
        return {"count": len(REFUSALS), "refusals": REFUSALS,
                "authority": "bin/mt1pl; if these diverge from its copy, mt1pl wins"}

    @srv.tool("persona_list", "Sheets this server serves, with pressure.")
    def _list(_args):
        rows = st.buoyancy() if st.mode() != _store.NOTVISIBLE else []
        chained = {r.get("seam") or dl2.slugify(r.get("name", "")) for r in rows}
        for r in rows:
            r.setdefault("source", "store")
        shelf, copies, roots = shelf_sheets()
        shadowed = []   # kept in the answer's shape; a sheet is never shadowed by its own journal now
        by = {r.get("seam") or dl2.slugify(r.get("name", "")): r for r in rows}
        for name, row in shelf.items():
            if name in chained:
                j = by[name]
                rows.remove(j)
                rows.append({**row, "source": "shelf+journal",
                             "journal": {k: j.get(k) for k in ("gens", "pressure", "last_cited", "head_stamp")}})
            else:
                rows.append(row)
        drift = sorted({c["name"] for c in copies if not c["bytes_agree"]})
        # 2026-09-25: a sheet renamed by its own name: line left a stale twin (same file name,
        # old text) serving under the OLD name -- a new persona, silently. Same file name, two
        # served names, is said out loud as a split.
        by_file: dict[str, set] = {}
        for r in list(shelf.values()) + copies:
            by_file.setdefault(Path(r["file"]).name, set()).add(r["name"])
        split = sorted(f"{f}: {' / '.join(sorted(n))}" for f, n in by_file.items() if len(n) > 1)
        store_say = ("the generation store is empty -- it is created on the first persona_mutate"
                     if st.mode() == _store.NOTVISIBLE else f"store {st.mode()}")
        n_shelf = sum(1 for r in rows if str(r.get("source", "")).startswith("shelf"))
        return {"count": len(rows), "personas": rows, "shelf_roots": roots,
                "shadowed": shadowed, "copies": copies, "drift": drift, "split": split,
                "store_root": str(st.root),
                "say": f"{len(rows)} persona(s): {len(rows) - n_shelf} chained, "
                       f"{n_shelf} from the shelf (read-only); {len(copies)} other "
                       f"cop{'y' if len(copies) == 1 else 'ies'} elsewhere"
                       + (f", DIFFERING for: {', '.join(drift)}" if drift else ", all agreeing")
                       + (f"; SPLIT (one file name, two served names -- a stale copy of a renamed "
                          f"sheet?): {'; '.join(split)}" if split else "")
                       + f"; {store_say}"}

    return srv


def main(argv=None) -> int:
    build().serve()
    return 0
