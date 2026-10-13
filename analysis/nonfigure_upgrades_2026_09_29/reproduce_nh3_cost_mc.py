"""Reconstruct the preregistered 5,000-draw NH3 cost-side Monte Carlo.

This script reproduces the existing 2026-09-20 cost summary exactly and adds
normalized decision-regret quantiles. It uses the frozen harness equations and
a compact deterministic kinetic-input extract whose workbook SHA256 is pinned.

No DFT, new process model, or LLM call is involved.

Model selection (analysis/nh3_model.py):
    NH3_MODEL=1.1 (default)  NH3-FINAL-1.1 through the in-repo frozen harness
                             provenance/discover_v1/source_harness; checks the
                             committed 2026-09-20 / 2026-09-29 summaries and
                             writes nh3_cost_mc_draws_reproduced.csv here.
    NH3_MODEL=1.2            NH3-FINAL-1.2 (harness_core, manifest and results of
                             the canonical 1.2 run via nh3_model); same seed,
                             priors, draw order and objective; writes to
                             nh3_1_2/ and gates against nh3_1_2/
                             nh3_cost_mc_regret_summary.json (written on first
                             run or with --write).
The response surface is never built: each draw re-optimizes the two frozen
state vectors (Fe and Ru at their canonical E_N) over all process states.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis"))
import nh3_model as NM  # noqa: E402

VERSION = NM.VERSION
WRITE = "--write" in sys.argv[1:]
INPUTS_11 = HERE / "nh3_cost_mc_repro_inputs.json"
if VERSION == "1.1":
    SRC = ROOT / "provenance/discover_v1/source_harness"
    sys.path.insert(0, str(SRC))
    import harness_core as HC  # noqa: E402
    RUN = SRC / "outputs/nh3_final_20260905T134204Z"
    OUT = HERE
else:
    SRC = NM.root()
    HC = NM.core()
    RUN = NM.run_dir()
    OUT = NM.out_dir(HERE)

CANON = RUN / "manifest_resolved.yaml"
EXISTING = ROOT / "analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json"  # 1.1 only
INPUTS = OUT / "nh3_cost_mc_repro_inputs.json"
EXPECTED = OUT / "nh3_cost_mc_regret_summary.json"

cfg = yaml.safe_load(CANON.read_text(encoding="utf-8"))

# Anchors of the selected canonical run (results.json of RUN; for 1.2 this is nh3_model.anchors()).
det = json.loads((RUN / "results.json").read_text(encoding="utf-8"))["deterministic"]
A_NSTATE = int(det["process_state_count"])
A_FE = float(det["metals"]["Fe"]["feasible"]["total_cost"])
A_RU = float(det["metals"]["Ru"]["feasible"]["total_cost"])
# The regret compares the intrinsic-activity winner with the feasible economic winner.
assert det["activity_order"][0] == "Ru" and det["feasible_economic_order"][0] == "Fe"
if VERSION == "1.1":
    assert A_NSTATE == 14136
    assert A_FE == 15.291704676621144 and A_RU == 22.03059478781101
else:
    A = NM.anchors()
    assert (A_NSTATE, A_FE, A_RU) == (A["NSTATE"], A["Fe"], A["Ru"])


def _same_kinetics(a: dict, b: dict, tol: float = 1e-12) -> bool:
    """Kinetic content of two extracts agrees (fits to tol: linregress differs in the last bit across builds)."""
    if a["activity_order"] != b["activity_order"] or a["EN0"] != b["EN0"]:
        return False
    if a["gasrec"] != b["gasrec"] or a["median_freqs_meV"] != b["median_freqs_meV"]:
        return False
    if set(a["fits"]) != set(b["fits"]):
        return False
    return all(abs(x - y) <= tol for k in a["fits"] for x, y in zip(a["fits"][k], b["fits"][k]))


if VERSION != "1.1":
    # 1.2 uses the same workbook (same SHA-256), so its kinetic extract is the 1.1 extract. When the workbook is
    # present, re-extract it with the 1.2 parser and check the content before using (or creating) the 1.2 copy.
    ext11 = json.loads(INPUTS_11.read_text(encoding="utf-8"))
    wb = SRC / cfg["inputs"]["activity_workbook"]
    if wb.exists():
        assert HC.sha256_file(wb) == ext11["source_workbook_sha256"]
        src = HC.parse_activity_workbook(wb)
        fresh = dict(ext11)
        fresh["fits"] = {k: [float(v[0]), float(v[1])] for k, v in src["fits"].items()}
        fresh["median_freqs_meV"] = {k: [float(x) for x in v] for k, v in src["median_freqs"].items()}
        fresh["gasrec"] = {k: {"E": float(v["E"]), "freqs": [float(x) for x in v["freqs"]]} for k, v in src["gasrec"].items()}
        fresh["activity_order"] = list(src["workbook_activity_order"])
        fresh["EN0"] = {m: HC.EN0_CANON[m] for m in ("Fe", "Ru")}
        assert _same_kinetics(fresh, ext11), "1.2 workbook parse differs from the committed kinetic extract"
    if not INPUTS.exists():
        shutil.copyfile(INPUTS_11, INPUTS)
    assert _same_kinetics(json.loads(INPUTS.read_text(encoding="utf-8")), ext11)

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

assert h.NSTATE == A_NSTATE
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
assert abs(fe0 - A_FE) < 1e-10
assert abs(ru0 - A_RU) < 1e-10

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

out_csv = OUT / "nh3_cost_mc_draws_reproduced.csv"
with out_csv.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

gap = np.array([r["gap_Ru_minus_Fe_USD_t"] for r in rows])
reg = np.array([r["normalized_regret"] for r in rows])
fe_cost = np.array([r["Fe_cost_USD_t"] for r in rows])
ru_cost = np.array([r["Ru_cost_USD_t"] for r in rows])

if VERSION == "1.1":
    existing = json.loads(EXISTING.read_text(encoding="utf-8"))
    v = existing["full_14136_state_direct_cost_verification"]

    # Exact reproduction of the already promoted 2026-09-20 summary.
    assert float(np.mean(gap > 0)) == v["P_C_Fe_lt_C_Ru"] == 1.0
    assert abs(float(np.min(gap)) - v["minimum_Ru_minus_Fe_USD_t"]) < 1e-12
    for q, key in ((0.05, "p05"), (0.50, "p50"), (0.95, "p95")):
        assert abs(float(np.quantile(gap, q)) - v["Ru_minus_Fe_USD_t_quantiles"][key]) < 1e-12
        assert abs(float(np.quantile(fe_cost, q)) - existing["Fe_cost_USD_t_quantiles"][key]) < 1e-12
        assert abs(float(np.quantile(ru_cost, q)) - existing["Ru_cost_USD_t_quantiles"][key]) < 1e-12
elif WRITE or not EXPECTED.exists():
    # NH3-FINAL-1.2: no earlier summary exists; write the gate file in the 1.1 schema.
    summary = {
        "schema": "nh3-cost-mc-regret-summary-v1",
        "date": "2026-10-13",
        "model": NM.LABEL,
        "run": NM.RUNS[VERSION],
        "draws": N,
        "seed": 20260920,
        "definition": "R=(C_Ru-C_Fe)/C_Fe for the upstream intrinsic-activity winner Ru versus the downstream economic winner Fe, after per-draw full-process reoptimization under the preregistered cost-side Monte Carlo.",
        "process_state_count": A_NSTATE,
        "deterministic_regret": (A_RU - A_FE) / A_FE,
        "P_regret_gt_0": float(np.mean(reg > 0)),
        "count_regret_gt_0": int(np.sum(reg > 0)),
        "regret_quantiles": {
            "min": float(np.min(reg)),
            "p05": float(np.quantile(reg, 0.05)),
            "p50": float(np.quantile(reg, 0.50)),
            "p95": float(np.quantile(reg, 0.95)),
            "max": float(np.max(reg)),
        },
        "draw_table_sha256": hashlib.sha256(out_csv.read_bytes()).hexdigest(),
        "draw_table_sha256_note": "SHA-256 of nh3_cost_mc_draws_reproduced.csv as written on the generating machine; last-bit float differences across platforms change it, so the gate is the 1e-12 check of the quantiles below and above.",
        "gap_and_cost_quantiles": {
            "gap_min": float(np.min(gap)),
            "gap_p05": float(np.quantile(gap, 0.05)),
            "gap_p50": float(np.quantile(gap, 0.50)),
            "gap_p95": float(np.quantile(gap, 0.95)),
            "Fe_cost_p05": float(np.quantile(fe_cost, 0.05)),
            "Fe_cost_p50": float(np.quantile(fe_cost, 0.50)),
            "Fe_cost_p95": float(np.quantile(fe_cost, 0.95)),
            "Ru_cost_p05": float(np.quantile(ru_cost, 0.05)),
            "Ru_cost_p50": float(np.quantile(ru_cost, 0.50)),
            "Ru_cost_p95": float(np.quantile(ru_cost, 0.95)),
        },
        "pressure_of_optimum_bar_quantiles": {
            "Fe_p05": float(np.quantile([r["Fe_P_bar"] for r in rows], 0.05)),
            "Fe_p50": float(np.quantile([r["Fe_P_bar"] for r in rows], 0.50)),
            "Fe_p95": float(np.quantile([r["Fe_P_bar"] for r in rows], 0.95)),
            "Ru_p05": float(np.quantile([r["Ru_P_bar"] for r in rows], 0.05)),
            "Ru_p50": float(np.quantile([r["Ru_P_bar"] for r in rows], 0.50)),
            "Ru_p95": float(np.quantile([r["Ru_P_bar"] for r in rows], 0.95)),
        },
    }
    EXPECTED.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {EXPECTED}")

expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
rq = expected["regret_quantiles"]
assert abs(float(np.min(reg)) - rq["min"]) < 1e-12
assert abs(float(np.quantile(reg, 0.05)) - rq["p05"]) < 1e-12
assert abs(float(np.quantile(reg, 0.50)) - rq["p50"]) < 1e-12
assert abs(float(np.quantile(reg, 0.95)) - rq["p95"]) < 1e-12
assert abs(float(np.max(reg)) - rq["max"]) < 1e-12
assert float(np.mean(reg > 0)) == expected["P_regret_gt_0"] == 1.0
if VERSION != "1.1":
    gq = expected["gap_and_cost_quantiles"]
    assert abs(float(np.min(gap)) - gq["gap_min"]) < 1e-12
    for q, key in ((0.05, "p05"), (0.50, "p50"), (0.95, "p95")):
        assert abs(float(np.quantile(gap, q)) - gq["gap_" + key]) < 1e-12
        assert abs(float(np.quantile(fe_cost, q)) - gq["Fe_cost_" + key]) < 1e-12
        assert abs(float(np.quantile(ru_cost, q)) - gq["Ru_cost_" + key]) < 1e-12

print("PASS NH3 5000-draw cost MC reconstruction" + ("" if VERSION == "1.1" else f" ({NM.LABEL})"))
print(f"regret p05/median/p95 = {np.quantile(reg,.05):.6f} / {np.median(reg):.6f} / {np.quantile(reg,.95):.6f}")
print(out_csv)
