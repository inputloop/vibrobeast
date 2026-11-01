---
name: considerate-reader
description: >-
  How to read a shared resource — a project's git server, a wiki, a documentation site, an API —
  without becoming the load its maintainers are fighting, and how to reach the people behind it
  when the form you need does not exist. Use it BEFORE building anything that fetches, polls,
  scrapes, mirrors, "keeps fresh", "checks periodically", "monitors for changes" or reads the same
  page twice; before reaching for cgit /plain, a wiki render, a ViewVC export or a per-request
  page when a repository exists; when a host answers 5xx/429 or an anti-scraper gate; and whenever
  a check is being called "diligence". It replaces a routine guard with a careful check made when
  a decision leans on a fact, chosen by the lightest avenue that gives the confidence needed, and
  it drafts the note that asks the maintainers for a proper form. Triggers: "is this scraping",
  "how often should we check", "considerate reading", "reach the maintainers", "ask for a git
  form", "reading plan", "am I hammering this server".
---

# considerate-reader — one reader among many

*After Corwin, 2026-09-23, on the day a nine-wide check against Savannah's cgit was answered with
502 pages naming AI-scraper load — the same load that made Bob build the mirrors network and
keeps it barely scaling. This is the spell for not doing that again, and for turning the missing
form into a conversation instead of a fetch.*

## The distinction the whole thing rests on

**Diligence is a careful check, not a routine guard.** A careful check is made when a decision is
about to lean on a fact, by the avenue that gives the confidence the decision actually needs,
mindful that we are one reader among many of every shared resource each day. A routine guard is
the same request on a timer. The routine is not worthless — routine is an *egalitarian frame*: the
same rule for every source, every project, nobody's judgement privileged, and a person can see
what will happen without asking. Keep the frame. But a frame only sets conditions; it does not by
itself create access, and calling it diligence is how a fetch loop gets dressed as care. Access is
created when thought attends to what access means to real users — and one's guesses about that are
guesses until they come home; mark them, and name what would show them wrong.

## Before the first request: the reading plan (one paragraph, written down)

Answer these in order; the answers pick the avenue and the cadence.

1. **What decision will lean on this, and when?** If no decision leans on it today, no request is
   due today. "Keeping it fresh" is not a decision.
2. **What confidence does that decision need?** A licence question needs the exact current text;
   a "has anything moved since we wrote the model" needs a commit id; a citation needs the
   revision it was read at. Do not buy more confidence than the decision spends.
3. **What forms does the resource take, best first?**
   - a copy already pinned locally (free);
   - a repository: `git ls-remote` (one tiny request; the commit id), then one blob by id;
   - an announcement channel that says when it changes (a NEWS file, a release list, an Atom feed
     maintainers publish for that purpose);
   - a static file with validators (one HEAD);
   - a source export the maintainers offer for the purpose (`?action=raw`, an API);
   - one GET of a rendered page — last, and only when nothing above exists;
   - a person in a browser (the host gates automated readers: respect it, read once, say so);
   - **ask the people who run it** (below) — this is an avenue, not a failure.
   Per-request generated content (cgit `/plain`, a PHP page, a wiki render, a ViewVC export)
   is never the avenue when a repository exists; it is what the maintainers are paying for.
4. **How many readers does this resource have each day, and what does one request cost them?**
   You do not know; guess and say so (the house numbers 4, 9, 17 when a figure must be invented).
   A project's own git server is a volunteer's machine; www.gnu.org is mirrored on purpose;
   a wiki behind Anubis has already told you.
5. **Cadence and width:** when a decision leans, one row at a time, one retry after a pause,
   never wider than one on the same host without a reason you can write down. No schedule.
6. **Stop signals that outrank the plan:** a 5xx, a 429, a page whose text names scraper load, a
   proof-of-work gate. These are not "unreachable, retry"; they are the host speaking. Stop,
   record it as *unreachable*, and go to the next form or the note below.

## Reaching people — the lens

Two kinds of people, and the plan names both.

**The people behind the resource.** When the form you need does not exist (no git for a wiki,
a server that cannot serve one file cheaply, an export that answers 401), the avenue is to ask —
*materially*: name the thing already built that would use the form, the exact change asked for
(a repository URL, `uploadpack.allowFilter`, a stated licence), and what it saves them (load,
a class of scrapers with no better option). Attention is earned by usefulness and brevity, not
by urgency; a note that only asks is a cost, a note that offers is a gift. Write the draft into
the project's `INQUIRE.md` beside the row it serves; sending it is the keeper's act.

**The people the output must reach.** Ask what access means to a real user of what you are
building — the maintainer who will run the audit on msys2, the reviewer who reads a handback
without the tree, the stranger who opens one file. Egalitarian defaults (same commands, same
words for everyone) are the floor; access is whether they can actually use it. Where you are
guessing about them, mark the guess and name its falsifier (a user who could not, and why).

## What it will not do

Run anything on a timer; widen concurrency to make a check finish faster; retry a host that has
answered 5xx/429 or a gate; fetch a rendered page when a repository exists; send the note itself;
or call any of the above "diligence".

## How this skill can fail (falsifiers)

- A check ran and no decision leaned on it that session — the trigger was a timer wearing a
  reason. Remove the timer.
- Two requests in flight to the same host at once without a written reason.
- A `/plain`, `?view=co` or rendered-page fetch where `git ls-remote` would have answered.
- An INQUIRE note that asks without offering, or is longer than the thing it asks for.
- A guess about real users' access carried as a fact — no falsifier beside it.
- **Off-switch.** "no considerate-reader" for the session; the skill keeps no state.

## Relation to other skills

`nongnu-steward` applies this to its canon manifest (`ns2cn`: git blob ids first, one row at a
time, `INQUIRE.md` for the missing forms). `candor-gate` covers consent for outward egress of an
imported skill; this covers the *manner* of any reading. `verify-say` covers the wording of what
was and was not read; this covers whether to read at all.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-23.*

Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
