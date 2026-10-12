"""Shared definitions for the methanol constraint-boundary analyses (Task A, run_boundary.py; Task B, run_rules.py).

Everything is scored on the frozen candidates of analysis/meoh_literature_inversion_2026_10_05 with that folder's own
scoring code (meoh_candidates.aggregate, mismatch_kinds.classify); nothing is re-extracted. The model sweep in
run_boundary.py only adds the purge levels open under each limit and asserts that it reproduces the frozen costs.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
for _p in (REPO / "data" / "meoh", INV):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import meoh_general_model as G  # noqa: E402
from meoh_candidates import aggregate, catalyst_key  # noqa: E402,F401
from mismatch_kinds import KINDS, TAGS, classify  # noqa: E402,F401

CANDIDATES = INV / "literature_candidates.csv"
BANSODE = "10.1039/c2cy20604h"              # Bansode 2013, the paper behind 6 of the 7 S5 regrets above 5 %
S6_LIMIT = float(G.NONREACTIVE_MAX)          # 6.86 %, the cost model's anchor loop
PUBLISHED_RANGE = (0.0492, 0.1025)           # inlet_inert_literature.csv: Nieminen 2019 to Campos 2022 three-step
LIMITS = (4, 5, 6, 8, 10, 12, 15, 20, 25, 30)
BOOT_N, BOOT_SEED = 10_000, 20261006         # the frozen bootstrap's resample count and seed (meoh_candidates.bootstrap)
PERM_N, PERM_SEED = 10_000, 20261012


def _scen(name, col, limit, label, curve=True):
    return dict(name=name, col=col, limit=limit, label=label, curve=curve)


# ordered by the limit on the reactor-inlet non-H2/CO2 fraction; S5 is the unconstrained end of the curve
SCENARIOS = ([_scen(f"lim{L}", f"cost_recycled_opt_lim{L}", L / 100.0, f"inlet limit {L} %") for L in LIMITS[:3]]
             + [_scen("S6", "cost_recycled_opt_inlet", S6_LIMIT, "S6: inlet limit 6.86 % (anchor loop)")]
             + [_scen(f"lim{L}", f"cost_recycled_opt_lim{L}", L / 100.0, f"inlet limit {L} %") for L in LIMITS[3:]]
             + [_scen("S5", "cost_recycled_opt", None, "S5: no inlet limit (frozen primary)"),
                _scen("S4_uncapped", "cost_recycled_opt_uncapped", None,
                      "S4: no inlet limit, laboratory conversion not capped at equilibrium", curve=False)])
BY_NAME = {s["name"]: s for s in SCENARIOS}


def load_candidates():
    return pd.read_csv(CANDIDATES)


def leaders(cand, col):
    """Per scored group: the STY leader (the cheapest of tied STY leaders, as group_metrics scores a tie), the
    plant-cost leader and the regret, checked against meoh_candidates.aggregate. Returns (table, gm, kinds_summary)
    where gm carries mismatch_kinds.classify's per-group kind."""
    gm, _ = aggregate(cand, col)
    gm, kinds = classify(cand, gm, col)
    f = cand[np.isfinite(cand[col].astype(float))]
    rows = []
    for key, g in f.groupby("group"):
        if len(g) < 2:
            continue
        top = g.STY.max()
        tied = g[g.STY >= top - 1e-12]
        lab = tied[col].idxmin()
        plant = g[col].idxmin()
        rows.append(dict(group=key, doi=g.doi.iloc[0], n=len(g), lab_idx=int(lab), plant_idx=int(plant),
                         n_sty_tied=len(tied), mismatch=plant not in tied.index,
                         c_lab=float(g.at[lab, col]), c_plant=float(g.at[plant, col])))
    t = pd.DataFrame(rows)
    t["regret"] = (t.c_lab - t.c_plant) / t.c_plant
    t = t.merge(gm[["group", "top1_mismatch", "regret", "kind", "n_catalysts", "temperature_series"]]
                .rename(columns={"regret": "regret_gm"}), on="group", how="left", validate="one_to_one")
    if len(t) != len(gm) or not (t.mismatch == t.top1_mismatch).all() or not np.allclose(t.regret, t.regret_gm,
                                                                                        rtol=0, atol=1e-12):
        raise AssertionError(f"{col}: leader identification differs from meoh_candidates.aggregate")
    return t.drop(columns=["top1_mismatch", "regret_gm"]), gm, kinds
