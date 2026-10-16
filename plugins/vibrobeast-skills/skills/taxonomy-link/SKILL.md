---
name: taxonomy-link
description: Say where each word's meaning lives in C4's taxonomy (m/t, the g/ word registry, terms-of-art, d/dict), fill a palace entry's words table from those places, and read a setting named in plain words by what the words mean -- BOUND, GUESS, TIE (ask, never pick) or NONE, with the whole parse shown and nothing set. Use on "what does this word mean here", "where is X defined", "link the words", "a proper gap", "which setting is that", "turn the tavern on" (or any setting said in words), or "is the taxonomy rich enough".
---

# taxonomy-link — words through the taxonomy

A word means something in C4 because some place says so: the register table `m/t`, the word registry
`g/<word>/<leaf>`, the curated `evidence/terms-of-art.tsv`, or a dictionary page in `d/dict/`. A word
none of them holds is a **proper gap**: not an error, a word to define. `scripts/tx1lk` (homed in C4,
dropped here by C4's `bin/dp1rc`) reads them all and writes nothing but a palace entry's words table.

```
sh scripts/tx1lk where tavern door seam           each word, every place that speaks for it
sh scripts/tx1lk link d/C4/PALACE/i/homed-item.md  fill the entry's "## The words" from those places
sh scripts/tx1lk config "turn the tavern on" --prefs polygram/mcp/prefs.py
sh scripts/tx1lk config "sign manually" --elect s/elect
sh scripts/tx1lk coverage --prefs polygram/mcp/prefs.py
```

A stem resolves everywhere ("doors" finds door). C4's root is `$C4_ROOT`, else the folder above the tool.

## Settings by meaning, not by key

A setting is usually set by its key (`tavern.on on`). Said in words, the phrase is split, each word
looked up, and each setting scored the way polygram's key binder scores names: a word that is part of
the setting's name counts most, a word in its description a little, a word that begins a name part
("llama" for `llamabridge`) between; the value said in the phrase (on, off, auto, manual) counts when
it is itself part of a name (`tavern.on`). Then a verdict:

- **BOUND** — one setting is clearly meant;
- **GUESS** — one leads; say yes before it is set;
- **TIE** — two read the same; ask which, never pick;
- **NONE** — nothing shares a word.

Nothing is set. The last line says what would set it (`pref_set`, or `el1ct NAME MODE`), so the
person decides, with the reading in front of them.

## The coverage gauge, and what it found

`coverage` asks, setting by setting, whether the words of its name resolve anywhere. On 2026-10-15,
for polygram's 21 preferences: **none** did (tavern, steward, tone, softskills, llamabridge and the
rest are proper gaps), and of C4's three ceremonies, one. That is the falsifier for settings by meaning
firing on its first run: the taxonomy is too thin to carry configuration yet, and the gap list is the
order of work — define those words in the registry (`word_register`) before a setting relies on them.

## Linked to the palace and the stack

`link` writes the words table every palace entry carries (fortress-palace; `pl1nk new` leaves it
empty), each sense quoted with its place, never written here. A context stack's boulder tags are words
too (context-stack): `where TAG` before a boulder becomes a mountain.

## A value must fit its setting (2026-10-16)

`config` reads a third vocab column, the setting's default (`--prefs` supplies it), as the KIND of
value the setting takes. A value word in the phrase (on, off, auto ...) fits a switch (+5); a setting
that takes a name or a folder is shown and set aside ("would match, but does not take on"). So "turn
the tavern on" BINDS `tavern.on`; before, it was a GUESS between it and `tavern.as` / `tavern.data`.
The words `tavern` and `c4` now have homes in C4's registry (`g/tavern/f`, `g/c4/f`), so those settings'
names resolve word by word (`coverage`: 4 of 21, from 0).

## Tests

`sh tests-tx1lk.sh` runs C4's `t/tx1lk-spec.pl` (Perl, a second author: 79 cases; `--prove-red` plants
18 faults) against this copy; with no C4 in reach it says NOT RUN and exits 77, never 0.

## How this skill can fail (falsifiers)

- **A sense written here.** fails if a words-table row carries a sense with no place beside it;
  check: every row's last column names m/t, g/, terms-of-art or d/dict, or says a proper gap.
- **A setting picked on a tie.** check: a TIE prints no "To set it" line (spec X-cases).
- **Coverage read as a pass.** fails if settings are configured by meaning while `coverage` says the
  taxonomy is too thin; check: run it first.

## Credits

Corwin, 2026-10-15: "refine the configuration by word meaning parsing backed analysis instead of simple
key/value parameters". The scoring follows polygram's key binder (keys.py), the closest precedent.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-16; spine: 2026-10-15.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
