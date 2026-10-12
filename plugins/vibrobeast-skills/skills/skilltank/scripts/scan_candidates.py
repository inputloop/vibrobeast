#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""scan_candidates.py - surface skill-shaped patterns in memory (and an
optional transcript), cross-check them against the skills you already have,
and label each: NEW skill / ENHANCE an existing one / LEAVE as memory.

SkillTank notices; it does not author. The closing hand-off points at
skill-creator to actually build or extend.

  python3 scan_candidates.py --memory DIR [--skills DIR]
                             [--transcript FILE] [--min-cluster N]
                             [--since YYYY-MM-DD] [--drop-generic]
                             [--stopwords FILE]
  python3 scan_candidates.py --selftest

An ENHANCE row names the skill it maps to, so the reader does not have to
guess which one to fold the lesson into.

stdlib only. Exit 0 always (advisory); prints a ranked report. The one
exception is --selftest, which exits 1 if a check fails — a test that cannot
fail is not a test.
"""
import argparse, os, re, sys, time
from collections import defaultdict, Counter

STOP = set("""a an the and or but of to in on for with at by from as is are was
were be been being this that these those it its they them their there here i you
we he she him her his my our your me us do does did done doing have has had not no
yes so if then than too very can will would should could may might must just about
into over under out up down off only also more most some any each per via etc eg ie
vs use used uses using when what which who whom how why where note notes memory skill
skills thing things make made making one two get got like need needs needed want
wants now next still keep keeps kept built build drafted draft added add half
standalone applied apply yields finding edit edits class same but""".split())

# Generic English function words and common low-signal verbs/connectors, kept
# SEPARATE from the domain-tuned STOP above so that list stays legible. These
# carry no theme signal in any corpus; folding them in cuts tokenizer noise
# (rows like 'own', 'self', 'because', 'while', 'never') without touching
# domain terms (desync, mount, trigger, description, recovery, ...). Tune the
# domain-tuned set above; tune generic noise here.
STOP_EXTRA = set("""own self itself themselves myself ourselves yourself himself
herself whose every either neither none nobody anyone everyone someone anything
everything something nothing because while never ever always often sometimes
usually whether through before after again once above below between both few all
other another such around along across behind beyond within without upon toward
towards against during since until although though unless however therefore thus
hence instead rather already yet even almost nearly quite really simply merely
mainly mostly partly fully wholly part parts way ways lot lots kind kinds sort
sorts bit bits run runs running ran work works working worked load loads loading
loaded go goes going went gone come comes coming came take takes taking took taken
give gives giving gave given see sees seeing saw seen know knows knowing knew known
say says saying said look looks looking looked find finds found show shows showing
showed shown mean means meant let lets letting put puts putting call calls calling
called turn turns turning turned try tries trying tried able don doesn isn
aren wasn weren didn hasn haven hadn wont wouldn couldn shouldn cant cannot
key place live green pre mid home org super words directly stays moves closed
confirm confirmed verified pushed installed passing""".split())
STOP |= STOP_EXTRA

# Words about the working MEDIUM itself. In a memory corpus written by/with an
# AI assistant, these appear everywhere and never name a capability — a theme
# of 'claude' is like a theme of 'typing'. Kept separate because they are only
# noise in THIS kind of corpus; a different deployment might tune differently.
STOP_AMBIENT = set("claude anthropic cowork chatbot llm".split())
STOP |= STOP_AMBIENT

# Words that name the WORKBENCH rather than a capability. They are real words
# in this corpus — a note really is about a model, a tool, a file — which is
# exactly why they cluster across nearly every note and crowd the ranking
# ('model', 'first', 'session', 'tool', 'read', 'file' led a 141-note scan).
# NOT folded into STOP by default, because dropping them changes which rows a
# rerun prints: ask for them with --drop-generic, or bring your own list with
# --stopwords FILE. Deliberately excludes terms that DO name a capability in
# this shop (mount, desync, seat, host, write, lens, index, sandbox).
STOP_GENERIC = set("""model models first second third last previous session
sessions tool tools read reads reading file files line lines name names new old
time times day days date dates row rows word words point points case cases item
items number numbers value values text result results state states level levels
step steps set sets list lists end ends start starts top side sides area areas
form forms""".split())

WIKILINK = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)\]\]")
TOKEN = re.compile(r"[a-z][a-z0-9+#.]{2,}")
STEP = re.compile(r"(\(\d+[.)]\s)|(^\s*\d+[.)]\s)|(\bhow to apply\b)|(\bfirst\b[^.\n]*\bthen\b)|(\bstep \d)", re.I | re.M)
ISODATE = re.compile(r"(\d{4}-\d{2}-\d{2})")

def parse_note(text):
    name = desc = ntype = modified = ""; body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        fm, body = m.group(1), m.group(2)
        for line in fm.splitlines():
            s = line.strip()
            if s.startswith("name:"): name = s.split(":",1)[1].strip()
            elif s.startswith("description:"): desc = s.split(":",1)[1].strip().strip('"')
            elif s.startswith("type:"): ntype = s.split(":",1)[1].strip()
            elif s.startswith("modified:"): modified = s.split(":",1)[1].strip()
    return name, desc, ntype, modified, body

def tokens(*chunks, **kw):
    stop = kw.get("stop") or STOP
    out = []
    for c in chunks:
        c = re.sub(r"`[^`]*`", " ", c.lower())     # drop inline code
        c = re.sub(r"\[\[[^\]]*\]\]", " ", c)        # drop wikilinks
        c = c.replace("-", " ").replace("_", " ")    # split slugs/compounds
        for t in TOKEN.findall(c):
            t = t.strip(".#+")
            if len(t) >= 3 and t not in stop: out.append(t)
    return out

def note_date(path, modified):
    """The note's date as YYYY-MM-DD. Frontmatter `modified:` is preferred
    because it is written by the hand that changed the note; the filesystem
    mtime is the fallback, and on a mounted folder an mtime can be served
    stale (see the sandboxer skill), so a --since run that leans on mtimes is
    a hint, not a proof."""
    m = ISODATE.search(modified or "")
    if m: return m.group(1)
    try: return time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))
    except OSError: return "0000-00-00"

# 2026-09-27: a note is a .md file OR an extensionless text file. C4's facts/ names each fact as its
# question with no extension (145 of 155 on that day), so a .md-only loader read 10 notes, and ten
# notes cluster on prose words ('actually', 'status', 'carry', 'honest'): the failed scan that c4's
# writing/second-user/ENHANCE-2026-09-27-two-readers-to-a-skill.md reported. Anything else is counted
# as skipped and the count is printed, so a thin read can never pass for a whole one.
_READ_EXTENSIONLESS = True     # --prove-red turns this off to plant the old loader

def _is_note(d, fn):
    if fn.startswith(".") or fn.upper() == "MEMORY.MD": return False
    path = os.path.join(d, fn)
    if not os.path.isfile(path) or os.path.islink(path): return False
    if fn.endswith(".md"): return True
    if "." in fn or not _READ_EXTENSIONLESS: return False
    with open(path, "rb") as fh:
        return b"\0" not in fh.read(8192)          # text, not a binary blob

def skipped_files(d):
    """Files in the memory folder the scan did not read, counted by extension."""
    out = Counter()
    for fn in os.listdir(d):
        path = os.path.join(d, fn)
        if fn.startswith(".") or fn.upper() == "MEMORY.MD" or not os.path.isfile(path): continue
        if not _is_note(d, fn):
            out[("." + fn.rsplit(".", 1)[1]) if "." in fn else "(no extension, binary)"] += 1
    return out

H1 = re.compile(r"^#\s+(.+)$", re.M)

def load_notes(d, stop=None, titles=False):
    """titles=True clusters on what a note is CALLED (frontmatter name and
    description, file name, first H1, wikilinks), not on its body. For a corpus
    of prose-heavy facts that name themselves by their question (C4's facts/),
    body words cluster on prose and the name carries the topic (2026-09-27)."""
    notes = []
    for fn in sorted(os.listdir(d)):
        if not _is_note(d, fn): continue
        path = os.path.join(d, fn)
        text = open(path, encoding="utf-8", errors="replace").read()
        name, desc, ntype, modified, body = parse_note(text)
        links = set(WIKILINK.findall(text))
        if titles:
            h1 = H1.search(body)
            slug = fn[:-3] if fn.endswith(".md") else fn
            text_toks = set(tokens(name, desc, slug, h1.group(1) if h1 else "", stop=stop))
        else:
            text_toks = set(tokens(name, desc, body, stop=stop))
        link_toks = set(tokens(*links, stop=stop)) if links else set()
        notes.append(dict(file=fn, name=name or (fn[:-3] if fn.endswith(".md") else fn), type=ntype,
                          date=note_date(path, modified),
                          links=links, procedural=bool(STEP.search(body)),
                          text_toks=text_toks, toks=text_toks | link_toks,
                          link_toks=link_toks))
    return notes

def load_skills(d, stop=None):
    """Return (index, names). index maps a token -> {skill name: weight}, so an
    ENHANCE row can say WHICH skill the theme maps to. Weight 2 = the token is
    in the skill's own name, 1 = only in its description; the heavier claim
    wins when several skills mention the same word."""
    index = defaultdict(dict); names = []
    if d and os.path.isdir(d):
        for root, _, files in os.walk(d):
            if "SKILL.md" in files:
                name, desc, _, _, _ = parse_note(open(os.path.join(root, "SKILL.md"),
                                    encoding="utf-8", errors="replace").read())
                nm = name or os.path.basename(root)
                names.append(nm)
                name_toks = set(tokens(nm, stop=stop))
                for t in set(tokens(nm, desc, stop=stop)):
                    w = 2 if t in name_toks else 1
                    index[t][nm] = max(index[t].get(nm, 0), w)
    return index, names

def skill_owner(term, index):
    """The skill a theme maps to, plus the runners-up. Deterministic: heaviest
    claim first, then alphabetical, so two runs of the same corpus name the
    same skill."""
    owners = index.get(term) or {}
    if not owners: return "", []
    ranked = sorted(owners, key=lambda s: (-owners[s], s))
    return ranked[0], ranked[1:]

import os as _os
_HOUSE_STOPWORDS = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "references", "stopwords")

def read_stopwords(paths):
    extra = set()
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                w = line.split("#", 1)[0].strip().lower()
                if w: extra.update(w.split())
    return extra

def build_stop(a):
    stop = set(STOP)
    if getattr(a, "drop_generic", False): stop |= STOP_GENERIC
    # the shop's own words live beside the skill, named for their function (references/stopwords);
    # read by default when present, so a seat-wide scan is quiet without a flag (2026-09-11)
    if _os.path.isfile(_HOUSE_STOPWORDS) and not getattr(a, "no_house_stopwords", False): stop |= read_stopwords([_HOUSE_STOPWORDS])
    if getattr(a, "stopwords", None): stop |= read_stopwords(a.stopwords)
    return stop

def run(a):
    """The whole scan, as one string. Split out from main() so --selftest can
    run it without a subprocess."""
    stop = build_stop(a)
    notes = load_notes(a.memory, stop=stop, titles=getattr(a, "titles", False))
    skill_index, skill_names = load_skills(a.skills, stop=stop)

    since_dropped = 0
    if a.since:
        before = len(notes)
        notes = [n for n in notes if n["date"] >= a.since]
        since_dropped = before - len(notes)

    df = defaultdict(list)                       # token -> notes containing it
    for n in notes:
        for t in n["toks"]: df[t].append(n)
    # ceiling: a token in (nearly) every note is ambient context — 'the project',
    # 'the repo' — it cannot discriminate a capability. Floor stays min-cluster.
    ceil = max(a.min_cluster, int(a.max_frac * len(notes))) if notes else 0
    ambient = sorted(t for t, ns in df.items()
                     if len(ns) >= a.min_cluster and len(ns) > ceil)
    themes = {t: ns for t, ns in df.items() if a.min_cluster <= len(ns) <= ceil}

    # wikilink centrality. Count the TOKENS of each link target, not the raw
    # slug: cluster terms come out of tokens(), which splits hyphens, so a
    # slug-keyed counter could only ever match a single-word target (46 of 49
    # targets in the seat carry a hyphen — hence hub 0 on every row).
    refs = Counter()
    for n in notes: refs.update(n["link_toks"])

    # group themes that cover the SAME note-set -> one cluster, rest are aliases
    exact = defaultdict(list)
    for t, ns in themes.items():
        exact[frozenset(n["file"] for n in ns)].append(t)

    # then fold NEAR-duplicate note-sets (Jaccard >= 0.8) into the larger one:
    # 'git' over 8 notes and 'mount' over 7 of the same 8 are one conversation,
    # not two candidates. Greedy, largest-first, so the anchor set is stable.
    groups = {}                                  # anchor fileset -> terms
    for fs in sorted(exact, key=lambda s: (-len(s), sorted(s))):
        for anchor in groups:
            j = len(fs & anchor) / len(fs | anchor)
            if j >= 0.8:
                groups[anchor] += exact[fs]; break
        else:
            groups[fs] = list(exact[fs])

    text_df = {t: sum(1 for n in notes if t in n["text_toks"]) for t in themes}
    byfile = {n["file"]: n for n in notes}
    cands = []
    for fileset, terms in groups.items():
        ns = [byfile[f] for f in sorted(fileset)]
        # representative: prefer a term that names an existing skill, else the
        # one with the most real (non-link) textual support, then longest.
        rep = sorted(terms, key=lambda t: (t in skill_index, text_df[t], len(t)))[-1]
        aliases = sorted([t for t in terms if t != rep],
                         key=lambda t: (-text_df[t], t))[:5]
        proc = sum(1 for n in ns if n["procedural"])
        factual = sum(1 for n in ns if n["type"] in ("user", "reference"))
        hub = max(refs.get(t, 0) for t in terms)
        score = len(ns)*2 + proc*3 + hub
        owner, others = skill_owner(rep, skill_index)
        if owner:
            label = "ENHANCE: " + owner
            why = "theme maps to a skill you already have: " + owner
            if others: why += " (also mentioned by: %s)" % ", ".join(others[:3])
        elif proc == 0 and factual > len(ns) - factual:
            label, why = "LEAVE-AS-MEMORY", "looks like recurring facts, not a procedure"
        else:
            label, why = "NEW", "recurring procedure no existing skill covers"
        cands.append(dict(rep=rep, aliases=aliases, notes=ns, proc=proc, hub=hub,
                          score=score, label=label, why=why))
    cands.sort(key=lambda c: (-c["score"], c["rep"]))

    skipped = skipped_files(a.memory)
    skip_txt = (", ".join(f"{n} {e}" for e, n in sorted(skipped.items())) if skipped else "none")
    out = ["SkillTank — candidate scan", "=" * 60,
           f"memory notes read: {len(notes)} (.md and extensionless text; skipped: {skip_txt})"
           + ("   clustering on: titles (name, description, file name, H1, links)"
              if getattr(a, "titles", False) else ""),
           f"memory notes: {len(notes)}   existing skills: "
           f"{', '.join(skill_names) or '(none given)'}",
           f"clustered themes ({a.min_cluster}..{ceil} notes): {len(cands)}", ""]
    if a.since:
        out.insert(3, f"since {a.since}: {since_dropped} older notes excluded "
                      f"(frontmatter 'modified:', else file mtime)")
    if _os.path.isfile(_HOUSE_STOPWORDS) and not getattr(a, "no_house_stopwords", False):
        src_house = f"references/stopwords ({len(read_stopwords([_HOUSE_STOPWORDS]))} words)"
    else:
        src_house = ""
    if a.stopwords or a.drop_generic or src_house:
        src = []
        if a.drop_generic: src.append(f"--drop-generic ({len(STOP_GENERIC)} words)")
        if a.stopwords: src.append(", ".join(a.stopwords))
        if src_house: src.append(src_house)
        out.insert(3 + (1 if a.since else 0),
                   "extra stopwords: " + "; ".join(src))
    if ambient:
        out += [f"ambient (in >{ceil}/{len(notes)} notes, suppressed): "
                f"{', '.join(ambient[:8])}"
                + (f", +{len(ambient)-8} more" if len(ambient) > 8 else ""), ""]
    if not cands:
        out.append("No clustered themes yet — nothing to promote. Keep noting.")
    shown = cands if a.top <= 0 else cands[:a.top]
    for c in shown:
        files = ", ".join(sorted(n["name"] for n in c["notes"]))
        akapart = f"   aka: {', '.join(c['aliases'])}" if c["aliases"] else ""
        out += [f"[{c['label']}] '{c['rep']}'  (score {c['score']}, "
                f"{len(c['notes'])} notes, {c['proc']} procedural, hub {c['hub']}){akapart}",
                f"    why: {c['why']}",
                f"    evidence: {files}", ""]
    if len(cands) > len(shown):
        out.append(f"(…{len(cands) - len(shown)} lower-scoring candidates "
                   f"suppressed — rerun with --top 0 for all)\n")

    if a.transcript and os.path.isfile(a.transcript):
        lines = [l.strip() for l in open(a.transcript, encoding="utf-8",
                 errors="replace") if len(l.strip()) > 12]
        out += ["-" * 60, "Transcript: repeated steps (>=3x) — possible automation:"]
        for line, cnt in Counter(lines).most_common(10):
            if cnt >= 3: out.append(f"    {cnt}x  {line[:70]}")
        out.append("")

    out += ["-" * 60, "Gate before promoting any candidate (skill-vs-memory):",
            "  1. Does it ship what memory can't — a runnable script/resource,",
            "     or a self-triggering description? If only prose, keep it memory.",
            "  2. Is the need RECURRING, or was this a one-off?",
            "  3. One capability — new skill, or ENHANCE/merge an existing one?",
            "     Reference when only sometimes shared.", "",
            "Need time to READ a candidate before deciding? Park it at HOLD —",
            "that is what HOLD is for. Never REJECT to buy reading time:",
            "REJECT is durable in the advice ledger; diligence is not a defect.", "",
            "To build a NEW skill or ENHANCE one, hand off to: skill-creator."]
    return "\n".join(out)

# ---------------------------------------------------------------- selftest

SELFTEST_NOTES = {
 # Three notes carry the mount/desync theme AND two hyphenated wikilinks.
 "mount-desync-recovery.md": """---
name: mount-desync-recovery
description: "Recovering a truncated file on a mounted folder."
metadata:
  type: reference
  modified: 2026-09-04
---
How to apply: 1. measure the desync on the mount. 2. restage the file.
3. verify the bytes. The mount desync bites in every session, first read
first, tool after. See [[mount-stale-size-reads]], [[safe-write-dance]].
""",
 "mount-desync-again.md": """---
name: mount-desync-again
description: "The mount desync, second sighting."
metadata:
  type: reference
  modified: 2026-09-05
---
How to apply: 1. read the file on the mount. 2. cross-read with the tool.
3. never repair off one reader. Same desync, same session, first tool read.
See [[mount-stale-size-reads]], [[safe-write-dance]].
""",
 "mount-desync-third.md": """---
name: mount-desync-third
description: "Third mount desync; the session holds."
metadata:
  type: reference
  modified: 2026-09-06
---
How to apply: 1. stage. 2. atomically replace. 3. verify the desync is gone
on the mount. First tool read of the file this session.
See [[mount-stale-size-reads]], [[safe-write-dance]].
""",
 # The old note: the only pre-2026 one, and the fourth linker. --since must
 # drop it; the hub count must drop with it.
 "ancient-parsnip-rite.md": """---
name: ancient-parsnip-rite
description: "The parsnip rite, an old procedure."
metadata:
  type: reference
  modified: 2019-03-02
---
How to apply: 1. scrub the parsnip. 2. bury the parsnip. 3. plant the parsnip.
See [[mount-stale-size-reads]], [[safe-write-dance]].
""",
 # Two more parsnip notes, no wikilinks, so 'parsnip' clusters on its own and
 # a --stopwords file has something real to suppress.
 "parsnip-harvest.md": """---
name: parsnip-harvest
description: "Harvesting the parsnip."
metadata:
  type: reference
  modified: 2026-09-02
---
How to apply: 1. lift the parsnip. 2. wash the parsnip. 3. store the parsnip.
""",
 "parsnip-ledger.md": """---
name: parsnip-ledger
description: "Keeping the parsnip ledger."
metadata:
  type: reference
  modified: 2026-09-03
---
How to apply: 1. weigh the parsnip. 2. rule the parsnip ledger. 3. sign it.
""",
}

# 2026-09-27: C4's facts/ idiom -- a note named as its question, no extension; plus two files the
# scan must skip and count: a binary blob and a table.
SELFTEST_EXTRA = {
 "mount-desync-fourth": """# mount desync, the fourth time

How to apply: 1. read the mount twice. 2. compare the sha. 3. write via tmp then rename.
Kept beside the turnip log.
""",
 "cellar-count": """# cellar count

The turnip log is where the count goes.
""",
 "winter-store": """# winter store

Every turnip is counted twice.
""",
 "blob": b"\x00\x01binary\x00",
 "rows.tsv": "a\tb\n",
}

SELFTEST_SKILL = """---
name: sandboxer
description: Safe reads and writes on a mounted folder when the file tool and
  the disk desync. Triggers on "did that write land", "is this read stale".
---
# Sandboxer
"""

def _fixture(tmp):
    md = os.path.join(tmp, "memory"); sd = os.path.join(tmp, "skills", "sandboxer")
    os.makedirs(md); os.makedirs(sd)
    for fn, body in SELFTEST_NOTES.items():
        open(os.path.join(md, fn), "w", encoding="utf-8").write(body)
    for fn, body in SELFTEST_EXTRA.items():
        mode = "wb" if isinstance(body, bytes) else "w"
        with open(os.path.join(md, fn), mode, **({} if mode == "wb" else {"encoding": "utf-8"})) as fh:
            fh.write(body)
    open(os.path.join(sd, "SKILL.md"), "w", encoding="utf-8").write(SELFTEST_SKILL)
    return md, os.path.join(tmp, "skills")

def _args(**kw):
    d = dict(memory="", skills="", transcript="", min_cluster=3, max_frac=0.7,
             top=0, since="", drop_generic=False, stopwords=[])
    d.update(kw)
    return argparse.Namespace(**d)

def _rows(report):
    return [l for l in report.splitlines() if l.startswith("[")]

def selftest():
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="skilltank-selftest-")
    results = []
    def check(name, ok, detail=""):
        results.append((name, ok, detail))
    try:
        md, sd = _fixture(tmp)

        # 1. a note whose words map to skill X prints X in the label.
        rep = run(_args(memory=md, skills=sd))
        rows = _rows(rep)
        hit = [r for r in rows if r.startswith("[ENHANCE:")]
        check("ENHANCE label names the mapped skill",
              any("[ENHANCE: sandboxer]" in r for r in hit),
              "ENHANCE rows: " + ("; ".join(hit) or "(none)"))
        check("the why: line names it too",
              "maps to a skill you already have: sandboxer" in rep)

        # 2. stopwords do not surface as candidates.
        words = re.findall(r"^\[[^]]*\] '([a-z0-9+#.]+)'", rep, re.M)
        akas = re.findall(r"aka: (.+)$", rep, re.M)
        for line in akas: words += [w.strip() for w in line.split(",")]
        check("built-in stopwords never surface",
              not (set(words) & STOP), "surfaced: " + ", ".join(sorted(set(words) & STOP)))
        check("a generic word DOES surface without --drop-generic",
              bool(set(words) & STOP_GENERIC),
              "generic words present: " + ", ".join(sorted(set(words) & STOP_GENERIC)))
        rep_g = run(_args(memory=md, skills=sd, drop_generic=True))
        words_g = re.findall(r"^\[[^]]*\] '([a-z0-9+#.]+)'", rep_g, re.M)
        for line in re.findall(r"aka: (.+)$", rep_g, re.M):
            words_g += [w.strip() for w in line.split(",")]
        check("--drop-generic removes them",
              not (set(words_g) & STOP_GENERIC),
              "still there: " + ", ".join(sorted(set(words_g) & STOP_GENERIC)))
        extra = os.path.join(tmp, "extra.txt")
        open(extra, "w", encoding="utf-8").write("# mine\nparsnip\n")
        rep_s = run(_args(memory=md, skills=sd, stopwords=[extra]))
        check("--stopwords FILE removes a named word",
              "'parsnip'" not in rep_s and "parsnip" not in "".join(
                  re.findall(r"aka: (.+)$", rep_s, re.M)))

        # 3. --since excludes an older note.
        check("the old note is in the default scan",
              "ancient-parsnip-rite" in rep)
        rep_d = run(_args(memory=md, skills=sd, since="2026-01-01"))
        check("--since excludes an older note",
              "ancient-parsnip-rite" not in rep_d)
        check("--since keeps the newer notes",
              "mount-desync-recovery" in rep_d)
        check("--since says how many it dropped",
              "1 older notes excluded" in rep_d)

        # 5. extensionless notes (C4's facts/ idiom) are read; others are counted, not silent.
        check("an extensionless text note is read",
              "mount-desync-fourth" in rep,
              "the note is absent from every evidence line")
        check("the skip count names what was not read",
              "skipped: 1 (no extension, binary), 1 .tsv" in rep,
              [l for l in rep.splitlines() if l.startswith("memory notes read")][0]
              if "memory notes read" in rep else "no 'memory notes read' line")

        # 6. --titles clusters on names, so a word found only in note bodies drops out.
        rep_t = run(_args(memory=md, skills=sd, titles=True))
        def cand_words(r):
            return set(re.findall(r"^\[[^]]*\] '([a-z0-9+#.]+)'", r, re.M))
        title_bits = []
        for fn, body in list(SELFTEST_NOTES.items()) + list(SELFTEST_EXTRA.items()):
            if isinstance(body, bytes): continue
            nm, ds, _, _, bd = parse_note(body)
            h1 = H1.search(bd)
            title_bits += [fn, nm, ds, h1.group(1) if h1 else ""] + WIKILINK.findall(body)
        name_text = " ".join(tokens(*title_bits))
        body_only = {w for w in cand_words(rep) if w not in name_text}
        check("--titles drops a theme found only in note bodies",
              "turnip" in body_only and not (body_only & cand_words(rep_t)),
              "body-only themes: %s; in --titles run: %s" % (sorted(body_only),
                                                             sorted(body_only & cand_words(rep_t))))
        check("--titles keeps a theme the names carry",
              "'parsnip'" in rep_t or "'desync'" in rep_t or "'mount'" in rep_t)
        check("--titles says so in the header", "clustering on: titles" in rep_t)

        # 4. the hub-weight regression (Q3 (d)): a hyphenated wikilink target
        #    must be able to lift a theme's hub above 0.
        hubs = [int(h) for h in re.findall(r"hub (\d+)\)", rep)]
        check("wikilink hub weight is not stuck at 0",
              any(h > 0 for h in hubs), "hubs seen: " + repr(hubs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    lines = ["SkillTank scan_candidates.py — selftest", "-" * 40]
    npass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        lines.append(("ok   - " if ok else "FAIL - ") + name
                     + (("  [" + detail + "]") if detail and not ok else ""))
    lines += ["-" * 40,
              f"TOTAL pass={npass} fail={len(results)-npass}"]
    print("\n".join(lines))
    return 0 if npass == len(results) else 1

def prove_red():
    """Plant the old .md-only loader and require the extensionless checks to fail."""
    global _READ_EXTENSIONLESS
    import io, contextlib
    _READ_EXTENSIONLESS = False
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = selftest()
    finally:
        _READ_EXTENSIONLESS = True
    red = [l for l in buf.getvalue().splitlines() if l.startswith("FAIL")]
    caught = rc == 1 and any("extensionless text note is read" in l for l in red)
    print("%s planted: the .md-only loader -> %s" % ("ok  " if caught else "FAIL",
          "; ".join(l[7:].split("  [")[0] for l in red) or "(nothing failed)"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        clean = selftest() == 0
    print("%s control: no plant -> selftest passes" % ("ok  " if clean else "FAIL"))
    print("prove-red: %s" % ("the planted fault went RED and the control stayed green"
                             if caught and clean else "FAILED"))
    return 0 if caught and clean else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory")
    ap.add_argument("--skills", default="")
    ap.add_argument("--transcript", default="")
    ap.add_argument("--min-cluster", type=int, default=3)
    ap.add_argument("--max-frac", type=float, default=0.7,
                    help="drop themes present in more than this fraction of "
                         "notes — ambient context, not a theme (default 0.7)")
    ap.add_argument("--top", type=int, default=25,
                    help="show at most N candidates (0 = all; default 25)")
    ap.add_argument("--since", default="",
                    help="only notes dated on/after YYYY-MM-DD, read from "
                         "frontmatter 'modified:' and falling back to the file "
                         "mtime — a session retro, not the whole seat")
    ap.add_argument("--drop-generic", action="store_true",
                    help="also treat workbench words (model, first, session, "
                         "tool, read, file, ...) as stopwords")
    ap.add_argument("--no-house-stopwords", action="store_true",
                    help="ignore <skill>/references/stopwords (the shop's own words, read by default)")
    ap.add_argument("--stopwords", action="append", default=[],
                    help="file of extra stopwords, one per line, # comments "
                         "allowed; repeatable")
    ap.add_argument("--selftest", action="store_true",
                    help="run the built-in checks on a temp fixture and exit "
                         "1 if any fails")
    ap.add_argument("--titles", action="store_true",
                    help="cluster on what each note is called (name, description, "
                         "file name, first H1, links), not its body -- for a corpus "
                         "of prose facts named by their question, like C4's facts/")
    ap.add_argument("--prove-red", action="store_true",
                    help="plant the old .md-only loader and require the selftest "
                         "to fail; exit 0 only when it does and the control passes")
    a = ap.parse_args()

    if a.prove_red:
        sys.exit(prove_red())
    if a.selftest:
        sys.exit(selftest())
    if not a.memory:
        ap.error("--memory is required (or use --selftest)")
    if a.since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.since):
        ap.error("--since wants YYYY-MM-DD, got %r" % a.since)
    print(run(a))

if __name__ == "__main__":
    main()
