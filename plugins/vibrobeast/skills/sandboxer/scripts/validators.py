#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""Language-aware validity checks: does a written file actually compile/parse?

Used by safe_write.py (a gate before promoting a staged file onto the real
path) and by verify.py (--validate). Dispatch is by file extension.

Design rule: a MISSING toolchain (e.g. no emacs on this box) is reported as
SKIP, never FAIL. The byte/structure checks still guard against truncation,
and we must not block a write just because the validator binary is absent.

validate(path) -> (status, detail)
    status in {"ok", "fail", "skip"}

Stdlib only - no dependencies.
"""
import os
import shutil
import subprocess
import tempfile


def _run(cmd, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return p.returncode, (p.stdout + p.stderr).strip()
    except OSError as e:
        return None, str(e)


def _validate_el(path):
    # Emacs Lisp: byte-compile must succeed. Warnings are allowed; only a
    # hard compile error fails the gate. checkdoc (style) is intentionally
    # NOT gated here - it is lint, not validity.
    if shutil.which("emacs") is None:
        return "skip", "emacs not found"
    root, _ = os.path.splitext(path)
    elc = root + ".elc"
    pre_existing = os.path.exists(elc)
    code, out = _run([
        "emacs", "-Q", "--batch",
        "--eval", "(setq byte-compile-error-on-warn nil)",
        "-f", "batch-byte-compile", path,
    ])
    if not pre_existing and os.path.exists(elc):
        try:
            os.remove(elc)  # clean up the .elc we just produced
        except OSError:
            pass
    if code is None:
        return "skip", out
    if code == 0:
        return "ok", "byte-compile clean"
    return "fail", (out[-400:] or "byte-compile error")


def _validate_py(path):
    # py_compile writes a .pyc into __pycache__/ beside the file it checks; on the
    # flaky mount that is a fresh stale-pyc shadow. Aim the cache at a temp dir
    # that is removed afterwards, so a validation pass leaves nothing behind.
    with tempfile.TemporaryDirectory(prefix="sandboxer-pyc.") as cache:
        env = dict(os.environ, PYTHONPYCACHEPREFIX=cache)
        code, out = _run(["python3", "-m", "py_compile", path], env=env)
    if code is None:
        return "skip", out
    return ("ok", "py_compile clean") if code == 0 else ("fail", out[-400:])


def _validate_html(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    if "</html>" not in text.lower():
        return "fail", "missing </html>"
    return "ok", "closing tag present"


_DISPATCH = {
    ".el": _validate_el,
    ".py": _validate_py,
    ".html": _validate_html,
    ".htm": _validate_html,
}


def validate(path):
    ext = os.path.splitext(path)[1].lower()
    fn = _DISPATCH.get(ext)
    if fn is None:
        return "skip", "no validator for {}".format(ext or "(no extension)")
    return fn(path)
