---
name: skill-metrics
description: >
  Keep a time series of what each shipped thing in the garden is doing — one row per interesting event (ITEM STATE CUR LAST DATE NOTE), one file per item holding its last STATE, and content-keyed archives of the current and previous version of its constituent. Use when benchmarking or checking a skill, plugin, tool or package and the result should be remembered: "log this result", "what state is polygram in", "which skills are RED", "when did skill-sign last change", "benchmark the skills", "record the garden run", "skill metrics", "show the metrics log", "what was the previous version". Ships the implementation (scripts/sk2mt, POSIX sh, plus the house library sh1lib.sh), a SPEC, and a suite with a second reader in Python — nothing to re-implement from notes or host config. Reads model POSIX grep over item names (exact names, -e/-E/-F, -i -v -x -c -l -q). Not a dashboard, not a token counter by itself, not a test runner — it remembers what a runner found.
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-09-22
  c4_born_of: Corwin's 2026-09-22 ask for routine per-skill benchmarking as a skill and an MCP wiring surface
  c4_ships_tool: scripts/sk2mt + scripts/sh1lib.sh + SPEC.md + tests.sh + tests/test_spec.py
---

# skill-metrics

A small store that remembers what happened to each thing the garden ships. It keeps *change*,
not noise: a row is written only when an item's STATE changes or its constituent's bytes change.

## The store, in one look

    metrics/log                    ITEM STATE CUR LAST DATE NOTE   (one event per line)
    metrics/skill-metrics/ITEM     the last STATE, nothing else — `cat` it
    metrics/archive/ITEM/H-NAME    archived constituent, H = first 16 hex of its sha256

- **ITEM** — the name people use for it: `polygram`, `skill-sign`, `c4`, `card-games.el`.
- **STATE** — one word: `GREEN`, `RED`, `LOOK`, `OK`, `FAULT`, `1234B`.
- **CUR / LAST** — the archived current and previous constituent, or `NONE`. The constituent is the
  full deliverable when there is one, else the most user-facing interface (a skill's `SKILL.md`).
- **NOTE** — the rest of the line: measures, counts, the reason.

The whole contract is `SPEC.md`. Read it before changing anything here.

## Doing things

Run from the directory that holds `metrics/`, or pass `-C DIR`, or set `SKILL_METRICS_ROOT`.

    sh scripts/sk2mt init                                  # the only command that creates a store
    sh scripts/sk2mt set skill-sign OK --file skills/skill-sign/SKILL.md --note "lint ok; 4296B"
    sh scripts/sk2mt state skill-sign                      # -> OK
    sh scripts/sk2mt state                                 # every item, "ITEM STATE"
    sh scripts/sk2mt state -e '^gf-'                       # a pattern (BRE; -E for ERE)
    sh scripts/sk2mt last polygram c4                      # a word list: exact names
    sh scripts/sk2mt items --state RED                     # which items are RED right now
    sh scripts/sk2mt say polygram                          # one plain-English sentence
    sh scripts/sk2mt table                                 # latest rows, aligned
    sh scripts/sk2mt log skill-sign                        # full history
    sh scripts/sk2mt check                                 # is the store self-consistent?

Field views are `state cur last date note row`. Patterns match item *names*; to filter by
what an item *is*, add `--state WORD`. Exit codes are grep's: 0 found, 1 none, 2 error —
plus 3 for NOTVISIBLE (no store where you pointed).

**Without the tool.** `cat metrics/skill-metrics/polygram` and `grep -l -x RED metrics/skill-metrics/*`
work on their own. That is deliberate: the store must outlive its scripts.

## Rules this carries

1. **A root you named is never created for you.** Only `init` creates. A typo and a first run look
   the same from inside; refusing is the only honest answer.
2. **Append-only.** No command rewrites or removes a log line. Mistakes are corrected by a new row.
3. **Content, not location.** Archive names carry their hash; `check` re-hashes every one it names.
4. **Word lists are exact names.** GNU `grep -w` is refused on purpose: names carry `-` and `.`, and
   GNU word-matching would find `layered` inside `gf-02-layered-assurance`.
5. **Report in words.** When a human asked, answer with `say`, not with rows.

## Testing it

    sh tests.sh              # shell checks against SPEC.md, then the Python second reader
    sh tests.sh --prove-red  # the harness must go red on a planted wrong expectation
    python3 tests/test_sh1lib.py --prove-red  # sh1lib.sh directly: all three sl_hash branches, every helper

## Where it plugs in

- **The garden kit** (`bin/gd1ck` in AS4CE0001) runs every suite and benchmark and records each
  result through `sk2mt set`. `gd1ck` is the runner; this skill is the memory.
- **MCP.** A server that wants these answers should run `scripts/sk2mt` (read views only) rather
  than re-implement the format — one implementation, many callers. Not wired yet; see the
  plugin README's usage section for the state of that.

## How this skill can fail (falsifiers)

- **A root created for you.** fails if any command but `init` creates a store; check: `sh scripts/sk2mt -C /tmp/none state; echo $?` prints 3, and `/tmp/none` stays empty.
- **History rewritten.** fails if a log line changes or disappears; check: save `metrics/log`, run your commands, then `head -n $(wc -l < SAVED) metrics/log | cmp - SAVED`.
- **An archive does not match its name.** fails if a constituent's sha256 prefix differs from its `H-` name; check: `sh scripts/sk2mt check`.
- **The readers disagree with SPEC.md.** fails if the shell or Python reader departs from the spec; check: `sh tests.sh` (46/46 on 2026-09-27) and `sh tests.sh --prove-red`.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-22.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
