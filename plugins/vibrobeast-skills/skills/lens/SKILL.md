---
name: lens
description: The LENS — the wide reflection discipline, one human's thought experiment, run before a deliverable leaves your hands. Hold four views apart (yours; the one you ascribe the other party; their influence over yours; yours over theirs), pass the persona and its inverse, restate each point from principles, then write it down or stop and make arrangements. Use whenever you are about to hand back a model, a card, a review, a plan, a skill edit, or any piece another person or agent will act on; when asked to "run a lens", "lens this", "four views", "hold the views apart", "persona and inverse", "reframe from principles", "weigh two people's views"; and inside any other skill that composes nothing and hands something back. It is the baseline of a family of three (LENS · MICROSCOPE · BUBBLE CHAMBER) and the sibling of eclipse-pass (the narrow, keep-the-losers critique). Portable — a SKILL.md alone, dropped into any agent's web UI, is enough to run it.
---

# lens — the wide reflection, run by hand

The LENS is a thought experiment one person can hold whole and turn by hand. Corwin, 2026-09-07:
*"Lens is the common baseline that works very nicely for humans as a general thought experiment."*
The four steps below are my reading of his 2026-09-01 LENS, confirmed by him
2026-09-11 (*"stand-alone lens is fine; nothing wrong with the four steps"*). Run it before a
deliverable leaves your hands; run it in any skill that hands something back and does not merely
compose other skills.

## The four steps

1. **Hold four views apart.** Write each as its own line, never blended:
   (a) *my own view* of the thing;
   (b) *the view I ascribe the other party* — the keeper, the reader, the colleague — drawn out
   explicitly, as a node you can point at;
   (c) *their influence over mine* — what in (a) is there because of (b);
   (d) *my influence over theirs* — what in (b) is there because of me.
   Each party shapes the other's domain. (c) and (d) are where blind agreement hides: if (a) and (b)
   already agree and you cannot say why, you have alignment, not a reading.
2. **Persona, then its inverse.** At the deliverable, ask how the available persona (the specific
   one wearing this work, or the general voice of the shop) would put it — then ask how its
   *inverse* would. If both readings land the same point, the point is rounded; if the inverse
   finds something the persona could not, write that down as a finding, not a mood.
3. **Reframe each noticed point from principles.** For every point worth keeping, restate it in
   the order the shop decides by: universalism and egalitarianism first, then the four freedoms,
   then the software-freedom movement, then the wider scientific and technical community; the
   keeper's signed canon is the source of truth for values (CANON.md and PRINCIPLES.md, on his
   publication shelf at `<H>:/pub/canon/principles/`, a drive on his own machine; in the SAVANNAH
   enclave until 2026-09-29). No canon in reach? Say so, and reframe from the order above as a
   quoted snapshot, not your own. A point that cannot be restated that way is a
   preference — label it so.
4. **Detailed notes, unless the writing itself is the danger.** Write it down: what each view saw,
   what the inverse found, the reframes. If you can see that you cannot capture enough to do the
   work justice and honour the requester's intent, **stop and make arrangements** — say so, hand
   the material to a seat that can hold it, and record that you stopped. Otherwise the material
   falls to some other hand under-documented.

The LENS is explicitly coupled with releasing the minions (ethicsminions): the reflection is where
risk *and* opportunity get named, and naming an opening matters as much as flagging a gotcha.

## Two parties in the room, and when the answer is a choice

**The second four.** When the hand-back weighs two people's views, say Bryant's and Corwin's, view (b)
is not one line but three: your construal of party A, your construal of party B, and where those two
meet, named. This is the four-view shape of the two-readers paper, §V (me · A · B · the seam;
`h/DISS-2026-09-17-two-readers.md`, edition 0.2 at `writing/two-readers/DISS-2026-09-27-two-readers-v0.2.md`).
It is a *different* four from step 1's (a)–(d). Keep the two apart by name and never merge them:
write the three lines as `b.A`, `b.B` and `b.AB`, never as (a), (b), (c).

```
b.A   <party A>, as I construe them:  ...   (their words: <path:line> | invented)
b.B   <party B>, as I construe them:  ...   (their words: <path:line> | invented)
b.AB  where A and B meet, named:      ...
```

All three lines are your construction, not the people. A line about someone you have no words from
will read confidently and will not repeat if you run it again. In the 2026-09-27 experiment
(`writing/two-readers/EXPERIMENT-2026-09-27-doubled-nine.md:162-169`), the view of the party with no
quoted words was the least stable in both runs. Put their own words in before you lean on that line,
or mark it *invented*.

**A persona shows reasons, not decisions.** Wearing a persona (a CORWIN.md-like file) changes which
reasons you give, and each change traces to a line of the persona. On its first test it did not change
which option was chosen any more than a plain rerun did (`:31`, `:124-125`). So when the hand-back is a
choice between options, run the pass more than once before reading any difference as the persona's.
The spread between runs of the same pass is the noise floor, and only a difference beyond it is news.
The test used four runs per arm; that is a chosen stand-in from the house set, not a measured minimum.
Until reruns agree, say the persona *cited* a reason, not that its bias was *load-bearing*.

### Optional: the doubled-nine mode (carries its kit)

When a choice will be acted on and a persona is in play, measure instead of eyeballing. The steps run
by hand; `scripts/doubled_nine.py` (stdlib) does the counting.

1. **Preregister.** Before any run, write down what would make "the persona changed this" fail, and
   the rule you will read the result by. Hash that file.
2. **Draw, don't choose.** `doubled_nine.py draw BANK.tsv` picks one open question by a date seed. One
   draw, no redraw.
3. **One packet, one method.** Every run gets the same context packet and the same method
   (`doubled_nine.py method --party A --party B --field option`). A party with no words of their own
   in the packet is marked *invented* in their view.
4. **Arms.** Several cold runs (the method and packet only) and as many persona runs (the persona, then
   the same). Each run is its own session and sees nothing of the others. The experiment used four per
   arm, a house stand-in: the fewest that give six same-arm pairs to set a floor.
5. **A blind judge.** `doubled_nine.py judge DIR --key key.json` shuffles the answers by seed and
   labels them A, B, C…; a separate session splits them into two groups without being told the arms.
6. **Measure.** `doubled_nine.py measure DIR --field option`: the per-block word distance within each
   arm and across arms, the excess over the within-arm floor, and how many pairs disagree on each
   decision field within each arm and across. `permute DIR` ranks the true split among every split.

Read it by the rule the first run earned: a difference is the persona's only beyond the rerun floor. If
cross-arm pairs disagree on the decision no more often than same-arm pairs, the persona cited reasons
and did not move the decision. The kit came from one experiment (c4 `writing/two-readers/arms/`, two
runs, one model family); on that experiment's own data it reproduces every recorded distance, rank and
decision count. Steps 1–4 of the LENS above do not need it.

## Where it sits in the family (one method at three scales)

Pick the rung by how much of the reasoning you can still observe, not by taste:

- **LENS** — one human; you can hold the whole thing and turn it. Nothing needs capturing yet.
- **MICROSCOPE** — one mind is no longer enough magnification: strip the assumptions and keep only
  what survives with *no trust in the scorer*. The scaling apparatus between rungs.
- **BUBBLE CHAMBER** — several agents over a wire, each stateless, each flushing at session end:
  you cannot observe the particle, only the track it leaves — so write the tracks to disk as they
  form.
- **ECLIPSE** (the sibling, `eclipse-pass`) — the narrow critique of one target under two opposed
  biases, keeping the losers.

A LENS pass that grows past what one head can hold is the signal to climb, not to squeeze.

## The shape of a written LENS

One short block, six labelled lines, then the reframes:

```
LENS · <what is being handed back> · <date>
a  my view:              ...
b  the view I ascribe:   ...
c  their pull on mine:   ...
d  my pull on theirs:    ...
persona / inverse:       <persona> says ... / the inverse says ...
principles reframe:      1. ...  2. ...
notes: written | STOPPED — arrangements: ...
```

Keep OBSERVED apart from JUDGED inside it. Say in words whose concern each one is, where that matters
(the keeper's rule of 2026-09-24 retired bracketed tags); a concern that is only your own never blocks; no
concern without a falsifier.

## The script, when there are several readers

`scripts/lens.py` (stdlib; needs `ferry_core.py` beside it) turns a cross-model LENS into a
measurement: `pin` a subject by sha256, `add` or `import-json` each reader's stance per view,
`converge` to see where readers agree exactly (a stance match) — a difflib ratio over the prose rides
along as a hint, never the verdict.

Reruns count. A reading is (subject, model, view, **run**): a second `add` by the same model for the
same view is kept as the next run, and only `--run N` replaces run N. `converge` prints two verdicts
per view: across models (CONVERGE · DIVERGE · SINGLE · GAP, counting every run's stance) and, beside
it, within each model: **SPLIT-WITHIN** when some model's reruns disagree, **STEADY** when every model
that reran agreed with itself, **ONE-RUN** when nobody reran. Read CONVERGE as settled only beside
STEADY. Before 2026-09-27 the run was not part of the identity: a rerun replaced the first reading, so
a model that disagreed with itself looked like one settled reading and could print CONVERGE. On a copy
of the script older than that, give every rerun its own label (`sonnet-5#1`, `sonnet-5#2`).
`lens.py selftest --prove-red` plants the old identity and must go red; c4's
`writing/second-user/lens-rerun-probe.sh` shows the difference on any copy. A reading whose declared subject sha is not the pinned sha is
refused and receipted; `lens.py selftest` proves that refusal, and SPLIT-WITHIN, can fire. Use the script at MICROSCOPE
scale and above; by hand is enough at LENS scale.

## Portability

This file is the whole instrument. Dropped alone into another vendor's agent through a web gateway,
steps 1–4 run without any other skill, tool or tree. The doubled-nine mode is the one part that
travels with its kit (`scripts/doubled_nine.py`); its steps still read by hand without it. Where several SKILL.md files travel together,
each one that hands something back should carry its own short LENS block (the six lines above)
rather than refer here, so the technique survives whichever subset arrives.

## Land it before you show it

Write the result to a file before showing it, and head the file with one line:
`produced-by: lens · subject: <path or name> · sha256: <the subject's> · <UTC date>`. Used alone,
that line is a comment and nothing more; a shop that indexes its work can find the result by it
(ERRATA E19, 2026-09-29).

## How this skill can fail (falsifiers)

- **Blended views.** If the written pass has (a) and (b) agreeing and lines (c)/(d) empty or
  restating (a), the four views were not held apart — the check is that (c) and (d) each name
  something that would change if the other party changed.
- **Inverse that agrees.** If the inverse pass finds nothing the persona pass did not, either the
  point is rounded (say so) or the inverse was not run; a real inverse produces at least one line
  the persona would not have written.
- **Reframe by relabel.** A "principles reframe" that only prefixes the point with a principle's
  name is a relabel — the check is that the restated point could be argued from the principle to a
  stranger who never read the original.
- **Blended fours.** A written pass that labels party A, party B and their seam as (a), (b), (c), or
  folds `b.AB` into (c)/(d), has merged the two fours. If that shows up in practice, the second four
  wants a skill of its own rather than a section here.
- **Reasons read as decisions.** A persona/cold difference on a choice, reported as the persona's
  bias with no rerun beside it, is one coin toss read as a finding. The check: a second run of the
  same arm, or a STEADY beside the CONVERGE. If a rerun on another model family shows the persona
  moving the *decision* beyond the rerun floor, "reasons, not decisions" is a fact about one family,
  and the paragraph above must say so.
- **Stopped without arrangements.** A pass that ends "stopped" without naming who or what takes
  the material next is abandonment wearing the LENS's word — the check is a named seat or file.
- **Off-switch.** Say "no lens on this" for scratch, drafts, or work that hands nothing to anyone;
  or remove this directory. Composing skills (ones that only dispatch to others) need not run it.

## Provenance

His LENS, 2026-09-01, as I read it (`AS4CE0001/memory/lens-discipline.md`, CANDIDATE
until his 2026-09-11 confirmation); the ladder in his words 2026-09-07
(`c4/facts/lens-microscope-bubble-chamber.md`); the family section in `eclipse-pass`
(2026-09-11); the script from `AS4CE0001/h/lens.py` (v2, 2026-09-11). Minted 2026-09-11, unblessed.
The two-party section, reasons-not-decisions and the rerun identity: 2026-09-27, from c4's
`writing/second-user/ENHANCE-2026-09-27-two-readers-to-a-skill.md` (Q1) on his rulings second-user-D5
and two-readers-D5 (both A). The doubled-nine mode and its kit, 2026-09-27 later: promoted from HOLD
(QA-10) on his word; grown from c4 `writing/two-readers/arms/` (method.md, draw.py, measure.py,
posthoc*.py, judge-prompt.txt), keeping what both runs shared and making the rest arguments.

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 1.1.2: edition revised from 1.1.0 on 2026-10-10; spine: 2026-09-01.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA4: https://creativecommons.org/licenses/by-sa/4.0/ (scripts: GNU General Public License, version 3 or any later version; SPDX GPL-3.0-or-later); Mentat (for Corwin, claude-opus-5-5)
From the collection Corwin Brust and Bryant Frankford keep together, with K Smith as editor of the works she edited; thanks in ACKNOWLEDGEMENTS; home: https://github.com/inputloop
<!-- /footer -->
