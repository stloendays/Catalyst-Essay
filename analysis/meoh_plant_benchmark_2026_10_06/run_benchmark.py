"""Benchmark of the CO2-to-methanol recycle-economics model against real plants and rigorous process TEAs.

Outputs (this folder):
  reconciliation_plant.csv  Table A: plant metrics, model vs references (model at the canonical states and at the
                            reference studies' own operating points)
  reconciliation_cost.csv   Table B: production cost and breakdown, model run with each reference's own prices
  capex_scale.csv           specific fixed capital (EUR/(t/a)) of the model at each reference's scale
  summary.json              key numbers, identity gate, sensitivity summary (from lit_sensitivity.py)

Model: data/meoh/meoh_general_model.py (unchanged) through plant_variant.py (same equations, knobs exposed).
Reference numbers: reference_values.csv (source, locator, conversion for each).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import plant_variant as V  # noqa: E402

G, M = V.G, V.M
REF = pd.read_csv(HERE / "reference_values.csv")
NM3 = 22.414                      # Nm3/kmol
BULK = 1.05                       # t/m3, anchor catalyst bed density (Campos 2022 p4)
H2_MW, CO2_MW, MEOH_MW = M.MW["H2"], M.MW["CO2"], M.MW["MeOH"]
ANCHOR_CAT_T = M.SOURCE_CAT_T
ANCHOR_TPY = M.PROD_TPY


def ref(ref_id, q, col="value"):
    r = REF[(REF.ref_id == ref_id) & (REF.quantity == q)]
    if r.empty:
        raise KeyError((ref_id, q))
    return float(r.iloc[0][col])


def rng(ref_id, q):
    r = REF[(REF.ref_id == ref_id) & (REF.quantity == q)].iloc[0]
    lo, hi, v = r["low"], r["high"], r["value"]
    if pd.notna(lo) and pd.notna(hi):
        return f"{lo:g}-{hi:g}"
    if pd.notna(v):
        return f"{v:g}"
    return f"<= {hi:g}" if pd.notna(hi) else f">= {lo:g}"


def run(c, **kw):
    """Model point + derived plant metrics (floats)."""
    r = V.economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], **kw)
    prod_tph = kw.get("prod_tph", M.PROD_TPH)
    cat_m3 = float(r["catalyst_t"]) / BULK
    out = {k: float(np.asarray(v)) for k, v in r.items() if k not in ("ec", "loop", "y_out")}
    out.update(GHSV_h=float(r["reactor_in_kmol_h"]) * NM3 / cat_m3, STY_kg_L_h=prod_tph / cat_m3,
               H2_CO2_inlet=kw.get("h2_co2"), P_bar=kw.get("P_bar"), T_C=kw.get("T_C"),
               purge=float(np.asarray(kw.get("purge"))), X=c["X"],
               H2_share=out["h2_eur_t"] / out["cost_eur_t"], CO2_share=out["co2_eur_t"] / out["cost_eur_t"],
               ACC_share=out["acc_eur_t"] / out["cost_eur_t"], elec_share=out["elec_eur_t"] / out["cost_eur_t"],
               feed_share=(out["h2_eur_t"] + out["co2_eur_t"]) / out["cost_eur_t"])
    return out, r


def purge_for_ce(c, target, **kw):
    """Purge fraction at which the model's carbon efficiency equals a reference value (bisection on 0.1-40 %)."""
    lo, hi = 0.001, 0.40
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        ce = float(V.economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], purge=mid, **kw)["carbon_efficiency"])
        lo, hi = (mid, hi) if ce > target else (lo, mid)
    return 0.5 * (lo + hi)


def sty_for_ghsv(c, ghsv, **kw):
    """Catalyst productivity (g/g/h) that gives the reference GHSV at the model's own reactor-inlet flow."""
    r = V.economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], STY_per_g_cat=1.0, **kw)
    cat_t = float(r["reactor_in_kmol_h"]) * NM3 / ghsv * BULK
    return kw.get("prod_tph", M.PROD_TPH) / cat_t


# ------------------------------------------------------------------ model cases --------------------------------
ANCHOR = dict(X=M.SOURCE_X, SMeOH=M.SOURCE_S_MEOH, SCH4=0.0, SCO=M.SOURCE_S_CO)
ANCHOR_KW = dict(STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T, P_bar=70.0, h2_co2=3.0, purge=0.02, T_C=247.5,
                 x_co="recycled_central")
# canonical Re/TiO2 states: inputs of meoh_candidate_ranking_D01v3.csv (the frozen ranking file)
RANK = pd.read_csv(REPO / "data" / "meoh" / "meoh_candidate_ranking_D01v3.csv")


def canon(name):
    r = RANK[RANK.candidate == name].iloc[0]
    sch4 = float(r.S_CH4)
    sm = float(r.S_MeOH)
    return dict(X=float(r.X_CO2), SMeOH=sm, SCH4=sch4, SCO=round(1 - sm - sch4, 12)), \
        dict(STY_per_g_metal=float(r.STY_gMeOH_gRe_h), metal_wt=float(r["Re_wt%"]), P_bar=100.0, h2_co2=4.0,
             T_C=float(r.T_C))


CEPCI = {2014: 576.1, 2017: 567.5, 2018: 603.1, 2020: 596.2, 2021: 708.0}   # annual averages (Chem. Eng. magazine)


def cepci(year):
    """EUR-2020 equipment cost -> cost-year of a reference."""
    return CEPCI[year] / CEPCI[2020]


def fit_x_purge(c_sel, rr_target, ce_target, **kw):
    """Per-pass conversion and purge at which the model loop has a reference's recycle ratio and carbon efficiency."""
    from scipy.optimize import least_squares

    def res(z):
        X, p = 1 / (1 + np.exp(-z[0])), 1 / (1 + np.exp(-z[1]))
        r = V.economics(X, c_sel["SMeOH"], c_sel["SCH4"], c_sel["SCO"], purge=p, **kw)
        return [np.log(float(r["recycle_ratio"]) / rr_target), np.log(float(r["carbon_efficiency"]) / ce_target)]

    z = least_squares(res, x0=[np.log(0.25 / 0.75), np.log(0.01 / 0.99)], xtol=1e-12, ftol=1e-12).x
    return float(1 / (1 + np.exp(-z[0]))), float(1 / (1 + np.exp(-z[1])))


# ------------------------------------------------------------------ reference operating points ------------------
# Each entry: catalyst/loop inputs (c), loop keywords (kw: P, T, H2/CO2, purge, catalyst), and the study's own
# economic assumptions (econ: prices, scale, hours, finance, CEPCI year; cat: catalyst price EUR/kg and life y).
SEL_ANCHOR = dict(SMeOH=0.995, SCH4=0.0, SCO=0.005)


def tea_points():
    t = {}
    # Perez-Fortes 2016 (primary). X 21.97 %, 0.4 % of reactor CO2 -> CO (S_CO 0.018); reactor-inlet H2/CO2 3.8
    # (stream 13); outlet 288 C sets the RWGS window; ~1 % purge; 44.5 t catalyst for 55.1 t/h.
    t["PF"] = dict(c=dict(X=0.2197, SMeOH=0.982, SCH4=0.0, SCO=0.018),
                   kw=dict(P_bar=76.0, h2_co2=3.8, T_C=288.0, purge=0.01, STY_per_g_cat=55.1 / 44.5,
                           x_co="recycled_central"),
                   econ=dict(h2_price=3090.0, co2_price=0.0, elec_price=95.1, prod_tph=55.1, hours=8000.0, ir=0.08,
                             life=20, capex_mult=cepci(2014)), cat=(95.24, 1.0))
    # Van-Dal & Bouallou 2013: X 33 %, 75.7 bar, outlet 284 C, 1 % purge, 44.5 t for 59.3 t/h (no economics)
    t["VD"] = dict(c=dict(X=0.33, SMeOH=0.996, SCH4=0.0, SCO=0.004),
                   kw=dict(P_bar=75.7, h2_co2=3.0, T_C=284.0, purge=0.01, STY_per_g_cat=59.3 / 44.5,
                           x_co="recycled_central"),
                   econ=dict(prod_tph=59.3), cat=None)
    # Szima & Cormos 2018: X 30.05 %, 80 bar, 220 C, 1 wt% purge; bed 71.8 m3 x 0.98 x 1.05 t/m3 ~ 74 t (derived)
    szc = 71.8 * 0.98 * BULK
    t["SZ"] = dict(c=dict(X=0.3005, **SEL_ANCHOR),
                   kw=dict(P_bar=80.0, h2_co2=3.0, T_C=220.0, purge=0.01, STY_per_g_cat=12.5 / szc,
                           x_co="recycled_central"),
                   econ=dict(h2_price=53.4 * 60.0, co2_price=-10.0, elec_price=60.0, prod_tph=12.5, hours=8000.0,
                             ir=0.08, life=25, capex_mult=cepci(2017)),
                   cat=(75.0, szc * 75.0 / 3350.0))   # life set so the charge equals Szima's 3.35 M EUR/a
    # Nieminen 2019 gas-phase case: X 20.3 %, S_MeOH 96.1 %, 50 bar, outlet 274.4 C, 1 % purge, 3.49 t
    t["NI"] = dict(c=dict(X=0.203, SMeOH=0.961, SCH4=0.0, SCO=0.039),
                   kw=dict(P_bar=50.0, h2_co2=3.0, T_C=274.4, purge=0.01, STY_per_g_cat=2.275 / 3.49,
                           x_co="recycled_central"),
                   econ=dict(h2_price=3000.0, co2_price=50.0, elec_price=60.0, prod_tph=2.275, hours=7250.0,
                             ir=0.05, life=20, capex_mult=cepci(2018)), cat=(95.24, 4.0))
    # Nyari 2022, three kinetic models: X and purge fitted to each model's recycle ratio and methanol yield
    for key, rr, ce, out in (("NY_Kiss", 3.47, 0.9273, 7.41275), ("NY_VD", 7.67, 0.8956, 7.15967),
                             ("NY_Slotboom", 2.89, 0.9367, 7.488)):
        kw = dict(P_bar=69.7, h2_co2=3.0, T_C=236.0, STY_per_g_cat=out / 7.11, x_co="recycled_central")
        X, p = fit_x_purge(SEL_ANCHOR, rr, ce, prod_tph=out, **kw)
        t[key] = dict(c=dict(X=X, **SEL_ANCHOR), kw=dict(kw, purge=p),
                      econ=dict(h2_price=3000.0, co2_price=50.0, elec_price=40.0, prod_tph=out, hours=8300.0, ir=0.07,
                                life=20, capex_mult=cepci(2021)), cat=None)
    # Schorn 2021: Gibbs reactor at 80 bar, 230-250 C, no purge -> equilibrium per-pass conversion, lowest grid purge
    xeq = G.equilibrium_co2_conversion(dict(H2=75.0, CO2=25.0), 250.0, 80.0)[0]
    t["SC"] = dict(c=dict(X=xeq, **SEL_ANCHOR),
                   kw=dict(P_bar=80.0, h2_co2=3.0, T_C=250.0, purge=0.005, STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T,
                           x_co="recycled_central"),
                   econ=dict(elec_price=97.6, prod_tph=434000 / 8000.0, hours=8000.0, ir=0.08, life=20), cat=None)
    return t


def model_cases(tp):
    cases = {}
    cases["M1 anchor one-step (calibration point)"] = (ANCHOR, dict(ANCHOR_KW))
    three = dict(X=ref("CAMPOS22_3S", "per_pass_CO2_conversion"), SMeOH=0.998, SCH4=0.0, SCO=0.002)
    cases["M2 anchor three-step inputs (out-of-sample design)"] = (
        three, dict(STY_per_g_cat=M.PROD_TPH / ref("CAMPOS22_3S", "catalyst_t"), P_bar=70.0, h2_co2=3.0,
                    purge=0.02, T_C=258.5, x_co="recycled_central"))
    c, kw = canon("5 wt% Re | 200 C")
    cases["M3 canonical economic optimum, 5 wt% Re 200 C, 2 % purge"] = (c, dict(kw, purge=0.02, x_co="inert"))
    c, kw = canon("1 wt% Re | 200 C")
    cases["M4 canonical optimum at own purge, 1 wt% Re 200 C, 0.5 % purge"] = (c, dict(kw, purge=0.005, x_co="inert"))
    lc = dict(X=0.40, SMeOH=0.995, SCH4=0.0, SCO=0.005)
    lkw = dict(P_bar=80.0, h2_co2=3.0, T_C=250.0, x_co="recycled_central")
    lkw["purge"] = purge_for_ce(lc, 0.9525, STY_per_g_cat=1.0, **lkw)
    lkw["STY_per_g_cat"] = sty_for_ghsv(lc, 10500.0, **lkw)
    cases["M5 at Lurgi CO2-pilot conditions (80 bar, X 0.40, CE 95.25 %)"] = (lc, lkw)
    gc = dict(X=0.141, SMeOH=0.99, SCH4=0.0, SCO=0.01)
    gkw = dict(P_bar=50.0, h2_co2=3.0, T_C=224.5, x_co="recycled_central", STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T)
    gkw["purge"] = purge_for_ce(gc, 0.915, **gkw)
    cases["M6 at Gonzalez-Garay conditions (50 bar, X 0.141, CE 91.5 %)"] = (gc, gkw)
    labels = {"PF": "M7 at Perez-Fortes 2016 point (76 bar, X 0.2197, 1 % purge, 44.5 t)",
              "VD": "M8 at Van-Dal 2013 point (75.7 bar, X 0.33, 1 % purge, 44.5 t)",
              "SZ": "M9 at Szima 2018 point (80 bar, X 0.30, 1 % purge)",
              "NY_Slotboom": "M10 at Nyari 2022 Slotboom point (fitted to RR 2.89, CE 0.937)",
              "NY_VD": "M11 at Nyari 2022 VD point (fitted to RR 7.67, CE 0.896)",
              "NI": "M12 at Nieminen 2019 gas-phase point (50 bar, X 0.203, S 0.961)"}
    for k, lab in labels.items():
        prod = tp[k]["econ"].get("prod_tph", M.PROD_TPH)
        cases[lab] = (tp[k]["c"], dict(tp[k]["kw"], prod_tph=prod))
    return cases


PLANT_ROWS = [
    ("Loop pressure (bar)", "P_bar"),
    ("Reactor / coolant T (C)", "T_C"),
    ("Reactor-inlet H2/CO2 (mol/mol)", "H2_CO2_inlet"),
    ("Fresh-feed H2/CO2 (mol/mol)", "fresh_h2_co2"),
    ("Per-pass CO2 conversion", "X"),
    ("Recycle ratio (recycle / fresh feed, mol)", "recycle_ratio"),
    ("Purge fraction of separator gas", "purge"),
    ("Purge flow (kmol/h, at the case's scale)", "purge_kmol_h"),
    ("H2 consumption (t/t MeOH)", "h2_t_per_t"),
    ("CO2 consumption (t/t MeOH)", "co2_t_per_t"),
    ("Carbon efficiency (MeOH C / fresh CO2)", "carbon_efficiency"),
    ("Electricity, compression (MWh/t)", "elec_MWh_t"),
    ("Catalyst inventory (t, at the case's scale)", "catalyst_t"),
    ("GHSV (1/h, bed density 1.05 t/m3)", "GHSV_h"),
    ("STY (kg MeOH / L cat / h)", "STY_kg_L_h"),
    ("Catalyst lifetime (y)", None),
    ("Loop pressure drop (bar)", None),
]

REFERENCE_CELLS = {
    "Loop pressure (bar)": "Campos 70 | Ott/Dieterich 50-100 | Bozzano 50-100 atm | Perez-Fortes 76 | Van-Dal 75.7 | "
                           "Szima 80 | Nyari 69.7 | Nieminen 50 | Schorn 80 | Zhang 78 | Sollai 65 | Battaglia 65 | "
                           "Cordero-Lanzac 50 | Gonzalez-Garay 50 | Hank 40 | Bos 50 | Rihko 50 | Lurgi pilot* 80 | "
                           "CRI Olah* 101",
    "Reactor / coolant T (C)": "Campos 247.5 / 258.5 | 200-300 | Perez-Fortes 210 in / 288 out | Van-Dal 210 / 284 | "
                               "Szima 220 | Nyari 236 | Nieminen 215 / 274 | Zhang 290 | Sollai 210 / 290 | "
                               "Battaglia 250 | Cordero-Lanzac 300 (In2O3/Co) | Gonzalez-Garay 221-228",
    "Reactor-inlet H2/CO2 (mol/mol)": "Campos 3.26 | Perez-Fortes ~3.8 (stream 13) | Cordero-Lanzac 4",
    "Fresh-feed H2/CO2 (mol/mol)": "3.0 in Campos, Perez-Fortes (2.98), Van-Dal, Szima, Nyari, Nieminen, Schorn, Rihko; "
                                   "Sollai 3.14",
    "Per-pass CO2 conversion": "Campos 0.285 / 0.539 | Perez-Fortes 0.2197 | Van-Dal 0.33 | Szima 0.3005 | "
                               "Nieminen 0.203 | Zhang 0.21 | Gonzalez-Garay 0.124-0.158 | SRC 0.36 | "
                               "Lurgi pilot* 0.35-0.45",
    "Recycle ratio (recycle / fresh feed, mol)": "Campos 2.81 (HP 2.67) / 1.21 | Perez-Fortes ~4.7 | Van-Dal 5.0 | "
                                                 "Nieminen 5.3 | Zhang 5.2 | Nyari 3.47 / 7.67 / 2.89 | "
                                                 "Rihko 3.2 | conventional 3-5 (Dieterich, Hansen) | Bozzano ~5 | "
                                                 "Lurgi pilot* 4.5 | Mitsui* 2.6-3.2",
    "Purge fraction of separator gas": "Campos 0.02 | Perez-Fortes ~0.01 | Van-Dal 0.01 | Szima 0.01 (mass) | "
                                       "Nyari 0.005 (mass) | Nieminen 0.01 | Zhang 0.013 | Cordero-Lanzac 0.025",
    "Purge flow (kmol/h, at the case's scale)": "Campos 1102 (SI) / 456",
    "H2 consumption (t/t MeOH)": "stoich. 0.189 | Campos 0.200 pure (0.2145 stream incl. N2) / 0.193 | "
                                 "Perez-Fortes 0.199 | Van-Dal 0.204 | Szima 0.194 | Nyari 0.204 / 0.211 / 0.202 | "
                                 "Nieminen 0.234 | Schorn 0.189 | Zhang 0.209 | Sollai 0.208 | Battaglia 0.217 | "
                                 "Hank 0.189-0.193 | Rihko 0.197",
    "CO2 consumption (t/t MeOH)": "stoich. 1.374 | Campos 1.457 / 1.406 | Perez-Fortes 1.460 | Van-Dal 1.484 | "
                                  "Szima 1.41 | Nyari 1.48 / 1.53 / 1.47 | Nieminen 1.706 | Schorn 1.373 | "
                                  "Zhang 1.51 | Sollai 1.446 | Battaglia 1.581 | CRI Olah 1.375-1.40 | Shunli 1.455",
    "Carbon efficiency (MeOH C / fresh CO2)": "Campos 0.943 / 0.977 | Perez-Fortes 0.9385 | Van-Dal 0.925 | "
                                              "Szima 0.9725 | Nyari 0.927 / 0.896 / 0.937 | Nieminen 0.805 | "
                                              "Sollai 0.950 | Battaglia 0.872 | conventional 0.93-0.98",
    "Electricity, compression (MWh/t)": "Campos 0.325 compressors / 0.121 net | Perez-Fortes 0.305 compressors / "
                                        "0.169 net | Van-Dal 0.297 net | Szima 0.229 | Nyari 0.151 / 0.474 / 0.140 | "
                                        "Nieminen 0.624 | Schorn 0.154 | Sollai 0.207 | Bos 0.22",
    "Catalyst inventory (t, at the case's scale)": "Campos 2869 / 1434 | Perez-Fortes 44.5 | Van-Dal 44.5 | "
                                                   "Nyari 7.11 | Nieminen 3.49 | Sollai 0.29 | Cordero-Lanzac 105",
    "GHSV (1/h, bed density 1.05 t/m3)": "Campos 604 | Perez-Fortes ~21000 | SRC 6000-12000 | Lurgi pilot* 10500",
    "STY (kg MeOH / L cat / h)": "Campos 0.053 | Perez-Fortes 1.31 | Van-Dal 1.42 | CO2 feed 0.4-0.8 (Dieterich); "
                                 "per kg: Nyari 1.04, Nieminen 0.65, Sollai 1.71, Cordero-Lanzac 0.31",
    "Catalyst lifetime (y)": "Campos 3 | Perez-Fortes 1 | Nyari 3 | Nieminen 4 | Sollai 4 | Zhang 4 | Ott 2-5 | "
                             "Dieterich 4-6 | Bozzano 3-4; price 95.24 EUR/kg (PF, Nieminen, Sollai, Battaglia), "
                             "75 (Szima), 18.1 (Campos), 15 (Bos)",
    "Loop pressure drop (bar)": "Perez-Fortes 4.2 | Van-Dal 4.6 | Zhang 4 | Schorn 1 | Lurgi SRC loop 3.5-4, "
                                "Toyo loop 3 (Dieterich)",
}


def table_a(cases):
    res = {k: run(c, **kw)[0] for k, (c, kw) in cases.items()}
    rows = []
    for label, key in PLANT_ROWS:
        row = {"metric": label}
        for k, r in res.items():
            if key is None:
                row[k] = {"Catalyst lifetime (y)": "3 (in constant residual; no inventory term)",
                          "Loop pressure drop (bar)": f"{M.LOOP_DP_BAR:g}"}[label]
            else:
                v = r[key]
                row[k] = round(v, 4) if abs(v) < 10 else round(v, 1)
        row["references"] = REFERENCE_CELLS[label]
        rows.append(row)
    rows.append({"metric": "Net production cost (EUR/t, anchor prices and scale conventions)",
                 **{k: round(r["cost_eur_t"], 2) for k, r in res.items()},
                 "references": "Campos 920 (Table 7: 1071.8 M EUR/a = 924.0) | 3-step 868 (871.2)"})
    return pd.DataFrame(rows), res


RANGE_METRICS = [("H2 consumption (t/t MeOH)", "h2_t_per_t"), ("CO2 consumption (t/t MeOH)", "co2_t_per_t"),
                 ("Carbon efficiency (MeOH C / fresh CO2)", "carbon_efficiency"),
                 ("Recycle ratio (recycle / fresh feed, mol)", "recycle_ratio"),
                 ("Electricity, compression (MWh/t)", "elec_MWh_t"), ("GHSV (1/h, bed density 1.05 t/m3)", "GHSV_h"),
                 ("Per-pass CO2 conversion", "X")]
CONVENTIONAL_X = (0.22, 0.33)          # per-pass conversion of the conventional reference loops (PF 0.2197 ... VD 0.33)


def metric_ranges(res):
    """Real min-max of each plant metric over the model cases of Table A, with the case at each end: all cases, and
    the cases at conventional per-pass conversion."""
    rows = []
    conv = [k for k, r in res.items() if CONVENTIONAL_X[0] - 1e-3 <= float(r["X"]) <= CONVENTIONAL_X[1] + 1e-3]
    for label, key in RANGE_METRICS:
        for subset, keys in (("all model cases (M1-M12)", list(res)),
                             (f"per-pass conversion {CONVENTIONAL_X[0]:g}-{CONVENTIONAL_X[1]:g}", conv)):
            v = {k: float(res[k][key]) for k in keys}
            lo, hi = min(v, key=v.get), max(v, key=v.get)
            rows.append(dict(metric=label, cases=subset, n=len(keys), min=v[lo], min_case=lo, max=v[hi], max_case=hi))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Table B ------------------------------------
def lean(r):
    """Model terms that every TEA boundary shares: feed + electricity + catalyst replacement + capital annuity."""
    return r["h2_eur_t"] + r["co2_eur_t"] + r["elec_eur_t"] + r["cat_eur_t"] + r["acc_eur_t"]


def B(case, term, model, reference, basis="", attribution=""):
    return dict(case=case, term=term, model=model, reference=reference, ref_basis=basis, attribution=attribution)


def table_b(tp):
    rows = []
    t = ANCHOR_TPY / 1e6
    a, _ = run(ANCHOR, **ANCHOR_KW)
    a_cat, _ = run(ANCHOR, cat_term=V.CAT_REF, **ANCHOR_KW)
    h2_stream = (0.995 * H2_MW + 0.005 * M.MW["N2"]) / (0.995 * H2_MW)   # Campos prices the H2 stream incl. N2
    c1 = "B1 Campos 2022 one-step (calibration point; SI Table S19)"
    rows += [
        B(c1, "H2", a["h2_eur_t"], ref("CAMPOS22", "H2_cost_MEUR_y") / t, "SI Table S19: 769.50 M EUR/a",
          f"model prices pure H2 (0.1985 t/t). Campos prices the 31.1 t/h stream incl. 0.5 % N2 (2.0 t/h N2): "
          f"model x {h2_stream:.4f} = {a['h2_eur_t'] * h2_stream:.1f}"),
        B(c1, "CO2", a["co2_eur_t"], ref("CAMPOS22", "CO2_cost_MEUR_y") / t, "SI Table S19: 74.93", "1.449 vs 1.460 t/t"),
        B(c1, "electricity", a["elec_eur_t"], ref("CAMPOS22", "power_cost_MEUR_y") / t,
          "SI Table S19: 12.66 (17.6 MW net of 29.82 MW generator)",
          "model: compressors only, isothermal/0.8 (28.9 MW vs Campos 47.18 MW), no Rankine credit"),
        B(c1, "catalyst replacement", a["cat_eur_t"], ref("CAMPOS22", "catalyst_cost_MEUR_y") / t,
          "SI Table S19: 17.31", "model: inside the constant residual"),
        B(c1, "other direct (residual)", a["residual_direct_eur_t"], ref("CAMPOS22", "other_direct_MEUR_y") / t,
          "SI Table S19: 0.52", "constant by construction; carries the N2, catalyst and power differences"),
        B(c1, "ACC (CAPEX annuity)", a["acc_eur_t"], ref("CAMPOS22", "ACC_MEUR_y") / t, "Table 7", ""),
        B(c1, "indirect OPEX", a["fixed_indirect_eur_t"] + a["revenue_linked_eur_t"],
          ref("CAMPOS22", "indirect_OPEX_MEUR_y") / t, "Table 7 (SI Table S19: 142.08)", "same formula (Eq. 24)"),
        B(c1, "TOTAL", a["cost_eur_t"], ref("CAMPOS22", "NPC_MEUR_y") / t, "Table 7 (text 920)", "calibration identity"),
        B(c1 + ", with catalyst term (18.1 EUR/kg, 3 y)", "catalyst replacement", a_cat["cat_eur_t"],
          ref("CAMPOS22", "catalyst_cost_MEUR_y") / t, "SI Table S19", "same 2869 t, 18.1 EUR/kg, 3 y"),
    ]
    c3 = dict(X=0.539, SMeOH=0.998, SCH4=0.0, SCO=0.002)
    kw3 = dict(STY_per_g_cat=M.PROD_TPH / ref("CAMPOS22_3S", "catalyst_t"), P_bar=70.0, h2_co2=3.0, purge=0.02,
               T_C=258.5, x_co="recycled_central")
    b, _ = run(c3, **kw3)
    b_cat, _ = run(c3, cat_term=V.CAT_REF, **kw3)
    c2 = "B2 Campos 2022 three-step (out-of-sample design, same price basis; SI Table S19)"
    rows += [
        B(c2, "H2", b["h2_eur_t"], ref("CAMPOS22_3S", "H2_cost_MEUR_y") / t, "SI: 742.51",
          f"x {h2_stream:.4f} for N2 = {b['h2_eur_t'] * h2_stream:.1f}"),
        B(c2, "CO2", b["co2_eur_t"], ref("CAMPOS22_3S", "CO2_cost_MEUR_y") / t, "SI: 72.30", ""),
        B(c2, "catalyst replacement (with catalyst term)", b_cat["cat_eur_t"],
          ref("CAMPOS22_3S", "catalyst_cost_MEUR_y") / t, "SI: 8.65", ""),
        B(c2, "electricity", b["elec_eur_t"], ref("CAMPOS22_3S", "power_cost_MEUR_y") / t, "SI: 15.72 (net)", ""),
        B(c2, "EC (M EUR)", b["EC_MEUR"], ref("CAMPOS22_3S", "EC_MEUR"), "Table 7",
          "model topology has no intermediate condensers / flash drums"),
        B(c2, "ACC", b["acc_eur_t"], ref("CAMPOS22_3S", "ACC_MEUR_y") / t, "Table 7", ""),
        B(c2, "TOTAL", b["cost_eur_t"], ref("CAMPOS22_3S", "NPC_MEUR_y") / t, "Table 7 (text 868)", ""),
        B(c2, "TOTAL with catalyst term", b_cat["cost_eur_t"], ref("CAMPOS22_3S", "NPC_MEUR_y") / t, "Table 7", ""),
        B(c2, "saving vs one-step", a["cost_eur_t"] - b["cost_eur_t"],
          (ref("CAMPOS22", "NPC_MEUR_y") - ref("CAMPOS22_3S", "NPC_MEUR_y")) / t, "Table 7",
          "catalyst halved: 7.5 EUR/t in the reference, constant in the canonical model"),
        B(c2, "saving vs one-step, with catalyst term", a_cat["cost_eur_t"] - b_cat["cost_eur_t"],
          (ref("CAMPOS22", "NPC_MEUR_y") - ref("CAMPOS22_3S", "NPC_MEUR_y")) / t, "Table 7", ""),
        B(c2, "recycle (kmol/h)", b["recycle_kmol_h"], ref("CAMPOS22_3S", "recycle_kmol_h"), "Table 6", ""),
        B(c2, "purge (kmol/h)", b["purge_kmol_h"], ref("CAMPOS22_3S", "purge_kmol_h_SI"), "SI Table S11", ""),
    ]
    out = {"anchor": a, "three_step": b, "three_step_cat": b_cat}

    def own(key, with_cat=True):
        p = tp[key]
        kw = dict(p["kw"], **p["econ"])
        if with_cat and p["cat"]:
            kw["cat_term"] = p["cat"]
        return run(p["c"], **kw)[0]

    # B3 Perez-Fortes 2016 (primary)
    pf = own("PF")
    pf_nocat = own("PF", with_cat=False)
    out["perez_fortes"] = pf
    c4 = "B3 Perez-Fortes 2016 at its own point and assumptions (primary; catalyst 95.24 EUR/kg, 1 y)"
    pf_cap = ref("PEREZFORTES16", "breakeven_MeOH_price_eur_t") - ref("PEREZFORTES16", "production_cost_no_capital_eur_t")
    rows += [
        B(c4, "H2", pf["h2_eur_t"], 0.959 * 283e6 / 440.8e3, "raw materials 95.9 % of VCP 283 M EUR/a",
          f"H2 use: model {pf['h2_t_per_t']:.4f} vs 0.199 t/t"),
        B(c4, "electricity + utilities", pf["elec_eur_t"], 0.026 * 283e6 / 440.8e3, "utilities 2.6 % of VCP (net power)",
          "model: compressors only, no turbine credit"),
        B(c4, "catalyst replacement", pf["cat_eur_t"], 0.015 * 283e6 / 440.8e3, "consumables 1.5 % of VCP",
          "44.5 t x 95.24 EUR/kg / 1 y in both"),
        B(c4, "capital (annuity at 8 %, 20 y)", pf["acc_eur_t"], pf_cap,
          "breakeven 723.6 minus VCP + FCP 666.05", "model FCI at 55.1 t/h vs TFCC 200 M EUR (see capex_scale.csv)"),
        B(c4, "fixed O&M", pf["fixed_indirect_eur_t"], ref("PEREZFORTES16", "FCP_eur_t"), "FCP 24.57",
          "model: anchor convention (labour + 0.081 FCI)"),
        B(c4, "residual direct + 10 % of NPC (anchor convention)", pf["residual_direct_eur_t"] + pf["revenue_linked_eur_t"],
          0.0, "no such terms in the reference", "common to every catalyst"),
        B(c4, "TOTAL, anchor convention", pf["cost_eur_t"], ref("PEREZFORTES16", "breakeven_MeOH_price_eur_t"),
          "NPV = 0 breakeven price (Table 5)", ""),
        B(c4, "TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)", lean(pf) + 24.57,
          ref("PEREZFORTES16", "breakeven_MeOH_price_eur_t"), "Table 5", ""),
        B(c4, "TOTAL, like-for-like, catalyst in residual (canonical)", lean(pf_nocat) + 24.57,
          ref("PEREZFORTES16", "breakeven_MeOH_price_eur_t"), "Table 5", ""),
    ]
    # B4 Szima 2018 (primary)
    sz = own("SZ")
    out["szima"] = sz
    c5 = "B4 Szima 2018 at its own point and assumptions (H2 = electrolysis electricity 3204 EUR/t; CO2 credit 10 EUR/t)"
    rows += [
        B(c5, "H2 (electrolysis electricity)", sz["h2_eur_t"], 0.92 * 670.49, "92 % of VOC is electricity",
          "Szima VOC electricity also nets the 0.79 MW surplus"),
        B(c5, "CO2", sz["co2_eur_t"], -10 * 1.41, "ETS credit 0.01 EUR/kg x 1.41 t/t (revenue)", ""),
        B(c5, "catalyst", sz["cat_eur_t"], 0.05 * 670.49, "5 % of VOC", "charge matched by construction"),
        B(c5, "capital (annuity at 8 %, 25 y)", sz["acc_eur_t"], 0.0937 * (55.55 + 4.83) * 10, "CRF x (TFCC + WC)", ""),
        B(c5, "TOTAL, like-for-like (feed + power + catalyst + capital + reference FOC and other VOC)",
          lean(sz) + 115.03 + 0.03 * 670.49, ref("SZIMA18", "cost_eur_t"), "VOC + FOC + capital (derived 842)",
          "model electricity = compression (no ORC / turbine credit)"),
        B(c5, "TOTAL, anchor convention", sz["cost_eur_t"], ref("SZIMA18", "cost_eur_t"), "derived 842", ""),
    ]
    # B5 Nyari 2022: three kinetic models of one plant
    c6 = "B5 Nyari 2022, three kinetic models (X and purge fitted to each model's recycle ratio and yield)"
    lcom = {"NY_Kiss": 823.0, "NY_VD": 885.0, "NY_Slotboom": 801.0}
    ny = {k: own(k) for k in lcom}
    out["nyari"] = {k: dict(X=tp[k]["c"]["X"], purge=tp[k]["kw"]["purge"], **{m: v[m] for m in (
        "cost_eur_t", "h2_t_per_t", "co2_t_per_t", "elec_MWh_t", "recycle_ratio", "carbon_efficiency")})
                    for k, v in ny.items()}
    for k, v in ny.items():
        rows.append(B(c6, f"{k[3:]}: like-for-like (feed + power + capital + reference fixed ~26)", lean(v) + 26.0,
                      lcom[k], "LCoM, Fig. 6", f"fitted X {tp[k]['c']['X']:.3f}, purge {tp[k]['kw']['purge']:.4f}; "
                                               f"H2 {v['h2_t_per_t']:.4f} t/t"))
    rows.append(B(c6, "VD minus Slotboom (kinetic-model spread)", lean(ny["NY_VD"]) - lean(ny["NY_Slotboom"]),
                  lcom["NY_VD"] - lcom["NY_Slotboom"], "Fig. 6",
                  "same plant and prices; only the catalyst kinetics differ"))
    rows.append(B(c6, "Kiss minus Slotboom", lean(ny["NY_Kiss"]) - lean(ny["NY_Slotboom"]),
                  lcom["NY_Kiss"] - lcom["NY_Slotboom"], "Fig. 6", ""))
    # B6 Nieminen 2019 gas-phase case
    ni = own("NI")
    out["nieminen"] = ni
    c7 = "B6 Nieminen 2019 gas-phase case at its own point and assumptions"
    rows += [
        B(c7, "H2", ni["h2_eur_t"], 703.0, "0.234 t/t x 3000 (derived)",
          f"model H2 {ni['h2_t_per_t']:.4f} t/t: the reference loses 89 kg/h H2 and 560 kg/h CO2 in flash gases "
          f"(carbon efficiency 0.805 vs model {ni['carbon_efficiency']:.3f})"),
        B(c7, "CO2", ni["co2_eur_t"], 85.0, "1.706 x 50 (derived)", ""),
        B(c7, "TOTAL, like-for-like (+ reference fixed 150, CW 43, steam credit -50)", lean(ni) + 150 + 43 - 50,
          1028.0, "production cost without the O2 credit (p18)", ""),
    ]
    # B7 Schorn 2021 NPC grid
    c8 = "B7 Schorn 2021 Table 2 grid (300 MW, 8 %, 20 y, electricity 97.6 EUR/MWh)"
    for (h2, co2, val) in ((1000.0, 0.0, 254.0), (3000.0, 40.0, 691.0), (4500.0, 0.0, 921.0)):
        sc = run(tp["SC"]["c"], **dict(tp["SC"]["kw"], **tp["SC"]["econ"], h2_price=h2, co2_price=co2))[0]
        rows.append(B(c8, f"H2 {h2 / 1000:g} EUR/kg, CO2 {co2:g} EUR/t: like-for-like (feed + power + capital + "
                          f"reference O&M 33.9)", lean(sc) + 33.9, val, "Table 2 cell; O&M = intercept 63 - capital 14.1 - power 15.0",
                      f"model H2 {sc['h2_t_per_t']:.4f} vs 0.189 t/t (Schorn: no purge, 100 % carbon efficiency)"))
    df = pd.DataFrame(rows)
    df["deviation"] = df.model - df.reference
    df["deviation_pct"] = 100 * df.deviation / df.reference
    return df, out


def capex_scale(tp):
    """Specific fixed capital of the model (each reference's own operating point and cost year) vs reported."""
    pts = [
        ("Campos 2022 one-step (anchor; FCI)", ANCHOR, dict(ANCHOR_KW), ref("CAMPOS22", "FCI_MEUR") * 1e6 / ANCHOR_TPY,
         "EUR2020"),
        ("Campos 2022 three-step (FCI)", dict(X=0.539, SMeOH=0.998, SCH4=0.0, SCO=0.002),
         dict(STY_per_g_cat=M.PROD_TPH / 1434.4, P_bar=70.0, h2_co2=3.0, purge=0.02, T_C=258.5,
              x_co="recycled_central"), ref("CAMPOS22_3S", "FCI_MEUR") * 1e6 / ANCHOR_TPY, "EUR2020"),
        ("Perez-Fortes 2016 (TFCC 200 M EUR)", tp["PF"]["c"], dict(tp["PF"]["kw"], **tp["PF"]["econ"]),
         200e6 / 440.8e3, "EUR2014"),
        ("Szima 2018 (TFCC 55.55 M EUR, electrolyser excluded)", tp["SZ"]["c"], dict(tp["SZ"]["kw"], **tp["SZ"]["econ"]),
         55.55e6 / 100e3, "EUR2017"),
        ("Schorn 2021 (FCI 60 M EUR, synthesis)", tp["SC"]["c"], dict(tp["SC"]["kw"], **tp["SC"]["econ"]),
         60e6 / 434e3, "EUR (year n.s.)"),
        ("Nieminen 2019 gas phase (TCI 10.5-17.9 M EUR)", tp["NI"]["c"], dict(tp["NI"]["kw"], **tp["NI"]["econ"]),
         17.9e6 / (2.275 * 7250), "EUR2018 (17.9 M EUR caption value)"),
        ("CRI Shunli 2022 (design + equipment, USD 90 M)", ANCHOR, dict(ANCHOR_KW, prod_tph=110000 / 8000.0),
         818.0 / 1.0530, "EUR2022 (USD/1.053)"),
        ("Bos 2020 methanol section (condensing reactor)", ANCHOR, dict(ANCHOR_KW, prod_tph=65000 / 8000.0), 169.0, "EUR"),
        ("Hank 2018 (input assumption)", ANCHOR, dict(ANCHOR_KW, prod_tph=4188 / 8000.0), 810.0, "EUR2018"),
    ]
    rows = []
    for name, c, kw, refv, basis in pts:
        r = run(c, **kw)[0]
        tpa = kw.get("prod_tph", M.PROD_TPH) * kw.get("hours", M.HOURS_Y)
        rows.append(dict(reference=name, capacity_t_a=tpa, model_FCI_MEUR=r["FCI_MEUR"],
                         model_FCI_eur_per_tpa=r["FCI_MEUR"] * 1e6 / tpa, model_EC_eur_per_tpa=r["EC_MEUR"] * 1e6 / tpa,
                         reference_eur_per_tpa=refv, reference_basis=basis,
                         ratio_model_FCI_to_reference=r["FCI_MEUR"] * 1e6 / tpa / refv))
    return pd.DataFrame(rows)


ANN = M.LF * (M.CRF + M.IR / 9.0 + 0.081) / 0.90      # EUR/a of NPC per EUR of equipment cost
GROUPS_EC = {"reactor (catalyst inventory)": ["Reactor modules"],
             "recycle-flow equipment (recycle compressor, preheaters, HX, flash)":
                 ["Recycle/reflux compressor", "Reactor preheaters", "Heat exchangers", "Flash drums"],
             "feed compressors": ["Carbon dioxide compressor", "Hydrogen compressor"],
             "purge equipment (furnace, turbine)": ["Furnace & blower", "Turbine & generator"],
             "distillation + pump": ["Distillation column", "Pump"]}


def decompose(row, **kw):
    """NPC of one literature candidate split into terms (EUR/t), all including the 1/0.9 revenue-linked mark-up."""
    c = dict(X=row.X, SMeOH=row.SMeOH, SCH4=row.SCH4, SCO=row.SCO)
    X = row.X_eff_recycled_opt if np.isfinite(row.X_eff_recycled_opt) else row.X   # conversion at the chosen purge
    r = V.economics(X, c["SMeOH"], c["SCH4"], c["SCO"], STY_per_g_cat=row.STY, P_bar=row.P_bar,
                    h2_co2=row.h2_co2, T_C=row.T_C, x_co="recycled_central", purge=row.purge_recycled_opt, **kw)
    per_t = 1e6 / ANCHOR_TPY
    out = {"feed H2 + CO2 (selectivity and purge losses)": float(r["h2_eur_t"] + r["co2_eur_t"]) / 0.9,
           "electricity: recycle compression": float(r["P_rec_MW"]) * M.HOURS_Y * M.ELEC_EUR_MWH / 1e6 * per_t / 0.9,
           "electricity: feed compression": float(r["P_co2_MW"] + r["P_h2_MW"]) * M.HOURS_Y * M.ELEC_EUR_MWH / 1e6 * per_t / 0.9,
           "catalyst replacement": float(r["cat_eur_t"]) / 0.9}
    for g, items in GROUPS_EC.items():
        out["capital: " + g] = sum(float(r["ec"][i]) for i in items) * ANN * per_t
    out["total"] = float(r["cost_eur_t"])
    return out


def driver_decomposition():
    """Cost gap (paper STY winner minus plant-cost winner) of the 33 mismatched groups, by term."""
    cand = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / "literature_candidates.csv")
    gm = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / "group_metrics.csv")
    mm = gm[gm.top1_mismatch]
    rows = []
    for basis, kw in (("canonical", {}), ("with catalyst replacement 18.1 EUR/kg, 3 y", dict(cat_term=V.CAT_REF)),
                      ("industrial loop: catalyst 3 y + loop dP 3.75 bar + recycle x2.68",
                       dict(cat_term=V.CAT_REF, loop_dp=3.75, recycle_mult=2.68)),
                      ("primary-source weights: catalyst 95.24 EUR/kg 1 y + loop dP 4.2 bar + recycle costs x10 "
                       "(Nyari spread)", dict(cat_term=(95.24, 1.0), loop_dp=4.2, recycle_mult=10.0))):
        for g in mm.itertuples():
            sub = cand[cand.group == g.group]
            up = sub[sub.catalyst == g.upstream_winner].iloc[0]
            ec = sub[sub.catalyst == g.economic_winner].iloc[0]
            du, de = decompose(up, **kw), decompose(ec, **kw)
            rows.append(dict(basis=basis, group=g.group, **{k: du[k] - de[k] for k in du}))
    d = pd.DataFrame(rows)
    terms = [c for c in d.columns if c not in ("basis", "group", "total")]
    agg = []
    for basis, s in d.groupby("basis", sort=False):
        tot = s["total"].sum()
        pos = s[terms].clip(lower=0).sum()
        assert float((s.total - s[terms].sum(axis=1)).abs().max()) < 1e-6
        agg.append(dict(basis=basis, groups=len(s), median_gap_eur_t=float(s.total.median()),
                        **{f"median_term_eur_t: {k}": float(s[k].median()) for k in terms},
                        **{f"share_of_summed_gap: {k}": float(s[k].sum() / tot) for k in terms},
                        **{f"groups_where_largest: {k}": int((s[terms].idxmax(axis=1) == k).sum()) for k in terms}))
    return d, pd.DataFrame(agg)


def main():
    gate = V.check_identity(300)
    assert gate < 1e-8, gate
    tp = tea_points()
    cases = model_cases(tp)
    ta, res = table_a(cases)
    ta.to_csv(HERE / "reconciliation_plant.csv", index=False)
    mr = metric_ranges(res)
    mr.to_csv(HERE / "plant_metric_ranges.csv", index=False, float_format="%.4g")
    print(mr.to_string())
    tb, bres = table_b(tp)
    tb.to_csv(HERE / "reconciliation_cost.csv", index=False, float_format="%.4g")
    cs = capex_scale(tp)
    cs.to_csv(HERE / "capex_scale.csv", index=False, float_format="%.4g")
    dd, dagg = driver_decomposition()
    dd.to_csv(HERE / "mismatch_driver_decomposition.csv", index=False, float_format="%.4g")
    dagg.to_csv(HERE / "mismatch_driver_shares.csv", index=False, float_format="%.4g")
    print(dagg.T.to_string())
    sens = json.loads((HERE / "sensitivity_summary.json").read_text(encoding="utf-8"))
    a = res["M1 anchor one-step (calibration point)"]
    summary = dict(
        identity_gate_max_abs_eur_t=gate,
        model_cases={k: {m: (round(v, 6) if isinstance(v, float) else v) for m, v in r.items()
                         if m in ("cost_eur_t", "X", "purge", "recycle_ratio", "h2_t_per_t", "co2_t_per_t",
                                  "carbon_efficiency", "elec_MWh_t", "catalyst_t", "GHSV_h", "STY_kg_L_h",
                                  "purge_kmol_h", "recycle_kmol_h", "feed_share", "H2_share", "CO2_share",
                                  "ACC_share", "P_bar", "T_C", "STY_per_g_cat")}
                     for k, r in res.items()},
        anchor_cost_breakdown_eur_t={k: round(a[k], 3) for k in ("h2_eur_t", "co2_eur_t", "elec_eur_t", "acc_eur_t",
                                                                   "residual_direct_eur_t", "fixed_indirect_eur_t",
                                                                   "revenue_linked_eur_t", "cost_eur_t")},
        three_step_out_of_sample={k: round(float(bres["three_step"][k]), 3) for k in
                                  ("cost_eur_t", "EC_MEUR", "FCI_MEUR", "acc_eur_t", "recycle_kmol_h", "purge_kmol_h",
                                   "carbon_efficiency", "h2_t_per_t", "co2_t_per_t")},
        perez_fortes_primary={k: round(float(bres["perez_fortes"][k]), 3) for k in
                              ("cost_eur_t", "h2_eur_t", "co2_eur_t", "elec_eur_t", "acc_eur_t", "cat_eur_t",
                               "FCI_MEUR", "h2_t_per_t", "co2_t_per_t", "carbon_efficiency", "recycle_ratio")},
        perez_fortes_like_for_like_eur_t=round(float(lean(bres["perez_fortes"]) + 24.57), 2),
        szima={k: round(float(bres["szima"][k]), 3) for k in ("cost_eur_t", "h2_eur_t", "acc_eur_t", "FCI_MEUR")},
        szima_like_for_like_eur_t=round(float(lean(bres["szima"]) + 115.03 + 0.03 * 670.49), 2),
        nyari=bres["nyari"],
        nieminen={k: round(float(bres["nieminen"][k]), 4) for k in ("cost_eur_t", "h2_t_per_t", "co2_t_per_t",
                                                                    "carbon_efficiency", "recycle_ratio")},
        capex_scale=cs.to_dict(orient="records"),
        sensitivity={k: dict(top1=f"{v['top1_mismatch_groups']}/{v['groups']}", papers=v["papers_with_mismatch"],
                             inversions=v["pairwise_inversions"],
                             regret_median_mismatched=round(v["regret_median_mismatched"], 4),
                             groups_flipped=v["groups_flipped_vs_baseline"],
                             economic_winner_changed=v["groups_economic_winner_changed"], knobs=v["knobs"])
                     for k, v in sens["variants"].items()},
        sensitivity_check=sens["check"],
        mismatch_driver_shares=dagg.to_dict(orient="records"),
        plant_metric_ranges=mr.to_dict(orient="records"),
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 60)
    print(ta.drop(columns="references").to_string())
    print(tb[["case", "term", "model", "reference", "deviation", "deviation_pct"]].to_string())
    print(cs.to_string())


if __name__ == "__main__":
    main()
