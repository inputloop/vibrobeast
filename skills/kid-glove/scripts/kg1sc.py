#!/usr/bin/env python3
"""kg1sc.py -- the kid glove's scan and re-check, read a second time, in Python.

usage: kg1sc.py scan ROOT --raw
       kg1sc.py recheck ROOT --raw
Prints the lines kg1sc prints with --raw (the scan less its SOURCE lines); the re-check exits as
kg1sc's does (1 a TRAMPLE, 2 NOT CHECKED, else 0).  Writes nothing.

Unfolded from kid-glove.org; edit that, not this.
Copyright 2026 Corwin Brust <corwin@bru.st> and Contributors; GPL-3.0-or-later.
Mentat (for Corwin; claude-opus-5-5)
"""
import glob, hashlib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.environ.get("KG_KIT", os.path.join(HERE, "..", "kit", "topics.org-table"))

FAMILIES = [  # first match wins, as in the shell's awk
    ("GNU AFFERO GENERAL PUBLIC LICENSE", "AGPL"),
    ("GNU LESSER GENERAL PUBLIC LICENSE", "LGPL"),
    ("GNU GENERAL PUBLIC LICENSE", "GPL"),
    ("Permission is hereby granted, free of charge", "MIT"),
    ("Apache License", "Apache-2.0"),
    ("Mozilla Public License", "MPL-2.0"),
    ("Redistribution and use in source and binary forms", "BSD"),
    ("Attribution-ShareAlike", "CC-BY-SA"),
    ("Attribution 4.0", "CC-BY"),
    ("free and unencumbered software released into the public domain", "Unlicense"),
    ("ISC License", "ISC"),
]

SPDX_PREFIXES = [("GPL-3.0", "GPL-3"), ("GPL-2.0", "GPL-2"), ("LGPL", "LGPL"), ("AGPL", "AGPL"),
                 ("MPL", "MPL-2.0"), ("BSD", "BSD"), ("CC-BY-SA", "CC-BY-SA"), ("CC-BY-", "CC-BY")]
SPDX_EXACT = {"MIT": "MIT", "Apache-2.0": "Apache-2.0", "Unlicense": "Unlicense", "ISC": "ISC"}
SPDX_LINE = re.compile(rb".*SPDX-License-Identifier:[ \t\n\r\f\v]*([A-Za-z0-9.+-]*)")


def kit():
    rows, header = [], True
    for line in open(KIT, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.startswith("|") or line.startswith("|-"):
            continue
        if header:
            header = False
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(dict(zip(("topic", "governs", "probes", "ours", "flagship"), cells)))
    return rows


def matches(root, probe):
    pattern, _, regex = probe.partition("~")
    found = []
    for path in sorted(glob.glob(os.path.join(glob.escape(root), pattern))):
        rel = os.path.relpath(path, root)
        if regex:
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    if not any(re.search(regex, l.rstrip("\n")) for l in fh):
                        continue
            except OSError:
                continue
        found.append(rel)
    if not found and not regex and not any(ch in pattern for ch in "*?[") and os.path.lexists(os.path.join(root, pattern)):
        found = [pattern]
    return found


def family(path):
    with open(path, "rb") as fh:
        text = fh.read(6000).decode("utf-8", "replace").replace("\n", " ").replace("\r", " ")
    for needle, fam in FAMILIES:
        if needle in text:
            if fam == "GPL":
                return "GPL-3" if "Version 3" in text else ("GPL-2" if "Version 2" in text else "GPL")
            return fam
    return "unknown"


def spdx_family(spdx):
    """An SPDX id -> the words family() uses for it; an id it does not know stands for itself."""
    if spdx in SPDX_EXACT:
        return SPDX_EXACT[spdx]
    for prefix, fam in SPDX_PREFIXES:
        if spdx.startswith(prefix):
            return fam
    return spdx


def lines_of(path):
    """A file's lines as awk reads them: split at newlines only."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace").split("\n")


def reuse_ids(root):
    """The SPDX ids a house declares the REUSE way: REUSE.toml, .reuse/dep5, the names under LICENSES/."""
    texts = []
    toml = os.path.join(root, "REUSE.toml")
    if os.path.isfile(toml):
        texts += [l.split("=", 1)[1] for l in lines_of(toml) if re.match(r"[ \t]*SPDX-License-Identifier[ \t]*=", l)]
    dep5 = os.path.join(root, ".reuse", "dep5")
    if os.path.isfile(dep5):
        texts += [l[len("License:"):] for l in lines_of(dep5) if l.startswith("License:")]
    folder = os.path.join(root, "LICENSES")
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if name.startswith(".") or not os.path.isfile(os.path.join(folder, name)):
                continue
            stem, dot, ext = name.rpartition(".")
            texts.append(stem if dot and re.fullmatch(r"[A-Za-z]+", ext) else name)
    ids = []
    for text in texts:
        words = [w for w in re.split(r"[ \t]+", re.sub(r'["(),\[\]\r]', " ", text)) if w]
        skip = False  # the word after WITH names an exception, not a licence
        for word in words:
            if word == "WITH":
                skip = True
            elif skip:
                skip = False
            elif word not in ("OR", "AND"):
                ids.append(word)
    return ids


def house_family(root, lic):
    """The house's licence families, comma separated, code first; a prose (CC-*) family is named only
    where there is no code one; "unknown" when neither the file's text nor REUSE names any."""
    fams = set(spdx_family(i) for i in reuse_ids(root))
    path = os.path.join(root, lic)
    if os.path.isfile(path):
        fams.add(family(path))
    fams.discard("unknown")
    code = sorted(f for f in fams if not f.startswith("CC-"))
    prose = sorted(f for f in fams if f.startswith("CC-"))
    return ",".join(code) or ",".join(prose) or "unknown"


def has_enhance(root):
    base = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.rstrip(os.sep).count(os.sep) - base
        dirnames[:] = [d for d in dirnames if not (depth == 0 and d == ".git")]
        if any("ENHANCE" in n for n in filenames + dirnames):
            return True
        if depth >= 2:
            dirnames[:] = []
    return False


def scan(root):
    out = ["TAG\t" + ("CONFLICT" if has_enhance(root) else "ENHANCE")]
    first = {}
    for row in kit():
        hit = None
        for probe in row["probes"].split():
            m = matches(root, probe)
            if m:
                hit = m[0]
                break
        if hit:
            first[row["topic"]] = hit
            out.append(f"FOUND\t{row['topic']}\t{hit}")
        elif row["ours"].startswith("HOLD:"):
            out.append(f"HOLD\t{row['topic']}")
        elif row["ours"].startswith("NOT CHECKED:"):
            out.append(f"UNCHECKED\t{row['topic']}")
        else:
            out.append(f"GAP\t{row['topic']}")
    lic = first.get("licence")
    fam = house_family(root, lic) if lic else "none"
    out.append(f"LICENCE\t{fam}")
    if fam not in ("none", "unknown") and "GPL-3" not in fam.split(","):
        out.append(f"CONFLICT\tlicence\thouse {lic} reads {fam}; the kit default for code is GPL-3.0-or-later; chose house")
    cl = first.get("changelog")
    if cl and cl != "ChangeLog":
        out.append(f"CONFLICT\tchangelog\thouse keeps {cl}; the kit writes a GNU-style ChangeLog; chose house: entries go in {cl}, in its form")
    return out


def cksum(data):
    """POSIX cksum, which kg1sc keys its state directory on."""
    crc, n, tail = 0, len(data), []
    while n:
        tail.append(n & 0xFF)
        n >>= 8
    for byte in list(data) + tail:
        crc ^= byte << 24
        for _ in range(8):
            crc = ((crc << 1) ^ 0x04C11DB7) if crc & 0x80000000 else crc << 1
            crc &= 0xFFFFFFFF
    return crc ^ 0xFFFFFFFF


def state_dir(root):
    base = os.environ.get("KG_STATE") or (os.environ.get("XDG_STATE_HOME") or os.environ.get("HOME", "") + "/.local/state") + "/kid-glove"
    return f"{base}/{os.path.basename(root)}-{cksum(os.fsencode(root))}"


def git(root, *args):
    try:
        return subprocess.run(["git", "-C", root, "--no-optional-locks", *args],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return subprocess.CompletedProcess(args, 127, b"", b"")


def spdx_in(data):
    """The first SPDX-License-Identifier value in the first 12 lines, or ""."""
    for line in data.split(b"\n")[:12]:
        m = SPDX_LINE.match(line)
        if m:
            return m.group(1).decode("ascii")
    return ""


def sha256_of(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return ""


def recheck(arg, root):
    base = state_dir(root) + "/BASELINE"
    if not os.access(base, os.R_OK):
        print(f"kg1sc recheck: NOT CHECKED (no baseline; run kg1sc scan {arg} first)")
        return 2
    rows = [l.split("\t", 2) for l in lines_of(base) if l]
    value = lambda key: next((r[1] for r in rows if r[0] == key and len(r) > 1), "")
    out = []
    for r in rows:
        if r[0] != "SOURCE" or len(r) < 3:
            continue
        sha, path = r[1], r[2]
        here = root + "/" + path
        if not os.path.exists(here):
            out.append(f"TOUCHED\t{path}\tgone since the scan")
        elif sha != "dir" and sha256_of(here) != sha:
            out.append(f"TOUCHED\t{path}\tchanged since the scan")
    head, fam, cl = value("HEAD"), value("LICENCE"), value("CHANGELOG")
    changed = []
    if head and git(root, "rev-parse", "-q", "--verify", head + "^{commit}").returncode == 0:
        names = git(root, "diff", "--name-only", head, "--").stdout + git(root, "ls-files", "--others", "--exclude-standard").stdout
        changed = sorted(set(n for n in names.decode("utf-8", "surrogateescape").split("\n") if n))
    else:
        out.append("UNCHECKED\t(git)\tno baseline commit, so only the house files were compared")
    for f in changed:
        here = root + "/" + f
        if not os.path.isfile(here):
            continue
        with open(here, "rb") as fh:
            now = spdx_in(fh.read())
        if git(root, "cat-file", "-e", f"{head}:{f}").returncode == 0:
            was = spdx_in(git(root, "show", f"{head}:{f}").stdout)
            if was != now:
                if not was:
                    words = f"a licence line was added (SPDX {now}) to a file the house already had"
                elif not now:
                    words = f"its licence line (SPDX {was}) was taken out"
                else:
                    words = f"its licence line changed from SPDX {was} to SPDX {now}"
                out.append(f"TOUCHED\t{f}\t{words}")
        if not now:
            continue
        if fam in ("none", "unknown"):
            out.append(f"UNCHECKED\t{f}\tcarries SPDX {now}; the house licence is {fam}, so it was not compared (a HOLD for the owners)")
            continue
        sf = spdx_family(now)
        if sf.startswith("CC-"):
            continue
        if sf not in fam.split(","):
            out.append(f"TRAMPLE\t{f}\tcarries SPDX {now}; the house licence is {fam}")
    if cl and changed and cl not in changed:
        out.append(f"GAP\t{cl}\t{len(changed)} file(s) changed; {cl} does not record them yet")
    if out:
        print("\n".join(out))
    if any(l.startswith("TRAMPLE\t") for l in out):
        return 1
    return 2 if any(l.startswith("UNCHECKED\t") for l in out) else 0


if __name__ == "__main__":
    a = sys.argv
    if len(a) == 4 and a[1] == "scan" and a[3] == "--raw":
        print("\n".join(scan(os.path.abspath(a[2]))))
    elif len(a) == 4 and a[1] == "recheck" and a[3] == "--raw":
        sys.exit(recheck(a[2], os.path.abspath(a[2])))
    else:
        sys.exit(__doc__)
