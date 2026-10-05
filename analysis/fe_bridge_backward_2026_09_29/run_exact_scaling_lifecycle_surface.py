"""Exact strict-scaling x lifecycle reachability audit for NH3-FINAL-1.1.

This is the missing physical-reachability test after the backward target region is
defined. It performs NO DFT and refuses to rebuild the frozen response surface.
It must be run on the original NH3-FINAL-1.1 harness machine with the existing
14136-state cached response.

For each Ru descriptor E_N on the frozen strict-scaling grid, the cached response
surface supplies the state-resolved logTOF vector. Ru is then fully reoptimized over
all process states while lifetime/recovery enter through the exact effective metal price

    P_eff = P_Ru * (1-r) * (10 y / L).

The primary question is whether the prespecified lifecycle envelope
L <= 20 y and r <= 0.99 intersects the strict E_N scaling manifold at C_Ru <= C_Fe.

Usage:
  python run_exact_scaling_lifecycle_surface.py /path/to/Catalyst_Economic_Leverage_Automation_Harness_v0.1

Outputs:
  scaling_lifecycle_exact_boundary.csv
  scaling_lifecycle_exact_keypoints.csv
  scaling_lifecycle_exact_summary.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HARNESS = Path(
    sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NH3_HARNESS", ".")
).resolve()
sys.path.insert(0, str(HARNESS))

from harness_core import EN0_CANON, NH3Harness, PRICE  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))

h = NH3Harness(cfg, HARNESS)
resp, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild frozen scientific assets")
if h.NSTATE != 14136:
    raise SystemExit(f"process-state count drift: {h.NSTATE}")

FE_COST = float(res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
P_RU = float(PRICE["Ru"])
BASELINE_STRICT_COST = float(res["backward_reachability"]["Ru_best_scaling_cost_USD_t"])
BASELINE_STRICT_EN = float(res["backward_reachability"]["Ru_best_scaling_EN_eV"])

# Use exactly the E_N values already frozen in the canonical scaling-reachability closure
# when the repository copy is available. Fall back to the same 0.005 eV grid.
scaling_csv = (
    REPO
    / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
    / "closure/scaling_reachability.csv"
)
if scaling_csv.exists():
    with scaling_csv.open(encoding="utf-8", newline="") as fh:
        en_grid = np.array([float(r["E_N_eV"]) for r in csv.DictReader(fh)], dtype=float)
else:
    en_grid = np.arange(-2.2, 0.2000001, 0.005, dtype=float)


def q(x: float, n: int = 9) -> float:
    y = round(float(x), n)
    return 0.0 if abs(y) < 10 ** (-n) else y


def ru_opt_at_en(en: float, effective_price: float):
    """Full 14136-state optimum for one strict-scaling descriptor value."""
    logv = h.interp_state_vector(resp, float(en))
    total, V, _metal, _reactor = h.cost_arrays("Ru", logv, price=effective_price)
    ok = V <= h.V_CAP
    if not ok.any():
        return None
    i = int(np.argmin(np.where(ok, total, np.inf)))
    return {
        "cost": float(total[i]),
        "V_m3": float(V[i]),
        "T_C": float(h.state_T[i]),
        "P_bar": float(h.state_P[i]),
        "Tsep_C": float(h.state_Tsep[i]),
    }


def best_on_scaling(effective_price: float):
    best = None
    for en in en_grid:
        opt = ru_opt_at_en(float(en), effective_price)
        if opt is None:
            continue
        if best is None or opt["cost"] < best["cost"]:
            best = {"E_N_eV": float(en), **opt}
    return best


# Regression anchor: with canonical price, reproduce the published strict-scaling minimum.
baseline = best_on_scaling(P_RU)
if baseline is None:
    raise SystemExit("no feasible Ru point on strict-scaling grid")
if abs(baseline["cost"] - BASELINE_STRICT_COST) > 1e-7:
    raise SystemExit(
        f"strict-scaling baseline cost drift: {baseline['cost']} vs {BASELINE_STRICT_COST}"
    )
if abs(baseline["E_N_eV"] - BASELINE_STRICT_EN) > 1e-12:
    raise SystemExit(
        f"strict-scaling baseline E_N drift: {baseline['E_N_eV']} vs {BASELINE_STRICT_EN}"
    )


def parity_effective_price_at_en(en: float):
    """Largest effective Ru price whose full process optimum at this E_N reaches Fe parity."""
    opt0 = ru_opt_at_en(en, 0.0)
    if opt0 is None or opt0["cost"] > FE_COST:
        return None
    lo, hi = 0.0, P_RU
    while ru_opt_at_en(en, hi)["cost"] <= FE_COST:
        hi *= 2.0
        if hi > 1e8:
            raise RuntimeError("failed to bracket effective-price parity")
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if ru_opt_at_en(en, mid)["cost"] <= FE_COST:
            lo = mid
        else:
            hi = mid
    return lo, ru_opt_at_en(en, lo)


# Boundary over E_N and lifecycle. Recovery can be read directly from P_eff*.
boundary_rows = []
for en in en_grid:
    ans = parity_effective_price_at_en(float(en))
    if ans is None:
        continue
    pcrit, opt = ans
    row = {
        "E_N_eV": q(en, 6),
        "parity_effective_Ru_price_USD_kg": q(pcrit, 6),
        "boundary_T_C": int(round(opt["T_C"])),
        "boundary_P_bar": int(round(opt["P_bar"])),
        "boundary_Tsep_C": int(round(opt["Tsep_C"])),
        "boundary_V_m3": q(opt["V_m3"], 9),
    }
    for life in (5.0, 10.0, 15.0, 20.0):
        row[f"required_recovery_at_{int(life)}y"] = q(
            1.0 - pcrit / P_RU * (life / 10.0), 9
        )
    boundary_rows.append(row)

if not boundary_rows:
    raise SystemExit("strict-scaling manifold never reaches Fe parity even at zero effective Ru price")

with (HERE / "scaling_lifecycle_exact_boundary.csv").open(
    "w", encoding="utf-8", newline=""
) as fh:
    w = csv.DictWriter(fh, fieldnames=list(boundary_rows[0]))
    w.writeheader()
    w.writerows(boundary_rows)

# Representative prespecified lifecycle combinations.
key_rows = []
for life, recovery in (
    (10.0, 0.99),
    (15.0, 0.99),
    (20.0, 0.99),
    (20.0, 0.98),
):
    peff = P_RU * (1.0 - recovery) * (10.0 / life)
    best = best_on_scaling(peff)
    key_rows.append(
        {
            "catalyst_life_y": int(life),
            "Ru_recovery_fraction": q(recovery, 6),
            "effective_Ru_price_USD_kg": q(peff, 6),
            "best_strict_scaling_E_N_eV": q(best["E_N_eV"], 6),
            "best_Ru_cost_USD_t": q(best["cost"], 9),
            "margin_vs_Fe_USD_t": q(best["cost"] - FE_COST, 9),
            "T_C": int(round(best["T_C"])),
            "P_bar": int(round(best["P_bar"])),
            "Tsep_C": int(round(best["Tsep_C"])),
            "V_m3": q(best["V_m3"], 9),
            "reaches_Fe_parity": bool(best["cost"] <= FE_COST),
        }
    )

with (HERE / "scaling_lifecycle_exact_keypoints.csv").open(
    "w", encoding="utf-8", newline=""
) as fh:
    w = csv.DictWriter(fh, fieldnames=list(key_rows[0]))
    w.writeheader()
    w.writerows(key_rows)

# The corner L=20 y, r=0.99 is monotone-best inside the preregistered lifecycle box.
corner = next(
    r
    for r in key_rows
    if r["catalyst_life_y"] == 20 and abs(r["Ru_recovery_fraction"] - 0.99) < 1e-12
)
summary = {
    "schema": "nh3-final-1.1-strict-scaling-lifecycle-reachability-v1",
    "no_new_DFT": True,
    "cached_response_reused": True,
    "process_states": 14136,
    "Fe_cost_USD_t": q(FE_COST, 9),
    "baseline_regression_anchor": {
        "E_N_eV": q(baseline["E_N_eV"], 6),
        "Ru_cost_USD_t": q(baseline["cost"], 9),
    },
    "tested_lifecycle_envelope": {
        "max_life_y": 20,
        "max_recovery_fraction": 0.99,
    },
    "best_envelope_corner": corner,
    "strict_scaling_joint_region_intersects_tested_lifecycle_envelope": bool(
        corner["reaches_Fe_parity"]
    ),
    "interpretation": (
        "If true, the strict E_N scaling manifold intersects the preregistered "
        "lifecycle envelope; if false, the backward target region remains outside it."
    ),
}
(HERE / "scaling_lifecycle_exact_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
