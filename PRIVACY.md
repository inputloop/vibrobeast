# Privacy Policy -- vibrobeast 1.2.62

*Minted 2026-10-18 by `bin/tp2mt` for this build and no other. Every sentence about what the servers
do was checked against their source when this was minted:*

- no server but llamabridge, tavernface and gwstatus opens a network connection: none imports a network library
- no server but llamabridge, tavernface and gwstatus makes a socket; socket is used only to read this machine's name
- llamabridge (Llama Bridge) is off until you set llamabridge.on, or LLAMABRIDGE_ON=1; while off it answers one tool and sends nothing
- when on, llamabridge sends the prompts Claude delegates to the Ollama server at OLLAMA_HOST (default http://127.0.0.1:11434, this computer)
- when on, llamabridge keeps its log in ~/.mentcached/llama-bridge.db
- tavernface (Tavern) is off until you set tavern.on, or TAVERN_ON=1; while off it answers one tool and sends nothing
- when on, tavernface runs only Tavern's own MCP mode (tavern.py mcp), not a Tavern node
- in MCP mode Tavern talks only to the Tavern node already running on this computer (127.0.0.1); that node, which you run yourself, copies what is posted to every member of your tavern
- c4face (C4's own server) is off until you set c4.on, or C4_ON=1; while off it answers one tool and runs nothing
- when on, c4face runs C4's own server (mcp/c4-mcp.js in your own C4 folder, with node) only after checking, at every start, that it and the files it loads ask for no module but readline and path, and reach no process, file or network power another way it can read; if one does, it starts nothing and says which. This check is a tripwire for an honest change, not a fence: no reading of JavaScript can be sure, which is why c4face is off until you ask
- c4face writes no file; the guard above refuses to start a C4 server that asks for the file module
- gwstatus (the ghostwheel status icon) is off until you set gw.on, or GW_ON=1 (the extension's Ghostwheel status door); while off it answers one tool and sends nothing
- when on, gwstatus connects only to the hosts you list (the hosts setting and its hosts register), by ssh, munin-node or http(s), to ask how they are (reachable, load, disk)
- before gwstatus looks up a host's name, it asks you, unless you switched lookups off (then it never does) or to always
- before gwstatus trusts a host key it has not seen, it shows you the fingerprint and asks, unless you switched that off or to always; a fingerprint pinned in the host's row that does not match is always refused
- host keys gwstatus accepts are kept in ~/.mentcached/gw_known_hosts, never in your ~/.ssh/known_hosts
- gwstatus writes its picture and last answers beside the seat (~/.mentcached/gw-status.svg, gw-status.html, gw-last.json) and its hosts register and your answers there too (gw-hosts.tsv, gw-approvals.tsv)
- gwstatus never prints the default password or the API token; its tools say only whether each is set
- the key register is kept in ~/.mentcached/keys.tsv (VIBROBEAST_KEYS_FILE moves it); it names where each key lives, never a key
- a register row that holds a key itself, rather than naming where it lives, is refused
- the key tools say a key is set or not set, never its value
- key_run starts nothing on its first call: it returns a confirmation naming the key, the program and the folder, with your usage constraints, and runs only when called again with that confirmation's code -- or under a standing yes you wrote yourself (keys.standing)
- a standing yes (keys.standing) covers one key, one program and one host, changes only on your own turn, never covers a run with an option, and lets scp only push to that host; every run under it says so in its result
- keys.standing is read only from a row written on the keeper's own turn
- key_run starts only the programs a key allows (by default gh, git, glab, ssh, scp, npm or twine, as the key's service needs)
- key_run's output has the key's value replaced by [key NAME] before Claude sees it, in each way a program may spell it (slashes turned, backslashes doubled)
- when key_run hands a second key to a program (gh secret set), it goes to the program's input as bytes, never its arguments, and the confirmation names it with its own usage constraints
- git started with the ssh key is told its ssh is OpenSSH, whatever ssh.variant a gitconfig names
- the seat defaults to ~/.mentcached/seat (MENTCACHED_SEAT moves it)
- preferences are kept in ~/.mentcached/prefs.tsv (MENTCACHED_PREFS moves it)
- timings are kept in ~/.mentcached/stats/spans.tsv (MENTCACHED_STATS moves it)
- soft-skill use is counted in ~/.mentcached/softskills-usage.tsv
- the usage record (the frame) is kept in ~/.mentcached/stats/fr, its column names in ~/.mentcached/stats/d/fr; MENTCACHED_FRAME moves it to a file you name, which is never created for you
- the usage record is off by default: nothing is written to it, and no file is made, until you set usage.capture on
- while usage.capture is off every writer of the usage record writes nothing and says so
- word_register writes one small file per word and leaf, <words root>/g/<word>/<leaf>, and never overwrites one (the words.root preference or C4_ROOT names the root)
- journal lines record this machine's name, the time, and who wrote them
- the persona server never opens a file whose name says SECRET
- skillx exchanges nothing: every tool refuses and says what is missing
- the extension's author, on its settings page, is Corwin and Bryant (BryantAndCorwin@inputloop.com)

## What leaves your computer

Nothing, by the plugin's own doing, unless you turn on llamabridge, tavernface or gwstatus (Llama Bridge,
Tavern and the ghostwheel status icon; Llama Bridge and Tavern began in Bryant Frankford's workshop). With llamabridge on, the prompts Claude delegates go
to the Ollama server at OLLAMA_HOST: by default on this computer (127.0.0.1:11434); point it at another
machine and they go there. With tavernface on, what Claude posts goes to the Tavern node you run on this
computer, and that node copies it to every member of your tavern: everything said there, DMs included,
is visible to every member. c4face is off until you turn it on; then it starts C4's own server from
your C4 folder only when that program and the files it loads pass its check (a tripwire, not a fence)
for network, process and file modules, and it reads and writes nothing itself. With gwstatus on,
it connects only to the hosts you list, by ssh, munin-node or http(s), to ask how they are; it asks you
before it looks up a name or trusts a new host key, unless you said always, and with basic
authorization it sends your user name and password to that host and nowhere else. The memory
server's key_run is a door of another kind: it opens no connection itself, but on your yes to a
confirmation that names the key, the program and the folder and reads your usage constraints back,
it starts that one program (gh, git, ssh and the like) with the key bound, and the program goes
where you sent it. A standing yes you write yourself (keys.standing: one key, one program, one host)
lets such a run go without asking each time; it never covers a run with an option, scp under it
only pushes, and each run under it says so in its result. The other servers make no network connections. What Claude itself sends
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
| usage record (the frame) | `~/.mentcached/stats/fr`, column names in `~/.mentcached/stats/d/fr` | `MENTCACHED_FRAME` | only while `usage.capture` is on (off by default). Two counts only, each with a date: the token count when a span starts, and the count after each prompt. While it is on, the record also mirrors each preference you set (key and value) and each question logged with `question_log` (the question's words). FRAME.md, in the plugin, says each column in words |
| key register | `~/.mentcached/keys.tsv` | `VIBROBEAST_KEYS_FILE` | the keys you keep, by name: kind, where each lives (never the key), what it is for, the programs it may start, and your usage constraints |
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

The usage record is yours to switch and to remove. To stop it, set `usage.capture` off (`pref_set`);
nothing more is written. To remove it, delete `~/.mentcached/stats/fr` and `~/.mentcached/stats/d/fr`
(or the file `MENTCACHED_FRAME` names); with capture off they are not made again.

## Words we use (the same block in the Terms and in the Privacy Policy)

- **plugin** -- vibrobeast, the bundle you install into Claude Desktop or Claude Code.
- **server** -- one of its six programs that answer Claude's tool calls on your computer: mentcached, persona, skillx, llamabridge, tavernface and c4face (llamabridge, tavernface and c4face are off until you turn them on; c4face then runs C4's own server from your C4 folder when it finds one).
- **seat** -- the folder where mentcached keeps notes it writes for you (default `~/.mentcached/seat`).
- **journal** -- the append-only record beside each note: what changed, when, on which machine, by whom.
- **shelf** -- folders of finished work the persona server reads but never writes, and the publication shelf (`<H>:/pub`).
- **persona** -- a sheet that says what a character, place, or person-model is, by its own first lines.
- **filter** -- anything that keeps something from being read, written, or shown. Every filter is named in the Privacy Policy; one that is not named does not exist.
- **you** -- the person running the plugin on their own computer.

This policy is part of our shared writing, under CC BY-SA 4.0 like the rest of it
(see TERMS-OF-SERVICE.md).
