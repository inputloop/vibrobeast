---
name: session-rotate
description: >-
  Corwin's own per-project rotation for a project that carries a model.md — archive the last
  prompt/response, snapshot model.md, bump z, and (optionally) bake in a new primary directive. Use it
  only on his own words — "rotate", "reseat", "snapshot the model", "roll over the continuity files",
  "hand off" — or when he asks to bump/snapshot a project's model.md or to preserve the current
  prompt/response before overwriting them. Never on your own read that a session is "winding down" or
  "cooling": there is no closing a session in C4 — a session is the assistant's bookkeeping, not the
  user's — and closing is never proposed, it is pended to him. Not a git tag, a CI release, or a
  generic changelog.
gates:
  - tool: c4 bin/ow1ed
    receipt: --receipt [--pressure FILE] [--since DATE]
    verify: --verify TOKEN
    consumed-by: scripts/rotate_session.sh --apply --after TOKEN
---

# Session Rotate — the close-out ritual

Some projects carry a **`model.md`**: a token-mindful "how to resume this project
cold" model with a small rotation header that holds a version (`v2`, `v3`, …).
Alongside it live two continuity files — **`.last-prompt.md`** and
**`last-response.md`** — the last thing asked and the last thing done, so the
next session opens where this one closed.

Left to entropy, these drift: the model goes stale, the continuity files get
silently overwritten and the prior context is lost, and the version stops meaning
anything. This ritual is the fix. Run it as a session winds down so every close
leaves a clean, versioned, resumable snapshot — and so a session cut short still
has a coherent last-known-good to rebuild against. Lineage: born dogfooded on
`skzb/pm`, used to carry `polygram`/AS4CE forward and to bake C4's archivist
directive into its model at v4.

This skill **rotates and snapshots**; it does not save memory ([[mentat-skill]])
or decide whether something is skill-shaped ([[skilltank]]). Because it writes to
mounted folders, it follows the [[sandboxer]] discipline: verify each write
actually landed, never trust the success message alone.

## When this applies

- On a `model.md`-bearing project, the user says, in their own words, any of:
  "call it a session", "let's wrap", "good session", "rotate", "close this out",
  "snapshot the model", "session's cooling".
- A **new** session opens on such a project and the prior `.last-prompt.md` /
  `last-response.md` must be rolled over before they're overwritten.
- The user asks to **bump** or **snapshot** the model, or to **bake a directive**
  into it.

If the project has no `model.md`, this ritual doesn't apply — offer to create one
(or just do the plain memory/PMO close-out) instead.

## The six steps

Run in this order; each depends on the one before.

0. **Say what only this session knows, then ask what is owed.** Write the session's pressure facts to a
   small file, one `key: value` per line (`compactions`, `context-left`, `staged-not-landed`,
   `stale-in-sandbox`, `sandbox-only-by-design`, `calls-timed-out`, `note`, and `said-in`: where the
   session wrote them down). Then run the close check over the tree with a receipt:
   `sh bin/ow1ed --receipt --pressure FILE` in C4 (its sections are LOOPS, PLANS, RECORD, FLOOR, ROTATE,
   ROOT, PRESSURE). Satisfy what it says is owed; its last line is `RECEIPT ow1ed1:...`, a token only a
   run can make. The script will not apply without it: `--apply --after TOKEN` re-runs the check
   (`ow1ed --verify`) and refuses if the token is forged, if the tree moved since, or if anything but the
   rotate is still owed. Where the check cannot run (no C4 on the machine), say so with `--ungated WHY`;
   the reason is written into the archive. It goes first because a rotate that runs before the check has
   already decided what the next session gets to know. With no pressure file it says NOT CHECKED, never a
   pass; it checks that something was written, never that it is true. (Held by the tool since
   2026-10-15, his rule: guard in the tool, so the check cannot be simulated or skipped.)
1. **Snapshot** the current `model.md` → `.models/model-<YYYY-MM-DD>.md`
   (timestamp-suffixed if that name already exists — never clobber a snapshot).
2. **Bump** the version in the model's rotation header — his rule (2026-09-23, door part
   `his-versioning`): *numbers read x.y.z, after GNU Emacs … z counts the atomic changes folded in
   since the save point … name the change, never "the session".* A header still on the old `vN`
   form is bumped as before, with the change named beside it; moving it to x.y.z is his call.
3. **Archive** the prior `.last-prompt.md` and `last-response.md` into
   `.sessions/<YYYY-MM-DD>/` (dated, so nothing is lost).
4. **Write fresh** `.last-prompt.md` and `last-response.md` for this session — the
   real prompt and a faithful summary of what was done, so the next open resumes
   cleanly. (If you don't have them yet, leave the templates the script writes and
   fill them before you finish.)
5. **Optionally bake a directive**: if the session established a standing
   directive for the project, fold it into `model.md` before the bump so the new
   version carries it (this is how `polygram`/C4 reached v4).

## Using the script

`scripts/rotate_session.sh` holds step 0, does steps 1–4 mechanically, and then commits its own
files: in a git repository, a verified apply commits the snapshot, the bump, the archive, GATE.txt and
the fresh continuity files, naming the receipt or the ungated reason, and nothing else you had staged
(his ENHANCE of 2026-10-15: the rotate hooks to version control). Outside git, the snapshot is the kept
copy, and it says so. It **defaults to a
dry-run** that prints the exact plan and touches nothing — matching the ritual of
"show the plan first, then apply". Only `--apply` writes, and every write is
read-back-verified on the real disk.

```sh
# Show the plan (writes nothing). The --project path is an example from the author's machine:
scripts/rotate_session.sh --project /f/claude/projects/skzb/pm

# Actually rotate, with the close check's receipt (step 0):
scripts/rotate_session.sh --project /f/claude/projects/skzb/pm --apply --after ow1ed1:2026-10-15:d/lens/p.txt:<hash>

# Force a version if the header can't be auto-detected:
scripts/rotate_session.sh --project <dir> --set-version 5 --apply
```

Flags: `--project DIR` (dir containing `model.md`; required) · `--after TOKEN` (ow1ed's receipt; an
apply needs it) · `--c4 DIR` (where ow1ed lives, when not found by itself) · `--ungated WHY` (the check
cannot run here; the reason is archived) · `--model FILE`
(override the model filename, default `model.md`) · `--set-version N` (skip
auto-detect) · `--apply` (write; default is dry-run) · `--no-fresh` (archive the
old continuity files but don't drop fresh templates) · `--no-commit` (leave the rotate's files
uncommitted) · `--no-bump` (a model that declares no session-close step, such as C4's: snapshot and
continuity only).

**Version header convention.** The bump looks for a `v<N>` on a header line
containing `version` or `rotate` (case-insensitive) in the first ~20 lines — e.g.
`version: v3` or `<!-- rotate: v3 (2026-06-27) -->`. If your `model.md` has no
such line, add one, or pass `--set-version`.

**The same step 0 rides two other moments.** Before a **hand-back** is written, run the check and quote
its output in the hand-back; a hand-back that claims a clean close with an unquoted check is one nobody
checked. At the top of a **drift** page, run it first: drift asks whether the tree moved away from what we
said, and this asks whether we said it at all, which is cheaper and comes first. (His ask, 2026-10-14:
"I'd really like this check as part of handback and also drift"; ruled in, Q591, 2026-10-14.)

## After the script

The mechanical moves are only half the ritual. Once the files are rotated:

- Make sure `.last-prompt.md` / `last-response.md` actually reflect this session
  (the script only leaves templates if there was nothing to carry).
- If durable facts surfaced, that's a [[mentat-skill]] memory note, not a model
  edit — keep the model a *resume aid*, not a memory store.
- Log the rotation wherever the project's status lives ([[pmo]] if it's a pmo
  project) so the version bump is traceable.
- Confirm the snapshot and bump to the user in one line — what version it is now
  and where the snapshot went.

## Pins at the close — what every declared close must carry

The rotation preserves files; these pins preserve *state*. They apply to any
declared close, model.md project or not.

**1. The gate pin.** Any gate, hold, or keeper-binding condition still open
at close gets written into the dated seal — its name, its state (ARMED /
HELD / PASSED), and who holds the key. Keeper-binding gates live as SIGNED
data on the keeper's surface; a gate that exists only in conversation does
not survive the session boundary (proven by the demonstration-gate saga,
2026-07-04→07).

**2. The dropped-turn rule.** If a close-critical answer may have landed in
a dead or errored turn, resend it or audit the transcript — never retype it
from memory. A retyped answer has no provenance; the transcript is the
event table.

**3. The reframe count-check.** At close, count the session's work-order
prompts against its reframe files (scope pin: work-orders = a file,
continuations = an appended line). A mismatch is a lapse — note it in the
seal, don't paper it.

**4. Honest names for broken closes.** A seal written while close is HELD
says so in its body. A close whose tail breaks (interrupted, dead turn,
unsealed edits) gets the fact IN THE FILENAME when repaired — rename, then
re-sign (the -BROKEN-TAIL-MEMJOY precedent, 2026-07-07). The name is the
first thing the next session reads; let it tell the truth.



## How this skill can fail (falsifiers)

- **The dry run wrote.** fails if a run without `--apply` changes any file; check: `touch /tmp/stamp; sh scripts/rotate_session.sh --project DIR; find DIR -newer /tmp/stamp -type f` lists nothing.
- **A snapshot was clobbered.** fails if a second `--apply` on one day overwrites `.models/model-<date>.md`; check: its sha256 is unchanged after the second run, and a suffixed snapshot appears beside it.
- **Continuity lost.** fails if the prior `.last-prompt.md` or `last-response.md` is missing from `.sessions/<date>/` after `--apply`; check: `cmp` each archived copy against a copy taken before the run.
- **The close was not checked.** fails if a rotate went through without a verified receipt or a written
  reason; check: `.sessions/<date>/GATE.txt` reads "verified" with a token, and `sh <c4>/bin/ow1ed --verify
  TOKEN` against the tree as it stood exits 0 -- or GATE.txt reads "NOT RUN" with the reason. A typed
  last line proves nothing (this falsifier's old check, until 2026-10-15, searched for one, and a model can
  write it); `tests.sh` holds the gate (an invented, stale or over-owing receipt is refused and nothing is
  written) and `tests.sh --prove-red` plants three faults. A hand-back or drift page quotes the RECEIPT line.
- **It fired on a guess.** fails if a rotation ran with no keeper word for it ("rotate", "reseat", "snapshot the model", "hand off") in the prompt that started it; check: quote that prompt line in the hand-back.

## Credits

Bryant Frankford: the static model a project carries (model.md), in Corwin's words of 2026-10-05:
"Tell Claude to create a static model of the problem before starting the task, written to make it
easy for you to resume the the work later if you are interupted." (The attribution ladder, rung 2:
credit.)

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.0 on 2026-10-15; spine: 2026-06-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
