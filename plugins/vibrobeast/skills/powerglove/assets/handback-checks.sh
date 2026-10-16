# handback-checks.sh -- the named checks a glove string can carry ("  !NAME"), read by bin/pg1lv only.
#
# A ledger can NAME a check; it can never bring one.  pg1lv runs hb_NAME from this file and nothing
# else, so a ledger (plain text anyone can edit) cannot run a command of its own.
#
# Each check reads HB_ROOT (the ledger's root), HB_REPOS (newline-separated repositories: the root,
# and every repository a git: receipt names), HB_SINCE (a file whose mtime is when the ledger opened)
# and HB_LEDGER.  It prints one line of finding (more lines may follow, indented) and returns:
#   0  OK     the question is answered by the tree
#   3  ASK    a person decides (it may be another session's work); never a failure, never a pass
#   1  FAULT  something was left that should not have been
# Wired 2026-10-16 from inculcat-boxer (the material has to go somewhere) after a session's git
# debris and three stray queues were found by somebody else, who then asked him what to do with them.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st> and Contributors.  Mentat (for Corwin; claude-opus-5-5).
# SPDX-License-Identifier: GPL-3.0-or-later

hb__repos() { printf '%s\n' "$HB_REPOS" | while IFS= read -r r; do [ -n "$r" ] && [ -d "$r/.git" ] && printf '%s\n' "$r"; done; }
hb__newer() { [ -n "${HB_SINCE:-}" ] && [ -f "$HB_SINCE" ] || return 0; [ "$1" -nt "$HB_SINCE" ]; }

# Did you leave a lock or a temp file in a repository's .git?  (a git that could not delete its own)
hb_debris() {
  found=""; n=0
  for r in $(hb__repos | tr '\n' ' '); do n=$((n + 1))
    for f in $(find "$r/.git" -maxdepth 3 \( -name '*.lock' -o -name 'tmp_obj_*' -o -name 'tmp_pack_*' \) 2>/dev/null | grep -v stale); do
      hb__newer "$f" && found="$found
    $f"
    done
  done
  if [ -n "$found" ]; then echo "left in .git since this prompt opened (if no git is running, they are leftovers):$found"; return 1; fi
  echo "no lock or temp file left in $n repositor$( [ "$n" = 1 ] && echo y || echo ies)"; return 0
}

# Did you leave files for someone else to ask about?  (written since the ledger opened, not committed)
hb_strays() {
  found=""
  for r in $(hb__repos | tr '\n' ' '); do
    git -C "$r" --no-optional-locks status --porcelain --untracked-files=all 2>/dev/null | sed -n 's/^?? //p' |
      while IFS= read -r p; do hb__newer "$r/$p" && printf '    %s/%s\n' "$r" "$p"; done > "${HB_SINCE}.strays.$$" 2>/dev/null
    [ -s "${HB_SINCE}.strays.$$" ] && found="$found
$(cat "${HB_SINCE}.strays.$$")"
    rm -f "${HB_SINCE}.strays.$$"
  done
  if [ -n "$found" ]; then echo "untracked and new since this prompt opened: commit, card or say each (some may be another session's):$found"; return 3; fi
  echo "nothing untracked was written since this prompt opened"; return 0
}

# Did each file you wrote land in a documented home?  (bin/hb1ck --layout, where a repository has it)
hb_layout() {
  ran=0; bad=0; out=""
  for r in $(hb__repos | tr '\n' ' '); do
    [ -f "$r/bin/hb1ck" ] && [ -f "$r/INDEX.md" ] || continue; ran=$((ran + 1))
    lst=${HB_SINCE}.files.$$
    { git -C "$r" --no-optional-locks log --since="$(sed -n 's/^# opened: *//p' "$HB_LEDGER" | head -1)" --name-only --format= 2>/dev/null
      git -C "$r" --no-optional-locks status --porcelain --untracked-files=all 2>/dev/null | sed -n 's/^?? //p'; } | sort -u | grep . > "$lst"
    res=$(sh "$r/bin/hb1ck" --layout "$r" --since "$lst" 2>&1); rc=$?; rm -f "$lst"
    [ $rc -eq 0 ] || { bad=1; out="$out
$(printf '%s\n' "$res" | grep FAULT | sed "s|^|    $r: |")"; }
  done
  [ $ran -gt 0 ] || { echo "NOT CHECKED: no repository here carries bin/hb1ck and INDEX.md"; return 3; }
  [ $bad -eq 0 ] && { echo "every file written since this prompt opened sits in a documented home ($ran map(s) read)"; return 0; }
  echo "a file landed off its map:$out"; return 1
}

# Did an ENHANCE queue land in the advice ledger, not in a scratch folder?  (bin/eh1dx --check)
hb_home() {
  ran=0
  for r in $(hb__repos | tr '\n' ' '); do
    [ -f "$r/bin/eh1dx" ] || continue; ran=1
    res=$(cd "$r" && sh bin/eh1dx --check 2>&1) || { echo "$res" | sed '1!s/^/    /'; return 1; }
  done
  [ $ran -eq 1 ] && { echo "no ENHANCE queue sits in a not-home"; return 0; }
  echo "NOT CHECKED: no repository here carries bin/eh1dx"; return 3
}

# Did you leave another prompt's strings taut?  (other open ledgers under the root's q/)
hb_ledgers() {
  others=$(for f in "$HB_ROOT"/q/*/STRINGS; do [ -f "$f" ] || continue; [ "$f" -ef "$HB_LEDGER" ] && continue
             grep -q '^# closed:\|^# bailed:' "$f" || printf '    %s (%s taut)\n' "$f" "$(grep -c '^\[ \] ' "$f")"; done)
  [ -z "$others" ] && { echo "no other open ledger under $HB_ROOT/q"; return 0; }
  echo "other ledgers are still open (close, bail or say why they wait):
$others"; return 3
}
