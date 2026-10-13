"""Measured ammonia-synthesis rate laws with the Gillespie-Beattie equilibrium and fugacity corrections.

All parameters are read from parameters.yaml (sources there). Rate functions take temperature T (K), total pressure
P (bar) and mole fractions yN2, yH2, yNH3 (numpy arrays or floats) and return the NH3 formation rate in
mol NH3 per kg of catalyst per second. Activities are fugacities in atm, as in every source.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
PAR = yaml.safe_load((HERE / "parameters.yaml").read_text(encoding="utf-8"))
KIN = PAR["kinetics"]

R_CAL = 1.98720425864083   # cal mol-1 K-1
R_J = 8.314462618           # J mol-1 K-1
BAR_PER_ATM = 1.01325
TINY = 1e-12

# --- Gillespie-Beattie equilibrium constant (1/2 N2 + 3/2 H2 = NH3, atm^-1) -------------------------------------


def log10_Ka(T):
    T = np.asarray(T, dtype=float)
    return -2.691122 * np.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T + 2001.6 / T + 2.6899


def Ka(T):
    return np.power(10.0, log10_Ka(T))


# --- Newton-Cooper fugacity coefficients (T in K, P in atm) -----------------------------------------------------


def fugacity_coefficients(T, P_atm):
    T = np.asarray(T, dtype=float)
    P = np.asarray(P_atm, dtype=float)
    cN = PAR["thermo"]["fugacity_coefficients"]["N2"]
    cA = PAR["thermo"]["fugacity_coefficients"]["NH3"]
    phiN = cN[0] + cN[1] * T + cN[2] * P + cN[3] * T * T + cN[4] * P * P
    phiA = cA[0] + cA[1] * T + cA[2] * P + cA[3] * T * T + cA[4] * P * P
    phiH = np.exp(np.exp(-3.8402 * T ** 0.125 + 0.541) * P - np.exp(-0.1263 * T ** 0.5 - 15.980) * P * P
                  + 300.0 * np.exp(-0.011901 * T - 5.941) * (np.exp(-P / 300.0) - 1.0))
    return phiN, phiH, phiA


def activities(T, P_bar, yN, yH, yA):
    P = np.asarray(P_bar, dtype=float) / BAR_PER_ATM
    phiN, phiH, phiA = fugacity_coefficients(T, P)
    aN = np.maximum(np.asarray(yN, dtype=float), TINY) * phiN * P
    aH = np.maximum(np.asarray(yH, dtype=float), TINY) * phiH * P
    aA = np.maximum(np.asarray(yA, dtype=float), TINY) * phiA * P
    return aN, aH, aA


# --- NIST Shomate ideal-gas enthalpy (J/mol, relative to 298.15 K formation basis) -------------------------------

SHOMATE = {
    "N2": (19.50583, 19.88705, -8.598535, 1.369784, 0.527601, -4.935202, 212.3900, 0.0),
    "H2": (33.066178, -11.363417, 11.432816, -2.772874, -0.158558, -9.980797, 172.707974, 0.0),
    "NH3": (19.99563, 49.77119, -15.37599, 1.921168, 0.189174, -53.30667, 203.8591, -45.89806),
    "CH4": (-0.703029, 108.4773, -42.52157, 5.862788, 0.678565, -76.84376, 158.7163, -74.87310),
    "Ar": (20.78600, 2.825911e-7, -1.464191e-7, 1.092131e-8, -3.661371e-8, -6.197350, 179.9990, 0.0),
}
DHF = {"N2": 0.0, "H2": 0.0, "NH3": -45.90, "CH4": -74.87, "Ar": 0.0}  # kJ/mol at 298.15 K (NIST)


def enthalpy(species, T):
    """Ideal-gas molar enthalpy in J/mol including the heat of formation at 298.15 K."""
    A, B, C, D, E, F, G, H = SHOMATE[species]
    t = np.asarray(T, dtype=float) / 1000.0
    return (DHF[species] + A * t + B * t * t / 2 + C * t ** 3 / 3 + D * t ** 4 / 4 - E / t + F - H) * 1000.0


def cp(species, T):
    A, B, C, D, E, *_ = SHOMATE[species]
    t = np.asarray(T, dtype=float) / 1000.0
    return A + B * t + C * t * t + D * t ** 3 + E / (t * t)


def heat_of_reaction(T):
    """J per mol NH3 formed (1/2 N2 + 3/2 H2 -> NH3), ideal gas."""
    return enthalpy("NH3", T) - 0.5 * enthalpy("N2", T) - 1.5 * enthalpy("H2", T)


# --- rate laws ---------------------------------------------------------------------------------------------------


def _temkin_bracket(T, aN, aH, aA, alpha):
    K = Ka(T)
    return K * K * aN * (aH ** 3 / aA ** 2) ** alpha - (aA ** 2 / aH ** 3) ** (1.0 - alpha)


def rate_fe_dyson_simon(T, P_bar, yN, yH, yA, per="kg"):
    """Dyson & Simon (1968): kmol NH3 m^-3 h^-1 -> mol NH3 kg^-1 s^-1 (or m^-3 s^-1 with per='m3')."""
    p = KIN["Fe_DysonSimon"]
    aN, aH, aA = activities(T, P_bar, yN, yH, yA)
    k = p["k0"] * np.exp(-p["E_cal_mol"] / (R_CAL * np.asarray(T, dtype=float)))
    r_m3 = 2.0 * k * _temkin_bracket(T, aN, aH, aA, p["alpha"]) * 1000.0 / 3600.0   # mol m^-3 s^-1
    return r_m3 if per == "m3" else r_m3 / p["bulk_density_kg_m3"]


def _rate_fe_tripodi(key, T, P_bar, yN, yH, yA):
    p = KIN[key]
    aN, aH, aA = activities(T, P_bar, yN, yH, yA)
    k = p["k0"] * np.exp(-p["E_cal_mol"] / (R_CAL * np.asarray(T, dtype=float)))  # kmol s^-1 kg^-1
    return k * _temkin_bracket(T, aN, aH, aA, p["alpha"]) * 1000.0


def rate_fe_wustite(T, P_bar, yN, yH, yA):
    return _rate_fe_tripodi("Fe_wustite_Tripodi", T, P_bar, yN, yH, yA)


def rate_fe_magnetite(T, P_bar, yN, yH, yA):
    return _rate_fe_tripodi("Fe_magnetite_Tripodi", T, P_bar, yN, yH, yA)


def rate_fe_gramatica(T, P_bar, yN, yH, yA, k20=None):
    p = KIN["Fe_Gramatica_industrial"]
    k20 = p["k20"] if k20 is None else k20
    T = np.asarray(T, dtype=float)
    aN, aH, aA = activities(T, P_bar, yN, yH, yA)
    k2 = k20 * np.exp(-p["E_cal_mol"] / R_CAL * (1.0 / T - 1.0 / p["T0_K"]))   # kmol NH3 h^-1 t^-1
    return k2 * _temkin_bracket(T, aN, aH, aA, p["alpha"]) / 3600.0               # mol kg^-1 s^-1


def ru_n2_rate_per_litre_h(T, P_bar, yN, yH, yA, lam=1.0):
    """Rossetti et al. (2006) eq 14: mol of the defective reactant per hour per litre of catalyst."""
    p = KIN["Ru_C_Rossetti"]
    T = np.asarray(T, dtype=float)
    aN, aH, aA = activities(T, P_bar, yN, yH, yA)
    kf = p["A"] * np.exp(-p["Ea_cal_mol"] / (R_CAL * T))
    KH = np.exp(p["dS_H2_cal_molK"] / R_CAL - p["dH_H2_cal_mol"] / (R_CAL * T))
    KA = np.exp(p["dS_NH3_cal_molK"] / R_CAL - p["dH_NH3_cal_mol"] / (R_CAL * T))
    num = aN ** 0.5 * aH ** 0.375 / aA ** 0.25 - aA ** 0.75 / (Ka(T) * aH ** 1.125)
    return kf * lam * num / (1.0 + KH * aH ** 0.3 + KA * aA ** 0.2)


def rate_ru_rossetti(T, P_bar, yN, yH, yA, ru_wt_frac=None):
    """mol NH3 kg^-1 s^-1 of Ru/C. The measured rate is per litre of the 3.2 wt% catalyst (0.59 kg/L); with
    ru_wt_frac set, it is scaled at constant activity per kg of Ru (stated calibration, see README)."""
    p = KIN["Ru_C_Rossetti"]
    r = 2.0 * ru_n2_rate_per_litre_h(T, P_bar, yN, yH, yA) / p["catalyst_density_kg_L"] / 3600.0
    if ru_wt_frac is not None:
        r = r * ru_wt_frac / p["ru_wt_frac"]
    return r


RATE = {
    "Fe": rate_fe_dyson_simon,
    "Fe_wustite": rate_fe_wustite,
    "Fe_magnetite": rate_fe_magnetite,
    "Fe_Gramatica": rate_fe_gramatica,
    "Ru": rate_ru_rossetti,
}


def apparent_orders(rate, T, P_bar, yA, d=0.02, inerts=0.0, **kw):
    """d ln r / d ln p_i at fixed other partial pressures, H2/N2 = 3."""
    yN = (1 - yA - inerts) / 4.0
    yH = 3 * yN
    base = float(rate(T, P_bar, yN, yH, yA, **kw))
    out = {}
    for name in ("N2", "H2", "NH3"):
        y = [yN, yH, yA]
        i = ("N2", "H2", "NH3").index(name)
        y[i] *= 10 ** d
        out[name] = (math.log10(float(rate(T, P_bar, *y, **kw))) - math.log10(base)) / d
    return out


def equilibrium_y_nh3(T, P_bar, inerts=0.0, ratio=3.0, fugacity=True):
    """Equilibrium NH3 mole fraction for an H2/N2 = ratio feed without NH3 (fugacity-corrected)."""
    from scipy.optimize import brentq
    n0 = 1.0 - inerts
    yN0 = n0 / (1 + ratio)
    yH0 = n0 * ratio / (1 + ratio)

    def f(xi):
        tot = 1 - 2 * xi
        yN, yH, yA = (yN0 - xi) / tot, (yH0 - 3 * xi) / tot, 2 * xi / tot
        if fugacity:
            aN, aH, aA = activities(T, P_bar, yN, yH, yA)
        else:
            P = P_bar / BAR_PER_ATM
            aN, aH, aA = yN * P, yH * P, yA * P
        return math.log(aA / (aN ** 0.5 * aH ** 1.5)) - math.log(Ka(T))

    hi = min(yN0, yH0 / 3) * (1 - 1e-9)
    xi = brentq(f, 1e-12, hi, xtol=1e-14)
    return 2 * xi / (1 - 2 * xi)
