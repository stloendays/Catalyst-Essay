"""Parameterised copy of `meoh_general_model.economics` for the plant benchmark (2026-10-06).

The frozen models (`data/meoh/meoh_d01_model.py`, `data/meoh/meoh_general_model.py`) are not modified. This module
re-states `meoh_general_model.economics` with every price, scale and finance constant exposed as a keyword, so that
the model can be run with a reference TEA's own assumptions. With all keywords at their defaults it reproduces
`meoh_general_model.economics` to machine precision (`check_identity`, run by `run_benchmark.py`).

Exposed knobs (defaults = canonical engine values):
  h2_price, co2_price          EUR/t (or the reference currency, see fx)
  elec_price                   EUR/MWh
  prod_tph, hours              plant scale; equipment is sized from absolute flows relative to the anchor's 145 t/h
                               flows (same exponents), so a smaller plant pays the usual economy-of-scale penalty
  ir, life                     annuity on FCI; WC = FCI/9 earns interest ir (anchor convention)
  capex_mult                   multiplies EC (currency and CEPCI year conversion of the anchor's EUR-2020 costs)
  opex_mult                    multiplies the catalyst-independent direct residual and operating labour (currency)
  loop_dp                      recycle-compressor pressure ratio (P - loop_dp) -> P
  cat_term                     None (canonical: the anchor's catalyst replacement sits inside the constant residual)
                               or (price per kg, lifetime y): an explicit replacement term catalyst_t * price / life;
                               the anchor's own replacement (SOURCE_CAT_T at CAT_REF) is then taken out of the
                               residual so that the anchor point is unchanged
  lang                         Lang factor (FCI = lang * EC)
  recycle_mult                 multiplies the recycle flow used for recycle compression and for the gas-flow-sized
                               equipment (reactor-inlet flow = fresh + recycle_mult * recycle); purge, feed and
                               species balance unchanged (cost-term sensitivity for loops that circulate more gas)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_d01_model as M  # noqa: E402
import meoh_general_model as G  # noqa: E402

CAT_REF = (18.1, 3.0)          # anchor Table 2: Cu/ZnO/Al2O3 18,100 EUR/t; Section 2.7: catalyst lifetime 3 years
ANCHOR_CAT_REPL_MEUR_Y = M.SOURCE_CAT_T * 1000.0 * CAT_REF[0] / CAT_REF[1] / 1e6   # 17.31 M EUR/y


def compressor_power_MW(flow_kmol_h, pin_bar, pout_bar):
    return G.compressor_power_MW(flow_kmol_h, pin_bar, pout_bar)


def economics(X, SMeOH, SCH4, SCO, *, STY_per_g_metal=None, metal_wt=None, STY_per_g_cat=None,
              P_bar=M.CAND_PRESSURE_BAR, h2_co2=M.CANDIDATE_H2_CO2, purge=M.SOURCE_PURGE, x_co="inert", T_C=None,
              h2_price=M.H2_PRICE_EUR_T, co2_price=M.CO2_PRICE_EUR_T, elec_price=M.ELEC_EUR_MWH,
              prod_tph=M.PROD_TPH, hours=M.HOURS_Y, ir=M.IR, life=M.PLANT_LIFE_Y, capex_mult=1.0, opex_mult=1.0,
              loop_dp=M.LOOP_DP_BAR, cat_term=None, lang=M.LF, h2_feed_bar=M.H2_FEED_PRESSURE_BAR,
              co2_feed_bar=M.CO2_FEED_PRESSURE_BAR, recycle_mult=1.0):
    x = G.resolve_x_co(x_co, X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar)
    loop = G.loop_balance(X, SMeOH, SCH4, SCO, h2_co2, purge, x)
    P = np.asarray(P_bar, dtype=float)
    kmol_h = prod_tph * 1000.0 / M.MW["MeOH"]
    tpy = prod_tph * hours
    p_co2 = compressor_power_MW(loop["fresh_co2"] * kmol_h, co2_feed_bar, P)
    p_h2 = compressor_power_MW(loop["fresh_h2"] * kmol_h, h2_feed_bar, P)
    p_rec = compressor_power_MW(loop["recycle"] * recycle_mult * kmol_h * M.RECYCLE_FLOW_CORRECTION,
                                np.maximum(1.0, P - loop_dp), P)
    h2_t = loop["fresh_h2"] * M.MW["H2"] / M.MW["MeOH"]          # t H2 / t MeOH
    co2_t = loop["fresh_co2"] * M.MW["CO2"] / M.MW["MeOH"]       # t CO2 / t MeOH
    h2_eur_t, co2_eur_t = h2_t * h2_price, co2_t * co2_price
    feed_M = (h2_eur_t + co2_eur_t) * tpy / 1e6
    elec_M = (p_co2 + p_h2 + p_rec) * hours * elec_price / 1e6
    if STY_per_g_cat is not None:
        catalyst_t = prod_tph / np.asarray(STY_per_g_cat, dtype=float)
    else:
        catalyst_t = prod_tph / np.asarray(STY_per_g_metal, dtype=float) / (np.asarray(metal_wt) / 100.0)
    common = M.COMMON_DIRECT_MEUR_Y * (tpy / M.PROD_TPY)
    cat_M = 0.0
    if cat_term is not None:
        price, cat_life = cat_term
        common = common - ANCHOR_CAT_REPL_MEUR_Y * (tpy / M.PROD_TPY)
        cat_M = catalyst_t * 1000.0 * price / cat_life / 1e6
    common = common * opex_mult
    reactor_in = (loop["reactor_in"] + (recycle_mult - 1.0) * loop["recycle"]) * kmol_h * M.RECYCLE_FLOW_CORRECTION
    purge_flow = loop["purge_gas"] * kmol_h * M.RECYCLE_FLOW_CORRECTION
    crude = loop["crude_liquid_mol"] * kmol_h
    gas_r = reactor_in / M.REF_REACTOR_IN_KMOL_H
    liq_r = crude / M.REF_CRUDE_LIQ_KMOL_H
    pur_r = np.maximum(purge_flow, 1e-12) / M.REF_PURGE_KMOL_H
    E, Gx, C = M.EC_REF, M.EXP_GENERAL, M.EXP_COMP
    ec = {
        "Reactor modules": E["Reactor modules"] * (catalyst_t / M.SOURCE_CAT_T) ** Gx,
        "Carbon dioxide compressor": E["Carbon dioxide compressor"] * (p_co2 / M.REF_POWERS[0]) ** C,
        "Hydrogen compressor": E["Hydrogen compressor"] * (np.maximum(p_h2, 0.0) / M.REF_POWERS[1]) ** C,
        "Recycle/reflux compressor": E["Recycle/reflux compressor"] * (p_rec / M.REF_POWERS[2]) ** C,
        "Reactor preheaters": E["Reactor preheaters"] * gas_r ** Gx,
        "Heat exchangers": E["Heat exchangers"] * gas_r ** Gx,
        "Flash drums": E["Flash drums"] * gas_r ** Gx,
        "Distillation column": E["Distillation column"] * liq_r ** Gx,
        "Pump": E["Pump"] * liq_r ** Gx,
        "Furnace & blower": E["Furnace & blower"] * pur_r ** Gx,
        "Turbine & generator": E["Turbine & generator"] * pur_r ** Gx,
    }
    ec = {k: v * capex_mult for k, v in ec.items()}
    EC = sum(ec.values())
    FCI = lang * EC
    WC = FCI / 9.0
    crf = ir * (1 + ir) ** life / ((1 + ir) ** life - 1)
    ACC = FCI * crf + WC * ir
    OL = M.SOURCE_OL_MEUR_Y * opex_mult
    direct = common + feed_M + elec_M + cat_M
    ind_fixed = 2.2125 * OL + 0.081 * FCI
    NPC = (ACC + direct + ind_fixed) / 0.90
    per_t = 1e6 / tpy
    out = dict(cost_eur_t=NPC * per_t, NPC_MEUR_Y=NPC, EC_MEUR=EC, FCI_MEUR=FCI, ACC_MEUR_Y=ACC,
               direct_MEUR_Y=direct, indirect_MEUR_Y=NPC - ACC - direct,
               h2_eur_t=h2_eur_t, co2_eur_t=co2_eur_t, elec_eur_t=elec_M * per_t, acc_eur_t=ACC * per_t,
               cat_eur_t=cat_M * per_t, residual_direct_eur_t=common * per_t,
               fixed_indirect_eur_t=ind_fixed * per_t, revenue_linked_eur_t=0.10 * NPC * per_t,
               h2_t_per_t=h2_t, co2_t_per_t=co2_t, catalyst_t=catalyst_t,
               recycle_kmol_h=loop["recycle"] * recycle_mult * kmol_h * M.RECYCLE_FLOW_CORRECTION,
               fresh_kmol_h=(loop["fresh_co2"] + loop["fresh_h2"]) * kmol_h,
               purge_kmol_h=purge_flow, reactor_in_kmol_h=reactor_in,
               P_co2_MW=p_co2, P_h2_MW=p_h2, P_rec_MW=p_rec, x_co=x,
               carbon_efficiency=loop["carbon_efficiency"], fresh_h2_co2=loop["fresh_h2_co2"],
               nonreactive_fraction=loop["nonreactive_fraction"], methane_fraction=loop["methane_fraction"],
               ec=ec, loop=loop)
    out["recycle_ratio"] = out["recycle_kmol_h"] / out["fresh_kmol_h"]
    out["elec_MWh_t"] = (p_co2 + p_h2 + p_rec) / prod_tph
    return out


def cost(c, **kw):
    keys = ("STY_per_g_metal", "metal_wt", "STY_per_g_cat", "P_bar", "h2_co2", "T_C")
    args = {k: c[k] for k in keys if k in c and c[k] is not None}
    args.update(kw)
    return economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], **args)


def check_identity(n=400, seed=7):
    """Max |variant - frozen| over random states at default knobs, EUR/t (must be ~1e-10)."""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for _ in range(n):
        X = rng.uniform(0.02, 0.6)
        sm = rng.uniform(0.3, 1.0)
        sch4 = rng.uniform(0, 1 - sm)
        sco = 1 - sm - sch4
        kw = dict(STY_per_g_cat=rng.uniform(0.02, 3.0), P_bar=rng.choice([30.0, 50.0, 70.0, 100.0]),
                  h2_co2=rng.uniform(3.2, 4.5), purge=rng.uniform(0.005, 0.2), T_C=rng.uniform(200, 280),
                  x_co=rng.choice(["inert", "recycled_central"]))
        try:
            a = G.economics(X, sm, sch4, sco, **kw)["cost_eur_t"]
        except ValueError:
            continue
        b = economics(X, sm, sch4, sco, **kw)["cost_eur_t"]
        worst = max(worst, float(abs(a - b)))
    return worst
