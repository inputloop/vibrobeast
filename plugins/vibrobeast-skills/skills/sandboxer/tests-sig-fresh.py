#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""tests-sig-fresh.py - scripts/sig-fresh.sh against files signed in a throwaway keyring.

  python3 tests-sig-fresh.py              a GOOD signature passes, every planted fault fails
  python3 tests-sig-fresh.py --prove-red  the above, then break sig-fresh.sh five ways in a temp
                                          copy; exit 0 only if the real script is green AND every
                                          break goes red

What sig-fresh.sh promises (its header): exit 0 and "GOOD" only when the signature verifies
against a key in the caller's keyring; exit 1 and "BAD" when it does not; exit 2 on usage,
unreadable input or no gpg; SIGFILE defaults to FILE.asc; the freshening rename leaves the file
exactly as it was, under its own name, with nothing beside it.

Written in Python on purpose: the script under test is sh, so the check is in a second language.
Needs python3 (stdlib) and gpg; a throwaway keyring is made under the temp dir and removed after,
your own keyring is never touched.  Exit: 0 all good - 1 a case failed / a break went unnoticed
- 2 setup (including: no gpg, since every promise here is about gpg's verdict).
"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "scripts", "sig-fresh.sh")
SH = shutil.which("sh") or "/bin/sh"

MUTANTS = [  # (name, old, new) -- old must occur exactly once in sig-fresh.sh
    ("verdict ignores gpg", 'if gpg --verify -- "$s" "$f" >/dev/null 2>&1 ; then', "if true ; then"),
    ("BAD exits 0", 'keep both artifacts for the record" >&2\nexit 1', 'keep both artifacts for the record" >&2\nexit 0'),
    ("missing signature not a usage error", 'test -r "$s" ||', "true ||"),
    ("freshen copies instead of renaming back", 'mv -- "$t" "$p"', 'cp -- "$t" "$p"'),
    ("SIGFILE default is not FILE.asc", "s=${2-${1-}.asc}", "s=${2-${1-}.sig}"),
]


def gpg(home, *args, inp=None):
    return subprocess.run(["gpg", "--homedir", home, "--batch", "--quiet", *args],
                          input=inp, capture_output=True)


class Fixture:
    def __init__(self, root):
        self.root = root
        # gpg-agent puts its sockets in the keyring folder, and a Unix socket path is capped near
        # 107 bytes: under a deep TMPDIR (bin/gd1ck gives each leg one) the agent cannot start.
        # So the two keyrings live in a short folder of their own when the temp dir is deep.
        self.homes = root if len(root) < 70 else tempfile.mkdtemp(prefix="sf-", dir="/tmp")
        self.ring = os.path.join(self.homes, "ring")        # the caller's keyring: holds 'trusted'
        self.stranger = os.path.join(self.homes, "stranger")  # a key the caller never imported
        for home, who in ((self.ring, "trusted"), (self.stranger, "stranger")):
            os.mkdir(home, 0o700)
            r = gpg(home, "--passphrase", "", "--pinentry-mode", "loopback",
                    "--quick-gen-key", f"sf-test-{who} <{who}@invalid>", "ed25519", "sign", "never")
            if r.returncode != 0:
                sys.exit(f"tests-sig-fresh.py: could not make a throwaway key: {r.stderr.decode()[-300:]}")
        os.mkdir(os.path.join(root, "nobin"))

    def close(self):
        for home in (self.ring, self.stranger):
            subprocess.run(["gpgconf", "--homedir", home, "--kill", "gpg-agent"], capture_output=True)
        if self.homes != self.root:
            shutil.rmtree(self.homes, ignore_errors=True)

    def case_dir(self, name):
        d = os.path.join(self.root, "c", name)
        os.makedirs(d)
        return d

    def sign(self, home, path, out=None):
        r = gpg(home, "--yes", "--armor", "--detach-sign", "-o", out or path + ".asc", path)
        if r.returncode != 0:
            sys.exit("tests-sig-fresh.py: could not sign " + path)


def run(script, fx, *args, path=None):
    env = dict(os.environ, GNUPGHOME=fx.ring)
    if path is not None:
        env["PATH"] = path
    p = subprocess.run([SH, script, *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr


def suite(script, fx, quiet=False):
    results, fails = [], []

    def check(name, ok, why=""):
        results.append(ok)
        if not ok:
            fails.append(name + " -- " + why)
        if not quiet:
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else " -- " + why))

    def expect(name, got, rc, out_has, err_has=""):
        code, out, err = got
        ok = code == rc and out_has in out and err_has in err
        check(name, ok, f"exit {code} (want {rc}); stdout={out.strip()[:80]!r} stderr={err.strip()[-80:]!r}")

    def write(d, name, data=b"hello, garden\n"):
        p = os.path.join(d, name)
        with open(p, "wb") as f:
            f.write(data)
        return p

    # control: a good signature, default SIGFILE, freshening leaves nothing behind
    d = fx.case_dir("good"); f = write(d, "f.txt"); fx.sign(fx.ring, f)
    before = open(f, "rb").read()
    expect("control: good signature, default FILE.asc, is GOOD", run(script, fx, f), 0, "GOOD " + f)
    check("control: file unchanged after freshening", open(f, "rb").read() == before, "bytes changed")
    left = sorted(set(os.listdir(d)) - {"f.txt", "f.txt.asc"})
    check("control: nothing left beside it (no .fresh.* copies)", not left, "left behind: " + " ".join(left))
    # control: an explicit SIGFILE
    d = fx.case_dir("explicit"); f = write(d, "f.txt"); fx.sign(fx.ring, f, os.path.join(d, "other.sig"))
    expect("control: explicit SIGFILE is used", run(script, fx, f, os.path.join(d, "other.sig")), 0, "GOOD")
    # planted faults
    d = fx.case_dir("tamper"); f = write(d, "f.txt"); fx.sign(fx.ring, f)
    with open(f, "ab") as h:
        h.write(b"one more line\n")
    expect("file edited after signing is BAD (exit 1)", run(script, fx, f), 1, "BAD " + f, "next moves")
    d = fx.case_dir("stranger"); f = write(d, "f.txt"); fx.sign(fx.stranger, f)
    expect("signed by a key not in the keyring is BAD", run(script, fx, f), 1, "BAD")
    d = fx.case_dir("swap"); f = write(d, "f.txt"); g = write(d, "g.txt", b"other bytes\n"); fx.sign(fx.ring, g)
    expect("another file's signature is BAD", run(script, fx, f, g + ".asc"), 1, "BAD")
    d = fx.case_dir("nosig"); f = write(d, "f.txt")
    expect("no signature file is a usage error (exit 2)", run(script, fx, f), 2, "", "no signature at")
    expect("no FILE argument is a usage error", run(script, fx), 2, "", "usage:")
    expect("unreadable FILE is a usage error", run(script, fx, os.path.join(d, "absent.txt")), 2, "", "cannot read")
    d = fx.case_dir("nogpg"); f = write(d, "f.txt"); fx.sign(fx.ring, f)
    expect("no gpg on PATH is exit 2, never GOOD", run(script, fx, f, path=os.path.join(fx.root, "nobin")),
           2, "", "gpg not on PATH")

    passed = sum(results)
    if not quiet:
        print(f"{passed}/{len(results)} pass, {len(results) - passed} fail")
    return passed == len(results), (fails[0] if fails else "")


def main():
    mode = sys.argv[1:] or [""]
    if mode[0] not in ("", "--prove-red") or len(mode) > 1:
        sys.exit("usage: python3 tests-sig-fresh.py [--prove-red]")
    if not os.path.isfile(SCRIPT):
        print("tests-sig-fresh.py: missing " + SCRIPT, file=sys.stderr); return 2
    if shutil.which("gpg") is None:
        print("tests-sig-fresh.py: gpg not found; nothing here can be checked without it", file=sys.stderr)
        return 2
    root = tempfile.mkdtemp(prefix="sf-tests.")
    fx = None
    try:
        fx = Fixture(root)
        if mode[0] == "":
            print("== sig-fresh.sh: a good signature passes, planted faults fail ==")
            return 0 if suite(SCRIPT, fx)[0] else 1
        print("== controls: the real sig-fresh.sh ==")
        if not suite(SCRIPT, fx)[0]:
            print("PROVE-RED NOT OK -- the real script is not green; a red here proves nothing")
            return 1
        print("\n== planted breaks: each must turn the suite red ==")
        src = open(SCRIPT, encoding="utf-8").read()
        caught = 0
        for i, (name, old, new) in enumerate(MUTANTS):
            if src.count(old) != 1:
                print(f"BREAK NOT PLANTED  {name} -- sig-fresh.sh changed shape; update MUTANTS")
                continue
            m = os.path.join(root, f"mutant{i}.sh")
            with open(m, "w", encoding="utf-8") as h:
                h.write(src.replace(old, new))
            shutil.rmtree(os.path.join(root, "c"), ignore_errors=True)
            ok, first = suite(m, fx, quiet=True)
            if ok:
                print(f"MISSED  {name} -- the suite stayed green on a broken script")
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
        if fx:
            fx.close()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
