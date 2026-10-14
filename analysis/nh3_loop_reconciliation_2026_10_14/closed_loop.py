"""Closed-loop side (NH3-SI-LOOP-v1 + NH3-KINETIC-COST-v1), reused unchanged.

Cold states come from the upstream bounded subprocess worker (`run_study.cold_subprocess` -> `cold_worker.job` ->
`loop.solve` + `coupling.flow_record`, 20 s numerical budget, unresolved cases retained). Beds come from
`kinetic_bridge.size_bed`, costs from `economics.evaluate`, exactly as `coupling.candidate` / `source_domains.repriced`.
"""
from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from itertools import product

import numpy as np
from scipy.optimize import brentq

import common
import coupling as C
import economics as E
import kinetic_bridge as KB
import run_study as RS
import source_domains as SD

B93 = E.EconomicSettings()
B94 = replace(E.EconomicSettings(), H2_USD_kg=3.0, N2_USD_kg=0.06, ru_recovery=0.90)
assert B94 == SD.PRICE, "B94 must be the #94 price basis"
BASES = {"B94": B94, "B93": B93}
MAX_INERT_PCT = SD.MAX_INERT_PCT
assert MAX_INERT_PCT == 15.0

T2_PRESSURES = (90.0, 100.0, 120.0, 140.0)
T3_EXTRA_PRESSURES = (105.0, 150.0)
GRID = {"T_C": (400.0, 425.0, 445.0, 450.0),
        "X": (0.08, 0.10, 0.12, 0.14, 0.20, 0.225, 0.25, 0.275, 0.35),
        "T2_C": (-20.0, -10.0, 0.0, 10.0),
        "purge": (0.0075, 0.01, 0.015, 0.03)}
TARGET_TPD = 1500.0
PRICES = lambda e: np.array([e.N2_USD_kg, e.H2_USD_kg, e.CH4_USD_kg, e.Ar_USD_kg, 0.0])


# --- cold states ----------------------------------------------------------------------------------------------------

def cold_grid(pressures, workers=4, cache=None, log=print):
    """All (P, X, T2, purge) cold states of the grid; upstream worker; cache keyed by run_study.grid_key."""
    have = {}
    if cache is not None and cache.exists():
        have = {d["state_id"]: d for d in common.load(cache)["designs"]}
    tasks = []
    for P, X, T2, pg in product(pressures, GRID["X"], GRID["T2_C"], GRID["purge"]):
        sid = RS.grid_key(P, X, T2, pg)
        if sid in have and have[sid].get("record"):
            continue
        tasks.append({"state_id": sid, "P_bar": P, "X": X, "T2_C": T2, "purge": pg})
    t0 = time.time()
    for attempt, nw in enumerate((workers, 2)):
        if not tasks:
            break
        with ThreadPoolExecutor(max_workers=nw) as ex:
            futs = [ex.submit(RS.cold_subprocess, dict(d), TARGET_TPD) for d in tasks]
            for k, fut in enumerate(as_completed(futs)):
                d = fut.result()
                d["attempt"] = attempt + 1
                have[d["state_id"]] = d
                if (k + 1) % 50 == 0:
                    log(f"  cold states {k + 1}/{len(tasks)} (attempt {attempt + 1}) {time.time() - t0:.0f} s")
        tasks = [{k: d[k] for k in ("state_id", "P_bar", "X", "T2_C", "purge")}
                 for d in have.values() if not d.get("record") and d["P_bar"] in pressures
                 and str(d.get("reason", "")).startswith("NUMERICAL_BUDGET")]
        if cache is not None:
            common.dump(cache, {"grid": GRID, "designs": sorted(have.values(), key=lambda d: d["state_id"])}, nd=12)
    wanted = {RS.grid_key(P, X, T2, pg) for P, X, T2, pg in product(pressures, GRID["X"], GRID["T2_C"], GRID["purge"])}
    return {k: v for k, v in have.items() if k in wanted}


# --- candidates -----------------------------------------------------------------------------------------------------

def with_heat(record, T_C):
    r = dict(record)
    r["isothermal_reaction_heat_removed_MW"] = -r["extent_kmol_h"] / 3.6 * KB.hot_heat_per_mol_NH3(T_C + 273.15) / 1e6
    return r


def size_candidates(states, temps=GRID["T_C"]):
    """Isothermal inverse-PFR bed for every (cold state, T, catalyst) (coupling.candidate without pricing)."""
    rows = []
    for d in states.values():
        if not d.get("record"):
            continue
        rec = d["record"]
        for T, cat in product(temps, ("Fe", "Ru")):
            try:
                v = KB.size_bed(cat, T + 273.15, d["P_bar"], rec["feed_kmol_h"], rec["extent_kmol_h"])
            except Exception as exc:          # retained, never counted
                v = {"feasible": False, "reason": "sizing_error:" + type(exc).__name__ + ":" + str(exc)[:120]}
            row = {"state_id": d["state_id"], "catalyst": cat, "T_C": T, "P_bar": d["P_bar"], "X": d["X"],
                   "T2_C": d["T2_C"], "purge": d["purge"], "inlet_inerts_pct": rec["inlet_inerts_pct"],
                   "inlet_NH3_pct": rec["inlet_NH3_pct"], **v}
            row["passes_inert_bound"] = rec["inlet_inerts_pct"] <= MAX_INERT_PCT + 1e-10
            row["eligible"] = bool(v.get("feasible") and v["bed_m3"] <= 90.0 and row["passes_inert_bound"])
            rows.append(row)
    return rows


def price(row, record, e):
    """economics.evaluate of one eligible isothermal bed plus the excess-feed split (identity, nothing added)."""
    c = E.evaluate(row["catalyst"], row["bed_m3"], row["P_bar"], with_heat(record, row["T_C"]), e)
    c.update(feed_split(record, e))
    assert abs(c["purge_gas_loss"] + c["dissolved_gas_loss"] + c["NH3_in_purge"] + c["feed_cost_decomposition_residual_USD_t"]
               - c["excess_feed_USD_t"]) < 1e-9
    return c


def feed_split(record, e):
    target_h = e.product_tpd / 24.0
    p = PRICES(e)
    purge = np.asarray(record["purge_kmol_h"])
    liq = np.asarray(record["products_kmol_h"]).copy()
    liq[4] = 0.0
    nh3_cost = 0.5 * E.MW[0] * e.N2_USD_kg + 1.5 * E.MW[1] * e.H2_USD_kg
    return {"purge_gas_loss": float(np.sum(purge * E.MW * p)) / target_h,
            "dissolved_gas_loss": float(np.sum(liq * E.MW * p)) / target_h,
            "NH3_in_purge": purge[4] / target_h * nh3_cost}


CATS = ("excess_feed", "purge_gas_loss", "dissolved_gas_loss", "NH3_in_purge", "feed_residual",
        "utilities", "inventory", "reactor", "compressor_capital", "hot_duty")


def categories(c):
    return {"excess_feed": c["excess_feed_USD_t"], "purge_gas_loss": c["purge_gas_loss"],
            "dissolved_gas_loss": c["dissolved_gas_loss"], "NH3_in_purge": c["NH3_in_purge"],
            "feed_residual": c["feed_cost_decomposition_residual_USD_t"], "utilities": c["utility_USD_t"],
            "inventory": c["inventory_USD_t"], "reactor": c["reactor_annualized_USD_t"],
            "compressor_capital": c["compressor_annualized_USD_t"], "hot_duty": c["hot_duty_scenario_USD_t"]}


def best(rows, states, e, cat, where=lambda r: True):
    out = None
    for r in rows:
        if r["catalyst"] != cat or not r["eligible"] or not where(r):
            continue
        c = price(r, states[r["state_id"]]["record"], e)
        if out is None or c["decision_relevant_cost_USD_t"] < out[1]["decision_relevant_cost_USD_t"]:
            out = (r, c)
    return out


def describe(sel, states):
    if sel is None:
        return None
    r, c = sel
    rec = states[r["state_id"]]["record"]
    kwh = 1000.0 / (TARGET_TPD / 24.0)
    d = {"model": "closed_loop", "catalyst": r["catalyst"], "state_id": r["state_id"], "T_C": r["T_C"], "P_bar": r["P_bar"],
         "X": r["X"], "T2_C": r["T2_C"], "purge": r["purge"], "bed_m3": r["bed_m3"],
         "inlet_inerts_pct": r["inlet_inerts_pct"], "inlet_NH3_pct": r["inlet_NH3_pct"],
         "rate_domain": r.get("rate_domain"), "rate_P_inside_source_range": r.get("rate_P_inside_source_range"),
         "rate_T_inside_source_range": r.get("rate_T_inside_source_range"),
         "decision_USD_t": c["decision_relevant_cost_USD_t"], "gross_USD_t": c["modeled_loop_cost_USD_t"],
         "total_USD_t": c["decision_relevant_cost_USD_t"],
         "recycle_compression_kWh_t": rec["compressor_shaft_MW_by_service"][-1] * kwh,
         "fresh_compression_kWh_t": sum(rec["compressor_shaft_MW_by_service"][:-1]) * kwh,
         "refrigeration_kWh_t": rec["refrigeration_MW"] * kwh,
         **categories(c)}
    return d


def gap_terms(ru, fe):
    return {k: ru[k] - fe[k] for k in CATS}


def crossover(rows, states, base, where=lambda r: True, lo=0.0, hi=0.12, step=0.0025):
    """Ru - Fe as a function of the metal finance rate (both reoptimised); scan then brentq on sign changes."""
    def gap(rate):
        e = replace(base, metal_rate=rate)
        f, r = best(rows, states, e, "Fe", where), best(rows, states, e, "Ru", where)
        if f is None or r is None:
            return math.nan
        return r[1]["decision_relevant_cost_USD_t"] - f[1]["decision_relevant_cost_USD_t"]
    rates = np.round(np.arange(lo, hi + step / 2, step), 10)
    g = [gap(x) for x in rates]
    roots = []
    for a, b, ga, gb in zip(rates[:-1], rates[1:], g[:-1], g[1:]):
        if math.isfinite(ga) and math.isfinite(gb) and ga * gb < 0:
            roots.append(brentq(gap, a, b, xtol=1e-6))
        elif ga == 0.0:
            roots.append(float(a))
    finite = [v for v in g if math.isfinite(v)]
    if roots:
        verdict = "crossover"
    elif finite and all(v < 0 for v in finite):
        verdict = "Ru_cheaper_on_whole_interval"
    elif finite and all(v > 0 for v in finite):
        verdict = "Fe_cheaper_on_whole_interval"
    else:
        verdict = "no_comparison"
    return {"roots": roots, "verdict": verdict, "gap_at_0": g[0], "gap_at_12pct": g[-1],
            "scan": [{"rate": float(x), "Ru_minus_Fe": v} for x, v in zip(rates, g)]}
