"""Forward and inverse use of the latest converter model (converter.py, measured rate laws) at a plant's own converter.

forward : given the plant's inlet gas (P, flow, NH3, inerts) and each bed's inlet temperature and catalyst volume,
          integrate every adiabatic bed (plug flow) and return outlet NH3 and outlet temperature per bed.
inverse : given each bed's inlet and outlet temperature (adiabatic), the extent follows from the energy balance; the
          model's catalyst volume needed for that extent is returned (compare with the installed volume).

Only converter.py / kinetics.py functions are used (bed_integral, adiabatic_T, max_extent, catalyst_props); nothing is
re-implemented except the root search for the extent of a bed of given volume.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq

import nh3_model as M

C = M.C
NM3_PER_MOL = 0.022414            # Nm3/mol, the normal volume used in converter.py and harness_core
T_UNLIMITED = 2000.0              # K: no catalyst temperature limit in forward/inverse use (only equilibrium)


def inlet_moles(y_nh3, inerts, yN2=None, yH2=None):
    """Mole fractions per mole of converter inlet (N2, H2, NH3, inerts): as printed, or H2/N2 = 3 if not given."""
    if yN2 is not None and yH2 is not None:
        tot = yN2 + yH2 + y_nh3 + inerts
        return (yN2 / tot, yH2 / tot, y_nh3 / tot, inerts / tot)
    yN = (1.0 - y_nh3 - inerts) / 4.0
    return (yN, 3.0 * yN, y_nh3, inerts)


def _econ(fe_kinetics="Fe", fe_activity=1.0):
    return C.Econ(accounting="frozen", recovery=0.9555, fe_kinetics=fe_kinetics, fe_activity=fe_activity)


def _y_nh3(n0, xi):
    return (n0[2] + 2.0 * xi) / (1.0 - 2.0 * xi)


def forward(P_bar, inlet_Nm3_h, y_nh3_in, inerts, beds, fe_kinetics="Fe", fe_activity=1.0, ngrid=161, yN2=None,
            yH2=None):
    """beds: list of (catalyst 'Fe'|'Ru', T_in_C, V_m3). Returns per-bed outlet NH3 (mol%) and outlet T (C)."""
    econ = _econ(fe_kinetics, fe_activity)
    n0 = inlet_moles(y_nh3_in, inerts, yN2, yH2)
    F_in = inlet_Nm3_h / NM3_PER_MOL / 3600.0          # mol/s
    xi_a, out = 0.0, []
    for cat, T_in_C, V in beds:
        rate, rho = C.catalyst_props(cat, econ)
        T_in = T_in_C + 273.15
        emax = C.max_extent(P_bar, n0, xi_a, T_in, "adiabatic", T_UNLIMITED, ngrid=400) - xi_a
        target = V * rho

        def need(d):
            I, _ = C.bed_integral(rate, P_bar, n0, xi_a, xi_a + d, T_in, "adiabatic", ngrid)
            return (F_in * I if math.isfinite(I) else 1e30) - target

        hi = emax * (1 - 1e-7)
        if emax <= 0:
            d = 0.0
        elif need(hi) < 0:                               # bed volume exceeds what equilibrium allows: at equilibrium
            d = hi
        else:
            d = brentq(need, 1e-12, hi, xtol=1e-12, rtol=1e-10, maxiter=200)
        T_out = C.adiabatic_T(T_in, n0, xi_a, xi_a + d)
        xi_a += d
        out.append(dict(catalyst=cat, T_in_C=T_in_C, V_m3=V, T_out_C=float(T_out - 273.15),
                        y_NH3_out_molpct=100 * _y_nh3(n0, xi_a), approach_eq_extent_fraction=d / emax if emax > 0 else 1.0))
    return out


def inverse(P_bar, inlet_Nm3_h, y_nh3_in, inerts, beds, fe_kinetics="Fe", fe_activity=1.0, ngrid=161, yN2=None,
            yH2=None):
    """beds: list of (catalyst, T_in_C, T_out_C). Returns the model catalyst volume (m3) per bed and outlet NH3."""
    econ = _econ(fe_kinetics, fe_activity)
    n0 = inlet_moles(y_nh3_in, inerts, yN2, yH2)
    F_in = inlet_Nm3_h / NM3_PER_MOL / 3600.0
    xi_a, out = 0.0, []
    for cat, T_in_C, T_out_C in beds:
        rate, rho = C.catalyst_props(cat, econ)
        T_in, T_out = T_in_C + 273.15, T_out_C + 273.15
        stoich = min(n0[0] - xi_a, (n0[1] - 3 * xi_a) / 3.0)
        d = brentq(lambda x: C.adiabatic_T(T_in, n0, xi_a, xi_a + x) - T_out, 0.0, 0.999 * stoich, xtol=1e-12)
        I, _ = C.bed_integral(rate, P_bar, n0, xi_a, xi_a + d, T_in, "adiabatic", ngrid)
        V = F_in * I / rho if math.isfinite(I) else math.inf
        xi_a += d
        out.append(dict(catalyst=cat, T_in_C=T_in_C, T_out_C=T_out_C, V_model_m3=V,
                        y_NH3_out_molpct=100 * _y_nh3(n0, xi_a)))
    return out


def equilibrium_outlet_T_check(P_bar, y_nh3_in, inerts, T_in_C, T_out_C):
    """Is the stated adiabatic outlet reachable (below equilibrium)? Returns ln(Q/K) at the outlet (<0: reachable)."""
    n0 = inlet_moles(y_nh3_in, inerts)
    T_in, T_out = T_in_C + 273.15, T_out_C + 273.15
    stoich = min(n0[0], n0[1] / 3.0)
    d = brentq(lambda x: C.adiabatic_T(T_in, n0, 0.0, x) - T_out, 0.0, 0.999 * stoich, xtol=1e-12)
    return float(C.equilibrium_gap(np.array([T_out]), P_bar, C.moles(n0, [d]))[0])


def min_volume(P_bar, inlet_Nm3_h, y_nh3_in, y_nh3_out, inerts, n_beds=3, T_min_C=350.0, T_max_C=530.0, seed=1,
               maxiter=200, popsize=20, ngrid=81):
    """Minimum fused-Fe volume of n adiabatic beds with interbed cooling that takes the inlet gas (H2/N2 = 3) from
    y_nh3_in to y_nh3_out. Variables: bed inlet temperatures and the split of the total extent; every bed must stay
    below equilibrium and below T_max. Differential evolution, then Nelder-Mead."""
    from scipy.optimize import differential_evolution, minimize
    econ = _econ()
    rate, rho = C.catalyst_props("Fe", econ)
    n0 = inlet_moles(y_nh3_in, inerts)
    F_in = inlet_Nm3_h / NM3_PER_MOL / 3600.0
    xi_t = (y_nh3_out - y_nh3_in) / (2.0 * (1.0 + y_nh3_out))
    T_max = T_max_C + 273.15

    def split(s):
        w, rest = [], 1.0
        for k in range(n_beds - 1):
            w.append(rest * s[k])
            rest -= w[-1]
        return w + [rest]

    def volume(x, detail=False):
        Ts, s = x[:n_beds], x[n_beds:]
        xi_a, V, beds = 0.0, 0.0, []
        for T_in_C, w in zip(Ts, split(s)):
            d = xi_t * w
            T_in = T_in_C + 273.15
            T_out = C.adiabatic_T(T_in, n0, xi_a, xi_a + d)
            if T_out > T_max:
                return (1e6 + (T_out - T_max)) if not detail else None
            I, _ = C.bed_integral(rate, P_bar, n0, xi_a, xi_a + d, T_in, "adiabatic", ngrid)
            if not math.isfinite(I):
                return 1e7 if not detail else None
            V += F_in * I / rho
            beds.append(dict(T_in_C=T_in_C, T_out_C=T_out - 273.15, V_m3=F_in * I / rho,
                             y_NH3_out_molpct=100 * _y_nh3(n0, xi_a + d)))
            xi_a += d
        return V if not detail else dict(V_total_m3=V, beds=beds)

    bounds = [(T_min_C, T_max_C - 1.0)] * n_beds + [(0.02, 0.98)] * (n_beds - 1)
    res = differential_evolution(volume, bounds, seed=seed, maxiter=maxiter, popsize=popsize, tol=1e-10, polish=False,
                                 init="sobol")
    lo, hi = np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds])
    nm = minimize(lambda x: volume(np.clip(x, lo, hi)), res.x, method="Nelder-Mead",
                  options=dict(xatol=1e-6, fatol=1e-9, maxiter=4000, maxfev=4000, adaptive=True))
    x = np.clip(nm.x, lo, hi) if volume(np.clip(nm.x, lo, hi)) < res.fun else res.x
    return volume(x, detail=True)
