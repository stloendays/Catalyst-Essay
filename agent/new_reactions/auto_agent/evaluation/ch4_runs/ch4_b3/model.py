import math, ast
import numpy as np
from scipy.optimize import brentq

REACTION = {
    "key": "CO2",
    "product": "CH4",
    "cofeed": "H2",
    "MW": {"CO2": 44.0095, "H2": 2.01588, "CH4": 16.0425, "H2O": 18.01528, "CO": 28.0101},
    "nu": {"CO2": -1.0, "H2": -4.0, "CH4": 1.0, "H2O": 2.0},
}

P = {
    "capacity_tpy": 100000.0,
    "operating_h": 8000.0,
    "crf": 0.10,
    "h2_price_kg": 5.0,
    "co2_price_t": 50.0,
    "elec_price_kwh": 0.0964,
    "gas_price_mmbtu": 5.0,
    "pef_elec": 3.0,
    "eta_comp": 0.75,
    "comp_cost_kw": 1800.0,
    "feed_pin": 1.01325,
    "product_pout": 30.0,
    "min_loop_p": 10.0,
    "purge": 0.02,
    "ch4_recovery": 0.995,
    "reactor_base_per_kgpy": 120.0,
    "reactor_cat_factor": 200.0,
    "hx_cost_MW": 120000.0,
    "cooler_cost_MW": 80000.0,
    "furnace_cost_MW": 100000.0,
    "membrane_per_kgpy": 60.0,
    "offsites_fraction": 0.25,
    "fixed_om_fraction": 0.04,
    "cooling_elec_frac": 0.01,
    "base_cat_life_y": 3.0,
    "cat_mfg_factor": 3.0,
    "support_price": 20.0,
}

MW = REACTION["MW"]
R = 8.314462618
CP_GAS_GJ_PER_KMOL_K = 3.5e-5   # average hot loop gas Cp, GJ/kmol/K
DH_METH_GJ_PER_KMOL = -0.165     # CO2+4H2 -> CH4+2H2O(g)
DH_RWGS_GJ_PER_KMOL = 0.041      # CO2+H2 -> CO+H2O(g)

PRICE = {
    "Ni": 20.0, "Co": 35.0, "Fe": 0.2, "Ru": 15000.0, "Rh": 150000.0,
    "Pt": 32000.0, "Pd": 30000.0, "Ir": 150000.0, "Ce": 30.0,
    "Zr": 30.0, "La": 30.0, "Y": 30.0, "Ti": 20.0, "Mn": 4.0,
    "Cu": 10.0, "Mg": 5.0, "Al": 3.0, "Si": 3.0, "C": 3.0, "O": 0.0,
}


def _float(x, default=None):
    try:
        if x is None: return default
        if isinstance(x, float) and math.isnan(x): return default
        return float(x)
    except Exception:
        return default


def _components(rec):
    c = rec.get("components", []) if isinstance(rec, dict) else []
    if isinstance(c, str):
        try: c = ast.literal_eval(c)
        except Exception: c = []
    out = []
    for item in c or []:
        try:
            el = str(item[0])
            wt = None if item[1] is None else float(item[1])
            out.append((el, wt))
        except Exception:
            pass
    return out


def _catalyst_price(rec):
    comps = _components(rec)
    known = 0.0
    raw = 0.0
    any_known = False
    for el, wt in comps:
        if wt is not None and wt > 0:
            f = max(0.0, min(1.0, wt / 100.0))
            raw += f * PRICE.get(el, P["support_price"])
            known += f
            any_known = True
    if any_known:
        raw += max(0.0, 1.0 - known) * P["support_price"]
    else:
        # If wt% is absent, distinguish PGM named catalysts from base-metal catalysts.
        name = str(rec.get("catalyst", ""))
        raw = P["support_price"]
        for el in ["Ru", "Rh", "Pt", "Pd", "Ir", "Ni", "Co"]:
            if el.lower() in name.lower():
                assumed_wt = 0.02 if el in ["Ru", "Rh", "Pt", "Pd", "Ir"] else 0.20
                raw += assumed_wt * PRICE.get(el, P["support_price"])
    return max(5.0, P["cat_mfg_factor"] * raw)


def _kp_methanation(T):
    # Constant dH/dS estimate from standard formation data, gases, 298 K.
    dH = -165000.0
    dG298 = -113600.0
    dS = (dH - dG298) / 298.15
    dG = dH - T * dS
    return math.exp(max(-100.0, min(100.0, -dG / (R * T))))


def _eq_conversion(T, Pbar):
    K = _kp_methanation(T)
    Pbar = max(1e-6, Pbar)
    def q_minus_k(x):
        x = min(max(x, 1e-12), 0.999999999)
        nco2 = 1.0 - x
        nh2 = 4.0 * (1.0 - x)
        nch4 = x
        nh2o = 2.0 * x
        nt = nco2 + nh2 + nch4 + nh2o
        yco2, yh2, ych4, yh2o = nco2/nt, nh2/nt, nch4/nt, nh2o/nt
        Q = (ych4*Pbar) * (yh2o*Pbar)**2 / ((yco2*Pbar) * (yh2*Pbar)**4)
        return math.log(Q) - math.log(K)
    try:
        if q_minus_k(0.999999) < 0:
            return 0.999999
        return brentq(q_minus_k, 1e-9, 0.999999, maxiter=100)
    except Exception:
        return 0.95


def _compressor(kmol_per_t, T_in, P_in, P_out, species="H2"):
    if kmol_per_t <= 0 or P_out <= P_in * 1.0001:
        return 0.0, 0.0
    gamma = 1.4 if species == "H2" else 1.3
    stages_ratio = max(1.0, P_out / max(P_in, 1e-6))
    # ideal gas isentropic work, GJ/t product
    w_gj = kmol_per_t * R * T_in / 1e6 * gamma/(gamma-1.0) * (stages_ratio**((gamma-1.0)/gamma) - 1.0) / P["eta_comp"]
    kw = w_gj * P["capacity_tpy"] / P["operating_h"] * 1e6 / 3600.0
    return w_gj, kw


def _annualize_capex(capex):
    return capex * (P["crf"] + P["fixed_om_fraction"]) / P["capacity_tpy"]


def _cost_for_x(rec, x):
    T = max(350.0, _float(rec.get("T_K"), 573.15))
    Plab = _float(rec.get("P_bar"), 1.01325)
    Pbar = max(P["min_loop_p"], Plab)
    Xlab = max(1e-4, min(0.999, _float(rec.get("X"), x)))
    S = max(0.50, min(1.0, _float(rec.get("S"), 1.0)))
    r = max(1e-5, _float(rec.get("r"), 0.05))
    x = max(0.01, min(x, 0.98, Xlab, 0.98 * _eq_conversion(T, Pbar)))

    nprod = 1000.0 / MW["CH4"]  # kmol CH4 in saleable product per tonne CH4 product
    purge = P["purge"]
    rec_ch4 = P["ch4_recovery"]
    a_ch4 = (1.0 - purge) * (1.0 - rec_ch4)
    gen_ch4 = nprod * (1.0 - a_ch4) / rec_ch4
    recycle_ch4 = a_ch4 * gen_ch4 / max(1e-12, (1.0 - a_ch4))
    eff_ch4 = gen_ch4 + recycle_ch4
    product_ch4 = rec_ch4 * eff_ch4
    tail_ch4 = (1.0 - rec_ch4) * eff_ch4
    purge_ch4 = purge * tail_ch4
    recycle_ch4_out = (1.0 - purge) * tail_ch4

    co2_conv = gen_ch4 / S
    co_gen = max(0.0, co2_conv - gen_ch4)
    h2_cons = 4.0 * gen_ch4 + co_gen
    water = 2.0 * gen_ch4 + co_gen
    reactor_co2_in = co2_conv / x
    unreact_co2 = max(0.0, reactor_co2_in - co2_conv)
    reactor_h2_in = 4.0 * reactor_co2_in
    unreact_h2 = max(0.0, reactor_h2_in - h2_cons)

    # Inert/byproduct recycle inventories from purge balance.
    recycle_co2 = (1.0 - purge) * unreact_co2
    purge_co2 = purge * unreact_co2
    recycle_h2 = (1.0 - purge) * unreact_h2
    purge_h2 = purge * unreact_h2
    recycle_co = (1.0 - purge) / purge * co_gen if co_gen > 0 else 0.0
    purge_co = co_gen

    fresh_co2 = co2_conv + purge_co2
    fresh_h2 = h2_cons + purge_h2

    # Hourly production and catalyst inventory.
    prod_kg_h = P["capacity_tpy"] * 1000.0 / P["operating_h"]
    gross_ch4_kg_h = prod_kg_h * gen_ch4 / nprod
    r_eff = max(1e-6, r * min(1.0, x / Xlab))
    cat_kg = gross_ch4_kg_h / r_eff
    tcyc = _float(rec.get("t_cycle_h"), None)
    if tcyc is not None and tcyc > 0:
        # Time to 10% loss converted to approximate replacement-equivalent life, capped.
        cat_life_y = max(0.05, min(P["base_cat_life_y"], 10.0 * tcyc / P["operating_h"]))
    else:
        cat_life_y = P["base_cat_life_y"]
    cat_price = _catalyst_price(rec)

    feed_cost = (fresh_h2 * MW["H2"] / 1000.0) * 1000.0 * P["h2_price_kg"] + (fresh_co2 * MW["CO2"] / 1000.0) * P["co2_price_t"]
    catalyst_cost = cat_kg * cat_price / cat_life_y / P["capacity_tpy"]

    # Compression duties and capex.
    w_co2, kw_co2 = _compressor(fresh_co2, 298.15, P["feed_pin"], Pbar, "CO2")
    w_h2, kw_h2 = _compressor(fresh_h2, 298.15, P["feed_pin"], Pbar, "H2")
    recycle_kmol = recycle_co2 + recycle_h2 + recycle_co + recycle_ch4_out
    w_rec, kw_rec = _compressor(recycle_kmol, 313.15, max(1.0, 0.92*Pbar), Pbar, "CO2")
    w_prod, kw_prod = _compressor(product_ch4, 298.15, max(1.0, 0.95*Pbar), max(P["product_pout"], Pbar), "CH4")

    # Heat duties.
    q_rxn = DH_METH_GJ_PER_KMOL * co2_conv
    reactor_feed_kmol = reactor_co2_in + reactor_h2_in + recycle_co + recycle_ch4
    preheat_target = max(0.0, (T - 298.15) * reactor_feed_kmol * CP_GAS_GJ_PER_KMOL_K)
    recoverable = min(max(0.0, -0.25*q_rxn), 0.80 * preheat_target)
    trim_heat = max(0.0, preheat_target - recoverable)
    cooler_duty = max(0.0, -q_rxn + max(0.0, (T-313.15))* (reactor_feed_kmol + gen_ch4 + water) * CP_GAS_GJ_PER_KMOL_K * 0.5)

    sep_primary = 3.0
    sep_elec_final = sep_primary / P["pef_elec"]
    elec_gj = w_co2 + w_h2 + w_rec + w_prod + P["cooling_elec_frac"] * cooler_duty + sep_elec_final
    fuel_gj = trim_heat / 0.90
    energy_cost = elec_gj * 277.7778 * P["elec_price_kwh"] + fuel_gj * 0.947817 * P["gas_price_mmbtu"]
    purchased_primary = elec_gj * P["pef_elec"] + fuel_gj

    # Installed equipment capital per submitted flowsheet unit.
    cap_co2 = kw_co2 * P["comp_cost_kw"]
    cap_h2 = kw_h2 * P["comp_cost_kw"]
    cap_rec = kw_rec * P["comp_cost_kw"]
    cap_prod = kw_prod * P["comp_cost_kw"]
    direct_capacity = P["capacity_tpy"] * 1000.0
    cap_mixer = 500000.0
    cap_hx = max(100000.0, P["hx_cost_MW"] * (recoverable * P["capacity_tpy"] / P["operating_h"] / 3.6))
    cap_furnace = max(50000.0, P["furnace_cost_MW"] * (trim_heat * P["capacity_tpy"] / P["operating_h"] / 3.6))
    cap_reactor = P["reactor_base_per_kgpy"] * direct_capacity/1000.0 + P["reactor_cat_factor"] * cat_kg
    cap_cooler = max(100000.0, P["cooler_cost_MW"] * (cooler_duty * P["capacity_tpy"] / P["operating_h"] / 3.6))
    cap_sep = P["membrane_per_kgpy"] * direct_capacity/1000.0
    direct_without_off = cap_co2+cap_h2+cap_rec+cap_prod+cap_mixer+cap_hx+cap_furnace+cap_reactor+cap_cooler+cap_sep+250000.0
    cap_off = P["offsites_fraction"] * direct_without_off
    cap_total = direct_without_off + cap_off
    capital_cost = _annualize_capex(cap_total)
    other_cost = 0.0

    parts = {"feed": feed_cost, "energy": energy_cost, "capital": capital_cost, "catalyst": catalyst_cost, "other": other_cost}

    feed_frac = {
        "CO2": reactor_co2_in/reactor_feed_kmol,
        "H2": reactor_h2_in/reactor_feed_kmol,
        "CO": recycle_co/reactor_feed_kmol if reactor_feed_kmol else 0.0,
        "CH4": recycle_ch4/reactor_feed_kmol if reactor_feed_kmol else 0.0,
    }
    dry_feed = eff_ch4 + unreact_co2 + unreact_h2 + recycle_co + co_gen
    tail_kmol = tail_ch4 + unreact_co2 + unreact_h2 + recycle_co + co_gen
    recycle_tail = recycle_ch4_out + recycle_co2 + recycle_h2 + recycle_co
    vent_tail = purge_ch4 + purge_co2 + purge_h2 + purge_co

    def stream(kmol, comp):
        return {"kmol_per_t": kmol, "mol_frac": comp}

    units = [
        {"name":"CO2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":w_co2*P["pef_elec"],"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_co2,"kmol_per_t":fresh_co2,"T_in_K":298.15,"P_in_bar":P["feed_pin"],"P_out_bar":Pbar,"power_GJ_per_t":w_co2},
        {"name":"H2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":w_h2*P["pef_elec"],"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_h2,"kmol_per_t":fresh_h2,"T_in_K":298.15,"P_in_bar":P["feed_pin"],"P_out_bar":Pbar,"power_GJ_per_t":w_h2},
        {"name":"Recycle compressor","type":"compressor","purchased_energy_GJ_per_t":w_rec*P["pef_elec"],"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_rec,"kmol_per_t":recycle_kmol,"T_in_K":313.15,"P_in_bar":max(1.0,0.92*Pbar),"P_out_bar":Pbar,"power_GJ_per_t":w_rec},
        {"name":"Feed mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_mixer},
        {"name":"Feed effluent heat exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_hx,"recovered_heat_GJ_per_t":recoverable},
        {"name":"Trim preheater","type":"furnace","purchased_energy_GJ_per_t":fuel_gj,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_furnace,"heat_duty_GJ_per_t":trim_heat},
        {"name":"Cooled methanation reactor","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_reactor,"T_K":T,"P_bar":Pbar,"per_pass_conversion":x,"heat_duty_GJ_per_t":q_rxn,"catalyst_inventory_kg":cat_kg},
        {"name":"Effluent cooler and water knockout","type":"knockout","purchased_energy_GJ_per_t":P["cooling_elec_frac"]*cooler_duty*P["pef_elec"],"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_cooler,"cooling_duty_GJ_per_t":cooler_duty},
        {"name":"Methane purification membrane","type":"separation","purchased_energy_GJ_per_t":sep_primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_sep,"feed":stream(dry_feed,{"CH4":eff_ch4/dry_feed,"CO2":unreact_co2/dry_feed,"H2":unreact_h2/dry_feed,"CO":(recycle_co+co_gen)/dry_feed}),"outlets":[stream(product_ch4,{"CH4":1.0}),stream(tail_kmol,{"CH4":tail_ch4/tail_kmol,"CO2":unreact_co2/tail_kmol,"H2":unreact_h2/tail_kmol,"CO":(recycle_co+co_gen)/tail_kmol})]},
        {"name":"Product compressor","type":"compressor","purchased_energy_GJ_per_t":w_prod*P["pef_elec"],"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_prod,"kmol_per_t":product_ch4,"T_in_K":298.15,"P_in_bar":max(1.0,0.95*Pbar),"P_out_bar":max(P["product_pout"],Pbar),"power_GJ_per_t":w_prod},
        {"name":"Recycle purge splitter","type":"separation","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":250000.0,"feed":stream(tail_kmol,{"CH4":tail_ch4/tail_kmol,"CO2":unreact_co2/tail_kmol,"H2":unreact_h2/tail_kmol,"CO":(recycle_co+co_gen)/tail_kmol}),"outlets":[stream(vent_tail,{"CH4":purge_ch4/vent_tail if vent_tail else 0.0,"CO2":purge_co2/vent_tail if vent_tail else 0.0,"H2":purge_h2/vent_tail if vent_tail else 0.0,"CO":purge_co/vent_tail if vent_tail else 0.0}),stream(recycle_tail,{"CH4":recycle_ch4_out/recycle_tail if recycle_tail else 0.0,"CO2":recycle_co2/recycle_tail if recycle_tail else 0.0,"H2":recycle_h2/recycle_tail if recycle_tail else 0.0,"CO":recycle_co/recycle_tail if recycle_tail else 0.0})]},
        {"name":"Utilities and offsites","type":"offsites","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_off},
    ]

    return {
        "cost_usd_per_t": sum(parts.values()),
        "parts": parts,
        "operating": {"T_K": T, "P_bar": Pbar, "per_pass_conversion": x},
        "balances": {
            "key_feed_t_per_t": fresh_co2 * MW["CO2"] / 1000.0,
            "energy_GJ_per_t": purchased_primary,
            "capex_usd": cap_total,
            "capacity_t_per_y": P["capacity_tpy"],
        },
        "physics": {
            "reactor": {"T_K": T, "P_bar": Pbar, "feed_mol_frac": feed_frac, "per_pass_conversion": x, "heat_duty_GJ_per_t": q_rxn},
            "boundary": {
                "in_t_per_t": {"CO2": fresh_co2*MW["CO2"]/1000.0, "H2": fresh_h2*MW["H2"]/1000.0},
                "out_t_per_t": {"CH4": product_ch4*MW["CH4"]/1000.0, "H2O": water*MW["H2O"]/1000.0, "CO2": purge_co2*MW["CO2"]/1000.0, "H2": purge_h2*MW["H2"]/1000.0, "CO": purge_co*MW["CO"]/1000.0, "CH4": product_ch4*MW["CH4"]/1000.0 + purge_ch4*MW["CH4"]/1000.0},
            },
            "units": units,
        },
    }


def plant_cost(rec):
    T = max(350.0, _float(rec.get("T_K"), 573.15))
    Plab = _float(rec.get("P_bar"), 1.01325)
    Pbar = max(P["min_loop_p"], Plab)
    Xlab = max(0.02, min(0.95, _float(rec.get("X"), 0.5)))
    xeq = 0.98 * _eq_conversion(T, Pbar)
    xmax = max(0.02, min(0.95, Xlab, xeq))
    xmin = max(0.01, min(0.20, 0.25*xmax))
    grid = np.unique(np.r_[np.linspace(xmin, xmax, 28), xmax])
    best = None
    for x in grid:
        c = _cost_for_x(rec, float(x))
        if (best is None) or (c["cost_usd_per_t"] < best["cost_usd_per_t"]):
            best = c
    return best


def reference():
    rec = {"T_K": 573.15, "P_bar": 10.0, "X": 0.80, "S": 0.99, "r": 1.0,
           "y_key": 0.20, "y_cofeed": 0.80, "t_cycle_h": None,
           "components": [["Ni", 20.0], ["Al", None]], "catalyst": "reference 20 wt% Ni/Al2O3"}
    out = plant_cost(rec)
    out["name"] = "100 kt/y catalytic CO2 methanation reference plant"
    out["record"] = rec
    return out
