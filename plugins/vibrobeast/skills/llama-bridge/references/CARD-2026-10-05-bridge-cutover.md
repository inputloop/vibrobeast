# CARD 2026-10-05: from the hand-added bridge to the plugin's, keeping its history

*For Corwin, on avalon. Each step is a hand on the keyboard; the CHECK lines say how you know it
worked. Nothing here has been run yet.*

**WHEN** you are ready to stop running the Llama Bridge you added by hand to the desktop config,
and run the one inside the vibrobeast plugin (1.4.0-vb.1) instead.

**Why the database matters.** The hand-added bridge keeps its log, scoreboard, ratings and cache
in `llama_bridge.db` beside its own `llama_bridge.py`. The plugin's bridge keeps them in
`.mentcached\llama-bridge.db` in your user folder. Copy the first to the second before the plugin's
bridge first runs, and the scoreboard (44 delegations, gemma4:12b-8k at 95% verified, as of
2026-10-05) carries over; skip it and the plugin's bridge starts with no history.

## DO

1. Open `claude_desktop_config.json` (Claude Desktop: Settings, Developer, Edit Config). Find the
   `"llama-bridge"` entry and note the folder its `llama_bridge.py` is in. Leave the file open.
2. Quit Claude Desktop completely (from the tray, not only the window), so the bridge closes its
   database.
3. In msys2, copy the database across (change FOLDER to the one from step 1; the `-wal` and `-shm`
   files may not exist, which is fine):

       mkdir -p "$USERPROFILE/.mentcached"
       ls "$USERPROFILE/.mentcached/llama-bridge.db" 2>/dev/null && echo "STOP: one is already there"
       cp FOLDER/llama_bridge.db "$USERPROFILE/.mentcached/llama-bridge.db"
       for x in wal shm; do [ -f FOLDER/llama_bridge.db-$x ] && cp FOLDER/llama_bridge.db-$x "$USERPROFILE/.mentcached/llama-bridge.db-$x"; done

4. Delete the `"llama-bridge"` entry from `claude_desktop_config.json` and save it.
5. In `/f/claude/AS4CE/AS4CE0001`: `make dist`, then install `dist/vibrobeast.plugin` the way you
   install it now.
6. Start Claude Desktop. In a session, turn the bridge on with the mentcached tool
   `pref_set llamabridge.on on`, then restart Claude Desktop once more (the plugin reads the switch
   when its servers start).

## CHECK

- `ollama_status` answers, and its tool name now carries `plugin_vibrobeast_llamabridge`.
- `model_scoreboard` still lists gemma4:12b-8k with its 38 or more uses. If it shows nothing, the
  database did not come across: quit, and redo step 3.
- From the plugin's folder: `python3 skills/llama-bridge/scripts/bridge_smoke.py --host
  http://127.0.0.1:11434 --model gemma4:12b-8k` ends `smoke: every step passed`.
- After that, `ollama_status` says the model is all in GPU memory. A percentage below 100 means it
  spilled: say so and we fit it before judging it.

## TELL ME

Whether the scoreboard came across, the smoke check's lines, and any "% in GPU memory" line.
Then, if you like, these settings make the drafting jobs cheaper (they are suggestions, not
switched on for you):

    python3 servers/polygram/mcp/llama_bridge.py config --db "$USERPROFILE/.mentcached/llama-bridge.db"
    python3 servers/polygram/mcp/llama_bridge.py config --db "$USERPROFILE/.mentcached/llama-bridge.db" think_default false

The first lists every setting with its value; the second turns thinking off by default (a call can
still ask for it with `think`).

---
*Version 1.0.0: first edition on 2026-10-05; spine: 2026-10-05.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0:
https://creativecommons.org/licenses/by-sa/4.0/; Mentat (for Corwin; claude-opus-5-5)
