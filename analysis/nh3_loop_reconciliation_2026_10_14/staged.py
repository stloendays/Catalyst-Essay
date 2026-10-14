"""T4: simplified series-PFR (labelled) — three adiabatic beds with interbed cooling to one common inlet temperature,
inside the closed loop at 90 bar.

Rate laws: the vectorised functions of `analysis/nh3_staged_converter_2026_10_12/kinetics.py` per m³ of bed (fused Fe
KM1, Dyson–Simon; promoted 3.2 wt% Ru/C, Rossetti 2006, at the closed-loop 590 kg/m³) — identical to
`kinetic_bridge.rate_m3` (checked in test_reconciliation.py). Ideal-gas NIST Shomate enthalpies of the same file;
isobaric beds. Inverse design: feed and total NH3 extent are those of the closed-loop cold state (as #93); the converter
only decides how the extent is split over beds, the common inlet temperature and the catalyst in each bed.
Costs: `economics.evaluate` terms, with the inventory split between fused Fe and Ru/C volumes (pure designs reproduce
`economics.evaluate` exactly; tested).
"""
from __future__ import annotations

import math
from dataclasses import replace
from itertools import product

import numpy as np
from scipy.optimize import minimize

import common  # noqa: F401
import economics as E
import kinetic_bridge as KB
import kinetics as K

SPECIES = ("N2", "H2", "CH4", "Ar", "NH3")         # closed-loop order
NU = np.array([-0.5, -1.5, 0.0, 0.0, 1.0])          # per mol NH3 formed
TMAX_C = {"F": 530.0, "R": 460.0}                    # parameters.yaml: T_max_Fe_C, T_max_Ru_C
TMIN_C = 350.0                                       # parameters.yaml: T_min_C
PATTERNS = ("FFF", "FFR", "FRR", "RRR", "RFF", "RRF")
CLASS = {"FFF": "all-Fe", "RRR": "all-Ru/C", "FFR": "Fe-first", "FRR": "Fe-first", "RFF": "Ru/C-first", "RRF": "Ru/C-first"}
RHO = {"F": KB.DENSITY["Fe"], "R": KB.DENSITY["Ru"]}
NGL = 64
GL_X, GL_W = np.polynomial.legendre.leggauss(NGL)
COARSE_F = (0.2, 0.35, 0.5, 0.65, 0.8)
assert K.PAR["process"]["T_max_Fe_C"] == TMAX_C["F"] and K.PAR["process"]["T_max_Ru_C"] == TMAX_C["R"]
assert K.PAR["process"]["T_min_C"] == TMIN_C


def rate_m3(cat, T, P, n):
    """mol NH3 m^-3(bed) s^-1 for moles n (5 x m) at T (m), closed-loop formulation."""
    y = n / n.sum(axis=0)
    if cat == "F":
        return K.rate_fe_dyson_simon(T, P, y[0], y[1], y[4], per="m3")
    return K.rate_ru_rossetti(T, P, y[0], y[1], y[4]) * KB.DENSITY["Ru"]


COEF = np.array([K.SHOMATE[s] for s in SPECIES])            # 5 x 8 Shomate coefficients of kinetics.py
H0 = np.array([K.DHF[s] for s in SPECIES]) * 1000.0         # J/mol


def enthalpy(n, T):
    """Mixture enthalpy (J) of moles n (5 x m) at T (m): sum_i n_i kinetics.enthalpy(i, T), in matrix form."""
    c = COEF.T @ n
    t = np.asarray(T, dtype=float) / 1000.0
    return H0 @ n + 1000.0 * (c[0] * t + c[1] * t * t / 2 + c[2] * t ** 3 / 3 + c[3] * t ** 4 / 4 - c[4] / t + c[5] - c[7])


def heat_capacity(n, T):
    """Mixture heat capacity (J/K): sum_i n_i kinetics.cp(i, T)."""
    c = COEF.T @ n
    t = np.asarray(T, dtype=float) / 1000.0
    return c[0] + c[1] * t + c[2] * t * t + c[3] * t ** 3 + c[4] / (t * t)


def adiabatic_T(f, xi_a, T_in, xi):
    """Temperature (K) along an adiabatic bed entered at extent xi_a, T_in (K); f inlet mol/s (5,)."""
    n_in = (f + NU * xi_a)[:, None]
    T0 = np.array([float(T_in)])
    h_in = enthalpy(n_in, T0)[0]
    xi = np.atleast_1d(xi)
    n = f[:, None] + NU[:, None] * xi[None, :]
    dH = float(K.heat_of_reaction(T_in))                     # J per mol NH3, negative
    T = T_in - dH * (xi - xi_a) / heat_capacity(n_in, T0)[0]  # linear start, then Newton
    for _ in range(30):
        step = (enthalpy(n, T) - h_in) / heat_capacity(n, T)
        T = T - step
        if np.max(np.abs(step)) < 1e-8:
            break
    return T, n


def q_over_k(T, P, n):
    y = n / n.sum(axis=0)
    aN, aH, aA = K.activities(T, P, y[0], y[1], y[4])
    return aA / (K.Ka(T) * aN ** 0.5 * aH ** 1.5)


def bed(cat, f, P, xi_a, xi_b, T_in_K):
    """Volume (m3) of one adiabatic bed from extent xi_a to xi_b (mol NH3/s); None if infeasible."""
    if xi_b <= xi_a:
        return 0.0, T_in_K
    xs = 0.5 * (xi_b - xi_a) * (GL_X + 1.0) + xi_a
    T, n = adiabatic_T(f, xi_a, T_in_K, np.append(xs, xi_b))
    if T[-1] > TMAX_C[cat] + 273.15 + 1e-9 or T[-1] > 820.0:
        return None, T[-1]
    if q_over_k(T[-1:], P, n[:, -1:])[0] >= 1.0 - 1e-9:
        return None, T[-1]
    r = rate_m3(cat, T[:-1], P, n[:, :-1])
    if not np.all(np.isfinite(r)) or np.any(r <= 0):
        return None, T[-1]
    return 0.5 * (xi_b - xi_a) * float(np.dot(GL_W, 1.0 / r)), T[-1]


def design(pattern, f, P, xi_tot, x):
    """x = (T_in C, f1, f2): bed extents xi1 = f1 xi_tot, xi2 = xi1 + f2 (xi_tot - xi1), xi3 = xi_tot."""
    T_in, f1, f2 = float(x[0]), float(x[1]), float(x[2])
    if not (TMIN_C <= T_in <= min(TMAX_C[c] for c in pattern) - 1.0) or not (0 <= f1 <= 1 and 0 <= f2 <= 1):
        return None
    cuts = [0.0, f1 * xi_tot]
    cuts.append(cuts[1] + f2 * (xi_tot - cuts[1]))
    cuts.append(xi_tot)
    V = {"F": 0.0, "R": 0.0}
    beds = []
    for k, cat in enumerate(pattern):
        v, Tout = bed(cat, f, P, cuts[k], cuts[k + 1], T_in + 273.15)
        if v is None:
            return None
        V[cat] += v
        beds.append({"catalyst": "Fe" if cat == "F" else "Ru/C", "T_in_C": T_in, "T_out_C": float(Tout) - 273.15,
                     "volume_m3": v, "extent_fraction": (cuts[k + 1] - cuts[k]) / xi_tot})
    return {"V_Fe": V["F"], "V_Ru": V["R"], "V_tot": V["F"] + V["R"], "beds": beds}


# --- costs ------------------------------------------------------------------------------------------------------

def loop_terms(record, P, T_in, e):
    """Converter-independent decision-cost terms of a cold state (economics.evaluate with a 1 m3 Fe dummy bed)."""
    rec = dict(record)
    rec["isothermal_reaction_heat_removed_MW"] = -rec["extent_kmol_h"] / 3.6 * KB.hot_heat_per_mol_NH3(T_in + 273.15) / 1e6
    c = E.evaluate("Fe", 1.0, P, rec, e)
    return {"excess_feed": c["excess_feed_USD_t"], "utilities": c["utility_USD_t"],
            "compressor_capital": c["compressor_annualized_USD_t"], "hot_duty": c["hot_duty_scenario_USD_t"],
            "loop": c["excess_feed_USD_t"] + c["utility_USD_t"] + c["compressor_annualized_USD_t"] + c["hot_duty_scenario_USD_t"]}


def unit_charges(e):
    """USD/t per m3 of fused-Fe bed and of Ru/C bed (economics.evaluate inventory formulas)."""
    annual = e.product_tpd * 365 * e.capacity_factor
    unrec = E.annual_inventory_factor(e.metal_rate, e.catalyst_life_y, e.project_y, 0.0)
    rec = E.annual_inventory_factor(e.metal_rate, e.catalyst_life_y, e.project_y, e.ru_recovery)
    a_fe = KB.DENSITY["Fe"] * e.Fe_USD_kg_catalyst * unrec / annual
    a_ru = (KB.DENSITY["Ru"] * KB.RU_WT * e.Ru_USD_kg_metal * rec + KB.DENSITY["Ru"] * e.Ru_fabrication_USD_kg_catalyst * unrec) / annual
    return a_fe, a_ru


def reactor_charge(V, P, e):
    annual = e.product_tpd * 365 * e.capacity_factor
    return E.vessel_cost(V, P) * E.crf(e.equipment_rate, e.project_y) / annual


def cost(d, loop, P, e, charges=None):
    a_fe, a_ru = charges or unit_charges(e)
    inv = a_fe * d["V_Fe"] + a_ru * d["V_Ru"]
    reac = reactor_charge(d["V_tot"], P, e)
    return loop["loop"] + inv + reac, inv, reac


def mixed_evaluate(V_Fe, V_Ru, P, record, T_in, e):
    """Reference implementation from economics.evaluate only (for tests): inventory of each catalyst from its own
    pure-catalyst evaluate call, all other terms from the evaluate call on the total volume."""
    rec = dict(record)
    rec["isothermal_reaction_heat_removed_MW"] = -rec["extent_kmol_h"] / 3.6 * KB.hot_heat_per_mol_NH3(T_in + 273.15) / 1e6
    tot = E.evaluate("Fe", V_Fe + V_Ru, P, rec, e)
    inv = (E.evaluate("Fe", V_Fe, P, rec, e)["inventory_USD_t"] if V_Fe > 0 else 0.0) + \
          (E.evaluate("Ru", V_Ru, P, rec, e)["inventory_USD_t"] if V_Ru > 0 else 0.0)
    return tot["decision_relevant_cost_USD_t"] - tot["inventory_USD_t"] + inv


# --- optimisation -----------------------------------------------------------------------------------------------

def optimise_state(state, pattern, econs, P=90.0):
    """For one cold state and pattern: coarse grid of volumes (rate independent), then Nelder–Mead per economics."""
    rec = state["record"]
    f = np.asarray(rec["feed_kmol_h"]) / 3.6
    xi_tot = rec["extent_kmol_h"] / 3.6
    tmax = min(TMAX_C[c] for c in pattern) - 1.0
    Ts = list(np.arange(TMIN_C, tmax, 10.0)) + [tmax]
    coarse = []
    for T_in, f1, f2 in product(Ts, COARSE_F, COARSE_F):
        d = design(pattern, f, P, xi_tot, (T_in, f1, f2))
        if d is not None and d["V_tot"] <= 90.0:
            coarse.append(((T_in, f1, f2), d))
    out = []
    if not coarse:
        return out
    for label, e in econs:
        loop = loop_terms(rec, P, 400.0, e)
        ch = unit_charges(e)
        x0, _ = min(coarse, key=lambda t: cost(t[1], loop, P, e, ch)[0])

        def fun(x):
            d = design(pattern, f, P, xi_tot, x)
            if d is None or d["V_tot"] > 90.0:
                return 1e6
            return cost(d, loop, P, e, ch)[0]
        res = minimize(fun, np.array(x0, dtype=float), method="Nelder-Mead",
                       options=dict(xatol=1e-4, fatol=1e-7, maxfev=600, initial_simplex=np.array(
                           [x0, (x0[0] + 8.0, x0[1], x0[2]), (x0[0], min(x0[1] + 0.1, 1.0), x0[2]),
                            (x0[0], x0[1], min(x0[2] + 0.1, 1.0))], dtype=float)))
        x = res.x if res.fun < fun(x0) else np.array(x0, dtype=float)
        d = design(pattern, f, P, xi_tot, x)
        total, inv, reac = cost(d, loop, P, e, ch)
        out.append({"econ": label, "state_id": state["state_id"], "pattern": pattern, "class": CLASS[pattern],
                    "X": state["X"], "T2_C": state["T2_C"], "purge": state["purge"],
                    "inlet_inerts_pct": rec["inlet_inerts_pct"], "inlet_NH3_pct": rec["inlet_NH3_pct"],
                    "T_in_C": float(x[0]), "f1": float(x[1]), "f2": float(x[2]),
                    "V_Fe": d["V_Fe"], "V_Ru": d["V_Ru"], "V_tot": d["V_tot"],
                    "Ru_volume_share": d["V_Ru"] / d["V_tot"] if d["V_tot"] > 0 else 0.0,
                    "decision_USD_t": total, "inventory": inv, "reactor": reac, **{k: loop[k] for k in loop if k != "loop"},
                    "beds": d["beds"]})
    return out


def envelope(library, loops, P, e):
    """Lower envelope of library designs at economics e: best per class (designs re-costed at e)."""
    ch = unit_charges(e)
    best = {}
    for d in library:
        lp = loops[d["state_id"]]
        total = cost(d, lp, P, e, ch)[0]
        c = d["class"]
        if c not in best or total < best[c][0]:
            best[c] = (total, d)
    return best
