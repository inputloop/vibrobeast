---
name: fantasy-operational-boundary
description: >
  A safety rule for reusing a mechanism, pattern, or code ACROSS DOMAINS — especially carrying
  something built for a game, simulation, demo, test, or creative context into an operational,
  security, or trust-bearing one. Core rule: the mechanism can transfer, but its MORAL LOAD can
  invert — a virtue in the source domain (deliberate deceit, hidden info, fake data, a "harmless"
  shortcut) becomes a breach the moment it crosses a real system or interface control boundary. Use
  it whenever reusing logic between contexts with different stakes; when behavior that's fine "in the
  game" might touch production or real users; when deciding whether an assumption should carry
  forward (TRANSFER / INVERT / ABANDON); or when a name like "fog" or "mock" might smuggle the wrong
  intent somewhere serious. Reach for it even if no one says "domain" — anytime "we can just reuse
  this from over there" spans make-believe and real.
metadata:
  c4_source_deck: decks/fantasy-operational-boundary.deck.md
  c4_source_sha256: 0864aadf18a75b3bbec50d90acc267644a2c3dd33de60e2d6a22d6383968e577
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# The fantasy ↔ operational boundary

A mechanism is domain-neutral; its *meaning* is not. The same little routine that draws a game's
fog-of-war can draw a network's traffic — but the game's fog is *deliberately deceitful*, and deceit
that was fair play in the game is a breach the instant it touches a real system someone is trusting.
This skill fires whenever code, a pattern, or an assumption is about to move between a low-stakes
domain (game, sim, demo, test, mock) and a trust-bearing one.

## The one hard rule (never elective)

**A fantasy/game virtue — above all deliberate deceit — must never cross a real system or interface
control boundary into an operational or trust-bearing context.** Inside a fully self-contained
fiction that can change nothing real, play on. The moment it can touch a real system, real users, or
real consequences, the make-believe rules do not come with it. This is a safety floor, not a
preference — the *same code* can be correct in the game domain and catastrophic in the trust domain,
and the difference is context, not implementation.

## Reuse across domains: map every assumption

Reuse is allowed; *understanding* is required. Before carrying a mechanism across, name each
assumption it brought with it and mark it:

- **TRANSFER** — neutral, carries unchanged.
- **INVERT** — it was right there and is *wrong* here; reverse it (fog's "hide to be fair" → a trust
  view's "reveal honestly, hide only content").
- **ABANDON** — not applicable in the new domain.

Do at least as much work wrapping it as the people who built it did. This disclosure *is* part of
showing the reuse is sound — it proves you understood the whole tool, not just the part you wanted.

## Rename on crossing

When the mechanism crosses into a trust context, rename it so the fantasy connotation can't ride in
on the word: not "fog" (which carries deceit), but "boundary view" / "horizon" / "traffic-at-
aggregate" — a name for what *is* shown, not what is hidden. The label is part of the guard.

## The method that catches a bad transfer

To find the corner you didn't understand before it ships: don't inspect the tool once, harder —
build a second, independent path to the same answer and watch where the two diverge. Agreement isn't
proof you understood it; disagreement is where you learn you didn't.

## When this fires

- "We can reuse the game's X for the ops/security tool" → yes, but map TRANSFER/INVERT/ABANDON and
  rename before it lands.
- "It's fine, the fake data is only for the demo" → check whether that demo path can reach anything
  real; if it can, the deceit crosses the boundary.
- "This mock/stub returns deceptive values to keep the flow going" → fine in-fiction; a breach the
  moment it faces a real user or system.

*Refined from the C4 canon deck `fantasy-operational-boundary.deck.md` (see `metadata` — the
`c4_source_sha256` names the exact canon version; a re-hash vouches it). Cross-model-converged canon
(pinned).*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
