#!/bin/sh
# polygram -- witness signature: WHICH witness dissented, not merely that one did.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPLv3+.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# usage:  sh bin/witness-signature.sh [--prove-red]
#
# Three witnesses draw three DIFFERENT facts from one set -- the frozen notes
# under tests/fixtures/frozen -- and the PATTERN of who dissents names the
# defect.  A single red light says "something is wrong".  A signature says
# which of three things moved, and that difference is the whole point.
#
#   MEANING         tests/test_frozen_witness.py  +  ..._v3.py
#                   the current parser vs the hand-written EXPECTATIONS.md
#   BYTES-vs-HUMAN  bin/frozen-check.awk
#                   the frozen front matter vs EXPECTATIONS.md, no Python
#   CHAIN           bin/dl2-verify.sh
#                   C1-C4: are these bytes the bytes that were written
#
# Each witness now reads BOTH name eras -- tests/fixtures/frozen (v2, 42-char
# names) and tests/fixtures/frozen-v3 (v3, 25-char names, plus one mixed-era
# seam). The signature does not distinguish them, on purpose: "the code moved"
# is the same finding whichever era exposed it, and the per-era detail is in
# whichever reader's output you go and read.
#
#   meaning  bytes  chain   what moved
#   -------  -----  -----   ----------------------------------------------
#   GREEN    GREEN  GREEN   nothing
#   RED      GREEN  GREEN   THE CODE.  The parser no longer reads what the
#                           bytes say.  This is the 2026-09-15 ghost: a
#                           front-matter key renamed, 207 tests green, the
#                           compaction queue inverted.
#   RED      RED    GREEN   THE HUMAN STATEMENT.  EXPECTATIONS.md was edited
#                           and the bytes were not.  Usually somebody
#                           "updated the expected value" -- which is the one
#                           move that file forbids.
#   RED      RED    RED     THE FROZEN BYTES.  Somebody edited a fixture.
#                           Restore it; it is a record, not a workspace.
#   GREEN    RED    *       The two readers of one file disagree.  Neither
#                           result is evidence. Read frozen-check.awk's
#                           output before touching anything.
#
# Corwin, 2026-09-15: "It isn't enough to have a second reader: we have to
# draw/consider different data from within the same set and reach the mutually
# supporting conclusion that information begins to show a signal strength."

# TWO ERAS, ONE SIGNATURE (spec v3, 2026-09-15).  The generation filename lost
# its timestamp and an archive-only store cannot migrate, so the tree holds two
# name shapes forever.  Both are witnessed here, together, because a signature
# that covered only one era would go GREEN GREEN GREEN while half the archive
# had stopped being read -- and an unread file reports nothing, which is the
# exact failure mode this table exists to name.
set -u
here=$(dirname "$0")/..
cd "$here" || exit 2
E=tests/fixtures/frozen/EXPECTATIONS.md
E3=tests/fixtures/frozen-v3/EXPECTATIONS.md
[ -f "$E" ]  || { echo "no frozen fixtures at $E" >&2; exit 2; }
[ -f "$E3" ] || { echo "no frozen v3 fixtures at $E3" >&2; exit 2; }

# The v3 mixed-era seam holds two generations that are BYTE COPIES of files
# under tests/fixtures/frozen/.  Their meaning is stated once, in the v2
# EXPECTATIONS.md; restating it beside the copies would create a second human
# record of one fact, and two records that agree because one was copied from
# the other teach nothing.  So hand the bytes reader exactly the notes its
# expectations speak about: everything under frozen-v3/ whose basename does
# not also exist under frozen/.
v3_stated() {
    for f in tests/fixtures/frozen-v3/*/g*.md; do
        b=${f##*/}
        dup=0
        for o in tests/fixtures/frozen/*/g*.md; do
            [ "${o##*/}" = "$b" ] && dup=1
        done
        [ "$dup" -eq 0 ] && printf '%s\n' "$f"
    done
}

run_meaning() {
    python3 -m unittest tests.test_frozen_witness    >/dev/null 2>&1 || return 1
    python3 -m unittest tests.test_frozen_witness_v3 >/dev/null 2>&1 || return 1
    return 0
}
run_bytes()   {
    awk -f bin/frozen-check.awk "$E" tests/fixtures/frozen/*/g*.md \
        >/dev/null 2>&1 || return 1
    # shellcheck disable=SC2046  # the file list is newline-free by construction
    awk -f bin/frozen-check.awk "$E3" $(v3_stated) >/dev/null 2>&1 || return 1
    return 0
}
run_chain()   {
    rc=0
    for d in tests/fixtures/frozen/*/ tests/fixtures/frozen-v3/*/; do
        sh bin/dl2-verify.sh "$d" >/dev/null 2>&1 || rc=1
    done
    return $rc
}

verdict() { if "$1"; then echo GREEN; else echo RED; fi; }

if [ "${1-}" = "--prove-red" ]; then
    # A signature table that cannot produce a RED tells you nothing. Corrupt a
    # COPY of the expectations and require the bytes witness to dissent.
    t=$(mktemp -d) || exit 2
    trap 'rm -rf "$t"' EXIT
    sed 's/unit                 = 16/unit                 = 8/' "$E" > "$t/E.md"
    if awk -f bin/frozen-check.awk "$t/E.md" tests/fixtures/frozen/*/g*.md >/dev/null 2>&1; then
        echo "prove-red FAIL: the bytes witness accepted a false expectation" >&2
        exit 1
    fi
    # And again for the v3 era. One era proving red says nothing about the
    # other: the v3 statements are read through a header pattern that was
    # WIDENED for this change, and a widening that silently stopped matching
    # would leave every v3 fact unchecked while the run still said OK.
    sed 's/unit                 = 9/unit                 = 4/' "$E3" > "$t/E3.md"
    # shellcheck disable=SC2046
    if awk -f bin/frozen-check.awk "$t/E3.md" $(v3_stated) >/dev/null 2>&1; then
        echo "prove-red FAIL: the bytes witness accepted a false v3 expectation" >&2
        exit 1
    fi
    echo "prove-red PASS: the bytes witness dissents when the human statement is wrong, in both name eras"
fi

m=$(verdict run_meaning)
b=$(verdict run_bytes)
c=$(verdict run_chain)

printf 'meaning=%s  bytes-vs-human=%s  chain=%s\n' "$m" "$b" "$c"

case "$m$b$c" in
  GREENGREENGREEN) echo "nothing moved."; exit 0 ;;
  REDGREENGREEN)   echo "THE CODE moved. The parser no longer reads what the frozen bytes say."
                   echo "Do NOT re-emit the fixtures. Fix the parser, or freeze a new generation"
                   echo "beside the old one with a migration note."; exit 1 ;;
  REDREDGREEN)     echo "THE HUMAN STATEMENT moved. EXPECTATIONS.md disagrees with bytes that are"
                   echo "still intact. If somebody 'updated the expected value', revert that."; exit 1 ;;
  REDREDRED)       echo "THE FROZEN BYTES were edited. A fixture is a record, not a workspace."
                   echo "Restore it from version control."; exit 1 ;;
  GREENRED*)       echo "The two readers of one file disagree and NEITHER is evidence."
                   echo "Read bin/frozen-check.awk's output before changing anything."; exit 1 ;;
  *)               echo "unclassified signature -- report it, do not guess."; exit 1 ;;
esac
