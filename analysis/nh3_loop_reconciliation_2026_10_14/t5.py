"""T5: industrial plausibility check against the only numerical KAAP/conventional energy figures in the repository.

docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md: KAAP energy saving ~1.17 GJ/t versus Fe loops (Humphreys 2021); ZA-5 loop
recycle compression 21.5 kWh/t at 10 MPa and 17.5 at 30 MPa, refrigeration 22.6 and 13.4 kWh/t (Humphreys 2021 citing
Liu 2013). No numerical KAAP cost difference is given in the repository, so no cost comparison is made.
"""
from __future__ import annotations

import csv

import closed_loop as CL
import common

KAAP_SAVING_GJ_T = 1.17
ZA5 = {"recycle_kWh_t": {"10MPa": 21.5, "30MPa": 17.5}, "refrigeration_kWh_t": {"10MPa": 22.6, "30MPa": 13.4}}
SOURCE = "docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md (table rows 'KAAP catalyst', 'Recycle compression', 'Refrigeration')"


def energy(rec):
    kwh = 1000.0 / (CL.TARGET_TPD / 24.0)
    rc = rec["compressor_shaft_MW_by_service"][-1] * kwh
    fc = sum(rec["compressor_shaft_MW_by_service"][:-1]) * kwh
    rf = rec["refrigeration_MW"] * kwh
    return {"recycle_kWh_t": rc, "fresh_kWh_t": fc, "refrigeration_kWh_t": rf, "loop_electricity_kWh_t": rc + fc + rf,
            "loop_electricity_GJ_t": (rc + fc + rf) * 3.6e-3}


def run(states, up, log=print):
    rows = []
    t2 = common.load(common.OUT / "t2.json")
    for e in t2["per_pressure"]:
        for cat in ("Fe", "Ru"):
            d = e["bases"]["B94"][cat]
            if d is not None and e["P_bar"] in (100.0, 140.0):
                rows.append({"config": f"isothermal all-{'Fe' if cat == 'Fe' else 'Ru/C'} (T2)", "P_bar": e["P_bar"],
                             "state_id": d["state_id"], "decision_USD_t": d["decision_USD_t"],
                             **energy(states[d["state_id"]]["record"])})
    t4 = common.load(common.OUT / "t4.json")
    r12 = next(r for r in t4["per_rate"] if r["basis"] == "B94" and r["Ru_finance_pct"] == 12)
    if r12.get("winner_state"):
        rows.append({"config": f"KAAP-type 90 bar optimum at 12%/y B94 ({r12['winner_pattern']}, {r12['winner_effective']})",
                     "P_bar": 90.0, "state_id": r12["winner_state"], "decision_USD_t": r12["winner_USD_t"],
                     **energy(states[r12["winner_state"]]["record"])})
    # all-Fe and best Fe-first adiabatic designs at 90 bar, 12%/y, from the library
    with (common.OUT / "t4_library.csv").open(encoding="utf-8") as f:
        libr = [x for x in csv.DictReader(f) if x["econ"] == "B94|12"]
    for cls in ("all-Fe", "Fe-first"):
        c = [x for x in libr if x["class"] == cls]
        if c:
            b = min(c, key=lambda x: float(x["decision_USD_t"]))
            rows.append({"config": f"adiabatic {cls} 90 bar ({b['pattern']}), 12%/y B94", "P_bar": 90.0,
                         "state_id": b["state_id"], "decision_USD_t": float(b["decision_USD_t"]),
                         **energy(states[b["state_id"]]["record"])})
    # conventional all-Fe at 140-220 bar: T2 grid at 140 bar and the #93 grid at 160/188/220 bar (B94, 15% inerts rule)
    u93 = {d["state_id"]: d for d in common.load(common.WORK / "u93" / "cold_cache.json")["designs"]}
    conv = []
    for P in (160.0, 188.0, 220.0):
        at = {k: v for k, v in u93.items() if v["P_bar"] == P}
        rws = CL.size_candidates(at, temps=(400.0, 425.0, 450.0))
        d = CL.describe(CL.best(rws, at, CL.B94, "Fe"), at)
        if d is not None:
            r = {"config": "isothermal all-Fe (#93 grid)", "P_bar": P, "state_id": d["state_id"],
                 "decision_USD_t": d["decision_USD_t"], **energy(at[d["state_id"]]["record"])}
            rows.append(r)
            conv.append(r)
    conv += [r for r in rows if r["config"].startswith("isothermal all-Fe (T2)") and r["P_bar"] == 140.0]
    best_conv = min(conv, key=lambda r: r["decision_USD_t"]) if conv else None
    kaap = next((r for r in rows if r["config"].startswith("KAAP-type")), None)
    cmp = None
    if best_conv and kaap:
        dE = best_conv["loop_electricity_GJ_t"] - kaap["loop_electricity_GJ_t"]
        cmp = {"best_conventional_all_Fe": best_conv, "KAAP_type_90bar": kaap,
               "delta_loop_electricity_GJ_t": dE, "published_KAAP_saving_GJ_t": KAAP_SAVING_GJ_T,
               "same_sign": dE > 0, "ratio_to_published": dE / KAAP_SAVING_GJ_T}
    za5 = []
    for r in rows:
        ref = "10MPa" if r["P_bar"] <= 100.0 else "10-30MPa range"
        if ref == "10MPa":
            za5.append({"config": r["config"], "P_bar": r["P_bar"], "recycle_kWh_t": r["recycle_kWh_t"],
                        "ZA5_recycle_10MPa": 21.5, "refrigeration_kWh_t": r["refrigeration_kWh_t"], "ZA5_refrigeration_10MPa": 22.6})
        else:
            za5.append({"config": r["config"], "P_bar": r["P_bar"], "recycle_kWh_t": r["recycle_kWh_t"],
                        "recycle_inside_17.5_21.5": 17.5 <= r["recycle_kWh_t"] <= 21.5,
                        "refrigeration_kWh_t": r["refrigeration_kWh_t"],
                        "refrigeration_inside_13.4_22.6": 13.4 <= r["refrigeration_kWh_t"] <= 22.6})
    log(f"T5 rows {len(rows)}; comparison {cmp and round(cmp['delta_loop_electricity_GJ_t'], 4)} GJ/t vs 1.17")
    return {"source": SOURCE, "KAAP_saving_GJ_t": KAAP_SAVING_GJ_T, "ZA5": ZA5,
            "cost_comparison": "skipped: no numerical KAAP/conventional cost difference in docs/ or data/",
            "rows": rows, "energy_comparison": cmp, "ZA5_comparison": za5}
