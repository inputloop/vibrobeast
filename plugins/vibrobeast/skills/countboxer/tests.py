#!/usr/bin/env python3
"""tests.py -- cb1ox read by a second language.  Written from the procedure as he wrote it
(c4/q/2026-10-14-count-ladder-palace-release/PROMPT.md), not from the script.
  python3 tests.py              every case
  python3 tests.py --prove-red  plant faults in copies of cb1ox; each must turn a case red
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
Authored by Mentat (for Corwin; claude-opus-5-5)."""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "scripts", "cb1ox")
SH = shutil.which("sh")


def run(tool, *args):
    p = subprocess.run([SH, tool, *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def mklist(d, n, inhibited=False, name="L"):
    path = os.path.join(d, name)
    with open(path, "w") as f:
        f.write("# the question: what would make the palace floor easier to read?\n")
        if inhibited:
            f.write("# sort: inhibited\n")
        for i in range(1, n + 1):
            f.write(f"idea {i:02d}\n\n" if i % 5 == 0 else f"idea {i:02d}\n")
    return path


def cases(tool):
    out = []
    def case(name, ok, why=""):
        out.append((name, bool(ok), why))
    d = tempfile.mkdtemp(prefix="cb1ox-t.")
    try:
        rc, o = run(tool, "state", mklist(d, 0, name="e"))
        case("empty: start by answering to 4", rc == 0 and "0 idea" in o and "until there are 4" in o, o)
        rc, o = run(tool, "state", mklist(d, 3, name="three"))
        case("3: one more to 4, and running dry is honest", "1 more to 4" in o and "honest" in o, o)
        rc, o = run(tool, "state", mklist(d, 4, name="four"))
        case("4: GRAIN, ask for one more", "rung: GRAIN" in o and "one more" in o, o)
        rc, o = run(tool, "state", mklist(d, 5, name="five"))
        case("blank and # lines are not ideas (5 written with blanks)", o.startswith("5 idea"), o)
        nine = mklist(d, 9, name="nine")
        rc, o = run(tool, "state", nine)
        case("9: GREAT, ask whether one can be taken away", "rung: GREAT" in o and "taken away" in o, o)
        rc, o = run(tool, "drop", nine, "3", "repeats idea 1 in other words")
        lost = open(nine + ".losers").read() if os.path.exists(nine + ".losers") else ""
        case("drop keeps the loser with its reason and count", lost.startswith("9\tGREAT\trepeats idea 1") and "idea 03" in lost, lost)
        case("drop removes only that idea", "idea 03" not in open(nine).read() and "idea 04" in open(nine).read(), o)
        case("drop keeps the # lines", open(nine).read().startswith("# the question"), "")
        rc, o = run(tool, "check", nine)
        case("check: one removal at GREAT is fine", rc == 0 and o.startswith("OK"), o)
        with open(nine, "a") as f: f.write("idea 10\n")
        run(tool, "drop", nine, "1", "weakest again")
        rc, o = run(tool, "check", nine)
        case("check: a second removal at GREAT is a fault", rc == 1 and "only the weakest one" in o, o)
        early = mklist(d, 5, name="early")
        run(tool, "drop", early, "1", "too soon")
        rc, o = run(tool, "check", early)
        case("check: taking away before GREAT is a fault", rc == 1 and "before GREAT" in o, o)
        rc, o = run(tool, "drop", mklist(d, 9, name="nowhy"), "2", "")
        case("drop refuses without a reason", rc == 2 and "say why" in o, o)
        rc, o = run(tool, "drop", mklist(d, 9, name="range"), "12", "x")
        case("drop refuses an idea that is not there", rc == 2 and "no idea 12" in o, o)
        rc, o = run(tool, "state", mklist(d, 17, inhibited=True, name="inh"))
        case("17 with sorting inhibited: STOP at GRAND", "STOP" in o and "inhibited" in o, o)
        rc, o = run(tool, "state", mklist(d, 17, name="g17"))
        case("17 sortable: one more, then race", "one more, then resort" in o, o)
        rc, o = run(tool, "check", mklist(d, 18, inhibited=True, name="inh18"))
        case("check: past GRAND with sorting inhibited is a fault", rc == 1 and "stops at GRAND" in o, o)
        g18 = mklist(d, 18, name="g18")
        rc, o = run(tool, "state", g18)
        case("18: race the halves inverted", "GRAND and one" in o and "race" in o, o)
        rc, o = run(tool, "race", g18)
        lines = o.splitlines()
        case("race pairs first with last, inward", lines[0] == "pair 1: idea 01" and lines[1].strip() == "vs: idea 18"
             and "pair 9: idea 09" in o and "vs: idea 10" in o, o)
        case("race at 18 adds no note", not o.startswith("note:"), o)
        case("race never names a winner", "winner is the idea with the more unique" in o and "wins" not in o, o)
        rc, o = run(tool, "race", mklist(d, 7, name="odd"))
        case("race refuses an odd count", rc == 2, o)
        rc, o = run(tool, "state", mklist(d, 20, name="g20"))
        case("over GRAND: continue unless a bigger instrument", "over GRAND" in o and "bigger instrument" in o, o)
        rc, o = run(tool, "frobnicate", g18)
        case("an unknown command is refused loudly, exit 2", rc == 2, o)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return out


PLANTS = [
    ("GREAT moved to 8", "GRAIN=4 GREAT=9 GRAND=17", "GRAIN=4 GREAT=8 GRAND=17"),
    ("drop forgets the loser", "\"$why\" \"$idea\" >> \"$losers\"", "\"$why\" \"$idea\" > /dev/null"),
    ("race pairs top with top", "a[n+1-i]", "a[i+n/2]"),
    ("inhibited is ignored", "grep -q '^# *sort: *inhibited' \"$list\"", "false"),
    ("blank lines count as ideas", "awk '!/^[ \\t]*($|#)/' \"$list\"", "awk '!/^#/' \"$list\""),
    ("a second GREAT removal passes", "[ \"$g\" -le 1 ]", "[ \"$g\" -le 9 ]"),
    ("early removal passes", "'$1 < G {f=1} END {exit f}'", "'END {exit 0}'"),
    ("drop needs no reason", "[ -n \"$why\" ] ||", "true ||"),
]


def prove_red():
    src = open(TOOL).read()
    d = tempfile.mkdtemp(prefix="cb1ox-mut.")
    caught = 0
    try:
        for name, old, new in PLANTS:
            if src.count(old) != 1:
                print(f"NOT PLANTED  {name} -- cb1ox changed shape; update PLANTS"); continue
            m = os.path.join(d, "cb1ox")
            open(m, "w").write(src.replace(old, new))
            try:
                fails = [c for c in cases(m) if not c[1]]
            except Exception as e:          # a crash on a broken tool is a red case too
                fails = [(f"the cases could not run: {e}", False, "")]
            if fails:
                caught += 1; print(f"CAUGHT  {name} -- {fails[0][0]}")
            else:
                print(f"MISSED  {name} -- every case stayed green on a broken cb1ox")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(f"prove-red: {caught} of {len(PLANTS)} planted faults caught")
    return caught == len(PLANTS)


if __name__ == "__main__":
    if not SH:
        print("needs sh"); sys.exit(77)
    if "--prove-red" in sys.argv:
        sys.exit(0 if prove_red() else 1)
    res = cases(TOOL)
    for name, ok, why in res:
        print(("ok    " if ok else "FAIL  ") + name + ("" if ok else "\n      " + why.strip().replace("\n", "\n      ")))
    bad = sum(1 for r in res if not r[1])
    print(f"{len(res) - bad} of {len(res)} cases hold")
    sys.exit(1 if bad else 0)
