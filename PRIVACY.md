# Privacy Policy -- vibrobeast 1.0.4

*Minted 2026-10-08 by `bin/tp2mt` for this build and no other. Every sentence about what the servers
do was checked against their source when this was minted:*

- no server but llamabridge and tavernface opens a network connection: none imports a network library
- no server but llamabridge and tavernface makes a socket; socket is used only to read this machine's name
- llamabridge (Bryant's Llama Bridge) is off until you set llamabridge.on, or LLAMABRIDGE_ON=1; while off it answers one tool and sends nothing
- when on, llamabridge sends the prompts Claude delegates to the Ollama server at OLLAMA_HOST (default http://127.0.0.1:11434, this computer)
- when on, llamabridge keeps its log in ~/.mentcached/llama-bridge.db
- tavernface (Bryant's Tavern) is off until you set tavern.on, or TAVERN_ON=1; while off it answers one tool and sends nothing
- when on, tavernface runs only Tavern's own MCP mode (tavern.py mcp), not a Tavern node
- in MCP mode Tavern talks only to the Tavern node already running on this computer (127.0.0.1); that node, which you run yourself, copies what is posted to every member of your tavern
- c4face (C4's own server) is off until you set c4.on, or C4_ON=1; while off it answers one tool and runs nothing
- when on, c4face runs C4's own server (mcp/c4-mcp.js in your own C4 folder, with node) only after checking, at every start, that it and the files it loads ask for no module but readline and path, and reach no process, file or network power another way it can read; if one does, it starts nothing and says which. This check is a tripwire for an honest change, not a fence: no reading of JavaScript can be sure, which is why c4face is off until you ask
- c4face writes no file; the guard above refuses to start a C4 server that asks for the file module
- the seat defaults to ~/.mentcached/seat (MENTCACHED_SEAT moves it)
- preferences are kept in ~/.mentcached/prefs.tsv (MENTCACHED_PREFS moves it)
- timings are kept in ~/.mentcached/stats/spans.tsv (MENTCACHED_STATS moves it)
- soft-skill use is counted in ~/.mentcached/softskills-usage.tsv
- word_register writes one small file per word and leaf, <words root>/g/<word>/<leaf>, and never overwrites one (the words.root preference or C4_ROOT names the root)
- journal lines record this machine's name, the time, and who wrote them
- the persona server never opens a file whose name says SECRET
- skillx exchanges nothing: every tool refuses and says what is missing

## What leaves your computer

Nothing, by the plugin's own doing, unless you turn llamabridge or tavernface on. With llamabridge on, the prompts Claude delegates go
to the Ollama server at OLLAMA_HOST: by default on this computer (127.0.0.1:11434); point it at another
machine and they go there. With tavernface on, what Claude posts goes to the Tavern node you run on this
computer, and that node copies it to every member of your tavern: everything said there, DMs included,
is visible to every member. c4face is off until you turn it on; then it starts C4's own server from
your C4 folder only when that program and the files it loads pass its check (a tripwire, not a fence)
for network, process and file modules, and it reads and writes nothing itself. The other
servers make no network connections. What Claude itself sends
to Anthropic when it calls a tool -- the tool's answer, as part of the conversation -- is governed by
Anthropic's own terms and privacy policy, not by this one.

## What is kept, and where

| store | default place | moved by | what is in it |
|---|---|---|---|
| seat | `~/.mentcached/seat` | `MENTCACHED_SEAT` | notes written at your or Claude's request, each with its journal |
| preferences | `~/.mentcached/prefs.tsv` | `MENTCACHED_PREFS` | settings you chose (`pref_set`) |
| timings | `~/.mentcached/stats/spans.tsv` | `MENTCACHED_STATS` | how long marked pieces of work took |
| soft-skill use | `~/.mentcached/softskills-usage.tsv` | `MENTCACHED_SOFTSKILLS_USAGE` | which soft skills were read, and when |
| persona journal | `~/.mentcached/seat/persona` | `PERSONA_ROOT` | changes made through the persona server |
| words | `<words root>/g/<word>/<leaf>` -- the C4 tree when one is found | `words.root` preference, `C4_ROOT` | one file per word you registered (`word_register`): its neighbour, meaning, date and who |
| llamabridge log | `~/.mentcached/llama-bridge.db` | (none) | when llamabridge is on: each delegation, its model, timing and result |

Each journal line records the machine's name, the time, and who wrote it. That is how "who said what"
is answered: by the record, not by marks in the text.

## Filters -- every one, by name

- **SECRET files.** The persona server never opens a file whose name contains SECRET.
- **skillx.** Exchanges nothing with anyone; every call is refused, and the refusal says what is missing.
- **The leak check** (`pb1ck`, a publishing tool beside the plugin, not a server). Before anything goes
  on the publication shelf it looks for this machine's paths and the names you listed in
  `.c4/leakwords`, reports each hit by line, and prints *(withheld)* instead of the name itself.
- **No other filter.** Nothing rewrites, censors, or drops words in your notes, sheets, or books.

## Your choices

Move any store with its variable. Delete any of them; the plugin starts fresh. Read every one -- they
are plain text.

## Words we use (the same block in the Terms and in the Privacy Policy)

- **plugin** -- vibrobeast, the bundle you install into Claude Desktop or Claude Code.
- **server** -- one of its six programs that answer Claude's tool calls on your computer: mentcached, persona, skillx, llamabridge, tavernface and c4face (llamabridge, tavernface and c4face are off until you turn them on; c4face then runs C4's own server from your C4 folder when it finds one).
- **seat** -- the folder where mentcached keeps notes it writes for you (default `~/.mentcached/seat`).
- **journal** -- the append-only record beside each note: what changed, when, on which machine, by whom.
- **shelf** -- folders of finished work the persona server reads but never writes, and the publication shelf (`<H>:/pub`).
- **persona** -- a sheet that says what a character, place, or person-model is, by its own first lines.
- **filter** -- anything that keeps something from being read, written, or shown. Every filter is named in the Privacy Policy; one that is not named does not exist.
- **you** -- the person running the plugin on their own computer.
