#!/bin/sh
# bind.sh -- which key you keep answers to a name a program asks for.  The pocket binder.
#
# Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors.  GPL-3.0-or-later.
# Mentat (for Corwin; claude-opus-5-5)
#
# A C4 form in your pocket: a word file (one word, an ARRAY of lines, each a SCALAR name with #TAGs
# saying what it means) and a register (the keys you keep, each with its kind and what it is for).
# A name is balanced against both: listed names take their line's tags; a name not listed is split
# at _ and each piece read the same way, a piece found nowhere standing for itself.  Each key
# scores: a name in its BINDS wins outright (100), its KIND among the tags 1, each FOR tag 2.
#   BOUND  a BINDS hit, or the best score reaches a service      use it
#   GUESS  only the kind matched                                  ask first
#   TIE    two keys share the best score                          ask which; never pick
#   NONE   no key answers                                         say so
# This is the second reader of polygram/mcp/keys.py (the servers' binder); tests/kb1nd-spec.rb
# holds both to one spec.  It reads no secret: a register names where a key lives, never the key.
#
# usage: bind.sh [-l WORDFILE] [-r REGISTER] [--tsv] NAME...
#   -l   the word file (default: ../fixtures/secret.md beside this script)
#   -r   the register, tab-separated NAME KIND SOURCE BINDS FOR RUN USAGE (default: none);
#        the settings page's keys come from the environment as in keys.py (VIBROBEAST_API_TOKEN ...)
#   --tsv  NAME VERDICT KEY SCORE, one line each, for comparing readers; default is words
# exit 0 every name answered (BOUND), 1 some name needs asking (GUESS, TIE, NONE), 2 usage
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
lex=$here/../fixtures/secret.md; reg=/dev/null; tsv=0
while [ $# -gt 0 ]; do
  case $1 in
    -l) lex=$2; shift 2 ;;
    -r) reg=$2; shift 2 ;;
    --tsv) tsv=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    --) shift; break ;;
    -*) echo "bind.sh: unknown option $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
[ $# -ge 1 ] || { echo "usage: bind.sh [-l WORDFILE] [-r REGISTER] [--tsv] NAME..." >&2; exit 2; }
[ -r "$lex" ] || { echo "bind.sh: cannot read the word file $lex" >&2; exit 2; }
names=$*
awk -v names="$names" -v tsv="$tsv" -v F2="$reg" '
function addtags(n, rest,   t) {
  while (match(rest, /#[a-z0-9][a-z0-9-]*/)) {
    t = substr(rest, RSTART + 1, RLENGTH - 1); LT[n, t] = 1
    if (!((n, "") in LT)) LT[n, ""] = 1
    if (!(n SUBSEP t in SEEN)) { SEEN[n SUBSEP t] = 1; LTL[n] = LTL[n] " " t }
    rest = substr(rest, RSTART + RLENGTH)
  }
  if (!(n in LTL)) LTL[n] = ""
}
function longrun(s,   i, c, run) {          # a run of 36+ token characters
  run = 0
  for (i = 1; i <= length(s); i++) {
    c = substr(s, i, 1)
    if (c ~ /[A-Za-z0-9+\/=_-]/) { if (++run >= 36) return 1 } else run = 0
  }
  return 0
}
function alnumafter(s, pre, n,   i, j) {    # pre followed by n alphanumerics
  i = index(s, pre); if (!i) return 0
  for (j = i + length(pre); j < i + length(pre) + n; j++) if (substr(s, j, 1) !~ /[A-Za-z0-9]/) return 0
  return 1
}
function secretish(s) {
  return (s ~ /ghp_|gho_|ghs_|github_pat_|glpat-|pypi-Ag|-----BEGIN/ || alnumafter(s, "npm_", 20) \
          || alnumafter(s, "sk-", 16) || longrun(s))
}
function ok(n, k, src, b, f, r, u,   cells, i) {
  if (n == "") return 0
  if (k !~ /^(token|ssh-key|password|-)$/) return 0
  if (k != "-" && src !~ /^(field:(api_token|ssh_key|gw_password)|env:[A-Za-z_][A-Za-z0-9_]*|file:.+)$/) return 0
  cells[1] = n; cells[2] = k; cells[3] = src; cells[4] = b; cells[5] = f; cells[6] = r
  for (i = 1; i <= 6; i++) if (secretish(cells[i]) && !(i == 3 && src ~ /^file:/)) return 0
  if (u ~ /ghp_|github_pat_|glpat-|-----BEGIN/) return 0
  return 1
}
function keep(n, k, b, f) {
  if (k == "-") { delete KIND[n]; return }
  if (!(n in KIND)) ORDER[++NK] = n
  KIND[n] = k; BINDS[n] = b; FOR[n] = f
}
function trim(s) { gsub(/^[ \t]+|[ \t\r]+$/, "", s); return s }
FNR == 1 { file++ }
file == 1 && /^- `[^`]+`/ { n = $0; sub(/^- `/, "", n); rest = n; sub(/`.*/, "", n); sub(/^[^`]*`/, "", rest); addtags(n, rest); next }
file == 1 { next }
file == 2 {
  if ($0 ~ /^#/ || $0 ~ /^[ \t]*$/) next
  nf = split($0, c, "\t"); for (i = nf + 1; i <= 7; i++) c[i] = ""
  for (i = 1; i <= 7; i++) c[i] = trim(c[i])
  if (ok(c[1], c[2], c[3], c[4], c[5], c[6], c[7])) keep(c[1], c[2], c[4], c[5])
  next
}
END {
  # the settings page, as keys.settings_rows: a register row of the same name wins
  if (ENVIRON["VIBROBEAST_API_TOKEN"] != "" && !("api" in KIND)) keep2("api", "token", "", ENVIRON["VIBROBEAST_API_TOKEN_FOR"])
  if (ENVIRON["VIBROBEAST_SSH_KEY"] != "" && !("ssh" in KIND)) keep2("ssh", "ssh-key", "", "ssh git " ENVIRON["VIBROBEAST_SSH_KEY_FOR"])
  if (ENVIRON["GW_PASSWORD"] != "" && !("gw" in KIND)) keep2("gw", "password", "", "ghostwheel")
  nq = split(names, Q, " "); bad = 0
  for (q = 1; q <= nq; q++) { v = verdict(Q[q]); if (v != "BOUND") bad = 1 }
  exit bad
}
function keep2(n, k, b, f) { if (!(n in KIND)) ORDER[++NK] = n; KIND[n] = k; BINDS[n] = b; FOR[n] = f }
function tagsof(name,   np, p, i, piece, hit) {
  delete T
  if (name in LTL) { np = split(LTL[name], p, " "); for (i = 1; i <= np; i++) T[p[i]] = 1; READ = name ": listed"; return }
  np = split(name, P, "_"); READ = ""
  for (i = 1; i <= np; i++) {
    piece = P[i]; if (piece == "") continue
    hit = (piece in LTL) ? piece : ((toupper(piece) in LTL) ? toupper(piece) : "")
    if (hit != "") { split(LTL[hit], p, " "); for (j in p) T[p[j]] = 1; READ = READ piece ": listed; " }
    else { T[tolower(piece)] = 1; READ = READ piece ": stands for itself; " }
  }
}
function inlist(x, lst,   a, n, i) { n = split(lst, a, /[ \t,;]+/); for (i = 1; i <= n; i++) if (a[i] == x) return 1; return 0 }
function verdict(name,   i, k, s, nf, f, j, best, nbest, bk, out) {
  tagsof(name)
  best = 0; nbest = 0; bk = ""
  for (i = 1; i <= NK; i++) {
    k = ORDER[i]; if (!(k in KIND)) continue
    if (inlist(name, BINDS[k])) s = 100
    else {
      s = (KIND[k] in T) ? 1 : 0
      nf = split(FOR[k], f, /[ \t,;]+/); delete DUP
      for (j = 1; j <= nf; j++) if (f[j] != "" && (f[j] in T) && !(f[j] in DUP)) { DUP[f[j]] = 1; s += 2 }
    }
    if (s == 0) continue
    if (s > best) { best = s; nbest = 1; bk = k }
    else if (s == best) { nbest++; if (k < bk) bk = k }
  }
  if (best == 0) out = "NONE"
  else if (nbest > 1) out = "TIE"
  else if (best >= 2) out = "BOUND"
  else out = "GUESS"
  if (tsv) printf "%s\t%s\t%s\t%d\n", name, out, (out == "BOUND" || out == "GUESS") ? bk : "-", best
  else if (out == "BOUND") printf "%s is answered by the key %s (score %d; %s)\n", name, bk, best, READ
  else if (out == "GUESS") printf "%s might be the key %s, but only its kind matched: ask first\n", name, bk
  else if (out == "TIE") printf "%s could be more than one key you keep: ask which, or add the name to one key'"'"'s BINDS\n", name
  else printf "no key you keep answers to %s\n", name
  return out
}
' "$lex" "$reg"
