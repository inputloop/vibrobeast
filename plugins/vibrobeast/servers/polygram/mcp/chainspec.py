# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  GPL-3.0-or-later.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.

"""chainspec -- what "the chain holds" means, written once, in prose.

An adversarial read on 2026-09-14 found that the two verifiers agreed on a
FORGED chain, and agreed for the same wrong reason: both decided which file was
generation 1 by reading its ``gen:`` field, and neither tied that field to the
file's position or to its own name.  Appending one hand-written file that said
``gen: 1`` re-rooted a genuine three-generation chain and both readers said OK.

Two independent implementations sharing one unstated assumption are not two
readers.  They are one reader, typed twice.

So the assumption is stated here, in words, as four numbered checks, and each
implementation is written from THIS text rather than from the other one.  That
is the only thing that makes them independent: not different languages, but a
common specification neither of them is.

THE CHAIN SPEC (v1)
===================

Given a seam directory, take every **regular file** whose name matches
``g<digits>-<stamp>-<hex16>.md``.  Ignore anything else -- a directory with a
matching name, a symlink, a stray note.  Order them by the integer value of
``<digits>``, ascending (NOT by string sort: ``g10000`` sorts before ``g9999``
as a string).  Call them file 1..N.

For file *i*:

  **C1  position**   the ``gen:`` field must equal *i*.
                     Catches: a forged generation 1 appended to a real chain;
                     a gap; a duplicate generation number.

  **C2  name**       the integer in the filename's ``g<digits>`` must equal the
                     ``gen:`` field.
                     Catches: a file renamed to change its place in the order.

  **C3  self**       the filename's ``<hex16>`` must equal the first 16 hex
                     characters of sha256 of **the whole file's bytes**.
                     Catches: any edit to any generation, including the HEAD,
                     which no ``prev:`` pointer can ever cover because nothing
                     comes after it; and a write that died partway through.

                     *Changed in v2, and it made the spec smaller.*  v1 hashed
                     only the body, so the head generation's FRONT MATTER was
                     unprotected -- ``mode: JAILED`` could be edited to
                     ``SEATED`` and every reader still said OK, while the code
                     that wrote it promised the word was "stamped in the bytes
                     forever".  Hashing the whole file needs no extra field and
                     no self-referential hash, because **the filename is not
                     inside the file**: the writer renders the text, hashes it,
                     and then names the file after it.  One rule replaced two
                     and covers strictly more.

  **C4  link**       ``prev:`` must be empty for i=1, and for i>1 must read
                     ``sha256:<h>`` where <h> is sha256 of file i-1's **bytes
                     as they sit on disk**, byte for byte, no newline
                     translation and no decoding.
                     Catches: any edit to a non-head generation.

The first check that fails, in the order C1 C2 C3 C4 within a file and files in
order, is THE failure.  Report it as ``BROKEN <filename> <which check> <why>``
and stop.  Both implementations must stop at the same place or they are not
answering the same question.

Normalisation rules, stated because they are where two readers silently differ:

  * **No newline translation anywhere.**  Hash bytes.  A file with CRLF endings
    is a different file from one with LF, and both readers must say so
    identically.
  * **Front-matter keys** are matched at the start of a line after stripping
    leading and trailing horizontal whitespace from the key, and the value is
    everything after the first colon, stripped the same way.
  * **The first occurrence of a key wins.**  A second ``prev:`` line is ignored.
  * **``gen:`` must match ``^[0-9]+$`` and is then compared as an integer**, so
    ``01`` and ``1`` are the same, while ``+7``, ``0x8``, a full-width ``０７``
    and a non-breaking space before a digit are all C1 failures.  Python's
    ``int()`` accepts every one of those and the other two readers accept
    none, so the permissive one has to be constrained, not the strict ones.
  * **Leading zeros are stripped before the integer compare, decimally.**
    POSIX ``$((0008))`` is an octal error, which crashed one reader at
    generation 8 and silently dropped the house from three readers to two.
  * **``prev:`` has exactly one legal prefix, ``sha256:``.**  Any other prefix
    is not stripped; it will simply fail to match, which is correct -- an
    unknown hash algorithm is a chain we cannot verify, not one we pass.
  * **A body that is not valid UTF-8 is not an error.**  Hash the bytes.
  * **C3 needs no parsing at all** -- it is a hash of the file against its own
    name.  That is worth noticing: the one check that covers every byte is the
    one that cannot be confused by a parser disagreement.

THE NAME (v3, 2026-09-15) -- THE DATE COMES OUT OF THE NAME
===========================================================

    v2 minted   g0001-20260915T120000Z-df2c139fa0f0d3be.md    42 characters
    v3 mints    g0001-df2c139fa0f0d3be.md                     25 characters

C1, C2, C3 and C4 are UNCHANGED.  Their text above is the text.  The only
thing that moves is the shape a name may take:

    v2 name     g<digits> - <stamp> - <hex16> .md
    v3 name     g<digits> -           <hex16> .md

The ``<stamp>`` segment is now OPTIONAL in the shape a reader accepts, and is
never written by a v3 writer.  **Both shapes are generation files, forever.**

WHY.  Corwin, 2026-09-15: *"dates attach to actions (often in log or otherwise
historical context) but otherwise look foolish when painted into prose (which
we can sometimes ... usefully consider filenames, or parts of them including
path, as being)."*  A path is prose.  ``notes/carrying-sixteen/g0001-df2c...md``
reads as: this seam, its first generation, that handle.  The date was a fact
about an ACT -- the append -- wearing the clothes of a fact about the thing.

And the measured reason, which is the stronger of the two.  **THE STAMP
SEGMENT IS CHECKED BY NOTHING.**  C1 reads ``gen:``.  C2 compares the name's
integer to ``gen:``.  C3 compares the name's hex to the file's own bytes.  C4
compares ``prev:`` to the previous file's bytes.  No check in this spec, and
no line in any of the four implementations, ever compared the name's stamp to
the ``stamp:`` field or to anything else.  ``GEN_NAME``'s group 2 was captured
by every reader and read by none.

  OBSERVED, 2026-09-15.  A COPY of tests/fixtures/frozen/carrying-sixteen with
  both filenames repainted -- ``g0001-19700101T000000Z-df2c139fa0f0d3be.md``
  and ``g0002-99999999T999999Z-03a13e819d19944d.md`` -- and the bytes inside
  untouched:

      sh bin/dl2-verify.sh   SEAM  ->  OK<TAB>2          exit 0
      perl bin/dl2-verify.pl SEAM  ->  OK<TAB>2          exit 0
      verify.verify_python(SEAM)   ->  ok=True, gens=2

  Seventeen characters asserting a date, in a store whose whole discipline is
  that a claim carries its check.  Deleting an unverified claim that sits
  beside three verified records of the same fact is not a loss of information.
  It is the removal of a thing that could only ever have been wrong.

WHERE THE DATE ALREADY LIVES -- three places, none of them the name:

    stamp:            in the note's own front matter, and therefore INSIDE the
                      C3 hash.  Tamper-evident, which the name never was.
    the receipts log  every APPEND is a dated line carrying the filename.
                      This is the owner's rule already true as a fact: the
                      date is attached to the ACTION, in a log.
    the citation log  every citation is separately dated, per seam.

WHAT A READER OF OLD FILES MUST STILL DO
----------------------------------------
This store never overwrites (rule 1), so every v2 name on disk stays a v2 name
forever.  Every reader is a reader of BOTH eras until the end of the store.

  N1  ACCEPT BOTH SHAPES.  ``g<digits>-<hex16>.md`` and
      ``g<digits>-<stamp>-<hex16>.md`` are both generation files.  A reader
      that accepts only one will either lose every archived note or lose every
      new one -- and neither failure announces itself, because a file that
      does not match the shape is silently skipped, which is exactly what an
      empty seam looks like.  That is the "lose the files" failure in its
      purest form and it is why N1 is first.

  N2  THE HANDLE IS ALWAYS THE LAST SEGMENT.  Parse it from the END of the
      name, never by counting segments from the front.  This one rule is what
      makes a two-shape format cheap in every language: ``${b##*-}`` in sh,
      ``rsplit('-', 1)`` in Python, an anchored regex's last group in Perl.
      The density test is satisfied by the shape, not by good intentions.

  N3  DO NOT START CHECKING THE STAMP.  It is tempting to add "if the name
      carries a stamp it must equal ``stamp:``".  REFUSE.  No rule ever
      constrained that segment, so a new check would retroactively invalidate
      archived bytes that broke no rule when they were written -- and rule 1
      forbids deleting them, so the result is a permanently BROKEN seam that
      nobody is allowed to repair.  A spec may stop requiring something.  It
      may not retroactively start.

  N4  MIXED SEAMS ARE ORDINARY.  A seam whose generations 1..k are v2 and
      k+1..n are v3 is ONE chain, not two.  C1 orders by the integer in the
      name, C4 links by bytes, and neither has ever looked at the name's
      shape.  There is no migration, no rename and no flag day.  That is a
      consequence of the format rather than a promise about it.

  N5  ``first-seen:`` IS WHATEVER IT SAYS.  A v3 generation of an old seam
      carries generation 1's v2 filename, because the pin is inherited from
      the previous generation and never recomputed.  A reader that
      "normalises" it to the new shape is inventing a filename that is not on
      disk.

REFUSED, WITH WHAT EACH REFUSAL COST
------------------------------------

  * DROP THE ZERO PADDING (``g1-`` rather than ``g0001-``).  SAVES 3
    CHARACTERS.  Refused.  The padding is the only reason a plain ``ls`` walks
    a chain in order, and store rule 2 says the index is a cache and the FILES
    are the record -- so a human with nothing but ``ls`` is the reader this
    format exists for.  And unlike the stamp, the padded integer is CHECKED:
    C2 compares it to ``gen:``.  The fat was never in the digits.
    COST: 3 characters, and the ``ls`` ordering still breaks above g9999,
    which is unchanged and was already true.
    FALSIFIER: show that no reader of this store ever lists a seam directory
    without the store's own tooling, and the padding is decoration.

  * BASE32 OR BASE36 RATHER THAN HEX.  13 base32 characters carry the same 64
    bits as 16 hex.  SAVES 3 CHARACTERS, and single-case base32 (A-Z2-7) is
    genuinely safe on a case-insensitive filesystem -- base64 is not, and
    neither is any mixed-case alphabet, because macOS and Windows fold ``A``
    and ``a`` together and two distinct digests could then name one file.
    Refused anyway, for two reasons that are not about size.
    First, THE DENSITY TEST this file applies to itself: ``sha256sum`` prints
    hex, so every reader would have to re-encode, and hand-rolling base32 in
    POSIX sh is precisely the point at which a spec becomes feasible in some
    languages only.
    Second, and worse: generation 2's ``prev:`` records generation 1's full
    sha256 in hex, and its first sixteen digits ARE generation 1's filename
    stem.  A human can SEE that agreement.  That free agreement between two
    independently written records is the entire thesis of
    tests/fixtures/frozen/EXPECTATIONS.md -- change the alphabet and the eye
    can no longer make the comparison.
    COST: 3 characters.
    FALSIFIER: put ``prev:`` in base32 too, so the two records share an
    alphabet again -- at the price of a hash format no tool prints.

  * A SHORTER HANDLE.  The arithmetic is below and it permits 12 hex.
    Refused; the binding constraint is not collisions.  COST: 4 characters.

HOW SHORT MAY THE HANDLE BE -- the arithmetic, not an assertion
--------------------------------------------------------------

THE ASSUMPTION, stated so it can be argued with: **collisions matter only
WITHIN ONE SEAM DIRECTORY**, because that is the only namespace two generation
files ever share.  A seam is one note's chain and its generations are authored
revisions, so a seam reaching 10^4 generations is already past anything this
store has seen; 10^6 appears below only to show where the cliff is.

Birthday bound, P ~= k(k-1) / (2 * 2^(4h)), computed rather than estimated:

    hex  bits   k=10^3     k=10^4     k=10^5     k=10^6     50% at k
     8    32    1.2e-04    1.2e-02    (>1)       (>1)        7.7e+04
    10    40    4.5e-07    4.6e-05    4.6e-03    4.6e-01     1.2e+06
    12    48    1.8e-09    1.8e-07    1.8e-05    1.8e-03     2.0e+07
    14    56    6.9e-12    6.9e-10    6.9e-08    6.9e-06     3.2e+08
    16    64    2.7e-14    2.7e-12    2.7e-10    2.7e-08     5.1e+09

On ACCIDENT alone 12 hex is comfortable at any plausible seam depth and 10
would serve.  And an accidental collision here is loud and mild rather than
silent: ``store.append`` opens with ``O_CREAT|O_EXCL`` and raises rather than
overwriting, so a collision is a REFUSED WRITE, never a lost note.

THE BINDING CONSTRAINT IS NOT COLLISIONS.  It is C3's work factor.  C3 is the
only check that reaches the HEAD generation's bytes -- nothing comes after the
head, so no ``prev:`` can ever cover it -- and forging an undetectable edit
means finding a file that agrees with the recorded name in its first 4h bits.
At a round 10^10 sha256/s, one high-end GPU:

    12 hex   2^48 = 2.8e14 evaluations   ~  7.8 hours
    14 hex   2^56 = 7.2e16               ~  83 days
    16 hex   2^64 = 1.8e19               ~  58 years

Four characters buy five orders of magnitude, on the one check that covers the
head of a chain.  That is why the handle stays at 16 while the date goes: one
of the two is a claim with a check behind it and the other never was.

THE CAVEAT, because the number above holds only where the NAME IS PINNED.  An
attacker who can edit a file in a seam directory can usually rename it too,
and then C3 compares the file against a name the attacker chose, for no work
at all.  The work factor binds only where the name is recorded somewhere the
attacker must ALSO reach: ``first-seen:`` inside every generation from 2
onward (itself under C3 and C4), and the receipts log's APPEND line.  For a
chain's head the receipts log is the only such pin.  That is a real limit on
the claim, written here rather than left for someone to discover.
FALSIFIER: a demonstrated 64-bit sha256 prefix second-preimage against a
chosen file, for less than the cost of simply rewriting the whole directory --
at which point the handle's length was never what protected anything.

WHAT v3 COSTS A HUMAN, said plainly rather than argued away
-----------------------------------------------------------
One affordance is genuinely lost: **a bare ``ls`` no longer shows when a
generation was written.**  It is a BROWSING affordance, not a FINDING one --
no path by which a human finds a note has ever run through the name's date --
but it is real and it is not nothing.

What replaces it, and whether each replacement is honestly as good:

    "which generation is newest?"     ``ls`` still answers it.  g0001, g0002,
                                      ... sorts by generation and generations
                                      are strictly appended, so within the
                                      only directory where both were ever
                                      visible, the stamp was a SECOND copy of
                                      an ordering the digits already gave.
                                      NOT WORSE.
    "when was this written?"          ``head -4 *.md`` or
                                      ``grep -H '^stamp:' *.md``.  One command
                                      instead of none -- WORSE BY ONE COMMAND
                                      -- and it reads the field that is inside
                                      the C3 hash instead of one that was
                                      inside nothing.  Worse to reach, better
                                      to trust.
    "what did I write last Tuesday?"  ``grep -r '^stamp: 20260909' notes/``.
                                      Exact, and it searches the authoritative
                                      field.  NOT WORSE.
    ``ls -t``                         IS NOT THE ANSWER and must not be
                                      offered as one.  mtime is filesystem
                                      metadata: ``cp``, ``unzip``, a restore
                                      and most sync tools rewrite it, and this
                                      store's whole claim is that the RECORD
                                      is the bytes.  Naming ``ls -t`` as the
                                      replacement would be trading a checked
                                      fact for an unchecked one and calling it
                                      parity.

The one place the loss is paid back in kind: ``rebuild_index`` now carries a
``head-stamp`` column.  The date moves from the record's NAME to the CACHE
built for browsing, which is where store rule 2 says a derived convenience
belongs.
COST: the index line is one column longer, and any consumer reading it by
column position must count again.  Nothing in this tree does; the citation-log
parsers read a different file.
FALSIFIER: a reader that browses seam directories with ``ls`` and never opens
the index -- for them the loss is not paid back, and they are the reader who
should say so.

THE DENSITY TEST (Corwin, 2026-09-14)
=====================================

His rule, stated while this file was being written:

    *"If something is so hard it can be implemented (or maintained) feasibly
    only in a given [language] -- or only in one, considering the ambition of
    our project at all -- then we have to question if our approach is too
    dense, or maybe the whole thing we are trying to bite off isn't quite right
    as we consider it relative to a general mission: to organize each given
    problem in terms of its solution."*

So the number of independent implementations a spec sustains is not only a
redundancy measure.  **It is a gauge of whether the spec is well decomposed.**
A specification that only one language can carry is not a hard problem well
stated; it is a problem still tangled with its first solution.

This spec is offered against that gauge and reports its own numbers:

    Python  polygram/mcp/verify.py:verify_python    47 lines
    sh+awk  bin/dl2-verify.sh:verify_dir             69 lines
    Perl    bin/dl2-verify.pl:verify_dir             44 lines
    node    tests/conformance/run.js (WRITES it)      35 lines

(counted with the commands in the conformance suite's header, not estimated --
a measured claim in a file about measurement should be measured.)

Four languages, none needing a library beyond a sha256 that each already ships,
none longer than a screen.  That is the evidence that C1-C4 are the right
decomposition -- not that they are correct, which the conformance suite shows,
but that they are *separable*.  If a fifth implementation needed a parser
generator, or if maintaining the shell one meant tracking the Python one line
by line, the density test would have failed and the spec would be the thing to
fix.

Where the test says one language is fine
----------------------------------------
The test applies to **proofs**, not to producers.  ``store.py`` writes these
files and exists only in Python, and that is not a violation: it produces bytes
that four languages can check.  The line is that whatever is load-bearing as
EVIDENCE must be multiply implementable; whatever is merely a convenience may
be written once.

That line is itself the useful output of the density test here, because it
forced a separation that was not obvious before: the *format* is the contract
and the *writer* is an implementation.  Had the two stayed mixed -- had
verification needed the writer's own parser -- the whole thing would have been
one language wide, and the 2026-09-14 forgery would have had no independent
reader to find it.

WHAT THE SPEC DOES NOT COVER, said plainly so nobody assumes it does:

  * It proves the files are internally consistent, not that they are *yours*.
    Authorship needs a signature against a pinned key; that is ``skill-sign``'s
    job and this is not a substitute for it.
  * An attacker who can rewrite the WHOLE directory can build a consistent
    forged chain from generation 1.  The chain is tamper-evident against edits,
    not against replacement.  Detecting replacement needs an anchor kept
    somewhere the attacker is not -- a signature, or a hash recorded elsewhere.
"""

from __future__ import annotations

import re

__all__ = ["GEN_NAME", "SPEC_VERSION", "NAME_VERSION", "checks", "name_checks",
           "name_era", "GEN_PAD", "HEX_LEN"]

SPEC_VERSION = 3

# The version of the NAME SHAPE a writer mints.  Separate from SPEC_VERSION on
# purpose: C1-C4 did not move, only the shape did, and conflating the two would
# make a future reader believe a check changed when none did.
NAME_VERSION = 3

GEN_PAD = 4      # g%04d -- checked by C2; see "REFUSED" in the v3 block.
HEX_LEN = 16     # the handle; see "HOW SHORT MAY THE HANDLE BE".

# BOTH shapes, and the stamp segment is optional (v3, N1):
#
#     v2   g<digits>-<stamp>-<hex16>.md
#     v3   g<digits>-<hex16>.md
#
# ASCII digits explicitly. Python's \d is Unicode-aware and matches e.g.
# U+0663 ARABIC-INDIC THREE, while the sh and Perl readers are ASCII-only --
# so one planted file with a non-ASCII digit made Python count a generation
# the other two could not see, and every check of that seam raised ChainSplit
# forever. A character class is cheaper than a permanent stalemate.
#
# THE GROUP NUMBERS DO NOT MOVE.  group(1) is the generation, group(3) is the
# handle, exactly as under v2 -- group(2) is now simply ``None`` for a v3 name.
# Every existing caller reads group(1) or group(3) and keeps working unchanged;
# renumbering would have been a silent way to make one reader read the stamp
# where another reads the hash, which is the class of split this whole file
# exists to prevent.
#
# THE OPTIONAL GROUP IS SAFE AGAINST A DIGITS-ONLY HANDLE.  ``[0-9TZ]+`` can
# match a handle made entirely of decimal digits, so ``g0001-0123456789012345.md``
# could in principle be read as gen + stamp + (nothing).  It is not: the trailing
# ``-([0-9a-f]{16})\.md$`` then has nothing to match, the engine backtracks, and
# the optional group drops out.  The anchored 16-character tail is what makes
# this unambiguous, which is the same fact N2 states for the other languages --
# parse the handle from the END.
GEN_NAME = re.compile(r"^g([0-9]+)(?:-([0-9TZ]+))?-([0-9a-f]{16})\.md$")

checks = ("C1 position", "C2 name", "C3 self", "C4 link")
name_checks = ("N1 both shapes", "N2 handle is last", "N3 do not check the "
               "stamp", "N4 mixed seams", "N5 first-seen verbatim")


def name_era(name: str) -> int:
    """2, 3, or 0 for "not a generation file".

    Reporting only.  NOTHING in C1-C4 may branch on this -- the era of a name
    is not a fact about whether the chain holds, and a reader that treated it
    as one would have invented a rule the archive was never written under
    (v3 N3).  It exists so that a human, or a test, can say *which* era a file
    is from without re-deriving the regex in a fifth place.
    """
    m = GEN_NAME.match(name)
    if not m:
        return 0
    return 2 if m.group(2) is not None else 3


# =====================================================================
# LIFT -- the buoyancy ranking, specified in prose so that no reader is
# the specification.
# =====================================================================
#
# This block is the CONTRACT.  `dl2.lift` is one implementation of it and
# `bin/dl2-lift.awk` is another; neither is authoritative, and where they
# disagree the answer is here.  That arrangement exists because of finding C9
# on 2026-09-14: two readers written in two languages by one hand FAILED
# TOGETHER on a forged chain, because they shared an unstated assumption.  Two
# languages is not independence.  A common spec that neither reader is, is.
#
# WHAT IT IS FOR.  `pressure` counts citations since a note's head generation
# was written.  Ranking a whole store by that count sinks a quiet consumer's
# entire world below a busy consumer's noise, which spends availability -- the
# thing Corwin says users actually need -- to buy nothing.  LIFT measures each
# seam against the worlds that cite it instead of against the store.
#
# INPUTS.  Two maps, both derived from files the store already keeps:
#   pressure[seam]  an integer, possibly negative (negative is PROOF the
#                   citation log lost lines -- see dl2.pressure)
#   citers[seam]    the set of distinct values in column 2 of that seam's
#                   citation log.  Column 2 is what the citer recorded about
#                   ITSELF.  It is never a label this store put on the note --
#                   that is store rule 4 and it is not negotiable here.
#
# DEFINITIONS, in order.  L1..L5 are the checks a conformance run makes.
#
#   L1 WORLD.   world(c) = { s : c is in citers[s] }.
#
#   L2 SCALE.   scale(c) = max(1, lower_median({ pressure[s] : s in world(c) }))
#               LOWER MEDIAN means sorted(values)[(n-1)//2] -- the element at
#               that index, NOT the mean of the two middle elements.  An
#               integer, exact, and four lines in awk.  A mean-of-middles
#               introduces a half, therefore a float, and a float is where
#               independent readers stop agreeing bit for bit.
#               The floor of 1 prevents division by zero when a whole world
#               has never been cited.
#
#   L3 LIFT.    For a seam s with at least one citer and pressure >= 0:
#                 lift_milli(s) = max over c in citers[s] of
#                                   (pressure[s] * 1000) // scale(c)
#               INTEGER FLOOR DIVISION, in thousandths.  Not a ratio: float
#               division is not bit-identical across languages and this number
#               is compared between readers.  1000 means "exactly the lower
#               median of the most favourable world that cites it".
#               Ties between citers are broken by the citer's name ascending,
#               so the reported `by` is deterministic.  ASCENDING BYTEWISE, as
#               a string, always.  This sentence used to say only "ascending"
#               and that was not enough: the first conformance run split the
#               two readers on it twice over.  Reader A took the LARGEST name
#               on a tie (a `max` whose key carried the name), and reader B
#               compared names NUMERICALLY whenever they both looked like
#               numbers, which is awk's rule for values read from input -- so
#               citers named "9" and "10" would have ordered differently in the
#               two readers while every test passed.  Both were fixed against
#               this clause; neither was fixed by copying the other.
#
#   L4 NO CITER.  If citers[s] is empty, lift_milli = 0 and scale = 0, and the
#               row says so in words.  A seam nobody has cited is not the same
#               as a seam that ranks at the bottom, and reporting a confident
#               zero for both loses that distinction.
#
#   L5 DAMAGE.  If pressure[s] < 0, lift is NOT COMPUTED: lift_milli = 0,
#               scale = 0, and the row is marked DAMAGED.  Ranking damage is
#               meaningless.  The caller sorts damage first regardless.
#
# WHAT LIFT MUST NOT DO.  It must not compact, delete, archive or reorder
# anything on disk.  It returns numbers and the arithmetic that produced them
# (scale, and which citer supplied it) so that the caller can disagree.
# Corwin: poly and meantcached together are not "a waldo for perfect semaphore
# structure, even with linked list and fort/palace techniques" -- they are the
# pipeline that keeps the problem in front of something with judgement.
#
# THE DENSITY TEST applied to this spec.  Every operation above is sort,
# index, multiply, integer-divide and compare.  There is no step that is
# feasible in one language only.  That was a design constraint and not a happy
# accident: an instrument that decides what stays available must be checkable
# by more than the hand that wrote it.

LIFT_SPEC_VERSION = 1
lift_checks = ("L1 world", "L2 scale", "L3 lift", "L4 no citer", "L5 damage")

__all__ += ["LIFT_SPEC_VERSION", "lift_checks"]


# =====================================================================
# SCORE -- the neutral-buoyancy line, specified in prose.
# =====================================================================
#
# His mechanic, 2026-09-14, and his words for why it is a mechanic and not a
# rule: "it isn't clear to me it is correct to 'pin' that for all users and all
# use-cases but balanced tensions generally, a simple mechanic to start
# thinking a specific problem through in terms of, implies mechanics."
#
# THE LINE.  A number line he thinks of as -1..1, the generic adjustment being
# toward zero.  Each seam carries a UNIT METRIC `u`, its neutral-buoyancy mark,
# declared when the item is interned.  Subtract the mark and work in units of
# the same:
#
#       score(s) = (pressure(s) - u(s)) / u(s)
#
#       pressure = 0      ->  score = -1    nothing has leaned on it
#       pressure = u      ->  score =  0    NEUTRAL BUOYANCY
#       pressure = 2u     ->  score = +1    ACT
#
# So the ceiling for any seam is 2u, and u is what says how much that seam was
# built to carry.  His examples, verbatim in effect:
#
#   a simple term      u = 1   act at 2, "then four when it reaches that for
#                              the given context" -- the mark DOUBLES on action
#   C4 double-balanced u = 4   act at 8
#                              ("four points of meaning intersection to context
#                               mapped already at the time of call to decide
#                               how to write the item we are interning")
#
# "atom" here is his: a system-contextual unit for a term or concept, however
# it happens to apply, WITHOUT the decomposition toward existing C4 meaning
# being required.  So u is not a C4 fact.  It is how much structure the writer
# had in hand at intern time, and one is the honest answer when they had none.
#
# U1  DECLARED, NEVER INFERRED.  u comes from the writer, on the call that
#     interns the item, and is carried in the note's front matter.  Nothing in
#     this codebase may derive u from a note's body, its length, its subject or
#     its links.  That is store rule 4: deriving u from content would be the
#     store forming an opinion about what the note is about, dressed as
#     arithmetic.  A note whose front matter has no `unit` reads as u = 1.
#
# U2  FLOOR OF ONE.  u >= 1 always.  u = 0 divides; u = 0 also claims an item
#     with no neutral point, which is not a thing this line can express.
#
# U3  SCORE IN THOUSANDTHS, TRUNCATED TOWARD ZERO.
#
#         score_milli(s) = trunc( (pressure(s) - u(s)) * 1000 / u(s) )
#
#     TRUNCATED TOWARD ZERO, said in capitals because this number goes
#     NEGATIVE by design and that is where readers split.  awk's int(), C's
#     integer division, Perl's int() and POSIX sh's $((...)) all truncate
#     toward zero.  Python's // FLOORS toward negative infinity, so
#     (-7 * 1000) // 3 is -2334 where every other reader here says -2333.
#     Python is the odd one out and must correct for it; the spec follows the
#     majority because four readers correcting one is worse than one
#     correcting four.
#
#     This clause exists because the LIFT spec above learned it the expensive
#     way: L3's tie-break said only "ascending" and split two readers twice.
#     Rounding is the same shape of ambiguity and it is being paid for up
#     front this time.
#
# U4  ACT AT +1000, AND THE MARK DOUBLES.  score_milli >= 1000 means the seam
#     is carrying twice what it was built to carry: act.  Acting means minting
#     a new generation, which resets pressure (cited-at-write) and records
#     u * 2.  Nothing here performs that action -- see WHAT SCORE MUST NOT DO.
#
# HOW THIS RELATES TO LIFT, because they are two different normalizations and
# conflating them would lose both:
#
#     score  is INTRINSIC.  Against what this item was built to carry.
#            Per-item, absolute, needs no other seam to compute.  Decides
#            WHETHER to act.
#     lift   is CONTEXTUAL.  Against the worlds that actually cite it.
#            Comparative, needs the whole store.  Decides ORDER.
#
# They are orthogonal by construction, which is what his index card asked for
# ("change volatility orthogonal"): a seam can be far over its own ceiling in a
# quiet world, or comfortably under it while topping a busy one, and the two
# numbers say different true things about it.  Neither is derived from the
# other and nothing in this codebase composes them into a single verdict.
#
# WHAT SCORE MUST NOT DO.  It must not compact, revise, double `u`, or mint
# anything.  It returns a number and the two inputs that made it.  The doubling
# in U4 is what a caller does when it decides to act, and deciding is not this
# module's job.
#
# OPEN, and his to settle -- recorded rather than guessed:
#   * "the generic adjustment being toward zero" is read here as a CONSERVATISM
#     RULE (when adjusting a value on this line, move toward neutral), not as a
#     state transition.  Under U4 acting leaves the seam at -1, not 0, because
#     pressure resets to 0 while u doubles.  If he meant the post-action state
#     should be 0, U4 is wrong and the fix is that acting sets cited-at-write
#     to u rather than to the full citation count.
#     FALSIFIER: he says which.  Until then this reading is [MINE] and the
#     alternative is written down where it cannot be quietly forgotten.

SCORE_SPEC_VERSION = 1
score_checks = ("U1 declared", "U2 floor", "U3 truncation", "U4 act and double")
ACT_AT_MILLI = 1000

__all__ += ["SCORE_SPEC_VERSION", "score_checks", "ACT_AT_MILLI"]
