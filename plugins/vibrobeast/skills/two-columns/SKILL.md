---
name: two-columns
description: Track where a fact was learned and when it was last used, with two extra columns on any note — first-seen and last-cited. Use when notes outgrow one file, when a claim needs its origin, when deciding what to compact or archive, or when handing notes to another agent. Triggers - "where did we learn this", "when did we last use this", "what should I compact", "split my notes", "doubly linked", "first seen", "last cited", "citation pressure", "what can I archive", "hand my notes to another AI".
---

# Two Columns

Notes usually carry what a thing *is*. Two more columns make them usable by
somebody who was not there:

| column | what it holds | when it is written |
|---|---|---|
| **first-seen** | where this was learned — the earliest record of it you can open | once, when the note is born, and never again |
| **last-cited** | the most recent time it was used, and where | every time it is used |

Everything else in this skill follows from those two, including what to
archive and what to keep.

## Why two, and why these two

Notes rot in two directions and the columns catch one each.

**Backward.** A claim with no origin becomes a fact by sitting still. Nobody
demoted it; it just outlived the memory of who said it. `first-seen` is the
receipt, and it is a *pointer*, not a date — a date tells you a fact is old,
a pointer lets you go and check it.

**Forward.** A note nobody has used in a year and a note used twelve times
last week look identical on disk. `last-cited` separates them, and the gap
between the two columns is the number that makes the rest of this skill
mechanical:

```
pressure = citations since this note was last revised
```

High pressure means the note is load-bearing and stale — you are leaning on
something you have not re-checked. Zero pressure means nothing needed it.
That is the compaction queue, and it is a count rather than a judgement.

**Buoyancy.** Pressure is how far a note floats. High pressure stays at the
surface, where a reader meets it first. Zero pressure sinks toward the floor.
*Sinking is not deletion* — the floor is still the store. A note at the floor
is one you can still open; it is just not in the way.

## The note shape

Start from the [[pocket-mentat]] one-liner — it already carries the origin
and the falsifier, and it needs no translation:

```
SEAM — PIN (triggers: …) — From: … — Would-change: …
```

- **SEAM** — the handle you will grab it by.
- **PIN** — what it means in plain words, plus the trigger words that should
  make it come back.
- **From:** — `you` · `them` · `a source (named)` · `a guess`.
- **Would-change:** — the one thing that would make this note wrong.

Then add the two columns, plus the palace's links when they are obviously
useful:

```
first-seen:  <pointer to the earliest record>
last-cited:  <when, and where>
came-from:   <the note this grew out of>
leads-to:    <where it points next>
```

`came-from` / `leads-to` are the [[fortress-palace]] spine. `first-seen` /
`last-cited` are the two columns. Beads on a string, walkable both ways.

## The rule that makes it survive more than one file

**When a note moves, changes, or is superseded, do not edit it. Write a new
one beside it and point back.**

```
first-seen: <unchanged — it still names the earliest record>
prev:       <the note this replaces>
```

The old note stays. `first-seen` is *carried*, never recomputed — that is the
whole trick, and it is why the chain still works after a hundred revisions:
generation 40 and generation 1 name the same origin, so no reader has to walk
backward to find out where a fact came from. They only walk backward if they
want to see how it got here.

Three consequences worth having on purpose:

1. **Nothing is lost to an edit**, so "we simplified that note last month" is
   never the reason an answer is gone.
2. **Editing somebody else's note becomes impossible rather than forbidden.**
   A second person can only add. You do not need a rule about it.
3. **Citing costs nothing.** A citation appends one line somewhere else; it
   never rewrites the note. If you put `last-cited` *inside* the note you
   would have to rewrite the note every time you used it, and the history
   would fill with revisions that changed one timestamp.

That third one is why the two columns live in two different places, and it is
the most common thing to get wrong.

## Paths, when notes point at files

A path with no scheme is right on one machine and unresolvable everywhere
else, and the note does not say which machine. Give every path a prefix:

```
notes:/seams/foo.md          somewhere inside this notes area
project:/docs/design.md      relative to the project root
laptop:/Users/me/x.md        pinned to a named machine, on purpose
/Users/me/x.md               ← don't. Which machine? The note cannot say.
```

The prefix is not bureaucracy. It is the difference between a note you can
hand to somebody and a note that only works where it was written.

## Doing it by hand, with no tools at all

This is the whole method, and it works in a plain text file:

1. Write the note in the one-line shape above. Fill `From:` and
   `Would-change:` even when they feel obvious — the obvious ones are the
   ones that later turn out to be guesses.
2. Set `first-seen` to the oldest thing you can actually open.
3. Every time you use the note somewhere, add a line to a running list:
   `<when> — <where you used it>`. That list is `last-cited`.
4. To revise: **copy the note, change the copy, add `prev:`, keep
   `first-seen` as it was.** Leave the original alone.
5. To decide what to compact: count citations since each note's last
   revision. Work top-down.

No tooling is required for any of that. The tool below only counts.

## Checking it

```
sh scripts/dl1nk NOTES.md          per-note verdict, and the pressure column
sh scripts/dl1nk --format          print the format reminder
sh tests.sh                        fixtures vs expected verdicts
sh tests.sh --prove-red            prove the harness can fail
```

Verdicts, in [[pocket-mentat]]'s own words plus the two this skill adds:

| verdict | meaning |
|---|---|
| `OK` | seam, meaning, triggers, source, falsifier and both columns present |
| `GUESS` | correctly labelled a guess — valid, and the label is the point |
| `UNSOURCED` | no `From:` — a guess wearing a fact's clothes |
| `UNFALSIFIABLE` | no `Would-change:` — an opinion filed as a note |
| `NO-FIRST-SEEN` | cannot say where it was learned |
| `NO-LAST-CITED` | never used since it was written, or nobody recorded it |
| `BARE-PATH` | a path with no scheme |

`UNSOURCED` and `UNFALSIFIABLE` are the two that matter most; the rest is
hygiene. `NO-LAST-CITED` is *not* a defect on a new note — it is the normal
state of something written and not yet used.

## What this is not for

Do not put the columns on things that have no origin and no uses: a
preference, a draft sentence, a shopping list. There the columns are cost
with no gauge. The test is whether you would ever want to ask "where did this
come from" or "is anyone still using this" — if not, skip it.

**Off-switch.** Say "no columns here — this is a draft" and it stops applying.

## Handing this to somebody else

`assets/TWO-COLUMNS.md` is the paste-in version: the same method with no
house vocabulary, no links to other skills, and nothing that assumes a
particular tree. Hand it over **verbatim**. Translating it into local
vocabulary destroys the only property that matters, which is that it works in
a stranger's assistant with no context at all.

## Interlocks

- [[pocket-mentat]] — the note shape this extends; the `came-from`/`leads-to`
  links are already there, and this adds the two columns.
- [[fortress-palace]] — its tables are these notes at scale.
- [[seams]] — `first-seen` is what makes a single source *visibly* single; a
  claim with one source carries the dagger `†` until a second one is on disk.
- [[countable-gauge]] — pressure is a gauge, so it prints a number and not a
  verdict. What the number means is your judgement, not the tool's.
- [[import-memory]] — the other direction, when notes are arriving.
- [[cxr]] — a notes table with `first-seen` and `pressure` columns is a table: unfolded, `who DIR first-seen PATH`
  is "everything we learned there", and `ls c/pressure` is the gauge's range without a query. Reach for it when
  the table outgrows one screen; say the atom count when you do.

## Provenance

The two columns are Corwin's, stated 2026-09-14: *"we must always implement in
terms of keeping close track of where we learned something and the most
[recent] citation of each fact we write/cite."* The note shape and the
`came-from`/`leads-to` links are [[pocket-mentat]]'s, unchanged. The
buoyancy reading is his own index card beside the 2026-09-14 drawing —
SURFACE / "buoyancy" over DEPTH / FLOOR, periscope up, DIVE down.

The archive-only mechanics are implemented in `polygram/mcp/store.py` and
served over MCP by `mentcached`; this skill is the version that works with
none of that installed. **Mint status: unblessed**, nothing installed.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: edition revised from 1.1.0 on 2026-10-20; spine: 2026-09-14.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
