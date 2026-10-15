"""Purge-boundary test and physically constrained optimization of the frozen methanol treatment (author decision
2026-10-12: step S5 stays the pre-specified primary; these two checks report how its purge optimum and its ranking
behave).

1. Purge-boundary test. At the S5 optimum every scored entry sits at the lowest level of the canonical purge grid
   (0.5 %). The grid is extended downwards (log-spaced from PURGE_FLOOR to 0.5 %, the canonical 0.1 % steps above)
   and, for every scored entry of the printed cohort, the cost-vs-purge curve, the unconstrained optimum on the
   extended grid, and the cost, reactor-inlet composition and recycle flow there are recorded; the groups are scored
   again on that optimum. Same model and treatment as S5 (recycled CO bounded by RWGS and CO-hydrogenation
   equilibrium, per-pass conversion capped at the loop's CO2-hydrogenation equilibrium).
2. Physically constrained optimization. The cost is minimised over the same extended grid subject to an upper bound on
   the reactor-inlet non-H2/CO2 fraction taken from published CO2-to-methanol loop designs (inlet_inert_literature.csv,
   with page and table of each value): the cost model's own anchor loop (Campos et al. 2022, one-step, 6.78 % in its SI
   Table S10; 6.86 % as reproduced by the model at its 2 % purge, meoh_d01_model.SOURCE_NONREACTIVE_REFERENCE) and the
   envelope of the published designs (lowest and highest value in the file). Every level must also be equilibrium
   feasible. Reported at each optimum: purge, recycle flow and recycle ratio (recycle / fresh make-up, molar),
   reactor-inlet composition, cost, and the groups' ranking (different winners, kinds with denominators, paper-cluster
   bootstrap, winners changed against S5). An entry with no eligible level on the grid (up to 40 % purge) is
   infeasible and leaves both leaderboards of its group.

Input: literature_candidates.csv (the frozen printed cohort; its cost_recycled_opt is the S5 primary and must be
reproduced on the canonical part of the grid). Outputs (this folder): purge_boundary_summary.json,
purge_boundary_entries.csv (one row per scored entry and treatment), purge_boundary_curves.csv (cost and loop state
along the purge grid, every scored entry).

MEOH_FIELD_SET=combined (analysis/meoh_field_pooled_2026_10_15/field_set.py) runs the same tests on the scored entries
of both extractions and writes to analysis/meoh_field_pooled_2026_10_15/robustness/purge_boundary/; the first-set
entries must reproduce the first-set purge-boundary result (optimum below 0.5 % for 309 of 310 entries, 14 of 40
groups with a different leader on the extended grid, 2 above 5 %).
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
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(HERE))
import meoh_general_model as G  # noqa: E402

from meoh_candidates import ROW_KEYS, aggregate, bootstrap  # noqa: E402
from mismatch_kinds import classify, leader_differences  # noqa: E402

M = G.M
WORKERS = int(os.environ.get("INV_WORKERS", "4"))
PURGE_FLOOR = 1e-6
GRID = np.unique(np.concatenate([np.geomspace(PURGE_FLOOR, G.PURGES[0], 121)[:-1], G.PURGES]))
CANON = GRID >= G.PURGES[0] - 1e-12
# purge levels written to the curves file: every level below 0.5 %, then 0.5-1 % in 0.1 % steps, 1-40 % in 1 % steps
CURVE = (~CANON) | np.isin(np.round(GRID, 3), np.round(np.r_[np.arange(0.005, 0.0101, 0.001),
                                                              np.arange(0.02, 0.4001, 0.01)], 3))
LIT = pd.read_csv(HERE / "inlet_inert_literature.csv")
LIMITS = {"published_min": float(LIT.non_h2co2_pct.min()) / 100.0,
          "anchor": float(G.NONREACTIVE_MAX),
          "published_max": float(LIT.non_h2co2_pct.max()) / 100.0}
SWEEP = (0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40)
sys.path.insert(0, str(REPO / "analysis" / "meoh_field_pooled_2026_10_15"))
import field_set as FS  # noqa: E402  (MEOH_FIELD_SET=first, the default, or combined)

OUT = FS.out_dir("purge_boundary", HERE)
FIRST_SET_ANCHOR = dict(entries=310, s5_at_0p5pct=310, below_0p5pct=309, groups=40, disagreements=14, gt5pct=2)
FIELDS = ("cost_eur_t", "nonreactive_fraction", "co_inlet_fraction", "methane_fraction", "n2_inlet_fraction",
          "recycle_kmol_h", "carbon_efficiency", "fresh_h2_co2", "X_eff", "equilibrium_feasible", "x_co")


def sweep(row):
    c = dict(X=row["X"], SMeOH=row["SMeOH"], SCH4=row["SCH4"], SCO=row["SCO"])
    s = G.purge_sweep(c, purges=GRID, STY_per_g_cat=row["STY"], x_co="recycled_central", P_bar=row["P_bar"],
                      h2_co2=row["h2_co2"], T_C=row["T_C"])
    out = {k: np.asarray(s[k], dtype=float) for k in FIELDS}
    fresh = (1.0 + out["fresh_h2_co2"]) / out["carbon_efficiency"] * M.PROD_KMOL_H
    out["recycle_ratio"] = out["recycle_kmol_h"] / fresh
    return out


def state(s, j, h2_co2):
    """Loop state at grid index j (None: no eligible level)."""
    if j is None:
        return dict(cost=np.nan, purge=np.nan, feasible=False)
    nr = s["nonreactive_fraction"][j]
    return dict(cost=s["cost_eur_t"][j], purge=GRID[j], feasible=True, nonreactive=nr,
                H2=h2_co2 * (1.0 - nr) / (1.0 + h2_co2), CO2=(1.0 - nr) / (1.0 + h2_co2),
                CO=s["co_inlet_fraction"][j], CH4=s["methane_fraction"][j], N2=s["n2_inlet_fraction"][j],
                recycle_kmol_h=s["recycle_kmol_h"][j], recycle_ratio=s["recycle_ratio"][j], X_eff=s["X_eff"][j],
                x_co=s["x_co"][j])


def pick(s, mask):
    if not mask.any():
        return None
    return int(np.argmin(np.where(mask, s["cost_eur_t"], np.inf)))


def scored(frame, col, label, purge_col=None):
    gm, out = aggregate(frame, col, label=label)
    m = gm[gm.top1_mismatch]
    out["regret_bins"] = {f"gt{int(t * 100)}pct": dict(groups=int((m.regret > t).sum()),
                                                        papers=int(m[m.regret > t].doi.nunique()))
                          for t in (0.01, 0.05, 0.10)}
    gm, out["kinds"] = classify(frame, gm, col)
    out["bootstrap"] = bootstrap(gm)
    if purge_col:
        out["leader_differences"] = leader_differences(frame, gm, col, purge_col)
    return gm, out


def concentration(e, gm, col, biggest):
    """Disagreements contributed by the paper with the most scored groups, and the result without it."""
    m = gm[gm.top1_mismatch]
    big = m[m.doi == biggest]
    gw, sw = aggregate(e[e.doi != biggest], col)
    mw = gw[gw.top1_mismatch]
    return dict(paper=biggest, its_disagreements=int(len(big)), its_gt5pct=int((big.regret > 0.05).sum()),
                without=dict(groups=sw["groups"], top1_mismatch_groups=sw["top1_mismatch_groups"],
                             gt5pct=int((mw.regret > 0.05).sum()),
                             regret_max=float(gw.regret.max())))


def at_optimum(e, tag):
    """Distribution of the loop state at the optimum over the feasible scored entries."""
    f = e[e[f"{tag}_feasible"]]
    q = lambda col: {k: float(f[f"{tag}_{col}"].quantile(v)) for k, v in  # noqa: E731
                     (("min", 0.0), ("p10", 0.1), ("median", 0.5), ("p90", 0.9), ("max", 1.0))}
    return dict(entries=int(len(f)), infeasible=int((~e[f"{tag}_feasible"]).sum()),
                purge=q("purge"), recycle_kmol_h=q("recycle_kmol_h"), recycle_ratio=q("recycle_ratio"),
                inlet_mol_frac={k: q(k) for k in ("nonreactive", "H2", "CO2", "CO", "CH4", "N2")},
                X_eff_over_X=q("X_eff_rel"), cost_eur_t=q("cost"))


def main():
    cand = FS.candidates()
    n = cand.groupby("group").size()
    cand = cand[cand.group.isin(n[n >= 2].index)].reset_index(drop=True)      # the scored entries of the primary
    keys = sorted({tuple(float(r[k]) for k in ROW_KEYS) for r in cand[ROW_KEYS].to_dict("records")})
    with Pool(WORKERS) as pool:
        res = pool.map(sweep, [dict(zip(ROW_KEYS, k)) for k in keys], chunksize=2)
    table = dict(zip(keys, res))

    tags = {"canonical": None, "extended": None, **{f"limit_{k}": v for k, v in LIMITS.items()}}
    rows, curves, sweep_cost = [], [], {L: [] for L in SWEEP}
    for i, r in cand.iterrows():
        s = table[tuple(float(r[k]) for k in ROW_KEYS)]
        eq = s["equilibrium_feasible"].astype(bool)
        finite = np.isfinite(s["cost_eur_t"])
        row = dict(i=i)
        for tag, lim in tags.items():
            mask = finite & (CANON if tag == "canonical" else True)
            if lim is not None:
                mask = mask & eq & (s["nonreactive_fraction"] <= lim)
            st = state(s, pick(s, mask), r.h2_co2)
            row.update({f"{tag}_{k}": v for k, v in st.items()})
            row[f"{tag}_X_eff_rel"] = st.get("X_eff", np.nan) / r.X
        j5 = int(np.flatnonzero(CANON)[0])
        jc = pick(s, finite & CANON)
        row["cost_at_0p5pct"] = s["cost_eur_t"][j5]
        row["canonical_rise_from_0p5pct"] = bool(np.all(np.diff(s["cost_eur_t"][CANON][jc - j5:]) >= -1e-9))
        row["extended_at_floor"] = bool(row["extended_purge"] <= GRID[0] * (1 + 1e-9))
        for L in SWEEP:
            j = pick(s, finite & eq & (s["nonreactive_fraction"] <= L))
            sweep_cost[L].append(np.nan if j is None else s["cost_eur_t"][j])
        rows.append(row)
        jj = np.flatnonzero(CURVE)
        curves.append(pd.DataFrame(dict(i=i, purge=GRID[jj], cost_eur_t=s["cost_eur_t"][jj],
                                        cost_rel_s5=s["cost_eur_t"][jj] / r.cost_recycled_opt,
                                        nonreactive=s["nonreactive_fraction"][jj], CO=s["co_inlet_fraction"][jj],
                                        CH4=s["methane_fraction"][jj], N2=s["n2_inlet_fraction"][jj],
                                        recycle_kmol_h=s["recycle_kmol_h"][jj], recycle_ratio=s["recycle_ratio"][jj],
                                        X_eff=s["X_eff"][jj], equilibrium_feasible=s["equilibrium_feasible"][jj])))
    e = pd.concat([cand, pd.DataFrame(rows).set_index("i")], axis=1)
    for L in SWEEP:
        e[f"limit_sweep_{L * 100:g}"] = sweep_cost[L]

    # the canonical part of the grid reproduces the frozen primary
    dev = float(np.max(np.abs(e.canonical_cost - e.cost_recycled_opt)))
    assert dev < 1e-6, dev
    # every first-set S5 optimum sits at the 0.5 % floor; on the combined set the count is reported
    # (boundary.canonical_optimum_at_0p5pct) instead of asserted
    assert FS.COMBINED or (e.canonical_purge == G.PURGES[0]).all()

    s5_gm, s5 = scored(e, "canonical_cost", "S5 primary (canonical grid 0.5-40 %)", "canonical_purge")
    biggest = s5_gm.groupby("doi").size().idxmax()          # as run_literature_inversion.py
    out = dict(
        treatment="S5 model (recycled CO bounded by RWGS and CO-hydrogenation equilibrium, per-pass conversion capped "
                  "at the loop's CO2-hydrogenation equilibrium); printed cohort, scored entries",
        grid=dict(levels=int(len(GRID)), floor=PURGE_FLOOR, canonical_floor=float(G.PURGES[0]),
                  top=float(GRID[-1]), below_canonical="log-spaced, %d levels" % int((~CANON).sum())),
        entries=int(len(e)), groups=int(e.group.nunique()), reproduces_primary_max_abs_diff_eur_t=dev,
        anchor_loop=dict(nonreactive=float(M.REF_LOOP["nonreactive_fraction"]),
                         recycle_ratio=float(M.SOURCE_RECYCLE_KMOL_H / ((M.REF_LOOP["fresh_co2"]
                                                                         + M.REF_LOOP["fresh_h2"]) * M.PROD_KMOL_H)),
                         recycle_kmol_h=float(M.SOURCE_RECYCLE_KMOL_H), purge=float(M.SOURCE_PURGE)),
        published_inlet_non_h2co2_pct={r.paper + " | " + r.case: float(r.non_h2co2_pct) for r in LIT.itertuples()},
        limits=LIMITS)

    # ---------------------------------------------------------------- 1. purge boundary ---------------------------
    gap = e.cost_at_0p5pct / e.extended_cost - 1.0
    ext_gm, ext = scored(e, "extended_cost", "unconstrained optimum, extended grid", "extended_purge")
    common = s5_gm.merge(ext_gm, on="group", suffixes=("_s5", "_x"))
    out["boundary"] = dict(
        canonical_optimum_at_0p5pct=int((e.canonical_purge == G.PURGES[0]).sum()),
        cost_rises_monotonically_above_0p5pct=int(e.canonical_rise_from_0p5pct.sum()),
        extended_optimum_below_0p5pct=int((e.extended_purge < G.PURGES[0] - 1e-12).sum()),
        extended_optimum_at_new_floor=int(e.extended_at_floor.sum()),
        cost_at_0p5pct_above_extended_optimum={k: float(gap.quantile(v)) for k, v in
                                              (("min", 0.0), ("p10", 0.1), ("median", 0.5), ("p90", 0.9),
                                               ("max", 1.0))},
        entries_gap_gt1pct=int((gap > 0.01).sum()), entries_gap_gt10pct=int((gap > 0.10).sum()),
        at_extended_optimum=at_optimum(e, "extended"), at_s5_optimum=at_optimum(e, "canonical"),
        scored=ext, s5_scored=dict(groups=s5["groups"], top1_mismatch_groups=s5["top1_mismatch_groups"],
                                   leader_differences=s5["leader_differences"],
                                   regret_bins=s5["regret_bins"], kinds_other_catalyst=s5["kinds"]["other_catalyst"],
                                   kinds_other_temperature=s5["kinds"]["other_temperature"]),
        plant_winner_changed_vs_s5=int((common.economic_winner_s5 != common.economic_winner_x).sum()),
        concentration=concentration(e, ext_gm, "extended_cost", biggest),
        s5_concentration=concentration(e, s5_gm, "canonical_cost", biggest))

    # ---------------------------------------------------------------- 2. constrained -----------------------------
    cons = {}
    for k, lim in LIMITS.items():
        tag = f"limit_{k}"
        gm, sc = scored(e, f"{tag}_cost", f"inlet non-H2/CO2 <= {lim * 100:.2f} %, extended grid", f"{tag}_purge")
        cm = s5_gm.merge(gm, on="group", suffixes=("_s5", "_c"))
        bind = e[e[f"{tag}_feasible"]]
        cons[k] = dict(limit=lim, scored=sc, at_optimum=at_optimum(e, tag),
                       limit_binding=int((bind[f"{tag}_nonreactive"] >= lim * (1 - 1e-3)).sum()),
                       optimum_below_0p5pct=int((bind[f"{tag}_purge"] < G.PURGES[0] - 1e-12).sum()),
                       groups_scored_in_both=int(len(cm)),
                       plant_winner_changed_vs_s5=int((cm.economic_winner_s5 != cm.economic_winner_c).sum()),
                       concentration=concentration(e, gm, f"{tag}_cost", biggest),
                       cost_increase_vs_s5={q: float((bind[f"{tag}_cost"] / bind.canonical_cost - 1).quantile(v))
                                            for q, v in (("median", 0.5), ("p90", 0.9), ("max", 1.0))})
        gm.to_csv(OUT / f"group_metrics_purge_{k}.csv", index=False, float_format="%.6g")
    out["constrained"] = cons
    if FS.COMBINED:                     # the first-set entries reproduce the first-set purge-boundary result
        e1 = FS.first_part(e)
        g1 = ext_gm[ext_gm.group.isin(set(e1.group))]
        m1 = g1[g1.top1_mismatch]
        got = dict(entries=int(len(e1)), s5_at_0p5pct=int((e1.canonical_purge == G.PURGES[0]).sum()),
                   below_0p5pct=int((e1.extended_purge < G.PURGES[0] - 1e-12).sum()),
                   groups=int(len(g1)), disagreements=int(len(m1)), gt5pct=int((m1.regret > 0.05).sum()))
        assert got == FIRST_SET_ANCHOR, ("first-set purge-boundary anchor", got)
        f1 = e1[e1.extended_feasible]
        got.update(purge_median=float(f1.extended_purge.median()),
                   nonreactive_median=float(f1.extended_nonreactive.median()),
                   recycle_ratio_median=float(f1.extended_recycle_ratio.median()))
        out["first_set"] = got
    out["limit_sweep_extended_grid"] = {
        f"{L * 100:g}%": {kk: v for kk, v in scored(e, f"limit_sweep_{L * 100:g}", f"limit {L * 100:g} %")[1].items()
                          if kk in ("groups", "top1_mismatch_groups", "candidates_infeasible",
                                    "groups_lost_to_infeasibility", "top1_mismatch_fraction")}
        for L in SWEEP}

    ext_gm.to_csv(OUT / "group_metrics_purge_extended.csv", index=False, float_format="%.6g")
    cols = ["batch"] * FS.COMBINED + ["group", "doi", "catalyst", "sty_basis", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCO", "SCH4", "STY",
            "cost_recycled_opt", "cost_at_0p5pct"] + [c for c in e.columns if c.split("_")[0] in
                                                     ("canonical", "extended", "limit")]
    e[cols].to_csv(OUT / "purge_boundary_entries.csv", index=False, float_format="%.8g")
    pd.concat(curves).to_csv(OUT / "purge_boundary_curves.csv", index=False, float_format="%.6g")
    (OUT / "purge_boundary_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n",
                                                      encoding="utf-8")
    b = out["boundary"]
    print(json.dumps(out, indent=1, default=float))
    print(f"\nS5 {s5['top1_mismatch_groups']}/{s5['groups']}; extended grid {ext['top1_mismatch_groups']}/"
          f"{ext['groups']} (optimum below 0.5 % for {b['extended_optimum_below_0p5pct']}/{len(e)}); constrained "
          + ", ".join(f"{k} {v['limit'] * 100:.2f} %: {v['scored']['top1_mismatch_groups']}/{v['scored']['groups']}"
                      for k, v in cons.items()))


if __name__ == "__main__":
    main()
