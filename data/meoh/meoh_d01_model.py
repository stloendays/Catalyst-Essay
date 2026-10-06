"""MEOH-D01-v3 explicit recycle / purge / separation cost model, vectorised.

Faithful port of `candidate_economics()`, the purge sweep, the purge diagnostic and the local leverage
functions of the original generator of `MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`
(`MeOH_C01_ExplicitLoopAndLeverage_v3.0.py`, project archive 2026-08-19 v1.0, 03_MeOH_Final/Code, lines 30-325).
It reproduces every stored cost value of the workbook to < 1e-9 EUR/t (`regenerate_d01_values.py --check`).

The workbook keeps the species balance as live Excel formulas (sheet Explicit_Loop_2pct, columns H-X) but
stores compression, catalyst mass, EC, FCI, ACC, direct/indirect OPEX and NPC (columns Y-AG) as values written by
that script; this module recomputes all of them. Every constant below is copied from the generator / workbook
sheet Controls and is held fixed (canonical cost parameters). Only catalyst inputs (X, S_MeOH, S_CH4, S_CO,
STY, Re wt%) vary.

All functions accept numpy arrays (any broadcastable shape) for the catalyst inputs.
"""
from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------- constants (Processes 2022, 10, 1535) ----
MW = {"MeOH": 32.04186, "CO2": 44.0095, "H2": 2.01588, "CH4": 16.0425, "CO": 28.0101, "N2": 28.0134,
      "H2O": 18.01528}
PROD_TPH = 145.0
HOURS_Y = 8000.0
PROD_TPY = PROD_TPH * HOURS_Y
PROD_KMOL_H = PROD_TPH * 1000.0 / MW["MeOH"]
H2_PRICE_EUR_T = 3097.4
CO2_PRICE_EUR_T = 44.3
ELEC_EUR_MWH = 90.0
H2_PURITY = 0.995
REF_PRESSURE_BAR = 70.0
CAND_PRESSURE_BAR = 100.0
H2_FEED_PRESSURE_BAR = 30.0
CO2_FEED_PRESSURE_BAR = 1.0
COMP_ETA = 0.80
COMP_T_K = 298.15
R = 8.314462618
LOOP_DP_BAR = 1.5
LF = 4.86
IR = 0.10
PLANT_LIFE_Y = 20
CRF = IR * (1 + IR) ** PLANT_LIFE_Y / ((1 + IR) ** PLANT_LIFE_Y - 1)
SOURCE_EC_MEUR = 85.5
SOURCE_FCI_MEUR = 415.9
SOURCE_DIRECT_MEUR_Y = 874.9
SOURCE_INDIRECT_MEUR_Y = 143.4
SOURCE_NPC_MEUR_Y = 1071.8
SOURCE_RECYCLE_KMOL_H = 54290.0
SOURCE_PURGE = 0.02
SOURCE_X, SOURCE_S_MEOH, SOURCE_S_CO, SOURCE_S_CH4 = 0.285, 0.995, 0.005, 0.0
SOURCE_H2_CO2 = 3.0
SOURCE_CAT_T = 478.13 * 6.0
SOURCE_OL_MEUR_Y = (SOURCE_INDIRECT_MEUR_Y - 0.081 * SOURCE_FCI_MEUR - 0.10 * SOURCE_NPC_MEUR_Y) / 2.2125
EC_PIXEL_WEIGHTS = {"Reactor modules": 306.0, "Carbon dioxide compressor": 257.0, "Hydrogen compressor": 94.0,
                    "Reactor preheaters": 27.0, "Heat exchangers": 23.0, "Furnace & blower": 37.0,
                    "Distillation column": 27.0, "Turbine & generator": 25.0, "Recycle/reflux compressor": 3.0,
                    "Flash drums": 2.0, "Pump": 1.0}
EC_REF = {k: SOURCE_EC_MEUR * v / sum(EC_PIXEL_WEIGHTS.values()) for k, v in EC_PIXEL_WEIGHTS.items()}
EXP_GENERAL = 0.60
EXP_COMP = 0.67
CANDIDATE_H2_CO2 = 4.0


# ---------------------------------------------------------------- species loop -----------------------------
def loop_balance(X, SMeOH, SCH4, SCO, h2_co2, purge, h2_purity=H2_PURITY):
    """Steady-state species balance per 1 mol net MeOH (generator lines 113-158)."""
    X, SMeOH, SCH4, SCO = map(np.asarray, (X, SMeOH, SCH4, SCO))
    if np.any((X <= 0) | (X >= 1) | (SMeOH <= 0) | (SMeOH > 1)):
        raise ValueError("invalid conversion/selectivity")
    if np.any(np.abs(SMeOH + SCH4 + SCO - 1.0) > 1e-9):
        raise ValueError("carbon selectivities must sum to 1")
    co2_in = 1.0 / (X * SMeOH)
    ch4_prod = SCH4 / SMeOH
    co_prod = SCO / SMeOH
    co2_out = (1.0 - X) * co2_in
    h2_in = h2_co2 * co2_in
    h2_out = h2_in - (3.0 + 4.0 * ch4_prod + co_prod)
    if np.any(h2_out <= 0):
        raise ValueError("H2 inlet ratio insufficient")
    fresh_co2 = co2_in - (1.0 - purge) * co2_out
    fresh_h2 = h2_in - (1.0 - purge) * h2_out
    n2_in = fresh_h2 * (1.0 - h2_purity) / h2_purity / purge
    ch4_in = (1.0 - purge) / purge * ch4_prod
    co_in = (1.0 - purge) / purge * co_prod
    gas_out = co2_out + h2_out + (ch4_in + ch4_prod) + (co_in + co_prod) + n2_in
    reactor_in = co2_in + h2_in + ch4_in + co_in + n2_in
    water_prod = 1.0 + 2.0 * ch4_prod + co_prod
    return dict(co2_in=co2_in, h2_in=h2_in, fresh_co2=fresh_co2, fresh_h2=fresh_h2, ch4_prod=ch4_prod,
                co_prod=co_prod, co2_out=co2_out, h2_out=h2_out, n2_in=n2_in, ch4_in=ch4_in, co_in=co_in,
                gas_out=gas_out, recycle=(1.0 - purge) * gas_out, purge_gas=purge * gas_out,
                reactor_in=reactor_in, nonreactive_fraction=(ch4_in + co_in + n2_in) / reactor_in,
                methane_fraction=ch4_in / reactor_in, crude_liquid_mol=1.0 + water_prod)


def compressor_power_MW(flow_kmol_h, pin_bar, pout_bar):
    j_per_mol = R * COMP_T_K * math.log(pout_bar / pin_bar) / COMP_ETA
    return j_per_mol * np.asarray(flow_kmol_h) * 1000.0 / 3.6e9


REF_LOOP = loop_balance(SOURCE_X, SOURCE_S_MEOH, SOURCE_S_CH4, SOURCE_S_CO, SOURCE_H2_CO2, SOURCE_PURGE)
RECYCLE_FLOW_CORRECTION = SOURCE_RECYCLE_KMOL_H / (float(REF_LOOP["recycle"]) * PROD_KMOL_H)
REF_REACTOR_IN_KMOL_H = float(REF_LOOP["reactor_in"]) * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION
REF_PURGE_KMOL_H = float(REF_LOOP["purge_gas"]) * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION
REF_CRUDE_LIQ_KMOL_H = float(REF_LOOP["crude_liquid_mol"]) * PROD_KMOL_H


def _powers(loop, pressure_bar):
    p_co2 = compressor_power_MW(loop["fresh_co2"] * PROD_KMOL_H, CO2_FEED_PRESSURE_BAR, pressure_bar)
    p_h2 = compressor_power_MW(loop["fresh_h2"] * PROD_KMOL_H, H2_FEED_PRESSURE_BAR, pressure_bar)
    p_rec = compressor_power_MW(loop["recycle"] * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION,
                                max(1.0, pressure_bar - LOOP_DP_BAR), pressure_bar)
    return p_co2, p_h2, p_rec


def _feed_cost(loop):
    co2 = loop["fresh_co2"] * MW["CO2"] / MW["MeOH"] * 1000.0 * CO2_PRICE_EUR_T / 1000.0
    h2 = loop["fresh_h2"] * MW["H2"] / MW["MeOH"] * 1000.0 * H2_PRICE_EUR_T / 1000.0
    return h2 + co2, h2, co2


REF_POWERS = tuple(float(p) for p in _powers(REF_LOOP, REF_PRESSURE_BAR))
_ref_feed, _, _ = _feed_cost(REF_LOOP)
COMMON_DIRECT_MEUR_Y = (SOURCE_DIRECT_MEUR_Y - float(_ref_feed) * PROD_TPY / 1e6
                        - sum(REF_POWERS) * HOURS_Y * ELEC_EUR_MWH / 1e6)


# ---------------------------------------------------------------- plant economics ----------------------------
def candidate_economics(X, SMeOH, SCH4, SCO, STY, Re_wt, purge=SOURCE_PURGE, pressure_bar=CAND_PRESSURE_BAR):
    """Net production cost (EUR/t MeOH) and loop state; generator lines 203-256, array-valued."""
    loop = loop_balance(X, SMeOH, SCH4, SCO, CANDIDATE_H2_CO2, purge)
    p_co2, p_h2, p_rec = _powers(loop, pressure_bar)
    feed_eur_t, h2_eur_t, co2_eur_t = _feed_cost(loop)
    feed_M = feed_eur_t * PROD_TPY / 1e6
    elec_M = (p_co2 + p_h2 + p_rec) * HOURS_Y * ELEC_EUR_MWH / 1e6
    catalyst_t = PROD_TPH * 1000.0 / np.asarray(STY) / (np.asarray(Re_wt) / 100.0) / 1000.0
    reactor_in = loop["reactor_in"] * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION
    recycle = loop["recycle"] * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION
    purge_flow = loop["purge_gas"] * PROD_KMOL_H * RECYCLE_FLOW_CORRECTION
    crude = loop["crude_liquid_mol"] * PROD_KMOL_H
    gas_r = reactor_in / REF_REACTOR_IN_KMOL_H
    liq_r = crude / REF_CRUDE_LIQ_KMOL_H
    pur_r = np.maximum(purge_flow, 1e-12) / REF_PURGE_KMOL_H
    ec = {
        "Reactor modules": EC_REF["Reactor modules"] * (catalyst_t / SOURCE_CAT_T) ** EXP_GENERAL,
        "Carbon dioxide compressor": EC_REF["Carbon dioxide compressor"] * (p_co2 / REF_POWERS[0]) ** EXP_COMP,
        "Hydrogen compressor": EC_REF["Hydrogen compressor"] * (p_h2 / REF_POWERS[1]) ** EXP_COMP,
        "Recycle/reflux compressor": EC_REF["Recycle/reflux compressor"] * (p_rec / REF_POWERS[2]) ** EXP_COMP,
        "Reactor preheaters": EC_REF["Reactor preheaters"] * gas_r ** EXP_GENERAL,
        "Heat exchangers": EC_REF["Heat exchangers"] * gas_r ** EXP_GENERAL,
        "Flash drums": EC_REF["Flash drums"] * gas_r ** EXP_GENERAL,
        "Distillation column": EC_REF["Distillation column"] * liq_r ** EXP_GENERAL,
        "Pump": EC_REF["Pump"] * liq_r ** EXP_GENERAL,
        "Furnace & blower": EC_REF["Furnace & blower"] * pur_r ** EXP_GENERAL,
        "Turbine & generator": EC_REF["Turbine & generator"] * pur_r ** EXP_GENERAL,
    }
    EC = sum(ec.values())
    FCI = LF * EC
    WC = FCI / 9.0
    ACC = FCI * CRF + WC * IR
    direct = COMMON_DIRECT_MEUR_Y + feed_M + elec_M
    NPC = (ACC + direct + 2.2125 * SOURCE_OL_MEUR_Y + 0.081 * FCI) / 0.90
    return dict(cost_eur_t=NPC * 1e6 / PROD_TPY, NPC_MEUR_Y=NPC, EC_MEUR=EC, FCI_MEUR=FCI, ACC_MEUR_Y=ACC,
                direct_MEUR_Y=direct, indirect_MEUR_Y=NPC - ACC - direct, h2_eur_t=h2_eur_t, co2_eur_t=co2_eur_t,
                elec_eur_t=elec_M * 1e6 / PROD_TPY, catalyst_t=catalyst_t, recycle_kmol_h=recycle,
                nonreactive_fraction=loop["nonreactive_fraction"], methane_fraction=loop["methane_fraction"],
                sep_loop_EC_MEUR=(ec["Recycle/reflux compressor"] + ec["Heat exchangers"] + ec["Flash drums"]
                                  + ec["Distillation column"] + ec["Pump"]),
                ec=ec)


# Frozen D01 v3 inputs (workbook sheet Candidate_Inputs; generator CANDIDATES)
FROZEN = {
    "1wtRe_200C": dict(name="1 wt% Re | 200 C", Re_wt=1.0, T_C=200, STY=55.0, X=0.19, SMeOH=0.99, SCH4=0.00, SCO=0.01),
    "5wtRe_200C": dict(name="5 wt% Re | 200 C", Re_wt=5.0, T_C=200, STY=18.0, X=0.33, SMeOH=0.97, SCH4=0.03, SCO=0.00),
    # S_CH4 1 %, CO-like 2 % per Table 3 of the source (corrected 2026-10-05, PR #7); this dict kept 3 % / 0 until 2026-10-06
    "1wtRe_250C": dict(name="1 wt% Re | 250 C", Re_wt=1.0, T_C=250, STY=65.0, X=0.23, SMeOH=0.97, SCH4=0.01, SCO=0.02),
    "5wtRe_250C": dict(name="5 wt% Re | 250 C", Re_wt=5.0, T_C=250, STY=16.0, X=0.40, SMeOH=0.74, SCH4=0.25, SCO=0.01),
}


def cost(c, **kw):
    return candidate_economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], c["STY"], c["Re_wt"], **kw)


# ---------------------------------------------------------------- generator post-processing -------------------
SOURCE_NONREACTIVE_REFERENCE = float(REF_LOOP["nonreactive_fraction"])
PURGES = np.round(np.arange(0.005, 0.4001, 0.001), 3)


def purge_sweep(c):
    """Every purge point re-solves the loop (generator lines 270-277)."""
    return [dict(purge=float(p), **cost(c, purge=float(p))) for p in PURGES]


def purge_diagnostic(sweep):
    """Lowest-cost purge whose non-H2/CO2 fraction is within the source reference (generator lines 281-286)."""
    feasible = [r for r in sweep if r["nonreactive_fraction"] <= SOURCE_NONREACTIVE_REFERENCE]
    return min(feasible, key=lambda r: float(r["cost_eur_t"])) if feasible else None


def _c(c, purge=SOURCE_PURGE):
    return float(cost(c, purge=purge)["cost_eur_t"])


def leverage_increase(c, key, eps=0.005):
    """L = -d ln C / d ln x for a beneficial increasing variable X or STY (generator lines 295-302)."""
    lo, hi = dict(c), dict(c)
    lo[key], hi[key] = c[key] * (1 - eps), c[key] * (1 + eps)
    return -(math.log(_c(hi)) - math.log(_c(lo))) / (math.log(1 + eps) - math.log(1 - eps))


def leverage_ch4_suppression(c, eps=0.005):
    """E = d ln C / d ln S_CH4, selectivity moved between CH4 and MeOH, CO-like held (generator lines 304-316)."""
    if c["SCH4"] <= 0:
        return math.nan
    ch = c["SCH4"]
    hi, lo = dict(c), dict(c)
    hi["SCH4"] = ch * (1 + eps); hi["SMeOH"] = c["SMeOH"] - (hi["SCH4"] - ch)
    lo["SCH4"] = ch * (1 - eps); lo["SMeOH"] = c["SMeOH"] + (ch - lo["SCH4"])
    return (math.log(_c(hi)) - math.log(_c(lo))) / (math.log(hi["SCH4"]) - math.log(lo["SCH4"]))
