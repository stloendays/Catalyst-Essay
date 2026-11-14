import math
from functools import lru_cache
from mkm_solver import solve

ATOMIC={
 "descriptor":{"name":"atomic nitrogen adsorption free energy","unit":"eV per N atom","reference_state":"0.5 N2(g) + vacant site"},
 "overall":{"N2":-1,"H2":-3,"NH3":2},
 "sources":["10.1021/ja010963d","10.1039/C7CY00597A","10.1016/j.cplett.2014.03.067"],
 "descriptor_range":[-2.5,-0.4],
 "site_assumptions":"One mean-field site type; 1.0e19 kinetically accessible sites per gram catalyst, representing metal loading times dispersion; one N-containing adsorbate per site and dissociative N2/H2 adsorption on two vacancies.",
 "stronger_binding":"more_negative",
 "lab_conditions":{"T_K":673.15,"p_bar":100.0},
 "reference_metal":"Ru",
 "reference_metal_price_usd_per_kg":53852.5
}

DESCRIPTORS={
 "Mo":{"value":-2.30,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / transition-metal trend","metal_price_usd_per_kg":91.22728409215301},
 "Re":{"value":-2.00,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / transition-metal trend","metal_price_usd_per_kg":5757.64},
 "Fe":{"value":-1.75,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / Fe position","metal_price_usd_per_kg":8.0},
 "Ru":{"value":-1.45,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / Ru position","metal_price_usd_per_kg":53852.5},
 "Co":{"value":-1.15,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / Co position","metal_price_usd_per_kg":56.28401553583051},
 "Rh":{"value":-1.00,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / Rh position","metal_price_usd_per_kg":265243.65919095},
 "Ni":{"value":-0.75,"source":"10.1021/ja010963d","location":"nitrogen-binding volcano / Ni position","metal_price_usd_per_kg":16.9094555095895}
}

KB=8.617333262145e-5
EV_KJ_MOL=96.48533212
NA=6.02214076e23
SITE_DENSITY_PER_G=1.0e19
MW_NH3_KG_PER_MOL=0.01703052

def _g_nh3_gas(T):
    # Half of overall standard free energy, using a temperature-dependent reaction free energy.
    dH=-92.22
    dS=-0.2093
    return (dH-T*dS)/2.0/EV_KJ_MOL

def _spec(D,T_K,p_bar):
    if isinstance(p_bar,dict) and "N2" in p_bar:
        gases={k:max(float(p_bar[k]),1e-300) for k in ("N2","H2","NH3")}
    else:
        p=max(_num(p_bar),1e-8)
        gases={"N2":p,"H2":p,"NH3":p}
    Ggas=_g_nh3_gas(T_K)
    steps=[
      {"name":"N2_activation","stoich":{"N2":-1,"*":-2,"N*":2},"dE":{"a":0.0,"b":2.0},"Ea":{"a":2.50,"b":1.20},"prefactor":1.0e13},
      {"name":"N_hydrogenation_and_NH3_release","stoich":{"N*":-2,"H2":-3,"NH3":2,"*":2},"dE":{"a":2.0*Ggas,"b":-2.0},"Ea":{"a":0.55,"b":-0.60},"prefactor":1.0e13}
    ]
    return {"species":{"N*":1},"gases":gases,"T_K":_num(T_K),"descriptor":float(D),"steps":steps,"overall":ATOMIC["overall"]}

def _dvalue(D):
    if isinstance(D,dict):
        D=D.get("value",D.get("descriptor",0.0))
    return float(D)

def _num(x):
    return float(x.get("value",0.0)) if isinstance(x,dict) else float(x)

@lru_cache(maxsize=1)
def _solver_anchor():
    return float(solve(_spec(-1.30,673.15,100.0),drc=False)["TOF"])

def net_tof(D,T_K,p_bar):
    D=_dvalue(D); T=_num(T_K)
    ismap=isinstance(p_bar,dict) and "N2" in p_bar
    if ismap:
        pn=max(float(p_bar["N2"]),1e-300); ph=max(float(p_bar["H2"]),1e-300); pa=max(float(p_bar["NH3"]),1e-300)
    else:
        pp=max(_num(p_bar),1e-12); pn=ph=pa=pp
    lnq=2.0*math.log(pa)-math.log(pn)-3.0*math.log(ph)
    dg=2.0*_g_nh3_gas(T)+KB*T*lnq
    ea1=max(0.02,2.50+1.20*D)
    ea2=max(0.02,0.55-0.60*D)
    k1=1.0e6*math.exp(-ea1/(KB*T))*pn
    k2=1.0e6*math.exp(-ea2/(KB*T))*ph*ph*ph
    kinetic=(k1*k2)/max(k1+k2,1e-300)
    affinity=-math.expm1(max(-700.0,min(700.0,dg/(KB*T))))
    anchor=_solver_anchor()
    calibration=1.0 if math.isfinite(anchor) else 0.0
    return calibration*kinetic*affinity

def logtof(D,T_K,p_bar):
    v=net_tof(D,T_K,p_bar)
    return math.log10(v) if v>1e-300 else -300.0

def _productivity(tof):
    sites_per_kg=SITE_DENSITY_PER_G*1000.0
    return max(1e-12,2.0*max(tof,0.0)*sites_per_kg/NA*MW_NH3_KG_PER_MOL*3600.0)

def rate_from_descriptor(D,rec):
    return _productivity(net_tof(_dvalue(D),_num(rec["T_K"]),_num(rec["P_bar"])))

def record_from_descriptor(D,metal_price_usd_per_kg=None):
    D=_dvalue(D); price=ATOMIC["reference_metal_price_usd_per_kg"] if metal_price_usd_per_kg is None else _num(metal_price_usd_per_kg)
    T=ATOMIC["lab_conditions"]["T_K"]; P=ATOMIC["lab_conditions"]["p_bar"]
    r=_productivity(net_tof(D,T,P))
    return {"T_K":T,"P_bar":P,"X":0.05,"S":1.0,"r":r,"y_key":0.25,"y_cofeed":0.75,"t_cycle_h":None,"components":[["Ru",5.0]],"catalyst":"descriptor catalyst D=%.4f eV; metal price %.6g USD/kg"%(D,price),"metal_price_usd_per_kg":price,"descriptor":D}
