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


SI_PATH = ROOT / "docs/SUPPLEMENTARY_INFORMATION.md"
raw_si = SI_PATH.read_text(encoding="utf-8") if SI_PATH.exists() else ""


def _block(raw, i, marker):
    j = raw.find("\n### ", i + len(marker))
    d = raw.find("\n## ", i + len(marker))
    ends = [x for x in (j, d) if x >= 0]
    j = min(ends) if ends else len(raw)
    return re.sub(r"\s+", " ", raw[i:j]).replace("−", "-")


def section(heading):
    """The full results of a section: its Supplementary Note when one has that title (the main text keeps a shorter
    version since the 2026-10-07 compression), otherwise the main-text subsection."""
    m = re.search(r"^### Supplementary Note \d+ \| " + re.escape(heading) + r"[ \t]*$", raw_si, re.M)
    if m:
        return _block(raw_si, m.start(), m.group(0))
    marker = "### " + heading
    return _block(raw_text, raw_text.index(marker), marker)


def main_section(heading):
    marker = "### " + heading
    return _block(raw_text, raw_text.index(marker), marker)


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

# ----- Discussion / Methods semantic locks ------------------------------------
discussion = raw_text[raw_text.index("## Discussion"):raw_text.index("## Methods")]
methods = re.sub(r"\s+", " ", raw_text[raw_text.index("## Methods"):]).replace("−", "-")
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
    "(C_Ru - C_Fe)/C_Fe",
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

# ----- Agent scaling: extraction accuracy, self-check, pruning ----------------------------------------------
s6 = section("An automated agent extends the analysis to published and computed catalysts")
ent = {r["doi"]: r for r in rows("agent/extraction/eval/entry_metrics.csv")}
tot = ent["TOTAL"]
src = {(r["source_type"], r["field"]): r for r in rows("agent/extraction/eval/field_accuracy_by_source.csv")}


def n_ok(source, field):
    r = src[(source, field)]
    return f"{r['n_correct_strict']} of {r['n_extracted']}"


ext = json.loads((ROOT / "agent/extraction/eval/summary.json").read_text(encoding="utf-8"))
p18, p31 = ext["precision"]["first18"], ext["precision"]["added31"]
err = ext["errata"]
lit = json.loads((ROOT / "analysis/meoh_literature_inversion_2026_10_05/summary.json").read_text(encoding="utf-8"))
alloy = json.loads((ROOT / "analysis/nh3_alloy_extension_2026_10_05/summary.json").read_text(encoding="utf-8"))
ext_all = alloy["extended_with_usgs_prices"]
tokens(
    "Agent extraction accuracy",
    s6,
    f"{ext['matching']['ambiguous_pairs']} of the {ext['matching']['pairs']} pairs",
    f"{tot['matched']} of the {tot['curated']} curated entries ({float(tot['recall']) * 100:.0f}%)",
    n_ok("table", "X_CO2"), n_ok("table", "S_MeOH"),
    n_ok("SI", "X_CO2"), n_ok("SI", "S_MeOH"), n_ok("SI", "STY"),
    n_ok("plot", "X_CO2"), n_ok("plot", "S_MeOH"),
    f"{p18['precision_all_extracted'] * 100:.0f}% are correct in the first 18 papers",
    f"({p18['unmatched_correct']} of the "
    f"{p18['unmatched_correct'] + p18['unmatched_duplicate'] + p18['unmatched_wrong']} reviewed are correct, "
    f"{p18['unmatched_unreviewed']} are not yet reviewed)",
    f"an estimated {p31['precision_all_extracted'] * 100:.0f}% in the 31 papers added later",
    f"{p31['pooled_sample'].split('/')[0]} of a random {p31['pooled_sample'].split('/')[1]} such entries",
    f"{sum(v['cells'] for v in err['by_reference'].values())} curated cells and {err['rows_dropped']} curated rows",
)
ok("Agent: Gothe Table 4 extracted exactly", ext["gothe"]["matched"] == 21 and ext["gothe"]["X_CO2"] == "21/21")
canon = lit["selfcheck"]["canonical_states"]
tokens(
    "Agent self-check",
    s6,
    "2.3 × 10⁻¹³",
    "943.30, 961.51, 966.96 and 1,258.17",
)
ok("Agent self-check source", lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12
   and sorted(round(v, 2) for v in canon.values()) == [943.3, 961.51, 966.96, 1258.17])
ok("Agent: pure-metal self-check source", all(r["match"] for r in alloy["self_check"]))
gate = json.loads((ROOT / "agent/selfcheck_report.json").read_text(encoding="utf-8"))
au_gate = next(x for x in gate["systems"] if x["system"] == "Au/TiO2")
ok("Agent self-check gate passes for all three systems", gate["pass"] and all(x["pass"] for x in gate["systems"]))
ok("Agent Au/TiO2 extracted inputs reproduce the control", au_gate["extracted"]["pass"]
   and au_gate["extracted"]["envelope"]["full_preservation"] == 1.0 and au_gate["extracted"]["semiopen_windows_compared"] == 6)
tokens("Agent Au/TiO2 self-check", s6, "all three systems", "all 10,000 literature-envelope samples", "six operating-window stress tests")
tokens(
    "Agent pruning",
    s6,
    f"{ext_all['costed']:,} priced bimetallic surfaces",
    f"excludes {ext_all['pruning']['pruned']:,} candidates ({ext_all['pruning']['fraction_saved'] * 100:.1f}%)",
)
ok("Agent pruning: no false exclusion", ext_all["pruning"]["false_prunes"] == [])
mpr = json.loads((ROOT / "analysis/meoh_pruning_2026_10_06/summary.json").read_text(encoding="utf-8"))
mp = mpr["pruning"]["recycled_opt"]
tokens(
    "Agent pruning, methanol",
    s6,
    f"needs the full optimization for {mp['evaluated']} of the {mp['full']} candidates "
    f"({mp['excluded']} excluded, {mp['excluded_fraction'] * 100:.1f}%)",
    f"plant-cost leader of all {mpr['groups']} groups",
    f"median gap {mpr['median_bound_gap_eur_t']['recycled_opt']:.0f} euros per tonne",
)
ok("Agent pruning, methanol: bound valid and no leader missed", mpr["bound_valid_all"] and mp["leader_missed"] == 0)

FE_COST_ALLOY = json.loads((ROOT / "analysis/nh3_alloy_extension_2026_10_05/alloy_backward_summary.json")
                           .read_text(encoding="utf-8"))["Fe_cost_USD_t"]

# ----- NH3 bimetallic surfaces ----------------------------------------------------------------------------------
s7 = section("Bimetallic surfaces that undercut Fe pair a cheap 3d metal with a group-6 metal")
tm = alloy["extended_excluding_sp_and_group3to5"]
glob_below = tm["below_Fe_surfaces"]
anch_below = [x[0] for x in tm["below_Fe_anchored_surfaces"]]
sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
tokens(
    "NH3 alloy screen",
    s7,
    f"{alloy['surfaces_fetched']:,} bimetallic and pure-metal surfaces",
    f"Among the {tm['costed']} surfaces", f"{tm['feasible']} satisfy",
    *[x.translate(sub) for x in glob_below], *[x.translate(sub) for x in anch_below],
    f"ranks {tm['route_global']['upstream_winner_economic_rank']}rd economically",
    f"({tm['route_global']['upstream_winner'].translate(sub)}, {tm['route_global']['regret'] * 100:.1f}% regret)",
    f"{tm['route_anchored']['upstream_winner_economic_rank']}th ({tm['route_anchored']['upstream_winner']}, "
    f"{tm['route_anchored']['regret'] * 100:.1f}%)",
    f"{tm['route_global']['spearman']:.2f} and {tm['route_anchored']['spearman']:.2f}",
)
ok("NH3 alloy: below-Fe family is cheap 3d + group 6", tm["below_Fe_either_route_all_3d_plus_group6"])
ok("NH3 alloy: counts in text match source", len(glob_below) == 5 and len(anch_below) == 6)
abw = {(r["surface"], r["route"]): r for r in rows("analysis/nh3_alloy_extension_2026_10_05/alloy_backward.csv")}
lead_g, lead_a = abw[(tm["route_global"]["upstream_winner"], "global")], abw[(tm["route_anchored"]["upstream_winner"], "anchored")]
cu3cr = abw[("Cu3Cr", "global")]
tokens(
    "NH3 alloy counterfactual and backward design",
    s7,
    f"({float(lead_g['cost_at_Fe_price_USD_t']):.2f} and {float(lead_a['cost_at_Fe_price_USD_t']):.2f} US dollars per tonne)",
    f"{float(lead_g['alpha_star']):.0f}-fold and {float(lead_a['alpha_star']):.0f}-fold",
    f"below {float(lead_g['best_scaling_cost_USD_t']):.2f} and {float(lead_a['best_scaling_cost_USD_t']):.2f} US dollars per tonne",
    f"with {float(cu3cr['alpha_star']) * 100:.0f}% of its activity",
)
ok("NH3 alloy: leaders undercut Fe only at the Fe price",
   float(lead_g["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_g["cost_USD_t"])
   and float(lead_a["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_a["cost_USD_t"]))
ok("NH3 alloy: Cu3Cr and Cu3Mo below Fe in both routes",
   all(abw[(m, r)]["beats_Fe"] == "True" for m in ("Cu3Cr", "Cu3Mo") for r in ("global", "anchored")))

# ----- NH3 actual-catalyst Monte Carlo -------------------------------------------------------------------------
mca = json.loads((ROOT / "analysis/nh3_mc_ru_actual_2026_10_06/summary.json").read_text(encoding="utf-8"))
wa = mca["A_where_Ru_wins"]
s2_full = section("Metal price and process optimization jointly determine the Fe-Ru ranking")
tokens(
    "NH3 actual-catalyst Monte Carlo",
    s2_full,
    f"Fe is cheaper in {mca['A']['P_Fe_cheaper'] * 100:.1f}% of draws when Ru is read at the effective price p(1 - r)/u in the benchmark bed",
    f"and in {mca['A_bed']['P_Fe_cheaper'] * 100:.1f}% when its own Ru content",
    f"Fe is cheaper in {mca['B']['P_Fe_cheaper'] * 100:.1f}% of draws with recovery and {mca['B0']['P_Fe_cheaper'] * 100:.1f}% without",
    f"five of the {mca['ranges']['measured_Ru_catalysts']} catalysts",
)
ok("NH3 actual-catalyst MC: base reproduced", mca["base_reproduced"]["P_Fe_cheaper"] == 1.0
   and abs(mca["base_reproduced"]["min_gap_USD_t"] - 2.382) < 1e-3)
ok("NH3 actual-catalyst MC: five winning measured catalysts", len(mca["B_Ru_winning_catalysts"]) == 5)
mcd_rows = rows("analysis/nh3_mc_ru_actual_2026_10_06/draws.csv")


def _win(sel):
    sub = [r_ for r_ in mcd_rows if sel(r_)]
    return sum(float(r_["Ru_A_bed"]) < float(r_["Fe"]) for r_ in sub) / len(sub)


def _quantiles(values, qs):
    """numpy.quantile's default (linear) interpolation; the audit runs without numpy."""
    v = sorted(values)
    out = []
    for q in qs:
        h_ = (len(v) - 1) * q
        lo = int(h_)
        out.append(v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (h_ - lo))
    return out


_tu = _quantiles([float(r_["u"]) for r_ in mcd_rows], [1 / 3, 2 / 3])
_tr = _quantiles([float(r_["r"]) for r_ in mcd_rows], [1 / 3, 2 / 3])
tokens(
    "NH3 actual-catalyst MC: where Ru wins",
    s2_full,
    f"in {_win(lambda r_: float(r_['u']) < _tu[0]) * 100:.1f}% of draws with u in its lowest tercile",
    f"{_win(lambda r_: float(r_['u']) >= _tu[1] and float(r_['r']) >= _tr[1]) * 100:.0f}% with u and r in their top terciles",
    f"in {_win(lambda r_: float(r_['measured_wt_pct']) < 2.5) * 100:.1f}% of draws below 2.5 wt% Ru",
    f"{_win(lambda r_: float(r_['measured_wt_pct']) >= 5.0) * 100:.0f}% at 5 wt% or more",
)

# ----- NH3 measured catalysts --------------------------------------------------------------------------------
s9 = section("Measured ammonia catalysts rank differently by laboratory rate and by plant cost")
sup = json.loads((ROOT / "analysis/nh3_supported_2026_10_06/summary.json").read_text(encoding="utf-8"))
adj = json.loads((ROOT / "agent/nh3_supported/out/adjudication_summary.json").read_text(encoding="utf-8"))
pm, ov = sup["per_metal"], sup["overall"]
fa = sorted((v for _, v in sup["fused_fe_alpha"]), reverse=True)
sgm = {r["ref"]: r for r in rows("analysis/nh3_supported_2026_10_06/group_metrics.csv")}
tokens(
    "NH3 measured catalysts",
    s9,
    f"the {adj['rows']} catalyst rows", f"agree on {adj['agree']} of {adj['numeric_fields']} numeric fields",
    f"(α = {fa[0]:.2f} and {fa[1]:.2f})",
    f"Of the {sup['primary']} catalysts in the primary set ({pm['Ru']['n']} Ru, {pm['Fe']['n']} Fe, {pm['Co']['n']} Co and {pm['Ni']['n']} Ni)",
    f"costs {ov['rate_leader_cost']:.2f} US dollars per tonne, {ov['regret'] * 100:.0f}% above",
    f"(Spearman ρ = {ov['spearman_rate_vs_cost']:.2f})",
    f"({float(sgm['81']['regret']) * 100:.1f}% and {float(sgm['82']['regret']) * 100:.1f}% regret)",
    f"(lowest {pm['Ru']['cost_min']:.2f} US dollars per tonne)",
    f"with 90% Ru recovery {['zero', 'one', 'two', 'three', 'four'][len(sup['sensitivity']['Ru_recovery90']['below_Fe'])]} do",
)
ok("NH3 measured: no measured catalyst below Fe without recovery (after the primary-paper errata)",
   all(v["below_Fe"] == 0 for v in pm.values()))
errata = rows("agent/nh3_supported/out/primary_errata.csv")
tokens("NH3 measured: errata and Methods row count", text,
       "ten transcription errors in nine rows",
       f"enter the chain: {sup['rows'] - sup['outside']} of {sup['rows']} rows")
ok("NH3 measured: errata file covers nine review rows", len({(r["page"], r["row"]) for r in errata}) == 9,
   f"{len({(r['page'], r['row']) for r in errata})} rows")

# ----- NH3 field statistic (30 primary papers) ------------------------------------------------------------------
fd = json.loads((ROOT / "analysis/nh3_field_2026_10_06/summary.json").read_text(encoding="utf-8"))
fev = json.loads((ROOT / "agent/nh3_field/eval/summary.json").read_text(encoding="utf-8"))
FP, FV = fd["primary"], fd["variants"]
fk = FP["mismatch_kinds"]
fci = FP["bootstrap_papers"]["mismatch_fraction_ci95"]
rate_ev = next(f for f in fev["fields"] if f["field"] == "rate")
_fe_dm = sum(1 for r in rows("analysis/nh3_field_2026_10_06/group_metrics.csv")
             if r["mismatch_kind"] == "different metal" and r["plant_winner"].startswith("Fe"))
tokens(
    "NH3 field statistic",
    s9,
    f"extracted {fd['papers_in_set']} primary ammonia-synthesis papers",
    f"For the {fev['matched']} entries that the review also tabulates",
    f"the rate in {fev['matched'] - rate_ev['extraction_errors']} of {fev['matched']}",
    f"form {FP['groups']} comparisons",
    f"in {FP['top1_mismatch_groups']} of them ({FP['top1_mismatch_fraction'] * 100:.0f}%; 95% confidence interval "
    f"{fci[0] * 100:.0f}–{fci[1] * 100:.0f}% from resampling papers), in {FP['papers_with_mismatch']} of {FP['papers']} papers",
    f"median regret of {FP['regret_median_mismatched'] * 100:.0f}%",
    f"in {fk['different metal']['groups']} comparisons a catalyst of another metal is the plant-cost leader, "
    f"in {_fe_dm} of them an Fe catalyst on the same support",
    f"in {fk['fused-Fe reference vs supported catalyst']['groups']} a commercial fused-iron catalyst",
    f"With 90% Ru recovery the disagreement is {FV['Ru_recovery_90pct']['top1_mismatch_groups']} of {FP['groups']}",
    f"raises it to {FV['per_g_metal_leaderboard']['top1_mismatch_groups']}",
)
_fc = [r for r in rows("analysis/nh3_field_2026_10_06/candidates.csv")
       if r["status"].startswith("primary") and r["cost_USD_t"] and float(r["cost_USD_t"]) < fd["Fe_benchmark_USD_t"]]
ok("NH3 field: every primary catalyst below the Fe benchmark is an iron catalyst",
   bool(_fc) and all(r["metal"] == "Fe" for r in _fc), f"{len(_fc)} below Fe")
ok("NH3 measured: same-support Fe/Ru studies favour Fe on cost",
   all(sgm[k]["same"] == "False" and "Fe" in sgm[k]["plant_leader"] and "Ru" in sgm[k]["rate_leader"] for k in ("81", "82")))
ok("NH3 measured: fused-iron calibration within a factor 2.2", all(0.45 <= v <= 2.2 for v in fa))

# ----- MeOH published leaderboards ------------------------------------------------------------------------------
s8 = section("Published methanol leaderboards and plant-cost leaderboards often disagree")
P0 = lit["primary"]
V = lit["variants"]
mk = json.loads((ROOT / "analysis/meoh_literature_inversion_2026_10_05/mismatch_kinds.json").read_text(encoding="utf-8"))
_inv = [int(x) for x in P0["pairwise_inversions"].split("/")]
_gm = rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics.csv")
_mm = [float(r["regret"]) for r in _gm if r["top1_mismatch"] == "True"]
_dc = mk["different catalyst"]
_sc = mk["same catalyst"]
_share = _dc["groups"] / mk["groups_with_two_or_more_catalysts"] * 100
tokens(
    "MeOH literature leaderboards",
    s8,
    f"{lit['candidates']} operating points", f"from {lit['papers_with_candidates']} studies",
    f"{P0['groups']} comparisons with {P0['entries']} entries",
    f"caps it for {lit['infeasible']['conversion_capped_at_primary_optimum']} entries",
    f"in {P0['top1_mismatch_groups']} of {P0['groups']} comparisons ({P0['top1_mismatch_fraction'] * 100:.0f}%)",
    f"in {P0['papers_with_mismatch']} of the {P0['papers']} papers",
    f"{_inv[0]:,} of {_inv[1]:,} pairwise orderings ({P0['pairwise_inversion_fraction'] * 100:.0f}%)",
    f"In {_sc['groups']} of the {mk['disagreements']} the plant-cost leader is the same catalyst",
    f"({_sc['papers']} papers, median regret {_sc['regret_median'] * 100:.0f}%)",
    f"in {_dc['groups']} it is a different catalyst ({_dc['papers']} papers, median regret {_dc['regret_median'] * 100:.0f}%)",
    f"{_share:.0f}% of the {mk['groups_with_two_or_more_catalysts']} comparisons",
    f"by conversion disagrees in {V['leaderboard_X']['top1_mismatch_groups']} of {V['leaderboard_X']['groups']} comparisons",
    f"by single-pass methanol yield in {V['leaderboard_X_times_S']['top1_mismatch_groups']}",
    f"by methanol selectivity in {V['leaderboard_S_MeOH']['top1_mismatch_groups']}",
    f"Treating recycled CO as inert gives {V['inert_opt']['top1_mismatch_groups']} of {V['inert_opt']['groups']}",
    f"{V['recycled_opt_limit_x1.5']['top1_mismatch_groups']}, {V['recycled_opt_limit_x2']['top1_mismatch_groups']} and "
    f"{V['recycled_opt_limit_x3']['top1_mismatch_groups']} of {V['recycled_opt_limit_x3']['groups']} comparisons",
    f"it is {V['recycled_opt_unconstrained']['top1_mismatch_groups']} of {V['recycled_opt_unconstrained']['groups']}",
    f"gave {V['recycled_opt_uncapped']['top1_mismatch_groups']} of {V['recycled_opt_uncapped']['groups']}",
    f"({V['printed_values_only']['top1_mismatch_groups']} of {V['printed_values_only']['groups']} comparisons)",
    f"({V['methanol_products_only']['top1_mismatch_groups']} of {V['methanol_products_only']['groups']})",
    f"({V['without_paper_with_most_groups']['top1_mismatch_groups']} of {V['without_paper_with_most_groups']['groups']})",
    f"more selective to methanol in {mk['plant_leader_more_selective']} of the {mk['disagreements']} comparisons "
    f"(median {mk['median']['S_ec'] * 100:.0f}% against {mk['median']['S_up'] * 100:.0f}%)",
    f"makes less CO in {mk['plant_leader_less_CO']}",
    f"has the higher conversion in only {mk['plant_leader_higher_conversion']}",
    f"runs cooler in {mk['plant_leader_cooler']}, by a median of {-mk['median']['dT']:.0f} °C",
    f"median purge of {mk['median']['purge_up'] * 100:.1f}%, the plant-cost leaders {mk['median']['purge_ec'] * 100:.1f}%",
    f"The largest regret, {P0['regret_max'] * 100:.0f}%",
    f"{sum(x >= 0.01 for x in _mm)} of the {len(_mm)} disagreements cost at least 1%, {sum(x >= 0.10 for x in _mm)} at least 10%",
)
# isothermal catalyst comparisons, the inlet-limit sweep and the published loop inlets it is read against
_iso = lit["isothermal"]["reference 6.86%"]
_ici = _iso["bootstrap"]["ci95"]
_sw = lit["limit_sweep"]
_span = ("5%", "6%", "8%", "10%")
_all = [_sw[k]["top1_mismatch_fraction"] for k in _span] + [P0["top1_mismatch_fraction"]]
_isw = [lit["isothermal"][k]["top1_mismatch_fraction"] for k in _span] + [_iso["top1_mismatch_fraction"]]
_lit = [r for r in rows("analysis/meoh_literature_inversion_2026_10_05/inlet_inert_literature.csv")
        if r["loop_type"] == "CO2"]
_litr = f"{min(float(r['non_h2co2_pct']) for r in _lit):.1f}–{max(float(r['non_h2co2_pct']) for r in _lit):.1f}%"
_nr = lit["infeasible"]["nonreactive_at_unconstrained_optimum_quantiles"]["0.5"]
tokens("Main text: methanol isothermal catalyst comparisons and inlet limit", text,
       f"a different catalyst leads on plant cost in {_iso['top1_mismatch_groups']} of {_iso['groups']} isothermal "
       f"comparisons ({_iso['top1_mismatch_fraction'] * 100:.0f}%; 95% confidence interval "
       f"{_ici[0] * 100:.0f}–{_ici[1] * 100:.0f}%), in {_iso['papers_with_mismatch']} of {_iso['papers']} papers",
       f"calibrated reference loop, {lit['infeasible']['nonreactive_limit'] * 100:.2f}%, inside the {_litr}",
       f"{min(_all) * 100:.0f}–{max(_all) * 100:.0f}% of all comparisons and "
       f"{min(_isw) * 100:.0f}–{max(_isw) * 100:.0f}% of isothermal catalyst comparisons disagree",
       f"to a median {_nr * 100:.0f}% of the reactor inlet",
       f"gives {_sw['none']['top1_mismatch_fraction'] * 100:.0f}% and "
       f"{lit['isothermal']['none']['top1_mismatch_fraction'] * 100:.0f}%")
tokens("Abstract: like-for-like methanol and ammonia shares",
       _block(raw_text, raw_text.index("## Abstract"), "## Abstract"),
       f"in {_iso['top1_mismatch_fraction'] * 100:.0f}% of methanol and")
tokens("SI: isothermal comparisons and absolute inlet limits", s8,
       f"{_iso['groups']} isothermal catalyst comparisons",
       f"in {_iso['top1_mismatch_groups']} of them ({_iso['top1_mismatch_fraction'] * 100:.0f}%; paper bootstrap "
       f"{_ici[0] * 100:.0f}–{_ici[1] * 100:.0f}%)",
       ", ".join(f"{_sw[k]['top1_mismatch_groups']} of {_sw[k]['groups']}" for k in _span[:3])
       + f" and {_sw['10%']['top1_mismatch_groups']} of {_sw['10%']['groups']} comparisons disagree",
       ", ".join(f"{lit['isothermal'][k]['top1_mismatch_groups']} of {lit['isothermal'][k]['groups']}" for k in _span[:3])
       + f" and {lit['isothermal']['10%']['top1_mismatch_groups']} of {lit['isothermal']['10%']['groups']} isothermal")
# ----- Firmness of the methanol headline ---------------------------------------------------------------------
st = json.loads((ROOT / "analysis/meoh_main_result_stats_2026_10_06/summary.json").read_text(encoding="utf-8"))
cc = json.loads((ROOT / "analysis/meoh_catalyst_cost_2026_10_06/summary.json").read_text(encoding="utf-8"))
pb = json.loads((ROOT / "analysis/meoh_plant_benchmark_2026_10_06/sensitivity_summary.json").read_text(encoding="utf-8"))
k1, ke = st["noise"]["meas_k1"], st["noise"]["meas_k1_plus_extraction"]
sci = P0["bootstrap"]["ci95"]
c3 = cc["variants"]["composition_3y"]
nf = k1["sty_leader_differs_from_reported_q025_q975"]
ok("MeOH statistics run on the current main result", st["point_estimate"]["groups"] == P0["top1_mismatch_groups"],
   str(st["point_estimate"]))
tokens(
    "MeOH literature: sampling, measurement and extraction firmness",
    s8,
    f"95% confidence interval of {sci[0] * 100:.0f}–{sci[1] * 100:.0f}%",
    f"keeps {k1['observed_mismatches_kept_in_ge_90pct']} of the {P0['top1_mismatch_groups']} disagreements",
    f"in {k1['sty_leader_differs_from_reported_mean']:.0f} comparisons (95% range {nf[0]:.0f}–{nf[1]:.0f})",
    f"leaves {ke['mismatch_groups_mean']:.1f} disagreeing comparisons on average (95% range "
    f"{ke['mismatch_groups_q025_q975'][0]:.0f}–{ke['mismatch_groups_q025_q975'][1]:.0f})",
    f"gives {c3['top1_mismatch_groups']} of {c3['groups']}.",
)
_pg = [r for r in rows("analysis/meoh_main_result_stats_2026_10_06/group_noise_probabilities.csv")
       if r["observed_mismatch"] == "True" and float(r["p_mismatch_meas_k1"]) >= 0.9]
ok("MeOH literature: robust disagreements all cost at least 1%",
   len(_pg) == k1["observed_mismatches_kept_in_ge_90pct"] and min(float(r["observed_regret"]) for r in _pg) >= 0.01,
   f"{len(_pg)} groups")
_v = st["validation"]
tokens("MeOH literature: response-surface validation in Methods", text,
       f"{_v['verdict_disagreements_total']} of {_v['verdicts_compared']:,} group verdicts")
_pvs = pb["variants"]
_pv = [v["top1_mismatch_groups"] for k, v in _pvs.items()
       if not k.startswith(("catalyst", "combined", "baseline", "recycle_weight"))]
tokens("MeOH plant benchmark: loop, recycle and price variants", text,
       f"disagreement at {min(_pv)}–{max(_pv)} of {P0['groups']} comparisons",
       f"fitted to one kinetic-model study, gives {_pvs['recycle_weight_nyari']['top1_mismatch_groups']}",
       f"every year at 95.24 euros per kilogram {_pvs['catalyst_repl_95.24EURkg_1y']['top1_mismatch_groups']}")
ok("MeOH plant benchmark: baseline reproduces the headline",
   pb["check"]["baseline_top1"] == f"{P0['top1_mismatch_groups']}/{P0['groups']}"
   and pb["check"]["baseline_inversions"] == P0["pairwise_inversions"])
_pm = {(r["metric"], r["cases"]): r for r in rows("analysis/meoh_plant_benchmark_2026_10_06/plant_metric_ranges.csv")}


def _rng(m, d):
    r = _pm[(m, "per-pass conversion 0.22-0.33")]
    return f"{float(r['min']):.{d}f}–{float(r['max']):.{d}f}"


tokens("MeOH plant benchmark: plant-metric ranges in Methods", text,
       f"({_rng('H2 consumption (t/t MeOH)', 3)} and {_rng('CO2 consumption (t/t MeOH)', 2)} tonnes per tonne of methanol)",
       f"carbon efficiency ({_rng('Carbon efficiency (MeOH C / fresh CO2)', 2)})",
       f"recycle ratio ({_rng('Recycle ratio (recycle / fresh feed, mol)', 1)})")

tokens("Abstract headline numbers", text, "1,695 alloy and metal surfaces",
       f"{lit['papers_with_candidates']} methanol studies and {fd['papers_in_set']} ammonia studies",
       f"in {_iso['top1_mismatch_fraction'] * 100:.0f}% of methanol and {FP['top1_mismatch_fraction'] * 100:.0f}% of ammonia cases")
tokens("Discussion: field-level shares", text,
       f"in {_iso['top1_mismatch_fraction'] * 100:.0f}% of isothermal methanol comparisons and "
       f"{FP['top1_mismatch_fraction'] * 100:.0f}% of ammonia comparisons",
       f"not the plant-cost leader in {P0['top1_mismatch_fraction'] * 100:.0f}% of methanol comparisons")
# main-text summaries written in the 2026-10-07 compression (the full statements live in the Supplementary Notes)
m_feru = main_section("Metal price and process optimization decide the Fe–Ru ranking")
tokens("Main text: actual-catalyst Monte Carlo summary", m_feru,
       f"Fe is cheaper in {mca['A_bed']['P_Fe_cheaper'] * 100:.1f}% of draws",
       f"in {mca['B']['P_Fe_cheaper'] * 100:.1f}% with the activities and Ru contents of the {mca['ranges']['measured_Ru_catalysts']} measured Ru catalysts")
_layer = {r["metal"]: r for r in rows("analysis/fe_bridge_backward_2026_09_29/inversion_layer_common_reference.csv")}
_ru_win = sum(r["economic_winner"] == "Ru" for r in draws)
tokens("Main text: layer-wise reversal, process narrowing and descriptor winners", m_feru,
       f"annualized metal replacement of {float(_layer['Fe']['annualized_replacement_cost_USD_t_NH3']):.3f} US dollars "
       f"per tonne for Fe against {float(_layer['Ru']['annualized_replacement_cost_USD_t_NH3']):.2f} for Ru",
       "Process optimization then narrows the gap", f"The remaining {gap:.3f} US dollars per tonne",
       f"Fe ranks first economically in {100 * fe_win / len(draws):.1f}% and Ru in {100 * _ru_win / len(draws):.1f}%")
ok("Descriptor samples: most Ru wins are Fe-bed-infeasible draws",
   2 * sum(r["economic_winner"] == "Ru" and str(r.get("Fe_feasible", "")).strip() in ("0", "False", "false")
           for r in draws) > _ru_win)
m_field = main_section("Published laboratory leaders are often not the plant-cost leaders")
tokens("Main text: field-level methanol and ammonia results", m_field,
       f"{lit['candidates']} operating points from {lit['papers_with_candidates']} studies",
       f"in {P0['top1_mismatch_groups']} of {P0['groups']} comparisons ({P0['top1_mismatch_fraction'] * 100:.0f}%",
       f"in {P0['papers_with_mismatch']} of the {P0['papers']} papers",
       f"in {FP['top1_mismatch_groups']} of them ({FP['top1_mismatch_fraction'] * 100:.0f}%",
       f"{tot['matched']} of the {tot['curated']} curated entries")
ok("no compute-budget Agent section in the manuscript",
   "Adaptive calculation selection makes the multiscale analysis repeatedly executable" not in raw_text
   and "5,000-CU" not in raw_text)

# ----- Report -----------------------------------------------------------------
failed = [(label, detail) for label, passed, detail in checks if not passed]
for label, passed, detail in checks:
    print(("PASS " if passed else "FAIL ") + label + (f" | {detail}" if detail else ""))
print(f"{len(checks)} checks, {len(failed)} failed")
raise SystemExit(1 if failed else 0)
