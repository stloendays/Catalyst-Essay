#!/usr/bin/env python3
"""Hou In2O3 SI S5 source feed correction, lab equilibrium and joint m-p recheck.

Unfrozen: never write to old extraction, frozen S5, earlier PR results, or main.
The original article Section 1.4 specifies H2:CO2:Ar=4:1:1 for both Au/In2O3
and bare In2O3 catalytic activity tests (DOI 10.1016/j.jes.2023.05.010).
The old curated three bare Table S5 entries used y_CO2=0.2, while the three
Au entries already used y_CO2=1/6.

Three source-level variants:
  legacy: prior committed industrial-cost optima; bare lab y_CO2=0.20,
          Au lab y_CO2=1/6; N2 stand-in for lab inert gas.
  corrected_N2_proxy: bare lab y_CO2=1/6; N2 stand-in retained so ONLY
          the correction to lab inert fraction is evaluated.
  corrected_Ar_PR: all six source rows use lab y_CO2=1/6 AND the measured
          inert species Ar in the laboratory PR equilibrium solver.

The INDUSTRIAL process/TEA is left unchanged. It still assumes its original
N2-containing process flow, and its published inlet composition limits are
reference scenarios rather than measured Hou plant constraints.

Argon PR critical properties are isolated to the laboratory equilibrium solver
(Tc=150.687 K, Pc=48.63 bar, acentric=-0.002). Tc/Pc: NIST JPCRD 1999;
acentric: NIST teqp General Cubics documentation.
https://srd.nist.gov/jpcrdreprint/1.556037.pdf
https://pages.nist.gov/teqp-docs/en/main/models/cubics.html

The frozen 304 NON-Hou candidate minima are reused verbatim, while changed
Hou points are reoptimized over m and purge under all 56 engineering settings.
The laboratory STY leader remains pinned to the original publication.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"analysis/meoh_engineering_envelope_2026_10_12"))
sys.path.insert(0,str(ROOT/"analysis/meoh_engineering_review_2026_10_12"))
import run_engineering_envelopes as E   # noqa: E402
import audit_fixed_sty_leader as F     # noqa: E402
from run_conversion_sensitivity import equilibrium_roots  # noqa: E402

J=E.J
G=J.G
DOI="10.1016/j.jes.2023.05.010"
FEED_RATIO=(4.,1.,1.)
Y_CO2_SOURCE=FEED_RATIO[1]/sum(FEED_RATIO)
Y_CO2_LEGACY_BARE=.2
ARGON_PR_CRIT=(150.687,48.63,-.002)
SOURCE_PDF_SHA256="a42b9e52bc33b8de323be4c2010b4c9d7faaeb1934fef96c7c6cd7f213ff51b7"
SOURCE_SI_PDF_SHA256="e429573f05bdd233f96963d397f6cd1ca802edf23e49adf42923b73b8aceb446"
SOURCE_SI_DOCX_SHA256="effbce2d5cad7d88183bd3e6851cc3c809eb6977f19148b55d6b70d4034ea8fe"
VARIANTS=("legacy","corrected_N2_proxy","corrected_Ar_PR")
COMPETITOR_SOURCE=ROOT/"analysis/meoh_engineering_envelope_2026_10_12/results/engineering_candidate_optima.csv"
REFERENCE=ROOT/"analysis/meoh_engineering_review_2026_10_12/results/fixed_original_STY_leader_summary.json"

def is_bare(entry:str)->bool:
    return entry.startswith("SI Table S5 row In2O3-")

def hou_candidates(base):
    hou=base[base.doi==DOI].copy().sort_values("row_id")
    if len(hou)!=6 or hou.group.nunique()!=2:
        raise AssertionError("Hou candidate membership/grouping changed; 3 bare and 3 Au points expected")
    bare=hou.entry.map(is_bare)
    if bare.sum()!=3 or (~bare).sum()!=3:
        raise AssertionError("Hou bare versus Au categories drifted")
    if not np.allclose(hou.loc[bare,"y_co2"],Y_CO2_LEGACY_BARE,atol=1e-10):
        raise AssertionError("Legacy bare In2O3 y_CO2 is no longer 0.20; update review protocol")
    if not np.allclose(hou.loc[~bare,"y_co2"],Y_CO2_SOURCE,atol=2e-10):
        raise AssertionError("Au source y_CO2 not consistent with 4:1:1")
    if set(hou.loc[bare,"entry"])!={"SI Table S5 row In2O3-HM",
                                   "SI Table S5 row In2O3-NP",
                                   "SI Table S5 row In2O3-NS"}:
        raise AssertionError("Unexpected S5 bare source labels")
    if not np.allclose(hou.h2_co2,4.0):
        raise AssertionError("Hou source reactant ratio drifted")
    if not np.allclose(hou.T_C,300.):
        raise AssertionError("Hou source temperature drifted")
    if not np.allclose(hou.P_bar,30.):
        raise AssertionError("Hou source pressure drifted")
    if not np.all(hou.sty_printed):
        raise AssertionError("All six primary Hou STY values must stay printed")
    return hou

def argon_equilibrium(h2_co2,y_co2,t_c,p_bar):
    """Argon-specific, multi-root laboratory equilibrium, NOT the plant loop."""
    if not np.isclose(h2_co2,4.,atol=1e-12) or not np.isclose(y_co2,Y_CO2_SOURCE,atol=2e-10):
        raise AssertionError("Argon correction is source-specific to Hou 4:1:1")
    if "Ar" in G.PR_CRIT:
        raise AssertionError("Industrial process species must not be modified by Ar laboratory solve")
    # For CO2=1, total feed=1/yCO2=6: H2=4 and Ar=1.
    inert_per_co2=1./y_co2-1.-h2_co2
    if not np.isclose(inert_per_co2,1.,atol=1e-8):
        raise AssertionError("Ar/CO2 ratio must be 1")
    feed={"CO2":1.,"H2":h2_co2,"Ar":inert_per_co2}
    # Add Ar ONLY while evaluating laboratory equilibrium and remove it
    # before the industrial G.cost loop is ever called. This prevents an
    # accidental Ar species in the process thermodynamics.
    G.PR_CRIT["Ar"]=ARGON_PR_CRIT
    try:
        roots=equilibrium_roots(feed,t_c,p_bar)
    finally:
        G.PR_CRIT.pop("Ar",None)
    if not roots:
        raise RuntimeError("No physically valid argon lab equilibrium root")
    if not 0 < roots[0] < 1:
        raise ValueError("Unphysical argon equilibrium conversion")
    return float(roots[0]),len(roots)

@contextmanager
def isolated_argon_solver():
    """Temporarily extend PR *lab* EOS only; restore model even after error."""
    if "Ar" in G.PR_CRIT:
        raise AssertionError("Expected frozen PR species set without Ar")
    original_eq=J.feed_eq
    try:
        J.feed_eq=argon_equilibrium
        yield
    finally:
        J.feed_eq=original_eq
        if "Ar" in G.PR_CRIT:
            raise AssertionError("Ar laboratory equilibrium was not isolated from the process EOS")

def compare_numerical_regression(prior,now,keys=("row_id","max_m","inlet","cap")):
    merged=now.merge(prior,on=list(keys),validate="one_to_one",
                     suffixes=("_calc","_prior"),indicator=True)
    if len(merged)!=len(now) or (merged._merge!="both").any():
        raise AssertionError("Legacy candidate/scenario keys no longer match pinned PR56")
    comparable=np.isclose(merged.cost_calc,merged.cost_prior,
                          rtol=2e-8,atol=2e-5,equal_nan=True)
    if not comparable.all():
        bad=merged.loc[~comparable,list(keys)+["cost_calc","cost_prior"]].head(6)
        raise AssertionError("Legacy run deviated from previously validated source model: "+repr(bad.to_dict("records")))
    return len(merged)

def measure_cases(variant,hou):
    for row in hou.itertuples(index=False):
        corrected=row._replace(y_co2=Y_CO2_SOURCE) if variant!="legacy" else row
        data=E.optimize(corrected)
        if len(data)!=56:
            raise AssertionError("Expected 56 equipment and inlet joint cases for each Hou source entry")
        for item in data:
            item["variant"]=variant
            item["y_co2_lab"]=float(corrected.y_co2)
            item["lab_inert_model"]=("argon_peng_robinson" if variant=="corrected_Ar_PR"
                                     else "nitrogen_surrogate")
            item["original_y_co2_lab"]=float(row.y_co2)
            item["source_entry"]=row.entry
        yield from data

def optimizer_results(hou,previous):
    old=pd.DataFrame(list(measure_cases("legacy",hou)))
    prior=previous[previous.row_id.isin(hou.row_id)]
    if compare_numerical_regression(prior,old)!=6*56:
        raise AssertionError("Legacy source re-run failed")
    print("PASSED: 336 pinned original Hou candidate optima reproduce PR #56",flush=True)
    bare=hou[hou.entry.map(is_bare)]
    corrected=pd.DataFrame(list(measure_cases("corrected_N2_proxy",bare)))
    # Au y_CO2 already source-correct; its old N2-proxy states stay identical.
    au=old[~old.source_entry.map(is_bare)].copy()
    au["variant"]="corrected_N2_proxy"
    corrected=pd.concat([corrected,au],ignore_index=True)
    if not np.allclose(corrected.y_co2_lab,Y_CO2_SOURCE,atol=2e-10):
        raise AssertionError("Not all corrected-source lab fractions are 1/6")
    with isolated_argon_solver():
        argon=pd.DataFrame(list(measure_cases("corrected_Ar_PR",hou)))
    combined=pd.concat([old,corrected,argon],ignore_index=True)
    if len(combined)!=6*56*3 or combined.duplicated(["variant","row_id","max_m","inlet","cap"]).any():
        raise AssertionError("Variant keys/total do not cover all six Hou entries")
    for v in VARIANTS:
        for rowid in hou.row_id:
            d=combined[(combined.variant==v)&(combined.row_id==rowid)]
            if len(d)!=56:
                raise AssertionError("Incomplete variant grid")
    return combined

def rescore_group(source_frame,costs):
    out={}
    for group,g in source_frame.groupby("group"):
        r=F.classify_group(g,costs)
        out[group]=r
    return out

def full_cohort_reports(base,reference,prior,cases):
    """All unaffected entries reused exactly; rescore the ORIGINAL 40 groups.

    This mathematically reproduces a full reoptimization under a data-only
    correction because candidate costs depend on lab y only through each
    candidate's independent xeq; do NOT import laboratory Ar into plant CO loop.
    """
    groups={g:sub for g,sub in base.groupby("group")}
    if len(groups)!=40 or len(base)!=310:
        raise AssertionError("Original 310-entry/40-group denominator not conserved")
    original_hou=set(cases.row_id)
    rows=[]
    summaries={}
    for max_m in E.LOADING_MAX:
        for cap in E.CAPS:
            for inlet in E.INLETS:
                expected=prior[(prior.max_m==max_m)&(prior.cap==cap)&(prior.inlet==inlet)]
                if len(expected)!=310 or expected.row_id.nunique()!=310:
                    raise AssertionError("Incomplete original engineering scenario")
                costs=expected.set_index("row_id").cost.copy()
                for variant in VARIANTS:
                    batch=cases[(cases.max_m==max_m)&(cases.cap==cap)&
                                (cases.inlet==inlet)&(cases.variant==variant)]
                    if len(batch)!=6 or set(batch.row_id)!=original_hou:
                        raise AssertionError("Missing one or more Hou corrected cases")
                    updated=costs.copy()
                    updated.loc[batch.row_id]=batch.cost.to_numpy()
                    scenario_rows=[]
                    for group,src in groups.items():
                        verdict=F.classify_group(src,updated)
                        verdict.update(max_m=int(max_m),cap=cap,inlet=inlet,variant=variant)
                        scenario_rows.append(verdict)
                        if src.doi.iloc[0]==DOI:
                            rows.append(verdict)
                    checks=pd.DataFrame(scenario_rows)
                    elig=checks[checks.status=="original_sty_leader_feasible"]
                    status=checks.status.value_counts().to_dict()
                    summary=dict(
                        groups_total=40,
                        groups_original_lab_champion_feasible=int(len(elig)),
                        original_lab_champion_excluded=int(status.get("original_sty_leader_infeasible",0)),
                        one_feasible=int(status.get("one_feasible_candidate",0)),
                        none_feasible=int(status.get("no_feasible_candidates",0)),
                        original_leader_mismatch=int(elig.mismatch.sum()),
                        material_regret_gt5=int(elig.material_gt5.sum()),
                        same_temperature_other_catalyst_gt5=int(elig.sameT_other_catalyst_gt5.sum()),
                        material_regret_gt5_without_bansode=int(
                            (elig.material_gt5 & (elig.doi!=J.BANSODE)).sum()),
                        hou_groups=dict(
                            (v["group"],dict(status=v["status"],
                              econ_winner=v["economic_winner"],
                              original_lab_winner=v["original_STY_leader"],
                              regret=(float(v["regret"]) if pd.notna(v["regret"]) else None),
                              material_gt5=bool(v["material_gt5"]),
                              sameT_other_catalyst_gt5=bool(v["sameT_other_catalyst_gt5"])))
                            for v in scenario_rows if v["doi"]==DOI)
                    )
                    if sum(status.values())!=40:
                        raise AssertionError("40 groups must partition feasibility outcomes")
                    if variant=="legacy":
                        p=reference["scenarios"][f"m{int(max_m)}__{cap}"]["inlets"][inlet]
                        if (summary["groups_original_lab_champion_feasible"] != p["original_leader_comparable"] or
                            summary["material_regret_gt5"]!=p["fixed_leader_regret_gt5"] or
                            summary["original_leader_mismatch"]!=p["fixed_leader_mismatch"] or
                            summary["one_feasible"]!=p["single_feasible"] or
                            summary["none_feasible"]!=p["none_feasible"] or
                            summary["original_lab_champion_excluded"]!=p["original_leader_excluded"]):
                            raise AssertionError("Complete 40-group legacy decision results drifted: "+
                                f"{max_m}/{cap}/{inlet}")
                    summaries[f"m{int(max_m)}__{cap}__{inlet}__{variant}"]=summary
    hout=pd.DataFrame(rows)
    if len(hout)!=2*56*3:
        raise AssertionError("Hou 2-group output missing scenario rows")
    return hout,summaries

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=HERE/"results")
    args=ap.parse_args()
    base=J.candidates()
    hou=hou_candidates(base)
    prior=pd.read_csv(COMPETITOR_SOURCE)
    reference=json.loads(REFERENCE.read_text(encoding="utf-8"))
    changes=optimizer_results(hou,prior)
    group,summaries=full_cohort_reports(base,reference,prior,changes)
    lines=[]
    for row in hou.itertuples(index=False):
        old=changes[(changes.variant=="legacy")&(changes.row_id==row.row_id)].iloc[0]
        n2=changes[(changes.variant=="corrected_N2_proxy")&(changes.row_id==row.row_id)].iloc[0]
        ar=changes[(changes.variant=="corrected_Ar_PR")&(changes.row_id==row.row_id)].iloc[0]
        lines.append(dict(row_id=int(row.row_id),source_entry=row.entry,group=row.group,
                          family=("bare In2O3" if is_bare(row.entry) else "Au/In2O3"),
                          measured_STY_g_gcat_h=float(row.STY),
                          measured_X_CO2=float(row.X),original_y_CO2=float(row.y_co2),
                          corrected_y_CO2=Y_CO2_SOURCE,
                          eq_legacy_N2=float(old.x_eq_feed),
                          eq_corrected_N2=float(n2.x_eq_feed),
                          eq_corrected_Ar=float(ar.x_eq_feed),
                          roots_legacy_N2=int(old.x_eq_roots),
                          roots_corrected_Ar=int(ar.x_eq_roots),
                          above_lab_eq_legacy=bool(old.above_feed_eq),
                          above_lab_eq_corrected_Ar=bool(ar.above_feed_eq)))
    # The unchanged 38 non-Hou groups preserve their already validated
    # three-inlet intersections. Rebuild only the two affected Hou groups.
    # This avoids claiming that deleted original-STY leaders are reversals.
    robust_intersections={}
    for max_m in E.LOADING_MAX:
        for cap in E.CAPS:
            known={d["group"] for d in reference["scenarios"][f"m{int(max_m)}__{cap}"]
                   ["fixed_leader_material_sameT_3inlet_intersection"]["cases"]}
            fixed_unaffected=known-set(hou.group)
            for variant in VARIANTS:
                new_hou=set()
                for group_key in hou.group.unique():
                    all_three=group[
                        (group.max_m==max_m)&(group.cap==cap)&
                        (group.variant==variant)&(group.group==group_key)&
                        (group.inlet.isin(J.INLET_NAMES))]
                    if len(all_three)!=3:
                        raise AssertionError("Hou 3 inlet comparisons missing")
                    if all_three.sameT_other_catalyst_gt5.astype(bool).all():
                        new_hou.add(group_key)
                current=sorted(fixed_unaffected|new_hou)
                key=f"m{int(max_m)}__{cap}__{variant}"
                robust_intersections[key]=dict(
                    groups=len(current),
                    independent_papers=len({g.split(" | ",1)[0] for g in current}),
                    without_bansode=sum(g.split(" | ",1)[0]!=J.BANSODE for g in current),
                    hou_groups=sorted(new_hou),
                    cases=current)
                if variant=="legacy" and set(current)!=known:
                    raise AssertionError("Legacy robust three-inlet intersection drifted")
    summary={
        "three_inlet_intersections_fixed_original_STY":robust_intersections,
        "scope":"Unfrozen Hou-only, 6-experiment source feed recheck with 304 other frozen-compatible experimental candidates untouched.",
        "source":{
            "doi":DOI, "journal_reference":"J. Environmental Sciences 140 (2024) 91-102",
            "verified_main_article_sha256":SOURCE_PDF_SHA256,
            "verified_si_pdf_sha256":SOURCE_SI_PDF_SHA256,
            "verified_si_docx_sha256":SOURCE_SI_DOCX_SHA256,
            "original_method":"Sec.1.4: Au/In2O3 OR bare In2O3 loaded for reactor activity test; H2:CO2:Ar=4:1:1, total 60 ml/min.",
            "supporting_information":"Table S5 states H2:CO2=4, 300 C, 3.0 MPa, GHSV 18000 h^-1, but omits inert species.",
            "source_archive":"Private stloendays/Catalyst-Essay-sources: freeze-field-2026-10-12",
            "raw_publisher_text_or_images_committed_publicly":False,
        },
        "laboratory_only_corrected_composition":{
            "old_bare_y_CO2":Y_CO2_LEGACY_BARE,
            "new_bare_and_Au_y_CO2":Y_CO2_SOURCE,
            "original_Ar_inert_fraction":1/6,
            "original_H2_CO2_ratio":4.0,
            "untouched_plant_makeup_composition":True
        },
        "argon_specific_PR_constants":{
            "Tc_K":ARGON_PR_CRIT[0],"Pc_bar":ARGON_PR_CRIT[1],"acentric":ARGON_PR_CRIT[2],
            "NIST_source":[
              "https://srd.nist.gov/jpcrdreprint/1.556037.pdf",
              "https://pages.nist.gov/teqp-docs/en/main/models/cubics.html"
            ],
            "mixing_rule":"Existing Peng-Robinson model k_ij=0; Argon only in laboratory thermodynamic equilibrium solver."
        },
        "input_entries":310,"hou_entries":len(hou),"hou_groups":int(hou.group.nunique()),
        "unchanged_entries":304,"scenarios":summaries,
        "laboratory_equilibria":lines,
        "caveats":[
            "Recomputes only Hou entries; other 304 candidates identical by construction, NOT independently revalidated.",
            "Measured STY, conversion, selectivity, source group identity, reactor inlet design constraints and plant N2 mix remain unchanged.",
            "The Arrhenius/first-order calibrated conversion-vs-loading relation is a surrogate and not measured kinetics.",
            "Fixed selectivity despite changing residence time remains a structural error possibility.",
            "PR Argon model k_ij=0 and lowest converged equilibrium root; not a validated multicomponent experimental EOS.",
            "The three bare entries miss CO/CH4 speciation; imputed residual carbon partition remains a separate uncertainty.",
            "All three bare entries come from one paper; morphology variants not three metal identities.",
            "Industrial reactor pressure drop still fixed 1.5 bar in the source TEA; Ergun follow-up PR #62 has no measured bed input."
        ],
    }
    args.output.mkdir(parents=True,exist_ok=True)
    changes.to_csv(args.output/"hou_candidate_feed_variants.csv",index=False,float_format="%.12g")
    group.to_csv(args.output/"hou_group_rankings_fixed_original_sty.csv",index=False,float_format="%.12g")
    (args.output/"hou_feed_source_correction_summary.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "hou_entries":len(hou),"candidate_variant_optima":len(changes),
      "fixed_group_decisions":len(group),"all_40_group_scenarios":len(summaries),
      "per_entry_equilibrium":lines,
      "anchor_m10_uncapped":{v:summaries[f"m10__uncapped__inlet_6p86__{v}"]
                            for v in VARIANTS},
      "original_four_robust_intersection":{v:robust_intersections[f"m10__uncapped__{v}"]
                                          for v in VARIANTS}
    },indent=2,default=float))


if __name__=="__main__":
    main()
