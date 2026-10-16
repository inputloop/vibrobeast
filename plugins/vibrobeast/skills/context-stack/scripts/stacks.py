#!/usr/bin/env python3
# stacks.py -- the context stack as files: one semaphore file for the pile, a boulder file when a group's pressure
#   reaches the dial, a mountain file when it reaches the dial again; every link doubly linked.
#   Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  Authored by Mentat (for Corwin).
#   SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
#
# WHY, his words (2026-10-11): "default to four for each layer of file indirection vs simple semaphore files, creating
#   extra files for boulder sized interim context first as I have an item with four points of pressure weighing down the
#   initial rocks single semaphore file, creating mountains as I amass a GRAIN pressure inside those to create mountains
#   files that collect those heavily trafficked context referent entry stacks".  And from METHOD-context-stacking
#   (modelthisbook/news): boulders are items with gravity toward each other, tagged together; mountains sort by
#   accumulated mass, and mass includes calendar time since the item last moved.
#
# usage: stacks.py PILE.tsv OUTDIR [--dial N] [--today YYYY-MM-DD]
#        stacks.py --prove-red
#   PILE.tsv  one rock per line: ID <tab> TAGS (comma-separated groups) <tab> PRESSURE <tab> LAST-MOVED (YYYY-MM-DD) <tab> LABEL
#   OUTDIR/SEMAPHORE.md         the pile: every rock, one line each, heaviest group first; a rock in a boulder points to it
#   OUTDIR/boulders/TAG.md      a group whose rocks carry DIAL or more pressure in all: its rocks, each linking back
#   OUTDIR/mountains/TAG.md     a group carrying DIAL x DIAL or more: its stack, heaviest and longest-unmoved first,
#                               linking back to its boulder (and the boulder links up to it)
#   The dial: 4 by default (GRAIN), the same at every layer.  1 makes many files, 2 more, 9 fewer, 17 rarely any.
#   MUST     writes only under OUTDIR, and refuses an OUTDIR that already has a SEMAPHORE.md; reads only PILE.tsv.
#   JOURNEY  mass order is pressure first, then the longer time since moving; no exchange rate between days and
#            pressure is invented (none is measured).  A rock with several tags sits in each group's file.
import os, re, sys
from datetime import date

def load(pile):
    rocks = []
    for n, ln in enumerate(open(pile, encoding="utf-8"), 1):
        if not ln.strip() or ln.startswith("#"): continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 5: sys.exit("stacks: %s:%d: needs ID, TAGS, PRESSURE, LAST-MOVED, LABEL" % (pile, n))
        if not re.fullmatch(r"[0-9]+", p[2]) or not re.fullmatch(r"\d{4}-\d\d-\d\d", p[3]):
            sys.exit("stacks: %s:%d: bad pressure or date" % (pile, n))
        rocks.append({"id": p[0], "tags": [t for t in p[1].split(",") if t] or ["untagged"], "p": int(p[2]),
                      "moved": p[3], "label": p[4]})
    return rocks

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "group"

def build(pile, out, dial=4, today=None):
    if dial < 1: sys.exit("stacks: the dial is a whole number, 1 or more")
    if os.path.exists(os.path.join(out, "SEMAPHORE.md")): sys.exit("stacks: %s already holds a SEMAPHORE.md" % out)
    rocks = load(pile); today = date.fromisoformat(today) if today else date.today()
    age = lambda r: (today - date.fromisoformat(r["moved"])).days
    groups = {}
    for r in rocks:
        for t in r["tags"]: groups.setdefault(t, []).append(r)
    mass = {t: sum(r["p"] for r in rs) for t, rs in groups.items()}
    oldest = {t: max(age(r) for r in rs) for t, rs in groups.items()}
    order = sorted(groups, key=lambda t: (-mass[t], -oldest[t], t))
    boulder = {t for t in groups if mass[t] >= dial}
    mountain = {t for t in groups if mass[t] >= dial * dial}
    stack = lambda rs: sorted(rs, key=lambda r: (-r["p"], -age(r), r["id"]))
    os.makedirs(out, exist_ok=True)
    if boulder: os.makedirs(os.path.join(out, "boulders"), exist_ok=True)
    if mountain: os.makedirs(os.path.join(out, "mountains"), exist_ok=True)
    with open(os.path.join(out, "SEMAPHORE.md"), "w") as f:
        f.write("# SEMAPHORE: the pile\n\nEvery rock, one line each, grouped heaviest first (pressure, then the longest unmoved). "
                "Dial %d: a group becomes a boulder file at %d, a mountain file at %d. Built %s.\n\n" % (dial, dial, dial * dial, today))
        for t in order:
            kind = "mountain" if t in mountain else "boulder" if t in boulder else "rock pile"
            link = " → [%s](boulders/%s.md)" % (kind, slug(t)) if t in boulder else ""
            f.write("## %s\n\n%s, pressure %d, oldest %d days unmoved%s\n\n" % (t, kind, mass[t], oldest[t], link))
            for r in stack(groups[t]):
                f.write('- <a id="%s"></a>`%s` %s (pressure %d, moved %s)\n' % (slug(t) + "--" + slug(r["id"]), r["id"], r["label"], r["p"], r["moved"]))
            f.write("\n")
    for t in sorted(boulder):
        up = "\n\nThis boulder is heavy enough to be a mountain: [%s](../mountains/%s.md)." % (t, slug(t)) if t in mountain else ""
        with open(os.path.join(out, "boulders", slug(t) + ".md"), "w") as f:
            f.write("# Boulder: %s\n\nItems with gravity toward each other, tagged together. Pressure %d (the dial is %d). Back to the pile: [SEMAPHORE](../SEMAPHORE.md#%s).%s\n\n" % (
                t, mass[t], dial, slug(t), up))
            for r in stack(groups[t]):
                f.write("- [`%s`](../SEMAPHORE.md#%s) %s (pressure %d)\n" % (r["id"], slug(t) + "--" + slug(r["id"]), r["label"], r["p"]))
    for t in sorted(mountain):
        with open(os.path.join(out, "mountains", slug(t) + ".md"), "w") as f:
            f.write("# Mountain: %s\n\nThe heavily trafficked stack: heaviest first, then the longest unmoved. Pressure %d, at least the dial squared (%d). "
                    "Its boulder: [%s](../boulders/%s.md).\n\n" % (t, mass[t], dial * dial, t, slug(t)))
            for i, r in enumerate(stack(groups[t]), 1):
                f.write("%d. `%s` %s (pressure %d, %d days unmoved)\n" % (i, r["id"], r["label"], r["p"], age(r)))
    return len(boulder), len(mountain)

def prove_red():
    import tempfile, shutil
    t = tempfile.mkdtemp(); fired = n = 0
    pile = os.path.join(t, "p.tsv")
    open(pile, "w").write("a\tx\t3\t2026-10-01\tone\nb\tx\t1\t2026-09-01\ttwo\nc\ty\t2\t2026-10-10\tthree\nd\tz,x\t12\t2026-10-05\tfour\n")
    nb, nm = build(pile, os.path.join(t, "o4"), 4, "2026-10-11")
    n += 1; fired += (nb, nm) == (2, 1)            # x=16 mountain at 16, z=12 boulder, y=2 neither
    n += 1; fired += os.path.exists(os.path.join(t, "o4", "mountains", "x.md")) and not os.path.exists(os.path.join(t, "o4", "boulders", "y.md"))
    m = open(os.path.join(t, "o4", "mountains", "x.md")).read()
    n += 1; fired += m.index("`d`") < m.index("`a`") < m.index("`b`")     # mass order: pressure first
    n += 1; fired += build(pile, os.path.join(t, "o17"), 17, "2026-10-11") == (0, 0)
    n += 1; fired += build(pile, os.path.join(t, "o1"), 1, "2026-10-11") == (3, 3)
    try: build(pile, os.path.join(t, "o4"), 4, "2026-10-11"); ok = False
    except SystemExit: ok = True
    n += 1; fired += ok                                                   # refuses an existing pile
    shutil.rmtree(t)
    print("stacks --prove-red: %d/%d planted cases read as planted" % (fired, n))
    return 0 if fired == n else 1

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--prove-red"]: sys.exit(prove_red())
    if len(a) < 2: sys.exit("usage: stacks.py PILE.tsv OUTDIR [--dial N] [--today YYYY-MM-DD] | --prove-red")
    dial, today = 4, None
    if "--dial" in a: dial = int(a[a.index("--dial") + 1])
    if "--today" in a: today = a[a.index("--today") + 1]
    nb, nm = build(a[0], a[1], dial, today)
    print("stacks: %s: %d boulder file(s), %d mountain file(s) at dial %d" % (a[1], nb, nm, dial))
