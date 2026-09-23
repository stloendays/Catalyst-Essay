"""Figure 2 model tables, computed with the frozen NH3-FINAL-1.1 harness.

Read-only with respect to the harness: the canonical run manifest is loaded as-is,
the response surface must come from the existing cache, and nothing is written
outside this directory. Every table is checked against the frozen results before
it is written.

  fig2_pressure_envelopes.csv  lowest feasible cost at each synthesis pressure, T and
                               Tsep reoptimized, for Fe, Ru, Os and Ru priced as Fe
  fig2_ru_price_sweep.csv      Ru reoptimized over all 14,136 states as its metal price
                               varies; the two frozen points (8 and 53,852.5 USD/kg)
                               are included exactly; the last row is the parity price

    CatalystForge/.venv/python fig2_model.py [harness_root]
"""
import csv
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
from harness_core import EN0_CANON, PRICE, NH3Harness  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
h = NH3Harness(cfg, HARNESS)
assert h.NSTATE == 14136, "process-state library changed"
resp, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")

FROZEN = {  # total USD/t, T, P, Tsep
    "Fe": (15.291704676621144, 425.0, 180.0, 30.0),
    "Ru": (22.03059478781101, 450.0, 425.0, 25.0),
    "Os": (25.832, None, None, None),
    "Ru_at_Fe_price": (14.712129952363274, 425.0, 170.0, 30.0),
}
POOLS = ("metal_cost", "reactor_base", "vessel_pressure_premium", "fresh_comp",
         "recycle_comp", "refrigeration", "compressor_capex")

logvec = {m: h.frozen_state_logtof(EN0_CANON[m]) for m in ("Fe", "Ru", "Os")}
CASES = {"Fe": ("Fe", None), "Ru": ("Ru", None), "Os": ("Os", None), "Ru_at_Fe_price": ("Ru", PRICE["Fe"])}


def optimum(metal, price=None, mask=None):
    total, V, metal_cost, reactor = h.cost_arrays(metal, logvec[metal], price=price)
    ok = V <= h.V_CAP
    if mask is not None:
        ok &= mask
    if not ok.any():
        return None
    i = int(np.argmin(np.where(ok, total, np.inf)))
    row = dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
               Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]))
    row.update(h.cost_breakdown_at(metal, V, metal_cost, reactor, i))
    return row


# ---- frozen optima reproduce --------------------------------------------------
for case, (m, price) in CASES.items():
    o = optimum(m, price)
    c, T, P, Ts = FROZEN[case]
    assert abs(o["cost"] - c) < (5e-4 if case == "Os" else 1e-9), (case, o["cost"], c)
    if T is not None:
        assert (o["T_C"], o["P_bar"], o["Tsep_C"]) == (T, P, Ts), (case, o)
    print("%-15s %.6f USD/t  %3.0f C  %4.0f bar  Tsep %3.0f C  V %.4f m3"
          % (case, o["cost"], o["T_C"], o["P_bar"], o["Tsep_C"], o["V_m3"]))

# ---- pressure envelopes -------------------------------------------------------
rows = []
for case, (m, price) in CASES.items():
    for P in h.P_GRID_BAR:
        o = optimum(m, price, mask=(h.state_P == P))
        if o is not None:
            rows.append(dict(case=case, **o))
for case in CASES:
    best = min((r for r in rows if r["case"] == case), key=lambda r: r["cost"])
    assert abs(best["cost"] - FROZEN[case][0]) < (5e-4 if case == "Os" else 1e-9)
with open(HERE / "fig2_pressure_envelopes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3", *POOLS],
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

# ---- Ru metal-price sweep ------------------------------------------------------
fe_cost = FROZEN["Fe"][0]
prices = sorted(set(np.round(np.logspace(0, math.log10(3e5), 241), 6).tolist() + [PRICE["Fe"], PRICE["Ru"]]))
sweep = [dict(price_USD_kg=p, **optimum("Ru", p)) for p in prices]
costs = np.array([r["cost"] for r in sweep])
assert np.all(np.diff(costs) >= -1e-12), "Ru optimum is not monotone in its price"
lo, hi = math.log10(PRICE["Fe"]), math.log10(PRICE["Ru"])
for _ in range(80):  # bisection on log price for Ru = Fe
    mid = 0.5 * (lo + hi)
    lo, hi = (mid, hi) if optimum("Ru", 10.0 ** mid)["cost"] < fe_cost else (lo, mid)
p_star = 10.0 ** hi
o_star = optimum("Ru", p_star)
print("Ru = Fe at %.2f USD/kg: %.6f USD/t, %3.0f C %4.0f bar Tsep %3.0f C, V %.3f m3"
      % (p_star, o_star["cost"], o_star["T_C"], o_star["P_bar"], o_star["Tsep_C"], o_star["V_m3"]))
with open(HERE / "fig2_ru_price_sweep.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["price_USD_kg", "cost", "T_C", "P_bar", "Tsep_C", "V_m3", *POOLS],
                       lineterminator="\n")
    w.writeheader()
    w.writerows(sweep)
    w.writerow(dict(price_USD_kg=p_star, **o_star))  # last row: parity price
print("wrote fig2_pressure_envelopes.csv (%d rows), fig2_ru_price_sweep.csv (%d rows)" % (len(rows), len(sweep) + 1))
