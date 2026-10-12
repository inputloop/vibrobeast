#!/usr/bin/env python3
# Copyright (C) 2026 Corwin Brust <corwin@bru.st>
# Authored by Mentat (for Corwin).
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of vibrobeast.  vibrobeast is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.  It is
# distributed WITHOUT ANY WARRANTY; see <https://www.gnu.org/licenses/>.
"""lens - structure a cross-model LENS reading and measure model (dis)agreement.

Task A. The LENS is the reflection discipline (making-vibrobeast .md, section 1):
four views held apart, then persona and its inverse, then reframe each point from
principles, then notes (unless the writing itself is the danger).

  a_self              (a) my own view
  b_ascribed          (b) the view I ascribe you - the externalized iT node, drawn
  c_infl_on_mine      (c) your influence over mine
  d_mine_on_ascribed  (d) mine over the ascribed
  persona             the persona pass
  inverse             its inverse

CROSS-MODEL is the new part: the SAME material is read by more than one model, and
their convergence/divergence is the measurement - the eclipse-pass opposed-bias
idea generalized across models (two opposed biases -> where they converge is the
stable result; here, N models -> where they converge is the stable reading).

The shared spine: the subject material is pinned by sha256, so we PROVE every model
read identical bytes. A reading keyed to a subject_sha that no longer matches the
pinned subject is flagged - you cannot compare readings of different bytes.

Measurement is honest: convergence is EXACT match of a human-supplied `stance`
token per view. A difflib ratio over the prose `claim` is offered only as a
non-authoritative HINT (kept, never the verdict - see the design losers).

Reruns count (2026-09-27). A reading is (subject_sha, model, view, run). A second
`add` by the same model for the same view is a NEW run, never a replacement; pass
--run N to correct run N in place. Before this, the identity had no run, so a model
that disagreed with itself was stored as one settled reading and `converge` could
print CONVERGE over a coin toss (c4 writing/second-user/lens-rerun-probe.sh, case 1).
`converge` now prints a second, within-model verdict beside the cross-model one:
  SPLIT-WITHIN  some model's reruns gave different stances on this view
  STEADY        every model with two or more runs agreed with itself
  ONE-RUN       no model has a second run, so self-agreement is unmeasured
Read CONVERGE as settled only beside STEADY. The cross-model verdict counts every
run's stance, so a split model can never be read as agreeing with the others.

import-json accepts another model's reading (e.g. Copilot); a reading whose
declared subject_sha is not the pinned sha is REFUSED and receipted, never
stamped over (selftest proves it). Accepted shapes:
  {"model":"copilot","subject_sha":"..","views":{"c_infl_on_mine":{"stance":"..",
      "claim":"..","reframe":"..","note":".."}, ...}}
  or a list of those, or a flat list of
  {"model":"..","view":"..","stance":"..","claim":"..",...}.

stdlib only. Canon governs; the pub shelf canon (canon/principles/) is source of truth. Minted, not vouched.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ferry_core as fc  # noqa: E402

VIEWS = ["a_self", "b_ascribed", "c_infl_on_mine", "d_mine_on_ascribed",
         "persona", "inverse"]
VIEW_LABEL = {
    "a_self": "(a) my own view",
    "b_ascribed": "(b) the view I ascribe you (the drawn iT node)",
    "c_infl_on_mine": "(c) your influence over mine",
    "d_mine_on_ascribed": "(d) mine over the ascribed",
    "persona": "persona pass",
    "inverse": "inverse of the persona pass",
}
SUBJ_HEADER = ["id", "title", "path", "sha256", "bytes", "notes_ok", "ts"]
LENS_HEADER = ["subject_id", "subject_sha", "model", "view", "stance", "claim",
               "principle_reframe", "note", "ts", "run"]

# Test switches. selftest --prove-red turns these off to plant the old faults
# (a rerun replaces; a split goes unreported) and must then see the checks fail.
_KEEP_RUNS = True
_REPORT_SPLIT = True


def _run_of(r):
    """A row written before 2026-09-27 has no run column: it was run 1."""
    return (r.get("run") or "1").strip() or "1"


def _load(path):
    header, rows = fc.read_tsv(path)
    return rows if header else []


# --- pin a subject (shared spine: identical bytes, proven) ----------------

def pin(path, title, subjects, receipts, notes_ok=True, subj_id=None):
    path = os.path.abspath(path)
    sha = fc.sha256_file(path)
    rec = {
        "id": subj_id or os.path.basename(path),
        "title": title or os.path.basename(path),
        "path": path, "sha256": sha, "bytes": str(os.path.getsize(path)),
        "notes_ok": "1" if notes_ok else "0", "ts": fc.now_iso(),
    }
    rows = _load(subjects)
    action = fc.upsert(rows, "id", rec)
    fc.write_tsv(subjects, SUBJ_HEADER, rows)
    fc.append_receipt(receipts, "pin", "OK",
                      {"id": rec["id"], "sha": sha, "action": action},
                      tail="pinned")
    return rec


def _subject(subjects, subject_id):
    for r in _load(subjects):
        if r.get("id") == subject_id:
            return r
    return None


# --- add / import readings ------------------------------------------------

def add_reading(subjects, lens, receipts, subject_id, model, view, stance,
                claim, reframe="", note="", run=None):
    if view not in VIEWS:
        raise ValueError("unknown view %r; one of %s" % (view, VIEWS))
    subj = _subject(subjects, subject_id)
    if subj is None:
        raise KeyError("pin the subject %r first" % subject_id)
    if subj.get("notes_ok", "1") == "0":
        note = ""  # 'detailed notes unless the writing itself is the danger'
    rec = {
        "subject_id": subject_id, "subject_sha": subj["sha256"],
        "model": model, "view": view, "stance": stance, "claim": claim,
        "principle_reframe": reframe, "note": note, "ts": fc.now_iso(),
    }
    rows = _load(lens)
    same = [r for r in rows if (r.get("subject_sha"), r.get("model"),
                                r.get("view")) == (rec["subject_sha"], model, view)]
    if run is None:
        # a second reading by the same model is a rerun, kept beside the first
        run = str(max([int(_run_of(r)) for r in same if _run_of(r).isdigit()] or [0]) + 1)
    rec["run"] = str(run)
    # identity of a reading = (subject_sha, model, view, run): only an explicit
    # --run N replaces, and only that run (before 2026-09-27 run was not in the key)
    key = (rec["subject_sha"], model, view, rec["run"])
    replaced = False
    for i, r in enumerate(rows):
        rkey = (r.get("subject_sha"), r.get("model"), r.get("view"))
        if _KEEP_RUNS:
            rkey = rkey + (_run_of(r),)
        if rkey == (key if _KEEP_RUNS else key[:3]):
            rows[i] = rec
            replaced = True
            break
    if not replaced:
        rows.append(rec)
    fc.write_tsv(lens, LENS_HEADER, rows)
    fc.append_receipt(receipts, "reading", "OK",
                      {"subject": subject_id, "model": model, "view": view,
                       "run": rec["run"], "sha": rec["subject_sha"],
                       "action": "replace" if replaced else "insert"},
                      tail="landed")
    return rec


def normalize_reading(obj):
    """Flatten an imported JSON reading into row dicts (model, view, ...)."""
    out = []
    items = obj if isinstance(obj, list) else [obj]
    for it in items:
        if "views" in it:  # nested shape
            model = it.get("model", "?")
            declared = it.get("subject_sha", "")
            for view, d in it["views"].items():
                out.append({"model": model, "view": view,
                            "run": d.get("run", it.get("run")),
                            "declared_sha": d.get("subject_sha", declared),
                            "stance": d.get("stance", ""),
                            "claim": d.get("claim", ""),
                            "reframe": d.get("reframe", ""),
                            "note": d.get("note", "")})
        elif "view" in it:  # flat shape
            out.append({"model": it.get("model", "?"), "view": it["view"],
                        "run": it.get("run"),
                        "declared_sha": it.get("subject_sha", ""),
                        "stance": it.get("stance", ""),
                        "claim": it.get("claim", ""),
                        "reframe": it.get("reframe", ""),
                        "note": it.get("note", "")})
    return out


def import_json(jsonfile, subjects, lens, receipts, subject_id):
    """Import readings; a reading whose declared subject_sha is not the pin
    is REFUSED (receipted), never stamped over. Returns (added, refused).

    Before 2026-09-11 the declared sha was dropped in normalize_reading and
    add_reading stamped the pin's sha over every import, so a reader of the
    wrong bytes went in green. Undeclared sha is accepted but receipted as
    declared=none - weaker evidence, marked, not hidden.
    """
    with open(jsonfile, encoding="utf-8") as fh:
        obj = json.load(fh)
    subj = _subject(subjects, subject_id)
    if subj is None:
        raise KeyError("pin the subject %r first" % subject_id)
    pin_sha = subj["sha256"]
    added, refused = [], []
    for r in normalize_reading(obj):
        declared = (r.get("declared_sha") or "").strip().lower()
        if declared and declared != pin_sha:
            fc.append_receipt(receipts, "reading", "REFUSED",
                              {"subject": subject_id, "model": r["model"],
                               "view": r["view"], "declared": declared,
                               "pin": pin_sha, "why": "sha-mismatch"},
                              tail="refused")
            refused.append(r)
            continue
        rec = add_reading(subjects, lens, receipts, subject_id,
                          r["model"], r["view"], r["stance"],
                          r["claim"], r.get("reframe", ""),
                          r.get("note", ""),
                          run=(str(r["run"]) if r.get("run") is not None else None))
        if not declared:
            fc.append_receipt(receipts, "reading", "NOTE",
                              {"subject": subject_id, "model": r["model"],
                               "view": r["view"], "declared": "none",
                               "pin": pin_sha},
                              tail="sha undeclared by reader")
        added.append(rec)
    return added, refused


def selftest():
    """Prove import-json can go red (a wrong declared sha is refused) and that
    the rerun verdicts can fire (SPLIT-WITHIN, STEADY, ONE-RUN)."""
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as td:
        subjects = os.path.join(td, "subjects.tsv")
        lens = os.path.join(td, "lens.tsv")
        receipts = os.path.join(td, "receipts.log")
        subj_path = os.path.join(td, "subject.txt")
        with open(subj_path, "w", encoding="utf-8") as fh:
            fh.write("the pinned bytes\n")
        rec = pin(subj_path, "t", subjects, receipts, subj_id="s1")
        good, bad = rec["sha256"], "0" * 64

        def imp(payload):
            jp = os.path.join(td, "in.json")
            with open(jp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            return import_json(jp, subjects, lens, receipts, "s1")

        a, r = imp({"model": "m1", "subject_sha": bad,
                    "views": {"a_self": {"stance": "x", "claim": "c"}}})
        checks.append(("wrong sha (nested) refused", (len(a), len(r)) == (0, 1)))
        a, r = imp([{"model": "m2", "view": "a_self", "subject_sha": bad,
                     "stance": "x", "claim": "c"}])
        checks.append(("wrong sha (flat) refused", (len(a), len(r)) == (0, 1)))
        a, r = imp({"model": "m3", "subject_sha": good.upper(),
                    "views": {"a_self": {"stance": "x", "claim": "c"}}})
        checks.append(("right sha accepted (case-folded)", (len(a), len(r)) == (1, 0)))
        a, r = imp({"model": "m4",
                    "views": {"a_self": {"stance": "x", "claim": "c"}}})
        checks.append(("undeclared sha accepted", (len(a), len(r)) == (1, 0)))
        rows = _load(lens)
        checks.append(("refused readings never landed",
                       sorted(x["model"] for x in rows) == ["m3", "m4"]))
        with open(receipts, encoding="utf-8") as fh:
            log = fh.read()
        checks.append(("refusal receipted", "REFUSED" in log and "sha-mismatch" in log))
        checks.append(("undeclared receipted", "sha undeclared" in log))
        checks.append(("mutant: the old path stamped pin over declared",
                       all(x["subject_sha"] == good for x in rows)))
    checks += _rerun_checks()
    bad_n = 0
    for name, ok in checks:
        print("%s %s" % ("ok  " if ok else "FAIL", name))
        bad_n += 0 if ok else 1
    return 1 if bad_n else 0


def _rerun_checks():
    """The 2026-09-27 checks: a rerun is kept, and a split is reported.
    Case 1 is c4 writing/second-user/lens-rerun-probe.sh case 1, verbatim."""
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as td:
        S = os.path.join(td, "subjects.tsv")
        L = os.path.join(td, "lens.tsv")
        R = os.path.join(td, "receipts.log")
        sp = os.path.join(td, "subj.txt")
        with open(sp, "w", encoding="utf-8") as fh:
            fh.write("subject text\n")
        for sid in ("S1", "S3", "S4", "S5"):
            pin(sp, "probe", S, R, subj_id=sid)

        def add(sid, model, stance, run=None):
            return add_reading(S, L, R, sid, model, "a_self", stance,
                               "option " + stance, run=run)

        def view(sid):
            return converge(L, sid, subjects=S)["per_view"]["a_self"]

        # case 1: sonnet-5 says A then B; opus says B
        add("S1", "sonnet-5", "A"); add("S1", "sonnet-5", "B"); add("S1", "opus", "B")
        mine = [r for r in _load(L) if r["subject_id"] == "S1" and r["model"] == "sonnet-5"]
        checks.append(("a rerun is kept beside the first (2 rows, runs 1 and 2)",
                       sorted(_run_of(r) for r in mine) == ["1", "2"]))
        d = view("S1")
        checks.append(("probe case 1 no longer reads CONVERGE", d["verdict"] != "CONVERGE"))
        checks.append(("SPLIT-WITHIN fires when a model disagrees with itself",
                       d["within"] == "SPLIT-WITHIN" and d["split_models"] == ["sonnet-5"]))
        checks.append(("the rendered line carries both verdicts",
                       "[DIVERGE  ] [SPLIT-WITHIN] (a) my own view"
                       in render(converge(L, "S1", subjects=S))))
        # every rerun agrees -> CONVERGE beside STEADY
        add("S3", "m1", "X"); add("S3", "m1", "X"); add("S3", "m2", "X")
        d = view("S3")
        checks.append(("STEADY when every rerun agrees",
                       (d["verdict"], d["within"]) == ("CONVERGE", "STEADY")))
        # nobody reran -> ONE-RUN (self-agreement unmeasured)
        add("S4", "m1", "X"); add("S4", "m2", "X")
        d = view("S4")
        checks.append(("ONE-RUN when nobody reran",
                       (d["verdict"], d["within"]) == ("CONVERGE", "ONE-RUN")))
        # --run N corrects run N in place, and only run N
        add("S1", "sonnet-5", "B", run="1")
        mine = sorted((_run_of(r), r["stance"]) for r in _load(L)
                      if r["subject_id"] == "S1" and r["model"] == "sonnet-5")
        checks.append(("--run 1 corrects run 1 only", mine == [("1", "B"), ("2", "B")]))
        # a lens.tsv written before the run column existed: its rows are run 1
        rows = _load(L)
        legacy = dict(rows[0], subject_id="S5", model="old", stance="Y")
        legacy.pop("run", None)
        old_header = [c for c in LENS_HEADER if c != "run"]
        fc.write_tsv(L, old_header, rows + [legacy])
        add("S5", "old", "Z")
        olds = sorted((_run_of(r), r["stance"]) for r in _load(L)
                      if r["subject_id"] == "S5" and r["model"] == "old")
        checks.append(("a pre-run row reads as run 1; the next add is run 2",
                       olds == [("1", "Y"), ("2", "Z")]))
        # import-json carries a declared run
        jp = os.path.join(td, "in.json")
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump([{"model": "imp", "view": "a_self", "run": 5,
                        "stance": "Q", "claim": "c"}], fh)
        import_json(jp, S, L, R, "S3")
        got = [_run_of(r) for r in _load(L) if r["model"] == "imp"]
        checks.append(("import-json keeps a declared run", got == ["5"]))
    return checks


def prove_red():
    """Plant each old fault and require the checks that guard it to fail."""
    global _KEEP_RUNS, _REPORT_SPLIT
    plants = [
        ("the old identity: a rerun REPLACES (run not in the key)", "_KEEP_RUNS",
         {"a rerun is kept beside the first (2 rows, runs 1 and 2)",
          "probe case 1 no longer reads CONVERGE"}),
        ("a split goes unreported (no within-model verdict)", "_REPORT_SPLIT",
         {"SPLIT-WITHIN fires when a model disagrees with itself",
          "the rendered line carries both verdicts"}),
    ]
    ok_all = True
    for label, flag, must_fail in plants:
        globals()[flag] = False
        try:
            res = dict(_rerun_checks())
        finally:
            globals()[flag] = True
        failed = {n for n, ok in res.items() if not ok}
        caught = must_fail <= failed
        ok_all = ok_all and caught
        print("%s planted: %s -> failing: %s" % ("ok  " if caught else "FAIL", label,
                                                 ", ".join(sorted(failed)) or "(none)"))
    res = dict(_rerun_checks())
    clean = all(res.values())
    print("%s control: no plant -> every rerun check passes" % ("ok  " if clean else "FAIL"))
    print("prove-red: %s" % ("every planted fault went RED and the control stayed green"
                             if ok_all and clean else "FAILED"))
    return 0 if ok_all and clean else 1


# --- the measurement: cross-model convergence -----------------------------

def converge(lens, subject_id, subjects=None):
    """Per view, do the models agree? Exact stance match => CONVERGE.

    Returns a dict with per-view verdicts and a summary. A claim-similarity ratio
    (difflib) rides along as a HINT only - never the verdict.
    """
    rows = [r for r in _load(lens) if r.get("subject_id") == subject_id]
    # stale-subject guard: every reading must be of the pinned bytes
    stale = []
    if subjects is not None:
        subj = _subject(subjects, subject_id)
        pin_sha = subj["sha256"] if subj else None
        for r in rows:
            if pin_sha and r.get("subject_sha") != pin_sha:
                stale.append((r.get("model"), r.get("view")))

    per_view = {}
    for view in VIEWS:
        vrows = [r for r in rows if r.get("view") == view]
        # every run of every model, in run order: model -> [(run, stance), ...]
        runs = {}
        for r in sorted(vrows, key=lambda r: (r["model"], int(_run_of(r))
                                              if _run_of(r).isdigit() else 0)):
            runs.setdefault(r["model"], []).append((_run_of(r), r.get("stance", "")))
        models = runs
        stances = {m: ",".join(s for _, s in rs) for m, rs in runs.items()}
        distinct = sorted({s for rs in runs.values() for _, s in rs})
        if len(models) < 2:
            verdict = "SINGLE" if models else "GAP"
        elif len(distinct) == 1:
            verdict = "CONVERGE"
        else:
            verdict = "DIVERGE"
        # within-model: did each model agree with itself across its reruns?
        split = sorted(m for m, rs in runs.items() if len({s for _, s in rs}) > 1)
        if not _REPORT_SPLIT:
            split = []
        if split:
            within = "SPLIT-WITHIN"
        elif any(len(rs) > 1 for rs in runs.values()):
            within = "STEADY"
        else:
            within = "ONE-RUN" if runs else "-"
        # non-authoritative hint: pairwise claim similarity
        claims = [r.get("claim", "") for r in vrows]
        hint = None
        if len(claims) >= 2:
            ratios = []
            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    ratios.append(difflib.SequenceMatcher(
                        None, claims[i], claims[j]).ratio())
            hint = round(sum(ratios) / len(ratios), 2)
        per_view[view] = {"verdict": verdict, "within": within,
                          "split_models": split, "models": list(models),
                          "runs": {m: len(rs) for m, rs in runs.items()},
                          "stances": stances, "distinct": distinct,
                          "claim_similarity_hint": hint}

    verdicts = [v["verdict"] for v in per_view.values()]
    summary = {
        "subject_id": subject_id,
        "n_models": len(sorted({r["model"] for r in rows})),
        "converge": verdicts.count("CONVERGE"),
        "diverge": verdicts.count("DIVERGE"),
        "single": verdicts.count("SINGLE"),
        "gap": verdicts.count("GAP"),
        "diverging_views": [v for v, d in per_view.items()
                            if d["verdict"] == "DIVERGE"],
        "split_within": [v for v, d in per_view.items()
                         if d["within"] == "SPLIT-WITHIN"],
        "stale_readings": stale,
    }
    return {"summary": summary, "per_view": per_view}


def render(report):
    s = report["summary"]
    out = []
    out.append("LENS convergence - subject %s  (%d models)" %
               (s["subject_id"], s["n_models"]))
    out.append("  converge=%d  diverge=%d  single=%d  gap=%d  split-within=%d" %
               (s["converge"], s["diverge"], s["single"], s["gap"],
                len(s["split_within"])))
    out.append("  (right column: did each model agree with itself across reruns?"
               " read CONVERGE as settled only beside STEADY)")
    if s["stale_readings"]:
        out.append("  !! STALE readings (not of pinned bytes): %s" %
                   s["stale_readings"])
    out.append("  minions released before the persona pass (eclipse move 3a)")
    for view in VIEWS:
        d = report["per_view"][view]
        line = "  [%-9s] [%-12s] %s" % (d["verdict"], d["within"], VIEW_LABEL[view])
        out.append(line)
        if d["verdict"] == "DIVERGE" or d["within"] == "SPLIT-WITHIN":
            for m in d["models"]:
                out.append("      %-10s stance=%s  (runs: %d)%s" % (
                    m, d["stances"][m], d["runs"][m],
                    "  SPLIT" if m in d["split_models"] else ""))
        if d["claim_similarity_hint"] is not None:
            out.append("      (hint only: claim-similarity %.2f - NOT the verdict)"
                       % d["claim_similarity_hint"])
    return "\n".join(out)


# --- cli ------------------------------------------------------------------

def _defaults():
    here = os.path.dirname(os.path.abspath(__file__))
    seat = os.path.abspath(os.path.join(here, "..", "mainmem", "lens"))
    return (os.path.join(seat, "subjects.tsv"),
            os.path.join(seat, "lens.tsv"),
            os.path.join(seat, "receipts.log"))


def main(argv=None):
    dsub, dlens, drec = _defaults()
    ap = argparse.ArgumentParser(description="cross-model LENS reading + measure")
    ap.add_argument("--subjects", default=dsub)
    ap.add_argument("--lens", default=dlens)
    ap.add_argument("--receipts", default=drec)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("views", help="list the canonical views")

    p = sub.add_parser("pin", help="pin subject material by sha256")
    p.add_argument("path")
    p.add_argument("--title", default="")
    p.add_argument("--id", default=None)
    p.add_argument("--no-notes", action="store_true",
                   help="the writing itself is the danger: drop notes")

    a = sub.add_parser("add", help="add one model's reading for one view")
    a.add_argument("--subject", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--view", required=True)
    a.add_argument("--stance", required=True)
    a.add_argument("--claim", required=True)
    a.add_argument("--reframe", default="")
    a.add_argument("--note", default="")
    a.add_argument("--run", default=None,
                   help="correct run N in place; omitted, a second reading by the "
                        "same model is kept as the next run")

    j = sub.add_parser("import-json", help="import another model's reading")
    j.add_argument("jsonfile")
    j.add_argument("--subject", required=True)

    st = sub.add_parser("selftest", help="prove the refusals and the rerun verdicts can fire")
    st.add_argument("--prove-red", action="store_true",
                    help="plant the old faults (a rerun replaces; a split goes "
                         "unreported) and require the checks to fail")

    c = sub.add_parser("converge", help="measure cross-model (dis)agreement")
    c.add_argument("--subject", required=True)
    c.add_argument("--json", action="store_true")

    a_ = ap.parse_args(argv)
    if a_.cmd == "views":
        for v in VIEWS:
            print("%-18s %s" % (v, VIEW_LABEL[v]))
    elif a_.cmd == "pin":
        rec = pin(a_.path, a_.title, a_.subjects, a_.receipts,
                  notes_ok=not a_.no_notes, subj_id=a_.id)
        print("pinned", rec["sha256"], rec["id"])
    elif a_.cmd == "add":
        rec = add_reading(a_.subjects, a_.lens, a_.receipts, a_.subject,
                          a_.model, a_.view, a_.stance, a_.claim,
                          a_.reframe, a_.note, run=a_.run)
        print("added", rec["model"], rec["view"], "run", rec["run"])
    elif a_.cmd == "import-json":
        added, refused = import_json(a_.jsonfile, a_.subjects, a_.lens,
                                     a_.receipts, a_.subject)
        print("imported", len(added), "readings; refused", len(refused),
              "(declared subject_sha is not the pin)" if refused else "")
        if refused:
            return 1
    elif a_.cmd == "selftest":
        return prove_red() if a_.prove_red else selftest()
    elif a_.cmd == "converge":
        report = converge(a_.lens, a_.subject, subjects=a_.subjects)
        if a_.json:
            print(json.dumps(report, indent=2))
        else:
            print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
