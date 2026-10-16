#!/usr/bin/env python3
"""tests.py -- monocle-stack's keeper (scripts/mn1sk, sh and awk) held by a second language.

usage:  python3 tests.py [--prove-red]
--prove-red plants six faults in copies of mn1sk; each must turn a case red.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "scripts" / "mn1sk"
BLOCK = "Trace down where the demand for a signature comes from. Is it a public repo?\nAvoid counts | lists.\n"
GOOD = """# block: block.txt
# seed: what does this ask?
? Where does the demand for a signature come from?  « where the demand for a signature comes from »
  > opening: a hook reads every time
  > falsifier: a commit with the link that pushes
  ? Who reads the rule, and when?  « ^ »
? Is it a public repo?  << is it a public repo >>
  > opening: private | so no rewrite
x How many trailers? -- the block says avoid counts
"""


def mk(stack, block=BLOCK):
    d = Path(tempfile.mkdtemp())
    (d / "block.txt").write_text(block, encoding="utf-8")
    (d / "s.txt").write_text(stack, encoding="utf-8")
    return d / "s.txt"


def run(tool, *args):
    p = subprocess.run(["sh", str(tool), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


def cases(tool):
    res = []
    def check(name, ok, why=""):
        res.append((name, bool(ok), why))
    def fault(name, stack, word):
        rc, out = run(tool, "check", mk(stack))
        check(name, rc == 1 and word in out, out)

    rc, out = run(tool, "check", mk(GOOD))
    check("M1 a stack whose every quote is in the block holds", rc == 0 and "holds (3 questions" in out, out)
    fault("M2 a quote that is not in the block is a fault", GOOD.replace("« where the demand", "« where the urge"), "not in the block")
    fault("M3 a question with no quote is a fault", GOOD.replace("  << is it a public repo >>", ""), "no « quote »")
    fault("M4 a first-layer question cannot cite its parent", GOOD.replace("<< is it a public repo >>", "« ^ »"), "has no parent")
    fault("M5 a question two layers below its parent is a fault", GOOD.replace("  ? Who reads", "    ? Who reads"), "jumps from layer")
    fault("M6 the same question twice is a fault", GOOD + "? is it a PUBLIC repo?  « public repo »\n", "the same question as line")
    fault("M7 a question set aside keeps its reason", GOOD.replace(" -- the block says avoid counts", ""), "keeps its reason")
    rc, out = run(tool, "check", mk(GOOD.replace("# block: block.txt\n", "")))
    check("M12 a stack with no block cannot be checked, and says so", rc == 1 and "no block" in out, out)

    rc, out = run(tool, "state", mk(GOOD))
    check("M8 state counts each layer and where its questions came from",
          "layer 1: 2 question(s); 2 raised by the block, 0 by their parent alone; 1 set aside" in out
          and "layer 2: 1 question(s); 0 raised by the block, 1 by their parent alone" in out and "in all: 3" in out, out)
    rc, out = run(tool, "grid", mk(GOOD))
    rows = [l for l in out.splitlines() if l.startswith("| ") and not l.startswith("| layer")]
    check("M9 the grid has a row per question and a column per cell name", len(rows) == 3
          and out.splitlines()[0] == "| layer | question | raised by | opening | falsifier |", out)
    check("M9 a | inside a cell is escaped, so the table keeps its columns", "private \\| so no rewrite" in out, out)
    rc, out = run(tool, "layer", mk(GOOD), 1)
    check("M10 layer N lists exactly that layer's questions", out.splitlines() == [
        "Where does the demand for a signature come from?", "Is it a public repo?"], out)
    rc, out = run(tool, "check", mk(GOOD.replace("<< is it a public repo >>", "« is it a public repo »")))
    check("M11 << >> and « » mean the same", rc == 0, out)
    g = GOOD.replace("  > opening: a hook reads every time\n", "").replace("  > falsifier: a commit with the link that pushes\n", "")
    rc, out = run(tool, "gaps", mk(g))
    check("M13 gaps names a first-layer question left with no answered, partly or opening cell",
          rc == 1 and "GAP" in out and "Where does the demand" in out and "public repo" not in out, out)
    rc, out = run(tool, "gaps", mk(GOOD))
    check("M13 gaps is quiet when every first-layer question has one", rc == 0 and "none" in out, out)
    return res


PLANTS = [
    ("every quote passes", 'index(NB, norm(quote)) ? "block" : "missing"', '1 ? "block" : "missing"'),
    ("duplicates pass", "if (key in seen)", "if (0)"),
    ("a first layer may cite its parent", 'inb == "parent" && d == 1', '0'),
    ("a set-aside needs no reason", '$3 !~ / -- [^ ]/', '0'),
    ("gaps sees every question as accounted", "if (!(order[i] in had))", "if (0)"),
    ("the grid drops its cells", "cell[r, col[name]] = (", "junk[r, col[name]] = ("),
]


def prove_red():
    src = TOOL.read_text(encoding="utf-8"); caught = 0
    for name, old, new in PLANTS:
        if src.count(old) != 1:
            print(f"  NOT PLANTED  {name} (the tool changed shape)"); continue
        d = Path(tempfile.mkdtemp()); t = d / "mn1sk"
        t.write_text(src.replace(old, new), encoding="utf-8")
        bad = [r for r in cases(t) if not r[1]]
        print(f"  {'caught' if bad else 'MISSED'}  {name}" + (f"  (by: {bad[0][0]})" if bad else ""))
        caught += bool(bad)
    print(f"monocle-stack --prove-red: {caught} of {len(PLANTS)} planted faults caught")
    return 0 if caught == len(PLANTS) else 1


def main():
    if "--prove-red" in sys.argv:
        return prove_red()
    res = cases(TOOL); bad = 0
    for name, ok, why in res:
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -- {why.strip()[:300]}"))
    print(f"monocle-stack: {len(res) - bad}/{len(res)} hold")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
