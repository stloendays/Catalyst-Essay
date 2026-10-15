"""Conversion raised with catalyst inventory, under the reactor-inlet limit of step S6.

The frozen conversion sensitivity (analysis/meoh_literature_inversion_2026_10_05/run_conversion_sensitivity.py) lets
each catalyst run at m times its laboratory inventory, X(m) = X_eq [1 - (1 - X0/X_eq)^m], on the S5 purge grid. Here the
same states are costed under the S6 rule: a purge level counts only if the loop also keeps the reactor-inlet
non-H2/CO2 fraction within the reference loop's limit (G.NONREACTIVE_MAX = 6.86 %), exactly as cost_recycled_opt_inlet
does for the laboratory point (meoh_candidates.plant_costs). Everything else is the frozen code: the equilibrium
conversion of the laboratory feed, the state grid, the equilibrium admission test, the paper leaderboard (laboratory
STY), the aggregation and the split into other catalyst / other temperature.

The laboratory cost of every entry must equal its frozen cost_recycled_opt_inlet. A candidate with no admissible
state is infeasible (NaN), as in the frozen S6 scoring.

Outputs (this folder): s6_conversion_summary.json, s6_conversion_groups.csv, s6_conversion_points.csv.
    INV_WORKERS=4 python run_s6_conversion.py

MEOH_FIELD_SET=combined (analysis/meoh_field_pooled_2026_10_15/field_set.py) runs both cohorts on the groups of both
extractions and writes to analysis/meoh_field_pooled_2026_10_15/robustness/conversion_s6/; the first-set groups of the
printed cohort must reproduce the first-set result (laboratory 28 of 40, raised conversion 23 of 40).
"""
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(INV))
import meoh_general_model as G  # noqa: E402
import run_conversion_sensitivity as RC  # noqa: E402
from meoh_candidates import ROW_KEYS, aggregate  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

WORKERS = int(os.environ.get("INV_WORKERS", "4"))
FS = RC.FS                              # MEOH_FIELD_SET=first, the default, or combined
OUT = FS.out_dir("conversion_s6", HERE)
FIRST_SET_ANCHORS = {"printed|lab": (28, 40), f"printed|cost_f{RC.F_PRIMARY:g}": (23, 40)}
F_PRIMARY, F_VARIANTS = RC.F_PRIMARY, RC.F_VARIANTS


def evaluate(job):
    """Same as RC.evaluate, with every purge level also required to meet the S6 inlet limit."""
    key, y_co2 = job
    X0, sm, sch4, sco, sty0, P, h2, T = key
    c = dict(X=X0, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, **RC.KW_RULE)
    s = G.purge_sweep(c, STY_per_g_cat=sty0, **kw)
    lab_cost = np.asarray(s["cost_eur_t"], dtype=float)
    ok_lab = G.eligible_purges(s)
    lab = float(np.min(lab_cost[ok_lab])) if ok_lab.any() else np.nan
    xeq, n_roots = RC.x_eq_feed(h2, y_co2, T, P)
    u0 = X0 / xeq
    out = dict(x_eq=xeq, x_eq_roots=n_roots, u0=u0, lab=lab)
    states = []
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, RC.U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        for u in us:
            states.append((float(u), float(np.log(1.0 - u) / np.log(1.0 - u0))))
    if u0 < 1.0:
        for m in RC.M_DOWN:
            states.append((float(1.0 - (1.0 - u0) ** m), float(m)))
    best = []
    for u, m in states:
        X = u * xeq
        sty = sty0 * X / (X0 * m)
        try:
            e = G.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **kw)
        except ValueError:
            best.append((u, m, np.nan))
            continue
        cost = np.asarray(e["cost_eur_t"], dtype=float)
        ok = ((np.asarray(e["co2_hyd_approach"], dtype=float) <= 1.0 + RC.EQ_TOL)
              & (np.asarray(e["nonreactive_fraction"], dtype=float) <= G.NONREACTIVE_MAX) & np.isfinite(cost))
        best.append((u, m, float(np.min(cost[ok])) if ok.any() else np.nan))

    def pick(f, two_sided=False):
        cands = [(lab, 1.0, u0)] if np.isfinite(lab) else []
        for u, m, cst in best:
            if np.isfinite(cst) and ((m > 1.0 and u <= f + 1e-12) or (two_sided and m < 1.0)):
                cands.append((cst, m, u))
        return min(cands) if cands else (np.nan, np.nan, np.nan)

    for f in (F_PRIMARY, *F_VARIANTS):
        out[f"cost_f{f:g}"], out[f"m_f{f:g}"], out[f"u_f{f:g}"] = pick(f)
    out["cost_two_sided"], out["m_two_sided"], out["u_two_sided"] = pick(F_PRIMARY, two_sided=True)
    return key, out


def main():
    sets = {"printed": FS.candidates(), "all": FS.candidates_all_entries()}
    jobs = {}
    for f in sets.values():
        for r in f.itertuples(index=False):
            key = tuple(float(getattr(r, k)) for k in ROW_KEYS)
            jobs[key] = (key, float(r.y_co2))
    with Pool(WORKERS) as pool:
        table = dict(pool.map(evaluate, list(jobs.values()), chunksize=4))

    cols = ["lab", "x_eq", "x_eq_roots", "u0",
            *[f"{p}_f{x:g}" for p in ("cost", "m", "u") for x in (F_PRIMARY, *F_VARIANTS)],
            "cost_two_sided", "m_two_sided", "u_two_sided"]
    summaries, groups, rows = {}, [], []
    for mode, f in sets.items():
        f = f.copy()
        outs = [table[tuple(float(getattr(r, k)) for k in ROW_KEYS)] for r in f.itertuples(index=False)]
        for col in cols:
            f[col] = [o[col] for o in outs]
        both = f.lab.notna() | f.cost_recycled_opt_inlet.notna()
        dev = float(np.nanmax(np.abs(f.lab[both] / f.cost_recycled_opt_inlet[both] - 1)))
        assert (f.lab.isna() == f.cost_recycled_opt_inlet.isna()).all() and dev < 1e-9, \
            f"laboratory cost differs from cost_recycled_opt_inlet ({mode}): {dev}"
        for col, label in RC.COLS.items():
            gm, s = aggregate(f, col, label=f"S6, {label}")
            gm, kinds = classify(f, gm, col)
            m = gm[gm.top1_mismatch]
            s.update(gt1pct=int((m.regret > 0.01).sum()), gt5pct=int((m.regret > 0.05).sum()),
                     gt10pct=int((m.regret > 0.10).sum()), gt5pct_papers=int(m[m.regret > 0.05].doi.nunique()),
                     kinds=kinds)
            k5 = m[m.regret > 0.05]
            s["gt5pct_by_kind"] = {k: dict(groups=int(len(d)), papers=int(d.doi.nunique()))
                                   for k, d in k5.groupby("kind")} if "kind" in k5 else {}
            summaries[f"{mode}|{col}"] = s
            groups.append(gm.assign(mode=mode, cost_col=col))
        f["raised"] = f[f"m_f{F_PRIMARY:g}"] > 1.0
        rows.append(f.assign(mode=mode))
    pts = pd.concat(rows)
    first_set = RC.check_first_set(pd.concat(groups), pts, FIRST_SET_ANCHORS) if FS.COMBINED else None
    keep = ["batch"] * FS.COMBINED + ["mode", "group", "doi", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCH4", "SCO", "STY", "y_co2",
            "cost_recycled_opt_inlet", *cols, "raised"]
    pts[keep].to_csv(OUT / "s6_conversion_points.csv", index=False, float_format="%.10g")
    pd.concat(groups).to_csv(OUT / "s6_conversion_groups.csv", index=False, float_format="%.6g")
    extra = dict(first_set=first_set) if FS.COMBINED else {}
    (OUT / "s6_conversion_summary.json").write_text(
        json.dumps(dict(nonreactive_max=G.NONREACTIVE_MAX, operating_points=len(jobs), scenarios=summaries, **extra),
                   indent=1, default=float) + "\n", encoding="utf-8")
    for k, s in summaries.items():
        print(k, f"{s['top1_mismatch_groups']}/{s['groups']}", ">5%", s["gt5pct"], "papers", s["gt5pct_papers"],
              "other catalyst", s["kinds"]["other_catalyst"], "by kind >5%", s["gt5pct_by_kind"])


if __name__ == "__main__":
    main()
