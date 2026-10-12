#!/bin/sh
# --prove-red for check-interpreter.sh: plant an interpreter that cannot work
# and watch the check go red. A check that has never said no carries no news.
set -eu
cd "$(dirname "$0")"
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cp check-interpreter.sh "$d/"; cp -r servers "$d/servers"
faults=0; fired=0

plant() {   # name, command-json, args-json
  faults=$((faults+1))
  printf '{\n  "mcpServers": {\n    "mentcached": {\n      "command": %s,\n      "args": %s,\n      "env": {}\n    }\n  }\n}\n' \
    "$2" "$3" > "$d/.mcp.json"
  if ( cd "$d" && sh check-interpreter.sh >/dev/null 2>&1 ); then
    printf '  MISSED  %s -- the check stayed green\n' "$1"
  else
    printf '  ok      %s -- went red\n' "$1"; fired=$((fired+1))
  fi
}

echo "RED -- one planted fault per rule:"
plant "an interpreter that is not on PATH" \
      '"definitely-not-an-interpreter-xyz"' '["-m", "polygram.mcp", "mentcached"]'
plant "a command that runs but is not python" \
      '"echo"' '["-m", "polygram.mcp", "mentcached"]'
plant "a bare py, the launcher unqualified" \
      '"py-that-does-not-exist"' '["-m", "polygram.mcp", "mentcached"]'

echo "GREEN -- what must hold:"
# NOT the baked interpreter. This proves the CHECK can say yes; whether the
# BAKED command works here is what `sh check-interpreter.sh` is for, and on a
# cross-host mint the honest answer to that is often no. Conflating the two
# would make --prove-red fail on exactly the machine that minted correctly.
faults=$((faults+1))
here=""
for c in python3 python "py -3"; do
  if $c -c 'import sys;sys.exit(0 if sys.version_info[:2]>=(3,10) else 1)' >/dev/null 2>&1; then here=$c; break; fi
done
if [ -z "$here" ]; then
  printf '  SKIP    no python on this host to prove the yes-case with\n'; faults=$((faults-1))
else
  hc=${here%% *}; hrest=${here#"$hc"}
  if [ "$hrest" = "$here" ]; then hargs='"-m", "polygram.mcp", "mentcached"'
  else hargs="\"${hrest# }\", \"-m\", \"polygram.mcp\", \"mentcached\""; fi
  printf '{\n  "mcpServers": {\n    "mentcached": {\n      "command": "%s",\n      "args": [%s],\n      "env": {}\n    }\n  }\n}\n' \
    "$hc" "$hargs" > "$d/.mcp.json"
  if ( cd "$d" && sh check-interpreter.sh >/dev/null 2>&1 ); then
    printf '  ok      an interpreter that DOES work here (%s) passes\n' "$here"; fired=$((fired+1))
  else
    printf '  MISSED  %s works but the check called it a fault\n' "$here"
  fi
fi

if [ "$fired" -eq "$faults" ]; then
  printf '\ncheck-interpreter: --prove-red OK (%s of %s)\n' "$fired" "$faults"; exit 0
fi
printf '\ncheck-interpreter: --prove-red FAILED (%s of %s)\n' "$fired" "$faults"; exit 1
