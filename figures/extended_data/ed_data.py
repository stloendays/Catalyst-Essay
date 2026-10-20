"""Panel tables of the Extended Data figures.

Every function returns {panel: (DataFrame, source)}, the exact numbers the panel plots, read from the analysis files.
`render_extended_data.py` draws from these tables and `tools/build_source_data.py` writes them to the Source Data
workbooks, so a figure and its Source Data cannot drift apart.

Ammonia panels (bimetallic surfaces, measured catalysts, actual-Ru Monte Carlo, the ammonia rows of the bound) read the
NH3-FINAL-1.2 outputs in the analysis folders' nh3_1_2/ subfolders (canonical run nh3_final_1_2_20261013).
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
ALLOY = "analysis/nh3_alloy_extension_2026_10_05/nh3_1_2/alloy_chain_results.csv"
ALLOY_SUM = "analysis/nh3_alloy_extension_2026_10_05/nh3_1_2/summary.json"
STATS = "analysis/meoh_main_result_stats_2026_10_06/"
INV = "analysis/meoh_literature_inversion_2026_10_05/"
SUP = "analysis/nh3_supported_2026_10_06/nh3_1_2/"
MC = "analysis/nh3_mc_ru_actual_2026_10_06/nh3_1_2/"
BENCH = "analysis/meoh_plant_benchmark_2026_10_06/"
PRUNE = "analysis/meoh_pruning_2026_10_06/"
S6R = "analysis/meoh_s6_robustness_2026_10_13/"
STATS6 = S6R + "stats_s6/"
IDEF = "analysis/meoh_inlet_definition_2026_10_12/"
CONV6 = "analysis/verify_2026_10_12_s6_conversion/"
# since 2026-10-16 the methanol Extended Data figures (2, 3 and 8) show the combined set of both extractions
# (81 groups, 50 papers): analysis/meoh_field_pooled_2026_10_15 and its robustness/ reruns (same scripts, same formats)
POOL = "analysis/meoh_field_pooled_2026_10_15/"
CMB = POOL + "robustness/"
STATS6_C, STATS5_C = CMB + "stats_s6/", CMB + "stats_s5/"
PRUNE_C = CMB + "pruning/"
IDEF_C = CMB + "inlet_definition/"
PURGE_C = CMB + "purge_boundary/purge_boundary_"


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
    b["reference_set"] = b.reference_set.map({"TOTAL themecat": "TheMeCat", "TOTAL suvarna": "Suvarna",
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
    assert len(out["a"][0]) == 137 and len(out["c"][0]) == s["extended_with_usgs_prices"]["feasible"]
    assert int(out["c"][0].below_Fe.sum()) == s["extended_with_usgs_prices"]["below_Fe"]
    return out, fe


# ------------------------------------------------------------------ ED Fig. 3: methanol robustness --------------
# Both loops of the revised manuscript: the inert-limited loop (primary; reactor-inlet CH4 + CO + N2 <= 6.86 %, frozen
# column cost_recycled_opt_inlet) and the loop without the limit (frozen column cost_recycled_opt).
LOOPS = (("inlet_limited", "inert-limited loop", STATS6_C), ("no_limit", "no limit", STATS5_C))


def bootstrap_distribution(stats=STATS):
    """Re-draws the paper-cluster bootstrap of run_main_result_stats.py (same seed, same sequence of draws)."""
    st = rjson(stats + "summary.json")
    gp = rcsv(stats + "group_noise_probabilities.csv")
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


def robustness_checks():
    """Leader changes under every robustness check of the methanol paragraph, in both loops (combined 81 groups)."""
    pl = rjson(POOL + "summary.json")
    ss = rjson(CMB + "selectivity_split/selectivity_split.json")
    cc = rjson(CMB + "catalyst_cost/catalyst_cost.json")
    ae = rjson(CMB + "all_entries/summary.json")
    conv6 = rjson(CMB + "conversion_s6/s6_conversion_summary.json")["scenarios"]["printed|cost_f0.95"]
    conv5 = rjson(CMB + "conversion_s5/conversion_sensitivity_summary.json")["scenarios"]["printed|cost_f0.95"]

    def fr(d):
        return d["groups"], d["disagreements"], d["gt5pct"]

    def sm(d):
        gt5 = d["regret_bins"]["gt5pct"]["groups"] if "regret_bins" in d else d["gt5pct"]
        return d["groups"], d["top1_mismatch_groups"], gt5

    checks = [
        ("as published", "primary", fr(pl["S6"]["primary"]), fr(pl["S5"]["primary"]), POOL + "summary.json (S6/S5.primary)"),
        ("without the study\nwith most comparisons", "without_bansode", fr(pl["S6"]["without_bansode"]),
         fr(pl["S5"]["without_bansode"]), POOL + "summary.json (S6/S5.without_bansode)"),
        ("plot-read entries\nadded", "all_entries", fr(ae["S6"]["combined"]), fr(ae["S5"]["combined"]),
         CMB + "all_entries/summary.json (S6/S5.combined)"),
        ("products close to\nMeOH, CO, CH$_4$", "closure_ge95", fr(pl["S6"]["closure_ge95"]),
         fr(pl["S5"]["closure_ge95"]), POOL + "summary.json (S6/S5.closure_ge95)"),
        ("unreported split:\nall CO", "split_all_CO", fr(ss["S6"]["low"]), fr(ss["S5"]["low"]),
         CMB + "selectivity_split/selectivity_split.json (S6/S5.low)"),
        ("unreported split:\nall CH$_4$", "split_all_CH4", fr(ss["S6"]["high"]), fr(ss["S5"]["high"]),
         CMB + "selectivity_split/selectivity_split.json (S6/S5.high)"),
        ("recycled CO\nas inert", "inert_co", fr(pl["S6"]["inert_co"]), fr(pl["S5"]["inert_co"]),
         POOL + "summary.json (S6/S5.inert_co)"),
        ("catalyst priced\nfrom composition", "catalyst_priced", fr(cc["S6"]["variants"]["composition_3y"]),
         fr(cc["S5"]["variants"]["composition_3y"]), CMB + "catalyst_cost/catalyst_cost.json (S6/S5.variants.composition_3y)"),
        ("more catalyst,\nconversion raised", "conversion_raised", sm(conv6), sm(conv5),
         CMB + "conversion_s6/s6_conversion_summary.json / conversion_s5/conversion_sensitivity_summary.json "
         "(printed|cost_f0.95)"),
    ]
    rows = []
    for label, key, s6, s5, src in checks:
        for loop, (g, d, h) in (("inlet_limited", s6), ("no_limit", s5)):
            rows.append(dict(check=label.replace("\n", " ").replace("$_4$", "4"), label=label, key=key, loop=loop,
                             groups=int(g), disagreements=int(d), regret_gt5pct=int(h), fraction=d / g, source=src))
    t = pd.DataFrame(rows)
    v = t.set_index(["key", "loop"])
    assert tuple(v.loc[("primary", "inlet_limited"), ["groups", "disagreements", "regret_gt5pct"]]) == (81, 50, 42)
    assert tuple(v.loc[("primary", "no_limit"), ["disagreements", "regret_gt5pct"]]) == (25, 10)
    assert tuple(v.loc[("conversion_raised", "inlet_limited"), ["disagreements", "regret_gt5pct"]]) == (46, 36)
    assert tuple(v.loc[("all_entries", "inlet_limited"), ["groups", "disagreements"]]) == (160, 101)
    assert tuple(v.loc[("without_bansode", "inlet_limited"), ["groups", "disagreements", "regret_gt5pct"]]) == (73, 43, 37)
    return t


def near_infeasible_classes():
    """PR #69 near-infeasibility rule on the combined candidate table (run_frozen_columns.near_infeasibility)."""
    import sys
    sys.path.insert(0, path(S6R))
    import run_frozen_columns as F
    c = rcsv(POOL + "pooled_candidates.csv")
    c["other_products"] = c.other_products.astype(str).str.lower().isin(["true", "1"])
    gm, _ = F.treatment(c, "S6")
    groups, _ = F.near_infeasibility(c, gm)
    return groups.set_index("group").cls


def edfig3():
    parts = {}
    for loop, name, stats in LOOPS:
        boot, st = bootstrap_distribution(stats)
        parts[loop] = (boot, st, name, stats)
    st0 = parts["no_limit"][1]
    assert all(p[1]["groups"] == st0["groups"] and p[1]["papers"] == st0["papers"] for p in parts.values())
    edges = np.arange(0.0, 1.0001, 0.02)
    a = pd.DataFrame({"bin_low_fraction": edges[:-1], "bin_high_fraction": edges[1:]})
    for loop, (boot, st, name, _) in parts.items():
        a["resamples_" + loop] = np.histogram(boot, bins=edges)[0]
        a.attrs[loop] = dict(name=name, point=st["point_estimate"]["fraction"],
                             mismatched=st["point_estimate"]["groups"], ci=st["cluster_bootstrap"]["fraction_ci95"])
    a.attrs["n"] = st0["cluster_bootstrap"]["resamples"]
    a.attrs["groups"] = st0["groups"]
    a.attrs["papers"] = st0["papers"]
    b = None
    for loop, (_, _, _, stats) in parts.items():
        cur = rcsv(stats + "regret_threshold_curve.csv")[["threshold", "groups", "papers"]]
        cur = cur.rename(columns={"groups": "groups_" + loop, "papers": "papers_" + loop})
        b = cur if b is None else b.merge(cur, on="threshold", validate="one_to_one")
    rows = []
    labels = {"meas_k1": "re-measured, error x1", "meas_k2": "re-measured, error x2", "meas_k4": "re-measured, error x4"}
    for loop, (_, st, name, _) in parts.items():
        for k, lab in labels.items():
            v = st["noise"][k]
            rows.append(dict(loop=loop, scenario=k, label=lab, observed=st["point_estimate"]["groups"],
                             mismatch_groups_mean=v["mismatch_groups_mean"],
                             mismatch_groups_q025=v["mismatch_groups_q025_q975"][0],
                             mismatch_groups_q975=v["mismatch_groups_q025_q975"][1],
                             noise_floor_mean=v["sty_leader_differs_from_reported_mean"],
                             noise_floor_q025=v["sty_leader_differs_from_reported_q025_q975"][0],
                             noise_floor_q975=v["sty_leader_differs_from_reported_q025_q975"][1],
                             robust_ge90pct=v["observed_mismatches_kept_in_ge_90pct"]))
    c = pd.DataFrame(rows)
    c.attrs["draws"] = st0["noise_model"]["draws"]
    c.attrs["groups"] = st0["groups"]
    cls = near_infeasible_classes()
    d = []
    for loop, (_, st, name, stats) in parts.items():
        gp = rcsv(stats + "group_noise_probabilities.csv")
        m = gp[gp.observed_mismatch.astype(str) == "True"].copy()
        m = m.sort_values(["p_mismatch_meas_k1", "observed_regret"], ascending=False).reset_index(drop=True)
        m.insert(0, "loop", loop)
        m["near_infeasible"] = (m.group.map(cls) == "near-infeasible") if loop == "inlet_limited" else False
        kept = st["noise"]["meas_k1"]["observed_mismatches_kept_in_ge_90pct"]
        assert int((m.p_mismatch_meas_k1 >= 0.9).sum()) == kept
        d.append(m[["loop", "group", "doi", "observed_regret", "p_mismatch_meas_k1", "p_mismatch_meas_k2",
                    "p_mismatch_meas_k4", "near_infeasible"]])
    d = pd.concat(d, ignore_index=True)
    s6 = d[d.loop == "inlet_limited"]
    assert int(s6.near_infeasible.sum()) == 26 and int((s6.near_infeasible & (s6.p_mismatch_meas_k1 >= 0.9)).sum()) == 26
    e = robustness_checks()
    return {"a": (a, "%sgroup_noise_probabilities.csv and %sgroup_noise_probabilities.csv (observed_mismatch, doi) "
                  "re-drawn with the seed and resample count of each summary.json; 95 %% CIs checked against "
                  "summary.json" % (STATS6_C, STATS5_C)),
            "b": (b, STATS6_C + "regret_threshold_curve.csv, " + STATS5_C + "regret_threshold_curve.csv"),
            "c": (c, STATS6_C + "summary.json, " + STATS5_C + "summary.json (noise.*)"),
            "d": (d, STATS6_C + "group_noise_probabilities.csv, " + STATS5_C + "group_noise_probabilities.csv "
                  "(observed_mismatch == True); near-infeasible: PR #69 rule on " + POOL + "pooled_candidates.csv"),
            "e": (e, "see column source")}


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
    rows = [("benchmark (pure-Ru bed)", "Ru_base", sm["base_reproduced"]["P_Fe_cheaper"]),
            ("A: u and r on the price, benchmark bed (Fig. 3d reading)", "Ru_A", sm["A"]["P_Fe_cheaper"]),
            ("A_bed: u and r, commercial Ru/C bed", "Ru_A_bed", sm["A_bed"]["P_Fe_cheaper"]),
            ("B: measured Ru catalysts, 90-95.6 % recovery", "Ru_B", sm["B"]["P_Fe_cheaper"]),
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
    w_edges = np.linspace(sm["ranges"]["A_bed_Ru_wt_pct"][0], sm["ranges"]["A_bed_Ru_wt_pct"][1], 6)
    b = binned(d.u.to_numpy(), u_edges, "u")
    c = binned(d.r.to_numpy(), r_edges, "r")
    e = binned(d.A_bed_wt_pct.to_numpy(), w_edges, "Ru_wt_pct")
    src = MC + "draws.csv (Ru wins: Ru_A_bed < Fe, or Ru_A < Fe)"
    return {"a": (a, MC + "summary.json (P_Fe_cheaper), checked against " + MC + "draws.csv"),
            "b": (b, src + "; 8 log-spaced bins of u over the drawn range"),
            "c": (c, src + "; 8 bins of r over the drawn range"),
            "d": (e, src + "; 5 bins of the drawn A_bed Ru content (A_bed_wt_pct)")}


# ------------------------------------------------------------------ ED Fig. 6: methanol plant benchmark ---------
def pf_cost_terms():
    """Perez-Fortes 2016 at its own point, prices, catalyst charge and finance, split into the stoichiometric feed
    (3 H2 and 1 CO2 per MeOH at the study's prices; the same for every catalyst) and the catalyst-sensitive terms (feed
    above stoichiometry, compression electricity, catalyst replacement, capital), from the independent accounting of
    analysis/review_pf_benchmark_2026_10_09/pf_benchmark_audit.py (molecular weights read from the model source). The
    harmonized total puts the reference fixed operating cost (FCP 24.57 EUR/t) on the model side; the model's own fixed
    O&M is reported separately and is not part of that total."""
    import sys
    sys.path.insert(0, path("analysis/review_pf_benchmark_2026_10_09"))
    import pf_benchmark_audit as PA
    from pathlib import Path as _P
    b = _P(path(BENCH))
    summ = json.loads((b / "summary.json").read_text(encoding="utf-8"))
    report, terms = PA.calculate(PA.rows(b / "reconciliation_cost.csv"), PA.ref_values(PA.rows(b / "reference_values.csv")),
                                 summ["perez_fortes_primary"], float(summ["perez_fortes_like_for_like_eur_t"]),
                                 PA.plant_pf(PA.rows(b / "reconciliation_plant.csv")), PA.weight_constants(PA.MODEL_PATH))
    assert not report["errors"], report["errors"]
    t = {r["item"]: r for r in terms}
    rc = rcsv(BENCH + "reconciliation_cost.csv")
    pf = rc[rc.case.str.startswith("B3 Perez-Fortes")].set_index("term")
    rows = [("stoichiometric H$_2$ and CO$_2$ (3:1)", "catalyst-independent",
             t["H2 for three H2 per MeOH"]["model_EUR_t"], t["H2 for three H2 per MeOH"]["reference_EUR_t"]),
            ("H$_2$ and CO$_2$ above stoichiometry", "catalyst-sensitive",
             t["H2 expenditure above stoichiometric floor"]["model_EUR_t"]
             + t["CO2 expenditure above stoichiometric floor"]["model_EUR_t"],
             t["H2 expenditure above stoichiometric floor"]["reference_EUR_t"]
             + t["CO2 expenditure above stoichiometric floor"]["reference_EUR_t"]),
            ("electricity (model: compressors; ref.: utilities net)", "catalyst-sensitive",
             t["electricity and utilities"]["model_EUR_t"], t["electricity and utilities"]["reference_EUR_t"]),
            ("catalyst replacement", "catalyst-sensitive",
             t["catalyst replacement"]["model_EUR_t"], t["catalyst replacement"]["reference_EUR_t"]),
            ("capital (8 %, 20 y)", "catalyst-sensitive",
             t["capital annuity"]["model_EUR_t"], t["capital annuity"]["reference_EUR_t"]),
            ("fixed O&M (reference value on both sides)", "accounting",
             t["fixed O&M on published basis"]["model_EUR_t"], t["fixed O&M on published basis"]["reference_EUR_t"])]
    a = pd.DataFrame(rows, columns=["term", "category", "model", "reference"])
    sens = a[a.category == "catalyst-sensitive"][["model", "reference"]].sum()
    tot = a[["model", "reference"]].sum()
    like = pf.loc["TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)"]
    # model side: the terms add up to the harmonized total; reference side: the published NPV = 0 break-even price.
    # The reference terms are derived shares of the variable production cost (raw materials 95.9 %, utilities 2.6 %,
    # consumables 1.5 % of 283 M EUR/a = 642.0 EUR/t, against 641.48 EUR/t in its Table 4) and add up to 724.1.
    assert abs(tot.model - float(like.model)) < 0.06 and abs(tot.reference - float(like.reference)) < 1.0, (tot, like)
    a = pd.concat([a, pd.DataFrame([
        dict(term="catalyst-sensitive subtotal", category="subtotal", model=sens.model, reference=sens.reference),
        dict(term="total (harmonized; ref.: NPV = 0 break-even price)", category="total", model=tot.model,
             reference=float(like.reference))])], ignore_index=True)
    a["deviation_pct"] = 100 * (a.model / a.reference - 1)
    a.attrs["reference_terms_sum"] = float(tot.reference)
    a.attrs["model_own_fixed_om"] = float(pf.loc["fixed O&M", "model"])
    a.attrs["anchor_residual"] = float(pf.loc["residual direct + 10 % of NPC (anchor convention)", "model"])
    a.attrs["breakeven_basis"] = str(like.ref_basis)
    return a


def edfig6():
    rc = rcsv(BENCH + "reconciliation_cost.csv")
    a = pf_cost_terms()
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
    sj = rjson(CMB + "plant_variants/sensitivity_summary.json")   # 81 combined groups (2026-10-17)
    ss = sj["variants"]
    d = pd.DataFrame([dict(variant=k, mismatch_groups=v["top1_mismatch_groups"], groups=v["groups"],
                           papers_with_mismatch=v["papers_with_mismatch"],
                           regret_median_mismatched=v["regret_median_mismatched"],
                           knobs=json.dumps(v.get("knobs", {}))) for k, v in ss.items() if "|" not in k])  # loop without the limit; the "|S6" variants are reported in the text
    d.attrs["pf_alignment"] = sj.get("pf_alignment", {})
    d = d.sort_values("mismatch_groups", kind="stable").reset_index(drop=True)
    d.insert(0, "key", np.arange(1, len(d) + 1))
    return {"a": (a, BENCH + "reconciliation_cost.csv (case B3 Perez-Fortes 2016), split by "
                  "analysis/review_pf_benchmark_2026_10_09/pf_benchmark_audit.py"),
            "b": (b, BENCH + "reconciliation_cost.csv (TOTAL and like-for-like rows)"),
            "c": (c, BENCH + "summary.json (model_cases M7) and reference_values.csv (ref_id PEREZFORTES16)"),
            "d": (d, CMB + "plant_variants/sensitivity_summary.json (variants)")}


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
    cb = rcsv(PRUNE_C + "candidate_bounds.csv")
    gp = rcsv(PRUNE_C + "group_pruning.csv").set_index("group")
    sm = rjson(PRUNE_C + "summary.json")
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
    assert int(al.pruned.sum()) == 1399 == len(al) - 296 and len(al) == s["costed_with_frozen_or_usgs_prices"]
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
    return {"a": (a, PRUNE_C + "candidate_bounds.csv; evaluated/excluded re-derived with the agent rule of "
                  "run_meoh_pruning.py and checked per group against group_pruning.csv"),
            "b": (c, ALLOY + " (lower_bound_USD_t, cost_USD_t, pruned); Fe " + ALLOY_SUM),
            "c": (d, PRUNE_C + "summary.json, " + ALLOY_SUM + " (pruning) and " + ALLOY)}, fe


# ------------------------------------------------------------------ ED Fig. 8: purge optimum and inlet composition
PURGE_TREATMENTS = (("canonical", "no limit: purge grid 0.5–40 %"),
                    ("extended", "no limit, purge grid extended to 10$^{-4}$ %"),
                    ("limit_published_max", "inlet ≤ %.2f %% (highest published design)"),
                    ("limit_anchor", "inlet ≤ %.2f %% (the cost model's anchor loop)"),
                    ("limit_published_min", "inlet ≤ %.2f %% (lowest published design)"))


def definition_sweep_table(sm):
    """Comparisons whose STY leader is not the plant-cost leader against the limit on the reactor-inlet fraction, when
    the limit counts CH4 + CO + N2 (the frozen definition) or CH4 + N2 only (analysis/meoh_inlet_definition_2026_10_12,
    definition_scan.csv), with the loop without a limit on the frozen purge grid and on the grid extended to 1e-4 %
    (purge_boundary_summary.json). Checked against the frozen limit sweep of the literature summary."""
    t = rcsv(IDEF_C + "definition_scan.csv")
    t = t[t.limit_pct != "none"].copy()
    t["limit"] = (t.limit_pct.astype(float) / 100.0).round(6)
    t["definition"] = t.definition.map({"frozen": "CH4 + CO + N2", "true_inert": "CH4 + N2"})
    t["order"] = (t.definition == "CH4 + N2").astype(int)
    t = t.sort_values(["order", "limit"])[["definition", "limit", "groups", "different_leader", "fraction", "gt5pct",
                                           "near_infeasible", "papers_with_disagreement"]].reset_index(drop=True)
    pl = rjson(POOL + "summary.json")
    sweep = rjson(CMB + "summary.json")["2_inlet"]["combined"]["sweep"]
    fr = t[t.definition == "CH4 + CO + N2"].set_index("limit")
    for key, v in sweep.items():
        if key != "none":
            assert "%d/%d" % tuple(fr.loc[round(float(key) / 100.0, 6), ["different_leader", "groups"]]) == v["disagreements"], key
    r6 = fr[np.isclose(fr.index, 0.0686)].iloc[0]
    p6, p = pl["S6"]["primary"], pl["S5"]["primary"]
    assert (r6.different_leader, r6.gt5pct) == (p6["disagreements"], p6["gt5pct"])
    none = rcsv(IDEF_C + "definition_scan.csv").query("limit_pct == 'none'").iloc[0]
    x = sm["boundary"]["scored"]
    assert (none.different_leader, none.gt5pct) == (p["disagreements"], p["gt5pct"])
    t = pd.concat([t, pd.DataFrame([
        dict(definition="no limit, purge grid 0.5–40 %", limit=np.nan, groups=p["groups"],
             different_leader=p["disagreements"], fraction=p["fraction"], gt5pct=p["gt5pct"], near_infeasible=0,
             papers_with_disagreement=p["papers_with_disagreement"]),
        dict(definition="no limit, purge grid from 1e-4 %", limit=np.nan, groups=x["groups"],
             different_leader=x["top1_mismatch_groups"], fraction=x["top1_mismatch_fraction"],
             gt5pct=x["regret_bins"]["gt5pct"]["groups"], near_infeasible=0,
             papers_with_disagreement=x["papers_with_mismatch"])])], ignore_index=True)
    t.attrs["anchor"] = sm["limits"]["anchor"]
    t.attrs["published"] = (sm["limits"]["published_min"], sm["limits"]["published_max"],
                            len(sm["published_inlet_non_h2co2_pct"]))
    return t


def edfig8():
    """Purge-boundary test and inlet-constrained optimization (run_purge_boundary.py): cost and inlet composition along
    the extended purge grid for every scored entry; purge, recycle ratio and inlet CO / CH4 / N2 at the optimum of each
    treatment; comparisons with a different winner against the inlet limit for both definitions of the limited
    species (analysis/meoh_inlet_definition_2026_10_12)."""
    src = PURGE_C
    sm = rjson(src + "summary.json")
    ent = rcsv(src + "entries.csv")
    cur = rcsv(src + "curves.csv")
    assert len(ent) == sm["entries"] and cur.i.nunique() == len(ent)
    lim = sm["limits"]
    label = {k: (t % (100 * lim[k[6:]]) if k.startswith("limit_") else t) for k, t in PURGE_TREATMENTS}
    cur["cost_rel_0p5pct"] = cur.cost_eur_t / ent.cost_at_0p5pct.to_numpy()[cur.i.to_numpy()]
    a = cur[["i", "purge", "cost_eur_t", "cost_rel_0p5pct"]]
    a.attrs["purge_floor"] = sm["grid"]["canonical_floor"]
    b = cur[["i", "purge", "nonreactive", "CO", "CH4", "N2"]].copy()
    b.attrs["published"] = (lim["published_min"], lim["published_max"], len(sm["published_inlet_non_h2co2_pct"]))
    b.attrs["anchor"] = lim["anchor"]
    long = []
    for k, _ in PURGE_TREATMENTS:
        t = pd.DataFrame(dict(treatment=label[k], key=k, i=ent.index, cost_eur_t=ent[k + "_cost"],
                              cost_rel_0p5pct=ent[k + "_cost"] / ent.cost_at_0p5pct, purge=ent[k + "_purge"],
                              recycle_ratio=ent[k + "_recycle_ratio"], nonreactive=ent[k + "_nonreactive"],
                              CO=ent[k + "_CO"], CH4=ent[k + "_CH4"], N2=ent[k + "_N2"]))
        long.append(t)
    long = pd.concat(long, ignore_index=True)
    c = long[["treatment", "key", "i", "purge", "cost_rel_0p5pct", "nonreactive"]]
    d = long[["treatment", "key", "i", "recycle_ratio"]].copy()
    d.attrs["anchor_recycle_ratio"] = sm["anchor_loop"]["recycle_ratio"]
    e = definition_sweep_table(sm)
    f = long.groupby(["key", "treatment"], sort=False)[["CO", "CH4", "N2", "nonreactive"]].mean().reset_index()
    f.attrs["published"] = b.attrs["published"]
    return {"a": (a, src + "curves.csv (cost_eur_t) / " + src + "entries.csv (cost_at_0p5pct)"),
            "b": (b, src + "curves.csv; limits " + src + "summary.json (" + INV + "inlet_inert_literature.csv)"),
            "c": (c, src + "entries.csv (<treatment>_purge)"),
            "d": (d, src + "entries.csv (<treatment>_recycle_ratio); anchor " + src + "summary.json anchor_loop"),
            "e": (e, IDEF_C + "definition_scan.csv (limits 4-30 %); no limit: " + POOL + "summary.json (S5.primary) and "
                  + src + "summary.json (boundary.scored)"),
            "f": (f, src + "entries.csv (<treatment>_CO, _CH4, _N2, _nonreactive), means over the scored entries")}


if __name__ == "__main__":
    for f in (edfig1, edfig3, edfig4, edfig5, edfig6, edfig8):
        r = f()
        print(f.__name__, {k: v[0].shape for k, v in r.items()})
    r, _ = edfig2()
    print("edfig2", {k: v[0].shape for k, v in r.items()})
    r, _ = edfig7()
    print("edfig7", {k: v[0].shape for k, v in r.items()})
