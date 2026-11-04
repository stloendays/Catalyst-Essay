"""Independent IDEAL-GAS ammonia equilibrium references for an UNFROZEN audit.

Reaction: N2 + 3 H2 <=> 2 NH3; pressures in bar, standard state 1 bar.
g_form(T) in eV per NH3: G_NH3 - 0.5 G_N2 - 1.5 G_H2.
Kp_full = exp[-2*g_form/(k_B*T)] is dimensionless under the 1-bar
standard-state convention.  No fitted catalyst kinetics are imported here.

Sources and provenance:
- NIST Chemistry WebBook Shomate coefficients, H2, N2, NH3.
- Gillespie-Beattie industrial K half-reaction correlation as transcribed
  in exploratory, corrected PR #68 (run_v2.py).
These references are restricted to the frozen temperature grid 350-450 C.
The frozen MKM is NOT replaced or certified by this module.
"""
from __future__ import annotations

import math

KB_EV = 8.617333262145e-5
R = 8.314462618
J_PER_MOL_PER_EV = 96485.33212331002
VALID_K = (623.15, 723.15)

# NIST 1-bar Shomate A, B, C, D, E, F, G, H. All T in the 350-450 C window.
NIST = {
    "N2": (19.50583, 19.88705, -8.598535, 1.369784,
           0.527601, -4.935202, 212.3900, 0.0),
    "H2": (33.066178, -11.363417, 11.432816, -2.772874,
           -0.158558, -9.980797, 172.707974, 0.0),
    "NH3": (19.99563, 49.77119, -15.37599, 1.921168,
            0.189174, -53.30667, 203.8591, -45.89806),
}


def _check_t(T: float) -> float:
    T = float(T)
    if not math.isfinite(T) or not VALID_K[0] - 1e-8 <= T <= VALID_K[1] + 1e-8:
        raise ValueError(f"Reference outside its frozen 350-450 C domain: {T} K")
    return T


def nist_h_s(species: str, T: float) -> tuple[float, float]:
    """Return absolute standard enthalpy J/mol, entropy J/(mol K).

    Reference elemental H(298)=0; ammonia includes NIST formation enthalpy.
    Shomate enthalpy increment: H(T)-H(298), in kJ/mol.
    """
    T = _check_t(T)
    A, B, C, D, E, F, G, H = NIST[species]
    t = T / 1000.0
    dh = A*t + B*t*t/2 + C*t**3/3 + D*t**4/4 - E/t + F - H
    s = A*math.log(t) + B*t + C*t*t/2 + D*t**3/3 - E/(2*t*t) + G
    return (H + dh)*1000.0, s


def gform_nist_ev(T: float) -> float:
    """Independent NIST delta G per NH3, eV; reaction is 2 NH3."""
    T = _check_t(T)
    gs = {}
    for species in ("H2", "N2", "NH3"):
        h, s = nist_h_s(species, T)
        gs[species] = h - T*s
    delta_g_full = 2*gs["NH3"] - gs["N2"] - 3*gs["H2"]
    return delta_g_full / (2.0 * J_PER_MOL_PER_EV)


def gb_half_k(T: float) -> float:
    """Gillespie-Beattie correlation K_half for bar-based ideal fugacities.

    Half reaction 1/2 N2 + 3/2 H2 -> NH3, Q_half has units (bar)^-1
    when numerical partial pressures are in bar. Divide the correlation's
    atmosphere-basis K by 1.01325, as in corrected exploratory PR #68.
    """
    T = _check_t(T)
    log10k_atm = (
        -2.691122*math.log10(T) - 5.519265e-5*T
        + 1.848863e-7*T*T + 2001.6/T + 2.6899
    )
    return 10.0**log10k_atm / 1.01325


def gform_gb_ev(T: float) -> float:
    T = _check_t(T)
    return -KB_EV*T*math.log(gb_half_k(T))


def full_kp(gform_ev: float, T: float) -> float:
    T = _check_t(T)
    return math.exp(-2.0*float(gform_ev)/(KB_EV*T))


def equilibrium_y_nh3(T: float, P_bar: float, gform_ev: float) -> float:
    """Ideal 1:3 N2/H2 feed, zero initial NH3; NH3 mole fraction at eq.

    Independent bisection over the extent 0 < xi < 1 to avoid using the
    frozen process's reactor model for its own validation.
    """
    T = _check_t(T)
    P_bar = float(P_bar)
    if not math.isfinite(P_bar) or P_bar <= 0:
        raise ValueError("P_bar must be positive")
    kh = math.sqrt(full_kp(gform_ev, T))

    def ratio(x: float) -> float:
        total = 4.0 - 2.0*x
        p_n2 = P_bar*(1.0-x)/total
        p_h2 = P_bar*(3.0-3.0*x)/total
        p_nh3 = P_bar*2.0*x/total
        return p_nh3 / (math.sqrt(p_n2)*p_h2**1.5)

    lo, hi = 0.0, 1.0-1e-12
    if ratio(hi) < kh:
        raise ValueError("Equilibrium extent not bracketed")
    for _ in range(110):
        mid = (lo+hi)/2.0
        if ratio(mid) < kh:
            lo = mid
        else:
            hi = mid
    xi = (lo+hi)/2.0
    return 2.0*xi/(4.0-2.0*xi)


def reference_summary(T: float = 698.15, P_bar: float = 90.0) -> dict:
    return {
        mode: {
            "gform_eV_per_NH3": g,
            "Kp_full": full_kp(g, T),
            "ideal_y_NH3": equilibrium_y_nh3(T, P_bar, g),
        }
        for mode, g in (
            ("NIST", gform_nist_ev(T)),
            ("Gillespie-Beattie", gform_gb_ev(T)),
        )
    }
