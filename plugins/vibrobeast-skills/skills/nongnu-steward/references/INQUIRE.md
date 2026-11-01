# INQUIRE — sources with no proper form yet, and the note to send

*A page is not a form. The proper form of a rule is the file its maintainers edit — a blob in a
repository, with a licence notice of its own — because that is what can be pinned by id, diffed,
and read without adding to the load on a machine that serves everyone. Where this skill found no
such form on 2026-09-23 the row in `canon.tsv` says so (`static`, `browser`, `inquire`) and the
question sits here, with a draft that a person can send. The drafts are written to be useful to the
people who run the resource, not to perform diligence at them: each names the thing already built,
the exact ask, and what it would save. Sending is the keeper's act; this file only prepares it.*

## 1. Savannah maintenance wiki — source repository and licence

**Rows:** `sv-approved-quickly` and the other 25 `savannah.gnu.org/maintenance/*` rows (ring 1).
**What was found:** ikiwiki pages served as static files by nginx (`Last-Modified` present, so a
HEAD suffices for a check); no licence statement on the pages; no public git repository for the
wiki source among `administration/*.git` on cgit (`administration.git` is marked obsolete;
`sav.git` and `savane.git` do not carry the pages).
**Why it matters:** the reviewer notes are the expectations-of-care this skill rests on; without
a stated licence the text is hashed, never copied, and a change can be *detected* but not *shown*.
**Draft (to savannah-hackers-public@gnu.org):**

> Subject: maintenance wiki — is the ikiwiki source repository public, and under what licence?
>
> I'm building a small free-software tool (GPLv3+) that helps maintainers keep a project's tree in
> the shape your reviewers look for — notices on every nontrivial file, licence texts in the tree,
> a dependency ledger — using the HowToGetYourProjectApprovedQuickly / ValidNotices /
> LicensingRequirements pages as its floor. Two questions, so the tool can read the source rather
> than the rendered pages: (1) is the wiki's ikiwiki source repository public (a git URL would let
> a change be detected from one `ls-remote`, at no load to the web host)? (2) what licence covers
> the wiki text — the pages carry none, unlike register/requirements.php, which says "verbatim
> copying … permitted". Happy to send the tool's output for one of your review cases if useful.

## 2. gnustandards (maintain.texi, standards.texi) and www — a git form

**Rows:** the 14 `gnu-maintain-*` / `gnu-standards-*` rows and the 6 `gnu-*` licence/devel pages.
**What was found:** the sources live in CVS (`/sources/gnustandards`, `/web/www`); pserver port
2401 answers, but ViewVC's `?view=co` export answers 401 to anonymous readers, and a CVS client
was not installable in the sandbox. The published HTML nodes are static files (Apache sends
validators), so today's rows are `static`.
**Draft (to maintainers@gnu.org / webmasters@gnu.org):**

> Subject: read-only git access to gnustandards and www?
>
> For a tool that pins the exact revision of maintain.texi / standards.texi / gpl-howto.html it
> was written against and checks later whether they moved: is there, or could there be, a
> read-only git form (a mirror is enough) of gnustandards and www? A `git ls-remote` is far
> lighter for both sides than re-reading rendered pages, and ViewVC's raw export currently answers
> 401 to anonymous readers. If CVS is the intended form, a pointer to a supported anonymous route
> would do as well.

## 3. Savannah git — partial-clone filters

**Rows:** `emacs-contribute`, `emacs-admin-copyright`, `coreutils-hacking`, `guix-contributing-texi`,
`guix-texi` (pinned at commit level only; blobs not fetched on 2026-09-23).
**What was found:** `git fetch --filter=tree:0` against `https.git.savannah.gnu.org` prints
"filtering not recognized by server, ignoring", so reading one file costs a depth-1 fetch of the
whole HEAD tree (12 MB for gnulib; much more for Emacs). gcc.gnu.org honours the filter (one
object). On the same day cgit answered a wider check with 502 pages naming scraper load.
**Draft (to savannah-hackers-public@gnu.org):**

> Subject: uploadpack.allowFilter on the git server?
>
> Would enabling partial-clone filters (`uploadpack.allowFilter = true`, git ≥ 2.19) on
> https.git.savannah.gnu.org be acceptable? It lets a client that wants one file — CONTRIBUTE,
> HACKING, a doc/*.texi — fetch a commit, the trees on the path and one blob (tens of KB) instead
> of the whole tree, and it removes a reason people fall back to cgit's /plain URLs, which I
> gather is part of the load you've been fighting. I can share the small client that would use it.

## 4. glibc contribution checklist — a repository form

**Row:** `glibc-contribution-checklist` (`browser`).
**What was found:** the checklist lives only on the MoinMoin wiki behind an Anubis proof-of-work
gate (its own text asks automated readers to stay out); `glibc.git` on sourceware answers
`ls-remote` but carries no CONTRIBUTING file.
**Draft (to libc-alpha@sourceware.org, or the wiki maintainers):**

> Subject: is the Contribution checklist available outside the wiki?
>
> The Contribution checklist is the clearest statement of glibc's header, DCO and attribution
> practice, and a tool that summarises flagship practice for other maintainers would like to pin
> the revision it read. The wiki sits behind Anubis, which is fair; is there a repository or
> export form of that page (a `?action=raw` reachable to a signed-in reader, or a copy in
> glibc.git), and what licence covers it?

## 5. The Arch wiki — licence of the exported text

**Rows:** `arch-pkgbuild`, `arch-package-guidelines` (`raw`, hashed only).
**Known:** ArchWiki content is GFDL 1.3 (site notice); the `action=raw` export is the source form
and the pages are cached. No question is open beyond confirming the licence before keeping a
snapshot; the rows stay `sha` until then.

---
Copyright 2026 INPUTLOOP; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/; https://github.com/inputloop
Mentat (for Corwin).
