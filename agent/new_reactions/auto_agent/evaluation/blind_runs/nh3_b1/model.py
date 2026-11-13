import math, csv
import numpy as np
from scipy.optimize import brentq, minimize_scalar

REACTION = {"key":"N2","product":"NH3","cofeed":"H2","MW":{"N2":28.0134,"H2":2.01588,"NH3":17.03052},"nu":{"N2":-1,"H2":-3,"NH3":2}}

PARAMS = {'NH3_condensation_duty_GJ_per_t': 1.37,
 'base_capacity_t_per_y': 330000.0,
 'base_reactor_catalyst_volume_m3': 100.0,
 'basis.capacity_t_per_y': 330000.0,
 'basis.feeds.H2.P_bar': 1.0,
 'basis.feeds.H2.T_K': 298.15,
 'basis.feeds.H2.purity_mol_frac': 1.0,
 'basis.feeds.H2O.P_bar': 3.0,
 'basis.feeds.H2O.T_K': 298.15,
 'basis.feeds.H2O.purity_mol_frac': 1.0,
 'basis.feeds.N2.P_bar': 1.0,
 'basis.feeds.N2.T_K': 298.15,
 'basis.feeds.N2.purity_mol_frac': 1.0,
 'basis.operating_hours_per_y': 8000.0,
 'basis.product.NH3.P_bar': 20.0,
 'basis.product.NH3.purity_mol_frac': 1.0,
 'basis.utilities.ambient_temperature': 298.15,
 'basis.utilities.cooling_water_return_temperature': 308.15,
 'basis.utilities.cooling_water_supply_temperature': 298.15,
 'basis.utilities.electricity_primary_energy_factor': 2.5,
 'capex.ammonia_condenser': 18000000.0,
 'capex.ammonia_converter': 25000000.0,
 'capex.ammonia_separator': 8000000.0,
 'capex.feed_effluent_exchanger': 15000000.0,
 'capex.feed_mixer': 1000000.0,
 'capex.makeup_compressor': 20000000.0,
 'capex.product_letdown_storage': 15000000.0,
 'capex.purge_splitter': 500000.0,
 'capex.recycle_compressor': 12000000.0,
 'capex.utilities_offsites': 25000000.0,
 'capex.waste_heat_boiler': 12000000.0,
 'capex_scale_exponent': 0.6,
 'catalyst_bulk_density_kg_per_m3': 1000.0,
 'compressor_installed_usd_per_kW': 2000.0,
 'condenser_COP': 3.0,
 'condenser_temperature_K': 248.15,
 'default_catalyst_life_y': 3.0,
 'equilibrium_deltaH_J_per_mol_rxn': -92220.0,
 'equilibrium_deltaS_J_per_molK_rxn': -209.3,
 'feed_effluent_exchanger_effectiveness': 0.8,
 'gas_sensible_heat_kJ_per_kmol_K': 31.0,
 'loop_pressure_drop_bar': 5.0,
 'makeup_compressor_efficiency': 0.75,
 'minimum_rate_kg_per_kg_h': 1e-06,
 'nitrogen_electricity_kWh_per_kg': 0.2,
 'offsites_electric_GJ_per_t': 0.02,
 'pressure_capex_exponent': 0.25,
 'price.capital_recovery_factor': 0.0944,
 'price.catalyst_support_and_manufacturing': 20.0,
 'price.electricity': 80.0,
 'price.fixed_om_fraction_of_capex': 0.04,
 'price.hydrogen': 3.0,
 'price.metal_Al': 3.9683,
 'price.metal_B': 1.0,
 'price.metal_Ba': 0.3569000679809653,
 'price.metal_Ca': 0.3637940925436203,
 'price.metal_Ce': 2.1005306603773586,
 'price.metal_Co': 56.28401553583051,
 'price.metal_Cu': 13.889122517655,
 'price.metal_Fe': 8.0,
 'price.metal_K': 1.4455393066229791,
 'price.metal_La': 1.1728,
 'price.metal_Mg': 2.5,
 'price.metal_Mn': 0.45,
 'price.metal_Mo': 91.22728409215301,
 'price.metal_Ni': 16.9094555095895,
 'price.metal_Ru': 53852.5,
 'price.metal_Si': 2.866006,
 'price.metal_W': 149.97,
 'price.metal_Y': 40.0,
 'price.metal_Zr': 22.0,
 'purge_fraction': 0.01,
 'reaction_heat_GJ_per_t_NH3': 2.708,
 'recycle_compressor_efficiency': 0.78,
 'reference_P_bar': 150.0,
 'reference_T_K': 700.0,
 'reference_X': 0.15,
 'reference_r': 0.5,
 'reference_t_cycle_h': 24000.0,
 'separation_electric_GJ_per_t_at_reference': 0.15,
 'separator_NH3_recovery': 1.0,
 'unknown_Co_loading_fraction': 0.4,
 'unknown_Fe_loading_fraction': 0.8,
 'unknown_Mo_loading_fraction': 0.2,
 'unknown_Ru_loading_fraction': 0.05,
 'waste_heat_recovery_fraction': 0.7}

def _p(k): return float(PARAMS[k])

def _kp(T):
    R=8.314462618
    dg=_p("equilibrium_deltaH_J_per_mol_rxn")-T*_p("equilibrium_deltaS_J_per_molK_rxn")
    return math.exp(max(-100.0,min(100.0,-dg/(R*T))))

def _state(X,P,yN=0.25,yH=0.75):
    e=yN*X
    nN=max(1e-30,yN-e); nH=max(1e-30,yH-3*e); nA=max(1e-30,2*e)
    nt=nN+nH+nA
    return nN/nt,nH/nt,nA/nt

def _q(X,P,yN=0.25,yH=0.75):
    yn,yh,ya=_state(X,P,yN,yH)
    return (ya*P)**2/max(1e-300,(yn*P)*(yh*P)**3)

def _xeq(T,P,yN=0.25,yH=0.75):
    xmax=min(0.999999,0.999999*yH/(3*yN))
    K=_kp(T)
    f=lambda x: math.log(max(_q(x,P,yN,yH),1e-300))-math.log(K)
    try: return brentq(f,1e-12,xmax,maxiter=200)
    except Exception: return max(1e-8,min(xmax,0.05))

def _drive(T,P,X,yN=0.25,yH=0.75):
    return max(1e-6,1.0-_q(X,P,yN,yH)/_kp(T))

def _metal_price(symbol):
    return PARAMS.get("price.metal_"+symbol,0.0)

def _cat_price(rec):
    support=_p("price.catalyst_support_and_manufacturing")
    comps=rec.get("components") or []
    load={}
    for c in comps:
        if isinstance(c,(list,tuple)) and len(c)>=2:
            el,w=c[0],c[1]
        elif isinstance(c,dict):
            el=c.get("element") or c.get("component"); w=c.get("wt_pct",c.get("loading_wt_pct"))
        else: continue
        if w is not None:
            try: load[str(el)]=max(0.0,float(w)/100.0)
            except Exception: pass
    name=str(rec.get("catalyst",rec.get("name","")))
    for el,key in [("Ru","unknown_Ru_loading_fraction"),("Fe","unknown_Fe_loading_fraction"),("Co","unknown_Co_loading_fraction"),("Mo","unknown_Mo_loading_fraction")]:
        if el in name and el not in load: load[el]=_p(key)
    total=sum(load.values())
    if total>1.0: load={k:v/total for k,v in load.items()}
    if rec.get("metal_price_usd_per_kg") is not None:
        loading=sum(load.values()) if load else _p("unknown_Ru_loading_fraction")
        return support+loading*float(rec["metal_price_usd_per_kg"])
    return support+sum(frac*_metal_price(el) for el,frac in load.items())

def _cap(base,through=1.0,pressure=1.0):
    return _p("capex."+base)*max(0.05,through)**_p("capex_scale_exponent")*max(0.2,pressure)**_p("pressure_capex_exponent")

def reference():
    rec={"T_K":_p("reference_T_K"),"P_bar":_p("reference_P_bar"),"X":_p("reference_X"),"S":1.0,"r":_p("reference_r"),"y_key":0.25,"y_cofeed":0.75,"t_cycle_h":_p("reference_t_cycle_h"),"components":[["Fe",90.0],["K",1.0],["Al",5.0]],"catalyst":"Industrial promoted iron reference"}
    ans=plant_cost(rec); ans["name"]="industrial promoted iron synthesis loop"; ans["record"]=rec; return ans

def plant_cost(rec):
    T=float(rec["T_K"]); P=max(1.01,float(rec["P_bar"])); r=max(_p("minimum_rate_kg_per_kg_h"),float(rec["r"])); S=max(1e-6,min(1.0,float(rec.get("S",1.0))))
    yN=float(rec.get("y_key",0.25) or 0.25); yH=float(rec.get("y_cofeed",0.75) or 0.75)
    Xlab=max(1e-10,float(rec.get("X",1e-6) or 1e-6)); xeq=_xeq(T,P,0.25,0.75)
    xeq_lab=_xeq(T,P,yN,yH)
    dlab=_drive(T,P,min(Xlab,0.999*xeq_lab),yN,yH)
    capacity=_p("basis.capacity_t_per_y"); hours=_p("basis.operating_hours_per_y"); kgph=capacity*1000.0/hours
    nprod=1000.0/REACTION["MW"]["NH3"]
    purge=_p("purge_fraction"); eta=_p("separator_NH3_recovery")
    elec_price=_p("price.electricity")
    primary=_p("basis.utilities.electricity_primary_energy_factor")
    capscale=capacity/_p("base_capacity_t_per_y")
    pscale=max(P,20.0)/150.0
    def calculate(X,detail=False):
        X=max(1e-8,min(X,0.995*xeq))
        reacted_N=nprod/(2.0*eta)
        loop_N=reacted_N/X; loop_H=3.0*loop_N
        eff_N=loop_N-reacted_N; eff_H=loop_H-3.0*reacted_N
        purge_N=purge*eff_N; purge_H=purge*eff_H
        fresh_N=reacted_N+purge_N; fresh_H=3.0*reacted_N+purge_H
        recycle_N=(1-purge)*eff_N; recycle_H=(1-purge)*eff_H
        recycle_kmol=recycle_N+recycle_H
        makeup_kmol=fresh_N+fresh_H
        feed_N_t=fresh_N*REACTION["MW"]["N2"]/1000.0
        feed_H_t=fresh_H*REACTION["MW"]["H2"]/1000.0
        h2_cost=feed_H_t*1000.0*_p("price.hydrogen")
        n2_kwh=feed_N_t*1000.0*_p("nitrogen_electricity_kWh_per_kg")
        n2_cost=n2_kwh*elec_price/1000.0
        feed_cost=h2_cost+n2_cost
        R=8.314462618
        PinN=_p("basis.feeds.N2.P_bar"); PinH=_p("basis.feeds.H2.P_bar"); Pin=min(PinN,PinH)
        wmake=0.0 if P<=Pin else makeup_kmol*R*_p("basis.feeds.N2.T_K")*math.log(P/Pin)/_p("makeup_compressor_efficiency")/1e6
        dp=min(_p("loop_pressure_drop_bar"),0.8*P)
        prec=max(0.2,P-dp)
        wrec=recycle_kmol*R*_p("basis.utilities.ambient_temperature")*math.log(P/prec)/_p("recycle_compressor_efficiency")/1e6
        circ=(loop_N+loop_H+nprod)/(4*reacted_N+nprod)
        sep_e=_p("separation_electric_GJ_per_t_at_reference")*max(1.0,circ)
        cond_duty=_p("NH3_condensation_duty_GJ_per_t")
        cond_e=cond_duty/_p("condenser_COP")
        off_e=_p("offsites_electric_GJ_per_t")
        electric=wmake+wrec+sep_e+cond_e+off_e
        energy_cost=electric/3.6*elec_price
        drive=_drive(T,P,X,0.25,0.75)
        netr=max(_p("minimum_rate_kg_per_kg_h"),r*S*drive/max(dlab,1e-4))
        inventory=kgph/netr
        catvol=inventory/_p("catalyst_bulk_density_kg_per_m3")
        through=max(0.1,(fresh_N+fresh_H+recycle_kmol)/(4*reacted_N))
        caps={
          "makeup_compressor":max(1e5,_p("compressor_installed_usd_per_kW")*(wmake*capacity/hours/3.6)*1000.0),
          "feed_mixer":_cap("feed_mixer",capscale*through,pscale),
          "feed_effluent_exchanger":_cap("feed_effluent_exchanger",capscale*through,pscale),
          "ammonia_converter":_cap("ammonia_converter",capscale*(1.0+catvol/_p("base_reactor_catalyst_volume_m3")),pscale),
          "waste_heat_boiler":_cap("waste_heat_boiler",capscale,pscale),
          "ammonia_condenser":_cap("ammonia_condenser",capscale*through,pscale),
          "ammonia_separator":_cap("ammonia_separator",capscale*through,pscale),
          "purge_splitter":_cap("purge_splitter",capscale*through,pscale),
          "recycle_compressor":max(1e5,_p("compressor_installed_usd_per_kW")*(wrec*capacity/hours/3.6)*1000.0),
          "product_letdown_storage":_cap("product_letdown_storage",capscale,1.0),
          "utilities_offsites":_cap("utilities_offsites",capscale,1.0)}
        capex=sum(caps.values())
        capital_cost=capex*(_p("price.capital_recovery_factor")+_p("price.fixed_om_fraction_of_capex"))/capacity
        tc=rec.get("t_cycle_h")
        life=_p("default_catalyst_life_y") if tc is None or not np.isfinite(float(tc)) or float(tc)<=0 else max(0.1,float(tc)/hours)
        cat_cost=inventory*_cat_price(rec)/life/capacity
        other=0.0
        total=feed_cost+energy_cost+capital_cost+cat_cost+other
        if not detail:return total
        reaction_heat=-(_p("reaction_heat_GJ_per_t_NH3")+0.000955*max(0.0,T-298.15))/eta
        recovered=-reaction_heat*_p("waste_heat_recovery_fraction")
        sep_feed={"kmol_per_t":eff_N+eff_H+nprod/eta,"mol_frac":{"N2":eff_N/(eff_N+eff_H+nprod/eta),"H2":eff_H/(eff_N+eff_H+nprod/eta),"NH3":(nprod/eta)/(eff_N+eff_H+nprod/eta)}}
        sep_liq={"kmol_per_t":nprod,"mol_frac":{"N2":0.0,"H2":0.0,"NH3":1.0}}
        sep_gas_k=eff_N+eff_H+nprod*(1/eta-1)
        sep_gas={"kmol_per_t":sep_gas_k,"mol_frac":{"N2":eff_N/max(sep_gas_k,1e-30),"H2":eff_H/max(sep_gas_k,1e-30),"NH3":nprod*(1/eta-1)/max(sep_gas_k,1e-30)}}
        units=[
          {"name":"makeup_compressor","type":"compressor","purchased_energy_GJ_per_t":wmake*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["makeup_compressor"],"kmol_per_t":makeup_kmol,"T_in_K":_p("basis.feeds.N2.T_K"),"P_in_bar":Pin,"P_out_bar":max(P,Pin),"power_GJ_per_t":wmake,"shaft_power_kW":wmake*capacity/hours/3.6*1000.0,"installed_usd_per_kW":_p("compressor_installed_usd_per_kW")},
          {"name":"feed_mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["feed_mixer"]},
          {"name":"feed_effluent_exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered*_p("feed_effluent_exchanger_effectiveness"),"capex_usd":caps["feed_effluent_exchanger"]},
          {"name":"ammonia_converter","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["ammonia_converter"],"heat_duty_GJ_per_t":reaction_heat,"catalyst_inventory_kg":inventory,"catalyst_volume_m3":catvol,"catalyst_price_usd_per_kg":_cat_price(rec),"catalyst_life_y":life},
          {"name":"waste_heat_boiler","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered*(1.0-_p("feed_effluent_exchanger_effectiveness")),"capex_usd":caps["waste_heat_boiler"]},
          {"name":"ammonia_condenser","type":"knockout","purchased_energy_GJ_per_t":cond_e*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["ammonia_condenser"],"cooling_duty_GJ_per_t":cond_duty},
          {"name":"ammonia_separator","type":"separation","purchased_energy_GJ_per_t":sep_e*primary,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"capex_usd":caps["ammonia_separator"],"feed":sep_feed,"outlets":[sep_liq,sep_gas]},
          {"name":"purge_splitter","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["purge_splitter"]},
          {"name":"recycle_compressor","type":"compressor","purchased_energy_GJ_per_t":wrec*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["recycle_compressor"],"kmol_per_t":recycle_kmol,"T_in_K":_p("basis.utilities.ambient_temperature"),"P_in_bar":prec,"P_out_bar":P,"power_GJ_per_t":wrec,"shaft_power_kW":wrec*capacity/hours/3.6*1000.0,"installed_usd_per_kW":_p("compressor_installed_usd_per_kW")},
          {"name":"product_letdown_storage","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["product_letdown_storage"]},
          {"name":"utilities_offsites","type":"offsites","purchased_energy_GJ_per_t":off_e*primary,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["utilities_offsites"]}]
        boundary_in={"N2":feed_N_t,"H2":feed_H_t}
        boundary_out={"NH3":1.0,"N2":purge_N*REACTION["MW"]["N2"]/1000.0,"H2":purge_H*REACTION["MW"]["H2"]/1000.0}
        return {"cost_usd_per_t":total,"parts":{"feed":feed_cost,"energy":energy_cost,"capital":capital_cost,"catalyst":cat_cost,"other":other},"operating":{"T_K":T,"P_bar":P,"per_pass_conversion":X},"balances":{"key_feed_t_per_t":loop_N*REACTION["MW"]["N2"]/(1000.0*S),"energy_GJ_per_t":electric*primary,"capex_usd":capex,"capacity_t_per_y":capacity},"physics":{"reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":{"N2":0.25,"H2":0.75,"NH3":0.0},"per_pass_conversion":X,"heat_duty_GJ_per_t":reaction_heat},"boundary":{"in_t_per_t":boundary_in,"out_t_per_t":boundary_out},"units":units}}
    xmax=max(1e-7,min(0.50,0.97*xeq))
    xmin=min(max(1e-6,0.005),0.25*xmax)
    if xmax<=xmin*1.001: xopt=0.5*xmax
    else:
        res=minimize_scalar(calculate,bounds=(xmin,xmax),method="bounded",options={"xatol":1e-7,"maxiter":120})
        xopt=float(res.x)
    return calculate(xopt,True)
