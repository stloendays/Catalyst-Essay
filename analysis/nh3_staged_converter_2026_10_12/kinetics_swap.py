"""NH3-FINAL-1.1 with measured rate laws for Fe and Ru only; everything else frozen.

Fe: Dyson & Simon (1968) fused-iron (KM1) Temkin rate with fugacities (rate per m3 of catalyst bed).
Ru: Rossetti et al. (2006) promoted Ru/C, modified Temkin with H2 and NH3 adsorption terms (rate per kg Ru, measured on
    the 3.2 wt% catalyst). See parameters.yaml and validate_kinetics.py.

The 14,136 process states (T 350-450 C, P 10-1000 bar, separator -40 to 30 C; per-pass conversion 0.8 of the loop
equilibrium), compression, refrigeration, converter cost and the V <= 90 m3 cap are those of NH3-FINAL-1.1 (harness_core.py,
manifest nh3_final_20260905T134204Z). Only the catalyst mass changes:

  sizing   'inlet'  : harness convention, mass = NH3 production / rate at the converter inlet
           'plug'   : isothermal plug flow from inlet to outlet of the state (same T), mass = F_in int 2 dxi / r
  scale    'FCAL'   : NH3-FINAL-1.1 calibration logic: one factor, fixed so that Fe needs the frozen Fe bed (66.007 m3)
                      at the calibration state (400 C, 80 bar, -35 C) with the same sizing, applied to Fe and Ru alike
           'source' : each rate law with its own measured absolute rate
  states   'frozen' : process states of NH3-FINAL-1.1 (model equilibrium)
           'GB'     : process states rebuilt with the Gillespie-Beattie NH3 equilibrium, as in PR #64
                      (analysis/verify_2026_10_12_nh3_equilibrium, branch verify-hou-feed-2026-10-12)
           '1.2'    : (NH3_MODEL=1.2) the 14,510 process states of NH3-FINAL-1.2 (Gillespie-Beattie NH3 formation and
                      Newton-Cooper fugacities in the loop equilibrium, the basis the measured rate laws already use);
                      the equilibrium dimension of 1.1 collapses, so 1.2 has the four sizing x scale variants. The FCAL
                      target is re-derived on its definition: the 1.2 descriptor Fe bed at the calibration state.

Catalyst mapping (as in NH3-FINAL-1.1 and analysis/nh3_actual_ru_params_2026_10_07):
  Fe bed volume V from the rate per m3; Fe metal = V * 0.7151 * 2500 kg/m3 at 8 USD/kg, no recovery.
  Ru benchmark formulation (Ru in the fused-iron bed form): Ru metal = u * M_Ru, V = Ru / (0.7151 * 2500), with M_Ru the
      Ru mass of the measured Ru/C catalyst and u = 11 its dispersion gain; 53,852.5 USD/kg, no recovery.
  Supported Ru/C: Ru metal = M_Ru, V = M_Ru / (0.08 * 490); recovery 90-95.55 %; metal charged straight-line (benchmark
      accounting) or by the 25-year cash flow at a metal financing rate of 0 or 12 %/y (Fe on the same convention).

    python kinetics_swap.py   -> kinetics_swap.json, kinetics_swap_pressure_profiles.csv
    NH3_MODEL=1.2 python kinetics_swap.py   -> nh3_1_2/kinetics_swap.json, nh3_1_2/kinetics_swap_pressure_profiles.csv
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

import kinetics as K

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

if NM.VERSION == "1.1":
    sys.path.insert(0, str(REPO / "provenance" / "discover_v1" / "source_harness"))
sys.path.insert(0, str(REPO / "analysis" / "nh3_ru_net_recovery_boundary_2026_10_12"))
if NM.VERSION == "1.1":
    import harness_core as hc  # noqa: E402
else:
    hc = NM.core()
from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier  # noqa: E402

if NM.VERSION == "1.1":
    ROOT = REPO / "provenance" / "nh3_final_1_1" / "source_harness"          # holds inputs/<activity workbook>
    CFG = yaml.safe_load((REPO / "provenance" / "discover_v1" / "source_harness" / "outputs" / "nh3_final_20260905T134204Z"
                          / "manifest_resolved.yaml").read_text(encoding="utf-8"))
    FROZEN = dict(Fe=15.291704676621144, Ru=22.03059478781101, alpha=201.2234429878984, Fe_KAAP=19.06868861189332)
    STATES = ("frozen", "GB")
else:
    ROOT, CFG = NM.root(), NM.cfg()                 # NH3-FINAL-1.2 core, manifest and activity workbook
    _A = NM.anchors()
    FROZEN = dict(Fe=_A["Fe"], Ru=_A["Ru"], alpha=_A["alpha"])
    STATES = ("1.2",)
OUT = NM.out_dir(HERE)
U, W, RHO = 11.0, 0.08, 490.0
P_RU = hc.PRICE["Ru"]
CAL_STATE = (400.0, 80.0, -35.0)
NGRID = 81
_S = np.linspace(0.0, 1.0, NGRID)
GRID, DGRID = 1.0 - (1.0 - _S) ** 2, 2.0 * (1.0 - _S)
WTS = np.ones(NGRID)
WTS[1:-1:2], WTS[2:-1:2] = 4.0, 2.0
WTS /= 3.0 * (NGRID - 1)
RU_PER_KG_RU = 1.0 / K.KIN["Ru_C_Rossetti"]["ru_wt_frac"]   # rate per kg Ru = rate per kg catalyst / 0.032


# --- process states -----------------------------------------------------------------------------------------------

def gb_dG(T):
    """Gillespie-Beattie formation free energy of NH3 (eV, 1 bar), as in PR #64."""
    lK = -2.691122 * math.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T + 2001.6 / T + 2.6899
    return -hc.K_B_EV * T * math.log(10 ** lK / 1.01325)


_ORIG_GAS_G = hc.KineticContext.gas_G


def _corrected_gas_G(self, T):
    g = dict(_ORIG_GAS_G(self, T))
    g["NH3"] -= (g["NH3"] - 0.5 * g["N2"] - 1.5 * g["H2"]) - gb_dG(T)
    return g


def build(corrected):
    if NM.VERSION != "1.1":                     # 1.2: the canonical states of the selected run, nothing patched
        assert not corrected
        return hc.NH3Harness(CFG, ROOT)
    hc.KineticContext.gas_G = _corrected_gas_G if corrected else _ORIG_GAS_G
    try:
        return hc.NH3Harness(CFG, ROOT)
    finally:
        hc.KineticContext.gas_G = _ORIG_GAS_G


def state_arrays(h):
    X = np.array([s["X"] for s in h.process_states])
    ysep = np.array([s["ysep"] for s in h.process_states])
    ratio = ysep / (1 - ysep)
    nA = ratio * 2.0 * (1 - X) / X
    tot = 2.0 / X + nA
    return dict(T=h.state_T + 273.15, P=h.state_P, yN=(0.5 / X) / tot, yH=(1.5 / X) / tot, yA=np.maximum(nA / tot, 1e-12),
                xi_out=0.5 / tot, F_in=h.nh3_mol_s * tot, X=X)


# --- catalyst amounts per state -----------------------------------------------------------------------------------

def rate_fe_m3(T, P, yN, yH, yA):
    return K.rate_fe_dyson_simon(T, P, yN, yH, yA, per="m3")              # mol NH3 m^-3 s^-1


def rate_ru_kgRu(T, P, yN, yH, yA):
    return K.rate_ru_rossetti(T, P, yN, yH, yA) * RU_PER_KG_RU            # mol NH3 (kg Ru)^-1 s^-1


def amount(st, rate, h, sizing, chunk=2000):
    """Catalyst amount (m3 for Fe, kg Ru for Ru) per state; inf where the rate law forbids the state's outlet."""
    n = len(st["T"])
    out = np.empty(n)
    if sizing == "inlet":
        r = rate(st["T"], st["P"], st["yN"], st["yH"], st["yA"])
        return np.where(r > 0, h.nh3_mol_s / np.where(r > 0, r, 1.0), np.inf)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        xi = st["xi_out"][a:b, None] * GRID[None, :]
        tot = 1.0 - 2.0 * xi
        T = np.repeat(st["T"][a:b, None], NGRID, axis=1)
        P = np.repeat(st["P"][a:b, None], NGRID, axis=1)
        r = rate(T, P, (st["yN"][a:b, None] - xi) / tot, (st["yH"][a:b, None] - 3 * xi) / tot,
                 (st["yA"][a:b, None] + 2 * xi) / tot)
        ok = np.all(np.isfinite(r) & (r > 0), axis=1)
        integ = np.sum(WTS[None, :] * DGRID[None, :] * 2.0 / np.where(r > 0, r, 1.0), axis=1) * st["xi_out"][a:b]
        out[a:b] = np.where(ok, st["F_in"][a:b] * integ, np.inf)
    return out


def reactor(h, V):
    Vf = np.where(np.isfinite(V), V, 1e6)
    return ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(Vf / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf / h.annual_output_t
            + h.vessel_pressure_premium(Vf))


def multiplier(accounting, recovery, fin_rate):
    if accounting == "benchmark":
        return 1.0 - recovery
    case = MetalCashflow(project_y=float(CFG["economics"]["plant_life_y"]),
                         catalyst_life_y=float(CFG["economics"]["catalyst_life_y"]), discount_rate=fin_rate,
                         gross_recovery=recovery)
    return annualized_metal_multiplier(case, 1.0, legacy_life_y=float(CFG["economics"]["catalyst_life_y"]))


def costs(h, V, metal_kg, price, mult):
    metal = metal_kg * price * mult / h.CATALYST_LIFE_Y / h.annual_output_t
    total = metal + reactor(h, V) + h.state_process_cost
    return np.where(np.isfinite(V) & (V <= h.V_CAP), total, np.inf), metal


def best(h, total, V, mask=None, extra=None):
    t = total if mask is None else np.where(mask, total, np.inf)
    i = int(np.argmin(t))
    if not np.isfinite(t[i]):
        return None
    d = dict(cost=float(t[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]), Tsep_C=float(h.state_Tsep[i]),
             V_m3=float(V[i]), X_per_pass=float(h.process_states[i]["X"]))
    if extra:
        d.update({k: float(v[i]) for k, v in extra.items()})
    return d


def evaluate(h, st, sizing, scale, fcal_target):
    fe_V = amount(st, rate_fe_m3, h, sizing)
    ru_M = amount(st, rate_ru_kgRu, h, sizing)
    j = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == CAL_STATE)
    phi = fe_V[j] / fcal_target if scale == "FCAL" else 1.0          # rates multiplied by phi (masses divided)
    fe_V, ru_M = fe_V / phi, ru_M / phi
    kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    res = dict(sizing=sizing, scale=scale, rate_factor_phi=float(phi), Fe_bed_at_calibration_state_unscaled_m3=float(fe_V[j] * phi))

    def fe_cost(acc="benchmark", i=0.0):
        return costs(h, fe_V, fe_V * h.ACTIVE_FRACTION * h.BED_DENSITY, hc.PRICE["Fe"], multiplier(acc, 0.0, i))[0]

    fe = fe_cost()
    res["Fe"] = best(h, fe, fe_V)
    res["Fe_KAAP"] = best(h, fe, fe_V, kaap)
    # Ru, benchmark formulation (bulk Ru in the fused-iron bed form, no recovery)
    V_b = ru_M * U / (h.ACTIVE_FRACTION * h.BED_DENSITY)

    def ru_bench(alpha):
        return costs(h, V_b / alpha, ru_M * U / alpha, P_RU, 1.0)[0]
    rb = ru_bench(1.0)
    res["Ru_benchmark"] = best(h, rb, V_b)
    res["Ru_benchmark_KAAP"] = best(h, rb, V_b, kaap)
    res["Ru_benchmark_best_100_200_bar"] = best(h, rb, V_b, (h.state_P >= 100.0) & (h.state_P <= 200.0))
    res["n_states"] = int(h.NSTATE)
    target = res["Fe"]["cost"]

    def gap(la):
        v = float(np.min(ru_bench(10.0 ** la)))
        return (v if math.isfinite(v) else 1e9) - target
    res["Ru_activity_multiple_for_parity"] = 10 ** brentq(gap, -6.0, 8.0, xtol=1e-12) if gap(-6.0) > 0 > gap(8.0) else None
    # cost-vs-pressure profile (min over T and separator) of Fe and benchmark Ru
    prof = {}
    for P in np.unique(h.state_P):
        m = h.state_P == P
        prof[float(P)] = dict(Fe=float(np.min(np.where(m, fe, np.inf))), Ru_benchmark=float(np.min(np.where(m, rb, np.inf))))
    res["_profile"] = prof
    # supported Ru/C (u = 11 already in M_Ru: measured Ru/C), 8 wt%, 490 kg/m3
    V_s = ru_M / (W * RHO)
    sup = {}
    for acc, i in (("benchmark", 0.0), ("cashflow", 0.0), ("cashflow", 0.12)):
        fe_i = fe_cost(acc, i)
        fe_g, fe_k = best(h, fe_i, fe_V), best(h, fe_i, fe_V, kaap)
        for r in (0.90, 0.9555):
            tot, metal = costs(h, V_s, ru_M, P_RU, multiplier(acc, r, i))
            g, k = best(h, tot, V_s, extra=dict(Ru_kg=ru_M)), best(h, tot, V_s, kaap, extra=dict(Ru_kg=ru_M))
            sup[f"{acc} {int(round(100 * i))}% r {r}"] = dict(
                Ru_C_global=g, Fe_global=fe_g, Ru_minus_Fe_global=g["cost"] - fe_g["cost"],
                Ru_C_KAAP=k, Fe_KAAP=fe_k, Ru_minus_Fe_KAAP=k["cost"] - fe_k["cost"])
            if acc == "benchmark" and r == 0.9555:
                for P in np.unique(h.state_P):
                    res["_profile"][float(P)]["Ru_C_supported_r9555"] = float(np.min(np.where(h.state_P == P, tot, np.inf)))
    res["Ru_C_supported"] = sup
    return res


def frozen_reference(h):
    """Frozen descriptor kinetics on the same states (reproduces NH3-FINAL-1.1) and their pressure profiles."""
    out = {}
    for m in ("Fe", "Ru"):
        lv = h.frozen_state_logtof(hc.EN0_CANON[m])
        tot, V, _, _ = h.cost_arrays(m, lv)
        ok = V <= h.V_CAP
        out[m] = best(h, np.where(ok, tot, np.inf), V)
        out[f"_{m}_profile"] = {float(P): float(np.min(np.where((h.state_P == P) & ok, tot, np.inf))) for P in np.unique(h.state_P)}
    assert abs(out["Fe"]["cost"] - FROZEN["Fe"]) < 1e-9 and abs(out["Ru"]["cost"] - FROZEN["Ru"]) < 1e-9, out
    if NM.VERSION != "1.1":                     # descriptor Fe in the KAAP-type states (90 bar, -20 C) and run identity
        lv = h.frozen_state_logtof(hc.EN0_CANON["Fe"])
        tot, V, _, _ = h.cost_arrays("Fe", lv)
        kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
        out["Fe_KAAP"] = best(h, np.where(V <= h.V_CAP, tot, np.inf), V, kaap)
        out["model"] = dict(version=NM.VERSION, run=NM.RUNS[NM.VERSION], n_states=int(h.NSTATE), F_CAL=float(h.F_CAL),
                            Ru_activity_multiple_for_parity_descriptor=FROZEN["alpha"])
    return out


def main():
    summary = {"frozen_anchor_check": None, "variants": []}
    profiles = []
    h0 = build(False)
    fr = frozen_reference(h0)
    summary["frozen_anchor_check"] = {k: v for k, v in fr.items() if not k.startswith("_")}
    for P in sorted(fr["_Fe_profile"]):
        profiles.append(dict(states=STATES[0], sizing="descriptor", scale="F_CAL", P_bar=P,
                             Fe=fr["_Fe_profile"][P], Ru_benchmark=fr["_Ru_profile"][P]))
    # calibration target: the frozen Fe bed at the calibration state (400 C, 80 bar, -35 C), as in PR #64
    _, V0, _, _ = h0.cost_arrays("Fe", h0.frozen_state_logtof(hc.EN0_CANON["Fe"]))
    j0 = next(i for i in range(h0.NSTATE) if (h0.state_T[i], h0.state_P[i], h0.state_Tsep[i]) == CAL_STATE)
    fcal_target = float(V0[j0])
    summary["frozen_Fe_bed_at_calibration_state_m3"] = fcal_target
    for states in STATES:
        h = h0 if states == STATES[0] else build(True)
        st = state_arrays(h)
        for sizing in ("inlet", "plug"):
            for scale in ("FCAL", "source"):
                r = evaluate(h, st, sizing, scale, fcal_target)
                r["states"] = states
                for P, d in sorted(r.pop("_profile").items()):
                    profiles.append(dict(states=states, sizing=sizing, scale=scale, P_bar=P, **d))
                summary["variants"].append(r)
                f, rb = r["Fe"], r["Ru_benchmark"]
                print(f"[{states:6s} {sizing:5s} {scale:6s}] phi {r['rate_factor_phi']:.3g}  Fe {f['cost']:.3f} at "
                      f"{f['T_C']:.0f}/{f['P_bar']:.0f}/{f['Tsep_C']:.0f} V {f['V_m3']:.1f} | Ru(bench) {rb['cost']:.3f} at "
                      f"{rb['T_C']:.0f}/{rb['P_bar']:.0f}/{rb['Tsep_C']:.0f} | alpha* {r['Ru_activity_multiple_for_parity']}",
                      flush=True)
                for k, v in r["Ru_C_supported"].items():
                    print(f"      Ru/C {k:24s} global {v['Ru_C_global']['cost']:.3f} ({v['Ru_C_global']['P_bar']:.0f} bar) "
                          f"vs Fe {v['Fe_global']['cost']:.3f}  |  KAAP {v['Ru_C_KAAP']['cost']:.3f} vs Fe {v['Fe_KAAP']['cost']:.3f}",
                          flush=True)
    with (OUT / "kinetics_swap_pressure_profiles.csv").open("w", newline="", encoding="utf-8") as f:
        keys = ["states", "sizing", "scale", "P_bar", "Fe", "Ru_benchmark", "Ru_C_supported_r9555"]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in profiles:
            w.writerow({k: (f"{row[k]:.6f}" if isinstance(row.get(k), float) and math.isfinite(row[k]) else row.get(k, ""))
                        for k in keys})
    (OUT / "kinetics_swap.json").write_text(json.dumps(_clean(summary), indent=1) + "\n", encoding="utf-8")


def _clean(o):
    if isinstance(o, float):
        return round(o, 6) if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    return o


if __name__ == "__main__":
    main()
