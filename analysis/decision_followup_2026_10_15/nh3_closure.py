#!/usr/bin/env python3
"""Independent join of freshly rerun, provenance-pinned industrial diagnostics. No fitting."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

TABLES={"A":(28,18),"B":(20,5),"C":(12,9),"E":(3,0),"V":(1,0)}
INLET_IDS={"A01","A04","A07","A14","A16"}


def require(cond, msg):
    if not cond:
        raise AssertionError(msg)


def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def load_csv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def save_csv(p, records):
    records=list(records)
    require(len(records)>0,f"empty output: {p}")
    with p.open("w",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f, fieldnames=list(records[0]))
        wr.writeheader()
        wr.writerows(records)


def number(v):
    value=float(v)
    require(math.isfinite(value),f"nonfinite number: {v}")
    return value


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sources",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    src=args.sources.resolve()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)

    audit=load_json(src/"audit"/"summary.json")
    require(audit["rescore_model"].endswith("32/64, unchanged"),"registered score changed")
    for k,(n,ok) in TABLES.items():
        z=audit["by_table"][k]
        require((z["n"],z["pass"])==(n,ok),f"industrial registration changed {k}")
    require(audit["unresolved"]==32,"registered failures changed")
    cases=load_csv(src/"audit"/"triage_64.csv")
    require(len(cases)==64 and len({x["metric_id"] for x in cases})==64,"provenance metric count")
    ids={x["metric_id"]:x for x in cases}
    require(all(ids[k]["unchanged_verdict"]=="FAIL" for k in INLET_IDS),"original inlets ceased to fail")

    vle=load_json(src/"vle"/"summary.json")
    require(vle["reference_thermo"]["n_table_entries"]==28,"VLE external table count drift")
    require(vle["reference_thermo"]["constant_multiplicative_correction_within_20pct_possible"] is False,
        "single multiplier VLE claim changed")
    s=load_csv(src/"vle"/"saturation_28.csv")
    require(len(s)==28 and len({(r["T_C"],r["P_MPa"]) for r in s})==28,"VLE table integrity")
    original=load_csv(src/"vle"/"conditional_model_inlet_5.csv")
    required=load_csv(src/"inverse"/"required_separator_5.csv")
    proxy=load_csv(src/"vle"/"plant_inlet_proxy_5.csv")
    require(len(original)==len(required)==len(proxy)==5,"five source inlets not reproduced")
    model_by={r["metric_id"]:r for r in original}
    req_by={r["metric_id"]:r for r in required}
    proxy_by={r["metric_id"]:r for r in proxy}
    require(set(model_by)==set(req_by)==set(proxy_by)==INLET_IDS,"source case IDs differ")

    joined=[]
    for mid in sorted(INLET_IDS):
        o,q,p = model_by[mid],req_by[mid],proxy_by[mid]
        case=o["case_id"]
        require(case==q["case_id"]==p["case_id"],f"source case join error {mid}")
        obs=number(o["plant_reported_inlet_pct"])
        orig=number(o["baseline_model_inlet_pct"])
        source=number(o["source_vapor_input_pct"])
        basf=number(q["BASF_separator_proxy_pct"])
        require(abs(source-basf)<1e-6,"BASF input mismatch")
        cf=number(o["counterfactual_model_inlet_pct"])
        target=number(q["target_reactor_inlet_pct"])
        inv=number(q["required_separator_pct"])
        require(abs(obs-target)<1e-9,"inverse source differs")
        require(abs(number(q["loop_inlet_with_BASF_separator_pct"])-cf)<1e-6,
            "counterfactual and inverse model closures disagree")
        joined.append(dict(metric_id=mid,case_id=case,plant_inlet_pct=obs,
            baseline_model_inlet_pct=orig,BASF_1to3_vapor_pct=basf,
            model_inlet_with_only_BASF_pct=cf,
            conditional_BASF_within_20pct=int(abs(cf/obs-1)<=.2),
            inverse_required_separator_pct=inv,
            inverse_required_over_BASF=inv/basf,
            baseline_rel_error=orig/obs-1,
            conditional_rel_error=cf/obs-1,
            inverse_is_model_target_fit=True,
            caveat="BASF 1:3 N2/H2 vapor != industrial inlet mixture/topology"))
    require(sum(z["conditional_BASF_within_20pct"] for z in joined)==1,
        "source VLE conditional 1/5 status changed")
    require(all(r["inverse_required_over_BASF"]>1 for r in joined),
        "inverse vapor requirement no longer exceeds 1:3 BASF comparator")
    save_csv(out/"01_five_inlet_joint_closure.csv",joined)

    flows=load_csv(src/"flow"/"source_mass_balance_bounds_3.csv")
    require(len(flows)==3 and {r["case_id"] for r in flows}=={"TOP140","TOP220","UHDE188"},
            "source-only 3-plant flow comparator changed")
    bycase={r["case_id"]:r for r in joined}
    flowout=[]
    for r in flows:
        case=r["case_id"];j=bycase[case]
        measured=number(r["source_inlet_NH3_molpct"])
        require(abs(measured-j["plant_inlet_pct"])<1e-9,"plant flow inlet mismatch")
        sep=number(r["BASF_saturated_vapor_pct"])
        require(abs(sep-j["BASF_1to3_vapor_pct"])<1e-6,
                "different source boundaries for named plant: do not combine")
        dil=number(r["optimistic_max_recycle_share"])
        original_limit=number(r["optimistic_max_inlet_NH3_pct"])
        implied=number(r["separator_y_required_at_minimum_makeup_pct"])
        require(abs(implied-measured/dil)<1e-8,"stoichiometric dilution identity")
        require(abs(original_limit-sep*dil)<1e-8,"stoichiometric upper-bound identity")
        flowout.append(dict(case_id=case,source_metric_id=j["metric_id"],
            industrial_inlet_pct=measured,BASF_vapor_pct=sep,
            inlet_flow_Nm3_h=number(r["source_inlet_Nm3_h"]),
            nominal_design_tpd=number(r["source_design_tpd"]),
            minimum_stoich_makeup_Nm3_h=number(r["minimum_stoichiometric_makeup_Nm3_h"]),
            upper_bound_under_one_separator_pct=original_limit,
            observed_over_conditional_upper_bound=measured/original_limit,
            hypothetical_minimum_separator_pct=implied,
            min_separator_over_BASF=implied/sep,
            source_model_inverse_separator_pct=j["inverse_required_separator_pct"],
            scope="one saturated 1:3 source vapor + NH3-free makeup + matched nominal design flow; real plant need not obey"))
    require(all(x["observed_over_conditional_upper_bound"]>1 for x in flowout),
            "one-separator conditional boundary changed")
    save_csv(out/"02_three_source_flow_consistency.csv",flowout)

    beds=load_csv(src/"bed"/"bed_profile_4.csv")
    require(len(beds)==4 and {(z["case"],z["bed"]) for z in beds}
           =={("LIU919A","1"),("LIU919A","2"),("LIU919B","1"),("LIU919B","2")},
           "source-conditioned measured bed count changed")
    ratios=[number(b["required_volume_over_installed"]) for b in beds]
    require(min(ratios)>0 and max(ratios)>1.5 and min(ratios)<1.1,
            "distinct bed profile source discrepancies changed")
    worst_factor=math.sqrt(max(ratios)/min(ratios))
    compromise=math.sqrt(max(ratios)*min(ratios))
    bed_rows=[]
    for b in beds:
        ratio=number(b["required_volume_over_installed"])
        bed_rows.append(dict(case=b["case"],bed=b["bed"],
            source_installed_m3=number(b["installed_m3"]),
            inverse_required_m3=number(b["required_m3_for_printed_heat_rise"]),
            fixed_trajectory_rate_equivalent=ratio,
            common_minimax_rate_multiplier=compromise,
            equivalent_factor_relative_to_common=ratio/compromise,
            source_Tout_C=number(b["source_outlet_T_C"]),
            model_forward_Tout_C=number(b["modeled_forward_Tout_C"]),
            status="Fixed-source-trajectory comparison; not measured catalyst effectiveness"))
    save_csv(out/"03_four_bed_single_multiplier_audit.csv",bed_rows)
    require(worst_factor>1.2,"bed common multiplier artificially reconciled")

    comp=[]
    for mid in ("E01","E02","E03"):
        a=ids[mid]
        m=number(a["model"]);plant=number(a["industrial"])
        require(m>=0 and plant>0 and a["unchanged_verdict"]=="FAIL",f"compressor source {mid}")
        comp.append(dict(metric_id=mid,case_id=a["case_id"],
            unit=a["unit"],model_duty=m,industrial_duty=plant,
            model_to_plant_ratio=m/plant,model_minus_plant=m-plant,
            relative_duty_gap=(plant-m)/plant,provenance_rows=a["source_row_ids"]))
    save_csv(out/"04_three_compression_duties.csv",comp)
    ratio_bound=audit["power_E01_pressure_ratio_only"]
    require(abs(number(ratio_bound["original_model_MW"])-comp[0]["model_duty"])<1e-9,"E01 model boundary")
    require(abs(number(ratio_bound["plant_MW"])-comp[0]["industrial_duty"])<1e-9,"E01 plant boundary")
    corrected=number(ratio_bound["generous_corrected_combined_MW"])
    remainder=number(ratio_bound["plant_MW"])-corrected
    require(remainder>0,"generous correction unexpectedly solves compressor")

    summary=dict(
        status="PROVENANCE_PINNED_CONDITIONAL_AUDIT_NOT_INDUSTRIAL_VALIDATION",
        original_verdict=dict(passes=32,metrics=64,table_breakdown=audit["by_table"]),
        source_mixture_vle=dict(n=28,model_ratio_min=vle["reference_thermo"]["model_to_table_ratio_min"],
            model_ratio_max=vle["reference_thermo"]["model_to_table_ratio_max"],
            universal_20pct_multiplier_possible=False),
        source_plant_inlets=dict(n=5,separator_only_within_20pct=sum(x["conditional_BASF_within_20pct"] for x in joined),
            source_loop_inverse_requires_above_BASF=sum(x["inverse_required_over_BASF"]>1 for x in joined)),
        source_only_flow_topology=dict(n=3,observed_above_conditional_upper_bound=sum(x["observed_over_conditional_upper_bound"]>1 for x in flowout),
            worst_observed_over_bound=max(x["observed_over_conditional_upper_bound"] for x in flowout),
            note="bounds hold ONLY for the declared one-separator NH3-free makeup nominal-flow comparator"),
        two_bed_source_profile=dict(n=4,distinct_cases=2,
            ratio_min=min(ratios),ratio_max=max(ratios),
            best_common_rate_equivalent_multiplier=compromise,
            unavoidable_worst_multiplicative_discrepancy_factor=worst_factor,
            note="algebraic lower bound for the fixed-trajectory rate-equivalent ratios, NOT a physical global fit"),
        compressor=dict(n_failures=len(comp),E01_hypothetical_gentle_pressure_bound_MW=corrected,
            E01_unexplained_duty_MW=remainder,
            E01_unexplained_share_of_source=remainder/number(ratio_bound["plant_MW"])),
        no_fit=True,canonical_NH3_model_modified=False)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# NH3 source-basis mismatch certificate (conditional, no fit)","",
      "Source original industrial benchmark: 32/64 pass, unchanged.","",
      "## Five source plant inlets",
      "| Plant | Observed NH3 inlet (%) | Original model (%) | BASF-only model (%) | Fixed-loop inverse required/BASF |",
      "|---|---:|---:|---:|---:|"]
    for x in joined:
        lines.append(f"| {x['case_id']} | {x['plant_inlet_pct']:.3f} | {x['baseline_model_inlet_pct']:.3f} | {x['model_inlet_with_only_BASF_pct']:.3f} | {x['inverse_required_over_BASF']:.2f} |")
    lines+=["","Source-vapor substitution moves 1/5 cases into the original +/-20% inlet diagnostic band. The inverse required/BASF ratios arise by fitting the SAME industrial target and are NOT independent EOS validation.",
        "","## Stoichiometric source-only topology bounds",
        "| Plant | Published inlet (%) | One-separator optimistic bound (%) | Measured / bound |",
        "|---|---:|---:|---:|"]
    for x in flowout:
        lines.append(f"| {x['case_id']} | {x['industrial_inlet_pct']:.3f} | {x['upper_bound_under_one_separator_pct']:.3f} | {x['observed_over_conditional_upper_bound']:.2f} |")
    lines+=["","These bounds use a simplified single-separator, NH3-free makeup, nominal-design production topology. A different plant topology or process boundaries removes this model-conditioned inequality; no real mass conservation violation is alleged.",
        "","## No single bed-rate equivalent fixes both beds",
        f"Four ratios span {min(ratios):.3f}–{max(ratios):.3f}; shared-multiplier minimax ratio ~{compromise:.3f}; irreducible worst multiplicative factor ~{worst_factor:.3f} within fixed trajectories.",
        "","## Compression scope",
        f"All three original compressor comparisons remain FAIL. E01 original {comp[0]['model_duty']:.3f} MW versus source {comp[0]['industrial_duty']:.3f} MW. Even original deliberately generous suction-only correction gives {corrected:.3f} MW, leaving {remainder:.3f} MW ({100*remainder/comp[0]['industrial_duty']:.1f}%).",
        "","## Interpretation gate",
        "These concurrent mismatches support NON-IDENTIFIABILITY of a one-parameter physics repair for the source-conditioned model; they do not identify unique causes.",
        "Before a new industrial simulator can be promoted, collect stream boundary definitions, mixed-gas VLE, compressor equipment boundaries/efficiencies, heat-transfer and hydrodynamics, and matched same-formulation kinetic windows.",
        "No baseline model, industrial pass rule or manuscript result was changed.",""]
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"registered":"32/64 unchanged","VLE_one_factor":False,
        "BASF_only_inlets":summary["source_plant_inlets"]["separator_only_within_20pct"],
        "flow_bounds":summary["source_only_flow_topology"]["observed_above_conditional_upper_bound"],
        "bed_worst_factor":worst_factor,"E01_remaining_MW":remainder},indent=2))


if __name__=="__main__":
    main()
