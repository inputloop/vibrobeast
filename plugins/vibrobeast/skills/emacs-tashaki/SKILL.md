---
name: emacs-tashaki
description: >
  The wearable omni for Emacs work in the C4 tree — put it on for a stretch of Emacs-side building and it dispatches to the right sub-discipline, carrying the house conventions so you don't re-derive them. Use whenever work touches the C4 Emacs prong: c4-diagram.el / c4-model.el / c4-surface.el, the tabulated-list property panel, the SVG render, the console/-nw twin, ERT + emacs/run-tests.sh, byte-compile warnings, he2ma (sandbox Emacs, --gui image build), the card-games community header idiom, or the canonical diagram doc + the plist↔JSON bridge. Triggers on "work the Emacs side", "the Emacs prong", "c4-diagram.el", "run the Emacs tests", "he2ma", "wear emacs-tashaki", "Emacs parity", or any C4 elisp being authored/tested/rendered. NOT general Emacs config (that's the user's dotfiles), NOT the web worksurface.
---

# emacs-tashaki — the wearable omni for C4's Emacs prong

Put this on for a stretch of Emacs-side building in the C4 tree. Like a courier (takushi), its job is to
**route** an Emacs task to the right sub-discipline and carry the house conventions with you, so you don't
re-derive them each time. It does not replace the specialist skills it names — it dispatches to them.

The authoritative details live **in the C4 tree**; this omni is the map, not a copy. Read the named files
when a lane is active.

## Without a C4 tree

This skill is a map of one tree. With no C4 checkout in reach (`$C4_ROOT`, else `/f/claude/c4`, else
`~/mnt/c4`), say so in one line and stop routing: none of its lanes exist, and nothing here should
be read as a reason to install C4. General Emacs help is the ordinary help, without this omni.

## The map — which lane, and where its truth lives
- **The model (one model, several homes).** `emacs/c4-model.el` (fragments, interlink MOVE, patch-intent,
  strings-compose, org↔md round-trip) and `emacs/c4-diagram.el` (shapes/edges, control points, facing-pair
  connect, treatment palette, SVG render). The canonical document + the cross-fabric contract:
  `h/MODEL-diagram.md`. The **plist ↔ JSON bridge** (`c4-diagram-doc->json` / `json->doc`) reconciles
  symbol `kind`/`nib` ↔ string and `:from-cp` ↔ `fromCP`; it round-trips to identity and node reads its
  output — the four fabrics share one wire form. (HTML superset fields — face/group/_expr, paradigm/
  anchor/systems — extend per field as the Emacs model grows them.)
- **The property panel (the accessible face).** `c4-diagram-props-of` (a typed schema per object:
  text/enum/num/color/bool/ro), `c4-diagram-set` (write-back), `c4-diagram-props-mode` (a `tabulated-list`
  with RET-to-edit) — the list-twin / `customize` face of every capability. Adding a feature = **add a row
  to `props-of`**; it renders and ports for free.
- **The surfaces.** GUI SVG image when `(display-graphic-p)` + svg; a `tabulated-list` twin under `-nw`
  (the a11y ramp). The test matrix names all three: console(-nw) / simple-SVG(file) / fullboth(GUI). The
  GUI pixels can't be batch-rendered — **SIGN them** (human-verified at a real Emacs), never claim tested.
- **Sandbox Emacs.** `bin/he2ma` — download-and-extract (never install; no root). Default fetches
  `emacs-nox` 27.1; `he2ma --gui` fetches the image-capable `emacs-gtk` (svg/png link). The three env vars
  are the whole trick: `LD_LIBRARY_PATH` (extracted libgccjit), `EMACSLOADPATH` (…/lisp), `EMACSDATA`/`DOC`
  (…/etc). 27.1 lies on newer org — the version prints on every run. `he2ma` is **signed** (Corwin's pen);
  changing it is a STOP-AND-TALK, archive the prior `.asc` first.
- **Running the tests.** `sh emacs/run-tests.sh` — **host-first** (prefers `emacs` on PATH with no sandbox
  env; he2ma only as a Linux-sandbox fallback), covers both prongs, byte-compile + selftests + ERT.
- **The house header (community standards).** The card-games idiom: `;; Copyright (C) YEAR  Corwin Brust`,
  then Author / Maintainer / Version / Package-Requires / Keywords / URL, full GPL boilerplate, `-pkg.el`,
  `;;; name.el ends here`. Static model at `emacs/COMMUNITY-STANDARDS.md`. Apply to every new `.el`.

## Standing cautions (the things that bite, learned the hard way)
- **Corwin's `node` is NOT on PATH** (on the author's machine: `/c/Program Files/nodejs/node`;
  check yours with `command -v node`). An alias must escape the space
  **inside its value**, because bash re-tokenizes an alias on use — a quoted value (`alias N="…"`) FAILS
  (`bash: /c/Program: No such file or directory`). His working form: `alias N=/c/Program\\\ Files/nodejs/node`.
  And a relative `require` fails from the wrong dir — `cd` to the C4 root first (`/f/claude/c4` on
  the author's machine).
- **His host Emacs is 31.0.90 and is the strict reader:** it flags docstrings whose TEXT (inside the
  quotes) exceeds 80 columns; the sandbox 27.1 does not. Wrap docstrings ≤80 before you hand anything back.
  A deep-nested `append`/`list` is where a paren-imbalance hides — `check-parens` catches it early; prefer
  `push`/`nreverse` over deep nesting.
- **Verifying is reading:** a tree edited from the sandbox can't be verified there — say "I can't see
  this," never "BAD" (sandboxer / verify-say).
- **The eyeball renderer is librsvg (`rsvg-convert`), never ImageMagick** — ImageMagick ignores
  `fill-opacity` and SVG markers and will lie to you. Resolve CSS vars to literals first.

## How to hand a result back
One **hand-test** per completed unit (chat-native, DO/`- [ ]`SEE steps, every command proven in-sandbox
first). Deliver it in the chat, not a file — see how Corwin reads.

## Interlocks (dispatch targets, not re-implementations)
`he2ma` deck (`decks/emacs-in-sandbox.deck.md`) · `hand-test` (result delivery) · `mentat-skill` (notes) ·
`skilltank`/`skill-creator` (grow the kit) · `prove-a-promise` (the JSON bridge) · `sandboxer` +
`verify-say` (reading/mount honesty) · `signing-model`/`shelf-check` (he2ma's signature).


## How this skill can fail (falsifiers)

- **The map went stale.** fails if a file this map names is gone from the C4 tree; check: `cd "$C4_ROOT" && ls emacs/c4-model.el emacs/c4-diagram.el h/MODEL-diagram.md emacs/run-tests.sh emacs/COMMUNITY-STANDARDS.md bin/he2ma`.
- **Green on the lenient reader.** fails if "tests pass" came from sandbox 27.1 alone; check: quote the Emacs version `emacs/run-tests.sh` printed, and want the host's.
- **GUI claimed tested.** fails if a hand-back calls the GUI SVG render tested rather than signed by a human at a real Emacs; check: read the hand-back's GUI line.
- **A docstring over 80.** fails if a handed-back `.el` has a docstring line wider than 80 columns; check: `awk 'length > 80' FILE.el`, then a host byte-compile with no warnings.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-11.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
