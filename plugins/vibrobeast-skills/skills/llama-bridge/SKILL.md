---
name: llama-bridge
description: "Operate and tune Llama Bridge, the local Ollama delegation bridge served by this plugin (off until llamabridge.on): delegate a subtask, pick a model that fits the task AND the machine, verify the output, run background jobs, and try it all with no GPU through scripts/fake_ollama.py and scripts/bridge_smoke.py. Covers bridge 1.4.0-vb.1's think, options and sized window, ollama_status's spill line, and the field notes (waiting is not silence; one job at a time). Triggers on 'llama bridge', 'delegate to ollama', 'offload to a local model', 'which model fits', 'is the bridge working', 'smoke test the bridge', 'fake ollama', 'num_ctx', 'think false', 'model spilled'. Bryant Frankford's operating manual (v1.4) is carried whole below; this garden's additions follow it."
---

# Llama Bridge: operation, delegation, and this garden's vb.1

This skill is two texts, kept apart so either side can see what the other changed:

1. **Bryant Frankford's manual for bridge v1.4**, carried byte for byte from his 2026-10-05
   bundle (its frontmatter left out; sha256 of his whole file `16b32644...ecc17d3`). Where it says
   "this skill", it means the whole of this one.
2. **This garden's additions for 1.4.0-vb.1**, after it: what the bridge here does that his
   1.4.0 does not, how to try it before tuning, how to fit a model to the machine, and the field
   notes from running it on Avalon.

Nothing of his is removed or reworded. His tool list, his model ladder and his decision procedure
all still hold on vb.1; the additions only add parameters and checks.

<!-- his text begins: Bryant Frankford, llama-bridge SKILL.md v1.4, CC-BY-SA-4.0 -->

# Llama Bridge — operation & delegation manual

Llama Bridge is a single-file, pure-Python tool with two parts sharing one
SQLite database: an **MCP server** Claude connects to, and a local **web
dashboard** (http://127.0.0.1:8765) for monitoring and control. It lets Claude
hand well-scoped subtasks to local Ollama models to save Claude tokens, logs
every delegation, and can auto-pick models, verify output, cache results, run
long jobs in the background, and learn which models are good at what.

This skill owns *operating* the bridge and *how* to delegate well. The decision
of *when* to offload lives in `omni-tool` (canonical) and `skilltank` (Curate
stage); this skill and those two should stay in sync.

## The tools (MCP)

| Tool | Purpose |
|---|---|
| `delegate_task` | Run a prompt on Ollama; returns the output. `model` optional. |
| `delegate_async` | Start a delegation in the background; returns a job id. |
| `delegate_result` | Poll a background job by id for status/result. |
| `list_models` | Installed models (name, params, size). |
| `recommend_model` | Preview the auto-pick for a task (+ optional budget). |
| `model_scoreboard` | Per model x task: uses, rating, verified %, tok/s. |
| `warm_model` | Preload a model into memory (avoid cold start). |
| `ollama_status` | Is Ollama up? version + loaded models. |
| `get_stats` | Delegations, Claude tokens saved, cost avoided, cache hits, latency. |

## Operating it

- **Install / connect:** `python llama_bridge.py install` prints an MCP config
  JSON and a `claude mcp add` command. Paste the JSON into the Claude MCP config
  (e.g. `claude_desktop_config.json`) or run the CLI command, then **restart
  Claude** so it loads the tools. Schema changes (new params/tools) require a
  restart to appear.
- **Run the dashboard:** `python llama_bridge.py` (opens the dashboard). Flags:
  `--port`, `--ollama-host`, `--db`, `--no-browser`.
- **Run both together:** the dashboard and MCP server share the DB, so the
  dashboard shows Claude's delegations live.
- **Requirements:** Python 3.8+ and Ollama running locally with at least one
  model pulled (`ollama pull llama3.2:3b`).

## Choosing the right model — the core discipline

`recommend_model` and `task_type` auto-select are conveniences, **not an oracle**.
Since bridge v1.4 the picker is family-aware (code -> coder, vision -> vision,
everything else -> general; a coder model is only picked for a non-code task when
nothing else is installed), ratings need >=3 votes before they influence the
pick, and the auto-collected verified-rate breaks ties. It still can't judge
difficulty or stakes, so run the pick past the two checks below before you
accept it.

### 1. Match the model FAMILY to the task family

| Task family | Use | Avoid |
|---|---|---|
| Write / refactor / explain code, emit strict formats | a **coder** model (e.g. `qwen3-coder`) | tiny general models |
| Image, screenshot, OCR, describe-a-picture | a **vision** model (`*-vision`, `*-vl`) | any text-only model (it literally can't see) |
| World knowledge, vocabulary, naming, creative, summarize, classify, extract, plain JSON | a **general** instruction-tuned model (`gemma*`, `qwen2.5`, `llama3.*`) | defaulting to the biggest *coder* model just because it's biggest — coder-tuning trades world-knowledge for code |

The failure mode to remember: picking a model by *size* alone. Biggest ≠ best-fit.
A 12B general model usually beats a 30B coder model at "name 20 common fruits."

### 2. Match the model SIZE to difficulty and stakes

A rough capability ladder (calibrate to what's installed via `list_models`):

| Tier | Examples | Reach for it when |
|---|---|---|
| ~3B | `llama3.2:3b` | trivial, high-volume, trivially verifiable: boolean/label classify, tiny reformat, yes/no extraction |
| ~7–8B | `qwen2.5:7b`, `gemma4:latest` | everyday summarize / classify / extract, simple structured output |
| ~12B | `gemma4:12b` | broader knowledge, multi-constraint instructions, cleaner JSON discipline |
| ~30B | `qwen3-coder:30b` | hardest reasoning or real code; **slow → always `delegate_async`** |

Rule of thumb: **start at the smallest model that could plausibly pass your
checks, and let `escalate_to` climb on failure** — you pay big-model latency only
when you actually need it. Exception: if the task genuinely needs world-knowledge,
jump straight to a ≥12B **general** model rather than stacking a weak 7B and
hoping.

### 3. Don't outsource machine-checkable constraints — enforce them in code

This is the highest-leverage rule in this file. If a rule can be checked or fixed
by a regex or a loop — exact length, exact count, dedup, allowed charset, output
format — **do not push it onto the model.** A hard constraint distorts the
model's output to satisfy it: told "every word 4–8 letters," a small model will
*truncate* `elephant → eleph` and `broccoli → brocc` rather than pick a word that
naturally fits. The JSON still parses; the content is junk.

Instead: **ask the model for the creative/knowledge part with loose bounds, tell
it to over-generate, then filter/dedupe/trim/validate in code.** Model does
ideation; code does enforcement. Over-generating (ask for 20, keep 12) gives the
filter room to drop anything that fails.

### 4. Verify semantically, not just structurally

`require_json` and `min_length` prove *shape*, not *correctness* — output can pass
both and still be garbage. And `escalate_to` only fires when a check **fails**, so
weak checks mean escalation never triggers and bad output sails through.

- Make at least one check able to catch the *real* failure mode (content, not just
  format): `must_include` for required tokens, or validate each item in code
  after the call.
- If you can't cheaply express a check that would catch failure, verify the output
  in code post-hoc — or keep the task on Claude.
- `[UNVERIFIED …]` is the system working: never ship it; redo on Claude.
- Two checks run on **every** delegation since v1.4, even with none requested:
  **empty output**, and **likely prompt truncation** (the model evaluated far
  fewer prompt tokens than the prompt contains, meaning the context window
  silently clipped the input). Both count as failed checks, so they trigger
  `escalate_to`.

### 5. Let the scoreboard steer you

`model_scoreboard` shows verified % per model×task family (cache hits are
excluded, so the number reflects real runs) — prefer models with a real track
record for *this* family, and rate results (👍/👎) so auto-select keeps
improving. Ratings and verified-rate need >=3 samples before the picker trusts
them. A high verified % on "json" tells you nothing about "vision."

### Decision procedure (run every delegation through this)

1. Classify the task family: code / vision / knowledge / structured / bulk-simple.
2. Pick a **family-appropriate** model at the **smallest size** that could pass
   your checks. Sanity-check `recommend_model`'s answer against steps 1–2; override
   it when the family is wrong.
3. Move every machine-checkable constraint into code. Give the model **loose
   bounds** and tell it to **over-generate**.
4. Define a check that catches the real failure mode (semantic, not just format).
5. Set `escalate_to` a larger **same-family** model (when the bridge
   auto-selects, it pre-fills this with the next size up in the same family).
6. Big model → `delegate_async` + poll. Verify (in code if needed). Ship only on
   pass; otherwise redo on Claude.

### Worked example — the trap and the fix

**Wrong** (model enforces the hard constraint → truncation):

```
delegate_task(model="qwen2.5:7b", require_json=true, min_length=400,
  prompt="8 categories, exactly 12 words each, every word 4–8 letters, JSON.")
# → valid JSON, but "elephant"→"eleph", "broccoli"→"brocc". Checks passed; content junk.
```

**Right** (general model + loose bounds + over-generate, then filter in code):

```
delegate_async(model="gemma4:12b",           # general knowledge, not a coder model
  require_json=true, escalate_to="qwen3-coder:30b",
  prompt="For each of these 8 categories, list 20 common single words, "
         "spelled in full — do NOT abbreviate or truncate. JSON only.")
# then in code: lowercase → /^[a-z]+$/ → keep length 4–8 → dedupe → take 12 → backfill if short.
```

## Delegating — the recipe

1. **Pick by task family first, then size** (see "Choosing the right model"). Pass
   `task_type` (code, json, extract, classify, summarize, vision, general) +
   `budget` (`fast`, `balanced`, `quality`) to auto-select, but override the pick
   when its family is wrong. Name a `model` explicitly whenever you have a clear
   fit in mind.
2. **Keep hard constraints in code, not the prompt.** Over-generate loosely;
   filter/dedupe/validate after. (Rule 3 above.)
3. **Verify in proportion to risk, and make checks catch the real failure.**
   `require_json` (also puts Ollama in JSON mode), `must_include` (+ `ignore_case`
   when a token's case varies), `min_length`. Set `escalate_to` a bigger
   same-family model to retry once on failure — it only fires on a failed
   check, but the always-on empty-output and truncation checks (v1.4) mean
   auto-selected runs get a working ladder without any checks from you.
4. **Slow/large models:** use `delegate_async` + poll `delegate_result` so you
   never hit the blocking tool timeout (a 30B can run ~a minute).
5. **Caching:** identical requests return instantly and free; pass `no_cache:
   true` for nondeterministic tasks. Only verified results are cached.
6. **Speed:** `warm_model` (or set a dashboard default) to avoid cold starts.
7. **Close the loop:** rate results 👍/👎 on the dashboard so auto-selection
   improves.

Example (structured extraction, verified, with fallback):

```
delegate_task(
  task_type="json", budget="fast", require_json=true,
  must_include=["name","role"], escalate_to="qwen2.5:7b",
  prompt="Extract name and role as JSON from: ..."
)
```

## Reading results

- Clean text → trust it (verified or no checks requested).
- `[UNVERIFIED on <model>: <reasons>] ...` → **do not ship**; redo the subtask
  on Claude. The flag is the safety net working.
- `[escalated to <model>, verified]` → a bigger model rescued it; fine to use.
- `[auto-selected <model>]` → which model the bridge picked when `model` omitted.
  If it's a family mismatch for the task, re-run with an explicit `model`.

## The dashboard

Shows Ollama status; installed models (pull / delete / warm / set default);
a **Test a delegation** panel (streams tokens live, supports auto task_type +
budget); the **activity log** (click a row for prompt/response, cost, tok/s, and
👍/👎 rating); the **model scoreboard**; **background jobs**; and stats +
controls for keep-alive, token prices, and the response cache. Since v1.4:
"cost avoided" is **net** (output price minus the input price Claude pays to
read the result back); the API answers only requests with a localhost
Host/Origin (DNS-rebinding and CSRF hardened); the cache self-prunes (30-day
TTL, 1000-entry cap).

## Troubleshooting

- **Ollama unreachable / no model:** `ollama_status` to confirm. Delegation is an
  optimization, not a dependency — just do the task on Claude.
- **Tool timed out on a big model:** switch to `delegate_async` + `delegate_result`.
- **Model truncated / distorted words to satisfy a rule** (e.g. `elephant`→`eleph`):
  you put a hard constraint in the prompt. Remove it, ask the model to over-generate
  loosely, and enforce the constraint in code (Rule 3). A bigger model helps a
  little; moving the constraint out of the prompt fixes it.
- **Output passed `require_json`/`min_length` but is wrong:** shape checks aren't
  content checks. Add `must_include` or validate items in code, and set
  `escalate_to` — escalation only fires on a failed check (Rule 4).
- **A coder model got picked for a knowledge/creative task:** shouldn't happen
  since v1.4 (family-aware picker) unless only coder models are installed. Name
  a general model explicitly, or pull one.
- **`prompt likely truncated` in checks_failed:** the prompt overflowed the
  model's context window and Ollama clipped it silently. Escalation fires
  automatically if `escalate_to` is set; otherwise shrink the prompt or use a
  larger-context model. (Rare false positive: KV-cache reuse on a repeated
  prompt.)
- **A check false-failed on case (e.g. `<!doctype` vs `<!DOCTYPE`):** add
  `ignore_case: true`.
- **Weak output:** raise `budget` to `quality`, or set `escalate_to`; if still
  `[UNVERIFIED]`, do it yourself.
- **New param/tool not visible:** restart the MCP server (schemas cache at
  connect time).
- **Only a 30B coder model installed:** code/quality auto-picks it — use async, and
  for knowledge tasks lower your expectations or do it on Claude.

## When to offload (brief; full policy in `omni-tool`)

Offload only when the subtask is separable, cheaply checkable or low-stakes,
small-model-shaped (summarize/classify/extract/reformat/translate/boilerplate/
drafts), and worth the overhead (large or repeated payloads). Keep on Claude the
core reasoning, high-stakes/irreversible/security-sensitive work, anything needing
full context, tiny tasks, or work you can't cheaply verify.

## Relationship to the Gauntlet

`omni-tool` and `skilltank` decide *whether* to offload and route here;
**this skill** runs and tunes the delegation — including *which model* and *how to
verify*; `sandboxer` confirms the output actually landed and rejects `[UNVERIFIED]`;
`ethicsminions` gates whether the data may be sent at all — even to a local model —
as a hard stop that outranks any token savings.

## Version note

This SKILL.md matches bridge **v1.4**, which implements: the family-aware
picker; rating gate (>=3 votes) + verified-rate tiebreak; auto `escalate_to`
on auto-select; always-on empty-output and prompt-truncation checks; net cost
accounting (price_out − price_in); localhost Host/Origin hardening on the
dashboard API; and response-cache self-pruning. On an older bridge, treat the
pre-v1.4 caveats (size-first picks, silent truncation) as live again.
<!-- his text ends -->

---

# In this garden: bridge 1.4.0-vb.1

## What vb.1 adds (all in `servers/polygram/mcp/llama_bridge.py`; the diff for Bryant is `references/llama_bridge-1.4.0-vb.1.diff`)

| addition | what it does | why |
|---|---|---|
| `think` on delegate_task / delegate_async | `true`, `false`, `low`, `medium`, `high`; sent only to a model whose `/api/show` lists `thinking` | on gemma4:12b a 90-token answer cost 2,725 tokens with thinking on (Avalon, 2026-10-05) |
| `options` | Ollama options passed through over a config default | `num_ctx`, `num_predict`, `temperature` without a Modelfile variant |
| a sized window | a model whose own context is very large (gemma4: 262,144) gets one sized to the prompt, from 8,192 up in doubling steps | 52.6 tok/s at 8,192 against 8.1 tok/s at the default, and a 2-minute load avoided |
| one at a time | generate calls queue in the bridge; `delegate_result` says `queued` and how many are ahead | on one GPU, four batches sent at once all timed out while waiting their turn |
| a thinking note | a result that thought because nobody said not to begins with one line saying so | so the caller learns to pass `think=false` |
| spill in `ollama_status` | "62% in GPU memory: the rest runs on the CPU, so it is slow" | Ollama's own `size_vram`; the cheapest sign a model does not fit |
| `warm_model` | warms at the window the next call will use | a warm at the default window, then a call at 8,192, loads twice |
| settings | `python3 llama_bridge.py config [KEY [VALUE]]`, or the dashboard's `/api/config` | `think_default`, `options`, `num_ctx_auto`, `num_ctx_floor`, `num_ctx_reserve`, `num_predict_cap` (empty = the reserve, 0 = none), `breaker_after` (4; 0 = off), `breaker_cool` (empty = the generate timeout), `max_parallel`, `generate_timeout` |

The cache key includes `think` and `options` only when one is set, so a cache made by 1.4.0
still hits. Tests: `tests/test_llama_bridge_vb.py` in the source tree, 19 checks, and
`--prove-red` plants six faults (think dropped, options dropped, no window, a cache blind to
think, no queue, think sent to any model); each turns the suite red.

## Try it before tuning anything

    python3 scripts/bridge_smoke.py                         # the plugin's bridge against fake_ollama
    python3 scripts/bridge_smoke.py --host http://127.0.0.1:11434 [--model NAME]   # a real Ollama
    python3 scripts/fake_ollama.py --port 11435 --log requests.jsonl  # a stand-in to point anything at

`fake_ollama.py` answers every call the bridge makes and writes each request down, so you can see
what the bridge sends (think, window, format) with no GPU and no model. `bridge_smoke.py` reaches
Ollama, lists models, runs one checked delegation and one background job, and says each step in
words; against the fake it also shows what was sent. It works on Bryant's 1.4.0 as well (it then
notes that no think and no window are sent). The fake runs nothing and measures nothing: speed is
only ever learned on the real machine.

## Fit the model to the machine, not only to the task

Bryant's rule picks a family, then a size. On a small card, size is also a question of memory:

- **What is free:** the card's memory less what the desktop holds. Avalon: an RTX 3080 with
  10 GB, about 1.6 GB held by the desktop across five monitors, so about 8.4 GB for models.
- **What a model needs:** its weights (the tag page's size), plus any draft model Ollama loads
  with it, plus the context cache at the window it runs with. The window is the part that moves:
  gemma4:12b at 262,144 does not fit 10 GB; at 8,192 it does.
- **The sign it did not fit:** `ollama_status` says less than 100% in GPU memory. Then lower the
  window, use a smaller model, or free memory; do not read a slow answer as a weak model.
- **Thinking is a token cost, not a memory cost:** set `think=false` for drafting, extracting,
  classifying and reformatting; leave it on for multi-step reasoning, and give such jobs room
  (`options.num_predict`, a longer `generate_timeout`).
- The houseboxer soft skill (`SOFT-SKILLS/houseboxer`) collects these facts cheaply and keeps
  them; `references/PROBE-2026-10-04-ollama-speed.md` is the worked example they came from.

## Field notes (Avalon, 2026-10-04 and 05)

- A delegation that takes longer than the desktop bridge's call limit (about a minute) cannot come
  back through `delegate_task`: use `delegate_async` and poll `delegate_result`.
- **Waiting is not silence.** Say what goes before it goes; never two polls without a line to the
  person; write each job id where the next session can find it (the altorewired skill, grown 03).
- Send one job at a time, sized to finish well inside `generate_timeout` on the slowest model you
  use. vb.1 queues them anyway; sizing still decides whether each one finishes.
- Whether to offload at all is Bryant's `frugal-offload` gate: the output is checkable, the stakes
  are low, the volume is real, and it is not judgment-heavy. Otherwise keep it on Claude.

## Judgement tasks: split the verdict, let code make it (measured 2026-10-22)

Rule 3 above, applied to judging rather than generating. When a small model is asked to judge a record
against a rule and answer OK, RED or NOT CHECKED, the rule text moves its bias but does not teach it the
third answer. Ask two yes/no questions instead and let code make the verdict:
`scripts/split_verdict.py --prompt` prints the instruction; pipe the answer to
`scripts/split_verdict.py`, which prints the verdict (PRESENT no → NOT CHECKED; PRESENT yes and MET
yes → OK; MET no → RED; anything else UNPARSED, never a pass). `--selftest` and `--prove-red` check it.

Receipt (Technology Architecture, `exp-2026-10-22-floor-ladder/RESULTS.md`; 17 cases by an independent
planter; readers at temperature 0, thinking off):

| reader | rules only | rules + split | false passes, rules only → split |
|---|---|---|---|
| qwen3:8b | 10–11 of 17 | **14 of 17** | 5 → 1 |
| gemma4:12b | 11–13 of 17 | 12 of 17 | 0 → 0 |

- It worked on qwen3:8b and did not help gemma4:12b, which almost never answers `PRESENT: no` and reads
  a missing record as the rule broken (fail-closed). Say in the rule which of the two you want.
- Count **false passes** (a fault or an unlooked-at record called OK), not accuracy: an error toward RED
  or NOT CHECKED sends the work to a person; an error toward OK lets it through.
- Hosted models were already at 16–17 of 17 with no rules; what the rules added there was the one rule
  peculiar to the house. Keep judgement on a small model only where the false-pass count says so.
- One planter, one case set, two local families: rerun before relying on it for a new kind of rule.

## Where the rest of the llama kit is

`references/KIT.md` lists every part (server, switch, tests, this skill, houseboxer, the probe,
the cutover card) and where each lives in the plugin, in the source tree, and in Bryant's garden.

## Version note

**1.0.1 (2026-10-22):** "Judgement tasks: split the verdict", with `scripts/split_verdict.py` (selftest
8 of 8, prove-red 3 of 3) and the receipt from the Technology Architecture floor-ladder run. Bryant's
text is unchanged.

**1.4.0-vb.1 (2026-10-05):** first garden edition. Bryant's v1.4 manual carried whole; the vb.1
additions, the fake and the smoke check written here. The bridge's own version string says
`1.4.0-vb.1` so no one takes it for his.

---
*Version 1.0.1: edition revised from 1.0.0 on 2026-10-22; spine: 2026-07-04.*

Copyright 2026 Bryant Frankford <nathanielfrankford@gmail.com> (his manual, the text between the
markers above) and Corwin Brust <corwin@bru.st> and Contributors (the additions); CC-BY-SA4:
https://creativecommons.org/licenses/by-sa/4.0/ (scripts GPL-3.0-or-later); Mentat (for Corwin,
claude-opus-5-5)
