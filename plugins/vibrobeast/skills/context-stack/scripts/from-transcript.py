#!/usr/bin/env python3
# from-transcript.py -- turn a transcript's subjects and result (tr2sm, tr3rm) into a cstk vector,
#   so tension is always bound to work that happened, with axis values taken from counts, not chosen.
#   Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  Authored by Mentat (for Corwin).
#   SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
#
# usage: from-transcript.py S2DIR > NAME.cmd
#   Each subject becomes a node (label: its title), in order of first appearance.
#   Pressure: one citation per cue line tr3rm found in it (pins + seams + semaphores).
#   Tension, only where a subject has at least one seam and at least one pin or semaphore, on two axes:
#     HELD/RAISED = (raised seams - held seams) / seams         -1: every seam held by a pin; +1: none held
#     SAID/ASKED  = (semaphores - pins) / (pins + semaphores)   -1: all pins; +1: all semaphores
#   rounded half away from zero to thousandths.  A tension whose seams are all held is pinned; the rest
#   stay suspended (the space left open).  Anchored subjects go into the fort; the floor orders them.
import os, re, sys


def q(num, den):
    """num/den in thousandths, rounded half away from zero, as a cstk VALUE."""
    k = (abs(num) * 2000 + den) // (2 * den)
    k = -k if num < 0 else k
    return "%s%d.%03d" % ("-" if k < 0 else "", abs(k) // 1000, abs(k) % 1000)


def main(s2):
    subs = [l.rstrip("\n").split("\t") for l in open(os.path.join(s2, "SUBJECTS.tsv"), encoding="utf-8")]
    kinds = {}
    for l in open(os.path.join(s2, "RESULT.tsv"), encoding="utf-8"):
        k, slug = l.split("\t")[:2]
        kinds.setdefault(slug, {"PIN": 0, "SEAM": 0, "SEMAPHORE": 0})[k] += 1
    held, cur, in_seam = {}, None, False
    for l in open(os.path.join(s2, "RESULT.md"), encoding="utf-8"):
        m = re.match(r"### \[.*\]\(([^)]+)\.md\)", l)
        if m: cur, in_seam = m.group(1), False; continue
        if l.startswith("**"): in_seam = l.startswith("**SEAM**"); continue
        if cur and in_seam and l.startswith("  - held by: "):
            h = held.setdefault(cur, [0, 0])
            h[1 if "still raised" in l else 0] += 1
    out = ["# from %s: subjects as nodes, cue lines as pressure, tension from counts" % os.path.normpath(s2)]
    for slug, kind, title, *_ in subs:
        out.append("push %s %s" % (slug, title))
    for slug, *_ in subs:
        c = kinds.get(slug)
        if c and sum(c.values()): out.append("cite %s %d" % (slug, sum(c.values())))
    pins = []
    for slug, *_ in subs:
        c = kinds.get(slug, {"PIN": 0, "SEAM": 0, "SEMAPHORE": 0})
        hd, rs = held.get(slug, [0, 0])
        seams = hd + rs
        if seams and c["PIN"] + c["SEMAPHORE"]:
            out.append("tension %s HELD/RAISED=%s SAID/ASKED=%s" % (
                slug, q(rs - hd, seams), q(c["SEMAPHORE"] - c["PIN"], c["PIN"] + c["SEMAPHORE"])))
            pins.append(rs == 0)
    n = 0
    for i, p in enumerate(pins, 1):
        if p: out.append("pin t%d" % i); n += 1
    for slug, kind, *_ in subs:
        if kind == "ANCHORED": out.append("fort %s" % slug)
    out += ["floor", "suspended", "check", "dump"]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("usage: from-transcript.py S2DIR")
    main(sys.argv[1])
