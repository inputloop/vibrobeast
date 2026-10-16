#!/usr/bin/env python3
"""tests.py -- session-rotate's gate, held by a second language (Python reads the sh script).

The rotate's step 0 is the close check (C4's bin/ow1ed).  Since 2026-10-15 the script holds it: an
--apply needs ow1ed's RECEIPT (a token only a run can make; ow1ed --verify re-runs it) and ow1ed must
owe nothing but the rotate, or the session says why with --ungated, which is written down.  Every
refusal must leave the project untouched.  The receipt cases use the real bin/ow1ed from C4
($C4_ROOT, /f/claude/c4 or ~/mnt/c4); without it they skip and say so.
--prove-red plants five faults in a copy of the script; each must turn a case red.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scripts" / "rotate_session.sh"


def find_ow1ed():
    for d in (os.environ.get("C4_ROOT", ""), "/f/claude/c4", str(Path.home() / "mnt" / "c4"),
              str(HERE.parent.parent.parent / "c4")):
        if d and Path(d, "bin", "ow1ed").is_file():
            return Path(d, "bin", "ow1ed")
    return None


def put(p, text=""):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def project(t):
    pr = Path(t, "proj")
    put(pr / "model.md", "# model\nversion: v3\n\nbody\n")
    put(pr / ".last-prompt.md", "# the last prompt\n")
    put(pr / "last-response.md", "# the last response\n")
    return pr


def c4tree(t, ow1ed, kind="clean"):
    """A C4 tree ow1ed can read.  kind: clean (owes nothing), rotate (owes the rotate only),
    record (owes a file the record does not name, too)."""
    c = Path(t, "c4")
    (c / "bin").mkdir(parents=True)
    shutil.copy(ow1ed, c / "bin" / "ow1ed")
    put(c / "MEMORY.md", "## 2026-01-02 names ow1ed SWING-A QA-A.md REPORT-A.md FLOOR.md later.md\n")   # the copied tool is a file too
    put(c / "h" / "P" / "SWING-A", "state: DONE\n")
    put(c / "h" / "P" / "QA-A.md")
    put(c / "h" / "P" / "REPORT-A.md")
    put(c / "h" / "P" / "FLOOR.md")
    if kind == "clean":
        put(c / "last-response.md")
        put(c / ".last-prompt.md")
    else:
        put(c / "last-response.md")
        put(c / ".last-prompt.md")
        time.sleep(1.1)
        put(c / "h" / "Q" / "later.md")          # newer than the continuity files: a rotate is owed
        if kind == "record":
            put(c / "h" / "Q" / "nobody-named-me.md")
    return c


def receipt(c):
    p = subprocess.run(["sh", str(c / "bin" / "ow1ed"), "--since", "2026-01-01", "--receipt"],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, C4_ROOT=str(c)))
    line = [l for l in p.stdout.splitlines() if l.startswith("RECEIPT ")]
    return line[-1].split()[1] if line else ""


def rotate(script, pr, *args, c4=None):
    env = dict(os.environ)
    env.pop("C4_ROOT", None)
    argv = ["sh", str(script), "--project", str(pr), *args]
    if c4 is not None:
        argv += ["--c4", str(c4)]
    p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", env=env)
    return p.returncode, p.stdout + p.stderr


def untouched(pr):
    return not (pr / ".models").exists() and not (pr / ".sessions").exists() \
        and (pr / "model.md").read_text(encoding="utf-8").count("v3") == 1


def cases(script, ow1ed):
    res = []

    def check(name, ok, why=""):
        res.append((name, bool(ok), why))

    t = tempfile.mkdtemp()
    pr = project(t)
    rc, out = rotate(script, pr)
    check("G1 a dry run needs no receipt and shows the gate in its plan",
          rc == 0 and "the close check: needs --after" in out and untouched(pr), out[-300:])
    check("G1 the plan lists step 0 first, as it runs (it printed after step 4 until 2026-10-15)",
          0 <= out.find("   0. the close check") < out.find("   1. snapshot"), out[-300:])
    rc, out = rotate(script, pr, "--apply")
    check("G2 an apply with no receipt and no reason is refused, nothing written",
          rc == 5 and "REFUSED" in out and untouched(pr), out[-300:])

    if ow1ed is None:
        for n in ("G3", "G4", "G5", "G6", "G7"):
            res.append((f"{n} (receipt cases)", None, "C4's bin/ow1ed not found"))
    else:
        t = tempfile.mkdtemp(); pr = project(t); c = c4tree(t, ow1ed, "clean")
        tok = receipt(c)
        forged = tok.rsplit(":", 1)[0] + ":" + "0" * 32
        rc, out = rotate(script, pr, "--apply", "--after", forged, c4=c)
        check("G3 an invented receipt is refused, nothing written", rc == 5 and untouched(pr), out[-300:])
        rc, out = rotate(script, pr, "--apply", "--after", tok, c4=c)
        gate = next(Path(pr, ".sessions").glob("*/GATE.txt"), None) if Path(pr, ".sessions").exists() else None
        check("G4 a genuine receipt on a tree that owes nothing rotates, and the receipt is recorded",
              rc == 0 and gate is not None and tok in gate.read_text(encoding="utf-8")
              and "verified" in gate.read_text(encoding="utf-8"), out[-300:])

        t = tempfile.mkdtemp(); pr = project(t); c = c4tree(t, ow1ed, "rotate")
        rc, out = rotate(script, pr, "--apply", "--after", receipt(c), c4=c)
        check("G5 a receipt that owes only the rotate rotates", rc == 0, out[-300:])

        t = tempfile.mkdtemp(); pr = project(t); c = c4tree(t, ow1ed, "record")
        rc, out = rotate(script, pr, "--apply", "--after", receipt(c), c4=c)
        check("G6 a genuine receipt that owes more than the rotate is refused, and names what",
              rc == 5 and "nobody-named-me.md" in out and untouched(pr), out[-300:])

        t = tempfile.mkdtemp(); pr = project(t); c = c4tree(t, ow1ed, "clean")
        tok = receipt(c)
        put(c / "h" / "P" / "made-after-the-receipt.md")
        rc, out = rotate(script, pr, "--apply", "--after", tok, c4=c)
        check("G7 a receipt made before the tree moved is refused", rc == 5 and untouched(pr), out[-300:])

    t = tempfile.mkdtemp(); pr = project(t)
    rc, out = rotate(script, pr, "--apply", "--ungated", "no C4 on this machine")
    gate = next(Path(pr, ".sessions").glob("*/GATE.txt"), None) if Path(pr, ".sessions").exists() else None
    check("G8 --ungated rotates and writes down why the check did not run",
          rc == 0 and gate is not None and "NOT RUN" in gate.read_text(encoding="utf-8")
          and "no C4 on this machine" in gate.read_text(encoding="utf-8"), out[-300:])
    def gitproj(t):
        pr = project(t)
        env = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@e", GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@e")
        for c in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "start"]):
            subprocess.run(c, cwd=pr, env=env, capture_output=True)
        put(pr / "other.txt", "someone else's work\n")
        subprocess.run(["git", "add", "other.txt"], cwd=pr, capture_output=True)
        return pr, env

    def gitrun(pr, *a):
        return subprocess.run(["git", *a], cwd=pr, capture_output=True, text=True).stdout

    t = tempfile.mkdtemp(); pr, env = gitproj(t)
    p = subprocess.run(["sh", str(script), "--project", str(pr), "--apply", "--ungated", "the tests"],
                       capture_output=True, text=True, env=env)
    out = p.stdout + p.stderr
    files = gitrun(pr, "show", "--name-only", "--format=", "HEAD").split()
    check("G9 a verified apply in a git repository commits the rotate's own files, naming the gate",
          p.returncode == 0 and "[ok] committed" in out and "model.md" in files and any(f.startswith(".sessions/") for f in files)
          and "NOT RUN (--ungated) -- the tests" in gitrun(pr, "log", "-1", "--format=%B"), out[-300:])
    check("G9 and nothing else: work someone had staged stays staged, uncommitted",
          "other.txt" not in files and "other.txt" in gitrun(pr, "diff", "--cached", "--name-only"), out[-300:])

    t = tempfile.mkdtemp(); pr, env = gitproj(t)
    head0 = gitrun(pr, "rev-parse", "HEAD")
    p = subprocess.run(["sh", str(script), "--project", str(pr), "--apply", "--ungated", "x", "--no-commit"],
                       capture_output=True, text=True, env=env)
    check("G10 --no-commit rotates and commits nothing", p.returncode == 0 and gitrun(pr, "rev-parse", "HEAD") == head0
          and "not committed (--no-commit)" in p.stdout, p.stdout[-300:])

    t = tempfile.mkdtemp(); pr = project(t)
    rc, out = rotate(script, pr, "--apply", "--ungated", "x")
    check("G11 outside git, the rotate says its snapshot is the kept copy", rc == 0 and "is the kept copy" in out, out[-300:])
    return res


PLANTS = [
    ("the commit takes everything staged", 'git commit -q -m "rotate: $what" -m "$GATELINE" -- $paths', 'git commit -q -m "rotate: $what" -m "$GATELINE"'),
    ("step 0 listed last", 'echo "  PLAN:"\n', 'echo "  PLAN:"\necho "   1. snapshot"\n'),
    ("no receipt asked for", "  echo \"REFUSED: an apply needs the close check's receipt",
     "  GATELINE=planted; : \"REFUSED: an apply needs the close check's receipt"),
    ("the owed list ignored", "others=$(printf '%s\\n' \"$vout\" | grep '^OWED' | grep -v 'a rotate is owed' || true)",
     "others=\"\""),
    ("a failed verify let through", "vrc=0; vout=$(sh \"$C4/bin/ow1ed\" --verify \"$AFTER\" 2>&1) || vrc=$?",
     "vrc=0; vout=$(sh \"$C4/bin/ow1ed\" --verify \"$AFTER\" 2>&1) || vrc=0"),
]


def prove_red(ow1ed):
    src = SCRIPT.read_text(encoding="utf-8")
    caught = 0
    for name, old, new in PLANTS:
        if src.count(old) != 1:
            print(f"  NOT PLANTED  {name} (the script changed shape)")
            continue
        d = Path(tempfile.mkdtemp())
        planted = d / "rotate_session.sh"
        txt = src.replace(old, new)
        if name == "no receipt asked for":   # the plant must also skip the exit that follows the message
            txt = txt.replace("  echo \"         and pass its token with --after; or say why it cannot run here with --ungated 'WHY'.\" >&2\n  exit 5",
                              "  : planted")
        planted.write_text(txt, encoding="utf-8", newline="\n")
        bad = [r for r in cases(planted, ow1ed) if r[1] is False]
        if bad:
            caught += 1
            print(f"  caught  {name}  (by: {bad[0][0]})")
        else:
            print(f"  MISSED  {name}")
    print(f"session-rotate --prove-red: {caught} of {len(PLANTS)} planted faults caught")
    return 0 if caught == len(PLANTS) else 1


def main():
    ow1ed = find_ow1ed()
    if "--prove-red" in sys.argv:
        return prove_red(ow1ed)
    res = cases(SCRIPT, ow1ed)
    bad = 0
    for name, ok, why in res:
        mark = "skip" if ok is None else ("ok  " if ok else "FAIL")
        bad += ok is False
        print(f"  {mark}  {name}" + (f"  -- {why.strip()[:300]}" if ok is not True and why else ""))
    n = sum(1 for r in res if r[1] is not None)
    print(f"session-rotate: {n - bad}/{n} hold" + (f", {len(res) - n} skipped" if len(res) > n else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
