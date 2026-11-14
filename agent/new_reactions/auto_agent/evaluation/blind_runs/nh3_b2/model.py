import csv, math, json, os
import numpy as np

REACTION = {
    "key": "N2", "product": "NH3", "cofeed": "H2",
    "MW": {"N2": 28.014, "H2": 2.016, "NH3": 17.031},
    "nu": {"N2": -1, "H2": -3, "NH3": 2}
}

def _load_params():
    out = {}
    with open(os.path.join(os.path.dirname(__file__), "sources.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try: out[row["parameter"]] = float(row["value"])
            except (ValueError, TypeError): pass
    return out

PARAMS = _load_params()

def _p(k):
    return float(PARAMS[k])

def _kp(T):
    # Dimensionless Kp on a 1 bar standard state for N2+3H2=2NH3.
    dH = 2.0 * _p("heat.reaction_enthalpy_J_per_mol_NH3")
    dS = _p("heat.reaction_entropy_J_per_mol_reaction_K")
    dG = dH - T*dS
    return math.exp(max(-100.0, min(100.0, -dG/(8.314462618*T))))

def _stoich_outlet_y(x, nh3_in=0.0):
    n2, h2 = 1.0-x, 3.0*(1.0-x)
    nh3 = nh3_in + 2.0*x
    nt = n2+h2+nh3
    return {"N2": n2/nt, "H2": h2/nt, "NH3": nh3/nt}

def _q(y, P):
    return (max(y.get("NH3",0.0),1e-30)**2)/(max(y.get("N2",0.0),1e-30)*max(y.get("H2",0.0),1e-30)**3) / max(P,1e-9)**2

def _xeq(T, P):
    K = _kp(T)
    lo, hi = 0.0, 0.999999
    for _ in range(80):
        mid=(lo+hi)/2
        if _q(_stoich_outlet_y(mid),P) < K: lo=mid
        else: hi=mid
    return (lo+hi)/2

def _compressor_power(kmol, T, Pin, Pout, gamma, eta):
    if Pout <= Pin or kmol <= 0: return 0.0
    # kJ/kmol/K times kmol gives kJ; convert to GJ.
    w = kmol*8.314462618*T*(gamma/(gamma-1.0))*((Pout/Pin)**((gamma-1.0)/gamma)-1.0)/eta
    return w/1e6

def _metal_price(rec):
    components=rec.get("components",[])
    price = _p("price.catalyst_support_and_manufacturing")
    if not components: return price
    for item in components:
        if not isinstance(item,(list,tuple)) or len(item)<2: continue
        el, wt = str(item[0]), item[1]
        if wt is None: continue
        key="price.metal_"+el
        if key in PARAMS:
            price += max(0.0,float(wt))/100.0*_p(key)
    return price

def _lab_drive(rec):
    T=max(250.0,float(rec.get("T_K",700.0))); P=max(0.1,float(rec.get("P_bar",1.0)))
    X=min(0.98,max(0.0,float(rec.get("X",0.0))))
    y=_stoich_outlet_y(X)
    return max(0.02,1.0-_q(y,P)/max(_kp(T),1e-30))

def _rate_at(rec,T,P,x,nh3_in_ratio):
    r=max(1e-12,float(rec.get("r",1e-12)))
    Tl=max(250.0,float(rec.get("T_K",T))); Pl=max(0.1,float(rec.get("P_bar",P)))
    Ea=_p("kinetic.activation_energy_J_per_mol")
    arr=math.exp(max(-20.0,min(20.0,Ea/8.314462618*(1.0/Tl-1.0/T))))
    pscale=(P/Pl)**_p("kinetic.pressure_order_total")
    y=_stoich_outlet_y(x,nh3_in_ratio)
    drive=max(0.0,1.0-_q(y,P)/max(_kp(T),1e-30))
    scale=min(_p("kinetic.max_rate_scale"),arr*pscale*drive/_lab_drive(rec))
    return max(1e-12,r*scale)

def _evaluate(rec,T,P,x):
    MW=REACTION["MW"]
    cap=_p("basis.capacity_t_per_y"); hours=_p("basis.operating_hours_per_y")
    tph=cap/hours; kgph=tph*1000.0
    f=_p("operation.purge_fraction"); eta=_p("operation.nh3_condensation_recovery")
    nprod=1000.0/MW["NH3"]
    sep_nh3=nprod/eta
    purge_nh3=f*(1.0-eta)*sep_nh3
    gen=nprod+purge_nh3
    cN=0.5*gen; cH=1.5*gen
    loopN=cN/x; loopH=cH/x
    outN=loopN-cN; outH=loopH-cH
    purgeN=f*outN; purgeH=f*outH
    freshN=cN+purgeN; freshH=cH+purgeH
    Sel=max(1e-6,min(1.0,float(rec.get("S",1.0))))
    extraN=(1.0/Sel-1.0)*cN
    extraH=3.0*extraN
    freshN += extraN; freshH += extraH
    purgeN += extraN; purgeH += extraH
    rec_nh3=(1.0-f)*(1.0-eta)*sep_nh3
    nh3_in_ratio=rec_nh3/max(loopN,1e-30)
    rate=_rate_at(rec,T,P,x,nh3_in_ratio)
    avg_act=1.0-0.5*_p("catalyst.activity_loss_fraction_at_cycle")
    cat_kg=kgph*(gen/nprod)/(rate*avg_act)
    # Compressor work.
    TinH=_p("basis.feeds.H2.T_K"); TinN=_p("basis.feeds.N2.T_K")
    PinH=_p("basis.feeds.H2.P_bar"); PinN=_p("basis.feeds.N2.P_bar")
    ce=_p("compressor.isentropic_efficiency")
    wH=_compressor_power(freshH,TinH,PinH,P,_p("compressor.gamma_h2"),ce)
    wN=_compressor_power(freshN,TinN,PinN,P,_p("compressor.gamma_n2"),ce)
    gas_recycle=(1.0-f)*(outN+outH+(1.0-eta)*sep_nh3)
    wR=_compressor_power(gas_recycle,_p("basis.utilities.cooling_water_return_temperature"),P/_p("compressor.recycle_pressure_ratio"),P,_p("compressor.gamma_loop"),ce)
    rxn_dh=_p("heat.reaction_enthalpy_J_per_mol_NH3")+_p("heat.delta_cp_J_per_mol_NH3_K")*(T-298.15)
    rxn_heat=rxn_dh*gen/1e6
    recovered=max(0.0,-rxn_heat)*_p("heat.waste_heat_recovery_fraction")
    cooler_duty=(1.0-_p("heat.feed_effluent_recovery_fraction"))*_p("heat.sensible_cooling_GJ_per_t")+max(0.0,-rxn_heat-recovered)
    cool_elec=cooler_duty*_p("heat.cooling_electricity_GJ_per_GJ_removed")
    primary=_p("energy.electricity_primary_factor")
    # Capital scaling.
    capscale=(cap/_p("capital.reference_capacity_t_per_y"))**_p("capital.scale_exponent")
    pscale=(P/_p("capital.reference_pressure_bar"))**_p("capital.pressure_exponent")
    loopscale=((loopN+loopH+rec_nh3)/( (0.5/x)+(1.5/x) )) if x>0 else 1.0
    flowrel=max(0.2,(0.15/x))
    def C(name,extra=1.0): return _p("capital."+name+"_usd")*capscale*pscale*extra
    reactor_extra=max(_p("capital.reactor_min_scale"),(cat_kg/_p("catalyst.reference_inventory_kg"))**_p("capital.reactor_activity_scale_exponent"))
    capex={
      "hydrogen_feed_compressor":C("hydrogen_feed_compressor",max(0.5,(freshH/(1.5*nprod))**0.65)),
      "nitrogen_feed_compressor":C("nitrogen_feed_compressor",max(0.5,(freshN/(0.5*nprod))**0.65)),
      "synthesis_gas_mixer":C("synthesis_gas_mixer",flowrel**0.4),
      "feed_effluent_exchanger":C("feed_effluent_exchanger",flowrel**0.65),
      "ammonia_converter":C("ammonia_converter",reactor_extra),
      "waste_heat_boiler":C("waste_heat_boiler",(gen/nprod)**0.65),
      "final_product_cooler":C("final_product_cooler",flowrel**0.65),
      "ammonia_knockout":C("ammonia_knockout",flowrel**0.55),
      "purge_splitter":C("purge_splitter",flowrel**0.4),
      "recycle_compressor":C("recycle_compressor",flowrel**0.65),
      "product_and_offsites":_p("capital.product_and_offsites_usd")*(cap/_p("capital.reference_capacity_t_per_y"))**_p("capital.offsites_capacity_exponent")
    }
    total_capex=sum(capex.values())
    h2_t=freshH*MW["H2"]/1000.0; n2_t=freshN*MW["N2"]/1000.0
    purge_m={"H2":purgeH*MW["H2"]/1000.0,"N2":purgeN*MW["N2"]/1000.0,"NH3":purge_nh3*MW["NH3"]/1000.0}
    feed_cost=h2_t*1000.0*_p("price.hydrogen") + n2_t*1000.0*_p("feed.nitrogen_embodied_electricity_kWh_per_kg")*_p("price.electricity")/1000.0
    electric_GJ=wH+wN+wR+cool_elec
    energy_cost=electric_GJ/3.6*_p("price.electricity")
    annual_cap=( _p("price.capital_recovery_factor")+_p("price.fixed_om_fraction_of_capex") )*total_capex
    capital_cost=annual_cap/cap
    cycle=rec.get("t_cycle_h",None)
    try: cycle=float(cycle) if cycle is not None and float(cycle)>0 else _p("catalyst.default_cycle_h")
    except: cycle=_p("catalyst.default_cycle_h")
    cat_price=_metal_price(rec)
    catalyst_cost=cat_kg*cat_price/(cycle*tph)
    other=0.0
    parts={"feed":feed_cost,"energy":energy_cost,"capital":capital_cost,"catalyst":catalyst_cost,"other":other}
    units=[
      {"name":"hydrogen_feed_compressor","type":"compressor","purchased_energy_GJ_per_t":wH*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":capex["hydrogen_feed_compressor"],"kmol_per_t":freshH,"T_in_K":TinH,"P_in_bar":PinH,"P_out_bar":P,"power_GJ_per_t":wH,"shaft_electricity_GJ_per_t":wH,"primary_energy_factor":primary},
      {"name":"nitrogen_feed_compressor","type":"compressor","purchased_energy_GJ_per_t":wN*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":capex["nitrogen_feed_compressor"],"kmol_per_t":freshN,"T_in_K":TinN,"P_in_bar":PinN,"P_out_bar":P,"power_GJ_per_t":wN,"shaft_electricity_GJ_per_t":wN,"primary_energy_factor":primary},
      {"name":"synthesis_gas_mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":capex["synthesis_gas_mixer"]},
      {"name":"feed_effluent_exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":_p("heat.feed_effluent_recovery_fraction")*_p("heat.sensible_cooling_GJ_per_t"),"capex_usd":capex["feed_effluent_exchanger"]},
      {"name":"ammonia_converter","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"heat_duty_GJ_per_t":rxn_heat,"catalyst_inventory_kg":cat_kg,"catalyst_price_usd_per_kg":cat_price,"cycle_h":cycle,"annual_replacement_kg":cat_kg*hours/cycle,"sizing_product_kg_per_h":kgph,"effective_productivity_kg_per_kg_h":rate*avg_act,"inlet_kmol_per_t":{"N2":loopN,"H2":loopH,"NH3":rec_nh3},"outlet_kmol_per_t":{"N2":outN,"H2":outH,"NH3":sep_nh3},"reaction_extent_kmol_per_t":cN,"capex_usd":capex["ammonia_converter"]},
      {"name":"waste_heat_boiler","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered,"capex_usd":capex["waste_heat_boiler"]},
      {"name":"final_product_cooler","type":"heat_exchanger","purchased_energy_GJ_per_t":cool_elec*primary,"internal_fuel_GJ_per_t":0.0,"cooling_duty_GJ_per_t":cooler_duty,"capex_usd":capex["final_product_cooler"]},
      {"name":"ammonia_knockout","type":"knockout","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"cooling_duty_GJ_per_t":0.0,"capex_usd":capex["ammonia_knockout"]},
      {"name":"purge_splitter","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"purge_fraction":f,"purge_kmol_per_t":{"N2":purgeN,"H2":purgeH,"NH3":purge_nh3},"recycle_kmol_per_t":{"N2":(1-f)*outN,"H2":(1-f)*outH,"NH3":rec_nh3},"capex_usd":capex["purge_splitter"]},
      {"name":"recycle_compressor","type":"compressor","purchased_energy_GJ_per_t":wR*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":capex["recycle_compressor"],"kmol_per_t":gas_recycle,"T_in_K":_p("basis.utilities.cooling_water_return_temperature"),"P_in_bar":P/_p("compressor.recycle_pressure_ratio"),"P_out_bar":P,"power_GJ_per_t":wR,"shaft_electricity_GJ_per_t":wR,"primary_energy_factor":primary},
      {"name":"product_and_offsites","type":"offsites","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"product_pressure_bar":_p("basis.product.NH3.P_bar"),"product_NH3_mol_frac":1.0,"minimum_spec_mol_frac":_p("basis.product.NH3.purity_mol_frac"),"capex_usd":capex["product_and_offsites"]}
    ]
    sep_feed={"kmol_per_t":outN+outH+sep_nh3,"mol_frac":{"N2":outN/(outN+outH+sep_nh3),"H2":outH/(outN+outH+sep_nh3),"NH3":sep_nh3/(outN+outH+sep_nh3)}}
    gas=outN+outH+(1-eta)*sep_nh3
    # Add stream accounting to the knockout unit.
    units[7]["feed"]=sep_feed
    units[7]["outlets"]=[{"kmol_per_t":nprod,"mol_frac":{"NH3":1.0}},{"kmol_per_t":gas,"mol_frac":{"N2":outN/gas,"H2":outH/gas,"NH3":(1-eta)*sep_nh3/gas}}]
    yin={"N2":loopN/(loopN+loopH+rec_nh3),"H2":loopH/(loopN+loopH+rec_nh3),"NH3":rec_nh3/(loopN+loopH+rec_nh3)}
    return {"cost_usd_per_t":sum(parts.values()),"parts":parts,"operating":{"T_K":T,"P_bar":P,"per_pass_conversion":x},"balances":{"key_feed_t_per_t":n2_t/max(1e-9,x),"energy_GJ_per_t":sum(u["purchased_energy_GJ_per_t"] for u in units),"capex_usd":total_capex,"capacity_t_per_y":cap},"physics":{"reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":yin,"per_pass_conversion":x,"heat_duty_GJ_per_t":rxn_heat},"boundary":{"in_t_per_t":{"N2":n2_t,"H2":h2_t},"out_t_per_t":{"NH3":1.0+purge_m["NH3"],"N2":purge_m["N2"],"H2":purge_m["H2"]}},"units":units}}

def plant_cost(rec):
    T0=max(300.0,min(800.0,float(rec.get("T_K",_p("operation.reference_T_K")))))
    Ts=sorted(set([max(300.0,T0-25.0),T0,min(800.0,T0+25.0)]))
    Ps=np.linspace(_p("operation.loop_pressure_min_bar"),_p("operation.loop_pressure_max_bar"),int(round(_p("operation.pressure_grid_points"))))
    best=None
    for T in Ts:
      for P in Ps:
        lab_yN=max(1e-9,float(rec.get("y_key",0.25))); lab_yH=max(0.0,float(rec.get("y_cofeed",0.75)))
        stoich_cap=min(0.98,lab_yH/(3.0*lab_yN))
        xmax=min(stoich_cap,_p("operation.equilibrium_fraction_limit")*_xeq(T,P))
        if xmax <= _p("operation.min_conversion"): continue
        for x in np.linspace(_p("operation.min_conversion"),xmax,int(round(_p("operation.conversion_grid_points")))):
            z=_evaluate(rec,T,float(P),float(x))
            if math.isfinite(z["cost_usd_per_t"]) and (best is None or z["cost_usd_per_t"]<best["cost_usd_per_t"]): best=z
    if best is None:
        raise ValueError("No feasible equilibrium-limited operating point")
    return best

def reference():
    rec={"T_K":_p("operation.reference_T_K"),"P_bar":_p("operation.reference_P_bar"),"X":_p("operation.reference_X"),"S":_p("operation.reference_selectivity"),"r":_p("catalyst.reference_rate_kg_per_kg_h"),"y_key":_p("operation.reference_y_N2"),"y_cofeed":_p("operation.reference_y_H2"),"t_cycle_h":_p("catalyst.default_cycle_h"),"components":[["Fe",70.0],["K",1.0]],"catalyst":"conventional promoted iron"}
    out=plant_cost(rec)
    out.update({"name":"published-scale promoted-iron ammonia synthesis loop","record":rec})
    return out
