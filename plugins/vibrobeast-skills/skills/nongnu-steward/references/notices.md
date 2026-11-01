# notices — the texts, verbatim from their sources

*These are the forms Savannah's reviewers ask for by name ("Please use the exact form of the license
notices recommended in that article" — ValidNotices). `sh scripts/ns1hd --suggest FILE` prints the
combined header for a file's comment syntax; this page is the source it draws on. Sources:
`gnu-gpl-howto`, `gnu-maintain-license-notices-code`, `gnu-maintain-license-notices-other`,
`gnu-maintain-license-notices-docs`, `sv-valid-notices`, `sv-dual-licensing` in `canon.tsv`.*

## The copyright line

    Copyright (C) 2024, 2025, 2026 Jane Hacker <jane@example.org>

- "Copyright" always in English. `(C)` optional; © where the character set allows. Every year with
  nontrivial changes; never delete an old year. A range `2024-2026` is allowed only if every year in
  it counts *and* the README says: "For any copyright year range specified as YYYY-ZZZZ in this
  package note that the range specifies every single year in that closed interval."
- Several holders: a line each. A file copied from another project keeps that project's line.

## GPL — a program of more than one file (the recommended form)

    This file is part of NAME.

    NAME is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    NAME is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with NAME.  If not, see <https://www.gnu.org/licenses/>.

## GPL — a one-file program

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

- **LGPL:** insert "Lesser" before "General" in all three places; ship `COPYING.LESSER` beside
  `COPYING`. **AGPL:** insert "Affero" in all three places; `COPYING` holds the AGPL text; the
  program must offer its source to network users (section 13). **Version 2 or later:** replace the
  first "3" with "2".

## JavaScript served to a browser (LibreJS), the combined form

A script a browser runs is read by two rule sets: LibreJS (GNU's browser add-on, which runs only
scripts it can see are free) and a reviewer reading the notice. Each was right alone and they
disagreed until both were satisfied (theseus, 2026-10-18: a label reading only "GPL-3.0" was read
here as GPL-only). The combined form: LibreJS's label on the first line, the licence's magnet link
from LibreJS's table and, as the human-readable name, the SPDX id (so the or-later is said there
too); then the notice above, with "either version 3 of the License, or (at your option) any later
version"; then the SPDX line; and the end label as the file's last line.

    // @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-3.0-or-later
    /*
     * NAME is free software: ... either version 3 of the License, or
     * (at your option) any later version.  ...
     * SPDX-License-Identifier: GPL-3.0-or-later
     */
    ... the code ...
    // @license-end

Magnet links (LibreJS's table, https://www.gnu.org/software/librejs/manual/html_node/Setting-Your-JavaScript-Free.html):
GPL-3.0 `1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt`, GPL-2.0
`cf05388f2679ee054f2beb29a391d25f4e673ac3&dn=gpl-2.0.txt`, LGPL-3.0
`0ef1b8170b3b615170ff270def6427c317705f85&dn=lgpl-3.0.txt`, LGPL-2.1
`5de60da917303dbfad4f93fb1b985ced5a89eac2&dn=lgpl-2.1.txt`, AGPL-3.0
`0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt` (each after `magnet:?xt=urn:btih:`).
`ns1hd --suggest FILE.js` prints the label and the notice, and says on stderr to end the file with
`// @license-end`. A page that builds its scripts (theseus's `argo/ui/compose.py`) writes the same
form at build time, so every script it serves carries it.

## The SPDX line (beside, never instead of, the notice)

    SPDX-License-Identifier: GPL-3.0-or-later

Read by Arch (`license=`), REUSE, Guix packagers and most licence scanners. On its own it is a
`SHORT-NOTICE` under this skill's audit: accepted by reviewers with a note, not the recommended
form.

## All-permissive — for README, INSTALL, small supporting files, short manuals under 300 lines

    Copying and distribution of this file, with or without modification,
    are permitted in any medium without royalty provided the copyright
    notice and this notice are preserved.  This file is offered as-is,
    without any warranty.

## Public domain — a file placed there

Instead of a copyright and licence notice, a note saying it is in the public domain, listing the
authors and anything else relevant. CC0 is for data, not for program code; if used, ship its legal
text as `COPYING.CC0`.

## Small licences (Expat / X11 / Modified BSD)

Do not write a notice: include the whole licence text at the top of every file (it is short), and
a copy in the tree.

## Manuals — the GNU FDL notice, after the copyright line(s)

    Permission is granted to copy, distribute and/or modify this document
    under the terms of the GNU Free Documentation License, Version 1.3 or
    any later version published by the Free Software Foundation; with no
    Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.
    A copy of the license is included in the section entitled "GNU Free
    Documentation License".

The FDL itself goes in as a section of the manual (a `fdl.texi` from gnulib); every end-format
(PDF, HTML, Info) must print the whole licence and a copyright line. Each *source* file of the
manual carries the copyright line and a short notice pointing at the section (fdl-howto).

## Binary and format-bound files

A `README` in the same directory: "Copyright (C) YEAR HOLDER. The images in this directory are
released under the GNU General Public License, version 3 or (at your option) any later version." —
and be clear which files it covers.

## Dual licensing (example from Savannah)

    You may copy, modify, and redistribute this file under the terms
    of the GNU General Public License version 2 (or, at your option,
    any later version), or the Eclipse Public License version 1.0.
    [standard GPL notice]
    [standard EPL notice]

## ChangeLog files

Notices go at the **end**: new material is added at the beginning, the end stays the end.

## Trivial files (10 lines or fewer)

No notice needed. Emacs's habit is worth copying: a reminder comment such as
`# add a license notice if this grows past 10 lines`, so the file cannot cross the line unnoticed.

---
Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; https://github.com/inputloop
Mentat (for Corwin). The notice texts above are the FSF's own recommended forms, reproduced as they are meant to be — copied into other people's files.
