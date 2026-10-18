# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
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

THE REGISTER -- a managed list, one row per key, ``~/.mentcached/keys.tsv`` (VIBROBEAST_KEYS_FILE
names another).  Append-only, like prefs.tsv: the last row for a NAME wins; KIND ``-`` removes it.

    NAME  KIND  SOURCE  BINDS  FOR  RUN  USAGE
    github  token  field:api_token  GH_TOKEN,GITHUB_TOKEN  github  gh,git  only inputloop repos

  KIND    token | ssh-key | password
  SOURCE  field:api_token | field:ssh_key | field:gw_password   (the settings page, via env)
          env:NAME  (an environment variable)  |  file:PATH  (a file holding the token, or the key file)
          Never the secret itself: a SOURCE without one of those prefixes is refused, and so is any
          cell that looks like a token (ghp_, github_pat_, glpat-, a long unbroken run).
  BINDS   names this key answers to, outright.  Empty: what the word file (secret.md) lists for FOR.
  FOR     the services it is for, as tags (github, gitlab, npm, pypi, ssh, ghostwheel ...).
  RUN     programs key_run may start with it.  Empty: the word file's #run lines for FOR.
  USAGE   usage constraints in your words.  Shown back in every confirmation, never enforced by us.

  The settings page adds rows of its own, when the register does not name them: ``api`` (API token,
  FOR from "API token: for", USAGE from "API token: usage constraints"), ``ssh`` (SSH key, FOR ssh
  git), ``gw`` (the ghostwheel password).  A register row of the same NAME wins.

THE BINDER -- word balancing against secret.md (a C4 word file).  A name the file lists takes that
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

    python3 -m polygram.mcp.keys --bind NAME [--register FILE] [--lexicon FILE] [--tsv]
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets as _secrets
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEXICON = HERE / "secret.md"
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


def read_register(path: Path | None = None) -> tuple[dict[str, dict], list[dict]]:
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


# ---------------------------------------------------------------- the door
_SALT = _secrets.token_bytes(16)


def _code(key: str, argv: list[str], cwd: str) -> str:
    msg = "\x1f".join([key, cwd, *argv]).encode()
    return hmac.new(_SALT, msg, hashlib.sha256).hexdigest()[:10]


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
    args = argv[1:]
    if not args or any(a.startswith("-") for a in args):
        return ""
    for key, prog, target in (standing_entries() if entries is None else entries):
        if key != row["name"] or prog != program:
            continue
        if program == "ssh" and args[0] == target:
            return f"standing yes ({key} {prog} {target}, keys.standing)"
        if program == "scp" and len(args) >= 2 and args[-1].startswith(target + ":") \
                and not any(_remote(a) for a in args[:-1]):
            return f"standing yes ({key} {prog} {target}, keys.standing)"
        if program == "git" and len(args) == 1 and args[0] in GIT_STANDING and cwd \
                and _same_dir(cwd, target):
            return f"standing yes ({key} {prog} {target}, keys.standing)"
    return ""


def run(row: dict, argv: list[str], cwd: str, confirm: str, lex, timeout: float = RUN_TIMEOUT,
        stdin_row: dict | None = None) -> dict:
    program = os.path.basename(argv[0]) if argv else ""
    for suffix in (".exe", ".cmd", ".bat"):
        program = program.removesuffix(suffix)
    if not argv:
        return {"ok": False, "say": "nothing to run: argv is empty"}
    if program not in row["run_list"]:
        return {"ok": False, "say": f"the key {row['name']!r} may start {', '.join(row['run_list']) or 'nothing'}; "
                                   f"not {program}. Add it to the key's RUN to allow it."}
    value = value_of(row)
    if not value:
        return {"ok": False, "say": f"the key {row['name']!r} has no value where it says ({row['source']})."}
    cwd = str(Path(cwd or ".").expanduser().resolve())
    feed = ""
    if stdin_row is not None:
        feed = stdin_value(stdin_row)
        if not feed:
            return {"ok": False, "say": f"the key {stdin_row['name']!r} has no value where it says ({stdin_row['source']}), so there is nothing to hand {program}."}
    code = _code(row["name"] + ("<" + stdin_row["name"] if stdin_row else ""), argv, cwd)
    usage = row.get("usage") or "(no usage constraints written for this key)"
    present = (f"About to run {' '.join(argv)} in {cwd} with the key {row['name']!r} "
               f"({row['kind']}, for {row['for'] or 'unspecified'}) bound as "
               f"{', '.join(row['binds_list']) or 'its own'}. Its usage constraints, in your words: {usage}"
               + (f" It also hands the key {stdin_row['name']!r} to the program's input (its usage constraints: "
                  f"{stdin_row.get('usage') or 'none written'})." if stdin_row else ""))
    stand = standing_for(row, program, argv, cwd=cwd) if stdin_row is None else ""
    if stand and program == "git" and argv[1:] == ["pull"]:
        argv = [*argv, "--ff-only"]                  # a standing pull never makes a merge commit
    if confirm != code and not stand:
        return {"ok": None, "confirm": code, "present": present,
                "say": "Show the person this confirmation, with the usage constraints, and call key_run "
                       "again with confirm set to the code only if they agree."}
    add, extra = bound_env(row, value, program, lex)
    env = {**os.environ, **add}
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
    try:
        p = subprocess.run([argv[0], *extra, *argv[1:]], cwd=cwd, env=env, capture_output=True,
                           # always an input of our own: inherited, it would be the server's own
                           # protocol pipe, and a prompt could sit on it until the bridge gave up.
                           # Bytes, not text: in text mode Windows writes every \n as \r\n, and a
                           # key with \r\n endings is refused ("Load key: error in libcrypto");
                           # found 2026-10-14, cast 2, on the pen job's first run with the deploy key.
                           input=(feed if stdin_row is not None else "").encode("utf-8"),
                           timeout=timeout)
        out = p.stdout.decode("utf-8", errors="replace")
        err = p.stderr.decode("utf-8", errors="replace")
        rc = p.returncode
    except FileNotFoundError:
        return {"ok": False, "say": f"{argv[0]} is not on this computer's PATH."}
    except subprocess.TimeoutExpired:
        return {"ok": False, "say": f"{argv[0]} ran past {timeout:.0f} s and was stopped."}
    mask = f"[key {row['name']}]"
    secrets_seen = [value, feed, login_secret] + [v for k, v in add.items() if k.startswith("GIT_CONFIG_VALUE_")]
    for s in secrets_seen:
        for sp in spellings(s or ""):
            out, err = out.replace(sp, mask), err.replace(sp, mask)
    return {"ok": rc == 0, "exit": rc, "stdout": out[-20000:], "stderr": err[-8000:],
            "seconds": round(time.time() - t0, 2), "bound": sorted(add),
            "say": f"{program} exited {rc} after {time.time() - t0:.1f} s with {row['name']!r} bound "
                   f"as {', '.join(sorted(k for k in add if not k.startswith('GIT_CONFIG')))}"
                   + (f"; ran on a {stand}, no confirmation asked" if stand and confirm != code else ""),
            **({"standing": stand, "present": present} if stand and confirm != code else {})}


# ---------------------------------------------------------------- tools
def _public(r: dict) -> dict:
    return {"name": r["name"], "kind": r["kind"], "source": r["source"], "for": _split(r["for"]),
            "binds": r["binds_list"], "run": r["run_list"], "usage": r.get("usage") or "",
            "from": "settings page" if r.get("line") == "settings" else f"register line {r.get('line')}",
            "value": "set" if value_of(r) else "not set"}


def register(srv) -> None:
    @srv.tool("key_list",
              "The keys you keep (the key register plus the settings page's API token, SSH key and "
              "password): each one's kind, what it is for, the names it answers to, the programs it "
              "may start, its usage constraints, and whether its value is set. Never a value.")
    def _list(_args):
        rows, ignored = keys()
        pub = [_public(r) for r in rows.values()]
        say = "; ".join(f"{p['name']}: {p['kind']} for {' '.join(p['for']) or '(unspecified)'}, answers to "
                        f"{', '.join(p['binds']) or 'nothing listed'}, value {p['value']}"
                        + (f", usage: {p['usage']}" if p["usage"] else "") for p in pub) or "no keys kept"
        if ignored:
            say += f"; {len(ignored)} register line(s) ignored: " + ", ".join(
                f"line {i['line']} ({i['reason']})" for i in ignored[:3])
        return {"register": str(register_file()), "keys": pub, "ignored": ignored, "say": say}

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
              "(field:api_token, field:ssh_key, field:gw_password, env:NAME, file:PATH).",
              {"type": "object",
               "properties": {c: {"type": "string"} for c in COLS},
               "required": ["name", "kind"]})
    def _set(args):
        row = {c: (args.get(c) or "").replace("\t", " ").replace("\n", " ").strip() for c in COLS}
        why = problems_of(row)
        if why:
            return {"ok": False, "say": "not written: " + "; ".join(why)}
        p = register_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        new = not p.is_file()
        with p.open("a", encoding="utf-8") as fh:
            if new:
                fh.write("# keys register: " + "\t".join(c.upper() for c in COLS)
                         + "  (append-only; the last row for a NAME wins; KIND - removes)\n")
            fh.write("\t".join(row[c] for c in COLS) + "\n")
        return {"ok": True, "register": str(p),
                "say": f"{row['name']} {'removed' if row['kind'] == '-' else 'written'}; key_list reads it back."}

    @srv.tool("key_run",
              "Run one program (gh, git, glab, ssh, scp, npm, twine: whatever the key's RUN allows) with "
              "one key bound under the names it answers to. The first call returns a confirmation to "
              "show the person, with the key's usage constraints, and a code; call again with confirm "
              "set to that code to run. The key's value is never returned; output has it masked.",
              {"type": "object",
               "properties": {"key": {"type": "string", "description": "a key's name, or a name it answers to (GH_TOKEN)"},
                              "argv": {"type": "array", "items": {"type": "string"}},
                              "cwd": {"type": "string"},
                              "stdin_key": {"type": "string", "description": "a key whose value is handed to the program's input, never its arguments (gh secret set NAME reads it there)"},
                              "confirm": {"type": "string"}},
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
        return run(row, list(args.get("argv") or []), args.get("cwd") or "", args.get("confirm") or "", lex,
                   stdin_row=feed_row)


def _main(argv: list[str]) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python3 -m polygram.mcp.keys")
    ap.add_argument("--bind", action="append", default=[])
    ap.add_argument("--register")
    ap.add_argument("--lexicon")
    ap.add_argument("--tsv", action="store_true")
    a = ap.parse_args(argv)
    lex = lexicon(Path(a.lexicon) if a.lexicon else None)
    rows, _ = keys(Path(a.register) if a.register else None, lex=lex)
    for n in a.bind:
        b = bind(n, rows, lex)
        print(f"{n}\t{b['verdict']}\t{b['key'] or '-'}\t{b['score']}" if a.tsv else b["say"])
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
