"""Check the committed S6 exact-run cache: recompute a random sample of its runs from their keys, and compare the
unconstrained (S5) cost recorded with every S6 run against the frozen S5 exact cache where the keys overlap.

    python verify_cache_sample.py [N]      (default 300 runs, seed 20261013)

The key holds the entry state to 10 significant digits, so a recomputed cost agrees to about 1e-9, not exactly;
tolerance 1e-6 relative (NaN must stay NaN). Writes cache_check.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0], "s6"] + sys.argv[1:]          # run_stats_wrapper reads the treatment from argv[1]
import run_stats_wrapper as W  # noqa: E402

STATE = ("X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C")


def job_of(key):
    state, _, pert = key.partition("#")
    e = dict(zip(STATE, map(float, state.split("|"))))
    p = {k: float(v) for k, v in (x.split("=") for x in pert.split("|") if x)}
    return e, p


def same(a, b, rtol=1e-6):
    return (np.isnan(a) & np.isnan(b)) | (np.abs(a - b) <= rtol * np.abs(b))


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    cache = pd.read_csv(HERE / "stats_s6" / "exact_cache.csv.gz", dtype={"key": str, "cost": float})
    pick = cache.sample(n=min(n, len(cache)), random_state=20261013)
    got = np.array([W.exact_cost_s6(job_of(k)) for k in pick.key])
    ok_s6 = same(got, pick.cost.to_numpy())
    x = pd.read_csv(HERE / "stats_s6" / "s5_crosscheck.csv.gz", dtype={"key": str})
    fz = pd.read_csv(W.FROZEN / "exact_cache.csv.gz", dtype={"key": str, "cost": float})
    m = x.merge(fz, on="key")
    ok_s5 = same(m.cost_s5.to_numpy(), m.cost.to_numpy(), rtol=1e-9)
    out = dict(s6_cache_runs=int(len(cache)), s6_sample=int(len(pick)), s6_sample_agree=int(ok_s6.sum()),
               s6_sample_max_rel_diff=float(np.nanmax(np.abs(got / pick.cost.to_numpy() - 1))),
               s5_recorded_with_s6_runs=int(len(x)), s5_overlap_with_frozen_cache=int(len(m)),
               s5_overlap_agree=int(ok_s5.sum()))
    (HERE / "cache_check.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    if not (ok_s6.all() and ok_s5.all()):
        sys.exit("cache check failed")


if __name__ == "__main__":
    main()
