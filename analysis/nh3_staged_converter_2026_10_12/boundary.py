"""Decision boundaries from the design library (lower envelope of designs whose cost is linear in the catalyst charges).

A design's cost is  noncatalyst + (c_Ru M_Ru + c_Fe M_Fe + c_sup M_RuC) / annual t,  with c_Ru = p_Ru m(r, i) / L the
yearly charge per kg of Ru metal (m: benchmark straight-line 1 - r, or the 25-year cash-flow multiplier at financing
rate i), c_Fe and c_sup the charges per kg of fused Fe and of Ru/C support. The library holds the optimum of each
arrangement at a grid of (c_Ru, c_Fe); the cost at any Ru price, recovery and financing rate is the lowest library
design (an upper bound on the optimum, checked against direct optimisation in envelope_checks.csv).

    python boundary.py   -> boundary_price_financing.csv, boundary_pressure.csv, boundary_summary.json
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

import converter as C

HERE = Path(__file__).resolve().parent
P_FE = C.PAR["economics"]["Fe_catalyst_USD_kg"]
P_SUP = C.PAR["economics"]["Ru_C_support_USD_kg"]
LIFE = C.PAR["economics"]["catalyst_life_y"]
PATS = ("FFF", "FFR", "FRR", "RRR")
KAAP, CONV150 = (90.0, -20.0), (150.0, -5.0)


def load_library(path):
    lib = {}
    with Path(path).open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lib.setdefault((float(r["P_bar"]), float(r["Tsep_C"]), r["pattern"]), []).append(r)
    return {k: {c: np.array([float(r[c]) for r in rows]) for c in
                ("noncatalyst", "Ru_metal_kg", "mass_Fe_kg", "mass_Ru_cat_kg", "Ru_volume_fraction", "V_m3",
                 "c_Ru", "c_Fe", "y_NH3_out")} for k, rows in lib.items()}


@lru_cache(maxsize=None)
def _mult(accounting, recovery, fin_rate):
    return C.Econ(accounting=accounting, recovery=recovery, fin_rate=fin_rate).multiplier(recovery)


def charges(p_Ru, recovery, fin_rate, accounting="dcf"):
    """(c_Ru per kg Ru per year, c_Fe per kg Fe per year, c_support per kg Ru/C per year)."""
    m0 = _mult(accounting, 0.0, fin_rate)
    return p_Ru * _mult(accounting, recovery, fin_rate) / LIFE, P_FE * m0 / LIFE, P_SUP * m0 / LIFE


def env_at(L, loop, pattern, c_ru, c_fe, c_sup):
    d = L[(float(loop[0]), float(loop[1]), pattern)]
    cost = d["noncatalyst"] + (c_ru * d["Ru_metal_kg"] + c_fe * d["mass_Fe_kg"] + c_sup * d["mass_Ru_cat_kg"]) / C.H.annual_output_t
    j = int(np.argmin(cost))
    return float(cost[j]), float(d["Ru_volume_fraction"][j]), float(d["V_m3"][j])


def envelope_cost(L, loop, pattern, p_Ru, recovery, fin_rate, accounting="dcf"):
    return env_at(L, loop, pattern, *charges(p_Ru, recovery, fin_rate, accounting))[0]


def decide(L, loop, p_Ru, recovery, fin_rate, accounting="dcf"):
    ch = charges(p_Ru, recovery, fin_rate, accounting)
    res = {p: env_at(L, loop, p, *ch) for p in PATS}
    staged = min(("FFR", "FRR"), key=lambda p: res[p][0])
    best = min(PATS, key=lambda p: res[p][0])
    return dict(all_Fe=res["FFF"][0], staged=res[staged][0], staged_pattern=staged, all_Ru=res["RRR"][0],
                staged_minus_Fe=res[staged][0] - res["FFF"][0], best=best, best_Ru_volume_fraction=res[best][1],
                staged_Ru_volume_fraction=res[staged][1])


def _crossing(x, g):
    """Largest x below which g < 0, by linear interpolation; None if g >= 0 everywhere."""
    neg = g < 0
    if not neg.any():
        return None
    j = int(np.where(neg)[0].max())
    if j + 1 >= len(x):
        return float(x[-1])
    return float(x[j] + (x[j + 1] - x[j]) * (-g[j]) / (g[j + 1] - g[j]))


def _write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})


def main():
    L = load_library(HERE / "design_library.csv")
    loops = sorted({(k[0], k[1]) for k in L})
    prices = [float(v) for v in np.geomspace(2000.0, 200000.0, 41)]
    rates = [round(float(v), 4) for v in np.linspace(0.0, 0.12, 25)]
    rows = []
    for loop in (KAAP, CONV150):
        for r_ in (0.90, 0.9555):
            for p in prices:
                for i in rates:
                    rows.append(dict(P_bar=loop[0], Tsep_C=loop[1], recovery=r_, p_Ru=p, fin_rate=i,
                                     **decide(L, loop, p, r_, i)))
    _write(HERE / "boundary_price_financing.csv", rows)
    prow = []
    for loop in loops:
        for i in rates:
            prow.append(dict(P_bar=loop[0], Tsep_C=loop[1], accounting="dcf", recovery=0.9555, p_Ru=53852.5, fin_rate=i,
                             **decide(L, loop, 53852.5, 0.9555, i)))
        for r_ in (0.90, 0.9555):
            prow.append(dict(P_bar=loop[0], Tsep_C=loop[1], accounting="benchmark", recovery=r_, p_Ru=53852.5,
                             fin_rate=0.0, **decide(L, loop, 53852.5, r_, 0.0, accounting="frozen")))
    _write(HERE / "boundary_pressure.csv", prow)

    summ = {"critical_financing_rate": [], "pressure": [], "critical_Ru_charge": []}
    fine = np.linspace(0.0, 0.12, 241)
    for loop in (KAAP, CONV150):
        for r_ in (0.90, 0.9555):
            for p in (20000.0, 30000.0, 53852.5, 75000.0, 100000.0):
                dec = [decide(L, loop, p, r_, i) for i in fine]
                gaps = np.array([d["staged_minus_Fe"] for d in dec])
                anyru = np.array([min(d["staged"], d["all_Ru"]) - d["all_Fe"] for d in dec])
                summ["critical_financing_rate"].append(dict(
                    P_bar=loop[0], Tsep_C=loop[1], recovery=r_, p_Ru=p, staged_beats_Fe_below=_crossing(fine, gaps),
                    Ru_in_optimum_below=_crossing(fine, anyru), best_at_0=dec[0]["best"], best_at_12=dec[-1]["best"],
                    gap_at_0=float(gaps[0]), gap_at_12=float(gaps[-1])))
    for loop in loops:
        gaps = np.array([decide(L, loop, 53852.5, 0.9555, i)["staged_minus_Fe"] for i in fine])
        b95 = decide(L, loop, 53852.5, 0.9555, 0.0, accounting="frozen")
        b90 = decide(L, loop, 53852.5, 0.90, 0.0, accounting="frozen")
        d0 = decide(L, loop, 53852.5, 0.9555, 0.0)
        d12 = decide(L, loop, 53852.5, 0.9555, 0.12)
        summ["pressure"].append(dict(
            P_bar=loop[0], Tsep_C=loop[1], staged_beats_Fe_below_rate=_crossing(fine, gaps),
            benchmark_r95=dict(best=b95["best"], staged_minus_Fe=b95["staged_minus_Fe"], all_Fe=b95["all_Fe"],
                               staged=b95["staged"], all_Ru=b95["all_Ru"], best_Ru_fraction=b95["best_Ru_volume_fraction"]),
            benchmark_r90=dict(best=b90["best"], staged_minus_Fe=b90["staged_minus_Fe"]),
            dcf0=dict(best=d0["best"], staged_minus_Fe=d0["staged_minus_Fe"]),
            dcf12=dict(best=d12["best"], staged_minus_Fe=d12["staged_minus_Fe"], all_Fe=d12["all_Fe"])))
    # universal form: critical yearly Ru charge c_Ru, converted to Ru-price thresholds for both recoveries
    grid = np.geomspace(5.0, 40000.0, 600)
    for loop in loops:
        for acc, i in (("frozen", 0.0), ("dcf", 0.0), ("dcf", 0.04), ("dcf", 0.08), ("dcf", 0.12)):
            m0 = _mult(acc, 0.0, i)
            c_fe, c_sup = P_FE * m0 / LIFE, P_SUP * m0 / LIFE
            fe = env_at(L, loop, "FFF", 0.0, c_fe, c_sup)[0]
            st = np.array([min(env_at(L, loop, "FFR", c, c_fe, c_sup)[0], env_at(L, loop, "FRR", c, c_fe, c_sup)[0]) for c in grid])
            ru = np.array([env_at(L, loop, "RRR", c, c_fe, c_sup)[0] for c in grid])
            staged_best = grid[(st < fe) & (st <= ru)]
            c_st = _crossing(grid, st - fe)
            c_any = _crossing(grid, np.minimum(st, ru) - fe)
            row = dict(P_bar=loop[0], Tsep_C=loop[1], accounting=acc, fin_rate=i, all_Fe=fe,
                       c_Ru_staged_beats_Fe_below=c_st, c_Ru_any_Ru_optimal_below=c_any,
                       c_Ru_range_staged_is_optimum=[float(staged_best.min()), float(staged_best.max())] if staged_best.size else None)
            for r_ in (0.90, 0.9555):
                m = _mult(acc, r_, i)
                row[f"p_Ru_staged_beats_Fe_below_r{r_}"] = c_st * LIFE / m if c_st else None
                row[f"p_Ru_any_Ru_optimal_below_r{r_}"] = c_any * LIFE / m if c_any else None
                row[f"p_Ru_range_staged_optimum_r{r_}"] = ([v * LIFE / m for v in row["c_Ru_range_staged_is_optimum"]]
                                                           if staged_best.size else None)
            summ["critical_Ru_charge"].append(row)
    (HERE / "boundary_summary.json").write_text(json.dumps(summ, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summ["pressure"], indent=1))


if __name__ == "__main__":
    main()
