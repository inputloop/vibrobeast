#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""ferry_core - the one spine: sha256 identity, receipts, hash-keyed TSV manifests.

Shared by the Drive ferry (Task B) and the cross-model LENS (Task A). Both move a
copy across a boundary and prove it landed by hash; this module owns that proof.

House rules honored:
  * stdlib only (hashlib, csv, os, datetime) - no dependency to justify.
  * receipts in the wordwise format:  TS<TAB>op<TAB>status<TAB>k=v...<TAB>tail
  * a manifest is keyed by content sha256 (identity), path is only a hint.
  * losses kept: nothing here deletes; callers append.

Canon governs; the pub shelf canon (canon/principles/) is source of truth. Minted, not vouched.
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import io
import os

CHUNK = 1 << 16


# --- identity -------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    """UTC, second precision, Z-suffixed - matches the existing receipts.log."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- receipts -------------------------------------------------------------

def receipt_line(op: str, status: str, fields=None, tail: str = "landed",
                 ts: str | None = None) -> str:
    """One receipt line. `fields` is an ordered dict rendered as k=v, tab-joined.

    Mirrors the wordwise receipts.log:  TS  op  status  src=..  dest=..  sha=..  landed
    """
    parts = [ts or now_iso(), op, status]
    if fields:
        for k, v in fields.items():
            parts.append("%s=%s" % (k, v))
    if tail:
        parts.append(tail)
    return "\t".join(parts)


def append_receipt(logpath: str, op: str, status: str, fields=None,
                   tail: str = "landed", ts: str | None = None) -> str:
    """Append a receipt line to logpath (created if absent). Returns the line."""
    line = receipt_line(op, status, fields=fields, tail=tail, ts=ts)
    os.makedirs(os.path.dirname(os.path.abspath(logpath)), exist_ok=True)
    with open(logpath, "a", encoding="utf-8", newline="") as fh:
        fh.write(line + "\n")
    return line


# --- hash-keyed TSV manifests --------------------------------------------

def read_tsv(path: str):
    """Return (header:list[str], rows:list[dict]). Missing file -> ([], [])."""
    if not os.path.exists(path):
        return [], []
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = None
        rows = []
        for rec in reader:
            if not rec:
                continue
            if header is None:
                # tolerate a leading '# ' on the header line (wordwise idiom)
                header = [c.lstrip("# ").strip() if i == 0 else c
                          for i, c in enumerate(rec)]
                continue
            rows.append({header[i]: (rec[i] if i < len(rec) else "")
                         for i in range(len(header))})
    return (header or []), rows


def write_tsv(path: str, header, rows, comment_header: bool = True) -> None:
    """Write rows (list[dict]) under header. Header may carry a leading '# '."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    out_header = list(header)
    if comment_header and out_header:
        out_header = ["# " + out_header[0]] + out_header[1:]
    writer.writerow(out_header)
    for r in rows:
        writer.writerow([r.get(c, "") for c in header])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


def upsert(rows, key_field: str, record: dict):
    """Insert-or-replace `record` in `rows` (list[dict]) by key_field. In place.

    Identity is the key's value (for manifests, that key is the sha256). Returns
    'insert' or 'replace' - the second, prove-a-promise-flavored signal callers
    use to assert idempotence (a re-run of unchanged bytes must 'replace' with an
    identical row, never grow the ledger).
    """
    k = record[key_field]
    for i, r in enumerate(rows):
        if r.get(key_field) == k:
            rows[i] = record
            return "replace"
    rows.append(record)
    return "insert"


if __name__ == "__main__":  # tiny self-demo, prints a receipt + a sha
    import sys
    if len(sys.argv) > 1:
        p = sys.argv[1]
        print("sha256", sha256_file(p), p)
    print(receipt_line("demo", "OK", {"src": "a", "dest": "b", "sha": "0" * 64}))
