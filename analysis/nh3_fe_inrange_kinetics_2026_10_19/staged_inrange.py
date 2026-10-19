"""Staged three-bed converter of the KAAP-type loop (9 MPa, -20 C separator, 8 % inerts) with both rate laws inside their
fitted pressure ranges: fused iron by Keestra et al. (2025) Model 3 with the Topsoe KM1R (1964) activity factor
(keestra_fe.py; fitted on 1-324 bar) and Ru/C by Rossetti et al. (2006) (50-100 bar). The manuscript's window used
Dyson-Simon for Fe, fitted at 151-313 bar, so 90 bar extrapolated it.

Same code path as analysis/nh3_staged_converter_2026_10_12/run_staged.py (converter.optimize, its DE settings, the
c_Ru x c_Fe continuation library and boundary.decide), restricted to the KAAP-type loop; only the Fe rate law and its bed
density (2,500 kg m^-3) change. Gate: the committed Dyson-Simon library (nh3_1_2/design_library.csv) run through the same
window extraction reproduces the manuscript window (all-Ru/C below 0.82 %/y, Fe-first to 6.65 %/y).

    set NH3_MODEL=1.2
    python staged_inrange.py [--workers 2] [--fe KM1R_1964]   -> staged_<fe>_*.csv, staged_<fe>_summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
STAGED = HERE.parent / "nh3_staged_converter_2026_10_12"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(STAGED))
import converter as C  # noqa: E402
import kinetics as K  # noqa: E402
import keestra_fe as KF  # noqa: E402
import run_staged as RS  # noqa: E402
import boundary as B  # noqa: E402

# --- register the Keestra Fe law (module level, so spawned workers get it on import) -------------------------------
for _cat in KF.BCAT:
    K.RATE[f"Fe_Keestra_{_cat}"] = (lambda c: (lambda T, P, a, b, y: KF.rate(T, P, a, b, y, catalyst=c)))(_cat)
_orig_props = C.catalyst_props


def _props(cat, econ):
    if cat != "Ru" and econ.fe_kinetics.startswith("Fe_Keestra_"):
        rate, act = K.RATE[econ.fe_kinetics], econ.fe_activity
        return (lambda T, P, a, b, y: act * rate(T, P, a, b, y)), KF.BED_DENSITY
    return _orig_props(cat, econ)


C.catalyst_props = _props

LOOP = RS.kaap()                                  # 90 bar, -20 C, 8 % inerts
KAAP = (90.0, -20.0)
PRICE, REC = 53852.5, 0.9555
LEASE = (0.0135, 0.0210, 0.0510)                  # disclosed lease rates used in the SI
FINE = np.linspace(0.0, 0.12, 241)


def window(L):
    dec = [B.decide(L, KAAP, PRICE, REC, i) for i in FINE]
    best = [d["best"] for d in dec]
    allru_below = B._crossing(FINE, np.array([d["all_Ru"] - min(d["staged"], d["all_Fe"]) for d in dec]))
    gaps = np.array([d["staged_minus_Fe"] for d in dec])
    staged_below = B._crossing(FINE, gaps)
    out = dict(all_RuC_optimal_below=allru_below, staged_beats_all_Fe_below=staged_below,
               best_at={f"{100 * i:.2f} %/y": B.decide(L, KAAP, PRICE, REC, i) for i in (0.0,) + LEASE + (0.12,)},
               benchmark_r9555=B.decide(L, KAAP, PRICE, REC, 0.0, accounting="frozen"))
    out["saving_vs_all_Fe_at_lease_rates"] = {f"{100 * i:.2f} %/y": -B.decide(L, KAAP, PRICE, REC, i)["staged_minus_Fe"]
                                              for i in LEASE}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--fe", default="KM1R_1964", choices=list(KF.BCAT))
    a = ap.parse_args()
    fe_key = f"Fe_Keestra_{a.fe}"
    tag = a.fe
    t0 = time.time()

    def stamp(msg):
        print(f"[{time.time() - t0:6.0f} s] {msg}", flush=True)

    # gate: committed Dyson-Simon library -> manuscript window
    Lds = B.load_library(STAGED / "nh3_1_2" / "design_library.csv")
    w_ds = window(Lds)
    stamp(f"Dyson-Simon library: all-Ru/C below {w_ds['all_RuC_optimal_below']}, staged beats Fe below "
          f"{w_ds['staged_beats_all_Fe_below']}")

    # 1. arrangements at three economics (global DE + polish), Fe = Keestra
    econs = {k: dict(v, fe_kinetics=fe_key) for k, v in RS.ECON.items() if k != "benchmark accounting, r 90%"}
    jobs = [dict(loop=LOOP, econ=ep, pattern=p, mode="adiabatic", tag=dict(economics=en))
            for en, ep in econs.items() for p in RS.THREE_BED]
    stamp(f"stage 1: {len(jobs)} global optimisations")
    arr = RS.run_pool(RS.solve, jobs, a.workers)
    for r, j in zip(arr, jobs):
        r["_job"] = j
    arr = RS.polish(arr, lambda r: r["economics"], a.workers)
    RS.write_csv(HERE / f"staged_{tag}_arrangements.csv", arr, extra=("economics",))
    stamp("stage 1 done")

    # 2. design library for the window (continuation in c_Ru at the three c_Fe of run_staged.py)
    base = {(r["economics"], r["pattern"]): r["x"] for r in arr}
    jobs = []
    for p in ("FFR", "FRR", "RRR"):
        for cfe in RS.C_FE_GRID:
            jobs.append(dict(loop=LOOP, pattern=p, c_fe=cfe, c_ru=RS.C_RU_GRID,
                             x0s=[base[(en, p)] for en in econs], tag=dict(stage="library"), fe_kinetics=fe_key))
    for cfe in RS.C_FE_GRID:
        jobs.append(dict(loop=LOOP, pattern="FFF", c_fe=cfe, c_ru=[RS.C_RU_GRID[0]],
                         x0s=[base[(en, "FFF")] for en in econs], tag=dict(stage="library"), fe_kinetics=fe_key))
    stamp(f"stage 2: {len(jobs)} continuation chains")
    lib = [r for g in RS.run_pool(chain, jobs, a.workers) for r in g]
    RS.write_csv(HERE / f"staged_{tag}_design_library.csv", lib, extra=("c_Ru", "c_Fe"))
    L = B.load_library(HERE / f"staged_{tag}_design_library.csv")
    w = window(L)
    stamp(f"Keestra {tag}: all-Ru/C below {w['all_RuC_optimal_below']}, staged beats Fe below {w['staged_beats_all_Fe_below']}")

    # 3. direct optimisations at the lease rates, to check the library envelope
    checks = [dict(loop=LOOP, econ=dict(accounting="dcf", fin_rate=i, recovery=REC, p_Ru=PRICE, fe_kinetics=fe_key),
                   pattern=p, mode="adiabatic", x0s=[base[(en, p)] for en in econs], tag=dict(fin_rate=i))
              for i in (0.0,) + LEASE + (0.12,) for p in ("FFF", "FFR", "FRR", "RRR")]
    chk = RS.run_pool(RS.solve, checks, a.workers)
    env = [dict(fin_rate=r["fin_rate"], pattern=r["pattern"], direct=r["cost"],
                envelope=B.envelope_cost(L, KAAP, r["pattern"], PRICE, REC, r["fin_rate"]))
           for r in chk]
    for e in env:
        e["envelope_minus_direct"] = e["envelope"] - e["direct"]
    with (HERE / f"staged_{tag}_envelope_checks.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(env[0]))
        wr.writeheader()
        wr.writerows(env)
    table = {}
    for en in econs:
        g = {r["pattern"]: r for r in arr if r["economics"] == en}
        table[en] = dict(costs={p: g[p]["cost"] for p in g}, best=min(g, key=lambda p: g[p]["cost"]),
                         Ru_volume_fraction={p: g[p]["Ru_volume_fraction"] for p in g})
    ru_first_never = all(t["best"] not in ("RFF", "RRF") for t in table.values())
    summ = dict(fe_law=f"Keestra 2025 Model 3, {a.fe} (b_cat {KF.BCAT[a.fe]})", loop=LOOP, Ru_price=PRICE, recovery=REC,
                arrangements=table, Ru_first_never_optimal=ru_first_never, window_keestra=w, window_dyson_simon_committed_library=w_ds,
                envelope_check=dict(n=len(env), max_envelope_minus_direct=max(e["envelope_minus_direct"] for e in env),
                                    min_envelope_minus_direct=min(e["envelope_minus_direct"] for e in env)),
                runtime_s=round(time.time() - t0))
    (HERE / f"staged_{tag}_summary.json").write_text(json.dumps(RS._round(summ), indent=1) + "\n", encoding="utf-8")
    stamp("done")


def chain(job):
    """run_staged.chain with the Fe law carried into each Econ."""
    loop = C.Loop(**job["loop"])
    pat = RS.PATTERNS[job["pattern"]]
    prev, out = None, []
    for c_ru in job["c_ru"]:
        t = time.time()
        econ = C.Econ(c_Ru=c_ru, c_Fe=job["c_fe"], fe_kinetics=job["fe_kinetics"])
        starts = ([prev] if prev is not None else []) + job["x0s"]
        r = C.optimize(pat, loop, econ, "adiabatic", de=False, x0=starts[0], restarts=starts[1:], nm_maxfev=1500)
        prev = r["x"]
        out.append(RS.record(r, dict(job, tag=dict(job["tag"], c_Ru=c_ru, c_Fe=job["c_fe"])), loop, time.time() - t))
    return out


if __name__ == "__main__":
    main()
