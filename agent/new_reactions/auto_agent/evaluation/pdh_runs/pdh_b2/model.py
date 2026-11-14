import math
import numpy as np

REACTION = {
    "key": "C3H8",
    "product": "C3H6",
    "cofeed": None,
    "MW": {"C3H8": 44.096, "C3H6": 42.080, "H2": 2.016},
}

PARAM = {
    "capacity_t_y": 600000.0,
    "hours_y": 8000.0,
    "base_capex_usd": 900e6,
    "capex_ref_capacity_t_y": 750000.0,
    "capital_charge_factor": 0.117,
    "propane_price_usd_t": 520.0,
    "gas_price_usd_GJ": 3.8 / 1.05506,
    "electricity_usd_GJ": 0.08 * 277.7777778,
    "reaction_enthalpy_kJ_mol": 125.0,
    "Kp_873_bar": 0.35,
    "Tref_K": 873.15,
    "furnace_eff": 0.85,
    "heat_recovery": 0.65,
    "sep_elec_base_GJ_t": 0.25,
    "recycle_elec_coeff_GJ_t": 0.15,
    "fixed_other_usd_t": 45.0,
    "support_price_usd_kg": 25.0,
    "replacement_life_default_h": 16000.0,
    "regen_cost_fraction": 0.005,
}

METAL_PRICE = {
    "Pt": 38000.0, "Rh": 150000.0, "Ga": 400.0, "Zn": 3.0, "In": 300.0,
    "Sn": 35.0, "Cr": 12.0, "Fe": 1.0, "Mn": 2.5, "Zr": 8.0, "Al": 2.5,
    "Si": 2.0, "Mg": 3.0, "La": 8.0, "Y": 40.0, "Ti": 10.0, "Ce": 5.0,
    "Mo": 45.0, "P": 3.0,
}

R = 8.314462618e-3  # kJ/mol/K

def _num(x, default):
    try:
        if x is None:
            return default
        v = float(x)
        if not math.isfinite(v):
            return default
        return v
    except Exception:
        return default

def _components(rec):
    comps = rec.get("components", rec.get("elements", [])) if isinstance(rec, dict) else []
    if comps is None:
        return []
    out = []
    for c in comps:
        try:
            if isinstance(c, (list, tuple)) and len(c) >= 2:
                el, wt = c[0], c[1]
            elif isinstance(c, dict):
                el, wt = c.get("element"), c.get("wt%", c.get("wt_pct"))
            else:
                continue
            if el is None:
                continue
            wt = None if wt is None else float(wt)
            out.append((str(el), wt))
        except Exception:
            continue
    return out

def _catalyst_price(rec):
    price = PARAM["support_price_usd_kg"]
    known_wt = 0.0
    for el, wt in _components(rec):
        if wt is None or not math.isfinite(wt) or wt <= 0:
            continue
        known_wt += wt
        price += (wt / 100.0) * METAL_PRICE.get(el, 10.0) * 1.25
    # unreported promoted catalysts still have synthesis/forming costs, but do not invent hidden metal loadings.
    if known_wt <= 0:
        price *= 1.2
    return max(price, 5.0)

def _Kp(T):
    T = max(650.0, min(1000.0, float(T)))
    Kref = PARAM["Kp_873_bar"]
    dH = PARAM["reaction_enthalpy_kJ_mol"]
    return Kref * math.exp((-dH / R) * (1.0 / T - 1.0 / PARAM["Tref_K"]))

def _xeq(T, P_bar, y_key=1.0):
    # For C3H8 <-> C3H6 + H2 in an inert-diluted feed.  The simple pure-feed expression is
    # adjusted mildly for dilution because total pressure/hydrocarbon fugacity are lower.
    P = max(0.05, float(P_bar))
    y = max(0.05, min(1.0, float(y_key)))
    K = _Kp(T)
    x = math.sqrt(max(1e-12, K / (P * y + K)))
    return max(0.02, min(0.98, x))

def _drive_factor(x, T, P, y_key):
    xe = _xeq(T, P, y_key)
    z = max(0.0, min(0.98, x / max(xe, 1e-9)))
    return max(0.04, 1.0 - z)  # coke/heat-transfer tests should not make the model singular

def _activity_at_conversion(rec, x):
    r_lab = max(_num(rec.get("r"), 0.05), 1e-5)
    T = _num(rec.get("T_K"), 873.15)
    P = _num(rec.get("P_bar"), 1.2)
    y = _num(rec.get("y_key"), 0.5)
    Xlab = max(0.001, min(0.95, _num(rec.get("X"), 0.15)))
    # Convert a printed productivity at its lab approach to equilibrium to an apparent low-conversion activity,
    # then penalise the requested plant per-pass conversion by the mean approach-to-equilibrium driving force.
    lab_drive = _drive_factor(0.5 * Xlab, T, P, y)
    plant_drive = _drive_factor(0.5 * x, T, P, y)
    return max(1e-5, r_lab * plant_drive / max(lab_drive, 0.04))

def _selectivity(rec):
    S = _num(rec.get("S"), 0.90)
    if S > 1.0 and S <= 100.0:
        S /= 100.0
    return max(0.40, min(0.999, S))

def _cycle_h(rec):
    t = _num(rec.get("t_cycle_h"), PARAM["replacement_life_default_h"] / 20.0)
    # t_cycle_h means hours to lose 10% activity; very high extracted values mean nearly stable.
    return max(1.0, min(5000.0, t))

def _cost_for_x(rec, x):
    S = _selectivity(rec)
    T = _num(rec.get("T_K"), 873.15)
    P = _num(rec.get("P_bar"), 1.2)
    y = _num(rec.get("y_key"), 0.5)
    cap = PARAM["capacity_t_y"]
    hpy = PARAM["hours_y"]
    prod_kg_h = cap * 1000.0 / hpy
    MWp = REACTION["MW"][REACTION["product"]]
    MWk = REACTION["MW"][REACTION["key"]]

    key_feed_t_t = (MWk / MWp) / S
    feed_cost = key_feed_t_t * PARAM["propane_price_usd_t"]

    r_eff = _activity_at_conversion(rec, x)
    catalyst_inventory_kg = prod_kg_h / r_eff

    # Energy.  Reaction heat per tonne product plus sensible heat of total propane circulated.
    rxn_GJ_t = (PARAM["reaction_enthalpy_kJ_mol"] / (MWp / 1000.0)) / 1e6 * 1000.0
    # equivalently kJ/mol / kg/mol = kJ/kg; /1e6*1000 kg/t -> GJ/t
    rxn_GJ_t = PARAM["reaction_enthalpy_kJ_mol"] / (MWp / 1000.0) / 1e6 * 1000.0
    cp_propane_kJ_molK = 0.115
    circulated_mol_per_mol_prod = 1.0 / max(1e-6, S * x)
    sensible_GJ_t = (cp_propane_kJ_molK * max(0.0, T - 330.0) * circulated_mol_per_mol_prod) / (MWp / 1000.0) / 1e6 * 1000.0
    fired_GJ_t = (rxn_GJ_t + (1.0 - PARAM["heat_recovery"]) * sensible_GJ_t) / PARAM["furnace_eff"]
    elec_GJ_t = PARAM["sep_elec_base_GJ_t"] + PARAM["recycle_elec_coeff_GJ_t"] * max(0.0, (1.0 - x) / x)
    energy_cost = fired_GJ_t * PARAM["gas_price_usd_GJ"] + elec_GJ_t * PARAM["electricity_usd_GJ"]
    primary_energy_GJ_t = fired_GJ_t + elec_GJ_t / 0.38

    # Installed capital: public PDH analogue scaled by capacity, with adders for large recycle and bulky reactor.
    scale_capex = PARAM["base_capex_usd"] * (cap / PARAM["capex_ref_capacity_t_y"]) ** 0.65
    recycle_adder = 0.12 * max(0.0, 0.35 / max(x, 1e-6) - 1.0)
    reactor_adder = 0.08 * (max(catalyst_inventory_kg, 1.0) / 200000.0) ** 0.6
    capex = scale_capex * (1.0 + recycle_adder + reactor_adder)
    capital_cost = capex * PARAM["capital_charge_factor"] / cap

    cat_price = _catalyst_price(rec)
    cycle_h = _cycle_h(rec)
    replacement_life = PARAM["replacement_life_default_h"]
    cat_usd_per_h = catalyst_inventory_kg * cat_price * (1.0 / replacement_life + PARAM["regen_cost_fraction"] / cycle_h)
    catalyst_cost = cat_usd_per_h * hpy / cap

    other = PARAM["fixed_other_usd_t"] + 0.015 * capex / cap
    parts = {
        "feed": feed_cost,
        "energy": energy_cost,
        "capital": capital_cost,
        "catalyst": catalyst_cost,
        "other": other,
    }
    total = float(sum(parts.values()))
    return {
        "cost_usd_per_t": total,
        "parts": {k: float(v) for k, v in parts.items()},
        "operating": {"T_K": float(T), "P_bar": float(P), "per_pass_conversion": float(x)},
        "balances": {
            "key_feed_t_per_t": float(key_feed_t_t),
            "energy_GJ_per_t": float(primary_energy_GJ_t),
            "capex_usd": float(capex),
            "capacity_t_per_y": float(cap),
        },
    }

def plant_cost(rec):
    rec = dict(rec or {})
    T = _num(rec.get("T_K"), 873.15)
    P = _num(rec.get("P_bar"), 1.2)
    y = _num(rec.get("y_key"), 0.5)
    xe = _xeq(T, P, y)
    xmax = max(0.03, min(0.90, 0.92 * xe))
    xmin = min(0.05, xmax)
    grid = np.linspace(xmin, xmax, 80)
    best = None
    for x in grid:
        c = _cost_for_x(rec, float(x))
        if best is None or c["cost_usd_per_t"] < best["cost_usd_per_t"]:
            best = c
    return best

def reference():
    rec = {
        "T_K": 873.15,
        "P_bar": 1.5,
        "X": 0.36,
        "S": 0.91,
        "r": 1.2,
        "y_key": 0.7,
        "y_cofeed": 0.0,
        "t_cycle_h": 720.0,
        "components": [["Pt", 0.3], ["Sn", 0.6]],
        "catalyst": "commercial Pt-Sn/Al2O3 PDH analogue",
    }
    ans = plant_cost(rec)
    ans["name"] = "600 kt/y Gulf Coast PDH reference"
    ans["record"] = rec
    return ans
