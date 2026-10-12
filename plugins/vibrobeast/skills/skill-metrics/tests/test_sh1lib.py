#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""test_sh1lib.py - scripts/sh1lib.sh, every helper, sourced into a real POSIX sh.

  python3 tests/test_sh1lib.py              each sl_ helper does what its comment says
  python3 tests/test_sh1lib.py --prove-red  the above, then break sh1lib.sh six ways in a temp
                                            copy; exit 0 only if the real library is green AND
                                            every break goes red

The skill's own suite (tests.sh) reaches sh1lib only through sk2mt, which uses six of the ten
helpers and only the sha256sum branch of sl_hash.  This file reads the library directly: all
three sl_hash branches (sha256sum, then shasum -- a Mac -- then openssl), each forced by a PATH
that holds only that tool, must give the digest Python gives; sl_match matches the WHOLE value
and never a value with a newline; sl_write_atomic replaces whole or leaves the old file whole
and no sidecar; sl_tally, sl_rel, sl_die, sl_warn, sl_utc, sl_epoch do what they say.
Runs under dash when it is on PATH (the library says it is tested under dash), else sh.
A branch whose tool this box lacks is SKIPPED and said so.  Needs: python3 and sh.
Exit: 0 all good - 1 a case failed / a break went unnoticed - 2 setup
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "scripts", "sh1lib.sh")
SH = shutil.which("dash") or shutil.which("sh") or "/bin/sh"
BASE_TOOLS = ["cat", "cut", "sed", "grep", "mv", "rm", "awk", "date", "perl"]

MUTANTS = [  # (name, old, new) -- old must occur exactly once in sh1lib.sh
    ("sl_match matches part of a value", 'grep -E -x -q -e "$1"', 'grep -E -q -e "$1"'),
    ("sl_match lets a newline through", "'*) return 1 ;; esac", "'*) : ;; esac"),
    ("openssl digest not trimmed", "sed 's/^.*= *//'", "cat"),
    ("sl_write_atomic leaves its sidecar", '{ rm -f "$_t"; return 1; }', "{ return 1; }"),
    ("sl_tally counts by two", "+ 1 ))", "+ 2 ))"),
    ("sl_rel keeps the slash", '${2#"$1"/}', '${2#"$1"}'),
]


def shim(root, name, tools):
    d = os.path.join(root, "bin-" + name)
    os.makedirs(d, exist_ok=True)
    for t in tools:
        p = shutil.which(t)
        if p and not os.path.exists(os.path.join(d, t)):
            os.symlink(p, os.path.join(d, t))
    return d


def sh(lib, script, path=None, stdin=None, cwd=None):
    env = dict(os.environ, SL_PROG="t")
    if path is not None:
        env["PATH"] = path
    p = subprocess.run([SH, "-c", '. "$0"\n' + script, lib], capture_output=True, text=True,
                       env=env, stdin=stdin, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def suite(lib, root, quiet=False):
    results, fails = [], []

    def check(name, ok, why=""):
        results.append(ok)
        if not ok:
            fails.append(name + " -- " + why)
        if not quiet:
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else " -- " + why))

    def skip(name, why):
        if not quiet:
            print("SKIP  " + name + " -- " + why)

    d = tempfile.mkdtemp(dir=root)
    f = os.path.join(d, "data.bin")
    with open(f, "wb") as h:
        h.write(b"garden bytes\x00\xff\n" * 3)
    want = hashlib.sha256(open(f, "rb").read()).hexdigest()

    # sl_hash, one branch at a time
    for tool in ("sha256sum", "shasum", "openssl"):
        if not shutil.which(tool):
            skip(f"sl_hash via {tool}", f"{tool} not on this box"); continue
        path = shim(root, tool, BASE_TOOLS + [tool])
        rc, out, err = sh(lib, f'sl_hash "{f}"', path=path)
        check(f"sl_hash via {tool} equals Python's sha256", rc == 0 and out.strip() == want,
              f"rc={rc} out={out.strip()!r} err={err.strip()!r}")
    rc, out, err = sh(lib, f'sl_hash "{f}"', path=shim(root, "none", BASE_TOOLS))
    check("sl_hash with no hash tool fails and says what it needs", rc == 1 and "need sha256sum" in err,
          f"rc={rc} err={err.strip()!r}")
    rc, out, err = sh(lib, f'sl_hash "{d}/absent"')
    check("sl_hash of a missing file fails and says so", rc == 1 and "not a file" in err, f"rc={rc}")

    # sl_match
    cases = [("[a-z]+", "abc", 0), ("[a-z]+", "abc1", 1), ("b", "abc", 1),
             ("[a-z]+", "abc\nabc", 1), ("a|b", "b", 0)]
    for ere, val, rcw in cases:
        rc = subprocess.run([SH, "-c", '. "$0"; sl_match "$1" "$2"', lib, ere, val],
                            capture_output=True).returncode
        check(f"sl_match {ere!r} {val!r} -> {'match' if rcw == 0 else 'no match'}", rc == rcw, f"rc={rc}")

    # sl_write_atomic
    t = os.path.join(d, "t.txt")
    with open(t, "w") as h:
        h.write("old whole file\n")
    rc, _, _ = sh(lib, f'printf "new\\n" | sl_write_atomic "{t}"')
    left = [n for n in os.listdir(d) if ".tmp." in n]
    check("sl_write_atomic replaces the file, no sidecar left",
          rc == 0 and open(t).read() == "new\n" and not left, f"rc={rc} left={left}")
    with open(t, "w") as h:
        h.write("old whole file\n")
    rc, _, _ = sh(lib, f'sl_write_atomic "{t}" < "{d}"')  # stdin is a directory: cat fails mid-write
    left = [n for n in os.listdir(d) if ".tmp." in n]
    check("sl_write_atomic on a failed read: old file whole, no sidecar, non-zero",
          rc != 0 and open(t).read() == "old whole file\n" and not left, f"rc={rc} left={left}")

    # sl_tally, sl_rel, sl_die, sl_warn
    rc, out, _ = sh(lib, "sl_tally n; sl_tally n; sl_tally n; echo $n")
    check("sl_tally counts from unset: 3 calls -> 3", out.strip() == "3", f"out={out.strip()!r}")
    rc, out, _ = sh(lib, "sl_rel /a/b /a/b/c/d; sl_rel /a/b /a/bc/d; sl_rel /a/b x/y")
    check("sl_rel strips ROOT/ only when PATH is under it",
          out.split("\n")[:3] == ["c/d", "/a/bc/d", "x/y"], f"out={out.split()!r}")
    rc, out, err = sh(lib, "sl_die broken thing; echo after")
    check("sl_die exits 2, names the program, stops", rc == 2 and err.strip() == "t: broken thing" and "after" not in out,
          f"rc={rc} err={err.strip()!r}")
    rc, out, err = sh(lib, "sl_warn soft; echo after")
    check("sl_warn prints to stderr and carries on", rc == 0 and err.strip() == "t: soft" and out.strip() == "after",
          f"rc={rc}")
    rc, out, _ = sh(lib, "sl_have sh && ! sl_have no-such-tool-xyzzy && echo ok")
    check("sl_have finds sh and not a tool that is not there", out.strip() == "ok", f"out={out.strip()!r}")

    # sl_utc, sl_epoch
    rc, out, _ = sh(lib, "sl_utc")
    okfmt = bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", out.strip()))
    near = okfmt and abs(time.mktime(time.strptime(out.strip(), "%Y-%m-%dT%H:%M:%SZ")) - time.mktime(time.gmtime())) < 60
    check("sl_utc is an ISO-8601 UTC stamp for now", near, f"out={out.strip()!r}")
    rc, out, _ = sh(lib, "sl_epoch")
    check("sl_epoch is seconds since 1970, now", out.strip().isdigit() and abs(int(out) - time.time()) < 60,
          f"out={out.strip()!r}")

    shutil.rmtree(d, ignore_errors=True)
    passed = sum(results)
    if not quiet:
        print(f"{passed}/{len(results)} pass, {len(results) - passed} fail  (shell: {SH})")
    return passed == len(results), (fails[0] if fails else "")


def main():
    mode = sys.argv[1:] or [""]
    if mode[0] not in ("", "--prove-red") or len(mode) > 1:
        sys.exit("usage: python3 tests/test_sh1lib.py [--prove-red]")
    lib = os.path.normpath(LIB)
    if not os.path.isfile(lib):
        print("test_sh1lib.py: missing " + lib, file=sys.stderr); return 2
    root = tempfile.mkdtemp(prefix="sh1lib-tests.")
    try:
        if mode[0] == "":
            print("== sh1lib.sh: every helper, sourced into " + SH + " ==")
            return 0 if suite(lib, root)[0] else 1
        print("== controls: the real sh1lib.sh ==")
        if not suite(lib, root)[0]:
            print("PROVE-RED NOT OK -- the real library is not green; a red here proves nothing")
            return 1
        print("\n== planted breaks: each must turn the suite red ==")
        src = open(lib, encoding="utf-8").read()
        caught = 0
        for i, (name, old, new) in enumerate(MUTANTS):
            if src.count(old) != 1:
                print(f"BREAK NOT PLANTED  {name} -- sh1lib.sh changed shape; update MUTANTS")
                continue
            m = os.path.join(root, f"mutant{i}.sh")
            with open(m, "w", encoding="utf-8") as h:
                h.write(src.replace(old, new))
            ok, first = suite(m, root, quiet=True)
            if ok:
                print(f"MISSED  {name} -- the suite stayed green on a broken library")
            else:
                caught += 1
                print(f"CAUGHT  {name} -- FAIL {first}")
        print()
        if caught == len(MUTANTS):
            print(f"PROVE-RED OK -- controls green, {caught}/{len(MUTANTS)} planted breaks caught")
            return 0
        print(f"PROVE-RED NOT OK -- {caught}/{len(MUTANTS)} planted breaks caught")
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
