#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""Atomically copy SOURCE onto TARGET on a mounted disk, then verify it landed.

Why this exists: the file (Edit/Write) tool's cached view of a mounted
Windows folder can desync from the real disk. It then reports "updated
successfully" while the bytes never reach the mount. bash writes the real
disk, so we cross the sand here and prove the crossing.

Usage:
    python3 safe_write.py [--validate] SOURCE TARGET
    python3 safe_write.py --selftest   (controls verify; mutants are caught)

Flow: write a staged temp file (same dir, same extension) + fsync. With
--validate, run a language-aware validity check on the STAGED file FIRST
(see validators.py: .el byte-compile, .py py_compile, .html closing tag) and
refuse to promote it if it fails - a broken file never replaces the good
one. Then atomic os.replace, then reopen TARGET and confirm its byte length
and sha256 match SOURCE.

Exit: 0 = verified, byte-identical write. 1 = byte/sha mismatch. 2 = staged
file failed validation (target left untouched).

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


def selftest():
    """--selftest: controls must verify, mutants must be refused or flagged."""
    import subprocess
    import tempfile
    me = os.path.abspath(__file__)
    bad = 0

    def case(label, ok):
        nonlocal bad
        print("  {}  {}".format("ok  " if ok else "FAIL", label))
        if not ok:
            bad += 1

    def run(*a):
        return subprocess.run([sys.executable, me] + list(a),
                              capture_output=True, text=True).returncode

    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, "src.txt")
        dst = os.path.join(t, "dst.txt")
        with open(src, "w") as f:
            f.write("one\ntwo\n")
        with open(dst, "w") as f:
            f.write("old\n")
        rc = run(src, dst)
        case("control: plain copy verifies (exit 0, bytes equal)",
             rc == 0 and sha256(src) == sha256(dst))

        good = os.path.join(t, "good.py")
        broken = os.path.join(t, "broken.py")
        with open(good, "w") as f:
            f.write("x = 1\n")
        with open(broken, "w") as f:
            f.write("def (:\n")
        before = sha256(good)
        rc = run("--validate", broken, good)
        case("mutant: --validate refuses a broken .py (exit 2, target untouched)",
             rc == 2 and sha256(good) == before)

        rc = run(os.path.join(t, "missing.txt"), dst)
        case("mutant: a missing SOURCE is refused (exit non-zero)", rc != 0)

        # The MISMATCH path must fire: make the target hash read wrong.
        real = globals()["sha256"]
        globals()["sha256"] = (lambda p: "0" * 64 if os.path.abspath(p)
                               == os.path.abspath(dst) else real(p))
        saved = sys.argv
        sys.argv = [me, src, dst]
        try:
            main()
            code = 0
        except SystemExit as e:
            code = e.code
        finally:
            sys.argv = saved
            globals()["sha256"] = real
        case("mutant: a target that reads back wrong is MISMATCH (exit 1)",
             code == 1)

    if bad == 0:
        print("selftest: every control verified and every mutant was caught")
        return 0
    print("selftest: {} case(s) misbehaved".format(bad))
    return 1


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        sys.exit(selftest())
    do_validate = "--validate" in args
    args = [a for a in args if a != "--validate"]
    if len(args) != 2:
        sys.exit("usage: safe_write.py [--validate] SOURCE TARGET")
    source, target = args

    if not os.path.isfile(source):
        sys.exit("safe_write: SOURCE does not exist: " + source)

    with open(source, "rb") as f:
        data = f.read()

    # Stage in the same directory, preserving the extension so language
    # validators (and emacs byte-compile) recognise the file type.
    root, ext = os.path.splitext(target)
    tmp = root + ".sandboxer.tmp" + ext
    target_dir = os.path.dirname(os.path.abspath(target)) or "."

    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    # Verify BEFORE promote: gate the staged copy so a broken file never
    # lands on the real path.
    if do_validate:
        status, detail = validate(tmp)
        print("validate: {:<5} ({})".format(status.upper(), detail))
        if status == "fail":
            try:
                os.remove(tmp)
            except OSError:
                pass
            print("RESULT : BLOCKED - staged file failed validation; "
                  "target left untouched")
            sys.exit(2)

    os.replace(tmp, target)

    # Make the rename durable where the filesystem allows it.
    try:
        dfd = os.open(target_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass

    src_len, src_hash = len(data), sha256(source)
    dst_len, dst_hash = os.path.getsize(target), sha256(target)
    ok = (src_len == dst_len) and (src_hash == dst_hash)

    print("source : {:>10} bytes  {}".format(src_len, src_hash))
    print("target : {:>10} bytes  {}".format(dst_len, dst_hash))
    if ok:
        print("RESULT : VERIFIED - write landed intact")
    else:
        print("RESULT : MISMATCH - write did NOT land; do not trust it")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
