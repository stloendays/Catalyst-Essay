import csv
import math
import ast
from pathlib import Path
import numpy as np


def _load_params():
    out = {}
    with open(Path(__file__).with_name('sources.csv'), newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            out[row['parameter']] = float(row['value'])
    return out


PARAMS = _load_params()

REACTION = {
    'key': 'CO2',
    'product': 'CH3OH',
    'cofeed': 'H2',
    'MW': {'CO2': 44.0095, 'H2': 2.01588, 'CH3OH': 32.04186, 'H2O': 18.01528},
    'nu': {'CO2': -1.0, 'H2': -3.0, 'CH3OH': 1.0, 'H2O': 1.0},
}

MW = {'CO2': 44.0095, 'H2': 2.01588, 'CH3OH': 32.04186, 'H2O': 18.01528, 'CO': 28.0101}
R_KJ_KMOL_K = 8.314462618


def _v(key):
    return float(PARAMS[key])


def _eq_constant(T):
    dh = _v('thermo.methanol_reaction_enthalpy_kJ_per_mol')
    ds = _v('thermo.methanol_reaction_entropy_J_per_mol_K') / 1000.0
    return math.exp(max(-80.0, min(80.0, -dh / (0.008314462618 * T) + ds / 0.008314462618)))


def _reaction_quotient(x, T, P, ratio, S):
    x = max(1e-12, min(x, 0.999999))
    S = max(1e-6, min(S, 1.0))
    n = {
        'CO2': 1.0 - x,
        'H2': ratio - (1.0 + 2.0 * S) * x,
        'CH3OH': S * x,
        'H2O': x,
        'CO': (1.0 - S) * x,
    }
    if n['CO2'] <= 0.0 or n['H2'] <= 0.0:
        return 1e100
    nt = sum(n.values())
    pco2 = n['CO2'] / nt * P
    ph2 = n['H2'] / nt * P
    pmeoh = n['CH3OH'] / nt * P
    ph2o = n['H2O'] / nt * P
    return (pmeoh * ph2o) / max(1e-300, pco2 * ph2 ** 3)


def _equilibrium_conversion(T, P, ratio, S):
    xmax_stoich = min(0.999, ratio / max(1.000001, 1.0 + 2.0 * max(S, 1e-6)) * 0.999)
    K = _eq_constant(T)
    lo, hi = 1e-10, xmax_stoich
    if _reaction_quotient(hi, T, P, ratio, S) < K:
        return hi
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if _reaction_quotient(mid, T, P, ratio, S) < K:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _compressor_energy(n_kmol, T, P_in, P_out):
    if n_kmol <= 0.0 or P_out <= P_in * (1.0 + 1e-12):
        return 0.0
    k = _v('process.compressor_heat_capacity_ratio')
    eta = _v('basis.utilities.compressor_isentropic_efficiency')
    motor = _v('basis.utilities.motor_efficiency')
    work_kJ = n_kmol * R_KJ_KMOL_K * T * k / (k - 1.0) * ((P_out / P_in) ** ((k - 1.0) / k) - 1.0)
    return work_kJ / 1e6 / eta / motor


def _scaled_cost(reference_cost, scale, exponent=None):
    expn = _v('capex.scale_exponent') if exponent is None else exponent
    floor = _v('capex.minimum_unit_cost_usd')
    return max(floor, reference_cost * max(scale, 1e-9) ** expn)


def _compressor_capex(power_kW):
    return max(_scaled_cost(_v('capex.compressor_reference_cost_usd'), power_kW / _v('capex.compressor_reference_power_kW')), _v('capex.minimum_compressor_usd_per_kW') * power_kW)


def _hx_capex(duty_MW):
    return _scaled_cost(_v('capex.heat_exchanger_reference_cost_usd'), duty_MW / _v('capex.heat_exchanger_reference_duty_MW'))


def _stream(n):
    total = sum(max(0.0, float(v)) for v in n.values())
    if total <= 0.0:
        return {'kmol_per_t': 0.0, 'mol_frac': {k: 0.0 for k in n}}
    return {'kmol_per_t': total, 'mol_frac': {k: max(0.0, float(v)) / total for k, v in n.items()}}


def _components(rec):
    comps = rec.get('components', rec.get('elements', []))
    if isinstance(comps, str):
        try:
            comps = ast.literal_eval(comps)
        except Exception:
            comps = []
    return comps or []


def _catalyst_price(rec):
    base = _v('price.catalyst_support_and_manufacturing')
    default_w = _v('process.unknown_component_wt_fraction')
    addition = 0.0
    total_w = 0.0
    for item in _components(rec):
        if not item or len(item) < 1:
            continue
        element = str(item[0])
        raw = item[1] if len(item) > 1 else None
        w = default_w if raw is None else float(raw) / 100.0
        w = max(0.0, min(w, 1.0 - total_w))
        key = 'price.metal_' + element
        if key in PARAMS:
            addition += w * _v(key)
        total_w += w
        if total_w >= 1.0:
            break
    return base + addition


def _life_y(rec):
    t_cycle = rec.get('t_cycle_h', None)
    if t_cycle is None or not np.isfinite(float(t_cycle)) or float(t_cycle) <= 0.0:
        return _v('process.default_catalyst_life_y')
    life = float(t_cycle) * _v('process.cycle_to_replacement_multiplier') / _v('basis.operating_hours_per_y')
    return min(_v('process.maximum_catalyst_life_y'), max(_v('process.minimum_catalyst_life_y'), life))


def _evaluate(rec, x):
    T = float(rec['T_K'])
    P = float(rec['P_bar'])
    S = max(1e-4, min(1.0, float(rec['S'])))
    r_lab = max(1e-9, float(rec['r']))
    y_key = rec.get('y_key', None)
    y_h2 = rec.get('y_cofeed', rec.get('y_h2', None))
    if y_key is None or y_h2 is None or not np.isfinite(float(y_key)) or not np.isfinite(float(y_h2)) or float(y_key) <= 0.0:
        ratio = _v('process.default_h2_co2_ratio')
    else:
        ratio = max(2.8, float(y_h2) / float(y_key))

    cond_meoh = _v('process.methanol_condensation_recovery')
    dist_rec = _v('process.distillation_methanol_recovery')
    cond_water = _v('process.water_condensation_recovery')
    co2_carry = _v('process.co2_liquid_carryover_fraction')
    purge = _v('process.purge_fraction')

    n_product = 1000.0 / MW['CH3OH']
    n_meoh = n_product / (cond_meoh * dist_rec)
    n_co2_conv = n_meoh / S
    n_co = n_co2_conv - n_meoh
    n_h2_cons = 3.0 * n_meoh + n_co
    n_co2_in = n_co2_conv / x
    n_co2_out = n_co2_in - n_co2_conv
    n_h2_in = ratio * n_co2_in
    n_h2_out = max(0.0, n_h2_in - n_h2_cons)
    n_co_in = (1.0 - purge) / purge * n_co
    n_co_out = n_co_in + n_co

    n_co2_recycle = (1.0 - purge) * (1.0 - co2_carry) * n_co2_out
    n_h2_recycle = (1.0 - purge) * n_h2_out
    n_co_recycle = (1.0 - purge) * n_co_out
    n_co2_fresh = n_co2_in - n_co2_recycle
    n_h2_fresh = n_h2_in - n_h2_recycle

    lab_xeq = _equilibrium_conversion(T, P, ratio, 1.0)
    lab_X = max(0.0, min(float(rec['X']), 0.999 * lab_xeq))
    floor = _v('process.driving_force_floor')
    lab_df = max(floor, 1.0 - lab_X / max(lab_xeq, 1e-9))
    plant_xeq = lab_xeq
    plant_df = max(floor, 1.0 - x / max(plant_xeq, 1e-9))
    effective_r = r_lab / lab_df * plant_df

    capacity = _v('basis.capacity_t_per_y')
    hours = _v('basis.operating_hours_per_y')
    production_kg_h = capacity * 1000.0 / hours * (n_meoh / n_product)
    catalyst_kg = production_kg_h / effective_r / _v('process.catalyst_working_fraction')

    co2_t = n_co2_fresh * MW['CO2'] / 1000.0
    h2_t = n_h2_fresh * MW['H2'] / 1000.0
    co2_purchase_t = co2_t / _v('basis.feeds.CO2.purity_mol_frac')
    h2_purchase_kg = h2_t * 1000.0 / _v('basis.feeds.H2.purity_mol_frac')
    feed_cost = co2_purchase_t * _v('price.carbon_dioxide') + h2_purchase_kg * _v('price.hydrogen')

    co2_comp_Pin = _v('basis.feeds.CO2.P_bar')
    h2_comp_Pin = _v('basis.feeds.H2.P_bar')
    co2_comp_el = _compressor_energy(n_co2_fresh / _v('basis.feeds.CO2.purity_mol_frac'), _v('basis.feeds.CO2.T_K'), co2_comp_Pin, P)
    h2_comp_el = _compressor_energy(n_h2_fresh / _v('basis.feeds.H2.purity_mol_frac'), _v('basis.feeds.H2.T_K'), h2_comp_Pin, P)
    recycle_kmol = n_co2_recycle + n_h2_recycle + n_co_recycle
    recycle_Pin = P * (1.0 - _v('process.loop_pressure_drop_fraction'))
    recycle_el = _compressor_energy(recycle_kmol, _v('process.recycle_compressor_inlet_temperature_K'), recycle_Pin, P)

    total_reactor_feed = n_co2_in + n_h2_in + n_co_in
    total_reactor_out = n_co2_out + n_h2_out + n_co_out + n_meoh + n_co2_conv
    cp = _v('process.gas_heat_capacity_kJ_per_kmol_K')
    Tcond = _v('process.condensation_temperature_K')
    sensible_total = max(0.0, total_reactor_out * cp * (T - Tcond) / 1e6)
    freshT = (n_co2_fresh * _v('basis.feeds.CO2.T_K') + n_h2_fresh * _v('basis.feeds.H2.T_K') + recycle_kmol * Tcond) / max(n_co2_fresh + n_h2_fresh + recycle_kmol, 1e-9)
    preheat_need = max(0.0, total_reactor_feed * cp * (T - freshT) / 1e6)
    recovered_sensible = min(preheat_need, sensible_total * _v('process.feed_effluent_heat_recovery_fraction'))
    preheat_shortfall = max(0.0, preheat_need - recovered_sensible)
    cooler_sensible = max(0.0, sensible_total - recovered_sensible)
    latent = (n_meoh * MW['CH3OH'] * _v('process.methanol_latent_heat_kJ_per_kg') + n_co2_conv * MW['H2O'] * _v('process.water_latent_heat_kJ_per_kg')) / 1e6
    cooler_el = cooler_sensible / _v('process.cooling_COP')
    knockout_el = latent / _v('process.cooling_COP')

    dh_T = _v('thermo.methanol_reaction_enthalpy_kJ_per_mol') + _v('thermo.methanol_reaction_deltaCp_kJ_per_mol_K') * (T - 298.15)
    q_reaction = n_meoh * dh_T / 1000.0
    recoverable_reaction_heat = max(0.0, -q_reaction) * _v('process.reactor_heat_recovery_fraction')
    heat_supply = max(0.0, q_reaction) + preheat_shortfall

    crude_meoh = n_meoh * cond_meoh
    crude_water = n_co2_conv * cond_water
    crude_co2 = n_co2_out * co2_carry
    crude_mass_t = (crude_meoh * MW['CH3OH'] + crude_water * MW['H2O'] + crude_co2 * MW['CO2']) / 1000.0
    dist_heat = crude_mass_t * _v('process.distillation_reboiler_GJ_per_t_crude')
    heat_recovered_to_dist = min(dist_heat, recoverable_reaction_heat)
    dist_fuel = max(0.0, dist_heat - heat_recovered_to_dist) / _v('basis.utilities.steam_generation_efficiency')
    heat_manager_fuel = heat_supply / _v('basis.utilities.steam_generation_efficiency')
    dist_el = crude_mass_t * _v('process.distillation_electricity_GJ_per_t_crude')

    pef = _v('basis.utilities.primary_energy_factor_electricity')
    electricity_GJ = co2_comp_el + h2_comp_el + recycle_el + cooler_el + knockout_el + dist_el
    fuel_GJ = dist_fuel + heat_manager_fuel
    energy_primary = electricity_GJ * pef + fuel_GJ
    energy_cost = electricity_GJ / 3.6 * _v('price.electricity') + fuel_GJ * _v('price.natural_gas')

    tph = capacity / hours
    def power_kw(e): return e * tph * 277.7777778
    def duty_mw(q): return abs(q) * tph / 3.6
    flow_scale = capacity / 100000.0 * (total_reactor_feed / _v('capex.reference_loop_kmol_per_t'))
    crude_scale = capacity / 100000.0 * (crude_mass_t / _v('capex.reference_crude_t_per_t_product'))

    cap_co2 = _compressor_capex(power_kw(co2_comp_el))
    cap_h2 = _compressor_capex(power_kw(h2_comp_el))
    cap_mixer = _scaled_cost(_v('capex.mixer_reference_cost_usd'), flow_scale)
    cap_fehx = _hx_capex(duty_mw(recovered_sensible))
    cap_reactor = _v('capex.reactor_base_cost_usd') * (capacity / 100000.0 + catalyst_kg / _v('capex.reactor_reference_catalyst_inventory_kg')) ** _v('capex.scale_exponent')
    cap_heat = _hx_capex(duty_mw(max(abs(q_reaction), heat_supply)))
    cap_cooler = _hx_capex(duty_mw(cooler_sensible))
    cap_knockout = _scaled_cost(_v('capex.knockout_reference_cost_usd'), flow_scale)
    cap_splitter = _scaled_cost(_v('capex.splitter_reference_cost_usd'), flow_scale)
    cap_recycle = _compressor_capex(power_kw(recycle_el))
    cap_dist = _scaled_cost(_v('capex.distillation_reference_cost_usd'), crude_scale)
    direct_before_offsites = cap_co2 + cap_h2 + cap_mixer + cap_fehx + cap_reactor + cap_heat + cap_cooler + cap_knockout + cap_splitter + cap_recycle + cap_dist
    cap_offsites = direct_before_offsites * _v('capex.offsites_fraction_direct_capex')
    capex = direct_before_offsites + cap_offsites

    catalyst_price = _catalyst_price(rec)
    catalyst_cost = catalyst_kg * catalyst_price / _life_y(rec) / capacity
    capital_cost = capex * _v('price.capital_recovery_factor') / capacity
    other_cost = capex * _v('price.fixed_om_fraction_of_capex') / capacity
    total_cost = feed_cost + energy_cost + capital_cost + catalyst_cost + other_cost

    electric_primary = lambda e: e * pef
    units = [
        {'name':'CO2 Feed Compressor','type':'compressor','purchased_energy_GJ_per_t':electric_primary(co2_comp_el),'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_co2,'kmol_per_t':n_co2_fresh / _v('basis.feeds.CO2.purity_mol_frac'),'T_in_K':_v('basis.feeds.CO2.T_K'),'P_in_bar':co2_comp_Pin,'P_out_bar':P,'power_GJ_per_t':co2_comp_el},
        {'name':'H2 Feed Compressor','type':'compressor','purchased_energy_GJ_per_t':electric_primary(h2_comp_el),'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_h2,'kmol_per_t':n_h2_fresh / _v('basis.feeds.H2.purity_mol_frac'),'T_in_K':_v('basis.feeds.H2.T_K'),'P_in_bar':h2_comp_Pin,'P_out_bar':P,'power_GJ_per_t':h2_comp_el},
        {'name':'Feed Mixer','type':'other','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_mixer,'kmol_per_t':total_reactor_feed},
        {'name':'Feed-Effluent Exchanger','type':'heat_exchanger','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'recovered_heat_GJ_per_t':recovered_sensible,'capex_usd':cap_fehx,'heat_duty_GJ_per_t':recovered_sensible},
        {'name':'Synthesis Reactor','type':'reactor','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_reactor,'heat_duty_GJ_per_t':q_reaction,'catalyst_inventory_kg':catalyst_kg},
        {'name':'Reactor Heat Management','type':'heat_exchanger','purchased_energy_GJ_per_t':heat_manager_fuel,'internal_fuel_GJ_per_t':0.0,'recovered_heat_GJ_per_t':recoverable_reaction_heat,'capex_usd':cap_heat,'heat_duty_GJ_per_t':-q_reaction,'preheat_shortfall_GJ_per_t':preheat_shortfall},
        {'name':'Effluent Cooler','type':'heat_exchanger','purchased_energy_GJ_per_t':electric_primary(cooler_el),'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_cooler,'cooling_duty_GJ_per_t':cooler_sensible},
        {'name':'Condensate Knockout','type':'knockout','purchased_energy_GJ_per_t':electric_primary(knockout_el),'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_knockout,'cooling_duty_GJ_per_t':latent},
        {'name':'Recycle Purge Splitter','type':'other','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_splitter,'purge_fraction':purge},
        {'name':'Recycle Compressor','type':'compressor','purchased_energy_GJ_per_t':electric_primary(recycle_el),'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_recycle,'kmol_per_t':recycle_kmol,'T_in_K':_v('process.recycle_compressor_inlet_temperature_K'),'P_in_bar':recycle_Pin,'P_out_bar':P,'power_GJ_per_t':recycle_el},
        {'name':'Crude Methanol Distillation','type':'separation','purchased_energy_GJ_per_t':dist_fuel + electric_primary(dist_el),'internal_fuel_GJ_per_t':0.0,'recovered_heat_GJ_per_t':heat_recovered_to_dist,'capex_usd':cap_dist,'feed':_stream({'CH3OH':crude_meoh,'H2O':crude_water,'CO2':crude_co2}),'outlets':[_stream({'CH3OH':n_product}),_stream({'CH3OH':max(0.0,crude_meoh-n_product),'H2O':crude_water,'CO2':crude_co2})]},
        {'name':'Utilities and Offsites','type':'offsites','purchased_energy_GJ_per_t':0.0,'internal_fuel_GJ_per_t':0.0,'capex_usd':cap_offsites,'wastewater_t_per_t':(crude_water*MW['H2O']+max(0.0,crude_meoh-n_product)*MW['CH3OH']+crude_co2*MW['CO2'])/1000.0},
    ]

    methanol_total_t = n_meoh * MW['CH3OH'] / 1000.0
    water_t = n_co2_conv * MW['H2O'] / 1000.0
    co_t = n_co * MW['CO'] / 1000.0
    co2_unreacted_loss_t = (n_co2_fresh - n_co2_conv) * MW['CO2'] / 1000.0
    h2_loss_t = (n_h2_fresh - n_h2_cons) * MW['H2'] / 1000.0

    reactor_feed = {'CO2':n_co2_in,'H2':n_h2_in,'CO':n_co_in}
    result = {
        'cost_usd_per_t':total_cost,
        'parts':{'feed':feed_cost,'energy':energy_cost,'capital':capital_cost,'catalyst':catalyst_cost,'other':other_cost},
        'operating':{'T_K':T,'P_bar':P,'per_pass_conversion':x},
        'balances':{'key_feed_t_per_t':co2_t,'energy_GJ_per_t':energy_primary,'capex_usd':capex,'capacity_t_per_y':capacity},
        'physics':{
            'reactor':{'T_K':T,'P_bar':P,'feed_mol_frac':_stream(reactor_feed)['mol_frac'],'per_pass_conversion':x,'heat_duty_GJ_per_t':q_reaction},
            'boundary':{'in_t_per_t':{'CO2':co2_t,'H2':h2_t},'out_t_per_t':{'CH3OH':methanol_total_t,'H2O':water_t,'CO':co_t,'CO2':max(0.0,co2_unreacted_loss_t),'H2':max(0.0,h2_loss_t)}},
            'units':units,
        },
    }
    return result


def plant_cost(rec):
    T = float(rec['T_K'])
    P = float(rec['P_bar'])
    S = max(1e-4, min(1.0, float(rec['S'])))
    y_key = rec.get('y_key', None)
    y_h2 = rec.get('y_cofeed', rec.get('y_h2', None))
    if y_key is None or y_h2 is None or not np.isfinite(float(y_key)) or not np.isfinite(float(y_h2)) or float(y_key) <= 0.0:
        ratio = _v('process.default_h2_co2_ratio')
    else:
        ratio = max(2.8, float(y_h2) / float(y_key))
    xeq = _equilibrium_conversion(T, P, ratio, 1.0) * _v('process.equilibrium_safety_fraction')
    xmax = min(_v('process.maximum_per_pass_conversion'), xeq)
    xmin = min(_v('process.minimum_per_pass_conversion'), max(0.002, 0.25 * xmax))
    if xmax <= xmin:
        xs = np.array([max(0.001, 0.8 * xmax)])
    else:
        xs = np.linspace(xmin, xmax, 81)
    best = None
    for x in xs:
        try:
            ans = _evaluate(rec, float(x))
        except Exception:
            continue
        if np.isfinite(ans['cost_usd_per_t']) and ans['cost_usd_per_t'] > 0.0:
            if best is None or ans['cost_usd_per_t'] < best['cost_usd_per_t']:
                best = ans
    if best is None:
        raise ValueError('No finite feasible operating point')
    return best


def reference():
    record = {
        'T_K':573.15,
        'P_bar':20.0,
        'X':0.034,
        'S':0.87,
        'r':0.248,
        'y_key':0.25,
        'y_cofeed':0.75,
        't_cycle_h':None,
        'components':[['Zn',None],['Zr',None]],
        'catalyst':'13%ZnO-ZrO2 solid solution (Science Advances 2017)',
    }
    out = plant_cost(record)
    out['name'] = '100 kt/y CO2-to-methanol reference plant with published ZnO-ZrO2 catalyst record'
    out['record'] = record
    return out
