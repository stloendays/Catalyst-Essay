"""Catalyst-level comparison with conversion raised towards equilibrium (the primary treatment, f = 0.95), across
inlet limits of CO, methane and N2 other than the primary 6.86%.

The costing is that of analysis/verify_2026_10_12_s6_conversion/run_s6_conversion.py (evaluate), with the inlet limit
passed explicitly instead of G.NONREACTIVE_MAX, on the printed cohort of both extractions. At every limit the laboratory
cost of each entry must equal the pooled cost_recycled_opt_lim<L> column (Extended Data Fig. 10); at 6.86% the
catalyst-level count must reproduce 21 of 63. Counting follows run_catalyst_level.py (RULES.md).

    MEOH_FIELD_SET=combined INV_WORKERS=6 python run_raised_limit_scan.py [LIMITS...]
        -> summary_raised_limit_scan.json, raised_limit_scan_points.csv
"""
import json
import os
import sys
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("MEOH_FIELD_SET", "combined")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis" / "verify_2026_10_12_s6_conversion"))
import run_s6_conversion as S  # noqa: E402

import run_catalyst_level as C  # noqa: E402

G, RC = S.G, S.RC
WORKERS = int(os.environ.get("INV_WORKERS", "6"))
F = S.F_PRIMARY                                    # 0.95 of equilibrium
LAB_COL = {4.0: "cost_recycled_opt_lim4", 5.0: "cost_recycled_opt_lim5", 6.0: "cost_recycled_opt_lim6",
           8.0: "cost_recycled_opt_lim8", 10.0: "cost_recycled_opt_lim10", 12.0: "cost_recycled_opt_lim12",
           15.0: "cost_recycled_opt_lim15", 20.0: "cost_recycled_opt_lim20"}


def evaluate(job, lim):
    """run_s6_conversion.evaluate with the inlet limit `lim` (fraction) in place of G.NONREACTIVE_MAX."""
    key, y_co2 = job
    X0, sm, sch4, sco, sty0, P, h2, T = key
    c = dict(X=X0, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, **RC.KW_RULE)
    s = G.purge_sweep(c, STY_per_g_cat=sty0, **kw)
    lab_cost = np.asarray(s["cost_eur_t"], dtype=float)
    ok_lab = G.eligible_purges(s, nonreactive_max=lim)
    lab = float(np.min(lab_cost[ok_lab])) if ok_lab.any() else np.nan
    xeq, _ = RC.x_eq_feed(h2, y_co2, T, P)
    u0 = X0 / xeq
    best = []
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, RC.U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        for u in us:
            m = float(np.log(1.0 - u) / np.log(1.0 - u0))
            X = u * xeq
            sty = sty0 * X / (X0 * m)
            try:
                e = G.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **kw)
            except ValueError:
                continue
            cost = np.asarray(e["cost_eur_t"], dtype=float)
            ok = ((np.asarray(e["co2_hyd_approach"], dtype=float) <= 1.0 + RC.EQ_TOL)
                  & (np.asarray(e["nonreactive_fraction"], dtype=float) <= lim) & np.isfinite(cost))
            if ok.any() and m > 1.0 and u <= F + 1e-12:
                best.append(float(np.min(cost[ok])))
    cands = ([lab] if np.isfinite(lab) else []) + best
    return key, dict(lab=lab, raised=min(cands) if cands else np.nan)


def main():
    limits = [float(x) for x in sys.argv[1:]] or [6.86, 4.0, 5.0, 8.0, 10.0, 15.0, 20.0]
    cand = S.FS.candidates()
    jobs = {}
    for r in cand.itertuples(index=False):
        key = tuple(float(getattr(r, k)) for k in S.ROW_KEYS)
        jobs[key] = (key, float(r.y_co2))
    out_json = HERE / "summary_raised_limit_scan.json"
    res = json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() else {}
    pts = []
    for L in limits:
        lim = G.NONREACTIVE_MAX if abs(L - 6.86) < 1e-9 else L / 100.0
        with Pool(WORKERS) as pool:
            table = dict(pool.map(partial(evaluate, lim=lim), list(jobs.values()), chunksize=4))
        f = cand.copy()
        outs = [table[tuple(float(getattr(r, k)) for k in S.ROW_KEYS)] for r in f.itertuples(index=False)]
        f["lab_L"] = [o["lab"] for o in outs]
        f["raised_L"] = [o["raised"] for o in outs]
        ref = "cost_recycled_opt_inlet" if abs(L - 6.86) < 1e-9 else LAB_COL[L]
        both = f.lab_L.notna() | f[ref].notna()
        dev = float(np.nanmax(np.abs(f.lab_L[both] / f[ref][both] - 1)))
        assert (f.lab_L.isna() == f[ref].isna()).all() and dev < 1e-9, f"lab cost differs from {ref}: {dev}"
        row = {}
        for name, col in (("laboratory_conversion", "lab_L"), ("conversion_raised", "raised_L")):
            fs = C.identities(C.scored(f, col))
            b = C.brief(C.compare(C.catalyst_table(fs, "cat_primary", col)))
            row[name] = dict(changed=b["changed"], groups=b["groups_2plus_catalysts"], gt5pct=b["gt5pct"],
                             papers_changed=b["papers_changed"], ci95=b["ci95"])
        if abs(L - 6.86) < 1e-9:
            assert row["conversion_raised"]["changed"] == 21 and row["laboratory_conversion"]["changed"] == 26
        res[f"{L:g}"] = row
        pts.append(f[["group", "catalyst", "T_C", "STY", "lab_L", "raised_L"]].assign(limit_pct=L))
        print(f"limit {L:g}%: lab {row['laboratory_conversion']['changed']}/{row['laboratory_conversion']['groups']}"
              f" (>5% {row['laboratory_conversion']['gt5pct']}), raised {row['conversion_raised']['changed']}/"
              f"{row['conversion_raised']['groups']} (>5% {row['conversion_raised']['gt5pct']})", flush=True)
        out_json.write_text(json.dumps(res, indent=1), encoding="utf-8")
    pd.concat(pts).to_csv(HERE / f"raised_limit_scan_points_{'_'.join(f'{x:g}' for x in limits)}.csv",
                          index=False, float_format="%.10g")


if __name__ == "__main__":
    main()
