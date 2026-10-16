---
name: pocket-mentat
description: >
  A portable, tool-free note discipline any AI can keep and hand off — SEAM / PIN / SEMAPHORE plus two honesty habits (From: where it came from, Would-change: what would prove it wrong) and came-from:/leads-to: links so notes walk both directions. Use it when the user says "keep notes as we go", "remember this", "take pocket mentat notes", "keep track of what we decide"; when they want to carry their memory to a different assistant ("move my notes to another AI", "export my memory", "hand this to ChatGPT/Gemini/a local model"); when notes need checking for form; and whenever someone needs a memory system with no tools, no accounts, no setup. Ships a paste-in file to hand over verbatim, plus pmnotes.sh to check a notes file for unsourced or unfalsifiable entries. Not mentat-skill (the house's own project-memory discipline), not import-memory (ingests another assistant's export), not seatkeeper (syncs the local seat) — this is the small portable one you can give away.
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-09-04
  c4_source: c4/h/pocket-mentat.md (the paste-in file; duplicated here as an asset by design)
  c4_ships_tool: scripts/pmnotes.sh + fixtures/ + tests.sh
  c4_asset: assets/POCKET-MENTAT.md
---

# Pocket Mentat — the note-keeper you can give away

Most memory systems are a house style: they assume a tree, a tool, a convention someone already
agreed to. Pocket Mentat is the opposite — it is designed to be **handed to a stranger's AI** and
still work. That constraint is what makes it useful, and it is why the user-facing file
(`assets/POCKET-MENTAT.md`) contains no house jargon at all. When you hand it over, hand it over
**verbatim**; translating it into our vocabulary destroys the only property that matters.

## The format

Three parts, two habits:

- **SEAM** — the thing itself: a word, an idea, a fact. The handle you will grab it by.
- **PIN** — what it means in plain words, plus **trigger words** that should make it come back.
- **SEMAPHORE** — the signal that gathers related notes and remembers where each came from.
- **From:** — `you` · `them` · `a source (named)` · `a guess`.
- **Would-change:** — the one thing that would make this note wrong.

One-line shape:

```
SEAM — PIN (triggers: …) — From: … — Would-change: …
```

Links, when obviously useful: **came-from:** the note this grew out of, **leads-to:** where it
points next. Beads on a string, walkable both ways.

## Why the two habits are the whole design

Everything else here is filing. These two are what make a note worth picking up:

- **A note that cannot say where it came from is a guess** — so label it one. That is not a demotion;
  a labelled guess is *usable*, and an unlabelled one quietly becomes a fact.
- **A note nothing could falsify is an opinion** — so label it one. This is the same law the house
  applies to concerns, arriving here in plain language.

Together they are what makes the handoff honest. When someone pastes their notes into a different
assistant, that assistant knows **what to trust and what to re-check** instead of swallowing it
whole. Without the habits you are not exporting memory, you are exporting confident-sounding text.

## Growing gently

Start with **one** notes area. Split into a second only when the first is genuinely hard to scan —
**not on a fixed count**. Useful nudges: you have edited the same spot several times today; you now
scroll to find things; a section has more terms than you can eyeball. These are nudges, and a
human's judgement beats a number every time. When you split, leave a one-line pointer behind
(`moved X → new area`) so nothing is lost.

*House note:* the source model states break-out thresholds as rules (4 edits / 9 sections / 17
terms). They are demoted to nudges here on purpose — a threshold picked-not-validated is exactly
what [[countable-gauge]] exists to catch, and this file is for people who will not tune a number.
The divergence is deliberate and recorded, not an oversight.

## Checking a notes file

```
sh scripts/pmnotes.sh NOTES.md      per-note verdict: OK / GUESS / UNSOURCED / …
sh scripts/pmnotes.sh --format      print the format reminder
sh tests.sh                         fixtures vs expected verdicts
sh tests.sh --prove-red             prove the harness can fail
```

The checker is for **your** side of the desk, not the user's — it exists so that "I have been
keeping good notes" is something you can show rather than assert. It reports:

| verdict | meaning |
|---|---|
| `OK` | seam, meaning, triggers, source and falsifier all present |
| `GUESS` | correctly labelled as a guess — valid, and the label is the point |
| `NO-TRIGGERS` | usable, but it will not come back on its own |
| `UNNAMED-SOURCE` | says "a source" without naming it, which is a citation that cites nothing |
| `UNSOURCED` | no `From:` at all — the note is a guess wearing a fact's clothes |
| `UNFALSIFIABLE` | no `Would-change:` — an opinion filed as a note |

`UNSOURCED` and `UNFALSIFIABLE` are the two that actually matter; the rest are hygiene.

## If things get sensitive

Pocket Mentat never tells anyone to hide things or to stop working — it helps them *keep and find*
what matters. If a note touches something private (a password, someone else's personal details),
**store a pointer, not the secret** ("the wifi password is in the kitchen drawer note") and leave the
secret where it belongs. This holds when you are the one keeping the notes, too.

## Interlocks

- [[mentat-skill]] — the house's own memory discipline. Pocket Mentat is its give-away cousin: same
  instincts, none of the layout.
- [[import-memory]] — the other direction; use that when notes are arriving rather than leaving.
- [[fortress-palace]] — its tables are SEAM/PIN/SEMAPHORE at scale, with `came-from`/`leads-to` as
  the doubly-linked spine.
- [[pencil-your-own]] — `From:` is provenance and `Would-change:` is the falsifier; a note sourced to
  `a guess` is the `PENCIL` disposition, written for someone who has never heard the word.
- [[countable-gauge]] — why the break-out numbers here are nudges rather than thresholds.

## Provenance

The paste-in file was authored at `c4/h/pocket-mentat.md` and is duplicated into `assets/` so this
skill is a self-contained universe — it ships what it needs and does not depend on a path inside
C4 existing on the reader's machine. C4 holds the original, so the duplication is the sanctioned
kind. **Mint status: unblessed**, nothing installed.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
