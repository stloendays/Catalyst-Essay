"""Common-reference layerwise inversion diagnostic for the NH3 top three.

This is a deterministic diagnostic from frozen FINAL-1.1 inputs. It does not run DFT
or process optimization. It asks where the Ru/Os/Fe order first changes if the
673 K atomistic activity is converted sequentially into (i) normalized active-metal
demand and then (ii) annualized metal replacement cost.

The active-metal normalization is exactly the one used by NH3Harness.cost_arrays:
  active_kg = nh3_mol_s * MW_metal / F_CAL * 10**(-log10_TOF)

Replacement cost uses the frozen 10-y catalyst life, zero recovery and 1000-tpd,
95%-capacity-factor annual output.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
RES = json.loads((RUN / "results.json").read_text(encoding="utf-8"))

MW_NH3_KG_MOL = 0.01703052
PLANT_TPD = 1000.0
CAPACITY_FACTOR = 0.95
F_CAL = 89806.49638662045
LIFE_Y = 10.0
RECOVERY = 0.0

MW = {"Ru": 101.07, "Os": 190.23, "Fe": 55.845}
PRICE = {"Ru": 53852.5, "Os": 142650.0, "Fe": 8.0}

nh3_mol_s = PLANT_TPD * 1000.0 / MW_NH3_KG_MOL / 86400.0
annual_output_t = PLANT_TPD * 365.0 * CAPACITY_FACTOR

rows = []
for m in ("Ru", "Os", "Fe"):
    logtof = float(RES["deterministic"]["metals"][m]["activity_logTOF"])
    active = nh3_mol_s * MW[m] / F_CAL * 10.0 ** (-logtof)
    replacement = active * PRICE[m] * (1.0 - RECOVERY) / LIFE_Y / annual_output_t
    rows.append({
        "metal": m,
        "activity_log10_TOF_673K": logtof,
        "required_active_metal_kg_common_reference": active,
        "metal_price_USD_kg": PRICE[m],
        "annualized_replacement_cost_USD_t_NH3": replacement,
    })

activity_order = sorted(rows, key=lambda r: r["activity_log10_TOF_673K"], reverse=True)
demand_order = sorted(rows, key=lambda r: r["required_active_metal_kg_common_reference"])
cost_order = sorted(rows, key=lambda r: r["annualized_replacement_cost_USD_t_NH3"])
for rank, r in enumerate(activity_order, 1):
    r["activity_rank"] = rank
for rank, r in enumerate(demand_order, 1):
    r["demand_rank_low_is_better"] = rank
for rank, r in enumerate(cost_order, 1):
    r["replacement_cost_rank_low_is_better"] = rank

out = Path(__file__).with_name("inversion_layer_common_reference.csv")
with out.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

assert [r["metal"] for r in activity_order] == ["Ru", "Os", "Fe"]
assert [r["metal"] for r in demand_order] == ["Ru", "Os", "Fe"]
assert [r["metal"] for r in cost_order] == ["Fe", "Ru", "Os"]
print("activity -> demand:", " > ".join(r["metal"] for r in demand_order))
print("after metal-price weighting:", " < ".join(r["metal"] for r in cost_order))
