#!/usr/bin/env python3
"""Evaluate source-table-fitted VLE corrections on five OTHER literature plant inlets.

All five published plant concentrations are held OUT from coefficient estimation.
The original process-library and all 64 registered score records remain read-only.
Post-hoc exploratory transfer, not new external plant validation.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SRC_DIR=ROOT/"analysis"/"nh3_industrial_validation_2026_10_14"
sys.path.insert(0,str(SRC_DIR))
import vle_cv as V
from audit_industrial import SRC,V12,PINS,SNAPSHOT_BLOB,enforce_pin,rows
from diagnose_separator_vle import grid_from_printed_sources,source_interpolation,INLETS
from bootstrap_replay import prepare

IDS=("A01","A04","A07","A14","A16")
METHODS=("M0_frozen", "BASF_bilinear", "M1_source_fit", "M2_source_fit")
R=8.314462618


def require(cond,reason):
    if not cond:raise AssertionError(reason)


def write(path,rows_):
    rows_=list(rows_)
    require(bool(rows_),"no data")
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows_[0]));w.writeheader();w.writerows(rows_)


def source_vapor(tsep,pbar,coef,kind):
    psat=V.psat_nh3_bar(tsep)
    x=(pbar-psat)*1.e5/(R*(tsep+273.15))
    if kind=="M1_source_fit":model="M1_one_effective_pressure"
    elif kind=="M2_source_fit":model="M2_intercept_plus_pressure"
    else:raise AssertionError("not a preregistered source vapor fit")
    base=dict(original_y=psat/pbar,X=x,key=f"plant_test:{tsep}C_{pbar}bar")
    return V.predict(base,model,coef)


def conditional_point(M,h,temp,p,sep,cap,fraction_method,grid,coefficients):
    if fraction_method=="M0_frozen":
        return M.state_point(h,temp,p,sep,cap),V.psat_nh3_bar(sep)/p
    if fraction_method=="BASF_bilinear":
        source_y=source_interpolation(grid,sep,p)/100.
    else:
        source_y=source_vapor(sep,p,coefficients[fraction_method],fraction_method)
    require(0<source_y<1.,"hypothetical source vapor physically impossible")
    had_local="psat_nh3_bar" in vars(h)
    old_local=vars(h).get("psat_nh3_bar")
    try:
        h.psat_nh3_bar=lambda _temp,pressure=p,coef=source_y:pressure*coef
        point=M.state_point(h,temp,p,sep,cap)
    finally:
        if had_local:
            h.psat_nh3_bar=old_local
        else:
            delattr(h,"psat_nh3_bar")
    return point,source_y


def evaluate():
    require(set(IDS)==set(INLETS),"original fixed five reference IDs changed")
    for f in ("benchmark_cases.csv","benchmark_metrics.csv","reference_values.csv"):
        enforce_pin(SRC/f,PINS[f])
    enforce_pin(V12/"results_metrics.csv",SNAPSHOT_BLOB)
    grid=grid_from_printed_sources()
    train=V.dataset()
    coefs={
        "M1_source_fit":V.fit(train,1),
        "M2_source_fit":V.fit(train,2)
    }
    # Source records and plant cases are separate published evidence collections.
    plant={r["metric_id"]:r for r in rows(SRC/"benchmark_metrics.csv")}
    cases={r["case_id"]:r for r in rows(SRC/"benchmark_cases.csv")}
    original={r["metric_id"]:r for r in rows(V12/"results_metrics.csv")}
    prepare()
    import nh3_model as M
    h=M.build_frozen()
    M.reproduce_anchors(h)
    predictions=[]
    for mid in IDS:
        reg=plant[mid]
        stored=original[mid]
        require(stored["pass_"]=="FAIL" and reg["rule"]=="rel:0.20",
                "changed pre-registered plant inlet metric")
        case=cases[reg["case_id"]]
        temp,p,sep,cap=(float(case[z]) for z in ("T_C","P_bar","Tsep_C","capacity_tpd"))
        industrial=float(reg["industrial_value"])
        require(abs(industrial-float(stored["industrial"]))<1e-9,
                "published source industrial concentration changed")
        # all four strategies share one original fixed industrial case.
        for method in METHODS:
            point,ysep=conditional_point(M,h,temp,p,sep,cap,method,grid,coefs)
            if method=="M0_frozen":
                require(point is not None,"pre-registered original source point infeasible")
                require(abs(point["inlet_NH3_molpct"]-float(stored["model"]))<=2e-5,
                        "baseline source model changed in plant code")
            estimated=None if point is None else float(point["inlet_NH3_molpct"])
            cost=None if point is None else float(point["process_cost_USD_t"])
            error=None if estimated is None else estimated/industrial-1.
            require(error is None or math.isfinite(error),"undefined physical model error")
            predictions.append(dict(metric_id=mid,case_id=reg["case_id"],
                method=method,plant_T_C=temp,P_bar=p,separator_T_C=sep,
                capacity_tpd=cap,published_plant_inlet_molpct=industrial,
                source_vapor_molpct=ysep*100,
                model_reactor_inlet_molpct=estimated,
                relative_error=error,
                abs_relative_error=None if error is None else abs(error),
                within_original_20pct=int(estimated is not None and abs(error)<=.20),
                model_process_cost_USD_t=cost,
                original_64_case_verdict=stored["pass_"],
                caveat="model-conditioned single-vapor-proxy transfer, not fully mixed-gas plant VLE validation"))
    require(len(predictions)==20,"five cases x four fixed policies missing")
    return predictions,coefs


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    records,coefs=evaluate()
    write(out/"01_five_industrial_inlet_transfer.csv",records)
    outcomes={}
    for m in METHODS:
        rs=[x for x in records if x["method"]==m]
        require(len(rs)==5 and len({x["metric_id"] for x in rs})==5,"source case loss")
        valid=[r["abs_relative_error"] for r in rs if r["abs_relative_error"] is not None]
        outcomes[m]=dict(n_cases=5,n_feasible=len(valid),
                         within_20pct=sum(r["within_original_20pct"] for r in rs),
                         mean_abs_relative_error=statistics.mean(valid) if valid else None,
                         max_abs_relative_error=max(valid) if valid else None,
                         count_error_reduced_vs_original=None)
    baseline={x["metric_id"]:x for x in records if x["method"]=="M0_frozen"}
    for m in METHODS[1:]:
        outcomes[m]["count_error_reduced_vs_original"]=sum(
            r["abs_relative_error"] is not None and
            r["abs_relative_error"]<baseline[r["metric_id"]]["abs_relative_error"]-1e-10
            for r in records if r["method"]==m)
    require(outcomes["M0_frozen"]["within_20pct"]==0 and
            outcomes["BASF_bilinear"]["within_20pct"]==1,
            "registered baseline or previous source-only 1/5 result drift")
    outcome=dict(status="POSTHOC_SOURCE_TO_PLANT_TRANSFER_DIAGNOSTIC_NOT_FIELD_VALIDATION",
        complete=20,source_BASF_training_points=28,
        source_coefficients={k:{"fitted_log_intercept":v[0],
                               "effective_pressure_coefficient_m3_mol":v[1]}
                             for k,v in coefs.items()},
        industrial_targets_used_for_fitting=False,
        industrial_test_metrics=list(IDS),
        fixed_policies=outcomes,
        source_uncertainty="BASF 1:3 N2/H2 mixture; plant can have Ar/CH4, different purge, makeup and separator equipment; source-measured inlet vs source-model predicted not independent prospective blind validation",
        original_64_case_registered_score_unchanged="32/64",
        no_permanent_library_patch=True,
        do_not_promote_as_EOS_or_plant_cost=True)
    (out/"summary.json").write_text(json.dumps(outcome,indent=2,ensure_ascii=False)+"\n")
    lines=["# Five published NH3 plant inlets: source-fit external transfer (post-hoc exploratory)","",
      "Coefficients are fitted exclusively to 28 BASF/Ullmann 1:3 N2:H2 saturation source points, without using these five separate industrial inlet observations.",
      "", "| Vapor source assumption | Within registered ±20% | Feasible cases | Mean absolute relative error |",
      "|---|---:|---:|---:|"]
    for m,z in outcomes.items():
        mae=z["mean_abs_relative_error"]
        lines.append(f"| {m} | {z['within_20pct']}/5 | {z['n_feasible']}/5 | {'NA' if mae is None else f'{mae:.2%}'} |")
    lines.extend(["","The full source model’s fixed reaction equilibrium, catalyst and recycle/mixing remain unchanged; only five scoped vapor fractions are replaced and immediately restored.",
                  "**No changes to the original 32/64 benchmark or V01 FAIL**. Comparison is conditional, post hoc and not an industrial five-component EOS validation.",
                  "A more predictive Poynting-like factor on the BASF table alone does NOT guarantee closure with published plant inlet concentrations.",
                  "Next industrial requirement: matched inlet/outlet gas stream compositions, separator hardware, heat/pressure drop, inert and methane content and independently measured VLE across high-pressure plant mixtures.",""])
    (out/"REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(outcome,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
