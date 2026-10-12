#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""doubled_nine - the optional doubled-nine mode of LENS: the four-view pass run cold and with a
persona loaded, several times per arm, so a persona's difference can be read against the rerun floor.

Kit, grown from the one experiment that used it (c4 writing/two-readers/arms/, 2026-09-27, two runs on
two questions). What both runs shared is here; what was specific to one question (its trait regexes,
its answer fields, its party names, its seed) is an argument.

  draw BANK.tsv [BANK.tsv ...] [--seed N]   one seeded draw, no redraw (seed default: today, YYYYMMDD)
  method --party A --party B [--field F]    the arm method, parties named, answer fields named
  judge DIR [--seed N] [--party A --party B] [--key FILE]
                                            the blind judge prompt: arms shuffled by seed, labelled A..
  measure DIR [--traits FILE] [--field F] [--json]
                                            per-block word distance within each arm and across arms
                                            (the excess over the within-arm floor), trait hits, and
                                            for each --field, how many pairs disagree within and across
  permute DIR                               where the true cold/persona split ranks among all splits
  selftest [--prove-red]

Arms are files named C<n>.txt (cold) and P<n>.txt (persona) in DIR, each in the method's shape.
The reading rule the experiment earned: a persona difference is news only beyond the rerun floor.
On a decision field, compare cross-arm disagreement with within-arm disagreement; if a plain rerun
disagrees as often, the persona cited reasons, it did not move the decision.
stdlib only.
"""
from __future__ import annotations
import argparse, csv, datetime, itertools, json, os, random, re, sys

STOP = set("the and for that this with are was not but its it's you your from what does name names can have has into they them their our who how why will would which when than then there also only just more most one two all any use used using a an of to in on is be as by or at it if so no do we i he his".split())
KEYS = ["VIEW 1", "VIEW 2", "VIEW 3", "VIEW 4", "ANSWER"]
_SUBTRACT_FLOOR = True        # --prove-red plants excess = cross (no floor) and must be caught
_SEED_THE_DRAW = True         # --prove-red plants an unseeded draw and must be caught

# --- the arms ---------------------------------------------------------------------------------

def parse(txt):
    out = {}
    parts = re.split(r"^(VIEW [1-4][^\n]*|ANSWER)\s*$", txt, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].split(" — ")[0].strip()] = parts[i + 1].strip()
    return out

def words(s):
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9][a-z0-9-]{2,}", s.lower()) if w not in STOP}

def jd(a, b):
    A, B = words(a), words(b)
    return 1 - len(A & B) / len(A | B) if A | B else 0.0

def load_arms(d):
    arms = {}
    for fn in sorted(os.listdir(d)):
        if re.fullmatch(r"[CP][0-9]+\.txt", fn):
            with open(os.path.join(d, fn), encoding="utf-8") as fh:
                arms[fn[:-4]] = fh.read()
    return arms

def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")

def field(parsed, f):
    m = re.search(rf"^{re.escape(f)}:\s*(.*)$", parsed.get("ANSWER", ""), flags=re.M)
    return m.group(1).strip() if m else "?"

def token(v):
    """The decision in a field line: its first word, before any ' — why'."""
    return (re.split(r"\s+—\s+|\s+-\s+|\s", v.strip(), maxsplit=1)[0] or "?").strip(".,;").lower()

# --- measure ----------------------------------------------------------------------------------

def excess_of(cross, wc, wp):
    return cross - (wc + wp) / 2 if _SUBTRACT_FLOOR else cross

def measure(d, traits=None, fields=()):
    arms = load_arms(d)
    P = {k: parse(v) for k, v in arms.items()}
    C = [k for k in arms if k[0] == "C"]; Pp = [k for k in arms if k[0] == "P"]
    res = {"arms": {"cold": C, "persona": Pp},
           "shape_ok": {k: all(x in p for x in KEYS) for k, p in P.items()}}
    table = {}
    for v in KEYS:
        wc = [jd(P[a].get(v, ""), P[b].get(v, "")) for a, b in itertools.combinations(C, 2)]
        wp = [jd(P[a].get(v, ""), P[b].get(v, "")) for a, b in itertools.combinations(Pp, 2)]
        cr = [jd(P[a].get(v, ""), P[b].get(v, "")) for a in C for b in Pp]
        table[v] = dict(within_cold=round(mean(wc), 3), within_persona=round(mean(wp), 3),
                        cross=round(mean(cr), 3),
                        excess=round(excess_of(mean(cr), mean(wc), mean(wp)), 3),
                        n=(len(wc), len(wp), len(cr)))
    res["distance_by_view"] = table
    if traits:
        tc = {}
        for t, rx in traits.items():
            cnt = {k: len(re.findall(rx, arms[k], flags=re.I)) for k in arms}
            tc[t] = dict(per_arm=cnt, mean_cold=mean([cnt[k] for k in C]),
                         mean_persona=mean([cnt[k] for k in Pp]))
        res["trait_hits"] = tc
    dec = {}
    for f in fields:
        val = {k: token(field(P[k], f)) for k in arms}
        diff = lambda pairs: (sum(val[a] != val[b] for a, b in pairs), len(pairs))
        dec[f] = dict(values=val,
                      within_cold=diff(list(itertools.combinations(C, 2))),
                      within_persona=diff(list(itertools.combinations(Pp, 2))),
                      cross=diff([(a, b) for a in C for b in Pp]))
    res["decisions"] = dec
    return res

def render(res):
    out = ["doubled-nine measure  cold=%s  persona=%s" % (",".join(res["arms"]["cold"]),
                                                          ",".join(res["arms"]["persona"]))]
    bad = [k for k, ok in res["shape_ok"].items() if not ok]
    if bad:
        out.append("  !! not in the method's shape (a block is missing): %s" % ", ".join(bad))
    out.append("  word distance (share of content words NOT shared), per block:")
    out.append("    %-8s %11s %14s %7s %8s" % ("block", "within-cold", "within-persona", "cross", "excess"))
    for v, t in res["distance_by_view"].items():
        out.append("    %-8s %11.3f %14.3f %7.3f %+8.3f" % (v, t["within_cold"], t["within_persona"],
                                                          t["cross"], t["excess"]))
    out.append("  excess = cross minus the within-arm floor; near zero means the persona's words are"
               " no further from cold than a rerun is from itself")
    for f, d in res.get("decisions", {}).items():
        c, p, x = d["within_cold"], d["within_persona"], d["cross"]
        out.append("  decision '%s': pairs that disagree  within-cold %d/%d  within-persona %d/%d"
                   "  cross %d/%d" % (f, c[0], c[1], p[0], p[1], x[0], x[1]))
        rate = lambda t: t[0] / t[1] if t[1] else 0.0
        floor = max(rate(c), rate(p))
        out.append("    %s" % ("the persona moved the decision beyond the rerun floor"
                               if rate(x) > floor else
                               "no further than a rerun: the persona cited reasons, it did not move the decision"))
    for t, d in res.get("trait_hits", {}).items():
        out.append("  trait %-22s cold %.2f -> persona %.2f" % (t, d["mean_cold"], d["mean_persona"]))
    return "\n".join(out)

def read_traits(path):
    tr = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"): continue
            name, rx = line.rstrip("\n").split("\t", 1)
            tr[name] = rx
    return tr

# --- permute ----------------------------------------------------------------------------------

def permute(d):
    """Rank the true cold/persona split's excess among every split into two equal groups."""
    arms = load_arms(d); P = {k: parse(v) for k, v in arms.items()}
    names = sorted(arms); half = len(names) // 2
    def ex(g1, g2, v):
        w1 = [jd(P[a].get(v, ""), P[b].get(v, "")) for a, b in itertools.combinations(g1, 2)]
        w2 = [jd(P[a].get(v, ""), P[b].get(v, "")) for a, b in itertools.combinations(g2, 2)]
        return excess_of(mean([jd(P[a].get(v, ""), P[b].get(v, "")) for a in g1 for b in g2]),
                         mean(w1), mean(w2))
    S = [(g1, tuple(n for n in names if n not in g1))
         for g1 in itertools.combinations(names, half) if names[0] in g1]
    T = [s for s in S if {n[0] for n in s[0]} in ({"C"}, {"P"})][0]
    rows = []
    for v in KEYS:
        vals = [ex(a, b, v) for a, b in S]; t = ex(*T, v)
        rows.append((v, round(t, 3), 1 + sum(x > t for x in vals), len(S), round(max(vals), 3)))
    return rows

# --- draw, method, judge ----------------------------------------------------------------------

def today_seed():
    return int(datetime.date.today().strftime("%Y%m%d"))

def draw(paths, seed):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            rows += [(os.path.basename(p), r) for r in list(csv.reader(fh, delimiter="\t"))[1:]]
    rng = random.Random(seed) if _SEED_THE_DRAW else random.Random()
    i = rng.randrange(len(rows))
    return seed, len(rows), i, rows[i]

METHOD = """# METHOD (identical for every arm): the four-views pass

You are the actor. Weigh the question below by holding exactly four views, all of which are your own
constructions (you cannot read another mind; you read your model of it):

1. Your view of yourself -- your own stance, with your own preferences showing.
2. Your view of {A} -- your construction of how {A} would answer, not {A} themself.
3. Your view of {B} -- your construction of how {B} would answer, not {B} themself.
4. Your view of the intersection -- where your constructions of {A} and {B} meet, or fail to meet.
   Name this seam explicitly; do not silently merge or split the two.

Then answer the question. Use only the context packet; if the packet does not settle something, say so.
A party you have no words from: say so in their view, and mark that view *invented*.

Reply in EXACTLY this shape and nothing else (plain text, no preamble):

{blocks}ANSWER
answer: <one or two sentences answering the question>
{fields}confidence: <low | medium | high>
"""

def method_text(a, b, fields):
    blocks = ""
    for n, who in ((1, "SELF"), (2, a.upper()), (3, b.upper()), (4, "INTERSECTION")):
        blocks += "VIEW %d — %s\nstance: <one sentence>\nreasons:\n- <reason>\n- <reason>\n- <reason>\n" % (n, who)
    flines = "".join("%s: <your choice> — <one line why>\n" % f for f in fields)
    return METHOD.format(A=a, B=b, blocks=blocks, fields=flines)

def judge(d, seed, a, b):
    arms = load_arms(d); names = sorted(arms)
    order = names[:]; random.Random(seed).shuffle(order)
    labels = [chr(ord("A") + i) for i in range(len(order))]
    key = dict(zip(labels, order))
    n = len(order); half = n // 2
    head = ("Below are %d answers, labelled %s to %s, to the same question, produced from the same "
            "instructions and the same context packet. They come from two conditions, %d answers each; "
            "you are not told what the conditions are.\n\nTask:\n1. Split the %d into the two groups of %d "
            "that you judge were produced under different conditions. Give the split as two lists of "
            "letters.\n2. Give your confidence in the split (low / medium / high).\n3. List the systematic "
            "differences between the two groups (not one-off differences). For each, say in which block it "
            "shows most: VIEW 1 (self), VIEW 2 (%s), VIEW 3 (%s), VIEW 4 (intersection) or ANSWER.\n4. Say "
            "in one or two sentences what you think the difference in conditions was.\n\nReply in plain "
            "text, under 400 words.\n" % (n, labels[0], labels[-1], half, n, half, a, b))
    body = "".join("\n===== ANSWER %s =====\n%s\n" % (l, arms[key[l]].strip()) for l in labels)
    return head + body, key

# --- selftest ---------------------------------------------------------------------------------

def _arm(self_, a, b, x, ans, opt):
    return ("VIEW 1 — SELF\nstance: %s\nVIEW 2 — A\nstance: %s\nVIEW 3 — B\nstance: %s\n"
            "VIEW 4 — INTERSECTION\nstance: %s\nANSWER\nanswer: %s\noption: %s — why\n"
            "confidence: medium\n" % (self_, a, b, x, ans, opt))

def _checks():
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as td:
        # cold arms share their words; persona arms carry the word 'freedom' in VIEW 1 only
        cold_opts, pers_opts = "BAAB", "BABA"      # run 2's options, as the experiment reported them
        for i in range(4):
            open(os.path.join(td, "C%d.txt" % (i + 1)), "w", encoding="utf-8").write(
                _arm("namespace address table" + (" ledger" if i == 0 else ""),
                     "bryant view words", "corwin view words",
                     "seam words here", "address answer", cold_opts[i]))
            open(os.path.join(td, "P%d.txt" % (i + 1)), "w", encoding="utf-8").write(
                _arm("namespace address freedom plain", "bryant view words", "corwin view words",
                     "seam words here", "address answer", pers_opts[i]))
        r = measure(td, traits={"T4 freedom": r"\bfreedom"}, fields=["option"])
        t = r["distance_by_view"]
        checks.append(("every arm is in the method's shape", all(r["shape_ok"].values())))
        checks.append(("identical blocks measure zero distance", t["VIEW 2"]["cross"] == 0.0))
        # VIEW 1: cold {stance,namespace,addre,table}, persona {stance,namespace,addre,freedom,plain}
        # ('stance' is a content word; a trailing s is folded, as measure.py folds it): jd = 1 - 3/6
        checks.append(("the distance is Jaccard on content words (one known pair = 0.5)",
                       jd("stance: namespace address table", "stance: namespace address freedom plain") == 0.5))
        # make one cold arm differ in VIEW 1, so the floor is not zero and subtracting it shows
        checks.append(("excess subtracts the within-arm floor (VIEW 1: cross - (within-cold + within-persona)/2)",
                       t["VIEW 1"]["excess"] == round(t["VIEW 1"]["cross"] - (t["VIEW 1"]["within_cold"]
                                                      + t["VIEW 1"]["within_persona"]) / 2, 3)
                       and t["VIEW 1"]["within_cold"] > 0))
        d = r["decisions"]["option"]
        checks.append(("decision counts reproduce the experiment's run 2 (cold 4/6, persona 4/6, cross 8/16)",
                       (d["within_cold"], d["within_persona"], d["cross"]) == ((4, 6), (4, 6), (8, 16))))
        checks.append(("the reading says 'no further than a rerun' on those counts",
                       "no further than a rerun" in render(r)))
        checks.append(("a trait counts where it was planted", r["trait_hits"]["T4 freedom"]["mean_persona"] == 1.0
                       and r["trait_hits"]["T4 freedom"]["mean_cold"] == 0.0))
        rows = permute(td)
        checks.append(("8 arms give 35 splits, and the true split ranks first on VIEW 1",
                       rows[0][3] == 35 and rows[0][2] == 1))
        bank = os.path.join(td, "bank.tsv")
        with open(bank, "w", encoding="utf-8") as fh:
            fh.write("id\tq\n" + "".join("Q%d\tquestion %d\n" % (i, i) for i in range(50)))
        five = {draw([bank], 20260927)[2] for _ in range(5)}
        checks.append(("the draw is seeded: same seed, same row, five times over", len(five) == 1))
        checks.append(("different seeds reach different rows",
                       len({draw([bank], s)[2] for s in range(20260920, 20260930)}) > 1))
        txt, key = judge(td, 20260927, "Bryant", "Corwin")
        checks.append(("the judge prompt labels every arm once and hides the condition",
                       sorted(key.values()) == sorted(load_arms(td)) and "C1" not in txt and "===== ANSWER H" in txt))
        m = method_text("Bryant", "Corwin", ["option"])
        checks.append(("the method names both parties and the answer field",
                       "Your view of Bryant" in m and "VIEW 3 — CORWIN" in m and "option: <your choice>" in m))
    return checks

def selftest():
    bad = 0
    for name, ok in _checks():
        print("%s %s" % ("ok  " if ok else "FAIL", name)); bad += 0 if ok else 1
    print("TOTAL pass=%d fail=%d" % (len(_checks()) - bad, bad))
    return 1 if bad else 0

def prove_red():
    global _SUBTRACT_FLOOR, _SEED_THE_DRAW
    plants = [("excess read as raw cross distance (no rerun floor)", "_SUBTRACT_FLOOR",
               "excess subtracts the within-arm floor"),
              ("an unseeded draw", "_SEED_THE_DRAW", "the draw is seeded")]
    ok_all = True
    for label, flag, must in plants:
        globals()[flag] = False
        try:
            failed = [n for n, ok in _checks() if not ok]
        finally:
            globals()[flag] = True
        caught = any(n.startswith(must) for n in failed)
        ok_all &= caught
        print("%s planted: %s -> failing: %s" % ("ok  " if caught else "FAIL", label, "; ".join(failed) or "(none)"))
    clean = all(ok for _, ok in _checks())
    print("%s control: no plant -> every check passes" % ("ok  " if clean else "FAIL"))
    print("prove-red: %s" % ("every planted fault went RED and the control stayed green" if ok_all and clean else "FAILED"))
    return 0 if ok_all and clean else 1

# --- cli --------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="the doubled-nine mode of LENS")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("draw"); p.add_argument("bank", nargs="+"); p.add_argument("--seed", type=int, default=None)
    p = sub.add_parser("method"); p.add_argument("--party", action="append", required=True)
    p.add_argument("--field", action="append", default=[])
    p = sub.add_parser("judge"); p.add_argument("dir"); p.add_argument("--seed", type=int, default=None)
    p.add_argument("--party", action="append", default=[]); p.add_argument("--key")
    p = sub.add_parser("measure"); p.add_argument("dir"); p.add_argument("--traits")
    p.add_argument("--field", action="append", default=[]); p.add_argument("--json", action="store_true")
    p = sub.add_parser("permute"); p.add_argument("dir")
    p = sub.add_parser("selftest"); p.add_argument("--prove-red", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return prove_red() if a.prove_red else selftest()
    if a.cmd == "draw":
        seed = a.seed if a.seed is not None else today_seed()
        seed, n, i, (src, row) = draw(a.bank, seed)
        print("seed=%d pool=%d index=%d source=%s  (one draw, no redraw)" % (seed, n, i, src))
        print("\t".join(row))
    elif a.cmd == "method":
        if len(a.party) != 2: ap.error("method takes exactly two --party")
        print(method_text(a.party[0], a.party[1], a.field), end="")
    elif a.cmd == "judge":
        parties = a.party if len(a.party) == 2 else ["party A", "party B"]
        txt, key = judge(a.dir, a.seed if a.seed is not None else today_seed(), *parties)
        print(txt, end="")
        if a.key:
            with open(a.key, "w", encoding="utf-8") as fh:
                json.dump(key, fh, indent=1)
    elif a.cmd == "measure":
        res = measure(a.dir, read_traits(a.traits) if a.traits else None, a.field)
        print(json.dumps(res, indent=1) if a.json else render(res))
    elif a.cmd == "permute":
        for v, t, rank, n, mx in permute(a.dir):
            print("%s: true_excess=%.3f rank=%d/%d max_any_split=%.3f" % (v, t, rank, n, mx))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
