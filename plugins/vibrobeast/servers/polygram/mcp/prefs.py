# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# GPL-3.0-or-later; see COPYING.  Authored by Mentat (for Corwin).

"""prefs -- the few switches this server honours, kept where he can read them.

Corwin, 2026-09-23: *"let's get such checks behind preference, by default on."*  So: a known
list of keys, each with a default and one line saying what it changes; a file that holds what
he set, append-only (last row per key wins, and the row says who and why); two tools, one to
list and one to set.  A key not on the list is refused -- a preference nobody reads is a note,
and it belongs in the seat, not here.

Where: ``$MENTCACHED_PREFS`` (must exist; a path you named is never created), else
``~/.mentcached/prefs.tsv`` (this server's choice, so it may create it).  Rows are
``ts  key  value  by  why``.  ``sh bin/pr1ef`` in the workspace reads the same file with awk.

A ROW IS REPORTED OR APPLIED, NEVER DROPPED (extension edition, 2026-10-10).  Every data row in the
file is one of three things, and ``classify()`` says which, with a reason in words: *applied* (the
last row for a key that has a reader), *superseded* (an earlier row for that key), or *ignored* (no
reader, or not a whole row).  ``pref_list`` lists the ignored rows under ``ignored:``; nothing is
skipped in silence.  ``pref_unset`` appends a row whose value is ``(unset)``: the key goes back to
its default.  ``python3 -m polygram.mcp.prefs --classify FILE`` prints the same table ``bin/pr1ef
--tsv`` prints, so ``tests/pr1ef-spec.rb`` can hold the two readers to one answer.

DECLARED KEYS AND PREFIXES (extension edition, A4; cards 06 and 22, agreement 6).  The key set stays
closed and grows by declaration: a skill lists the keys it reads under ``preferences:`` in its
SKILL.md front matter (``softskills.declared()`` finds them), and a declared key's reader is that
skill.  Three prefixes carry a name in the key, each with a named reader and a name check
(``PREFIXES``): ``person.<name>.<key>`` (the keeper or a participant he named in ``people.named``),
``room.<tavern>.<key>`` and ``skill.<skill>.<key>`` (that skill must declare it).

THE WRITER RULE for ``person.<name>.*`` (P1 J7 as narrowed, P2 J5): a row is written on that person's
own turn, on the keeper's turn for a participant he named, or with a consent row's id; otherwise it
is refused, and someone else's report becomes one question to that person, or a seat note.  Rows say
whose turn wrote them (the ``turn`` and ``consent`` columns), so the rule holds at read time too: a
hand-written row that breaks it is ignored, with the reason.  A ``person.<other>.*`` row is a third
party's fact: it never goes into the frame.

THE WRITER RULE for ``room.<tavern>.*`` (F1, pass 2, P5 O5/J4, card 06; it mirrors the person
rule).  A room preference is a rule for everyone in that room, so not just any turn may write it: a
row is written on the keeper's own turn, or on the turn of a participant he named (``people.named``)
who is present in that room's turn -- the call says ``room=<tavern>`` and it is the key's own
<tavern>.  Otherwise it is refused, in words.  The rule is checked at write; the room road is dormant
until gp.1, so no reader checks a hand-written row against it yet.

THE SEATKEEPER "NO" (card 22).  ``skill.seatkeeper.<hash>`` = ``no: <the folder's path>``, where
<hash> is the first 12 hex digits of sha256 over the path (backslashes made "/", one trailing "/"
dropped; ``seat_hash``).  The key is the hash; the value carries the path in words, and pref_list
reads it back as the path.  ``pref_unset`` takes the "no" back.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
from pathlib import Path

from .rpc import ToolError

DEFAULT_PATH = Path.home() / ".mentcached" / "prefs.tsv"
HEADER = "ts\tkey\tvalue\tby\twhy\tturn\tconsent"
KEEPER = "corwin"   # the keeper, unless $MENTCACHED_KEEPER names another
UNSET = "(unset)"   # the value pref_unset writes: the key goes back to its default

#: key -> (default, what it changes).  Add a row here when a check grows a switch.
KNOWN: dict[str, tuple[str, str]] = {
    "freshness.auto": ("on", "seat_mode and span_start report whether the installed plugin is the shelf's mint"),
    "freshness.shelf": ("", "the minted tree on the shelf; else $POLYGRAM_DIST, else a guess beside the seat"),
    "softskills.auto": ("on", "seat_mode and span_start report how many soft skills are loadable, and from where"),
    "softskills.roots": ("", "SOFT-SKILLS roots, os.pathsep-separated; else $SOFT_SKILLS, else ~/.mentcached/SOFT-SKILLS and <seat>/../SOFT-SKILLS"),
    "steward.auto": ("on", "nongnu-steward: ns1op runs its header + ledger audit at session open in a tree carrying .nongnu-steward"),
    "persona.sheets": ("", "folders holding persona sheets and person models, os.pathsep-separated, earlier wins a name; a file is a sheet by what its own first lines say (actor:, a sheet heading, or model front matter); else $PERSONA_SHEETS, else guessed from softskills.roots and words.root"),
    "words.root": ("", "the C4 root the word-path registry (word_where / word_register) reads: else $C4_ROOT, else /f/claude/c4, else ~/mnt/c4 -- whichever carries m/t"),
    "llamabridge.on": ("off", "llamabridge: off until set to on; when on, prompts Claude delegates go to the Ollama server at OLLAMA_HOST (default http://127.0.0.1:11434, this computer). Restart the plugin after changing it (the README's Words say how)"),
    "tavern.on": ("off", "tavern: off until set to on; when on, Claude can read and post in your Tavern rooms, and what is posted is copied to every member machine's disk. Restart the plugin after changing it (the README's Words say how)"),
    "tavern.as": ("claude", "tavern: the agent name Claude uses in the Tavern (Tavern adds this machine's address, e.g. claude-192.0.2.7, a documentation address). When unset, it is the agent already registered in the Tavern for this machine's person, else claude"),
    "tavern.data": ("", "tavern: the Tavern data folder, when it is not where Tavern's installer or a download would put it; else $TAVERN_DATA, else found by itself"),
    "gw.on": ("off", "gwstatus: off until set to on; when on, Claude can ask your listed hosts (GW_HOSTS, the hosts register) how they are and draw the ghostwheel status icon, asking first before any name lookup or new host key unless told always. Restart the plugin after changing it"),
    "c4.on": ("off", "c4face: off until set to on; when on, Claude can use your C4 work surface by running C4's own server (mcp/c4-mcp.js in your C4 folder) with node, after a check at every start. Restart the plugin after changing it (the README's Words say how)"),
    "c4.root": ("", "c4face: your C4 folder (the one holding mcp/c4-mcp.js), when it is not found by itself; else $C4_ROOT, else words.root, else a c4 folder near the seat or the shelf, else the usual places"),
    "steward.canon": ("on", "nongnu-steward: ns1op reports the canon pins' age and the check command at session open; it never fetches unasked"),
    "usage.capture": ("off", "usage capture: off until set to on; when on, span_start writes the token count at start and each new prompt writes the count after it, as rows in the frame (~/.mentcached/stats/fr; FRAME.md, beside this README, says each column in words). Those start and prompt rows hold two counts and a date, nothing else: no labels, no notes, no content. While it is on, the frame also mirrors each preference you set (key and value) and each question logged with question_log (its words); PRIVACY.md lists all of it. What the AI vendor sees is unchanged: the counts are ones the model already reports"),
    "tone.dial": ("0/0, 0/0", "tone: where the voice sits on two axes, answer length and narration, as signals seen / signals total on each; the default is the origin (no signals yet), which is plain voice"),
    "tone.show": ("words", "tone: how the tone reading is shown to you: words (a plain sentence, no numbers) or numbers"),
    "people.named": ("corwin", "the people whose person.<name>.* rows this server keeps: the keeper and the participants he named, comma-separated. Only the keeper's own turn changes it"),
}

#: prefix -> the key's shape, who reads it, and the name check.  A key under a prefix is read by
#: that reader; a key under no prefix and not in KNOWN needs a skill that declares it.
PREFIXES: dict[str, dict[str, str]] = {
    "person.": {"shape": "person.<name>.<key>",
                "reader": "the session-open quote: pref_list says each row in words",
                "check": "<name> is the keeper or a participant he named (people.named), and the row "
                         "was written on that person's own turn, on the keeper's turn, or with a consent row's id"},
    "room.": {"shape": "room.<tavern>.<key>",
              "reader": "the session-open quote: pref_list says each row in words (the room road "
                        "itself is dormant until gp.1 runs)",
              "check": "<tavern> is a plain name"},
    "skill.": {"shape": "skill.<skill>.<key>",
               "reader": "the skill <skill>",
               "check": "<skill> is loadable and declares the key in its SKILL.md preferences: list"},
}
_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_REST = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
SEAT_NO = "skill.seatkeeper."


def keeper() -> str:
    k = (os.environ.get("MENTCACHED_KEEPER") or "").strip().lower()
    return k if k and not k.startswith("$") and "%" not in k else KEEPER


def _split(key: str):
    """(prefix, name, rest) for a key under a prefix, else None."""
    for pfx in PREFIXES:
        if key.startswith(pfx):
            name, _, rest = key[len(pfx):].partition(".")
            return pfx, name, rest
    return None


def _names(value: str) -> list[str]:
    return [n for n in re.split(r"[,\s]+", (value or "").lower()) if n]


def seat_hash(path_words: str) -> tuple[str, str]:
    """(hash, the path as normalised) for a seatkeeper "no" key."""
    s = path_words.strip().replace("\\", "/")
    if len(s) > 1 and s.endswith("/"):
        s = s[:-1]
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12], s


def _match(pattern: str, key: str) -> bool:
    """A declared pattern; <anything> in it stands for one dot-free segment."""
    rx = "[^.]+".join(re.escape(part) for part in re.split(r"<[^>]*>", pattern))
    return re.fullmatch(rx, key) is not None


def _declared() -> dict:
    try:
        from . import softskills as _ss
        return _ss.declared()
    except Exception:          # noqa: BLE001 -- a broken scan declares nothing; rows are then reported, not lost
        return {}


def path() -> tuple[Path, bool]:
    raw = (os.environ.get("MENTCACHED_PREFS") or "").strip()
    if not raw or "${" in raw or raw.startswith("$"):
        return DEFAULT_PATH, True
    return Path(raw).expanduser(), False


def _rows(p: Path) -> list[list[str]]:
    if not p.is_file():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("ts\t"):
            continue
        f = ln.split("\t")
        if len(f) >= 3:
            out.append(f + [""] * (7 - len(f)))
    return out


def named(p: Path | None = None) -> list[str]:
    """The keeper plus the participants he named (people.named), lower-case."""
    nm = _names(current(p)["people.named"]["value"])
    k = keeper()
    return nm if k in nm else [k] + nm


def reader(key: str, decl: dict | None = None, names: list[str] | None = None) -> tuple[str | None, str]:
    """(who reads this key, or None; and why not, in words, when nobody does)."""
    if key in KNOWN:
        return "this server", ""
    sp = _split(key)
    if sp:
        pfx, name, rest = sp
        if not _NAME.match(name) or not _REST.match(rest):
            return None, f"not the shape {PREFIXES[pfx]['shape']} (plain lower-case names, dot-separated)"
        if pfx == "person.":
            nm = names if names is not None else named()
            if name not in nm:
                return None, (f"{name!r} is not a person this server keeps rows for: only the keeper and "
                              f"the participants he named (people.named: {', '.join(nm)})")
            return PREFIXES[pfx]["reader"], ""
        if pfx == "room.":
            return PREFIXES[pfx]["reader"], ""
        d = (decl if decl is not None else _declared()).get(name)
        if d is None:
            return None, f"no skill named {name!r} is loadable, so nobody reads it"
        if any(_match(k, key) for k in d["keys"]):
            return f"the skill {name}", ""
        return None, f"the skill {name} does not declare it in its preferences: list"
    for sname, d in (decl if decl is not None else _declared()).items():
        if any(_match(k, key) for k in d["keys"]):
            return f"the skill {sname}", ""
    return None, "no reader: not a known key, and no skill declares it in its preferences: list"


def writer(key: str, turn: str, consent: str, names: list[str] | None = None,
           room: str = "") -> str:
    """"" when this turn may write the key, else why not, in words (the person and room writer
    rules)."""
    t = (turn or "").strip().lower()
    if key == "people.named" and t != keeper():
        return (f"people.named is changed only on the keeper's ({keeper()}) own turn; this turn is "
                f"{t or 'unnamed'}")
    sp = _split(key)
    if sp and sp[0] == "room.":
        # SPEC F1-5: the keeper's turn, or a named participant present in that room's turn.
        tav = sp[1]
        nm = names if names is not None else named()
        here = (room or "").strip().lower()
        if t == keeper() or (t in nm and here == tav): #guard:room
            return ""
        return (f"a {key} row is a rule for everyone in the room {tav}, so it is written only on the "
                f"keeper's ({keeper()}) turn or on the turn of a participant he named who is in that "
                f"room's turn (room={tav}); this turn is {t or 'unnamed'}"
                + (f", in the room {here}" if here else ", with no room given")
                + ". Ask the keeper, or say it in that room")
    if not sp or sp[0] != "person.":
        return ""
    name = sp[1]
    nm = names if names is not None else named()
    if t == name or (t == keeper() and name in nm) or (consent or "").strip():
        return ""
    return (f"a {key} row is written only on {name}'s own turn, on the keeper's ({keeper()}) turn for "
            f"a participant he named, or with a consent row's id; this turn is {t or 'unnamed'}. "
            f"Ask {name} instead, or keep it as a seat note")


def _seat_shape(key: str, value: str) -> str:
    """At read: a seatkeeper row's value is "no: <path>" (or the unset mark)."""
    if not key.startswith(SEAT_NO) or value == UNSET:
        return ""
    if value.startswith("no: ") and value[4:].strip():
        return ""
    return "a seatkeeper row's value is 'no: <the folder's path>', so pref_list can say which folder"


def _seat_value(key: str, value: str) -> str:
    """At write: the shape, and the path must hash to the key."""
    bad = _seat_shape(key, value)
    if bad or not key.startswith(SEAT_NO) or value == UNSET:
        return bad
    h, _ = seat_hash(value[4:])
    if key[len(SEAT_NO):] != h:
        return (f"the path in the value hashes to {h}, not {key[len(SEAT_NO):]}; the key is "
                f"skill.seatkeeper.{h}")
    return ""


def classify(p: Path | None = None) -> list[dict]:
    """Every data row of the file, in file order, each marked applied, superseded or ignored.
    ``line`` is the physical line number (the header is line 1 when present)."""
    if p is None:
        p, _ = path()
    if not p.is_file():
        return []
    rows: list[dict] = []
    names = named(p)
    decl = None
    for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip() or ln.startswith("ts\t"):
            continue
        f = ln.split("\t")
        if len(f) < 3:
            rows.append({"line": n, "ts": f[0], "key": f[1] if len(f) > 1 else "", "value": "",
                         "by": "", "why": "", "status": "ignored",
                         "reason": "not a whole row: fewer than three fields"})
            continue
        f = f + [""] * (7 - len(f))
        if decl is None and f[1] not in KNOWN and (_split(f[1]) or ("", "", ""))[0] not in ("person.", "room."):
            decl = _declared()
        who, why_not = reader(f[1], decl if decl is not None else {}, names)
        if who:
            why_not = writer(f[1], f[5], f[6], names) or _seat_shape(f[1], f[2])
            if why_not:
                who = None
        rows.append({"line": n, "ts": f[0], "key": f[1], "value": f[2], "by": f[3], "why": f[4],
                     "turn": f[5], "consent": f[6],
                     "status": "applied" if who else "ignored", "reader": who or "",
                     "reason": "" if who else why_not})
    last: dict[str, dict] = {}
    for r in rows:
        if r["status"] == "applied":
            if r["key"] in last:
                last[r["key"]]["status"] = "superseded"
                last[r["key"]]["reason"] = f"a later row (line {r['line']}) sets this key"
            last[r["key"]] = r
    return rows


def ignored(p: Path | None = None) -> list[dict]:
    return [r for r in classify(p) if r["status"] == "ignored"]


def current(p: Path | None = None) -> dict[str, dict]:
    """key -> {value, source, by, ts} for every known key.  Known keys need no skill scan, so this
    reads the file alone (softskills.roots() calls it; a scan here would call itself)."""
    if p is None:
        p, _ = path()
    got = {}
    for f in _rows(p):
        if f[1] in KNOWN and not (f[1] == "people.named" and writer(f[1], f[5], f[6], [])):
            got[f[1]] = {"value": f[2], "by": f[3], "ts": f[0], "turn": f[5]}
    out = {}
    for k, (default, _what) in KNOWN.items():
        if k in got and got[k]["value"] != UNSET:
            g = got[k]
            out[k] = {"value": g["value"], "source": "file", "by": g["by"], "ts": g["ts"]}
        else:
            out[k] = {"value": default, "source": "unset" if k in got else "default",
                      "by": got[k]["by"] if k in got else "", "ts": got[k]["ts"] if k in got else ""}
    return out


def applied(p: Path | None = None) -> dict[str, dict]:
    """key -> the applied row, for every key with a reader other than this server (declared,
    person., room., skill.), leaving out keys whose last row is the unset mark."""
    return {r["key"]: r for r in classify(p)
            if r["status"] == "applied" and r["key"] not in KNOWN and r["value"] != UNSET}


def get(key: str) -> str:
    if key in KNOWN:
        return current()[key]["value"]
    if reader(key)[0] is None:
        raise KeyError(key)
    r = applied().get(key)
    return r["value"] if r else ""


def declined() -> list[dict]:
    """Every seatkeeper "no" in force: the key, the path in words and the date."""
    return [{"key": k, "path": r["value"][4:].strip(), "since": r["ts"][:10],
             "say": f"you said no to seating {r['value'][4:].strip()} on {r['ts'][:10]}; "
                    f"pref_unset {k} takes it back"}
            for k, r in applied().items() if k.startswith(SEAT_NO)]


def quote(turn: str = "") -> str:
    """The session-open quote, in words: the person., room. and declared rows in force, and every
    seatkeeper "no".  With ``turn`` (a person's name, not the keeper's), only that person's OWN
    ``person.<turn>.*`` rows are quoted: a third party's rows are never shown to someone else."""
    t = (turn or "").strip().lower()
    parts = []
    for k, r in applied().items():
        if k.startswith(SEAT_NO):
            continue
        sp = _split(k)
        if t and t != keeper() and sp and sp[0] == "person." and sp[1] != t:
            continue
        whose = (f"on {r['turn']}'s turn" if r.get("turn") else "turn not recorded") + (
            f", consent row {r['consent']} (not checked here)" if r.get("consent") else "")
        if sp and sp[0] == "person.":
            parts.append(f"{k} = {r['value']} ({whose}, {r['ts'][:10]})")
        elif sp and sp[0] == "room.":
            parts.append(f"{k} = {r['value']} (a wish for the room {sp[1]}, {whose})")
        else:
            parts.append(f"{k} = {r['value']} (read by {r['reader']})")
    return "; ".join(parts + [d["say"] for d in declined()])


def on(key: str) -> bool:
    return get(key).strip().lower() in ("on", "1", "true", "yes")


def set_(key: str, value: str, by: str, why: str, *, turn: str = "", consent: str = "",
         room: str = "", _unset: bool = False) -> dict:
    who, why_not = reader(key)
    if who is None:
        raise ToolError(f"unknown preference {key!r}: {why_not}. Known: {', '.join(KNOWN)}; or a key a "
                        "skill declares, or person.<name>.<key>, room.<tavern>.<key>, skill.<skill>.<key>. "
                        "A preference nobody reads is a note -- put it in the seat instead")
    if not _unset and " ".join(str(value).split()) == UNSET:
        raise ToolError(f"{UNSET!r} is the value pref_unset writes; use pref_unset {key} instead")
    bad = writer(key, turn, consent, room=room) or _seat_value(key, UNSET if _unset else " ".join(str(value).split()))
    if bad:
        raise ToolError(bad)
    p, ours = path()
    if not p.exists():
        if not ours:
            raise ToolError(f"MENTCACHED_PREFS names {p}, which does not exist; a path you named is "
                            "never created. Unset it, or create the file (empty is fine).")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(HEADER + "\n", encoding="utf-8", newline="\n")
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    one = lambda x: " ".join(str(x or "").split())   # noqa: E731
    row = [ts, key, one(value), one(by), one(why), one(turn).lower(), one(consent)]
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(row) + "\n")
    sp = _split(key)
    if sp and sp[0] == "person." and sp[1] != keeper():
        frame = "a third party's fact: never written to the frame"
    else:
        try:
            from . import spans as _spans
            frame = _spans.Frame(by).pref(key, row[2])
        except Exception as e:      # noqa: BLE001 -- the preference is set either way
            frame = f"frame not written: {e}"
    return {"key": key, "value": row[2], "file": str(p), "ts": ts, "reader": who, "frame": frame,
            "say": f"{key} = {row[2]!r} (read by {who})"}


def unset_(key: str, by: str, why: str, *, turn: str = "", consent: str = "", room: str = "") -> dict:
    was = current().get(key, {}).get("value") if key in KNOWN else (applied().get(key) or {}).get("value")
    out = set_(key, UNSET, by, why, turn=turn, consent=consent, room=room, _unset=True)
    default = KNOWN[key][0] if key in KNOWN else None
    out.update(value=default, was=was,
               say=f"{key} unset: back to its default {default!r} (was {was!r})" if key in KNOWN
               else f"{key} unset (was {was!r})")
    return out


def _ignored_words(rows: list[dict]) -> str:
    if not rows:
        return ""
    return (f"; {len(rows)} row(s) in the file ignored, listed under ignored: ("
            + ", ".join(f"line {r['line']} {r['key'] or '(no key)'}: {r['reason']}" for r in rows[:4])
            + (", ..." if len(rows) > 4 else "") + ")")


def register(srv, by: str) -> None:
    @srv.tool("pref_list",
              "Every preference this server honours: its current value, whether that came from "
              "the file or the default, and one line on what it changes.")
    def _list(_args):
        p, ours = path()
        cur = current()
        ign = ignored(p)
        q = quote()
        return {"file": str(p), "file_exists": p.is_file(), "chosen_by": "this server" if ours else "MENTCACHED_PREFS",
                "prefs": [{"key": k, **cur[k], "default": d, "what": w} for k, (d, w) in KNOWN.items()],
                "declared": [{"key": k, "value": r["value"], "reader": r["reader"], "turn": r["turn"],
                              "consent": r["consent"], "ts": r["ts"]} for k, r in applied(p).items()],
                "declined": declined(),
                "prefixes": [{"prefix": k, **v} for k, v in PREFIXES.items()],
                "ignored": [{k: r[k] for k in ("line", "key", "value", "reason")} for r in ign],
                "say": "; ".join(f"{k}={cur[k]['value'] or '(unset)'}" + ("" if cur[k]["source"] == "file" else " (default)")
                                 for k in KNOWN) + (f"; in force: {q}" if q else "") + _ignored_words(ign)}

    @srv.tool("pref_set",
              "Set one preference (append-only; the last row wins and says who and why). Accepted: "
              "the keys pref_list shows, a key a skill declares in its SKILL.md preferences: list, "
              "and person.<name>.<key>, room.<tavern>.<key>, skill.<skill>.<key>. A person.<name> "
              "row needs turn (whose words these are): that person's own, the keeper's for a "
              "participant he named, or a consent row's id. A room.<tavern> row is written on the "
              "keeper's turn, or a named participant's turn in that room (give room). A seatkeeper no is "
              "skill.seatkeeper.<hash> = 'no: <path>'.",
              {"type": "object",
               "properties": {"key": {"type": "string"}, "value": {"type": "string"},
                              "why": {"type": "string", "description": "one line"},
                              "turn": {"type": "string", "description": "whose turn asked for this, by name"},
                              "consent": {"type": "string", "description": "a consent row's id, when the person did not ask on their own turn"},
                              "room": {"type": "string", "description": "the room (tavern) this turn is in, for a room.<tavern> key"}},
               "required": ["key", "value"]})
    def _set(args):
        key = args.get("key", "")
        cur = (current().get(key, {}).get("value") if key in KNOWN
               else (applied().get(key) or {}).get("value"))
        out = set_(key, args.get("value", ""), by, args.get("why") or "",
                   turn=args.get("turn") or "", consent=args.get("consent") or "",
                   room=args.get("room") or "")
        out["was"] = cur
        out["say"] = f"{out['key']} = {out['value']!r} (was {cur!r}; read by {out['reader']})"
        return out

    @srv.tool("pref_unset",
              "Take a preference back: append a row that returns the key to its default. Nothing "
              "is rewritten; the earlier rows stay in the file as the record.",
              {"type": "object",
               "properties": {"key": {"type": "string"},
                              "why": {"type": "string", "description": "one line"},
                              "turn": {"type": "string", "description": "whose turn asked for this, by name"},
                              "consent": {"type": "string", "description": "a consent row's id"},
                              "room": {"type": "string", "description": "the room (tavern) this turn is in, for a room.<tavern> key"}},
               "required": ["key"]})
    def _unset(args):
        return unset_(args.get("key", ""), by, args.get("why") or "",
                      turn=args.get("turn") or "", consent=args.get("consent") or "",
                      room=args.get("room") or "")


def _main(argv: list[str]) -> int:
    """``--classify FILE``: one line per data row, ``line<TAB>key<TAB>status``, the shape
    ``bin/pr1ef --tsv`` prints, so the two readers can be compared byte for byte."""
    if len(argv) != 2 or argv[0] != "--classify":
        print("usage: python3 -m polygram.mcp.prefs --classify FILE")
        return 2
    for r in classify(Path(argv[1])):
        print(f"{r['line']}\t{r['key']}\t{r['status']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
