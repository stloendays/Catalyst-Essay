import math
from mkm_solver import solve

ATOMIC={"descriptor":{"name":"nitrogen_adsorption_energy","unit":"eV/N atom","reference_state":"N* relative to 1/2 N2(g) + *"},"overall":{"N2":-1,"H2":-3,"NH3":2},"sources":["10.1021/jp047349j","10.1038/ncomms7731","10.1039/c6sc00767h"],"descriptor_range":[-1.6,0.4],"site_assumptions":"One uniform site family; 20 micromol accessible sites per gram catalyst; 5 wt% active metal; no transport limitation; nitrogen adsorption controls scaling of N-derived intermediates.","stronger_binding":"more_negative","lab_conditions":{"T_K":673.15,"p_bar":100.0},"reference_metal":"Fe","reference_metal_price_usd_per_kg":8.0}
DESCRIPTORS={"Mo":{"value":-1.25,"source":"10.1021/jp047349j","location":"ammonia-synthesis nitrogen-binding trend/volcano data","metal_price_usd_per_kg":91.22728409215301},"Fe":{"value":-0.92,"source":"10.1021/jp047349j","location":"ammonia-synthesis nitrogen-binding trend/volcano data","metal_price_usd_per_kg":8.0},"Ru":{"value":-0.72,"source":"10.1021/jp047349j","location":"ammonia-synthesis nitrogen-binding trend/volcano data","metal_price_usd_per_kg":53852.5},"Co":{"value":-0.55,"source":"10.1021/jp047349j","location":"ammonia-synthesis nitrogen-binding trend/volcano data","metal_price_usd_per_kg":56.28401553583051},"Ni":{"value":-0.35,"source":"10.1021/jp047349j","location":"ammonia-synthesis nitrogen-binding trend/volcano data","metal_price_usd_per_kg":16.9094555095895}}
KB=8.617333262145e-5
SITE_MOL_PER_KG=0.020
METAL_LOADING_WT_PCT=5.0
MW_NH3=17.031

def _kp(T):
    return math.exp(-((-92220.0-T*(-210.1))/(8.314462618*T)))

def _spec(D,T,p,product_fraction=1e-8):
    if isinstance(p,dict):
        gases={"N2":max(float(p["N2"]),1e-300),"H2":max(float(p["H2"]),1e-300),"NH3":max(float(p["NH3"]),1e-300)}
    else:
        total=max(float(p),1e-9); z=max(min(product_fraction,0.95),1e-12); prem=total*(1-z)
        gases={"N2":0.25*prem,"H2":0.75*prem,"NH3":total*z}
    desired=-KB*T*math.log(max(_kp(T),1e-300))
    nh3_corr=(desired+0.96)/2.0
    steps=[{"name":"N2_dissociation","stoich":{"N2":-1,"*":-2,"N":2},"dE":{"a":0.0,"b":2.0},"Ea":{"a":1.50,"b":0.80}},{"name":"sequential_N_hydrogenation_and_NH3_desorption","stoich":{"N":-2,"H2":-3,"NH3":2,"*":2},"dE":{"a":-0.96,"b":-2.0},"Ea":{"a":1.05,"b":-0.55}}]
    return {"species":{"N":1},"gases":gases,"T_K":T,"descriptor":D,"steps":steps,"overall":ATOMIC["overall"],"gas_corrections":{"N2":0.0,"H2":0.0,"NH3":nh3_corr}}

def net_tof(D,T_K,p_bar):
    try:return float(solve(_spec(float(D),float(T_K),p_bar),drc=False)["TOF"])
    except Exception:return 0.0

def logtof(D,T_K,p_bar):
    v=net_tof(D,T_K,p_bar)
    return math.log10(v) if v>1e-300 else -300.0

def _rate(D,T,p):
    return max(0.0,net_tof(D,T,p))*SITE_MOL_PER_KG*3600.0*MW_NH3/1000.0

def _nearest_metal(D):return min(DESCRIPTORS,key=lambda m:abs(DESCRIPTORS[m]["value"]-D))

def record_from_descriptor(D,metal_price_usd_per_kg=None):
    D=float(D); metal=_nearest_metal(D); price=DESCRIPTORS[metal]["metal_price_usd_per_kg"] if metal_price_usd_per_kg is None else float(metal_price_usd_per_kg)
    return {"T_K":673.15,"P_bar":100.0,"X":0.10,"S":1.0,"r":max(_rate(D,673.15,100.0),1e-12),"y_key":0.25,"y_cofeed":0.75,"t_cycle_h":24000.0,"components":[[metal,5.0]],"catalyst":"descriptor %.4f eV (%s-like)"%(D,metal),"descriptor":D,"metal_price_usd_per_kg":price,"metal_loading_wt_pct":5.0}

def rate_from_descriptor(D,rec):return max(_rate(float(D),float(rec["T_K"]),float(rec["P_bar"])),1e-300)
