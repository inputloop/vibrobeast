#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""Independent cross-checks on a written file. Trust the disk, not the tool.

Usage:
    python3 verify.py FILE [--validate] [--expect-lines N] [--expect-sha SHA]
    python3 verify.py --selftest   (controls pass; mutants exit non-zero)

Always prints: byte count, line count, sha256, and the last 3 lines.

Structural checks by extension (advisory unless noted):
  .html/.htm : closing </html> present?   (MISSING is a hard failure -
               a strong truncation tell for a complete HTML document)
  .js/.html  : are {} () [] balanced?     (advisory: a crude scan that does
               not strip strings/comments, so a lone brace inside a string
               can flag a false positive - read it as a hint, not a verdict)

With --validate, also run a language-aware validity check (validators.py:
.el byte-compile, .py py_compile, .html closing tag). A FAIL exits nonzero;
a SKIP (e.g. no emacs installed) does not.

Exit code is nonzero if an --expect assertion fails, an HTML file is missing
its closing tag, or --validate reports FAIL. Use two or more signals
together; no single check is proof. A line count that DROPS after an
additive edit is truncation until you have proven otherwise.

Stdlib only - no dependencies.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validators import validate  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def brace_balance(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    opens = set(pairs.values())
    stack = []
    for ch in text:
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False, "premature '{}'".format(ch)
            stack.pop()
    if stack:
        return False, "{} unclosed (likely truncation): {}".format(
            len(stack), "".join(stack[-8:]))
    return True, "balanced"


def selftest():
    """--selftest: controls must pass, mutants must exit non-zero."""
    import subprocess
    import tempfile
    me = os.path.abspath(__file__)
    bad = 0

    def case(label, want, *a):
        nonlocal bad
        rc = subprocess.run([sys.executable, me] + list(a),
                            capture_output=True, text=True).returncode
        ok = (rc == 0) if want == 0 else (rc != 0)
        print("  {}  {} (exit {})".format("ok  " if ok else "FAIL", label, rc))
        if not ok:
            bad += 1

    with tempfile.TemporaryDirectory() as t:
        txt = os.path.join(t, "three.txt")
        with open(txt, "w") as f:
            f.write("a\nb\nc\n")
        good_sha = sha256(txt)
        case("control: right line count and sha", 0,
             txt, "--expect-lines", "3", "--expect-sha", good_sha)
        case("mutant:  wrong line count", 1, txt, "--expect-lines", "4")
        case("mutant:  wrong sha", 1, txt, "--expect-sha", "0" * 64)
        page = os.path.join(t, "page.html")
        with open(page, "w") as f:
            f.write("<html><body>x</body></html>\n")
        case("control: complete html", 0, page)
        cut = os.path.join(t, "cut.html")
        with open(cut, "w") as f:
            f.write("<html><body>x</bo")
        case("mutant:  html missing </html>", 1, cut)
        broken = os.path.join(t, "broken.py")
        with open(broken, "w") as f:
            f.write("def (:\n")
        case("mutant:  --validate on a broken .py", 1, broken, "--validate")

    if bad == 0:
        print("selftest: every control passed and every mutant exited non-zero")
        return 0
    print("selftest: {} case(s) misbehaved".format(bad))
    return 1


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        sys.exit(selftest())
    do_validate = "--validate" in args
    args = [a for a in args if a != "--validate"]
    if not args:
        sys.exit("usage: verify.py FILE [--validate] "
                 "[--expect-lines N] [--expect-sha SHA]")

    path = args[0]
    expect_lines = None
    expect_sha = None
    i = 1
    while i < len(args):
        if args[i] == "--expect-lines":
            expect_lines = int(args[i + 1]); i += 2
        elif args[i] == "--expect-sha":
            expect_sha = args[i + 1].lower(); i += 2
        else:
            sys.exit("verify: unknown arg: " + args[i])

    if not os.path.isfile(path):
        sys.exit("verify: file does not exist: " + path)

    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8", errors="replace")
    nbytes = len(raw)
    lines = text.splitlines()
    nlines = len(lines)
    digest = sha256(path)

    print("file   : {}".format(path))
    print("bytes  : {}".format(nbytes))
    print("lines  : {}".format(nlines))
    print("sha256 : {}".format(digest))
    print("tail   :")
    for ln in lines[-3:]:
        print("  | " + ln)

    failed = False
    ext = os.path.splitext(path)[1].lower()

    if ext in (".html", ".htm"):
        has_close = "</html>" in text.lower()
        print("html   : </html> {}".format("present" if has_close else "MISSING"))
        if not has_close:
            failed = True

    if ext in (".html", ".htm", ".js"):
        ok, why = brace_balance(text)
        print("braces : {} ({})".format("ok" if ok else "ADVISORY", why))

    if do_validate:
        status, detail = validate(path)
        print("validate: {:<5} ({})".format(status.upper(), detail))
        if status == "fail":
            failed = True

    if expect_lines is not None:
        ok = (nlines == expect_lines)
        print("expect : lines {} vs {} -> {}".format(
            expect_lines, nlines, "ok" if ok else "FAIL"))
        if not ok:
            failed = True

    if expect_sha is not None:
        ok = (digest == expect_sha)
        print("expect : sha {} -> {}".format(
            expect_sha[:16] + "...", "ok" if ok else "FAIL"))
        if not ok:
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
