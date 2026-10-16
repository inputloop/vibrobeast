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

"""verify -- the chain check, written twice, on purpose.

Corwin's requirement, in his words: *"implementing very important controls in
several languages and potentially opportunistically swapping out what checks
are used to provide run-time test coverage across the functionally load-bearing
set of proofs."*

The chain check is the load-bearing proof of this store: it is what makes
"nothing was overwritten" a fact rather than a policy.  So it exists twice --
once in Python (``verify_python``) and once in POSIX shell with ``sha256sum``
and ``awk`` (``bin/dl2-verify.sh``, driven by ``verify_shell``) -- and the two
share no code, no parser and no hash implementation.

That makes them two INDEPENDENT representations of one truth, which is exactly
what [[seams]] says evidence requires.  A single implementation checking itself
is a writer grading its own homework: it can only find the bugs it does not
have.

The swap
--------
``verify()`` picks one implementation per call and runs BOTH when the note has
not been verified yet in this process, and every 9th call thereafter.

- *First touch is derived*, not chosen: a note with no recorded agreement in
  this process has no second reader yet, so the first look pays for both.
- *9 is from the house set (4, 9, 17) and is not derived.*  Said plainly here
  because an undeclared magic number is the thing the house rule exists to
  catch.  It becomes derivable the moment there is a measured disagreement
  rate: pick N so expected calls-to-detection stays under one session.

Cross-checking on every call would cost a subprocess per read and teach us
nothing new most of the time; never cross-checking would make the second
implementation decoration.  The sampling is the point -- over a session the
two implementations cover each other, and neither is ever the only witness to
a whole run.

When they disagree
------------------
STOP.  ``verify()`` raises ``ChainSplit`` and says which implementation said
what.  It does not pick a winner.  A disagreement between two independent
readers of one truth is the process succeeding, and choosing a side here would
throw away the only signal the arrangement was built to produce.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import dl2
from .chainspec import GEN_NAME, SPEC_VERSION

__all__ = ["verify", "verify_python", "verify_shell", "verify_perl",
           "ChainSplit",
           "ChainResult", "CROSSCHECK_EVERY", "Verifier"]

# House set (4, 9, 17).  Not derived -- see the module docstring.
CROSSCHECK_EVERY = 9

_SHELL = Path(__file__).resolve().parents[2] / "bin" / "dl2-verify.sh"
_PERL = Path(__file__).resolve().parents[2] / "bin" / "dl2-verify.pl"


class ChainSplit(RuntimeError):
    """Two independent verifiers disagreed.  Nobody wins; look."""


@dataclass
class ChainResult:
    seam: str
    ok: bool
    gens: int
    broken_at: str = ""
    by: str = ""          # which implementation produced this
    detail: str = ""
    check: str = ""       # which of C1..C4 failed

    def key(self) -> tuple:
        """The comparable part.

        ``check`` is in here, and that is the fix for a real hole: the key used
        to be ``(ok, gens, broken_at)`` and ``broken_at`` is only a filename,
        so two readers stopping at the same file **for different reasons**
        counted as agreeing.  A planted indented ``  ---`` fence produced
        ``C1 position`` from one reader and ``C3 body`` from the other two, at
        the same file, and no ChainSplit was raised.

        The node conformance suite compared the check name all along.  The
        production comparator being weaker than the test harness is its own
        small lesson.

        ``by`` and ``detail`` stay out -- implementations may phrase themselves
        differently, but they may not disagree about which check failed.
        """
        return (self.ok, self.gens, self.broken_at, self.check)


def _files(seam_dir: Path) -> list[tuple[int, Path]]:
    """Generation files only, ordered by the INTEGER in the name.

    Regular files only: a directory or a dangling symlink named ``g0009-x.md``
    is not a generation, and treating it as one crashed the shell reader while
    the Python one silently skipped it -- a split, found 2026-09-14.

    Ordered numerically, not by string: ``g10000`` sorts before ``g9999``
    lexically, so a store that ever reached five digits would have read its own
    chain out of order.

    BOTH NAME ERAS, and this reader needs no branch for it (spec v3 N1/N2).
    ``GEN_NAME`` accepts ``g<gen>-<stamp>-<hex16>.md`` and ``g<gen>-<hex16>.md``
    alike, group(1) is still the generation and group(3) is still the handle,
    so nothing downstream of here knows or cares which era a file is from.
    That is the whole reason the era is not a fact any check may branch on: an
    archive-only store cannot migrate, so every seam that outlives a format is
    mixed, and a reader that treated the shape as meaningful would be inventing
    a rule the archived bytes were never written under.
    """
    out = []
    for p in seam_dir.iterdir():
        if not p.is_file() or p.is_symlink():
            continue
        m = GEN_NAME.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    out.sort(key=lambda t: t[0])
    return out


def verify_python(seam_dir: Path) -> ChainResult:
    """Implementation A: pure Python, written from ``chainspec``.

    Written from the SPEC, not from the shell version.  That is what makes the
    two independent -- not that they are in different languages, which an
    earlier pair was, while sharing the one assumption that let a forged
    generation 1 through both of them.
    """
    seam = seam_dir.name
    files = _files(seam_dir)
    n = len(files)

    def bad(p, check, why):
        return ChainResult(seam, False, n, p.name, "python", f"{check}: {why}",
                           check=check)

    prev_bytes = b""
    for i, (num, p) in enumerate(files, start=1):
        raw = p.read_bytes()
        try:
            fm, body = dl2.front_matter(raw)
        except ValueError as exc:
            return bad(p, "C0 shape", str(exc))

        # C1 position.  Strict ASCII digits, not int(): Python's int() accepts
        # "+7", a full-width "０７" and a leading non-breaking space, while the
        # sh and Perl readers accept none of them -- so the anchor reader was
        # the permissive one, and it answers alone on one rotation in three.
        # strip(" \t\r"), not strip(): bare strip() removes Unicode
        # whitespace such as U+00A0, which the ASCII-only readers keep --
        # so "\xa07" was accepted here and rejected by both of them.
        raw_gen = fm.get("gen", "").strip(" \t\r")
        if not raw_gen or not all("0" <= c <= "9" for c in raw_gen):
            return bad(p, "C1 position",
                       f"gen is not a plain decimal integer: {raw_gen!r}")
        gen = int(raw_gen)
        if gen != i:
            return bad(p, "C1 position",
                       f"gen says {gen} but this is file {i} of {n}")
        # C2 name
        if num != gen:
            return bad(p, "C2 name", f"filename says g{num:04d} but gen says {gen}")
        # C3 self -- the name against the WHOLE file (spec v2). No parsing is
        # involved, which is why this is the one check a parser disagreement
        # cannot confuse, and why it reaches the head generation's front matter
        # that the v1 body-only hash left open.
        want = GEN_NAME.match(p.name).group(3)
        got = dl2.file_sha(raw)[:16]
        if want != got:
            return bad(p, "C3 self",
                       f"name carries {want} but the file hashes to {got} "
                       "-- this generation was changed after it was written")
        # C4 link
        rec = fm.get("prev", "").strip()
        if i == 1:
            if rec:
                return bad(p, "C4 link", "generation 1 records a prev")
        else:
            if not rec.startswith("sha256:"):
                return bad(p, "C4 link",
                           f"prev is not a sha256: reference: {rec[:24]!r}")
            if rec[len("sha256:"):] != dl2.file_sha(prev_bytes):
                return bad(p, "C4 link",
                           f"recorded {rec[7:23]} != actual "
                           f"{dl2.file_sha(prev_bytes)[:16]}")
        prev_bytes = raw

    return ChainResult(seam, True, n, "", "python", f"chain holds (spec v{SPEC_VERSION})")


def _run_reader(tool: Path, runner: str, seam_dir: Path, label: str) -> ChainResult:
    """Run an out-of-process reader and parse its one-line verdict."""
    seam = seam_dir.name
    if not tool.is_file():
        raise FileNotFoundError(f"{label} verifier missing at {tool}")
    exe = shutil.which(runner)
    if exe is None:
        raise FileNotFoundError(
            f"{runner} is not on PATH, so the {label} reader cannot run. "
            "This matters more than it looks: with no second reader every "
            "verification is a single reader, which is DATA and not proof.")
    # HYPOTHESIS, 2026-10-16 (written before the fix; NOT CHECKED on Windows from here): on avalon the
    # shell reader has said "OK 0" for every seam the Python reader counts 1-3 generations in (10-12
    # handback, and persona_chain mentat tonight).  An empty-but-present folder reads OK 0, so msys sh
    # sees the folder and not its files.  The suspect is the backslash spelling: the folder is handed
    # over as C:\Users\...\mentat and globbed as "$dir"/g*.md.  Hand the out-of-process readers the
    # forward-slash spelling (C:/Users/.../mentat), which msys, Perl and POSIX all take.  Falsifier: after
    # a rebuild, persona_chain mentat on avalon still shows shell gens=0 against Python's 3.
    # tests/test_verify_windows_arg.py checks the hand-over, not the cure.
    arg = seam_dir.as_posix() if os.name == "nt" else str(seam_dir)
    proc = subprocess.run([exe, str(tool), arg],
                          capture_output=True, text=True, encoding="utf-8", timeout=60)
    out = (proc.stdout or "").strip()
    # Contract: "OK\t<gens>" or "BROKEN\t<gens>\t<file>\t<check>\t<why>"
    parts = out.split("\t")
    if parts and parts[0] == "OK":
        return ChainResult(seam, True, int(parts[1]), "", label,
                           f"chain holds (spec v{SPEC_VERSION})")
    if parts and parts[0] == "BROKEN":
        check = parts[3] if len(parts) > 3 else ""
        why = ": ".join(x for x in parts[3:] if x)
        return ChainResult(seam, False, int(parts[1]), parts[2], label, why,
                           check=check)
    raise RuntimeError(
        f"{label} verifier gave an unreadable answer: {out!r} "
        f"(stderr: {(proc.stderr or '').strip()!r})")


def verify_shell(seam_dir: Path) -> ChainResult:
    """Implementation B: POSIX sh + sha256sum + awk, no Python in the loop."""
    return _run_reader(_SHELL, "sh", seam_dir, "shell")


def verify_perl(seam_dir: Path) -> ChainResult:
    """Implementation C: Perl + Digest::SHA, no Python and no shell.

    Not a spare.  On a Windows host where Claude Desktop was launched from
    Explorer, msys2's ``sh`` is not on PATH -- and with only two readers every
    verification there would quietly become a single reader.  Perl ships with
    msys2 and with essentially every POSIX system, so between the two there is
    almost always a second opinion actually available.

    This is also the density test paying out (see ``chainspec``): adding a
    third reader cost 44 lines because the spec was separable enough to be
    reimplemented from its words.
    """
    return _run_reader(_PERL, "perl", seam_dir, "perl")


@dataclass
class Verifier:
    """Holds the per-process call count and the set of seams already
    cross-checked, so the swap policy is testable rather than global state."""

    calls: int = 0
    seen: dict = field(default_factory=dict)
    every: int = CROSSCHECK_EVERY
    force_both: bool = False

    def verify(self, seam_dir: Path) -> ChainResult:
        # Keyed on the RESOLVED path, and counted PER SEAM.  Keying on the
        # basename made two stores with a same-named seam mark each other as
        # already-touched; counting globally meant that with several seams
        # interleaved a given seam might never be re-crossed at all. Both
        # found by an adversarial read, 2026-09-14.
        key = str(Path(seam_dir).resolve())
        self.calls += 1
        n = self.seen.get(key, 0) + 1
        self.seen[key] = n
        both = self.force_both or n == 1 or (n % self.every == 0)

        others = [("shell", verify_shell), ("perl", verify_perl)]
        if not both:
            # Rotate through all three, so no implementation is ever the only
            # witness to a whole run.  Deterministic, so a run is reproducible.
            pick = [("python", verify_python)] + others
            label, impl = pick[n % len(pick)]
            try:
                r = impl(seam_dir)
                # Say it. This branch returned a bare "chain holds" on seven
                # calls in nine while the tool's own description promised two
                # independent verifiers -- and it was the mechanism that turned
                # a reader disagreement from a loud ChainSplit into a silent
                # flip-flop between OK and BROKEN on successive reads.
                r.detail += (" -- SINGLE READER (rotation); this result is "
                             "DATA not proof. Call again for a cross-check.")
                return r
            except Exception as exc:                          # noqa: BLE001
                if label == "python":
                    raise
                r = verify_python(seam_dir)
                r.detail += (f" [the {label} reader failed: "
                             f"{type(exc).__name__}: {exc}] -- SINGLE READER, "
                             "this result is DATA not proof")
                return r

        a = verify_python(seam_dir)
        agreed = ["python"]
        failed = []
        for label, impl in others:
            try:
                b = impl(seam_dir)
            except Exception as exc:                          # noqa: BLE001
                failed.append(f"{label}: {type(exc).__name__}: {exc}")
                continue
            if a.key() != b.key():
                raise ChainSplit(
                    f"{seam_dir.name}: python and {label} disagree, and "
                    f"neither wins.\n  python: ok={a.ok} gens={a.gens} "
                    f"at={a.broken_at!r} {a.detail}\n"
                    f"  {label}: ok={b.ok} gens={b.gens} at={b.broken_at!r} "
                    f"{b.detail}\n"
                    "STOP. The note files on disk are the tiebreaker -- every "
                    "reader is derived from them, so rebuild the disagreeing "
                    "reader's answer by hand against chainspec, then widen the "
                    "audit to the neighbouring seams.")
            agreed.append(label)

        a.by = "+".join(agreed)
        if len(agreed) == 1:
            a.detail += (" [no second reader ran: " + "; ".join(failed)
                         + "] -- SINGLE READER, this result is DATA not proof")
        elif a.ok:
            a.detail = (f"chain holds (spec v{SPEC_VERSION}); "
                        f"{len(agreed)} independent readers agree")
            if failed:
                a.detail += " (" + "; ".join(failed) + ")"
        else:
            # Do NOT overwrite the failure. This line used to be unconditional,
            # so a BROKEN chain came back reading "chain holds ... 3 independent
            # readers agree" -- true about the agreement, catastrophic as a
            # sentence a human reads next to a BROKEN verdict.
            a.detail = (f"{a.detail} -- {len(agreed)} independent readers agree "
                        "THAT IT IS BROKEN")
            if failed:
                a.detail += " (" + "; ".join(failed) + ")"
        return a


_DEFAULT = Verifier()


def verify(seam_dir: Path) -> ChainResult:
    """Module-level convenience over a process-wide :class:`Verifier`."""
    return _DEFAULT.verify(Path(seam_dir))
