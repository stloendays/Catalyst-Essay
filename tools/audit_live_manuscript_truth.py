"""Audit the current live manuscript against committed scientific sources.

This checker is intentionally section-aware rather than phrase-fragile. It verifies that
current canonical/derived numbers appear in the Results section where they belong,
including the closed strict-scaling x lifecycle reachability result.

Usage:
  python tools/audit_live_manuscript_truth.py [docs/MANUSCRIPT_MAIN_TEXT.md]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/MANUSCRIPT_MAIN_TEXT.md"
RUN = ROOT / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
SUP = ROOT / "analysis/supervisor_2026_09_20"

raw_text = TEXT_PATH.read_text(encoding="utf-8")
text = re.sub(r"\s+", " ", raw_text).replace("−", "-")


def rows(path):
    with open(ROOT / path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def section(heading):
    marker = "### " + heading
    i = raw_text.index(marker)
    j = raw_text.find("\n### ", i + len(marker))
    d = raw_text.find("\n## Discussion", i + len(marker))
    ends = [x for x in (j, d) if x >= 0]
    if not ends:
        j = len(raw_text)
    else:
        j = min(ends)
    return re.sub(r"\s+", " ", raw_text[i:j]).replace("−", "-")


checks = []


def ok(label, condition, detail=""):
    checks.append((label, bool(condition), detail))


def tokens(label, haystack, *needles):
    missing = [n for n in needles if n not in haystack]
    ok(label, not missing, "missing: " + ", ".join(missing) if missing else "")


res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
det = res["deterministic"]
mc = res["monte_carlo"]
bw = res["backward_reachability"]
head = json.loads((RUN / "closure/headline_1_1.json").read_text(encoding="utf-8"))
draws = rows(RUN.relative_to(ROOT) / "closure/mc_draws.csv")
eq = json.loads((SUP / "nh3_ru_price_equalization.json").read_text(encoding="utf-8"))
dec = {r["cost_pool"]: r for r in rows("analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv")}
cmc = json.loads((SUP / "nh3_cost_mc_summary.json").read_text(encoding="utf-8"))
price_sweep = rows("figures/composite/fig2/fig2_ru_price_sweep.csv")
parity = price_sweep[-1]
targets = rows("analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_target_keypoints.csv")
strict_joint = json.loads((ROOT / "analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json").read_text(encoding="utf-8"))
headline = rows("data/manuscript_headline_results_2026-09-20.csv")
regret = {r["system"]: r for r in rows("analysis/nonfigure_upgrades_2026_09_29/decision_regret_summary.csv")}
transfer = {r["system"]: r for r in rows("analysis/nonfigure_upgrades_2026_09_29/pairwise_inversion_index.csv")}
corr_uq = rows("analysis/nonfigure_upgrades_2026_09_29/descriptor_correlation_sensitivity.csv")
stop_eff = json.loads((ROOT / "analysis/nonfigure_upgrades_2026_09_29/agent_stopping_efficiency.json").read_text(encoding="utf-8"))
regret_mc = json.loads((ROOT / "analysis/nonfigure_upgrades_2026_09_29/nh3_cost_mc_regret_summary.json").read_text(encoding="utf-8"))

meoh = {r["candidate"]: r for r in rows("data/meoh/meoh_candidate_ranking_D01v3.csv")}
meoh_prov = json.loads((ROOT / "data/meoh/meoh_candidate_ranking_D01v3_provenance.json").read_text(encoding="utf-8"))
purge = rows("data/meoh/meoh_purge_robustness_D01v3.csv")
meoh_mc = json.loads((ROOT / "analysis/meoh_measurement_mc_2026_10_05/mc_summary.json").read_text(encoding="utf-8"))[
    "sets"]["canonical"]["k=1"]
au = rows("data/rank_preservation_control_v1_1.csv")
semi = {(r["window"], r["stress"]): r for r in rows("data/rank_preservation_semiopen_v1_3_summary.csv")}

panel = rows("data/agent_figure_panel_data_2026-09-13.csv")
comp = rows("data/discover_boundary_c1_decision_components.csv")
orc = {r["metric"]: float(r["value"]) for r in rows("analysis/supervisor_2026_09_20/agent_oracle_summary.csv")}
schema = json.loads((ROOT / "provenance/discover_v1/source_harness/DISCOVER_ACTION_SCHEMA_V1.json").read_text(encoding="utf-8"))


def target(life, recovery):
    return next(
        r for r in targets
        if int(r["catalyst_life_y"]) == life
        and abs(float(r["Ru_recovery_fraction"]) - recovery) < 1e-12
    )


def agent_cell(tier, budget, arm="E"):
    return next(r for r in panel if r["tier"] == tier and r["arm"] == arm and r["budget_CU"] == str(budget))


# ----- Results 1: NH3 ranking -------------------------------------------------
s1 = section("Process and economic evaluation reverse the leading ammonia ranking")
m = det["metals"]
tokens(
    "NH3 ranking/cost anchors in correct section",
    s1,
    f"{m['Fe']['feasible']['total_cost']:.3f}",
    f"{m['Ru']['feasible']['total_cost']:.3f}",
    f"{m['Os']['feasible']['total_cost']:.3f}",
    f"{head['top3_spearman']:.2f}",
    f"{head['top3_kendall']:.2f}",
    f"{det['raw_global_spearman']:.3f}",
)
ok("NH3 atomic top3 source", det["activity_order"][:3] == ["Ru", "Os", "Fe"])
ok("NH3 economic top3 source", det["raw_economic_order"][:3] == ["Fe", "Ru", "Os"])
tokens(
    "NH3 decision regret in ranking section",
    s1,
    "44.1%",
)
ok(
    "NH3 decision regret source",
    abs(float(regret["NH3"]["normalized_decision_regret"]) - 0.44068926608899806) < 1e-12,
)

# ----- Results 2: price/process/uncertainty ----------------------------------
s2 = section("Metal price and process optimization jointly determine the Fe-Ru ranking")
fe = m["Fe"]["feasible"]
ru = m["Ru"]["feasible"]
r8 = eq["Ru_price_equalized_to_Fe"]
gap = float(dec["TOTAL"]["Ru_minus_Fe_USD_t"])
fe_win = sum(r["economic_winner"] == "Fe" for r in draws)
tokens(
    "NH3 operating/equal-price anchors",
    s2,
    "425 °C",
    "180 bar",
    "450 °C",
    "425 bar",
    "8 US dollars per kilogram",
    f"{r8['total_cost_USD_t']:.3f}",
    f"{-eq['Ru_minus_Fe_USD_t']:.3f}",
    f"{float(parity['price_USD_kg']):.2f}",
    "6.24 m³",
)
tokens(
    "NH3 canonical cost-gap decomposition",
    s2,
    f"{gap:.3f}",
    f"+{float(dec['fresh_compression_electricity']['Ru_minus_Fe_USD_t']):.3f}",
    f"+{float(dec['metal_inventory']['Ru_minus_Fe_USD_t']):.3f}",
    f"+{float(dec['compressor_CAPEX']['Ru_minus_Fe_USD_t']):.3f}",
    f"+{float(dec['refrigeration_electricity']['Ru_minus_Fe_USD_t']):.3f}",
)
tokens(
    "NH3 descriptor uncertainty semantics",
    s2,
    f"{100*mc['Fe_feasibility_probability']:.1f}%",
    f"{100*fe_win/len(draws):.1f}%",
    f"({fe_win}/{len(draws)})",
    f"{100*mc['top3_actionable']:.1f}%",
    f"{100*mc['top1_survival']:.1f}%",
)
v = cmc["full_14136_state_direct_cost_verification"]
a = cmc["alpha_star"]
tokens(
    "NH3 cost-MC and parity-target distribution",
    s2,
    f"{cmc['draws']:,}",
    f"{v['P_C_Fe_lt_C_Ru']:.3f}",
    f"{v['minimum_Ru_minus_Fe_USD_t']:.3f}",
    f"{a['p05']:.2f}-fold",
    f"{a['p50']:.2f}-fold",
    f"{a['p95']:.2f}-fold",
)
rq = regret_mc["regret_quantiles"]
tokens(
    "NH3 cost-MC decision-regret distribution",
    s2,
    f"{100*rq['p05']:.2f}%",
    f"{100*rq['p50']:.2f}%",
    f"{100*rq['p95']:.2f}%",
    "all 5,000 draws",
)
ok(
    "NH3 regret MC source",
    regret_mc["draws"] == 5000
    and regret_mc["P_regret_gt_0"] == 1.0
    and abs(rq["p05"] - 0.30479402441495995) < 1e-12
    and abs(rq["p50"] - 0.4088909107436396) < 1e-12
    and abs(rq["p95"] - 0.5425375993576715) < 1e-12,
)
rho0 = next(r for r in corr_uq if abs(float(r["latent_pairwise_correlation"]) - 0.0) < 1e-12)
rho9 = next(r for r in corr_uq if abs(float(r["latent_pairwise_correlation"]) - 0.9) < 1e-12)
tokens(
    "NH3 descriptor error-dependence sensitivity",
    s2,
    "21.7%",
    "10.7%",
    "Gaussian copula",
    "common-offset",
)
ok(
    "NH3 copula Fe-top1 anchors",
    abs(float(rho0["P_atomic_top1_Fe"]) - 0.10707) < 1e-8
    and abs(float(rho9["P_atomic_top1_Fe"]) - 0.21678) < 1e-8,
)

# ----- Results 3: backward target and reachability ----------------------------
s3 = section("Backward design separates the required catalyst-property region from physical reachability")
tokens(
    "NH3 activity-only backward/reachability anchors",
    s3,
    f"{bw['Ru_activity_break_even_multiplier']:.2f}-fold",
    f"{bw['Ru_scaling_max_gain_673K']:.3f}-fold",
    f"{bw['Ru_scaling_max_gain_all_states']:.3f}-fold",
    f"{bw['Ru_best_scaling_cost_USD_t']:.3f}",
    f"{bw['Ru_best_scaling_EN_eV']:.3f}",
    f"{a['p05']:.2f}-fold",
    f"{float(parity['price_USD_kg']):.2f}",
    "53,852.5",
    "99.70%",
    "99.39%",
    "32.9-year",
)
t10 = float(target(10, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t15 = float(target(15, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20 = float(target(20, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20r98 = float(target(20, 0.98)["certified_upper_bound_required_direct_activity_multiplier"])
tokens(
    "NH3 joint backward target region",
    s3,
    f"{t10:.3f}-fold",
    f"{t15:.3f}-fold",
    f"{t20:.3f}-fold",
    "20-year lifetime with 98% recovery",
)
ok("joint target ordering", t20 < t15 < t10)
ok("20y/98 target equals 10y/99 within audit", abs(t20r98 - t10) < 1e-9)
tokens(
    "NH3 strict-scaling lifecycle closure",
    s3,
    "4.4068",
    "15.362",
    "0.071",
    "99.119%",
    "22.69-year",
    "-1.230",
)
ok(
    "strict-scaling tested lifecycle box remains outside parity",
    strict_joint["tested_lifecycle_envelope"]["intersects_strict_scaling_manifold"] is False,
)
ok(
    "strict-scaling headline table promoted",
    any(
        r["metric"] == "strict_scaling_lifecycle_joint_reachability"
        and r["value"] == "NO_INTERSECTION_WITHIN_TESTED_BOX"
        for r in headline
    ),
)
ok(
    "strict-scaling lifecycle audit scripts present",
    (ROOT / "analysis/fe_bridge_backward_2026_09_29/run_statewise_strict_scaling_lifecycle.py").exists()
    and (ROOT / "analysis/fe_bridge_backward_2026_09_29/run_exact_scaling_lifecycle_surface.py").exists(),
)

# ----- Results 4: methanol ----------------------------------------------------
s4 = section("Selectivity, recycle and purge reshape the methanol ranking")
econ_order = sorted(meoh, key=lambda k: int(meoh[k]["economic_rank"]))
npc = [round(float(meoh[k]["NPC_EUR_t_2pct_purge"])) for k in econ_order]
sty_metric = meoh_prov["metrics"]["STY_per_gRe (intrinsic productivity, reaction-case atomic_rank)"]
c55 = meoh["5 wt% Re | 250 C"]
tokens(
    "MeOH canonical ranking/economics",
    s4,
    "2% purge",
    *(f"{x:,}" for x in npc),
    f"{sty_metric['spearman']:.2f}",
    f"{sty_metric['kendall']:.2f}",
    "two of six",
)
tokens(
    "MeOH leverage/purge robustness",
    s4,
    f"{float(c55['L_CH4_suppression']):.5f}",
    f"{float(c55['L_conversion']):.5f}",
    f"{float(c55['L_STY']):.5f}",
    f"{len(purge)}",
    f"{100*min(float(r['purge']) for r in purge):.1f}%",
    f"{round(100*max(float(r['purge']) for r in purge))}%",
    f"{max(float(r['spearman']) for r in purge):.2f}",
)
ok("MeOH at least one inversion across purge", min(int(r["pairwise_inversions"]) for r in purge) == 1)
tokens("MeOH decision regret", s4, "1.93%")
tokens(
    "MeOH measurement Monte Carlo",
    s4,
    "5,000",
    f"{round(meoh_mc['P_winner_stays_first'] * 5000):,}",
    f"{100 * meoh_mc['P_winner_stays_first']:.1f}%",
    f"{round(meoh_mc['second_vs_third']['P_inverted'] * 5000):,}",
    f"{100 * meoh_mc['second_vs_third']['P_inverted']:.1f}%",
    f"{round(meoh_mc['P_upstream_winner_1wtRe_250C_economic_first'] * 5000)}",
)
ok("MeOH measurement MC: last place fixed", meoh_mc["rank_probability"]["5wtRe_250C"][3] == 1.0)
ok(
    "MeOH regret source",
    abs(float(regret["MeOH"]["normalized_decision_regret"]) - 0.019304569066044774) < 1e-12,
)

# ----- Results 5: rank-preservation control ----------------------------------
s5 = section("Catalyst effects on process operation determine whether rankings change")
p1 = semi[("primary_273_293K", "moderate")]
p2 = semi[("sensitivity_273_313K", "moderate")]
tokens(
    "Au/TiO2 rank-preservation anchors",
    s5,
    "2 > 3 > 4 > 5 > 6 nm",
    "1.000",
    "10,000",
    f"{100*float(p1['full_preservation_fraction']):.2f}%",
    str(p1["mean_spearman_rho"]),
    f"{100*float(p2['full_preservation_fraction']):.2f}%",
    str(p2["mean_spearman_rho"]),
)
ok(
    "Au activity monotone",
    all(
        float(a["mass_activity_umol_CO_gcat_s"]) > float(b["mass_activity_umol_CO_gcat_s"])
        for a, b in zip(au, au[1:])
    ),
)
tokens("Au zero decision regret", s5, "zero selection regret")
ok("Au regret source", float(regret["AuTiO2"]["normalized_decision_regret"]) == 0.0)

# ----- Results 6: Agent -------------------------------------------------------
s6 = section("Adaptive calculation selection makes the multiscale analysis repeatedly executable")
s75 = agent_cell("strong", 75)
s50 = agent_cell("strong", 50)
tokens(
    "Agent compute-budget anchors",
    s6,
    "11 predefined calculations",
    f"{int(orc['D_threshold_CU'])} compute units",
    f"{s75['k_complete_decision']}/{s75['n']}",
    "75-CU",
    f"{s75['decision_stable_CU_median']} CU",
    f"{s50['k_complete_decision']}/{s50['n']}",
    "50 CU",
    "5,000-CU",
    f"{int(orc['nonbinding_stable_CU'])} CU",
    f"{int(orc['nonbinding_overrun_CU'])} CU",
    f"{int(orc['nonbinding_final_CU'])} CU",
)
ok("Agent interface source has 11 actions", len(schema["actions"]) == 11)
c50 = next(r for r in comp if r["tier"] == "strong" and r["arm"] == "E" and r["budget_CU"] == "50")
ok("Agent winner/pair 20/20 at 50 CU", c50["k_winner"] == c50["k_pair"] == c50["n"] == "20")
tokens(
    "Agent nonbinding stopping diagnostic",
    s6,
    "14/20",
    "8,207",
    "17,535",
    "46.8%",
)
ok(
    "Agent post-stability source",
    stop_eff["runs_with_positive_overrun"] == 14
    and stop_eff["total_post_stability_overrun_CU"] == 8207
    and abs(stop_eff["fraction_total_compute_after_hindsight_stability"] - 0.46803535785571715) < 1e-12,
)

# ----- Discussion / Methods semantic locks ------------------------------------
discussion = raw_text[raw_text.index("## Discussion"):raw_text.index("## Methods")]
methods = raw_text[raw_text.index("## Methods"):]
tokens(
    "pairwise transfer-index interpretation",
    discussion,
    "χ_AB",
    "+0.085",
    "+0.015",
    "-1.00",
)
ok(
    "pairwise transfer-index source signs",
    float(transfer["NH3"]["pairwise_transfer_index_chi"]) > 0
    and float(transfer["MeOH"]["pairwise_transfer_index_chi"]) > 0
    and float(transfer["AuTiO2"]["pairwise_transfer_index_chi"]) < 0,
)
tokens(  # wording of the 2026-09-30 scope framing: the objective holds only catalyst-responsive terms
    "NH3 reduced-cost scope lock",
    methods,
    "the economic objective contains the terms that respond directly to catalyst identity",
    "Common upstream H₂/N₂ supply contributions are held fixed",
)
tokens(
    "NH3 draw-level cost-MC reconstruction lock",
    methods,
    "complete draw sequence has been reconstructed",
    "(C_Ru-C_Fe)/C_Fe",
)
ok(
    "no stale pending joint-reachability language",
    "Strict scaling-consistent joint reachability is not yet promoted" not in raw_text
    and "PENDING_EXACT_CACHE_SWEEP" not in raw_text,
)

# ----- 2026-10-05 additions: actual Ru catalyst cost, literature gains, methanol backward design --------------
ac = {r["key"]: r for r in rows("figures/composite/fig2/fig2_ru_actual_cost_points.csv")}
tokens(
    "NH3 actual-catalyst cost (Fig. 2d)",
    s2,
    "11%",
    f"{float(ac['supp_rec94']['p_eff_USD_kg']):.0f}–{float(ac['supp_rec90']['p_eff_USD_kg']):.0f}",
    f"{float(ac['supp_rec94']['cost']):.2f}–{float(ac['supp_rec90']['cost']):.2f}",
    f"{float(ac['supp_rec94']['gap_to_Fe']):.2f}–{float(ac['supp_rec90']['gap_to_Fe']):.2f}",
    f"{float(ac['supp_rec94']['alpha_star']):.1f}–{float(ac['supp_rec90']['alpha_star']):.1f}-fold",
    f"{float(ac['kaap94']['cost']):.2f}–{float(ac['kaap90']['cost']):.2f}",
    f"{float(ac['fe_kaap']['cost']):.2f}",
)
ok("NH3 actual-catalyst: Ru/C with recovery below Fe in the KAAP loop",
   float(ac["kaap90"]["cost"]) < float(ac["fe_kaap"]["cost"]) and float(ac["kaap94"]["cost"]) < float(ac["fe_kaap"]["cost"]))
lit = {r["id"]: r for r in rows("analysis/promoted_ru_literature_2026_10_05/fig3_literature_points.csv")}
tokens(
    "NH3 literature activity gains (Fig. 3a)",
    s3,
    f"{float(lit['P01']['factor_low']):.0f}- and {float(lit['P02']['factor_low']):.0f}-fold",
    f"more than {float(lit['P03']['factor_high']):.0f}-fold at 5 MPa",
    f"more than {float(lit['P04']['factor_high']):.0f}-fold",
    f"{float(lit['E01']['factor_low']):.1f}-fold",
    f"{float(lit['E10']['factor_low']):.1f}-fold",
    f"{float(lit['E09']['factor_low']):.1f}-fold",
    f"{float(lit['C01']['factor_low']):.1f}-fold",
)
mcb = json.loads((ROOT / "analysis/meoh_counterfactual_backward_2026_10_05/summary.json").read_text(encoding="utf-8"))
cf = {r["case"].split(" (")[0]: r for r in mcb["counterfactuals"]}
mbw = {r["property"]: r for r in mcb["backward"]}
tokens(
    "MeOH counterfactual and backward design",
    s4,
    f"rho = -{abs(cf['CH4 selectivity removed']['rho']):.2f}",
    f"rho to +{cf['conversion equalized']['rho']:.2f}",
    mbw["STY per g Re (multiplier)"]["note"].split("= ")[1].split(" ")[0],
    f"{float(mbw['single-pass CO2 conversion']['required']):.3f}",
)
ok("MeOH backward: STY alone cannot reach parity", mbw["STY per g Re (multiplier)"]["required"] == "unreachable")

# ----- Report -----------------------------------------------------------------
failed = [(label, detail) for label, passed, detail in checks if not passed]
for label, passed, detail in checks:
    print(("PASS " if passed else "FAIL ") + label + (f" | {detail}" if detail else ""))
print(f"{len(checks)} checks, {len(failed)} failed")
raise SystemExit(1 if failed else 0)
