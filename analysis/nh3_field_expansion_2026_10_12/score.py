"""Thin wrapper around the frozen scoring code (analysis/nh3_field_2026_10_06/run_field_chain.py and
run_printed_primary.py), imported unchanged. It only redirects the input records and the output folder.

    python score.py chain <label> <records.csv> [--corrections batch2_corrections.csv] [--paper-set file] [--workers N]
        -> runs/<label>/{candidates.csv, group_metrics.csv, selfcheck_supported.csv, summary.json,
                         summary_printed.json, group_metrics_printed.csv, candidates_printed.csv}
    python score.py pool <label> <run_dir_or_frozen> <run_dir> ...
        -> runs/<label>/: the union of the scored entries of each run (each with its own chain costs), aggregated with
           the frozen aggregate and printed-primary code

Corrections (batch2_corrections.csv: doi, entry_label, field, extracted, corrected, ...) replace a field of
records_normalized.csv before the chain; every applied correction is listed in runs/<label>/corrections_applied.csv.

Model version (analysis/nh3_model.py, read by run_field_chain): NH3_MODEL=1.1 (default) scores on NH3-FINAL-1.1 and
writes runs/<label>/ in this folder, as before. NH3_MODEL=1.2 scores on NH3-FINAL-1.2 (harness root $NH3_HARNESS_1_2,
run nh3_final_1_2_20261013) and writes nh3_1_2/runs/<label>/ with the same files. The run arguments of `pool` are
written as for 1.1 (../nh3_field_2026_10_06, runs/<label>) and are read from the selected model's folders: the frozen
round 1 from ../nh3_field_2026_10_06/nh3_1_2/ (run_field_chain.py under NH3_MODEL=1.2) and runs/<label> from
nh3_1_2/runs/<label>. The input records and corrections files are model-independent and shared.

    NH3_MODEL=1.2 NH3_HARNESS_1_2=<1.2 source_harness with its cache/> python score.py chain|pool ...
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FROZEN = REPO / "analysis" / "nh3_field_2026_10_06"
os.environ.setdefault("NH3_HARNESS", r"D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1")
sys.path.insert(0, str(FROZEN))
_argv, sys.argv = sys.argv, sys.argv[:1]
import run_field_chain as F  # noqa: E402
import run_printed_primary as P  # noqa: E402
sys.argv = _argv
NM = F.NM                         # analysis/nh3_model.py, the version run_field_chain selected
FROZEN_OUT = F.OUT                # the frozen round-1 run of that model: FROZEN (1.1) or FROZEN/nh3_1_2 (1.2)
RUNS = NM.out_dir(HERE) / "runs"  # runs/ (1.1) or nh3_1_2/runs/ (1.2)


def stage(run: Path, records: pd.DataFrame):
    """run/agent/nh3_field/out/records_normalized.csv: the records run_printed_primary reads (REPO -> run)."""
    p = run / "agent" / "nh3_field" / "out"
    p.mkdir(parents=True, exist_ok=True)
    records.to_csv(p / "records_normalized.csv", index=False, encoding="utf-8")
    return p / "records_normalized.csv"


def apply_corrections(rec: pd.DataFrame, path: Path, run: Path) -> pd.DataFrame:
    cor = pd.read_csv(path, keep_default_na=False, na_values=[""], dtype=str)
    rec = rec.copy()
    log = []
    for r in cor.to_dict("records"):
        m = (rec.doi == r["doi"]) & (rec.entry_label == r["entry_label"])
        if m.sum() != 1:
            raise SystemExit(f"correction does not match exactly one record: {r}")
        old = rec.loc[m, r["field"]].iloc[0]
        new = r["corrected"]
        rec[r["field"]] = rec[r["field"]].astype(object)
        rec.loc[m, r["field"]] = float(new) if new not in ("", None) and _isnum(new) else (None if new in ("", None) else new)
        log.append(dict(doi=r["doi"], entry_label=r["entry_label"], field=r["field"], before=old, after=new))
    pd.DataFrame(log).to_csv(run / "corrections_applied.csv", index=False)
    print(f"{len(log)} corrections applied")
    return rec


def _isnum(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def printed(run: Path):
    """run_printed_primary.main() with its folder (HERE, OUT) and repository root (REPO) pointed at the run."""
    P.HERE, P.REPO, P.OUT = run, run, run
    P.main()


def run_folder(d: Path) -> Path:
    """A run argument as written for 1.1 (../nh3_field_2026_10_06 or runs/<label>) -> the folder holding that run for
    the selected model (the same folder for 1.1)."""
    if d.resolve() == FROZEN.resolve():
        return FROZEN_OUT
    try:
        rel = d.resolve().relative_to((HERE / "runs").resolve())
    except ValueError:
        return d
    return RUNS / rel


def chain(args):
    run = RUNS / args.label
    run.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(args.records, keep_default_na=False, na_values=[""])
    if args.corrections:
        rec = apply_corrections(rec, Path(args.corrections), run)
    staged = stage(run, rec)
    F.RECORDS, F.HERE, F.OUT = staged, run, run
    if args.paper_set:
        F.PAPER_SET = Path(args.paper_set)
    sys.argv = [sys.argv[0], "--workers", str(args.workers)] + (["--skip-selfcheck"] if args.skip_selfcheck else [])
    F.main()
    printed(run)


def pool(args):
    run = RUNS / args.label
    run.mkdir(parents=True, exist_ok=True)
    cands, recs, read = [], [], []
    for a in map(Path, args.runs):
        d = run_folder(a)
        read.append(d)
        rec_path = (REPO / "agent" / "nh3_field" / "out" / "records_normalized.csv" if a.resolve() == FROZEN.resolve()
                    else d / "agent" / "nh3_field" / "out" / "records_normalized.csv")
        cands.append(pd.read_csv(d / "candidates.csv", keep_default_na=False, na_values=[""]))
        recs.append(pd.read_csv(rec_path, keep_default_na=False, na_values=[""]))
    c = pd.concat(cands, ignore_index=True)
    r = pd.concat(recs, ignore_index=True)
    assert not set.intersection(*[set(x.doi) for x in cands]), "a paper appears in two runs"
    c.to_csv(run / "candidates.csv", index=False, float_format="%.6g")
    stage(run, r)
    # summary.json "primary" of the pooled all-entries set, as run_field_chain computes it (read back by
    # run_printed_primary's consistency assertion)
    c2 = pd.read_csv(run / "candidates.csv", keep_default_na=False, na_values=[""])
    prim = c2[c2.status.str.startswith("primary") & c2.cost_USD_t.notna() & c2.duplicate_in_group.isna()].copy()
    gm, s = F.aggregate(prim, label="pooled: paper's own rate basis, plant cost without metal recovery", boot=True)
    gm.to_csv(run / "group_metrics.csv", index=False, float_format="%.6g")
    summary = dict(pooled_from=[str(x) for x in args.runs], primary=s)
    if NM.VERSION != "1.1":          # the 1.1 summary keeps its committed keys; later versions name their run
        A = NM.anchors()
        summary = dict(model=dict(label=A["label"], run=A["run"], process_states=A["NSTATE"], F_CAL=A["F_CAL"],
                                  Fe_USD_t=A["Fe"]),
                       pooled_from=[str(x) for x in args.runs],
                       pooled_from_read=[x.resolve().relative_to(REPO.resolve()).as_posix() for x in read], primary=s)
    (run / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    printed(run)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("chain")
    a.add_argument("label")
    a.add_argument("records")
    a.add_argument("--corrections")
    a.add_argument("--paper-set")
    a.add_argument("--workers", type=int, default=1)
    a.add_argument("--skip-selfcheck", action="store_true")
    b = sub.add_parser("pool")
    b.add_argument("label")
    b.add_argument("runs", nargs="+")
    args = ap.parse_args()
    chain(args) if args.cmd == "chain" else pool(args)
