import math
import numpy as np
from scipy.optimize import minimize_scalar

REACTION = {
    "key": "C3H8",
    "product": "C3H6",
    "cofeed": None,
    "MW": {"C3H8": 44.0956, "C3H6": 42.0797, "H2": 2.01588},
}

# Economic/plant constants. Each value is recorded in sources.csv.
CAPACITY_TPY = 750_000.0
HOURS_Y = 8000.0
PROPANE_USD_PER_GAL = 0.750
PROPANE_LB_PER_GAL = 4.24
PROPANE_USD_PER_T = PROPANE_USD_PER_GAL / (PROPANE_LB_PER_GAL * 0.45359237 / 1000.0)
GAS_USD_PER_MMBTU = 3.5
GAS_USD_PER_GJ = GAS_USD_PER_MMBTU / 1.055056
ELEC_USD_PER_KWH = 0.096
DH_KJ_PER_MOL = 124.3
KREF_T = 873.15
KREF = 0.50
DH_EQ_J_PER_MOL = 124300.0
R = 8.314462618
REF_CAPEX = 1.20e9
CRF = 0.12
FIXED_OM_FRAC = 0.04
FURNACE_EFF = 0.85
HEAT_RECOVERY = 0.75
CP_PROPANE_KJ_KG_K = 2.3
SEP_BASE_KWH = 60.0
RECYCLE_KWH_COEFF = 12.0
SUPPORT_COST = 20.0
CAT_LIFE_Y = 3.0
REGEN_COEFF_H = 4.0
REF_ACTIVITY = 2.0  # kg C3H6 kg-cat-1 h-1 at reference severity
REF_X = 0.35

METAL_PRICE = {
    "Pt": 33000.0, "Ru": 16000.0, "Rh": 140000.0, "Ga": 500.0, "In": 250.0,
    "Co": 35.0, "Cu": 10.0, "Zn": 3.0, "Sn": 30.0, "Fe": 1.0, "Cr": 10.0,
    "Al": 3.0, "P": 3.0, "B": 20.0, "K": 5.0, "Na": 3.0, "Mg": 4.0,
    "Ca": 3.0, "Si": 2.0, "O": 0.0,
}


def _num(rec, key, default):
    v = rec.get(key, default) if isinstance(rec, dict) else default
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return default
        return float(v)
    except Exception:
        return default


def _components(rec):
    comps = rec.get("components", rec.get("elements", [])) if isinstance(rec, dict) else []
    if comps is None:
        return []
    if isinstance(comps, str):
        # very small safe parser for JSON-like strings from csv readers
        try:
            import ast
            comps = ast.literal_eval(comps)
        except Exception:
            return []
    out = []
    for c in comps:
        try:
            el, wt = c[0], c[1]
            if wt is None:
                continue
            wt = float(wt)
            if wt > 0:
                out.append((str(el), wt))
        except Exception:
            continue
    return out


def _kp(T):
    T = max(650.0, min(1000.0, float(T)))
    return KREF * math.exp(-DH_EQ_J_PER_MOL / R * (1.0 / T - 1.0 / KREF_T))


def _xeq(T, P_bar=1.0, y_key=1.0, y_h2=0.0):
    """Equilibrium conversion for C3H8 -> C3H6+H2 with inert/H2 in feed.
    Basis n_C3H8,0=1. Kp = y_C3H6*y_H2/y_C3H8 * P_bar.
    """
    K = max(_kp(T), 1e-12)
    P = max(0.05, float(P_bar))
    yk = max(1e-6, min(1.0, float(y_key)))
    yh = max(0.0, min(0.95, float(y_h2)))
    inert = max(0.0, (1.0 - yk - yh) / yk)
    h0 = max(0.0, yh / yk)
    def f(x):
        nt = 1.0 + inert + h0 + x
        return (x * (h0 + x) / max(1e-12, (1.0 - x) * nt)) * P - K
    lo, hi = 0.0, 0.999
    if f(hi) < 0:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return max(1e-4, min(0.999, 0.5 * (lo + hi)))


def _tau_shape(x, xeq):
    z = max(1e-9, min(0.985, x / max(1e-9, xeq)))
    return -math.log(1.0 - z)


def _r_eff_at_x(rec, x, T, P):
    r = max(1e-6, _num(rec, "r", 0.05))
    Xlab = max(1e-4, min(0.95, _num(rec, "X", x)))
    ylab = _num(rec, "y_key", 1.0)
    yh2 = _num(rec, "y_h2", _num(rec, "y_cofeed", 0.0))
    xeq_lab = _xeq(_num(rec, "T_K", T), _num(rec, "P_bar", P), ylab, yh2)
    xlab_eff = min(Xlab, 0.92 * xeq_lab)
    xeq_p = _xeq(T, P, 1.0, 0.0)
    x_eff = min(x, 0.92 * xeq_p)
    lab_prod_per_tau = max(1e-9, xlab_eff / _tau_shape(xlab_eff, xeq_lab))
    plant_prod_per_tau = max(1e-9, x_eff / _tau_shape(x_eff, xeq_p))
    # Temperature transfer is intentionally weak: use reported activity at its own T; only penalize plant if clipped.
    return max(1e-5, r * plant_prod_per_tau / lab_prod_per_tau)


def _catalyst_price_usd_per_kg(rec):
    price = SUPPORT_COST
    for el, wt in _components(rec):
        price += (wt / 100.0) * METAL_PRICE.get(el, 50.0) * 1.25
    return max(5.0, price)


def _cost_at_x(rec, x):
    T = max(700.0, min(980.0, _num(rec, "T_K", 873.15)))
    P = max(0.5, min(3.0, _num(rec, "P_bar", 1.5)))
    S = max(0.30, min(1.0, _num(rec, "S", 0.90)))
    xeq_p = _xeq(T, P, 1.0, 0.0)
    if x <= 0.0 or x >= 0.93 * xeq_p:
        return 1e12, None
    r_eff = _r_eff_at_x(rec, x, T, P)

    mw_ratio = REACTION["MW"]["C3H8"] / REACTION["MW"]["C3H6"]
    key_feed_t = mw_ratio / S
    feed_cost = key_feed_t * PROPANE_USD_PER_T

    # Heat of reaction per tonne propylene: mol propylene per tonne * dH, scaled by selectivity.
    rxn_gj = (DH_KJ_PER_MOL / REACTION["MW"]["C3H6"]) / S  # GJ/t because kJ/mol divided kg/kmol
    circ_propane_t = mw_ratio / (S * max(0.01, x))
    sensible_gj = circ_propane_t * CP_PROPANE_KJ_KG_K * max(0.0, T - 320.0) / 1000.0 * (1.0 - HEAT_RECOVERY)
    fuel_gj = (rxn_gj + sensible_gj) / FURNACE_EFF
    sep_kwh = SEP_BASE_KWH + RECYCLE_KWH_COEFF * max(0.0, 1.0 / x - 1.0)
    energy_cost = fuel_gj * GAS_USD_PER_GJ + sep_kwh * ELEC_USD_PER_KWH
    primary_energy_gj = fuel_gj + sep_kwh * 0.0036 / 0.38

    # Capital: most cost is separations/heaters; recycle and reactor/catalyst productivity perturb it.
    recycle_factor = (REF_X / x) ** 0.40
    activity_factor = math.sqrt(max(0.05, REF_ACTIVITY) / max(0.02, r_eff))
    temp_factor = 1.0 + 0.0015 * max(0.0, T - 873.15)
    capex = REF_CAPEX * (0.65 + 0.25 * recycle_factor + 0.10 * activity_factor) * temp_factor
    annual_capital = capex * CRF / CAPACITY_TPY
    fixed_om = capex * FIXED_OM_FRAC / CAPACITY_TPY

    prod_kg_h = CAPACITY_TPY * 1000.0 / HOURS_Y
    tcy = _num(rec, "t_cycle_h", 24.0)
    if tcy <= 0:
        tcy = 24.0
    swing = 1.0 + REGEN_COEFF_H / max(1.0, tcy)
    cat_inventory_kg = prod_kg_h / max(1e-5, r_eff) * swing
    cat_price = _catalyst_price_usd_per_kg(rec)
    catalyst_cost = cat_inventory_kg * cat_price / CAT_LIFE_Y / CAPACITY_TPY

    other = fixed_om
    cost = feed_cost + energy_cost + annual_capital + catalyst_cost + other
    parts = {"feed": feed_cost, "energy": energy_cost, "capital": annual_capital, "catalyst": catalyst_cost, "other": other}
    out = {
        "cost_usd_per_t": cost,
        "parts": parts,
        "operating": {"T_K": T, "P_bar": P, "per_pass_conversion": x},
        "balances": {
            "key_feed_t_per_t": key_feed_t,
            "energy_GJ_per_t": primary_energy_gj,
            "capex_usd": capex,
            "capacity_t_per_y": CAPACITY_TPY,
            "r_eff_kg_per_kg_h": r_eff,
            "equilibrium_conversion": xeq_p,
        },
    }
    return cost, out


def plant_cost(rec):
    T = max(700.0, min(980.0, _num(rec, "T_K", 873.15)))
    P = max(0.5, min(3.0, _num(rec, "P_bar", 1.5)))
    xeq_p = _xeq(T, P, 1.0, 0.0)
    lo = max(0.015, min(0.08, 0.15 * xeq_p))
    hi = max(lo * 1.2, min(0.55, 0.88 * xeq_p))
    def obj(xx):
        return _cost_at_x(rec, xx)[0]
    res = minimize_scalar(obj, bounds=(lo, hi), method="bounded", options={"xatol": 1e-5})
    candidates = [lo, hi, float(res.x)]
    best = None
    for xx in candidates:
        c, o = _cost_at_x(rec, xx)
        if o is not None and (best is None or c < best[0]):
            best = (c, o)
    if best is None:
        _, out = _cost_at_x(rec, lo)
        return out
    # remove tiny numerical part mismatch
    out = best[1]
    s = sum(out["parts"].values())
    out["cost_usd_per_t"] = s
    return out


def reference():
    rec = {
        "T_K": 873.15,
        "P_bar": 1.5,
        "X": 0.35,
        "S": 0.90,
        "r": 2.0,
        "y_key": 1.0,
        "y_cofeed": 0.0,
        "y_h2": 0.0,
        "t_cycle_h": 24.0,
        "components": [["Pt", 0.30], ["Sn", 0.60], ["Al", None]],
        "catalyst": "industrial Pt-Sn/Al2O3 reference",
    }
    out = plant_cost(rec)
    out["name"] = "750 kt/y PDH reference plant (Enterprise PDH2-scale, Pt-Sn/Al2O3 catalyst)"
    out["record"] = rec
    return out
