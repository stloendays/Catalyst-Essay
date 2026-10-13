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
    """run_printed_primary.main() with its folder (HERE) and repository root (REPO) pointed at the run."""
    P.HERE, P.REPO = run, run
    P.main()


def chain(args):
    run = HERE / "runs" / args.label
    run.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(args.records, keep_default_na=False, na_values=[""])
    if args.corrections:
        rec = apply_corrections(rec, Path(args.corrections), run)
    staged = stage(run, rec)
    F.RECORDS, F.HERE = staged, run
    if args.paper_set:
        F.PAPER_SET = Path(args.paper_set)
    sys.argv = [sys.argv[0], "--workers", str(args.workers)] + (["--skip-selfcheck"] if args.skip_selfcheck else [])
    F.main()
    printed(run)


def pool(args):
    run = HERE / "runs" / args.label
    run.mkdir(parents=True, exist_ok=True)
    cands, recs = [], []
    for d in map(Path, args.runs):
        rec_path = (REPO / "agent" / "nh3_field" / "out" / "records_normalized.csv" if d.resolve() == FROZEN.resolve()
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
    (run / "summary.json").write_text(json.dumps(dict(pooled_from=[str(x) for x in args.runs], primary=s), indent=1,
                                                 default=float) + "\n", encoding="utf-8")
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
