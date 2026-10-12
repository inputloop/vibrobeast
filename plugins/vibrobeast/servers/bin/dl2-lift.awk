#!/usr/bin/awk -f
# polygram -- dl2 lift, implementation B (awk), written from chainspec.py's
# LIFT block.  Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPLv3+.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# This reader exists so that no single hand's arithmetic decides what stays
# available in a memory store.  It is NOT derived from polygram/mcp/dl2.py and
# must not be "fixed" by copying that file: where the two disagree, the spec in
# chainspec.py decides which one is wrong.
#
# INPUT: tab-separated on stdin, one line per (seam, citer) pair, plus one line
# per seam giving its pressure:
#
#   P<TAB>seam<TAB>pressure
#   C<TAB>seam<TAB>citer
#   U<TAB>seam<TAB>unit          (optional; absent means 1)
#
# A seam with no C line has no citers (L4).  Order does not matter.
#
# OUTPUT: one line per seam, tab-separated, sorted by seam:
#
#   seam<TAB>pressure<TAB>lift_milli<TAB>scale<TAB>by<TAB>state<TAB>unit<TAB>score_milli
#
# score_milli is chainspec's SCORE (U1-U4), the neutral-buoyancy line, and it
# is computed here as a SECOND READER of that spec: -1000 = nothing has leaned
# on it, 0 = carrying exactly what it was built to carry, +1000 = act.
# Truncation toward zero is awk's native int() on a negative, which is what
# U3 specifies -- Python is the reader that has to correct for this one.
#
# state is OK, NOCITER (L4) or DAMAGED (L5).

BEGIN { FS = "\t"; OFS = "\t" }

$1 == "P" { press[$2] = $3 + 0; seen[$2] = 1; next }
$1 == "U" { unit[$2] = ($3 + 0 < 1) ? 1 : $3 + 0; seen[$2] = 1; next }   # U2
$1 == "C" {
    seen[$2] = 1
    if (!(($2 SUBSEP $3) in pair)) {
        pair[$2, $3] = 1
        cn[$2]++;            cite[$2, cn[$2]] = $3      # citers of this seam
        wn[$3]++;            world[$3, wn[$3]] = $2      # world of this citer
    }
    next
}

# chainspec U3: score in thousandths, truncated toward zero. int() truncates
# toward zero in awk, which IS the spec -- so this reader needs no correction
# and the Python one does. Written out anyway rather than inlined, because a
# rounding rule that lives only in an expression is a rounding rule nobody
# reviews.
function score_of(s,   u) {
    u = (s in unit) ? unit[s] : 1
    if (u < 1) u = 1
    return int((press[s] - u) * 1000 / u)
}

# L2: lower median of a citer's world, floored at 1.
function scale_of(c,   i, n, v, tmp, j, t) {
    n = 0
    for (i = 1; i <= wn[c]; i++) { n++; v[n] = press[world[c, i]] + 0 }
    if (n == 0) return 1
    # insertion sort -- n is the size of one consumer's world, not the store
    for (i = 2; i <= n; i++) {
        t = v[i]; j = i - 1
        while (j >= 1 && v[j] > t) { v[j + 1] = v[j]; j-- }
        v[j + 1] = t
    }
    t = v[int((n - 1) / 2) + 1]          # awk arrays are 1-based; (n-1)//2
    return (t < 1) ? 1 : t
}

END {
    for (s in seen) {
        p = press[s] + 0
        u = (s in unit) ? unit[s] : 1
        sm = score_of(s)
        if (cn[s] == 0) { print s, p, 0, 0, "", "NOCITER", u, sm | "sort"; continue }
        if (p < 0)      { print s, p, 0, 0, "", "DAMAGED", u, sm | "sort"; continue }
        best = -1; bestby = ""; bestscale = 0
        for (i = 1; i <= cn[s]; i++) {
            c = cite[s, i]
            sc = scale_of(c)
            lm = int((p * 1000) / sc)          # non-negative here, so int() == floor
            # L3 tie-break: citer name ascending, so `by` is deterministic.
            # L3 tie-break: ascending BYTEWISE. The empty-string concatenation
            # is load-bearing: awk compares two strnum values NUMERICALLY, so
            # citers named "9" and "10" would tie-break the other way from the
            # Python reader without it. Forcing string type here is the fix
            # the spec's "ascending bytewise" clause requires.
            if (lm > best || (lm == best && (c "") < (bestby ""))) {
                best = lm; bestby = c; bestscale = sc
            }
        }
        print s, p, best, bestscale, bestby, "OK", u, sm | "sort"
    }
    close("sort")
}
