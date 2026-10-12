#!/usr/bin/awk -f
# polygram -- the frozen-note witness, second reader.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPLv3+.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# Usage: awk -f bin/frozen-check.awk EXPECTATIONS.md FROZEN_NOTE...
#
# WHY THIS IS NOT A TRANSLATION OF THE PYTHON.  It reads two files that already
# exist -- the hand-written EXPECTATIONS.md and the frozen note bytes -- and
# imports nothing from polygram.  If it were derived from dl2.py it would
# inherit dl2.py's beliefs, which is precisely the failure it is here to catch:
# on 2026-09-15 a renamed front-matter key passed 207 tests and three chain
# verifiers while inverting the compaction queue, because every one of those
# readers computed the same function over the same bytes.
#
# Corwin, the same day: "It isn't enough to have a second reader: we have to
# draw/consider different data from within the same set and reach the mutually
# supporting conclusion that information begins to show a signal strength."
#
# So this reader draws a DIFFERENT fact: it takes the human's statement of
# meaning as its input and asks the bytes whether they say that. The Python
# witness goes the other way -- bytes first, meaning checked after. Two
# directions across one set.
#
# WHAT IT CHECKS, F1..F4:
#   F1  every `key = value` stated for a note is present in that note's front
#       matter with that value
#   F2  `(empty)` in the expectations means the field is present and empty,
#       NOT absent -- an absent field is a different fact and must not pass
#   F3  the derived rows -- triggers.count, prev.hex16, filename.hex16,
#       body.first-word -- recomputed here, never copied
#   F4  every note handed to it appears in the expectations, and vice versa

BEGIN { FS = "\n"; phase = "expect"; bad = 0; notes = 0 }

FNR == 1 && FILENAME ~ /EXPECTATIONS\.md$/ { phase = "expect"; cur = "" }
FNR == 1 && FILENAME !~ /EXPECTATIONS\.md$/ {
    phase = "note"; notes++
    nf = FILENAME
    sub(/.*\//, "", nf)
    nd = FILENAME
    sub("/" nf "$", "", nd); sub(/.*\//, "", nd)
    key = nd "/" nf
    seen_note[key] = 1
    in_fm = 0; fm_done = 0; body_first = ""
}

phase == "expect" {
    # BOTH NAME ERAS (spec v3 N1): the stamp segment is optional.
    #   v2  ## seam / g0001-20260915T120000Z-<hex16>.md
    #   v3  ## seam / g0001-<hex16>.md
    # A header this reader does not match is a header it silently ignores, so
    # narrowing it would make every v3 statement unread while the run still
    # said OK -- a witness that has quietly stopped witnessing.
    if ($0 ~ /^## [a-z0-9-]+ \/ g[0-9]+(-[0-9TZ]+)?-[0-9a-f]{16}\.md$/) {
        cur = $0; sub(/^## /, "", cur); gsub(/ /, "", cur)
        seen_expect[cur] = 1
        next
    }
    if (cur != "" && $0 ~ /^    [a-z0-9.-]+ +=/) {
        k = $0; sub(/^    /, "", k); sub(/ *=.*/, "", k)
        v = $0; sub(/^    [a-z0-9.-]+ +=  ?/, "", v)
        gsub(/^[ \t]+|[ \t]+$/, "", v)
        want[cur, k] = v
        want_keys[cur] = want_keys[cur] " " k
    }
    next
}

# ---- note files -------------------------------------------------------
phase == "note" {
    if (FNR == 1) { if ($0 == "---") in_fm = 1; next }
    if (in_fm && $0 == "---") { in_fm = 0; fm_done = 1; next }
    if (in_fm) {
        k = $0; sub(/:.*/, "", k)
        v = $0; sub(/^[^:]*: ?/, "", v)
        gsub(/[ \t]+$/, "", v)
        have[key, k] = v
        present[key, k] = 1
        next
    }
    if (fm_done && body_first == "" && $0 ~ /[^ \t]/) {
        body_first = $0
        sub(/^[ \t]*/, "", body_first); sub(/[ \t].*/, "", body_first)
        have[key, "body.first-word"] = body_first
        present[key, "body.first-word"] = 1
    }
}

function fail(k, what) { bad++; printf "%s: %s\n", k, what > "/dev/stderr" }

END {
    # F3: recompute the derived rows rather than copying them.
    for (k in seen_note) {
        n = split(have[k, "triggers"], parts, ",")
        cnt = 0
        for (i = 1; i <= n; i++) if (parts[i] ~ /[^ \t]/) cnt++
        have[k, "triggers.count"] = cnt; present[k, "triggers.count"] = 1
        first = parts[1]; gsub(/^[ \t]+|[ \t]+$/, "", first)
        have[k, "triggers.first"] = (cnt ? first : ""); present[k, "triggers.first"] = 1

        p = have[k, "prev"]; sub(/^sha256:/, "", p)
        have[k, "prev.hex16"] = substr(p, 1, 16); present[k, "prev.hex16"] = 1

        f = k; sub(/.*\//, "", f)
        if (match(f, /-[0-9a-f]{16}\.md$/))
            have[k, "filename.hex16"] = substr(f, RSTART + 1, 16)
        present[k, "filename.hex16"] = 1
    }

    # F4: the two sets must be the same set.
    for (k in seen_expect)
        if (!(k in seen_note))
            fail(k, "F4 expectations state a note that was not handed to me")
    for (k in seen_note)
        if (!(k in seen_expect))
            fail(k, "F4 note has no hand-written expectations -- nobody is reading it")

    # F1/F2: every stated fact must hold.
    for (k in seen_expect) {
        n = split(want_keys[k], ks, " ")
        for (i = 1; i <= n; i++) {
            kk = ks[i]
            if (kk == "") continue
            checked++
            w = want[k, kk]
            if (w == "(empty)") {
                if (!present[k, kk])
                    fail(k, "F2 " kk " is ABSENT; the expectations say present-and-empty, which is a different fact")
                else if (have[k, kk] != "")
                    fail(k, "F2 " kk " should be empty, note says \"" have[k, kk] "\"")
                continue
            }
            if (!present[k, kk]) { fail(k, "F1 " kk " absent from the note"); continue }
            if (have[k, kk] != w)
                fail(k, "F1 " kk ": the human says \"" w "\", the bytes say \"" have[k, kk] "\"")
        }
    }

    if (bad) {
        printf "FAULT  %d disagreement(s) between the frozen bytes and the hand-written meaning.\n", bad
        print  "One of them is wrong and NEITHER is evidence until you know which."
        print  "Do not re-emit the fixtures. See tests/fixtures/frozen/EXPECTATIONS.md."
        exit 1
    }
    printf "OK  %d note(s), %d stated fact(s); the bytes and the human agree\n", notes, checked
}
