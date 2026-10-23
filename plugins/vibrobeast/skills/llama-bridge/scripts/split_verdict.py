#!/usr/bin/env python3
# split_verdict.py -- for a judgement task on a small model: the model answers two yes/no questions,
#   and this code, not the model, makes the three-valued verdict.
#     PRESENT: no            -> NOT CHECKED   (what it would need to look at is not there)
#     PRESENT: yes, MET: yes -> OK
#     PRESENT: yes, MET: no  -> RED
#     anything else          -> UNPARSED      (never a pass)
# Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
# Written by Mentat (for Corwin, claude-opus-5-5), 2026-10-22.
# usage: split_verdict.py < answer.txt          prints the verdict; exit 0 OK, 1 RED, 2 NOT CHECKED, 3 UNPARSED
#        split_verdict.py --prompt              prints the two-question instruction to append to a system prompt
#        split_verdict.py --selftest | --prove-red
import sys

PROMPT = ("Answer with exactly two lines and nothing before them:\n"
          "PRESENT: yes or no  (is what you would need to look at, to apply the rule, shown?)\n"
          "MET: yes or no  (if it is shown, is the rule met?)\n"
          "Then one sentence saying why.")
EXIT = {"OK": 0, "RED": 1, "NOT CHECKED": 2, "UNPARSED": 3}

def decide(text):
    p = m = None
    for ln in text.splitlines():
        u = ln.strip().strip("*").upper()
        if u.startswith("PRESENT:"): p = u.split(":", 1)[1].strip(" *.").split(" ")[0]
        elif u.startswith("MET:"): m = u.split(":", 1)[1].strip(" *.").split(" ")[0]
    if p == "NO": return "NOT CHECKED"
    if p == "YES" and m == "YES": return "OK"
    if p == "YES" and m == "NO": return "RED"
    return "UNPARSED"

CASES = [("PRESENT: no\nMET: yes\nwhy", "NOT CHECKED"), ("**PRESENT:** yes\n**MET:** no", "RED"),
         ("PRESENT: Yes.\nMET: Yes", "OK"), ("PRESENT: yes", "UNPARSED"),
         ("Looks fine to me.", "UNPARSED"), ("PRESENT: maybe\nMET: yes", "UNPARSED"),
         ("", "UNPARSED"), ("present: no", "NOT CHECKED")]

def selftest(d):
    bad = [(a, w, d(a)) for a, w in CASES if d(a) != w]
    for b in bad: print("split_verdict: WRONG %r: want %s got %s" % b)
    return len(bad)

def main(a):
    if a[:1] == ["--prompt"]: print(PROMPT); return 0
    if a[:1] == ["--selftest"]:
        n = selftest(decide); print("split_verdict: selftest %d of %d" % (len(CASES) - n, len(CASES)))
        return 1 if n else 0
    if a[:1] == ["--prove-red"]:   # each planted mutant must fail the selftest
        mutants = {
            "missing PRESENT passes": lambda t: "OK" if decide(t) == "UNPARSED" else decide(t),
            "PRESENT no ignored": lambda t: {"NOT CHECKED": "RED"}.get(decide(t), decide(t)),
            "MET read as PRESENT": lambda t: decide(t.replace("MET:", "PRESENT:")),
        }
        caught = 0
        for name, f in mutants.items():
            ok = selftest(f) > 0; caught += ok
            print("split_verdict: plant '%s' %s" % (name, "caught" if ok else "MISSED"))
        print("split_verdict: prove-red %d of %d" % (caught, len(mutants)))
        return 0 if caught == len(mutants) else 1
    v = decide(sys.stdin.read()); print(v); return EXIT[v]

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
