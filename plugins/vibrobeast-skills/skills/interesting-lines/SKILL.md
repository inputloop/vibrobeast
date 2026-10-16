---
name: interesting-lines
description: Watch a long run (make check, a build, a test suite, any log) with the interesting lines shown and the dull ones folded into one counted line each, so a failure and its traceback are never buried and known noise is a number, not a screenful. Use when output is too long to read, on "fold the log", "show me only what matters", "keep the errors visible", "too many warnings", "what did make check say", or when a person or an agent has to read a run and should not page through it.
---

# interesting-lines — show what matters, fold the rest, and say what was folded

A run of 661 tests wrote 2,650 lines. Eleven tests failed. The failures were in there, between 901
lines of one Python warning repeated and two thousand lines saying `ok`. A person reading that pages
through it; an agent reading it pays for every line. This skill is the filter between the run and
the reader:

```sh
make check 2>&1 | tee full.log | sh scripts/ln1fd           # live: folds as it goes
sh scripts/ln1fd records/2026-10/make-check-last.log         # afterwards, on the kept log
```

On that log: 2,650 lines in, 287 out. All eleven failures are there with their tracebacks, the
closing summary is there, and the last line says what happened to the rest:

```
ln1fd: 2650 lines read, 261 shown, 2389 folded in 25 runs; noise 901 (folded), failrun 11, fail 33, warn 0, mark 2
```

## The three promises

1. **An interesting line is never folded away.** A line a shown class matches is printed, with the
   lines after it that its class asks for (a failure keeps its traceback).
2. **A fold says what it folded.** `... 190 lines folded: <the first> ... <the last>`. A run of one
   line is shown as it is: folding it saves nothing.
3. **The counts add up.** Lines read = shown + folded, and each class is counted, folded or not.

`tee` keeps the whole stream; this filter only decides what is on the screen.

## The table: `assets/interesting.tsv`

```
CLASS<TAB>AFTER<TAB>PATTERN          (an awk ERE; the first matching row wins)
noise    fold  ResourceWarning|Enable tracemalloc
failrun  0     [.][.][.] (FAIL|ERROR)$
fail     12    ^(FAIL|ERROR|BROKEN|MISSED|OWED)[: ]|Traceback|AssertionError|^fatal:|^not ok
warn     1     [Ww]arning|WARN|deprecated
mark     0     ^Ran [0-9]+ tests?|^OK( |$)|^FAILED [(]|^GREEN|^RED|...
```

`AFTER` is how many lines to keep after a match, or `fold`: the class is **counted but folded**. That
third choice is what made the table work on a real run. A plain "warn" class showed all 901
warnings and buried the eleven failures; as `noise ... fold`, they are one number in the last line,
still visible, no longer a screenful. The table is meant to be edited for the program you watch;
copy it and pass `--table`.

## Lines Windows writes

Trailing `\r` is dropped, including the `\r\r\n` a writer that is text mode twice over leaves
(118 lines of that log). A `\r` inside a line keeps what a terminal would show: the part after the
last one, so a progress counter reads as its final value.

## With test-tax

[[test-tax]] gives each test its categories; `bin/tg1rn` draws a bar per category while the run
goes and keeps failures and warnings on screen. This filter does the same for output that has no
test structure at all, and for a log after the fact. The classes here are categories too: the
closing counts are where "the warnings and errors themselves" become something to read (Corwin,
2026-10-15 05:07).

## How this skill can fail (falsifiers)

- **An interesting line was folded.** fails if a line a shown class matches is missing from the
  output; check: `sh tests.sh` holds that property on a synthetic run and on the seat's own make
  check log.
- **The counts lie.** fails if read ≠ shown + folded, or the fold lines' counts do not add up; check:
  the same property tests.
- **The filter cannot fail.** check: `sh scripts/ln1fd --prove-red` plants six faults (no lines after
  a failure, a miscounted fold, an interesting line folded, the last run unsaid, a folded class
  shown, the second row never tried) and must catch all six.
- **The table rots.** fails if a run's real failures stop matching `fail` (a new tool, a new word);
  check: after a red run, grep the full log for the failing test's name and see it in the output.

## Credits

Corwin, 2026-10-14 23:58 and 2026-10-15 04:52: the card-game work on how many lines a run shows and
retracts, "keeping all lines showing after when interesting, such as warning or error", and "another
[skill] that hands the part where we show/hide interesting lines".

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.2: first edition 2026-10-15; spine: 2026-10-14.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
