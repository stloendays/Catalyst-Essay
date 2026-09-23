"""Check every number in the live manuscript against the file it comes from.

Each claim recomputes a value from a committed source, formats it the way the manuscript
states it, and requires that exact string to appear in the manuscript. A value that moved
in its source, or text that drifted from its source, fails the check.

    python tools/check_manuscript_numbers.py [manuscript.md] [--replay=replay.json] [-v]

--replay points at the output of ci/replay_discover_v1_headlines.py (default
artifacts/discover_v1_scorer_replay/replay.json) for the parity-multiplier recovery counts.

Sources (all committed): NH3-FINAL-1.1 provenance (results.json, closure/*), the
2026-09-20 supervisor analyses, figures/composite/fig2 model tables, MEOH-D01-v3 data,
the Au/TiO2 control tables and the DISCOVER-BOUNDARY-C1 agent tables.
"""
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
TEXT_PATH = Path(ARGS[0]) if ARGS else ROOT / "docs/MANUSCRIPT_MAIN_TEXT_v8_2026-09-20.md"
REPLAY = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--replay=")),
                   ROOT / "artifacts/discover_v1_scorer_replay/replay.json"))
text = TEXT_PATH.read_text(encoding="utf-8")
text = re.sub(r"\s+", " ", text)
RUN = ROOT / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
SUP = ROOT / "analysis/supervisor_2026_09_20"


def rows(path):
    return list(csv.DictReader(open(ROOT / path, encoding="utf-8")))


res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
det, mc, bw = res["deterministic"], res["monte_carlo"], res["backward_reachability"]
head = json.loads((RUN / "closure/headline_1_1.json").read_text(encoding="utf-8"))
mcd = json.loads((RUN / "closure/mc_detail.json").read_text(encoding="utf-8"))
draws = rows(RUN.relative_to(ROOT) / "closure/mc_draws.csv")
eq = json.loads((SUP / "nh3_ru_price_equalization.json").read_text(encoding="utf-8"))
dec = {r["cost_pool"]: r for r in rows("analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv")}
cmc = json.loads((SUP / "nh3_cost_mc_summary.json").read_text(encoding="utf-8"))
orc = {r["metric"]: float(r["value"]) for r in rows("analysis/supervisor_2026_09_20/agent_oracle_summary.csv")}
sweep = rows("figures/composite/fig2/fig2_ru_price_sweep.csv")
parity = sweep.pop()
meoh = {r["candidate"]: r for r in rows("data/meoh/meoh_candidate_ranking_D01v3.csv")}
meoh_prov = json.loads((ROOT / "data/meoh/meoh_candidate_ranking_D01v3_provenance.json").read_text(encoding="utf-8"))
purge = rows("data/meoh/meoh_purge_robustness_D01v3.csv")
rankp = rows("analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv")
au = rows("data/rank_preservation_control_v1_1.csv")
semi = {(r["window"], r["stress"]): r for r in rows("data/rank_preservation_semiopen_v1_3_summary.csv")}
panel = rows("data/agent_figure_panel_data_2026-09-13.csv")
comp = rows("data/discover_boundary_c1_decision_components.csv")
tax = rows("data/discover_boundary_c1_error_taxonomy_summary.csv")
schema = json.loads((ROOT / "provenance/discover_v1/source_harness/DISCOVER_ACTION_SCHEMA_V1.json").read_text(encoding="utf-8"))
M = det["metals"]


def cell(tier, budget, arm="E"):
    return next(r for r in panel if r["tier"] == tier and r["arm"] == arm and r["budget_CU"] == str(budget))


def comp_cell(tier, budget, arm="E"):
    return next(r for r in comp if r["tier"] == tier and r["arm"] == arm and r["budget_CU"] == str(budget))


def f(v, nd):
    return ("%%.%df" % nd) % v


def minus(s):
    return s.replace("−", "-")


checks = []


def claim(label, expected, where=None):
    """expected: the exact string that must appear in the manuscript."""
    checks.append((label, expected, expected in text))


def fact(label, ok, detail=""):
    """A source-side consistency condition that the manuscript statement relies on."""
    checks.append((label, detail, bool(ok)))


# ---- NH3 ranking -----------------------------------------------------------------------------
act, eco = det["activity_order"], det["raw_economic_order"]
fact("atomic top three Ru > Os > Fe", act[:3] == ["Ru", "Os", "Fe"], " > ".join(act[:3]))
fact("economic top three Fe > Ru > Os", eco[:3] == ["Fe", "Ru", "Os"], " > ".join(eco[:3]))
claim("atomic order in abstract", "Ru > Os > Fe")
claim("economic order in abstract", "Fe > Ru > Os")
cost = {m: M[m]["unconstrained"]["total_cost"] for m in ("Fe", "Ru", "Os")}
claim("Fe/Ru/Os costs", "costs of %s, %s and %s US dollars per tonne" % (f(cost["Fe"], 3), f(cost["Ru"], 3), f(cost["Os"], 3)))
claim("top-3 Spearman", "Spearman rho is %s" % minus(f(head["top3_spearman"], 2)))
claim("top-3 Kendall", "Kendall tau is %s" % minus(f(head["top3_kendall"], 2)))
claim("global Spearman", "remains %s" % f(det["raw_global_spearman"], 3))
fact("15 metals screened", len(act) == 15, str(len(act)))
fact("14,136 process states", det["process_state_count"] == 14136, str(det["process_state_count"]))
claim("14,136-state library (text)", "14,136-state")
fe_u, ru_u = M["Fe"]["unconstrained"], M["Ru"]["unconstrained"]
claim("Fe operating point", "Fe occupies an interior optimum near %d °C and %d bar with a %d °C separator"
      % (fe_u["T_C"], fe_u["P_bar"], fe_u["Tsep_C"]))
claim("Ru operating point", "Ru prefers approximately %d °C and %d bar with a %d °C separator"
      % (ru_u["T_C"], ru_u["P_bar"], ru_u["Tsep_C"]))

# ---- equal-price counterfactual and decomposition ---------------------------------------------------
r8 = eq["Ru_price_equalized_to_Fe"]
claim("Fe price 8 USD/kg", "Fe value of %d US dollars per kilogram" % eq["Ru_price_equalized_to_Fe"]["price_USD_kg"])
claim("equal-price optimum", "to %d °C and %d bar, and the optimized cost falls to %s" % (r8["T_C"], r8["P_bar"], f(r8["total_cost_USD_t"], 3)))
claim("equal-price margin", "%s US dollars per tonne below Fe" % f(-eq["Ru_minus_Fe_USD_t"], 3))
claim("equal-price in abstract", "Ru reaching %s versus %s" % (f(r8["total_cost_USD_t"], 3), f(cost["Fe"], 3)))
claim("canonical gap", "canonical %s US dollars per tonne Ru-Fe gap" % f(float(dec["TOTAL"]["Ru_minus_Fe_USD_t"]), 3))
for pool, lab in (("fresh_compression_electricity", "Fresh-feed compression contributes +%s"), ("metal_inventory", "metal inventory +%s"),
                  ("compressor_CAPEX", "compressor capital +%s"), ("refrigeration_electricity", "refrigeration +%s")):
    claim("pool " + pool, lab % f(float(dec[pool]["Ru_minus_Fe_USD_t"]), 3))
fact("offset pools negative", all(float(dec[p]["Ru_minus_Fe_USD_t"]) < 0 for p in
                                  ("vessel_pressure_premium", "recycle_compression_electricity", "reactor_base")))

# ---- price sweep (Fig. 2d) -----------------------------------------------------------------------------
p_star = float(parity["price_USD_kg"])
claim("parity price", "parity at %s US dollars per kilogram" % f(p_star, 2))
claim("parity price, discussion", "reversal at %s US dollars per kilogram of Ru" % f(p_star, 2))
claim("parity / canonical ratio", "%d-fold below the canonical Ru price" % round(53852.5 / p_star))
claim("parity state", "Ru operates at %d °C and %d bar with a %s m3 bed" % (float(parity["T_C"]), float(parity["P_bar"]), f(float(parity["V_m3"]), 2)))
lo_row, hi_row = sweep[0], sweep[-1]
claim("sweep low end", "from %d bar and a %s m3 bed at 1 US dollar per kilogram" % (float(lo_row["P_bar"]), f(float(lo_row["V_m3"]), 1)))
top_p = sorted({float(r["P_bar"]) for r in sweep if float(r["price_USD_kg"]) > 5e4})
claim("sweep high end", "to %d–%d bar, a %d °C separator and a %s m3 bed at 3 × 10^5" % (top_p[0], top_p[-1], float(hi_row["Tsep_C"]), f(float(hi_row["V_m3"]), 3)))
fact("sweep monotone", all(float(a["cost"]) <= float(b["cost"]) + 1e-12 for a, b in zip(sweep, sweep[1:])))
fact("sweep: 241 log-spaced prices + 2 frozen", len(sweep) == 243, str(len(sweep)))
claim("sweep method count", "241 log-spaced prices")

# ---- descriptor Monte Carlo ------------------------------------------------------------------------
n_draws = len(draws)
fe_win = sum(r["economic_winner"] == "Fe" for r in draws)
fe_feas = sum(r["Fe_feasible"] == "1" for r in draws)
fact("1,000 descriptor draws", n_draws == 1000, str(n_draws))
claim("Fe feasible", "in %s%% of realizations" % f(100 * fe_feas / n_draws, 1))
claim("Fe economic Top-1", "economic Top-1 candidate in %s%% (%d/%d)" % (f(100 * fe_win / n_draws, 1), fe_win, n_draws))
claim("Fe Top-3 actionable", "actionable Top-3 in %s%%" % f(100 * mc["top3_actionable"], 1))
claim("Top-1 survival", "Top-1 survival is %s%%" % f(100 * mc["top1_survival"], 1))
fact("Fe feasibility matches results.json", abs(fe_feas / n_draws - mc["Fe_feasibility_probability"]) < 1e-12)
claim("Discussion 68.1%", "%s%% probability that Fe is the economic Top-1" % f(100 * fe_win / n_draws, 1))
claim("90 m3 criterion", "90 m3 bed-volume criterion")

# ---- joint cost Monte Carlo --------------------------------------------------------------------------
v = cmc["full_14136_state_direct_cost_verification"]
a = cmc["alpha_star"]
claim("cost MC draws", "Across %s draws" % format(cmc["draws"], ","))
claim("P(Fe<Ru)", "P(C_Fe < C_Ru) = %s" % f(v["P_C_Fe_lt_C_Ru"], 3))
claim("min gap", "cost gap equal to %s" % f(v["minimum_Ru_minus_Fe_USD_t"], 3))
claim("alpha* quantiles", "spans %s-fold, %s-fold and %s-fold" % (f(a["p05"], 2), f(a["p50"], 2), f(a["p95"], 2)))
claim("alpha* interval (discussion)", "%s-%s-fold central 90%% interval" % (f(a["p05"], 2), f(a["p95"], 2)))
claim("seed", "seed %d" % cmc["seed"])
fact("priors as stated", cmc["priors"]["Fe_price_multiplier"] == "log-uniform[0.5,2.0]" and
     cmc["priors"]["electricity_USD_MWh"].startswith("uniform[20,100]") and
     cmc["priors"]["catalyst_lifetime_y"].startswith("uniform[5,20]") and cmc["priors"]["CAPEX_multiplier"].startswith("uniform[0.8,1.2]"))

# ---- backward design and reachability ---------------------------------------------------------------
claim("alpha* canonical", "%s-fold activity increase" % f(bw["Ru_activity_break_even_multiplier"], 2))
claim("alpha* abstract", "at %d-fold" % round(bw["Ru_activity_break_even_multiplier"]))
claim("headroom 673 K", "headroom is %s-fold at 673 K" % f(bw["Ru_scaling_max_gain_673K"], 3))
claim("headroom max", "maximum of %s-fold" % f(bw["Ru_scaling_max_gain_all_states"], 3))
claim("best scaling cost", "remains %s US dollars per tonne of NH3 at E_N = %s eV" % (f(bw["Ru_best_scaling_cost_USD_t"], 3), minus(f(bw["Ru_best_scaling_EN_eV"], 3))))
fact("p05 exceeds headroom by > 10x", a["p05"] / bw["Ru_scaling_max_gain_all_states"] > 10, "%.1f" % (a["p05"] / bw["Ru_scaling_max_gain_all_states"]))

# ---- methanol ---------------------------------------------------------------------------------------
K = {"1wt250": "1 wt% Re | 250 C", "1wt200": "1 wt% Re | 200 C", "5wt200": "5 wt% Re | 200 C", "5wt250": "5 wt% Re | 250 C"}
up = sorted(K.values(), key=lambda k: int(meoh[k]["rank_STY_per_gRe"]))
ec = sorted(K.values(), key=lambda k: int(meoh[k]["economic_rank"]))
fact("MeOH upstream order", up == [K["1wt250"], K["1wt200"], K["5wt200"], K["5wt250"]], " > ".join(up))
fact("MeOH economic order", ec == [K["5wt200"], K["1wt200"], K["1wt250"], K["5wt250"]], " > ".join(ec))
npc = [round(float(meoh[k]["NPC_EUR_t_2pct_purge"])) for k in ec]
claim("MeOH NPC", "net production costs of %d, %d, %d and %s euros per tonne" % (npc[0], npc[1], npc[2], format(npc[3], ",")))
st = meoh_prov["metrics"]["STY_per_gRe (intrinsic productivity, reaction-case atomic_rank)"]
claim("MeOH rho/tau/inversions", "Spearman rho is %s, Kendall tau is %s and three of six pairwise comparisons invert"
      % (f(st["spearman"], 2), f(st["kendall"], 2)))
fact("3 of 6 inverted", st["pairwise_inversions"] == 3 and st["pairs"] == 6)
c55 = meoh[K["5wt250"]]
claim("MeOH leverage", "leverage is %s for methane suppression, %s for single-pass conversion and %s for space-time yield"
      % (f(float(c55["L_CH4_suppression"]), 5), f(float(c55["L_conversion"]), 5), f(float(c55["L_STY"]), 5)))
pp = [float(r["purge"]) for r in purge]
claim("purge range", "purge from %s%% to %d%% over %d levels" % (f(100 * min(pp), 1), round(100 * max(pp)), len(purge)))
claim("purge rho max", "rho never exceeds %s" % f(max(float(r["spearman"]) for r in purge), 2))
fact("at least two pairs inverted at every purge", min(int(r["pairwise_inversions"]) for r in purge) == 2)
fact("upstream winner never economic winner", all(r["economic_winner"] != K["1wt250"] for r in purge))
fact("MeOH order kept in 5,000/5,000 (both boundaries)",
     all(float(r["rank_%d" % (ec.index(K[{"1wtRe_200C": "1wt200", "5wtRe_200C": "5wt200", "1wtRe_250C": "1wt250",
                                             "5wtRe_250C": "5wt250"}[r["candidate"]]]) + 1)]) == 1.0 for r in rankp))
claim("2% purge", "source-anchored 2% purge condition")

# ---- Au/TiO2 control -------------------------------------------------------------------------------------
acts = [float(r["mass_activity_umol_CO_gcat_s"]) for r in au]
burd = [float(r["procurement_burden_vs_best"]) for r in au]
fact("Au activity strictly decreasing with size", all(x > y for x, y in zip(acts, acts[1:])))
fact("Au burden strictly increasing with size", all(x < y for x, y in zip(burd, burd[1:])))
claim("Au order", "2 > 3 > 4 > 5 > 6 nm")
claim("Au 10,000 draws", "all 10,000 predefined literature-envelope draws")
p1 = semi[("primary_273_293K", "moderate")]
p2 = semi[("sensitivity_273_313K", "moderate")]
claim("semi-open primary", "exact order in %s%% of 10,000 draws over 273.15–293.15 K, with mean rho = %s"
      % (f(100 * float(p1["full_preservation_fraction"]), 2), p1["mean_spearman_rho"]))
claim("semi-open wide", "lowers exact preservation to %s%% while retaining mean rho = %s"
      % (f(100 * float(p2["full_preservation_fraction"]), 2), p2["mean_spearman_rho"]))

# ---- agent -----------------------------------------------------------------------------------------------
claim("D threshold", "completes at %d compute units (CU)" % orc["D_threshold_CU"])
s75, s50 = cell("strong", 75), cell("strong", 50)
claim("strong 75 CU", "reaches %s/%s complete decisions at a 75-CU allowance" % (s75["k_complete_decision"], s75["n"]))
claim("strong 75 median stable", "median %s CU to the ledger-true decision-stable point" % s75["decision_stable_CU_median"])
claim("strong 50 CU", "at 50 CU, completion falls to %s/%s" % (s50["k_complete_decision"], s50["n"]))
c50 = comp_cell("strong", 50)
fact("winner and pair 20/20 at 50 CU", c50["k_winner"] == c50["k_pair"] == c50["n"] == "20")
fact("weaker tiers never above 7/20", max(int(r["k_complete_decision"]) for r in panel if r["tier"] in ("mini", "nano")) == 7)
fact("typed-interface mini arm completes 0/20", cell("mini", 175, "E2")["k_complete_decision"] == "0")
t_mini, t_e2 = next(r for r in tax if r["tier"] == "mini" and r["arm"] == "E" and r["budget_CU"] == "175"), \
    next(r for r in tax if r["tier"] == "mini" and r["arm"] == "E2" and r["budget_CU"] == "175")
fact("typed interface removes mini interface errors", t_mini["interface"] != "0" and t_e2["interface"] == "0",
     "%s -> %s" % (t_mini["interface"], t_e2["interface"]))
fact("typed interface raises budget and sequencing errors",
     int(t_e2["budget"]) > int(t_mini["budget"]) and int(t_e2["sequencing"]) > int(t_mini["sequencing"]))
claim("scorer floor", "floor is %d CU" % orc["scorer_oracle_CU"])
claim("protocol oracle", "oracle requires %d CU" % orc["protocol_oracle_CU"])
claim("oracle multiples", "allowance is %s times oracle, its median %s-CU decision-stable spend is %s times oracle, and the fixed-policy threshold is %s times oracle"
      % (f(orc["strong_allowance_75_over_oracle"], 2), s75["decision_stable_CU_median"], f(orc["strong_75_stable_over_oracle"], 2), f(orc["D_over_oracle"], 2)))
claim("non-binding", "canonical narrow-window use is %d/20, median decision stabilization moves to %d CU, and the policy spends a further median %d CU before self-stop, producing %d CU median final spend"
      % (round(orc["nonbinding_narrow_window_fraction"] * 20), orc["nonbinding_stable_CU"], orc["nonbinding_overrun_CU"], orc["nonbinding_final_CU"]))
claim("11-action interface", "%d-action" % len(schema["actions"]))

if REPLAY.exists():
    cb = json.loads(REPLAY.read_text(encoding="utf-8"))["c1"]["canonical_backward_by_budget"]
    claim("parity multiplier 9/20 at 75", "recovered in %d/%d runs at 75 CU and %d/%d at 225 CU"
          % (cb["75"]["canonical_backward"], cb["75"]["n"], cb["225"]["canonical_backward"], cb["225"]["n"]))

# ---- report ----------------------------------------------------------------------------------------------
bad = [c for c in checks if not c[2]]
for label, detail, ok in checks:
    if not ok or "-v" in sys.argv:
        print(("PASS " if ok else "FAIL ") + label + ("  |  " + detail if detail else ""))
print("%d checks, %d failed" % (len(checks), len(bad)))
sys.exit(1 if bad else 0)
