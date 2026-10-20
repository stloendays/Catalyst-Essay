"""Sabatier (CO2 methanation) Ru/Al2O3 vs Ni/Al2O3 catalyst-dependent cost model.

Literature-level rank-preservation / decision-boundary case built on Moioli & Zuettel,
Sustainable Energy Fuels 2020, 4, 1396-1408 (DOI 10.1039/C9SE00787C).  Every sourced
number is listed in SOURCE_LEDGER.csv; bracketed (unsourced) parameters are marked there.

The cost chain follows the repository convention used by the ammonia harness
(provenance/discover_v1/source_harness/harness_core.py::cost_arrays):

    activity -> catalyst inventory -> reactor capital -> metal/catalyst replacement

plus one term the ammonia chain does not need: the Ni process-topology penalty of an
intermediate water-condensation stage (second reactive stage + condenser/reheater set).

Only catalyst-dependent terms are costed.  Hydrogen, CO2, compression and heat
integration are common to both catalysts at the declared boundary and are excluded.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

# --------------------------------------------------------------------------- constants
R = 8.314462618                      # J mol-1 K-1
LHV_CH4_KJ_MOL = 802.3               # kJ mol-1 (lower heating value)
V_STP_M3_MOL = 0.022414              # m3 mol-1 at 0 degC, 1 atm
EUR_TO_USD = 1.12                    # fixed conversion for the 2019 EUR figures of the source
HOURS_Y = 8760.0

# Frozen repository metal prices (USD kg-1), harness_core.PRICE
PRICE_USD_KG = {"Ru": 53852.5, "Ni": 16.9094555095895}

# Source Table 6 (Moioli & Zuettel 2020): cost of metal in each basis, EUR per kg of metal
SOURCE_BASIS_EUR_PER_KG_METAL = {
    "Ru": {"metal": 8233.0, "precursor": 207900.0, "commercial": 592800.0},
    "Ni": {"metal": 12.0, "precursor": 680.0, "commercial": 1700.0},
}
# Non-metal manufacturing increment per kg of metal, EUR (basis value minus pure-metal value)
MANUFACTURING_INCREMENT_EUR_PER_KG_METAL = {
    m: {b: SOURCE_BASIS_EUR_PER_KG_METAL[m][b] - SOURCE_BASIS_EUR_PER_KG_METAL[m]["metal"]
        for b in ("metal", "precursor", "commercial")}
    for m in ("Ru", "Ni")
}

# Frozen repository reactor correlation and financing (nh3_final.yaml economics block)
REACTOR_FIXED_USD = 66800.0
REACTOR_VAR_USD = 268000.0
REACTOR_REF_M3 = 20.0
REACTOR_EXP = 0.52
DISCOUNT_RATE = 0.12
PLANT_LIFE_Y = 25
CAPACITY_FACTOR = 0.95
CRF = DISCOUNT_RATE * (1 + DISCOUNT_RATE) ** PLANT_LIFE_Y / ((1 + DISCOUNT_RATE) ** PLANT_LIFE_Y - 1)


@dataclass(frozen=True)
class Params:
    """One parameter set.  Defaults are the pre-registered central values."""
    conversion: float = 0.995        # target CO2 conversion (source Sec. 3.3 / Table 6)
    ghsv_h: float = 3000.0           # h-1, STP basis (source Figs 1-2)
    r_V: float = 1.89                # V_Ni / V_Ru at 99.5 % yield with condensation (source Table 6)
    rho_bulk_kg_m3: float = 1500.0   # source Table 5
    w_Ru: float = 0.005              # 0.5 wt % Ru (source Table 6)
    w_Ni: float = 0.35               # 35 wt % Ni (source Table 6)
    ru_price_mult: float = 1.0
    ni_price_mult: float = 1.0
    ru_recovery: float = 0.0         # frozen harness default; bracketed in MC
    ni_recovery: float = 0.0
    life_y: float = 5.0              # bracketed, not sourced
    basis_u: float = 0.5             # 0 metal-only, 0.5 precursor, 1 commercial (source Table 6)
    kappa: float = 1.5               # inter-stage condensation set as multiple of one Ni stage vessel; bracketed
    capex_mult: float = 1.0
    n_ni_stages: int = 2             # Ni needs one intermediate condensation (source Sec. 3.5)


CENTRAL = Params()


# --------------------------------------------------------------------------- helpers
def manufacturing_increment_eur(metal: str, u) -> np.ndarray:
    """Piecewise-linear non-metal increment per kg metal: u=0 metal-only, 0.5 precursor, 1 commercial."""
    u = np.asarray(u, dtype=float)
    inc = MANUFACTURING_INCREMENT_EUR_PER_KG_METAL[metal]
    lo = np.clip(u / 0.5, 0.0, 1.0) * inc["precursor"]
    hi = np.clip((u - 0.5) / 0.5, 0.0, 1.0) * (inc["commercial"] - inc["precursor"])
    return lo + hi


def catalyst_price_usd_per_kg(metal: str, w, price_mult, recovery, basis_u) -> np.ndarray:
    """USD per kg of finished catalyst = w * [metal price * (1 - recovery) + manufacturing increment]."""
    metal_term = PRICE_USD_KG[metal] * np.asarray(price_mult, dtype=float) * (1.0 - np.asarray(recovery, dtype=float))
    manuf_term = manufacturing_increment_eur(metal, basis_u) * EUR_TO_USD
    return np.asarray(w, dtype=float) * (metal_term + manuf_term)


def stage_capex_usd(V_m3, capex_mult=1.0) -> np.ndarray:
    """Frozen repository reactor-vessel correlation, one reactive stage of volume V."""
    V = np.asarray(V_m3, dtype=float)
    return np.asarray(capex_mult, dtype=float) * (REACTOR_FIXED_USD + REACTOR_VAR_USD * np.power(V / REACTOR_REF_M3, REACTOR_EXP))


def inlet_flow_stp_m3_h(scale_mw, conversion) -> np.ndarray:
    """Reactor inlet gas at STP for an SNG output of `scale_mw` (LHV), stoichiometric undiluted CO2:H2 = 1:4."""
    ch4_mol_s = np.asarray(scale_mw, dtype=float) * 1e3 / LHV_CH4_KJ_MOL
    co2_mol_s = ch4_mol_s / conversion
    return 5.0 * co2_mol_s * V_STP_M3_MOL * 3600.0


def annual_mwh(scale_mw) -> np.ndarray:
    return np.asarray(scale_mw, dtype=float) * HOURS_Y * CAPACITY_FACTOR


# --------------------------------------------------------------------------- cost chain
def cost_chain(scale_mw, p: Params | None = None, **over) -> dict:
    """Catalyst-dependent cost (USD per MWh SNG) for Ru and Ni at plant scale(s) `scale_mw`.

    Array-valued in scale_mw and in any array-valued override (for Monte Carlo).
    Returns every intermediate so the leverage inequality can be rebuilt from the parts.
    """
    p = replace(p or CENTRAL, **over) if over else (p or CENTRAL)
    S = np.asarray(scale_mw, dtype=float)
    Q = inlet_flow_stp_m3_h(S, p.conversion)
    V_Ru = Q / np.asarray(p.ghsv_h, dtype=float)
    V_Ni = np.asarray(p.r_V, dtype=float) * V_Ru
    m_Ru = V_Ru * p.rho_bulk_kg_m3
    m_Ni = V_Ni * p.rho_bulk_kg_m3
    pc_Ru = catalyst_price_usd_per_kg("Ru", p.w_Ru, p.ru_price_mult, p.ru_recovery, p.basis_u)
    pc_Ni = catalyst_price_usd_per_kg("Ni", p.w_Ni, p.ni_price_mult, p.ni_recovery, p.basis_u)
    L = np.asarray(p.life_y, dtype=float)
    A_Ru = m_Ru * pc_Ru / L                       # USD y-1 catalyst replacement
    A_Ni = m_Ni * pc_Ni / L
    cap_Ru = stage_capex_usd(V_Ru, p.capex_mult)
    n = p.n_ni_stages
    cap_Ni_stages = n * stage_capex_usd(V_Ni / n, p.capex_mult)
    cap_Ni_cond = (n - 1) * np.asarray(p.kappa, dtype=float) * stage_capex_usd(V_Ni / n, p.capex_mult)
    R_Ru = cap_Ru * CRF
    R_Ni = (cap_Ni_stages + cap_Ni_cond) * CRF
    mwh = annual_mwh(S)
    C_Ru = (A_Ru + R_Ru) / mwh
    C_Ni = (A_Ni + R_Ni) / mwh
    Pi = pc_Ru / pc_Ni                            # catalyst price penalty ratio per kg catalyst
    phi = (R_Ni - R_Ru) / A_Ni                    # Ni net process/reactor penalty as fraction of Ni catalyst cost
    lev_lhs = np.asarray(p.r_V, dtype=float) * (1.0 + phi)
    return dict(
        scale_mw=S, Q_stp_m3_h=Q, V_Ru_m3=V_Ru, V_Ni_m3=V_Ni, m_Ru_kg=m_Ru, m_Ni_kg=m_Ni,
        metal_Ru_kg=m_Ru * p.w_Ru, metal_Ni_kg=m_Ni * p.w_Ni,
        pcat_Ru_usd_kg=pc_Ru, pcat_Ni_usd_kg=pc_Ni,
        A_Ru_usd_y=A_Ru, A_Ni_usd_y=A_Ni, R_Ru_usd_y=R_Ru, R_Ni_usd_y=R_Ni,
        capex_Ru_usd=cap_Ru, capex_Ni_stages_usd=cap_Ni_stages, capex_Ni_cond_usd=cap_Ni_cond,
        cost_Ru_usd_mwh=C_Ru, cost_Ni_usd_mwh=C_Ni, diff_ru_minus_ni_usd_mwh=C_Ru - C_Ni,
        ru_cheaper=C_Ru < C_Ni, Pi=Pi, phi_proc=phi, leverage_lhs=lev_lhs, leverage_margin=lev_lhs - Pi,
    )


def parity_scale_mw(p: Params | None = None, lo=0.1, hi=100.0, tol=1e-10, **over):
    """Scale at which C_Ru == C_Ni by bisection in log10 S.  Returns (S*, status)."""
    f = lambda logS: float(cost_chain(10.0 ** logS, p, **over)["diff_ru_minus_ni_usd_mwh"])
    a, b = math.log10(lo), math.log10(hi)
    fa, fb = f(a), f(b)
    if fa < 0 and fb < 0:
        return math.nan, "ru_cheaper_everywhere"
    if fa > 0 and fb > 0:
        return math.nan, "ni_cheaper_everywhere"
    if fa == 0:
        return 10.0 ** a, "root"
    for _ in range(300):
        c = 0.5 * (a + b)
        fc = f(c)
        if fc == 0 or (b - a) < tol:
            return 10.0 ** c, "root"
        if (fc < 0) == (fa < 0):
            a, fa = c, fc
        else:
            b, fb = c, fc
    return 10.0 ** (0.5 * (a + b)), "root"


def parity_scale_from_leverage(p: Params | None = None, lo=0.1, hi=100.0, tol=1e-10, **over):
    """Same root solved on the leverage inequality r_V (1 + phi(S)) - Pi = 0 (H3 bookkeeping check)."""
    f = lambda logS: float(cost_chain(10.0 ** logS, p, **over)["leverage_margin"])
    a, b = math.log10(lo), math.log10(hi)
    fa, fb = f(a), f(b)
    if (fa > 0) == (fb > 0):
        return math.nan, ("ru_cheaper_everywhere" if fa > 0 else "ni_cheaper_everywhere")
    for _ in range(300):
        c = 0.5 * (a + b)
        fc = f(c)
        if fc == 0 or (b - a) < tol:
            return 10.0 ** c, "root"
        if (fc > 0) == (fa > 0):
            a, fa = c, fc
        else:
            b, fb = c, fc
    return 10.0 ** (0.5 * (a + b)), "root"


# --------------------------------------------------------------------------- kinetic cross-check
def k_eq_sabatier_bar(T_K):
    """CO2 + 4 H2 <-> CH4 + 2 H2O equilibrium constant, bar^-2 (Koschany et al. 2016, Eq. A.8 form)."""
    T = np.asarray(T_K, dtype=float)
    return 137.0 * np.power(T, -3.998) * np.exp(158.7e3 / (R * T))


def rate_ru_falbo(T_K, p_atm: dict) -> float:
    """Ru/Al2O3 power law as tabulated by Moioli & Zuettel (Table 1, from Falbo et al. 2018).

    r = k0 exp(-EA/RT) [ (pCO2^n pH2^4n) - (pCH4^n pH2O^2n) / Keq^n ],  mol s-1 gcat-1, pressures in atm.
    n = 0.076, k0 = 18.26 mol s-1 gcat-1 atm^-5n, EA = 65.2 kJ mol-1.
    """
    n, k0, EA = 0.076, 18.26, 65.2e3
    k = k0 * math.exp(-EA / (R * T_K))
    Keq = float(k_eq_sabatier_bar(T_K)) * (1.01325 ** 2)   # bar^-2 -> atm^-2
    fwd = p_atm["CO2"] ** n * p_atm["H2"] ** (4 * n)
    rev = (p_atm["CH4"] ** n * p_atm["H2O"] ** (2 * n)) / Keq ** n
    return k * (fwd - rev)


def rate_ni_koschany(T_K, p_bar: dict, T_ref=555.0, k_ref=3.46e-4) -> float:
    """Ni/Al2O3 LHHW (Koschany, Schlereth, Hinrichsen 2016, as tabulated by Moioli & Zuettel Table 3).

    r = k pH2^0.5 pCO2^0.5 (1 - pCH4 pH2O^2 / (pCO2 pH2^4 Keq)) / (1 + K_OH pH2O/pH2^0.5 + K_H2 pH2^0.5 + K_mix pCO2^0.5)^2
    k_ref = 3.46e-4 mol bar-1 s-1 gcat-1 (two secondary SI tabulations) or 3.46e-5 (as printed in Moioli & Zuettel
    Table 3); EA = 77.5 kJ/mol; K_OH 0.5 (22.4), K_H2 0.44 (-6.2), K_mix 0.88 (-10.0) bar^-0.5 (kJ/mol).
    The original Koschany paper was not accessible; both printed k_ref values are carried as a documented ambiguity.
    """
    k = k_ref * math.exp(77.5e3 / R * (1 / T_ref - 1 / T_K))
    vh = lambda K0, dH: K0 * math.exp(dH * 1e3 / R * (1 / T_ref - 1 / T_K))
    K_OH, K_H2, K_mix = vh(0.5, 22.4), vh(0.44, -6.2), vh(0.88, -10.0)
    pH2, pCO2, pCH4, pH2O = p_bar["H2"], p_bar["CO2"], p_bar["CH4"], p_bar["H2O"]
    Keq = float(k_eq_sabatier_bar(T_K))
    drv = 1.0 - pCH4 * pH2O ** 2 / max(pCO2 * pH2 ** 4 * Keq, 1e-300)
    den = (1.0 + K_OH * pH2O / math.sqrt(pH2) + K_H2 * math.sqrt(pH2) + K_mix * math.sqrt(pCO2)) ** 2
    return k * math.sqrt(pH2) * math.sqrt(pCO2) * drv / den


def partial_pressures(X, P_bar):
    """Stoichiometric CO2:H2 = 1:4, undiluted, conversion X; total moles 5 - 2X per mol CO2 fed."""
    tot = 5.0 - 2.0 * X
    y = {"CO2": (1 - X) / tot, "H2": 4 * (1 - X) / tot, "CH4": X / tot, "H2O": 2 * X / tot}
    return {s: max(v, 1e-12) * P_bar for s, v in y.items()}


def isothermal_pfr_mass_per_mol_co2(rate_fn, T_K, P_bar, X_target, pressure_unit="bar", n=4000):
    """Catalyst mass (g) per (mol CO2 s-1) fed to reach X_target in an isothermal plug-flow bed.

    W/F = integral_0^X dX / r(X); trapezoidal on a uniform X grid.  Returns inf if equilibrium is reached first.
    """
    Xs = np.linspace(0.0, X_target, n + 1)
    inv = np.empty_like(Xs)
    for i, X in enumerate(Xs):
        pp = partial_pressures(X, P_bar)
        if pressure_unit == "atm":
            pp = {s: v / 1.01325 for s, v in pp.items()}
        r = rate_fn(T_K, pp)
        if r <= 0:
            return math.inf
        inv[i] = 1.0 / r
    return float(np.trapezoid(inv, Xs))


def kinetic_volume_ratio(T_C=300.0, P_bar=10.0, X_target=0.90):
    """Isothermal V_Ni / V_Ru from the tabulated rate laws at equal bulk density (cross-check only).

    Reported for both printed Koschany k_ref values (3.46e-4 and 3.46e-5 mol bar-1 s-1 gcat-1).
    """
    T = T_C + 273.15
    W_Ru = isothermal_pfr_mass_per_mol_co2(rate_ru_falbo, T, P_bar, X_target, pressure_unit="atm")
    W_Ni = isothermal_pfr_mass_per_mol_co2(rate_ni_koschany, T, P_bar, X_target, pressure_unit="bar")
    W_Ni_lo = isothermal_pfr_mass_per_mol_co2(lambda t, p: rate_ni_koschany(t, p, k_ref=3.46e-5), T, P_bar, X_target, pressure_unit="bar")
    ok = lambda a, b: (a / b if math.isfinite(a) and math.isfinite(b) else math.nan)
    return dict(T_C=T_C, P_bar=P_bar, X_target=X_target, W_Ru_g_per_mol_s=W_Ru, W_Ni_g_per_mol_s_kref_3p46e_4=W_Ni,
                W_Ni_g_per_mol_s_kref_3p46e_5=W_Ni_lo, ratio_Ni_over_Ru_kref_3p46e_4=ok(W_Ni, W_Ru),
                ratio_Ni_over_Ru_kref_3p46e_5=ok(W_Ni_lo, W_Ru))
