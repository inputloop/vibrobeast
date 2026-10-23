---
name: monocle-stack
description: Grind one block of input (a prompt, a brief, a finding) into a stack of questions -- every question the block raises, each tied to the words that raised it, then the questions those raise, layer by layer until none raises another -- and lay the stack out as a grid of openings and falsifiers. Use when a message asks more than it says, on "how many questions can you drive into the lens grinder", "monocle", "lens stack", "a question that seeks questions", or before answering a long prompt so nothing it asked is dropped.
---

# monocle-stack — a question that seeks questions

A long message asks more than its question marks show. Answer only the marked ones and the rest are
dropped without anyone deciding to drop them. This skill grinds the message into the questions it
raises, stacks the questions those raise, and lays the stack out as a grid you can read, answer and
come back to.

```
sh scripts/mn1sk check STACK      is every question tied to words the block really says?
sh scripts/mn1sk state STACK      how many questions on each layer, and where the stack ran dry
sh scripts/mn1sk grid STACK       the grid, as a markdown table
sh scripts/mn1sk layer STACK 1    one layer as a plain list (countboxer reads it)
sh scripts/mn1sk gaps STACK       any first-layer question left with no answer, partial answer or opening
```

## The four phases

1. **Grind the first lens (the microscope).** Seed: *what does this block ask, said or unsaid?* Write
   one question per line, each with the block's own words that raised it. A question no words raised
   is yours, not the block's; it does not go on the first layer. `check` holds this: every quote must
   be found in the block, so the scorer is never trusted.
2. **Stretch (countboxer).** Hand the first layer to countboxer's G/G/G stretch (`mn1sk layer STACK 1`
   into `cb1ox`). Its rungs say when to ask for one more, when to take one away, and when a list has
   outgrown one reader and belongs with a bigger instrument. Halve by a shape the list really has,
   never because it is half. Questions answered already against questions still open is often that
   shape.
3. **Stack.** Each question kept open is itself a lens: ask it of the block again and write the
   questions it raises one layer down, quoting `« ^ »` when only the parent raised them. Stop when a
   layer raises nothing. Where it ran dry is a finding, and `state` says it.
4. **Grid and open (the LENS).** Under any question, cells: `> opening:`, `> falsifier:`,
   `> answered:`, a LENS view, whatever the work needs. `grid` makes one column per cell name. An
   opening matters as much as a gotcha.

## The stack file

Plain text anyone can write by hand:

```
# block: ../PROMPT-2026-10-15-guard-in-the-repos.md
# seed: what does this message ask, said or unsaid?
? Is it a public repo?  « is it a public repo »
  > answered: no; private on the forge
? What is opportunist test skipping?  « opportunist test skipping »
  ? What makes a skip honest?  « ^ »
    > falsifier: a changed input, and the test still skipped
x How many trailers are there? -- the block says avoid counts
```

`?` a question (two spaces of indent per layer), `>` a cell for the question above, `x` a question
set aside with its reason (kept, never deleted). `<< >>` works wherever `« »` does. Keep the stack
beside what it was ground from: in C4, the prompt's ITEM folder in `q/`.

## Tests

`sh tests.sh` runs 15 cases in Python, a second language reading the sh and awk tool. `sh tests.sh
--prove-red` plants six faults (every quote passes, duplicates pass, a first layer cites a parent, a
set-aside without a reason, gaps that sees none, a grid that drops its cells); each must turn a case
red. The tool reads the same under mawk, gawk and busybox awk.

## The first run

On Corwin's message of 2026-10-15 12:54: 33 questions in three layers, the first layer all from his
words; it ran dry below the third. Of the 21 on the first layer, 12 were answered in the same turn and
3 partly; the rest carry openings. `gaps` was written that day, because one first-layer question had
been left with nothing at all and a reader found it by hand (`c4/q/2026-10-15-guard-in-the-repos/`, `STACK-monocle.md` and `GRID.md`).

## Interlocks

- **countboxer** — the stretch, phase 2. The name `monocle` was one of its candidates (Q594); this is
  where it went.
- **lens** — the grid's views; the ladder lens, microscope, bubble chamber says when to climb.
- **eclipse-pass** — keeps the losers of a deep pass; a stack keeps its set-aside questions.
- **reformat-prompt** — lands the prompt verbatim; a stack grinds the landed copy.
- **cxr** — the grid is a table: `mn1sk grid STACK` → `GRID.tsv` → `tv1cr unfold`, and `ls c/layer/1`,
  `cat c/opening/*` read the stack cold; a first-layer question with no cell shows as `c/answered/%`.
  Not optional once a stack is landed in C4: the atoms sit beside `GRID.md` (first: `q/2026-10-19-cxr-duality/`).

## How this skill can fail (falsifiers)

- **A question the block never raised.** fails if a first-layer question's quote is not in the block;
  check: `mn1sk check`, which refuses it.
- **A dropped question.** fails if the reply to a message answers less than the stack holds and says
  nothing of the rest; check: `mn1sk gaps`, which names any first-layer question with no `answered`,
  `partly` or `opening` cell.
- **A stack that cannot run dry.** fails if a layer only restates its parent; check: read the deepest
  layer cold and name what each question adds.
- **The keeper cannot fail.** check: `sh tests.sh --prove-red` catches six of six.

## Credits

Corwin, 2026-10-15 12:54: "This grids a lens stack from a question iterating a bot of input …
Consider as using microscope to grind a first lens and then a stack of lenses working from a question
that seeks questions. Impetus: How many questions can you drive into the lens grinder from the
insight/framing/prompt/query given?"

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-20; spine: 2026-10-15.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
