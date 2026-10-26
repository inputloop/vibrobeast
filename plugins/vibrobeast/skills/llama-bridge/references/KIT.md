# The llama kit: every part, and where to find it

*Written 2026-10-05 for Corwin, Bryant, and anyone who receives the vibrobeast plugin or its
source. One list, so no part has to be found by asking.*

The kit lets Claude hand small, checkable jobs to a local model through Ollama, tuned to the
machine it runs on. Three parts carry it, as Corwin named them: the **MCP bridge**, the
**delegation skill**, and the **houseboxer** (tuning to the hardware). Everything else below
supports one of those three.

| part | in the plugin | in the source tree (code.bru.st/corwin/vibrobeast) | in Bryant's garden |
|---|---|---|---|
| The bridge, 1.4.0-vb.1 | `servers/polygram/mcp/llama_bridge.py` | `polygram/mcp/llama_bridge.py` | his 1.4.0: `llama_bridge.py` (github.com/takushieternal/llamaBridge) |
| Its notice: both hashes, terms | `servers/polygram/mcp/NOTICE-llama_bridge` | `polygram/mcp/NOTICE-llama_bridge` | (none) |
| The change, as a diff against his 1.4.0 | `skills/llama-bridge/references/llama_bridge-1.4.0-vb.1.diff` | the same path | for him to read and merge as he thinks best |
| The switch that keeps it off until turned on | `servers/polygram/mcp/llamabridge.py` (`pref_set llamabridge.on on`) | `polygram/mcp/llamabridge.py` | (his runs on from the config he writes) |
| The delegation skill | `skills/llama-bridge/SKILL.md` | `skills/llama-bridge/SKILL.md` | his `llama-bridge` v1.4, carried whole inside ours |
| A stand-in Ollama | `skills/llama-bridge/scripts/fake_ollama.py` | the same path | (new; works with his 1.4.0 too) |
| The smoke check, run first | `skills/llama-bridge/scripts/bridge_smoke.py` | the same path | (new; works with his 1.4.0 too) |
| The bridge's tests | (not shipped) | `tests/test_llama_bridge_vb.py`, `tests/test_mcp_llamabridge.py` | (none yet) |
| The houseboxer (tuning to the machine) | `SOFT-SKILLS/houseboxer/SKILL.md`, read live through `soft_skill_read` | `SOFT-SKILLS/houseboxer/` | (none yet) |
| The worked example the houseboxer came from | `skills/llama-bridge/references/PROBE-2026-10-04-ollama-speed.md` | the same path | (none) |
| When to offload at all | (his) | (his) | `frugal-offload` and its `offload_gate.py`; `omni-tool` owns the policy |
| Moving from a hand-added bridge to the plugin's | `skills/llama-bridge/references/CARD-2026-10-05-bridge-cutover.md` | the same path | (none) |

## Run it in this order

1. `python3 skills/llama-bridge/scripts/bridge_smoke.py` from the plugin's folder: the bridge's own
   path works, against the stand-in. No GPU, no model, no Ollama needed.
2. The same with `--host http://127.0.0.1:11434`: your Ollama, your models.
3. `ollama_status` after a real delegation: if a model is less than 100% in GPU memory, fit it
   before you judge it (the delegation skill, "Fit the model to the machine").
4. The houseboxer, when you want the machine's facts kept and the fit worked out for you.

## What is not here, said plainly

- No model ships with the kit, and nothing here downloads one.
- The stand-in measures nothing. Speed is learned on the machine.
- The houseboxer is a soft skill: read on demand, provisional, its name his working name.
- Bryant's `frugal-offload`, `omni-tool` and `token-optimizer` are his; this kit points at them and
  does not carry copies.

---
*Version 1.0.0: first edition on 2026-10-05; spine: 2026-07-04.*

Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; CC-BY-SA-4.0:
https://creativecommons.org/licenses/by-sa/4.0/; Mentat (for Corwin; claude-opus-5-5)
