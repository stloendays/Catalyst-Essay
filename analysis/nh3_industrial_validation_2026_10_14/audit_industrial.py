#!/usr/bin/env python3
"""Read-only forensic audit of the preregistered NH3 plant benchmark.

This audit does not change the model, literature targets, tolerances, or original
64-case verdict. A PASS means source/provenance/replay consistency, NOT plant
validation. Failure mechanisms are testable hypotheses unless stated otherwise.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "analysis" / "validation_nh3_plant_2026_10_13"
V12 = SRC / "nh3_1_2"

# Git blob hashes from the 2026-10-14 main snapshot. Original rules are immutable.
PINS = {
    "benchmark_metrics.csv": "6083f2aca6dddec91572e2334b311d35ca83f0c6",
    "benchmark_cases.csv": "25816cab4aa12a5fd835981ead9135a304cee9fe",
    "industrial_windows.csv": "b08ee28a9a3bfe49bb6d6d827f3a0a1687c8d996",
    "PREREGISTRATION.md": "dc82d6030bbd00bb8ca511305e1e5ac151c8f220",
    "reference_values.csv": "5c112504a5ca5ac8d349501baa955bc751c95463",
}
SNAPSHOT_BLOB = "b4101ddd80206707ba364d3292db97a292d5b458"
SUMMARY_BLOB = "70e67d0085924f94c28723ed0362ff7819e0c4b7"

# Evidence labels are NOT verified causal attributions. Every failure remains
# scored FAIL in the preregistered benchmark, irrespective of category.
GROUPS = {
    "separator_vapor_and_loop_inlet": {
        "ids": "A01 A04 A07 A14 A16 V01",
        "evidence": "model p_sat(Tsep)/P; BASF saturation-table median ratio 0.602",
        "interpretation": "physical submodel discrepancy; influence on each plant inlet remains to be proven",
        "status": "model-versus-reference discrepancy; cause provisional",
        "needed": "sourced mixed-gas VLE, separator pressure/temperature, actual recycle NH3 and any interstage separation",
    },
    "conversion_and_operating_point": {
        "ids": "A13 A15 A20 A22 A26",
        "evidence": "source plant conversion versus 0.8-equilibrium loop surrogate; some T are T_REF",
        "interpretation": "plant operating point and kinetic/equilibrium assumptions are not fully matched",
        "status": "unresolved model and comparator confounding",
        "needed": "plant-specific bed inlet/outlet temperatures, inerts, approach to equilibrium and conversion definition",
    },
    "compressor_scope_or_hydraulics": {
        "ids": "E01 E02 E03",
        "evidence": "source compressor duty versus modeled fresh plus recycle or fixed 3-bar recycle rise",
        "interpretation": "equipment boundaries/thermodynamics/pressure loss may differ; do not assert a cause without inputs",
        "status": "power discrepancy demonstrated; causal mechanism unresolved",
        "needed": "source-specific suction/discharge states, compressor efficiency, stages, interstage cooling, actual loop pressure drop and included auxiliaries",
    },
    "source_conditioned_bed_heat_profile": {
        "ids": "B01 B02 B05 B06",
        "evidence": "converter forward calculation uses printed feed, temperatures and bed volumes",
        "interpretation": "source-matched bed-temperature profile discrepancy, not just an economic-design mismatch",
        "status": "direct source-conditioned model discrepancy",
        "needed": "measured effectiveness/particle size, heat exchange, axial gas temperature profiles and rate-law validity",
    },
    "cost_optimum_vs_installed_converter": {
        "ids": "B10 B11 B12 B13 B14 B15 B16 B17 B18",
        "evidence": "cost-optimized modeled converter compared with an installed plant/design at common loop P and Tsep",
        "interpretation": "different design objectives and incomplete physical/equipment cost constraints may cause mismatch",
        "status": "not a like-for-like fixed-design comparison",
        "needed": "real bed hydraulics, recycle compressor curve, equipment and refrigeration cost, installed bed/heat management constraints",
    },
    "kaap_converter_architecture": {
        "ids": "B19 B20",
        "evidence": "model KAAP-style converter compared with published 89-bar design volume split and outlet",
        "interpretation": "converter design, cooling, capacity and kinetic assumptions remain non-identical",
        "status": "industrial-design mismatch; cause unresolved",
        "needed": "bed-specific source flow, interbed cooling, catalyst volumes, rate-law domain, pressure loss and finance contract",
    },
    "plant_scale_reference_window": {
        "ids": "C02",
        "evidence": "model optimum evaluated at own capacity; window taken from world-scale 1200-2000 t/d plants",
        "interpretation": "the operating-pressure window mixes economic plant scales",
        "status": "comparison-basis mismatch, still a preregistered fail",
        "needed": "capacity-matched equipment economics and same design-class comparison",
    },
    "separator_cost_decision": {
        "ids": "C04",
        "evidence": "cost optimum Tsep=30 C versus measured Fe-loop final separators -25 to 7.5 C",
        "interpretation": "model favors warm separation; missing recycle/refrigeration economics is a hypothesis",
        "status": "model decision disagrees with built operating windows",
        "needed": "source refrigeration duty, recycle/condensation thermodynamics, equipment and electricity costs",
    },
    "metal_financing_vs_observed_deployment": {
        "ids": "C09",
        "evidence": "model uses 12%/y Ru finance; disclosed platinum-group leases 1.35-5.10%/y",
        "interpretation": "a 12%-financed optimum is not directly comparable to a lower-rate leased-metal deployment",
        "status": "explicit scenario mismatch; original pass/fail kept",
        "needed": "actual KAAP metal ownership, lease rate, recovered-metal credits and plant-specific timing",
    },
}
EXPECTED_COUNTS = {"A": (28, 18), "E": (3, 0), "B": (20, 5),
                   "C": (12, 9), "V": (1, 0)}


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def enforce_pin(path: Path, expected: str) -> None:
    actual = blob_sha(path)
    if actual != expected:
        raise AssertionError(f"Evidence bytes changed at {path}: {actual} != {expected}. "
                             "Do not silently edit registered inputs or baseline outputs.")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(value: str | None) -> float | None:
    return None if value in ("", None) else float(value)


def windows_from_sources() -> dict[str, tuple[float, float, set[str]]]:
    windows: dict[str, tuple[float, float, set[str]]] = {}
    for row in rows(SRC / "industrial_windows.csv"):
        key = row["window_id"]
        lo, hi = float(row["window_low"]), float(row["window_high"])
        if key not in windows:
            windows[key] = (lo, hi, set())
        old = windows[key]
        if (lo, hi) != old[:2]:
            raise AssertionError(f"Window inconsistent for {key}")
        old[2].add(row["row_id"])
    return windows


def independent_judge(rule: str, model_text: str,
                      value: float | None, low: float | None, high: float | None,
                      windows: dict) -> bool:
    kind, _, arg = rule.partition(":")
    if model_text in ("", None):
        return False
    if kind == "equals":
        if model_text not in ("True", "False"):
            raise ValueError(f"Boolean model required for {rule}: {model_text}")
        return (model_text == "True") == (arg == "True")
    model = float(model_text)
    if not math.isfinite(model):
        return False
    if kind == "rel":
        tol = float(arg)
        if value is not None:
            return abs(model - value) <= tol * abs(value) + 1e-12
        return low * (1.0 - tol) - 1e-12 <= model <= high * (1.0 + tol) + 1e-12
    if kind == "factor":
        return 1.0 / float(arg) <= model / value <= float(arg)
    if kind == "abs":
        return abs(model - value) <= float(arg) + 1e-12
    if kind == "range":
        return low <= model <= high
    if kind == "window":
        lo, hi, _ = windows[arg]
        return lo <= model <= hi
    if kind == "above":
        return model > float(arg)
    if kind == "below":
        return model < float(arg)
    raise ValueError(f"Unrecognized registered scoring rule: {rule}")


def verify_recomputed(registered: list[dict], recomputed_path: Path) -> dict:
    recalculated = rows(recomputed_path)
    new_by_id = {r["metric_id"]: r for r in recalculated}
    if len(new_by_id) != 64 or len(recalculated) != 64:
        raise AssertionError("The replay does not contain exactly 64 distinct metrics")
    diffs = []
    for original in registered:
        key = original["metric_id"]
        if key not in new_by_id:
            raise AssertionError(f"Missing replay metric: {key}")
        new = new_by_id[key]
        for field in ("table", "case_id", "quantity", "unit", "rule", "ref_rows"):
            if new[field] != original[field]:
                raise AssertionError(f"Replay changed {key}.{field}")
        if new["pass_"].lower() != original["pass_"].lower():
            raise AssertionError(f"Replay flipped a registered verdict at {key}: {original['pass_']} -> {new['pass_']}")
        a, b = original["model"], new["model"]
        if a in ("True", "False") or b in ("True", "False"):
            if a != b:
                raise AssertionError(f"Replay changed boolean at {key}")
            continue
        va, vb = float(a), float(b)
        tolerance = max(2e-5, 2e-5 * abs(va))
        if abs(va - vb) > tolerance:
            raise AssertionError(f"Replay shifted metric {key}: {va} -> {vb}; tolerance {tolerance}")
        diffs.append((key, abs(va - vb)))
    return {"replayed_metrics": 64, "same_verdicts": 64,
            "max_abs_numeric_difference": max((d[1] for d in diffs), default=0.0),
            "recompute_status": "reproduced within preregistered-adjacent numerical replay tolerance"}


def audit(snapshot: Path | None = None, recomputed: Path | None = None, summary_snapshot: Path | None = None) -> tuple[dict, list[dict]]:
    for name, digest in PINS.items():
        enforce_pin(SRC / name, digest)
    enforce_pin(summary_snapshot or V12 / "summary.json", SUMMARY_BLOB)
    baseline = snapshot or V12 / "results_metrics.csv"
    enforce_pin(baseline, SNAPSHOT_BLOB)

    source_metrics = rows(SRC / "benchmark_metrics.csv")
    observed = rows(baseline)
    references = {r["row_id"]: r for r in rows(SRC / "reference_values.csv")}
    cases = {r["case_id"]: r for r in rows(SRC / "benchmark_cases.csv")}
    win = windows_from_sources()
    reference_map = {r["metric_id"]: r for r in source_metrics}
    if len(reference_map) != 64 or len(source_metrics) != 64 or len(observed) != 64:
        raise AssertionError("Registered benchmark must contain exactly 64 distinct metrics")
    if len({r["metric_id"] for r in observed}) != 64:
        raise AssertionError("Duplicate result metric IDs")
    model_row_map = {r["metric_id"]: r for r in observed}
    if set(reference_map) != set(model_row_map):
        raise AssertionError("The result IDs do not match the preregistered comparison set")

    failure_groups = {}
    for group, info in GROUPS.items():
        for metric_id in info["ids"].split():
            if metric_id in failure_groups:
                raise AssertionError(f"Duplicated triage assignment: {metric_id}")
            failure_groups[metric_id] = group

    by_table = Counter()
    passing = Counter()
    output = []
    for original in source_metrics:
        metric_id = original["metric_id"]
        result = model_row_map[metric_id]
        if original["counted"] != "yes":
            raise AssertionError(f"Uncounted comparison smuggled into benchmark: {metric_id}")
        for field in ("table", "case_id", "quantity", "unit", "rule"):
            if result[field] != original[field]:
                raise AssertionError(f"{metric_id} mismatched {field}")
        correct = independent_judge(original["rule"], result["model"],
                                    number(original["industrial_value"]),
                                    number(original["industrial_low"]), number(original["industrial_high"]), win)
        published = result["pass_"].lower() == "pass"
        if correct != published:
            raise AssertionError(f"Independent pass/fail differs from committed outcome for {metric_id}")
        ref_ids = re.findall(r"R\d{4}", original["ref_rows"] or "")
        if original["rule"].startswith("window:"):
            ref_ids += sorted(win[original["rule"].split(":", 1)[1]][2])
        unique_ref_ids = list(dict.fromkeys(ref_ids))
        if not unique_ref_ids and metric_id != "V01":
            raise AssertionError(f"{metric_id} lacks a registered source or source window")
        for ref_id in unique_ref_ids:
            if ref_id not in references:
                raise AssertionError(f"Missing primary evidence row {ref_id} for {metric_id}")
            if references[ref_id]["kind"] == "web_summary":
                raise AssertionError(f"Web summary used as scored evidence at {metric_id}")
        group = failure_groups.get(metric_id, "passed")
        if published and group != "passed":
            raise AssertionError(f"Current PASS is incorrectly assigned a failing triage category: {metric_id}")
        if not published and group == "passed":
            raise AssertionError(f"Missing failing triage category: {metric_id}")
        by_table[original["table"]] += 1
        passing[original["table"]] += int(published)
        note = GROUPS.get(group, {})
        case = cases.get(original["case_id"], {})
        output.append({
            "metric_id": metric_id, "table": original["table"], "case_id": original["case_id"],
            "model": result["model"], "industrial": result["industrial"], "unit": original["unit"],
            "registered_rule": original["rule"], "unchanged_verdict": "PASS" if published else "FAIL",
            "triage_family": group, "evidence_status": note.get("status", "passed registered comparison"),
            "hypothesis_not_attribution": note.get("interpretation", ""),
            "needed_to_discriminate": note.get("needed", ""),
            "model_case_level": case.get("level", "derived/optimum"),
            "temperature_basis": case.get("T_basis", ""),
            "separator_basis": case.get("Tsep_basis", ""),
            "source_row_ids": ";".join(unique_ref_ids),
            "source_citations": "; ".join(dict.fromkeys(references[k]["citation"] for k in unique_ref_ids)),
        })

    for table, (n, n_ok) in EXPECTED_COUNTS.items():
        if (by_table[table], passing[table]) != (n, n_ok):
            raise AssertionError(f"Unexpected NH3-FINAL-1.2 baseline for {table}: {(by_table[table], passing[table])}")

    if sum(passing.values()) != 32 or len(failure_groups) != 32:
        raise AssertionError("The 32/64 registered baseline is not preserved")

    # A falsification-bound diagnostic, NOT a re-fitted compressor or new scored result.
    # E01 source lists 2.7 -> 15.1 MPa while the model assumes 30 bar suction.
    # Treating ALL combined compression power as if affected by fresh-feed suction
    # maximizes this single correction in an ideal isothermal, equal-efficiency model.
    e01 = model_row_map["E01"]
    model_power = float(e01["model"])
    target_power = float(reference_map["E01"]["industrial_value"])
    pressure_out = float(cases["LIU93_151"]["P_bar"])
    pressure_ratio_correction = math.log(pressure_out / 27.0) / math.log(pressure_out / 30.0)
    generous_power = model_power * pressure_ratio_correction
    if generous_power >= target_power:
        raise AssertionError("Unexpected pressure-ratio bound: revisit explicit source assumptions")
    summary = {
        "scope": "NH3-FINAL-1.2 conditional industrial benchmark / independent triage",
        "status": "AUDIT_REPRODUCIBLE__ENGINEERING_VALIDATION_NOT_ESTABLISHED",
        "registered_first_model": "NH3-FINAL-1.1: 14/64, unchanged",
        "rescore_model": "NH3-FINAL-1.2: 32/64, unchanged",
        "by_table": {k: {"n": by_table[k], "pass": passing[k], "fail": by_table[k] - passing[k]}
                     for k in EXPECTED_COUNTS},
        "failure_groups": dict(Counter(x["triage_family"] for x in output if x["unchanged_verdict"] == "FAIL")),
        "unresolved": 32,
        "evidence_pins_git_blob": PINS | {"nh3_1_2/results_metrics.csv": SNAPSHOT_BLOB,
                                        "nh3_1_2/summary.json": SUMMARY_BLOB},
        "power_E01_pressure_ratio_only": {
            "status": "conditional upper-bound sensitivity, not a new model prediction",
            "industrial_model_boundary": "plant suction 27 bar and discharge 151 bar; model suction 30 bar",
            "isothermal_equal_efficiency_ratio": pressure_ratio_correction,
            "original_model_MW": model_power,
            "generous_corrected_combined_MW": generous_power,
            "plant_MW": target_power,
            "unexplained_fraction_of_plant_power_after_correction": 1.0 - generous_power / target_power,
        },
        "review_actions": {
            k: {"evidence": v["evidence"], "interpretation": v["interpretation"],
                "evidence_status": v["status"], "required_source_inputs": v["needed"]}
            for k, v in GROUPS.items()
        },
    }
    if recomputed is not None:
        if summary_snapshot is None:
            raise AssertionError("A full model rerun must preserve the original summary separately")
        summary["replay"] = verify_recomputed(observed, recomputed)
        regenerated = json.loads((V12 / "summary.json").read_text(encoding="utf-8"))
        historical = json.loads(summary_snapshot.read_text(encoding="utf-8"))
        if (regenerated.get("n_metrics"), regenerated.get("n_pass")) != (64, 32):
            raise AssertionError("The rebuilt benchmark summary changed registered score totals")
        if regenerated.get("by_table") != historical.get("by_table"):
            raise AssertionError("The rebuilt 64-metric by-table score changed")
        for field in ("frozen_Fe", "frozen_Ru"):
            if abs(float(regenerated["anchors"][field]) - float(historical["anchors"][field])) > 1e-6:
                raise AssertionError(f"Canonical 1.2 anchor drift: {field}")
        if abs(float(regenerated["anchors"]["measured_Fe"]["cost"]) -
               float(historical["anchors"]["measured_Fe"]["cost"])) > 1e-5:
            raise AssertionError("Measured-Fe anchor drift")
        summary["replay"]["summary_science_counts_and_anchors_preserved"] = True
        summary["replay"]["operational_seconds_not_pinned"] = True
        summary["replay"]["pr77_diagnostic_is_uncounted"] = True
    return summary, output


def emit_report(summary: dict, output: list[dict], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    with (destination / "triage_64.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    lines = [
        "# NH3-FINAL-1.2 industrial benchmark forensic audit",
        "",
        "**No refitting; no scoring-rule modifications; no scientific validation PASS claimed.**",
        "",
        "Original preregistered 1.1: **14/64**. Upgraded 1.2: **32/64** (both kept).",
        "",
        "| Subtest | PASS | FAIL |",
        "|---|---:|---:|",
    ]
    lines.extend(f"| {k} | {v['pass']} | {v['fail']} |" for k, v in summary["by_table"].items())
    lines += ["", "## Remaining 32 failures: triage hypothesis, not proven cause", "",
              "| Category | Count | Evidence status | Required next evidence |",
              "|---|---:|---|---|"]
    for category, info in GROUPS.items():
        lines.append(f"| {category} | {summary['failure_groups'].get(category, 0)} | "
                     f"{info['status']} | {info['needed']} |")
    d = summary["power_E01_pressure_ratio_only"]
    lines.extend(["", "## Non-fitting E01 compressor boundary bound", "",
                  "Published E01 power is 13.0 MW versus modeled 7.500 MW. The published "
                  "fresh-feed suction is 27 bar versus the model's 30 bar. Under an "
                  "**ideal-isothermal, unchanged-efficiency assumption**, even applying "
                  "the full fresh-gas pressure-ratio correction to ALL combined compression "
                  "power (a deliberately generous attribution) gives "
                  f"**{d['generous_corrected_combined_MW']:.3f} MW**. The remaining "
                  f"deficit is **{100*d['unexplained_fraction_of_plant_power_after_correction']:.1f}%** "
                  "of the literature total. This DOES NOT identify the missing equipment "
                  "power or validate a compressor curve.",
                  "",
                  "## Interpretation boundaries", "",
                  "- B01/B02/B05/B06 use a printed bed/feed comparator and retain measured-profile discrepancies.",
                  "- B10-B20 compare cost-optimized (or illustrative KAAP-like) designs with installed designs.",
                  "- C09 uses a 12% metal-financing assumption rather than documented lower-rate leases.",
                  "- V01 compares the simplified p_sat/P separator with an ammonia saturation table.",
                  "- No FAILED record is relabeled as PASS; missing physical inputs remain unresolved.",
                  "- GitHub CI success indicates reproducibility and traceability only.",
                  "",
                  "Full 64-row provenance and evidence identifiers: triage_64.csv.",
                  ""])
    if "replay" in summary:
        lines += ["Recompute replay: 64/64 identical verdicts within the declared numerical replay tolerance.", ""]
    report = "\n".join(lines)
    (destination / "REPORT.md").write_text(report, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, default=None,
                        help="Preserved original 1.2 metrics file for replay after model rerun")
    parser.add_argument("--summary-snapshot", type=Path, default=None,
                        help="Git-blob-pinned original summary saved before source model rewrites its timing fields")
    parser.add_argument("--recomputed", type=Path, default=None,
                        help="Optional recomputed 1.2 metrics file; only compare against the preserved snapshot")
    args = parser.parse_args()
    summary, output = audit(snapshot=args.snapshot, recomputed=args.recomputed,
                            summary_snapshot=args.summary_snapshot)
    emit_report(summary, output, args.out_dir)
    print(f"PASS: 64 registered metrics, 32 passing, 32 failing; "
          f"source pins OK; triage report at {args.out_dir}")
    if args.recomputed:
        print("PASS: full NH3-FINAL-1.2 recomputation, 64/64 verdicts unchanged")


if __name__ == "__main__":
    main()
