# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""pushyes -- the yes for a git push is decided here, by a tool, never by the model.

His words, 2026-10-22 23:38 CDT, after a fork confirmed two push codes itself: "I really don't want to
see the push codes so much as I want to avoid using claude logic to work with them and use tool
wherever we can".  So key_run sends every ``git push`` here and never issues a code for one.

The shape allowed: ``git push REMOTE REFSPEC`` and nothing else.  REMOTE is a configured remote's
name (its push URL is read from git) or a URL of a known shape (ssh://, git@host:, user@host:,
https://); a remote set to mirror is refused.  REFSPEC is one ``SRC`` or ``SRC:DST``: no ``+`` (a
force), no empty SRC (a delete), no ``*``.  Any argument starting with ``-`` was refused before this.

The check is c4 ``bin/fr1me egress``, read twice: here in Python (the first reader), and fr1me itself
(sh, the second) whenever sh and C4 are found.  GO only when every reader that ran says GO; when they
differ the push is refused and both answers are logged.  Every decision is a row of
``~/.mentcached/push-yes.log`` (PUSH_YES_LOG names another): utc, folder, remote, place (no
user:password@), refspec, verdict, reasons, range.  The result carries the same facts as
``push_yes``; how they are said in chat is the voicer's (c4 h/MODEL-2026-10-23-voicer-aspects.md).

FR1ME_VISIBILITY=public|private skips the anonymous read in both readers, as in fr1me: for tests.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

VERDICTS = ("GO", "STOP", "NOT CHECKED", "REFUSED")
_URL_OK = re.compile(r"^(ssh://[^\s/@]+@[^\s/]+/\S+|https://[^\s/]+/\S+|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:\S+)$")
_PRIVATE_HINT = re.compile(r"Username|Authentication|could not read|terminal prompts|not found|"
                           r"Repository not found|403|401", re.I)


def log_file() -> Path:
    raw = os.environ.get("PUSH_YES_LOG", "").strip()
    return Path(raw).expanduser() if raw else Path.home() / ".mentcached" / "push-yes.log"


def strip_userinfo(url: str) -> str:
    """https://user:pass@host/x -> https://host/x; an ssh user name is no secret and stays."""
    return re.sub(r"^(https?://)[^/@]*@", r"\1", url)


def https_of(url: str) -> str:
    """fr1me's https_of, the same four rules in the same order."""
    u = re.sub(r"^git@([^:]+):/?", r"https://\1/", url, count=1)
    u = re.sub(r"^ssh://[^@]+@([^/]+)/", r"https://\1/", u, count=1)
    u = re.sub(r"^[^@/]+@([^:]+):/*", r"https://\1/", u, count=1)
    return re.sub(r"(\.git)?$", ".git", u, count=1)


def owner_of(url: str) -> str:
    u = re.sub(r"^ssh://[^/]+/+", "", url, count=1)
    u = re.sub(r"^https?://[^/]+/+", "", u, count=1)
    u = re.sub(r"^[^@/]+@[^:]+:/*", "", u, count=1)
    return u.split("/")[0]


def _row_for(path: Path, url: str) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        if line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) >= 2 and f[0]:
            try:
                if re.search(f[0], url):
                    return f
            except re.error:
                continue
    return []


def find_c4() -> Path | None:
    raw = os.environ.get("C4_ROOT", "").strip()
    if raw and (Path(raw) / "d" / "users" / "FRAMES.tsv").is_file():
        return Path(raw)
    try:
        from . import c4face
        d = c4face.find_c4().get("dir")
    except Exception:                                   # noqa: BLE001 -- no c4face: no C4
        d = None
    return Path(d) if d and (Path(d) / "d" / "users" / "FRAMES.tsv").is_file() else None


def parties_file(c4: Path, tree: str | None) -> Path | None:
    raw = os.environ.get("FR1ME_PARTIES", "").strip()
    if raw:
        return Path(raw)
    if tree and (Path(tree) / ".colophon-parties.json").is_file():
        return Path(tree) / ".colophon-parties.json"
    for c in (c4 / ".." / "AS4CE" / "AS4CE0001", c4 / ".." / "AS4CE0001", c4 / ".." / ".." / "AS4CE" / "AS4CE0001",
              Path(__file__).resolve().parents[2]):
        f = c / "peers" / "bryant" / "colophon" / "references" / "parties.example.json"
        if f.is_file():
            return f
    return None


def _git_env() -> dict:
    """An environment with no key bound and no way to ask anyone: for the anonymous read."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and not k.startswith("GCM_")}
    env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    return env


def visibility(url: str) -> str:
    forced = os.environ.get("FR1ME_VISIBILITY", "").strip()
    if forced:
        return forced
    try:
        r = subprocess.run(["git", "-c", "credential.helper=", "-c", "core.askPass=", "ls-remote", https_of(url), "HEAD"],
                           env=_git_env(), capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=25, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if r.returncode == 0:
        return "public"
    return "private" if _PRIVATE_HINT.search(r.stderr) else "unknown"


def first_reader(url: str, c4: Path, tree: str | None) -> tuple[str, list[str]]:
    """(verdict, reasons): fr1me egress, read again in Python."""
    seams, notes = [], []
    fr = _row_for(c4 / "d" / "users" / "FRAMES.tsv", url)
    parties = ""
    if not fr:
        notes.append("no row in FRAMES.tsv names this place: its frame is not declared")
    else:
        org = fr[1] if len(fr) > 1 else ""
        parties = fr[2] if len(fr) > 2 else ""
        own = owner_of(url)
        if org != "-" and own != org:
            seams.append(f"FRAMES says org {org}; the place's own URL says owner {own}")
    if parties:
        pf = parties_file(c4, tree)
        if pf is None or not pf.is_file():
            seams.append("no colophon parties file to set beside FRAMES (FR1ME_PARTIES)")
        else:
            try:
                d = json.loads(pf.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                d = {}
            miss = [k.strip() for k in parties.split(",") if not isinstance(d.get(k.strip()), dict)]
            if miss:
                seams.append("FRAMES names parties colophon's parties file does not hold: " + " ".join(miss))
    vis = visibility(url)
    ur = _row_for(c4 / "d" / "users" / "USERS.tsv", url)
    decl = (ur[1] if len(ur) > 1 and ur[1] else "unnamed")
    pub = decl in ("published", "users")
    if tree:
        try:
            q = subprocess.run(["git", "-C", tree, "config", "--get", "fr1me.public"], capture_output=True,
                               text=True, timeout=15, stdin=subprocess.DEVNULL)
            pub = pub or q.stdout.strip() == "true"
        except (OSError, subprocess.TimeoutExpired):
            pass
    reasons = [f"visible {vis}; declared {decl}; public on purpose {'yes' if pub else 'no'}"] + \
              [f"SEAM {s}" for s in seams] + [f"NOTE {n}" for n in notes]
    if seams:
        return "STOP", reasons + ["the sources disagree about whose place this is; held for the keeper"]
    if notes:
        return "STOP", reasons + ["nothing declares whose place this is; add a FRAMES.tsv row on the keeper's word"]
    if vis == "public" and not pub:
        return "STOP", reasons + [f"anyone can read {strip_userinfo(url)}, and nothing declares it public"]
    if vis not in ("public", "private"):
        return "NOT CHECKED", reasons + ["whether anyone can read the place (the read gave no clear answer)"]
    return "GO", reasons + ["the frame is declared, two sources agree, and who can read the place is known"]


def second_reader(url: str, c4: Path, remote: str, tree: str | None) -> tuple[str, list[str]]:
    """fr1me itself, when sh can run it; ("", [why not]) otherwise."""
    fr1me = c4 / "bin" / "fr1me"
    sh = shutil.which("sh")
    if not fr1me.is_file() or not sh:
        return "", ["fr1me not run: " + ("no sh on PATH" if not sh else f"no {fr1me}")]
    where = ["--repo", tree, "--remote", remote] if tree else ["--url", url]
    env = {**_git_env(), "C4_ROOT": str(c4)}
    try:
        r = subprocess.run([sh, str(fr1me), "egress", *where], env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return "NOT CHECKED", [f"fr1me did not finish ({e.__class__.__name__})"]
    last = [ln for ln in r.stdout.splitlines() if ln.strip()][-1:] or ["(no answer)"]
    return {0: "GO", 1: "STOP"}.get(r.returncode, "NOT CHECKED"), ["fr1me: " + last[0]]


def shape_problem(args: list[str]) -> str:
    """args after 'push'.  '' when the shape is allowed."""
    opt = [a for a in args if a.startswith("-")]
    if opt:
        return f"{opt[0]!r} is an option; a push through key_run takes none (no --force, --mirror, --delete, -u)"
    if len(args) != 2:
        return "a push through key_run is `git push REMOTE REFSPEC`: one remote and one refspec, nothing else"
    remote, spec = args
    if spec.startswith("+"):
        return f"{spec!r} forces the push (a leading +); a forced push is never decided here"
    src = spec.split(":", 1)[0]
    if not src:
        return f"{spec!r} has no source: it deletes the branch on the remote; never decided here"
    if "*" in spec:
        return f"{spec!r} is a pattern; name one branch"
    if ("/" in remote or ":" in remote or "@" in remote) and not _URL_OK.match(remote):
        return f"{remote!r} is not a remote name or a URL of a known shape (ssh://, git@host:, https://)"
    return ""


def _git(cwd: str, *a: str) -> str:
    try:
        r = subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=15, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def commit_range(cwd: str, remote: str, spec: str, named: bool) -> str:
    src, _, dst = spec.partition(":")
    dst = (dst or src).removeprefix("refs/heads/")
    new = _git(cwd, "rev-parse", "--verify", "-q", src + "^{commit}")[:12] or "?"
    old = (_git(cwd, "rev-parse", "--verify", "-q", f"refs/remotes/{remote}/{dst}")[:12] if named else "") or "new"
    return f"{old}..{new}"


_USERINFO = re.compile(r"(https?://)[^/@\s]*@")


def scrub_text(f: str, masks: list[str]) -> str:
    f = _USERINFO.sub(r"\1", f)
    for s in masks:
        if s and len(s) >= 4:
            f = f.replace(s, "[key]")
    return f


def write_log(row: list[str], masks: list[str]) -> str:
    clean = []
    for f in row:
        f = scrub_text(f, masks)
        f = f.replace("\t", " ").replace("\n", " ").replace("\r", " ")
        clean.append(f)
    p = log_file()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as h:
            h.write("\t".join(clean) + "\n")
    except OSError as e:
        return f"not written ({e.__class__.__name__})"
    return str(p)


def decide(argv: list[str], cwd: str, masks: list[str]) -> dict:
    """The decision for one `git push`, logged.  {"verdict", "reasons", "place", "range", "log", "url"}."""
    args = argv[1:]
    if args and args[0] == "push":
        args = args[1:]
    remote = args[0] if args else ""
    spec = args[1] if len(args) > 1 else ""
    reasons: list[str] = []
    url, verdict, rng = "", "REFUSED", ""
    prob = shape_problem(args)
    named = bool(remote) and not prob and not ("/" in remote or ":" in remote or "@" in remote)
    if prob:
        reasons.append(prob)
    elif named:
        url = _git(cwd, "remote", "get-url", "--push", remote)
        if not url:
            reasons.append(f"{remote!r} is not a remote of {cwd}")
        elif _git(cwd, "config", "--get", f"remote.{remote}.mirror") == "true":
            reasons.append(f"the remote {remote!r} is set to mirror: a mirror push forces and deletes")
            url = ""
        elif not _URL_OK.match(url):
            reasons.append(f"the remote {remote!r} has a URL of a shape not decided here (ssh://, git@host:, https:// only)")
            url = ""
    else:
        url = remote
    if url:
        c4 = find_c4()
        if c4 is None:
            verdict = "NOT CHECKED"
            reasons.append("no C4 found (C4_ROOT, or the c4.root preference): there is no frame to read")
        else:
            tree = cwd if named else None
            v1, r1 = first_reader(url, c4, tree)
            v2, r2 = second_reader(url, c4, remote, tree)
            reasons += r1 + r2
            if v2 and v2 != v1:
                verdict = "STOP" if "GO" in (v1, v2) else v1
                reasons.append(f"the two readers differ (python {v1}, fr1me {v2}): held, not guessed")
            else:
                verdict = v1
        rng = commit_range(cwd, remote, spec, named)
    place = strip_userinfo(url) if url else ""
    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    logged = write_log([utc, cwd, strip_userinfo(remote), place, spec, verdict, "; ".join(reasons), rng], masks)
    reasons = [scrub_text(r, masks) for r in reasons]
    return {"verdict": verdict, "reasons": reasons, "place": place, "range": rng, "log": logged, "url": url}
