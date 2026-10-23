"""Methanol catalyst-level count with selectivity that moves with conversion (PREREGISTRATION.md).

The raised-conversion states of verify_2026_10_12_s6_conversion/run_s6_conversion.evaluate (f = 0.95, 6.86 % inlet
limit, recycled CO 'central'), with the selectivities of each state set by one model: constant (frozen), equilibrium
(methanol/CO split moving linearly in u = X/X_eq to the equilibrium split), slope_median, slope_q1, slope_q3.
Catalyst identity, leaders and bootstrap: analysis/meoh_catalyst_level_2026_10_19/run_catalyst_level.py, unchanged.

    set MEOH_FIELD_SET=combined
    set INV_WORKERS=6
    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 run_selectivity_conversion.py
        -> summary.json, raised_<model>.csv, groups_<model>.csv, s_eq.csv
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

os.environ.setdefault("MEOH_FIELD_SET", "combined")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AN = REPO / "analysis"
for p in (AN / "meoh_catalyst_level_2026_10_19", AN / "verify_2026_10_12_s6_conversion"):
    sys.path.insert(0, str(p))
import run_catalyst_level as CL  # noqa: E402
import run_s6_conversion as S6  # noqa: E402

RC, G = S6.RC, S6.G
POOLED = AN / "meoh_field_pooled_2026_10_15"
F = S6.F_PRIMARY
SLOPES = {"slope_median": -0.9259259259, "slope_q1": -2.648795, "slope_q3": -0.064844}
MODELS = ["constant", "equilibrium", *SLOPES]
WORKERS = int(os.environ.get("INV_WORKERS", "6"))


def eq_split(h2_co2, y_co2, T_C, P_bar):
    """(X_eq, s_eq): total CO2 conversion and methanol share of the converted carbon (MeOH + CO) at the simultaneous
    CO2-hydrogenation + RWGS equilibrium of the laboratory feed; the root of RC.x_eq_feed (the lowest)."""
    xeq, _ = RC.x_eq_feed(h2_co2, y_co2, T_C, P_bar)
    inert = max(0.0, 1.0 - y_co2 * (1.0 + h2_co2))
    n0 = {k: 0.0 for k in G.PR_CRIT}
    n0.update(CO2=1.0, H2=h2_co2, N2=inert / y_co2 if inert > 1e-9 else 0.0)
    T_K = T_C + 273.15

    def comp(xi):
        x1, x2 = xi
        n = dict(n0)
        n["CO2"] -= x1 + x2; n["H2"] -= 3 * x1 + x2; n["MeOH"] += x1; n["H2O"] += x1 + x2; n["CO"] += x2
        return n

    def res(xi):
        n = comp(xi)
        tot = sum(n.values())
        y = {k: max(v, 1e-30) / tot for k, v in n.items()}
        f = G.gas_activities(y, T_K, P_bar)
        return [np.log(f["MeOH"] * f["H2O"] / (f["CO2"] * f["H2"] ** 3)) - np.log(G.K_co2_hyd(T_K)),
                np.log(f["CO"] * f["H2O"] / (f["CO2"] * f["H2"])) - np.log(G.K_rwgs(T_K))]
    best = None
    scale = 1.0 if h2_co2 >= 3.0 else min(1.0, h2_co2 / 3.0)
    for sc in (1.0, scale):
        for g1 in (0.05, 0.25, 0.5, 0.8, 0.95):
            for g2 in (0.0, 0.01, 0.05):
                if g1 * sc + g2 >= 0.999 or 3 * g1 * sc + g2 >= n0["H2"]:
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    xi, _, ier, _ = fsolve(res, [g1 * sc, g2], xtol=1e-12, full_output=True)
                if ier != 1 or not np.all(np.isfinite(xi)) or np.abs(res(xi)).max() > 1e-8 or min(comp(xi).values()) < -1e-12:
                    continue
                if abs(xi[0] + xi[1] - xeq) < 1e-6:
                    best = xi
                    break
            if best is not None:
                break
        if best is not None:
            break
    if best is None:
        raise RuntimeError(f"no equilibrium split at {h2_co2}, {y_co2}, {T_C}, {P_bar}")
    return xeq, float(best[0] / (best[0] + best[1]))


def selectivities(model, X, X0, xeq, sm0, sch4, sco0, s_eq):
    if model == "constant":
        return sm0, sco0
    rest = sm0 + sco0
    if model == "equilibrium":
        u0, u = X0 / xeq, X / xeq
        s0 = sm0 / rest if rest > 0 else 0.0
        s = s0 + (s_eq - s0) * min(1.0, max(0.0, (u - u0) / (1.0 - u0)))
        return s * rest, (1.0 - s) * rest
    sm = min(max(sm0 + SLOPES[model] * (X - X0), 0.0), rest)
    return sm, rest - sm


def evaluate(job):
    """run_s6_conversion.evaluate with model-dependent selectivities in the raised states; returns cost_f0.95 per model."""
    key, y_co2, s_eq = job
    X0, sm, sch4, sco, sty0, P, h2, T = key
    c = dict(X=X0, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, **RC.KW_RULE)
    s = G.purge_sweep(c, STY_per_g_cat=sty0, **kw)
    lab_cost = np.asarray(s["cost_eur_t"], dtype=float)
    ok_lab = G.eligible_purges(s)
    lab = float(np.min(lab_cost[ok_lab])) if ok_lab.any() else np.nan
    xeq, _ = RC.x_eq_feed(h2, y_co2, T, P)
    u0 = X0 / xeq
    out = {"lab": lab}
    states = []
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, RC.U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        states = [(float(u), float(np.log(1.0 - u) / np.log(1.0 - u0))) for u in us if u <= F + 1e-12]
    for model in MODELS:
        cands = [lab] if np.isfinite(lab) else []
        for u, m in states:
            if m <= 1.0:
                continue
            X = u * xeq
            smX, scoX = selectivities(model, X, X0, xeq, sm, sch4, sco, s_eq)
            if smX <= 0:
                continue
            sty = sty0 * X * smX / (X0 * sm * m)
            try:
                e = G.cost(dict(X=X, SMeOH=smX, SCH4=sch4, SCO=scoX), purge=G.PURGES, STY_per_g_cat=sty, **kw)
            except ValueError:
                continue
            cost = np.asarray(e["cost_eur_t"], dtype=float)
            ok = ((np.asarray(e["co2_hyd_approach"], dtype=float) <= 1.0 + RC.EQ_TOL)
                  & (np.asarray(e["nonreactive_fraction"], dtype=float) <= G.NONREACTIVE_MAX) & np.isfinite(cost))
            if ok.any():
                cands.append(float(np.min(cost[ok])))
        out[model] = min(cands) if cands else np.nan
    return key, out


def count(frame, cost):
    f = CL.identities(CL.scored(frame, cost))
    gm = CL.compare(CL.catalyst_table(f, "cat_primary", cost))
    return CL.brief(gm), gm


def main():
    conv = pd.read_csv(POOLED / "robustness" / "conversion_s6" / "s6_conversion_points.csv")
    p = conv[conv["mode"] == "printed"].reset_index(drop=True).assign(sty_basis="")
    feeds = {(float(r.h2_co2), float(r.y_co2), float(r.T_C), float(r.P_bar)) for r in p.itertuples()}
    with Pool(WORKERS) as pool:
        splits = dict(zip(feeds, pool.starmap(eq_split, list(feeds))))
    seq = pd.DataFrame([dict(h2_co2=k[0], y_co2=k[1], T_C=k[2], P_bar=k[3], X_eq=v[0], s_eq=v[1]) for k, v in splits.items()])
    seq.to_csv(HERE / "s_eq.csv", index=False, float_format="%.8g")
    gates = dict(s_eq_in_unit_interval=bool(seq.s_eq.between(0, 1).all()),
                 X_eq_matches_frozen=bool(np.allclose([splits[(float(r.h2_co2), float(r.y_co2), float(r.T_C), float(r.P_bar))][0]
                                                       for r in p.itertuples()], p.x_eq, rtol=1e-6)))
    jobs = {}
    for r in p.itertuples():
        key = tuple(float(getattr(r, k)) for k in S6.ROW_KEYS)
        jobs[key] = (key, float(r.y_co2), splits[(float(r.h2_co2), float(r.y_co2), float(r.T_C), float(r.P_bar))][1])
    with Pool(WORKERS) as pool:
        table = dict(pool.map(evaluate, list(jobs.values()), chunksize=4))
    res = dict(gates=gates, models={})
    for model in MODELS:
        col = f"cost_{model}"
        p[col] = [table[tuple(float(getattr(r, k)) for k in S6.ROW_KEYS)][model] for r in p.itertuples()]
        b, gm = count(p, col)
        gm.to_csv(HERE / f"groups_{model}.csv", index=False, float_format="%.6g")
        res["models"][model] = b
        print(f"{model:13s} {b['changed']}/{b['groups_2plus_catalysts']} >5% {b['gt5pct']} CI {b['ci95']}", flush=True)
    dev = np.nanmax(np.abs(p["cost_constant"] / p[f"cost_f{F:g}"] - 1))
    b = res["models"]["constant"]
    res["gates"]["constant_reproduces_frozen"] = dict(max_rel_dev=float(dev), changed=b["changed"], gt5pct=b["gt5pct"],
                                                      ok=dev < 1e-9 and (b["changed"], b["gt5pct"]) == (21, 10))
    keep = ["group", "doi", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCH4", "SCO", "STY", "x_eq",
            f"cost_f{F:g}", *[f"cost_{m}" for m in MODELS]]
    p[keep].to_csv(HERE / "raised_points.csv", index=False, float_format="%.10g")
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(res["gates"], indent=1))


if __name__ == "__main__":
    main()
