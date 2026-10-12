#!/bin/sh
# check-interpreter.sh -- does the interpreter this plugin was minted with
# actually START on THIS machine?
#
# check.sh answers "are these the bytes that were minted". This answers the
# other question, and it is the one that has actually bitten: a plugin whose
# bytes are perfect and whose `command` line names an interpreter this host
# does not have reports `not_started / could_not_prepare` and hands the reader
# no error they can act on. On Windows `python3` is frequently an App
# Execution Alias that exits without ever being an interpreter, which is
# exactly that shape.
#
# The mint cannot answer this for you. It bakes the command on the MINTING
# host; the servers run on the INSTALLING host, and on this estate those are
# not the same machine. So the claim travels as a check you run where it
# lands, rather than as an assertion made somewhere it could not be tested.
#
# No python is needed to READ this file -- it extracts the argv from
# .mcp.json, which this plugin generated itself in a known shape, with sed.
set -eu
cd "$(dirname "$0")"
me=check-interpreter.sh
[ -f .mcp.json ] || { echo "$me: no .mcp.json beside me"; exit 2; }

# The generated shape is one "command" line and one "args" array per server,
# indent=2, no tabs. Anything else is not a file this plugin wrote.
argv_of() {          # server -> argv, one token per line
  sed -n "/\"$1\": {/,/^    }/p" .mcp.json |
  sed -n -e 's/.*"command": "\(.*\)".*/\1/p' \
         -e '/"args": \[/,/\]/ s/^ *"\([^"]*\)",\{0,1\} *$/\1/p'
}

servers=$(sed -n 's/^    "\([a-z][a-z0-9_-]*\)": {$/\1/p' .mcp.json)
[ -n "$servers" ] || { echo "$me: no servers in .mcp.json"; exit 2; }

# Claude Desktop will not PREPARE a plugin server whose env names PYTHONPATH. Its own log
# (avalon, 2026-09-19..23): `failed to build host proxy target: env declares reserved variable
# name "PYTHONPATH"`, and the servers show as not_started / could_not_prepare with no error
# surfaced anywhere a reader would look. So this is checked before any interpreter is.
if grep -q '"PYTHONPATH"' .mcp.json; then
  printf 'FAULT  .mcp.json declares PYTHONPATH in an env block. Claude Desktop refuses to prepare
'
  printf '       such a server ("env declares reserved variable name"); re-mint from a polygram
'
  printf '       checkout dated 2026-09-23 or later, which launches through servers/launch.py.
'
  exit 1
fi

# 2026-10-08: a Windows mint starts every server as `cmd /d /c <plugin>\servers\launch.cmd NAME`,
# and launch.cmd FINDS a Python itself (VIBROBEAST_PYTHON, py -3, python3/python on PATH but never
# the WindowsApps stub, the MSYS2 trees, python.org installs). There is no interpreter in .mcp.json
# to test, so the finder is what is run: through cmd.exe, the way the app runs it.
if grep -q '"command": "cmd"' .mcp.json; then
  [ -f servers/launch.cmd ] || { printf 'FAULT  .mcp.json starts the servers through cmd, and servers/launch.cmd is missing\n'; exit 1; }
  if ! command -v cmd.exe >/dev/null 2>&1; then
    printf 'NOT CHECKED  this plugin starts its servers through cmd.exe (a Windows mint), and there is\n'
    printf '             no cmd.exe here. Run this script on the Windows machine (Git Bash or MSYS2), or\n'
    printf '             run servers\\launch.cmd --list in a Command Prompt there.\n'
    exit 2
  fi
  # MSYS2 and Git Bash rewrite /d and /c into drive paths unless told not to.
  if ! out=$(MSYS2_ARG_CONV_EXCL='*' MSYS_NO_PATHCONV=1 cmd.exe /d /c 'servers\launch.cmd' --list 2>&1); then
    printf 'FAULT  servers\\launch.cmd could not start the servers here. What it said:\n'
    printf '%s\n' "$out" | sed 's/^/       /'
    exit 1
  fi
  printf '%s\n' "$out" | sed -n 's/^vibrobeast: starting the .* server with /OK     launch.cmd found Python: /p'
  bad=0
  for s in $servers; do
    if printf '%s\n' "$out" | grep -q "^$s "; then printf 'OK     %s: listed by launch.cmd --list\n' "$s"
    else printf 'FAULT  %s: not listed by launch.cmd --list\n' "$s"; bad=$((bad+1)); fi
  done
  [ "$bad" -eq 0 ] && { printf '\nOK  every server starts through launch.cmd on this machine.\n'; exit 0; }
  exit 1
fi

bad=0; n=0
for s in $servers; do
  n=$((n+1))
  # Only the interpreter prefix -- everything before -m -- is what we test.
  # Two shapes now: `-m polygram.mcp NAME`, and the zero-substitution
  # `<abs>/servers/launch.py NAME`. Stop at whichever comes first.
  pre=$(argv_of "$s" | awk '$0=="-m"||/\.py$/{exit} {print}')
  [ -n "$pre" ] || { printf 'FAULT  %s: could not read a command out of .mcp.json\n' "$s"; bad=$((bad+1)); continue; }
  shown=$(printf '%s ' $pre); shown=${shown% }
  if ! out=$($pre -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>&1); then
    printf 'FAULT  %s: `%s` did not run\n       %s\n' "$s" "$shown" "$(printf '%s' "$out" | tail -1)"
    bad=$((bad+1)); continue
  fi
  case "$out" in
  3.[89]|3.1[0-9]*) ;;
  *) printf 'FAULT  %s: `%s` reported python %s; this needs 3.10+\n' "$s" "$shown" "$out"
     bad=$((bad+1)); continue ;;
  esac
  # This mint bakes the launcher's path ABSOLUTE, because nothing in its
  # .mcp.json is expanded by anybody. So where the default shape has one
  # thing to check, this one has two -- and the first is the likelier to be
  # wrong: a tree minted on one host and installed at another path.
  lp=$(argv_of "$s" | awk '/\.py$/{print; exit}')
  if [ -n "$lp" ]; then
    # The default shape names it as ${CLAUDE_PLUGIN_ROOT}/servers/launch.py; the app expands that
    # to the plugin root, which is the directory this script cd'd into.
    case $lp in '${CLAUDE_PLUGIN_ROOT}'/*) lp=$PWD/${lp#'${CLAUDE_PLUGIN_ROOT}'/} ;; esac
    if [ ! -f "$lp" ]; then
      printf 'FAULT  %s: the baked launcher path is not a file on THIS host\n       %s\n' "$s" "$lp"
      printf '       Re-mint naming where this tree really lives:\n'
      printf '       polygram dist --format plugin --self-locating --install-root DIR\n'
      bad=$((bad+1)); continue
    fi
    # And the claim this mint exists to make: the launcher finds the servers
    # with NO PYTHONPATH set, because it works out its own directory.
    if ! imp=$( unset PYTHONPATH; $pre servers/launch.py --list 2>&1 ); then
      printf 'FAULT  %s: `%s` runs, but servers/launch.py could not list\n       %s\n' \
             "$s" "$shown" "$(printf '%s' "$imp" | tail -1)"
      bad=$((bad+1)); continue
    fi
  # A config in the OTHER shape -- `-m polygram.mcp NAME` -- is still a config
  # this script gets handed: check-interpreter-prove-red.sh plants three of
  # them, and so does anyone comparing the two arms by hand. Check it the way
  # the default mint would rather than calling it malformed. This clause was
  # written because prove-red went from 4/4 to 3/4 without it, and a harness
  # that fails for its own reasons stops being read.
  elif ! imp=$(PYTHONPATH=servers PYTHONDONTWRITEBYTECODE=1 $pre -c 'import polygram.mcp' 2>&1); then
    printf 'FAULT  %s: `%s` runs, but cannot import the shipped server\n       %s\n' \
           "$s" "$shown" "$(printf '%s' "$imp" | tail -1)"
    bad=$((bad+1)); continue
  fi
  printf 'OK     %s: `%s` is python %s and imports the server\n' "$s" "$shown" "$out"
done

if [ "$bad" -eq 0 ]; then
  printf '\nOK  %s server(s) will start with the interpreter this plugin was minted with.\n' "$n"
  exit 0
fi
cat <<'FIX'

FAULT  Something baked at mint time does not work here. Nothing is wrong
       with the bytes.

       If the fault above named the LAUNCHER PATH, the interpreter is fine
       and this tree is not where its .mcp.json says it is. Re-mint with
       --install-root naming where it actually lives.

       If it named the interpreter, re-mint with one that works, from the
       polygram checkout:

           python -m polygram dist --format plugin --python auto
           python -m polygram dist --format plugin --python 'py -3'
           python -m polygram dist --format plugin --python /mingw64/bin/python3

       `auto` probes python3, python, then py -3 ON THE MINTING HOST and bakes
       the first that starts -- so run it on the machine that will RUN the
       plugin, or name the interpreter yourself. A spec may carry its own
       flags; the argv probed is the argv baked.
FIX
exit 1
