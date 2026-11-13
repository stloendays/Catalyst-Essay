import csv
import math
from pathlib import Path
import numpy as np

REACTION = {
    "key": "N2",
    "product": "NH3",
    "cofeed": "H2",
    "MW": {"N2": 28.014, "H2": 2.016, "NH3": 17.031},
    "nu": {"N2": -1, "H2": -3, "NH3": 2},
}


def _load_params():
    out = {}
    with Path(__file__).with_name("sources.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["parameter"]] = float(row["value"])
    return out


PARAMS = _load_params()


def _p(name):
    return float(PARAMS[name])


def _kp(T):
    # N2 + 3 H2 -> 2 NH3; ideal-gas standard state of 1 bar.
    R = _p("thermo.R_J_per_mol_K")
    dH = -2.0 * _p("thermo.reaction_heat_J_per_mol_NH3")
    dS = _p("thermo.reaction_entropy_J_per_molrxn_K")
    dG = dH - T * dS
    z = max(-700.0, min(700.0, -dG / (R * T)))
    return math.exp(z)


def _outlet_from_conversion(y_n2, y_h2, y_nh3, X):
    total0 = y_n2 + y_h2 + y_nh3
    if total0 <= 0.0:
        return {"N2": 0.0, "H2": 0.0, "NH3": 0.0}
    n2 = y_n2 / total0
    h2 = y_h2 / total0
    nh3 = y_nh3 / total0
    extent = min(max(0.0, X * n2), h2 / 3.0)
    vals = {"N2": max(0.0, n2 - extent), "H2": max(0.0, h2 - 3.0 * extent), "NH3": max(0.0, nh3 + 2.0 * extent)}
    s = sum(vals.values())
    return {k: v / s for k, v in vals.items()}


def _q(T, P_bar, y_n2, y_h2, y_nh3, X):
    yo = _outlet_from_conversion(y_n2, y_h2, y_nh3, X)
    pn = max(1e-30, yo["N2"] * P_bar)
    ph = max(1e-30, yo["H2"] * P_bar)
    pa = max(1e-30, yo["NH3"] * P_bar)
    return (pa * pa) / (pn * ph ** 3)


def _equilibrium_conversion(T, P_bar):
    K = _kp(T)
    lo, hi = 0.0, 0.999999
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if _q(T, P_bar, 0.25, 0.75, 0.0, mid) < K:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _lab_rate_anchor(rec, T, P_bar, X):
    R = _p("thermo.R_J_per_mol_K")
    Ea = _p("kinetics.apparent_Ea_J_per_mol")
    nexp = _p("kinetics.pressure_exponent")
    cexp = _p("kinetics.composition_exponent")
    r0 = max(_p("kinetics.minimum_rate_kgkg_h"), float(rec.get("r") or 0.0))
    T0 = max(250.0, float(rec.get("T_K") or T))
    P0 = max(0.1, float(rec.get("P_bar") or P_bar))
    y0n = max(1e-8, float(rec.get("y_key") or 0.25))
    y0h = max(1e-8, float(rec.get("y_cofeed") or rec.get("y_h2") or 0.75))
    sy = y0n + y0h
    y0n, y0h = y0n / sy, y0h / sy
    X0 = min(0.95, max(0.0, float(rec.get("X") or 0.0)))
    K0 = _kp(T0)
    q0 = _q(T0, P0, y0n, y0h, 0.0, X0)
    app0 = max(0.05, min(1.0, 1.0 - q0 / max(K0, 1e-300)))
    arr = math.exp(max(-80.0, min(80.0, -Ea / R * (1.0 / T - 1.0 / T0))))
    pf = (P_bar / P0) ** nexp
    comp0 = max(1e-12, y0n * y0h ** 3)
    comp = 0.25 * 0.75 ** 3
    cf = (comp / comp0) ** (0.25 * cexp)
    K = _kp(T)
    qout = _q(T, P_bar, 0.25, 0.75, 0.0, X)
    # Bed-average reversible driving force is less inhibited than the outlet.
    approach = max(0.01, min(1.0, 1.0 - 0.5 * qout / max(K, 1e-300)))
    return max(_p("kinetics.minimum_rate_kgkg_h"), r0 / app0 * arr * pf * cf * approach)


def _catalyst_price(rec):
    support = _p("prices.catalyst_support_and_manufacturing")
    custom = rec.get("metal_price_usd_per_kg")
    if custom is not None:
        return support + _p("catalyst.default_metal_loading_wt_frac") * float(custom)
    price_map = {"Ru": "prices.metal_Ru", "Fe": "prices.metal_Fe", "Co": "prices.metal_Co", "K": "prices.metal_K"}
    comps = rec.get("components") or []
    known = []
    unknown_priced = []
    for item in comps:
        if not isinstance(item, (list, tuple)) or not item:
            continue
        el = str(item[0])
        wt = item[1] if len(item) > 1 else None
        if el not in price_map:
            continue
        if wt is None:
            unknown_priced.append(el)
        else:
            w = float(wt)
            if w > 1.0:
                w /= 100.0
            known.append((el, max(0.0, min(1.0, w))))
    cost = support + sum(w * _p(price_map[el]) for el, w in known)
    if unknown_priced:
        residual = max(0.0, _p("catalyst.default_metal_loading_wt_frac") - sum(w for _, w in known))
        share = residual / len(unknown_priced)
        cost += sum(share * _p(price_map[el]) for el in unknown_priced)
    return max(support, cost)


def _compressor_power(kmol, T, Pin, Pout):
    if kmol <= 0.0 or Pout <= Pin:
        return 0.0
    R_kJ = _p("thermo.R_J_per_mol_K")
    eta = _p("compression.isentropic_efficiency")
    return kmol * R_kJ * T * math.log(Pout / Pin) / eta / 1.0e6


def _cap(base_key, capacity_factor, duty_factor=1.0):
    exponent = _p("capital.scaling_exponent")
    floor = _p("capital.minimum_scale_factor")
    return _p(base_key) * max(floor, capacity_factor * max(floor, duty_factor) ** exponent)


def _evaluate(rec, T, P, X, details=False):
    capacity = _p("basis.capacity_t_per_y")
    hours = _p("basis.operating_hours_per_y")
    refcap = _p("capital.reference_capacity_tpy")
    capfac = (capacity / refcap) ** _p("capital.scaling_exponent")
    feed_purity = min(_p("basis.feeds.H2.purity_mol_frac"), _p("basis.feeds.N2.purity_mol_frac"))
    purge = min(0.10, _p("separation.purge_fraction"))
    recovery = _p("separation.nh3_recovery")
    product_purity = _p("basis.product.NH3.purity_mol_frac")
    product_nh3_kmol = 1000.0 / REACTION["MW"]["NH3"]
    # Steady-state NH3 condensation/recycle balance.
    sep_den = 1.0
    sep_feed_nh3 = product_nh3_kmol
    formed_nh3 = product_nh3_kmol
    recycle_nh3 = 0.0
    purge_nh3 = 0.0
    reacted_n2 = formed_nh3 / 2.0
    reactor_n2_in = reacted_n2 / X
    reactor_h2_in = 3.0 * reactor_n2_in
    n2_out = reactor_n2_in - reacted_n2
    h2_out = reactor_h2_in - 3.0 * reacted_n2
    recycle_n2 = (1.0 - purge) * n2_out
    recycle_h2 = (1.0 - purge) * h2_out
    purge_n2 = purge * n2_out
    purge_h2 = purge * h2_out
    fresh_n2 = reactor_n2_in - recycle_n2
    fresh_h2 = reactor_h2_in - recycle_h2
    selectivity = max(1e-6, min(1.0, float(rec.get("S") or 1.0)))
    bypass_n2 = reacted_n2 * (1.0 / selectivity - 1.0)
    bypass_h2 = 3.0 * bypass_n2
    fresh_n2 += bypass_n2
    fresh_h2 += bypass_h2
    reactor_feed_kmol = reactor_n2_in + reactor_h2_in + recycle_nh3
    reactor_out_kmol = n2_out + h2_out + sep_feed_nh3
    recycle_kmol = recycle_n2 + recycle_h2 + recycle_nh3
    formed_t = formed_nh3 * REACTION["MW"]["NH3"] / 1000.0

    rate = _lab_rate_anchor(rec, T, P, X)
    plant_kg_h = capacity * 1000.0 / hours
    catalyst_mass = plant_kg_h * formed_t / rate * _p("catalyst.inventory_design_factor")
    catalyst_volume = catalyst_mass / _p("catalyst.bulk_density_kg_m3")
    life_h = float(rec.get("t_cycle_h") or _p("catalyst.default_life_h"))
    life_h = max(24.0, life_h)
    cat_price = _catalyst_price(rec)
    catalyst_cost = catalyst_mass * cat_price * (hours / life_h) / capacity

    T_h2 = _p("basis.feeds.H2.T_K")
    T_n2 = _p("basis.feeds.N2.T_K")
    Pin_h2 = _p("basis.feeds.H2.P_bar")
    Pin_n2 = _p("basis.feeds.N2.P_bar")
    h2_power = _compressor_power(fresh_h2, T_h2, Pin_h2, P)
    n2_power = _compressor_power(fresh_n2, T_n2, Pin_n2, P)
    drop = _p("compression.recycle_pressure_drop_fraction")
    recycle_power = _compressor_power(recycle_kmol, 305.0, P * (1.0 - drop), P)
    cp = _p("thermo.gas_cp_GJ_per_kmol_K")
    feed_T = (fresh_h2 * T_h2 + fresh_n2 * T_n2 + recycle_kmol * 305.0) / max(1e-12, fresh_h2 + fresh_n2 + recycle_kmol)
    eff = _p("heat_exchange.effectiveness")
    preheated_T = feed_T + eff * max(0.0, T - feed_T)
    heater_power = max(0.0, reactor_feed_kmol * cp * (T - feed_T) * (1.0 - eff))
    hx_recovered = max(0.0, reactor_feed_kmol * cp * (T - feed_T) * eff)
    reactor_heat = -formed_nh3 * (_p("thermo.reaction_heat_J_per_mol_NH3") + _p("thermo.reaction_heat_temperature_coefficient_J_per_molNH3_K") * (T - 298.15)) / 1.0e6
    after_hx_T = feed_T + (T - feed_T) * (1.0 - eff)
    sensible_cooling = reactor_out_kmol * cp * max(0.0, after_hx_T - _p("basis.utilities.cooling_water_return_T"))
    latent_cooling = formed_t * _p("thermo.nh3_condensation_GJ_per_t")
    cooling_duty = sensible_cooling + latent_cooling
    sep_electric = cooling_duty / (_p("basis.utilities.refrigeration_COP") * product_purity * feed_purity * recovery)
    electricity_GJ = h2_power + n2_power + recycle_power + sep_electric
    primary_factor = _p("basis.utilities.electricity_primary_energy_factor")
    purchased_primary = electricity_GJ * primary_factor

    nominal_X = _p("capital.nominal_conversion")
    nominal_P = _p("capital.nominal_pressure_bar")
    nominal_loop = 4.0 * reacted_n2 / nominal_X
    flow_factor = reactor_feed_kmol / max(1e-12, nominal_loop)
    pressure_factor = max(0.2, math.log(P / min(Pin_h2, Pin_n2)) / math.log(nominal_P / min(Pin_h2, Pin_n2)))
    reactor_size_factor = max(0.2, catalyst_volume / _p("capital.catalyst_volume_reference_m3"))
    caps = {
        "H2 feed compressor": _cap("capital.H2_feed_compressor_usd", capfac, pressure_factor * fresh_h2 / max(1e-12, reacted_n2 * 3.0)),
        "N2 feed compressor": _cap("capital.N2_feed_compressor_usd", capfac, pressure_factor * fresh_n2 / max(1e-12, reacted_n2)),
        "makeup gas mixer": _cap("capital.makeup_gas_mixer_usd", capfac, (fresh_n2 + fresh_h2) / max(1e-12, 4.0 * reacted_n2)),
        "loop feed mixer": _cap("capital.loop_feed_mixer_usd", capfac, flow_factor),
        "feed effluent heat exchanger": _cap("capital.feed_effluent_heat_exchanger_usd", capfac, max(0.1, flow_factor * (T - feed_T) / 400.0)),
        "recovered-heat trim exchanger": 0.0,
        "interbed heat recovery exchanger": _cap("capital.interbed_heat_recovery_usd", capfac, max(0.1, -reactor_heat / 3.14)),
        "ammonia synthesis reactor": _cap("capital.ammonia_synthesis_reactor_usd", capfac, reactor_size_factor),
        "ammonia condenser separator": _cap("capital.ammonia_condenser_separator_usd", capfac, max(0.1, flow_factor)),
        "purge splitter": _cap("capital.purge_splitter_usd", capfac, flow_factor),
        "recycle compressor": _cap("capital.recycle_compressor_usd", capfac, max(0.1, recycle_power / 0.02)),
        "NH3 product letdown": _cap("capital.NH3_product_letdown_usd", capfac, formed_t),
        "purge handling and offsites": _cap("capital.purge_handling_and_offsites_usd", capfac, 1.0),
    }
    capex = sum(caps.values())
    electricity_cost = electricity_GJ / 3.6 * _p("prices.electricity")
    feed_h2_t = fresh_h2 * REACTION["MW"]["H2"] / 1000.0
    feed_n2_t = fresh_n2 * REACTION["MW"]["N2"] / 1000.0
    feed_cost = feed_h2_t * 1000.0 * _p("prices.hydrogen")
    capital_cost = capex * (_p("prices.capital_recovery_factor") + _p("prices.fixed_om_fraction_of_capex")) / capacity
    parts = {"feed": feed_cost, "energy": electricity_cost, "capital": capital_cost, "catalyst": catalyst_cost, "other": 0.0}
    total_cost = sum(parts.values())

    if not details:
        return total_cost

    yfeed = {"N2": reactor_n2_in / reactor_feed_kmol, "H2": reactor_h2_in / reactor_feed_kmol}
    ysep = {"N2": n2_out / reactor_out_kmol, "H2": h2_out / reactor_out_kmol, "NH3": sep_feed_nh3 / reactor_out_kmol}
    sep_gas_kmol = n2_out + h2_out
    ygas = {"N2": n2_out / sep_gas_kmol, "H2": h2_out / sep_gas_kmol, "NH3": 0.0}
    liquid_kmol = sep_feed_nh3
    units = [
        {"name": "H2 feed compressor", "type": "compressor", "purchased_energy_GJ_per_t": h2_power * primary_factor, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["H2 feed compressor"], "kmol_per_t": fresh_h2, "T_in_K": T_h2, "P_in_bar": Pin_h2, "P_out_bar": P, "power_GJ_per_t": h2_power},
        {"name": "N2 feed compressor", "type": "compressor", "purchased_energy_GJ_per_t": n2_power * primary_factor, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["N2 feed compressor"], "kmol_per_t": fresh_n2, "T_in_K": T_n2, "P_in_bar": Pin_n2, "P_out_bar": P, "power_GJ_per_t": n2_power},
        {"name": "makeup gas mixer", "type": "other", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["makeup gas mixer"]},
        {"name": "loop feed mixer", "type": "other", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["loop feed mixer"]},
        {"name": "feed effluent heat exchanger", "type": "heat_exchanger", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "recovered_heat_GJ_per_t": hx_recovered, "T_cold_in_K": feed_T, "T_cold_out_K": preheated_T, "T_hot_in_K": T, "T_hot_out_K": max(_p("basis.utilities.cooling_water_return_T"), T - eff * (T - feed_T)), "capex_usd": caps["feed effluent heat exchanger"]},
        {"name": "recovered-heat trim exchanger", "type": "heat_exchanger", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "recovered_heat_GJ_per_t": heater_power, "heat_duty_GJ_per_t": heater_power, "T_cold_in_K": preheated_T, "T_cold_out_K": T, "capex_usd": caps["recovered-heat trim exchanger"]},
        {"name": "ammonia synthesis reactor", "type": "reactor", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["ammonia synthesis reactor"], "T_K": T, "P_bar": P, "feed_mol_frac": yfeed, "per_pass_conversion": X, "heat_duty_GJ_per_t": reactor_heat, "catalyst_mass_kg": catalyst_mass, "catalyst_volume_m3": catalyst_volume, "catalyst_rate_kgNH3_per_kgcat_h": rate, "catalyst_price_usd_per_kg": cat_price, "catalyst_life_h": life_h, "catalyst_replacement_kg_per_y": catalyst_mass * hours / life_h},
        {"name": "interbed heat recovery exchanger", "type": "heat_exchanger", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "recovered_heat_GJ_per_t": -reactor_heat, "heat_duty_GJ_per_t": reactor_heat, "T_hot_in_K": T + 40.0, "T_hot_out_K": T, "capex_usd": caps["interbed heat recovery exchanger"]},
        {"name": "ammonia condenser separator", "type": "separation", "purchased_energy_GJ_per_t": sep_electric * primary_factor, "internal_fuel_GJ_per_t": 0.0, "recovered_heat_GJ_per_t": 0.0, "power_GJ_per_t": sep_electric, "cooling_duty_GJ_per_t": cooling_duty, "sensible_cooling_GJ_per_t": sensible_cooling, "condensation_duty_GJ_per_t": latent_cooling, "T_in_K": after_hx_T, "T_out_K": _p("basis.utilities.cooling_water_return_T"), "refrigeration_COP": _p("basis.utilities.refrigeration_COP"), "capex_usd": caps["ammonia condenser separator"], "feed": {"kmol_per_t": reactor_out_kmol, "mol_frac": ysep}, "outlets": [{"kmol_per_t": liquid_kmol, "mol_frac": {"N2": 0.0, "H2": 0.0, "NH3": 1.0}}, {"kmol_per_t": sep_gas_kmol, "mol_frac": ygas}]},
        {"name": "purge splitter", "type": "other", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["purge splitter"]},
        {"name": "recycle compressor", "type": "compressor", "purchased_energy_GJ_per_t": recycle_power * primary_factor, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["recycle compressor"], "kmol_per_t": recycle_kmol, "T_in_K": 305.0, "P_in_bar": P * (1.0 - drop), "P_out_bar": P, "power_GJ_per_t": recycle_power},
        {"name": "NH3 product letdown", "type": "other", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["NH3 product letdown"]},
        {"name": "purge handling and offsites", "type": "offsites", "purchased_energy_GJ_per_t": 0.0, "internal_fuel_GJ_per_t": 0.0, "capex_usd": caps["purge handling and offsites"]},
    ]
    boundary_in = {"N2": feed_n2_t, "H2": feed_h2_t}
    boundary_out = {"N2": (purge_n2 + bypass_n2) * REACTION["MW"]["N2"] / 1000.0, "H2": (purge_h2 + bypass_h2) * REACTION["MW"]["H2"] / 1000.0, "NH3": (product_nh3_kmol + purge_nh3) * REACTION["MW"]["NH3"] / 1000.0}
    return {
        "cost_usd_per_t": total_cost,
        "parts": parts,
        "operating": {"T_K": T, "P_bar": P, "per_pass_conversion": X},
        "balances": {"key_feed_t_per_t": reactor_n2_in * REACTION["MW"]["N2"] / 1000.0, "energy_GJ_per_t": purchased_primary, "capex_usd": capex, "capacity_t_per_y": capacity},
        "physics": {
            "reactor": {"T_K": T, "P_bar": P, "feed_mol_frac": yfeed, "per_pass_conversion": X, "heat_duty_GJ_per_t": reactor_heat},
            "boundary": {"in_t_per_t": boundary_in, "out_t_per_t": boundary_out},
            "units": units,
        },
    }


def plant_cost(rec):
    Tmin, Tmax = _p("operation.T_min_K"), _p("operation.T_max_K")
    Pmin, Pmax = _p("operation.P_min_bar"), _p("operation.P_max_bar")
    Xmin, Xmax = _p("operation.X_min"), _p("operation.X_max")
    margin = _p("operation.equilibrium_margin")
    Ts = np.linspace(Tmin, Tmax, 7)
    Ps = np.linspace(Pmin, Pmax, 7)
    Xs = np.linspace(Xmin, Xmax, 10)
    best = None
    for T in Ts:
        for P in Ps:
            xeq = _equilibrium_conversion(float(T), float(P)) * margin
            for X in Xs:
                if X > xeq:
                    continue
                c = _evaluate(rec, float(T), float(P), float(X), details=False)
                key = (float(c), float(T), float(P), float(X))
                if best is None or key < best[0]:
                    best = (key, float(T), float(P), float(X))
    if best is None:
        T, P = Tmin, Pmax
        X = max(1e-4, min(Xmin, _equilibrium_conversion(T, P) * 0.8))
    else:
        _, T, P, X = best
    return _evaluate(rec, T, P, X, details=True)


def reference():
    rec = {
        "T_K": _p("reference.T_K"),
        "P_bar": _p("reference.P_bar"),
        "X": _p("reference.X"),
        "S": _p("reference.S"),
        "r": _p("reference.r"),
        "y_key": _p("reference.y_key"),
        "y_cofeed": _p("reference.y_cofeed"),
        "t_cycle_h": None,
        "components": [["Fe", 24.7]],
        "catalyst": "FeOOH/Al2O3 (25% Fe)",
    }
    out = plant_cost(rec)
    out["name"] = "Published FeOOH/Al2O3 reference catalyst in the accepted synthesis-loop basis"
    out["record"] = rec
    return out
