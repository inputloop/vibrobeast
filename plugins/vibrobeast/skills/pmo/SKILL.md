---
name: pmo
description: >-
  Drive Corwin's own PMO ("project-management office") tool from inside Cowork — the
  dependency-free supervisor over all projects in the keeper's projects folder (here:
  F:\claude\projects), backed by two TSV
  ledgers (projects.tsv, todos.tsv) and POSIX scripts in bin/. Use this whenever the work
  touches the PMO ledger or cross-project status: "what's next / what's on my plate", "what
  are the risks / top items", "add a todo", "mark #N done", "move #N to DOING", "bump #N to
  priority A", "regenerate the status report / dashboard", or any time you're reading or
  changing project state for these projects even if the user doesn't say the word "pmo".
  Prefer this over hand-editing the ledger TSVs or pmo's generated README.md/index.html, and
  over inventing a new tracker for the projects in that folder — pmo already is that
  tracker. This is Corwin's own local pmo tool specifically, not Jira/Asana/Linear, a code
  TODO comment, a generic repo README, or building a new tracker from scratch.
---

# pmo — the project-management office, inside Cowork

`pmo` is Corwin's tiny, dependency-free supervisor for every project in the keeper's
projects folder (here: `F:\claude\projects`). Two plain-text TSV ledgers hold all state; a handful of POSIX
`sh` programs read and rewrite them and regenerate the human-facing report
(`README.md`) and dashboard (`index.html`). No Python, no packages, no network —
anything with `/bin/sh` + `awk` + `sort` runs it.

This skill is the bridge: it lets you operate that tool faithfully from a Cowork
session instead of guessing at its interface or building a parallel tracker.

## The one rule that protects the data

**The TSV ledgers are the source of truth. `README.md` and `index.html` are
generated artifacts — never hand-edit them.** Change state only through the `bin/`
scripts (or, for bulk edits, by rewriting the TSV and re-running `pmo-report`). Then
regenerate. If you edit the report directly, the next `pmo-report` silently erases
your change, so it's wasted work and a source of drift.

## Locate the workspace first

The scripts find their ledgers two ways: the parent of `bin/`, or the `PMO_DIR`
environment variable. In Cowork the pmo folder is a mounted directory, so the robust
move is to set `PMO_DIR` explicitly to the bash mount path and call the scripts by
full path:

```sh
PMO_DIR=/path/to/mnt/pmo            # the bash view of the pmo folder (here: F:\claude\projects\pmo)
export PMO_DIR
"$PMO_DIR/bin/pmo-list"             # scripts read $PMO_DIR/{todos,projects}.tsv
```

If the pmo folder isn't mounted in the session, ask the user to connect
their pmo folder (on the author's machine: `F:\claude\projects\pmo`) before proceeding — without it there is no ledger to read.

## Command surface

All scripts are in `bin/`. Ledger columns: `todos.tsv` = `id  project  state
priority  tags  text`; `projects.tsv` = `key  name  status  publish  summary  home`
(`home` = where the project lives, msys form `/f/claude/...`; `-` = not known yet). Until the C4
ON turn a project without another home gets a folder under the projects folder
(`/f/claude/projects/<key>` on the author's machine); after it,
homes move to `$C4_ROOT/p/<SLUG>`, SLUG being the SCALAR name that uniquely represents the project
along the garden rings in that build turn. Before the first build SLUG = the PMO key; after it,
SCALAR-to-SCALAR resolution through the C4 registry may map a key to a different SLUG where names
would collide, without leaking that detail to people who do not need it (Corwin, 2026-09-25).
States are `TODO` / `DOING` / `DONE`; priorities are `A` / `B` / `C`; tags are a
comma-separated field (e.g. `risk,top,security`).

| Need | Command |
|---|---|
| List open items (filterable) | `pmo-list [PROJECT] [--state TODO\|DOING\|DONE] [--prio A\|B\|C] [--all]` |
| Cross-project prioritized list | `pmo-prio` (no args) |
| Risks + top items | `pmo-risks` |
| Add an item | `pmo-add PROJECT PRIORITY "text" [--tags a,b] [--state S]` |
| Set an item's state | `pmo-done ID [STATE]` (STATE defaults to `DONE`) |
| Set an item's priority | `pmo-prio ID A\|B\|C` |
| Regenerate report + dashboard | `pmo-report` |
| The roster, as other tools read it | `pmo-roster --keys [--status active,idle]` · `--home KEY` · `--check` (homes + unrostered folders; exit 1 = a named home is gone) |

Notes that matter in practice:

- `pmo-done` is misleadingly named — it sets *any* state. To move an item into
  progress, `pmo-done 38 DOING`; to reopen, `pmo-done 38 TODO`. Default with no
  state is `DONE`.
- `--all` is what reveals completed items; by default `pmo-list` hides `DONE`.
- `pmo-add` warns (but still adds) if `PROJECT` isn't a known key in `projects.tsv`.
- "A random project" (eclipse-pass, and anything like it) means the roster — `--from
  pmo/projects.tsv` or `pmo-roster --keys` — never a listing of the `projects/` folder, which
  also holds non-projects (`extern/`, empty folders). `pmo-report`'s Opportunities section
  names what is ready, stuck, unqueued, and where the roster itself has gaps.
  If you meant an existing project, fix the key rather than spawning a phantom one.
- `pmo-report` writes `README.md` and `index.html` from the current TSVs. Run it
  after any mutation so the human-facing views stay in sync.

## The core loop

Most PMO requests are a small, repeatable cycle. Follow it so the ledger and the
generated views never drift apart:

1. **Read** the relevant slice first — `pmo-list <project>`, `pmo-prio`, or
   `pmo-risks` — so you act on the real current state and the right id.
2. **Mutate** through exactly one script call per change (`pmo-add`, `pmo-done`,
   `pmo-prio ID P`). Echo back the id and the before->after.
3. **Regenerate** with `pmo-report` so `README.md` + `index.html` reflect the change.
4. **Verify the write landed**, then **present** the regenerated `README.md` (and
   `index.html` if asked) with the present-files tool so the user sees current status.

## Guardrails specific to this project

These are hard constraints from the PMO ledger itself and from how Cowork mounts
behave. Honor them — they prevent real data loss.

- **Never run git inside the mounted pmo folder (PMO item #25).** Writes to a Windows
  mount desync; git operations there corrupt state. Commit/push only from an upstream
  clone on the user's own machine, never from the session's mount. If a task seems to
  need git here, stop and hand it back to the user to run in their real shell.
- **Verify mount writes actually landed.** The file tool can report success while the
  bytes don't reach the disk (and bash can return a stale short read of the same
  file). After a mutation, confirm by re-reading the TSV through bash (`grep` the id,
  check the field) rather than trusting a success message. This is the sandboxer
  discipline; reach for that skill if a write looks truncated or desynced.
- **TSV edits go through the atomic path.** The scripts already rewrite via a temp
  file + `mv` (see `pmo-lib.sh`). If you ever edit a TSV directly, mirror that: write
  a temp file and move it into place, never a partial in-place edit.
- **Don't hand-edit `README.md` / `index.html`.** Regenerate them with `pmo-report`.

## pmo-secfix — the guided security remediation

`bin/pmo-secfix [BASE_DIR]` is a separate, interactive remediation tool for the
dprojects security risk (PMO #26). It is deliberately cautious: nothing is hard-
deleted (removed files are quarantined), no git history is rewritten and nothing is
force-pushed automatically, every change asks first defaulting to "leave it", and a
flagged secret is treated as a leak only on explicit confirmation. It supports per-
step and per-item skip/quit. It is meant to be **run by the user in their own shell**,
walking through the manual blocks — not driven headlessly from a Cowork mount. Point
the user to it; don't try to auto-run its rotations or history steps for them.

Also note a standing policy: **history rewrites / force-pushes on GNU packages or
projects hosted at Savannah are not normally allowed and must be coordinated with
Savannah first** — never run one as a fait accompli.

## Examples

**Example 1 — "what should I work on next?"**
Run `pmo-prio` (and `pmo-risks` for the A/risk view), then summarize the top open
items by priority with their ids and projects. Don't invent an ordering — the script
already sorts A->B->C across projects.

**Example 2 — "ccspt's license blocker is handled, mark it done."**
`pmo-list ccspt` to find the id (e.g. 37) -> `pmo-done 37` -> `pmo-report` -> re-read
todos.tsv to confirm `37 ... DONE` -> present the updated `README.md`.

**Example 3 — "start the first real ccspt publish, it's next."**
Find the item (`pmo-list ccspt`, id 38) -> `pmo-done 38 DOING` -> `pmo-report` ->
confirm and present. Don't run git from the mount; if publishing needs a clone +
SSH key, hand that step to the user (cf. #25).

**Example 4 — "add a B-priority todo to polygram: vet the HOLD queue."**
`pmo-add polygram B "Vet HOLD review queue: promote or reject" --tags top` (verify
`polygram` is a real key first) -> `pmo-report` -> present.


## The read view (cxr), and one writer at a time

`PMO_ATOMS=1 sh bin/pmo-report` also keeps the ledgers as folders and files (C4's `tv1cr`, the [[cxr]]
skill: a column is a collection, a row is a registry): `ls projects/c/status/`, `cat todos/r/42/text`, and
`todo-tags/`, the table the comma-joined tags column hides (`cut -f1 todo-tags/c/tag/risk` is every id
tagged risk). Once `todos/` exists every report keeps it current; it is a view, committed with the
ledgers (the repo is a private backup, and nothing is left out of a backup), and the TSVs stay the record. Every program that writes the ledger takes `todos.tsv.lock/` first, so two shells,
or a shell and an agent, no longer repeat ids or lose rows; a lock left by a crash is named, never broken
silently. The round that added both: `HARDEN.md` (and [[harden]]).

## How this skill can fail (falsifiers)

- **The views drifted from the ledger.** fails if `README.md` or `index.html` differs from a fresh `pmo-report`; check: copy both, run `pmo-report`, and `cmp` each copy against the new file.
- **A write did not land.** fails if a mutated id is missing or unchanged in the TSV read back through bash; check: `grep -n "^ID" "$PMO_DIR/todos.tsv"` shows the new field.
- **A phantom project.** fails if an item sits under a key the roster does not know; check: `pmo-roster --check` exits 0, and `cut -f2 "$PMO_DIR/todos.tsv" | sort -u` names only rostered keys.
- **git on the mount.** fails if any `git` command ran against `$PMO_DIR` in the session; check: grep the session's tool calls for `git` with that path.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.0 on 2026-10-20; spine: 2026-09-23.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
