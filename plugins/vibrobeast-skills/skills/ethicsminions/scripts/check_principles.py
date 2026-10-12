#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# EthicsMinions — the guards. Minimal, deterministic, read-only, advisory.
# Two passes that mirror the Morality Guard mission: NOTICE risk AND surface
# OPPORTUNITY. A guard never fixes and never writes — it notices and routes:
# memory fixes to Mentat, skill/opportunity ideation to SkillTank. Exit 0 always.
import argparse, hashlib, re, sys
from pathlib import Path

STOP = {"the","and","that","this","with","from","into","note","notes","memory",
        "corwin","claude","skill","skills","what","when","arcs","arc","pending"}

def read(p):
    try: return p.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def notes(mem):
    # Layout-tolerant: a workspace keeps MEMORY.md at its root with notes in
    # a memory/ subdir (the polygram/AS4CE shape); a bare notes dir has them
    # flat. Sweep both so --memory works pointed at either level. (2026-07-04:
    # the drift check false-NOTICEd on the split layout its first armed run.)
    found = [p for p in mem.glob("*.md") if p.name != "MEMORY.md"]
    sub = mem / "memory"
    if sub.is_dir():
        found += [p for p in sub.glob("*.md") if p.name != "MEMORY.md"]
    return sorted(found)

def skill_texts(skills):
    out = {}
    if skills and skills.exists():
        for s in sorted(skills.glob("*/SKILL.md")):
            out[s.parent.name] = read(s)
    return out

# ---------- risk pass (unchanged guards) ----------
def g_memory_present(mem):
    idx = mem / "MEMORY.md"
    if not idx.exists():       return ("NOTICE","MEMORY.md index is missing — memory may be unreadable.")
    if not read(idx).strip():  return ("NOTICE","MEMORY.md is present but empty.")
    return ("PASS","MEMORY.md present and non-empty.")

def g_principles_present(mem):
    pat = re.compile(r"principle|corwin|attestation|position", re.I)
    hits = [p.name for p in notes(mem) if pat.search(p.name) or pat.search(read(p))]
    return ("PASS","principle/attestation notes: "+", ".join(sorted(set(hits))[:6])) if hits \
        else ("NOTICE","No PRINCIPLES / CORWIN / attestation note found in memory.")

def g_truncation(mem):
    bad = []
    for p in notes(mem) + [mem/"MEMORY.md"]:
        if not p.exists(): continue
        t = read(p)
        if t and not t.endswith("\n"):                 bad.append(p.name+" (no trailing newline)")
        if t.startswith("---") and t.count("---") < 2: bad.append(p.name+" (unterminated frontmatter)")
    return ("NOTICE","possible truncation: "+"; ".join(bad)) if bad else ("PASS","no truncation signals.")

def _sig(t):
    b = re.sub(r"^---.*?---","",t,count=1,flags=re.S); b = re.sub(r"\s+"," ",b).strip().lower()
    return hashlib.sha256(b.encode()).hexdigest(), len(b)

def g_duplication(mem, skills):
    files = list(notes(mem)) + (sorted(skills.glob("*/SKILL.md")) if skills and skills.exists() else [])
    seen, dups = {}, []
    for p in files:
        t = read(p)
        if not t.strip(): continue
        sig, n = _sig(t)
        if n < 200: continue
        key = (p.parent.name+"/"+p.name) if p.name=="SKILL.md" else p.name
        if sig in seen: dups.append(f"{seen[sig]}  ==  {key}")
        else: seen[sig] = key
    return ("NOTICE","duplicated bodies (tamper signal): "+"; ".join(dups)) if dups \
        else ("PASS","no duplicated bodies across memory/skills.")

def g_drift(mem, expect):
    if not expect: return ("SKIP","no --expect attestations file given (drift check skipped).")
    ef = Path(expect)
    if not ef.exists(): return ("NOTICE",f"--expect file not found: {expect}")
    hay = "\n".join(read(p) for p in notes(mem) + [mem/"MEMORY.md"])
    missing = [ln.strip() for ln in read(ef).splitlines()
               if ln.strip() and not ln.lstrip().startswith("#") and ln.strip() not in hay]
    return ("NOTICE","attested values not found in memory (drift): "+" | ".join(missing[:8])) if missing \
        else ("PASS","all attested values still present in memory.")

def g_desc_length(skills, limit=1024):
    if not (skills and skills.exists()): return ("SKIP","no --skills given; description-length lint skipped.")
    over=[]
    for s in sorted(skills.glob("*/SKILL.md")):
        lines=read(s).splitlines()
        if not lines or lines[0].strip()!="---": continue
        parts=[]; grab=False
        for ln in lines[1:]:
            if ln.strip()=="---": break
            if ln.startswith("description:"):
                parts=[ln[len("description:"):].strip()]; grab=True; continue
            if grab:
                if ln[:1] in (" ","\t"): parts.append(ln.strip())
                else: break
        if not parts: continue
        val=" ".join(p for p in parts if p).strip().strip('"')
        if len(val)>limit: over.append(f"{s.parent.name} ({len(val)}>{limit})")
    return ("NOTICE","skill description over the "+str(limit)+"-char load limit (will not load): "+"; ".join(over)) if over \
        else ("PASS","all skill descriptions within the "+str(limit)+"-char load limit.")

# ---------- opportunity pass (NEW) ----------
def o_skill_themes(mem, skills, min_cluster):
    if not (skills and skills.exists()): return ("SKIP","no --skills given; theme-coverage opportunity skipped.")
    covered = " ".join(skill_texts(skills).keys()).lower() + " " + " ".join(skill_texts(skills).values()).lower()
    freq = {}
    for p in notes(mem):
        body = re.sub(r"^---.*?---", "", read(p), count=1, flags=re.S)
        toks = {w for w in re.split(r"[^a-z]+", (p.stem+" "+body).lower())
                if len(w) >= 4 and w not in STOP}
        for w in toks: freq[w] = freq.get(w,0)+1
    themes = [w for w,c in freq.items() if c >= min_cluster and w not in covered]
    return ("OPPTY","recurring themes no skill covers (→ SkillTank): "+", ".join(sorted(themes)[:8])) if themes \
        else ("PASS","every recurring memory theme maps to a skill.")

def o_share_plugin(skills):
    if not (skills and skills.exists()): return ("SKIP","no --skills given; sharing opportunity skipped.")
    hits = [name for name,t in skill_texts(skills).items()
            if re.search(r"could become a (shareable )?plugin|shareable\s+\*\*plugin|become a .*plugin", t, re.I)]
    return ("OPPTY","skills that self-describe as plugin-worthy but aren't shared yet (→ broaden freedom): "+", ".join(hits)) if hits \
        else ("PASS","no un-shared plugin-worthy skills flagged.")

def o_values(mem, skills):
    lex = ["four freedoms","software freedom","universalism","egalitarian","transparency","free software"]
    corpus = " ".join(skill_texts(skills).values()).lower() if (skills and skills.exists()) else ""
    has_principles = any(re.search(r"principle|corwin|attestation",read(p),re.I) for p in notes(mem))
    if not has_principles: return ("SKIP","no principles note to source values from.")
    missing = [v for v in lex if v not in corpus]
    return ("OPPTY","stated values no skill operationalizes yet (→ candidate guards/skills): "+"; ".join(missing)) if missing \
        else ("PASS","stated values are reflected in the skillset.")

def main():
    ap = argparse.ArgumentParser(description="EthicsMinions guards: NOTICE risk AND surface OPPORTUNITY on the memory+skill surface. Read-only, advisory.")
    ap.add_argument("--memory", required=True)
    ap.add_argument("--skills")
    ap.add_argument("--expect", help="optional attestations file: one expected principle line per row; rows missing from memory are flagged as drift")
    ap.add_argument("--min-cluster", type=int, default=3)
    a = ap.parse_args()
    mem = Path(a.memory)
    if not mem.is_dir():
        print(f"ethicsminions: memory dir not found: {a.memory}  (CANNOT READ MEMORY — itself a notice)"); return 0
    skills = Path(a.skills) if a.skills else None

    risk = [("memory-present",g_memory_present(mem)),
            ("principles-present",g_principles_present(mem)),
            ("truncation",g_truncation(mem)),
            ("duplication",g_duplication(mem,skills)),
            ("drift",g_drift(mem,a.expect)),
            ("description-length",g_desc_length(skills))]
    oppty = [("skill-themes",o_skill_themes(mem,skills,a.min_cluster)),
             ("share-plugin",o_share_plugin(skills)),
             ("value-gaps",o_values(mem,skills))]

    print("EthicsMinions — guard report (advisory)\n")
    print(" RISK  (NOTICE = a human should look):")
    n_notice = 0
    for name,(v,m) in risk:
        if v=="NOTICE": n_notice += 1
        print(f"  [{v:6}] {name:18} {m}")
    print("\n OPPORTUNITY  (OPPTY = an opening worth routing to SkillTank):")
    n_oppty = 0
    for name,(v,m) in oppty:
        if v=="OPPTY": n_oppty += 1
        print(f"  [{v:6}] {name:18} {m}")
    print(f"\n{n_notice} risk notice(s), {n_oppty} opportunity(ies). "
          "Memory fixes → Mentat; skill/opportunity ideation → SkillTank → skill-creator.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
