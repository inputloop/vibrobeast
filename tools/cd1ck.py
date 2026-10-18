#!/usr/bin/env python3
# cd1ck -- CLAUDE DESKTOP 1 CHECK: read a claude_desktop_config.json and say, server by server, which entries
#   are vibrobeast's, which are someone else's, and what moving one more server over would look like.
#   It reads and prints. It never writes the configuration file; the person who keeps it by hand keeps doing so.
#
# usage: python3 cd1ck.py [CONFIG]                       each mcpServers entry, in words
#        python3 cd1ck.py --entry NAME --root DIR [--python CMD] [--env K=V ...]
#                                                         the JSON for one of our servers, to paste by hand
#        python3 cd1ck.py --prove-red
#   CONFIG defaults to the usual place: %APPDATA%\Claude\claude_desktop_config.json on Windows,
#   ~/Library/Application Support/Claude/claude_desktop_config.json on macOS, ~/.config/Claude/... elsewhere.
#   DIR is the folder that holds servers/launch.py: plugins/vibrobeast in a clone of inputloop/vibrobeast.
# Exit 0: read (findings are information); 1: two entries start the same one of our servers, which would put
#   two writers on one memory seat; 2: usage, or a file that is not JSON.
#
# Why (2026-10-18): Bryant adds each MCP server to this file by hand. The way from there to the extension's
# settings page goes one server at a time, and editing JSON by hand stays a valid way to keep it. This says
# where a configuration stands on that way without changing it.
#
# Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  Authored by Mentat (for Corwin, opus-5-5).
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
import json, os, platform, shutil, sys, tempfile
from pathlib import Path

SERVERS = ("mentcached", "persona", "skillx", "llamabridge", "tavernface", "c4face", "gwstatus")
#: The variables each server reads (read from each server's source, 2026-10-18; the extension's settings page sets\n#: the same names, polygram/mcpb.py USER_CONFIG). The _ON switches are read by each server's env_switch.
ENV = {
    "mentcached": ["MENTCACHED_KEEPER", "MENTCACHED_SEAT", "MENTCACHED_PREFS", "VIBROBEAST_KEYS_FILE",
                   "VIBROBEAST_API_TOKEN", "VIBROBEAST_API_TOKEN_FOR", "VIBROBEAST_API_TOKEN_USAGE",
                   "VIBROBEAST_SSH_KEY", "VIBROBEAST_SSH_KEY_FOR", "VIBROBEAST_SSH_KEY_USAGE",
                   "GW_PASSWORD", "GW_PASSWORD_USAGE"],
    "persona": ["MENTCACHED_KEEPER", "MENTCACHED_SEAT", "PERSONA_SHEETS", "PERSONA_ROOT"],
    "skillx": [],
    "llamabridge": ["LLAMABRIDGE_ON", "OLLAMA_HOST"],
    "tavernface": ["TAVERN_ON", "TAVERN_DATA", "TAVERN_AS"],
    "c4face": ["C4_ON", "C4_ROOT", "MENTCACHED_SEAT"],
    "gwstatus": ["GW_ON", "GW_HOSTS", "GW_HOSTS_FILE", "GW_DOMAIN", "GW_USER", "GW_PASSWORD", "GW_AUTH",
                 "GW_AUTH_METHOD", "GW_METHOD", "GW_PORT", "GW_REFRESH", "GW_SCANNER", "GW_LOOKUPS",
                 "GW_LOOKUPS_ALWAYS", "GW_KNOWN_HOSTS", "GW_KNOWN_HOSTS_ALWAYS", "VIBROBEAST_API_TOKEN",
                 "VIBROBEAST_SSH_KEY"],
}
WHAT = {
    "mentcached": "the memory seat (notes, preferences, timings, the key register)",
    "persona": "persona sheets and bylines",
    "skillx": "skill exchange between parties (refuses every call for now, and says why)",
    "llamabridge": "Llama Bridge: hands small jobs to an Ollama model (off until LLAMABRIDGE_ON=1)",
    "tavernface": "Tavern's own MCP mode, for a Tavern node on this computer (off until TAVERN_ON=1)",
    "c4face": "C4's own server, from your C4 folder (off until C4_ON=1)",
    "gwstatus": "the ghostwheel status icon: asks hosts you list how they are (off until GW_ON=1)",
}
#: One seat, one writer: two of these on one seat is the fault the seat is built to refuse.
SINGLE = {"mentcached", "persona"}


def default_config() -> Path:
    s = platform.system()
    if s == "Windows":
        return Path(os.environ.get("APPDATA", "~")).expanduser() / "Claude" / "claude_desktop_config.json"
    if s == "Darwin":
        return Path("~/Library/Application Support/Claude/claude_desktop_config.json").expanduser()
    return Path("~/.config/Claude/claude_desktop_config.json").expanduser()


def ours(entry: dict) -> str | None:
    """Which of our servers an entry starts, read from its command line (launch.py NAME, or -m polygram.mcp NAME)."""
    args = [str(a) for a in entry.get("args", [])]
    for i, a in enumerate(args):
        low = a.replace("\\", "/").lower()
        if low.endswith("/launch.py") or low == "launch.py":
            nxt = args[i + 1] if i + 1 < len(args) else ""
            if nxt in SERVERS:
                return nxt
            if nxt == "hub":
                return "hub"
        if a == "polygram.mcp" and i + 1 < len(args) and args[i + 1] in SERVERS:
            return args[i + 1]
    return None


def read(cfg: dict) -> tuple[list[str], int]:
    lines, fault = [], 0
    servers = cfg.get("mcpServers") or {}
    if not servers:
        return ["no mcpServers in this file: nothing is configured by hand"], 0
    seen: dict[str, list[str]] = {}
    for name, e in servers.items():
        if not isinstance(e, dict):
            lines.append(f"  {name}: not an object; Claude Desktop will skip it")
            continue
        if "url" in e:
            lines.append(f"  {name}: a remote server ({e.get('url')}); not ours, left as it is")
            continue
        o = ours(e)
        if o == "hub":
            lines.append(f"  {name}: vibrobeast's hub, all seven servers behind one entry (what the extension runs)")
            for s in SERVERS:
                seen.setdefault(s, []).append(name)
        elif o:
            env = e.get("env") or {}
            set_ = [k for k in ENV[o] if k in env]
            extra = [k for k in env if k not in ENV[o]]
            note = f"; sets {', '.join(set_)}" if set_ else "; no settings (defaults apply)"
            if extra:
                note += f"; also sets {', '.join(extra)}, which {o} does not read"
            lines.append(f"  {name}: ours, {o}: {WHAT[o]}{note}")
            seen.setdefault(o, []).append(name)
        else:
            cmd = " ".join([str(e.get("command", ""))] + [str(a) for a in e.get("args", [])])[:90]
            lines.append(f"  {name}: someone else's server ({cmd}); left as it is")
    for s, names in seen.items():
        if len(names) > 1:
            fault = 1 if s in SINGLE else fault
            why = "two writers on one memory seat" if s in SINGLE else "two copies of one server"
            lines.append(f"  TWICE: {s} is started by {', '.join(names)}: {why}. Keep one.")
    missing = [s for s in SERVERS if s not in seen]
    if seen and missing:
        lines.append(f"  not yet here (each can be added on its own): {', '.join(missing)}")
    return lines, fault


def extension_beside(config: Path) -> str | None:
    """A folder named like the vibrobeast extension, in the extensions folder beside the configuration file.
    Best effort: Claude Desktop keeps installed extensions in "Claude Extensions" next to this file; if that
    ever moves, this finds nothing and says nothing, rather than guessing."""
    d = config.parent / "Claude Extensions"
    try:
        hits = [p.name for p in d.iterdir() if p.is_dir() and "vibrobeast" in p.name.lower()]
    except OSError:
        return None
    return str(d / hits[0]) if hits else None


def entry(name: str, root: str, python: str, env: list[str]) -> dict:
    sep = "\\" if "\\" in root else "/"
    launch = root.rstrip("/\\") + sep + "servers" + sep + "launch.py"
    e = {"command": python, "args": [launch, name]}
    if env:
        e["env"] = dict(kv.split("=", 1) for kv in env)
    return {f"vibrobeast-{name}": e}


def prove_red() -> int:
    t = Path(tempfile.mkdtemp(prefix="cd1ck."))
    fails = 0
    try:
        def case(label, cfg, want_exit, want_text):
            nonlocal fails
            lines, fault = read(cfg)
            text = "\n".join(lines)
            ok = fault == want_exit and want_text in text
            print(f"  {'ok  ' if ok else 'FAIL'} {label}" + ("" if ok else f" (exit {fault}; {text!r})"))
            fails += 0 if ok else 1
        mine = lambda s, **env: {"command": "python", "args": [r"C:\v\plugins\vibrobeast\servers\launch.py", s], **({"env": env} if env else {})}
        case("an empty file says nothing is configured", {}, 0, "nothing is configured")
        case("someone else's server is left as it is", {"mcpServers": {"tavern": {"command": "python", "args": ["tavern.py", "mcp"]}}}, 0, "someone else's")
        case("one of ours is named, with its settings", {"mcpServers": {"seat": mine("mentcached", MENTCACHED_KEEPER="Bryant")}}, 0, "ours, mentcached")
        case("a variable the server does not read is said", {"mcpServers": {"seat": mine("persona", TAVERN_ON="1")}}, 0, "does not read")
        case("the seat started twice is a fault", {"mcpServers": {"a": mine("mentcached"), "b": mine("mentcached")}}, 1, "two writers")
        case("the hub beside a hand entry is a fault", {"mcpServers": {"hub": {"command": "python", "args": ["x/server/launch.py", "hub"]}, "seat": mine("mentcached")}}, 1, "TWICE: mentcached")
        case("what is not yet here is listed", {"mcpServers": {"p": mine("persona")}}, 0, "not yet here")
        e = entry("persona", "/v/plugins/vibrobeast", "python3", ["MENTCACHED_KEEPER=Bryant"])
        ok = ours(e["vibrobeast-persona"]) == "persona" and e["vibrobeast-persona"]["env"]["MENTCACHED_KEEPER"] == "Bryant"
        print(f"  {'ok  ' if ok else 'FAIL'} the pasteable entry reads back as ours")
        fails += 0 if ok else 1
        cfgp = t / "claude_desktop_config.json"
        cfgp.write_text(json.dumps({"mcpServers": {"seat": mine("mentcached")}}))
        (t / "Claude Extensions" / "local.mcpb.inputloop.vibrobeast").mkdir(parents=True)
        rc = main([str(cfgp)])
        print(f"  {'ok  ' if rc == 1 else 'FAIL'} a hand seat beside the installed extension exits 1")
        fails += 0 if rc == 1 else 1
        bad = t / "bad.json"; bad.write_text("{ not json")
        rc = main([str(bad)])
        print(f"  {'ok  ' if rc == 2 else 'FAIL'} a file that is not JSON exits 2")
        fails += 0 if rc == 2 else 1
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print("cd1ck: PROVE-RED " + ("OK" if not fails else f"FAILED ({fails})"))
    return 0 if not fails else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["--prove-red"]:
        return prove_red()
    if argv[:1] == ["--entry"]:
        a = argv[1:]
        if not a or a[0] not in SERVERS or "--root" not in a:
            print(f"usage: cd1ck.py --entry NAME --root DIR [--python CMD] [--env K=V ...]; NAME is one of {', '.join(SERVERS)}", file=sys.stderr)
            return 2
        name, root = a[0], a[a.index("--root") + 1]
        py = a[a.index("--python") + 1] if "--python" in a else ("python" if platform.system() == "Windows" else "python3")
        env = [a[i + 1] for i, x in enumerate(a) if x == "--env" and i + 1 < len(a)]
        bad = [kv.split("=", 1)[0] for kv in env if kv.split("=", 1)[0] not in ENV[name]]
        print(json.dumps(entry(name, root, py, env), indent=2)[1:-1].strip("\n"))
        print(f"# paste inside \"mcpServers\": {{ ... }}, then restart Claude Desktop. {name}: {WHAT[name]}.", file=sys.stderr)
        if bad:
            print(f"# note: {name} does not read {', '.join(bad)}; it reads {', '.join(ENV[name]) or 'no settings'}.", file=sys.stderr)
        return 0
    path = Path(argv[0]) if argv else default_config()
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"cd1ck: no file at {path}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"cd1ck: {path} is not JSON ({e}); Claude Desktop will not read it either", file=sys.stderr)
        return 2
    lines, fault = read(cfg)
    ext = extension_beside(path)
    if ext:
        hand = [l for l in lines if ": ours, mentcached" in l or ": ours, persona" in l]
        lines.append(f"  the vibrobeast extension looks installed ({ext}): it already runs every one of our servers"
                     + (", so the hand entries for mentcached or persona above put two writers on one seat. Keep one." if hand else "."))
        fault = 1 if hand else fault
    print(f"cd1ck: {path}")
    print("\n".join(lines))
    return fault


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
