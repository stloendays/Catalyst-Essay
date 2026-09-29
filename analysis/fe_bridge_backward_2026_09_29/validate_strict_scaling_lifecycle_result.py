"""Validate imported strict-scaling x lifecycle reachability outputs before promotion."""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "scaling_lifecycle_exact_summary.json"
BOUNDARY = HERE / "scaling_lifecycle_exact_boundary.csv"
KEYS = HERE / "scaling_lifecycle_exact_keypoints.csv"

EXPECTED_COST = 21.397872966049547
EXPECTED_EN = -1.215
EXPECTED_STATES = 14136


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


for p in (SUMMARY, BOUNDARY, KEYS):
    if not p.exists():
        fail(f"missing output: {p.name}")

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
if s.get("schema") != "nh3-final-1.1-strict-scaling-lifecycle-reachability-v1":
    fail("unexpected schema")
if s.get("no_new_DFT") is not True:
    fail("no_new_DFT must be true")
if s.get("cached_response_reused") is not True:
    fail("cached_response_reused must be true")
if int(s.get("process_states", -1)) != EXPECTED_STATES:
    fail(f"process-state count drift: {s.get('process_states')}")

anchor = s.get("baseline_regression_anchor", {})
if abs(float(anchor.get("Ru_cost_USD_t", 1e9)) - EXPECTED_COST) > 1e-7:
    fail("strict-scaling baseline cost did not reproduce")
if abs(float(anchor.get("E_N_eV", 1e9)) - EXPECTED_EN) > 1e-12:
    fail("strict-scaling baseline E_N did not reproduce")

with BOUNDARY.open(encoding="utf-8", newline="") as fh:
    boundary = list(csv.DictReader(fh))
if not boundary:
    fail("empty strict-scaling boundary")

with KEYS.open(encoding="utf-8", newline="") as fh:
    keys = list(csv.DictReader(fh))
if not keys:
    fail("empty keypoint table")

corner = next(
    (
        r for r in keys
        if int(r["catalyst_life_y"]) == 20
        and abs(float(r["Ru_recovery_fraction"]) - 0.99) < 1e-12
    ),
    None,
)
if corner is None:
    fail("20 y / 99% recovery corner missing")

reported = bool(s.get("strict_scaling_joint_region_intersects_tested_lifecycle_envelope"))
parsed = str(corner["reaches_Fe_parity"]).strip().lower() in {"true", "1", "yes"}
if reported != parsed:
    fail("summary/keypoint reachability verdict mismatch")

print("PASS strict-scaling lifecycle result gate")
print(f"baseline: {anchor['Ru_cost_USD_t']} USD/t at E_N={anchor['E_N_eV']} eV")
print(f"20 y / 99% recovery reaches parity: {reported}")
print(f"best corner cost: {corner['best_Ru_cost_USD_t']} USD/t")
print(f"best corner E_N: {corner['best_strict_scaling_E_N_eV']} eV")
