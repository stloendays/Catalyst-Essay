"""Fused-iron NH3 rate law of Keestra et al. (2025), Model 3, on the thermodynamic basis of the staged-converter code.

Source: H. Keestra, Y. Slotboom, K. H. R. Rouwenhorst, D. W. F. Brilman, "A century of data: Thermodynamics and kinetics
for ammonia synthesis on various commercial iron-based catalysts", Chem. Eng. J. 518 (2025) 164593,
doi:10.1016/j.cej.2025.164593 (CC BY). Supplementary Information (publisher file
1-s2.0-S1385894725054294-mmc1.pdf, SHA-256 b43f9988b4b5f69d824409e706c1c1b8862afb523a2b18cb053f7c286465773a):

  Table 2, Model 3:  r_NH3 = b_cat k f_N2 (1 - f_NH3^2 / (K_f^2 f_N2 f_H2^3)) (1 + f_NH3 / (K_N f_H2^1.5) + sqrt(K_H f_H2))^-2
  Table 8 (original Arrhenius form X = A exp(-B / R T)):
      k_NH3   A 2.215e13 mol kg^-1 s^-1 bar^-1, B 1.007e5 J/mol
      K_N     A 2.455e-8 bar^-0.5,               B -1.795e4 J/mol
      sqrt K_H A 3.276e2 bar^-0.5,               B -4.948e3 J/mol      (units as in SI Table 24)
  Table 9, relative catalytic activity b_cat (Model 3): Topsoe KM1R (1964) 0.350 (Nielsen, Kjaer & Hansen 1964, the data
      Dyson & Simon fitted), Topsoe KM1R (1999) 0.905, Clariant AmoMax 10 (2024) 1.00
  SI A-5-1 code, K_eq: K_f = 1.3627949655792108e-6 exp(51111.189247481634 / (R T)), bar^-1, R = 8.31446261815324
  Rate in mol NH3 per kg catalyst per s; fugacities in bar (SI A-7-2: "the units used in this study were mol kg^-1 s^-1").

Fugacities here are the Newton-Cooper ones of the staged-converter kinetics (kinetics.activities, atm) converted to bar,
the same basis the Dyson-Simon and Rossetti laws use in the cost model. The source uses its own K_f; eq="GB" swaps in the
Gillespie-Beattie constant of the loop states (sensitivity).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nh3_staged_converter_2026_10_12"))
import kinetics as K  # noqa: E402

R = 8.31446261815324
BAR_PER_ATM = 1.01325
PAR = dict(kA=2.215e13, kB=1.007e5, NA=2.455e-8, NB=-1.795e4, HA=3.276e2, HB=-4.948e3)
BCAT = {"KM1R_1964": 0.350, "KM1R_1999": 0.905, "AmoMax10_2024": 1.00}
BCAT_CI95 = {"KM1R_1964": 7.95e-3, "KM1R_1999": 4.05e-2, "AmoMax10_2024": 4.02e-2}
BED_DENSITY = 2500.0          # kg m^-3, fused-iron bed of the NH3 harness (and Keestra's Fe example, SI Table 19)


def Kf_source(T):
    return 1.3627949655792108e-6 * np.exp(51111.189247481634 / (R * np.asarray(T, dtype=float)))


def Kf_GB(T):
    return K.Ka(T) / BAR_PER_ATM


def rate(T, P_bar, yN, yH, yA, catalyst="KM1R_1964", eq="source", per="kg"):
    """mol NH3 kg^-1 s^-1 (per='kg') or m^-3 s^-1 of bed (per='m3', 2500 kg m^-3)."""
    T = np.asarray(T, dtype=float)
    aN, aH, aA = K.activities(T, P_bar, yN, yH, yA)            # fugacities, atm
    fN, fH, fA = aN * BAR_PER_ATM, aH * BAR_PER_ATM, aA * BAR_PER_ATM
    Kf = Kf_source(T) if eq == "source" else Kf_GB(T)
    k = PAR["kA"] * np.exp(-PAR["kB"] / (R * T))
    KN = PAR["NA"] * np.exp(-PAR["NB"] / (R * T))
    sKH = PAR["HA"] * np.exp(-PAR["HB"] / (R * T))
    r = BCAT[catalyst] * k * fN * (1.0 - fA * fA / (Kf * Kf * fN * fH ** 3)) / (1.0 + fA / (KN * fH ** 1.5) + sKH * np.sqrt(fH)) ** 2
    return r * BED_DENSITY if per == "m3" else r
