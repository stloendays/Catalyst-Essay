"""Staged Fe -> Ru/C window in the KAAP-type loop (90 bar, -20 C, 8 % inerts) by direct global optimisation (item 6).

Imports the merged PR #75 converter model unchanged (analysis/nh3_staged_converter_2026_10_12/converter.py and the
optimiser settings of run_staged.py). Owned-metal 25-year cash flow, Ru 53,852.5 USD/kg, recovery 95.55 % unless the
case says otherwise. Arrangements FFF (all-Fe), FFR and FRR (Fe first, Ru/C downstream; 'staged' is the cheaper of the
two) and RRR (all-Ru/C).

  stage A  scan: for every case and arrangement, continuation in the financing rate i = 0, 0.5, ..., 12 %/y
           (Nelder-Mead from the previous optimum and from the committed KAAP optima at 0 and 12 %/y)
  stage B  edges: differential evolution + Nelder-Mead (run_staged.DE_KW, restarted from the scan optima) for all
           four arrangements at financing rates bracketing each edge seen in the scan; the window edge is the linear
           interpolation of the directly optimised cost differences between the two bracketing rates
             lower edge: staged = all-Ru/C (all-Ru/C optimal below)
             upper edge: staged = all-Fe   (all-Fe optimal above)
  stage C  base case: direct optimisation across the window (Ru/C share of catalyst volume) and at 1.35, 2.10, 5.10 %/y

Cases: base; Ru/C cap 480 C; Ru/C cap 500 C; both catalysts capped at 460 C; Ru/C law without H2 inhibition (K_H2 = 0,
rescaled to the fitted rate at 400 C, 90 bar, 2 % NH3, H2/N2 = 3); recovery 90 %; Ru price x0.7; Ru price x1.3.

    python staged_window.py [--workers 4]  -> staged_scan.csv, staged_direct.csv, staged_window.json
    NH3_MODEL=1.2 python staged_window.py [--workers 2] [--cases base "Ru/C cap 480 C" ...]
                                           -> nh3_1_2/staged_scan.csv, nh3_1_2/staged_direct.csv, nh3_1_2/staged_window.json

NH3_MODEL=1.2: converter.py builds its economic controls from the NH3-FINAL-1.2 core and manifest; its costs are
bit-identical to 1.1 (analysis/nh3_staged_converter_2026_10_12/staged_invariance_1_2.py), and the committed KAAP-type
optima used as the check and as start points are read from that folder's nh3_1_2/arrangements.csv (byte copy of the 1.1
file). --cases restricts the run to a subset of CASES (the base case is always included); the default is all cases.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SC = REPO / "analysis" / "nh3_staged_converter_2026_10_12"
sys.path.insert(0, str(SC))
import converter as C  # noqa: E402
import kinetics as K  # noqa: E402
from run_staged import DE_KW, PATTERNS  # noqa: E402

NM = C.NM                                                       # NH3_MODEL=1.1 (default) | 1.2, analysis/nh3_model.py
OUT = NM.out_dir(HERE)                                          # this folder for 1.1, nh3_1_2/ for 1.2
ARR = C.OUT / "arrangements.csv"                                # committed KAAP-type optima (1.2: byte copy of 1.1)

P_RU = 53852.5
PATS = ("FFF", "FFR", "FRR", "RRR")
RATES = [round(0.005 * k, 4) for k in range(25)]                 # 0 ... 12 %/y
T_MAX_FE = C.PAR["process"]["T_max_Fe_C"]
CASES = {
    "base": {},
    "Ru/C cap 480 C": dict(T_max_Ru=480.0),
    "Ru/C cap 500 C": dict(T_max_Ru=500.0),
    "both catalysts capped at 460 C": dict(T_max_Fe=460.0),
    "Ru/C without H2 inhibition (rescaled)": dict(no_h2_inhibition=True),
    "recovery 90%": dict(recovery=0.90),
    "Ru price x0.7": dict(p_Ru=P_RU * 0.7),
    "Ru price x1.3": dict(p_Ru=P_RU * 1.3),
}
BASE_EXTRA_RATES = [0.010, 0.0135, 0.015, 0.021, 0.030, 0.040, 0.051, 0.060]

# --- Ru/C rate law without H2 inhibition -----------------------------------------------------------------------
_ORIG_RU = K.rate_ru_rossetti
_REF = (673.15, 90.0, 0.98 / 4, 3 * 0.98 / 4, 0.02)


def _ru_no_h2_raw(T, P_bar, yN, yH, yA, ru_wt_frac=None):
    p = K.KIN["Ru_C_Rossetti"]
    T = np.asarray(T, dtype=float)
    aN, aH, aA = K.activities(T, P_bar, yN, yH, yA)
    kf = p["A"] * np.exp(-p["Ea_cal_mol"] / (K.R_CAL * T))
    KA = np.exp(p["dS_NH3_cal_molK"] / K.R_CAL - p["dH_NH3_cal_mol"] / (K.R_CAL * T))
    num = aN ** 0.5 * aH ** 0.375 / aA ** 0.25 - aA ** 0.75 / (K.Ka(T) * aH ** 1.125)
    r = 2.0 * kf * num / (1.0 + KA * aA ** 0.2) / p["catalyst_density_kg_L"] / 3600.0
    if ru_wt_frac is not None:
        r = r * ru_wt_frac / p["ru_wt_frac"]
    return r


NO_H2_SCALE = float(_ORIG_RU(*_REF) / _ru_no_h2_raw(*_REF))


def rate_ru_no_h2(T, P_bar, yN, yH, yA, ru_wt_frac=None):
    return NO_H2_SCALE * _ru_no_h2_raw(T, P_bar, yN, yH, yA, ru_wt_frac)


def _setup(case):
    """Per-job switches (workers are reused across cases)."""
    o = CASES[case]
    C.PAR["process"]["T_max_Fe_C"] = o.get("T_max_Fe", T_MAX_FE)
    K.rate_ru_rossetti = rate_ru_no_h2 if o.get("no_h2_inhibition") else _ORIG_RU
    return o


def econ(case, i):
    o = CASES[case]
    return C.Econ(accounting="dcf", fin_rate=i, recovery=o.get("recovery", 0.9555), p_Ru=o.get("p_Ru", P_RU))


LOOP = C.Loop(P_bar=90.0, Tsep_C=-20.0, inerts=0.08)


def rec(case, pat, i, r, stage, dt):
    d = r["detail"]
    return dict(case=case, stage=stage, pattern=pat, fin_rate=i, cost=r["cost"], Ru_volume_fraction=d["Ru_volume_fraction"],
                V_m3=d["V_m3"], V_Ru_m3=d["V_Ru_m3"], Ru_metal_kg=d["Ru_metal_kg"], catalyst_Fe=d["catalyst_Fe"],
                catalyst_Ru=d["catalyst_Ru"], y_NH3_out=d["y_NH3_out"],
                beds=";".join(f"{b['catalyst']}:{b['T_in_C']:.1f}-{b['T_out_C']:.1f}:{b['volume_m3']:.3f}" for b in d["beds"]),
                x=";".join(f"{v:.5f}" for v in r["x"]), seconds=round(dt, 1))


def chain(job):
    o = _setup(job["case"])
    pat = PATTERNS[job["pattern"]]
    prev, out = None, []
    for i in RATES:
        t0 = time.time()
        starts = ([prev] if prev is not None else []) + job["x0s"]
        r = C.optimize(pat, LOOP, econ(job["case"], i), "adiabatic", o.get("T_max_Ru"), de=False, x0=starts[0],
                       restarts=starts[1:], nm_maxfev=1500)
        prev = r["x"]
        out.append(rec(job["case"], job["pattern"], i, r, "scan", time.time() - t0))
    return out


def direct(job):
    o = _setup(job["case"])
    t0 = time.time()
    r = C.optimize(PATTERNS[job["pattern"]], LOOP, econ(job["case"], job["fin_rate"]), "adiabatic", o.get("T_max_Ru"),
                   seed=1, restarts=job["x0s"], **DE_KW)
    return rec(job["case"], job["pattern"], job["fin_rate"], r, job.get("stage", "direct"), time.time() - t0)


def pool_map(fn, jobs, workers):
    with mp.get_context("spawn").Pool(workers) as p:
        return p.map(fn, jobs, chunksize=1)


def committed_x():
    out = {}
    with ARR.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["loop"].startswith("KAAP") and r["mode"] == "adiabatic" and r["economics"].startswith("25-y"):
                out.setdefault(r["pattern"], []).append([float(v) for v in r["x"].split(";")])
    return out


def table(recs):
    """{case: {rate: {pattern: record}}} keeping the cheapest record per (case, rate, pattern)."""
    t = {}
    for r in recs:
        d = t.setdefault(r["case"], {}).setdefault(r["fin_rate"], {})
        if r["pattern"] not in d or r["cost"] < d[r["pattern"]]["cost"]:
            d[r["pattern"]] = r
    return t


def diffs(d):
    st = min((d["FFR"], d["FRR"]), key=lambda r: r["cost"])
    return st, st["cost"] - d["RRR"]["cost"], st["cost"] - d["FFF"]["cost"]


def crossings(rates, g):
    """Rates where g changes sign (linear interpolation)."""
    out = []
    for a, b, ga, gb in zip(rates[:-1], rates[1:], g[:-1], g[1:]):
        if ga == 0 or (ga < 0) != (gb < 0):
            out.append(a + (b - a) * (-ga) / (gb - ga) if gb != ga else a)
    return out


def edges(trow):
    """Lower (staged = all-Ru/C) and upper (staged = all-Fe) edges from {rate: {pattern: rec}}."""
    rates = sorted(r for r in trow if all(p in trow[r] for p in PATS))
    lo = [diffs(trow[r])[1] for r in rates]
    up = [diffs(trow[r])[2] for r in rates]
    # all-Ru/C optimal where staged > RRR; staged optimal where staged < RRR and staged < FFF
    return dict(rates=rates, staged_minus_RRR=lo, staged_minus_FFF=up,
                lower=[x for x in crossings(rates, lo)], upper=[x for x in crossings(rates, up)])


def bracket_rates(e, step=0.0025):
    """Rates around an edge estimate for direct optimisation."""
    return sorted({round(min(max(e + k * step, 0.0), 0.12), 5) for k in (-2, -1, 1, 2)} | {round(min(max(e, 0.0), 0.12), 5)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cases", nargs="+", choices=list(CASES), default=None,
                    help="run only these cases (the base case is always included); default: all")
    a = ap.parse_args()
    if a.cases:                                                 # subset run (CASES keeps its order)
        keep = {"base", *a.cases}
        for c in [c for c in CASES if c not in keep]:
            del CASES[c]
    t0 = time.time()

    def stamp(m):
        print(f"[{time.time() - t0:6.0f} s] {m}", flush=True)

    stamp(f"Ru/C without H2 inhibition: rescale factor {NO_H2_SCALE:.6f} (fitted / uninhibited at 400 C, 90 bar, 2 % NH3)")
    cx = committed_x()
    # ---- check: direct optimisation reproduces the committed KAAP-type cash-flow optima at 0 and 12 %/y ----------
    jobs = [dict(case="base", pattern=p, fin_rate=i, x0s=cx[p], stage="check") for i in (0.0, 0.12) for p in PATS]
    checks = pool_map(direct, jobs, a.workers)
    committed = {}
    with ARR.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["loop"].startswith("KAAP") and r["mode"] == "adiabatic" and r["economics"].startswith("25-y"):
                committed[(0.12 if "12%" in r["economics"] else 0.0, r["pattern"])] = float(r["cost"])
    chk = [dict(fin_rate=r["fin_rate"], pattern=r["pattern"], direct=r["cost"], committed=committed[(r["fin_rate"], r["pattern"])],
                direct_minus_committed=r["cost"] - committed[(r["fin_rate"], r["pattern"])]) for r in checks]
    for c in chk:
        print("  check", c, flush=True)
        assert abs(c["direct_minus_committed"]) < 0.02, c
    stamp("committed KAAP-type optima reproduced within 0.02 USD/t")

    # ---- A. scan -------------------------------------------------------------------------------------------------
    jobs = [dict(case=c, pattern=p, x0s=cx[p]) for c in CASES for p in PATS]
    stamp(f"stage A: {len(jobs)} continuation chains x {len(RATES)} rates")
    scan = [r for g in pool_map(chain, jobs, a.workers) for r in g]
    T = table(scan)
    scan_edges = {c: edges(T[c]) for c in CASES}
    for c, e in scan_edges.items():
        stamp(f"  scan {c}: lower {e['lower']}, upper {e['upper']}")

    # ---- B. direct optimisation around each edge -------------------------------------------------------------------
    allrec = list(checks)
    want = set()
    for c, e in scan_edges.items():
        for x in e["lower"] + e["upper"]:
            for i in bracket_rates(x):
                want.add((c, i))
    for i in BASE_EXTRA_RATES:
        want.add(("base", round(i, 5)))
    for i in (0.0, 0.12):
        want.add(("base", i))

    def near_x(c, p, i):
        pts = sorted(T[c], key=lambda r: abs(r - i))[:2]
        return [[float(v) for v in T[c][r][p]["x"].split(";")] for r in pts] + cx[p][:1]

    done = {(r["case"], r["fin_rate"]) for r in checks}
    for rnd in range(3):
        todo = sorted(want - done)
        if not todo:
            break
        jobs = [dict(case=c, pattern=p, fin_rate=i, x0s=near_x(c, p, i)) for c, i in todo for p in PATS]
        stamp(f"stage B round {rnd + 1}: {len(jobs)} direct global optimisations at {len(todo)} (case, rate) points")
        allrec += pool_map(direct, jobs, a.workers)
        done |= set(todo)
        D = table(allrec)
        # an edge is closed when two directly optimised rates bracket it; otherwise widen the bracket
        for c in CASES:
            if c not in D:
                continue
            e = edges(D[c])
            for x in scan_edges[c]["lower"] + scan_edges[c]["upper"]:
                near = [r for r in e["rates"] if abs(r - x) <= 0.0051 * (rnd + 1)]
                kind = "lower" if x in scan_edges[c]["lower"] else "upper"
                got = [y for y in e[kind] if abs(y - x) <= 0.0051 * (rnd + 1)]
                if not got and near:
                    for i in bracket_rates(x, step=0.005 * (rnd + 2)):
                        want.add((c, i))
    D = table(allrec)

    # ---- outputs -----------------------------------------------------------------------------------------------
    def write(path, recs):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(recs[0]))
            w.writeheader()
            for r in sorted(recs, key=lambda r: (list(CASES).index(r["case"]), r["fin_rate"], r["pattern"])):
                w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})
    write(OUT / "staged_scan.csv", scan)
    write(OUT / "staged_direct.csv", allrec)

    out = dict(no_h2_inhibition_rescale_factor=NO_H2_SCALE, committed_check=chk, cases={})
    if NM.VERSION != "1.1":                                     # run identity (the 1.1 file is unchanged)
        out["model"] = dict(version=NM.VERSION, run=NM.RUNS[NM.VERSION], manifest=C.MANIFEST.relative_to(NM.root()).as_posix(),
                            F_CAL=float(C.CFG["economics"]["calibration_factor"]), cases_run=list(CASES),
                            committed_optima=ARR.relative_to(REPO).as_posix())
    for c in CASES:
        e = edges(D[c])
        es = scan_edges[c]
        # Ru/C share of catalyst volume of the optimum across the window (direct where available, scan otherwise)
        lo = e["lower"][0] if e["lower"] else (0.0 if diffs(D[c][min(D[c])])[2] < 0 else None)
        hi = e["upper"][-1] if e["upper"] else None
        share = []
        for src, tab in (("direct", D[c]), ("scan", T[c])):
            for i in sorted(tab):
                if all(p in tab[i] for p in PATS) and lo is not None and hi is not None and lo <= i <= hi:
                    st, _, _ = diffs(tab[i])
                    share.append(dict(source=src, fin_rate=i, pattern=st["pattern"], Ru_volume_fraction=st["Ru_volume_fraction"],
                                      staged_minus_all_Fe=st["cost"] - tab[i]["FFF"]["cost"]))
        out["cases"][c] = dict(
            window_direct=dict(lower=e["lower"], upper=e["upper"]),
            window_scan=dict(lower=es["lower"], upper=es["upper"]),
            direct_rates=e["rates"],
            direct_points=[dict(fin_rate=i, **{p: D[c][i][p]["cost"] for p in PATS},
                                staged=diffs(D[c][i])[0]["pattern"], staged_Ru_volume_fraction=diffs(D[c][i])[0]["Ru_volume_fraction"],
                                best=min(PATS, key=lambda p: D[c][i][p]["cost"]))
                           for i in e["rates"]],
            Ru_share_across_window=share)
    base = D["base"]
    out["base_savings_vs_all_Fe"] = {
        f"{100 * i:.2f}%/y": dict(staged_pattern=diffs(base[i])[0]["pattern"], staged=diffs(base[i])[0]["cost"],
                                   all_Fe=base[i]["FFF"]["cost"], all_RuC=base[i]["RRR"]["cost"],
                                   saving_staged=base[i]["FFF"]["cost"] - diffs(base[i])[0]["cost"],
                                   saving_best=base[i]["FFF"]["cost"] - min(base[i][p]["cost"] for p in PATS),
                                   best=min(PATS, key=lambda p: base[i][p]["cost"]),
                                   Ru_volume_fraction=diffs(base[i])[0]["Ru_volume_fraction"])
        for i in (0.0135, 0.021, 0.051)}
    out["runtime_s"] = round(time.time() - t0)
    (OUT / "staged_window.json").write_text(json.dumps(_round(out), indent=1) + "\n", encoding="utf-8")
    for c, v in out["cases"].items():
        print(c, "direct", v["window_direct"], "scan", v["window_scan"])
    print(json.dumps(_round(out["base_savings_vs_all_Fe"]), indent=1))
    stamp("done")


def _round(o):
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6) if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): _round(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_round(v) for v in o]
    return o


if __name__ == "__main__":
    main()
