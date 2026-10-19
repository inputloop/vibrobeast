#!/bin/sh
# tests.sh -- pocket-binder: the demonstration register reads as its README says, and goes red
# when a verdict is planted wrong.  POSIX sh.  The two-reader spec is tests/kb1nd-spec.rb (Ruby)
# in the source tree.  usage: sh tests.sh [--prove-red]
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
B="sh $here/scripts/bind.sh"
unset VIBROBEAST_API_TOKEN VIBROBEAST_API_TOKEN_FOR VIBROBEAST_SSH_KEY GW_PASSWORD
pass=0; fail=0
want() {   # want NAME VERDICT KEY [bind.sh to use]
  got=$(${4:-$B} --tsv -r "$here/fixtures/register.tsv" "$1" | cut -f2,3 | tr '\t' ' ')
  if [ "$got" = "$2 $3" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL $1: got '$got', want '$2 $3'"; fi
}
suite() {
  want GH_TOKEN TIE - "$@"
  want GITLAB_TOKEN BOUND lab "$@"
  want GIT_SSH_COMMAND BOUND forge "$@"
  want GH_ENTERPRISE_TOKEN BOUND hub2 "$@"
  want WEATHER NONE - "$@"
}
suite
# the refused row is ignored: no key named leaky ever answers. The row is planted here, at run time, with its
# token-shaped SOURCE put together from pieces, so that no file this skill ships holds a string shaped like a
# key (the directory's scan refuses one, demonstration or not; 2026-10-18).
lk=$(mktemp); cat "$here/fixtures/register.tsv" > "$lk"
printf 'leaky\ttoken\t%s%s\tPLANTED_TOKEN\tgithub\t\t\ta planted, refused row: no key\n' "gh""p_" "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" >> "$lk"
if $B --tsv -r "$lk" PLANTED_TOKEN GITHUB_TOKEN | grep -q leaky; then fail=$((fail+1)); echo "  FAIL leaky answered"; else pass=$((pass+1)); fi
grep -q '^leaky' "$lk" || { fail=$((fail+1)); echo "  FAIL the refused row was not planted"; }
rm -f "$lk"
# words mode says "ask" for a tie
if $B -r "$here/fixtures/register.tsv" GH_TOKEN | grep -q "ask which"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL tie not said in words"; fi
if [ "${1-}" = --prove-red ]; then
  # The planted copy keeps the layout (scripts/ beside fixtures/), so it fails on its verdicts and
  # not on a missing word file (the unexercised-branch lesson: a planted failure must speak).
  t=$(mktemp -d); mkdir -p "$t/scripts" "$t/fixtures"; cp "$here/fixtures/key.md" "$t/fixtures/"
  sed 's/else if (nbest > 1) out = "TIE"/else if (0) out = "TIE"/' "$here/scripts/bind.sh" > "$t/scripts/bind.sh"
  if cmp -s "$here/scripts/bind.sh" "$t/scripts/bind.sh"; then echo "  FAIL the plant did not apply"; fail=$((fail+1)); fi
  if sh "$t/scripts/bind.sh" --tsv -r "$here/fixtures/register.tsv" GH_TOKEN 2>&1 | grep -q "cannot read"; then
    echo "  FAIL the planted copy cannot read its word file"; fail=$((fail+1)); fi
  before=$fail; bp=$pass; suite "sh $t/scripts/bind.sh" >/dev/null 2>&1; red=$((fail-before)); fail=$before; pass=$bp
  rm -rf "$t"
  if [ "$red" -gt 0 ]; then echo "  ok   a binder that never ties fails $red case(s)"; else echo "  FAIL planted fault stayed green"; fail=$((fail+1)); fi
  # Second plant: a binder that takes a key in its SOURCE (both refusals off: the SOURCE shape and the
  # secret-shaped cell). The planted leaky row must then answer, and the check above must catch it.
  t=$(mktemp -d); mkdir -p "$t/scripts" "$t/fixtures"; cp "$here/fixtures/key.md" "$t/fixtures/"
  sed -e 's#if (k != "-" \&\& src !~#if (0 \&\& src !~#' -e 's#^  return (s ~ /ghp_#  return 0; (s ~ /ghp_#' "$here/scripts/bind.sh" > "$t/scripts/bind.sh"
  lk=$(mktemp); cat "$here/fixtures/register.tsv" > "$lk"
  printf 'leaky\ttoken\t%s%s\tPLANTED_TOKEN\tgithub\t\t\ta planted row\n' "gh""p_" "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" >> "$lk"
  if sh "$t/scripts/bind.sh" --tsv -r "$lk" PLANTED_TOKEN 2>/dev/null | grep -q leaky; then echo "  ok   a binder that takes a key in its SOURCE is caught by the leaky check"
  else echo "  FAIL the leaky plant stayed green"; fail=$((fail+1)); fi
  rm -rf "$t" "$lk"
fi
echo "pocket-binder: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
