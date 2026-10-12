#!/usr/bin/awk -f
# polygram -- bytes-lint, the Windows-byte guard.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPLv3+.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
#
# WHY THIS EXISTS.  On 2026-09-14 the Python suite was green on GNU/Linux and
# FOURTEEN tests were red on Avalon, and I could not see it: one platform is
# one reader.  Every one of the fourteen was the same fault in two flavours:
#
#   text-mode WRITE   Python turns "\n" into "\r\n" on Windows.  A test that
#                     hashes b"x\n" and then calls write_text("x\n") hashes
#                     two bytes and writes three.  That is not a Windows
#                     quirk; it is a test asserting about bytes it did not
#                     write.
#   text-mode READ    Python decodes with the LOCALE codec on Windows
#                     (cp1252), so the first em-dash raises UnicodeDecodeError
#                     4205 bytes in and takes an unrelated test with it.
#
# THE RULE, in one line: any call that crosses the text/bytes boundary must
# say which encoding and which newline convention it means.
#
# This is a lint in a THIRD language, per the house rule -- the work under
# test is Python and so are the tests, so a Python checker written by the same
# hand would have inherited the same blind spot ("write_text writes what you
# give it").  awk reads the file as text and believes nothing.
#
# HOW IT READS PYTHON, and where that stops.  Three passes, cheapest first:
#
#   1. Triple-quoted regions are SKIPPED entirely.  Docstrings and test
#      fixtures legitimately contain the very patterns this hunts for, and the
#      first version of this lint failed on its own test file for exactly that
#      reason -- a guard that cannot tell code from writing about code will be
#      disabled by the first person who documents it.
#   2. Quoted spans are BLANKED before matching, so `assertIn("p.read_text(")`
#      is not a finding.
#   3. Physical lines are joined into LOGICAL lines by paren balance, so a
#      call whose encoding= sits on the next line is judged whole.  The first
#      version checked B3/B4 line-at-a-time and flagged correct code.
#
# It is not a Python parser and does not need to be.  What it cannot see it
# will simply not report, and the honest name for a quiet run is "no finding",
# not "clean".
#
# Usage:  awk -f bin/bytes-lint.awk FILE...        (exit 1 if anything found)
#         awk -f bin/bytes-lint.awk -v prove_red=1 FILE...

BEGIN { bad = 0; files = 0 }

FNR == 1 { files++; buf = ""; depth = 0; start = 0; triple = "" }

{
    line = $0

    # ---- pass 1: triple-quoted regions ----------------------------------
    if (triple != "") {
        if (index(line, triple)) {
            line = substr(line, index(line, triple) + 3)
            triple = ""
        } else next
    }
    line = drop_triples(line)      # sets `triple` if one is left open

    # ---- pass 2: blank quoted spans -------------------------------------
    line = blank_strings(line)

    # ---- pass 3: join into logical lines --------------------------------
    if (depth <= 0) { buf = line; start = FNR; depth = paren_delta(line) }
    else            { buf = buf " " line; depth += paren_delta(line) }
    if (depth > 0) next

    judge(buf, start)
    buf = ""; depth = 0
}

function judge(s, ln) {
    if (s ~ /\.read_text\(/ && s !~ /\.read_text\([^)]*encoding[ \t]*=/)
        report("B1", ln, "read_text() without encoding= (cp1252 on Windows)")
    if (s ~ /\.write_text\(/) {
        if (s !~ /encoding[ \t]*=/)
            report("B2", ln, "write_text() without encoding=")
        if (s !~ /newline[ \t]*=/)
            report("B2", ln, "write_text() without newline= (LF becomes CRLF on Windows)")
    }
    if (s ~ /open\(/ && s ~ /"[rwa]\+?"/ && s !~ /"[rwa]b\+?"/ \
        && s !~ /encoding[ \t]*=/)
        report("B3", ln, "open() in text mode without encoding=")
    if (s ~ /text[ \t]*=[ \t]*True/ && s !~ /encoding[ \t]*=/)
        report("B4", ln, "subprocess text=True without encoding= (locale codec on Windows)")
}

# Remove complete triple-quoted spans; if one is left open, record its marker
# in the global `triple` and truncate there.
function drop_triples(s,   out, i, m, j) {
    out = ""
    while (1) {
        i = match(s, /"""|'''/)
        if (!i) return out s
        m = substr(s, RSTART, 3)
        out = out substr(s, 1, RSTART - 1)
        s = substr(s, RSTART + 3)
        j = index(s, m)
        if (!j) { triple = m; return out }          # opens and stays open
        s = substr(s, j + 3)
    }
}

# Blank the CONTENTS of quoted spans, with one exception: a span of two
# characters or fewer is kept verbatim.  That exception exists for file MODE
# strings -- open(p, "w") -- and it is the whole of B3's evidence.  Blanking
# them made B3 silently unable to fire, which the prove-red now catches: a
# check that cannot go red is worse than no check, because it reports OK.
function blank_strings(s,   i, c, q, out, span) {
    out = ""; q = ""; span = ""
    for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (q != "") {
            if (c == "\\") { i++; continue }
            if (c == q) {
                q = ""
                out = out ((length(span) <= 2) ? "\"" span "\"" : "\"\"")
                span = ""
            } else span = span c
            continue
        }
        if (c == "\"" || c == "'") { q = c; span = ""; continue }
        if (c == "#") break
        out = out c
    }
    return out
}

function paren_delta(s,   i, c, d) {
    d = 0
    for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == "(" || c == "[") d++
        else if (c == ")" || c == "]") d--
    }
    return d
}

function report(code, ln, why) {
    bad++
    printf "%s:%d: %s %s\n", FILENAME, ln, code, why > "/dev/stderr"
}

END {
    if (prove_red) {
        if (blank_strings("assertIn(\"x.read_text()\")") ~ /\.read_text\(/) {
            print "prove-red FAIL: a read_text inside a STRING still matches, "\
                  "so this lint fires on anything that documents it" > "/dev/stderr"
            exit 2
        }
        if (!(blank_strings("p.read_text()") ~ /\.read_text\(/)) {
            print "prove-red FAIL: a real read_text does NOT match, so B1 "\
                  "can never fire and means nothing" > "/dev/stderr"
            exit 2
        }
        if (paren_delta("run(a,") != 1 || paren_delta("b)") != -1) {
            print "prove-red FAIL: logical-line joining is broken, so a call "\
                  "with encoding= on the next line reads as a finding" > "/dev/stderr"
            exit 2
        }
        if (!(blank_strings("open(p, \"w\")") ~ /"[rwa]\+?"/)) {
            print "prove-red FAIL: string-blanking ate the file MODE, so B3 "\
                  "can never fire and a quiet run means nothing" > "/dev/stderr"
            exit 2
        }
        if (blank_strings("x(\"a long literal\")") ~ /"[rwa]\+?"/) {
            print "prove-red FAIL: a long literal survived blanking" > "/dev/stderr"
            exit 2
        }
        print "prove-red PASS: the lint distinguishes code, strings and continuations"
    }
    if (bad) {
        printf "FAULT  %d byte-boundary problem(s) in %d file(s).\n", bad, files
        print  "Every one is a place where this code means different bytes on"
        print  "Windows than on GNU/Linux. Say the encoding and the newline."
        exit 1
    }
    printf "OK  no byte-boundary finding in %d file(s)\n", files
}
