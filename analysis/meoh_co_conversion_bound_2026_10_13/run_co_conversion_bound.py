"""How far does the methanol field result depend on the recycled-CO conversion rule?

The frozen plant leaderboards (analysis/meoh_literature_inversion_2026_10_05) convert recycled CO with
x_co='recycled_central': the LOWER end of the thermodynamic window, the least per-pass CO conversion that keeps the
reactor outlet at or below RWGS and CO-hydrogenation equilibrium. Under the inlet-limited loop (reactor-inlet
CH4 + CO + N2 <= 6.86 %, meoh_general_model.eligible_purges) the disagreement rests largely on CO build-up. This
script reruns the frozen code path (meoh_candidates.plant_costs: meoh_general_model.purge_sweep, conversion capped
at CO2-hydrogenation equilibrium, canonical purge grid) with the two other recycled-CO rules of the model:

  recycled_equal_X  x_CO = X (the CO2 per-pass conversion) clipped into the window   (meoh_general_model.resolve_x_co)
  recycled_high     x_CO = x at CO-hydrogenation equilibrium (upper end of the window)

each without an inlet limit (minimum over every finite purge level, as cost_recycled_opt), with the 6.86 % limit
(eligible_purges, as cost_recycled_opt_inlet) and with absolute limits 5 / 8 / 10 / 15 % (equilibrium feasible and
nonreactive <= limit, as cost_recycled_opt_lim<L>).

Gate: the central rule is recomputed first from the frozen inputs (literature_candidates.csv, printed cohort) and
must reproduce the frozen columns cost_recycled_opt, cost_recycled_opt_inlet and cost_recycled_opt_lim{5,8,10,15}
to 1e-6 relative (NaN where frozen is NaN); the script stops otherwise.

Scoring with the frozen code: meoh_candidates.aggregate(frame, col, up_col='STY'), bootstrap (10,000 paper
resamples, seed 20261006) and mismatch_kinds.classify.

Writes entry_costs.csv, summary.json and results_table.md (this folder). Parallel over entries, COB_WORKERS
processes (default 4).
"""
import json
import os
import sys
import time
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
from meoh_candidates import ROW_KEYS, aggregate, bootstrap  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

WORKERS = int(os.environ.get("COB_WORKERS", "4"))
RULES = {"central": "recycled_central", "equal_X": "recycled_equal_X", "high": "recycled_high"}
SWEEP = (0.05, 0.08, 0.10, 0.15)
LIMITS = {"none": None, "6.86": "inlet", **{f"{L * 100:g}": L for L in SWEEP}}
FROZEN = {"none": "cost_recycled_opt", "6.86": "cost_recycled_opt_inlet",
          **{f"{L * 100:g}": f"cost_recycled_opt_lim{L * 100:g}" for L in SWEEP}}
BANSODE = "10.1039/c2cy20604h"
RTOL = 1e-6


def entry(row):
    """Costs of one candidate under every rule x limit, with purge, inlet CO share, nonreactive share and x_CO at
    each optimum, and the CO-hydrogenation / RWGS approach at the optimum."""
    c = dict(X=row["X"], SMeOH=row["SMeOH"], SCH4=row["SCH4"], SCO=row["SCO"])
    kw = dict(P_bar=row["P_bar"], h2_co2=row["h2_co2"], T_C=row["T_C"])
    out = {}
    for tag, rule in RULES.items():
        s = G.purge_sweep(c, STY_per_g_cat=row["STY"], x_co=rule, **kw)
        cost = np.asarray(s["cost_eur_t"], dtype=float)
        eq = np.asarray(s["equilibrium_feasible"])
        nonreactive = np.asarray(s["nonreactive_fraction"])
        for lname, lim in LIMITS.items():
            if lim is None:
                mask = np.isfinite(cost)
            elif lim == "inlet":
                mask = G.eligible_purges(s)
            else:
                mask = eq & (nonreactive <= lim)
            key = f"{tag}_{lname}"
            if not mask.any():
                out.update({f"cost_{key}": np.nan, f"purge_{key}": np.nan, f"co_in_{key}": np.nan,
                            f"nonreactive_{key}": np.nan, f"xco_{key}": np.nan, f"Xeff_{key}": np.nan})
                continue
            j = int(np.argmin(np.where(mask, cost, np.inf)))
            out.update({f"cost_{key}": float(cost[j]), f"purge_{key}": float(G.PURGES[j]),
                        f"co_in_{key}": float(np.asarray(s["co_inlet_fraction"])[j]),
                        f"nonreactive_{key}": float(nonreactive[j]),
                        f"xco_{key}": float(np.asarray(s["x_co"]).ravel()[j]),
                        f"Xeff_{key}": float(np.asarray(s["X_eff"])[j])})
        out[f"n_inlet_ok_{tag}"] = int(G.eligible_purges(s).sum())
        out[f"n_eq_infeasible_{tag}"] = int((~eq).sum())
    return out


def score(c, col, purge_col, co_col):
    gm, s = aggregate(c, col, up_col="STY")
    gm, k = classify(c, gm, col)
    m = gm[gm.top1_mismatch]
    bt = bootstrap(gm)
    nb_gm, nb = aggregate(c[c.doi != BANSODE], col, up_col="STY")
    nbm = nb_gm[nb_gm.top1_mismatch] if len(nb_gm) else nb_gm
    f = c[np.isfinite(c[col])]
    ing = f[f.group.isin(gm.group)]                       # entries in scored groups with a finite cost
    return gm, dict(
        groups=s["groups"], papers=s["papers"], entries=s["entries"],
        candidates_infeasible=s["candidates_infeasible"], groups_lost_to_infeasibility=s["groups_lost_to_infeasibility"],
        disagreements=s["top1_mismatch_groups"], gt5pct=int((m.regret > 0.05).sum()),
        gt10pct=int((m.regret > 0.10).sum()),
        papers_with_disagreement=s["papers_with_mismatch"], gt5pct_papers=int(m[m.regret > 0.05].doi.nunique()),
        regret_median_disagreements=s["regret_median_mismatched"], pairwise_inversions=s["pairwise_inversions"],
        kinds={t: dict(groups=k[t]["groups"], gt5pct=k[t]["gt5pct"], papers=k[t]["papers"])
               for t in ("cat_sameT", "cat_and_T", "T", "same_record")},
        other_catalyst=k["other_catalyst"], other_temperature=k["other_temperature"],
        kinds_with_gt5pct=[k[t]["kind"] for t in ("cat_sameT", "cat_and_T", "T", "same_record") if k[t]["gt5pct"] > 0],
        without_bansode=dict(groups=nb.get("groups", 0), disagreements=nb.get("top1_mismatch_groups", 0),
                             gt5pct=int((nbm.regret > 0.05).sum()) if len(nbm) else 0),
        median_inlet_co_share_at_optimum=float(ing[co_col].median()),
        median_purge_at_optimum=float(ing[purge_col].median()),
        bootstrap=dict(fraction=bt["fraction"], ci95=bt["ci95"], ci95_of_groups=bt["ci95_of_groups"],
                       resamples=bt["resamples"], seed=bt["seed"]))


def leaders(c, gm, tag, lname):
    """STY leader versus plant-cost leader in the groups where they differ: temperature, CO selectivity, and the
    reactor-inlet CO share, x_CO and purge at the optimum (medians), with counts."""
    rows = []
    for r in gm[gm.top1_mismatch].itertuples():
        e = c[c.group == r.group]
        u, p = e[e.catalyst == r.upstream_winner].iloc[0], e[e.catalyst == r.economic_winner].iloc[0]
        rows.append({f"{w}_{k}": float(x[f"{k}_{tag}_{lname}"] if k in ("co_in", "xco", "purge") else x[k])
                     for w, x in (("sty", u), ("plant", p)) for k in ("T_C", "SCO", "co_in", "xco", "purge")})
    d = pd.DataFrame(rows)
    if d.empty:
        return {}
    return dict(disagreements=len(d), median={k: float(v) for k, v in d.median().items()},
                sty_leader_hotter=int((d.sty_T_C > d.plant_T_C + 0.05).sum()),
                sty_leader_higher_SCO=int((d.sty_SCO > d.plant_SCO).sum()),
                sty_leader_higher_inlet_co=int((d.sty_co_in > d.plant_co_in).sum()),
                sty_leader_higher_purge=int((d.sty_purge > d.plant_purge).sum()))


def table(results):
    """Markdown table rule x limit (results_table.md)."""
    name = {"central": "central (frozen)", "equal_X": "equal_X", "high": "high (CO-hyd. equilibrium)"}
    lab = {"none": "no limit", "6.86": "6.86 %", "5": "5 %", "8": "8 %", "10": "10 %", "15": "15 %"}
    out = ["| x_CO rule | inlet limit | different leader | > 5 % | papers (> 5 %) | other catalyst / 32 (> 5 %) | "
           "other T / 22 (> 5 %) | kinds with > 5 % | w/o Bansode 2013 (> 5 %) | median inlet CO | median purge | "
           "bootstrap 95 % CI | infeasible |", "|" + "---|" * 13]
    for tag, v in results.items():
        for l, r in v.items():
            oc, ot, nb, bt = r["other_catalyst"], r["other_temperature"], r["without_bansode"], r["bootstrap"]
            kinds = ", ".join(f"{k['groups']}/{k['gt5pct']}" for k in r["kinds"].values())
            out.append(f"| {name[tag]} | {lab[l]} | {r['disagreements']}/{r['groups']} | {r['gt5pct']} | "
                       f"{r['papers_with_disagreement']}/{r['papers']} ({r['gt5pct_papers']}) | "
                       f"{oc['groups']} ({oc['gt5pct']}) | {ot['groups']} ({ot['gt5pct']}) | {kinds} | "
                       f"{nb['disagreements']}/{nb['groups']} ({nb['gt5pct']}) | "
                       f"{r['median_inlet_co_share_at_optimum'] * 100:.2f} % | {r['median_purge_at_optimum'] * 100:.2g} % | "
                       f"{bt['ci95'][0] * 100:.0f}-{bt['ci95'][1] * 100:.0f} % | {r['candidates_infeasible']} |")
    out.append("")
    out.append("kinds with > 5 %: groups/>5 % for other catalyst same T, other catalyst and T, other T, same record.")
    return "\n".join(out) + "\n"


def main():
    t0 = time.time()
    c = pd.read_csv(INV / "literature_candidates.csv")
    rows = c[ROW_KEYS].to_dict("records")
    with Pool(WORKERS) as pool:
        res = pool.map(entry, rows, chunksize=4)
    c = pd.concat([c, pd.DataFrame(res, index=c.index)], axis=1)

    # ------------------------------------------------ gate: central reproduces the frozen columns ---------------
    gate = {}
    for lname, fcol in FROZEN.items():
        a, b = c[f"cost_central_{lname}"].to_numpy(float), c[fcol].to_numpy(float)
        nan_ok = bool((np.isnan(a) == np.isnan(b)).all())
        both = np.isfinite(a) & np.isfinite(b)
        rel = float(np.max(np.abs(a[both] - b[both]) / np.abs(b[both]))) if both.any() else 0.0
        gate[fcol] = dict(max_rel_diff=rel, nan_pattern_equal=nan_ok, entries=int(len(a)),
                          passed=bool(nan_ok and rel <= RTOL))
    pf = c.purge_central_none.to_numpy(float), c.purge_recycled_opt.to_numpy(float)
    gate["purge_recycled_opt"] = dict(max_abs_diff=float(np.nanmax(np.abs(pf[0] - pf[1]))),
                                      passed=bool(np.nanmax(np.abs(pf[0] - pf[1])) < 1e-12))
    pi = c["purge_central_6.86"]
    d = np.abs(pi.to_numpy(float) - c.purge_recycled_opt_inlet.to_numpy(float))
    gate["purge_recycled_opt_inlet"] = dict(max_abs_diff=float(np.nanmax(d)), passed=bool(np.nanmax(d) < 1e-12))
    print(json.dumps(gate, indent=1))
    if not all(g["passed"] for g in gate.values()):
        sys.exit("central rule does not reproduce the frozen columns: stopping")

    # ------------------------------------------------ scoring -------------------------------------------------
    results, group_rows = {}, []
    for tag in RULES:
        results[tag] = {}
        for lname in LIMITS:
            key = f"{tag}_{lname}"
            gm, results[tag][lname] = score(c, f"cost_{key}", f"purge_{key}", f"co_in_{key}")
            results[tag][lname]["leaders"] = leaders(c, gm, tag, lname)
            for r in gm.itertuples():
                group_rows.append(dict(rule=tag, limit=lname, group=r.group, doi=r.doi, n=r.n,
                                       disagreement=bool(r.top1_mismatch), regret=r.regret, kind=r.kind,
                                       sty_leader=r.upstream_winner, plant_leader=r.economic_winner))
    # x_CO actually used: how far the high / equal_X rules move above the central rule (entries in scored groups)
    n = c.groupby("group").size()
    ing = c[c.group.isin(n[n >= 2].index)]
    xco = {}
    for lname in ("none", "6.86"):
        xco[lname] = {tag: dict(median=float(ing[f"xco_{tag}_{lname}"].median()),
                                p10=float(ing[f"xco_{tag}_{lname}"].quantile(0.1)),
                                p90=float(ing[f"xco_{tag}_{lname}"].quantile(0.9)))
                      for tag in RULES}
    s6c, s6h = results["central"]["6.86"], results["high"]["6.86"]
    frozen_anchor = dict(central_none_15_of_40=(results["central"]["none"]["disagreements"],
                                                results["central"]["none"]["groups"]) == (15, 40),
                         central_none_gt5_7=results["central"]["none"]["gt5pct"] == 7,
                         central_686_28_of_40=(s6c["disagreements"], s6c["groups"]) == (28, 40),
                         central_686_gt5_22=s6c["gt5pct"] == 22)
    summary = dict(
        gate=gate, frozen_anchors=frozen_anchor, results=results, x_co_used_in_scored_groups=xco,
        entries=int(len(c)), entries_in_scored_groups=int(len(ing)),
        infeasible_entries={tag: {l: int(c[f"cost_{tag}_{l}"].isna().sum()) for l in LIMITS} for tag in RULES},
        infeasible_entries_in_scored_groups={tag: {l: int(ing[f"cost_{tag}_{l}"].isna().sum()) for l in LIMITS}
                                             for tag in RULES},
        inlet_limit=float(G.NONREACTIVE_MAX), runtime_s=round(time.time() - t0, 1), workers=WORKERS)
    if not all(frozen_anchor.values()):
        print("WARNING frozen anchors:", frozen_anchor)
    keep = ["group", "doi", "entry", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCO", "SCH4", "STY",
            "cost_recycled_opt", "cost_recycled_opt_inlet"] + [col for col in res[0]]
    c[keep].to_csv(HERE / "entry_costs.csv", index=False, float_format="%.10g")
    pd.DataFrame(group_rows).to_csv(HERE / "group_results.csv", index=False, float_format="%.6g")
    (HERE / "results_table.md").write_text(table(results), encoding="utf-8")
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({t: {l: (r["disagreements"], r["groups"], r["gt5pct"]) for l, r in v.items()}
                      for t, v in results.items()}))
    print("runtime", summary["runtime_s"])


if __name__ == "__main__":
    main()
