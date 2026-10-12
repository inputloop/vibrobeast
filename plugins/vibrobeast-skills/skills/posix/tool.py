#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""posix check — advisory lint for shell deliverables (posix skill).

stdlib only; READ-ONLY; always exits 0 (advisory means advisory).
Usage: python3 tool.py FILE...

Reports, per file:
  - shebang: present? which dialect does it declare?
  - dialect mismatch: bashisms in a #!/bin/sh file (heuristic, named)
  - transport smells: CRLF line endings, missing final newline, NUL bytes
    (torn write / stale-mount fingerprints — see MODEL-readers-and-mounts)
  - notes: set -e/-u presence (a prompt, not a demand)
  - sh -n / bash -n syntax check when the interpreter is on PATH

Heuristics prompt the review loop in SKILL.md; they never replace it.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

# Bashisms that break or silently change meaning under a strict POSIX sh.
# (pattern, human name) — heuristic by design; false positives are cheap,
# a silent bashism in a #!/bin/sh script is not.
BASHISMS = [
    (re.compile(r'(^|\s)\[\['), "[[ ... ]] test"),
    (re.compile(r'(^|\s)function\s+\w+'), "'function' keyword"),
    (re.compile(r'(^|\s)local\s+\w'), "'local' (common but not POSIX)"),
    (re.compile(r'\w+\+?=\('), "array assignment"),
    (re.compile(r"\$'"), "$'...' quoting"),
    (re.compile(r'(^|\s)source\s'), "'source' (use '.')"),
    (re.compile(r'\$RANDOM'), "$RANDOM"),
    (re.compile(r'\$\{\w+(//|\^|,|:\d)'), "bash parameter expansion"),
    (re.compile(r'&>'), "&> redirection"),
    (re.compile(r'(^|\s)echo\s+-[en]'), "echo -e/-n (use printf)"),
    (re.compile(r'<<<'), "here-string"),
    (re.compile(r'(^|\s)\(\('), "(( arithmetic command"),
]

SH_RE = re.compile(r'^#!\s*(/usr)?/bin/(env\s+)?sh\b')
BASH_RE = re.compile(r'^#!\s*(/usr)?/bin/(env\s+)?bash\b')


def strip_comments(line: str) -> str:
    """Cheap comment strip — good enough for advisory pattern checks."""
    out, quote = [], None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == '#' and (i == 0 or line[i - 1] in ' \t;'):
            break
        out.append(ch)
        i += 1
    return ''.join(out)


def check(path: str) -> None:
    def say(level: str, msg: str) -> None:
        print(f"posix: {path}: [{level}] {msg}")

    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as e:
        say("READ", f"cannot read: {e}")
        return

    # transport smells first — a torn file lints as nonsense
    nuls = data.count(b'\x00')
    if nuls:
        say("SMELL", f"{nuls} NUL bytes — torn write or stale read; "
            "cross-read a second path before judging content")
    if b'\r\n' in data:
        say("SMELL", "CRLF line endings — most sh reject or misparse; "
            "convert before landing")
    if data and not data.endswith(b'\n'):
        say("SMELL", "no final newline — truncation fingerprint, or just "
            "untidy; confirm which")

    text = data.decode('utf-8', errors='replace')
    lines = text.splitlines()
    first = lines[0] if lines else ''

    is_sh = bool(SH_RE.match(first))
    is_bash = bool(BASH_RE.match(first))
    if not first.startswith('#!'):
        say("NOTE", "no shebang — fine for a fragment; name the assumed "
            "dialect in a comment")
    elif not (is_sh or is_bash):
        say("NOTE", f"shebang {first!r} — not sh/bash, checks limited")

    if is_sh:
        for n, raw in enumerate(lines[1:], start=2):
            code = strip_comments(raw)
            if not code.strip():
                continue
            for pat, name in BASHISMS:
                if pat.search(code):
                    say("BASHISM", f"line {n}: {name} under #!/bin/sh")

    if is_sh or is_bash:
        body = '\n'.join(strip_comments(l) for l in lines)
        if not re.search(r'set\s+(-\w*[eu]\b|-o\s+(errexit|nounset))', body):
            say("NOTE", "no set -e/-u — deliberate is fine (warn-don't-die "
                "is a live house idiom); accidental is not. Which is it?")

    checker = 'bash' if is_bash else 'sh'
    if shutil.which(checker):
        r = subprocess.run([checker, '-n', path],
                           capture_output=True, text=True)
        if r.returncode == 0:
            say("OK", f"{checker} -n clean")
        else:
            detail = (r.stderr or r.stdout).strip()
            last = detail.splitlines()[-1] if detail else "failed"
            say("SYNTAX", f"{checker} -n: {last} — if this file lives on a "
                "mount, re-check from fresh bytes before trusting this")
    else:
        say("SKIP", f"{checker} not on PATH; syntax unchecked")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    for p in argv:
        check(p)
    return 0  # advisory, always


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
