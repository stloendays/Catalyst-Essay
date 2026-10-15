"""Read-only, preregistered decision and physical-evidence audit. Python stdlib only."""
from __future__ import annotations
import argparse, collections, csv, json, math, random, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = Path(__file__).resolve().parent
LIMITS = ("lim5", "lim6", "S6", "lim8", "lim10")
ALL = ("S5", "S6", "lim4", "lim5", "lim6", "lim8", "lim10", "lim12", "lim15", "lim20", "lim25", "lim30")
COLUMNS = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}
COLUMNS.update({f"lim{x}": f"cost_recycled_opt_lim{x}" for x in (4, 5, 6, 8, 10, 12, 15, 20, 25, 30)})
ANCHORS = {"S5": 15, "S6": 28}

def load(path):
    with (ROOT / path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write(out, name, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else ["empty"]
    with (out / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def num(value):
    try:
        f = float(value)
        return f if math.isfinite(f) else math.inf
    except (TypeError, ValueError):
        return math.inf

def require(test, reason):
    if not test: raise AssertionError(reason)

def bygroup(rows):
    groups = collections.defaultdict(list)
    for r in rows: groups[r["group"]].append(r)
    return dict(groups)

def source():
    raw_rows = load("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
    # The 351-row source includes singletons; frozen printed evaluation is 310 entries in 40 scored groups.
    allowed = {r["group"] for r in load("analysis/meoh_literature_inversion_2026_10_05/group_metrics_inlet_limit.csv")}
    rows = [r for r in raw_rows if r["group"] in allowed]
    groups = bygroup(rows)
    require(len(rows) == 310 and len(groups) == 40, f"frozen cohort changed: {len(rows)}, {len(groups)}")
    require(len({x["doi"] for x in rows}) == 28, "paper count changed")
    require(all(len({z["catalyst"] for z in rs}) == len(rs) for rs in groups.values()), "duplicate group+candidate identity")
    frozen = load("analysis/meoh_constraint_boundary_2026_10_12/boundary_groups.csv")
    frozen_by = {(r["scenario"], r["group"]): r for r in frozen}
    require(len(frozen_by) == len(frozen), "duplicate boundary verdict")
    for s in ALL:
        require(sum(z["scenario"] == s for z in frozen) == 40, f"missing boundary scenario {s}")
    for s, want in ANCHORS.items():
        n = sum(r["mismatch"].strip().lower() == "true" for r in frozen if r["scenario"] == s)
        require(n == want, f"boundary anchor {s} {n}!={want}")
    return groups, frozen_by

def selections(groups, boundary):
    outputs={}
    for group, entries in groups.items():
        # Preserve the frozen upstream winner and its tie-breaking convention exactly.
        lab_name = boundary[("S5",group)]["lab_leader"]
        matched = [r for r in entries if r["catalyst"] == lab_name]
        require(len(matched)==1,f"frozen STY winner missing or ambiguous {group}")
        lab = matched[0]
        choices={}
        for scenario in ALL:
            col=COLUMNS[scenario]
            finite=[r for r in entries if math.isfinite(num(r[col]))]
            require(finite, f"all candidates infeasible in {group}/{scenario}")
            old=boundary[(scenario,group)]
            selected=[r for r in finite if r["catalyst"]==old["plant_leader"]]
            require(len(selected)==1,f"published plant winner missing {group}/{scenario}")
            p=selected[0]
            # Published optimizer breaks exact-price ties by original candidate order.
            require(num(p[col])<=min(num(x[col]) for x in finite)+max(0.01,1e-6*num(p[col])),f"old winner not at minimum {group}/{scenario}")
            c_lab=num(lab[col])
            mismatch=p["catalyst"]!=lab["catalyst"]
            # Published group verdicts are computed with frozen tie conventions; crosscheck costs and mismatch.
            require(bool(old["mismatch"].lower()=="true")==mismatch,f"verdict mismatch {group}/{scenario}")
            require(abs(num(old["c_plant"])-num(p[col])) <= max(0.1,1e-4*num(p[col])),f"cost ledger {group}/{scenario}")
            choices[scenario]={"winner":p["catalyst"],"winner_material":p["catalyst_key"],
              "cost":num(p[col]),"lab_cost":c_lab,"mismatch":mismatch,
              "regret":max(0.0,c_lab/num(p[col])-1.0) if math.isfinite(c_lab) else math.inf,
              "lab_feasible":math.isfinite(c_lab)}
        outputs[group]={"doi":lab["doi"],"lab":lab,"choices":choices,"entries":entries}
    return outputs

def stable(choices,scenarios):
    verdicts=[choices[s]["mismatch"] for s in scenarios]
    winners=[choices[s]["winner"] for s in scenarios]
    materials=[choices[s]["winner_material"] for s in scenarios]
    return {"class":("inverted_all" if all(verdicts) else "preserved_all" if not any(verdicts) else "model_dependent"),
      "same_operating_point":len(set(winners))==1,"same_material":len(set(materials))==1,
      "worst_regret":max(choices[s]["regret"] for s in scenarios),
      "best_regret":min(choices[s]["regret"] for s in scenarios)}

def extra_model(data):
    rows=load("analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv")
    index={(r["group"],r["entry"]):r for r in rows}
    require(len(index)==len(rows),"duplicate alternative entries")
    require(sum(len(x["entries"]) for x in data.values())==len(rows),"alternative model lacks cohort entries")
    for group,b in data.items():
        finite=[]
        for r in b["entries"]:
            k=(group,r["entry"])
            require(k in index,f"missing alternative cost row {k}")
            cost=num(index[k]["cost_true_inert_6.86"])
            if math.isfinite(cost):finite.append((cost,r))
        require(finite,f"no finite alternative choices {group}")
        cost,p=min(finite,key=lambda z:(z[0],z[1]["catalyst"]))
        lab_cost=num(index[(group,b["lab"]["entry"])]["cost_true_inert_6.86"])
        b["choices"]["true_inert_S6"]={"winner":p["catalyst"],"winner_material":p["catalyst_key"],
          "cost":cost,"lab_cost":lab_cost,"mismatch":p["catalyst"]!=b["lab"]["catalyst"],
          "regret":max(0.,lab_cost/cost-1) if math.isfinite(lab_cost) else math.inf,
          "lab_feasible":math.isfinite(lab_cost)}
    total=sum(x["choices"]["true_inert_S6"]["mismatch"] for x in data.values())
    require(total==18,f"alternative definition anchor 18/40, got {total}")

def study2(out, data):
    extra_model(data)
    sets={"canonical_all":ALL, "published_limit_envelope":LIMITS,
      "model_form_at_6p86":("S5","S6","true_inert_S6"),
      "published_plus_model_form":(*LIMITS,"true_inert_S6")}
    rows=[]
    for group,b in sorted(data.items()):
        r={"group":group,"doi":b["doi"],"lab_catalyst":b["lab"]["catalyst"],"lab_material":b["lab"]["catalyst_key"]}
        for s,c in b["choices"].items():
            r.update({s+"_winner":c["winner"],s+"_material":c["winner_material"],
              s+"_inverted":int(c["mismatch"]),s+"_regret":c["regret"]})
        for name,scens in sets.items():
            t=stable(b["choices"],scens)
            r.update({name+"_"+k:v for k,v in t.items()})
        rows.append(r)
    write(out,"02_group_robustness.csv",rows)
    summary={"kind":"model_conditional_internal","groups":40,"papers":28,
      "anchors":{s:sum(b["choices"][s]["mismatch"] for b in data.values()) for s in ("S5","S6","true_inert_S6")}}
    for name,scens in sets.items():
        c=collections.Counter(stable(b["choices"],scens)["class"] for b in data.values())
        same=sum(stable(b["choices"],scens)["same_operating_point"] for b in data.values())
        same_mat=sum(stable(b["choices"],scens)["same_material"] for b in data.values())
        summary[name]={"scenarios":list(scens),"classification":dict(c),"same_operating_point":same,"same_material":same_mat}
        paper_ids=sorted({b["doi"] for b in data.values()})
        bypaper={p:[b for b in data.values() if b["doi"]==p] for p in paper_ids}
        rng=random.Random(20261015)
        samples=[]
        for _ in range(5000):
            selected=[bb for p in rng.choices(paper_ids,k=len(paper_ids)) for bb in bypaper[p]]
            samples.append(sum(stable(b["choices"],scens)["class"]=="inverted_all" for b in selected)/len(selected))
        samples.sort()
        summary[name]["inverted_all_bootstrap_ci95"]=[samples[124],samples[4874]]
    (out/"02_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    return summary

def leader_by(entries,method):
    eligible=[r for r in entries if math.isfinite(num(r["cost_recycled_opt_inlet"]))]
    require(eligible,"no S6-eligible candidates")
    if method=="STY":return max(eligible,key=lambda r:num(r["STY"]))
    if method=="S":return max(eligible,key=lambda r:(num(r["SMeOH"]),num(r["STY"])))
    raise ValueError(method)

def action_rule(entries,base,thr):
    bind=num(base["nonreactive_at_opt_recycled"])>0.0686*thr+1e-12
    return leader_by(entries,"S" if bind else "STY")

def rule_eval(b,kind,thr=1.0):
    entries=b["entries"]
    if kind=="threshold":chosen=action_rule(entries,b["lab"],thr)
    elif kind=="STY" and math.isfinite(num(b["lab"]["cost_recycled_opt_inlet"])):
        chosen=b["lab"]  # Original paper leaderboard includes tied winners; keep frozen primary choice.
    else:chosen=leader_by(entries,kind)
    winner=b["choices"]["S6"]["winner"]
    cost=num(chosen["cost_recycled_opt_inlet"])
    lowest=b["choices"]["S6"]["cost"]
    return {"correct":int(chosen["catalyst"]==winner),"regret":max(0.0,cost/lowest-1.0),
      "chosen":chosen["catalyst"],"chosen_material":chosen["catalyst_key"]}

def score_subset(subset,kind,thr=1.):
    rr=[rule_eval(b,kind,thr) for b in subset]
    return (sum(z["correct"] for z in rr)/len(rr),statistics.mean(z["regret"] for z in rr))

def study3(out,data):
    values=list(data.values())
    require(sum(rule_eval(b,"STY")["correct"] for b in values)==12,"S6 STY anchor 12/40")
    require(sum(rule_eval(b,"S")["correct"] for b in values)==23,"S6 selectivity anchor 23/40")
    candidates=[("threshold",x) for x in (.75,1.,1.25,1.5,2.)]+[("STY",0.),("S",0.)]
    paper_ids=sorted({b["doi"] for b in values})
    fold=[]
    for paper in paper_ids:
        train=[b for b in values if b["doi"]!=paper]
        test=[b for b in values if b["doi"]==paper]
        ranked=[]
        for order,(k,t) in enumerate(candidates):
            a,r=score_subset(train,k,t)
            ranked.append((-a,r,order,k,t))
        _,_,_,k,t=min(ranked)
        fold.append({"doi":paper,"chosen_rule":k,"threshold":t,"test_n":len(test)})
        for b in test:b["cv_method"],b["cv_threshold"]=k,t
    write(out,"03_folds.csv",fold)
    groups=[]
    for group,b in sorted(data.items()):
        lab=b["lab"]
        base=float(lab["nonreactive_at_opt_recycled"])
        s5_cost=float(lab["cost_recycled_opt"])
        s6_cost=float(lab["cost_recycled_opt_inlet"])
        dp=float(lab["purge_recycled_opt_inlet"])-float(lab["purge_recycled_opt"])
        proxy=base>0.0686+1e-12
        # A constrained optimum cannot have a lower objective than the unconstrained optimum.
        require(s6_cost+max(1e-5,1e-7*s5_cost)>=s5_cost,f"nested cost violated for {group}")
        if not proxy:
            require(abs(s5_cost-s6_cost)<=max(1e-4,1e-6*s5_cost),f"S5-feasible leader became more costly {group}")
        res={k:rule_eval(b,k) for k in ("STY","S")}
        res["cv"]=rule_eval(b,b["cv_method"],b["cv_threshold"])
        groups.append({"group":group,"doi":b["doi"],"lab":lab["catalyst"],
         "actual_inversion":int(b["choices"]["S6"]["mismatch"]),
         "near_infeasible":int(b["choices"]["S6"]["regret"]>1 or s6_cost>2*s5_cost),
         "activation_proxy":int(proxy),"s5_inlet":base,"s5_purge":num(lab["purge_recycled_opt"]),
         "s6_purge":num(lab["purge_recycled_opt_inlet"]),"purge_delta":dp,"s5_cost":s5_cost,
         "s6_cost":s6_cost,"cost_increase_ratio":s6_cost/s5_cost,
         "cv_rule":b["cv_method"],"cv_threshold":b["cv_threshold"],
         **{prefix+"_"+k:v for prefix,r in res.items() for k,v in r.items()}})
    write(out,"03_group_predictions.csv",groups)
    metrics={}
    for m in ("STY","S","cv"):
        metrics[m]={"accuracy":sum(r[m+"_correct"] for r in groups)/len(groups),
          "mean_regret":statistics.mean(r[m+"_regret"] for r in groups),
          "median_regret":statistics.median(r[m+"_regret"] for r in groups),
          "gt5pct_regret":sum(r[m+"_regret"]>.05 for r in groups)}
    summary={"kind":"internal_leave_one_paper_out_conditional","n_groups":40,"n_papers":len(paper_ids),
      "activation_proxy_count":sum(r["activation_proxy"] for r in groups),
      "proxy_inversion_table":{f"{a}_{b}":sum(r["activation_proxy"]==a and r["actual_inversion"]==b for r in groups)
        for a in (0,1) for b in (0,1)},
      "rules":metrics,"selected_rules":dict(collections.Counter(f"{r['chosen_rule']}:{r['threshold']}" for r in fold)),
      "leakage_notice":"S6 feasibility oracle removes infeasible candidates as in frozen rule scoring; this is NOT lab-only deployment.",
      "sample_notice":"training, CV and scoring share the same 40 frozen papers and plant model; separate PR80 prospective check required"}
    (out/"03_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary

def study4(out):
    r=load("analysis/validation_nh3_plant_2026_10_13/nh3_1_2/results_metrics.csv")
    require(len(r)==64 and len({x["metric_id"] for x in r})==64,"NH3 64-row integrity")
    counts=collections.Counter(z["table"] for z in r)
    passes=collections.Counter(z["table"] for z in r if z["pass_"].lower()=="pass")
    expected={"A":(28,18),"B":(20,5),"C":(12,9),"E":(3,0),"V":(1,0)}
    require({k:(counts[k],passes[k]) for k in expected}==expected,"NH3 locked prereg verdict changed")
    for z in r:
        require(z["pass_"].lower() in ("pass","fail"),"unknown verdict")
        # Published benchmarks legitimately use source ranges/windows/boolean verdicts; never coerce them to floats.
        require(bool(z["industrial"].strip()) and bool(z["model"].strip()),f"missing registered comparator {z['metric_id']}")
    write(out,"04_industrial_metric_ledger.csv",r)
    pressures={"Fe_Dyson_Simon_bar":[149*1.01325,309*1.01325],
      "RuC_Rossetti_bar":[50.,100.]}
    require(pressures["Fe_Dyson_Simon_bar"][0]>pressures["RuC_Rossetti_bar"][1],"source domains overlap unexpectedly")
    bridge=load("analysis/nh3_loop_reconciliation_2026_10_14/outputs/t3_points.csv")
    group=collections.defaultdict(dict)
    for z in bridge:
        k=(z["pair"],z["model_basis"])
        require(z["catalyst"] in ("Fe","Ru"),"unsupported bridge formulation")
        require(z["catalyst"] not in group[k],"duplicate catalyst bridge result")
        group[k][z["catalyst"]]=z
    rows=[]
    for (pair,basis),cases in sorted(group.items()):
        require(set(cases)=={"Fe","Ru"},f"not a complete model pair {pair}/{basis}")
        fe,ru=cases["Fe"],cases["Ru"]
        costdiff=num(ru["total_USD_t"])-num(fe["total_USD_t"])
        require(math.isfinite(costdiff),"non-finite paired cost")
        fp,rp=num(fe["P_bar"]),num(ru["P_bar"])
        rows.append({"pair":pair,"model_basis":basis,"Fe_P_bar":fp,"Ru_P_bar":rp,
          "Fe_source_pressure_valid":pressures["Fe_Dyson_Simon_bar"][0]<=fp<=pressures["Fe_Dyson_Simon_bar"][1],
          "Ru_source_pressure_valid":50<=rp<=100,"delta_Ru_minus_Fe_USD_t":costdiff,
          "preferred":"Fe" if costdiff>0 else "Ru" if costdiff<0 else "tie"})
    write(out,"04_kinetic_model_bridge.csv",rows)
    t1=load("analysis/nh3_loop_reconciliation_2026_10_14/outputs/t1_metals.csv")
    pressure_checks=[]
    for z in t1:
        pressure_checks.append({"metal":z["metal"],"recycle_rise_bar":z["recycle_pressure_rise_bar"],
          "cost_USD_t":z["cost_USD_t"],"rank":z["censored_rank"],
          "kinetics_type":"descriptor; do NOT apply measured Fe/Ru domain"})
    write(out,"04_descriptor_rise.csv",pressure_checks)
    with (ROOT/"analysis/nh3_loop_reconciliation_2026_10_14/outputs/t5.json").open() as f: energy=json.load(f)
    e=energy["energy_comparison"]
    require(e["same_sign"] is False and e["delta_loop_electricity_GJ_t"]<0 and
      e["published_KAAP_saving_GJ_t"]>0,"KAAP electricity discrepancy changed")
    summary={"scope":"diagnostic; NO new industrial validation or correction","metrics_total":len(r),
      "passes":sum(passes.values()),"categories":{k:{"total":v[0],"pass":v[1],
      "failed_ids":[z["metric_id"] for z in r if z["table"]==k and z["pass_"]=="FAIL"]} for k,v in expected.items()},
      "source_pressure_ranges":pressures,"pressure_range_overlap":False,
      "bridge_model_basis_pairs":len(rows),"bridge_pairs_with_both_source_valid":sum(x["Fe_source_pressure_valid"] and x["Ru_source_pressure_valid"] for x in rows),
      "energy_comparison":{"published_KAAP_saving_GJ_t":e["published_KAAP_saving_GJ_t"],
        "modeled_KAAP_saving_GJ_t":e["delta_loop_electricity_GJ_t"],
        "same_sign":e["same_sign"],"diagnostic":"reported plant and model comparison scopes may differ"},
      "caveat":"source-pressure validity does not imply mixture, temperature, heat-transfer, unit-operation or process validation"}
    (out/"04_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--study",choices=("all","2","3","4"),default="all")
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    results={}
    if args.study in ("all","2","3"):
        groups,boundary=source();data=selections(groups,boundary)
        if args.study in ("all","2"):results["study2"]=study2(out,data)
        if args.study in ("all","3"):results["study3"]=study3(out,data)
    if args.study in ("all","4"):results["study4"]=study4(out)
    (out/"summary.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:{p:v for p,v in z.items() if p in ("anchors","rules","passes","n_groups","metrics_total")} for k,z in results.items()},indent=2))

if __name__=="__main__":
    main()
