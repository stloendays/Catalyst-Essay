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


def model_cases():
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
    # Lurgi CO2 pilot operating point: X mid of 35-45 %, purge set to the mid carbon efficiency 95.25 %,
    # catalyst from GHSV 10 500 1/h; selectivity as the anchor (by-products < 0.05 wt%)
    lc = dict(X=0.40, SMeOH=0.995, SCH4=0.0, SCO=0.005)
    lkw = dict(P_bar=80.0, h2_co2=3.0, T_C=250.0, x_co="recycled_central")
    p = purge_for_ce(lc, 0.9525, STY_per_g_cat=1.0, **lkw)
    lkw.update(purge=p)
    lkw["STY_per_g_cat"] = sty_for_ghsv(lc, 10500.0, **{k: v for k, v in lkw.items()})
    cases["M5 at Lurgi CO2-pilot conditions (80 bar, X 0.40, CE 95.25 %)"] = (lc, lkw)
    # Gonzalez-Garay 2019 operating point: 50 bar, 225 C, X mid 14.1 %, S 0.99, carbon efficiency 91.5 %
    gc = dict(X=0.141, SMeOH=0.99, SCH4=0.0, SCO=0.01)
    gkw = dict(P_bar=50.0, h2_co2=3.0, T_C=224.5, x_co="recycled_central", STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T)
    gkw["purge"] = purge_for_ce(gc, 0.915, **gkw)
    cases["M6 at Gonzalez-Garay conditions (50 bar, X 0.141, CE 91.5 %)"] = (gc, gkw)
    # Perez-Fortes 2016 operating point (secondary values): 78 bar, 210 C, X 0.22, 2 % purge, 55 t/h
    pc = dict(X=0.22, SMeOH=0.995, SCH4=0.0, SCO=0.005)
    pkw = dict(P_bar=78.0, h2_co2=3.0, T_C=210.0, x_co="recycled_central", purge=0.02,
               STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T)
    cases["M7 at Perez-Fortes 2016 conditions (78 bar, X 0.22; secondary)"] = (pc, pkw)
    return cases


PLANT_ROWS = [
    # (label, model key, reference cells builder)
    ("Loop pressure (bar)", "P_bar"),
    ("Reactor / coolant T (C)", "T_C"),
    ("Reactor-inlet H2/CO2 (mol/mol)", "H2_CO2_inlet"),
    ("Fresh-feed H2/CO2 (mol/mol)", "fresh_h2_co2"),
    ("Per-pass CO2 conversion", "X"),
    ("Recycle ratio (recycle / fresh feed, mol)", "recycle_ratio"),
    ("Purge fraction of separator gas", "purge"),
    ("Purge flow (kmol/h, at 145 t/h)", "purge_kmol_h"),
    ("H2 consumption (t/t MeOH)", "h2_t_per_t"),
    ("CO2 consumption (t/t MeOH)", "co2_t_per_t"),
    ("Carbon efficiency (MeOH C / fresh CO2)", "carbon_efficiency"),
    ("Electricity, compression (MWh/t)", "elec_MWh_t"),
    ("Catalyst inventory (t, at 145 t/h)", "catalyst_t"),
    ("GHSV (1/h, bed density 1.05 t/m3)", "GHSV_h"),
    ("STY (kg MeOH / L cat / h)", "STY_kg_L_h"),
    ("Catalyst lifetime (y)", None),
    ("Loop pressure drop (bar)", None),
]

REFERENCE_CELLS = {
    "Loop pressure (bar)": "Campos 70 | 3-step 70 | Ott/Dieterich 50-100 | Lurgi pilot 80 | Mitsui 50 | CRI Olah 101 | "
                           "Gonzalez-Garay 50 | Hank 40 | Bos 50 | Rihko 50 | Perez-Fortes* 78",
    "Reactor / coolant T (C)": "Campos 247.5 | 3-step 258.5 | Ott/Dieterich 200-300 | Lurgi pilot 250 | CRI Olah 250 | "
                               "Gonzalez-Garay 221-228 | Bos 240 | Rihko 220 | Perez-Fortes* 210",
    "Reactor-inlet H2/CO2 (mol/mol)": "Campos 3.26 (reactor feed)",
    "Fresh-feed H2/CO2 (mol/mol)": "Campos 3.0 | Rihko 3.0 | Gonzalez-Garay slightly < 3 | Dieterich optimum 3",
    "Per-pass CO2 conversion": "Campos 0.285 | 3-step 0.539 | Lurgi pilot 0.35-0.45 | conventional SRC 0.36 (<0.40) | "
                               "Gonzalez-Garay 0.124-0.158 | Perez-Fortes* 0.22 | Szima* 0.30",
    "Recycle ratio (recycle / fresh feed, mol)": "Campos 2.81 | 3-step 1.21 | conventional loops 3-5 (Dieterich, Hansen) | "
                                                 "Lurgi SRC 3-4 | MegaMethanol 2-2.7 | Lurgi CO2 pilot 4.5 | "
                                                 "Mitsui pilot 2.6-3.2 | Rihko 3.2",
    "Purge fraction of separator gas": "Campos 0.02 | Mitsui pilot 7-10 % of reactor inlet | LPMeOH 2-6 % of recycle",
    "Purge flow (kmol/h, at 145 t/h)": "Campos 1100 | 3-step 455",
    "H2 consumption (t/t MeOH)": "stoichiometric 0.189 | Campos 0.200 (Table 6) / 0.214 (Fig. 11b H2 bar) | "
                                 "3-step 0.193 | Hank 0.189-0.193 | Rihko 0.197",
    "CO2 consumption (t/t MeOH)": "stoichiometric 1.374 | Campos 1.457 | 3-step 1.406 | CRI Olah 1.375-1.40 | "
                                  "CRI Shunli 1.455 | Hank 1.511-1.526 | Rihko 1.436 | Bos 1.385 | Dieterich 1.43 at 96 %",
    "Carbon efficiency (MeOH C / fresh CO2)": "Campos 0.943 | 3-step 0.977 | conventional 0.93-0.98 | "
                                              "Lurgi CO2 pilot 0.940-0.965 | Rihko 0.968 | Gonzalez-Garay > 0.915 | "
                                              "Hank 0.90",
    "Electricity, compression (MWh/t)": "Campos gross 0.327 / net 0.121 (whole plant) | 3-step 0.294 / 0.150 | "
                                        "Bos feed compressors 0.22 | Rihko 1.33 (97 kg/h, feed from 1 bar)",
    "Catalyst inventory (t, at 145 t/h)": "Campos 2868.8 | 3-step 1434.4",
    "GHSV (1/h, bed density 1.05 t/m3)": "Campos 604 | SRC 6000-12000 | Lurgi CO2 pilot 10500 | Mitsui 10000",
    "STY (kg MeOH / L cat / h)": "Campos 0.053 | CO2 feed 0.4-0.8 (Dieterich) | syngas 0.7-2.3",
    "Catalyst lifetime (y)": "Campos 3 | Ott 2-5 | Dieterich 4-6 (up to 8)",
    "Loop pressure drop (bar)": "Dieterich: Lurgi SRC loop 3.5-4, Toyo loop 3; Campos 0.75 per reactor module",
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
    rows.append({"metric": "Net production cost (EUR/t, anchor prices)",
                 **{k: round(r["cost_eur_t"], 2) for k, r in res.items()},
                 "references": "Campos 920 (Table 7: 1071.8 M EUR/a = 924.0) | 3-step 868 (871.2)"})
    return pd.DataFrame(rows), res


# ------------------------------------------------------------------ Table B ------------------------------------
def table_b():
    rows = []
    a, _ = run(ANCHOR, **ANCHOR_KW)
    t = ANCHOR_TPY / 1e6  # Mt/a
    fig = dict(h2=ref("CAMPOS22", "H2_cost_MEUR_y"), co2=ref("CAMPOS22", "CO2_cost_MEUR_y"),
               cat=ref("CAMPOS22", "catalyst_cost_MEUR_y"), pw=ref("CAMPOS22", "power_cost_MEUR_y"))
    anchor_cat_eur_t = V.ANCHOR_CAT_REPL_MEUR_Y / t
    rows += [
        dict(case="B1 Campos 2022 one-step (calibration point; model prices = reference prices)", term="H2",
             model=a["h2_eur_t"], reference=fig["h2"] / t, ref_basis="Fig. 11b bar reading (+/- 3 M EUR/a)",
             attribution="model H2 0.1985 t/t vs 0.214 t/t implied by the bar; Table-6 feed excess gives 0.200 t/t "
                         "(model -0.8 %). The gap is carried by the constant residual, so the level is reproduced"),
        dict(case="B1", term="CO2", model=a["co2_eur_t"], reference=fig["co2"] / t, ref_basis="Fig. 11b",
             attribution="CO2 1.449 vs 1.457 t/t (Table 6)"),
        dict(case="B1", term="electricity", model=a["elec_eur_t"], reference=fig["pw"] / t,
             ref_basis="Fig. 11b (net power after Rankine credit; 17.6 MW x 90 EUR/MWh = 10.9 EUR/t)",
             attribution="model counts compressors only (28.9 MW) and no Rankine credit; difference sits in the residual"),
        dict(case="B1", term="catalyst replacement", model=0.0, reference=fig["cat"] / t,
             ref_basis=f"Fig. 11b; inputs give {anchor_cat_eur_t:.1f} EUR/t (2868.8 t x 18.1 EUR/kg / 3 y)",
             attribution="model: inside the catalyst-independent residual (no inventory dependence)"),
        dict(case="B1", term="other direct (residual)", model=a["residual_direct_eur_t"],
             reference=ref("CAMPOS22", "direct_OPEX_MEUR_y") / t - (fig["h2"] + fig["co2"] + fig["cat"] + fig["pw"]) / t,
             ref_basis="Table 7 direct OPEX minus Fig. 11b bars", attribution="constant by construction"),
        dict(case="B1", term="ACC (CAPEX annuity)", model=a["acc_eur_t"], reference=ref("CAMPOS22", "ACC_MEUR_y") / t,
             ref_basis="Table 7", attribution="same EC, Lang factor and annuity"),
        dict(case="B1", term="indirect OPEX", model=a["cost_eur_t"] - a["acc_eur_t"] - a["direct_MEUR_Y"] * 1e6 / ANCHOR_TPY,
             reference=ref("CAMPOS22", "indirect_OPEX_MEUR_y") / t, ref_basis="Table 7", attribution="same formula (Eq. 24)"),
        dict(case="B1", term="TOTAL", model=a["cost_eur_t"], reference=ref("CAMPOS22", "NPC_MEUR_y") / t,
             ref_basis="Table 7 (text: 920 EUR/t)", attribution="calibration identity; -0.03 % with CO recycled"),
    ]
    # B2: three-step design with the same prices (out of sample)
    c3 = dict(X=0.539, SMeOH=0.998, SCH4=0.0, SCO=0.002)
    kw3 = dict(STY_per_g_cat=M.PROD_TPH / ref("CAMPOS22_3S", "catalyst_t"), P_bar=70.0, h2_co2=3.0, purge=0.02,
               T_C=258.5, x_co="recycled_central")
    b, _ = run(c3, **kw3)
    b_cat, _ = run(c3, cat_term=V.CAT_REF, **kw3)
    a_cat, _ = run(ANCHOR, cat_term=V.CAT_REF, **ANCHOR_KW)
    rows += [
        dict(case="B2 Campos 2022 three-step (out-of-sample design, same price basis)", term="EC (M EUR)",
             model=b["EC_MEUR"], reference=ref("CAMPOS22_3S", "EC_MEUR"), ref_basis="Table 7",
             attribution="model topology has no intermediate condensers / flash drums"),
        dict(case="B2", term="FCI (M EUR)", model=b["FCI_MEUR"], reference=ref("CAMPOS22_3S", "FCI_MEUR"),
             ref_basis="Table 7", attribution=""),
        dict(case="B2", term="ACC", model=b["acc_eur_t"], reference=ref("CAMPOS22_3S", "ACC_MEUR_y") / t,
             ref_basis="Table 7", attribution=""),
        dict(case="B2", term="direct OPEX", model=b["direct_MEUR_Y"] * 1e6 / ANCHOR_TPY,
             reference=ref("CAMPOS22_3S", "direct_OPEX_MEUR_y") / t, ref_basis="Table 7",
             attribution="feed saving from the higher carbon efficiency; catalyst halved (in residual in the model)"),
        dict(case="B2", term="indirect OPEX", model=b["cost_eur_t"] - b["acc_eur_t"] - b["direct_MEUR_Y"] * 1e6 / ANCHOR_TPY,
             reference=ref("CAMPOS22_3S", "indirect_OPEX_MEUR_y") / t, ref_basis="Table 7", attribution=""),
        dict(case="B2", term="TOTAL", model=b["cost_eur_t"], reference=ref("CAMPOS22_3S", "NPC_MEUR_y") / t,
             ref_basis="Table 7 (text: 868 EUR/t)", attribution=""),
        dict(case="B2", term="saving vs one-step (EUR/t)", model=a["cost_eur_t"] - b["cost_eur_t"],
             reference=(ref("CAMPOS22", "NPC_MEUR_y") - ref("CAMPOS22_3S", "NPC_MEUR_y")) / t, ref_basis="Table 7",
             attribution="direction and size of the conversion benefit"),
        dict(case="B2 with explicit catalyst term (18.1 EUR/kg, 3 y)", term="saving vs one-step (EUR/t)",
             model=a_cat["cost_eur_t"] - b_cat["cost_eur_t"],
             reference=(ref("CAMPOS22", "NPC_MEUR_y") - ref("CAMPOS22_3S", "NPC_MEUR_y")) / t, ref_basis="Table 7",
             attribution="the halved catalyst charge (6 -> 3 modules) is a reference cost the canonical model keeps "
                         "constant"),
        dict(case="B2 with explicit catalyst term (18.1 EUR/kg, 3 y)", term="TOTAL", model=b_cat["cost_eur_t"],
             reference=ref("CAMPOS22_3S", "NPC_MEUR_y") / t, ref_basis="Table 7", attribution=""),
        dict(case="B2", term="recycle (kmol/h)", model=b["recycle_kmol_h"], reference=ref("CAMPOS22_3S", "recycle_kmol_h"),
             ref_basis="Table 6", attribution=""),
        dict(case="B2", term="purge (kmol/h)", model=b["purge_kmol_h"], reference=ref("CAMPOS22_3S", "purge_kmol_h"),
             ref_basis="text p18", attribution=""),
    ]
    # B3: Perez-Fortes 2016 price set (secondary values), at its scale and operating point
    pc = dict(X=0.22, SMeOH=0.995, SCH4=0.0, SCO=0.005)
    prod = 440000.0 / 8000.0
    common = dict(P_bar=78.0, h2_co2=3.0, T_C=210.0, x_co="recycled_central", purge=0.02,
                  STY_per_g_cat=M.PROD_TPH / ANCHOR_CAT_T)
    p_own, _ = run(pc, h2_price=3090.0, co2_price=0.0, elec_price=95.1, prod_tph=prod, hours=8000.0, **common)
    p_anchor, _ = run(pc, **common)
    rows += [
        dict(case="B3 Perez-Fortes 2016 prices, scale and operating point (secondary values; primary pending)",
             term="TOTAL", model=p_own["cost_eur_t"], reference=ref("PEREZFORTES16", "cost_eur_t"),
             ref_basis="Dieterich 2020 Table 12", attribution=""),
        dict(case="B3", term="H2", model=p_own["h2_eur_t"], reference=np.nan,
             ref_basis="H2 3090 EUR/t (Mbatha Table 15)", attribution="breakdown not available without the primary"),
        dict(case="B3", term="CO2", model=p_own["co2_eur_t"], reference=0.0, ref_basis="0 EUR/t (Dieterich Table 12)",
             attribution=""),
        dict(case="B3", term="electricity", model=p_own["elec_eur_t"], reference=np.nan, ref_basis="95.1 EUR/MWh",
             attribution=""),
        dict(case="B3", term="FCI (M EUR)", model=p_own["FCI_MEUR"], reference=ref("PEREZFORTES16", "capex_per_tpd") * 1300 / 1e6,
             ref_basis="181 kEUR/(t/d) x 1300 t/d (Dieterich Table 12)", attribution="see capex_scale.csv"),
        dict(case="B3", term="ACC", model=p_own["acc_eur_t"], reference=np.nan, ref_basis="", attribution=""),
        dict(case="B3", term="residual direct OPEX (anchor convention)", model=p_own["residual_direct_eur_t"],
             reference=np.nan, ref_basis="", attribution="catalyst-independent constant"),
        dict(case="B3", term="indirect OPEX: labour + 0.081 FCI", model=p_own["fixed_indirect_eur_t"], reference=np.nan,
             ref_basis="", attribution="anchor (Peters/Albrecht) convention"),
        dict(case="B3", term="indirect OPEX: 10 % of NPC", model=p_own["revenue_linked_eur_t"], reference=np.nan,
             ref_basis="", attribution="anchor convention: distribution, selling, R&D"),
        dict(case="B3", term="ACC + electricity (capital and power only)", model=p_own["acc_eur_t"] + p_own["elec_eur_t"],
             reference=ref("PEREZFORTES16", "cost_eur_t") - p_own["h2_t_per_t"] * 3090.0,
             ref_basis="724 minus model H2 tonnage x 3090", attribution="like-for-like with a lean TEA boundary"),
        dict(case="B3", term="all non-feed terms", model=p_own["cost_eur_t"] - p_own["h2_eur_t"] - p_own["co2_eur_t"],
             reference=ref("PEREZFORTES16", "cost_eur_t") - p_own["h2_t_per_t"] * 3090.0,
             ref_basis="724 minus model H2 tonnage x 3090 (assumes the same H2 use)", attribution=""),
        dict(case="B3 (memo) same operating point at anchor prices and scale", term="TOTAL",
             model=p_anchor["cost_eur_t"], reference=np.nan, ref_basis="", attribution="price-basis effect"),
    ]
    df = pd.DataFrame(rows)
    df["deviation"] = df.model - df.reference
    df["deviation_pct"] = 100 * df.deviation / df.reference
    return df, dict(anchor=a, three_step=b, perez_fortes=p_own, perez_fortes_anchor_prices=p_anchor)


def capex_scale():
    """Specific fixed capital of the model (anchor operating point) at each reference scale."""
    pts = [("Campos 2022 one-step (anchor)", 145.0, 8000.0, ref("CAMPOS22", "FCI_MEUR") * 1e6 / ANCHOR_TPY, "EUR2020"),
           ("Perez-Fortes 2016* (CO2 and H2 external)", 55.0, 8000.0, 181000.0 * 1300 / 440000.0, "EUR (year n.s.)"),
           ("CRI Shunli 2022 (design + equipment only)", 110000 / 8000.0, 8000.0, 818.0 / 1.0530, "EUR2022 (USD/1.053)"),
           ("Bos 2020 (methanol section; feed comp. + reactor + distillation)", 65000 / 8000.0, 8000.0, 169.0, "EUR"),
           ("Hank 2018 (methanol synthesis, input assumption)", 4188 / 8000.0, 8000.0, 810.0, "EUR2018"),
           ("CRI George Olah (no cost data)", 4000 / 8000.0, 8000.0, np.nan, "")]
    rows = []
    for name, tph, hours, refv, basis in pts:
        r, _ = run(ANCHOR, **dict(ANCHOR_KW, prod_tph=tph, hours=hours))
        rows.append(dict(reference=name, capacity_t_a=tph * hours, model_FCI_MEUR=r["FCI_MEUR"],
                         model_FCI_eur_per_tpa=r["FCI_MEUR"] * 1e6 / (tph * hours),
                         model_EC_eur_per_tpa=r["EC_MEUR"] * 1e6 / (tph * hours),
                         reference_eur_per_tpa=refv, reference_basis=basis,
                         ratio_model_FCI_to_reference=(r["FCI_MEUR"] * 1e6 / (tph * hours)) / refv if refv == refv else np.nan,
                         ratio_model_EC_to_reference=(r["EC_MEUR"] * 1e6 / (tph * hours)) / refv if refv == refv else np.nan))
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
    r = V.economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], STY_per_g_cat=row.STY, P_bar=row.P_bar,
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
                       dict(cat_term=V.CAT_REF, loop_dp=3.75, recycle_mult=2.68))):
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
    cases = model_cases()
    ta, res = table_a(cases)
    ta.to_csv(HERE / "reconciliation_plant.csv", index=False)
    tb, bres = table_b()
    tb.to_csv(HERE / "reconciliation_cost.csv", index=False, float_format="%.4g")
    cs = capex_scale()
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
        perez_fortes_secondary={k: round(float(bres["perez_fortes"][k]), 3) for k in
                                ("cost_eur_t", "h2_eur_t", "co2_eur_t", "elec_eur_t", "acc_eur_t", "FCI_MEUR")},
        sensitivity={k: dict(top1=f"{v['top1_mismatch_groups']}/{v['groups']}", papers=v["papers_with_mismatch"],
                             inversions=v["pairwise_inversions"],
                             regret_median_mismatched=round(v["regret_median_mismatched"], 4),
                             groups_flipped=v["groups_flipped_vs_baseline"],
                             economic_winner_changed=v["groups_economic_winner_changed"], knobs=v["knobs"])
                     for k, v in sens["variants"].items()},
        sensitivity_check=sens["check"],
        mismatch_driver_shares=dagg.to_dict(orient="records"),
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 60)
    print(ta.drop(columns="references").to_string())
    print(tb[["case", "term", "model", "reference", "deviation", "deviation_pct"]].to_string())
    print(cs.to_string())


if __name__ == "__main__":
    main()
