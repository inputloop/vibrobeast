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

"""store -- an archive-only, granular, human-readable memory seat.

Five rules, and every one of them is a refusal:

1. **Nothing is ever overwritten, simplified, or deleted.**  A write mints a
   new generation file beside the old ones.  There is no code path in this
   module that opens an existing note for writing, and that is checked by a
   test rather than promised by a comment.

2. **The index is a cache, never the record.**  Every forward pointer this
   store serves can be rebuilt from the note files alone (``rebuild_index``).
   The backward pointers live in the bytes as a hash chain, so the record is
   not merely as recoverable as a packed b-tree -- it is *strictly stronger*,
   because a b-tree's internal pointers are not self-verifying and a hash chain
   is.  Tamper with any generation and every later ``prev:`` stops matching.

3. **The mode is always said out loud.**  Every read and every write returns
   ``SEATED`` | ``JAILED`` | ``NOTVISIBLE``.  A write while JAILED is refused
   unless the caller says ``allow_jailed`` in so many words, and when it is
   allowed the generation carries ``mode: JAILED`` in its front matter forever,
   so no later reader can mistake a jailed write for a seated one.

   This is the rule Corwin asked for in the plainest terms: *"it would be
   incorrect to silently resume using project-jailed memory while I think
   things are safely landing to a semaphored multi-consumer async friendly
   store."*  Silence is the failure.  The store has no silent path.

4. **The store has no opinion about subject.**  Every tool's observable
   behaviour is a function of a note's *bytes*, never of what those bytes are
   about.  The store MAY judge the **form** of a reference -- ``link_check``
   refuses a bare absolute path because such a path cannot be followed from
   another machine, which is a fact about paths and the same fact whoever wrote
   the note.  The store may NEVER judge the **subject** of a note, because
   there is no reading of "what is this about" that is a fact about bytes.

   Rule 4 exists because on 2026-09-14 I looked at a note on Corwin's desk,
   decided it was "personal admin ... not system content", and stopped.  It was
   notes for his client.  His correction went past the fact to the design:
   *"we can't decide what kinda memory our MCP or whatever tools will transact
   in ... We have to be careful that our views about what is useful to what
   don't leak into what we are making"* -- and, flatly, *"I don't have a
   separate Claude account I can use for memories about personal things."*

   Checked by ``tests/test_no_taxonomy.py``, which runs five deliberately
   unalike bodies through the whole tool surface and fails if any observable
   differs.  Its prove-red case injects the forbidden behaviour to show the
   check can go red.

   NOT covered, named so it is not mistaken for covered: an *iT* may still
   refuse to work with a given memory.  That is a persona-layer refusal, it is
   visible, and the user may reject it.  Rule 4 binds the store, which must
   carry whatever it is handed.

   ON THE EXCEPTION, 2026-09-14.  I asked him to construct a case where the
   store genuinely must read subject matter, because I could not.  He could not
   either -- yet: *"let's protect this 'not yet a requirement' while the
   appearance of absence persists. I can't state the exception quite yet, if
   there is an obvious/important one."*  So this is ABSENCE OF EVIDENCE after
   an attempt by both parties, with the receipt, and not a proof that no
   exception exists.  The slot stays open and empty.  If one turns up, rule 4
   earns a STATED exception, which is a different thing from a quiet one -- and
   the reason to write this paragraph now is that a rule nobody can break looks
   identical to a rule nobody has tried to break.

5. **Nothing is canonical because it was written.**  A note becomes canonical
   when somebody who did NOT write it BLESSES it, naming the exact bytes and
   what they checked.

   This is the two-witness doctrine turned from a habit into an access rule.
   Corwin, 2026-09-15, on his own register page: *"Keeper's pen to bless;
   letters marked ? still need confirming."*  A bless is his existing act --
   the moment a proposal stops being a proposal -- and the thing that makes it
   worth anything is that the blesser is a second party.  ``bless`` therefore
   REFUSES when the blesser is the generation's own author, and the refusal is
   the feature: an author blessing their own work is one witness signing twice.

   Three properties, each with a reason:

   * A bless names the SHA of the exact bytes.  Blessing does not inherit
     forward -- generation 3 is not blessed because generation 2 was, because
     the whole point is that somebody looked at THESE bytes.
   * A bless records WHAT WAS CHECKED, in words, and refuses an empty one.  "I
     read it" is not a check; a bless with no stated check is a rubber stamp
     with a nicer name.
   * Blessings are append-only and live outside the notes, for the same reason
     ``last-cited`` does: recording one must not mint a generation, or the act
     of endorsing would change the thing endorsed.

   A note that has never been blessed is not suspect -- most notes never will
   be.  It is simply UNBLESSED, and the store says which, because the
   difference between "nobody has checked this" and "somebody did" is exactly
   the difference this project keeps discovering it needs.

On the fence
------------
The house rule is "never edit a note another session wrote."  Here that rule
needs no enforcement code, because rule 1 already makes editing impossible: a
second session can only ever *append a generation*, and the generation it
appends records its own ``by:``.  The fence stops being a promise and becomes a
property of the layout.  ``chain()`` reports where authorship changed hands so a
reader can see the seam without being told about it.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import dl2
from . import shipdate as _shipdate
from . import chainspec as _chainspec
from .chainspec import GEN_NAME

# %NAME% -- the Windows environment-variable form, matched as a shape
# rather than by counting per-cent signs.
_WINVAR = re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%")
# A bare $NAME, unexpanded. Cheap to check and the same failure shape.
_SHVAR = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")

__all__ = [
    "SEATED", "JAILED", "NOTVISIBLE", "Store", "StoreError", "Jailed",
    "Semaphore", "SemaphoreBusy",
]

SEATED = "SEATED"
JAILED = "JAILED"
NOTVISIBLE = "NOTVISIBLE"

# Locks older than this are stale: the holder died without lowering.  Ten
# minutes is longer than any single tool call this server makes and shorter
# than a human coffee break, so a stale lock never blocks the next session for
# a whole sitting.  Derived from the call budget, not picked.
STALE_LOCK_SECONDS = 600


class StoreError(RuntimeError):
    pass


class Jailed(StoreError):
    """A write was attempted against a jailed store without saying so."""


class SemaphoreBusy(StoreError):
    pass


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _one_line(what: str, value) -> None:
    """dl2.refuse_line_breaks, reported as the store's own refusal."""
    try:
        dl2.refuse_line_breaks(what, str(value))
    except ValueError as exc:
        raise StoreError(str(exc)) from None


@dataclass
class Semaphore:
    """A named, multi-consumer advisory signal.

    Raising is cheap and anyone may do it.  Lowering is the named ceremony and
    the lowerer must say the ceremony word, which is how a signal stops being
    something a passing session clears by accident.
    """

    path: Path
    name: str

    def raise_(self, why: str, by: str) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = f"{dl2.stamp()}\tRAISE\t{by}\t{why}\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return {"name": self.name, "state": "RAISED", "why": why, "by": by}

    def lower(self, ceremony: str, by: str) -> dict:
        if not ceremony.strip():
            raise StoreError(
                f"semaphore {self.name!r}: lowering is a named ceremony; "
                "pass the ceremony word that discharges it")
        if not self.path.exists():
            return {"name": self.name, "state": "NOT-RAISED"}
        line = f"{dl2.stamp()}\tLOWER\t{by}\t{ceremony}\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return {"name": self.name, "state": "LOWERED", "ceremony": ceremony,
                "by": by}

    def state(self) -> dict:
        if not self.path.exists():
            return {"name": self.name, "state": "NOT-RAISED", "log": []}
        rows = [ln.split("\t") for ln in
                self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        last = rows[-1] if rows else None
        st = "NOT-RAISED"
        if last:
            st = "RAISED" if last[1] == "RAISE" else "LOWERED"
        return {"name": self.name, "state": st, "log": ["\t".join(r) for r in rows]}


class _Lock:
    """O_EXCL lockfile with a stale-age escape.  Context manager.

    Three defects an adversarial read found in the first version, all fixed
    here, all of the same family -- *acting on a file without checking it is
    still the file you measured*:

    1. ``__exit__`` unlinked unconditionally.  A holder whose lock had been
       broken as stale would, on finishing, delete the **new** holder's lock.
       Now the token written at acquisition is read back before unlinking, and
       a lock that is not ours is left alone.
    2. Two processes could both judge one lock stale, both unlink, and both
       take it.  The second unlink destroyed the first's fresh lock.  Now the
       break is conditional on the file still having the mtime that was
       measured, and the winner is whoever's ``O_EXCL`` succeeds.
    3. ``stat()`` and ``read_text()`` between the failed open and the age check
       were unguarded, so a holder releasing in that window produced a bare
       ``FileNotFoundError`` instead of a retry.

    The cost of (1) and (2) was not theoretical: two writers past a broken lock
    both computed the same next generation number and wrote two files claiming
    to be it, leaving a chain that no rule in this store may repair, because
    repairing it would mean deleting one.
    """

    def __init__(self, path: Path, by: str, receipt=None):
        self.path = path
        self.by = by
        self._token = ""
        self._held = False
        self._receipt = receipt

    def __enter__(self) -> "_Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            self._token = (f"{self.by}\tpid={os.getpid()}\t"
                           f"host={socket.gethostname()}\t{dl2.stamp()}\t"
                           f"{os.urandom(8).hex()}\n")
            try:
                fd = os.open(str(self.path),
                             os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                try:
                    st = self.path.stat()
                    holder = self.path.read_text(encoding="utf-8").strip()
                except OSError:
                    continue          # released underneath us; try again
                age = time.time() - st.st_mtime
                if age <= STALE_LOCK_SECONDS:
                    raise SemaphoreBusy(
                        f"store is locked by another consumer ({holder}); "
                        f"age {age:.0f}s < stale {STALE_LOCK_SECONDS}s")
                # Stale.  Break it only if it is still the lock we measured --
                # otherwise another process got there first and this unlink
                # would destroy their fresh lock.
                try:
                    if self.path.stat().st_mtime_ns != st.st_mtime_ns:
                        continue
                    self.path.unlink()
                except OSError:
                    continue
                if self._receipt:
                    # Leave the evidence. The unlink destroys the only other
                    # record that a lock was broken and whose it was.
                    self._receipt("LOCK-BROKEN",
                                  f"{self.path.name}\tage={age:.0f}s\twas={holder}")
                continue
            else:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(self._token)
                self._held = True
                return self
        raise SemaphoreBusy(
            "could not acquire the store lock after three attempts -- another "
            "consumer is contending for it. Nothing was written.")

    def __exit__(self, *exc) -> None:
        if not self._held:
            return
        self._held = False
        try:
            if self.path.read_text(encoding="utf-8") != self._token:
                # Somebody broke our lock as stale and took it. Theirs now;
                # deleting it would be the bug this check exists to prevent.
                return
            self.path.unlink()
        except OSError:
            pass


@dataclass
class Store:
    """A memory seat rooted at *root*.

    ``jail_root`` is the project-local fallback.  If it is used at all, the
    store's mode is JAILED and every result says so.
    """

    root: Path
    by: str = "unknown"
    jail_root: Path | None = None

    # ------------------------------------------------------------- layout
    # Every layout path hangs off `active`, never off `root`.  See mode().
    @property
    def notes(self) -> Path:
        return self.active / "notes"

    @property
    def cited(self) -> Path:
        return self.active / "cited"

    @property
    def index(self) -> Path:
        return self.active / "index" / "dl2.tsv"

    @property
    def locks(self) -> Path:
        return self.active / ".locks"

    @property
    def semaphores(self) -> Path:
        return self.active / "semaphores"

    @property
    def blessed(self) -> Path:
        return self.active / "blessed"

    @property
    def receipts(self) -> Path:
        return self.active / "receipts"

    # --------------------------------------------------------------- mode
    def mode(self) -> str:
        """SEATED / JAILED / NOTVISIBLE.  Pure: computes, never assigns.

        Recomputed on every call rather than cached, because a mount can go
        away mid-session and a cached SEATED is exactly the silent lie rule 3
        exists to prevent.

        **A seat root that does not exist is NOT seated.**  An earlier version
        answered SEATED whenever the root's *parent* was writable, reasoning
        that absence is not unreachability.  That is true of a first run and
        false of a typo, and the two are indistinguishable from here -- so
        ``MENTCACHED_SEAT=/f/claude/seaat`` answered SEATED, created an empty
        store and served "I have no note about that", which is strictly worse
        than JAILED because JAILED at least says something is wrong.  Creating
        a seat is now a deliberate act: ``ensure(create=True)``.

        **And it must not reassign ``self.root``.**  An earlier draft did --
        on falling back it set ``self.root = self.jail_root`` -- and the store's
        own ``--prove-red`` caught it on the first run: the *second* call to
        ``mode()`` inside a single write then found a perfectly good directory
        at ``self.root`` and answered SEATED.  The write landed in the jail and
        the receipt said the seat.

        That is the whole failure this class exists to prevent, reproduced by
        the code meant to prevent it, and it is a textbook seam: "which mode
        are we in" and "which root are we using" are two representations of one
        truth, and collapsing them into one mutable field let them split
        silently.  They are now derived from one function that assigns nothing.
        """
        raw = str(self.root)
        if not self.root.is_absolute():
            # ".." existed and answered SEATED, rooting the store in the parent
            # of whatever directory the process happened to start in. A seat is
            # a place, not a place relative to wherever we were launched.
            return NOTVISIBLE
        if not raw.strip() or raw.strip() in (".", "./"):
            # An empty seat path becomes Path('.') and answers SEATED for the
            # process's working directory -- exactly the silent substitute this
            # class exists to prevent, arrived at by an unset variable.
            return NOTVISIBLE
        if "${" in raw or _WINVAR.search(raw) or _SHVAR.search(raw):
            # An unexpanded ${MENTCACHED_SEAT} or %MENTCACHED_SEAT% is not a
            # path. The Windows form used to be tested with
            # `"%" in raw.strip("%")`, which strips the very delimiters it is
            # looking for -- so %VAR% passed, a directory by that literal name
            # was created, and it was reported as the semaphored seat. It also
            # meant any legitimate path containing a per-cent sign was called
            # NOTVISIBLE. A regex for the actual shape does both jobs.
            # The plugin's own
            # .mcp.json contains that literal, so a host that does not expand
            # it used to hand us the string -- and an earlier mode() answered
            # SEATED and created a directory literally named "${MENTCACHED_SEAT}"
            # in the process's cwd, then reported it as the semaphored seat.
            return NOTVISIBLE
        if self.root.is_dir() and os.access(self.root, os.W_OK):
            return SEATED
        if self.jail_root is not None and self.jail_root.is_dir():
            return JAILED
        return NOTVISIBLE

    @property
    def active(self) -> Path:
        """The root actually in use, derived from mode() and never stored."""
        return self.jail_root if self.mode() == JAILED else self.root

    def ensure(self, create: bool = False,
               make_parents: bool = False) -> "Store":
        """Open the seat, creating it only if told to.

        *make_parents* relaxes one guard and only one: normally the seat's
        PARENT must already exist, so that a typo in a middle component --
        ``~/Documnets/memory`` -- cannot quietly build a whole tree nobody
        asked for and then serve it as memory.  That guard is right for a path
        the USER named.

        It is wrong for a path this program chose.  A default location has no
        typo to be wrong about, so refusing to make its parent just means the
        first run fails for no reason.  Callers pass ``make_parents=True``
        exactly when they picked the path themselves -- see
        ``mentcached._roots``, which returns that fact as its third value.

        We may create a path we chose.  We may never create a path you chose.
        """
        m = self.mode()
        if m == NOTVISIBLE:
            raw = str(self.root)
            parent_ok = (self.root.parent.is_dir()
                         and os.access(self.root.parent, os.W_OK))
            if make_parents and not parent_ok:
                # Only reachable for a path we chose; find the nearest existing
                # ancestor and require THAT to be writable, so a read-only home
                # still fails loudly rather than half-building a tree.
                anc = self.root.parent
                while not anc.is_dir() and anc != anc.parent:
                    anc = anc.parent
                parent_ok = anc.is_dir() and os.access(anc, os.W_OK)
            creatable = (create and "${" not in raw and not _WINVAR.search(raw)
                         and raw.strip() not in ("", ".", "./")
                         and parent_ok)
            if creatable:
                try:
                    self.root.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    # A regular file or a dangling symlink at the seat root
                    # raised FileExistsError straight past the message written
                    # for exactly this case -- and mentcached._open catches only
                    # StoreError, so it reached the caller as a bare traceback.
                    raise StoreError(
                        f"the seat root {self.root} exists but is not a "
                        f"directory ({type(exc).__name__}: {exc}). Nothing was "
                        "read or written. Move it aside, or point "
                        "MENTCACHED_SEAT somewhere else.") from exc
                m = self.mode()
            if m == NOTVISIBLE:
                raise StoreError(
                    "seat is NOTVISIBLE: neither the seat root nor a jail root "
                    f"is reachable from here ({self.root}). Nothing was read or "
                    "written, and no fallback was chosen for you.\n"
                    + ("The path still contains an unexpanded ${...} -- the "
                       "host did not substitute the environment variable.\n"
                       if "${" in str(self.root) else "")
                    + ("The directory was created and the seat is STILL not "
                       "usable -- check permissions.\n" if creatable else "")
                    + "If this is a first run and the seat should be created "
                      "here, say so: seat_open with create=true.")
        for d in (self.notes, self.cited, self.index.parent, self.locks,
                  self.semaphores, self.receipts, self.blessed):
            d.mkdir(parents=True, exist_ok=True)
        return self

    # -------------------------------------------------------------- reads
    def seams(self) -> list[str]:
        if not self.notes.is_dir():
            return []
        return sorted(p.name for p in self.notes.iterdir() if p.is_dir())

    def generations(self, seam: str) -> list[Path]:
        d = self.notes / dl2.slugify(seam)
        if not d.is_dir():
            return []
        # Ordered by the INTEGER in the name, and shape-matched, so this
        # agrees with all three verifiers rather than with string sort.
        # "sorted by filename == sorted by generation" held only up to g9999:
        # as strings, g10000 sorts before g9999.
        out = []
        for p in d.iterdir():
            if not p.is_file() or p.is_symlink():
                continue
            m = GEN_NAME.match(p.name)
            if m:
                out.append((int(m.group(1)), p))
        return [p for _, p in sorted(out, key=lambda t: t[0])]

    def strays(self, seam: str) -> list[str]:
        """Files sitting in a seam directory that are not generations.

        The chain spec says to ignore anything whose name is not a generation,
        and all four readers do -- otherwise one stray file would stop every
        read of a seam. But ignored is not the same as invisible: a file nobody
        put there on purpose should be reported once, by name, rather than
        quietly tolerated forever.
        """
        d = self.notes / dl2.slugify(seam)
        if not d.is_dir():
            return []
        out = []
        for p in d.iterdir():
            if not GEN_NAME.match(p.name):
                out.append(p.name)
            elif not p.is_file() or p.is_symlink():
                # Gen-SHAPED but not a generation: every reader skips it
                # because it is not a regular file, and the name-based filter
                # above would skip it too -- so a symlink to /etc/passwd sat in
                # a notes directory permanently unnamed by anything.
                out.append(p.name + "  (gen-shaped, but not a regular file)")
        return sorted(out)

    def head(self, seam: str) -> Path | None:
        gens = self.generations(seam)
        return gens[-1] if gens else None

    def read(self, seam: str, gen: int | None = None) -> dict:
        """Read a generation (default: the head).  Never mutates anything."""
        self.ensure()
        gens = self.generations(seam)
        if not gens:
            return {"mode": self.mode(), "seam": seam, "found": False,
                    "note": None, "pressure": 0,
                    "say": f"no note named {seam!r} in this store"}
        # Select by the INTEGER the name carries, not by a rendered prefix.
        # This used to be `p.name.startswith(f"g{gen:04d}-")`, which is a
        # SECOND, weaker copy of C2's rule wearing an f-string. It agreed with
        # GEN_NAME only while every name was padded to exactly four digits, so
        # a five-digit generation was unreachable through `read(gen=10000)`
        # while `generations()` listed it happily -- the note was on disk, in
        # the index, and could not be opened. Parsing it the way every reader
        # in the house parses it is both shorter and the only version that
        # cannot drift.
        path = gens[-1] if gen is None else next(
            (p for p in gens
             if (_m := GEN_NAME.match(p.name)) and int(_m.group(1)) == gen),
            None)
        if path is None:
            raise StoreError(f"{seam}: no generation {gen}")
        # Bytes, decoded without newline translation: read_text() applies
        # universal newlines, so the text served back did not hash to the
        # filename -- the exact hazard file_sha raises TypeError about.
        text = path.read_bytes().decode("utf-8", errors="surrogateescape")
        note = self._parse(path)
        cites = self.citations(seam)
        stray = self.strays(seam)
        shown = stray[:5]
        return {
            "mode": self.mode(),
            "seam": seam,
            "found": True,
            # The COUNT always, the first few by name, never the whole list:
            # a seam with twenty thousand strays produced a 360 KB payload on
            # every single read, recomputed each time.
            **({"strays": shown, "stray_count": len(stray),
                "say": (f"{len(stray)} file(s) in this seam's directory are not "
                        "generations and were ignored by every reader: "
                        + ", ".join(shown)
                        + (f" (+{len(stray) - len(shown)} more)"
                           if len(stray) > len(shown) else "")
                        + ". Nothing here removes them; move them out by hand.")}
               if stray else {}),
            "file": path.name,
            "gen": note.gen,
            "generations": len(gens),
            "note": text,
            "verdict": note.verdict(),
            # Resolve the gen-1 convention for the caller, so nobody outside
            # this module has to know about it.
            "first_seen": note.first_seen or gens[0].name,
            "last_cited": cites[-1] if cites else "",
            "pressure": dl2.pressure(note.cited_at_write, cites),
            **({"pressure_say":
                "NEGATIVE pressure: the citation log has fewer lines than this "
                "generation recorded seeing. An append-only log cannot shrink, "
                "so this is evidence that lines were removed, not a count."}
               if dl2.pressure(note.cited_at_write, cites) < 0 else {}),
            "by": note.by,
            "written_mode": note.mode,
        }

    def stamp(self) -> str:
        """The date this CONTEXT is at -- from a file, not from the host clock.

        Corwin, 2026-09-15: *"When we put a date into a file (or filename) it
        should come from a file ... having a running conception of shipboard
        date is potentially quite helpful, and I also find it helpful to think
        about that date as I do the high-water mark VERSION that a project --
        or some other context! -- could have."*

        See ``shipdate``.  The host clock's only job is populating the file the
        first time, and that leaves a receipt.
        """
        try:
            s, source = _shipdate.ensure(self.active, by=self.by)
        except _shipdate.ShipdateError:
            # A malformed DATE file must not deny somebody their whole store.
            # Fall back to the clock, loudly, in the receipts.
            s, source = _shipdate.fmt(_shipdate.now_from_host()), "host-clock-fallback"
        if source != "file":
            self._receipt("SHIPDATE", f"{s}\t{source}")
        return s

    def citations(self, seam: str) -> list[str]:
        """One entry per RECORD in the log, and a record ends at \\n.

        Two faults an independent Perl reader found here on 2026-09-15, both
        of which move `pressure` -- the number that drives the compaction
        queue -- without anybody tampering with anything:

        1. ``str.splitlines()`` splits on U+000B, U+000C, U+001C-U+001E,
           U+0085, U+2028 and U+2029 as well as \\n.  ``cite()`` writes \\n and
           nothing else, and the ``where`` column is caller-supplied text, so
           one citation mentioning a line separator became TWO citations.
        2. ``read_text(encoding="utf-8")`` raises on one bad byte, and this
           method is called for every seam by ``buoyancy``.  Every other
           decode in dl2 uses ``surrogateescape``; this was the one that did
           not.  chainspec's own words: "A body that is not valid UTF-8 is
           not an error.  Hash the bytes."
        """
        p = self.cited / f"{dl2.slugify(seam)}.log"
        if not p.is_file():
            return []
        out = []
        for raw in p.read_bytes().split(b"\n"):
            if not raw.strip():
                continue
            ln = raw.decode("utf-8", errors="surrogateescape")
            out.append(ln.split("\t", 1)[0])
        return out

    def citers(self, seam: str) -> list[str]:
        """The distinct ``by`` values in this seam's citation log.

        A fact each citer recorded about ITSELF, never a label this store put
        on the note. That is what keeps the orthogonal ranking in ``buoyancy``
        on the right side of rule 4.
        """
        p = self.cited / f"{dl2.slugify(seam)}.log"
        if not p.is_file():
            return []
        out = []
        for raw in p.read_bytes().split(b"\n"):
            if not raw.strip():
                continue
            ln = raw.decode("utf-8", errors="surrogateescape")
            cols = ln.split("\t")
            who = cols[1].strip() if len(cols) > 1 else ""
            if who and who not in out:
                out.append(who)
        return sorted(out)

    def _parse(self, path: Path) -> dl2.Note:
        """Parse a generation, naming the file if it will not parse.

        A foreign file dropped into a notes directory is a fault, and the
        failure must say *which file* -- "note has no front matter" with no
        path is the kind of error that sends a reader hunting through a store
        at the exact moment they need it to be legible.
        """
        try:
            # Bytes, and the same front-matter reader the verifier uses, so
            # "what the front matter says" has one answer on this side.
            return dl2.parse_note(
                path.read_bytes().decode("utf-8", errors="surrogateescape"))
        except ValueError as exc:
            raise StoreError(
                f"{path.name} is in a notes directory but is not a generation "
                f"file ({exc}). Nothing here rewrites or removes it; move it "
                "out by hand, or it will keep stopping every read of this seam."
            ) from exc

    def chain(self, seam: str) -> list[dict]:
        """Walk the generations, reporting where the chain holds and where
        authorship changed hands."""
        rows = []
        prev_sha = ""
        prev_by = ""
        for p in self.generations(seam):
            n = self._parse(p)
            want = n.prev.replace("sha256:", "")
            ok = (n.gen == 1 and not want) or (want == prev_sha)
            rows.append({
                "file": p.name, "gen": n.gen, "by": n.by, "mode": n.mode,
                "link": "OK" if ok else "BROKEN",
                "expected_prev": prev_sha[:16], "recorded_prev": want[:16],
                "hands_changed": bool(prev_by and n.by != prev_by),
            })
            prev_sha = dl2.file_sha(p.read_bytes())
            prev_by = n.by
        return rows

    # ------------------------------------------------------------- writes
    def append(self, seam: str, body: str, *, frm: str, would_change: str,
               triggers: list[str] | None = None,
               came_from: list[str] | None = None,
               leads_to: list[str] | None = None,
               unit: int | None = None,
               allow_jailed: bool = False,
               now: _dt.datetime | None = None) -> dict:
        """Mint a NEW generation.  Never touches an existing file.

        Refuses a jailed write unless *allow_jailed*; stamps the mode into the
        bytes either way.

        *unit* is the neutral-buoyancy mark (chainspec U1-U4): how much this
        item was built to carry, declared by the WRITER at intern time.  It is
        never inferred from the body -- deriving it from content would be the
        store forming an opinion about what a note is about, dressed as
        arithmetic, which store rule 4 forbids.  ``None`` inherits the previous
        generation's mark, so a revision does not silently reset a seam's
        ceiling; on generation 1 ``None`` means 1, the honest answer when the
        writer declared nothing.
        """
        # Caller text becomes front-matter LINES. render_note refuses a line
        # break too; checking here as well means a refused write leaves no
        # empty seam directory behind.
        for what, v in (("seam", seam), ("source", frm),
                        ("would_change", would_change),
                        *(("triggers", t) for t in triggers or []),
                        *(("came_from", c) for c in came_from or []),
                        *(("leads_to", x) for x in leads_to or [])):
            _one_line(what, v)
        self.ensure()
        m = self.mode()
        if m == JAILED and not allow_jailed:
            raise Jailed(
                "REFUSED: this store is JAILED -- the semaphored seat is not "
                "reachable and only the project-local fallback is. Nothing was "
                "written. Re-run with allow_jailed=true to write to the "
                "fallback; the generation will carry mode: JAILED in its front "
                "matter permanently so nobody later mistakes it for a seated "
                "write.")

        slug = dl2.slugify(seam)
        d = self.notes / slug
        d.mkdir(parents=True, exist_ok=True)

        # Pass the receipt writer, or the LOCK-BROKEN branch is dead code and
        # the unlink destroys the only record that a lock was broken.
        with _Lock(self.locks / f"{slug}.lock", self.by, self._receipt):
            gens = self.generations(seam)
            gen = len(gens) + 1
            prev = ""
            first_seen = ""
            if gens:
                prev = "sha256:" + dl2.file_sha(gens[-1].read_bytes())
                # gen 2 is where gen 1's filename first gets written down.
                first_seen = self._parse(gens[-1]).first_seen or gens[0].name
            if unit is None:
                unit = self._parse(gens[-1]).unit if gens else 1
            unit = max(1, int(unit))                      # U2
            cites = self.citations(seam)
            note = dl2.Note(
                seam=seam, body=body, gen=gen, by=self.by, frm=frm,
                would_change=would_change, triggers=triggers or [],
                first_seen=first_seen, prev=prev,
                came_from=came_from or [], leads_to=leads_to or [],
                last_cited_at_write=cites[-1] if cites else "",
                cited_at_write=len(cites),
                unit=unit,
                # An explicit `now` still wins -- the frozen fixtures and the
                # conformance writers pass one deliberately. Everything else
                # takes the CONTEXT's date from the file, never the host clock.
                mode=m, stamp=dl2.stamp(now) if now is not None else self.stamp(),
            )
            # Generation 1 leaves first-seen EMPTY, and that is the honest
            # answer rather than a missing one: under spec v2 the filename is
            # the hash of the file, and first-seen on gen 1 would name the file
            # it is written inside -- a value that changes the bytes it is
            # derived from. There is no fixed point worth chasing for a fact
            # every reader can see: **an empty first-seen on generation 1 means
            # "this file".** Generations 2+ carry gen 1's real filename, so the
            # pin a reader actually needs -- on the head of a long chain -- is
            # there and is openable.
            data = dl2.render_note(note).encode("utf-8", errors="surrogateescape")
            fname = dl2.gen_filename(gen, dl2.file_sha(data), now)
            path = d / fname
            if path.exists():                       # pragma: no cover
                raise StoreError(
                    f"refusing to overwrite {path.name}: this store never "
                    "rewrites a generation")
            # Render, hash the rendered BYTES, then name the file after them
            # (spec v2 C3). The name is not inside the file, so there is no
            # circularity -- and this is what makes the head generation's front
            # matter tamper-evident, which the body-only hash never did.
            # O_EXCL: the archive rule enforced by the kernel, not by us.
            # BINARY, and LF only. Text mode on Windows turns every \n into
            # \r\n on the way out while prev: is computed from the LF form, so
            # every generation the store wrote on its own target platform would
            # have failed its own verifier. Nothing in the container could have
            # caught that; it was found by reasoning about the platform.
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            self._receipt("APPEND", f"{slug}\tg{gen:04d}\t{fname}\tmode={m}")

        return {"mode": m, "seam": seam, "gen": gen, "file": fname,
                # gens[] here is the PRE-write list and is empty for gen 1, so
                # the gen-1 convention resolves to this file's own name.
                "first_seen": note.first_seen or fname,
                "verdict": note.verdict(),
                "say": (f"minted generation {gen} of {seam!r} while {m}"
                        + (" -- JAILED IS STAMPED IN THE BYTES" if m == JAILED else ""))}

    def cite(self, seam: str, by_whom: str, where: str) -> dict:
        """Record a citation.  Append-only; sets last-cited; moves pressure."""
        # One citation is one line. A line break in `where` wrote a second
        # record naming any citer the caller liked -- the caller-chosen citer
        # seat_cite refuses at the front door.
        _one_line("by_whom", by_whom)
        _one_line("where", where)
        self.ensure()
        self.cited.mkdir(parents=True, exist_ok=True)
        p = self.cited / f"{dl2.slugify(seam)}.log"
        line = f"{self.stamp()}\t{by_whom}\t{where}\n"
        with p.open("a", encoding="utf-8") as fh:
            fh.write(line)
        h = self.head(seam)
        at_write = dl2.parse_note(h.read_text(encoding="utf-8")).cited_at_write if h else 0
        cites = self.citations(seam)
        return {"mode": self.mode(), "seam": seam,
                "last_cited": cites[-1],
                "pressure": dl2.pressure(at_write, cites)}

    def bless(self, seam: str, by_whom: str, checked: str,
              gen: int | None = None) -> dict:
        """Rule 5.  Endorse bytes you did not write, and say what you checked.

        Refuses the author.  Refuses an empty check.  Names the sha so the
        blessing cannot drift onto a later generation.
        """
        self.ensure()
        if not str(checked).strip():
            raise StoreError(
                "REFUSED: a bless must say WHAT YOU CHECKED. Nothing was "
                "written.\n'I read it' is not a check. The value of a blessing "
                "is entirely in the claim the blesser is making about their "
                "own attention, and a bless with no stated check is a rubber "
                "stamp with a better name.")
        # One bless is one line. A line break in `checked` wrote a second
        # blessing under any name, past the author refusal below.
        _one_line("by_whom", by_whom)
        _one_line("checked", checked)
        gens = self.generations(seam)
        if not gens:
            raise StoreError(f"no such seam to bless: {seam!r}")
        idx = (gen or len(gens)) - 1
        if idx < 0 or idx >= len(gens):
            raise StoreError(
                f"seam {seam!r} has {len(gens)} generation(s); you asked to "
                f"bless number {gen}.")
        path = gens[idx]
        note = self._parse(path)
        if note.by == by_whom:
            raise StoreError(
                f"REFUSED: {by_whom!r} wrote generation {note.gen} of "
                f"{seam!r} and cannot bless it. Nothing was written.\n"
                "A bless is worth something only because the blesser is a "
                "SECOND party -- an author blessing their own work is one "
                "witness signing twice, which is the exact failure this "
                "store's whole discipline exists to catch. Ask somebody else "
                "to read it.")
        sha = dl2.file_sha(path.read_bytes())
        self.blessed.mkdir(parents=True, exist_ok=True)
        line = f"{self.stamp()}\t{by_whom}\t{note.gen}\t{sha}\t{checked}\n"
        with (self.blessed / f"{dl2.slugify(seam)}.log").open(
                "a", encoding="utf-8", newline="") as fh:
            fh.write(line)
        return {"mode": self.mode(), "seam": seam, "gen": note.gen,
                "by": by_whom, "author": note.by, "sha": sha,
                "checked": checked,
                "say": (f"generation {note.gen} of {seam!r}, written by "
                        f"{note.by!r}, blessed by {by_whom!r}")}

    def blessings(self, seam: str) -> list[dict]:
        """Every bless recorded for this seam, oldest first.

        A blessing whose sha no longer matches any generation on disk is
        reported as STALE rather than dropped: it is evidence that somebody
        blessed bytes that are no longer there, which is worth more than a
        clean list.
        """
        p = self.blessed / f"{dl2.slugify(seam)}.log"
        if not p.is_file():
            return []
        live = {dl2.file_sha(g.read_bytes()): g.name
                for g in self.generations(seam)}
        out = []
        for raw in p.read_bytes().split(b"\n"):
            if not raw.strip():
                continue
            cols = raw.decode("utf-8", errors="surrogateescape").split("\t")
            if len(cols) < 5:
                continue
            stamp, who, gen, sha, checked = cols[0], cols[1], cols[2], cols[3], "\t".join(cols[4:])
            out.append({"stamp": stamp, "by": who, "gen": dl2.ascii_int(gen, 0),
                        "sha": sha, "checked": checked,
                        "file": live.get(sha, ""),
                        "state": "OK" if sha in live else "STALE"})
        return out

    def _receipt(self, kind: str, detail: str) -> None:
        self.receipts.mkdir(parents=True, exist_ok=True)
        day = _utcnow().strftime("%Y-%m")
        with (self.receipts / f"{day}.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{dl2.stamp()}\t{kind}\t{self.by}\t{detail}\n")

    # ------------------------------------------------------------- index
    def rebuild_index(self) -> dict:
        """Regenerate the forward index, and say what it was rebuilt FROM.

        The index has two sources, not one: the generation files, and the
        append-only ``cited/`` logs.  An earlier version claimed it rebuilt
        "from the note files alone" and then silently read ``cited/`` anyway --
        so deleting that directory produced an index reporting every note as
        never cited, with no fault and a cheerful success message.  That is a
        cache quietly becoming the record, which is the exact failure the rule
        was written against.

        Now: when a citation log is missing, the note's own
        ``last-cited-at-write`` / ``cited-at-write`` fields are used -- they are
        in the generation's bytes, which is why they are there -- and the row is
        marked ``~`` to say the live log is gone and this is the last value the
        note itself witnessed.  The result reports how many rows are degraded.
        A number a reader can see beats a silent zero.
        """
        self.ensure()
        # `head-stamp` is here because spec v3 took the date out of the
        # FILENAME. The date did not disappear -- it is in the note's own
        # `stamp:` field, inside the C3 hash -- but a human scanning seam
        # directories with `ls` used to read it for free and now cannot. The
        # index is a cache (store rule 2), which is exactly where a derived
        # browsing convenience belongs; the record stays the bytes.
        # COST: one more column. A consumer reading this file by column
        # position must count again. Nothing in this tree does.
        rows = ["# seam\tgens\thead\thead-stamp\tfirst-seen\tlast-cited"
                "\tpressure\tverdict\tby"]
        degraded: list[str] = []
        no_log: list[str] = []
        for slug in self.seams():
            gens = self.generations(slug)
            if not gens:
                continue
            n = self._parse(gens[-1])
            log = self.cited / f"{dl2.slugify(slug)}.log"
            if log.is_file():
                cites = self.citations(slug)
                last = cites[-1] if cites else "-"
                raw_press = dl2.pressure(n.cited_at_write, cites)
                if raw_press < 0:
                    # The log has FEWER lines than this generation recorded
                    # seeing. Impossible in an append-only file, so it is proof
                    # that lines were removed -- not a zero.
                    degraded.append(slug)
                    press = f"!{raw_press}"
                else:
                    press = str(raw_press)
            elif n.cited_at_write or n.last_cited_at_write:
                # The log is gone AND the note remembers citations it once saw.
                # A known loss, and it reports the SAME number read() and
                # buoyancy() report -- three code paths gave three different
                # answers for this one state.
                degraded.append(slug)
                last = f"~{n.last_cited_at_write or '-'}"
                press = f"!{-int(n.cited_at_write or 0)}"
            else:
                # No log, and the note never witnessed a citation either. A
                # note that was simply never cited looks exactly like one whose
                # log was deleted before it was ever revised. We cannot tell,
                # so we do not claim -- "0" here means "no evidence of any",
                # never "certainly none".
                no_log.append(slug)
                last, press = "-", "0"
            rows.append("\t".join([
                slug, str(len(gens)), gens[-1].name, n.stamp or "-",
                n.first_seen or gens[0].name, last, press, n.verdict(), n.by,
            ]))
        self.index.parent.mkdir(parents=True, exist_ok=True)
        self.index.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="")
        out = {"mode": self.mode(), "seams": len(rows) - 1,
               "index": str(self.index.name),
               "degraded": len(degraded), "no_log": len(no_log)}
        if no_log:
            out["no_log_say"] = (
                f"{len(no_log)} seam(s) have no citation log and no citation "
                "recorded in their own bytes. A note that was never cited is "
                "indistinguishable from one whose log was removed, so their "
                "pressure reads 0 meaning 'no evidence of any', never "
                "'certainly none'.")
        if degraded:
            out["say"] = (
                f"{len(degraded)} seam(s) have a citation history that is gone "
                "or shorter than the note itself recorded seeing: "
                + ", ".join(degraded[:5])
                + (" ..." if len(degraded) > 5 else "")
                + ". Their last-cited and pressure are marked '~' and come from "
                  "the note's own record of what it last saw, not from a live "
                  "log. The logs are append-only and nothing here deletes them, "
                  "so a missing one means something outside this tooling removed "
                  "it.")
        return out

    def buoyancy(self, by: str = "lift") -> list[dict]:
        """Every seam ordered by buoyancy, most buoyant first.

        The compaction queue.  Leaned on since last revised = floats.  Nothing
        has needed it = free to sink to a continuation page.  Sinking is not
        deletion; the floor is still the store.

        ``by="lift"`` (the default) ranks each seam against the worlds that
        cite it, so a quiet consumer's world is not drowned by a busy one --
        see ``dl2.lift``.  ``by="pressure"`` gives the older absolute order,
        kept because a caller comparing two runs across the change needs to be
        able to ask for the ranking it had before.

        This REPORTS.  It compacts nothing, and the arithmetic that produced
        every number (``scale``, ``by``) rides in the row so the caller can
        disagree with it.  Corwin: poly and meantcached together are not "a
        waldo for perfect semaphore structure" -- they are the pipeline that
        keeps the problem in front of something with judgement.
        """
        out = []
        for slug in self.seams():
            gens = self.generations(slug)
            if not gens:
                continue
            n = self._parse(gens[-1])
            log = self.cited / f"{dl2.slugify(slug)}.log"
            cites = self.citations(slug)
            press = dl2.pressure(n.cited_at_write, cites)
            row = {"seam": slug, "gens": len(gens),
                   "pressure": press,
                   "unit": n.unit,
                   "score_milli": dl2.score(press, n.unit),
                   "act": dl2.score(press, n.unit) >= _chainspec.ACT_AT_MILLI,
                   "head_stamp": n.stamp,
                   "last_cited": cites[-1] if cites else ""}
            if not log.is_file() and (n.cited_at_write or n.last_cited_at_write):
                # Say it rather than reporting a confident zero.
                row["pressure_source"] = "NOTVISIBLE -- citation log missing"
                row["last_cited"] = n.last_cited_at_write
            row["citers"] = self.citers(slug)
            row["name"] = n.seam or slug
            out.append(row)

        # Orthogonality. `pressure` alone ranks every world on one scale, and a
        # quiet consumer's entire world then sorts below a busy consumer's
        # noise -- so compaction sinks it wholesale and the person who needed
        # those notes finds them gone. `lift` measures each seam against the
        # median of the worlds that actually cite it, so the most-leaned-on
        # thing in a small world floats. See dl2.lift for the arithmetic and
        # for why it is integer thousandths rather than a ratio.
        # PATH COHORTS ARE SPEC'D BUT NOT WIRED, and that is deliberate.
        #
        # His 2026-09-16 ruling settles where a buoyancy context comes from:
        # the taxonomy path the thing already has, walked deepest first. I
        # implemented it, fed it into `lift` alongside the citer cohorts, and
        # the Perl reader immediately dissented -- because I had changed one
        # reader's arithmetic without writing the clause first, which is the
        # precise error chainspec's prose-spec discipline exists to prevent.
        #
        # So the mechanism ships as `dl2.path_contexts` and `dl2.split_points`
        # -- pure, tested, and specified -- and the RANKING is untouched until
        # L6 is written and both readers are built from it. A seam's contexts
        # are reported on every row so the material is visible; nothing scores
        # by them yet.
        #
        # There is a second thing in the way, found by wiring it: `slugify`
        # collapses `/` to `-`, so the handle a row is keyed by has already
        # lost the path. The contexts below come from the seam's REAL name in
        # the front matter, which is the only place it survives intact.
        for r in out:
            r["contexts"] = dl2.path_contexts(r.get("name") or r["seam"])
        lifts = dl2.lift({r["seam"]: r["pressure"] for r in out},
                         {r["seam"]: set(r["citers"]) for r in out})
        for r in out:
            r.update({k: v for k, v in lifts[r["seam"]].items()
                      if k != "pressure"})

        # Negative pressure is evidence of tampering, and a plain -pressure
        # sort put it BELOW a note nobody ever cited -- ranking a damaged seam
        # as the most disposable thing in the store. Damage sorts first.
        if by == "pressure":
            key = lambda r: (r["pressure"] >= 0,
                             -abs(r["pressure"]) if r["pressure"] < 0
                             else -r["pressure"], r["seam"])
        else:
            key = lambda r: (r["pressure"] >= 0,
                             -abs(r["pressure"]) if r["pressure"] < 0
                             else -r["lift_milli"], -r["pressure"], r["seam"])
        self._last_splits = dl2.split_points([r["seam"] for r in out])
        return sorted(out, key=key)

    def semaphore(self, name: str) -> Semaphore:
        slug = dl2.slugify(name)
        return Semaphore(self.semaphores / f"{slug}.log", slug)
