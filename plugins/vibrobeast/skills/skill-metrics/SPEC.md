# SPEC — the skill-metrics store (version 1, 2026-09-22)

This is the contract. `scripts/sk2mt` is one reader/writer of it; `tests/test_spec.py` is a second
reader written from this page, not from the script. Where they disagree, this page decides and one of
them has a bug.

## S1 — What is measured

An **ITEM** is the single most user-facing name a thing ships as, without version, date or extension
unless the extension is part of how people name it: `polygram`, `skill-sign`, `c4`, `card-games.el`,
`dungeon-mode`. ITEM matches `[A-Za-z0-9][A-Za-z0-9._+-]*`.

A **STATE** is one word: `GREEN`, `RED`, `LOOK`, `OK`, `FAULT`, `1234B`, `98%`. It matches
`[A-Za-z0-9][A-Za-z0-9._:+%-]*`.

The **constituent** of an ITEM is what gets archived: the full deliverable if one was made, else the most
user-facing interface (a skill's `SKILL.md`), descending toward documentation and eventually code comments.

## S2 — The layout, under a ROOT

    ROOT/log                  the event log (S3)
    ROOT/skill-metrics/ITEM   one line: the last STATE of ITEM, and nothing else
    ROOT/archive/ITEM/H-NAME  an archived constituent; H = first 16 lowercase hex of its sha256,
                              NAME = its basename with every char outside [A-Za-z0-9._+-] made `_`

ROOT is chosen by, in order: `-C DIR`; `$SKILL_METRICS_ROOT`; `./metrics`. A ROOT that does not hold
`log` and `skill-metrics/` is **NOTVISIBLE** (exit 3) for every operation except `init`, which is the only
operation that creates one.

## S3 — The log

Line 1 is exactly `ITEM STATE CUR LAST DATE NOTE`. Every later line is one event:
six fields separated by single spaces. Fields 1–5 contain no whitespace. **NOTE** is everything after the
fifth space, never empty (`-` when there is nothing to say), with tabs and newlines folded to spaces and
runs of spaces squeezed to one.

- **CUR** — `NONE`, or `archive/ITEM/H-NAME` naming the current constituent.
- **LAST** — `NONE`, or the archive path of the constituent before CUR.
- **DATE** — UTC, `YYYY-MM-DDTHH:MM:SSZ`.

The log is **append-only**. No operation rewrites or removes a line.

## S4 — Writing (`set ITEM STATE [--file PATH] [--note TEXT] [--date UTC] [--force]`)

Let P be the latest row for ITEM (absent on first sight).

1. With `--file`: archive the file at `archive/ITEM/H-NAME` (identical bytes are stored once). CUR is that
   path. If CUR equals P's CUR, LAST is P's LAST; otherwise LAST is P's CUR (or `NONE`).
2. Without `--file`: CUR and LAST carry over from P (or are both `NONE`).
3. **Interesting-only.** A row is appended when there is no P, or STATE differs from P's, or CUR differs
   from P's — or `--force` is given. Otherwise nothing is appended and the tool says `UNCHANGED`.
4. `skill-metrics/ITEM` is rewritten (atomically) to hold STATE in every case.

## S5 — Reading

A **field view** is one of `state cur last date note row`. `state` reads `skill-metrics/ITEM`; the others
read P. A missing value prints `NONE`.

**Selection** is over the list of item names, with POSIX `grep` meaning:

| form | meaning |
|---|---|
| no names, no patterns | every item |
| `NAME ...` | exact names — `grep -F -x` with those words as the pattern list |
| `-e PAT` (repeatable), `-f FILE` | patterns; `-G` BRE (default), `-E` ERE, `-F` fixed |
| `-i` `-v` `-x` | ignore case, invert, whole-name |
| `-c` `-l` `-q` | count, names only, quiet |
| `--state WORD` | after the above, keep only items whose last STATE is exactly WORD |

Patterns select on **names**, never on states: `-e RED` finds items *named* like RED. To ask
"which items are RED", use `--state RED`. Names and patterns together are a usage error. GNU `-w` is refused on purpose: names carry `-` and `.`,
so GNU word-matching would find `layered` inside `gf-02-layered-assurance`.

**Output.** Exactly one exact NAME selected → the bare value. Otherwise one line per item, `ITEM VALUE`,
in `LC_ALL=C` name order. `row` always prints the bare row.

**Exit** (grep's): 0 selected something · 1 selected nothing · 2 usage or store error · 3 NOTVISIBLE.

Other views over the same selection: `items` (names), `log` (header + every row of the selected items, in
log order), `table` (latest rows, columns aligned), `say` (one plain-English sentence per item).

## S6 — The check

`check` passes (exit 0) only when: every log row is well-formed per S3; every ITEM in the log has a
`skill-metrics/ITEM` whose line equals the STATE of its latest row; every file in `skill-metrics/` is
mentioned by the log; every archive path in any CUR or LAST exists and its bytes hash to the H in its name.

## S7 — Why these choices

- One word per STATE and a rest-of-line NOTE keep the log greppable and readable without a TSV reader.
- The item file lets `cat ROOT/skill-metrics/polygram` or `grep -l RED ROOT/skill-metrics/*` answer with
  no tool at all — the store stays usable if every script here is lost.
- Content-keyed archives: a path is an address, a hash is an identity.
- Interesting-only rows keep the series about change; `--force` exists for a deliberate heartbeat.

---
Copyright (C) 2026 Corwin Brust <corwin@bru.st>
Authored by Mentat (for Corwin).
SPDX-License-Identifier: GPL-3.0-or-later
This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.  It is
distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
