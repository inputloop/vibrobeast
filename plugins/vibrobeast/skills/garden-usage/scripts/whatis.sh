#!/bin/sh
# whatis.sh - what is this thing in the garden, in one sentence, and how do I use it?
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  Authored by Mentat (for Corwin).
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.  SPDX-License-Identifier: GPL-3.0-or-later
#
# usage: sh whatis.sh NAME [--json]     every meaning NAME has here, each in one sentence
#        sh whatis.sh --list              every skill, one line each (label and its sentence)
# Looks in, first found first: the four-name register (C4 c/skillnames), the tool register (C4
# c/names), the skills installed beside this one, and C4 entities under Z/ (first lines).
# C4 is found at $C4_ROOT, else /f/claude/c4, else ~/mnt/c4; without it, only installed skills.
# A skill that is SOFT here (a folder under a SOFT-SKILLS root, not installed) is answered with the
# line that reads it: soft_skill_read NAME.  Soft roots: $GARDEN_SOFT (os.pathsep-separated: ";" on Windows, else ":"), else
# $SOFT_SKILLS, ~/.mentcached/SOFT-SKILLS, <$MENTCACHED_SEAT>/../SOFT-SKILLS and the SOFT-SKILLS
# folder beside the skills (ERRATA E3).  The softskills.roots preference is the server's to read.
# A NAME with two meanings prints both, marked SEAM; nothing is picked on the reader's behalf.
# Exit: 0 found - 1 not known here (the closest names are printed) - 2 usage.

set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILLS=${GARDEN_SKILLS:-$(CDPATH= cd -- "$here/../.." && pwd)}
C4=${C4_ROOT:-}
[ -n "$C4" ] || for c in /f/claude/c4 "$HOME/mnt/c4"; do [ -d "$c/c" ] && { C4=$c; break; }; done
roots_nl() {   # an os.pathsep list -> one root a line: ';' when there is one (Windows), else ':', but
  # never the colon of a drive letter ("C:/x", "C:\x"), which tr ':;' cut in two (make check, 2026-10-15)
  printf '%s\n' "$1" | awk '{ n = 0; if (index($0, ";")) n = split($0, a, ";")
    else { cur = ""; for (i = 1; i <= length($0); i++) { c = substr($0, i, 1)
        if (c == ":" && !(cur ~ /^[A-Za-z]$/ && substr($0, i + 1, 1) ~ /[\/\\]/)) { a[++n] = cur; cur = "" } else cur = cur c }
      a[++n] = cur }
    for (i = 1; i <= n; i++) if (a[i] != "") print a[i] }'
}
nl='
'
SEATSOFT=''; [ -n "${MENTCACHED_SEAT:-}" ] && SEATSOFT=$(dirname -- "$MENTCACHED_SEAT")/SOFT-SKILLS$nl
if [ -n "${GARDEN_SOFT:-}" ]; then SOFT=$(roots_nl "$GARDEN_SOFT")
else SOFT=${SOFT_SKILLS:+$(roots_nl "$SOFT_SKILLS")$nl}$HOME/.mentcached/SOFT-SKILLS$nl$SEATSOFT$SKILLS/../SOFT-SKILLS; fi

soft_dir() {   # NAME -> the first soft root's folder for it, if any (and only if not installed)
  [ -f "$SKILLS/$1/SKILL.md" ] && return 1
  _ifs=$IFS; IFS=$nl
  for r in $SOFT; do [ -n "$r" ] && [ -f "$r/$1/SKILL.md" ] && { IFS=$_ifs; printf '%s\n' "$r/$1"; return 0; }; done
  IFS=$_ifs; return 1
}

first_sentence() {   # the description in SKILL.md $1, joined, first sentence
  awk 'NR == 1 && $0 == "---" { fm = 1; next }
       fm && $0 == "---" { exit }
       fm && /^description:/ { v = $0; sub(/^description:[ \t]*/, "", v)
         if (v ~ /^[>|]/) { blk = 1; v = "" } d = v; next }
       fm && blk && /^[ \t]/ { t = $0; sub(/^[ \t]+/, "", t); d = d (d ? " " : "") t; next }
       fm && blk { blk = 0 }
       END { gsub(/^["\x27]|["\x27]$/, "", d)
             n = index(d, ". "); if (n) d = substr(d, 1, n); print d }' "$1"
}

hits=0; out=''; json=''
say() { hits=$((hits+1)); out="$out$1
"; json="$json${json:+,}{\"kind\":\"$2\",\"name\":\"$3\",\"sentence\":\"$(printf '%s' "$4" | sed 's/\\/\\\\/g; s/"/\\"/g')\"}"; }

lookup() {
  n=$1
  if [ -n "$C4" ] && [ -f "$C4/c/skillnames" ]; then
    row=$(grep -v '^#' "$C4/c/skillnames" | awk -F'\t' -v n="$n" '$1==n||$2==n||$3==n||$4==n' | head -1)
    if [ -n "$row" ]; then
      label=$(printf '%s' "$row" | cut -f1); others=$(printf '%s' "$row" | tr '\t' '\n' | grep -vx "$n" | tr '\n' ' ')
      s=''; [ -f "$SKILLS/$label/SKILL.md" ] && s=$(first_sentence "$SKILLS/$label/SKILL.md")
      sd=$(soft_dir "$label") || sd=''
      [ -z "$s" ] && [ -n "$sd" ] && s=$(first_sentence "$sd/SKILL.md")
      [ -z "$s" ] && [ -f "$C4/dist/skills/$label/SKILL.md" ] && s=$(first_sentence "$C4/dist/skills/$label/SKILL.md")
      if [ -n "$sd" ]; then use="Use it: it is a SOFT skill here, not installed; read it with soft_skill_read $label"
      else use="Use it: ask for it by any of its names, or describe the task; it loads when the task matches."; fi
      say "$n is a SKILL (label $label; also named: ${others% }). ${s:-(its description was not found here)}
    $use" skill "$label" "$s"
    fi
  fi
  if [ -z "${row:-}" ] && [ -f "$SKILLS/$n/SKILL.md" ]; then
    s=$(first_sentence "$SKILLS/$n/SKILL.md"); say "$n is a SKILL. $s
    Use it: ask for it by name, or describe the task; it loads when the task matches." skill "$n" "$s"
  fi
  if [ -z "${row:-}" ] && sd=$(soft_dir "$n"); then
    s=$(first_sentence "$sd/SKILL.md"); say "$n is a SOFT SKILL (served live from $(dirname "$sd"), not installed). $s
    Read it: soft_skill_read $n   (the mentcached server's tool)" soft "$n" "$s"
  fi
  if [ -n "$C4" ] && [ -f "$C4/c/names" ]; then
    grep -v '^#' "$C4/c/names" | awk -F'\t' -v n="$n" '$1==n||$2==n' | while IFS='	' read -r plain code path purpose; do
      printf 'TOOL\t%s\t%s\t%s\t%s\n' "$plain" "$code" "$path" "$purpose"; done > "${TMPDIR:-/tmp}/whatis.$$"
    while IFS='	' read -r _ plain code path purpose; do
      say "$n is a TOOL ($plain; coded name $code). What it does: $purpose.
    Use it: sh $C4/$path --help" tool "$plain" "$purpose"
    done < "${TMPDIR:-/tmp}/whatis.$$"; rm -f "${TMPDIR:-/tmp}/whatis.$$"
  fi
  if [ -n "$C4" ] && [ -d "$C4/Z" ]; then
    for e in $(find "$C4/Z" -maxdepth 4 -type f -name "$n" 2>/dev/null | head -4); do
      say "$n is an ENTITY ($(basename "$(dirname "$e")")). $(sed -n 1p "$e")
    Read it: $e" entity "$n" "$(sed -n 1p "$e")"
    done
  fi
}

case ${1:-} in
  ''|-h|--help) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
  --list) for d in "$SKILLS"/*/; do [ -f "$d/SKILL.md" ] && printf '%-28s %s\n' "$(basename "$d")" "$(first_sentence "$d/SKILL.md")"; done
          IFS=$nl; for r in $SOFT; do IFS=' '; for d in "$r"/*/; do n=$(basename "$d"); [ -f "$d/SKILL.md" ] && [ ! -f "$SKILLS/$n/SKILL.md" ] && printf '%-28s (soft) %s\n' "$n" "$(first_sentence "$d/SKILL.md")"; done; IFS=$nl; done; exit 0 ;;
esac
lookup "$1"
if [ "${2:-}" = --json ]; then printf '{"name":"%s","meanings":[%s]}\n' "$1" "$json"; [ $hits -gt 0 ]; exit $?; fi
if [ $hits -eq 0 ]; then
  printf '%s is not known here.' "$1"
  near=$( { [ -n "$C4" ] && grep -v '^#' "$C4/c/skillnames" 2>/dev/null | tr '\t' '\n'; ls "$SKILLS" 2>/dev/null; } | grep -i -- "$(printf '%s' "$1" | cut -c1-4)" | sort -u | head -6 | tr '\n' ' ')
  [ -n "$near" ] && printf ' Closest names: %s' "$near"; printf '\n'; exit 1
fi
[ $hits -gt 1 ] && printf 'SEAM: "%s" means %d things here; each is below. Say which you mean.\n' "$1" "$hits"
printf '%s' "$out"
