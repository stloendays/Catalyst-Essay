"""Full 14,136-state joint Ru activity/lifecycle parity sweep.

This script is designed for the original NH3-FINAL-1.1 harness machine. It performs
NO DFT and refuses to rebuild the frozen response surface. It only reuses the cached
MKM/process response and reoptimizes the existing 14,136 process states.

Usage:
  python run_exact_joint_surface.py /path/to/Catalyst_Economic_Leverage_Automation_Harness_v0.1

Outputs are written next to this script.
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

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NH3_HARNESS", ".")).resolve()
sys.path.insert(0, str(HARNESS))

from harness_core import EN0_CANON, NH3Harness, PRICE  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
h = NH3Harness(cfg, HARNESS)
resp, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild frozen scientific assets")
assert h.NSTATE == 14136

FE_COST = float(res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
ALPHA_STAR = float(res["backward_reachability"]["Ru_activity_break_even_multiplier"])
G673 = float(res["backward_reachability"]["Ru_scaling_max_gain_673K"])
GALL = float(res["backward_reachability"]["Ru_scaling_max_gain_all_states"])
P_RU = float(PRICE["Ru"])

logru0 = h.frozen_state_logtof(EN0_CANON["Ru"])


def ru_opt(alpha: float, effective_price: float):
    logv = logru0 + math.log10(alpha)
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


def parity_price(alpha: float):
    lo, hi = 0.0, max(P_RU, 1.0)
    if ru_opt(alpha, lo)["cost"] > FE_COST:
        return None
    while ru_opt(alpha, hi)["cost"] <= FE_COST:
        hi *= 2.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if ru_opt(alpha, mid)["cost"] <= FE_COST:
            lo = mid
        else:
            hi = mid
    return lo, ru_opt(alpha, lo)


# Two exact anchor checks against frozen published results.
p1, _ = parity_price(1.0)
if abs(p1 - 163.76330261666772) > 1e-3:
    raise SystemExit(f"alpha=1 price-parity anchor failed: {p1}")
pa, _ = parity_price(ALPHA_STAR)
if abs(pa - P_RU) > 1e-2:
    raise SystemExit(f"activity-parity anchor failed: {pa} vs {P_RU}")

alpha_grid = sorted(set(
    np.geomspace(1.0, GALL, 41).tolist()
    + [1.0, G673, 1.5, 2.0, 2.25, 2.4, GALL]
))

rows = []
for alpha in alpha_grid:
    pcrit, opt = parity_price(float(alpha))
    row = {
        "alpha": float(alpha),
        "parity_effective_Ru_price_USD_kg": pcrit,
        "T_C": opt["T_C"],
        "P_bar": opt["P_bar"],
        "Tsep_C": opt["Tsep_C"],
        "V_m3": opt["V_m3"],
    }
    for life in (10.0, 15.0, 20.0):
        row[f"required_recovery_at_{int(life)}y"] = 1 - pcrit / P_RU * (life / 10.0)
    rows.append(row)

out_csv = HERE / "activity_lifecycle_exact_full14136.csv"
with out_csv.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

key_peff = P_RU * (1 - 0.98) * (10.0 / 20.0)
key = ru_opt(GALL, key_peff)
summary = {
    "full_process_states": 14136,
    "no_new_DFT": True,
    "cached_response_reused": True,
    "Fe_cost_USD_t": FE_COST,
    "key_point": {
        "activity_multiplier": GALL,
        "life_y": 20.0,
        "recovery": 0.98,
        "effective_price_USD_kg": key_peff,
        **key,
        "margin_vs_Fe_USD_t": key["cost"] - FE_COST,
    },
}
(HERE / "activity_lifecycle_exact_full14136_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
