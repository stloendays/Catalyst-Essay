"""Reproduce non-figure decision-regret and descriptor-correlation sensitivity outputs.

Uses only frozen repository data. No DFT, process rerun, or LLM call.

Model selection (analysis/nh3_model.py):
    NH3_MODEL=1.1 (default)  NH3-FINAL-1.1 run committed under provenance/nh3_final_1_1. Writes
                             descriptor_correlation_sensitivity.csv here (as before) and checks the NH3 rows of the
                             committed decision_regret_summary.csv, pairwise_inversion_index.csv,
                             decision_regret_uncertainty_sign.csv and common_mode_descriptor_shift.json against the
                             same generator that writes them for 1.2 (the committed 1.1 files are not rewritten).
    NH3_MODEL=1.2            NH3-FINAL-1.2 canonical run (nh3_model.run_dir()). Writes all five files to nh3_1_2/ with
                             the NH3 rows recomputed and the MeOH and Au/TiO2 rows copied verbatim from the 1.1 files.
                             Run reproduce_nh3_cost_mc.py with NH3_MODEL=1.2 first (it writes the cost-MC summary that
                             the NH3 row of decision_regret_uncertainty_sign.csv reads).
"""
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"analysis"))
import nh3_model as NM  # noqa: E402

VERSION=NM.VERSION
if VERSION=="1.1":
    RUN=ROOT/"provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
    OUT=HERE
else:
    RUN=NM.run_dir()
    OUT=NM.out_dir(HERE)

def rows(path):
    with open(path,encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

# Decision regret.
res=json.loads((RUN/"results.json").read_text(encoding="utf-8"))
det=res["deterministic"]
UP=det["activity_order"][0]            # intrinsic-activity (upstream) winner
DOWN=det["feasible_economic_order"][0]  # feasible economic (downstream) winner
assert (UP,DOWN)==("Ru","Fe")
nh3=(det["metals"][UP]["feasible"]["total_cost"]-det["metals"][DOWN]["feasible"]["total_cost"])/det["metals"][DOWN]["feasible"]["total_cost"]
meoh={r["candidate"]:r for r in rows(ROOT/"data/meoh/meoh_candidate_ranking_D01v3.csv")}
j_up=float(meoh["1 wt% Re | 250 C"]["NPC_EUR_t_2pct_purge"])
j_best=float(meoh["5 wt% Re | 200 C"]["NPC_EUR_t_2pct_purge"])
if VERSION=="1.1":
    assert abs(nh3-0.44068926608899806)<1e-12
else:
    A=NM.anchors()
    assert abs(nh3-(A["Ru"]-A["Fe"])/A["Fe"])<1e-12
assert abs((j_up-j_best)/j_best-0.019304569066044774)<1e-12  # Table 3-corrected inputs (2026-10-05)

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
if VERSION!="1.1":
    # Descriptor centres and marginal widths are those of 1.1; confirm them in the 1.2 harness and manifest.
    unc=NM.cfg()["uncertainty"]
    assert float(unc["Fe_sigma_eV"])==sig_fe and float(unc["other_uniform_half_width_eV"])==half
    assert all(NM.core().EN0_CANON[m]==cent[m] for m in cent)

def phi(z):
    return 0.5*(1+math.erf(z/math.sqrt(2)))

class LCGNormal:
    """Match the deterministic JS audit stream used for the committed 2026-09-29 table."""
    def __init__(self, seed):
        self.seed=int(seed) & 0xffffffff
    def uniform(self):
        self.seed=(1664525*self.seed+1013904223) & 0xffffffff
        return self.seed/4294967296.0
    def normal(self):
        u=0.0
        v=0.0
        while u==0.0:
            u=self.uniform()
        while v==0.0:
            v=self.uniform()
        return math.sqrt(-2.0*math.log(u))*math.cos(2.0*math.pi*v)

out=[]
for rho in (0.0,0.25,0.5,0.75,0.9):  # 0.0, not 0: the committed table prints the first cell as 0.0
    rng=LCGNormal(20260929+round(rho*1000))
    n=100000
    cnt={"Ru":0,"Os":0,"Fe":0}; full=0
    sr,si=math.sqrt(rho),math.sqrt(1-rho)
    for _ in range(n):
        g0=rng.normal()
        z={m:sr*g0+si*rng.normal() for m in ("Fe","Ru","Os")}
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

with (OUT/"descriptor_correlation_sensitivity.csv").open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(json.dumps(out,indent=2))


# ---- NH3 rows of the remaining non-figure tables (written for 1.2, checked against the committed files for 1.1) ----
def lines(name):
    """Lines of the committed 1.1 file (MeOH and Au/TiO2 rows are model-independent and are copied verbatim)."""
    return (HERE/name).read_text(encoding="utf-8").splitlines()

def emit(name, header_and_rows):
    if VERSION=="1.1":
        return
    with (OUT/name).open("w",encoding="utf-8",newline="") as f:
        f.write("\r\n".join(header_and_rows)+"\r\n")

def check_csv_row(name, system, mine, numeric):
    """1.1 self-test: the generated NH3 row equals the committed one (numeric fields to 1e-12, text fields exactly)."""
    ref={r["system"]:r for r in rows(HERE/name)}[system]
    got=next(csv.DictReader([lines(name)[0], mine]))
    for k,v in ref.items():
        if k in numeric:
            assert abs(float(got[k])-float(v))<=1e-12, (name,k,got[k],v)
        else:
            assert got[k]==v, (name,k,got[k],v)

cost={m:det["metals"][m]["feasible"]["total_cost"] for m in (UP,DOWN)}

# decision_regret_summary.csv
name="decision_regret_summary.csv"
row=(f'NH3,{UP},{DOWN},{cost[UP]!r},{cost[DOWN]!r},{nh3!r},"Selecting the intrinsic-activity winner instead of the '
     f'economic winner raises the catalyst-dependent cost objective by {100*nh3:.2f}%."')
L=lines(name)
if VERSION=="1.1":
    check_csv_row(name,"NH3",row,{"upstream_selected_downstream_objective","best_downstream_objective","normalized_decision_regret"})
emit(name,[L[0],row]+[l for l in L[1:] if not l.startswith("NH3,")])

# pairwise_inversion_index.csv: chi = ln(J_A/J_B) / ln(s_A/s_B), A = activity winner, B = economic winner; s from the
# atomic-reference logTOF at 673 K (results.json activity_logTOF, identical to fig1_metals.csv logTOF_673K in 1.1).
name="pairwise_inversion_index.csv"
s_nh3=10**(det["metals"][UP]["activity_logTOF"]-det["metals"][DOWN]["activity_logTOF"])
J_nh3=cost[UP]/cost[DOWN]
chi_nh3=math.log(J_nh3)/math.log(s_nh3)
assert chi_nh3>0  # inverted pair; the note text below states this
row=(f'NH3,"{UP} vs {DOWN}",{s_nh3!r},{J_nh3!r},{chi_nh3!r},inverted,"A={UP} is upstream activity winner; B={DOWN} is '
     f'economic winner. chi>0 means higher upstream performance carries a higher downstream cost."')
L=lines(name)
if VERSION=="1.1":
    fig1={r["metal"]:r for r in rows(ROOT/"figures/composite/fig1/fig1_metals.csv")}
    assert all(float(fig1[m]["logTOF_673K"])==det["metals"][m]["activity_logTOF"] for m in (UP,DOWN))
    check_csv_row(name,"NH3",row,{"upstream_metric_ratio_sA_over_sB","downstream_objective_ratio_JA_over_JB","pairwise_transfer_index_chi"})
emit(name,[L[0],row]+[l for l in L[1:] if not l.startswith("NH3,")])

# decision_regret_uncertainty_sign.csv: NH3 row from the cost-side Monte Carlo summary of the same model.
name="decision_regret_uncertainty_sign.csv"
mc=json.loads((OUT/"nh3_cost_mc_regret_summary.json").read_text(encoding="utf-8"))
P=float(mc["P_regret_gt_0"]); nd=int(mc["draws"]); npos=int(round(P*nd))
assert P==1.0  # the interpretation text below states that Ru stays worse in every draw
row=(f'NH3,economic-parameter Monte Carlo,{nd},P_regret_gt_0={P:.3f},"Fe lower cost than Ru in {npos}/{nd} reoptimized '
     f'cost draws","Following intrinsic-activity winner Ru remains economically worse than Fe throughout the '
     f'preregistered cost-side uncertainty range."')
L=lines(name)
if VERSION=="1.1":
    assert row==next(l for l in L if l.startswith("NH3,"))
emit(name,[L[0],row]+[l for l in L[1:] if not l.startswith("NH3,")])

# common_mode_descriptor_shift.json: the same additive delta_E_N on Ru, Os and Fe; switch points where two candidates
# have equal activity on the 673 K volcano. Brackets come from a 0.0025 eV scan of [-0.6, +0.6] eV (one root per pair
# on the single-peak volcano), then 80 bisection steps.
def diff(delta,a,b):
    return interp(cent[a]+delta)-interp(cent[b]+delta)

def bisect(lo,hi,a,b):
    flo=diff(lo,a,b)
    for _ in range(80):
        mid=0.5*(lo+hi)
        fm=diff(mid,a,b)
        if flo*fm<=0:
            hi=mid
        else:
            lo,flo=mid,fm
    return 0.5*(lo+hi)

def switch_points(a,b):
    grid=[-0.6+0.0025*k for k in range(481)]
    roots=[]
    for lo,hi in zip(grid,grid[1:]):
        if diff(lo,a,b)*diff(hi,a,b)<0:
            roots.append(bisect(lo,hi,a,b))
    return roots

assert sorted(cent,key=lambda m:interp(cent[m]),reverse=True)==["Ru","Os","Fe"]
pairs={"Ru_Os":("Ru","Os"),"Fe_Os":("Fe","Os"),"Fe_Ru":("Fe","Ru")}
roots={k:switch_points(*v) for k,v in pairs.items()}
assert all(len(r)==1 for r in roots.values()), roots
sw={f"{k}_equal_activity_delta":r[0] for k,r in roots.items()}
neg=max(v for v in sw.values() if v<0); pos=min(v for v in sw.values() if v>0)
first_neg=next(k for k,v in sw.items() if v==neg).replace("_equal_activity_delta","").replace("_"," / ")
first_pos=next(k for k,v in sw.items() if v==pos).replace("_equal_activity_delta","").replace("_"," / ")
if VERSION=="1.1":
    ref=json.loads((HERE/"common_mode_descriptor_shift.json").read_text(encoding="utf-8"))["switch_points_eV"]
    assert set(ref)==set(sw) and all(abs(sw[k]-ref[k])<=1e-12 for k in ref), (sw,ref)
else:
    common={
        "schema":"nh3-common-mode-descriptor-shift-sensitivity-v1",
        "date":"2026-10-13",
        "model":NM.LABEL,
        "run":NM.RUNS[VERSION],
        "scope":"atomistic Ru/Os/Fe ordering only; no downstream economic probability is inferred",
        "method":f"Apply the same additive delta_E_N to canonical Ru, Os and Fe descriptors and evaluate the {NM.LABEL} 673 K one-descriptor volcano by interpolation of scaling_reachability.csv.",
        "canonical_order":"Ru > Os > Fe",
        "switch_points_eV":sw,
        "preserved_interval_eV":[neg,pos],
        "first_switch_negative_shift":first_neg,
        "first_switch_positive_shift":first_pos,
        "interpretation":(f"A common additive descriptor bias does not generally cancel in activity ranking because all candidates move across a nonlinear volcano. "
                          f"The canonical top-three order is preserved only over a finite common-shift interval, approximately {neg:.4f} < delta_E_N < {pos:.4f} eV."),
    }
    (OUT/"common_mode_descriptor_shift.json").write_text(json.dumps(common,indent=2)+"\n",encoding="utf-8")
print(f"{NM.LABEL if VERSION!='1.1' else 'NH3-FINAL-1.1'}: regret {nh3:.6f}; chi {chi_nh3:.6f} (s={s_nh3:.4f}, J={J_nh3:.6f}); "
      f"common-shift window {neg:.4f} < dE_N < {pos:.4f} eV (first switches {first_neg} / {first_pos}); "
      f"{'checked against committed 1.1 files' if VERSION=='1.1' else 'written to '+str(OUT)}")
