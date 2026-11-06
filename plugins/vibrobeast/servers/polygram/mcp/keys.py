# polygram -- gated agent-skill synthesis.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later; https://github.com/inputloop.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""keys -- the keys you keep, the names programs ask for them by, and a door that uses one.

Why it exists (2026-10-12, his party favour).  The first API token on the settings page is for
GitHub.  A token is kept once; programs ask for it under their own names (gh: GH_TOKEN, then
GITHUB_TOKEN; git over https: a header; git over ssh: GIT_SSH_COMMAND).  Binding the one to the
many by hand is the pain point.  Three pieces answer it:

ATOMS (2026-11-01).  When a ``keys/`` folder sits beside the register, the register is that folder: one
small file per key, ``keys/NAME.kv``, lines ``field: value``.  ``keys.tsv`` is then GENERATED from the
atoms (the same seven columns, sorted by name, byte-stable) so other readers (dn1or) keep working
unchanged.  Each change also appends to ``keys/NAME.hist``.  No ``keys/`` folder: the TSV is read and
written as before.  ``python3 -m polygram.mcp.keys --migrate`` moves a TSV to atoms once.  Restore: put the
``keys/`` folder back from git or a backup, then ``--rollup``.  See advice/ENHANCE-20261101-keys-as-atoms.md.

THE REGISTER -- a managed list, one row per key, ``~/.mentcached/keys.tsv`` (VIBROBEAST_KEYS_FILE
names another).  Append-only, like prefs.tsv: the last row for a NAME wins; KIND ``-`` removes it.

    NAME  KIND  SOURCE  BINDS  FOR  RUN  USAGE
    github  token  field:api_token  GH_TOKEN,GITHUB_TOKEN  github  gh,git  only inputloop repos

  KIND    token | ssh-key | password
  SOURCE  field:api_token | field:ssh_key | field:gw_password   (the settings page, via env)
          env:NAME  (an environment variable)  |  file:PATH  (a file holding the token, or the key file)
          Never the secret itself: a SOURCE without one of those prefixes is refused, and so is any
          cell that looks like a token (ghp_, github_pat_, glpat-, a long unbroken run).
  BINDS   names this key answers to, outright.  Empty: what the word file (key.md) lists for FOR.
  FOR     the services it is for, as tags (github, gitlab, npm, pypi, ssh, ghostwheel ...).
  RUN     programs key_run may start with it.  Empty: the word file's #run lines for FOR.
  USAGE   usage constraints in your words.  Shown back in every confirmation, never enforced by us.

  The settings page adds rows of its own, when the register does not name them: ``api`` (API token,
  FOR from "API token: for", USAGE from "API token: usage constraints"), ``ssh`` (SSH key, FOR ssh
  git), ``gw`` (the ghostwheel password).  A register row of the same NAME wins.

THE BINDER -- word balancing against key.md (a C4 word file).  A name the file lists takes that
line's #tags; a name it does not list is split at ``_`` and each piece looked up the same way, a
piece found nowhere standing for itself.  Each key scores: a name in its BINDS wins outright (100);
its KIND among the tags, 1; each FOR tag among them, 2.  Verdicts: BOUND (a BINDS hit, or the best
score includes a service), GUESS (kind only: say so and ask), TIE (two keys share the best score:
ask, never pick), NONE.  ``skills/pocket-binder/scripts/bind.sh`` is the second reader, in awk;
tests/kb1nd-spec.rb holds both to one spec.

THE DOOR -- key_run starts one program with one key bound, after a confirmation.  The first call
returns the confirmation (the key's name, the program, the folder, the USAGE text) and a code; the
second call, with that code, runs it.  The code proves the confirmation was returned to the model,
not that a person read it [PLATFORM]; Claude is asked to show it.  The value never leaves this
process: not in a result, not in a log; program output has it replaced by ``[key github]``.
Each code is random, runs once, and expires (CONFIRM_TTL); key_set asks the same way before it writes
(2026-10-22, the audit's HOLD item 13 and WARN J4).  Programs that would take a key as an argument
are handed it on input instead: docker login (--password-stdin), curl for DreamHost (a config, -K -).

THE PLAN DOOR (2026-11-04, plans.py) -- one code for a written plan.  key_run with argv ``plan_approve PLANFILE``
shows the whole plan in words and returns one code; with that code it writes an approval tied to the plan's
sha256.  Then each step of that plan, run exactly as written with the same key from the plan's folder, runs
with no code until the approval expires, its runs are used, or it is revoked; anything else asks as above,
and says why.  The keeper's switch is the preference keys.plans, which ships off: nothing here is on until he
turns it on.

THE KEYRING FOLDER -- one settings field (VIBROBEAST_KEYRING_DIR).  key_list names the files in it
that no register row names yet, with a kind guessed from the NAME (NAME beside NAME.pub: ssh-key;
*.pub skipped; *.pat, *.token: token; else unknown) and a warning when others can read one.  Read
by name, size and mode only; nothing in it is opened.

    python3 -m polygram.mcp.keys --bind NAME [--register FILE] [--lexicon FILE] [--tsv]
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import json
import secrets as _secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEXICON = HERE / "key.md"
STATE = Path.home() / ".mentcached"
COLS = ("name", "kind", "source", "binds", "for", "run", "usage")
KINDS = ("token", "ssh-key", "password", "login")
#: kind login: a program's own saved sign-in (gh auth login: a browser click, no token pages).  The
#: register names the program (source login:gh); nothing is bound, and the names a token would
#: answer to are taken OUT of the program's environment so its own sign-in is the one used.
LOGINS = {"gh": (("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"),
                 ("gh", "auth", "token"))}
FIELDS = {"api_token": "VIBROBEAST_API_TOKEN", "ssh_key": "VIBROBEAST_SSH_KEY",  # sb:allow (names, no values)
          "gw_password": "GW_PASSWORD"}
_LINE = re.compile(r"^- `([^`]+)`(.*)$")
_TAG = re.compile(r"#([a-z0-9][a-z0-9-]*)")
#: Shapes that are secrets, not references to one.  A register row carrying one is refused.
_LOOKS_SECRET = re.compile(r"(ghp_|gho_|ghs_|github_pat_|glpat-|npm_[A-Za-z0-9]{20}|pypi-Ag|"
                           r"sk-[A-Za-z0-9]{16}|-----BEGIN|[A-Za-z0-9+/=_-]{36,})")


def _env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    return "" if "${" in v else v


def register_file() -> Path:
    p = _env("VIBROBEAST_KEYS_FILE")
    return Path(p).expanduser() if p else STATE / "keys.tsv"


# ---------------------------------------------------------------- the word file
def lexicon(path: Path | None = None) -> dict[str, set[str]]:
    """NAME -> the union of the #tags on every array line naming it."""
    out: dict[str, set[str]] = {}
    for line in Path(path or LEXICON).read_text(encoding="utf-8").splitlines():
        m = _LINE.match(line)
        if m:
            out.setdefault(m.group(1), set()).update(_TAG.findall(m.group(2)))
    return out


def tags_for(name: str, lex: dict[str, set[str]]) -> tuple[set[str], list[str]]:
    """The tags a name balances to, and how each piece was read (for the words back)."""
    if name in lex:
        return set(lex[name]), [f"{name}: listed ({' '.join(sorted(lex[name]))})"]
    tags: set[str] = set()
    how = []
    for piece in [p for p in name.split("_") if p]:
        hit = lex.get(piece) or lex.get(piece.upper())
        if hit:
            tags |= hit
            how.append(f"{piece}: listed ({' '.join(sorted(hit))})")
        else:
            tags.add(piece.lower())
            how.append(f"{piece}: not listed, stands for itself")
    return tags, how


def run_for(services: set[str], lex: dict[str, set[str]]) -> list[str]:
    return sorted(n for n, t in lex.items() if "run" in t and t & services)


def binds_for(services: set[str], kind: str, lex: dict[str, set[str]]) -> list[str]:
    """Variable names (upper case, with an underscore: not the pieces of M4) of this kind that
    share a service with the key."""
    return sorted(n for n, t in lex.items()
                  if kind in t and t & services and "run" not in t and n.isupper() and "_" in n)


# ---------------------------------------------------------------- the register
def _split(cell: str) -> list[str]:
    return [x for x in re.split(r"[\s,;]+", cell or "") if x]


def problems_of(row: dict) -> list[str]:
    p = []
    if row["kind"] not in KINDS + ("-",):
        p.append(f"kind {row['kind']!r} is not one of {', '.join(KINDS)} (or - to remove)")
    src = row["source"]
    if row["kind"] != "-" and not re.match(r"^(field:(api_token|ssh_key|gw_password)|env:[A-Za-z_][A-Za-z0-9_]*|file:.+|login:(%s))$"
                                           % "|".join(LOGINS), src):
        p.append("source must be field:api_token, field:ssh_key, field:gw_password, env:NAME, file:PATH "
                 "or login:" + "|".join(LOGINS))
    if (row["kind"] == "login") != src.startswith("login:") and row["kind"] != "-":
        p.append("a login key's source is login:PROGRAM, and only a login key's is")
    for c in COLS:
        if c != "usage" and _LOOKS_SECRET.search(row.get(c) or "") and not (c == "source" and src.startswith("file:")):
            p.append(f"{c} looks like a secret itself; keep the value on the settings page or in a file, and name it here")
    if _LOOKS_SECRET.search(row.get("usage") or "") and re.search(r"(ghp_|github_pat_|glpat-|-----BEGIN)", row.get("usage") or ""):
        p.append("usage looks like it holds a secret; say the constraint in words")
    return p


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
ATOM_FIELDS = COLS            # name first; the file is NAME.kv


def keys_dir(path: Path | None = None) -> Path:
    """The atoms folder: VIBROBEAST_KEYS_DIR, else ``keys/`` beside the register file."""
    d = _env("VIBROBEAST_KEYS_DIR")
    return Path(d).expanduser() if d else Path(path or register_file()).parent / "keys"


def atom_text(row: dict) -> str:
    return "".join(f"{c}: {row.get(c) or ''}\n".replace(": \n", ":\n") for c in ATOM_FIELDS)


def parse_atom(text: str) -> dict:
    row = {c: "" for c in COLS}
    for line in text.splitlines():
        if ":" in line and not line.startswith("#"):
            f, _, v = line.partition(":")
            if f.strip() in row:
                row[f.strip()] = v.strip()
    return row


def read_atoms(d: Path) -> tuple[dict[str, dict], list[dict]]:
    rows: dict[str, dict] = {}
    ignored: list[dict] = []
    for f in sorted(d.glob("*.kv")):
        row = parse_atom(f.read_text(encoding="utf-8"))
        why = problems_of(row) if row["name"] else ["no name"]
        if row["name"] and f.name != row["name"] + ".kv":
            why.append(f"file name does not match name {row['name']!r}")
        if row["kind"] == "-":
            why.append("an atom is never kind -; remove the key to remove the file")
        if why:
            ignored.append({"line": f"keys/{f.name}", "name": row["name"], "reason": "; ".join(why)})
        else:
            row["line"] = f"keys/{f.name}"
            rows[row["name"]] = row
    return rows, ignored


def rollup_text(rows: dict[str, dict]) -> str:
    """keys.tsv as generated: a header, then one row per key, sorted by name.  Nothing else (no time)."""
    out = ["# keys register: " + "\t".join(c.upper() for c in COLS)
           + "  (GENERATED from keys/*.kv by polygram.mcp.keys; change the atoms, not this file)\n"]
    for n in sorted(rows):
        out.append("\t".join(rows[n].get(c, "") for c in COLS) + "\n")
    return "".join(out)


def _put(path: Path, text: str) -> bool:
    """Write only when the bytes differ, through a temp file; True when it wrote."""
    if path.is_file() and path.read_bytes() == text.encode("utf-8"):
        return False
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)
    return True


def write_rollup(path: Path | None = None) -> bool:
    p = Path(path or register_file())
    d = keys_dir(p)
    rows, _ = read_atoms(d)
    p.parent.mkdir(parents=True, exist_ok=True)
    return _put(p, rollup_text(rows))


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def set_atom(row: dict, path: Path | None = None, note: str = "set") -> str:
    """Write (or, kind -, remove) one atom, append its history, regenerate the roll-up.  Returns what happened."""
    p = Path(path or register_file())
    d = keys_dir(p)
    d.mkdir(parents=True, exist_ok=True)
    f = d / (row["name"] + ".kv")
    hist = d / (row["name"] + ".hist")
    if row["kind"] == "-":
        if f.is_file():
            f.unlink()
            with hist.open("a", encoding="utf-8", newline="") as fh:
                fh.write(f"# {_stamp()} removed\n")
        write_rollup(p)
        return "removed"
    text = atom_text(row)
    changed = _put(f, text)
    if changed:
        with hist.open("a", encoding="utf-8", newline="") as fh:
            fh.write(f"# {_stamp()} {note}\n{text}")
    write_rollup(p)
    return "written" if changed else "unchanged"


def migrate(tsv: Path | None = None, dry: bool = False) -> dict:
    """One-shot: the TSV (last row wins, - removes) becomes atoms.  Two-sided stop: if keys/ already holds
    atoms that differ from what the TSV gives, nothing is written.  Safe to run twice."""
    tsv = Path(tsv or register_file())
    d = keys_dir(tsv)
    rows, ignored = read_tsv(tsv)
    bad = sorted(n for n in rows if not SAFE_NAME.match(n))
    if bad:
        return {"ok": False, "say": "not migrated: these names cannot be file names: " + ", ".join(bad),
                "ignored": ignored}
    want = {n: atom_text(r) for n, r in rows.items()}
    have = {f.stem: f.read_text(encoding="utf-8") for f in sorted(d.glob("*.kv"))} if d.is_dir() else {}
    differ = sorted(n for n in set(want) | set(have) if want.get(n) != have.get(n))
    if have and differ:
        return {"ok": False, "stopped": True, "differ": differ, "ignored": ignored,
                "say": "stopped: keys/ already holds atoms that differ from keys.tsv (" + ", ".join(differ)
                       + "); nothing was written. Look at both sides and decide which is right."}
    if dry:
        return {"ok": True, "dry": True, "would_write": sorted(want), "ignored": ignored,
                "say": f"would write {len(want)} atom(s): " + ", ".join(sorted(want))}
    d.mkdir(parents=True, exist_ok=True)
    keep = d / (tsv.name + ".before-atoms")
    if tsv.is_file() and not keep.exists() and not have:
        shutil.copyfile(tsv, keep)
    for n, t in want.items():
        if have.get(n) != t:
            (d / (n + ".kv")).write_text(t, encoding="utf-8", newline="")
            with (d / (n + ".hist")).open("a", encoding="utf-8", newline="") as fh:
                fh.write(f"# {_stamp()} migrated from {tsv.name} line {rows[n].get('line')}\n{t}")
    write_rollup(tsv)
    return {"ok": True, "written": sorted(want), "ignored": ignored, "kept": str(keep) if keep.exists() else "",
            "say": f"{len(want)} atom(s) in {d}; {tsv.name} is now generated; the old one is kept as {keep.name}."}


def read_register(path: Path | None = None) -> tuple[dict[str, dict], list[dict]]:
    """(rows by NAME; ignored lines with their reason).  Atoms first: when the keys/ folder exists it is the
    register; otherwise the TSV."""
    p = Path(path or register_file())
    d = keys_dir(p)
    if d.is_dir():
        return read_atoms(d)
    return read_tsv(p)


def read_tsv(path: Path | None = None) -> tuple[dict[str, dict], list[dict]]:
    """(rows by NAME, last wins; ignored lines with their reason)."""
    p = Path(path or register_file())
    rows: dict[str, dict] = {}
    ignored: list[dict] = []
    if not p.is_file():
        return rows, ignored
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        row = dict(zip(COLS, (c.strip() for c in cells + [""] * len(COLS))))
        why = problems_of(row) if row["name"] else ["no name"]
        if why:
            ignored.append({"line": n, "name": row["name"], "reason": "; ".join(why)})
            continue
        if row["kind"] == "-":
            rows.pop(row["name"], None)
        else:
            row["line"] = n
            rows[row["name"]] = row
    return rows, ignored


def settings_rows() -> dict[str, dict]:
    """The rows the settings page implies, when its fields are filled."""
    out = {}
    if _env("VIBROBEAST_API_TOKEN"):
        out["api"] = {"name": "api", "kind": "token", "source": "field:api_token", "binds": "",
                      "for": _env("VIBROBEAST_API_TOKEN_FOR"), "run": "",
                      "usage": _env("VIBROBEAST_API_TOKEN_USAGE"), "line": "settings"}
    if _env("VIBROBEAST_SSH_KEY"):
        out["ssh"] = {"name": "ssh", "kind": "ssh-key", "source": "field:ssh_key", "binds": "",
                      "for": "ssh git " + _env("VIBROBEAST_SSH_KEY_FOR"), "run": "",
                      "usage": _env("VIBROBEAST_SSH_KEY_USAGE"), "line": "settings"}
    if _env("GW_PASSWORD"):
        out["gw"] = {"name": "gw", "kind": "password", "source": "field:gw_password", "binds": "",
                     "for": "ghostwheel", "run": "", "usage": _env("GW_PASSWORD_USAGE"),
                     "line": "settings"}
    return out


def keys(path: Path | None = None, lex=None) -> tuple[dict[str, dict], list[dict]]:
    lex = lex or lexicon()
    reg, ignored = read_register(path)
    rows = {**settings_rows(), **reg}
    for r in rows.values():
        svc = set(_split(r["for"]))
        r["binds_list"] = _split(r["binds"]) or binds_for(svc, r["kind"], lex)
        r["run_list"] = _split(r["run"]) or run_for(svc, lex)
    return rows, ignored


def value_of(row: dict) -> str:
    src = row["source"]
    if src.startswith("login:"):
        return src  # a marker, not a secret: the program keeps its own sign-in
    if src.startswith("field:"):
        return _env(FIELDS[src[6:]])
    if src.startswith("env:"):
        return _env(src[4:])
    p = Path(src[5:]).expanduser()
    if row["kind"] == "ssh-key":
        return str(p) if p.is_file() else ""
    try:
        return p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    except OSError:
        return ""


def stdin_value(row: dict) -> str:
    """What a key hands a program's input.  For an ssh key, the key file's own text, byte for byte
    (its value elsewhere is the file's path, which is what ssh -i wants; gh secret set wants the key).
    Found 2026-10-14, cast 2, before the first deploy key was set as a secret."""
    if row["kind"] == "ssh-key" and row["source"].startswith(("file:", "field:")):
        p = Path(value_of(row) or "")
        try:
            return p.read_text(encoding="utf-8") if p.is_file() else ""
        except OSError:
            return ""
    if row["kind"] == "login":
        return ""
    return value_of(row)


# ---------------------------------------------------------------- the binder
def bind(name: str, rows: dict[str, dict], lex: dict[str, set[str]]) -> dict:
    tags, how = tags_for(name, lex)
    scored = []
    for r in rows.values():
        if name in _split(r["binds"]):
            scored.append((100, r["name"], ["named in its BINDS"]))
            continue
        why, s = [], 0
        if r["kind"] in tags:
            s += 1
            why.append(f"kind {r['kind']}")
        svc = sorted(set(_split(r["for"])) & tags)
        if svc:
            s += 2 * len(svc)
            why.append("for " + " ".join(svc))
        if s:
            scored.append((s, r["name"], why))
    scored.sort(key=lambda x: (-x[0], x[1]))
    if not scored:
        verdict, key = "NONE", ""
    elif len(scored) > 1 and scored[0][0] == scored[1][0]:
        verdict, key = "TIE", ""
    elif scored[0][0] >= 2:
        verdict, key = "BOUND", scored[0][1]
    else:
        verdict, key = "GUESS", scored[0][1]
    best = scored[0][0] if scored else 0
    say = {"BOUND": f"{name} is answered by the key {key!r} ({'; '.join(scored[0][2])})." if scored else "",
           "GUESS": f"{name} might be the key {key!r}, but only its kind matched; ask before using it.",
           "TIE": f"{name} could be any of {', '.join(repr(s[1]) for s in scored if s[0] == best)}; "
                  "ask which (or add the name to one key's BINDS).",
           "NONE": f"no key you keep answers to {name}."}[verdict]
    return {"name": name, "verdict": verdict, "key": key, "score": best, "tags": sorted(tags),
            "read": how, "candidates": [{"key": k, "score": s, "why": w} for s, k, w in scored],
            "say": say}


# ---------------------------------------------------------------- the confirmation codes
_SALT = _secrets.token_bytes(16)
#: How long a confirmation's code stays good.  A person reading a confirmation and saying yes takes
#: minutes, not hours; a code older than this is refused and a new confirmation asked for.
CONFIRM_TTL = 15 * 60.0
_now = time.monotonic           # one clock for the codes; a test moves it


def _code(key: str, argv: list[str], cwd: str) -> str:
    """The fingerprint of what a confirmation was shown for (key, folder, words).  Not the code."""
    msg = "\x1f".join([key, cwd, *argv]).encode()
    return hmac.new(_SALT, msg, hashlib.sha256).hexdigest()[:16]


class Codes:
    """Confirmation codes, kept in this process only: each one random, good for one use, for the
    words it was shown with, until CONFIRM_TTL runs out.  Found 2026-10-19 (the security audit, HOLD
    item 13): the old code was a keyed hash of the words, so it ran again and again, for as long as
    the server lived.  When one code is used, every other code shown for the same words is spent too:
    a yes is for one run.  A restart forgets them all; nothing is written to disk."""

    MAX = 64

    def __init__(self):
        self.live: dict[str, tuple[str, float]] = {}   # code -> (fingerprint, expires)
        self.spent: dict[str, float] = {}               # code -> when it was spent or expired

    def issue(self, fp: str) -> str:
        now = _now()
        for c, (_f, exp) in list(self.live.items()):
            if exp <= now:
                self.spent[c] = now
                del self.live[c]
        while len(self.live) >= self.MAX:               # oldest first
            c = min(self.live, key=lambda k: self.live[k][1])
            self.spent[c] = now
            del self.live[c]
        if len(self.spent) > 4 * self.MAX:
            for c in sorted(self.spent, key=self.spent.get)[: len(self.spent) - 2 * self.MAX]:
                del self.spent[c]
        c = _secrets.token_hex(5)
        self.live[c] = (fp, now + CONFIRM_TTL)
        return c

    def take(self, code: str, fp: str) -> str:
        """'ok' (the code is good for these words and is now spent), 'used', 'expired' or 'other'
        (no code, or a code for other words: ask again, as a first call does)."""
        if not code:
            return "other"
        if code in self.spent:
            return "used"
        hit = self.live.get(code)
        if hit is None or not hmac.compare_digest(hit[0], fp):
            return "other"
        now = _now()
        if hit[1] <= now:
            del self.live[code]
            self.spent[code] = now
            return "expired"
        for c, (f, _e) in list(self.live.items()):
            if f == fp:
                del self.live[c]
                self.spent[c] = now
        return "ok"


CODES = Codes()
REFUSED = {"used": "That confirmation code was used already; a yes is for one run. Call again without "
                   "confirm for a new confirmation, and show it to the person.",
           "expired": "That confirmation code is more than %d minutes old and has expired. Call again "
                      "without confirm for a new confirmation, and show it to the person."
                      % int(CONFIRM_TTL // 60)}


# ---------------------------------------------------------------- the door


def _shq(s: str) -> str:
    """Quote one word for sh (and for git's own command splitter, which reads single quotes the
    same way): nothing inside single quotes is special, so a Windows path keeps its backslashes."""
    return "'" + s.replace("'", "'\\''") + "'"


def ssh_for_git() -> str:
    """The ssh git should run for a kept key.  On Windows, git's own bundled ssh is found first on
    git's PATH, and from inside the desktop extension it failed before reaching any host while
    the system's OpenSSH, started the same way, connected (2026-10-14, spells/api-heal, cast 1).
    So name the system's OpenSSH by absolute path, written with forward slashes.  Elsewhere: ssh."""
    if os.name != "nt":
        return "ssh"
    import shutil
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    for c in (os.path.join(root, "System32", "OpenSSH", "ssh.exe"), shutil.which("ssh") or ""):
        if c and os.path.isfile(c) and "\\git\\" not in c.lower().replace("/", "\\"):
            return c.replace("\\", "/")
    return "ssh"


def git_ssh_command(key_path: str, ssh: str | None = None) -> str:
    """BatchMode=yes: a question ssh would ask (trust this host? a passphrase?) fails at once, in words,
    instead of waiting on an input nobody can answer (2026-10-14, cast 2: a git run hung past the
    bridge's wait and held the extension)."""
    return (f"{_shq(ssh or ssh_for_git())} -i {_shq(key_path.replace(chr(92), '/'))} "
            f"-o IdentitiesOnly=yes -o BatchMode=yes")


def spellings(s: str) -> list[str]:
    """The ways a value can come back in a program's output: as given, with forward slashes, with
    backslashes doubled (a program quoting it), with backslashes for slashes.  Longest first, so a
    longer spelling is masked before a shorter one inside it."""
    v = {s, s.replace("\\", "/"), s.replace("\\", "\\\\"), s.replace("/", "\\")}
    return sorted((x for x in v if len(x) >= 4), key=len, reverse=True)


def bound_env(row: dict, value: str, program: str, lex) -> tuple[dict, list[str]]:
    """The environment additions (and argv additions) that bind one key for one program."""
    add: dict[str, str] = {}
    extra: list[str] = []
    if row["kind"] == "login":
        return add, extra
    if row["kind"] == "ssh-key":
        cmd = git_ssh_command(value)
        add["GIT_SSH_COMMAND"] = cmd
        # Git for Windows' installer can write ssh.variant=tortoiseplink into its system gitconfig
        # (the PuTTY/TortoiseGit choice).  git then adds PuTTY's -batch, which OpenSSH reads as
        # "-b atch" and fails looking up a host named "atch" (2026-10-14, cast 2).  The variable outranks
        # every config file, for this run only; the person's own git settings are left alone.
        add["GIT_SSH_VARIANT"] = "ssh"
        if program in ("ssh", "scp"):
            extra = ["-i", value, "-o", "IdentitiesOnly=yes"]
        for n in row["binds_list"]:
            add.setdefault(n, value if n != "GIT_SSH_COMMAND" else cmd)
        return add, extra
    for n in row["binds_list"]:
        add[n] = value
    if program == "git" and row["kind"] == "token":
        import base64
        svc = set(_split(row["for"]))
        hosts = (["github.com"] if "github" in svc else []) + (["gitlab.com"] if "gitlab" in svc else [])
        user = "oauth2" if "gitlab" in svc and "github" not in svc else "x-access-token"
        basic = base64.b64encode(f"{user}:{value}".encode()).decode()
        for i, h in enumerate(hosts):
            add[f"GIT_CONFIG_KEY_{i}"] = f"http.https://{h}/.extraheader"
            add[f"GIT_CONFIG_VALUE_{i}"] = f"AUTHORIZATION: basic {basic}"
        if hosts:
            add["GIT_CONFIG_COUNT"] = str(len(hosts))
    return add, extra


# ---------------------------------------------------------------- marshalling: how each program takes a key
# His ask, 2026-10-22 22:33: keys that want "careful martialing around".  Two programs here take a key
# in a way an environment variable cannot carry, and both would put it in their arguments if asked the
# obvious way (docker login -p KEY; curl "https://api.dreamhost.com/?key=KEY&...").  Arguments are
# seen by every process on the computer and land in shell histories and logs.  So the door hands the
# key to each on its input instead, and refuses the spellings that would put it in an argument.

#: Services whose API takes the key as a URL parameter: service -> (the API's host, the parameter).
#: DreamHost's API: https://api.dreamhost.com/?key=KEY&cmd=dns-list_records&format=json
URL_KEYS = {"dreamhost": ("api.dreamhost.com", "key")}
MARSHAL_SAID = {"docker": "docker login's input (--password-stdin), never an argument",
                "curl": "a curl config on its input (-K -), never an argument or a URL in the command line"}


def _is_password_arg(a: str) -> bool:
    return a in ("-p", "--password") or a.startswith("--password=") or (a.startswith("-p") and not a.startswith("--"))


def _the_url(argv: list[str]) -> list[int]:
    return [i for i, a in enumerate(argv) if i and a.lower().startswith(("http://", "https://"))]


def marshal_problem(row: dict, program: str, argv: list[str], stdin_row: dict | None) -> str:
    """Why this key cannot go to this program this way, in a sentence, or "".  Asked before any
    confirmation is shown, so a refused shape never earns a code."""
    from urllib.parse import parse_qsl, urlsplit
    if program == "docker":
        if row["kind"] != "token":
            return f"docker takes a token to log in; the key {row['name']!r} is a {row['kind']}."
        if argv[1:2] != ["login"]:
            return ("docker needs the key only to log in (docker login -u NAME [REGISTRY]); after that, "
                    "docker push and pull use the login docker kept. Run those without a key.")
        if any(_is_password_arg(a) for a in argv[1:]):
            return "leave -p/--password out: the door hands docker the key on its input (--password-stdin)."
        if stdin_row is not None:
            return "docker reads this key on its input already, so it cannot take a stdin_key too."
    if program == "curl":
        svc = [s for s in _split(row["for"]) if s in URL_KEYS]
        if not svc:
            return (f"curl gets a key here only as a URL parameter for a service the door knows "
                    f"({', '.join(sorted(URL_KEYS))}); the key {row['name']!r} is for "
                    f"{row['for'] or 'nothing named'}.")
        host, param = URL_KEYS[svc[0]]
        if stdin_row is not None:
            return "the door hands curl its config on input, so curl cannot take a stdin_key too."
        if any(a in ("-K", "--config") or a.startswith("--config=") or (a.startswith("-K") and len(a) > 2)
               for a in argv[1:]):
            return "leave -K/--config out: the door hands curl its own config on input."
        urls = _the_url(argv)
        if len(urls) != 1:
            return f"give curl exactly one URL (https://{host}/?...), without {param}=; it has {len(urls)}."
        u = urlsplit(argv[urls[0]])
        if u.scheme != "https" or (u.hostname or "").lower() != host:
            return f"the key {row['name']!r} goes only to https://{host}/, not {u.scheme}://{u.hostname}/."
        if any(k == param for k, _v in parse_qsl(u.query, keep_blank_values=True)):
            return f"leave {param}= out of the URL; the door adds it, in a config curl reads on its input."
    return ""


def marshal(row: dict, program: str, argv: list[str], value: str) -> tuple[list[str], str, list[str]]:
    """(the argv to run, what to hand the program's input, extra spellings to mask).  Only after
    marshal_problem said nothing and the person said yes."""
    from urllib.parse import parse_qsl, quote, quote_plus, urlencode, urlsplit, urlunsplit
    if program == "docker":
        return ([*argv] if "--password-stdin" in argv else [*argv, "--password-stdin"]), value + "\n", []
    if program == "curl":
        host, param = URL_KEYS[next(s for s in _split(row["for"]) if s in URL_KEYS)]
        i = _the_url(argv)[0]
        u = urlsplit(argv[i])
        q = urlencode([(param, value)] + parse_qsl(u.query, keep_blank_values=True))
        url = urlunsplit((u.scheme, u.netloc, u.path or "/", q, u.fragment))
        config = 'url = "' + url.replace("\\", "\\\\").replace('"', '\\"') + '"\n'
        # -q first: no .curlrc of anyone's may add a --trace that writes the URL to a file.
        return [argv[0], "-q", "-K", "-", *argv[1:i], *argv[i + 1:]], config, [quote_plus(value), quote(value, safe="")]
    return argv, "", []


# ---------------------------------------------------------------- the keyring folder
# His folder (2026-10-22): id_ed25519 and its .pub, tavern-pen-deploy and its .pub, docker.pat,
# dns-dreamhost.uak.  One settings field names the folder; the register still names each key.  The
# folder is read by NAME only: nothing in it is opened, hashed or copied here.
PUBLIC_SUFFIX = ".pub"
TOKEN_SUFFIXES = (".pat", ".token")
UNKNOWN = "unknown, say what it is"


def keyring_dir() -> Path | None:
    p = _env("VIBROBEAST_KEYRING_DIR")
    return Path(p).expanduser() if p else None


def guess_kind(name: str, names: set[str]) -> str:
    """A kind from a file's NAME and its neighbours' names: "" for a public half (skipped)."""
    if name.endswith(PUBLIC_SUFFIX):
        return ""
    if name + PUBLIC_SUFFIX in names:
        return "ssh-key"
    if name.lower().endswith(TOKEN_SUFFIXES):
        return "token"
    return UNKNOWN


def _same_file(a: str | Path, b: str | Path) -> bool:
    def norm(x) -> str:
        return os.path.normcase(os.path.normpath(os.path.abspath(os.path.expanduser(str(x)))))
    return norm(a) == norm(b)


def mode_warning(path: Path, mode: int) -> str:
    """A private file readable by others, said with its fix; on Windows, that it cannot be told."""
    if os.name == "nt":
        return (f"{path.name}: on Windows the mode bits ({oct(mode)}) do not say who may read it; its access "
                f"list does. To make it yours alone: icacls \"{path}\" /inheritance:r /grant:r \"%USERNAME%:R\"")
    if mode & 0o077:
        return f"{path.name} is readable by others ({oct(mode)}); fix: chmod 600 \"{path}\""
    return ""


def found_in_folder(rows: dict[str, dict], folder: Path | None = None) -> tuple[list[dict], list[str], str]:
    """(files in the keyring folder that no register row names, warnings, a problem in words).
    os.scandir and stat only: names, sizes and modes; never a file's contents."""
    folder = folder or keyring_dir()
    if folder is None:
        return [], [], ""
    if not folder.is_dir():
        return [], [], f"the keyring folder {folder} is not a folder here"
    named = [r["source"][5:] for r in rows.values() if r.get("source", "").startswith("file:")]
    if any(r.get("source") == "field:ssh_key" for r in rows.values()):
        named.append(_env(FIELDS["ssh_key"]))         # the settings page's key file: a path, not a secret
    reg = register_file()
    entries = sorted((e for e in os.scandir(folder) if e.is_file(follow_symlinks=False)), key=lambda e: e.name)
    names = {e.name for e in entries}
    found, warn = [], []
    for e in entries:
        if e.name.startswith(".") or _same_file(e.path, reg):
            continue
        kind = guess_kind(e.name, names)
        if not kind:
            continue
        st = e.stat(follow_symlinks=False)
        mode = st.st_mode & 0o777
        w = mode_warning(Path(e.path), mode)
        if w and (os.name != "nt" or not warn):      # on Windows the one sentence says it for all
            warn.append(w)
        if any(_same_file(e.path, n) for n in named):
            continue
        found.append({"file": e.name, "path": e.path, "size": st.st_size, "mode": oct(mode), "kind": kind,
                      "registered": False})
    return found, warn, ""


def same_key_names(rows: dict[str, dict]) -> list[str]:
    """One key file kept under more than one name, said with each name's usage words.  key_run keeps
    names apart by name only, and the ghostwheel door uses the settings page's SSH key whatever the
    register calls it, so a second name with narrower words reads as a second key (2026-11-01: the
    projects key was 'ssh' on the settings page and 'aboutcorwinhost' in the register; gw33 looked
    unreachable as gw33 although 'ssh' already reached it).  Paths only; no file is opened."""
    groups: list[tuple[str, list[dict]]] = []
    for r in rows.values():
        src = r.get("source", "")
        path = src[5:] if src.startswith("file:") else (_env(FIELDS["ssh_key"]) if src == "field:ssh_key" else "")
        if not path:
            continue
        for p, rs in groups:
            if _same_file(p, path):
                rs.append(r)
                break
        else:
            groups.append((path, [r]))
    out = []
    for path, rs in groups:
        if len(rs) < 2:
            continue
        names = " and ".join(f"'{r['name']}'" for r in rs)
        uses = "; ".join(f"{r['name']}: {r.get('usage') or 'no usage words'}" for r in rs)
        door = next((r["name"] for r in rs if r.get("source") == "field:ssh_key"), "")
        out.append(f"one key, {len(rs)} names: {names} are the same file ({Path(path).name}); their usage words: "
                   f"{uses}" + (f". The ghostwheel door uses this key as '{door}' (each host logs in under its "
                                f"own name unless its row says otherwise)" if door else "")
                   + ". Keep one name (key_set a dash row for the other) or make their words agree.")
    return out


def has_value(row: dict) -> bool:
    """Whether a key's value is there, without reading a file: a file source is there when the file
    exists and is not empty (key_list used to read each token file to say "set")."""
    src = row["source"]
    if src.startswith("file:"):
        try:
            return Path(src[5:]).expanduser().stat().st_size > 0
        except OSError:
            return False
    return bool(value_of(row))


# ---------------------------------------------------------------- the scrubber, chosen at mint
# His 22:49 answer: "output scrubbing adaptor is build time fixed (but not absolutely required to be
# an inline thing ...)".  scrub.py holds the scrubbers; the mint writes SCRUBBER beside this file
# (the name chosen, and scrub.py's sha256 as minted), the way the emacs recipe's tools carry the hash
# they were built against.  The masking in run() below the scrubber is the FLOOR: it always runs.
SCRUBBER_FILE = HERE / "SCRUBBER"


def scrubber() -> tuple[object, str]:
    """(the scrubber to run, or None for the floor alone; how it was chosen, in words)."""
    try:
        from . import scrub as _scrub
    except Exception as e:                           # noqa: BLE001 -- no scrub.py: the floor alone
        return None, f"floor (scrub.py did not load: {type(e).__name__})"
    if not SCRUBBER_FILE.is_file():
        return _scrub.SCRUBBERS[_scrub.DEFAULT], f"{_scrub.DEFAULT} (source: no SCRUBBER minted beside keys.py)"
    name, _, sha = SCRUBBER_FILE.read_text(encoding="utf-8").strip().partition("\t")
    if name not in _scrub.SCRUBBERS:
        return None, f"floor (SCRUBBER names {name!r}, which this scrub.py does not have)"
    if hashlib.sha256(Path(_scrub.__file__).read_bytes()).hexdigest() != sha.strip():
        return None, "floor (scrub.py is not the file minted with this package)"
    return _scrub.SCRUBBERS[name], f"{name} (minted)"


# Under the desktop bridge's own 60 s wait, so a slow run comes back as a sentence, not a silence.
RUN_TIMEOUT = 45.0


def standing_entries() -> list[tuple[str, str, str]]:
    """(key, program, target) for each standing yes in the keeper's preference keys.standing."""
    try:
        from . import prefs
        raw = (prefs.current().get("keys.standing") or {}).get("value") or ""
    except Exception:                                   # noqa: BLE001 -- no prefs: no standing yes
        return []
    out = []
    for part in raw.split(";"):
        f = part.split()
        if len(f) == 3:
            out.append((f[0], f[1], f[2]))
    return out


def _remote(arg: str) -> bool:
    """An scp operand that names another host: it holds '@', or a ':' anywhere but a drive letter's
    place (C:\\x and C:/x are this computer)."""
    i = arg.find(":")
    return "@" in arg or (i != -1 and i != 1)


def _same_dir(a: str, b: str) -> bool:
    """Two spellings of one folder (F:/x, F:\\x, f:/x/ are the same on Windows)."""
    def norm(x: str) -> str:
        return os.path.normcase(os.path.normpath(str(Path(x).expanduser().resolve())))
    try:
        return norm(a) == norm(b)
    except (OSError, ValueError):
        return False


# git subcommands a standing yes may cover, run in exactly its folder: they bring the remote's work
# home and change nothing anywhere else.  A pull runs fast-forward only (run() adds --ff-only), so a
# standing yes never makes a merge commit.  His ask, 2026-10-18: "please allow the git command that
# prompted the question going forward" (the pull of his Avalon copy of c4-draw-kiosk).
GIT_STANDING = ("pull", "fetch")


def standing_for(row: dict, program: str, argv: list[str],
                 entries: list[tuple[str, str, str]] | None = None, cwd: str | None = None) -> str:
    """The standing yes that covers this run, in words, or "" (it asks as before).

    Narrow on purpose: no argument may start with '-' (an ssh option such as ProxyCommand runs a
    program on THIS computer), so a remote command goes as ONE quoted argument ("ls -la", not ls
    -la, which asks); ssh only when its host argument is exactly the target; scp only
    pushing to the target, every source a local path and the destination TARGET:path (a pull
    could write this computer's files); git only `pull` or `fetch` alone, run in exactly the
    folder TARGET (no -C: the folder is the run's cwd).  His ask, 2026-10-15: "If you can't just
    attend to it then it's broken." -- a confirmation on every routine run to his own host."""
    m = standing_match(row, program, argv, entries, cwd)
    return f"standing yes ({m[0]} {m[1]} {m[2]}, keys.standing)" if m else ""


STANDING_SKIP_DASH = ("standing yes skipped: an argument starts with '-' (a standing yes never covers an "
                      "option, since an ssh option such as ProxyCommand runs a program on this computer)")


def standing_skip_reason(row: dict, program: str, argv: list[str],
                         entries: list[tuple[str, str, str]] | None = None) -> str:
    """Why a standing yes the keeper holds for this key and program did not cover this run, or "".
    ENHANCE-20261105 R4 (first asked 2026-10-16, Q2c): a code with no reason reads as a bug."""
    if not any(a.startswith("-") for a in argv[1:]):
        return ""
    ents = standing_entries() if entries is None else entries
    return STANDING_SKIP_DASH if any(k == row["name"] and p == program for k, p, _ in ents) else ""


def pinned_known_hosts(program: str, argv: list[str]) -> list[str]:
    """ssh or scp to a host whose key gw_known_hosts pins: the run checks that pin, strictly, and never the
    user's own known_hosts.  ENHANCE-20261105 R3: a survey helper failed "Host key verification failed"
    on gw34 with the pin in hand, because plain ssh looked elsewhere.  An argv that names its own
    UserKnownHostsFile is left as written; a host with no pin is left as before."""
    if program not in ("ssh", "scp") or any("UserKnownHostsFile" in a for a in argv):
        return argv
    try:
        from . import gwstatus
        if not gwstatus.KNOWN.is_file():
            return argv
        hit = False
        for a in argv[1:]:
            if a.startswith("-"):
                continue
            host = a.split("@", 1)[-1]
            if program == "scp":
                if not _remote(a):
                    continue
                host = host.split(":", 1)[0]
            if host and gwstatus.known(host.lower(), 22):
                hit = True
                break
        if not hit:
            return argv
        return [argv[0], "-o", f"UserKnownHostsFile={gwstatus.KNOWN}", "-o", "StrictHostKeyChecking=yes", *argv[1:]]
    except Exception:                                  # noqa: BLE001 -- no register: plain ssh as before
        return argv


def standing_match(row: dict, program: str, argv: list[str],
                   entries: list[tuple[str, str, str]] | None = None, cwd: str | None = None):
    """(key, program, target) of the standing yes that covers this run, or None (standing_for's rule)."""
    args = argv[1:]
    if not args or any(a.startswith("-") for a in args):
        return None
    for key, prog, target in (standing_entries() if entries is None else entries):
        if key != row["name"] or prog != program:
            continue
        if program == "ssh" and args[0] == target:
            return (key, prog, target)
        if program == "scp" and len(args) >= 2 and args[-1].startswith(target + ":") \
                and not any(_remote(a) for a in args[:-1]):
            return (key, prog, target)
        if program == "git" and len(args) == 1 and args[0] in GIT_STANDING and cwd \
                and _same_dir(cwd, target):
            return (key, prog, target)
    return None


def standing_decision(row: dict, program: str, argv: list[str], cwd: str | None = None,
                      entries: list[tuple[str, str, str]] | None = None, org: list | None = None) -> tuple[str, str]:
    """(stand, org_note): the standing yes after a group's ORG.md has had its say.  It can only narrow:
    a must not drops the standing yes (the run asks for a code as before); a prefer not keeps it and says so."""
    m = standing_match(row, program, argv, entries, cwd)
    if not m:
        return "", ""
    from . import orglimits
    lim = orglimits.standing(program, m[2], org, cwd)
    stand = f"standing yes ({m[0]} {m[1]} {m[2]}, keys.standing)"
    if lim is None:
        return stand, ""
    note = orglimits.say(lim)
    if lim["strength"] == "must not":
        return "", note + " So this run asks for a confirmation, as it would without a standing yes."
    return stand, note


# ---- the child's environment: a floor, not the server's own (the 2026-10-19 audit, BLOCK item 1) ----
#: What a child may inherit from this process.  Everything else -- every other key the server holds, the API
#: token, a password -- stays here.  The bound names are added on top.  Windows needs SystemRoot to open a
#: socket, COMSPEC/PATHEXT to find programs and ProgramData for Windows OpenSSH (without it ssh.exe exits 255
#: and prints nothing); both platforms need PATH and a home.  On Windows the names are matched without regard
#: to case: os.environ there hands every key back in upper case, so "ProgramData" written here never matched
#: PROGRAMDATA, and the first ssh under the floor (2026-10-26, 1.2.83 installed) failed with no message.
ENV_FLOOR = ("PATH", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "USER", "USERNAME", "LOGNAME", "SHELL",
             "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "TERM", "TZ", "TMPDIR", "TEMP", "TMP",
             "SystemRoot", "SYSTEMROOT", "SystemDrive", "COMSPEC", "ComSpec", "PATHEXT", "windir",
             "APPDATA", "LOCALAPPDATA", "ProgramData", "ALLUSERSPROFILE", "PUBLIC",
             "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432",
             "CommonProgramFiles", "CommonProgramFiles(x86)", "CommonProgramW6432",
             "OS", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
             "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR",
             "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "GIT_SSL_CAINFO",
             "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
             "SSH_AUTH_SOCK", "GIT_TERMINAL_PROMPT", "GIT_CONFIG_NOSYSTEM", "GH_HOST", "GH_PAGER", "GIT_PAGER",
             "PAGER", "EDITOR", "GIT_EDITOR", "PYTHONIOENCODING")


# ---- ssh -J: the hop gets the same key (found 2026-11-04 reaching an inner host through a hop) ----
#: How long the hop's own connection may take, in seconds (an invented number, from the house set).
JUMP_CONNECT_TIMEOUT = 17
_JUMP_HOST = re.compile(r"^(?P<h>(?:[A-Za-z0-9_.-]+@)?(?:\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9_.-]+))(?::(?P<p>[0-9]{1,5}))?$")


def _proxy_word(s: str, nt: bool) -> str:
    """One word of a ProxyCommand.  POSIX ssh hands the command to the shell (exec ...): single quotes.
    Windows OpenSSH splits it as a Windows command line: double quotes, and a double quote inside is refused."""
    if nt:
        if '"' in s:
            raise ValueError(f"{s!r} holds a double quote, which a Windows ProxyCommand cannot carry")
        return f'"{s}"'
    return _shq(s)


def jump_rewrite(args: list[str], exe: str, key_path: str, nt: bool | None = None) -> tuple[list[str], str]:
    """ssh -J HOST (or -o ProxyJump=HOST) starts a second ssh for the hop, and that one never sees the -i
    this door adds: the hop has no key, and the run dies in the banner exchange (2026-11-04, ssh -J
    hop@hop.example.org inner@192.0.2.27: "Connection timed out during banner exchange").  So the hop is
    rewritten as a ProxyCommand that runs the same ssh (by absolute path) with the same key FILE (its path,
    never its text), IdentitiesOnly, BatchMode and a connect timeout; it inherits ssh's own environment,
    which is already the floor.  A caller's own ProxyCommand is refused while a key is bound, and so is a
    chain (-J a,b): one hop per run.  -> (args without -J, problem); args unchanged when there is no -J."""
    nt = (os.name == "nt") if nt is None else nt
    out: list[str] = []
    hop = None
    i = 0
    while i < len(args):
        a = args[i]
        low = a.lower()
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if a == "-J":
            if not nxt:
                return args, "-J needs a host"
            val, i = nxt, i + 2
        elif a.startswith("-J"):
            val, i = a[2:], i + 1
        elif a == "-o" and nxt.lower().replace(" ", "").startswith("proxyjump="):
            val, i = nxt.split("=", 1)[1].strip(), i + 2
        elif low.replace(" ", "").startswith("-oproxyjump="):
            val, i = a.split("=", 1)[1].strip(), i + 1
        elif (a == "-o" and nxt.lower().lstrip().startswith("proxycommand")) or low.startswith("-oproxycommand"):
            return args, ("a ProxyCommand of the caller's own is not run with a key bound "
                          "(it would run any program with the key's path at hand); name the hop with -J HOST")
        else:
            out.append(a)
            i += 1
            continue
        if hop is not None:
            return args, "one -J per run"
        hop = val
    if hop is None:
        return args, ""
    if "," in hop:
        return args, "one jump host per run: -J a,b is a chain; run its hops one at a time"
    m = _JUMP_HOST.match(hop)
    if not m or hop.startswith("-"):
        return args, f"-J {hop!r} is not a plain [user@]host[:port]"
    try:
        words = [_proxy_word(exe, nt), "-i", _proxy_word(key_path, nt), "-o", "IdentitiesOnly=yes",
                 "-o", "BatchMode=yes", "-o", f"ConnectTimeout={JUMP_CONNECT_TIMEOUT}",
                 *(["-p", m.group("p")] if m.group("p") else []), "-W", "%h:%p", _proxy_word(m.group("h"), nt)]
    except ValueError as e:
        return args, str(e)
    return ["-o", "ProxyCommand=" + " ".join(words), *out], ""


def child_env(add: dict, environ: dict | None = None, nt: bool | None = None) -> dict:
    """The environment one run gets: the floor from this process, then the bound names.  Found 2026-10-19
    (the audit, BLOCK item 1): the child used to get the whole of os.environ plus the bound names, so a run with one key
    handed every other secret the server held to the program, and back out in its output.
    On Windows (nt) a floor name matches the process's key in any case, since os.environ upper-cases them there;
    elsewhere the names are exact (http_proxy and HTTP_PROXY are two variables).  environ and nt are for tests."""
    src = os.environ if environ is None else environ
    if (os.name == "nt") if nt is None else nt:
        floor = {k.upper() for k in ENV_FLOOR}
        env = {k: v for k, v in src.items() if k.upper() in floor}
    else:
        env = {k: v for k, v in src.items() if k in ENV_FLOOR}
    env.update(add)
    return env


def resolve_program(argv0: str) -> tuple[str, str, str]:
    """(name, path, problem): the program's bare name, where PATH says it is, and why not.  A caller names
    a program; it never gives a path.  Found 2026-10-19 (the audit, BLOCK item 2): RUN was checked against
    the basename and the path ran as given, so any file called ssh in any folder passed as ssh."""
    a = (argv0 or "").strip()
    if not a:
        return "", "", "nothing to run: argv is empty"
    if "/" in a or "\\" in a or a in (".", ".."):
        return "", "", (f"name the program, not a path: {a!r} has a slash, and only a program found on PATH "
                        "under its own name may run with a key bound")
    name = a
    for suffix in (".exe", ".cmd", ".bat"):
        name = name.removesuffix(suffix)
    # Where PATH says it is, so the result can say what ran.  When PATH has no such program the bare name
    # goes to the process start as before and its FileNotFoundError says so; a bare name can only be
    # found on PATH, which is the point.
    path = shutil.which(a) or (shutil.which(name) if name != a else "") or a
    return name, path, ""

# ---------------------------------------------------------------- background runs
# His words: key_run should not have "its own ideas about how long everyone's work will take".  The 45 s
# above is the desktop bridge's wait, not the work's; a run asked with background=true is started
# detached (its own session / process group), writes to a log under the seat folder, and returns a
# run_id at once.  key_result reads it, masked by the same scrubber and floor as a foreground run's output.
BG_DEFAULT_MAX = 3600.0
_RUN_ID = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")
#: What the detached process runs: the program, then its exit code written to a file, so the exit
#: survives the server restarting.  Its input and output are the ones it was started with.
_BG_WRAPPER = ("import os, subprocess, sys\n"
               "ef = sys.argv[1]\n"
               "try:\n"
               "    rc = subprocess.call(sys.argv[2:])\n"
               "except OSError as e:\n"
               "    sys.stderr.write('could not start %s: %s\\n' % (sys.argv[2], e)); rc = 127\n"
               "open(ef + '.tmp', 'w').write(str(rc)); os.replace(ef + '.tmp', ef)\n")
_BG: dict[str, dict] = {}          # run_id -> {"p": Popen, "secrets": [...]}: this server's own memory of its starts

#: mask_log (2026-11-05, his words: "The log masking is a good option to have: I do NOT want to enable it but I would
#: like to support it").  OFF unless a call says mask_log=true or the settings page's "Keys: mask background logs as
#: they are written" is on.  Then the detached process is a RELAY: it reads a one-line header on its input (the
#: values to mask, the mask word, the program's input; they travel over the pipe, never on disk or in an
#: argument), runs the program with its output on a pipe, and writes that output to the log only after masking it
#: (the same _mask_pair when this module can be imported there, and the floor of every spelling always).  The
#: last HOLD characters are kept back until more output arrives, so a value split between two reads is still
#: found; they are written when the program ends.  The log is then text (bytes that are not UTF-8 become U+FFFD)
#: and a running log can lag the program by up to HOLD characters.
MASK_LOG_ENV = "VIBROBEAST_KEYS_MASK_LOG"
_BG_RELAY = ("import codecs, importlib, json, os, subprocess, sys, threading\n"
             "ef = sys.argv[1]\n"
             "hdr = json.loads(sys.stdin.buffer.readline().decode('utf-8'))\n"
             "mask, floor, secrets, feed = hdr['mask'], hdr['floor'], hdr['secrets'], hdr['feed']\n"
             "hold = max([512] + [len(x) for x in floor])\n"
             "fn = None\n"
             "try:\n"
             "    sys.path.insert(0, hdr['root'])\n"
             "    fn = importlib.import_module(hdr['mod'])._mask_pair\n"
             "except Exception:\n"
             "    fn = None\n"
             "def scrub(t):\n"
             "    if fn is not None:\n"
             "        try:\n"
             "            t = fn(t, '', secrets, mask)[0]\n"
             "        except Exception:\n"
             "            pass\n"
             "    for x in floor:\n"
             "        t = t.replace(x, mask)\n"
             "    return t\n"
             "def emit(t):\n"
             "    if t:\n"
             "        sys.stdout.buffer.write(t.encode('utf-8', 'replace')); sys.stdout.buffer.flush()\n"
             "carry = ''\n"
             "rc = 127\n"
             "try:\n"
             "    p = subprocess.Popen(sys.argv[2:], stdin=subprocess.PIPE if feed else subprocess.DEVNULL,\n"
             "                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)\n"
             "except OSError as e:\n"
             "    emit(scrub('could not start %s: %s\\n' % (sys.argv[2], e)))\n"
             "else:\n"
             "    def feeder():\n"
             "        try:\n"
             "            p.stdin.write(feed.encode('utf-8')); p.stdin.close()\n"
             "        except OSError:\n"
             "            pass\n"
             "    if feed:\n"
             "        threading.Thread(target=feeder, daemon=True).start()\n"
             "    dec = codecs.getincrementaldecoder('utf-8')('replace')\n"
             "    fd = p.stdout.fileno()\n"
             "    while True:\n"
             "        b = os.read(fd, 65536)\n"
             "        if not b:\n"
             "            break\n"
             "        m = scrub(carry + dec.decode(b))\n"
             "        if len(m) > hold:\n"
             "            emit(m[:-hold]); carry = m[-hold:]\n"
             "        else:\n"
             "            carry = m\n"
             "    emit(scrub(carry + dec.decode(b'', True))); carry = ''\n"
             "    rc = p.wait()\n"
             "open(ef + '.tmp', 'w').write(str(rc)); os.replace(ef + '.tmp', ef)\n")


def mask_log_wanted(asked=None, environ: dict | None = None) -> bool:
    """mask_log: the call's own word when it gave one (true or false), else the settings page's field; off when neither
    is plainly on.  A field left as the template text, or empty, is off."""
    if asked is not None:
        return bool(asked)
    raw = (os.environ if environ is None else environ).get(MASK_LOG_ENV) or ""
    return raw.strip().lower() in ("true", "1", "on", "yes")


def runs_dir() -> Path:
    e = os.environ.get("VIBROBEAST_RUNS_DIR")
    return Path(e).expanduser() if e else STATE / "runs"


def _mask_pair(out: str, err: str, secrets_seen: list, mask: str) -> tuple[str, str, str]:
    """The one place output is masked: the minted scrubber, then the floor (always).  run() and key_result both call it."""
    fn, scrubbed_by = scrubber()
    if fn is not None:
        out, err = fn(out, secrets_seen, mask), fn(err, secrets_seen, mask)
    for s in secrets_seen:                           # the floor: after any scrubber, always
        for sp in spellings(s or ""):
            out, err = out.replace(sp, mask), err.replace(sp, mask)
    return out, err, scrubbed_by


def _write_meta(path: Path, meta: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, default=str))


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        q = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=15)
        return f" {pid} " in q.stdout.replace("\r", " ")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, stdin=subprocess.DEVNULL, timeout=30)
        return
    import signal
    try:
        os.killpg(pid, signal.SIGKILL)               # start_new_session made pid its own group's leader
    except (ProcessLookupError, PermissionError):
        pass


def _bg_start(row: dict, stdin_row: dict | None, program: str, exe: str, extra: list, argv: list, shown: list,
              cwd: str, env: dict, feed: str, secrets_seen: list, max_seconds: float, plan_ref,
              mask_log: bool = False, mask: str = "") -> dict:
    d = runs_dir()
    d.mkdir(parents=True, exist_ok=True)
    rid = time.strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(3).hex()
    log, exitf, meta_f = d / f"{rid}.log", d / f"{rid}.exit", d / f"{rid}.json"
    fd = os.open(str(log), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)   # the log holds unmasked bytes: owner only
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kw["start_new_session"] = True
    try:
        with os.fdopen(fd, "wb") as lf:
            p = subprocess.Popen([sys.executable, "-I", "-c", _BG_RELAY if mask_log else _BG_WRAPPER, str(exitf), exe, *extra, *argv[1:]],
                                 cwd=cwd, env=env, stdin=subprocess.PIPE if (feed or mask_log) else subprocess.DEVNULL,
                                 stdout=lf, stderr=subprocess.STDOUT, **kw)
    except OSError as e:
        return {"ok": False, "say": f"{program} could not be started in the background ({e.__class__.__name__})."}
    if mask_log:
        seen = [x for x in secrets_seen if x]
        floor = sorted({sp for x in seen for sp in spellings(x)}, key=len, reverse=True)
        head = {"mask": mask, "floor": floor, "secrets": seen, "feed": feed or "",
                "root": str(Path(__file__).resolve().parents[__name__.count(".")]), "mod": __name__}
        try:
            p.stdin.write((json.dumps(head) + "\n").encode("utf-8"))   # json.dumps escapes newlines: one line
            p.stdin.close()
        except OSError:
            pass
    elif feed:
        try:
            p.stdin.write(feed.encode("utf-8"))
            p.stdin.close()
        except OSError:
            pass
    _BG[rid] = {"p": p, "secrets": [x for x in secrets_seen if x]}
    meta = {"run_id": rid, "pid": p.pid, "started": time.time(), "max_seconds": max_seconds, "key": row["name"],
            "stdin_key": stdin_row["name"] if stdin_row else "", "program": program, "argv": shown, "cwd": cwd,
            "plan_ref": plan_ref, "noted": False}
    if mask_log:
        meta["mask_log"] = True
    _write_meta(meta_f, meta)
    if plan_ref:
        from . import plans
        plans.ran(plan_ref, "started")
    return {"ok": True, "run_id": rid, "pid": p.pid, "max_seconds": max_seconds, "mask_log": bool(mask_log),
            "say": f"{program} started in the background as run {rid} (stopped after {max_seconds:.0f} s if still running "
                   f"when key_result checks); key_result {rid} reads it."
                   + (" Its log is masked as it is written." if mask_log else "")}


def _masks_again(row: dict, stdin_row: dict | None, program: str, argv: list, lex) -> list:
    """The secrets run() would have masked, found again from the register, so key_result can mask after a restart."""
    value = value_of(row)
    feed = stdin_value(stdin_row) if stdin_row is not None else ""
    argv2, own_feed, masks = marshal(row, program, list(argv), value)
    if own_feed:
        feed = own_feed
    add, _ = bound_env(row, value, program, lex)
    login_secret = ""
    if row["kind"] == "login":
        drop, ask = LOGINS[row["source"][6:]]
        env = child_env(add)
        for n in drop:
            env.pop(n, None)
        try:
            q = subprocess.run(list(ask), env=env, capture_output=True, input="", text=True, encoding="utf-8",
                               errors="replace", timeout=15)
            login_secret = q.stdout.strip() if q.returncode == 0 else ""  # sb:allow (a name; its value is read at run time, only to mask it)
        except (OSError, subprocess.TimeoutExpired):
            login_secret = ""
    return [value, feed, login_secret, *masks] + [v for k, v in add.items() if k.startswith("GIT_CONFIG_VALUE_")]


def result(run_id: str, tail: int = 60, lex=None) -> dict:
    """What a background key_run is doing: running, exited (with its exit code) or stopped, its seconds, and the
    last TAIL lines of its output, masked exactly as a foreground run's output is.  The cap (max_seconds) is
    checked HERE, when this is called, not by a timer: a run nobody asks about keeps running."""
    run_id = (run_id or "").strip()
    if not _RUN_ID.match(run_id):
        return {"ok": False, "say": "run_id is the id key_run gave when it started the run in the background."}
    d = runs_dir()
    try:
        meta = json.loads((d / f"{run_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"ok": False, "say": f"no background run {run_id} here."}
    tail = max(1, min(int(tail or 60), 2000))
    exitf, log = d / f"{run_id}.exit", d / f"{run_id}.log"
    now = time.time()
    elapsed = now - meta["started"]
    rc = None
    state = "running"
    if exitf.exists():
        state = "exited"
        try:
            rc = int(exitf.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            rc = None
    else:
        mem = _BG.get(run_id)
        alive = (mem["p"].poll() is None) if mem else _pid_alive(int(meta["pid"]))
        if meta.get("stopped"):
            state = "stopped"
        elif alive and elapsed > float(meta["max_seconds"]):
            _kill_tree(int(meta["pid"]))
            meta["stopped"] = True
            state = "stopped"
        elif not alive:
            state = "ended"                          # gone without writing its exit code (killed from outside?)
    if state in ("exited", "ended", "stopped") and not meta.get("noted"):
        meta["noted"] = True
        if meta.get("plan_ref"):
            from . import plans
            plans.journal([plans._stamp(), "ENDED", *(str(meta["plan_ref"].get(k, "")) for k in ("plan", "sha12", "approval", "step")),
                           rc if rc is not None else state, *(str(meta["plan_ref"].get(k, "")) for k in ("key", "target", "folder")), ""])
    if state == "stopped" or meta.get("noted"):
        try:
            _write_meta(d / f"{run_id}.json", meta)
        except OSError:
            pass
    # the secrets: this server's own memory of the start, and again from the register (survives a restart)
    secrets_seen = list((_BG.get(run_id) or {}).get("secrets") or [])
    try:
        rows, _ = keys(lex=lex or lexicon())
        row = rows.get(meta["key"])
        if row is not None:
            srow = rows.get(meta["stdin_key"]) if meta.get("stdin_key") else None
            secrets_seen += _masks_again(row, srow, meta["program"], meta["argv"], lex or lexicon())
    except Exception:                                # noqa: BLE001 -- fall back on what the start remembered
        pass
    if not [x for x in secrets_seen if x]:
        return {"ok": False, "run_id": run_id, "state": state,
                "say": "the key this run used cannot be found again, so its output cannot be masked and is not shown."}
    try:
        raw = log.read_bytes()
    except OSError:
        raw = b""
    cut = len(raw) > 2_000_000
    text = raw[-2_000_000:].decode("utf-8", errors="replace")
    if cut:
        text = text.split("\n", 1)[-1]
    text, _e, scrubbed_by = _mask_pair(text, "", secrets_seen, f"[key {meta['key']}]")
    lines = text.splitlines()[-tail:]
    say = {"running": f"still running after {elapsed:.0f} s",
           "exited": f"exited {rc} after {elapsed:.0f} s",
           "ended": f"ended after {elapsed:.0f} s, exit code unknown (the process went away without writing one)",
           "stopped": f"over max_seconds ({meta['max_seconds']:.0f}), stopped"}[state]
    return {"ok": (rc == 0) if state == "exited" else None, "run_id": run_id, "state": state, "exit": rc,
            "seconds": round(elapsed, 1), "output": "\n".join(lines)[-20000:], "lines": len(lines),
            "scrubber": scrubbed_by, "say": f"{meta['program']} {say}."}


def run(row: dict, argv: list[str], cwd: str, confirm: str, lex, timeout: float = RUN_TIMEOUT,
        stdin_row: dict | None = None, background: bool = False,
        max_seconds: float = BG_DEFAULT_MAX, mask_log: bool | None = None) -> dict:
    """Run one program with one key bound.  background=True starts it detached and returns a run_id at once
    (key_result reads it); max_seconds then bounds it, checked when key_result is called, not by a timer."""
    if argv and argv[0] in ("plan_approve", "plan_revoke", "plan_list"):
        # The plan door (2026-11-04, plans.py): one code for a written plan, then its steps run with none.
        from . import plans
        return plans.door(row, argv, cwd, confirm, lex)
    program, exe, problem = resolve_program(argv[0] if argv else "")
    if problem:
        return {"ok": False, "say": problem}
    if program not in row["run_list"]:
        return {"ok": False, "say": f"the key {row['name']!r} may start {', '.join(row['run_list']) or 'nothing'}; "
                                   f"not {program}. Add it to the key's RUN to allow it."}
    shown = list(argv)
    pre = marshal_problem(row, program, argv, stdin_row)
    if pre:
        return {"ok": False, "say": pre}
    if program == "ssh" and row["kind"] == "ssh-key":
        _, jp = jump_rewrite(argv[1:], exe, "KEY")   # refuse before a confirmation is asked or spent
        if jp:
            return {"ok": False, "say": jp}
    value = value_of(row)
    if not value:
        return {"ok": False, "say": f"the key {row['name']!r} has no value where it says ({row['source']})."}
    cwd = str(Path(cwd or ".").expanduser().resolve())
    feed = ""
    if stdin_row is not None:
        feed = stdin_value(stdin_row)
        if not feed:
            return {"ok": False, "say": f"the key {stdin_row['name']!r} has no value where it says ({stdin_row['source']}), so there is nothing to hand {program}."}
    fp = _code(row["name"] + ("<" + stdin_row["name"] if stdin_row else ""), shown, cwd)
    usage = row.get("usage") or "(no usage constraints written for this key)"
    present = (f"About to run {' '.join(shown)} in {cwd} with the key {row['name']!r} "
               f"({row['kind']}, for {row['for'] or 'unspecified'}) "
               + (f"handed over as {MARSHAL_SAID[program]}" if program in MARSHAL_SAID else
                  f"bound as {', '.join(row['binds_list']) or 'its own'}")
               + f". Its usage constraints, in your words: {usage}"
               + (f" It also hands the key {stdin_row['name']!r} to the program's input (its usage constraints: "
                  f"{stdin_row.get('usage') or 'none written'})." if stdin_row else ""))
    stand, org_note = standing_decision(row, program, argv, cwd=cwd) if stdin_row is None else ("", "")
    if not stand and stdin_row is None:
        why = standing_skip_reason(row, program, argv)
        if why:
            present += f" ({why}.)"
    push_yes = None
    if program == "git" and argv[1:2] != ["push"]:
        sub = argv[1] if len(argv) > 1 else ""
        alias = ""
        if sub and not sub.startswith("-"):
            try:
                alias = subprocess.run(["git", "-C", cwd, "config", "--get", f"alias.{sub}"], capture_output=True,
                                       text=True, encoding="utf-8", timeout=15, stdin=subprocess.DEVNULL).stdout
            except (OSError, subprocess.TimeoutExpired):
                alias = ""
        if "push" in argv[2:] and sub.startswith("-") or "push" in alias:
            from . import pushyes
            pushyes.write_log([time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), cwd, "", "", " ".join(argv[1:]),
                               "REFUSED", "a push by another spelling (-C, an option first, or an alias)", ""], [value, feed])
            return {"ok": False, "say": "a push goes only as `git push REMOTE REFSPEC`, run in its folder (give the folder as "
                                        "cwd, not -C; no alias): the push door decides it, and nothing else may"}
    if program == "git" and argv[1:2] == ["push"]:
        # A push's yes is decided by a tool, never by a code the model passes back (his words,
        # 2026-10-22 23:38: "avoid using claude logic to work with them and use tool wherever we can").
        from . import pushyes
        d = pushyes.decide(argv, cwd, [value, feed])
        push_yes = {k: d[k] for k in ("verdict", "reasons", "place", "range", "log")}
        if d["verdict"] != "GO":
            return {"ok": False, "push_yes": push_yes,
                    "say": f"push {d['verdict']}: " + "; ".join(d["reasons"][-1:]) + " (decided by the push door; no code can open it)"}
        stand = f"push yes ({d['place']}, {d['range']}, fr1me egress GO)"
    plan_ref = None
    if not stand and stdin_row is None:
        # An approved plan may cover this exact run (plans.match); if not, the confirmation says why.
        from . import plans
        plan_ref, plan_why = plans.match(row, program, argv, cwd)
        if plan_ref:
            stand = plan_ref["stand"]
        elif plan_why:
            present += " " + plan_why
    habit_off = False
    if not stand:
        # The Habit row off (habit.py, 2026-11-04): no code of ours; the app's own approval of this key_run call
        # was the yes.  A group's ORG.md limit on standing yeses for this program, at any host, keeps the code
        # (it can only narrow; the stricter reading, since no standing row names a target here).
        from . import habit
        if not habit.on():
            # (nothing standing or planned: the person's own command runs as written, with no --ff-only added)
            from . import orglimits
            lim = orglimits._strongest([x for x in orglimits.limits(cwd) if x["setting"] == "keys.standing"
                                        and (not x["program"] or x["program"] == program)])
            if lim is not None and lim["strength"] == "must not":
                note = (orglimits.say(lim) + " So this run asks for a confirmation, though the Habit row is off.")
                org_note = (org_note + " " + note) if org_note else note
            else:
                stand, habit_off = habit.ran_without_code(), True
                if lim is not None:
                    note = orglimits.say(lim)
                    org_note = (org_note + " " + note) if org_note else note
    if stand and not habit_off and program == "git" and argv[1:] == ["pull"]:
        argv = [*argv, "--ff-only"]                  # a standing pull never makes a merge commit
    if not stand:
        took = CODES.take(confirm, fp)
        if took in REFUSED:
            return {"ok": False, "refused": took, "say": REFUSED[took]}
        if took != "ok":
            if not org_note:
                present += " (Asked because the Habit row, Extra Checks for potentially unsafe things, is on.)"
            return {"ok": None, "confirm": CODES.issue(fp), "present": present,
                    **({"org": org_note} if org_note else {}),
                    "say": (org_note + " " if org_note else "") +
                           "Show the person this confirmation, with the usage constraints, and call key_run "
                           "again with confirm set to the code only if they agree. The code is good for one "
                           f"run, within {int(CONFIRM_TTL // 60)} minutes."}
    argv, own_feed, masks = marshal(row, program, argv, value)
    if own_feed:
        feed = own_feed
    add, extra = bound_env(row, value, program, lex)
    if program == "ssh" and row["kind"] == "ssh-key":
        rest, jp = jump_rewrite(argv[1:], exe, value)  # the hop of a -J gets the same key file
        if jp:
            return {"ok": False, "say": jp}
        argv = [argv[0], *rest]
    argv = pinned_known_hosts(program, argv)       # after the code: the yes was given to the argv as shown
    env = child_env(add)                             # the floor plus the bound names; never the server's own
    login_secret = ""
    if row["kind"] == "login":
        drop, ask = LOGINS[row["source"][6:]]
        for n in drop:
            env.pop(n, None)
        try:  # learn the login's own token only to mask it, should the program print it
            q = subprocess.run(list(ask), env=env, capture_output=True, input="", text=True, encoding="utf-8", errors="replace", timeout=15)
            login_secret = q.stdout.strip() if q.returncode == 0 else ""  # sb:allow (a name; its value is read at run time, only to mask it)
        except (OSError, subprocess.TimeoutExpired):
            login_secret = ""
    if os.name == "nt" and not (env.get("SystemRoot") or env.get("SYSTEMROOT")):
        # A process started without SystemRoot cannot open a socket on Windows; the extension's
        # environment is the host's to choose, so put back the one variable networking needs.
        env["SystemRoot"] = r"C:\Windows"
    t0 = time.time()
    if background:
        mask_seen = [value, feed, login_secret, *masks] + [v for k, v in add.items() if k.startswith("GIT_CONFIG_VALUE_")]
        out = _bg_start(row, stdin_row, program, exe, extra, argv, shown, cwd, env, feed, mask_seen, max_seconds, plan_ref,
                        mask_log=mask_log_wanted(mask_log), mask=f"[key {row['name']}]")
        if out.get("ok"):
            out["bound"] = sorted(add)
            if stand:
                out["standing"] = stand
                out["say"] += f" Ran on a {stand}, no confirmation asked."
            if org_note:
                out["org"] = org_note
            if push_yes:
                out["push_yes"] = push_yes
        return out
    try:
        p = subprocess.run([exe, *extra, *argv[1:]], cwd=cwd, env=env, capture_output=True,
                           # always an input of our own: inherited, it would be the server's own
                           # protocol pipe, and a prompt could sit on it until the bridge gave up.
                           # Bytes, not text: in text mode Windows writes every \n as \r\n, and a
                           # key with \r\n endings is refused ("Load key: error in libcrypto");
                           # found 2026-10-14, cast 2, on the pen job's first run with the deploy key.
                           input=feed.encode("utf-8"),
                           timeout=timeout)
        out = p.stdout.decode("utf-8", errors="replace")
        err = p.stderr.decode("utf-8", errors="replace")
        rc = p.returncode
        if plan_ref:
            plans.ran(plan_ref, rc)                  # one journal line per covered run: it counts the budget
    except FileNotFoundError:
        if plan_ref:
            plans.ran(plan_ref, "not-found")
        return {"ok": False, "say": f"{argv[0]} is not on this computer's PATH."}
    except subprocess.TimeoutExpired:
        if plan_ref:
            plans.ran(plan_ref, "timeout")
        return {"ok": False, "say": f"{argv[0]} ran past {timeout:.0f} s; the local client was stopped, and "
                                    "the remote command may still be running. background: true runs it detached "
                                    "(key_result reads it later)."}
    mask = f"[key {row['name']}]"
    secrets_seen = [value, feed, login_secret, *masks] + [v for k, v in add.items() if k.startswith("GIT_CONFIG_VALUE_")]
    out, err, scrubbed_by = _mask_pair(out, err, secrets_seen, mask)
    return {"ok": rc == 0, "exit": rc, "stdout": out[-20000:], "stderr": err[-8000:],
            "seconds": round(time.time() - t0, 2), "bound": sorted(add), "scrubber": scrubbed_by, "ran": exe,
            "say": f"{program} exited {rc} after {time.time() - t0:.1f} s with {row['name']!r} bound "
                   f"as {', '.join(sorted(k for k in add if not k.startswith('GIT_CONFIG')))}"
                   + (f"; ran on a {stand}, no confirmation asked" if stand else "")
                   + (f". {org_note}" if org_note and stand else ""),
            **({"standing": stand, "present": present} if stand else {}),
            **({"org": org_note} if org_note else {}),
            **({"push_yes": push_yes} if push_yes else {})}


# ---------------------------------------------------------------- tools
def _public(r: dict) -> dict:
    return {"name": r["name"], "kind": r["kind"], "source": r["source"], "for": _split(r["for"]),
            "binds": r["binds_list"], "run": r["run_list"], "usage": r.get("usage") or "",
            "from": ("settings page" if r.get("line") == "settings" else
                     f"atom {r.get('line')}" if str(r.get("line")).startswith("keys/") else
                     f"register line {r.get('line')}"),
            "value": "set" if has_value(r) else "not set"}


def register(srv) -> None:
    @srv.tool("key_list",
              "The keys you keep (the key register plus the settings page's API token, SSH key and "
              "password): each one's kind, what it is for, the names it answers to, the programs it "
              "may start, its usage constraints, and whether its value is set; and the files in the "
              "keyring folder no row names yet (name, size, mode, a kind guessed from the name), with a "
              "warning for a private file others can read. Never a value; no file is opened.")
    def _list(_args):
        rows, ignored = keys()
        pub = [_public(r) for r in rows.values()]
        say = "; ".join(f"{p['name']}: {p['kind']} for {' '.join(p['for']) or '(unspecified)'}, answers to "
                        f"{', '.join(p['binds']) or 'nothing listed'}, value {p['value']}"
                        + (f", usage: {p['usage']}" if p["usage"] else "") for p in pub) or "no keys kept"
        if ignored:
            say += f"; {len(ignored)} register line(s) ignored: " + ", ".join(
                f"line {i['line']} ({i['reason']})" for i in ignored[:3])
        found, warn, why = found_in_folder(rows)
        warn = warn + same_key_names(rows)
        if found:
            say += ("; found in the keyring folder, not registered: " + ", ".join(
                f"{f['file']} ({f['kind']}, {f['size']} bytes, {f['mode']})" for f in found)
                + ". Name each with key_set (source file:PATH) to use it.")
        if warn:
            say += "; WARNING: " + "; ".join(warn)
        if why:
            say += "; " + why
        folder = keyring_dir()
        return {"register": str(register_file()), "keys": pub, "ignored": ignored,
                "keyring_folder": str(folder) if folder else "", "found": found, "warnings": warn, "say": say}

    @srv.tool("key_bind",
              "Which key you keep answers to a name a program asks for (GH_TOKEN, GIT_SSH_COMMAND, "
              "OPENAI_API_KEY ...), by balancing the name's words against the key word file. Says "
              "BOUND, GUESS (ask first), TIE (ask which) or NONE, and how each word was read. Never a value.",
              {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]})
    def _bind(args):
        lex = lexicon()
        rows, _ = keys(lex=lex)
        return bind(args.get("name", ""), rows, lex)

    @srv.tool("key_set",
              "Add or change one key in the register (append-only; the last row for a name wins; kind - "
              "removes it). The key itself is never written here: source names where it lives "
              "(field:api_token, field:ssh_key, field:gw_password, env:NAME, file:PATH). The first call "
              "writes nothing: it returns the row as it would be written and a code; show the person the "
              "row and call again with confirm set to the code only if they agree.",
              {"type": "object",
               "properties": {**{c: {"type": "string"} for c in COLS}, "confirm": {"type": "string"}},
               "required": ["name", "kind"]})
    def _set(args):
        row = {c: (args.get(c) or "").replace("\t", " ").replace("\n", " ").strip() for c in COLS}
        why = problems_of(row)
        if why:
            return {"ok": False, "say": "not written: " + "; ".join(why)}
        p = register_file()
        line = "\t".join(row[c] for c in COLS)
        fp = _code("key_set", [line], str(p))
        took = CODES.take(args.get("confirm") or "", fp)
        if took in REFUSED:
            return {"ok": False, "refused": took, "say": "not written: " + REFUSED[took]}
        if took != "ok":
            what = ("remove the key " + repr(row["name"]) if row["kind"] == "-" else
                    f"keep the key {row['name']!r} ({row['kind']}, source {row['source']}, for "
                    f"{row['for'] or 'unspecified'}, programs {row['run'] or 'from the word file'}, "
                    f"usage: {row['usage'] or 'none written'})")
            return {"ok": None, "confirm": CODES.issue(fp), "row": dict(row), "register": str(p),
                    "present": f"About to write one row to {p}: {what}.",
                    "say": "Nothing is written yet. Show the person this row and call key_set again with "
                           "the same fields and confirm set to the code only if they agree."}
        if keys_dir(p).is_dir():
            if not SAFE_NAME.match(row["name"]):
                return {"ok": False, "say": "not written: a key's name is a file name here: letters, digits, "
                                            "_ . - only, starting with a letter or digit"}
            did = set_atom(row, p)
            return {"ok": True, "register": str(p), "atom": str(keys_dir(p) / (row["name"] + ".kv")),
                    "say": f"{row['name']} {did}; key_list reads it back."}
        p.parent.mkdir(parents=True, exist_ok=True)
        new = not p.is_file()
        with p.open("a", encoding="utf-8") as fh:
            if new:
                fh.write("# keys register: " + "\t".join(c.upper() for c in COLS)
                         + "  (append-only; the last row for a NAME wins; KIND - removes)\n")
            fh.write(line + "\n")
        return {"ok": True, "register": str(p),
                "say": f"{row['name']} {'removed' if row['kind'] == '-' else 'written'}; key_list reads it back."}

    @srv.tool("key_run",
              "Run one program (gh, git, glab, ssh, scp, npm, twine: whatever the key's RUN allows) with "
              "one key bound under the names it answers to. The first call returns a confirmation to "
              "show the person, with the key's usage constraints, and a code; call again with confirm "
              "set to that code to run. A code runs once, within 15 minutes. A written plan needs one code for all "
              "its steps: argv [\"plan_approve\", PLANFILE] shows it in words and asks once; then each step, run "
              "exactly as written from the plan's folder, needs none until the approval ends (plan_revoke ID ends "
              "it early; plan_list shows them; the plan file's shape is plans.py's docstring). docker login gets a token "
              "on its input; curl gets a DreamHost key in a config on its input (give the URL without "
              "key=). The key's value is never returned, never an argument; output has it masked. "
              "A run that may take long (over about 45 s, which is the desktop bridge's wait) is asked with "
              "background=true: after the same confirmation it starts detached, writing to a log in the seat folder, "
              "and returns a run_id at once; key_result with that run_id reads it (running or exited, the exit code, "
              "the last lines, masked the same). max_seconds (default 3600) bounds a background run; it is checked "
              "when key_result is called, not by a timer. A plan step may run in the background too.",
              {"type": "object",
               "properties": {"key": {"type": "string", "description": "a key's name, or a name it answers to (GH_TOKEN)"},
                              "argv": {"type": "array", "items": {"type": "string"}},
                              "cwd": {"type": "string"},
                              "stdin_key": {"type": "string", "description": "a key whose value is handed to the program's input, never its arguments (gh secret set NAME reads it there)"},
                              "confirm": {"type": "string"},
                              "background": {"type": "boolean", "description": "start it detached and return a run_id at once; read it with key_result"},
                              "max_seconds": {"type": "number", "description": "background only: stop the run if still going when key_result is called past this many seconds (default 3600)"},
                              "mask_log": {"type": "boolean", "description": "background only: mask the key's value as the log is written, so it never reaches the disk (default: the settings page's choice, which ships off; key_result masks what it shows either way)"}},
               "required": ["key", "argv"]})
    def _run(args):
        lex = lexicon()
        rows, _ = keys(lex=lex)
        k = args.get("key", "")
        row = rows.get(k)
        if row is None:
            b = bind(k, rows, lex)
            if b["verdict"] != "BOUND":
                return {"ok": False, "say": b["say"], "bind": b}
            row = rows[b["key"]]
        feed_row = None
        if args.get("stdin_key"):
            sk = args["stdin_key"]
            feed_row = rows.get(sk)
            if feed_row is None:
                b2 = bind(sk, rows, lex)
                if b2["verdict"] != "BOUND":
                    return {"ok": False, "say": "stdin_key: " + b2["say"], "bind": b2}
                feed_row = rows[b2["key"]]
        try:
            cap = float(args.get("max_seconds") or BG_DEFAULT_MAX)
        except (TypeError, ValueError):
            return {"ok": False, "say": "max_seconds is a number of seconds."}
        if cap <= 0:
            return {"ok": False, "say": "max_seconds must be more than 0."}
        return run(row, list(args.get("argv") or []), args.get("cwd") or "", args.get("confirm") or "", lex,
                   stdin_row=feed_row, background=bool(args.get("background")), max_seconds=cap,
                   mask_log=args.get("mask_log") if isinstance(args.get("mask_log"), bool) else None)

    @srv.tool("key_result",
              "Read a key_run that was started with background=true: give its run_id. Says running, exited (with the "
              "exit code) or stopped, the seconds it has taken, and the last `tail` lines (default 60) of its output "
              "with any key value masked exactly as key_run masks. A run past its max_seconds is stopped when this is "
              "called (checked at the call, not by a timer).",
              {"type": "object",
               "properties": {"run_id": {"type": "string"}, "tail": {"type": "integer", "description": "lines from the end (default 60)"}},
               "required": ["run_id"]})
    def _result(args):
        return result(args.get("run_id") or "", args.get("tail") or 60)


def _main(argv: list[str]) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python3 -m polygram.mcp.keys")
    ap.add_argument("--bind", action="append", default=[])
    ap.add_argument("--register")
    ap.add_argument("--lexicon")
    ap.add_argument("--tsv", action="store_true")
    ap.add_argument("--migrate", action="store_true", help="move keys.tsv to keys/NAME.kv atoms, once")
    ap.add_argument("--dry-run", action="store_true", help="with --migrate: say what would be written")
    ap.add_argument("--rollup", action="store_true", help="regenerate keys.tsv from the atoms (after a restore)")
    ap.add_argument("--found", metavar="FOLDER", help="the keyring folder read by name: FILE KIND MODE per line")
    a = ap.parse_args(argv)
    if a.migrate or a.rollup:
        reg = Path(a.register) if a.register else register_file()
        if a.migrate:
            r = migrate(reg, dry=a.dry_run)
            print(r["say"])
            return 0 if r["ok"] else 1
        if not keys_dir(reg).is_dir():
            print(f"no atoms folder at {keys_dir(reg)}")
            return 1
        print("keys.tsv rewritten" if write_rollup(reg) else "keys.tsv already matches the atoms")
        return 0
    lex = lexicon(Path(a.lexicon) if a.lexicon else None)
    rows, _ = keys(Path(a.register) if a.register else None, lex=lex)
    if a.found:
        found, warn, why = found_in_folder(rows, Path(a.found))
        for f in found:
            print(f"{f['file']}\t{f['kind']}\t{f['mode']}")
        for w in warn:
            print("WARNING\t" + w)
        if why:
            print("PROBLEM\t" + why)
            return 1
    for n in a.bind:
        b = bind(n, rows, lex)
        print(f"{n}\t{b['verdict']}\t{b['key'] or '-'}\t{b['score']}" if a.tsv else b["say"])
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
