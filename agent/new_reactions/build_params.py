"""Write params.json for plant_models.py. Metal prices reuse the repository's frozen sets (NH3 harness PRICE and
USGS MCS 2026, as in analysis/meoh_catalyst_cost_2026_10_06); process parameters carry their source in SOURCES."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis" / "meoh_catalyst_cost_2026_10_06"))
FROZEN = {'Ru': 53852.5, 'Os': 142650.0, 'Fe': 8.0, 'Rh': 265243.65919095, 'Ir': 252383.36056351,
          'Co': 56.28401553583051, 'Re': 5757.64, 'Mo': 91.22728409215301, 'Ni': 16.9094555095895,
          'W': 149.97, 'Pd': 40670.694409279, 'Pt': 51508.71107755406, 'Cu': 13.889122517655,
          'Ag': 1823.590345370992, 'Au': 128732.2322756058}   # provenance/nh3_final_1_2/source_harness/harness_core.py
prices = dict(FROZEN)
for r in csv.DictReader(open(REPO / "analysis/nh3_alloy_extension_2026_10_05/element_prices_usgs_mcs2026.csv", encoding="utf-8")):
    prices.setdefault(r["element"], float(r["price_USD_per_kg_metal"]))
prices.update({"Ce": 1.71 / 0.81408, "Si": 130.0 * 2.20462 / 100, "Mg": 2.5, "Ca": 0.26 / 0.71469,
               "K": 1.2 / 0.83014, "Ba": 0.21 / 0.58840, "B": 1.0})  # MCS 2026 as in catalyst_prices.py; B: placeholder

P = json.loads((HERE / "params_process.json").read_text(encoding="utf-8"))
P["common"]["metal_usd_per_kg"] = prices
(HERE / "params.json").write_text(json.dumps(P, indent=1), encoding="utf-8")
print(len(prices), "element prices; written params.json")
