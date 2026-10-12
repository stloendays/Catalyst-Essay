"""Task A: where in process-constraint space the STY leader stops being the plant-cost leader (methanol field result).

For every scenario of common.SCENARIOS (reactor-inlet non-H2/CO2 limit 4-30 %, S6 = 6.86 %, S5 = no limit, S4 = no
limit with the laboratory conversion uncapped) on the frozen printed-cohort candidates:

  1. groups with a different leader, regret > 1 / 5 / 10 %, contributing papers, the same without Bansode 2013, the
     mismatch kinds (mismatch_kinds.classify) with their > 5 % and paper counts, median and maximum regret;
  2. paper-cluster bootstrap (10,000 resamples of the 28 papers, the frozen seed) of the fraction of groups with a
     different leader and with a regret > 5 %, the same resamples for every scenario; trend of the incidence against
     the limit over the ten absolute limits (Cochran-Armitage on the 40 groups per limit, and permutation versions
     that shuffle the limit labels within each paper and within each group);
  3. near-infeasibility: a disagreement is ordinary when the regret is <= 1 and the STY leader's cost is <= 2x its S5
     cost, otherwise near-infeasible; the model sweep below adds the purge levels open to the STY leader;
  4. mechanism: in the disagreements, is the plant-cost leader more selective, higher in single-pass conversion,
     cooler (and lower in CO selectivity) than the STY leader.

Model sweep: every scored entry is run through meoh_general_model.purge_sweep (recycled CO, the frozen S5 settings)
to count the purge levels open under each limit, the purge chosen and the tightest limit the entry can meet on the
0.5-40 % grid (L_min). The sweep must reproduce every frozen cost column it re-derives (relative 1e-7) and the frozen
n_inlet_ok_recycled exactly. BOUNDARY_WORKERS (default 4) processes; BOUNDARY_REUSE_SWEEP=1 reads the committed
entry_feasibility.csv instead.

Outputs: entry_feasibility.csv, boundary_groups.csv, boundary_curve.csv, boundary_summary.json (make_boundary_figure.py
draws boundary_curve.png/.svg).
"""
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import norm

from common import (BANSODE, BOOT_N, BOOT_SEED, BY_NAME, HERE, LIMITS, PERM_N, PERM_SEED, PUBLISHED_RANGE, S6_LIMIT,
                    SCENARIOS, G, load_candidates, leaders)

SWEEP_SCENARIOS = [s for s in SCENARIOS if s["name"] != "S4_uncapped"]
NEAR_REGRET, NEAR_COST_RATIO = 1.0, 2.0


# ------------------------------------------------------------------------------------------------ model sweep ------
def sweep_entry(row):
    c = dict(X=row["X"], SMeOH=row["SMeOH"], SCH4=row["SCH4"], SCO=row["SCO"])
    s = G.purge_sweep(c, STY_per_g_cat=row["STY"], x_co="recycled_central", P_bar=row["P_bar"],
                      h2_co2=row["h2_co2"], T_C=row["T_C"])
    cost = np.asarray(s["cost_eur_t"], dtype=float)
    nr = np.asarray(s["nonreactive_fraction"], dtype=float)
    eq = np.asarray(s["equilibrium_feasible"], dtype=bool)
    out = dict(idx=row["idx"], L_min=float(nr[eq].min()) if eq.any() else math.nan)
    for sc in SWEEP_SCENARIOS:
        mask = np.isfinite(cost) if sc["limit"] is None else eq & (nr <= sc["limit"])
        n = sc["name"]
        out[f"n_ok_{n}"] = int(mask.sum())
        if mask.any():
            j = int(np.argmin(np.where(mask, cost, np.inf)))
            out[f"cost_{n}"], out[f"purge_{n}"], out[f"inlet_{n}"] = float(cost[j]), float(G.PURGES[j]), float(nr[j])
        else:
            out[f"cost_{n}"] = out[f"purge_{n}"] = out[f"inlet_{n}"] = math.nan
    return out


def model_sweep(cand, scored_idx):
    path = HERE / "entry_feasibility.csv"
    if os.environ.get("BOUNDARY_REUSE_SWEEP") == "1" and path.exists():
        feas = pd.read_csv(path)
    else:
        rows = [dict(idx=int(i), **{k: cand.at[i, k] for k in ("X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2",
                                                                 "T_C")}) for i in scored_idx]
        workers = int(os.environ.get("BOUNDARY_WORKERS", "4"))
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            feas = pd.DataFrame(list(ex.map(sweep_entry, rows, chunksize=8)))
        print(f"model sweep: {len(rows)} entries, {time.time() - t0:.0f} s on {workers} workers")
        feas.insert(1, "group", cand.loc[feas.idx, "group"].to_numpy())
        feas.insert(2, "catalyst", cand.loc[feas.idx, "catalyst"].to_numpy())
        feas.to_csv(path, index=False, float_format="%.12g")
    feas = feas.set_index("idx")
    # the sweep must reproduce the frozen costs it re-derives and the frozen count of levels open under 6.86 %
    worst = 0.0
    for sc in SWEEP_SCENARIOS:
        a = cand.loc[feas.index, sc["col"]].astype(float).to_numpy()
        b = feas[f"cost_{sc['name']}"].to_numpy(float)
        if not (np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a, b, rtol=1e-7, atol=0, equal_nan=True)):
            raise AssertionError(f"model sweep does not reproduce {sc['col']}")
        ok = np.isfinite(a)
        worst = max(worst, float(np.max(np.abs(a[ok] / b[ok] - 1.0))))
    if not (cand.loc[feas.index, "n_inlet_ok_recycled"].to_numpy() == feas.n_ok_S6.to_numpy()).all():
        raise AssertionError("model sweep does not reproduce n_inlet_ok_recycled")
    return feas, dict(entries=len(feas), max_relative_cost_difference=worst, n_inlet_ok_recycled_identical=True,
                      cost_columns_checked=[s["col"] for s in SWEEP_SCENARIOS])


# ------------------------------------------------------------------------------------------ per scenario ----------
def group_table(cand, feas, sc, s5_lab):
    col, name = sc["col"], sc["name"]
    t, gm, kinds = leaders(cand, col)
    lab, plant = cand.loc[t.lab_idx], cand.loc[t.plant_idx]
    t.insert(0, "scenario", name)
    t["lab_leader"], t["plant_leader"] = lab.catalyst.to_numpy(), plant.catalyst.to_numpy()
    for k in ("T_C", "SMeOH", "X", "SCO", "SCH4", "STY"):
        t[f"lab_{k}"], t[f"plant_{k}"] = lab[k].to_numpy(), plant[k].to_numpy()
    t["c_lab_S5"] = lab.cost_recycled_opt.to_numpy()
    t["lab_cost_vs_S5"] = t.c_lab / t.c_lab_S5
    t["plant_cost_vs_S5"] = t.c_plant / plant.cost_recycled_opt.to_numpy()
    t["bansode"] = t.doi == BANSODE
    near = (t.regret > NEAR_REGRET) | (t.lab_cost_vs_S5 > NEAR_COST_RATIO)
    t["class"] = np.where(t.mismatch, np.where(near, "near-infeasible", "ordinary"), "")
    # the S5 STY leader left the group (infeasible in this scenario), so another entry leads by STY here
    t["s5_lab_leader_dropped"] = [bool(s5_lab.get(g, li) != li) for g, li in zip(t.group, t.lab_idx)]
    if sc["name"] != "S4_uncapped":
        fl, fp = feas.loc[t.lab_idx], feas.loc[t.plant_idx]
        t["lab_n_purge_levels_open"] = fl[f"n_ok_{name}"].to_numpy()
        t["lab_purge"], t["plant_purge"] = fl[f"purge_{name}"].to_numpy(), fp[f"purge_{name}"].to_numpy()
        t["lab_L_min"], t["plant_L_min"] = fl.L_min.to_numpy(), fp.L_min.to_numpy()
        t["lab_L_min_over_limit"] = (fl.L_min.to_numpy() / sc["limit"]) if sc["limit"] else np.nan
    return t, kinds


def counts(t):
    m = t[t.mismatch]
    return dict(groups=len(t), different_leader=len(m), fraction=len(m) / len(t) if len(t) else math.nan,
                gt1pct=int((m.regret > 0.01).sum()), gt5pct=int((m.regret > 0.05).sum()),
                gt10pct=int((m.regret > 0.10).sum()), papers=int(m.doi.nunique()),
                papers_gt5pct=int(m[m.regret > 0.05].doi.nunique()))


def mechanism(m):
    if m.empty:
        return dict(disagreements=0)
    dS, dX, dT, dCO = (m.plant_SMeOH - m.lab_SMeOH, m.plant_X - m.lab_X, m.plant_T_C - m.lab_T_C,
                       m.plant_SCO - m.lab_SCO)
    n = len(m)
    out = dict(disagreements=n,
               plant_more_selective=int((dS > 1e-12).sum()), plant_equally_selective=int((dS.abs() <= 1e-12).sum()),
               plant_higher_conversion=int((dX > 1e-12).sum()), plant_equal_conversion=int((dX.abs() <= 1e-12).sum()),
               plant_cooler=int((dT < -0.05).sum()), plant_same_temperature=int((dT.abs() <= 0.05).sum()),
               plant_less_CO=int((dCO < -1e-12).sum()))
    for k in ("plant_more_selective", "plant_higher_conversion", "plant_cooler", "plant_less_CO"):
        out[f"{k}_fraction"] = out[k] / n
    out["median"] = dict(dS=float(dS.median()), dX=float(dX.median()), dT_C=float(dT.median()),
                         S_lab=float(m.lab_SMeOH.median()), S_plant=float(m.plant_SMeOH.median()))
    return out


def near_infeasibility(t, sc):
    m = t[t.mismatch]
    out = {}
    for cls in ("ordinary", "near-infeasible"):
        x = m[m["class"] == cls]
        d = dict(groups=len(x), gt5pct=int((x.regret > 0.05).sum()), gt10pct=int((x.regret > 0.10).sum()),
                 papers=int(x.doi.nunique()), without_bansode=int((~x.bansode).sum()),
                 regret_median=float(x.regret.median()) if len(x) else None,
                 regret_max=float(x.regret.max()) if len(x) else None,
                 lab_cost_vs_S5_median=float(x.lab_cost_vs_S5.median()) if len(x) else None)
        if "lab_purge" in x and len(x):
            d.update(lab_purge_median=float(x.lab_purge.median()),
                     lab_n_purge_levels_open_median=float(x.lab_n_purge_levels_open.median()),
                     lab_L_min_over_limit_median=(float(x.lab_L_min_over_limit.median()) if sc["limit"] else None))
        out[cls.replace("-", "_")] = d
    out["by_criterion"] = dict(regret_gt1=int((m.regret > NEAR_REGRET).sum()),
                               lab_cost_gt2x_S5=int((m.lab_cost_vs_S5 > NEAR_COST_RATIO).sum()),
                               both=int(((m.regret > NEAR_REGRET) & (m.lab_cost_vs_S5 > NEAR_COST_RATIO)).sum()))
    # near-infeasible by the cost criterion alone while the plant-cost leader's cost also more than doubled: the
    # whole group is expensive under the limit, not only its STY leader
    nm = m[m["class"] == "near-infeasible"]
    out["near_infeasible_group_wide"] = int(((nm.regret <= NEAR_REGRET) & (nm.plant_cost_vs_S5 > NEAR_COST_RATIO)).sum())
    out["s5_lab_leader_dropped_groups"] = int(t.s5_lab_leader_dropped.sum())
    o = out["ordinary"]["groups"]
    out["different_leader_with_near_infeasible"] = len(m)
    out["different_leader_without_near_infeasible"] = o
    out["fraction_without_near_infeasible_of_all_groups"] = o / len(t)
    out["fraction_without_near_infeasible_of_groups_not_near_infeasible"] = o / (len(t) - out["near_infeasible"]["groups"])
    return out


# ------------------------------------------------------------------------------------------ statistics -----------
def per_paper(t, papers):
    g = t.assign(gt5=t.mismatch & (t.regret > 0.05),
                 ordinary=t.mismatch & (t["class"] == "ordinary")).groupby("doi")
    return (g.size().reindex(papers).to_numpy(float), g.mismatch.sum().reindex(papers).to_numpy(float),
            g.gt5.sum().reindex(papers).to_numpy(float), g.ordinary.sum().reindex(papers).to_numpy(float))


def bootstrap_all(tables, papers):
    """The frozen bootstrap's resamples (meoh_candidates.bootstrap: same seed, count and paper order), applied to
    every scenario, so the bands and the differences from S5 use the same resamples."""
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(papers), size=(BOOT_N, len(papers)))
    w = np.zeros((BOOT_N, len(papers)))
    np.add.at(w, (np.repeat(np.arange(BOOT_N), len(papers)), idx.ravel()), 1.0)
    fr = {}
    for name, t in tables.items():
        n, mis, gt5, ordi = per_paper(t, papers)
        fr[name] = dict(different_leader=(w @ mis) / (w @ n), gt5pct=(w @ gt5) / (w @ n),
                        ordinary=(w @ ordi) / (w @ n))

    def ci(v):
        lo, hi = np.percentile(v, [2.5, 97.5])
        return [float(lo), float(hi)]

    out = {}
    for name in tables:
        out[name] = {k: dict(ci95=ci(v), mean=float(v.mean())) for k, v in fr[name].items()}
        out[name].update({f"{k}_minus_S5": dict(ci95=ci(fr[name][k] - fr["S5"][k]))
                          for k in ("different_leader", "gt5pct")})
    return out, dict(resamples=BOOT_N, seed=BOOT_SEED, papers=len(papers))


def cochran_armitage(r, n, s):
    r, n, s = (np.asarray(v, float) for v in (r, n, s))
    p = r.sum() / n.sum()
    T = float(np.sum(s * (r - n * p)))
    var = p * (1 - p) * (np.sum(n * s * s) - np.sum(n * s) ** 2 / n.sum())
    z = T / math.sqrt(var) if var > 0 else math.nan
    return dict(z=z, p_two_sided=float(2 * norm.sf(abs(z))), statistic=T)


def block_permutation(Y, s, n_perm, seed):
    """Two-sided permutation test of sum_l s_l * sum_b Y[b, l]: the limit labels are shuffled within each block (row
    of Y), which keeps every block's own total and the correlation of its outcomes across limits."""
    rng = np.random.default_rng(seed)
    s = np.asarray(s, float)
    obs = float((Y * s).sum())
    null_mean = float(Y.sum() * s.mean())
    perm = np.argsort(rng.random((n_perm, Y.shape[0], Y.shape[1])), axis=2)
    stat = (Y[None, :, :] * s[perm]).sum(axis=(1, 2))
    extreme = np.abs(stat - null_mean) >= abs(obs - null_mean) - 1e-9
    return dict(statistic=obs, null_mean=null_mean, p_two_sided=float((extreme.sum() + 1) / (n_perm + 1)),
                permutations=n_perm, seed=seed, blocks=int(Y.shape[0]))


def trend_tests(tables, papers):
    names = [f"lim{L}" for L in LIMITS]
    scores = dict(limit_pct=np.array(LIMITS, float), rank=np.arange(1, len(LIMITS) + 1, dtype=float))
    groups = sorted(tables["S5"].group)
    out = dict(scenarios=names, note="the ten absolute limits of the frozen sweep; the same 40 groups at every limit")
    for outcome in ("different_leader", "gt5pct"):
        def flag(t):
            return (t.mismatch & (t.regret > 0.05)) if outcome == "gt5pct" else t.mismatch
        r = [int(flag(tables[nm]).sum()) for nm in names]
        n = [len(tables[nm]) for nm in names]
        Yg = np.column_stack([pd.Series(flag(tables[nm]).to_numpy(float), index=tables[nm].group)
                              .reindex(groups).to_numpy() for nm in names])
        Yp = np.column_stack([flag(tables[nm]).groupby(tables[nm].doi).sum().reindex(papers).to_numpy(float)
                              for nm in names])
        if np.isnan(Yg).any() or np.isnan(Yp).any():
            raise AssertionError("trend test: a group or paper is missing at some limit")
        res = dict(counts=r, groups=n)
        for sname, s in scores.items():
            res[sname] = dict(cochran_armitage_groups=cochran_armitage(r, n, s),
                              permutation_within_paper=block_permutation(Yp, s, PERM_N, PERM_SEED),
                              permutation_within_group=block_permutation(Yg, s, PERM_N, PERM_SEED + 1))
        out[outcome] = res
    return out


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main():
    t0 = time.time()
    cand = load_candidates()
    s5, _, _ = leaders(cand, "cost_recycled_opt")
    scored_idx = sorted(cand.index[cand.group.isin(s5.group)])
    feas, sweep_check = model_sweep(cand, scored_idx)
    s5_lab = dict(zip(s5.group, s5.lab_idx))
    papers = sorted(s5.doi.unique())

    tables, kinds = {}, {}
    for sc in SCENARIOS:
        tables[sc["name"]], kinds[sc["name"]] = group_table(cand, feas, sc, s5_lab)
    boot, boot_meta = bootstrap_all(tables, papers)
    trend = trend_tests(tables, papers)

    rows, scen_out = [], {}
    for sc in SCENARIOS:
        name = sc["name"]
        t = tables[name]
        m = t[t.mismatch]
        c, nb = counts(t), counts(t[~t.bansode])
        k = kinds[name]
        ni, mech = near_infeasibility(t, sc), mechanism(m)
        mech_ord = mechanism(m[m["class"] == "ordinary"])
        reg = dict(median_of_disagreements=float(m.regret.median()) if len(m) else 0.0,
                   median_all=float(t.regret.median()), max=float(t.regret.max()), mean_all=float(t.regret.mean()))
        scen_out[name] = dict(label=sc["label"], cost_column=sc["col"], limit=sc["limit"], papers=int(t.doi.nunique()),
                              entries=int(t.n.sum()),
                              candidates_infeasible=int((~np.isfinite(cand.loc[scored_idx, sc["col"]].astype(float))).sum()),
                              counts=c, without_bansode=nb, kinds=k, regret=reg, bootstrap=boot[name],
                              near_infeasibility=ni, mechanism=mech, mechanism_ordinary_only=mech_ord)
        row = dict(scenario=name, limit_pct=sc["limit"] * 100 if sc["limit"] else np.nan, cost_column=sc["col"],
                   on_curve=sc["curve"], groups=c["groups"], papers=int(t.doi.nunique()),
                   different_leader=c["different_leader"], fraction=c["fraction"],
                   fraction_ci_lo=boot[name]["different_leader"]["ci95"][0],
                   fraction_ci_hi=boot[name]["different_leader"]["ci95"][1],
                   gt1pct=c["gt1pct"], gt5pct=c["gt5pct"], gt5pct_fraction=c["gt5pct"] / c["groups"],
                   gt5pct_ci_lo=boot[name]["gt5pct"]["ci95"][0], gt5pct_ci_hi=boot[name]["gt5pct"]["ci95"][1],
                   gt10pct=c["gt10pct"], papers_with_disagreement=c["papers"], papers_gt5pct=c["papers_gt5pct"],
                   nobansode_groups=nb["groups"], nobansode_different_leader=nb["different_leader"],
                   nobansode_gt1pct=nb["gt1pct"], nobansode_gt5pct=nb["gt5pct"], nobansode_gt10pct=nb["gt10pct"],
                   nobansode_papers=nb["papers"])
        for tag, lab in (("cat_sameT", "other_cat_sameT"), ("T", "other_T"), ("cat_and_T", "other_cat_and_T"),
                         ("same_record", "same_record")):
            row[f"{lab}"], row[f"{lab}_gt5pct"], row[f"{lab}_papers"] = k[tag]["groups"], k[tag]["gt5pct"], k[tag]["papers"]
        row.update(other_catalyst=k["other_catalyst"]["groups"], other_catalyst_of=k["other_catalyst"]["of"],
                   other_temperature=k["other_temperature"]["groups"], other_temperature_of=k["other_temperature"]["of"],
                   regret_median_disagreements=reg["median_of_disagreements"], regret_max=reg["max"],
                   ordinary=ni["ordinary"]["groups"], ordinary_gt5pct=ni["ordinary"]["gt5pct"],
                   ordinary_papers=ni["ordinary"]["papers"], ordinary_nobansode=ni["ordinary"]["without_bansode"],
                   near_infeasible=ni["near_infeasible"]["groups"], near_infeasible_gt5pct=ni["near_infeasible"]["gt5pct"],
                   near_infeasible_group_wide=ni["near_infeasible_group_wide"],
                   ordinary_fraction=ni["fraction_without_near_infeasible_of_all_groups"],
                   ordinary_ci_lo=boot[name]["ordinary"]["ci95"][0], ordinary_ci_hi=boot[name]["ordinary"]["ci95"][1])
        for kk in ("plant_more_selective", "plant_higher_conversion", "plant_cooler", "plant_less_CO"):
            row[kk] = mech.get(kk, 0)
            row[f"{kk}_fraction"] = mech.get(f"{kk}_fraction", np.nan)
        rows.append(row)

    curve = pd.DataFrame(rows)
    curve.to_csv(HERE / "boundary_curve.csv", index=False, float_format="%.10g")
    pd.concat(tables.values()).to_csv(HERE / "boundary_groups.csv", index=False, float_format="%.10g")
    summary = dict(
        source="analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv (frozen printed cohort, read as is)",
        groups=len(s5), papers=len(papers), entries=int(s5.n.sum()), bansode_doi=BANSODE,
        bansode_groups=int((s5.doi == BANSODE).sum()), s6_limit=S6_LIMIT, published_range=list(PUBLISHED_RANGE),
        near_infeasible_rule=f"disagreement with regret > {NEAR_REGRET:g} or STY leader's cost > {NEAR_COST_RATIO:g}x "
                             "its own S5 cost; otherwise ordinary",
        model_sweep=sweep_check, bootstrap=boot_meta, trend=trend, scenarios=scen_out,
        runtime_s=round(time.time() - t0, 1))
    (HERE / "boundary_summary.json").write_text(json.dumps(jsonable(summary), indent=1) + "\n", encoding="utf-8")
    show = ["scenario", "different_leader", "gt1pct", "gt5pct", "gt10pct", "papers_with_disagreement",
            "nobansode_different_leader", "nobansode_gt5pct", "ordinary", "ordinary_gt5pct", "near_infeasible",
            "near_infeasible_group_wide", "ordinary_ci_lo", "ordinary_ci_hi",
            "fraction_ci_lo", "fraction_ci_hi", "gt5pct_ci_lo", "gt5pct_ci_hi"]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(curve[show].round(3).to_string(index=False))
    print(json.dumps(jsonable({o: {s: trend[o][s] for s in ("limit_pct",)} for o in ("different_leader", "gt5pct")}),
                     indent=1))
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
