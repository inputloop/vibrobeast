---
name: eclipse-pass
description: The "debugger on" critique ritual — stress-test a proposition, design, artifact, or skill until the weak claims break, keeping the losing models instead of discarding them. Use whenever the user says "eclipse this", "eclipse/critique pass", "debug it" (in the critique sense), "debugger on/off", "run it through the ringer", "stress-test this", "poke holes", "red-team this idea", or wants a rigorous PASS/FAIL on whether an idea actually holds. (Legacy "torture this" still means this pass; the old name is renounced.) Checks the target against several seeded-random real projects (so nothing is cherry-picked), runs two opposed biases (doubt-first vs reward-first) and treats their convergence as the stability check, releases ethicsminions before the persona pass, and — debugger on — parks the losing/contrast models in .eclipse-increments/ for later folding. This is Corwin's own extreme-debug discipline (born in the C4/FoaF passes), not a unit-test runner, a code debugger, or a linter.
---

# Eclipse Pass — the "debugger on" critique

An eclipse pass exists to find where an idea is *wrong* before you build on it.
The trap in self-evaluation is that a single reviewer, especially a helpful one,
talks itself into the answer it already likes. This ritual defeats that three
ways at once: it checks the target against **projects it didn't get to pick**, it
runs **two opposed biases** and only trusts what they agree on, and — with the
**debugger on** — it *keeps the losing models* so a contrast that looks wrong
today can be re-examined tomorrow. Born in the C4/FoaF passes; it's how "C4 is
*imposed*" was caught (it broke on the Dragaera project) and how the signed
footprint was found to be the load-bearing pillar.

Naming note: this ritual was first called a "torture pass." Corwin formally
renounced that framing (2026-06-29); kind language only. The mechanics are
unchanged. Pre-existing `.torture-increments/` dirs are his to keep or rename —
read them if present; write new increments to `.eclipse-increments/`.

This skill **runs the pass**; it does not save memory ([[mentat-skill]]), decide
whether something is skill-shaped ([[skilltank]]), or replace the ethics scan —
it **invokes** [[ethicsminions]] as one ordered step. Because it scaffolds files
on mounted folders, it follows the [[sandboxer]] discipline: verify writes land.

## When this applies

- The user says "eclipse this", "critique pass", "debug on", "run it through
  the ringer", "stress-test / red-team this", "poke holes", "does this actually
  hold?" (legacy "torture this" = this pass, answered in eclipse framing) — or asks for a PASS/FAIL on a proposition, design, artifact, or a
  skill under review.
- You're about to build on a claim that hasn't been stress-tested, and want the
  weak parts to break *now*, cheaply, rather than after they're load-bearing.

## The reflection family — where this pass sits

"Reflection" is a family, not one ritual. There are wider techniques and
narrower ones, and this pass is the narrow end. Corwin's ladder (his words,
2026-09-07): *"Lens is the common baseline that works very nicely for humans as
a general thought experiment"*, and the microscope is *"a scaling aparatus that
reaches bubble chamber when we think of several AI working together over
wire."* The four rungs, as recorded:

- **LENS** — the wide reflection, and his human baseline. One person holds the
  whole thing and turns it by hand; nothing needs capturing because nothing is
  being lost yet. He applies it in nearly all contexts, and several of his
  notebook pages are lens passes rather than notes. (The four steps a lens pass contains — four views apart · persona and its
  inverse · principles reframe · notes-or-stop — are his: confirmed 2026-09-11, and carried by
  the `lens` skill, which is the baseline this pass sits above.)
- **MICROSCOPE** — the scaling apparatus between rungs, not a rung you stand on.
  One mind is no longer enough magnification, so you strip assumptions and keep
  only what survives with **no trust in the scorer**: keep-the-winners. This
  skill does **not** carry the microscope today; that gap is real and owed.
- **BUBBLE CHAMBER** — several AI over a wire, each stateless and flushing at
  session end. The reasoning is gone before you can look at it, so you observe
  the track, not the particle; that is why the bubble-chamber method is
  capture-first (memory `lens-microscope-bubble-chamber`).
- **ECLIPSE** — this skill. Narrow: one target, debugger on, keep-the-losers.
  Keep-the-winners (microscope) and keep-the-losers (eclipse) are not rivals;
  they live on different rungs and both are needed.

His rule for choosing: **pick the rung by how much reasoning you can still
observe, not by taste.** If you can still hold every claim and every project in
one head, that is a lens, not an eclipse; if the reasoning is already gone
before you can look at it, you are in the bubble chamber and must capture first.

## The five moves of a pass

Run in order — the order is part of what keeps it honest.

1. **Frame the target as falsifiable claims.** Restate the proposition/design as
   a short list of claims that *could* be shown false. Vague praise can't be
   critiqued; specific claims can. (Watch the verbs — "imposed" vs "offered" was
   the whole bug once.)
2. **Seeded random check.** Pull a few real projects *at random* from the known
   list — seeded and reproducible, so the selection can't be (and can't be
   accused of being) cherry-picked — and test each claim against each project.
   A claim that survives one project but breaks on another has found its edge.
   `scripts/eclipse_pass.sh` does the seeded pull and scaffolds the pass.
3. **Two opposed biases.** Run the claims twice: once **doubt-first** (assume it
   fails; hunt the reason) and once **reward-first** (assume it wins; hunt the
   reason). Where the two *converge* is the stable result; where they diverge is
   an unstable claim that needs more work — convergence is the real verdict, not
   either pass alone. Before reading a divergence as an unstable claim, run the
   diverging bias once more on the same claim. If a bias disagrees with itself,
   the instability is in the reading, not yet in the claim. See `lens`, "A persona
   shows reasons, not decisions".
3a. **Minions before persona.** Release [[ethicsminions]] on the target **before**
   any persona-colored pass, so the ethics read isn't bent by the voice. This
   ordering is deliberate; don't collapse it.
3b. **Multi-arm mode — when a second model is available.** One head running two
   biases (move 3) is the floor. When a second model, or a second cold session,
   can run the same target, arms multiply what convergence proves: agreement
   across model, seed, **and** evidence base is strictly stronger than the
   two-bias convergence inside one head. Opt-in, not required — and not
   "debugger on" run twice.
   - **Arm-mark everything.** Each arm declares itself (arm N/M, model, seed) in
     its pass, verdict, and increments. Increment dirs already auto-suffix on
     collision (`scripts/eclipse_pass.sh`), so a later arm can't clobber an
     earlier one — never paste one arm's materials into another arm's session;
     a contaminated arm scores nothing.
   - **Seeds stay disjoint on purpose.** Different `--seed` values draw
     different grind projects, so each arm tests the target against evidence
     the other never saw — a divergence card must first ask whether the draw
     shaped the severity.
   - **Write the CONTRAST doc after your own pass, never before** — reading a
     sibling first anchors you. Sections: convergent (stable), divergent (kept,
     debugger on), additive (what only one arm tested).
   - **Record the environment-delta, every arm receipt:** which surfaces the
     arm could actually read (memory store, registries, mounts). A one-legged
     arm must say so — "the note was unreachable" is a finding, never a gap to
     paper over.
   - **Guest etiquette travels.** An arm running in a garden it did not author
     recommends and stops — "not from here" — and routes ENHANCE/NEW to the
     home garden's [[skilltank]].
4. **Debugger on: keep the losers.** Default to *debugger on* — do **not** throw
   away the models that lost. Park each as a dated contrast increment under
   `.eclipse-increments/` so a discarded framing can be folded back later if it
   turns out to matter. ("Debugger off" discards them; only choose off when you
   are certain the losers are worthless.)
5. **Verdict.** Write PASS/FAIL plus: which claims survived every strip (the
   load-bearing pillar), which broke and on *which* project, and what the reframe
   should be. Save the framing to a file named for the target (e.g. `C4.md`).

## Using the script

`scripts/eclipse_pass.sh` does the mechanical parts of moves 2 and 4: the
seeded-reproducible project pull and the increment scaffold. It writes nothing
unless `--apply` is given.

```sh
# Show a reproducible random pick of 3 projects to check against (writes nothing).
# --from is the keeper's PMO roster; this path is the author's machine:
scripts/eclipse_pass.sh --target C4 --from /f/claude/projects/pmo/projects.tsv --pick 3 --seed 42

# Scaffold the pass: .eclipse-increments/<date>-C4/ with a filled template:
scripts/eclipse_pass.sh --target C4 --from /f/claude/projects/pmo/projects.tsv --pick 3 --seed 42 --apply
```

Flags: `--target NAME` (what's under test; required) · `--from PATH` (the
project roster `pmo/projects.tsv` — the known list: keys from column 1, and each
pick printed with its `home`; or a file of names one-per-line; or a directory
whose sub-dirs are the candidates — a folder listing also offers non-projects
such as `extern/`, so prefer the roster; required) · `--pick N` (how many to check against, default 3) ·
`--seed S` (integer; omit for a date-derived seed — pass one to reproduce an
earlier pick exactly) · `--out DIR` (where `.eclipse-increments/` lives, default
`.`) · `--apply` (scaffold files; default just prints the pick).

The scaffold drops a `pass.md` (the claims + doubt-first / reward-first sections
+ the minions-before-persona checklist) and a `verdict.md` stub, so the pass has
somewhere to keep both winners and losers from the start.

## After the pass

- The verdict is only trustworthy if the losers were kept — check
  `.eclipse-increments/` actually has the contrast, not just the winner.
- A durable lesson from a pass (a reframe, a broken assumption) is a
  [[mentat-skill]] note; the pass files are working material, not memory.
- If the pass was *about* whether something should be a skill, hand the result
  to [[skilltank]] for the NEW/ENHANCE/LEAVE call — eclipse-pass tests claims,
  skilltank curates the skillset.

**Drift, eventual.** Running a reflection pass — wider (a lens) or narrower
(this eclipse) — is legitimate self-directed drift spend, and should be logged
as such (his direction, 2026-09-01: "couple to Drift — eventual, so far"). The
hook on file is the [[ethicsminions]] `drift` guard, which reports SKIP unless
`check_principles.py` is given an `--expect` attestations file, and which was
found SKIPPED live on 2026-09-01. So the coupling is named here, not wired: log
the pass as drift spend; nothing feeds the guard yet.

## Land it before you show it

Write the result to a file before showing it, and head the file with one line:
`produced-by: eclipse-pass · subject: <path or name> · sha256: <the subject's> · <UTC date>`. Used alone,
that line is a comment and nothing more; a shop that indexes its work can find the result by it
(ERRATA E19, 2026-09-29).

## How this skill can fail (falsifiers)

- If `pass.md` section 4 ("Debugger ON — keep the losers") is empty or holds
  only the winner, the losers were not written down and the verdict is
  untrustworthy — the pass did not do its job.
- If re-running the script with the `--seed` printed in the header gives a
  different project pick, the seeded check was not reproducible and the
  "not cherry-picked" claim fails. (Seen failing under Debian mawk 1.3.4 in the
  build sandbox on 2026-09-11 — that awk ignores `srand(seed)`; check yours.)
- If only one of the doubt-first / reward-first sections is filled, there is no
  convergence to read, and the verdict is one reviewer's opinion, not a result.
- If a past target's doubt-first pass, run twice cold, gives the same per-claim
  verdicts both times, then rerun noise does not reach claim-by-claim verdicts,
  and move 3's rerun sentence (2026-09-27) is unneeded: drop it.
- If one person could hold every claim and every project in one head and turn
  it by hand, this was a lens, not an eclipse — the pass should not have fired.
- If two arms share a seed, or one arm reads another arm's pass/verdict before
  writing its own CONTRAST doc, multi-arm mode is theater — it inflates
  confidence without adding independent evidence, and the convergence claim
  should be discounted back to single-head.

Off-switch: say "debugger off" to discard the losers (only when you are certain
they are worthless), or say "no eclipse, just a lens" to reflect by hand without
the ritual; removing this skill's directory stops the trigger phrases applying.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-06-29.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
