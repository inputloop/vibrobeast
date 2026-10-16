#!/usr/bin/env python3
"""tests.py -- interesting-lines' cases: Python reads the awk filter (scripts/ln1fd).

Fixed cases, then the filter's promises held as PROPERTIES of any log, recomputed here in Python
from the same table: every line a shown class matches is in the output, in order; nothing a shown
class matches is ever folded; the counts add up (read = shown + folded); every fold line names the
first and last lines it folded.  Run on a synthetic log always, and on the seat's own make check
log when it is beside us.  --prove-red runs the filter's own planted faults.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "scripts" / "ln1fd"
TABLE = HERE / "assets" / "interesting.tsv"


def ln(text, table=TABLE, *extra):
    d = Path(tempfile.mkdtemp())
    f = d / "in.log"
    f.write_bytes(text.encode("utf-8"))
    p = subprocess.run(["sh", str(TOOL), "--no-live", "--table", str(table), *extra, str(f)],
                       capture_output=True)      # bytes: text mode would split a lone \r into a line
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def rows(table):
    out = []
    for line in Path(table).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        c, a, pat = line.split("\t", 2)
        # awk's ERE and Python's re agree on what this table uses; a [.] bracket, | and anchors
        out.append((c, a, re.compile(pat)))
    return out


def properties(text, table=TABLE):
    """The promises, checked from outside; returns a list of what broke."""
    rc, out, err = ln(text, table)
    broke = []
    if rc != 0:
        return [f"exit {rc}: {err}"]
    lines = [re.sub(r"\r+$", "", l).rsplit("\r", 1)[-1] for l in text.split("\n")]   # as the filter reads them
    if lines and lines[-1] == "":
        lines.pop()
    tab = rows(table)
    shown_class = []
    for l in lines:
        c = next((c for c, a, rx in tab if rx.search(l)), None)
        if c is not None and next(a for cc, a, _ in tab if cc == c) != "fold":
            shown_class.append(l)
    got = out.split("\n")
    i = 0
    for l in got:                                   # every shown-class line, in order
        if i < len(shown_class) and l == shown_class[i]:
            i += 1
    if i != len(shown_class):
        broke.append(f"a line a shown class matches is missing or out of order: {shown_class[i]!r}")
    summary = got[-2] if got and got[-1] == "" else got[-1]
    m = re.match(r"ln1fd: (\d+) lines read, (\d+) shown, (\d+) folded in (\d+) runs?", summary)
    if not m:
        broke.append(f"no summary line: {summary!r}")
    else:
        read, shown, folded, runs = map(int, m.groups())
        if read != len(lines):
            broke.append(f"read {read}, but the log has {len(lines)} lines")
        if shown + folded != read:
            broke.append(f"shown {shown} + folded {folded} != read {read}")
        fold_lines = [l for l in got if re.match(r"\.\.\. \d+ lines folded: ", l)]
        if len(fold_lines) != runs:
            broke.append(f"{runs} runs said, {len(fold_lines)} fold lines printed")
        if sum(int(l.split()[1]) for l in fold_lines) != folded:
            broke.append("the fold lines' counts do not add up to the folded total")
        if any(" ... " not in l[l.index(": ") + 2:] for l in fold_lines):
            broke.append("a fold of several lines does not name its first and last")
    return broke


SYNTH = "\n".join(
    [f"test_{i} (m.C.test_{i}) ... ok" for i in range(40)]
    + ["test_x (m.C.test_x) ... FAIL", "F:/t.py:20: ResourceWarning: unclosed file", "  open(x)",
       "ResourceWarning: Enable tracemalloc to get the object allocation traceback"]
    + [f"test_{i} (m.D.test_{i}) ... ok" for i in range(40, 60)]
    + ["=" * 70, "FAIL: test_x (m.C.test_x)", "-" * 70, "Traceback (most recent call last):",
       '  File "t.py", line 3, in test_x', "AssertionError: 1 != 2", "", "-" * 70,
       "Ran 61 tests in 1.0s", "", "FAILED (failures=1)"]) + "\n"


def cases():
    res = []

    def check(name, ok, why=""):
        res.append((name, bool(ok), why))

    rc, out, _ = ln(SYNTH)
    check("the failure block and its traceback are shown", "FAIL: test_x (m.C.test_x)" in out
          and "AssertionError: 1 != 2" in out, out)
    check("the running line ... FAIL is shown", "test_x (m.C.test_x) ... FAIL" in out, out)
    check("the 40 passing lines before it fold to one line", "... 40 lines folded: test_0 " in out, out)
    check("the noise is folded and counted (a fold may quote it; no line of its own)",
          not any(l.startswith(("F:/t.py", "ResourceWarning")) for l in out.splitlines())
          and "noise 2 (folded)" in out, out)
    check("the closing marks are shown", "Ran 61 tests in 1.0s" in out and "FAILED (failures=1)" in out, out)
    b = properties(SYNTH)
    check("the promises hold on a synthetic run", not b, "; ".join(b))

    rc, out, _ = ln("only\n")
    check("a one-line log is shown, not folded", out.startswith("only\n"), out)
    rc, out, _ = ln("")
    check("an empty log says so and exits 0", rc == 0 and "0 lines read" in out, out)
    rc, out, _ = ln("a\r\nFAIL: b\r\r\nprog 10%\rprog 100%\n")
    check("CRLF and CRCRLF lines read as lines (Windows logs)", "FAIL: b\n" in out and "\r" not in out, repr(out))
    check("a \\r inside a line shows what a terminal would", "prog 100%" in out and "prog 10%" not in out, repr(out))

    real = HERE.parent.parent / "records"
    logs = sorted(real.glob("*/make-check-last.log")) if real.is_dir() else []
    if logs:
        text = logs[-1].read_bytes().decode("utf-8", "replace")
        b = properties(text)
        check(f"the promises hold on this seat's own make check log ({logs[-1].parent.name})", not b, "; ".join(b))
    else:
        res.append(("the promises hold on this seat's own make check log", None, "no records/*/make-check-last.log here"))

    p = subprocess.run(["sh", str(TOOL), "--prove-red"], capture_output=True, text=True, encoding="utf-8")
    check("the filter's own planted faults are all caught", p.returncode == 0 and "6 of 6" in p.stdout, p.stdout)
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
    print(f"interesting-lines: {n - bad}/{n} hold" + (f", {len(res) - n} skipped" if len(res) > n else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
