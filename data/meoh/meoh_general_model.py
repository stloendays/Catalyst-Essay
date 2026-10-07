"""Methanol recycle-economics model generalized to arbitrary CO2-hydrogenation catalysts.

Built on `meoh_d01_model.py` (the faithful port of the workbook generator), whose constants, process anchor
(Processes 2022, 10, 1535) and cost structure are imported unchanged. What is generalized:

* per-catalyst inputs: single-pass CO2 conversion X; carbon selectivities S_MeOH, S_CO, S_CH4 (closure enforced);
  reaction temperature T and pressure P; reactor-inlet H2/CO2 ratio; productivity either per g active metal
  (STY_per_g_metal with metal_wt) or per g catalyst (STY_per_g_cat); optional catalyst price (EUR/kg) and
  lifetime (y) for a catalyst-replacement term (default off, so the canonical objective is unchanged);
* compression of fresh CO2 (1 bar), fresh H2 (30 bar) and recycle (P - 1.5 bar) to the stated P (an entry with
  P below the H2 delivery pressure needs no H2 compression);
* CO recycle. The engine treats CO like CH4: it accumulates in the loop and leaves only through the purge. Here CO
  in the recycle is converted with a per-pass fractional conversion x_CO by the net reaction CO + 2 H2 -> CH3OH.
  (The water-gas-shift route CO + H2O -> CO2 + H2 followed by CO2 + 3 H2 -> CH3OH + H2O has the same net
  stoichiometry, so H2 demand and water make are identical whichever route the catalyst uses.) The loop balance is
  linear in the unknown reactor-inlet CO2 flow and is solved exactly; x_CO = 0 reproduces the engine bit for bit.

x_CO rules (`x_co=` accepts a number or one of these names):

* "inert"             x_CO = 0: the engine behaviour (CO leaves only with the purge); lower limit of the range,
                      a catalyst with no water-gas-shift or CO-hydrogenation activity;
* "recycled_central"  x_CO = min(x_RWGS, x_MeOH). x_RWGS is the smallest per-pass CO conversion for which the
                      reactor outlet does not exceed reverse-water-gas-shift equilibrium (Q_RWGS <= K_RWGS); 0 when
                      the inert loop already satisfies it. CO above that level is shifted back by any catalyst with
                      WGS activity. This is how CO behaves in the anchor's own loop: its kinetic model forms and
                      consumes CO only through (R)WGS, its reactor outlet sits at RWGS equilibrium (Q/K = 1.02 from
                      the published outlet composition) and the rule reproduces its loop CO level. x_MeOH is the
                      largest per-pass CO conversion permitted by CO + 2 H2 <-> CH3OH equilibrium at the outlet
                      (capped at 1); recycled CO is never converted to methanol beyond it. When x_RWGS > x_MeOH no
                      CO conversion satisfies both equilibria: x_CO = x_MeOH and the outlet is above
                      CO2-hydrogenation equilibrium (`equilibrium_feasible` False);
* "recycled_high"     x_CO = x_MeOH: upper limit of the range;
* "recycled_equal_X"  x_CO = X clipped into [x_central, x_MeOH]: recycled CO converted by the same fraction per pass
                      as CO2 (sensitivity).

Feasibility. `economics` (with T_C) returns `equilibrium_feasible`: the reactor outlet does not exceed
CO2-hydrogenation (methanol) equilibrium, Q_CO2hyd / K_CO2hyd <= 1 + EQ_TOL. A loop state above it would make
methanol beyond equilibrium and cannot be built. `optimal_purge` minimises the cost over the purge levels that are
equilibrium feasible and whose non-H2/CO2 (nonreactive) fraction at the reactor inlet is within the workbook's own
limit (`meoh_d01_model.SOURCE_NONREACTIVE_REFERENCE`, the `purge_diagnostic` of the generator); a candidate with no
such level is infeasible.

Equilibrium constants are those of the process anchor's kinetic model (Processes 2022, 10, 1535, Table 1;
K_CO2hyd in bar^-2, K_RWGS dimensionless, K_COhyd = K_CO2hyd / K_RWGS). Activities are fugacities of the
reactor-outlet gas (methanol and water still in the gas) at the stated T and P from the Peng-Robinson equation of
state, as in the anchor (k_ij = 0; effective H2 acentric factor -0.05 as used there); `FUGACITY = "ideal"` switches
to ideal-gas mole fractions.

All functions accept numpy arrays for catalyst inputs, purge, T and P (broadcastable).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meoh_d01_model as M  # noqa: E402

X_CO_RULES = ("inert", "recycled_central", "recycled_high", "recycled_equal_X")
EQ_TOL = 1e-6            # relative tolerance on Q/K for the CO2-hydrogenation equilibrium check
NONREACTIVE_MAX = M.SOURCE_NONREACTIVE_REFERENCE   # workbook purge_diagnostic limit on the inlet non-H2/CO2 share
REF_T_C = 247.5          # optimized cooling-fluid temperature of the anchor's one-step loop (Processes 2022, 3.1.2)
REF_FEED_MOLPCT = dict(H2=71.3, CO=1.5, CO2=21.9, CH3OH=0.3, H2O=0.0, N2=5.0)   # anchor reactor feed, Figure 6
REF_CO_OUT_MOLPCT = 1.76                                                          # anchor reactor outlet CO


# ---------------------------------------------------------------- equilibrium ---------------------------------
def K_co2_hyd(T_K):
    """CO2 + 3 H2 <-> CH3OH + H2O, bar^-2 (anchor Table 1)."""
    T_K = np.asarray(T_K, dtype=float)
    return T_K ** -4.481 * np.exp(4755.7 / T_K + 8.369)


def K_rwgs(T_K):
    """CO2 + H2 <-> CO + H2O, dimensionless (anchor Table 1)."""
    T_K = np.asarray(T_K, dtype=float)
    return T_K ** -1.097 * np.exp(-5337.4 / T_K + 12.569)


def K_co_hyd(T_K):
    """CO + 2 H2 <-> CH3OH, bar^-2."""
    return K_co2_hyd(T_K) / K_rwgs(T_K)


# ---------------------------------------------------------------- Peng-Robinson fugacity ----------------------
FUGACITY = "PR"
# Tc (K), Pc (bar), acentric factor
PR_CRIT = {"H2": (33.19, 13.13, -0.05), "CO2": (304.13, 73.77, 0.225), "CO": (132.85, 34.94, 0.045),
           "MeOH": (512.6, 80.97, 0.565), "H2O": (647.1, 220.64, 0.345), "CH4": (190.56, 45.99, 0.011),
           "N2": (126.2, 33.98, 0.037)}
R_BAR = 8.314462618e-5  # m3 bar / (mol K)


def pr_phi(y, T_K, P_bar):
    """Peng-Robinson vapour fugacity coefficients of a mixture (dict species -> mole fraction arrays), k_ij = 0."""
    T = np.asarray(T_K, dtype=float)
    P = np.asarray(P_bar, dtype=float)
    a, b = {}, {}
    for k in y:
        tc, pc, w = PR_CRIT[k]
        kappa = 0.37464 + 1.54226 * w - 0.26992 * w * w
        alpha = (1.0 + kappa * (1.0 - np.sqrt(T / tc))) ** 2
        a[k] = 0.45724 * R_BAR ** 2 * tc ** 2 / pc * alpha
        b[k] = 0.07780 * R_BAR * tc / pc
    sa = {k: sum(y[j] * np.sqrt(a[k] * a[j]) for j in y) for k in y}   # sum_j y_j a_kj
    am = sum(y[k] * sa[k] for k in y)
    bm = sum(y[k] * b[k] for k in y)
    A = am * P / (R_BAR * T) ** 2
    B = bm * P / (R_BAR * T)
    Z = np.ones(np.broadcast(A, B).shape) + B  # vapour root by Newton from above
    for _ in range(60):
        f = Z ** 3 - (1 - B) * Z ** 2 + (A - 3 * B ** 2 - 2 * B) * Z - (A * B - B ** 2 - B ** 3)
        df = 3 * Z ** 2 - 2 * (1 - B) * Z + (A - 3 * B ** 2 - 2 * B)
        Z_new = Z - f / df
        done = np.all(np.abs(Z_new - Z) <= 1e-15 * np.abs(Z))  # converged to a few ulp (further steps oscillate)
        Z = Z_new
        if done:
            break
    s2 = np.sqrt(2.0)
    lg = np.log((Z + (1 + s2) * B) / (Z + (1 - s2) * B))
    return {k: np.exp(b[k] / bm * (Z - 1) - np.log(Z - B)
                      - A / (2 * s2 * B) * (2 * sa[k] / am - b[k] / bm) * lg) for k in y}


def gas_activities(y, T_K, P_bar, fugacity=None):
    """Fugacities (bar) of the species in y."""
    P = np.asarray(P_bar, dtype=float)
    if (fugacity or FUGACITY) == "ideal":
        return {k: v * P for k, v in y.items()}
    phi = pr_phi(y, T_K, P)
    return {k: phi[k] * y[k] * P for k in y}


def equilibrium_co2_conversion(feed, T_C, P_bar, fugacity=None):
    """Simultaneous CO2-hydrogenation + RWGS equilibrium of a feed (dict species -> mol); returns CO2 conversion."""
    from scipy.optimize import fsolve
    T_K = T_C + 273.15
    n0 = {k: float(feed.get(k, 0.0)) for k in PR_CRIT}

    def comp(xi):
        x1, x2 = xi  # CO2 hydrogenation extent, RWGS extent
        n = dict(n0)
        n["CO2"] -= x1 + x2; n["H2"] -= 3 * x1 + x2; n["MeOH"] += x1; n["H2O"] += x1 + x2; n["CO"] += x2
        return n

    def res(xi):
        n = comp(xi)
        tot = sum(n.values())
        y = {k: max(v, 1e-30) / tot for k, v in n.items()}
        f = gas_activities(y, T_K, P_bar, fugacity)
        r1 = np.log(f["MeOH"] * f["H2O"] / (f["CO2"] * f["H2"] ** 3)) - np.log(K_co2_hyd(T_K))
        r2 = np.log(f["CO"] * f["H2O"] / (f["CO2"] * f["H2"])) - np.log(K_rwgs(T_K))
        return [r1, r2]

    xi = fsolve(res, [0.25 * n0["CO2"], 0.0], xtol=1e-12)
    return float((xi[0] + xi[1]) / n0["CO2"]), comp(xi)


# ---------------------------------------------------------------- selectivity closure -------------------------
def parse_pct(v):
    """Table entry -> fraction; '<1' (below reporting resolution) -> 0."""
    s = str(v).strip()
    return 0.0 if s.startswith("<") else float(s) / 100.0


def close_selectivity(S_MeOH, S_CO_reported, S_CH4):
    """Workbook convention: S_MeOH and S_CH4 as reported, CO(-like) = 1 - S_MeOH - S_CH4 (rounded residual)."""
    s_co = 1.0 - S_MeOH - S_CH4
    if s_co < -1e-12:
        raise ValueError("S_MeOH + S_CH4 > 1")
    return S_MeOH, max(0.0, round(s_co, 12)), S_CH4


# ---------------------------------------------------------------- species loop --------------------------------
def loop_balance(X, SMeOH, SCH4, SCO, h2_co2, purge, x_co=0.0, h2_purity=M.H2_PURITY):
    """Steady-state species balance per 1 mol net MeOH with CO recycle at per-pass conversion x_co.

    Unknown a = reactor-inlet CO2. Per pass: CO2 -> MeOH (X S_MeOH a), CO (X S_CO a), CH4 (X S_CH4 a);
    recycled CO -> MeOH (x_co * co_in). Steady state CO: co_in = (1-p) [co_in (1-x) + X S_CO a]
    -> co_in = (1-p) X S_CO a / (p + x (1-p)). Net MeOH (all condensed) = 1 fixes a.
    """
    X, SMeOH, SCH4, SCO, x = (np.asarray(v, dtype=float) for v in (X, SMeOH, SCH4, SCO, x_co))
    p = np.asarray(purge, dtype=float)
    if np.any((X <= 0) | (X >= 1) | (SMeOH <= 0) | (SMeOH > 1)):
        raise ValueError("invalid conversion/selectivity")
    if np.any(np.abs(SMeOH + SCH4 + SCO - 1.0) > 1e-9):
        raise ValueError("carbon selectivities must sum to 1")
    if np.any((x < 0) | (x > 1)):
        raise ValueError("x_co outside [0, 1]")
    D = p + x * (1.0 - p)
    co2_in = 1.0 / (X * SMeOH + x * (1.0 - p) * X * SCO / D)
    meoh_co2 = X * SMeOH * co2_in
    ch4_prod = X * SCH4 * co2_in
    co_prod = X * SCO * co2_in
    co_in = (1.0 - p) * co_prod / D
    meoh_co = x * co_in
    co_out = co_in * (1.0 - x) + co_prod
    co2_out = (1.0 - X) * co2_in
    h2_in = h2_co2 * co2_in
    h2_out = h2_in - (3.0 * meoh_co2 + 4.0 * ch4_prod + co_prod + 2.0 * meoh_co)
    if np.any(h2_out <= 0):
        raise ValueError("H2 inlet ratio insufficient")
    fresh_co2 = co2_in - (1.0 - p) * co2_out
    fresh_h2 = h2_in - (1.0 - p) * h2_out
    n2_in = fresh_h2 * (1.0 - h2_purity) / h2_purity / p
    ch4_in = (1.0 - p) / p * ch4_prod
    gas_out = co2_out + h2_out + (ch4_in + ch4_prod) + co_out + n2_in
    reactor_in = co2_in + h2_in + ch4_in + co_in + n2_in
    water_prod = meoh_co2 + 2.0 * ch4_prod + co_prod
    nonh2co2 = ch4_in + co_in + n2_in
    return dict(co2_in=co2_in, h2_in=h2_in, fresh_co2=fresh_co2, fresh_h2=fresh_h2, ch4_prod=ch4_prod,
                co_prod=co_prod, co2_out=co2_out, h2_out=h2_out, n2_in=n2_in, ch4_in=ch4_in, co_in=co_in,
                co_out=co_out, meoh_from_co2=meoh_co2, meoh_from_co=meoh_co, water_prod=water_prod, x_co=x,
                gas_out=gas_out, recycle=(1.0 - p) * gas_out, purge_gas=p * gas_out, reactor_in=reactor_in,
                nonreactive_fraction=nonh2co2 / reactor_in, methane_fraction=ch4_in / reactor_in,
                co_inlet_fraction=co_in / reactor_in, n2_inlet_fraction=n2_in / reactor_in,
                crude_liquid_mol=1.0 + water_prod,
                net_co_selectivity=p * co_out / (1.0 + p * co_out + ch4_prod),
                pass_net_co_selectivity=(co_out - co_in) / (X * co2_in),
                carbon_efficiency=1.0 / fresh_co2, fresh_h2_co2=fresh_h2 / fresh_co2)


def outlet_quotients(loop, P_bar, T_C, fugacity=None):
    """Reaction quotients (fugacity basis, bar) at the reactor outlet, MeOH and H2O in the gas phase."""
    n = dict(H2=loop["h2_out"], CO2=loop["co2_out"], CO=loop["co_out"], MeOH=np.ones_like(loop["h2_out"]),
             H2O=loop["water_prod"], CH4=loop["ch4_in"] + loop["ch4_prod"], N2=loop["n2_in"])
    tot = loop["gas_out"] + 1.0 + loop["water_prod"]
    y = {k: v / tot for k, v in n.items()}
    f = gas_activities(y, np.asarray(T_C, dtype=float) + 273.15, P_bar, fugacity)
    with np.errstate(divide="ignore", invalid="ignore"):
        q_rwgs = f["CO"] * f["H2O"] / (f["CO2"] * f["H2"])
        q_coh = f["MeOH"] / (f["CO"] * f["H2"] ** 2)
        q_co2h = f["MeOH"] * f["H2O"] / (f["CO2"] * f["H2"] ** 3)
    return dict(Q_rwgs=q_rwgs, Q_co_hyd=q_coh, Q_co2_hyd=q_co2h, y_out=y)


def _bisect(f, lo, hi, n=80):
    """Vectorized bisection for a root of the monotone function f on [lo, hi] (f(lo), f(hi) of opposite sign)."""
    flo = f(lo)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if np.all((mid == lo) | (mid == hi)):  # interval at float resolution: lo and hi no longer change
            break
        fm = f(mid)
        same = np.sign(fm) == np.sign(flo)
        lo = np.where(same, mid, lo)
        flo = np.where(same, fm, flo)
        hi = np.where(same, hi, mid)
    return 0.5 * (lo + hi)


def x_co_window(X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar):
    """Thermodynamic window (min(x_RWGS, x_MeOH), x_MeOH) for the per-pass CO conversion; see module docstring.
    The window is a single point x_MeOH where x_RWGS > x_MeOH (no conversion satisfies both equilibria)."""
    X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar = np.broadcast_arrays(
        *(np.asarray(v, dtype=float) for v in (X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar)))
    T_K = T_C + 273.15
    k2, k1 = K_rwgs(T_K), K_co_hyd(T_K)
    has_co = SCO > 0
    sco = np.where(has_co, SCO, 1e-12)  # dummy positive value where no CO is formed (window collapses to 0)
    smeoh = SMeOH - (sco - SCO)

    def q(x):
        lb = loop_balance(X, smeoh, SCH4, sco, h2_co2, purge, x)
        return outlet_quotients(lb, P_bar, T_C)

    zero, one = np.zeros_like(X), np.ones_like(X)
    q0, q1 = q(zero), q(one)
    # RWGS: Q_rwgs decreases with x. Need Q_rwgs <= K_rwgs.
    g = lambda x: np.log(q(x)["Q_rwgs"]) - np.log(k2)  # noqa: E731
    x_rwgs = np.where(q0["Q_rwgs"] <= k2, 0.0, np.where(q1["Q_rwgs"] > k2, 1.0, _bisect(g, zero, one)))
    # CO hydrogenation: Q_co_hyd increases with x. Allowed while Q_co_hyd <= K_co_hyd.
    h = lambda x: np.log(q(x)["Q_co_hyd"]) - np.log(k1)  # noqa: E731
    x_meoh = np.where(q0["Q_co_hyd"] >= k1, 0.0, np.where(q1["Q_co_hyd"] <= k1, 1.0, _bisect(h, zero, one)))
    x_meoh = np.where(has_co, x_meoh, 0.0)
    x_low = np.where(has_co, np.minimum(x_rwgs, x_meoh), 0.0)
    return x_low, x_meoh


def resolve_x_co(rule, X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar):
    """Numeric x_CO for a rule name (or pass-through number)."""
    if not isinstance(rule, str):
        return np.asarray(rule, dtype=float)
    if rule == "inert":
        return np.zeros(np.broadcast(np.asarray(X), np.asarray(purge)).shape)
    if T_C is None:
        raise ValueError("x_co rule %r needs the reaction temperature T_C" % rule)
    lo, hi = x_co_window(X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar)
    if rule == "recycled_central":
        return lo
    if rule == "recycled_high":
        return hi
    if rule == "recycled_equal_X":
        return np.clip(np.asarray(X, dtype=float), lo, hi)
    raise ValueError("unknown x_co rule %r" % rule)


# ---------------------------------------------------------------- compression ---------------------------------
def compressor_power_MW(flow_kmol_h, pin_bar, pout_bar):
    """Engine formula, array-valued in pressure; zero work when the stream is already at pressure."""
    ratio = np.maximum(np.asarray(pout_bar, dtype=float) / np.asarray(pin_bar, dtype=float), 1.0)
    j_per_mol = M.R * M.COMP_T_K * np.log(ratio) / M.COMP_ETA
    return j_per_mol * np.asarray(flow_kmol_h) * 1000.0 / 3.6e9


def powers(loop, pressure_bar):
    P = np.asarray(pressure_bar, dtype=float)
    p_co2 = compressor_power_MW(loop["fresh_co2"] * M.PROD_KMOL_H, M.CO2_FEED_PRESSURE_BAR, P)
    p_h2 = compressor_power_MW(loop["fresh_h2"] * M.PROD_KMOL_H, M.H2_FEED_PRESSURE_BAR, P)
    p_rec = compressor_power_MW(loop["recycle"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION,
                                np.maximum(1.0, P - M.LOOP_DP_BAR), P)
    return p_co2, p_h2, p_rec


# ---------------------------------------------------------------- plant economics -----------------------------
def catalyst_tonnes(STY_per_g_metal=None, metal_wt=None, STY_per_g_cat=None):
    if STY_per_g_cat is not None:
        if STY_per_g_metal is not None:
            raise ValueError("give one productivity basis")
        return M.PROD_TPH * 1000.0 / np.asarray(STY_per_g_cat, dtype=float) / 1000.0
    if STY_per_g_metal is None or metal_wt is None:
        raise ValueError("STY_per_g_metal needs metal_wt")
    return M.PROD_TPH * 1000.0 / np.asarray(STY_per_g_metal, dtype=float) / (np.asarray(metal_wt) / 100.0) / 1000.0


def economics(X, SMeOH, SCH4, SCO, *, STY_per_g_metal=None, metal_wt=None, STY_per_g_cat=None,
              P_bar=M.CAND_PRESSURE_BAR, h2_co2=M.CANDIDATE_H2_CO2, purge=M.SOURCE_PURGE, x_co="inert", T_C=None,
              cat_price_eur_kg=None, cat_life_y=None):
    """Net production cost (EUR/t MeOH) and loop state of one catalyst operating point (array-valued)."""
    x = resolve_x_co(x_co, X, SMeOH, SCH4, SCO, h2_co2, purge, T_C, P_bar)
    loop = loop_balance(X, SMeOH, SCH4, SCO, h2_co2, purge, x)
    p_co2, p_h2, p_rec = powers(loop, P_bar)
    feed_eur_t, h2_eur_t, co2_eur_t = M._feed_cost(loop)
    feed_M = feed_eur_t * M.PROD_TPY / 1e6
    elec_M = (p_co2 + p_h2 + p_rec) * M.HOURS_Y * M.ELEC_EUR_MWH / 1e6
    catalyst_t = catalyst_tonnes(STY_per_g_metal, metal_wt, STY_per_g_cat)
    cat_repl_M = 0.0
    if cat_price_eur_kg is not None:
        if not cat_life_y:
            raise ValueError("catalyst price needs a lifetime")
        cat_repl_M = catalyst_t * 1000.0 * np.asarray(cat_price_eur_kg) / np.asarray(cat_life_y) / 1e6
    reactor_in = loop["reactor_in"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION
    recycle = loop["recycle"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION
    purge_flow = loop["purge_gas"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION
    crude = loop["crude_liquid_mol"] * M.PROD_KMOL_H
    gas_r = reactor_in / M.REF_REACTOR_IN_KMOL_H
    liq_r = crude / M.REF_CRUDE_LIQ_KMOL_H
    pur_r = np.maximum(purge_flow, 1e-12) / M.REF_PURGE_KMOL_H
    E, G, C = M.EC_REF, M.EXP_GENERAL, M.EXP_COMP
    ec = {
        "Reactor modules": E["Reactor modules"] * (catalyst_t / M.SOURCE_CAT_T) ** G,
        "Carbon dioxide compressor": E["Carbon dioxide compressor"] * (p_co2 / M.REF_POWERS[0]) ** C,
        "Hydrogen compressor": E["Hydrogen compressor"] * (p_h2 / M.REF_POWERS[1]) ** C,
        "Recycle/reflux compressor": E["Recycle/reflux compressor"] * (p_rec / M.REF_POWERS[2]) ** C,
        "Reactor preheaters": E["Reactor preheaters"] * gas_r ** G,
        "Heat exchangers": E["Heat exchangers"] * gas_r ** G,
        "Flash drums": E["Flash drums"] * gas_r ** G,
        "Distillation column": E["Distillation column"] * liq_r ** G,
        "Pump": E["Pump"] * liq_r ** G,
        "Furnace & blower": E["Furnace & blower"] * pur_r ** G,
        "Turbine & generator": E["Turbine & generator"] * pur_r ** G,
    }
    EC = sum(ec.values())
    FCI = M.LF * EC
    WC = FCI / 9.0
    ACC = FCI * M.CRF + WC * M.IR
    direct = M.COMMON_DIRECT_MEUR_Y + feed_M + elec_M + cat_repl_M
    NPC = (ACC + direct + 2.2125 * M.SOURCE_OL_MEUR_Y + 0.081 * FCI) / 0.90
    out = dict(cost_eur_t=NPC * 1e6 / M.PROD_TPY, NPC_MEUR_Y=NPC, EC_MEUR=EC, FCI_MEUR=FCI, ACC_MEUR_Y=ACC,
               direct_MEUR_Y=direct, indirect_MEUR_Y=NPC - ACC - direct, h2_eur_t=h2_eur_t, co2_eur_t=co2_eur_t,
               elec_eur_t=elec_M * 1e6 / M.PROD_TPY, cat_repl_eur_t=cat_repl_M * 1e6 / M.PROD_TPY,
               catalyst_t=catalyst_t, recycle_kmol_h=recycle, raw_recycle_kmol_h=loop["recycle"] * M.PROD_KMOL_H,
               x_co=x, nonreactive_fraction=loop["nonreactive_fraction"],
               methane_fraction=loop["methane_fraction"], co_inlet_fraction=loop["co_inlet_fraction"],
               n2_inlet_fraction=loop["n2_inlet_fraction"], net_co_selectivity=loop["net_co_selectivity"],
               pass_net_co_selectivity=loop["pass_net_co_selectivity"],
               carbon_efficiency=loop["carbon_efficiency"], fresh_h2_co2=loop["fresh_h2_co2"],
               P_co2_MW=p_co2, P_h2_MW=p_h2, P_rec_MW=p_rec,
               sep_loop_EC_MEUR=(ec["Recycle/reflux compressor"] + ec["Heat exchangers"] + ec["Flash drums"]
                                 + ec["Distillation column"] + ec["Pump"]),
               ec=ec, loop=loop)
    if T_C is not None:
        q = outlet_quotients(loop, P_bar, T_C)
        T_K = np.asarray(T_C, dtype=float) + 273.15
        out.update(rwgs_approach=q["Q_rwgs"] / K_rwgs(T_K), co_hyd_approach=q["Q_co_hyd"] / K_co_hyd(T_K),
                   co2_hyd_approach=q["Q_co2_hyd"] / K_co2_hyd(T_K), y_out=q["y_out"])
        out["equilibrium_feasible"] = out["co2_hyd_approach"] <= 1.0 + EQ_TOL
    return out


def cost(c, **kw):
    """Convenience wrapper for a candidate dict with keys X, SMeOH, SCH4, SCO and productivity/operating keys."""
    keys = ("STY_per_g_metal", "metal_wt", "STY_per_g_cat", "P_bar", "h2_co2", "T_C", "cat_price_eur_kg",
            "cat_life_y")
    args = {k: c[k] for k in keys if k in c and c[k] is not None}
    args.update(kw)
    return economics(c["X"], c["SMeOH"], c["SCH4"], c["SCO"], **args)


PURGES = M.PURGES  # 0.5-40 %, 0.1 % steps (396 levels), same grid as the canonical sweep


def purge_sweep(c, cap_conversion=True, **kw):
    """Cost and loop state on the canonical purge grid (vectorized over purge).

    With the reaction temperature known and cap_conversion, the per-pass CO2 conversion at each purge level is
    min(X, X_eq), X_eq being the conversion at which the loop outlet reaches CO2-hydrogenation equilibrium: a
    catalyst that would pass equilibrium at the loop-inlet composition reaches it and stops there. X_eff and
    X_capped record the conversion used."""
    s = cost(c, purge=PURGES, **kw)
    n = len(PURGES)
    s["X_eff"] = np.full(n, float(c["X"]))
    s["X_capped"] = np.zeros(n, dtype=bool)
    if not cap_conversion or "equilibrium_feasible" not in s:
        return s
    bad = ~np.asarray(s["equilibrium_feasible"])
    if not bad.any():
        return s
    purges, X0 = PURGES[bad], float(c["X"])

    def f(X):
        return np.log(cost(dict(c, X=X), purge=purges, **kw)["co2_hyd_approach"])

    lo, hi = np.full(purges.shape, X0 * 1e-6), np.full(purges.shape, X0)   # f(lo) < 0 <= f(hi)
    for _ in range(60):                       # bisection that keeps the feasible end, so the outlet stays <= K
        mid = 0.5 * (lo + hi)
        below = f(mid) <= 0.0
        lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        if np.all(hi - lo <= 1e-9 * hi):
            break
    x_eq = lo
    capped = cost(dict(c, X=x_eq), purge=purges, **kw)
    for k, v in capped.items():
        if isinstance(v, np.ndarray) and isinstance(s.get(k), np.ndarray) and s[k].shape == (n,) and v.shape == purges.shape:
            s[k] = s[k].copy()
            s[k][bad] = v
    s["X_eff"][bad] = x_eq
    s["X_capped"][bad] = True
    return s


def eligible_purges(sweep, nonreactive_max=NONREACTIVE_MAX):
    """Purge levels of a sweep that are equilibrium feasible and within the nonreactive-fraction limit."""
    return np.asarray(sweep["equilibrium_feasible"]) & (np.asarray(sweep["nonreactive_fraction"]) <= nonreactive_max)


def optimal_purge(c, constrained=True, sweep=None, **kw):
    """Cost-optimal purge level of one candidate on the canonical grid (needs T_C).

    constrained=True: minimum over the eligible levels (`eligible_purges`); cost and purge are NaN when no level is
    eligible (the candidate is infeasible). constrained=False: minimum over every level (the earlier treatment).
    Returns dict(cost_eur_t, purge, feasible, n_eligible, at_opt) where at_opt holds the sweep entries at the
    chosen level."""
    s = purge_sweep(c, **kw) if sweep is None else sweep
    cost_ = np.asarray(s["cost_eur_t"], dtype=float)
    ok = eligible_purges(s)
    pick = ok if constrained else np.isfinite(cost_)
    if not pick.any():
        return dict(cost_eur_t=np.nan, purge=np.nan, feasible=False, n_eligible=0, at_opt={})
    j = int(np.argmin(np.where(pick, cost_, np.inf)))
    at = {k: float(np.asarray(v).ravel()[j]) for k, v in s.items()
          if isinstance(v, np.ndarray) and v.shape == cost_.shape}
    return dict(cost_eur_t=float(cost_[j]), purge=float(PURGES[j]), feasible=bool(ok[j]), n_eligible=int(ok.sum()),
                at_opt=at)


def reference_economics(x_co="inert", S_CO=M.SOURCE_S_CO, S_MeOH=M.SOURCE_S_MEOH):
    """The anchor loop (X 0.285, 70 bar, H2/CO2 3, 2 % purge, catalyst 6 x 478.13 t) through this model."""
    return economics(M.SOURCE_X, S_MeOH, M.SOURCE_S_CH4, S_CO, STY_per_g_cat=M.PROD_TPH * 1000.0 / (M.SOURCE_CAT_T * 1000.0),
                     P_bar=M.REF_PRESSURE_BAR, h2_co2=M.SOURCE_H2_CO2, purge=M.SOURCE_PURGE, x_co=x_co, T_C=REF_T_C)
