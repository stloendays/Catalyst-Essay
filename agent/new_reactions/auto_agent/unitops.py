"""Generic unit-operation library for AI-built plant models (library UO-1.1, 2026-11-14; UO-1.0 shipped with build mode V3.3,
UO-1.1 with V3.3.1). Fixed infrastructure, like mkm_solver.py: it holds
no reaction, catalyst or plant data and makes no design choice. It turns the agent's design decisions into energy numbers that
are consistent with the physics gate, because it uses the same NIST thermodynamic data (physics_gate.species_thermo).

Basis: per tonne of main product. Streams are {formula: kmol per t product}. Energies are GJ per t product.
Design references: Douglas, Conceptual Design of Chemical Processes (1988) for the recycle/purge and separation balances;
Smith, Chemical Process Design and Integration (2016) for compression staging and fired-heater efficiency; IDAES unit-model
library (Lee et al. 2021) for the unit-by-unit balance structure. Physical data sources are given next to each table.

Import in model.py:  from unitops import compressor, sensible_heat, latent_heat, fired_heater, stream_lhv, recycle_loop, ...
"""
from __future__ import annotations

import math

from physics_gate import R, formula_mw, reaction_dH, species_thermo, equilibrium_conversion  # noqa: F401  (re-exported)

# Lower heating values, MJ/kg, 298 K, gas-phase products (Engineering ToolBox / NIST combustion enthalpies; NH3: 18.6 MJ/kg).
LHV_MJ_PER_KG = {"H2": 120.0, "CH4": 50.0, "CO": 10.1, "NH3": 18.6, "C2H6": 47.5, "C2H4": 47.2, "C3H8": 46.4, "C3H6": 45.8,
                 "CH3OH": 19.9, "C2H5OH": 26.8}
# Enthalpy of vaporisation, kJ/mol, at the normal boiling point unless noted (CRC Handbook of Chemistry and Physics, 6-x tables).
LATENT_KJ_PER_MOL = {"H2O": 40.65, "NH3": 23.33, "CH3OH": 35.21, "C2H5OH": 38.56, "C3H8": 19.04, "C3H6": 18.42,
                     "CO2": 15.33}   # CO2: sublimation-free liquid near the triple point, used only for liquefaction duties
GAMMA_DEFAULT = 1.4


def _kmol(stream):
    if not isinstance(stream, dict) or not stream:
        raise ValueError("stream must be a non-empty {formula: kmol per t product} dict")
    for s, v in stream.items():
        if v is None or v < 0:
            raise ValueError(f"negative or missing flow for {s}")
    return stream


def sensible_heat(stream, T_in_K, T_out_K):
    """Heat to take an ideal-gas stream from T_in to T_out, GJ per t (positive = heat added). NIST Shomate enthalpies."""
    _kmol(stream)
    return sum(n * (species_thermo(s, T_out_K)[0] - species_thermo(s, T_in_K)[0]) for s, n in stream.items()) * 1e3 / 1e9


def latent_heat(species, kmol_per_t):
    """Heat to vaporise kmol_per_t of a condensable species, GJ per t (constant enthalpy of vaporisation)."""
    if species not in LATENT_KJ_PER_MOL:
        raise ValueError(f"no enthalpy of vaporisation for {species}")
    return kmol_per_t * LATENT_KJ_PER_MOL[species] * 1e3 * 1e3 / 1e9


def reaction_heat(nu, extent_kmol_per_t, T_K):
    """Reaction heat for extent_kmol_per_t of the reaction as written, GJ per t (negative = exothermic, heat released)."""
    return reaction_dH(nu, T_K) * extent_kmol_per_t * 1e3 / 1e9


def isothermal_work(kmol_per_t, T_in_K, P_in_bar, P_out_bar):
    """Reversible isothermal compression work, GJ per t (the physics gate's lower bound)."""
    return kmol_per_t * 1e3 * R * T_in_K * math.log(P_out_bar / P_in_bar) / 1e9


def compressor(kmol_per_t, T_in_K, P_in_bar, P_out_bar, eta_isentropic=0.75, max_stage_ratio=3.5, intercool_T_K=313.15,
               gamma=GAMMA_DEFAULT, primary_efficiency=None):
    """Multistage intercooled compressor with equal stage ratios (Smith 2016, ch. 13). Returns physics-unit fields:
    kmol_per_t, T_in_K, P_in_bar, P_out_bar, power_GJ_per_t, stages, T_out_K and, if primary_efficiency is given (for example
    0.38 for grid electricity on a primary basis), purchased_energy_GJ_per_t = power / primary_efficiency; otherwise
    purchased_energy_GJ_per_t = power (shaft work bought as electricity on a final-energy basis)."""
    if P_out_bar <= P_in_bar:
        return dict(kmol_per_t=kmol_per_t, T_in_K=T_in_K, P_in_bar=P_in_bar, P_out_bar=P_out_bar, power_GJ_per_t=0.0, stages=0,
                    T_out_K=T_in_K, purchased_energy_GJ_per_t=0.0, cooling_duty_GJ_per_t=0.0)
    ratio = P_out_bar / P_in_bar
    stages = max(1, math.ceil(math.log(ratio) / math.log(max_stage_ratio)))
    r = ratio ** (1 / stages)
    k = (gamma - 1) / gamma
    power, T, cooling = 0.0, T_in_K, 0.0
    for i in range(stages):
        t_in = T_in_K if i == 0 else intercool_T_K
        w = kmol_per_t * 1e3 * R * t_in / k * (r ** k - 1) / eta_isentropic / 1e9   # GJ per t
        power += w
        T = t_in * (1 + (r ** k - 1) / eta_isentropic)
        if i < stages - 1:
            cooling += kmol_per_t * 1e3 * R / k * (T - intercool_T_K) / 1e9
    purchased = power / primary_efficiency if primary_efficiency else power
    return dict(kmol_per_t=kmol_per_t, T_in_K=T_in_K, P_in_bar=P_in_bar, P_out_bar=P_out_bar, power_GJ_per_t=power,
                stages=stages, T_out_K=T, purchased_energy_GJ_per_t=purchased, cooling_duty_GJ_per_t=cooling)


def pump(kmol_per_t, mw_kg_per_kmol, density_kg_m3, dP_bar, eta=0.70):
    """Liquid pump shaft work, GJ per t (volume flow x pressure rise / efficiency)."""
    volume_m3 = kmol_per_t * mw_kg_per_kmol / density_kg_m3
    return volume_m3 * dP_bar * 1e5 / eta / 1e9


def stream_lhv(stream):
    """Lower heating value of a gas stream (for example a purge or PSA tail gas), GJ per t. Species without an LHV entry
    (N2, CO2, H2O, Ar, ...) contribute nothing."""
    _kmol(stream)
    return sum(n * formula_mw(s) * LHV_MJ_PER_KG[s] for s, n in stream.items() if s in LHV_MJ_PER_KG) / 1e3


def fired_heater(duty_GJ_per_t, internal_fuel_available_GJ_per_t=0.0, efficiency=0.85):
    """Fired heater supplying a process duty. Internal fuel (purge, tail gas, off-gas) is burned first; only the remainder is
    bought (Douglas 1988, level 5; Smith 2016, ch. 15 onion model). Returns physics-unit fields: purchased_energy_GJ_per_t,
    internal_fuel_GJ_per_t, fuel_fired_GJ_per_t, surplus_internal_fuel_GJ_per_t."""
    if duty_GJ_per_t < 0:
        raise ValueError("a fired heater supplies heat: duty must be >= 0")
    fired = duty_GJ_per_t / efficiency
    internal = min(fired, max(0.0, internal_fuel_available_GJ_per_t))
    return dict(purchased_energy_GJ_per_t=fired - internal, internal_fuel_GJ_per_t=internal, fuel_fired_GJ_per_t=fired,
                surplus_internal_fuel_GJ_per_t=max(0.0, internal_fuel_available_GJ_per_t - internal))


def heat_recovery(hot_duty_GJ_per_t, cold_duty_GJ_per_t, approach_fraction=0.85):
    """Feed-effluent or reaction-heat recovery: recoverable heat = approach_fraction x min(hot, cold). Returns
    recovered_heat_GJ_per_t, remaining_cold_duty_GJ_per_t (still to be supplied) and surplus_hot_GJ_per_t (to cooling or steam)."""
    rec = approach_fraction * min(max(hot_duty_GJ_per_t, 0.0), max(cold_duty_GJ_per_t, 0.0))
    return dict(recovered_heat_GJ_per_t=rec, remaining_cold_duty_GJ_per_t=max(cold_duty_GJ_per_t, 0.0) - rec,
                surplus_hot_GJ_per_t=max(hot_duty_GJ_per_t, 0.0) - rec)


def recycle_loop(per_pass_conversion, purge_fraction):
    """Reactor with recycle of unconverted reactant and a purge (fraction of the recycle stream leaving the loop).
    Returns overall_conversion (fresh-feed basis), recycle_ratio (recycle / fresh feed of the key reactant) and
    purge_loss_fraction (key reactant lost in the purge per fresh feed). Douglas 1988, level 3."""
    X, p = per_pass_conversion, purge_fraction
    if not 0 < X <= 1 or not 0 <= p <= 1:
        raise ValueError("per_pass_conversion in (0, 1], purge_fraction in [0, 1]")
    keep = (1 - X) * (1 - p)
    overall = X / (1 - keep)
    return dict(overall_conversion=overall, recycle_ratio=keep / (1 - keep), purge_loss_fraction=(1 - X) * p / (1 - keep))


def split(stream, recovery, product_species):
    """Ideal component split (PSA, membrane, absorber, column): `recovery` of each product species goes to the product, all
    other species and the rest to the tail. recovery is a float or {formula: fraction}. Returns (product, tail) streams."""
    _kmol(stream)
    rec = recovery if isinstance(recovery, dict) else {s: recovery for s in product_species}
    product = {s: n * rec.get(s, 0.0) for s, n in stream.items() if s in product_species}
    tail = {s: n - product.get(s, 0.0) for s, n in stream.items()}
    return product, {s: n for s, n in tail.items() if n > 0}


def mole_fractions(stream):
    total = sum(_kmol(stream).values())
    return {s: n / total for s, n in stream.items()}


def scaled_capex(base_cost_usd, base_capacity, capacity, exponent=0.6, cost_index_base=None, cost_index_now=None):
    """Capacity scaling (six-tenths rule unless a sourced exponent is given) and optional cost-index escalation; the index
    values are cited by the agent (for example CEPCI of the base and target years)."""
    c = base_cost_usd * (capacity / base_capacity) ** exponent
    if cost_index_base and cost_index_now:
        c *= cost_index_now / cost_index_base
    return c


def annual_capital_charge(capex_usd, capital_recovery_factor, fixed_om_fraction):
    """Annual capital charge plus fixed O&M, USD per year (both factors cited from prices.json)."""
    return capex_usd * (capital_recovery_factor + fixed_om_fraction)



# ---------------- UO-1.1 (build mode V3.3.1): utilities, pressure-driven separation and per-unit ledgers
# Cooling utilities from first principles. Wet cooling tower: liquid-to-gas mass ratio about 1 (0.75-1.5) and fan static
# pressure 100-250 Pa; cooling-water circuit pressure rise 2-4 bar; air coolers: air temperature rise 10-20 K (Perry's
# Chemical Engineers' Handbook, 8th ed., sec. 11 air-cooled exchangers and sec. 12 cooling towers). Refrigeration: Carnot
# COP times a second-law efficiency (0.4-0.6 for industrial vapour-compression units; Smith 2016, ch. 24).
CP_WATER = 4184.0      # J/(kg K)
CP_AIR = 1006.0        # J/(kg K)
RHO_AIR = 1.18         # kg/m3 at 298 K, 1 atm


def cooling_utility(duty_GJ_per_t, T_process_out_K, medium="auto", T_ambient_K=298.15, approach_K=10.0, cw_range_K=10.0,
                    cw_pressure_rise_bar=3.0, pump_eta=0.75, tower_air_to_water=1.0, air_dP_Pa=200.0, fan_eta=0.6,
                    air_range_K=15.0, refrigeration_second_law=0.5, primary_efficiency=None):
    """Electricity bought to reject a process cooling duty (GJ per t, positive = heat removed). A cooling duty is not purchased
    energy; only the pump, fan or refrigeration-compressor electricity is. medium: 'cooling_water', 'air', 'refrigeration'
    or 'auto' (cooling water when the process outlet is at least ambient + approach, otherwise refrigeration).
    Returns physics-unit fields: service 'cooling', cooling_medium, cooling_duty_GJ_per_t, electricity_GJ_per_t (final),
    cop (duty / electricity), T_process_out_K and purchased_energy_GJ_per_t (= electricity / primary_efficiency if given)."""
    if duty_GJ_per_t < 0:
        raise ValueError("cooling duty must be >= 0 (heat removed)")
    floor = T_ambient_K + approach_K
    if medium == "auto":
        medium = "cooling_water" if T_process_out_K >= floor else "refrigeration"
    if medium in ("cooling_water", "air") and T_process_out_K < floor - 1e-9:
        raise ValueError(f"{medium} cannot cool below ambient + approach ({floor:.1f} K); use refrigeration")
    J = duty_GJ_per_t * 1e9
    if medium == "cooling_water":
        water_kg = J / (CP_WATER * cw_range_K)
        pump_J = water_kg / 1000.0 * cw_pressure_rise_bar * 1e5 / pump_eta
        fan_J = tower_air_to_water * water_kg / RHO_AIR * air_dP_Pa / fan_eta
        elec = (pump_J + fan_J) / 1e9
    elif medium == "air":
        elec = J / (CP_AIR * air_range_K) / RHO_AIR * air_dP_Pa / fan_eta / 1e9
    elif medium == "refrigeration":
        t_evap, t_cond = T_process_out_K - 5.0, T_ambient_K + approach_K
        cop_r = refrigeration_second_law * t_evap / max(t_cond - t_evap, 1e-6)
        comp = duty_GJ_per_t / cop_r
        elec = comp + cooling_utility(duty_GJ_per_t + comp, t_cond, "cooling_water", T_ambient_K, 0.0, cw_range_K,
                                      cw_pressure_rise_bar, pump_eta, tower_air_to_water, air_dP_Pa, fan_eta)["electricity_GJ_per_t"]
    else:
        raise ValueError("medium must be cooling_water, air, refrigeration or auto")
    purchased = elec / primary_efficiency if primary_efficiency else elec
    return dict(service="cooling", cooling_medium=medium, cooling_duty_GJ_per_t=duty_GJ_per_t, electricity_GJ_per_t=elec,
                cop=duty_GJ_per_t / elec if elec > 0 else math.inf, T_process_out_K=T_process_out_K,
                purchased_energy_GJ_per_t=purchased)


def separator_energy(P_in_bar, outlets, T_K=313.15, eta_isentropic=0.75, primary_efficiency=None):
    """Energy of a pressure-driven separation (membrane, PSA, absorber at pressure) from its stream pressures. Each outlet is
    {"kmol_per_t", "P_out_bar", "P_required_bar"}: the pressure at which it leaves the separator and the pressure the next
    unit or the battery limit needs. Electricity = compression of every outlet whose required pressure is above its outlet
    pressure (recompression, or vacuum pumping when P_out < 1 bar), via compressor(). Outlets leaving below P_in release
    pressure exergy (n R T0 ln(P_in/P_out)), which drives the separation; the physics gate counts it against the mixing
    minimum. A per-volume energy factor from a source whose feed is at a lower pressure already contains feed compression
    and must not be applied to a feed that is already at pressure.
    Returns physics-unit fields: energy_method, P_in_bar, power_GJ_per_t, letdown_exergy_GJ_per_t, outlet_pressures,
    purchased_energy_GJ_per_t (= power / primary_efficiency if given)."""
    power, letdown, pressures = 0.0, 0.0, []
    for o in outlets:
        n, pout = o["kmol_per_t"], o["P_out_bar"]
        preq = o.get("P_required_bar", pout)
        if pout > P_in_bar + 1e-9:
            raise ValueError("an outlet of a pressure-driven separator cannot leave above the feed pressure")
        if preq > pout:
            power += compressor(n, T_K, pout, preq, eta_isentropic=eta_isentropic)["power_GJ_per_t"]
        if pout < P_in_bar:
            letdown += n * 1e3 * R * 298.15 * math.log(P_in_bar / pout) / 1e9
        pressures.append(dict(kmol_per_t=n, P_out_bar=pout, P_required_bar=preq))
    purchased = power / primary_efficiency if primary_efficiency else power
    return dict(energy_method="unitops.separator_energy", P_in_bar=P_in_bar, power_GJ_per_t=power,
                letdown_exergy_GJ_per_t=letdown, outlet_pressures=pressures, purchased_energy_GJ_per_t=purchased)


BOUNDARY_ROLES = ("feed_conditioning", "reaction", "heat_integration", "separation", "recycle", "product_conditioning",
                  "utilities", "offsites")


def energy_ledger(units):
    """Per-unit energy ledger rows from the physics units: duty types kept apart (shaft power, cooling duty, recovered heat,
    internal fuel) from what is bought (purchased_energy_GJ_per_t, the only column that sums to balances.energy_GJ_per_t)."""
    rows = []
    for u in units:
        rows.append(dict(unit=u["name"], type=u["type"], boundary_role=u.get("boundary_role", ""),
                         shaft_power_GJ_per_t=u.get("power_GJ_per_t", 0.0) or 0.0,
                         electricity_GJ_per_t=u.get("electricity_GJ_per_t", u.get("power_GJ_per_t", 0.0)) or 0.0,
                         cooling_duty_GJ_per_t=u.get("cooling_duty_GJ_per_t", 0.0) or 0.0,
                         cooling_medium=u.get("cooling_medium", ""),
                         recovered_heat_GJ_per_t=u.get("recovered_heat_GJ_per_t", 0.0) or 0.0,
                         internal_fuel_GJ_per_t=u.get("internal_fuel_GJ_per_t", 0.0) or 0.0,
                         purchased_energy_GJ_per_t=u.get("purchased_energy_GJ_per_t", 0.0) or 0.0,
                         energy_method=u.get("energy_method", "")))
    return rows


def capex_ledger(units, capacity_t_per_y):
    """Per-unit capital ledger rows: installed capital, USD per annual tonne and the cost basis the model declared."""
    rows = []
    for u in units:
        b = u.get("capex_basis") or {}
        rows.append(dict(unit=u["name"], type=u["type"], boundary_role=u.get("boundary_role", ""), capex_usd=u.get("capex_usd", 0.0),
                         usd_per_t_y=(u.get("capex_usd", 0.0) or 0.0) / capacity_t_per_y, method=b.get("method", ""),
                         size_basis=b.get("size_basis", ""), share=b.get("share", ""), plant_cost_usd=b.get("plant_cost_usd", ""),
                         source_capacity=b.get("source_capacity", ""), cost_year=b.get("cost_year", ""),
                         installed=b.get("installed", ""), installation_factor=b.get("installation_factor", "")))
    return rows


def plant_cost_share(plant_cost_usd, share, method="plant_specific_cost_share", **basis):
    """Capital of one unit as its share of a plant-level installed cost that is already scaled to the model capacity (use
    scaled_capex from the source's own capacity first). The share is fixed: a plant-level specific cost already prices a
    complete plant of the source's design, so internal flows such as recycle do not scale it again. Returns capex_usd and the
    capex_basis record the physics gate checks."""
    if not 0 <= share <= 1:
        raise ValueError("share must be in [0, 1]")
    return dict(capex_usd=plant_cost_usd * share,
                capex_basis=dict(method=method, plant_cost_usd=plant_cost_usd, share=share, installed=True, **basis))
