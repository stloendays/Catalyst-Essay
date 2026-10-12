#!/usr/bin/env python3
"""Independent, source-aligned GHSV holdouts for PR #55 first-order X(m).

A reported variation in the normalized feed space velocity can serve as an
inverse-catalyst-inventory perturbation ONLY where catalyst preparation, T,
pressure, feed ratio and GHSV mass units agree. The original catalog omits
Re/TiO2 prereduction temperature: reconstruct from DOI paper's printed table,
never pool the 250C- and 500C-pretreated 5wt%-Re experiments.

An attempted 1-point prediction is NOT calibrated to its test target; paper-
specific equilibrium values are labelled as literature comparators, separate
from the unchanged repo equilibrium solver.
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/"analysis/field_robustness_2026_10_12"))
import joint_inventory_purge as J

ACS="10.1021/acscatal.5c05984"
SA="10.1126/sciadv.abi6012"
SOURCE_DOIS=(ACS,SA)
PRETREAT_250=(5,6,7,8,9)
PRETREAT_500=(10,11,12,13,14)
# Manual matching to ACS Catalysis article Table 4. The catalyst identity
# 5wt% Re/TiO2 alone is INSUFFICIENT: two prereduction states appear.
ACS_PRETREAT={**{n:250 for n in PRETREAT_250},
              **{n:500 for n in PRETREAT_500}}
SA_PAPER_XEQ=0.116   # Science Advances 2021 reported 11.6% equilibrium at 300C/40bar/H2:CO2=3.
MATCH_CRITERIA="same DOI+catalyst+pretreatment+T+P+H2/CO2+mass-normalized GHSV units"


def mass_ghsv(raw):
    """Accept ONLY the printed mass-based normal-liter GHSV key."""
    m=re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s+NL/g/h\s*",str(raw))
    if not m:return None
    x=float(m.group(1))
    return x if math.isfinite(x) and x>0 else None


def pretreatment(row):
    if row.doi==SA:
        return "source_single_prep_per_catalyst_unchecked"  # paper does not enumerate extra pretreatments
    if row.doi!=ACS or row.catalyst_key!="5wt%re/tio2":
        return None
    m=re.fullmatch(r"Table 4 row (\d+)",str(row.entry))
    if not m:return None
    temp=ACS_PRETREAT.get(int(m.group(1)))
    return None if temp is None else f"reduction_{temp}C_paper_table"


def comparable_tracks(dataset=None):
    """Return independent one-anchor/multiple-test cohorts, never blend prep.

    A track is an experimental cohort. Each other GHSV is held out exactly
    once from its lowest-GHSV anchor. Different catalyst tracks within a
    common DOI do NOT count as separate papers.
    """
    if dataset is None:
        dataset=pd.read_csv(REPO/"analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
    matching=defaultdict(list)
    rejected={"no_source_tag":0,"unsupported_GHSV_basis":0,"ACS_prereduction_not_mapped":0}
    for row in dataset.itertuples(index=False):
        if row.doi not in SOURCE_DOIS:continue
        ghsv=mass_ghsv(row.ghsv_key)
        if ghsv is None:
            rejected["unsupported_GHSV_basis"]+=1
            continue
        prep=pretreatment(row)
        if prep is None:
            rejected["ACS_prereduction_not_mapped"]+=1
            continue
        # Geometric conversions are fixed in the original dataset; do not
        # assume independently that nominal feed composition is identical
        # if a source declares another feed or uses volumetric GHSV.
        key=(str(row.doi),str(row.catalyst_key),str(prep),
             float(row.T_C),float(row.P_bar),float(row.h2_co2))
        matching[key].append((ghsv,row))
    tracks=[]
    for key,observations in sorted(matching.items()):
        g_values=[g for g,r in observations]
        if len(set(g_values))<2:continue
        unique={}
        ambiguous=[]
        for g,r in observations:
            if g in unique:
                ambiguous.append((g,str(r.entry)))
            else:unique[g]=r
        if ambiguous:
            raise AssertionError(f"Repeated nominal conditions within a pretreatment cohort: {key}: {ambiguous}")
        sorted_obs=sorted(unique.items())
        anchor_g,anchor=sorted_obs[0]
        tracks.append({"doi":key[0],"catalyst":key[1],"pretreatment":key[2],
                       "T_C":key[3],"P_bar":key[4],"H2_CO2":key[5],
                       "ghsv_anchor":anchor_g,"anchor":anchor,
                       "holdouts":sorted_obs[1:]})
    return tracks,rejected


def model_x(x0,xeq,m,beta=1.0):
    if not all(math.isfinite(v) for v in (x0,xeq,m,beta)) or not 0<x0<xeq<1 or m<=0 or beta<=0:
        raise ValueError("X(m) outside pre-equilibrium model domain")
    return -xeq*math.expm1(m**beta*math.log1p(-x0/xeq))


def fitted_beta(x0,x1,xeq,m):
    if not (0<x0<xeq and 0<x1<xeq and m>0 and m!=1):
        return None
    inner=math.log1p(-x1/xeq)/math.log1p(-x0/xeq)
    if inner<=0:return None
    return math.log(inner)/math.log(m)


def evaluate_holdouts():
    tracks,rejected=comparable_tracks()
    records=[]
    for t in tracks:
        a=t["anchor"]
        x0=float(a.X)
        S0=float(a.SMeOH)
        feed_y=1/(1+t["H2_CO2"])
        model_error=""
        try:xeq,roots=J.feed_eq(t["H2_CO2"],feed_y,t["T_C"],t["P_bar"])
        except Exception as e:
            xeq,roots=math.nan,0
            model_error=f"{type(e).__name__} (laboratory feed model)"
        for g,target in t["holdouts"]:
            x1=float(target.X)
            s1=float(target.SMeOH)
            m=t["ghsv_anchor"]/g
            eq_ok=math.isfinite(xeq) and max(x0,x1)<xeq
            pred=model_x(x0,xeq,m) if eq_ok else math.nan
            lit_eq=SA_PAPER_XEQ if (t["doi"]==SA and t["T_C"]==300
                                  and t["P_bar"]==40 and t["H2_CO2"]==3) else math.nan
            lit_eq_ok=math.isfinite(lit_eq) and max(x0,x1)<lit_eq
            pred_paper=model_x(x0,lit_eq,m) if lit_eq_ok else math.nan
            beta=fitted_beta(x0,x1,xeq,m) if eq_ok else None
            records.append({
                "doi":t["doi"],"catalyst":t["catalyst"],
                "prereduction_treatment":t["pretreatment"],"T_C":t["T_C"],
                "P_bar":t["P_bar"],"H2_CO2":t["H2_CO2"],
                "source_entry_anchor":str(a.entry),"source_entry_holdout":str(target.entry),
                "GHSV_anchor_NL_g_h":t["ghsv_anchor"],"GHSV_holdout_NL_g_h":g,
                "effective_inventory_factor_m":m,
                "measured_X_anchor":x0,"measured_X_holdout":x1,
                "model_feed_Xeq":xeq,"model_eq_roots":roots,
                "model_surrogate_status":("prediction_out_of_domain" if not eq_ok
                                          else "testable_one_point_holdout"),
                "X_pred_beta1_model_eq":pred,
                "error_absolute_X_model_eq":abs(pred-x1) if eq_ok else math.nan,
                "error_signed_X_model_eq":pred-x1 if eq_ok else math.nan,
                "error_relative_model_eq":(pred-x1)/x1 if eq_ok else math.nan,
                "implied_beta_from_two_points_not_independent_validation":
                    beta if beta is not None else math.nan,
                "paper_reported_Xeq":lit_eq,
                "X_pred_beta1_paper_eq":pred_paper,
                "error_abs_X_paper_eq":abs(pred_paper-x1) if lit_eq_ok else math.nan,
                "measured_SMeOH_anchor":S0,"measured_SMeOH_holdout":s1,
                "delta_MeOH_selectivity_pp":100*(s1-S0),
                "fixed_selectivity_off_by_5pp":abs(s1-S0)>0.05,
                "STY_anchor_basis":str(a.sty_basis),
                "STY_holdout_basis":str(target.sty_basis),
                "do_not_use_STY_as_holdout_without_identical_basis":(
                    str(a.sty_basis)!=str(target.sty_basis)),
                "source_scope_warning":model_error or "same nominal conditions and curated pretreatment only",
            })
    return records,tracks,rejected


def main():
    rows,tracks,exclusions=evaluate_holdouts()
    if not rows:
        raise AssertionError("No genuinely repeated-GHSV experimental source pairs")
    df=pd.DataFrame(rows)
    HERE.mkdir(exist_ok=True,parents=True)
    df.to_csv(HERE/"measured_ghsv_holdouts.csv",index=False,float_format="%.12g")
    ok=df[df.model_surrogate_status=="testable_one_point_holdout"]
    short={
        "nature":"HOLDOUT TEST of frozen PR55 one-point X(m) model using measured X(GHSV), not a newly fitted kinetic mechanism",
        "source_papers":[{"doi":doi,"url":"https://doi.org/"+doi} for doi in sorted(df.doi.unique())],
        "all_source_rows_count":len(pd.read_csv(REPO/"analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")),
        "eligible_cohorts":len(tracks),
        "unique_papers":df.doi.nunique(),
        "heldout_measurements":len(df),
        "testable_under_original_model_feed_equilibrium":len(ok),
        "out_of_model_domain":len(df)-len(ok),
        "conversion_model_mae_percentage_points":(
            float(100*ok.error_absolute_X_model_eq.mean()) if len(ok) else None),
        "conversion_model_median_absolute_relative_error":(
            float(ok.error_relative_model_eq.abs().median()) if len(ok) else None),
        "measured_selectivity_changes_over_5pp":int(df.fixed_selectivity_off_by_5pp.sum()),
        "heldout_by_DOI":{str(k):int(v) for k,v in df.groupby("doi").size().items()},
        "equilibrium_comparators":{
            "repo_model":"unchanged PR55 multi-start feed equilibrium for each one-point X(m) anchor",
            "Science_Advances_source_specific":"published 11.6% feed equilibrium at 300C/40bar/H2:CO2=3; shown as independent thermodynamics sensitivity, NEVER silently substituted",
        },
        "ACS_prereduction_confusion_caught":True,
        "ACS_pretreatment_mapping":{
            "5wt% Re/TiO2 rows 5-9":"250C prereduction",
            "5wt% Re/TiO2 rows 10-14":"500C prereduction",
            "source":"ACS Catalysis DOI 10.1021/acscatal.5c05984, published Table 3/4",
        },
        "limitations":[
            "Only two source papers contain strictly comparable repeated-GHSV series in this preselected catalog; measurements are clustered by paper and catalyst",
            "GHSV scaling is equivalent to inverse inventory only at fixed feed/conditions/packing and comparable mass-normalized flow; this is a local kinetic holdout, not industrial pressure-drop validation",
            "Some published STY is mass-GHSV-derived and other STY is printed; this audit validates conversion and methanol selectivity from reported source values, not mixed STY bases",
            "Pretreatment affects Re catalyst identity and original PR55 inventory optimization; no global reclassification of original 4 inversions is made here",
            "Observed selectivity varies with GHSV and violates frozen selectivity assumption for relevant source tracks",
            "Alternative inferred beta from 2 measurements is in-sample identification, not independent validation",
            "Industrial reactor size, porosity, pellet diameter, pressure drop, heat removal and catalyst lifetime are not available for a validated bed model",
        ]
    }
    (HERE/"holdout_report.json").write_text(json.dumps(short,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(short,indent=2,ensure_ascii=False,allow_nan=False))


if __name__=="__main__":
    main()
