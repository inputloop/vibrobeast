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

"""The SHIPBOARD DATE -- a context's date, held in a file, moving like a version.

Corwin, 2026-09-15:

    "When we put a date into a file (or filename) it should come from a file.
     ... Unless we have a good reason to use system date, such as to populate
     that file: my point is that having a running conception of shipboard date
     -- to lean into the new UI framing -- is potentially quite helpful, and I
     also find it helpful to think about that date as I do the high-water mark
     VERSION that a project -- or some other context! -- could have."

WHAT THIS REPLACES.  Every stamp in this store used to come from
``datetime.now()`` -- the HOST CLOCK, which is a fact about the machine that
happened to run the write and about nothing else.  That is an INFERRED value
dressed as a recorded one, and this codebase already has a name for the
distinction: chainspec U1 says the neutral-buoyancy mark is "DECLARED, NEVER
INFERRED", and the reason is the same here.

WHY IT IS A VERSION AND NOT A CLOCK.  A high-water mark only ever moves
forward.  So:

  * A shipboard date never goes backward.  ``advance`` refuses a value earlier
    than the recorded one and says so; it does not silently take the larger.
  * Reading it never moves it.  A thousand reads leave the file untouched, so
    "what date was this context at" has one answer, not one per observer.
  * The host clock is legitimate for exactly one job: POPULATING the file.
    That is an explicit act, it leaves a receipt, and it is the only door the
    system clock has into this store.

WHAT IT BUYS, concretely, in a project whose whole doctrine is witnesses:

  1. TWO MACHINES CAN AGREE.  Two readers on hosts whose clocks differ by
     seconds produced different bytes for the same write.  A date from a file
     is a fact both of them can share, which is the difference between a second
     witness and a second opinion.
  2. A RESTORE STOPS LYING.  Notes recovered from a backup and re-written used
     to be stamped "now", interleaving years-old material with today's under a
     clock nobody recorded a decision about.
  3. THE STAMP BECOMES CHECKABLE.  A declared value can be compared against
     what a context says about itself.  A clock reading can only be compared
     against another clock.

WHAT IT IS NOT.  It is not a lock, not a schedule, and not an attempt to be
right about the real world.  If the file says 2026-09-15 and the wall says
otherwise, the file is what this context believes and the receipt says who
told it so.  Being wrong in a way that is recorded and monotonic beats being
right in a way that is unrepeatable.

WHERE IT LIVES.  ``<seat>/DATE``, one line, ``YYYYMMDDTHHMMSSZ`` -- the same
shape already used in every note's ``stamp:`` and every citation log line, so
nothing has to learn a second format.  Extensionless on purpose: in this house
a bare name is a register-ish fact about the context rather than a document
about it.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

__all__ = ["STAMP", "read", "advance", "ensure", "now_from_host", "ShipdateError"]

#: ``YYYYMMDDTHHMMSSZ@host``.  Corwin, 2026-09-16: *"dates (including
#: date/time, where I prefer a 24h clock and UTC invariant affixed with
#: hostname) I accept zero padding."*
#:
#: THE HOSTNAME IS NOT DECORATION.  A stamp says WHEN; the host says WHOSE
#: CLOCK SAID SO.  Without it, a date populated from a machine is
#: indistinguishable from a date a person declared -- which is the exact
#: distinction this module exists to keep, and it was missing from the format
#: itself for one day.  The host is optional on READ, because dates written
#: before this rule are still dates; it is always written on WRITE.
#:
#: ASCII digits explicitly -- Python's ``\d`` matches U+0663 ARABIC-INDIC
#: THREE and the sh, awk and Perl readers do not, which has already cost this
#: project one silent reader split.
STAMP = re.compile(r"^([0-9]{8})T([0-9]{6})Z(?:@([A-Za-z0-9][A-Za-z0-9._-]*))?$")


class ShipdateError(RuntimeError):
    pass


def host() -> str:
    """This machine's name, sanitised to the characters a stamp may carry."""
    import socket
    h = (socket.gethostname() or "unknown").split(".")[0]
    h = "".join(c for c in h if c.isascii() and (c.isalnum() or c in "._-"))
    return h or "unknown"


def split_host(s: str) -> tuple[str, str]:
    """``("20260916T093000Z", "avalon")``.  Host is "" when none was recorded."""
    m = STAMP.match(s.strip())
    if not m:
        raise ShipdateError(
            f"not a shipboard date: {s.strip()!r}. Expected "
            "YYYYMMDDTHHMMSSZ@host, ASCII digits only.")
    d, tm, h = m.groups()
    return f"{d}T{tm}Z", (h or "")


def _parse(s: str) -> _dt.datetime:
    m = STAMP.match(s.strip())
    if not m:
        raise ShipdateError(
            f"not a shipboard date: {s.strip()!r}. Expected "
            "YYYYMMDDTHHMMSSZ@host, ASCII digits only.")
    d, t, _h = m.groups()
    return _dt.datetime(int(d[:4]), int(d[4:6]), int(d[6:8]),
                        int(t[:2]), int(t[2:4]), int(t[4:6]),
                        tzinfo=_dt.timezone.utc)


def fmt(when: _dt.datetime, with_host: bool = True) -> str:
    s = when.astimezone(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{s}@{host()}" if with_host else s


def now_from_host() -> _dt.datetime:
    """The host clock.  The ONE legitimate use is populating the file.

    Named rather than inlined so that every call site is greppable: this is the
    only door the system clock has into the store, and a door you cannot count
    is a door you cannot guard.
    """
    return _dt.datetime.now(_dt.timezone.utc)


def path_for(seat: Path) -> Path:
    return Path(seat) / "DATE"


def read(seat: Path) -> tuple[str, str]:
    """``(stamp, source)``.  Reading NEVER moves it.

    *source* is ``"file"`` when the context had declared a date, and
    ``"UNSET"`` when it had not -- said out loud rather than quietly
    substituted, because a store that invents a date and does not mention it
    is the JAILED-memory failure in a different costume.
    """
    p = path_for(seat)
    if not p.is_file():
        return "", "UNSET"
    raw = p.read_bytes().decode("utf-8", errors="surrogateescape")
    first = next((ln for ln in raw.split("\n") if ln.strip()), "")
    _parse(first)                      # raises if the file is not a date
    return first.strip(), "file"


def whose(seat: Path) -> str:
    """Which machine's clock is behind this context's date, or "" if unsaid."""
    s, source = read(seat)
    return split_host(s)[1] if source == "file" else ""


def advance(seat: Path, to: str | _dt.datetime, by: str,
            why: str = "") -> dict:
    """Move the shipboard date FORWARD, or refuse and say why.

    Monotonic is the whole point.  A high-water mark that can fall is a clock
    with extra steps, and a clock is the thing this exists to stop trusting.
    """
    p = path_for(seat)
    want = to if isinstance(to, str) else fmt(to)
    if "@" not in want:
        # A date arriving without a host gets this one's, said rather than
        # assumed: somebody has to have been the clock.
        want = f"{want}@{host()}"
    new = _parse(want)
    old_s, source = read(seat)
    if source == "file":
        old = _parse(old_s)
        if new < old:
            raise ShipdateError(
                f"REFUSED: the shipboard date is a high-water mark and only "
                f"moves forward. This context is at {old_s}; you asked for "
                f"{want}. Nothing was written.\nIf the recorded date is wrong, "
                "that is a fact worth its own note -- fix it deliberately and "
                "say who and why, rather than letting a write walk it back.")
        if new == old:
            return {"date": old_s, "moved": False, "source": source,
                    "say": "already at that date; nothing written"}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((want + "\n").encode("utf-8"))
    return {"date": want, "moved": True, "from": old_s or "(unset)",
            "by": by, "why": why,
            "say": (f"shipboard date {'advanced' if old_s else 'set'} to {want}"
                    + (f" (was {old_s})" if old_s else " (was unset)"))}


def ensure(seat: Path, by: str = "host-clock", allow_host: bool = True) -> tuple[str, str]:
    """The stamp a write should use, and where it came from.

    If the context has declared a date, that is the answer and the host clock
    is never consulted.  If it has not, and *allow_host*, the clock populates
    the file once -- which is the "good reason to use system date" he named --
    and the receipt records that it was the clock and not a person.
    """
    s, source = read(seat)
    if source == "file":
        return s, source
    if not allow_host:
        raise ShipdateError(
            f"no shipboard date at {path_for(seat)} and the host clock was "
            "not permitted. Nothing was written. Set one with seat_date, or "
            "allow the clock to populate it once.")
    r = advance(seat, now_from_host(), by=by,
                why="populating an unset shipboard date from the host clock")
    return r["date"], "host-clock"
