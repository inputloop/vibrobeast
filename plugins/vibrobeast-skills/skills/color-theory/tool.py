# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""color-theory: WCAG 2.1 contrast checker for accessible palettes.

stdlib only. Subcommands:
  contrast FG BG          ratio + AA/AAA pass-fail for a foreground/background pair
  suggest BG [--level]    nudge toward black or white until it passes on BG
  audit [FILE]            many "FG BG" pairs from FILE or stdin; pass/fail each
                          (comment lines are '#' + whitespace; '#rrggbb' is data)
  selftest                prove audit reads hex pairs and can go red
"""
from __future__ import annotations

import argparse
import sys

THRESHOLDS = {
    "AA":  {"normal": 4.5, "large": 3.0},
    "AAA": {"normal": 7.0, "large": 4.5},
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    h = value.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"not a 3- or 6-digit hex color: {value!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _linearize(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_linearize(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(hex_to_rgb(fg))
    l2 = relative_luminance(hex_to_rgb(bg))
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def grades(ratio: float) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for level in ("AA", "AAA"):
        for size in ("normal", "large"):
            out.append((f"{level} {size}", ratio >= THRESHOLDS[level][size]))
    return out


def cmd_contrast(args: argparse.Namespace) -> int:
    ratio = contrast_ratio(args.fg, args.bg)
    print(f"{args.fg} on {args.bg}: contrast ratio {ratio:.2f}:1")
    for label, ok in grades(ratio):
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    target = THRESHOLDS[args.level]["normal"]
    best = None
    for candidate in ("#000000", "#ffffff"):
        r = contrast_ratio(candidate, args.bg)
        if r >= target and (best is None or r > best[1]):
            best = (candidate, r)
    if best:
        print(f"On {args.bg}, use {best[0]} -> {best[1]:.2f}:1 (passes {args.level} normal text)")
        return 0
    blk = ("#000000", contrast_ratio("#000000", args.bg))
    wht = ("#ffffff", contrast_ratio("#ffffff", args.bg))
    pick = max((blk, wht), key=lambda t: t[1])
    print(f"On {args.bg}, no pure black/white reaches {args.level} normal text.")
    print(f"  Closest: {pick[0]} -> {pick[1]:.2f}:1. Adjust the background's lightness and re-check.")
    return 1


def is_comment(line: str) -> bool:
    """A comment is '#' followed by whitespace, or a bare '#'.

    Hex colours also begin with '#', so a bare startswith("#") test silently
    skipped every data line written as '#rrggbb #rrggbb' and the audit
    reported a pass over nothing (fixed 2026-09-11; see selftest).
    """
    return line == "#" or line[:1] == "#" and line[1:2].isspace()


def cmd_selftest(args: argparse.Namespace) -> int:
    """Prove the audit can go red: hex-pair lines must be read, not skipped."""
    import io
    sample = "# a comment line\n#777777 #ffffff\n#000000 #ffffff\n"
    stream = io.StringIO(sample)
    seen = [ln.strip() for ln in stream if ln.strip() and not is_comment(ln.strip())]
    checks = [
        ("comment '# ...' skipped", len(seen) == 2),
        ("hex pair lines kept", seen == ["#777777 #ffffff", "#000000 #ffffff"]),
        ("failing pair goes red", contrast_ratio("#777777", "#ffffff") < THRESHOLDS["AA"]["normal"]),
        ("passing pair stays green", contrast_ratio("#000000", "#ffffff") >= THRESHOLDS["AA"]["normal"]),
        ("mutant: bare startswith('#') would skip data", "#777777 #ffffff".startswith("#")),
    ]
    bad = 0
    for name, ok in checks:
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        bad += 0 if ok else 1
    return 1 if bad else 0


def cmd_audit(args: argparse.Namespace) -> int:
    stream = open(args.file) if args.file and args.file != "-" else sys.stdin
    failures = 0
    pairs = 0
    try:
        for lineno, raw in enumerate(stream, 1):
            line = raw.strip()
            if not line or is_comment(line):
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f"line {lineno}: expected 'FG BG', got {line!r}", file=sys.stderr)
                failures += 1
                continue
            fg, bg = parts[0], parts[1]
            pairs += 1
            try:
                ratio = contrast_ratio(fg, bg)
            except ValueError as exc:
                print(f"line {lineno}: {exc}", file=sys.stderr)
                failures += 1
                continue
            aa = ratio >= THRESHOLDS["AA"]["normal"]
            print(f"{fg} on {bg}: {ratio:5.2f}:1  {'AA-pass' if aa else 'AA-FAIL'}")
            if not aa:
                failures += 1
    finally:
        if stream is not sys.stdin:
            stream.close()
    # 2026-10-05, from Bryant's color-theory 1.1: an audit that read no pairs checked nothing.
    # Here that is NOT CHECKED (exit 2), and every audit says how many pairs it read.
    print(f"audit: {pairs} pair(s) read, {failures} failed", file=sys.stderr)
    if pairs == 0 and not failures:
        print("audit: NOT CHECKED: no 'FG BG' pairs were read", file=sys.stderr)
        return 2
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="WCAG 2.1 contrast checker for accessible palettes")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("contrast", help="ratio + AA/AAA grades for one FG/BG pair")
    c.add_argument("fg"); c.add_argument("bg")
    c.set_defaults(func=cmd_contrast)

    s = sub.add_parser("suggest", help="suggest black or white text for a background")
    s.add_argument("bg"); s.add_argument("--level", choices=("AA", "AAA"), default="AA")
    s.set_defaults(func=cmd_suggest)

    a = sub.add_parser("audit", help="audit many 'FG BG' pairs from a file or stdin")
    a.add_argument("file", nargs="?", default="-")
    a.set_defaults(func=cmd_audit)

    t = sub.add_parser("selftest", help="prove the audit reads hex pairs and can go red")
    t.set_defaults(func=cmd_selftest)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
