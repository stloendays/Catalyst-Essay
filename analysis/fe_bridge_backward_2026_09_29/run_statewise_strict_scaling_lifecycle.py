"""Fast exact strict-scaling x lifecycle closure for NH3-FINAL-1.1.

No DFT is run and no response cache is required. The calculation uses the frozen
FINAL-1.1 equations and all 14,136 process states.

Key reduction: at fixed process state, E_N affects cost only through TOF -> active
metal -> bed volume. Metal replacement, reactor volume and pressure-vessel terms are
all monotone in active metal / volume, while the process-state cost is independent of
E_N. Therefore the cost-minimizing E_N for that state is simply its TOF-maximizing
E_N, independent of catalyst lifetime or metal recovery. We find that statewise
optimum on the canonical 0.005-eV strict-scaling grid, then construct the exact lower
cost envelope over all states.

Usage:
  python run_statewise_strict_scaling_lifecycle.py /path/to/Catalyst_Economic_Leverage_Automation_Harness_v0.1
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
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NH3_HARNESS", ".")).resolve()
sys.path.insert(0, str(HARNESS))
from harness_core import NH3Harness, PRICE  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
h = NH3Harness(cfg, HARNESS)
if h.NSTATE != 14136:
    raise SystemExit(f"process-state count drift: {h.NSTATE}")

FE = float(res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
P_RU = float(PRICE["Ru"])
strict_ref = float(res["backward_reachability"]["Ru_best_scaling_cost_USD_t"])
strict_en = float(res["backward_reachability"]["Ru_best_scaling_EN_eV"])

# Regression gate on the canonical strict-scaling point.
log_ref = h.frozen_state_logtof(strict_en)
tot_ref, V_ref, _, _ = h.cost_arrays("Ru", log_ref)
ok_ref = V_ref <= h.V_CAP
check = float(np.min(np.where(ok_ref, tot_ref, np.inf)))
if abs(check - strict_ref) > 1e-8:
    raise SystemExit(f"strict-scaling anchor drift: {check} vs {strict_ref}")

# For each state, locate its TOF maximum, snap to the frozen 0.005-eV grid,
# and check neighboring grid points.
best_log = np.empty(h.NSTATE)
best_en = np.empty(h.NSTATE)
for i, state in enumerate(h.process_states):
    cond = state["condition"]
    fit = minimize_scalar(
        lambda e: -cond.logtof(float(e)),
        bounds=(-2.2, 0.2),
        method="bounded",
        options={"xatol": 2e-4, "maxiter": 60},
    )
    e0 = round(round(fit.x / 0.005) * 0.005, 3)
    cand = [max(-2.2, min(0.2, round(e0 + d, 3))) for d in (-0.010, -0.005, 0.0, 0.005, 0.010)]
    vals = [cond.logtof(e) for e in cand]
    j = int(np.argmax(vals))
    best_en[i] = cand[j]
    best_log[i] = vals[j]

active = h.nh3_mol_s * 101.07 / h.F_CAL * np.power(10.0, -best_log)
V = active / h.ACTIVE_FRACTION / h.BED_DENSITY
metal_coeff = active * P_RU / h.annual_output_t
reactor = (
    (h.REACTOR_FIXED + h.REACTOR_VAR * np.power(V / h.REACTOR_REF, h.REACTOR_EXP))
    * h.crf / h.annual_output_t
    + h.vessel_pressure_premium(V)
)
base = reactor + h.state_process_cost
mask = V <= h.V_CAP
base = np.where(mask, base, np.inf)
metal_coeff = np.where(mask, metal_coeff, np.inf)

def optimum(q):
    total = base + metal_coeff * q
    i = int(np.argmin(total))
    return float(total[i]), i

# q = (1-recovery)/life_y. Solve the largest q that still reaches Fe parity.
lo, hi = 0.0, 0.1
for _ in range(80):
    mid = 0.5 * (lo + hi)
    if optimum(mid)[0] <= FE:
        lo = mid
    else:
        hi = mid
qcrit = lo
cost, i = optimum(qcrit)

rows = []
for life in (5, 10, 15, 20, 25, 30, 40, 50):
    rows.append({
        "life_y": life,
        "required_recovery_fraction": 1.0 - qcrit * life,
        "required_recovery_percent": 100.0 * (1.0 - qcrit * life),
    })
with (HERE / "scaling_lifecycle_exact_global_boundary.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

keypoints = []
for life, recovery in ((10.0, 0.99), (15.0, 0.99), (20.0, 0.99), (20.0, 0.98)):
    q = (1.0 - recovery) / life
    c, k = optimum(q)
    keypoints.append({
        "life_y": life,
        "recovery": recovery,
        "effective_price_USD_kg": P_RU * (1.0 - recovery) * (10.0 / life),
        "best_cost_USD_t": c,
        "margin_vs_Fe_USD_t": c - FE,
        "E_N_eV": float(best_en[k]),
        "T_C": float(h.state_T[k]),
        "P_bar": float(h.state_P[k]),
        "Tsep_C": float(h.state_Tsep[k]),
        "V_m3": float(V[k]),
        "reaches_parity": bool(c <= FE),
    })
with (HERE / "scaling_lifecycle_exact_keypoints.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(keypoints[0]))
    w.writeheader()
    w.writerows(keypoints)

summary = {
    "schema": "nh3-final-1.1-strict-scaling-lifecycle-reachability-v2",
    "no_new_DFT": True,
    "process_states": 14136,
    "baseline_regression_anchor": {"Ru_cost_USD_t": check, "E_N_eV": strict_en},
    "Fe_reference_cost_USD_t": FE,
    "critical_lifecycle_factor_q_per_y": qcrit,
    "effective_price_parity_at_10y_USD_kg": P_RU * 10.0 * qcrit,
    "parity_state": {
        "E_N_eV": float(best_en[i]),
        "T_C": float(h.state_T[i]),
        "P_bar": float(h.state_P[i]),
        "Tsep_C": float(h.state_Tsep[i]),
        "V_m3": float(V[i]),
        "cost_USD_t": cost,
    },
    "tested_box_intersects": bool((1.0 - qcrit * 20.0) <= 0.99),
    "required_recovery_at_20y": 1.0 - qcrit * 20.0,
    "required_life_at_99pct_recovery_y": 0.01 / qcrit,
    "keypoints": keypoints,
}
(HERE / "scaling_lifecycle_exact_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
