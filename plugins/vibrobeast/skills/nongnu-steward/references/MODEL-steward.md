# MODEL-steward — the care a free software project's artifacts are owed

*Read from one narrow perspective outward: what Savannah's non-GNU hosting expects (ring 1), then
what the GNU materials Savannah points at say (ring 2), then how the flagship packages actually do
it (ring 3, the preferred handling). Every expectation carries its source and the check that would
show it wrong. Two piles: what a source SAYS is tagged with its slug; what this model CONCLUDES is
tagged [JUDGED]. The slugs resolve in `canon.tsv`, which pins each source with a hash and a clock
stamp; `sh scripts/ns2cn --check` says whether any of them has moved since.*

Contents: §0 the perspective · §1 ring 1, E1–E11 (Savannah) · §2 ring 2, E12–E18 (GNU form) ·
§3 ring 3 (Emacs, GCC, coreutils, glibc, Guix, Arch) · §4 the two notice idioms · §5 what the
steward tends and with what · §6 what it does not do · §7 falsifiers · §8 provenance.

Tags: `[SV:<slug>]` Savannah · `[GNU:<slug>]` gnu.org · `[FLAG:<slug>]` a flagship package ·
`[JUDGED]` this model's own reading. A slug is a row in `canon.tsv`; the rows whose page permits
a copy have a text snapshot in `canon/<slug>.txt`.

## 0. The perspective, and why it is the right narrow one

Savannah reviews every non-GNU submission by hand against a short public policy and a longer body of
reviewer notes. It is the one place in the free software world where somebody *reads your tree for
legal and philosophical soundness before letting you in*, and says in writing what they look for.
That makes its expectations a good working definition of "tended" for any free software project,
whether or not it will ever be hosted there — and this model never assumes it will be. Hosting is
mentioned only where a source is about hosting; the skill does not push it. `[JUDGED]`

Three facts frame everything below:

- **Committing to a public repository is distribution.** "Distribution, in any form, is the usual
  trigger for copyright-based licenses" — so the legal parts of packaging are due *before* the
  first public commit, not at the first tarball. `[SV:sv-why-legal-checks]`
- **Reviewers nitpick, and say so, but approve over small things.** A project that is free, has no
  nonfree dependencies, consistent licensing and consistent notices, "but uses an old FSF address
  or lacks a complete copy of the license" is approved with a note rather than sent back.
  `[SV:sv-requirement-threshold]` So the care is graded: some misses block, most are corrected.
- **Policy and advice are separate documents.** The hosting requirements page is the rule
  `[SV:sv-requirements]`; the approval checklist is "not the official hosting policy; just advice"
  `[SV:sv-approved-quickly]`. The model keeps that line: E-rules below cite the rule; P-rules cite
  the advice.

## 1. Ring 1 — what Savannah expects (the rule and the reviewer's notes)

Each entry: the expectation · source · **check** (what a session runs or reads to know) · what
fails it.

**E1 Free, and independent of nonfree software.** The project must be free software and "kept
independent of any nonfree software"; it must not "refer the user to any nonfree software", must
not automatically download or install any, and must "deliver its full functionality and
convenience on a completely free platform". Running *also* on nonfree platforms is fine provided
free software gets "at least as good support". `[SV:sv-requirements]` Android: Replicant yes;
anything depending on proprietary drivers or AndroidOS no. `[SV:sv-requirements]`
**check:** read the README, the build files and the dependency ledger (`ns2ld`) for anything that
names a nonfree platform as required, or a nonfree service as the way to use the program. **fails:**
a "requires X" where X is nonfree; a download step that fetches a nonfree blob.

**E2 A GPL-compatible licence, with "or any later version".** The licence must be one that gives
the freedom "to use, study, copy, and distribute the source code and distribute modified versions"
and is "compatible with the GNU GPL version 3 and any later versions". GPLv3-or-later is
recommended; the "or any later version" formulation is *required* for the GNU GPL, AGPL and LGPL.
`[SV:sv-requirements]` GPL*-only "is not acceptable"; LGPLv2.*-only is accepted because it converts
to any GPL, but is recommended against. `[SV:sv-licensing-requirements] [SV:sv-gpl-two-or-later]`
Manuals: GNU FDL, current version or later, or something compatible with it; informal materials
(FAQs, README) may be under a GPL- or FDL-compatible licence. Images and other secondary data: any
free licence — free meaning you can freely use, modify and share it, with or without modification.
`[SV:sv-licensing-requirements] [SV:sv-license-free-3-points]` A licence not on the list is reviewed case by case,
"most likely" by the FSF licensing group. `[SV:sv-requirements]`
**check:** `ns1hd` reports `GPL-ONLY` for a GNU licence named without the or-later clause; the
licence id against `ns2ld --compat`. **fails:** "GPL version 2" with no "or later"; a licence the
GNU list marks incompatible.

**E3 Copyright and licence notices on every nontrivial file.** "Proper legal notices should be
applied to, at least, each source (non-derived) file" `[SV:sv-requirements]`; "any file more than
ten lines long is nontrivial, so it should have copyright and license notices"
`[SV:sv-valid-notices]`. Source files "include Makefiles, scripts, image files, and ChangeLogs …
not just bare source code" `[SV:sv-approved-quickly]`. Binary files may carry their notices in a
README in the same directory `[SV:sv-valid-notices] [SV:sv-requirements]`. Derived files: "ideal"
to carry generated notices, not required `[SV:sv-approved-quickly]`. The notice text: "Please use
the exact form of the license notices recommended in" the GPL HowTo `[SV:sv-valid-notices]`; for a
small licence (Modified BSD, X11, Expat) "include it entirely at the top of all your files"
instead of a notice; public-domain files get a note saying so, naming the authors.
`[SV:sv-valid-notices]` Copyright holder: real names or entities with legal status are recommended;
"Project Foo contributors" is acceptable though weaker in court. Year lists may be ranges.
`[SV:sv-valid-notices]`
**check:** `sh scripts/ns1hd` (statuses `NO-NOTICES`, `NO-COPYRIGHT`, `NO-LICENSE`,
`SHORT-NOTICE`, `BINARY`); `--suggest FILE` prints the recommended form. **fails:** any nontrivial
file with no `Copyright` line or no licence sentence; a licence named only by an id
(`SHORT-NOTICE` — accepted with a note, but the recommended text is what reviewers ask for).

**E4 The full licence text travels with the code.** "Without a license notice giving permission to
copy and change the file, the file is nonfree" `[GNU:gnu-maintain-license-notices]`; "a copy of
the full text of all applicable licenses should also be included in the project" `[SV:sv-requirements]`; "as plain text, do not
point users to an external source" `[SV:sv-approved-quickly]`. GPL/AGPL go in `COPYING`; the LGPL
adds `COPYING.LESSER` beside `COPYING` (the LGPLv3 is additional permissions on the GPL, so both
are needed) `[SV:sv-valid-notices]`. The FDL goes in as a *section of the manual*, and every
end-format (PDF, HTML) must print the whole licence and a copyright line. `[SV:sv-valid-notices]
[SV:sv-documentation-notices]`
**check:** `ns1hd` reports `COPYING-MISSING` / `COPYING-LESSER-MISSING`; a manual's build output
contains the FDL. **fails:** a `LICENSE` that is a URL; an LGPL project with only `COPYING`.

**E5 Dependencies are free and licence-compatible, and you can point at their licences.** "Your
project dependencies need to be free, and compatible with your license" `[SV:sv-project-dependencies]`;
"give us URLs to your dependencies, ideally with direct links to their website pages explaining their
licensing" `[SV:sv-approved-quickly] [SV:sv-uris-to-dependencies]`. Do not combine incompatible code
(the example given is GPL with CPL); avoid Perl modules under the Artistic licence only and PHP
modules under the PHP licence; Java on IcedTea/OpenJDK, .Net on free implementations.
`[SV:sv-approved-quickly] [SV:sv-cpl-issues] [SV:sv-java-issues] [SV:sv-php-issues]`
**check:** `sh scripts/ns2ld --check` — every declared dependency has a licence filled in and a
`yes` (or a read `ask`) in GPL3-COMPAT, and a URL. **fails:** a row left `UNKNOWN`; a `no`.

**E6 Formats that free software can create and edit.** Files "need to be created / editable using
free software, and the free replacements need to be at least as good" `[SV:sv-file-formats]`. For
documentation: LaTeX, Texinfo, ODT are fine; Word and RTF are not accepted; HTML is fine "as long
as it comes with the source format". `[SV:sv-documentation-formats]` No nonfree formats in the
package or recommended by it. `[SV:sv-requirements]`
**check:** `find` for `.doc .docx .rtf .swf .fla .psd`-class files; generated HTML with no source
beside it. **fails:** a manual whose only form is a `.docx`.

**E7 Words.** Describe the package as "free software", not "open source"; say "GNU/Linux" when the
system is meant. `[SV:sv-requirements]` No "Open" in the project name; no "GNU" in the name unless
officially dubbed; identifiers "reasonably descriptive, rather than terse abbreviations or
confusingly general"; unix group names at least four characters, globally findable.
`[SV:sv-requirements] [SV:sv-approved-quickly]`
**check:** `grep -rniw 'open source' README* doc/`; the name. **fails:** "OpenFoo"; a README that
calls the package open source. *(This is a stated preference of the host; a steward names it, and
the project decides. `[JUDGED]`)*

**E8 No advertising.** Nothing commercial advertised, with two exceptions: pointers to commercial
support for the project itself, and fan items the project sells directly. `[SV:sv-requirements]
[SV:sv-no-advertising]`

**E9 Work with upstream first; be a project, not a shelf.** When a submission is a feature,
translation or i18n effort for another project, reviewers ask whether upstream would take it as a
branch or patches instead `[SV:sv-upstream-collaboration]`; storage-only or backup-only use is
declined, as are "simplistic text-only projects" `[SV:sv-approved-quickly]`. **check:** the README
says what this is that upstream is not. `[JUDGED]`

**E10 Releases: signed, world-readable, plain.** On the Savannah download area two files go up per
release: the file and a detached binary signature made with `gpg -b`; `scp -O` since OpenSSH 9;
`chmod a+r`; signatures are not enforced or verified by the host. `[SV:sv-download-area]` Project
web pages live in a separate CVS repository; no symlinks (a `.symlinks` file instead); `.htaccess`
within limits. `[SV:sv-homepage]` (The tarball shape itself is GCS 7.3 — ring 2, E13.)

**E11 Licence changes and dual licensing.** The licence field can only be changed by admins,
because it must remain free `[SV:sv-changing-license]`; dual licensing needs every included
third-party piece compatible with *both* licences and the permission of all copyright holders to
move from single to dual; an example combined notice is given. `[SV:sv-dual-licensing]`

**Reviewer stance, for calibration.** The reviewer's own checklist is the submitter's checklist
`[SV:sv-project-approval]`; the mechanics are a tracker item, a group-type check ("often
submitters choose 'official GNU' by mistake") and a green V `[SV:sv-approving-submission]`. GNU
and non-GNU projects share accounts, trackers and VCS; web pages and lists differ by domain; a
non-GNU project can later become GNU through the GNU evaluation process, which "does not happen
through Savannah" `[SV:sv-gnu-vs-nongnu] [SV:sv-nongnu-to-gnu] [SV:sv-approved-quickly]` — this
skill points at that only when asked. What the host itself offers (a choice of VCS, trackers,
lists, web pages, a download area with mirrors, no advertisements) is answer material for the same
question, not a pitch. `[SV:sv-why-choose-savannah]`

## 2. Ring 2 — what GNU says where Savannah points

Savannah's pages defer to the GNU maintainers' guide (`maintain.texi`, chapter 6 "Legal Matters"
`[GNU:gnu-maintain-legal-matters]`), the GNU Coding Standards and the GPL HowTo for the *form* of
things. What those add:

**E12 The notice, exactly.** Copyright notice: `Copyright (C) year1, year2, year3 copyright-holder`;
the word "Copyright" always in English; `(C)` optional, C-in-a-circle where it works.
`[GNU:gnu-maintain-copyright-notices]` Years: add each year with nontrivial changes; never delete
old years; a range `2008-2010` is allowed only if every year in it is copyrightable *and* the README
carries the sentence "For any copyright year range specified as YYYY-ZZZZ in this package note that
the range specifies every single year in that closed interval." `[GNU:gnu-maintain-copyright-notices]
[GNU:gnu-gpl-howto]` Files copied from another project keep their own notice (gnulib is the
example). ChangeLogs carry their notices *at the end*. Generated files copy the notice of their
source, or say what they are generated from. `[GNU:gnu-maintain-copyright-notices]` The licence
notice for a multi-file program begins "This file is part of NAME" and names NAME in the three
places; a one-file program uses "This program"; Lesser/Affero are inserted before "General" in all
three places; the closing pointer is `<https://www.gnu.org/licenses/>`. `[GNU:gnu-gpl-howto]
[GNU:gnu-maintain-license-notices-code]` The verbatim templates are in `notices.md`.

**E13 The tarball.** `foo-69.96.tar.gz` unpacking into `foo-69.96`; a README with the name,
version (or where to find it), description, a pointer to INSTALL, a note on unusual top-level
files, and "a reference to the file which contains the copying conditions"; GPL in `COPYING`, LGPL
in `COPYING.LESSER`; no symlinks; world-readable files, 755 directories; generated files only if
up to date and machine-independent; ship the `texinfo.tex` you used. `[GNU:gnu-standards-releases]`
**check:** the README against that list; `find . -type l`. `[JUDGED]`

**E14 Small supporting files.** Short manuals under 300 lines and rough documentation (README,
INSTALL) may use the all-permissive notice ("Copying and distribution of this file, with or without
modification, are permitted in any medium without royalty provided the copyright notice and this
notice are preserved. This file is offered as-is, without any warranty.") or be public domain; CC0
is for data, "don't use CC0 for software code". `[GNU:gnu-maintain-license-notices-other]`

**E15 External modules you did not write.** Use them as libraries: link to an installed copy, or
ship the source in its own subdirectory whose README says it is not part of the program; the
module's licence must be compatible with current *and future* GPL versions — GPL-2-or-later, LGPL,
AGPL-or-later and lax permissive licences are fine; "GPL version 2 only" and "GPL version 3 only"
are not. `[GNU:gnu-maintain-external-libraries]` Code copied *into* the tree from a GPL-compatible
package: record its authors as the contributors of that part; public-domain code needs every author
to have disclaimed. `[GNU:gnu-maintain-copying-from-other] [GNU:gnu-maintain-non-fsf-package]` Canonical licence texts come from
gnu.org/licenses or gnulib. `[GNU:gnu-maintain-canonical-license-sources]`

**E16 References to nonfree software.** Do not "recommend, promote, or grant legitimacy to the use
of any nonfree program"; a well-known one may be mentioned in passing with only the information a
user of it needs, "preferably after first explaining how to achieve the same results on the GNU
system with solely free software"; an obscure one is not mentioned at all; a free program that
depends on a nonfree platform is judged as that platform. `[GNU:gnu-standards-references]` This is
the GNU standard behind Savannah's E1. `[JUDGED]`

**E17 The employer disclaimer, the startup notice, the AGPL offer.** Ask an employer or school to
disclaim copyright interest before release; interactive programs may show a brief copyright and
copying notice at startup; an AGPL program that talks to users over a network must offer its source
to them. `[GNU:gnu-gpl-howto]` Documentation licence notices: FDL notice after the copyright
line(s), invariant sections and cover texts stated (or "with no Invariant Sections"); the FDL
included in the manual. `[GNU:gnu-maintain-license-notices-docs] [GNU:gnu-fdl-howto]`

**E18 Choosing a licence.** GPLv3-or-later for most software; Apache 2.0 for small programs under
about 300 lines where copyleft buys little; LGPL only when the library's free alternatives are
already common; AGPL for network services; FDL for manuals; CC BY-SA 4.0 or CC0 for other works.
`[GNU:gnu-license-recommendations]`

**Hosting, from GNU's side.** GNU recommends savannah.gnu.org for repositories "but that's not
required"; ftp.gnu.org for GNU releases; a company-hosted GNU package must say it is not the
company's product. `[GNU:gnu-maintain-hosting] [GNU:gnu-devel]`

## 3. Ring 3 — flagship practice, the preferred handling

Savannah sets the floor. The packages below set the shape of good tending, and where they go beyond
the floor the skill treats their way as *preferred*, never required. `[JUDGED]`

**Emacs** `[FLAG:emacs-admin-copyright] [FLAG:emacs-contribute]`
- "Every non-trivial file distributed through the Emacs repository should be self-explanatory in
  terms of copyright and license" — including files never shipped in releases, because the
  repository is public. Trivial ≈ under 15 lines of actual content; put a reminder comment in a
  trivial file ("add a license notice if this grows to > 10 lines of code") so it cannot grow past
  the line unnoticed.
- Years are updated every year across the tree (an `admin/notes/years` procedure; gnulib's
  `update-copyright` does the same job elsewhere). Refcard PDFs show a copyright even though
  generated; the year list lives in comments in the source.
- Images: one README per directory with images carries their notices.
- Non-trivial README and other text files get the same notices as code.
- The long notice sits at the top; some files say "See the end of the file for license conditions"
  and keep it at the end — a reader (and `ns1hd`) looks in both places.
- Contribution: after "a dozen or so lines of non-trivial changes" a copyright assignment to the FSF
  is needed; commit messages are ChangeLog entries (ChangeLog files are generated from git at
  release); a tiny change is marked `Copyright-paperwork-exempt: yes`; user-visible changes get a
  NEWS entry whose first sentence fits one line.

**GCC** `[FLAG:gcc-contribute]`
- Legal prerequisite: an FSF copyright assignment *or* the Developer Certificate of Origin via
  `Signed-off-by:`; DCO entries in MAINTAINERS are a permanent record, never removed once used.
  Small changes are accepted without either.

**coreutils** `[FLAG:coreutils-hacking]`
- `make syntax-check` (and `make distcheck`) run "many integrity and project-specific
  policy-conformance tests" — the model for a project keeping its own tending mechanical rather
  than remembered. Assignment for changes over ~10 lines; NEWS for user-visible change; `--help`
  text is the source of the man page; prose in the active voice.

**glibc** `[FLAG:glibc-contribution-checklist]` *(read in a browser; the host gates automated
fetching)*
- LGPL-2.1-or-later. Contributions by FSF assignment *or* DCO sign-off; assignment-covered commits
  do not add `Signed-off-by`, so the two can be told apart. DCO contributions add the line
  `Copyright The GNU Toolchain Authors.` under the file's one-line description; a file copied from
  elsewhere keeps its foreign notice and gains an FSF line beside it.
- Years are updated by a script (`scripts/update-copyrights`); contributors do not touch them.
- Every file starts with a one-line description, then the copyright, then the notice.
- "Contributed by" lines were moved out of files into a top-level `CONTRIBUTED-BY`; attribution
  lives in git (`Author`, `Co-authored-by`, `Reviewed-by`, `Suggested-by`).
- Commit subject: `subsystem: summary [BZ #n]`; the body explains reproduction, observed vs
  expected, the solution and alternatives, and which targets were tested.

**Guix** `[FLAG:guix-contributing-texi] [FLAG:guix-texi]`
- A package is a recipe *plus metadata including licensing*, and the distribution "provides only
  software that conveys these four freedoms", following the free system distribution guidelines;
  a free upstream with a nonfree corner is shipped with that corner removed at the source.
- Bundled ("vendored") dependencies are removed and the package built against separately packaged
  copies — the distribution-side view of E5/E15: a tree that vendors copies of libraries is a tree
  whose licensing a downstream cannot reason about. `[JUDGED]`
- Names: lowercase upstream name, underscores to hyphens, no `lib` prefix unless upstream has it.
- `guix lint` is a checklist a steward can borrow: synopsis/description style, source and home-page
  URLs that resolve, a stable release tarball rather than an autogenerated one, archival at
  Software Heritage, known CVEs, formatting (trailing whitespace, tabs).
- `etc/copyright.el` inserts and updates the copyright line from Emacs (`M-x copyright-update`).

**Arch** `[FLAG:arch-pkgbuild] [FLAG:arch-package-guidelines]`
- The `license` field is an SPDX identifier or expression (`GPL-3.0-or-later`,
  `'GPL-2.0-or-later OR LGPL-2.1-or-later'`, `WITH` exceptions); common licence texts are provided
  system-wide, everything else is installed to `/usr/share/licenses/<pkg>/` from the tree.
- Package sources themselves are 0BSD, declared through a `REUSE.toml` and checked by
  `pkgctl license check` — a machine-checkable licensing layout that downstream packagers read.
- **What this means for a project's tree:** a downstream packager needs one unambiguous SPDX id per
  licence, a licence file they can install, and per-file clarity the REUSE tooling can verify.
  `[JUDGED]`

## 4. The two idioms, reconciled

GNU's long notice (E3/E12) is what Savannah reviewers ask for by name. The SPDX line
(`SPDX-License-Identifier: GPL-3.0-or-later`) is what Arch, REUSE and much downstream tooling read.
They do not conflict: the preferred header carries **both** — a one-line description, the copyright
line, the SPDX line, then the recommended notice text. An SPDX line *alone* is a `SHORT-NOTICE`
under E3: accepted with a note, not the recommended form. `ns1hd --suggest` prints the combined
header. `[JUDGED]`

## 5. What the steward tends, and with what

| expectation | tool / check | implicit? (pref `steward.auto`, on) |
|---|---|---|
| E3, E4, E12 notices and licence texts | `ns1hd` (audit) · `ns1hd --suggest` (the header) | yes: `ns1op` at session open runs it and reports |
| E5, E15 dependencies and their licences | `ns2ld` (ledger `LICENSE-DEPS.tsv`) · `--check` · `--compat` | yes: `--check` at open when a ledger exists |
| E2 or-later, compat | `ns1hd` `GPL-ONLY` · `ns2ld --compat` | yes |
| canon — a careful check | `ns2cn --check SLUG` (one ls-remote / one HEAD) · `--diff SLUG` | no: on demand only; `ns1op` reports the pins' age and the command |
| E1, E6, E7, E9, E13, E16 | read by the session: README, build files, names, formats | reported, never edited unasked |
| E10 signed releases · E17 disclaimer, startup, AGPL | named when a release or a first publication is in view | — |

The pen stays the keeper's: no script here edits a file. A finding comes back as a row, and a
header comes back as text to paste. `[JUDGED]`

## 6. What this model does not do

It does not recommend Savannah, GNU membership or any host unless asked or the project is already
there; it does not choose a licence for a project (it can lay out E18 and `ns2ld --compat`); it
does not sign anything; it does not treat "open source" in a README as an error, only as a thing
Savannah would ask about (E7); it does not fetch through a gate a host has put up against
automated readers (`FETCH=browser` rows are read by a person in a browser and said so).

## 7. Falsifiers — what would show this model wrong

- A Savannah reviewer approves, without a note, a project whose files carry only SPDX lines → E3's
  `SHORT-NOTICE` is too strict; downgrade it to informational.
- `ns2cn --check` reports `CHANGED` on `sv-requirements` or `sv-valid-notices` → the rule moved;
  re-read the snapshot diff before trusting any E-rule that cites them.
- A flagship package drops long-form notices for SPDX-only headers (watch `emacs-admin-copyright`,
  `coreutils-hacking`) → §4 is out of date.
- `ns1hd` calls OK a file a reviewer would send back, or vice versa → the classifier's window (60
  head / 40 tail lines) or its patterns are wrong; the fixture in `--prove-red` is where to add the
  case.

## 8. Provenance — and the form a source takes

Every source above is a row in `references/canon.tsv`: its URL, ring, **form**, the sha256 over
the HEAD response (for a repository, the `git ls-remote` line — the HEAD request, literally) and
over the normalised HEAD, the clock stamp taken after that HEAD answered, the commit and blob ids
or the HTTP validators, the body-text sha, and (for `SNAP=yes` rows) a text snapshot under
`references/canon/`, whose README states each copy's source and the permission it was kept under.

**The form is the point.** A page is not a form; the file its maintainers edit is. In order of
preference: `git` (a blob in a repository — pinned by id, diffed by id, checked with one
`ls-remote` that costs the server almost nothing) · `raw` (a source export such as a wiki's
`action=raw`) · `static` (a file published once and served as-is, which a HEAD can validate) ·
`browser` (a host that gates automated readers; read by a person, said so) · `inquire` (no proper
form known; the question, with a draft note, is in `references/INQUIRE.md`). Per-request
generated content (cgit's `/plain`, a PHP page, a wiki render) is never scraped: it is the load
that the people running these machines have been fighting, and it is also the wrong object to
pin. On 2026-09-23 the hosting-requirements rule was re-pinned from its source in `savane.git`
(with its own AGPL/GPL header), the licence texts from `gnulib.git`, GCC's page from
`gcc-wwwdocs.git`; the Emacs, coreutils and Guix files are pinned at commit level until their
blobs can be fetched on a day Savannah's git server (which ignores partial-clone filters, so one
file costs a whole-tree depth-1 fetch there) is calm. `[JUDGED]`

**Diligence is a careful check, not a routine guard.** Nothing in this skill re-reads a shared
resource on a schedule. The routine — the same manifest, the same ladder of forms, the same audit
for every project — is kept because routine is an egalitarian frame: no source and no project gets
a different rule. But that frame only sets conditions; it does not by itself create access, and it
must not be mistaken for diligence. Diligence is the situated check made when a decision is about
to lean on a rule, by the avenue that gives the confidence the decision needs, mindful that we are
one reader among many of every resource each day. **Be a considerate client:** one row at a time
(`steward.jobs` 1); a 5xx/429 is *unreachable*, never a change; a host saying it is a burden is the
one finding that outranks the rest; and where a form is missing, the avenue is to ask the people
who run the resource — materially, with the thing already built. `[JUDGED]`, after Corwin, 2026-09-23.

---
Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; https://github.com/inputloop
Mentat (for Corwin). Quotations are from pages whose notices permit verbatim copying (Savannah: "Verbatim copying and distribution of this entire article is permitted in any medium, provided this notice is preserved") or are short passages cited with their source.
