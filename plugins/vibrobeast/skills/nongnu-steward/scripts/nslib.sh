# nslib.sh -- shared by the nongnu-steward scripts: preferences, clock, hashing, small helpers.
# Sourced, never run.  POSIX sh; needs awk, and one of sha256sum / shasum / openssl.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of nongnu-steward.  It is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.  Authored by Mentat
# (for Corwin).
#
# PREFERENCES.  One file, `key value` or `key=value` per line, `#` comments, last row wins:
#   $HOME/.nongnu-steward  (yours, for every project)
#   <root>/.nongnu-steward (the project's own)
#   $NONGNU_STEWARD_PREFS  (named by you; never created)
# All three are read in that order and a later file overrides an earlier one, so a project can
# narrow what you set globally.  Beneath all three sits the mentcached prefs ledger
# ($MENTCACHED_PREFS, else ~/.mentcached/prefs.tsv: the plugin's pref_set rows, last wins), so a
# switch set from the seat holds in every tree until a file says otherwise.
# Keys the scripts read (defaults in parentheses):
#   steward.auto       (on)   implicit maintenance: run the audits at session open and report
#   steward.threshold  (10)   a file with MORE lines than this is nontrivial and needs notices
#   steward.holder     ()     copyright holder used by ns1hd --suggest
#   steward.name       ()     the program's name in "This file is part of NAME" (else the root dir's name, marked a guess)
#   steward.license    (GPL-3.0-or-later)  SPDX id used by ns1hd --suggest
#   steward.canon      (on)   ns1op reports the canon pins' age and the check command (never runs it unasked)
#   steward.ua         (a browser-like User-Agent)  some canon hosts serve a trap to bare fetchers
#   steward.timeout    (60)   seconds per HEAD (bodies get three times that); one retry on a miss
#   steward.jobs       (1)    rows ns2cn --check fetches at a time -- one, because the canon hosts are
#                             the community's own machines (cgit told a 9-wide check it was overwhelmed)
#   steward.ignore     ()     extra path fragments to skip in audits, space-separated

ns_root() { CDPATH= cd -- "${1:-.}" 2>/dev/null && pwd; }

ns_stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# ns_sha FILE -> 64 hex chars
ns_sha() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -c1-64
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -c1-64
  elif command -v openssl >/dev/null 2>&1; then openssl dgst -sha256 "$1" | awk '{print $NF}'
  else echo "nslib: no sha256 tool (sha256sum, shasum, openssl)" >&2; return 1; fi
}

# ns_pref KEY DEFAULT [ROOT] -> value
ns_pref() {
  key=$1; def=$2; root=${3:-.}
  files=""
  [ -f "$HOME/.nongnu-steward" ] && files="$HOME/.nongnu-steward"
  [ -f "$root/.nongnu-steward" ] && files="$files $root/.nongnu-steward"
  [ -n "${NONGNU_STEWARD_PREFS:-}" ] && [ -f "$NONGNU_STEWARD_PREFS" ] && files="$files $NONGNU_STEWARD_PREFS"
  # the mentcached prefs ledger (pref_set from the plugin) is the floor: ts<TAB>key<TAB>value rows, last wins
  ledger=${MENTCACHED_PREFS:-$HOME/.mentcached/prefs.tsv}
  lv=""; [ -f "$ledger" ] && lv=$(awk -F'\t' -v k="$key" '$2==k {v=$3} END {print v}' "$ledger")
  [ -n "$files" ] || { [ -n "$lv" ] && printf '%s\n' "$lv" || printf '%s\n' "$def"; return 0; }
  # shellcheck disable=SC2086
  v=$(cat $files | awk -v k="$key" '
      /^[ \t]*#/ || /^[ \t]*$/ { next }
      { line=$0; sub(/^[ \t]+/, "", line)
        if (match(line, /^[^ \t=]+[ \t]*=/)) { kk=substr(line,1,RLENGTH-1); sub(/[ \t]*$/, "", kk); vv=substr(line,RLENGTH+1) }
        else { kk=line; sub(/[ \t].*/, "", kk); vv=line; sub(/^[^ \t]*[ \t]*/, "", vv) }
        gsub(/^[ \t]+|[ \t]+$/, "", kk); gsub(/^[ \t]+|[ \t]+$/, "", vv)
        if (kk==k) out=vv }
      END { print out }')
  [ -n "$v" ] || v=$lv
  [ -n "$v" ] && printf '%s\n' "$v" || printf '%s\n' "$def"
}

# ns_is_on VALUE -> 0 when on/yes/true/1
ns_is_on() { case $(printf '%s' "$1" | tr 'A-Z' 'a-z') in on|yes|true|1) return 0 ;; *) return 1 ;; esac; }

ns_ua_default='Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/128.0'
