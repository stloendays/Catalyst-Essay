#!/usr/bin/env python3
"""Audited no-refit compressor calibration intervals and kinetics pressure-domain limits."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/"analysis"/"nh3_industrial_validation_2026_10_14"
sys.path.insert(0,str(AUDIT))
from audit_industrial import SRC,V12,SNAPSHOT_BLOB,PINS,enforce_pin,blob_sha

FE_BAR=(149*1.01325,309*1.01325)
RUC_BAR=(50.0,100.0)
REL_TOL=.30


def require(test,why):
    if not test: raise AssertionError(why)


def readcsv(file):
    with file.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def save(path,data):
    data=list(data)
    require(data,"empty source table")
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)


def source_metrics():
    for f in ("benchmark_metrics.csv","benchmark_cases.csv",
              "industrial_windows.csv","PREREGISTRATION.md","reference_values.csv"):
        enforce_pin(SRC/f,PINS[f])
    enforce_pin(V12/"results_metrics.csv",SNAPSHOT_BLOB)
    rows=readcsv(V12/"results_metrics.csv")
    require(len(rows)==64 and len({r["metric_id"] for r in rows})==64,"64-metric original prereg record damaged")
    bytab=defaultdict(list)
    for r in rows:
        bytab[r["table"]].append(r)
    for category,(n,npass) in {"A":(28,18),"B":(20,5),"C":(12,9),"E":(3,0),"V":(1,0)}.items():
        rs=bytab[category]
        require((len(rs),sum(r["pass_"].lower()=="pass" for r in rs))==(n,npass),
                f"original registered {category} counts altered")
    return {r["metric_id"]:r for r in rows}


def compressor(records):
    out=[]
    for mid in ("E01","E02","E03"):
        r=records[mid]
        require(r["pass_"]=="FAIL" and r["rule"]=="rel:0.30","changed registered compressor acceptance")
        m=float(r["model"]);p=float(r["industrial"])
        require(m>0 and p>0,"power values must be positive")
        out.append(dict(metric_id=mid,case_id=r["case_id"],
            equipment_boundary=r["quantity"],unit=r["unit"],
            original_model_MW=m,published_MW=p,
            source_to_model_power_ratio=p/m,
            missing_MW=p-m,
            relative_model_shortfall=(p-m)/p,
            lower_scale_to_pass=(1-REL_TOL)*p/m,
            upper_scale_to_pass=(1+REL_TOL)*p/m,
            original_rule=r["rule"],original_verdict=r["pass_"],
            source_rows=r["ref_rows"]))
    intersection_both=(max(r["lower_scale_to_pass"] for r in out),
                       min(r["upper_scale_to_pass"] for r in out))
    combined=out[:2]
    intersection_combined=(max(r["lower_scale_to_pass"] for r in combined),
                           min(r["upper_scale_to_pass"] for r in combined))
    # Source-only, deliberately over-attributed suction pressure correction already published by audit.
    corrected=out[0]["original_model_MW"]*math.log(151/27)/math.log(151/30)
    require(corrected<out[0]["published_MW"],"E01 27->30 bar cannot close source gap")
    return out,dict(
        all_three_bound_intersection=[*intersection_both],
        all_three_could_pass_single_scalar=intersection_both[0]<=intersection_both[1],
        combined_E01_E02_intersection=[*intersection_combined],
        combined_E01_E02_could_pass_single_scalar=intersection_combined[0]<=intersection_combined[1],
        unlike_equipment_boundaries=True,
        E01_generous_suction_only_MW=corrected,
        E01_remaining_after_generous_suction_MW=out[0]["published_MW"]-corrected,
        E01_remaining_source_fraction=(out[0]["published_MW"]-corrected)/out[0]["published_MW"])


def kinetic_bridge():
    rs=readcsv(ROOT/"analysis"/"nh3_loop_reconciliation_2026_10_14"/"outputs"/"t3_points.csv")
    group=defaultdict(dict)
    for r in rs:
        key=(r["pair"],r["model_basis"])
        require(r["catalyst"] in ("Fe","Ru"),"unregistered bridge catalyst name")
        require(r["catalyst"] not in group[key],"duplicate source bridge point")
        group[key][r["catalyst"]]=r
    require(group,"no bridge comparisons")
    compare=[]
    for (pair,basis),c in sorted(group.items()):
        require(set(c)=={"Fe","Ru"},"incomplete per-basis Fe/Ru comparison")
        fe,ru=c["Fe"],c["Ru"]
        pf=float(fe["P_bar"]);pr=float(ru["P_bar"])
        cf=float(fe["total_USD_t"]);cr=float(ru["total_USD_t"])
        require(all(math.isfinite(x) for x in (pf,pr,cf,cr)) and pf>0 and pr>0,
                "nonphysical model source bridge")
        fvalid=FE_BAR[0]<=pf<=FE_BAR[1]
        rvalid=RUC_BAR[0]<=pr<=RUC_BAR[1]
        compare.append(dict(pair=pair,model_basis=basis,Fe_P_bar=pf,Ru_P_bar=pr,
             Fe_within_original_fit_pressure=int(fvalid),
             RuC_within_original_fit_pressure=int(rvalid),
             both_within_separate_fit_ranges=int(fvalid and rvalid),
             common_operating_pressure=int(abs(pf-pr)<1e-6),
             difference_Ru_minus_Fe_USD_t=cr-cf,
             modeled_lower_cost="Fe" if cf<cr else "Ru" if cr<cf else "tie",
             industrial_validation=False,
             qualifier="Different kinetic provenance and separately nonoverlapping fit windows"))
    require(len(compare)==24,"bridge comparisons expected 24 preexisting source pairs")
    # Even if both candidates are within their own source fit domain, no ONE pressure
    # has experimental fit support for both catalysts.
    require(FE_BAR[0]>RUC_BAR[1],"original measured pressure ranges unexpectedly overlap")
    return compare


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    metrics=source_metrics()
    power,bound=compressor(metrics)
    bridge=kinetic_bridge()
    save(out/"01_preregistered_compressor_scopes.csv",power)
    save(out/"02_Fe_Ru_kinetic_bridge_domains.csv",bridge)
    summary=dict(status="ORIGINAL_PREREGISTERED_INDUSTRIAL_FAILURES_RETAINED",
       original_NH3_scores={"pass":32,"total":64,
                            "compressor":{"passed":0,"total":3},
                            "separator":{"passed":0,"total":1}},
       compressor=dict(n=3,original_failures=3,**bound),
       rates=dict(Fe_Dyson_Simon_fit_atm=[149,309],
                  Fe_fit_bar=list(FE_BAR),RuC_Rossetti_fit_bar=list(RUC_BAR),
                  common_fit_pressure_interval_bar=None,
                  pooled_matched_pressure_experimental_comparison_possible=False),
       modeled_bridge=dict(n_source_pairs=len(bridge),
            n_both_fit_valid_own_pressures=sum(r["both_within_separate_fit_ranges"] for r in bridge),
            n_exact_shared_pressure_models=sum(r["common_operating_pressure"] for r in bridge),
            low_cost_Fe_count=sum(r["modeled_lower_cost"]=="Fe" for r in bridge),
            low_cost_Ru_count=sum(r["modeled_lower_cost"]=="Ru" for r in bridge)),
       physical_scope="E01/E02 fresh+recycle versus E03 recycle-only power must not be assigned one physical machinery correction. Comparing Fe/Ru experiments across disjoint pressure ranges is extrapolation if matched to a single common P.",
       no_fit_to_external_plant=True,
       ranking_not_rescored=True)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# NH3 compression and measured-kinetic applicability audit", "",
       "**All original benchmark verdicts remain unchanged: NH3-FINAL-1.2 32/64 PASS; E 0/3, V 0/1.**",
       "", "| Compressor metric | Equipment scope | Source MW | Source-model MW | source/model | Multiplicative factor acceptance interval (predeclared ±30%) |",
       "|---|---|---:|---:|---:|---|"]
    for e in power:
        lines.append(f"| {e['metric_id']} | {e['equipment_boundary']} | {e['published_MW']:.3f} | {e['original_model_MW']:.3f} | {e['source_to_model_power_ratio']:.2f} | [{e['lower_scale_to_pass']:.2f}, {e['upper_scale_to_pass']:.2f}] |")
    lines+=["",f"Single scalar meeting all three historical ±30% windows exists: **{bound['all_three_could_pass_single_scalar']}**.",
             f"Single scalar meeting the *comparable combined-power* E01/E02 only exists: **{bound['combined_E01_E02_could_pass_single_scalar']}**.",
             f"Under a deliberately generous ideal-isothermal E01 27→30 bar correction, source-model prediction {bound['E01_generous_suction_only_MW']:.3f} MW still falls {bound['E01_remaining_after_generous_suction_MW']:.3f} MW below published 13 MW.",
             "",f"Measured original Fe domain {FE_BAR[0]:.3f}–{FE_BAR[1]:.3f} bar and promoted Ru/C {RUC_BAR[0]:.0f}–{RUC_BAR[1]:.0f} bar **do not overlap**.",
             f"Existing 24 per-basis cost comparisons: {summary['modeled_bridge']['n_both_fit_valid_own_pressures']} are within each catalyst's OWN pressure-fit domain, but this does not create a common-pressure matched measured-kinetics test.",
             "", "These are falsification and scope gates, not a new industrial compressor curve, new binary kinetic fit, or measured change in plant catalyst economics.",""]
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
