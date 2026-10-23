---
name: cxr
description: Unfold a TSV so a COLUMN is a COLLECTION (c/) and a ROW is a REGISTRY (r/) of paths you can ls, then fold it back byte for byte; set a cell with two writers; check that the two sides agree. Use when a table is too wide to read, when "who carries this value" is the question, or when a register should be read by path and not by grep.
---

# cxr — a column is a collection, a row is a registry

A TSV is a grid laid over a graph. Every cell (row *k*, column *c*, value *v*) is one fact told two ways:
the row says *k has c = v*; the column says *v is carried by k*. Flat, both readings share one long line a
person cannot read. Unfolded, each gets a path:

```
<stem>/r/<k>/<c>      REGISTRY   a file named for the column, holding the value     (the row's reading)
<stem>/c/<c>/<v>      COLLECTION a file named for the value, listing the keys        (the column's reading)
```

`ls c/status` is the set of states a table uses. `cat c/status/hand-turning` is every key in that state.
`cat r/seam/sense` is one cell. No tool is needed to read any of it; the tool is for writing and checking.
The words are the register table's own: C col4 COLLECTION, R col2 REGISTRY (`m/t`); nothing was coined.

```
sh scripts/tv1cr unfold TABLE.tsv [--key COL[,COL]] [--cols a,b,c] [--out DIR] [--replace]
sh scripts/tv1cr fold DIR [--where COL=VALUE] [--to TABLE.tsv]      the table back, byte for byte
sh scripts/tv1cr set DIR KEY COL VALUE                              both sides written; the old value kept under d/
sh scripts/tv1cr get DIR KEY [COL]           sh scripts/tv1cr who DIR COL VALUE
sh scripts/tv1cr check DIR [--each]          every r atom listed in its c twin, every c line reads back; one
                                             awk pass (11,406 atoms: 0.4 s on local disk, 80 s on the
                                             Windows mount); --each is the first, per-atom way, a second reader
sh scripts/tv1cr stale DIR [TABLE.tsv]       is any atom newer than the last fold or unfold?
sh scripts/tv1cr enc STRING                  the one naming rule, applied to one string
```

## The stem, and its letters

The stem is beside the table, named by one rule (`PATH/NAME/` for `PATH/NAME.tsv`); nothing is searched for.
It holds `r/` and `c/` and a few one-letter files, each a word from `m/t`: `i` IDENTITY (the key column, or
columns, one per line) · `l` LAYOUT (the columns, in order) · `t` TEMPLATE (the header line, verbatim, when
there was one) · `n` NOTE (leading `#` lines) · `o` OTHER (trailing `#` lines) · `a` ARRAY (the keys, in row
order) · `s` SEMAPHORE (the last moment atoms and table were known equal) · `d/<stamp>/` what `--replace` and
`set` trampled, kept whole. None of these is meta-data written into the data: the table's own bytes are the
cells and the header, and they land as cells and a header.

**Naming.** A value becomes a filename by one reversible rule: `[a-z0-9._-]` pass; an upper-case run is
`^run^` (`DEFAULTED` → `^defaulted^`), because a disk that folds case would otherwise collapse `Seam` into
`seam`; any other byte is `%XX`; the empty value is `%`; a name over 200 bytes is cut and ends `%~sha16`.
The name of a member file is an index, never read back as the value — `fold` reads values from `r/`.

**Keys.** One column by default (the first). A composite key (`--key term,receipt`) is its parts joined by a
tab in `a` and by `+` in the `r/` dir name. A table whose rows repeat on the chosen key is refused, naming
the duplicate: on its first real table (`evidence/terms-of-art.tsv`) that refusal was a finding — seven terms
carry two senses — not a fault in the tool.

## Two writers, one gauge

`set` writes `r/K/C` and edits the member lists under `c/C/`; nothing else writes an atom. `fold` writes the
table only. `check` is the falsifier for the whole shape: if the two sides could disagree and nothing said
so, there would be one writer with a cache, not two writers. `check` names every fault by path. A second
reader in a third language (`scripts/tv1cr-roundtrip.pl`, Perl) rebuilds the table from the atoms with its
own encoder and never calls `fold`; it says MATCH, DIFFER at a line, or NOT CHECKED.

## The cost, said out loud

An unfolded table is many small files: 171 rows × 6 columns made **1524 atoms** from a 40 KB table. That is
the price of a value having a path. Unfold a table because someone will *read* it that way, or because a
tool will ask `who` of it; do not unfold a tree of tables because you can. The `--replace` archive under
`d/` doubles it each time. A stem nobody reads is abundance, and abundance is this shop's named failure mode.

## Where it stands in the shop (binding, so the next session cannot not know it)

- **On by default, whenever nothing says otherwise** (his ask, 2026-10-20: apply it "opportunistically
  ... whenever we are not specifically inhibited"). Any session that reads, writes, audits or ships a tree
  with tables in it runs `sh bin/cx1op scan TREE` once and acts on the verdicts: a FINDING (a first
  column that is nearly a key but repeats) is reported as a finding; a CANDIDATE that a person will read
  is unfolded as a read view by the tool that owns the table, regenerated, the TSV staying the record
  (a view is not left out of a private backup repo just because it can be rebuilt); a cell holding a list is a hidden table and gets its own (`id`, `item`) view. What inhibits
  it, and is said each time it does: a `.cxr-hold` line (`GLOB<TAB>REASON` in any folder: the keeper
  works in that TSV directly, or it travels as one file, as `pocket-mentat`'s paste-in must), a signature
  or a pin over the bytes, a test's fixture, a table over 4,913 rows (BULK), a two-column map (PAIRS), a
  view nobody will read (the cost paragraph below). `cx1op why TABLE` gives every reason for one table,
  and `tv1cr unfold` itself refuses a held table, saying the reason, unless told `--held-anyway`.
  Worked examples: `pmo-report` (todos/, projects/, todo-tags/ when `PMO_ATOMS=1`), `hd1rp report
  --atoms` (a HARDEN ledger as HARDEN/ledger/), and the `harden` soft skill, whose rounds run cx1op.

- **A C4 register that a person must read is unfolded beside itself** when it is wider than one screen:
  `evidence/terms-of-art/` is the first; the question bank, `c/names` and `c/skillnames` are the next
  candidates and are *not* done — a session that unfolds one says so in MEMORY.md and leaves the TSV as the
  source of record until the keeper rules otherwise. The TSV stays the file other tools read; `stale`
  says whether the two have parted.
- **A monocle stack's grid is a table**: `mn1sk grid` → `GRID.tsv` → `tv1cr unfold`, so `c/layer/1` and
  `c/opening/` can be listed (`q/2026-10-19-cxr-duality/GRID/` is the first).
- **A character sheet's TSV is a table**: `h/persona/CHARACTER-*.tsv` with `--key table,key`; `ls
  c/treatment` reads the sheet's treatments cold.
- **A skill that writes a TSV** (two-columns, taxonomy-link's words table, the lab ledgers) **may write it as
  atoms and fold on the way out** — the lab ledger `t/tv1cr-lab.tsv` is born that way: `set`, then `fold --to`.
- **The tool homes in C4** (`bin/tv1cr`, spec `t/tv1cr-spec.py`, second reader `t/tv1cr-roundtrip.pl`); this
  skill carries copies that `bin/dp1rc` keeps the same (`f/garden/RECIPE.org`). A copy that drifts is a
  DRIFT row there, not a fork.
- **Not built, and not to be assumed built:** TAG-level routing of a column to the registry's own `c/`
  (Q609), joins between tables sharing a column, the undo walk over `d/` by stamp. Each is an `> opening:`
  cell in the first stack's grid.

## Tests

Three defects got past the spec, the selftest and the Perl reader on 2026-10-20, each found on a real
table by a harden round's reviewer or by the corpus spec, and each now a case and a plant: a `#` line
between the header and the first row was hoisted above the header on fold while `check` held (check
compares r with c, never with the table), so it is refused by name; a key column whose name holds a
space was split on the space, so keys split on commas only; a value of `.` or `..` was named as a folder,
so both encode as `%2E`. `scripts/tv1cr-corpus.rb ROOT` (Ruby, a fourth language) unfolds every real table
under a tree and accepts only SAME or a named refusal; its `--prove-red` plants the hoisting shape.

`sh tests.sh` runs `tests.py` (Python, a second author: 73 cases) against `scripts/tv1cr`; `sh tests.sh
--prove-red` plants sixteen faults in copies of the tool (no hold check, a one-pass check that exits 0
on faults or skips the c side, no duplicate check, case kept, note dropped, one
writer, a check that never faults, stale always fresh, ragged rows pass, nothing kept under d/, a comment
under the header taken as the note, keys split on spaces, a name of . or .. kept as is) and each must
turn a case red. `perl scripts/tv1cr-roundtrip.pl --selftest` holds the Perl leg; `sh scripts/tv1cr
--prove-red` is the tool's own two-fault selftest. `tests.py --lab DIR` appends the run to a lab ledger
through the tool itself.

## LENS (carried, so it survives alone)

```
LENS · cxr, handed back · 2026-10-19
a  my view:              a grid is a graph flattened; give every cell two paths and the reader needs no tool
b  the view I ascribe:   he cannot read long lines; he wants C4's own words, two writers, no meta in data
c  their pull on mine:   composite keys, written s, mktemp scratch: each there because of his disk, not my taste
d  my pull on theirs:    ^run^ on his eyes to keep Seam and seam apart; the letters i l t n o a s d are mine
persona / inverse:       count, then receipt / you built a filesystem inside his and called it reading -- say the file count
principles reframe:      1. a path is read by anyone with ls  2. sh+awk, GPL, spec and reader in other languages
                         3. ships through the garden, needs no C4 tree  4. make's rule and a star schema, in files
notes: written           c4/h/LENS-2026-10-19-cxr.md
```

## How this skill can fail (falsifiers)

- **fold is not the table.** fails if `fold` differs from the source by one byte; check: `tv1cr fold DIR | cmp - TABLE.tsv`, and the Perl reader's MATCH line.
- **One writer.** fails if a `set` leaves `r/` and `c/` disagreeing and `check` says holds; check: `tests.py --prove-red` plants "set writes r only" and "check never faults" and both go red.
- **A name that collides.** fails if two values differ only by case and land in one member file on a case-folding disk; check: unfold `Seam`/`seam`/`SEAM` on the mount and `ls c/` shows three names.
- **A stem that was searched for.** fails if any command finds a stem by a search path; check: every stem is `TABLE` less `.tsv`, or the `--out` the caller named.
- **The cost unsaid.** fails if a hand-back unfolds a table and does not say the atom count; check: the count is in the hand-back.
- **A table it cannot carry, carried wrong.** fails if a real table unfolds and folds to different bytes;
  check: `ruby scripts/tv1cr-corpus.rb TREE` says DIFFER, naming the first differing line.
- **The opportunity unsaid.** fails if a session ships or audits a tree and no one ran `cx1op scan` on
  it; check: the hand-back carries cx1op's counts, or says what inhibited it.
- **Off-switch.** Do not unfold; the TSV is still the file of record. Remove `scripts/tv1cr`; nothing else depends on it.

## Interlocks

- [[harden]] (soft skill): every round runs `cx1op scan` and acts on it; `hd1rp report --atoms` keeps a HARDEN ledger as atoms; its rounds found this tool's three 2026-10-20 defects.
- [[pmo]]: `pmo-report` keeps the ledgers and the tags table as a read view (`PMO_ATOMS=1`), committed with the ledgers: the repo is a private backup.
- [[pocket-mentat]]: the named inhibitor: its paste-in travels as one file to a stranger's AI with no tools, so nothing of it is ever unfolded.
- [[monocle-stack]] — its grid is this skill's third worked example; `mn1sk grid` makes the table this unfolds.
- [[taxonomy-link]] — `evidence/terms-of-art/` is the register's atoms; `ls c/status`, `cat c/term/^lc^` are answers `tx1lk where` can cite by path.
- [[two-columns]] — a note table with `first-seen`/`pressure` columns is a table; `who DIR first-seen PATH` is "what did we learn there".
- [[lens]] — the four views above; the inverse voice's one line is the cost paragraph.
- [[reformat-prompt]] — the pair that raised this: `h/REFORMAT-2026-10-19-cxr-duality.md`; the model: `h/MODEL-2026-10-19-cxr-column-collection-row-registry.md`.
- [[persona-engine]] — the tool took the gate (use 2, first use, during a build) and got WAIT: no persona of its own.

## Credits

Corwin, 2026-10-19: "Consider that each column of a TSV is implicitly a collection of the values in the column
... a row is a registry of some value in each given cell putting it into the collection for each column ...
In C4 terms we may say: COLUMN is a COLLECTION and a ROW is a REGISTRY or ROUTE ... only two direct writers are
required ... the smallest practical value has four written atoms being four zero byte files when all four cells
are empty ... write extra information into other places, don't add meta data to data."
(`c4/q/PROMPT-2026-10-19-cxr-duality.md`, verbatim.) Banked today: Q607–Q611.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 0.2: edition revised from 0.1 on 2026-10-20; spine: 2026-10-19.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
