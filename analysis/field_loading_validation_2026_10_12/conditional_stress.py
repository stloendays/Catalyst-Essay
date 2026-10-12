#!/usr/bin/env python3
"""Focused PR #55 robustness to UNVALIDATED loading kinetics, selectivity and mass caps.

Does not change or refit the frozen original PFR/plant models, the official S5
or the pre-existing joint m-p experiment. All perturbations are declared and
only the 28 original entries of the FOUR cross-inlet survivor groups are
rescreened, with each candidate fully reoptimised over loading and purge.
A GHSV holdout mismatch is empirical evidence against treating beta=1 as
a universally validated law; beta != 1 is a stress model, NOT a fit.
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
JPATH=REPO/"analysis/field_robustness_2026_10_12"
sys.path.insert(0,str(JPATH))
import joint_inventory_purge as J
from experimental_holdout import model_x

# alpha for m^beta in a constrained reparametrization; no new source kinetics.
# Methanol selectivity sensitivity changes by gamma*ln(m) (ABSOLUTE fraction)
# relative to the original measured anchor and preserves total carbon closure.
# Inventory caps are multiples of the published plant reference (2,868.78 t),
# NOT actual reactor vessel capacities or pressure-drop constraints.
SCENARIOS=(
    ("reference",1.0,0.0,None),
    ("kinetic_beta_0p5",0.5,0.0,None),
    ("kinetic_beta_0p75",0.75,0.0,None),
    ("kinetic_beta_1p25",1.25,0.0,None),
    ("selectivity_gamma_minus_0p05",1.0,-0.05,None),
    ("selectivity_gamma_plus_0p05",1.0,0.05,None),
    ("selectivity_gamma_minus_0p15",1.0,-0.15,None),
    ("inventory_cap_1x_plant_ref",1.0,0.0,1.0),
    ("inventory_cap_2x_plant_ref",1.0,0.0,2.0),
    ("inventory_cap_5x_plant_ref",1.0,0.0,5.0),
)


def shift_selectivity(sm,co,ch4,m,gamma):
    """The anchor m=1 is bitwise unchanged, and C selectivities sum to one."""
    for x in (sm,co,ch4,m,gamma):
        if not math.isfinite(x):
            raise ValueError("Nonfinite selectivity variable")
    if not 0<sm<=1 or co<0 or ch4<0 or m<=0 or abs(sm+co+ch4-1)>1e-6:
        raise ValueError("Invalid source selectivity, balance or m")
    if gamma==0 or m==1.0:
        return float(sm),float(co),float(ch4)
    s=float(np.clip(sm+gamma*math.log(m),.001,1.0))
    remainder=max(0.0,1-s)
    base=co+ch4
    ratio=co/base if base>1e-12 else 1.0
    sco=remainder*ratio
    sch4=remainder-sco
    return s,sco,sch4


def kinetic_states(x0,xeq,beta):
    if not math.isfinite(beta) or beta<=0:
        raise ValueError("beta must be positive")
    if x0>=xeq*(1-1e-10):
        return [(1.0,float(x0),"above_feed_eq_only_measured")]
    answer=[]
    for m in J.M_GRID:
        x=x0 if m==1 else model_x(x0,xeq,float(m),beta)
        if 0<x<1:
            answer.append((float(m),float(x),"surrogate_sensitivity" if beta!=1 else "surrogate"))
    return answer


def optimize_one(row,beta=1.0,gamma=0.0,inventory_cap_multiple=None):
    """Mirror J.evaluate at beta=1,gamma=0,no cap; independently cross-check."""
    x0,sty0=float(row.X),float(row.STY)
    xeq,roots=J.feed_eq(float(row.h2_co2),float(row.y_co2),
                         float(row.T_C),float(row.P_bar))
    cap=(J.G.M.SOURCE_CAT_T*inventory_cap_multiple if inventory_cap_multiple is not None
         else float("inf"))
    if not math.isfinite(cap) and inventory_cap_multiple is not None or cap<=0:
        raise ValueError("Invalid inventory cap")
    out={"row_id":int(row.row_id),"group":str(row.group),"doi":str(row.doi),
         "catalyst":str(row.catalyst),"x_eq_feed":xeq,"x_eq_roots":roots,
         "above_feed_eq":bool(x0>=xeq*(1-1e-10)),"states_tested":0,
         "feasible_states":0}
    best={k:None for k in J.LIMITS}
    for m,x,flag in kinetic_states(x0,xeq,beta):
        s,co,ch4=shift_selectivity(float(row.SMeOH),float(row.SCO),
                                  float(row.SCH4),m,gamma)
        sty=sty0*x/(x0*m)
        c={"X":x,"SMeOH":s,"SCH4":ch4,"SCO":co,
           "STY":sty,"P_bar":float(row.P_bar),"T_C":float(row.T_C),
           "h2_co2":float(row.h2_co2)}
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore",RuntimeWarning)
            e=J.evaluate_array(c,J.GRID)
        cost=e["cost_eur_t"]
        ok=(np.isfinite(cost)&(cost>0)&np.isfinite(e["co2_hyd_approach"])&
            (e["co2_hyd_approach"]<=1.0+J.TOL)&np.isfinite(e["catalyst_t"])&
            (e["catalyst_t"]>0)&(e["catalyst_t"]<=cap))
        out["states_tested"]+=1
        if not ok.any():continue
        out["feasible_states"]+=1
        for tag,lim in J.LIMITS.items():
            legal=ok if lim is None else (ok&np.isfinite(e["nonreactive_fraction"])&
                                          (e["nonreactive_fraction"]<=lim))
            if not legal.any():continue
            j=int(np.argmin(np.where(legal,cost,np.inf)))
            if best[tag] is not None and float(cost[j])>=best[tag]["cost"]-1e-9:continue
            fresh=(1.0+float(e["fresh_h2_co2"][j]))/float(e["carbon_efficiency"][j])*J.G.M.PROD_KMOL_H
            best[tag]={"cost":float(cost[j]),"m":m,"purge":float(J.GRID[j]),
                       "X":x,"STY":sty,"inventory_t":float(e["catalyst_t"][j]),
                       "nonreactive":float(e["nonreactive_fraction"][j]),
                       "recycle_ratio":float(e["recycle_kmol_h"][j]/fresh) if fresh>0 else np.nan,
                       "mode":flag}
    for tag,entry in best.items():
        for field in ("cost","m","purge","X","STY","inventory_t","nonreactive","recycle_ratio","mode"):
            out[f"{tag}_{field}"]=entry[field] if entry is not None else ("" if field=="mode" else np.nan)
        out[f"{tag}_feasible"]=entry is not None
    return out


def run():
    prior=json.loads((JPATH/"results/joint_summary.json").read_text(encoding="utf-8"))
    groups=[q["group"] for q in prior["cross_inlet_sameT_other_catalyst_gt5"]["groups_and_dois"]]
    if len(groups)!=4 or len(set(groups))!=4:
        raise AssertionError("Original four PR55 groups changed")
    orig=J.candidates()
    orig=orig[orig.group.isin(groups)].copy()
    assert len(orig)==28 and orig.group.nunique()==4
    source=pd.read_csv(JPATH/"results/joint_candidates.csv").set_index("row_id")
    verdicts=[]
    opt_rows=[]
    summary={}
    for label,beta,gamma,cap in SCENARIOS:
        print(f"Auditing {label} for {len(orig)} candidates, all original m/p purge points",flush=True)
        jobs=[optimize_one(r,beta,gamma,cap) for r in orig.itertuples(index=False)]
        frame=orig.merge(pd.DataFrame(jobs).drop(columns=["group","doi","catalyst"]),
                         on="row_id",validate="one_to_one")
        if label=="reference":
            for name in J.LIMITS:
                k=name+"_cost"
                if not np.allclose(frame.set_index("row_id")[k],
                                   source.loc[frame.row_id,k],rtol=2e-8,
                                   atol=2e-5,equal_nan=True):
                    raise AssertionError(f"Reference baseline differs from committed PR55 {k}")
            if not (np.array_equal(frame.row_id,orig.row_id)):
                raise AssertionError("Row matching drift")
        gm_by_tag={}
        row_result={"beta_exponent":beta,"methanol_selectivity_shift_per_ln_m":gamma,
                    "inventory_cap_multiple_of_plant_reference":cap,
                    "inventory_cap_tonnes":float(J.G.M.SOURCE_CAT_T*cap) if cap else None,
                    "candidates":len(frame),
                    "inlet_scored":{}}
        for t in J.INLET_NAMES:
            col=t+"_cost"
            grp,agg=J.aggregate(frame,col,label=label)
            if len(grp):
                grp,kinds=J.classify(frame,grp,col)
            else:kinds={}
            by=grp.set_index("group")
            gm_by_tag[t]=by
            row_result["inlet_scored"][t]={"groups":len(grp),
                "same_temperature_different_catalyst_material":int((
                    (grp.top1_mismatch)&(grp.regret>0.05)&
                    (grp.kind=="other catalyst, same temperature")).sum()) if len(grp) else 0,
                "infeasible_candidates":int((~np.isfinite(frame[col])).sum())}
            for key in groups:
                if key not in by.index:
                    verdicts.append({"scenario":label,"inlet":t,"group":key,
                                     "status":"unscored_due_to_candidate_infeasibility",
                                     "regret":np.nan,"different_catalyst_sameT_gt5":False,
                                     "original_winner":"","optimized_winner":""})
                    continue
                q=by.loc[key]
                keep=bool(q.top1_mismatch) and float(q.regret)>0.05 and q.kind=="other catalyst, same temperature"
                verdicts.append({"scenario":label,"inlet":t,"group":key,
                                 "status":"ranked","regret":float(q.regret),
                                 "different_catalyst_sameT_gt5":keep,
                                 "original_winner":str(q.upstream_winner),
                                 "optimized_winner":str(q.economic_winner)})
        stable=[key for key in groups if all(
            key in gm_by_tag[t].index and
            bool(gm_by_tag[t].loc[key,"top1_mismatch"]) and
            float(gm_by_tag[t].loc[key,"regret"])>0.05 and
            gm_by_tag[t].loc[key,"kind"]=="other catalyst, same temperature"
            for t in J.INLET_NAMES)]
        row_result["cross_three_envelopes_robust_groups"]=len(stable)
        row_result["robust_group_ids"]=stable
        row_result["loading_grid_ceiling_selected_inlet_6p86"]=int(
            np.isclose(frame.inlet_6p86_m.fillna(-1),max(J.M_GRID)).sum())
        for j in jobs:
            j["scenario"]=label
            j["beta_exponent"]=beta
            j["S_gamma"]=gamma
            j["inventory_cap_multiple"]=cap if cap is not None else ""
            opt_rows.append(j)
        summary[label]=row_result
    p=pd.DataFrame(verdicts)
    p.to_csv(HERE/"conditional_group_verdicts.csv",index=False,float_format="%.12g")
    pd.DataFrame(opt_rows).to_csv(HERE/"conditional_candidates.csv",
                                  index=False,float_format="%.12g")
    output={"status":"UNFROZEN post-hoc structural stress of ONLY FOUR PR55 groups, not independent kinetic validation",
            "original_survivor_groups":groups,"number_of_scenarios":len(SCENARIOS),
            "scenarios":summary,
            "original_joint_results_unmodified":True,
            "inlet_envelopes":"original 4.92%, 6.86%, 10.249% source-derived reference scenarios; not universal industrial limits",
            "selectivity_gamma":"absolute CH3OH selectivity shift per ln(inventory multiple) with CO/CH4 residual proportions retained; hypothetical, anchor exactly reproduced",
            "beta_parameter":"power of inventory m in approach-to-equilibrium rate; 1 original first-order surrogate; other values are nonfitted structural stresses",
            "inventory_cap":"relative to published plant's benchmark 2,868.78 tonne inventory; NOT a measured physical volume or pressure-drop limit",
            "engineering_gate":{"pressure_drop_checked":False,"pellet_diameter_known":False,
                                "bulk_bed_density_known":False,"bed_porosity_known":False,
                                "reactor_cross_section_known":False,
                                "absolute_plant_hydraulic_feasibility_validated":False},
            "publication_ready":False,
            "limitations":[
                "Four groups preselected for robustness; cannot extrapolate prevalence or a global robust decision probability",
                "DOI paper source controls pretreatment and independent X(GHSV) holdouts; structural accuracy of beta=1 must be reported",
                "Fixed bed/catalyst installation constraints have only a provisional catalyst mass ceiling, no pressure-drop and energy balance",
                "No independent selectivity response function fitted or verified across catalysts",
            ]}
    (HERE/"conditional_stress_report.json").write_text(
        json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:{"cross_three_envelopes_robust_groups":
                        v["cross_three_envelopes_robust_groups"],
                        "inlet_6p86":v["inlet_scored"]["inlet_6p86"]}
                      for k,v in summary.items()},indent=2))


if __name__=="__main__":
    run()
