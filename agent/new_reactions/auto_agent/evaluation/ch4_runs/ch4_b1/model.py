import math, json, ast
import numpy as np

REACTION = {
    "key": "CO2",
    "product": "CH4",
    "cofeed": "H2",
    "MW": {"CO2": 44.0095, "H2": 2.01588, "CH4": 16.043, "H2O": 18.01528, "CO": 28.0101},
    "nu": {"CO2": -1.0, "H2": -4.0, "CH4": 1.0, "H2O": 2.0},
}

PARAM = {
    "capacity_t_y": 100000.0,
    "capacity_factor": 0.90,
    "discount_rate": 0.08,
    "life_y": 20.0,
    "h2_price": 2.5,
    "co2_price_t": 70.0,
    "elec_usd_kwh": 0.085,
    "P_reactor": 20.0,
    "P_co2_in": 1.0,
    "P_h2_in": 1.0,
    "P_ch4_out": 70.0,
    "eta_comp": 0.72,
    "comp_cost_per_MW": 1.5e6,
    "reactor_fixed_cost": 5.0e6,
    "reactor_catalyst_cost_factor": 80.0,
    "hx_base_cost": 2.0e6,
    "ko_cost": 1.5e6,
    "sep_base_cost": 10.0e6,
    "sep_energy_GJ_per_kmol": 0.012,
    "methane_recovery": 0.995,
    "reactant_recovery": 0.98,
    "dP_recycle": 2.0,
    "heat_recovery_fraction": 0.75,
    "cooling_aux_GJ_t": 0.01,
    "offsites_fraction": 0.25,
    "support_price": 20.0,
    "base_cat_life_y": 3.0,
    "short_min_life_y": 0.25,
}

UNIT_NAMES = [
    "CO2 feed compressor", "H2 feed compressor", "Feed mixer", "Feed effluent heat exchanger",
    "Trim feed heater", "Methanation reactor", "Reactor heat recovery", "Product cooler condenser",
    "Gas separation", "Recycle compressor", "Product compressor", "Utilities and offsites"
]

# Shomate coefficients (NIST form) for common gases, used only for target-reaction equilibrium.
# Ranges cover the methanation temperatures in the extracted records.
SHOMATE = {
    "CO2": (298.0, 1200.0, [24.99735,55.18696,-33.69137,7.948387,-0.136638,-403.6075,228.2431,-393.5224]),
    "H2": (298.0, 1000.0, [33.066178,-11.363417,11.432816,-2.772874,-0.158558,-9.980797,172.707974,0.0]),
    "CH4": (298.0, 1300.0, [-0.703029,108.4773,-42.52157,5.862788,0.678565,-76.84376,158.7163,-74.87310]),
    "H2O": (500.0, 1700.0, [30.09200,6.832514,6.793435,-2.534480,0.082139,-250.8810,223.3967,-241.8264]),
}
R = 8.314462618  # J/mol/K

def _shomate_h_s(sp, T):
    lo, hi, c = SHOMATE[sp]
    T = min(max(float(T), lo), hi)
    t = T / 1000.0
    A,B,C,D,E,F,G,H = c
    HkJ = A*t + B*t*t/2 + C*t**3/3 + D*t**4/4 - E/t + F
    S = A*math.log(t) + B*t + C*t*t/2 + D*t**3/3 - E/(2*t*t) + G
    return HkJ, S

def _lnK_methanation(T):
    # CO2 + 4H2 = CH4 + 2H2O(g)
    nu = {"CO2":-1.0, "H2":-4.0, "CH4":1.0, "H2O":2.0}
    dH = 0.0; dS = 0.0
    for sp, v in nu.items():
        h, s = _shomate_h_s(sp, T)
        dH += v*h*1000.0
        dS += v*s
    dG = dH - T*dS
    return -dG/(R*T)

def _dh_methanation_kJmol(T):
    nu = {"CO2":-1.0, "H2":-4.0, "CH4":1.0, "H2O":2.0}
    dH = 0.0
    for sp, v in nu.items():
        h, _s = _shomate_h_s(sp, T)
        dH += v*h
    return dH

def _equilibrium_x(T, Pbar, y_ch4_in=0.0):
    # basis: 1 mol CO2 + 4 mol H2 plus optional inert/product CH4 recycle. Conservative cap.
    K = math.exp(max(min(_lnK_methanation(T), 80.0), -80.0))
    n_ch4_in = max(0.0, y_ch4_in) * 5.0 / max(1e-9, 1.0-y_ch4_in)
    def q_of_x(x):
        n_co2 = max(1e-15, 1-x)
        n_h2 = max(1e-15, 4-4*x)
        n_ch4 = max(1e-15, n_ch4_in + x)
        n_h2o = max(1e-15, 2*x)
        nt = n_co2+n_h2+n_ch4+n_h2o
        pco2 = Pbar*n_co2/nt; ph2 = Pbar*n_h2/nt; pch4 = Pbar*n_ch4/nt; ph2o = Pbar*n_h2o/nt
        return (pch4*ph2o*ph2o)/(pco2*ph2**4)
    lo, hi = 1e-8, 0.999999
    if q_of_x(hi) < K:
        return 0.999
    for _ in range(90):
        mid=(lo+hi)/2
        if q_of_x(mid) < K: lo=mid
        else: hi=mid
    return max(0.02, min(0.999, (lo+hi)/2))

def _crf():
    i=PARAM["discount_rate"]; n=PARAM["life_y"]
    return i*(1+i)**n/((1+i)**n-1)

def _comp_power(n_kmol, T, Pin, Pout):
    if Pout <= Pin or n_kmol <= 0:
        return 0.0
    # isothermal ideal minimum divided by efficiency, GJ per tonne product
    kJ = n_kmol*8.314*T*math.log(Pout/Pin)/PARAM["eta_comp"]
    return kJ/1e6

def _annualized_capex_part(capex):
    return capex*_crf()/PARAM["capacity_t_y"]

def _mw_from_GJ_per_t(gj_t):
    annual_GJ = gj_t*PARAM["capacity_t_y"]
    return annual_GJ/(PARAM["capacity_factor"]*8760.0*0.0036)

def _cap_compressor(gj_t):
    mw = _mw_from_GJ_per_t(gj_t)
    if mw <= 1e-9: return 0.0
    return PARAM["comp_cost_per_MW"]*(mw**0.72)

def _cap_hx(abs_duty_gj_t, base=1.0):
    mw = max(0.001, _mw_from_GJ_per_t(abs_duty_gj_t))
    return PARAM["hx_base_cost"]*base*((mw/10.0)**0.65)

def _cat_price(components):
    price = PARAM["support_price"]
    metal_prices = {"Ni":20.0,"Co":35.0,"Ru":400000.0,"Rh":30000.0,"Pd":30000.0,"Pt":30000.0,"Au":30000.0,"Fe":5.0,"Cu":10.0,"Mn":5.0,"Ce":8.0,"La":8.0,"Ti":6.0,"Zr":8.0,"Mg":4.0,"Al":3.0,"Si":2.0,"Zn":5.0,"Ca":4.0,"Sr":5.0,"Y":30.0,"V":30.0}
    seen_w = 0.0
    for el, wt in components:
        try:
            w = float(wt)/100.0
        except Exception:
            continue
        if w <= 0 or w > 1: continue
        seen_w += w
        price += w*metal_prices.get(str(el), 10.0)*1.5
    return max(5.0, price)

def _parse_components(rec):
    comps = rec.get("components", [])
    if isinstance(comps, str):
        try: comps = ast.literal_eval(comps)
        except Exception: comps = []
    out=[]
    for c in comps or []:
        if isinstance(c,(list,tuple)) and len(c)>=2:
            out.append((str(c[0]), c[1]))
    return out

def _evaluate(rec, xpass):
    T = float(rec.get("T_K") or 573.15)
    P = max(PARAM["P_reactor"], min(30.0, float(rec.get("P_bar") or PARAM["P_reactor"])))
    Xlab = min(0.999, max(0.01, float(rec.get("X") or 0.1)))
    S = min(0.999, max(0.02, float(rec.get("S") or 0.95)))
    r = max(1e-4, float(rec.get("r") or 0.01))
    n_pipe = 1000.0 / REACTION["MW"]["CH4"]   # kmol pipeline methane per tonne
    rec_ch4 = PARAM["methane_recovery"]
    rr = PARAM["reactant_recovery"]
    n_ch4_reactor = n_pipe/rec_ch4
    converted_co2 = n_ch4_reactor/S
    Fco2_reactor = converted_co2/xpass
    Fh2_reactor = 4.0*Fco2_reactor
    ch4_byprod_loss = n_ch4_reactor - n_pipe
    n_co = converted_co2*(1.0-S)
    co2_un = Fco2_reactor - converted_co2
    h2_cons = converted_co2*(1.0 + 3.0*S)
    h2_un = max(0.0, Fh2_reactor - h2_cons)
    h2o = 2*n_ch4_reactor + n_co
    # separation purge losses of unreacted species; byproduct CO is purged.
    co2_fresh = converted_co2 + (1-rr)*co2_un
    h2_fresh = h2_cons + (1-rr)*h2_un
    recycle_kmol = rr*(co2_un+h2_un) + 0.20*ch4_byprod_loss
    dry_feed_sep = co2_un + h2_un + n_ch4_reactor + n_co
    # recycle CH4 slip roughly maps to inlet product fraction for equilibrium conservatism.
    y_ch4_in = min(0.25, max(0.0, 0.20*ch4_byprod_loss/max(1e-9, Fco2_reactor+Fh2_reactor+recycle_kmol)))
    # Compressor and separation duties.
    co2_comp = _comp_power(co2_fresh, 298.15, PARAM["P_co2_in"], P)
    h2_comp = _comp_power(h2_fresh, 298.15, PARAM["P_h2_in"], P)
    rec_comp = _comp_power(recycle_kmol, 320.0, max(1.0, P-PARAM["dP_recycle"]), P)
    prod_comp = _comp_power(n_pipe, 300.0, max(1.0, P-1.0), PARAM["P_ch4_out"])
    sep_energy = PARAM["sep_energy_GJ_per_kmol"]*dry_feed_sep
    cooling = PARAM["cooling_aux_GJ_t"]
    # heat duties: negative for heat removed from reactor; plus preheat requirement.
    q_rxn = _dh_methanation_kJmol(T)*n_ch4_reactor/1000.0
    preheat = max(0.0, (Fco2_reactor+Fh2_reactor+recycle_kmol)*0.000035*(T-298.15))
    trim_heat = preheat*(1.0-PARAM["heat_recovery_fraction"])
    # catalyst inventory based on observed productivity, corrected for target conversion and deactivation.
    cycle = rec.get("t_cycle_h")
    try: cycle = float(cycle) if cycle not in (None, "", "None", np.nan) else None
    except Exception: cycle = None
    if cycle and cycle > 0:
        cat_life_y = max(PARAM["short_min_life_y"], min(PARAM["base_cat_life_y"], 3.0*cycle/8760.0))
        activity_cycle = 0.85
    else:
        cat_life_y = PARAM["base_cat_life_y"]
        activity_cycle = 0.95
    conv_factor = max(0.35, (xpass/Xlab)**0.7)
    cat_kg = (1000.0/r)*conv_factor/activity_cycle  # kg catalyst inventory per tonne CH4/h
    plant_t_h = PARAM["capacity_t_y"]/(PARAM["capacity_factor"]*8760.0)
    cat_inventory = cat_kg*plant_t_h
    cprice = _cat_price(_parse_components(rec))
    # capex by flowsheet units
    cap_co2 = _cap_compressor(co2_comp); cap_h2 = _cap_compressor(h2_comp); cap_rec = _cap_compressor(rec_comp); cap_prod = _cap_compressor(prod_comp)
    cap_feed_hx = _cap_hx(preheat*PARAM["heat_recovery_fraction"], 0.8)
    cap_trim = 0.3e6*max(0.1, _mw_from_GJ_per_t(trim_heat)**0.6) if trim_heat>0 else 0.0
    cap_reactor = PARAM["reactor_fixed_cost"]*(PARAM["capacity_t_y"]/100000.0)**0.6 + PARAM["reactor_catalyst_cost_factor"]*cat_inventory
    cap_heat = _cap_hx(abs(q_rxn), 1.0)
    cap_ko = PARAM["ko_cost"]*(PARAM["capacity_t_y"]/100000.0)**0.55
    sep_scale = max(0.05, (dry_feed_sep*plant_t_h/1000.0))
    cap_sep = PARAM["sep_base_cost"]*(sep_scale**0.6)
    direct = cap_co2+cap_h2+cap_rec+cap_prod+cap_feed_hx+cap_trim+cap_reactor+cap_heat+cap_ko+cap_sep
    cap_off = PARAM["offsites_fraction"]*direct
    capex = direct + cap_off
    elec = co2_comp+h2_comp+rec_comp+prod_comp+sep_energy+cooling
    purchased_GJ = elec + trim_heat
    energy_cost = elec*(PARAM["elec_usd_kwh"]/0.0036) + trim_heat*8.0
    feed_cost = (h2_fresh*REACTION["MW"]["H2"])*PARAM["h2_price"] + (co2_fresh*REACTION["MW"]["CO2"]/1000.0)*PARAM["co2_price_t"]
    catalyst_cost = cat_inventory*cprice/cat_life_y/PARAM["capacity_t_y"]
    capital_cost = _annualized_capex_part(capex)
    other = 0.03*(feed_cost+energy_cost+capital_cost)  # maintenance, chemicals not otherwise itemised
    parts = {"feed": feed_cost, "energy": energy_cost, "capital": capital_cost, "catalyst": catalyst_cost, "other": other}
    units = [
        {"name":"CO2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":co2_comp,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_co2,"kmol_per_t":co2_fresh,"T_in_K":298.15,"P_in_bar":PARAM["P_co2_in"],"P_out_bar":P,"power_GJ_per_t":co2_comp},
        {"name":"H2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":h2_comp,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_h2,"kmol_per_t":h2_fresh,"T_in_K":298.15,"P_in_bar":PARAM["P_h2_in"],"P_out_bar":P,"power_GJ_per_t":h2_comp},
        {"name":"Feed mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":0.0},
        {"name":"Feed effluent heat exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_feed_hx,"recovered_heat_GJ_per_t":preheat*PARAM["heat_recovery_fraction"]},
        {"name":"Trim feed heater","type":"furnace","purchased_energy_GJ_per_t":trim_heat,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_trim},
        {"name":"Methanation reactor","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_reactor,"catalyst_inventory_kg":cat_inventory,"catalyst_price_usd_per_kg":cprice},
        {"name":"Reactor heat recovery","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_heat,"recovered_heat_GJ_per_t":max(0.0,-q_rxn)},
        {"name":"Product cooler condenser","type":"knockout","purchased_energy_GJ_per_t":cooling,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_ko,"cooling_duty_GJ_per_t":max(0.0, preheat + max(0.0,-q_rxn)*0.05)},
        {"name":"Gas separation","type":"separation","purchased_energy_GJ_per_t":sep_energy,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_sep,
         "feed":{"kmol_per_t":dry_feed_sep,"mol_frac":{"CO2":co2_un/dry_feed_sep if dry_feed_sep else 0,"H2":h2_un/dry_feed_sep if dry_feed_sep else 0,"CH4":n_ch4_reactor/dry_feed_sep if dry_feed_sep else 0,"CO":n_co/dry_feed_sep if dry_feed_sep else 0}},
         "outlets":[{"name":"raw methane product","kmol_per_t":n_pipe,"mol_frac":{"CH4":1.0}}, {"name":"recycle gas","kmol_per_t":recycle_kmol,"mol_frac":{"CO2":(rr*co2_un)/recycle_kmol if recycle_kmol else 0,"H2":(rr*h2_un)/recycle_kmol if recycle_kmol else 0,"CH4":(0.20*ch4_byprod_loss)/recycle_kmol if recycle_kmol else 0,"CO":0.0}}, {"name":"purge gas","kmol_per_t":(1-rr)*(co2_un+h2_un)+n_co+0.80*ch4_byprod_loss,"mol_frac":{"CO2":((1-rr)*co2_un)/max(1e-12,((1-rr)*(co2_un+h2_un)+n_co+0.80*ch4_byprod_loss)),"H2":((1-rr)*h2_un)/max(1e-12,((1-rr)*(co2_un+h2_un)+n_co+0.80*ch4_byprod_loss)),"CH4":(0.80*ch4_byprod_loss)/max(1e-12,((1-rr)*(co2_un+h2_un)+n_co+0.80*ch4_byprod_loss)),"CO":n_co/max(1e-12,((1-rr)*(co2_un+h2_un)+n_co+0.80*ch4_byprod_loss))}}]},
        {"name":"Recycle compressor","type":"compressor","purchased_energy_GJ_per_t":rec_comp,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_rec,"kmol_per_t":recycle_kmol,"T_in_K":320.0,"P_in_bar":max(1.0,P-PARAM["dP_recycle"]),"P_out_bar":P,"power_GJ_per_t":rec_comp},
        {"name":"Product compressor","type":"compressor","purchased_energy_GJ_per_t":prod_comp,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_prod,"kmol_per_t":n_pipe,"T_in_K":300.0,"P_in_bar":max(1.0,P-1.0),"P_out_bar":PARAM["P_ch4_out"],"power_GJ_per_t":prod_comp},
        {"name":"Utilities and offsites","type":"offsites","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":cap_off},
    ]
    boundary_in = {"CO2": co2_fresh*REACTION["MW"]["CO2"]/1000.0, "H2": h2_fresh*REACTION["MW"]["H2"]/1000.0, "H2O": 0.0}
    vent_co2 = (1-rr)*co2_un; vent_h2=(1-rr)*h2_un; vent_ch4=ch4_byprod_loss; vent_co=n_co
    boundary_out = {"CH4":1.0, "H2O":h2o*REACTION["MW"]["H2O"]/1000.0, "CO2":vent_co2*REACTION["MW"]["CO2"]/1000.0, "H2":vent_h2*REACTION["MW"]["H2"]/1000.0, "CO":vent_co*REACTION["MW"]["CO"]/1000.0}
    return {"cost_usd_per_t":sum(parts.values()), "parts":parts,
            "operating":{"T_K":T,"P_bar":P,"per_pass_conversion":xpass},
            "balances":{"key_feed_t_per_t":boundary_in["CO2"],"energy_GJ_per_t":purchased_GJ,"capex_usd":capex,"capacity_t_per_y":PARAM["capacity_t_y"]},
            "physics":{"reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":{"CO2":0.2,"H2":0.8,"CH4":0.0},"per_pass_conversion":xpass,"heat_duty_GJ_per_t":q_rxn},
                       "boundary":{"in_t_per_t":boundary_in,"out_t_per_t":boundary_out},"units":units}}

def plant_cost(rec):
    T = float(rec.get("T_K") or 573.15)
    P = max(PARAM["P_reactor"], min(30.0, float(rec.get("P_bar") or PARAM["P_reactor"])))
    xeq = _equilibrium_x(T, P)
    xmax = min(0.95, 0.985*xeq)
    xmin = min(0.30, max(0.05, 0.35*xmax))
    if xmax < 0.06:
        xmax = max(0.03, xmax); xmin = max(0.01, 0.5*xmax)
    grid = np.linspace(xmin, xmax, 32)
    best = None
    for x in grid:
        try:
            val = _evaluate(rec, float(x))
        except Exception:
            continue
        if best is None or val["cost_usd_per_t"] < best["cost_usd_per_t"]:
            best = val
    if best is None:
        best = _evaluate(rec, max(0.05, min(0.5, xmax)))
    return best

def reference():
    rec = {"T_K": 573.15, "P_bar": 20.0, "X": 0.80, "S": 0.995, "r": 1.0,
           "y_key":0.20, "y_cofeed":0.80, "t_cycle_h": None,
           "components":[["Ni",20.0],["Al",40.0]], "catalyst":"reference 20 wt% Ni/Al2O3"}
    out = plant_cost(rec)
    out["name"] = "100 kt/y CO2 methanation to pipeline methane reference plant"
    out["record"] = rec
    return out
