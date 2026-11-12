import math, json, ast
import numpy as np

REACTION = {
    "key": "C3H8",
    "product": "C3H6",
    "cofeed": None,
    "MW": {"C3H8": 44.09562, "C3H6": 42.07974, "H2": 2.01588},
    "nu": {"C3H8": -1.0, "C3H6": 1.0, "H2": 1.0},
}

# Central parameters. Uncertainty/source table is in sources.csv.
PARAM = {
    "capacity_tpy": 750000.0,
    "hours_y": 8000.0,
    "propane_price": 390.0,
    "gas_price_per_GJ": 5.0,
    "electricity_price_per_GJ": 0.080 * 277.7777777778,
    "h2_credit_per_kg": 1.5,
    "base_capex": 1.20e9,
    "crf": 0.117,
    "fixed_opex_frac": 0.035,
    "furnace_eff": 0.88,
    "heat_recovery": 0.75,
    "dH_kJ_mol": 124.3,
    "dS_J_molK": 126.5,
    "c3_splitter_GJ_per_kmol": 0.025,
    "h2_sep_GJ_per_kmol": 0.003,
    "comp_eff": 0.72,
    "cooling_aux": 0.02,
    "cat_support_price": 20.0,
    "cat_life_y": 3.0,
    "regen_penalty": 2.0,
}
METAL_PRICE = {
    "Pt": 32000.0, "Rh": 150000.0, "Ga": 300.0, "In": 250.0,
    "Zn": 4.0, "Sn": 25.0, "Cu": 9.0, "Fe": 1.0, "Mn": 2.0,
    "Zr": 30.0, "Ti": 12.0, "La": 5.0, "Y": 35.0, "Ce": 5.0,
    "Mg": 3.0, "Al": 3.0, "Si": 2.0, "Ca": 3.0, "Ba": 5.0,
    "K": 2.0, "Na": 2.0, "Cr": 10.0, "V": 30.0, "Mo": 40.0,
    "Ni": 20.0, "Co": 35.0, "P": 3.0, "B": 5.0, "C": 1.0,
}
UNIT_NAMES = [
    "fresh_propane_pressurisation", "recycle_mixer", "feed_vaporiser",
    "feed_effluent_exchanger", "charge_furnace", "PDH_reactor",
    "catalyst_regenerator", "effluent_cooler_knockout", "product_compressor",
    "hydrogen_recovery", "C3_splitter", "utilities_offsites"
]
MWP = REACTION["MW"]["C3H6"]
MWA = REACTION["MW"]["C3H8"]
MWH2 = REACTION["MW"]["H2"]
KMOL_PROD_PER_T = 1000.0 / MWP


def _f(x, default):
    try:
        if x is None: return default
        if isinstance(x, float) and math.isnan(x): return default
        return float(x)
    except Exception:
        return default


def equilibrium_Kp(T_K):
    # ideal gas, 1 bar standard state: ln Kp = dS/R - dH/(RT)
    R = 8.314462618
    return math.exp(PARAM["dS_J_molK"] / R - (PARAM["dH_kJ_mol"] * 1000.0) / (R * T_K))


def equilibrium_conversion(T_K, P_bar):
    Kp = equilibrium_Kp(T_K)
    P = max(0.05, float(P_bar))
    # pure propane feed A -> B + H2: Kp = P*x^2/(1-x^2)
    return math.sqrt(max(0.0, Kp / (P + Kp)))


def approach_integral(X, Xeq):
    X = max(1e-5, min(float(X), 0.985 * Xeq))
    xs = np.linspace(0.0, X, 240)
    # For the pure-feed stoichiometric gas mixture Q/K = (x^2/(1-x^2))/(Xeq^2/(1-Xeq^2))
    denom = 1.0 - (xs * xs / np.maximum(1e-12, 1.0 - xs * xs)) / max(1e-12, (Xeq * Xeq / max(1e-12, 1.0 - Xeq * Xeq)))
    denom = np.clip(denom, 0.025, None)
    return float(np.trapz(1.0 / denom, xs))


def catalyst_price(components):
    price = PARAM["cat_support_price"]
    try:
        comps = components
        if isinstance(comps, str):
            comps = ast.literal_eval(comps)
        for el, wt in comps or []:
            if wt is None: continue
            price += METAL_PRICE.get(str(el), 10.0) * max(0.0, float(wt)) / 100.0
    except Exception:
        pass
    return price


def _compressor_power(kmol_per_t, T_in, P_in, P_out, gamma=1.13, MWmix=32.0):
    if P_out <= P_in or kmol_per_t <= 0: return 0.0
    RkJ = 8.314462618
    eta = PARAM["comp_eff"]
    ratio = P_out / P_in
    work_kJ_per_kmol = gamma / (gamma - 1.0) * RkJ * T_in / eta * (ratio ** ((gamma - 1.0) / gamma) - 1.0)
    return kmol_per_t * work_kJ_per_kmol / 1e6


def _record_val(rec, key, default):
    if isinstance(rec, dict): return _f(rec.get(key), default)
    return _f(getattr(rec, key, default), default)


def _record_obj(rec, key, default=None):
    if isinstance(rec, dict): return rec.get(key, default)
    return getattr(rec, key, default)


def _base_calcs(rec, Xop):
    T = _record_val(rec, "T_K", 873.15)
    P = max(1.05, _record_val(rec, "P_bar", 1.5))
    S = max(0.50, min(0.999, _record_val(rec, "S", 0.90)))
    Xlab = max(0.005, min(0.90, _record_val(rec, "X", 0.20)))
    rlab = max(1e-4, _record_val(rec, "r", 0.2))
    Xeq = equilibrium_conversion(T, P)
    Xlab_eff = min(Xlab, 0.94 * Xeq)
    Ilab = approach_integral(Xlab_eff, Xeq)
    Iop = approach_integral(Xop, Xeq)
    rel = (Xop / Iop) / max(1e-9, (Xlab_eff / Ilab))
    # temperature mismatch not used because plant operates at the reported catalyst temperature
    r_eff = max(1e-5, rlab * rel)
    nP = KMOL_PROD_PER_T
    fresh_propane_kmol = nP / S
    fresh_propane_t = fresh_propane_kmol * MWA / 1000.0
    h2_kg = nP * MWH2
    propane_to_reactor_kmol = nP / max(1e-5, S * Xop)
    recycle_kmol = max(0.0, propane_to_reactor_kmol - fresh_propane_kmol)
    unselective_propane_equiv_kmol = max(0.0, fresh_propane_kmol - nP)
    # effluent = unconverted propane recycle + desired propylene + H2 + propane-equivalent undesired C3 material
    effluent_kmol = recycle_kmol + nP + nP + unselective_propane_equiv_kmol
    c3_to_splitter_kmol = recycle_kmol + nP + unselective_propane_equiv_kmol
    return dict(T=T, P=P, S=S, Xlab=Xlab, r_eff=r_eff, Xeq=Xeq, nP=nP,
                fresh_propane_kmol=fresh_propane_kmol, fresh_propane_t=fresh_propane_t,
                h2_kg=h2_kg, propane_to_reactor_kmol=propane_to_reactor_kmol,
                recycle_kmol=recycle_kmol, unselective_propane_equiv_kmol=unselective_propane_equiv_kmol,
                effluent_kmol=effluent_kmol, c3_to_splitter_kmol=c3_to_splitter_kmol)


def _cost_at_X(rec, Xop):
    c = _base_calcs(rec, Xop)
    T = c["T"]; P = c["P"]
    # heat: reaction enthalpy plus unrecovered sensible heat of circulating C3 from 320 K to reactor T
    q_rxn = c["nP"] * PARAM["dH_kJ_mol"] / 1000.0  # GJ/t (kJ/mol == GJ/kmol)
    cp_c3_GJ_per_kmolK = 0.000095
    sensible = c["propane_to_reactor_kmol"] * cp_c3_GJ_per_kmolK * max(0.0, T - 320.0)
    purchased_furnace = (q_rxn + (1.0 - PARAM["heat_recovery"]) * sensible) / PARAM["furnace_eff"]
    cooler_removed = max(0.0, PARAM["heat_recovery"] * sensible)
    cooling_purchased = cooler_removed * PARAM["cooling_aux"]
    P_reactor = max(1.05, P)
    comp_gj = _compressor_power(c["effluent_kmol"], 330.0, P_reactor, 20.0)
    fresh_comp_gj = _compressor_power(c["fresh_propane_kmol"], 300.0, 1.0, P_reactor, gamma=1.13)
    h2sep_gj = PARAM["h2_sep_GJ_per_kmol"] * c["effluent_kmol"]
    c3split_gj = PARAM["c3_splitter_GJ_per_kmol"] * c["c3_to_splitter_kmol"]
    feed_cost = c["fresh_propane_t"] * PARAM["propane_price"]
    energy_cost = (purchased_furnace + h2sep_gj + c3split_gj + cooling_purchased) * PARAM["gas_price_per_GJ"] + (comp_gj + fresh_comp_gj) * PARAM["electricity_price_per_GJ"]
    h2_credit = c["h2_kg"] * PARAM["h2_credit_per_kg"]
    # Catalyst inventory from transferred productivity
    prod_rate_kg_h = PARAM["capacity_tpy"] * 1000.0 / PARAM["hours_y"]
    cat_inventory_kg = prod_rate_kg_h / c["r_eff"]
    cat_unit_price = catalyst_price(_record_obj(rec, "components", _record_obj(rec, "elements", [])))
    cat_makeup = cat_inventory_kg * cat_unit_price / (PARAM["cat_life_y"] * PARAM["capacity_tpy"])
    tcy = _record_val(rec, "t_cycle_h", 24.0)
    if tcy <= 0 or tcy > 1e5: tcy = 24.0
    regen_pen = PARAM["regen_penalty"] * max(0.25, min(20.0, 24.0 / max(1.0, tcy)))
    catalyst_cost = cat_makeup + regen_pen
    # Installed capital scales with capacity and process severity/throughput. Fractions sum to one at base case.
    base = PARAM["base_capex"]
    sep_scale = (c["c3_to_splitter_kmol"] / (KMOL_PROD_PER_T / 0.38)) ** 0.65
    comp_scale = ((comp_gj + 0.02) / 0.25) ** 0.65
    rxn_scale = (cat_inventory_kg / 250000.0) ** 0.45
    heat_scale = ((purchased_furnace * PARAM["furnace_eff"]) / 3.6) ** 0.65
    stab_mult = 1.0 + min(1.5, 6.0 / max(1.0, tcy))
    fr = {
        "fresh_propane_pressurisation": 0.015 * (c["fresh_propane_t"] / 1.08) ** 0.65,
        "recycle_mixer": 0.005,
        "feed_vaporiser": 0.025 * heat_scale,
        "feed_effluent_exchanger": 0.055 * heat_scale,
        "charge_furnace": 0.090 * heat_scale,
        "PDH_reactor": 0.220 * rxn_scale * stab_mult,
        "catalyst_regenerator": 0.070 * rxn_scale * stab_mult,
        "effluent_cooler_knockout": 0.030 * (c["effluent_kmol"] / (KMOL_PROD_PER_T * (1+0.38)/0.38)) ** 0.65,
        "product_compressor": 0.090 * comp_scale,
        "hydrogen_recovery": 0.070 * (c["effluent_kmol"] / (KMOL_PROD_PER_T * (1+0.38)/0.38)) ** 0.65,
        "C3_splitter": 0.270 * sep_scale,
        "utilities_offsites": 0.080,
    }
    # normalize gently to preserve base capex meaning but allow severity movement
    capex_units = {k: max(0.0, base*v) for k, v in fr.items()}
    capex = sum(capex_units.values())
    capital_cost = capex * (PARAM["crf"] + PARAM["fixed_opex_frac"]) / PARAM["capacity_tpy"]
    other = -h2_credit
    total = feed_cost + energy_cost + capital_cost + catalyst_cost + other
    units = []
    def add(name, typ, pe=0.0, cap=0.0, **kw):
        d = {"name": name, "type": typ, "purchased_energy_GJ_per_t": float(pe), "internal_fuel_GJ_per_t": 0.0, "capex_usd": float(cap)}
        d.update(kw); units.append(d)
    add("fresh_propane_pressurisation", "compressor", fresh_comp_gj, capex_units["fresh_propane_pressurisation"], kmol_per_t=c["fresh_propane_kmol"], T_in_K=300.0, P_in_bar=1.0, P_out_bar=P_reactor, power_GJ_per_t=fresh_comp_gj)
    add("recycle_mixer", "other", 0.0, capex_units["recycle_mixer"])
    add("feed_vaporiser", "heat_exchanger", 0.0, capex_units["feed_vaporiser"], recovered_heat_GJ_per_t=0.0)
    add("feed_effluent_exchanger", "heat_exchanger", 0.0, capex_units["feed_effluent_exchanger"], recovered_heat_GJ_per_t=PARAM["heat_recovery"]*sensible)
    add("charge_furnace", "furnace", purchased_furnace, capex_units["charge_furnace"], heat_added_GJ_per_t=purchased_furnace*PARAM["furnace_eff"])
    add("PDH_reactor", "reactor", 0.0, capex_units["PDH_reactor"], heat_duty_GJ_per_t=q_rxn, catalyst_inventory_kg=cat_inventory_kg)
    add("catalyst_regenerator", "regenerator", 0.0, capex_units["catalyst_regenerator"], t_cycle_h=tcy)
    add("effluent_cooler_knockout", "knockout", cooling_purchased, capex_units["effluent_cooler_knockout"], cooling_duty_GJ_per_t=cooler_removed)
    add("product_compressor", "compressor", comp_gj, capex_units["product_compressor"], kmol_per_t=c["effluent_kmol"], T_in_K=330.0, P_in_bar=P_reactor, P_out_bar=20.0, power_GJ_per_t=comp_gj)
    yH = c["nP"] / max(1e-9, c["effluent_kmol"]); yP = c["nP"] / max(1e-9, c["effluent_kmol"]); yA = max(0.0, 1-yH-yP)
    add("hydrogen_recovery", "separation", h2sep_gj, capex_units["hydrogen_recovery"], feed={"kmol_per_t": c["effluent_kmol"], "mol_frac": {"C3H8": yA, "C3H6": yP, "H2": yH}}, outlets=[{"name":"hydrogen_product","kmol_per_t":c["nP"],"mol_frac":{"H2":1.0}}, {"name":"C3_liquid","kmol_per_t":c["c3_to_splitter_kmol"],"mol_frac":{"C3H8":max(0.0,(c["recycle_kmol"]+c["unselective_propane_equiv_kmol"])/max(1e-9,c["c3_to_splitter_kmol"])),"C3H6":c["nP"]/max(1e-9,c["c3_to_splitter_kmol"])}}])
    add("C3_splitter", "separation", c3split_gj, capex_units["C3_splitter"], feed={"kmol_per_t": c["c3_to_splitter_kmol"], "mol_frac": {"C3H8": max(0.0, (c["recycle_kmol"]+c["unselective_propane_equiv_kmol"])/max(1e-9,c["c3_to_splitter_kmol"])), "C3H6": c["nP"]/max(1e-9,c["c3_to_splitter_kmol"])}}, outlets=[{"name":"propylene_product","kmol_per_t":c["nP"],"mol_frac":{"C3H6":1.0}}, {"name":"propane_recycle","kmol_per_t":c["recycle_kmol"],"mol_frac":{"C3H8":1.0}}, {"name":"purge_propane_byproduct","kmol_per_t":c["unselective_propane_equiv_kmol"],"mol_frac":{"C3H8":1.0}}])
    add("utilities_offsites", "offsites", 0.0, capex_units["utilities_offsites"])
    purchased_energy = purchased_furnace + h2sep_gj + c3split_gj + cooling_purchased + comp_gj + fresh_comp_gj
    physics = {
        "reactor": {"T_K": T, "P_bar": P_reactor, "feed_mol_frac": {"C3H8": 1.0}, "per_pass_conversion": Xop, "heat_duty_GJ_per_t": q_rxn},
        "boundary": {"in_t_per_t": {"C3H8": c["fresh_propane_t"]}, "out_t_per_t": {"C3H6": 1.0, "H2": c["h2_kg"]/1000.0, "C3H8": c["unselective_propane_equiv_kmol"]*MWA/1000.0}},
        "units": units,
    }
    return dict(cost_usd_per_t=float(total), parts={"feed":float(feed_cost), "energy":float(energy_cost), "capital":float(capital_cost), "catalyst":float(catalyst_cost), "other":float(other)}, operating={"T_K":T,"P_bar":P_reactor,"per_pass_conversion":float(Xop)}, balances={"key_feed_t_per_t":float(c["fresh_propane_t"]), "energy_GJ_per_t":float(purchased_energy), "capex_usd":float(capex), "capacity_t_per_y":PARAM["capacity_tpy"]}, physics=physics)


def plant_cost(rec):
    T = _record_val(rec, "T_K", 873.15)
    P = max(1.05, _record_val(rec, "P_bar", 1.5))
    Xeq = equilibrium_conversion(T, P)
    xmax = max(0.02, min(0.86, 0.92 * Xeq))
    xmin = min(0.05, 0.5*xmax)
    grid = np.linspace(xmin, xmax, 45)
    vals = [_cost_at_X(rec, float(x)) for x in grid]
    best = min(vals, key=lambda d: d["cost_usd_per_t"])
    # exact part summation after numerical minimization
    best["cost_usd_per_t"] = float(sum(best["parts"].values()))
    return best


def reference():
    rec = {"T_K": 873.15, "P_bar": 1.5, "X": 0.35, "S": 0.90, "r": 1.0, "y_key": 1.0, "y_cofeed": 0.0, "t_cycle_h": 24.0, "components": [["Pt",0.3],["Sn",0.6]], "catalyst": "reference Pt-Sn/Al2O3 industrial PDH"}
    out = plant_cost(rec)
    out["name"] = "750 kt/y continuous propane dehydrogenation reference plant"
    out["record"] = rec
    return out
