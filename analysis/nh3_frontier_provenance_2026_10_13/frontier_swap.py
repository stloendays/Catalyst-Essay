"""Committed sources for the kinetics-swap frontier numbers (items 1-5 of the README).

Imports the merged PR #75 code unchanged (analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py: process states,
plug-flow / inlet-rate catalyst amounts, multiplier(), costs(), best(), evaluate()). First re-runs the committed
headline variant (NH3-FINAL-1.1 states, plug flow, measured rates) with kinetics_swap.evaluate() and stops unless it
reproduces kinetics_swap.json. Every other number uses the same arrays and the cost function below, which is
kinetics_swap.costs() with four explicit knobs (Ru/Fe price, catalyst life, converter-premium factor, effectiveness
factor) and is asserted equal to it at the base point.

    python frontier_swap.py                   -> frontier_swap.json, frontier_swap_robustness.csv (NH3-FINAL-1.1)
    NH3_MODEL=1.2 python frontier_swap.py     -> nh3_1_2/frontier_swap.json, nh3_1_2/frontier_swap_robustness.csv

With NH3_MODEL=1.2 kinetics_swap builds the 14,510 process states of NH3-FINAL-1.2 (run nh3_final_1_2_20261013), the
reproduction gate checks the committed 1.2 headline variant (states '1.2', plug flow, measured rates) of
analysis/nh3_staged_converter_2026_10_12/nh3_1_2/kinetics_swap.json, and the descriptor Ru-price parity of item 3 is
checked against the 1.2 Fig. 2 Ru price sweep (analysis/fe_bridge_backward_2026_09_29/nh3_1_2/ru_price_sweep.csv)
instead of the 1.1 manuscript value 163.76 USD/kg.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SC = REPO / "analysis" / "nh3_staged_converter_2026_10_12"
sys.path.insert(0, str(SC))
import kinetics_swap as KS  # noqa: E402

NM = KS.NM                                   # NH3_MODEL=1.1 (default) | 1.2, analysis/nh3_model.py
OUT = NM.out_dir(HERE)                       # this folder for 1.1, nh3_1_2/ for 1.2
hc = KS.hc
P_RU, P_FE = KS.P_RU, hc.PRICE["Fe"]
R_HEAD = 0.9555
# committed headline of the plug-flow / measured-rate variant, rounded as quoted (README of the kinetics swap)
HEADLINE = {
    "1.1": dict(Fe=(15.58, 425.0, 170.0), Ru_benchmark=(28.07, 325.0), parity=(24.6, 1), gaps=[-1.36, 1.12, -1.07, 1.86]),
    "1.2": dict(Fe=(14.93, 450.0, 140.0), Ru_benchmark=(33.07, 735.0), parity=(13.95, 2), gaps=[-3.46, 1.45, -1.41, 1.73]),
}[NM.VERSION]


def close(a, b, tol):
    assert abs(a - b) <= tol, (a, b)


def mult(accounting, recovery, i, life):
    if accounting == "benchmark":
        return 1.0 - recovery
    case = KS.MetalCashflow(project_y=float(KS.CFG["economics"]["plant_life_y"]), catalyst_life_y=float(life),
                            discount_rate=i, gross_recovery=recovery)
    return KS.annualized_metal_multiplier(case, 1.0, legacy_life_y=float(life))


class Model:
    """Catalyst amounts per process state for one sizing, and the generalised cost function."""

    def __init__(self, h, st, sizing):
        self.h = h
        self.fe_V = KS.amount(st, KS.rate_fe_m3, h, sizing)          # m3 Fe bed
        self.ru_M = KS.amount(st, KS.rate_ru_kgRu, h, sizing)        # kg Ru (measured Ru/C)
        self.kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)

    def cost(self, V, metal_kg, price, m, life=None, prem=1.0):
        h = self.h
        life = h.CATALYST_LIFE_Y if life is None else life
        Vf = np.where(np.isfinite(V), V, 1e6)
        base = (h.REACTOR_FIXED + h.REACTOR_VAR * np.power(Vf / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf / h.annual_output_t
        reactor = base + prem * h.vessel_pressure_premium(Vf)
        metal = metal_kg * price * m / life / h.annual_output_t
        total = metal + reactor + h.state_process_cost
        ok = np.isfinite(V) & (V <= h.V_CAP)
        return np.where(ok, total, np.inf), dict(metal=metal, reactor=reactor, process=h.state_process_cost)

    # --- catalysts ---
    def fe(self, acc="cashflow", i=0.0, life=None, prem=1.0, p_fe=P_FE, eta=1.0):
        life = self.h.CATALYST_LIFE_Y if life is None else life
        V = self.fe_V / eta
        return self.cost(V, V * self.h.ACTIVE_FRACTION * self.h.BED_DENSITY, p_fe, mult(acc, 0.0, i, life), life, prem), V

    def ruc(self, acc="cashflow", i=0.0, r=R_HEAD, rho=KS.RHO, w=KS.W, p_ru=P_RU, life=None, prem=1.0, eta=1.0):
        life = self.h.CATALYST_LIFE_Y if life is None else life
        M = self.ru_M / eta
        V = M / (w * rho)
        return self.cost(V, M, p_ru, mult(acc, r, i, life), life, prem), V

    def ru_bench(self, u=KS.U, alpha=1.0, p_ru=P_RU, prem=1.0):
        M = self.ru_M * u / alpha
        V = M / (self.h.ACTIVE_FRACTION * self.h.BED_DENSITY)
        return self.cost(V, M, p_ru, 1.0, None, prem), V


def opt(h, tot, V, mask=None, parts=None):
    t = tot if mask is None else np.where(mask, tot, np.inf)
    j = int(np.argmin(t))
    d = dict(cost=float(t[j]), T_C=float(h.state_T[j]), P_bar=float(h.state_P[j]), Tsep_C=float(h.state_Tsep[j]),
             V_m3=float(V[j]))
    if parts:
        d.update({k: float(v[j]) for k, v in parts.items()})
    return d


def gaps(M, i, **kw):
    """Supported Ru/C minus Fe (global and KAAP) at financing rate i; kw split between the two catalysts."""
    fe_kw = {k: kw[k] for k in ("life", "prem") if k in kw}
    fe_kw.update({k[3:]: kw[k] for k in ("fe_p_fe", "fe_eta") if k in kw})
    ru_kw = {k: kw[k] for k in ("r", "rho", "p_ru", "life", "prem") if k in kw}
    if "ru_eta" in kw:
        ru_kw["eta"] = kw["ru_eta"]
    (ft, fp), fV = M.fe("cashflow", i, **fe_kw)
    (rt, rp), rV = M.ruc("cashflow", i, **ru_kw)
    out = {}
    for name, mask in (("global", None), ("KAAP", M.kaap)):
        f, r = opt(M.h, ft, fV, mask, fp), opt(M.h, rt, rV, mask, rp)
        out[name] = dict(Ru_C=r, Fe=f, gap=r["cost"] - f["cost"])
    return out


def breakeven(M, where, **kw):
    g = lambda i: gaps(M, i, **kw)[where]["gap"]  # noqa: E731
    lo, hi = g(0.0), g(0.30)
    if not (lo < 0 < hi):
        return None
    return brentq(g, 0.0, 0.30, xtol=1e-10)


def parity_multiple(M, target, **kw):
    def g(la):
        v = float(np.min(M.ru_bench(alpha=10.0 ** la, **kw)[0][0]))
        return (v if math.isfinite(v) else 1e9) - target
    return 10 ** brentq(g, -6.0, 8.0, xtol=1e-12)


def main():
    out = {}
    h = KS.build(False)
    st = KS.state_arrays(h)
    # ---- 0. reproduce the committed headline -----------------------------------------------------------------
    committed = json.loads((KS.OUT / "kinetics_swap.json").read_text(encoding="utf-8"))
    cv = next(v for v in committed["variants"] if v["states"] == KS.STATES[0] and v["sizing"] == "plug" and v["scale"] == "source")
    _, V0, _, _ = h.cost_arrays("Fe", h.frozen_state_logtof(hc.EN0_CANON["Fe"]))
    j0 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == KS.CAL_STATE)
    rv = KS.evaluate(h, st, "plug", "source", float(V0[j0]))
    for key in ("Fe", "Ru_benchmark", "Ru_benchmark_best_100_200_bar"):
        close(rv[key]["cost"], cv[key]["cost"], 1e-5)
        close(rv[key]["P_bar"], cv[key]["P_bar"], 0)
    close(rv["Ru_activity_multiple_for_parity"], cv["Ru_activity_multiple_for_parity"], 1e-4)
    for k in ("cashflow 0% r 0.9555", "cashflow 12% r 0.9555"):
        for g in ("Ru_minus_Fe_global", "Ru_minus_Fe_KAAP"):
            close(rv["Ru_C_supported"][k][g], cv["Ru_C_supported"][k][g], 1e-5)
    sup = rv["Ru_C_supported"]
    head = dict(Fe=rv["Fe"], Ru_benchmark=rv["Ru_benchmark"], Ru_benchmark_best_100_200_bar=rv["Ru_benchmark_best_100_200_bar"],
                parity_multiple=rv["Ru_activity_multiple_for_parity"],
                RuC_minus_Fe={k: dict(global_=sup[k]["Ru_minus_Fe_global"], KAAP=sup[k]["Ru_minus_Fe_KAAP"])
                              for k in ("cashflow 0% r 0.9555", "cashflow 12% r 0.9555")})
    E = HEADLINE
    assert round(head["Fe"]["cost"], 2) == E["Fe"][0] and head["Fe"]["T_C"] == E["Fe"][1] and head["Fe"]["P_bar"] == E["Fe"][2]
    assert round(head["Ru_benchmark"]["cost"], 2) == E["Ru_benchmark"][0] and head["Ru_benchmark"]["P_bar"] == E["Ru_benchmark"][1]
    assert round(head["parity_multiple"], E["parity"][1]) == E["parity"][0]
    c0, c12 = head["RuC_minus_Fe"]["cashflow 0% r 0.9555"], head["RuC_minus_Fe"]["cashflow 12% r 0.9555"]
    assert [round(v, 2) for v in (c0["global_"], c12["global_"], c0["KAAP"], c12["KAAP"])] == E["gaps"]
    out["reproduced_headline"] = head
    print("headline reproduced:", json.dumps(head, default=float)[:400], flush=True)

    M = Model(h, st, "plug")
    Mi = Model(h, st, "inlet")
    # generalised cost == committed cost at the base point
    (ft, _), _ = M.fe("cashflow", 0.12)
    close(float(np.min(ft)), sup["cashflow 12% r 0.9555"]["Fe_global"]["cost"], 1e-9)
    (rt, _), _ = M.ruc("cashflow", 0.12)
    close(float(np.min(rt)), sup["cashflow 12% r 0.9555"]["Ru_C_global"]["cost"], 1e-9)
    (bt, _), _ = M.ru_bench()
    close(float(np.min(bt)), rv["Ru_benchmark"]["cost"], 1e-9)

    # ---- 1. break-even financing rate ----------------------------------------------------------------------------
    be = {}
    for r in (R_HEAD, 0.90):
        for where in ("global", "KAAP"):
            i = breakeven(M, where, r=r)
            g = gaps(M, i, r=r)[where]
            be[f"r {r} {where}"] = dict(rate=i, Ru_C=g["Ru_C"], Fe=g["Fe"])
    out["1_breakeven_financing_rate"] = be

    # ---- 2. supported Ru/C optimum pressure ----------------------------------------------------------------------
    p2 = {}
    for i in (0.0, 0.12):
        base = gaps(M, i)
        rows = []
        for rho in (430.0, 490.0, 550.0):
            for r in (0.90, R_HEAD):
                for pf in (0.7, 1.0, 1.3):
                    g = gaps(M, i, rho=rho, r=r, p_ru=P_RU * pf)["global"]["Ru_C"]
                    rows.append(dict(rho=rho, recovery=r, Ru_price_factor=pf, P_bar=g["P_bar"], T_C=g["T_C"], cost=g["cost"]))
        oat = [x for x in rows if sum([x["rho"] != 490.0, x["recovery"] != R_HEAD, x["Ru_price_factor"] != 1.0]) <= 1]
        p2[f"{int(round(100 * i))}%/y"] = dict(
            base=base["global"]["Ru_C"], one_at_a_time=oat,
            one_at_a_time_range_bar=[min(x["P_bar"] for x in oat), max(x["P_bar"] for x in oat)],
            all_combinations_range_bar=[min(x["P_bar"] for x in rows), max(x["P_bar"] for x in rows)], all_combinations=rows)
    out["2_RuC_optimum_pressure"] = p2

    # ---- 3. Ru-price parity, benchmark formulation ---------------------------------------------------------------
    fe_target = rv["Fe"]["cost"]

    def gp(lp):
        return float(np.min(M.ru_bench(p_ru=10.0 ** lp)[0][0])) - fe_target
    p_par = 10 ** brentq(gp, -2.0, 6.0, xtol=1e-12)
    (bt, bp), bV = M.ru_bench(p_ru=p_par)
    # same sweep on the frozen descriptor kinetics (1.1: reproduces the manuscript's 163.76 USD/kg; 1.2: the 1.2 Fig. 2
    # Ru price sweep's parity price, last row of fe_bridge_backward_2026_09_29/nh3_1_2/ru_price_sweep.csv)
    lv = h.frozen_state_logtof(hc.EN0_CANON["Ru"])
    fe_fr = KS.FROZEN["Fe"]

    def gf(lp):
        tot, V, _, _ = h.cost_arrays("Ru", lv, price=10.0 ** lp)
        return float(np.min(np.where(V <= h.V_CAP, tot, np.inf))) - fe_fr
    p_fr = 10 ** brentq(gf, -2.0, 6.0, xtol=1e-12)
    if NM.VERSION == "1.1":
        ref = dict(frozen_descriptor_manuscript=163.76)
    else:
        sweep = REPO / "analysis" / "fe_bridge_backward_2026_09_29" / "nh3_1_2" / "ru_price_sweep.csv"
        with sweep.open(encoding="utf-8") as f:
            p_ref = float(list(csv.DictReader(f))[-1]["price_USD_kg"])
        close(p_fr, p_ref, 1e-6 * p_ref)
        ref = dict(frozen_descriptor_reference=p_ref,
                   frozen_descriptor_reference_source="analysis/fe_bridge_backward_2026_09_29/nh3_1_2/ru_price_sweep.csv (last row)")
    out["3_Ru_price_parity_benchmark"] = dict(
        measured_kinetics_USD_kg=p_par, at_parity=opt(h, bt, bV),
        frozen_descriptor_USD_kg_recomputed=p_fr, **ref,
        Ru_benchmark_best_100_200_bar=rv["Ru_benchmark_best_100_200_bar"],
        Ru_benchmark_best_100_200_bar_minus_optimum=rv["Ru_benchmark_best_100_200_bar"]["cost"] - rv["Ru_benchmark"]["cost"])

    # ---- 4. parity multiple vs dispersion ratio and converter premium -------------------------------------------
    p4 = dict(vs_u={}, vs_premium={})
    for u in (5.5, 11.0, 22.0, 50.0):
        p4["vs_u"][str(u)] = parity_multiple(M, fe_target, u=u)
    for pf in (0.0, 0.5, 1.0, 2.0):
        (ft, _), _ = M.fe("benchmark", 0.0, prem=pf)
        p4["vs_premium"][f"x{pf}"] = dict(Fe=float(np.min(ft)), multiple=parity_multiple(M, float(np.min(ft)), prem=pf))
    close(p4["vs_u"]["11.0"], rv["Ru_activity_multiple_for_parity"], 1e-6)
    out["4_parity_multiple"] = p4

    # ---- 5. robustness ------------------------------------------------------------------------------------------
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
        g0, g12 = gaps(mm, 0.0, **kw), gaps(mm, 0.12, **kw)
        row = dict(case=name)
        for where in ("global", "KAAP"):
            row[f"gap_0_{where}"] = g0[where]["gap"]
            row[f"gap_12_{where}"] = g12[where]["gap"]
            row[f"RuC_P_0_{where}"] = g0[where]["Ru_C"]["P_bar"]
            row[f"RuC_P_12_{where}"] = g12[where]["Ru_C"]["P_bar"]
            row[f"breakeven_{where}"] = breakeven(mm, where, **kw)
        rows.append(row)
    with (OUT / "frontier_swap_robustness.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})
    summ = {}
    for where in ("global", "KAAP"):
        fe12 = [r for r in rows if r[f"gap_12_{where}"] > 0]
        ru0 = [r for r in rows if r[f"gap_0_{where}"] < 0]
        # a gap of -inf / +inf means Fe / Ru/C has no state within the 90 m3 bed cap (none in 1.1; in 1.2 Fe with
        # effectiveness 0.5 in the KAAP-type loop); min / max are taken over the cases where both are feasible
        fin = [r for r in rows if math.isfinite(r[f"gap_0_{where}"]) and math.isfinite(r[f"gap_12_{where}"])]
        summ[where] = dict(
            n_cases=len(rows), Fe_ahead_at_12=len(fe12), RuC_ahead_at_0=len(ru0),
            min_gap_12=min((r[f"gap_12_{where}"], r["case"]) for r in fin),
            max_gap_0=max((r[f"gap_0_{where}"], r["case"]) for r in fin),
            exceptions_12=[r["case"] for r in rows if r[f"gap_12_{where}"] <= 0],
            exceptions_0=[r["case"] for r in rows if r[f"gap_0_{where}"] >= 0])
        bad = {k: [r["case"] for r in rows if any(r[f"gap_{t}_{where}"] == s for t in (0, 12))]
               for k, s in (("Fe_infeasible", -math.inf), ("RuC_infeasible", math.inf))}
        summ[where].update({k: v for k, v in bad.items() if v})
    g0 = gaps(M, 0.0)["global"]
    dec = {k: g0["Ru_C"][k] - g0["Fe"][k] for k in ("process", "reactor", "metal")}
    dec["total"] = g0["gap"]
    close(sum(dec[k] for k in ("process", "reactor", "metal")), dec["total"], 1e-9)
    out["5_robustness"] = dict(summary=summ, cases=rows, decomposition_0pct_global=dict(
        RuC_minus_Fe=dec, Ru_C=g0["Ru_C"], Fe=g0["Fe"],
        note="process = compression energy + compressor CAPEX + refrigeration (state_process_cost); "
             "reactor = converter vessel proxy + Turton pressure premium; metal = catalyst metal charge"))
    if NM.VERSION != "1.1":                      # run identity (the 1.1 file is unchanged)
        out["model"] = dict(version=NM.VERSION, run=NM.RUNS[NM.VERSION], n_states=int(h.NSTATE), F_CAL=float(h.F_CAL))
    (OUT / "frontier_swap.json").write_text(json.dumps(KS._clean(out), indent=1) + "\n", encoding="utf-8")
    print(json.dumps(KS._clean({k: v for k, v in out.items() if k != "5_robustness"}), indent=1)[:6000])
    print(json.dumps(KS._clean(out["5_robustness"]["summary"]), indent=1))
    print(json.dumps(KS._clean(out["5_robustness"]["decomposition_0pct_global"]), indent=1))


if __name__ == "__main__":
    main()
