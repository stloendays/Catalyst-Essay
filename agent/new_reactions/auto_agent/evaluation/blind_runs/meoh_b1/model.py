from pathlib import Path
import csv
import math
import numpy as np
from scipy.optimize import brentq, minimize_scalar

_BASE = Path(__file__).resolve().parent
with (_BASE / "sources.csv").open(newline="", encoding="utf-8") as _f:
    PARAMS = {row["parameter"]: float(row["value"]) for row in csv.DictReader(_f)}

REACTION = {
    "key": "CO2",
    "product": "CH3OH",
    "cofeed": "H2",
    "MW": {"CO2": 44.0095, "H2": 2.01588, "CH3OH": 32.04186, "H2O": 18.01528, "CO": 28.0101},
    "nu": {"CO2": -1.0, "H2": -3.0, "CH3OH": 1.0, "H2O": 1.0}
}


def _p(name):
    return float(PARAMS[name])


def _equilibrium_conversion(T, P_bar, ratio):
    """Ideal-gas equilibrium for CO2+3H2=CH3OH+H2O from constant dH,dS."""
    dh = _p("thermo.equilibrium_reaction_heat_kJ_per_mol") * 1000.0
    ds = _p("thermo.equilibrium_reaction_entropy_J_per_mol_K")
    lnK = -(dh - T * ds) / (8.314462618 * T)
    K = float(np.exp(np.clip(lnK, -60.0, 60.0)))
    R = max(float(ratio), 3.0001)
    xmax = min(0.999999, R / 3.0 * 0.999999)

    def logq(x):
        nt = 1.0 + R - 2.0 * x
        yco2 = (1.0 - x) / nt
        yh2 = (R - 3.0 * x) / nt
        ym = x / nt
        yw = x / nt
        return math.log(max(ym * yw, 1e-300)) - math.log(max(yco2 * yh2**3, 1e-300)) - 2.0 * math.log(max(P_bar, 1e-9))

    target = math.log(max(K, 1e-300))
    lo, hi = 1e-10, xmax
    if logq(hi) < target:
        return hi
    return float(brentq(lambda z: logq(z) - target, lo, hi, xtol=1e-12, rtol=1e-10))


def _compressor_power(kmol, T, Pin, Pout, gamma):
    if kmol <= 0.0 or Pout <= Pin * (1.0 + 1e-12):
        return 0.0
    eta = _p("compressor.isentropic_efficiency")
    exponent = (gamma - 1.0) / gamma
    # kmol * kJ/(kmol K) * K = kJ; /1e6 = GJ
    return kmol * 8.314462618 * T * gamma / (gamma - 1.0) * ((Pout / Pin) ** exponent - 1.0) / eta / 1e6


def _component_cost(rec):
    base = _p("price.catalyst_support_and_manufacturing")
    components = rec.get("components") or []
    known = []
    specified_total = 0.0
    for item in components:
        if not isinstance(item, (list, tuple)) or len(item) < 1:
            continue
        el = str(item[0]).strip()
        wt = item[1] if len(item) > 1 else None
        key = "price.metal_" + el
        if key not in PARAMS:
            continue
        if wt is None:
            known.append((el, None))
        else:
            w = float(wt)
            if w > 1.0:
                w /= 100.0
            w = min(max(w, 0.0), 1.0)
            known.append((el, w))
            specified_total += w
    unspecified = [x for x in known if x[1] is None]
    default_total = min(_p("catalyst.unspecified_active_fraction"), max(0.0, 1.0 - specified_total))
    default_each = default_total / max(len(unspecified), 1)
    extra = 0.0
    for el, wt in known:
        w = default_each if wt is None else wt
        extra += w * _p("price.metal_" + el)
    return base + extra


def _stream(kmol_by_species):
    total = float(sum(max(0.0, v) for v in kmol_by_species.values()))
    if total <= 0.0:
        return {"kmol_per_t": 0.0, "mol_frac": {k: 0.0 for k in kmol_by_species}}
    return {"kmol_per_t": total, "mol_frac": {k: max(0.0, v) / total for k, v in kmol_by_species.items()}}


def _evaluate(rec, X, purge, build_units=True):
    T = float(rec["T_K"])
    P = float(rec["P_bar"])
    S = min(max(float(rec["S"]), 1e-4), 0.999999)
    yco2 = max(float(rec.get("y_key", 0.25)), 1e-6)
    yh2 = max(float(rec.get("y_cofeed", 0.75)), 1e-6)
    ratio = max(yh2 / yco2, 3.0001)
    xeq = _equilibrium_conversion(T, P, ratio)
    recovery = _p("separation.methanol_recovery")
    n_product = 1000.0 / REACTION["MW"]["CH3OH"]
    n_meoh = n_product / recovery
    n_converted = n_meoh / S
    n_co = max(0.0, n_converted - n_meoh)
    reactor_co2 = n_converted / max(X, 1e-8)
    dfrac = _p("separation.dissolved_CO2_fraction_of_reactor_feed")
    dissolved_co2 = min(dfrac * reactor_co2 * max(P / 50.0, 0.2), 0.20 * max(reactor_co2 - n_converted, 0.0))
    gas_co2 = max(0.0, reactor_co2 - n_converted - dissolved_co2)
    h2_consumed = 3.0 * n_meoh + n_co
    reactor_h2 = ratio * reactor_co2
    if reactor_h2 <= h2_consumed:
        return None
    gas_h2 = reactor_h2 - h2_consumed
    fresh_co2 = n_converted + dissolved_co2 + purge * gas_co2
    fresh_h2 = h2_consumed + purge * gas_h2
    reactor_co_in = (1.0 - purge) / purge * n_co
    separator_co = reactor_co_in + n_co
    recycle_co2 = (1.0 - purge) * gas_co2
    recycle_h2 = (1.0 - purge) * gas_h2
    recycle_co = (1.0 - purge) * separator_co
    recycle_kmol = recycle_co2 + recycle_h2 + recycle_co
    reactor_feed_kmol = reactor_co2 + reactor_h2 + reactor_co_in

    # Rate transfer using measured productivity and thermodynamic driving force.
    Xlab = min(max(float(rec["X"]), 0.0), 0.999)
    rlab = max(float(rec["r"]), 1e-9)
    lab_drive = max(0.05, 1.0 - Xlab / max(xeq, 1e-6))
    r0 = rlab / lab_drive
    plant_drive = max(0.01, 1.0 - X / max(xeq, 1e-6))
    average_activity = _p("catalyst.average_activity_factor")
    rplant = r0 * plant_drive * average_activity
    cap = _p("basis.capacity_t_per_y")
    hours = _p("basis.operating_hours_per_y")
    product_kg_h = cap * 1000.0 / hours / recovery
    catalyst_kg = product_kg_h / max(rplant, 1e-12)
    catalyst_m3 = catalyst_kg / _p("catalyst.bulk_density_kg_per_m3")

    # Material boundary, tonnes per tonne of methanol product.
    co2_in_t = fresh_co2 * REACTION["MW"]["CO2"] / 1000.0
    h2_in_t = fresh_h2 * REACTION["MW"]["H2"] / 1000.0
    out_co2_kmol = dissolved_co2 + purge * gas_co2
    out_h2_kmol = purge * gas_h2
    out_co_kmol = n_co
    out_water_kmol = n_converted
    out_meoh_loss_kmol = n_meoh - n_product

    # Energies per tonne product.
    Tco2 = _p("basis.feeds.CO2.T_K")
    Th2 = _p("basis.feeds.H2.T_K")
    Pco2 = _p("basis.feeds.CO2.P_bar")
    Ph2 = _p("basis.feeds.H2.P_bar")
    e_c1 = _compressor_power(fresh_co2, Tco2, Pco2, P, _p("compressor.gamma_CO2"))
    e_c2 = _compressor_power(fresh_h2, Th2, Ph2, P, _p("compressor.gamma_H2"))
    dp = _p("recycle.pressure_drop_fraction")
    e_rc = _compressor_power(recycle_kmol, _p("basis.utilities.cooling_water_supply_temperature"), P * (1.0 - dp), P, _p("compressor.gamma_recycle"))
    cp = _p("thermo.gas_cp_GJ_per_kmol_K")
    sensible = reactor_feed_kmol * cp * max(T - _p("basis.feeds.CO2.T_K"), 0.0)
    recovered = sensible * _p("heat_recovery.feed_effluent_fraction")
    e_trim = max(0.0, sensible - recovered)
    dh_meoh = _p("thermo.methanol_reaction_heat_kJ_per_mol") + _p("thermo.reaction_heat_temperature_coefficient_kJ_per_mol_K") * (T - 493.0)
    reactor_heat = dh_meoh * n_meoh / 1000.0
    condense = 1.10 * n_meoh * 0.0353 + out_water_kmol * 0.0407
    cooling_duty = max(0.0, (sensible - recovered) + condense)
    e_cooling = cooling_duty * _p("utilities.cooling_electricity_fraction")
    e_dist = _p("separation.distillation_base_GJ_per_t_methanol") / recovery + _p("separation.stabilization_GJ_per_kmol_dissolved_CO2") * dissolved_co2
    pump_dp_bar = max(0.0, _p("basis.product.CH3OH.P_bar") - _p("pump.column_outlet_pressure_bar"))
    e_pump = pump_dp_bar * 1e5 / (_p("pump.methanol_density_kg_per_m3") * _p("pump.isentropic_efficiency")) / 1e6
    e_offsites = _p("offsites.energy_GJ_per_t")

    # Installed capital by exact flowsheet unit.
    tph = cap / hours
    capacity_scale = (cap / _p("capital.reference_capacity_t_per_y")) ** _p("capital.scale_exponent")
    def mw(e):
        return e * tph / 3.6
    def comp_cap(e):
        return max(_p("capital.compressor_min_USD"), mw(e) * 1000.0 * _p("capital.compressor_USD_per_kW"))
    c_c1 = comp_cap(e_c1)
    c_c2 = comp_cap(e_c2)
    c_mix = _p("capital.mixer_reference_USD") * capacity_scale * (max(reactor_feed_kmol, 1.0) / _p("capital.reference_gas_kmol_per_t")) ** _p("capital.scale_exponent")
    c_hx = max(_p("capital.heat_exchanger_min_USD"), mw(recovered) * 1000.0 * _p("capital.heat_exchanger_USD_per_kW"))
    c_trim = max(_p("capital.heat_exchanger_min_USD"), mw(e_trim) * 1000.0 * _p("capital.heat_exchanger_USD_per_kW"))
    c_reactor = (_p("capital.reactor_fixed_USD") * capacity_scale + _p("capital.reactor_volume_reference_USD") * (max(catalyst_m3, 0.1) / _p("capital.reactor_reference_m3")) ** _p("capital.scale_exponent") + mw(abs(reactor_heat)) * 1000.0 * _p("capital.reactor_heat_removal_USD_per_kW"))
    c_ko = _p("capital.knockout_reference_USD") * capacity_scale * (max(reactor_feed_kmol, 1.0) / _p("capital.reference_gas_kmol_per_t")) ** _p("capital.scale_exponent")
    c_split = _p("capital.splitter_reference_USD") * capacity_scale * (max(recycle_kmol, 1.0) / _p("capital.reference_gas_kmol_per_t")) ** _p("capital.scale_exponent")
    c_rc = comp_cap(e_rc)
    crude_kmol = n_meoh + out_water_kmol + dissolved_co2
    c_col = _p("capital.column_reference_USD") * capacity_scale * (max(crude_kmol, 1.0) / _p("capital.reference_liquid_kmol_per_t")) ** _p("capital.scale_exponent")
    c_pump = _p("capital.pump_reference_USD") * capacity_scale
    direct_before_offsites = c_c1+c_c2+c_mix+c_hx+c_trim+c_reactor+c_ko+c_split+c_rc+c_col+c_pump
    c_off = _p("capital.offsites_fixed_USD") * capacity_scale + _p("capital.offsites_fraction_direct") * direct_before_offsites

    life = rec.get("t_cycle_h")
    if life is None or not np.isfinite(float(life)) or float(life) <= 0:
        life = _p("catalyst.default_life_h")
    catalyst_price = _component_cost(rec)

    units = [
        {"name":"CO2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":e_c1,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_c1,"kmol_per_t":fresh_co2,"T_in_K":Tco2,"P_in_bar":Pco2,"P_out_bar":max(P,Pco2),"power_GJ_per_t":e_c1},
        {"name":"H2 feed compressor","type":"compressor","purchased_energy_GJ_per_t":e_c2,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_c2,"kmol_per_t":fresh_h2,"T_in_K":Th2,"P_in_bar":Ph2,"P_out_bar":max(P,Ph2),"power_GJ_per_t":e_c2},
        {"name":"Feed mixer","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_mix,"component_feed_kmol_per_t":{"CO2":reactor_co2,"H2":reactor_h2,"CO":reactor_co_in}},
        {"name":"Feed-effluent heat exchanger","type":"heat_exchanger","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":recovered,"capex_usd":c_hx},
        {"name":"Electric trim preheater","type":"heat_exchanger","purchased_energy_GJ_per_t":e_trim,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_trim},
        {"name":"Cooled fixed-bed reactor","type":"reactor","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":max(0.0,-reactor_heat),"capex_usd":c_reactor,"T_K":T,"P_bar":P,"heat_duty_GJ_per_t":reactor_heat,"reaction_extents_kmol_per_t":{"methanol":n_meoh,"RWGS_selectivity_byproduct":n_co},"reaction_heat_scope":"fixed contracted methanol reaction thermochemistry; RWGS represented in material/selectivity accounting","catalyst_inventory_kg":catalyst_kg,"catalyst_volume_m3":catalyst_m3,"catalyst_price_USD_per_kg":catalyst_price,"catalyst_life_h":float(life),"average_activity_factor":average_activity,"annual_replacement_kg":catalyst_kg*hours/float(life)},
        {"name":"Effluent condenser and knockout","type":"knockout","purchased_energy_GJ_per_t":e_cooling,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_ko,"cooling_duty_GJ_per_t":cooling_duty},
        {"name":"Recycle purge splitter","type":"other","purchased_energy_GJ_per_t":0.0,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_split,"separator_gas_kmol_per_t":{"CO2":gas_co2,"H2":gas_h2,"CO":separator_co},"purge_fraction":purge,"purge_kmol_per_t":{"CO2":purge*gas_co2,"H2":purge*gas_h2,"CO":purge*separator_co},"recycle_kmol_per_t":{"CO2":recycle_co2,"H2":recycle_h2,"CO":recycle_co}},
        {"name":"Recycle compressor","type":"compressor","purchased_energy_GJ_per_t":e_rc,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_rc,"kmol_per_t":recycle_kmol,"T_in_K":_p("basis.utilities.cooling_water_supply_temperature"),"P_in_bar":P*(1.0-dp),"P_out_bar":P,"power_GJ_per_t":e_rc},
        {"name":"Methanol purification column","type":"separation","purchased_energy_GJ_per_t":e_dist,"internal_fuel_GJ_per_t":0.0,"recovered_heat_GJ_per_t":0.0,"capex_usd":c_col,"feed":_stream({"CH3OH":n_meoh,"H2O":out_water_kmol,"CO2":dissolved_co2}),"outlets":[_stream({"CH3OH":n_product}),_stream({"CH3OH":out_meoh_loss_kmol,"H2O":out_water_kmol,"CO2":dissolved_co2})]},
        {"name":"Methanol product pump","type":"pump","purchased_energy_GJ_per_t":e_pump,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_pump,"P_in_bar":_p("pump.column_outlet_pressure_bar"),"P_out_bar":_p("basis.product.CH3OH.P_bar"),"power_GJ_per_t":e_pump},
        {"name":"Product storage and offsites","type":"offsites","purchased_energy_GJ_per_t":e_offsites,"internal_fuel_GJ_per_t":0.0,"capex_usd":c_off}
    ]
    total_energy = sum(u["purchased_energy_GJ_per_t"] for u in units)
    capex = sum(u["capex_usd"] for u in units)
    feed_cost = co2_in_t / _p("basis.feeds.CO2.purity_mol_frac") * _p("price.carbon_dioxide") + h2_in_t * 1000.0 / _p("basis.feeds.H2.purity_mol_frac") * _p("price.hydrogen")
    energy_cost = total_energy / 3.6 * _p("price.electricity")
    capital_cost = (_p("price.capital_recovery_factor") + _p("price.fixed_om_fraction_of_capex")) * capex / cap
    life = rec.get("t_cycle_h")
    if life is None or not np.isfinite(float(life)) or float(life) <= 0:
        life = _p("catalyst.default_life_h")
    catalyst_price = _component_cost(rec)
    catalyst_cost = catalyst_kg * catalyst_price * hours / float(life) / cap
    parts = {"feed":feed_cost,"energy":energy_cost,"capital":capital_cost,"catalyst":catalyst_cost,"other":0.0}
    total_cost = sum(parts.values())
    feedfrac = {"CO2":reactor_co2/reactor_feed_kmol,"H2":reactor_h2/reactor_feed_kmol,"CO":reactor_co_in/reactor_feed_kmol}
    physics = {
        "reactor":{"T_K":T,"P_bar":P,"feed_mol_frac":feedfrac,"per_pass_conversion":X,"heat_duty_GJ_per_t":reactor_heat},
        "boundary":{"in_t_per_t":{"CO2":co2_in_t,"H2":h2_in_t},"out_t_per_t":{"CH3OH":1.0+out_meoh_loss_kmol*REACTION["MW"]["CH3OH"]/1000.0,"H2O":out_water_kmol*REACTION["MW"]["H2O"]/1000.0,"CO":out_co_kmol*REACTION["MW"]["CO"]/1000.0,"CO2":out_co2_kmol*REACTION["MW"]["CO2"]/1000.0,"H2":out_h2_kmol*REACTION["MW"]["H2"]/1000.0}},
        "units":units
    }
    return {"cost_usd_per_t":total_cost,"parts":parts,"operating":{"T_K":T,"P_bar":P,"per_pass_conversion":X,"purge_fraction":purge,"equilibrium_conversion":xeq},"balances":{"key_feed_t_per_t":co2_in_t,"energy_GJ_per_t":total_energy,"capex_usd":capex,"capacity_t_per_y":cap},"physics":physics,"normalization":{"basis":"one tonne final stored methanol","product_CH3OH_t":1.0,"aqueous_loss_CH3OH_t":out_meoh_loss_kmol*REACTION["MW"]["CH3OH"]/1000.0},"_catalyst_kg":catalyst_kg,"_rplant":rplant}


def plant_cost(rec):
    T = float(rec["T_K"])
    P = float(rec["P_bar"])
    yco2 = max(float(rec.get("y_key", 0.25)), 1e-6)
    yh2 = max(float(rec.get("y_cofeed", 0.75)), 1e-6)
    xeq = _equilibrium_conversion(T, P, max(yh2/yco2, 3.0001))
    xmin = max(0.002, min(0.02, 0.10 * xeq))
    xmax = max(xmin * 1.05, min(0.90 * xeq, 0.85))
    pmin = _p("recycle.purge_min_fraction")
    pmax = _p("recycle.purge_max_fraction")

    def best_for_x(x):
        def obj_p(p):
            z = _evaluate(rec, float(x), float(p), False)
            return 1e30 if z is None else z["cost_usd_per_t"]
        optp = minimize_scalar(obj_p, bounds=(pmin, pmax), method="bounded", options={"xatol":1e-5,"maxiter":100})
        return float(optp.fun), float(optp.x)

    def obj_x(x):
        return best_for_x(float(x))[0]
    optx = minimize_scalar(obj_x, bounds=(xmin, xmax), method="bounded", options={"xatol":1e-5,"maxiter":120})
    _, purge = best_for_x(float(optx.x))
    ans = _evaluate(rec, float(optx.x), purge, True)
    if ans is None or not np.isfinite(ans["cost_usd_per_t"]):
        raise ValueError("No finite feasible plant operating point")
    ans.pop("_catalyst_kg", None)
    ans.pop("_rplant", None)
    return ans


def reference():
    record = {"T_K":493.0,"P_bar":30.0,"X":0.064,"S":0.57,"r":0.44,"y_key":0.2222222222222222,"y_cofeed":0.7777777777777777,"t_cycle_h":None,"components":[["Cu",None],["Zn",None]],"catalyst":"FHI-standard commercial Cu/ZnO/Al2O3"}
    out = plant_cost(record)
    out["name"] = "Published commercial Cu/ZnO/Al2O3 reference at 493 K and 30 bar"
    out["record"] = record
    return out
