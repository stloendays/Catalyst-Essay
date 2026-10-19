#!/usr/bin/env python3
"""Compare BASF-fitted NH3 separator gas pressure correction to two UHDE source gas streams.

External source file is fetched from a separate PR and Git-blob pinned,
not refitted to these plant values. Two points share ONE plant; this is a
cross-source diagnostic, not independent multi-plant physical validation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"analysis"/"nh3_industrial_validation_2026_10_14"))
import vle_cv as V
from diagnose_separator_vle import grid_from_printed_sources, source_interpolation

SOURCE_BLOB="7d511a788895d1f3ab825f9db9a3f0929db44460"
DOI="10.1002/14356007.o02_o11"
PRIMARY_IDS=(5,6)
METHODS=("M0_ideal","BASF_interpolated","M1_source_fit","M2_source_fit")
R=8.314462618


def require(t,m):
    if not t:raise AssertionError(m)


def data(path):
    blob=path.read_bytes()
    name=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
    require(name==SOURCE_BLOB,f"Source Figure57 git-blob integrity failed: {name}")
    with path.open(encoding="utf-8-sig",newline="") as f:raw=list(csv.DictReader(f))
    require(len(raw)==12 and {int(r["stream_id"]) for r in raw}==set(range(1,13)),
            "wrong 12-source stream record")
    for r in raw:
        require(r["primary_doi"]==DOI and r["source_figure"]=="Figure 57" and
                r["printed_page"]=="211","unattributed printed source")
        values=[float(r[f"{x}_molpct"]) for x in ("N2","H2","CH4","Ar","NH3")]
        require(all(0<=v<=100 for v in values) and abs(sum(values)-100)<.02,
                "invalid printed gas composition; do not renormalize a source")
    chosen={int(r["stream_id"]):r for r in raw if int(r["stream_id"]) in PRIMARY_IDS}
    require(len(chosen)==2,"missing source gas separators")
    require(abs(float(chosen[5]["NH3_molpct"])-8.51)<1e-10 and
            abs(float(chosen[6]["NH3_molpct"])-4.18)<1e-10,
            "original publication sample changed")
    require(abs(float(chosen[5]["pressure_MPa"])-18.02)<1e-10 and
            abs(float(chosen[6]["pressure_MPa"])-17.88)<1e-10,
            "original industrial pressure context changed")
    return chosen


def prediction(T_C,P_bar,model,coefs,grid):
    y0=V.psat_nh3_bar(T_C)/P_bar
    if model=="M0_ideal":return y0
    if model=="BASF_interpolated":
        return source_interpolation(grid,T_C,P_bar)/100.
    x=(P_bar-V.psat_nh3_bar(T_C))*1e5/(R*(T_C+273.15))
    lookup={"M1_source_fit":"M1_one_effective_pressure",
            "M2_source_fit":"M2_intercept_plus_pressure"}
    require(model in lookup,"unknown unregistered source model")
    r=dict(key=f"uhde:{T_C}C,{P_bar}bar",X=x,original_y=y0)
    return V.predict(r,lookup[model],coefs[model])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--streams",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    selected=data(args.streams)
    grid=grid_from_printed_sources()
    train=V.dataset()
    coeffs={"M1_source_fit":V.fit(train,1),"M2_source_fit":V.fit(train,2)}
    result=[]
    for idx in PRIMARY_IDS:
        source=selected[idx]
        T=float(source["temperature_C"]);P=float(source["pressure_MPa"])*10.
        observed=float(source["NH3_molpct"])
        ch4=float(source["CH4_molpct"]);ar=float(source["Ar_molpct"])
        for model in METHODS:
            y=100.*prediction(T,P,model,coeffs,grid)
            require(0<y<100 and math.isfinite(y),"unphysical source gas vapor prediction")
            err=y/observed-1
            result.append(dict(stream_id=idx,source_stream=source["stream_label"],
                  source_DOI=DOI,source_page="211",source_figure="Figure 57",
                  source_P_bar=P,source_T_C=T,
                  published_NH3_molpct=observed,
                  source_CH4_plus_Ar_molpct=ch4+ar,
                  method=model,
                  predicted_vapor_NH3_molpct=y,
                  relative_error=err,
                  absolute_relative_error=abs(err),
                  within_20pct=int(abs(err)<=.2),
                  within_10pct=int(abs(err)<=.1),
                  caveat="two related streams one plant; stream 5 gas P inferred by same-vessel source P boundary"))
    require(len(result)==8,"2-source-gas x 4 source models missing")
    with (out/"01_uhde_two_gas_separators.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    outcomes={}
    for m in METHODS:
        entries=[x for x in result if x["method"]==m]
        outcomes[m]=dict(n=2,
            mean_absolute_relative_error=statistics.mean(z["absolute_relative_error"] for z in entries),
            within_20pct=sum(x["within_20pct"] for x in entries),
            within_10pct=sum(x["within_10pct"] for x in entries))
    s=dict(status="POSTHOC_CROSS_SOURCE_VAPOR_COMPARATOR__ONE_INDUSTRIAL_PLANT",
           source_Doi=DOI,source_figure="Figure 57",source_source_git_blob=SOURCE_BLOB,
           count_independent_plants=1,count_gas_streams=2,
           source_fit_training="separate 28 BASF/Ullmann data points, NO Uhde values used",
           M1_coefficient=coeffs["M1_source_fit"][1],
           M2_intercept_and_coefficient=list(coeffs["M2_source_fit"]),
           outcomes=outcomes,
           original_registered_industrial_NH3_score="32/64 unchanged",
           physical_boundary="Separation gas vapor mole fraction vs source gas stream; NOT reactor inlet, liquid-vapor whole-loop EOS or reactor kinetic validation",
           caveat_stream5_pressure="180.2bar source pressure is the identified co-vessel separator liquid/pressure boundary, not a separate measured gas-phase pressure instrument")
    (out/"summary.json").write_text(json.dumps(s,indent=2,ensure_ascii=False)+"\n")
    lines=["# Cross-source NH3 separator vapor transfer from BASF to Uhde Figure 57","",
       "**Two gas streams from ONE published Uhde plant only.** No fitting to Uhde gas data.",
       "", "| Source gas stream | Published NH3 mol% | Original psat/P | BASF table | M1 source-fitted | M2 source-fitted |",
       "|---|---:|---:|---:|---:|---:|"]
    for idx in PRIMARY_IDS:
        got={x["method"]:x for x in result if x["stream_id"]==idx}
        lines.append(f"| {idx} | {got['M0_ideal']['published_NH3_molpct']:.3f} | "+
          " | ".join(f"{got[m]['predicted_vapor_NH3_molpct']:.3f}" for m in METHODS)+" |")
    lines.extend(["","All four treatments only evaluate gas vapor concentration at source T/P. This test does not propagate through makeup and recycle, which are already seen to fail as simple industrial inlet estimators.",
        "Source 5 pressure is the co-vessel inferred pressure; both streams have substantial CH4+Ar unlike the BASF reference binary mixture of carrier gases.",
        "Any match to published gas NH3 is evidence for a useful empirical vapor comparator **at those two source conditions**, not a validated full-component PVT flash or a complete industrial plant simulation.",
        "Original NH3-FINAL-1.2 32/64 score unchanged.",""])
    (out/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(s,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
