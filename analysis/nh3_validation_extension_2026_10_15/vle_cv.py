#!/usr/bin/env python3
"""Blocked predictions against pinned independent BASF/Ullmann NH3 saturation grid.

This intentionally does NOT replace the frozen industrial thermo or rescore
the 64 plant metrics; all parameter estimation is confined to source table data.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"analysis"/"nh3_industrial_validation_2026_10_14"
sys.path.insert(0,str(SOURCE))
from diagnose_separator_vle import grid_from_printed_sources, psat_nh3_bar, T_GRID, P_GRID

R=8.314462618
MAX_K=1.e-3
MODELS=("M0_original_ideal","M1_one_effective_pressure","M2_intercept_plus_pressure")
BLOCKS=("leave_temperature_out","leave_pressure_out")


def require(cond,msg):
    if not cond:raise AssertionError(msg)


def csvout(path,items):
    items=list(items)
    require(items,"empty output "+str(path))
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]))
        w.writeheader();w.writerows(items)


def dataset():
    g=grid_from_printed_sources()
    rows=[]
    require(len(g)==28,"missing BASF source grid point")
    for t in T_GRID:
        for p in P_GRID:
            z=g[t,p]
            press=float(p)*10. # 10 MPa -> 100 bar
            T=float(t)+273.15
            y0=psat_nh3_bar(float(t))/press
            y=float(z["source_y_pct"])/100.
            require(0<y0<1 and 0<y<1,"invalid external saturation mixing ratios")
            require(abs(y0*100.-float(z["model_psat_P_pct"]))<1e-5,
                    "canonical baseline changed from frozen source record")
            x=(press-psat_nh3_bar(float(t)))*1.e5/(R*T)
            require(x>0 and math.isfinite(x),"Poynting argument outside domain")
            rows.append(dict(key=z["row_id"],T_C=t,P_MPa=p,T_K=T,P_bar=press,
                             X=x,source_y=y,original_y=y0,
                             z=math.log(y/y0),source_citation=z["source_citation"]))
    require(len({(v["T_C"],v["P_MPa"]) for v in rows})==28,"duplicate literature source cell")
    return rows


def fit(rows,nparam):
    """Fit ln(y_source/y0)=a+kX, constrained k>=0 in both cases."""
    require(len(rows)>=3 and nparam in (1,2),"invalid training source")
    xx=[r["X"] for r in rows]
    zz=[r["z"] for r in rows]
    if nparam==1:
        denom=sum(x*x for x in xx)
        require(denom>0,"singular 1-param basis")
        k=sum(x*z for x,z in zip(xx,zz))/denom
        k=max(0.,min(MAX_K,k))
        a=0.
    else:
        xbar=statistics.mean(xx);zbar=statistics.mean(zz)
        denom=sum((x-xbar)**2 for x in xx)
        require(denom>0,"singular two-param source")
        k=sum((x-xbar)*(z-zbar) for x,z in zip(xx,zz))/denom
        k=max(0.,min(MAX_K,k))
        a=zbar-k*xbar
    require(all(math.isfinite(v) for v in (k,a)),"unbounded EOS correction fit")
    return (a,k)


def predict(row,method,coeff):
    if method=="M0_original_ideal":
        yhat=row["original_y"]
    else:
        a,k=coeff
        yhat=row["original_y"]*math.exp(a+k*row["X"])
    require(math.isfinite(yhat) and 0<yhat<1.,
            "fitted external gas mixing ratio nonphysical: "+str(row["key"]))
    return yhat


def _fold(rows,block,value):
    if block=="leave_temperature_out":
        train=[r for r in rows if r["T_C"]!=value]
        test=[r for r in rows if r["T_C"]==value]
        require(len(train)==24 and len(test)==4,"non-disjoint 7-T-fold")
    else:
        train=[r for r in rows if r["P_MPa"]!=value]
        test=[r for r in rows if r["P_MPa"]==value]
        require(len(train)==21 and len(test)==7,"non-disjoint 4-P-fold")
    require({r["key"] for r in train}.isdisjoint({r["key"] for r in test}),"training leaked source test row")
    return train,test


def cv():
    rows=dataset()
    predictions=[]
    folds=[]
    for block in BLOCKS:
        heldouts=T_GRID if block=="leave_temperature_out" else P_GRID
        for value in heldouts:
            train,test=_fold(rows,block,value)
            coefs={"M0_original_ideal":(0.,0.),
                   "M1_one_effective_pressure":fit(train,1),
                   "M2_intercept_plus_pressure":fit(train,2)}
            for method,(a,k) in coefs.items():
                folds.append(dict(block=block,heldout=value,method=method,
                     training_cells=len(train),test_cells=len(test),
                     fitted_intercept_log=a,parameter_effective_m3_mol=k,
                     source_stratification="same pinned external 28-point BASF/N2:H2 1:3 table"))
                for r in test:
                    y=predict(r,method,(a,k))
                    predictions.append(dict(block=block,heldout=value,method=method,
                        source_ref_id=r["key"],T_C=r["T_C"],P_MPa=r["P_MPa"],
                        T_K=r["T_K"],P_bar=r["P_bar"],
                        source_molpct=100*r["source_y"],
                        predicted_molpct=100*y,
                        original_psat_over_P_molpct=100*r["original_y"],
                        model_minus_source_molpct=100*(y-r["source_y"]),
                        log_error=math.log(y/r["source_y"]),
                        abs_log_error=abs(math.log(y/r["source_y"])),
                        relative_error=y/r["source_y"]-1,
                        abs_relative_error=abs(y/r["source_y"]-1),
                        within_registered_plus_minus_20pct=int(abs(y/r["source_y"]-1)<=.2),
                        source_citation=r["source_citation"]))
    for block in BLOCKS:
        for m in MODELS:
            selected=[r for r in predictions if r["block"]==block and r["method"]==m]
            require(len(selected)==28 and len({r["source_ref_id"] for r in selected})==28,
                    "holdout source cells missing/duplicated")
    return rows,folds,predictions


def compile_scores(predictions):
    agg={}
    for block in BLOCKS:
        agg[block]={}
        for method in MODELS:
            r=[x for x in predictions if x["block"]==block and x["method"]==method]
            agg[block][method]=dict(
                n=len(r),mean_abs_log_error=statistics.mean(x["abs_log_error"] for x in r),
                median_abs_log_error=statistics.median(x["abs_log_error"] for x in r),
                mean_abs_relative_error=statistics.mean(x["abs_relative_error"] for x in r),
                max_abs_relative_error=max(x["abs_relative_error"] for x in r),
                mean_signed_log_bias=statistics.mean(x["log_error"] for x in r),
                within_20pct=sum(x["within_registered_plus_minus_20pct"] for x in r),
                within_20pct_fraction=sum(x["within_registered_plus_minus_20pct"] for x in r)/len(r))
    one_better=all(agg[b]["M1_one_effective_pressure"]["mean_abs_log_error"] <
                    agg[b]["M0_original_ideal"]["mean_abs_log_error"] for b in BLOCKS)
    two_better=all(agg[b]["M2_intercept_plus_pressure"]["mean_abs_log_error"] <
                    agg[b]["M0_original_ideal"]["mean_abs_log_error"] for b in BLOCKS)
    return agg,one_better,two_better


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    rows,folds,predictions=cv()
    agg,one_better,two_better=compile_scores(predictions)
    csvout(out/"01_source28.csv",rows)
    csvout(out/"02_locked_holdout_folds.csv",folds)
    csvout(out/"03_blocked_source_predictions.csv",predictions)
    result=dict(status="EXTERNAL_LITERATURE_DATA__INTERNAL_TABLE_BLOCKED_CV",
        source="Pinned Ullmann/BASF saturation in N2:H2=1:3; original model ideal psat/P as baseline",
        n_pinned_source_points=len(rows),n_temperature_folds=7,n_pressure_folds=4,
        models={m:("zero fit" if m==MODELS[0] else "effective non-physical pressure coefficient fitted on source table ONLY") for m in MODELS},
        outcomes=agg,
        M1_better_than_canonical_both_blockings=one_better,
        M2_better_than_canonical_both_blockings=two_better,
        source_record_not_industrial_loop=True,preregistered_64case_NH3_score_untouched="32/64",
        research_gate="No candidate can be promoted to an industrial high-pressure EOS or PVT process forecast from blocked cross-validation on one N2:H2 source table",
        next_required_source="independent mixed NH3-N2-H2-Ar-CH4 high-pressure flashed phase-equilibrium data and compressor manufacturer conditions")
    (out/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Blocked source VLE prediction (source-scope only)","",
           "Original 28 BASF/Ullmann NH3 vapor saturation values in 1:3 N2:H2, 7 temperatures x 4 pressures. NOT a matched industrial plant liquid-vapor process.",
           "", "| Holdout blocking | Fixed baseline log-MAE | 1param effective log-MAE | 2param effective log-MAE | Baseline within ±20% | 1param within | 2param within |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for b in BLOCKS:
        v=agg[b]
        lines.append(f"| {b} | {v[MODELS[0]]['mean_abs_log_error']:.4f} | {v[MODELS[1]]['mean_abs_log_error']:.4f} | {v[MODELS[2]]['mean_abs_log_error']:.4f} | {v[MODELS[0]]['within_20pct']}/28 | {v[MODELS[1]]['within_20pct']}/28 | {v[MODELS[2]]['within_20pct']}/28 |")
    lines.extend(["",f"One-parameter model beats original source model in BOTH heldout-axis analyses: **{one_better}**.",
        f"Two-parameter model beats original source model in BOTH: **{two_better}**.",
        "The parameters are phenomenological, not a validated equation of state. N2/H2 mixture does not represent a whole NH3 plant loop (Ar/CH4, makeup, multiple equipment stages).",
        "No earlier 64-case industrial metric changes; original 32/64 (and original V01 failure) persist.",""])
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
