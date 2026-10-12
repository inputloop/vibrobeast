#!/usr/bin/env python3
"""pe1gt.py -- the second reader of pe1gt: the same answers, in Python.

usage: pe1gt.py plan --use N [...] | pe1gt.py refusals | pe1gt.py sheet FILE
Unfolded from persona-engine.org; edit that, not this.
Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; GPL-3.0-or-later.
Mentat (for Corwin; claude-opus-5-5)
"""
import re
import string
import sys

REFUSALS = """1. Never mint a persona. A declaration pointing at a file that does not exist is a FAULT, never a cue to write that file.
2. Never write the persona's voice. A skeleton may be drafted; the journal entry is the persona's own.
3. Never edit a sheet another session wrote, except by appending to that sheet's own log.
4. Never take the rights. The byline says for somebody, always.
5. A persona's voice may not be the place a defect is explained. Fix the thing first; then the persona may say what it likes about it.
"""
OPTS = {"--use": "use", "--name": "name", "--for": "for_", "--declared": "declared", "--second-use": "second",
        "--consent": "consent", "--building": "building", "--roll": "roll"}
CODES = {"GO": 0, "WAIT": 3, "HOLD": 4, "STOP": 5}
LOWER = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)  # ASCII only, as awk under LC_ALL=C


def plan(o):
    out, steps = [], []

    def say(v, why):
        out.append(v + ": " + why)
        return v

    def step(s):
        steps.append("  %d. %s" % (len(steps) + 1, s))

    use, name, for_ = o["use"], o["name"], o["for_"]
    who, pr = name, for_
    if not re.fullmatch(r"[1-4]", use):  # not match("^[1-4]$"): Python's $ also takes "2" and a newline
        v = say("STOP", "no use named (1 a real person, 2 a system actor, 3 the context of an actor, 4 tensions at an intersection); without one a persona is not warranted. Say it in your own voice.")
    elif o["building"] == "yes":
        v = say("WAIT", "never during a local build or test; come back when the work is used.")
    elif o["roll"] == "yes" and name.translate(LOWER) in ("mentat", "vibrobeast"):
        v = say("STOP", name + " grew its voice before the bias engine; it is not re-rolled.")
    elif o["roll"] == "yes" and use != "2":
        v = say("STOP", "bias rolls are for system actors (use 2) only.")
    elif use != "4" and (o["declared"] != "yes" or name == ""):
        v = say("STOP", "nothing declared, so nothing to resolve. Never mint a persona; the voice stays Mentat.")
    elif use == "2" and o["second"] != "yes":
        v = say("WAIT", "a system actor affixes on its second use, not its first.")
    elif use == "1" and name != for_ and o["consent"] != "yes":
        v = say("HOLD", "a real person who is not the principal: consent first (consent-gate), and share their view, not their facts.")
    elif for_ == "":
        v = say("WAIT", "no principal named; name one with --for (the byline says for somebody, always).")
    elif use == "4":
        v = say("GO", "model the tensions in the LENS; read the actors' sheets where declared; make no new sheet.")
        step("name the actors at the intersection; persona_resolve each (or bin/mt1pl --explain)")
        step("persona_read each declared sheet once; an undeclared actor stays a plain description")
        step("run the LENS: the four views apart, the persona and its inverse, restate from principles")
        step("write the tensions in your own voice; sign Author: Mentat (for " + pr + ")")
    else:
        v = say("GO", "use " + use + " for " + who + ", written for " + pr + ".")
        step("persona_resolve " + who + " (or sh bin/mt1pl --explain)")
        step("persona_read " + who + " once; cite the sheet by path")
        if use == "1":
            step("share the person's view, not their private facts; nothing from a SECRET file")
        if use == "2":
            step("the actor's jobs (watching) and clothes (showing, stating, reporting, knowing)")
        if use == "2" and o["roll"] == "yes":
            step("one bad-guy roll with bin/rf1bm --fate (a fold, never a sample), kept; then an inversion stage")
        if use == "3":
            step("tell the context as a story in your own voice; the actor's journal stays its own")
        step("persona_byline " + who + " " + pr + " (Author: " + who + " (for " + pr + "))")
        step("change the sheet only by persona_mutate with the entry, evidence and would_change all in hand")
        step("before hand-back: bin/cs1gk on any sheet that changed, persona_chain for generations; else NOT CHECKED")
    sys.stdout.write("\n".join(out + steps) + "\n")
    return CODES[v]


def sheet(path):
    name = actor = principal = journal = fiction = news = heading = fmname = fmmodel = infm = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh.read().split("\n"), 1):
            if i == 1 and re.match(r"^---[ \t]*$", line):
                infm = True
                continue
            if infm and re.match(r"^---[ \t]*$", line):
                infm = False
                continue
            if i <= 15 and infm and line.startswith("name:"):
                fmname = True
            if i <= 15 and infm and re.match(r"^(status|description):", line):
                low = re.sub(r"model[ \t]+this[ \t]+book", "", line.lower())
                if re.search(r"persona|model", low):
                    fmmodel = True
            if i <= 40 and re.match(r"^name:[ \t]*[^ \t]", line):
                name = True
            if i <= 40 and re.match(r"^actor:[ \t]*[^ \t]", line):
                actor = True
            if i <= 40 and re.match(r"^principal:[ \t]*[^ \t]", line):
                principal = True
            if i <= 15 and re.match(r"^#[ \t]+(character sheet|item sheet|persona)", line.lower()):
                heading = True
            if re.match(r"^#+[ \t].*([Jj]ournal|[Ll]og)", line):
                journal = True
            if re.match(r"^[Aa]ctor:[ \t]*fiction", line):
                fiction = True
            if "for fiction or analysis" in line:
                news = True
    out, miss = [], 0
    if actor:
        out.append("OK       actor:")
    elif heading:
        out.append("OK       a sheet heading (no actor: line)")
    elif fmname and fmmodel:
        out.append("OK       frontmatter names a persona model (name and description)")
    else:
        out.append("MISSING  actor: or a CHARACTER SHEET / PERSONA heading (how the server knows a sheet)")
        miss += 1
    out.append("OK       name:" if name else "DEFAULT  name: none, so the file name stands for it")
    out.append("OK       principal:" if principal else "DEFAULT  principal: none, so the tools assume Corwin (bin/mt1pl)")
    if journal:
        out.append("OK       a journal or log section")
    else:
        out.append("MISSING  a journal or log section (changes append there)")
        miss += 1
    if fiction and not news:
        out.append("MISSING  the NEWS mark a fiction sheet carries (for fiction or analysis)")
        miss += 1
    out.append("NOTCHK   the full gauge is bin/cs1gk (sections, guards, sidecar, corpus, twin, bad-guy stage)")
    sys.stdout.write("\n".join(out) + "\n")
    return 1 if miss else 0


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "refusals":
        sys.stdout.write(REFUSALS)
        return 0
    if cmd == "sheet":
        if len(argv) < 2:
            sys.stderr.write("pe1gt: no such sheet: \n")
            return 2
        try:
            return sheet(argv[1])
        except OSError:
            sys.stderr.write("pe1gt: no such sheet: %s\n" % argv[1])
            return 2
    if cmd != "plan":
        sys.stderr.write("usage: pe1gt plan --use N [...] | pe1gt refusals | pe1gt sheet FILE\n")
        return 2
    o = {v: "" for v in OPTS.values()}
    args = argv[1:]
    while args:
        if len(args) < 2:
            sys.stderr.write("pe1gt: %s needs a value\n" % args[0])
            return 2
        if args[0] not in OPTS:
            sys.stderr.write("pe1gt: unknown option %s\n" % args[0])
            return 2
        o[OPTS[args[0]]] = args[1]
        args = args[2:]
    return plan(o)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
