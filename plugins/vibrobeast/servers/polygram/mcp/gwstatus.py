# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""gwstatus -- the ghostwheel status icon, live: ask a list of hosts how they are, and draw it.

OFF until switched on (GW_ON, the extension's "Ghostwheel status door"): while off, one tool says
so and nothing is sent anywhere.  On, it asks each enabled host for a little health -- reachable,
load, disk -- and draws the answer with gwicon (a letter made of small letters, one per host).

WHERE THE SETTINGS COME FROM (2026-10-12, Corwin's items 3.1-3.4).
  Defaults, from the settings page (environment):  GW_HOSTS (a simple list), GW_DOMAIN, GW_METHOD,
    GW_PORT, GW_AUTH (none | ssh | basic), GW_AUTH_METHOD (SYSTEM | MUNIN), GW_USER, GW_PASSWORD,
    VIBROBEAST_SSH_KEY, GW_LOOKUPS + GW_LOOKUPS_ALWAYS, GW_KNOWN_HOSTS + GW_KNOWN_HOSTS_ALWAYS,
    GW_REFRESH, GW_LETTER, GW_HTTP_PATH, GW_HOSTS_FILE, GW_SCANNER (the ssh-keyscan to ask for host
    keys; unset: the first one on PATH).
  Per host, from the hosts register (GW_HOSTS_FILE, else ~/.mentcached/gw-hosts.tsv), one row each:
    ENABLED  NAME  FINGERPRINT  USER  KEY  AUTH          ("-" for a cell left to its default)
  The settings page cannot hold a table, so the rows live in the register and gw_host_set edits it;
  a name in GW_HOSTS with no row is an enabled host with every cell at its default.

DEFAULTS, said once.  An unqualified name gets GW_DOMAIN.  USER blank: GW_USER, else the host's
short name (gw7 logs in as gw7).  KEY blank: VIBROBEAST_SSH_KEY.  AUTH blank: GW_AUTH, else ssh when
a default key is set, else none.  A new row takes the default AUTH written in (the prefill).
FINGERPRINT blank: filled from the first host key accepted.  METHOD and PORT: GW_METHOD/GW_PORT
for a host using the default AUTH; otherwise, and when unset, from the AUTH (ssh -> ssh:22,
basic -> https:443, none -> munin:4949 under MUNIN, https:443 under SYSTEM).

AUTH METHOD, as read (his word: "authorization method with options SYSTEM and MUNIN").  The reading
taken here, labelled as a reading: which agent on the host answers.  SYSTEM: the host's own system
(over ssh: /proc/loadavg, nproc, df; over http(s): whether GW_HTTP_PATH answers).  MUNIN: the
munin-node (directly on 4949; over ssh, the node on the host's own 127.0.0.1:4949; over http(s):
whether /munin/ answers).  Falsifier: he names it as something else, and only this paragraph and
_plan() move.

PERMISSIONS (consent, not a dialog: a server cannot pop one).  Before a name is looked up, and
before a host key is trusted, the switch decides: off = never; on + "always" = go ahead; on alone =
ASK.  An ASK comes back from gw_probe in words, with the fingerprint where there is one; the person
answers, and gw_allow records it (once, or always for that host).  Host keys go to this server's
own known-hosts file (~/.mentcached/gw_known_hosts), never ~/.ssh/known_hosts.  A pinned
FINGERPRINT that does not match is refused whatever the switches say.

SECRETS.  GW_PASSWORD and VIBROBEAST_API_TOKEN are never written, logged or returned: tools say
"set" or "not set".  A per-host basic password has no home yet (the register is plain text); the
default password is used for every basic host.  The API token is carried and reported; nothing
here sends it.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

VERSION = "0.1.0"
STATE = Path.home() / ".mentcached"
KNOWN = STATE / "gw_known_hosts"
APPROVALS = STATE / "gw-approvals.tsv"
LAST = STATE / "gw-last.json"
OUT_SVG = STATE / "gw-status.svg"
OUT_HTML = STATE / "gw-status.html"
COLS = ("ENABLED", "NAME", "FINGERPRINT", "USER", "KEY", "AUTH")
AUTHS = ("none", "ssh", "basic")
METHODS = {"ssh": 22, "http": 80, "https": 443, "munin": 4949}
AUTH_METHODS = ("SYSTEM", "MUNIN")
TIMEOUT = 9                     # seconds; a house number
ASSUMED_CPUS = 4                # load is scored against this when the host does not say (house number)
_LABEL = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")
_LOCK = threading.RLock()


# ------------------------------------------------------------------ settings
def _env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    return "" if "${" in v else v


def _switch(name: str, default: bool) -> bool:
    from .rpc import env_switch
    s = env_switch(name)
    return default if s is None else s


def is_on() -> bool:
    from .rpc import env_switch
    s = env_switch("GW_ON")
    if s is not None:
        return s
    try:
        from . import prefs
        return prefs.on("gw.on")
    except Exception:                                   # noqa: BLE001
        return False


def hosts_file() -> Path:
    p = _env("GW_HOSTS_FILE")
    return Path(p).expanduser() if p else STATE / "gw-hosts.tsv"


def defaults() -> dict:
    key = _env("VIBROBEAST_SSH_KEY")
    auth = _env("GW_AUTH").lower() or ("ssh" if key else "none")
    am = (_env("GW_AUTH_METHOD") or "SYSTEM").upper()
    port = _env("GW_PORT")
    refresh = _env("GW_REFRESH")
    d = {
        "hosts": [h for h in re.split(r"[\s,;]+", _env("GW_HOSTS")) if h],
        "domain": _env("GW_DOMAIN").strip("."),
        "method": _env("GW_METHOD").lower(),
        "port": int(float(port)) if re.fullmatch(r"\d+(\.0+)?", port) else None,
        "auth": auth, "auth_method": am,
        "user": _env("GW_USER"), "key": key,
        "password_set": bool(_env("GW_PASSWORD")),
        "api_token_set": bool(_env("VIBROBEAST_API_TOKEN")),
        "lookups": _switch("GW_LOOKUPS", True), "lookups_always": _switch("GW_LOOKUPS_ALWAYS", False),
        "known_hosts": _switch("GW_KNOWN_HOSTS", True),
        "known_hosts_always": _switch("GW_KNOWN_HOSTS_ALWAYS", False),
        "refresh": int(float(refresh)) if re.fullmatch(r"\d+(\.\d+)?", refresh) else 300,
        "letter": (_env("GW_LETTER") or "G")[:1],
        "http_path": _env("GW_HTTP_PATH"),
    }
    problems = []
    if d["auth"] not in AUTHS:
        problems.append(f"GW_AUTH {d['auth']!r} is not none, ssh or basic; none is used")
        d["auth"] = "none"
    if d["auth_method"] not in AUTH_METHODS:
        problems.append(f"GW_AUTH_METHOD {d['auth_method']!r} is not SYSTEM or MUNIN; SYSTEM is used")
        d["auth_method"] = "SYSTEM"
    if d["method"] and d["method"] not in METHODS:
        problems.append(f"GW_METHOD {d['method']!r} is not one of {', '.join(METHODS)}; it is ignored")
        d["method"] = ""
    d["problems"] = problems
    return d


def valid_name(name: str) -> bool:
    if _is_ip(name):
        return True
    n = name[:-1] if name.endswith(".") else name
    return 0 < len(n) <= 253 and all(_LABEL.match(x) for x in n.split("."))


def _is_ip(name: str) -> bool:
    try:
        ipaddress.ip_address(name.strip("[]"))
        return True
    except ValueError:
        return False


# ------------------------------------------------------------------ the register
def read_rows(path: Path | None = None) -> list[dict]:
    path = path or hosts_file()
    rows = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = (line.split("\t") + ["-"] * len(COLS))[:len(COLS)]
        r = {c.lower(): ("" if v.strip() == "-" else v.strip()) for c, v in zip(COLS, cells)}
        r["enabled"] = r["enabled"].lower() not in ("0", "off", "no", "false", "disabled")
        rows.append(r)
    return rows


def write_rows(rows: list[dict], path: Path | None = None) -> None:
    path = path or hosts_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["# gw-hosts: one host per row, tab-separated; '-' leaves a cell to its default.",
           "# " + "\t".join(COLS)]
    for r in rows:
        out.append("\t".join(["on" if r["enabled"] else "off"] +
                             [r.get(c.lower()) or "-" for c in COLS[1:]]))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def hosts(d: dict | None = None) -> list[dict]:
    """Every host: register rows first, in order, then names in GW_HOSTS with no row."""
    d = d or defaults()
    rows = read_rows()
    seen = {r["name"].lower() for r in rows}
    for n in d["hosts"]:
        if n.lower() not in seen:
            rows.append({"enabled": True, "name": n, "fingerprint": "", "user": "", "key": "",
                         "auth": "", "from_list": True})
            seen.add(n.lower())
    return [resolve(r, d) for r in rows]


def resolve(r: dict, d: dict) -> dict:
    name = r["name"]
    qualified = "." in name or _is_ip(name) or not d["domain"]
    fqdn = name.rstrip(".") if qualified else f"{name}.{d['domain']}"
    short = name.split(".")[0] if not _is_ip(name) else name
    auth = (r.get("auth") or d["auth"]).lower()
    how = {"name": "row" if not r.get("from_list") else "GW_HOSTS"}
    how["fqdn"] = "as given" if qualified else "GW_DOMAIN"
    how["user"] = "row" if r.get("user") else ("GW_USER" if d["user"] else "short name")
    how["key"] = "row" if r.get("key") else ("VIBROBEAST_SSH_KEY" if d["key"] else "none")
    how["auth"] = "row" if r.get("auth") else "default"
    method, port = _plan(auth, d, uses_default_auth=(auth == d["auth"]))
    return {"enabled": r["enabled"], "name": name, "fqdn": fqdn, "short": short,
            "fingerprint": r.get("fingerprint", ""), "user": r.get("user") or d["user"] or short,
            "key": r.get("key") or d["key"], "auth": auth, "method": method, "port": port,
            "auth_method": d["auth_method"], "valid": valid_name(name) and auth in AUTHS, "how": how}


def page_meaning(d: dict | None = None) -> dict:
    """The page's words for every Ghostwheel field (pagewords), and what each comes to on each host.

    2026-10-26 05:32, Corwin and Bryant: an empty field must reach the agent with the meaning the page
    gives it.  "applies_here" is computed by resolve(), the same code that logs in, so the sentence and
    the behaviour can be compared (tests: t/pagewords-check.sh and its second reader)."""
    from . import pagewords
    d = d or defaults()
    out = pagewords.explain(fields=None)
    hs = [h for h in hosts(d) if h["enabled"]]
    def each(f):
        return "; ".join(f(h) for h in hs) or "no hosts listed yet"
    here = {
        "gw_domain": lambda: each(lambda h: f"{h['name']} is {h['fqdn']}"),
        "gw_auth": lambda: f"{d['auth']} (" + ("an SSH key is set" if d["key"] else "no SSH key is set") + ")",
        "gw_user": lambda: each(lambda h: f"{h['short']} logs in as {h['user']}"),
        "gw_method": lambda: each(lambda h: f"{h['name']}: {h['method']}"),
        "gw_port": lambda: each(lambda h: f"{h['name']}: {h['port']}"),
        "gw_auth_method": lambda: d["auth_method"],
        "gw_refresh": lambda: f"{d['refresh']} seconds",
        "gw_hosts_file": lambda: str(hosts_file()),
    }
    rows = [r for r in out["fields"] if r["field"].startswith("gw_")]
    for r in rows:
        if r["field"] in here:
            try:
                r["applies_here"] = here[r["field"]]()
            except Exception as e:                          # noqa: BLE001
                r["applies_here"] = f"could not work it out ({e.__class__.__name__})"
    out["fields"] = rows
    return out


def _plan(auth: str, d: dict, uses_default_auth: bool) -> tuple[str, int]:
    if uses_default_auth and d["method"]:
        method = d["method"]
    elif auth == "ssh":
        method = "ssh"
    elif auth == "basic":
        method = "https"
    else:
        method = "munin" if d["auth_method"] == "MUNIN" else "https"
    port = d["port"] if (uses_default_auth and d["port"] and (d["method"] or method) == method) else METHODS[method]
    return method, port


# ------------------------------------------------------------------ consent
def _approvals() -> list[list[str]]:
    if not APPROVALS.is_file():
        return []
    return [l.split("\t") for l in APPROVALS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def _approve(kind: str, host: str, how: str, extra: str = "") -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    new = not APPROVALS.is_file()
    with APPROVALS.open("a", encoding="utf-8", newline="\n") as f:
        if new:
            f.write("# gw approvals: KIND HOST HOW WHEN EXTRA (once is used up by the next probe)\n")
        f.write("\t".join([kind, host.lower(), how, _now(), extra]) + "\n")


def _consume(kind: str, host: str) -> None:
    rows = _approvals()
    keep, used = [], False
    for r in rows:
        if not used and r[0] == kind and r[1] == host.lower() and r[2] == "once":
            used = True
            continue
        keep.append(r)
    if used:
        APPROVALS.write_text("# gw approvals: KIND HOST HOW WHEN EXTRA (once is used up by the next probe)\n"
                             + "".join("\t".join(r) + "\n" for r in keep), encoding="utf-8", newline="\n")


def _allowed(kind: str, host: str, extra: str | None = None) -> str | None:
    """'always' / 'once' when a recorded answer covers this, else None."""
    for r in _approvals():
        if r[0] == kind and r[1] == host.lower() and (extra is None or (r + [""])[4] == extra):
            return r[2]
    return None


def gate(kind: str, host: str, d: dict, extra: str | None = None) -> str:
    """GO, OFF or ASK for a lookup or a host key."""
    on, always = ((d["lookups"], d["lookups_always"]) if kind == "lookup"
                  else (d["known_hosts"], d["known_hosts_always"]))
    if not on:
        return "OFF"
    if always:
        return "GO"
    a = _allowed(kind, host, extra)
    if a == "once":
        _consume(kind, host)
    return "GO" if a else "ASK"


# ------------------------------------------------------------------ host keys
def fingerprint(b64key: str) -> str:
    raw = base64.b64decode(b64key)
    return "SHA256:" + base64.b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")


def _hostfield(fqdn: str, port: int) -> str:
    return fqdn if port == 22 else f"[{fqdn}]:{port}"


def known(fqdn: str, port: int) -> bool:
    if not KNOWN.is_file():
        return False
    hf = _hostfield(fqdn, port).lower()
    return any(l.split(" ", 1)[0].lower() == hf for l in KNOWN.read_text(encoding="utf-8").splitlines())


def known_fingerprints(fqdn: str, port: int) -> list[str]:
    """The fingerprints of every key gw_known_hosts holds for this host and port (the 2026-10-19 audit, HOLD
    item 5: the pin was compared only on the first contact, and a host already known ran with whatever its
    known_hosts line said; now the pin is compared against that line on every probe)."""
    if not KNOWN.is_file():
        return []
    hf = _hostfield(fqdn, port).lower()
    out = []
    for l in KNOWN.read_text(encoding="utf-8").splitlines():
        parts = l.split()
        if len(parts) >= 3 and parts[0].lower() == hf:
            try:
                out.append(fingerprint(parts[2]))
            except Exception:   # noqa: BLE001 -- a line that is not a key is not a fingerprint
                pass
    return out


#: Why the last keyscan offered no key, in the scanner's own words; probe says it with the DOWN.
SCAN_WHY = {"why": ""}


def keyscan(fqdn: str, port: int) -> list[tuple[str, str, str]]:
    # GW_SCANNER names the binary to use; unset, the first ssh-keyscan on PATH.  2026-10-15: on Windows
    # that is System32's, which against gw7 fails every try with "choose_kex: unsupported KEX method
    # sntrup761x25519-sha512@openssh.com" (Corwin, from cmd) -- it offers that method first and cannot
    # finish it -- while Git's ssh-keyscan returns all three keys; so every host read DOWN.  Also the
    # children get SystemRoot back (_child_env), and SCAN_WHY carries the scanner's own words, so a
    # DOWN now says which of these it was instead of "unreachable?".
    SCAN_WHY["why"] = ""
    exe = _env("GW_SCANNER") or shutil.which("ssh-keyscan")
    if not exe:
        raise RuntimeError("ssh-keyscan not found on PATH, and GW_SCANNER is not set")
    r = subprocess.run([exe, "-T", str(TIMEOUT), "-p", str(port), "-t", "ed25519,ecdsa,rsa", fqdn],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT * 3,
                       env=_child_env(), **_quiet())
    out = []
    for l in (r.stdout or "").splitlines():
        p = l.split()
        if len(p) >= 3 and not l.startswith("#"):
            out.append((p[1], p[2], fingerprint(p[2])))
    if not out:
        said = next((l.strip() for l in (r.stderr or "").splitlines() if l.strip() and not l.startswith("#")), "")
        name = Path(exe).name
        SCAN_WHY["why"] = f"{name} said: {said[:160]}" if said else f"{name} exited {r.returncode} and printed no key"
    order = {"ssh-ed25519": 0}
    return sorted(out, key=lambda k: order.get(k[0], 1))


def _add_known(fqdn: str, port: int, ktype: str, b64: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with KNOWN.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"{_hostfield(fqdn, port)} {ktype} {b64}\n")


def _quiet() -> dict:
    return {"creationflags": 0x08000000} if os.name == "nt" else {}      # CREATE_NO_WINDOW


def _child_env(base: dict | None = None, nt: bool | None = None) -> dict:
    """The environment for a program we start.  On Windows a process started without SystemRoot cannot
    open a socket, and the extension's host chooses our environment (keys.py found it 2026-10-14), so
    put back the one variable networking needs and change nothing else."""
    env = dict(os.environ if base is None else base)
    if (os.name == "nt" if nt is None else nt) and not (env.get("SystemRoot") or env.get("SYSTEMROOT")):
        env["SystemRoot"] = r"C:\Windows"
    return env


# ------------------------------------------------------------------ probes
def _scores(load: float | None, cpus: int | None, disk_used: float | None) -> list:
    pairs = [["up", 100]]
    if load is not None:
        ratio = load / (cpus or ASSUMED_CPUS)
        pairs.append(["load", max(0, min(100, round(100 - 50 * ratio)))])
    if disk_used is not None:
        pairs.append(["disk", max(0, min(100, round(100 - disk_used)))])
    return pairs


def parse_munin(text: str) -> tuple[float | None, float | None]:
    """A munin-node conversation's answers to 'fetch load' then 'fetch df': two blocks, each ended by
    a line holding one '.'; '#' lines (the banner, comments) are skipped.  Load is load.value; disk
    is the fullest of df's values (percent used)."""
    blocks, cur = [], []
    for l in text.splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if l == ".":
            blocks.append(cur)
            cur = []
            continue
        cur.append(l)
    if cur:
        blocks.append(cur)

    def values(block):
        out = {}
        for l in block:
            m = re.match(r"^([A-Za-z0-9_]+)\.value\s+(\S+)$", l)
            if m:
                try:
                    out[m.group(1)] = float(m.group(2))
                except ValueError:
                    pass
        return out
    load = values(blocks[0]).get("load") if blocks else None
    df = values(blocks[1]) if len(blocks) > 1 else {}
    return load, (max(df.values()) if df else None)


def munin_tcp(fqdn: str, port: int) -> str:
    """Talk to a munin-node directly; return the conversation in the shape parse_munin reads."""
    with socket.create_connection((fqdn, port), timeout=TIMEOUT) as s:
        f = s.makefile("rwb")
        out = [f.readline().decode("utf-8", "replace").rstrip("\r\n")]   # "# munin node at ..."
        for cmd in ("fetch load", "fetch df"):
            f.write((cmd + "\n").encode())
            f.flush()
            while True:
                raw = f.readline()
                l = raw.decode("utf-8", "replace").rstrip("\r\n")
                out.append(l if raw else ".")
                if l == "." or not raw:
                    break
        f.write(b"quit\n")
        f.flush()
    return "\n".join(out)


SYSTEM_CMD = "cat /proc/loadavg; (nproc 2>/dev/null || getconf _NPROCESSORS_ONLN); df -P / | tail -n 1"
MUNIN_CMD = ("(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN); "
             "printf 'fetch load\\nfetch df\\nquit\\n' | "
             "(nc -w %d 127.0.0.1 4949 2>/dev/null || nc 127.0.0.1 4949)" % TIMEOUT)


def ssh_run(h: dict, cmd: str) -> str:
    exe = shutil.which("ssh")
    if not exe:
        raise RuntimeError("ssh not found on PATH")
    args = [exe, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={KNOWN}", "-o", f"GlobalKnownHostsFile={KNOWN}",
            "-o", f"ConnectTimeout={TIMEOUT}", "-p", str(h["port"]), "-l", h["user"]]
    if h["key"]:
        args += ["-o", "IdentitiesOnly=yes", "-i", h["key"]]
    r = subprocess.run(args + [h["fqdn"], cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=TIMEOUT * 3, env=_child_env(), **_quiet())
    if r.returncode != 0:
        raise RuntimeError(f"ssh exited {r.returncode}: {(r.stderr or '').strip()[:200]}")
    return r.stdout


def http_get(h: dict, d: dict) -> int:
    path = d["http_path"] or ("/munin/" if h["auth_method"] == "MUNIN" else "/")
    url = f"{h['method']}://{h['fqdn']}:{h['port']}{path}"
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "vibrobeast-gwstatus/" + VERSION})
    if h["auth"] == "basic":
        if h["method"] != "https" and h["fqdn"] not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("basic auth over plain http would send the password in clear across the network; use https, "
                             "or a tunnel to 127.0.0.1 (the 2026-10-19 audit, item 11)")
        pw = _env("GW_PASSWORD")
        req.add_header("Authorization", "Basic " + base64.b64encode(f"{h['user']}:{pw}".encode()).decode())
    # No redirect is followed: urllib would re-send the Authorization header to wherever the host pointed
    # (item 11).  A 3xx is answered as its own status, which the caller already reads as not-200.
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):   # noqa: N802 -- urllib's name
            return None
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def probe(h: dict, d: dict) -> dict:
    """One host: {state, pairs, say, ...}.  States: UP, DOWN, ASK, OFF, BLOCKED, DISABLED, INVALID."""
    if not h["enabled"]:
        return {"state": "DISABLED", "pairs": [["disabled", 0]], "say": "switched off in its row"}
    if not h["valid"]:
        return {"state": "INVALID", "pairs": [["invalid", 0]],
                "say": "not a valid host name, or an auth that is not none, ssh or basic"}
    if not _is_ip(h["fqdn"]):
        g = gate("lookup", h["fqdn"], d)
        if g != "GO":
            return {"state": "ASK" if g == "ASK" else "OFF", "pairs": [["ask" if g == "ASK" else "blocked", 50 if g == "ASK" else 0]],
                    "ask": {"kind": "lookup", "host": h["fqdn"]} if g == "ASK" else None,
                    "say": (f"may I look up {h['fqdn']}? answer with gw_allow" if g == "ASK"
                            else "hostname lookups are switched off (GW_LOOKUPS)")}
    try:
        if h["method"] == "ssh":
            if known(h["fqdn"], h["port"]) and h["fingerprint"] and h["fingerprint"] not in known_fingerprints(h["fqdn"], h["port"]):
                return {"state": "BLOCKED", "pairs": [["hostkey", 0]],
                        "say": f"the host key gw_known_hosts holds for {h['fqdn']} does not match the pinned {h['fingerprint']}: refused "
                               "(the pin is compared on every probe, not only the first; remove the stale known_hosts line or fix the pin)"}
            if not known(h["fqdn"], h["port"]):
                SCAN_WHY["why"] = ""
                keys = keyscan(h["fqdn"], h["port"])
                if not keys:
                    return {"state": "DOWN", "pairs": [["down", 0]],
                            "say": f"no host key offered ({SCAN_WHY['why'] or 'unreachable?'})"}
                fps = [k[2] for k in keys]
                if h["fingerprint"]:
                    if h["fingerprint"] not in fps:
                        return {"state": "BLOCKED", "pairs": [["hostkey", 0]],
                                "say": f"host key {fps[0]} does not match the pinned {h['fingerprint']}: refused"}
                    k = keys[fps.index(h["fingerprint"])]
                else:
                    k = keys[0]
                    g = gate("hostkey", h["fqdn"], d, extra=k[2])
                    if g != "GO":
                        return {"state": "ASK" if g == "ASK" else "OFF",
                                "pairs": [["ask" if g == "ASK" else "blocked", 50 if g == "ASK" else 0]],
                                "ask": {"kind": "hostkey", "host": h["fqdn"], "fingerprint": k[2]} if g == "ASK" else None,
                                "say": (f"trust host key {k[2]} ({k[0]}) for {h['fqdn']}? answer with gw_allow"
                                        if g == "ASK" else "adding host keys is switched off (GW_KNOWN_HOSTS)")}
                    _pin(h["name"], k[2])
                _add_known(h["fqdn"], h["port"], k[0], k[1])
            out = ssh_run(h, MUNIN_CMD if h["auth_method"] == "MUNIN" else SYSTEM_CMD)
            lines = out.splitlines()
            if h["auth_method"] == "MUNIN":
                cpus = int(lines[0]) if lines and lines[0].strip().isdigit() else None
                load, disk = parse_munin("\n".join(lines[1:]))
            else:
                load = float(lines[0].split()[0])
                cpus = int(lines[1]) if len(lines) > 1 and lines[1].strip().isdigit() else None
                disk = float(lines[-1].split()[4].rstrip("%")) if lines else None
            return {"state": "UP", "pairs": _scores(load, cpus, disk), "say": "answered over ssh"}
        if h["method"] == "munin":
            load, disk = parse_munin(munin_tcp(h["fqdn"], h["port"]))
            return {"state": "UP", "pairs": _scores(load, None, disk),
                    "say": f"munin-node answered (load scored against {ASSUMED_CPUS} CPUs; it does not say)"}
        code = http_get(h, d)
        if code < 400:
            return {"state": "UP", "pairs": [["up", 100]], "say": f"HTTP {code}"}
        return {"state": "DOWN", "pairs": [["down", 0]], "say": f"HTTP {code}"}
    except Exception as e:                                          # noqa: BLE001
        return {"state": "DOWN", "pairs": [["down", 0]], "say": f"{type(e).__name__}: {e}"[:240]}


def _pin(name: str, fp: str) -> None:
    """Fill a blank FINGERPRINT from the first key accepted (his: 'default blank meaning auto-filled')."""
    with _LOCK:
        rows = read_rows()
        for r in rows:
            if r["name"].lower() == name.lower():
                if not r["fingerprint"]:
                    r["fingerprint"] = fp
                    write_rows(rows)
                return
        rows.append({"enabled": True, "name": name, "fingerprint": fp, "user": "", "key": "", "auth": ""})
        write_rows(rows)


# ------------------------------------------------------------------ the picture
def label(h: dict, i: int) -> str:
    from .gwicon import NAME
    return h["short"] if NAME.match(h["short"]) else f"host{i + 1}"


def draw(results: list[dict], letter: str) -> dict:
    from . import gwicon
    used, items = set(), []
    for i, r in enumerate(results):
        lb = label(r["host"], i)
        while lb in used:
            lb = f"{lb}-{i + 1}"
        used.add(lb)
        items.append((lb, r["pairs"]))
    if not items:
        items = [("none", [["nohosts", 0]])]
    svg, uri = gwicon.render(letter, items)
    return {"svg": svg, "uri": uri}


def page(refresh: int) -> str:
    meta = f'<meta http-equiv="refresh" content="{max(refresh, 30)}">' if refresh else ""
    return ("<!doctype html><html><head><meta charset=\"utf-8\"><title>ghostwheel status</title>" + meta +
            "<style>body{margin:0;background:#111;display:grid;place-items:center;height:100vh}"
            "img{width:200px;image-rendering:pixelated}</style></head><body>"
            "<img src=\"gw-status.svg\" alt=\"ghostwheel status\"></body></html>\n")


def run_all(d: dict | None = None) -> dict:
    with _LOCK:
        d = d or defaults()
        hs = hosts(d)
        results = [dict(probe(h, d), host=h) for h in hs]
        pic = draw(results, d["letter"])
        STATE.mkdir(parents=True, exist_ok=True)
        OUT_SVG.write_text(pic["svg"], encoding="utf-8", newline="")
        OUT_HTML.write_text(page(d["refresh"]), encoding="utf-8", newline="")
        last = {"when": _now(), "hosts": [{"name": r["host"]["name"], "fqdn": r["host"]["fqdn"],
                                           "state": r["state"], "pairs": r["pairs"], "say": r["say"]}
                                          for r in results]}
        LAST.write_text(json.dumps(last, indent=1), encoding="utf-8", newline="")
        return {"results": results, "picture": pic, "when": last["when"]}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _words(r: dict) -> str:
    return f"{r['host']['name']}: {r['state']} -- {r['say']} ({' '.join(f'{c}:{v}' for c, v in r['pairs'])})"


# ------------------------------------------------------------------ server
def build():
    from .rpc import Server, ToolError
    srv = Server(name="gwstatus", version=VERSION, require_mode=False)

    if not is_on():
        @srv.tool("gw_status", "Whether the ghostwheel status door is on, and what turning it on means. "
                  "While it is off this is the only tool, and nothing is sent anywhere.")
        def _off(_a):
            return {"state": "OFF", "turn_on": "switch on 'Ghostwheel status door' in the extension's "
                    "settings (or GW_ON=1), then restart", "when_on": "asks each listed host for "
                    "reachable/load/disk (ssh, munin-node or http, as configured), asking first before "
                    "any name lookup or new host key unless you said always", "sent": "nothing"}
        return srv

    @srv.tool("gw_settings", "The ghostwheel settings as the settings page says them: each field's title "
              "and words, whether it was filled in, and when it was not, the page's own Left empty "
              "sentence and what that comes to on each host (gw33 logs in as gw33). Say an empty field "
              "by that sentence, never as missing. Secrets are said as set or not set, never shown.")
    def _settings(_a):
        d = defaults()
        return {"page": page_meaning(d),
                "defaults": {k: v for k, v in d.items() if k not in ("problems",)},
                "problems": d["problems"], "hosts_file": str(hosts_file()),
                "outputs": {"svg": str(OUT_SVG), "page": str(OUT_HTML), "last": str(LAST)},
                "known_hosts_file": str(KNOWN),
                "scanner": _env("GW_SCANNER") or shutil.which("ssh-keyscan") or "none found on PATH",
                "scanner_from": "GW_SCANNER" if _env("GW_SCANNER") else "PATH"}

    @srv.tool("gw_hosts", "Every host: its row in the hosts register (or the simple list), each value "
              "resolved, and where each came from (row, default, or derived).")
    def _hosts(_a):
        return {"hosts": hosts(), "hosts_file": str(hosts_file())}

    @srv.tool("gw_host_set", "Add a host to the register or change its row: enabled, name, "
              "fingerprint, user, key, auth (none, ssh or basic). A cell given as '-' goes back to "
              "its default. A new row takes the default auth written in.",
              {"type": "object", "required": ["name"], "properties": {
                  "name": {"type": "string"}, "enabled": {"type": "boolean"},
                  "fingerprint": {"type": "string"}, "user": {"type": "string"},
                  "key": {"type": "string"}, "auth": {"type": "string"}}})
    def _host_set(a):
        name = (a.get("name") or "").strip()
        if not valid_name(name):
            raise ToolError(f"{name!r} is not a valid host name (labels of letters, digits and '-')")
        if a.get("auth") not in (None, "-", "") and a["auth"].lower() not in AUTHS:
            raise ToolError("auth must be none, ssh or basic")
        fp = a.get("fingerprint")
        if fp not in (None, "-", "") and not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{43}", fp):
            raise ToolError("fingerprint must look like SHA256:<43 base64 characters> (ssh-keygen -lf)")
        with _LOCK:
            rows = read_rows()
            row = next((r for r in rows if r["name"].lower() == name.lower()), None)
            made = row is None
            if made:
                row = {"enabled": True, "name": name, "fingerprint": "", "user": "", "key": "",
                       "auth": defaults()["auth"]}
                rows.append(row)
            for k in ("fingerprint", "user", "key", "auth"):
                if k in a and a[k] is not None:
                    row[k] = "" if a[k] in ("-", "") else (a[k].lower() if k == "auth" else a[k])
            if "enabled" in a and a["enabled"] is not None:
                row["enabled"] = bool(a["enabled"])
            write_rows(rows)
        return {"made": made, "row": resolve(row, defaults()), "hosts_file": str(hosts_file())}

    @srv.tool("gw_probe", "Ask every enabled host how it is, draw the icon, and write it beside the "
              "seat (gw-status.svg and gw-status.html). Any lookup or host key that needs your yes "
              "comes back as ASK, in words; answer with gw_allow.")
    def _probe(_a):
        r = run_all()
        asks = [x["ask"] for x in r["results"] if x.get("ask")]
        return {"when": r["when"], "say": [_words(x) for x in r["results"]] or ["no hosts configured"],
                "asks": asks, "svg": str(OUT_SVG), "page": str(OUT_HTML)}

    @srv.tool("gw_allow", "Record the person's yes to a lookup or a host key that gw_probe asked "
              "about: once (used by the next probe) or always (for that host).",
              {"type": "object", "required": ["kind", "host"], "properties": {
                  "kind": {"type": "string", "enum": ["lookup", "hostkey"]},
                  "host": {"type": "string"}, "always": {"type": "boolean"},
                  "fingerprint": {"type": "string",
                                  "description": "for hostkey: the fingerprint gw_probe showed"}}})
    def _allow(a):
        kind, host = a.get("kind"), (a.get("host") or "").strip()
        if kind not in ("lookup", "hostkey") or not valid_name(host):
            raise ToolError("kind must be lookup or hostkey, and host a valid name")
        fp = (a.get("fingerprint") or "").strip()
        if kind == "hostkey" and not fp:
            raise ToolError("a host key is allowed by its fingerprint: pass the one gw_probe showed")
        # One row per yes, and only the shape ssh-keygen prints (the 2026-10-19 audit, HOLD item 6: a fingerprint
        # carrying a tab or a newline wrote extra approval rows and turned a lookup gate GO).
        if fp and not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{43}", fp):
            raise ToolError("fingerprint must look like SHA256:<43 base64 characters>, exactly as gw_probe showed it")
        if kind == "lookup" and fp:
            raise ToolError("a lookup yes carries no fingerprint; pass one only for kind=hostkey")
        _approve(kind, host, "always" if a.get("always") else "once", fp)
        return {"recorded": {"kind": kind, "host": host.lower(), "how": "always" if a.get("always") else "once",
                             "fingerprint": fp or None}, "next": "run gw_probe"}

    @srv.tool("gw_icon", "The ghostwheel status icon from the last probe (probing first if there is "
              "none): a data: URI ready for CSS, the SVG file, and the same in words.",
              {"type": "object", "properties": {"probe": {"type": "boolean"}}})
    def _icon(a):
        if a.get("probe") or not LAST.is_file():
            run_all()
        last = json.loads(LAST.read_text(encoding="utf-8"))
        d = defaults()
        results = [{"host": {"name": x["name"], "short": x["name"].split(".")[0]}, "pairs": x["pairs"],
                    "state": x["state"], "say": x["say"]} for x in last["hosts"]]
        pic = draw(results, d["letter"])
        return {"when": last["when"], "uri": pic["uri"], "svg": str(OUT_SVG), "page": str(OUT_HTML),
                "words": [_words(x) for x in results]}

    d = defaults()
    if d["refresh"] > 0:
        def _loop():
            while True:
                time.sleep(d["refresh"])
                try:
                    run_all()
                except Exception as e:                       # noqa: BLE001
                    print(f"gwstatus: refresh failed: {e}", file=sys.stderr)
        threading.Thread(target=_loop, name="gw-refresh", daemon=True).start()
    return srv


def main(argv=None) -> int:
    build().serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
