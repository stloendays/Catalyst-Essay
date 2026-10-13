"""Feasibility check: can the frozen NH3 model (NH3-FINAL-1.1) describe a staged Fe -> Ru/C converter as in KAAP?

Industrial KAAP loops place magnetite/fused iron in the first bed and promoted Ru/C downstream (Tripodi et al., J. Ind.
Eng. Chem. 2018, 10.1016/j.jiec.2018.05.027; RSC Sustain. Energy Fuels 2024, 10.1039/D4SE00254G): Ru is used where NH3
is high because Fe is inhibited by NH3 and Ru much less. This script asks whether the frozen kinetics reproduce that.

1. Apparent reaction orders in N2, H2 and NH3 of the frozen microkinetics (Condition.logtof) for Fe and Ru at 90 bar,
   400 and 425 C, H2/N2 = 3, NH3 2% (far from equilibrium). Measured orders for comparison: fused Fe, H2 about +1.5 and
   NH3 about -1 (Temkin-Pyzhev, alpha 0.5); promoted Ru, H2 negative (H inhibition) and NH3 weakly negative.
2. NH3 equilibrium of the model's gas-phase free energies against the Gillespie-Beattie constant (ref. 59 of the paper).
3. Staged bed: the frozen harness sizes a bed from the rate at the reactor inlet. Here the same logtof is integrated over
   the extent of reaction (isothermal plug flow, per process state of the KAAP loop, 90 bar and -20 C, and two
   high-pressure loops), Fe for the first fraction phi of the NH3 made per pass and supported Ru/C for the rest, and the
   reverse order. Ru on the paper's actual-catalyst reading (p (1 - r) / u, u = 11, r = 95.55%, 8 wt% Ru at 490 kg m-3).
   One factor per state rescales the integral so that pure Fe reproduces the frozen inlet-sized Fe mass of that state.

Read-only with respect to the harness. Output: hybrid_bed_feasibility.json.
    python hybrid_bed_feasibility.py [harness_root]   (default: $NH3_HARNESS)
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ["NH3_HARNESS"])
sys.path.insert(0, str(HARNESS))
from harness_core import EN0_CANON, K_B_EV, MW, PRICE, NH3Harness  # noqa: E402

h = NH3Harness(yaml.safe_load((HARNESS / "outputs" / "nh3_final_20260905T134204Z" / "manifest_resolved.yaml")
                              .read_text(encoding="utf-8")), HARNESS)
assert h.NSTATE == 14136
U, W, RHO, R_RU = 11.0, 0.08, 490.0, 0.9555
BENCH = h.ACTIVE_FRACTION * h.BED_DENSITY
NXI = 401


def orders(T_K, P, yA, metal, d=0.02):
    yN, yH = (1 - yA) * 0.25, (1 - yA) * 0.75
    p0 = [P * yN, P * yH, P * yA]
    base = h.ctx.condition(T_K, *p0).logtof(EN0_CANON[metal])
    out = {}
    for i, sp in enumerate(("N2", "H2", "NH3")):
        p = list(p0); p[i] *= 10 ** d
        out[sp] = (h.ctx.condition(T_K, *p).logtof(EN0_CANON[metal]) - base) / d
    return out


def y_eq(Kp, P):  # 1/2 N2 + 3/2 H2 = NH3, Kp in bar^-1, stoichiometric feed
    f = lambda x: (2 * x / (4 - 2 * x) * P) / (((1 - x) / (4 - 2 * x) * P) ** 0.5 * ((3 - 3 * x) / (4 - 2 * x) * P) ** 1.5) - Kp
    x = brentq(f, 1e-9, 1 - 1e-9)
    return 2 * x / (4 - 2 * x)


def vessel_premium(V, P):
    if not h.PCAPEX_ENABLED:
        return 0.0
    Vd = max(V, h.PC_V_AMIN); D = (4.0 * Vd / (math.pi * h.PC_V_LD)) ** (1 / 3)
    t = P * D / (2.0 * (h.PC_V_SE - 0.6 * P)) + h.PC_V_CA
    cp0 = float(h.turton_cp0(h.PC_VK, Vd, h.PC_V_AMIN, h.PC_V_AMAX, h.PC_V_NEXP))
    return cp0 * h.PC_V_B2 * h.PC_V_FM * (max(t / h.PC_V_TMIN, 1.0) - 1.0) * h.PC_INDEX_RATIO * h.crf / h.annual_output_t


def reactor(V, P):
    return (h.REACTOR_FIXED + h.REACTOR_VAR * (V / h.REACTOR_REF) ** h.REACTOR_EXP) * h.crf / h.annual_output_t + vessel_premium(V, P)


def staged(T, P, Tsep):
    s = h.self_consistent_process_state(T, P, Tsep)
    X, ysep = s["X"], s["ysep"]
    nN0, nH0, nA0 = 0.5 / X, 1.5 / X, ysep / (1 - ysep) * 2.0 * (1 - X) / X
    xi = np.linspace(0.0, 1.0, NXI)
    lt = {}
    for m in ("Fe", "Ru"):
        v = []
        for x in xi:
            nN, nH, nA = nN0 - 0.5 * x, nH0 - 1.5 * x, nA0 + x; tot = nN + nH + nA
            v.append(h.ctx.condition(T + 273.15, P * nN / tot, P * nH / tot, max(P * nA / tot, 1e-12)).logtof(EN0_CANON[m]))
        lt[m] = np.array(v)
    I = {m: np.concatenate([[0.0], np.cumsum(0.5 * (10 ** -lt[m][1:] + 10 ** -lt[m][:-1]) * np.diff(xi))]) for m in lt}
    k = 10 ** (-lt["Fe"][0]) / I["Fe"][-1]
    p_eff = PRICE["Ru"] * (1 - R_RU) / U

    def cost(mFe, mRu):
        V = mFe / BENCH + mRu / (U * W * RHO)
        return ((mFe * PRICE["Fe"] + mRu * p_eff) / h.CATALYST_LIFE_Y / h.annual_output_t + reactor(V, P)
                + s["process_cost"]), V

    pre = lambda m: h.nh3_mol_s * MW[m] / h.F_CAL * k
    fe_first = [cost(pre("Fe") * I["Fe"][j], pre("Ru") * (I["Ru"][-1] - I["Ru"][j])) for j in range(NXI)]
    ru_first = [cost(pre("Fe") * (I["Fe"][-1] - I["Fe"][j]), pre("Ru") * I["Ru"][j]) for j in range(NXI)]

    def best(curve):
        c = np.array([x[0] if x[1] <= h.V_CAP else np.inf for x in curve])
        j = int(np.argmin(c))
        return dict(cost=float(c[j]), phi=float(xi[j])) if np.isfinite(c[j]) else None

    pure_fe, pure_ru = fe_first[-1], fe_first[0]
    return dict(T_C=T, P_bar=P, Tsep_C=Tsep, X=X, y_NH3_inlet=ysep,
                ru_fe_rate_ratio_inlet=float(10 ** (lt["Ru"][0] - lt["Fe"][0])),
                ru_fe_rate_ratio_outlet=float(10 ** (lt["Ru"][-1] - lt["Fe"][-1])),
                plug_flow_over_inlet_Fe=float(I["Fe"][-1] / 10 ** -lt["Fe"][0]),
                plug_flow_over_inlet_Ru=float(I["Ru"][-1] / 10 ** -lt["Ru"][0]),
                pure_Fe=dict(cost=pure_fe[0], V_m3=pure_fe[1], feasible=pure_fe[1] <= h.V_CAP),
                pure_Ru=dict(cost=pure_ru[0], V_m3=pure_ru[1], feasible=pure_ru[1] <= h.V_CAP),
                best_Fe_first=best(fe_first), best_Ru_first=best(ru_first))


def main():
    out = {"orders": [], "equilibrium": [], "staged": []}
    for T_K in (673.15, 698.15):
        for m in ("Fe", "Ru"):
            out["orders"].append(dict(T_C=round(T_K - 273.15), P_bar=90, y_NH3=0.02, metal=m, **orders(T_K, 90.0, 0.02, m)))
    for C in (400, 425, 450):
        T = C + 273.15; gg = h.ctx.gas_G(T); G = gg["NH3"] - 0.5 * gg["N2"] - 1.5 * gg["H2"]
        Kmod = math.exp(-G / (K_B_EV * T))
        Kexp = 10 ** (-2.691122 * math.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T + 2001.6 / T + 2.6899) / 1.01325
        out["equilibrium"].append(dict(T_C=C, dGf_model_kJ_mol=G * 96.485, dGf_exp_kJ_mol=-8.314462618e-3 * T * math.log(Kexp),
                                       y_eq_90bar_model=y_eq(Kmod, 90.0), y_eq_90bar_exp=y_eq(Kexp, 90.0)))
    for P, Tsep in ((90.0, -20.0), (150.0, -20.0), (200.0, -10.0)):
        for T in h.T_GRID_C:
            out["staged"].append(staged(float(T), P, Tsep))
    for loop in sorted({(d["P_bar"], d["Tsep_C"]) for d in out["staged"]}):
        rows = [d for d in out["staged"] if (d["P_bar"], d["Tsep_C"]) == loop]
        pick = lambda key: min((d[key]["cost"] if isinstance(d[key], dict) and "cost" in d[key] and
                                (d[key].get("feasible", True)) else np.inf, d["T_C"]) for d in rows)
        out.setdefault("loop_optima", []).append(dict(P_bar=loop[0], Tsep_C=loop[1], pure_Fe=pick("pure_Fe"),
                                                      pure_Ru=pick("pure_Ru"), Fe_first=pick("best_Fe_first"),
                                                      Ru_first=pick("best_Ru_first")))
    (HERE / "hybrid_bed_feasibility.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    for r in out["orders"]:
        print(f"orders {r['metal']} {r['T_C']} C: N2 {r['N2']:+.2f} H2 {r['H2']:+.2f} NH3 {r['NH3']:+.2f}")
    for r in out["equilibrium"]:
        print(f"equilibrium {r['T_C']} C: dGf model {r['dGf_model_kJ_mol']:+.1f} exp {r['dGf_exp_kJ_mol']:+.1f} kJ/mol; "
              f"y_eq(90 bar) model {r['y_eq_90bar_model']:.3f} exp {r['y_eq_90bar_exp']:.3f}")
    for d in out["staged"]:
        bf, br = d["best_Fe_first"], d["best_Ru_first"]
        print(f"{d['P_bar']:4.0f} bar {d['Tsep_C']:4.0f} C {d['T_C']:4.0f} C  Ru/Fe rate {d['ru_fe_rate_ratio_inlet']:6.1f} -> "
              f"{d['ru_fe_rate_ratio_outlet']:5.2f}  PFR/inlet Fe {d['plug_flow_over_inlet_Fe']:.2f} Ru {d['plug_flow_over_inlet_Ru']:6.2f}  "
              f"Fe {d['pure_Fe']['cost']:8.3f}{'' if d['pure_Fe']['feasible'] else '*'}  Ru {d['pure_Ru']['cost']:8.3f}"
              f"{'' if d['pure_Ru']['feasible'] else '*'}  Fe-first {bf and round(bf['cost'], 3)} (phi {bf and bf['phi']})  "
              f"Ru-first {br and round(br['cost'], 3)} (phi {br and br['phi']})")
    for r in out["loop_optima"]:
        print("loop optimum", r)


if __name__ == "__main__":
    main()
