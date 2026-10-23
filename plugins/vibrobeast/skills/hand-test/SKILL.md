---
name: hand-test
description: >
  Hand the user ONE chat-native test after a completed build/swing — run-card's rigor delivered in the chat (nothing to open), 3–5 DO/SEE-checkbox steps they tick as they flit. Use when laying a test/verification on the user: "hand-test", "lay a test on me", "how do I check/verify this", "give me steps to confirm it works", or after building something they'll verify by hand. NOT run-card (a paste-ready FILE for touching foreign systems), NOT rolls (status reports), NOT a CI runner.
---

# hand-test — a chat-native test-program, handed to the keeper

A **hand-test** gives the user *one* small test to run after a completed unit of work, delivered **in the
chat** so they never navigate away, never open a file, never parse code-vs-markdown in a pager. It carries
`run-card`'s spine (ordered steps · exact expected results · a clean/pass check) but is sized for a person
who is jumping around and must not lose the chat.

## When to use
- After you finish a build the user will verify **by hand** — a feature, a fix, a cross-fabric change.
- Ration it: **one hand-test per completed unit** ("swing"). Not after every edit; not a wall of checks.
- Do **not** use it for running against a foreign/production system you didn't build — that is `run-card`
  (a paste-ready, auditable file). Do not use it for status reporting — that is `rolls`.

## The form (keep it exactly this shape)
A titled card, **3–5 steps**, closing in one line. No preamble, no "why" inline (offer it on ask — extra
prose is noise that hides signal).

```
HAND-TEST — <the claim this proves> (<what unit/swing>)
Run at <the working directory>.

① <what this step proves>
   <ONE fenced, copy-paste command>
   - [ ] SEE `<the exact string/shape to look for>`  → <pass condition, ≤5 words>

② …
③ …

all ✓ ⇒ <the claim> holds.
```

- **DO = one fenced command.** The user's only terminal act is paste + enter. No `cd`-then-open-then-read.
- **`- [ ] SEE …` is a checkbox**, not prose. It carries the *exact* expected output next to the command
  so verification is a glance-compare, and the user ticks it inline as they go. It does **not** report back
  to you — it is *their* progress marker while they flit. (Mirror in a widget only if you also keep the
  plain-chat version.)
- **Close with one line**: `all ✓ ⇒ <claim> holds.`

## Non-negotiables
1. **Prove every DO yourself first.** Run each command in your sandbox before handing it. A hand-test that
   fails on the user's machine is worse than none — it spends their focus and their trust.
2. **Prereqs are proven, not assumed.** Name the real interpreter invocation and pin the working directory.
   Watch the user's actual toolchain — e.g. an interpreter not on `PATH`, a path with spaces that bites in
   bash, a relative `require`/import that needs the right CWD, a stricter compiler on their host than in
   your sandbox. If in doubt, lead with a one-time `alias`/PATH line.
3. **Chat-resident.** Never "go read `some.md`". The steps and expected outputs live in the chat message so
   they inherit real rendering (headings, fences) — code and prose never blur.
4. **Self-locating.** Because each step is self-contained (do / see / pass), flitting away and back costs
   nothing: the chat still says what to paste, what to see, and how to know.
5. **Un-pedantic.** 3–5 steps, five-word pass conditions, no ceremony. Over-instruction is the failure mode.

## Why this shape (the reading model it serves)
People who move fast between the chat and a terminal read differently: the **chat is the reading surface**
and every file-open is a flit-away cost plus a parse burden. They **copy-paste rather than navigate**, they
verify by **expected-beside-actual**, they filter hard so **rationed + high-signal** wins, and many are
**spatial thinkers** for whom an aligned DO / SEE / ✓ layout reads faster than a paragraph. Design to that.

## Interlocks
- `run-card` — the ancestor; use it (not this) for careful, auditable runs against systems you didn't build.
- `rolls` — status/close reports; a hand-test proves, a roll summarizes.
- `takushi` — the last-mile delivery; a hand-test is one clean thing that must land where the user can see
  it (the chat) and be acted on without you in the room.


## How this skill can fail (falsifiers)

- **An unproven DO.** fails if a step's command was not run in the sandbox before handing; check: each fenced command appears in an earlier tool call of the session, with the output its SEE line quotes.
- **SEE does not match.** fails if the keeper's output differs from the SEE string; check: put their output beside the SEE line. The first suspects are the toolchain prereqs (interpreter, PATH, working directory).
- **Too big.** fails if the card has more than 5 steps or asks the keeper to open a file; check: count the steps and look for "open" or "read <file>".

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-11.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
