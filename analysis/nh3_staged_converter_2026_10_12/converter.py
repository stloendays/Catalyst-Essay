"""Staged ammonia converter (2-4 beds in series, fused Fe or Ru/C per bed) inside the NH3-FINAL-1.1 loop accounting.

Model
  * Converter inlet per mole: H2/N2 = 3, inerts y_I (half CH4, half Ar), NH3 from the recycle. With fresh syngas added
    after the separator (NH3-FINAL-1.1 convention) and the separator vapour at y_sep = p_sat(T_sep)/P, the recycle
    closure gives y_NH3,in = y_sep (1 - 4 xi), xi = mol N2 converted per mol converter inlet.
  * Each bed is plug flow, either adiabatic (inlet temperature chosen, indirect interbed exchange, ideal-gas NIST
    enthalpies) or isothermal (bed temperature chosen). Catalyst mass of a bed = F_in * int 2 dxi / r_NH3(xi, T(xi)).
    A bed's extent is set as a fraction f of the largest extent it can reach (adiabatic: equilibrium or the
    catalyst's maximum temperature, whichever comes first; isothermal: equilibrium), so every design is feasible.
  * Costs per tonne NH3 use the NH3-FINAL-1.1 functions (harness_core.py): converter vessel cost proxy on the total
    bed volume plus the Turton pressure premium, fresh and recycle compression electricity and bare-module CAPEX,
    refrigeration of the product. Catalysts are priced by mass: fused Fe per kg, Ru/C as Ru metal (with recovery)
    plus a non-recoverable support charge, either with the frozen straight-line replacement charge or the 25-year
    discounted cash flow of analysis/nh3_ru_net_recovery_boundary_2026_10_12/lifecycle_cashflow.py.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

import kinetics as K

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "provenance" / "discover_v1" / "source_harness"))
sys.path.insert(0, str(REPO / "analysis" / "nh3_ru_net_recovery_boundary_2026_10_12"))
from harness_core import MW_NH3_KG_MOL, NH3Harness  # noqa: E402
from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier  # noqa: E402

MANIFEST = REPO / "provenance" / "discover_v1" / "source_harness" / "outputs" / "nh3_final_20260905T134204Z" / "manifest_resolved.yaml"
CFG = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
H = NH3Harness.__new__(NH3Harness)   # economic constants and cost functions only; no process library is built
H.cfg = CFG
H._init_controls()

PAR = K.PAR
R_J = K.R_J
SPECIES = ("N2", "H2", "NH3", "CH4", "Ar")
NU = np.array([-1.0, -3.0, 2.0, 0.0, 0.0])          # per unit extent (mol N2 converted)
COEF = np.array([K.SHOMATE[s] for s in SPECIES])     # 5 x 8 Shomate coefficients
H0 = np.array([K.DHF[s] for s in SPECIES]) * 1000.0
F_MAX = 0.995                                        # largest fraction of the attainable extent a bed may use


# --- thermodynamics of the reacting gas --------------------------------------------------------------------------


def moles(n0, xi):
    """n0 = (N2, H2, NH3, I) per mole inlet; xi (array) -> (5, len) moles of N2, H2, NH3, CH4, Ar."""
    N2, H2, A, I = n0
    xi = np.atleast_1d(np.asarray(xi, dtype=float))
    base = np.array([N2, H2, A, I / 2, I / 2])
    return base[:, None] + NU[:, None] * xi[None, :]


def _h_cp(n, T):
    """Mixture enthalpy (J) and heat capacity (J/K) for moles n (5 x G) at T (G)."""
    c = COEF.T @ n                                   # 8 x G
    t = T / 1000.0
    h = H0 @ n + 1000.0 * (c[0] * t + c[1] * t * t / 2 + c[2] * t ** 3 / 3 + c[3] * t ** 4 / 4 - c[4] / t + c[5] - c[7])
    cpm = c[0] + c[1] * t + c[2] * t * t + c[3] * t ** 3 + c[4] / (t * t)
    return h, cpm


def adiabatic_T(T_in, n0, xi_in, xi):
    """Temperature after an adiabatic advance from extent xi_in at T_in to extent(s) xi (enthalpy conserved)."""
    scalar = np.ndim(xi) == 0
    xi = np.atleast_1d(np.asarray(xi, dtype=float))
    h_in, _ = _h_cp(moles(n0, [xi_in]), np.array([float(T_in)]))
    n = moles(n0, xi)
    dH = -float(K.heat_of_reaction(T_in)) * 2.0     # J per unit extent (2 NH3)
    _, cp_in = _h_cp(moles(n0, [xi_in]), np.array([float(T_in)]))
    T = T_in + dH * (xi - xi_in) / cp_in[0]
    for _ in range(8):
        h, cpm = _h_cp(n, T)
        step = (h - h_in[0]) / cpm
        T = T - step
        if np.max(np.abs(step)) < 1e-6:
            break
    return float(T[0]) if scalar else T


def equilibrium_gap(T, P, n):
    """ln Q - ln Ka (negative before equilibrium) for moles n (5 x G) at T (G)."""
    tot = n.sum(axis=0)
    aN, aH, aA = K.activities(T, P, n[0] / tot, n[1] / tot, n[2] / tot)
    return np.log(aA) - 0.5 * np.log(aN) - 1.5 * np.log(aH) - np.log(K.Ka(T))


def max_extent(P, n0, xi_a, T_in, mode, T_max, ngrid=48):
    """Largest extent a bed starting at (xi_a, T_in) can reach: equilibrium or, adiabatic, T = T_max."""
    stoich = min(n0[0], n0[1] / 3.0) * 0.999
    hi = stoich
    if mode == "adiabatic":
        if T_in >= T_max:
            return xi_a
        _, cp_in = _h_cp(moles(n0, [xi_a]), np.array([float(T_in)]))
        dH = -float(K.heat_of_reaction(T_in)) * 2.0
        hi = min(hi, xi_a + 1.5 * (T_max - T_in) * cp_in[0] / dH)
    xs = np.linspace(xi_a, hi, ngrid)
    T = adiabatic_T(T_in, n0, xi_a, xs) if mode == "adiabatic" else np.full_like(xs, T_in)
    crit = np.maximum(equilibrium_gap(T, P, moles(n0, xs)), (T - T_max) / 50.0)
    lim = np.where(crit >= 0)[0]
    if lim.size == 0:
        return hi
    j = lim[0]
    if j == 0:
        return xi_a
    c0, c1 = crit[j - 1], crit[j]                    # linear interpolation of the first crossing
    return xs[j - 1] + (xs[j] - xs[j - 1]) * (-c0) / (c1 - c0)


# --- loop -------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Loop:
    P_bar: float
    Tsep_C: float = -20.0
    inerts: float = 0.08
    production_tpd: float = 1000.0

    @property
    def ysep(self):
        return H.psat_nh3_bar(self.Tsep_C) / self.P_bar

    @property
    def nh3_mol_s(self):
        return self.production_tpd * 1000.0 / MW_NH3_KG_MOL / 86400.0

    def inlet(self, xi_total):
        yA = self.ysep * (1.0 - 4.0 * xi_total)
        yN = (1.0 - yA - self.inerts) / 4.0
        return (yN, 3.0 * yN, yA, self.inerts)

    def process_costs(self, xi_total):
        """USD/t NH3 of compression (energy + CAPEX) and refrigeration, NH3-FINAL-1.1 formulas."""
        P = self.P_bar
        n_per_t = H.n_per_t
        recycle_total = 1.0 / (2.0 * xi_total) - 2.0           # mol recycle gas per mol NH3
        fresh = 0.0 if P <= H.FRESH_FEED_PRESSURE_BAR else (
            2.0 * n_per_t * R_J * 298.15 * math.log(P / H.FRESH_FEED_PRESSURE_BAR) / H.COMPRESSOR_ETA / 3.6e9 * H.ELECTRICITY)
        recycle = n_per_t * recycle_total * R_J * 298.15 * math.log(P / (P - H.DP_RECYCLE_BAR)) / H.COMPRESSOR_ETA / 3.6e9 * H.ELECTRICITY
        refrig = H.refriger_cost(self.Tsep_C)
        capex = H.compressor_capex_USD_t(fresh) + H.compressor_capex_USD_t(recycle)
        return dict(fresh_comp=fresh, recycle_comp=recycle, refrigeration=refrig, compressor_capex=capex,
                    recycle_mol_per_mol=recycle_total)


def reactor_cost(V, P):
    """NH3-FINAL-1.1 converter cost proxy + Turton pressure premium on the total bed volume (USD/t)."""
    base = (H.REACTOR_FIXED + H.REACTOR_VAR * (V / H.REACTOR_REF) ** H.REACTOR_EXP) * H.crf / H.annual_output_t
    Vd = max(V, H.PC_V_AMIN)
    D = (4.0 * Vd / (math.pi * H.PC_V_LD)) ** (1 / 3)
    t = P * D / (2.0 * (H.PC_V_SE - 0.6 * P)) + H.PC_V_CA
    cp0 = float(H.turton_cp0(H.PC_VK, Vd, H.PC_V_AMIN, H.PC_V_AMAX, H.PC_V_NEXP))
    prem = cp0 * H.PC_V_B2 * H.PC_V_FM * (max(t / H.PC_V_TMIN, 1.0) - 1.0) * H.PC_INDEX_RATIO * H.crf / H.annual_output_t
    return base + prem


# --- catalysts and economics -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Econ:
    p_Fe: float = PAR["economics"]["Fe_catalyst_USD_kg"]
    p_Ru: float = PAR["economics"]["Ru_USD_kg"]
    w_Ru: float = PAR["economics"]["Ru_wt_frac_commercial"]
    rho_Ru: float = PAR["economics"]["Ru_C_bed_density_kg_m3"]
    p_support: float = PAR["economics"]["Ru_C_support_USD_kg"]
    recovery: float = 0.9555
    fin_rate: float = 0.0
    accounting: str = "frozen"            # 'frozen' straight-line (1 - r)/L, or 'dcf' 25-year cash flow
    life_y: float = PAR["economics"]["catalyst_life_y"]
    fe_kinetics: str = "Fe"               # key of kinetics.RATE
    fe_activity: float = 1.0              # sensitivity multipliers (effectiveness factors); 1 = intrinsic
    ru_activity: float = 1.0
    ru_scale_with_loading: bool = True    # rate per kg Ru as measured (True) or rate per kg catalyst as measured
    c_Ru: float | None = None             # override: USD per kg Ru metal per year (decision-boundary library)
    c_Fe: float | None = None             # override: USD per kg fused Fe per year (support charged pro rata)

    def multiplier(self, recovery):
        if self.accounting == "frozen":
            return 1.0 - recovery
        case = MetalCashflow(project_y=float(H.PLANT_LIFE_Y), catalyst_life_y=self.life_y,
                             discount_rate=self.fin_rate, gross_recovery=recovery)
        return annualized_metal_multiplier(case, 1.0, legacy_life_y=self.life_y)

    def ru_cost_per_kg_ru_year(self):
        if self.c_Ru is not None:
            return self.c_Ru
        return self.p_Ru * self.multiplier(self.recovery) / self.life_y

    def fe_cost_per_kg_year(self):
        if self.c_Fe is not None:
            return self.c_Fe
        return self.p_Fe * self.multiplier(0.0) / self.life_y

    def support_cost_per_kg_year(self):
        if self.c_Fe is not None:
            return self.c_Fe * self.p_support / self.p_Fe
        return self.p_support * self.multiplier(0.0) / self.life_y

    def ru_cat_cost_per_kg_year(self):
        return self.w_Ru * self.ru_cost_per_kg_ru_year() + self.support_cost_per_kg_year()


def catalyst_props(cat, econ):
    """(rate function of (T, P, yN, yH, yA) -> mol NH3 per kg per s, bed density kg/m3)."""
    if cat == "Ru":
        w = econ.w_Ru if econ.ru_scale_with_loading else None
        act = econ.ru_activity

        def f(T, P, a, b, c):
            return act * K.rate_ru_rossetti(T, P, a, b, c, ru_wt_frac=w)
        return f, econ.rho_Ru
    key = econ.fe_kinetics
    rho = {"Fe": K.KIN["Fe_DysonSimon"]["bulk_density_kg_m3"],
           "Fe_wustite": K.KIN["Fe_wustite_Tripodi"]["bulk_density_kg_m3"],
           "Fe_magnetite": K.KIN["Fe_magnetite_Tripodi"]["bulk_density_kg_m3"],
           "Fe_Gramatica": 2850.0}[key]
    rate = K.RATE[key]
    act = econ.fe_activity

    def g(T, P, a, b, c):
        return act * rate(T, P, a, b, c)
    return g, rho


# --- converter evaluation ----------------------------------------------------------------------------------------


def _quad(ngrid):
    s = np.linspace(0.0, 1.0, ngrid)
    w = np.ones(ngrid)
    w[1:-1:2] = 4.0
    w[2:-1:2] = 2.0
    w /= 3.0 * (ngrid - 1)
    return 1.0 - (1.0 - s) ** 2, 2.0 * (1.0 - s), w        # grid graded towards the bed outlet


QUAD = {n: _quad(n) for n in (41, 81, 161, 641)}


def bed_integral(rate, P, n0, xi_a, xi_b, T_in, mode, ngrid=41):
    """int 2/r dxi over the bed (kg s per mol inlet) and its temperature profile."""
    if xi_b <= xi_a:
        return 0.0, np.array([T_in, T_in])
    grid, dgrid, wts = QUAD[ngrid]
    xi = xi_a + (xi_b - xi_a) * grid
    T = adiabatic_T(T_in, n0, xi_a, xi) if mode == "adiabatic" else np.full_like(xi, T_in)
    n = moles(n0, xi)
    tot = n.sum(axis=0)
    r = rate(T, P, n[0] / tot, n[1] / tot, n[2] / tot)
    if np.any(~np.isfinite(r)) or np.any(r <= 0):
        return math.inf, T
    return float(np.sum(wts * dgrid * 2.0 / r) * (xi_b - xi_a)), T


def T_limits(pattern, T_max_Ru=None):
    proc = PAR["process"]
    tmax = {"Fe": proc["T_max_Fe_C"], "Ru": T_max_Ru or proc["T_max_Ru_C"]}
    return [tmax[c] + 273.15 for c in pattern]


def extents(x, pattern, loop, mode, T_max_Ru=None):
    """Bed extents from x = [T_1..T_N (C), f_1..f_N].

    The attainable extent of each bed is computed for the reference inlet that carries the most NH3 the recycle can
    bring (y_NH3,in = y_sep). The actual inlet (y_sep (1 - 4 xi_total)) carries less NH3, so every bed of the design is
    further from equilibrium than in the reference and the design stays feasible; the adiabatic outlet temperature
    differs from the reference by less than 0.1 K (reported per bed)."""
    nb = len(pattern)
    Ts = np.asarray(x[:nb], dtype=float) + 273.15
    fs = np.clip(np.asarray(x[nb:2 * nb], dtype=float), 0.0, F_MAX)
    Tmax = T_limits(pattern, T_max_Ru)
    n_ref = loop.inlet(0.0)
    dxi, xi_a = [], 0.0
    for k in range(nb):
        if fs[k] <= 0.0:
            dxi.append(0.0)
            continue
        emax = max_extent(loop.P_bar, n_ref, xi_a, Ts[k], mode, Tmax[k]) - xi_a
        d = fs[k] * max(emax, 0.0)
        dxi.append(d)
        xi_a += d
    xi_tot = max(xi_a, 1e-9)
    return Ts, np.array(dxi), xi_tot, loop.inlet(xi_tot)


def evaluate(x, pattern, loop, econ, mode="adiabatic", T_max_Ru=None, detail=False, ngrid=41):
    """Total catalyst-dependent NH3 cost (USD/t) of design x = [T_1..T_N (C), f_1..f_N]."""
    Ts, dxi, xi_tot, n0 = extents(x, pattern, loop, mode, T_max_Ru)
    if xi_tot < 1e-4:
        return (math.inf, None) if detail else math.inf
    F_in = loop.nh3_mol_s / (2.0 * xi_tot)
    masses, vols, profiles, xi_a = [], [], [], 0.0
    for k, cat in enumerate(pattern):
        rate, rho = catalyst_props(cat, econ)
        I, T = bed_integral(rate, loop.P_bar, n0, xi_a, xi_a + dxi[k], Ts[k], mode, ngrid)
        if not math.isfinite(I):
            return (math.inf, None) if detail else math.inf
        masses.append(F_in * I)
        vols.append(F_in * I / rho)
        profiles.append(T)
        xi_a += dxi[k]
    V = float(sum(vols))
    m_fe = sum(m for m, c in zip(masses, pattern) if c == "Fe")
    m_ru = sum(m for m, c in zip(masses, pattern) if c == "Ru")
    cat_fe = m_fe * econ.fe_cost_per_kg_year() / H.annual_output_t
    cat_ru = m_ru * econ.ru_cat_cost_per_kg_year() / H.annual_output_t
    reac = reactor_cost(V, loop.P_bar)
    pc = loop.process_costs(xi_tot)
    total = cat_fe + cat_ru + reac + pc["fresh_comp"] + pc["recycle_comp"] + pc["refrigeration"] + pc["compressor_capex"]
    feasible = V <= H.V_CAP
    if not detail:
        return total if feasible else 1e3 + V
    v_ru = sum(v for v, c in zip(vols, pattern) if c == "Ru")
    tot_out = 1 - 2 * xi_tot
    return total, dict(
        total=total, feasible_V_cap=feasible, catalyst_Fe=cat_fe, catalyst_Ru=cat_ru, reactor=reac,
        **{k: v for k, v in pc.items()},
        V_m3=V, V_Ru_m3=v_ru, Ru_volume_fraction=v_ru / V if V > 0 else 0.0, mass_Fe_kg=m_fe, mass_Ru_cat_kg=m_ru,
        Ru_metal_kg=m_ru * econ.w_Ru, xi_total=xi_tot, y_NH3_in=n0[2], y_NH3_out=(n0[2] + 2 * xi_tot) / tot_out,
        X_N2_per_pass=xi_tot / n0[0], inlet_Nm3_h=F_in * 0.022414 * 3600.0,
        beds=[dict(catalyst=c, T_in_C=float(t[0] - 273.15), T_out_C=float(t[-1] - 273.15), mass_kg=m, volume_m3=v,
                   dxi=float(d), y_NH3_out=float((n0[2] + 2 * xo) / (1 - 2 * xo)))
              for c, t, m, v, d, xo in zip(pattern, profiles, masses, vols, dxi, np.cumsum(dxi))])


# --- optimisation ------------------------------------------------------------------------------------------------


def bounds(pattern, mode, T_max_Ru=None):
    proc = PAR["process"]
    tb = [(proc["T_min_C"], t - 273.15 - (1.0 if mode == "adiabatic" else 0.0)) for t in T_limits(pattern, T_max_Ru)]
    return tb + [(0.0, F_MAX) for _ in pattern]


def optimize(pattern, loop, econ, mode="adiabatic", T_max_Ru=None, seed=1, x0=None, de=True, maxiter=150,
             popsize=12, restarts=(), nm_maxfev=2000):
    """Global (differential evolution) then local (Nelder-Mead) minimisation of the cost."""
    from scipy.optimize import differential_evolution, minimize
    b = bounds(pattern, mode, T_max_Ru)
    lo = np.array([u for u, _ in b])
    hi = np.array([v for _, v in b])

    def f(x):
        v = evaluate(np.clip(x, lo, hi), pattern, loop, econ, mode, T_max_Ru)
        return v if math.isfinite(v) else 1e6

    starts = []
    if de:
        res = differential_evolution(f, b, seed=seed, maxiter=maxiter, popsize=popsize, tol=1e-9, mutation=(0.5, 1.0),
                                     recombination=0.7, polish=False, init="sobol", x0=x0)
        starts.append(res.x)
    elif x0 is not None:
        starts.append(np.asarray(x0, dtype=float))
    starts += [np.asarray(s, dtype=float) for s in restarts]

    def nm(x, maxfev):
        res = minimize(f, x, method="Nelder-Mead",
                       options=dict(xatol=1e-5, fatol=1e-7, maxiter=maxfev, maxfev=maxfev, adaptive=True))
        nxt = np.clip(res.x, lo, hi)
        return (nxt, f(nxt)) if f(nxt) < f(x) else (x, f(x))

    best, fbest = None, math.inf
    for s in starts:                                  # short local search from every start
        cur, fc = nm(np.clip(s, lo, hi), nm_maxfev)
        if fc < fbest:
            best, fbest = cur, fc
    for _ in range(2):                                # restart the best (Nelder-Mead stalls on bounds)
        cur, fc = nm(best, nm_maxfev)
        if fc >= fbest - 1e-9:
            break
        best, fbest = cur, fc
    val, det = evaluate(best, pattern, loop, econ, mode, T_max_Ru, detail=True)
    return dict(x=[float(v) for v in best], cost=val, detail=det)
