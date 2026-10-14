#!/usr/bin/env python3
"""Zero-refit PR78 EOS external benchmark and Figure57 source conditional checks.

CI PASS means mathematical/source-provenance and deterministic result generation.
A scientific acceptance criterion failing MUST BE REPORTED as FAIL, not hidden
as an exception or "fixed" by choosing k_ij on the validation targets.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"analysis"/"nh3_industrial_validation_2026_10_14"))
sys.path.insert(0,str(ROOT/"analysis"/"nh3_source_matched_loop_v0"))
from diagnose_separator_vle import grid_from_printed_sources
from species_reconstruct import load_streams
from thermo_pr import (
    COMPONENTS, eos_phase, saturated_vapor_over_pure_liquid_nh3,
    flash_isothermal_isobaric_no_kij, isothermal_compression_work
)

ACCEPTANCE={
    "BASF_TABLE_ABS_REL_MAX":0.20,
    "BASF_TABLE_REQUIRE_WITHIN_BAND":24,   # minimum 24/28, declared before evaluating model
    "PLANT_STAGE_ABS_REL_MAX":0.20,
    "PLANT_STAGE_REQUIRE_WITHIN_BAND":2,   # both 5 & 6 under source composition
}
SCIENCE_MODEL="PR78_ZERO_KIJ_SATURATED_PURE_NH3_LIQUID_SCREEN_V0"
COMPRESSOR_METHOD="SOURCED_BOUNDARY_PR78_Z_FIXED_T_ISOTHERMAL_REFERENCE"


def relative_error(pred,ref):
    if ref<=0 or not math.isfinite(pred):
        raise ValueError("Invalid source comparison value")
    return (pred-ref)/ref


def dry_ratio(stream):
    other={j:stream["y"][j] for j in COMPONENTS if j!="NH3"}
    return other


def report_saturation()->tuple[list[dict],dict,list[dict]]:
    grid=grid_from_printed_sources()
    tab=[]
    for (T_C,P_MPa),source in sorted(grid.items()):
        pred=saturated_vapor_over_pure_liquid_nh3(
            T_C+273.15,P_MPa*1e6,{"N2":1.0,"H2":3.0}
        )
        y=pred["y_NH3_molpct"]
        obs=source["source_y_pct"]
        err=relative_error(y,obs)
        baseline=source["model_psat_P_pct"]
        tab.append({
            "reference_row":source["row_id"],
            "T_C":T_C,"P_MPa":P_MPa,
            "BASF_NH3_molpct":obs,
            "PR78_no_kij_pure_liquid_NH3_molpct":y,
            "PR78_abs_relative_error_pct":abs(100*err),
            "PR78_signed_relative_error_pct":100*err,
            "PR78_within_20pct":abs(err)<=ACCEPTANCE["BASF_TABLE_ABS_REL_MAX"],
            "canonical_psat_P_pct":baseline,
            "canonical_abs_relative_error_pct":abs(100*relative_error(baseline,obs)),
            "model_scope":SCIENCE_MODEL
        })
    if len(tab)!=28:
        raise AssertionError("The immutable BASF reference must contain 28 entries")
    st=load_streams()
    plants=[]
    for k,upstream in ((5,4),(6,1)):
        source=st[k]
        feed=st[upstream]
        # Upstream feed dry fractions are input; source NH3 in outlet is
        # deliberately withheld from model input until post-prediction scoring.
        pred=saturated_vapor_over_pure_liquid_nh3(
            source["T_C"]+273.15,source["P_MPa"]*1e6,dry_ratio(feed)
        )
        obs=100.0*source["y"]["NH3"]
        err=relative_error(pred["y_NH3_molpct"],obs)
        plants.append({
            "observed_gas_stream":k,
            "dry_composition_from_stream":upstream,
            "dry_composition_is_source_conditioned":True,
            "dry_gas_definition":"non-NH3 fractions normalized from measured source upstream gas",
            "separator_T_C":source["T_C"],
            "separator_P_bar":source["P_MPa"]*10,
            "published_NH3_molpct":obs,
            "PR78_NH3_molpct":pred["y_NH3_molpct"],
            "PR78_abs_relative_error_pct":abs(100*err),
            "within_20pct":abs(err)<=ACCEPTANCE["PLANT_STAGE_ABS_REL_MAX"],
            "fugacity_relative_residual":
                abs(pred["vapor_fugacity_PR_Pa"]/pred["liquid_fugacity_PR_Pa"]-1.0),
            "source_status":"SOURCE_CONDITIONED_HOLDOUT_NH3_ONLY__NOT_FULLY_INDEPENDENT",
        })
    ok28=sum(int(x["PR78_within_20pct"]) for x in tab)
    ok_plant=sum(int(x["within_20pct"]) for x in plants)
    summary={
        "n_BASF_source_points":len(tab),
        "n_BASF_under_20pct":ok28,
        "n_BASF_over_20pct":len(tab)-ok28,
        "BASF_mean_abs_relative_pct":sum(x["PR78_abs_relative_error_pct"] for x in tab)/28,
        "BASF_median_abs_relative_pct":sorted(x["PR78_abs_relative_error_pct"] for x in tab)[14],
        "BASF_max_abs_relative_pct":max(x["PR78_abs_relative_error_pct"] for x in tab),
        "canonical_psat_P_mean_abs_relative_pct":
            sum(x["canonical_abs_relative_error_pct"] for x in tab)/28,
        "n_plant_stage_under_20pct":ok_plant,
        "n_plant_stage":2,
        "predeclared_science_gate":ACCEPTANCE,
        "gate_BASF_pass":ok28>=ACCEPTANCE["BASF_TABLE_REQUIRE_WITHIN_BAND"],
        "gate_plant_pass":ok_plant>=ACCEPTANCE["PLANT_STAGE_REQUIRE_WITHIN_BAND"],
        "science_gate_verdict":"PENDING",
        "binary_interaction": "kij=0 all 10 pairs (explicit unvalidated no-fit default)",
        "origin_of_critical_data":"CoolProp 8.0 public fluid pages; no industry case parameters fitted",
        "status":"MODEL_SCREENING_NOT_PRODUCTION_APPROVED",
    }
    summary["science_gate_verdict"]=(
        "PASS_EXTERNAL_SCREEN_ONLY"
        if summary["gate_BASF_pass"] and summary["gate_plant_pass"]
        else "FAIL__DO_NOT_PROMOTE_MODEL")
    return tab,summary,plants


def first_separator_flash_source_only()->dict:
    st=load_streams()
    feed=st[4]       # composition/flow known *before* the first separator
    firstgas=st[5]   # strictly held out from TP flash input
    firstliquid=st[7]
    t=firstgas["T_C"]+273.15
    P=firstgas["P_MPa"]*1e6
    candidate=flash_isothermal_isobaric_no_kij(t,P,feed["y"])
    output={
        "fixed_industrial_feed_stream":4,"observed_vapor_stream":5,
        "observed_liquid_stream":7,
        "feed_NH3_molpct":100*feed["y"]["NH3"],
        "observed_vapor_NH3_molpct":100*firstgas["y"]["NH3"],
        "observed_liquid_NH3_molpct":100*firstliquid["y"]["NH3"],
        "observed_vapor_fraction":firstgas["flow_kmol_h"]/feed["flow_kmol_h"],
        "model": "NO_FIT_PR78_KIJ_ZERO_TWO_PHASE_TP_FLASH",
        "uses_observed_phase_values_to_predict":False,
        "method_warning":"PR78 zero binary interactions lacks high-pressure mixture stability/BIP evidence",
        "flash_status":candidate["status"],
        "full_candidate":candidate,
    }
    if candidate.get("screening_accepted"):
        beta=candidate["beta_vapor"]
        yp=candidate["vapor_y"]["NH3"]*100
        xp=candidate["liquid_x"]["NH3"]*100
        out_pred=feed["flow_kmol_h"]*beta
        liquid_pred=feed["flow_kmol_h"]*(1.0-beta)
        output.update({
            "predicted_vapor_NH3_molpct":yp,
            "predicted_liquid_NH3_molpct":xp,
            "predicted_vapor_kmol_h":out_pred,
            "predicted_liquid_kmol_h":liquid_pred,
            "vapor_composition_abs_relative_error_pct":
                100*abs(relative_error(yp,100*firstgas["y"]["NH3"])),
            "observed_liquid_kmol_h":firstliquid["flow_kmol_h"],
            "vapor_fraction_relative_error_pct":
                100*abs(relative_error(beta,output["observed_vapor_fraction"])),
            "flash_fugacity_residual_max":candidate["fugacity_log_ratio_error_max"],
        })
    return output


def source_conditioned_compression()->dict:
    st=load_streams()
    cases=[
        # Source station p10 raw syngas compression to source stream12 delivered P.
        ("raw_makeup_10_to_12",10,12),
        # Returned recovered hydrogen stream11 has a *distinct* source suction state.
        ("recovered_H2_11_to_12",11,12),
        # Source stream6 cold recycle gas to converter inlet stream1 total pressure
        # rise, which may span multiple equipment units/heat exchanges.
        ("cold_recycle_6_to_1",6,1),
    ]
    output={}
    for name,a,b in cases:
        src,dst=st[a],st[b]
        v=isothermal_compression_work(
            src["T_C"]+273.15,src["P_MPa"]*1e6,dst["P_MPa"]*1e6,
            src["flow_kmol_h"],src["y"]
        )
        output[name]=v
        output[name]["source_inlet_stream"]=a
        output[name]["source_destination_stream"]=b
        output[name]["source_temperature_assumption"]="isothermal at inlet source T; actual compressor stages and cooling unmeasured"
    total=sum(output[n]["PR_isothermal_reversible_MW"] for n in output)
    ideal_total=sum(output[n]["ideal_gas_isothermal_reversible_MW"] for n in output)
    return {
        "per_boundary":output,
        "separate_makeup_plus_cold_recycle_PR_isothermal_MW":total,
        "separate_makeup_plus_cold_recycle_ideal_isothermal_MW":ideal_total,
        "scenario_shaft_power_at_eta_0p65_to_0p85_MW":
            [total/0.85,total/0.65],
        "eta_scenarios_not_from_source":"0.65 and 0.85 are illustrative, not claimed compressor source efficiencies",
        "engineering_equipment_validation":"BLOCKED_MISSING_STAGE_THERMAL_PATH_AND_MANUFACTURER_COMPRESSOR_CURVE",
        "comparison_to_E01_external_13MW":"NOT_COMPARABLE__E01_SOURCE_IS_DIFFERENT_INDUSTRIAL_INSTALLATION",
        "model":COMPRESSOR_METHOD
    }


def write_csv(path,records):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def run(outdir:Path)->dict:
    tab,summary,plant=report_saturation()
    flash=first_separator_flash_source_only()
    compressor=source_conditioned_compression()
    outdir.mkdir(parents=True,exist_ok=True)
    write_csv(outdir/"BASF_28_PR_no_fit.csv",tab)
    write_csv(outdir/"uhde_2_sep_PR_no_fit.csv",plant)
    (outdir/"source_first_sep_TP_flash.json").write_text(json.dumps(flash,indent=2)+"\n",encoding="utf-8")
    (outdir/"source_compression_Z_integral.json").write_text(json.dumps(compressor,indent=2)+"\n",encoding="utf-8")
    overview={
        "phase_validation":summary,
        "plant_stage_NH3_conditional":plant,
        "first_separator_TP_flash":flash,
        "source_compression":compressor,
        "baseline_catalyst_model_unchanged":"NH3-FINAL-1.2 32/64; Fe/Ru/Os costs not recomputed",
        "scientific_validation_state":"PR screening can FAIL even if CI passes; no false promotion",
    }
    (outdir/"summary.json").write_text(json.dumps(overview,indent=2)+"\n",encoding="utf-8")
    lines=[
        "# NH3-PR-SCREEN-V0 | High-pressure VLE and compression without fitting",
        "",
        "**Scientific validation verdict: "+summary["science_gate_verdict"]+"**",
        "",
        "Fixed model: Peng–Robinson 1976, all k_ij=0, pure NH3 liquid approximation for saturated vapor; "
        "CoolProp critical properties, no fitted parameter or industrial-performance calibration.",
        "",
        "## BASF 28 printed high-pressure NH3 saturation references (3:1 H2:N2)",
        "",
        f"- PR predicted within ±20%: **{summary['n_BASF_under_20pct']}/28**; "
        f"mean absolute relative error **{summary['BASF_mean_abs_relative_pct']:.1f}%**, "
        f"maximum **{summary['BASF_max_abs_relative_pct']:.1f}%**.",
        f"- Original ideal p_sat/P basis mean absolute relative error **{summary['canonical_psat_P_mean_abs_relative_pct']:.1f}%**.",
        f"- Predeclared external screen needs ≥{ACCEPTANCE['BASF_TABLE_REQUIRE_WITHIN_BAND']}/28 BASF cases "
        f"and both industrial stage vapor NH3 predictions within 20%, without using their results to tune k_ij.",
        "",
        "## Two industrial stages: no-fit, source-conditioned dry-gas mixture",
        "",
        "| Gas | T (C) | P (bar) | Observed NH3 (%) | PR saturation NH3 (%) | Abs. relative error |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for v in plant:
        lines.append(
            f"| {v['observed_gas_stream']} | {v['separator_T_C']:.1f} | "
            f"{v['separator_P_bar']:.1f} | {v['published_NH3_molpct']:.3f} | "
            f"{v['PR78_NH3_molpct']:.3f} | {v['PR78_abs_relative_error_pct']:.1f}% |"
        )
    lines +=[
        "",
        "## Full five-component feed-to-first-separator flash (no source gas/liq outputs used as input)",
        "",
        f"PR phi-phi flash status: **{flash['flash_status']}**. "
        "Output predictions and differences are in source_first_sep_TP_flash.json. "
        "A single liquid/vapor PR root computation does not constitute rigorous phase-stability verification.",
        "",
        "## Source-aligned compression references",
        "",
        f"Mixture-PR fixed-T reversible work sum **{compressor['separate_makeup_plus_cold_recycle_PR_isothermal_MW']:.3f} MW** "
        f"across raw makeup 10→12, recovered H2 11→12 and cold recycle 6→1; "
        f"ideal-gas reference **{compressor['separate_makeup_plus_cold_recycle_ideal_isothermal_MW']:.3f} MW**.",
        "These source end points are not independently resolved compressor casing locations. "
        "A real measured shaft duty requires efficiency/staging/intercooling, the correct mechanical boundary "
        "and gas-pressure-loss breakdown. The E01 13 MW benchmark is a DIFFERENT plant and MUST NOT be used "
        "as the Uhde measured compressor power.",
        "",
        "## Decision",
        "",
        "The frozen published Fe/Ru/Os costs and 32/64 source benchmark are unchanged. "
        "A failed PR physics gate blocks promotion to a new catalyst cost/ranking calculation. "
        "No target was fitted and no result was relabeled to pass.",
        ""
    ]
    report="\n".join(lines)
    (outdir/"REPORT.md").write_text(report,encoding="utf-8")
    print(report)
    return overview


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()
    run(a.out_dir)
