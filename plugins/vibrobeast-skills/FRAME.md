# FRAME — the one table that spans, checkpoints, gauges and tone readings share

*Form: a reference, for anyone reading or writing the frame by hand or by tool. Written for the
extension edition (2026-10-10; design §2, cards 14 and 22). The code that writes it is
`polygram/mcp/spans.py` (class `Frame`).*

## What it is

The frame is **one file, one row per event, added to and never rewritten**. Each row is a line of
twelve cells separated by tabs. The file has **no header line**: the column names live one path
over, in a file of the same name inside a `d/` folder beside it. For the default place that is:

- the rows: `~/.mentcached/stats/fr`
- the column names: `~/.mentcached/stats/d/fr` (one line, the twelve names below)

Set `MENTCACHED_FRAME` to put the rows somewhere else. A place you name is never created: the file
must already exist (empty is fine), or no row is written and the answer says why.

## When anything is written

Nothing is written unless the preference **`usage.capture` is `on`**. It is **`off`** by default,
and when the preference cannot be read the answer is still off. Off means no row and no file.
`pref_set usage.capture on` turns it on; `pref_unset usage.capture` turns it back off.

With capture on, this edition writes three kinds of row, and only these:

- **`start`** when a span opens (`span_start`): the token count at the start.
- **`prompt`** when a new prompt is seen: a span mark or stop whose token count *rose* (a reset),
  or a mark the caller flags with `prompt: true`. It holds the count after the prompt.
- **`pref`** when a preference is set or unset: the key and its value. A preference about another
  person (`person.<name>.*` for anyone but the keeper) is a third party's fact and is **never**
  written here. A seatkeeper "no" is mirrored here so it can be counted; only the preference acts.

`start` and `prompt` rows carry a date, the kind, the span, the count and who wrote it, **and
nothing else**: no label, no note, no content. A `gauge` row is written when Claude logs a question put to a person (the `question_log` tool on
mentcached): the question's id, whether one or two were asked together, a likelihood guess, the
confidence that the second could be skipped, and the question's words. These rows **do** carry
words: the question as asked. `checkpoint` and `tone` are reserved for the tools that will write
them (the drift checkpoints and the tone dial).

**What the AI vendor sees** is unchanged by turning capture on: the counts are figures the model
already reports, and the frame stays on this computer.

## The twelve columns, in order

| # | name | what it holds, in words |
|---|---|---|
| 1 | TS | when the row was written, in UTC, like `2026-10-10T08:52:22Z` |
| 2 | KIND | what happened: `start`, `mark`, `stop`, `prompt`, `checkpoint`, `gauge`, `tone` or `pref` |
| 3 | SESSION | which span or session the row belongs to (the span id from `span_start`); blank on a `pref` row |
| 4 | SPAN | reserved for a span inside a session; blank in this edition |
| 5 | LABEL | a short name for what was being done; blank on `start`, `prompt` and `pref` rows |
| 6 | TOKENS_LEFT | the token count the caller reported, a whole number; blank when none was given |
| 7 | BY | who wrote the row: the server's identity (`MENTCACHED_BY`) |
| 8 | KEY | on a `pref` row, the preference's key; on a `gauge` or `tone` row, what was measured |
| 9 | VALUE | on a `pref` row, the value set (`(unset)` when it was taken back); on a gauge, the reading |
| 10 | LIKELIHOOD | on a gauge or tone row, a guessed likelihood (low, medium, high, or a number) |
| 11 | CONFIDENCE | on a gauge or tone row, how sure the guess is, as a fraction (0.17) or a percent (17%), read as the same number; `qg1ck` (the question gauge) fails a two-question frame above 17%, and a frame at exactly 17% passes |
| 12 | NOTE | one line of words; blank on `start`, `prompt` and `pref` rows |

A blank cell is an empty string between two tabs, never a dash or `null`.

**One rule, two numbers.** Claude may ask two questions at once only when it is at least 83% likely
the second will be needed. Seen from the other end, that is the same as being at most 17% sure the
second can be skipped, and that is the figure the CONFIDENCE column holds (0.17). The release notes
say 83%; this page and `qg1ck` say 0.17; they are one rule.

## Reading it

- With awk: `awk -F'\t' '$2=="prompt"' ~/.mentcached/stats/fr` lists the prompt rows.
- **Resets.** The token count goes *up* when a new prompt begins, and the app's own housekeeping
  can raise it too; nothing here can tell which. So a count of prompts "counted from resets" may
  run high. `span_report` and `bin/sp1rp` (the span reader in awk) say "N resets seen" in words
  and leave the legs across a reset out of every total.
- The span ledger (`~/.mentcached/stats/spans.tsv`, with a header line) is a separate file and is
  written whether or not capture is on; the frame is the shared, opt-in one.

## Leaving

You can turn capture off at any time by asking Claude (`pref_unset usage.capture`). What that costs,
said plainly:

- **The rows already written stay.** The frame is added to and never rewritten, so turning capture
  off stops new rows; it does not remove old ones. Nothing expires them: they are kept until you
  remove them.
- **To remove them, delete the file**: `~/.mentcached/stats/fr` (or the file `MENTCACHED_FRAME`
  names) and, if you like, its column-name file `~/.mentcached/stats/d/fr`. Claude can do this for you
  where it can reach your files; otherwise delete it as you would any file. Nothing else holds a
  copy, unless you sent one somewhere yourself.
- **Turning it off writes no row** in this edition (the check happens before the row would be
  written), so the record shows no moment of leaving: it simply stops.
- The span ledger (`spans.tsv`, below) is a separate file and is not affected either way.

## Checked by

- `tests/test_mcp_spans.py`: off writes no row; on writes two counts and nothing else.
- `tests/prefs-declared-spec.rb` (D9): a third party's preference never reaches the frame.
- R18 in `python3 -m polygram.mcp --prove-red`: capture off writes no row.
- `tests/test_mcp_spans.py`: a `question_log` row reads back through `qg1ck`.
- `tests/frame-leak-tests.sh`: the tests never write your real frame.

---
Authored by Mentat (for Corwin; claude-opus-5-5).
Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
SPDX-License-Identifier: CC-BY-SA-4.0
