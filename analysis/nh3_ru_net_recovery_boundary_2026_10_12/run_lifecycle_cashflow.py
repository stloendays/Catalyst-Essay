"""Run an explicit, finite-25-year Fe/Ru metal cash-flow comparison.

This extends PR #57 without rewriting frozen NH3-FINAL-1.1. A metal inventory
is purchased at 0, L, 2L ... before plant closure; spent catalyst is processed
on replacement, and final metal recovery is credited at plant retirement.
Recycling fees are paid at collection; metal sale receipts can be delayed.

All recovery yields, fees and settlement lags beyond the source gross recovery
examples are scenario values, NOT literature-verified industrial contracts.
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

from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier
import harness_core as hc


R_VALUES = (0.90, 0.9305, 0.9555)
LOADINGS = (0.05, 0.08, 0.10)
DENSITIES = (430.0, 490.0, 550.0)
RU_LIVES = (5.0, 10.0, 15.0)
RATES = (0.0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.12)


def csv_write(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)


def min_valid(total, mask):
    feasible = np.where(mask, total, np.inf)
    i = int(np.argmin(feasible))
    if not math.isfinite(float(feasible[i])):
        raise AssertionError("No feasible process states for this model scenario")
    return float(feasible[i]), i


def main():
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), ROOT)
    matrix, _, cached = h.build_or_load_response()
    if not cached or h.NSTATE != 14136:
        raise AssertionError("The pinned NH3 response cache must be used, not regenerated")
    v = {m: h.interp_state_vector(matrix, hc.EN0_CANON[m]) for m in ("Fe", "Ru")}
    if not np.isfinite(v["Fe"]).all() or not np.isfinite(v["Ru"]).all():
        raise AssertionError("Missing descriptor columns in the frozen response cache")
    # The discount rate and project lifetime below come from the FROZEN manifest,
    # not user-made pricing assumptions.
    horizon = float(h.PLANT_LIFE_Y)
    plant_rate = float(h.DISCOUNT_RATE)
    legacy_life = float(h.CATALYST_LIFE_Y)
    if abs(horizon - 25.0) > 1e-9 or abs(plant_rate - 0.12) > 1e-9 or abs(legacy_life - 10.0) > 1e-9:
        raise AssertionError("The frozen finance/lifetime anchors have changed")
    if abs(float(hc.PRICE["Ru"]) - 53852.5) > 1e-9:
        raise AssertionError("Ru procurement price has changed")
    u = 11.0

    fe_original, fe_volume, fe_metal, _fe_reactor = h.cost_arrays("Fe", v["Fe"])
    _ru_original, ru_volume, ru_metal, _ru_reactor = h.cost_arrays(
        "Ru", v["Ru"], price=hc.PRICE["Ru"] / u, life_y=legacy_life, recovery=0)
    fe_nonmetal = fe_original - fe_metal
    kaap_mask = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    masks = {"main": np.ones(h.NSTATE, dtype=bool), "KAAP": kaap_mask}
    fe_feasible = fe_volume <= h.V_CAP
    bed_scale = h.ACTIVE_FRACTION * h.BED_DENSITY

    fe_cache = {}
    ru_geometries = {}

    def get_geometry(w, rho):
        key = (w, rho)
        if key not in ru_geometries:
            actual_v = ru_volume * bed_scale / (u * w * rho)
            reactor = ((h.REACTOR_FIXED
                        + h.REACTOR_VAR * np.power(actual_v / h.REACTOR_REF, h.REACTOR_EXP))
                       * h.crf / h.annual_output_t + h.vessel_pressure_premium(actual_v))
            ru_geometries[key] = (reactor + h.state_process_cost, actual_v <= h.V_CAP)
        return ru_geometries[key]

    def get_fe_cost(loop, rate):
        key = (loop, rate)
        if key not in fe_cache:
            fe_case = MetalCashflow(project_y=horizon, catalyst_life_y=legacy_life,
                                   discount_rate=rate, gross_recovery=0.0)
            factor = annualized_metal_multiplier(fe_case, hc.PRICE["Fe"], legacy_life)
            cost, state = min_valid(fe_nonmetal + fe_metal * factor, fe_feasible & masks[loop])
            fe_cache[key] = (cost, state, factor)
        return fe_cache[key]

    def evaluate(loop, w, rho, ru_life, physical_r, discount_rate, yield_sale=1.0,
                 sale_fraction=1.0, fee_per_collected_kg=0.0, sale_delay_y=0.0,
                 terminal_recovery=True, project_y=None):
        years = horizon if project_y is None else project_y
        fe_case = MetalCashflow(project_y=years, catalyst_life_y=legacy_life,
                               discount_rate=discount_rate, gross_recovery=0.0)
        if project_y is None and terminal_recovery:
            fe_cost, fe_state, fe_factor = get_fe_cost(loop, discount_rate)
        else:
            fe_factor = annualized_metal_multiplier(fe_case, hc.PRICE["Fe"], legacy_life)
            fe_cost, fe_state = min_valid(fe_nonmetal + fe_metal * fe_factor,
                                          fe_feasible & masks[loop])
        ru_case = MetalCashflow(project_y=years, catalyst_life_y=ru_life,
                               discount_rate=discount_rate, gross_recovery=physical_r,
                               refining_yield=yield_sale, sale_price_fraction=sale_fraction,
                               processing_fee_USD_kg_collected=fee_per_collected_kg,
                               sale_delay_y=sale_delay_y, terminal_recovery=terminal_recovery)
        ru_factor = annualized_metal_multiplier(ru_case, hc.PRICE["Ru"], legacy_life)
        nonmetal, feasible = get_geometry(w, rho)
        ru_cost, ru_state = min_valid(nonmetal + ru_metal * ru_factor, feasible & masks[loop])
        return {"Fe_same_loop_USD_t": fe_cost, "Ru_USD_t": ru_cost,
                "gap_Ru_minus_Fe_USD_t": ru_cost - fe_cost,
                "Ru_metal_factor": ru_factor, "Fe_metal_factor": fe_factor,
                "Ru_opt_T_C": float(h.state_T[ru_state]),
                "Ru_opt_P_bar": float(h.state_P[ru_state]),
                "Ru_opt_Tsep_C": float(h.state_Tsep[ru_state]),
                "Fe_opt_P_bar": float(h.state_P[fe_state])}

    # Independent 24-point regression: a zero-discount *20-year* project with
    # full final resale reproduces the legacy 10-year straight-line algebra
    # exactly, while the project-consistent primary analysis is 25 years.
    regressions = []
    with (HERE / "cost_surface.csv").open(newline="", encoding="utf-8") as fh:
        frozen_overlay = list(csv.DictReader(fh))
    selected = [x for x in frozen_overlay
                if float(x["net_realization"]) == 1.0
                and float(x["recovery"]) in (0.90, 0.9555)
                and float(x["rho_kg_m3"]) in (430.0, 550.0)]
    assert len(selected) == 24
    for row in selected:
        loop = row["loop"]
        result = evaluate(loop, float(row["w_Ru"]), float(row["rho_kg_m3"]),
                          10, float(row["recovery"]), 0.0, project_y=20)
        delta = result["Ru_USD_t"] - float(row["Ru_cost_USD_t"])
        fdelta = result["Fe_same_loop_USD_t"] - float(row["Fe_same_loop_USD_t"])
        if abs(delta) > 1e-9 or abs(fdelta) > 1e-9:
            raise AssertionError("Finite cash flow does not recover original cost benchmark")
        regressions.append({"loop": loop, "recovery": row["recovery"],
                            "w_Ru": row["w_Ru"], "rho_kg_m3": row["rho_kg_m3"],
                            "Ru_cost_difference_USD_t": delta, "Fe_cost_difference_USD_t": fdelta})
    csv_write(HERE / "lifecycle_legacy_regression.csv", regressions)

    cases = [
        ("zero_carrying_ideal", 0.0, 1.0, 1.0, 0.0, 0.0),
        ("project_12pct_ideal", plant_rate, 1.0, 1.0, 0.0, 0.0),
        ("project_12pct_mild_losses", plant_rate, 0.95, 0.95, 500.0, 0.5),
        ("project_12pct_stress_losses", plant_rate, 0.85, 0.90, 1500.0, 1.0),
    ]
    scenario_rows = []
    for label, rate, sale_yield, fraction, fee, delay in cases:
        for loop in ("main", "KAAP"):
            for w in LOADINGS:
                for rho in DENSITIES:
                    for r in R_VALUES:
                        for life in RU_LIVES:
                            result = evaluate(loop, w, rho, life, r, rate, sale_yield, fraction, fee, delay)
                            scenario_rows.append({
                                "scenario": label, "loop": loop, "w_Ru": w, "rho_kg_m3": rho,
                                "Ru_life_y": life, "gross_Ru_recovery": r,
                                "metal_finance_rate": rate, "refining_yield": sale_yield,
                                "payout_fraction": fraction, "processing_fee_USD_kg_collected": fee,
                                "sale_delay_y": delay, **result})
    csv_write(HERE / "lifecycle_cost_scenarios.csv", scenario_rows)
    assert len(scenario_rows) == 648

    rate_rows = []
    for loop in ("main", "KAAP"):
        for w in LOADINGS:
            for rho in DENSITIES:
                for r in R_VALUES:
                    for rate in RATES:
                        result = evaluate(loop, w, rho, 10.0, r, rate)
                        rate_rows.append({"loop": loop, "w_Ru": w, "rho_kg_m3": rho,
                                          "gross_Ru_recovery": r, "Ru_life_y": 10.0,
                                          "metal_finance_rate": rate, **result})
    csv_write(HERE / "lifecycle_finance_sensitivity.csv", rate_rows)
    assert len(rate_rows) == 378

    # A purely conditional financing hurdle is solved only after a coarse
    # monotonicity check. It is NOT a commercial catalyst lease quotation.
    critical_case = dict(loop="KAAP", w=0.08, rho=490.0, ru_life=10.0, physical_r=0.9555)
    def gap_at(rate, **extra):
        return evaluate(discount_rate=rate, **critical_case, **extra)["gap_Ru_minus_Fe_USD_t"]
    coarse = [gap_at(float(r)) for r in np.linspace(0.0, plant_rate, 25)]
    if any(coarse[i+1] < coarse[i] - 1e-8 for i in range(len(coarse)-1)):
        critical_rate = None
        critical_note = "No monotonic rate threshold: inspected grid has nonmonotone cost gaps"
    elif coarse[0] < 0 and coarse[-1] > 0:
        lo, hi = 0.0, plant_rate
        for _ in range(48):
            mid = (lo + hi) / 2
            if gap_at(mid) <= 0:
                lo = mid
            else:
                hi = mid
        critical_rate = (lo + hi) / 2
        critical_note = "Metal inventory financing hurdle at 95.55% Ru recovery, ideal sale"
    else:
        critical_rate = None
        critical_note = "The financing-rate sweep does not bracket a parity threshold"

    def price_fraction_threshold(rate):
        if gap_at(rate, sale_fraction=1.0) > 0:
            return None
        if gap_at(rate, sale_fraction=0.0) <= 0:
            return 0.0
        lo, hi = 0.0, 1.0
        for _ in range(48):
            mid = (lo + hi) / 2
            if gap_at(rate, sale_fraction=mid) <= 0:
                hi = mid
            else:
                lo = mid
        return hi

    flagship = {}
    for label, rate, yield_sale, payout, fee, delay in cases:
        flagship[label] = evaluate(discount_rate=rate, **critical_case,
                                   yield_sale=yield_sale, sale_fraction=payout,
                                   fee_per_collected_kg=fee, sale_delay_y=delay)
    summary = {
        "status": "exploratory finite-horizon metal DCF overlay; original frozen science unchanged",
        "frozen_plant_years": horizon, "frozen_plant_discount_rate": plant_rate,
        "frozen_catalyst_life_y": legacy_life, "financing_rate_interpretation":
        "metal-specific project discount/carrying rate; other reactor/process costs stay frozen at 12%/25y",
        "Ru_original_metal_price_USD_kg": hc.PRICE["Ru"], "Ru_exposure_multiplier_u": u,
        "rows_scenarios": len(scenario_rows), "rows_rate_sensitivity": len(rate_rows),
        "rows_legacy_crosscheck": len(regressions),
        "flagship_geometry": critical_case, "flagship_results": flagship,
        "financing_hurdle_rate": critical_rate, "financing_hurdle_explanation": critical_note,
        "sale_fraction_threshold_if_zero_metal_finance": price_fraction_threshold(0.0),
        "sale_fraction_threshold_if_12pct_metal_finance": price_fraction_threshold(plant_rate),
        "source_assumptions": "Only 90/93.05/95.55% gross recovery is linked to promoted spent Ru/C source examples; 85/95% metallization yields, payout fractions, fees and delays are uncalibrated scenario stresses",
        "model_limitations": [
            "gross recovery reported for salts is not verified saleable metal recovery",
            "same-mask Fe in Ru-specific KAAP converter is an unvalidated engineering replacement scenario",
            "fixed 14,136-state isothermal process grid and frozen cost coefficients",
            "last partially used Ru bed credited at plant closure (optimistic terminal salvage)",
            "same mass loading and constant nominal metal price at each replacement; no volatility",
            "uniform production and sale proceeds as annuity equivalents; no tax or working-capital loan contract",
        ],
    }
    (HERE / "lifecycle_dcf_report.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.2, 5.1), constrained_layout=True)
    for r in R_VALUES:
        selected = [x for x in rate_rows if x["loop"] == "KAAP"
                    and x["w_Ru"] == 0.08 and x["rho_kg_m3"] == 490.0
                    and x["gross_Ru_recovery"] == r]
        selected.sort(key=lambda x: x["metal_finance_rate"])
        ax.plot([100*x["metal_finance_rate"] for x in selected],
                [x["gap_Ru_minus_Fe_USD_t"] for x in selected],
                marker="o", label=f"Gross recovery {100*r:.2f}%")
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.axvline(100*plant_rate, linestyle=":", linewidth=1, label="Frozen plant discount rate")
    if critical_rate is not None:
        ax.scatter([critical_rate*100], [0], zorder=6)
    ax.set_xlabel("Metal inventory financing/discount rate (% per year)")
    ax.set_ylabel("Ru - Fe same-loop cost (USD/t NH3)")
    ax.set_title("KAAP-type loop, 8 wt% Ru/C, 490 kg/m3, 25-year cash-flow horizon")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.20)
    fig.savefig(HERE / "lifecycle_financing_break_even.png", dpi=200)
    plt.close(fig)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
