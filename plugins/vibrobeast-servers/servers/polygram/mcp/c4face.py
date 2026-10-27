# polygram -- gated agent-skill synthesis.
# Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# This file is part of polygram.  It is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version; or, at your choice, the
# GNU Lesser General Public License, version 3 or later.  It is distributed WITHOUT ANY WARRANTY;
# see <https://www.gnu.org/licenses/>.
# Written by Mentat (for Corwin; claude-opus-5-5), 2026-10-08.

"""c4face -- C4's own MCP server (``<c4>/mcp/c4-mcp.js``, Corwin's, Node stdlib only), served
from the vibrobeast plugin out of the person's own C4 tree, with nothing to edit by hand.

C4 is not copied into the plugin: it lives in the person's tree and changes there.  This server
finds that tree and a Node by itself, then hands its stdin and stdout to
``node <c4>/mcp/c4-mcp.js`` -- the same process the C4 README registers by hand -- so the tools
Claude sees are C4's own (c4_fragments, c4_diagram_*, ...), answered by C4's own code.

Where the C4 tree is looked for, in order (the first that holds ``mcp/c4-mcp.js`` and
``lib/c4-model.js`` wins):

  1. ``C4_ROOT`` in the environment;
  2. the ``c4.root`` preference -- ask Claude to set it (the plugin's ``pref_set``), never JSON;
  3. the ``words.root`` preference, which already names a C4 tree when the person set one;
  4. a ``c4`` folder beside, or up to three folders above, the places this plugin already knows
     about: the seat (``MENTCACHED_SEAT``), the shelf (``freshness.shelf`` / ``POLYGRAM_DIST``)
     and the soft-skill roots -- on the author's machine the seat and C4 are siblings under
     ``F:\\claude``;
  5. the usual guesses: ``/f/claude/c4``, ``F:/claude/c4``, ``~/c4``, ``~/claude/c4``,
     ``~/mnt/c4`` -- skipped when ``C4FACE_GUESS=0`` (the test kits set it, so a machine that
     really has ``F:/claude/c4`` can still test "nothing found"; a person may set it too).

Where Node is looked for: ``VIBROBEAST_NODE``; ``node`` on PATH, skipping any folder under
``WindowsApps``; ``C:\\Program Files\\nodejs\\node.exe``; the MSYS2 trees
(``C:\\msys64\\{ucrt64,mingw64,clang64}\\bin\\node.exe``).  A candidate counts only when it runs
and prints a version.

When either is missing this server answers one tool, ``c4_status``, which says in plain words
what is missing and how to fix it by asking Claude.

OFF UNTIL ASKED (2026-10-08, QA1 row 14; it shipped on by default that morning, and the call was
reversed the same day).  c4-mcp.js and the three lib files it requires read nothing from disk
after loading, write nothing, and open no connection -- they require only ``readline`` and
``path``.  The first build rested "on by default" on a regex over those files, and QA showed a
regex misses ``require(`fs`)``, a variable, ``createRequire``, ``process.binding`` and more.
The check is now an ALLOW-LIST over a small JavaScript lexer (``scan_js``): ``require`` only of
readline/path or ``path.join(__dirname, '..', 'lib', '<name>.js')``; ``process`` only for its
streams, argv and exit; ``module`` only for ``module.exports``; and no ``import``, ``eval``,
``Function``, ``globalThis``, ``constructor`` and the like, as code or as a string.  Any other
shape is a hit, and nothing starts.  Names and strings are decoded first (``js_unescape``:
\\u, \\u{..}, \\x, octal), so an escaped spelling reads as the name it is (QA2 row 7).
But JavaScript can reach any module through a computed name
(``obj["constr" + "uctor"]``), so NO static reading of it is sound, and this one is a tripwire for
an honest change, not a fence against a hostile one.  So the server is off until the person asks
Claude to turn it on (the ``c4.on`` preference, set with ``pref_set``; or ``C4_ON=1``), and the
tripwire still runs at every start.  Falsifier of the OFF call: a check that is sound for what C4
uses -- e.g. node's own permission model (``node --permission`` with reads allowed only under
``<c4>/mcp`` and ``<c4>/lib``, and no child processes, workers or addons) verified on the node
versions the plugin meets -- would let this be on by default again.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"

#: 2026-10-08 (QA1 row 14): the guard is an ALLOW-LIST read from a small JavaScript lexer, not a
#: regex.  It is a tripwire for an honest change, not a fence against a hostile one: JavaScript can
#: reach any module through computed names (``obj["constr" + "uctor"]``), and no static reading of
#: it is sound.  So c4face is OFF until the person asks (pref ``c4.on``), and this guard still runs
#: every start.  bin/tp2mt checks that it is here; tests/c4face-tests.sh plants each evasion.
ALLOW_MODULES = frozenset({"readline", "path", "node:readline", "node:path"})
#: Names that, as code, reach modules, processes or code-from-strings.  Any one is a hit.
DENY_NAMES = frozenset({"import", "eval", "Function", "globalThis", "global", "createRequire",
                        "constructor", "__proto__", "Reflect", "Proxy", "WebAssembly", "fetch",
                        "XMLHttpRequest", "WebSocket", "Worker", "dlopen", "binding",
                        "_linkedBinding", "mainModule", "_load", "getBuiltinModule"})
#: The same names as string contents: the way to reach them by ``obj["name"]``.
DENY_STRINGS = DENY_NAMES | {"prototype", "require", "process", "module"}
#: The only members of ``process`` C4 may touch: its three streams, its arguments, and exiting.
PROCESS_OK = frozenset({"stdin", "stdout", "stderr", "argv", "exit", "exitCode"})
_LIBNAME = re.compile(r"[A-Za-z0-9_.-]+\.js\Z")
_KW_BEFORE_REGEX = frozenset({"return", "typeof", "case", "do", "else", "in", "of", "new", "delete",
                              "void", "throw", "instanceof", "yield", "await"})
_PUNCT3 = ("===", "!==", "**=", "...", "<<=", ">>=", ">>>", "&&=", "||=", "??=")
#: 2026-10-08 (FOLD-QA2 row 7): JavaScript lets a name or a string be spelled with escapes
#: (``requir\u0065``, ``"\x63onstructor"``), and node runs them.  Every identifier and every string
#: is decoded by ``js_unescape`` BEFORE it is matched; an identifier escape the decoder cannot read is
#: itself a hit.
_ESC = re.compile(r"\\(?:x([0-9A-Fa-f]{2})|u([0-9A-Fa-f]{4})|u\{([0-9A-Fa-f]+)\}|([0-3][0-7]{0,2}|[4-7][0-7]?)"
                  r"|(\r\n|[\n\r\u2028\u2029])|(.))", re.S)
_ID_ESC = re.compile(r"\\u(?:([0-9A-Fa-f]{4})|\{([0-9A-Fa-f]+)\})")
_SIMPLE = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v"}


def _cp(h: str) -> str:
    v = int(h, 16)
    return chr(v) if v <= 0x10FFFF else "\ufffd"


def js_unescape(raw: str, ident: bool = False) -> str:
    """The text JavaScript means by ``raw``.  ident=False: a string or template body (\\xHH,
    \\uXXXX, \\u{...}, legacy octal, line continuations, \\n and kin, and \\c for any other c).
    ident=True: an identifier, where only \\uXXXX and \\u{...} exist; anything else is left with
    its backslash, and the caller treats that as a name it cannot read."""
    if ident:
        return _ID_ESC.sub(lambda m: _cp(m.group(1) or m.group(2)), raw)

    def one(m):
        x, u4, ub, oc, nl, ch = m.groups()
        if x or u4 or ub:
            return _cp(x or u4 or ub)
        if oc:
            return chr(int(oc, 8))
        if nl:
            return ""
        return _SIMPLE.get(ch, ch)
    return _ESC.sub(one, raw)


_PUNCT2 = ("=>", "==", "!=", "<=", ">=", "&&", "||", "??", "?.", "++", "--", "+=", "-=", "*=", "/=",
           "%=", "&=", "|=", "^=", "<<", ">>", "**")


MEANS = ("Turning C4 on lets Claude use your C4 work surface (fragments, diagrams, doors) by "
         "running C4's own server, mcp/c4-mcp.js from your C4 folder, with node. That program is "
         "yours and changes in your folder; this plugin checks it at every start and does not run "
         "it if it asks for a network, process or file module, but that check is a tripwire, not "
         "a fence.")
HOW_ON = ("Ask Claude: \"turn C4 on\". Claude sets the preference c4.on to on with the plugin's "
          "pref_set tool; then restart Claude (or the vibrobeast plugin). Nothing to edit by hand.")

HOW_ROOT = ("Tell Claude where your C4 folder is (the one holding mcp/c4-mcp.js), and ask it to set "
            "the preference c4.root to that folder with the plugin's pref_set tool; then restart "
            "Claude (or the vibrobeast plugin). Nothing to edit by hand.")
HOW_NODE = ("Install Node.js (https://nodejs.org, the LTS installer for Windows, or your system's "
            "package), then restart Claude. If Node lives somewhere unusual, the environment "
            "variable VIBROBEAST_NODE can name it.")


def _pref(key: str) -> str:
    try:
        from . import prefs
        return (prefs.get(key) or "").strip()
    except Exception:
        return ""


def is_on() -> bool:
    from .rpc import env_switch
    sw = env_switch("C4_ON")
    if sw is not None:
        return sw
    return _pref("c4.on").lower() in ("on", "1", "true", "yes")


def _named(raw: str):
    raw = (raw or "").strip()
    if not raw or "${" in raw or raw.startswith("$"):
        return None
    return Path(raw).expanduser()


def is_c4(p: Path) -> bool:
    try:
        return (p / "mcp" / "c4-mcp.js").is_file() and (p / "lib" / "c4-model.js").is_file()
    except OSError:
        return False


def c4_candidates() -> list[tuple[str, Path]]:
    """(where the guess came from, folder) in the order they are tried."""
    out: list[tuple[str, Path]] = []
    for why, raw in (("C4_ROOT", os.environ.get("C4_ROOT", "")),
                     ("preference c4.root", _pref("c4.root")),
                     ("preference words.root", _pref("words.root"))):
        p = _named(raw)
        if p is not None:
            out.append((why, p))
    anchors: list[tuple[str, str]] = [("MENTCACHED_SEAT", os.environ.get("MENTCACHED_SEAT", "")),
                                      ("preference freshness.shelf", _pref("freshness.shelf")),
                                      ("POLYGRAM_DIST", os.environ.get("POLYGRAM_DIST", ""))]
    for r in _pref("softskills.roots").split(os.pathsep):
        anchors.append(("preference softskills.roots", r))
    for why, raw in anchors:
        a = _named(raw)
        if a is None:
            continue
        up = a
        for _ in range(4):                      # beside it, then up to three folders above
            out.append((f"a c4 folder near {why}", up / "c4"))
            if up.parent == up:
                break
            up = up.parent
    home = Path.home()
    guesses = () if os.environ.get("C4FACE_GUESS", "").strip() == "0" else (
        ("the author's layout /f/claude/c4", Path("/f/claude/c4")),
        ("the author's layout F:/claude/c4", Path("F:/claude/c4")),
        ("~/c4", home / "c4"), ("~/claude/c4", home / "claude" / "c4"),
        ("~/mnt/c4", home / "mnt" / "c4"))
    for why, p in guesses:
        out.append((why, p))
    seen, uniq = set(), []
    for why, p in out:
        k = str(p)
        if k not in seen:
            seen.add(k)
            uniq.append((why, p))
    return uniq


def find_c4() -> dict:
    tried, named_missing = [], []
    for why, p in c4_candidates():
        tried.append(str(p))
        if is_c4(p):
            return {"dir": p, "from": why, "tried": tried, "named_missing": named_missing}
        if why in ("C4_ROOT", "preference c4.root"):
            named_missing.append(f"{why} names {p}, which does not hold mcp/c4-mcp.js and lib/c4-model.js")
    return {"dir": None, "from": "", "tried": tried, "named_missing": named_missing}


def _probe_node(exe: str) -> str:
    """'' when *exe* runs and prints a Node version, else why not."""
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"did not run ({e.__class__.__name__})"
    if r.returncode != 0 or not r.stdout.strip().startswith("v"):
        return f"exited {r.returncode} without a version"
    return ""


def node_candidates() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    env = (os.environ.get("VIBROBEAST_NODE") or "").strip()
    if env and "${" not in env:
        out.append(("VIBROBEAST_NODE", env))
    names = ("node.exe", "node") if os.name == "nt" else ("node",)
    for d in (os.environ.get("PATH") or "").split(os.pathsep):
        if not d or "windowsapps" in d.replace("/", "\\").lower():
            continue                            # the Store's alias folder: never a real node
        for n in names:
            p = os.path.join(d, n)
            if os.path.isfile(p):
                out.append(("node on PATH", p))
    pf = os.environ.get("ProgramFiles") or "C:\\Program Files"
    out.append(("Program Files", os.path.join(pf, "nodejs", "node.exe")))
    for tree in ("ucrt64", "mingw64", "clang64"):
        out.append((f"MSYS2 {tree}", f"C:\\msys64\\{tree}\\bin\\node.exe"))
        out.append((f"MSYS2 {tree}", f"/{tree}/bin/node"))
    seen, uniq = set(), []
    for why, p in out:
        if p not in seen:
            seen.add(p)
            uniq.append((why, p))
    return uniq


def find_node() -> dict:
    tried = []
    for why, p in node_candidates():
        if why != "VIBROBEAST_NODE" and not os.path.isfile(p):
            continue
        bad = _probe_node(p)
        tried.append(f"{p}: {bad or 'ok'}")
        if not bad:
            return {"exe": p, "from": why, "tried": tried}
    return {"exe": None, "from": "", "tried": tried}


def js_tokens(src: str) -> list[tuple[str, str, int]]:
    """(kind, text, line) for JavaScript source: kind is id, str, num, punct or re.  Comments are
    dropped; a string's text is its contents; a template's literal parts are strings and its
    ``${...}`` parts are lexed as code (so nothing hides in a template).  Good enough for a
    tripwire; a lexing surprise shows up as a hit, never as silence about code."""
    out: list[tuple[str, str, int]] = []
    i, n, line = 0, len(src), 1
    tmpl: list[int] = []                       # brace depth inside each open ${ ... }

    def prev_allows_regex() -> bool:
        if not out:
            return True
        k, t, _ = out[-1]
        if k == "id":
            return t in _KW_BEFORE_REGEX
        return k == "punct" and t not in (")", "]", "}")

    def read_template(i: int, line: int):
        buf = []
        while i < n:
            c = src[i]
            if c == "\\":
                if src[i + 1:i + 2] == "\n":
                    line += 1
                buf.append(src[i:i + 2]); i += 2; continue
            if c == "`":
                out.append(("str", js_unescape("".join(buf)), line)); return i + 1, line, False
            if c == "$" and src[i + 1:i + 2] == "{":
                out.append(("str", js_unescape("".join(buf)), line)); tmpl.append(0); return i + 2, line, True
            if c == "\n":
                line += 1
            buf.append(c); i += 1
        out.append(("str", js_unescape("".join(buf)), line))
        return i, line, False

    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c.isspace():
            i += 1; continue
        if src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            line += src.count("\n", i, j); i = j; continue
        if c in "'\"":
            j, buf = i + 1, []
            while j < n and src[j] != c and src[j] != "\n":
                if src[j] == "\\":
                    if src[j + 1:j + 2] == "\n":
                        line += 1
                    buf.append(src[j:j + 2]); j += 2; continue
                buf.append(src[j]); j += 1
            out.append(("str", js_unescape("".join(buf)), line)); i = j + 1; continue
        if c == "`":
            i, line, _ = read_template(i + 1, line); continue
        if c == "}" and tmpl:
            if tmpl[-1] == 0:
                tmpl.pop(); i, line, _ = read_template(i + 1, line); continue
            tmpl[-1] -= 1
        if c == "{" and tmpl:
            tmpl[-1] += 1
        if c.isalpha() or c in "_$\\" or ord(c) > 127:
            j = i
            while j < n:
                if src[j] == "\\":
                    m = _ID_ESC.match(src, j)
                    j = m.end() if m else j + 1    # an unreadable escape stays in, and is a hit
                    continue
                if src[j].isalnum() or src[j] in "_$" or ord(src[j]) > 127:
                    j += 1; continue
                break
            raw = src[i:j]
            name = js_unescape(raw, ident=True) if "\\" in raw else raw
            out.append(("bad" if "\\" in name else "id", name if "\\" not in name else raw, line))
            i = j; continue
        if c.isdigit():
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "._"):
                j += 1
            out.append(("num", src[i:j], line)); i = j; continue
        if c == "/" and prev_allows_regex():
            j, cls = i + 1, False
            while j < n and src[j] != "\n":
                if src[j] == "\\":
                    j += 2; continue
                if src[j] == "[":
                    cls = True
                elif src[j] == "]":
                    cls = False
                elif src[j] == "/" and not cls:
                    break
                j += 1
            j += 1
            while j < n and src[j].isalpha():
                j += 1
            out.append(("re", src[i:j], line)); i = j; continue
        for p in _PUNCT3 + _PUNCT2:
            if src.startswith(p, i):
                out.append(("punct", p, line)); i += len(p); break
        else:
            out.append(("punct", c, line)); i += 1
    return out


def _require_at(toks, k: int):
    """At toks[k] == require: ('module', name) or ('lib', name) for a shape the guard can read,
    else None.  Readable shapes: require('<allowed module>') and
    require(path.join(__dirname, '..', 'lib', '<name>.js'))."""
    t = [x[0] + ":" + x[1] for x in toks[k:k + 16]]
    if t[1:2] == ["punct:("] and len(t) > 3 and t[2].startswith("str:") and t[3] == "punct:)":
        return ("module", t[2][4:])
    want = ["punct:(", "id:path", "punct:.", "id:join", "punct:(", "id:__dirname", "punct:,",
            "str:..", "punct:,", "str:lib", "punct:,"]
    if t[1:12] == want and len(t) > 14 and t[12].startswith("str:") and t[13:15] == ["punct:)", "punct:)"]:
        return ("lib", t[12][4:])
    return None


def scan_js(src: str, allow_libs: bool):
    """(hits, lib names) for one file.  allow_libs: whether the lib require shape is allowed here
    (c4-mcp.js yes; a lib file no -- the libs require nothing but allowed modules)."""
    toks = js_tokens(src)
    hits, libs = [], []
    for k, (kind, text, line) in enumerate(toks):
        prev = toks[k - 1] if k else ("", "", 0)
        nxt = toks[k + 1] if k + 1 < len(toks) else ("", "", 0)
        if kind == "str":
            if text.strip() in DENY_STRINGS:
                hits.append(f"line {line}: the string '{text.strip()}' (a way to reach a module by name)")
            continue
        if kind == "bad":
            hits.append(f"line {line}: an escaped name this check cannot read ({text})")
            continue
        if kind != "id":
            continue
        if text == "require":
            got = _require_at(toks, k) if prev[1] != "." else None
            if got and got[0] == "module" and got[1] in ALLOW_MODULES:
                continue
            if got and got[0] == "lib" and allow_libs and _LIBNAME.match(got[1]):
                libs.append(got[1]); continue
            if got and got[0] == "module":
                hits.append(f"line {line}: require of {got[1]}")
            else:
                hits.append(f"line {line}: require used in a way this check cannot read")
        elif text == "process" and prev[1] != ".":
            nn = toks[k + 2] if k + 2 < len(toks) else ("", "", 0)
            if not (nxt[1] == "." and nn[0] == "id" and nn[1] in PROCESS_OK):
                what = "process." + nn[1] if nxt[1] == "." else "process used directly"
                hits.append(f"line {line}: {what}")
        elif text == "module" and prev[1] != ".":
            nn = toks[k + 2] if k + 2 < len(toks) else ("", "", 0)
            if not (prev[1] == "typeof" or (nxt[1] == "." and nn[1] == "exports")):
                hits.append(f"line {line}: module used for more than module.exports")
        elif text in DENY_NAMES:
            hits.append(f"line {line}: {text}")
    return hits, libs


def guard(c4: Path) -> list[str]:
    """What, in the files c4-mcp.js would load, ends the call to serve it.  [] = nothing."""
    js = c4 / "mcp" / "c4-mcp.js"
    try:
        text = js.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [f"could not read {js}: {e}"]
    found, libs = scan_js(text, allow_libs=True)
    hits = [f"mcp/c4-mcp.js {h}" for h in found]
    for name in dict.fromkeys(libs):
        f = c4 / "lib" / name
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            hits.append(f"could not read {f}: {e}")
            continue
        hits += [f"lib/{name} {h}" for h in scan_js(t, allow_libs=False)[0]]
    return hits



def status() -> dict:
    if not is_on():
        return {"state": "OFF", "means": MEANS, "turn_on": HOW_ON,
                "talks_to": "nothing; while it is off this is the only tool"}
    c = find_c4()
    n = find_node()
    if c["dir"] is None:
        return {"state": "NO C4 TREE FOUND",
                "say": "C4's MCP server lives in your own C4 folder, and none was found. " + HOW_ROOT,
                "looked_in": c["tried"], "notes": c["named_missing"], "talks_to": "nothing"}
    if n["exe"] is None:
        return {"state": "C4 FOUND, BUT NO NODE",
                "c4": str(c["dir"]), "found_by": c["from"],
                "say": "C4's MCP server is a Node program, and no working Node was found. " + HOW_NODE,
                "tried": n["tried"], "talks_to": "nothing"}
    hits = guard(c["dir"])
    if hits:
        return {"state": "C4 FOUND, NOT STARTED: IT ASKS FOR MORE THAN IT USED TO",
                "c4": str(c["dir"]), "node": n["exe"],
                "say": "This plugin serves C4's MCP server only while it reads no files, writes none "
                       "and opens no connection. These files now ask for something that could, or "
                       "in a way this check cannot read: " + "; ".join(hits) + ". So it was not "
                       "started. The call to serve it has to be made again (in "
                       "polygram/mcp/c4face.py, ALLOW_MODULES and scan_js).",
                "talks_to": "nothing"}
    return {"state": "ON", "c4": str(c["dir"]), "found_by": c["from"], "node": n["exe"],
            "node_found_by": n["from"]}


def build():
    """The server whenever C4's own server is not started: one tool, which says why."""
    from .rpc import Server
    srv = Server(name="c4face", version=VERSION, require_mode=False)

    @srv.tool("c4_status",
              "Whether C4's own MCP server (the C4 work surface: fragments, diagrams, doors) is "
              "being served from your C4 folder, and if not, why: off until you ask Claude to turn "
              "C4 on, or something missing, and how to fix it by asking Claude. When it is on and "
              "C4 and Node are both found, C4's own tools appear instead.")
    def _status(_args):
        return status()
    return srv


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    st = status()
    if st["state"] != "ON":
        build().serve()
        return 0
    js = str(Path(st["c4"]) / "mcp" / "c4-mcp.js")
    cmd = [st["node"], js] + argv
    # node gets a floor of the environment plus C4's own names, never the plugin's keys, token or password
    # (the 2026-10-19 audit, HOLD item 12 and S3: c4face execs node with the full environment).
    from .keys import child_env
    env = child_env({k: v for k, v in os.environ.items() if k.startswith(("C4_", "C4OK_", "NODE_"))})
    sys.stdout.flush()
    sys.stderr.write(f"c4face: serving {js} with {st['node']}\n")
    sys.stderr.flush()
    if os.name == "nt":
        # os.exec* on Windows starts a new process and ENDS this one, and the app would see its
        # server exit.  So wait on the child instead; stdin, stdout and stderr are inherited.
        return subprocess.call(cmd, env=env)
    try:
        os.execve(st["node"], cmd, env)               # this process becomes node; nothing in between
    except OSError as e:                        # pragma: no cover -- probe said it runs
        sys.stderr.write(f"c4face: could not start node ({e}); serving c4_status instead\n")
        build().serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
