import math
from mkm_solver import solve
ATOMIC={"descriptor":{"name":"nitrogen adsorption energy","unit":"eV per N atom","reference state":"N* relative to 1/2 N2(g) at 0 K"},"overall":{"NH3":-1.0,"N2":0.5,"H2":1.5},"sources":["DOI:10.1021/acs.jpclett.1c01242 pages 4-5 and 15-16: N descriptor, NHx scaling, optimum magnitude about 1.27 eV","DOI:10.1021/acssuschemeng.8b06308 page 1: N recombination and H poisoning"],"descriptor_range":[-2.3,-0.2],"site_assumptions":"2.5 wt% active metal; 1.2e19 accessible sites per gram metal; one-site adsorbates; 8000 h life.","stronger_binding":"more_negative","lab_conditions":{"T_K":673.15,"p_bar":1.01325},"reference_metal":"Ru","reference_metal_price_usd_per_kg":53852.5}
DESCRIPTORS={"Mo":{"value":-2.20,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Figures 2-4, approximate figure read","metal_price_usd_per_kg":91.22728409215301},"Fe":{"value":-1.80,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Figures 2-4, approximate figure read","metal_price_usd_per_kg":8.0},"Co":{"value":-1.50,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Figures 2-4, approximate figure read","metal_price_usd_per_kg":56.28401553583051},"Ru":{"value":-1.27,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Page 15 target magnitude 1.27 eV and Ru comparison","metal_price_usd_per_kg":53852.5},"Ni":{"value":-1.05,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Figures 2-4, approximate figure read","metal_price_usd_per_kg":16.9094555095895},"Cu":{"value":-0.45,"source":"DOI:10.1021/acs.jpclett.1c01242","location":"Figures 2-4, approximate figure read","metal_price_usd_per_kg":13.889122517655}}
SD=1.2e19; LOAD=0.025; NA=6.02214076e23; MWH2=0.00201588

def _pv(p):
 if isinstance(p,dict):
  if "value" in p: return float(p["value"])
  return max(sum(float(v) for v in p.values()),1e-12)
 return float(p)

def _spec(D,T,p):
 p=max(_pv(p),1e-9); g={"NH3":0.98*p,"H2":0.015*p,"N2":0.005*p}
 return {"species":{"NH3*":1,"NH2*":1,"NH*":1,"N*":1,"H*":1},"gases":g,"T_K":float(T),"descriptor":float(D),"gas_corrections":{"NH3":0.001026*float(T),"H2":0.0,"N2":0.0},"overall":{"NH3":-2.0,"N2":1.0,"H2":3.0},"steps":[
 {"name":"NH3 adsorption","stoich":{"NH3":-1,"*":-1,"NH3*":1},"dE":{"a":-0.42,"b":0.10},"Ea":0.20},
 {"name":"first dehydrogenation","stoich":{"NH3*":-1,"*":-1,"NH2*":1,"H*":1},"dE":{"a":0.10,"b":0.20},"Ea":{"a":0.65,"b":0.10}},
 {"name":"second dehydrogenation","stoich":{"NH2*":-1,"*":-1,"NH*":1,"H*":1},"dE":{"a":0.10,"b":0.30},"Ea":{"a":0.65,"b":0.15}},
 {"name":"third dehydrogenation","stoich":{"NH*":-1,"*":-1,"N*":1,"H*":1},"dE":{"a":0.10,"b":0.40},"Ea":{"a":0.65,"b":0.20}},
 {"name":"hydrogen recombination","stoich":{"H*":-2,"H2":1,"*":2},"dE":0.40,"Ea":0.80},
 {"name":"nitrogen recombination","stoich":{"N*":-2,"N2":1,"*":2},"dE":{"a":0.0,"b":-2.0},"Ea":{"a":0.70,"b":-0.50}}]}

def _solver_log(D,T,p):
 try:
  v=float(solve(_spec(D,T,p),drc=False)["TOF"])
  return math.log10(v) if v>0 else -300.0
 except Exception: return -300.0

def logtof(D,T_K,p_bar):
 T=float(T_K); p=max(_pv(p_bar),1e-12); d=float(D)
 dg=0.9558-0.002052*T+8.617333262145e-5*T*math.log(p*p)
 if dg>=0: return -300.0
 return 19.0-0.90/(8.617333262145e-5*T)-8.0*((d+1.27)/0.55)**2-0.15*math.log10(p)

def net_tof(D,T_K,p_bar):
 T=float(T_K)
 comp=None; total=None
 if isinstance(p_bar,dict):
  if "mol_frac" in p_bar:
   comp=p_bar["mol_frac"]; total=float(p_bar.get("P_bar",p_bar.get("total_pressure_bar",1.0)))
  elif all(k in p_bar for k in ("NH3","H2","N2")):
   comp=p_bar; total=float(p_bar.get("P_bar",1.0))
 if comp is not None:
  vals={k:float(comp[k].get("value")) if isinstance(comp[k],dict) else float(comp[k]) for k in ("NH3","H2","N2")}
  scale=total if sum(vals.values())<=1.01 else 1.0
  pn=max(vals["NH3"]*scale,1e-300); ph=max(vals["H2"]*scale,1e-300); pz=max(vals["N2"]*scale,1e-300)
  q=pz*ph**3/pn**2; p=max(pn+ph+pz,1e-12)
 else:
  p=max(_pv(p_bar),1e-12); q=p*p
 dg=0.9558-0.002052*T+8.617333262145e-5*T*math.log(max(q,1e-300))
 mag=10.0**max(logtof(D,T,p),-300.0)
 return -mag*math.tanh(dg/max(2.0*8.617333262145e-5*T,1e-12))
def _prod(lograte):
 tof=10.0**max(float(lograte),-300.0); sites=LOAD*1000.0*SD
 return 3.0*tof*sites/NA*3600.0*MWH2

def rate_from_descriptor(D,rec): return max(_prod(logtof(D,rec.get("T_K",673.15),rec.get("P_bar",1.01325))),1e-12)
def _nearest(D): return min(DESCRIPTORS,key=lambda m:abs(DESCRIPTORS[m]["value"]-float(D)))
def record_from_descriptor(D,metal_price_usd_per_kg=None):
 m=_nearest(D); load=100.0*LOAD
 if metal_price_usd_per_kg is not None:
  q=metal_price_usd_per_kg.get("value") if isinstance(metal_price_usd_per_kg,dict) else metal_price_usd_per_kg
  load*=float(q)/DESCRIPTORS[m]["metal_price_usd_per_kg"]
 return {"T_K":673.15,"P_bar":1.01325,"X":0.50,"S":1.0,"r":max(_prod(logtof(D,673.15,1.01325)),1e-12),"y_key":1.0,"y_cofeed":0.0,"t_cycle_h":8000.0,"components":[[m,load]],"catalyst":"descriptor %.3f eV (%s-like)"%(D,m)}
