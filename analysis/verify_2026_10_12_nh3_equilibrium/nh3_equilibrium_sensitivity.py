"""NH3-FINAL-1.1 with the experimental NH3 equilibrium in the plant loop (sensitivity, not a replacement).

The frozen model's NH3 formation free energy (DFT gas energies + ideal-gas corrections) lies 0.064 eV per NH3 above the
Gillespie-Beattie equilibrium constant at 400-450 C, so its loop equilibrium NH3 fraction at 90 bar is about 40% of the
experimental one. Here the NH3 gas free energy is shifted at every temperature by the gap to Gillespie-Beattie
(KineticContext.gas_G), which moves the loop equilibrium (process states) and the NH3 adsorption / reverse steps of the
microkinetics consistently. The fused-iron calibration is redone on its own definition: F_CAL is the factor at which Fe
needs the frozen bed volume at the calibration state (found here as the 400 C, 80 bar state whose frozen Fe bed is
65 m3). Everything else is frozen.

Outputs: nh3_equilibrium_sensitivity.json. Read-only with respect to the harness.
    python nh3_equilibrium_sensitivity.py [harness_root]   (default: $NH3_HARNESS)
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ["NH3_HARNESS"])
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

CFG = yaml.safe_load((HARNESS / "outputs" / "nh3_final_20260905T134204Z" / "manifest_resolved.yaml").read_text(encoding="utf-8"))
EV_KJ = 96.485332
U, W, RHO, R_RU = 11.0, 0.08, 490.0, 0.9555
FROZEN = dict(Fe=15.291704676621144, Ru=22.03059478781101)


def gb_dG(T):
    """Gillespie-Beattie formation free energy of NH3 (eV), standard state 1 bar."""
    lK = -2.691122 * math.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T + 2001.6 / T + 2.6899  # atm^-1
    return -hc.K_B_EV * T * math.log(10 ** lK / 1.01325)


_orig_gas_G = hc.KineticContext.gas_G


def corrected_gas_G(self, T):
    g = _orig_gas_G(self, T)
    gap = (g["NH3"] - 0.5 * g["N2"] - 1.5 * g["H2"]) - gb_dG(T)
    g = dict(g); g["NH3"] -= gap
    return g


def build(corrected):
    hc.KineticContext.gas_G = corrected_gas_G if corrected else _orig_gas_G
    h = hc.NH3Harness(CFG, HARNESS)
    return h


def evaluate(h, tag):
    t0 = time.time()
    lv = {m: h.frozen_state_logtof(hc.EN0_CANON[m]) for m in hc.ACTIVITY_ORDER_CANON}
    print(f"[{tag}] logtof for 15 metals over {h.NSTATE} states: {time.time() - t0:.0f} s", flush=True)
    return lv


def summarize(h, lv, fcal):
    h.F_CAL = fcal
    act = {m: h.base_condition.logtof(hc.EN0_CANON[m]) for m in hc.ACTIVITY_ORDER_CANON}
    act_order = sorted(act, key=act.get, reverse=True)
    res = {}
    for m in hc.ACTIVITY_ORDER_CANON:
        total, V, mc, rc = h.cost_arrays(m, lv[m])
        ok = V <= h.V_CAP
        if ok.any():
            i = int(np.argmin(np.where(ok, total, np.inf)))
            res[m] = dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
                          Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]), X=float(h.process_states[i]["X"]))
        else:
            res[m] = None
    feas = sorted([m for m in res if res[m]], key=lambda m: res[m]["cost"])
    # actual Ru (supported Ru/C) in the KAAP loop and globally, and Fe in the KAAP loop
    kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    p_eff = hc.PRICE["Ru"] * (1 - R_RU) / U
    tot, V, mc, _ = h.cost_arrays("Ru", lv["Ru"], price=p_eff)
    Vs = V * (h.ACTIVE_FRACTION * h.BED_DENSITY) / (U * W * RHO)
    reactor = ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(Vs / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf
               / h.annual_output_t + h.vessel_pressure_premium(Vs))
    tot_s = mc + reactor + h.state_process_cost
    fe_tot, fe_V, _, _ = h.cost_arrays("Fe", lv["Fe"])

    def best(t, v, mask=None):
        ok = v <= h.V_CAP
        if mask is not None:
            ok &= mask
        i = int(np.argmin(np.where(ok, t, np.inf)))
        return dict(cost=float(t[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]), Tsep_C=float(h.state_Tsep[i]))

    common = [m for m in hc.ACTIVITY_ORDER_CANON if res[m]]
    rho = spearmanr([act_order.index(m) for m in common], [feas.index(m) for m in common]).statistic
    return dict(F_CAL=fcal, activity_order=act_order[:5], economic_order=feas[:5],
                spearman_activity_vs_cost_feasible=float(rho), metals=res,
                Ru_actual_supported=dict(global_=best(tot_s, Vs), KAAP=best(tot_s, Vs, kaap)),
                Fe_KAAP=best(fe_tot, fe_V, kaap))


def calib_state(h, lv_fe):
    total, V, _, _ = h.cost_arrays("Fe", lv_fe)
    sel = np.where((h.state_T == 400.0) & (h.state_P == 80.0))[0]
    j = sel[int(np.argmin(np.abs(V[sel] - 65.0)))]
    return int(j), float(V[j])


def main():
    out = {}
    h0 = build(False)
    lv0 = evaluate(h0, "frozen")
    j, v = calib_state(h0, lv0["Fe"])
    st = (float(h0.state_T[j]), float(h0.state_P[j]), float(h0.state_Tsep[j]))
    print(f"calibration state {st}: frozen Fe bed {v:.4f} m3", flush=True)
    out["calibration_state"] = dict(T_C=st[0], P_bar=st[1], Tsep_C=st[2], V_Fe_frozen=v)
    out["frozen"] = summarize(h0, lv0, h0.F_CAL)
    assert abs(out["frozen"]["metals"]["Fe"]["cost"] - FROZEN["Fe"]) < 1e-9, out["frozen"]["metals"]["Fe"]
    assert abs(out["frozen"]["metals"]["Ru"]["cost"] - FROZEN["Ru"]) < 1e-9, out["frozen"]["metals"]["Ru"]

    h1 = build(True)
    lv1 = evaluate(h1, "corrected")
    k = next(i for i in range(h1.NSTATE) if (h1.state_T[i], h1.state_P[i], h1.state_Tsep[i]) == st)
    # F_CAL such that Fe needs the same bed at the calibration state: V ∝ 1 / (F_CAL * TOF)
    fcal1 = h0.F_CAL * 10 ** (lv0["Fe"][j] - lv1["Fe"][k])
    out["corrected_fixed_FCAL"] = summarize(h1, lv1, h0.F_CAL)
    out["corrected_recalibrated"] = summarize(h1, lv1, fcal1)
    out["equilibrium"] = [dict(T_C=C, gap_eV=(lambda g: (g["NH3"] - 0.5 * g["N2"] - 1.5 * g["H2"]))(_orig_gas_G(h0.ctx, C + 273.15))
                               - gb_dG(C + 273.15)) for C in (350, 400, 450, 500)]
    out["loop_conversion"] = {tag: dict(KAAP_425_X=float(next(s["X"] for s in hh.process_states
                                                             if (s["T_C"], s["P_bar"], s["Tsep_C"]) == (425.0, 90.0, -20.0))))
                              for tag, hh in (("frozen", h0), ("corrected", h1))}
    hc.KineticContext.gas_G = _orig_gas_G
    (HERE / "nh3_equilibrium_sensitivity.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    for tag in ("frozen", "corrected_fixed_FCAL", "corrected_recalibrated"):
        s = out[tag]
        print(f"\n[{tag}] F_CAL {s['F_CAL']:.1f}; activity {s['activity_order']}; economic {s['economic_order']}; "
              f"rho {s['spearman_activity_vs_cost_feasible']:.3f}")
        for m in ("Fe", "Ru", "Os", "Co"):
            r = s["metals"][m]
            print(f"   {m}: {r and round(r['cost'], 3)} at {r and (r['T_C'], r['P_bar'], r['Tsep_C'])} V {r and round(r['V_m3'], 1)}")
        print(f"   Ru actual (supported) global {s['Ru_actual_supported']['global_']}")
        print(f"   Ru actual (supported) KAAP {s['Ru_actual_supported']['KAAP']['cost']:.3f} vs Fe KAAP {s['Fe_KAAP']['cost']:.3f}")
    print("\nequilibrium gap (eV):", [round(e["gap_eV"], 4) for e in out["equilibrium"]], "KAAP X:", out["loop_conversion"])


if __name__ == "__main__":
    main()
