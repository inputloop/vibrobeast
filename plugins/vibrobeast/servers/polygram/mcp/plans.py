# polygram -- gated agent-skill synthesis.
# Copyright 2026 INPUTLOOP; GPL-3.0-or-later; https://github.com/inputloop.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""plans -- the plan door: one yes for a written plan, then its steps run with no code each.

His words, 2026-11-04 17:19 CST: "... now with writing plan as a script so you can ask for approvals once.
Let's get that fixed."  Before this, key_run asked one code per run, so a plan of three steps on his own
host was three codes (and, on two of his hosts that day, a dialog for every two or three of them).

A PLAN is a text file: a short header, then prose, numbered steps, and one command per step.  The shape is
below (PLAN-FORMAT.md, which came with this change, says it at length with a worked example); the reader here
is the one this server trusts, and plan-check.sh (sh and awk) is the second reader, held to the same output
byte for byte.

    plan: hop-forward-inner           (an id: lower-case letters, digits, -)
    purpose: words
    key: ssh                          (the key every step runs with)
    hosts: hop.example.org            (every host a step may reach; documentation names here)
    logins: hop                       (every login a step may use)
    hours: 9                          (optional, at most PLAN_HOURS)
    runs: 17                          (optional, at most PLAN_RUNS)

    Prose.  step 1: what it does
    sends: <sha256>  <path>           (one per local file an scp step sends)
    $ scp FILES hop@hop.example.org:/tmp/

ITS IDENTITY is the sha256 of the plan file.  Every file the plan sends is named in it with its own sha256,
so the one hash covers them too, and the door hashes each file again at approval and before each run.

THE DOOR, as key_run argv words (the key named in key_run's own key field):
  plan_approve PLANFILE   reads the plan; any problem refuses at once, with no code.  Else it returns the
                          whole plan in words and a code (keys.CODES: random, one use, 15 minutes).  Called
                          again with that code, it writes the approval: a copy of the plan as approved
                          (plan-yes/SHA12.plan) and its atom (plan-yes/SHA12.kv), and an APPROVED line in
                          the journal.  The approval itself is one confirmation code the person sees: the
                          2026-10-19 audit's rule for keeper-only writes, kept.
  plan_revoke ID          ends approvals of a plan (its id, its sha256's first 12, or the approval's id).
                          No code: it only narrows.
  plan_list               the approvals in force, in words.

A STEP RUNS WITH NO CODE when key_run's argv is exactly a step of an approved plan's copy, with the same key,
from the plan's folder, before the approval's expiry, under its run budget, not revoked, keys.plans on (it
ships off; only the keeper's own turn, with a code, turns it on, and no defaults file may), no
group ORG.md saying "must not" for a standing yes there, and every file that step sends hashing as written.
Anything else falls back to the code door, and the confirmation says why.  Each covered run is a RAN line in
the journal (plan-yes.log beside push-yes.log): utc, event, plan, sha12, approval, step, exit, key, target,
folder, note.  The run budget is counted from those lines, so the journal is load-bearing: when it cannot be
written, the step asks for a code instead.

Narrow on purpose, like keys.standing: ssh and scp take only the options in SAFE_OPTS (they cannot start a
program on this computer), ssh -J only when keys.py has the -J hop (jump_rewrite), scp only sends, git only
fetch or pull alone (a push stays the push door's).  scp sends into a folder (its path ends in /), so a file
keeps its name there.  A plan's ssh step whose remote command names a file an earlier step sent to that same
login@host must also carry that file's sha256 in the command (the seam between "sent"
and "used": the far copy is outside our sight, so the command checks it there).  "Names" is plain text: the
file's name appears in the command.  A file used without being named (a script that reads another) is not
seen by the rule; the approval words list every such file per step, so the reader can judge it.

    python3 -m polygram.mcp.plans --read PLANFILE [--jump]     (the line form plan-check.sh prints)
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets as _secrets
import time
from pathlib import Path

#: How long an approval lasts and how many runs it covers, at most.  Both are invented numbers, from the
#: house set (4, 9, 17); a plan may ask for fewer in its header, never more.
PLAN_HOURS = 9
PLAN_RUNS = 17
WORDS = ("plan_approve", "plan_revoke", "plan_list")
PROGRAMS = ("ssh", "scp", "git")
GIT_ALONE = ("fetch", "pull")
FIELDS = ("plan", "purpose", "key", "hosts", "logins", "hours", "runs")
REQUIRED = ("plan", "purpose", "key", "hosts", "logins")
#: ssh/scp options a plan step may carry: none of them starts a program on this computer or writes a file
#: here (ProxyCommand, LocalCommand, -F, -E, -L/-R/-D and the rest are refused).  name (lower case) -> value.
SAFE_OPTS = {"stricthostkeychecking": r"yes", "userknownhostsfile": r"[A-Za-z0-9_./:+-]+",
             "hostkeyalias": r"[A-Za-z0-9_.-]+", "connecttimeout": r"[0-9]{1,4}", "batchmode": r"yes",
             "serveraliveinterval": r"[0-9]{1,4}", "serveralivecountmax": r"[0-9]{1,4}"}
_PLAIN = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./:@%+=,-")
_PATH_PART = re.compile(r"^[A-Za-z0-9_.+=,-]+$")
_wall = time.time               # the clock approvals are read by; a test moves it


# ---------------------------------------------------------------- where things are kept
def state_dir() -> Path:
    raw = os.environ.get("PLAN_YES_DIR", "").strip()
    return Path(raw).expanduser() if raw else Path.home() / ".mentcached" / "plan-yes"


def log_file() -> Path:
    raw = os.environ.get("PLAN_YES_LOG", "").strip()
    return Path(raw).expanduser() if raw else Path.home() / ".mentcached" / "plan-yes.log"


def _u(s: str) -> str:
    """A plan's text is read byte for byte (latin-1), as the awk reader reads it; this is the same text as
    the person wrote it (UTF-8), for words and for comparing with key_run's argv."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except UnicodeDecodeError:
        return s.encode("latin-1").decode("utf-8", "replace")


def _ws(s: str) -> str:
    # spaces and tabs only: str.strip() would also take \x85 and \xa0, which are bytes inside UTF-8 letters here
    return re.sub(r"[ \t]+", " ", s).strip(" \t")


def sha256_file(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------- the reader
def split_words(s: str) -> list[str] | None:
    """A command line's words, as sh would read them, for the little sh a plan allows: plain characters
    (_PLAIN), '...' (nothing inside is special; no tab), and \\' (a single quote).  None for anything else."""
    out: list[str] = []
    cur: str | None = None
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t":
            if cur is not None:
                out.append(cur)
                cur = None
            i += 1
        elif c == "'":
            j = s.find("'", i + 1)
            if j < 0 or "\t" in s[i + 1:j]:
                return None
            cur = (cur or "") + s[i + 1:j]
            i = j + 1
        elif c == "\\" and i + 1 < n and s[i + 1] == "'":
            cur = (cur or "") + "'"
            i += 2
        elif c in _PLAIN:
            cur = (cur or "") + c
            i += 1
        else:
            return None
    if cur is not None:
        out.append(cur)
    return out


def local_path_ok(p: str) -> bool:
    parts = p.split("/")
    return bool(p) and all(x and x not in (".", "..") and _PATH_PART.match(x) for x in parts)


_TARGET = re.compile(r"^([^@:/]+)@([^@:/]+)$")
_DEST = re.compile(r"^([^@:/]+)@([^@:/]+):(.*)$")


def _opts(argv: list[str], program: str, jump: bool):
    """(the options, the rest, a problem sentence and detail, the -J hop)."""
    i, opts, hop = 1, [], ""
    while i < len(argv) and argv[i].startswith("-"):
        o = argv[i]
        v = argv[i + 1] if i + 1 < len(argv) else None
        ok = False
        if v is not None:
            if (program == "ssh" and o == "-p") or (program == "scp" and o == "-P"):
                ok = bool(re.fullmatch(r"[0-9]{1,5}", v))
            elif o == "-o":
                name, eq, val = v.partition("=")
                ok = bool(eq) and name.lower() in SAFE_OPTS and bool(re.fullmatch(SAFE_OPTS[name.lower()], val))
            elif o == "-J" and program == "ssh" and jump and not hop:
                ok = True
                hop = v
        if not ok:
            return opts, argv[i:], ("this option is not read in a plan", o), hop
        opts += [o, v]
        i += 2
    return opts, argv[i:], None, hop


def read_bytes(data: bytes, folder: Path, jump: bool = False, hash_files: bool = True) -> dict:
    """Read a plan.  -> {sha256, header, hours, runs, steps, problems}.  Problems are (step, sentence,
    detail) with step a number or "-".  The words are fixed sentences, the same in plan-check.awk."""
    sha = hashlib.sha256(data).hexdigest()
    text = data.decode("latin-1")
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]
    if lines and lines[-1] == "" and text.endswith("\n"):
        lines.pop()
    probs: list[tuple] = []
    head: dict[str, str] = {}
    i = 0
    while i < len(lines) and not re.fullmatch(r"[ \t]*", lines[i]):
        ln = lines[i]
        i += 1
        if ln.startswith("#"):
            continue
        m = re.fullmatch(r"([a-z]+):[ \t]*(.*)", ln)
        if not m:
            probs.append(("-", "a header line is field: value", f"line {i}"))
        elif m.group(1) not in FIELDS:
            probs.append(("-", "unknown header field", m.group(1)))
        elif m.group(1) in head:
            probs.append(("-", "a header field is given twice", m.group(1)))
        else:
            head[m.group(1)] = _ws(m.group(2))
    for f in REQUIRED:
        if not head.get(f):
            probs.append(("-", "a header field is missing", f))
    if head.get("plan") and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", head["plan"]):
        probs.append(("-", "the plan id is lower-case letters, digits and -", "-"))
    if head.get("key") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", head["key"]):
        probs.append(("-", "the key is a key's name", "-"))
    hosts = [h for h in re.split(r"[ ,]+", head.get("hosts", "")) if h]
    logins = [x for x in re.split(r"[ ,]+", head.get("logins", "")) if x]
    for h in hosts:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", h):
            probs.append(("-", "a host is a plain host name or address", h))
    for x in logins:
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*", x):
            probs.append(("-", "a login is a plain user name", x))
    granted = {}
    for f, cap in (("hours", PLAN_HOURS), ("runs", PLAN_RUNS)):
        v = head.get(f, "")
        if not v:
            granted[f] = str(cap)
        elif re.fullmatch(r"[0-9]+", v) and int(v) >= 1:
            granted[f] = str(min(int(v), cap))
        else:
            granted[f] = "-"
            probs.append(("-", f"{f} is a whole number, 1 or more", "-"))
    # the body
    steps: list[dict] = []
    while i < len(lines):
        ln = lines[i]
        i += 1
        m = re.fullmatch(r"step ([0-9]+):[ \t]*(.*)", ln)
        if m:
            k = len(steps) + 1
            if m.group(1) != str(k):
                probs.append(("-", "steps are numbered 1, 2, 3 in order", f"line {i}"))
            st = {"n": k, "heading": _ws(m.group(2)), "cmd": None, "sends": [], "argv": None}
            if not st["heading"]:
                probs.append((k, "a step needs words saying what it does", "-"))
            steps.append(st)
            continue
        if ln.startswith("sends:"):
            m = re.fullmatch(r"sends:[ \t]+([0-9a-f]{64})[ \t]+(.*[^ \t])[ \t]*", ln)
            if not steps:
                probs.append(("-", "a sends line comes before any step", f"line {i}"))
            elif not m:
                probs.append((steps[-1]["n"], "a sends line is a sha256 then a path", f"line {i}"))
            else:
                steps[-1]["sends"].append([m.group(1), m.group(2), ""])
            continue
        if ln.startswith("$ "):
            if not steps:
                probs.append(("-", "a command comes before any step", f"line {i}"))
            elif steps[-1]["cmd"] is not None:
                probs.append((steps[-1]["n"], "a step has one command", f"line {i}"))
            else:
                steps[-1]["cmd"] = ln[2:]
            continue
    if not steps:
        probs.append(("-", "a plan needs at least one step", "-"))
    sent: dict[str, list] = {}
    for st in steps:
        k = st["n"]
        if st["cmd"] is None:
            probs.append((k, "a step has no command", "-"))
            continue
        argv = split_words(st["cmd"])
        if argv is None:
            probs.append((k, "a command uses quoting a plan does not read", "-"))
            continue
        if not argv:
            probs.append((k, "a step has no command", "-"))
            continue
        st["argv"] = argv
        prog = argv[0]
        st["program"] = prog
        sources: list[str] = []
        if prog not in PROGRAMS:
            probs.append((k, "a plan runs ssh, scp or git", prog))
        elif prog == "git":
            if not (argv[1:] in ([g] for g in GIT_ALONE) or argv[1:2] == ["push"]):
                probs.append((k, "git in a plan is fetch or pull alone, or a push", "-"))
            st["target"] = "."
        else:
            opts, rest, bad, hop = _opts(argv, prog, jump)
            st["opts"], st["hop"] = opts, hop
            if bad:
                probs.append((k, *bad))
            elif any(a.startswith("-") for a in rest):
                probs.append((k, "this option is not read in a plan", next(a for a in rest if a.startswith("-"))))
            elif prog == "ssh":
                m = _TARGET.match(rest[0]) if len(rest) == 2 else None
                if not m:
                    probs.append((k, "ssh in a plan is ssh login@host and one command", "-"))
                else:
                    st["target"], st["remote"] = rest[0], rest[1]
                    pairs = [(m.group(1), m.group(2))]
                    if hop:
                        mh = _TARGET.match(hop)
                        if not mh:
                            probs.append((k, "ssh in a plan is ssh login@host and one command", "-"))
                        else:
                            pairs.append((mh.group(1), mh.group(2)))
                    for lg, h in pairs:
                        if lg not in logins:
                            probs.append((k, "the login is not one the plan names", lg))
                        if h not in hosts:
                            probs.append((k, "the host is not one the plan names", h))
                    for path, fsha in sent.get(rest[0], []):
                        if path.rsplit("/", 1)[-1] in rest[1] and fsha not in rest[1]:
                            probs.append((k, "this command names a file sent here earlier but not its sha256", path))
            else:  # scp
                m = _DEST.match(rest[-1]) if len(rest) >= 2 else None
                if not m:
                    probs.append((k, "scp in a plan sends local files to login@host:path", "-"))
                else:
                    st["target"], st["dest"] = f"{m.group(1)}@{m.group(2)}", m.group(3)
                    if m.group(3) and not m.group(3).endswith("/"):
                        probs.append((k, "scp in a plan sends into a folder: end the path with /", m.group(3)))
                    if m.group(1) not in logins:
                        probs.append((k, "the login is not one the plan names", m.group(1)))
                    if m.group(2) not in hosts:
                        probs.append((k, "the host is not one the plan names", m.group(2)))
                    sources = rest[:-1]
                    named = [s[1] for s in st["sends"]]
                    for src in sources:
                        if not local_path_ok(src):
                            probs.append((k, "a sent file is a plain path inside the plan's folder", src))
                        elif src not in named:
                            probs.append((k, "a sent file needs a sends line", src))
        for s in st["sends"]:
            if s[1] not in sources:
                probs.append((k, "a sends line names a file this step does not send", s[1]))
            if not local_path_ok(s[1]):
                s[2] = "unread"
            elif hash_files:
                got = sha256_file(folder / s[1])
                s[2] = "missing" if not got else ("ok" if got == s[0] else "changed")
                if s[2] == "missing":
                    probs.append((k, "a sent file is missing", s[1]))
                elif s[2] == "changed":
                    probs.append((k, "a sent file has changed since the plan was written", s[1]))
            else:
                s[2] = "unhashed"
            if s[1] in sources and local_path_ok(s[1]) and st.get("target"):
                sent.setdefault(st["target"], []).append((s[1], s[0]))
    return {"sha256": sha, "header": head, "hosts": hosts, "logins": logins, "hours": granted["hours"],
            "runs": granted["runs"], "steps": steps, "problems": probs, "jump": jump}


def read(path: Path, jump: bool = False, hash_files: bool = True) -> dict:
    p = Path(path)
    r = read_bytes(p.read_bytes(), p.resolve().parent, jump, hash_files)
    r["folder"] = str(p.resolve().parent)
    return r


def lines(r: dict) -> list[str]:
    """The reader's answer as lines, the shape plan-check.sh prints (latin-1 text: the plan's own bytes)."""
    out = [f"plan-sha256\t{r['sha256']}"]
    h = r["header"]
    for f in FIELDS:
        v = (" ".join(r["hosts"]) if f == "hosts" else " ".join(r["logins"]) if f == "logins"
             else r[f] if f in ("hours", "runs") else h.get(f, ""))
        out.append(f"header\t{f}\t{v}")
    for st in r["steps"]:
        out.append(f"step\t{st['n']}\t{st['heading']}")
        for j, w in enumerate(st["argv"] or []):
            out.append(f"word\t{st['n']}\t{j}\t{w}")
        for s in st["sends"]:
            out.append(f"sends\t{st['n']}\t{s[0]}\t{s[1]}\t{s[2]}")
    out += sorted(f"problem\t{a}\t{b}\t{c}" for a, b, c in r["problems"])
    return out


# ---------------------------------------------------------------- words for the person
def _reading(st: dict, r: dict) -> str:
    """What a step changes, as the door reads it (beside the author's own heading)."""
    argv = [_u(w) for w in st["argv"]]
    prog = argv[0]
    opts = st.get("opts") or []
    o = (" (ssh options: " + " ".join(_u(x) for x in opts) + ")") if opts else ""
    if prog == "scp":
        files = ", ".join(f"{_u(s[1])} (sha256 {s[0][:12]})" for s in st["sends"])
        return (f"copies {len(st['sends'])} file(s) to {_u(st['target'])}:{_u(st['dest'])}, replacing any files "
                f"of the same names there: {files}{o}")
    if prog == "ssh":
        checks = [p for p, fs in _sent_before(r, st) if fs in st["remote"]]
        return (f"runs, as {_u(st['target'].split('@')[0])} on {_u(st['target'].split('@')[1])}"
                + (f" (through {_u(st['hop'])})" if st.get("hop") else "")
                + f": {_u(st['remote'])}{o}"
                + (f"; the command checks by sha256 {', '.join(_u(c) for c in checks)} before using them" if checks else ""))
    if argv[1:2] == ["push"]:
        return ("a push: decided by the push door when it runs, as every push is (fr1me egress); this plan "
                "neither opens nor shuts it")
    return f"git {argv[1]} in the plan's folder" + (" (fast-forward only)" if argv[1] == "pull" else "")


def _sent_before(r: dict, step: dict):
    out = []
    for st in r["steps"]:
        if st is step:
            break
        if st.get("program") == "scp" and st.get("target") == step.get("target"):
            out += [(s[1], s[0]) for s in st["sends"]]
    return out


def _unchecked(r: dict) -> list[str]:
    """Files sent to a login@host that no later ssh step there checks by sha256: a script that uses one without
    naming it is not seen by the seam rule, so the person is told which copies nothing checks."""
    out = []
    for st in r["steps"]:
        if st.get("program") != "scp":
            continue
        later = [x for x in r["steps"] if x["n"] > st["n"] and x.get("program") == "ssh"
                 and x.get("target") == st.get("target")]
        out += [f"{_u(s[1])} (to {_u(st['target'])})" for s in st["sends"]
                if not any(s[0] in x.get("remote", "") for x in later)]
    return out


def words(r: dict, row: dict) -> str:
    h = r["header"]
    hours, runs = int(r["hours"]), int(r["runs"])
    house = "the door's most, an invented number from the house set 4, 9, 17"
    asked = (f"{hours} hours, " + ("as the plan asks" if h.get("hours") and int(h["hours"]) <= PLAN_HOURS else house)
             + f"; {runs} runs, " + ("as the plan asks" if h.get("runs") and int(h["runs"]) <= PLAN_RUNS else house))
    until = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(_wall() + hours * 3600))
    steps = " ".join(f"Step {st['n']}: {_u(st['heading'])}. The door reads it as: {_reading(st, r)}."
                     for st in r["steps"])
    nochk = _unchecked(r)
    steps += (f" No later step checks these copies on the far side by sha256: {', '.join(nochk)}." if nochk else
              (" A later step checks every sent file by sha256 on the far side."
               if any(st.get("program") == "scp" for st in r["steps"]) else ""))
    return (f"Plan {_u(h['plan'])}: {_u(h['purpose'])}. Its sha256 is {r['sha256']}. Every step runs with the key "
            f"{row['name']!r} ({row['kind']}, for {row.get('for') or 'unspecified'}); its usage constraints, in your "
            f"words: {row.get('usage') or '(none written for this key)'}. From the folder {r['folder']}, on "
            f"{', '.join(_u(x) for x in r['hosts'])} as {', '.join(_u(x) for x in r['logins'])}. {steps} "
            f"If you approve, these {len(r['steps'])} step(s) run exactly as written, from that folder, with no code "
            f"each, until {until} or {runs} runs, whichever comes first ({asked}). A changed file, "
            f"any other command, host, folder or key asks for a code as before. To end it early: key_run plan_revoke "
            f"{_u(h['plan'])}.")


# ---------------------------------------------------------------- approvals and the journal
def _stamp(t: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_wall() if t is None else t))


def journal(row: list[str]) -> str:
    """One line of the plan-yes journal; the log's path, or why it was not written."""
    clean = [str(f).replace("\t", " ").replace("\n", " ").replace("\r", " ") for f in row]
    p = log_file()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(clean) + "\n")
    except OSError as e:
        return f"not written ({e.__class__.__name__})"
    return str(p)


def _journal_rows() -> list[list[str]]:
    try:
        text = log_file().read_text(encoding="utf-8")
    except OSError:
        return []
    return [ln.split("\t") for ln in text.splitlines() if ln and not ln.startswith("#")]


def _writable() -> bool:
    p = log_file()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8"):
            pass
        return True
    except OSError:
        return False


def _atom(path: Path) -> dict:
    out = {}
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            f, sep, v = ln.partition(":")
            if sep and not ln.startswith("#"):
                out[f.strip()] = v.strip()
    except OSError:
        pass
    return out


def _write_atom(path: Path, a: dict) -> None:
    text = "".join(f"{k}: {str(v).replace(chr(10), ' ')}\n" for k, v in a.items())
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def approvals() -> list[dict]:
    d = state_dir()
    if not d.is_dir():
        return []
    out = [dict(_atom(f), _file=str(f)) for f in sorted(d.glob("*.kv"))]
    return sorted((a for a in out if a.get("sha256")), key=lambda a: a.get("approved_at", ""), reverse=True)


def _used(a: dict, rows: list[list[str]]) -> int:
    return sum(1 for r in rows if len(r) > 4 and r[1] == "RAN" and r[4] == a.get("approval"))


def _revoked(a: dict, rows: list[list[str]]) -> str:
    if a.get("revoked"):
        return a["revoked"]
    for r in rows:
        if len(r) > 4 and r[1] == "REVOKED" and r[4] == a.get("approval"):
            return f"{r[0]} (a REVOKED line in the journal)"
    return ""


def _live(a: dict, rows) -> str:
    """"" when the approval is in force, else why not."""
    why = _revoked(a, rows)
    if why:
        return f"revoked {why}"
    if _wall() >= float(a.get("expires_s") or 0):
        return f"expired at {a.get('expires_at')}"
    if _used(a, rows) >= int(a.get("runs") or 0):
        return f"its {a.get('runs')} runs are used"
    return ""


#: Said wherever the door is found shut, so the words carry the way to open it.
OFF_SAID = ("the plan door is off: either the keeper set keys.plans off (pref_set keys.plans on, on his own turn, "
            "with the code pref_set shows, opens it again), or keys.plans is unset and the settings page's Habit row "
            "(Extra Checks for potentially unsafe things) is off, in which case key_run asks no code for a plan to cover")


def switch_on() -> bool:
    """keys.plans: the keeper's word when he has set it (on or off); unset, it follows the settings page's Habit row,
    which ships on (habit.py; his 2026-11-04 ruling: the habit "preplans complex sequences as scripted actions where
    possible ... default it on").  Every plan is still approved with a code the person sees, so the door being open
    approves nothing by itself (the LENS on approval layers, E2, as he narrowed it).  A value that is neither on
    nor off, or prefs that cannot be read, is off."""
    try:
        from . import prefs
        row = prefs.current().get("keys.plans") or {}
        v = (row.get("value") or "").strip().lower()
    except Exception:                                   # noqa: BLE001 -- no prefs: shut
        return False
    if v in ("", prefs.UNSET):
        from . import habit
        return habit.on()
    return v in ("on", "1", "true", "yes")


def _jump() -> bool:
    from . import keys
    return hasattr(keys, "jump_rewrite")


def _frozen(a: dict) -> dict | None:
    """The plan as approved, read again from the copy kept beside its atom (never the live file)."""
    p = state_dir() / (a["sha256"][:12] + ".plan")
    try:
        data = p.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(data).hexdigest() != a["sha256"]:
        return None
    r = read_bytes(data, Path(a.get("folder") or "."), _jump(), hash_files=False)
    r["folder"] = a.get("folder") or ""
    return r


def match(row: dict, program: str, argv: list[str], cwd: str):
    """(a plan reference when an approved plan covers this exact run, else None; why not, in words, or "")."""
    from . import keys
    rows = _journal_rows()
    mine = [a for a in approvals() if a.get("key") == row["name"] and not _live(a, rows)]
    whys: list[str] = []
    hit_any = False
    for a in approvals():
        r = _frozen(a)
        if r is None:
            if a.get("key") == row["name"]:
                whys.append(f"the copy of plan {a.get('plan')} kept at approval is missing or changed")
            continue
        steps = [st for st in r["steps"] if st["argv"] is not None and [_u(w) for w in st["argv"]] == list(argv)]
        if not steps:
            continue
        hit_any = True
        st = steps[0]
        name = f"plan {a.get('plan')} step {st['n']}"
        if a.get("key") != row["name"]:
            whys.append(f"{name} runs with the key {a.get('key')!r}, not {row['name']!r}")
            continue
        if not keys._same_dir(cwd, a.get("folder") or ""):
            whys.append(f"{name} runs from {a.get('folder')}, not {cwd}")
            continue
        why = _live(a, rows)
        if why:
            whys.append(f"{name}: the approval is {why}")
            continue
        if r["problems"]:
            whys.append(f"{name}: the plan no longer reads cleanly ({r['problems'][0][1]})")
            continue
        if not switch_on():
            whys.append(f"{name}: {OFF_SAID}")
            continue
        bad = []
        for fsha, path, _s in st["sends"]:
            got = sha256_file(Path(a["folder"]) / _u(path))
            if got != fsha:
                bad.append(f"{_u(path)} " + ("is missing" if not got else
                                             f"has changed since the plan was approved (sha256 now {got[:12]}, "
                                             f"approved {fsha[:12]})"))
        if bad:
            whys.append(f"{name}: " + "; ".join(bad))
            continue
        target = _u(st.get("target") or ".")
        lim = None
        try:
            from . import orglimits
            lim = orglimits.standing(program, target if program != "git" else cwd, None, cwd)
        except Exception:                               # noqa: BLE001 -- no orglimits: no group limit
            lim = None
        org = ""
        if lim is not None:
            from . import orglimits
            org = orglimits.say(lim)
            if lim["strength"] == "must not":
                whys.append(f"{name}: {org}")
                continue
        if not _writable():
            whys.append(f"{name}: the plan-yes journal ({log_file()}) cannot be written, and it counts the runs")
            continue
        used = _used(a, rows) + 1
        ref = {"plan": a.get("plan"), "sha12": a["sha256"][:12], "approval": a.get("approval"), "step": st["n"],
               "key": row["name"], "target": target, "folder": a.get("folder"),
               "stand": (f"plan yes ({a.get('plan')} step {st['n']} of {len(r['steps'])}, sha256 {a['sha256'][:12]}, "
                         f"run {used} of {a.get('runs')}, until {a.get('expires_at')}; journal {log_file()})"
                         + (f". {org}" if org else ""))}
        return ref, ""
    if not mine and not whys:
        return None, ""
    if not hit_any:
        hosts = sorted({h for a in mine for h in (a.get("hosts") or "").split()})
        tgt = next((w for w in argv[1:] if "@" in w and not w.startswith("-")), "")
        host = tgt.split("@", 1)[-1].split(":", 1)[0] if tgt else ""
        names = ", ".join(sorted({a.get("plan", "") for a in mine}))
        if host and host not in hosts:
            whys.append(f"no approved plan for the key {row['name']!r} reaches {host} (plans in force: {names}; "
                        f"their hosts: {' '.join(hosts) or 'none'})")
        else:
            whys.append(f"this command is not a step of an approved plan for the key {row['name']!r} "
                        f"(plans in force: {names})")
    why = "Not run on a plan: " + "; ".join(whys) + "."
    journal([_stamp(), "NOT COVERED", "-", "-", "-", "-", "-", row["name"], " ".join(argv[:2]), cwd, why])
    return None, why


def ran(ref: dict, rc) -> str:
    return journal([_stamp(), "RAN", ref["plan"], ref["sha12"], ref["approval"], ref["step"], rc, ref["key"],
                    ref["target"], ref["folder"], ""])


# ---------------------------------------------------------------- the door's words in key_run
def door(row: dict, argv: list[str], cwd: str, confirm: str, lex=None) -> dict:
    word = argv[0]
    if word == "plan_list":
        return plan_list(row)
    if word == "plan_revoke":
        return revoke(row, argv[1] if len(argv) > 1 else "")
    return approve(row, argv[1] if len(argv) > 1 else "", cwd, confirm)


def approve(row: dict, plan_path: str, cwd: str, confirm: str) -> dict:
    from . import keys
    if not plan_path:
        return {"ok": False, "say": "plan_approve takes the plan file: argv [\"plan_approve\", \"PLANFILE\"]"}
    base = Path(cwd or ".").expanduser()
    p = Path(plan_path).expanduser()
    p = (p if p.is_absolute() else base / p).resolve()
    if not p.is_file():
        return {"ok": False, "say": f"no plan file at {p}"}
    r = read(p, _jump())
    if r["problems"]:
        return {"ok": False, "problems": [list(x) for x in r["problems"]],
                "say": "not approved, and no code asked: the plan does not read cleanly: "
                       + "; ".join(f"{'step ' + str(a) if a != '-' else 'header'}: {b}"
                                   + (f" ({_u(c)})" if c != "-" else "") for a, b, c in r["problems"]) + "."}
    h = r["header"]
    if h["key"] != row["name"]:
        return {"ok": False, "say": f"the plan names the key {h['key']!r}; this call used {row['name']!r}. "
                                    "Call key_run with the plan's key."}
    progs = sorted({st["argv"][0] for st in r["steps"]} - set(row["run_list"]))
    if progs:
        return {"ok": False, "say": f"the key {row['name']!r} may start {', '.join(row['run_list']) or 'nothing'}; "
                                    f"the plan also runs {', '.join(progs)}."}
    if not switch_on():
        return {"ok": False, "say": f"not approved, and no code asked: {OFF_SAID}. Until then each step asks for "
                                    "its own code."}
    fp = keys._code("plan_approve|" + row["name"], [r["sha256"]], r["folder"])
    took = keys.CODES.take(confirm, fp)
    if took in keys.REFUSED:
        return {"ok": False, "refused": took, "say": keys.REFUSED[took]}
    if took != "ok":
        return {"ok": None, "confirm": keys.CODES.issue(fp), "present": words(r, row),
                "say": "Nothing is approved yet. Show the person this plan in words, and call key_run again with the "
                       "same key and argv and confirm set to the code only if they agree. The code is good for one "
                       f"approval, within {int(keys.CONFIRM_TTL // 60)} minutes."}
    d = state_dir()
    d.mkdir(parents=True, exist_ok=True)
    sha12 = r["sha256"][:12]
    (d / (sha12 + ".plan")).write_bytes(p.read_bytes())
    now = _wall()
    try:
        from . import prefs
        who = prefs.keeper()
    except Exception:                                   # noqa: BLE001
        who = "the keeper"
    a = {"plan": h["plan"], "sha256": r["sha256"], "approval": _secrets.token_hex(6), "key": row["name"],
         "folder": r["folder"], "source": str(p), "hosts": " ".join(r["hosts"]), "logins": " ".join(r["logins"]),
         "steps": len(r["steps"]), "runs": r["runs"], "hours": r["hours"], "approved_at": _stamp(now),
         "expires_at": _stamp(now + int(r["hours"]) * 3600), "expires_s": int(now + int(r["hours"]) * 3600),
         "approved_by": f"{who} (the yes is the code shown with this plan's words)", "revoked": ""}
    _write_atom(d / (sha12 + ".kv"), a)
    logged = journal([a["approved_at"], "APPROVED", a["plan"], sha12, a["approval"], "-", "-", a["key"],
                      a["hosts"], a["folder"], f"{a['steps']} steps, {a['runs']} runs, until {a['expires_at']}"])
    return {"ok": True, "plan": a["plan"], "sha256": r["sha256"], "approval": a["approval"],
            "expires": a["expires_at"], "runs": int(a["runs"]), "journal": logged,
            "say": f"plan {a['plan']} approved: its {a['steps']} step(s) run with no code, exactly as written, from "
                   f"{a['folder']}, until {a['expires_at']} or {a['runs']} runs. key_run plan_revoke {a['plan']} ends it."}


def revoke(row: dict, which: str) -> dict:
    rows = _journal_rows()
    hit = [a for a in approvals() if which and which in (a.get("plan"), a["sha256"][:12], a.get("approval"))
           and not _revoked(a, rows)]
    if not hit:
        return {"ok": False, "say": f"no approval in force matches {which!r} (a plan id, the first 12 of its sha256, "
                                    "or an approval id; plan_list names them)"}
    for a in hit:
        a2 = {k: v for k, v in a.items() if k != "_file"}
        a2["revoked"] = f"{_stamp()} by key_run plan_revoke"
        _write_atom(Path(a["_file"]), a2)
        journal([_stamp(), "REVOKED", a.get("plan"), a["sha256"][:12], a.get("approval"), "-", "-", a.get("key"),
                 a.get("hosts"), a.get("folder"), "key_run plan_revoke"])
    return {"ok": True, "say": f"revoked {len(hit)} approval(s) of {', '.join(sorted({a.get('plan', '') for a in hit}))}; "
                               "their steps ask for a code again."}


def plan_list(row: dict) -> dict:
    rows = _journal_rows()
    out = []
    for a in approvals():
        why = _live(a, rows)
        out.append({"plan": a.get("plan"), "sha12": a["sha256"][:12], "approval": a.get("approval"),
                    "key": a.get("key"), "folder": a.get("folder"), "hosts": a.get("hosts"),
                    "used": _used(a, rows), "runs": a.get("runs"), "expires": a.get("expires_at"),
                    "in_force": not why, "why_not": why})
    live = [x for x in out if x["in_force"]]
    return {"ok": True, "approvals": out,
            "say": ("; ".join(f"{x['plan']} (key {x['key']}, {x['used']} of {x['runs']} runs, until {x['expires']})"
                              for x in live) or "no plan approval is in force")
                   + (f"; {len(out) - len(live)} more ended (revoked, expired or used)" if len(out) > len(live) else "")}


def _main(argv: list[str]) -> int:
    if not argv or argv[0] != "--read" or len(argv) < 2:
        print("usage: python3 -m polygram.mcp.plans --read PLANFILE [--jump]")
        return 2
    import sys
    r = read(Path(argv[1]), jump="--jump" in argv[2:])
    sys.stdout.buffer.write(("\n".join(lines(r)) + "\n").encode("latin-1"))
    return 1 if r["problems"] else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
