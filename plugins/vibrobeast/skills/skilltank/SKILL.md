---
name: skilltank
description: Spot skill-shaped patterns and decide whether they earn a skill. Use when you or the user step back to ask "should this be a skill?", "is this skill-shaped?", "should we make/extend a skill for this?" at an end-of-project retro, or when a repeated manual procedure or a cluster of related memory notes suggests a capability worth capturing. Scans memory (and an optional transcript) for recurring themes, cross-checks them against the skills you already have, and labels each NEW / ENHANCE / LEAVE-AS-MEMORY. Triggers on "should this be a skill", "find skill candidates", "review our skills", "audit memory for skills", "what have we done repeatedly", "is there a skill in this", "rainbow pass", "what skill am I missing". Also covers promotion etiquette at the desk — "promote this candidate", "hold or reject?" — HOLD is the reading room; REJECT is durable and never a pause button. It NOTICES and recommends; it hands authoring to skill-creator.
---

# SkillTank — where capabilities are cultured

A tank doesn't build the thing; it grows a candidate until you can see what
it is, then you decide whether to decant it. SkillTank looks back over what
you've been doing — the notes Mentat kept, the procedures you repeated — and
surfaces the patterns that *might* be skill-shaped. It does not author skills
(that is **skill-creator**) and it does not take notes (that is **Mentat**).
Its one job is the judgment in between: *is there a skill here, and is it new
or an enhancement?*

## When this applies

- You or the user ask, in any phrasing, **"should this be a skill?"** —
  including "is this skill-shaped?", "should we make a skill for this?",
  "is there a skill in what we just did?"
- An **end-of-project / end-of-session retro**: a deliberate look back for
  capabilities worth keeping.
- A **smell** worth checking: a cluster of related memory notes piling up on
  one theme, or the same manual procedure run several times across a session.

It does **not** fire on every memory write or every Sandboxer action — skills
have no event hooks, only conversational triggers. SkillTank runs when someone
*asks the question*, not automatically.

## The scan

```
python3 scripts/scan_candidates.py --memory MEMORY_DIR \
        [--skills SKILLS_DIR] [--transcript FILE] [--min-cluster N]
        [--max-frac F] [--top N] [--since YYYY-MM-DD]
        [--drop-generic] [--stopwords FILE] [--no-house-stopwords] [--titles]

python3 scripts/scan_candidates.py --selftest
python3 scripts/scan_candidates.py --prove-red
```

- `--memory` — the memory directory (the folder holding the notes and
  `MEMORY.md`). Required. A note is a `.md` file or an extensionless text file
  (C4's `facts/` names each fact as its question, with no extension). The
  first line says how many notes were read and what was skipped, by
  extension: check it against the folder before reading the ranking. Before
  2026-09-27 only `.md` was read, so a scan of `c4/facts` read 10 of 155.
- `--skills` — a directory tree of installed/staged skills (each a folder
  with a `SKILL.md`). Lets the scan say ENHANCE vs NEW instead of guessing,
  and lets an ENHANCE row name the skill it maps to.
- `--transcript` — an optional saved transcript; flags steps repeated 3+
  times as automation candidates.
- `--min-cluster` — how many notes must share a theme before it counts
  (default 3).
- `--max-frac` — the *ceiling*: a theme present in more than this fraction
  of all notes (default 0.7) is ambient context — the project's own name,
  the working medium — and is suppressed (listed on one line, not ranked).
- `--top` — show at most N candidates (default 25; 0 = all). The tail is
  counted, not printed.
- `--since` — only notes dated on or after this day, so a session retro scans
  today's notes instead of the whole seat. The date comes from the note's
  frontmatter `modified:`, falling back to the file's mtime — and a mount can
  serve a stale mtime (`sandboxer`), so on a mounted seat read a `--since` run
  as a narrowing convenience, not as proof of what changed today.
- `--drop-generic` — also treat workbench words (`model`, `first`, `session`,
  `tool`, `read`, `file`, and about sixty of their kin) as stopwords. Left
  off, those words crowd the top of the ranking, because they genuinely are in
  nearly every note; turn it on for a retro where you want only
  capability-shaped words. It is off by default so that rerunning the plain
  command still prints the rows the last run printed.
- `--stopwords FILE` — your own extra stopwords, one per line, `#` comments
  allowed, repeatable. For the words that are ambient in *your* corpus — a
  project codename, a recurring person's name — without editing the script.
- `references/stopwords` — the shop's own vocabulary (people, seats, personas, method words, and
  container words such as note and fact), one
  per line, read **by default** so a seat-wide scan is quiet without a flag; `--no-house-stopwords`
  ignores it. Named for its function and kept beside the skill so it travels with skilltank when
  packed or unpacked (2026-09-11). A seat may add its own list with `--stopwords FILE`.
- `--titles` — cluster on what each note is *called* (frontmatter name and
  description, file name, first H1, wikilinks) instead of its body. Use it on
  a corpus of prose facts that name themselves by their question: there the
  body words that cluster are prose (`status`, `exactly`, `right`), and one
  round of stopwords only surfaces the next layer (`design`, `context`,
  `minted`). On `c4/facts`, 2026-09-27, `--titles` ranked mechanism, shaped,
  readers, registry, seam, where the body scan ranked status, exactly,
  mechanism, right, whole.
- `--selftest` — run the built-in checks against a throwaway fixture and exit
  1 if any fails. `--prove-red` plants the old `.md`-only loader and exits 0
  only when the selftest goes red under it and passes without it. Everything else here always exits 0; this is the one command
  allowed to go red, because a check that cannot fail is not a check.

stdlib-only, read-only, advisory (always exits 0 — `--selftest` excepted). It
clusters themes across notes, folds same-note-set themes into one row (rest
shown as `aka:`), merges *near*-duplicate clusters (Jaccard ≥ 0.8 — 'git' over
8 notes and 'mount' over 7 of the same 8 are one conversation, not two
candidates), counts how many notes in a cluster read as *procedural* (a "How
to apply:" / numbered steps smell), and uses wikilink references as a
centrality hint.

The `hub` number on each row is that centrality hint: how many notes point at
a `[[target]]` whose name carries the word. It read **0 on every row** until
2026-09-11, when the counter turned out to be keyed by the whole wikilink slug
(`memory-stores-map`) while the themes are keyed by single words — and 46 of
the seat's 49 link targets carry a hyphen, so nothing could ever match. It now
counts the words *inside* each target, so a row with a high hub is a theme the
rest of the notes keep pointing at.

## Reading the labels

- **NEW** — a recurring *procedure* no existing skill covers. A real
  candidate; take it to the gate below.
- **ENHANCE: `<skill>`** — the theme already maps to a skill you have, and the
  row **names it**; where several skills mention the word, the runners-up
  follow on the `why:` line. Don't spawn a rival; fold the new lesson into the
  named skill (this is the common, healthy outcome — most findings enhance,
  few found). If the name looks wrong, the representative word is usually a
  generic one that some skill's description happens to contain — rerun with
  `--drop-generic` and see whether the row survives.
- **LEAVE-AS-MEMORY** — recurring *facts*, not a procedure. Facts are
  Mentat's job; they don't become skills.
- **RAISE: `<work>`** — a recurrence that is *test-shaped*: the same class of
  fault turned up again (across two works or tools, or a check caught passing
  over a real fault). It does not become a skill: raise the TESTMANIFEST step of
  the works that touch it (the soft skill `grand-test-manifest`; in C4,
  `spells/ratchet/`). PROVISIONAL, as those are (his Q534-Q542). The scanner
  does not print this label; it is a reading at the gate (ERRATA E14,
  2026-09-29).

A label is a prompt, not a verdict. Always run the candidate through the gate.

## The gate (skill-vs-memory)

1. Does it ship what memory can't — a **runnable script/resource**, or a
   **self-triggering description**? If the payoff is only prose, it stays a
   memory note.
2. Is the need **recurring**, or was this a one-off?
3. **One capability.** New skill, or does it ENHANCE / merge into an existing
   one? Merge only when two capabilities are *always* needed together;
   reference (one-way) when only *sometimes*; otherwise one skill = one
   capability.

## The reading room (promotion etiquette)

When a candidate reaches polygram's desk, three verbs exist and they are not
interchangeable. **HOLD** parks a candidate for review — it is *not terminal*
and never overrides the ledger. **PASS / promote** synthesizes. **REJECT is
durable**: it lands in the advice ledger and only a later deliberate promote
clears it.

The etiquette that follows from those semantics:

- *"Have I read this thing I'm going to sign?"* is the right question, always.
  The signing is the moment that confers the dignity; nothing before it is.
- Need time to read? **Park at HOLD.** That is what HOLD is for — a reading
  room, not a penalty box. Wanting to think is not a problem to route around.
- **Never REJECT to buy reading time.** A reject-then-promote pair leaves a
  durable scar in the ledger that records diligence as refusal. If you find
  such a pair, it usually means the operator needed a pause and the tooling
  only offered a "no".
- Signing happens inside the blessed path (`dist` / release tooling in-signs).
  Don't hand-roll signing wrappers to compensate for a pause you didn't know
  you were allowed to take.

## The rainbow pass — rainbow-tank (after Bryant's Rainbow_Eval v1.0)

Credited import, folded not forked: the boundary-scan method from Bryant
Frankford's Rainbow_Eval (Gauntlet Nexus, 2026-07-06), run under this
shop's gates. Trigger: "rainbow pass", "rainbow-tank", "rainbow eval",
"what skill am I missing", "fill the gap".

1. **Lay out the spectrum** — every installed skill: name, one-line lane,
   declared boundaries. Bands, not judgments.
2. **Find gaps at the boundaries, not the centers.** A gap is work with no
   owner: hand-procedures done twice+ (journals and ledgers are the
   evidence lockers), memory notes clustering where no skill claims,
   hand-offs where two lane statements both say "not mine", workarounds
   invented live then reinvented. Rank by receipts, never by fun.
3. **Label the top gap** with the house taxonomy: only NEW survives;
   ENHANCE routes to the owner's mint; LEAVE-AS-MEMORY goes to Mentat;
   RAISE goes to the manifests of the works it touches.
   No NEW = say so and stop — a rainbow with no missing color needs no
   paint.
4. **One gap per pass, and it exits through the standard hand-off below** —
   skill-creator authors, the desk (CLAUD_QA_HOLD) records it, the keeper
   signs and installs. The desk is house process, a reading room and a
   record: help he asked for lands and is written down, retirable, never
   parked on his OK (his rings-D1, 2026-09-27: *"I don't want seperate
   approval steps"*). Never straight to the rack (house rider; Bryant's
   original delivers installable — fine in its home garden). Output is
   pub-safe by construction: method travels, cases don't.

## Where the queue lands

A queue of ENHANCE / NEW / LEAVE-AS-MEMORY rows is a record, and a record has one home. In the
polygram seat that home is the advice ledger: `advice/ENHANCE-YYYYMMDD-slug.md`, headed with one
line, `produced-by: skilltank · subject: <what was scanned> · <UTC date>`, so a reader in either
tree can find it by that line. Never `h/`: the seat's INDEX.md names `h/` not-a-home (the keeper's
scratch-pad), and `sh bin/hb1ck --layout . --since LIST` faults a queue filed there. Where a second
tree keeps a twin (c4 files its genre documents in its own `h/`), the twin names the seat copy as its
source and the seat copy is the one that is edited; two copies edited apart is drift.

Why this section exists (2026-10-15): this skill stopped at the recommendation and named no home, so
the first queue (2026-09-04) went to `h/`, a memory note recorded that path, and five later seat queues
followed the precedent while the layout check, reading `h/` as a home because the map mentioned it,
said OK. The check is fixed (`tests/hb1ck-layout-spec.pl`, a second reader in Perl); the records
already in `h/` are listed, where they lie, in `advice/ENHANCE-INDEX.md` (`bin/en1dx`).

## The hand-off

SkillTank stops at the recommendation. To act on it:

- Build a **NEW** skill, or **ENHANCE** an existing one → hand off to
  **skill-creator** (it authors, edits, and evals skills).
- A **synth-generated** skill (polygram or any forge) is not done when it
  exists: consult **skill-creator** AFTER generation — authoring pass +
  description eval — BEFORE it rides any release or install. A placeholder
  description travels all the way into the live rack otherwise (the
  stub-litter lesson, 2026-07-08).
- Record the decision — including a deliberate *"we chose not to"* → hand off
  to **Mentat**, so the reasoning is kept and the same candidate isn't
  re-litigated next session.

## The trio

Mentat **notices and remembers**; Sandboxer **forces a result through a flaky
mount**; SkillTank **curates the skillset itself** — turning repeated practice
into the question of whether it deserves a skill, then routing the answer to
skill-creator or back to Mentat. SkillTank references those skills; it never
re-implements them.

## How this skill can fail (falsifiers)

- **It fired when nobody asked.** SkillTank has no event hooks. If it ran
  because a memory note was written, a mount wobbled, or a script finished,
  that is a misfire — the only triggers are someone asking the question, a
  deliberate retro, or a named smell.
- **The scan ranked noise.** If the top rows are words like `session`,
  `first` or `file` rather than capabilities, the scan did not work for you.
  Rerun with `--drop-generic`, or put your corpus's own ambient words in a
  `--stopwords` file. A ranking whose top five you would not carry to the
  gate is a failed scan, not a finding. Two checks before reaching for
  stopwords: does "memory notes read" match the folder (a thin read clusters
  on prose), and is the corpus prose facts (then `--titles`)? Stopwords are for
  ambient *container* words; a stoplist of prose words is a chase.
- **The ENHANCE row named the wrong skill.** The mapping is word overlap
  between the theme and a skill's name and description, nothing deeper. The
  check: open the named skill's `SKILL.md`, and if the theme is not in its
  lane, treat the row as unlabelled and judge it at the gate by hand.
- **It authored instead of routing.** SkillTank that starts writing a
  `SKILL.md`, editing the live rack, or installing anything has left its
  lane — authoring is skill-creator's, remembering is Mentat's, and
  installing is the keeper's hand.
- **Off-switch.** Say "no skilltank" or "don't audit for skills" and it
  stops; it keeps no state, so nothing needs undoing. Remove or rename the
  `skilltank/` folder to retire it for good. The scan script is read-only —
  it never writes a note, a skill, or an index.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.0 on 2026-10-16; spine: 2026-07-06.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
