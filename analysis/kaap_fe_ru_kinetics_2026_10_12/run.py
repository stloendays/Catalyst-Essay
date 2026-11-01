"""Independent, unfrozen Fe/Ru-CeO2 bed-order and boundary calculations."""
import json
from pathlib import Path
from scipy.optimize import brentq
from model import bed_sequence, equilibrium_extent, kp_full

FEED=(1.,3.,0.1)
T=698.15

def compare(p,m,g,phi=.5,eos="ideal",dh=0.,temps=(T,T)):
    opts=dict(P_bar=p,ru_gain=g,eos=eos,ru_h2_shift_j=dh*1000)
    masses=(m*phi,m*(1-phi))
    return {name:bed_sequence(FEED,order,masses,temps,**opts)["X_N2"] for name,order in (
      ("Fe_only",("Fe","Fe")),("Fe_to_Ru",("Fe","Ru")),
      ("Ru_to_Fe",("Ru","Fe")),("Ru_only",("Ru","Ru")))}

def threshold(p,m,eos="ideal",temps=(T,T),mode="gain"):
    ref=compare(p,m,1.,eos=eos,temps=temps)["Fe_only"]
    def f(v):
        kw={"g":v} if mode=="gain" else {"g":1.,"dh":v}
        return compare(p,m,eos=eos,temps=temps,**kw)["Fe_to_Ru"]-ref
    lo,hi=(1.,100.) if mode=="gain" else (0.,30.)
    return brentq(f,lo,hi,xtol=1e-5) if f(lo)*f(hi)<0 else None

def main():
    records=[]
    for P in (45.,80.,90.):
      for M in (25.,60.,120.):
       for gain in (1.,5.,10.,15.,20.,25.,35.,50.):
        for split in (.25,.5,.75):
         for eos in ("ideal","srk"):
          r=compare(P,M,gain,split,eos)
          records.append(dict(P_bar=P,total_kg=M,Fe_first_fraction=split,eos=eos,
                              hypothetical_Ru_gain=gain,outside_2024_P=P>80,**r))
    target=[]
    for P in (45.,80.,90.):
      for eos in ("ideal","srk"):
       target.append(dict(P_bar=P,eos=eos,unmodified=compare(P,60.,1.,eos=eos),
             hypothetical_gain20=compare(P,60.,20.,eos=eos),
             gain_required_to_beat_Fe=threshold(P,60.,eos=eos),
             H2_binding_weakening_required_kJmol=threshold(P,60.,eos=eos,mode="dh")))
    for P in (80.,90.):
      for eos in ("ideal","srk"):
       target.append(dict(P_bar=P,eos=eos,first_C=425,second_C=390,
             gain20=compare(P,60.,20.,eos=eos,temps=(698.15,663.15)),
             gain_required=threshold(P,60.,eos=eos,temps=(698.15,663.15))))
    out=Path(__file__).resolve().parent/"results"
    out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(dict(status="UNFROZEN",Ru_source="Ru/CeO2 NOT commercial Ru/C", 
          pressure90="Extrapolation",economics="NOT PERFORMED",source_matched_KAAP_validation=False,
          scenarios=len(records),summary=target),indent=2),encoding="utf-8")
    (out/"all_scenarios.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
    print("PASS",len(records),"two-bed scenarios")
    for r in target:print(r)
if __name__=="__main__":main()
