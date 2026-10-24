"""Staged three-bed converter with the Ru/C temperature cap raised from 460 C to 500 C or 530 C.

The manuscript's staged converter (analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_inrange.py: KAAP-type loop,
9 MPa, -20 C separator, 8 % inerts; fused iron = Keestra 2025 Model 3 KM1R-1964, Ru/C = Rossetti 2006) caps Ru/C at
460 C, the top of its measured range, and fused iron at 530 C. SI Note 7 then attributes the hottest-bed position of
fused iron to that cap. This run lifts the cap to 500 C (methanation limit of the carbon support) or 530 C (the fused
iron cap, so both catalysts get the same window) and asks whether fused iron still goes first. Above 460 C the Rossetti
law is extrapolated in temperature.

Same code path as staged_inrange.py (converter.optimize, DE settings, c_Ru x c_Fe continuation library, window
extraction); the only change is PAR["process"]["T_max_Ru_C"], set at import so spawned workers inherit it. Unlike the
manuscript library, the Ru/C-first arrangements RFF and RRF are also continued over the (c_Ru, c_Fe) grid, so the
financing-rate window compares all six three-bed arrangements, not only FFF/FFR/FRR/RRR.

    set NH3_MODEL=1.2
    set RU_TMAX_C=500
    python staged_ru_tmax.py --workers 3      -> tmax500_*.csv, tmax500_summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
TMAX = float(os.environ["RU_TMAX_C"])
HERE = Path(__file__).resolve().parent
INRANGE = HERE.parent / "nh3_fe_inrange_kinetics_2026_10_19"
sys.path.insert(0, str(INRANGE))
import staged_inrange as SI  # noqa: E402  (registers the Keestra Fe law, patches catalyst_props)

C, K, RS, B = SI.C, SI.K, SI.RS, SI.B
K.PAR["process"]["T_max_Ru_C"] = TMAX        # module level: spawned workers re-import this file
assert C.PAR["process"]["T_max_Ru_C"] == TMAX

PATS6 = ("FFF", "FFR", "FRR", "RRR", "RFF", "RRF")
ARR = {"FFF": "all-Fe", "RRR": "all-Ru/C", "FFR": "Fe first", "FRR": "Fe first", "RFF": "Ru/C first", "RRF": "Ru/C first"}


def decide6(L, i, accounting="dcf"):
    ch = B.charges(SI.PRICE, SI.REC, i, accounting)
    res = {p: B.env_at(L, SI.KAAP, p, *ch) for p in PATS6}
    best = min(res, key=lambda p: res[p][0])
    fe_first = min(("FFR", "FRR"), key=lambda p: res[p][0])
    ru_first = min(("RFF", "RRF"), key=lambda p: res[p][0])
    return dict(fin_rate=i, best=best, best_class=ARR[best], best_cost=res[best][0],
                best_Ru_volume_fraction=res[best][1], costs={p: res[p][0] for p in PATS6},
                Fe_first=fe_first, Ru_first=ru_first,
                Ru_first_minus_Fe_first=res[ru_first][0] - res[fe_first][0])


def windows(L):
    dec = [decide6(L, i) for i in SI.FINE]
    runs, cur = [], None
    for d in dec:
        if cur is None or d["best_class"] != cur["class"]:
            cur = dict(**{"class": d["best_class"]}, from_rate=d["fin_rate"], to_rate=d["fin_rate"])
            runs.append(cur)
        cur["to_rate"] = d["fin_rate"]
    gap = np.array([d["Ru_first_minus_Fe_first"] for d in dec])
    return dict(regimes=runs, Ru_first_ever_best=any(d["best_class"] == "Ru/C first" for d in dec),
                Ru_first_minus_Fe_first_min=float(gap.min()), Ru_first_minus_Fe_first_max=float(gap.max()),
                at={f"{100 * i:.2f} %/y": decide6(L, i) for i in (0.0,) + SI.LEASE + (0.12,)},
                benchmark_r9555=decide6(L, 0.0, accounting="frozen"), dec=dec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    fe_key = "Fe_Keestra_KM1R_1964"
    tag = f"tmax{TMAX:.0f}"
    t0 = time.time()

    def stamp(msg):
        print(f"[{time.time() - t0:6.0f} s] {msg}", flush=True)

    stamp(f"Ru/C cap {TMAX} C, Fe cap {C.PAR['process']['T_max_Fe_C']} C")
    econs = {k: dict(v, fe_kinetics=fe_key) for k, v in RS.ECON.items() if k != "benchmark accounting, r 90%"}
    jobs = [dict(loop=SI.LOOP, econ=ep, pattern=p, mode="adiabatic", tag=dict(economics=en))
            for en, ep in econs.items() for p in RS.THREE_BED]
    stamp(f"stage 1: {len(jobs)} global optimisations")
    arr = RS.run_pool(RS.solve, jobs, a.workers)
    for r, j in zip(arr, jobs):
        r["_job"] = j
    arr = RS.polish(arr, lambda r: r["economics"], a.workers)
    RS.write_csv(HERE / f"{tag}_arrangements.csv", arr, extra=("economics",))
    stamp("stage 1 done")

    base = {(r["economics"], r["pattern"]): r["x"] for r in arr}
    jobs = []
    for p in ("FFR", "FRR", "RRR", "RFF", "RRF"):
        for cfe in RS.C_FE_GRID:
            jobs.append(dict(loop=SI.LOOP, pattern=p, c_fe=cfe, c_ru=RS.C_RU_GRID,
                             x0s=[base[(en, p)] for en in econs], tag=dict(stage="library"), fe_kinetics=fe_key))
    for cfe in RS.C_FE_GRID:
        jobs.append(dict(loop=SI.LOOP, pattern="FFF", c_fe=cfe, c_ru=[RS.C_RU_GRID[0]],
                         x0s=[base[(en, "FFF")] for en in econs], tag=dict(stage="library"), fe_kinetics=fe_key))
    stamp(f"stage 2: {len(jobs)} continuation chains")
    lib = [r for g in RS.run_pool(SI.chain, jobs, a.workers) for r in g]
    RS.write_csv(HERE / f"{tag}_design_library.csv", lib, extra=("c_Ru", "c_Fe"))
    L = B.load_library(HERE / f"{tag}_design_library.csv")
    w = windows(L)
    stamp(f"regimes: {[(r['class'], round(100 * r['from_rate'], 2), round(100 * r['to_rate'], 2)) for r in w['regimes']]}")

    checks = [dict(loop=SI.LOOP, econ=dict(accounting="dcf", fin_rate=i, recovery=SI.REC, p_Ru=SI.PRICE,
                                           fe_kinetics=fe_key),
                   pattern=p, mode="adiabatic", x0s=[base[(en, p)] for en in econs], tag=dict(fin_rate=i))
              for i in (0.0, 0.021, 0.12) for p in PATS6]
    chk = RS.run_pool(RS.solve, checks, a.workers)
    env = [dict(fin_rate=r["fin_rate"], pattern=r["pattern"], direct=r["cost"],
                envelope=B.envelope_cost(L, SI.KAAP, r["pattern"], SI.PRICE, SI.REC, r["fin_rate"]))
           for r in chk]
    for e in env:
        e["envelope_minus_direct"] = e["envelope"] - e["direct"]
    with (HERE / f"{tag}_envelope_checks.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(env[0]))
        wr.writeheader()
        wr.writerows(env)

    table = {}
    for en in econs:
        g = {r["pattern"]: r for r in arr if r["economics"] == en}
        b = min(g, key=lambda p: g[p]["cost"])
        table[en] = dict(costs={p: g[p]["cost"] for p in g}, best=b,
                         Ru_volume_fraction={p: g[p]["Ru_volume_fraction"] for p in g},
                         best_bed_inlet_T_C=list(g[b]["x"][:3]))
    dec = w.pop("dec")
    with (HERE / f"{tag}_window.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["fin_rate", "best"] + [f"cost_{p}" for p in PATS6])
        for d in dec:
            wr.writerow([f"{d['fin_rate']:.4f}", d["best"]] + [f"{d['costs'][p]:.4f}" for p in PATS6])
    summ = dict(Ru_C_T_max_C=TMAX, Fe_T_max_C=C.PAR["process"]["T_max_Fe_C"],
                fe_law="Keestra 2025 Model 3, KM1R_1964", ru_law="Rossetti 2006 (extrapolated above 460 C)",
                loop=SI.LOOP, Ru_price=SI.PRICE, recovery=SI.REC, arrangements=table,
                Ru_first_never_optimal_arrangements=all(t["best"] not in ("RFF", "RRF") for t in table.values()),
                window=w,
                envelope_check=dict(n=len(env), max_envelope_minus_direct=max(e["envelope_minus_direct"] for e in env),
                                    min_envelope_minus_direct=min(e["envelope_minus_direct"] for e in env)),
                runtime_s=round(time.time() - t0))
    (HERE / f"{tag}_summary.json").write_text(json.dumps(RS._round(summ), indent=1) + "\n", encoding="utf-8")
    stamp("done")


if __name__ == "__main__":
    main()
