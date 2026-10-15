"""Conversion sensitivity of the frozen methanol field result: each catalyst may be run at its own catalyst inventory
(advisor review 2026-10-08, item 2).

The laboratory point (X0, STY0) fixes the per-pass conversion in the primary. Here the plant may load m times the
laboratory catalyst per unit feed (space velocity / m). Conversion follows a first-order approach to the equilibrium
conversion of the laboratory feed, calibrated on the measured point:

    X(m) = X_eq [1 - (1 - X0 / X_eq)^m],      STY(m) = STY0 X(m) / (X0 m)

with the measured selectivities held. X_eq is the simultaneous CO2-hydrogenation + RWGS equilibrium conversion of the
laboratory feed (H2/CO2 and inert share as extracted) at the laboratory T and P (Peng-Robinson fugacities, solved from
a grid of starting points; the lowest root where several exist; meoh_general_model.equilibrium_co2_conversion starts
from one point and returns a wrong root for 10 of 284 laboratory conditions). Each candidate takes the cheapest of its
laboratory point and the raised-conversion states (m > 1) up to X = f X_eq, over the canonical purge grid; a raised
state is admitted only where the loop's reactor outlet does not pass CO2-hydrogenation equilibrium. The paper
leaderboard stays the laboratory STY. Primary f = 0.95; variants f = 0.90 and 0.99, and a two-sided variant that also
allows m = 0.5 and 0.25 (less catalyst, lower conversion). This is a model sensitivity (a calibrated first-order
approach with fixed selectivity), not a measured optimum.

Plant model and cohorts: the frozen treatment (literature_candidates.csv, printed values, the primary) and all entries
(literature_candidates_all_entries.csv). The laboratory cost of every entry must equal its cost_recycled_opt.
Disagreements are split by kind (mismatch_kinds.classify).

Outputs (this folder): conversion_sensitivity_summary.json, conversion_sensitivity_groups.csv,
conversion_sensitivity_points.csv.

MEOH_FIELD_SET=combined (analysis/meoh_field_pooled_2026_10_15/field_set.py) runs both cohorts on the groups of both
extractions and writes to analysis/meoh_field_pooled_2026_10_15/robustness/conversion_s5/; the first-set groups of the
printed cohort must reproduce the first-set result (laboratory 15 of 40).
"""
import json
import os
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(HERE))
import meoh_general_model as G  # noqa: E402
from meoh_candidates import ROW_KEYS, aggregate  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

sys.path.insert(0, str(REPO / "analysis" / "meoh_field_pooled_2026_10_15"))
import field_set as FS  # noqa: E402  (MEOH_FIELD_SET=first, the default, or combined)

OUT = FS.out_dir("conversion_s5", HERE)
FIRST_SET_ANCHORS = {"printed|lab": (15, 40)}

WORKERS = int(os.environ.get("INV_WORKERS", "4"))
F_PRIMARY, F_VARIANTS = 0.95, (0.90, 0.99)
U_GRID = 30                     # raised states per candidate between X0/X_eq and 0.99
M_DOWN = (0.5, 0.25)
EQ_TOL = 1e-6
KW_RULE = dict(x_co="recycled_central")
COLS = {"lab": "laboratory conversion", f"cost_f{F_PRIMARY:g}": f"conversion up to {F_PRIMARY:g} X_eq",
        "cost_f0.9": "up to 0.90 X_eq", "cost_f0.99": "up to 0.99 X_eq",
        "cost_two_sided": f"up to {F_PRIMARY:g} X_eq, or m = 0.5 / 0.25"}


def equilibrium_roots(feed, T_C, P_bar, scale=1.0):
    """Every converged root of the simultaneous CO2-hydrogenation + RWGS equilibrium of a feed, from a grid of
    starting points (methanol extents g1 x scale of the CO2). Returns the total CO2 conversions."""
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
            if g1 * scale + g2 >= 0.999 or 3 * g1 * scale + g2 >= n0["H2"]:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                xi, _, ier, _ = fsolve(res, [g1 * scale * n0["CO2"], g2 * n0["CO2"]], xtol=1e-12, full_output=True)
            if ier != 1 or not np.all(np.isfinite(xi)):
                continue
            n = comp(xi)
            if np.abs(res(xi)).max() < 1e-8 and min(n.values()) >= -1e-12:
                roots.add(round(float((xi[0] + xi[1]) / n0["CO2"]), 9))
    return sorted(roots)


def x_eq_feed(h2_co2, y_co2, T_C, P_bar):
    """Equilibrium CO2 conversion of the laboratory feed and the number of distinct roots; the lowest root where
    several exist (conservative: it limits how far the conversion may be raised)."""
    inert = max(0.0, 1.0 - y_co2 * (1.0 + h2_co2))
    feed = dict(CO2=1.0, H2=h2_co2, N2=inert / y_co2 if inert > 1e-9 else 0.0)
    roots = equilibrium_roots(feed, T_C, P_bar)
    if not roots and h2_co2 < 3.0:
        # H2-lean feed (second extraction: H2/CO2 = 0.1 in 10.1021/acscatal.6c04842): every methanol extent of the
        # CO2-based grid needs more H2 than the feed holds, so the grid is rescaled to the H2-limited extent
        # (H2/CO2 / 3 of the CO2). No first-extraction feed reaches this branch.
        roots = equilibrium_roots(feed, T_C, P_bar, scale=h2_co2 / 3.0)
    if not roots:
        raise RuntimeError(f"no equilibrium root for H2/CO2 {h2_co2}, y_CO2 {y_co2}, {T_C} C, {P_bar} bar")
    return roots[0], len(roots)


def evaluate(job):
    """job = (key, y_co2). Per-candidate minimum costs for every variant."""
    key, y_co2 = job
    X0, sm, sch4, sco, sty0, P, h2, T = key
    c = dict(X=X0, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, **KW_RULE)
    lab = np.asarray(G.purge_sweep(c, STY_per_g_cat=sty0, **kw)["cost_eur_t"], dtype=float)
    xeq, n_roots = x_eq_feed(h2, y_co2, T, P)
    u0 = X0 / xeq
    out = dict(x_eq=xeq, x_eq_roots=n_roots, u0=u0, lab=float(np.nanmin(lab)))
    states = []                                     # (u, m)
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        for u in us:
            states.append((float(u), float(np.log(1.0 - u) / np.log(1.0 - u0))))
    if u0 < 1.0:                                    # a laboratory point above X_eq keeps only its own state
        for m in M_DOWN:
            states.append((float(1.0 - (1.0 - u0) ** m), float(m)))
    best = []
    if states:
        us, ms = np.array([u for u, _ in states]), np.array([m for _, m in states])
        Xs = us * xeq
        stys = sty0 * Xs / (X0 * ms)
        try:            # every state at once, broadcast over the purge grid
            e = G.cost(dict(c, X=Xs[:, None]), purge=G.PURGES[None, :], STY_per_g_cat=stys[:, None], **kw)
            costs = [np.asarray(e["cost_eur_t"], dtype=float)[i] for i in range(len(us))]
            oks = [np.asarray(e["co2_hyd_approach"], dtype=float)[i] <= 1.0 + EQ_TOL for i in range(len(us))]
        except ValueError:   # some state infeasible (H2 inlet ratio insufficient): evaluate one by one
            costs, oks = [], []
            for X, sty in zip(Xs, stys):
                try:
                    e = G.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **kw)
                    costs.append(np.asarray(e["cost_eur_t"], dtype=float))
                    oks.append(np.asarray(e["co2_hyd_approach"], dtype=float) <= 1.0 + EQ_TOL)
                except ValueError:
                    costs.append(None)
                    oks.append(None)
        for u, m, cost, ok in zip(us, ms, costs, oks):
            if cost is None or not ok.any():
                best.append((float(u), float(m), np.nan))
                continue
            j = int(np.argmin(np.where(ok, cost, np.inf)))
            best.append((float(u), float(m), float(cost[j])))

    def pick(f, two_sided=False):
        cands = [(out["lab"], 1.0, u0)]
        for u, m, cst in best:
            if np.isfinite(cst) and ((m > 1.0 and u <= f + 1e-12) or (two_sided and m < 1.0)):
                cands.append((cst, m, u))
        return min(cands)

    for f in (F_PRIMARY, *F_VARIANTS):
        cst, m, u = pick(f)
        out[f"cost_f{f:g}"], out[f"m_f{f:g}"], out[f"u_f{f:g}"] = cst, m, u
    cst, m, u = pick(F_PRIMARY, two_sided=True)
    out["cost_two_sided"], out["m_two_sided"], out["u_two_sided"] = cst, m, u
    return key, out


def check_first_set(groups, pts, anchors=None):
    """Counts of the first-set groups in the combined run (disagreements, groups, > 5 %, > 5 % papers) for every
    cohort x cost column; stops when an anchor (cohort|column -> (disagreements, groups)) is not reproduced."""
    first = set(FS.first_part(pts).group)
    out = {}
    for (mode, col), g in groups[groups.group.isin(first)].groupby(["mode", "cost_col"]):
        m = g[g.top1_mismatch]
        out[f"{mode}|{col}"] = dict(disagreements=int(len(m)), groups=int(len(g)), gt5pct=int((m.regret > 0.05).sum()),
                                    gt5pct_papers=int(m[m.regret > 0.05].doi.nunique()))
    for k, exp in (FIRST_SET_ANCHORS if anchors is None else anchors).items():
        got = (out[k]["disagreements"], out[k]["groups"])
        if got != exp:
            sys.exit(f"STOP: first-set anchor {k}: {got} != {exp}")
    return out


def main():
    sets = {"printed": FS.candidates(), "all": FS.candidates_all_entries()}
    jobs = {}
    for f in sets.values():
        for r in f.itertuples(index=False):
            key = tuple(float(getattr(r, k)) for k in ROW_KEYS)
            jobs[key] = (key, float(r.y_co2))
    with Pool(WORKERS) as pool:
        table = dict(pool.map(evaluate, list(jobs.values()), chunksize=4))

    summaries, groups, rows = {}, [], []
    for mode, f in sets.items():
        f = f.copy()
        outs = [table[tuple(float(getattr(r, k)) for k in ROW_KEYS)] for r in f.itertuples(index=False)]
        for col in ("lab", "x_eq", "x_eq_roots", "u0",
                    *[f"{p}_f{x:g}" for p in ("cost", "m", "u") for x in (F_PRIMARY, *F_VARIANTS)],
                    "cost_two_sided", "m_two_sided", "u_two_sided"):
            f[col] = [o[col] for o in outs]
        dev = float(np.nanmax(np.abs(f.lab / f.cost_recycled_opt - 1)))
        assert dev < 1e-9, f"laboratory cost differs from cost_recycled_opt ({mode}): {dev}"
        for col, label in COLS.items():
            gm, s = aggregate(f, col, label=label)
            gm, kinds = classify(f, gm, col)
            m = gm[gm.top1_mismatch]
            s.update(gt1pct=int((m.regret > 0.01).sum()), gt5pct=int((m.regret > 0.05).sum()),
                     gt10pct=int((m.regret > 0.10).sum()), gt5pct_papers=int(m[m.regret > 0.05].doi.nunique()),
                     kinds=kinds)
            summaries[f"{mode}|{col}"] = s
            groups.append(gm.assign(mode=mode, cost_col=col))
        f["raised"] = f[f"m_f{F_PRIMARY:g}"] > 1.0
        rows.append(f.assign(mode=mode))
    pts = pd.concat(rows)
    if FS.COMBINED:                     # the first-set groups of the combined run reproduce the first-set result
        meta_first = check_first_set(pd.concat(groups), pts)
    meta = dict(x_eq_multiple_roots=int((pts.drop_duplicates(ROW_KEYS).x_eq_roots > 1).sum()),
                laboratory_above_x_eq=int((pts.drop_duplicates(ROW_KEYS).u0 >= 1.0).sum()),
                operating_points=len(jobs))
    if FS.COMBINED:
        meta["first_set"] = meta_first
    keep = ["batch"] * FS.COMBINED + ["mode", "group", "doi", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCH4", "SCO", "STY", "y_co2",
            "cost_recycled_opt", *[c for c in pts.columns if c in ("lab", "x_eq", "x_eq_roots", "u0", "raised")
                                   or c.startswith(("cost_f", "m_f", "u_f", "cost_two", "m_two", "u_two"))]]
    pts[keep].to_csv(OUT / "conversion_sensitivity_points.csv", index=False, float_format="%.10g")
    pd.concat(groups).to_csv(OUT / "conversion_sensitivity_groups.csv", index=False, float_format="%.6g")
    (OUT / "conversion_sensitivity_summary.json").write_text(
        json.dumps(dict(meta=meta, scenarios=summaries), indent=1, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250)
    tab = pd.DataFrame([dict(scenario=k, groups=v["groups"], mismatch=v["top1_mismatch_groups"], gt5pct=v["gt5pct"],
                             gt10pct=v["gt10pct"], other_catalyst=f"{v['kinds']['other_catalyst']['groups']}"
                             f"/{v['kinds']['other_catalyst']['of']}",
                             other_T=f"{v['kinds']['other_temperature']['groups']}"
                             f"/{v['kinds']['other_temperature']['of']}")
                        for k, v in summaries.items()])
    print(json.dumps(meta))
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
