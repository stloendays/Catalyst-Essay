"""UNFROZEN paper-law Fe/Ru-CeO2 fixed-material-budget bed comparison.

Corrected Cholewa 2024 Eqs 11/12 and NIST thermochemistry.
All numbers are research scenarios, never commercial KAAP predictions.
"""
import csv
import json
import math
from pathlib import Path
from scipy.optimize import brentq
from model import FE, RU_CEO2, kp_full, rate, stage, bed_sequence

INLET=(1.,3.,.1) # mol N2, H2, NH3 per second: normalized hypothetical inlet
T_K=698.15
OUT=Path(__file__).resolve().parent/"results_v2"

def compare(P,fe_mass,ru_mass,gain=1.,eos="ideal",Ts=(T_K,T_K)):
    """Same quantities of each element/support, even after reversing bed order."""
    kw=dict(P_bar=P,ru_gain=gain,eos=eos)
    beds={
      "Fe_then_Ru":(("Fe","Ru"),(fe_mass,ru_mass)),
      "Ru_then_Fe":(("Ru","Fe"),(ru_mass,fe_mass)),
      "all_Fe":(("Fe","Fe"),(fe_mass,ru_mass)),
      "all_Ru":(("Ru","Ru"),(fe_mass,ru_mass))}
    return {key:bed_sequence(INLET,seq,masses,Ts,**kw)["X_N2"]
            for key,(seq,masses) in beds.items()}

def critical_gain(P,fe_mass,ru_mass,eos="ideal",Ts=(T_K,T_K)):
    def gap(g):
        c=compare(P,fe_mass,ru_mass,g,eos,Ts)
        return c["Fe_then_Ru"]-c["all_Fe"]
    if gap(1.)>=0:return 1.
    if gap(100.)<=0:return None
    return float(brentq(gap,1.,100.,xtol=3e-7))

def local_replacement_gain(P,fe_total,eos="ideal"):
    f=stage(INLET,FE,T_K,P,fe_total,eos=eos)
    return float(rate(FE,T_K,P,f,eos=eos)/rate(RU_CEO2,T_K,P,f,eos=eos))

def thermochemistry(T,P=90.):
    """Independent NIST Shomate vs #64 Gillespie-Beattie, zero initial NH3."""
    kn=math.sqrt(kp_full(T))
    kg=10**(-2.691122*math.log10(T)-5.519265e-5*T+
             1.848863e-7*T*T+2001.6/T+2.6899)/1.01325
    def equilibrium_y(k):
        def f(x):
            tot=4.-2*x
            an=P*(1-x)/tot
            ah=P*(3-3*x)/tot
            aa=P*2*x/tot
            return aa/(an**.5*ah**1.5)-k
        x=brentq(f,1e-12,1-1e-12,xtol=1e-13)
        return 2*x/(4-2*x)
    yn,yg=equilibrium_y(kn),equilibrium_y(kg)
    return dict(T_C=T-273.15,P_bar_abs=P,K_half_NIST=kn,K_half_GB=kg,
                yNH3_NIST=yn,yNH3_GB=yg,difference_percentage_points=100*(yn-yg))

def csv_output(name,rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for P in (45.,80.,90.):
        for eos in ("ideal","srk"):
            for gain in (1.,3.,5.,6.,7.,10.,20.):
                for phi in (.1,.25,.5,.75,.9):
                    fmass=60*phi
                    rmass=60-fmass
                    c=compare(P,fmass,rmass,gain,eos)
                    rows.append(dict(P_bar_abs=P,eos=eos,Fe_mass_kg=fmass,
                      Ru_CeO2_mass_kg=rmass,hypothetical_Ru_factor=gain,
                      pressure_above_source_range=P>81.01325,**c,
                      FeRu_minus_RuFe=c["Fe_then_Ru"]-c["Ru_then_Fe"],
                      FeRu_minus_allFe=c["Fe_then_Ru"]-c["all_Fe"]))
    csv_output("matched_mass_scenarios.csv",rows)
    parity=[]
    for P in (45.,80.,90.):
        for eos in ("ideal","srk"):
            for phi in (.1,.25,.5,.75,.9):
                parity.append(dict(P_bar_abs=P,eos=eos,Fe_mass_fraction=phi,
                  hypothetical_gain_to_match_all_Fe=critical_gain(P,60*phi,60*(1-phi),eos),
                  pressure_above_source_range=P>81.01325))
    csv_output("parity_thresholds.csv",parity)
    thermo=[thermochemistry(t+273.15) for t in (400.,425.,450.)]
    csv_output("thermodynamic_crosscheck.csv",thermo)
    def ccount(g,key):
        r=[v for v in rows if v["P_bar_abs"]<81.01325 and
           v["eos"]=="ideal" and v["hypothetical_Ru_factor"]==g]
        return len(r),sum(v[key]>0 for v in r)
    summary=dict(
      status="UNFROZEN CONDITIONAL MECHANISM (NO VALIDATED KAAP CLAIM)",
      source="Cholewa et al. 2024 measured Fe and Ru/CeO2; NOT promoted Ru/C",
      invalid_prior_threshold="17.23x from algebraically incorrect final fitted rate law",
      model="final published Eqs 11/12 with NIST Shomate thermochemistry",
      source_pressure="80 bar(g) approx 81.01325 bar(abs); 90 bar abs is extrapolation",
      matched_material_budgets="W_Fe,W_Ru preserved across order reversal",
      unmodified_Fe_first_over_Ru_first=ccount(1.,"FeRu_minus_RuFe"),
      unmodified_hybrid_beats_all_Fe=ccount(1.,"FeRu_minus_allFe"),
      hypothetical_7x_Fe_first_over_Ru_first=ccount(7.,"FeRu_minus_RuFe"),
      hypothetical_7x_hybrid_beats_all_Fe=ccount(7.,"FeRu_minus_allFe"),
      comparison_80barabs_425C_30plus30kg=dict(unmodified=compare(80,30,30,1.),
                counterfactual_unmeasured_7x=compare(80,30,30,7.)),
      threshold_80barabs_equal_mass=critical_gain(80,30,30),
      threshold_80barabs_min_over_tested_splits=min(v["hypothetical_gain_to_match_all_Fe"] 
           for v in parity if v["P_bar_abs"]==80 and v["eos"]=="ideal"),
      threshold_infinitesimal_Ru_replacement_at_Fe_outlet=local_replacement_gain(80,60),
      equilibrium_crosscheck=thermo,
      outstanding=dict(Ru_C_kinetic_parameters="MISSING",adiabatic_energy="NOT COUPLED",
               pressure_drop="NOT CALIBRATED",financing_DCF="NOT EVALUATED",
               industrial_comparison="NOT VALIDATED"))
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    print("computed",len(rows),"matched cases and",len(parity),"thresholds")

if __name__=="__main__":main()
