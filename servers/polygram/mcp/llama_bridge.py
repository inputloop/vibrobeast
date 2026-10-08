#!/usr/bin/env python3
"""
Llama Bridge - let Claude delegate small tasks to local Ollama models.

One file. Pure standard library. Two modes:

  python llama_bridge.py            # start the web dashboard (GUI + REST API)
  python llama_bridge.py mcp        # run as an MCP stdio server for Claude
  python llama_bridge.py install    # print MCP config to paste into Claude

Why: offloading well-scoped subtasks (summarize, classify, extract, reformat,
simple code) to a local Ollama model means Claude doesn't spend tokens doing
them. Every delegation is logged to SQLite so the dashboard can show exactly
what happened and roughly how many tokens were kept off Claude.

The GUI process and the MCP process share the same SQLite database (WAL mode),
so the dashboard shows delegations made by Claude in real time.

This copy is 1.4.0-vb.1: Bryant Frankford's Llama Bridge 1.4.0 with the changes
below, made in Corwin Brust's vibrobeast garden for Bryant to see and merge back
as he thinks best (NOTICE-llama_bridge has both hashes and the list). In short:
  - think: delegate_task / delegate_async take `think` (true, false, or
    "low"/"medium"/"high") and pass it to Ollama; it is only sent to a model
    that reports the thinking capability. Config default: `think_default`.
  - options: they take `options` (num_ctx, num_predict, temperature, ...),
    passed through over a config default (`options`, a JSON object).
  - num_ctx auto (config `num_ctx_auto`, on): a model whose own context is very
    large (gemma4: 262,144) gets a window sized to the prompt instead, in
    buckets from `num_ctx_floor` (8192) up, so it stays on the GPU. Measured on
    an RTX 3080: 52.6 tok/s at 8,192 against 8.1 tok/s at the default.
  - one at a time (config `max_parallel`, 1): generate calls queue in the
    bridge, so a background job's time limit (`generate_timeout`, 600 s) counts
    from when it starts, not from when it was queued; delegate_result says
    "queued".
  - warm_model warms at the same window the next call will use.
  - the cache key includes think and options (unchanged when neither is set,
    so an existing cache still hits).
  - each result records whether the model thought, and how much; ollama_status
    says when a loaded model has spilled out of GPU memory.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.4.0-vb.1"
DEFAULT_PORT = 8765
DEFAULT_OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "llama_bridge.db")

# Runtime config, finalised in main().
CFG = {"db": DEFAULT_DB, "ollama": DEFAULT_OLLAMA, "port": DEFAULT_PORT}

_DB_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# Storage / logging                                                           #
# --------------------------------------------------------------------------- #
def db_conn():
    c = sqlite3.connect(CFG["db"], timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=5000")
    return c


def init_db():
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts              TEXT    NOT NULL,
                    level           TEXT    NOT NULL,
                    source          TEXT    NOT NULL,
                    type            TEXT    NOT NULL,
                    model           TEXT,
                    message         TEXT,
                    prompt          TEXT,
                    response        TEXT,
                    duration_ms     INTEGER,
                    prompt_tokens   INTEGER,
                    response_tokens INTEGER,
                    claude_saved    INTEGER,
                    cost_saved      REAL,
                    cached          INTEGER,
                    tok_per_sec     REAL,
                    task_type       TEXT,
                    budget          TEXT,
                    rating          INTEGER
                )
                """
            )
            c.execute("CREATE INDEX IF NOT EXISTS ix_events_id ON events(id)")
            c.execute(
                "CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)"
            )
            # Migrate older databases as columns were added over time.
            cols = [r[1] for r in c.execute("PRAGMA table_info(events)").fetchall()]
            for _col, _type in (("claude_saved", "INTEGER"), ("cost_saved", "REAL"),
                                ("cached", "INTEGER"), ("tok_per_sec", "REAL"),
                                ("task_type", "TEXT"), ("budget", "TEXT"),
                                ("rating", "INTEGER")):
                if _col not in cols:
                    c.execute("ALTER TABLE events ADD COLUMN %s %s" % (_col, _type))
            c.execute(
                """CREATE TABLE IF NOT EXISTS cache (
                    key             TEXT PRIMARY KEY,
                    model           TEXT,
                    response        TEXT,
                    prompt_tokens   INTEGER,
                    response_tokens INTEGER,
                    created_ts      TEXT,
                    hits            INTEGER DEFAULT 0
                )""")
            c.execute(
                """CREATE TABLE IF NOT EXISTS jobs (
                    id          TEXT PRIMARY KEY,
                    status      TEXT,
                    model       TEXT,
                    task_type   TEXT,
                    prompt      TEXT,
                    created_ts  TEXT,
                    done_ts     TEXT,
                    result      TEXT,
                    error       TEXT
                )""")
            c.commit()
        finally:
            c.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def log_event(level, source, etype, message=None, model=None, prompt=None,
              response=None, duration_ms=None, prompt_tokens=None,
              response_tokens=None, claude_saved=None, cost_saved=None,
              cached=None, tok_per_sec=None, task_type=None, budget=None):
    """Write one row to the event log and return its id. Never raises."""
    try:
        with _DB_LOCK:
            c = db_conn()
            try:
                cur = c.execute(
                    """INSERT INTO events
                       (ts, level, source, type, model, message, prompt,
                        response, duration_ms, prompt_tokens, response_tokens,
                        claude_saved, cost_saved, cached, tok_per_sec,
                        task_type, budget)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (now_iso(), level, source, etype, model, message, prompt,
                     response, duration_ms, prompt_tokens, response_tokens,
                     claude_saved, cost_saved, cached, tok_per_sec,
                     task_type, budget),
                )
                rid = cur.lastrowid
                c.commit()
                return rid
            finally:
                c.close()
    except Exception as e:  # pragma: no cover
        sys.stderr.write("log_event failed: %s\n" % e)
        return None


def cfg_get(key, default=None):
    try:
        c = db_conn()
        try:
            row = c.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default
        finally:
            c.close()
    except Exception:
        return default


def cfg_set(key, value):
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute(
                "INSERT INTO config(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )
            c.commit()
        finally:
            c.close()


def ollama_host():
    return (cfg_get("ollama_host") or CFG["ollama"]).rstrip("/")


# --------------------------------------------------------------------------- #
# Ollama client (urllib only)                                                 #
# --------------------------------------------------------------------------- #
class OllamaError(Exception):
    pass


def _http(method, url, body=None, timeout=300):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:
        raise OllamaError("cannot reach Ollama at %s (%s)" % (url, e))


def _http_json(method, path, body=None, timeout=300):
    status, raw = _http(method, ollama_host() + path, body, timeout)
    try:
        obj = json.loads(raw or b"{}")
    except Exception:
        obj = {"raw": (raw or b"").decode("utf-8", "replace")}
    if status >= 400:
        raise OllamaError(obj.get("error") or ("HTTP %s" % status))
    return obj


def ollama_version(timeout=3):
    return _http_json("GET", "/api/version", timeout=timeout).get("version")


def ollama_tags():
    """Return list of installed models: [{name, size, param, family, modified}]."""
    obj = _http_json("GET", "/api/tags", timeout=10)
    out = []
    for m in obj.get("models", []):
        det = m.get("details") or {}
        out.append({
            "name": m.get("name") or m.get("model"),
            "size": m.get("size"),
            "param": det.get("parameter_size"),
            "family": det.get("family"),
            "modified": m.get("modified_at"),
        })
    out.sort(key=lambda x: (x["name"] or "").lower())
    return out


def ollama_ps():
    """Names of currently loaded/running models."""
    return [m["name"] for m in ollama_ps_detail()]


def ollama_ps_detail():
    """Loaded models with how much of each sits in GPU memory (vb.1).
    Ollama reports size and size_vram; when size_vram is less than size, part
    of the model runs on the CPU, and generation is several times slower."""
    try:
        obj = _http_json("GET", "/api/ps", timeout=5)
    except OllamaError:
        return []
    out = []
    for m in obj.get("models", []):
        size, vram = m.get("size"), m.get("size_vram")
        pct = None
        if isinstance(size, int) and size > 0 and isinstance(vram, int):
            pct = int(round(100.0 * vram / size))
        out.append({"name": m.get("name") or m.get("model"), "size": size,
                    "size_vram": vram, "gpu_pct": pct,
                    "context_length": m.get("context_length")})
    return out


def describe_loaded(d):
    """One loaded model in words, for ollama_status."""
    bits = []
    if d.get("gpu_pct") is not None:
        if d["gpu_pct"] >= 100:
            bits.append("all in GPU memory")
        else:
            bits.append("%d%% in GPU memory: the rest runs on the CPU, so it is "
                        "slow; a smaller num_ctx or a smaller model fits" % d["gpu_pct"])
    if d.get("context_length"):
        bits.append("context %s" % d["context_length"])
    return "%s (%s)" % (d["name"], ", ".join(bits)) if bits else d["name"]


# --------------------------------------------------------------------------- #
# vb.1: what a model can do, and the request body built from it               #
# --------------------------------------------------------------------------- #
_SHOW_CACHE = {}
_SHOW_LOCK = threading.Lock()
THINK_LEVELS = ("low", "medium", "high")


def ollama_show(model, timeout=10):
    """{thinking, context_length, num_ctx_param, capabilities} from /api/show,
    cached per process; {} when Ollama cannot say (then nothing extra is sent)."""
    with _SHOW_LOCK:
        if model in _SHOW_CACHE:
            return _SHOW_CACHE[model]
    try:
        obj = _http_json("POST", "/api/show", {"model": model}, timeout=timeout)
    except OllamaError:
        return {}
    caps = obj.get("capabilities") or []
    ctx = None
    for k, v in (obj.get("model_info") or {}).items():
        if str(k).endswith(".context_length") and isinstance(v, int):
            ctx = v
            break
    param = None
    for line in (obj.get("parameters") or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "num_ctx":
            try:
                param = int(parts[1])
            except ValueError:
                pass
    meta = {"thinking": "thinking" in caps, "context_length": ctx,
            "num_ctx_param": param, "capabilities": list(caps)}
    with _SHOW_LOCK:
        _SHOW_CACHE[model] = meta
    return meta


def parse_think(v):
    """None (not said), True, False, or a level. Raises ValueError on anything else."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    t = str(v).strip().lower()
    if t == "":
        return None
    if t in ("true", "on", "yes", "1"):
        return True
    if t in ("false", "off", "no", "0"):
        return False
    if t in THINK_LEVELS:
        return t
    raise ValueError("think must be true, false, low, medium or high (got %r)" % v)


def _cfg_int(key, dflt):
    try:
        return int(cfg_get(key, dflt))
    except (TypeError, ValueError):
        return dflt


def cfg_options():
    """The config default for Ollama options (a JSON object), or {}."""
    raw = cfg_get("options")
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def caller_think(think):
    """The caller's think, else the config default (think_default)."""
    if think is not None:
        return think
    try:
        return parse_think(cfg_get("think_default"))
    except ValueError:
        return None


def caller_options(options):
    """Config default options with the caller's on top."""
    opts = cfg_options()
    opts.update(options or {})
    return opts


def choose_num_ctx(meta, prompt, system=None, num_predict=None):
    """A context window for a model whose own is very large, or None to leave
    it to Ollama. Sized to the prompt plus room to answer, in buckets from
    num_ctx_floor upward (doubling), so a change of size rarely reloads."""
    if cfg_get("num_ctx_auto", "1") != "1":
        return None
    if not meta or meta.get("num_ctx_param"):
        return None  # Ollama cannot say, or the Modelfile already sets one
    native = meta.get("context_length")
    if not native or native <= _cfg_int("num_ctx_auto_above", 32768):
        return None
    floor = _cfg_int("num_ctx_floor", 8192)
    reserve = num_predict if isinstance(num_predict, int) and num_predict > 0 \
        else _cfg_int("num_ctx_reserve", 4096)
    need = int(est_claude_tokens((system or "") + "\n" + (prompt or "")) * 1.25) + reserve
    n = floor
    while n < need and n < native:
        n *= 2
    return min(n, native)


def build_generate_body(model, prompt, system=None, fmt=None, think=None,
                        options=None, stream=False):
    """The /api/generate body, and what was decided: (body, info)."""
    body = {"model": model, "prompt": prompt, "stream": stream,
            "keep_alive": cfg_get("keep_alive", "30m")}
    if system:
        body["system"] = system
    if fmt:
        body["format"] = fmt
    meta = ollama_show(model)
    want = caller_think(think)
    info = {"think": "unknown", "num_ctx": None, "num_ctx_auto": False}
    if meta:
        if not meta.get("thinking"):
            info["think"] = "n/a"  # never sent: Ollama refuses think on such a model
        elif want is None:
            info["think"] = "default"  # Ollama's own default: it thinks
        else:
            body["think"] = want
            info["think"] = "off" if want is False else ("on" if want is True else want)
    elif think is not None:
        body["think"] = think  # Ollama could not say; the caller asked, so send it
        info["think"] = "sent"
    opts = caller_options(options)
    if "num_ctx" not in opts:
        n = choose_num_ctx(meta, prompt, system, opts.get("num_predict"))
        if n:
            opts["num_ctx"] = n
            info["num_ctx_auto"] = True
    if opts:
        body["options"] = opts
    info["num_ctx"] = opts.get("num_ctx")
    return body, info


_GEN_SEM = None
_GEN_SEM_LOCK = threading.Lock()


def generate_slot():
    """One generate call at a time (config max_parallel, read once per process):
    on one GPU Ollama runs them in turn anyway, and a call waiting here has not
    started its time limit."""
    global _GEN_SEM
    with _GEN_SEM_LOCK:
        if _GEN_SEM is None:
            _GEN_SEM = threading.BoundedSemaphore(max(1, _cfg_int("max_parallel", 1)))
        return _GEN_SEM


def ollama_generate(model, prompt, system=None, timeout=None, fmt=None,
                    think=None, options=None, on_start=None):
    body, info = build_generate_body(model, prompt, system=system, fmt=fmt,
                                     think=think, options=options)
    if timeout is None:
        timeout = _cfg_int("generate_timeout", 600)
    with generate_slot():
        if on_start:
            on_start()
        res = _http_json("POST", "/api/generate", body, timeout=timeout)
    res["_vb"] = info
    return res


def ollama_generate_stream(model, prompt, system=None):
    """Yield streaming chunks {response, done, ...} from /api/generate."""
    url = ollama_host() + "/api/generate"
    body, _info = build_generate_body(model, prompt, system=system, stream=True)
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except (urllib.error.URLError, OSError) as e:
        raise OllamaError("cannot reach Ollama at %s (%s)" % (url, e))


def ollama_warm(model, timeout=300):
    """Preload a model into memory (empty prompt) so later calls are fast."""
    body, _info = build_generate_body(model, "")
    body.pop("think", None)  # nothing to think about; only the window matters
    return _http_json("POST", "/api/generate", body, timeout=timeout)


def ollama_delete(name):
    status, raw = _http("DELETE", ollama_host() + "/api/delete",
                        {"name": name}, timeout=30)
    if status >= 400:
        raise OllamaError((raw or b"").decode("utf-8", "replace") or ("HTTP %s" % status))
    return True


def ollama_pull_stream(name):
    """Generator yielding status dicts while pulling a model."""
    url = ollama_host() + "/api/pull"
    data = json.dumps({"name": name, "stream": True}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            for line in r:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except (urllib.error.URLError, OSError) as e:
        raise OllamaError("pull failed: %s" % e)


# --------------------------------------------------------------------------- #
# Core: delegate a task to a model                                            #
# --------------------------------------------------------------------------- #
def est_claude_tokens(text):
    """Estimate the Claude output tokens saved by NOT generating this text.
    Blends a char/4 estimate with a word*1.33 estimate to reduce error;
    tokenizers differ, so treat it as directional."""
    if not text:
        return 0
    chars = len(text)
    words = len(text.split())
    return max(1, round((chars / 4.0 + words * 1.33) / 2.0))


def est_cost_saved(out_tokens):
    """Estimated NET Claude cost avoided (USD): output tokens Claude did not
    generate (at the output price) minus the input cost of reading the result
    back into context (at the input price). Directional, not an invoice."""
    def _price(key, dflt):
        try:
            return float(cfg_get(key, dflt))
        except (TypeError, ValueError):
            return float(dflt)
    net = max(_price("price_out", "15.0") - _price("price_in", "3.0"), 0.0)
    return round((out_tokens or 0) * net / 1000000.0, 6)


def _tok_per_sec(res):
    ec = res.get("eval_count")
    ed = res.get("eval_duration")
    if ec and ed:
        return round(ec / (ed / 1e9), 1)
    return None


def _cache_key(model, prompt, system, fmt, think=None, options=None):
    raw = "%s\x00%s\x00%s\x00%s" % (model, system or "", prompt, fmt or "")
    if think is not None or options:
        # vb.1: a thought-through answer is not the same answer; neither is one
        # made with other options. Unchanged when neither is set.
        raw += "\x00think=%s\x00options=%s" % (
            json.dumps(think), json.dumps(options or {}, sort_keys=True))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cache_get(key):
    c = db_conn()
    try:
        row = c.execute("SELECT * FROM cache WHERE key=?", (key,)).fetchone()
        return dict(row) if row else None
    finally:
        c.close()


def cache_put(key, model, response, p_tok, r_tok):
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute(
                "INSERT OR REPLACE INTO cache "
                "(key, model, response, prompt_tokens, response_tokens, "
                " created_ts, hits) VALUES (?,?,?,?,?,?,"
                " COALESCE((SELECT hits FROM cache WHERE key=?), 0))",
                (key, model, response, p_tok, r_tok, now_iso(), key))
            # Hygiene: drop stale entries, cap total rows (oldest evicted).
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            c.execute("DELETE FROM cache WHERE created_ts < ?", (cutoff,))
            c.execute("DELETE FROM cache WHERE key IN (SELECT key FROM cache "
                      "ORDER BY created_ts DESC LIMIT -1 OFFSET 1000)")
            c.commit()
        finally:
            c.close()


def cache_touch(key):
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute("UPDATE cache SET hits = hits + 1 WHERE key=?", (key,))
            c.commit()
        finally:
            c.close()


def cache_clear():
    with _DB_LOCK:
        c = db_conn()
        try:
            n = c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            c.execute("DELETE FROM cache")
            c.commit()
            return n
        finally:
            c.close()


def cache_info():
    c = db_conn()
    try:
        row = c.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(hits),0) h FROM cache").fetchone()
        return {"entries": row["n"], "hits": row["h"]}
    finally:
        c.close()


def _strip_fences(text):
    t = (text or "").strip()
    if t.startswith("```"):
        nl = t.find("\n")
        t = t[nl + 1:] if nl >= 0 else t
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def verify_output(text, checks):
    """Run cheap deterministic checks. Returns (ok, [reasons])."""
    reasons = []
    if not text or not text.strip():
        return False, ["empty output"]
    if checks.get("min_length") and len(text) < int(checks["min_length"]):
        reasons.append("shorter than min_length=%s" % checks["min_length"])
    ci = bool(checks.get("ignore_case"))
    hay = text.lower() if ci else text
    for sub in (checks.get("must_include") or []):
        needle = sub.lower() if ci else sub
        if needle not in hay:
            reasons.append("missing required text: %r" % sub)
    if checks.get("require_json"):
        try:
            json.loads(_strip_fences(text))
        except Exception as e:
            reasons.append("not valid JSON (%s)" % e)
    return (len(reasons) == 0), reasons


FAMILY_CODE = ("coder", "code", "deepseek", "starcoder", "codellama")
FAMILY_VISION = ("vision", "llava", "moondream", "bakllava")


def _is_code_model(name):
    return any(k in (name or "").lower() for k in FAMILY_CODE)


def _is_vision_model(name):
    n = (name or "").lower()
    base = n.split(":", 1)[0]
    return (any(k in n for k in FAMILY_VISION)
            or base.endswith("vl") or "-vl-" in base)


def model_scores(task_type=None):
    """Aggregate delegate outcomes per model (optionally for one task_type)."""
    c = db_conn()
    try:
        q = ("SELECT model, COUNT(*) n, AVG(rating) ar, COUNT(rating) rn, "
             "AVG(CASE WHEN level='INFO' THEN 1.0 ELSE 0.0 END) vr, "
             "AVG(tok_per_sec) tps, AVG(duration_ms) ms "
             "FROM events WHERE type='delegate' AND level!='ERROR' "
             "AND COALESCE(cached,0)=0")
        p = []
        if task_type:
            q += " AND task_type=?"
            p.append(task_type)
        q += " GROUP BY model"
        return {r["model"]: dict(r) for r in c.execute(q, p).fetchall()}
    finally:
        c.close()


def scoreboard():
    c = db_conn()
    try:
        rows = c.execute(
            "SELECT model, COALESCE(task_type,'-') task_type, COUNT(*) n, "
            "AVG(rating) ar, COUNT(rating) rn, "
            "AVG(CASE WHEN level='INFO' THEN 1.0 ELSE 0.0 END) vr, "
            "AVG(tok_per_sec) tps, AVG(duration_ms) ms "
            "FROM events WHERE type='delegate' AND level!='ERROR' "
            "AND COALESCE(cached,0)=0 "
            "GROUP BY model, task_type ORDER BY n DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def set_rating(event_id, rating):
    with _DB_LOCK:
        c = db_conn()
        try:
            cur = c.execute(
                "UPDATE events SET rating=? WHERE id=? AND type='delegate'",
                (rating, event_id))
            c.commit()
            return cur.rowcount > 0
        finally:
            c.close()


def pick_model(task_type, budget):
    """Choose an installed model for a task type + budget, informed by ratings.
    Returns (model_name, reason) or (None, reason)."""
    try:
        models = ollama_tags()
    except OllamaError as e:
        return None, str(e)
    if not models:
        return None, "no models installed"
    tt = (task_type or "general").lower()
    if tt == "code":
        cands = [m for m in models if _is_code_model(m["name"])] or models
    elif tt == "vision":
        cands = [m for m in models if _is_vision_model(m["name"])]
        if not cands:
            return None, "no vision-capable model installed"
    else:
        # Family first: general instruction models. Vision excluded; coder
        # models only considered when nothing else is installed (coder-tuning
        # trades world knowledge for code).
        pool = [m for m in models if not _is_vision_model(m["name"])] or models
        cands = [m for m in pool if not _is_code_model(m["name"])] or pool
    scores = model_scores(tt)
    sizes = sorted((m["size"] or 0) for m in cands)
    median = sizes[len(sizes) // 2] if sizes else 0
    b = (budget or "balanced").lower()

    def rating_key(m):
        # Ratings and verified-rate only count with >=3 samples, then are
        # shrunk and bucketed so a weak signal can't lexicographically
        # override the budget; budget breaks ties within a bucket.
        sc = scores.get(m["name"])
        ar = vr = 0.0
        if sc:
            if (sc["rn"] or 0) >= 3 and sc["ar"] is not None:
                ar = sc["ar"] * sc["rn"] / (sc["rn"] + 2.0)
            if (sc["n"] or 0) >= 3:
                vr = (sc["vr"] or 0.0) * sc["n"] / (sc["n"] + 3.0)
        return (-round(ar * 2) / 2.0, -round(vr * 4) / 4.0)

    def budget_key(m):
        sz = m["size"] or 0
        if b in ("fast", "cheap", "cheapest", "small", "quick"):
            return sz
        if b in ("quality", "best", "max", "large", "smart"):
            return -sz
        return abs(sz - median)

    best = sorted(cands, key=lambda m: (rating_key(m), budget_key(m)))[0]
    sc = scores.get(best["name"])
    why = "task=%s budget=%s" % (tt, b)
    if sc and sc["rn"]:
        why += " (rating %.2f over %d)" % (sc["ar"], sc["rn"])
    return best["name"], why


def pick_escalation(model_name, task_type=None):
    """Smallest same-family installed model strictly larger than model_name,
    or None. Used to auto-fill escalate_to when the bridge auto-selects."""
    try:
        models = ollama_tags()
    except OllamaError:
        return None
    cur = next((m for m in models if m["name"] == model_name), None)
    if not cur or not cur.get("size"):
        return None
    if _is_vision_model(model_name):
        fam = _is_vision_model
    elif _is_code_model(model_name):
        fam = _is_code_model
    else:
        def fam(n):
            return not _is_vision_model(n) and not _is_code_model(n)
    bigger = [m for m in models
              if m["name"] != model_name and fam(m["name"])
              and (m.get("size") or 0) > cur["size"]]
    if not bigger:
        return None
    return sorted(bigger, key=lambda m: m["size"])[0]["name"]


def job_create(model, task_type, prompt, status="running"):
    jid = uuid.uuid4().hex[:12]
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute("INSERT INTO jobs(id,status,model,task_type,prompt,created_ts)"
                      " VALUES(?,?,?,?,?,?)",
                      (jid, status, model, task_type, (prompt or "")[:2000],
                       now_iso()))
            c.commit()
        finally:
            c.close()
    return jid


def job_finish(jid, result=None, error=None):
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute("UPDATE jobs SET status=?, done_ts=?, result=?, error=? "
                      "WHERE id=?",
                      ("error" if error else "done", now_iso(),
                       json.dumps(result) if result is not None else None,
                       error, jid))
            c.commit()
        finally:
            c.close()


def job_mark(jid, status):
    with _DB_LOCK:
        c = db_conn()
        try:
            c.execute("UPDATE jobs SET status=? WHERE id=? AND status IN "
                      "('queued','running')", (status, jid))
            c.commit()
        finally:
            c.close()


def jobs_ahead(job):
    """How many jobs were queued or running before this one."""
    c = db_conn()
    try:
        return c.execute("SELECT COUNT(*) FROM jobs WHERE status IN "
                         "('queued','running') AND created_ts <= ? AND id != ?",
                         (job["created_ts"], job["id"])).fetchone()[0]
    finally:
        c.close()


def job_get(jid):
    c = db_conn()
    try:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        return dict(row) if row else None
    finally:
        c.close()


def jobs_recent(limit=20):
    c = db_conn()
    try:
        rows = c.execute("SELECT id,status,model,task_type,created_ts,done_ts "
                         "FROM jobs ORDER BY created_ts DESC LIMIT ?",
                         (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def start_job(kwargs):
    """Run a delegation in the background; return a job id immediately."""
    jid = job_create(kwargs.get("model"), kwargs.get("task_type"),
                     kwargs.get("prompt"), status="queued")

    def _worker():
        try:
            r = do_delegate(on_start=lambda: job_mark(jid, "running"), **kwargs)
            job_finish(jid, result=r)
        except Exception as e:  # pragma: no cover
            job_finish(jid, error=str(e))

    threading.Thread(target=_worker, daemon=True).start()
    return jid


def do_delegate(model, prompt, system=None, source="mcp", checks=None,
                escalate_to=None, no_cache=False, task_type=None, budget=None,
                think=None, options=None, on_start=None):
    """Run a prompt on Ollama: auto-select if no model, check cache, optionally
    verify and escalate, record cost/throughput, and cache verified results."""
    if not prompt:
        return {"ok": False, "error": "'prompt' is required"}
    auto = False
    if not model:
        model, why = pick_model(task_type, budget)
        if not model:
            return {"ok": False, "error": "auto-select failed: %s" % why}
        auto = True
        if not escalate_to:
            # Free safety ladder: next size up in the same family.
            escalate_to = pick_escalation(model, task_type)
    checks = checks or {}
    fmt = "json" if checks.get("require_json") else None
    use_cache = (cfg_get("cache_enabled", "1") == "1") and not no_cache
    k_think = caller_think(think)
    k_opts = caller_options(options)
    key = _cache_key(model, prompt, system, fmt, k_think, k_opts) if use_cache else None
    if key:
        hit = cache_get(key)
        if hit:
            cache_touch(key)
            text = hit["response"]
            saved = est_claude_tokens(text)
            cost = est_cost_saved(saved)
            eid = log_event("INFO", source, "delegate",
                      message="[cache hit] ~%d saved ($%.4f)" % (saved, cost),
                      model=hit["model"], prompt=prompt, response=text,
                      duration_ms=0, prompt_tokens=0, response_tokens=0,
                      claude_saved=saved, cost_saved=cost, cached=1,
                      task_type=task_type, budget=budget)
            return {"ok": True, "model": hit["model"], "response": text,
                    "duration_ms": 0, "prompt_tokens": 0, "response_tokens": 0,
                    "tokens_offloaded": 0, "claude_saved": saved,
                    "cost_saved": cost, "tok_per_sec": None, "verified": True,
                    "checks_failed": [], "escalated": False, "cached": True,
                    "auto_selected": auto, "event_id": eid}
    chain = [model] + ([escalate_to] if escalate_to else [])
    last = None
    errors = []
    for i, m in enumerate(chain):
        t0 = time.time()
        try:
            res = ollama_generate(m, prompt, system=system, fmt=fmt,
                                  think=think, options=options,
                                  on_start=on_start if i == 0 else None)
        except OllamaError as e:
            ms = int((time.time() - t0) * 1000)
            log_event("ERROR", source, "delegate", message=str(e), model=m,
                      prompt=prompt, duration_ms=ms, task_type=task_type,
                      budget=budget)
            errors.append("%s: %s" % (m, e))
            continue
        ms = int((time.time() - t0) * 1000)
        text = res.get("response", "")
        p_tok = res.get("prompt_eval_count")
        r_tok = res.get("eval_count")
        offloaded = (p_tok or 0) + (r_tok or 0)
        saved = est_claude_tokens(text)
        cost = est_cost_saved(saved)
        tps = _tok_per_sec(res)
        # Always verify: even with no checks requested, empty output and a
        # silently truncated prompt are failures worth catching.
        ok, reasons = verify_output(text, checks)
        est_p = est_claude_tokens(prompt)
        if p_tok and est_p > 1000 and p_tok < est_p * 0.5:
            # Ollama evaluated far fewer prompt tokens than the prompt holds:
            # the context window likely clipped the input. (KV-cache reuse can
            # also lower this count, hence the wide 50% margin.)
            ok = False
            reasons = reasons + [
                "prompt likely truncated (model evaluated ~%d of ~%d tokens)"
                % (p_tok, est_p)]
        vb = res.get("_vb") or {}
        thinking_chars = len(res.get("thinking") or "")
        vmsg = "verified" if ok else ("unverified: " + "; ".join(reasons))
        if not checks:
            vmsg += ", no caller checks"
        vmsg += "; think %s%s; ctx %s%s" % (
            vb.get("think", "unknown"),
            (" %d chars" % thinking_chars) if thinking_chars else "",
            vb.get("num_ctx") or "model default",
            " auto" if vb.get("num_ctx_auto") else "")
        note = "escalated " if i > 0 else ("auto " if auto else "")
        eid = log_event("INFO" if ok else "WARN", source, "delegate",
                  message="%s~%d saved ($%.4f, %d offloaded) %dms [%s]"
                          % (note, saved, cost, offloaded, ms, vmsg),
                  model=m, prompt=prompt, response=text, duration_ms=ms,
                  prompt_tokens=p_tok, response_tokens=r_tok, claude_saved=saved,
                  cost_saved=cost, cached=0, tok_per_sec=tps,
                  task_type=task_type, budget=budget)
        last = {"ok": True, "model": m, "response": text, "duration_ms": ms,
                "prompt_tokens": p_tok, "response_tokens": r_tok,
                "tokens_offloaded": offloaded, "claude_saved": saved,
                "cost_saved": cost, "tok_per_sec": tps, "verified": ok,
                "checks_failed": reasons, "escalated": i > 0, "cached": False,
                "auto_selected": auto, "event_id": eid,
                "think": vb.get("think"), "thinking_chars": thinking_chars,
                "num_ctx": vb.get("num_ctx"), "num_ctx_auto": vb.get("num_ctx_auto"),
                "caller_checks": bool(checks)}
        if ok:
            if key:
                cache_put(key, m, text, p_tok, r_tok)
            return last
    if last is not None:
        return last
    return {"ok": False, "error": "; ".join(errors) or "delegation failed",
            "model": model}


def get_stats():
    c = db_conn()
    try:
        row = c.execute(
            """SELECT
                 SUM(CASE WHEN type='delegate' AND level!='ERROR' THEN 1 ELSE 0 END) tasks,
                 SUM(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN COALESCE(prompt_tokens,0)+COALESCE(response_tokens,0)
                          ELSE 0 END) toks,
                 SUM(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN COALESCE(claude_saved,0) ELSE 0 END) saved,
                 SUM(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN COALESCE(cost_saved,0) ELSE 0 END) cost,
                 SUM(CASE WHEN type='delegate' AND cached=1 THEN 1 ELSE 0 END) chits,
                 AVG(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN duration_ms END) avg_ms,
                 SUM(CASE WHEN type='delegate' AND level='ERROR' THEN 1 ELSE 0 END) fails
               FROM events""").fetchone()
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        row24 = c.execute(
            """SELECT
                 SUM(CASE WHEN type='delegate' AND level!='ERROR' THEN 1 ELSE 0 END) tasks,
                 SUM(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN COALESCE(prompt_tokens,0)+COALESCE(response_tokens,0)
                          ELSE 0 END) toks,
                 SUM(CASE WHEN type='delegate' AND level!='ERROR'
                          THEN COALESCE(claude_saved,0) ELSE 0 END) saved
               FROM events WHERE ts >= ?""", (cutoff,)).fetchone()
        ci = cache_info()
        return {
            "tasks": row["tasks"] or 0,
            "tokens_offloaded": row["toks"] or 0,
            "claude_saved": row["saved"] or 0,
            "cost_saved": round(row["cost"] or 0, 4),
            "cache_hits": row["chits"] or 0,
            "cache_entries": ci["entries"],
            "avg_latency_ms": int(row["avg_ms"]) if row["avg_ms"] else 0,
            "failures": row["fails"] or 0,
            "tasks_24h": row24["tasks"] or 0,
            "tokens_24h": row24["toks"] or 0,
            "claude_saved_24h": row24["saved"] or 0,
        }
    finally:
        c.close()


def recommend_model(task, budget=None):
    """Suggest a model using the family taxonomy, budget and rating scoreboard."""
    t = (task or "").lower()
    code_words = ("code", "python", "javascript", "function", "regex", "sql",
                  "refactor", "bug", "script", "typescript", "rust", "go ")
    if any(w in t for w in code_words):
        tt = "code"
    elif any(w in t for w in ("image", "photo", "screenshot", "vision", "picture")):
        tt = "vision"
    elif "json" in t or "extract" in t:
        tt = "json"
    else:
        tt = "general"
    pick, why = pick_model(tt, budget)
    if not pick:
        return {"ok": False, "error": why}
    try:
        names = [m["name"] for m in ollama_tags()]
    except OllamaError:
        names = []
    return {"ok": True, "task_type": tt, "recommended": pick, "why": why,
            "models": names,
            "note": "Pass this as model, or call delegate_task with task_type "
                    "and let the bridge pick."}


def human_size(n):
    if not n:
        return "-"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return "%.1f%s" % (n, unit)
        n /= 1024
    return "%.1fPB" % n


# --------------------------------------------------------------------------- #
# MCP stdio server (hand-rolled JSON-RPC 2.0, newline-delimited)              #
# --------------------------------------------------------------------------- #
def _send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _result(mid, result):
    _send({"jsonrpc": "2.0", "id": mid, "result": result})


def _error(mid, code, message):
    _send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})


def mcp_tools():
    return [
        {
            "name": "delegate_task",
            "description": (
                "Run a prompt on a LOCAL Ollama model instead of doing the work "
                "yourself, to save Claude tokens. Best for well-scoped, "
                "lower-stakes subtasks: summarizing, classifying, extracting, "
                "drafting, reformatting, or simple code. Pass the exact model "
                "name (from list_models) you judge capable. Returns the model's "
                "full text output. If Ollama is unreachable it returns an error "
                "and you should just do the task yourself. Optional checks "
                "(require_json, must_include, min_length) verify the output; "
                "escalate_to retries a failed check on a bigger model. Empty "
                "output and likely prompt truncation are always flagged as "
                "failed checks. Omit model and pass task_type to let the "
                "bridge choose (family-aware; it also auto-fills escalate_to "
                "with the next-size-up same-family model)."),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "model": {"type": "string",
                              "description": "Exact Ollama model name (e.g. 'llama3.2:3b'). Optional: omit and pass task_type to let the bridge pick."},
                    "prompt": {"type": "string",
                               "description": "The full instruction/content for the model."},
                    "system": {"type": "string",
                               "description": "Optional system prompt to steer the model."},
                    "require_json": {"type": "boolean",
                               "description": "Verify output parses as JSON (also enables Ollama JSON mode)."},
                    "must_include": {"type": "array", "items": {"type": "string"},
                               "description": "Verify all these substrings appear in the output."},
                    "ignore_case": {"type": "boolean",
                               "description": "Make must_include matching case-insensitive."},
                    "min_length": {"type": "integer",
                               "description": "Verify output is at least this many characters."},
                    "escalate_to": {"type": "string",
                               "description": "If a check fails, retry once on this (usually larger) model."},
                    "no_cache": {"type": "boolean",
                               "description": "Bypass the response cache for this call (for nondeterministic tasks)."},
                    "task_type": {"type": "string",
                               "description": "If model is omitted, auto-pick for: code, json, extract, classify, summarize, vision, or general."},
                    "budget": {"type": "string",
                               "description": "Auto-pick budget: fast, balanced (default), or quality."},
                    "think": {"type": "string",
                               "description": "vb.1: true, false, low, medium or high. Sent only to a model that can think. Thinking can multiply the tokens a short answer costs (30x measured on gemma4:12b); false for drafting, extracting and classifying."},
                    "options": {"type": "object",
                               "description": "vb.1: Ollama options passed through, e.g. {\"num_ctx\": 8192, \"num_predict\": 400, \"temperature\": 0.2}. Without num_ctx, a model with a very large context gets one sized to the prompt."},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "list_models",
            "description": ("List Ollama models installed locally, with size and "
                            "parameter count, so you can pick one capable of a "
                            "subtask before calling delegate_task."),
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "ollama_status",
            "description": ("Check whether the local Ollama server is reachable, "
                            "its version, and which models are currently loaded."),
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "recommend_model",
            "description": ("Suggest which installed model fits a described "
                            "subtask, using a task taxonomy, budget and the "
                            "rating scoreboard. You make the final choice."),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string",
                             "description": "Short description of the subtask."},
                    "budget": {"type": "string",
                               "description": "fast, balanced (default), or quality."},
                },
                "required": ["task"],
            },
        },
        {
            "name": "get_stats",
            "description": ("Delegation stats: tasks run, approximate tokens "
                            "offloaded from Claude, average latency, failures."),
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "warm_model",
            "description": ("Preload a model into Ollama memory so the next "
                            "delegate_task avoids cold-start latency. Optional."),
            "inputSchema": {
                "type": "object",
                "properties": {"model": {"type": "string"}},
                "required": ["model"],
            },
        },
        {
            "name": "model_scoreboard",
            "description": ("How installed models have performed per task type: "
                            "uses, avg human rating, verified rate, tokens/sec. "
                            "Use it to choose a model."),
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "delegate_async",
            "description": ("Start a delegation in the BACKGROUND and return a "
                            "job id immediately. Use for long jobs (big models, "
                            "large outputs) that would exceed the tool timeout. "
                            "Same options as delegate_task; poll delegate_result. "
                            "Jobs run one at a time; a queued job's time limit "
                            "starts when it runs."),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "model": {"type": "string"},
                    "prompt": {"type": "string"},
                    "system": {"type": "string"},
                    "task_type": {"type": "string"},
                    "budget": {"type": "string"},
                    "require_json": {"type": "boolean"},
                    "must_include": {"type": "array", "items": {"type": "string"}},
                    "min_length": {"type": "integer"},
                    "ignore_case": {"type": "boolean"},
                    "escalate_to": {"type": "string"},
                    "no_cache": {"type": "boolean"},
                    "think": {"type": "string",
                              "description": "vb.1: true, false, low, medium or high (see delegate_task)."},
                    "options": {"type": "object",
                                "description": "vb.1: Ollama options passed through (see delegate_task)."},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "delegate_result",
            "description": ("Fetch the status/result of a background delegation "
                            "started with delegate_async, by job id."),
            "inputSchema": {
                "type": "object",
                "properties": {"job_id": {"type": "string"}},
                "required": ["job_id"],
            },
        },
    ]


def _text(s):
    return [{"type": "text", "text": s}]


def _thinking_note(r):
    """vb.1: one line when the model thought because nobody said not to."""
    if r.get("think") == "default" and r.get("thinking_chars"):
        return ("[%s thought first (~%d chars) because think was not set; "
                "think=false skips that]\n\n" % (r.get("model"), r["thinking_chars"]))
    return ""


def _delegate_result_text(r):
    """Format a do_delegate result dict into (content, is_error) for MCP."""
    if not r.get("ok"):
        return _text("Delegation failed: %s" % r.get("error")), True
    c, e = _delegate_result_text_upstream(r)
    note = _thinking_note(r)
    if note:
        c = [{"type": "text", "text": note + c[0]["text"]}]
    return c, e


def _delegate_result_text_upstream(r):
    """Bryant's 1.4.0 formatting, unchanged."""
    if not r.get("ok"):
        return _text("Delegation failed: %s" % r.get("error")), True
    if not r.get("verified"):
        warn = ("[UNVERIFIED on %s: %s] The output below may be unreliable - "
                "consider doing this yourself.\n\n---\n"
                % (r.get("model"), "; ".join(r.get("checks_failed") or [])))
        return _text(warn + r.get("response", "")), False
    if r.get("escalated"):
        return _text("[escalated to %s, verified]\n\n%s"
                     % (r.get("model"), r.get("response", ""))), False
    if r.get("auto_selected"):
        return _text("[auto-selected %s]\n\n%s"
                     % (r.get("model"), r.get("response", ""))), False
    return _text(r.get("response", "")), False


def _vb_args(args):
    """vb.1: think and options from a tool call: ({think, options}, error)."""
    try:
        think = parse_think(args.get("think"))
    except ValueError as e:
        return {}, str(e)
    opts = args.get("options")
    if opts is not None and not isinstance(opts, dict):
        return {}, "options must be an object, e.g. {\"num_ctx\": 8192}"
    return {"think": think, "options": opts}, None


def mcp_call_tool(name, args):
    """Return (content_list, is_error)."""
    try:
        if name == "delegate_task":
            checks = {}
            if args.get("require_json"):
                checks["require_json"] = True
            if args.get("must_include"):
                checks["must_include"] = args["must_include"]
            if args.get("min_length"):
                checks["min_length"] = args["min_length"]
            if args.get("ignore_case"):
                checks["ignore_case"] = True
            vb, err = _vb_args(args)
            if err:
                return _text(err), True
            r = do_delegate(args.get("model"), args.get("prompt"),
                            system=args.get("system"), source="mcp",
                            checks=checks, escalate_to=args.get("escalate_to"),
                            no_cache=bool(args.get("no_cache")),
                            task_type=args.get("task_type"),
                            budget=args.get("budget"), **vb)
            return _delegate_result_text(r)

        if name == "list_models":
            models = ollama_tags()
            if not models:
                return _text("No models installed. Use the dashboard or "
                             "`ollama pull <name>` to add one."), False
            lines = ["Installed Ollama models:"]
            for m in models:
                lines.append("- %s  (%s, %s)" % (
                    m["name"], m.get("param") or "?", human_size(m.get("size"))))
            return _text("\n".join(lines)), False

        if name == "ollama_status":
            try:
                ver = ollama_version()
            except OllamaError as e:
                return _text("Ollama is NOT reachable at %s (%s)."
                             % (ollama_host(), e)), False
            running = [describe_loaded(d) for d in ollama_ps_detail()]
            return _text("Ollama %s is up at %s. Loaded models: %s"
                         % (ver, ollama_host(), "; ".join(running) or "none")), False

        if name == "recommend_model":
            r = recommend_model(args.get("task", ""), args.get("budget"))
            if not r.get("ok"):
                return _text("Could not recommend: %s" % r.get("error")), True
            return _text("Recommended: %s (%s)\nAvailable: %s\n%s"
                         % (r["recommended"], r["why"],
                            ", ".join(r["models"]) or "none", r["note"])), False

        if name == "warm_model":
            try:
                ollama_warm(args.get("model"))
                log_event("INFO", "mcp", "warm", message="warmed",
                          model=args.get("model"))
                return _text("Warmed %s (kept in memory)." % args.get("model")), False
            except OllamaError as e:
                return _text("Warm failed: %s" % e), True

        if name == "model_scoreboard":
            board = scoreboard()
            if not board:
                return _text("No delegations recorded yet."), False
            lines = ["model | task | uses | rating | verified% | tok/s"]
            for b in board:
                ar = ("%.2f" % b["ar"]) if b["rn"] else "-"
                vr = "%d%%" % round((b["vr"] or 0) * 100)
                tps = ("%.0f" % b["tps"]) if b["tps"] else "-"
                lines.append("%s | %s | %d | %s | %s | %s"
                             % (b["model"], b["task_type"], b["n"], ar, vr, tps))
            return _text("\n".join(lines)), False

        if name == "delegate_async":
            checks = {}
            if args.get("require_json"):
                checks["require_json"] = True
            if args.get("must_include"):
                checks["must_include"] = args["must_include"]
            if args.get("min_length"):
                checks["min_length"] = args["min_length"]
            if args.get("ignore_case"):
                checks["ignore_case"] = True
            if not args.get("prompt"):
                return _text("prompt is required"), True
            vb, err = _vb_args(args)
            if err:
                return _text(err), True
            kwargs = {"model": args.get("model"), "prompt": args.get("prompt"),
                      "system": args.get("system"), "source": "mcp",
                      "checks": checks, "escalate_to": args.get("escalate_to"),
                      "no_cache": bool(args.get("no_cache")),
                      "task_type": args.get("task_type"),
                      "budget": args.get("budget")}
            kwargs.update(vb)
            jid = start_job(kwargs)
            return _text("Started background job %s. Poll with "
                         "delegate_result(job_id=\"%s\")." % (jid, jid)), False

        if name == "delegate_result":
            job = job_get(args.get("job_id"))
            if not job:
                return _text("No such job: %s" % args.get("job_id")), True
            if job["status"] == "queued":
                return _text("Job %s queued (created %s): %d job(s) ahead of it. "
                             "One runs at a time; its time limit starts when it runs."
                             % (job["id"], job["created_ts"], jobs_ahead(job))), False
            if job["status"] == "running":
                return _text("Job %s still running (started %s)."
                             % (job["id"], job["created_ts"])), False
            if job["status"] == "error":
                return _text("Job %s failed: %s" % (job["id"], job["error"])), True
            try:
                r = json.loads(job["result"])
            except Exception:
                return _text("Job %s done but result unreadable." % job["id"]), True
            return _delegate_result_text(r)

        if name == "get_stats":
            s = get_stats()
            return _text(
                "Delegations: %d (last 24h: %d)\n"
                "Est. Claude tokens saved: %d (last 24h: %d)\n"
                "Est. cost avoided: $%.2f\n"
                "Cache hits: %d (cached entries: %d)\n"
                "Tokens offloaded to Ollama: %d (last 24h: %d)\n"
                "Avg latency: %d ms\nFailures: %d"
                % (s["tasks"], s["tasks_24h"], s["claude_saved"],
                   s["claude_saved_24h"], s["cost_saved"], s["cache_hits"],
                   s["cache_entries"], s["tokens_offloaded"],
                   s["tokens_24h"], s["avg_latency_ms"], s["failures"])), False

        return _text("Unknown tool: %s" % name), True
    except Exception as e:
        log_event("ERROR", "mcp", "tool_error", message="%s: %s" % (name, e))
        return _text("Tool error: %s" % e), True


def handle_mcp(msg):
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    is_notification = "id" not in msg

    if method == "initialize":
        pv = params.get("protocolVersion") or "2024-11-05"
        ci = (params.get("clientInfo") or {}).get("name", "?")
        log_event("INFO", "mcp", "initialize", message="client=%s pv=%s" % (ci, pv))
        _result(mid, {
            "protocolVersion": pv,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "llama-bridge", "version": VERSION},
        })
    elif method in ("notifications/initialized", "initialized",
                    "notifications/cancelled"):
        return  # notifications get no response
    elif method == "ping":
        _result(mid, {})
    elif method == "tools/list":
        _result(mid, {"tools": mcp_tools()})
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        content, is_err = mcp_call_tool(name, args)
        _result(mid, {"content": content, "isError": is_err})
    else:
        if not is_notification:
            _error(mid, -32601, "Method not found: %s" % method)


def run_mcp():
    init_db()
    log_event("INFO", "mcp", "start", message="MCP stdio server started")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            _error(None, -32700, "Parse error")
            continue
        try:
            if isinstance(msg, list):
                for m in msg:
                    handle_mcp(m)
            else:
                handle_mcp(msg)
        except Exception as e:
            sys.stderr.write("mcp handler error: %s\n" % e)
    log_event("INFO", "mcp", "stop", message="MCP stdio server stopped")


# --------------------------------------------------------------------------- #
# Web dashboard + REST API                                                    #
# --------------------------------------------------------------------------- #
def events_query(limit=120, etype=None, level=None):
    limit = max(1, min(int(limit or 120), 500))
    sql = "SELECT * FROM events"
    where, params = [], []
    if etype:
        where.append("type=?")
        params.append(etype)
    if level:
        where.append("level=?")
        params.append(level)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    c = db_conn()
    try:
        rows = c.execute(sql, params).fetchall()
    finally:
        c.close()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("prompt", "response"):
            if d.get(k) and len(d[k]) > 4000:
                d[k] = d[k][:4000] + "\n...[truncated]"
        out.append(d)
    return out


def status_payload():
    host = ollama_host()
    up, ver, running = False, None, []
    try:
        ver = ollama_version()
        up = True
        running = ollama_ps()
    except OllamaError:
        up = False
    return {
        "ollama_up": up, "host": host, "version": ver, "running": running,
        "default_model": cfg_get("default_model"), "bridge_version": VERSION,
    }


def _pull_worker(name):
    log_event("INFO", "gui", "pull", message="pull started", model=name)
    last = None
    try:
        for chunk in ollama_pull_stream(name):
            st = chunk.get("status", "")
            if chunk.get("error"):
                log_event("ERROR", "gui", "pull", message=chunk["error"], model=name)
                return
            if st and st != last:
                last = st
                log_event("INFO", "gui", "pull", message=st, model=name)
        log_event("INFO", "gui", "pull", message="pull complete", model=name)
    except OllamaError as e:
        log_event("ERROR", "gui", "pull", message=str(e), model=name)


class Handler(BaseHTTPRequestHandler):
    server_version = "LlamaBridge/" + VERSION

    def log_message(self, *a):  # silence default stderr access log
        pass

    # -- helpers ----------------------------------------------------------- #
    def _send(self, body, status=200, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    _LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1", "[::1]")

    def _origin_ok(self):
        """Reject DNS-rebinding and cross-site requests to the local API."""
        host = (self.headers.get("Host") or "").strip().lower()
        if host.startswith("["):
            hostname = host.split("]", 1)[0] + "]"
        else:
            hostname = host.split(":", 1)[0]
        if hostname not in self._LOCAL_HOSTS:
            return False
        origin = self.headers.get("Origin")
        if origin:
            oh = (urllib.parse.urlparse(origin).hostname or "").lower()
            if oh not in self._LOCAL_HOSTS:
                return False
        return True

    # -- routing ----------------------------------------------------------- #
    def do_GET(self):
        if not self._origin_ok():
            return self._send({"error": "forbidden"}, status=403)
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        path = u.path
        if path == "/":
            return self._send(PAGE, ctype="text/html; charset=utf-8")
        if path == "/favicon.ico":
            return self._send(b"", status=204, ctype="image/x-icon")
        if path == "/api/status":
            return self._send(status_payload())
        if path == "/api/models":
            try:
                return self._send({"ok": True, "models": ollama_tags()})
            except OllamaError as e:
                return self._send({"ok": False, "error": str(e), "models": []})
        if path == "/api/events":
            return self._send({"events": events_query(
                limit=(q.get("limit", [120])[0]),
                etype=(q.get("type", [None])[0]),
                level=(q.get("level", [None])[0]))})
        if path == "/api/stats":
            return self._send(get_stats())
        if path == "/api/config":
            return self._send({"ollama_host": ollama_host(),
                               "default_model": cfg_get("default_model"),
                               "keep_alive": cfg_get("keep_alive", "30m"),
                               "price_in": cfg_get("price_in", "3.0"),
                               "price_out": cfg_get("price_out", "15.0"),
                               "cache_enabled": cfg_get("cache_enabled", "1")})
        if path == "/api/mcp_config":
            cfg, cli = build_mcp_config()
            return self._send({"json": json.dumps(cfg, indent=2), "cli": cli})
        if path == "/api/cache":
            info = cache_info()
            info["enabled"] = (cfg_get("cache_enabled", "1") == "1")
            return self._send(info)
        if path == "/api/scoreboard":
            return self._send({"board": scoreboard()})
        if path == "/api/jobs":
            return self._send({"jobs": jobs_recent()})
        return self._send({"error": "not found"}, status=404)

    def do_POST(self):
        if not self._origin_ok():
            return self._send({"error": "forbidden"}, status=403)
        path = urllib.parse.urlparse(self.path).path
        body = self._read_json()
        if path == "/api/delegate":
            r = do_delegate(body.get("model"), body.get("prompt"),
                            system=body.get("system"), source="gui",
                            task_type=body.get("task_type"),
                            budget=body.get("budget"))
            return self._send(r, status=200 if r.get("ok") else 400)
        if path == "/api/delegate_stream":
            model = body.get("model")
            prompt = body.get("prompt")
            task_type = body.get("task_type")
            budget = body.get("budget")
            if not prompt:
                return self._send({"ok": False, "error": "prompt required"}, 400)
            if not model:
                model, _why = pick_model(task_type, budget)
                if not model:
                    return self._send({"ok": False, "error": "auto-select failed: %s" % _why}, 400)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            t0 = time.time()
            acc = []
            p_tok = None
            r_tok = None
            def emit(obj):
                try:
                    self.wfile.write(("data: " + json.dumps(obj) + "\n\n").encode())
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            emit({"model": model})
            try:
                for ch in ollama_generate_stream(model, prompt, system=body.get("system")):
                    piece = ch.get("response", "")
                    if piece:
                        acc.append(piece)
                        emit({"t": piece})
                    if ch.get("done"):
                        p_tok = ch.get("prompt_eval_count")
                        r_tok = ch.get("eval_count")
            except OllamaError as e:
                emit({"error": str(e)})
                log_event("ERROR", "gui", "delegate", message=str(e),
                          model=model, prompt=prompt, task_type=task_type,
                          budget=budget)
                return
            text = "".join(acc)
            ms = int((time.time() - t0) * 1000)
            saved = est_claude_tokens(text)
            cost = est_cost_saved(saved)
            offloaded = (p_tok or 0) + (r_tok or 0)
            eid = log_event("INFO", "gui", "delegate",
                      message="~%d saved ($%.4f, %d offloaded) %dms [stream]"
                              % (saved, cost, offloaded, ms),
                      model=model, prompt=prompt, response=text, duration_ms=ms,
                      prompt_tokens=p_tok, response_tokens=r_tok,
                      claude_saved=saved, cost_saved=cost, cached=0,
                      task_type=task_type, budget=budget)
            emit({"done": True, "duration_ms": ms, "claude_saved": saved,
                  "cost_saved": cost, "tokens_offloaded": offloaded,
                  "model": model, "event_id": eid})
            return
        if path == "/api/warm":
            name = (body.get("name") or body.get("model") or "").strip()
            if not name:
                return self._send({"ok": False, "error": "model name required"}, 400)
            try:
                ollama_warm(name)
                log_event("INFO", "gui", "warm", message="warmed", model=name)
                return self._send({"ok": True})
            except OllamaError as e:
                return self._send({"ok": False, "error": str(e)}, 400)
        if path == "/api/pull":
            name = (body.get("name") or "").strip()
            if not name:
                return self._send({"ok": False, "error": "model name required"}, 400)
            threading.Thread(target=_pull_worker, args=(name,), daemon=True).start()
            return self._send({"ok": True, "message": "pull started"}, 202)
        if path == "/api/delete":
            name = (body.get("name") or "").strip()
            if not name:
                return self._send({"ok": False, "error": "model name required"}, 400)
            try:
                ollama_delete(name)
                log_event("WARN", "gui", "delete", message="model deleted", model=name)
                return self._send({"ok": True})
            except OllamaError as e:
                log_event("ERROR", "gui", "delete", message=str(e), model=name)
                return self._send({"ok": False, "error": str(e)}, 400)
        if path == "/api/config":
            if "default_model" in body:
                cfg_set("default_model", body["default_model"] or "")
                log_event("INFO", "gui", "config",
                          message="default model = %s" % (body["default_model"] or "none"))
            if body.get("ollama_host"):
                cfg_set("ollama_host", body["ollama_host"].rstrip("/"))
                log_event("INFO", "gui", "config",
                          message="ollama host = %s" % body["ollama_host"])
            if body.get("keep_alive"):
                cfg_set("keep_alive", body["keep_alive"])
                log_event("INFO", "gui", "config",
                          message="keep_alive = %s" % body["keep_alive"])
            for _k in ("price_in", "price_out"):
                if body.get(_k) is not None:
                    cfg_set(_k, body[_k])
            if "cache_enabled" in body:
                cfg_set("cache_enabled", "1" if body["cache_enabled"] else "0")
            for _k in VB_CONFIG:
                if _k in body:
                    _ok, _why = vb_config_set(_k, body[_k])
                    if not _ok:
                        return self._send({"ok": False, "error": _why}, 400)
            return self._send({"ok": True})
        if path == "/api/cache":
            if body.get("clear"):
                n = cache_clear()
                log_event("WARN", "gui", "cache", message="cleared %d entries" % n)
                return self._send({"ok": True, "cleared": n})
            return self._send({"ok": True})
        if path == "/api/rate":
            try:
                eid = int(body.get("id"))
            except (TypeError, ValueError):
                return self._send({"ok": False, "error": "id required"}, 400)
            rating = body.get("rating")
            rating = None if rating in (None, 0, "0") else int(rating)
            return self._send({"ok": set_rating(eid, rating)})
        return self._send({"error": "not found"}, status=404)


def run_gui(port, open_browser=True):
    init_db()
    log_event("INFO", "gui", "start", message="dashboard started on port %d" % port)
    _dm = cfg_get("default_model")
    if _dm:
        def _warm_default():
            try:
                ollama_warm(_dm)
                log_event("INFO", "gui", "warm",
                          message="preloaded default model", model=_dm)
            except OllamaError:
                pass
        threading.Thread(target=_warm_default, daemon=True).start()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    print("Llama Bridge dashboard:  %s" % url)
    print("Ollama host:             %s" % ollama_host())
    print("Log database:            %s" % CFG["db"])
    print("Press Ctrl+C to stop.", flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
        log_event("INFO", "gui", "stop", message="dashboard stopped")
        httpd.shutdown()


# --------------------------------------------------------------------------- #
# The dashboard page (vanilla HTML/CSS/JS, no external dependencies)          #
# --------------------------------------------------------------------------- #
PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Llama Bridge</title>
<style>
  :root{
    --bg:#0d1117; --panel:#161b22; --panel2:#1c2330; --border:#30363d;
    --text:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --good:#3fb950;
    --warn:#d29922; --bad:#f85149; --chip:#21262d;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
       font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  a{color:var(--accent);text-decoration:none}
  header{display:flex;align-items:center;gap:14px;padding:14px 20px;
         border-bottom:1px solid var(--border);background:var(--panel);position:sticky;top:0;z-index:5}
  header h1{font-size:17px;margin:0;font-weight:650;letter-spacing:.2px}
  header .sub{color:var(--muted);font-size:12px}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;
        font-size:12px;background:var(--chip);border:1px solid var(--border)}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--muted)}
  .dot.up{background:var(--good);box-shadow:0 0 6px var(--good)}
  .dot.down{background:var(--bad);box-shadow:0 0 6px var(--bad)}
  main{max-width:1180px;margin:0 auto;padding:20px;display:grid;gap:16px}
  .grid{display:grid;gap:16px}
  .cols{grid-template-columns:1fr 1fr}
  @media(max-width:880px){.cols{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px}
  .card h2{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
  .stat{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:14px}
  .stat .n{font-size:26px;font-weight:680}
  .stat .l{color:var(--muted);font-size:12px;margin-top:2px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--border);vertical-align:top}
  th{color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  tr.clickable{cursor:pointer}
  tr.clickable:hover{background:var(--panel2)}
  input,textarea,select,button{font:inherit;color:var(--text);background:var(--panel2);
    border:1px solid var(--border);border-radius:7px;padding:8px 10px}
  textarea{width:100%;resize:vertical;min-height:78px}
  input,select{width:100%}
  button{background:var(--accent);border-color:var(--accent);color:#0b1220;font-weight:600;cursor:pointer}
  button.ghost{background:var(--panel2);color:var(--text)}
  button.danger{background:transparent;border-color:var(--bad);color:var(--bad);font-weight:500;padding:4px 8px;font-size:12px}
  button:hover{filter:brightness(1.08)}
  .row{display:flex;gap:8px}
  .row > *{flex:1}
  .row .auto{flex:0 0 auto}
  .lvl{font-size:11px;font-weight:700;padding:1px 7px;border-radius:6px}
  .lvl.INFO{color:var(--accent);background:rgba(88,166,255,.12)}
  .lvl.WARN{color:var(--warn);background:rgba(210,153,34,.12)}
  .lvl.ERROR{color:var(--bad);background:rgba(248,81,73,.12)}
  .src{color:var(--muted);font-size:12px}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
  .muted{color:var(--muted)}
  .detail{background:#0b0f14;border:1px solid var(--border);border-radius:8px;
          padding:10px;margin:6px 0 2px;white-space:pre-wrap;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
  .toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
  .tag{font-size:11px;color:var(--muted);background:var(--chip);border:1px solid var(--border);
       border-radius:6px;padding:1px 6px}
  .out{margin-top:10px;white-space:pre-wrap}
  .hint{color:var(--muted);font-size:12px;margin-top:6px}
  .err{color:var(--bad)}
</style>
</head>
<body>
<header>
  <h1>&#129433; Llama Bridge</h1>
  <span class="sub">Claude &rarr; local Ollama, logged</span>
  <span style="flex:1"></span>
  <span class="pill"><span id="dot" class="dot"></span><span id="ollamaState">checking…</span></span>
  <span class="pill mono" id="hostPill">—</span>
</header>

<main>
  <div class="stats">
    <div class="stat"><div class="n" id="sTasks">0</div><div class="l">Tasks delegated</div></div>
    <div class="stat"><div class="n" id="sSaved" style="color:var(--good)">0</div><div class="l">Claude tokens saved (est.)</div></div>
    <div class="stat"><div class="n" id="sCost" style="color:var(--good)">$0</div><div class="l">Est. cost avoided</div></div>
    <div class="stat"><div class="n" id="sToks">0</div><div class="l">~Tokens offloaded</div></div>
    <div class="stat"><div class="n" id="sCache">0</div><div class="l">Cache hits</div></div>
    <div class="stat"><div class="n" id="sLat">0<span style="font-size:14px"> ms</span></div><div class="l">Avg latency</div></div>
    <div class="stat"><div class="n" id="sFail">0</div><div class="l">Failures</div></div>
  </div>

  <div class="grid cols">
    <!-- Models / control -->
    <div class="card">
      <h2>Ollama models</h2>
      <table id="modelTbl"><thead>
        <tr><th>Default</th><th>Model</th><th>Params</th><th>Size</th><th></th></tr>
      </thead><tbody id="modelBody">
        <tr><td colspan="5" class="muted">loading…</td></tr>
      </tbody></table>
      <div class="row" style="margin-top:12px">
        <input id="pullName" placeholder="pull a model, e.g. llama3.2:3b">
        <button class="auto" onclick="pull()">Pull</button>
      </div>
      <div class="hint" id="ctrlHint">Set a default for your own reference; Claude still picks per task.</div>
      <div class="row" style="margin-top:8px">
        <input id="keepAlive" placeholder="keep-alive, e.g. 30m" style="flex:0 0 170px">
        <button class="ghost auto" onclick="saveKeepAlive(event)">Save keep-alive</button>
        <span style="flex:1"></span>
      </div>
      <div class="row" style="margin-top:8px">
        <input id="priceOut" placeholder="output $/Mtok, e.g. 15" style="flex:0 0 170px">
        <button class="ghost auto" onclick="savePrice(event)">Save price</button>
        <label class="tag" style="align-self:center"><input type="checkbox" id="cacheOn" onchange="toggleCache()" style="width:auto;vertical-align:middle"> cache</label>
        <button class="ghost auto" onclick="clearCache(event)">Clear cache</button>
        <span style="flex:1"></span>
      </div>
    </div>

    <!-- Test delegation -->
    <div class="card">
      <h2>Test a delegation</h2>
      <div class="row" style="margin-bottom:8px">
        <select id="testModel"><option value="">(auto — pick for me)</option></select>
      </div>
      <div class="row" style="margin-bottom:8px">
        <select id="testTask" title="task type (used when model is auto)">
          <option value="">task: general</option>
          <option value="code">code</option>
          <option value="json">json</option>
          <option value="extract">extract</option>
          <option value="classify">classify</option>
          <option value="summarize">summarize</option>
          <option value="vision">vision</option>
        </select>
        <select id="testBudget" title="budget (used when model is auto)">
          <option value="">budget: balanced</option>
          <option value="fast">fast</option>
          <option value="quality">quality</option>
        </select>
      </div>
      <textarea id="testPrompt" placeholder="Prompt to send to the model…"></textarea>
      <div class="row" style="margin-top:8px">
        <button onclick="runTest()">Run</button>
        <button class="ghost auto" onclick="document.getElementById('testOut').innerHTML=''">Clear</button>
      </div>
      <div class="out mono" id="testOut"></div>
    </div>
  </div>

  <!-- Connect Claude -->
  <div class="card">
    <h2>Connect Claude (MCP)</h2>
    <div class="hint" style="margin-top:0">Paste into your Claude MCP config (e.g. <span class="mono">claude_desktop_config.json</span>), then restart Claude. Keep this dashboard running alongside to watch activity live.</div>
    <div class="detail mono" id="mcpJson">loading…</div>
    <div class="row" style="margin-top:8px">
      <button class="auto" onclick="copyText(document.getElementById('mcpJson').textContent, this)">Copy config</button>
      <span style="flex:1"></span>
    </div>
    <div class="hint">Or Claude Code CLI:</div>
    <div class="row">
      <input class="mono" id="mcpCli" readonly value="">
      <button class="ghost auto" onclick="copyText(document.getElementById('mcpCli').value, this)">Copy</button>
    </div>
  </div>

  <!-- Model scoreboard -->
  <div class="card">
    <h2>Model scoreboard <span class="tag">learns from your &#128077;/&#128078;</span></h2>
    <table><thead>
      <tr><th>Model</th><th>Task</th><th>Uses</th><th>Rating</th><th>Verified</th><th>Tok/s</th></tr>
    </thead><tbody id="sbBody">
      <tr><td colspan="6" class="muted">loading…</td></tr>
    </tbody></table>
    <div class="hint">Auto-selection prefers higher-rated models per task type.</div>
  </div>

  <!-- Background jobs -->
  <div class="card" id="jobsCard" style="display:none">
    <h2>Background jobs</h2>
    <table><thead><tr><th>Job</th><th>Status</th><th>Model</th><th>Task</th><th>Started</th></tr></thead>
    <tbody id="jobsBody"></tbody></table>
  </div>

  <!-- Live log -->
  <div class="card">
    <div class="toolbar">
      <h2 style="margin:0">Activity log</h2>
      <span style="flex:1"></span>
      <select id="fType" style="width:auto" onchange="loadLog()">
        <option value="">all types</option>
        <option value="delegate">delegate</option>
        <option value="pull">pull</option>
        <option value="delete">delete</option>
        <option value="config">config</option>
        <option value="initialize">initialize</option>
        <option value="start">start</option>
        <option value="tool_error">tool_error</option>
      </select>
      <select id="fLevel" style="width:auto" onchange="loadLog()">
        <option value="">all levels</option>
        <option value="INFO">INFO</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
      </select>
      <label class="tag"><input type="checkbox" id="autoref" checked style="width:auto;vertical-align:middle"> auto</label>
    </div>
    <table><thead>
      <tr><th style="width:90px">Time</th><th style="width:60px">Level</th><th style="width:60px">Src</th>
          <th style="width:90px">Type</th><th style="width:150px">Model</th><th>Detail</th></tr>
    </thead><tbody id="logBody">
      <tr><td colspan="6" class="muted">loading…</td></tr>
    </tbody></table>
  </div>
  <div class="muted" style="text-align:center;font-size:12px">Llama Bridge v__VER__ · log is append-only in SQLite</div>
</main>

<script>
const $ = s => document.querySelector(s);
async function j(url, opts){ const r = await fetch(url, opts); return r.json(); }
function esc(s){ return (s==null?'':String(s)).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function jsq(s){ return esc(String(s==null?'':s).replace(/\\/g,'\\\\').replace(/'/g,"\\'")); }
function fmtTime(iso){ try{ return new Date(iso).toLocaleTimeString(); }catch(e){ return iso; } }
function num(n){ return (n||0).toLocaleString(); }

let MODELS = [];

async function loadStatus(){
  const s = await j('/api/status');
  $('#dot').className = 'dot ' + (s.ollama_up?'up':'down');
  $('#ollamaState').textContent = s.ollama_up ? ('Ollama '+(s.version||'')+' up') : 'Ollama offline';
  $('#hostPill').textContent = s.host;
}

async function loadStats(){
  const s = await j('/api/stats');
  $('#sTasks').textContent = num(s.tasks);
  $('#sSaved').textContent = num(s.claude_saved);
  $('#sCost').textContent  = '$' + (s.cost_saved||0).toFixed(2);
  $('#sToks').textContent  = num(s.tokens_offloaded);
  $('#sCache').textContent = num(s.cache_hits);
  $('#sLat').innerHTML     = num(s.avg_latency_ms) + '<span style="font-size:14px"> ms</span>';
  $('#sFail').textContent  = num(s.failures);
}

async function loadModels(){
  const r = await j('/api/models');
  const cfg = await j('/api/config');
  if(cfg.keep_alive && document.getElementById('keepAlive') && !$('#keepAlive').value) $('#keepAlive').value = cfg.keep_alive;
  if(cfg.price_out && document.getElementById('priceOut') && !$('#priceOut').value) $('#priceOut').value = cfg.price_out;
  if(document.getElementById('cacheOn')) $('#cacheOn').checked = (cfg.cache_enabled==='1' || cfg.cache_enabled===true);
  MODELS = r.models || [];
  const tb = $('#modelBody');
  if(!r.ok){ tb.innerHTML = '<tr><td colspan="5" class="err">'+esc(r.error)+'</td></tr>'; }
  else if(!MODELS.length){ tb.innerHTML = '<tr><td colspan="5" class="muted">No models. Pull one below.</td></tr>'; }
  else {
    tb.innerHTML = MODELS.map(m => {
      const def = (cfg.default_model===m.name);
      return '<tr>'+
        '<td><input type="radio" name="def" '+(def?'checked':'')+' onclick="setDefault(\''+jsq(m.name)+'\')" style="width:auto"></td>'+
        '<td class="mono">'+esc(m.name)+'</td>'+
        '<td>'+esc(m.param||'?')+'</td>'+
        '<td>'+esc(hsize(m.size))+'</td>'+
        '<td><button class="ghost" style="padding:4px 8px;font-size:12px" onclick="warm(\''+jsq(m.name)+'\')">warm</button> <button class="danger" onclick="del(\''+jsq(m.name)+'\')">delete</button></td>'+
      '</tr>';
    }).join('');
  }
  const sel = $('#testModel');
  const cur = sel.value;
  sel.innerHTML = '<option value="">(auto — pick for me)</option>' +
    MODELS.map(m=>'<option value="'+esc(m.name)+'">'+esc(m.name)+'</option>').join('');
  if(cur) sel.value = cur;
  else if(cfg.default_model) sel.value = cfg.default_model;
}
function hsize(n){ if(!n) return '-'; const u=['B','KB','MB','GB','TB']; let i=0; n=+n;
  while(n>=1024 && i<u.length-1){ n/=1024; i++; } return n.toFixed(1)+u[i]; }

async function loadLog(){
  const t = $('#fType').value, l = $('#fLevel').value;
  const r = await j('/api/events?limit=200'+(t?'&type='+t:'')+(l?'&level='+l:''));
  const tb = $('#logBody');
  if(!r.events.length){ tb.innerHTML='<tr><td colspan="6" class="muted">No events yet.</td></tr>'; return; }
  tb.innerHTML = r.events.map(e=>{
    const hasDetail = e.prompt || e.response;
    const main = '<tr class="'+(hasDetail?'clickable':'')+'" onclick="toggle('+e.id+')">'+
      '<td class="muted">'+esc(fmtTime(e.ts))+'</td>'+
      '<td><span class="lvl '+esc(e.level)+'">'+esc(e.level)+'</span></td>'+
      '<td class="src">'+esc(e.source)+'</td>'+
      '<td>'+esc(e.type)+'</td>'+
      '<td class="mono">'+esc(e.model||'')+'</td>'+
      '<td>'+esc(e.message||'')+ (hasDetail?' <span class="tag">details</span>':'') +'</td>'+
    '</tr>';
    let det = '';
    if(hasDetail){
      det = '<tr id="d'+e.id+'" style="display:none"><td colspan="6">'+
        (e.prompt?'<div class="muted">prompt</div><div class="detail">'+esc(e.prompt)+'</div>':'')+
        (e.response?'<div class="muted">response ('+num(e.response_tokens)+' tok · ~'+num(e.claude_saved)+' saved · $'+(e.cost_saved||0).toFixed(4)+(e.cached?' · cache hit':(e.tok_per_sec?' · '+e.tok_per_sec+' tok/s':''))+' · '+num(e.duration_ms)+' ms)</div><div class="detail">'+esc(e.response)+'</div>':'')+
        ((e.type==='delegate'&&e.response)?'<div style="margin-top:6px">rate:'+ratebtns(e.id)+' '+(e.rating>0?'<span class="tag">rated &#128077;</span>':(e.rating<0?'<span class="tag">rated &#128078;</span>':''))+'</div>':'')+
        '</td></tr>';
    }
    return main+det;
  }).join('');
}
function toggle(id){ const el=document.getElementById('d'+id); if(el) el.style.display = el.style.display==='none'?'':'none'; }

async function setDefault(name){
  await j('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({default_model:name})});
  loadLog();
}
async function pull(){
  const name = $('#pullName').value.trim(); if(!name) return;
  $('#ctrlHint').textContent = 'Pulling '+name+' … watch the log below.';
  await j('/api/pull',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  $('#pullName').value=''; setTimeout(loadLog,500);
}
async function del(name){
  if(!confirm('Delete model '+name+'?')) return;
  const r = await j('/api/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  if(!r.ok) alert('Delete failed: '+r.error);
  loadModels(); loadLog();
}
function ratebtns(id){ return ' <button class="ghost" style="padding:2px 7px;font-size:12px" onclick="rate('+id+',1,event)">&#128077;</button> <button class="ghost" style="padding:2px 7px;font-size:12px" onclick="rate('+id+',-1,event)">&#128078;</button>'; }
async function runTest(){
  const model = $('#testModel').value;
  const prompt = $('#testPrompt').value;
  const task_type = $('#testTask') ? $('#testTask').value : '';
  const budget = $('#testBudget') ? $('#testBudget').value : '';
  if(!prompt.trim()){ $('#testOut').innerHTML='<span class="err">Enter a prompt.</span>'; return; }
  $('#testOut').innerHTML = '<div class="tag" id="testMeta">'+(model?('streaming from '+esc(model)+' …'):'auto-selecting a model …')+'</div><div class="detail" id="testStream"></div>';
  const out = document.getElementById('testStream');
  try{
    const resp = await fetch('/api/delegate_stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model,prompt,task_type,budget})});
    const reader = resp.body.getReader(); const dec = new TextDecoder(); let buf='', picked=model;
    while(true){
      const {done, value} = await reader.read(); if(done) break;
      buf += dec.decode(value,{stream:true});
      let idx;
      while((idx = buf.indexOf('\n\n')) >= 0){
        const line = buf.slice(0, idx); buf = buf.slice(idx+2);
        if(!line.startsWith('data: ')) continue;
        let obj; try{ obj = JSON.parse(line.slice(6)); }catch(e){ continue; }
        if(obj.model && !obj.done){ picked=obj.model; $('#testMeta').textContent='streaming from '+picked+' …'; }
        else if(obj.t){ out.textContent += obj.t; }
        else if(obj.error){ out.innerHTML += '<span class="err">'+esc(obj.error)+'</span>'; }
        else if(obj.done){ $('#testMeta').innerHTML = esc(picked)+' · ~'+num(obj.claude_saved)+' saved · $'+(obj.cost_saved||0).toFixed(4)+' · '+num(obj.duration_ms)+' ms'+(obj.event_id?ratebtns(obj.event_id):''); }
      }
    }
  }catch(e){ out.innerHTML += '<span class="err">'+esc(e.message||e)+'</span>'; }
  loadStats(); loadLog();
}

function flash(btn,msg){ const o=btn.textContent; btn.textContent=msg; setTimeout(()=>btn.textContent=o,1200); }
async function copyText(text, btn){
  try{ await navigator.clipboard.writeText(text); flash(btn,'Copied!'); }
  catch(e){
    const ta=document.createElement('textarea'); ta.value=text;
    document.body.appendChild(ta); ta.select();
    try{ document.execCommand('copy'); flash(btn,'Copied!'); }catch(_){ flash(btn,'Copy failed'); }
    ta.remove();
  }
}
async function loadMcp(){
  const r = await j('/api/mcp_config');
  $('#mcpJson').textContent = r.json;
  $('#mcpCli').value = r.cli;
}
async function warm(name){
  const r = await j('/api/warm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  if(!r.ok){ alert('Warm failed: '+r.error); } else { loadStatus(); loadLog(); }
}
async function saveKeepAlive(ev){
  const v = $('#keepAlive').value.trim(); if(!v) return;
  await j('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keep_alive:v})});
  if(ev&&ev.target){ flash(ev.target,'Saved!'); }
}
async function savePrice(ev){
  const v = $('#priceOut').value.trim(); if(!v) return;
  await j('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({price_out:v})});
  if(ev&&ev.target){ flash(ev.target,'Saved!'); } loadStats();
}
async function toggleCache(){
  await j('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cache_enabled:$('#cacheOn').checked})});
}
async function clearCache(ev){
  if(!confirm('Clear the response cache?')) return;
  const r = await j('/api/cache',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clear:true})});
  if(ev&&ev.target){ flash(ev.target, r.ok?('Cleared '+r.cleared):'Failed'); }
}
async function rate(id, val, ev){
  if(ev){ ev.stopPropagation(); }
  const r = await j('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id, rating: val})});
  if(ev&&ev.target){ flash(ev.target, r.ok?'✓':'x'); }
  loadScoreboard();
}
async function loadScoreboard(){
  const el = document.getElementById('sbBody'); if(!el) return;
  const r = await j('/api/scoreboard');
  if(!r.board || !r.board.length){ el.innerHTML='<tr><td colspan="6" class="muted">No delegations yet.</td></tr>'; return; }
  el.innerHTML = r.board.map(b=>'<tr>'+
    '<td class="mono">'+esc(b.model)+'</td>'+
    '<td>'+esc(b.task_type)+'</td>'+
    '<td>'+num(b.n)+'</td>'+
    '<td>'+(b.rn?((b.ar>0?'⬆ ':(b.ar<0?'⬇ ':''))+b.ar.toFixed(2)+' ('+b.rn+')'):'—')+'</td>'+
    '<td>'+Math.round((b.vr||0)*100)+'%</td>'+
    '<td>'+(b.tps?b.tps.toFixed(0):'—')+'</td>'+
  '</tr>').join('');
}
async function loadJobs(){
  const el = document.getElementById('jobsBody'); if(!el) return;
  const r = await j('/api/jobs');
  const jobs = r.jobs||[];
  document.getElementById('jobsCard').style.display = jobs.length? '' : 'none';
  el.innerHTML = jobs.map(x=>'<tr>'+
    '<td class="mono">'+esc(x.id)+'</td>'+
    '<td>'+(x.status==='running'||x.status==='queued'?'<span class="lvl WARN">'+x.status+'</span>':(x.status==='error'?'<span class="lvl ERROR">error</span>':'<span class="lvl INFO">done</span>'))+'</td>'+
    '<td class="mono">'+esc(x.model||'auto')+'</td>'+
    '<td>'+esc(x.task_type||'-')+'</td>'+
    '<td class="muted">'+esc(fmtTime(x.created_ts))+'</td>'+
  '</tr>').join('');
}
function tick(){ loadStatus(); if($('#autoref').checked){ loadLog(); loadStats(); } }
loadStatus(); loadModels(); loadStats(); loadLog(); loadMcp(); loadScoreboard(); loadJobs();
setInterval(tick, 2500);
setInterval(loadModels, 12000);
setInterval(loadScoreboard, 15000);
setInterval(loadJobs, 4000);
</script>
</body>
</html>'''
PAGE = PAGE.replace("__VER__", VERSION)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def build_mcp_config():
    """Single source of truth for the MCP config (used by `install` and the UI)."""
    py = sys.executable or "python"
    script = os.path.abspath(__file__)
    cfg = {"mcpServers": {"llama-bridge": {"command": py, "args": [script, "mcp"]}}}
    cli = 'claude mcp add llama-bridge -- "%s" "%s" mcp' % (py, script)
    return cfg, cli


def print_install():
    cfg, cli = build_mcp_config()
    print("Add this to your Claude MCP config (e.g. claude_desktop_config.json):\n")
    print(json.dumps(cfg, indent=2))
    print("\nOr, with Claude Code CLI:\n")
    print("  " + cli)
    print("\nThen run the dashboard separately to watch activity:\n")
    print('  "%s" "%s"' % (sys.executable or "python", os.path.abspath(__file__)))


VB_CONFIG = {
    "think_default": ("", "think when a call does not say: '' (Ollama's default), "
                          "true, false, low, medium or high"),
    "options": ("", "default Ollama options, a JSON object, e.g. {\"temperature\": 0.2}"),
    "num_ctx_auto": ("1", "1: size the window for a model whose own context is very large; 0: never"),
    "num_ctx_auto_above": ("32768", "a model's own context above this counts as very large"),
    "num_ctx_floor": ("8192", "the smallest window num_ctx_auto chooses"),
    "num_ctx_reserve": ("4096", "room left to answer, in tokens, when num_predict is not set"),
    "max_parallel": ("1", "generate calls at once (read when the server starts)"),
    "generate_timeout": ("600", "seconds one generate call may take once it starts"),
}


def vb_config_set(key, value):
    """Check and store one vb.1 setting: (ok, why)."""
    v = "" if value is None else str(value).strip()
    if key == "think_default":
        try:
            parse_think(v)
        except ValueError as e:
            return False, str(e)
    elif key == "options":
        if v:
            try:
                if not isinstance(json.loads(v), dict):
                    raise ValueError
            except ValueError:
                return False, "options must be a JSON object"
    elif key == "num_ctx_auto":
        if v not in ("0", "1"):
            return False, "num_ctx_auto must be 0 or 1"
    elif key in VB_CONFIG:
        try:
            if int(v) < 1:
                raise ValueError
        except ValueError:
            return False, "%s must be a whole number above 0" % key
    else:
        return False, "unknown setting %s" % key
    cfg_set(key, v)
    log_event("INFO", "cli", "config", message="%s = %s" % (key, v or "(unset)"))
    return True, ""


def config_cli(rest):
    if not rest:
        for k, (dflt, what) in VB_CONFIG.items():
            print("%-18s %-10s %s" % (k, cfg_get(k, dflt) or "''", what))
        return 0
    if rest[0] not in VB_CONFIG:
        print("unknown setting %s; known: %s" % (rest[0], ", ".join(VB_CONFIG)))
        return 2
    if len(rest) == 1:
        print(cfg_get(rest[0], VB_CONFIG[rest[0]][0]))
        return 0
    ok, why = vb_config_set(rest[0], " ".join(rest[1:]))
    print("%s = %s" % (rest[0], cfg_get(rest[0])) if ok else why)
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(
        description="Llama Bridge - delegate small tasks from Claude to local Ollama.")
    p.add_argument("mode", nargs="?", default="gui",
                   choices=["gui", "mcp", "install", "config"],
                   help="gui (default), mcp (stdio server), install (print config), "
                        "or config [KEY [VALUE]] (vb.1: show or set a setting)")
    p.add_argument("rest", nargs="*", help="for config: KEY and VALUE")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="dashboard port")
    p.add_argument("--ollama-host", default=None, help="override Ollama base URL")
    p.add_argument("--db", default=None, help="path to the log database")
    p.add_argument("--no-browser", action="store_true", help="don't open a browser")
    args = p.parse_args()

    if args.db:
        CFG["db"] = os.path.abspath(args.db)
    if args.ollama_host:
        CFG["ollama"] = args.ollama_host.rstrip("/")
    CFG["port"] = args.port

    if args.mode == "config":
        init_db()
        raise SystemExit(config_cli(args.rest))
    if args.mode == "install":
        print_install()
    elif args.mode == "mcp":
        run_mcp()
    else:
        run_gui(args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
