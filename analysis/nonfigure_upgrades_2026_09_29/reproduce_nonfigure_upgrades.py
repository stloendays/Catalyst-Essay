"""Reproduce non-figure decision-regret and descriptor-correlation sensitivity outputs.

Uses only frozen repository data. No DFT, process rerun, or LLM call.
"""
from __future__ import annotations
import csv, json, math, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/"provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"

def rows(path):
    with open(path,encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

# Decision regret.
res=json.loads((RUN/"results.json").read_text(encoding="utf-8"))
nh3=(res["deterministic"]["metals"]["Ru"]["feasible"]["total_cost"]-res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])/res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"]
meoh={r["candidate"]:r for r in rows(ROOT/"data/meoh/meoh_candidate_ranking_D01v3.csv")}
j_up=float(meoh["1 wt% Re | 250 C"]["NPC_EUR_t_2pct_purge"])
j_best=float(meoh["5 wt% Re | 200 C"]["NPC_EUR_t_2pct_purge"])
assert abs(nh3-0.44068926608899806)<1e-12
assert abs((j_up-j_best)/j_best-0.03359482667232064)<1e-12

# Frozen 673 K one-descriptor volcano.
sc=rows(RUN/"closure/scaling_reachability.csv")
x=[float(r["E_N_eV"]) for r in sc]
y=[math.log(float(r["gain_673K"])) for r in sc]

def interp(v):
    if v<=x[0]: return y[0]
    if v>=x[-1]: return y[-1]
    lo,hi=0,len(x)-1
    while hi-lo>1:
        m=(lo+hi)//2
        if x[m]<=v: lo=m
        else: hi=m
    t=(v-x[lo])/(x[hi]-x[lo])
    return y[lo]*(1-t)+y[hi]*t

cent={"Fe":-1.392120623747696,"Ru":-1.1333,"Os":-1.1095}
sig_fe=0.2271258177356984
half=0.15

def phi(z):
    return 0.5*(1+math.erf(z/math.sqrt(2)))

out=[]
for rho in (0,0.25,0.5,0.75,0.9):
    rng=random.Random(20260929+round(rho*1000))
    n=100000
    cnt={"Ru":0,"Os":0,"Fe":0}; full=0
    sr,si=math.sqrt(rho),math.sqrt(1-rho)
    for _ in range(n):
        g0=rng.gauss(0,1)
        z={m:sr*g0+si*rng.gauss(0,1) for m in ("Fe","Ru","Os")}
        E={
            "Fe":cent["Fe"]+sig_fe*z["Fe"],
            "Ru":cent["Ru"]+half*(2*phi(z["Ru"])-1),
            "Os":cent["Os"]+half*(2*phi(z["Os"])-1),
        }
        order=sorted(E,key=lambda m:interp(E[m]),reverse=True)
        cnt[order[0]]+=1
        full+=order==["Ru","Os","Fe"]
    out.append({
        "latent_pairwise_correlation":rho,"n_draws":n,
        "P_canonical_Ru_gt_Os_gt_Fe":full/n,
        "P_atomic_top1_Ru":cnt["Ru"]/n,"P_atomic_top1_Os":cnt["Os"]/n,"P_atomic_top1_Fe":cnt["Fe"]/n,
    })

with (HERE/"descriptor_correlation_sensitivity.csv").open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(json.dumps(out,indent=2))
