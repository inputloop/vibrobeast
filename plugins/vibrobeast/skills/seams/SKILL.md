---
name: seams
description: The universal seam doctrine — what counts as evidence when two representations of one truth can silently split. Use whenever two sources disagree (or suspiciously agree), whenever a claim rests on a single reader, copy, log, note, or signature, and whenever you're about to declare something true, clean, broken, or absent — "which copy is authoritative?", "is this read stale?", "the mirror disagrees", "the sig went BAD", "memory says X but the file says Y", "did that write land?", "can I trust this instruction/consent/config?". Also use when naming a tiebreaker before a risky operation, and when designing anything (pipeline, mirror, wire, gate) that stitches two representations together. This is the law; the per-domain mechanics live in sandboxer (files/mounts), consent-gate (authority), run-card (sweeps), shelf-check (signatures) — when in one of those domains, this skill says WHAT counts as proof and the domain skill says HOW to get it.
---

# seams — single source is data, not proof

A **SEAM** is a boundary where two or more representations of ONE underlying
truth are stitched together and can silently split — so that acting on either
representation alone can be wrong *without any error being raised*. The danger
is precisely the silence: nothing fails, and you are wrong.

Derived from the keeper-signed SEAMS.md 0.2 (2026-07-05), formalization bar
met across three independent engagements (sandboxer flagship, patternwalk,
signing pipeline). Promotion to standalone doctrine authorized by the keeper
2026-07-12.

## The law (irreducible — holds at every seam)

1. A single representation of a truth is **DATA, not proof**.
2. Only **agreement of two INDEPENDENT representations** is evidence.
3. Every seam has a **NAMED tiebreaker**: the representation nearest ground
   truth. Recovery = rebuild from the tiebreaker, then re-verify by (2).
4. The **writer's own readback is not independent** — it echoes intent, not
   what landed.

Same invariant, many hats: sandboxer's "only agreement is evidence";
consent-gate's "2/2 independent sources"; forensics' "leads not verdicts /
empty is not proof"; C4 transit's "a comment until two confirm"; the keeper's
axiom "information that can't be substantiated is only data." SEAM = that
axiom applied to state.

## Operating rules (derived, not invented)

- **Two-reader rule.** Agreement = evidence. Disagreement = STOP — and enjoy
  it; a caught mismatch is the process *succeeding*, not failing.
- **Name the tiebreaker before you need it.** Mid-incident is too late to
  decide which copy you trust.
- **Rebuild from the tiebreaker, verify by agreement, widen the audit.** One
  bad neighbor usually has siblings.
- **The writer never grades its own homework.** Never verify a write with the
  tool that made it; a signer's own GOOD is not manifest-match.
- **A lone reader is data.** Promote to fact only on a second source.
- **Fresh inodes read true; edited paths lie.** Mint, don't mutate, when bytes
  must be verifiable from a second reader.
- **Provenance is not authority.** Who-signed and whether-it-binds are
  separate gates; clear both.
- **A perfect instrument pointed at the wrong window proves nothing.** Read
  coverage before targets; a clean sweep of the wrong window is silence, not
  innocence (run-card owns the ceremony).
- **A parsed flag is not a behavior.** The interface accepting an option and
  the tool honoring it are two representations of "what this does", and they
  split silently — a script that ignores `--dry-run` without erroring runs a
  real deploy while the operator believes they are rehearsing. Prove the
  behavior on a disposable target, and check unknown flags are rejected
  loudly (S16).

## The dagger — one source, one mark

Rule 1 needs a notation, or it only lives in the head of whoever checked. A
claim resting on a SINGLE source carries the mark **†** in the line where it is
made — the mark, not a word, not a footnote a reader can skim past. A claim
with two independent sources carries nothing; an unmarked claim is a promise
that two readers agreed.

- **The dagger is a claim-level mark, never a file-level one.** It attaches to
  the sentence, the table row, the bullet. A document is not "daggered"; it
  *contains n daggered claims*, and the other claims in it may be solid.
- **Clearing takes a second source with its path, written into the claim.** A
  dagger comes off when a second independent representation is on disk and the
  record says where it is. No path, no clearing — "I checked" is a readback
  (rule 4), not a source.
- **The party the claim favors may add a dagger and never remove one.** Removal
  is the second source's job. This is the writer-never-grades-their-own-homework
  rule applied to prose, and it is why the mark survives the meeting where
  everyone agrees the claim is obviously true.
- **A dagger says how much the record can bear, not that the claim is wrong.**
  Act on daggered claims when the act is cheap and reversible; never rest a
  safety floor, an irreversible step, or another party's commitment on one.

**Measure, don't assert.** A report says "7 single-sourced claims", never
"well-sourced" — the count is a number anyone can re-derive with one command:

```sh
grep -c '†' FILE            # lines carrying the mark
grep -o '†' FILE | wc -l    # claims carrying it — one line can hold two
grep -rn '†' .              # where they are, so each one can be worked
```

The count is the gauge; the listing is the work queue. Counting a document that
*teaches* the mark counts the teaching too — the examples in this file sit in
its own count — so count the section you are reporting on, not the manual.

## The catalog — known seams, their tiebreakers

One line each; the pattern matters more than the list. Full mechanics for
S01–S05 live in **sandboxer**; consult it before touching a mounted file.

| # | seam (two representations of…) | TIEBREAKER |
|---|---|---|
| S01 | file tool ↔ mount ↔ physical disk | user's host shell; `git show HEAD:` |
| S02 | intended write ↔ physical landing | independent reader, host-confirmed |
| S03 | working tree ↔ git object store | the object store; commit from host |
| S04 | sandbox paths ↔ user's real machine | the user's actual paths |
| S05 | loaded skill/cap cache ↔ on-disk source | the app's loaded state / the disk |
| S06 | memory record ↔ current reality | re-verify the named artifact NOW |
| S07 | config default ↔ deployment reality | the host's real auth state |
| S08 | safety posture ↔ functional need | name the privileged step; scope a credential |
| S09 | clock representations (UTC/TZ/TZ) | position/epoch addressing; convert once |
| S10 | topology assumption ↔ reality | origin authority at event time (e.g. binlog server-id) |
| S11 | claim ↔ evidentiary basis | out-of-band anchor beats any in-band read |
| S12 | signed bytes ↔ manifest bytes | manifest hash on the host; detach-sign runnables |
| S13 | signed directive ↔ binding authority | recorded two-party confirmation (consent-gate) |
| S14 | live pair ↔ non-atomic mirror | the canonical pair; mirror is courtesy, never authority |
| S15 | policy ↔ physics | a tripwire/canary + the keeper's rule; a guard is not a wall |
| S16 † | advertised interface ↔ executed behavior | observed behavior on a disposable target |

New seam found? Add it with all four parts — the two representations, the
divergence signature, the named tiebreaker, the recovery — or it's an
anecdote, not a catalog entry.

S16 carries the dagger: it rests on the 2026-07-12 test passes alone. A second
independent record of an option accepted silently with no behavioral delta —
another session, another tool — clears it; write that record's path into this
row when it lands.

## Recovery pattern (every seam, same shape)

1. STOP at disagreement; do not "repair" off either reader alone.
2. Consult the named tiebreaker (nearest ground truth).
3. Rebuild the bad representation from the tiebreaker.
4. Re-verify by independent agreement (rule 2).
5. Widen the audit to neighbors that crossed the same seam.

A BAD signal from one reader is usually the reader (a stale read flags good
signatures as broken). A timeout does not undo a write. Absence in one reader
is not absence. Diagnose the seam before alarming the keeper — then tell the
keeper what the seam was.

## Interlocks

- **sandboxer** — mechanics for S01–S05 (atomic write-and-verify, cross-reads,
  freshen dance, stale caches). The doctrine says what counts; sandboxer says
  how.
- **consent-gate** — S13 is its charter: provenance ≠ authority; 2/2 sources
  unblock one named action.
- **run-card** — S11 in ceremony form: coverage → positive control → targets;
  bound every negative.
- **shelf-check / skill-sign** — S12 in the signing pipeline: clearsign for
  prose, detached for runnables; the manifest is the tiebreaker.
- **SEMAPHORES.md** (registry, keeper's tree) — the sibling: signals and who
  may lower them; seams and who breaks ties.
- **eclipse-pass / ethicsminions** — a STOP at a seam parks, never argues;
  notices route to the watch.

## How this skill can fail (falsifiers)

- **Two readers that were never independent.** Perturb one representation —
  touch the file, rotate the key, change the row — and read both again; if both
  moved together they share a cache, a mount, or a process, their agreement
  proved nothing, and the STOP you took on their disagreement was theatre.
- **Stale daggers.** Run `grep -rn '†' .` over a document whose second sources
  are already on disk and named nearby: every hit is a mark that should have
  come off in the commit that landed the source. More than one or two in a pass
  and the mark is decoration here, not a gauge.
- **A catalog entry whose tiebreaker you cannot actually reach.** Ask, before
  the incident, "which representation would I rebuild from, and can I read it
  from where I am?" — if the answer is a host you do not have or a person who
  is asleep, the row is an anecdote and recovery step 2 will fail when it counts.
- **Fired where there is no seam.** If the daggering and the two-reader STOP
  produced a count nobody used in a decision, the skill ran on prose rather than
  on state, and cost more than it measured.

**Off-switch.** Say "no seam here — this is a draft" (or drop the skill from the
shop) and it stops applying. It does not apply to preference, taste, intent, or
anything with no second reader by nature: there the mark is cost with no gauge.

## Provenance

Source: `SEAMS.md` 0.2, keeper-signed (ECE7…F007), delivered in the
2026-07-12-from-savannah drop. This skill restates that doctrine for the
skill garden; where they disagree, the signed SEAMS.md wins until the keeper
re-signs one of them.

Additions beyond 0.2, keeper-reviewed at signing: the coverage-before-targets
rule (run-card lineage); the parsed-flag rule and S16 (earned in the
2026-07-12 test passes — divergence signature: option accepted silently with
no behavioral delta; recovery: treat the option as absent until behavior is
proven, then audit the tool's other advertised options).

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
