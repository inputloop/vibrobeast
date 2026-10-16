#!/usr/bin/env python3
"""tests.py -- test-tax's cases: Python reads the awk tool (scripts/tt1ax).

Each mode on a small fixture; the rows that must not match; a dead row and a malformed one; the
tool's own prove-red; and, inside a tree that has bin/tg1rn, the two readers held to each other on
that tree's whole suite.  --prove-red runs the tool's planted faults.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "scripts" / "tt1ax"
IDS = "a.B.test_one\na.B.test_two\nc.test_x\nc.test_xy\nd.E.test_star\naXB.test_one\nlone\n"
TABLE = ("# a comment\n\n*.B.*\tbee\nc.test_?\tsee\na.B.test_one\tbee solo\n"
         "d.E.test_[st]tar\tbracket\n")


def tt(mode, ids=IDS, table=TABLE):
    d = Path(tempfile.mkdtemp())
    (d / "t.tsv").write_text(table, encoding="utf-8", newline="\n")
    p = subprocess.run(["sh", str(TOOL), "--table", str(d / "t.tsv"), mode], input=ids,
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def cases():
    res = []

    def check(name, ok, why=""):
        res.append((name, bool(ok), why))

    rc, out, err = tt("--of")
    want = ("a.B.test_one\ta a.B #bee #solo\na.B.test_two\ta a.B #bee\nc.test_x\tc #see\n"
            "c.test_xy\tc\nd.E.test_star\td d.E #bracket\naXB.test_one\taXB\nlone\tlone\n")
    check("--of gives file, group, then each tag once in table order", rc == 0 and out == want, out + err)
    check("a ? is one character, and the pattern is anchored at its end", "c.test_xy\tc\n" in out, out)
    check("a dot in a pattern is a dot", "aXB.test_one\taXB\n" in out, out)
    check("a bare name is its own file", "lone\tlone\n" in out, out)

    rc, out, _ = tt("--counts")
    lines = out.splitlines()
    check("--counts puts the tags first", lines[:4] == ["2\t#bee", "1\t#bracket", "1\t#see", "1\t#solo"], out)
    check("--counts names files and groups after", "2\ta.B" in lines and "1\tlone" in lines, out)

    rc, out, _ = tt("--untagged")
    check("--untagged lists the tests no row tags", out.split() == ["c.test_xy", "aXB.test_one", "lone"], out)

    rc, out, _ = tt("--dead", table=TABLE + "none.*\tghost\n")
    check("--dead names the row that tags nothing, exit 1", rc == 1 and out == "none.*\tghost\n", out)
    rc, out, _ = tt("--check", table=TABLE + "no-tab-here\n")
    check("--check names a malformed row, exit 1", rc == 1 and "malformed row" in out, out)
    rc, out, _ = tt("--check")
    check("--check passes a sound table", rc == 0 and "every one tags at least one test" in out, out)

    rc, out, err = tt("--of", table="")
    check("an empty table tags nothing and fails nothing", rc == 0 and "#" not in out, out + err)

    p = subprocess.run(["sh", str(TOOL), "--prove-red"], capture_output=True, text=True, encoding="utf-8")
    check("the tool's own planted faults are all caught", p.returncode == 0 and "6 of 6" in p.stdout, p.stdout)

    # the second reader, when this skill sits in a tree that has one
    root = HERE.parent.parent
    tg = root / "bin" / "tg1rn"
    if tg.is_file():
        a = subprocess.run([sys.executable, str(tg), "--ids"], capture_output=True, text=True,
                           encoding="utf-8", cwd=str(root))
        names = "".join(l.split("\t")[0] + "\n" for l in a.stdout.splitlines())
        table = next((root / d / "CATEGORIES.tsv" for d in ("t", ".t", "tests")
                      if (root / d / "CATEGORIES.tsv").is_file()), None)
        if a.returncode == 0 and table is not None:
            b = subprocess.run(["sh", str(TOOL), "--table", str(table), "--of"], input=names,
                               capture_output=True, text=True, encoding="utf-8")
            check(f"tg1rn and tt1ax agree on every test of this tree ({len(names.splitlines())})",
                  a.stdout == b.stdout, "the first difference: " + next(
                      (f"{x!r} / {y!r}" for x, y in zip(a.stdout.splitlines(), b.stdout.splitlines()) if x != y), "lengths"))
        else:
            res.append(("tg1rn and tt1ax agree on this tree", None, "tg1rn could not list, or no table"))
    else:
        res.append(("tg1rn and tt1ax agree on this tree", None, "no bin/tg1rn here: the skill travelled alone"))
    return res


def main():
    if "--prove-red" in sys.argv:
        return subprocess.run(["sh", str(TOOL), "--prove-red"]).returncode
    res = cases()
    bad = 0
    for name, ok, why in res:
        mark = "skip" if ok is None else ("ok  " if ok else "FAIL")
        bad += ok is False
        print(f"  {mark}  {name}" + (f"  -- {why.strip()[:300]}" if ok is not True and why else ""))
    n = sum(1 for r in res if r[1] is not None)
    print(f"test-tax: {n - bad}/{n} hold" + (f", {len(res) - n} skipped" if len(res) > n else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
