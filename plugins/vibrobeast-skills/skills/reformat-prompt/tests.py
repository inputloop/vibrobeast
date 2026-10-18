#!/usr/bin/env python3
"""pg1lv-spec.py (a skill's tests.py) -- the glove's ledger (scripts/pg1lv, sh and awk) held by a second language.

usage:  python3 tests.py [--prove-red]
--prove-red plants faults in copies of pg1lv; each must turn a case red.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The same file is C4's t/pg1lv-spec.py and each glove skill's tests.py (dropped by bin/dp1rc from
# f/garden/RECIPE.org): the tool and its strings are beside it in a skill, one folder up in C4.
if not (HERE / "scripts" / "pg1lv").exists() and (HERE.parent / "bin" / "pg1lv").exists():
    TOOLHOME, ASSETS = HERE.parent / "bin", HERE.parent / "assets"
else:
    TOOLHOME, ASSETS = HERE / "scripts", HERE / "assets"
NAME = "pg1lv" if TOOLHOME.name == "bin" else HERE.name


def tree():
    """A small C4-shaped tree: q/INDEX-captures.tsv, a file, a git repo with one commit."""
    r = Path(tempfile.mkdtemp()) / "c4"      # a fresh parent, so a repository can sit one folder over
    (r / "q").mkdir(parents=True)
    (r / "q" / "INDEX-captures.tsv").write_text("2026-10-15\tfiled-one\tq/PROMPT-2026-10-15-filed-one.md\t-\t-\tq/2026-10-15-filed-one\tT\n")
    (r / "h").mkdir(); (r / "h" / "PAIR.md").write_text("pair\n")
    g = r / "repo"; g.mkdir()
    env = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@e", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@e"}
    subprocess.run(["git", "init", "-q", str(g)], check=True)
    (g / "a").write_text("a\n")
    subprocess.run(["git", "-C", str(g), "add", "a"], check=True)
    subprocess.run(["git", "-C", str(g), "commit", "-q", "-m", "a"], check=True, env={**__import__("os").environ, **env})
    sha = subprocess.run(["git", "-C", str(g), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return r, r / "q" / "2026-10-15-filed-one" / "STRINGS", sha


def kit(tool):
    """The tool beside its assets, as the skill ships it."""
    d = Path(tempfile.mkdtemp())
    (d / "scripts").mkdir(); (d / "assets").mkdir()
    shutil.copy(tool, d / "scripts" / "pg1lv"); shutil.copy(ASSETS / "strings.default", d / "assets")
    shutil.copy(ASSETS / "handback-checks.sh", d / "assets")
    return d / "scripts" / "pg1lv"


def run(tool, *a, env=None):
    p = subprocess.run(["sh", str(tool), *map(str, a)], capture_output=True, text=True, encoding="utf-8",
                       env={**__import__("os").environ, **(env or {})})
    return p.returncode, p.stdout + p.stderr


def nstrings():
    return sum(1 for l in (ASSETS / "strings.default").read_text().splitlines() if l.strip() and not l.startswith("#"))


def relax_all_but(tool, L, keep):
    for i in range(1, nstrings() + 1):
        if i not in keep:
            run(tool, "relax", L, i, "not this prompt's")


def cases(tool):
    res = []
    def check(name, ok, why=""):
        res.append((name, bool(ok), why))
    N = nstrings()

    r, L, sha = tree()
    rc, out = run(tool, "open", L, "q/PROMPT-2026-10-15-filed-one.md")
    check("P1 open starts every default string taut", rc == 0 and f"{N} string(s), all taut" in out
          and L.read_text().count("[ ] ") == N, out)
    rc, out = run(tool, "state", L)
    check("P1 state says how many are taut and names the next", f"{N} taut" in out and "next taut: in   read the project's own memory" in out, out)
    rc, out = run(tool, "owe", L, "out", "tell Bryant")
    check("P2 owe adds a numbered string", rc == 0 and f"string {N + 1} taut" in out, out)
    rc, out = run(tool, "close", L)
    check("P8 close refuses while anything is taut, and names what", rc == 1 and "still taut" in out and "tell Bryant" in out, out)
    rc, out = run(tool, "pull", L, 1)
    check("P7 a pull with no receipt is refused", rc == 2 and "receipt" in out, out)
    rc, out = run(tool, "relax", L, 2)
    check("P7 a relax with no reason is refused", rc == 2 and "reason" in out, out)
    rc, out = run(tool, "pull", L, 99, "said:x")
    check("P12 a string that does not exist is an error", rc == 2 and "no string 99" in out, out)

    run(tool, "pull", L, 1, "said:read preferences.md")
    run(tool, "pull", L, 4, "q:filed-one")   # 4, not 3: this ledger has no egg, so its egg string cannot be pulled (P22)
    run(tool, "pull", L, 5, "file:h/PAIR.md")
    run(tool, "pull", L, 8, f"git:repo@{sha}")
    relax_all_but(tool, L, {1, 4, 5, 8})
    run(tool, "relax", L, N + 1, "he tells Bryant himself")
    rc, out = run(tool, "close", L)
    check("P3 close holds when nothing is taut and every receipt holds", rc == 0 and "nothing further owed" in out
          and "holds  file:h/PAIR.md" in out and "holds  q:filed-one" in out and f"holds  git:repo@{sha}" in out, out)
    check("P10 a said receipt is counted, never claimed as checked", "said   said:read preferences.md (counted, not checked)" in out
          and "1 said and not checked" in out, out)
    rc, out = run(tool, "pull", L, 2, "said:late")
    check("P13 a closed ledger keeps its strings as they were", rc == 2 and "closed" in out, out)
    rc, out = run(tool, "drift", L)
    check("P11 drift says closed, with the counts", "closed" in out and "0 taut" in out, out)

    for kind, rec, word in (("file", "file:h/NOT-THERE.md", "no such file"), ("git", "git:repo@" + "0" * 40, "no such commit"),
                            ("q", "q:never-filed", "not in q/INDEX-captures.tsv")):
        r, L, sha = tree(); run(tool, "open", L)
        run(tool, "pull", L, 1, rec); relax_all_but(tool, L, {1})
        rc, out = run(tool, "close", L)
        check(f"P4 a {kind} receipt that does not hold stops the close", rc == 1 and word in out and "# closed" not in L.read_text(), out)

    r, L, sha = tree(); (r / "q" / "PROMPT-2026-10-15-filed-one.md").write_text("what he asked\n")
    rc, out = run(tool, "open", L, "q/PROMPT-2026-10-15-filed-one.md")
    check("P15 open lays the egg: the captured prompt's hash", "# egg: " in L.read_text() and "q/PROMPT-2026-10-15-filed-one.md" in L.read_text(), L.read_text())
    relax_all_but(tool, L, set())
    (r / "q" / "PROMPT-2026-10-15-filed-one.md").write_text("what he asked, edited later\n")
    rc, out = run(tool, "close", L)
    check("P15 close refuses when the capture changed after intake", rc == 1 and "changed after intake" in out and "# closed" not in L.read_text(), out)
    (r / "q" / "PROMPT-2026-10-15-filed-one.md").write_text("what he asked\n")
    rc, out = run(tool, "close", L)
    check("P15 and closes when it is what was asked", rc == 0 and "unchanged since intake" in out, out)
    r2, L2, _ = tree(); run(tool, "open", L2)
    p = subprocess.run(["sh", str(tool), "resume", str(L), str(L2)], capture_output=True, text=True)
    check("P16 resume names each open ledger and its next taut string, and skips closed ones",
          str(L2) in p.stdout and "next: in   read the project" in p.stdout and str(L) not in p.stdout, p.stdout)

    r, L, sha = tree(); run(tool, "open", L)
    (r.parent / "AS4CE").mkdir(); shutil.move(str(r / "repo"), str(r.parent / "AS4CE" / "seat"))
    run(tool, "pull", L, 1, f"git:seat@{sha}"); relax_all_but(tool, L, {1})
    rc, out = run(tool, "close", L)
    check("P14 a git receipt can name a repository one folder over, so it reads the same from any shell",
          rc == 0 and f"holds  git:seat@{sha}" in out, out)

    r, L, sha = tree(); run(tool, "open", L); run(tool, "pull", L, 1, "said:x")
    rc, out = run(tool, "bail", L, "the session ran out")
    t = L.read_text()
    check("P9 bail marks every taut string bailed, with the reason", rc == 0 and t.count("[!] ") == N - 1
          and t.count("-- bailed: the session ran out") == N - 1 and "[ ] " not in t, out)
    rc, out = run(tool, "drift", L)
    check("P9 drift says bailed", "bailed" in out and f"{N - 1} bailed" in out, out)

    # 2026-10-16: the hand-back as questions, delegated to skills, answered by named checks
    r, L, sha = tree(); run(tool, "open", L)
    run(tool, "owe", L, "out", "a thing with a skill and no question  @run-card")
    rc, out = run(tool, "ask", L)
    check("P17 ask puts each taut string as a question, with the skills it delegates to and its checks",
          rc == 0 and "Did you leave anything behind for someone else to ask about?" in out
          and "delegates to: inculcat-boxer run-card" in out and "!debris !strays !layout !home" in out, out)
    check("P17 a string with a skill and no question still reads as a question (no field collapses)",
          f"{N + 1}. Did you see to this: a thing with a skill and no question?" in out and "delegates to: run-card" in out, out)
    fx = r.parent / "fx-checks.sh"; flag = r.parent / "flag"
    fx.write_text('hb_ok() { [ -f "%s" ] && { echo fine; return 0; }; echo gone; return 1; }\n'
                  'hb_ask() { echo a person decides; return 3; }\n'
                  'hb_bad() { echo left a mess; return 1; }\n' % flag)
    flag.write_text("x")
    E = {"PG1LV_CHECKS": str(fx)}
    r, L, sha = tree(); run(tool, "open", L); relax_all_but(tool, L, set())
    run(tool, "owe", L, "out", "one  !ok"); run(tool, "owe", L, "out", "two  !ok  !ask"); run(tool, "owe", L, "out", "three  !bad")
    rc, out = run(tool, "check", L, env=E)
    check("P18 check runs each taut string's named checks and says OK, ASK or FAULT", rc == 1 and "OK     !ok  fine" in out
          and "ASK    !ask  a person decides" in out and "FAULT  !bad  left a mess" in out, out)
    rc, out = run(tool, "check", L, "--pull", env=E)
    t = L.read_text()
    check("P18 --pull pulls only a string whose checks all say OK, with a check: receipt", "[x] out  one  !ok -- check:ok" in t
          and "[ ] out  two" in t and "[ ] out  three" in t, t)
    run(tool, "relax", L, N + 2, "not tonight"); run(tool, "relax", L, N + 3, "not tonight")
    flag.unlink()
    rc, out = run(tool, "close", L, env=E)
    check("P18 close re-runs a check: receipt, and it holds only if the check still says OK", rc == 1
          and "FAILS  check:ok" in out and "# closed" not in L.read_text(), out)
    flag.write_text("x")
    rc, out = run(tool, "close", L, env=E)
    check("P18 and closes once it does", rc == 0 and "holds  check:ok (re-run now: OK)" in out, out)
    r, L, sha = tree(); run(tool, "open", L); relax_all_but(tool, L, set())
    boom = r.parent / "BOOM"
    run(tool, "owe", L, "out", "x  !ok;touch%s" % boom); run(tool, "owe", L, "out", "y  !nosuch")
    rc, out = run(tool, "check", L, env=E)
    check("P19 a ledger names a check and cannot bring one: a bad name is refused, an unknown one faults",
          rc == 1 and not boom.exists() and "a check name is lowercase" in out and "FAULT  !nosuch  no such check" in out, out)
    r, L, sha = tree(); run(tool, "open", L)
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    lock = r / ".git" / "index.lock"; __import__("time").sleep(1.1); lock.write_text("")
    (r / "stray.md").write_text("left\n")
    rc, out = run(tool, "check", L)
    check("P20 the shipped checks see git debris and new untracked files since the ledger opened",
          "FAULT  !debris" in out and "index.lock" in out and "ASK    !strays" in out and "stray.md" in out, out)
    r, L, sha = tree(); subprocess.run(["git", "init", "-q", str(r)], check=True); run(tool, "open", L)
    run(tool, "pull", L, 1, "git:c4@" + sha); relax_all_but(tool, L, {1}); run(tool, "owe", L, "out", "z  !debris")
    rc, out = run(tool, "check", L)
    check("P21 a repository named by a receipt and also the root is looked at once", "left in 1 repository" in out, out)

    # P22 (2026-10-18): no egg, no claim to have laid one. modelthisbook's selfcheck ledger said "egg: none" and
    # still had its egg string pulled.
    r, L, sha = tree(); run(tool, "open", L, "q/NOT-CAPTURED.md")
    rc, out = run(tool, "pull", L, 3, "file:h/PAIR.md")
    check("P22 with no egg, the egg string cannot be pulled", rc == 2 and "no egg" in out and "[ ] in   capture" in L.read_text(), out)
    rc, out = run(tool, "relax", L, 3, "captured late, after the first write")
    check("P22 with no egg, the egg string can be relaxed with its reason", rc == 0 and "[~] in   capture" in L.read_text(), out)
    relax_all_but(tool, L, {3})
    L.write_text(L.read_text().replace("[~] in   capture", "[x] in   capture"))   # a hand-edit past the guard
    rc, out = run(tool, "close", L)
    check("P22 close refuses a ledger with no egg whose egg string is pulled", rc == 1 and "no egg" in out and "# closed" not in L.read_text(), out)
    return res


PLANTS = [
    ("close ignores taut strings", 'if [ -n "$taut" ]; then', "if false; then"),
    ("a file receipt always holds", 'if [ -e "$f" ]; then', "if true; then"),
    ("a git receipt always holds", 'if git -C "$repo" cat-file -e "$sha^{commit}" 2>/dev/null; then', "if true; then"),
    ("a relax needs no reason", '[ -n "$x" ] || {', "true || {"),
    ("bail drops taut strings silently", 's/^\\[ \\] \\(.*\\)$/[!] \\1 -- bailed: ', "s/^\\[ \\] \\(.*\\)$/[x] \\1 -- said:"),
    ("the egg is never checked", '[ "$now_h" = "$eh" ] || {', 'true || {'),
    ("said is claimed as checked", 'echo "  said   $rc (counted, not checked)"', 'echo "  holds  $rc"'),
    ("a check: receipt always holds", 'if runchecks $names >/dev/null; then', "if true; then"),
    ("a ledger can bring a command", "case \"$_c\" in *[!a-z0-9-]*|'') echo", "case \"$_c\" in '') echo"),
    ("an empty field collapses", "US=$(printf '\\037')", "US=$(printf '\\t')"),
    ("the root is counted twice", "done; done; } | awk '!seen[$0]++'; }", "done; done; } | cat; }"),
    ("an egg string pulled with no egg", "if [ \"$cmd\" = pull ] && grep -q '^# egg: none' \"$L\"", "if false"),
    ("close takes a pulled egg string with no egg", "if grep -q '^# egg: none' \"$L\" && grep -q", "if false && grep -q"),
    ("--pull pulls past an ASK", 'if [ $rc = 0 ] && [ $pullok = 1 ]; then', 'if [ $rc != 1 ] && [ $pullok = 1 ]; then'),
]


def prove_red():
    src = (TOOLHOME / "pg1lv").read_text(encoding="utf-8"); caught = 0
    for name, old, new in PLANTS:
        if src.count(old) != 1:
            print(f"  NOT PLANTED  {name} (the tool changed shape)"); continue
        d = Path(tempfile.mkdtemp()); t = d / "pg1lv"; t.write_text(src.replace(old, new), encoding="utf-8")
        bad = [r for r in cases(kit(t)) if not r[1]]
        print(f"  {'caught' if bad else 'MISSED'}  {name}" + (f"  (by: {bad[0][0]})" if bad else ""))
        caught += bool(bad)
    print(f"{NAME} --prove-red: {caught} of {len(PLANTS)} planted faults caught")
    return 0 if caught == len(PLANTS) else 1


def main():
    if "--prove-red" in sys.argv:
        return prove_red()
    res = cases(kit(TOOLHOME / "pg1lv")); bad = 0
    for name, ok, why in res:
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -- {why.strip()[:400]}"))
    print(f"{NAME}: {len(res) - bad}/{len(res)} hold")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
