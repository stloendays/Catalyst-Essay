#!/usr/bin/env python3
"""Fe-first applicability audit: *distinct* experimentally reported kinetic P domains.

Stacked upon NH3-KINETIC-COST-v1 (PR #93). Fe source 149-309 atm, promoted
3.2wt% Ru/C source 50-100bar: NO COMMON SOURCE PRESSURE. Same product,
equipment/inert limits, priced-feed scenario, and physical loop equations.
Every failed phase solve, physical exclusion, and Ru-favorable economic scenario
is retained. This is not a same-P kinetic comparison or plant validation.
"""
from __future__ import annotations
import argparse,csv,json,sys,math
from dataclasses import replace,asdict
from itertools import product
from pathlib import Path
from collections import Counter
import numpy as np

HERE=Path(__file__).resolve().parent
UP=HERE.parent/"nh3_kinetic_cost_coupling_v1"
sys.path.insert(0,str(UP))
import run_study as BASE_RUN
import coupling as C
from economics import EconomicSettings, evaluate
from kinetic_bridge import hot_heat_per_mol_NH3

EXPERIMENTAL={"Fe":(149*1.01325,309*1.01325),"Ru":(50.,100.)}
TEMPERATURE_C={"Fe":(330.,495.),"Ru":(370.,460.)}
COMMON_T=(370.,460.)
MAX_INERT_PCT=15.
TEMPS=(400.,425.,445.,450.)
# This is an explicit limited expansion, not a claim of exhaustive continuous
# optimization. Both catalysts get source-window pressure opportunities.
ADDITIONS={
    "Fe":{"P":[235.,285.],"X":[.225,.25,.275],"T2":[0.,10.],"purge":[.0075,.015]},
    "Ru":{"P":[95.,100.],"X":[.08,.10,.12,.14],"T2":[-20.,-10.],"purge":[.0075,.01,.015]},
}
PRICE=replace(EconomicSettings(),H2_USD_kg=3.,N2_USD_kg=.06,ru_recovery=.90)


def ensure_source_domain(name,T_C,Pbar):
    lo,hi=EXPERIMENTAL[name]
    tl,th=TEMPERATURE_C[name]
    return lo<=Pbar<=hi and tl<=T_C<=th


def native(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def save(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False,default=native)+"\n",encoding="utf-8")


def cold_additions(cache,limit=0):
    baseline={d["state_id"]:d for d in cache["designs"] if d.get("record")}
    states=dict(baseline)
    unresolved=[]
    n=0
    for catalyst,g in ADDITIONS.items():
        for P,X,T2,pg in product(g["P"],g["X"],g["T2"],g["purge"]):
            state_id=BASE_RUN.grid_key(P,X,T2,pg)
            if state_id in states:continue
            d={"state_id":state_id,"P_bar":P,"X":X,"T2_C":T2,"purge":pg}
            d=BASE_RUN.cold_subprocess(d,PRICE.product_tpd)
            n+=1
            if d.get("record") is None:
                unresolved.append({"state_id":state_id,"reason":d.get("reason","UNSPECIFIED_NUMERIC_OR_PHASE_FAILURE"),"status":"UNRESOLVED_NOT_INFEASIBLE"})
            else:states[state_id]=d
            print("ADDITION",n,"accepted",len(states)-len(baseline),"unresolved",len(unresolved),flush=True)
            if limit and n>=limit:return states,unresolved,True
    return states,unresolved,False


def candidate_rows(states):
    passed=[];rejected=[]
    for state in states.values():
        P=state["P_bar"]
        for c in ("Fe","Ru"):
            if not EXPERIMENTAL[c][0]<=P<=EXPERIMENTAL[c][1]:continue
            setting=C.cold_settings(P,state["X"],state["T2_C"],state["purge"])
            for T in TEMPS:
                if not ensure_source_domain(c,T,P):continue
                try:r=C.candidate(c,T,P,setting,state["record"],PRICE)
                except Exception as exc:
                    rejected.append({"source_state":state["state_id"],"catalyst":c,"T_C":T,"why":type(exc).__name__+":"+str(exc)[:180]})
                    continue
                r["state_id"]=state["state_id"]
                # size_bed returns only {feasible:false, reason:...} for
                # equilibrium-infeasible states; source flags exist only on
                # a successfully integrated bed. Do not recast these expected
                # physical exclusions as pressure-domain software failures.
                r["source_TP_checked"]=ensure_source_domain(c,T,P)
                if r.get("feasible") and not (
                    r.get("rate_T_inside_source_range") and r.get("rate_P_inside_source_range")
                ):
                    raise AssertionError("Feasible bed contradicts pinned kinetic source domain")
                r["inert_bound_pct"]=MAX_INERT_PCT
                r["passes_inert_bound"]=float(r.get("inlet_inerts_pct",float("inf")))<=MAX_INERT_PCT+1e-10
                r["eligible"]=bool(r.get("feasible") and r["passes_inert_bound"])
                passed.append(r)
    return passed,rejected


def repriced(row,state,economics):
    if not row.get("eligible"):return None
    if row["bed_m3"]>economics.max_bed_m3:return None
    if not row["passes_inert_bound"]:return None
    copy=dict(state["record"])
    copy["isothermal_reaction_heat_removed_MW"]=(
        -copy["extent_kmol_h"]/3.6*hot_heat_per_mol_NH3(row["T_C"]+273.15)/1e6)
    return evaluate(row["catalyst"],row["bed_m3"],row["P_bar"],copy,economics)


def choose(rows,states,e):
    out={}
    for cat in ("Fe","Ru"):
        candidates=[]
        for row in rows:
            if row["catalyst"]!=cat:continue
            val=repriced(row,states[row["state_id"]],e)
            if val is not None:
                candidates.append((val["decision_relevant_cost_USD_t"],row,val))
        if not candidates:
            out[cat]=None
        else:
            _,row,cost=min(candidates,key=lambda v:v[0])
            out[cat]={"catalyst":cat,"state_id":row["state_id"],
                      "T_C":row["T_C"],"P_bar":row["P_bar"],
                      "X":row["X_design"],"cold_T2_C":row["T2_C"],
                      "purge":row["purge"],"bed_m3":row["bed_m3"],
                      "inlet_inerts_molpct":row["inlet_inerts_pct"],
                      "decision_USD_t":cost["decision_relevant_cost_USD_t"],
                      "gross_USD_t":cost["modeled_loop_cost_USD_t"],
                      "cost":cost,"source_TP_checked":row["source_TP_checked"]}
    return out


def writecsv(path,lines):
    if not lines:return
    keys=list(dict.fromkeys(k for row in lines for k,v in row.items() if not isinstance(v,(dict,list))))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for row in lines:w.writerow({k:row.get(k,"") for k in keys})


def main(outdir,baseline_dir,limit=0):
    if EXPERIMENTAL["Fe"][0]<=EXPERIMENTAL["Ru"][1]:
        raise AssertionError("Joint kinetic pressure source domain unexpectedly overlaps")
    base=json.loads((baseline_dir/"cold_cache.json").read_text(encoding="utf-8"))
    if len(base.get("designs",[]))!=32:
        raise AssertionError("Expected full registered 32 upstream source cold states")
    states,unresolved,partial=cold_additions(base,limit)
    rows,rejected=candidate_rows(states)
    nominal=choose(rows,states,PRICE)
    if partial:
        outdir.mkdir(parents=True,exist_ok=True)
        save(outdir/"partial.json",{"partial":True,"n_states":len(states),"new_unresolved":unresolved})
        print("PARTIAL: not scientific-complete",flush=True)
        return
    if any(v is None for v in nominal.values()):
        status="NO_BOTH_ELIGIBLE_CATALYSTS"
    else:
        status="BOTH_SOURCE_TP_PRESSURE_OPTIONS_EVALUATED"
    bridge={}
    gap=None
    if status=="BOTH_SOURCE_TP_PRESSURE_OPTIONS_EVALUATED":
        cats=nominal
        gap=cats["Ru"]["decision_USD_t"]-cats["Fe"]["decision_USD_t"]
        for key in ("excess_feed_USD_t","utility_USD_t","inventory_USD_t",
                    "reactor_annualized_USD_t","compressor_annualized_USD_t",
                    "hot_duty_scenario_USD_t"):
            bridge[key]=cats["Ru"]["cost"][key]-cats["Fe"]["cost"][key]
        if abs(sum(bridge.values())-gap)>3e-7:raise AssertionError("Cost terms do not explain gap")
    fin=[]
    for r,recovery,h2 in product((0.,.03,.08,.12,.2),(.9,.9555,1.),(1.,3.,6.)):
        e=replace(PRICE,metal_rate=r,ru_recovery=recovery,H2_USD_kg=h2)
        opt=choose(rows,states,e)
        g=None if any(v is None for v in opt.values()) else opt["Ru"]["decision_USD_t"]-opt["Fe"]["decision_USD_t"]
        fin.append({"finance":r,"recovery":recovery,"H2_USD_kg":h2,"Ru_minus_Fe_USD_t":g,
                    "winner":"NO_COMPARISON" if g is None else ("Fe" if g>0 else "Ru" if g<0 else "Tie")})
    caps={}
    for label,changes in (("zero_Ru_metal_price",{"Ru_USD_kg_metal":0.}),
                           ("full_metal_recovery",{"ru_recovery":1.}),
                           ("zero_finance",{"metal_rate":0.}),
                           ("bed_cap_60m3",{"max_bed_m3":60.})):
        opt=choose(rows,states,replace(PRICE,**changes))
        caps[label]={"Fe_cost":None if opt["Fe"] is None else opt["Fe"]["decision_USD_t"],
                     "Ru_cost":None if opt["Ru"] is None else opt["Ru"]["decision_USD_t"],
                     "Ru_minus_Fe":None if any(v is None for v in opt.values()) else opt["Ru"]["decision_USD_t"]-opt["Fe"]["decision_USD_t"]}
    outdir.mkdir(parents=True,exist_ok=True)
    data={"method":"SOURCE_FIT_TP_WINDOW_PROCESS_ECONOMICS_V1",
          "source_pressure_ranges_bar":EXPERIMENTAL,
          "source_pressure_overlap":False,
          "source_temperature_overlap_C":COMMON_T,
          "Fe_and_Ru_separately_optimized_P":True,
          "same_pressure_catalyst_claim_allowed":False,
          "price_basis":asdict(PRICE),
          "max_inlet_inerts_pct":MAX_INERT_PCT,
          "matched_product_tpd":PRICE.product_tpd,
          "original_canonical_score_unchanged":"32/64",
          "original_Fe_Ru_Os_prices_untouched":"11.516 / 16.633 / 19.747 USD/t (NH3-FINAL-1.2 different economic objective)",
          "cold_design_count":len(states),
          "numerically_unresolved_new_cold":unresolved,
          "new_hot_rejections":rejected,
          "source_valid_rate_sized_rows":len(rows),
          "inlet_inerts_eligible_rows":sum(bool(r["eligible"]) for r in rows),
          "science_state":status,
          "nominal_selected":nominal,"gap_Ru_minus_Fe_USD_t":gap,
          "Ru_minus_Fe_components":bridge,
          "finance_recovery_H2_scenarios":fin,
          "scenario_winners":dict(Counter(x["winner"] for x in fin)),
          "counterfactuals":caps,
          "important_limitations":["Source fitted Fe 149-309 atm and promoted Ru/C 50-100 bar pressures do not overlap",
          "Fe and Ru/C operate at different optimization pressure; no common-pressure intrinsic ranking claim",
          "Source fit T/P ranges alone do not validate full process/catalyst feed mixture or high-pressure flash",
          "Subambient SI S27 cold-temperature correlations may require extrapolation; original SI does not establish all mixture application conditions",
          "Finite catalog and engineered costs are not certified global plant optimum; source Ru/C at upper P is a boundary",
          "Some numerical unresolved states explicitly retained; not physical infeasibility",
          "PR92/P93 staged dependencies and old canonical hashes unchanged"] }
    save(outdir/"summary.json",data)
    writecsv(outdir/"source_domain_candidate_grid.csv",rows)
    writecsv(outdir/"finance_recovery_H2_45.csv",fin)
    md=["# Fe-first source-kinetic-pressure validity audit","",
        "**Distinct pressure design option comparison; NO overlapping fitted Fe/Ru pressure interval.**",
        "Fe: 149–309 atm; promoted 3.2wt% Ru/C: 50–100 bar. All options have the same 1500 t/d product, cost prices, 90 m3 bed and 15% inlet-inerts bounds. The 235bar Ru rate model remains an extrapolation, not an industrial validation.",
        "",
        "| Catalyst | P bar | T C | Cold T2 C | X N2 | purge | Bed m3 | Decision cost USD/t |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in ("Fe","Ru"):
        v=nominal[c]
        if v is None:md.append("| "+c+" | NO FEASIBLE | | | | | | |")
        else:md.append(f"| {c} | {v['P_bar']:.1f} | {v['T_C']:.1f} | {v['cold_T2_C']:.0f} | {v['X']:.3f} | {v['purge']:.4f} | {v['bed_m3']:.2f} | {v['decision_USD_t']:.3f} |")
    md+=["",f"**Ru−Fe:** {'NO COMPARABLE PAIR' if gap is None else format(gap,'+.3f')+' USD/t'} (reduced objective, common feed floor excluded).",
         "","## Mechanism", "| Cost term | Ru−Fe USD/t |","|---|---:|"]
    for k,v in bridge.items():md.append(f"| {k} | {v:+.3f} |")
    md+=["",f"45 economic settings: {data['scenario_winners']} **not probabilities**.",
         "","## Numerical and evidence limitations",
         f"New unresolved cold process states: {len(unresolved)}; hot excluded numerical/physical evaluations: {len(rejected)}. Failures retained; no fabricated pass.",
         "Same-pressure causal inference prohibited; identical source T/P validity cannot be simultaneously fulfilled for these two empirical rate laws.",
         "A new matched-pressure Fe vs Ru/CeO2 literature case is a separate formulation and must not be represented as promoted Ru/C.",
         "No original manuscript, frozen score or ranking overwritten.", ""]
    (outdir/"REPORT.md").write_text("\n".join(md),encoding="utf-8")
    print("\n".join(md),flush=True)
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out-dir",required=True,type=Path)
    p.add_argument("--baseline-dir",required=True,type=Path)
    p.add_argument("--limit",type=int,default=0)
    a=p.parse_args()
    main(a.out_dir,a.baseline_dir,a.limit)
