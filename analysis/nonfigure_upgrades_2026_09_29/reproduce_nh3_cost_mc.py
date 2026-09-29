"""Reconstruct the preregistered 5,000-draw NH3 cost-side Monte Carlo.

This script reproduces the existing 2026-09-20 cost summary exactly and adds
normalized decision-regret quantiles. It uses the frozen harness equations and
a compact deterministic kinetic-input extract whose workbook SHA256 is pinned.

No DFT, new process model, or LLM call is involved.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SRC = ROOT / "provenance/discover_v1/source_harness"
sys.path.insert(0, str(SRC))
import harness_core as HC  # noqa: E402

CANON = SRC / "outputs/nh3_final_20260905T134204Z/manifest_resolved.yaml"
EXISTING = ROOT / "analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json"
INPUTS = HERE / "nh3_cost_mc_repro_inputs.json"
EXPECTED = HERE / "nh3_cost_mc_regret_summary.json"

cfg = yaml.safe_load(CANON.read_text(encoding="utf-8"))
kin = json.loads(INPUTS.read_text(encoding="utf-8"))

# The source workbook is not stored in Git. Replace only the parsing stage with
# the committed deterministic extract; all kinetic/process/economic equations
# still come from the frozen harness.
def _embedded_activity_source(_path):
    gasrec = {
        k: {"surface": None, "phase": "gas", "site": None, "species": k,
            "E": float(v["E"]), "freqs": [float(x) for x in v["freqs"]]}
        for k, v in kin["gasrec"].items()
    }
    return {
        "rows": [],
        "D": {},
        "fits": {k: (float(v[0]), float(v[1])) for k, v in kin["fits"].items()},
        "median_freqs": {k: [float(x) for x in v] for k, v in kin["median_freqs_meV"].items()},
        "gasrec": gasrec,
        "workbook_activity_order": kin["activity_order"],
        "direct_ru_tof": None,
        "scaling_ru_tof": None,
    }

HC.parse_activity_workbook = _embedded_activity_source
cfg["inputs"]["activity_workbook"] = "__embedded__/nh3_cost_mc_repro_inputs.json"
h = HC.NH3Harness(cfg, SRC)

assert h.NSTATE == 14136
fe_vec = h.frozen_state_logtof(h.EN0["Fe"])
ru_vec = h.frozen_state_logtof(h.EN0["Ru"])

def evaluate(metal, vec, *, price, life_y, capex_multiplier, electricity):
    _, V, metal_cost, reactor = h.cost_arrays(
        metal, vec, price=price, life_y=life_y
    )
    elec_scale = float(electricity) / h.ELECTRICITY
    opex = (h.state_fresh + h.state_reccomp + h.state_refrig) * elec_scale
    total = metal_cost + capex_multiplier * (reactor + h.state_compcapex) + opex
    ok = V <= h.V_CAP
    i = int(np.argmin(np.where(ok, total, np.inf)))
    return float(total[i]), i

# Baseline regression gate.
fe0, _ = evaluate(
    "Fe", fe_vec, price=HC.PRICE["Fe"], life_y=h.CATALYST_LIFE_Y,
    capex_multiplier=1.0, electricity=h.ELECTRICITY
)
ru0, _ = evaluate(
    "Ru", ru_vec, price=HC.PRICE["Ru"], life_y=h.CATALYST_LIFE_Y,
    capex_multiplier=1.0, electricity=h.ELECTRICITY
)
assert abs(fe0 - 15.291704676621144) < 1e-10
assert abs(ru0 - 22.03059478781101) < 1e-10

# Exact preregistered draw construction. The five arrays are drawn in blocks;
# this order is required for byte-stable reproduction of the 2026-09-20 result.
N = 5000
rng = np.random.default_rng(20260920)
fe_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
ru_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
cap = rng.uniform(0.8, 1.2, N)
elec = rng.uniform(20.0, 100.0, N)
life = rng.uniform(5.0, 20.0, N)

rows = []
for d in range(N):
    fe, fi = evaluate(
        "Fe", fe_vec, price=HC.PRICE["Fe"] * float(fe_pm[d]),
        life_y=float(life[d]), capex_multiplier=float(cap[d]),
        electricity=float(elec[d])
    )
    ru, ri = evaluate(
        "Ru", ru_vec, price=HC.PRICE["Ru"] * float(ru_pm[d]),
        life_y=float(life[d]), capex_multiplier=float(cap[d]),
        electricity=float(elec[d])
    )
    gap = ru - fe
    rows.append({
        "draw": d,
        "Fe_price_multiplier": float(fe_pm[d]),
        "Ru_price_multiplier": float(ru_pm[d]),
        "capex_multiplier": float(cap[d]),
        "electricity_USD_MWh": float(elec[d]),
        "catalyst_life_y": float(life[d]),
        "Fe_cost_USD_t": fe,
        "Ru_cost_USD_t": ru,
        "gap_Ru_minus_Fe_USD_t": gap,
        "normalized_regret": gap / fe,
        "Fe_P_bar": float(h.state_P[fi]),
        "Ru_P_bar": float(h.state_P[ri]),
    })

out_csv = HERE / "nh3_cost_mc_draws_reproduced.csv"
with out_csv.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

gap = np.array([r["gap_Ru_minus_Fe_USD_t"] for r in rows])
reg = np.array([r["normalized_regret"] for r in rows])
fe_cost = np.array([r["Fe_cost_USD_t"] for r in rows])
ru_cost = np.array([r["Ru_cost_USD_t"] for r in rows])

existing = json.loads(EXISTING.read_text(encoding="utf-8"))
v = existing["full_14136_state_direct_cost_verification"]

# Exact reproduction of the already promoted 2026-09-20 summary.
assert float(np.mean(gap > 0)) == v["P_C_Fe_lt_C_Ru"] == 1.0
assert abs(float(np.min(gap)) - v["minimum_Ru_minus_Fe_USD_t"]) < 1e-12
for q, key in ((0.05, "p05"), (0.50, "p50"), (0.95, "p95")):
    assert abs(float(np.quantile(gap, q)) - v["Ru_minus_Fe_USD_t_quantiles"][key]) < 1e-12
    assert abs(float(np.quantile(fe_cost, q)) - existing["Fe_cost_USD_t_quantiles"][key]) < 1e-12
    assert abs(float(np.quantile(ru_cost, q)) - existing["Ru_cost_USD_t_quantiles"][key]) < 1e-12

expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
rq = expected["regret_quantiles"]
assert abs(float(np.min(reg)) - rq["min"]) < 1e-12
assert abs(float(np.quantile(reg, 0.05)) - rq["p05"]) < 1e-12
assert abs(float(np.quantile(reg, 0.50)) - rq["p50"]) < 1e-12
assert abs(float(np.quantile(reg, 0.95)) - rq["p95"]) < 1e-12
assert abs(float(np.max(reg)) - rq["max"]) < 1e-12
assert float(np.mean(reg > 0)) == expected["P_regret_gt_0"] == 1.0

print("PASS NH3 5000-draw cost MC reconstruction")
print(f"regret p05/median/p95 = {np.quantile(reg,.05):.6f} / {np.median(reg):.6f} / {np.quantile(reg,.95):.6f}")
print(out_csv)
