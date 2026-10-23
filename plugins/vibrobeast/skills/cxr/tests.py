#!/usr/bin/env python3
"""tv1cr-spec.py -- the CxR unfolder (bin/tv1cr, POSIX sh + awk) held by a second author, on
throwaway tables in temporary folders; nothing in the tree is touched.

usage:  python3 t/tv1cr-spec.py [--prove-red] [--tool PATH] [--lab PATH]
--prove-red plants faults in copies of the tool; each must turn at least one case red.
--lab       append this run's row to a lab ledger (the from-scratch worked example) through the
            tool itself: `tv1cr set` into the ledger's stem, then `tv1cr fold` to its TSV.
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  Mentat (for Corwin).
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os, platform, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "scripts" / "tv1cr"            # as a skill's tests.py (dropped by dp1rc)
if not TOOL.exists():
    TOOL = HERE.parent / "bin" / "tv1cr"     # at home in C4, as t/tv1cr-spec.py
if "--tool" in sys.argv:
    TOOL = Path(sys.argv[sys.argv.index("--tool") + 1]).resolve()
RESULTS = []


def run(tool, *args, stdin=None):
    p = subprocess.run(["sh", str(tool)] + [str(a) for a in args], capture_output=True, input=stdin)
    return p.returncode, p.stdout, p.stderr


def case(name, ok, note=""):
    RESULTS.append((name, bool(ok), note))


def fresh():
    return Path(tempfile.mkdtemp(prefix="tv1cr-"))


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


HEADED = (b"# cols: id state sense\n# second note line\twith a tab\n"
          b"id\tstate\tsense\n"
          b"q1\tOPEN\tfirst, with a space\n"
          b"q2\t\tSeam/seam %\n"
          b"q3\tDEFAULTED\tnon-ascii \xc2\xb7 middle dot\n"
          b"q4\tRULED\t" + b"x" * 300 + b"\n")
BARE = (b"# terms-of-art shaped: no header row\n"
        b"seam\tCorwin-verbatim\tpinned\n"
        b"pin\tCorwin-verbatim\tpinned\n"
        b"deck\ttree\tpinned\n")


def spec(tool):
    # 1. round trip, headed, with notes and the awkward bytes
    t = fresh(); write(t / "x.tsv", HEADED)
    rc, out, err = run(tool, "unfold", t / "x.tsv")
    case("unfold headed exits 0", rc == 0, err.decode())
    rc, out, _ = run(tool, "fold", t / "x")
    case("fold reproduces the headed table byte for byte", out == HEADED)
    case("the note lands in n, verbatim, tabs kept", (t / "x/n").read_bytes() == b"# cols: id state sense\n# second note line\twith a tab\n")
    case("the header lands in t", (t / "x/t").read_bytes() == b"id\tstate\tsense\n")
    case("l holds the columns in order", (t / "x/l").read_text() == "id\nstate\nsense\n")
    case("i names the key column (first, unsaid)", (t / "x/i").read_text() == "id\n")
    case("a holds the keys in row order", (t / "x/a").read_text() == "q1\nq2\nq3\nq4\n")
    # 2. the four atoms of an empty cell
    case("an empty cell is a zero-byte r atom", (t / "x/r/q2/state").exists() and (t / "x/r/q2/state").stat().st_size == 0)
    case("an empty value is the member % in c/", (t / "x/c/state/%").read_text() == "q2\n")
    # 3. names: case folded, bytes escaped, long capped
    case("an upper-case run is ^run^ (case-safe on a folding disk)", (t / "x/c/state/^open^").exists() and (t / "x/c/state/^defaulted^").exists())
    case("/ space % are escaped", (t / "x/c/sense/^s^eam%2Fseam%20%25").read_text() == "q2\n")
    case("a non-ascii byte is escaped by byte", (t / "x/c/sense/non-ascii%20%C2%B7%20middle%20dot").exists())
    longs = [p.name for p in (t / "x/c/sense").iterdir() if "%~" in p.name]
    case("a long value's member name is capped and ends in %~sha16", len(longs) == 1 and len(longs[0]) == 198 and re.search(r"%~[0-9a-f]{16}$", longs[0]))
    case("the long value itself is whole in r/", (t / "x/r/q4/sense").read_bytes() == b"x" * 300 + b"\n")
    rc, out, _ = run(tool, "enc", "Seam/seam %")
    case("enc (sh) agrees with the awk encoder on the member name", out == b"^s^eam%2Fseam%20%25\n")
    rc, out, _ = run(tool, "enc", "")
    case("enc of the empty string is %", out == b"%\n")
    # 4. check holds on a fresh unfold; who; get
    rc, out, _ = run(tool, "check", t / "x")
    case("check holds after unfold", rc == 0 and b"holds" in out, out.decode())
    rc, out, _ = run(tool, "who", t / "x", "state", "")
    case("who finds the key carrying the empty value", out == b"q2\n")
    rc, out, _ = run(tool, "get", t / "x", "q1", "sense")
    case("get reads a cell", out == b"first, with a space\n")
    rc, out, _ = run(tool, "get", t / "x", "q3")
    case("get with no column prints every column", out == b"id\tq3\nstate\tDEFAULTED\nsense\tnon-ascii \xc2\xb7 middle dot\n")
    # 5. set: two writers, the trampled value kept, member emptied, check holds
    rc, out, err = run(tool, "set", t / "x", "q2", "state", "RULED")
    case("set exits 0", rc == 0, err.decode())
    case("set wrote r", (t / "x/r/q2/state").read_text() == "RULED\n")
    case("set wrote c", "q2\n" in (t / "x/c/state/^ruled^").read_text())
    case("set emptied the old member file (never rm: the mount cannot)", (t / "x/c/state/%").read_text() == "")
    kept = list((t / "x/d").glob("*/r/q2/state"))
    case("set kept the trampled value under d/<stamp>/", len(kept) == 1 and kept[0].stat().st_size == 0)
    rc, out, _ = run(tool, "check", t / "x")
    case("check holds after set", rc == 0, out.decode())
    rc, out, err = run(tool, "set", t / "x", "q9", "state", "OPEN")
    case("set on a new key appends to a and writes the key cell", (t / "x/a").read_text().endswith("q9\n") and (t / "x/r/q9/id").read_text() == "q9\n" and (t / "x/c/id/q9").read_text() == "q9\n")
    rc, out, _ = run(tool, "fold", t / "x")
    case("fold after set shows the new row with empty cells unsaid", out.endswith(b"q9\tOPEN\t\n"))
    rc, out, _ = run(tool, "set", t / "x", "q1", "nope", "v")
    case("set refuses a column not in l", rc != 0)
    rc, out, _ = run(tool, "col", t / "x", "since")
    case("col adds a column to l and extends t", (t / "x/l").read_text().endswith("since\n") and (t / "x/t").read_text() == "id\tstate\tsense\tsince\n")
    rc, out, _ = run(tool, "fold", t / "x", "--where", "state=OPEN")
    case("fold --where keeps the matching rows only", out.count(b"\n") == 2 + 1 + 2 and b"q1\t" in out and b"q9\t" in out and b"q3\t" not in out, out.decode())
    # 6. stale
    rc, out, _ = run(tool, "stale", t / "x", t / "x.tsv")
    case("stale says stale after set (an atom is newer than the TSV)", rc == 1)
    time.sleep(1.1)
    rc, out, err = run(tool, "fold", t / "x", "--to", t / "x.tsv")
    rc2, out2, _ = run(tool, "stale", t / "x", t / "x.tsv")
    case("fold --to writes the TSV, marks s, and stale then says fresh", rc == 0 and rc2 == 0 and (t / "x/s").exists() and (t / "x.tsv").read_bytes().endswith(b"q9\tOPEN\t\t\n"), out2.decode() + err.decode())
    rc, out, err = run(tool, "fold", t / "x", "--to", t / "y.tsv", "--where", "state=OPEN")
    case("fold --to refuses a --where view", rc != 0)
    # 7. check faults, each named by path
    write(t / "x/c/state/^open^", (t / "x/c/state/^open^").read_bytes() + b"q77\n")
    rc, out, _ = run(tool, "check", t / "x")
    case("check faults a one-sided c write and names it", rc == 1 and b"q77" in out and b"c/state/^open^" in out, out.decode())
    write(t / "x/c/state/^open^", b"q1\nq9\n")
    write(t / "x/r/q1/state", b"RULED\n")
    rc, out, _ = run(tool, "check", t / "x")
    case("check faults a one-sided r write and names it", rc == 1 and b"r/q1/state" in out, out.decode())
    write(t / "x/r/q1/state", b"OPEN\n")
    write(t / "x/a", (t / "x/a").read_bytes() + b"ghost\n")
    rc, out, _ = run(tool, "check", t / "x")
    case("check faults a key in a with no r/ dir", rc == 1 and b"ghost" in out)
    # the one-pass check and the per-atom one (--each) name the same faults, as sets of lines
    write(t / "x/c/state/^open^", (t / "x/c/state/^open^").read_bytes() + b"q78\n")
    write(t / "x/r/q1/state", b"RULED\n")
    _, one, _ = run(tool, "check", t / "x")
    _, each, _ = run(tool, "check", t / "x", "--each")
    fs = lambda o: sorted(l for l in o.decode().splitlines() if l.startswith("FAULT"))
    case("check and check --each name the same faults", fs(one) == fs(each) and len(fs(one)) >= 3, (fs(one), fs(each)))
    write(t / "x/r/q1/state", b"OPEN\n")
    # a table a .cxr-hold line holds is refused, with the reason; --held-anyway unfolds it
    th = fresh(); write(th / "p.tsv", b"k\tv\na\t1\n"); write(th / ".cxr-hold", b"p.tsv\tthe keeper edits it by hand\n")
    rc, out, err = run(tool, "unfold", th / "p.tsv")
    rc2, _, _ = run(tool, "unfold", th / "p.tsv", "--held-anyway")
    case("unfold refuses a held table and says why; --held-anyway unfolds it", rc != 0 and b"edits it by hand" in err and rc2 == 0 and (th / "p/r").is_dir(), (rc, err.decode()[-120:], rc2))
    # 8. refusals
    t2 = fresh()
    write(t2 / "d.tsv", b"a\tb\n1\t2\n1\t3\n")
    rc, out, err = run(tool, "unfold", t2 / "d.tsv")
    case("a duplicate key is refused, naming it", rc != 0 and b"duplicate key" in err and b": 1" in err)
    write(t2 / "r.tsv", b"a\tb\n1\t2\t3\n")
    rc, out, err = run(tool, "unfold", t2 / "r.tsv")
    case("a ragged row is refused, naming the line", rc != 0 and b"ragged" in err and b"line 2" in err)
    write(t2 / "c.tsv", b"a\tb\n1\t2\n# no\n3\t4\n")
    rc, out, err = run(tool, "unfold", t2 / "c.tsv")
    case("a comment between rows is refused, naming its line", rc != 0 and b"comment" in err and b"line 3" in err, err.decode())
    # 2026-10-20, found on real tables (pmo epmo-keys.tsv; c4-serve ollama-known.tsv): see t/tv1cr-corpus.rb
    write(t2 / "h.tsv", b"garden\tfingerprint\n# a note under the header\ncorwin\tAAAA\n")
    rc, out, err = run(tool, "unfold", t2 / "h.tsv")
    case("a comment between the header and the first row is refused (fold would hoist it)", rc != 0 and b"between the header" in err, err.decode())
    write(t2 / "dot.tsv", b"k\tv\na\t.\nb\t..\nc\tx\n")
    rc, out, err = run(tool, "unfold", t2 / "dot.tsv")
    rc2, out2, err2 = run(tool, "fold", t2 / "dot")
    case("a value of . or .. is a member file, not a folder, and folds back", rc == 0 and out2 == b"k\tv\na\t.\nb\t..\nc\tx\n" and (t2 / "dot/c/v/%2E%2E").read_text() == "b\n", err.decode())
    write(t2 / "s.tsv", b"first col\tv\nx\t1\ny\t2\n")
    rc, out, err = run(tool, "unfold", t2 / "s.tsv")
    rc2, out2, err2 = run(tool, "fold", t2 / "s")
    case("a key column whose name holds a space unfolds and folds back", rc == 0 and out2 == b"first col\tv\nx\t1\ny\t2\n", err.decode())
    write(t2 / "b.tsv", b"a\tb\n1\t2\n\n")
    rc, out, err = run(tool, "unfold", t2 / "b.tsv")
    case("a blank line inside the table is refused", rc != 0 and b"blank" in err)
    write(t2 / "k.tsv", b"a\tb\n1\t2\n")
    rc, out, err = run(tool, "unfold", t2 / "k.tsv", "--key", "zz")
    case("--key naming no column is refused", rc != 0 and b"--key" in err)
    rc, out, err = run(tool, "unfold", t2 / "k.tsv")
    rc, out, err = run(tool, "unfold", t2 / "k.tsv")
    case("a stem already holding a table is refused without --replace", rc != 0 and b"--replace" in err)
    rc, out, err = run(tool, "unfold", t2 / "k.tsv", "--replace")
    arch = list((t2 / "k/d").glob("*/r/1/b"))
    case("--replace archives the prior table under d/<stamp>/", rc == 0 and len(arch) == 1)
    # 9. bare (no header) with --cols and a non-first key
    t3 = fresh(); write(t3 / "terms.tsv", BARE)
    rc, out, err = run(tool, "unfold", t3 / "terms.tsv", "--cols", "term,definer,status")
    case("--cols unfolds a headerless table", rc == 0 and not (t3 / "terms/t").exists() and (t3 / "terms/l").read_text() == "term\ndefiner\nstatus\n", err.decode())
    rc, out, _ = run(tool, "fold", t3 / "terms")
    case("fold of a headerless table prints no header", out == BARE)
    rc, out, _ = run(tool, "who", t3 / "terms", "definer", "Corwin-verbatim")
    case("a column is a collection: who lists every key carrying the value", out == b"seam\npin\n")
    write(t3 / "k2.tsv", b"n\tname\n1\tone\n2\ttwo\n")
    rc, out, err = run(tool, "unfold", t3 / "k2.tsv", "--key", "name")
    case("--key picks a non-first column", rc == 0 and (t3 / "k2/i").read_text() == "name\n" and (t3 / "k2/r/one/n").read_text() == "1\n")
    # 9b. a composite key (terms-of-art has 7 terms with two senses: LC is law and feature)
    write(t3 / "c.tsv", b"term\tdisp\tsense\nLC\tlaw\tliterate\nLC\tfeature\tlearning\npin\tcanon\ta pin\n")
    rc, out, err = run(tool, "unfold", t3 / "c.tsv", "--key", "term,disp")
    case("--key a,b unfolds a table unique only on two columns", rc == 0 and (t3 / "c/i").read_text() == "term\ndisp\n" and (t3 / "c/r/^lc^+law/sense").read_text() == "literate\n", err.decode())
    case("a composite key is tab-joined in a", (t3 / "c/a").read_text() == "LC\tlaw\nLC\tfeature\npin\tcanon\n")
    case("the key's parts are collected: c/term/^lc^ lists both rows", (t3 / "c/c/term/^lc^").read_text() == "LC\tlaw\nLC\tfeature\n")
    rc, out, _ = run(tool, "fold", t3 / "c")
    case("fold of a composite-key table round-trips", out == (t3 / "c.tsv").read_bytes())
    rc, out, _ = run(tool, "set", t3 / "c", "new\tx", "sense", "fresh")
    rc2, out2, _ = run(tool, "check", t3 / "c")
    case("set with a composite key writes every part and check holds", rc == 0 and rc2 == 0 and (t3 / "c/r/new+x/term").read_text() == "new\n" and (t3 / "c/c/disp/x").read_text() == "new\tx\n")
    rc, out, err = run(tool, "set", t3 / "c", "lonely", "sense", "v")
    case("set with the wrong number of key parts is refused", rc != 0 and b"part" in err)
    write(t3 / "c.tsv", b"term\tdisp\tsense\nLC\tlaw\tliterate\nLC\tfeature\tlearning\n")
    rc, out, err = run(tool, "unfold", t3 / "c.tsv", "--out", t3 / "c1")
    case("a table unique only on two columns is refused with a one-column key, naming it", rc != 0 and b"duplicate key" in err and b"LC" in err)
    # 9c. a trailing note after the last row (a character-sheet TSV ends this way)
    write(t3 / "tail.tsv", b"a\tb\n1\tx\n# v2.0: a footer\n#  continued\n")
    rc, out, err = run(tool, "unfold", t3 / "tail.tsv")
    case("a trailing # block lands in o, verbatim", rc == 0 and (t3 / "tail/o").read_bytes() == b"# v2.0: a footer\n#  continued\n", err.decode())
    rc, out, _ = run(tool, "fold", t3 / "tail")
    case("fold prints the trailing note last, byte for byte", out == (t3 / "tail.tsv").read_bytes())
    case("the trailing note is not a row", (t3 / "tail/a").read_text() == "1\n")
    write(t3 / "nh.tsv", b"# only a note\n")
    rc, out, err = run(tool, "unfold", t3 / "nh.tsv")
    case("a table with no header and no --cols is refused", rc != 0)
    # 9d. route: a column built into a root c/ (Q609, built 2026-10-20)
    t4 = fresh(); (t4 / "e").mkdir(); (t4 / "q").mkdir()
    write(t4 / "e/terms.tsv", b"term\tstatus\nseam\tpinned\nring\thand-turning\n")
    write(t4 / "q/bank.tsv", b"id\tstatus\nQ1\thand-turning\nQ2\tpinned\n")
    run(tool, "unfold", t4 / "e/terms.tsv"); run(tool, "unfold", t4 / "q/bank.tsv")
    rc, out, err = run(tool, "route", t4 / "e/terms", "status", "--into", t4)
    case("route writes addresses, not values", rc == 0 and (t4 / "c/status/hand-turning").read_text() == "e/terms/r/ring\n" and (t4 / "c/status/pinned").read_text() == "e/terms/r/seam\n", err.decode())
    rc, out, err = run(tool, "route", t4 / "e/terms", "status", "--into", t4)
    case("route is idempotent", (t4 / "c/status/hand-turning").read_text() == "e/terms/r/ring\n")
    rc, out, err = run(tool, "route", t4 / "q/bank", "status", "--into", t4)
    case("two tables sharing a column route into one root collection", (t4 / "c/status/hand-turning").read_text() == "e/terms/r/ring\nq/bank/r/^q^1\n")
    rc, out, err = run(tool, "route", t4 / "q/bank", "status", "--into", t4, "--as", "state")
    case("--as names the root collection", rc == 0 and (t4 / "c/state/pinned").read_text() == "q/bank/r/^q^2\n")
    rc, out, _ = run(tool, "route", "--check", t4 / "e/terms", "status", "--into", t4)
    case("route --check holds after route", rc == 0 and b"holds" in out, out.decode())
    run(tool, "set", t4 / "e/terms", "ring", "status", "pinned")
    rc, out, _ = run(tool, "route", "--check", t4 / "e/terms", "status", "--into", t4)
    case("route --check names a stale route by path after set", rc == 1 and b"e/terms/r/ring" in out and b"c/status/hand-turning" in out, out.decode())
    rc, out, err = run(tool, "route", t4 / "e/terms", "status")
    case("route with no --into is refused (asserted, never searched)", rc != 0 and b"--into" in err)
    rc, out, _ = run(tool, "fold", t4 / "e/terms")
    case("route writes nothing under the table", out == b"term\tstatus\nseam\tpinned\nring\tpinned\n")
    shutil.rmtree(t4, ignore_errors=True)
    # 10. the keeper's own selftest and prove-red
    rc, out, err = run(tool, "--prove-red")
    case("the tool's own --prove-red ends PROVE-RED OK", rc == 0 and b"PROVE-RED OK" in out, err.decode())
    for d in (t, t2, t3):
        shutil.rmtree(d, ignore_errors=True)


def report(label):
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, note in RESULTS:
        print(("ok   " if ok else "FAIL ") + name + ("" if ok or not note else "  -- " + note.strip()[:200]))
    print(f"{label}: {len(RESULTS) - len(bad)} of {len(RESULTS)} ok")
    return len(bad)


PLANTS = {
    "no duplicate check": (r'''  [ -z "$dup" ] ||''', r'''  true ||'''),
    "enc keeps case (collides on a folding disk)": (r'''if (ch ~ /[A-Z]/) { if (!up) { out = out "^"; up = 1 }; out = out tolower(ch); continue }''',
                                                     r'''if (ch ~ /[A-Z]/) { out = out ch; continue }'''),
    "fold drops the note": (r'''  [ -f "$dir/n" ] && cat "$dir/n"''', r'''  :'''),
    "set writes r only": (r'''  mkdir -p "$dir/c/$ce"; printf '%s\n' "$k" >> "$dir/c/$ce/$ve"''', r'''  :'''),
    "no hold check": (r'''  if [ $held_anyway -eq 0 ] && why=$(held "$tsv"); then''', r'''  if false; then'''),
    "one-pass check exits 0 on faults": (r'''exit(faults ? 1 : 0)''', r'''exit(0)'''),
    "one-pass check skips the c side": (r'''for (x = 1; x <= nc; x++) for (y = 1; y <= cl[x]; y++) {''', r'''for (x = 1; x <= 0; x++) for (y = 1; y <= cl[x]; y++) {'''),
    "check never faults": (r'''faults=$((faults+1))''', r'''faults=0'''),
    "stale always fresh": (r'''  if [ -n "$newest" ]; then''', r'''  if false; then'''),
    "ragged rows pass": (r'''    NF != nc { print "FAULT"''', r'''    0 { print "FAULT"'''),
    "set keeps nothing under d/": (r'''cp -p "$f" "$dir/d/$st/r/$ke/$ce"''', r'''true'''),
    "a comment under the header is taken as the note": (r'''    !rows && /^#/ && hl { print "FAULT"''', r'''    0 { print "FAULT"'''),
    "a name of . or .. kept as is": (r'''    if (out == "." || out == "..") gsub(/\./, "%2E", out)''', r'''    if (0) gsub(/\./, "%2E", out)'''),
    "keys split on spaces": (r'''printf '%s\n' "$key" | tr ',' '\n' > "$w/kparts"''', r'''printf '%s\n' "$key" | tr ', ' '\n\n' > "$w/kparts"'''),
    "route copies the value, not the address": (r'''addr="$rel/r/$ke"; m=''', r'''addr="$v"; m='''),
    "route --check never faults": (r'''else echo "route --check: $faults fault(s)"; exit 1; fi''', r'''else echo "route --check: holds"; fi'''),
}


def prove_red():
    src = TOOL.read_text()
    red = 0
    for name, (old, new) in PLANTS.items():
        assert src.count(old) >= 1, f"plant site not found: {name}"
        d = fresh(); (d / "bin").mkdir(); bad = d / "bin" / "tv1cr"
        bad.write_text(src.replace(old, new)); os.chmod(bad, 0o755)
        RESULTS.clear()
        try:
            spec(bad)
        except Exception as e:  # a planted fault may crash a case; that is red too
            RESULTS.append(("spec crashed: " + str(e), False, ""))
        fails = [r[0] for r in RESULTS if not r[1]]
        print(f"plant '{name}': {len(fails)} case(s) red" + (" -- " + fails[0] if fails else ""))
        red += 1 if fails else 0
        shutil.rmtree(d, ignore_errors=True)
    print(f"PROVE-RED {'OK' if red == len(PLANTS) else 'FAILED'}: {red} of {len(PLANTS)} plants caught")
    return 0 if red == len(PLANTS) else 1


def lab(path, ok, total, red_ok, seconds):
    """The from-scratch worked example: a registry born in atoms, folded to a TSV by the tool."""
    stem = Path(path); tsv = Path(str(stem) + ".tsv")
    if not (stem / "l").exists():
        stem.mkdir(parents=True, exist_ok=True)
        (stem / "n").write_text("# tv1cr lab ledger: one row per spec run, born as atoms (tv1cr set), folded by tv1cr fold\n")
        (stem / "l").write_text("run\thost\ttool\tcases\tok\tprove-red\tseconds\n".replace("\t", "\n"))
        (stem / "t").write_text("run\thost\ttool\tcases\tok\tprove-red\tseconds\n")
        (stem / "i").write_text("run\n"); (stem / "a").write_text(""); (stem / "r").mkdir(); (stem / "c").mkdir()
    run_id = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    rows = [("host", platform.node()), ("tool", str(TOOL.relative_to(HERE.parent)) if str(TOOL).startswith(str(HERE.parent)) else str(TOOL)),
            ("cases", str(total)), ("ok", str(ok)), ("prove-red", "OK" if red_ok else "FAILED" if red_ok is False else "not-run"),
            ("seconds", f"{seconds:.1f}")]
    for col, val in rows:
        rc, out, err = run(TOOL, "set", stem, run_id, col, val)
        if rc != 0:
            print("lab: set failed:", err.decode()); return
    rc, out, err = run(TOOL, "fold", stem)
    tsv.write_bytes(out)
    rc, out, err = run(TOOL, "check", stem)
    print(f"lab: row {run_id} set into {stem} (7 columns); folded to {tsv}; {out.decode().strip()}")


if __name__ == "__main__":
    t0 = time.time()
    spec(TOOL)
    bad = report("tv1cr-spec")
    main_ok, main_total = len(RESULTS) - bad, len(RESULTS)
    red_ok = None
    if "--prove-red" in sys.argv:
        red_ok = prove_red() == 0
    if "--lab" in sys.argv:
        lab(sys.argv[sys.argv.index("--lab") + 1], main_ok, main_total, red_ok, time.time() - t0)
    sys.exit(1 if bad or red_ok is False else 0)
