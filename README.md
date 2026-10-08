# vibrobeast

One plugin, six stdio MCP servers, and the skill garden.

| server | state | what it is |
|---|---|---|
| `mentcached` | always on | the memory seat, served. Archive-only notes, a
  first-seen/last-cited spine, citation pressure, semaphores, and a mode word
  (`SEATED` / `JAILED` / `NOTVISIBLE`) on every single answer. |
| `persona` | always on | persona sheets. Row 0 of `bin/mt1pl`'s resolution
  order (in the author's tree, not shipped), which that tool has been
  reserving since 2026-09-13. |
| `skillx` | **refuses** | party-to-party skill exchange. Every tool refuses
  and names its blocker. This is on purpose: an absent server teaches a caller
  nothing, a refusing one is a checkable statement of what the design owes. |
| `llamabridge` | **off** until you ask Claude to set `llamabridge.on` | Bryant's Llama
  Bridge: hands subtasks to local Ollama models. While off, one tool says so. |
| `tavernface` | **off** until you ask Claude to set `tavern.on` | Bryant's Tavern, a common
  room for people and agents. While off, one tool says so and nothing is sent. This is his
  **stock Tavern 2.3.1**, byte for byte: it has no garden-pony tool registry (`tavern_tools`) and
  does not mark receipt lines an agent typed itself. That patched build (2.3.1+gp) lives in
  `projects/garden-pony` on the author's machine now, and at github.com/inputloop/tavern once
  published. |
| `c4face` | **off** until you ask Claude to set `c4.on` | C4's own MCP server, run with
  node from YOUR C4 folder (nothing of C4 is copied in). It finds both by itself, and checks
  C4's code at every start (a tripwire, not a fence: it refuses code that asks for a network,
  process or file module). While off, or when anything is missing, one tool, `c4_status`,
  says what and how to fix it by asking Claude (`c4.on`, `c4.root`). |

Two words used below. **`<your-root>`** is wherever you keep a checkout of the
source tree this was minted from (public at `code.bru.st/corwin/vibrobeast`),
if you keep one at all -- nothing here needs it. **"In the author's tree, not
shipped"** marks a tool this README mentions that lives in that source tree or
in the author's C4 tree and is NOT in this plugin; you can run everything else
from the directory this README is in.

## Install

Claude Desktop: upload `vibrobeast.plugin` where the app installs plugins.
Claude Code: `claude plugin install` (the form it takes depends on your
version; `claude plugin --help` says). Nothing else is needed to start: the
servers need a Python 3.10+ the app can launch (see the next section), and the
checks below need `sh`, `sha256sum` (or `shasum`) and, for signatures, `gpg`.

## Verify

The skills are signed with Corwin Brust's OpenPGP key, fingerprint

    ECE7 7CF4 17C7 6C1A CFCE  7C2B 5B61 3551 1580 F007

Get the key from keys.openpgp.org (search that fingerprint), or from the
source tree as `skills/ECE77CF417C76C1ACFCE7C2B5B6135511580F007.asc`. Import
it, and check that the fingerprint gpg prints is the one above:

    gpg --import ECE77CF417C76C1ACFCE7C2B5B6135511580F007.asc
    gpg --fingerprint ECE77CF417C76C1ACFCE7C2B5B6135511580F007

Then, from the directory this README is in:

    sh check.sh
        every shipped byte matches MANIFEST (no gpg needed)
    sh skills/skill-sign/scripts/skill-sign.sh verify skills/NAME
        "signature valid" for a signed skill; UNVERIFIED-AUTHOR for one that
        carries only a hash manifest (it proves the bytes, not the author);
        TREE CHANGED or SIGNATURE FAILED if something is wrong

## What it reads and writes

`PRIVACY.md` beside this README is the full list, minted for this build from
claims checked against the servers' source: every file the servers write,
where, what moves it, and every filter by name. In short: the servers make no
network connections; they write under `~/.mentcached/` unless you point them
elsewhere, and `word_register` writes under a words root only if one is found.
`TERMS-OF-SERVICE.md` has the licences and the words.

## Before the first run -- what has actually gone wrong, and the one line that might

Two things have stopped this plugin's servers on a real desktop, one of them
for a week. Both are checked by `sh check-interpreter.sh`, and it names which.

**The one that did it (2026-09-16 .. 09-23):** an `env` block naming
`PYTHONPATH`. Claude Desktop refuses to prepare a plugin server whose `env`
declares that name -- its log says `failed to build host proxy target: env
declares reserved variable name "PYTHONPATH"` -- and the only thing a reader
sees is `not_started / could_not_prepare`. This plugin's `.mcp.json` now has
no `env` key at all: each server starts through `servers/launch.py`, named as
`${CLAUDE_PLUGIN_ROOT}/servers/launch.py` in `args`, and the launcher puts its
own directory on `sys.path` and sets `sys.dont_write_bytecode` itself.

**The one that might:** `.mcp.json` launches the servers with ``python3``. If
that name is not an interpreter on the machine that runs the plugin (on
Windows, `python3` can be a Store alias that never starts), re-mint from
`<your-root>` with

    python -m polygram dist --format plugin --python /mingw64/bin/python3

or let the minting host pick one for you:

    python -m polygram dist --format plugin --python auto

which runs `python3`, then `python`, then `py -3`, and bakes in the first that
actually starts and reports 3.10+. It probes by RUNNING each one, because a name
being on PATH is not the same as it being python -- on Windows `python3` is
often an App Execution Alias that exits without ever being an interpreter.

Or edit the three `command` lines in `.mcp.json` by hand. Do not add an
`env` block back: the seat variables below are read from the environment the
app launches the server in, and a subprocess inherits that either way.

## Pointing the seat at your memory

**You do not have to set anything to start.** With nothing set, notes go to
`~/.mentcached/seat`, and your first note creates it. Ask `seat_mode` at any
time and it will tell you the exact directory it is using and who chose it.

Three variables change that:

    MENTCACHED_SEAT    where your notes live
    MENTCACHED_JAIL    a project-local fallback, used only if the seat is
                       unreachable and then said out loud on every answer
    MENTCACHED_BY      who is writing and citing (default: `claude`)

There is one rule worth knowing, because it will look like rudeness the first
time it happens:

> **A path this server chose, it may create. A path YOU named, it never will.**

If you set `MENTCACHED_SEAT` to somewhere that does not exist, you get
`NOTVISIBLE` and a refusal, not a new empty store. That is on purpose. From
inside, a first run and a typo look identical — and if it guessed wrong it
would serve you an empty directory as though it were your memory. So it stops
and shows you the path it was given. Check the spelling, or use `seat_open`
with `create: true` to say you meant it.

`MENTCACHED_BY` should be stable. It is not a display name: buoyancy ranks each
note against the other notes the same party has cited, so if this value changes
every time you restart, every note becomes its own little world and the ranking
stops meaning anything.

## Time and tokens -- span_start / span_mark / span_stop / span_report

Four tools on `mentcached` keep a ledger of how long each piece of work took and
what it cost. The discipline is one line: **call `span_start` when a piece of
work begins and `span_stop` when it ends, passing the token budget you can see
each time.** Time is the server's (host clock, UTC, stamped on arrival --
nothing can backdate a row). Tokens are yours to report: an MCP server cannot
see the model's usage, so pass `tokens_left` -- the running figure your harness
shows you -- and the server subtracts. Leave it out and the span reports time
only, in words. `span_mark` is a checkpoint between steps; `span_report` is the
rollup (per span, per label, in all, and what is still open).

The ledger is one append-only TSV, one row per event, never rewritten:
`~/.mentcached/stats/spans.tsv` (or `$MENTCACHED_STATS`, which must already
exist -- a path you named is never created). `sh bin/sp1rp` (in the author's
tree, not shipped) reads the same file with awk, so the report can be checked
in a second language.

## Am I running the shelf's mint? -- plugin_freshness

The pipe from the shelf (`dist/vibrobeast` in the workspace) to this app is a
manual upload, by your hand, on purpose. `plugin_freshness` (on `mentcached`)
makes the question "did anything change that I need to reinstall for?" a call:
it compares the MANIFEST of the plugin the server is running from with the
shelf's (`shelf` argument, or `$POLYGRAM_DIST`), and answers CURRENT / BEHIND /
UNKNOWN with the files that would change, sorted into servers, skills (by name)
and other, and a one-line `reinstall:` verdict in words. Read-only; hashes
nothing. The same answer from a shell:

    python3 -m polygram.mcp.freshness --shelf dist/vibrobeast --installed <installed tree>
        (run in <your-root>)

## Soft skills -- the dynaloader, and the switches

`SOFT-SKILLS/<name>/SKILL.md` -- a folder per skill, the same frontmatter format
as an installed skill, under a root this server reads live: `soft_skills_list`
scans on every call and `soft_skill_read` returns the text. Nothing is minted,
signed, uploaded or installed for a soft skill to be usable; drop the folder in
and it is there on the next call. Roots: the `softskills.roots` preference, else
`$SOFT_SKILLS`, else `~/.mentcached/SOFT-SKILLS` (and `<seat>/../SOFT-SKILLS`); and,
read last whatever those say, the plugin's own `SOFT-SKILLS/` folder when it has one.

`pref_list` / `pref_set` are the switches (append-only, last row wins, says who
and why): `freshness.auto` and `softskills.auto` (both on by default) make
`seat_mode` and every `span_start` carry a `checks` panel -- is the installed
plugin the shelf's mint, and how many soft skills are loadable -- and
`freshness.shelf` / `softskills.roots` say where to look. The plugin's own
`SOFT-SKILLS/` folder is always read, after any root you set; set a root only
for soft skills you keep somewhere else:

    pref_set softskills.roots <your-root>/SOFT-SKILLS
    pref_set freshness.shelf  <your-root>/dist/vibrobeast

Every `soft_skill_read` appends one line to `~/.mentcached/softskills-usage.tsv`
(the usage ledger); `bin/ss2gr` (in the author's tree, not shipped) reads it and reports which soft
skills are earning a place in the garden. Skills stay soft until they show
use; graduation is by hand, never by the build.

## Words -- word_where / word_register

"We have defined memory, maybe we need words." `word_where NAME` answers where
a word's meaning lives: the C4 word-path registry (`g/<word>/<leaf>`, the leaf
named for the nearest well-known place toward `m/t`: t z s e d g f c h m) plus a
live check of the short list of places one must always look (the register
table, scalars, terms of art, the G graphs, facts, context). Nothing on the
list holds it -> the answer says PROPER GAP, with every place named.
`word_register` writes one leaf and never overwrites; a second leaf on a word
is a seam, kept. The root: `words.root` preference, else `$C4_ROOT`, else
`/f/claude/c4` (the author's layout), else `~/mnt/c4`; with none of them there,
both tools say no root was found and write nothing. The POSIX twin is
`c4/bin/wd1nn` / `wd2nn` (in the author's tree, not shipped): two readers over
one registry, and a test that they agree.

## The three rules this carries

1. **Nothing is overwritten, simplified or deleted.** A write mints a new
   generation beside the old ones. No code path opens an existing note for
   writing, and a test asserts that rather than a comment promising it.
2. **The index is a cache.** Every forward pointer rebuilds from the note files
   alone; every backward pointer is a hash chain in the bytes. Delete the index
   and run `seat_index`; nothing is lost. Tamper with a generation and every
   later `prev:` stops matching.
3. **The mode is always said out loud.** A write while `JAILED` is refused
   unless you ask for it by name, and an allowed one carries `mode: JAILED` in
   its front matter forever.

## Checking it yourself

Run these from the directory this README is in. Every one of them was once
printed here in a form that did not work, so each is written out in full:

    sh check.sh
        the shipped bytes match MANIFEST

    sh servers/bin/dl2-verify.sh --prove-red
        the second chain reader, made to fail on purpose

    perl servers/bin/dl2-verify.pl --prove-red
        the third chain reader, likewise

    python3 servers/launch.py --list
        the three servers and every tool they offer, started the way the app starts them

    python3 servers/launch.py --prove-red
        fire every refusal on purpose

    sh check-interpreter.sh
        will the interpreter named in .mcp.json start HERE, and is the env block clean

`PYTHONDONTWRITEBYTECODE=1` is not optional in the last two. Without it Python
leaves `.pyc` files inside the bundle, and the next `sh check.sh` reports them
as UNLISTED and tells you to treat a `.pyc` you did not put there as hostile —
which would be sound advice about a file you had in fact just put there
yourself.

The chain check exists twice -- once in Python, once in POSIX shell -- sharing
no code, no parser and no hash implementation. Only the agreement of two
independent readers is evidence; a single implementation checking itself can
only find the bugs it does not have.

## Using it -- the garden's test kit and its metrics

The `skill-metrics` skill in `skills/skill-metrics/` carries a small store of
what each shipped thing was last seen doing: one row per interesting event
(`ITEM STATE CUR LAST DATE NOTE`), one file per item holding its last STATE,
and content-keyed copies of the current and previous version. Its one
implementation is `skills/skill-metrics/scripts/sk2mt` (POSIX sh); its contract
is `skills/skill-metrics/SPEC.md`.

    sh skills/skill-metrics/scripts/sk2mt -C DIR say
        every item, one plain sentence each
    sh skills/skill-metrics/scripts/sk2mt -C DIR state -e '^gf-'
        a POSIX grep pattern over item names
    sh skills/skill-metrics/scripts/sk2mt -C DIR items --state RED
        which items are RED now (patterns match NAMES, never states)
    sh skills/skill-metrics/tests.sh --prove-red
        its suite, made to fail on purpose

`mentcached` also offers **`metrics_read`** (arguments: `view`, `names`,
`pattern`, `state`, and the grep flags), a read-only window on the same store. It runs `sk2mt` rather than parsing the store a second time, so it needs
two things from the environment the app launches it in:

    SKILL_METRICS_ROOT   the store directory (in <your-root>: its metrics/ folder).
                         Unset or missing answers NOTVISIBLE; nothing is created.
    SKILL_METRICS_SH     only if `sh` is not on that PATH -- on Windows, e.g.
                         <msys2-root>/usr/bin/sh.exe. Without an sh it refuses by name.

Rows are written on the host, by the run that measured them:
`sh bin/gd1ck --record` (in the author's tree, not shipped) runs every suite in
that repo and the C4 tree, lints and sizes every skill, checks this plugin's bytes and gauges the
garden, then records each result. Nothing here writes a row from a chat.

## Licence

Every file not otherwise marked is GPL-3.0-or-later (`COPYING`); see
TERMS-OF-SERVICE.md for the writing. Free software: you may run, study, share
and improve it.


## This copy starts its servers through cmd.exe (a Windows mint)

**Made for Windows only.** On macOS or GNU/Linux there is no cmd.exe, and none of this copy's
servers would start. Use the other build: `make dist` on a Windows machine mints it beside this
one, as `dist/posix/vibrobeast.plugin` (same plugin, its servers started with `python3`); on
macOS or GNU/Linux a plain `make dist` mints that shape by itself.

`.mcp.json` here starts each server as `cmd /d /c <plugin>\servers\launch.cmd NAME`, and
`servers\launch.cmd` finds a Python 3.10 or newer by itself, in this order: the
`VIBROBEAST_PYTHON` variable if you set one; `py -3`; `python3`, then `python`, on PATH (never
the Microsoft Store stub under `WindowsApps`); MSYS2's `C:\msys64\ucrt64`, `mingw64` and
`clang64`; then python.org installs under `%LOCALAPPDATA%\Programs\Python` and
`%ProgramFiles%`. Nothing in the JSON needs editing. It says on stderr which Python it chose (the
app keeps that in its log), and if it finds none, it says in one sentence what to install.

By hand, from this folder in a Command Prompt: `servers\launch.cmd --list`.

## Skills that fire broadly

These skills say, in their own description, that they engage on most prompts:

- `altorewired`
- `token-optimizer`

In your shop that is yours to decide, not ours: until you opt in, tell your agent
not to use them, or remove their folders from `skills/` before you install. The
author's own gate holds an import like this at the receiving door:
`sh skills/candor-gate/scripts/candor_gate.sh skills/NAME` reads HOLD on its
engagement check; `--travel` is the sender's read, which says it and sends it.
