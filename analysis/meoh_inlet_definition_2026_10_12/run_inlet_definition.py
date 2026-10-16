"""Which species the reactor-inlet limit counts, and does it change the methanol field result (supervisor Q1).

The frozen inlet limit (meoh_general_model.loop_balance, `nonreactive_fraction`) caps (CH4 + CO + N2) / reactor inlet.
CO is not inert in the reaction: recycled CO is converted per pass (x_co='recycled_central', bounded by RWGS and
CO-hydrogenation equilibrium). This script recomputes every printed-cohort candidate's minimum cost under the limit for
two definitions of the limited quantity:

  frozen      CH4 + CO + N2   must reproduce the frozen columns cost_recycled_opt (S5), cost_recycled_opt_inlet (6.86 %)
                              and cost_recycled_opt_lim{4..30} of literature_candidates.csv to 1e-6 relative (stops if not)
  true_inert  CH4 + N2        CO excluded because it is a reactant

on the frozen code path (meoh_general_model.purge_sweep with recycled CO, conversion capped at the loop's
CO2-hydrogenation equilibrium, minimum over the equilibrium-feasible purge levels of the canonical 0.5-40 % grid whose
limited inlet fraction is within the limit, as meoh_candidates.plant_costs does). Limits 4, 5, 6, 6.86, 8, 10, 12, 15,
20, 25, 30 % and none (S5, identical for both definitions).

Each definition x limit is scored with meoh_candidates.aggregate(frame, col, up_col='STY') and mismatch_kinds.classify:
groups with a different leader, regret > 5 %, papers, the result without Bansode 2013, the kinds with their > 5 %
counts, median regret, the near-infeasibility split of draft PR #69 (a disagreement is near-infeasible when the regret
is > 1 or the STY leader's cost is > 2x its S5 cost), the CO and CH4+N2 shares of the inlet at each candidate's optimum
(medians over the entries of scored groups) and a paper-cluster bootstrap (the 28 S5 papers resampled, 10,000 draws,
seed 20261012, the same resamples for every scenario) of the fraction with a different leader and with regret > 5 %.

INLET_WORKERS processes (default 4). Outputs (this folder): entry_costs.csv, definition_scan.csv, stability_5_15.csv,
scan_groups.csv, summary.json.

MEOH_FIELD_SET=combined (analysis/meoh_field_pooled_2026_10_15/field_set.py) runs the same analysis on the 81 groups of
both extractions (the bootstrap then resamples the papers of both) and writes to
analysis/meoh_field_pooled_2026_10_15/robustness/inlet_definition/; the first-set groups must reproduce the frozen
anchors, the 5-10 % band (24-28 of 40) and the CO-excluded 6.86 % result (18 of 40).
"""
import json
import os
import time
from multiprocessing import Pool

import sys

import numpy as np
import pandas as pd

from common import (ANCHORS, BANSODE, BOOT_N, BOOT_SEED, CANDIDATES, DEFINITIONS, FROZEN_COLUMNS, HERE, LIMITS_PCT,
                    NEAR_COST_RATIO, NEAR_REGRET, STABILITY_PCT, G, aggregate, classify, limit_value)

sys.path.insert(0, str(HERE.parents[0] / "meoh_field_pooled_2026_10_15"))
import field_set as FS  # noqa: E402  (MEOH_FIELD_SET=first, the default, or combined)

OUT = FS.out_dir("inlet_definition", HERE)
WORKERS = int(os.environ.get("INLET_WORKERS", "4"))
FIRST_SET_ANCHORS = {("frozen", L): v for L, v in ANCHORS.items()}
FIRST_SET_ANCHORS[("true_inert", "6.86")] = (18, 40)
FIRST_SET_BAND = ((5, 6, "6.86", 8, 10), (24, 28))           # every limit of the 5-10 % band, frozen definition
ROW_KEYS = ["X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"]
LABELS = ["none"] + [str(L) for L in LIMITS_PCT]
REL_TOL = 1e-6


# ------------------------------------------------------------------------------------------------ model sweep ------
def sweep(key):
    """The frozen S5 sweep of one operating point: cost, equilibrium feasibility and inlet shares on the purge grid."""
    r = dict(zip(ROW_KEYS, key))
    s = G.purge_sweep(dict(X=r["X"], SMeOH=r["SMeOH"], SCH4=r["SCH4"], SCO=r["SCO"]), STY_per_g_cat=r["STY"],
                      x_co="recycled_central", P_bar=r["P_bar"], h2_co2=r["h2_co2"], T_C=r["T_C"])
    return dict(cost=np.asarray(s["cost_eur_t"], float), eq=np.asarray(s["equilibrium_feasible"], bool),
                nonreactive=np.asarray(s["nonreactive_fraction"], float),
                co=np.asarray(s["co_inlet_fraction"], float),
                true_inert=np.asarray(s["methane_fraction"], float) + np.asarray(s["n2_inlet_fraction"], float))


def pick(sw, definition, L):
    """Minimum cost under one definition x limit, as meoh_candidates._pick: NaN when no purge level is eligible."""
    lim = limit_value(L)
    if lim is None:
        mask = np.isfinite(sw["cost"])                      # S5: every level of the capped sweep
    else:
        frac = sw["nonreactive"] if definition == "frozen" else sw["true_inert"]
        mask = sw["eq"] & (frac <= lim)
    if not mask.any():
        return dict(cost=np.nan, purge=np.nan, co=np.nan, true_inert=np.nan, nonreactive=np.nan)
    j = int(np.argmin(np.where(mask, sw["cost"], np.inf)))
    return dict(cost=float(sw["cost"][j]), purge=float(G.PURGES[j]), co=float(sw["co"][j]),
                true_inert=float(sw["true_inert"][j]), nonreactive=float(sw["nonreactive"][j]))


def col(definition, L):
    return f"cost_{definition}_{L}"


def entry_table(cand):
    keys = [tuple(float(r[k]) for k in ROW_KEYS) for r in cand[ROW_KEYS].to_dict("records")]
    uniq = sorted(set(keys))
    with Pool(WORKERS) as pool:
        sweeps = dict(zip(uniq, pool.map(sweep, uniq, chunksize=4)))
    rows = []
    for k in keys:
        sw, row = sweeps[k], {}
        for d in DEFINITIONS:
            for L in LABELS:
                p = pick(sw, d, L)
                row[col(d, L)] = p["cost"]
                for q in ("purge", "co", "true_inert", "nonreactive"):
                    row[f"{q}_{d}_{L}"] = p[q]
        rows.append(row)
    return pd.concat([cand, pd.DataFrame(rows, index=cand.index)], axis=1), len(uniq)


def reproduce(t):
    """The frozen definition must reproduce every frozen cost column (NaN pattern identical, 1e-6 relative)."""
    worst = {}
    for L, fc in FROZEN_COLUMNS.items():
        a, b = t[col("frozen", L)].to_numpy(float), t[fc].to_numpy(float)
        if not np.array_equal(np.isnan(a), np.isnan(b)):
            raise SystemExit(f"STOP: frozen definition does not reproduce the NaN pattern of {fc}")
        ok = np.isfinite(a)
        rel = float(np.max(np.abs(a[ok] / b[ok] - 1.0))) if ok.any() else 0.0
        if rel > REL_TOL:
            raise SystemExit(f"STOP: frozen definition does not reproduce {fc} (max relative difference {rel:.3g})")
        worst[fc] = rel
    # S5 is the same for both definitions
    if not np.array_equal(t[col("frozen", "none")].to_numpy(), t[col("true_inert", "none")].to_numpy()):
        raise AssertionError("S5 differs between definitions")
    return dict(max_relative_difference=max(worst.values()), per_column=worst, tolerance=REL_TOL,
                nan_pattern_identical=True)


# ------------------------------------------------------------------------------------------------ scoring ----------
def leaders(cand, c):
    """Per scored group: STY leader (cheapest of tied STY leaders, as group_metrics scores a tie), plant-cost leader and
    regret, checked against meoh_candidates.aggregate; with mismatch_kinds.classify's kind."""
    gm, _ = aggregate(cand, c, up_col="STY")
    gm, kinds = classify(cand, gm, c)
    f = cand[np.isfinite(cand[c].astype(float))]
    rows = []
    for key, g in f.groupby("group"):
        if len(g) < 2:
            continue
        tied = g[g.STY >= g.STY.max() - 1e-12]
        lab, plant = tied[c].idxmin(), g[c].idxmin()
        rows.append(dict(group=key, doi=g.doi.iloc[0], n=len(g), lab_idx=int(lab), plant_idx=int(plant),
                         mismatch=plant not in tied.index, c_lab=float(g.at[lab, c]), c_plant=float(g.at[plant, c])))
    t = pd.DataFrame(rows)
    t["regret"] = (t.c_lab - t.c_plant) / t.c_plant
    t = t.merge(gm[["group", "top1_mismatch", "regret", "kind"]].rename(columns={"regret": "regret_gm"}),
                on="group", how="left", validate="one_to_one")
    if len(t) != len(gm) or not (t.mismatch == t.top1_mismatch).all() or not np.allclose(t.regret, t.regret_gm,
                                                                                        rtol=0, atol=1e-12):
        raise AssertionError(f"{c}: leader identification differs from meoh_candidates.aggregate")
    t["lab_leader"] = cand.loc[t.lab_idx, "catalyst"].to_numpy()
    t["plant_leader"] = cand.loc[t.plant_idx, "catalyst"].to_numpy()
    t["c_lab_S5"] = cand.loc[t.lab_idx, "cost_recycled_opt"].to_numpy()
    t["lab_cost_vs_S5"] = t.c_lab / t.c_lab_S5
    near = (t.regret > NEAR_REGRET) | (t.lab_cost_vs_S5 > NEAR_COST_RATIO)
    t["class"] = np.where(t.mismatch, np.where(near, "near-infeasible", "ordinary"), "")
    t["bansode"] = t.doi == BANSODE
    return t.drop(columns=["top1_mismatch", "regret_gm"]), kinds


def counts(t):
    m = t[t.mismatch]
    return dict(groups=len(t), different_leader=len(m), gt5pct=int((m.regret > 0.05).sum()),
                gt10pct=int((m.regret > 0.10).sum()), papers=int(t.doi.nunique()),
                papers_with_disagreement=int(m.doi.nunique()), papers_gt5pct=int(m[m.regret > 0.05].doi.nunique()))


def shares(t, cand, d, L):
    """Inlet composition at each candidate's optimum, over the entries of the scored groups."""
    e = cand[cand.group.isin(t.group) & np.isfinite(cand[col(d, L)])]
    s5 = e[col(d, "none")]
    return dict(entries=len(e), co_share_median=float(e[f"co_{d}_{L}"].median()),
                true_inert_share_median=float(e[f"true_inert_{d}_{L}"].median()),
                nonreactive_share_median=float(e[f"nonreactive_{d}_{L}"].median()),
                co_fraction_of_nonreactive_median=float((e[f"co_{d}_{L}"] / e[f"nonreactive_{d}_{L}"]).median()),
                purge_median=float(e[f"purge_{d}_{L}"].median()),
                limit_binds=int((e[col(d, L)] > s5 * (1 + 1e-12)).sum()),
                candidates_infeasible=int((~np.isfinite(cand.loc[cand.group.isin(t.group), col(d, L)])).sum()))


def bootstrap_all(tables, papers):
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(papers), size=(BOOT_N, len(papers)))
    w = np.zeros((BOOT_N, len(papers)))
    np.add.at(w, (np.repeat(np.arange(BOOT_N), len(papers)), idx.ravel()), 1.0)
    out = {}
    for name, t in tables.items():
        g = t.assign(gt5=t.mismatch & (t.regret > 0.05)).groupby("doi")
        n = g.size().reindex(papers).fillna(0).to_numpy(float)
        mis = g.mismatch.sum().reindex(papers).fillna(0).to_numpy(float)
        gt5 = g.gt5.sum().reindex(papers).fillna(0).to_numpy(float)
        out[name] = {}
        for k, v in (("different_leader", mis), ("gt5pct", gt5)):
            f = (w @ v) / (w @ n)
            lo, hi = np.percentile(f, [2.5, 97.5])
            out[name][k] = dict(fraction=float(v.sum() / n.sum()), ci95=[float(lo), float(hi)])
    return out


def main():
    t0 = time.time()
    cand = FS.candidates() if FS.COMBINED else pd.read_csv(CANDIDATES)
    cand, n_unique = entry_table(cand)
    repro = reproduce(cand)

    tables, kinds, rows, scen = {}, {}, [], {}
    for d in DEFINITIONS:
        for L in LABELS:
            name = f"{d}|{L}"
            t, k = leaders(cand, col(d, L))
            t.insert(0, "definition", d)
            t.insert(1, "limit", L)
            tables[name], kinds[name] = t, k
    papers = sorted(tables["frozen|none"].doi.unique())
    boot = bootstrap_all(tables, papers)

    for name, t in tables.items():
        d, L = name.split("|")
        c, nb, k = counts(t), counts(t[~t.bansode]), kinds[name]
        m = t[t.mismatch]
        sh = shares(t, cand, d, L)
        ordi, near = m[m["class"] == "ordinary"], m[m["class"] == "near-infeasible"]
        row = dict(definition=d, limit_pct=L, groups=c["groups"], different_leader=c["different_leader"],
                   fraction=c["different_leader"] / c["groups"],
                   fraction_ci_lo=boot[name]["different_leader"]["ci95"][0],
                   fraction_ci_hi=boot[name]["different_leader"]["ci95"][1],
                   gt5pct=c["gt5pct"], gt5pct_ci_lo=boot[name]["gt5pct"]["ci95"][0],
                   gt5pct_ci_hi=boot[name]["gt5pct"]["ci95"][1], gt10pct=c["gt10pct"],
                   papers=c["papers"], papers_with_disagreement=c["papers_with_disagreement"],
                   papers_gt5pct=c["papers_gt5pct"],
                   nobansode_groups=nb["groups"], nobansode_different_leader=nb["different_leader"],
                   nobansode_gt5pct=nb["gt5pct"],
                   other_catalyst_sameT=k["cat_sameT"]["groups"], other_catalyst_sameT_gt5=k["cat_sameT"]["gt5pct"],
                   other_temperature=k["T"]["groups"], other_temperature_gt5=k["T"]["gt5pct"],
                   other_catalyst_and_T=k["cat_and_T"]["groups"], other_catalyst_and_T_gt5=k["cat_and_T"]["gt5pct"],
                   same_record=k["same_record"]["groups"],
                   multi_catalyst_groups=k["multi_catalyst_groups"],
                   temperature_series_groups=k["temperature_series_groups"],
                   regret_median_all=float(t.regret.median()),
                   regret_median_disagreements=float(m.regret.median()) if len(m) else 0.0,
                   regret_max=float(t.regret.max()),
                   ordinary=len(ordi), ordinary_gt5pct=int((ordi.regret > 0.05).sum()),
                   near_infeasible=len(near), near_infeasible_gt5pct=int((near.regret > 0.05).sum()),
                   near_by_regret_gt1=int((m.regret > NEAR_REGRET).sum()),
                   near_by_lab_cost_gt2x_S5=int((m.lab_cost_vs_S5 > NEAR_COST_RATIO).sum()),
                   candidates_infeasible=sh["candidates_infeasible"], limit_binds=sh["limit_binds"],
                   entries_scored=sh["entries"],
                   co_share_median=sh["co_share_median"], true_inert_share_median=sh["true_inert_share_median"],
                   nonreactive_share_median=sh["nonreactive_share_median"],
                   co_fraction_of_nonreactive_median=sh["co_fraction_of_nonreactive_median"],
                   purge_median=sh["purge_median"])
        rows.append(row)
        scen[name] = dict(row, kinds=k, bootstrap=boot[name])
    scan = pd.DataFrame(rows)

    # reproduction anchors (frozen definition)
    anchors = {}
    for L, (dl, g) in ANCHORS.items():
        r = scan[(scan.definition == "frozen") & (scan.limit_pct == L)].iloc[0]
        anchors[L] = dict(expected=f"{dl}/{g}", got=f"{r.different_leader}/{r.groups}",
                          ok=bool(r.different_leader == dl and r.groups == g))
    if not FS.COMBINED and not all(a["ok"] for a in anchors.values()):
        raise SystemExit(f"STOP: reproduction anchors fail: {anchors}")
    if FS.COMBINED:                     # the first-set groups of the combined tables reproduce the first-set result
        first = set(FS.first_part(cand).group)
        got = {}
        for (d, L), exp in FIRST_SET_ANCHORS.items():
            t = tables[f"{d}|{L}"]
            t = t[t.group.isin(first)]
            got[f"{d}|{L}"] = (int(t.mismatch.sum()), len(t))
            if got[f"{d}|{L}"] != exp:
                raise SystemExit(f"STOP: first-set anchor {d}|{L}: {got[f'{d}|{L}']} != {exp}")
        lo, hi = FIRST_SET_BAND[1]
        for L in FIRST_SET_BAND[0]:
            t = tables[f"frozen|{L}"]
            n = int(t[t.group.isin(first)].mismatch.sum())
            got[f"frozen|{L}"] = (n, int(t.group.isin(first).sum()))
            if not lo <= n <= hi:
                raise SystemExit(f"STOP: first-set 5-10 % band, limit {L}: {n} outside {lo}-{hi}")
        anchors = dict(first_set={k: f"{a}/{b}" for k, (a, b) in got.items()},
                       combined={L: a["got"] for L, a in anchors.items()})

    stab = scan[scan.limit_pct.isin([str(L) for L in STABILITY_PCT])]
    stab = stab[["definition", "limit_pct", "groups", "different_leader", "fraction_ci_lo", "fraction_ci_hi", "gt5pct",
                 "gt5pct_ci_lo", "gt5pct_ci_hi", "papers_with_disagreement", "nobansode_different_leader",
                 "nobansode_gt5pct", "other_catalyst_sameT", "other_temperature", "other_catalyst_and_T",
                 "ordinary", "near_infeasible", "regret_median_disagreements"]]

    keep = ["group", "doi", "entry", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCO", "SCH4", "STY",
            *[f"{q}_{d}_{L}" for d in DEFINITIONS for L in LABELS
              for q in ("cost", "purge", "co", "true_inert", "nonreactive")]]
    if FS.COMBINED:
        keep.insert(0, "batch")
    cand[keep].to_csv(OUT / "entry_costs.csv", index=False, float_format="%.10g")
    scan.to_csv(OUT / "definition_scan.csv", index=False, float_format="%.6g")
    stab.to_csv(OUT / "stability_5_15.csv", index=False, float_format="%.6g")
    pd.concat(tables.values()).drop(columns=["lab_idx", "plant_idx"]).to_csv(OUT / "scan_groups.csv", index=False,
                                                                           float_format="%.6g")
    summary = dict(
        definitions=DEFINITIONS, limits_pct=LABELS, s6_limit_exact=float(G.NONREACTIVE_MAX),
        reproduction=repro, anchors=anchors, bootstrap=dict(resamples=BOOT_N, seed=BOOT_SEED, papers=len(papers)),
        near_infeasibility_rule=f"regret > {NEAR_REGRET:g} or STY leader cost > {NEAR_COST_RATIO:g} x its S5 cost",
        entries=int(len(cand)), unique_operating_points=n_unique, scenarios=scen,
        runtime_s=round(time.time() - t0, 1))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250)
    print(scan[["definition", "limit_pct", "groups", "different_leader", "gt5pct", "papers_with_disagreement",
                "nobansode_different_leader", "nobansode_gt5pct", "ordinary", "near_infeasible",
                "co_share_median", "true_inert_share_median"]].to_string(index=False))
    print("reproduction", repro["max_relative_difference"], "anchors",
          anchors if FS.COMBINED else {k: v["got"] for k, v in anchors.items()})


if __name__ == "__main__":
    main()
