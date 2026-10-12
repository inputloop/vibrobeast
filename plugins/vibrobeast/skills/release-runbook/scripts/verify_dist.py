#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""verify_dist.py - signature-coverage gate for polygram release artifacts.

For each release version found in the dist directory (or the one named with
--version): the three artifacts exist, each carries a detached .asc, each
signature verifies against the pinned fingerprint (when gpg is available),
and the MANIFEST lists no sed-strays.

Exits NON-ZERO on any failure: this is a gate, not advisory. It exists
because a hand-rolled signing loop once glob-typo'd 'MANIFST' and shipped
manifests unsigned with no error — coverage must be checked from the
outside, by a tool that fails loudly.

  python3 verify_dist.py --dist DIR [--version X.Y.Z] [--fpr FINGERPRINT]

stdlib only; shells out to gpg if present, else degrades to coverage-only
with a warning (and still fails on missing files/signatures).
"""
import argparse, os, re, shutil, subprocess, sys

PIN = "ECE77CF417C76C1ACFCE7C2B5B6135511580F007"
KINDS = ("tar.gz", "zip", "MANIFEST")
STRAY = re.compile(r"/sed[A-Za-z0-9]{6}$", re.M)
VER = re.compile(r"^polygram-curation-(\d[\w.]*?)\.(?:tar\.gz|zip|MANIFEST)$")

def gpg_verify(asc, target, fpr):
    """Return (ok, detail). Verifies signature AND that the signing key
    matches the pinned fingerprint (gpg --verify alone trusts any key)."""
    r = subprocess.run(["gpg", "--batch", "--status-fd", "1", "--verify",
                        asc, target], capture_output=True, text=True)
    good = "[GNUPG:] GOODSIG" in r.stdout or "\nGOODSIG" in r.stdout
    m = re.search(r"VALIDSIG (\w+)", r.stdout)
    if r.returncode != 0 or not good:
        return False, "signature does not verify"
    if not m or not m.group(1).endswith(fpr[-16:]):
        return False, f"signed, but NOT by pinned key ({m.group(1) if m else 'unknown'})"
    return True, "verified, pinned key"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--version", default="",
                    help="check one version (default: every version present)")
    ap.add_argument("--fpr", default=PIN, help="pinned signing fingerprint")
    a = ap.parse_args()

    if not os.path.isdir(a.dist):
        sys.exit(f"verify_dist: no such directory: {a.dist}")

    versions = {a.version} if a.version else \
        {m.group(1) for f in os.listdir(a.dist) if (m := VER.match(f))}
    if not versions:
        sys.exit("verify_dist: no polygram-curation-* artifacts found")

    havegpg = shutil.which("gpg") is not None
    if not havegpg:
        print("WARN   gpg not found — checking coverage only, NOT verifying "
              "signatures. Do not treat this as a full pass.")

    failures = 0
    for ver in sorted(versions):
        print(f"== verify dist {ver} ==")
        for kind in KINDS:
            f = os.path.join(a.dist, f"polygram-curation-{ver}.{kind}")
            asc = f + ".asc"
            name = os.path.basename(f)
            if not os.path.isfile(f):
                print(f"FAIL   missing artifact: {name}"); failures += 1; continue
            if not os.path.isfile(asc):
                print(f"FAIL   UNSIGNED: {name} (no .asc)"); failures += 1; continue
            if havegpg:
                ok, why = gpg_verify(asc, f, a.fpr)
                print(f"{'OK    ' if ok else 'FAIL  '} {name}.asc — {why}")
                failures += 0 if ok else 1
            else:
                print(f"OK?    {name}.asc present (unverified — no gpg)")
        man = os.path.join(a.dist, f"polygram-curation-{ver}.MANIFEST")
        if os.path.isfile(man):
            text = open(man, encoding="utf-8", errors="replace").read()
            if STRAY.search(text):
                print("FAIL   MANIFEST lists a sed-stray — remint"); failures += 1
            else:
                print("OK     MANIFEST stray-free")
        print()

    if failures:
        print(f"verify_dist: {failures} FAILURE(S) — this dist is not release-clean.")
        sys.exit(1)
    print("verify_dist: all checks passed.")

if __name__ == "__main__":
    main()
