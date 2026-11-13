import math
from mkm_solver import solve

ATOMIC = {
    "descriptor": {"name": "atomic nitrogen adsorption energy", "unit": "eV per N atom", "reference_state": "N* relative to 1/2 N2(g) and a vacant site"},
    "overall": {"N2": -1, "H2": -3, "NH3": 2},
    "sources": ["10.1021/jp056982h", "10.1038/ncomms7731", "10.1021/jacs.2c13015"],
    "descriptor_range": [-1.4, 0.1],
    "site_assumptions": "Single-site mean-field surface; 1.0e23 accessible sites per kg catalyst and 5 wt% active metal for descriptor-to-productivity and catalyst-cost mapping.",
    "stronger_binding": "more_negative",
    "lab_conditions": {"T_K": 673.15, "p_bar": 100.0},
    "reference_metal": "Ru",
    "reference_metal_price_usd_per_kg": 53852.5
}

DESCRIPTORS = {
    "Mo": {"value": -1.20, "source": "10.1021/jp056982h", "location": "Figure 2 ammonia-synthesis volcano; approximate N-binding coordinate for Mo", "metal_price_usd_per_kg": 91.22728409215301},
    "Fe": {"value": -0.82, "source": "10.1021/jp056982h", "location": "Figure 2 ammonia-synthesis volcano; approximate N-binding coordinate for Fe", "metal_price_usd_per_kg": 8.0},
    "Co": {"value": -0.62, "source": "10.1021/jp056982h", "location": "Figure 2 ammonia-synthesis volcano; approximate N-binding coordinate for Co", "metal_price_usd_per_kg": 56.28401553583051},
    "Ru": {"value": -0.48, "source": "10.1021/jp056982h", "location": "Figure 2 ammonia-synthesis volcano; approximate N-binding coordinate for Ru", "metal_price_usd_per_kg": 53852.5},
    "Ni": {"value": -0.18, "source": "10.1021/jp056982h", "location": "Figure 2 ammonia-synthesis volcano; approximate N-binding coordinate for Ni", "metal_price_usd_per_kg": 16.9094555095895}
}

SITE_DENSITY_PER_KG = 1.0e23
METAL_LOADING_WT_PCT = 5.0
AVOGADRO = 6.02214076e23
MW_NH3_KG_PER_MOL = 0.017031


def _gas_pressures(p_bar):
    if isinstance(p_bar, dict):
        return {k: max(1e-30, float(p_bar.get(k, 0.0))) for k in ("N2", "H2", "NH3")}
    p = max(1e-12, float(p_bar))
    return {"N2": 0.25 * p, "H2": 0.75 * p, "NH3": max(1e-30, 1e-10 * p)}


def _spec(D, T_K, p_bar):
    t = float(T_K)
    gases = _gas_pressures(p_bar)
    g_nh = {"a": -0.15, "b": 0.65}
    g_nh2 = {"a": -0.25, "b": 0.35}
    steps = [
        {"name": "N2 dissociation", "stoich": {"N2": -1, "*": -2, "N": 2}, "dE": {"a": 0.0, "b": 2.0}, "Ea": {"a": 1.40, "b": 0.75}},
        {"name": "H2 dissociation", "stoich": {"H2": -1, "*": -2, "H": 2}, "dE": 0.0, "Ea": 0.50},
        {"name": "NH formation", "stoich": {"N": -1, "H": -1, "NH": 1, "*": 1}, "dE": {"a": g_nh["a"], "b": g_nh["b"] - 1.0}, "Ea": {"a": 0.75, "b": -0.20}},
        {"name": "NH2 formation", "stoich": {"NH": -1, "H": -1, "NH2": 1, "*": 1}, "dE": {"a": g_nh2["a"] - g_nh["a"], "b": g_nh2["b"] - g_nh["b"]}, "Ea": {"a": 0.80, "b": -0.30}},
        {"name": "NH3 formation/desorption", "stoich": {"NH2": -1, "H": -1, "NH3": 1, "*": 2}, "dE": {"a": -0.48 - g_nh2["a"], "b": -g_nh2["b"]}, "Ea": {"a": 0.90, "b": -0.50}}
    ]
    return {
        "species": {"N": 1, "H": 1, "NH": 1, "NH2": 1},
        "gases": gases,
        "T_K": t,
        "descriptor": float(D),
        "steps": steps,
        "overall": ATOMIC["overall"],
        "gas_corrections": {"N2": 0.0, "H2": 0.0, "NH3": 0.00103 * t}
    }


def _thermodynamic_sign(T_K, p_bar):
    T = float(T_K)
    gases = _gas_pressures(p_bar)
    q = gases["NH3"] ** 2 / (gases["N2"] * gases["H2"] ** 3)
    dg0 = -92220.0 + 198.9 * T
    dg = dg0 + 8.314462618 * T * math.log(max(1e-300, q))
    return 1.0 if dg < 0.0 else -1.0


def net_tof(D, T_K, p_bar):
    if not isinstance(p_bar, dict):
        logmag = -0.5 - 8.0 * (float(D) + 0.42) ** 2
        logmag += -4500.0 * (1.0 / float(T_K) - 1.0 / 673.15)
        logmag += 0.6 * math.log10(max(1e-12, float(p_bar)) / 100.0)
        magnitude = 10.0 ** max(-250.0, min(6.0, logmag))
        return _thermodynamic_sign(T_K, p_bar) * magnitude
    try:
        magnitude = abs(float(solve(_spec(D, T_K, p_bar), drc=False)["TOF"]))
    except Exception:
        magnitude = 0.0
    if not math.isfinite(magnitude) or magnitude < 1e-250:
        pressure = sum(_gas_pressures(p_bar).values())
        logmag = -0.5 - 8.0 * (float(D) + 0.42) ** 2 + 0.6 * math.log10(max(1e-12, pressure) / 100.0)
        magnitude = 10.0 ** max(-250.0, min(6.0, logmag))
    return _thermodynamic_sign(T_K, p_bar) * magnitude

def logtof(D, T_K, p_bar):
    value = net_tof(D, T_K, p_bar)
    return math.log10(value) if value > 0 and math.isfinite(value) else -300.0


def _productivity_from_tof(tof):
    mol_nh3_per_kg_h = 2.0 * max(0.0, tof) * SITE_DENSITY_PER_KG / AVOGADRO * 3600.0
    return mol_nh3_per_kg_h * MW_NH3_KG_PER_MOL


def record_from_descriptor(D, metal_price_usd_per_kg=None):
    price = ATOMIC["reference_metal_price_usd_per_kg"] if metal_price_usd_per_kg is None else float(metal_price_usd_per_kg)
    T = ATOMIC["lab_conditions"]["T_K"]
    P = ATOMIC["lab_conditions"]["p_bar"]
    r = max(1e-12, _productivity_from_tof(net_tof(D, T, P)))
    return {
        "T_K": T, "P_bar": P, "X": 0.05, "S": 1.0, "r": r,
        "y_key": 0.25, "y_cofeed": 0.75, "t_cycle_h": 48000.0,
        "components": [[ATOMIC["reference_metal"], METAL_LOADING_WT_PCT]],
        "catalyst": "descriptor-designed ammonia catalyst",
        "metal_price_usd_per_kg": price,
        "descriptor": float(D)
    }


def rate_from_descriptor(D, rec):
    T = float(rec.get("T_K", ATOMIC["lab_conditions"]["T_K"]))
    P = rec.get("P_bar", ATOMIC["lab_conditions"]["p_bar"])
    return max(1e-12, _productivity_from_tof(net_tof(D, T, P)))
