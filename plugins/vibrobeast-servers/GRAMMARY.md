# GRAMMARY.md -- GRAMMARY is a made word: the garden's lexicon, its words with what they mean and whose they are

> *"If GRAMMARY is out of date or confusing, the garden isn't correct."* -- Corwin

> Our grammar: the words, named here so we stop thinking in ephemeral ideas and start composing in a
> shared idiom. Start broad; prune what no tool or skill uses. Each entry says *what it is* and *how
> it acts*. Co-authors name their own terms in their own region (CORWIN.md §5/§22); this records the
> shared core, not anyone's private vocabulary, and points at a co-author's words instead of restating
> them. Revised when a term changes in the tree; last revised 2026-10-10, for the extension edition:
> fifty-three entries added to the 2026-07 seed's thirty-six, eighty-nine in all, as `sh bin/gm1gk` †
> counts them. Forty-seven came first: forty-one new words (twelve from the other lanes' requests),
> five pointer entries for co-authors' words, and one seed line given its own entry (NO4C); three
> more came in the second fix pass, and three in the third (buoyancy, steward, altorewired). The
> seed's confusing passages were reworded (study S2, part B).

## How to read an entry

Each entry has its own heading and five labelled lines: **What it is**, **How it acts**, **Where**
(the files or tools that use it), **Since** (the first date found), and **Whose word** (who coined
it or whose meaning it carries; a co-author's word is pointed at, not restated). A word with two
senses gets one entry and says both. Two names recur, the two people who made this garden together:
**Corwin** (Corwin Brust) keeps this install and rules on it, and **Bryant** (Bryant Frankford) made
Llama Bridge, the Tavern and the skills that carry his name. Each names his own words in his own
region, and this file points at them rather than restating them. **C4** is Corwin's model-and-tools
tree (see its entry below); **MCP** is the protocol the plugin's servers speak to Claude. A path
written in code type names a file or folder. A path marked † lives in the source tree this plugin
was minted from (public at code.bru.st/corwin/vibrobeast) or in the C4 tree, not in this plugin;
every other path is in the plugin, beside this file. `sh bin/gm1gk` † counts the entries, the
entries with no "Whose word" line, and the tree's own words that have no entry; it never stops
anything.

## Words a newcomer meets first

### seat
- **What it is:** the folder and record that holds one person's memory for a project, so a new
  session picks up where the last one left off. `AS4CE0001` (this project's folder) is the main seat.
- **How it acts:** the mentcached server (the plugin's memory server) reads and writes notes there; a note is never overwritten, a
  change is a new generation beside the old. Where no seat can be reached, nothing is invented.
- **Where:** mentcached's `seat_*` tools; the seatkeeper skill; `MEMORY.md`.
- **Since:** 2026-07-02.
- **Whose word:** the shop's (Corwin and Mentat); review P3 of the extension spell drafted this entry.

### SEATED, JAILED, NOTVISIBLE
- **What it is:** the three mode words mentcached puts on every answer. SEATED: the seat is reached.
  JAILED: the seat is not reached and a fallback folder inside the project (`MENTCACHED_JAIL`) is in
  use. NOTVISIBLE: nothing is
  reached, or a path you named does not exist.
- **How it acts:** a write while JAILED is refused unless asked for by name, and an allowed one carries
  `mode: JAILED` in its front matter forever; NOTVISIBLE refuses rather than create an empty store.
- **Where:** `polygram/mcp/mentcached.py` †; the plugin README's "three rules".
- **Since:** 2026-09 (the mentcached server).
- **Whose word:** the shop's.

### soft skill
- **What it is:** a skill kept as a plain file and read live by the plugin when a session asks for it,
  instead of being installed.
- **How it acts:** `soft_skills_list` finds it on every call and `soft_skill_read` returns its text;
  it becomes a full skill only after it shows use and Corwin graduates it by hand.
- **Where:** `SOFT-SKILLS/` †; mentcached's soft-skill tools (the "dynaloader").
- **Since:** 2026-09-23.
- **Whose word:** Corwin's direction of 2026-09-23.

### spell
- **What it is:** a prompt written as chapters, which a fresh session can be handed cold and run
  ("fired") again and again until it works.
- **How it acts:** each run leaves a dated run beside the spell (`runs/<date>/`), so a later firing
  starts from what the last one learned.
- **Where:** `c4/spells/` † (for example `c4/spells/extension/`, `c4/spells/build-turn/` †).
- **Since:** 2026-09-11.
- **Whose word:** Corwin's.

### prove-red
- **What it is:** a test's ability to show itself failing on purpose.
- **How it acts:** the test plants a known fault (a broken copy, a bad fixture) and must then fail
  ("go red", as a failing test shows); a test that cannot fail cannot be told apart from one that is not running.
- **Where:** nearly every file in `tests/` † (`--prove-red`); `python3 -m polygram.mcp --prove-red` †.
- **Since:** 2026-09-11.
- **Whose word:** the shop's.

### gauge, check, guard
- **What it is:** three strengths of test. A **gauge** counts and prints, and never stops anything. A
  **check** compares against a line Corwin ruled and calls a breach a fault. A **guard** stops the work.
- **How it acts:** the house default is a gauge, not a guard. Tool names end in `gk` for gauges and
  `ck` for checks (`cs1gk`, `gm1gk`; `hb1ck`, `lc1ck`).
- **Where:** the countable-gauge skill; `bin/*gk`, `bin/*ck` †.
- **Since:** his working norm of 2026-09-10 ("the general answer to signature drift is a gauge, not a
  guard on every edit").
- **Whose word:** Corwin's.

### falsifier
- **What it is:** the observation that would prove a claim wrong, written next to the claim.
- **How it acts:** a claim with no falsifier is an opinion, and is said as one; a JUDGED line carries
  its falsifier.
- **Where:** the lens and eclipse-pass skills; every JUDGED line.
- **Since:** 2026-07-09.
- **Whose word:** the shop's.

### OBSERVED, JUDGED
- **What it is:** the two piles a report keeps apart. OBSERVED is what was seen, with the command or
  source that shows it. JUDGED is a reading of it, with a falsifier.
- **How it acts:** a reader can re-run every OBSERVED line; a JUDGED line is never dressed up as
  OBSERVED. The old bracket tags on JUDGED lines are retired: cite the source instead.
- **Where:** lens, ethicsminions, every hand-back.
- **Since:** 2026-09-10 (his "two piles").
- **Whose word:** Corwin's.

### NOT CHECKED
- **What it is:** what a tool says when it could not look, instead of "clean" or "absent".
- **How it acts:** a missing path, an absent dictionary or an unreachable store is reported as NOT
  CHECKED with what it tried; it is never counted as a pass.
- **Where:** drift, color-theory, gd1ck, lc1ck, gm1gk.
- **Since:** 2026-09.
- **Whose word:** the shop's.

### persona sheet
- **What it is:** a character's written record: who it is, what it holds, a journal and a mutation
  log, used to give a voice its own line. Its **inverse** is the version of the character it must not
  become. It replaces the older name "behavior template".
- **How it acts:** the persona server reads sheets and archives a change as a new generation;
  `persona_resolve` finds the sheet for an actor, and with none found the actor still speaks in a
  plain default voice.
- **Where:** `book/*.md`; `h/persona/` †; the persona server; persona-engine.
- **Since:** 2026-09-11.
- **Whose word:** the shop's; CORWIN.md is Corwin's own sheet.

### road
- **What it is:** one way to reach a stored fact: a plugin tool, a folder on the mount, a Drive file, a
  Project doc.
- **How it acts:** the ROADS table lists the roads for each store in order; `rd1ck` walks them and
  prints READ, NOT REACHED or FENCED, never "absent". His name for the idea is TMTOWTDI, "there's more
  than one way to do it".
- **Where:** `conventions/ROADS.md`, `bin/rd1ck` † (the extension edition, lane D).
- **Since:** 2026-10-10.
- **Whose word:** TMTOWTDI is Model T's name for the idea (card 18; Model W called them routes); review
  P3 gives it as Corwin's. Which is right is NOT CHECKED.

### tone dial
- **What it is:** how long and how talkative answers are, from "crisp/laconic" to
  "detailed/contextualized" (his words), set from what the person's own messages show.
- **How it acts:** the preference `tone.dial` holds it as two pairs, signals seen over signals total,
  for answer length and for narration; the default `0/0, 0/0` (the origin) means no signal yet, and
  answers stay plain. `tone.show` says whether it is shown in words or numbers (default words).
- **Where:** `polygram/mcp/prefs.py` †; the extension spell, chapter 1; cards 10-12.
- **Since:** 2026-10-10.
- **Whose word:** Corwin's (the spell's chapter 1).

### guessed pair
- **What it is:** every guess given as two numbers: how likely, and how sure of that, each marked as a
  guess.
- **How it acts:** a second question in one turn may be asked only when the confidence that it could be
  skipped is 17% or less; `qg1ck` (the question gauge) checks that.
- **Where:** the extension spell's rulings Q573 and Q574; `KIND=gauge` rows in the frame; `bin/qg1ck` †.
- **Since:** 2026-10-10.
- **Whose word:** Corwin's rulings.

### HEAVY
- **What it is:** a tag on a piece of work, in Corwin's words: "try hard to apply effort, and lean back
  a little against the optimizations where that gives better results, even or especially for
  diagnostics" (the extension spell, chapter 3, Q576). In plain words: spend more, on purpose.
- **How it acts:** the HEAVY lens runs under it: a GRAIN warm-up, two contrasting models, their
  convergence with the tensions shipped as options, review by persona pairs and a control GRAIN, and
  repeat until it stops paying.
- **Where:** `c4/spells/extension/chapters/03-heavy-lens.md` †; the extension spell's runs.
- **Since:** 2026-10-10.
- **Whose word:** Corwin's (Q576).

### GRAIN, GREAT, GRAND (4, 9, 17)
- **What it is:** the house numbers: 4, 9 and 17, the three sizes the shop uses whenever it needs a
  small, medium or large count. As sizes of a sized edition: the floor plus 4, 9 or
  17 percent of what the build draws on. As sub-agent counts: 4 by default, 9 and 17 for larger work.
- **How it acts:** when a number must be invented, the house set 4, 9, 17 is used and said to be
  invented; `make edition SIZE=grain` (or great, grand) mints that size.
- **Where:** `polygram/editions.py` † (`HOUSE`); NEWS 0.8.90.
- **Since:** 2026-09-04.
- **Whose word:** Corwin's.

### edition
- **What it is:** one minted shape of the plugin: the full plugin, or a sized edition (GRAIN, GREAT,
  GRAND) that carries the floor plus a share picked by use, with every other skill shipped soft. Also:
  the plugin's next version as a whole ("the extension edition").
- **How it acts:** every edition carries the floor (the skills listed in `editions.FLOOR`, eight
  today); the minted README names them.
- **Where:** `polygram/editions.py` †; `make edition`.
- **Since:** 2026-09-28.
- **Whose word:** the shop's.

### mint
- **What it is:** to make a file from its sources by a tool, never by typing it: a plugin, a footer, a
  README's counts, the terms of service.
- **How it acts:** a minted file is re-made, not hand-edited; if it is wrong, the source or the tool is
  fixed and it is minted again.
- **Where:** `make dist`; `bin/ft1mt` † (footers); `bin/tp2mt` † (terms and privacy); `polygram/plugin.py` †
  (the README).
- **Since:** 2026-09.
- **Whose word:** the shop's.

### shelf
- **What it is:** a folder of finished work that others read: the publication shelf (`<H>:/pub`), the
  plugin shelf (`dist/vibrobeast` †), a persona shelf.
- **How it acts:** tools read a shelf and do not write it unless its `.gate` says so; drafts land on the
  shelf as plain files and the keeper signs them there.
- **Where:** shelf-check skill; `.gate` files; the persona server's shelves.
- **Since:** 2026-07.
- **Whose word:** the shop's.

### door, drawer
- **What it is:** two kinds of artifact. A **door** has a named reader who relies on it, so its
  signature means something. A **drawer** has no named reader and is expected to change.
- **How it acts:** before proposing any signing work, name the reader: no named reader, no ask. Also,
  `.door/` † holds this project's door parts, the rules C4's `door render` pulls in by context.
- **Where:** the drawer-vs-door skill; `.door/`; `c4/bin/door` †.
- **Since:** 2026-09-23.
- **Whose word:** the shop's.

### swing
- **What it is:** the final step of a build loop, owed when the QA rounds are spent and a pass was not
  clean: close what is left (unmet requirements, reachable fixes, cheap improvements, warnings).
- **How it acts:** snapshot what it will touch first; in the swing, not undoing earlier fixes comes
  first; if it made things worse, restore the snapshot. Once per try at the full loop. `sw1ng` counts
  the passes; `sw1mt` runs several tasks' checks together (the multitask swing).
- **Where:** the build-loop skill; `c4/spells/build-turn/` †.
- **Since:** 2026-10-04.
- **Whose word:** Corwin's ("final swing only once per try at the full build-loop").

### egress
- **What it is:** anything leaving this machine: a push, a post, a call to a model.
- **How it acts:** before it goes, say what leaves and to whom, and stop at a fence; the before-ship
  hook in `polygram/hooks.md` † names the act that does this.
- **Where:** `SOFT-SKILLS/egress/` †; candor-gate; `polygram/hooks.md` †.
- **Since:** 2026-10.
- **Whose word:** the shop's.

## More words the tree uses

### LENS
- **What it is:** the wide reflection, run before a deliverable leaves your hands: hold four views apart
  (yours; the one you ascribe the other party; their influence over yours; yours over theirs), pass the
  persona and its inverse, restate each point from principles, then write it down or stop and make
  arrangements.
- **How it acts:** by hand, or with many readers (a HEAVY lens); it changes what is handed over, not
  how it is checked.
- **Where:** the lens skill.
- **Since:** 2026-09.
- **Whose word:** the shop's ("one human's thought experiment").

### eclipse, eclipse pass
- **What it is:** the "debugger on" critique ritual (a critique, not a code debugger): stress-test a proposition, design or skill until
  its weak claims break.
- **How it acts:** it checks the target against seeded-random real projects, runs a doubt-first and a
  reward-first bias and treats their agreement as the stability check, and keeps the losing models
  instead of throwing them away.
- **Where:** the eclipse-pass skill; `.eclipse-increments/` †.
- **Since:** 2026-07.
- **Whose word:** Corwin's (his extreme-debug discipline).

### footer, spine
- **What it is:** the **footer** is the common last block of a skill or document: its version, the
  version it was revised from and when, its **spine** (the earliest evidence of the work found), and the
  copyright, licence and byline.
- **How it acts:** it is minted by `bin/ft1mt` † from `conventions/house.env` † and
  `conventions/FOOTERS.org` †, never typed; a file is re-dated only when its body changes.
- **Where:** every SKILL.md; this file's own footer.
- **Since:** 2026-10-04.
- **Whose word:** the shop's.

### byline
- **What it is:** the line that says who wrote a piece and for whom:
  `Authored by Mentat (for Corwin; claude-opus-5-5)`.
- **How it acts:** the persona server's `persona_byline` makes it; it names the persona, the principal
  and the model, so a reader knows whose voice and whose hand.
- **Where:** footers; the persona server.
- **Since:** 2026-06 (Mentat as a byline in Corwin's dungeon repo).
- **Whose word:** the shop's.

### hand-back
- **What it is:** the report a session or builder leaves when its work is done or paused: what was
  done, what was not, what it found, and what the keeper owes (a signature, a choice).
- **How it acts:** OBSERVED apart from JUDGED; a deferral names its blocker; it is written to a file a
  later session can read.
- **Where:** `Inbox/HANDBACK-*.md`, `advice/*/HANDBACK-*.md` †.
- **Since:** 2026-09.
- **Whose word:** the shop's.

### dynaloader
- **What it is:** the plugin's live reader of soft skills.
- **How it acts:** see **soft skill**: it scans the SOFT-SKILLS roots on every call and serves a skill's
  text, with nothing installed.
- **Where:** `polygram/mcp/softskills.py` †.
- **Since:** 2026-09-23.
- **Whose word:** Corwin's direction of 2026-09-23.

### c4face
- **What it is:** the plugin server that runs C4's own MCP server (`mcp/c4-mcp.js`) from your C4 folder,
  with node.
- **How it acts:** off until you ask Claude to set `c4.on`; it checks C4's code at every start against
  an allow-list (a tripwire, not a wall), and with anything missing one tool, `c4_status`, says what.
- **Where:** `polygram/mcp/c4face.py` †.
- **Since:** 2026-10-08.
- **Whose word:** the shop's.

### build loop
- **What it is:** a counted build discipline: plan, do, check, act, with a budget of QA passes, one
  redesign per cause, and a final **swing** that can be backed out.
- **How it acts:** a design and a QA plan are written before the build; `sw1ng` counts the passes.
  Choosing the loop is optional; once chosen, every step is required.
- **Where:** the build-loop skill; `c4/spells/build-turn/` †.
- **Since:** 2026-10-04.
- **Whose word:** Corwin's (the Deming cycle, his rules for it).

### buoyancy
- **What it is:** how strongly a note in the seat is being leaned on: its citation pressure (how often
  it has been cited since it was last revised), measured against the other notes the same party
  cites, not against the whole store. A small reader's most-used note floats even when a busy
  reader's ordinary traffic is larger.
- **How it acts:** `seat_buoyancy` lists the notes most buoyant first, as the compaction queue: a high
  one floats (it stays on the loaded index page), one at zero may sink to a continuation page.
  Sinking is never deletion; the floor is still the store. The tool reports and compacts nothing.
  Because it ranks each note within one party's world, `MENTCACHED_BY` (who is writing) must stay the
  same from one start to the next.
- **Where:** mentcached's `seat_buoyancy` tool; `polygram/mcp/dl2.py` †; `servers/bin/dl2-lift.awk` in
  the plugin, a second reader of the same ranking.
- **Since:** 2026-09-14 (the index card beside that day's drawing: SURFACE / "buoyancy" over DEPTH /
  FLOOR).
- **Whose word:** Corwin's (his index card); the ranking against each party's world is the shop's.

### steward, nongnu-steward
- **What it is:** nongnu-steward is a soft skill that tends a free software project the way a careful
  reviewer reads it: a copyright and licence notice on every file that needs one, the licence texts in
  the tree, a list of dependencies with their licences and addresses, and "or any later version" on
  GNU licences. The expectations Savannah (the GNU project's hosting site) states for projects that
  are not part of GNU are its floor. The two switches whose names start `steward.` belong to it.
- **How it acts:** it audits and suggests; it edits a file only when asked with `--write`, and never
  signs, chooses a licence or sends anything to a host. In a project folder that carries a
  `.nongnu-steward` file, its opener ns1op (the steward's session opener) runs when a session opens:
  `steward.auto` (on by default) runs the notice and dependency audit, and `steward.canon` (on by
  default) says how old its pinned sources are and the command that checks them; it never fetches
  anything unasked.
- **Where:** `SOFT-SKILLS/nongnu-steward/` †; the two switches in `polygram/mcp/prefs.py` †.
- **Since:** 2026-09-23.
- **Whose word:** the shop's, for Corwin (a GNU volunteer); the floor is Savannah's own published
  expectations, pointed at, not restated.

### altorewired (Alto Re-wireD)
- **What it is:** a skill that makes sure word reaches Corwin when an action might otherwise leave him
  with nothing back: it appends one dated line to a return-tail file that his relay carries to him,
  and at the end of a prompt that changed something testable it gives one line, RAN (naming the test)
  or NOT RUN (naming what exists and was not run).
- **How it acts:** it fires broadly (its description says to trigger on most prompts), so the plugin
  README lists it under "Skills that fire broadly", where a new user can decline it; it writes rarely.
  If the tail cannot be written it says NOT ATTEMPTED and prints what would have run; Claude never
  reads the tail back. The name is "alto", a voice, re-wired: his plan to replace the Wire.
- **Where:** `skills/altorewired/SKILL.md`.
- **Since:** 2026-08-17 (its first grown section; the seed above it is earlier).
- **Whose word:** Corwin's: the seed is his, kept word for word.

## Words the extension edition adds

*Taken from the other lanes' requests (`advice/EXTENSION-2026-10-10/REQUESTS-lane-C.txt` †), 2026-10-10.
Each says whose word it is as the requesting lane gave it.*

### frame
- **What it is:** the one append-only table that spans, drift checkpoints, question gauges and tone
  readings share: one row per event, twelve columns, described in words in `FRAME.md`.
- **How it acts:** rows are only added, never rewritten; usage capture writes to it only when
  `usage.capture` is on (it is off by default).
- **Where:** `polygram/mcp/spans.py` †; `FRAME.md`; `bin/qg1ck` † reads its `gauge` rows.
- **Since:** 2026-10-10.
- **Whose word:** Mentat's, from the extension design (lane A).

### reset (of a span)
- **What it is:** a token count that went up between two readings, which can only mean the count was
  reset (a new prompt, or the app's own housekeeping).
- **How it acts:** it is counted as a reset and said in words ("N resets seen"), never subtracted into
  a negative cost; that leg is left out of the totals.
- **Where:** `polygram/mcp/spans.py`; `bin/sp1rp` †.
- **Since:** 2026-10-10.
- **Whose word:** Mentat's, from the extension design (lane A, card 15).

### declared key
- **What it is:** a preference that a skill names in the `preferences:` list of its SKILL.md front
  matter; that skill is its reader.
- **How it acts:** the preferences server accepts a key no built-in list knows only when a loadable
  skill declares it.
- **Where:** `polygram/mcp/softskills.py`, `polygram/mcp/prefs.py` †.
- **Since:** 2026-10-10.
- **Whose word:** Mentat's, from the extension design (lane A).

### people.named, writer rule
- **What it is:** `people.named` is the preference that lists the keeper and the participants he
  named; only their `person.<name>.*` rows are kept. The **writer rule** says who may write such a row:
  that person on their own turn, the keeper on his, or anyone with a consent row's id.
- **How it acts:** a `person.` row for anyone else, or from anyone else, is refused, and other people's
  rows stay out of export and the frame.
- **Where:** `polygram/mcp/prefs.py` † (`PREFIXES`).
- **Since:** 2026-10-10.
- **Whose word:** Mentat's, from the extension design (lane A).

### seatkeeper "no"
- **What it is:** the remembered answer when a person says no to seating a folder: the preference
  `skill.seatkeeper.<hash>` with the value `no: <the folder's path, in words>`.
- **How it acts:** the seating detector (`st1dt`) does not ask again about that folder; `pref_unset`
  takes the no back, and `pref_list` reads it back as the path, not the hash.
- **Where:** `skills/seatkeeper/SKILL.md`; `polygram/mcp/prefs.py`; `bin/st1dt` †.
- **Since:** 2026-10-10.
- **Whose word:** Mentat's, from the extension design (lanes A and D, card 22).

### persona ledger, DIVERGED
- **What it is:** `LEDGER.md`, regenerated (never hand-edited) from the persona sheets: a table of who
  carries whose inverse, with a read-back in words. **DIVERGED** is its word for a second copy of a
  sheet whose bytes differ from the first.
- **How it acts:** the read-only `persona_ledger` tool writes it only from what the sheets say; which
  copy of a DIVERGED sheet is the master is Corwin's to choose.
- **Where:** `polygram/mcp/persona.py`; `persona-ledger/LEDGER.md` †.
- **Since:** 2026-10-10.
- **Whose word:** Corwin's ruling of 2026-10-10 for the net; study S4's name for the file (lane B).

### "Whose inverse I carry"
- **What it is:** the section a persona sheet would carry naming the personas whose inverse it holds,
  so it can say when they go wrong.
- **How it acts:** the persona ledger is built from these sections; a sheet without one adds no row.
- **Where:** proposed for the sheets in `h/persona/` and `book/` †; not yet in any sheet.
- **Since:** 2026-10-10 (proposed).
- **Whose word:** study S4's (proposed); the sheets are Corwin's pen (lane B).

### default voice
- **What it is:** the plain voice an actor speaks in when no persona sheet resolves for it, at the
  origin of the tone dial.
- **How it acts:** `persona_resolve` hands it back instead of failing, so an actor with no sheet still
  speaks; shown in words, not numbers, by default (`tone.show`).
- **Where:** `polygram/mcp/persona.py` †.
- **Since:** 2026-10-10.
- **Whose word:** card 11 of the extension spell (lane B).

### READ, NOT REACHED, FENCED
- **What it is:** the three answers `rd1ck` (the roads checker) gives for each road: READ (it answered),
  NOT REACHED (it did not answer this time) and FENCED (it runs through a path that is never read).
- **How it acts:** never "absent": a road that did not answer is not evidence the fact is gone. A NOT
  REACHED row names the seat that looked, the folder it listed and the request it tried.
- **Where:** `bin/rd1ck`; `conventions/ROADS.md` †.
- **Since:** 2026-10-10.
- **Whose word:** the extension design's ROADS row (lane D).

### grain (of seating), kept out of view
- **What it is:** how much seating the seating detector proposes for a folder: none, light (a `.gate`
  only) or full (a `.gate`, an `INDEX.md` and a seat entry). Not the same as GRAIN the size (see GRAIN,
  GREAT, GRAND). **Kept out of view** is its count of secret-class files, which are never named or
  opened.
- **How it acts:** `st1dt` proposes one grain and asks once; it never writes. Secret-class material is
  shown as a count ("3 files kept out of view"), names only on ask.
- **Where:** `bin/st1dt` †.
- **Since:** 2026-10-10.
- **Whose word:** Model T's seating act; this reading of "grain" is lane D's guess; card 21.

### drop, counterpart, modes of work
- **What it is:** a **drop** is one hand-over of files from Bryant, kept under `c4/from-bryant/<date>` †.
  A **counterpart** is our skill that matches one of his, with how they relate (same origin, derived
  from ours, derived from his, an answer to it, or none). **Modes of work** are lines pulled by pattern
  from a skill's description and headings (its trigger, loop, gates, hand-back), with no reading of
  what they mean.
- **How it acts:** `br1in` (the Bryant drop intake) checks a drop's sums and his pinned key, hashes
  every file and reports in words; it never installs, signs or edits his files.
- **Where:** `bin/br1in`; `conventions/bryant-counterparts.tsv` †.
- **Since:** 2026-10-10.
- **Whose word:** study S1 (drop, counterpart); Corwin's ask for Bryant-modes intake (modes of work);
  lane D.

### tool code
- **What it is:** the short name a house tool gets: letters, a digit, letters, five in all, read as
  words (`gm1gk`: GRAMMARY, 1, gauge; `lc1ck`: licence, 1, check).
- **How it acts:** each tool's header says what its code stands for, and a page explains the code on
  first use. This edition's: `st1dt` (the seating detector), `rd1ck` (the roads checker), `qg1ck` (the
  question gauge), `br1in` (the Bryant drop intake), `pr1ef` (the preferences reader in awk), `lc1ck`
  (the licence check), `gm1gk` (the GRAMMARY gauge).
- **Where:** `bin/` †.
- **Since:** 2026-07.
- **Whose word:** the shop's.

## Co-authors' words (pointer entries)

These are Bryant Frankford's, or name his software. Their meaning is his: each entry points at his
words and does not restate them.

### RECIPE
- **What it is:** one pickable way to connect or set something up, written down so a stranger can
  choose it: its name, what it needs, what it touches, how to undo it, and how to check it worked.
  Corwin first wrote it "RECIPIES"; the spelling was healed on his ruling (Q575).
- **How it acts:** the extension offers Wire and Tavern connections as RECIPES to pick from, instead
  of steps to follow by hand. The pub surface (`<H>:/pub`, the as-publisher shelf) also keeps a `RECIPE.org`: its front-door
  instructions for how material gets in and how a release gets out.
- **Where:** `c4/spells/extension/chapters/04-design.md` † (A1); `<H>:/pub/RECIPE.org`; the option cards
  `c4/spells/extension/runs/2026-10-10/cards/OPTION-04-recipe-surface.md` †.
- **Since:** 2026-09-11 (the pub surface); 2026-10-09 (the extension).
- **Whose word:** Corwin's.

### carry-in
- **What it is:** a note left in a spell's `runs/` folder before a firing, carrying something into
  it: a review, a ruling or a question. Its name ends `-NOTE-carry-in.md`.
- **How it acts:** a firing reads the newest carry-in first, and doesn't count it as a firing.
- **Where:** `c4/spells/*/runs/` †; the first one is
  `c4/spells/extension/runs/2026-10-10-NOTE-carry-in.md` †.
- **Since:** 2026-09 (the spells' "how to fire it" chapters).
- **Whose word:** the shop's (Mentat's), in the spells he hangs.

### READER PRESENT, NOT READ
- **What it is:** what `rd1ck` (the road check) prints when a road to a store has a reader program
  but nothing was actually read back through it this time. Only a fact read back counts as READ.
  "One road, two stores" names a folder that serves two stores, which the check lists twice.
- **How it acts:** a road whose kind is `reader` (a program such as `pr1ef` or `sp1rp`) stays
  READER PRESENT until a line comes back through it.
- **Where:** `bin/rd1ck`, `conventions/ROADS.md` †.
- **Since:** 2026-10-10.
- **Whose word:** the shop's (fix lane F1, review pass 2).

### question_log
- **What it is:** the `mentcached` tool that writes one `gauge` row in the frame when Claude puts a
  question to a person: one or two at once, the likelihood guess and the confidence that the
  second could be skipped. `qg1ck` (the question gauge) reads these rows.
- **Where:** `polygram/mcp/spans.py` †; FRAME.md.
- **Since:** 2026-10-10.
- **Whose word:** the shop's (fix lane F1, review pass 2).

### LOOK (exit 77)
- **What it is:** what the kit shows when a check could not run here (a missing Tcl or Ruby, say),
  or when a gauge has a count worth looking at. The runner exits 77 and prints NOT CHECKED. A LOOK
  is neither a pass nor a failure. `gm1gk --kit` is the GRAMMARY gauge's kit form.
- **Where:** `bin/gd1ck` †; the test runners under `tests/` †.
- **Since:** 2026-10-10.
- **Whose word:** the shop's (fix lane F1, review pass 2).

### Tavern
- **What it is:** Bryant Frankford's common room for people and agents (written with Alfred).
- **How it acts:** see his own text, not ours: `polygram/mcp/NOTICE-tavern` † says where the copy we
  carry byte for byte (stock 2.3.1) came from and where its updates come from.
- **Where:** the tavernface server; the garden-pony skill.
- **Since:** 2026-10-08 in this tree.
- **Whose word:** Bryant's.

### Wire
- **What it is:** the relay between gardens (the ÆTHERNET relay), Bryant's, run at
  `bryantfrankford.com/aethernet`; peers send and read messages there.
- **How it acts:** see the aethernet-relay and wire-connect skills, which carry his relay's own rules
  (his signed original is kept at `c4/from-bryant/2026-08-05/` †).
- **Where:** `skills/aethernet-relay/`, `skills/wire-connect/`, `skills/wire-ledger/`.
- **Since:** 2026-07-05.
- **Whose word:** Bryant's (with Alfred).

### garden-pony
- **What it is:** a tool registry for a Tavern: a patch, called **gp.1**, to Bryant's Tavern 2.3.1
  (`tavern_status` says which build is running). "garden-pony"
  is a working name; who coined it is NOT CHECKED here.
- **How it acts:** see the garden-pony skill; the patch runs nowhere yet, so every road through a
  Tavern room is dormant until it does.
- **Where:** `skills/garden-pony/`; `projects/garden-pony` †.
- **Since:** 2026-10-08.
- **Whose word:** the software it patches is Bryant's; the registry came from Corwin's Tavern work.

## The 2026-07 seed (kept, reworded where it confused)

The entries below are the seed of 2026-07-02/09, one bullet each. Their "whose word" is given once per
section, from the seed's own note that it records the shared core; it is not checked word by word.
Words used here that the tree no longer uses are marked "book word" (they live in book/CORWIN.md).

## The agents / skills (the orchestra)
*Whose word: the shop's (Corwin and Mentat).*

- **Mentat** — the note discipline. NOTICES and *remembers*; turns lived moments
  into tagged memory. Everything downstream feeds on Mentat's notes. Also a persona
  (its sheet is in `h/persona/` †) and an authorship byline,
  `Authored by Mentat (for Corwin)`, on nearly two hundred files.
- **EthicsMinions** — deterministic *guards* over the shared surface. Notices drift
  from stated values, tamper, flattery, and the care concerns listed in CORWIN.md §10
  (the seed called them "care-gate (H6)"); recommends, never fixes.
  Hands memory to Mentat, skill ideation to skilltank.
- **SkillTank** — curates the skillset itself: spots skill-shaped patterns, labels
  NEW / ENHANCE / LEAVE-AS-MEMORY, routes to skill-creator or back to Mentat.
- **Sandboxer** — forces a write through a flaky mount; write-and-verify, restore
  from HEAD, clear stale compiled artifacts.
- **polygram** — the forge. Gated agent-skill synthesis (see Pipeline).
- **pmo** — the cross-project supervisor (TSV ledgers; never hand-edit its output).

## polygram pipeline terms
*Whose word: the shop's.*

- **candidate** — a tag cluster that may deserve a skill.
- **gate / verdict** — the explainable PASS/HOLD/REJECT scorer + recorded reasons.
  PASS≥3 synthesizes; HOLD≥1 parks; REJECT drops. Corroboration +2, well-formed
  label +1, generic label −2; an operator `:SKILL:` flag *surfaces* without scoring.
- **advice** — the dated paper trail of every gate/dist/operator decision.
- **synth** — writes the SKILL.md (+tool.py) skeleton for a PASS.
- **review** — the HOLD desk: `--promote` / `--reject` / `--freeze-extern`.
- **extern** — an upstream source; feeds candidates ONLY via its own `memory/` †.
- **family** — the list that limits which *installed* skills `dist` will pull in;
  the garden's own `skills/` always ships (`polygram/dist.py` †).
- **.skill bundle** — folder-rooted zip the desktop app installs; SHA-256 manifest.
- **dist** — `make dist`: mints the tar.gz/zip aggregates and per-skill `.skill`
  bundles, and also signs, mints the plugin (and its sized editions), and the terms
  and privacy texts (`bin/tp2mt` †).
- **.gate (sign-post)** — dotfile at a directory root declaring consented tool
  traffic: `policy` (read-write/read-only/write-only/none) + `reason` + `since`
  (`polygram/gatefile.py` †).
  Nearest sign governs; silence ≠ consent; bad policy fails closed. NOT the
  candidate gate — this one gates *access*, that one gates *synthesis*.
- **embargo (on a .gate)** — optional field gating *egress* (anything leaving this
  machine; here, publishing), orthogonal
  to policy: you can read and work the tree, not move it out. While present,
  publish is denied. **No timer ever lifts an embargo** — a date in the value is
  documentation of intent; a date passing is silence, and silence ≠ consent. A
  human lifts it by editing the sign (`lift:` names who/how); the file's history
  is the audit trail.

## The dimensional model (the book's lenses)
*Whose word: Corwin's. These are book words: they live in book/CORWIN.md and no tool in the tree uses them.*

- **dim1 (tags)** — `:modeling: :memory: :skills: :ethics: :freedom: :persona:
  :method: :meta:`.
- **dim2 (categories)** — `:teach: :show: :argue: :reference:`.
- **dim6 (carry-forward)** — **uniting / integration**: the "self" lens that
  presides; asks *what does this sit on top of / unite with?* Our refinement base.
- **ASPECTS template (6+6)** — HARD hexad: memory · tool-building · optimization ·
  introspection · critique · ethical baseline. SQUISHY hexad: self · honesty ·
  diligence · thoughtfulness · tempo · soul. Each cell carries a *do-this acting
  clause* — a model that DRIVES, not just describes.
- **drive, not describe** — house principle: portrait + acting clause = control surface.

## C4 / ghostwheel
*Whose word: Corwin's.*

- **C4** — Corwin's model-and-tools tree (`F:\claude\c4`, mounted as `~/mnt/c4`): its
  own `bin/` †, `spells/`, `man/` and an MCP server (`mcp/c4-mcp.js`), which the plugin
  reaches through c4face. Its shell core is `p/c4fn/ghostwheel.fn.sh`: a hub-and-spoke
  mesh of tiny namespaced, override-able POSIX functions; tests-first (run-levels 0–5);
  sign/SHA-256 by default ("crude-ci").
- **17-letter taxonomy** (filesystem-as-DB): asset · command · document ·
  environment · feature · graph · heap · identity · job · link · mapping · object ·
  package · register · subscription · taxonomy · workspace.
- **c4-consent-quartet** (book word; cited by INDEX.md) — the four of seventeen that scope consent into a behavior
  template. **Adopted as START:** identity (WHO) · package (WHAT) · subscription
  (GRANT) · register (PROOF). To be refined over ≥6 rounds.
- **ghostwheel** — Corwin's free-software hosting collective; Fosshost successor;
  the federation substrate (spokes, signed `.skill` exchange).

## Sharing / federation
*Whose word: Corwin's.*

- **federation** — multi-player = consented *single-player* models exchanged as
  signed artifacts; **never a merged brain**. Each co-author owns their region.
- **ccspt** — the consent + provenance + trust seam; where memory leaves a project
  and must be trustworthy. Consent rides the artifact (the quartet). The skillx
  server's first blocker is "ccspt not pinned". What the letters stand for is NOT
  CHECKED here (no file in the tree spells them out): Corwin's to say.
- **behavior template** — the old name for a **persona sheet** (see that entry): a
  fillable multidimensional persona model (CORWIN.md is the flagship; BRYANT, KELSEY
  are seeds) used to direct AI *as oneself*. The tree now says "persona sheet".
- **CLAUD_QA_HOLD** — the record of changes Claude made or holds (`CLAUD_QA_HOLD.md`).
  Since 2026-09-27, help he asked for lands without a box: a hold waits on a named
  trigger or reader, and only real consent cases wait on him; decisions are dated to
  advice/.

## Guards & idioms (values in the grammar)
*Whose word: Corwin's.*

- **"merely data"** — an unsubstantiated assessment; cite sources or it doesn't count.
- **no flattery / no vanity-play** — Corwin holds people high; praise reads as
  manipulation. Soul/vibe is *shown, never claimed*.
- **intermingle, don't un-mingle** — blend the work; keep the voices distinct.
- **on their own terms** — bespoke naming as empowerment; everyone coins their own.
- **rail-laundering guard** — owning the pipeline must not silently attribute
  co-authors' ideas to the infrastructure-owner.
- **values spine** — his order of what decides: universalism and egalitarianism,
  then the four freedoms, then the software-freedom movement, then the wider
  technical community; "we must reach everyone." The signed values canon lives on the
  publication shelf, `canon/principles/` † (moved from SAVANNAH 2026-09-29).

## LABELS (the pinned vocabulary — formalized 2026-07-04)
*Whose word: the shop's; NO4C is Corwin's.*

The machine mirror is **`labels.tsv`** (label · meaning · owner · consumer ·
since); this section is the human truth and the tsv must agree with it. The
rule that earns a label its row: **a definition, an owner, and at least one
mechanical consumer** — an unconsumed label is decoration with a serial
number (the pre-fix REJECT was the standing counter-example: recorded,
respected by no tool, and `concise` walked right through it). Current set:
`:SKILL:` (gate surfaces) · `PASS`/`HOLD`/`REJECT` (gate verdicts; REJECT is
**durable** — latest-terminal-wins in advice, cleared only by `review
--promote`; HOLD is never terminal) · `:CLAUD_QA_HOLD:`/`QA-n` (the desk) ·
`NOSIG`/`FURNITURE` (publish audit vouches) · `.gate` (access sign-post) ·
`AI_GUARD_*_CLAUDE` (guard provenance) · `.skill-manifest` (what skill-sign
signs) · attestations (the minions `--expect` drift pins, echoing SAVANNAH) ·
`NO4C` (see the NO4C entry below).
Curate like skills: every label taxes every cold session — small set, teeth
required.

- **NO4C** — a message marker meaning: this does not cross the network or the local
  boundary. Spelled with the letter O; `N04C`, with a zero, is read the same (in the
  registry "N0" is network zero, usually this computer, and does not restrict
  loopback).
  - *What happens to a marked message headed out* (the Wire, for one): it is dropped
    and flagged, in either direction. To send it anyway it must be wrapped in one more
    layer that says it is not an instruction: a comment, an example, a quoted source or
    a proposal ("wrap in a cons layer").
  - *The lift gate* (ruled 2026-07-08): a marker RAISED (at the start of a line, an
    active envelope) parks the file until the keeper lowers it with `-f`; a marker
    MENTIONED in mid-prose lifts with a note; CARRIED disarms it by renaming it
    `NO4C-CARRIED`.
  - *Where its rules live:* the registry row in `models/SEMAPHORES.md` † (also carried
    as `projects/pmo/SEMAPHORES.md` †; that row still reads "provisional", though
    `labels.tsv` and the lift gate carry the 2026-07-08 ruling), and the gate itself,
    `projects/Avalon/bin/lift.sh` † (Avalon's, not in this tree).

## feeds →
`INDEX.md` (the map) · `model.md` (dimensional standardization) · `CORWIN.md` +
co-author seeds · ccspt/ghostwheel consent seam · `labels.tsv` (machine mirror)

<!-- footer: minted by bin/ft1mt from conventions/house.env and conventions/FOOTERS.org; edit those, not this -->
*Version 0.2: edition revised from 0.1 on 2026-10-10; spine: 2026-07-02.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin; claude-opus-5-5)
<!-- /footer -->
