<!--
SPDX-FileCopyrightText: 2026 Corwin Brust <corwin@bru.st>, Bryant Frankford and Contributors
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Contributing to vibrobeast

Thank you for looking. A pull request here is the easiest way in, and it is read by a person.

## How this repository works

This repository holds what the build makes, not the source. The source tree lives on Corwin's
Forgejo (code.bru.st) and is built with `make dist`. So:

1. You open a pull request here, against `main`, in the usual way.
2. A maintainer runs `sh bin/gh1in PR-NUMBER` in the source tree. It reads `PATHS` (in this
   repository) to find where each changed file comes from, applies your change there on a branch
   named `pr/gh-NUMBER`, keeps you as its author, and says in words any file it could not place.
3. The next build carries the change back here, and the pull request is closed with a link to the
   commit that has it.

Generated files cannot be changed directly; `gh1in` says which generator to change instead
(`README.md` comes from `publish/github/vibrobeast/README.md.in`; `PRIVACY.md` and
`TERMS-OF-SERVICE.md` from `bin/tp2mt`; each `MANIFEST` from the build).

## Before you open one

- **Skills** (`plugins/*/skills/NAME/`): keep the `SKILL.md` front matter (`name`, `description`), say
  in the description when the skill should be used, and include a "How this skill can fail" section:
  each claim it makes, and the check that would show it wrong.
- **Servers** (`plugins/vibrobeast/servers/`): Python standard library only. Add a test that fails
  without your change. In the source tree, `python3 -m unittest discover -s tests` must pass.
- **Shell**: POSIX `sh`, checked with `dash -n`. A check you add should be able to show itself failing
  (a `--prove-red` mode), because a green check that cannot go red tells nobody anything.
- **Words**: plain ones. Say what a thing does and how to tell if it did. A claim a reader cannot check
  is a feeling, and is welcome if it is labelled as one.

## Work an agent wrote

Welcome, and signed the way this project signs its own: by the agent, for the person it worked for,
with the model when you know it, once at the end of the file and as the commit's author:
`Alfred (for Bryant)`, `Mentat (for Corwin; claude-opus-5-5)`, or `Claude (for YOUR NAME)` if you did
not name a persona. The byline says *for* somebody, always; the copyright and the say stay with that
person. Work you wrote yourself, sign as yourself. Please do not let a tool sign as you, and do not
sign an agent's work with your own name alone.

## Your words

If this project's words are not yours, say so in the pull request: a glossary entry, a setting's
title or a tool's description can change. Terms are explained where they ship (`GRAMMARY.md`), and
the person using the tools decides what their words mean (`word_register`).

## Licence of what you send

By sending a pull request you agree it may be distributed under the same terms as the file you change:
code `GPL-3.0-or-later OR LGPL-3.0-or-later`, prose `CC-BY-SA-4.0`. Add yourself to the copyright line
of a file you change substantially, as "and Contributors" already invites.

## Barriers count as bugs

If a step here needs more dexterity, sight, typing or jargon than it should, open an issue with the
**Barrier** form. Settings belong on a page or in a sentence to Claude, never in a hand-edited file.

## Where to talk

Issues here. People already in a Tavern with us can raise it there.

Authored by Mentat (for Corwin; claude-opus-5-5).
Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors. SPDX-License-Identifier: CC-BY-SA-4.0
