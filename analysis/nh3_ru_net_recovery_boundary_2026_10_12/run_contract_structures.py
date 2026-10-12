"""Evaluate supplier-owned Ru lease/consignment versus owned/buyback metal.

This is an additive NH3-FINAL-1.1 financing audit: 14,136 process states
are reused exactly, same Fe reference and the same 12% discount rate for
ALL operator cash flows. Supplier quotations are NOT claimed to exist.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path(os.environ.get("NH3_HARNESS", "/tmp/nh3_harness"))
RUN = ROOT / "outputs" / "nh3_final_20260905T134204Z"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import harness_core as hc
from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier
from supplier_metal_contracts import (SupplierMetalTerms, owned_metal_multiplier,
                                      supplier_metal_multiplier)

LOADINGS = (0.05, 0.08, 0.10)
DENSITIES = (430.0, 490.0, 550.0)
RECOVERIES = (0.90, 0.9305, 0.9555)
LEASE_RATES = (0.0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.12)
CONSIGNMENT_CYCLE_FEES = (0.0, 0.005, 0.01, 0.02, 0.04)
BUYBACK_PAYOUT_FLOORS = (0.8, 0.9, 0.95, 1.0)


def save_csv(filename, records):
    with (HERE / filename).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def optimized(arr, feasible):
    masked = np.where(feasible, arr, np.inf)
    ix = int(np.argmin(masked))
    out = float(masked[ix])
    if not math.isfinite(out):
        raise AssertionError("A contract removes every physically feasible process state")
    return out, ix


def bisect_fair_rent(f):
    """Largest annual fee rate with Ru <= Fe, if any in 0..15%."""
    if f(0.0) > 1e-10:
        return None
    if f(0.15) <= 0:
        return 0.15
    left, right = 0.0, 0.15
    for _ in range(45):
        mid = (left + right) / 2
        if f(mid) <= 0.0:
            left = mid
        else:
            right = mid
    return (left + right) / 2


def main():
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), ROOT)
    response, _, cached = h.build_or_load_response()
    if not cached or h.NSTATE != 14136:
        raise AssertionError("Missing or changed frozen NH3 state response")
    if abs(float(h.DISCOUNT_RATE) - 0.12) > 1e-12 or abs(float(h.PLANT_LIFE_Y) - 25.0) > 1e-12:
        raise AssertionError("Project finance assumptions drifted")
    if abs(float(h.CATALYST_LIFE_Y) - 10.0) > 1e-12:
        raise AssertionError("Fe replacement-life basis drifted")
    if abs(float(hc.PRICE["Ru"]) - 53852.5) > 1e-9:
        raise AssertionError("Frozen Ru price drifted")

    v = {m: h.interp_state_vector(response, hc.EN0_CANON[m]) for m in ("Fe", "Ru")}
    assert all(np.isfinite(vec).all() for vec in v.values())
    u = 11.0
    ru_price = hc.PRICE["Ru"]
    horizon = float(h.PLANT_LIFE_Y)
    rate = float(h.DISCOUNT_RATE)
    legacy_life = float(h.CATALYST_LIFE_Y)
    fe_orig, fe_v, fe_metal, _ = h.cost_arrays("Fe", v["Fe"])
    fe_proc = fe_orig - fe_metal
    _ru_orig, ru_bench_v, ru_metal, _ = h.cost_arrays(
        "Ru", v["Ru"], price=ru_price / u, recovery=0.0, life_y=legacy_life)
    main_mask = np.ones(h.NSTATE, dtype=bool)
    kaap_mask = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    masks = {"main": main_mask, "KAAP": kaap_mask}
    fe_multiplier = annualized_metal_multiplier(
        MetalCashflow(horizon, legacy_life, rate, 0.0),
        hc.PRICE["Fe"], legacy_life)
    fe_ref = {loop: optimized(fe_proc + fe_metal * fe_multiplier,
                              (fe_v <= h.V_CAP) & mask)[0]
              for loop, mask in masks.items()}

    geom = {}
    def nonmetal(w, rho):
        key = (w, rho)
        if key not in geom:
            reactor_v = ru_bench_v * (h.ACTIVE_FRACTION * h.BED_DENSITY / (u * w * rho))
            vessel_cost = ((h.REACTOR_FIXED
                            + h.REACTOR_VAR * np.power(reactor_v / h.REACTOR_REF, h.REACTOR_EXP))
                           * h.crf / h.annual_output_t + h.vessel_pressure_premium(reactor_v))
            geom[key] = (vessel_cost + h.state_process_cost, reactor_v <= h.V_CAP)
        return geom[key]

    def evaluate(loop, w, rho, metal_factor):
        base, ok = nonmetal(w, rho)
        total, idx = optimized(base + ru_metal * metal_factor, ok & masks[loop])
        return (total, total - fe_ref[loop], idx)

    def supplier(physical_r, *, annual_rent=0.0, cycle_fee=0.0, collateral=0.0,
                 refining_yield=1.0, processing_fee=0.0, settlement_delay=0.0):
        terms = SupplierMetalTerms(
            project_y=horizon, catalyst_life_y=legacy_life,
            project_discount_rate=rate, gross_recovery=physical_r,
            refining_yield=refining_yield, annual_fee_fraction=annual_rent,
            cycle_fee_fraction=cycle_fee, deposit_fraction=collateral,
            deposit_refund_fraction=1.0, loss_settlement_price_fraction=1.0,
            processing_fee_USD_kg_collected=processing_fee,
            charge_delay_years=settlement_delay, terminal_return=True)
        return supplier_metal_multiplier(terms, ru_price, legacy_life)

    def buyer(physical_r, payout):
        return owned_metal_multiplier(
            project_y=horizon, catalyst_life_y=legacy_life,
            discount_rate=rate, metal_price_USD_kg=ru_price,
            gross_recovery=physical_r, payout_fraction=payout,
            legacy_life_y=legacy_life)

    with (HERE / "lifecycle_dcf_report.json").open(encoding="utf-8") as f:
        prev = json.load(f)
    if abs(fe_ref["KAAP"] - prev["flagship_results"]["project_12pct_ideal"]["Fe_same_loop_USD_t"]) > 1e-9:
        raise AssertionError("Fe DCF reference changed")
    prior_ru_ideal = prev["flagship_results"]["project_12pct_ideal"]["Ru_USD_t"]
    ru_full, _, _ = evaluate("KAAP", .08, 490, buyer(.9555, 1.0))
    if abs(ru_full - prior_ru_ideal) > 1e-9:
        raise AssertionError("Owned/guaranteed buyback must match existing owned DCF")

    rows = []
    def add(mode, loop, w, rho, physical_r, contract_fee, metal_factor,
            *, collateral=0.0, refining_yield=1.0, sale_floor=None):
        cost, gap, ix = evaluate(loop, w, rho, metal_factor)
        rows.append({
            "contract_mode": mode,
            "loop": loop, "Ru_loading": w, "bed_density_kg_m3": rho,
            "physical_recovery": physical_r, "ru_life_y": legacy_life,
            "project_discount_rate": rate,
            "annual_lease_fee_fraction": contract_fee if mode.startswith("lease") else 0.0,
            "consignment_cycle_fee_fraction": contract_fee if mode.startswith("consignment") else 0.0,
            "buyback_payout_floor_fraction": "" if sale_floor is None else sale_floor,
            "collateral_fraction": collateral, "refining_yield": refining_yield,
            "metal_multiplier": metal_factor,
            "Ru_cost_USD_t": cost, "Fe_same_loop_USD_t": fe_ref[loop],
            "gap_Ru_minus_Fe_USD_t": gap,
            "Ru_wins_same_loop": gap < -1e-9,
            "Ru_beats_global_Fe": cost < fe_ref["main"] - 1e-9,
            "Ru_opt_T_C": float(h.state_T[ix]),
            "Ru_opt_P_bar": float(h.state_P[ix]),
            "Ru_opt_Tsep_C": float(h.state_Tsep[ix]),
        })

    for loop in ("main", "KAAP"):
        for w in LOADINGS:
            for rho in DENSITIES:
                for r in RECOVERIES:
                    add("owned_ideal", loop, w, rho, r, 0.0, buyer(r, 1.0), sale_floor=1.0)
                    for fraction in BUYBACK_PAYOUT_FLOORS[:-1]:
                        add("owned_guaranteed_buyback_scenario", loop, w, rho, r, fraction,
                            buyer(r, fraction), sale_floor=fraction)
                    for f in LEASE_RATES:
                        add("lease_unsecured", loop, w, rho, r, f,
                            supplier(r, annual_rent=f))
                        add("lease_collateral25", loop, w, rho, r, f,
                            supplier(r, annual_rent=f, collateral=.25), collateral=.25)
                        add("lease_refining_loss", loop, w, rho, r, f,
                            supplier(r, annual_rent=f, refining_yield=.95,
                                     processing_fee=500.0, settlement_delay=.5),
                            refining_yield=.95)
                    for f in CONSIGNMENT_CYCLE_FEES:
                        add("consignment_cycle_service", loop, w, rho, r, f,
                            supplier(r, cycle_fee=f))
                        add("consignment_secured25", loop, w, rho, r, f,
                            supplier(r, cycle_fee=f, collateral=.25),
                            collateral=.25)
    assert len(rows) == 1890, len(rows)
    save_csv("contract_cost_surface.csv", rows)

    thresholds = []
    for loop in ("main", "KAAP"):
        for w in LOADINGS:
            for rho in DENSITIES:
                for r in RECOVERIES:
                    for mode, kwargs in (
                        ("lease_unsecured", {}),
                        ("lease_collateral25", {"collateral": 0.25}),
                        ("lease_refining_loss", {"refining_yield": .95,
                                                "processing_fee": 500.0,
                                                "settlement_delay": .5}),
                    ):
                        f = lambda rent: evaluate(loop, w, rho, supplier(
                            r, annual_rent=rent, **kwargs))[1]
                        critical = bisect_fair_rent(f)
                        thresholds.append({
                            "loop": loop, "Ru_loading": w, "bed_density_kg_m3": rho,
                            "physical_recovery": r, "contract_mode": mode,
                            "maximum_annual_lease_fee_fraction_for_Ru_parity":
                            "" if critical is None else critical,
                            "Ru_parity_at_zero_rent": f(0.0) <= 0.0,
                            "at_15pct_rent_Ru_still_cheaper": f(.15) <= 0.0,
                            "Fe_same_loop_USD_t": fe_ref[loop]})
    assert len(thresholds) == 162
    save_csv("contract_parity_thresholds.csv", thresholds)

    def select(loop, mode, r, w=.08, rho=490.0, annual_rate=None, cycle_rate=None,
               sale_floor=None):
        matched = [x for x in rows if x["loop"] == loop and x["contract_mode"] == mode
                   and x["physical_recovery"] == r and x["Ru_loading"] == w
                   and x["bed_density_kg_m3"] == rho
                   and (annual_rate is None or x["annual_lease_fee_fraction"] == annual_rate)
                   and (cycle_rate is None or x["consignment_cycle_fee_fraction"] == cycle_rate)
                   and (sale_floor is None or x["buyback_payout_floor_fraction"] == sale_floor)]
        if len(matched) != 1:
            raise AssertionError(f"Ambiguous result: {mode}/{annual_rate}/{cycle_rate}")
        x = matched[0]
        return {"Ru_USD_t": x["Ru_cost_USD_t"],
                "Fe_same_loop_USD_t": x["Fe_same_loop_USD_t"],
                "Ru_minus_Fe_USD_t": x["gap_Ru_minus_Fe_USD_t"]}

    anchor = {
        "owned_ideal": select("KAAP", "owned_ideal", .9555),
        "buyback_floor_90pct": select("KAAP", "owned_guaranteed_buyback_scenario", .9555, sale_floor=.9),
        "lease_rent_0pct": select("KAAP", "lease_unsecured", .9555, annual_rate=0.0),
        "lease_rent_1pct": select("KAAP", "lease_unsecured", .9555, annual_rate=.01),
        "lease_rent_2pct": select("KAAP", "lease_unsecured", .9555, annual_rate=.02),
        "lease_rent_4pct": select("KAAP", "lease_unsecured", .9555, annual_rate=.04),
        "lease_rent_2pct_secured": select("KAAP", "lease_collateral25", .9555, annual_rate=.02),
        "consign_cycle_fee_1pct": select("KAAP", "consignment_cycle_service", .9555, cycle_rate=.01),
        "consign_cycle_fee_2pct": select("KAAP", "consignment_cycle_service", .9555, cycle_rate=.02),
    }
    summary_counts = {}
    for mode in sorted({x["contract_mode"] for x in rows}):
        summary_counts[mode] = {}
        for loop in ("main", "KAAP"):
            matches = [x for x in rows if x["contract_mode"] == mode and x["loop"] == loop]
            summary_counts[mode][loop] = {
                "Ru_wins": sum(bool(x["Ru_wins_same_loop"]) for x in matches),
                "total": len(matches)}
    critical = [x for x in thresholds if x["loop"] == "KAAP" and
                x["Ru_loading"] == .08 and x["bed_density_kg_m3"] == 490 and
                x["physical_recovery"] == .9555]
    final = {
        "study": "Ru/Fe supplier-metal contract structure stress: ownership vs leasing vs consignment",
        "status": "pure scenario model; not an observed Ru/C rental quote",
        "frozen_process_states": h.NSTATE,
        "frozen_discount_rate": rate,
        "Fe_metal_factor_25y": fe_multiplier,
        "Fe_cost_USD_t": fe_ref,
        "Ru_price_per_kg_frozen": ru_price,
        "exposed_atom_multiplier_u": u,
        "rows_surface": len(rows), "rows_rent_thresholds": len(thresholds),
        "owned_DCF_regression_to_prior": abs(ru_full-prior_ru_ideal),
        "anchor": anchor,
        "anchor_lease_hurdles": {x["contract_mode"]:
            x["maximum_annual_lease_fee_fraction_for_Ru_parity"] for x in critical},
        "win_counts_over_deterministic_grid": summary_counts,
        "source_scope": "Public BASF ECMS documents confirm leasing/consignment for PGM category; Heraeus confirms Ru trading/recycling/weight account; none substantiates commercial NH3 Ru/C pricing or contract rate.",
        "contract_assumptions": {
            "lease": "Supplier retains metal title; end-of-year rental charged on starting Ru metal value; the operator must cover fine-metal shortfall at each retirement; no double charge for supplier-owned metal principal.",
            "consignment": "Supplier retains metal title; fee at each catalyst loading; no periodic rental in this hypothetical scenario. Real consignment may include finance fees.",
            "owned_buyback": "Operator purchases each Ru loading; sale credits are discounted at plant rate with an assumed floor payout; no evidence of commercial Ru buyback floor.",
            "collateral": "Repayable security posted at year 0, returned at plant closure; any shortfall is billed separately, not netted again against collateral.",
            "limitations": "Ru salt collection and fine-metal yield not validated; no metal price volatility, insurance, inventory margin calls, taxes or actual quote; same-mask Fe KAAP retrofit is not a verified plant option.",
        }
    }
    (HERE / "contract_terms_report.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.1, 4.5), constrained_layout=True)
    for mode, title in (("lease_unsecured", "Supplier-owned lease"),
                        ("lease_collateral25", "Lease, 25% refundable collateral"),
                        ("lease_refining_loss", "Lease, 95% refining yield")):
        sample = [x for x in rows if x["loop"] == "KAAP" and x["Ru_loading"] == .08
                  and x["bed_density_kg_m3"] == 490 and x["physical_recovery"] == .9555
                  and x["contract_mode"] == mode]
        sample.sort(key=lambda x: x["annual_lease_fee_fraction"])
        axes[0].plot([100*x["annual_lease_fee_fraction"] for x in sample],
                     [x["gap_Ru_minus_Fe_USD_t"] for x in sample],
                     marker="o", label=title)
    axes[0].axhline(0, linewidth=1, linestyle="--")
    axes[0].axhline(anchor["owned_ideal"]["Ru_minus_Fe_USD_t"], linewidth=1,
                    linestyle=":", label="Operator-owned Ru")
    axes[0].set_xlabel("Annual metal leasing charge (% of Ru value)")
    axes[0].set_ylabel("Ru - Fe same-loop cost (USD/t NH3)")
    axes[0].set_title("(a) Annual lease structures")
    axes[0].legend(fontsize=7)
    axes[0].grid(alpha=.2)

    for mode, label in (("consignment_cycle_service", "Consignment, no collateral"),
                        ("consignment_secured25", "Consignment, 25% refundable collateral")):
        sample = [x for x in rows if x["loop"] == "KAAP" and x["Ru_loading"] == .08
                  and x["bed_density_kg_m3"] == 490 and x["physical_recovery"] == .9555
                  and x["contract_mode"] == mode]
        sample.sort(key=lambda x: x["consignment_cycle_fee_fraction"])
        axes[1].plot([100*x["consignment_cycle_fee_fraction"] for x in sample],
                     [x["gap_Ru_minus_Fe_USD_t"] for x in sample],
                     marker="o", label=label)
    axes[1].axhline(0, linewidth=1, linestyle="--")
    axes[1].axhline(anchor["owned_ideal"]["Ru_minus_Fe_USD_t"], linewidth=1,
                    linestyle=":", label="Operator-owned Ru")
    axes[1].set_xlabel("Contract fee each metal loading (% Ru value)")
    axes[1].set_ylabel("Ru - Fe same-loop cost (USD/t NH3)")
    axes[1].set_title("(b) Supplier consignment structures")
    axes[1].legend(fontsize=7)
    axes[1].grid(alpha=.2)
    fig.suptitle("KAAP-type model: 8 wt% Ru/C, rho=490 kg/m3, r=95.55%, 12% plant DCF",
                 fontsize=11)
    fig.savefig(HERE / "contract_structure_parity.png", dpi=200)
    plt.close(fig)
    print(json.dumps(final, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
