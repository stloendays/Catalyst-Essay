import csv, math, os
import os, csv, math
import numpy as np
from scipy.optimize import brentq, minimize_scalar

REACTION = {
    "key": "NH3", "product": "H2", "cofeed": None,
    "MW": {"NH3": 17.03052, "H2": 2.01588, "N2": 28.0134},
    "nu": {"NH3": -1.0, "N2": 0.5, "H2": 1.5}
}

def _load_params():
    out = {}
    with open(os.path.join(os.path.dirname(__file__), 'sources.csv'), newline='') as f:
        for row in csv.DictReader(f):
            out[row['parameter']] = float(row['value'])
    return out

PARAMS = _load_params()

def _p(name):
    return float(PARAMS[name])

def _equilibrium_conversion(T, P_bar):
    # Standard-state approximation for 2 NH3 -> N2 + 3 H2; used only as a feasibility ceiling.
    dH = 2.0 * _p('reaction_heat_GJ_per_kmol_NH3') * 1.0e6  # kJ per stoichiometric reaction
    dS = _p('reaction_entropy_kJ_per_kmol_K')
    R = _p('gas_constant_kJ_per_kmol_K')
    lnK = -(dH - T*dS)/(R*T)
    lnK = float(np.clip(lnK, -100.0, 100.0))
    K = math.exp(lnK)
    def logq(x):
        nt = 1.0 + x
        pnh3 = max((1.0-x)/nt*P_bar, 1e-300)
        ph2 = max(1.5*x/nt*P_bar, 1e-300)
        pn2 = max(0.5*x/nt*P_bar, 1e-300)
        return math.log(pn2) + 3.0*math.log(ph2) - 2.0*math.log(pnh3)
    target = math.log(max(K, 1e-300))
    f = lambda x: logq(x)-target
    try:
        return brentq(f, 1e-10, 1.0-1e-10)
    except ValueError:
        return 1e-10 if f(1e-10) > 0 else 1.0-1e-10

def _metal_price(symbol):
    key = 'price.metal_' + str(symbol)
    return _p(key) if key in PARAMS else _p('price.catalyst_support_and_manufacturing')

def _catalyst_price(rec):
    components = rec.get('components') or []
    weighted = 0.0
    known_fraction = 0.0
    for item in components:
        if isinstance(item, dict):
            symbol = item.get('component') or item.get('element')
            wt = item.get('loading_wt_pct')
        else:
            symbol = item[0] if len(item) else None
            wt = item[1] if len(item) > 1 else None
        if symbol and wt is not None and np.isfinite(float(wt)):
            frac = max(0.0, min(float(wt)/100.0, 1.0-known_fraction))
            weighted += frac*_metal_price(symbol)
            known_fraction += frac
    weighted += max(0.0, 1.0-known_fraction)*_p('price.catalyst_support_and_manufacturing')
    return weighted

def _record_value(rec, key, default):
    v = rec.get(key, default)
    try:
        v = float(v)
        return v if np.isfinite(v) else default
    except Exception:
        return default

def _capital_scale(base, throughput_factor=1.0):
    cap_ratio = _p('basis.capacity_t_per_y')/_p('reference_capacity_t_per_y')
    return base * max(cap_ratio*throughput_factor, 1e-9)**_p('capacity_scaling_exponent')

def _evaluate(rec, x):
    mw = REACTION['MW']
    capacity = _p('basis.capacity_t_per_y')
    hours = _p('basis.operating_hours_per_y')
    T = _record_value(rec, 'T_K', 673.15)
    P = _p('reactor_pressure_bar')
    S = min(max(_record_value(rec, 'S', 1.0), 1e-6), 1.0)
    psa_rec = _p('psa_h2_recovery')
    psa_purity = _p('basis.product.H2.purity_mol_frac')
    nh3_rec = _p('nh3_knockout_recovery')

    h2_product_kmol = 1000.0/mw['H2']
    h2_gross_kmol = h2_product_kmol/psa_rec
    nh3_reacted_kmol = (2.0/3.0)*h2_gross_kmol/S
    n2_kmol = 0.5*nh3_reacted_kmol*S
    reactor_nh3_feed_kmol = nh3_reacted_kmol/x
    unreacted_kmol = reactor_nh3_feed_kmol - nh3_reacted_kmol
    recycle_kmol = nh3_rec*unreacted_kmol
    purge_nh3_kmol = (1.0-nh3_rec)*unreacted_kmol
    fresh_nh3_kmol = nh3_reacted_kmol + purge_nh3_kmol
    fresh_nh3_t = fresh_nh3_kmol*mw['NH3']/1000.0
    recycle_t = recycle_kmol*mw['NH3']/1000.0
    total_nh3_t = reactor_nh3_feed_kmol*mw['NH3']/1000.0

    # Catalyst inventory from measured productivity, with a plug-flow conversion correction anchored at lab X.
    r = max(_record_value(rec, 'r', 0.05), 1e-9)
    xlab = min(max(_record_value(rec, 'X', 0.5), 1e-4), 0.9999)
    phi = (x/max(-math.log(1.0-x),1e-12))/(xlab/max(-math.log(1.0-xlab),1e-12))
    effective_r = max(r*phi, 1e-12)
    gross_h2_kg_h = capacity*1000.0/hours/psa_rec
    catalyst_kg = gross_h2_kg_h/effective_r*_p('catalyst_void_and_scale_factor')
    cat_price = _catalyst_price(rec)
    tcycle = rec.get('t_cycle_h')
    try: life = float(tcycle) if tcycle is not None and np.isfinite(float(tcycle)) else _p('default_catalyst_life_h')
    except Exception: life = _p('default_catalyst_life_h')
    life = max(life, _p('minimum_catalyst_life_h'))
    catalyst_cost = catalyst_kg*cat_price*_p('catalyst_inventory_factor')*(hours/life)/capacity

    # Heat and electricity duties per delivered tonne H2.
    vapor_GJ = total_nh3_t*_p('nh3_vaporization_GJ_per_t_NH3')
    dT = max(T-_p('basis.feeds.NH3.T_K'), 0.0)
    feed_sensible = reactor_nh3_feed_kmol*_p('feed_sensible_heat_kJ_per_kmol_K')*dT/1e6
    effluent_kmol = unreacted_kmol + 1.5*nh3_reacted_kmol*S + n2_kmol
    effluent_sensible = effluent_kmol*_p('product_sensible_heat_kJ_per_kmol_K')*dT/1e6
    recovered = _p('recuperator_effectiveness')*min(feed_sensible, effluent_sensible)
    reaction_heat_per_kmol = _p('reaction_heat_GJ_per_kmol_NH3') + _p('reaction_heat_capacity_increment_kJ_per_kmol_K')*max(T-298.15,0.0)/1e6
    reaction_heat = nh3_reacted_kmol*reaction_heat_per_kmol
    heater_electric_GJ = (reaction_heat + max(feed_sensible-recovered,0.0))/_p('electric_heater_efficiency')
    # Chiller removes unrecovered product sensible heat plus ammonia condensation; electric work from COP surrogate.
    cooling_duty = max(effluent_sensible-recovered,0.0) + unreacted_kmol*mw['NH3']/1000.0*_p('nh3_vaporization_GJ_per_t_NH3')
    chiller_MWh = cooling_duty*_p('chilling_electricity_MWh_per_GJ_removed')
    pump_MWh = recycle_t*_p('pump_electricity_MWh_per_t_recycle')
    psa_MWh = _p('psa_electricity_MWh_per_t_H2')
    offsites_MWh = _p('offsites_electricity_MWh_per_t_H2')

    # Isentropic H2 compression from PSA pressure to product pressure.
    P_in = max(P-_p('reactor_pressure_drop_bar'), 0.2)
    P_out = _p('basis.product.H2.P_bar')
    gamma = _p('compression_heat_capacity_ratio')
    eta = _p('compressor_isentropic_efficiency')
    Tin = _p('ambient_temperature_K')
    ratio = max(P_out/P_in, 1.0)
    product_gas_kmol = h2_product_kmol/psa_purity
    n2_product_kmol = product_gas_kmol-h2_product_kmol
    compressor_kJ_per_kmol = gamma/(gamma-1.0)*_p('gas_constant_kJ_per_kmol_K')*Tin*(ratio**((gamma-1.0)/gamma)-1.0)/eta
    compressor_GJ = compressor_kJ_per_kmol*product_gas_kmol/1e6
    compressor_MWh = compressor_GJ/3.6
    heater_MWh = heater_electric_GJ/3.6
    vapor_MWh = vapor_GJ/_p('electric_heater_efficiency')/3.6
    total_MWh = vapor_MWh+heater_MWh+chiller_MWh+pump_MWh+psa_MWh+compressor_MWh+offsites_MWh
    primary_factor = _p('basis.utilities.electricity_primary_energy_factor')

    flow_factor = fresh_nh3_t/(nh3_reacted_kmol*mw['NH3']/1000.0)
    activity_factor = 1.0 + _p('capital_activity_multiplier')*max(catalyst_kg/_p('reactor_reference_catalyst_kg')-1.0,0.0)
    cap_vap = _capital_scale(_p('vaporizer_base_capex_usd'), flow_factor)
    cap_mix = _capital_scale(_p('mixer_base_capex_usd'), flow_factor)
    cap_hx = _capital_scale(_p('recuperator_base_capex_usd'), reactor_nh3_feed_kmol/nh3_reacted_kmol)
    cap_heat = _capital_scale(_p('heater_base_capex_usd'), (reaction_heat+feed_sensible)/max(reaction_heat,1e-9))
    cap_reactor = _capital_scale(_p('reactor_base_capex_usd'), activity_factor)
    cap_chill = _capital_scale(_p('chiller_base_capex_usd'), max(cooling_duty/20.0,0.1))
    cap_ko = _capital_scale(_p('knockout_base_capex_usd'), reactor_nh3_feed_kmol/nh3_reacted_kmol)
    cap_pump = _capital_scale(_p('recycle_pump_base_capex_usd'), max(recycle_t/6.0,0.1))
    cap_psa = _capital_scale(_p('psa_base_capex_usd'), h2_gross_kmol/h2_product_kmol)
    cap_comp = _capital_scale(_p('compressor_base_capex_usd'), max(compressor_GJ/3.0,0.1))
    direct = cap_vap+cap_mix+cap_hx+cap_heat+cap_reactor+cap_chill+cap_ko+cap_pump+cap_psa+cap_comp
    cap_off = direct*_p('offsites_fraction_of_direct_capex')
    capex = direct+cap_off

    feed_cost = fresh_nh3_t*_p('price.ammonia')
    energy_cost = total_MWh*_p('price.electricity')
    capital_cost = capex*_p('price.capital_recovery_factor')/capacity
    other_cost = capex*_p('price.fixed_om_fraction_of_capex')/capacity
    parts = {'feed':feed_cost,'energy':energy_cost,'capital':capital_cost,'catalyst':catalyst_cost,'other':other_cost}

    h2_tail_kmol = h2_gross_kmol-h2_product_kmol
    n2_tail_kmol = max(n2_kmol-n2_product_kmol,0.0)
    psa_feed_kmol = h2_gross_kmol+n2_kmol+purge_nh3_kmol
    psa_y = {'NH3':purge_nh3_kmol/psa_feed_kmol,'H2':h2_gross_kmol/psa_feed_kmol,'N2':n2_kmol/psa_feed_kmol}
    tail_kmol = h2_tail_kmol+n2_tail_kmol+purge_nh3_kmol
    tail_y = {'NH3':purge_nh3_kmol/tail_kmol,'H2':h2_tail_kmol/tail_kmol,'N2':n2_tail_kmol/tail_kmol}
    units = [
      {'name':'ammonia_vaporizer','type':'heat_exchanger','purchased_energy_GJ_per_t':vapor_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_vap,'heat_duty_GJ_per_t':vapor_GJ,'delivered_electricity_GJ_per_t':vapor_MWh*3.6},
      {'name':'recycle_mixer','type':'other','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_mix},
      {'name':'feed_effluent_recuperator','type':'heat_exchanger','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_hx,'recovered_heat_GJ_per_t':recovered},
      {'name':'electric_trim_heater','type':'furnace','purchased_energy_GJ_per_t':heater_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_heat,'heat_supplied_GJ_per_t':reaction_heat+max(feed_sensible-recovered,0.0),'delivered_electricity_GJ_per_t':heater_MWh*3.6,'feed_sensible_GJ_per_t':feed_sensible,'recovered_heat_credit_GJ_per_t':recovered},
      {'name':'ammonia_decomposition_reactor','type':'reactor','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_reactor,'heat_duty_GJ_per_t':reaction_heat,'catalyst_kg':catalyst_kg,'catalyst_price_usd_per_kg':cat_price,'catalyst_life_h':life,'gross_h2_kg_per_h':gross_h2_kg_h,'effective_productivity_kg_H2_per_kgcat_h':effective_r,'reported_productivity_kg_H2_per_kgcat_h':r,'lab_conversion':xlab,'lab_pressure_bar':_record_value(rec,'P_bar',1.01325),'components':rec.get('components') or [],'inventory_scale_factor':_p('catalyst_void_and_scale_factor'),'equilibrium_conversion':_equilibrium_conversion(T,P)},
      {'name':'effluent_chiller','type':'heat_exchanger','purchased_energy_GJ_per_t':chiller_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_chill,'cooling_duty_GJ_per_t':cooling_duty,'delivered_electricity_GJ_per_t':chiller_MWh*3.6},
      {'name':'ammonia_knockout','type':'knockout','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_ko,'cooling_duty_GJ_per_t':0.0},
      {'name':'ammonia_recycle_pump','type':'pump','purchased_energy_GJ_per_t':pump_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_pump},
      {'name':'hydrogen_psa','type':'separation','purchased_energy_GJ_per_t':psa_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'recovered_heat_GJ_per_t':0.0,'capex_usd':cap_psa,'feed':{'kmol_per_t':psa_feed_kmol,'mol_frac':psa_y,'P_bar':P_in,'T_K':_p('basis.utilities.chilled_water_supply_temperature')},'outlets':[{'kmol_per_t':product_gas_kmol,'mol_frac':{'H2':psa_purity,'N2':1.0-psa_purity,'NH3':0.0}},{'kmol_per_t':tail_kmol,'mol_frac':tail_y}],'h2_recovery':psa_rec,'h2_product_purity':psa_purity},
      {'name':'hydrogen_product_compressor','type':'compressor','purchased_energy_GJ_per_t':compressor_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_comp,'kmol_per_t':product_gas_kmol,'T_in_K':Tin,'P_in_bar':P_in,'P_out_bar':P_out,'power_GJ_per_t':compressor_GJ,'electric_input_GJ_per_t':compressor_GJ,'primary_energy_factor':primary_factor},
      {'name':'tailgas_and_offsites','type':'offsites','purchased_energy_GJ_per_t':offsites_MWh*3.6*primary_factor,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_off}
    ]
    primary_energy = sum(u['purchased_energy_GJ_per_t'] for u in units)
    boundary_out = {'H2':1.0+h2_tail_kmol*mw['H2']/1000.0,'N2':n2_kmol*mw['N2']/1000.0,'NH3':purge_nh3_kmol*mw['NH3']/1000.0}
    return {
      'cost_usd_per_t':sum(parts.values()),'parts':parts,
      'operating':{'T_K':T,'P_bar':P,'per_pass_conversion':x},
      'balances':{'key_feed_t_per_t':reactor_nh3_feed_kmol*mw['NH3']/1000.0,'fresh_NH3_t_per_t':fresh_nh3_t,'reactor_NH3_feed_t_per_t':total_nh3_t,'recycle_NH3_t_per_t':recycle_t,'purge_NH3_t_per_t':purge_nh3_kmol*mw['NH3']/1000.0,'energy_GJ_per_t':primary_energy,'delivered_electricity_MWh_per_t':total_MWh,'capex_usd':capex,'capacity_t_per_y':capacity},
      'physics':{
        'reactor':{'T_K':T,'P_bar':P,'feed_mol_frac':{'NH3':1.0},'per_pass_conversion':x,'heat_duty_GJ_per_t':reaction_heat},
        'boundary':{'in_t_per_t':{'NH3':fresh_nh3_t},'out_t_per_t':boundary_out},
        'units':units
      },
      '_aux':{'catalyst_kg':catalyst_kg,'equilibrium_conversion':_equilibrium_conversion(T,P),'recycle_ratio':recycle_kmol/max(fresh_nh3_kmol,1e-12)}
    }

def plant_cost(rec):
    T = _record_value(rec,'T_K',673.15)
    P = _p('reactor_pressure_bar')
    xeq = _equilibrium_conversion(T,P)*_p('equilibrium_margin')
    xmin = _p('minimum_per_pass_conversion')
    # Ensure recycle ratio remains within the declared operating window.
    xmin_recycle = 1.0/(1.0+_p('maximum_recycle_ratio'))
    lo = max(xmin,xmin_recycle,1e-4)
    hi = min(xeq,_p('maximum_per_pass_conversion'))
    if hi <= lo: lo = max(1e-4,0.5*hi)
    objective = lambda xx: _evaluate(rec,float(xx))['cost_usd_per_t']
    opt = minimize_scalar(objective,bounds=(lo,hi),method='bounded',options={'xatol':1e-7,'maxiter':200})
    x = float(opt.x if opt.success else hi)
    out = _evaluate(rec,x)
    out.pop('_aux',None)
    return out

def reference():
    rec = {
      'T_K':623.0,'P_bar':1.01325,'X':0.90,'S':1.0,'r':0.50,
      'y_key':1.0,'y_cofeed':0.0,'t_cycle_h':None,
      'components':[['Ru',5.0],['Ba',None],['Al',None]],
      'catalyst':'5 wt% Ru/Ba hexaaluminate literature reference'
    }
    out = plant_cost(rec)
    out['name'] = '50,000 t/y H2 ammonia-cracking reference plant with Ru/BHA catalyst'
    out['record'] = rec
    return out
