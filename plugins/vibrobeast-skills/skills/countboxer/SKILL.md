---
name: countboxer
description: Grow a list of answers to one question by Corwin's G/G/G stretch (4, one more; at 9 take away the weakest; at 18 race the halves inverted; resort for bias; a justified bisection; losers kept), with a tool that does the counting so the house numbers stay invisible. Use when ideating toward microscope or LENS, on "G/G/G", "stretch this", "get grist into the microscope", "how many ideas is enough", "race the halves", or when a list keeps growing with no rule for when to stop or what to cut.
---

# countboxer — the G/G/G stretch, counted for you

A list of ideas has two ways to go wrong: it stops too early, because the first few felt like enough, or
it grows without limit, because nothing says when to cut. Corwin's stretch answers both with the house
numbers, GRAIN 4 · GREAT 9 · GRAND 17. The numbers are arbitrary and acknowledged as such ("logically
imaginary": real once used, each with a complementary "not quite"), so the work is to make them
invisible. The tool keeps the count; you keep the judgement.

## The stretch

Ask one question. Answer it, one idea per line.

1. **To 4, then one more.** Keep answering until there are four (GRAIN). Then ask for one more.
2. **At 9, take one away.** At nine (GREAT), ask whether one can go. If one can, take away only the
   weakest — sort first, unless sorting is inhibited — and continue.
3. **Running dry is a stop.** At any rung, if the questions stop producing ideas, stop. The count is
   where you ran out, and that is a finding, not a failure.
4. **Near 17.** If sorting is inhibited (the ideas cannot be ranked against each other), stop at GRAND.
   Otherwise, when one more than GRAND fits (18), take it in, resort, and **race the halves**: read the
   top half top-down against the bottom half bottom-up, so the first meets the last and the pairs move
   inward. Each pair's winner is the idea with the **more unique contribution to the context**, judged
   by one standard for the whole race.
5. **Resort for bias.** Look at what the sort's order did to the contrast. Resort until no sort controls
   better for bias.
6. **Take away half, but not because it is half.** Find a reason that bisects the list (a shape in the
   information), lean into it, and set the losers aside. They are kept, never deleted: they help you pick
   smarter next time.
7. **Past GRAND.** Continue only if no bigger instrument is available. If one is (several readers, a
   bubble chamber over the wire), take the list there instead.

What comes out is grist: the microscope keeps what survives with no trust in the scorer, and the LENS
takes it from there.

## The tool

```
sh scripts/cb1ox state LIST        the count, the rung, and the next step, in words
sh scripts/cb1ox drop LIST N WHY   set idea N aside with its reason (to LIST.losers, kept)
sh scripts/cb1ox race LIST         the halves inverted: pair 1 = first vs last, inward
sh scripts/cb1ox check LIST        the invariants; exit 1 on a fault
```

A LIST is plain text: one idea per line; blank lines and `#` lines are not ideas. Write `# sort:
inhibited` in it when the ideas cannot be ranked. `cb1ox` never ranks an idea, never names a winner and
never calls an idea weak; those are yours. It keeps three promises: an idea set aside is kept with its
reason and the count it left at; only one idea is taken away at GREAT, and none before it; a list whose
sorting is inhibited does not pass GRAND.

**One reading of mine, marked as such.** After one idea goes at 9, the list can climb back to 9. His
words do not say whether to take one away again. Taking one each time could cycle forever, so `cb1ox`
allows one removal at GREAT and flags a second. If he rules otherwise, the check is one line.

## Tests

`sh tests.sh` runs 23 cases written from his procedure in Python, a second language reading the shell
tool. `sh tests.sh --prove-red` plants eight faults in copies of `cb1ox` (moving GREAT, forgetting a
loser, pairing top with top, ignoring inhibition, counting blank lines, passing a second or an early
removal, dropping without a reason); each must turn a case red.

## The name

He offered `countboxer`, `lens-loop` and `monocle`, and asked for one more: `gristmill`, from his own
"get grist into the microscope". It ships as `countboxer` (his first, and kin to `inculcat-boxer`) until he
rules (Q594). The stretch cannot choose its own name: below 18 it never races, and four names never get
there.

## Interlocks

- **lens** — where the grist goes; the four views and the persona pass.
- **eclipse-pass** — keeps the losers of a deep pass; countboxer keeps the losers of a wide one.
- **fortress-palace** — the walk that fills buckets; countboxer is how one bucket's question is stretched.
- **countable-gauge** — measure the write-up the stretch feeds.

## How this skill can fail (falsifiers)

- **It stopped too early.** fails if a stretch ends below 4 while the question was still producing
  ideas; check: the list's last lines were added after the stop was declared, or `cb1ox state` was never
  run before stopping.
- **It cut without a rule.** fails if an idea left the list without a line in `LIST.losers`; check: the
  list's history (or the person's notes) names an idea that neither the list nor the losers file holds.
- **The race was judged by two standards.** fails if pairs were won on different grounds (one on novelty,
  the next on feasibility); check: write the standard once above the race and test every pair against it.
- **The numbers stayed visible.** fails if the people using it are doing the arithmetic themselves; check:
  ask them what rung they are on without `cb1ox` — if they know, the tool did not carry it, and should.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-15; spine: 2026-10-15.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
