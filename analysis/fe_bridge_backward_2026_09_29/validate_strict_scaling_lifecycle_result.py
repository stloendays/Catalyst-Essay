"""Validate the promoted strict-scaling x lifecycle reachability closure.

NH3_MODEL=1.1 (default) validates the committed NH3-FINAL-1.1 files next to this script against the frozen 1.1
values; NH3_MODEL=1.2 validates nh3_1_2/ against the NH3-FINAL-1.2 run (results.json under provenance/nh3_final_1_2)
and the promoted 1.2 critical lifecycle factor. Standard library only (runs in CI without the harness).
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VERSION = os.environ.get("NH3_MODEL", "1.1")

if VERSION == "1.1":
    DIR = HERE
    EXPECTED_SCHEMA = "nh3-final-1.1-strict-scaling-lifecycle-reachability-v2"
    EXPECTED_COST = 21.397872966049547
    EXPECTED_EN = -1.215
    EXPECTED_STATES = 14136
    EXPECTED_FE = 15.291704676621144
    EXPECTED_Q = 0.00044068345398945024
    EXPECTED_REC20 = 0.991186330920211
    EXPECTED_INTERSECTS = False
elif VERSION == "1.2":
    DIR = HERE / "nh3_1_2"
    _res = json.loads((REPO / "provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json")
                      .read_text(encoding="utf-8"))
    EXPECTED_SCHEMA = "nh3-final-1.2-strict-scaling-lifecycle-reachability-v2"
    EXPECTED_COST = float(_res["backward_reachability"]["Ru_best_scaling_cost_USD_t"])
    EXPECTED_EN = float(_res["backward_reachability"]["Ru_best_scaling_EN_eV"])
    EXPECTED_STATES = int(_res["deterministic"]["process_state_count"])
    EXPECTED_FE = float(_res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
    EXPECTED_Q = 0.0008251028617208592  # promoted 1.2 result of run_statewise_strict_scaling_lifecycle.py
    EXPECTED_REC20 = 1.0 - 20.0 * EXPECTED_Q
    EXPECTED_INTERSECTS = True
else:
    raise SystemExit(f"NH3_MODEL must be 1.1 or 1.2, not {VERSION!r}")

SUMMARY = DIR / "scaling_lifecycle_exact_summary.json"
BOUNDARY = DIR / "scaling_lifecycle_exact_global_boundary.csv"
KEYS = DIR / "scaling_lifecycle_exact_keypoints.csv"


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


for p in (SUMMARY, BOUNDARY, KEYS):
    if not p.exists():
        fail("missing promoted result: " + p.name)

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
if s.get("schema") != EXPECTED_SCHEMA:
    fail("unexpected schema")
if s.get("no_new_DFT") is not True:
    fail("no_new_DFT must be true")
if int(s.get("process_states", -1)) != EXPECTED_STATES:
    fail(f"process-state count drift: {s.get('process_states')}")
if abs(float(s.get("Fe_reference_cost_USD_t", 1e9)) - EXPECTED_FE) > 1e-8:
    fail("Fe reference cost drift")
if abs(float(s.get("critical_lifecycle_factor_q_per_y", 1e9)) - EXPECTED_Q) > 1e-12:
    fail("critical lifecycle factor drift")

anchor = s.get("baseline_regression_anchor", {})
if abs(float(anchor.get("Ru_cost_USD_t", 1e9)) - EXPECTED_COST) > 1e-8:
    fail("strict-scaling baseline cost did not reproduce")
if abs(float(anchor.get("E_N_eV", 1e9)) - EXPECTED_EN) > 1e-12:
    fail("strict-scaling baseline E_N did not reproduce")

tested = s.get("tested_lifecycle_envelope", {})
if tested.get("intersects_strict_scaling_manifold") is not EXPECTED_INTERSECTS:
    fail("tested lifecycle box must " + ("intersect" if EXPECTED_INTERSECTS else "remain outside")
         + " strict-scaling parity")

corner = tested.get("best_corner", {})
if abs(float(corner.get("life_y", -1)) - 20.0) > 1e-12:
    fail("best tested corner lifetime drift")
if abs(float(corner.get("recovery_fraction", -1)) - 0.99) > 1e-12:
    fail("best tested corner recovery drift")
if (float(corner.get("margin_vs_Fe_USD_t", 0)) <= 0) != EXPECTED_INTERSECTS:
    fail("best tested corner margin sign disagrees with the intersection verdict")

with BOUNDARY.open(encoding="utf-8", newline="") as fh:
    boundary = list(csv.DictReader(fh))
if len(boundary) < 4:
    fail("global lifecycle boundary is unexpectedly sparse")

b20 = next((r for r in boundary if abs(float(r["life_y"]) - 20.0) < 1e-12), None)
if b20 is None:
    fail("20-year boundary row missing")
if abs(float(b20["required_recovery_fraction"]) - EXPECTED_REC20) > 1e-9:
    fail("20-year recovery boundary drift")

with KEYS.open(encoding="utf-8", newline="") as fh:
    keys = list(csv.DictReader(fh))
if len(keys) != 4:
    fail("expected four lifecycle keypoints")
k20 = next(
    (
        r for r in keys
        if abs(float(r["life_y"]) - 20.0) < 1e-12
        and abs(float(r["recovery"]) - 0.99) < 1e-12
    ),
    None,
)
if k20 is None:
    fail("20 y / 99% recovery keypoint missing")
if (str(k20["reaches_parity"]).strip().lower() in {"true", "1", "yes"}) != EXPECTED_INTERSECTS:
    fail("20 y / 99% keypoint parity flag disagrees with the intersection verdict")
if abs(float(k20["best_cost_USD_t"]) - float(corner["best_strict_scaling_cost_USD_t"])) > 1e-8:
    fail("summary/keypoint best-corner cost mismatch")

print(f"PASS strict-scaling lifecycle result gate (NH3-FINAL-{VERSION})")
print(f"baseline: {anchor['Ru_cost_USD_t']} USD/t at E_N={anchor['E_N_eV']} eV")
print(f"q*: {s['critical_lifecycle_factor_q_per_y']} 1/y")
print(f"20 y recovery boundary: {b20['required_recovery_percent']}%")
print(f"20 y / 99% corner: {k20['best_cost_USD_t']} USD/t; reaches parity={k20['reaches_parity']}")
