# vibrobeast

vibrobeast is a plugin for Claude Desktop and Claude Code. It gives Claude a memory that keeps its
history (a note is never overwritten, only followed by a newer one), a shelf of persona sheets to
read, a set of skills, and switches you change by asking in plain words. It runs on your computer
and, by its own doing, sends nothing anywhere unless you turn on a part that says it sends; what
Claude reads from it becomes part of your conversation, as with any tool.

It comes from one collection that Corwin Brust and Bryant Frankford keep and share together:
the memory servers and skills from Corwin's workshop, and Tavern and Llama Bridge, which began in
Bryant's. We offer all of it on the same terms (`TERMS-OF-SERVICE.md`, beside this README).

One plugin, seven small programs (its servers), and the skill garden. The words this README
uses come first, then the table of servers.

## Words this README uses

This README is written for someone new to the project, and
the project's own words in it are explained in `GRAMMARY.md` (the glossary, beside this README). `FRAME.md`,
also beside it, says in words what the opt-in usage record holds. The words you meet first:

- **A server** is one small program on your computer that Claude can call for help. Claude and the
  servers speak **MCP** (the Model Context Protocol, the way Claude asks a program to do something);
  these servers speak it over **stdio**, the program's own input and output, so no network port is
  opened for it.
- **`<your-root>`** is wherever you keep a checkout of the source tree this was minted from (public
  at `code.bru.st/corwin/vibrobeast`), if you keep one at all -- nothing here needs it.
- **"In the source tree, not shipped"** marks a tool this README mentions that lives in that
  source tree, or in the C4 tree (Corwin's folder of models and tools), and is NOT in this
  plugin. You can run everything else from the directory this README is in.
- **A switch** is a preference you change by asking Claude in plain words ("turn on the local
  model"); Claude calls `pref_set` for you. Nothing is edited by hand. The table near the end lists
  every switch and its default.
- **Restart the plugin** means: quit Claude completely and open it again (in Claude Code, end the
  session and start `claude` again). Turning the plugin off and back on, where the app lists your
  plugins, does the same. A server reads its on/off switch only when it starts, so a switch whose
  name ends in `.on` takes effect after a restart.
- **The keeper** is the one person an install is for, whose say decides what is kept about people.
  The server reads the keeper's name from the Keeper field (`MENTCACHED_KEEPER`); when that is empty,
  from this computer's account name (unless it is a generic one such as `user`); else the keeper is
  `corwin` (Corwin Brust: this began as his own install, and his name is the default until you set
  yours). Nothing in the seat names the keeper: a row only the keeper may write counts only when the
  keeper wrote it, so it cannot also decide who the keeper is.
- **`people.named` starts as `corwin`.** The server keeps preferences about a person (rows named
  `person.<name>.*`) only for the names in `people.named`. To have yours kept, ask Claude to "set
  people.named to" your name. In this build that change is accepted only on the keeper's turn, so
  on a fresh install first ask Claude to help you set `MENTCACHED_KEEPER` to your name where the app
  starts the plugin (the same place as the seat variables below), restart the plugin, then ask
  again. If the change is refused, Claude is told why, in words, and can tell you.
- **A persona** is a named voice Claude can take on: a written sheet says how it speaks, what it
  cares about and what it will not do (GRAMMARY: "persona sheet"). With no sheet, the `persona`
  server answers in a plain default voice.
- **The seat** is the folder that holds your memory notes; **the garden** is the set of skills this
  plugin carries; **to mint** is to build this plugin from the source tree. Each has its GRAMMARY
  entry.
- **An unsigned build** is explained under Verify, below.

## The servers

| server | state | what it is |
|---|---|---|
| `mentcached` | always on | the memory seat, served. Archive-only notes, a first-seen/last-cited spine, citation pressure, semaphores, and a mode word (`SEATED` / `JAILED` / `NOTVISIBLE`) on every single answer. |
| `persona` | always on | persona sheets. A persona is a named voice Claude can take on, written down as a sheet (see Words, above). This server lists and reads the sheets, says which one applies (`persona_resolve`; with none, a plain default voice) and keeps the ledger of which sheet can check which. `bin/mt1pl` (in the source tree, not shipped) resolves the same order in shell. |
| `skillx` | **refuses** | party-to-party skill exchange. Every tool refuses and names its blocker. This is on purpose: an absent server teaches a caller nothing, a refusing one is a checkable statement of what the design owes. |
| `llamabridge` | **off** until you ask Claude to set `llamabridge.on` | Llama Bridge: hands small jobs to models on an Ollama server you choose. While off, one tool says so. |
| `tavernface` | **off** until you ask Claude to set `tavern.on` | Tavern, a common room for people and agents. While off, one tool says so and nothing is sent. This is **stock Tavern 2.3.1** as Bryant Frankford published it, byte for byte: it has no garden-pony tool registry (`tavern_tools`) and does not mark receipt lines an agent typed itself. That patched build (2.3.1+gp) lives in `projects/garden-pony` on Corwin's machine now, and at github.com/inputloop/tavern once published. |
| `c4face` | **off** until you ask Claude to set `c4.on` | C4's own MCP server, run with node from YOUR C4 folder (nothing of C4 is copied in). It finds both by itself, and checks C4's code at every start (a tripwire, not a fence: it refuses code that asks for a network, process or file module). While off, or when anything is missing, one tool, `c4_status`, says what and how to fix it by asking Claude (`c4.on`, `c4.root`). |
| `gwstatus` | **off** until you ask Claude to set `gw.on` | the ghostwheel status icon: asks your listed hosts how they are (reachable, load, disk) and draws a letter made of small letters, one per host, as an SVG beside the seat. It asks before looking up a name or trusting a new host key, unless you said always; host keys go to its own known-hosts file. |

## Skills that fire broadly -- read before you install

These skills say, in their own description, that they engage on most prompts
(each one's `skills/NAME/SKILL.md` says what it does; `GRAMMARY.md` has an entry
for `altorewired`):

- `altorewired`
- `token-optimizer`

In your shop that is yours to decide, not ours. Before you install, you can remove
their folders from `skills/`; after you install, ask Claude not to use them until
you choose to opt in. Our own gate holds an import like this at the
receiving door: `sh skills/candor-gate/scripts/candor_gate.sh skills/NAME` reads
HOLD on its engagement check; `--travel` is the sender's read, which says it and
sends it.

## Install

Claude Code, in one step (Claude Code 2.1.275 or later):

    /plugin install vibrobeast --marketplace inputloop/vibrobeast

or, on any version, `/plugin marketplace add inputloop/vibrobeast` and then
`/plugin install vibrobeast@inputloop`. Claude Desktop: use the extension
(`vibrobeast.mcpb`) with the skills-only plugin `vibrobeast-skills` beside it,
not this plugin; the two would run the same memory server twice. Nothing else is needed to start: the
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
        carries only a hash manifest (it proves the bytes, not who made them);
        TREE CHANGED or SIGNATURE FAILED if something is wrong -- or, for
        TREE CHANGED only, if this is an unsigned build (next paragraph)

**An unsigned build.** A build its release notes call "unsigned" carries skills that changed after
Corwin last signed them. For those skills `sh check.sh` still says every byte matches MANIFEST
(the files are the ones this build shipped), but `skill-sign.sh verify` says TREE CHANGED, because
the signature is for the earlier text. That is expected for an unsigned build and is not a sign of
tampering; it does mean no author's signature vouches for the changed skills. If you need that
proof, wait for the signed build; if the byte check is enough for you, install it.

## What it reads and writes

`PRIVACY.md` beside this README is the full list, minted for this build from
claims checked against the servers' source: every file the servers write,
where, what moves it, and every filter by name. In short: while their switches
are off (the default) the servers make no network connections; Tavern, Llama
Bridge and the ghostwheel status icon reach only what you name once you switch
them on. They write under `~/.mentcached/` unless you point them
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

**The one that might:** `.mcp.json` launches the servers with `python3`. If
that name is not an interpreter on the machine that runs the plugin (on
Windows, `python3` can be a Store alias that never starts), the servers do not
start. What to do, with no source checkout: install Python 3.10 or newer from
python.org (on Windows, tick "Add python.exe to PATH" in its installer, then
search Windows Settings for "App execution aliases" and turn off the `python`
and `python3` entries that open the Store), restart the plugin, and run
`sh check-interpreter.sh` to see that it starts. If you keep a checkout, you can
instead re-mint from `<your-root>` naming the interpreter:

    python -m polygram dist --format plugin --python /mingw64/bin/python3

or let the minting host pick one for you:

    python -m polygram dist --format plugin --python auto

which runs `python3`, then `python`, then `py -3`, and bakes in the first that
actually starts and reports 3.10+. It probes by RUNNING each one, because a name
being on PATH is not the same as it being python -- on Windows `python3` is
often an App Execution Alias that exits without ever being an interpreter.

Do not add an `env` block to `.mcp.json`: the seat variables below are read from the environment the
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

## Time and tokens -- span_start / span_mark / span_stop / span_report, and question_log

`question_log` writes one `gauge` row in the frame (FRAME.md, beside this README) when Claude
puts a question to you: whether one or two were asked at once, and the guess behind that. It
writes only while `usage.capture` is on.

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
exist -- a path you named is never created). `sh bin/sp1rp` (in the source
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
(the usage ledger); `bin/ss2gr` (in the source tree, not shipped) reads it and reports which soft
skills are earning a place in the garden. Skills stay soft until they show
use; graduation is by hand, never by the build.

## Words -- word_where / word_register

Corwin put the need in one line: *"We have defined memory, maybe we need words."* So
`word_where NAME` answers where
a word's meaning lives: the C4 word-path registry (`g/<word>/<leaf>`, the leaf
named for the nearest well-known place toward `m/t`: t z s e d g f c h m) plus a
live check of the short list of places one must always look (the register
table, scalars, terms of art, the G graphs, facts, context). Nothing on the
list holds it -> the answer says PROPER GAP, with every place named.
`word_register` writes one leaf and never overwrites; a second leaf on a word
is a seam, kept. The root: `words.root` preference, else `$C4_ROOT`, else
`/f/claude/c4` (Corwin's layout), else `~/mnt/c4`; with none of them there,
both tools say no root was found and write nothing. The POSIX twin is
`c4/bin/wd1nn` / `wd2nn` (in the source tree, not shipped): two readers over
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
        every server (seven) and every tool it offers, started the way the app starts them

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
`sh bin/gd1ck --record` (in the source tree, not shipped) runs every suite in
that repo and the C4 tree, lints and sizes every skill, checks this plugin's bytes and gauges the
garden, then records each result. Nothing here writes a row from a chat.

## The switches -- every preference key, and its default

Each switch is changed by asking Claude (`pref_set KEY VALUE`, or `pref_unset KEY` to go back to the
default); nothing here is edited by hand. This table is minted from the keys the server knows
(`polygram/mcp/prefs.py`, `KNOWN`), so it lists exactly what this build reads.

| key | default | what it changes |
|---|---|---|
| `freshness.auto` | `on` | seat_mode and span_start report whether the installed plugin is the shelf's mint |
| `freshness.shelf` | (none) | the minted tree on the shelf; else $POLYGRAM_DIST, else a guess beside the seat |
| `softskills.auto` | `on` | seat_mode and span_start report how many soft skills are loadable, and from where |
| `softskills.roots` | (none) | SOFT-SKILLS roots, os.pathsep-separated; else $SOFT_SKILLS, else ~/.mentcached/SOFT-SKILLS and <seat>/../SOFT-SKILLS |
| `steward.auto` | `on` | nongnu-steward: ns1op runs its header + ledger audit at session open in a tree carrying .nongnu-steward |
| `persona.sheets` | (none) | folders holding persona sheets and person models, os.pathsep-separated, earlier wins a name; a file is a sheet by what its own first lines say (actor:, a sheet heading, or model front matter); else $PERSONA_SHEETS, else guessed from softskills.roots and words.root |
| `words.root` | (none) | the C4 root the word-path registry (word_where / word_register) reads: else $C4_ROOT, else /f/claude/c4, else ~/mnt/c4 -- whichever carries m/t |
| `words.kv` | `offer` | words: whether word_register also files a word's keeper row in C4's k/v (whose word it is, whether it is settled): offer writes the row when a kind is given, require refuses a word with no kind, off never writes k/v |
| `llamabridge.on` | `off` | llamabridge: off until set to on; when on, prompts Claude delegates go to the Ollama server at OLLAMA_HOST (default http://127.0.0.1:11434, this computer). Restart the plugin after changing it (the README's Words say how) |
| `tavern.on` | `off` | tavern: off until set to on; when on, Claude can read and post in your Tavern rooms, and what is posted is copied to every member machine's disk. Restart the plugin after changing it (the README's Words say how) |
| `tavern.as` | `claude` | tavern: the agent name Claude uses in the Tavern (Tavern adds this machine's address, e.g. claude-192.0.2.7, a documentation address). When unset, it is the agent already registered in the Tavern for this machine's person, else claude |
| `tavern.data` | (none) | tavern: the Tavern data folder, when it is not where Tavern's installer or a download would put it; else $TAVERN_DATA, else found by itself |
| `tavern.face` | (none) | tavernface: which tavern.py speaks for a Tavern that runs the garden-pony build. Empty: the stock 2.3.1 this plugin carries. sha256:<the whole hash>: this Tavern's own tavern.py, imported only while its bytes match that hash (the status words say the hash to pin). bundled: the stock copy, on purpose. A pin is code the plugin will run, so pref_set asks for a code first (2026-10-26; the 10-19 audit's item 4) |
| `gw.on` | `off` | gwstatus: off until set to on; when on, Claude can ask your listed hosts (GW_HOSTS, the hosts register) how they are and draw the ghostwheel status icon, asking first before any name lookup or new host key unless told always. Restart the plugin after changing it |
| `c4.on` | `off` | c4face: off until set to on; when on, Claude can use your C4 work surface by running C4's own server (mcp/c4-mcp.js in your C4 folder) with node, after a check at every start. Restart the plugin after changing it (the README's Words say how) |
| `c4.root` | (none) | c4face: your C4 folder (the one holding mcp/c4-mcp.js), when it is not found by itself; else $C4_ROOT, else words.root, else a c4 folder near the seat or the shelf, else the usual places |
| `steward.canon` | `on` | nongnu-steward: ns1op reports the canon pins' age and the check command at session open; it never fetches unasked |
| `usage.capture` | `off` | usage capture: off until set to on; when on, span_start writes the token count at start and each new prompt writes the count after it, as rows in the frame (~/.mentcached/stats/fr; FRAME.md, beside this README, says each column in words). Those start and prompt rows hold two counts and a date, nothing else: no labels, no notes, no content. While it is on, the frame also mirrors each preference you set (key and value) and each question logged with question_log (its words); PRIVACY.md lists all of it. What the AI vendor sees is unchanged: the counts are ones the model already reports |
| `tone.dial` | `0/0, 0/0` | tone: where the voice sits on two axes, answer length and narration, as signals seen / signals total on each; the default is the origin (no signals yet), which is plain voice |
| `tone.show` | `words` | tone: how the tone reading is shown to you: words (a plain sentence, no numbers) or numbers |
| `persona.on_threshold` | `off` | persona: what happens when someone crosses a threshold (used twice outside a test run; cited twice in seat notes; shipped through a cut with their credit): off (nothing; the default, his standing rule), propose (persona_list names the crossing and asks, in words), draft (persona_list names it and a draft may be written to the holding shelf ~/.mentcached/seat/persona/drafts, marked not-his-instruction and kept out of the index). No value mints a sheet: saying yes to a proposal or a draft is the instruction his rule asks for (2026-10-14) |
| `keys.standing` | (none) | key_run: standing yeses, so routine runs on the keeper's own hosts need no confirmation each time. Entries KEY PROGRAM TARGET, separated by ';' (e.g. 'ssh ssh vibrobeast@gw33.bru.st; ssh scp vibrobeast@gw33.bru.st'). ssh: the host argument is exactly TARGET. scp: pushes to TARGET only (a pull could write this computer's files). git: TARGET is a folder, and only `git pull` (run fast-forward only) or `git fetch`, alone, run in exactly that folder (e.g. 'ssh git /home/you/projects/c4-draw-kiosk'). Any argument starting with - still asks. Every standing run says so in its result. Only the keeper's own turn changes it, and only with a code the person saw beside the row (pref_set asks first) |
| `people.named` | (none) | the people whose person.<name>.* rows this server keeps, besides the keeper, who is always one of them: the participants the keeper named, comma-separated. Only the keeper's own turn changes it, and only with a code the person saw beside the row (pref_set asks first) |

## The floor -- the skills every edition carries

The floor is eight skills, carried by every sized edition whatever its size (`polygram/editions.py`, `FLOOR`): `mentat-skill`, `principles`, `skilltank`, `sandboxer`, `lens`, `garden-usage`, `consent-gate`, `drift`.

## Licence

Every file not otherwise marked is GPL-3.0-or-later (`COPYING`), or at your choice LGPL-3.0-or-later; see
TERMS-OF-SERVICE.md for the writing. Free software: you may run, study, share
and improve it. Corwin Brust and Bryant Frankford offer it together; the
Terms say in full what goes with each part.
