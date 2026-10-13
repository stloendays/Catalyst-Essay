"""Independent, noncanonical fitted-domain / thermodynamic convention diagnostics.

Evaluates the pressure supports of published Fe and Ru/C rate fits against
every optimized state from PR #75; checks the two different equilibrium
conventions at matched T/P. No optimization outputs or source papers are
modified. The published literature fits are NOT independently refitted.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis" / "nh3_staged_converter_2026_10_12"))
import kinetics as K  # noqa: E402

# Rossetti 2006 fitted 50-100 bar (paper test T ~366.6-461.3 C).
# Dyson-Simon reference 150-300 atm; expressed in bar for the audit.
RU_FIT_BAR = (50.0, 100.0)
FE_FIT_BAR = (150.0 * 1.01325, 300.0 * 1.01325)
RU_FIT_C = (366.0, 462.0)

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _valid(value):
    return value is not None and math.isfinite(float(value))

def _best(rows, col, lo=None, hi=None):
    choices = [float(x[col]) for x in rows
               if x.get(col, "") not in ("", None)
               and _valid(x[col])
               and (lo is None or float(x["P_bar"]) >= lo - 1e-8)
               and (hi is None or float(x["P_bar"]) <= hi + 1e-8)]
    return min(choices) if choices else None

def _check_eq(T, P):
    # The published Ru/C kinetics are based on Gillespie-Beattie Ka and
    # Newton-Cooper fugacity coefficients. The separate PR #72 gas-standard
    # thermochemistry audit explicitly uses an IDEAL reaction equilibrium.
    ideal = float(K.equilibrium_y_nh3(T + 273.15, P, fugacity=False))
    fugacity = float(K.equilibrium_y_nh3(T + 273.15, P, fugacity=True))
    return {"T_C": T, "P_bar": P, "ideal_yNH3": ideal,
            "newton_cooper_yNH3": fugacity,
            "difference_percentage_points": 100.0 * (fugacity - ideal)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinetics", required=True, type=Path)
    ap.add_argument("--profiles", required=True, type=Path)
    ap.add_argument("--validation", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    summary = _load(args.kinetics)
    validation = _load(args.validation)

    measured = validation["Ru_C_Rossetti2006_Table2"]["all_points_N2_basis"]
    fe = validation["micropilot_430C_100bar_30000h"]["Fe_DysonSimon_KM1_vs_magnetite_8pct"]
    if measured["n"] != 125 or not 0 <= measured["mean_abs_rel_err"] <= 0.15:
        raise AssertionError("Published Ru/C fit reproduction drift; expected n=125, mean error <=15%")
    if not _valid(fe["rel_err"]) or abs(fe["rel_err"]) > 0.10:
        raise AssertionError("Published Fe source anchor drift")

    profiles = {}
    with args.profiles.open(newline="", encoding="utf-8") as f:
        for line in csv.DictReader(f):
            key = (line["states"], line["sizing"], line["scale"])
            profiles.setdefault(key, []).append(line)

    rows = []
    for v in summary["variants"]:
        key = (v["states"], v["sizing"], v["scale"])
        data = profiles[key]
        total_fe = _best(data, "Fe")
        total_ru_supported = _best(data, "Ru_C_supported_r9555")
        constrained_fe = _best(data, "Fe", *FE_FIT_BAR)
        constrained_ru_supported = _best(data, "Ru_C_supported_r9555", *RU_FIT_BAR)

        # The pressure profiles reflect the benchmark metal-loss replacement
        # accounting with 95.55% Ru recovery, NOT the DCF financing cases.
        fixed = v["Ru_C_supported"]["benchmark 0% r 0.9555"]["Ru_C_global"]
        if total_fe is None or abs(total_fe - v["Fe"]["cost"]) > 0.002:
            raise AssertionError(f"{key}: Fe pressure-cost profile fails regression")
        if total_ru_supported is None or abs(total_ru_supported - fixed["cost"]) > 0.002:
            raise AssertionError(f"{key}: Ru/C pressure-cost profile fails regression")
        if constrained_fe is not None and constrained_fe + 1e-5 < total_fe:
            raise AssertionError(f"{key}: constrained Fe improves the global optimum")
        if constrained_ru_supported is not None and constrained_ru_supported + 1e-5 < total_ru_supported:
            raise AssertionError(f"{key}: constrained Ru improves the global optimum")

        ru_c_0 = v["Ru_C_supported"]["cashflow 0% r 0.9555"]["Ru_C_global"]
        ru_c_12 = v["Ru_C_supported"]["cashflow 12% r 0.9555"]["Ru_C_global"]
        row = {
            "states": key[0], "sizing": key[1], "scale": key[2],
            "Fe_opt_P_bar": v["Fe"]["P_bar"],
            "Fe_opt_P_inside_documented_range": FE_FIT_BAR[0] <= v["Fe"]["P_bar"] <= FE_FIT_BAR[1],
            "Fe_global_USD_t": total_fe,
            "Fe_in_pressure_range_USD_t": constrained_fe,
            "Fe_pressure_penalty_USD_t": constrained_fe - total_fe if constrained_fe is not None else None,
            "RuC_opt_P_bar_zero_finance": ru_c_0["P_bar"],
            "RuC_opt_T_C_zero_finance": ru_c_0["T_C"],
            "RuC_opt_P_inside_measured_range": RU_FIT_BAR[0] <= ru_c_0["P_bar"] <= RU_FIT_BAR[1],
            "RuC_opt_T_inside_measured_range": RU_FIT_C[0] <= ru_c_0["T_C"] <= RU_FIT_C[1],
            "RuC_opt_P_bar_12pct_finance": ru_c_12["P_bar"],
            "RuC_opt_P_12pct_inside_measured_range": RU_FIT_BAR[0] <= ru_c_12["P_bar"] <= RU_FIT_BAR[1],
            "RuC_benchmark_global_USD_t": total_ru_supported,
            "RuC_benchmark_in_pressure_range_USD_t": constrained_ru_supported,
            "RuC_benchmark_pressure_penalty_USD_t":
                constrained_ru_supported - total_ru_supported if constrained_ru_supported is not None else None,
        }
        rows.append(row)

    eq_rows = [_check_eq(t, p) for t, p in ((425.0, 90.0), (400.0, 90.0),
                                               (425.0, 145.0), (425.0, 325.0))]
    if abs(eq_rows[0]["ideal_yNH3"] - 0.17642782294536968) > 1e-9:
        raise AssertionError("GB ideal reference to published fit drift")
    if abs(eq_rows[0]["newton_cooper_yNH3"] - 0.1886536481722159) > 1e-9:
        raise AssertionError("GB fugacity-reference to published fit drift")

    report = {
        "status": "UNFROZEN source-domain diagnostic; external validation NOT established",
        "ru_source_pressure_bar": RU_FIT_BAR,
        "ru_source_temperature_C": RU_FIT_C,
        "fe_source_pressure_bar": FE_FIT_BAR,
        "fe_source_pressure_basis": "150-300 atm from cited D-S reference; 1 atm=1.01325 bar",
        "rossetti_125_fit_points_MARE": measured["mean_abs_rel_err"],
        "rossetti_fit_points_n": measured["n"],
        "fe_micropilot_single_point_relative_error": fe["rel_err"],
        "n_variants": len(rows),
        "ru_opt_zero_finance_outside_fitted_pressure_count":
            sum(not row["RuC_opt_P_inside_measured_range"] for row in rows),
        "ru_opt_12pct_finance_outside_fitted_pressure_count":
            sum(not row["RuC_opt_P_12pct_inside_measured_range"] for row in rows),
        "fugacity_convention_check": eq_rows,
        "variants": rows,
        "warnings": [
            "Ru fit accuracy is calculated on published model-fitting records, not a held-out industrial validation cohort",
            "Even a source-domain pressure does not establish validated supported 8 wt% Ru/C rate after extrapolating the original 3.2 wt% catalyst",
            "PR #75 process-state equilibrium was rebuilt from GB ideal gas standard Gibbs; Ru/C rate law uses Newton-Cooper high-pressure fugacity coefficients",
            "The reported equilibrium mismatch is quantified, not dynamically corrected here; no single thermodynamically closed NH3-FINAL-1.2 core is claimed",
            "Constrained pressure-profile cost only applies to benchmark loss-only accounting at r=95.55%; DCF financing optimization is not recalculated under source pressure limits",
            "Fe fit support in atm is converted to bar; the original Fe kinetics are not independently refitted",
        ],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "source_domain.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (args.out / "source_domain.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    md = [
        "# Source domain / fugacity audit (noncanonical)",
        "",
        f'- Rossetti 2006 reproduced {measured["n"]} published fit points; mean absolute relative error {measured["mean_abs_rel_err"]:.1%}.',
        f'- Supported Ru/C zero-finance optimum is outside the original 50-100 bar Ru/C fit in **{report["ru_opt_zero_finance_outside_fitted_pressure_count"]}/8** variant scenarios.',
        f'- Supported Ru/C 12%-finance optimum is outside the fit in **{report["ru_opt_12pct_finance_outside_fitted_pressure_count"]}/8** variants.',
        "- The published Ru/C fit concerns 3.2 wt% Ru/C. Modeling 8 wt% at equal per-kg-Ru activity is an extrapolation.",
        "",
        "| T (C) | P (bar) | GB ideal yNH3 | Newton-Cooper yNH3 | gap (percentage points) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for x in eq_rows:
        md.append(f'| {x["T_C"]:.0f} | {x["P_bar"]:.0f} | {x["ideal_yNH3"]:.4f} | {x["newton_cooper_yNH3"]:.4f} | {x["difference_percentage_points"]:+.2f} |')
    md += [
        "",
        "This is a **physical-closure warning**, not a CI error. The GB gas standard Gibbs reference is aligned, but loop equilibrium and kinetic rates still use different ideal/fugacity conventions. The full axial industrial plant and fitted pressure range are NOT validated.",
        "",
        "Pressure-constrained profile penalties describe only the 95.55%-recovery straight-line replacement benchmark; do not extrapolate them to 25-year DCF cases.",
        "",
    ]
    (args.out / "SOURCE_DOMAIN.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))

if __name__ == "__main__":
    main()
