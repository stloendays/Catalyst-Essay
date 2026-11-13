import csv, math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq, minimize_scalar

REACTION = {
    "key": "NH3", "product": "H2", "cofeed": None,
    "MW": {"NH3": 17.031, "N2": 28.014, "H2": 2.016},
    "nu": {"NH3": -1.0, "N2": 0.5, "H2": 1.5},
}


def _load_params():
    out = {}
    with open(Path(__file__).with_name("sources.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["parameter"]] = float(row["value"])
    return out

PARAMS = _load_params()

UNIT_NAMES = [
    "U1 Fresh ammonia pump", "U2 Feed-recycle mixer", "U3 Feed-effluent recuperator",
    "U4 Ammonia vaporizer and trim heater", "U5 Electric reaction furnace",
    "U6 Packed-bed ammonia decomposition reactor", "U7 Ammonia condenser",
    "U8 Ammonia knockout drum", "U9 Ammonia recycle pump", "U10 Hydrogen PSA",
    "U11 Hydrogen product compressor", "U12 Utilities and offsites"
]


def _p(name):
    return float(PARAMS[name])


def _finite(v, default):
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except Exception:
        return default


def _equilibrium_constant(T):
    R = 8.314462618
    dH = _p("thermo.deltaH_kJ_per_mol_NH3") * 1000.0
    dS = _p("thermo.deltaS_J_per_molK_NH3")
    return math.exp(max(-100.0, min(100.0, dS / R - dH / (R * T))))


def _q_for_conversion(x, P_bar, y_nh3=1.0):
    x = min(max(float(x), 1e-12), 1.0 - 1e-12)
    y = min(max(float(y_nh3), 1e-8), 1.0)
    n_nh3 = y * (1.0 - x)
    n_n2 = 0.5 * y * x
    n_h2 = 1.5 * y * x
    n_inert = 1.0 - y
    nt = n_nh3 + n_n2 + n_h2 + n_inert
    p_nh3 = max(1e-12, P_bar * n_nh3 / nt)
    p_n2 = max(1e-12, P_bar * n_n2 / nt)
    p_h2 = max(1e-12, P_bar * n_h2 / nt)
    q = (p_n2 ** 0.5) * (p_h2 ** 1.5) / p_nh3
    return q, p_nh3, p_h2, p_n2


def _equilibrium_conversion(T, P_bar):
    K = _equilibrium_constant(T)
    def f(x):
        return math.log(max(_q_for_conversion(x, P_bar, 1.0)[0], 1e-300)) - math.log(max(K, 1e-300))
    try:
        return float(brentq(f, 1e-9, 1.0 - 1e-9, maxiter=100))
    except Exception:
        return 1e-6 if f(0.5) > 0 else 0.999999


def _rate_at_plant(rec, x, T, P):
    r0 = max(_finite(rec.get("r"), _p("kinetics.rate_floor_kg_per_kg_h")), _p("kinetics.rate_floor_kg_per_kg_h"))
    Tlab = max(300.0, _finite(rec.get("T_K"), T))
    Plab = max(0.05, _finite(rec.get("P_bar"), 1.01325))
    ylab = min(max(_finite(rec.get("y_key"), 1.0), 1e-5), 1.0)
    xlab = min(max(_finite(rec.get("X"), 0.1), 1e-5), 0.999999)
    Ea = _p("kinetics.activation_energy_kJ_per_mol") * 1000.0
    arr = math.exp(max(-50.0, min(50.0, -Ea / 8.314462618 * (1.0 / T - 1.0 / Tlab))))
    qp, pnh3p, ph2p, _ = _q_for_conversion(0.5 * x, P, 1.0)
    ql, pnh3l, ph2l, _ = _q_for_conversion(0.5 * xlab, Plab, ylab)
    Kp = _equilibrium_constant(T)
    Kl = _equilibrium_constant(Tlab)
    approach_p = max(1e-4, 1.0 - qp / max(Kp, 1e-300))
    approach_l = max(1e-4, 1.0 - ql / max(Kl, 1e-300))
    reg = _p("kinetics.H2_regularization_bar")
    pressure_factor = (pnh3p / max(pnh3l, 1e-9)) ** _p("kinetics.NH3_order")
    inhibition = ((reg + ph2l) / (reg + ph2p)) ** _p("kinetics.H2_inhibition_order")
    return max(_p("kinetics.rate_floor_kg_per_kg_h"), r0 * arr * pressure_factor * inhibition * approach_p / approach_l)


def _catalyst_price(rec):
    base = _p("price.catalyst_support_and_manufacturing")
    custom = _finite(rec.get("metal_price_usd_per_kg"), float("nan"))
    loading = _finite(rec.get("metal_loading_wt_pct"), float("nan"))
    if math.isfinite(custom) and math.isfinite(loading):
        return max(base, base + min(max(loading, 0.0), 100.0) / 100.0 * custom)
    total = base
    seen = set()
    for item in rec.get("components", []) or []:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        el = str(item[0])
        wt = _finite(item[1], 0.0)
        if el in seen or wt <= 0.0:
            continue
        seen.add(el)
        key = "price.metal_" + el
        if key in PARAMS:
            total += min(wt, 100.0) / 100.0 * _p(key)
    return max(base, total)


def _capital_reference():
    return _p("capex.reference_installed_capital_usd")


def _evaluate(rec, x):
    MW = REACTION["MW"]
    capacity = _p("basis.capacity_t_per_y")
    hours = _p("basis.operating_hours_per_y")
    T = min(max(_finite(rec.get("T_K"), 773.15), 450.0), 1100.0)
    P = _p("process.reactor_pressure_bar")
    S = min(max(_finite(rec.get("S"), 1.0), 0.01), 1.0)
    psa_rec = _p("process.PSA_H2_recovery")
    nh3_rec = _p("process.NH3_condensation_recovery")
    product_H2_kmol = 1000.0 / MW["H2"]
    gross_H2_kmol = product_H2_kmol / psa_rec
    productive_NH3_kmol = (2.0 / 3.0) * gross_H2_kmol
    total_converted_NH3_kmol = productive_NH3_kmol / S
    reactor_NH3_in_kmol = total_converted_NH3_kmol / max(x, 1e-8)
    nonselective_NH3_kmol = total_converted_NH3_kmol - productive_NH3_kmol
    unconverted_NH3_kmol = reactor_NH3_in_kmol - total_converted_NH3_kmol
    recovered_NH3_kmol = nh3_rec * unconverted_NH3_kmol
    separator_NH3_loss_kmol = (1.0 - nh3_rec) * unconverted_NH3_kmol
    NH3_out_kmol = nonselective_NH3_kmol + separator_NH3_loss_kmol
    fresh_NH3_kmol = productive_NH3_kmol + NH3_out_kmol
    N2_kmol = 0.5 * productive_NH3_kmol
    tail_H2_kmol = gross_H2_kmol - product_H2_kmol

    rate = _rate_at_plant(rec, x, T, P) * S
    gross_H2_kg_h = capacity * 1000.0 / hours / psa_rec
    catalyst_mass_kg = gross_H2_kg_h / max(rate, 1e-12) * _p("catalyst.inventory_factor")
    tcycle = _finite(rec.get("t_cycle_h"), _p("deactivation.default_t_cycle_h"))
    tcycle = max(1.0, tcycle)
    availability = tcycle / (tcycle + _p("deactivation.replacement_outage_h"))
    catalyst_mass_kg /= availability
    cat_price = _catalyst_price(rec)
    annual_cat = catalyst_mass_kg * cat_price * hours / tcycle * (1.0 + _p("catalyst.replacement_labor_fraction"))

    reaction_heat_GJ = productive_NH3_kmol * (_p("thermo.deltaH_kJ_per_mol_NH3") + _p("thermo.reaction_deltaCp_J_per_molK_NH3") * (T - 298.15) / 1000.0) / 1000.0
    feed_T = _p("basis.feeds.NH3.T_K")
    sensible_liquid_GJ = fresh_NH3_kmol * MW["NH3"] * _p("process.NH3_liquid_Cp_kJ_per_kgK") * max(0.0, 298.15 - feed_T) / 1e6
    vapor_GJ = reactor_NH3_in_kmol * _p("process.NH3_latent_heat_kJ_per_mol") / 1000.0
    gas_sensible_GJ = reactor_NH3_in_kmol * _p("process.gas_Cp_kJ_per_kmolK") * max(0.0, T - 298.15) / 1e6
    recoverable_GJ = (reaction_heat_GJ + gas_sensible_GJ) * _p("process.recuperator_effectiveness")
    trim_preheat_GJ = max(0.0, sensible_liquid_GJ + vapor_GJ + gas_sensible_GJ - recoverable_GJ)
    furnace_heat_GJ = (reaction_heat_GJ + trim_preheat_GJ) * (1.0 + _p("process.heat_loss_fraction"))
    furnace_electric_GJ = furnace_heat_GJ / _p("process.electric_heater_efficiency")

    fresh_NH3_t = fresh_NH3_kmol * MW["NH3"] / 1000.0
    recycle_NH3_t = recovered_NH3_kmol * MW["NH3"] / 1000.0
    pump1_e_GJ = fresh_NH3_t * _p("process.fresh_feed_pump_specific_kWh_per_t_NH3") * 0.0036
    pump9_e_GJ = recycle_NH3_t * _p("process.recycle_pump_specific_kWh_per_t_NH3") * 0.0036
    psa_e_GJ = _p("process.PSA_specific_electricity_kWh_per_kg_H2") * 1000.0 * 0.0036
    Pin = max(1.01, P - _p("process.loop_pressure_drop_bar"))
    Pout = _p("basis.product.H2.P_bar")
    compressor_kJ_per_kmol = 8.314462618 * _p("process.compressor_inlet_T_K") * math.log(max(Pout / Pin, 1.0)) / _p("process.compressor_isentropic_efficiency")
    compressor_e_GJ = product_H2_kmol * compressor_kJ_per_kmol / 1e6
    condenser_heat_GJ = max(0.0, (reactor_NH3_in_kmol + gross_H2_kmol + N2_kmol) * _p("process.gas_Cp_kJ_per_kmolK") * max(T - _p("basis.utilities.cooling_water_return_temperature"), 0.0) / 1e6 + recovered_NH3_kmol * _p("process.NH3_latent_heat_kJ_per_mol") / 1000.0)
    cooling_e_GJ = condenser_heat_GJ * _p("process.cooling_electricity_fraction")

    electric_by_unit = {
        "U1 Fresh ammonia pump": pump1_e_GJ,
        "U2 Feed-recycle mixer": 0.0,
        "U3 Feed-effluent recuperator": 0.0,
        "U4 Ammonia vaporizer and trim heater": 0.0,
        "U5 Electric reaction furnace": furnace_electric_GJ,
        "U6 Packed-bed ammonia decomposition reactor": 0.0,
        "U7 Ammonia condenser": 0.0,
        "U8 Ammonia knockout drum": 0.0,
        "U9 Ammonia recycle pump": pump9_e_GJ,
        "U10 Hydrogen PSA": psa_e_GJ,
        "U11 Hydrogen product compressor": compressor_e_GJ,
        "U12 Utilities and offsites": cooling_e_GJ,
    }
    primary_factor = _p("basis.utilities.electricity_primary_energy_factor")

    ref_capex = _capital_reference()
    cap_scale = (capacity / _p("capex.reference_capacity_t_per_y")) ** _p("capex.scale_exponent")
    ref_x = _p("capex.reference_per_pass_conversion")
    ref_fresh_t = ((2.0 / 3.0) * (1000.0 / MW["H2"])) * MW["NH3"] / 1000.0
    loop_ratio = (reactor_NH3_in_kmol / max(productive_NH3_kmol / ref_x, 1e-12))
    fresh_ratio = fresh_NH3_t / max(ref_fresh_t, 1e-12)
    ref_cat_mass = gross_H2_kg_h / _p("capex.reference_catalyst_productivity_kg_per_kg_h")
    cat_ratio = catalyst_mass_kg / max(ref_cat_mass, 1e-12)
    heat_ratio = furnace_electric_GJ / 45.0
    cool_ratio = condenser_heat_GJ / 20.0
    comp_ratio = compressor_e_GJ / 9.0
    loads = {
        "U1 Fresh ammonia pump": fresh_ratio,
        "U2 Feed-recycle mixer": loop_ratio,
        "U3 Feed-effluent recuperator": loop_ratio,
        "U4 Ammonia vaporizer and trim heater": loop_ratio,
        "U5 Electric reaction furnace": heat_ratio,
        "U6 Packed-bed ammonia decomposition reactor": cat_ratio ** _p("capex.reactor_activity_exponent"),
        "U7 Ammonia condenser": cool_ratio,
        "U8 Ammonia knockout drum": loop_ratio,
        "U9 Ammonia recycle pump": max(recycle_NH3_t / max(ref_fresh_t * (1.0 / ref_x - 1.0), 1e-12), 0.0),
        "U10 Hydrogen PSA": 1.0,
        "U11 Hydrogen product compressor": comp_ratio,
        "U12 Utilities and offsites": 1.0,
    }
    unit_capex = {}
    for name in UNIT_NAMES:
        load = max(_p("capex.minimum_load_fraction"), loads[name])
        unit_capex[name] = ref_capex * _p("capex.fraction." + name) * cap_scale * load ** _p("capex.scale_exponent")
    furnace_kW = furnace_electric_GJ * capacity / hours / 0.0036
    unit_capex["U5 Electric reaction furnace"] = max(unit_capex["U5 Electric reaction furnace"], furnace_kW * _p("capex.furnace_min_usd_per_kW"))
    total_capex = sum(unit_capex.values())

    units = []
    def base_unit(name, typ):
        return {"name": name, "type": typ, "purchased_energy_GJ_per_t": electric_by_unit[name] * primary_factor, "electricity_GJ_per_t": electric_by_unit[name], "internal_fuel_GJ_per_t": 0.0, "capex_usd": unit_capex[name]}
    units.append(base_unit("U1 Fresh ammonia pump", "pump"))
    units.append(base_unit("U2 Feed-recycle mixer", "other"))
    u = base_unit("U3 Feed-effluent recuperator", "heat_exchanger"); u["recovered_heat_GJ_per_t"] = min(recoverable_GJ, sensible_liquid_GJ + vapor_GJ + gas_sensible_GJ); units.append(u)
    u = base_unit("U4 Ammonia vaporizer and trim heater", "heat_exchanger"); u["heat_duty_GJ_per_t"] = trim_preheat_GJ; units.append(u)
    u = base_unit("U5 Electric reaction furnace", "furnace"); u["heat_duty_GJ_per_t"] = furnace_heat_GJ; units.append(u)
    u = base_unit("U6 Packed-bed ammonia decomposition reactor", "reactor"); reactor_out_total = unconverted_NH3_kmol + nonselective_NH3_kmol + gross_H2_kmol + N2_kmol; u.update({"T_K": T, "P_bar": P, "heat_duty_GJ_per_t": reaction_heat_GJ, "catalyst_mass_kg": catalyst_mass_kg, "catalyst_bed_volume_m3": catalyst_mass_kg / _p("catalyst.bulk_density_kg_per_m3"), "effective_productivity_kg_H2_per_kgcat_h": rate, "replacement_cycle_h": tcycle, "annual_replacements": hours / tcycle, "feed_kmol_per_t": reactor_NH3_in_kmol, "outlet": {"kmol_per_t": reactor_out_total, "mol_frac": {"NH3": (unconverted_NH3_kmol + nonselective_NH3_kmol)/reactor_out_total, "H2": gross_H2_kmol/reactor_out_total, "N2": N2_kmol/reactor_out_total}}}); units.append(u)
    u = base_unit("U7 Ammonia condenser", "heat_exchanger"); u["heat_duty_GJ_per_t"] = -condenser_heat_GJ; units.append(u)
    u = base_unit("U8 Ammonia knockout drum", "knockout"); u["cooling_duty_GJ_per_t"] = condenser_heat_GJ; units.append(u)
    units.append(base_unit("U9 Ammonia recycle pump", "pump"))
    psa_feed = {"kmol_per_t": gross_H2_kmol + N2_kmol + NH3_out_kmol, "mol_frac": {"H2": gross_H2_kmol / (gross_H2_kmol + N2_kmol + NH3_out_kmol), "N2": N2_kmol / (gross_H2_kmol + N2_kmol + NH3_out_kmol), "NH3": NH3_out_kmol / (gross_H2_kmol + N2_kmol + NH3_out_kmol)}}
    psa_out_product = {"kmol_per_t": product_H2_kmol, "mol_frac": {"H2": 1.0}}
    tail_total = tail_H2_kmol + N2_kmol + NH3_out_kmol
    psa_out_tail = {"kmol_per_t": tail_total, "mol_frac": {"H2": tail_H2_kmol / tail_total, "N2": N2_kmol / tail_total, "NH3": NH3_out_kmol / tail_total}}
    u = base_unit("U10 Hydrogen PSA", "separation"); u.update({"feed": psa_feed, "outlets": [psa_out_product, psa_out_tail], "recovered_heat_GJ_per_t": 0.0}); units.append(u)
    u = base_unit("U11 Hydrogen product compressor", "compressor"); u.update({"kmol_per_t": product_H2_kmol, "T_in_K": _p("process.compressor_inlet_T_K"), "P_in_bar": Pin, "P_out_bar": Pout, "power_GJ_per_t": compressor_e_GJ}); units.append(u)
    units.append(base_unit("U12 Utilities and offsites", "offsites"))

    total_electric_GJ = sum(electric_by_unit.values())
    purchased_primary_GJ = total_electric_GJ * primary_factor
    feed_cost = fresh_NH3_t / _p("basis.feeds.NH3.purity_mol_frac") * _p("price.ammonia")
    energy_cost = total_electric_GJ / 3.6 * _p("price.electricity")
    capital_cost = total_capex * _p("price.capital_recovery_factor") / capacity
    catalyst_cost = annual_cat / capacity
    other_cost = total_capex * _p("price.fixed_om_fraction_of_capex") / capacity
    parts = {"feed": feed_cost, "energy": energy_cost, "capital": capital_cost, "catalyst": catalyst_cost, "other": other_cost}
    total_cost = sum(parts.values())
    boundary_in = {"NH3": fresh_NH3_t}
    boundary_out = {"H2": gross_H2_kmol * MW["H2"] / 1000.0, "N2": N2_kmol * MW["N2"] / 1000.0, "NH3": NH3_out_kmol * MW["NH3"] / 1000.0}
    return {
        "cost_usd_per_t": total_cost,
        "parts": parts,
        "operating": {"T_K": T, "P_bar": P, "per_pass_conversion": x},
        "balances": {"key_feed_t_per_t": reactor_NH3_in_kmol * MW["NH3"] / 1000.0, "energy_GJ_per_t": purchased_primary_GJ, "capex_usd": total_capex, "capacity_t_per_y": capacity},
        "physics": {
            "reactor": {"T_K": T, "P_bar": P, "feed_mol_frac": {"NH3": 1.0, "N2": 0.0, "H2": 0.0}, "per_pass_conversion": x, "heat_duty_GJ_per_t": reaction_heat_GJ},
            "boundary": {"in_t_per_t": boundary_in, "out_t_per_t": boundary_out},
            "units": units,
        },
        "diagnostics": {"equilibrium_conversion": _equilibrium_conversion(T, P), "net_productivity": rate, "catalyst_mass_kg": catalyst_mass_kg, "catalyst_price_usd_per_kg": cat_price}
    }


def plant_cost(rec):
    T = min(max(_finite(rec.get("T_K"), 773.15), 450.0), 1100.0)
    P = _p("process.reactor_pressure_bar")
    xeq = _equilibrium_conversion(T, P)
    xmax = min(_p("process.maximum_absolute_per_pass_conversion"), xeq * _p("process.maximum_per_pass_conversion_fraction_of_equilibrium"), max(0.0005, _finite(rec.get("X"), 0.1)))
    xmin_nom = _p("process.minimum_per_pass_conversion")
    xmin = min(xmin_nom, max(0.001, 0.45 * xmax))
    if xmax <= xmin * 1.001:
        x = max(0.0005, min(0.999, 0.8 * xmax))
        return _evaluate(rec, x)
    def obj(z):
        try:
            v = _evaluate(rec, float(z))["cost_usd_per_t"]
            return v if np.isfinite(v) else 1e30
        except Exception:
            return 1e30
    opt = minimize_scalar(obj, bounds=(xmin, xmax), method="bounded", options={"xatol": 1e-5, "maxiter": 120})
    candidates = [xmin, xmax, float(opt.x)]
    vals = [(obj(z), z) for z in candidates]
    x = min(vals, key=lambda a: a[0])[1]
    return _evaluate(rec, x)


def reference():
    rec = {"T_K": 823.15, "P_bar": 1.0, "X": 0.666, "S": 1.0, "r": 1.180086,
           "y_key": 1.0, "y_cofeed": 0.0, "t_cycle_h": None,
           "components": [["Ni", 9.0]], "catalyst": "9 wt% Ni/Sm2O3 literature reference"}
    out = plant_cost(rec)
    out["name"] = "Central ammonia cracking reference using a published Ni/Sm2O3 operating point"
    out["record"] = rec
    return out
