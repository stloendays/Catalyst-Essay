#!/usr/bin/env python3
"""Read-only model-conditioned catalyst minimax regret and cap-transition topology."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261015
BANSODE = "10.1039/c2cy20604h"
CAPS = ("lim5", "lim6", "S6", "lim8", "lim10")
FORM = ("S6", "true_inert_S6")
AUGMENTED = CAPS + ("true_inert_S6",)
ALL12 = ("S5", "lim4", "lim5", "lim6", "S6", "lim8", "lim10",
         "lim12", "lim15", "lim20", "lim25", "lim30")
SCENARIO_COLUMN = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}
SCENARIO_COLUMN.update({f"lim{n}":f"cost_recycled_opt_lim{n}" for n in
                       (4,5,6,8,10,12,15,20,25,30)})
SETS = {"augmented_six": AUGMENTED, "canonical_five": CAPS,
        "two_forms_6p86": FORM, "canonical_twelve": ALL12}
TOL = 1e-6
ZERO = 1e-7


def require(condition, reason):
    if not condition: raise AssertionError(reason)


def read(path):
    with (ROOT / path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def save(path, rows):
    rows = list(rows)
    require(rows, "empty output "+str(path))
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction="ignore")
        w.writeheader();w.writerows(rows)


def val(text):
    try:
        x=float(text)
        return x if math.isfinite(x) and x>0 else math.inf
    except (ValueError,TypeError):
        return math.inf


def fmt(x):
    return x if isinstance(x,(float,int)) and math.isfinite(x) else "INF"


def load():
    original=read("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
    selected_groups={r["group"] for r in
      read("analysis/meoh_literature_inversion_2026_10_05/group_metrics_inlet_limit.csv")}
    require(len(original)==351 and len(selected_groups)==40,"cohort source drift")
    scored={i:r for i,r in enumerate(original) if r["group"] in selected_groups}
    bygroup=defaultdict(list)
    for i,r in scored.items():
        bygroup[r["group"]].append(i)
    require(len(scored)==310 and len(bygroup)==40 and len({r["doi"] for r in scored.values()})==28,
            "scored 40-group/310-entry/28-paper source changed")
    require(all(len(ids)>=2 for ids in bygroup.values()),"singleton retained")
    require(all(len(set((scored[i]["group"],scored[i]["entry"]) for i in ids))==len(ids)
                for ids in bygroup.values()),"duplicate group/entry")

    existing=read("analysis/meoh_constraint_boundary_2026_10_12/boundary_groups.csv")
    old={(r["scenario"],r["group"]):r for r in existing}
    require(len(old)==len(existing),"duplicate boundary outcome")
    for scenario,n in (("S5",15),("S6",28)):
        require(sum(x["mismatch"]=="True" for x in existing if x["scenario"]==scenario)==n,
                f"frozen {scenario} inversion count changed")
    for s in ALL12:
        require(sum(x["scenario"]==s for x in existing)==40,"missing canonical scenario "+s)
    for s in SCENARIO_COLUMN:
        for g,ids in bygroup.items():
            winner=int(old[(s,g)]["plant_idx"])
            lab=int(old[(s,g)]["lab_idx"])
            require(winner in ids and lab in ids,"published group entry identity changed")
            costs=[val(scored[i][SCENARIO_COLUMN[s]]) for i in ids]
            require(any(math.isfinite(z) for z in costs),"all-infeasible group "+s+g)
            Jstar=min(costs);chosen=val(scored[winner][SCENARIO_COLUMN[s]])
            require(chosen<=Jstar+max(.01,1e-6*Jstar),"published winner disagrees with original costs")
            require(abs(float(old[(s,g)]["c_plant"])/chosen-1)<1e-6,
                    "published cost does not match chosen entry")
    # Check alternate source has exact one-to-one entry coverage for all 310 scored entries.
    alternate=read("analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv")
    byid={(r["group"],r["entry"]):r for r in alternate}
    require(len(alternate)==len(byid),"ambiguous alternative candidate identity")
    truecost={}
    for i,r in scored.items():
        key=(r["group"],r["entry"])
        require(key in byid,"missing alternate scenario cost "+str(key))
        truecost[i]=val(byid[key]["cost_true_inert_6.86"])
    altrows=[r for r in read("analysis/meoh_inlet_definition_2026_10_12/scan_groups.csv")
             if r["definition"]=="true_inert" and r["limit"]=="6.86"]
    alt={r["group"]:r for r in altrows}
    require(len(altrows)==40 and len(alt)==40 and
      sum(r["mismatch"]=="True" for r in altrows)==18,
      "alternative model form source anchor changed (18/40)")
    altwinner={}
    for g,ids in bygroup.items():
        matching=[i for i in ids if scored[i]["catalyst"]==alt[g]["plant_leader"]]
        require(len(matching)==1,"ambiguous alternative model plant leader "+g)
        winner=matching[0]
        finite=[truecost[i] for i in ids if math.isfinite(truecost[i])]
        require(finite,"no viable alternative scenario "+g)
        require(truecost[winner]<=min(finite)+max(.01,1e-6*min(finite)),
          "published alternative model winner not cost-optimal "+g)
        altwinner[g]=winner
    costs={i:{s:val(r[col]) for s,col in SCENARIO_COLUMN.items()}|
             {"true_inert_S6":truecost[i]} for i,r in scored.items()}
    winners={(s,g):int(old[(s,g)]["plant_idx"]) for s in ALL12 for g in bygroup}
    winners.update({("true_inert_S6",g):idx for g,idx in altwinner.items()})
    for s in (*ALL12,"true_inert_S6"):
        require(sum(winners[s,g] in ids for g,ids in bygroup.items())==40,"missing scenario source winner")
    return scored,dict(bygroup),old,alt,costs,winners


def regret(cost,minimum):
    require(minimum>0 and math.isfinite(minimum),"invalid scenario minimum")
    if not math.isfinite(cost):return math.inf
    r=cost/minimum-1.0
    require(r>=-TOL, f"negative model regret {r}")
    return max(0.0,r)


def scenarios_for_group(ids,costs,scenarios):
    return {s:min(costs[i][s] for i in ids) for s in scenarios}


def all_risks(ids,costs,scenarios):
    minimum=scenarios_for_group(ids,costs,scenarios)
    return {i:max(regret(costs[i][s],minimum[s]) for s in scenarios)
            for i in ids}


def minimax(ids,costs,scenarios):
    risks=all_risks(ids,costs,scenarios)
    finite=[i for i in ids if math.isfinite(risks[i])]
    if not finite:return None,math.inf,risks
    best=min(finite,key=lambda i:(risks[i],i))
    return best,risks[best],risks


def quantile_ci(rows,field):
    groups=sorted({r["doi"] for r in rows})
    pmap={p:[r for r in rows if r["doi"]==p] for p in groups}
    rng=random.Random(SEED)
    draws=[]
    for _ in range(5000):
        rs=[r for p in rng.choices(groups,k=len(groups)) for r in pmap[p]]
        draws.append(sum(float(r[field]) for r in rs)/len(rs))
    draws.sort()
    return [draws[124],draws[4874]]


def percentile(rows):
    if not rows:return None
    return statistics.median(rows)


def policy_choices(g,ids,scored,old,winners):
    original=int(old[("S5",g)]["lab_idx"])
    sty_select=sorted(ids,key=lambda i: (-float(scored[i]["SMeOH"]),
                                      -float(scored[i]["STY"]),i))[0]
    return {"original_STY":original,"max_selectivity":sty_select,
            "S5_cost":winners[("S5",g)],
            "S6_assumed":winners[("S6",g)],
            "true_inert_assumed":winners[("true_inert_S6",g)]}


def study_decision(out, scored,bygroup,old,costs,winners):
    records=[]
    for g,ids in sorted(bygroup.items()):
        decision={}
        for label,scenarios in SETS.items():
            best,risk,risks=minimax(ids,costs,scenarios)
            equivalent=[i for i in ids if risks[i]<=.05+1e-12]
            tight=[i for i in ids if math.isfinite(risks[i]) and
                   abs(risks[i]-risk)<=1e-10]
            decision[label]=dict(winner=best,risk=risk,risks=risks,
                 equivalent=equivalent,tight=tight,
                 common_feasible=sum(math.isfinite(z) for z in risks.values()))
        base=policy_choices(g,ids,scored,old,winners)
        full=decision["augmented_six"];cap=decision["canonical_five"]
        form=decision["two_forms_6p86"]
        row=dict(group=g,doi=scored[ids[0]]["doi"],n_candidates=len(ids),
          robust_id=full["winner"],robust_entry=scored[full["winner"]]["entry"] if full["winner"] is not None else "",
          robust_material=scored[full["winner"]]["catalyst_key"] if full["winner"] is not None else "",
          worst_regret_full=fmt(full["risk"]),worst_regret_cap_only=fmt(cap["risk"]),
          worst_regret_form_6p86=fmt(form["risk"]),
          worst_regret_full12=fmt(decision["canonical_twelve"]["risk"]),
          n_common_feasible_full=full["common_feasible"],
          robust_minimax_ties=len(full["tight"]),
          n_candidates_at_5pct_risk=len(full["equivalent"]),
          n_distinct_materials_at_5pct=len({scored[i]["catalyst_key"] for i in full["equivalent"]}),
          decision_equiv_5pct=int(bool(full["equivalent"])),
          robust_5pct=int(full["risk"]<=.05+1e-12),
          robust_10pct=int(full["risk"]<=.10+1e-12),
          robust_exact_zero=int(full["risk"]<=ZERO),
          robust_cap_5pct=int(cap["risk"]<=.05+1e-12),
          form_knowledge_reduction=fmt(max(0.,full["risk"]-cap["risk"])) if all(math.isfinite(x) for x in (full["risk"],cap["risk"])) else "INF",
          form_knowledge_material_5pp=int(full["risk"]-cap["risk"]>.05) if all(math.isfinite(x) for x in (full["risk"],cap["risk"])) else None,
          model_form_resolution_changes_point=int(full["winner"]!=cap["winner"]),
          canonical_cap_perfect_knowledge_ceiling=fmt(cap["risk"]),
          two_form_perfect_knowledge_ceiling=fmt(form["risk"]),
          full_worst_scenarios=";".join(s for s in AUGMENTED
                         if full["winner"] is not None and
                         abs(regret(costs[full["winner"]][s],min(costs[i][s] for i in ids))-full["risk"])<=1e-8)
                         if full["winner"] is not None else "",
          robust_scenario_wins=sum(full["winner"]==winners[(s,g)] for s in AUGMENTED))
        for label,d in decision.items():
            chosen=d["winner"]
            row[label+"_point_id"]=chosen
            row[label+"_material"]=scored[chosen]["catalyst_key"] if chosen is not None else ""
            row[label+"_risk"]=fmt(d["risk"])
        for label,idx in base.items():
            row[label+"_id"]=idx
            row[label+"_material"]=scored[idx]["catalyst_key"]
            row[label+"_worst_regret"]=fmt(full["risks"][idx])
            row[label+"_certified_5pct"]=int(full["risks"][idx]<=.05+1e-12)
        records.append(row)
    save(out/"01_robust_group_decisions.csv",records)
    summary=dict(kind="MODEL_CONDITIONAL_ROBUST_ORACLE__NOT_PROSPECTIVE",
        scenario_sets={k:list(v) for k,v in SETS.items()},
        frozen_anchors={"groups":40,"entries":310,"papers":28,
                        "S5_STY_inversion":15,"S6_STY_inversion":28,"true_inert_STY_inversion":18},
        robust_primary=dict(
          full_feasible_groups=sum(r["n_common_feasible_full"]>0 for r in records),
          certified_5pct_groups=sum(r["robust_5pct"] for r in records),
          certified_10pct_groups=sum(r["robust_10pct"] for r in records),
          certified_exact0_groups=sum(r["robust_exact_zero"] for r in records),
          median_worst_regret=percentile([float(r["worst_regret_full"]) for r in records
                   if r["worst_regret_full"]!="INF"]),
          median_worst_regret_without_Bansode=percentile([float(r["worst_regret_full"]) for r in records
                if r["doi"]!=BANSODE and r["worst_regret_full"]!="INF"]),
          certified_5pct_fraction_cluster_CI95=quantile_ci(records,"robust_5pct"),
          ambiguous_form_material5pp_groups=sum(r["form_knowledge_material_5pp"]==1 for r in records),
          ambiguous_form_material5pp_fraction_cluster_CI95=quantile_ci(records,"form_knowledge_material_5pp"),
          form_resolution_changes_point_groups=sum(r["model_form_resolution_changes_point"] for r in records),
          form_knowledge_positive_reduction_groups=sum(
              r["form_knowledge_reduction"]!="INF" and float(r["form_knowledge_reduction"])>1e-9 for r in records),
          form_resolution_5pp_reduction_groups=sum(r["form_knowledge_material_5pp"]==1 for r in records),
          median_form_knowledge_risk_reduction=percentile([float(r["form_knowledge_reduction"])
                for r in records if r["form_knowledge_reduction"]!="INF"]),
          median_cap_five_perfect_knowledge_ceiling=percentile([float(r["worst_regret_cap_only"]) for r in records
                if r["worst_regret_cap_only"]!="INF"]),
          zero_common_feasible_groups=[r["group"] for r in records if r["n_common_feasible_full"]==0]),
        baselines={})
    for name in ("original_STY","max_selectivity","S5_cost","S6_assumed","true_inert_assumed"):
        finite=[float(r[name+"_worst_regret"]) for r in records if r[name+"_worst_regret"]!="INF"]
        summary["baselines"][name]=dict(
          n_unbounded=sum(r[name+"_worst_regret"]=="INF" for r in records),
          median_finite_worst_regret=percentile(finite),
          n_certified_5pct=sum(r[name+"_certified_5pct"] for r in records))
    for label in ("augmented_six","canonical_five","two_forms_6p86","canonical_twelve"):
        v=[float(r[label+"_risk"]) for r in records if r[label+"_risk"]!="INF"]
        summary[label+"_risk"]=dict(
          n_finite=len(v),median=percentile(v),
          n_worst_le_5pct=sum(r[label+"_risk"]!="INF" and float(r[label+"_risk"])<=.05+1e-12 for r in records))
    require(all((float(r["worst_regret_full"]) +1e-9>=
          float(r["worst_regret_cap_only"])) for r in records
          if r["worst_regret_full"]!="INF" and r["worst_regret_cap_only"]!="INF"),
          "information reveal monotonicity: full < cap")
    require(all((float(r["worst_regret_full"]) +1e-9>=
          float(r["worst_regret_form_6p86"])) for r in records
          if r["worst_regret_full"]!="INF" and r["worst_regret_form_6p86"]!="INF"),
          "information reveal monotonicity: full < form")
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Minimax catalyst selection under model-form ambiguity (exploratory)", "",
           "Only the existing source-model candidate operating points and per-candidate cost surfaces enter this robust decision certificate.",
           "", "| Policy (same candidate for all six scenarios) | Groups with worst-case regret <=5% | Groups with nonfinite worst-case risk | Finite median worst-case regret |",
           "|---|---:|---:|---:|"]
    lines.append(f"| Minimax oracle (6 scenarios) | {summary['robust_primary']['certified_5pct_groups']}/40 | {40-summary['robust_primary']['full_feasible_groups']} | {summary['robust_primary']['median_worst_regret']:.3f} |")
    for name,v in summary["baselines"].items():
        med="NA" if v["median_finite_worst_regret"] is None else f"{v['median_finite_worst_regret']:.3f}"
        lines.append(f"| {name} | {v['n_certified_5pct']}/40 | {v['n_unbounded']} | {med} |")
    lines.extend(["","The minimax oracle USES all six scenario cost outcomes to choose the retrospective robust winner. It is not a one-shot, laboratory-only or prospective predictor.",
       f"Learning whether CO counts leaves canonical cap uncertainty; it reduces >5 percentage points of worst-case modeled risk in {summary['robust_primary']['form_resolution_5pp_reduction_groups']}/40 groups (conditional, not experimental EVI).",
       "Full-case regret is relative and dimensionless, not the validated total ammonia or methanol plant cost.",
       "True-inert data exist only at one cap in the specified augmented set; model-form and limit-resolution benefits cannot be directly compared as if fully crossed physical alternatives.",
       "No model-probability distribution, experiment cost, real measured response or partial-observation likelihood was assumed.", ""])
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    return summary


def has_reentry(seq):
    # A-B-A, not necessarily consecutive; prevent counting repeated contiguous identical winners.
    collapsed=[seq[0]]
    for x in seq[1:]:
        if x!=collapsed[-1]:collapsed.append(x)
    return len(set(collapsed))<len(collapsed)


def study_paths(out,scored,bygroup,old,costs,winners):
    for i,d in scored.items():
        seq=[costs[i][s] for s in CAPS]
        for earlier,later in zip(seq[:-1],seq[1:]):
            require(not(math.isfinite(earlier) and not math.isfinite(later)),
                    f"nested feasibility violation row {i}")
            if math.isfinite(earlier) and math.isfinite(later):
                require(earlier+max(1e-5,1e-6*earlier)>=later,
                        f"nested candidate cost monotonicity violation row {i}, {earlier}>{later}")
    records=[]
    transitions=[]
    for g,ids in sorted(bygroup.items()):
        path=[winners[(s,g)] for s in CAPS]
        mats=[scored[i]["catalyst_key"] for i in path]
        switches=sum(path[i]!=path[i-1] for i in range(1,len(path)))
        mswitches=sum(mats[i]!=mats[i-1] for i in range(1,len(mats)))
        large1=0;large5=0
        for j in range(1,len(CAPS)):
            s0,s1=CAPS[j-1],CAPS[j]
            oldi,newi=path[j-1:j+1]
            opt=costs[newi][s1]
            changed=oldi!=newi
            keep=regret(costs[oldi][s1],opt)
            require(not math.isinf(keep), "previously feasible point infeasible under looser cap")
            significant1=bool(changed and keep>.01)
            significant5=bool(changed and keep>.05)
            large1+=significant1;large5+=significant5
            transitions.append(dict(group=g,doi=scored[ids[0]]["doi"],
                from_scenario=s0,to_scenario=s1,old_point_id=oldi,new_point_id=newi,
                old_catalyst=scored[oldi]["catalyst"],new_catalyst=scored[newi]["catalyst"],
                point_switch=int(changed),material_switch=int(mats[j]!=mats[j-1]),
                old_point_regret_at_new_cap=keep,significant_1pct=int(significant1),
                significant_5pct=int(significant5),
                previous_scenario_min_cost=min(costs[i][s0] for i in ids),
                new_scenario_min_cost=opt))
        row=dict(group=g,doi=scored[ids[0]]["doi"],n=len(ids),
           n_unique_point_winners=len(set(path)),n_unique_material_winners=len(set(mats)),
           n_point_switches=switches,n_material_switches=mswitches,
           reentrant_point=int(has_reentry(path)),reentrant_material=int(has_reentry(mats)),
           switches_with_regret_gt1pct=large1,switches_with_regret_gt5pct=large5,
           sequence_point_ids=";".join(map(str,path)),
           sequence_materials=";".join(mats),
           sequence_catalyst_names=";".join(scored[i]["catalyst"] for i in path),
           sequence_cost_optima=";".join(f"{costs[i][s]:.9g}" for i,s in zip(path,CAPS)))
        records.append(row)
    save(out/"01_cap_path_groups.csv",records)
    save(out/"02_cap_switch_events.csv",transitions)
    interval={}
    for a,b in zip(CAPS[:-1],CAPS[1:]):
        t=[z for z in transitions if z["from_scenario"]==a and z["to_scenario"]==b]
        require(len(t)==40,"lost groups from transition")
        interval[f"{a}_to_{b}"]=dict(point_switches=sum(z["point_switch"] for z in t),
             material_switches=sum(z["material_switch"] for z in t),
             economically_material_gt1pct=sum(z["significant_1pct"] for z in t),
             economically_material_gt5pct=sum(z["significant_5pct"] for z in t))
    summary=dict(kind="RETROSPECTIVE_SOURCED_OPTIMAL_PATHS",
        costs_are_monotone_per_candidate=True,verified_candidate_count=len(scored),
        scenario_order=list(CAPS),groups=40,paired_transitions=len(transitions),
        source_anchor_S6_inversions=28,
        points_switch_once_or_more=sum(r["n_point_switches"]>0 for r in records),
        materials_switch_once_or_more=sum(r["n_material_switches"]>0 for r in records),
        point_reentrant_groups=sum(r["reentrant_point"] for r in records),
        material_reentrant_groups=sum(r["reentrant_material"] for r in records),
        switches_1pct_groups=sum(r["switches_with_regret_gt1pct"]>0 for r in records),
        switches_5pct_groups=sum(r["switches_with_regret_gt5pct"]>0 for r in records),
        point_reentrant_without_Bansode=sum(r["reentrant_point"] for r in records if r["doi"]!=BANSODE),
        material_reentrant_without_Bansode=sum(r["reentrant_material"] for r in records if r["doi"]!=BANSODE),
        by_cap_interval=interval)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Candidate-specific optimal-cost monotonicity versus winner switching", "",
       "The existing five nested cap optimizations have been verified point-by-point for all 310 candidate entries.",
       f"Among 40 groups, {summary['points_switch_once_or_more']} switch exact winning operating point and {summary['materials_switch_once_or_more']} switch catalyst formulation somewhere between the declared 5-10% caps.",
       f"Point re-entrance A-B-A: {summary['point_reentrant_groups']}/40 groups; material re-entrance: {summary['material_reentrant_groups']}/40.",
       "A nominal model switching because of a numerical tie is not automatically a decision-relevant effect: see >1% and >5% regret definitions.","",
       "| Cap change | Exact point changes | Material changes | >1% cost consequence | >5% cost consequence |",
       "|---|---:|---:|---:|---:|"]
    for interval_name,v in interval.items():
        lines.append(f"| {interval_name} | {v['point_switches']} | {v['material_switches']} | {v['economically_material_gt1pct']} | {v['economically_material_gt5pct']} |")
    lines.extend(["","Even though each fixed candidate gets no more expensive when a nested constraint is relaxed, the identity of the minimum-cost candidate may change more than once.",
         "This is not a universal thermodynamic theorem about reaction networks and does not validate the underlying cap definition.", ""])
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--study",choices=("decision","paths"),required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    scored,bygroup,old,alt,costs,winners=load()
    if args.study=="decision":s=study_decision(out,scored,bygroup,old,costs,winners)
    else:s=study_paths(out,scored,bygroup,old,costs,winners)
    print(json.dumps(s,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
