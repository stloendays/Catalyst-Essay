import math
import numpy as np

REACTION = {
    "key": "C3H8",
    "product": "C3H6",
    "cofeed": None,
    "MW": {"C3H8": 44.096, "C3H6": 42.080, "H2": 2.016},
}

P = {
    "capacity_tpy": 600000.0,
    "hours_y": 8000.0,
    "propane_price": 520.0,
    "ng_price_GJ": 5.0,
    "elec_price_MWh": 70.0,
    "base_capex": 720e6,
    "crf": 0.12,
    "fixed_opex_frac": 0.035,
    "dH_kJ_mol": 124.3,
    "K_ref": 0.42,
    "T_ref": 873.15,
    "dH_eq_J_mol": 124300.0,
    "R": 8.314462618,
    "base_X": 0.42,
    "base_S": 0.95,
    "heat_recovery": 0.65,
    "furnace_eff": 0.85,
    "elec_primary_eff": 0.38,
    "base_sep_heat": 0.9,
    "base_elec_kWh": 80.0,
    "recycle_heat_coeff": 0.08,
    "recycle_elec_coeff": 25.0,
    "support_price": 25.0,
    "makeup_life_h": 24000.0,
    "regen_cost": 0.8,
    "default_cycle_h": 720.0,
    "inventory_install": 320.0,
    "other_variable": 20.0,
}

METAL_PRICE = {
    "Pt": 35000.0, "Rh": 150000.0, "Ga": 500.0, "Sn": 35.0, "Zn": 4.0,
    "Cr": 12.0, "Co": 35.0, "Mn": 3.0, "In": 250.0, "Fe": 1.0,
    "K": 20.0, "Al": 3.0, "Si": 3.0, "Zr": 35.0, "O": 0.0, "P": 5.0,
    "Cu": 10.0, "Ni": 20.0, "Mo": 45.0, "V": 25.0, "Ce": 8.0,
}

def _float(x, default):
    try:
        if x is None: return default
        y = float(x)
        if not math.isfinite(y): return default
        return y
    except Exception:
        return default

def _clip(v, lo, hi):
    return max(lo, min(hi, v))

def _Kp(T):
    T = _clip(_float(T, P["T_ref"]), 650.0, 1100.0)
    return P["K_ref"] * math.exp((-P["dH_eq_J_mol"] / P["R"]) * (1.0 / T - 1.0 / P["T_ref"]))

def _Q_over_K(x, T, Pbar=1.0, y0=1.0):
    x = _clip(x, 1e-9, 0.999999)
    y0 = _clip(y0, 1e-4, 1.0)
    Pbar = _clip(_float(Pbar, 1.0), 0.05, 10.0)
    # basis: initial total mol = 1, propane = y0, inert = 1-y0
    Q = Pbar * y0 * x * x / max((1.0 - x) * (1.0 + y0 * x), 1e-12)
    return Q / max(_Kp(T), 1e-12)

def _xeq(T, Pbar=1.0, y0=1.0):
    # monotone bisection for Q/K = 1
    lo, hi = 1e-8, 0.999999
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _Q_over_K(mid, T, Pbar, y0) < 1.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

def _tau_integral(x, T, Pbar=1.0, y0=1.0):
    x = _clip(x, 1e-6, 0.98 * _xeq(T, Pbar, y0))
    n = 160
    xs = np.linspace(0.0, x, n + 1)
    app = np.array([max(1.0 - _Q_over_K(float(z), T, Pbar, y0), 0.015) for z in xs])
    vals = 1.0 / app
    return float(np.trapz(vals, xs))

def _components(rec):
    comps = rec.get("components", rec.get("elements", [])) if isinstance(rec, dict) else []
    if isinstance(comps, str):
        try:
            import ast
            comps = ast.literal_eval(comps)
        except Exception:
            comps = []
    out = []
    if isinstance(comps, (list, tuple)):
        for c in comps:
            try:
                el = str(c[0])
                wt = c[1]
                wt = None if wt is None else float(wt)
                out.append((el, wt))
            except Exception:
                pass
    return out

def _catalyst_price(rec):
    price = P["support_price"]
    used_wt = 0.0
    saw_pt_name = False
    name = str(rec.get("catalyst", "")) if isinstance(rec, dict) else ""
    comps = _components(rec)
    for el, wt in comps:
        if wt is None:
            # common literature shorthand: 1000 ppm Pt = 0.1 wt%; use a tiny default only if Pt is named.
            if el == "Pt" and ("ppm Pt" in name or "Pt" in name):
                wt = 0.10
                saw_pt_name = True
            else:
                continue
        wt = _clip(wt, 0.0, 100.0)
        used_wt += wt
        price += (wt / 100.0) * METAL_PRICE.get(el, 20.0)
    if (not saw_pt_name) and "Pt" in name and all(el != "Pt" for el, _ in comps):
        price += 0.001 * METAL_PRICE["Pt"]
    # manufacturing/attrition contingency; bounded so metal perturbations remain visible but not dominant.
    return _clip(price * 1.25, 10.0, 20000.0)

def _effective_rate(rec, xplant, T, Pbar):
    r = max(_float(rec.get("r", None), 0.05), 1e-4)
    Xlab = _clip(_float(rec.get("X", None), 0.20), 0.005, 0.95)
    ylab = _clip(_float(rec.get("y_key", None), 1.0), 0.02, 1.0)
    Plab = _clip(_float(rec.get("P_bar", None), 1.0), 0.05, 10.0)
    Tlab = _clip(_float(rec.get("T_K", None), T), 650.0, 1100.0)
    # if the reported point is beyond the simple thermodynamic cap due to strong dilution, calibrate at the cap.
    Xlab_eff = min(Xlab, 0.96 * _xeq(Tlab, Plab, ylab))
    Xlab_eff = max(Xlab_eff, 0.003)
    Ilab = _tau_integral(Xlab_eff, Tlab, Plab, ylab)
    Ipl = _tau_integral(xplant, T, Pbar, 1.0)
    # Arrhenius correction only for modest deviations from extracted T (apparent Ea 80 kJ/mol); normally zero because plant uses record T.
    Ea = 80000.0
    arr = math.exp((-Ea / P["R"]) * (1.0 / T - 1.0 / Tlab))
    eff = r * (xplant / max(Ipl, 1e-12)) / (Xlab_eff / max(Ilab, 1e-12)) * arr
    return max(eff, 1e-5)

def _plant_given_x(rec, x):
    T = _clip(_float(rec.get("T_K", None), 873.15), 720.0, 1050.0)
    # Industrial PDH is run at low pressure; use extracted pressure if low, otherwise cap the reactor pressure.
    Pbar = _clip(_float(rec.get("P_bar", None), 1.5), 0.5, 3.0)
    S = _clip(_float(rec.get("S", None), 0.85), 0.20, 0.999)
    r_eff = _effective_rate(rec, x, T, Pbar)

    MWk = REACTION["MW"]["C3H8"]
    MWp = REACTION["MW"]["C3H6"]
    key_feed = (MWk / MWp) / S
    feed_cost = key_feed * P["propane_price"]

    # Heat: reaction enthalpy per tonne propylene plus unrecovered sensible and recycle/separation heat.
    q_rxn = P["dH_kJ_mol"] / MWp  # GJ/t, because kJ/mol divided by kg/kmol
    mol_key_kmol_t = key_feed * 1000.0 / MWk
    cp_GJ_per_kmol_K = 0.000105  # ~105 kJ/kmol/K for hot propane-rich gas
    sensible = mol_key_kmol_t * cp_GJ_per_kmol_K * max(T - 298.15, 0.0) * (1.0 - P["heat_recovery"])
    recycle_factor = max(1.0 / max(x, 1e-6) - 1.0 / P["base_X"], 0.0)
    sep_heat = P["base_sep_heat"] + P["recycle_heat_coeff"] * recycle_factor
    process_heat = q_rxn + sensible + sep_heat
    fuel_GJ = process_heat / P["furnace_eff"]
    elec_kWh = P["base_elec_kWh"] + P["recycle_elec_coeff"] * recycle_factor
    energy_cost = fuel_GJ * P["ng_price_GJ"] + (elec_kWh / 1000.0) * P["elec_price_MWh"]
    primary_energy = fuel_GJ + elec_kWh * 0.0036 / P["elec_primary_eff"]

    # Catalyst inventory sized by annual average productivity.
    cap = P["capacity_tpy"]
    kgprod_h = cap * 1000.0 / P["hours_y"]
    cat_mass = kgprod_h / r_eff
    cat_price = _catalyst_price(rec)
    cycle = rec.get("t_cycle_h", None)
    if cycle is None or _float(cycle, 0.0) <= 0.0:
        cycle_h = P["default_cycle_h"]
    else:
        cycle_h = _clip(_float(cycle, P["default_cycle_h"]), 1.0, 10000.0)
    cat_repl = cat_price * 1000.0 / (r_eff * P["makeup_life_h"])
    cat_regen = P["regen_cost"] * 1000.0 / (r_eff * cycle_h)
    catalyst_cost = cat_repl + cat_regen

    # Installed capital: main recovery section scales with feed/recycle flow, reactor increment with catalyst inventory.
    flow_norm = (key_feed / ((REACTION["MW"]["C3H8"] / REACTION["MW"]["C3H6"]) / P["base_S"])) * (P["base_X"] / max(x, 1e-6))
    flow_norm = _clip(flow_norm, 0.25, 8.0)
    main_capex = P["base_capex"] * (cap / P["capacity_tpy"]) ** 0.65 * flow_norm ** 0.45
    reactor_capex = P["inventory_install"] * cat_mass
    capex = main_capex + reactor_capex
    capital_cost = capex * (P["crf"] + P["fixed_opex_frac"]) / cap

    other = P["other_variable"]
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
        "operating": {"T_K": float(T), "P_bar": float(Pbar), "per_pass_conversion": float(x)},
        "balances": {
            "key_feed_t_per_t": float(key_feed),
            "energy_GJ_per_t": float(primary_energy),
            "capex_usd": float(capex),
            "capacity_t_per_y": float(cap),
        },
    }

def plant_cost(rec):
    if rec is None:
        rec = {}
    T = _clip(_float(rec.get("T_K", None), 873.15), 720.0, 1050.0)
    Pbar = _clip(_float(rec.get("P_bar", None), 1.5), 0.5, 3.0)
    xmax = 0.94 * _xeq(T, Pbar, 1.0)
    xmax = _clip(xmax, 0.03, 0.86)
    xmin = min(0.05, 0.6 * xmax)
    # Include the reported lab conversion if feasible, but optimize economics over the recycle/equilibrium tradeoff.
    grid = np.unique(np.concatenate([
        np.linspace(xmin, xmax, 80),
        np.array([_clip(_float(rec.get("X", None), 0.25), xmin, xmax), P["base_X"]])
    ]))
    best = None
    for x in grid:
        if x < xmin - 1e-12 or x > xmax + 1e-12:
            continue
        out = _plant_given_x(rec, float(x))
        if best is None or out["cost_usd_per_t"] < best["cost_usd_per_t"]:
            best = out
    return best

def reference():
    rec = {
        "T_K": 873.15,
        "P_bar": 1.5,
        "X": 0.42,
        "S": 0.95,
        "r": 2.5,
        "y_key": 1.0,
        "y_cofeed": 0.0,
        "t_cycle_h": 720.0,
        "components": [["Pt", 0.3], ["Sn", 1.0], ["Al", None]],
        "catalyst": "industrial Pt-Sn/Al2O3 Oleflex-like reference catalyst",
    }
    d = plant_cost(rec)
    d["name"] = "600 kt/y low-pressure propane dehydrogenation reference plant"
    d["record"] = rec
    return d
