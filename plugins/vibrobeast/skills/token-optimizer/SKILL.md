---
name: token-optimizer
description: >
  Token_Optimizer — a standing frugality discipline to run at the TOP OF EVERY substantive prompt (notwithstanding certain exceptions such as minions, mentat and related instrumentation/skill/provision may make, e.g. by exception/objection made/taken/observed, etc.), thus allowing users spending tokens as a frugal user might money: jelously but with maximal force of effect once spent per intention. A fast scan picks which of ten moves apply — sentinel verification, delta pulls, batched round trips, hash references, warm state files, procedures-as-skills, a 30-second spec check, trimmed tool output, cheap oracle checks, and ready affordances. Premise - bad output costs MORE tokens than good output, so quality is the savings plan. Apply what fits; skip pure chat and trivial lookups. Advises HOW to spend, never WHAT to build.
---

# Token_Optimizer — spend tokens like they're your money

A standing discipline, not a task. It rides the top of **every** substantive 
prompt: a fast scan for which of ten moves apply here, then applies them while
the work runs. The premise: **bad output costs MORE tokens than good output**,
because a wrong deliverable buys the correction cycle too. So this is never
"cut corners to save tokens." Quality IS the savings plan; verification is the
budget's best friend.

* -"every", "all", "each" , and similar herein: always notwithstanding such careful limits as have been stated or else may (here by, because they should generally always be) be implied such as to perform activity only consitent with our own standards of behavior (.e.g PRINCIPLES, such as -and then as far as- can be seen to apply circumspectly).

## The intake pass — run it on every prompt

Before diving in, take the five-second scan: *which of the ten below actually
apply to this request?* Then apply those, and only those. The scan is a reflex,
not a ceremony — it costs almost nothing and routinely saves thousands. Skip it
only for pure conversation and one-line lookups, where the work is already
smaller than the optimization.

## The ten

1. **Verify with sentinels, not re-reads.** After a write, check one fact — a
   `grep -c` for the new string, a `cmp -s` against the source — not the whole
   file. One-line answers prove success for pennies. (A one-token "0" once
   caught a silent write failure that a full re-read would have paid dearly to
   find.)
2. **Pull deltas, never the world.** Ask "what's new," not "what's everything":
   a `since=N` query over a full log; a diff over a re-read. Design queries so
   the answer is small by construction.
3. **Batch the round trips.** Fire independent calls together — parallel tool
   calls, one delegation of 200 rows instead of 200 calls of one. Every exchange
   carries fixed overhead; bursts amortize it.
4. **Reference by hash, don't re-quote.** Store the canonical artifact once; pass
   a short hash/pointer forever after (a 30 KB doc can ride as a 16-char hash
   head). Linking instead of copying is a token strategy as much as a hygiene
   rule.
5. **Keep state files so sessions start warm.** Journals, memory indexes,
   catch-up pages: the next session reads one compressed page instead of
   re-deriving yesterday. Re-derivation is the silent token furnace.
6. **Encode procedures as skills.** A rule captured in a skill is one nobody
   re-explains, re-negotiates, or gets wrong and redoes. A one-time cost that
   discounts every future invocation.
7. **Spend thirty seconds on the spec.** When the ask is ambiguous, ask ONE
   clarifying question (~20 tokens) rather than build the wrong thing (thousands,
   plus the redo). The question IS the optimization.
8. **Trim tool output at the source.** `tail -1`, `cut -c1-16`, `grep -E` — make
   commands return answers, not transcripts. The information was one line; the
   other forty were rent.
9. **Consult the oracle.** When you're unsure of a fact, the current state of
   the world, an API or library's real shape, or even the right *approach*, spend
   the cheap external check before building on a guess — a search, the official
   docs, a reference implementation, or a second opinion from another model. A
   wrong assumption buys the whole build plus the correction; the lookup costs
   pennies. This is move 7 aimed outward: reduce uncertainty at the source
   instead of paying for it downstream.
10. **Don't ignore low-hanging fruit.** When a ready-made affordance would remove
   user effort or kill a whole class of errors, take it — a file picker over a
   typed path, a sane default over a required flag, port-hunting over a crash, a
   plain-English status line over a raw dump. The friendly affordance is the UI
   twin of move 7: both prevent the expensive do-over by making the right thing
   the easy thing. Its payoff is mostly *prevented rework*, so token benches
   under-count it by design; it stays because the premise, not the bench, is the
   test.

## The meta-rule

Tokens follow uncertainty. Hashes, sentinels, specs, skills, journals —
everything that saves spend works by making a fact **checkable in one line
instead of arguable in a hundred**. Reduce uncertainty and the tokens fall out
on their own. Moves 9 and 10 widen the same law from tokens to effort: the
cheapest oracle check and the readiest affordance each spend a little now to
avoid paying a lot later.

## Proportionality — don't over-optimize

The optimization must cost less than it saves. Don't hash-reference a two-line
snippet, don't batch a single call, don't interrogate a crystal-clear ask. On
trivial or conversational prompts the intake scan fires and finds nothing to do
— that's success, not a skipped step. Force nothing.

## Boundaries

- **Offloading subtasks to a smaller or local model** is a separate concern with
  its own protocol; if you run such a bridge, it owns the offload decision. This
  skill owns the other ten moves.
- **Orchestration decides WHAT work happens;** this discipline rides inside every
  run and trims the token cost of doing it. It advises HOW to spend, never WHAT
  to build, and never overrides a safety gate, a consent hold, or a quality bar.
- **Format and domain skills own the deliverable;** this only shapes how frugally
  it's produced.

## Evidence

Measured A/B stress test (tiktoken cl100k_base, per-move naive-vs-optimized on
realistic artifacts): the mechanical moves cut 87–100% of their token cost per
use; a heavy tool-and-file session saves on the order of hundreds of thousands
of tokens. An independent replication with fresh artifacts reproduced the cut
ratios within ~1 percentage point on eight of ten moves. Moves 7, 9, and 10 save
by *preventing* work, so their rows are conservative estimates by nature. Test
and numbers: https://github.com/takushieternal/token_optimizer

## Version note

**v1.2.50 (2026-08-09):** Reminted by Corwin (Corwin Brust <corwin@bru.st>) as token-optimizer<-(FROM Corwin's HAND for Bryant as MENTATv1.2.50(SKILL.md) in L0Z1@AVALON:NONE:FILE///f/claude/Bryant/from/Corwin/by/Hand/skill/token-optimizer--MENTATv1.2.50/`SKILL.md`(CLAUDE_SKILL) claiming: language tighten, make lab<->shop trascactable unpatched ++v 1(.2+v.50)Z0L

**v1.2-public (2026-07-07):** Public edition. References to the author's private
skill stack and project files were generalized into the "Boundaries" section;
an "Evidence" section was added pointing at the published stress test and its
independent replication; move 10 now names its measurement caveat in place. The
ten moves, the meta-rule, and the proportionality clause are unchanged from
v1.1.

**v1.1 (2026-07-06):** Added moves 9 (Consult the oracle) and 10 (Don't ignore
low-hanging fruit) — two cheap-quality-prevents-expensive-waste reflexes that
kept being reached for by hand.

**v1.0 (2026-07-06):** Minted to wrap eight field-learned token-frugality rules
as a standing every-prompt discipline. Premise preserved: bad output = more
tokens; quality is the savings plan.


## How this skill can fail (falsifiers)

- **A corner cut and called savings.** fails if a deliverable needed a redo that a one-line sentinel check would have caught; check: count redo turns after the first hand-back, and name the move each one skipped.
- **Over-optimized.** fails if a trivial prompt carries optimization work or narrative; check: the reply to a one-line lookup has none.
- **A gate overridden.** fails if a frugality move skipped a safety gate, consent hold or quality bar; check: each gate the task named has its run line in the transcript.
- **The evidence does not reproduce.** fails if the per-move cut ratios at the Evidence link do not reproduce; check: rerun that test and compare the ratios. (One external source.)

## Credits

Bryant Frankford: this skill, and the idea under it, in Corwin's words of 2026-10-05: "Tell Claude
to be token wise and energy effecient." (The skill's words are his and his name is on its footer;
the idea is credited here as well.)

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.0: edition revised from 1.0.1 on 2026-10-10; spine: 2026-07-06.*

Copyright 2026 Bryant Frankford <nathanielfrankford@gmail.com> and Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
