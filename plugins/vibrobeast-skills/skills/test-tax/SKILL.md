---
name: test-tax
description: Give every test categories that cut across files (windows, second-reader, prove-red, keys…) in one table beside the tests, read the same way for tests in any language, so a run can show a bar per category and a failure names its family. Use when tests are being grouped, tagged or counted; on "test taxonomy", "tag these tests", "which tests touch X", "CATEGORIES.tsv", "a bar per category", "dead tag rows", or when a suite spans several languages and one runner's own tags cannot hold it.
---

# test-tax — the categories a test belongs to

A test already belongs to two things without anyone saying so: the file it lives in and the group
(class, describe-block) inside that file. What it cannot say by itself is what cuts across files:
that these 31 tests all exist because Windows writes `\r\n`, that these 43 hold one reader against a
second written in another language. Those are the categories a person asks about after a red run
("is it only the Windows ones?"), and they are the ones a runner can only show if something tells it.

This skill keeps them in **one table beside the tests**, `t/CATEGORIES.tsv`, read by a tool that does
not care which language the tests are written in.

## The table

```
# pattern<TAB>tag [tag...]   -- the pattern is a shell glob against the WHOLE test name
*Windows*           windows
test_keys.*         keys
*.TheHeals.*        heals windows
*SecondLanguage*    second-reader
```

- **Where:** `t/` is the house default for tests (`.t/` is fine, or `t/` nested deeper); a tree that
  keeps `tests/` is not wrong, and the tool finds the table in any of the three.
- **Names:** `file.Group.name` (Python's unittest), `file.name`, or a bare name (ERT, shell). The file
  is the first dotted part; the group is the first two when there are three.
- **A tag earns its row when it cuts across files.** A tag that only ever matches one file is that
  file, already a category; leave it out.
- **An untagged test is not a fault.** Its file and group still hold it. Most tests are untagged.
- **A dead row is a fault.** A pattern that matches no test is a promise about nothing: usually a
  test renamed out from under it. `tt1ax --check` names each one with its line.

Why one table and not each runner's own tags: pytest has markers, ERT has `:tags`, CTest has
`LABELS`, JUnit has `@Tag`, and each lives inside its own language. A shop whose tests are Python,
Perl, Ruby, awk, shell and Emacs Lisp at once needs the categories outside all of them. Where a
runner's own tags are in use, the table can mirror them; it never replaces them.

## The tool: `scripts/tt1ax`

POSIX sh and awk. It reads test names on standard input, one per line, from any runner:

```sh
python3 bin/tg1rn --ids | cut -f1 | sh scripts/tt1ax --counts      # Python (tg1rn names every test)
emacs -batch -l t/tests.el --eval '(dolist (x (ert-select-tests t t)) (princ (format "%s\n" (ert-test-name x))))' \
  | sh scripts/tt1ax --of                                           # Emacs Lisp
grep -ho '^test_[a-z0-9_]*' t/*.sh | sh scripts/tt1ax --untagged    # shell, by name
```

| mode | says |
|---|---|
| `--of` | each test, a tab, its categories: file, group, then `#tag` for each tag, in table order, once each |
| `--counts` | how many tests each category holds, tags first |
| `--untagged` | the tests no row tags |
| `--dead` | the rows that tag no test (exit 1 if any) |
| `--check` | malformed rows and dead rows, in words (exit 1 if any) |
| `--prove-red` | plants six faults in a copy of the reader and shows each one caught |

## Two readers, one table

`bin/tg1rn` (Python, `fnmatch`) and `tt1ax` (awk, its own glob-to-pattern) read the same table. On
the seat's suite, 679 tests, they give every test the same categories (checked 2026-10-15); a
disagreement means one of them is wrong and neither result is evidence. `tests.py` holds the reader
to its cases and, inside a tree that has `bin/tg1rn`, holds the two readers to each other.

## What the categories are for

The run's view: `bin/tg1rn` draws a bar, a percentage and a mark per category, and a tag's bar
reopens each time one of its tests comes up, so "the Windows ones" is a line on the screen while the
run is still going. What a run keeps on the screen and what it folds away is the other half, and
its own skill: [[interesting-lines]].

## How this skill can fail (falsifiers)

- **The two readers part.** fails if `tg1rn --ids` and `tt1ax --of` disagree on any test of a suite;
  check: `python3 bin/tg1rn --ids > a; cut -f1 a | sh scripts/tt1ax --of > b; cmp a b`.
- **A glob means something else here.** fails if a pattern matches a name the shell's `case` would
  not (or misses one it would); check: `sh scripts/tt1ax --prove-red` (the anchor, `*`, `?`, a literal
  dot, `[...]`).
- **The table rots.** fails if a renamed test leaves a row matching nothing and nobody hears; check:
  `tt1ax --check` in `make check` or the runner's own preamble.
- **Tags that do no work.** fails if a tag's bar has never once changed what a person looked at after
  a red run; check: ask, after the next red run, which bar they read first. A tag nobody reads goes.

## Credits

Corwin, 2026-10-14 23:58, from the card-game work: "dimensionalize" the run — layers that reopen as
tests that carry a category come up, a completion bar, percentage and mark per test and per category,
the group totals right before the failing tests and their own logs. Named a skill at 04:52 the next
morning ("What about test-tax as a skill?").

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-15; spine: 2026-10-14.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
