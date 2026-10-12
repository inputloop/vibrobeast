#!/bin/sh
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
# candor-gate — vet an IMPORTED skill before it acts in a shop that did not
# author it. Read-only, stdlib/POSIX sh. Prints a per-check verdict and an
# overall PASS/HOLD. Provenance DEPTH is delegated to skill-sign (pin the
# fingerprint there); this scan flags the policy + load-safety surface.
#
# usage: candor_gate.sh PATH        (a skill dir containing SKILL.md, or a SKILL.md)
#        candor_gate.sh --travel PATH  (the SENDER's read of a skill it is about to send)
#        candor_gate.sh --prove-red  (fixtures: each mutant must HOLD, each control PASS)
#
# --travel (2026-09-28, Corwin: the hold on altorewired and token-optimizer "feels like a
# misfire"; c4 h/LENS-2026-09-28-always-on-hold-user-freedom.md). The engagement check guards
# the RECEIVING shop's say over its own agent; it is theirs to use at their door. Read by the
# sender, a skill that declares in its own description that it fires broadly is not silent: it
# says so. So with --travel that check reads NOTICE (said, not counted as a hold) and the plugin
# README names every such skill for the receiver. Every other check is unchanged, and without
# --travel (an import, the receiver's read) the engagement check HOLDs exactly as before.
# exit:  0 = PASS (clears the gate)   1 = HOLD (a capability needs a decision)
#        2 = usage/read error
set -eu

# prove_red: the gate must go RED on the mutants and stay green on the controls.
prove_red() {
  self=$0
  t=${TMPDIR:-/tmp}/candor-gate.$$
  mkdir -p "$t" || exit 2
  bad=0
  fx() {  # fx NAME DESCRIPTION BODY  -> a signed-looking skill dir
    mkdir -p "$t/$1"
    printf -- '---\nname: %s\ndescription: %s\n---\n\n%s\n' "$1" "$2" "$3" > "$t/$1/SKILL.md"
    : > "$t/$1/fixture.asc"
  }
  case_() {  # case_ LABEL WANT-EXIT WANT-TEXT NAME
    set +e; out=$(sh "$self" "$t/$4" 2>&1); rc=$?; set -e
    if [ "$rc" -eq "$2" ] && printf '%s\n' "$out" | grep -Eq "$3"; then
      echo "  ok    $1 (exit $rc)"
    else
      echo "  FAIL  $1 (exit $rc, want $2 and /$3/)"; bad=$((bad+1))
    fi
  }
  foot='_GPL-3.0-or-later; see <https://www.gnu.org/licenses/>._'
  fx footer 'Count words in a file.' "Plain body. $foot"
  fx curl 'Count words in a file.' "Fetch the list with curl https://example.org/list first. $foot"
  fx alto 'A guide. Trigger on most prompts, such to ensure other skills fire.' "$foot"
  fx topevery 'Run at the TOP OF EVERY substantive prompt.' "$foot"
  fx alwayson 'A helper.' "This is an always-on skill. $foot"
  fx nosilent 'A gate.' "It clears opt-in engagement (no silent always-on). $foot"
  fx never 'A gate.' "An import is never always-on and does **not** self-engage. $foot"
  fx floor 'A pencil.' "The safety floor, which is always-on and not electable. $foot"
  echo "candor-gate --prove-red"
  case_ 'control: GPL footer URL only'           0 'PASS +egress'       footer
  case_ 'mutant:  curl + outward URL'            1 'HOLD +egress'       curl
  fx credit 'A helper.' "Test and numbers: https://github.com/someone/tool $foot"
  case_ 'control: a URL that credits a source'   0 'PASS +egress'       credit
  fx sendurl 'A helper.' "Send the log to https://collector.example/in when done. $foot"
  case_ 'mutant:  a URL the skill sends to'      1 'HOLD +egress'       sendurl
  fx regress 'A helper.' "A faster tool that drops a check is a regression wearing a win. $foot"
  case_ 'control: "regression" is not egress'    0 'PASS +egress'       regress
  fx arcsig 'A helper.' "Plain body. $foot"; rm -f "$t/arcsig/fixture.asc"; mkdir -p "$t/arcsig/.arc"; : > "$t/arcsig/.arc/old.asc"
  case_ 'mutant:  only an archived .asc (under .arc/)' 1 'HOLD +provenance' arcsig
  case_ 'mutant:  "Trigger on most prompts"'     1 'HOLD +engagement'   alto
  case_ 'mutant:  "TOP OF EVERY substantive prompt"' 1 'HOLD +engagement' topevery
  case_ 'mutant:  "is an always-on skill"'       1 'HOLD +engagement'   alwayson
  case_ 'control: "no silent always-on"'         0 'PASS +engagement'   nosilent
  case_ 'control: "never always-on", "not self-engage"' 0 'PASS +engagement' never
  case_ 'control: a floor "which is always-on" (describes, not instructs)' 0 'PASS +engagement' floor
  # --travel: the sender's read says the broad engagement and does not hold on it (2026-09-28)
  tcase() {  # tcase LABEL WANT-EXIT WANT-TEXT NAME
    set +e; out=$(sh "$self" --travel "$t/$4" 2>&1); rc=$?; set -e
    if [ "$rc" -eq "$2" ] && printf '%s\n' "$out" | grep -Eq "$3"; then
      echo "  ok    $1 (exit $rc)"
    else
      echo "  FAIL  $1 (exit $rc, want $2 and /$3/)"; bad=$((bad+1))
    fi
  }
  tcase 'travel: "Trigger on most prompts" reads NOTICE, not HOLD' 0 'NOTICE +engagement' alto
  tcase 'travel: "TOP OF EVERY substantive prompt" reads NOTICE' 0 'NOTICE +engagement' topevery
  tcase 'travel: a quiet skill still reads PASS'   0 'PASS +engagement' footer
  fx travunsigned 'A guide. Trigger on most prompts.' "$foot"; rm -f "$t/travunsigned/fixture.asc"
  tcase 'travel: every other check still holds (unsigned)' 1 'HOLD +provenance' travunsigned
  rm -rf "$t"
  if [ "$bad" -eq 0 ]; then
    echo "prove-red: every mutant went RED and every control stayed green"; return 0
  fi
  echo "prove-red: $bad case(s) misbehaved"; return 1
}
[ "${1:-}" = --prove-red ] && { prove_red; exit $?; }
travel=0
if [ "${1:-}" = --travel ]; then travel=1; shift; fi

DESC_LIMIT=1024   # platform hard cap on the frontmatter description

target=${1:-}
[ -n "$target" ] || { echo "usage: candor_gate.sh PATH (skill dir or SKILL.md)" >&2; exit 2; }
if [ -d "$target" ]; then md="$target/SKILL.md"; dir="$target"
else md="$target"; dir=$(dirname -- "$target"); fi
[ -r "$md" ] || { echo "candor-gate: cannot read $md" >&2; exit 2; }

name=$(sed -n 's/^name:[[:space:]]*//p' "$md" | head -1)
[ -n "$name" ] || name=$(basename -- "$dir")
hold=0
gov=0
if grep -qi 'candor-gate clause' "$md"; then gov=1; fi

say() { printf '  %-8s %s\n' "$1" "$2"; }
# A governed capability (a candor-gate clause is present) is not an open hold.
# Provenance is exempt: a clause cannot self-certify a signature.
flag() {
  if [ "$gov" -eq 1 ]; then
    say GOVERNED "$1"
  else
    say HOLD "$1"; hold=$((hold+1))
  fi
}

# extract the frontmatter description (folds a >-/| block into one line)
desc=$(awk '
  /^---[[:space:]]*$/ { d++; next }
  d==1 && /^description:/ { ind=1; s=$0; sub(/^description:[[:space:]]*/,"",s);
                           if (s ~ /^[>|][+-]?[[:space:]]*$/) s="";
                           if (s!="") buf=buf s " "; next }
  d==1 && ind==1 && /^[A-Za-z_][A-Za-z0-9_]*:/ { ind=0 }
  d==1 && ind==1 { t=$0; sub(/^[[:space:]]+/,"",t); buf=buf t " " }
  END { gsub(/[[:space:]]+/," ",buf); sub(/[[:space:]]+$/,"",buf); printf "%s", buf }
' "$md")
# strip a matching pair of surrounding YAML quotes so we count the VALUE,
# not the quote delimiters (an inline "..."/'...' description).
case $desc in
  \"*\") desc=${desc#\"}; desc=${desc%\"};;
  \'*\') desc=${desc#\'}; desc=${desc%\'};;
esac
dlen=$(printf '%s' "$desc" | wc -m | tr -d ' ')

printf '== candor-gate: %s ==\n' "$name"

# 1. Provenance — a signature present in the skill dir, else HOLD.
# An archived signature (under .arc/, the record of a retired or BAD one) is not provenance
# (2026-09-28: it had been passing this check for skills whose live signature was retired).
if find "$dir" -name .arc -type d -prune -o \( -name '*.asc' -o -name '.signature.asc' \) -print 2>/dev/null | grep -q .; then
  say PASS "provenance: signature present (verify vs pinned fpr with skill-sign)"
else
  say HOLD "provenance: unsigned — verify against the authors pinned key first"
  hold=$((hold+1))
fi

# 2. Always-on engagement — opt-in required in a foreign shop.
# Match an instruction to fire broadly, not a sentence that forbids it: fold
# case, drop markdown emphasis, then cut negated phrases ("no silent always-on",
# "does not self-engage", "never on every turn") before matching.
eng_text=$(tr '[:upper:]' '[:lower:]' < "$md" | tr -d '*_`' | sed -E \
  's/(^|[^a-z])(no|not|never|without|forbids?|don.t|doesn.t|isn.t|won.t)[[:space:]]+([a-z-]+[[:space:]]+){0,3}(always-on|self-engag[a-z]*|call yourself|(on |at the top of )?(most|every) (substantive )?(prompts?|turns?))//g')
ENG_RE='most prompts|every (substantive )?(prompt|turn)|any time a prompt|self-engag|call yourself'
ENG_RE="$ENG_RE|(run|runs|engage|engages|fire|fires|trigger|triggers|load|loads|stay|stays)( it| this skill)? (an? )?always-on"
ENG_RE="$ENG_RE|(is|be|as) an? always-on"
ENG_RE="$ENG_RE|always-on (skill|mode|engagement|trigger)"
if printf '%s\n' "$eng_text" | grep -Eq "$ENG_RE"; then
  if [ "$travel" -eq 1 ]; then
    say NOTICE "engagement: fires broadly by its own description; it travels with that said (plugin README), and the receiving shop opts in at its door"
  else
    flag "engagement: declares always-on — require OPT-IN per project in this shop"
  fi
else
  say PASS "engagement: not always-on"
fi

# 3. Auto-persist of person-facts — consent-gate before writing third-party data.
if grep -Eqi 'memory[- ]first|persist|biography|genome|for future reference' "$md" \
   && grep -Eqi 'person|people|pet|family|bond|friend|namesake|identity' "$md"; then
  flag "person-data: auto-persists person-facts — consent-gate third-party/family first"
else
  say PASS "person-data: no auto-persist of person-facts"
fi

# 4. Outward egress — consent-gate; forensic/entrusted/third-party never rides it.
# The GPL footer URL (<https://www.gnu.org/licenses/>) and a /uploads path
# segment are not outward paths; drop them before matching.
# 2026-09-28 (the user-freedom LENS): a URL that CREDITS a source (a line with no fetch or send
# verb on it) is not an outward path, and "egress" inside "regression" is not egress. A URL on a
# line that fetches, posts, sends or uploads still holds, as does every tool word below.
egr_text=$(sed -E 's#<?https?://www\.gnu\.org/licenses/?>?##g; s#/uploads?(/|$)#/#g' "$md" | awk '
  { l = tolower($0)
    if (l !~ /(curl|wget|fetch|post|put |get |send|push|submit|upload|request|urllib|http\.client|invoke-webrequest|deploy)/)
      gsub(/<?https?:\/\/[^ )>`"]*>?/, "")
    print }')
if printf '%s\n' "$egr_text" | grep -Eqi 'ollama|llama[- ]bridge|curl|wget|https?://|network call|upload|(^|[^a-z])egress|remote model'; then
  flag "egress: opens an outward path — consent-gate; keep forensic/entrusted/3p off it"
else
  say PASS "egress: no outward data path declared"
fi

# 5. Description length — platform cap; an over-long description will not load right.
if [ "$dlen" -gt "$DESC_LIMIT" ]; then
  say HOLD "description: ${dlen} chars > ${DESC_LIMIT} limit — trim before install"
  hold=$((hold+1))
elif [ "$dlen" -gt $((DESC_LIMIT - 80)) ]; then
  say NOTE "description: ${dlen} chars (near the ${DESC_LIMIT} limit)"
else
  say PASS "description: ${dlen} chars (<= ${DESC_LIMIT})"
fi

# 6. Dangling routes — delegation must not name skills that are not installed.
if grep -Eqi 'rout(e|ing)|delegat|hand it to|pipeline|subsystem' "$md"; then
  say NOTE "routes/delegates — confirm every named sibling skill is installed"
fi

if [ "$hold" -eq 0 ]; then
  printf '== verdict: PASS — clears the gate ==\n'
  exit 0
else
  printf '== verdict: HOLD — %d check(s) need a decision or a consent record ==\n' "$hold"
  exit 1
fi
