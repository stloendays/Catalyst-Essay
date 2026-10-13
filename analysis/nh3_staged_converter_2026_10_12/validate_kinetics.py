"""Validate the measured rate laws against data and statements of their source papers.

Outputs: validation_ru_rossetti2006.csv (every point of Rossetti et al. 2006, Table 2), validation_summary.json.
    python validate_kinetics.py
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

import kinetics as K

HERE = Path(__file__).resolve().parent
NM3 = 22.414  # L(STP)/mol, the normal volume used by Rossetti et al. 2006 (time factor definition, p. 4151)

# Rossetti et al. 2006, Table 1 (p. 4151) and Table 2 (p. 4153): test, P bar, H2/N2 q, T_ave C, Exp/Eq, NH3 vol% at
# GHSV 50,000 / 60,000 / 90,000 / 120,000 / 200,000 / 300,000 / 400,000 h^-1 (None = not determined).
GHSV = [50000, 60000, 90000, 120000, 200000, 300000, 400000]
ROSSETTI_T2 = [
    (1, 100, 1.5, 431.1, 0.80, [13.20, 12.62, 11.66, 10.05, 7.62, 4.87, 3.60]),
    (2, 100, 1.5, 366.9, 0.17, [3.55, 3.32, 2.62, 2.24, 1.48, 0.89, 0.60]),
    (3, 85, 1.5, 366.9, 0.16, [3.41, 3.08, 2.43, 2.00, 1.43, None, None]),
    (4, 85, 1.5, 431.2, 0.80, [11.82, 11.33, 9.53, 8.25, 5.46, 4.17, 3.30]),
    (7, 70, 3.0, 366.6, 0.10, [2.19, 1.91, 1.43, 1.14, 0.60, None, None]),
    (8, 70, 3.0, 430.7, 0.59, [8.21, 7.75, 6.78, 5.80, 4.15, 2.81, 2.24]),
    (10, 85, 3.0, 366.6, 0.10, [2.24, 2.00, 1.62, 1.28, 0.60, None, None]),
    (11, 85, 3.0, 430.7, 0.59, [9.45, 8.42, 6.94, 5.64, 4.16, 2.72, 2.10]),
    (13, 100, 3.0, 366.9, 0.12, [3.13, 2.90, 2.19, 1.62, 1.04, None, None]),
    (15, 100, 1.5, 431.7, 0.86, [14.16, 12.50, 11.13, 9.06, 6.91, 4.83, 3.90]),
    (16, 100, 3.0, 431.7, 0.69, [12.53, 10.00, 8.29, 6.99, 5.24, 3.42, 2.81]),
    (17, 70, 1.5, 431.7, 0.76, [9.49, 9.03, 7.82, 6.20, 4.83, 3.31, 2.85]),
    (18, 50, 1.5, 431.4, 0.85, [8.21, 7.34, 6.49, 5.12, 3.98, 3.18, 2.25]),
    (19, 100, 1.5, 400.9, 0.38, [7.28, 6.64, 5.16, 4.32, 3.51, 2.25, 1.88]),
    (20, 70, 1.5, 400.3, 0.42, [6.62, 5.66, 4.61, 4.11, 2.59, 1.88, 1.56]),
    (21, 50, 1.5, 400.2, 0.43, [5.33, 4.86, 4.10, 3.32, 2.48, 2.23, 2.09]),
    (22, 100, 1.5, 461.3, 1.00, [13.23, 13.17, 12.11, 11.28, 8.84, 6.95, 5.87]),
    (23, 70, 1.5, 461.2, 1.01, [10.07, 9.92, 9.35, 8.74, 7.04, 5.55, 4.57]),
    (24, 50, 1.5, 460.6, 1.09, [8.79, 7.72, 7.16, 6.56, 5.58, 4.29, 3.69]),
]


def comp_from_eta(eta, q):
    """Rossetti 2006 eqs 8-10: mole fractions at fractional conversion eta of the defective reactant."""
    beta = 1.0 if q == 3.0 else 0.5
    tot = 1 + q - 2 * eta * beta
    return (1 - eta * beta) / tot, (q - 3 * eta * beta) / tot, 2 * eta * beta / tot


def rossetti_outlet(T_C, P_bar, q, ghsv, factor=1.0):
    """Integrate deta/dtau = factor * eq 14 to tau = 22.414 / (GHSV x_reactif); return NH3 vol%."""
    T = T_C + 273.15
    x_react = 0.25 if q == 3.0 else 0.60
    lam = 1.0 if q == 3.0 else 3.0
    tau = NM3 / (ghsv * x_react)
    a = 2.0 if q == 3.0 else 2.5

    def rhs(_, y):
        eta = min(max(y[0], 1e-9), 0.999)
        return [factor * float(K.ru_n2_rate_per_litre_h(T, P_bar, *comp_from_eta(eta, q), lam=lam))]

    sol = solve_ivp(rhs, [0, tau], [1e-6], method="LSODA", rtol=1e-8, atol=1e-12)
    eta = sol.y[0, -1]
    return 100 * eta / (a - eta)


def pfr_outlet(rate, T_C, P_bar, ghsv, density_kg_L, q=3.0, per_volume=False):
    """Isothermal plug flow, stoichiometric N2/H2 feed without NH3: NH3 vol% at GHSV (per catalyst volume)."""
    T = T_C + 273.15
    yN0 = 1 / (1 + q)
    F_per_L = ghsv / NM3 / 3600.0  # mol inlet gas per s per litre of catalyst

    def rhs(_, y):  # y = moles NH3 formed per mol inlet; d/dV(L)
        xi = min(max(y[0], 1e-9), 0.999)
        tot = 1 - xi
        yN, yH, yA = (yN0 - xi / 2) / tot, (1 - yN0 - 1.5 * xi) / tot, xi / tot
        r = float(rate(T + 0.0, P_bar, yN, yH, yA))  # mol NH3 per kg (or per m3) per s
        r_L = r / 1000.0 if per_volume else r * density_kg_L
        return [r_L / F_per_L]

    sol = solve_ivp(rhs, [0, 1.0], [1e-7], method="LSODA", rtol=1e-8, atol=1e-12)
    xi = sol.y[0, -1]
    return 100 * xi / (1 - xi)


def main():
    out = {}
    # 1. Ru/C, Rossetti 2006 Table 2, both rate bases (N2 consumption, as fitted; and NH3 per reaction as in the
    #    Aspen implementation of Tripodi et al. 2018, which halves the NH3 rate)
    rows = []
    for test, P, q, T_C, ratio, vals in ROSSETTI_T2:
        y_eq = 100 * K.equilibrium_y_nh3(T_C + 273.15, P, ratio=q)
        for g, v in zip(GHSV, vals):
            if v is None:
                continue
            p1 = rossetti_outlet(T_C, P, q, g, 1.0)
            p05 = rossetti_outlet(T_C, P, q, g, 0.5)
            rows.append(dict(test=test, P_bar=P, H2_N2=q, T_C=T_C, GHSV_h=g, NH3_meas_pct=v,
                             NH3_model_pct=round(p1, 4), rel_err=round((p1 - v) / v, 4),
                             NH3_model_halfrate_pct=round(p05, 4), rel_err_halfrate=round((p05 - v) / v, 4),
                             NH3_eq_model_pct=round(y_eq, 3), exp_over_eq_paper=ratio))
    with (HERE / "validation_ru_rossetti2006.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    def stats(key, sub):
        e = np.array([r[key] for r in sub])
        return dict(n=len(e), mean_abs_rel_err=float(np.mean(np.abs(e))), median_abs_rel_err=float(np.median(np.abs(e))),
                    mean_rel_err=float(np.mean(e)), max_abs_rel_err=float(np.max(np.abs(e))),
                    share_within_10pct=float(np.mean(np.abs(e) <= 0.10)))

    q3 = [r for r in rows if r["H2_N2"] == 3.0]
    out["Ru_C_Rossetti2006_Table2"] = {
        "all_points_N2_basis": stats("rel_err", rows),
        "H2_N2_3_points_N2_basis": stats("rel_err", q3),
        "H2_N2_3_points_T_ge_400C": stats("rel_err", [r for r in q3 if r["T_C"] > 400]),
        "all_points_half_rate": stats("rel_err_halfrate", rows),
        "note": "N2 basis = deta/dtau of eq 14 is the N2 (H2 at q = 1.5) consumption rate, as fitted by the authors",
    }
    # equilibrium check: implied equilibrium of the paper (NH3 at 50,000 h^-1 divided by Exp/Eq) vs model
    eqc = []
    for test, P, q, T_C, ratio, vals in ROSSETTI_T2:
        implied = vals[0] / ratio
        model = 100 * K.equilibrium_y_nh3(T_C + 273.15, P, ratio=q)
        eqc.append(dict(test=test, implied_eq_pct=round(implied, 3), model_eq_pct=round(model, 3),
                        rel=round(model / implied - 1, 4)))
    out["equilibrium_vs_Rossetti_Exp_over_Eq"] = dict(
        mean_abs_rel=float(np.mean([abs(e["rel"]) for e in eqc])),
        near_equilibrium_tests_460C=[e for e in eqc if e["test"] in (22, 23, 24)])

    # 2. Rossetti 2006 p. 4153: Ru/C at 57 bar, 460 C, tau = 0.0010 h L/mol, H2/N2 = 3 gives 6.6 % NH3
    ghsv_tau = NM3 / (0.0010 * 0.25)
    ru57 = rossetti_outlet(460.0, 57.0, 3.0, ghsv_tau)
    out["Ru_C_Rossetti2006_Fig3_statement"] = dict(stated_pct=6.6, model_pct=ru57, rel_err=ru57 / 6.6 - 1,
                                                   conditions="57 bar, 460 C, tau 0.0010 h L/mol, H2/N2 3")

    # 3. Micropilot points (Tripodi et al. 2018 AAM p. 7, data of Pernicone et al. 2003 / Rossetti 2006):
    #    430 C, 100 bar, GHSV 30,000 h^-1: magnetite (H2/N2 3) ca. 8, wustite (3) ca. 12.5, Ru/C (1.5) ca. 15.5 vol%
    fe = {}
    fe["Fe_DysonSimon_KM1_vs_magnetite_8pct"] = pfr_outlet(
        lambda T, P, a, b, c: K.rate_fe_dyson_simon(T, P, a, b, c, per="m3"), 430, 100, 30000, None, per_volume=True)
    fe["Fe_magnetite_Tripodi_vs_8pct"] = pfr_outlet(K.rate_fe_magnetite, 430, 100, 30000,
                                                    K.KIN["Fe_magnetite_Tripodi"]["bulk_density_kg_m3"] / 1000)
    fe["Fe_wustite_Tripodi_vs_12p5pct"] = pfr_outlet(K.rate_fe_wustite, 430, 100, 30000,
                                                     K.KIN["Fe_wustite_Tripodi"]["bulk_density_kg_m3"] / 1000)
    fe["Fe_Gramatica_k20_85_vs_magnetite_8pct"] = pfr_outlet(K.rate_fe_gramatica, 430, 100, 30000, 2.85)
    ru15 = rossetti_outlet(430.0, 100.0, 1.5, 30000)
    measured = {"Fe_DysonSimon_KM1_vs_magnetite_8pct": 8.0, "Fe_magnetite_Tripodi_vs_8pct": 8.0,
                "Fe_wustite_Tripodi_vs_12p5pct": 12.5, "Fe_Gramatica_k20_85_vs_magnetite_8pct": 8.0}
    out["micropilot_430C_100bar_30000h"] = {k: dict(model_pct=v, measured_pct=measured[k], rel_err=v / measured[k] - 1)
                                            for k, v in fe.items()}
    out["micropilot_430C_100bar_30000h"]["Ru_C_H2N2_1p5_vs_15p5pct"] = dict(model_pct=ru15, measured_pct=15.5,
                                                                            rel_err=ru15 / 15.5 - 1)
    # 4. Rossetti 2006 p. 4153: Fe-magnetite at 100 bar, 460 C, tau 0.0010 h L/mol -> 6.6 %
    mag = pfr_outlet(K.rate_fe_magnetite, 460, 100, ghsv_tau, K.KIN["Fe_magnetite_Tripodi"]["bulk_density_kg_m3"] / 1000)
    out["Fe_magnetite_Rossetti2006_statement"] = dict(stated_pct=6.6, model_pct=mag, rel_err=mag / 6.6 - 1)

    # 5. Tripodi 2018 Table 1 Aspen coefficients = Gillespie-Beattie Ka^2 plus a Pa->atm conversion only
    Ts = np.linspace(620, 800, 7)
    lnPa = math.log(101325.0)
    chk = {}
    for name, (A, B, C, D), expo in (("Fe_Kfor", (-7.8, 9218, -5.42, 7.8e-4), 1.75), ("KM_Kfor", (-4.9, 9218, -5.42, 7.8e-4), 1.5)):
        aspen = A + B / Ts + C * np.log(Ts) + D * Ts
        gb = 2 * np.log(K.Ka(Ts)) - expo * lnPa
        chk[name] = float(np.max(np.abs(aspen - gb)))
    A, B, C, D = (-1.876, -4609, 2.69, 1.27e-4)
    chk["Ru_Krev"] = float(np.max(np.abs(A + B / Ts + C * np.log(Ts) + D * Ts - (-np.log(K.Ka(Ts)) + 0.375 * lnPa))))
    chk["Ru_Kfor_A_minus_0p625lnPa"] = -7.19 + 0.625 * lnPa
    chk["Ru_k0_426_vs_9.02e8_per_L_h"] = 9.02e8 / 1000 / 3600 / 0.59
    chk["KM_k0_1.72e8_vs_2x8.849e14_per_m3_h"] = 2 * 8.849e14 / 3600 / 2850
    out["Tripodi2018_Table1_consistency_max_abs_ln_dev"] = chk

    # 6. adiabatic temperature rise per 1 % NH3 (industrial 14-15 K, Gramatica & Pernicone 1991 p. 245)
    from converter import adiabatic_T
    rises = {}
    for P, yI in ((150.0, 0.08), (90.0, 0.08), (200.0, 0.12)):
        yA0 = 0.03
        yN0 = (1 - yA0 - yI) / 4
        T0 = 673.15
        xi = 0.04  # mol N2 per mol inlet
        T1 = adiabatic_T(T0, (yN0, 3 * yN0, yA0, yI), 0.0, xi)
        dyA = (yA0 + 2 * xi) / (1 - 2 * xi) - yA0
        rises[f"{P:.0f}bar_inerts{yI}"] = (T1 - T0) / (100 * dyA)
    out["adiabatic_rise_K_per_pct_NH3"] = rises

    # 7. apparent orders (90 bar, 2 % NH3, H2/N2 3) to set against the descriptor model of PR #64
    orders = {}
    for T_C in (400, 425):
        orders[f"Fe_DysonSimon_{T_C}C"] = K.apparent_orders(K.rate_fe_dyson_simon, T_C + 273.15, 90.0, 0.02)
        orders[f"Fe_wustite_{T_C}C"] = K.apparent_orders(K.rate_fe_wustite, T_C + 273.15, 90.0, 0.02)
        orders[f"Ru_C_Rossetti_{T_C}C"] = K.apparent_orders(K.rate_ru_rossetti, T_C + 273.15, 90.0, 0.02)
        orders[f"Ru_C_Rossetti_{T_C}C_12pctNH3"] = K.apparent_orders(K.rate_ru_rossetti, T_C + 273.15, 90.0, 0.12)
        orders[f"Fe_DysonSimon_{T_C}C_12pctNH3"] = K.apparent_orders(K.rate_fe_dyson_simon, T_C + 273.15, 90.0, 0.12)
    out["apparent_orders_90bar"] = orders
    ratios = {}
    for T_C in (400, 425):
        for yA in (0.02, 0.06, 0.10, 0.14):
            yN = (1 - yA) / 4
            fe_ = float(K.rate_fe_dyson_simon(T_C + 273.15, 90.0, yN, 3 * yN, yA))
            ru_ = float(K.rate_ru_rossetti(T_C + 273.15, 90.0, yN, 3 * yN, yA, ru_wt_frac=0.08))
            ratios[f"{T_C}C_yNH3_{yA}"] = dict(Fe_DS_mol_kg_s=fe_, Ru8_mol_kg_s=ru_, Ru_over_Fe_per_kg=ru_ / fe_,
                                                Ru_over_Fe_per_m3=ru_ * 490 / (fe_ * 2850))
    out["rate_ratio_90bar"] = ratios
    out["equilibrium_90bar_425C"] = dict(ideal=K.equilibrium_y_nh3(698.15, 90.0, fugacity=False),
                                         fugacity=K.equilibrium_y_nh3(698.15, 90.0, fugacity=True),
                                         PR64_GB_ideal=0.17642782294535503)
    (HERE / "validation_summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
