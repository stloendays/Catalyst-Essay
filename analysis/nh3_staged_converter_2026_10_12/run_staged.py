"""Staged Fe / Ru/C converter with measured rate laws: arrangement costs, sensitivities and decision boundaries.

    python run_staged.py [--workers N]

Stages
  1. Every 3-bed arrangement (FFF, RRR, FFR, FRR, RFF, RRF) in three loops (KAAP-type 90 bar with a -20 C separator;
     conventional 150 and 200 bar with -5 C; 8 % inerts), four catalyst accountings and two bed modes (adiabatic
     with interbed exchange; isothermal, for two accountings):
     differential evolution + Nelder-Mead, then a polishing pass that restarts every case from the optima of the
     other arrangements of the same case.
  2. Sensitivities in the KAAP-type loop, and four-bed converters.
  3. Design library for the decision boundaries: for 8 loop pressures and the arrangements FFF, FFR, FRR, RRR, the
     optimum at a grid of Ru charges c_Ru (USD per kg Ru per year) and Fe charges c_Fe (USD per kg per year), by
     continuation in c_Ru. A design's cost is exactly linear in (c_Ru, c_Fe), so the cost at any Ru price, recovery
     and financing rate is the lower envelope of the library (an upper bound on the optimum; checked in stage 4).
  4. Direct global optimisation at check points of the maps.

Outputs (this folder): arrangements.csv, sensitivities.csv, design_library.csv, envelope_checks.csv, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

import converter as C

HERE = Path(__file__).resolve().parent

PATTERNS = {
    "FFF": ("Fe", "Fe", "Fe"), "RRR": ("Ru", "Ru", "Ru"),
    "FFR": ("Fe", "Fe", "Ru"), "FRR": ("Fe", "Ru", "Ru"),
    "RFF": ("Ru", "Fe", "Fe"), "RRF": ("Ru", "Ru", "Fe"),
    "FFFF": ("Fe",) * 4, "RRRR": ("Ru",) * 4, "FRRR": ("Fe", "Ru", "Ru", "Ru"),
    "FFRR": ("Fe", "Fe", "Ru", "Ru"), "FFFR": ("Fe", "Fe", "Fe", "Ru"),
}
THREE_BED = ["FFF", "RRR", "FFR", "FRR", "RFF", "RRF"]
ARRANGEMENTS = {"all-Fe": ["FFF"], "all-Ru/C": ["RRR"], "Fe-first, Ru/C downstream": ["FFR", "FRR"],
                "Ru/C-first, Fe downstream": ["RFF", "RRF"]}
LOOPS = {"KAAP-type 90 bar, -20 C": (90.0, -20.0), "conventional 150 bar, -5 C": (150.0, -5.0),
         "conventional 200 bar, -5 C": (200.0, -5.0)}   # -5 C: Topsoe 140/220-bar loops (Dybkjaer 1995, Table 6.1)
ECON = {
    "benchmark accounting, r 95.55%": dict(accounting="frozen", recovery=0.9555),
    "benchmark accounting, r 90%": dict(accounting="frozen", recovery=0.90),
    "25-y cash flow, financing 0%, r 95.55%": dict(accounting="dcf", fin_rate=0.0, recovery=0.9555),
    "25-y cash flow, financing 12%, r 95.55%": dict(accounting="dcf", fin_rate=0.12, recovery=0.9555),
}
B95, D12 = "benchmark accounting, r 95.55%", "25-y cash flow, financing 12%, r 95.55%"
DE_KW = dict(maxiter=80, popsize=10)
C_RU_GRID = [float(v) for v in np.geomspace(10.0, 30000.0, 12)]   # USD per kg Ru per year
C_FE_GRID = [0.8, 0.96, 1.4542]                                    # frozen; 25-y cash flow at 0 % and 12 %
PRESSURES = [60.0, 75.0, 90.0, 105.0, 120.0, 150.0, 180.0, 200.0]
LIBRARY_LOOPS = [(P, -20.0) for P in PRESSURES] + [(150.0, -5.0), (200.0, -5.0)]
KAAP = "KAAP-type 90 bar, -20 C"


def kaap(**kw):
    d = dict(P_bar=90.0, Tsep_C=-20.0, inerts=0.08)
    d.update(kw)
    return d


def solve(job):
    """job: dict(loop, pattern, mode, econ, T_max_Ru, de, x0s, tag). Returns a flat record."""
    t0 = time.time()
    loop = C.Loop(**job["loop"])
    econ = C.Econ(**job["econ"])
    pat = PATTERNS[job["pattern"]]
    nb = len(pat)
    x0s = [list(x)[:2 * nb] if len(x) >= 2 * nb else None for x in job.get("x0s", []) if x is not None]
    x0s = [x for x in x0s if x is not None]
    mode = job.get("mode", "adiabatic")
    if job.get("de", True):
        r = C.optimize(pat, loop, econ, mode, job.get("T_max_Ru"), seed=job.get("seed", 1), restarts=x0s, **DE_KW)
    else:
        r = C.optimize(pat, loop, econ, mode, job.get("T_max_Ru"), de=False, x0=x0s[0], restarts=x0s[1:])
    return record(r, job, loop, time.time() - t0)


def record(r, job, loop, dt):
    d = r["detail"] or {}
    rec = dict(job.get("tag", {}))
    rec.update(pattern=job["pattern"], mode=job.get("mode", "adiabatic"), P_bar=loop.P_bar, Tsep_C=loop.Tsep_C,
               inerts=loop.inerts, cost=r["cost"], x=r["x"], seconds=round(dt, 1))
    for k in ("catalyst_Fe", "catalyst_Ru", "reactor", "fresh_comp", "recycle_comp", "refrigeration",
              "compressor_capex", "V_m3", "V_Ru_m3", "Ru_volume_fraction", "mass_Fe_kg", "mass_Ru_cat_kg",
              "Ru_metal_kg", "X_N2_per_pass", "y_NH3_in", "y_NH3_out", "inlet_Nm3_h", "feasible_V_cap"):
        v = d.get(k)
        rec[k] = float(v) if isinstance(v, (float, np.floating)) else v
    rec["noncatalyst"] = (r["cost"] - d["catalyst_Fe"] - d["catalyst_Ru"]) if d else None
    rec["beds"] = [{k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in b.items()}
                   for b in d.get("beds", [])]
    return rec


def chain(job):
    """Continuation in c_Ru for one (pressure, pattern, c_Fe): returns one record per c_Ru."""
    loop = C.Loop(**job["loop"])
    pat = PATTERNS[job["pattern"]]
    prev = None
    out = []
    for c_ru in job["c_ru"]:
        t0 = time.time()
        econ = C.Econ(c_Ru=c_ru, c_Fe=job["c_fe"])
        starts = ([prev] if prev is not None else []) + job["x0s"]
        r = C.optimize(pat, loop, econ, "adiabatic", de=False, x0=starts[0], restarts=starts[1:], nm_maxfev=1500)
        prev = r["x"]
        sub = dict(job, tag=dict(job["tag"], c_Ru=c_ru, c_Fe=job["c_fe"]))
        out.append(record(r, sub, loop, time.time() - t0))
    return out


def run_pool(fn, jobs, workers):
    if workers <= 1:
        return [fn(j) for j in jobs]
    with mp.get_context("spawn").Pool(workers) as pool:
        return pool.map(fn, jobs, chunksize=1)


def group(recs, key):
    out = {}
    for r in recs:
        out.setdefault(key(r), []).append(r)
    return out


def polish(recs, keyf, workers):
    """Restart every case from the optima of the other arrangements of the same case; keep the better one."""
    by = group(recs, keyf)
    jobs = []
    for k, g in by.items():
        for r in g:
            nb = len(PATTERNS[r["pattern"]])
            others = [o["x"] for o in sorted(g, key=lambda o: o["cost"])
                      if o is not r and len(PATTERNS[o["pattern"]]) == nb][:3]
            jobs.append(dict(r["_job"], de=False, x0s=[r["x"]] + others))
    new = run_pool(solve, jobs, workers)
    out = []
    for old, nw in zip([r for g in by.values() for r in g], new):
        best = nw if nw["cost"] < old["cost"] - 1e-9 else old
        best["_job"] = old["_job"]
        out.append(best)
    return out


def write_csv(path, recs, extra=()):
    cols = list(extra) + ["pattern", "mode", "P_bar", "Tsep_C", "inerts", "cost", "noncatalyst", "catalyst_Fe",
                          "catalyst_Ru", "reactor", "fresh_comp", "recycle_comp", "refrigeration", "compressor_capex",
                          "V_m3", "V_Ru_m3", "Ru_volume_fraction", "mass_Fe_kg", "mass_Ru_cat_kg", "Ru_metal_kg",
                          "X_N2_per_pass", "y_NH3_in", "y_NH3_out", "inlet_Nm3_h", "feasible_V_cap",
                          "beds_T_in_out_C", "beds_volume_m3", "beds_y_NH3_out", "x"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in recs:
            row = []
            for c in cols:
                if c == "beds_T_in_out_C":
                    row.append(";".join(f"{b['catalyst']}:{b['T_in_C']:.1f}-{b['T_out_C']:.1f}" for b in r["beds"]))
                elif c == "beds_volume_m3":
                    row.append(";".join(f"{b['volume_m3']:.3f}" for b in r["beds"]))
                elif c == "beds_y_NH3_out":
                    row.append(";".join(f"{b['y_NH3_out']:.4f}" for b in r["beds"]))
                elif c == "x":
                    row.append(";".join(f"{v:.5f}" for v in r["x"]))
                else:
                    v = r.get(c)
                    row.append(f"{v:.6f}" if isinstance(v, float) else v)
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, min(8, mp.cpu_count())))
    a = ap.parse_args()
    t_start = time.time()
    summary = {}

    def stamp(msg):
        print(f"[{time.time() - t_start:6.0f} s] {msg}", flush=True)

    # ---- 1. arrangements ----------------------------------------------------------------------------------------
    jobs = []
    for lname, (P, Ts) in LOOPS.items():
        for ename, ep in ECON.items():
            for mode in (("adiabatic", "isothermal") if ename in (B95, D12) else ("adiabatic",)):
                for pname in THREE_BED:
                    jobs.append(dict(loop=kaap(P_bar=P, Tsep_C=Ts), econ=ep, pattern=pname, mode=mode,
                                     tag=dict(loop=lname, economics=ename)))
    stamp(f"stage 1: {len(jobs)} global optimisations")
    arr = run_pool(solve, jobs, a.workers)
    for r, j in zip(arr, jobs):
        r["_job"] = j
    stamp("stage 1: polishing")
    arr = polish(arr, lambda r: (r["loop"], r["economics"], r["mode"]), a.workers)
    write_csv(HERE / "arrangements.csv", arr, extra=("loop", "economics"))
    base_x = {(r["loop"], r["economics"], r["mode"], r["pattern"]): r["x"] for r in arr}
    table = []
    for k, g in group(arr, lambda r: (r["loop"], r["economics"], r["mode"])).items():
        row = dict(loop=k[0], economics=k[1], mode=k[2])
        for an, pats in ARRANGEMENTS.items():
            b = min((r for r in g if r["pattern"] in pats), key=lambda r: r["cost"])
            row[an] = dict(cost=b["cost"], pattern=b["pattern"], Ru_volume_fraction=b["Ru_volume_fraction"],
                           V_m3=b["V_m3"], y_NH3_out=b["y_NH3_out"], beds=b["beds"])
        best = min(g, key=lambda r: r["cost"])
        row["best"] = best["pattern"]
        table.append(row)
    summary["arrangements"] = table

    # ---- 2. sensitivities (KAAP-type loop, adiabatic) --------------------------------------------------------
    sens_cases = {
        "base": (kaap(), {}, None),
        "no inerts": (kaap(inerts=0.0), {}, None),
        "Ru/C up to 500 C": (kaap(), {}, 500.0),
        "Ru/C 3.2 wt% as measured (rate per kg catalyst, 590 kg/m3)": (kaap(), dict(w_Ru=0.032, rho_Ru=590.0,
                                                                                    ru_scale_with_loading=False), None),
        "Ru/C bed 430 kg/m3": (kaap(), dict(rho_Ru=430.0), None),
        "Ru/C bed 550 kg/m3": (kaap(), dict(rho_Ru=550.0), None),
        "Fe effectiveness 0.5": (kaap(), dict(fe_activity=0.5), None),
        "Fe and Ru/C effectiveness 0.5": (kaap(), dict(fe_activity=0.5, ru_activity=0.5), None),
        "Fe = wustite fit (Tripodi 2018)": (kaap(), dict(fe_kinetics="Fe_wustite"), None),
        "Fe catalyst 4 USD/kg": (kaap(), dict(p_Fe=4.0), None),
        "Fe catalyst 16 USD/kg": (kaap(), dict(p_Fe=16.0), None),
        "separator -5 C": (kaap(Tsep_C=-5.0), {}, None),
    }
    jobs = []
    for sname, (lp, eo, tmax) in sens_cases.items():
        for ename in (B95, D12):
            for pname in ("FFF", "FFR", "FRR", "RRR"):
                jobs.append(dict(loop=lp, econ=dict(ECON[ename], **eo), pattern=pname, mode="adiabatic", T_max_Ru=tmax,
                                 x0s=[base_x[(KAAP, ename, "adiabatic", pname)]],
                                 tag=dict(case=sname, economics=ename)))
    for pname in ("FFFF", "RRRR", "FRRR", "FFRR", "FFFR"):
        for ename in (B95, D12):
            jobs.append(dict(loop=kaap(), econ=ECON[ename], pattern=pname, mode="adiabatic",
                             tag=dict(case="four beds", economics=ename)))
    stamp(f"stage 2: {len(jobs)} sensitivity optimisations")
    sens = run_pool(solve, jobs, a.workers)
    for r, j in zip(sens, jobs):
        r["_job"] = j
    sens = polish(sens, lambda r: (r["case"], r["economics"]), a.workers)
    write_csv(HERE / "sensitivities.csv", sens, extra=("case", "economics"))
    summary["sensitivities"] = []
    for (case, ename), g in group(sens, lambda r: (r["case"], r["economics"])).items():
        b = min(g, key=lambda r: r["cost"])
        fe = [r for r in g if r["pattern"] in ("FFF", "FFFF")]
        st = [r for r in g if r["pattern"] in ("FFR", "FRR", "FRRR", "FFRR", "FFFR")]
        bst = min(st, key=lambda r: r["cost"])
        summary["sensitivities"].append(dict(
            case=case, economics=ename, best=b["pattern"], best_cost=b["cost"], all_Fe=min(r["cost"] for r in fe),
            Fe_first=bst["pattern"], Fe_first_cost=bst["cost"], Fe_first_Ru_volume_fraction=bst["Ru_volume_fraction"],
            costs={r["pattern"]: r["cost"] for r in g}))

    # ---- 3. design library for the decision boundaries -------------------------------------------------------
    jobs = []
    for P, Ts in LIBRARY_LOOPS:
        for pname in ("FFF", "FFR", "FRR", "RRR"):
            for ename in (B95, D12):
                x0s = [base_x[(ln, ename, "adiabatic", pname)] for ln in LOOPS]
                jobs.append(dict(loop=kaap(P_bar=P, Tsep_C=Ts), econ=ECON[ename], pattern=pname, mode="adiabatic",
                                 x0s=x0s, tag=dict(stage="anchor", economics=ename)))
    stamp(f"stage 3a: {len(jobs)} anchor optimisations")
    anchors = run_pool(solve, jobs, a.workers)
    ax = group(anchors, lambda r: (r["P_bar"], r["Tsep_C"], r["pattern"]))
    jobs = []
    for P, Ts in LIBRARY_LOOPS:
        for pname in ("FFR", "FRR", "RRR"):
            for cfe in C_FE_GRID:
                jobs.append(dict(loop=kaap(P_bar=P, Tsep_C=Ts), pattern=pname, c_fe=cfe, c_ru=C_RU_GRID,
                                 x0s=[r["x"] for r in ax[(P, Ts, pname)]], tag=dict(stage="library")))
        for cfe in C_FE_GRID:
            jobs.append(dict(loop=kaap(P_bar=P, Tsep_C=Ts), pattern="FFF", c_fe=cfe, c_ru=[C_RU_GRID[0]],
                             x0s=[r["x"] for r in ax[(P, Ts, "FFF")]], tag=dict(stage="library")))
    stamp(f"stage 3b: {len(jobs)} continuation chains")
    lib = [r for g in run_pool(chain, jobs, a.workers) for r in g]
    write_csv(HERE / "design_library.csv", lib, extra=("c_Ru", "c_Fe"))
    stamp("stage 3: done")

    # ---- 4. direct checks of the envelope --------------------------------------------------------------------
    from boundary import envelope_cost, load_library
    L = load_library(HERE / "design_library.csv")
    checks = []
    for P, Ts in ((90.0, -20.0), (150.0, -5.0)):
        for p, r_, i in ((53852.5, 0.9555, 0.0), (53852.5, 0.9555, 0.12), (53852.5, 0.90, 0.0), (20000.0, 0.9555, 0.04),
                         (100000.0, 0.90, 0.02)):
            for pname in ("FFF", "FFR", "FRR", "RRR"):
                checks.append(dict(loop=kaap(P_bar=P, Tsep_C=Ts),
                                   econ=dict(accounting="dcf", fin_rate=i, recovery=r_, p_Ru=p),
                                   pattern=pname, mode="adiabatic", x0s=[x["x"] for x in ax[(P, Ts, pname)]],
                                   tag=dict(p_Ru=p, recovery=r_, fin_rate=i)))
    stamp(f"stage 4: {len(checks)} direct optimisations at map points")
    chk = run_pool(solve, checks, a.workers)
    rows = []
    for r in chk:
        env = envelope_cost(L, (r["P_bar"], r["Tsep_C"]), r["pattern"], r["p_Ru"], r["recovery"], r["fin_rate"])
        rows.append(dict(P_bar=r["P_bar"], Tsep_C=r["Tsep_C"], pattern=r["pattern"], p_Ru=r["p_Ru"], recovery=r["recovery"],
                         fin_rate=r["fin_rate"], direct=r["cost"], envelope=env, envelope_minus_direct=env - r["cost"]))
    with (HERE / "envelope_checks.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for row in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})
    summary["envelope_check"] = dict(n=len(rows), max_envelope_minus_direct=max(r["envelope_minus_direct"] for r in rows),
                                     min_envelope_minus_direct=min(r["envelope_minus_direct"] for r in rows))
    summary["runtime_s"] = round(time.time() - t_start)
    summary["inputs"] = dict(loops=LOOPS, economics=ECON, de=DE_KW, c_Ru_grid=C_RU_GRID, c_Fe_grid=C_FE_GRID,
                             library_loops=LIBRARY_LOOPS, quadrature_points=41)
    (HERE / "summary.json").write_text(json.dumps(_round(summary), indent=1) + "\n", encoding="utf-8")
    stamp("done")


def _round(o):
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6) if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): _round(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_round(v) for v in o]
    return o


if __name__ == "__main__":
    main()
