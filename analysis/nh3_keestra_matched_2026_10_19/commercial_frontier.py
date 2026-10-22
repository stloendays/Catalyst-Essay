#!/usr/bin/env python3
"""Source-factor-locked, ideal-fugacity Fe vs Ru-Ba-K/C local kinetic frontier.

This is NOT a process-economic phase boundary or a source-equivalent
adiabatic final-bed simulation. It evaluates local activity at the same
gas composition and pressure using published 2025 equations and the
Ru-Ba-K/C SI Model D Table 8-specific bcat, bN (no refitting).
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

import kinetics as K

P_BAR_A=100.0
H2_N2=2.25
TGRID=(350.0,375.0,400.0,425.0,450.0)
Y_MAX=.15
STEP=.0025
RATIO_GATE=1.0
FE=K.KineticModel.from_locked("Fe")
RU=K.KineticModel.from_locked("Ru_Ba_K_C")


def point(T_C:float,nh3_mole_fraction:float):
    gas=K.inlet_composition(ammonia_mole_fraction=nh3_mole_fraction,
                            h2_n2_ratio=H2_N2)
    f=K.ideal_fugacity_bar(P_BAR_A,gas)
    fe=K.published_rate_mol_kg_s(FE,T_C+273.15,f)
    ru=K.published_rate_mol_kg_s(RU,T_C+273.15,f)
    Kf=K.eq_constant(T_C+273.15)
    q=f["NH3"]**2/(Kf**2*f["N2"]*f["H2"]**3)
    if not all(math.isfinite(x) for x in (fe,ru,q)):
        raise AssertionError("nonfinite matched inlet rate")
    return dict(T_C=T_C,P_bar_absolute=P_BAR_A,inlet_NH3_mole_fraction=nh3_mole_fraction,
                inlet_H2_N2=H2_N2,
                Fe_AmoMax10_r_mol_kg_s=fe,Ru_Ba_K_C_r_mol_kg_s=ru,
                Ru_over_Fe_local_rate=ru/fe if fe>0 and ru>0 else None,
                reaction_quotient_over_equilibrium=q,
                forward_feasible=(q<1 and fe>0 and ru>0),
                model_formulation="Keestra2025 Fe AmoMax10 and Ru-Ba-K/C Model D Table8 source factors",
                eos_assumption="ideal fugacity fi=yi P; not Keestra corrected-SRK")


def crossover(Tc:float):
    # Search for sign change while both rates are forward under the local
    # ideal-fugacity assumption, no tuning to external activity/bed output.
    rows=[point(Tc,k*STEP) for k in range(round(Y_MAX/STEP)+1)]
    active=[r for r in rows if r["forward_feasible"]]
    for a,b in zip(active[:-1],active[1:]):
        fa=a["Ru_over_Fe_local_rate"]-1
        fb=b["Ru_over_Fe_local_rate"]-1
        if fa==0:
            return a["inlet_NH3_mole_fraction"]
        if fa*fb<0:
            lo=a["inlet_NH3_mole_fraction"]
            hi=b["inlet_NH3_mole_fraction"]
            for _ in range(55):
                mid=(lo+hi)/2
                c=point(Tc,mid)
                if not c["forward_feasible"]:
                    raise AssertionError("unexpected loss of forward validity in crossover bracket")
                fm=c["Ru_over_Fe_local_rate"]-1
                if fa*fm<=0:hi=mid
                else:lo=mid;fa=fm
            root=(hi+lo)/2
            err=abs(point(Tc,root)["Ru_over_Fe_local_rate"]-1)
            assert err<1e-9,(root,err)
            return root
    return None


def plot(rows:list,summary:dict,out:Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5.5),layout="constrained")
    for T in TGRID:
        subset=[z for z in rows if z["T_C"]==T and z["forward_feasible"]]
        x=[100*z["inlet_NH3_mole_fraction"] for z in subset]
        y=[z["Ru_over_Fe_local_rate"] for z in subset]
        ax.plot(x,y,lw=1.7,label=f"{T:.0f} °C")
    ax.axhline(1,color="#333333",lw=1.2,ls="--")
    ax.axvline(11,color="#7B7B7B",lw=1.2,ls=":")
    ax.set_yscale("log")
    ax.set_xlabel("Assumed reactor-inlet NH₃ mole fraction (%)")
    ax.set_ylabel("Ru-Ba-K/C : Fe local rate ratio (mol NH₃ kg-cat⁻¹ s⁻¹)")
    ax.set_title("100 bar(a), H₂/N₂=2.25 | published catalyst-specific factors\nIDEAL fugacities; local kinetic rates, NOT industrial cost or adiabatic bed")
    ax.legend(title="Source-model rate temperature",ncol=2,frameon=False)
    ax.grid(axis="y",alpha=.2)
    fig.savefig(out/"SI_source_locked_100bar_local_kinetic_frontier.png",dpi=220)
    fig.savefig(out/"SI_source_locked_100bar_local_kinetic_frontier.svg")
    plt.close(fig)


def run(out:Path, *, produce_plot=True):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for T in TGRID:
        rows.extend(point(T,k*STEP) for k in range(round(Y_MAX/STEP)+1))
    matching=point(400,0.11)
    initial=point(400,0.0)
    crossings=[{"T_C":T,"NH3_mole_fraction_crossover":crossover(T)}
               for T in TGRID]
    assert all(r["NH3_mole_fraction_crossover"] is not None for r in crossings)
    assert initial["Ru_over_Fe_local_rate"]<1.0
    assert matching["Ru_over_Fe_local_rate"]>1.0
    assert all(z["forward_feasible"] for z in (initial,matching))
    result={
      "evidence":"SOURCE_SPECIFIC_MODEL_D_FACTOR_LOCAL_SENSITIVITY_NOT_PHYSICAL_VALIDATION",
      "source_Keestra_Fe_2025":"10.1016/j.cej.2025.164593",
      "source_Keestra_Ru_2025":"10.1016/j.cej.2025.168541",
      "Ru_original_SI_sha256":K.CONFIG["referenceTarget100Bar"]["specific_ru_parameters_source"]["source_sha256"],
      "factor_source":"Ru 2025 SI A-1-4 Model D Table 8, Ru-Ba-K/C – Liu (2013) [4]",
      "bcat_Ru_Ba_K_C":RU.bcat,"bN_Ru_Ba_K_C":RU.bN,
      "bcat_Fe":FE.bcat,"bN_Fe":FE.bN,
      "pressure_bar_absolute":P_BAR_A,
      "H2_N2":H2_N2,
      "source_industrial_final_bed_inlet":matching,
      "zero_NH3_inlet":initial,
      "rate_crossover_by_temperature":crossings,
      "same_pressure_ranking_is_state_dependent":True,
      "method":"Keestra global Langmuir-Hinshelwood rate equations, ideal fugacity fi=yi*P; no original modified SRK, no adiabatic bed, no measured new data",
      "industrial_G2":"BLOCKED_FULL_MODIFIED_SRK_ADIABATIC_BED_REQUIRED",
      "economic_G3":"BLOCKED_G2_REQUIRED",
      "no_new_process_economic_parity":True
    }
    with (out/"100bar_source_locked_local_rate_grid.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    (out/"100bar_source_locked_kinetic_frontier_summary.json").write_text(
          json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if produce_plot:
        plot(rows,result,out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--no-plot",action="store_true")
    args=p.parse_args()
    run(args.out,produce_plot=not args.no_plot)
