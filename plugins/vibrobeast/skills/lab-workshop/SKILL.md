---
name: lab-workshop
description: >
  LAB or WORKSHOP: how much checking and measuring a task gets, read from the working mode (mode_get, or
  sh bin/md1rd in a shell). WORKSHOP (the default) trusts the calibrations: use and confirm against the
  baselines, say only what falls outside range. LAB checks and measures more, treats every run as a chance
  to calibrate, proves it first, and writes the research before a build loop when two or more options
  differ in energy cost, accessibility, or fitness for the user or their teams and orgs. Use at the start of
  any long or costly task (a build, a test run, a release, a migration), on "lab mode", "workshop mode",
  "how careful should this be", "measure this run", "just confirm it", "mode_get", "mode_set", or when
  a run's output is long and you must choose what to show.
metadata:
  c4_status: mint-unblessed
  c4_minted: 2026-10-23
  c4_source: Corwin, 2026-10-23 11:04 CDT; AS4CE0001/advice/MODE-2026-10-23/MODEL.md
  c4_ships_tool: polygram/mcp/mode.py (mode_get, mode_set, mode_clear) and bin/md1rd
---

# LAB or WORKSHOP

His words (2026-10-23): a LAB is "more checks, more measurement, each run being a chance to learn from to
improve calibration (at the cost of some changes to test the existing calibrations because of the cost of
measuring so agressively)"; in a WORKSHOP "we can reverse this, assuming that our calibration is valid and
taking measurement in context feedback as tuning the intended baseline performance expectations".

## Read the mode first

Call `mode_get` (or run `sh bin/md1rd --why` in a shell) before a long or costly task. It says the mode
and where it came from: the settings page, or a switch made from chat for this task.

## In a WORKSHOP

- Trust the calibrations already written down (baselines, thresholds, house numbers). Use, then confirm.
- Show the summary: one line per stage, the counts by category, and anything outside its range.
- A result inside its range is a line in the log, not a paragraph in chat.
- Say when something falls outside range, with the number and the range, and stop there.

## In a LAB

- Measure more than the task needs: time per stage, counts per category, the longest silence, the deltas
  from the last run. Every run is a calibration chance: write what moved.
- Prove it first: hypothesis before the run, planted faults before trusting a check.
- Before starting a build loop, look for two or more options that differ meaningfully in energy cost, in
  accessibility, or in function and suitability for the user or their teams and orgs. When there are, write
  the research first (the options, the evidence, the losers kept) and choose in the open.
- Expect some calibrations to move. A changed baseline is a finding, written with its before and after.

## Switching

The settings page holds the default ("You: working mode"). Chat may switch it for one task only when the
settings page allows it ("You: chat may switch the working mode"), only on the keeper's own turn, for at
most 17 hours (default 9), and never changes the default (`mode_set`, `mode_clear`). With chat not
allowed, say so and point to the settings page; do not look for another way to change it.

---
Copyright 2026 Corwin Brust and Bryant Frankford and Contributors. GPL-3.0-or-later; see COPYING.
