---
name: persona-engine
description: >-
  Use the garden's persona model carefully and without waste: decide first whether a persona is
  warranted at all (which of the four uses: a real person shared safely, a system actor, the
  context of an actor for a story, the tensions at an intersection), then resolve, read once, act
  in your own voice, sign "NAME (for PRINCIPAL)", and change a sheet only by appending with
  evidence. Carries the five refusals and the gate pe1gt, which answers GO, WAIT, HOLD or STOP
  before any persona work starts. Works with the persona MCP server when present and with plain
  files when not. Use when a persona, character sheet, byline, "for Corwin", persona_resolve,
  persona_mutate, mt1pl, cs1gk, rf1bm, a bias roll, the nine context models, or "should this be a
  persona?" comes up.
---

# persona-engine

A persona is a stand-in.  It lets the work speak about a person, a system or a meeting of the two
without carrying the person's own facts around, and it keeps the rights where they belong: a
persona writes *for* somebody, always.  Used well it saves explaining; used carelessly it costs
tokens, invents people, and gives defects a charming voice.  This skill is the careful path.

## First: is a persona warranted?

Run the gate, or answer its questions yourself:

    sh scripts/pe1gt plan --use N [--name NAME] [--for PRINCIPAL] [--declared yes|no]
                          [--second-use yes|no] [--consent yes|no] [--building yes|no] [--roll yes|no]

| use | what it models                                          | needs                                      |
|-----|---------------------------------------------------------|--------------------------------------------|
| 1   | a real person, so their view can be shared safely        | a declared sheet; consent unless the person is the principal |
| 2   | a system actor: its jobs (watching) and clothes (showing, stating, reporting, knowing) | a declared sheet; its second use, not its first |
| 3   | the context of an actor, to tell a story                | the actor's declared sheet                  |
| 4   | the tensions at an intersection of actors, or of an actor and a system or event | the LENS; the actors' sheets where declared; no new sheet |

No use named: no persona.  Say it plainly in your own voice.

The answers:
- **GO**: the steps below, in order.
- **WAIT**: not yet (a system feature on its first use; anything during a local build or test; no
  principal named, so name one with --for: the byline says *for* somebody, always).
- **HOLD**: a person must act first (consent for a third party's facts).
- **STOP**: a refusal applies (nothing declared, so nothing to resolve; a pre-engine voice asked to
  be re-rolled).

## The steps, when it is GO

1. **Resolve.**  `persona_resolve NAME` on the persona MCP server, or `sh bin/mt1pl --explain` in a
   garden checkout.  The order: `$MENTAT_PERSONA`, `Persona:` in CLAUDE.md, PERSONA.md, `.persona`,
   `persona:` in MEMORY.md; when none declares one, the voice is Mentat (the default, not a gap).
2. **Read once.**  `persona_read NAME` (the shelf sheet, with any chained generations beside it as
   its journal).  Keep what you read for the session; do not re-read to re-decide.
3. **Act in your own voice.**  You may describe the persona, quote its sheet, and work as its stand-in
   for the principal's judgment.  You do not write its journal for it.
4. **Sign.**  `persona_byline NAME PRINCIPAL [owns]` gives `Author: NAME (for PRINCIPAL)` and the
   copyright line in the principal's name; when the principal owns the content, the split line
   `PRINCIPAL (owns), transcribed & formalized by NAME`.  In the garden the footer is minted
   (`Mentat (for Corwin; MODEL)`) by `bin/ft1mt`; do not hand-write it.
5. **Change a sheet only by appending.**  `persona_mutate NAME entry evidence would_change`: the
   entry is the persona's own (from its session or its principal), the evidence is what happened,
   and would_change says what it changes.  All three, or no generation.  Never overwrite.
6. **Gauge before hand-back.**  If a sheet changed: `python3 bin/cs1gk SHEET.md` (sections, guards,
   evidence and story together, the NEWS mark, the sidecar, the corpus listing, the twin copy, the
   break-character watch, the system actor's bad-guy stage).  `persona_chain NAME` for chained
   generations.  A gauge you could not run is NOT CHECKED, said aloud.

## The five refusals

1. Never mint a persona.  A declaration pointing at a file that does not exist is a FAULT, never a
   cue to write that file.
2. Never write the persona's voice.  A skeleton may be drafted; the journal entry is the persona's own.
3. Never edit a sheet another session wrote, except by appending to that sheet's own log.
4. Never take the rights.  The byline says *for* somebody, always.
5. A persona's voice may not be the place a defect is explained.  Fix the thing first; then the
   persona may say what it likes about it.

(`sh bin/mt1pl --refusals` and the MCP server's `persona_refusals` state the same five, held word for word
by a test; `sh scripts/pe1gt refusals` prints them too.)

## Curating a new persona, and noting an authorial voice

Refusal 1 is about a pointer with nothing behind it.  Curation is a different act: the work has
already produced a voice, and the record shows it.  A new persona may be curated only when all six
hold:
1. LENS, or a method like it, was run;
2. the work can be written down;
3. the work made a material contribution that shows a constructive, representative voice;
4. two consumers are demonstrated;
5. the context has no persona already;
6. a first persona model of the context, from its own viewpoint, is written as `<ITEM>-PERSONA.md`.

The first model is a viewpoint model (what the context sees, wants and guards), not the persona's
journal, so refusal 2 still holds.  Mutating a persona that exists follows step 5 above: append,
with evidence.

**An authorial voice.**  Writing prose for people may grow a new authorial voice.  It needs no
second consumer.  It is documented only to tell an editor, or another supervising persona that
already exists, that the voice contributed material worth noting.

**A persona as a skill.**  Where a customary form gives a chance to put the work in a perspective
(credits, a colophon, an acknowledgement), use an established persona the way a skill is used:
through LENS, or a similar method.  If LENS is unavailable or budgeted out, say so and log it.
Treat the persona as a personified actor unless the material shows that a human holds rights in it
(a copyright or licence line).

## Careful, not wasteful

- **Second use.**  A system feature does not get a persona on its first local use; wait for the
  second.  Never during a local build or test.
- **Pre-engine voices.**  Vibrobeast and Mentat grew their voices before the bias engine existed.
  Do not re-roll them, however the name is typed (mentat is Mentat).
- **Rolls are folds.**  A bias roll for a system actor uses `bin/rf1bm` (fold to 36, seeded 6x6,
  `--fate`; reuse with `--fate-from`), never a random sample.  A system, host or place actor takes
  one bad-guy roll, kept, plus an inversion stage.  Traits: `bin/pg1rl`.
- **Method travels, cases don't.**  A use-1 sheet shares a person's view, not their private facts.
  Facts about a third party need their consent before they persist (consent-gate).  A file with
  SECRET in its name is never read.
- **Gauges, not memory.**  When a sheet looks wrong, run the gauge; do not trust a recollection of
  the shape.
- **The kit says when and how, never whom.**  Stop short of directing that a particular persona be
  created; offer the shape and let the principal decide.
- **Read once, cite the path.**  One read per session; quote the sheet by path, not from memory.

## The nine context models

The four uses are played back two ways: apart from the LENS, and in the LENS's terms.  A subject
either comes in as a consuming context (one model), or comes back with up to four evolved versions,
one per use, plus a composite of them (eight), for nine in all.  Build only the ones the question
asks for; the composite is earned, not default.

## When the MCP server is absent

Everything above works with plain files: resolve with `bin/mt1pl` or by reading the order by hand;
read the sheet file; sign by the byline form; append to the sheet's own log section with the
evidence beside the entry; run `cs1gk` if you have the garden, and say NOT CHECKED if you do not.
`sh scripts/pe1gt sheet FILE` checks what makes a file a sheet to the tools (an actor: line or a
sheet heading), names the defaults that apply when name: or principal: is absent, looks for the
journal, and names the fuller gauge it is not.

## Leans on

Required: nothing beyond this folder.  Recommended: lens (run before any hand-back that a persona
shaped).  When present: consent-gate (use 1), eclipse-pass (stress a persona's claim),
fantasy-operational-boundary (a fiction persona near a real system), the persona MCP server,
`bin/mt1pl`, `bin/cs1gk`, `bin/rf1bm`, `bin/pg1rl`.

*Version 0.3: edition revised from 0.2 on 2026-10-05; spine: 2026-10-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
