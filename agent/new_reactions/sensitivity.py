"""One-at-a-time sensitivity of the headline numbers to the plant parameters (results/sensitivity_<rxn>.csv).
Headline numbers: reference cost and its largest share, spread of the literature catalysts (p10-p90, as % of the
reference), groups where the productivity leader is not the plant-cost leader, records below the reference,
and the cost change for +1 point selectivity vs +10 % activity at the reference."""
import copy
import csv
import json
import statistics as st
import sys
from pathlib import Path

import analyze as an
import plant_models as pm

HERE = Path(__file__).resolve().parent
BASE = copy.deepcopy(pm.PARAMS)
VARIANTS = {
    "pdh": [("base", None, None),
            ("propane 373 USD/t (EIA 2023)", ("pdh", "prices", "propane_usd_t"), 373.0),
            ("propane 570 USD/t (EIA 2022)", ("pdh", "prices", "propane_usd_t"), 570.0),
            ("propane 650 USD/t (Asia)", ("pdh", "prices", "propane_usd_t"), 650.0),
            ("gas 12 USD/GJ", ("common", "gas_usd_per_GJ"), 12.0),
            ("capex x0.5", ("pdh", "capex", "usd"), 0.65e9),
            ("capex x1.5", ("pdh", "capex", "usd"), 1.95e9),
            ("approach 0.8", ("pdh", "plant", "approach"), 0.8),
            ("plant 3 bar", ("pdh", "plant", "P_bar"), 3.0),
            ("catalyst life 1 y", ("pdh", "catalyst_life_y"), 1.0),
            ("regeneration 2 h", ("pdh", "t_regen_h"), 2.0)],
    "ch4": [("base", None, None),
            ("H2 2 USD/kg (grey)", ("ch4", "prices", "h2_usd_kg"), 2.0),
            ("H2 6 USD/kg (electrolytic)", ("ch4", "prices", "h2_usd_kg"), 6.0),
            ("CO2 50 USD/t", ("ch4", "prices", "co2_usd_t"), 50.0),
            ("capex 130 EUR/kW", ("ch4", "capex", "usd"), 130 * 1.33 * 96354),
            ("capex 400 EUR/kW", ("ch4", "capex", "usd"), 400 * 1.33 * 96354),
            ("capex 1000 EUR/kW", ("ch4", "capex", "usd"), 1000 * 1.33 * 96354),
            ("plant 1 bar", ("ch4", "plant", "P_bar"), 1.01325),
            ("catalyst life 1 y", ("ch4", "catalyst_life_y"), 1.0)],
}


def setp(path, v):
    d = pm.PARAMS
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v


def headline(rxn, rows):
    ref = pm.reference_record(rxn)
    c_ref, d_ref = an.cost(rxn, ref, detail=True)
    costs = []
    for r in rows:
        costs.append(an.cost(rxn, r["rec"]))
        r["cost"] = costs[-1]
    costs.sort()
    p10, p90 = costs[len(costs) // 10], costs[(9 * len(costs)) // 10]
    G = an.groups(rows)
    differ = sum(1 for m in G.values() if max(m, key=lambda r: r["r_kg_kg_h"]) is not min(m, key=lambda r: r["cost"]))
    big = max(d_ref["parts"], key=d_ref["parts"].get)
    x = dict(ref, S=min(ref["S"] + 0.01, 1.0))
    y = dict(ref, r=ref["r"] * 1.1)
    return dict(ref_cost=round(c_ref, 1), largest_part=big, largest_share=round(d_ref["parts"][big] / c_ref, 3),
                spread_p10_p90_pct=round(100 * (p90 - p10) / c_ref, 2), groups=len(G), productivity_leader_differs=differ,
                below_reference=sum(1 for c in costs if c < c_ref), n=len(costs),
                dS_1pt=round(an.cost(rxn, x) - c_ref, 2), dr_10pct=round(an.cost(rxn, y) - c_ref, 2))


def run(rxn):
    rows = an.load(rxn)
    for r in rows:
        r["rec"]["xeq_lab"] = pm.lab_xeq(rxn, r["rec"])
    out = []
    for name, path, v in VARIANTS[rxn]:
        pm.PARAMS.clear()
        pm.PARAMS.update(copy.deepcopy(BASE))
        if path:
            setp(path, v)
        pm.init_reference()
        out.append(dict(variant=name, **headline(rxn, rows)))
        print(rxn, out[-1], flush=True)
    pm.PARAMS.clear()
    pm.PARAMS.update(copy.deepcopy(BASE))
    pm.init_reference()
    with open(HERE / "results" / f"sensitivity_{rxn}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    for rxn in sys.argv[1:] or ["pdh", "ch4"]:
        run(rxn)
