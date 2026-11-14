"""Plant cost models for the two new reactions, built on the same logic as the NH3 / methanol chains:
a measured catalyst (conditions, conversion, selectivity, productivity, stability, composition) goes into a plant
mass and energy balance, the plant optimises its free operating variable (here the per-pass conversion, as the
purge was optimised in the methanol loop), and the plant cost per tonne of product is split into terms.

Activity transfer from the lab to the plant: first-order approach to equilibrium,
    k = -ln(1 - X_lab / Xeq_lab) / tau_lab,   tau = catalyst mass per molar feed of the key reactant,
so the catalyst needed per tonne of product at plant per-pass conversion Xp is
    r_plant = r_lab * (Xp / X_lab) * ln(1 - X_lab/Xeq_lab) / ln(1 - Xp/Xeq_plant).
Selectivity keeps its lab value (records measured far below the plant conversion are flagged by analyze.py).
Parameters and their sources: params.json (built by build_params.py from params_process.json), SOURCES.md.

PDH  : C3H8 -> C3H6 + H2, USD per t propylene.
CH4  : CO2 + 4 H2 -> CH4 + 2 H2O, USD per t CH4 (USD/MWh = USD/t / 15.42 on the HHV).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
PARAMS = json.loads((HERE / "params.json").read_text(encoding="utf-8"))
R = 8.314
MW_C3H8, MW_C3H6, MW_H2, MW_CH4, MW_CO2 = 44.097, 42.081, 2.016, 16.043, 44.010
XP_GRID = np.linspace(0.04, 1.0, 49)          # plant per-pass conversion as a fraction of approach x Xeq


def K_of(T, th):
    return math.exp(-(th["dH_J_mol"] - T * th["dS_J_molK"]) / (R * T))


def pdh_xeq(T, P_bar, h2_ratio=0.0, inert_ratio=0.0):
    """Equilibrium conversion, feed 1 C3H8 : h2_ratio H2 : inert_ratio inert, at P_bar."""
    K = K_of(T, PARAMS["pdh"]["thermo"])

    def f(x):
        n = 1 + h2_ratio + inert_ratio + x
        return (x * (h2_ratio + x)) / ((1 - x) * n) * P_bar - K
    return brentq(f, 1e-12, 1 - 1e-12)


def ch4_xeq(T, P_bar, h2_ratio=4.0, inert_ratio=0.0):
    """Equilibrium CO2 conversion for CO2 + 4 H2 = CH4 + 2 H2O, feed 1 CO2 : h2_ratio H2 : inert_ratio inert."""
    K = K_of(T, PARAMS["ch4"]["thermo"])
    xmax = min(1.0, h2_ratio / 4) * (1 - 1e-12)

    def f(x):
        n = 1 + h2_ratio + inert_ratio - 2 * x
        num = (x / n) * (2 * x / n) ** 2
        den = ((1 - x) / n) * ((h2_ratio - 4 * x) / n) ** 4 * P_bar ** 2
        return math.log(num) - math.log(den) - math.log(K)
    return brentq(f, 1e-12, xmax)


def lab_xeq(rxn, rec):
    """Equilibrium conversion under the lab test conditions (feed fractions of the record)."""
    y, yh = rec.get("y_key") or None, rec.get("y_h2")
    P = rec.get("P_bar") or 1.01325
    if rxn == "pdh":
        y = y or 1.0
        h = (yh or 0.0) / y
        inert = max(0.0, 1 - y - (yh or 0.0)) / y
        return pdh_xeq(rec["T_K"], P, h, inert)
    y = y or 0.2
    h = (yh / y) if yh else 4.0
    inert = max(0.0, 1 - y * (1 + h)) / y
    return ch4_xeq(rec["T_K"], P, h, inert)


def activity_scale(X_lab, xeq_lab, Xp, xeq_p):
    """r_plant / r_lab for first-order approach to equilibrium (see module docstring)."""
    a = min(X_lab / xeq_lab, 0.98)
    b = min(Xp / xeq_p, 0.999)
    return (Xp / X_lab) * math.log(1 - a) / math.log(1 - b)


def catalyst_price(components, metal_prices, base):
    """USD per kg catalyst: stated metal contents x metal price + a base (support + manufacture);
    returns (non-recoverable part incl. base, recoverable precious-metal part)."""
    c, pgm = base, 0.0
    for comp in components:
        el, wt = comp["element"], comp["wt_pct"]
        if wt is None or el not in metal_prices:
            continue
        v = wt / 100 * metal_prices[el]
        if el in PARAMS["common"]["recoverable_metals"]:
            pgm += v
        else:
            c += v
    return c, pgm


# ---------------------------------------------------------------- PDH
def _pdh_at(rec, Xp, xeq_p, xeq_l, p, c):
    plant = p["plant"]
    prod, hours = plant["capacity_t_per_y"], plant["hours_per_y"]
    S = rec["S"]
    m_feed = (MW_C3H8 / MW_C3H6) / S
    F = m_feed / Xp
    gas = c["gas_usd_per_GJ"]
    feed = m_feed * p["prices"]["propane_usd_t"]
    h2_credit = (MW_H2 / MW_C3H6) * p["h2_credit_GJ_per_t_H2"] * gas
    light_credit = m_feed * (1 - S) * p["light_ends_GJ_per_t"] * gas
    q_rxn = p["thermo"]["dH_J_mol"] / MW_C3H6 * 1e-3 / p["furnace_eff"]
    energy = (q_rxn + p["e_proc_GJ_per_t_feed"] * F) * gas + p["power_kWh_per_t_feed"] * F * c["power_usd_kWh"]
    t_cyc = max(rec.get("t_cycle_h") or p["reference"]["t_cycle_h"], p["t_cycle_min_h"])
    f_off = p["t_regen_h"] / (t_cyc + p["t_regen_h"])
    cap = p["capex"]
    F_ref = p["reference"]["F"]
    capex = cap["usd"] * (cap["fixed_share"] + cap["throughput_share"] * (F / F_ref) ** 0.6
                          + cap["reactor_share"] * (F / F_ref) ** 0.6 * (1 - p["reference"]["f_off"]) / (1 - f_off))
    capital = capex * (c["crf"] + c["fixed_om_frac"]) / prod
    r_p = rec["r"] * activity_scale(rec["X"], xeq_l, Xp, xeq_p)
    W_on = (prod / hours) / r_p
    W_t = W_on / (1 - f_off)
    base, pgm = catalyst_price(rec["components"], c["metal_usd_per_kg"], p["catalyst_base_usd_kg"])
    life = p["catalyst_life_y"]
    cat = W_t * 1e3 * (base / life + pgm * ((1 - c["metal_recovery"]) / life + c["metal_financing"])) / prod
    regen = W_on * (hours * (1 - f_off) / t_cyc) * p["regen_GJ_per_t_cat"] * gas / prod
    parts = dict(feed=feed, h2_credit=-h2_credit, light_ends_credit=-light_credit, energy=energy,
                 capital=capital, catalyst=cat, regeneration=regen)
    return sum(parts.values()), dict(parts=parts, Xp=Xp, Xeq=xeq_p, F=F, m_feed=m_feed, W_t=W_t, f_off=f_off,
                                     t_cycle_h=t_cyc, r_plant=r_p)


def pdh_cost(rec, prm=None, detail=False):
    """Minimum plant cost (USD per t propylene) over the per-pass conversion, for one normalised PDH record.
    rec: T_K, X, S, r (kg C3H6/kg cat/h, lab), components, t_cycle_h, and the lab feed (P_bar, y_key, y_h2)."""
    p = prm or PARAMS["pdh"]
    c = PARAMS["common"]
    plant = p["plant"]
    xeq_p = pdh_xeq(rec["T_K"], plant["P_bar"], plant["h2_ratio"])
    xeq_l = rec.get("xeq_lab") or lab_xeq("pdh", rec)
    best = min((_pdh_at(rec, f * plant["approach"] * xeq_p, xeq_p, xeq_l, p, c) for f in XP_GRID), key=lambda t: t[0])
    best[1]["Xeq_lab"] = xeq_l
    return best if detail else best[0]


# ---------------------------------------------------------------- CO2 methanation
def _ch4_at(rec, Xp, xeq_p, xeq_l, p, c):
    plant = p["plant"]
    prod, hours = plant["capacity_t_per_y"], plant["hours_per_y"]
    eta = plant["overall_conv"]
    h2 = 4 * MW_H2 / MW_CH4 / eta * p["prices"]["h2_usd_kg"] * 1e3
    co2 = MW_CO2 / MW_CH4 / eta * p["prices"]["co2_usd_t"]
    recycle = (1 - Xp) / Xp
    feed_mass = (4 * MW_H2 + MW_CO2) / MW_CH4 / eta
    power = (p["power_kWh_per_t_fresh"] + p["power_kWh_per_t_recycle"] * recycle) * feed_mass * c["power_usd_kWh"]
    # CO by-product of the lead reactor is converted downstream; its selectivity costs extra catalyst there
    r_p = rec["r"] * activity_scale(rec["X"], xeq_l, Xp, xeq_p)
    W_t = (prod / hours) / r_p
    base, pgm = catalyst_price(rec["components"], c["metal_usd_per_kg"], p["catalyst_base_usd_kg"])
    life = p["catalyst_life_y"]
    cat = W_t * 1e3 * (base / life + pgm * ((1 - c["metal_recovery"]) / life + c["metal_financing"])) / prod
    cap = p["capex"]
    ref = p["reference"]
    capex = cap["usd"] * (cap["fixed_share"] + cap["recycle_share"] * ((1 + recycle) / (1 + ref["recycle"])) ** 0.6
                          + cap["reactor_share"] * (W_t / ref["W_t"]) ** 0.6)
    capital = capex * (c["crf"] + c["fixed_om_frac"]) / prod
    parts = dict(hydrogen=h2, co2=co2, power=power, capital=capital, catalyst=cat)
    return sum(parts.values()), dict(parts=parts, Xp=Xp, Xeq=xeq_p, recycle=recycle, W_t=W_t, r_plant=r_p)


def ch4_cost(rec, prm=None, detail=False):
    """Minimum plant cost (USD per t CH4) over the lead-reactor per-pass conversion for one methanation record.
    The staged plant reaches the grid specification (overall conversion `overall_conv`) whatever the catalyst;
    the catalyst sets the catalyst inventory and reactor volume and, through them, the recycle/size trade-off."""
    p = prm or PARAMS["ch4"]
    c = PARAMS["common"]
    plant = p["plant"]
    xeq_p = ch4_xeq(rec["T_K"], plant["P_bar"], 4.0, plant["inert_ratio"])
    xeq_l = rec.get("xeq_lab") or lab_xeq("ch4", rec)
    best = min((_ch4_at(rec, f * plant["approach"] * xeq_p, xeq_p, xeq_l, p, c) for f in XP_GRID), key=lambda t: t[0])
    best[1]["Xeq_lab"] = xeq_l
    return best if detail else best[0]


def init_reference(params=None):
    """Reference-plant quantities the scalings are normalised to, from the reference catalyst at the reference
    per-pass conversion (no optimisation, so the scalings are anchored to the published plant)."""
    P = params or PARAMS
    p = P["pdh"]
    ref = p["reference"]
    xeq = pdh_xeq(ref["T_K"], p["plant"]["P_bar"], p["plant"]["h2_ratio"])
    ref["Xeq_plant"] = xeq
    ref["F"] = (MW_C3H8 / MW_C3H6) / ref["S"] / ref["X"]
    ref["f_off"] = p["t_regen_h"] / (max(ref["t_cycle_h"], p["t_cycle_min_h"]) + p["t_regen_h"])
    q = P["ch4"]
    qr = q["reference"]
    qr["recycle"] = (1 - qr["X"]) / qr["X"]
    qr["W_t"] = (q["plant"]["capacity_t_per_y"] / q["plant"]["hours_per_y"]) / qr["r"]


def reference_record(rxn):
    ref = PARAMS[rxn]["reference"]
    comps = [dict(element=e, wt_pct=w) for e, w in ref["elements"]]
    rec = dict(T_K=ref["T_K"], X=ref["X"], S=ref["S"], r=ref["r"], t_cycle_h=ref.get("t_cycle_h"), components=comps)
    # the reference r is the industrial productivity at its own per-pass conversion and plant equilibrium
    rec["xeq_lab"] = ref["Xeq_plant"] if rxn == "pdh" else ch4_xeq(ref["T_K"], PARAMS["ch4"]["plant"]["P_bar"], 4.0,
                                                                   PARAMS["ch4"]["plant"]["inert_ratio"])
    return rec


init_reference()
