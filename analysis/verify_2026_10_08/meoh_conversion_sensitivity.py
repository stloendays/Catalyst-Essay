"""Conversion sensitivity of the methanol field result: each catalyst may be run at its own catalyst inventory.

The laboratory point (X0, STY0) fixes the per-pass conversion in the main analysis. Here the plant may load m times
the laboratory catalyst per unit feed (space velocity / m). Conversion follows a first-order approach to the
equilibrium conversion of the laboratory feed, calibrated on the measured point:

    X(m) = X_eq [1 - (1 - X0 / X_eq)^m],      STY(m) = STY0 X(m) / (X0 m)

with the measured selectivities held. X_eq is the simultaneous CO2-hydrogenation + RWGS equilibrium conversion of
the laboratory feed (H2/CO2 and inert share as extracted) at the laboratory T and P (Peng-Robinson fugacities,
solved from a grid of starting points; the lowest root where several exist). Each candidate takes the cheapest of its laboratory point and the
raised-conversion states (m > 1) up to X = f X_eq, over the canonical purge grid; a raised state is admitted only where
the loop's reactor outlet does not pass CO2-hydrogenation equilibrium. The paper leaderboard stays the laboratory
STY. Primary f = 0.95; variants f = 0.90 and 0.99, and a two-sided variant that also allows m = 0.5 and 0.25 (less
catalyst, lower conversion).

Two base treatments (the decomposition steps of meoh_decomposition.py), both on the corrected candidate set S3:
  orig    model of main (recycled CO at x_RWGS), laboratory conversion uncapped, no inlet limit (step S3)
  thermo  recycled CO also bounded by CO-hydrogenation equilibrium and conversion capped at the loop's
          CO2-hydrogenation equilibrium, no inlet limit (step S5)
and two data modes: all entries, and printed values only (as defined in meoh_decomposition.py).

Outputs: conversion_sensitivity_summary.json, conversion_sensitivity_groups.csv, conversion_sensitivity_points.csv.
"""
import json
import sys
from io import StringIO
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meoh_decomposition as D  # noqa: E402

G = D.G
F_PRIMARY, F_VARIANTS = 0.95, (0.90, 0.99)
U_GRID = 30                     # raised states per candidate between X0/X_eq and 0.99
M_DOWN = (0.5, 0.25)
EQ_TOL = 1e-6


def equilibrium_roots(feed, T_C, P_bar):
    """Every converged root of the simultaneous CO2-hydrogenation + RWGS equilibrium of a feed, from a grid of
    starting points (meoh_general_model.equilibrium_co2_conversion starts from one point and can return a
    non-converged or a spurious root at high pressure and low temperature). Returns the total CO2 conversions."""
    import warnings
    from scipy.optimize import fsolve
    T_K = T_C + 273.15
    n0 = {k: float(feed.get(k, 0.0)) for k in G.PR_CRIT}

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

    roots = set()
    for g1 in (0.05, 0.25, 0.5, 0.8, 0.95):
        for g2 in (0.0, 0.01, 0.05):
            if g1 + g2 >= 0.999 or 3 * g1 + g2 >= n0["H2"]:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                xi, _, ier, _ = fsolve(res, [g1 * n0["CO2"], g2 * n0["CO2"]], xtol=1e-12, full_output=True)
            if ier != 1 or not np.all(np.isfinite(xi)):
                continue
            n = comp(xi)
            if np.abs(res(xi)).max() < 1e-8 and min(n.values()) >= -1e-12:
                roots.add(round(float((xi[0] + xi[1]) / n0["CO2"]), 9))
    return sorted(roots)


def x_eq_feed(h2_co2, y_co2, T_C, P_bar):
    """Equilibrium CO2 conversion of the laboratory feed; the lowest root where several exist (conservative: it
    limits how far the conversion may be raised)."""
    inert = max(0.0, 1.0 - y_co2 * (1.0 + h2_co2))
    feed = dict(CO2=1.0, H2=h2_co2, N2=inert / y_co2 if inert > 1e-9 else 0.0)
    roots = equilibrium_roots(feed, T_C, P_bar)
    if not roots:
        raise RuntimeError(f"no equilibrium root for H2/CO2 {h2_co2}, y_CO2 {y_co2}, {T_C} C, {P_bar} bar")
    return roots[0]


def _base(model, rule_kw, c, kw):
    s = model.purge_sweep(c, **rule_kw, **kw)
    return np.asarray(s["cost_eur_t"], dtype=float)


def evaluate(job):
    """job = (key, y_co2, base). Returns per-candidate minimum costs for every variant."""
    key, y_co2, base = job
    X0, sm, sch4, sco, sty0, P, h2, T = key
    c = dict(X=X0, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, x_co="recycled_central")
    model = G if base == "orig" else D.GL
    if base == "orig":
        lab = np.asarray(G.purge_sweep(c, STY_per_g_cat=sty0, **kw)["cost_eur_t"], dtype=float)
    else:
        lab = np.asarray(D.GL.purge_sweep(c, STY_per_g_cat=sty0, **kw)["cost_eur_t"], dtype=float)
    xeq = x_eq_feed(h2, y_co2, T, P)
    u0 = X0 / xeq
    out = dict(x_eq=xeq, u0=u0, lab=float(np.nanmin(lab)))
    states = []                                     # (u, m, min admissible cost over purge)
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, U_GRID + 1)[1:], [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        for u in us:
            m = np.log(1.0 - u) / np.log(1.0 - u0)
            states.append((float(u), float(m)))
    if u0 < 1.0:                                    # a laboratory point above X_eq keeps only its own state
        for m in M_DOWN:
            states.append((float(1.0 - (1.0 - u0) ** m), float(m)))
    best = []
    if states:
        us, ms = np.array([u for u, _ in states]), np.array([m for _, m in states])
        Xs = us * xeq
        stys = sty0 * Xs / (X0 * ms)
        try:            # every state at once, broadcast over the purge grid
            e = model.cost(dict(c, X=Xs[:, None]), purge=G.PURGES[None, :], STY_per_g_cat=stys[:, None], **kw)
            costs = [np.asarray(e["cost_eur_t"], dtype=float)[i] for i in range(len(us))]
            oks = [np.asarray(e["co2_hyd_approach"], dtype=float)[i] <= 1.0 + EQ_TOL for i in range(len(us))]
        except ValueError:   # some state infeasible (H2 inlet ratio insufficient): evaluate one by one
            costs, oks = [], []
            for X, sty in zip(Xs, stys):
                try:
                    e = model.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **kw)
                    costs.append(np.asarray(e["cost_eur_t"], dtype=float))
                    oks.append(np.asarray(e["co2_hyd_approach"], dtype=float) <= 1.0 + EQ_TOL)
                except ValueError:
                    costs.append(None)
                    oks.append(None)
        for u, m, cost, ok in zip(us, ms, costs, oks):
            if cost is None or not ok.any():
                best.append((float(u), float(m), np.nan, np.nan))
                continue
            j = int(np.argmin(np.where(ok, cost, np.inf)))
            best.append((float(u), float(m), float(cost[j]), float(G.PURGES[j])))
    out["states"] = best

    def pick(f, two_sided=False):
        cands = [(out["lab"], 1.0, u0)]
        for u, m, cst, _ in best:
            if np.isfinite(cst) and ((m > 1.0 and u <= f + 1e-12) or (two_sided and m < 1.0)):
                cands.append((cst, m, u))
        return min(cands)

    for f in (F_PRIMARY, *F_VARIANTS):
        cst, m, u = pick(f)
        out[f"cost_f{f:g}"], out[f"m_f{f:g}"], out[f"u_f{f:g}"] = cst, m, u
    cst, m, u = pick(F_PRIMARY, two_sided=True)
    out["cost_two_sided"], out["m_two_sided"], out["u_two_sided"] = cst, m, u
    return key, base, out


def summarize(frame, cost_col, label):
    gm = D.top1(frame, cost_col)
    return gm, dict(variant=label, groups=len(gm), papers=int(gm.doi.nunique()), mismatch=int(gm.mismatch.sum()),
                    fraction=float(gm.mismatch.mean()), papers_with_mismatch=int(gm[gm.mismatch].doi.nunique()),
                    gt1pct=int((gm.mismatch & (gm.regret > 0.01)).sum()),
                    gt5pct=int((gm.mismatch & (gm.regret > 0.05)).sum()),
                    gt10pct=int((gm.mismatch & (gm.regret > 0.10)).sum()),
                    regret_max=float(gm.regret.max()),
                    gt5pct_papers=int(gm[gm.mismatch & (gm.regret > 0.05)].doi.nunique()))


def main():
    rec_lock = pd.read_csv(StringIO(D.git_show("agent/extraction/out/records_normalized.csv")),
                           keep_default_na=False, na_values=[""])
    sets = {mode: D.build(rec_lock, D.basis_lock, True, po) for mode, po in (("all", False), ("printed", True))}
    jobs = {}
    for f in sets.values():
        for r in f.itertuples(index=False):
            key = tuple(float(getattr(r, k)) for k in D.KEYS)
            for base in ("orig", "thermo"):
                jobs[(key, base)] = (key, float(r.y_co2), base)
    with Pool(4, initializer=D._init) as pool:
        res = pool.map(evaluate, list(jobs.values()), chunksize=4)
    table = {(k, b): o for k, b, o in res}

    rows, summaries, groups = [], {}, []
    for base in ("orig", "thermo"):
        for mode, f in sets.items():
            f = f.copy()
            outs = [table[(tuple(float(getattr(r, k)) for k in D.KEYS), base)] for r in f.itertuples(index=False)]
            for col in ("lab", "x_eq", "u0", *[f"{p}_f{x:g}" for p in ("cost", "m", "u") for x in (F_PRIMARY, *F_VARIANTS)],
                        "cost_two_sided", "m_two_sided", "u_two_sided"):
                f[col] = [o[col] for o in outs]
            for col, label in (("lab", "laboratory conversion (base)"), (f"cost_f{F_PRIMARY:g}", "conversion up to 0.95 X_eq"),
                               ("cost_f0.9", "up to 0.90 X_eq"), ("cost_f0.99", "up to 0.99 X_eq"),
                               ("cost_two_sided", "up to 0.95 X_eq, or m = 0.5 / 0.25")):
                gm, s = summarize(f, col, label)
                summaries[f"{base}|{mode}|{col}"] = s
                gm["base"], gm["mode"], gm["cost_col"] = base, mode, col
                groups.append(gm)
            f["base"], f["mode"] = base, mode
            rows.append(f)
    pts = pd.concat(rows)
    pts.drop(columns=[c for c in ("sty_print", "sty_mass", "sty_vol", "gv") if c in pts]).to_csv(
        HERE / "conversion_sensitivity_points.csv", index=False, float_format="%.6g")
    pd.concat(groups).to_csv(HERE / "conversion_sensitivity_groups.csv", index=False, float_format="%.6g")
    (HERE / "conversion_sensitivity_summary.json").write_text(json.dumps(summaries, indent=1, default=float) + "\n",
                                                             encoding="utf-8")
    tab = pd.DataFrame([dict(key=k, **{x: v[x] for x in ("groups", "mismatch", "fraction", "papers_with_mismatch",
                                                         "gt5pct", "gt10pct", "gt5pct_papers", "regret_max")})
                        for k, v in summaries.items()])
    pd.set_option("display.width", 250)
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
