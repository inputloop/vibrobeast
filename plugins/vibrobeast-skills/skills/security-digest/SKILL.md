---
name: security-digest
description: >-
  Daily Linux security vulnerability and advisory digest for Ubuntu/Debian fleets. Use when generating a fresh security summary for your infrastructure — triggered by schedule (pair with the `schedule` skill to automate daily runs). Searches LWN, kernel.org, Ubuntu Security Notices, and Debian Security Advisories for CVEs and DSAs published in the last 24 hours, groups by severity, extracts actionable patches and reboots, and produces a punch list of urgent tasks. This is Corwin's own fleet-ops digest, not a generic vulnerability database query.
metadata:
  lineage: Haiku draft 2026-07-03 (FreshLocalGossip stowaway); adopted QA-8 2026-07-04
---

# Security Digest — Daily Vulnerability Summary for Ubuntu/Debian

This skill captures the discipline for keeping a Ubuntu/Debian fleet aware of security patches without noise. It runs autonomously on a schedule (pair with the `schedule` skill) and produces a structured, actionable summary of the last 24 hours' advisories.

## Operating Principles

### Report, never act
This skill *recommends*; it never executes. An autonomous run must not
run `apt`, trigger reboots, touch any host, or act on its own punch
list — applying patches to entrusted systems is the keeper's act (or a
separately-consented action through the consent gate). The digest's
whole authority is the quality of its report.

### Severity-first prioritization
Group findings by CVSS/severity tier (Critical, High, Medium, Low), not by package or source. Surface RCE and DoS vectors first because they demand immediate attention. Use formal severity ratings when available; infer conservatively if ambiguous.

### Patch availability is table stakes
Never surface a vulnerability without stating whether a fix is available. Unpatched findings go into a separate "No patch available" section with risk mitigation guidance instead of a punch list. The punch list is only for actionable patches.

### Autonomous execution discipline
This skill is written to run cold without session context. Every run must be self-contained: hardcode no UUIDs, no ephemeral links, no "see above." Search strategies, source URLs, and expected output formats are all explicit so a future run (days or weeks from now, in a fresh session) will work identically.

### Don't fetch what you didn't search for
The five sources (LWN, kernel.org, Ubuntu, Debian, CVE tracker) are the search surface. Do not web-fetch individual CVE detail pages unless the summary data is ambiguous. Avoid chasing every tangential link — focus on the advisory title, severity, affected versions, and patch status.

### Sources are ordered by trustworthiness, not recency
Search in order: LWN (fastest, mature analysis) → kernel.org (authoritative for kernel) → Ubuntu Security Notices (official) → Debian Security Advisories (official) → CVE tracker (fallback for detail). If multiple sources report the same CVE, don't duplicate — cite the most authoritative source.

## Method: Search → Parse → Summarize

**Step 1: Search the five sources** for advisories published in the last 24 hours.
- If today is Monday, include Friday's advisories (weekend accumulation).
- If no results from a source, note it briefly ("No LWN advisories today") and move on.

**Step 2: For each advisory**, extract:
- CVE ID(s) or DSA number (if no CVE, use the advisory ID)
- Affected package/component and versions
- Severity (Critical/High/Medium/Low)
- One-line description (what the vulnerability is, not the bug backstory)
- Patch status (available / pending / no patch expected)

**Step 3: Group by severity**, with RCE and DoS (code execution paths) at the top.

**Step 4: Call out kernel updates separately** — they often require reboots.

**Step 5: Produce a "Key actions" punch list** only for Critical/High vulnerabilities with patches available. Omit findings you can't act on today.

## Output Format

**One-line summary:**
> X advisories today — Y critical, Z high, W medium, V low.

**Advisories section** (grouped by severity):

```
**CRITICAL / HIGH**
- [CVE-XXXX-XXXXX or DSA-NNNN-N] Package name — brief description. Fix available: yes/no.

**MEDIUM / LOW**
- (same format)

**Kernel updates**
- (kernel-specific patches noted separately with version/reboot impact)
```

**Key Actions** (only if there are actionable patches for Critical/High):

```
**IMMEDIATE (next 24 hours):**
1. [CVE-XXX-XXX] Package: Rationale for urgency. Command: apt update && apt install <pkg>

**URGENT (24–48 hours):**
2. [Other High severity]

**ROUTINE (48–72 hours):**
3. [Medium or Low, for completeness]

**Punch list:**
- [ ] Action 1
- [ ] Action 2
- [ ] Schedule kernel reboot (if applicable)
```

If no Critical/High vulnerabilities with patches exist, close with: "No immediate action required; monitor for updates on [package list]."

## Notes for Autonomous Runs

This skill is designed to run via the `schedule` skill. Every run is independent:

- Do not assume context from previous runs. The "last 24 hours" boundary is always computed fresh (or "since last weekday" on Monday).
- Search the hardcoded source URLs directly; do not rely on cached results or a "security dashboard."
- If a search returns no results, that is *data* — note it and move on. Do not retry or second-guess.
- Keep the summary concise (under 500 words for typical days). Long days with many advisories may exceed this; that's OK — prioritization is more important than brevity.
- Punch-list commands are for the keeper to run; see "Report, never act."

When scheduling: set the cron expression so runs happen early morning (e.g., 6 AM America/Chicago) giving time to review and act before business hours. See the `schedule` skill for how to wire this up.

## Related Skills

- **schedule** — Use to automate daily runs of this digest. Pair them: create the task with `schedule`, point it at this skill, set a daily cron.
- **pmo** — If your fleet ops are tracked in Corwin's PMO, consider adding "patch [CVE-XXX]" as a TODO when this digest surfaces Critical/High findings.
- **mentat-skill** — Use to capture any patterns you notice across weeks of digests (e.g., "nginx has been patched 4 times this month, consider upgrade strategy").
- **consent-gate** — the boundary this skill reports up to: recommendations end where entrusted-system actions begin.


## How this skill can fail (falsifiers)

- **It acted.** fails if a run's transcript shows an `apt`, reboot or other host command executed; check: `grep -nE 'apt(-get)? (install|upgrade)|reboot|systemctl' RUN.jsonl` finds no tool-call line.
- **Patch status missing.** fails if an advisory line lacks its fix status; check: `grep -c '^- \[' DIGEST.md` equals `grep -c 'Fix available: \(yes\|no\)' DIGEST.md`.
- **Wrong window.** fails if a listed advisory was published before the 24-hour window (or before Friday, on a Monday); check: open two cited advisories and compare their dates to the run date.
- **The summary line disagrees.** fails if the one-line totals differ from the bullets listed per tier; check: count the bullets by tier against "X advisories today, Y critical ...".

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-03.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
