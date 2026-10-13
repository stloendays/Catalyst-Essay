"""Ru/C vs fused Fe in the KAAP-type loop at documented metal lease/financing rates.

Reuses, without modification:
  * merged PR #57 owned-metal cash-flow algebra (lifecycle_cashflow.py on main);
  * draft PR #61 supplier-lease algebra (supplier_metal_contracts_pr61.py, a
    byte-identical copy of blob c2f24bb9 on branch nh3-ru-commercial-terms-2026-10-12).

Two contract structures are evaluated at each rate listed in documented_rates.csv:
  owned  - operator buys each Ru charge; all metal cash flows (and Fe's) discounted
           at the metal financing rate (PR #57 convention; parity 0.56 %/y in 1.1);
  lease  - supplier keeps title; operator pays an annual rent fraction of the Ru
           value plus fine-metal shortfall at each return, all at the frozen 12 %
           plant rate (PR #61 lease_unsecured; parity 0.92 %/y in 1.1).

The rates are documented for Pt, Pd and Au. No Ru lease or financing rate was
found; applying them to Ru is an inference, labelled as such in the outputs.

Model version: NH3_MODEL=1.1 (default) writes the committed files in this folder;
NH3_MODEL=1.2 reads the NH3-FINAL-1.2 run (NH3_HARNESS_1_2) and writes nh3_1_2/.
The response surface is loaded from the harness cache and never rebuilt.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PR57 = REPO / "analysis" / "nh3_ru_net_recovery_boundary_2026_10_12"
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

ROOT, RUN = NM.root(), NM.run_dir()
OUT = NM.out_dir(HERE)
# PR #57 reference outputs of the same model: the committed files for 1.1, PR57/nh3_1_2/ for 1.2 (once ported).
PR57_OUT = PR57 if NM.VERSION == "1.1" else PR57 / "nh3_1_2"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PR57))
sys.path.insert(0, str(HERE))

hc = NM.core()
from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier  # noqa: E402
from supplier_metal_contracts_pr61 import (SupplierMetalTerms,  # noqa: E402
                                           supplier_metal_multiplier)

U_EXPOSURE = 11.0
FLAGSHIP = dict(loop="KAAP", w=0.08, rho=490.0, physical_r=0.9555)
RECOVERIES = (0.90, 0.9305, 0.9555)
LOADINGS = (0.05, 0.08, 0.10)
DENSITIES = (430.0, 490.0, 550.0)
LEASE_VARIANTS = {
    "lease_unsecured": {},
    "lease_collateral25": {"collateral": 0.25},
    "lease_refining_loss": {"refining_yield": 0.95, "processing_fee": 500.0,
                            "settlement_delay": 0.5},
}
TOL = 1e-9


def pinned_response(h):
    """The selected run's cached response surface; refuses to rebuild it (the harness roots are read-only)."""
    cp = h.response_cache_path()
    if not cp.exists():
        raise AssertionError(f"Pinned NH3 response cache missing, not rebuilding it: {cp}")
    z = np.load(cp)
    matrix, egrid = z["response"], z["EGRID"]
    if matrix.shape != (h.NSTATE, len(h.EGRID)) or not np.allclose(egrid, h.EGRID):
        raise AssertionError(f"Pinned NH3 response cache does not match the run, not rebuilding it: {cp}")
    return matrix


def threshold_tag(x):
    """Column-name tag of a parity threshold, e.g. 0.0056 -> '0p56' (the 1.1 column names)."""
    return "none" if x is None else f"{100 * x:.2f}".replace(".", "p")


def write_csv(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)


def read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def min_valid(total, mask):
    feasible = np.where(mask, total, np.inf)
    i = int(np.argmin(feasible))
    if not math.isfinite(float(feasible[i])):
        raise AssertionError("No feasible process state")
    return float(feasible[i]), i


def bisect(f, lo, hi, n=48, cap=1.0):
    """Largest x >= lo with f(x) <= 0 for f increasing in x; None if f(lo) > 0.

    [lo, hi] is the search range of the NH3-FINAL-1.1 run. If f(hi) <= 0 the root lies above it (NH3-FINAL-1.2:
    Ru/C stays at or below Fe across the 0-12 %/y owned sweep in the KAAP loop), so the bracket is moved up in steps
    of hi - lo until f changes sign, and the same bisection runs there. Not bracketed by cap -> error, not a value.
    """
    if f(lo) > 0:
        return None
    step = hi - lo
    while f(hi) <= 0:
        if hi >= cap:
            raise AssertionError(f"Parity not bracketed below {cap:.0%}/y")
        lo, hi = hi, min(hi + step, cap)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if f(mid) <= 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def documented_rates():
    contracts = read_csv(HERE / "pbf_catalyst_lease_contracts.csv")
    pbf = [float(c["annual_rate_pct"]) for c in contracts]
    if len(pbf) != 32 or len({c["contract_id"] for c in contracts}) != 32:
        raise AssertionError("Expected 32 distinct PBF contracts")
    computed = {"pbf_min": min(pbf), "pbf_median": statistics.median(pbf), "pbf_max": max(pbf)}
    rows = []
    for row in read_csv(HERE / "documented_rates.csv"):
        if row["rate_id"] in computed:
            row["rate_pct"] = f"{computed[row['rate_id']]:.4g}"
        rows.append(row)
    return rows, pbf, computed


def main():
    A = NM.anchors()
    h = NM.harness()
    matrix = pinned_response(h)
    if h.NSTATE != A["NSTATE"]:
        raise AssertionError(f"{A['label']} process-state count drifted: {h.NSTATE} vs {A['NSTATE']}")
    horizon, plant_rate, legacy_life = float(h.PLANT_LIFE_Y), float(h.DISCOUNT_RATE), float(h.CATALYST_LIFE_Y)
    if (horizon, plant_rate, legacy_life) != (25.0, 0.12, 10.0) or abs(float(hc.PRICE["Ru"]) - 53852.5) > 1e-9:
        raise AssertionError("Frozen finance anchors or Ru price drifted")
    ru_price, fe_price = float(hc.PRICE["Ru"]), float(hc.PRICE["Fe"])

    v = {m: h.interp_state_vector(matrix, hc.EN0_CANON[m]) for m in ("Fe", "Ru")}
    fe_original, fe_volume, fe_metal, _ = h.cost_arrays("Fe", v["Fe"])
    _, ru_volume, ru_metal, _ = h.cost_arrays("Ru", v["Ru"], price=ru_price / U_EXPOSURE,
                                              life_y=legacy_life, recovery=0)
    fe_nonmetal = fe_original - fe_metal
    masks = {"main": np.ones(h.NSTATE, dtype=bool),
             "KAAP": (h.state_P == 90.0) & (h.state_Tsep == -20.0)}
    fe_feasible = fe_volume <= h.V_CAP
    # The cache and cost algebra reproduce the selected run's feasible Fe and Ru headlines (results.json).
    ru_total_frozen, ru_volume_frozen, _, _ = h.cost_arrays("Ru", v["Ru"])
    run_headline = {"Fe": min_valid(fe_original, fe_feasible)[0],
                    "Ru": min_valid(ru_total_frozen, ru_volume_frozen <= h.V_CAP)[0]}
    for m, value in run_headline.items():
        if abs(value - A[m]) > TOL:
            raise AssertionError(f"{A['label']} {m} headline not reproduced: {value} vs {A[m]}")
    if not masks["KAAP"].any():
        raise AssertionError("No KAAP-type (90 bar, -20 C) process state in this run")
    bed_scale = h.ACTIVE_FRACTION * h.BED_DENSITY
    geom_cache, fe_cache = {}, {}

    def ru_geometry(w, rho):
        if (w, rho) not in geom_cache:
            vol = ru_volume * bed_scale / (U_EXPOSURE * w * rho)
            reactor = ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(vol / h.REACTOR_REF, h.REACTOR_EXP))
                       * h.crf / h.annual_output_t + h.vessel_pressure_premium(vol))
            geom_cache[(w, rho)] = (reactor + h.state_process_cost, vol <= h.V_CAP)
        return geom_cache[(w, rho)]

    def fe_cost(loop, rate):
        if (loop, rate) not in fe_cache:
            factor = annualized_metal_multiplier(
                MetalCashflow(project_y=horizon, catalyst_life_y=legacy_life,
                              discount_rate=rate, gross_recovery=0.0), fe_price, legacy_life)
            cost, _ = min_valid(fe_nonmetal + fe_metal * factor, fe_feasible & masks[loop])
            fe_cache[(loop, rate)] = cost
        return fe_cache[(loop, rate)]

    def ru_cost(loop, w, rho, factor):
        base, ok = ru_geometry(w, rho)
        return min_valid(base + ru_metal * factor, ok & masks[loop])

    def owned(loop, w, rho, physical_r, rate):
        factor = annualized_metal_multiplier(
            MetalCashflow(project_y=horizon, catalyst_life_y=legacy_life, discount_rate=rate,
                          gross_recovery=physical_r), ru_price, legacy_life)
        ru, idx = ru_cost(loop, w, rho, factor)
        fe = fe_cost(loop, rate)
        return ru, fe, idx

    def leased(loop, w, rho, physical_r, rent, collateral=0.0, refining_yield=1.0,
               processing_fee=0.0, settlement_delay=0.0):
        terms = SupplierMetalTerms(
            project_y=horizon, catalyst_life_y=legacy_life, project_discount_rate=plant_rate,
            gross_recovery=physical_r, refining_yield=refining_yield, annual_fee_fraction=rent,
            cycle_fee_fraction=0.0, deposit_fraction=collateral, deposit_refund_fraction=1.0,
            loss_settlement_price_fraction=1.0, processing_fee_USD_kg_collected=processing_fee,
            charge_delay_years=settlement_delay, terminal_return=True)
        ru, idx = ru_cost(loop, w, rho, supplier_metal_multiplier(terms, ru_price, legacy_life))
        return ru, fe_cost(loop, plant_rate), idx

    # ---- Regression 1: every row of PR #57 lifecycle_finance_sensitivity.csv (same model version) ----
    # 1.1: the committed PR #57 files (mandatory). 1.2: PR #57's nh3_1_2/ outputs when that port exists; the
    # algebra identity itself is established by the 1.1 run, so their absence is recorded, not faked.
    pr57_files = (PR57_OUT / "lifecycle_finance_sensitivity.csv", PR57_OUT / "lifecycle_dcf_report.json")
    pr57_present = all(p.exists() for p in pr57_files)
    if NM.VERSION == "1.1" and not pr57_present:
        raise AssertionError("PR #57 reference outputs missing")
    n_reg = 0
    prior = flag = None
    ru12, fe12, _ = owned(**FLAGSHIP, rate=plant_rate)
    if pr57_present:
        for row in read_csv(pr57_files[0]):
            ru, fe, _ = owned(row["loop"], float(row["w_Ru"]), float(row["rho_kg_m3"]),
                              float(row["gross_Ru_recovery"]), float(row["metal_finance_rate"]))
            if abs(ru - float(row["Ru_USD_t"])) > TOL or abs(fe - float(row["Fe_same_loop_USD_t"])) > TOL:
                raise AssertionError(f"PR #57 finance-sensitivity row not reproduced: {row}")
            n_reg += 1
        prior = json.loads(pr57_files[1].read_text(encoding="utf-8"))
        flag = prior["flagship_results"]["project_12pct_ideal"]
        if abs(ru12 - flag["Ru_USD_t"]) > TOL or abs(fe12 - flag["Fe_same_loop_USD_t"]) > TOL:
            raise AssertionError("PR #57 flagship 12 % owned result not reproduced")

    def owned_gap(rate, r=FLAGSHIP["physical_r"], w=FLAGSHIP["w"], rho=FLAGSHIP["rho"]):
        ru, fe, _ = owned("KAAP", w, rho, r, rate)
        return ru - fe

    def lease_gap(rent, variant="lease_unsecured", r=FLAGSHIP["physical_r"], w=FLAGSHIP["w"],
                  rho=FLAGSHIP["rho"]):
        ru, fe, _ = leased("KAAP", w, rho, r, rent, **LEASE_VARIANTS[variant])
        return ru - fe

    owned_hurdle = bisect(owned_gap, 0.0, plant_rate)
    if prior is not None and (owned_hurdle is None or prior["financing_hurdle_rate"] is None
                              or abs(owned_hurdle - prior["financing_hurdle_rate"]) > 1e-9):
        raise AssertionError(f"PR #57 owned financing hurdle not reproduced: {owned_hurdle}")
    if NM.VERSION == "1.1" and owned_hurdle is None:
        raise AssertionError("PR #57 owned financing hurdle (0.56 %/y) not reproduced")
    # ---- Regression 2: PR #61 owned-vs-lease anchors (PR #61 was run on 1.1 only) ----
    lease_hurdle = bisect(lease_gap, 0.0, 0.15, n=45)
    if NM.VERSION == "1.1" and (lease_hurdle is None or round(100 * lease_hurdle, 2) != 0.92):
        raise AssertionError(f"PR #61 lease parity (0.92 %/y) not reproduced: {lease_hurdle}")
    ru0, fe_lease, _ = leased("KAAP", FLAGSHIP["w"], FLAGSHIP["rho"], FLAGSHIP["physical_r"], 0.0)
    if abs(fe_lease - fe12) > TOL or (flag is not None and abs(fe_lease - flag["Fe_same_loop_USD_t"]) > TOL):
        raise AssertionError("PR #61 Fe reference differs from PR #57 12 % Fe")
    # Lease rent equal to the plant rate is the owned case at the plant rate (both versions).
    ru_rent12, _, _ = leased("KAAP", FLAGSHIP["w"], FLAGSHIP["rho"], FLAGSHIP["physical_r"], plant_rate)
    if abs(ru_rent12 - ru12) > TOL:
        raise AssertionError(f"Lease at the plant rate differs from owned at the plant rate: {ru_rent12} vs {ru12}")

    def below(rate, hurdle):
        return hurdle is not None and rate <= hurdle

    owned_col = f"owned_vs_{threshold_tag(owned_hurdle)}_threshold"
    lease_col = f"lease_vs_{threshold_tag(lease_hurdle)}_threshold"

    # ---- Documented rates ----
    rates, pbf, computed = documented_rates()
    flagship_rows = []
    for row in rates:
        if row["rate_pct"] == "":
            continue
        pct = float(row["rate_pct"])
        rate = pct / 100.0
        ru_o, fe_o, io = owned("KAAP", FLAGSHIP["w"], FLAGSHIP["rho"], FLAGSHIP["physical_r"], rate)
        out = {"rate_id": row["rate_id"], "rate_pct": pct, "category": row["category"],
               "basis": row["basis"], "metal_documented": row["metal"], "source_id": row["source_id"],
               "owned_Ru_USD_t": ru_o, "owned_Fe_USD_t": fe_o, "owned_gap_USD_t": ru_o - fe_o,
               owned_col: "below (Ru <= Fe)" if below(rate, owned_hurdle) else "above (Fe cheaper)",
               "owned_Ru_opt_T_C": float(h.state_T[io])}
        for variant in LEASE_VARIANTS:
            ru_l, fe_l, il = leased("KAAP", FLAGSHIP["w"], FLAGSHIP["rho"], FLAGSHIP["physical_r"],
                                    rate, **LEASE_VARIANTS[variant])
            out[f"{variant}_Ru_USD_t"] = ru_l
            out[f"{variant}_gap_USD_t"] = ru_l - fe_l
        out["lease_Fe_USD_t"] = fe_lease
        out[lease_col] = "below (Ru <= Fe)" if below(rate, lease_hurdle) else "above (Fe cheaper)"
        out["rate_applied_to_Ru_is"] = "inference: documented for " + row["metal"]
        flagship_rows.append(out)
    write_csv(OUT / "flagship_documented_rates.csv", flagship_rows)

    # ---- Parity thresholds by recovery (flagship bed) for each structure ----
    thresholds = []
    for r in RECOVERIES:
        rec = {"physical_recovery": r,
               "owned_parity_rate_pct": None, "lease_unsecured_parity_rent_pct": None,
               "lease_collateral25_parity_rent_pct": None, "lease_refining_loss_parity_rent_pct": None}
        x = bisect(lambda q: owned_gap(q, r=r), 0.0, plant_rate)
        rec["owned_parity_rate_pct"] = "" if x is None else 100 * x
        for variant in LEASE_VARIANTS:
            x = bisect(lambda q: lease_gap(q, variant=variant, r=r), 0.0, 0.15, n=45)
            rec[f"{variant}_parity_rent_pct"] = "" if x is None else 100 * x
        thresholds.append(rec)
    write_csv(OUT / "parity_thresholds_by_recovery.csv", thresholds)

    # ---- Robustness over the KAAP bed grid at the headline documented rates ----
    headline = {"pt_implied_pre2020": 0.0, "pt_implied_2021_avg": 0.8,
                "pbf_min": computed["pbf_min"], "pbf_median": computed["pbf_median"],
                "pbf_max": computed["pbf_max"]}
    grid_rows = []
    for rid, pct in headline.items():
        rate = pct / 100.0
        for w in LOADINGS:
            for rho in DENSITIES:
                for r in RECOVERIES:
                    ru_o, fe_o, _ = owned("KAAP", w, rho, r, rate)
                    ru_l, fe_l, _ = leased("KAAP", w, rho, r, rate)
                    grid_rows.append({"rate_id": rid, "rate_pct": pct, "w_Ru": w, "rho_kg_m3": rho,
                                      "physical_recovery": r, "owned_Ru_USD_t": ru_o,
                                      "owned_Fe_USD_t": fe_o, "owned_gap_USD_t": ru_o - fe_o,
                                      "lease_Ru_USD_t": ru_l, "lease_Fe_USD_t": fe_l,
                                      "lease_gap_USD_t": ru_l - fe_l})
    write_csv(OUT / "kaap_grid_headline_rates.csv", grid_rows)
    grid_counts = {}
    for rid in headline:
        sel = [g for g in grid_rows if g["rate_id"] == rid]
        grid_counts[rid] = {"cells": len(sel),
                            "owned_Ru_le_Fe": sum(g["owned_gap_USD_t"] <= 0 for g in sel),
                            "lease_Ru_le_Fe": sum(g["lease_gap_USD_t"] <= 0 for g in sel)}

    by_id = {r["rate_id"]: r for r in flagship_rows}
    summary = {
        "status": "unfrozen exploratory overlay on PR #57/#61 algebra; frozen NH3-FINAL-1.1 unchanged",
        "flagship": {**FLAGSHIP, "Ru_life_y": legacy_life, "project_y": horizon},
        "regressions": {"pr57_finance_sensitivity_rows_reproduced": n_reg,
                        "pr57_owned_12pct_Ru_USD_t": ru12, "pr57_owned_12pct_Fe_USD_t": fe12,
                        "owned_parity_rate": owned_hurdle, "lease_parity_rent": lease_hurdle,
                        "lease_zero_rent_Ru_USD_t": ru0, "lease_Fe_USD_t": fe_lease},
        "pbf_fixed_rates_pct": {"n": len(pbf), **computed},
        "headline": {k: {"rate_pct": by_id[k]["rate_pct"],
                         "owned_Ru_USD_t": by_id[k]["owned_Ru_USD_t"],
                         "owned_Fe_USD_t": by_id[k]["owned_Fe_USD_t"],
                         "owned_gap_USD_t": by_id[k]["owned_gap_USD_t"],
                         "lease_Ru_USD_t": by_id[k]["lease_unsecured_Ru_USD_t"],
                         "lease_Fe_USD_t": fe_lease,
                         "lease_gap_USD_t": by_id[k]["lease_unsecured_gap_USD_t"]}
                     for k in ("pt_implied_pre2020", "pt_implied_2021_avg", "pbf_min",
                               "pbf_median", "pbf_max", "evonik_owner_carrying", "frozen_plant_rate")},
        "kaap_grid_counts_27_cells": grid_counts,
        "parity_by_recovery": thresholds,
        "inference_flag": "No Ru lease or financing rate was found; Pt/Pd/Au rates applied to Ru by analogy.",
    }
    if NM.VERSION != "1.1":
        summary["status"] = (f"unfrozen exploratory overlay on PR #57/#61 algebra; {A['label']} run {A['run']}; "
                             "frozen NH3-FINAL-1.1 unchanged")
        summary["model"] = {
            "version": A["version"], "label": A["label"], "run": A["run"], "process_states": h.NSTATE,
            "F_CAL": A["F_CAL"], "headline_Fe_USD_t_reproduced": run_headline["Fe"],
            "headline_Ru_USD_t_reproduced": run_headline["Ru"], "kaap_states": int(masks["KAAP"].sum()),
            "pr57_reference": (f"reproduced from {PR57_OUT.relative_to(REPO).as_posix()}" if pr57_present else
                               "PR #57 has no nh3_1_2 outputs; its algebra is reproduced row by row under 1.1 "
                               "and the 1.2 owned 12 % values come from the same code"),
            "pr61_reference": "PR #61 lease parity 0.92 %/y is a 1.1 anchor; PR #61 has no 1.2 run",
            "lease_at_plant_rate_equals_owned_at_plant_rate": True,
            "parity_search": ("same bisection as 1.1 on [0, 12 %] (owned) and [0, 15 %] (lease); where Ru <= Fe at the "
                              "upper end the bracket moves up by its own width until the gap changes sign"),
            "owned_parity_column": owned_col, "lease_parity_column": lease_col,
        }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                                      encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
