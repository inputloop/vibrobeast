#!/bin/sh
# landing.sh -- did the files land on his disk, and only those files? Reads a receipt in the
#   plain `sha256sum` format ("<sha256>  <path>", paths relative to ROOT) and says, one word
#   per file: LANDED (the bytes match), STALE (the file is there, the bytes differ), MISSING.
#   With --dir it also lists every file under that folder the receipt does not name: STRAY.
#   The receipt is the one thing that travels; `sha256sum -c RECEIPT` run from ROOT in his own
#   shell is the same check without this script, and a second reader for it.
#
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
#
# usage: sh landing.sh RECEIPT [ROOT]            check (ROOT defaults to the receipt's folder)
#        sh landing.sh --dir DIR RECEIPT [ROOT]   check, and name files under DIR not in the receipt
#        sh landing.sh --make ROOT FILE...        print receipt lines for FILEs, relative to ROOT
#        sh landing.sh --stage SRC [OUTDIR]       copy SRC to a staged path never used before,
#                                                 OUTDIR/<stem>-<sha8>/<name> (OUTDIR default
#                                                 /mnt/user-data/outputs), and print that path and
#                                                 its sha256: commit from it, then hash the device side
#        sh landing.sh --prove-red                planted cases must come out as planted
# exit:  0 every file LANDED and no STRAY · 1 anything else · 2 usage
# Writes nothing, except --stage (one new folder in OUTDIR) and --prove-red, which works under
#   ${TMPDIR:-/tmp} and cleans up after itself.
# Why --stage: device_commit_files keeps the bytes it first read under a staged path. A staged path
#   reused after an edit landed the old bytes 3 times of 3 on 2026-10-19; a fresh staged path landed
#   the new bytes 6 of 6. The sha8 in the folder name makes each version a new path, and a staged path
#   that is already there is refused, so a name is never reused by accident.
set -u

sha() { sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }

check() { # check RECEIPT ROOT [DIR] -> prints words, returns 0 or 1
  r=$1; root=$2; dir=${3:-}
  [ -f "$r" ] || { printf 'landing: no receipt: %s\n' "$r" >&2; return 2; }
  [ -d "$root" ] || { printf 'landing: no root folder: %s\n' "$root" >&2; return 2; }
  bad=0; n=0; named=$(mktemp "${TMPDIR:-/tmp}/landing.XXXXXX")
  while IFS= read -r line || [ -n "$line" ]; do
    case $line in ''|'#'*) continue ;; esac
    want=${line%% *}; p=${line#*  }; p=${p#\*}
    n=$((n+1)); printf '%s\n' "$p" >> "$named"
    if [ ! -f "$root/$p" ]; then printf 'MISSING  %s\n' "$p"; bad=1
    elif [ "$(sha "$root/$p")" = "$want" ]; then printf 'LANDED   %s\n' "$p"
    else printf 'STALE    %s  (receipt %.12s, disk %.12s)\n' "$p" "$want" "$(sha "$root/$p")"; bad=1; fi
  done < "$r"
  s=0
  if [ -n "$dir" ]; then
    ( cd "$root" && find "$dir" -type f | sed 's#^\./##' | sort ) | while IFS= read -r f; do
      case $f in "${r##*/}"|*/"${r##*/}") continue ;; esac
      grep -qxF "$f" "$named" || printf 'STRAY    %s\n' "$f"
    done > "$named.stray"
    s=$(wc -l < "$named.stray" | tr -d ' '); cat "$named.stray"; [ "$s" = 0 ] || bad=1
    rm -f "$named.stray"
  fi
  rm -f "$named"
  printf -- '-- %s file(s) in the receipt; %s\n' "$n" \
    "$( [ "$bad" = 0 ] && echo 'all LANDED' || echo 'NOT all landed: read the lines above' )$( [ -n "$dir" ] && printf '; %s stray' "$s" )"
  return "$bad"
}

stage() { src=$1; out=${2:-/mnt/user-data/outputs}
  [ -f "$src" ] || { printf 'landing: no such file to stage: %s\n' "$src" >&2; return 2; }
  [ -d "$out" ] || { printf 'landing: no outputs folder: %s\n' "$out" >&2; return 2; }
  h=$(sha "$src"); name=${src##*/}; stem=${name%.*}; [ -n "$stem" ] || stem=$name
  dest=$out/$stem-$(printf '%.8s' "$h")/$name
  if [ -e "$dest" ] || [ -e "${dest%/*}" ]; then
    printf 'landing: %s is already a staged path; a staged path is used once (commit from it as it is, or edit and stage again)\n' "$dest" >&2; return 1; fi
  mkdir -p "${dest%/*}" && cp "$src" "$dest" || return 1
  [ "$(sha "$dest")" = "$h" ] || { printf 'landing: the staged copy does not hash like its source: %s\n' "$dest" >&2; return 1; }
  printf '%s\n%s\n' "$dest" "$h"; }

make_receipt() { root=$1; shift; for f in "$@"; do
    case $f in "$root"/*) rel=${f#"$root"/} ;; *) rel=$f ;; esac
    ( cd "$root" && sha256sum "$rel" ) || return 1; done; }

prove_red() {
  T=$(mktemp -d "${TMPDIR:-/tmp}/landing-red.XXXXXX"); trap 'rm -rf "$T"' EXIT INT TERM
  ok=0; red=0
  case_() { if [ "$2" = "$3" ]; then ok=$((ok+1)); printf '  ok    %s\n' "$1"; else red=$((red+1)); printf '  RED   %s (wanted %s, got %s)\n' "$1" "$2" "$3"; fi; }
  mkdir -p "$T/root/h" && printf 'one\n' > "$T/root/h/a.md" && printf 'two\n' > "$T/root/h/b.md"
  make_receipt "$T/root" "$T/root/h/a.md" "$T/root/h/b.md" > "$T/root/r.sha256"
  check "$T/root/r.sha256" "$T/root" >/dev/null; case_ 'clean: every file LANDED, exit 0' 0 $?
  check "$T/root/r.sha256" "$T/root" "h" >/dev/null; case_ 'clean with --dir: no STRAY, exit 0' 0 $?
  printf 'changed\n' > "$T/root/h/b.md"
  o=$(check "$T/root/r.sha256" "$T/root"); e=$?; case_ 'a changed file exits 1' 1 $e
  case_ 'a changed file reads STALE' yes "$(printf '%s' "$o" | grep -q '^STALE    h/b.md' && echo yes || echo no)"
  printf 'two\n' > "$T/root/h/b.md"; mv "$T/root/h/a.md" "$T/root/h/a.gone"
  o=$(check "$T/root/r.sha256" "$T/root"); case_ 'a missing file reads MISSING' yes "$(printf '%s' "$o" | grep -q '^MISSING  h/a.md' && echo yes || echo no)"
  mv "$T/root/h/a.gone" "$T/root/h/a.md"; printf 'tmp\n' > "$T/root/h/t.12"
  o=$(check "$T/root/r.sha256" "$T/root" "h"); e=$?; case_ 'a stray under --dir exits 1' 1 $e
  case_ 'a stray reads STRAY' yes "$(printf '%s' "$o" | grep -q '^STRAY    h/t.12' && echo yes || echo no)"
  check "$T/root/r.sha256" "$T/root" >/dev/null; case_ 'without --dir a stray is not looked for (exit 0)' 0 $?
  ( cd "$T/root" && sha256sum -c r.sha256 >/dev/null 2>&1 ); case_ 'the receipt is plain sha256sum -c format (second reader agrees)' 0 $?
  mkdir -p "$T/out"; o=$(stage "$T/root/h/a.md" "$T/out"); e=$?; d=$(printf '%s\n' "$o" | sed -n 1p)
  case_ '--stage copies to <stem>-<sha8>/<name> with the same bytes' yes "$( [ $e = 0 ] && cmp -s "$d" "$T/root/h/a.md" && case $d in "$T/out"/a-????????/a.md) echo yes;; *) echo no;; esac || echo no)"
  stage "$T/root/h/a.md" "$T/out" >/dev/null 2>&1; case_ '--stage refuses a staged path that is already there (no reuse)' 1 $?
  printf 'one, edited\n' > "$T/root/h/a.md"; o2=$(stage "$T/root/h/a.md" "$T/out"); d2=$(printf '%s\n' "$o2" | sed -n 1p)
  case_ '--stage after an edit gives a new path' yes "$( [ -n "$d2" ] && [ "$d2" != "$d" ] && echo yes || echo no)"
  printf -- '-- prove-red: %s ok, %s red --\n' "$ok" "$red"; [ "$red" = 0 ]
}

case ${1:-} in
  --prove-red) prove_red; exit $? ;;
  --stage) shift; [ $# -ge 1 ] || { echo 'usage: landing.sh --stage SRC [OUTDIR]' >&2; exit 2; }; stage "$@"; exit $? ;;
  --make) shift; [ $# -ge 2 ] || { echo 'usage: landing.sh --make ROOT FILE...' >&2; exit 2; }; make_receipt "$@"; exit $? ;;
  --dir) [ $# -ge 3 ] || { echo 'usage: landing.sh --dir DIR RECEIPT [ROOT]' >&2; exit 2; }
         d=$2; r=$3; root=${4:-$(dirname "$r")}; check "$r" "$root" "$d"; exit $? ;;
  -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
  '') sed -n '2,26p' "$0" >&2; exit 2 ;;
  *) r=$1; root=${2:-$(dirname "$r")}; check "$r" "$root"; exit $? ;;
esac
