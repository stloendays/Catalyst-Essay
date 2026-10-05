"""Validate the promoted strict-scaling x lifecycle reachability closure."""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "scaling_lifecycle_exact_summary.json"
BOUNDARY = HERE / "scaling_lifecycle_exact_global_boundary.csv"
KEYS = HERE / "scaling_lifecycle_exact_keypoints.csv"

EXPECTED_COST = 21.397872966049547
EXPECTED_EN = -1.215
EXPECTED_STATES = 14136
EXPECTED_FE = 15.291704676621144
EXPECTED_Q = 0.00044068345398945024


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


for p in (SUMMARY, BOUNDARY, KEYS):
    if not p.exists():
        fail("missing promoted result: " + p.name)

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
if s.get("schema") != "nh3-final-1.1-strict-scaling-lifecycle-reachability-v2":
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
if tested.get("intersects_strict_scaling_manifold") is not False:
    fail("tested lifecycle box must remain outside strict-scaling parity")

corner = tested.get("best_corner", {})
if abs(float(corner.get("life_y", -1)) - 20.0) > 1e-12:
    fail("best tested corner lifetime drift")
if abs(float(corner.get("recovery_fraction", -1)) - 0.99) > 1e-12:
    fail("best tested corner recovery drift")
if float(corner.get("margin_vs_Fe_USD_t", -1)) <= 0:
    fail("best tested corner unexpectedly reaches parity")

with BOUNDARY.open(encoding="utf-8", newline="") as fh:
    boundary = list(csv.DictReader(fh))
if len(boundary) < 4:
    fail("global lifecycle boundary is unexpectedly sparse")

b20 = next((r for r in boundary if abs(float(r["life_y"]) - 20.0) < 1e-12), None)
if b20 is None:
    fail("20-year boundary row missing")
if abs(float(b20["required_recovery_fraction"]) - 0.991186330920211) > 1e-9:
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
if str(k20["reaches_parity"]).strip().lower() not in {"false", "0", "no"}:
    fail("20 y / 99% keypoint must not reach parity")
if abs(float(k20["best_cost_USD_t"]) - float(corner["best_strict_scaling_cost_USD_t"])) > 1e-8:
    fail("summary/keypoint best-corner cost mismatch")

print("PASS strict-scaling lifecycle result gate")
print(f"baseline: {anchor['Ru_cost_USD_t']} USD/t at E_N={anchor['E_N_eV']} eV")
print(f"q*: {s['critical_lifecycle_factor_q_per_y']} 1/y")
print(f"20 y recovery boundary: {b20['required_recovery_percent']}%")
print(f"20 y / 99% corner: {k20['best_cost_USD_t']} USD/t; reaches parity={k20['reaches_parity']}")
