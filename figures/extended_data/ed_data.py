"""Panel tables of the Extended Data figures.

Every function returns {panel: (DataFrame, source)}, the exact numbers the panel plots, read from the analysis files.
`render_extended_data.py` draws from these tables and `tools/build_source_data.py` writes them to the Source Data
workbooks, so a figure and its Source Data cannot drift apart.
"""
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

EXTRACT_ACC = "agent/extraction/eval/field_accuracy_by_source.csv"
EXTRACT_ENT = "agent/extraction/eval/entry_metrics.csv"
ALLOY = "analysis/nh3_alloy_extension_2026_10_05/alloy_chain_results.csv"
ALLOY_SUM = "analysis/nh3_alloy_extension_2026_10_05/summary.json"
STATS = "analysis/meoh_main_result_stats_2026_10_06/"
INV = "analysis/meoh_literature_inversion_2026_10_05/"
SUP = "analysis/nh3_supported_2026_10_06/"
MC = "analysis/nh3_mc_ru_actual_2026_10_06/"
BENCH = "analysis/meoh_plant_benchmark_2026_10_06/"
PRUNE = "analysis/meoh_pruning_2026_10_06/"


def path(rel):
    return os.path.join(REPO, rel)


def rcsv(rel, **kw):
    return pd.read_csv(path(rel), **kw)


def rjson(rel):
    return json.load(open(path(rel), encoding="utf-8"))


# ------------------------------------------------------------------ ED Fig. 1: extraction accuracy -------------
def edfig1():
    acc = rcsv(EXTRACT_ACC)
    src = [("table", "main-text tables"), ("SI", "SI printed"), ("plot", "main-text plots"), ("SI-plot", "SI plots")]
    fields = ["X_CO2", "S_MeOH", "STY"]
    a = acc[acc.source_type.isin([s for s, _ in src]) & acc.field.isin(fields)].copy()
    a["source_label"] = a.source_type.map(dict(src))
    a["source_order"] = a.source_type.map({s: i for i, (s, _) in enumerate(src)})
    a["field_order"] = a.field.map({f: i for i, f in enumerate(fields)})
    a["n_correct_strict"] = (a.acc_strict * a.n_extracted).round().astype(int)
    a = a.sort_values(["source_order", "field_order"])[
        ["source_type", "source_label", "field", "n_curated", "n_extracted", "n_correct_strict", "acc_strict",
         "acc_loose"]].reset_index(drop=True)
    ent = rcsv(EXTRACT_ENT)
    b = ent[ent.doi.isin(["TOTAL themecat", "TOTAL suvarna", "TOTAL"])][
        ["doi", "curated", "matched", "recall", "matched_with_X_and_S"]].rename(columns={"doi": "reference_set"})
    b["reference_set"] = b.reference_set.map({"TOTAL themecat": "ThemeCat", "TOTAL suvarna": "Suvarna",
                                              "TOTAL": "all"})
    b = b.reset_index(drop=True)
    return {"a": (a, EXTRACT_ACC), "b": (b, EXTRACT_ENT + " (rows TOTAL themecat, TOTAL suvarna, TOTAL)")}


# ------------------------------------------------------------------ ED Fig. 2: bimetallic surfaces --------------
CHEAP_3D, GROUP6 = {"Fe", "Co", "Ni", "Cu"}, {"Cr", "Mo", "W"}


def _els(name):
    return set(re.findall(r"[A-Z][a-z]?", name))


def edfig2():
    al = rcsv(ALLOY)
    s = rjson(ALLOY_SUM)
    fe = s["Fe_cost_USD_t"]
    feas = al[al.feasible.astype(str) == "True"].copy()
    feas["family_3d_group6"] = [len(_els(x)) == 2 and len(_els(x) & CHEAP_3D) == 1 and len(_els(x) & GROUP6) == 1
                                for x in feas.surface]
    feas["below_Fe"] = feas.cost_USD_t < fe
    cols = ["surface", "domain", "logTOF_673K", "cost_USD_t", "below_Fe", "family_3d_group6", "price_USD_kg"]
    layers = [("a", ["transition_metal"]), ("b", ["transition_metal", "contains_group3to5"]),
              ("c", ["transition_metal", "contains_group3to5", "contains_sp_metal"])]
    out = {}
    for p, doms in layers:
        t = feas[feas.domain.isin(doms)][cols].sort_values("cost_USD_t").reset_index(drop=True)
        out[p] = (t, ALLOY + " (feasible == True; domains %s); Fe benchmark %s" % (", ".join(doms), ALLOY_SUM))
    assert len(out["a"][0]) == 138 and len(out["c"][0]) == s["extended_with_usgs_prices"]["feasible"]
    assert int(out["c"][0].below_Fe.sum()) == s["extended_with_usgs_prices"]["below_Fe"]
    return out, fe


# ------------------------------------------------------------------ ED Fig. 3: methanol robustness --------------
def bootstrap_distribution():
    """Re-draws the paper-cluster bootstrap of run_main_result_stats.py (same seed, same sequence of draws)."""
    st = rjson(STATS + "summary.json")
    gp = rcsv(STATS + "group_noise_probabilities.csv")
    mm0 = gp.observed_mismatch.astype(str).eq("True").to_numpy()
    doi = gp.doi.to_numpy()
    rng = np.random.default_rng(st["noise_model"]["seed"])
    papers = np.unique(doi)
    by_paper = {p: np.where(doi == p)[0] for p in papers}
    n = st["cluster_bootstrap"]["resamples"]
    boot = np.empty(n)
    for b in range(n):
        pick = rng.choice(papers, len(papers), replace=True)
        boot[b] = mm0[np.concatenate([by_paper[p] for p in pick])].mean()
    ci = np.percentile(boot, [2.5, 97.5])
    assert np.allclose(ci, st["cluster_bootstrap"]["fraction_ci95"], atol=1e-12), (ci, st["cluster_bootstrap"])
    assert int(mm0.sum()) == st["point_estimate"]["groups"]
    return boot, st


def edfig3():
    boot, st = bootstrap_distribution()
    edges = np.arange(0.0, 0.8001, 0.02)
    cnt, _ = np.histogram(boot, bins=edges)
    a = pd.DataFrame({"bin_low_fraction": edges[:-1], "bin_high_fraction": edges[1:], "resamples": cnt})
    a.attrs["point"] = st["point_estimate"]["fraction"]
    a.attrs["ci"] = st["cluster_bootstrap"]["fraction_ci95"]
    a.attrs["n"] = st["cluster_bootstrap"]["resamples"]
    b = rcsv(STATS + "regret_threshold_curve.csv")
    rows = []
    labels = {"meas_k1": "re-measured, error x1", "meas_k2": "re-measured, error x2",
              "meas_k4": "re-measured, error x4", "meas_k1_plus_extraction": "error x1 + plot-reading errors"}
    for k, lab in labels.items():
        v = st["noise"][k]
        rows.append(dict(scenario=k, label=lab, mismatch_groups_mean=v["mismatch_groups_mean"],
                         mismatch_groups_q025=v["mismatch_groups_q025_q975"][0],
                         mismatch_groups_q975=v["mismatch_groups_q025_q975"][1],
                         noise_floor_mean=v["sty_leader_differs_from_reported_mean"],
                         noise_floor_q025=v["sty_leader_differs_from_reported_q025_q975"][0],
                         noise_floor_q975=v["sty_leader_differs_from_reported_q025_q975"][1],
                         robust_ge90pct=v["groups_mismatched_in_ge_90pct_of_draws"]))
    c = pd.DataFrame(rows)
    c.attrs["observed"] = st["point_estimate"]["groups"]
    c.attrs["draws"] = st["noise_model"]["draws"]
    gp = rcsv(STATS + "group_noise_probabilities.csv")
    d = gp[gp.observed_mismatch.astype(str) == "True"].copy()
    d = d.sort_values(["p_mismatch_meas_k1", "observed_regret"], ascending=False).reset_index(drop=True)
    d = d[["group", "doi", "observed_regret", "p_mismatch_meas_k1", "p_mismatch_meas_k2", "p_mismatch_meas_k4",
           "p_mismatch_meas_k1_plus_extraction"]]
    assert int((d.p_mismatch_meas_k1 >= 0.9).sum()) == st["noise"]["meas_k1"]["observed_mismatches_kept_in_ge_90pct"]
    return {"a": (a, STATS + "group_noise_probabilities.csv (observed_mismatch, doi) re-drawn with the seed and "
                  "resample count of " + STATS + "summary.json; 95 % CI checked against summary.json"),
            "b": (b, STATS + "regret_threshold_curve.csv"),
            "c": (c, STATS + "summary.json (noise.*)"),
            "d": (d, STATS + "group_noise_probabilities.csv (observed_mismatch == True)")}


# ------------------------------------------------------------------ ED Fig. 4: measured ammonia catalysts -------
FUSED_FE_WT = 71.51      # run_supported_chain.py line 181: w = 0.7151 if fused


def edfig4():
    s = rcsv(SUP + "supported_candidates.csv")
    sm = rjson(SUP + "summary.json")
    p = s[s.status.str.startswith("primary") & s.cost_USD_t.notna()].copy()
    assert len(p) == sm["primary"]
    fused = p.metal_wt_pct.isna()
    assert set(p[fused].catalyst) == {"Fe1−xO", "Fe3O4"}
    p["metal_wt_pct_used"] = np.where(fused, FUSED_FE_WT, p.metal_wt_pct)
    p["rate_umol_per_g_metal_h"] = p.rate_umol_g_h / (p.metal_wt_pct_used / 100.0)
    t = p[["catalyst", "active_metals", "metal_wt_pct_used", "T_C", "P_MPa", "rate_umol_g_h",
           "rate_umol_per_g_metal_h", "cost_USD_t", "cost_recovery90", "ref"]].sort_values("cost_USD_t")
    t = t.rename(columns={"active_metals": "metal", "rate_umol_g_h": "rate_umol_per_g_cat_h"}).reset_index(drop=True)
    t.attrs["fe"] = sm["Fe_benchmark_USD_t"]
    t.attrs["overall"] = sm["overall"]
    b = t.loc[t.groupby("metal").cost_USD_t.idxmin(), ["metal", "catalyst", "cost_USD_t"]].rename(
        columns={"catalyst": "lowest_cost_catalyst", "cost_USD_t": "lowest_cost_USD_t"})
    b = b.merge(t.groupby("metal").size().rename("catalysts").reset_index(), on="metal")
    b = b.set_index("metal").loc[["Ru", "Fe", "Co", "Ni"]].reset_index()
    for m, v in sm["per_metal"].items():
        assert abs(b.set_index("metal").loc[m, "lowest_cost_USD_t"] - v["cost_min"]) < 1e-9
    b.attrs["fe"] = sm["Fe_benchmark_USD_t"]
    return {"b": (b, SUP + "supported_candidates.csv (lowest cost per metal; checked against summary.json per_metal)"),
            "a": (t, SUP + "supported_candidates.csv (status primary*, cost present); rate per g metal = rate per g "
                  "catalyst / metal content (fused Fe 71.51 wt%, run_supported_chain.py); Fe benchmark "
                  + SUP + "summary.json")}


# ------------------------------------------------------------------ ED Fig. 5: actual-Ru Monte Carlo -------------
def edfig5():
    sm = rjson(MC + "summary.json")
    d = rcsv(MC + "draws.csv")
    rows = [("preregistered (pure-Ru benchmark bed)", "Ru_base", sm["base_reproduced"]["P_Fe_cheaper"]),
            ("A: u and r, benchmark bed volume", "Ru_A", sm["A"]["P_Fe_cheaper"]),
            ("A_bed: u and r, supported bed", "Ru_A_bed", sm["A_bed"]["P_Fe_cheaper"]),
            ("B: measured Ru catalysts, 90-94 % recovery", "Ru_B", sm["B"]["P_Fe_cheaper"]),
            ("B0: measured Ru catalysts, no recovery", "Ru_B0", sm["B0"]["P_Fe_cheaper"])]
    a = []
    for lab, col, p in rows:
        pd_ = float((d.Fe < d[col]).mean())
        assert abs(pd_ - p) < 1e-12, (col, pd_, p)
        a.append(dict(treatment=lab, column=col, P_Fe_cheaper=p, draws=len(d),
                      median_Ru_minus_Fe_USD_t=float((d[col] - d.Fe).median())))
    a = pd.DataFrame(a)
    ru_wins = d.Ru_A_bed < d.Fe

    def binned(x, edges, name):
        idx = np.digitize(x, edges[1:-1])
        out = []
        for i in range(len(edges) - 1):
            m = idx == i
            out.append({name + "_low": edges[i], name + "_high": edges[i + 1], "draws": int(m.sum()),
                        "P_Ru_wins_A_bed": float(ru_wins[m].mean()),
                        "P_Ru_wins_A": float((d.Ru_A < d.Fe)[m].mean())})
        return pd.DataFrame(out)

    u_edges = np.geomspace(sm["ranges"]["u"][0], sm["ranges"]["u"][1], 9)
    r_edges = np.linspace(sm["ranges"]["r"][0], sm["ranges"]["r"][1], 9)
    w_edges = np.array([0.0, 1.0, 2.5, 5.0, 10.0, 15.0])
    b = binned(d.u.to_numpy(), u_edges, "u")
    c = binned(d.r.to_numpy(), r_edges, "r")
    e = binned(d.measured_wt_pct.to_numpy(), w_edges, "Ru_wt_pct")
    src = MC + "draws.csv (Ru wins: Ru_A_bed < Fe, or Ru_A < Fe)"
    return {"a": (a, MC + "summary.json (P_Fe_cheaper), checked against " + MC + "draws.csv"),
            "b": (b, src + "; 8 log-spaced bins of u over the drawn range"),
            "c": (c, src + "; 8 bins of r over the drawn range"),
            "d": (e, src + "; bins of the drawn Ru content")}


# ------------------------------------------------------------------ ED Fig. 6: methanol plant benchmark ---------
def edfig6():
    rc = rcsv(BENCH + "reconciliation_cost.csv")
    pf = rc[rc.case.str.startswith("B3 Perez-Fortes")].copy()
    terms = ["H2", "electricity + utilities", "catalyst replacement", "capital (annuity at 8 %, 20 y)", "fixed O&M",
             "residual direct + 10 % of NPC (anchor convention)",
             "TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)", "TOTAL, anchor convention"]
    a = pf.set_index("term").loc[terms, ["model", "reference", "deviation", "ref_basis"]].reset_index()
    tot = rc[rc.term.str.contains("like-for-like") | (rc.term == "TOTAL") | (rc.term == "TOTAL with catalyst term")]
    tot = tot[~tot.term.str.contains("catalyst in residual")]
    label = []
    for cs, tm in zip(tot.case, tot.term):
        study = re.match(r"B\d (\S+ \S+ ?\S*)", cs).group(1)
        if cs.startswith("B1"):
            study = "Campos 2022 one-step"
        elif cs.startswith("B2"):
            study = "Campos 2022 three-step" + (" + catalyst term" if "catalyst" in tm else "")
        elif cs.startswith("B3"):
            study = "Perez-Fortes 2016"
        elif cs.startswith("B4"):
            study = "Szima 2018"
        elif cs.startswith("B5"):
            study = "Nyari 2022, " + tm.split(":")[0]
        elif cs.startswith("B6"):
            study = "Nieminen 2019"
        elif cs.startswith("B7"):
            study = "Schorn 2021, " + tm.split(":")[0]
        label.append(study)
    b = pd.DataFrame({"study": label, "case": tot.case.values, "term": tot.term.values, "model_eur_t": tot.model.values,
                      "reference_eur_t": tot.reference.values})
    b["deviation_pct"] = 100 * (b.model_eur_t / b.reference_eur_t - 1)
    b = b.drop_duplicates("study").reset_index(drop=True)
    sm = rjson(BENCH + "summary.json")
    m7 = next(v for k, v in sm["model_cases"].items() if k.startswith("M7"))
    ref = rcsv(BENCH + "reference_values.csv")
    ref = ref[ref.ref_id == "PEREZFORTES16"].set_index("quantity").value
    qs = [("H$_2$ (t/t)", "h2_t_per_t", "H2_t_per_t"), ("CO$_2$ (t/t)", "co2_t_per_t", "CO2_t_per_t"),
          ("carbon efficiency", "carbon_efficiency", "carbon_efficiency"),
          ("recycle ratio", "recycle_ratio", "recycle_ratio"),
          ("compression power (MWh/t)", "elec_MWh_t", "electricity_compressors_MWh_t")]
    c = pd.DataFrame([dict(metric=lab, model=m7[mk], reference=float(ref[rk]), ratio=m7[mk] / float(ref[rk]))
                      for lab, mk, rk in qs])
    ss = rjson(BENCH + "sensitivity_summary.json")["variants"]
    d = pd.DataFrame([dict(variant=k, mismatch_groups=v["top1_mismatch_groups"], groups=v["groups"],
                           papers_with_mismatch=v["papers_with_mismatch"],
                           regret_median_mismatched=v["regret_median_mismatched"]) for k, v in ss.items()])
    d = d.sort_values("mismatch_groups", kind="stable").reset_index(drop=True)
    d.insert(0, "key", np.arange(1, len(d) + 1))
    return {"a": (a, BENCH + "reconciliation_cost.csv (case B3 Perez-Fortes 2016)"),
            "b": (b, BENCH + "reconciliation_cost.csv (TOTAL and like-for-like rows)"),
            "c": (c, BENCH + "summary.json (model_cases M7) and reference_values.csv (ref_id PEREZFORTES16)"),
            "d": (d, BENCH + "sensitivity_summary.json (variants)")}


# ------------------------------------------------------------------ ED Fig. 7: compute saved by the bound -------
def _prune_group(g, col, rel):
    up = g.STY.idxmax()
    ev, best = {up}, g.loc[up, col]
    for i in g.sort_values("bound", kind="stable").index:
        if g.loc[i, "bound"] > best * (1 + rel):
            break
        ev.add(i)
        best = min(best, g.loc[i, col])
    return ev


def edfig7():
    cb = rcsv(PRUNE + "candidate_bounds.csv")
    gp = rcsv(PRUNE + "group_pruning.csv").set_index("group")
    sm = rjson(PRUNE + "summary.json")
    for t, col in (("recycled_opt", "cost_recycled_opt"), ("inert_opt", "cost_inert_opt")):
        flag = np.zeros(len(cb), bool)
        for key, g in cb.groupby("group"):
            ev = _prune_group(g, col, 5e-6)
            assert len(ev) == gp.loc[key, "evaluated_" + t], (key, t)
            flag[list(ev)] = True
        cb["evaluated_" + t] = flag
        assert int(flag.sum()) == sm["pruning"][t]["evaluated"]
    a = cb[["group", "entry", "bound", "cost_recycled_opt", "cost_inert_opt", "evaluated_recycled_opt",
            "evaluated_inert_opt"]]
    al = rcsv(ALLOY)
    s = rjson(ALLOY_SUM)
    al["pruned"] = al.pruned.astype(str) == "True"
    al["feasible"] = al.feasible.astype(str) == "True"
    assert int(al.pruned.sum()) == 1397 == len(al) - 298 and len(al) == s["costed_with_frozen_or_usgs_prices"]
    c = al[["surface", "domain", "lower_bound_USD_t", "cost_USD_t", "feasible", "pruned"]].copy()
    fe = s["Fe_cost_USD_t"]
    assert not ((c.pruned) & (c.cost_USD_t < fe)).any()
    frozen = al[al.price_source == "frozen"]
    rows = [dict(system="methanol, recycled CO", candidates=sm["pruning"]["recycled_opt"]["full"],
                 full_evaluations=sm["pruning"]["recycled_opt"]["evaluated"],
                 excluded_by_bound=sm["pruning"]["recycled_opt"]["excluded"],
                 leader_missed=sm["pruning"]["recycled_opt"]["leader_missed"]),
            dict(system="methanol, inert CO", candidates=sm["pruning"]["inert_opt"]["full"],
                 full_evaluations=sm["pruning"]["inert_opt"]["evaluated"],
                 excluded_by_bound=sm["pruning"]["inert_opt"]["excluded"],
                 leader_missed=sm["pruning"]["inert_opt"]["leader_missed"]),
            dict(system="ammonia alloys, frozen prices", candidates=s["costed"],
                 full_evaluations=s["pruning"]["full_optimizations_needed"],
                 excluded_by_bound=s["pruning"]["pruned"], leader_missed=len(s["pruning"]["false_prunes"])),
            dict(system="ammonia alloys, frozen + USGS prices", candidates=len(c),
                 full_evaluations=int((~c.pruned).sum()), excluded_by_bound=int(c.pruned.sum()),
                 leader_missed=int(((c.pruned) & (c.cost_USD_t < fe)).sum()))]
    assert len(frozen) == s["costed"] and int(frozen.pruned.sum()) == s["pruning"]["pruned"]
    d = pd.DataFrame(rows)
    return {"a": (a, PRUNE + "candidate_bounds.csv; evaluated/excluded re-derived with the agent rule of "
                  "run_meoh_pruning.py and checked per group against group_pruning.csv"),
            "b": (c, ALLOY + " (lower_bound_USD_t, cost_USD_t, pruned); Fe " + ALLOY_SUM),
            "c": (d, PRUNE + "summary.json, " + ALLOY_SUM + " (pruning) and " + ALLOY)}, fe


if __name__ == "__main__":
    for f in (edfig1, edfig3, edfig4, edfig5, edfig6):
        r = f()
        print(f.__name__, {k: v[0].shape for k, v in r.items()})
    r, _ = edfig2()
    print("edfig2", {k: v[0].shape for k, v in r.items()})
    r, _ = edfig7()
    print("edfig7", {k: v[0].shape for k, v in r.items()})
