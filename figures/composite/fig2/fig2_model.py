"""Figure 2 model tables, computed with the frozen NH3 harness of the selected model version.

    NH3_MODEL=1.1 (default)  NH3-FINAL-1.1, canonical run nh3_final_20260905T134204Z -> this directory
    NH3_MODEL=1.2            NH3-FINAL-1.2, canonical run nh3_final_1_2_20261013    -> nh3_1_2/
(analysis/nh3_model.py; harness roots $NH3_HARNESS and $NH3_HARNESS_1_2, or the optional argument below).

Read-only with respect to the harness: the canonical run manifest is loaded as-is,
the response surface must come from the existing cache, and nothing is written
outside this directory. Every table is checked against the canonical results of the
selected run before it is written.

  fig2_pressure_envelopes.csv  lowest feasible cost at each synthesis pressure, T and
                               Tsep reoptimized, for Fe, Ru, Os and Ru priced as Fe
  fig2_ru_price_sweep.csv      Ru reoptimized over all process states as its metal price
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if len(sys.argv) > 1:  # harness root of the selected version
    os.environ["NH3_HARNESS_1_2" if os.environ.get("NH3_MODEL", "1.1") == "1.2" else "NH3_HARNESS"] = sys.argv[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

hc = NM.core()
EN0_CANON, PRICE = hc.EN0_CANON, hc.PRICE
A = NM.anchors()
OUT = NM.out_dir(HERE)
h = NM.harness()
assert h.NSTATE == A["NSTATE"], "process-state library changed"
if not h.response_cache_path().exists():
    raise SystemExit("response surface is not cached (%s); refusing to rebuild a frozen asset" % h.response_cache_path())
resp, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")
print("%s, run %s, %d process states -> %s" % (A["label"], A["run"], h.NSTATE, OUT))

FROZEN = {m: (A[m], *A[m + "_optimum"]) for m in ("Fe", "Ru", "Os")}  # total USD/t, T, P, Tsep of the canonical run
if NM.VERSION == "1.1":  # equal-price reoptimized Ru of the frozen supervisor decomposition (1.1 only)
    FROZEN["Ru_at_Fe_price"] = (14.712129952363274, 425.0, 170.0, 30.0)
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


# ---- canonical optima reproduce -----------------------------------------------
OPT = {}
for case, (m, price) in CASES.items():
    o = OPT[case] = optimum(m, price)
    if case in FROZEN:
        c, T, P, Ts = FROZEN[case]
        assert abs(o["cost"] - c) < 1e-9, (case, o["cost"], c)
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
    assert abs(best["cost"] - OPT[case]["cost"]) < 1e-12
    if case in FROZEN:
        assert abs(best["cost"] - FROZEN[case][0]) < 1e-9
with open(OUT / "fig2_pressure_envelopes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["case", "P_bar", "cost", "T_C", "Tsep_C", "V_m3", *POOLS],
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

# ---- Ru metal-price sweep ------------------------------------------------------
fe_cost = FROZEN["Fe"][0]
# the parity bisection below needs Ru below Fe at the Fe price and above it at the frozen Ru price
assert optimum("Ru", PRICE["Fe"])["cost"] < fe_cost < optimum("Ru", PRICE["Ru"])["cost"]
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
with open(OUT / "fig2_ru_price_sweep.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["price_USD_kg", "cost", "T_C", "P_bar", "Tsep_C", "V_m3", *POOLS],
                       lineterminator="\n")
    w.writeheader()
    w.writerows(sweep)
    w.writerow(dict(price_USD_kg=p_star, **o_star))  # last row: parity price
print("wrote fig2_pressure_envelopes.csv (%d rows), fig2_ru_price_sweep.csv (%d rows)" % (len(rows), len(sweep) + 1))
