---
name: context-stack
description: Hold context the way the shop talks about it -- rocks that gain pressure when cited, forced out as boulders and then mountains, a planning fort carried forward and a palace floor ordered by pressure, tensions held suspended until pinned -- with C4's cstk machine and its file layer (a pile to a semaphore index, boulder and mountain files, every link both ways). Use on "context stack", "rocks, boulders, mountains", "what is weighing on this", "pile this", "the fort", "floor the palace", "hold this tension", or before a long session's notes are compacted.
---

# context-stack — rocks, boulders, mountains, and the fort

C4's context stack (`cstk`) is a small machine with one specification and five builds. This skill
carries the reference build and the file layer, dropped from C4's `f/cstk/RECIPE.org` (C4's
`bin/dp1rc` keeps the copies the same as C4's). Its words, as `references/SPEC.md` holds them:

- **rock, boulder, mountain.** Every item starts as a rock. Each citation adds pressure; at 4 a rock
  is forced out as a boulder, at 9 a mountain. The 4 and 9 are the house numbers, invented and said so.
- **the context stack.** Doubly linked, oldest at the head; closure `open`, `ring` or `mobius`.
- **tension.** Opposites held across two or more axes, bound to the work; suspended until `pin`.
- **the fort and the floor.** The fort is what you carry forward (the plan); `floor` orders it by
  pressure and records a generation, never edited: the palace floor of the moment.

## Two scales

**The machine** reads commands on standard input:

```
printf 'push a the floor\ncite a 4\nfort a\nfloor\n' | python3 scripts/cstk.py
```

**The file layer** turns a pile (`ID<TAB>TAGS<TAB>PRESSURE<TAB>LAST-MOVED<TAB>LABEL`) into files:

```
python3 scripts/stacks.py PILE.tsv OUTDIR --dial 4
sh scripts/check-stacks.sh OUTDIR 4                  the second reader: every link both ways
```

The two widths of the palace show up here: `SEMAPHORE.md` is the index, one line per rock (width 2:
where each is, and when it last moved); boulder and mountain files are doubly linked, each pointing
down to its rocks and back up (width 4). `scripts/from-transcript.py` binds a transcript's subjects to
a stack, each citation a cue it carried.

## Linked to the palace and the taxonomy

- A floor's highest-pressure node is a candidate for the palace's floor; write it with
  `pl1nk new` (fortress-palace) at width 4, and cite it there as pressure grows (`pl1nk cite`).
- A boulder's TAG is a word: `tx1lk where TAG` (taxonomy-link) says where its meaning lives, and a
  tag found nowhere is a proper gap to define before the boulder becomes a mountain.
- C4 draws the stack in its served surface (`c4 serve`, the /cstk room).

## Tests

`sh tests.sh`: eight cases in sh over the Python tools (promotion at 4 and 9, fort and floor, tension
and pin, refusals, the file layer's boulder and mountain files, the second reader, the refusal to
overwrite). `sh tests.sh --prove-red` runs each dropped tool's own planted faults from this folder,
so a copy that cannot stand alone shows red.

## How this skill can fail (falsifiers)

- **A copy drifted from C4.** check: `sh bin/dp1rc check f/cstk/RECIPE.org` in C4 reads SAME.
- **A mountain with no boulder under it.** check: `check-stacks.sh OUTDIR DIAL` (S2).
- **The dial picked, then defended.** fails if a dial other than 4 is used without saying why; check:
  the command line in the notes carries `--dial` and the reason.

## Credits

Corwin, 2026-10-11 (the boulder and mountain files, quoted in `stacks.py`) and 2026-10-15 ("Work on
skill each for our context stacking and palace and taxonomy linking").

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-15; spine: 2026-10-11.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
