---
name: liner-notes
description: "The page at the end that says who made this, as stories of effort, written at the cut by a tool from what the tree already declares; and the gauge of whether every file's last lines carry the house's credit line (partner, editor, thanks, home). Corwin's side of colophon: it runs last, only through a tool, writes one page into dist/ and nothing anywhere else, names nobody the tree does not name, and proposes no terms. Use at a release or pretest cut, on 'liner notes', 'colophon page', 'who made this release', 'credit line', 'is this fair', 'footer uniformity', or before anything of ours goes out to a public home. NOT a stamper (bin/ft1mt mints footers; Bryant's colophon answers who made a file), NOT a licence chooser (terms come from the keepers)."
---

# liner-notes: the page at the end, and the gauge of the last lines

A colophon in a book is one page of end matter that tells the story of the making. A header on
every file is a different thing, a label sewn into the garment. This skill keeps the book's
sense. Corwin, recorded 2026-10-10, on the stamping kind: *"If it runs, it has to run at the very
end ... it can only work via tool."* And 2026-10-14: *"CREDIT MY PARTNER AND OUR EDITOR THANK
PEOPLE."*

## What it does, in two commands

| command | does | writes |
|---|---|---|
| `sh bin/ln1ot gauge [DIR ...]` | reads the last 12 lines of each prose and code file and counts four shapes: credited, holder-only, other-maker, none; lists the holder-only files (the uniformity he named) | nothing |
| `sh bin/ln1ot page VERSION` | writes `dist/COLOPHON-VERSION.md` from AUTHORS, ACKNOWLEDGEMENTS, MAKERS.org, FOOTERS.org, `releases/VERSION`, NEWS and house.env, with the version read in words by `bin/ve1rs` | one page, only under dist/ |

Both run at the very end: `make dist` runs the gauge and writes the page after the plugin and the
extension are minted, as a report, never a stop. `bin/ln1ot --prove-red` plants four faults and
requires each to be caught; `perl tests/ln1ot-spec.pl` is the second reader of the gauge, written
from the rule in words.

## The rules it keeps

1. **Last, and by tool.** Nothing here runs while the work is being made. The page is regenerated
   at every cut and never edited by hand; if a line is wrong, the source file it names is wrong.
2. **Writes one page, in one place.** `page` refuses any destination outside dist/. The gauge
   writes nothing at all.
3. **Names only what the tree names.** AUTHORS, ACKNOWLEDGEMENTS, MAKERS.org: a person enters the
   page by entering one of those, as they give their own wording. No name comes from a local
   file's incidental contents, a commit's e-mail, or a guess.
4. **Proposes no terms.** The terms section repeats what `conventions/house.env` declares. New
   terms come only from the keepers.
5. **Credit as a story, not an inventory.** The credit line is his own sentence (Terms v2): *"From
   the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the
   works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop."* `bin/ft1mt`
   mints it into every footer from `house.env`; the gauge counts where it is missing.
6. **The one test the page has to pass** is the partner's: *is this fair?* Hand the page to Bryant
   with that question and nothing else.

## Where it sits among its neighbours

- `bin/ft1mt` writes the footers (version sentence, copyright line, credit line). This reads them.
- Bryant's `colophon` (garden edition at `peers/bryant/colophon`, the ladder and the parties file)
  answers *who made this file*, with `plan` that writes nothing and `who --sources`. This answers
  *who made this release*, on one page.
- `bin/lc1ck` faults a code licence on prose; `bin/release --gauge` reads the NEWS lag. The gauge
  here is the credit-line twin of those.
- `conventions/version/SCHEMA.md` is the written schema of every version shape the page quotes.

## By hand, without the script

Read the last twelve lines of each file. If one begins "From the collection", it is credited. If
a Copyright line names someone beside the house holder, it names another maker: check
`conventions/MAKERS.org` names them. If there is a Copyright line and no credit line, list it. Then
write the page: the cut in words, the record in `releases/`, the first NEWS heading, the credit
line, the people in ACKNOWLEDGEMENTS, the skills with another maker, the terms as declared, and the
sentence "is this fair?". Put it under dist/ and nowhere else.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.0: first edition 2026-10-14; spine: 2026-10-14.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
