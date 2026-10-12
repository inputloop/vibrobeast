# Two Columns — a way to keep notes that someone else can use

Paste this whole file into any AI assistant, or keep it beside your notes.
It needs no software and no particular setup.

Most notes say what a thing is. Two more pieces of information make a note
usable by somebody who was not there when you wrote it:

- **first-seen** — where you learned it. Not the date: the *place you could
  go and check*.
- **last-cited** — the last time you actually used it, and what for.

That is the whole idea. Everything below is how to keep those two honest.

---

## The shape of a note

```
THING — what it means in plain words (comes up when: word, word, word)
From: …
Would-change: …
first-seen: …
last-cited: …
```

- **THING** — the handle you will grab it by. A word or a short phrase.
- **what it means** — plain words, and the words that should make it come
  back to you later.
- **From:** — one of: `me` · `someone else (name them)` · `a document (name
  it)` · `a guess`.
- **Would-change:** — the one thing that would make this note wrong.
- **first-seen** — the earliest record of this you can actually open.
- **last-cited** — when you last used it, and where.

Two habits carry the whole thing:

**A note that cannot say where it came from is a guess, so label it one.**
That is not a demotion. A labelled guess is useful. An unlabelled one quietly
becomes a fact.

**A note that nothing could prove wrong is an opinion, so label it one.**

Together they are what makes the notes safe to hand over. Someone reading
them knows what to trust and what to re-check, instead of swallowing the lot.

---

## When a note changes

**Do not edit it. Write a new copy, change the copy, and leave the original
alone.**

On the new copy:

- keep `first-seen` exactly as it was — it still names where you learned it
- add `replaces:` pointing at the copy you just superseded

So a note revised ten times still says, on the newest copy, where the idea
originally came from. You never have to walk back through ten versions to
find out. You only walk back if you want to see how it changed.

Three things fall out of this, all of them useful:

1. **Nothing disappears because you tidied.** "We simplified that last
   month" is never the reason an answer is gone.
2. **Two people can keep the same notes** without overwriting each other.
   Neither can edit the other's copy — only add a new one. You do not need a
   rule about it; there is no way to do the wrong thing.
3. **Using a note stays cheap.** Using it just adds a line to a list. It does
   not rewrite the note.

That third point is why `last-cited` is kept *outside* the note:

```
cited/THING.txt
  2026-09-14 — used in the quarterly summary
  2026-09-20 — answered a question about pricing
  2026-10-02 — quoted in the vendor email
```

If you put that inside the note, you would rewrite the note every time you
used it, and its history would fill up with versions that differ by one date.

---

## Which notes to tidy up first

Count, for each note: **how many times it has been used since you last
revised it.**

```
used-since-revised = lines in cited/THING.txt added after the current version
```

- **A high number** means you are leaning on something you have not
  re-checked. Look at it first.
- **Zero** means nothing has needed it. It can move somewhere out of the way.

Moving it out of the way is *not* throwing it out. Keep it; just stop putting
it in front of yourself. You can always open it again.

This replaces "tidy up when it feels messy" with a number, which matters
because the feeling arrives at the same time as the tiredness, and the
tiredness is what makes tidying lose things.

---

## If a note points at a file

Say which machine or which place, every time:

```
notes:/ideas/pricing.md        somewhere in your notes
project:/docs/design.md        relative to the project
laptop:/Users/me/pricing.md    a specific machine, named on purpose
/Users/me/pricing.md           ← avoid: which machine? The note can't say.
```

A path with no prefix works where you wrote it and nowhere else, and nothing
in the note warns the next reader about that.

---

## Doing it, start to finish

1. Write the note in the shape above.
2. Fill in `From:` and `Would-change:` even when they feel obvious. The
   obvious ones are the ones that later turn out to be guesses.
3. Set `first-seen` to the oldest thing you can genuinely open.
4. Each time you use the note, add one line to its citation list.
5. To change a note: copy it, edit the copy, add `replaces:`, keep
   `first-seen`. Leave the original.
6. When there is too much to read: sort by used-since-revised, highest first,
   and work down.

---

## When not to bother

Skip the two columns on anything with no origin and no uses — a preference, a
draft sentence, a shopping list. The test: would you ever want to ask "where
did this come from?" or "is anyone still using this?" If not, the columns are
work with nothing to show for it.

---

## If a note touches something private

Store a pointer, not the secret. `the wifi password is in the kitchen drawer
note` — and leave the password where it belongs. This holds even when the
notes are only for you, because notes get handed over eventually.
