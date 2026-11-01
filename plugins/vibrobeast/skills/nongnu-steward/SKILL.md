---
name: nongnu-steward
description: >-
  Tend a free software project's artifacts to the standard a careful reviewer holds them to:
  copyright and licence notices on every nontrivial file, the licence texts in the tree, a
  dependency ledger with licences and URLs, "or any later version" on GNU licences, formats and
  words that stay free. Savannah's non-GNU hosting expectations are the floor, GNU's maintainer
  materials the form, and Emacs/GCC/coreutils/glibc/Guix/Arch practice the preferred handling. Use
  when setting up or reworking a project, adding a file or a dependency, preparing a release, when
  asked "is this project properly licensed", "add licence headers", "which licence for this", "what
  does Savannah expect", "steward persona for X", or at session open in a project carrying a
  .nongnu-steward file — there, whenever files, README, dependencies or a release are set up,
  reworked or published, even if nobody says "licence"; elsewhere only when named.
  Audits and suggests; edits only on --write; never signs, chooses a licence, or pushes a host.
---

# nongnu-steward — tending, not applying

A project is *tended* when a stranger who reads its tree for legal and philosophical soundness
finds nothing to send back. Savannah's non-GNU reviewers are the one group that does that reading
in public and writes down what they look for, so their expectations are the working floor here —
without ever assuming the project is going there. The skill mentions hosting only when asked, or
when the project already lives on a host whose rules are in play.

The model behind every rule is `references/MODEL-steward.md` (three rings, every expectation with
its source tag and its check). The verbatim notice texts are `references/notices.md`; the tending
list is `references/checklist.md`; the sources are pinned in `references/canon.tsv`.

## When this applies

- Setting up a new project, reworking an existing tree, or stamping a template project.
- A file is added (it needs a header), a dependency is added (it needs a ledger row), a release or
  a first public commit is in view ("committing to a public repository is distribution").
- Any phrasing of *is this licensed properly*, *add headers*, *which licence*, *what would a
  reviewer say*, *what does Savannah / GNU expect*, *steward persona for &lt;project&gt;*.
- **Implicitly, at session open**, in a project that carries a `.nongnu-steward` file — or where
  this skill was loaded by name — unless the preference `steward.auto` is off. Implicit means
  `sh scripts/ns1op --root .`: the local audits run, one summary line each, findings as rows for
  the handback; the canon line reports how old the pins are and the command for a careful check —
  it never fetches on its own. It never means editing.

## The four scripts (POSIX sh; run from the skill folder or by path)

    sh scripts/ns1op [--root DIR] [--no-canon|--force-canon]     the session open: headers · deps · canon, one line each
    sh scripts/ns1hd [--root DIR] [--quiet] [--tsv] [PATH ...]   headers: every nontrivial file (>10 lines)
    sh scripts/ns1hd --suggest FILE [--holder H] [--license ID] [--name N]  the header to paste, in the file's comment syntax
    sh scripts/ns2hw [--root DIR] [--write] [PATH ...]           the header pass: a plan per file by default; --write puts it in, sha-verified
    sh scripts/ns2ld [--root DIR] [--write] [--check]            dependency ledger LICENSE-DEPS.tsv; --check refuses UNKNOWN / no
    sh scripts/ns2ld --compat SPDX-ID                            one licence against the GPLv3 table (yes · no · ask · ?)
    sh scripts/ns2cn --check [SLUG...] | --diff SLUG | --refresh   a careful check: has this rule's source moved? (git blob id first)
    sh scripts/ns2cn --derive [SLUG...]                          a pin-only row with a snapshot gets the snapshot's blob id, no network
    sh scripts/<any> --prove-red                                 each script shows itself going red

`ns1hd` statuses: `OK` · `NO-NOTICES` · `NO-COPYRIGHT` · `NO-LICENSE` · `SHORT-NOTICE` (a licence
id such as `GPL-3.0-or-later` with no notice sentence — reviewers accept it with a note and ask for
the recommended text) · `GPL-ONLY` (a GNU licence without "or any later version" — refused) ·
`README-COVERS` / `BINARY` (a format-bound file — images and PDFs included — with, or without, a
README naming its copyright; a README that says `covers: *` covers every file in its directory) ·
`COPYING-MISSING` / `COPYING-LESSER-MISSING` / `COPYING-SHORT` (a licence file that names a GNU
licence but is too short to be its text). Exit 1 on findings. The audit skips `.git`, `vendor/`,
`externs/`, `dist/`, build output, lockfiles, signatures, archives and data tables;
`steward.ignore` adds more. `--suggest` fills the program's name from `--name`, else
`steward.name`, else the root directory's name (and says that was a guess).

`ns2ld` reads `configure.ac` (PKG_CHECK_MODULES, AC_CHECK_LIB), `requirements*.txt`,
`pyproject.toml`, `package.json` (dependencies, peerDependencies — not devDependencies),
`Cargo.toml`, `go.mod`, `Gemfile`, `PKGBUILD`, `*.el` Package-Requires, Guix `*.scm` inputs and
`*.cabal`. A new dependency's LICENSE is `UNKNOWN` until a person fills it from the dependency's own
COPYING and puts the page that says so in URL; the script never guesses a licence. Filled columns
survive a `--write`. A signed ledger is not rewritten without `--force`.

## The tending, in order

1. **Read the tree first**: `sh scripts/ns1op --root .` (headers, then the ledger if one exists,
   then canon if due). Say the counts with the commands beside them.
2. **A file at a time.** For each finding the keeper wants fixed, `--suggest FILE` prints the
   header (one-line description · copyright · SPDX line · the recommended notice); the session
   pastes it with the keeper's consent, in that session's normal edit path. Small licences (Expat,
   BSD) go in whole; a ChangeLog's notice goes at the end; a binary gets a README beside it.
3. **Dependencies.** `ns2ld --write`, then fill each `UNKNOWN` from the dependency's licence page,
   then `--check`. An `ask` row means the GNU licence list makes it conditional — read the entry.
4. **The rest of the checklist** (`references/checklist.md`): README contents, formats, words,
   NEWS, years, signed releases. These are read, reported and left to the keeper.
5. **Canon — a careful check, not a routine guard.** When a decision is about to lean on a rule
   (a licence question, a header form, a release), check that rule's source moved or not:
   `sh scripts/ns2cn --check SLUG` — one `git ls-remote` for a repository-backed row, one HEAD
   for a static page, one row at a time. Nothing here runs on a schedule: the canon hosts are the
   community's own machines, we are one reader among many of them each day, and on 2026-09-23
   one of them answered a wider check with a 502 page naming scraper load. A `CHANGED` row means
   the source moved: `--diff SLUG`, fold the difference into the model's paragraph that cites the
   slug, then `--refresh SLUG`. Offline or a server error is "nothing decided" / "unreachable",
   not a finding. Sources with no proper form (a page but no repository) are on
   `references/INQUIRE.md` with a draft note for the people who run them — the avenue there is
   to ask, not to scrape.

## Preferences (`.nongnu-steward` in the project root; `key value` per line, last wins)

`steward.auto` (on) · `steward.threshold` (10) · `steward.holder` · `steward.name` ·
`steward.license` (GPL-3.0-or-later) · `steward.canon` (on: report the pins; never fetch unasked) ·
`steward.jobs` (1) · `steward.timeout` (60) · `steward.ua` · `steward.ignore`.
`$HOME/.nongnu-steward` sets defaults for every project; `$NONGNU_STEWARD_PREFS` names a file
explicitly; beneath both, the plugin's `pref_set` ledger (`~/.mentcached/prefs.tsv`) holds
`steward.auto` and `steward.canon` from the seat. `sh scripts/nslib.sh` documents each key.

## Setting up, reworking, templating — and the persona

- **New project:** write `.nongnu-steward` (holder, licence), `COPYING` from
  gnu.org/licenses (plus `COPYING.LESSER` for LGPL), a README that meets checklist row 8, then
  headers on the first files via `--suggest`.
- **Existing tree:** the audit first, the counts second, then the keeper's order of work; never a
  bulk edit — the pen is the keeper's, and a bulk "fix" is exactly what the bad-guy roll in the
  persona template warns of.
- **Template project:** the same, with `<slots>` left where the template's users fill their own
  holder and licence, and a `.nongnu-steward` that names them as `<unset>` so the audit reports it.
- **A steward persona** for one project, when the user asks for one: copy
  `references/PERSONA-template-steward.md`, fill every slot, add the TSV sidecar, gauge it with
  `python3 bin/cs1gk SHEET.md` where that gauge exists. Generation is at the user's word only.

## What it will not do

Edit a file unasked (`ns2hw` plans; only `--write` edits, and it shows the sha it verified), sign
anything, choose a licence (it lays out `MODEL-steward.md` E18 and
`ns2ld --compat` and stops), recommend Savannah or GNU membership unprompted, treat "open source"
in a README as an error (it is a thing reviewers would ask about — E7), or fetch through a gate a
host has put up against automated readers (`FETCH=browser` rows in `canon.tsv` are read by a person
in a browser and recorded as such).

## How this skill can fail (falsifiers)

- **It fired on a tree it was not asked about.** The implicit run is for a project that carries
  `.nongnu-steward` or where the skill was named; anything else is a misfire.
- **A finding is wrong.** Open the file: if the notice is there and `ns1hd` said `NO-LICENSE`, the
  pattern or the 60-head/40-tail window is at fault — add the case to `--prove-red` and fix it.
- **The ledger guessed.** A LICENSE column filled by anything but a person reading the dependency's
  own licence text is a defect, not a convenience.
- **The canon check flaps.** `UNCHANGED` one minute and `CHANGED` the next on the same source
  means a volatile header slipped through; a blob id or the body text is the tie-breaker — and a
  body that is an error page is `UNREACHABLE`, never a change (`--diff SLUG` shows which).
- **It fetched on its own.** Any network request the keeper did not ask for in that session —
  a check "to keep fresh", a wider `--jobs` — is the misfire; a host answering 502/429 and naming
  scraper load is the one finding that outranks the rest. Stop, lower `steward.jobs`, say so.
- **It scraped a page it could have read from a repository.** Every `static` row on
  `INQUIRE.md` is a standing question; a `curl` row (per-request generated content) is a defect.
- **It pushed a host.** Any unprompted "you should apply to Savannah" is out of character.
- **Off-switch.** `steward.auto off` stops the implicit run; "no steward" in the conversation stops
  it for the session; the skill keeps no state outside `LICENSE-DEPS.tsv` and `.nongnu-steward`,
  both of which are the project's own files.

## Files

    SKILL.md                                 this
    references/MODEL-steward.md              the model: three rings, E1-E18, checks, falsifiers
    references/notices.md                    verbatim notice texts (GPL/LGPL/AGPL, all-permissive, FDL, SPDX)
    references/checklist.md                  the tending list, E-numbered, with the check per row
    references/PERSONA-template-steward.md   the steward persona template (gw7 shape; cs1gk-gaugeable)
    references/canon-seed.tsv                the referents (SLUG URL RING FETCH SNAP NOTE); FETCH = git · raw · static · browser · inquire
    references/canon.tsv                     the manifest: hashes, clock stamps, commit + blob ids, validators
    references/INQUIRE.md                    sources with no proper form yet, each with a draft note to send
    references/canon/<slug>.txt + README     text snapshots of the SNAP=yes rows, each with its stated permission
    scripts/nslib.sh  ns1op  ns1hd  ns2hw  ns2ld  ns2cn   the tools (open · headers · header writer · deps · canon)
    tests.sh · tests/spec.pl                 the suite (sh) and the black-box spec (Perl), both --prove-red

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-23.*

Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
