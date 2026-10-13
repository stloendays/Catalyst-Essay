"""NH3-FINAL-1.2 calibration and deterministic comparison against NH3-FINAL-1.1.

Variants (all with the 1.2 harness_core; only the `thermo` block differs):
  v1_1        no thermo block                         -> must reproduce NH3-FINAL-1.1 bit for bit (14,136 states, 15.2917 / 22.0306)
  gb          Gillespie-Beattie NH3 formation, ideal gas (PR #64 / #72 basis)
  gb_nc_loop  + Newton-Cooper fugacities in the loop equilibrium only (PR #77 basis)
  v1_2        + Newton-Cooper fugacities in the microkinetics as well (NH3-FINAL-1.2)

F_CAL is recalibrated on the NH3-FINAL-1.1 definition: the factor at which Fe needs the NH3-FINAL-1.1 Fe bed at the
calibration state (400 C, 80 bar, -35 C separator). V is proportional to 1 / (F_CAL * TOF), so
F_CAL(variant) = F_CAL(1.1) * 10 ** (logTOF_Fe(1.1) - logTOF_Fe(variant)) at that state.

    python calibrate_and_compare.py            -> calibration_comparison.json
"""
from __future__ import annotations

import copy
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness_core as hc  # noqa: E402

CFG11 = yaml.safe_load((HERE / "configs" / "nh3_final_1_1_reference.yaml").read_text(encoding="utf-8"))
CFG11["inputs"]["activity_workbook"] = "../../nh3_final_1_1/source_harness/inputs/ammonia_activity_volcano_s1_v1.xlsx"
CAL_STATE = (400.0, 80.0, -35.0)
KAAP_STATE = (425.0, 90.0, -20.0)
FROZEN = dict(NSTATE=14136, Fe=15.291704676621144, Ru=22.03059478781101, Os=25.83179725613286)
VARIANTS = {
    "v1_1": None,
    "gb": dict(nh3_formation_reference="gillespie_beattie", fugacity="ideal"),
    "gb_nc_loop": dict(nh3_formation_reference="gillespie_beattie", fugacity="newton_cooper",
                       apply_to_loop_equilibrium=True, apply_to_microkinetics=False),
    "v1_2": dict(nh3_formation_reference="gillespie_beattie", fugacity="newton_cooper",
                 apply_to_loop_equilibrium=True, apply_to_microkinetics=True),
}


def cfg_for(name):
    cfg = copy.deepcopy(CFG11)
    if VARIANTS[name] is not None:
        cfg["thermo"] = dict(VARIANTS[name])
    return cfg


def state_index(h, st):
    return next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == st)


def summarize(h, lv, fcal):
    h.F_CAL = fcal
    act = {m: h.base_condition.logtof(h.EN0[m]) for m in h.activity_order}
    act_order = sorted(h.activity_order, key=act.get, reverse=True)
    metals = {}
    for m in h.activity_order:
        total, V, _, _ = h.cost_arrays(m, lv[m])
        ok = V <= h.V_CAP
        iu = int(np.argmin(total))
        feas = None
        if ok.any():
            i = int(np.argmin(np.where(ok, total, np.inf)))
            feas = dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
                        Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]), X=float(h.process_states[i]["X"]))
        metals[m] = dict(activity_logTOF=float(act[m]), unconstrained_cost=float(total[iu]), feasible=feas)
    raw = sorted(h.activity_order, key=lambda m: metals[m]["unconstrained_cost"])
    feas_order = sorted([m for m in metals if metals[m]["feasible"]], key=lambda m: metals[m]["feasible"]["cost"])
    ar = {m: i + 1 for i, m in enumerate(act_order)}
    top3 = act_order[:3]
    top3_cost = sorted(top3, key=lambda m: metals[m]["unconstrained_cost"])
    rho3 = float(spearmanr([ar[m] for m in top3], [top3_cost.index(m) + 1 for m in top3]).statistic)
    rho_raw = float(spearmanr([ar[m] for m in h.activity_order], [raw.index(m) + 1 for m in h.activity_order]).statistic)
    k = state_index(h, CAL_STATE)
    _, V, _, _ = h.cost_arrays("Fe", lv["Fe"])
    return dict(F_CAL=float(fcal), Fe_bed_at_calibration_state=float(V[k]), activity_order=act_order,
                raw_economic_order=raw, feasible_economic_order=feas_order, top3_spearman=rho3,
                raw_global_spearman=rho_raw, metals=metals)


def run_variant(name, base_cal_logtof=None):
    t0 = time.time()
    h = hc.NH3Harness(cfg_for(name), HERE)
    t1 = time.time()
    lv = {m: h.frozen_state_logtof(h.EN0[m]) for m in h.activity_order}
    t2 = time.time()
    k = state_index(h, CAL_STATE)
    cal_lt = float(lv["Fe"][k])
    fcal_fixed = float(h.F_CAL)
    fcal_recal = fcal_fixed * 10 ** ((cal_lt if base_cal_logtof is None else base_cal_logtof) - cal_lt)
    kx = [s["X"] for s in h.process_states if (s["T_C"], s["P_bar"], s["Tsep_C"]) == KAAP_STATE]
    return dict(name=name, NSTATE=h.NSTATE, seconds_build=t1 - t0, seconds_logtof=t2 - t1, cal_logtof_Fe=cal_lt,
                cal_X=float(h.process_states[k]["X"]), KAAP_425_X=float(kx[0]) if kx else None,
                fixed_FCAL=summarize(h, lv, fcal_fixed), recalibrated=summarize(h, lv, fcal_recal))


def report(r):
    print(f"[{r['name']}] states {r['NSTATE']} build {r['seconds_build']:.0f}s logtof {r['seconds_logtof']:.0f}s "
          f"F_CAL {r['fixed_FCAL']['F_CAL']:.1f}->{r['recalibrated']['F_CAL']:.1f} cal X {r['cal_X']:.4f} "
          f"KAAP X {r['KAAP_425_X']}", flush=True)
    for tag in ("fixed_FCAL", "recalibrated"):
        s = r[tag]
        print(f"   {tag}: Fe bed at cal {s['Fe_bed_at_calibration_state']:.3f}; activity {s['activity_order'][:3]} "
              f"economic {s['feasible_economic_order'][:5]} rho3 {s['top3_spearman']:.2f} raw15 {s['raw_global_spearman']:.3f}",
              flush=True)
        for m in ("Fe", "Ru", "Os"):
            f = s["metals"][m]["feasible"]
            print(f"      {m}: {f and round(f['cost'], 4)} at {f and (f['T_C'], f['P_bar'], f['Tsep_C'])} "
                  f"V {f and round(f['V_m3'], 2)}", flush=True)


def main():
    base = run_variant("v1_1")
    report(base)
    assert base["NSTATE"] == FROZEN["NSTATE"], base["NSTATE"]
    for m in ("Fe", "Ru", "Os"):
        assert abs(base["fixed_FCAL"]["metals"][m]["feasible"]["cost"] - FROZEN[m]) < 1e-9, m
    print("NH3-FINAL-1.1 anchors reproduced bit for bit", flush=True)
    names = [n for n in VARIANTS if n != "v1_1"]
    with ProcessPoolExecutor(max_workers=3) as ex:
        runs = list(ex.map(run_variant, names, [base["cal_logtof_Fe"]] * len(names)))
    out = dict(calibration_state=dict(zip(("T_C", "P_bar", "Tsep_C"), CAL_STATE)),
               variants={"v1_1": base, **{r["name"]: r for r in runs}})
    for r in runs:
        report(r)
    (HERE / "calibration_comparison.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
