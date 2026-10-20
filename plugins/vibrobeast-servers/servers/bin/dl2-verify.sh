#!/bin/sh
# dl2-verify.sh -- the chain check, implementation B (POSIX sh).
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# Written from polygram/mcp/chainspec.py's SPEC TEXT, not from the Python or
# Perl implementation.  That is the thing that makes these independent: an
# earlier pair was in two languages and still shared one unstated assumption --
# that "generation 1" is whichever file SAYS gen: 1 -- so a hand-appended file
# re-rooted a real chain and both readers said OK.  The spec is now prose, and
# each implementation is written from the prose.
#
# Checks, per file i of N ordered by the integer in the name:
#   C1 position  gen: == i
#   C2 name      the integer in g<digits> == gen:
#   C3 self      the hex16 in the name == first 16 of sha256(WHOLE file)
#   C4 link      prev: empty for i=1, else sha256:<sha256 of file i-1's bytes>
#
# usage:  sh bin/dl2-verify.sh SEAM_DIR
#         sh bin/dl2-verify.sh --prove-red
#
# output, one line, tab-separated:
#   OK<TAB>N
#   BROKEN<TAB>N<TAB>FILE<TAB>CHECK<TAB>WHY
# exit: 0 holds · 1 broken · 2 usage/environment.

set -eu

die() { printf '%s\n' "$*" >&2; exit 2; }
have() { command -v "$1" >/dev/null 2>&1; }

if have sha256sum; then _H() { sha256sum | cut -d' ' -f1; }
elif have shasum;  then _H() { shasum -a 256 | cut -d' ' -f1; }
else die "dl2-verify: need sha256sum or shasum"; fi

# sha256 of a whole file's bytes.  No translation, no decoding.
hash_file() { _H < "$1"; }

# One front-matter value.  First occurrence wins; key and value stripped.
fm() {
  awk -v want="$2" '
    NR==1 && $0 ~ /^---[[:space:]]*$/ { inh=1; next }
    inh && $0 ~ /^---[[:space:]]*$/ { exit }
    inh {
      i = index($0, ":")
      if (i > 0) {
        k = substr($0, 1, i-1); v = substr($0, i+1)
        gsub(/^[ \t]+|[ \t]+$/, "", k); gsub(/^[ \t]+|[ \t\r]+$/, "", v)
        if (k == want && !seen) { print v; seen=1; exit }
      }
    }
  ' "$1"
}

broken() { printf 'BROKEN\t%s\t%s\t%s\t%s\n' "$2" "$1" "$3" "$4"; exit 1; }

# Decimal value of a digit string, leading zeros and all. Never $(( )).
strip0() {
  v=${1%%-*}
  while [ "${#v}" -gt 1 ] && [ "${v#0}" != "$v" ]; do v=${v#0}; done
  printf '%s' "$v"
}

verify_dir() {
  dir=$1
  [ -d "$dir" ] || die "not a directory: $dir"
  # A newline inside the path would split the newline-delimited file list and
  # produce a confident BROKEN about files that do not exist. Refuse loudly
  # rather than answer wrongly: a wrong verdict is worse than no verdict.
  # A literal newline in a variable: $(printf '\n') is EMPTY, because command
  # substitution strips trailing newlines -- so the obvious spelling of this
  # guard matched every path and refused everything.
  NL='
'
  case $dir in
    *"$NL"*) die "dl2-verify: path contains a newline; this reader cannot address it safely" ;;
  esac

  # Generation files only: regular files whose NAME matches the shape.  A
  # directory or a symlink named g0009-x.md is not a generation -- feeding one
  # to awk used to abort this script while the Python reader skipped it.
  # Sorted by the integer in the name, so g10000 follows g9999.
  # A newline-delimited list, read with `while IFS= read -r`. NEVER
  # `for f in $list`: that word-splits on spaces, and on the stated target
  # platform the default seat lives under C:\Users\First Last\..., where the
  # unquoted version split one path into two and reported a confident BROKEN
  # about a file called "First".
  tmplist=$(
    for f in "$dir"/g*.md; do
      [ -e "$f" ] || continue
      [ -f "$f" ] || continue
      [ -L "$f" ] && continue
      b=${f##*/}
      # The FULL shape, BOTH ERAS (spec v3, N1):
      #   v2  g<digits>-<[0-9TZ]+>-<16 lowercase hex>.md   three segments
      #   v3  g<digits>-<16 lowercase hex>.md              two segments
      # A reader that takes only one of them loses a whole era of the archive
      # SILENTLY -- an unmatched name is skipped, and a skipped seam looks
      # exactly like an empty one. That is the "lose the files" failure and it
      # is why N1 is the first name rule.
      #
      # The loose `g*-*-*.md` glob once accepted uppercase hex, a 15- or
      # 17-character tail, letters in the stamp and four segments -- all of
      # which the Python and Perl readers reject, so one planted file made
      # `seat_chain` flip between OK and BROKEN on successive calls. Same hole
      # the \d-vs-[0-9] fix closed on the Python side. Keep it closed: every
      # segment is still checked below, era by era.
      #
      # ORDER MATTERS. `g*-*.md` also matches a three-segment name, because a
      # glob `*` happily eats a hyphen. Test the longer shape first.
      case $b in
        g*-*-*-*) continue ;;       # four or more segments: not a generation
        g*-*-*.md) era=2 ;;
        g*-*.md)   era=3 ;;
        *) continue ;;
      esac
      num=${b#g}; num=${num%%-*}
      case $num in (*[!0-9]*|'') continue ;; esac
      # N2: the handle is the LAST segment, in both eras. Parsing from the end
      # is what makes two shapes cost one line instead of two code paths.
      tail=${b%.md}; tail=${tail##*-}
      case $tail in
        ????????????????) ;;
        *) continue ;;
      esac
      case $tail in (*[!0-9a-f]*) continue ;; esac
      if [ "$era" -eq 2 ]; then
        mid=${b%.md}; mid=${mid#*-}; mid=${mid%-*}
        case $mid in ('' | *[!0-9TZ]*) continue ;; esac
        # N3: the stamp segment's SHAPE is checked so the three readers agree
        # on which files exist. Its VALUE is checked by nothing, here or
        # anywhere, and must stay that way -- no rule ever constrained it, and
        # a rule added now would condemn archived bytes that broke none.
      fi
      printf '%s\t%s\n' "$(strip0 "$num")" "$f"
    done | sort -n -k1,1 | cut -f2-
  )

  n=$(printf '%s' "$tmplist" | grep -c . || true)
  if [ "${n:-0}" -eq 0 ]; then printf 'OK\t0\n'; return 0; fi

  i=0
  prev=''
  printf '%s\n' "$tmplist" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    i=$((i+1))
    b=${f##*/}

    # C0 shape -- front matter must open and close.
    head1=$(head -n1 "$f" 2>/dev/null || true)
    case $head1 in
      ---*) ;;
      *) broken "$b" "$n" "C0 shape" "note has no front matter" ;;
    esac

    gen=$(fm "$f" gen)
    # C1 position -- gen must be an integer equal to i.
    case $gen in
      ''|*[!0-9]*) broken "$b" "$n" "C1 position" "gen is not an integer: $gen" ;;
    esac
    # Strip leading zeros DECIMALLY before comparing. POSIX $(( )) reads a
    # leading zero as octal, so $((0008)) is "Illegal number" and this whole
    # reader exited 2 at generation 8 -- which the Verifier swallowed as an
    # exception rather than a disagreement, silently dropping the house from
    # three readers to two on every seam deeper than seven. $((0010)) was
    # worse: it succeeded, as 8.
    gen=$(strip0 "$gen")
    if [ "$gen" -ne "$i" ]; then
      broken "$b" "$n" "C1 position" "gen says $gen but this is file $i of $n"
    fi

    # C2 name -- the integer in the filename must equal gen.
    num=$(strip0 "${b#g}" )
    if [ "$num" -ne "$gen" ]; then
      broken "$b" "$n" "C2 name" "filename says g$num but gen says $gen"
    fi

    # C3 self -- the hex16 in the name must be the WHOLE FILE's digest
    # (spec v2). No awk, no parsing: the one check a parser cannot confuse.
    # N2: last segment, both eras. This was `rest=${b#*-}; want=${rest#*-}`,
    # which counts TWO segments from the front and therefore read a v3 name's
    # handle as the empty string -- every v3 file would have failed C3 with a
    # confident, wrong message. Parsing from the end is era-blind.
    want=${b%.md}; want=${want##*-}
    got=$(printf '%.16s' "$(hash_file "$f")")
    if [ "$want" != "$got" ]; then
      broken "$b" "$n" "C3 self" \
        "name carries $want but the file hashes to $got -- this generation was changed after it was written"
    fi

    # C4 link.
    rec=$(fm "$f" prev)
    if [ "$i" -eq 1 ]; then
      [ -z "$rec" ] || broken "$b" "$n" "C4 link" "generation 1 records a prev"
    else
      case $rec in
        sha256:*) ;;
        *) broken "$b" "$n" "C4 link" "prev is not a sha256: reference: $rec" ;;
      esac
      rec=${rec#sha256:}
      if [ "$rec" != "$prev" ]; then
        broken "$b" "$n" "C4 link" \
          "recorded $(printf '%.16s' "$rec") != actual $(printf '%.16s' "$prev")"
      fi
    fi
    prev=$(hash_file "$f")
    if [ "$i" -eq "$n" ]; then printf 'OK\t%s\n' "$n"; fi
  done
  # The while loop runs in a subshell (it is the right-hand side of a pipe),
  # so `broken`'s `exit 1` ends the subshell and its verdict is on stdout.
  # Propagate that exit status rather than returning the pipeline's default.
  return $?
}

prove_red() {
  t=$(mktemp -d) || die "mktemp failed"
  trap 'rm -rf "$t"' EXIT
  fail=0
  say() { if [ "$3" = "$2" ]; then printf '  PASS  %s\n' "$1"
          else printf '  FAIL  %s (wanted %s, got %s)\n' "$1" "$2" "$3"; fail=1; fi }

  # Run verify_dir in a subshell so its exit 1 never reaches this script.
  run() { ( verify_dir "$1" ) 2>&1 || true; }

  # mkgen DIR GEN PREV BODY [ERA] -- name from the WHOLE FILE (C3).
  # ERA defaults to 2: every existing case below keeps writing the ARCHIVE
  # shape on purpose. A suite that stopped writing v2 would stop witnessing
  # the files that are already on disk and can never be renamed.
  mkgen() {
    era=${5:-2}
    txt=$(printf -- '---\nseam: red\ngen: %s\nprev: %s\n---\n%s' "$2" "$3" "$4")
    bh=$(printf '%s\n' "$txt" | _H); bh=$(printf '%.16s' "$bh")
    if [ "$era" -eq 2 ]; then
      nm=$(printf 'g%04d-2026091%sT000000Z-%s.md' "$2" "$(( $2 % 10 ))" "$bh")
    else
      nm=$(printf 'g%04d-%s.md' "$2" "$bh")
    fi
    printf '%s\n' "$txt" > "$1/$nm"
  }
  mkchain() { # mkchain NAME [ERA1] [ERA2] -> a good two-generation chain
    d=$t/$1; mkdir -p "$d"
    mkgen "$d" 1 "" "one" "${2:-2}"
    h1=$(hash_file "$(ls "$d"/g0001-*)")
    mkgen "$d" 2 "sha256:$h1" "two" "${3:-2}"
    printf '%s' "$d"
  }

  printf 'prove-red: every check fired by a chain built to break it\n'

  d=$(mkchain a)
  say "intact chain" "OK" "$(run "$d" | cut -f1)"

  d=$(mkchain b)
  printf 'x' >> "$(ls "$d"/g0001-*)"
  say "C3 edit to gen 1" "C3 self" "$(run "$d" | cut -f4)"

  d=$(mkchain b4)
  g1=$(ls "$d"/g0001-*)
  sed 's/^seam: red$/seam: rebranded/' "$g1" > "$g1.new" && mv "$g1.new" "$g1"
  # In spec v2 a front-matter edit is caught by C3 as well, because C3
  # hashes the whole file. C4 still earns its place: it catches a file
  # substituted WHOLESALE, name and all, which C3 cannot see.
  say "front-matter edit to gen 1" "C3 self" "$(run "$d" | cut -f4)"

  d=$(mkchain c)
  printf 'tampered' >> "$(ls "$d"/g0002-*)"
  say "C3 edit to the head" "C3 self" "$(run "$d" | cut -f4)"

  d=$(mkchain e)
  bh=$(printf '%s' "ZERO" | _H); bh=$(printf '%.16s' "$bh")
  printf -- '---\nseam: red\ngen: 1\nprev:\n---\nZERO\n' \
    > "$d/g0003-20260914T999999Z-$bh.md"
  say "C1 forged gen 1" "C1 position" "$(run "$d" | cut -f4)"

  d=$(mkchain f)
  g2=$(ls "$d"/g0002-*)
  mv "$g2" "$(printf '%s' "$g2" | sed 's/g0002/g0007/')"
  # Renaming g0002 to g0007 leaves C1 satisfied (it is still file 2 of 2
  # and still says gen: 2) -- C2 is the check that notices, which is why
  # C2 exists separately. The first expectation written here said C1, and
  # the spec was right and the expectation was wrong.
  say "C2 renamed file" "C2 name" "$(run "$d" | cut -f4)"

  d=$(mkchain g)
  mkdir "$d/g0009-20260914T000000Z-0123456789abcdef.md"
  say "directory ignored" "OK" "$(run "$d" | cut -f1)"

  # C4 with the body AND the name left intact: swap generation 2 for a whole
  # file that is internally consistent but is not the one gen 1 points at.
  d=$(mkchain h)
  rm -f "$d"/g0002-*
  mkgen "$d" 2 "sha256:0000000000000000000000000000000000000000000000000000000000000000" "two"
  say "C4 wholesale substitution" "C4 link" "$(run "$d" | cut -f4)"

  # ---- spec v3 names, and the mixed seam -----------------------------
  # N1 both shapes, N4 mixed seams. These are the cases whose failure mode is
  # SILENCE: a reader that does not match a name does not see the file, and a
  # seam nobody can see reads exactly like a seam with nothing in it. That is
  # "lose the files" and it is the thing this change must not buy.
  d=$(mkchain v3 3 3)
  say "v3 chain holds" "OK" "$(run "$d" | cut -f1)"

  d=$(mkchain mixed 2 3)
  say "mixed seam: v2 then v3" "OK" "$(run "$d" | cut -f1)"

  d=$(mkchain mixedback 3 2)
  say "mixed seam: v3 then v2" "OK" "$(run "$d" | cut -f1)"

  # C3 must still fire on a v3 name: the name got shorter, the check did not.
  d=$(mkchain v3c3 3 3)
  printf 'tampered' >> "$(ls "$d"/g0002-*)"
  say "C3 edit to a v3 head" "C3 self" "$(run "$d" | cut -f4)"

  # A v3 handle of sixteen DECIMAL digits -- the one shape where a stamp-first
  # parse could swallow the handle. If the name failed to parse there would be
  # no generation files at all and the answer would be OK with a count of 0;
  # C3 firing proves the file was SEEN and its handle read from the end.
  d=$t/v3digits; mkdir -p "$d"
  printf -- '---\nseam: red\ngen: 1\nprev:\n---\nall-digits\n' \
    > "$d/g0001-0123456789012345.md"
  say "v3 handle of all digits parses as a handle" "C3 self" "$(run "$d" | cut -f4)"

  printf '\n'
  if [ "$fail" -eq 0 ]; then printf 'prove-red PASS\n'; return 0
  else printf 'prove-red FAILED\n'; return 1; fi
}

case ${1:-} in
  --prove-red) prove_red ;;
  --spec) printf 'chainspec v3: C1 position, C2 name, C3 self, C4 link; names N1-N5 (g<gen>-<hex16>.md, and g<gen>-<stamp>-<hex16>.md forever)\n' ;;
  -h|--help|'') printf 'usage: sh %s SEAM_DIR | --prove-red | --spec\n' "$0"; exit 2 ;;
  *) verify_dir "$1" ;;
esac
