---
name: verify-say
description: >-
  How to WRITE about a signature or verification claim so the words never outrun what was checked,
  AND how to trust the checker before trusting what it reports. Use whenever a report, dashboard,
  sweep, or reply is about to say a file is "signed", "verified", "clean", or "good" — or whenever
  rendering a status token for signatures, hashes, or attestations. Carries the four-state shelf
  vocabulary (SIGN / DETACH / NOSIG / FURNITURE), a generic absent/present-unverified/verified
  fallback for anything not shelf-shaped, a canary-first rule (verify the verifier before trusting
  its verdict), and print-the-attempted-command over assumption. v2 of verify-say: folds in
  shelf-check's state vocabulary and instrument-panel's canary discipline so one skill carries the
  full wording layer. Not signing-model (what "signed" MEANS), not shelf-check (produces the state,
  this borrows it), not instrument-panel (runs the canary, this borrows the rule), not
  color-theory (contrast math). Owns the WORDS, not the check.
metadata:
  origin: "extracted from rolls guard 3 (2026-08-10 stub) at Corwin's request, 2026-08-17; v2 folds in shelf-check's state vocabulary and instrument-panel's canary rule as an opt-in deeper interlock"
  version: "2.0.1 — description trimmed 17 chars (dropped the redundant palette clause; color-theory boundary already named) to clear the 1024-char description load limit; minions catch 2026-08-19, staged in AS4CE for keeper skill-sign"
---

# verify-say — say only what you checked, and trust the checker first

A signature, hash, or attestation claim is cheap to write and expensive to get wrong. The failure
mode is always the same shape: a file sitting next to a `.asc` gets called "signed" by someone who
never ran `verify`, and the word survives into a report, a dashboard, a summary for the keeper — and
now a false claim has a byline. This skill is the discipline that stops the word from outrunning the
check — and, one layer earlier, that stops a broken checker from handing out false confidence in the
first place.

## Canary first — verify the verifier before you trust its verdict

Before any other state below means anything, confirm the thing doing the checking is itself sound:
reader plus keyring against the pinned key. If that canary fails, nothing downstream gets a verdict —
report **PANEL-FAULT** (or the local equivalent) and refuse every other claim in the same breath. A
BAD reading from one checker is *the checker's* problem until a second, independent reader agrees;
never let a single untrusted reader's "verified" pass through as if it meant something.

*Why this comes first:* every other rule in this skill is about not overstating what a good check
found. This rule is about not trusting a check that was never good to begin with. Skipping it doesn't
make the report wrong in the same way guard-3-style overstatement does — it makes the report wrong
underneath, in a way that *looks* rigorous. That's worse.

## The state vocabulary — shelf-shaped or generic, never invented fresh

**If the artifact lives on a governed shelf** (anything with a `.gate` map, or reachable by
`sign.sh check-shelf`), use that shelf's own four states and don't paraphrase them:

| state | means |
|---|---|
| **SIGN** | clearsigned, must verify — and did |
| **DETACH** | has a verifying `FILE.asc`, checked against it |
| **NOSIG** | intentionally unsigned by policy (not a failure to say so) |
| **FURNITURE** | unsigned by nature — tooling, keys, the `.gate` file itself |

This is shelf-check's vocabulary, not a new one — reuse it verbatim so a reader who knows shelf-check
already knows what your report means.

**If the artifact is not shelf-shaped** — a one-off file, a hash claim, a test result, anything
without a `.gate` — fall back to the generic three states:

1. **Absent.** No signature/check found at all.
2. **Present but unverified.** Evidence exists but was not checked. Write `PRESENT`, write
   `verify NOT ATTEMPTED`.
3. **Verified.** The check actually ran, on the actual content, and passed.

**For a copy, name which side was actually checked.** "Verified" on a copy claim needs both sides in
reach, and often only one is:

- **Copied, verified.** Both sides hashed — source and destination — and the hashes match.
- **Copied, re-read.** The destination was hashed after the write; the source could not be hashed
  (unmounted, read-only fence, no route to it from here) — so the write is confirmed and the read of
  the original is not. This is weaker than "copied, verified"; keep the two phrases apart and never
  round the weaker one up to the stronger.

Never blur SIGN into "verified" without having verified, and never blur NOSIG into "absent" — NOSIG
is a policy statement, not a gap.

## Print the attempt, not the assumption

Whenever a check could not be run — no key on hand, no network, out of scope, ran out of time, or (for
a copy) a source that cannot be hashed from here — the honest artifact is the **attempted command**,
printed with the literal word `NOT ATTEMPTED` beside it, in a form the reader can paste and run
themselves:

```
gpg --verify report.md.asc report.md
# or, for a governed shelf:
sign.sh check-shelf DIR
# or, for a copy whose source can't be reached from here:
source: NOT ATTEMPTED (sha256sum SOURCE)
```

"I could not see this" is a finding. "This is fine" is a claim you didn't earn. A report that hands
the reader the falsifying command is worth more than one that hands them a conclusion.

## Pairing the word with the token

If the claim renders as a colored status chip, pair every token with its **word** — `[ SIGN ]`,
`[ NOSIG ]`, `[ present, unverified ]`, `[ PANEL-FAULT ]` — because a reader who can't receive the
hue still needs the state. `color-theory` owns the contrast math; `rolls` owns the broader
"measured color, quote the ratio" discipline for anything that renders a dashboard.

## Who else touches this and how it divides

- **signing-model** defines what "signed" *means*. This skill is downstream: once you know what
  signing means, this is how you write a sentence about one instance of it without lying.
- **shelf-check** *produces* the SIGN/DETACH/NOSIG/FURNITURE state this skill narrates — this skill
  borrows the vocabulary, it does not reimplement the gate. Always prefer shelf-check's own output
  over re-deriving state by hand.
- **instrument-panel** *runs* the canary and the other gauges — this skill borrows the canary-first
  rule as a writing discipline, it does not replace the panel's read-only measurement.
- **skill-sign** verifies imported skills; same discipline applies when reporting on a skill's
  provenance check.
- **rolls** is the report-kind skill this was extracted from. Guard 3 there now points here for any
  claim about a signature or attestation specifically.

## What this skill is not

It does not check anything, sign anything, or decide whether unsigned is acceptable by policy (the
`.gate` owns that). It is the words — including the word "trust the checker first" — that keep a
verification claim honest once someone sits down to write it down.

## Note on this version

This is the **v2, opt-in-deeper** proposal: it pulls shelf-check's and instrument-panel's vocabulary
directly into this skill's body so a writer never has to context-switch to get the right words. The
narrower **v1** keeps this skill to the generic three-state rule only and *defers* to shelf-check and
instrument-panel by reference rather than quoting their vocabulary inline. Land v1 if you'd rather
keep this skill small and stable while shelf-check/instrument-panel evolve their own state names
independently; land v2 if you want one skill that's the complete answer to "how do I say this" even
if it means updating this skill when those two skills' vocabularies change.

## How this skill can fail (falsifiers)

- **A claim outran the check.** Grep the report for "signed" / "verified" / "clean" / "good" and
  match each hit to a command that actually ran; any hit with no command behind it is the failure
  this skill exists to catch.
- **The canary never ran.** If a report states a SIGN/DETACH/verified state without first confirming
  the reader plus keyring against the pinned key, the canary-first rule was skipped — check for a
  `PANEL-FAULT` line, or the canary's own command, in the report.
- **`NOT ATTEMPTED` silently dropped.** Any check the reader could not run — no key, no network, out
  of scope, an unhashable copy source — should print the literal word `NOT ATTEMPTED` plus the
  paste-able command; its absence where a check plainly didn't happen is a miss.
- **Off-switch:** say "just tell me what you see" or "skip the verify-say wording" when a draft,
  sketch, or internal scratch note isn't making a signature/verification claim to anyone else.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-10.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
