#!/bin/sh
# .github/ci/check.sh -- every check the published vibrobeast tree can run on itself, in words.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.
# SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
# Written by Mentat (for Corwin; claude-opus-5-5), 2026-10-12.
#
# usage: sh .github/ci/check.sh [ROOT]          run every check on ROOT (default: this repository)
#        sh .github/ci/check.sh --prove-red     plant a fault for each check in a copy; each must go red
# One line per check: ok, FAIL (with why) or SKIP (with what it needs; never counted as ok).
# Exit 0 when nothing failed; 1 when something did; 2 when the tree could not be read.
set -u
export PYTHONDONTWRITEBYTECODE=1   # a check must not leave bytecode in the tree it checks
PY=${PYTHON:-python3}
here=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
fails=0; skips=0
ok()   { echo "ok    $*"; }
fail() { echo "FAIL  $*"; fails=$((fails+1)); }
skip() { echo "SKIP  $*"; skips=$((skips+1)); }

checks() {
  R=$1
  [ -f "$R/.claude-plugin/marketplace.json" ] || { echo "not a published vibrobeast tree: $R"; return 2; }
  # 1 every shell script parses as POSIX sh
  n=0; bad=""
  for f in $(find "$R/plugins" -name '*.sh' -type f); do n=$((n+1)); sh -n "$f" 2>/dev/null || bad="$bad ${f#$R/}"; done
  [ -z "$bad" ] && ok "C1 $n shell scripts parse" || fail "C1 shell scripts that do not parse:$bad"
  # 2 every Python file compiles
  out=$("$PY" - "$R" <<'P'
import pathlib, sys
bad = []
for p in pathlib.Path(sys.argv[1], "plugins").rglob("*.py"):
    try:
        compile(p.read_bytes(), str(p), "exec")
    except SyntaxError as e:
        bad.append(f"{p}:{e.lineno}")
print(" ".join(bad))
P
)
  [ -z "$out" ] && ok "C2 Python files compile" || fail "C2 does not compile: $out"
  # 3 every JSON file is JSON
  out=$("$PY" - "$R" <<'P'
import json, pathlib, sys
bad = []
for p in pathlib.Path(sys.argv[1]).rglob("*.json"):
    if ".git" in p.parts: continue
    try: json.loads(p.read_text(encoding="utf-8"))
    except Exception as e: bad.append(f"{p}: {e}")
print("; ".join(bad))
P
)
  [ -z "$out" ] && ok "C3 JSON files parse" || fail "C3 $out"
  # 4 every skill names itself and says when to use it
  bad=""; n=0
  for f in "$R"/plugins/*/skills/*/SKILL.md; do
    n=$((n+1))
    awk 'NR==1 && $0!="---" {exit 1} NR>1 && $0=="---" {exit (n && d) ? 0 : 1} /^name:[ \t]*[^ \t]/ {n=1} /^description:/ {d=1}' "$f" || bad="$bad ${f#$R/}"
  done
  [ -z "$bad" ] && ok "C4 $n skills have a name and a description" || fail "C4 skills missing name or description:$bad"
  # 5 the marketplace lists plugins that are here, under their own names and one version
  out=$("$PY" - "$R" <<'P'
import json, pathlib, sys
r = pathlib.Path(sys.argv[1]); m = json.loads((r / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
bad = []
for e in m.get("plugins", []):
    pj = r / e["source"] / ".claude-plugin/plugin.json"
    if not pj.is_file(): bad.append(f"{e['name']}: no {pj}"); continue
    p = json.loads(pj.read_text(encoding="utf-8"))
    if p.get("name") != e["name"]: bad.append(f"{e['name']}: plugin.json says {p.get('name')}")
    if e.get("version") and p.get("version") != e["version"]: bad.append(f"{e['name']}: version {p.get('version')} != {e['version']}")
print("; ".join(bad))
P
)
  [ -z "$out" ] && ok "C5 marketplace entries match their plugins" || fail "C5 $out"
  # 6 PROVENANCE's hashes are the files' hashes
  bad=""
  while IFS="$(printf '\t')" read -r k h f; do
    [ "$k" = sha256 ] || continue
    case $f in *" "*) continue ;; esac
    [ -f "$R/$f" ] || { bad="$bad $f(missing)"; continue; }
    [ "$(sha256sum < "$R/$f" | cut -c1-64)" = "$h" ] || bad="$bad $f"
  done < "$R/PROVENANCE"
  [ -z "$bad" ] && ok "C6 PROVENANCE hashes match" || fail "C6 PROVENANCE does not match:$bad"
  # 7 the plugin's own byte check
  if [ -f "$R/plugins/vibrobeast/check.sh" ]; then
    ( cd "$R/plugins/vibrobeast" && sh check.sh ) > /tmp/vbck.$$ 2>&1 && ok "C7 plugin bytes match its MANIFEST" || fail "C7 plugin check.sh: $(tail -2 /tmp/vbck.$$ | tr '\n' ' ')"
    rm -f /tmp/vbck.$$
  else fail "C7 plugins/vibrobeast/check.sh is missing"; fi
  # 7b the servers-only plugin: its own bytes, and the same servers as the full plugin, byte for byte
  if [ -d "$R/plugins/vibrobeast-servers" ]; then
    if ( cd "$R/plugins/vibrobeast-servers" && sh check.sh ) > /tmp/vbck.$$ 2>&1 \
       && diff -r -x __pycache__ "$R/plugins/vibrobeast/servers" "$R/plugins/vibrobeast-servers/servers" > /dev/null 2>&1 \
       && [ ! -e "$R/plugins/vibrobeast-servers/skills" ]; then
      ok "C7b servers-only plugin: its MANIFEST holds, its servers are the full plugin's, no skills"
    else fail "C7b servers-only plugin: $(tail -2 /tmp/vbck.$$ | tr '\n' ' ')"; fi
    rm -f /tmp/vbck.$$
  fi
  # 8 every server builds its tools (doors off), from the plugin as shipped
  if out=$(cd "$R/plugins/vibrobeast/servers" && "$PY" -B launch.py --list 2>&1); then
    ok "C8 servers build: $(printf '%s\n' "$out" | grep -c '^[a-z]') servers, $(printf '%s\n' "$out" | grep -c '^    ') tools"
  else fail "C8 servers do not build: $(printf '%s\n' "$out" | tail -2 | tr '\n' ' ')"; fi
  # 9 the extension: its hub starts every server from the unpacked .mcpb and answers initialize
  x=$(mktemp -d)
  if "$PY" -m zipfile -e "$R/extension/vibrobeast.mcpb" "$x" 2>/dev/null; then
    out=$(HOME=$x "$PY" - "$x" <<'P'
import json, subprocess, sys
x = sys.argv[1]
p = subprocess.Popen([sys.executable, "-B", f"{x}/server/launch.py", "hub"], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
def rpc(i, m, a=None):
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": a or {}}) + "\n"); p.stdin.flush()
    while True:
        r = json.loads(p.stdout.readline())
        if r.get("id") == i: return r
rpc(1, "initialize", {"protocolVersion": "2024-11-05"})
st = json.loads(rpc(2, "tools/call", {"name": "vibrobeast_status", "arguments": {}})["result"]["content"][0]["text"])
p.stdin.close(); p.wait(30)
down = [s["name"] for s in st["servers"] if s["state"] != "running"]
print("DOWN " + " ".join(down) if down else f"{len(st['servers'])} servers running, {st['tools_total']} tools")
P
)
    case $out in DOWN*|"") fail "C9 extension hub: ${out:-no answer}" ;; *) ok "C9 extension hub: $out" ;; esac
  else fail "C9 extension/vibrobeast.mcpb does not unpack"; fi
  rm -rf "$x"
  # 11 no bytecode ships (a .pyc is code nobody can read; the plugin's check.sh treats one as hostile)
  pyc=$(find "$R" -path "$R/.git" -prune -o \( -name '*.pyc' -o -name __pycache__ \) -print | head -3)
  [ -z "$pyc" ] && ok "C11 no bytecode in the tree" || fail "C11 bytecode in the tree: $(printf '%s ' $pyc)"
  # 10 the icon's two renderers agree (gwicon.js and gwicon.py share one model)
  G=$R/plugins/vibrobeast/servers/polygram/mcp
  if [ ! -f "$G/gwicon.js" ]; then skip "C10 no gwicon in this build"
  elif ! command -v node >/dev/null 2>&1; then skip "C10 needs node for the JavaScript renderer"
  else
    in='{"letter":"G","hosts":[["gw7",[["up",100],["load",80],["disk",55]]],["gw33",[["down",0]]]]}'
    a=$(printf '%s' "$in" | node "$G/gwicon.js")
    b=$(cd "$R/plugins/vibrobeast/servers" && "$PY" -B -c 'import json,sys; from polygram.mcp import gwicon; i=json.loads(sys.argv[1]); print(gwicon.render(i["letter"], [(h,p) for h,p in i["hosts"]])[1])' "$in")
    [ -n "$a" ] && [ "$a" = "$b" ] && ok "C10 icon renderers agree" || fail "C10 gwicon.js and gwicon.py differ"
  fi
}

prove_red() {
  t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; bad=0
  plant() {  # label, check id, shell that breaks the copy at $c
    lbl=$1; id=$2; shift 2
    c=$t/$id; rm -rf "$c"; mkdir -p "$c"; ( cd "$here" && tar --exclude=.git -cf - . ) | ( cd "$c" && tar -xf - )
    ( cd "$c" && eval "$*" )
    if sh "$here/.github/ci/check.sh" "$c" 2>&1 | grep -q "^FAIL  $id "; then echo "  red  $id $lbl"; else echo "  MISSED $id $lbl"; bad=$((bad+1)); fi; }
  plant "a script that does not parse" C1 'f=$(find plugins -name "*.sh" | head -1); echo "if then fi (" >> "$f"'
  plant "a Python file that does not compile" C2 'f=$(find plugins -name "*.py" | head -1); echo "def (:" >> "$f"'
  plant "a JSON file that is not JSON" C3 'echo "{" > plugins/vibrobeast/broken.json'
  plant "a skill with no description" C4 'f=$(ls plugins/vibrobeast/skills/*/SKILL.md | head -1); sed -i "/^description:/d" "$f"'
  plant "a marketplace entry under the wrong name" C5 'sed -i "s/\"name\": \"vibrobeast-skills\"/\"name\": \"vibrobeast-skillz\"/" .claude-plugin/marketplace.json'
  plant "an artifact changed after PROVENANCE" C6 'echo x >> extension/vibrobeast.mcpb'
  plant "a stray .pyc" C11 'mkdir -p plugins/vibrobeast/servers/__pycache__ && echo x > plugins/vibrobeast/servers/__pycache__/x.pyc'
  plant "a plugin file changed after its MANIFEST" C7 'f=$(ls plugins/vibrobeast/skills/*/SKILL.md | head -1); echo x >> "$f"'
  plant "a server differs between the full and the servers-only plugin" C7b 'echo "# x" >> plugins/vibrobeast-servers/servers/launch.py'
  [ $bad -eq 0 ] && { echo "check: PROVE-RED OK"; return 0; } || { echo "check: PROVE-RED FAILED ($bad missed)"; return 1; }; }

case ${1:-} in
  --prove-red) prove_red ;;
  *) checks "${1:-$here}"; rc=$?; [ $rc -eq 2 ] && exit 2
     echo "check: $fails failed, $skips not checked here"; [ $fails -eq 0 ] ;;
esac
