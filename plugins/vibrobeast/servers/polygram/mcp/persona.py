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

# The refusals.  bin/mt1pl states all five (`sh bin/mt1pl --refusals`, since 2026-10-16; tests/test_mcp_persona.py
# RefusalsParity holds the two copies word for word).  Before that it stated three (never creates a sheet,
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


# --- the plain voice when no sheet resolves (lane B, 2026-10-10; card 11, R19) --------------
#
# A newcomer should not have to learn a character before getting an answer (card 11, from Model W
# A2c). When no persona resolves, persona_resolve says so (refusal 1 stands: nothing is minted) AND
# hands back default_voice: the plain voice this shop calls iT, at the origin of the tone dial.
# tone.dial and tone.show are lane A's preference keys; until prefs.KNOWN carries them, a missing
# key is its default (DESIGN-extension-edition.md section 2).

TONE_ORIGIN = "0/0, 0/0"     # signals seen / signals total, on two axes: answer length, narration


def _tone_pref(key: str, default: str) -> str:
    try:
        v = (_prefs.get(key) or "").strip()
    except Exception:                      # noqa: BLE001 -- an unknown key is its default
        v = ""
    return v or default


def default_voice() -> dict:
    """{voice, line, tone_show[, tone_dial]}: one plain line, and numbers only when asked for."""
    dial = _tone_pref("tone.dial", TONE_ORIGIN)
    show = _tone_pref("tone.show", "words").lower()
    at = ("at the starting tone, because nothing has been counted yet to move it"
          if " ".join(dial.split()) == TONE_ORIGIN else
          "at the tone the signals counted so far have set")
    line = ("No persona is at the desk, so Claude answers in its plain voice "
            "(this shop calls it iT), " + at + ".")
    out = {"voice": "plain", "line": line, "tone_show": show}
    if show != "words":
        out["tone_dial"] = dial
    return out


# --- the persona ledger (lane B, 2026-10-10; card 19, agreements 29-32, R20) -----------------
#
# Corwin, 2026-10-10: "Persona inverse should be carried by other Persona, like a boundary
# network ... forming this net in terms of falsifying knowledge held among participants (and
# not some additional stores they may keep)."  So the ledger is READ from the sheets and never
# kept: each sheet may hold a section "## Whose inverse I carry" whose lines read
# "NAME : what I know that would show NAME broke its line"; the ledger only reads and reverses
# them.  Writing those lines is persona-writing -- his pen -- so this code never writes a sheet.
# Edges a review proposed (not yet in any sheet) ride in their own section, each quoting its
# source line.  Only head lines, version lines and the inverse section are ever printed (L5);
# person models are counted, never named (L6).  SPEC: tests/persona-ledger-SPEC.txt.

_INVERSE_HEAD = re.compile(r"^#{1,6}\s+Whose inverse I carry\b", re.I)
_ANY_HEAD = re.compile(r"^#{1,6}\s")
_EDGE_LINE = re.compile(r"^\s*(?:[-*]\s+)?([A-Za-z0-9][A-Za-z0-9 ,()-]*?)\s+:\s+(\S.*?)\s*$")
_ARROW = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9 ,()-]*?)\s*->\s*([A-Za-z0-9][A-Za-z0-9 ,()-]*?)\s*:\s*(.*?)\s*$")
_CITE = re.compile(r"\bsource:\s*(\S+?):(\d+)(?:-(\d+))?\b")
_NOT_PERSON = re.compile(r"\bnot\s+a\s+(?:real\s+)?person\b", re.I)
_VERSION_FOOT = re.compile(r"^\*(Version [^*]+)\*\s*$")
QUOTE_CAP = 300

_SMALL = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
          "fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _num(n: int) -> str:
    """'fifteen (15)': a count in words and numerals, as the read-back promises (L1)."""
    if n < 20:
        w = _SMALL[n]
    elif n < 100:
        w = _TENS[n // 10] + ("" if n % 10 == 0 else "-" + _SMALL[n % 10])
    else:
        w = str(n)
    return f"{w} ({n})"


def _guard(path) -> Path:
    """The one rule every read in this server keeps: a file whose name says SECRET is never opened, whatever
    pointed at it (a shelf row, a `proposed` path, a `source:` pointer).  Found 2026-10-19 (the audit, HOLD
    item 10): classify() kept the rule and six other reads did not.  Raises OSError, which every caller
    already treats as 'not readable'."""
    p = Path(path)
    if "SECRET" in p.name.upper():
        raise OSError(f"refused: {p.name} says SECRET in its name, and this server never opens such a file")
    return p


def _head(path: Path) -> list[str]:
    try:
        with _guard(path).open(encoding="utf-8", errors="replace") as fh:
            return [fh.readline() for _ in range(HEAD_LINES)]
    except OSError:
        return []


def _is_person_model(row: dict) -> bool:
    """L6: a 'model' sheet is a person model unless its own head says it is not a person."""
    if row.get("kind") != "model":
        return False
    return not any(_NOT_PERSON.search(h) for h in _head(Path(row["file"])))


def _version(path: Path) -> str:
    """The sheet's last '*Version ...*' footer line, else its front-matter version (first two
    parts), else a plain 'no version line'.  Version lines only (L5)."""
    last = ""
    try:
        for raw in _guard(path).read_text(encoding="utf-8", errors="replace").splitlines():
            m = _VERSION_FOOT.match(raw.strip())
            if m:
                last = m.group(1).strip()
    except OSError:
        return "not readable"
    if last:
        return last
    for h in _head(path):
        t = h.strip()
        if t.lower().startswith("version:"):
            parts = [p.strip() for p in t.split(":", 1)[1].split("·")]
            return " · ".join(p.strip("* ") for p in parts[:2] if p)
    return "no version line"


def _names(cell: str) -> list[str]:
    """'ilunga, pell (fiction)' -> ['ilunga', 'pell']; parentheses are remarks, not names."""
    cell = re.sub(r"\([^)]*\)", "", cell)
    return [dl2.slugify(x.strip()) for x in cell.split(",") if x.strip()]


def _inverse_lines(path: Path) -> tuple[list[tuple[int, str, str]], bool]:
    """([(line number, target cell, words)], section present?) from the sheet's own section."""
    out, inside, present = [], False, False
    try:
        lines = _guard(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out, False
    for i, raw in enumerate(lines, 1):
        if _INVERSE_HEAD.match(raw):
            inside = present = True
            continue
        if inside and _ANY_HEAD.match(raw):
            inside = False
        if inside:
            m = _EDGE_LINE.match(raw)
            if m:
                out.append((i, m.group(1), m.group(2)))
    return out, present


def _proposed_edges(src: Path) -> list[dict]:
    """Arrow lines 'A -> B : words' in a review or study file (fenced or not).  A line whose
    words are only 'source: FILE:N[-M]' takes its words from those lines of FILE (relative to
    src), so a pointer file states nothing of its own."""
    out = []
    src = Path(os.path.abspath(src))
    try:
        lines = _guard(src).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return [{"fault": f"proposed source not readable: {exc}", "src": src, "line": 0}]
    i = 0
    while i < len(lines):
        m = _ARROW.match(lines[i])
        if not m:
            i += 1
            continue
        words, j = m.group(3), i + 1
        # continuation: indented lines that are not themselves arrows, up to a blank or fence
        while (j < len(lines) and lines[j].startswith((" ", "\t")) and lines[j].strip()
               and not _ARROW.match(lines[j]) and not lines[j].strip().startswith("```")):
            words += " " + lines[j].strip()
            j += 1
        row = {"carriers": _names(m.group(1)), "targets": _names(m.group(2)),
               "src": src, "line": i + 1, "words": " ".join(words.split())}
        c = _CITE.search(row["words"])
        if c and row["words"].replace(c.group(0), "").strip(" ;,.()") == "":
            f = Path(os.path.normpath(src.parent / c.group(1)))
            a = int(c.group(2)); b = int(c.group(3) or a)
            try:
                got = _guard(f).read_text(encoding="utf-8", errors="replace").splitlines()[a - 1:b]
            except OSError:
                got = []
            text = " ".join(" ".join(got).split())
            low = text.lower()
            ok = bool(got) and all(any(part in low for part in n.split("-")[:1])
                                   for n in row["carriers"] + row["targets"])
            if not ok:
                row["fault"] = (f"cites {c.group(1)}:{c.group(0).split(':')[-1]} but those "
                                "lines do not name both ends")
            row.update({"words": text, "cited": f, "cited_lines": f"{a}-{b}" if b != a else str(a)})
        out.append(row)
        i = j
    return out


def _cell(s: str) -> str:
    return " ".join(str(s).split()).replace("|", "\\|")


def _quote(s: str) -> str:
    s = _cell(s)
    return (s[:QUOTE_CAP - 1] + "…") if len(s) > QUOTE_CAP else s


def ledger(proposed: list | None = None, today: str | None = None) -> dict:
    """Regenerate LEDGER.md from the sheets on the shelf (read-only).  Returns
    {markdown, sheets, edges, faults, proposed, diverged, person_models, say}."""
    import datetime as _dt
    import hashlib
    today = today or _dt.date.today().isoformat()
    shelf, copies, roots = shelf_sheets()
    persons = {n for n, r in shelf.items() if _is_person_model(r)}
    sheets = {n: r for n, r in shelf.items() if n not in persons}
    root_dirs = [Path(r["root"]) for r in roots if r["exists"]]
    base = Path(os.path.commonpath([str(p) for p in root_dirs])) if root_dirs else Path("/")
    def show(p) -> str:
        p = Path(p)
        try:
            return str(p.relative_to(base)) if base != Path("/") else str(p)
        except ValueError:
            return str(p)
    # twins: copies in other roots, and a same-name file left in the folder beside a root (L4)
    twins: dict[str, list[dict]] = {}
    for c in copies:
        if c["name"] in sheets:
            twins.setdefault(c["name"], []).append({"file": c["file"], "sha256": c["sha256"],
                                                    "bytes": c["bytes"]})
    served_files = {r["file"] for r in shelf.values()} | {c["file"] for c in copies}
    for rd in root_dirs:
        for name, r in sheets.items():
            cand = rd.parent / Path(r["file"]).name
            if cand.is_file() and str(cand) not in served_files and str(cand) != r["file"]:
                if any(t["file"] == str(cand) for t in twins.get(name, [])):
                    continue
                twins.setdefault(name, []).append({"file": str(cand), "bytes": cand.stat().st_size,
                    "sha256": hashlib.sha256(cand.read_bytes()).hexdigest()})
    diverged = sorted(n for n, ts in twins.items() if any(t["sha256"] != sheets[n]["sha256"] for t in ts))

    def end(n: str) -> str:
        return "a person model" if n in persons else n

    edges, faults, with_section = [], [], []
    for name in sorted(sheets):
        r = sheets[name]
        lines, present = _inverse_lines(Path(r["file"]))
        if present:
            with_section.append(name)
        for ln, cell, words in lines:
            for t in _names(cell):
                where = f"{show(r['file'])}:{ln}"
                if t not in shelf:
                    faults.append({"name": t, "where": where,
                                   "say": f"{name}'s sheet names {t!r}, which no served sheet is"})
                    continue
                withheld = t in persons
                edges.append({"carrier": name, "target": end(t), "where": where,
                              "words": "(withheld: a person model is at one end)" if withheld else words})
    prop, hand_files = [], set()
    for src in (proposed or []):
        for row in _proposed_edges(Path(src)):
            if "fault" in row and "carriers" not in row:
                faults.append({"name": "-", "where": show(row["src"]), "say": row["fault"]})
                continue
            if row.get("fault"):
                faults.append({"name": "-", "where": f"{show(row['src'])}:{row['line']}",
                               "say": row["fault"]})
                continue
            for a in row["carriers"]:
                for b in row["targets"]:
                    missing = [x for x in (a, b) if x not in shelf]
                    where = (f"{show(row['cited'])}:{row['cited_lines']}" if row.get("cited")
                             else f"{show(row['src'])}:{row['line']}")
                    if missing:
                        faults.append({"name": ", ".join(missing), "where": where,
                                       "say": "a proposed edge names " + " and ".join(repr(x) for x in missing)
                                              + ", which no served sheet is"})
                        continue
                    withheld = a in persons or b in persons
                    prop.append({"carrier": end(a), "target": end(b), "where": where,
                                 "words": "(withheld: a person model is at one end)" if withheld
                                          else row["words"],
                                 "_key": (a, b, " ".join(row["words"].split()))})
                    for f in (row["src"], row.get("cited")):
                        if f:
                            hand_files.add(str(f))
    # SPEC L9 (F1, pass 2, P5 O7/J6, card 19): the proposed edges are deduped to distinct
    # (from, to, claim) triples -- the true ends, so two withheld edges to two different person
    # models stay two -- and the read-back says raw lines, distinct triples, distinct pairs,
    # distinct source lines and the proposing hands, so 27 rows are not read as 27 edges.
    raw_n = len(prop)
    seen: dict = {}
    for e in prop:
        k = e["_key"] #guard:dedupe
        if k in seen:
            seen[k]["times"] += 1
            continue
        seen[k] = dict(e, times=1)
    prop = list(seen.values())
    pairs_n = len({e["_key"][:2] for e in prop})
    src_n = len({e["where"] for e in prop})
    hands = set()
    for f in sorted(hand_files):
        try:
            txt = _guard(f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for h in re.findall(r"\(for Corwin; ([A-Za-z0-9._-]+)\)", txt):
            hands.add(re.sub(r"(-\d+)+$", "", h))
    hand_words = (f"one model: {next(iter(hands))}" if len(hands) == 1 else
                  f"{len(hands)} models: {', '.join(sorted(hands))}" if hands else
                  "the proposing hand is not stated in the sources")

    md = [f"# LEDGER — who carries whose inverse ({today})", "",
          "*Regenerated by `persona_ledger` (polygram/mcp/persona.py); never hand-edited. Built "
          "only from the persona sheets' own \"Whose inverse I carry\" sections and, in its own "
          "marked section, from edges a review proposed. A new copy is made each time; the old "
          "ones are kept.*", "",
          "## Read-back in words", ""]
    n_roots = len(root_dirs)
    def cnt(n: int, one: str, many: str) -> str:
        return f"{_num(n)} {one if n == 1 else many}"
    def Cnt(n: int, one: str, many: str) -> str:
        c = cnt(n, one, many)
        return c[0].upper() + c[1:]
    rb = (f"This ledger read {cnt(len(sheets), 'persona sheet', 'persona sheets')} from "
          f"{cnt(n_roots, 'folder', 'folders')}. "
          f"{Cnt(len(persons), 'person model was', 'person models were')} found and counted here "
          "only, never named, because person models stay off Drive. ")
    rb += (f"{Cnt(len(with_section), 'sheet has', 'sheets have')} a \"Whose inverse I carry\" "
           f"section, and the sheets name {cnt(len(edges), 'edge', 'edges')} between them. ")
    if not with_section:
        rb += "No sheet has that section yet: writing it is persona-writing, which is the keeper's own pen. "
    rb += (f"{Cnt(raw_n, 'proposed edge row was', 'proposed edge rows were')} read (raw, before dedupe); "
           f"{cnt(len(prop), 'is a distinct (from, to, claim) edge', 'are distinct (from, to, claim) edges')}, "
           f"between {cnt(pairs_n, 'distinct (from, to) pair', 'distinct (from, to) pairs')}, from "
           f"{cnt(src_n, 'distinct source line', 'distinct source lines')}, proposed by review "
           f"({hand_words}) and not yet in any sheet; they are listed apart, and an edge proposed by "
           "one hand is not yet a net. "
           f"{Cnt(len(faults), 'fault was', 'faults were')} found. ")
    if diverged:
        rb += (f"{Cnt(len(diverged), 'sheet has', 'sheets have')} a second copy whose bytes differ "
               f"({', '.join(diverged)}); which copy is the master is the keeper's to say.")
    else:
        rb += "Every second copy of a sheet has the same bytes."
    md += [rb, ""]
    md += ["## Sheets", "",
           "| name | actor | version | sha256 | bytes | file | second copies |",
           "|---|---|---|---|---|---|---|"]
    for name in sorted(sheets):
        r = sheets[name]
        tw = twins.get(name, [])
        if not tw:
            tcell = "none"
        else:
            bits = []
            for t in tw:
                state = "same bytes" if t["sha256"] == r["sha256"] else "DIVERGED"
                bits.append(f"{state}: {show(t['file'])} ({t['bytes']} bytes, sha256 {t['sha256']})")
            tcell = "; ".join(bits)
        actor = ("model, not a person" if r.get("kind") == "model" else (r.get("actor") or "-"))
        md.append(f"| {name} | {_cell(actor)} | {_cell(_version(Path(r['file'])))} "
                  f"| {r['sha256']} | {r['bytes']} | {show(r['file'])} | {_cell(tcell)} |")
    md += ["", "## Edges in the sheets", ""]
    if edges:
        md += ["| carrier | carries the inverse of | what it knows (the sheet's own words) | where |",
               "|---|---|---|---|"]
        md += [f"| {e['carrier']} | {e['target']} | {_quote(e['words'])} | {e['where']} |" for e in edges]
    else:
        md.append("None yet. No served sheet has a \"Whose inverse I carry\" section.")
    md += ["", f"## Proposed by review ({hand_words}), not yet in a sheet", ""]
    if prop:
        md += [f"Each row is proposed by review ({hand_words}), not yet in a sheet. It is not "
               "part of the net until the carrier's own sheet says it. Repeated lines are shown "
               f"once; \"times\" says how often a line was proposed ({_num(raw_n)} lines, "
               f"{_num(len(prop))} distinct).", "",
               "| carrier | would carry the inverse of | what the source says | source | times |",
               "|---|---|---|---|---|"]
        md += [f"| {e['carrier']} | {e['target']} | {_quote(e['words'])} | {e['where']} | {e['times']} |"
               for e in prop]
    else:
        md.append("None given.")
    md += ["", "## Faults", ""]
    if faults:
        md += ["| name | where | what is wrong |", "|---|---|---|"]
        md += [f"| {_cell(f['name'])} | {f['where']} | {_cell(f['say'])} |" for f in faults]
    else:
        md.append("None.")
    md += ["", "## What the model was shown", "",
           f"To build this, the tool read the first {HEAD_LINES} lines, the version line and the "
           f"\"Whose inverse I carry\" section of each of the {_num(len(sheets) + len(persons))} "
           "sheets and person models, hashed each whole file (the bytes are hashed, not returned), "
           f"and read the arrow lines of {_num(len(proposed or []))} proposed sources and the "
           "lines they cite. It returned only what is printed above: names, actors, version lines, "
           "hashes, sizes, paths, and the quoted edge lines. No other line of any sheet, and no "
           "line of any person model, was returned to the model.", "",
           "Authored by Mentat (for Corwin; claude-opus-5-5).",
           "Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.",
           "SPDX-License-Identifier: CC-BY-SA-4.0", ""]
    say = rb
    return {"markdown": "\n".join(md), "sheets": len(sheets), "person_models": len(persons),
            "edges": edges, "proposed": [{k: v for k, v in e.items() if k != "_key"} for e in prop],
            "proposed_raw": raw_n, "proposed_pairs": pairs_n, "proposed_sources": src_n,
            "proposing_hands": sorted(hands),
            "faults": faults, "diverged": diverged, "with_section": with_section, "say": say}


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
                    "default_voice": default_voice(),
                    "say": (f"NOT SERVED HERE: no sheet named {slug!r}. This is "
                            "a FAULT, not a cue to mint one -- refusal 1. Fall "
                            "through to bin/mt1pl for rows 1-6; meanwhile the "
                            "plain voice speaks (default_voice).")}
        shelf, _sh, _roots = shelf_sheets()
        served = sorted(set(served) | set(shelf))
        return {"resolved": "", "row": None, "served": served,
                "order": [list(r) for r in ORDER],
                "default_voice": default_voice(),
                "say": "name a persona, or read rows 1-6 with bin/mt1pl; until one "
                       "resolves, the plain voice speaks (default_voice)"}

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
                         "note": _guard(p).read_text(encoding="utf-8", errors="replace"),
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
        # 2026-10-14: the threshold switch (prefs KNOWN persona.on_threshold), read here so the key has a
        # reader.  off: nothing.  propose / draft: the crossings would be named here; the counter that
        # finds a crossing is not built yet, so until it is this block says so in words rather than
        # listing nothing in silence.  No value of the switch mints a sheet.
        on_th = (_prefs.get("persona.on_threshold") or "off").strip().lower() or "off"
        threshold = {"setting": on_th,
                     "means": {"off": "no crossing is looked for; sheets are made only at his instruction",
                               "propose": "a crossing is named here and asked about, in words; nothing is written",
                               "draft": "a crossing is named here; a draft may go to the holding shelf, marked not-his-instruction, out of the index"}.get(on_th, "unknown value: read as off"),
                     "crossings": [],
                     "counter": "not built: the three thresholds (used twice outside a test run; cited twice; shipped through a cut with credit) have no counter yet, so no crossing can be reported" if on_th in ("propose", "draft") else ""}
        return {"count": len(rows), "personas": rows, "shelf_roots": roots, "threshold": threshold,
                "shadowed": shadowed, "copies": copies, "drift": drift, "split": split,
                "store_root": str(st.root),
                "say": f"{len(rows)} persona(s): {len(rows) - n_shelf} chained, "
                       f"{n_shelf} from the shelf (read-only); {len(copies)} other "
                       f"cop{'y' if len(copies) == 1 else 'ies'} elsewhere"
                       + (f", DIFFERING for: {', '.join(drift)}" if drift else ", all agreeing")
                       + (f"; SPLIT (one file name, two served names -- a stale copy of a renamed "
                          f"sheet?): {'; '.join(split)}" if split else "")
                       + f"; {store_say}"}

    @srv.tool("persona_ledger",
              "Read-only. Regenerate LEDGER.md: who carries whose inverse, read from each "
              "sheet's own 'Whose inverse I carry' section (never inferred, never kept), the "
              "sheets with their version line and full sha256, second copies that DIVERGED, "
              "faults (a name no sheet is), and, apart, edges a review proposed. Person models "
              "are counted, never named. Ends with a words read-back of what was shown.",
              {"type": "object",
               "properties": {"proposed": {"type": "array", "items": {"type": "string"},
                                           "description": "review or study files whose 'A -> B : words' lines are proposed edges"}}})
    def _ledger(args):
        return ledger([str(x) for x in (args.get("proposed") or [])])

    return srv


def main(argv=None) -> int:
    """Serve on stdio; or, with --ledger [--proposed FILE ...], print LEDGER.md and exit
    (python3 -m polygram.mcp persona --ledger)."""
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--ledger":
        prop, rest = [], argv[1:]
        while rest:
            if rest[0] == "--proposed" and len(rest) > 1:
                prop.append(rest[1]); rest = rest[2:]
            else:
                print(f"persona --ledger: unknown argument {rest[0]!r}", file=sys.stderr)
                return 2
        sys.stdout.write(ledger(prop)["markdown"])
        return 0
    build().serve()
    return 0
