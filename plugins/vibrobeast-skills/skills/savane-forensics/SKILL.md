---
name: savane-forensics
description: >-
  Use for forensic security review or breach-notification work on GNU Savane /
  Savannah, or when extending the svhck-forensics suite. Covers turning a
  vulnerability report into database-traceable IOC checks, diffing a restored
  backup against live data, verifying the deployed code tree, correlating access
  logs, reconciling Mailman lists, and sending templated user notifications ---
  with MySQL/MariaDB read-only safety, the Savane schema and role model, GNU
  packaging conventions, and the suite's coding standards.
---

# Savane / Savannah forensics

This skill captures how to do data-side forensic review and user notification
for GNU Savane (the software behind GNU and non-GNU Savannah), as built in the
`svhck-forensics` suite. It is a *method and conventions* guide; the runnable
tools live in the project repo, not in this skill.

## Operating principles

- **Read-only first.** Never mutate the data under review. Every check is a
  `SELECT`, run through a SELECT-only DB account, and the tools refuse to start
  unless `SHOW GRANTS` proves the account cannot write (parse each privilege
  token; reject INSERT/UPDATE/DELETE/CREATE/DROP/ALTER/.../`WITH GRANT OPTION`,
  and `ALL`). Make the account contract a *pure* `GRANT SELECT` --- so do NOT
  require `CREATE TEMPORARY TABLES`; inline any lookup table (e.g. a role map)
  as a derived `(SELECT ... UNION ALL SELECT ...)` subquery instead.
- **Live or dumps.** Support both: scan a `mysqldump` loaded into a throwaway
  scratch database, or the live database directly by name. Assume the operator
  may not be able to export dumps.
- **Leads, not verdicts.** A flagged row means "a human should look", not
  "this is malicious". Expect benign true matches; make checks tunable.
- **Hand off for offline execution.** Produce tools and evidence; do not run
  them against production yourself. Seal evidence dirs (SHA256SUMS + MANIFEST)
  for chain of custody.
- **Free software, GNU style.** GPLv3-or-later; follow the GNU coding
  standards, the GNU Maintainers manual, and GNU Emacs sources for shape and
  commentary. Put the FULL "more than one file" GPL notice from the GPL-howto
  in every source file (shell, SQL, config) --- a one-line "License GPLv3+."
  is not enough. Reference: https://www.gnu.org/licenses/gpl-howto.html.

## Method: report -> checks

1. Read the vulnerability report. For each finding ask: *does it leave a durable
   trace in the database?* Only those are in scope for data-side IOC checks.
   Code/runtime-only defects (reflected XSS, ReDoS, timing) go to code review
   and web/proxy log analysis instead --- record them, don't fake them.
2. Write one self-contained SQL scanner per traceable finding, named for the
   finding (`ioc-NN-short-name.sql`), each emitting TSV rows for review.
3. Add a **backup-vs-present diff**: per-table row-count deltas, deleted rows,
   and sensitive-column mutations. With MyISAM (no transaction log) this is the
   strongest tool for silent deletion/mutation.
4. Add a **code-tree verify**: sha256 the deployed tree vs a clean checkout of
   the same release; flag added scripts. Prefer the served-verbatim subtree
   (`frontend/php`); generated `*.in` templates won't byte-match.
5. Add **log correlation**: match request signatures, and join the IPs of
   flagged DB actions (`*_history.ip`) to their full web activity. Note Savane's
   `ip` is `varchar(15)` --- IPv4 only.
6. Add **Mailman reconciliation** (statedir vs `mail_group_list`) for the
   path-traversal finding.
7. **Notify** via a dataset-driven mailer that resolves each address from the
   live DB at send time (never write an address list to disk); default dry-run,
   spool with real `To:` headers, send with a resumable sent-log keyed by
   user_id and a rate limit. Templatize copy + headers with `{{TOKEN}}`s, and
   substitute in a single pass so a hostile field cannot re-expand a token.

## Savane schema + role facts (release 3.17)

- Site-admin project: `groups.unix_group_name = 'administration'`, group_id 101
  in stock; user 101 is its admin. Anonymous/system user_id = 100 (and 0).
- All trackers (`bugs`, `task`, `support`, `patch`, `cookbook`) reuse the same
  column names: item PK `bug_id`, history PK `bug_history_id`, plus `mod_by`
  and `ip` --- so cross-tracker SQL is uniform. `*_history` records who and
  from where: prime forensic signal.
- Roles: `user_group.admin_flags` (`''` member, `A` admin, `P` pending, `SQD`
  squad); per-tracker `*_flags` (1 technician, 2 both, 3 manager).
- `user.confirm_hash` = `time() ! item ! enc-hash` (sep `!`); leading epoch is
  creation time. `session` is IPv4 `ip_addr`; `user_lostpw.count` = reset count.
- Self-service writes `group_history 'User Requested Membership'` with
  `mod_by` = the requester, so drive any "admin op by non-admin" check from an
  explicit allow-list of admin field_names, never "any group_history row".

## Verification discipline

- Prove detection logic on synthetic positives AND negatives before trusting a
  check (a small SQLite harness with a registered REGEXP works when no MariaDB
  is handy). Ship fixtures + expected counts + a self-test runner.
- After writing/editing ANY file, GREP for the specific content you intended
  (functions, section headers, license blocks) --- a syntax check (`dash -n`)
  is NOT enough: a script that merely calls a now-missing function still parses,
  and silent truncation can drop critical code (it once removed the entire
  read-only guard, and `dash -n` stayed green).
- Before a release, run a COLD review (a fresh subagent reading the tree with no
  prior context) for safety/correctness/convention issues.

## Packaging & release (GNU)

- Run-in-place suite + a `Makefile` with `lint`, `check`, `install`,
  `uninstall`, `dist`, `clean`. `install` copies the tree under
  `$(prefix)/share/<pkg>` and writes thin `$(bindir)` wrappers that `exec` the
  real script by absolute path (so each tool still finds its `sql/`, `conf/`,
  `templates/`; a bare symlink would break `$0`-relative discovery). Honour
  `prefix`/`DESTDIR`.
- Ship `VERSION`, `NEWS`, `ChangeLog`, `AUTHORS`, `.gitignore`; give every tool
  a `--version`/`-V` that reads `VERSION`.
- This suite + skill could become a shareable **plugin** for the Savannah
  hackers once the method stabilizes and teammates are onboarding.

## How this skill can fail (falsifiers)

- **The read-only guard is gone.** fails if a tool starts on an account whose `SHOW GRANTS` has a write privilege or `ALL`; check: run it against a test account granted `INSERT` and want a refusal before any query.
- **A check never proven.** fails if an IOC scanner ships without a synthetic positive and negative with expected counts; check: the suite's self-test runner reports each `ioc-NN-*.sql` against its fixtures.
- **Truncation passed the syntax check.** fails if an edited file lost a function or block while `dash -n` stays clean; check: `grep -n` for the guard function and the licence block in every file you touched.
- **An address list on disk.** fails if a notification run writes email addresses anywhere but the spool; check: `grep -rlE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+' <workdir>` outside the spool lists nothing.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-09-23.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
