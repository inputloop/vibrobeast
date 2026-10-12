#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""A second reader of SPEC.md, written from the spec and not from scripts/sk2mt.

It builds stores BY HAND to the letter of the spec and asks sk2mt to read them, and it drives sk2mt to
write and then parses the log itself. Stdlib only.  GPL-3.0-or-later.  Authored by Mentat (for Corwin).
"""
import hashlib, os, re, subprocess, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "scripts", "sk2mt")
HEADER = "ITEM STATE CUR LAST DATE NOTE"
ITEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")
STATE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+%-]*\Z")
DATE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")


def run(root, *args):
    p = subprocess.run(["sh", SK, "-C", root, *args], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, LC_ALL="C"))
    return p.returncode, p.stdout


def parse(root):
    """S3, read independently: header, then six fields with NOTE as the rest of the line."""
    with open(os.path.join(root, "log")) as f:
        lines = f.read().split("\n")
    assert lines[0] == HEADER, lines[0]
    rows = []
    for ln in lines[1:]:
        if not ln:
            continue
        parts = ln.split(" ", 5)
        assert len(parts) == 6 and parts[5] != "", ln
        rows.append(dict(zip(HEADER.split(), parts)))
    return rows


def handmade(root, rows, archive=()):
    """Write a spec-compliant store without using sk2mt."""
    os.makedirs(os.path.join(root, "skill-metrics"))
    with open(os.path.join(root, "log"), "w") as f:
        f.write(HEADER + "\n")
        for r in rows:
            f.write(" ".join(r) + "\n")
    last = {}
    for r in rows:
        last[r[0]] = r[1]
    for it, st in last.items():
        with open(os.path.join(root, "skill-metrics", it), "w") as f:
            f.write(st + "\n")
    for rel, data in archive:
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        with open(os.path.join(root, rel), "wb") as f:
            f.write(data)


def arc(item, name, data):
    return f"archive/{item}/{hashlib.sha256(data).hexdigest()[:16]}-{name}"


class SpecReader(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = os.path.join(self.d, "m")

    def test_reads_a_handmade_store(self):
        a = arc("c4", "C4.md", b"one\n")
        handmade(self.root, [
            ("c4", "GREEN", "NONE", "NONE", "2026-09-01T00:00:00Z", "-"),
            ("c4", "RED", a, "NONE", "2026-09-02T00:00:00Z", "two words  here"),
            ("dungeon-mode", "OK", "NONE", "NONE", "2026-09-01T00:00:00Z", "-"),
        ], [(a, b"one\n")])
        self.assertEqual(run(self.root, "state", "c4"), (0, "RED\n"))
        self.assertEqual(run(self.root, "cur", "c4"), (0, a + "\n"))
        self.assertEqual(run(self.root, "note", "c4"), (0, "two words  here\n"))
        self.assertEqual(run(self.root, "state"), (0, "c4 RED\ndungeon-mode OK\n"))
        self.assertEqual(run(self.root, "check")[0], 0)

    def test_check_catches_a_row_the_spec_forbids(self):
        handmade(self.root, [("c4", "GREEN", "NONE", "NONE", "yesterday", "-")])
        self.assertEqual(run(self.root, "check")[0], 1)

    def test_check_catches_an_unlogged_item_file(self):
        handmade(self.root, [("c4", "GREEN", "NONE", "NONE", "2026-09-01T00:00:00Z", "-")])
        with open(os.path.join(self.root, "skill-metrics", "stray"), "w") as f:
            f.write("OK\n")
        self.assertEqual(run(self.root, "check")[0], 1)

    def test_written_log_obeys_s3_and_s4(self):
        self.assertEqual(run(self.root, "init")[0], 0)
        src = os.path.join(self.d, "SKILL.md")
        for i, (state, body) in enumerate([("OK", b"a"), ("OK", b"a"), ("OK", b"b"), ("FAULT", b"b")]):
            with open(src, "wb") as f:
                f.write(body)
            run(self.root, "set", "skill-sign", state, "--file", src, "--note", f"run {i}")
        rows = parse(self.root)
        for r in rows:
            self.assertRegex(r["ITEM"], ITEM); self.assertRegex(r["STATE"], STATE); self.assertRegex(r["DATE"], DATE)
            for k in ("CUR", "LAST"):
                v = r[k]
                if v != "NONE":
                    data = open(os.path.join(self.root, v), "rb").read()
                    self.assertEqual(os.path.basename(v)[:16], hashlib.sha256(data).hexdigest()[:16])
        # S4.3: the repeat with identical bytes is not interesting; three rows survive
        self.assertEqual([r["STATE"] for r in rows], ["OK", "OK", "FAULT"])
        self.assertEqual(rows[0]["LAST"], "NONE")
        self.assertEqual(rows[1]["LAST"], rows[0]["CUR"])          # new bytes: LAST = old CUR
        self.assertEqual(rows[2]["CUR"], rows[1]["CUR"])           # same bytes, new state
        self.assertEqual(rows[2]["LAST"], rows[1]["LAST"])         # ...so LAST carries over
        with open(os.path.join(self.root, "skill-metrics", "skill-sign")) as f:
            self.assertEqual(f.read(), "FAULT\n")

    def test_grep_semantics_on_names(self):
        handmade(self.root, [(n, "OK", "NONE", "NONE", "2026-09-01T00:00:00Z", "-")
                             for n in ("gf-02-layered-assurance", "layered", "polygram")])
        self.assertEqual(run(self.root, "items", "layered"), (0, "layered\n"))
        self.assertEqual(run(self.root, "items", "-e", "layered")[1].split(), ["gf-02-layered-assurance", "layered"])
        self.assertEqual(run(self.root, "items", "-c", "-E", "-e", "^(poly|lay)"), (0, "2\n"))
        self.assertEqual(run(self.root, "items", "nosuch")[0], 1)
        self.assertEqual(run(os.path.join(self.d, "absent"), "items")[0], 3)

    def test_state_filter_reads_the_item_files(self):
        handmade(self.root, [("a", "RED", "NONE", "NONE", "2026-09-01T00:00:00Z", "-"),
                             ("b", "GREEN", "NONE", "NONE", "2026-09-01T00:00:00Z", "-"),
                             ("RED", "GREEN", "NONE", "NONE", "2026-09-01T00:00:00Z", "-")])
        self.assertEqual(run(self.root, "items", "--state", "RED"), (0, "a\n"))
        self.assertEqual(run(self.root, "items", "-e", "RED"), (0, "RED\n"))   # names, not states


if __name__ == "__main__":
    import sys
    r = unittest.main(exit=False, verbosity=0).result
    n, bad = r.testsRun, len(r.failures) + len(r.errors)
    print(f"{n - bad}/{n} spec checks")
    sys.exit(1 if bad else 0)
