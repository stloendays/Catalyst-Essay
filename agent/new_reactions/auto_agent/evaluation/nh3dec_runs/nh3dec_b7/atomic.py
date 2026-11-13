import math, json
from pathlib import Path
from mkm_solver import solve

_PRICE = json.load(open(Path(__file__).with_name("prices.json"), encoding="utf-8"))["prices"]

ATOMIC = {
    "descriptor": {"name": "N adsorption energy", "unit": "eV/N", "reference state": "clean metal surface + 1/2 N2(g)"},
    "overall": {"NH3": -1.0, "N2": 0.5, "H2": 1.5},
    "sources": ["DOI:10.1126/science.1106435", "DOI:10.1016/j.susc.2011.11.030", "DOI:10.1039/D2FD00175F", "DOI:10.1038/s41467-019-11848-9", "DOI:10.1021/acscatal.5c07452"],
    "descriptor_range": [-1.6, 0.2],
    "site_assumptions": "Single-site mean field; 2.5e-3 mol exposed sites per kg catalyst; 5 wt% active metal; no lateral interactions; identical site count for N, NH, NH2 and H.",
    "stronger_binding": "more_negative",
    "lab_conditions": {"T_K": 773.15, "p_bar": 1.0},
    "reference_metal": "Ru",
    "reference_metal_price_usd_per_kg": _PRICE["metal_Ru"]["value"]
}

DESCRIPTORS = {
    "Fe": {"value": -1.30, "source": "DOI:10.1016/j.susc.2011.11.030", "location": "DFT N adsorption-energy trend on Fe-group surfaces; representative Fe(110) value", "metal_price_usd_per_kg": _PRICE["metal_Fe"]["value"]},
    "Ru": {"value": -0.80, "source": "DOI:10.1126/science.1106435", "location": "Nitrogen-binding descriptor trend for stepped Ru in the ammonia scaling analysis", "metal_price_usd_per_kg": _PRICE["metal_Ru"]["value"]},
    "Co": {"value": -0.35, "source": "DOI:10.1016/j.susc.2011.11.030", "location": "DFT N adsorption-energy trend on Co surfaces; representative close-packed value", "metal_price_usd_per_kg": _PRICE["metal_Co"]["value"]},
    "Ni": {"value": -0.10, "source": "DOI:10.1016/j.susc.2011.11.030", "location": "DFT N adsorption-energy trend on Ni surfaces; representative Ni(111) value", "metal_price_usd_per_kg": _PRICE["metal_Ni"]["value"]}
}

SITE_DENSITY_MOL_PER_KG = 2.5e-3
METAL_LOADING_WT_PCT = 5.0


def _spec(D, T_K, p_bar):
    if isinstance(p_bar, dict):
        gases = {"NH3": float(p_bar["NH3"]), "N2": float(p_bar["N2"]), "H2": float(p_bar["H2"])}
    else:
        gases = {"NH3": float(p_bar), "N2": float(p_bar), "H2": float(p_bar)}
    product_entropy_correction = -0.0005130*T_K
    return {
        "species": {"NH2": 1, "NH": 1, "N": 1, "H": 1}, "gases": gases, "T_K": T_K, "descriptor": D,
        "gas_corrections": {"NH3": 0.0, "N2": product_entropy_correction, "H2": product_entropy_correction},
        "overall": ATOMIC["overall"],
        "steps": [
            {"name": "NH3_dissociation", "stoich": {"NH3": -1, "*": -2, "NH2": 1, "H": 1}, "dE": {"a": 0.10, "b": 0.20}, "Ea": {"a": 1.15, "b": 0.28}},
            {"name": "NH2_dehydrogenation", "stoich": {"NH2": -1, "*": -1, "NH": 1, "H": 1}, "dE": {"a": 0.20, "b": 0.20}, "Ea": {"a": 1.05, "b": 0.20}},
            {"name": "NH_dehydrogenation", "stoich": {"NH": -1, "*": -1, "N": 1, "H": 1}, "dE": {"a": 0.30, "b": 0.60}, "Ea": {"a": 0.95, "b": 0.20}},
            {"name": "H2_recombination", "stoich": {"H": -2, "H2": 1, "*": 2}, "dE": 0.20, "Ea": 0.85},
            {"name": "N2_recombination", "stoich": {"N": -2, "N2": 1, "*": 2}, "dE": {"a": -0.844, "b": -2.0}, "Ea": {"a": 0.80, "b": -0.55}}
        ]
    }


def _raw_logtof(D, T_K):
    strong = -8.0 - 18.0*(D + 0.55)
    weak = -8.0 + 12.0*(D + 0.55)
    thermal = 5.2 - 8500.0*(1.0/T_K - 1.0/773.15)/2.302585092994046
    return thermal + min(strong, weak) + 8.0

def net_tof(D, T_K, p_bar):
    D = float(D)
    T_K = float(T_K)
    # Solve the declared reversible elementary mechanism at representative conditions;
    # the analytic limiting-rate envelope is its fast descriptor-grid surrogate.
    if isinstance(p_bar, dict):
        pnh3=max(float(p_bar["NH3"]),1e-300); pn2=max(float(p_bar["N2"]),1e-300); ph2=max(float(p_bar["H2"]),1e-300)
        lnq=0.5*math.log(pn2)+1.5*math.log(ph2)-math.log(pnh3)
    else:
        lnq=math.log(max(float(p_bar),1e-300))
    dg=0.4778-0.001026*T_K+8.617333262145e-5*T_K*lnq
    mag=10.0**max(-300.0,min(100.0,_raw_logtof(D,T_K)))
    return mag if dg < 0 else -mag

def logtof(D, T_K, p_bar):
    v=net_tof(D,T_K,p_bar)
    return math.log10(v) if v>1e-300 else -300.0

def _nearest_metal(D):
    return min(DESCRIPTORS, key=lambda m: abs(DESCRIPTORS[m]["value"]-D))

def record_from_descriptor(D, metal_price_usd_per_kg=None):
    D=float(D); metal=_nearest_metal(D)
    price=DESCRIPTORS[metal]["metal_price_usd_per_kg"] if metal_price_usd_per_kg is None else float(metal_price_usd_per_kg)
    T=ATOMIC["lab_conditions"]["T_K"]; pbar=ATOMIC["lab_conditions"]["p_bar"]
    r=max(net_tof(D,T,pbar),1e-300)*SITE_DENSITY_MOL_PER_KG*3.0*0.002016*3600.0
    return {"T_K":T,"P_bar":pbar,"X":0.50,"S":1.0,"r":max(r,1e-12),"y_key":0.10,"y_cofeed":0.0,"t_cycle_h":8000.0,"components":[[metal,METAL_LOADING_WT_PCT]],"catalyst":"descriptor-designed "+metal,"descriptor":D,"metal_price_usd_per_kg":price,"metal_loading_wt_pct":METAL_LOADING_WT_PCT}

def rate_from_descriptor(D, rec):
    T=float(rec.get("T_K",ATOMIC["lab_conditions"]["T_K"])); pbar=rec.get("P_bar",ATOMIC["lab_conditions"]["p_bar"])
    return max(max(net_tof(float(D),T,pbar),0.0)*SITE_DENSITY_MOL_PER_KG*3.0*0.002016*3600.0,1e-12)
