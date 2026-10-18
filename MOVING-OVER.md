# Moving over, one server at a time

This is for anyone who adds MCP servers to Claude Desktop by hand, in `claude_desktop_config.json`, and installs
skills one `.skill` file at a time. Nothing here asks you to stop doing that. Each rung is optional, and you can
stop on any of them. Hand-written JSON stays a supported way to run every server here: it is the same servers,
reading the same settings, that the extension's settings page writes.

The rungs go servers first, skills last.

## Rung 0: see where you stand

    python tools/cd1ck.py

This reads your `claude_desktop_config.json` from its usual place, or a path you give it. It never writes it.
For each server it says one of three things:
- it is someone else's, and is left as it is;
- it is one of ours, and which settings it sets;
- it is started twice. For the memory seat, that is two writers on one store, and the one thing to fix.

It also lists which of our servers are not there yet.

## Rung 1: add one of our servers by hand

1. Clone this repository, or download it, anywhere you like.
2. Ask `cd1ck` for the entry, naming the server and the `plugins/vibrobeast` folder of your copy:

       python tools/cd1ck.py --entry persona --root C:\path\to\vibrobeast\plugins\vibrobeast --env MENTCACHED_KEEPER=YourName

3. Paste what it prints inside `"mcpServers": { ... }`, save, and restart Claude Desktop.

Then add the next one when you want it. A sensible order is:
1. `persona`, which reads persona sheets;
2. `mentcached`, the memory seat;
3. then any door you want.

Each door is off until its `_ON` variable is `1`, and says so when called.

| server | what it is | the settings it reads (`env`) |
|---|---|---|
| `persona` | persona sheets and bylines | `MENTCACHED_KEEPER`, `MENTCACHED_SEAT`, `PERSONA_SHEETS` |
| `mentcached` | the memory seat: notes, preferences, timings, the key register | `MENTCACHED_KEEPER`, `MENTCACHED_SEAT`, `VIBROBEAST_KEYS_FILE`, and the key fields |
| `llamabridge` | Llama Bridge: small jobs to an Ollama model | `LLAMABRIDGE_ON`, `OLLAMA_HOST` |
| `tavernface` | Tavern's own MCP mode, for a Tavern node on this computer | `TAVERN_ON`, `TAVERN_DATA`, `TAVERN_AS` |
| `c4face` | C4's own server, from your C4 folder | `C4_ON`, `C4_ROOT`, `MENTCACHED_SEAT` |
| `gwstatus` | the ghostwheel status icon | `GW_ON`, `GW_HOSTS`, and the other `GW_` fields |
| `skillx` | skill exchange between parties | none; it refuses every call for now, and says why |

If you already run Tavern or Llama Bridge from their own folders, keep doing so. `tavernface` and `llamabridge`
are only for when you would rather have them here, and only one copy of each should run.

## Rung 2: let the extension run them, if you want a settings page

Download `extension/vibrobeast.mcpb` and open it. Its settings page sets the same variables as the table above,
and Claude Desktop keeps passwords and tokens in your system's keychain.

**Then remove the hand entries for our servers.** The extension already runs all seven, and two copies of
`mentcached` would put two writers on one memory seat. `cd1ck` says so if both are there. Your own servers stay in
your JSON, untouched.

If you would rather keep editing JSON, stay on rung 1: it is the same servers with the same settings. The
extension is a convenience, not a requirement. Its stored settings are Claude Desktop's own files, and editing
them by hand is not documented; hand-written JSON is.

## Rung 3: skills from one place, instead of one file each

In Claude Desktop: Customize, Plugins, Add, Add marketplace, Add from a repository, then `inputloop/vibrobeast-skills`.
Then add vibrobeast-skills from it, and new releases reach you from there.

Before you do:
- **Remove the skills you uploaded one at a time that it also carries**, so two copies of one skill are not both
  offered.
- **The plugin is all its skills together.** If you want only a few, keep uploading those few as files. That stays
  a fine way to run them.

## Rung 4: Claude Code

    /plugin install vibrobeast --marketplace inputloop/vibrobeast

That is the servers and the skills together, for Claude Code and Cowork.

Authored by Mentat (for Corwin, opus-5-5).
