"""Quantify what the frozen 90-bar Fe/Ru comparator does and does NOT validate.

The original NH3-FINAL-1.1 model treats Fe or Ru as an entire independent
catalyst bed in a lumped 14,136-state process approximation. Published KAAP-
style reactor designs couple Fe upstream and Ru downstream with intercooling.
This script reports SAME-MASK mono-metal volume/TOF feasibility and activity
de-rating counterfactuals. It must NEVER claim to simulate serial Fe+Ru beds.

All Fe/Ru finance uses the existing merged 25-year, 12% project DCF, and
the supplier-owned Ru contract anchors come from the previous cloud output.
No paper figure or frozen parameter is overwritten.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("NH3_HARNESS", "/tmp/nh3_harness"))
RUN = ROOT / "outputs" / "nh3_final_20260905T134204Z"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import harness_core as hc
from lifecycle_cashflow import MetalCashflow, annualized_metal_multiplier
from kaap_feasibility_math import (classify_feasibility, minimum_feasible_activity_multiplier,
                                   find_fe_activity_cost_parity)

FE_ALPHA = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0)
CAPACITY_SCALE = (0.5, 0.75, 1.0, 1.25, 1.5)
CONTRACTS = ("owned_ideal", "lease_rent_0pct", "lease_rent_1pct",
             "lease_rent_2pct", "lease_rent_2pct_secured",
             "consign_cycle_fee_1pct", "consign_cycle_fee_2pct")
SOURCE_ARTICLES = [
    "https://doi.org/10.1016/j.jiec.2018.05.027",
    "https://pubs.rsc.org/en/content/articlehtml/2024/se/d4se00254g",
]


def save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    h=hc.NH3Harness(yaml.safe_load((RUN/"manifest_resolved.yaml").read_text(encoding="utf-8")),ROOT)
    grid, _, cache=h.build_or_load_response()
    if not cache or h.NSTATE!=14136:
        raise AssertionError("Only frozen cached state response permitted")
    if abs(h.DISCOUNT_RATE-.12)>1e-12 or h.PLANT_LIFE_Y!=25:
        raise AssertionError("Finance drift")
    if abs(h.V_CAP-90)>1e-12:
        raise AssertionError("Frozen catalyst-bed volume cap drift")
    if not math.isfinite(h.PLANT_TPD) or h.PLANT_TPD<=0:
        raise AssertionError("Invalid frozen NH3 capacity")
    fe=h.interp_state_vector(grid,hc.EN0_CANON["Fe"])
    if not np.isfinite(fe).all():
        raise AssertionError("Fe TOF data not finite")
    fe_full, fe_volume_1, fe_metal_1, _=h.cost_arrays("Fe",fe,recovery=0.0)
    kaap=(h.state_P==90.0)&(h.state_Tsep==-20.0)
    masks={"main":np.ones(h.NSTATE,dtype=bool),"KAAP":kaap}
    if not np.any(kaap):
        raise AssertionError("No 90-bar and -20C KAAP mask")
    fe_factor=annualized_metal_multiplier(
        MetalCashflow(float(h.PLANT_LIFE_Y),float(h.CATALYST_LIFE_Y),
                      float(h.DISCOUNT_RATE),0.0),
        hc.PRICE["Fe"],float(h.CATALYST_LIFE_Y))

    def calculate_fe(loop, alpha, cap_factor):
        if alpha<=0 or cap_factor<=0 or not (math.isfinite(alpha) and math.isfinite(cap_factor)):
            raise ValueError("alpha and cap_factor positive and finite")
        vol=fe_volume_1/alpha
        metal=fe_metal_1/alpha*fe_factor
        reactor=((h.REACTOR_FIXED+
                  h.REACTOR_VAR*np.power(vol/h.REACTOR_REF,h.REACTOR_EXP))
                 *h.crf/h.annual_output_t+h.vessel_pressure_premium(vol))
        valid=masks[loop]&(vol <= h.V_CAP*cap_factor)
        eligible=int(np.count_nonzero(valid))
        if eligible==0:
            return None
        cost=metal+reactor+h.state_process_cost
        idx=int(np.argmin(np.where(valid,cost,np.inf)))
        return {
            "Fe_cost_USD_t":float(cost[idx]), "Fe_metal_USD_t":float(metal[idx]),
            "Fe_reactor_USD_t":float(reactor[idx]),
            "Fe_process_USD_t":float(h.state_process_cost[idx]),
            "Fe_bed_volume_m3":float(vol[idx]),
            "Fe_bed_volume_margin_m3":float(h.V_CAP*cap_factor-vol[idx]),
            "Fe_bed_capacity_fraction":float(vol[idx]/(h.V_CAP*cap_factor)),
            "Fe_opt_T_C":float(h.state_T[idx]), "Fe_opt_P_bar":float(h.state_P[idx]),
            "Fe_opt_Tsep_C":float(h.state_Tsep[idx]),
            "Fe_frozen_log10_TOF":float(fe[idx]),
            "n_Fe_volume_feasible_states":eligible,
            "Fe_state_index":idx,
        }

    with (HERE/"contract_terms_report.json").open(encoding="utf-8") as file:
        contract_report=json.load(file)
    anchor=contract_report["anchor"]
    fe_kaap_ref=float(contract_report["Fe_cost_USD_t"]["KAAP"])
    fe_main_ref=float(contract_report["Fe_cost_USD_t"]["main"])
    for loop,expected in (("main",fe_main_ref),("KAAP",fe_kaap_ref)):
        nominal=calculate_fe(loop,1.0,1.0)
        if nominal is None or abs(nominal["Fe_cost_USD_t"]-expected)>1e-9:
            raise AssertionError(f"Canonical DCF Fe cost under {loop} changed")

    # Reference diagnostics give two explicitly distinct volume metrics:
    # min_volume over T options and volume at minimum-cost solution.
    original_volume_diagnostics={}
    for loop, mask in masks.items():
        subset=fe_volume_1[mask]
        imin=int(np.argmin(np.where(mask,fe_volume_1,np.inf)))
        orig=calculate_fe(loop,1.0,1.0)
        original_volume_diagnostics[loop]={
            "n_process_states":int(np.count_nonzero(mask)),
            "min_required_Fe_bed_volume_m3":float(fe_volume_1[imin]),
            "min_volume_state_T_C":float(h.state_T[imin]),
            "min_volume_state_P_bar":float(h.state_P[imin]),
            "frozen_bed_cap_m3":float(h.V_CAP),
            "min_activity_factor_for_volume_feasibility":
                minimum_feasible_activity_multiplier(float(fe_volume_1[imin]),float(h.V_CAP)),
            "nominal_opt_Fe_cost_USD_t":orig["Fe_cost_USD_t"],
            "nominal_opt_Fe_volume_m3":orig["Fe_bed_volume_m3"],
            "nominal_feasible_volume_margin_m3":orig["Fe_bed_volume_margin_m3"],
            "nominal_best_Fe_T_C":orig["Fe_opt_T_C"],
            "nominal_count_feasible_states":orig["n_Fe_volume_feasible_states"],
            "engineering_validation_status":"UNVALIDATED -- isothermal whole-bed model only",
        }

    curves=[]
    comparisons=[]
    for loop in ("main","KAAP"):
        for cap_factor in CAPACITY_SCALE:
            for alpha in FE_ALPHA:
                result=calculate_fe(loop,alpha,cap_factor)
                curves.append({
                    "loop":loop,"Fe_relative_TOF_effectiveness":alpha,
                    "assumed_Fe_bed_cap_multiplier":cap_factor,
                    "assumed_bed_capacity_m3":h.V_CAP*cap_factor,
                    "Fe_model_volume_feasible":result is not None,
                    "Fe_feasibility_status":classify_feasibility(
                        (result["Fe_bed_volume_m3"] if result is not None else math.inf),
                        h.V_CAP*cap_factor),
                    **({k:"" for k in ("Fe_cost_USD_t","Fe_metal_USD_t","Fe_reactor_USD_t",
                        "Fe_process_USD_t","Fe_bed_volume_m3","Fe_bed_volume_margin_m3",
                        "Fe_bed_capacity_fraction","Fe_opt_T_C","Fe_opt_P_bar",
                        "Fe_opt_Tsep_C","Fe_frozen_log10_TOF",
                        "n_Fe_volume_feasible_states","Fe_state_index")} if result is None else result)
                })
                if loop=="KAAP":
                    for mode in CONTRACTS:
                        ru_cost=float(anchor[mode]["Ru_USD_t"])
                        gap=(ru_cost-result["Fe_cost_USD_t"]) if result is not None else None
                        comparisons.append({
                            "Ru_contract":mode,
                            "Fe_relative_TOF_effectiveness":alpha,
                            "Fe_assumed_cap_multiplier":cap_factor,
                            "Fe_volume_model_feasible":result is not None,
                            "Ru_cost_USD_t":ru_cost,
                            "Fe_cost_USD_t":"" if result is None else result["Fe_cost_USD_t"],
                            "Ru_minus_Fe_USD_t":"" if gap is None else gap,
                            "preferred_if_Fe_model_feasible":(
                                "Fe_not_volume_feasible_do_not_rank" if gap is None
                                else "Ru" if gap<-1e-9 else "Fe" if gap>1e-9 else "tie"
                            )
                        })
    save_csv(HERE/"kaap_fe_volume_alpha_sweep.csv",curves)
    save_csv(HERE/"kaap_fe_contract_contingency.csv",comparisons)
    if len(curves)!=2*len(CAPACITY_SCALE)*len(FE_ALPHA):
        raise AssertionError("Fe alpha/bed-capacity sweep omitted states")
    if len(comparisons)!=len(CAPACITY_SCALE)*len(FE_ALPHA)*len(CONTRACTS):
        raise AssertionError("contract contingency coverage drift")

    alpha_thresholds=[]
    for cap_factor in CAPACITY_SCALE:
        min_fe_alpha=(original_volume_diagnostics["KAAP"]["min_required_Fe_bed_volume_m3"] /
                      (h.V_CAP*cap_factor))
        def f(alpha):
            result=calculate_fe("KAAP",alpha,cap_factor)
            if result is None:
                raise ValueError("Called Fe objective below geometric feasibility")
            return result["Fe_cost_USD_t"]
        for mode in CONTRACTS:
            ru_cost=float(anchor[mode]["Ru_USD_t"])
            decision=find_fe_activity_cost_parity(
                f,ru_cost,lowest_feasible_alpha=min_fe_alpha,
                low=.2,high=4.0)
            alpha_thresholds.append({
                "Ru_contract":mode,"Fe_cap_multiplier":cap_factor,
                "Fe_volume_threshold_alpha":min_fe_alpha,
                "status":decision["status"],
                "Fe_activity_multiplier_at_Ru_Fe_cost_parity":
                    "" if decision["alpha"] is None else decision["alpha"],
                "parity_residual_USD_t":
                    decision.get("gap_residual_USD_t",""),
                "Ru_reference_USD_t":ru_cost,
                "status_warning":"Only a frozen-kinetic activity-and-volume sensitivity; no serial-bed process model",
            })
    save_csv(HERE/"kaap_fe_effectiveness_parity.csv",alpha_thresholds)
    assert len(alpha_thresholds)==len(CAPACITY_SCALE)*len(CONTRACTS)

    # The source literature explicitly describes Fe upfront + Ru downstream.
    # This flag must remain FAIL for any claim of a validated mixed-bed KAAP TEA.
    report={
        "scope":"FEASIBILITY SCREEN ONLY, not validated industrial KAAP converter design",
        "status":"read-only frozen model counterfactual; industrial mixed-bed claim BLOCKED",
        "science_response_unchanged":True,
        "n_frozen_states":h.NSTATE,
        "modeled_mask":{"pressure_bar":90.0,"separator_temperature_C":-20.0,
                        "reactor_temperature_C":"discrete frozen optimum",
                        "single_metal_bed":True,
                        "serial_Fe_then_Ru_reactor_implemented":False},
        "source_literature_hybrid":{"author_year":"Tripodi et al. (2018)",
                                   "doi":"10.1016/j.jiec.2018.05.027",
                                   "finding":"Validated kinetic/process simulations used Fe-based upstream beds followed by Ru/C for increased NH3 productivity",
                                   "other_source":"RSC 2024 DOI 10.1039/D4SE00254G; commercial process Ru rear multistage",
                                   "exact_industrial_bed_split":"not established or assumed in frozen model"},
        "Fe_nominal_model_diagnostics":original_volume_diagnostics,
        "n_fe_sweep_rows":len(curves),
        "n_fe_contract_contingencies":len(comparisons),
        "n_fe_cost_parity_cases":len(alpha_thresholds),
        "n_Fe_infeasible_states_in_alpha_cap_sweep":sum(not x["Fe_model_volume_feasible"] for x in curves),
        "n_KAAP_feasible_comparisons":sum(x["Fe_volume_model_feasible"] for x in comparisons),
        "n_KAAP_feasible_Ru_better_than_Fe":sum(x["preferred_if_Fe_model_feasible"]=="Ru" for x in comparisons),
        "baseline_FE_vs_RU_from_contract_DCF":{
            "Fe_KAAP_cost_USD_t":fe_kaap_ref,
            "Ru_annual_1percent_lease_USD_t":float(anchor["lease_rent_1pct"]["Ru_USD_t"]),
            "Ru_annual_0percent_lease_USD_t":float(anchor["lease_rent_0pct"]["Ru_USD_t"]),
            "Fe_nominal_KAAP_bed_capacity_fraction":
                original_volume_diagnostics["KAAP"]["nominal_opt_Fe_volume_m3"]/h.V_CAP,
        },
        "missing_physical_evidence":[
            "Fe/Cu? site-dependent true rate constant and Fe particle morphology at KAAP pressure/composition",
            "adiabatic multibed plug-flow conversion, gas phase compositions and intercooling",
            "Ru inlet after Fe stages, NH3 inhibition of Fe vs Ru, H2 inhibition on Ru",
            "actual KBR installation bed distributions, pressure drop and size at equal annual NH3 capacity",
            "actual Ru/C promoter, deactivation, metal recoverability and lease terms",
        ],
        "editorial_gate":{
            "same_mask_Fe_vs_Ru_comparison":"ACCEPTABLE AS A MODEL CONDITIONAL COUNTERFACTUAL",
            "Fe_retrofit_at_90bar_is_industrially_verified":False,
            "full_multibed_KAAP_process_economics_is_verified":False,
            "may_replace_frozen_manuscript_claims":False,
        }
    }
    (HERE/"kaap_feasibility_gate_report.json").write_text(
        json.dumps(report,ensure_ascii=False,allow_nan=False,indent=2)+"\n",encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11.2,4.5),constrained_layout=True)
    for multiplier in CAPACITY_SCALE:
        p=[x for x in curves if x["loop"]=="KAAP" and
           x["assumed_Fe_bed_cap_multiplier"]==multiplier]
        axes[0].plot([x["Fe_relative_TOF_effectiveness"] for x in p],
                     [float(x["Fe_cost_USD_t"]) if x["Fe_model_volume_feasible"] else np.nan
                      for x in p],marker="o",label=f"Vcap x{multiplier:g}")
    axes[0].axhline(fe_kaap_ref,linestyle=":",label="Nominal Fe DCF")
    axes[0].set_xlabel("Fe effective TOF multiplier (unmeasured counterfactual)")
    axes[0].set_ylabel("Fe same-mask cost (USD/t NH3)")
    axes[0].set_title("(a) Fe model-only 90-bar capacity sensitivity")
    axes[0].legend(fontsize=7)
    axes[0].grid(alpha=.2)

    p=[x for x in curves if x["loop"]=="KAAP" and
       x["assumed_Fe_bed_cap_multiplier"]==1.0]
    alpha=[x["Fe_relative_TOF_effectiveness"] for x in p]
    fe_costs=[float(x["Fe_cost_USD_t"]) if x["Fe_model_volume_feasible"] else np.nan
              for x in p]
    axes[1].plot(alpha,fe_costs,marker="o",label="Fe same 90-bar mask")
    for mode,label in (("owned_ideal","Ru owned"),
                       ("lease_rent_0pct","Ru supplier-owned, 0% annual fee"),
                       ("lease_rent_1pct","Ru supplier-owned, 1% annual fee"),
                       ("consign_cycle_fee_2pct","Ru consignment, 2% cycle fee")):
        axes[1].axhline(float(anchor[mode]["Ru_USD_t"]),linewidth=1.3,label=label)
    axes[1].set_xlabel("Fe effective TOF multiplier (unmeasured counterfactual)")
    axes[1].set_ylabel("Ru/Fe same-mask cost (USD/t NH3)")
    axes[1].set_title("(b) Financial contract vs Fe-activity uncertainty")
    axes[1].legend(fontsize=7)
    axes[1].grid(alpha=.2)
    fig.suptitle("NOT a multibed KAAP simulation: Fe volume-limited whole-bed surrogate",
                 fontsize=11)
    fig.savefig(HERE/"kaap_fe_model_feasibility_gate.png",dpi=200)
    plt.close(fig)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
