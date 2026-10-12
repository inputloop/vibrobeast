# PROBE · 2026-10-04 · why gemma4:12b drafts are slow on avalon

Run from the built-in browser against his own Ollama (0.35.1, http://127.0.0.1:11434), one request at a
time, store-and-poll (the browser tool gives up at 45 s). Test prompt: the r2 header plus the first three
b01 words (CAPSULE, CARD, CELL); 143 prompt tokens. Every request as the bridge sends it (`format: json`,
`keep_alive: 30m`, `stream` aside) plus the one change named.

## Observed

| run | change | first token | tokens | rate | outcome |
|---|---|---|---|---|---|
| A | none (bridge's request) | — | — | — | no answer after 600 s; stopped by closing the request (22:56:50Z–23:07Z) |
| A, streamed | none | 11.9 s | 138 in 75.5 s | 1.83 tok/s | all thinking, no answer yet; stopped by hand |
| C | `options.num_ctx 8192` (model reloaded) | 57.0 s | 332 in 180 s | 1.84 tok/s average, 0.67 to 4.1 in 30 s windows | all thinking (1,354 chars), no answer yet; stopped by hand |
| D | `think: false` + `num_ctx 8192` | 1.7 s | 92 (eval_count) | 0.77 tok/s (Ollama's own eval_duration 119.7 s) | done, `stop`; 391 chars, valid JSON, no thinking |

- `/api/show`: capabilities completion, vision, audio, tools, **thinking**; context_length 262,144;
  RENDERER and PARSER `gemma4` (built in; `TEMPLATE` is only `{{ .Prompt }}`); a **DRAFT** model
  (speculative decoding, `draft_num_predict 3`); Q4_K_M, 11.9 B, 7.5 GB on disk.
- `/api/ps` after A: context 262,144, size 1,111,092,100 = size_vram. After C: context 8,192, size 1,090,120,580 = size_vram.
- His Task Manager at about 22:57Z (screenshot in chat): RTX 3080, dedicated GPU memory 9.6 / 10.0 GB,
  shared GPU memory 5.2 / 16.0 GB, utilisation 18 %, 3D about 7 %; CPU 25 %.
- Bridge source (AS4CE0001/polygram/mcp/llama_bridge.py, v1.4.0, Bryant's, kept byte for byte):
  `ollama_generate` sends model, prompt, stream, keep_alive, and system/format when given; no `think`, no `options`.

## Judged

- **H1 holds.** With thinking on, 332 tokens went by before the first answer character (C); the whole answer
  with thinking off was 92 (D): at least 3.6 times, against a falsifier of a quarter. Every bridge batch pays this.
- **H2 is falsified as stated.** At 8,192 context the rate stayed within a quarter of the 262,144 rate
  (1.84 vs 1.83 tok/s averaged; D lower still). The context was not what made it slow.
- **H4 (new, open): most of the model is not running on the GPU.** 1–2 tok/s is CPU speed for a 12 B Q4
  model; a 3080 does tens. Ollama's own `size` reads about 1.1 GB for a 7.5 GB model, while Windows shows
  the card full and 5.2 GB spilled to shared memory. Candidates: another process holding VRAM (e.g. a
  runner left from before the restart), or the main model plus its draft model not fitting in 10 GB.
  Test: list GPU memory per process (Task Manager, Details, Dedicated GPU memory). Falsified if Ollama's
  runner is the only large holder and holds about 8 GB or more.
- **H3 (JSON-mode runaway) is falsified:** the A and C streams showed ordinary thinking text arriving slowly, no padding,
  and D stopped cleanly (`done_reason: stop`) at 92 tokens. A was slow because it was thinking at 1–2 tok/s.

## Retest after his Ollama restart (hypotheses written before the runs)

Observed before: he restarted Ollama ~23:5xZ; his Task Manager then showed dedicated GPU memory 1.6 / 10.0 GB,
shared 0.1 GB, 3D 40 % with nothing loaded (five monitors and the desktop). Before the restart it had read
9.6 dedicated + 5.3 shared during runs, so memory from earlier loads may not have been released between
A, C and D: the first round's numbers may describe a crowded card, not the model.

- **H2′ (H2 retested on a clean card):** with Ollama fresh, gemma4:12b at `num_ctx 8192` fits in VRAM and
  runs about ten times D's 0.77 tok/s. Falsified if it runs under 4 tok/s.
- **H2″:** at the default 262,144 context on a clean card it spills to shared memory and stays slow.
  Falsified if it is within a quarter of the 8k rate.
- Measured by Ollama's own eval_count / eval_duration; Task Manager watched by screenshot during each run.

Hardware (his, shared without embargo): Avalon — Intel Core i7-6950X (10 cores, 3.0 GHz), 32 GB RAM,
NVIDIA GeForce RTX 3080 10 GB (driver 32.0.15.7242), MSI X99 Godlike Gaming Carbon, Windows 64-bit;
SSDs (Samsung 970 PRO 1 TB, Kingston 240 GB, Crucial M4 256 GB) and two 4 TB Toshiba HDDs; five monitors.

### Observed (clean card, 2026-10-05 ~00:04–00:08Z)

| run | change | load | tokens | rate | outcome |
|---|---|---|---|---|---|
| E | `think: false` + `num_ctx 8192` | 9.6 s | 90 | **52.6 tok/s** | done, `stop`, valid JSON |
| G | `num_ctx 8192` (thinking on, as the bridge sends) | (loaded) | **2,725** (8,064 chars of thinking) | **66.7 tok/s** | done, `stop`, 41 s in all |
| F | `think: false`, default context (262,144) | **124.6 s** | 110 | **8.1 tok/s** | done, `stop` |

Task Manager with E/G's model loaded and idle: dedicated 9.6 / 10.0 GB, shared 1.6 GB, GPU memory 11.2 GB.

### Judged

- **H2′ holds:** 52.6 tok/s against D's 0.77 (68×). The first round ran on a card still crowded by earlier loads.
- **H2″ holds:** on the clean card the default 262,144 context alone costs 6.5× (8.1 vs 52.6 tok/s) and a two-minute
  load. Since the bridge sends no `num_ctx`, every bridge call pays it. H2 as first stated was wrong only because
  the card was already full.
- **H1, measured cleanly:** thinking turns a 90-token answer into 2,725 tokens (30×). At 8k it still fits:
  41 s for three words.
- Speculative decoding helps here: G's 66.7 tok/s beat E's 52.6, and its 2,433 stream chunks carried 2,725 tokens.

### Done about it

- Created a local variant on his Ollama: `gemma4:12b-8k` = `FROM gemma4:12b` + `PARAMETER num_ctx 8192` (no download; a
  manifest beside the original; same weights, same draft model, thinking unchanged). The bridge can use it by name,
  so its request stays byte-for-byte the bridge's own and only the context window changes.
- Batch size for drafts: 6 words. Thinking runs about 900 tokens a word, so 12 words could pass 8,192 tokens of
  context; 6 stay under it. Remove the variant with `ollama rm gemma4:12b-8k` (the original is untouched).

## Baseline: the smallest gemma4 (pulled at his request, 2026-10-05 ~00:56Z)

`gemma4:e2b-it-qat` from ollama.com: 3.35 GB downloaded in 59 s; `num_ctx 8192`, thinking on, same prompts.

| model | prompt | tokens | thinking chars | rate | eval time | kept by the intake check |
|---|---|---|---|---|---|---|
| gemma4:12b-8k | 3 words (G) | 2,725 | 8,064 | 66.7 tok/s | 40.9 s | 3 of 3 |
| gemma4:e2b-it-qat | 3 words | 762 | 2,450 | 157.6 tok/s | 4.8 s | 3 of 3 (headwords in capitals) |
| gemma4:12b-8k | b01a, 6 words (bridge) | n/a | n/a | n/a | about 75–90 s | 6 of 6 |
| gemma4:e2b-it-qat | b01a, 6 words | 909 | 3,050 | 158.5 tok/s | 5.7 s | **5 of 6** (CHARGE: the sentence never uses the word) |

Judged: e2b is about 13× faster per batch and thinks a third as much, but loses words and sense (CHARGE missing,
CELL as "a tiny light cell"). For short prose that must hold a given sense, the 12b is the keeper here; e2b
suits jobs where speed matters more than fidelity. Sample of one prompt each: a baseline, not a ranking.
