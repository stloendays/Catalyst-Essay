#!/usr/bin/env python3
"""Reference-grounded, no-fit NH3 saturation/VLE diagnostic for the industrial benchmark.

The Ullmann/BASF table describes NH3 saturated over liquid ammonia in a 1:3
N2/H2 gas mixture; it is NOT a complete industrial loop state. Interpolation
does not fit parameters, and optional loop propagation is an explicitly
noncanonical counterfactual, never a replacement for any registered score.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from audit_industrial import SRC, V12, PINS, enforce_pin, rows

HERE = Path(__file__).resolve().parent
CASE_PIN = "3a4116999a8c6765154970e057f46be3c82a420f"
T_GRID = (-30, -20, -10, 0, 10, 20, 30)
P_GRID = (10, 15, 20, 30)  # MPa
INLETS = ("A01", "A04", "A07", "A14", "A16")


def psat_nh3_bar(t_c: float) -> float:
    """The canonical model's original Antoine correlation, independently evaluated."""
    t = t_c + 273.15
    if t < 239.6:
        a, b, c = 3.18757, 506.713, -80.78
    else:
        a, b, c = 4.86886, 1113.928, -10.409
    return 10.0 ** (a - b / (t + c))


def grid_from_printed_sources():
    enforce_pin(SRC / "reference_values.csv", PINS["reference_values.csv"])
    enforce_pin(V12 / "results_cases.json", CASE_PIN)
    reference = rows(SRC / "reference_values.csv")
    stored = json.loads((V12 / "results_cases.json").read_text(encoding="utf-8"))["ullmann"]
    ledger = {r["row_id"]: r for r in reference}
    found = {}
    for r in reference:
        if r["ref_id"] != "APPL11_A1" or r["table_or_figure"] != "Table 5":
            continue
        if "NH3 concentration at saturation" not in r["record"]:
            continue
        m = re.search(r"at t\s*=\s*(-?\d+)\s*C,\s*p\s*=\s*(\d+)\s*MPa",
                      r["printed_value_and_unit"])
        if m is None:
            continue
        t, p = int(m.group(1)), int(m.group(2))
        if t in T_GRID and p in P_GRID:
            assert r["kind"] == "source_fact" and r["checked_by_image"] == "yes", r["row_id"]
            if (t, p) in found:
                raise AssertionError(f"Duplicate reference table point at {t} C, {p} MPa")
            measured = float(r["value"])
            model_pct = 100.0 * psat_nh3_bar(t) / (p * 10.0)
            found[t, p] = dict(row_id=r["row_id"], T_C=t, P_MPa=p, source_y_pct=measured,
                               source_citation=r["citation"], model_psat_P_pct=model_pct,
                               model_to_source_ratio=model_pct / measured)
    if set(found) != {(t, p) for t in T_GRID for p in P_GRID}:
        raise AssertionError(f"Missing/interpolated Table 5 points: {set(found)}")
    if len(stored) != 28:
        raise AssertionError("The frozen NH3-FINAL-1.2 VLE record should have 28 cases")
    for item in stored:
        t, p, rid = int(item["T_C"]), int(item["P_MPa"]), item["row_id"]
        v = found[t, p]
        if rid != v["row_id"] or abs(v["source_y_pct"] - float(item["table"])) > 1e-8:
            raise AssertionError(f"Source table mismatch at {rid}")
        if abs(v["model_psat_P_pct"] - float(item["model"])) > 1e-5:
            raise AssertionError(f"Canonical Antoine baseline mismatch at {rid}")
    return found


def source_interpolation(grid, T_C: float, P_bar: float) -> float:
    """Piecewise bilinear interpolation *within* source table only; no fit/extrapolation."""
    P_MPa = P_bar / 10.0
    if not (T_GRID[0] <= T_C <= T_GRID[-1] and P_GRID[0] <= P_MPa <= P_GRID[-1]):
        raise ValueError("The Ullmann/BASF table does not cover this temperature/pressure")
    def bracket(values, value):
        for low, high in zip(values[:-1], values[1:]):
            if low <= value <= high:
                return low, high
        return values[-1], values[-1]
    t0, t1 = bracket(T_GRID, T_C)
    p0, p1 = bracket(P_GRID, P_MPa)
    ft = 0.0 if t0 == t1 else (T_C - t0) / (t1 - t0)
    fp = 0.0 if p0 == p1 else (P_MPa - p0) / (p1 - p0)
    y00 = grid[t0, p0]["source_y_pct"]
    y01 = grid[t0, p1]["source_y_pct"]
    y10 = grid[t1, p0]["source_y_pct"]
    y11 = grid[t1, p1]["source_y_pct"]
    return (1.0 - ft) * ((1.0 - fp) * y00 + fp * y01) + ft * ((1.0 - fp) * y10 + fp * y11)


def source_diagnostic(grid):
    rows_28 = [grid[t, p].copy() for t in T_GRID for p in P_GRID]
    m2s = [r["model_to_source_ratio"] for r in rows_28]
    by_T = []
    for t in T_GRID:
        rs = [grid[t, p] for p in P_GRID]
        ratios = [r["model_to_source_ratio"] for r in rs]
        assert all(a > b for a, b in zip(ratios[:-1], ratios[1:])), (
            f"Unexpected pressure trend at {t} C; no monotonicity may be assumed a priori")
        # A multiplicative correction c would pass every Table 5 entry at this T
        # under a +/-20%-of-source comparison iff all intervals overlap.
        lo = max(0.8 / r for r in ratios)
        hi = min(1.2 / r for r in ratios)
        by_T.append(dict(T_C=t, ratio_by_P=ratios,
                         global_constant_multiplier_20pct_low=lo,
                         global_constant_multiplier_20pct_high=hi,
                         constant_correction_feasible=lo <= hi))
    assert all(not x["constant_correction_feasible"] for x in by_T), (
        "Unexpected global correction conclusion; do not claim a single-factor failure")
    return rows_28, {
        "n_table_entries": 28,
        "model_to_table_ratio_min": min(m2s),
        "model_to_table_ratio_max": max(m2s),
        "all_temperatures_have_monotonic_pressure_bias": True,
        "constant_multiplicative_correction_within_20pct_possible": False,
        "by_temperature": by_T,
    }


def inlet_proxies(grid):
    enforce_pin(SRC / "benchmark_metrics.csv", PINS["benchmark_metrics.csv"])
    enforce_pin(SRC / "benchmark_cases.csv", PINS["benchmark_cases.csv"])
    metrics = {r["metric_id"]: r for r in rows(SRC / "benchmark_metrics.csv")}
    cases = {r["case_id"]: r for r in rows(SRC / "benchmark_cases.csv")}
    proxies = []
    for metric_id in INLETS:
        r = metrics[metric_id]
        case = cases[r["case_id"]]
        assert r["quantity"] == "inlet_NH3_molpct"
        t, p = float(case["Tsep_C"]), float(case["P_bar"])
        source_proxy = source_interpolation(grid, t, p)
        plant = float(r["industrial_value"])
        proxies.append(dict(metric_id=metric_id, case_id=r["case_id"],
                            Tsep_C=t, P_bar=p, plant_inlet_NH3_molpct=plant,
                            BASF_saturated_vapor_proxy_molpct=source_proxy,
                            proxy_relative_deviation_pct=100.0 * (source_proxy / plant - 1.0),
                            source_only_within_20pct=(abs(source_proxy / plant - 1.0) <= 0.2),
                            interpretation="SEPARATOR VAPOR PROXY ONLY; not model plant inlet and not a re-scored case",
                            caveat="Ullmann/BASF 1:3 N2/H2 vapor; actual plant can contain inerts and different feed mixing"))
    return proxies


def propagate_source_ysep(grid, proxies):
    """One-factor physical boundary substitution, retaining the exact NH3-FINAL-1.2 equations.

    A temporary method override changes ONLY psat_nh3_bar() at a fixed state
    to P * tabulated_ysep; all reaction-equilibrium, balance, cost and
    measured-Fe plug flow equations are the original ones. No source edits.
    """
    from bootstrap_replay import prepare
    prepare()
    import nh3_model as M  # plant adapter, after cached converter dependencies
    h = M.build_frozen()
    M.reproduce_anchors(h)
    cases = {r["case_id"]: r for r in rows(SRC / "benchmark_cases.csv")}
    actual = {r["metric_id"]: r for r in rows(V12 / "results_metrics.csv")}
    effects = []
    for proxy in proxies:
        key = proxy["metric_id"]
        c = cases[proxy["case_id"]]
        t, p, sep, cap = (float(c[x]) for x in ("T_C", "P_bar", "Tsep_C", "capacity_tpd"))
        control = M.state_point(h, t, p, sep, cap)
        if control is None:
            raise AssertionError("A registered baseline state became infeasible")
        stored = float(actual[key]["model"])
        if abs(control["inlet_NH3_molpct"] - stored) > 2e-5:
            raise AssertionError(f"Baseline source model changed at {key}, {control['inlet_NH3_molpct']} vs {stored}")
        had_local_override = "psat_nh3_bar" in vars(h)
        old_override = vars(h).get("psat_nh3_bar")
        try:
            # The modified psat is scoped to ONE state; not a global Antoine rewrite.
            h.psat_nh3_bar = lambda _tsep, pressure=p: pressure * source_interpolation(
                grid, float(_tsep), pressure) / 100.0
            scenario = M.state_point(h, t, p, sep, cap)
        finally:
            if had_local_override:
                h.psat_nh3_bar = old_override
            else:
                delattr(h, "psat_nh3_bar")
        plant = proxy["plant_inlet_NH3_molpct"]
        current = control["inlet_NH3_molpct"]
        changed = None if scenario is None else scenario["inlet_NH3_molpct"]
        effects.append(dict(
            metric_id=key, case_id=proxy["case_id"], T_C=t, P_bar=p, Tsep_C=sep,
            baseline_model_inlet_pct=current, source_vapor_input_pct=proxy["BASF_saturated_vapor_proxy_molpct"],
            counterfactual_model_inlet_pct=changed, plant_reported_inlet_pct=plant,
            baseline_rel_error_pct=100.0 * (current / plant - 1.0),
            counterfactual_rel_error_pct=None if changed is None else 100.0 * (changed / plant - 1.0),
            conditional_counterfactual_within_original_20pct_band=(
                None if changed is None else abs(changed / plant - 1.0) <= 0.20),
            baseline_process_cost_USD_t=control["process_cost_USD_t"],
            conditional_process_cost_USD_t=None if scenario is None else scenario["process_cost_USD_t"],
            scenario_status="INFEASIBLE" if scenario is None else "CONDITIONAL_SENSITIVITY_ONLY",
        ))
    return effects


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--propagate", action="store_true")
    args = parser.parse_args()
    grid = grid_from_printed_sources()
    rows_28, diagnostic = source_diagnostic(grid)
    proxies = inlet_proxies(grid)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "saturation_28.csv", rows_28)
    write_csv(args.out_dir / "plant_inlet_proxy_5.csv", proxies)
    outputs = {"reference_thermo": diagnostic,
               "plant_inlet_proxy": {"n": len(proxies),
                                      "n_proxy_within_20pct": sum(p["source_only_within_20pct"] for p in proxies),
                                      "note": "BASF vapor proxy alone cannot be equated with a plant inlet after recycle/make-up mixing"}}
    if args.propagate:
        effects = propagate_source_ysep(grid, proxies)
        write_csv(args.out_dir / "conditional_model_inlet_5.csv", effects)
        outputs["no_fit_state_propagation"] = {
            "n": len(effects),
            "n_feasible": sum(e["counterfactual_model_inlet_pct"] is not None for e in effects),
            "n_within_20pct_diagnostic_only": sum(e["conditional_counterfactual_within_original_20pct_band"] is True for e in effects),
            "rows": effects,
            "status": "NONCANONICAL_COMPARISON__DO_NOT_PROMOTE_INDUSTRIAL_PASS_RATE",
        }
    (args.out_dir / "summary.json").write_text(json.dumps(outputs, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    lines = [
        "# NH3 separator vapor source diagnostic (not a revised 64-case score)", "",
        "Source: Ullmann/BASF ammonia concentration at saturation over liquid ammonia, N2:H2 = 1:3, Table 5 (28 entries, image-checked source ledger).", "",
        f"The original p_sat/P model / BASF table ratios span **{diagnostic['model_to_table_ratio_min']:.3f}-{diagnostic['model_to_table_ratio_max']:.3f}**.",
        "All 7 temperature slices show worsening model-to-source ratio from 10 to 30 MPa.",
        "No single multiplicative factor makes all 4 pressures at even one fixed temperature fall within +/-20% of the source.", "",
        "## Five plant-inlet proxy comparisons (NOT a loop model)", "",
        "| Case | Plant inlet mol% | BASF saturated-vapor proxy mol% | Proxy error |",
        "|---|---:|---:|---:|",
    ]
    lines += [f"| {r['metric_id']} | {r['plant_inlet_NH3_molpct']:.2f} | "
              f"{r['BASF_saturated_vapor_proxy_molpct']:.3f} | "
              f"{r['proxy_relative_deviation_pct']:+.1f}% |" for r in proxies]
    lines += ["", "This comparison does not account for make-up mixing, inerts, or the actual separator hardware; no registered case is re-scored.", ""]
    if args.propagate:
        lines += ["## Same source model with only the separator vapor input changed (no fit, diagnostic)", "",
                  "| Case | Original inlet mol% | Conditional inlet mol% | Plant mol% | Conditional error |",
                  "|---|---:|---:|---:|---:|"]
        for r in effects:
            val = r["counterfactual_model_inlet_pct"]
            delta = r["counterfactual_rel_error_pct"]
            lines.append(f"| {r['metric_id']} | {r['baseline_model_inlet_pct']:.3f} | "
                         f"{'INFEASIBLE' if val is None else format(val,'.3f')} | "
                         f"{r['plant_reported_inlet_pct']:.2f} | "
                         f"{'N/A' if delta is None else format(delta,'+.1f')+'%'} |")
        lines += ["", "Conditional numbers do not replace the frozen process library, do not prove nonideal VLE physics, and must never be promoted into the original registered pass rate.", ""]
    (args.out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS: independently reconstructed 28 table entries and 5 inlet proxies; "
          f"optional source-model propagation={args.propagate}")


if __name__ == "__main__":
    main()
