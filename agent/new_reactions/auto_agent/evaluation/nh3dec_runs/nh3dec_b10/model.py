import csv, json, math
from pathlib import Path
import numpy as np

REACTION = {
    "key": "NH3",
    "product": "H2",
    "cofeed": None,
    "MW": {"NH3": 17.031, "H2": 2.016, "N2": 28.014},
    "nu": {"NH3": -2, "H2": 3, "N2": 1},
}

MW_ALL = {**REACTION["MW"], "CH4": 16.04246, "O2": 31.9988, "CO2": 44.0095, "H2O": 18.01528}


def _load_params():
    out = {}
    with open(Path(__file__).with_name("sources.csv"), newline="") as f:
        for row in csv.DictReader(f):
            out[row["parameter"]] = float(row["value"])
    return out


PARAMS = _load_params()


def _p(name):
    return float(PARAMS[name])


def _val(rec, key, default):
    v = rec.get(key, default)
    if v is None or v == "":
        return default
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except Exception:
        return default


def _components(rec):
    c = rec.get("components", rec.get("elements", []))
    if isinstance(c, str):
        try:
            c = json.loads(c)
        except Exception:
            c = []
    ans = []
    for item in c or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            el = str(item[0])
            wt = None if item[1] is None else float(item[1])
            ans.append([el, wt])
    return ans


def _equilibrium_K(T):
    dH = _p("thermo.reaction_enthalpy_kJ_per_mol_reaction") * 1000.0
    dS = _p("thermo.reaction_entropy_J_per_molK_reaction")
    return math.exp(max(-100.0, min(100.0, dS / 8.314462618 - dH / (8.314462618 * T))))


def _q_pure(X, P):
    X = min(max(float(X), 1e-12), 1.0 - 1e-12)
    nt = 1.0 + X
    pnh3 = P * (1.0 - X) / nt
    ph2 = P * 1.5 * X / nt
    pn2 = P * 0.5 * X / nt
    return (ph2 ** 3) * pn2 / max(pnh3 ** 2, 1e-30)


def _xeq(T, P):
    K = _equilibrium_K(T)
    lo, hi = 0.0, 1.0 - 1e-10
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if _q_pure(mid, P) < K:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _lab_terms(rec):
    T = _val(rec, "T_K", 673.15)
    P = max(_val(rec, "P_bar", 1.01325), 0.05)
    X = min(max(_val(rec, "X", 0.1), 1e-5), 0.99999)
    y0 = min(max(_val(rec, "y_key", 1.0), 1e-6), 1.0)
    yh20 = min(max(_val(rec, "y_h2", 0.0), 0.0), max(0.0, 1.0-y0))
    inert = max(0.0, 1.0-y0-yh20)
    def state(x):
        nnh3=y0*(1.0-x); nh2=yh20+1.5*y0*x; nn2=0.5*y0*x
        nt=max(nnh3+nh2+nn2+inert,1e-12)
        return max(P*nnh3/nt,1e-6),max(P*nh2/nt,1e-4),max(P*nn2/nt,1e-8)
    pnh3,ph2,_=state(0.5*X)
    onh3,oh2,on2=state(X)
    Q = oh2**3 * on2 / max(onh3**2, 1e-30)
    drive = max(0.02, 1.0-Q/_equilibrium_K(T))
    order_term = pnh3**_p("kinetics.nh3_order") * ph2**_p("kinetics.h2_order")
    return T, max(order_term*drive, 1e-20)


def _plant_rate(rec, T, P, X):
    rlab = max(_val(rec, "r", _p("kinetics.minimum_rate_kg_per_kg_h")), _p("kinetics.minimum_rate_kg_per_kg_h"))
    Tlab, labterm = _lab_terms(rec)
    Xm = max(1e-6, 0.5*X)
    nt = 1.0+Xm
    pnh3 = max(P*(1.0-Xm)/nt, 1e-6)
    ph2 = max(P*1.5*Xm/nt, 1e-4)
    plantterm = pnh3**_p("kinetics.nh3_order") * ph2**_p("kinetics.h2_order")
    drive = max(1e-5, 1.0-_q_pure(X,P)/_equilibrium_K(T))
    Ea = _p("kinetics.activation_energy_kJ_per_mol")*1000.0
    arr = math.exp(max(-80.0, min(80.0, -Ea/8.314462618*(1.0/T-1.0/Tlab))))
    S = min(max(_val(rec,"S",1.0),0.01),1.0)
    return max(_p("kinetics.minimum_rate_kg_per_kg_h"), rlab*arr*(plantterm*drive/labterm)*_p("kinetics.scaleup_factor")*S)


def _catalyst_price(rec):
    comps = _components(rec)
    support = _p("price.catalyst_support_and_manufacturing")
    named = []
    known_sum = 0.0
    cost = support
    for el, wt in comps:
        key = "price.metal_"+el
        if key not in PARAMS:
            continue
        named.append(el)
        if wt is not None:
            frac = min(max(wt/100.0,0.0),1.0)
            known_sum += frac
            cost += frac*_p(key)
    if named and all(wt is None for _,wt in comps):
        frac = _p("catalyst.default_named_metal_wt_fraction")
        cost += frac*sum(_p("price.metal_"+el) for el in named if "price.metal_"+el in PARAMS)/max(len(named),1)
    return max(support, cost)*(1.0-_p("catalyst.recovery_credit_fraction"))


def _base_capex(unit, load, capacity_scale):
    floor = _p("capex.flow_floor_fraction")
    exponent = _p("capital.capacity_exponent")
    return _p("capex."+unit+"_base_usd") * capacity_scale * max(floor, load)**exponent


def _evaluate(rec, T, X):
    MW = MW_ALL
    P = _p("operating.reactor_pressure_bar")
    cap = _p("basis.capacity_t_per_y")
    hours = _p("basis.operating_hours_per_y")
    psa_rec = _p("separation.psa_h2_recovery")
    nh3_rec = _p("separation.nh3_recovery")
    gross_h2 = 1.0/psa_rec
    stoich_nh3_per_h2 = (2.0*MW["NH3"])/(3.0*MW["H2"])
    reacted_nh3 = gross_h2*stoich_nh3_per_h2
    selectivity = min(max(_val(rec, "S", 1.0), 0.01), 1.0)
    unselective_nh3 = reacted_nh3*(1.0/selectivity-1.0)
    reactor_nh3_in = reacted_nh3/max(X,1e-9)
    unreacted_nh3 = reactor_nh3_in-reacted_nh3
    recovered_nh3 = nh3_rec*unreacted_nh3
    nh3_loss = unreacted_nh3-recovered_nh3
    fresh_nh3 = reacted_nh3+nh3_loss+unselective_nh3
    boundary_nh3_in = fresh_nh3
    reported_key_feed = fresh_nh3
    nh3_boundary_out = nh3_loss+unselective_nh3

    rate = _plant_rate(rec,T,P,X)
    gross_h2_kg_h = cap*1000.0/hours/psa_rec
    cat_kg = gross_h2_kg_h/rate*_p("catalyst.inventory_factor")
    cycle = max(24.0,_val(rec,"t_cycle_h",_p("kinetics.default_cycle_h")))
    cat_price = _catalyst_price(rec)
    catalyst_cost = cat_kg*cat_price*(hours/cycle)/cap

    dH = _p("thermo.reaction_enthalpy_kJ_per_mol_reaction")
    h2_t_per_kmol_rxn = 3.0*MW["H2"]/1000.0
    reaction_heat = gross_h2*dH/1000.0/h2_t_per_kmol_rxn
    Tfeed = _p("basis.feeds.NH3.T_K")
    sensible = reactor_nh3_in*_p("thermo.gas_cp_GJ_per_tK")*max(0.0,T-Tfeed)
    recovered_heat = _p("heat_recovery.effectiveness")*sensible
    reactor_heat = reaction_heat + sensible-recovered_heat
    vaporization = reactor_nh3_in*_p("thermo.ammonia_vaporization_GJ_per_t")
    condenser_cooling = unreacted_nh3*_p("thermo.ammonia_vaporization_GJ_per_t")
    refrigeration_power = condenser_cooling/_p("refrigeration.COP")
    pump_power = 0.005*recovered_nh3/_p("pump.efficiency")
    psa_power = gross_h2*_p("separation.psa_electricity_GJ_per_t_H2_feed")

    Pin = P
    Pout = _p("basis.product.H2.P_bar")
    Tin = _p("compressor.inlet_temperature_K")
    gamma = _p("compressor.heat_capacity_ratio")
    eta = _p("compressor.isentropic_efficiency")
    kmol_product = 1000.0/MW["H2"]
    if Pout > Pin:
        comp_power = kmol_product*8.314462618*Tin*(gamma/(gamma-1.0))*((Pout/Pin)**((gamma-1.0)/gamma)-1.0)/eta/1e6
    else:
        comp_power = 0.0
    offsites_power = _p("offsites.electricity_GJ_per_t")

    tail_h2 = gross_h2-1.0
    needed_fuel = reactor_heat/_p("furnace.thermal_efficiency")
    available_internal = tail_h2*_p("thermo.h2_LHV_GJ_per_t")
    internal_fuel = min(available_internal,needed_fuel)
    h2_burned = internal_fuel/_p("thermo.h2_LHV_GJ_per_t")
    natural_gas_energy = max(0.0,needed_fuel-internal_fuel)
    ch4_in = natural_gas_energy/_p("thermo.ch4_LHV_GJ_per_t")
    h2_purge = max(0.0,tail_h2-h2_burned)
    tail_burn_fraction = h2_burned/max(tail_h2,1e-30) if tail_h2>0 else 0.0

    electric_energy = vaporization+refrigeration_power+pump_power+psa_power+comp_power+offsites_power
    purchased_energy = electric_energy+natural_gas_energy
    energy_cost = electric_energy/3.6*_p("price.electricity") + natural_gas_energy*_p("price.natural_gas")
    feed_cost = fresh_nh3*_p("price.ammonia")

    refcap = _p("capital.reference_capacity_t_per_y")
    capscale = (cap/refcap)**_p("capital.capacity_exponent")
    ref_gross_h2 = 1.0/psa_rec
    ref_reacted = ref_gross_h2*stoich_nh3_per_h2
    reference_flow = ref_reacted/0.90
    flow_load = reactor_nh3_in/reference_flow
    gas_kmol = gross_h2*1000.0/MW["H2"] + gross_h2*1000.0/MW["H2"]/3.0
    ref_gas_kmol = ref_gross_h2*1000.0/MW["H2"]*4.0/3.0
    gas_load = gas_kmol/ref_gas_kmol
    recycle_load = max(0.05,recovered_nh3/max(reference_flow-ref_reacted,1e-9))
    duty_load = max(0.05,reactor_heat/22.0)
    cool_load = max(0.05,condenser_cooling/2.0)
    power_load = max(0.05,comp_power/3.0)

    caps = {
      "fresh_ammonia_conditioner": _base_capex("fresh_ammonia_conditioner",flow_load,capscale),
      "feed_recycle_mixer": _base_capex("feed_recycle_mixer",flow_load,capscale),
      "feed_effluent_exchanger": _base_capex("feed_effluent_exchanger",max(0.05,recovered_heat/5.0),capscale),
      "fired_heater": _base_capex("fired_heater",duty_load,capscale),
      "tubular_fixed_bed_reactor": _base_capex("tubular_fixed_bed_reactor",max(flow_load,cat_kg/_p("capital.reference_catalyst_inventory_kg")),capscale),
      "refrigeration_condenser": _base_capex("refrigeration_condenser",cool_load,capscale),
      "ammonia_knockout": _base_capex("ammonia_knockout",flow_load,capscale),
      "recycle_pump_vaporizer": _base_capex("recycle_pump_vaporizer",recycle_load,capscale),
      "hydrogen_psa": _base_capex("hydrogen_psa",gas_load,capscale),
      "tail_gas_splitter": _base_capex("tail_gas_splitter",gas_load,capscale),
      "hydrogen_product_compressor": _base_capex("hydrogen_product_compressor",power_load,capscale),
      "utility_offsites": _base_capex("utility_offsites",max(duty_load,power_load),capscale),
    }
    total_capex = sum(caps.values())
    capital_cost = total_capex*_p("price.capital_recovery_factor")/cap
    other_cost = total_capex*_p("price.fixed_om_fraction_of_capex")/cap

    n2_reaction = gross_h2*(MW["N2"]/(3.0*MW["H2"]))
    n2_to_furnace = n2_reaction*tail_burn_fraction
    n2_purge = n2_reaction-n2_to_furnace
    h2_burn_kmol = h2_burned*1000.0/MW["H2"]
    ch4_kmol = ch4_in*1000.0/MW["CH4"]
    o2_stoich_kmol = 0.5*h2_burn_kmol+2.0*ch4_kmol
    o2_in_kmol = o2_stoich_kmol*(1.0+_p("furnace.excess_air_fraction"))
    air_n2_kmol = 0.0
    o2_out_t = (o2_in_kmol-o2_stoich_kmol)*MW["O2"]/1000.0
    air_n2_t = air_n2_kmol*MW["N2"]/1000.0
    co2_out = ch4_kmol*MW["CO2"]/1000.0
    water_comb = (h2_burn_kmol+2.0*ch4_kmol)*MW["H2O"]/1000.0
    cooling_water = 1.0

    raw_h2_kmol = gross_h2*1000.0/MW["H2"]
    raw_n2_kmol = n2_reaction*1000.0/MW["N2"]
    raw_nh3_kmol = nh3_loss*1000.0/MW["NH3"]
    raw_total = raw_h2_kmol+raw_n2_kmol+raw_nh3_kmol
    tail_h2_kmol = tail_h2*1000.0/MW["H2"]
    tail_total = tail_h2_kmol+raw_n2_kmol+raw_nh3_kmol

    units = [
      {"name":"fresh_ammonia_conditioner","type":"other","purchased_energy_GJ_per_t":vaporization,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["fresh_ammonia_conditioner"]},
      {"name":"feed_recycle_mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["feed_recycle_mixer"]},
      {"name":"feed_effluent_exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered_heat,"capex_usd":caps["feed_effluent_exchanger"]},
      {"name":"fired_heater","type":"furnace","purchased_energy_GJ_per_t":natural_gas_energy,"internal_fuel_GJ_per_t":internal_fuel,"recovered_heat_GJ_per_t":0.0,"capex_usd":caps["fired_heater"]},
      {"name":"tubular_fixed_bed_reactor","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["tubular_fixed_bed_reactor"],"catalyst_inventory_kg":cat_kg},
      {"name":"refrigeration_condenser","type":"heat_exchanger","purchased_energy_GJ_per_t":refrigeration_power,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"capex_usd":caps["refrigeration_condenser"]},
      {"name":"ammonia_knockout","type":"knockout","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"cooling_duty_GJ_per_t":condenser_cooling,"capex_usd":caps["ammonia_knockout"]},
      {"name":"recycle_pump_vaporizer","type":"pump","purchased_energy_GJ_per_t":pump_power,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["recycle_pump_vaporizer"]},
      {"name":"hydrogen_psa","type":"separation","purchased_energy_GJ_per_t":psa_power,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"capex_usd":caps["hydrogen_psa"],"feed":{"kmol_per_t":raw_total,"mol_frac":{"H2":raw_h2_kmol/raw_total,"N2":raw_n2_kmol/raw_total,"NH3":raw_nh3_kmol/raw_total}},"outlets":[{"kmol_per_t":kmol_product,"mol_frac":{"H2":1.0}},{"kmol_per_t":tail_total,"mol_frac":{"H2":tail_h2_kmol/tail_total,"N2":raw_n2_kmol/tail_total,"NH3":raw_nh3_kmol/tail_total}}]},
      {"name":"tail_gas_splitter","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["tail_gas_splitter"]},
      {"name":"hydrogen_product_compressor","type":"compressor","purchased_energy_GJ_per_t":comp_power,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["hydrogen_product_compressor"],"kmol_per_t":kmol_product,"T_in_K":Tin,"P_in_bar":Pin,"P_out_bar":Pout,"power_GJ_per_t":comp_power},
      {"name":"utility_offsites","type":"offsites","purchased_energy_GJ_per_t":offsites_power,"internal_fuel_GJ_per_t":0.0,"capex_usd":caps["utility_offsites"]},
    ]
    parts={"feed":feed_cost,"energy":energy_cost,"capital":capital_cost,"catalyst":catalyst_cost,"other":other_cost}
    total=sum(parts.values())
    return {
      "cost_usd_per_t":total,
      "parts":parts,
      "operating":{"T_K":T,"P_bar":P,"per_pass_conversion":X},
      "balances":{"key_feed_t_per_t":reported_key_feed,"energy_GJ_per_t":purchased_energy,"capex_usd":total_capex,"capacity_t_per_y":cap},
      "physics":{
        "reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":{"NH3":1.0},"per_pass_conversion":X,"heat_duty_GJ_per_t":reactor_heat},
        "boundary":{"in_t_per_t":{"NH3":boundary_nh3_in},"out_t_per_t":{"H2":gross_h2,"N2":n2_purge+n2_to_furnace,"NH3":nh3_boundary_out}},
        "units":units
      }
    }


def plant_cost(rec):
    Tmin=_p("operating.temperature_min_K")
    Tmax=_p("operating.temperature_max_K")
    nT=max(2,int(round(_p("operating.temperature_grid_points"))))
    nX=max(2,int(round(_p("operating.conversion_grid_points"))))
    P=_p("operating.reactor_pressure_bar")
    best=None
    for T in np.linspace(Tmin,Tmax,nT):
        xmax=min(0.999,_p("operating.conversion_max_fraction_equilibrium")*_xeq(T,P))
        xmin=min(_p("operating.conversion_min"),0.95*xmax)
        if xmax<=0.05:
            continue
        for X in np.linspace(max(0.05,xmin),xmax,nX):
            ans=_evaluate(rec,float(T),float(X))
            if np.isfinite(ans["cost_usd_per_t"]) and (best is None or ans["cost_usd_per_t"]<best["cost_usd_per_t"]):
                best=ans
    if best is None:
        best=_evaluate(rec,Tmax,max(0.05,0.8*_xeq(Tmax,P)))
    return best


def reference():
    rec={
        "T_K":623.0,"P_bar":1.01325,"X":0.80,"S":1.0,"r":0.2558753894211271,
        "y_key":0.05,"y_cofeed":0.0,"t_cycle_h":100.0,
        "components":[["Ru",2.5]],
        "catalyst":"2.5Ru/SiC; published laboratory reference from 10.1016/j.jiec.2020.11.003"
    }
    for _ in range(4):
        out=plant_cost(rec)
        rec["X"]=out["operating"]["per_pass_conversion"]
    out=plant_cost(rec)
    out["name"]="30,000 t/y H2 ammonia-cracking reference using published 2.5Ru/SiC laboratory record"
    out["record"]=rec
    return out
