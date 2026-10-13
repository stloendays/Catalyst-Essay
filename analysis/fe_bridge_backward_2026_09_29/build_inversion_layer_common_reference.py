"""Common-reference layerwise inversion diagnostic for the NH3 top three.

This is a deterministic diagnostic from frozen model inputs. It does not run DFT
or process optimization. It asks where the Ru/Os/Fe order first changes if the
673 K atomistic activity is converted sequentially into (i) normalized active-metal
demand and then (ii) annualized metal replacement cost.

The active-metal normalization is exactly the one used by NH3Harness.cost_arrays:
  active_kg = nh3_mol_s * MW_metal / F_CAL * 10**(-log10_TOF)

Replacement cost uses the frozen 10-y catalyst life, zero recovery and 1000-tpd,
95%-capacity-factor annual output.

Model version (analysis/nh3_model.py): NH3_MODEL=1.1 (default) reads the committed NH3-FINAL-1.1 run under
provenance/nh3_final_1_1 and writes next to this script; NH3_MODEL=1.2 reads the NH3-FINAL-1.2 run under
provenance/nh3_final_1_2 and writes to nh3_1_2/. F_CAL, plant size, capacity factor, catalyst life and recovery
are read from the run's manifest (1.1: F_CAL 89,806.5; 1.2: 74,351.6), the 673 K log10 TOF from its results.json.

Outputs:
  inversion_layer_common_reference.csv
  inversion_layer_table.csv   layer-by-layer summary; the equal-price ablation row is the Ru optimum at the Fe price
                              (8 USD/kg) in the selected model's fully reoptimized Ru price sweep
                              (1.1: figures/composite/fig2/fig2_ru_price_sweep.csv; 1.2: nh3_1_2/ru_price_sweep.csv)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis"))
import nh3_model as NM  # noqa: E402

RUN = ROOT / {"1.1": "provenance/nh3_final_1_1/source_harness/outputs",
              "1.2": "provenance/nh3_final_1_2/source_harness/outputs"}[NM.VERSION] / NM.RUNS[NM.VERSION]
RES = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
CFG = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
OUT = NM.out_dir(HERE)
SWEEP = (ROOT / "figures/composite/fig2/fig2_ru_price_sweep.csv" if NM.VERSION == "1.1"
         else OUT / "ru_price_sweep.csv")

MW_NH3_KG_MOL = 0.01703052
PLANT_TPD = float(CFG["plant"]["production_tpd"])            # 1000
CAPACITY_FACTOR = float(CFG["plant"]["capacity_factor"])     # 0.95
F_CAL = float(CFG["economics"]["calibration_factor"])        # 1.1: 89806.49638662045
LIFE_Y = float(CFG["economics"]["catalyst_life_y"])          # 10
RECOVERY = float(CFG["economics"]["metal_recovery_fraction"])  # 0

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

out = OUT / "inversion_layer_common_reference.csv"
with out.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

assert [r["metal"] for r in activity_order] == ["Ru", "Os", "Fe"]
assert [r["metal"] for r in demand_order] == ["Ru", "Os", "Fe"]
assert [r["metal"] for r in cost_order] == ["Fe", "Ru", "Os"]
print("activity -> demand:", " > ".join(r["metal"] for r in demand_order))
print("after metal-price weighting:", " < ".join(r["metal"] for r in cost_order))

# ---- layer table ----------------------------------------------------------------------------------------------
by = {r["metal"]: r for r in rows}
det = RES["deterministic"]
total = {m: float(det["metals"][m]["feasible"]["total_cost"]) for m in ("Fe", "Ru", "Os")}
with SWEEP.open(encoding="utf-8", newline="") as fh:
    ru_at_fe_price = next(float(r["cost"]) for r in csv.DictReader(fh) if float(r["price_USD_kg"]) == PRICE["Fe"])
act_seq = [r["metal"] for r in activity_order]
dem_seq = [r["metal"] for r in demand_order]
rep_seq = [r["metal"] for r in cost_order]
fin_seq = sorted(total, key=total.get)
pair = sorted((("Ru", ru_at_fe_price), ("Fe", total["Fe"])), key=lambda t: t[1])
dem_status = "preserved" if dem_seq == act_seq else "FIRST FLIP"
rep_status = "preserved" if rep_seq == act_seq else ("FIRST FLIP" if dem_status == "preserved" else "flipped")
table = [
    ("Atomic/MKM intrinsic activity", "higher TOF better", " > ".join(act_seq), "preserved",
     "log10 TOF Ru/Os/Fe = " + "/".join(f"{by[m]['activity_log10_TOF_673K']:.5f}" for m in ("Ru", "Os", "Fe"))
     + " at the common 673 K reference"),
    ("Common-reference catalyst demand", "lower required active metal better", " < ".join(dem_seq), dem_status,
     "active metal demand Ru/Os/Fe = "
     + "/".join(f"{by[m]['required_active_metal_kg_common_reference']:.1f}" for m in ("Ru", "Os", "Fe"))
     + " kg under the same plant-throughput normalization"),
    ("Common-reference catalyst replacement economics", "lower annualized replacement cost better",
     " < ".join(rep_seq), rep_status,
     f"canonical prices and {LIFE_Y:.0f}-y life give Fe/Ru/Os = "
     + "/".join(f"{by[m]['annualized_replacement_cost_USD_t_NH3']:.3f}" for m in ("Fe", "Ru", "Os"))
     + " USD/t NH3; no reactor/process cost is included"),
    ("Equal-price full-process causal ablation", "lower total cost better", f"{pair[0][0]} < {pair[1][0]} (pairwise)",
     "Fe does not win" if pair[0][0] == "Ru" else "Fe wins",
     f"setting Ru price = Fe price and fully reoptimizing all {det['process_state_count']:,} states gives "
     f"Ru {ru_at_fe_price:.3f} vs Fe {total['Fe']:.3f} USD/t"),
    ("Full canonical process + economics", "lower total cost better", " < ".join(fin_seq),
     "inversion retained/amplified" if fin_seq != act_seq else "no inversion",
     "total Fe/Ru/Os = " + "/".join(f"{total[m]:.3f}" for m in ("Fe", "Ru", "Os")) + " USD/t"),
]
lines = ["layer,metric,order_or_pairwise_result,status,evidence"]
lines += [f'{a},{b},{c},{d},"{e}"' for a, b, c, d, e in table]
(OUT / "inversion_layer_table.csv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("layer table:", " | ".join(f"{t[0]}: {t[2]} ({t[3]})" for t in table))
