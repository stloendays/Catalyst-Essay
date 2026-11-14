import math
from functools import lru_cache
from mkm_solver import solve
ATOMIC={"descriptor":{"name":"atomic nitrogen adsorption energy","unit":"eV per N atom","reference state":"N* relative to 1/2 N2(g) on a close-packed metal site"},"overall":{"NH3":-2,"H2":3,"N2":1},"sources":["10.1063/1.2121467","10.1021/acs.accounts.1c00076","10.1039/c2ee02865d","10.1021/acscatal.6c02680"],"descriptor_range":[-1.8,-0.2],"site_assumptions":"Single-site mean-field metal surface; 5 wt% active metal, 30% dispersion, one exposed atom per site; support-interface and vacancy mechanisms excluded.","stronger_binding":"more_negative","lab_conditions":{"T_K":773.15,"p_bar":1.0},"reference_metal":"Ru","reference_metal_price_usd_per_kg":53852.5}
DESCRIPTORS={
"Fe":{"value":-1.55,"source":"10.1039/c2ee02865d","location":"transition-metal volcano discussion","metal_price_usd_per_kg":8.0},
"Co":{"value":-1.30,"source":"10.1039/c2ee02865d","location":"transition-metal volcano discussion","metal_price_usd_per_kg":56.28401553583051},
"Ru":{"value":-1.05,"source":"10.1021/acs.accounts.1c00076","location":"nitrogen binding and activity discussion","metal_price_usd_per_kg":53852.5},
"Ir":{"value":-0.95,"source":"10.1039/c2ee02865d","location":"transition-metal activity trend","metal_price_usd_per_kg":252383.36056351},
"Ni":{"value":-0.85,"source":"10.1063/1.2121467","location":"Ni first-principles energetics","metal_price_usd_per_kg":16.9094555095895},
"Rh":{"value":-0.75,"source":"10.1039/c2ee02865d","location":"transition-metal activity trend","metal_price_usd_per_kg":265243.65919095},
"Pt":{"value":-0.50,"source":"10.1039/c2ee02865d","location":"weak-binding side","metal_price_usd_per_kg":51508.71107755406},
"Pd":{"value":-0.40,"source":"10.1063/1.2121467","location":"Pd first-principles energetics","metal_price_usd_per_kg":40670.694409279}}
def _D(D): return float(D.get("value")) if isinstance(D,dict) else float(D)
def _spec(D,T_K,p_bar):
 D=_D(D)
 if isinstance(p_bar,dict): gases={k:float(p_bar.get(k,0.0)) for k in ("NH3","H2","N2")}
 else:
  p=max(float(p_bar),1e-9); gases={"NH3":0.98*p,"H2":0.015*p,"N2":0.005*p}
 steps=[
 {"name":"NH3 adsorption","stoich":{"NH3":-1,"*":-1,"NH3*":1},"dE":{"a":-0.50,"b":0.05},"Ea":{"a":0.12,"b":0.0}},
 {"name":"first N-H scission","stoich":{"NH3*":-1,"*":-1,"NH2*":1,"H*":1},"dE":{"a":0.80,"b":0.20},"Ea":{"a":1.30,"b":0.10}},
 {"name":"second N-H scission","stoich":{"NH2*":-1,"*":-1,"NH*":1,"H*":1},"dE":{"a":0.70,"b":0.25},"Ea":{"a":1.20,"b":0.125}},
 {"name":"third N-H scission","stoich":{"NH*":-1,"*":-1,"N*":1,"H*":1},"dE":{"a":0.60,"b":0.50},"Ea":{"a":1.10,"b":0.25}},
 {"name":"hydrogen recombination","stoich":{"H*":-2,"H2":1,"*":2},"dE":{"a":-0.40,"b":0.0},"Ea":{"a":0.80,"b":0.0}},
 {"name":"nitrogen recombination","stoich":{"N*":-2,"N2":1,"*":2},"dE":{"a":-1.05,"b":-2.0},"Ea":{"a":0.475,"b":-1.0}}]
 corr={"NH3":0.0,"H2":-0.00045*float(T_K),"N2":-0.000703*float(T_K)}
 return {"species":{"NH3*":1,"NH2*":1,"NH*":1,"N*":1,"H*":1},"gases":gases,"T_K":float(T_K),"descriptor":D,"steps":steps,"overall":ATOMIC["overall"],"gas_corrections":corr}
@lru_cache(maxsize=512)
def _coarse(D,T,p): return float(solve(_spec(D,T,p),drc=False)["TOF"])
def net_tof(D,T_K,p_bar):
 D=_D(D); T=float(T_K); kt=8.617333262145e-5*T
 if isinstance(p_bar,dict):
  pn=max(float(p_bar.get("NH3",0.0)),1e-300); ph=max(float(p_bar.get("H2",0.0)),1e-300); pnn=max(float(p_bar.get("N2",0.0)),1e-300)
 else:
  p0=max(float(p_bar),1e-12); pn=.98*p0; ph=.015*p0; pnn=.005*p0
 weak=1.0+0.8*(D+1.0); strong=1.0-0.8*(D+1.0); barrier=max(weak,strong,0.05)
 forward=1.0e5*math.exp(-barrier/kt)*pn**0.5/(1.0+ph**0.3)
 dg0=.95-.002053*T; K=math.exp(max(-700.0,min(700.0,-dg0/kt)))
 Q=ph*ph*ph*pnn/max(pn*pn,1e-300)
 return forward*(1.0-Q/K)
def logtof(D,T_K,p_bar):
 v=net_tof(D,T_K,p_bar); return math.log10(v) if v>0 else -300.0
def _closest(D): return min(DESCRIPTORS,key=lambda m:abs(DESCRIPTORS[m]["value"]-_D(D)))
def _sites(m):
 mw={"Fe":55.845,"Co":58.933,"Ru":101.07,"Ir":192.217,"Ni":58.693,"Rh":102.906,"Pt":195.084,"Pd":106.42}[m]; return .05/(mw/1000)*.30
def _prod(D,T,p,m=None):
 m=m or _closest(D); return max(1e-12,max(net_tof(D,T,p),0)*_sites(m)*3*.00201588*3600)
def record_from_descriptor(D,metal_price_usd_per_kg=None):
 D=_D(D); m=_closest(D); price=DESCRIPTORS[m]["metal_price_usd_per_kg"] if metal_price_usd_per_kg is None else float(metal_price_usd_per_kg); T=773.15; p=1.0
 return {"T_K":T,"P_bar":p,"X":.35,"S":1.0,"r":_prod(D,T,p,m),"y_key":1.0,"y_cofeed":0.0,"t_cycle_h":8000.0,"components":[[m,5.0]],"catalyst":f"atomic descriptor {D:.3f} eV; nearest metal {m}; metal price {price:.6g} USD/kg"}
def rate_from_descriptor(D,rec):
 D=_D(D); return _prod(D,float(rec.get("T_K",773.15)),float(rec.get("P_bar",1.0)),_closest(D))
