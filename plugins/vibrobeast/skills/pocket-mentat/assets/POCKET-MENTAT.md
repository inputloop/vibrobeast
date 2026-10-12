# Pocket Mentat — a note-keeper you can hand to any AI

*Paste this at the top of a chat with any AI (or save it as a file your AI can read). It teaches the
AI a simple, portable way to take notes that stay findable, honest about where they came from, and
easy to carry to a different AI later. No tools, no accounts, no setup. If your AI can save files,
great; if not, it all works right in the chat.*

---

## What it does, in one breath
It helps your AI keep a running memory of the useful bits of your conversations — and, crucially,
**say where each bit came from** and **what would prove it wrong** — so the notes are trustworthy and
you (or a different AI tomorrow) can pick them straight up.

## Use it in 30 seconds
Tell your AI: **"Keep Pocket Mentat notes as we go."** From then on, whenever something worth
remembering shows up — a decision, a preference, a fact, a name, a gotcha — the AI writes one note in
the little format below and reads its notes back before answering things they touch. That's the whole
starter move.

## The note format (three parts + two honesty habits)
Every note is one line (or a short block) with three parts:

- **SEAM** — the thing itself: a word, idea, or fact. *(Think: the handle you'll grab it by.)*
- **PIN** — what it means in plain words, plus a few **trigger words** that should make the AI recall
  it. *(Think: the definition + "bring this up when I hear…")*
- **SEMAPHORE** — a little signal that gathers related notes together and remembers **where each came
  from**. *(Think: the folder-tab + the receipt.)*

…and two habits that make the notes worth trusting:

- **From:** say where it came from — `you`, `them`, `a source (name it)`, or `a guess`. *A note that
  can't say where it came from is a guess; label it one.*
- **Would-change-my-mind:** say the one thing that would make this note wrong. *If nothing could, it's
  an opinion, not a fact — label it so.*

**One-line shape:**
`SEAM — PIN (triggers: …) — From: … — Would-change: …`

**Example:**
`Deploys on Fridays — team avoids shipping before the weekend (triggers: "release", "Friday", "ship it") — From: you — Would-change: you say a hotfix is urgent`

## Linking near-neighbors (so notes find each other)
When a note relates to another, add two tiny links:

- **came-from:** the note or moment this one grew out of.
- **leads-to:** where it points next.

That's it — a note can be walked backward and forward, like beads on a string. Don't overthink it;
link when it's obviously useful.

## Growing gently (start small, split only when it earns it)
Begin with **one** notes area. Let it grow. **Split into a second area only when the first is
genuinely hard to scan** — not on a fixed count. Helpful *nudges* that usually mean "time to split":

- you've edited the **same spot** several times today (it's a hotspot — give it its own home),
- one page has gotten **long enough that you scroll to find things**,
- one section has **so many terms** you can't eyeball the list.

These are nudges, not laws. A human's judgment always wins over a number. When you split, leave a
one-line pointer behind (`moved X → new area`) so nothing gets lost.

## Carrying notes to another AI (the portable part)
The notes are plain text and self-describing, so any AI can read them. To hand your memory to a
different assistant, paste **this file + your notes**. Say: **"Here are my Pocket Mentat notes —
keep them going."** That's the handoff. Because every note carries its **From:** and
**Would-change:**, the new AI knows what to trust and what to re-check, instead of swallowing it all
whole.

## If things get sensitive
Pocket Mentat never tells you to hide things or to stop working — it helps you *keep and find* what
matters. If a note touches something private (a password, someone else's personal details), don't
store the secret itself; store a pointer ("the wifi password is in the kitchen drawer note") and keep
the secret where it belongs.

## A tiny worked example (three notes + a link)
```
SEAM: Pocket Mentat — a portable note format any AI can keep (triggers: "take notes", "remember")
  From: you  |  Would-change: you ask for a different system
  leads-to: "one area to start"

SEAM: one area to start — keep all notes in a single place until it's hard to scan
  From: this file  |  Would-change: the page gets long enough that you scroll to find things
  came-from: "Pocket Mentat"

SEAM: split-when-it-earns-it — make a second area only on a real nudge, not a fixed count
  From: this file  |  Would-change: you prefer strict thresholds instead
  came-from: "one area to start"
```

## The one rule under all of it
**Keep freely, say where it came from, say what would change it — and let the human decide.**
