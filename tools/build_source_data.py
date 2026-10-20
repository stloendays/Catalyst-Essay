"""Source Data workbooks for the main figures (new numbering) and the Extended Data figures.

    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe tools/build_source_data.py   -> source_data/*.xlsx

Each workbook has a first sheet README naming the source file of every sheet, then one sheet per panel. A panel that
plots several arrays gets several titled blocks on its sheet. Every number is read from the CSV/JSON files the
renderers read, with the same filters and arithmetic (quoted in the block notes); nothing is typed in.

Figure numbering (manuscript of 2026-10-15; functions fig3/fig4/fig5 keep their 2026-10-07 names):
  Fig. 1  ammonia ranking reversal                    figures/composite/fig1/make_fig1.py
  Fig. 2  laboratory vs plant-cost leaderboards       figures/composite/fig_field/make_fig_field.py
  Fig. 3  methanol Re/TiO2 mechanism                  figures/composite/fig4/make_fig4.py   (function fig5)
  Fig. 4  metal price and process optimization        figures/composite/fig2/make_fig2.py   (function fig3)
  Fig. 5  backward design                             figures/composite/fig3/make_fig3.py   (function fig4)
  Fig. 6  process routes and Au/TiO2 control          figures/composite/fig5/make_fig5.py
  ED Figs 1-8                                         figures/extended_data/render_extended_data.py (tables: ed_data.py)

Ammonia numbers are those of NH3-FINAL-1.2: the canonical run provenance/nh3_final_1_2/.../nh3_final_1_2_20261013 and
the nh3_1_2/ outputs of each ammonia analysis. The Fig. 1 metal and rolling tables are built from that run's
results.json and the DISCOVER task descriptors with the arithmetic of figures/composite/fig1/fig1_data.py.
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

RUN = "provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013"
TASK = "provenance/discover_v1/source_harness/DISCOVER_TASK_V1.json"
SUP = "analysis/supervisor_2026_09_20/nh3_1_2"
BWD = "analysis/fe_bridge_backward_2026_09_29/nh3_1_2"
FIELD = "analysis/nh3_field_2026_10_06/nh3_1_2"
NH3F = "analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen"   # Fig. 2c,f: both ammonia batches
PROMO = "analysis/promoted_ru_literature_2026_10_05/nh3_1_2"
MC4 = "analysis/meoh_measurement_mc_2026_10_05"
F1, F2, F3, F4, F5 = ("figures/composite/fig%d" % i for i in range(1, 6))
F2M = F2 + "/nh3_1_2"            # the ammonia model tables of Fig. 3 (renderer figures/composite/fig2)


def csv(rel, **kw):
    return pd.read_csv(os.path.join(REPO, rel), **kw)


def js(rel):
    return json.load(open(os.path.join(REPO, rel), encoding="utf-8"))


def kv(d):
    """A two-column table from a dict of scalars."""
    return pd.DataFrame({"quantity": list(d), "value": list(d.values())})


def fig1_tables():
    """The Fig. 1 metal and rolling Top-K tables (columns of fig1_metals.csv and fig1_rolling.csv), built from the
    run's results.json and the DISCOVER task descriptors with the arithmetic of figures/composite/fig1/fig1_data.py."""
    det = js(RUN + "/results.json")["deterministic"]
    desc = {c["id"]: c for c in js(TASK)["candidate_set"]}
    act, eco = det["activity_order"], det["raw_economic_order"]
    assert set(desc) == set(act), "candidate set mismatch"
    met = pd.DataFrame([{
        "metal": m,
        "E_N_eV": desc[m]["descriptor_E_N_eV"],
        "price_USD_kg": desc[m]["price_USD_kg"],
        "logTOF_673K": det["metals"][m]["activity_logTOF"],
        "min_bed_m3": det["metals"][m]["min_bed_m3"],
        "log10_min_bed_m3": np.log10(det["metals"][m]["min_bed_m3"]),
        "feasible_90m3": int(det["metals"][m]["min_bed_m3"] <= 90.0),
        "cost_USD_t": det["metals"][m]["unconstrained"]["total_cost"],
        "atomic_rank": act.index(m) + 1,
        "economic_rank": eco.index(m) + 1} for m in act])
    roll = pd.DataFrame([{k: r[k] for k in ("K", "rho_raw", "rho_censored", "n_feasible")} for r in det["rolling"]])
    return met, roll


F1_SRC = RUN + "/results.json (deterministic) + " + TASK + " (descriptor_E_N_eV, price_USD_kg)"
F1_ROLL = RUN + "/results.json (deterministic.rolling)"


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
    met, roll = fig1_tables()
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
                   " + " + F1_SRC, "logTOF = logTOF(Ru) + log10(gain_673K)"),
                  ("cost-stack icon (stage 5): bar proportions only, no numbers printed", stack,
                   SUP + "/nh3_cost_decomposition.csv (Fe canonical pools)",
                   "the icon draws these four Fe pools in proportion")])
    b.panel("b", [("frontier step sites (structures are renders)", met[met.metal.isin(["Ru", "Os", "Fe"])][
        ["metal", "E_N_eV", "price_USD_kg", "atomic_rank", "economic_rank"]], F1_SRC, "")])

    def off_axis(mask):
        return " and ".join(met.metal[~mask])

    keep = met.logTOF_673K.between(-32, 1)
    b.panel("c", [("model curve", curve[["E_N_eV", "logTOF_673K_model_curve"]],
                   RUN + "/closure/scaling_reachability.csv", "Ru logTOF + log10(gain_673K)"),
                  ("metals", met[["metal", "E_N_eV", "logTOF_673K"]].assign(plotted=keep.values), F1_SRC,
                   "%s fall below the axis (logTOF < -32) and are annotated" % off_axis(keep))])
    keepd = met.log10_min_bed_m3.between(-5, 25)
    b.panel("d", [("minimum bed volume", met[["metal", "E_N_eV", "min_bed_m3", "log10_min_bed_m3", "feasible_90m3"]]
                   .assign(plotted=keepd.values), F1_SRC,
                   "90 m3 bed limit (log10 = %.6f); %s above the axis" % (np.log10(90.0), off_axis(keepd)))])
    fe, ru = met.set_index("metal").loc["Fe"], met.set_index("metal").loc["Ru"]
    b.panel("e", [("price vs activity", met[["metal", "logTOF_673K", "price_USD_kg"]].assign(
        plotted=(met.logTOF_673K >= -31).values), F1_SRC, ""),
                  ("ratios printed", kv({"Ru/Fe activity": 10 ** (ru.logTOF_673K - fe.logTOF_673K),
                                         "Ru/Fe price": ru.price_USD_kg / fe.price_USD_kg}), F1_SRC, "")])
    b.panel("f", [("atomic -> economic rank", met[["metal", "atomic_rank", "economic_rank"]], F1_SRC, ""),
                  ("Spearman rho printed", roll[roll.K.isin([3, 15])][["K", "rho_raw"]], F1_ROLL, "")])
    b.panel("g", [("rolling top-K Spearman", roll[["K", "rho_raw"]], F1_ROLL, "")])
    h = met.set_index("metal").loc[["Fe", "Ru", "Os"], ["cost_USD_t", "atomic_rank", "economic_rank"]].reset_index()
    b.panel("h", [("cost of the three feasible metals", h, F1_SRC, "")])
    b.save()


# ============================================================================== Fig. 2 (field leaderboards)
def fig2():
    b = Book("SourceData_Fig2.xlsx", "Fig. 2 (laboratory leaderboards vs plant-cost leaderboards; renderer "
             "figures/composite/fig_field/make_fig_field.py)")
    nh3 = js(NH3F + "/summary_printed.json")            # the printed-values primary the renderer plots
    b.panel("a", [("ACSA workflow", None, "schematic", "")])
    # panels b, d, e: the renderer's own tables (frozen scoring code, inert-limited loop and the loop without the limit)
    sys.path.insert(0, os.path.join(REPO, "figures", "composite", "fig_field"))
    import make_fig_field as FF  # noqa: E402
    lb = FF.meoh_leaderboards().drop(index="XS").reset_index()   # single-pass yield is in the caption only
    lb["label"] = lb.label.str.replace("S$_{MeOH}$", "S_MeOH", regex=False)
    kj = js("analysis/meoh_catalyst_level_2026_10_19/summary.json")
    kc = kj["cat_primary"]["comparison"]
    kr = kj["conversion_raised"]["cost_f0.95"]["cat_primary"]
    b.panel("b", [("leader changes by paper leaderboard: inert-limited loop (primary) and STY without the limit", lb,
                   "analysis/meoh_field_pooled_2026_10_15/pooled_candidates.csv (both extractions; cost_column) "
                   "scored with meoh_candidates.aggregate; CI95: analysis/meoh_field_pooled_2026_10_15/summary.json "
                   "(S6 / S5 primary.bootstrap_frozen_inversion.ci95)",
                   "bar height = fraction; hatched height = regret_gt5pct / groups"),
                  ("STY leader changes catalyst against catalyst (each catalyst at its best measured point), "
                   "inert-limited loop",
                   kv({"comparisons with at least two catalysts": kc["groups_2plus_catalysts"],
                       "leader is another catalyst": kc["changed"],
                       "of which cost gap above 5 %": kc["gt5pct"],
                       "CI95 low (paper bootstrap)": kc["ci95"][0], "CI95 high (paper bootstrap)": kc["ci95"][1]}),
                   "analysis/meoh_catalyst_level_2026_10_19/summary.json (cat_primary.comparison)",
                   "second bar (cat., lab. X)"),
                  ("STY leader changes catalyst against catalyst, each entry free to raise its conversion to 0.95 X_eq "
                   "with catalyst amount (primary count), inert-limited loop",
                   kv({"comparisons with at least two catalysts": kr["groups_2plus_catalysts"],
                       "leader is another catalyst": kr["changed"],
                       "of which cost gap above 5 %": kr["gt5pct"], "papers": kr["papers_changed"],
                       "CI95 low (paper bootstrap)": kr["ci95"][0], "CI95 high (paper bootstrap)": kr["ci95"][1]}),
                   "analysis/meoh_catalyst_level_2026_10_19/summary.json (conversion_raised.cost_f0.95.cat_primary); "
                   "per group: groups_catalyst_level_conversion_raised.csv", "first bar (cat., X raised)")])
    pr, nv = nh3["primary"], nh3["variants"]
    cases = [("rate per g catalyst (primary)", pr), ("rate per g metal", nv["per_g_metal_leaderboard"]),
             ("rate per g catalyst, 90 % Ru recovery", nv["Ru_recovery_90pct"])]
    tc = pd.DataFrame([dict(leaderboard=k, mismatch_groups=x["top1_mismatch_groups"], groups=x["groups"],
                            papers=x["papers"], fraction=x["top1_mismatch_fraction"],
                            CI95_low=x["bootstrap_papers"]["mismatch_fraction_ci95"][0],
                            CI95_high=x["bootstrap_papers"]["mismatch_fraction_ci95"][1],
                            regret_gt5pct_groups=x["regret_bins"]["gt5pct"]["groups"] if "regret_bins" in x else None)
                       for k, x in cases])
    gm = csv(NH3F + "/group_metrics_printed.csv")
    cand = csv(NH3F + "/candidates_printed.csv")
    dm = gm[gm.mismatch_kind == "different metal"]
    assert len(dm) == pr["mismatch_kinds"]["different metal"]["groups"]
    kinds = pd.DataFrame([dict(mechanism=k, groups=v["groups"], papers=v["papers"], regret_median=v["regret_median"],
                               regret_max=v["regret_max"]) for k, v in pr["mismatch_kinds"].items()])
    kinds["of_which_plant_winner_is_Fe"] = [int((dm.plant_winner_metal == "Fe").sum()) if k == "different metal"
                                            else None for k in kinds.mechanism]
    b.panel("c", [("ammonia leader changes", tc, NH3F + "/summary_printed.json (primary, "
                   "variants.per_g_metal_leaderboard, variants.Ru_recovery_90pct; bootstrap_papers, regret_bins)",
                   "bar height = fraction; hatched height = regret_gt5pct_groups / groups (primary only)"),
                  ("what the mismatched comparisons differ by (primary)", kinds,
                   NH3F + "/summary_printed.json (primary.mismatch_kinds); plant-winner metal from "
                   "group_metrics_printed.csv (plant_winner_metal)", "")])
    for sheet, (g, _, byp, _) in zip("de", FF.MEOH_GROUPS):
        t = FF.meoh_group(g, byp)
        b.panel(sheet, [("comparison group " + g, t, "analysis/meoh_literature_inversion_2026_10_05/"
                         "literature_candidates.csv", "x = STY (g_MeOH g_cat-1 h-1); filled y = cost_recycled_opt_inlet "
                         "(EUR/t, inert-limited loop; purge_recycled_opt_inlet, fraction of loop gas); open y = "
                         "cost_recycled_opt (no limit); marker area ~ %s; leaders of the inert-limited loop" % byp)])
    g = "10.1002/aenm.201801772 | 400 C | 5 MPa | H2/N2 3 | 6.6e+04 mL/g/h"
    t = cand[cand.group == g][["catalyst", "metal", "metal_wt_pct", "paper_rate", "cost_USD_t"]].copy()
    gr = gm.set_index("group").loc[g]
    assert len(t) == int(gr["n"])
    t["rate_mmol_gcat_h"] = t.paper_rate / 1000.0
    t["rate_leader"] = t.paper_rate == t.paper_rate.max()
    t["plant_cost_leader"] = t.cost_USD_t == t.cost_USD_t.min()
    b.panel("f", [("comparison group " + g, t, NH3F + "/candidates_printed.csv",
                   "paper_rate in umol g_cat-1 h-1; regret of the rate leader %.4f (group_metrics_printed.csv)"
                   % gr["regret"])])
    b.save()


# ============================================================================== Fig. 3 (price and process)
def fig3():
    b = Book("SourceData_Fig4.xlsx", "Fig. 4 (metal price and process optimization; renderer "
             "figures/composite/fig2/make_fig2.py)")
    env = csv(F2M + "/fig2_pressure_envelopes.csv")
    opt = env.loc[env.groupby("case").cost.idxmin()].reset_index(drop=True)
    sweep = csv(F2M + "/fig2_ru_price_sweep.csv")
    asw = csv(F2M + "/fig2_ru_alpha_sweep.csv")
    pts = csv(F2M + "/fig2_ru_actual_cost_points.csv")
    dec = csv(SUP + "/nh3_cost_decomposition.csv").set_index("cost_pool")
    f3 = csv(SUP + "/f3_panel_summary.csv").set_index("metric").value
    hist = csv(SUP + "/nh3_cost_mc_histogram.csv")
    draws = csv(RUN + "/closure/mc_draws.csv")
    met = fig1_tables()[0].set_index("metal")
    b.panel("a", [("NH3 synthesis loop", None, "schematic", "")])
    o = opt.set_index("case")
    ratios = kv({"Fe bed / Ru bed": o.loc["Fe", "V_m3"] / o.loc["Ru", "V_m3"],
                 "Ru metal cost / Fe metal cost": o.loc["Ru", "metal_cost"] / o.loc["Fe", "metal_cost"],
                 "Ru-priced-as-Fe bed / Ru bed": o.loc["Ru_at_Fe_price", "V_m3"] / o.loc["Ru", "V_m3"]})
    b.panel("b", [("optimum of each case (bed renders to scale)", opt[["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3",
                                                                       "metal_cost"]],
                   F2M + "/fig2_pressure_envelopes.csv", "minimum-cost row of each case"),
                  ("ratios printed", ratios, F2M + "/fig2_pressure_envelopes.csv", "")])
    b.panel("c", [("pressure envelopes", env[["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3"]],
                   F2M + "/fig2_pressure_envelopes.csv", ""),
                  ("optima", opt[["case", "P_bar", "cost"]], F2M + "/fig2_pressure_envelopes.csv", "")])
    sw = sweep.iloc[:-1][["price_USD_kg", "cost", "P_bar"]].assign(alpha_star=asw.iloc[:-1].alpha_star.values)
    assert np.allclose(sweep.iloc[:-1].price_USD_kg.values, asw.iloc[:-1].price_USD_kg.values)
    b.panel("d", [("Ru price sweep (upper: cost; lower: alpha* for parity)", sw, F2M + "/fig2_ru_price_sweep.csv + "
                   + F2M + "/fig2_ru_alpha_sweep.csv", "last row of each file is the parity point, listed below"),
                  ("parity", sweep.iloc[[-1]][["price_USD_kg", "cost", "P_bar"]], F2M + "/fig2_ru_price_sweep.csv", ""),
                  ("marked points: model Ru price and Ru priced as Fe", pts[pts.key == "pure"],
                   F2M + "/fig2_ru_actual_cost_points.csv", "Ru priced as Fe: the 8 USD/kg row of the sweep"),
                  ("Fe optimum", kv({"Fe cost USD/t": o.loc["Fe", "cost"]}), F2M + "/fig2_pressure_envelopes.csv", "")])
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
                      "canonical E_N Fe": met.loc["Fe", "E_N_eV"], "canonical E_N Ru": met.loc["Ru", "E_N_eV"]}),
                   RUN + "/closure/mc_draws.csv + " + F1_SRC, "")])
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
    b = Book("SourceData_Fig6.xlsx", "Fig. 6 (backward design; renderer figures/composite/fig3/make_fig3.py)")
    sw = csv(RUN + "/closure/breakeven_sweep.csv")
    sr = csv(RUN + "/closure/scaling_reachability.csv")
    res = js(RUN + "/results.json")
    mc = js(SUP + "/nh3_cost_mc_summary.json")["alpha_star"]
    cb = csv(BWD + "/activity_lifecycle_certified_boundary.csv")
    ck = csv(BWD + "/activity_lifecycle_target_keypoints.csv")
    gb = csv(BWD + "/scaling_lifecycle_exact_global_boundary.csv")
    ss = js(BWD + "/scaling_lifecycle_exact_summary.json")
    lit = csv(PROMO + "/fig3_literature_points.csv")
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
                  ("measured activity gains (bottom strip)", lit, PROMO + "/fig3_literature_points.csv",
                   "P04 is drawn as one point at factor_high, offset below its row")])
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
    b = Book("SourceData_Fig3.xlsx", "Fig. 3 (methanol Re/TiO2 mechanism; renderer figures/composite/fig4/make_fig4.py)")
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


# ============================================================================== Fig. 5 (Ru/C against fused iron, measured kinetics)
CONS = "analysis/nh3_keestra_consolidation_2026_10_20"
INR = "analysis/nh3_fe_inrange_kinetics_2026_10_19"


def frontier():
    b = Book("SourceData_Fig5.xlsx", "Fig. 5 (supported Ru/C against fused iron with measured rate laws; renderer "
             "figures/composite/fig_frontier/make_fig_frontier.py)")
    fc = csv(CONS + "/financing_curves.csv")
    leases = csv("analysis/nh3_ru_metal_financing_evidence_2026_10_12/pbf_catalyst_lease_contracts.csv")
    sm = js(CONS + "/summary.json")
    b.panel("a", [("Ru/C - Fe against the Ru financing rate", fc[["financing_rate_pct", "KAAP_RuC_minus_Fe",
                                                                  "benchmark_RuC_minus_Fe"]],
                   CONS + "/financing_curves.csv", "USD/t NH3; KAAP-type loop solid, each at own optimum dashed"),
                  ("break-even rates (owned metal and supplier lease)", kv({k: v for k, v in sm["D"]["breakevens"].items() if v is not None}),
                   CONS + "/summary.json", ""),
                  ("disclosed catalyst-metal leases (shaded range; median = reference rate)", leases,
                   "analysis/nh3_ru_metal_financing_evidence_2026_10_12/pbf_catalyst_lease_contracts.csv", "")])
    b.panel("b", [("three-bed converter at 9 MPa: best design of each arrangement", fc[[
        "financing_rate_pct", "staged_all_Fe", "staged_all_RuC", "staged_Ru_first", "staged_Ru_first_pattern",
        "staged_Fe_first", "staged_Fe_first_pattern", "staged_optimal", "staged_optimal_cost"]],
        CONS + "/financing_curves.csv", "Fe-first window from " + INR + "/staged_KM1R_1964_summary.json "
        "(window_keestra.staged_beats_all_Fe_below)")])
    sys.path.insert(0, os.path.join(REPO, "analysis", "nh3_staged_converter_2026_10_12"))
    import boundary as BD  # noqa: E402
    lib = csv(INR + "/staged_KM1R_1964_design_library.csv")
    lib = lib[(lib.P_bar == 90.0) & (lib.Tsep_C == -20.0)].copy()
    c_ru, c_fe, c_sup = BD.charges(53852.5, 0.9555, 0.021)
    lib["cost_at_2p10"] = lib.noncatalyst + (c_ru * lib.Ru_metal_kg + c_fe * lib.mass_Fe_kg
                                             + c_sup * lib.mass_Ru_cat_kg) / BD.C.H.annual_output_t
    best = lib.loc[[lib.cost_at_2p10.idxmin()], ["pattern", "cost_at_2p10", "V_m3", "Ru_volume_fraction",
                                                 "beds_volume_m3", "beds_T_in_out_C", "beds_y_NH3_out"]]
    b.panel("c", [("least-cost converter at 2.10 % per year", best, INR + "/staged_KM1R_1964_design_library.csv "
                   "(costed with analysis/nh3_staged_converter_2026_10_12/boundary.charges)", "")])
    val = js(INR + "/validation.json")["rate_ratio_90bar_Keestra"]
    rr = pd.DataFrame([dict(y_NH3=float(k.split("_")[-1]), **v) for k, v in val.items()]).sort_values("y_NH3")
    b.panel("d", [("Ru/C (8 wt%) to fused-iron rate ratio, 90 bar, 400 C", rr, INR + "/validation.json "
                   "(rate_ratio_90bar_Keestra)", "")])
    b.save()


# ============================================================================== Extended Data
# numbered in first-citation order (2026-10-07); E.edfigN keep the names of the first numbering
ED_TITLES = {1: "Extraction accuracy", 2: "Compute saved by the lower bound", 3: "Robustness of the methanol result",
             4: "Methanol plant benchmark", 5: "Measured ammonia catalysts", 6: "Bimetallic surfaces",
             7: "Supported Ru/C against fused iron with measured rate laws: robustness",
             8: "Au/TiO2 rank preservation and the catalyst-life channel", 9: "Ru against Ni in CO2 methanation",
             10: "Methanol purge optimum and reactor-inlet composition"}


def ed():
    import ed_new_2026_10_21 as N  # noqa: E402
    au, sab = N.au_data(), N.sab_data()
    rob = N.frontier_data()
    tables = {1: E.edfig1(), 2: E.edfig7()[0], 3: E.edfig3(), 4: E.edfig6(), 5: E.edfig4(), 6: E.edfig2()[0],
              7: {"a": (rob[["case", "gap_0_global", "gap_12_global", "gap_0_KAAP", "gap_12_KAAP"]], N.INR + "robustness.csv"),
                  "b": (rob[["case", "breakeven_global", "breakeven_KAAP"]], N.INR + "robustness.csv")},
              8: {"a": (pd.DataFrame({"diameter_nm": N.SIZES, "catalyst_required_rel_2nm": au["burden"]}),
                        N.AU + "summary.json"),
                  "b": (au["mc"], N.AU + "mc_v2_per_candidate.csv"),
                  "c": (au["map"], N.AU + "l2_boundary_map_q_vs_nm.csv (column q is the life exponent lambda)"),
                  "d": (au["comb"], N.AU + "l2_l3_combined_273_293K_moderate.csv (column q is lambda)")},
              9: {"a": (sab["central"][["scale_mw", "diff_ru_minus_ni_usd_mwh"]], N.SAB + "central_sweep.csv"),
                  "a_mc": (sab["mc"], N.SAB + "mc_summary.csv"),
                  "b": (sab["mc"][["scale_mw", "p_ru_cheaper"]], N.SAB + "mc_summary.csv"),
                  "c": (sab["lev"], N.SAB + "leverage_decomposition.csv")},
              10: E.edfig8()}
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
            if n == 6:
                blocks.append(("Fe benchmark line", kv({"Fe_cost_USD_t": fe2}), E.ALLOY_SUM, ""))
            b.panel(p, blocks)
        b.save()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (fig1, fig2, fig3, frontier, fig4, fig5, ed):
        f()
