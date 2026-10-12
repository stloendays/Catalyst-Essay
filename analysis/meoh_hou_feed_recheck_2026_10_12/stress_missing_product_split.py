#!/usr/bin/env python3
"""Joint Hou argon-lab-feed correction x unreported product-selectivity closure.

STRICT SOURCE SCOPE: 3 bare In2O3 source Table S5 entries. The original paper
identifies CO and methanol as primary products and CH4 as a TRACE product,
therefore allocating all unreported carbon to methane is an intentionally
physically implausible ADVERSARIAL bound, not an empirical probability model.

The Ar laboratory feed equilibrium is recomputed with explicit Peng-Robinson
Argon; only while solving lab Xeq, never inside industrial G.cost. At each
CH4/CO bound, each bare source candidate jointly reoptimizes (m, purge) for
2 x 4 x 7 source-engineering scenarios.

Outputs compare the original STY leader and test independent inlet-envelope
robustness without reselecting the experimental source champion. No frozen
manuscript, source dataset or previous joint runs are overwritten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import recheck_source_argon as R   # noqa: E402

E=R.E
F=R.F
J=R.J
DOI=R.DOI
BOUNDS=("residual_as_CO_original_closure",
        "residual_as_CH4_adversarial")
BASE=HERE/"results/hou_candidate_feed_variants.csv"
MAIN=HERE/"results/hou_feed_source_correction_summary.json"

def bare_cases():
    base=J.candidates()
    hou=R.hou_candidates(base)
    bare=hou[hou.entry.map(R.is_bare)].copy()
    if len(bare)!=3 or not np.all(bare.ch4_printed==False) or not np.all(bare.co_printed==False):
        raise AssertionError("Original bare source product reporting changed; no bound justified")
    for row in bare.itertuples(index=False):
        if not np.isclose(row.SCO,1-row.SMeOH,atol=1e-10) or not np.isclose(row.SCH4,0.,atol=1e-10):
            raise AssertionError("Original source carbon residual CO closure drifted")
    return base,hou,bare

def optima_for_Ar_CH4_bound(bare):
    out=[]
    with R.isolated_argon_solver():
        for row in bare.itertuples(index=False):
            modified=row._replace(
                y_co2=R.Y_CO2_SOURCE,
                SCO=0.,
                SCH4=1.-float(row.SMeOH))
            if not np.isclose(modified.SMeOH+modified.SCO+modified.SCH4,1.,atol=1e-10):
                raise AssertionError("Modelled carbon-selectivity closure not 100%")
            results=E.optimize(modified)
            if len(results)!=56:
                raise AssertionError("Incomplete joint source equilibrium × CH4 purge scan")
            for x in results:
                x["bound"]=BOUNDS[1]
                x["original_lab_y_co2"]=float(row.y_co2)
                x["corrected_lab_y_co2"]=float(modified.y_co2)
                x["SMeOH"]=float(modified.SMeOH)
                x["SCO"]=float(modified.SCO)
                x["SCH4"]=float(modified.SCH4)
                x["original_aryl"]=False
                out.append(x)
            print(f"joint Ar × residual-CH4 boundary: completed {row.entry}",flush=True)
    df=pd.DataFrame(out)
    if len(df)!=3*56 or df.duplicated(["row_id","max_m","cap","inlet"]).any():
        raise AssertionError("Partial or duplicated joint boundary results")
    if "Ar" in J.G.PR_CRIT:
        raise AssertionError("Laboratory argon must not leak into source plant PR thermodynamics")
    return df

def summarize(all_original,source_hou,bare,alternate):
    src=json.loads(MAIN.read_text(encoding="utf-8"))
    prior=pd.read_csv(BASE)
    prior=prior[prior.variant=="corrected_Ar_PR"]
    prior_rows=prior[prior.row_id.isin(bare.row_id)]
    if len(prior_rows)!=3*56:
        raise AssertionError("Corrected argon/CO source scan is not yet finished")
    records=[]
    scenarios={}
    intersections={}
    bare_group=str(bare.group.iloc[0])
    for max_m in E.LOADING_MAX:
        for cap in E.CAPS:
            verdicts_by_bound={}
            for inlet in E.INLETS:
                select=lambda d:d.loc[(d.max_m==max_m)&(d.cap==cap)&(d.inlet==inlet)]
                original=select(prior_rows)
                changed=select(alternate)
                if len(original)!=3 or len(changed)!=3 or set(changed.row_id)!=set(bare.row_id):
                    raise AssertionError("All three bare formulations must remain represented in each scenario")
                for tag,costdf in zip(BOUNDS,(original,changed)):
                    costs=costdf.set_index("row_id")["cost"]
                    v=F.classify_group(bare,costs)
                    verdicts_by_bound[(tag,inlet)]=v
                    prev=src["scenarios"][f"m{int(max_m)}__{cap}__{inlet}__corrected_Ar_PR"]
                    assert v["group"]==bare_group
                    if tag==BOUNDS[0]:
                        old=prev["hou_groups"][bare_group]
                        if (v["status"]!=old["status"] or
                            v["economic_winner"]!=old["econ_winner"] or
                            bool(v["material_gt5"])!=old["material_gt5"] or
                            not np.isclose(v["regret"] if np.isfinite(v["regret"]) else np.nan,
                                           old["regret"] if old["regret"] is not None else np.nan,
                                           equal_nan=True,atol=1e-9,rtol=1e-9)):
                            raise AssertionError("Ar/CO baseline source S5 ranking drifted")
                    record=dict(
                        max_m=int(max_m),cap=cap,inlet=inlet,
                        product_bound=tag, original_bare_lab_leader=v["original_STY_leader"],
                        economic_leader=v["economic_winner"],status=v["status"],
                        regret=v["regret"],material_gt5=bool(v["material_gt5"]),
                        sameT_other_catalyst_gt5=bool(v["sameT_other_catalyst_gt5"]),
                        group=v["group"],doi=v["doi"])
                    records.append(record)
            for tag in BOUNDS:
                c=[verdicts_by_bound[(tag,inlet)] for inlet in J.INLET_NAMES]
                stable=all(bool(v["sameT_other_catalyst_gt5"]) for v in c)
                old_set=set(src["three_inlet_intersections_fixed_original_STY"]
                       [f"m{int(max_m)}__{cap}__corrected_Ar_PR"]["cases"])
                new_set=old_set-{bare_group}
                if stable:
                    new_set.add(bare_group)
                if tag==BOUNDS[0] and new_set!=old_set:
                    raise AssertionError("Prior joint feed correction robust intersection no longer reproduces")
                intersections[f"m{int(max_m)}__{cap}__{tag}"]=dict(
                    original_bare_compared_all_inlets=all(v["status"]=="original_sty_leader_feasible" for v in c),
                    bare_sameT_gt5_all_3inlets=stable,
                    all_40_group_source_fixed_three_inlet_material_sameT_groups=len(new_set),
                    independently_sourced_papers=len({g.split(" | ",1)[0] for g in new_set}),
                    cases=sorted(new_set))
    report={
        "status":"Unfrozen joint argon-feed AND unknown-carbon-product stress test; CH4 bound is deliberately adversarial and contradicts the paper's trace CH4 description.",
        "original_source":"JES 140 (2024) 91-102, DOI "+DOI+", printed SI Table S5 bare morphology comparison",
        "experimentally_reported_carbon_products":"MeOH selectivity printed, CO and CH4 selectivities not reported separately; text identifies CO as main coproduct and CH4 as trace.",
        "bounds":{
            BOUNDS[0]:"All unreported carbon from the measured residual (1-S_MeOH) assigned to CO; original source closure in the accepted plant model.",
            BOUNDS[1]:"All unreported carbon assigned to CH4, zero CO: extreme model stress test, NOT consistent with published description of trace methane.",
        },
        "lab_feed":"Both stress tests use original H2:CO2:Ar=4:1:1 and Argon PR species for lab equilibrium, with no Ar in the plant CO/purge loop.",
        "unchanged_experimental_entries":307,
        "jointly_reoptimized_bare_candidates":3,
        "source_comparison_groups_impacted":1,
        "scenarios":intersections,
        "caveats":[
            "Plant CO chemistry and CO2 conversion selectivity correlations not kinetically measured for altered catalyst inventory.",
            "All other 307 experimental points reuse the already corrected source Ar and prior TEA optima.",
            "An all-CH4 residual allocation is intentionally unphysical given the reported trace CH4; a robust result would only bound this particular model sensitivity.",
            "Multiple physical and product uncertainties are not a measured joint probability distribution; cannot claim statistical confidence from these two extreme endpoints.",
            "No actual-bed pressure drop or fixed-pressure industrial reactor design validation."
        ]
    }
    return pd.DataFrame(records),report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=HERE/"results")
    args=ap.parse_args()
    base,hou,bare=bare_cases()
    alternate=optima_for_Ar_CH4_bound(bare)
    verdicts,report=summarize(base,hou,bare,alternate)
    args.output.mkdir(parents=True,exist_ok=True)
    alternate.to_csv(args.output/"hou_argon_all_CH4_candidate_optima.csv",index=False,float_format="%.12g")
    verdicts.to_csv(args.output/"hou_argon_product_split_comparison.csv",index=False,float_format="%.12g")
    (args.output/"hou_argon_product_split_summary.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "boundary_candidate_optima":len(alternate),
        "comparison_rows":len(verdicts),
        "scenarios":len(report["scenarios"]),
        "anchor_m10_no_cap_3inlet":{
            k:report["scenarios"][f"m10__uncapped__{k}"] for k in BOUNDS},
        "strict_m10_2x_3inlet":{
            k:report["scenarios"][f"m10__anchor_2x__{k}"] for k in BOUNDS}
    },indent=2))

if __name__=="__main__":
    main()
