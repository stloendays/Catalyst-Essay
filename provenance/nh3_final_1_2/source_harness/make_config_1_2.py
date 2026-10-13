"""Write configs/nh3_final_1_2.yaml from the NH3-FINAL-1.1 manifest: thermo block, recalibrated F_CAL, model version.
Frozen-regression anchors are filled from the first full run (promote step), as for NH3-FINAL-1.1.

    python make_config_1_2.py [--anchors outputs/<run>/results.json]
"""
import argparse
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
NAN = float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default=None)
    a = ap.parse_args()
    cfg = yaml.safe_load((HERE / "configs" / "nh3_final_1_1_reference.yaml").read_text(encoding="utf-8"))
    cal = json.loads((HERE / "calibration_comparison.json").read_text(encoding="utf-8"))["variants"]["v1_2"]
    cfg["project"]["model_version"] = "NH3-FINAL-1.2"
    cfg["project"]["run_label"] = "nh3_final_1_2"
    cfg["project"]["scientific_scope"] = (
        "NH3-FINAL-1.1 on one experimental thermodynamic basis: NH3 formation free energy from the Gillespie-Beattie "
        "equilibrium constant and Newton-Cooper fugacity coefficients for N2, H2 and NH3, used alike in the loop "
        "equilibrium and in the microkinetic gas activities; fused-iron calibration redone on its 1.1 definition. "
        "Workbook, scaling relations, process grid, economics, bed cap and uncertainty settings are those of 1.1.")
    cfg["inputs"]["activity_workbook"] = "inputs/ammonia_activity_volcano_s1_v1.xlsx"  # copy of the 1.1 workbook (same SHA-256)
    cfg["thermo"] = {
        "nh3_formation_reference": "gillespie_beattie",
        "nh3_formation_source": "Gillespie & Beattie, Phys. Rev. 36, 743 (1930); log10 Ka as printed in Rossetti et al., "
                                "Ind. Eng. Chem. Res. 45, 4150 (2006), eq 4",
        "fugacity": "newton_cooper",
        "fugacity_source": "Newton-Cooper correlations (Dyson & Simon, Ind. Eng. Chem. Fundam. 7, 605 (1968)), as printed "
                           "in Rossetti et al. 2006 eqs 5-7",
        "apply_to_loop_equilibrium": True,
        "apply_to_microkinetics": True,
    }
    cfg["economics"]["calibration_factor"] = cal["recalibrated"]["F_CAL"]
    cfg["economics"]["calibration_note"] = (
        "Recalibrated on the NH3-FINAL-1.1 definition: Fe needs the 1.1 Fe bed (66.007 m3) at the calibration state "
        "400 C, 80 bar, -35 C separator (calibrate_and_compare.py); 1.1 value 89806.49638662045.")
    cfg["numerics"]["response_workers"] = 6
    fr = cfg["frozen_regression"]
    if a.anchors:
        res = json.loads((HERE / a.anchors).read_text(encoding="utf-8"))
        d, mc, bk = res["deterministic"], res["monte_carlo"], res["backward_reachability"]
        fr.update(process_state_count=d["process_state_count"], raw_global_spearman=d["raw_global_spearman"],
                  censored_global_spearman=d["censored_global_spearman"], top3_spearman=d["rolling"][0]["rho_raw"],
                  feasible_metals=d["feasible_economic_order"],
                  Fe_feasibility_probability=mc["Fe_feasibility_probability"], **{
                      k: bk[k] for k in ("Ru_activity_break_even_multiplier", "Ru_scaling_max_gain_673K",
                                         "Ru_scaling_max_gain_all_states", "Ru_best_scaling_cost_USD_t")})
        for m in ("Fe", "Ru", "Os"):
            f = d["metals"][m]["feasible"]
            fr[f"{m}_cost_USD_t"] = f["total_cost"]
            fr[f"{m}_optimum"] = {k: f[k] for k in ("T_C", "P_bar", "Tsep_C")}
        fr["_status"] = f"canonical NH3-FINAL-1.2 anchors from the first full run {Path(a.anchors).parent.name}"
        cfg["gates"]["fail_on_regression"] = True
    else:
        for k in list(fr):
            if not k.startswith("_") and k != "feasible_metals":
                fr[k] = {kk: NAN for kk in fr[k]} if isinstance(fr[k], dict) else NAN
        fr["_status"] = "NH3-FINAL-1.2 candidate: anchors not yet set (first full run)"
        cfg["gates"]["fail_on_regression"] = False
    (HERE / "configs" / "nh3_final_1_2.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
                                                         encoding="utf-8")
    print("wrote configs/nh3_final_1_2.yaml; F_CAL", cfg["economics"]["calibration_factor"])


if __name__ == "__main__":
    main()
