# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""dl2 -- the doubly-linked citation spine.

Two columns, and the whole discipline is in them:

  **first-seen**   where we learned it.  Written INTO the bytes, once, and
                   never edited again.  It names generation 1 of the note by
                   filename, so it is a pin a reader can open.
  **last-cited**   the most recent citation of the fact.  NOT a field in the
                   note, and that is not an oversight -- see below.

Why last-cited is not a field
-----------------------------
A note is archived, never overwritten (``store.py``).  If ``last-cited`` lived
in the note's front matter, then every *citation* -- an act that changes
nothing about the fact -- would have to mint a new generation, and the chain
would fill with generations that differ from their parent by one timestamp.
So citations go to an append-only sidecar log and ``last-cited`` is read from
its tail.

The constraint pays for itself.  The gap between what a generation *said* the
last citation was when it was written, and what the log says now, is a number:

    pressure(seam) = citations recorded since the head generation was written

That is **memory change pressure**.  A note nobody cites has pressure 0 and can
sink.  A note leaned on twenty times since it was last revised is the one that
needs looking at.  Compaction reads this number instead of guessing, which is
the point: the house rule is that a compaction is triggered by the loaded page
approaching its cap, never by tidiness -- pressure adds a second honest trigger
that is also not tidiness.

The buoyancy reading
--------------------
Corwin's index card beside the 2026-09-14 drawing gives the same idea its
picture: SURFACE / "buoyancy" over DEPTH / FLOOR, with a periscope going up and
a DIVE going down.  Pressure is buoyancy.  High pressure floats a note to the
surface (it stays on the loaded index page); zero pressure lets it sink toward
the floor (a continuation page, then the archive).  Nothing is thrown out at the
floor -- the floor is still the store.

Links
-----
``came-from`` / ``leads-to`` are the palace's spine, kept verbatim from
[[pocket-mentat]] so a note written under the portable rules parses here with no
translation.

Link paths carry a scheme or they FAULT.  A bare host path is host-specific
without saying so, which is the failure the C4 invariant-link rule names:

    seat:/notes/foo.md        the memory seat, wherever it is mounted
    c4:/h/MODEL-....md        the C4 register tree
    ws:/skills/two-columns    the polygram workspace
    avalon:F:/claude/...      pinned to a named host, on purpose, declared
    [[seam-slug]]             another note in this store
    [[seam-slug|g0001-...]]   ... pinned to a named generation

``/f/claude/c4/h/x.md`` alone is a FAULT: it may be right on his machine and is
unresolvable anywhere else, and nothing in the bytes says which.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field

# The pad width and handle length live in chainspec, beside the prose that
# argues for them and beside GEN_NAME, which must agree with whatever this
# function mints. Two copies of "16" in two files is how a format quietly
# forks.
from . import chainspec as _chainspec

__all__ = [
    "SCHEMES", "Note", "parse_note", "render_note", "slugify",
    "links_in", "check_link", "LinkFault", "gen_filename", "pressure",
    "LINE_BREAKS", "refuse_line_breaks",
]

# Link schemes that resolve per-host and are therefore checkable.  A pinned
# host path (``<host>:<path>``) is also legal but must name the host; the
# resolver treats any scheme not in this set as a host pin.
SCHEMES = ("seat", "c4", "ws")

_FM_OPEN = "---"
_STAMP_FMT = "%Y%m%dT%H%M%SZ"

# [[target]] or [[target|pin]] -- the house's own wikilink, unchanged.
_WIKILINK = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")
# scheme:path -- one scheme word, a colon, then a non-space path.
_SCHEMED = re.compile(r"\b([A-Za-z][A-Za-z0-9_-]*):((?:[A-Za-z]:)?/[^\s)\]]+)")
# A bare absolute path with no scheme at all.  This is the fault case.
_BARE_ABS = re.compile(r"(?<![A-Za-z0-9_:-])((?:[A-Za-z]:)?/(?:[\w.-]+/)+[\w.-]+)")
# A Windows path: a drive letter with backslashes, or a UNC share.  These were
# invisible to the checker until an adversarial read pointed out that the most
# host-specific path form in the house was the one form it could not see --
# on a Windows host, which is the platform the whole thing runs on.
_WIN_ABS = re.compile(r"(?<![A-Za-z0-9_-])((?:[A-Za-z]:|\\\\[\w.-]+)\\[\w.\\-]+)")


class LinkFault(ValueError):
    """A link that cannot be resolved on a host other than the one that wrote it."""


def slugify(seam: str) -> str:
    """A filesystem-safe handle for *seam*, stable across hosts.

    Lowercase, non-alphanumerics collapsed to single hyphens, trimmed.  Two
    seams that slugify the same are the same seam; that collision is
    deliberate, so ``Two Columns`` and ``two-columns`` do not fork.
    """
    # NORMALISE FIRST, and this is not decoration. Without it "cafe\u0301" and
    # "caf\u00e9" -- the same word, in the two forms macOS and GNU/Linux
    # respectively hand you -- slugged to "cafe" and "caf": ONE seam forking
    # into two chains depending on which machine wrote the name, each holding
    # half the history, neither saying so. Found by a normalisation test, not
    # by reading the code.
    #
    # NFKD decomposes an accented letter into base + combining mark; dropping
    # the marks folds it to its base rather than deleting it, so "cafe\u0301
    # notes" becomes "cafe-notes" and not "caf-notes". Better for every Latin
    # script with diacritics -- French, Spanish, Polish, Czech, Vietnamese --
    # and it leaves non-Latin scripts to the handle branch below.
    folded = "".join(c for c in unicodedata.normalize("NFKD", seam.strip())
                     if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    if not s:
        # A seam written entirely in a non-Latin script -- Japanese, Cyrillic,
        # Greek, Hebrew, Arabic, Thai, Chinese, Korean -- has no ASCII
        # alphanumerics, and the first version of this function raised
        # ValueError on it. That meant a user could not name a note in their
        # own language, which is not a small bug: it is this store deciding
        # whose memory is welcome, and it is the same fault as store rule 4
        # wearing an encoding instead of a category.
        #
        # The ASCII restriction earns its place for a different reason -- these
        # become directory names on filesystems with wildly different
        # normalisation rules (NFC vs NFD, case folding, and Windows' own
        # reserved set), and a name that round-trips on one host and not
        # another is a seam that silently forks. So the fix is not to widen the
        # character class; it is to give such a seam a stable ASCII HANDLE
        # while the real name lives, unaltered and in full, in the note's
        # `seam:` front matter where every reader already looks.
        #
        # Stable: the same seam always produces the same handle, on every host,
        # forever. Collision-resistant: 12 hex digits of sha256 over the NFC
        # form. Honest: the `n-` prefix says "this handle was generated", so
        # nobody mistakes it for something a human chose.
        digest = hashlib.sha256(
            unicodedata.normalize("NFC", seam.strip()).encode("utf-8")
        ).hexdigest()[:12]
        if not seam.strip():
            raise ValueError(
                "a seam needs a name: it is how you will find this note again")
        return f"n-{digest}"
    if len(s) <= 80:
        return s
    # A long seam is truncated, and truncation alone would merge two different
    # seams that share their first 80 characters into ONE chain -- reading the
    # first would serve the second's bytes. The digest of the full name keeps
    # them apart while the readable head stays readable.
    tail = hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]
    return f"{s[:71]}-{tail}"



# ---- the ASCII-digit boundary, in one place ------------------------------
#
# Found on 2026-09-15 by an independent PERL reader of this same format --
# the first second witness this project had at the server layer, and it
# produced four findings in one run that 277 Python tests did not.
#
# chainspec already settles the rule for `gen:`: "Python's int() accepts every
# one of those and the other two readers accept none, so the PERMISSIVE one
# has to be constrained, not the strict ones."  `verify.py` applies it.
# `parse_note` did not -- it used Unicode-aware `str.isdigit()`, so:
#
#   unit: １６  (FULLWIDTH)  ->  Python read 16, every other reader read 1
#   unit: \xa016\xa0 (NBSP)  ->  Python read 16, every other reader read 1
#
# Either produces THE SAME compaction inversion as the 2026-09-15 ghost
# (-437 becoming +8000) through a different door.
#
# And worse, the severe one: `'\u00b2'.isdigit()` is True while
# `int('\u00b2')` RAISES.  A single hand-edited superscript in one note's
# front matter made `buoyancy()` and `rebuild_index()` -- which walk every
# seam -- throw, taking a whole store down.  Unrepairable, too: the value is
# inside the C3 hash so it cannot be edited, and rule 1 forbids deleting it.
#
# One function, used at every site, so the rule has one home.
#: The largest integer EVERY reader in this house carries exactly -- including
#: the awk one, whose numbers are doubles.  chainspec U2 gave the mark a floor
#: and no ceiling, so `unit: 99999999999999999999` was legal by the words,
#: exact in Python's bignums, and wrapped to a NEGATIVE mark in Perl -- breaking
#: U2 inside the reader that checks U2.  A rule only one language can carry is
#: a rule that fails this project's own density test, so the bound is derived
#: from the readers rather than picked.
MAX_UNIT = 2 ** 53 - 1

_ASCII_DIGITS = frozenset("0123456789")


def ascii_int(raw, default: int = 0) -> int:
    """The integer a POSIX sh, awk or Perl reader would see.  Nothing else.

    Strips only whitespace those readers strip, then requires every remaining
    character to be an ASCII digit.  Anything else is *default*, never an
    exception: a malformed field in one note must not deny the whole store to
    its owner.
    """
    # ONLY what a POSIX sh, awk or Perl reader strips: space, tab, CR, LF.
    # NOT U+00A0 and friends. The first version of this function stripped them
    # too, out of helpfulness, and helpfulness is the entire mechanism of the
    # split it was written to close: a Python reader being kind about a value
    # that every other reader refuses is how "16" and "1" end up in two places
    # at once. The permissive reader is the one that gets constrained.
    s = str(raw if raw is not None else "").strip(" \t\r\n")
    if not s or not _ASCII_DIGITS.issuperset(s):
        return default
    try:
        return int(s)
    except ValueError:          # pragma: no cover -- unreachable by the above
        return default


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def stamp(now: _dt.datetime | None = None) -> str:
    return (now or _utcnow()).strftime(_STAMP_FMT)


def gen_filename(gen: int, self_sha: str, now: _dt.datetime | None = None) -> str:
    """``g0007-3f2a1b9c4d5e6f70.md`` -- 25 characters, spec v3.

    ``self_sha`` is sha256 of the file's own bytes (C3). There is no
    circularity: the filename is not inside the file, so the writer renders the
    text, hashes it, and names the file after the hash.

    Sortable by generation first so a plain ``ls`` walks the chain in order --
    which is the whole "human readable" requirement doing real work: the
    ordering is in the names, not in an index a reader has to trust. That is
    also why the zero padding survived the shortening while the date did not:
    the padding is what makes ``ls`` sort correctly and C2 checks it, whereas
    the date was checked by nothing. See chainspec's v3 block, "REFUSED".

    THE DATE IS GONE FROM THE NAME AND IS NOT GONE.  It is in the note's own
    ``stamp:`` front matter, which is inside the C3 hash and therefore
    tamper-evident in a way the name never was; the APPEND is separately dated
    in the receipts log; and every citation is separately dated in the citation
    log. Corwin, 2026-09-15: dates attach to ACTIONS, in a log. A filename is
    prose, and a date painted into prose looks foolish.

    ``now`` IS ACCEPTED AND UNUSED, on purpose rather than by oversight. The
    caller that has a clock is ``store.append``, which needs it for the
    ``stamp:`` FIELD in the same breath as the name; making it drop the
    argument here would have read as "the store stopped timestamping", which is
    the opposite of what happened. Removing the parameter is a separate change
    from moving the date, and mixing the two would hide one inside the other.
    FALSIFIER: if a caller ever passes ``now`` expecting it to reach the name,
    that caller is reading v2 semantics and the parameter should go.
    """
    if gen < 1:
        raise ValueError("generations are 1-based")
    return f"g{gen:0{_chainspec.GEN_PAD}d}-{self_sha[:_chainspec.HEX_LEN]}.md"


@dataclass
class Note:
    """One generation of one note.  Immutable once written."""

    seam: str
    body: str
    gen: int = 1
    by: str = "unknown"
    frm: str = "a guess"                 # pocket-mentat's From:
    would_change: str = ""               # pocket-mentat's Would-change:
    triggers: list[str] = field(default_factory=list)
    first_seen: str = ""                 # column 1 -- gen-1 filename
    prev: str = ""                       # sha256: of the previous generation
    came_from: list[str] = field(default_factory=list)
    leads_to: list[str] = field(default_factory=list)
    last_cited_at_write: str = ""        # column 2, SNAPSHOT -- log holds truth
    cited_at_write: int = 0              # ... and the exact count behind it
    unit: int = 1                        # neutral-buoyancy mark -- see `score`
    mode: str = "NOTVISIBLE"             # SEATED | JAILED | NOTVISIBLE
    stamp: str = ""
    extra: dict = field(default_factory=dict)

    # -- verdicts, in pocket-mentat's own words so a reader who knows that
    #    skill needs no new vocabulary here.
    def verdict(self) -> str:
        if not self.frm.strip():
            return "UNSOURCED"
        if not self.would_change.strip():
            return "UNFALSIFIABLE"
        if self.frm.strip().lower() in ("a source", "source"):
            return "UNNAMED-SOURCE"
        if self.frm.strip().lower() == "a guess":
            return "GUESS"
        if not self.triggers:
            return "NO-TRIGGERS"
        return "OK"


def _fm_list(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


def parse_note(text: str | bytes) -> Note:
    """Parse a generation file.  Tolerant of unknown keys -- they ride in
    ``extra`` so a newer writer's fields survive an older reader untouched.

    Reads through :func:`front_matter`, which is the same parser the verifier
    uses.  It had its own loop once, and that loop was **last**-key-wins while
    ``front_matter`` is first-key-wins as the spec requires -- so a note with a
    duplicated ``by:`` line verified perfectly while ``store.read`` reported a
    different author than the chain did.  ``by:`` is what the fence is read
    from, so the two parsers disagreeing was a way to rewrite the displayed
    author of a note without breaking a single hash.

    One set of bytes gets one parser.  Two parsers of one truth is a seam, and
    this one had already split.
    """
    if isinstance(text, str):
        text = text.encode("utf-8", errors="surrogateescape")
    fm, body_bytes = front_matter(text)
    # rstrip only. strip("\n") also removed LEADING newlines, so a body
    # beginning with one was served back shorter than it was written.
    body = normalize_body(
        body_bytes.decode("utf-8", errors="surrogateescape"))

    known = {
        "seam", "gen", "by", "from", "would-change", "triggers", "first-seen",
        "prev", "came-from", "leads-to", "last-cited-at-write", "cited-at-write",
        "unit", "mode", "stamp",
    }
    return Note(
        seam=fm.get("seam", ""),
        body=body,
        gen=ascii_int(fm.get("gen", "1"), 0) or (1 if str(fm.get("gen", "")).strip() == "" else 0),
        by=fm.get("by", "unknown"),
        frm=fm.get("from", ""),
        would_change=fm.get("would-change", ""),
        triggers=_fm_list(fm.get("triggers", "")),
        first_seen=fm.get("first-seen", ""),
        prev=fm.get("prev", ""),
        came_from=_fm_list(fm.get("came-from", "")),
        leads_to=_fm_list(fm.get("leads-to", "")),
        last_cited_at_write=fm.get("last-cited-at-write", ""),
        cited_at_write=ascii_int(fm.get("cited-at-write", "0"), 0),
        # A missing or unreadable unit is 1, never 0: 0 would divide, and a
        # note written by an older writer that never heard of `unit` must read
        # as an ordinary atom rather than as damage.
        unit=max(1, min(ascii_int(fm.get("unit", "1"), 1), MAX_UNIT)),
        mode=fm.get("mode", "NOTVISIBLE"),
        stamp=fm.get("stamp", ""),
        extra={k: v for k, v in fm.items() if k not in known},
    )


def render_note(n: Note) -> str:
    """Render a generation file.  Deterministic: same Note, same bytes.

    That determinism is load-bearing -- the chain is hashed, so a renderer that
    reordered keys would break every downstream verification for no reason.

    It is also literal: an earlier version fell back to ``stamp()`` when the
    Note had none, so two renders of one stamp-less Note differed by the clock
    and the docstring was false. A Note with no stamp is now refused.
    """
    if not n.stamp:
        raise ValueError(
            "render_note needs an explicit stamp. Defaulting to the clock "
            "would make the same Note render to different bytes on two calls, "
            "and these bytes get hashed.")
    rows = [
        ("seam", n.seam),
        ("gen", str(n.gen)),
        ("stamp", n.stamp),
        ("by", n.by),
        ("from", n.frm),
        ("would-change", n.would_change),
        ("triggers", ", ".join(n.triggers)),
        ("first-seen", n.first_seen),
        ("prev", n.prev),
        ("came-from", ", ".join(n.came_from)),
        ("leads-to", ", ".join(n.leads_to)),
        ("last-cited-at-write", n.last_cited_at_write),
        ("cited-at-write", str(n.cited_at_write)),
        ("unit", str(n.unit)),
        ("mode", n.mode),
    ]
    rows += sorted(n.extra.items())
    for k, v in rows:
        refuse_line_breaks(f"front-matter key {k!r}", str(k))
        refuse_line_breaks(f"the {k!r} value", str(v))
    head = "\n".join(f"{k}: {v}" for k, v in rows)
    return f"{_FM_OPEN}\n{head}\n{_FM_OPEN}\n{normalize_body(n.body)}\n"


# Every character that ends a line for SOME reader of these bytes: \n for
# front_matter() and awk, \r for a terminal (the rest of the value overprints
# what came before it), and the rest of str.splitlines()'s set for any reader
# that uses it -- the same set citations() was caught splitting on.
LINE_BREAKS = "\n\r\v\f\x1c\x1d\x1e\x85  "


def refuse_line_breaks(what: str, value: str) -> None:
    """A front-matter value is ONE line.  So is one column of an append-only log.

    render_note writes ``key: value`` lines, and the parser is first-key-wins,
    so a value carrying ``\\nmode: SEATED`` wrote a second ``mode:`` line ABOVE
    the real one and won: a JAILED write read back SEATED, and the chain still
    verified, because C3 hashes whatever bytes were written (B5U-007, found by a
    cold read, 2026-09-30).  Refusing is the whole fix: nothing is escaped, so
    every value that was ever legal renders to the same bytes as before.
    """
    bad = [c for c in LINE_BREAKS if c in value]
    if bad:
        raise ValueError(
            f"REFUSED: {what} contains a line break "
            f"({', '.join(repr(c) for c in bad)}). Nothing was written. A "
            "value here is one line; a line break inside it would write a "
            "second line that a reader takes for a real field or record. Put "
            "multi-line text in the note body.")


def normalize_body(body: str) -> str:
    """The single definition of a note body's bytes.

    Used by BOTH the renderer and the hasher.  They used to normalise
    differently -- ``render_note`` wrote ``body.strip()`` while ``body_sha``
    stripped only trailing newlines -- so a note whose text had one trailing
    space was written with the space removed and named with the space's hash.
    The store minted a generation that failed its own C3 immediately, and rule
    1 forbids deleting it, so the note was permanently unverifiable.

    Trailing whitespace in authored text is routine, which made this a bug that
    would have fired on ordinary use rather than on an attack.
    """
    return body.rstrip("\r\n")


def body_sha(body: str | bytes) -> str:
    """sha256 of a normalised body.

    No longer what C3 checks -- C3 hashes the whole file now (spec v2) -- but
    kept because the store still uses it to notice that a body is unchanged.

    Calls :func:`normalize_body` rather than repeating its rule. It used to
    have its own copy while the docstring of ``normalize_body`` claimed to be
    "the single definition", which was two definitions that merely agreed.
    """
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="surrogateescape")
    return hashlib.sha256(
        normalize_body(body).encode("utf-8", errors="surrogateescape")).hexdigest()


def file_sha(data: bytes) -> str:
    """sha256 of a generation file's bytes as they sit on disk (C4).

    **Bytes, not text.**  An earlier version took a ``str`` and every caller
    handed it ``read_text()``, which applies universal-newline translation --
    so a CRLF file hashed as though it were LF.  The Python reader and the
    shell reader then disagreed about the same file, and on Windows (the stated
    target platform) the store would have written files that failed its own
    verifier.  Found by an adversarial read, 2026-09-14.
    """
    if isinstance(data, str):                     # a caller that did not get
        raise TypeError(                          # the memo, stopped loudly
            "file_sha takes bytes. Passing text applies newline translation "
            "and the hash stops matching what is on disk -- which is the whole "
            "thing prev: is for. Use Path.read_bytes().")
    return hashlib.sha256(data).hexdigest()


def front_matter(data: bytes) -> tuple[dict, bytes]:
    """Parse front matter from raw bytes per the chainspec normalisation rules.

    First occurrence of a key wins; keys and values are stripped of horizontal
    whitespace; the body is returned as bytes and never decoded.  This is the
    function both the Python verifier and ``store`` read through, so that
    "what the front matter says" has one answer on this side of the fence.
    """
    lines = data.split(b"\n")
    if not lines or lines[0].strip() != b"---":
        raise ValueError("note has no front matter")
    fm: dict[str, str] = {}
    i = 1
    while i < len(lines) and lines[i].strip() != b"---":
        raw = lines[i]
        if b":" in raw:
            k, _, v = raw.partition(b":")
            key = k.strip(b" \t").decode("utf-8", "replace")
            if key not in fm:                     # first occurrence wins
                fm[key] = v.strip(b" \t\r").decode("utf-8", "replace")
        i += 1
    if i >= len(lines):
        raise ValueError("note front matter is not closed")
    return fm, b"\n".join(lines[i + 1:])


# ---------------------------------------------------------------- links

def links_in(text: str) -> list[tuple[str, str]]:
    """Every link in *text* as ``(kind, target)``.

    kind is ``wiki`` | ``scheme`` | ``bare``.  ``bare`` is the fault class and
    is returned rather than raised so a caller can report *all* of them at once
    instead of stopping at the first.
    """
    found: list[tuple[str, str]] = []
    spans: list[tuple[int, int]] = []
    for m in _WIKILINK.finditer(text):
        target = m.group(1).strip()
        if m.group(2):
            target = f"{target}|{m.group(2).strip()}"
        found.append(("wiki", target))
        spans.append(m.span())
    for m in _SCHEMED.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        found.append(("scheme", f"{m.group(1)}:{m.group(2)}"))
        spans.append(m.span())
    for m in _WIN_ABS.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        found.append(("winbare", m.group(1)))
        spans.append(m.span())
    for m in _BARE_ABS.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        found.append(("bare", m.group(1)))
    return found


def check_link(kind: str, target: str) -> tuple[str, str]:
    """``(verdict, why)`` for one link.

    OK          resolvable anywhere the store is mounted
    PINNED      names a host explicitly -- legal, and says what it costs
    FAULT       host-specific without saying so
    """
    if kind == "wiki":
        return ("OK", "note-local link")
    if kind == "bare":
        return ("FAULT",
                "absolute path with no scheme: right on one host, unresolvable "
                "elsewhere, and the bytes do not say which host")
    if kind == "winbare":
        return ("FAULT",
                "a Windows drive or UNC path with no host named: it resolves "
                "on one machine and nowhere else. Write it as "
                f"<host>:{target.replace(chr(92), '/')} if you mean it.")
    scheme, _, rest = target.partition(":")
    if scheme in SCHEMES:
        return ("OK", f"{scheme}: resolves per host")
    if len(scheme) == 1 and scheme.isalpha():
        # "C:/Users/..." -- a drive letter, not a host name. Waving this
        # through as PINNED was the checker calling a drive a machine.
        return ("FAULT",
                f"{scheme}: is a drive letter, not a host. A drive says which "
                "disk, never which machine; write <host>:" + target)
    return ("PINNED", f"pinned to host {scheme!r}; portable only where that host is")


# ---------------------------------------------------------------- pressure

def pressure(cited_at_write: int, citations: list[str]) -> int:
    """Citations recorded since the head generation was written.

    A **count**, not a clock comparison, and the reason is a bug this store's
    own tests caught: stamps are second-resolution, so a citation recorded in
    the same second as the write compared equal to it and vanished. Pressure
    read 0 while three citations sat in the log.

    Comparing timestamps was the wrong instrument anyway. The question is "how
    many citations has this note collected since it was last revised", and the
    head generation can simply record how many there were when it was written.
    Subtraction is exact, monotonic, and immune to clock resolution, clock
    skew, and a log line written out of order.

    ``last-cited-at-write`` stays in the front matter beside it -- the count is
    what the gauge subtracts, the stamp is what a human reads.
    """
    n = len(citations) - int(cited_at_write or 0)
    if n < 0:
        # Impossible in an append-only log, therefore PROOF that lines were
        # removed. `max(0, ...)` used to swallow it, which made a note whose
        # citation history had been truncated indistinguishable from a healthy
        # note nobody has cited. The negative number is the signal; callers
        # report it rather than clamping it.
        return n
    return n


# ---------------------------------------------------------------- buoyancy
#
# ORTHOGONALITY.  `pressure` is an absolute count and that is exactly right for
# what it measures: how hard a note has been leaned on since it was last
# revised.  It is the wrong instrument for ranking a whole store, and the way
# it fails is the way that hurts most.
#
# A store holds several worlds at once.  One consumer cites four hundred times
# a week; another cites three times a month and those three are the only notes
# it has.  Rank by absolute pressure and the second consumer's entire world
# sorts below the first consumer's noise -- so compaction sinks the quiet
# world wholesale, and the user who needed those three notes finds them gone
# from the top of the store.  Corwin's word for what users need is
# "availability and coherence", and absolute pressure spends the first to buy
# nothing.
#
# The fix must not introduce a taxonomy (store rule 4): I may not label a seam
# "personal" or "infra" or anything else and rank within the label.  So the
# context is DERIVED rather than declared, from a fact the citer recorded about
# ITSELF at citation time -- the ``by`` column of the citation log.  Who cited
# is not what the note is about.  That distinction is rule 4's line, and it is
# the whole reason this is implementable without deciding anything on a user's
# behalf.
#
#   world(c)  = the seams citer c has cited
#   scale(c)  = the lower median pressure across world(c), floored at 1
#   lift(s)   = max over c citing s of pressure(s) / scale(c)
#
# "The most-leaned-on thing in somebody's world floats, however small that
# world is."  A store with one citer degenerates to the old global ranking,
# which is the correct no-op for the simple case.
#
# TWO CHOICES MADE FOR THE DENSITY TEST, not for elegance:
#
#   * LOWER MEDIAN, not the mean of the two middle values.  The lower median is
#     ``sorted[(n-1)//2]`` -- an integer, exact, and four lines in awk, perl or
#     sh.  A mean-of-middles introduces a half and therefore a float, and a
#     float is where three independent readers stop agreeing.
#   * LIFT IN THOUSANDTHS, as integer floor division, not a ratio.  Float
#     division is not bit-identical across languages and this number is
#     compared between readers.  ``(pressure * 1000) // scale`` is exact
#     everywhere that has integers.
#
# WHAT THIS IS NOT.  It does not compact anything and it must not.  Corwin:
# meantcached and poly together "are [not] a 'waldo' for perfect semaphore
# structure, even with linked list and fort/palace techniques" -- they are a
# pipeline that helps C4 work the problem continuously.  So this reports the
# number AND the arithmetic that produced it (scale, and which citer supplied
# it), and something with judgement decides.  A gauge that acts is not a gauge.

def lower_median(values: list[int]) -> int:
    """Exact, integer, and the same in every language that can sort."""
    if not values:
        return 0
    s = sorted(values)
    return s[(len(s) - 1) // 2]


def lift(pressure_by_seam: dict, citers_by_seam: dict) -> dict:
    """Pressure made orthogonal to how busy each citer's world is.

    Returns ``{seam: {"pressure", "lift_milli", "scale", "by", "cohorts"}}``.

    ``lift_milli`` is thousandths: 1000 means "exactly the median of the
    busiest world that cites it", 3000 means "three times that median".
    """
    world: dict = {}
    for seam, cs in citers_by_seam.items():
        for c in cs:
            world.setdefault(c, []).append(seam)

    scale = {c: max(1, lower_median([int(pressure_by_seam.get(s, 0))
                                     for s in seams]))
             for c, seams in world.items()}

    out = {}
    for seam, p in pressure_by_seam.items():
        cs = sorted(citers_by_seam.get(seam, ()))
        if not cs:
            # Never cited by anyone: no world to be relative to. Report the
            # absence rather than a confident zero that looks like a ranking.
            out[seam] = {"pressure": int(p), "lift_milli": 0, "scale": 0,
                         "by": "", "cohorts": [],
                         "why": "no citer has ever recorded using this seam"}
            continue
        if p < 0:
            # Negative pressure is proof the log lost lines. Ranking damage is
            # meaningless; say so and let the damage-first sort carry it.
            out[seam] = {"pressure": int(p), "lift_milli": 0, "scale": 0,
                         "by": "", "cohorts": cs,
                         "why": "DAMAGED -- citation log is short; lift not computed"}
            continue
        # L3 tie-break: ascending bytewise. `cs` is already sorted and `max`
        # returns the FIRST maximal element, so the key must carry the lift
        # ALONE -- putting `c` in the key took the largest name instead of the
        # smallest, which is the split the first conformance run found.
        best_c = max(cs, key=lambda c: (int(p) * 1000) // scale[c])
        out[seam] = {"pressure": int(p),
                     "lift_milli": (int(p) * 1000) // scale[best_c],
                     "scale": scale[best_c],
                     "by": best_c,
                     "cohorts": cs}
    return out


def trunc_div(n: int, d: int) -> int:
    """Integer division TRUNCATED TOWARD ZERO, per chainspec U3.

    Python's ``//`` floors toward negative infinity; awk, Perl, C and POSIX sh
    all truncate toward zero.  ``score`` goes negative by design, so the two
    disagree exactly where this store is most often read, and the spec follows
    the majority rather than making four readers correct for one.

        (-7 * 1000) // 3   == -2334      Python's floor
        trunc_div(-7000, 3) == -2333     everybody else, and the spec
    """
    q = abs(n) // abs(d)
    return -q if (n < 0) != (d < 0) else q


def score(pressure_now: int, unit: int) -> int:
    """Neutral buoyancy in thousandths.  chainspec U1-U4.

    -1000 = nothing has leaned on it.  0 = neutral, carrying exactly what it
    was built to carry.  +1000 = ACT, carrying twice that.
    """
    u = max(1, int(unit or 1))                       # U2
    return trunc_div((int(pressure_now) - u) * 1000, u)   # U3


# ---------------------------------------------------------------- context
#
# WHERE A BUOYANCY CONTEXT COMES FROM.  Corwin, 2026-09-16, answering the
# question this store left open since the cohort ranking was built:
#
#     "grouping context for buoyancy from the top (e.g. task/project) toward
#      the lowest (back toward root from a file system standpoint) to reuse
#      existing taxonomy pathing ... placing new meanings at seams that split
#      on the way up and otherwise new branches ... toward the lowest
#      registered path/component element that exists already or must already
#      be created and which can directly support the new meanings (or support
#      the assertion that a seam has multiple confusable and so is really a
#      seam)."
#
# The answer is that a context is NOT a label anybody assigns.  It is the PATH
# the thing already has.  That matters for two reasons, and the second is the
# one that makes it buildable:
#
#   1. It reuses taxonomy that exists.  A project/program/task tree is already
#      a grouping somebody maintained for other reasons, and it is right for
#      the same reason `by` was right for the citer cohorts: it is a fact the
#      writer recorded about their own work, not a judgement this store made
#      about what a note is ABOUT.  Store rule 4 survives intact -- a path is
#      form, not subject.
#   2. It walks DEEPEST FIRST.  A new meaning pins at the lowest element that
#      can carry it, and only splits upward when it must.  So the contexts of
#      `mentat/persona/voice` are that, then `mentat/persona`, then `mentat` --
#      narrowest first, each one a real cohort a seam can be ranked inside.
#
# A SEAM, in his sense, is a path element with more than one confusable
# meaning under it.  This module cannot decide that -- deciding it is exactly
# the judgement the store may not make -- but it can COUNT it, and a count is
# what turns "that feels like a seam" into an argument.  `split_points` reports
# where one element carries several distinct children, which is the evidence
# for the assertion, not the assertion.


def path_contexts(seam: str, sep: str = "/") -> list[str]:
    """The seam's own path, deepest first, then each ancestor up toward root.

    ``"mentat/persona/voice"`` -> ``["mentat/persona/voice",
    "mentat/persona", "mentat"]``.  A seam with no separator is its own only
    context, which is the correct answer and not a degenerate one: a flat name
    has a taxonomy of exactly one element.
    """
    parts = [p for p in str(seam).split(sep) if p.strip()]
    return [sep.join(parts[:i]) for i in range(len(parts), 0, -1)]


def split_points(seams: list[str], sep: str = "/") -> dict:
    """Every path element carrying more than one distinct child.

    Evidence for "this element is a seam", never the verdict.  The store does
    not get to decide that two meanings under one name are CONFUSABLE -- that
    is a reading, and readings belong to whoever is doing the work.  What it
    can do is hand them the count, which is the difference between an argument
    and a feeling.
    """
    kids: dict = {}
    for s in seams:
        parts = [p for p in str(s).split(sep) if p.strip()]
        for i in range(1, len(parts)):
            kids.setdefault(sep.join(parts[:i]), set()).add(parts[i])
    return {k: sorted(v) for k, v in sorted(kids.items()) if len(v) > 1}
