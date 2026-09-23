"""Figure 1 source table, taken only from pinned, CI-validated provenance.

  descriptor E_N and metal price : provenance/discover_v1/source_harness/DISCOVER_TASK_V1.json
  activity, bed volume, cost, ranks, rolling Top-K :
      provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/results.json

Guards reproduce the NH3-FINAL-1.1 frozen regression values; the script stops
rather than writing a table if any of them fails.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TASK = os.path.join(REPO, "provenance/discover_v1/source_harness/DISCOVER_TASK_V1.json")
RES = os.path.join(REPO, "provenance/nh3_final_1_1/source_harness/outputs/"
                         "nh3_final_20260905T134204Z/results.json")

task = json.load(open(TASK, encoding="utf-8"))
det = json.load(open(RES, encoding="utf-8"))["deterministic"]

act, eco = det["activity_order"], det["raw_economic_order"]
assert act[:3] == ["Ru", "Os", "Fe"] and eco[:3] == ["Fe", "Ru", "Os"], "frontier order changed"
assert abs(det["raw_global_spearman"] - 0.9285714285714284) < 1e-12, "global rho changed"
assert det["process_state_count"] == 14136, "process-state library changed"
costs = {m: det["metals"][m]["unconstrained"]["total_cost"] for m in ("Fe", "Ru", "Os")}
for m, v in (("Fe", 15.291704676621144), ("Ru", 22.03059478781101), ("Os", 25.832)):
    assert abs(costs[m] - v) < 5e-4, "%s cost changed" % m

desc = {c["id"]: c for c in task["candidate_set"]}
assert set(desc) == set(act), "candidate set mismatch"

rows = []
for m in act:
    d = det["metals"][m]
    rows.append({
        "metal": m,
        "E_N_eV": desc[m]["descriptor_E_N_eV"],
        "price_USD_kg": desc[m]["price_USD_kg"],
        "logTOF_673K": d["activity_logTOF"],
        "min_bed_m3": d["min_bed_m3"],
        "log10_min_bed_m3": math.log10(d["min_bed_m3"]),
        "feasible_90m3": int(d["min_bed_m3"] <= 90.0),
        "cost_USD_t": d["unconstrained"]["total_cost"],
        "atomic_rank": act.index(m) + 1,
        "economic_rank": eco.index(m) + 1,
    })
with open(os.path.join(HERE, "fig1_metals.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

with open(os.path.join(HERE, "fig1_rolling.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["K", "rho_raw", "rho_censored", "n_feasible"], lineterminator="\n")
    w.writeheader()
    for r in det["rolling"]:
        w.writerow({k: r[k] for k in ("K", "rho_raw", "rho_censored", "n_feasible")})

print("wrote fig1_metals.csv (%d metals, %d feasible) and fig1_rolling.csv (%d K values)"
      % (len(rows), sum(r["feasible_90m3"] for r in rows), len(det["rolling"])))
