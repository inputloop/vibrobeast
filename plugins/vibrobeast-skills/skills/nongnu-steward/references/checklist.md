# checklist — tending a free software project's artifacts

*Derived from Savannah's submission checklist and reviewer notes (`sv-approved-quickly`,
`sv-requirements`, `sv-valid-notices`), GCS 7.3 (`gnu-standards-releases`) and the flagship habits
in `MODEL-steward.md` §3. Numbered to the model's E-rules. Use it as a tending list, not an
application form: nothing here assumes a host. A row's "check" is what a session runs or reads.*

| # | tended when | check | E |
|---|---|---|---|
| 1 | every nontrivial file (>10 lines; scripts, Makefiles, ChangeLogs, docs too) carries a copyright line and the recommended licence notice; binaries, images and PDFs covered by a README beside them | `sh scripts/ns1hd` → no `NO-*`, `GPL-ONLY`, `BINARY` rows; `SHORT-NOTICE` rows upgraded when touched | E3 E12 |
| 2 | `COPYING` holds the full plain-text licence (not a stub or a pointer); `COPYING.LESSER` beside it for LGPL; the FDL is a section of each manual | `ns1hd` root rows (`COPYING-MISSING`, `COPYING-SHORT`); the manual build output contains the FDL | E4 |
| 3 | every GNU licence notice says "or (at your option) any later version" | `ns1hd` reports no `GPL-ONLY` | E2 |
| 4 | every dependency is free, GPLv3-compatible, and has a URL to its licence page in `LICENSE-DEPS.tsv` | `sh scripts/ns2ld --check` exits 0 | E5 E15 |
| 5 | vendored copies of other projects' code sit in their own directory with a README saying they are not part of this program, and keep their own notices | `ls` the tree; `ns2ld` rows for them | E15 |
| 6 | the program does its whole job on a free operating system with free software; nonfree platforms are secondary and never favoured; no nonfree download or install step | read README, build scripts, CI files | E1 E16 |
| 7 | no file needs nonfree software to create or edit; docs in Texinfo/LaTeX/ODT/HTML-with-source, never Word/RTF | `find . -iname '*.doc*' -o -iname '*.rtf' -o -iname '*.swf'` | E6 |
| 8 | README names the package, its version (or where it is), what it does, points at INSTALL and at the copying conditions, explains odd top-level files; contact information somewhere | read README | E13 |
| 9 | the words: "free software", "GNU/Linux"; no "Open" in the name, no "GNU" unless dubbed; a descriptive, findable name | `grep -rniw 'open source' README* doc/` | E7 |
| 10 | NEWS carries every user-visible change, first sentence on one line; ChangeLog generated from commit messages or kept with notices at its end | read NEWS; `tail ChangeLog` | flagship |
| 11 | copyright years are current across the tree, updated once a year by a script (`update-copyright`, `copyright-update`), old years kept | `grep -rL "$(date +%Y)"` over files with a Copyright line | E12 flagship |
| 12 | trivial files carry a reminder comment so they cannot grow past the line unnoticed | spot-check | flagship |
| 13 | a release is `name-version.tar.gz` unpacking into `name-version`, world-readable, no symlinks, generated files up to date, `texinfo.tex` shipped; uploaded with a detached `gpg -b` signature | `tar tzf`; `find . -type l` | E13 E10 |
| 14 | contributions over about a dozen lines have their legal basis recorded: assignment, or DCO `Signed-off-by`, or a `Copyright-paperwork-exempt: yes` mark for tiny ones; attribution in git (`Author`, `Co-authored-by`) | `git log --format=%b \| grep -c Signed-off-by` | flagship |
| 15 | the employer/school disclaimer question has been asked once, before first release | read CONTRIBUTING / AUTHORS | E17 |
| 16 | an interactive program shows its copyright and copying notice at startup; an AGPL network program offers its source | run `prog --version` | E17 |
| 17 | no advertising; support pointers only for this project | read the web pages | E8 |
| 18 | canon this skill rests on has not moved | `sh scripts/ns2cn --check` | canon |

A row a project deliberately does not meet is written down as such (a line in README or a note the
memory keeps), so the same question is not re-asked next session.

---
Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; https://github.com/inputloop
Mentat (for Corwin).
