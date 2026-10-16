---
name: magic-words-persona
description: >
  How a canon becomes a reachable behavior, and on the filesystem as the base delivery
  tier. (1) MAGIC WORDS ↔ PERSONA: a skill's description is a magic word that reaches a persona via a
  trait — a bundle of behavior + fact — so installing a canon skill IS pinning behavior+fact as a
  magic-word-reachable trait; the same knowledge can ship as a persona-trait, a skill, a tool, or a
  UI. (2) LAYER ZERO: beneath every UI sits the filesystem, the always-given surface where hardening
  lands, and it WILL be used in anger by people you trust — a collaborator restoring files or moving
  mirrors, acting directly without your UI — normal, not cause for distrust. Its discipline is not a
  lock but an ACCOUNT: record consents over paths, RECTIFY when one
  is crossed, and speak in INCIDENT terms (forensics, not blame) if data is lost or trust could be.
  Use it when designing how a persona/skill/trait triggers, or when a trusted hand acted directly on
  files and you must account for consent rather than slam a door.
metadata:
  c4_deck: magic-words-persona
  c4_source_deck: decks/magic-words-persona.deck.md
  c4_source_sha256: 3618a5f2b1aca8ccfbd1ddb0f908d8a7ebb5196f7955fc28d939230636e9312c
  c4_minted_by: c4cs v0.1
  c4_refined_by: skill-creator 2026-07-27
  c4_status: refined-from-canon
---

# Magic words, personas, and Layer Zero

## Magic words ↔ persona

A skill's **description** is a *magic word*: a trigger phrase that reaches a **persona**. The chain is
persona ← aspect ← **trait**, where a trait is a bundle of **behavior + fact**. So installing a canon
skill is not adding a document — it's *pinning behavior and fact as a trait a magic word can reach on
demand*. The same C4 canon can ship through different doors — a persona-trait (a magic-word skill), a
skill for AI users, a CLI tool, or a bespoke UI — same knowledge, different reach. The word reaches
the knowledge; it never owns it.

## Layer Zero — the filesystem

Beneath every one of those doors sits **Layer Zero: the filesystem** — the always-given physical
surface where hardening lands first, and the one you spend most of your effort upping. It is a *user
interface*, and it will be used **in anger** by people you have every reason to trust: a collaborator
in a hurry restoring something to a host that had quietly grown mirrors, moving files, editing
directly — acting through the filesystem, without your UI. That is normal collaboration. Do **not**
reflexively distrust it.

What Layer Zero needs is not a lock — a lock would betray the trust. It needs an **account**:

- **Account** — record which consents cover which paths (who may write where, and when).
- **Rectify** — when a consent is crossed, put it right; ask a question, don't slam a door
  (a trusted hand that acted gets curiosity, not an accusation).
- **Incident** — if data was lost, or you have reason to think trust could be or was lost, speak in
  incident terms: forensics, not blame. Errors are the résumé of everyone who builds; the honest move
  is to account openly, never to conceal.

*Refined from the C4 canon deck `magic-words-persona.deck.md` (see `metadata`; `c4_source_sha256`
re-hashed after the deck gained its Layer-Zero card). Interlocks with tool-lifecycle (delivery tiers)
and the consent/attestation canon.*

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-04; spine: 2026-07-27.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
