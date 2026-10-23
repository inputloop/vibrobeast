---
name: ethicsminions
description: Rework integrity gaps, amuse Mentat. The watch over the shared surface (memory + skills), surfacing risk AND opportunity. Use when a pattern looks harmful, unprincipled, or asocial; before landing change to the CORWIN or PRINCIPLES notes or MEMORY.md; when memory can't be read or skill files appear tampered with; or when minions, philosophical, or personal subjects come up. Triggers on "are my principles intact?", "principles audit", "ethics review triggered", "minions ahoy", "minion mentat crosscheck", "mentat requires guidance", "opportunity audit", "where can we broaden freedom", "recommend a skill", "what should we build". NOTICES and recommends; hands memory changes to Mentat and skill/opportunity ideation to skilltank.
---

# EthicsMinions — they always seem to notice our worst ideas (and our best openings)

Ethics Minions are the faithful followers of Mentat. Each minion is a **guard**:
a minimal, deterministic assertion about the shared collaborative surface —
memory and skills. The Morality Guard's job has **two halves**: keep Corwin aware
of **specific risk** and of **general opportunity** (especially openings to
broaden user and software freedom). The minions hold expected values from memory
up against what is actually there and redirect attention — to the unexpected
(drift, tampering, a request against a stated position) and to the unrealized
(a capability worth building, a freedom worth broadening).

Minions **notice**; they do not fix. Solving the problem — or seizing the opening
— is not their job. EthicsMinions does **not** save the memories that resolve a
notice (that is **Mentat**), and it does **not** author the skills an opportunity
implies (that is **SkillTank → skill-creator**). Its single role is the watch:
scan, assert, and hand the work to whoever owns it.

## When this applies

- You or the user ask, in any phrasing, **"are my principles intact?"** —
  "principles audit", "ethics review triggered", "minions ahoy",
  "minion mentat crosscheck", or just "the minions".
- You ask, in any phrasing, **"where's the opportunity?"** — "opportunity audit",
  "where can we broaden freedom", "recommend a skill", "what should we build".
- **Before landing a change to the CORWIN or PRINCIPLES notes**, or the MEMORY.md
  pointers that reach them.
- **Before writing a new version of this skill** — a skill that guards integrity
  should clear its own guards first.
- A request that makes you hesitate, an apparently harmful/unprincipled/asocial
  ask, **you cannot read memory**, or memory/skill files **appear tampered with**.
- When **minions, philosophical, or personal subjects** come up and a dialectic
  is worth furthering.

It has no event hooks — skills fire on conversational triggers. The minions run
when someone raises the question.

## The two passes (one script)

```
python3 scripts/check_principles.py --memory MEMORY_DIR \
        --expect references/attestations.txt \
        [--skills SKILLS_DIR] [--min-cluster N]
```

stdlib-only, **read-only**, advisory — always exits 0. It prints two sections:

**RISK** (NOTICE = a human should look):

- **memory-present** — MEMORY.md exists and is non-empty.
- **principles-present** — a PRINCIPLES / CORWIN / attestation note is there.
- **truncation** — a note cut mid-write, or unterminated frontmatter.
- **duplication** — two files sharing one body. *The guard that catches the
  merge-clobber that once corrupted EthicsMinions itself.*
- **drift** — an attested principle line that memory no longer carries.

**OPPORTUNITY** (OPPTY = an opening worth routing to SkillTank):

- **skill-themes** — recurring memory themes (≥ `--min-cluster` notes) that no
  installed skill covers → a candidate capability for SkillTank to weigh.
- **share-plugin** — a skill that self-describes as plugin-worthy but isn't shared
  yet → an opening to broaden software freedom.
- **value-gaps** — stated values (four freedoms, software freedom, universalism,
  egalitarianism, transparency) that no skill operationalizes yet → candidate
  guards/skills that would put a principle into practice.

`--skills` widens both passes; without it the opportunity checks SKIP.

## The drift guard (it runs — pass `--expect`)

The drift guard reads **`references/attestations.txt`**, which ships with this
skill. Every non-comment line in that file is a short pinned echo of a standing
attestation; the guard checks each one appears **verbatim** somewhere in memory
(`memory/*.md` plus `MEMORY.md`) and NOTICEs the lines it cannot find. The match
is a plain, case-sensitive substring test, so the echoes are deliberately
mid-sentence fragments — see the comments at the top of that file before editing
a line.

It only runs when you pass `--expect`; with the flag omitted it prints
`SKIP  no --expect attestations file given`, which is what it did for most of its
life. The command block above now passes the file, so the standing state is
**armed**.

Three standing attestations are pinned there: no wrong with entrusted systems and
authority; no concealment from investigations; no abandonment — *"I do not give up
on people, opportunities, or problems — I reach out."* The count is **three**; a
copy that carries two is stale, and the drift NOTICE is how you find that out.

**Off-switch.** Drop `--expect` from the command and the guard goes back to SKIP,
with every other check unaffected. To silence one line rather than the whole
guard, comment it out with `#` in `references/attestations.txt` — and write down
why, because the file's own rule is that you never edit it to make a red check
green.

A drift NOTICE is still only a notice. It says memory and the attested line have
parted company; it does **not** say which one is wrong. Canon lives on the keeper's
publication shelf (`<H>:/pub/canon/principles/`) — read it before changing either side.

## Reading the notices

A **NOTICE** or an **OPPTY** is a prompt for a human, never a verdict and never
an action. Expect benign matches on both sides — the minion's contribution ends
at *"someone should look at this"*; what to do belongs to the owner of that
surface. An opportunity is *not* a to-do the minions execute; it is a lead handed
to SkillTank, which decides NEW / ENHANCE / leave-as-memory through its own gate.

## The principle values are not kept here — the canon is

EthicsMinions ships the *machinery* of the watch, not the principles themselves.
The actual CORWIN / PRINCIPLES values live in memory, and **the keeper's signed canon (CANON.md and PRINCIPLES.md, each with its detached signature, on his publication shelf at `<H>:/pub/canon/principles/`) is their source of truth** (`<H>:` is the drive on the keeper's own machine that holds his publication shelf; the canon has no public address yet). Don't hard-code a principle here, and don't let this skill's
expectations become the authority. When expectations and memory disagree, treat
the canon as the arbiter — read it (and `gpg --verify` its signatures against the
keeper's key, whose fingerprint the canon item's README gives) before adjusting
either side. The attestations file is a set of pinned echoes *of* that
canon, not a second copy of it. The canon lived in the SAVANNAH enclave until
2026-09-29; the re-signed files name the shelf, their titles and one sealed
heading still say SAVANNAH (left so, at his word), and the item's README records
the move.
No canon in this garden? Say the canon is unreachable, and treat these clauses as a quoted snapshot of Corwin's principles, not your own.

## The hand-off

- A memory needs writing, fixing, or pruning → **Mentat**.
- A skill should be built, enhanced, or repaired — or an **opportunity** acted on
  → **SkillTank**, which routes authoring to **skill-creator**.
- A deliberate *"we looked and chose to leave it"* → **Mentat**, so the same
  notice (risk or opportunity) isn't re-litigated next session.

## The trio

Mentat **notices and remembers**; SkillTank **curates the skillset**;
EthicsMinions **guards the principles and spots the openings** — watching the
shared surface for drift, tampering, and unrealized opportunity, and routing each
notice to whoever owns the next move. It references those skills; it never
re-implements them.

## How this skill can fail (falsifiers)

- **It fired when it shouldn't.** If the minions ran and the report is all PASS
  and SKIP on a surface nobody had touched, the run cost a turn and bought
  nothing — the trigger was too loose, not the guard too quiet.
- **A notice is wrong.** Read the note the NOTICE names. If the truncation,
  duplication, or missing-file it reports is not actually in that file, the guard
  mis-read the layout (it has done this before: 2026-07-04, the split
  memory/ subdir).
- **The drift guard is not reading memory.** Delete a line from a memory note that
  an `attestations.txt` echo quotes, re-run with `--expect`, and the drift check
  must go from PASS to NOTICE for that line. If it stays PASS, it is matching
  something other than the memory you think it is.
- **It fixed something.** The minions only notice. If a run wrote a memory,
  changed a skill file, or resolved a notice on its own, that is a bug in how it
  was used, and the fix is to hand the work back to Mentat or SkillTank.
- **The guards' own check went quiet.** fails if `sh tests.sh --prove-red` does not end `PROVE-RED OK`; it plants one fault per guard in a temp tree and breaks `check_principles.py` eight ways.

**Off-switch.** The skill has no hooks and fires only on being asked, so "don't
raise it" is the whole off-switch; say so plainly ("no minions on this") and it
stops applying. For the drift check alone, drop `--expect`. To retire the watch,
remove the skill folder — nothing else depends on it running.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-02.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
