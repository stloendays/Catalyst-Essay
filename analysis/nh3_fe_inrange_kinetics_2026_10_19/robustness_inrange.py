"""The 16 robustness cases of analysis/nh3_frontier_provenance_2026_10_13/frontier_swap.py (section 5), with each
catalyst restricted to the pressure range of its rate law: Fe by Keestra 2025 KM1R-1964 (1-324 bar), Ru/C by
Rossetti 2006 (50-100 bar); main loop (each in range) and KAAP-type loop (90 bar, -20 C; both in range).

frontier_swap.Model, its cost function and case definitions are used unchanged; only kinetics_swap.rate_fe_m3 is
replaced and the optima are taken over the in-range states. Gate: the base case equals results.json of fe_inrange.py.

    set NH3_MODEL=1.2
    python robustness_inrange.py   -> robustness.csv, robustness.json
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "analysis" / "nh3_frontier_provenance_2026_10_13"))
import frontier_swap as FS  # noqa: E402
import keestra_fe as KF  # noqa: E402

KS = FS.KS
P_RU, P_FE = FS.P_RU, FS.P_FE


def gaps(M, i, mfe, mru, **kw):
    fe_kw = {k: kw[k] for k in ("life", "prem") if k in kw}
    fe_kw.update({k[3:]: kw[k] for k in ("fe_p_fe", "fe_eta") if k in kw})
    ru_kw = {k: kw[k] for k in ("r", "rho", "p_ru", "life", "prem") if k in kw}
    if "ru_eta" in kw:
        ru_kw["eta"] = kw["ru_eta"]
    (ft, _), fV = M.fe("cashflow", i, **fe_kw)
    (rt, _), rV = M.ruc("cashflow", i, **ru_kw)
    out = {}
    for name, (a, b) in {"global": (mfe, mru), "KAAP": (mfe & M.kaap, mru & M.kaap)}.items():
        f, r = FS.opt(M.h, ft, fV, a), FS.opt(M.h, rt, rV, b)
        out[name] = dict(Fe=f, Ru_C=r, gap=r["cost"] - f["cost"])
    return out


def breakeven(M, where, mfe, mru, **kw):
    g = lambda i: gaps(M, i, mfe, mru, **kw)[where]["gap"]  # noqa: E731
    lo, hi = g(0.0), g(0.30)
    if not (math.isfinite(lo) and math.isfinite(hi) and lo < 0 < hi):
        return None
    return brentq(g, 0.0, 0.30, xtol=1e-10)


def main():
    h = KS.build(False)
    st = KS.state_arrays(h)
    KS.rate_fe_m3 = lambda T, P, a, b, c: KF.rate(T, P, a, b, c, per="m3")
    M, Mi = FS.Model(h, st, "plug"), FS.Model(h, st, "inlet")
    mfe = h.state_P <= 324.0 + 1e-6
    mru = (h.state_P >= 50.0 - 1e-6) & (h.state_P <= 100.0 + 1e-6)
    ref = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["Fe_Keestra"]["Keestra KM1R-1964, source Kf"]
    b0, b12 = gaps(M, 0.0, mfe, mru), gaps(M, 0.12, mfe, mru)
    for got, key in ((b0["global"], "b_0"), (b12["global"], "b_12"), (b0["KAAP"], "c_0_KAAP"), (b12["KAAP"], "c_12_KAAP")):
        assert abs(got["gap"] - ref[key]["gap"]) < 1e-5, (key, got["gap"], ref[key]["gap"])
    cases = {
        "base": (M, {}), "Fe catalyst price x0.5": (M, dict(fe_p_fe=P_FE * 0.5)),
        "Fe catalyst price x2": (M, dict(fe_p_fe=P_FE * 2)), "Ru/C bed 430 kg/m3": (M, dict(rho=430.0)),
        "Ru/C bed 550 kg/m3": (M, dict(rho=550.0)), "recovery 90%": (M, dict(r=0.90)),
        "Ru price x0.7": (M, dict(p_ru=P_RU * 0.7)), "Ru price x1.3": (M, dict(p_ru=P_RU * 1.3)),
        "catalyst life 5 y": (M, dict(life=5.0)), "catalyst life 15 y": (M, dict(life=15.0)),
        "Fe effectiveness 0.5": (M, dict(fe_eta=0.5)), "Ru/C effectiveness 0.5": (M, dict(ru_eta=0.5)),
        "converter premium x0": (M, dict(prem=0.0)), "converter premium x0.5": (M, dict(prem=0.5)),
        "converter premium x2": (M, dict(prem=2.0)), "inlet-rate sizing": (Mi, {}),
    }
    rows = []
    for name, (mm, kw) in cases.items():
        g0, g12 = gaps(mm, 0.0, mfe, mru, **kw), gaps(mm, 0.12, mfe, mru, **kw)
        row = dict(case=name)
        for where in ("global", "KAAP"):
            row[f"gap_0_{where}"] = g0[where]["gap"]
            row[f"gap_12_{where}"] = g12[where]["gap"]
            row[f"Fe_P_12_{where}"] = g12[where]["Fe"]["P_bar"]
            row[f"RuC_P_12_{where}"] = g12[where]["Ru_C"]["P_bar"]
            row[f"breakeven_{where}"] = breakeven(mm, where, mfe, mru, **kw)
        rows.append(row)
    summ = {}
    for where in ("global", "KAAP"):
        fin = [r for r in rows if math.isfinite(r[f"gap_0_{where}"]) and math.isfinite(r[f"gap_12_{where}"])]
        bes = [r[f"breakeven_{where}"] for r in rows if r[f"breakeven_{where}"] is not None]
        summ[where] = dict(n_cases=len(rows), Fe_ahead_at_12=sum(r[f"gap_12_{where}"] > 0 for r in rows),
                           RuC_ahead_at_0=sum(r[f"gap_0_{where}"] < 0 for r in rows),
                           exceptions_12=[r["case"] for r in rows if not r[f"gap_12_{where}"] > 0],
                           exceptions_0=[r["case"] for r in rows if not r[f"gap_0_{where}"] < 0],
                           infeasible=[r["case"] for r in rows if r not in fin],
                           breakeven_range=[min(bes), max(bes)] if bes else None, n_breakeven=len(bes))
    with (HERE / "robustness.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})
    (HERE / "robustness.json").write_text(json.dumps(KS._clean(dict(summary=summ, cases=rows)), indent=1) + "\n",
                                          encoding="utf-8")
    print(json.dumps(KS._clean(summ), indent=1))


if __name__ == "__main__":
    main()
