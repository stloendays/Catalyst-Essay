#!/usr/bin/env python3
"""Inverse, no-refit separator-vapor requirement at five published plant conditions.

Question: With the original NH3-FINAL-1.2 reaction equilibrium and recycle closure
unchanged, what *hypothetical* separator vapor NH3 fraction would be required to
reproduce the plant's reported CONVERTER INLET NH3? This is a one-output inverse
constraint, not an independent validation or a new calibrated model.

The source BASF 1:3 N2/H2 saturation table is the external thermodynamic reference.
No canonical data/physics code, registered scoring, or literature targets are changed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from audit_industrial import SRC, V12, PINS, enforce_pin, rows
from diagnose_separator_vle import (
    INLETS, CASE_PIN, grid_from_printed_sources, source_interpolation, psat_nh3_bar,
)
from bootstrap_replay import prepare


def reactor_inlet_fraction(ysep: float, x: float) -> float:
    """Exact algebraic simplification of the source harness recycle/makeup closure.

    Source harness: NH3 recirculated = [ysep/(1-ysep)]*2*(1-X)/X;
    total reactor inlet = 2/X + recirculated NH3.
    """
    if not (0 <= ysep < 1 and 0 < x < 1):
        raise ValueError("Invalid separator vapor or per-pass conversion")
    return ysep * (1.0 - x) / (1.0 - ysep * x)


def inverse_diagnostics():
    from scipy.optimize import brentq  # only required for optional full source-model inverse run
    # Pin the exact registered comparison targets, case operating points, and
    # original 1.2 model output before doing ANY inverse diagnostic.
    enforce_pin(SRC / "benchmark_metrics.csv", PINS["benchmark_metrics.csv"])
    enforce_pin(SRC / "benchmark_cases.csv", PINS["benchmark_cases.csv"])
    enforce_pin(V12 / "results_cases.json", CASE_PIN)
    grid = grid_from_printed_sources()
    metrics = {r["metric_id"]: r for r in rows(SRC / "benchmark_metrics.csv")}
    cases = {r["case_id"]: r for r in rows(SRC / "benchmark_cases.csv")}
    recorded = {r["metric_id"]: r for r in rows(V12 / "results_metrics.csv")}

    prepare()
    import nh3_model as M  # benchmark adapter, after shared selector and converter loaded
    h = M.build_frozen()
    M.reproduce_anchors(h)

    original_psat = h.psat_nh3_bar  # bound source method; restored after each evaluation
    results = []
    for metric_id in INLETS:
        r = metrics[metric_id]
        c = cases[r["case_id"]]
        assert r["quantity"] == "inlet_NH3_molpct"
        temp = float(c["T_C"])
        P = float(c["P_bar"])
        t_sep = float(c["Tsep_C"])
        target = float(r["industrial_value"]) / 100.0
        source_sep_y = source_interpolation(grid, t_sep, P) / 100.0
        model_sep_y = psat_nh3_bar(t_sep) / P

        def state_at_separator_y(y):
            had_local = "psat_nh3_bar" in vars(h)
            old_local = vars(h).get("psat_nh3_bar")
            try:
                h.psat_nh3_bar = lambda _t, sep_fraction=y, pressure=P: pressure * sep_fraction
                st = h.self_consistent_process_state(temp, P, t_sep)
            finally:
                if had_local:
                    h.psat_nh3_bar = old_local
                else:
                    delattr(h, "psat_nh3_bar")
            return st

        def inlet_at(y):
            state = state_at_separator_y(y)
            if state is None:
                return None
            return reactor_inlet_fraction(float(state["ysep"]), float(state["X"]))

        # Assert source implementation remains unchanged. No book-keeping
        # correction is permitted to masquerade as model improvement.
        baseline = h.self_consistent_process_state(temp, P, t_sep)
        if baseline is None:
            raise AssertionError(f"Canonical source model infeasible: {metric_id}")
        yin_orig = reactor_inlet_fraction(baseline["ysep"], baseline["X"])
        if abs(100 * yin_orig - float(recorded[metric_id]["model"])) > 2e-5:
            raise AssertionError(f"Original source output drift: {metric_id}")

        external_model_y = inlet_at(source_sep_y)
        if external_model_y is None:
            raise AssertionError(f"BASF in-table separator point invalid in current model: {metric_id}")

        # Source table is not itself a full-loop prediction. Find an inverse
        # model consistency requirement with [0, RECYCLE_NH3_CAP) and no extrapolation
        # of BASF Table 5. Searching beyond BASF is deliberately an unphysical
        # *requirement comparison*, NEVER a proposed EOS.
        upper = min(float(h.RECYCLE_NH3_CAP) * (1 - 1e-6), 0.999)
        lower = max(source_sep_y, model_sep_y)
        sampled = []
        for j in range(151):
            y = lower + (upper - lower) * j / 150.0
            v = inlet_at(y)
            if v is not None:
                sampled.append((y, v))
        if not sampled:
            raise AssertionError(f"No physically feasible source loop states: {metric_id}")
        # We do not assume the model response is monotone without evidence.
        # A bracket gives a valid inverse root; no bracket => unresolved.
        crossings = []
        for (y0, v0), (y1, v1) in zip(sampled[:-1], sampled[1:]):
            if (v0 - target) * (v1 - target) <= 0:
                crossings.append((y0, y1))
        if crossings:
            y0, y1 = crossings[0]
            if y0 == y1:
                required = y0
            elif abs(inlet_at(y0) - target) < 1e-12:
                required = y0
            else:
                required = brentq(lambda y: inlet_at(y) - target, y0, y1, xtol=1e-12, rtol=1e-10)
            reproduced = inlet_at(required)
            if reproduced is None or abs(reproduced - target) > 1e-9:
                raise AssertionError(f"Inverse root insufficient for {metric_id}")
            status = "INVERSE_TARGET_REACHABLE_UNDER_HYPOTHETICAL_SEPARATOR"
        else:
            required = None
            status = "NO_BRACKETED_INVERSE_ROOT_WITHIN_MODEL_CAP_NOT_GLOBAL_PROOF"

        # Independent structural bound: NH3-free makeup cannot increase inlet
        # NH3 concentration above recycle vapor concentration in this flow-sheet.
        assert external_model_y < source_sep_y + 1e-12
        row = dict(
            metric_id=metric_id, case_id=c["case_id"], plant_T_C=temp, plant_P_bar=P,
            separator_T_C=t_sep, target_reactor_inlet_pct=100 * target,
            canonical_separator_pct=100 * model_sep_y, canonical_reactor_inlet_pct=100 * yin_orig,
            BASF_separator_proxy_pct=100 * source_sep_y,
            loop_inlet_with_BASF_separator_pct=100 * external_model_y,
            required_separator_pct=None if required is None else 100 * required,
            required_over_BASF_separator=None if required is None else required / source_sep_y,
            required_over_canonical_separator=None if required is None else required / model_sep_y,
            cap_percent=100 * upper,
            source_table_covers_required_y=False if required is None else bool(abs(required-source_sep_y) < 1e-8),
            lower_bound_inlet_no_ammonia_makeup=100 * target,
            inverse_status=status,
            preregistered_verdict_unchanged=recorded[metric_id]["pass_"],
        )
        assert recorded[metric_id]["pass_"].lower() == "fail"
        results.append(row)
    # The source method must not be permanently replaced by an inverse exercise.
    assert h.psat_nh3_bar.__func__ is original_psat.__func__
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args=parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results=inverse_diagnostics()
    with (args.out_dir / "required_separator_5.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    overview={
        "n": len(results),
        "found_inverse_root": sum(r["required_separator_pct"] is not None for r in results),
        "status": "INVERSE_CONSTRAINT_NOT_VALIDATION",
        "preregistered_failure_count_unchanged": 5,
        "need_additional_loop_equipment_or_composition_evidence": True,
        "original_64_case_pass_rate_unchanged": "32/64",
        "rows": results,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(overview, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    lines=["# Five plant inlets: required separator vapor under unchanged source-model closure", "",
           "**Inverse diagnostic only, NOT a model fit or a revised preregistered benchmark.**", "",
           "| Plant | BASF separator NH3 % | Model inlet with BASF % | Actual inlet % | Separator required by fixed original loop % | Requirement / BASF |",
           "|---|---:|---:|---:|---:|---:|"]
    for v in results:
        p=v["required_separator_pct"];ratio=v["required_over_BASF_separator"]
        lines.append(f"| {v['case_id']} | {v['BASF_separator_proxy_pct']:.3f} | {v['loop_inlet_with_BASF_separator_pct']:.3f} | {v['target_reactor_inlet_pct']:.2f} | {'UNRESOLVED' if p is None else format(p,'.3f')} | {'n/a' if ratio is None else format(ratio,'.2f')} |")
    lines+=["","The inverse target is *the same reported plant inlet used to construct the requirement*. "
            "Matching it by construction cannot validate the model, and a required separator value above "
            "BASF is not evidence that a real separator could operate there.",
            "The source baseline assumes stoichiometric NH3-free makeup, no inerts and a single mixing topology. "
            "Real plants may have inerts, purge, different mixing, bypass, interstage product recovery, "
            "or source equipment-boundary differences.",
            "BASF source data are N2:H2=1:3 saturated-vapor measurements; interpolation is in-domain only. "
            "Required concentrations are compared *against* the table and are not extrapolated EOS claims.",
            "All original industrial benchmark judgments are unchanged.", ""]
    (args.out_dir / "REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(f"PASS: {len(results)} hypothetical no-fit inverse constraints, "
          f"{overview['found_inverse_root']} root(s), unchanged scientific baseline")


if __name__=="__main__":
    main()
