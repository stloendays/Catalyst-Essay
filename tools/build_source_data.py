"""Source Data workbooks for the main figures (new numbering) and the Extended Data figures.

    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe tools/build_source_data.py   -> source_data/*.xlsx

Each workbook has a first sheet README naming the source file of every sheet, then one sheet per panel. A panel that
plots several arrays gets several titled blocks on its sheet. Every number is read from the CSV/JSON files the
renderers read, with the same filters and arithmetic (quoted in the block notes); nothing is typed in.

Figure numbering (manuscript of 2026-10-07):
  Fig. 1  ammonia ranking reversal                    figures/composite/fig1/make_fig1.py
  Fig. 2  laboratory vs plant-cost leaderboards       figures/composite/fig_field/make_fig_field.py
  Fig. 3  metal price and process optimization        figures/composite/fig2/make_fig2.py
  Fig. 4  backward design                             figures/composite/fig3/make_fig3.py
  Fig. 5  methanol Re/TiO2 mechanism                  figures/composite/fig4/make_fig4.py
  Fig. 6  process routes and Au/TiO2 control          figures/composite/fig5/make_fig5.py
  ED Figs 1-7                                         figures/extended_data/render_extended_data.py (tables: ed_data.py)
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(REPO, "source_data")
sys.path.insert(0, os.path.join(REPO, "figures", "extended_data"))
import ed_data as E  # noqa: E402

RUN = "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
SUP = "analysis/supervisor_2026_09_20"
BWD = "analysis/fe_bridge_backward_2026_09_29"
MC4 = "analysis/meoh_measurement_mc_2026_10_05"
F1, F2, F3, F4, F5 = ("figures/composite/fig%d" % i for i in range(1, 6))


def csv(rel, **kw):
    return pd.read_csv(os.path.join(REPO, rel), **kw)


def js(rel):
    return json.load(open(os.path.join(REPO, rel), encoding="utf-8"))


def kv(d):
    """A two-column table from a dict of scalars."""
    return pd.DataFrame({"quantity": list(d), "value": list(d.values())})


class Book:
    def __init__(self, name, figure):
        self.name, self.figure, self.sheets = name, figure, []

    def panel(self, sheet, blocks):
        """blocks: list of (title, DataFrame or None, source, note)."""
        self.sheets.append((sheet, blocks))

    def save(self):
        wb = Workbook()
        rd = wb.active
        rd.title = "README"
        rd.append(["Source Data for %s" % self.figure])
        rd["A1"].font = Font(bold=True)
        rd.append(["Built by tools/build_source_data.py from the files below; each sheet holds the numbers its panel "
                   "plots."])
        rd.append([])
        rd.append(["sheet", "block", "source file", "note"])
        for c in rd[4]:
            c.font = Font(bold=True)
        for sheet, blocks in self.sheets:
            ws = wb.create_sheet(sheet)
            r = 1
            for title, df, src, note in blocks:
                rd.append([sheet, title, src, note])
                ws.cell(r, 1, title).font = Font(bold=True)
                ws.cell(r + 1, 1, "source: " + src)
                r += 2
                if note:
                    ws.cell(r, 1, note)
                    r += 1
                if df is None:
                    ws.cell(r, 1, "no tabular data (schematic or rendered structure)")
                    r += 2
                    continue
                for j, col in enumerate(df.columns, 1):
                    ws.cell(r, j, str(col)).font = Font(bold=True)
                for row in df.itertuples(index=False):
                    r += 1
                    for j, v in enumerate(row, 1):
                        if isinstance(v, (np.bool_, bool)):
                            v = bool(v)
                        elif isinstance(v, np.integer):
                            v = int(v)
                        elif isinstance(v, np.floating):
                            v = None if np.isnan(v) else float(v)
                        elif isinstance(v, float) and np.isnan(v):
                            v = None
                        ws.cell(r, j, v)
                r += 3
            for j in range(1, 30):
                ws.column_dimensions[get_column_letter(j)].width = 16
        for col, w in zip("ABCD", (12, 40, 70, 90)):
            rd.column_dimensions[col].width = w
        path = os.path.join(OUT, self.name)
        wb.save(path)
        print("wrote", os.path.relpath(path, REPO), "(%d panel sheets)" % len(self.sheets))


# ============================================================================== Fig. 1 (ammonia ranking reversal)
def fig1():
    b = Book("SourceData_Fig1.xlsx", "Fig. 1 (ammonia ranking reversal; renderer figures/composite/fig1/make_fig1.py)")
    met = csv(F1 + "/fig1_metals.csv")
    roll = csv(F1 + "/fig1_rolling.csv")
    sr = csv(RUN + "/closure/scaling_reachability.csv")
    dec = csv(SUP + "/nh3_cost_decomposition.csv").set_index("cost_pool")
    ru_log = float(met.set_index("metal").loc["Ru", "logTOF_673K"])
    curve = pd.DataFrame({"E_N_eV": sr.E_N_eV, "gain_673K": sr.gain_673K,
                          "logTOF_673K_model_curve": ru_log + np.log10(sr.gain_673K)})
    stack = pd.DataFrame({"cost_pool": ["fresh_compression_electricity", "compressor_CAPEX",
                                        "vessel_pressure_premium + reactor_base", "recycle_compression_electricity"],
                          "Fe_canonical_USD_t": [dec.loc["fresh_compression_electricity", "Fe_canonical_USD_t"],
                                                 dec.loc["compressor_CAPEX", "Fe_canonical_USD_t"],
                                                 dec.loc["vessel_pressure_premium", "Fe_canonical_USD_t"]
                                                 + dec.loc["reactor_base", "Fe_canonical_USD_t"],
                                                 dec.loc["recycle_compression_electricity", "Fe_canonical_USD_t"]]})
    b.panel("a", [("model volcano icon (stage 2), drawn min-max normalized", curve, RUN + "/closure/scaling_reachability.csv"
                   " + " + F1 + "/fig1_metals.csv", "logTOF = logTOF(Ru) + log10(gain_673K)"),
                  ("cost-stack icon (stage 5): bar proportions only, no numbers printed", stack,
                   SUP + "/nh3_cost_decomposition.csv (Fe canonical pools)", "the renderer types these four values in "
                   "rounded (9.66, 3.87, 0.92, 0.76); they are the Fe pools listed here")])
    b.panel("b", [("frontier step sites (structures are renders)", met[met.metal.isin(["Ru", "Os", "Fe"])][
        ["metal", "E_N_eV", "price_USD_kg", "atomic_rank", "economic_rank"]], F1 + "/fig1_metals.csv", "")])
    keep = met.logTOF_673K.between(-32, 1)
    b.panel("c", [("model curve", curve[["E_N_eV", "logTOF_673K_model_curve"]],
                   RUN + "/closure/scaling_reachability.csv", "Ru logTOF + log10(gain_673K)"),
                  ("metals", met[["metal", "E_N_eV", "logTOF_673K"]].assign(plotted=keep.values),
                   F1 + "/fig1_metals.csv", "Ag and Au fall below the axis (logTOF < -32) and are annotated")])
    keepd = met.log10_min_bed_m3.between(-5, 25)
    b.panel("d", [("minimum bed volume", met[["metal", "E_N_eV", "min_bed_m3", "log10_min_bed_m3", "feasible_90m3"]]
                   .assign(plotted=keepd.values), F1 + "/fig1_metals.csv",
                   "90 m3 bed limit (log10 = %.6f); Ag and Au above the axis" % np.log10(90.0))])
    fe, ru = met.set_index("metal").loc["Fe"], met.set_index("metal").loc["Ru"]
    b.panel("e", [("price vs activity", met[["metal", "logTOF_673K", "price_USD_kg"]].assign(
        plotted=(met.logTOF_673K >= -31).values), F1 + "/fig1_metals.csv", ""),
                  ("ratios printed", kv({"Ru/Fe activity": 10 ** (ru.logTOF_673K - fe.logTOF_673K),
                                         "Ru/Fe price": ru.price_USD_kg / fe.price_USD_kg}), F1 + "/fig1_metals.csv",
                   "")])
    b.panel("f", [("atomic -> economic rank", met[["metal", "atomic_rank", "economic_rank"]], F1 + "/fig1_metals.csv",
                   ""),
                  ("Spearman rho printed", roll[roll.K.isin([3, 15])][["K", "rho_raw"]], F1 + "/fig1_rolling.csv", "")])
    b.panel("g", [("rolling top-K Spearman", roll[["K", "rho_raw"]], F1 + "/fig1_rolling.csv", "")])
    h = met.set_index("metal").loc[["Fe", "Ru", "Os"], ["cost_USD_t", "atomic_rank", "economic_rank"]].reset_index()
    b.panel("h", [("cost of the three feasible metals", h, F1 + "/fig1_metals.csv", "")])
    b.save()


# ============================================================================== Fig. 2 (field leaderboards)
def fig2():
    b = Book("SourceData_Fig2.xlsx", "Fig. 2 (laboratory leaderboards vs plant-cost leaderboards; renderer "
             "figures/composite/fig_field/make_fig_field.py)")
    lit = js("analysis/meoh_literature_inversion_2026_10_05/summary.json")
    st = js("analysis/meoh_main_result_stats_2026_10_06/summary.json")
    nh3 = js("analysis/nh3_field_2026_10_06/summary.json")
    b.panel("a", [("ACSA workflow", None, "schematic", "")])
    P, V = lit["primary"], lit["variants"]
    rows = [("STY", P), ("X*S", V["leaderboard_X_times_S"]), ("X", V["leaderboard_X"]),
            ("S_MeOH", V["leaderboard_S_MeOH"])]
    tb = pd.DataFrame([dict(leaderboard=k, mismatch_groups=x["top1_mismatch_groups"], groups=x["groups"],
                            papers=x["papers"], fraction=x["top1_mismatch_fraction"]) for k, x in rows])
    ci = st["cluster_bootstrap"]
    b.panel("b", [("leader changes by paper leaderboard (recycled CO)", tb,
                   "analysis/meoh_literature_inversion_2026_10_05/summary.json (primary, variants.leaderboard_*)", ""),
                  ("marker: STY leaderboard with inert CO", kv({"inert CO, mismatch groups":
                                                                V["inert_opt"]["top1_mismatch_groups"],
                                                                "inert CO, fraction":
                                                                V["inert_opt"]["top1_mismatch_fraction"]}),
                   "analysis/meoh_literature_inversion_2026_10_05/summary.json (variants.inert_opt)", ""),
                  ("error bar on STY: paper-cluster bootstrap", kv({"resamples": ci["resamples"],
                                                                    "CI95 low": ci["fraction_ci95"][0],
                                                                    "CI95 high": ci["fraction_ci95"][1]}),
                   "analysis/meoh_main_result_stats_2026_10_06/summary.json (cluster_bootstrap)", "")])
    pr, nv = nh3["primary"], nh3["variants"]
    cases = [("rate per g catalyst (primary)", pr), ("rate per g metal", nv["per_g_metal_leaderboard"]),
             ("rate per g catalyst, 90 % Ru recovery", nv["Ru_recovery_90pct"])]
    tc = pd.DataFrame([dict(leaderboard=k, mismatch_groups=x["top1_mismatch_groups"], groups=x["groups"],
                            papers=x["papers"], fraction=x["top1_mismatch_fraction"],
                            CI95_low=x["bootstrap_papers"]["mismatch_fraction_ci95"][0],
                            CI95_high=x["bootstrap_papers"]["mismatch_fraction_ci95"][1]) for k, x in cases])
    gm = csv("analysis/nh3_field_2026_10_06/group_metrics.csv")
    cand = csv("analysis/nh3_field_2026_10_06/candidates.csv")
    metal = cand.dropna(subset=["group"]).set_index(["group", "catalyst"]).sort_index().metal
    dm = gm[gm.mismatch_kind == "different metal"]
    winner_metal = [metal.loc[(g, w)] for g, w in zip(dm.group, dm.plant_winner)]
    winner_metal = [m.iloc[0] if isinstance(m, pd.Series) else m for m in winner_metal]
    kinds = pd.DataFrame([dict(mechanism=k, groups=v["groups"], papers=v["papers"], regret_median=v["regret_median"],
                               regret_max=v["regret_max"]) for k, v in pr["mismatch_kinds"].items()])
    kinds["of_which_plant_winner_is_Fe"] = [sum(m == "Fe" for m in winner_metal) if k == "different metal" else None
                                            for k in kinds.mechanism]
    b.panel("c", [("ammonia leader changes", tc, "analysis/nh3_field_2026_10_06/summary.json (primary, "
                   "variants.per_g_metal_leaderboard, variants.Ru_recovery_90pct; bootstrap_papers)", ""),
                  ("what the mismatched comparisons differ by (primary)", kinds,
                   "analysis/nh3_field_2026_10_06/summary.json (primary.mismatch_kinds); plant-winner metal from "
                   "group_metrics.csv + candidates.csv", "")])
    lc = csv("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
    for sheet, g in (("d", "10.1021/acscatal.5c05984 | 100 bar | H2/CO2 4 | 10 NL/g/h"),
                     ("e", "10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h")):
        t = lc[lc.group == g][["entry", "catalyst", "T_C", "X", "SMeOH", "SCH4", "STY", "cost_recycled_opt"]].copy()
        t["STY_leader"] = t.STY == t.STY.max()
        t["plant_cost_leader"] = t.cost_recycled_opt == t.cost_recycled_opt.min()
        b.panel(sheet, [("comparison group " + g, t, "analysis/meoh_literature_inversion_2026_10_05/"
                         "literature_candidates.csv", "x = STY (g_MeOH g_cat-1 h-1), y = cost_recycled_opt (EUR/t), "
                         "marker area ~ SCH4")])
    g = "10.1002/aenm.201801772 | 400 C | 5 MPa | H2/N2 3 | 6.6e+04 mL/g/h"
    t = cand[cand.group == g][["catalyst", "metal", "metal_wt_pct", "paper_rate", "cost_USD_t"]].copy()
    t["rate_mmol_gcat_h"] = t.paper_rate / 1000.0
    t["rate_leader"] = t.paper_rate == t.paper_rate.max()
    t["plant_cost_leader"] = t.cost_USD_t == t.cost_USD_t.min()
    b.panel("f", [("comparison group " + g, t, "analysis/nh3_field_2026_10_06/candidates.csv",
                   "paper_rate in umol g_cat-1 h-1; regret of the rate leader %.4f (group_metrics.csv)"
                   % gm.set_index("group").loc[g, "regret"])])
    b.save()


# ============================================================================== Fig. 3 (price and process)
def fig3():
    b = Book("SourceData_Fig3.xlsx", "Fig. 3 (metal price and process optimization; renderer "
             "figures/composite/fig2/make_fig2.py)")
    env = csv(F2 + "/fig2_pressure_envelopes.csv")
    opt = env.loc[env.groupby("case").cost.idxmin()].reset_index(drop=True)
    sweep = csv(F2 + "/fig2_ru_price_sweep.csv")
    asw = csv(F2 + "/fig2_ru_alpha_sweep.csv")
    pts = csv(F2 + "/fig2_ru_actual_cost_points.csv")
    dec = csv(SUP + "/nh3_cost_decomposition.csv").set_index("cost_pool")
    f3 = csv(SUP + "/f3_panel_summary.csv").set_index("metric").value
    hist = csv(SUP + "/nh3_cost_mc_histogram.csv")
    draws = csv(RUN + "/closure/mc_draws.csv")
    b.panel("a", [("NH3 synthesis loop", None, "schematic", "")])
    o = opt.set_index("case")
    ratios = kv({"Fe bed / Ru bed": o.loc["Fe", "V_m3"] / o.loc["Ru", "V_m3"],
                 "Ru metal cost / Fe metal cost": o.loc["Ru", "metal_cost"] / o.loc["Fe", "metal_cost"],
                 "Ru-priced-as-Fe bed / Ru bed": o.loc["Ru_at_Fe_price", "V_m3"] / o.loc["Ru", "V_m3"]})
    b.panel("b", [("optimum of each case (bed renders to scale)", opt[["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3",
                                                                       "metal_cost"]],
                   F2 + "/fig2_pressure_envelopes.csv", "minimum-cost row of each case"),
                  ("ratios printed", ratios, F2 + "/fig2_pressure_envelopes.csv", "")])
    b.panel("c", [("pressure envelopes", env[["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3"]],
                   F2 + "/fig2_pressure_envelopes.csv", "axis shows 0-1000 bar and 10.5-30 USD/t"),
                  ("optima", opt[["case", "P_bar", "cost"]], F2 + "/fig2_pressure_envelopes.csv", "")])
    sw = sweep.iloc[:-1][["price_USD_kg", "cost", "P_bar"]].assign(alpha_star=asw.iloc[:-1].alpha_star.values)
    assert np.allclose(sweep.iloc[:-1].price_USD_kg.values, asw.iloc[:-1].price_USD_kg.values)
    b.panel("d", [("Ru price sweep (upper: cost; lower: alpha* for parity)", sw, F2 + "/fig2_ru_price_sweep.csv + "
                   + F2 + "/fig2_ru_alpha_sweep.csv", "last row of each file is the parity point, listed below"),
                  ("parity", sweep.iloc[[-1]][["price_USD_kg", "cost", "P_bar"]], F2 + "/fig2_ru_price_sweep.csv", ""),
                  ("actual Ru catalyst points", pts, F2 + "/fig2_ru_actual_cost_points.csv", ""),
                  ("Fe optimum", kv({"Fe cost USD/t": o.loc["Fe", "cost"]}), F2 + "/fig2_pressure_envelopes.csv", "")])
    order = ["fresh_compression_electricity", "metal_inventory", "compressor_CAPEX", "refrigeration_electricity",
             "vessel_pressure_premium", "recycle_compression_electricity", "reactor_base"]
    wf = dec.loc[order, ["Fe_canonical_USD_t", "Ru_canonical_USD_t", "Ru_minus_Fe_USD_t"]].reset_index()
    wf["bar_start_USD_t"] = dec.loc["TOTAL", "Fe_canonical_USD_t"] + wf.Ru_minus_Fe_USD_t.cumsum().shift(fill_value=0)
    b.panel("e", [("waterfall Fe -> Ru", wf, SUP + "/nh3_cost_decomposition.csv", ""),
                  ("totals", dec.loc[["TOTAL"], ["Fe_canonical_USD_t", "Ru_canonical_USD_t", "Ru_minus_Fe_USD_t",
                                                 "Ru_equal_price_reoptimized_USD_t"]].reset_index(),
                   SUP + "/nh3_cost_decomposition.csv", "")])
    feas = draws.Fe_feasible.astype(str).isin(["1", "True", "1.0"])
    b.panel("f", [("1,000 descriptor draws", draws[["E_N_Fe", "E_N_Ru", "economic_winner", "Fe_feasible"]],
                   RUN + "/closure/mc_draws.csv", ""),
                  ("Fe bed-feasibility interval and canonical point", kv({
                      "E_N_Fe feasible min": draws.E_N_Fe[feas].min(), "E_N_Fe feasible max": draws.E_N_Fe[feas].max(),
                      "canonical E_N Fe": csv(F1 + "/fig1_metals.csv").set_index("metal").loc["Fe", "E_N_eV"],
                      "canonical E_N Ru": csv(F1 + "/fig1_metals.csv").set_index("metal").loc["Ru", "E_N_eV"]}),
                   RUN + "/closure/mc_draws.csv + " + F1 + "/fig1_metals.csv", "")])
    gm = ["Fe_feasible_descriptor_MC", "Fe_economic_top1_descriptor_MC", "top1_survival_descriptor_MC",
          "Fe_top3_actionable_descriptor_MC"]
    b.panel("g", [("decision endpoints (% of 1,000 draws)", pd.DataFrame({"metric": gm, "fraction": [float(f3[m]) for m in gm],
                                                                           "percent": [100 * float(f3[m]) for m in gm]}),
                   SUP + "/f3_panel_summary.csv", "")])
    b.panel("h", [("Ru - Fe cost gap, 5,000 joint cost draws", hist[["delta_left", "delta_right", "delta_count"]],
                   SUP + "/nh3_cost_mc_histogram.csv", ""),
                  ("lines", kv({m: float(f3[m]) for m in ("median_Ru_minus_Fe_cost_MC", "min_Ru_minus_Fe_cost_MC",
                                                          "P_C_Fe_lt_C_Ru_cost_MC")}),
                   SUP + "/f3_panel_summary.csv", "")])
    b.save()


# ============================================================================== Fig. 4 (backward design)
def fig4():
    b = Book("SourceData_Fig4.xlsx", "Fig. 4 (backward design; renderer figures/composite/fig3/make_fig3.py)")
    sw = csv(RUN + "/closure/breakeven_sweep.csv")
    sr = csv(RUN + "/closure/scaling_reachability.csv")
    res = js(RUN + "/results.json")
    mc = js(SUP + "/nh3_cost_mc_summary.json")["alpha_star"]
    cb = csv(BWD + "/activity_lifecycle_certified_boundary.csv")
    ck = csv(BWD + "/activity_lifecycle_target_keypoints.csv")
    gb = csv(BWD + "/scaling_lifecycle_exact_global_boundary.csv")
    ss = js(BWD + "/scaling_lifecycle_exact_summary.json")
    lit = csv("analysis/promoted_ru_literature_2026_10_05/fig3_literature_points.csv")
    br = res["backward_reachability"]
    fe = res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"]
    lit = lit.copy()
    row = {"promoter": 2, "support": 1, "confinement": 0}
    lit["y_plotted"] = [row[r] - (0.42 if i == "P04" else 0) for i, r in zip(lit["id"], lit["row"])]
    lit["x_plotted"] = [h if i == "P04" else lo for i, lo, h in zip(lit["id"], lit.factor_low, lit.factor_high)]
    b.panel("a", [("Ru cost vs direct activity multiplier", sw[["alpha", "Ru_cost"]],
                   RUN + "/closure/breakeven_sweep.csv", "axis shows alpha 0.3-800"),
                  ("lines and bands", kv({"alpha* (break-even)": br["Ru_activity_break_even_multiplier"],
                                          "Fe cost USD/t": fe,
                                          "Ru cost USD/t": res["deterministic"]["metals"]["Ru"]["feasible"]["total_cost"],
                                          "strict-scaling max gain (all states)": br["Ru_scaling_max_gain_all_states"],
                                          "alpha* p05 (cost MC)": mc["p05"], "alpha* p95 (cost MC)": mc["p95"]}),
                   RUN + "/results.json; " + SUP + "/nh3_cost_mc_summary.json", ""),
                  ("measured activity gains (bottom strip)", lit, "analysis/promoted_ru_literature_2026_10_05/"
                   "fig3_literature_points.csv", "P04 is drawn as one point at factor_high, offset below its row")])
    b.panel("b", [("lowest feasible Ru cost along the strict E_N scaling line",
                   sr.dropna(subset=["Ru_min_feasible_cost"])[["E_N_eV", "Ru_min_feasible_cost"]],
                   RUN + "/closure/scaling_reachability.csv", "rows with a feasible cost"),
                  ("printed values", kv({"best cost": br["Ru_best_scaling_cost_USD_t"],
                                         "best E_N eV": br["Ru_best_scaling_EN_eV"], "Fe cost": fe,
                                         "673 K headroom": br["Ru_scaling_max_gain_673K"],
                                         "state-specific max gain": br["Ru_scaling_max_gain_all_states"]}),
                   RUN + "/results.json (backward_reachability)", "")])
    m = cb.alpha <= 3.000001
    cc = cb[m][["alpha"]].copy()
    for L in (10, 15, 20):
        cc["required_recovery_pct_%dy" % L] = 100 * cb[m]["required_recovery_at_%dy" % L]
    kp = ck[(ck.Ru_recovery_fraction - 0.99).abs() <= 1e-12][
        ["catalyst_life_y", "Ru_recovery_fraction", "certified_upper_bound_required_direct_activity_multiplier"]]
    b.panel("c", [("required recovery vs direct activity multiplier", cc,
                   BWD + "/activity_lifecycle_certified_boundary.csv", "alpha <= 3"),
                  ("targets at 99 % recovery", kp, BWD + "/activity_lifecycle_target_keypoints.csv", "")])
    te = ss["tested_lifecycle_envelope"]
    bx = ss["boundary_examples"]
    b.panel("d", [("exact strict-scaling lifecycle boundary", gb[["life_y", "required_recovery_percent"]],
                   BWD + "/scaling_lifecycle_exact_global_boundary.csv", ""),
                  ("tested box and parity points", kv({
                      "tested box: max life (y)": te["max_life_y"],
                      "tested box: max recovery (%)": 100 * te["max_recovery_fraction"],
                      "best-corner margin vs Fe USD/t": te["best_corner"]["margin_vs_Fe_USD_t"],
                      "best-corner cost USD/t": te["best_corner"]["best_strict_scaling_cost_USD_t"],
                      "required recovery at 20 y (%)": 100 * bx["required_recovery_at_20y"],
                      "required life at 99 % recovery (y)": bx["required_life_at_99pct_recovery_y"],
                      "critical lifecycle factor q* (1/y)": ss["critical_lifecycle_factor_q_per_y"]}),
                   BWD + "/scaling_lifecycle_exact_summary.json", "")])
    b.save()


# ============================================================================== Fig. 5 (methanol Re/TiO2)
def fig5():
    b = Book("SourceData_Fig5.xlsx", "Fig. 5 (methanol Re/TiO2 mechanism; renderer figures/composite/fig4/make_fig4.py)")
    cand = csv("data/meoh/meoh_candidate_ranking_D01v3.csv")
    purge = csv("data/meoh/meoh_purge_robustness_D01v3.csv")
    rp = csv(MC4 + "/mc_rank_probability_matrix.csv")
    mcs = js(MC4 + "/mc_summary.json")["sets"]["canonical"]["k=1"]
    prov = js("data/meoh/meoh_candidate_ranking_D01v3_provenance.json")["metrics"]
    met = prov[next(k for k in prov if k.startswith("STY_per_gRe"))]
    cand = cand.sort_values("economic_rank")
    b.panel("a", [("CO2-to-methanol loop", None, "schematic", "")])
    b.panel("b", [("Re/TiO2 at 1 and 5 wt% Re", None, "structure renders (renders/ReTiO2_*.png)",
                   "the 12 and 60 Re atoms are illustrative")])
    cols = ["candidate", "STY_gMeOH_gRe_h", "X_CO2", "S_CH4", "CH4_fraction", "recycle_kmol_h", "H2_feed_EUR_t",
            "NPC_EUR_t_2pct_purge", "economic_rank"]
    c = cand[cols].copy()
    c["X_CO2_pct"], c["S_CH4_pct"], c["CH4_fraction_pct"] = 100 * c.X_CO2, 100 * c.S_CH4, 100 * c.CH4_fraction
    c["recycle_1e3_kmol_h"] = c.recycle_kmol_h / 1000.0
    b.panel("c", [("four states through the loop at 2 % purge", c, "data/meoh/meoh_candidate_ranking_D01v3.csv",
                   "rows in economic order")])
    r = rp[(rp.input_set == "canonical") & (rp.scale.astype(float) == 1.0)]
    b.panel("d", [("rank probability, 5,000 draws, measured uncertainty x1", r,
                   MC4 + "/mc_rank_probability_matrix.csv", "input_set canonical, scale 1"),
                  ("printed", kv({"P(winner stays first)": mcs["P_winner_stays_first"],
                                  "P(second vs third inverted)": mcs["second_vs_third"]["P_inverted"]}),
                   MC4 + "/mc_summary.json (sets.canonical.k=1)", "")])
    b.panel("e", [("STY-per-g-Re rank vs economic rank", cand[["candidate", "rank_STY_per_gRe", "economic_rank"]],
                   "data/meoh/meoh_candidate_ranking_D01v3.csv", ""),
                  ("rank statistics printed", kv({k: met[k] for k in ("spearman", "kendall", "pairwise_inversions",
                                                                      "pairs")}),
                   "data/meoh/meoh_candidate_ranking_D01v3_provenance.json (metrics STY_per_gRe)", "")])
    p = purge.copy()
    p.insert(1, "purge_pct", 100 * p.purge)
    b.panel("f", [("net cost and Spearman rho over 396 purge levels", p, "data/meoh/meoh_purge_robustness_D01v3.csv",
                   "")])
    c55 = cand.set_index("candidate").loc["5 wt% Re | 250 C", ["L_CH4_suppression", "L_conversion", "L_STY"]]
    b.panel("g", [("local economic leverage, 5 wt% Re, 250 C", kv(c55.to_dict()),
                   "data/meoh/meoh_candidate_ranking_D01v3.csv", "")])
    b.save()


# ============================================================================== Fig. 6 (routes and control)
def fig6():
    b = Book("SourceData_Fig6.xlsx", "Fig. 6 (process routes and Au/TiO2 control; renderer "
             "figures/composite/fig5/make_fig5.py)")
    dec = csv(SUP + "/nh3_cost_decomposition.csv")
    cand = csv("data/meoh/meoh_candidate_ranking_D01v3.csv").set_index("candidate")
    au = csv("data/rank_preservation_control_v1_1.csv")
    semi = csv("data/rank_preservation_semiopen_v1_3_summary.csv")
    meta = js(F5 + "/renders/Au_TiO2_2to6nm.json")
    roll = csv(F1 + "/fig1_rolling.csv").set_index("K").rho_raw
    prov = js("data/meoh/meoh_candidate_ranking_D01v3_provenance.json")["metrics"]
    met = prov[next(k for k in prov if k.startswith("STY_per_gRe"))]
    purge = csv("data/meoh/meoh_purge_robustness_D01v3.csv")
    lev = cand.loc["5 wt% Re | 250 C", ["L_CH4_suppression", "L_conversion", "L_STY"]].astype(float)
    levt = pd.DataFrame({"driver": ["S_CH4", "X_CO2", "STY"], "leverage": lev.values,
                         "edge_width_pt": 0.45 + 2.2 * (np.log10(lev.values) + 3.0) / 2.6})
    d = dec[["cost_pool", "Ru_minus_Fe_USD_t"]].copy()
    d["edge_width_pt"] = np.where(d.cost_pool == "TOTAL", np.nan, 0.35 + 0.55 * d.Ru_minus_Fe_USD_t.abs())
    b.panel("a", [("NH3: Ru - Fe by cost pool (edge widths)", d, SUP + "/nh3_cost_decomposition.csv", ""),
                  ("MeOH: local leverage at 5 wt% Re, 250 C (edge widths)", levt,
                   "data/meoh/meoh_candidate_ranking_D01v3.csv", "")])
    b.panel("b", [("Au/TiO2 particles (render)", pd.DataFrame({"diameter_nm": meta["diameters_nm"],
                                                              "Au_atoms": meta["au_atoms"]}),
                   F5 + "/renders/Au_TiO2_2to6nm.json", "labels only; the image is a render")])
    b.panel("c", [("activity rank vs catalyst-burden rank", au[["diameter_nm", "mass_activity_umol_CO_gcat_s",
                                                               "procurement_burden_vs_best"]],
                   "data/rank_preservation_control_v1_1.csv", "ranks 1-5 in file order on both sides")])
    b.panel("d", [("mass activity and required catalyst vs diameter", au[["diameter_nm", "mass_activity_umol_CO_gcat_s",
                                                                         "required_catalyst_mass_mg"]],
                   "data/rank_preservation_control_v1_1.csv", "")])
    e = semi[["window", "stress", "full_preservation_fraction"]].copy()
    e["percent"] = 100 * e.full_preservation_fraction
    b.panel("e", [("exact order kept, semi-open extension", e, "data/rank_preservation_semiopen_v1_3_summary.csv", "")])
    semi_mod = semi[(semi.window == "primary_273_293K") & (semi.stress == "moderate")].mean_spearman_rho.iloc[0]
    f = pd.DataFrame([
        dict(system="NH3, all 15 metals", rho=roll.loc[15], source=F1 + "/fig1_rolling.csv (K = 15)"),
        dict(system="NH3, frontier top 3", rho=roll.loc[3], source=F1 + "/fig1_rolling.csv (K = 3)"),
        dict(system="MeOH, 4 states, 2 % purge", rho=met["spearman"],
             source="data/meoh/meoh_candidate_ranking_D01v3_provenance.json"),
        dict(system="MeOH, min over purge 0.5-40 %", rho=purge.spearman.min(),
             source="data/meoh/meoh_purge_robustness_D01v3.csv"),
        dict(system="MeOH, max over purge 0.5-40 %", rho=purge.spearman.max(),
             source="data/meoh/meoh_purge_robustness_D01v3.csv"),
        dict(system="Au/TiO2, 5 sizes", rho=1.0, source="docs/RANK_PRESERVATION_CONTROL_V1_1_RESULT.md (rho = 1.000; "
             "the ranks in data/rank_preservation_control_v1_1.csv are identical)"),
        dict(system="Au/TiO2, semi-open moderate, mean", rho=semi_mod,
             source="data/rank_preservation_semiopen_v1_3_summary.csv (primary_273_293K, moderate)")])
    b.panel("f", [("upstream-to-downstream Spearman rho", f, "see column source", "")])
    b.save()


# ============================================================================== Extended Data
ED_TITLES = {1: "Extraction accuracy", 2: "Bimetallic surfaces", 3: "Robustness of the methanol result",
             4: "Measured ammonia catalysts", 5: "Actual-Ru-catalyst Monte Carlo", 6: "Methanol plant benchmark",
             7: "Compute saved by the lower bound"}


def ed():
    tables = {1: E.edfig1(), 2: E.edfig2()[0], 3: E.edfig3(), 4: E.edfig4(), 5: E.edfig5(), 6: E.edfig6(),
              7: E.edfig7()[0]}
    _, fe2 = E.edfig2()
    for n, t in tables.items():
        b = Book("SourceData_EDFig%d.xlsx" % n, "Extended Data Fig. %d (%s; renderer "
                 "figures/extended_data/render_extended_data.py, tables figures/extended_data/ed_data.py)"
                 % (n, ED_TITLES[n]))
        for p, (df, src) in sorted(t.items()):
            blocks = [("panel " + p, df, src, "")]
            if df.attrs:
                consts = {k: v for k, v in df.attrs.items() if not isinstance(v, dict)}
                for k, v in df.attrs.items():
                    if isinstance(v, dict):
                        consts.update({"%s.%s" % (k, kk): vv for kk, vv in v.items()})
                consts = {k: (", ".join("%.6g" % x for x in v) if isinstance(v, (list, tuple)) else v)
                          for k, v in consts.items()}
                blocks.append(("constants drawn on panel " + p, kv(consts), src.split(" ")[0], ""))
            if n == 2:
                blocks.append(("Fe benchmark line", kv({"Fe_cost_USD_t": fe2}), E.ALLOY_SUM, ""))
            b.panel(p, blocks)
        b.save()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, ed):
        f()
