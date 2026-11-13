import csv, json, math
from pathlib import Path
import numpy as np

REACTION = {
    "key": "CO2", "product": "CH3OH", "cofeed": "H2",
    "MW": {"CO2": 44.0095, "H2": 2.01588, "CH3OH": 32.04186, "H2O": 18.01528, "CO": 28.0101},
    "nu": {"CO2": -1.0, "H2": -3.0, "CH3OH": 1.0, "H2O": 1.0}
}

PARAMS = {}
with Path(__file__).with_name("sources.csv").open(newline="") as _f:
    for _r in csv.DictReader(_f):
        PARAMS[_r["parameter"]] = float(_r["value"])
with Path(__file__).with_name("basis.json").open() as _f:
    _basis = json.load(_f)

def _flatten_basis(obj, prefix="basis"):
    if isinstance(obj, dict):
        if "value" in obj and isinstance(obj["value"], (int, float)):
            PARAMS[prefix] = float(obj["value"])
        else:
            for k, v in obj.items():
                if k not in ("evidence", "battery_limit", "purchased_preheat_reason", "zero_duty_evidence"):
                    _flatten_basis(v, prefix + "." + k)
_flatten_basis(_basis)

def _p(k):
    return float(PARAMS[k])

def _equilibrium_K(T):
    R = 8.314462618
    T0 = 298.15
    dH0 = _p("thermo.dH_methanol_kJ_per_mol") * 1000.0
    dG0 = _p("thermo.dG_methanol_298_kJ_per_mol") * 1000.0
    dCp = _p("thermo.dCp_methanol_J_per_molK")
    dS0 = (dH0 - dG0) / T0
    dH = dH0 + dCp * (T - T0)
    dS = dS0 + dCp * math.log(T / T0)
    dG = dH - T * dS
    return math.exp(max(-80.0, min(80.0, -dG / (R * T))))

def _outlet_state(x, S, P, purge, co_recycle=True):
    x = max(1e-10, min(0.999, x)); S = max(1e-6, min(0.999999, S))
    co_in = ((1.0 - purge) / purge) * x * (1.0 - S) if co_recycle else 0.0
    n = {"CO2": 1.0 - x, "H2": 3.0 - x * (1.0 + 2.0 * S),
         "CH3OH": x * S, "H2O": x, "CO": co_in + x * (1.0 - S)}
    nt = sum(max(0.0, v) for v in n.values())
    y = {k: max(0.0, v) / nt for k, v in n.items()}
    q = (max(y["CH3OH"],1e-30) * max(y["H2O"],1e-30) /
         (max(y["CO2"],1e-30) * max(y["H2"],1e-30)**3)) / max(P,1e-9)**2
    return y, q

def _xeq(T, P, S, purge, co_recycle=True):
    K = _equilibrium_K(T)
    lo, hi = 1e-8, min(0.98, 3.0 / max(1.0 + 2.0*S, 1e-9) * 0.999)
    if _outlet_state(hi, S, P, purge, co_recycle)[1] < K:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _outlet_state(mid, S, P, purge, co_recycle)[1] < K: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

def _compressor(kmol, Tin, Pin, Pout):
    if kmol <= 0.0 or Pout <= Pin:
        return 0.0
    eta = _p("compressor.isentropic_efficiency")
    R = 8.314462618
    gamma = 1.30
    ratio = Pout / Pin
    stages = max(1, int(math.ceil(math.log(ratio) / math.log(4.0))))
    rs = ratio ** (1.0 / stages)
    w_kJ_per_mol = stages * (gamma/(gamma-1.0)) * R * Tin * (rs**((gamma-1.0)/gamma)-1.0) / eta / 1000.0
    return kmol * 1000.0 * w_kJ_per_mol / 1e6

def _catalyst_price(components):
    price = _p("price.catalyst_support_and_manufacturing")
    if components is None: return price
    if isinstance(components, str):
        try: components = json.loads(components)
        except Exception: return price
    vals=[]
    for item in components:
        if not isinstance(item,(list,tuple)) or len(item)<2 or item[1] is None: continue
        try: vals.append((str(item[0]), max(0.0,float(item[1]))))
        except Exception: pass
    total=sum(v for _,v in vals); scale=100.0/total if total>100.0 else 1.0
    for el, wt in vals:
        key="price.metal_"+el
        if key in PARAMS: price += (wt*scale/100.0)*_p(key)
    return price

def _activity(rec, T, P, x, S, purge):
    r=max(float(rec.get("r",0.0) or 0.0),1e-9)
    Tl=max(float(rec.get("T_K",T) or T),300.0); Pl=max(float(rec.get("P_bar",P) or P),1.0)
    yco2=max(float(rec.get("y_key",0.25) or 0.25),1e-4)
    yh2=max(float(rec.get("y_cofeed",rec.get("y_h2",0.75)) or 0.75),1e-4)
    Xl=max(1e-6,min(0.95,float(rec.get("X",0.05) or 0.05)))
    Sl=max(1e-4,min(0.9999,float(rec.get("S",S) or S)))
    _, ql=_outlet_state(Xl,Sl,Pl,1.0,False); Kl=_equilibrium_K(Tl)
    dfl=max(_p("kinetics.minimum_driving_force"),1.0-ql/Kl)
    _, qp=_outlet_state(x,S,P,purge,True); Kp=_equilibrium_K(T)
    dfp=max(_p("kinetics.minimum_driving_force"),1.0-qp/Kp)
    Ea=_p("kinetics.activation_energy_J_per_mol"); R=8.314462618
    arr=math.exp(max(-20.0,min(20.0,-Ea/R*(1.0/T-1.0/Tl))))
    yin_co=1.0; yin_h2=3.0; co_in=((1-purge)/purge)*x*(1-S); nt=yin_co+yin_h2+co_in
    pco2=P*yin_co/nt; ph2=P*yin_h2/nt
    press=(pco2/max(Pl*yco2,1e-6))**_p("kinetics.order_CO2")*(ph2/max(Pl*yh2,1e-6))**_p("kinetics.order_H2")
    fac=arr*press*dfp/dfl; cap=_p("kinetics.max_activity_extrapolation_factor")
    return r*max(1.0/cap,min(cap,fac))

def _deactivation(rec):
    tc=rec.get("t_cycle_h",None)
    try: tc=float(tc)
    except Exception: tc=float("nan")
    hours=_p("basis.operating_hours_per_y")
    if math.isfinite(tc) and tc>0:
        k=-math.log(0.9)/tc; f=max(0.05,min(0.95,_p("catalyst.replacement_activity_fraction")))
        life_h=-math.log(f)/k; avg=(1.0-f)/(-math.log(f))
        return max(life_h/hours,0.02),avg
    return _p("catalyst.default_life_y"),_p("catalyst.default_average_activity")

def _evaluate(rec,T,P,x):
    MW=REACTION["MW"]; cap=_p("basis.capacity_t_per_y"); hours=_p("basis.operating_hours_per_y")
    S=max(0.02,min(0.999,float(rec.get("S",0.5) or 0.5))); purge=_p("process.purge_fraction")
    recov=_p("process.methanol_recovery"); cfrac=_p("process.methanol_condensation_fraction"); wfrac=_p("process.water_condensation_fraction")
    nprod=1000.0/MW["CH3OH"]; nrxn=nprod/max(recov*cfrac,1e-9); nco=nrxn*(1.0-S)/S
    F=nrxn/(x*S); consumed=nrxn+nco
    co2_purge=purge*(1.0-x)*F; co2_fresh=consumed+co2_purge
    h2_consumed=3.0*nrxn+nco; h2_out=max(0.0,3.0*F-h2_consumed); h2_purge=purge*h2_out; h2_fresh=h2_consumed+h2_purge
    co_in=((1.0-purge)/purge)*nco; recycle_co2=(1.0-purge)*(1.0-x)*F; recycle_h2=(1.0-purge)*h2_out
    recycle_kmol=recycle_co2+recycle_h2+co_in
    reactor_kmol=F+3.0*F+co_in
    rate=_activity(rec,T,P,x,S,purge); life_y,avg_act=_deactivation(rec)
    production_kg_h=cap*1000.0/hours; cat_kg=production_kg_h/max(rate*avg_act,1e-12); cat_m3=cat_kg/_p("catalyst.bulk_density_kg_per_m3")
    cat_price=_catalyst_price(rec.get("components",rec.get("elements"))); cat_annual=cat_kg*cat_price/max(life_y,1e-6)
    PinCO2=_p("basis.feeds.CO2.P_bar"); PinH2=_p("basis.feeds.H2.P_bar"); Tin=_p("compressor.intercool_temperature_K"); TinCO2=_p("basis.feeds.CO2.T_K"); TinH2=_p("basis.feeds.H2.T_K")
    e_co2=_compressor(co2_fresh,TinCO2,PinCO2,P); e_h2=_compressor(h2_fresh,TinH2,PinH2,P)
    e_rec=_compressor(recycle_kmol,Tin,max(P-_p("process.recycle_pressure_drop_bar"),1.0),P)
    dH_T=_p("thermo.dH_methanol_kJ_per_mol")+_p("thermo.dCp_methanol_J_per_molK")*(T-298.15)/1000.0
    reactor_heat=nprod*dH_T/1000.0
    sensible=max(0.0,reactor_kmol*0.035*(T-Tin)/1000.0)
    recovered=sensible*_p("process.feed_preheat_recovery_fraction")
    condenser_cooling=max(0.0,-reactor_heat)+max(0.0,sensible-recovered)+nrxn*0.035+nco*0.040
    water_rxn=nrxn+nco; water_liq=water_rxn*wfrac; meoh_liq=nrxn*cfrac
    crude_t=(water_liq*MW["H2O"]+meoh_liq*MW["CH3OH"])/1000.0
    dist_heat=crude_t*_p("process.distillation_energy_GJ_per_t_feed")
    purity=_p("basis.product.CH3OH.purity_mol_frac"); product_water=nprod*(1.0-purity)/purity
    wastewater_kmol=max(0.0,water_liq-product_water); wastewater_t=wastewater_kmol*MW["H2O"]/1000.0
    ww_energy=wastewater_t*_p("process.wastewater_energy_GJ_per_t")
    cool_elec=condenser_cooling*_p("process.cooling_electricity_GJ_per_GJ")
    primary=_p("process.electricity_primary_energy_factor")
    scale=(cap/_p("capital.reference_capacity_t_per_y"))**_p("capital.scaling_exponent")
    tph=cap/hours
    def mw(e): return e*tph/3.6
    def comp_cap(e): return max(_p("capital.compressor_min_usd"),_p("capital.compressor_usd_per_MW")*mw(e))
    c_co2=comp_cap(e_co2); c_h2=comp_cap(e_h2); c_rec=_p("capital.compressor_usd_per_MW")*mw(e_rec)
    c_mix=_p("capital.mixer_usd")*scale
    c_hx=max(_p("capital.heat_exchanger_min_usd"),_p("capital.heat_exchanger_usd_per_MW")*mw(recovered))
    c_reactor=_p("capital.reactor_base_usd")*scale*(1.0+_p("capital.reactor_inventory_factor")*(cat_m3/_p("capital.reference_catalyst_volume_m3"))**0.6)
    c_cond=max(_p("capital.heat_exchanger_min_usd"),_p("capital.heat_exchanger_usd_per_MW")*mw(condenser_cooling))
    c_ko=_p("capital.knockout_base_usd")*scale*(max(reactor_kmol,1.0)/(4.0*nprod))**0.35
    c_split=_p("capital.splitter_usd")*scale
    c_dist=_p("capital.distillation_base_usd")*(max(crude_t*cap,1.0)/_p("capital.reference_capacity_t_per_y"))**_p("capital.scaling_exponent")
    c_cool=_p("capital.cooling_system_base_usd")*(max(mw(condenser_cooling),0.1)/_p("capital.reference_cooling_MW"))**_p("capital.scaling_exponent")
    c_ww=_p("capital.wastewater_base_usd")*scale*max(wastewater_t,0.05)**0.5
    direct=c_co2+c_h2+c_mix+c_hx+c_reactor+c_cond+c_ko+c_split+c_rec+c_dist+c_cool+c_ww
    c_off=_p("capital.offsites_fraction_direct")*direct; c_ww_off=c_ww+c_off
    capex=c_co2+c_h2+c_mix+c_hx+c_reactor+c_cond+c_ko+c_split+c_rec+c_dist+c_cool+c_ww_off
    units=[
      {"name":"CO2 feed compressor","type":"compressor","kmol_per_t":co2_fresh,"T_in_K":TinCO2,"P_in_bar":PinCO2,"P_out_bar":P,"power_GJ_per_t":e_co2,"purchased_energy_GJ_per_t":e_co2*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_co2,"electricity_GJ_per_t":e_co2},
      {"name":"H2 feed compressor","type":"compressor","kmol_per_t":h2_fresh,"T_in_K":TinH2,"P_in_bar":PinH2,"P_out_bar":P,"power_GJ_per_t":e_h2,"purchased_energy_GJ_per_t":e_h2*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_h2,"electricity_GJ_per_t":e_h2},
      {"name":"Synthesis feed mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_mix},
      {"name":"Feed effluent exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered,"capex_usd":c_hx},
      {"name":"Methanol synthesis reactor","type":"reactor","purchased_energy_GJ_per_t":max(0.0,reactor_heat),"internal_fuel_GJ_per_t":0.0,"heat_duty_GJ_per_t":reactor_heat,"capex_usd":c_reactor,"catalyst_kg":cat_kg},
      {"name":"Effluent condenser","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"cooling_duty_GJ_per_t":condenser_cooling,"capex_usd":c_cond},
      {"name":"High pressure knockout","type":"knockout","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"cooling_duty_GJ_per_t":0.0,"capex_usd":c_ko},
      {"name":"Recycle purge splitter","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_split},
      {"name":"Recycle compressor","type":"compressor","kmol_per_t":recycle_kmol,"T_in_K":Tin,"P_in_bar":max(P-_p("process.recycle_pressure_drop_bar"),1.0),"P_out_bar":P,"power_GJ_per_t":e_rec,"purchased_energy_GJ_per_t":e_rec*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_rec,"electricity_GJ_per_t":e_rec},
      {"name":"Methanol purification","type":"separation","feed":{"kmol_per_t":meoh_liq+water_liq,"mol_frac":{"CH3OH":meoh_liq/(meoh_liq+water_liq),"H2O":water_liq/(meoh_liq+water_liq)}},"outlets":[{"kmol_per_t":nprod+product_water,"mol_frac":{"CH3OH":purity,"H2O":1.0-purity}},{"kmol_per_t":max(0.0,meoh_liq-nprod)+wastewater_kmol,"mol_frac":{"CH3OH":max(0.0,meoh_liq-nprod)/max(max(0.0,meoh_liq-nprod)+wastewater_kmol,1e-12),"H2O":wastewater_kmol/max(max(0.0,meoh_liq-nprod)+wastewater_kmol,1e-12)}}],"purchased_energy_GJ_per_t":dist_heat,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"capex_usd":c_dist,"natural_gas_GJ_per_t":dist_heat},
      {"name":"Cooling water system","type":"offsites","purchased_energy_GJ_per_t":cool_elec*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_cool,"electricity_GJ_per_t":cool_elec},
      {"name":"Wastewater treatment and plant offsites","type":"offsites","purchased_energy_GJ_per_t":ww_energy,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_ww_off,"natural_gas_GJ_per_t":ww_energy}
    ]
    elec=sum(u.get("electricity_GJ_per_t",0.0) for u in units); gas=sum(u.get("natural_gas_GJ_per_t",0.0) for u in units)+max(0.0,reactor_heat)
    feed_cost=h2_fresh*MW["H2"]*_p("price.hydrogen")+co2_fresh*MW["CO2"]/1000.0*_p("price.carbon_dioxide")
    energy_cost=elec/3.6*_p("price.electricity")+gas*_p("price.natural_gas")
    capital_cost=capex*(_p("finance.capital_recovery_factor")+_p("finance.fixed_om_fraction_of_capex"))/cap
    catalyst_cost=cat_annual/cap; other=0.0
    parts={"feed":feed_cost,"energy":energy_cost,"capital":capital_cost,"catalyst":catalyst_cost,"other":other}
    cooling_makeup_t=0.01
    methanol_loss=nrxn-nprod
    water_purge=water_rxn*(1.0-wfrac)
    boundary_in={"CO2":co2_fresh*MW["CO2"]/1000.0,"H2":h2_fresh*MW["H2"]/1000.0,"H2O":cooling_makeup_t}
    boundary_out={"CH3OH":nprod*MW["CH3OH"]/1000.0,"H2O":water_rxn*MW["H2O"]/1000.0+cooling_makeup_t,"CO":nco*MW["CO"]/1000.0,"CO2":co2_purge*MW["CO2"]/1000.0,"H2":h2_purge*MW["H2"]/1000.0}
    # Allocate all reacted methanol and water among product, wastewater and trace purge while retaining total boundary species.
    boundary_out["CH3OH"] += methanol_loss*MW["CH3OH"]/1000.0
    reactor_feed_total=F+3.0*F+co_in
    feed_y={"CO2":F/reactor_feed_total,"H2":3.0*F/reactor_feed_total,"CO":co_in/reactor_feed_total,"CH3OH":0.0,"H2O":0.0}
    primary_energy=sum(u.get("purchased_energy_GJ_per_t",0.0) for u in units)
    return {"cost_usd_per_t":sum(parts.values()),"parts":parts,"operating":{"T_K":T,"P_bar":P,"per_pass_conversion":x},"balances":{"key_feed_t_per_t":boundary_in["CO2"],"energy_GJ_per_t":primary_energy,"capex_usd":capex,"capacity_t_per_y":cap},"physics":{"reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":feed_y,"per_pass_conversion":x,"heat_duty_GJ_per_t":reactor_heat},"boundary":{"in_t_per_t":boundary_in,"out_t_per_t":boundary_out},"units":units}}

def plant_cost(rec):
    S=max(0.02,min(0.999,float(rec.get("S",0.5) or 0.5)))
    Tmin=_p("operation.T_min_K"); Tmax=_p("operation.T_max_K"); Tl=float(rec.get("T_K",523.15) or 523.15)
    Ts=np.unique(np.clip(np.array([Tl-20.0,Tl,Tl+20.0,Tmin,Tmax]),Tmin,Tmax))
    Pmin=_p("operation.P_min_bar"); Pmax=_p("operation.P_max_bar"); Pl=float(rec.get("P_bar",50.0) or 50.0)
    Ps=np.unique(np.clip(np.array([Pmin,Pl,50.0,75.0,Pmax]),Pmin,Pmax))
    best=None
    for T in Ts:
        for P in Ps:
            xe=_xeq(float(T),float(P),S,_p("process.purge_fraction"),True)*_p("operation.equilibrium_fraction")
            xe=min(xe,_p("operation.selectivity_conversion_cap_intercept")+_p("operation.selectivity_conversion_cap_slope")*S)
            xmin=_p("operation.minimum_conversion")
            if xe<=xmin: xs=np.array([max(0.005,0.8*xe)])
            else: xs=np.linspace(xmin,xe,9)
            for x in xs:
                try: ans=_evaluate(rec,float(T),float(P),float(x))
                except Exception: continue
                if math.isfinite(ans["cost_usd_per_t"]) and (best is None or ans["cost_usd_per_t"]<best["cost_usd_per_t"]): best=ans
    if best is None: raise ValueError("no feasible operating point")
    return best

def reference():
    record={"T_K":533.15,"P_bar":28.0,"X":0.080,"S":0.711,"r":0.4003,"y_key":0.25,"y_cofeed":0.75,"t_cycle_h":294.86887,"components":[["Cu",52.82],["Zn",1.12]],"catalyst":"Ce-CuZn (10.1038/s41467-024-46513-3)"}
    out=plant_cost(record); out["name"]="100,000 t/y recycled CO2-to-methanol reference plant"; out["record"]=record
    return out
