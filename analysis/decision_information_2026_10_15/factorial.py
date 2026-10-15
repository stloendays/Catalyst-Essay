#!/usr/bin/env python3
"""Full crossed (5 caps x 2 definitions) MeOH source-conditioned risk certificate."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

from run import (ROOT,BANSODE,CAPS,AUGMENTED,SEED,load,read,val,fmt,require,
                 minimax,regret,all_risks,save,has_reentry,quantile_ci,policy_choices)

CAP_PERCENT=("5","6","6.86","8","10")
DEFS=("frozen","true_inert")
SCENARIOS=tuple(f"{d}_{x}" for d in DEFS for x in CAP_PERCENT)
INV_ANCHORS={"frozen":(26,27,28,27,24),"true_inert":(18,18,18,15,15)}
PREVIOUS_FROZEN={"5":"lim5","6":"lim6","6.86":"S6","8":"lim8","10":"lim10"}


def read_full_factorial(scored,bygroup,canonical_costs):
    entries=read("analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv")
    index={(z["group"],z["entry"]):z for z in entries}
    require(len(index)==len(entries),"duplicate original source entry")
    costs={}
    compared=0
    for i,c in scored.items():
        key=(c["group"],c["entry"])
        require(key in index,"no alternate original candidate: "+str(key))
        rec=index[key]
        costs[i]={}
        for d in DEFS:
            for limit in CAP_PERCENT:
                s=f"{d}_{limit}"
                value=val(rec[f"cost_{d}_{limit}"])
                costs[i][s]=value
                if d=="frozen":
                    old=canonical_costs[i][PREVIOUS_FROZEN[limit]]
                    require(math.isfinite(value)==math.isfinite(old),"frozen reference feasibility drift")
                    if math.isfinite(value):
                        require(abs(value/old-1)<1e-6, "source model cost drift at "+str(key)+s)
                    compared+=1
        # With identical purge grid and economics, adding CO to constrained species cannot LOWER the optimum.
        for limit in CAP_PERCENT:
            full=costs[i][f"frozen_{limit}"]
            true=costs[i][f"true_inert_{limit}"]
            if math.isfinite(full):
                require(math.isfinite(true),"stricter frozen feasible but weaker true-inert infeasible")
                require(true<=full+max(1e-5,full*1e-6),"weaker chemical exclusion raised minimum cost")
        for d in DEFS:
            seq=[costs[i][f"{d}_{p}"] for p in CAP_PERCENT]
            for a,b in zip(seq[:-1],seq[1:]):
                require(not(math.isfinite(a) and not math.isfinite(b)),"relaxing cap eliminated feasibility")
                if math.isfinite(a):
                    require(a+max(1e-5,1e-6*a)>=b,"relaxing cap raised optimum in "+d)
            for scenario in seq:
                if math.isfinite(scenario):
                    require(canonical_costs[i]["S5"]<=scenario+max(1e-5,scenario*1e-6),
                            "constrained model cheaper than unconstrained S5")
    require(compared==1550,"not all canonical cost columns cross-verified")
    # Original independent scenario ledger resolves ties explicitly and is NOT a new model prediction.
    scan=read("analysis/meoh_inlet_definition_2026_10_12/scan_groups.csv")
    subset=[r for r in scan if r["definition"] in DEFS and r["limit"] in CAP_PERCENT]
    require(len(subset)==400, "full factorial source ledger not 2*5*40")
    byscenario={(r["definition"],r["limit"],r["group"]):r for r in subset}
    require(len(byscenario)==400,"duplicated factorial source verdict")
    winner={}
    for d in DEFS:
        for j,limit in enumerate(CAP_PERCENT):
            ledger=[r for r in subset if r["definition"]==d and r["limit"]==limit]
            inverted=sum(x["mismatch"]=="True" for x in ledger)
            require(inverted==INV_ANCHORS[d][j],
                    f"unmodified alternative scenario {d}/{limit} inverted {inverted}, expected {INV_ANCHORS[d][j]}")
            s=f"{d}_{limit}"
            for g,ids in bygroup.items():
                source=byscenario[d,limit,g]
                matches=[i for i in ids if scored[i]["catalyst"]==source["plant_leader"]]
                require(len(matches)==1,f"original optimized winner ambiguous {g}/{s}")
                chosen=matches[0]
                opt=min(costs[i][s] for i in ids)
                require(math.isfinite(opt)>0 and math.isfinite(costs[chosen][s]),"no feasible group")
                require(costs[chosen][s]<=opt+max(.01,opt*1e-6),
                        f"ledger winner not minimum {g}/{s}")
                require(abs(float(source["c_plant"])/costs[chosen][s]-1)<1e-5,
                        f"published group cost not matching source candidate {g}/{s}")
                winner[(g,s)]=chosen
    return costs,winner


def median_finite(rows,key):
    v=[float(r[key]) for r in rows if r[key]!="INF"]
    return statistics.median(v) if v else None


def run(out):
    scored,bygroup,old,alt,canonical_costs,canonical_winners=load()
    costs,winner=read_full_factorial(scored,bygroup,canonical_costs)
    records=[];paths=[]
    for g,ids in sorted(bygroup.items()):
        full_i,full_r,full_risks=minimax(ids,costs,SCENARIOS)
        require(full_i is not None and math.isfinite(full_r),"no all-scenario robust entrant "+g)
        canonical_six_i,canonical_six_r,_=minimax(ids,canonical_costs,AUGMENTED)
        require(canonical_six_i is not None and full_r+1e-9>=canonical_six_r,
                "fully crossed set paradoxically less risky than smaller 6-case set")
        separate_form={d:minimax(ids,costs,tuple(f"{d}_{L}" for L in CAP_PERCENT))
                       for d in DEFS}
        separate_cap={L:minimax(ids,costs,tuple(f"{d}_{L}" for d in DEFS))
                      for L in CAP_PERCENT}
        residual_form=max(separate_form[d][1] for d in DEFS)
        residual_cap=max(separate_cap[L][1] for L in CAP_PERCENT)
        require(full_r+1e-9>=residual_form and full_r+1e-9>=residual_cap,
                f"perfect information worsened minimax regret {g}")
        form_benefit=max(0.,full_r-residual_form)
        cap_benefit=max(0.,full_r-residual_cap)
        policies=policy_choices(g,ids,scored,old,canonical_winners)
        row=dict(group=g,doi=scored[ids[0]]["doi"],n=len(ids),
            robust10_id=full_i,robust10_material=scored[full_i]["catalyst_key"],
            robust10_entry=scored[full_i]["entry"],
            robust10_worst_regret=full_r,robust10_certified5=int(full_r<=.05+1e-12),
            robust10_certified10=int(full_r<=.10+1e-12),
            robust10_exact0=int(full_r<=1e-7),
            robust10_equiv5_count=sum(z<=.05+1e-12 for z in full_risks.values()),
            robust10_material_count=len({scored[i]["catalyst_key"] for i in ids if full_risks[i]<=.05+1e-12}),
            robust6_id=canonical_six_i,robust6_material=scored[canonical_six_i]["catalyst_key"],
            robust6_risk=canonical_six_r,robust6_certified5=int(canonical_six_r<=.05+1e-12),
            robust10_same_choice_as_6=int(full_i==canonical_six_i),
            robust10_same_material_as_6=int(scored[full_i]["catalyst_key"]==scored[canonical_six_i]["catalyst_key"]),
            robust10_risk_increase_over_6=full_r-canonical_six_r,
            full_form_known_residual_regret=residual_form,
            full_cap_known_residual_regret=residual_cap,
            form_information_gain=form_benefit,
            cap_information_gain=cap_benefit,
            form_info_gt5pp=int(form_benefit>.05),
            cap_info_gt5pp=int(cap_benefit>.05),
            form_info_positive=int(form_benefit>1e-9),
            cap_info_positive=int(cap_benefit>1e-9),
            form_more_valuable=int(form_benefit>cap_benefit+1e-9),
            cap_more_valuable=int(cap_benefit>form_benefit+1e-9),
            source_form_known_winner_frozen=scored[separate_form["frozen"][0]]["catalyst_key"],
            source_form_known_winner_true_inert=scored[separate_form["true_inert"][0]]["catalyst_key"],
            source_form_known_risk_frozen=separate_form["frozen"][1],
            source_form_known_risk_true_inert=separate_form["true_inert"][1],
            worst_full_scenarios=";".join(s for s in SCENARIOS if
              abs(regret(costs[full_i][s],min(costs[k][s] for k in ids))-full_r)<=1e-8))
        for name,idx in policies.items():
            row[name+"_risk10"]=fmt(full_risks[idx])
            row[name+"_within5"]=int(full_risks[idx]<=.05+1e-12)
            row[name+"_material"]=scored[idx]["catalyst_key"]
        row["robust6_risk_under_all10"]=fmt(full_risks[canonical_six_i])
        row["robust6_within5_under_all10"]=int(full_risks[canonical_six_i]<=.05+1e-12)
        records.append(row)
        # Independently trace the two optimal paths to avoid conflating CO-definition with cap value.
        for d in DEFS:
            pp=[winner[(g,f"{d}_{L}")] for L in CAP_PERCENT]
            mats=[scored[i]["catalyst_key"] for i in pp]
            material_changes=0;point_changes=0;econ1=0;econ5=0
            for j in range(1,len(pp)):
                oldi,newi=pp[j-1:j+1]
                if oldi!=newi:
                    point_changes+=1
                    if mats[j-1]!=mats[j]:material_changes+=1
                    newscenario=f"{d}_{CAP_PERCENT[j]}"
                    regret_keep=regret(costs[oldi][newscenario],costs[newi][newscenario])
                    econ1+=regret_keep>.01;econ5+=regret_keep>.05
            paths.append(dict(group=g,doi=scored[ids[0]]["doi"],definition=d,
                n_point_switches=point_changes,n_material_switches=material_changes,
                point_reentry=int(has_reentry(pp)),material_reentry=int(has_reentry(mats)),
                economically_gt1pct_switches=econ1,economically_gt5pct_switches=econ5,
                point_path=";".join(map(str,pp)),material_path=";".join(mats)))
    require(len(records)==40 and len(paths)==80,"incomplete source cohort")
    save(out/"01_factorial10_minimax_groups.csv",records)
    save(out/"02_form_specific_cap_paths.csv",paths)
    require(sum(r["robust6_certified5"] for r in records)==24,
            "previously reported six-model 24/40 anchor changed")
    summary=dict(status="POSTHOC_REGISTERED_EXTENSION_MODEL_CONDITIONAL_NOT_FIELD_VALIDATION",
       n_papers=28,n_groups=40,n_scored_entries=310,scenario_count=10,
       source_inversion_anchors={d:dict(zip(CAP_PERCENT,INV_ANCHORS[d])) for d in DEFS},
       source_crosscheck=dict(n_original_frozen_costs_checked=1550,
           nested_cap_and_form_feasibility=True),
       previous_six_scenario=dict(certified5=sum(r["robust6_certified5"] for r in records),
           still_certified5_under_all10_using_same_6_optimum=sum(r["robust6_within5_under_all10"] for r in records),
           same_optimum_choice_after_factorial=sum(r["robust10_same_choice_as_6"] for r in records),
           same_material_after_factorial=sum(r["robust10_same_material_as_6"] for r in records)),
       fully_crossed_ten=dict(certified5=sum(r["robust10_certified5"] for r in records),
           certified10=sum(r["robust10_certified10"] for r in records),
           certified0=sum(r["robust10_exact0"] for r in records),
           median_worst_risk=median_finite(records,"robust10_worst_regret"),
           certified5_excluding_Bansode=sum(r["robust10_certified5"] for r in records if r["doi"]!=BANSODE),
           groups_excluding_Bansode=sum(r["doi"]!=BANSODE for r in records),
           certified5_paper_ci95=quantile_ci(records,"robust10_certified5"),
           mean_robust_risk_increase=statistics.mean(r["robust10_risk_increase_over_6"] for r in records),
           median_robust_risk_increase=statistics.median(r["robust10_risk_increase_over_6"] for r in records)),
       perfect_information_counters=dict(
           form_known_gt5pp=sum(r["form_info_gt5pp"] for r in records),
           cap_known_gt5pp=sum(r["cap_info_gt5pp"] for r in records),
           form_known_positive=sum(r["form_info_positive"] for r in records),
           cap_known_positive=sum(r["cap_info_positive"] for r in records),
           form_more_benefit=sum(r["form_more_valuable"] for r in records),
           cap_more_benefit=sum(r["cap_more_valuable"] for r in records),
           equal_benefit=sum(not r["form_more_valuable"] and not r["cap_more_valuable"] for r in records),
           form_info_5pp_bootstrap=quantile_ci(records,"form_info_gt5pp"),
           cap_info_5pp_bootstrap=quantile_ci(records,"cap_info_gt5pp"),
           median_form_gain=statistics.median(r["form_information_gain"] for r in records),
           median_cap_gain=statistics.median(r["cap_information_gain"] for r in records)),
       fixed_policies={},
       source_paths={},
       caveats=["All 10 scenarios are deterministic outputs of the same engineering cost surrogate, not externally verified industrial plants.",
                "Full crossed scenario set spans 5%-10% input cap; these caps are not empirically established as all equally plausible.",
                "No prior over models, experiment likelihood, or experiment costs: reported regret reduction is not Bayesian value of information.",
                "The 10-scenario retrospective minimax requires the COSTS of all 10 models; no claim of cheap laboratory predictor.",
                "Models differ in whether reactive recycled CO counts in the reactor inlet constraint. This is an engineering convention, not a molecule's intrinsic inertness."])
    for name in ("original_STY","max_selectivity","S5_cost","S6_assumed","true_inert_assumed"):
        finite=[float(r[name+"_risk10"]) for r in records if r[name+"_risk10"]!="INF"]
        summary["fixed_policies"][name]=dict(guaranteed5=sum(r[name+"_within5"] for r in records),
                nonfinite=len(records)-len(finite),median_finite_risk=statistics.median(finite) if finite else None)
    for d in DEFS:
        selected=[p for p in paths if p["definition"]==d]
        summary["source_paths"][d]=dict(point_switch_groups=sum(p["n_point_switches"]>0 for p in selected),
             material_switch_groups=sum(p["n_material_switches"]>0 for p in selected),
             material_reentrant_groups=sum(p["material_reentry"] for p in selected),
             nontrivial_regret_gt1_groups=sum(p["economically_gt1pct_switches"]>0 for p in selected),
             nontrivial_regret_gt5_groups=sum(p["economically_gt5pct_switches"]>0 for p in selected))
    summary["greatest_form_information_cases"]=[
        dict(group=r["group"],doi=r["doi"],form_gain=r["form_information_gain"],
             cap_gain=r["cap_information_gain"],robust10_material=r["robust10_material"])
        for r in sorted(records,key=lambda z:-z["form_information_gain"])[:5]]
    summary["greatest_cap_information_cases"]=[
        dict(group=r["group"],doi=r["doi"],form_gain=r["form_information_gain"],
             cap_gain=r["cap_information_gain"],robust10_material=r["robust10_material"])
        for r in sorted(records,key=lambda z:-z["cap_information_gain"])[:5]]
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    m=summary
    lines=["# Fully crossed 5 inlet limits x 2 CO-constraint definitions (post-hoc registered extension)","",
      "The earlier six-case comparison intentionally used a single alternative CO-exclusion cap. The source actually includes the other four alternative limits too, so this complete 10-case comparison supersedes that **asymmetric sensitivity** as the main structural stress test.",
      "", "| Model-defined decision | Groups with worst-case regret <= 5% |",
      "|---|---:|",
      f"| Retrospective minimax, six-case incomplete form coverage | {m['previous_six_scenario']['certified5']}/40 |",
      f"| Retrospective minimax, FULL ten-case factorial | {m['fully_crossed_ten']['certified5']}/40 |"]
    for name,detail in m["fixed_policies"].items():
        lines.append(f"| {name} fixed candidate across ten cases | {detail['guaranteed5']}/40 |")
    info=m["perfect_information_counters"]
    lines+=["","## Perfect knowledge counterfactuals (NOT field value of information)",
      f"Perfectly learning definition with cap still unknown reduces worst-case relative regret >5 percentage points in {info['form_known_gt5pp']}/40; perfectly learning cap while form is unknown: {info['cap_known_gt5pp']}/40.",
      f"Definition information has greater mathematical payoff in {info['form_more_benefit']} groups, cap information in {info['cap_more_benefit']}, equal in {info['equal_benefit']}.",
      "These comparisons assume oracle revelation and zero measurement cost, not scientifically available observation channels or probabilities.",
      "","## Path switching by model form"]
    for name,p in m["source_paths"].items():
        lines.append(f"- {name}: {p['point_switch_groups']}/40 exact-point switching, {p['material_switch_groups']}/40 formulation switching, {p['material_reentrant_groups']}/40 formulation re-entry")
    lines+=["","No new catalyst data, no experimental model selection, and no independent plant validation were carried out.",
       "All original 40-group and per-candidate cost consistency assertions passed."]
    (out/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    dest=args.out.resolve();dest.mkdir(parents=True,exist_ok=True)
    run(dest)
