"""Parts A-C of the frozen statistics script under the S5 (frozen) or S6 (inlet-limited) plant cost.

Thin wrapper around analysis/meoh_main_result_stats_2026_10_06/run_main_result_stats.py: that module is imported
unchanged and only the plant-cost treatment is swapped. Bootstrap, regret curve, error model, draws, random
streams, response surface, exact off-grid runs and validation replicates are the frozen code.

    python run_stats_wrapper.py s5    frozen treatment, read from the frozen exact cache (reproduction check)
    python run_stats_wrapper.py s6    inlet-limited loop: every perturbed entry is re-costed with the constrained
                                      purge (meoh_general_model.optimal_purge(constrained=True), reactor-inlet
                                      CH4 + CO + N2 <= NONREACTIVE_MAX = 6.86 %); an entry with no eligible purge
                                      level is infeasible in that draw and leaves both leaderboards (frozen rule)

S6 swaps:
  - load(): the frozen candidates with cost_recycled_opt replaced by the frozen S6 column cost_recycled_opt_inlet,
    and group_metrics_inlet_limit.csv as the reference for the point-estimate assertion;
  - exact_cost(): the constrained optimum on the same conversion-capped sweep with recycled CO (x_co =
    recycled_central). Each run also records the unconstrained (S5) cost of the same sweep in s5_crosscheck.csv.gz,
    compared with the frozen S5 exact cache where the keys overlap.
Outputs go to stats_s5/ or stats_s6/ next to this file.
"""
import os
import shutil
import sys
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FROZEN = REPO / "analysis" / "meoh_main_result_stats_2026_10_06"
sys.path.insert(0, str(FROZEN))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import run_main_result_stats as R  # noqa: E402

TREATMENT = sys.argv[1] if len(sys.argv) > 1 else "s6"
assert TREATMENT in ("s5", "s6")
OUT = HERE / f"stats_{TREATMENT}"
OUT.mkdir(exist_ok=True)
R.HERE = OUT
R.CACHE_FILE = OUT / "exact_cache.csv.gz"
G = R.G
_S5_SEEN = {}


def exact_cost_both(args):
    """(S5 cost, S6 cost) of one perturbed entry from one conversion-capped sweep (frozen perturbation rules)."""
    e, pert = args
    c, sty = R.perturbed(e, **pert)
    if c["SMeOH"] <= 1e-6 or c["SCH4"] < -1e-12 or c["SCO"] < -1e-12:
        return np.nan, np.nan
    c["SCH4"], c["SCO"] = max(c["SCH4"], 0.0), max(c["SCO"], 0.0)
    kw = dict(STY_per_g_cat=sty, P_bar=e["P_bar"], h2_co2=e["h2_co2"], T_C=e["T_C"], x_co="recycled_central")
    try:
        s = G.purge_sweep(c, **kw)
    except ValueError:
        return np.nan, np.nan
    return (G.optimal_purge(c, sweep=s, **kw)["cost_eur_t"],
            G.optimal_purge(c, constrained=True, sweep=s, **kw)["cost_eur_t"])


def exact_cost_s6(args):
    return exact_cost_both(args)[1]


def _compute_s6(jobs):
    if not jobs:
        return np.array([])
    with Pool(R.WORKERS) as pool:
        res = pool.map(exact_cost_both, jobs, chunksize=4)
    for j, (s5, _) in zip(jobs, res):
        _S5_SEEN[R.job_key(j)] = s5
    return np.array([r[1] for r in res])


def load_s6():
    c = pd.read_csv(R.INV / "literature_candidates.csv")
    c = c[np.isfinite(c.cost_recycled_opt_inlet)]
    n = c.groupby("group").size()
    c = c[c.group.isin(n[n >= 2].index)].reset_index(drop=True)
    c["cost_recycled_opt"] = c["cost_recycled_opt_inlet"]      # the column the frozen script scores
    c["sty_printed_basis"] = c.sty_basis.str.startswith("printed STY")
    gm = pd.read_csv(R.INV / "group_metrics_inlet_limit.csv")
    return c, gm


def save_crosscheck():
    if not _S5_SEEN:
        return
    f = OUT / "s5_crosscheck.csv.gz"
    old = pd.read_csv(f, dtype={"key": str}) if f.exists() else pd.DataFrame(columns=["key", "cost_s5"])
    new = pd.DataFrame(sorted(_S5_SEEN.items()), columns=["key", "cost_s5"])
    t = pd.concat([old, new]).drop_duplicates("key", keep="last").sort_values("key")
    t.to_csv(f, index=False, float_format="%.12g", compression={"method": "gzip", "mtime": 0})


if __name__ == "__main__":
    if TREATMENT == "s5":
        # the frozen cache holds every exact run of the frozen analysis; a run missing from it would be recomputed
        # with the frozen exact_cost (S5) and reported by the count below
        if not R.CACHE_FILE.exists():
            shutil.copy(FROZEN / "exact_cache.csv.gz", R.CACHE_FILE)
        n0 = len(R.exact_cache())
        R.main()
        print("S5 exact runs added to the frozen cache:", len(R.exact_cache()) - n0)
    else:
        R.exact_cost = exact_cost_s6
        R._compute = _compute_s6
        R.load = load_s6
        _save = R.save_cache

        def save_both():
            _save()
            save_crosscheck()
        R.save_cache = save_both
        R.main()
