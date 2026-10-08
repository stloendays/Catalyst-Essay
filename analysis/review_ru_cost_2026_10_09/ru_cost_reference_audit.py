"""Independent QA: reconcile Fe reference denominators in Ru/C plant costs.

Read-only checker. Existing figure/source tables use different reference
conventions: fig2_ru_actual_cost_points.csv has a global Fe-main-loop
gap_to_Fe for *all* points, whereas supported-bed sensitivity tables use the
Fe optimum appropriate to the same process loop. Reconcile rather than
silently changing any published cost or frozen scientific inputs.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POINTS = ROOT / "figures/composite/fig2/fig2_ru_actual_cost_points.csv"
BEDS = ROOT / "figures/composite/fig2/fig2_ru_bed_sensitivity.csv"
READINGS = ROOT / "analysis/nh3_actual_ru_params_2026_10_07/fig3d_readings.csv"
TOL = 1e-7


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def approx(a: float, b: float, *, tol: float = TOL) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


def loop_for_key(key: str) -> str:
    return "KAAP" if key.startswith("kaap") or key == "fe_kaap" else "main"


def audit(points: list[dict], beds: list[dict], readings: list[dict]
          ) -> tuple[dict, list[dict]]:
    by_key = {x["key"]: x for x in points}
    errors: list[str] = []
    for expected in ("pure", "fe_kaap", "kaap90", "kaap97"):
        if expected not in by_key:
            errors.append(f"Missing canonical point {expected}")
    if errors:
        return {"status": "NOT_FROZEN", "errors": errors}, []

    # Independently recover the intended global comparison price from source.
    fe_main = float(by_key["pure"]["cost"]) - float(by_key["pure"]["gap_to_Fe"])
    fe_kaap = float(by_key["fe_kaap"]["cost"])
    references = {"main": fe_main, "KAAP": fe_kaap}
    corrected = []
    global_only_rows = []
    for row in points:
        loop = loop_for_key(row["key"])
        price = float(row["cost"])
        stored = float(row["gap_to_Fe"])
        global_gap = price - fe_main
        same_loop_gap = price - references[loop]
        if not approx(stored, global_gap):
            errors.append(f"Global Fe gap inconsistent for point {row['key']}")
        if loop == "KAAP":
            global_only_rows.append(row["key"])
        corrected.append(dict(
            key=row["key"], loop=loop, cost_USD_t=price,
            Fe_main_loop_reference_USD_t=fe_main,
            Fe_same_loop_reference_USD_t=references[loop],
            existing_gap_to_Fe_global_USD_t=stored,
            derived_gap_to_Fe_same_loop_USD_t=same_loop_gap,
            global_reference_differs_from_same_loop=(loop == "KAAP"),
        ))

    bed_index = {}
    for r in beds:
        key = (r["key"], round(float(r["w_Ru"]), 7),
               round(float(r["rho_bed_kg_m3"]), 5))
        if key in bed_index:
            errors.append(f"Duplicate bed sensitivity state {key}")
        bed_index[key] = r
        loop = loop_for_key(r["key"])
        cost, source_fe = float(r["cost"]), float(r["Fe_reference_cost"])
        if not approx(source_fe, references[loop]):
            errors.append(f"Bed source Fe comparator wrong loop: {key}")
        if not approx(cost - source_fe, float(r["gap_to_Fe_reference"])):
            errors.append(f"Bed delta is inconsistent with source costs: {key}")

    compared = 0
    r_all = []
    for row in readings:
        if row["set"] != "R_all" or row["reading"] != "own_bed":
            continue
        loop = row["loop"]
        r = float(row["recovery"])
        key = ("kaap" if loop == "KAAP" else "supp_rec") + str(round(r * 100))
        state = (key, round(float(row["w_Ru"]), 7),
                 round(float(row["rho_bed_kg_m3"]), 5))
        match = bed_index.get(state)
        if match is None:
            errors.append(f"R_all no matching canonical sensitivity row: {state}")
            continue
        compared += 1
        for field_a, field_b in (
            ("cost", "cost"), ("gap_to_Fe", "gap_to_Fe_reference"),
            ("Fe_reference_cost", "Fe_reference_cost"),
            ("alpha_star", "alpha_star_supported_bed"),
            ("P_bar", "P_bar"), ("T_C", "T_C"),
            ("Tsep_C", "Tsep_C"), ("V_m3", "V_m3"),
        ):
            if not approx(float(row[field_a]), float(match[field_b])):
                errors.append(f"R_all {field_a} differs from canonical bed state {state}")
        r_all.append(row)

    w8 = [r for r in r_all if approx(float(r["w_Ru"]), 0.08, tol=1e-9)]
    ranges = {}
    for loop in ("main", "KAAP"):
        group = [r for r in w8 if r["loop"] == loop]
        all_in_loop = [r for r in r_all if r["loop"] == loop]
        if len(group) != 4:
            errors.append(f"Expected 4 Ru 8 wt% corner states, got {len(group)} in {loop}")
        if len(all_in_loop) != 12:
            errors.append(f"Expected 12 Ru-content sensitivity corners, got {len(all_in_loop)} in {loop}")
        if group:
            cs = [float(x["cost"]) for x in group]
            gaps = [float(x["cost"]) - references[loop] for x in group]
            ranges[loop] = dict(
                Ru_wt_pct=8, n_corners=len(group),
                costs_min_USD_t=min(cs), costs_max_USD_t=max(cs),
                gap_min_USD_t=min(gaps), gap_max_USD_t=max(gaps),
                Ru_cheaper_than_Fe_at_corners=sum(d < 0 for d in gaps),
                Ru_cheaper_than_Fe_across_5_to_10wt_pct=sum(
                    float(x["cost"]) < references[loop] for x in all_in_loop),
                grid_corners=len(all_in_loop),
            )

    return dict(
        status="INDEPENDENT_QA_NOT_FROZEN",
        Fe_main_loop_USD_t=fe_main, Fe_KAAP_loop_USD_t=fe_kaap,
        canonical_points=len(points),
        bed_sensitivity_states=len(beds),
        R_all_own_bed_states_compared=compared,
        KAAP_points_with_global_Fe_gap_field=global_only_rows,
        Ru_8wt_percent_ranges=ranges,
        errors=errors,
        interpretation=(
            "Existing canonical gap_to_Fe is relative to globally optimized "
            "Fe main loop, including KAAP points. This is not the same as "
            "a paired Fe-KAAP comparison."
        ),
    ), corrected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--points", type=Path, default=POINTS)
    ap.add_argument("--beds", type=Path, default=BEDS)
    ap.add_argument("--readings", type=Path, default=READINGS)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    summary, derived = audit(read_csv(args.points),
                             read_csv(args.beds), read_csv(args.readings))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "ru_reference_audit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if derived:
        with (args.out_dir / "ru_reference_gaps.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(derived[0]))
            writer.writeheader()
            writer.writerows(derived)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return int(args.strict and bool(summary["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
