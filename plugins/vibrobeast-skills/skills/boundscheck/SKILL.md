---
name: boundscheck
description: Prove from a saved transcript that a run did not reach a path it was told to stay out of — the authors' tree behind an experiment seat, a client's folder, SAVANNAH, any named out-of-bounds path. Reads one JSONL transcript, reports every tool call and every read-back that names a denied prefix, with line, tool and field, and exits 1 on a call. Use for "did that run read X", "prove the candidate stayed in its seat", "out-of-bounds audit", "transcript audit", "the scorer must not have seen the answers", or before scoring a run whose fairness depends on what it did not look at.
---

# boundscheck — prove a run stayed in its domain

*Named and built by a builder in Corwin's shop, 2026-09-11, against queue Q7. Unsigned,
uninstalled: delivered as files, installed his way.*

Most fairness rules can be proved from files. One cannot. When a run is told "do not read the
authors' tree", nothing on disk changes if it reads anyway — no mtime moves, no byte differs.
The only witness is the run's own transcript, which is a JSONL file the session owns. This skill
is that witness read by a command instead of by eye.

## When this applies

- Before scoring a candidate run whose result only means something if the run did not see the
  scoring material (the experiment-seat case Q7 named).
- After any run under a standing "stay out of X" instruction — a client folder, a keeper's
  private tree, a mount you were told to read and not write.
- Any time you are about to write "the run did not read X" in a report. If you cannot run this,
  write NOT ATTEMPTED with the command, not a claim.

It does **not** fire for ordinary tidiness questions ("did I touch too many files?") and it is
not a permission system. It reports on a run that already happened.

## The one command

```sh
sh scripts/ot1rd TRANSCRIPT.jsonl --deny /mnt/user-data/uploads/AS4CE0001
```

`scripts/ot1rd` is the copy that ships here, and it is complete on its own. A C4 tree keeps a twin at
`bin/ot1rd`; when the two differ, that is a finding, not a ruling: read the diff and carry the fix across
on purpose, in whichever direction it runs.

Add `--deny` again for a second path, `--allow PATH` for a carve-out inside a denied tree (a
`pub/` subfolder the run was allowed), `--strict` to fail on read-backs too, `--json` for a
machine-readable report. `sh scripts/ot1rd --prove-red` runs the tool's own proof: planted
out-of-bounds records must go red, a real transcript with an unused path must stay green.

Exit 0 clean (or read-backs only) · 1 a denied **call**, `--strict`, or a recount disagreement ·
2 usage. Each hit line carries the transcript line number, the tool name, the field the path sat
in (`input.command`, `input.files[0].devicePath`, `result.content[0].text`), the offset, and the
matched prefix — **never the rest of the string**, so a report can be shared without leaking the
rest of a command.

Two counters, deliberately apart:

- **call** — the run *did* the thing: a path inside a tool's input. This is what fails the run.
- **read-back** — the path appeared in text the run *read*: a tool result, an attachment, a
  frame link. Someone else may have put it there. It prints a warning and exits 0 unless
  `--strict`.

The tally is recounted by a second reader (grep and awk over the report the scanner just wrote)
and printed as AGREE or DISAGREE. A count a program prints about itself is an assertion; a count
two readers agree on is a receipt.

## What it proves, and what it cannot

It proves: **for the spans of the transcript that are still in the file, no logged tool call
named the denied prefix.** That is a real proof and it is narrower than "the run never read X".
It cannot see:

- **A tool the transcript does not log**, or a subagent's own calls — a delegating run's
  transcript carries the subagent's *summary*, not its tool calls. Audit the subagent's own
  transcript, or say NOT ATTEMPTED for that span.
- **A path the run never spelled**: `$HOME`, a glob, `cd` then a relative name, a symlink into
  the denied tree, a path assembled from variables.
- **Anything a context compaction dropped.** The tool prints `WARN compact-boundary` with the
  dropped-token count when it finds one; a clean report over a compacted transcript is a clean
  report over a fragment, and must be quoted that way.
- **What a person typed.** Prompts are not scanned: a path a user named is not a path the run
  read.

A live transcript also grows while you read it. Audit a copy, and quote the copy's line count.

## How this skill can fail (falsifiers)

- **It fired when it should not have.** The run was never under a stay-out instruction, or the
  denied path was never agreed — then the report is noise. Check: the run's brief or the seat's
  `.gate` names the path in so many words. If it does not, do not run this.
- **It said clean and the run did read the tree.** Check: `grep -c '<the path>' TRANSCRIPT` by
  hand. If grep finds the string on a line and ot1rd reported no occurrence, the scanner is
  wrong — not the transcript. Report it; do not fix the report.
- **It said clean over a fragment.** Check: does the report carry `WARN compact-boundary`, or
  does the transcript's first line look like a compact summary? If so, "clean" covers only what
  survived compaction, and the claim must say so.
- **It cried wolf.** Check: run `sh scripts/ot1rd --prove-red`; the minted-token control must find
  zero hits in a real transcript. A hit there means the matcher is matching things that are not
  paths (a backslash escape such as `\n` folded into `/n` is the known way this happens — spell
  the denied path with two or more segments).

**Off-switch.** There is no daemon and no hook: it runs when someone types the command. To stop
it applying, drop the "stay out of X" rule from the run's brief — with no denied path there is
nothing to check, and `ot1rd` refuses to run without an explicit `--deny` (exit 2). To retire it
entirely, delete `scripts/ot1rd` and this file; nothing else depends on them.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-11.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
