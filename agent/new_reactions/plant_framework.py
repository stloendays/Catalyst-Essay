"""One plant cost framework for any single-product catalytic reaction (USD per tonne of product).

The reaction is a configuration (configs/<rxn>_<set>.json), not code: stoichiometry, thermodynamics, prices, plant
basis, energy, capital scaling, catalyst and regeneration, plus two structural switches. A new reaction needs one
config, written once (by hand or by the agent, every value with its source); everything else is shared.

Terms per tonne of product, at plant per-pass conversion Xp of the key reactant (optimised on a grid up to
approach x equilibrium):
  raw materials   sum_i nu_i MW_i / MW_product / overall_conv, divided by S for every reactant when
                  selectivity_loss = "lost" (by-products leave the plant) and not when "converted_downstream"
  credits         fixed per tonne product (e.g. H2 burnt as fuel) + lost key reactant burnt as fuel
  energy          reaction heat / furnace efficiency (endothermic only) + e_proc x reactor throughput, x gas price;
                  power (fresh + recycle) x fresh mass x power price
  capital         capex x (fixed + throughput (F/F_ref)^0.6 + reactor term) x (CRF + fixed O&M) / capacity, the
                  reactor term scaling with throughput and off-stream fraction ("throughput") or with catalyst
                  inventory ("catalyst")
  catalyst        inventory = production / plant productivity; base + metal price; precious metals recovered
  regeneration    cyclic: off-stream fraction t_regen / (t_cycle + t_regen) and burn energy per cycle
Activity moves from lab to plant by a first-order approach to equilibrium:
  r_plant = r_lab (Xp / X_lab) ln(1 - X_lab/Xeq_lab) / ln(1 - Xp/Xeq_plant).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
R = 8.314
XP_GRID = np.linspace(0.04, 1.0, 49)


def load(rxn, pset="ours"):
    cfg = json.loads((HERE / "configs" / f"{rxn}_{pset}.json").read_text(encoding="utf-8"))
    init_reference(cfg)
    return cfg


# ------------------------------------------------------------------ thermodynamics
def K_of(T, th):
    return math.exp(-(th["dH_J_mol"] - T * th["dS_J_molK"]) / (R * T))


def xeq(cfg, T, P_bar, ratios, inert=0.0):
    """Equilibrium conversion of the key reactant; feed 1 key : ratios[s] s : inert, pressure P_bar."""
    nu, key = cfg["stoich"]["nu"], cfg["stoich"]["key"]
    dn = sum(nu.values())
    K = K_of(T, cfg["thermo"])
    n0 = {s: (1.0 if s == key else ratios.get(s, 0.0)) for s in nu}
    xmax = 1.0
    for s, v in nu.items():
        if v < 0 and s != key:
            xmax = min(xmax, n0[s] / (-v / -nu[key]))
    xmax *= 1 - 1e-12
    tot0 = sum(n0.values()) + inert

    def f(x):  # x = extent per mol key fed, with nu normalised to nu_key = -1
        ext = x / -nu[key]
        n = {s: n0[s] + v * ext for s, v in nu.items()}
        nt = tot0 + dn * ext
        lnQ = sum(v * math.log(max(n[s], 1e-300) / nt) for s, v in nu.items()) + dn * math.log(P_bar)
        return lnQ - math.log(K)
    return brentq(f, 1e-12, xmax)


def lab_xeq(cfg, rec):
    lab = cfg["lab_feed"]
    y = rec.get("y_key") or lab["default_y_key"]
    ratios = {}
    used = y
    for s, default in lab["default_ratio"].items():
        yh = rec.get("y_h2") if s == "H2" else None
        ratios[s] = (yh / y) if yh else default
        used += ratios[s] * y
    inert = max(0.0, 1 - used) / y
    return xeq(cfg, rec["T_K"], rec.get("P_bar") or 1.01325, ratios, inert)


def plant_xeq(cfg, T):
    pl = cfg["plant"]
    return xeq(cfg, T, pl["P_bar"], pl.get("feed_ratio", {}), pl.get("inert_ratio", 0.0))


def activity_scale(X_lab, xeq_lab, Xp, xeq_p):
    a = min(X_lab / xeq_lab, 0.98)
    b = min(Xp / xeq_p, 0.999)
    return (Xp / X_lab) * math.log(1 - a) / math.log(1 - b)


# ------------------------------------------------------------------ prices
def catalyst_price(cfg, components):
    c, pgm = cfg["catalyst"]["base_usd_kg"], 0.0
    prices, rec_m = cfg["metal_usd_per_kg"], set(cfg["catalyst"]["recoverable_metals"])
    for comp in components:
        el, wt = comp["element"], comp["wt_pct"]
        if wt is None or el not in prices:
            continue
        v = wt / 100 * prices[el]
        if el in rec_m:
            pgm += v
        else:
            c += v
    return c, pgm


# ------------------------------------------------------------------ cost at one per-pass conversion
def _masses(cfg, S):
    sp, nu, key, prod = cfg["species"], cfg["stoich"]["nu"], cfg["stoich"]["key"], cfg["stoich"]["product"]
    eta = cfg["plant"].get("overall_conv", 1.0)
    lost = cfg["switches"]["selectivity_loss"] == "lost"
    m = {}
    for s, v in nu.items():
        if v < 0:
            m[s] = (-v / nu[prod]) * sp[s]["MW"] / sp[prod]["MW"] / eta / (S if lost else 1.0)
    return m


def _at(cfg, rec, Xp, xeq_p, xeq_l):
    pl, en, cap, cat, rg = cfg["plant"], cfg["energy"], cfg["capex"], cfg["catalyst"], cfg["regeneration"]
    prod, hours = pl["capacity_t_per_y"], pl["hours_per_y"]
    sp, key, product = cfg["species"], cfg["stoich"]["key"], cfg["stoich"]["product"]
    S = rec["S"]
    m = _masses(cfg, S)
    gas, power_p = cfg["prices"]["gas_usd_per_GJ"], cfg["prices"]["power_usd_kWh"]
    parts = {}
    for s, t in m.items():
        parts["raw_" + s] = t * sp[s]["price_usd_t"]
    credit = sum(c["t_per_t_product"] * c["GJ_per_t"] * gas for c in cfg.get("fixed_credits", []))
    if cfg["switches"]["selectivity_loss"] == "lost" and cfg.get("lost_key_fuel_GJ_per_t"):
        credit += m[key] * (1 - S) * cfg["lost_key_fuel_GJ_per_t"] * gas
    parts["credits"] = -credit
    recycle = (1 - Xp) / Xp
    fresh = m[key] if en["fresh_basis"] == "key" else sum(m.values())
    F = fresh * (1 + recycle)
    q = 0.0
    if cfg["thermo"]["dH_J_mol"] > 0 and en.get("pay_reaction_heat", True):
        q = cfg["thermo"]["dH_J_mol"] / sp[product]["MW"] * 1e-3 / en["furnace_eff"]
    parts["energy"] = (q + en["e_proc_GJ_per_t_reactor_feed"] * F) * gas \
        + (en["power_kWh_per_t_fresh"] + en["power_kWh_per_t_recycle"] * recycle) * fresh * power_p
    if rg["enabled"]:
        t_cyc = max(rec.get("t_cycle_h") or cfg["reference"]["t_cycle_h"], rg["t_cycle_min_h"])
        f_off = rg["t_regen_h"] / (t_cyc + rg["t_regen_h"])
    else:
        t_cyc, f_off = None, 0.0
    r_p = rec["r"] * activity_scale(rec["X"], xeq_l, Xp, xeq_p)
    W_on = (prod / hours) / r_p
    W_t = W_on / (1 - f_off)
    ref = cfg["reference"]
    thr = (F / ref["F"]) ** 0.6
    if cap["reactor_basis"] == "throughput":
        reactor = thr * (1 - ref["f_off"]) / (1 - f_off)
    else:
        reactor = (W_t / ref["W_t"]) ** 0.6
    capex = cap["usd"] * (cap["fixed_share"] + cap["throughput_share"] * thr + cap["reactor_share"] * reactor)
    parts["capital"] = capex * (cfg["finance"]["crf"] + cfg["finance"]["fixed_om_frac"]) / prod
    base, pgm = catalyst_price(cfg, rec["components"])
    life = cat["life_y"]
    parts["catalyst"] = W_t * 1e3 * (base / life + pgm * ((1 - cat["metal_recovery"]) / life
                                                         + cat["metal_financing"])) / prod
    parts["regeneration"] = (W_on * (hours * (1 - f_off) / t_cyc) * rg["regen_GJ_per_t_cat"] * gas / prod
                             if rg["enabled"] else 0.0)
    return sum(parts.values()), dict(parts=parts, Xp=Xp, Xeq=xeq_p, F=F, recycle=recycle, W_t=W_t, f_off=f_off,
                                     t_cycle_h=t_cyc, r_plant=r_p)


def cost(cfg, rec, detail=False):
    """Minimum plant cost over the per-pass conversion. rec: T_K, X, S, r (kg product/kg cat/h), components,
    t_cycle_h, P_bar, y_key, y_h2 (lab), optional xeq_lab."""
    xeq_p = plant_xeq(cfg, rec["T_K"])
    xeq_l = rec.get("xeq_lab") or lab_xeq(cfg, rec)
    top = cfg["plant"]["approach"] * xeq_p
    best = min((_at(cfg, rec, f * top, xeq_p, xeq_l) for f in XP_GRID), key=lambda t: t[0])
    best[1]["Xeq_lab"] = xeq_l
    return best if detail else best[0]


def reference_record(cfg):
    ref = cfg["reference"]
    rec = dict(T_K=ref["T_K"], X=ref["X"], S=ref["S"], r=ref["r"], t_cycle_h=ref.get("t_cycle_h"),
               components=[dict(element=e, wt_pct=w) for e, w in ref["elements"]])
    rec["xeq_lab"] = plant_xeq(cfg, ref["T_K"])     # the reference productivity is at plant conditions
    return rec


def init_reference(cfg):
    """Throughput, off-stream fraction and catalyst inventory of the reference plant at its published per-pass
    conversion; the scalings are normalised to them."""
    ref, en = cfg["reference"], cfg["energy"]
    m = _masses(cfg, ref["S"])
    fresh = m[cfg["stoich"]["key"]] if en["fresh_basis"] == "key" else sum(m.values())
    ref["F"] = fresh / ref["X"]
    rg = cfg["regeneration"]
    ref["f_off"] = (rg["t_regen_h"] / (max(ref["t_cycle_h"], rg["t_cycle_min_h"]) + rg["t_regen_h"])
                    if rg["enabled"] else 0.0)
    ref["W_t"] = (cfg["plant"]["capacity_t_per_y"] / cfg["plant"]["hours_per_y"]) / ref["r"]
