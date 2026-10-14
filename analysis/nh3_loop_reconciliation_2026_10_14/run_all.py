#!/usr/bin/env python3
"""Run the preregistered tests T1-T5 (PREREGISTRATION.md) and write outputs/ and REPORT.md.

    python run_all.py --stage all --workers 4
Stages: cold (closed-loop cold states), upstream (#93/#94 reruns, unchanged code), t1, t2, t3, t4, t5, report.
Intermediate caches go to work/ (not committed); every reported number goes to outputs/.
"""
from __future__ import annotations

import argparse
import time

import common

STAGES = ("cold", "upstream", "t1", "t2", "t3", "t4", "t5", "report")


def log(msg):
    print(msg, flush=True)


def stage_cold(a):
    import closed_loop as CL
    pressures = tuple(CL.T2_PRESSURES) + tuple(CL.T3_EXTRA_PRESSURES)
    states = CL.cold_grid(pressures, workers=a.workers, cache=common.WORK / "cold_cache.json", log=log)
    common.dump(common.OUT / "cold_states.json", {"grid": CL.GRID, "pressures_bar": pressures,
                                                  "designs": sorted(states.values(), key=lambda d: d["state_id"])}, nd=12)
    log(f"cold: {len(states)} states, unresolved {sum(not d.get('record') for d in states.values())}")


def cold_states():
    return {d["state_id"]: d for d in common.load(common.OUT / "cold_states.json")["designs"]}


def stage_upstream(a):
    """#93 (run_study.run) and #94 (source_domains.main), unchanged code, outputs under work/."""
    import run_study as RS
    import source_domains as SD
    base = common.WORK / "u93"
    RS.run(base)
    RS.run(base, retry_unresolved=True)
    s93 = common.load(base / "summary.json")
    d94 = SD.main(common.WORK / "u94", base)
    keep = ("state_id", "T_C", "P_bar", "X_design", "X", "T2_C", "cold_T2_C", "purge", "bed_m3", "decision_relevant_cost_USD_t",
            "decision_USD_t", "excess_feed_USD_t", "utility_USD_t", "inventory_USD_t", "reactor_annualized_USD_t",
            "compressor_annualized_USD_t", "inlet_inerts_pct", "inlet_inerts_molpct")
    out = {"u93": {"stats": s93["stats"], "selected": {c: {k: v for k, v in s93["selected"][c].items() if k in keep}
                                                         for c in ("Fe", "Ru")},
                   "finance_crossover": s93["finance_crossover"]},
           "u94": {"science_state": d94["science_state"], "gap_Ru_minus_Fe_USD_t": d94["gap_Ru_minus_Fe_USD_t"],
                   "Ru_minus_Fe_components": d94["Ru_minus_Fe_components"],
                   "nominal_selected": {c: {k: v for k, v in d94["nominal_selected"][c].items() if k != "cost"}
                                        for c in ("Fe", "Ru")},
                   "nominal_cost": {c: {k: v for k, v in d94["nominal_selected"][c]["cost"].items() if k != "economic_settings"}
                                    for c in ("Fe", "Ru")},
                   "unresolved": len(d94["numerically_unresolved_new_cold"]), "cold_design_count": d94["cold_design_count"]}}
    out["gates"] = {
        "u93_Fe_47.245": abs(s93["selected"]["Fe"]["decision_relevant_cost_USD_t"] - 47.245) < 1e-3,
        "u93_Ru_49.484": abs(s93["selected"]["Ru"]["decision_relevant_cost_USD_t"] - 49.484) < 1e-3,
        "u94_Fe_41.634": abs(d94["nominal_selected"]["Fe"]["decision_USD_t"] - 41.634) < 1e-3,
        "u94_Ru_82.636": abs(d94["nominal_selected"]["Ru"]["decision_USD_t"] - 82.636) < 1e-3}
    common.dump(common.OUT / "upstream_93_94.json", out)
    log(f"upstream gates {out['gates']}")


def stage_t1(a):
    import canonical
    out, rows = canonical.t1()
    common.dump(common.OUT / "t1.json", out, nd=12)
    common.write_csv(common.OUT / "t1_metals.csv", rows, nd=12)
    log(f"T1 gate {out['replay_gate_3bar']}")


def stage_t2(a):
    import t2
    out, rows, opt, terms, cross = t2.run(cold_states(), log=log)
    common.dump(common.OUT / "t2.json", out)
    common.write_csv(common.OUT / "t2_optima.csv", opt)
    common.write_csv(common.OUT / "t2_terms.csv", terms)
    common.write_csv(common.OUT / "t2_crossover.csv", cross)


def stage_t3(a):
    import t3
    out, pts, wf = t3.run(cold_states(), common.load(common.OUT / "upstream_93_94.json"), log=log)
    common.dump(common.OUT / "t3.json", out)
    common.write_csv(common.OUT / "t3_points.csv", pts)
    common.write_csv(common.OUT / "t3_waterfall.csv", wf)


def stage_t4(a):
    import t4
    out, rates, lib = t4.run(cold_states(), workers=a.workers, log=log)
    common.dump(common.OUT / "t4.json", out)
    common.write_csv(common.OUT / "t4_rates.csv", rates)
    common.write_csv(common.OUT / "t4_library.csv", lib)


def stage_t5(a):
    import t5
    common.dump(common.OUT / "t5.json", t5.run(cold_states(), common.load(common.OUT / "upstream_93_94.json"), log=log))


def stage_report(a):
    import report
    common.dump(common.OUT / "provenance.json", common.provenance())
    report.write()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", default="all", choices=STAGES + ("all",))
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    common.OUT.mkdir(parents=True, exist_ok=True)
    common.WORK.mkdir(parents=True, exist_ok=True)
    for s in (STAGES if a.stage == "all" else (a.stage,)):
        t = time.time()
        log(f"== stage {s}")
        globals()["stage_" + s](a)
        log(f"== stage {s} done in {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
