import math, ast
import numpy as np

REACTION = {
    "key": "CO2",
    "product": "CH4",
    "cofeed": "H2",
    "MW": {"CO2": 44.0095, "H2": 2.01588, "CH4": 16.0425, "H2O": 18.01528, "CO": 28.0101},
    "nu": {"CO2": -1.0, "H2": -4.0, "CH4": 1.0, "H2O": 2.0},
}

PARAM = {
    "capacity_tpy": 50000.0, "stream_factor": 0.90, "crf": 0.10,
    "h2_price_usd_per_kg": 2.0, "co2_price_usd_per_t": 50.0,
    "electricity_price_usd_per_kwh": 0.0938, "fuel_price_usd_per_GJ": 6.0,
    "primary_factor_electricity": 3.0, "feed_pressure_bar": 1.0,
    "default_P_bar": 20.0, "max_P_bar": 30.0, "product_P_bar": 30.0,
    "compressor_eff": 0.72, "purge_fraction": 0.02,
    "hx_effectiveness": 0.70, "min_x": 0.03, "max_x": 0.90, "approach_margin": 0.98,
    "support_price": 20.0, "cat_life_default_y": 2.0, "cat_install_factor": 1.5,
    "dh_meth_GJ_per_kmol": -0.180, "dh_rwgs_GJ_per_kmol": 0.0,
    "cooling_energy_fraction": 0.01, "sep_energy_GJ_per_t": 0.15,
    "other_om_frac": 0.04, "ref_cap_tpy": 50000.0, "scale_exp": 0.65,
    "offsites_frac": 0.25,
}

METAL_PRICE = {
    "Ni": 17.26, "Co": 35.0, "Fe": 1.0, "Mg": 4.0, "Ru": 61093.0,
    "Rh": 299000.0, "Pt": 49961.0, "Pd": 33661.0, "Ce": 8.0, "Zr": 40.0,
    "Al": 3.0, "Si": 2.0, "Mn": 3.0, "Cu": 10.0, "Zn": 4.0, "Y": 35.0,
    "V": 25.0, "La": 8.0, "Ca": 2.0, "K": 2.0, "Na": 1.0, "C": 1.0, "O": 0.0,
}

UNIT_NAMES = [
    "CO2 feed compressor", "H2 feed compressor", "feed mixer", "feed effluent heat exchanger",
    "trim heater", "cooled methanation reactor", "effluent cooler and water knockout",
    "methane purification membrane", "product compressor", "recycle compressor", "offsites and utilities"
]

def _num(v, default):
    try:
        if v is None: return default
        x = float(v)
        if not math.isfinite(x): return default
        return x
    except Exception:
        return default

def _components(rec):
    comps = rec.get("components", rec.get("elements", []))
    if isinstance(comps, str):
        try: comps = ast.literal_eval(comps)
        except Exception: comps = []
    out = []
    for c in comps or []:
        try:
            el, wt = c[0], c[1]
            out.append((str(el), None if wt is None else float(wt)))
        except Exception:
            pass
    return out

def _catalyst_price(rec):
    price = PARAM["support_price"]
    for el, wt in _components(rec):
        p = METAL_PRICE.get(el, 5.0)
        if wt is None:
            if el in ("Ru", "Rh", "Pt", "Pd"):
                wt = 1.0
            elif el in ("Ni", "Co", "Fe"):
                wt = 15.0
            else:
                wt = 5.0
        if wt > 1.0:
            frac = max(0.0, min(wt/100.0, 0.9))
        else:
            frac = max(0.0, min(wt, 0.9))
        price += frac * p
    return max(price, PARAM["support_price"])

def _eq_cap(T, P):
    T = max(450.0, min(900.0, T))
    P = max(1.0, min(60.0, P))
    cap = 0.92 - 0.00105*(T-550.0) + 0.045*math.log(P/10.0)
    return max(0.08, min(0.95, cap))

def _compress_power(kmol, T, Pin, Pout):
    if kmol <= 0 or Pout <= Pin: return 0.0
    return kmol * 8.314e-6 * T * math.log(Pout/Pin) / PARAM["compressor_eff"]

def _molfrac(d):
    s = sum(max(0.0, v) for v in d.values())
    if s <= 0: return {k: 0.0 for k in d}
    return {k: max(0.0, v)/s for k, v in d.items() if max(0.0, v) > 1e-14}

def _stream(kmol_dict):
    return {"kmol_per_t": float(sum(kmol_dict.values())), "mol_frac": _molfrac(kmol_dict)}

def _case(rec, x):
    MW = REACTION["MW"]
    n_ch4 = 1000.0 / MW["CH4"]  # kmol per tonne methane
    S = max(0.02, min(1.0, _num(rec.get("S"), 0.98)))
    r = max(1e-5, _num(rec.get("r"), 0.05))
    T = max(450.0, min(900.0, _num(rec.get("T_K"), 623.15)))
    P_lab = _num(rec.get("P_bar"), PARAM["default_P_bar"])
    P = max(P_lab, PARAM["default_P_bar"])
    P = min(P, PARAM["max_P_bar"])
    p = PARAM["purge_fraction"]

    n_co2_conv = n_ch4 / S
    n_co_side = max(0.0, n_co2_conv - n_ch4)
    F_co2_reactor = n_co2_conv / max(x, 1e-6)
    F_h2_reactor = 4.0 * F_co2_reactor
    un_co2 = max(0.0, F_co2_reactor - n_co2_conv)
    h2_cons = 4.0*n_ch4 + n_co_side
    un_h2 = max(0.0, F_h2_reactor - h2_cons)
    fresh_co2 = n_co2_conv + p*un_co2
    fresh_h2 = h2_cons + p*un_h2
    water = 2.0*n_ch4 + n_co_side

    # recycle/separation dry gas accounting
    dry_feed = {"CH4": n_ch4, "CO": n_co_side, "CO2": un_co2, "H2": un_h2}
    recycle = {"CO2": (1.0-p)*un_co2, "H2": (1.0-p)*un_h2}
    purge = {"CO2": p*un_co2, "H2": p*un_h2, "CO": n_co_side}
    product = {"CH4": n_ch4}

    co2_t = fresh_co2*MW["CO2"]/1000.0
    h2_t = fresh_h2*MW["H2"]/1000.0
    h2_cost = h2_t*1000.0*PARAM["h2_price_usd_per_kg"]
    co2_cost = co2_t*PARAM["co2_price_usd_per_t"]
    feed_cost = h2_cost + co2_cost

    # Compression duties per tonne product.
    co2_comp = _compress_power(fresh_co2, 298.15, PARAM["feed_pressure_bar"], P)
    h2_comp = _compress_power(fresh_h2, 298.15, PARAM["feed_pressure_bar"], P)
    rec_in_P = max(1.0, P*(1.0-0.10))
    rec_comp = _compress_power(sum(recycle.values()), 313.15, rec_in_P, P)
    prod_comp = _compress_power(n_ch4, 313.15, max(1.0, P*(1.0-0.10)), PARAM["product_P_bar"])

    q_reaction = PARAM["dh_meth_GJ_per_kmol"]*n_ch4
    heat_removed = max(0.0, -q_reaction)
    sensible_need = max(0.0, 0.000035*(T-298.15)*(F_co2_reactor+F_h2_reactor))
    recovered = PARAM["hx_effectiveness"]*min(heat_removed, sensible_need)
    trim_heat = max(0.0, sensible_need - recovered)
    cooling_aux_e = heat_removed*PARAM["cooling_energy_fraction"]
    sep_e = max(PARAM["sep_energy_GJ_per_t"]*(1.0 + 0.15*max(0.0, (1.0-S))/max(S,1e-6) + 0.01/max(x,1e-6)), 0.012*sum(dry_feed.values()))

    electricity_GJ = co2_comp + h2_comp + rec_comp + prod_comp + cooling_aux_e + sep_e
    purchased_primary = electricity_GJ*PARAM["primary_factor_electricity"] + trim_heat
    energy_cost = electricity_GJ/0.0036*PARAM["electricity_price_usd_per_kwh"] + trim_heat*PARAM["fuel_price_usd_per_GJ"]

    xeq = _eq_cap(T, P)
    approach = max(1.0, 1.0/(1.0 - min(0.97, x/max(xeq,1e-6))))
    prod_kg_h = PARAM["capacity_tpy"]*1000.0/(8760.0*PARAM["stream_factor"])
    cat_mass = prod_kg_h/r * approach
    tcy = rec.get("t_cycle_h", None)
    tcy = _num(tcy, float("nan"))
    if math.isfinite(tcy) and tcy > 0:
        life_y = max(0.05, min(PARAM["cat_life_default_y"], 5.0*tcy/8760.0))
    else:
        life_y = PARAM["cat_life_default_y"]
    cat_price = _catalyst_price(rec)
    cat_cost = cat_mass*cat_price*PARAM["cat_install_factor"]/(life_y*PARAM["capacity_tpy"])

    scale = (PARAM["capacity_tpy"]/PARAM["ref_cap_tpy"])**PARAM["scale_exp"]
    rec_severity = (F_co2_reactor + F_h2_reactor)/(n_ch4*5.0)
    comp_cap = 3000000.0*scale*(0.5 + 0.5*(co2_comp+h2_comp+rec_comp+prod_comp)/0.55)
    sep_cap = 8000000.0*scale*(0.7 + 0.3*rec_severity)
    hx_cap = 4000000.0*scale*(0.6 + 0.4*(heat_removed+sensible_need)/12.0)
    react_cap = 12000000.0*scale*(0.5 + 0.5*(cat_mass/60000.0)**0.35)
    off_cap = PARAM["offsites_frac"]*(comp_cap+sep_cap+hx_cap+react_cap)
    capex = comp_cap+sep_cap+hx_cap+react_cap+off_cap
    capital_cost = PARAM["crf"]*capex/PARAM["capacity_tpy"]
    other_cost = PARAM["other_om_frac"]*capex/PARAM["capacity_tpy"]

    units = []
    def u(name, typ, pe, cap, extra=None):
        d = {"name": name, "type": typ, "purchased_energy_GJ_per_t": float(max(0.0, pe)), "internal_fuel_GJ_per_t": 0.0, "capex_usd": float(max(0.0, cap))}
        if extra: d.update(extra)
        units.append(d)
    u("CO2 feed compressor", "compressor", co2_comp*PARAM["primary_factor_electricity"], 0.28*comp_cap, {"kmol_per_t": fresh_co2, "T_in_K": 298.15, "P_in_bar": PARAM["feed_pressure_bar"], "P_out_bar": P, "power_GJ_per_t": co2_comp})
    u("H2 feed compressor", "compressor", h2_comp*PARAM["primary_factor_electricity"], 0.32*comp_cap, {"kmol_per_t": fresh_h2, "T_in_K": 298.15, "P_in_bar": PARAM["feed_pressure_bar"], "P_out_bar": P, "power_GJ_per_t": h2_comp})
    u("feed mixer", "other", 0.0, 0.02*sep_cap)
    u("feed effluent heat exchanger", "heat_exchanger", 0.0, 0.70*hx_cap, {"recovered_heat_GJ_per_t": recovered})
    u("trim heater", "furnace", trim_heat, 0.15*hx_cap)
    u("cooled methanation reactor", "reactor", 0.0, react_cap, {"heat_duty_GJ_per_t": q_reaction, "catalyst_inventory_kg": cat_mass})
    u("effluent cooler and water knockout", "knockout", cooling_aux_e*PARAM["primary_factor_electricity"], 0.15*hx_cap, {"cooling_duty_GJ_per_t": heat_removed})
    u("methane purification membrane", "separation", sep_e*PARAM["primary_factor_electricity"], 0.98*sep_cap, {"feed": _stream(dry_feed), "outlets": [_stream(product), _stream(recycle), _stream(purge)], "recovered_heat_GJ_per_t": 0.0})
    u("product compressor", "compressor", prod_comp*PARAM["primary_factor_electricity"], 0.18*comp_cap, {"kmol_per_t": n_ch4, "T_in_K": 313.15, "P_in_bar": max(1.0, P*(1.0-0.10)), "P_out_bar": PARAM["product_P_bar"], "power_GJ_per_t": prod_comp})
    u("recycle compressor", "compressor", rec_comp*PARAM["primary_factor_electricity"], 0.22*comp_cap, {"kmol_per_t": sum(recycle.values()), "T_in_K": 313.15, "P_in_bar": rec_in_P, "P_out_bar": P, "power_GJ_per_t": rec_comp})
    u("offsites and utilities", "offsites", 0.0, off_cap)

    parts = {"feed": feed_cost, "energy": energy_cost, "capital": capital_cost, "catalyst": cat_cost, "other": other_cost}
    total = sum(parts.values())
    in_t = {"CO2": co2_t, "H2": h2_t}
    out_t = {"CH4": 1.0, "H2O": water*MW["H2O"]/1000.0}
    if purge["CO2"] > 1e-12: out_t["CO2"] = purge["CO2"]*MW["CO2"]/1000.0
    if purge["H2"] > 1e-12: out_t["H2"] = purge["H2"]*MW["H2"]/1000.0
    if purge["CO"] > 1e-12: out_t["CO"] = purge["CO"]*MW["CO"]/1000.0
    return {
        "cost_usd_per_t": float(total),
        "parts": {k: float(v) for k,v in parts.items()},
        "operating": {"T_K": float(T), "P_bar": float(P), "per_pass_conversion": float(x)},
        "balances": {"key_feed_t_per_t": float(co2_t), "energy_GJ_per_t": float(purchased_primary), "capex_usd": float(capex), "capacity_t_per_y": PARAM["capacity_tpy"]},
        "physics": {
            "reactor": {"T_K": float(T), "P_bar": float(P), "feed_mol_frac": {"CO2": 0.2, "H2": 0.8}, "per_pass_conversion": float(x), "heat_duty_GJ_per_t": float(q_reaction)},
            "boundary": {"in_t_per_t": in_t, "out_t_per_t": out_t},
            "units": units,
        }
    }

def plant_cost(rec):
    T = max(450.0, min(900.0, _num(rec.get("T_K"), 623.15)))
    P_lab = _num(rec.get("P_bar"), PARAM["default_P_bar"])
    P = min(max(P_lab, PARAM["default_P_bar"]), PARAM["max_P_bar"])
    labX = max(0.0, min(1.0, _num(rec.get("X"), 0.5)))
    xcap = min(PARAM["max_x"], labX if labX > 0 else 0.5, PARAM["approach_margin"]*_eq_cap(T, P))
    if xcap < PARAM["min_x"]:
        xcap = max(0.005, xcap)
    lo = min(PARAM["min_x"], xcap)
    grid = np.linspace(lo, xcap, 30) if xcap > lo else np.array([xcap])
    best = None
    for x in grid:
        res = _case(rec, float(max(1e-4, x)))
        if best is None or res["cost_usd_per_t"] < best["cost_usd_per_t"]:
            best = res
    return best

def reference():
    rec = {"T_K": 623.15, "P_bar": 20.0, "X": 0.75, "S": 0.995, "r": 1.0,
           "y_key": 0.2, "y_cofeed": 0.8, "t_cycle_h": None,
           "components": [["Ni", 20.0], ["Al", None]], "catalyst": "reference 20 wt% Ni/Al2O3"}
    out = plant_cost(rec)
    out["name"] = "50 kt/y CO2 methanation reference plant with 20 wt% Ni/Al2O3"
    out["record"] = rec
    return out
