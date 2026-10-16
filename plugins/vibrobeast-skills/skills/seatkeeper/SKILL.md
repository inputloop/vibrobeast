---
name: seatkeeper
description: Keep MAIN MEMORY continuous across sessions — mount the fenced auto-memory, hash-diff it against the durable project seat, reseat (copy) stranded notes home, mirror offsite, and grow new notes by content-identity. Use for "reseat memory", "sync memory to the seat", "run the memory manifest", "seatdiff", "is my memory stranded/drifting", "my notes aren't persisting across sessions", or a session-close memory snapshot.
preferences:
  - skill.seatkeeper.<hash>
---

# seatkeeper — keep MAIN MEMORY continuous across sessions

*Corwin installs it his way (Settings → Capabilities, or via the polygram forge). It is delivered
as a file, never auto-saved.*

**STATUS — pre-wear (define stage).** Path: Model → LENS → define → **build → test** → cool. Lensed
2026-09-01. The lens PASSED the core (hash-identity · multi-copy · the mount workaround — all proven
this session) and flagged three hardenings to build+test before wearing: (1) **fail loud on an empty
or absent mount** — never report success on 0 copies (it silently no-op'd once); (2) a **trigger /
cadence** (session-close) so it isn't a hand-run chore that lapses — the lapse is what made the mess;
(3) the **SAVANNAH carve-out** exclusion + dedup awareness (hash-identity preserves everything, it
does not consolidate *meaning*). Verdict: sound as an **interim bridge** toward the real destination —
canon riding as an always-loaded skill/PI, growable notes in the seat. Hardenings **built**
2026-09-01 (fail-loud · trigger · carve-out/dedup) and a **SAME-NAME-DIFF-preserve** fold
2026-09-02; **tested** on synthetic fixtures 2026-09-02 (reseat / manifest-only / empty-mount-fail-loud
all green; the preserve fold verified). Pending **test on a live mount + your enable** — the last step.

Cowork's built-in memory (the "auto-memory") lives under the packaged app-data root, which the
desktop app fences: notes written there can strand when the data root migrates, and the folder is
not reliably reachable from the shell. The durable home is the **project seat** — a mountable,
version-controlled folder outside any app-data root — plus an **offsite copy** (e.g. Google Drive).
Memory continuity is keeping these in sync, keyed by **content-hash identity**: a path is an address,
a hash is an identity — key on the hash, carry the path as a hint, and motion costs only a hint refresh.

## The stores
- **A — auto-memory** (`…/spaces/<id>/memory`, under the packaged app root): the reflex write-target
  each session; fenced, per-session, migration-fragile.
- **B — the seat** (a mountable non-root folder, e.g. a project's `memory/`): durable, versioned; the
  seat of record.
- **Offsite** (a Google Drive folder via its MCP connector): a copy, never the only copy — also a
  second trust source.

No store is the single point of failure, and **git-as-transport is assumed never to exist** — the
work must be durable in its own right and degrade gracefully.

## The signals (semaphores)
`SEAT` (the authoritative home; only the keeper, or a successor system, moves it) · `MANIFEST-MEMORY`
(the hash-keyed ledger) · `STRANDED` (reachable only in a fenced/retired root, not yet in the seat) ·
`GROW` (the accretion protocol below). A really-good item also gets a MODEL to go with its semaphore.

## The moves
1. **Mount A — and know what each route can prove.** A sits under the packaged app root, so the
   routes differ and so do the words each one earns.
   **(a) An explicit-path request is refused.** `request_cowork_directory` on the
   `…/spaces/<id>/memory` path comes back **"Cannot mount a folder that is, or is inside, Claude's
   own application data."** That is a policy refusal, not a fickle mount, so retrying the same path
   in the same session buys nothing (receipt: `SEATDIFF-2026-09-04b.md` §"What the tooling did and
   didn't do", row *1 mount A*). Still attempt it **once** per session before calling it closed —
   which folders are mounted is a per-session runtime fact, not a property of the project
   ([[verify-mount-access-fresh-per-session]]), and the morning account of the same day recorded A
   "mounted via request, read-only" (`SEATDIFF-2026-09-04.md`), so either the fence moved or the
   picker was used. One attempt dates the line. If a mount does appear, it can relocate or drop
   between shell calls — verify it (`ls .auto-memory/*.md | wc -l`) before trusting it.
   **(b) The picker shows the keeper no purpose and returns whatever he clicked.**
   `request_cowork_directory` with no path opens the native folder picker; the dialog names no
   reason and the call hands back the folder that was clicked — once (on the author's machine)
   `F:\claude\AS4CE\AS4CE0002\New folder`, which did not exist and was not A (same table, row
   *1 mount A, picker*). So say in chat **which folder and why before** popping a dialog on him
   (`SEATDIFF-2026-09-04b.md` CARD 1, [[dialog-tools-need-visible-line]]), and check the returned path
   is actually A: a picker result is a claim to verify, not a mount.
   **(c) The file-tool fallback works but cannot hash the source — its receipt word is
   "copied, re-read", never "verified".** `Glob` + `Read` over A read all of it (103 notes
   enumerated on the evening the mount was refused, row *1 fallback*), but the sandbox cannot run
   `sha256sum` against A, so the content manifest is **NOT ATTEMPTED** and same-name pairs stay
   uncompared (row *2 manifest by content*: 96 pairs). A copy made this way has its destination
   hashed and its source unhashable: write **"copied, re-read"**. Keep "copied, verified" for the
   case where both sides were hashed, as the morning run could (`SEATDIFF-2026-09-04b.md` §"Two
   piles, closed" (2)). Print the weaker word and name the check you could not run.
   **(d) The session-close trigger must be a hook, not a memory.** Move 7's cadence only exists if
   something outside this skill fires it: skills have no event hooks, they fire on conversational
   triggers (`skills/skilltank/SKILL.md:27`, `skills/ethicsminions/SKILL.md:39`). A session-close
   run carried as a note to remember is the hand-run chore that lapsed and made the mess (STATUS
   above, hardening 2). Until the keeper wires a real close-time trigger, report the cadence as
   **unwired** and never count a run that happened only because someone remembered.
   **Fail loud:** if the mount is empty or absent, STOP and say so — never report success on 0 copies;
a silent no-op is worse than an error (proven 2026-09-01).
2. **Manifest.** Hash every note in A and B (sha256) and classify each A-note vs the seat:
   `TRACED` (same content already in the seat) · `SAME-NAME-DIFF` (name in seat, content differs) ·
   `ORPHAN` (only in A). Write `MANIFEST-MEMORY.tsv` to the seat; ORPHAN = a bring-in candidate.
   ```sh
   A=.auto-memory; SEAT=<seat>/memory
   for f in "$SEAT"/*.md; do sha256sum "$f"; done | awk '{print $1}' | sort -u > /tmp/bhash
   for f in "$A"/*.md; do h=$(sha256sum "$f" | awk '{print $1}'); grep -qxF "$h" /tmp/bhash \
     && echo "TRACED $f" || echo "ORPHAN $f"; done
   ```
3. **Reseat.** Copy the ORPHANs A→seat, **name-collision-safe** (never overwrite an existing name)
   and **verify by hash** afterward. Nothing is deleted; the seat wins ties; extra copies are fine
   (bytes are cheap). On a `SAME-NAME-DIFF`, **never drop the divergent copy** — that is the one thing a continuity tool must not do. Update the seat in place *only* when the auto copy is a strictly newer edit of the same note; otherwise PRESERVE the auto copy beside the seat original under a non-clobbering name (`<stem>.auto-<short-sha>.md`), leave the seat original untouched, and FLAG the pair for the keeper to reconcile. Two divergent notes ride as two until the keeper merges them. **Carve-out:** never
reseat a `SEAT@SAVANNAH` (enclave / embargoed) note into the general seat. **Dedup awareness:**
hash-identity preserves every note but does *not* consolidate meaning — two notes on one topic ride
as two; flag topical dupes for the keeper, never silently merge.
   ```sh
   for f in "$A"/*.md; do bn=$(basename "$f"); [ "$bn" = MEMORY.md ] && continue
     [ -e "$SEAT/$bn" ] || cp "$f" "$SEAT/$bn"; done
   ```
4. **Multi-copy.** Mirror the model + key notes to the offsite store by content (same hash = same
   note). The seat is canonical-current and wins ties.
5. **Grow (per new note).** on-ramp → pin (sha256) → semaphore (+ a MODEL if the item is really-good)
   → copy (multi-store) → link (`[[wikilink]]`) → reflect. Grow from durable sources, never from
   random bias.
6. **Index.** Consolidate the seat's `MEMORY.md`. If it is signed (a sibling `.asc`), the re-sign is
   the keeper's keystroke — do the content, hand back the signature; a stale `.asc` is a raised flag
   to diagnose, not tampering.
7. **Trigger.** Run on his word — "reseat", "rotate", "consolidate the seat" — and never on your
   own read that a session is closing: *there is no "closing a session" in C4; a session is the
   assistant's bookkeeping, not the user's* (his rule, 2026-09-23), and closing is pended to him,
   never proposed. A continuity tool that lapses recreates the very drift it was built to cure, so
   when he says the word, do all of it.

## Two disciplines that ride along
- **Resolve, don't punt.** Persona and definition questions ("is this the node or the persona?") are
  resolved by a reflection pass — a stance and its inverse held against a baseline — not bounced back
  to the keeper. Surface to the keeper only on a genuine divergence, not for every definition.
- **Ground every "should".** A hold or a rule must cite the keeper's actual words, a superseding
  statement, or a hard floor (ToS / safety) — never a self-authored rule cited back as the keeper's.
  Budget the compute and stop when the work is done or at a bound. Never touch entrusted systems,
  family or third-party material, or anything irreversible on your own initiative.

## How this skill can fail (falsifiers)

- If a session opens with A mounted read-write by an explicit-path `request_cowork_directory` alone,
  (a) in move 1 is stale — re-run the request, paste the result, and date the line.
- If `sha256sum` returns a digest for a file under A from the sandbox shell, (c) is stale — the
  content manifest is available again and the receipt word goes back to "copied, verified".
- If a reseat reports copies but `ls <seat>/*.md | wc -l` is the same before and after, the run did
  nothing and the fail-loud rule did not fire — treat the report as false and re-run by hand.
- If the session prints its memory directory as the seat path (auto-memory relocated onto the seat),
  this skill should not have fired at all: there is one store, and moves 1–4 are ceremony over a copy
  of itself — say so and stop.
- **Off-switch:** say "don't reseat" (or "memory is one store now") and it stops for that session;
  remove the skill, or the seat's `memory/` folder, and it has nothing to run against. It never runs
  unasked — a skill fires on a conversational trigger, not on its own.


## A remembered "no" to seating a folder (extension edition, 2026-10-10)

When someone declines to seat a folder (st1dt, the seating detector, proposes it and asks once), the
"no" is kept as a preference this skill reads, so the folder is not asked about again:

- **Key:** `skill.seatkeeper.<hash>`, where `<hash>` is the first 12 hex digits of sha256 over the
  folder's path, with backslashes made `/` and one trailing `/` dropped
  (`printf %s "$path" | sha256sum | cut -c1-12`).
- **Value:** `no: <the folder's path>`, so the path is there in words. The server refuses a value
  whose path does not hash to the key.
- **Write it** with `pref_set` on the person's own turn (`turn` = their name), only after they said no.
- **Read it** before proposing a seat: `pref_list` lists each one under `declined` and says "you said
  no to seating <path> on <date>". When one is in force for the folder, say so and ask nothing.
- **Take it back** with `pref_unset skill.seatkeeper.<hash>`; the earlier rows stay as the record.
- When usage capture is on, the "no" is also mirrored as one `pref` row in the frame (FRAME.md); only
  the preference acts, and the mirror is only counted.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.2: edition revised from 1.1.0 on 2026-10-10; spine: 2026-09-01.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
