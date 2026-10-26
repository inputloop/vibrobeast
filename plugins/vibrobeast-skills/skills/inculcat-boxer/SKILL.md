---
name: inculcat-boxer
description: >-
  Disposition discipline — what happens to material AFTER it is read or acted on, so nothing
  quietly stays put. Fires when reading anything whose path carries "inbox" or "Inbox" or whose
  filename begins with it; when an action will fall to a human hand and needs placing where they
  will find it; when a pending note is finally clearable; and whenever the words archive, intake,
  drop, pushout, or "still sitting there" come up. It ships NO archiver of its own — it names the
  one that exists (c4/bin/aw2ri: keep / retire / put [--force]) and, since 2026-09-23, that tool
  accepts unsigned received material via `retire`, so the top rung of the ladder is reachable;
  where the tool still refuses, the refusal routes to a run-card rather than a second way to
  archive. Verify before and after any write, on two readers. Not sandboxer (write mechanics), not
  run-card (ceremony authoring), not mentat (note conventions).
metadata:
  stub: true
  cut: "2026-08-17"
  occasion: "read two inbox files and never said they needed moving"
  replant: "toward poly, if poly yields back"
---

# inculcat-boxer — the material has to go somewhere

**Grown, 2026-09-23.** This began as a stub carrying triggers, a reverse-engineered convention, and
one precisely-named gap, under the keeper's instruction *"DO NOT invent a new way to archive: reuse a
tool, or take the time to plan, test, verify, then complete that tool."* On 2026-09-23 he asked for
the archiver to be fixed, and the gap was closed the way the instruction says: the tool that
existed, `c4/bin/aw2ri`, grew a `retire` verb (plan → `--prove-red` → `c4/tests/aw2ri-tests.sh` →
landed). Nothing new was invented. §4 and §5 below say what is now reachable.

## Why it exists — the failure that occasioned it

On 2026-08-17 an agent read two files under `Inbox/` — a six-week-cold Savannah pushout and a
countersign — reported their contents at length, drew conclusions, banked five cards, **and never
once said the files needed moving.** They are still sitting there. Nothing about the reading was
wrong; the *disposition* simply never happened, because nothing fires on it.

**That is the whole shape: reading is loud and disposition is silent, so disposition is what rots.**

## 1 · INBOX — read implies a move is owed

**Trigger:** any path with `inbox` / `Inbox` as a path element, or as the leading word-shaped part of
a filename.

On reading such a file, **say so in the same turn**:

> *Read from an inbox — these N files are owed a move. I cannot archive them (see §4); this wants a
> run-card, or your hand.*

Do not bury it in a summary. Do not defer it to "later." **An inbox that is read but not emptied
reads as processed and is not**, and six weeks is how long that lie survived last time.

## 2 · RUN-CARD — anything falling to a human hand gets placed where the hand is

When an act belongs to a person — a move, a signature, a delete the sandbox cannot do, a lock only
the host can clear — **place it in local context as a run-card**, and defer to any bespoke UI that
has focus and has expressly mentioned you (automation confirmations, log snipping, interactive
surfaces). Do not narrate a manual step and move on; a narrated step is not a placed step.

The `run-card` skill owns *how* a card is written. This skill owns *that one is owed, and when*.

**Testing note:** run-card ceremonies can be exercised by subagents — spawn one, hand it only the
card, and see whether a careful stranger could run it without you in the room. Optional, valuable
when the card is load-bearing.

## 3 · MENTAT — clear the pending thing, carefully, and only then

When a pending note becomes clearable — the action landed, the question got ruled, the thing shipped:

- **Overwrites are normal.** Do not treat an ordinary supersede as an incident; the ledger is
  append-only and the latest row wins. Panic about routine writes is its own noise.
- **Verify before and after** any write, and per `sandboxer`, **on two independent readers** — the
  writer never grades its own homework, and a bash read of a changed path is a suspect reader.
- **Never overwrite what we normally archive and trample.** The trample is deliberate; the archive
  is what makes it safe. If the archive step cannot happen, the trample must not either.
- **Check new or complex action against the standing declarations** — PRINCIPLES, the skills in
  force, the shop's own floor. A disposition that quietly widens a reach is not a disposition.

**Only when all of that holds** should pending actions reachable through the features this skill
harnesses be taken on. The ordering is the safety: verify, check, *then* act.

## 4 · ARCHIVE — reverse-engineered, and the gap named rather than filled

**The ceremony that exists**, `projects/Avalon/tools/archive-markdown.sh IN-DIR FROM-FILE AS-FILE`:

1. **verify the incoming file's signature first** — it refuses outright: *"sign $ai first"*
2. if a target exists, move it to `archive/<name><LABEL>.md`, and its `.asc` with it
3. move the new file and its `.asc` into place
4. `sha256sum` the result, **verify again**
5. tee the whole run to `archive/receipts/<name>.md<LABEL>.log`

**The convention it reveals**, and which anything else must match rather than reinvent:

    archive dir      archive/            receipts in  archive/receipts/
    label            <YYYY-MM-DD>_Archived-by-Corwin
    dated batches    .arc/<name>-<date>/   ·  coarse: arc/<name>-<date>/
    discipline       verify BEFORE, verify AFTER, receipt is a tee'd log
    hand             the label says Archived-by-Corwin. It is his ceremony.

**THE GAP, as it was stated, and how it closed (2026-09-23):**

> `archive-markdown.sh` **requires a signature and refuses unsigned input.** Inbox drops are
> unsigned — the 2026-07-01 Savannah pushout carried 17 files, **zero signed, no checksum file.**
> **So the tool that exists cannot archive the case that occasioned this skill.**

That was a boundary, not a defect: the tool archived *signed instruments*. The family since grew
(`archive-markdown-next.sh` 2026-09-04: unsigned may replace unsigned; `c4/bin/aw2ri` 2026-09-07:
any extension, `keep` a copy) and on 2026-09-23, at the keeper's word, `aw2ri` grew the two verbs
this case needs:

    aw2ri retire FILE...          archive copy + hash + receipt FIRST, then the live file (and its
                                  .asc) is removed. All-or-nothing across FILE...; never a directory.
                                  This is the inbox disposition: unsigned received material, moved.
    aw2ri put [--force] IN AS     his ruling, verbatim: "the correct behavior is to refuse to replace
                                  a signed file with an unsigned file without a --force". --force
                                  lifts only that gate, is receipted as FORCE, retires the signed
                                  live file WITH its signature, and never passes a signature that
                                  FAILS or CANNOT verify.

For material in the AS4CE0001 tree the archive root is that tree's `archive/`
(`ARCHIVE_ROOT=/f/claude/AS4CE/AS4CE0001/archive` on the author's machine; in another garden, point it
at your own tree's `archive/`); the receipt log is `archive/receipts/aw2ri-YYYY-MM.log`
and the retired file is `archive/YYYY-MM/<name>-<YYYY-MM-DD>_Archived-by-<who>.<ext>`. Say who:
`ARCHIVED_BY=Mentat` when Claude made the archive, so the label does not claim his hand.

## 5 · THE LADDER — turn it, card it, or say it, and never nothing

His ruling, 2026-08-17. Evaluate top-down; take the first rung that holds.

    1  TURN IT      the archive tool is reachable AND the input is one it accepts
                    AND **Mentat is present**                        -> run the ceremony
                    (since 2026-09-23 an unsigned inbox drop IS accepted: `aw2ri retire`)
    2  CARD IT      cannot turn (tool absent, or it refuses this input)
                    AND run-card is present                          -> write the run-card
    3  SAY IT       no run-card                                      -> give direction as normal

**There is no fourth rung and no failure state.** Each step down is weaker and still honest — the
same totality that makes an unresolvable token a `word` and an unparseable line a comment, arriving
now at the level of *what to do about it*. "I can't, sorry" is never the answer; the answer degrades.

### Why MENTAT gates the top rung, and it is not decoration

Archiving **moves and supersedes**. The keeper's own precept holds both halves at once: *overwrites
are normal actions* AND *never overwrite what we normally archive and trample.* The trample is
deliberate and safe **only because something remembers it happened.**

**Mentat is that something.** Turn the archive without it and the supersede is a one-way door with
no receipt in memory — the file moves, the record of why does not. So the gate is not "be careful";
it is **the archive's recoverability condition**, and it is why the tool being handy is not
sufficient.

### And the build case

If **run-card is present as well as Mentat**, the missing archiver — the one for unsigned received
material, §4's named gap — **may be built from here**: plan, test, verify, then land it so that a
reset would clearly have used it. Building it needs the card discipline (a careful stranger runs it
without you) and the memory discipline (the trample is remembered). With both, it is a build. With
either missing, it is still only a card or a sentence.

## 6 · AT THE HAND-BACK — the glove asks, the tree answers (2026-10-16)

This skill says *that* a disposition is owed; the powerglove frame (`pg1lv`) asks it at the hand-back,
as one of its default strings:

    Did you leave anything behind for someone else to ask about?   @inculcat-boxer  @run-card
        !debris   a lock or temp file left in .git since the prompt opened      FAULT
        !strays   untracked files written since the prompt opened                ASK (may be another session's)
        !layout   a file written off the project's map (bin/hb1ck --layout)      FAULT
        !home     an ENHANCE queue in a not-home (bin/eh1dx --check)             FAULT

`sh scripts/pg1lv check LEDGER` in powerglove (or `c4/bin/pg1lv`) runs them. An ASK is this skill's
ladder in miniature: turn it (commit, or `aw2ri retire`), card it, or say it. Never nothing.
The night it was wired, the keeper was asked by another session what to do with files a session
had abandoned: seven git temp files and a gc lock (debris), and queues filed in h/ (home). Both
checks fire on those cases in the glove's tests (P20, and eh1dx's own `--prove-red`).

## What is deliberately NOT here

- **No SECOND archiver.** The one that exists grew a verb; that is the whole of what was built.
- **No automatic moves.** Moving someone's received mail on their behalf is a reach, and this skill
  is about naming what is owed, not about quietly clearing it.
- **No decode of `(H->K || XX)->Z`.** The keeper's shape for this. My reading — H (working
  transform space) into K (pinned vocabulary), *or* through XX (the paired check), landing in Z — is
  a guess, and a guessed routing baked into a skill is a manufactured rule. Banked, not assumed.

## How this skill can fail (falsifiers)

- **A read inbox left silent.** fails if a turn reads a path with an `inbox` element and does not say a move is owed; check: the same turn's reply names the files and the owed move.
- **Trample without archive.** fails if a live file was replaced or removed with no archive copy and receipt; check: its name in `archive/receipts/aw2ri-YYYY-MM.log`, with a sha256 equal to the pre-write copy.
- **The label claims his hand.** fails if an archive Claude made is labelled `Archived-by-Corwin`; check: `ls archive/YYYY-MM/ | grep Archived-by-` against who ran it.
- **A second archiver.** fails if a change moves files into `archive/` by any path other than `aw2ri`; check: grep the change for `mv` or `cp` into `archive/`.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.2 on 2026-10-16; spine: 2026-07-01.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
