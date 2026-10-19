#!/usr/bin/env python3
"""G2 exploratory 100 bar source-specific adiabatic final-bed calculation.

Exact chemical kinetic sources:
  Keestra Fe CEJ 2025 164593, global Table 2, AmoMax10 b_cat=1.
  Keestra Ru CEJ 2025 168541, global Table 3; ORIGINAL Ru SI
  A-1-4 Model D Table 8, Ru-Ba-K/C Liu (2013):
  b_cat=76.25, b_N=0.8514, fixed, not regressed here.

Thermodynamic fugacity:
  Keestra Fe SI A-5-1 source Python/SI A-6 exact critical values,
  Mathias p_pol and Aspen HYSYS kij. Compare literal-source printed
  alpha-mixture code against conventional square-root SRK mixing.

Adiabatic enthalpy:
  Public NIST Chemistry WebBook 69 Shomate ideal gas enthalpy for
  N2, H2, NH3; optionally analytically computed SRK mixture departure.
  The underlying Aspen energy/enthalpy configuration is not available
  in the authors' Fe SI A-5 Python model; NIST is an explicit
  independent engineering approximation, NOT source-equivalent Aspen.

The target GHSV numbers MUST NOT enter equations or numerical fitting.
No new economic optimization or manuscript update.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import sys
from scipy.integrate import quad
from scipy.optimize import brentq

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import kinetics as K
import g2_srk as S

P_BAR=100.
T0=673.15
H2_N2=2.25
Y_NH3_0=.11
TEMP_LO=T0
TEMP_HI=1350.
TARGET_EQUIL_FRACTION=.9
NTP_T=298.15
NTP_P=101325.
VM_NTP=S.R*NTP_T/NTP_P # m3/mol; 25 C and 1 atm as source
RHO={"Fe":2500.,"Ru_Ba_K_C":750.}
SOURCE_REPORT_GHSV={"Fe":22250.,"Ru_Ba_K_C":130000.}
THERMO_MODES=("nist_ideal","nist_plus_srk_residual")
GAS_MODES=("ideal","literal_source","conventional")
# A,B,C,D,E,F,H and the valid T range, from NIST WebBook SRD69 (J, kJ)
# https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Type=JANAFG (N2)
# https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Type=JANAFG (H2)
# https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Type=JANAFG (NH3)
SHOMATE={
 "N2":[(100,500,(28.98641,1.853978,-9.647459,16.63537,.000117,-8.671914,0.)),
        (500,2000,(19.50583,19.88705,-8.598535,1.369784,.527601,-4.935202,0.))],
 "H2":[(298,1000,(33.066178,-11.363417,11.432816,-2.772874,-.158558,-9.980797,0.)),
        (1000,2500,(18.563083,12.257357,-2.859786,.268238,1.977990,-1.147438,0.))],
 "NH3":[(298,1400,(19.99563,49.77119,-15.37599,1.921168,.189174,-53.30667,-45.89806)),
        (1400,6000,(52.02427,18.48801,-3.765128,.248541,-12.45799,-85.53895,-45.89806))]
}
FE=K.KineticModel.from_locked("Fe")
RU=K.KineticModel.from_locked("Ru_Ba_K_C")
INLET_N2=(1-Y_NH3_0)/(1+H2_N2)
INLET_H2=(1-Y_NH3_0)-INLET_N2
INLET={"N2":INLET_N2,"H2":INLET_H2,"NH3":Y_NH3_0}
X_LIM=min(INLET_N2,INLET_H2/3.)


def shomate_cp_h(spec,T):
    if not math.isfinite(T) or T<298 or T>1600:
        raise ValueError("T out of NIST heat-capacity temperature bounds")
    windows=SHOMATE[spec]
    match=next((c for low,hi,c in windows if low<=T<=hi),None)
    if match is None:raise ValueError(f"no Shomate support for {spec} T={T}")
    A,B,C,D,E,F,H=match
    t=T/1000.
    cp=A+B*t+C*t*t+D*t**3+E/t**2 # J/mol/K
    delta_h=A*t+B*t*t/2+C*t**3/3+D*t**4/4-E/t+F-H # kJ/mol rel to 298
    return cp,(delta_h+H)*1000. # J/mol INCLUDING standard formation H


def flows(x):
    if not (math.isfinite(x) and 0<=x<.999999*X_LIM):
        raise ValueError(f"extent x outside stoichiometric feasible domain: {x}")
    out={"N2":INLET_N2-x,"H2":INLET_H2-3*x,"NH3":Y_NH3_0+2*x}
    ntot=1.-2*x
    if abs(sum(out.values())-ntot)>1e-11:raise ArithmeticError("mole-flow conservation failed")
    return out,ntot,{s:n/ntot for s,n in out.items()}


class Bed:
    def __init__(self,gas_mode,energy_mode):
        if gas_mode not in GAS_MODES or energy_mode not in THERMO_MODES:
            raise ValueError("unknown declared EOS/energy mode")
        if gas_mode=="ideal" and energy_mode!="nist_ideal":
            raise ValueError("no SRK residual without an SRK gas model")
        self.gas_mode=gas_mode
        self.energy_mode=energy_mode
        self.cache={}
        self.h_in=self.enthalpy(0.,T0)

    def thermo(self,x,T):
        out,ntot,frac=flows(x)
        if self.gas_mode=="ideal":
            f={s:frac[s]*P_BAR for s in ("N2","H2","NH3")}
            return f,1.,0.,[1.,1.,1.]
        v=S.evaluate(frac,T,P_BAR,rule=self.gas_mode)
        f=dict(zip(S.SPECIES,v.fugacity_bar))
        return f,v.compressibility,v.gas_enthalpy_departure_J_per_mol,list(v.phi)

    def enthalpy(self,x,T):
        out,ntot,frac=flows(x)
        result=sum(n*shomate_cp_h(s,T)[1] for s,n in out.items())
        if self.energy_mode=="nist_plus_srk_residual":
            _,_,hres,_=self.thermo(x,T)
            result+=ntot*hres
        return result

    def state(self,x):
        if x in self.cache:return self.cache[x]
        if x==0:temp=T0
        else:
            b=self.h_in
            def err(T):return self.enthalpy(x,T)-b
            fa=err(TEMP_LO);fb=err(TEMP_HI)
            if fa>1e-3 or fb<0:
                raise ArithmeticError(f"adiabatic temperature not bracketed, x={x}, f0={fa}, fhi={fb}")
            temp=brentq(err,TEMP_LO,TEMP_HI,xtol=2e-8)
        f,Z,hres,phi=self.thermo(x,temp)
        ratio=f["NH3"]**2/(K.eq_constant(temp)**2*f["N2"]*f["H2"]**3)
        if ratio<0 or not math.isfinite(ratio):
            raise ArithmeticError("bad equilibrium ratio")
        out,ntot,y=flows(x)
        st={"extent_N2_mol_per_feed_mol":float(x),"T_K":temp,"T_C":temp-273.15,
            "y_NH3":y["NH3"],"y_N2":y["N2"],"y_H2":y["H2"],
            "equilibrium_ratio":ratio,"Z":Z,"mixture_enthalpy_departure_J_mol":hres,
            "f_N2_bar":f["N2"],"f_H2_bar":f["H2"],"f_NH3_bar":f["NH3"],
            "energy_residual_J_per_inlet_mol":self.enthalpy(x,temp)-self.h_in,
            "phi_N2":phi[0],"phi_H2":phi[1],"phi_NH3":phi[2]}
        self.cache[x]=st
        return st

    def eq_extent(self):
        assert self.state(0.)["equilibrium_ratio"]<1
        hi=1e-5
        while self.state(hi)["equilibrium_ratio"]<1:
            hi*=1.8
            if hi>.35*X_LIM:
                raise ArithmeticError("equilibrium not bracketed inside explored domain")
        x=brentq(lambda xi:self.state(xi)["equilibrium_ratio"]-1,
                 0,hi,xtol=2e-13,rtol=1e-10)
        assert abs(self.state(x)["equilibrium_ratio"]-1)<1e-7
        return x

    def reactor(self,model,*,profile_points=21):
        xmax=self.eq_extent()
        target=TARGET_EQUIL_FRACTION*xmax
        if model.catalyst=="Ru_Ba_K_C" and (
            self.state(target)["T_C"]>465.):
            source_specific_T_warning=True
        else:source_specific_T_warning=False

        def dWdx(x):
            st=self.state(x)
            f={s:st["f_"+s+"_bar"] for s in ("N2","H2","NH3")}
            rate=K.published_rate_mol_kg_s(model,st["T_K"],f)
            if not math.isfinite(rate) or rate<=0:
                raise ArithmeticError(f"nonforward finite source rate at x={x}: {rate}")
            return 2./rate
        W,err=quad(dWdx,0.,target,epsabs=2e-7,epsrel=2e-6,limit=150)
        if W<=0:raise ArithmeticError("nonphysical catalyst mass demand")
        ghsv=RHO[model.catalyst]*VM_NTP*3600./W
        points=[]
        for i in range(profile_points):
            x=target*i/(profile_points-1)
            z=self.state(x).copy()
            z["Fe_gas_rate_mol_kg_s"]=K.published_rate_mol_kg_s(FE,z["T_K"],
                    {s:z["f_"+s+"_bar"] for s in ("N2","H2","NH3")})
            z["Ru_promoted_gas_rate_mol_kg_s"]=K.published_rate_mol_kg_s(RU,z["T_K"],
                    {s:z["f_"+s+"_bar"] for s in ("N2","H2","NH3")})
            points.append(z)
        return dict(catalyst=model.catalyst,gas_model=self.gas_mode,energy_model=self.energy_mode,
                    author_printed_GHSV_h=SOURCE_REPORT_GHSV[model.catalyst],
                    predicted_GHSV_h=ghsv,ratio_predicted_to_published=ghsv/SOURCE_REPORT_GHSV[model.catalyst],
                    relative_error_vs_published=(ghsv/SOURCE_REPORT_GHSV[model.catalyst]-1),
                    catalyst_W_over_F0_kg_s_mol=W,quadrature_estimated_abs_error=err,
                    source_NTP_molar_volume_m3_mol=VM_NTP,catalyst_bulk_density_kg_m3=RHO[model.catalyst],
                    x_equilibrium=xmax,x_target=target,
                    source_fraction_adiabatic_equilibrium=TARGET_EQUIL_FRACTION,
                    target_state=self.state(target),
                    non_mixture_kinetic_T_global_caution=source_specific_T_warning,
                    source_fit_Ru_global_max_C=465.,profiles=points)


def one_scenario(gas_mode,energy_mode):
    bed=Bed(gas_mode,energy_mode)
    fe=bed.reactor(FE)
    ru=bed.reactor(RU)
    return dict(gas_model=gas_mode,energy_model=energy_mode,
                predicted_GHSV_Fe_h=fe["predicted_GHSV_h"],
                predicted_GHSV_Ru_h=ru["predicted_GHSV_h"],
                printed_GHSV_Fe_h=SOURCE_REPORT_GHSV["Fe"],
                printed_GHSV_Ru_h=SOURCE_REPORT_GHSV["Ru_Ba_K_C"],
                inferred_volume_ratio_Fe_over_Ru=ru["predicted_GHSV_h"]/fe["predicted_GHSV_h"],
                printed_volume_ratio_Fe_over_Ru=SOURCE_REPORT_GHSV["Ru_Ba_K_C"]/SOURCE_REPORT_GHSV["Fe"],
                inferred_mass_ratio_Fe_over_Ru=(ru["predicted_GHSV_h"]/fe["predicted_GHSV_h"])*(RHO["Fe"]/RHO["Ru_Ba_K_C"]),
                final_temperature_C=fe["target_state"]["T_C"],
                final_ammonia_mol_fraction=fe["target_state"]["y_NH3"],
                equilibrium_extent_N2_per_feed_mol=fe["x_equilibrium"],
                target_extent_N2_per_feed_mol=fe["x_target"],
                max_energy_residual_J_per_feed_mol=max(abs(x["energy_residual_J_per_inlet_mol"]) for x in fe["profiles"]),
                Fe_relative_GHSV_error=fe["relative_error_vs_published"],
                Ru_relative_GHSV_error=ru["relative_error_vs_published"],
                Ru_model_global_T_overreach=ru["non_mixture_kinetic_T_global_caution"],
                Fe_profile=fe["profiles"],Ru_profile=ru["profiles"])


def run(out:Path,*,show_plot=True):
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for mode in GAS_MODES:
        for energy in THERMO_MODES:
            if mode=="ideal" and energy!="nist_ideal":continue
            results.append(one_scenario(mode,energy))
    # No printed target GHSV used in the nonlinear solve, root, quadrature,
    # eos coefficients, source catalyst factors or heat capacities.
    clean=[{k:v for k,v in z.items() if k not in ("Fe_profile","Ru_profile")}
           for z in results]
    data={
       "study":"2025 Keestra 100bar source-factor adiabatic PFR FALSIFICATION ATTEMPT",
       "status":"EXPLORATORY_NONIDENTICAL_THERMO_UNVERIFIED_G2",
       "published_source_Fe_DOI":"10.1016/j.cej.2025.164593",
       "published_source_Ru_DOI":"10.1016/j.cej.2025.168541",
       "Fe_SI_original_SHA256":S.SOURCE_SI_SHA256,
       "Ru_SI_original_SHA256":K.CONFIG["referenceTarget100Bar"]["specific_ru_parameters_source"]["source_sha256"],
       "Fe_reference_bcat":FE.bcat,
       "Ru_promoted_bcat":RU.bcat,"Ru_promoted_bN":RU.bN,
       "parameter_fitting":"NONE; model data and experimental output targets NEVER tuned",
       "symmetric_gas_states":"N2/H2/NH3-only with source authors' printed inlet conditions",
       "P_bar_abs":P_BAR,"T_in_C":T0-273.15,"NH3_in_mol_fraction":Y_NH3_0,
       "H2_N2_in_ratio":H2_N2,"void_fraction_mentioned_by_source_but_not_used_in_bulk_density_again":.4,
       "NTP_definition":"298.15 K, 101325 Pa per source paper",
       "adiabatic_heat":"NIST ideal gas Shomate enthalpy, or NIST+analytic SRK enthalpy-departure, NOT the paper Aspen caloric basis",
       "kij_source":"Keestra Fe 2025 SI A-5-1 / A-6, Aspen HYSYS V14 3x3 submatrix",
       "EOS_mixing_comparison":"source literal published code vs conventional SRK due unexpected extra sqrt(alpha_i alpha_j) in SI Python",
       "source_kinetic_temperature_domain_warning":"Ru pooled 247-465C, individual promoted Ru domain not independently validated",
       "authors_bed_outputs_predeclared_as_comparison_only":SOURCE_REPORT_GHSV,
       "G2_independent_complete_reproduction":False,
       "G3_updated_economic_phase_map":False,
       "scenarios":clean}
    (out/"g2_adiabatic_readiness.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    with (out/"g2_adiabatic_scenario_results.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(clean[0]))
        w.writeheader();w.writerows(clean)
    for z in results:
        stem=z["gas_model"]+"_"+z["energy_model"]
        with (out/("g2_profile_"+stem+".csv")).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["catalyst"]+list(z["Fe_profile"][0]))
            w.writeheader()
            for c in ("Fe","Ru"):
                for row in z[c+"_profile"]:
                    w.writerow({"catalyst":c,**row})
    if show_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(1,2,figsize=(12,5.5),layout="constrained")
        labels=[z["gas_model"]+"\n"+z["energy_model"].replace("nist_","") for z in clean]
        for ax,key,target,title in [(axs[0],"predicted_GHSV_Fe_h",22250,"Fe AmoMax10"),
                                    (axs[1],"predicted_GHSV_Ru_h",130000,"Ru-Ba-K/C Liu 2013")]:
            ax.barh(labels,[z[key] for z in clean],color="#899DA6")
            ax.axvline(target,color="#972C31",ls="--",lw=2,label="Authors' printed GHSV")
            ax.set_xlabel("Required final-bed GHSV (h$^{-1}$)")
            ax.set_title(title)
            ax.legend(fontsize=8)
        fig.suptitle("100 bar matched-kinetic adiabatic PFR | source SRK + NIST heat options\n"
                     "EXPLORATORY sensitivity, not exact authors' Aspen replication")
        fig.savefig(out/"g2_adiabatic_vs_published.png",dpi=220,bbox_inches="tight")
        fig.savefig(out/"g2_adiabatic_vs_published.svg",bbox_inches="tight")
        plt.close(fig)
    header=[
      "# G2 attempted original 100bar matched Fe/Ru adiabatic final-bed reproduction",
      "",
      "Full source-specific kinetics + original SI Mathias polarity EOS/gas pure properties/HYSYS kij. NIST-JANAF Shomate ideal enthalpy with/without analytical SRK enthalpy departure, NOT the source's explicit Aspen caloric basis. No kinetic factor or property fitted to authors' GHSV.",
      "",
      "## Computed source-grid comparisons",
      "",
      "| SRK gas fugacity | Energy closure | Fe predicted GHSV h-1 | Ru predicted GHSV h-1 | Predicted Fe/Ru volume ratio | Fe rel. deviation | Ru rel. deviation | T_out C |",
      "|---|---|---:|---:|---:|---:|---:|---:|"
    ]
    for z in clean:
        header.append(f"| {z['gas_model']} | {z['energy_model']} | {z['predicted_GHSV_Fe_h']:.1f} | {z['predicted_GHSV_Ru_h']:.1f} | {z['inferred_volume_ratio_Fe_over_Ru']:.3f} | {100*z['Fe_relative_GHSV_error']:+.1f}% | {100*z['Ru_relative_GHSV_error']:+.1f}% | {z['final_temperature_C']:.2f} |")
    header+=["",
      "Printed source target: 22,250 h-1 Fe and 130,000 h-1 Ru, i.e. pure ratio 5.8427 (source result, NOT calibration input).",
      "",
      "## What remains incomplete",
      "1. The original Fe SI Python contains an extra alpha multiplier in mixing relative to its own standard a_ij text; both literal and conventional paths were preserved rather than silently correcting one.",
      "2. Public NIST Shomate Cp and SRK enthalpy departures do not guarantee equivalence to Aspen Plus physical property/heat-capacity and fugacity settings.",
      "3. Pressure is fixed and inerts neglected (Table 4 lists only reactants/product), radial geometry/mass-transfer and source GHSV void convention unverified.",
      "4. The model's global Ru fitted T upper range is 465C and does not guarantee per-formulation support at the adiabatic bed outlet.",
      "5. No independent measured rate holdout or industrial plant simulation validation was conducted. The pre-existing industrial NH3-64 score is unchanged.",
      "",
      "**G2 explicitly remains open to scientific review regardless of numeric closeness**; no economic/phase atlas was rerun. This is a legitimate partial *kinetic PFR* replication attempt with externally sourced NIST enthalpy, not a claim of exact source-matched Aspen outputs.",
      ""
    ]
    (out/"G2_REPORT.md").write_text("\n".join(header),encoding="utf-8")
    print(json.dumps(clean,ensure_ascii=False,indent=2))
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--no-plot",action="store_true")
    a=p.parse_args()
    run(a.out,show_plot=not a.no_plot)
