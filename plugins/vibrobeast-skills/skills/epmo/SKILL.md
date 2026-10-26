---
name: epmo
description: Ask any piece of work who cares, how much, and why, and carry rows between trackers that have never met (pmo, a Tavern task board, a kiosk stack, an EPMO export) onto one capability lens, declaring what each mapping loses. Use on "who cares about this", "how much is this worth", "why does this exist", "place this on the lens", "where does this sit", "bridge Tavern and pmo", "whose runtime is it", "what does change cost us", "is this at the X", "trade recognition for latitude", "EPMO", "ep1mo", or before a roadmap, a review or a hand-back that weighs several trackers' work at once.
---

# epmo — who cares, how much, and why

A tracker keeps rows: an id, a project, a state, a priority, a few words. Each tracker keeps them in its own
schema, at its own moment, and none of them says who the work is for, what it costs, or why it exists. EPMO asks
those three questions of every row, wherever it came from, and answers on one lens. Corwin, 2026-10-19: the
standout tags speak to *"whose frame of reference do I help define?"*, answering *"who cares?"*, *"how much?"*
and *"why?"*.

```
sh scripts/ep1mo lens                     the lens: eight dimensions, each value, and its cardinality
sh scripts/ep1mo place KEY                one project in words: who cares, how much, why, whose runtime, change cost
sh scripts/ep1mo pmo TODOS                pmo rows onto the lens (also: tavern TASKS, stack STACK)
sh scripts/ep1mo roundtrip TODOS          what comes back, and what is declared lost; an undeclared loss exits 1
sh scripts/ep1mo propose tavern TASKS TODOS   the pmo-add lines that would carry Tavern tasks across (prints only)
sh scripts/ep1mo edges                    who may name, lift or depend on what of whom, and until when
sh scripts/ep1mo closure                  what changes if the who line is a ring or a Möbius strip
sh scripts/ep1mo seam                     every social guess or bet, read both ways (felt cost above and below what it is)
sh scripts/ep1mo walk [--all]             the boundary walk: findings that cannot change without revisiting another box
sh scripts/ep1mo assy KEY|--all           the placement as a C4 ASSY line
sh scripts/ep1mo check [--roster FILE]    the data set holds together; every rostered key is placed
```

The tool is homed in C4 (`bin/ep1mo`); its data is C4's registry (`r/epmo`), or this skill's `assets/`, or
whatever `EPMO_DIR` names. Its rules are data, never code: change `SCHEMAS.tsv`, not the script.

## The technique, in eight moves

1. **Ask the three questions, in this order.** *Who cares?* places the work on the line from the organisation
   (plans and proves) through team, pair and person to the public (many people, each caring personally). *How much?* reads the organisation's
   forecast or proscribe, and the person's guess or bet. *Why?* names function, structure or form, and how far
   toward the operating system it is materialised. A row that cannot answer one of them is a finding, not a gap
   to fill by guessing.
2. **Pick the frame by whose runtime it is.** From an edge, two keepers trading rows, EPMO is a **bridge**
   (`epmo-export`, `epmo-ingest`). From the centre, when the runtime is ours, it is a **transformer**
   (`ep1mo`). When the runtime is theirs, it is a **mapping document** (`SCHEMAS.tsv`), which they run by hand
   or in any language.
3. **Never retype; carry, and declare the loss.** A row stays in the tracker that owns it. EPMO carries it
   across with the source line, and every mapping says in words what it drops. A compatibility layer is a
   transformer, so it owes a round trip or a declared loss (`prove-a-promise`). `ep1mo roundtrip` refuses
   an undeclared one.
4. **Read the horizon.** Cost is time, nearly always the time of change, much of it forced by someone else's
   change. Above the line, where no upstream churn would ever cost anything, nothing real sits. Below it, our
   own design constraints bind. At the **X**, building on system libraries, well-trodden tools and standards
   in use, the pressure we feel is about the right amount, and it pushes us toward good change and
   contributions back. Prefer work at the X; name work below it as a choice.
5. **Trade recognition for latitude, as rows.** Neighbouring systems give each other recognition (naming,
   credit, being reminded of each other) in exchange for latitude in how each designs. `EDGES.tsv` holds each
   trade: who may name, lift or depend on what, the condition that lifts a hold, and where the decision is on
   record. A project's reserved words are owned by that project, never by its neighbour.
6. **Read the social seam both ways.** Social is personal for each of us, and any non-solo thing is social.
   The more social a decision seems, the more a bold one feels like cost; cost being time, how it feels and
   what it is part only once it is partly paid. Which way it drifts cannot be known in advance, so read both:
   a guess that feels dearer than it is waits too long, one that feels cheaper eats unseen time; a bet that
   feels dearer is dropped before it pays, one that feels cheaper commits more than meant.
7. **Walk for boundaries.** Upstream first (distributions, RFC-governed formats, packages, libraries and
   frameworks: who will want what we put down, who will burn us with churn), then components (what we have,
   how sure we are of its shape, whether we can take the shape upstream suggests), back and across to forms
   (which tensions to bridge and which to leave, why our forms differ from the obvious ones), and across again
   to containers (what encapsulates our dependencies so our forms fit our structure). A finding that cannot
   change without revisiting another box is a meaningful boundary; the boundaries we are least sure of are
   where a small, reversible probe goes first.
8. **Test the human terms.** *"Any good, accurate resource reminds."* An EPMO output is good if it reminds its
   reader of something they hold, and accurate if what it reminds them of is true. One that reminds nobody
   of anything is not finished.

## Hand-offs (skills by technique, not only by tool)

- **monocle-stack / lens** grind the ask into questions and views; each open question that names work goes to
  `ep1mo place` before it becomes a row.
- **pmo** holds the shop's rows; **Tavern** holds the team's; **ep1mo** carries between them (`propose`).
- **taxonomy-link** says where each lens word means what (all lens words are registered in C4's `g/`).
- **context-stack** owns the closure words (open, ring, mobius) that `ep1mo closure` borrows.
- **countable-gauge / drift** report what the lens shows over time; the lens review is a gauge, never a target.
- **consent-gate** governs any edge whose lift needs a person's yes.

## Tests

`sh tests.sh` runs C4's `t/ep1mo-spec.rb` (Ruby, a language the tool and its data are not written in) against
this copy: 18 cases, and `--prove-red` plants eleven faults, each of which must turn a case red. With no Ruby in
reach it says NOT RUN and exits 77, never 0.

## How this skill can fail (falsifiers)

- **A placement read as a measure.** fails if a count over placements is reported as what matters; check: every
  report says the placements are judged, with their confidence counts (`ep1mo check`).
- **A lossy map read as lossless.** fails if a mapping drops something and says "none"; check: `ep1mo
  roundtrip` exits 1 on any undeclared loss.
- **A row retyped instead of carried.** fails if a pmo row copies a Tavern task without the `tavern:<id>` tag;
  check: `ep1mo propose` lists it again.
- **A placement in the land of impossibility.** fails if anything claims no upstream change will ever cost it;
  check: `ep1mo check` faults horizon `impossible`.

## Credits

Corwin, 2026-10-19: the capability lens (his drawing), EPMO as a transforming component in C4's registry, the
three questions, "who's run-time is it, anyway?", and the horizon. The ladder it extends (heuristic, EPMO, PMO)
is his of 2026-09-07; the edge table is from the 2026-08-29 plan.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-19; spine: 2026-08-29.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
