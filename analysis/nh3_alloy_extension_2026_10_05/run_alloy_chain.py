"""Bimetallic-alloy extension of the NH3 screen: every Mamun et al. (2019) surface through the full chain.

Chain per candidate (no step is specific to alloys):
  1. E_N: most stable N* site of the surface, 0.5 N2(g) + * -> N* (Catalysis-Hub, MamunHighT2019).
  2. Dataset bridge: the Mamun pure-metal terrace values are mapped onto the Dataset S1 terrace scale by a
     linear fit over the metals present in both (fit stored in calibration.json).
  3. Step descriptor: step E_N = 1.15474 x terrace E_N - 0.17006, the regression the frozen workbook already
     uses to place Fe on the step-site volcano (sheet Terrace_Step_N, 14 metals, R^2 = 0.982).
  3b. Element-anchored bridge (second route): each element's offset between the frozen-screen step E_N and
     its pure-metal chain value is added in proportion to its atomic fraction, so every pure metal sits
     exactly at its frozen descriptor. Candidates are reported as robust when both routes place them below Fe.
  4. Activity: per-state log10 TOF read from the cached frozen response surface (14,136 process states).
  5. Cost: frozen cost model with the alloy's mole-weighted molar mass and mass-weighted metal price,
     minimized over all states with V <= V_CAP. The 15 model metals keep their frozen prices; the other
     elements take USGS Mineral Commodity Summaries 2026 prices per kg of contained metal
     (element_prices_usgs_mcs2026.csv). Metrics are reported for the frozen-price set and for the full set.

Self-check: the same code path reproduces the canonical deterministic cost of every pure metal.
Pruning: a descriptor-only lower bound (best state activity, smallest reactor, cheapest process state)
decides which candidates need the full 14,136-state optimization; every candidate is also optimized in
full to show that no candidate that beats Fe is pruned.

    CatalystForge/.venv/python run_alloy_chain.py [harness_root]
"""
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
h = hc.NH3Harness(cfg, HARNESS)
assert h.NSTATE == 14136, "process-state library changed"
response, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")
canon = json.loads((RUN / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]

S1_TERRACE = {'Ag': 2.9765, 'Au': 2.3914, 'Co': -0.0986, 'Cu': 1.0619, 'Ir': -0.0913, 'Mo': -1.5343,
              'Ni': 0.0996, 'Os': -0.7404, 'Pd': 0.8054, 'Pt': 0.334, 'Re': -1.4205, 'Rh': -0.0431,
              'Ru': -0.7938, 'W': -1.765, 'Fe': -1.0583}      # workbook sheet Terrace_Step_N
STEP_SLOPE, STEP_INTERCEPT = 1.15474363873408, -0.170055430875424
ATOMIC_MASS = dict(hc.MW)
FE_COST = float(canon["Fe"]["feasible"]["total_cost"])


def elements(formula):
    return {el: int(n) if n else 1 for el, n in re.findall(r"([A-Z][a-z]?)(\d*)", formula)}


FROZEN_PRICE = dict(hc.PRICE)
USGS = {r["element"]: r for r in csv.DictReader((HERE / "element_prices_usgs_mcs2026.csv").open(encoding="utf-8"))}
assert not set(USGS) & set(FROZEN_PRICE)
USGS_PRICE = {el: float(r["price_USD_per_kg_metal"]) for el, r in USGS.items()}
ALL_PRICE = {**FROZEN_PRICE, **USGS_PRICE}
ATOMIC_MASS.update({el: float(r["atomic_mass"]) for el, r in USGS.items()})
# Applicability: the activity model is fitted on transition metals (Dataset S1 scaling and BEP relations).
SP_METALS = {"Al", "Zn", "Cd", "Hg", "Ga", "In", "Tl", "Sn", "Pb", "Bi"}   # main-group / post-transition
GROUP_3_TO_5 = {"Sc", "Y", "La", "Ti", "Zr", "Hf", "V", "Nb", "Ta"}        # very stable bulk nitrides


def domain(els):
    if set(els) & SP_METALS:
        return "contains_sp_metal"
    if set(els) & GROUP_3_TO_5:
        return "contains_group3to5"
    return "transition_metal"


def optimum(name, logvec, mw, price):
    name = "candidate::" + name                      # never shadow a frozen metal entry
    hc.MW[name] = mw
    hc.PRICE[name] = price
    try:
        return h.eval_scenario(name, logvec)
    except RuntimeError:
        return None
    finally:
        hc.MW.pop(name, None)
        hc.PRICE.pop(name, None)


# ----- self-check: canonical pure-metal costs through this code path ------------------------------
selfcheck = []
for m, rec in canon.items():
    feas = rec.get("feasible")
    lv = h.interp_state_vector(response, hc.EN0_CANON[m])
    got = optimum(m + "_check", lv, hc.MW[m], hc.PRICE[m])
    want = None if feas is None else float(feas["total_cost"])
    ok = (got is None and want is None) or (got is not None and want is not None and abs(got["total_cost"] - want) < 1e-9)
    selfcheck.append({"metal": m, "canonical": want, "chain": None if got is None else got["total_cost"], "match": ok})
assert all(r["match"] for r in selfcheck), selfcheck
assert hc.PRICE == FROZEN_PRICE

# ----- descriptor bridge -------------------------------------------------------------------------
sites = list(csv.DictReader((HERE / "mamun2019_N_binding_sites.csv").open(encoding="utf-8")))
best = {}
for r in sites:
    k = r["surface_composition"]
    if k not in best or float(r["E_N_eV"]) < float(best[k]["E_N_eV"]):
        best[k] = r
pure = {k: float(v["E_N_eV"]) for k, v in best.items() if len(elements(k)) == 1}
shared = sorted(set(pure) & set(S1_TERRACE))
x = np.array([pure[m] for m in shared])
y = np.array([S1_TERRACE[m] for m in shared])
a, b = np.polyfit(x, y, 1)
resid = y - (a * x + b)
calib = {"bridge_metals": shared, "slope": float(a), "intercept": float(b),
         "r2": float(np.corrcoef(x, y)[0, 1] ** 2), "rms_eV": float(np.sqrt(np.mean(resid ** 2))),
         "max_abs_residual_eV": float(np.max(np.abs(resid))),
         "step_slope": STEP_SLOPE, "step_intercept": STEP_INTERCEPT}
step_metals = [m for m in S1_TERRACE if m != "Fe"]     # Fe step E_N is itself the regression prediction
step_res = [hc.EN0_CANON[m] - (STEP_SLOPE * S1_TERRACE[m] + STEP_INTERCEPT) for m in step_metals]
calib["step_rms_eV"] = float(np.sqrt(np.mean(np.square(step_res))))
calib["propagated_rms_eV"] = float(math.hypot(STEP_SLOPE * calib["rms_eV"], calib["step_rms_eV"]))


def step_EN(e_mamun, shift=0.0):
    return STEP_SLOPE * (a * e_mamun + b) + STEP_INTERCEPT + shift


OFFSET = {m: hc.EN0_CANON[m] - step_EN(pure[m]) for m in hc.EN0_CANON if m in pure}
calib["element_offsets_eV"] = {m: round(v, 4) for m, v in OFFSET.items()}


def anchored_EN(e_mamun, els):
    n = sum(els.values())
    return step_EN(e_mamun) + sum(OFFSET.get(el, 0.0) * k / n for el, k in els.items())


UNANCHORED = sorted(el for el in FROZEN_PRICE if el not in OFFSET)   # frozen metals with no Mamun pure surface
calib["unanchored_elements"] = UNANCHORED


# ----- lower bound for pruning -------------------------------------------------------------------
envelope = response.max(axis=0)                     # best state log TOF at each descriptor grid point
C0 = float(np.min(h.state_process_cost)) + (h.REACTOR_FIXED * h.crf / h.annual_output_t)


def lower_bound(en, mw, price):
    xg = min(max(en, float(h.EGRID[0])), float(h.EGRID[-1]))
    lmax = float(np.interp(xg, h.EGRID, envelope))
    hc.MW["_lb"] = mw
    try:
        _, _, metal, _ = h.cost_arrays("_lb", np.array([lmax]), price=price)
    finally:
        hc.MW.pop("_lb", None)
    return float(metal[0]) + C0


# ----- batch chain -------------------------------------------------------------------------------
rows, no_price = [], defaultdict(int)
for surf, r in sorted(best.items()):
    els = elements(r["bulk_composition"])
    missing = [el for el in els if el not in ALL_PRICE]
    if missing:
        for el in missing:
            no_price[el] += 1
        continue
    n_tot = sum(els.values())
    mw = sum(ATOMIC_MASS[el] * n for el, n in els.items()) / n_tot
    mass = {el: ATOMIC_MASS[el] * n for el, n in els.items()}
    price = sum(ALL_PRICE[el] * mass[el] for el in els) / sum(mass.values())
    price_source = "frozen" if all(el in FROZEN_PRICE for el in els) else "frozen+USGS2026"
    e_m = float(r["E_N_eV"])
    en = step_EN(e_m)
    lv = h.interp_state_vector(response, en)
    opt = optimum(surf, lv, mw, price)
    lb = lower_bound(en, mw, price)
    row = {"surface": surf, "bulk": r["bulk_composition"], "facet": r["facet"], "site": r["site"],
           "n_elements": len(els), "E_N_mamun_eV": round(e_m, 4), "E_N_step_eV": round(en, 4),
           "logTOF_673K": round(float(h.base_condition.logtof(en)), 4), "MW_g_mol": round(mw, 4),
           "price_USD_kg": round(price, 4), "price_source": price_source, "domain": domain(els), "lower_bound_USD_t": round(lb, 4),
           "pruned": lb >= FE_COST}
    if opt is None:
        row.update(cost_USD_t="", T_C="", P_bar="", Tsep_C="", V_m3="", feasible=False)
    else:
        row.update(cost_USD_t=round(opt["total_cost"], 6), T_C=opt["T_C"], P_bar=opt["P_bar"],
                   Tsep_C=opt["Tsep_C"], V_m3=round(opt["V_m3"], 5), feasible=True)
    ena = anchored_EN(e_m, els)
    oa = optimum(surf, h.interp_state_vector(response, ena), mw, price)
    row["E_N_step_anchored_eV"] = round(ena, 4)
    row["logTOF_673K_anchored"] = round(float(h.base_condition.logtof(ena)), 4)
    row["cost_anchored_USD_t"] = "" if oa is None else round(oa["total_cost"], 6)
    row["fully_anchored"] = not any(el in UNANCHORED for el in els)
    for shift, tag in ((-calib["propagated_rms_eV"], "minus"), (calib["propagated_rms_eV"], "plus")):
        o = optimum(surf, h.interp_state_vector(response, step_EN(e_m, shift)), mw, price)
        row[f"cost_shift_{tag}"] = "" if o is None else round(o["total_cost"], 6)
    rows.append(row)
assert hc.PRICE == FROZEN_PRICE and set(hc.MW) == set(FROZEN_PRICE)
all_rows = rows

def scope_metrics(rows):
    feas = [r for r in rows if r["feasible"]]
    alloys = [r for r in feas if r["n_elements"] == 2]
    below_fe = sorted([r for r in feas if r["cost_USD_t"] < FE_COST], key=lambda r: r["cost_USD_t"])
    false_prunes = [r["surface"] for r in feas if r["pruned"] and r["cost_USD_t"] < FE_COST]
    up = sorted(feas, key=lambda r: -r["logTOF_673K"])
    econ = sorted(feas, key=lambda r: r["cost_USD_t"])
    rho = spearmanr([r["logTOF_673K"] for r in feas], [-r["cost_USD_t"] for r in feas]).statistic
    up_winner, econ_winner = up[0], econ[0]
    regret = (up_winner["cost_USD_t"] - econ_winner["cost_USD_t"]) / econ_winner["cost_USD_t"]


    below_anch = sorted([r for r in rows if r["cost_anchored_USD_t"] != "" and r["cost_anchored_USD_t"] < FE_COST],
                        key=lambda r: r["cost_anchored_USD_t"])
    robust = [r["surface"] for r in below_fe if r in below_anch]
    pure_anchor_ok = all(abs(r["E_N_step_anchored_eV"] - round(hc.EN0_CANON[r["surface"]], 4)) < 1e-3
                         for r in rows if r["n_elements"] == 1 and r["surface"] in hc.EN0_CANON)
    assert pure_anchor_ok


    def route_metrics(cost_key, tof_key):
        ok = [r for r in rows if r[cost_key] != ""]
        up_r = sorted(ok, key=lambda r: -r[tof_key])
        ec_r = sorted(ok, key=lambda r: r[cost_key])
        return {"feasible": len(ok),
                "upstream_winner": up_r[0]["surface"], "upstream_winner_cost": up_r[0][cost_key],
                "upstream_winner_economic_rank": ec_r.index(up_r[0]) + 1,
                "economic_winner": ec_r[0]["surface"], "economic_winner_cost": ec_r[0][cost_key],
                "economic_winner_upstream_rank": up_r.index(ec_r[0]) + 1,
                "spearman": float(spearmanr([r[tof_key] for r in ok], [-r[cost_key] for r in ok]).statistic),
                "regret": (up_r[0][cost_key] - ec_r[0][cost_key]) / ec_r[0][cost_key]}


    CHEAP_3D, GROUP6 = {"Fe", "Co", "Ni", "Cu"}, {"Cr", "Mo", "W"}


    def family(surf):
        els = set(elements(surf))
        return len(els) == 2 and len(els & CHEAP_3D) == 1 and len(els & GROUP6) == 1


    def count_below(tag):
        return sum(1 for r in feas if r[f"cost_shift_{tag}"] != "" and r[f"cost_shift_{tag}"] < FE_COST)


    return {
        "costed": len(rows), "feasible": len(feas), "infeasible_V_cap": len(rows) - len(feas),
        "bimetallic_feasible": len(alloys),
        "Fe_cost_USD_t": FE_COST,
        "below_Fe": len(below_fe), "below_Fe_surfaces": [r["surface"] for r in below_fe],
        "below_Fe_at_minus_rms": count_below("minus"), "below_Fe_at_plus_rms": count_below("plus"),
        "below_Fe_anchored": len(below_anch),
        "below_Fe_anchored_surfaces": [(r["surface"], r["cost_anchored_USD_t"]) for r in below_anch],
        "below_Fe_both_routes": robust,
        "route_global": route_metrics("cost_USD_t", "logTOF_673K"),
        "route_anchored": route_metrics("cost_anchored_USD_t", "logTOF_673K_anchored"),
        "below_Fe_either_route_all_3d_plus_group6": all(family(sv) for sv in
            {r["surface"] for r in below_fe} | {r["surface"] for r in below_anch}),
        "family_3d_group6_costed": sum(family(r["surface"]) for r in rows),
        "upstream_winner": {k: up_winner[k] for k in ("surface", "E_N_step_eV", "logTOF_673K", "cost_USD_t", "price_USD_kg")},
        "economic_winner": {k: econ_winner[k] for k in ("surface", "E_N_step_eV", "logTOF_673K", "cost_USD_t", "price_USD_kg", "T_C", "P_bar")},
        "upstream_winner_economic_rank": econ.index(up_winner) + 1,
        "economic_winner_upstream_rank": up.index(econ_winner) + 1,
        "spearman_upstream_vs_economic": float(rho),
        "regret_choosing_upstream_winner": float(regret),
        "pruning": {"lower_bound_constant_USD_t": C0, "pruned": sum(r["pruned"] for r in rows),
                    "full_optimizations_needed": sum(not r["pruned"] for r in rows),
                    "fraction_saved": sum(r["pruned"] for r in rows) / len(rows),
                    "false_prunes": false_prunes},
    }



frozen_rows = [r for r in all_rows if r["price_source"] == "frozen"]
summary = {"surfaces_fetched": len(best), "sites_fetched": len(sites),
           "costed_with_frozen_prices": len(frozen_rows),
           "costed_with_frozen_or_usgs_prices": len(all_rows),
           "not_costed_no_price": len(best) - len(all_rows),
           "elements_without_price": dict(sorted(no_price.items(), key=lambda kv: -kv[1]))}
summary.update(scope_metrics(frozen_rows))
summary["extended_with_usgs_prices"] = scope_metrics(all_rows)
summary["extended_transition_metals_only"] = scope_metrics([r for r in all_rows if r["domain"] != "contains_sp_metal"])
summary["extended_excluding_sp_and_group3to5"] = scope_metrics([r for r in all_rows if r["domain"] == "transition_metal"])
summary["domain_counts"] = {d: sum(r["domain"] == d for r in all_rows) for d in
                            ("transition_metal", "contains_group3to5", "contains_sp_metal")}
summary["self_check"] = selfcheck
summary["calibration"] = calib
rows = all_rows

cols = list(rows[0].keys())
with (HERE / "alloy_chain_results.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in sorted(rows, key=lambda r: (not r["feasible"], r["cost_USD_t"] if r["feasible"] else 0, r["surface"])):
        w.writerow(r)
(HERE / "calibration.json").write_text(json.dumps(calib, indent=1) + "\n", encoding="utf-8")
(HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k not in ("self_check", "below_Fe_surfaces")}, indent=1))
