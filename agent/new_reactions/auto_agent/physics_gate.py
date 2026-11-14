"""Independent ideal-gas physics checks for AI-built plant models (1 bar standard state)."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from scipy.optimize import brentq

R = 8.314462618
COMPRESSOR_MAX_ISOTHERMAL = 2.5  # Maximum shaft work relative to reversible isothermal work.
MIN_PRIMARY_EFFICIENCY = .30  # Minimum primary-energy-to-shaft conversion efficiency.
BOUNDARY_STATE_RTOL = .01  # Boundary inlet pressure and temperature agreement.
EXOTHERMIC_PREHEAT_FRACTION = .05  # Purchased preheat fraction requiring external evidence.
COMPRESSOR_CAPEX_PER_KW = (200, 8000)  # Installed compressor capital per shaft kW.
FURNACE_CAPEX_PER_KW = (50, 3000)  # Installed furnace capital per purchased-duty kW.
ZERO_DUTY_TYPES = ("regenerator", "furnace", "separation")  # Zero energy/heat duty needs measured/published evidence.
ZERO_DUTY_EPS = 1e-6  # GJ/t below which a unit counts as zero duty.
T0 = 298.15
# V3.3.1 engineering-ledger checks (2026-11-14; found on the development reaction CO2 methanation, ch4_v33_t3, written per
# unit type and valid for any process). A cooling duty is not purchased energy: cooling water and air coolers need about
# 1.5-2 % of the rejected heat as pump and fan electricity (unitops.cooling_utility); the limits allow twice that.
COOLING_MAX_ELECTRIC_FRACTION = {"cooling_water": .03, "air": .04}
REFRIGERATION_MIN_SECOND_LAW = .25        # refrigeration COP at least a quarter of Carnot
COOLING_MEDIA = ("cooling_water", "air", "refrigeration")
SEPARATION_ENERGY_METHODS = ("unitops.separator_energy", "published_factor")
SOURCE_PRESSURE_RATIO_MIN = .5            # a per-volume energy factor measured on a feed below half the unit's feed pressure
                                          # already contains feed compression
BOUNDARY_ROLES = ("feed_conditioning", "reaction", "heat_integration", "separation", "recycle", "product_conditioning",
                  "utilities", "offsites")
CAPEX_METHODS = ("power_based", "duty_based", "size_based", "plant_specific_cost_share", "published_unit_cost", "vendor_quote")
# NIST Chemistry WebBook SRD 69, gas phase thermochemistry, SI units:
# https://webbook.nist.gov/cgi/cbook.cgi?ID=C<CAS digits>&Units=SI&Mask=1
# Columns: formation enthalpy kJ/mol, entropy J/mol/K (1 bar), Cp J/mol/K at 298.15 K.
# CODATA/JANAF (Cox et al. 1984; Chase 1998); hydrocarbons/alcohol Cp: TRC tables.
# CAS digits in the same order: 1333740, 74828, 74840, 74851, 74986, 115071,
# 630080, 124389, 7732185, 7664417, 7727379, 7782447, 64175, 67561, 7440371.
# Cp298 remains the fallback only for species without WebBook Shomate coefficients.
THERMO = {
    "H2": (0., 130.680, 28.836), "CH4": (-74.87, 186.25, 35.69),
    "C2H6": (-84.0, 229.49, 52.49), "C2H4": (52.47, 219.32, 42.84),
    "C3H8": (-104.7, 269.91, 73.60), "C3H6": (20.41, 266.94, 64.32),
    "CO": (-110.53, 197.660, 29.14), "CO2": (-393.51, 213.785, 37.13),
    "H2O": (-241.826, 188.835, 33.59), "NH3": (-45.94, 192.77, 35.06),
    "N2": (0., 191.609, 29.124), "O2": (0., 205.152, 29.376),
    "C2H5OH": (-234.0, 282.70, 65.21), "CH3OH": (-201.0, 239.9, 44.06),
    "Ar": (0., 154.845, 20.786),
}
# NIST gas-phase Shomate fits (Chase 1998), fetched 2026-11-12.
# Each row: Tmin K, Tmax K, (A, B, C, D, E, F, G, H); t = T/1000.
SHOMATE = {
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Units=SI&Mask=1
    "H2": [
        (298, 1000, (33.066178, -11.363417, 11.432816, -2.772874, -0.158558, -9.980797, 172.707974, 0.0)),
        (1000, 2500, (18.563083, 12.257357, -2.859786, 0.268238, 1.97799, -1.147438, 156.288133, 0.0)),
        (2500, 6000, (43.41356, -4.293079, 1.272428, -0.096876, -20.533862, -38.515158, 162.081354, 0.0)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Units=SI&Mask=1
    "CH4": [
        (298, 1300, (-0.703029, 108.4773, -42.52157, 5.862788, 0.678565, -76.84376, 158.7163, -74.8731)),
        (1300, 6000, (85.81217, 11.26467, -2.114146, 0.13819, -26.42221, -153.5327, 224.4143, -74.8731)),
    ],
    # C2H6: no gas Shomate entry; constant Cp298 fallback.
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C74840&Units=SI&Mask=1
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C74851&Units=SI&Mask=1
    "C2H4": [
        (298, 1200, (-6.38788, 184.4019, -112.9718, 28.49593, 0.31554, 48.17332, 163.1568, 52.46694)),
        (1200, 6000, (106.5104, 13.7326, -2.628481, 0.174595, -26.14469, -35.36237, 275.0424, 52.46694)),
    ],
    # C3H8: no gas Shomate entry; constant Cp298 fallback.
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C74986&Units=SI&Mask=1
    # C3H6: no gas Shomate entry; constant Cp298 fallback.
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C115071&Units=SI&Mask=1
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C630080&Units=SI&Mask=1
    "CO": [
        (298, 1300, (25.56759, 6.09613, 4.054656, -2.671301, 0.131021, -118.0089, 227.3665, -110.5271)),
        (1300, 6000, (35.1507, 1.300095, -0.205921, 0.01355, -3.28278, -127.8375, 231.712, -110.5271)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Units=SI&Mask=1
    "CO2": [
        (298, 1200, (24.99735, 55.18696, -33.69137, 7.948387, -0.136638, -403.6075, 228.2431, -393.5224)),
        (1200, 6000, (58.16639, 2.720074, -0.492289, 0.038844, -6.447293, -425.9186, 263.6125, -393.5224)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=1
    "H2O": [
        (500, 1700, (30.092, 6.832514, 6.793435, -2.53448, 0.082139, -250.881, 223.3967, -241.8264)),
        (1700, 6000, (41.96426, 8.622053, -1.49978, 0.098119, -11.15764, -272.1797, 219.7809, -241.8264)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Units=SI&Mask=1
    "NH3": [
        (298, 1400, (19.99563, 49.77119, -15.37599, 1.921168, 0.189174, -53.30667, 203.8591, -45.89806)),
        (1400, 6000, (52.02427, 18.48801, -3.765128, 0.248541, -12.45799, -85.53895, 223.8022, -45.89806)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Units=SI&Mask=1
    "N2": [
        (100, 500, (28.98641, 1.853978, -9.647459, 16.63537, 0.000117, -8.671914, 226.4168, 0.0)),
        (500, 2000, (19.50583, 19.88705, -8.598535, 1.369784, 0.527601, -4.935202, 212.39, 0.0)),
        (2000, 6000, (35.51872, 1.128728, -0.196103, 0.014662, -4.55376, -18.97091, 224.981, 0.0)),
    ],
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Units=SI&Mask=1
    "O2": [
        (100, 700, (31.32234, -20.23531, 57.86644, -36.50624, -0.007374, -8.903471, 246.7945, 0.0)),
        (700, 2000, (30.03235, 8.772972, -3.988133, 0.788313, -0.741599, -11.32468, 236.1663, 0.0)),
        (2000, 6000, (20.91111, 10.72071, -2.020498, 0.146449, 9.245722, 5.337651, 237.6185, 0.0)),
    ],
    # C2H5OH: no gas Shomate entry; constant Cp298 fallback.
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175&Units=SI&Mask=1
    # CH3OH: no gas Shomate entry; constant Cp298 fallback.
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C67561&Units=SI&Mask=1
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440371&Units=SI&Mask=1
    "Ar": [
        (298, 6000, (20.786, 2.825911e-07, -1.464191e-07, 1.092131e-08, -3.661371e-08, -6.19735, 179.999, 0.0)),
    ],
}
ATOMIC_MASS = dict(H=1.008, C=12.011, N=14.007, O=15.999, S=32.06,
                   Cl=35.45, F=18.998, Ar=39.948, He=4.0026)
UNIT_TYPES = {"reactor", "furnace", "compressor", "separation", "knockout", "heat_exchanger",
              "regenerator", "pump", "offsites", "other"}
CATEGORIES = {"feed_preparation", "reactor_heat_supply_or_removal", "catalyst_regeneration",
              "product_compression", "separation_and_purification", "recycle", "heat_recovery",
              "utilities_and_offsites"}


def formula_elements(formula):
    """Parse complete simple formulas, accumulating repeated elements (e.g. C2H5OH)."""
    if not isinstance(formula, str) or not re.fullmatch(r"(?:[A-Z][a-z]?\d*)+", formula):
        raise ValueError(f"invalid formula {formula!r}")
    counts = {}
    for el, count in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        n = int(count) if count else 1
        if n <= 0 or el not in ATOMIC_MASS:
            raise ValueError(f"invalid element/count in {formula}")
        counts[el] = counts.get(el, 0) + n
    return counts


def formula_mw(formula):
    return round(sum(ATOMIC_MASS[e] * n for e, n in formula_elements(formula).items()), 3)


def _number(value, minimum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"expected finite number, got {value!r}")
    if (minimum is not None and value < minimum) or (positive and value <= 0):
        raise ValueError(f"invalid physical value {value}")
    return value


def _thermo(species):
    if species not in THERMO:
        raise ValueError(f"no thermo data for {species}")
    return THERMO[species]


def _shomate_integrals(coeff, T):
    """NIST H(T)-H298 in kJ/mol and S(T) in J/mol/K."""
    a, b, c, d, e, f, g, h = coeff
    t = T / 1000
    return (a*t + b*t*t/2 + c*t**3/3 + d*t**4/4 - e/t + f - h,
            a*math.log(t) + b*t + c*t*t/2 + d*t**3/3 - e/(2*t*t) + g)


def species_thermo(species, T):
    """Return H (formation basis, J/mol) and S (J/mol/K), anchored at 298.15 K.

    Integrate each fit over its interval, preserving continuity and the tabulated
    formation enthalpy/S298 despite small rounding mismatches between NIST fits.
    Water's lowest gas fit starts at 500 K: explicitly extrapolate that fit down
    to 298.15 K for the gas reference integral. Other out-of-range requests fail.
    Species without WebBook Shomate fits retain the original constant Cp298.
    """
    _number(T, positive=True)
    hf, s0, cp = _thermo(species)
    fits = SHOMATE.get(species)
    if not fits:
        return hf*1000 + cp*(T-T0), s0 + cp*math.log(T/T0)
    minimum = T0 if species == "H2O" else fits[0][0]
    if not minimum <= T <= fits[-1][1]:
        raise ValueError(f"thermo temperature {T:g} K outside {species} range [{minimum:g}, {fits[-1][1]:g}]")
    lo, hi = sorted((T0, T))
    cuts = [lo] + [row[1] for row in fits[:-1] if lo < row[1] < hi] + [hi]
    dh, ds = 0., 0.
    for left, right in zip(cuts, cuts[1:]):
        mid = (left + right) / 2
        coeff = next(row[2] for row in fits if mid <= row[1])
        h1, s1 = _shomate_integrals(coeff, left)
        h2, s2 = _shomate_integrals(coeff, right)
        dh += (h2-h1)*1000
        ds += s2-s1
    sign = 1 if T >= T0 else -1
    return hf*1000 + sign*dh, s0 + sign*ds


def reaction_dH(nu, T):
    """J/mol reaction as written, from formation enthalpies and Shomate integrals."""
    _number(T, positive=True)
    return sum(v * species_thermo(s, T)[0] for s, v in nu.items())


def _fractions(y):
    if not y or abs(sum(_number(v, 0) for v in y.values()) - 1) > 1e-6:
        raise ValueError("mole fractions must be nonnegative and sum to 1")
    return y


def equilibrium_conversion(nu, key, feed_y, T_K, P_bar):
    """Single ideal-gas reaction; bracket the full feasible extent, including reverse reaction."""
    _number(T_K, positive=True)
    _number(P_bar, positive=True)
    _fractions(feed_y)
    for s in set(nu) | set(feed_y):
        _thermo(s)
    if nu.get(key, 0) >= 0 or feed_y.get(key, 0) <= 0 or not any(v > 0 for v in nu.values()):
        raise ValueError("key must be a fed reactant; reaction must have products")
    ds = sum(v * species_thermo(s, T_K)[1] for s, v in nu.items())
    logk = -(reaction_dH(nu, T_K) - T_K * ds) / (R * T_K)
    lo = max(-feed_y.get(s, 0) / v for s, v in nu.items() if v > 0)
    hi = min(-feed_y.get(s, 0) / v for s, v in nu.items() if v < 0)
    if hi <= lo:
        raise ValueError("no feasible reaction extent")

    def residual(extent):
        mol = {s: feed_y.get(s, 0) + nu.get(s, 0) * extent for s in set(feed_y) | set(nu)}
        total = sum(mol.values())
        return sum(v * math.log(max(mol[s] / total * P_bar, 1e-300))
                   for s, v in nu.items() if v) - logk

    # Endpoint limits are represented with a log floor, avoiding overflow in K itself.
    if residual(lo) >= 0:
        extent = lo
    elif residual(hi) <= 0:
        extent = hi
    else:
        extent = brentq(residual, lo, hi, xtol=1e-14)
    return -nu[key] * extent / feed_y[key]


def check_flowsheet(path):
    """Validate the graph and explicit completeness checklist; return actionable failures."""
    failures = []
    try:
        f = json.loads(Path(path).read_text(encoding="utf-8"))
        units, streams = f["units"], f["streams"]
        names = [u["name"] for u in units]
        if not names or any(not isinstance(n, str) or not n.strip() or n == "boundary" for n in names):
            failures.append("flowsheet: nonempty unit names required; boundary is reserved")
        if len(names) != len(set(names)):
            failures.append("flowsheet: duplicate unit names")
        snames = [s["name"] for s in streams]
        if len(snames) != len(set(snames)) or any(not n for n in snames):
            failures.append("flowsheet: stream names must be unique and nonempty")
        known = set(names) | {"boundary"}
        reached = set()
        for s in streams:
            if s["from"] not in known or s["to"] not in known or s["from"] == s["to"] == "boundary":
                failures.append(f"flowsheet stream {s['name']}: invalid from/to")
            if not s["species"]:
                failures.append(f"flowsheet stream {s['name']}: species missing")
            for species in s["species"]:
                formula_elements(species)
            if s["from"] == "boundary":
                reached.add(s["to"])
        for _ in units:
            reached.update(s["to"] for s in streams if s["from"] in reached)
        if not any(s["to"] == "boundary" and s["from"] in names for s in streams):
            failures.append("flowsheet: boundary outlet missing")
        for u in units:
            name = u["name"]
            if u["type"] not in UNIT_TYPES or not str(u["purpose"]).strip():
                failures.append(f"flowsheet unit {name}: invalid type/purpose")
            for field, endpoint in (("inlets", "to"), ("outlets", "from")):
                actual = {s["name"] for s in streams if s[endpoint] == name}
                if not u[field] or set(u[field]) != actual:
                    failures.append(f"flowsheet unit {name}: {field} inconsistent with streams")
            if name not in reached:
                failures.append(f"flowsheet unit {name}: unreachable from boundary inlet")
        checklist = f["checklist"]
        if set(checklist) != CATEGORIES:
            failures.append("flowsheet: checklist categories must match exactly: " + ", ".join(sorted(CATEGORIES)))
        for category, item in checklist.items():
            if set(item) == {"included"}:
                if not isinstance(item["included"], list) or not item["included"] or any(n not in names for n in item["included"]):
                    failures.append(f"flowsheet checklist {category}: included unit missing/unknown")
            elif set(item) != {"excluded"} or not isinstance(item["excluded"], str) or len(item["excluded"].strip()) < 40:
                failures.append(f"flowsheet checklist {category}: exclusion needs at least 40 characters")
        if not isinstance(f["diagram"], str) or not f["diagram"].strip():
            failures.append("flowsheet: diagram missing")
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as e:
        failures.append(f"flowsheet schema: {e}")
    return failures


def check_physics(model_module, out, flowsheet, basis=None, ledger=False):
    """Check one output, failing closed on malformed/missing/nonfinite physical fields. ledger=True (build mode V3.3.1 and
    later, with basis) adds the engineering-ledger checks: boundary roles, cooling utilities, separation energy basis and
    capital basis."""
    failures = []

    def check(label, fn):
        try:
            fn()
        except (KeyError, TypeError, ValueError, AttributeError, ZeroDivisionError, OverflowError) as e:
            failures.append(f"{label}: {e}")

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    try:
        reaction = model_module.REACTION
        nu, key, product = reaction["nu"], reaction["key"], reaction["product"]
        physics = out["physics"]
        reactor, boundary, units = physics["reactor"], physics["boundary"], physics["units"]
        if not isinstance(nu, dict) or not nu or not isinstance(reactor, dict) or not isinstance(boundary, dict):
            raise ValueError("nu, reactor and boundary must be nonempty mappings")
        if not isinstance(units, list) or not units or any(not isinstance(u, dict) for u in units):
            raise ValueError("units must be a nonempty list of unit mappings")
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        return [f"physics contract: {e}"]

    def stoichiometry():
        atoms = {}
        require(nu[key] < 0 < nu[product], "key/product stoichiometric signs invalid")
        for s, v in nu.items():
            _number(v)
            for el, n in formula_elements(s).items():
                atoms[el] = atoms.get(el, 0) + n * v
        for el, v in atoms.items():
            require(abs(v) < 1e-8, f"element {el} imbalanced in nu ({v})")
    check("element_balance reaction", stoichiometry)

    def boundary_balance():
        sides = []
        masses = []
        for side in ("in_t_per_t", "out_t_per_t"):
            atoms = {}
            masses.append(sum(_number(v, 0) for v in boundary[side].values()))
            for s, mass in boundary[side].items():
                for el, n in formula_elements(s).items():
                    atoms[el] = atoms.get(el, 0) + mass / formula_mw(s) * n
            sides.append(atoms)
        require(abs(masses[0] - masses[1]) <= .01 * max(masses), "total mass imbalance > 1%")
        for el in set(sides[0]) | set(sides[1]):
            a, b = (s.get(el, 0) for s in sides)
            require(abs(a - b) <= .01 * max(a, b), f"element {el} boundary imbalance > 1%")
        require(boundary["out_t_per_t"].get(product, 0) >= .99, f"product {product} out < 0.99 t/t")
    check("element_balance boundary_mass", boundary_balance)

    def equilibrium():
        eq = equilibrium_conversion(nu, key, reactor["feed_mol_frac"], reactor["T_K"], reactor["P_bar"])
        x = _number(reactor["per_pass_conversion"], 0)
        require(x <= 1 and x <= eq + .03, f"reactor {key} conversion {x:g} exceeds equilibrium {eq:g} + 0.03")
    check("equilibrium", equilibrium)

    def heat():
        q = reaction_dH(nu, reactor["T_K"]) * (1e6 / formula_mw(product) / nu[product]) / 1e9
        duty = _number(reactor["heat_duty_GJ_per_t"])
        require(duty >= .9 * q if q > 0 else duty <= .9 * q, f"reactor heat duty {duty:g}, reaction heat {q:g} GJ/t")
        if q > 0:
            supply = sum(_number(u["purchased_energy_GJ_per_t"], 0) + _number(u["internal_fuel_GJ_per_t"], 0) for u in units)
            require(supply >= duty, "reactor heat supply below duty")
    check("reaction_heat heat_supply", heat)

    def unit_check(u):
        typ = u["type"]
        require(typ in UNIT_TYPES, f"unknown type {typ}")
        energy = _number(u["purchased_energy_GJ_per_t"], 0)
        fuel = _number(u["internal_fuel_GJ_per_t"], 0)
        _number(u["capex_usd"], 0)
        if typ == "compressor":
            n = _number(u["kmol_per_t"], 0) * 1000
            t = _number(u["T_in_K"], positive=True)
            pin, pout = (_number(u[k], positive=True) for k in ("P_in_bar", "P_out_bar"))
            require(pout > pin, "compressor P_out <= P_in")
            wmin = n * R * t * math.log(pout / pin) / 1e9
            power = _number(u["power_GJ_per_t"], 0)
            require(power + 1e-10 >= wmin, f"compressor power below isothermal minimum {wmin:g}")
            require(energy + 1e-10 >= power, "compressor purchased energy below power")
            if basis is not None:
                require(power <= COMPRESSOR_MAX_ISOTHERMAL * wmin + 1e-10, "compressor_upper: power exceeds 2.5 times isothermal minimum")
                require(energy <= power / MIN_PRIMARY_EFFICIENCY + 1e-10, "compressor_upper: purchased energy exceeds power / 0.30")
        elif typ == "separation":
            def stream(s):
                n = _number(s["kmol_per_t"], 0)
                y = _fractions(s["mol_frac"])
                for species in y:
                    formula_elements(species)
                return {k: n * v for k, v in y.items()}, n * sum(x * math.log(x) for x in y.values() if x)
            feed, mix_in = stream(u["feed"])
            outputs, mix_out = {}, 0.
            require(bool(u["outlets"]), "separation outlets missing")
            for s in u["outlets"]:
                comp, mix = stream(s)
                mix_out += mix
                for k, v in comp.items():
                    outputs[k] = outputs.get(k, 0) + v
            for s in set(feed) | set(outputs):
                a, b = feed.get(s, 0), outputs.get(s, 0)
                require(abs(a - b) <= .02 * max(a, b), f"separation component {s} imbalance > 2%")
            wmin = R * T0 * 1000 * (mix_out - mix_in) / 1e9
            supply = energy + fuel + _number(u.get("recovered_heat_GJ_per_t", 0), 0) + _letdown_exergy(u)
            require(supply + 1e-10 >= wmin, f"separation energy below mixing minimum {wmin:g}")
        elif typ == "knockout":
            _number(u["cooling_duty_GJ_per_t"], 0)
    for i, u in enumerate(units):
        check(f"unit {u.get('name', i) if isinstance(u, dict) else i} compression/separation", lambda u=u: unit_check(u))

    def accounting():
        for field, balance, floor in (("purchased_energy_GJ_per_t", "energy_GJ_per_t", .05), ("capex_usd", "capex_usd", 0)):
            total = sum(_number(u[field], 0) for u in units)
            reported = _number(out["balances"][balance], 0)
            require(abs(total - reported) <= max(floor, .01 * abs(reported)), f"{balance} unit sum {total:g} != balances {reported:g}")
        if out["balances"]["energy_GJ_per_t"] > .05:
            require(_number(out["parts"]["energy"]) > 0, "parts.energy must be positive")
    check("accounting", accounting)

    def consistency():
        names = [u["name"] for u in units]
        require(len(names) == len(set(names)), "duplicate physics unit names")
        expected = {u["name"] for u in flowsheet["units"]}
        require(set(names) == expected, f"unit names differ: {sorted(set(names) ^ expected)}")
        types = {u["name"]: u["type"] for u in flowsheet["units"]}
        for u in units:
            require(u["type"] == types[u["name"]], f"unit {u['name']} type differs from flowsheet")
    check("flowsheet_consistency", consistency)
    if basis is not None:
        def boundary_states():
            feeds = basis["feeds"]
            for stream in flowsheet["streams"]:
                if stream["from"] == "boundary":
                    require(set(stream["species"]) <= set(feeds), "boundary species absent from basis feeds")
                    for u in units:
                        if u["name"] == stream["to"] and u["type"] == "compressor":
                            for sp in stream["species"]:
                                for field, uf in (("P_bar", "P_in_bar"), ("T_K", "T_in_K")):
                                    v = feeds[sp][field]["value"]
                                    require(abs(u[uf] - v) <= BOUNDARY_STATE_RTOL * abs(v), f"boundary_feed_state: {u['name']} {sp} {uf} differs from basis")
        check("boundary_feed_state", boundary_states)
        def preheat():
            duty = reactor["heat_duty_GJ_per_t"]
            # V3.2 (2026-11-14, found on the development reaction CO2 methanation): purchased heat counts from furnaces and from
            # heat exchangers / other units unless they declare service 'cooling'; a trim heater typed heat_exchanger
            # previously escaped this check
            bought = sum(u["purchased_energy_GJ_per_t"] for u in units if u["type"] == "furnace" or
                         (u["type"] in ("heat_exchanger", "other") and u.get("service") != "cooling"))
            if duty < 0 and bought > EXOTHERMIC_PREHEAT_FRACTION * abs(duty):
                from_basis = basis.get("purchased_preheat_reason") or {}
                require(from_basis.get("type") in ("measured", "published"), "exothermic reactor buys preheat")
                try:
                    from .basis_gate import evidence
                except ImportError:
                    from basis_gate import evidence
                evidence(from_basis)
        check("exothermic_preheat", preheat)
        def capital():
            hours = _number(basis["operating_hours_per_y"]["value"], positive=True)
            capacity = _number(basis["capacity_t_per_y"]["value"], positive=True)
            require(abs(out["balances"]["capacity_t_per_y"] - capacity) <= .01 * capacity, "capacity differs from basis")
            for u in units:
                if u["type"] not in ("compressor", "furnace"):
                    continue
                duty = u["power_GJ_per_t"] if u["type"] == "compressor" else u["purchased_energy_GJ_per_t"]
                kw = duty * capacity / hours / .0036
                if kw <= 0:
                    require(u["capex_usd"] == 0, "nonzero equipment capital at zero power")
                    continue
                ratio = u["capex_usd"] / kw
                lo, hi = COMPRESSOR_CAPEX_PER_KW if u["type"] == "compressor" else FURNACE_CAPEX_PER_KW
                require(lo <= ratio <= hi, f"capital_plausibility: {u['name']} {ratio:g} USD/kW outside [{lo}, {hi}]")
        check("capital_plausibility", capital)
        def zero_duty():
            proofs = basis.get("zero_duty_evidence") or {}
            try:
                from .basis_gate import evidence
            except ImportError:
                from basis_gate import evidence
            for u in units:
                if u["type"] not in ZERO_DUTY_TYPES:
                    continue
                duty = sum(_number(u.get(k, 0), 0) for k in ("purchased_energy_GJ_per_t", "internal_fuel_GJ_per_t", "recovered_heat_GJ_per_t"))
                if u["type"] == "separation":
                    duty += _letdown_exergy(u)      # a pressure-driven separation is driven by its feed pressure (V3.3.1)
                if duty <= ZERO_DUTY_EPS:
                    ev = proofs.get(u["name"])
                    require(isinstance(ev, dict) and ev.get("type") in ("measured", "published"),
                            f"zero_duty: {u['type']} {u['name']} has zero energy/heat duty without measured/published evidence in basis.zero_duty_evidence")
                    evidence(ev)
        check("zero_duty", zero_duty)
        if ledger:
            ledger_checks(units, out, basis, failures)
    return failures


def _letdown_exergy(u):
    """Pressure exergy released by separation outlets that leave below the feed pressure, GJ per t (ideal gas, T0):
    sum n R T0 ln(P_feed / P_outlet). Zero unless the feed (feed.P_bar or P_in_bar) and outlet pressures (P_bar) are given."""
    feed = u.get("feed") or {}
    pin = feed.get("P_bar", u.get("P_in_bar"))
    if pin is None:
        return 0.
    pin = _number(pin, positive=True)
    total = 0.
    for o in u.get("outlets") or []:
        if o.get("P_bar") is None:
            continue
        pout = _number(o["P_bar"], positive=True)
        if pout < pin:
            total += _number(o["kmol_per_t"], 0) * 1000 * R * T0 * math.log(pin / pout) / 1e9
    return total


def ledger_checks(units, out, basis, failures):
    """V3.3.1 engineering-ledger checks; generic per unit type."""
    def check(label, fn):
        try:
            fn()
        except (KeyError, TypeError, ValueError, AttributeError, ZeroDivisionError, OverflowError) as e:
            failures.append(f"{label}: {e}")

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def roles():
        bad = [u["name"] for u in units if u.get("boundary_role") not in BOUNDARY_ROLES]
        require(not bad, f"units without boundary_role in {BOUNDARY_ROLES}: {bad[:5]}")
    check("ledger boundary_role", roles)

    def cooling(u):
        duty = _number(u.get("cooling_duty_GJ_per_t", 0), 0)
        energy = _number(u["purchased_energy_GJ_per_t"], 0)
        if duty <= ZERO_DUTY_EPS:
            return
        medium = u.get("cooling_medium")
        require(medium in COOLING_MEDIA, f"cooling duty {duty:g} GJ/t without cooling_medium in {COOLING_MEDIA}")
        if medium == "refrigeration":
            t = _number(u["T_process_out_K"], positive=True)
            t_evap, t_cond = t - 5., T0 + 10.
            require(t_cond > t_evap, "refrigeration above ambient: use cooling_water or air")
            limit = 1 / (REFRIGERATION_MIN_SECOND_LAW * t_evap / (t_cond - t_evap)) + COOLING_MAX_ELECTRIC_FRACTION["cooling_water"]
        else:
            limit = COOLING_MAX_ELECTRIC_FRACTION[medium]
        bound = duty * limit / MIN_PRIMARY_EFFICIENCY
        require(energy <= bound + 1e-10,
                f"cooling_utility: purchased energy {energy:g} GJ/t for a {medium} duty of {duty:g} GJ/t exceeds {bound:g} "
                f"(a cooling duty is not purchased energy; use unitops.cooling_utility)")
    for u in units:
        if u["type"] in ("heat_exchanger", "knockout", "other") and (u.get("service") == "cooling" or u["type"] == "knockout"):
            check(f"ledger unit {u['name']} cooling", lambda u=u: cooling(u))

    def separation(u):
        energy = _number(u["purchased_energy_GJ_per_t"], 0)
        if energy <= ZERO_DUTY_EPS:
            return
        method = u.get("energy_method")
        require(method in SEPARATION_ENERGY_METHODS, f"separation energy {energy:g} GJ/t without energy_method in {SEPARATION_ENERGY_METHODS}")
        pin = _number((u.get("feed") or {}).get("P_bar", u.get("P_in_bar")), positive=True)
        if method == "published_factor":
            src = _number(u["source_feed_P_bar"], positive=True)
            require(src >= SOURCE_PRESSURE_RATIO_MIN * pin,
                    f"separation_pressure: energy factor from a source with feed at {src:g} bar applied to a feed at {pin:g} bar "
                    f"(the factor contains feed compression; compute the energy from stream pressures with unitops.separator_energy)")
        else:
            require(energy + 1e-10 >= _number(u["power_GJ_per_t"], 0), "separation purchased energy below its compression power")
    for u in units:
        if u["type"] == "separation":
            check(f"ledger unit {u['name']} separation", lambda u=u: separation(u))

    def capital():
        capacity = _number(basis["capacity_t_per_y"]["value"], positive=True)
        shares = {}
        for u in units:
            capex = _number(u["capex_usd"], 0)
            if capex <= 0:
                continue
            b = u.get("capex_basis")
            require(isinstance(b, dict), f"{u['name']}: capital without capex_basis")
            require(b.get("method") in CAPEX_METHODS, f"{u['name']}: capex_basis.method not in {CAPEX_METHODS}")
            _number(b["cost_year"], positive=True)
            require(isinstance(b.get("installed"), bool), f"{u['name']}: capex_basis.installed must be true or false")
            if b["installed"] and _number(b.get("installation_factor", 1), 0) > 1 + 1e-9:
                raise ValueError(f"capital_double_count: {u['name']} installed cost multiplied by an installation factor again")
            if b["method"] == "plant_specific_cost_share":
                share, plant = _number(b["share"], 0), _number(b["plant_cost_usd"], positive=True)
                require(share <= 1, f"{u['name']}: share > 1")
                require(capex <= share * plant * 1.02 + 1e-6,
                        f"capital_double_count: {u['name']} capital {capex:.4g} exceeds its share {share:g} of the plant cost "
                        f"{plant:.4g} (a plant-level cost already prices the whole plant; do not rescale its shares with internal flows)")
                key = round(plant, 2)
                shares[key] = shares.get(key, 0) + share
                missing = [k for k in ("source_cost_usd", "source_capacity", "scale_exponent") if k not in b]
                require(not missing, f"capital_scaling: {u['name']} plant-level cost without {missing} (state the source plant's "
                                     f"cost and capacity and scale it to the model capacity with scaled_capex)")
                expect = _number(b["source_cost_usd"], positive=True) * (capacity / _number(b["source_capacity"], positive=True)) ** _number(b["scale_exponent"], positive=True)
                if b.get("cost_index_base") and b.get("cost_index_now"):
                    expect *= _number(b["cost_index_now"], positive=True) / _number(b["cost_index_base"], positive=True)
                require(abs(plant - expect) <= .02 * expect,
                        f"capital_scaling: {u['name']} plant_cost_usd {plant:.4g} != source cost scaled to the model capacity {expect:.4g}")
        for plant, total in shares.items():
            require(total <= 1 + 1e-6, f"capital_double_count: shares of plant cost {plant:.4g} sum to {total:g} > 1")
    check("ledger capital_basis", capital)

