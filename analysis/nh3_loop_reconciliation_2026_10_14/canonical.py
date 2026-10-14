"""Canonical NH3-FINAL-1.2 side: T1 recycle-rise sensitivity and canonical point costs for the T3 bridge.

The canonical harness (`harness_core.NH3Harness`) is built from the canonical manifest unchanged. A recycle-rise variant
is a shallow copy whose `DP_RECYCLE_BAR` is changed and whose process states are rebuilt with the canonical
`_build_process_states`; only the recycle-compressor electricity and its CAPEX can move (asserted: identical T, P, Tsep,
per-pass conversion and recycle ratio in every state).
"""
from __future__ import annotations

import copy
import math

import numpy as np
from scipy.optimize import brentq
from scipy.stats import spearmanr

import common  # noqa: F401  (paths, NH3_MODEL=1.2)
import nh3_model as NM

hc = NM.core()
FROZEN_RESULTS = common.load(NM.run_dir() / "results.json")
FROZEN_ALPHA = FROZEN_RESULTS["backward_reachability"]["Ru_activity_break_even_multiplier"]


def build():
    h = hc.NH3Harness(NM.cfg(), NM.root())
    assert h.DP_RECYCLE_BAR == 3.0 and h.NSTATE == 14510
    return h


def with_recycle_rise(h, dp):
    """Canonical harness with process.recycle_pressure_rise_bar = dp (labelled sensitivity)."""
    if float(dp) == h.DP_RECYCLE_BAR:
        return h
    g = copy.copy(h)
    g.DP_RECYCLE_BAR = float(dp)
    g.process_states = g._build_process_states()
    g._state_arrays()
    assert g.NSTATE == h.NSTATE
    for k in ("state_T", "state_P", "state_Tsep", "state_fresh", "state_refrig"):
        assert np.array_equal(getattr(g, k), getattr(h, k)), k
    for a, b in zip(g.process_states, h.process_states):
        assert a["X"] == b["X"] and a["recycle_total"] == b["recycle_total"]
    return g


# --- T1 -------------------------------------------------------------------------------------------------------------

def censored_ranks(det, metals):
    ford = det["feasible_economic_order"]
    nf = len(ford)
    tie = (nf + 1 + len(metals)) / 2.0
    return {m: (ford.index(m) + 1 if m in ford else tie) for m in metals}


def raw_ranks(det, metals):
    return {m: det["raw_economic_order"].index(m) + 1 for m in metals}


def parity_multiple(h):
    fe_log = h.frozen_state_logtof(hc.EN0_CANON["Fe"])
    ru_log = h.frozen_state_logtof(hc.EN0_CANON["Ru"])
    FE = h.eval_scenario("Fe", fe_log)["total_cost"]

    def gap(loga):
        try:
            return h.eval_scenario("Ru", ru_log, alpha=10.0 ** loga)["total_cost"] - FE
        except RuntimeError:
            return 1e100
    return 10.0 ** brentq(gap, -6.0, 12.0, xtol=1e-11)


def t1(rises=(3.0, 6.0, 9.2)):
    h0 = build()
    frozen = FROZEN_RESULTS["deterministic"]
    metals = list(hc.ACTIVITY_ORDER_CANON)
    out = {"rises_bar": list(rises), "n_states": h0.NSTATE, "runs": {}}
    rows = []
    for dp in rises:
        h = with_recycle_rise(h0, dp)
        det = h.deterministic()
        alpha = parity_multiple(h)
        cr, cf = censored_ranks(det, metals), censored_ranks(frozen, metals)
        rr, rf = raw_ranks(det, metals), raw_ranks(frozen, metals)
        feas = {m: det["metals"][m]["feasible"] for m in metals}
        run = {
            "recycle_pressure_rise_bar": dp,
            "feasible_economic_order": det["feasible_economic_order"],
            "raw_economic_order": det["raw_economic_order"],
            "spearman_censored_vs_frozen": float(spearmanr([cf[m] for m in metals], [cr[m] for m in metals]).statistic),
            "spearman_raw_vs_frozen": float(spearmanr([rf[m] for m in metals], [rr[m] for m in metals]).statistic),
            "activity_vs_economic_raw_spearman": det["raw_global_spearman"],
            "activity_vs_economic_censored_spearman": det["censored_global_spearman"],
            "top3_spearman": det["rolling"][0]["rho_raw"],
            "Ru_minus_Fe": feas["Ru"]["total_cost"] - feas["Fe"]["total_cost"],
            "Ru_minus_Os": feas["Ru"]["total_cost"] - feas["Os"]["total_cost"],
            "Ru_parity_activity_multiple": alpha,
            "metals": {},
        }
        for m in metals:
            f, u = feas[m], det["metals"][m]["unconstrained"]
            rec = {"metal": m, "recycle_pressure_rise_bar": dp,
                   "feasible": f is not None,
                   "cost_USD_t": None if f is None else f["total_cost"],
                   "T_C": None if f is None else f["T_C"], "P_bar": None if f is None else f["P_bar"],
                   "Tsep_C": None if f is None else f["Tsep_C"], "V_m3": None if f is None else f["V_m3"],
                   "recycle_comp_USD_t": None if f is None else f["breakdown"]["recycle_comp"],
                   "compressor_capex_USD_t": None if f is None else f["breakdown"]["compressor_capex"],
                   "censored_rank": cr[m], "frozen_censored_rank": cf[m],
                   "unconstrained_cost_USD_t": u["total_cost"], "unconstrained_P_bar": u["P_bar"],
                   "raw_rank": rr[m], "frozen_raw_rank": rf[m],
                   "frozen_cost_USD_t": None if frozen["metals"][m]["feasible"] is None
                   else frozen["metals"][m]["feasible"]["total_cost"]}
            run["metals"][m] = rec
            rows.append(rec)
        out["runs"][f"{dp:g}"] = run
    # replay gate at 3 bar
    g = out["runs"]["3"]
    gate = {"Fe_Ru_Os_cost_max_abs_diff": max(abs(g["metals"][m]["cost_USD_t"] - frozen["metals"][m]["feasible"]["total_cost"])
                                              for m in ("Fe", "Ru", "Os")),
            "optima_identical": all((g["metals"][m]["T_C"], g["metals"][m]["P_bar"], g["metals"][m]["Tsep_C"]) ==
                                    (frozen["metals"][m]["feasible"]["T_C"], frozen["metals"][m]["feasible"]["P_bar"],
                                     frozen["metals"][m]["feasible"]["Tsep_C"]) for m in ("Fe", "Ru", "Os")),
            "parity_abs_diff": abs(g["Ru_parity_activity_multiple"] - FROZEN_ALPHA),
            "order_identical": g["feasible_economic_order"] == frozen["feasible_economic_order"]}
    gate["pass"] = bool(gate["Fe_Ru_Os_cost_max_abs_diff"] < 1e-9 and gate["optima_identical"]
                        and gate["parity_abs_diff"] < 1e-6 and gate["order_identical"])
    out["replay_gate_3bar"] = gate
    return out, rows


# --- canonical points with measured kinetics (T3) ------------------------------------------------------------------

def kinetics_swap():
    import kinetics_swap as KS          # NH3_MODEL=1.2 branch of the staged-converter folder
    return KS


def manuscript_optima(h):
    """Recompute the manuscript measured-kinetics headline (plug flow, measured rates) on the canonical states."""
    KS = kinetics_swap()
    _, V0, _, _ = h.cost_arrays("Fe", h.frozen_state_logtof(hc.EN0_CANON["Fe"]))
    j0 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == KS.CAL_STATE)
    res = KS.evaluate(h, KS.state_arrays(h), "plug", "source", float(V0[j0]))
    res.pop("_profile", None)
    return res


def point_harness(h, points, dp=3.0):
    """Canonical harness restricted to the given (T_C, P_bar, Tsep_C) self-consistent states (same functions)."""
    g = copy.copy(h)
    g.DP_RECYCLE_BAR = float(dp)
    states = []
    for T, P, Ts in points:
        s = g.self_consistent_process_state(float(T), float(P), float(Ts))
        if s is None:
            raise ValueError(f"no canonical self-consistent state at {T} C, {P} bar, Tsep {Ts} C")
        states.append(s)
    g.process_states = states
    g._state_arrays()
    return g


def canonical_point_costs(h, point, catalyst, recovery=0.9555, fin_rate=0.12, dp=3.0, accounting="cashflow"):
    """Cost categories (USD/t) of one catalyst at one canonical state, measured kinetics, plug sizing, source rates.

    Fe: fused-iron bed (rate per m3, 0.7151 x 2500 kg/m3 at 8 USD/kg). Ru: supported Ru/C, 8 wt%, 490 kg/m3, measured
    activity per kg Ru, 53,852.5 USD/kg. Accounting as kinetics_swap (25-y cash flow at fin_rate, or benchmark).
    """
    KS = kinetics_swap()
    g = point_harness(h, [point], dp)
    st = KS.state_arrays(g)
    if catalyst == "Fe":
        V = KS.amount(st, KS.rate_fe_m3, g, "plug")
        metal_kg = V * g.ACTIVE_FRACTION * g.BED_DENSITY
        tot, metal = KS.costs(g, V, metal_kg, hc.PRICE["Fe"], KS.multiplier(accounting, 0.0, fin_rate))
    else:
        M = KS.amount(st, KS.rate_ru_kgRu, g, "plug")
        V = M / (KS.W * KS.RHO)
        tot, metal = KS.costs(g, V, M, KS.P_RU, KS.multiplier(accounting, recovery, fin_rate))
    reactor = float(KS.reactor(g, V)[0])
    s = g.process_states[0]
    d = {"model": "canonical", "catalyst": catalyst, "T_C": point[0], "P_bar": point[1], "Tsep_C": point[2],
         "recycle_rise_bar": dp, "recovery": recovery, "metal_rate": fin_rate,
         "total_USD_t": float(tot[0]), "bed_m3": float(V[0]), "within_90m3": bool(V[0] <= g.V_CAP),
         "inventory": float(metal[0]), "reactor": reactor,
         "utilities": float(s["fresh_comp"] + s["recycle_comp"] + s["refrigeration"]),
         "compressor_capital": float(s["compressor_capex"]),
         "fresh_comp": float(s["fresh_comp"]), "recycle_comp": float(s["recycle_comp"]),
         "refrigeration": float(s["refrigeration"]),
         "excess_feed": 0.0, "purge_gas_loss": 0.0, "dissolved_gas_loss": 0.0, "NH3_in_purge": 0.0,
         "feed_residual": 0.0, "hot_duty": 0.0,
         "X_per_pass": float(s["X"]), "inlet_NH3_pct": float(100 * st["yA"][0]), "inlet_inerts_pct": 0.0}
    if not math.isfinite(d["total_USD_t"]):        # bed above the 90 m3 cap: categories still reported
        d["total_USD_t"] = d["inventory"] + d["reactor"] + d["utilities"] + d["compressor_capital"]
    d["sum_check"] = d["inventory"] + d["reactor"] + d["utilities"] + d["compressor_capital"] - d["total_USD_t"]
    return d
