"""Typed, reaction-independent contracts at scientific scale boundaries."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import math
from typing import Literal

from physics_gate import formula_elements, equilibrium_conversion, reaction_dH


@dataclass(frozen=True)
class Verdict:
    interface: str
    status: Literal['PASS', 'WARNING', 'BLOCK']
    reasons: list[str]
    warnings: list[str]


class Contract:
    def __init__(self, name):
        self.name, self.blocks, self.warnings = name, [], []

    def require(self, ok, reason):
        if not ok:
            self.blocks.append(reason)

    def warn(self, ok, reason):
        if not ok:
            self.warnings.append(reason)

    def verdict(self):
        return Verdict(self.name, 'BLOCK' if self.blocks else 'WARNING' if self.warnings else 'PASS',
                       self.blocks+self.warnings, self.warnings)


def scalar(x):
    x = x.get('value') if isinstance(x, dict) else x
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError('expected finite numeric scalar')
    return x


def reactor_process(model, out, flow):
    c = Contract('reactor_to_process')
    try:
        r = out['physics']['reactor']
        nu = model.REACTION['nu']
        sides = []
        for field in ('inlet_kmol_per_t', 'outlet_kmol_per_t'):
            streams = r[field]
            c.require(isinstance(streams, dict) and bool(streams), field+' must be a nonempty species mapping')
            atoms = {}
            for s, n in streams.items():
                n = scalar(n)
                c.require(n >= 0, field+': negative species flow')
                for el, count in formula_elements(s).items():
                    atoms[el] = atoms.get(el, 0)+n*count
            sides.append(atoms)
        for el in set(sides[0]) | set(sides[1]):
            a, b = (s.get(el, 0) for s in sides)
            c.require(abs(a-b) <= .01*max(abs(a), abs(b), 1e-12), 'reactor outlet element imbalance: '+el)
        eq = equilibrium_conversion(nu, model.REACTION['key'], r['feed_mol_frac'], r['T_K'], r['P_bar'])
        x = scalar(r['per_pass_conversion'])
        c.require(0 <= x <= 1 and x <= eq+.03, 'conversion exceeds equilibrium +0.03 or physical range')
        c.warn(x < .98*eq, 'conversion within 2% of equilibrium limit')
        dh, q = reaction_dH(nu, r['T_K']), scalar(r['heat_duty_GJ_per_t'])
        c.require(dh*q >= 0 and (dh == 0 or q != 0), 'heat-duty sign differs from reaction enthalpy')
        reactor_names = {u['name'] for u in flow['units'] if u['type'] == 'reactor'}
        c.require(bool(reactor_names), 'flowsheet reactor missing')
        for side, field in (('to', 'inlet_kmol_per_t'), ('from', 'outlet_kmol_per_t')):
            species = {s for stream in flow['streams'] if stream[side] in reactor_names for s in stream['species']}
            c.require(set(r[field]) <= species, field+': species absent from reactor flowsheet streams')
    except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError) as exc:
        c.blocks.append('reactor interface data: '+str(exc))
    return c.verdict()


def process_tea(out, flow, basis):
    c = Contract('process_to_tea')
    try:
        c.require(isinstance(basis.get('battery_limit'), str) and bool(basis['battery_limit'].strip()), 'basis battery_limit text required')
        eff = scalar(basis['utilities']['primary_efficiency'])
        c.require(0 < eff <= 1, 'utilities.primary_efficiency must be in (0,1]')
        for key in ('capacity_t_per_y', 'operating_hours_per_y'):
            expected = scalar(basis[key])
            c.require(expected > 0 and math.isclose(scalar(out['balances'][key]), expected, rel_tol=1e-9), key+' must come from basis')
        # product state comes from the model output (the flowsheet lists species only): physics.boundary.product =
        # {species: {"P_bar": .., "mol_frac": ..}}; pressure must match the basis, purity must meet it (a spec is a minimum)
        products = out['physics']['boundary'].get('product') or {}
        for species, state in basis['product'].items():
            c.require(any(s['to'] == 'boundary' and species in s['species'] for s in flow['streams']),
                      'product boundary stream missing in flowsheet: '+species)
            got = products.get(species)
            c.require(isinstance(got, dict), 'physics.boundary.product.'+species+' {P_bar, mol_frac} required')
            c.require(math.isclose(scalar(got['P_bar']), scalar(state['P_bar']), rel_tol=.02), 'product pressure differs from basis: '+species)
            c.require(scalar(got['mol_frac']) >= scalar(state['purity_mol_frac']) - 1e-3, 'product purity below basis spec: '+species)
        for u in out['physics']['units']:
            if u.get('capex_usd', 0) or 'capex_basis' in u:
                b = u.get('capex_basis', {})
                c.require(bool(b.get('cost_year')), str(u['name'])+': capex_basis.cost_year required')
                if b.get('cost_index_now') is not None or b.get('cost_index_base') is not None:
                    c.warn(bool(b.get('cost_index_source')), str(u['name'])+': cost index source missing')
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        c.blocks.append('process/TEA interface data: '+str(exc))
    return c.verdict()


def mkm_reactor(atomic, out):
    c = Contract('mkm_to_reactor')
    try:
        c.require(atomic.get('tof_unit') in ('s^-1', '1/s', 'site^-1 s^-1'), 'TOF units must be declared as per-site per-second')
        for field in ('site_density_evidence', 'dispersion_evidence'):
            c.warn(bool(atomic.get(field)), field+' missing')
        bounds = atomic.get('temperature_range_K')
        c.warn(bool(bounds), 'MKM fitted/declared temperature_range_K missing')
        if bounds:
            lo, hi = map(scalar, bounds)
            c.require(0 < lo <= hi, 'invalid MKM temperature range')
            c.warn(lo <= scalar(out['physics']['reactor']['T_K']) <= hi, 'reactor temperature outside MKM fitted/declared range')
    except (KeyError, ValueError, TypeError) as exc:
        c.blocks.append('MKM/reactor interface data: '+str(exc))
    return c.verdict()


def dft_mkm(atomic):
    c = Contract('dft_to_mkm')
    c.require(isinstance(atomic.get('energy_reference_state'), str) and bool(atomic['energy_reference_state'].strip()), 'energy reference state required')
    c.warn(bool(atomic.get('scaling_bep_source')), 'scaling/BEP source missing')
    return c.verdict()


def check(model, out, flow, basis, atomic=None):
    verdicts = [reactor_process(model, out, flow), process_tea(out, flow, basis)]
    if atomic is not None:
        verdicts += [mkm_reactor(atomic, out), dft_mkm(atomic)]
    return dict(passed=all(v.status != 'BLOCK' for v in verdicts), contracts=[asdict(v) for v in verdicts],
                blocks=[v.interface+': '+r for v in verdicts if v.status == 'BLOCK' for r in v.reasons],
                warnings=[v.interface+': '+r for v in verdicts for r in v.warnings])
