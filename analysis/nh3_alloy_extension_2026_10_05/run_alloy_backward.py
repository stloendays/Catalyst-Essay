"""Counterfactual and backward design for the leading bimetallic surfaces (the expensive step, spent only on the
candidates the forward screen puts at the top).

Candidates: transition-metal-layer surfaces that undercut Fe under either descriptor route, plus the highest-activity
surface of each route. For each candidate and route, on the frozen 14,136-state process library with full
reoptimization, as for Ru in the hand-built case (harness backward_and_reachability):
  forward       cost at its own descriptor, molar mass and price (reproduces alloy_chain_results.csv);
  counterfactual  cost with the metal price set to the Fe price (does the ordering follow activity once price is
                equalized?);
  backward      activity multiplier alpha* at which the cost equals Fe (alpha* < 1: activity margin of a surface
                already below Fe), and the metal price p* at which it equals Fe;
  reachability  lowest cost at any descriptor on the strict scaling range (E_N -2.2 to 0.2 eV) with the candidate's
                molar mass and price, and the descriptor that gives it.

    CatalystForge/.venv/python run_alloy_backward.py [harness_root]
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

sys.path.insert(0, str(HERE.parents[1] / "agent"))
from selfcheck_gate import require  # noqa: E402

require()          # ACSA scores new candidates only after reproducing all three hand-built cases

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), HARNESS)
response, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")
FE = float(json.loads((RUN / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
FE_PRICE = float(hc.PRICE["Fe"])
ROUTES = {"global": ("E_N_step_eV", "cost_USD_t"), "anchored": ("E_N_step_anchored_eV", "cost_anchored_USD_t")}
SCALING = (h.EGRID >= -2.2) & (h.EGRID <= 0.2)


def cost(en, mw, price, alpha=1.0):
    name = "candidate::backward"
    hc.MW[name], hc.PRICE[name] = mw, price
    try:
        return h.eval_scenario(name, h.interp_state_vector(response, en), alpha=alpha)
    except RuntimeError:
        return None
    finally:
        hc.MW.pop(name, None)
        hc.PRICE.pop(name, None)


def total(en, mw, price, alpha=1.0):
    r = cost(en, mw, price, alpha)
    return 1e100 if r is None else r["total_cost"]


def best_scaling(mw, price):
    hc.MW["_scan"] = mw
    try:
        best, best_en = math.inf, None
        for j in np.where(SCALING)[0]:
            t, V, _, _ = h.cost_arrays("_scan", response[:, j], price=price)
            ok = V <= h.V_CAP
            if np.any(ok):
                v = float(np.min(np.where(ok, t, np.inf)))
                if v < best:
                    best, best_en = v, float(h.EGRID[j])
        return best, best_en
    finally:
        hc.MW.pop("_scan", None)


rows = [r for r in csv.DictReader((HERE / "alloy_chain_results.csv").open(encoding="utf-8"))
        if r["domain"] == "transition_metal"]
pick = {}
for route, (ecol, ccol) in ROUTES.items():
    costed = [r for r in rows if r[ccol] not in ("", None)]
    for r in costed:
        if float(r[ccol]) < FE:
            pick.setdefault(r["surface"], set()).add(f"below Fe ({route})")
    act = "logTOF_673K" if route == "global" else "logTOF_673K_anchored"
    top = max(costed, key=lambda r: float(r[act]))
    pick.setdefault(top["surface"], set()).add(f"highest activity ({route})")

out = []
for r in rows:
    if r["surface"] not in pick:
        continue
    mw, price = float(r["MW_g_mol"]), float(r["price_USD_kg"])
    for route, (ecol, ccol) in ROUTES.items():
        if r[ccol] in ("", None):
            continue
        en = float(r[ecol])
        fwd = cost(en, mw, price)
        alpha_star = 10.0 ** brentq(lambda la: total(en, mw, price, 10.0 ** la) - FE, -6.0, 12.0, xtol=1e-11)
        g = lambda p: total(en, mw, p) - FE                      # noqa: E731 - cost rises with price
        p_star = brentq(g, 1e-6, 1e9, xtol=1e-9) if g(1e-6) < 0 else None
        eq = cost(en, mw, FE_PRICE)
        bs, bs_en = best_scaling(mw, price)
        out.append({
            "surface": r["surface"], "route": route, "why": "; ".join(sorted(pick[r["surface"]])),
            "E_N_step_eV": en, "MW_g_mol": mw, "price_USD_kg": price,
            "cost_USD_t": round(fwd["total_cost"], 4), "cost_csv_USD_t": float(r[ccol]),
            "T_C": fwd["T_C"], "P_bar": fwd["P_bar"], "V_m3": round(fwd["V_m3"], 4),
            "cost_at_Fe_price_USD_t": None if eq is None else round(eq["total_cost"], 4),
            "alpha_star": alpha_star, "price_parity_USD_kg": p_star,
            "best_scaling_cost_USD_t": round(bs, 4), "best_scaling_E_N_eV": bs_en,
            "beats_Fe": fwd["total_cost"] < FE,
        })

for o in out:
    assert abs(o["cost_USD_t"] - o["cost_csv_USD_t"]) < 2e-3 * o["cost_csv_USD_t"], o   # CSV descriptors are rounded
fields = list(out[0])
with (HERE / "alloy_backward.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
summary = {"Fe_cost_USD_t": FE, "Fe_price_USD_kg": FE_PRICE, "candidates": sorted(pick),
           "rows": [{k: o[k] for k in ("surface", "route", "cost_USD_t", "cost_at_Fe_price_USD_t", "alpha_star",
                                        "price_parity_USD_kg", "best_scaling_cost_USD_t")} for o in out]}
(HERE / "alloy_backward_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
for o in out:
    print(f"{o['surface']:10s} {o['route']:8s} cost {o['cost_USD_t']:8.3f}  @Fe-price {o['cost_at_Fe_price_USD_t']}  "
          f"alpha* {o['alpha_star']:.4g}  p* {o['price_parity_USD_kg'] if o['price_parity_USD_kg'] is None else round(o['price_parity_USD_kg'], 2)}  "
          f"best-scaling {o['best_scaling_cost_USD_t']} @ {o['best_scaling_E_N_eV']}  ({o['why']})")
