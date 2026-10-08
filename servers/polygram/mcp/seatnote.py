# polygram -- gated agent-skill synthesis.
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>.  Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of polygram.  polygram is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""seatnote -- put one note into Mentat's seat from a plain shell (no MCP needed).

    python -m polygram.mcp.seatnote --release-note TEXT [--root DIR]
    python -m polygram.mcp.seatnote --seam S --text T --source SRC --would-change W
    python -m polygram.mcp.seatnote --where        which seat would be written, and why
    python -m polygram.mcp.seatnote --prove-red

Why this exists (Corwin, 2026-09-27): "does this let me share a reason/comment that could flow
toward MEMORY given the MCP is reachable when I make the call?"  `make` runs in a shell, and a
shell cannot speak to the mentcached MCP server.  It does not need to: the seat the server serves
is a folder, and this writes into it through the SAME store code (polygram.mcp.store), under the
same per-seam lock, with the same required `source` and `would_change`.

Which seat.  The first of these that is SEATED (reachable and writable, as the server means it):
  --seat PATH, else $MENTCACHED_SEAT, else ~/.mentcached/seat, else the desktop app's home seen
  from this shell ($USERPROFILE -> /c/Users/<you>/.mentcached/seat on msys2, /mnt/c/... on WSL).
The last one matters on Windows: in an msys2 shell `~` is usually not the home the desktop app's
server uses, and guessing wrong would either miss the seat or start a second one.
It NEVER creates a seat.  Nothing reachable: it says where it looked and exits 3; the caller
(make dist) goes on, and the note stays in releases/<x.y.z>, the build's own record.
Exit: 0 written (or --where found one) - 2 usage - 3 no seat reachable - 4 the store refused.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from . import store as _store

BY = "polygram-make-dist"   # a stable consumer identity (never a pid: see mentcached.create_server)
SEAM = "polygram-releases"


def _unexpanded(v: str) -> bool:
    return "${" in v or "%" in v or v.startswith("$")


def _desktop_homes() -> list[Path]:
    """The Windows profile folder as this shell can reach it, if it can."""
    up = (os.environ.get("USERPROFILE") or "").strip()
    if not up:
        return []
    if os.name == "nt":
        return [Path(up)]
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", up)
    if not m:
        return [Path(up)]
    d, rest = m.group(1).lower(), m.group(2).replace("\\", "/")
    return [Path(f"/{d}/{rest}"), Path(f"/cygdrive/{d}/{rest}"), Path(f"/mnt/{d}/{rest}")]


def candidates(seat: str | None = None) -> list[tuple[Path, str]]:
    if seat:
        return [(Path(seat).expanduser(), "--seat")]
    env = (os.environ.get("MENTCACHED_SEAT") or "").strip()
    if env and not _unexpanded(env):
        return [(Path(env).expanduser(), "$MENTCACHED_SEAT")]
    out = [(Path.home() / ".mentcached" / "seat", "this shell's home")]
    for h in _desktop_homes():
        p = h / ".mentcached" / "seat"
        if p not in [c for c, _ in out]:
            out.append((p, "the desktop app's home ($USERPROFILE)"))
    return out


def find_seat(seat: str | None = None):
    """(Store, why) for the first SEATED candidate, or (None, what was looked at)."""
    looked = []
    for path, why in candidates(seat):
        st = _store.Store(root=path, by=BY)
        m = st.mode()
        if m == _store.SEATED:
            return st, f"{path} ({why})"
        looked.append(f"{path} ({why}): {m}")
    return None, "; ".join(looked)


def _version(root: Path) -> str:
    try:
        t = (root / "polygram" / "__init__.py").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r'^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"', t, re.M)
    return m.group(1) if m else ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="seatnote", description=__doc__.split("\n")[0])
    ap.add_argument("--release-note", metavar="TEXT")
    ap.add_argument("--root", default=".", help="the garden holding polygram/ and releases/")
    ap.add_argument("--seam"); ap.add_argument("--text")
    ap.add_argument("--source"); ap.add_argument("--would-change")
    ap.add_argument("--seat")
    ap.add_argument("--where", action="store_true")
    ap.add_argument("--prove-red", action="store_true")
    a = ap.parse_args(argv)
    if a.prove_red:
        return prove_red()
    st, why = find_seat(a.seat)
    if a.where:
        print(f"seatnote: {'seat ' + why if st else 'no seat reachable -- looked at ' + why}")
        return 0 if st else 3
    if a.release_note is not None:
        root = Path(a.root)
        v = _version(root)
        if not v:
            print(f"seatnote: no __version__ in {root}/polygram/__init__.py", file=sys.stderr)
            return 2
        seam, text = SEAM, f"v{v}: {' '.join(a.release_note.split())}"
        src = f"releases/{v} in the garden (make dist NOTE=..., typed by the keeper at the build)"
        wc = f"a later note from the keeper about v{v}, or v{v} being withdrawn"
    else:
        seam, text, src, wc = a.seam, a.text, a.source, a.would_change
        if not all((seam, text, src, wc)):
            ap.error("give --release-note TEXT, or all of --seam --text --source --would-change")
    if st is None:
        print(f"seatnote: no seat reachable -- the note stays in releases/ only (looked at {why})",
              file=sys.stderr)
        return 3
    try:
        r = st.append(seam, text, frm=src, would_change=wc)
    except (_store.StoreError, _store.SemaphoreBusy) as exc:
        print(f"seatnote: the seat refused the note: {exc}", file=sys.stderr)
        return 4
    gen = r.get("gen", "?")
    print(f"seatnote: note written to seam {seam} (generation {gen}) in the seat at {why}")
    return 0


def prove_red() -> int:
    """Each promise, fired on purpose: finds the seat the desktop app uses, never creates one."""
    import io, tempfile, contextlib
    ok_all = True

    def check(name, cond):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(("ok    " if cond else "FAIL  ") + name)

    saved = {k: os.environ.get(k) for k in ("MENTCACHED_SEAT", "USERPROFILE", "HOME")}
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            shell_home, app_home = td / "shellhome", td / "c" / "Users" / "k"
            shell_home.mkdir(); (app_home / ".mentcached" / "seat").mkdir(parents=True)
            _store.Store(root=app_home / ".mentcached" / "seat", by=BY).ensure(create=True, make_parents=True)
            os.environ.pop("MENTCACHED_SEAT", None)
            os.environ["HOME"] = str(shell_home)
            os.environ["USERPROFILE"] = str(app_home)          # a POSIX-form profile path
            (td / "polygram").mkdir()
            with open(td / "polygram" / "__init__.py", "w", encoding="utf-8", newline="\n") as fh:
                fh.write('__version__ = "0.8.90"\n')
            st, why = find_seat()
            check("finds the seat under the desktop app's home when this shell's home has none",
                  st is not None and str(app_home) in why)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = main(["--release-note", "a test\nnote", "--root", str(td)])
            notes = list((app_home / ".mentcached" / "seat").rglob("*"))
            body = "".join(p.read_text(encoding="utf-8", errors="replace") for p in notes if p.is_file())
            check("writes the note, versioned and one line, through the store (exit 0)",
                  rc == 0 and "v0.8.90: a test note" in body)
            check("the note carries its source and what would change it",
                  "releases/0.8.90" in body and "withdrawn" in body)
            check("this shell's home was not given a seat", not (shell_home / ".mentcached").exists())
            os.environ["USERPROFILE"] = str(td / "nobody")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = main(["--release-note", "x", "--root", str(td)])
            check("no seat anywhere: exit 3, says where it looked, creates nothing",
                  rc == 3 and "looked at" in err.getvalue() and not (td / "nobody").exists()
                  and not (shell_home / ".mentcached").exists())
            check("a Windows profile path maps to the msys2 form",
                  (os.environ.__setitem__("USERPROFILE", r"C:\Users\k") or True)
                  and Path("/c/Users/k") in _desktop_homes())
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print("prove-red: " + ("every promise held" if ok_all else "FAILED"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
