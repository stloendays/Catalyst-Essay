"""Fast exact strict-scaling x lifecycle closure for the selected NH3 model (NH3_MODEL=1.1|1.2).

No DFT is run and no response cache is required. The calculation uses the selected model's
equations and all of its process states (1.1: 14,136; 1.2: 14,510).

Key reduction: at fixed process state, E_N affects cost only through TOF -> active
metal -> bed volume. Metal replacement, reactor volume and pressure-vessel terms are
all monotone in active metal / volume, while the process-state cost is independent of
E_N. Therefore the cost-minimizing E_N for that state is simply its TOF-maximizing
E_N, independent of catalyst lifetime or metal recovery. We find that statewise
optimum on the canonical 0.005-eV strict-scaling grid, then construct the exact lower
cost envelope over all states.

Model version (analysis/nh3_model.py): NH3_MODEL=1.1 (default) writes the committed files next to this
script; NH3_MODEL=1.2 writes the same files to nh3_1_2/. The regression anchors (Fe cost, strict-scaling
minimum and its E_N, process-state count) are read from the selected run's results.json.

Usage:
  python run_statewise_strict_scaling_lifecycle.py [harness_root]
  (harness_root defaults to $NH3_HARNESS for 1.1 and $NH3_HARNESS_1_2 for 1.2, see nh3_model.py)
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if len(sys.argv) > 1:  # explicit harness root for the selected version
    os.environ["NH3_HARNESS" if os.environ.get("NH3_MODEL", "1.1") == "1.1" else "NH3_HARNESS_1_2"] = sys.argv[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

hc = NM.core()
PRICE = hc.PRICE
A = NM.anchors()
res = json.loads((NM.run_dir() / "results.json").read_text(encoding="utf-8"))
h = NM.harness()
if h.NSTATE != A["NSTATE"]:
    raise SystemExit(f"process-state count drift: {h.NSTATE} vs {A['NSTATE']}")
OUT = NM.out_dir(HERE)
LABEL = {"1.1": "FINAL-1.1", "1.2": "FINAL-1.2"}[NM.VERSION]
CREATED = {"1.1": "2026-09-29", "1.2": "2026-10-13"}[NM.VERSION]

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


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        # booleans as lower-case JSON literals, as in the promoted files
        w.writerows([{k: (str(v).lower() if isinstance(v, bool) else v) for k, v in r.items()} for r in rows])


rows = []
for life in (5, 10, 15, 20, 25, 30, 40, 50):
    rows.append({
        "life_y": life,
        "required_recovery_fraction": 1.0 - qcrit * life,
        "required_recovery_percent": 100.0 * (1.0 - qcrit * life),
    })
write_csv(OUT / "scaling_lifecycle_exact_global_boundary.csv", rows)

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
write_csv(OUT / "scaling_lifecycle_exact_keypoints.csv", keypoints)

# Promoted summary (schema v2). The tested lifecycle box is life <= 20 y, recovery <= 0.99; its best corner is
# 20 y / 99 % because cost is monotone in q = (1 - r) / L.
corner = next(k for k in keypoints if k["life_y"] == 20.0 and k["recovery"] == 0.99)
margin = corner["margin_vs_Fe_USD_t"]
intersects = bool(corner["best_cost_USD_t"] <= FE)
rec20 = 1.0 - qcrit * 20.0
life99 = 0.01 / qcrit
if not intersects:
    verdict = (
        "but the preregistered lifecycle box (life <= 20 y, recovery <= 0.99) still does not intersect it. "
        f"The nearest tested corner misses Fe by {margin:.4f} USD/t NH3 ({100 * margin / FE:.2f}%). "
        f"Parity is reached just outside the box, e.g. at 20 y with {100 * rec20:.4f}% recovery "
        f"or at 99% recovery with {life99:.2f} y lifetime."
    )
else:
    verdict = (
        "and the preregistered lifecycle box (life <= 20 y, recovery <= 0.99) intersects it. "
        f"The best tested corner (20 y, 99% recovery) is below Fe by {-margin:.4f} USD/t NH3 "
        f"({-100 * margin / FE:.2f}%). Parity is reached inside the box, e.g. at 20 y with {100 * rec20:.4f}% "
        f"recovery or at 99% recovery with {life99:.2f} y lifetime."
    )
summary = {
    "schema": f"nh3-{LABEL.lower()}-strict-scaling-lifecycle-reachability-v2",
    "created_date": CREATED,
    "no_new_DFT": True,
    "method": (
        f"For each of the {h.NSTATE:,} frozen {LABEL} process states, maximize strict-scaling TOF over the canonical "
        "0.005-eV E_N grid. At fixed state, metal inventory, reactor volume and vessel cost are monotone in required "
        "active metal / bed volume, so the E_N that maximizes TOF is also the cost-minimizing E_N for every "
        "lifetime/recovery value. The global lifecycle boundary is then the lower envelope over all states."
    ),
    "process_states": h.NSTATE,
    "strict_scaling_E_N_domain_eV": [-2.2, 0.2],
    "canonical_grid_step_eV": 0.005,
    "baseline_regression_anchor": {
        "Ru_cost_USD_t": check,
        "E_N_eV": strict_en,
        "canonical_Ru_cost_target_USD_t": strict_ref,
        "status": "PASS",
    },
    "Fe_reference_cost_USD_t": FE,
    "critical_lifecycle_factor_q_per_y": qcrit,
    "equivalent_effective_Ru_price_at_10y_USD_kg": P_RU * 10.0 * qcrit,
    "strict_scaling_parity_state": {
        "E_N_eV": float(best_en[i]),
        "T_C": float(h.state_T[i]),
        "P_bar": float(h.state_P[i]),
        "Tsep_C": float(h.state_Tsep[i]),
        "V_m3": float(V[i]),
        "cost_USD_t": cost,
    },
    "tested_lifecycle_envelope": {
        "max_life_y": 20.0,
        "max_recovery_fraction": 0.99,
        "best_corner": {
            "life_y": corner["life_y"],
            "recovery_fraction": corner["recovery"],
            "best_strict_scaling_cost_USD_t": corner["best_cost_USD_t"],
            "margin_vs_Fe_USD_t": margin,
            "relative_margin_vs_Fe": margin / FE,
            "best_E_N_eV": corner["E_N_eV"],
            "T_C": corner["T_C"],
            "P_bar": corner["P_bar"],
            "Tsep_C": corner["Tsep_C"],
            "V_m3": corner["V_m3"],
        },
        "intersects_strict_scaling_manifold": intersects,
    },
    "boundary_examples": {
        "required_recovery_at_10y": 1.0 - qcrit * 10.0,
        "required_recovery_at_15y": 1.0 - qcrit * 15.0,
        "required_recovery_at_20y": rec20,
        "required_life_at_99pct_recovery_y": life99,
        "required_life_at_98pct_recovery_y": 0.02 / qcrit,
    },
    "interpretation": (
        "The direct activity-only target is unreachable. Allowing lifetime and recovery to improve jointly moves the "
        "economic target much closer to the strict scaling manifold, " + verdict
    ),
}
text = json.dumps(summary, indent=2).replace('[\n    -2.2,\n    0.2\n  ]', '[-2.2, 0.2]')  # promoted layout
(OUT / "scaling_lifecycle_exact_summary.json").write_text(text + "\n", encoding="utf-8", newline="\n")
print(json.dumps(summary, indent=2))
