---
name: drawer-vs-door
description: >
  Decide WHETHER an artifact should carry a signature at all, and stop the recurring re-sign ask.
  Three dispositions — REMOVE (drawer: no named reader, churn expected), RE-SIGN (door: a named
  reader relies, or the signature means assent to content), FREEZE (archived: the BAD sig IS the
  record). The gate that ends the treadmill: before proposing ANY signing work, NAME THE READER —
  no named reader, no ask, no exception. Use when a `.asc` reads BAD, when "re-sign owed" is about
  to be written, on "should I sign this", "sign-queue", "the signature went stale", "do we still
  need this .asc", when a batch of drawer signatures generates repeated asks, or before adding a
  signature to anything. Also owns the standing SIGNING SILENCE default and the rule that
  keep-and-ignore (tolerating a BAD sig) is forbidden. NOT signing-model (what "signed" MEANS,
  clearsign vs detached), NOT shelf-check (when to run the gate), NOT verify-say (the wording),
  NOT skill-sign or release-runbook (per-skill and release mechanics).
metadata:
  origin: hand-authored 2026-09-14, keeper-directed ("install whatever you need to to make sure we
    do not hit this again"). NOT polygram-synthesized from memory tags — the usual skills/ path is
    memory → SkillTank → skill-creator → gate → advice → synth; this one skipped synth because the
    rule came from a keeper ruling, not from an accreted tag.
  occasion: a survey found 56 signatures in `c4/bin`, 44 sharing one batch timestamp
    (2026-08-08T14:10), each generating a re-sign ask on every edit and paying no reader.
  advice_note: advice/2026-09-14-drawer-vs-door-mint.md
  unsigned_by_design: a skill earns its signature at mint/dist where an installer relies on it.
    The drawer stays quiet. Corwin's pen, at the door.
---

# drawer-vs-door — whether to sign at all, and why the ask keeps coming back

`signing-model` says **how** to sign and what "signed" means. `shelf-check` says **when** to verify.
This skill says **whether the artifact should carry a signature at all** — and it exists because the
wrong answer produces a *recurring* cost: a signature with no reader generates a re-sign ask on every
edit, forever, and pays nobody.

## The gate — this is the whole skill

**Before proposing any signing work, name the reader. Out loud, specifically.**

> Who relies on this signature, and across what boundary?

- **A name comes out** → it is at the door. Signing is warranted. Proceed.
- **No name comes out** → it is in the drawer. **Do not ask. Do not queue it. Do not mention it.**

There is no third answer and no "well, someone might someday." *Someday* is the drawer. A signature
bought for a hypothetical reader is paid for by a real person, repeatedly, in attention.

The keeper's own rule, which this operationalizes: *"sign at the door, not in the drawer — only where
a named reader relies on it (a human reading your proud name, or a comrade verifying your bytes
across a boundary). Everywhere else, unsigned is the honest default."*

## The three dispositions

Most surveys offer two, and the missing third is roughly half of any real population.

| | when | why |
|---|---|---|
| **REMOVE** | drawer artifact, no named reader, churn expected | the `.asc` is standing debt with no beneficiary. Deleting it makes the absence **honest** |
| **RE-SIGN** | a named reader relies across a boundary, **or** the signature means **assent to content** (canon, principles, a recorded GO, published prose) | here the per-change cost buys something real |
| **FREEZE** | archived / retired copy | its `.asc` is a **historical record**. Re-signing falsifies history; removing destroys a receipt. A BAD signature on an archived file is the archive doing its job |

**Assent is a real reader.** A signature on a values document, a canon file, or a recorded decision is
an accountability ACK — the reader is whoever later asks "did he actually agree to this?" That is a
name. Do not mistake canon for drawer just because it never leaves the machine.

## The option to reject: keep-and-ignore

Leaving a BAD signature in place and teaching the instrument not to raise on it **softens a defined
guard** — and a softened guard is worse than an absent one, because it still *looks* like assurance to
the next reader. Guard false-positives are a small price; a guard taught to lie is not.

**If you will not maintain it, remove it.** Those are the only two honest options for a broken
signature outside an archive.

## Why the cost is recurring, and how it goes to zero

A signed artifact's `.asc` reads BAD the moment its content changes. So **the re-sign cadence exactly
equals the artifact's own churn.** For a tool still being shaped, churn is the point — which makes the
signature a subscription to interruptions, billed against the very work that improves the tool.

- Drawer signature: **one re-sign per edit, forever, paying nobody.**
- Removal: **once.**

Removing does **not** block shipping. A door gate that requires a signature (a sig-gated lifter, a
release script) needs the signature *at that moment* — which is sign-at-the-door, exactly as designed.
Sign when it stabilizes and ships, not while it churns.

**Measured, so the cadence is not feared in the abstract:** a door-class re-sign cost exactly one
command — `sign.sh verify FILE || sign.sh detach FILE` — observed 2026-09-14 on a canon file.
**The cadence was never the burden. Unearned signatures were.**

**Watch for the batch.** The tell that a drawer has been over-signed is a cohort of `.asc` files
sharing one timestamp — a single mass ceremony whose interest is still being paid months later. Group
by signature time; a batch is a decision that was made once and should be revisited once.

## SIGNING SILENCE — the standing default

Default is silence: **land it, archive it, queue it, say nothing.** Speak only when

1. you are **at the door** — a downstream reader is about to rely on the artifact, or
2. a **missing signature is blocking work the keeper asked for right now**.

One line, carrying its own reason. If you cannot say in one line why *he* would want to know, you do
not say it. A signature is his ceremony and his pen — guide toward it, never perform it, and never
manufacture an occasion for it.

**Retiring a stale ledger row is not signing narration.** If a queue still carries "re-sign X" and X
now verifies — or X has been removed as drawer — say so once. That is closing a false open item, not
asking for a signature. A satisfied obligation left standing in a ledger is its own bug.

## Removal is deletion

Destroying data takes two keys and a receipt **before** the burn.

- Produce the **list first** — full paths, one disposition each, with the reason. The list *is* the
  receipt.
- **Do not supply a paste-ready `rm`.** A deletion loop written by an assistant, over paths an
  assistant classified, is the shape of an accident. The keeper writes the loop, or asks for a
  run-card with the gate inside the card.
- Never remove anything under an archive path. See FREEZE.

## Before surveying, check the instrument

A signature survey that cannot see failure proves nothing when it reports success. Two legs:

1. **Is the pinned key actually in the ring?** An empty keyring makes *every* signature read BAD —
   which looks like a spectacular finding instead of a blind instrument.
2. **Can a corrupted body be made to read BAD?** If the verifier cannot go red, its green is decoration.

Either leg failing is a panel fault: report **no verdicts at all** rather than anything as clean.

Two distinctions a naive survey gets wrong, both of which slander good signatures:

- **UNKNOWN-KEY is not BAD.** A valid signature by a signer outside your ring is a *good* signature you
  cannot check. Keep the classes apart.
- **A manifest signature is not an orphan.** Per-skill and per-bundle signing covers a manifest of many
  files, not a same-named body; a byte-verifier sees "orphan" and is wrong. That is furniture.

Also state the bound: body-newer-than-`.asc` is ordinary edit-after-sign, but **mtime-preserving
archival flattens body and signature to the same second**, destroying the evidence that would separate
edit-after-sign from anything else. Say "undiagnosed" rather than guessing.

## How this skill fails (falsifiers)

- **It fired on mechanics.** If the question is clearsign-vs-detached, or what "signed" means, that is
  `signing-model`. If it is when to run a verification gate, that is `shelf-check`. If it is how to
  word a verdict, that is `verify-say`.
- **A reader was named lazily.** "Future me" and "someone auditing later" are not names unless a real
  boundary is crossed. If the named reader cannot be described as a person or a gate, the gate failed
  open and a drawer artifact just got signed.
- **It was used to talk the keeper out of a signature he wants.** This skill removes *unearned*
  obligations; it never overrides an explicit request. "Sign this" ends the analysis.
- **Off-switch:** "skip the disposition check", or an explicit instruction to sign a named artifact.

## Interlocks

`signing-model` (how, and what the word means) · `shelf-check` (when the gate runs) · `verify-say`
(how to word a verdict without outrunning the check) · `skill-sign` (per-skill manifests) ·
`release-runbook` (the ship boundary) · `consent-gate` (removal as a consent-bearing act) ·
`run-card` (the form a gated deletion takes).

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-08-08.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
