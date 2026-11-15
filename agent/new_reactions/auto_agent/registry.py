"""Versioned scientific capabilities and experimental-module validation (offline)."""
from __future__ import annotations
import copy
import hashlib
import importlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def enabled(h):
    match = re.match(r'V(\d+)\.(\d+)', getattr(h, 'build_version', ''))
    return bool(match and tuple(map(int, match.groups())) >= (3, 6))


PROMPT = """
V3.6: model.py is a composition layer; new scientific equations belong in modules/<name>.py.
Every energy/cooling/capital unit declares computed_by=[registered module IDs or experimental:<name>].
Use list_modules/describe_module for contracts. Experimental modules expose META and compute(**inputs),
and tests() returning conservation/limit/reference cases {kind, inputs}; tests assert their expected results.
META declares inputs, outputs (name:unit), units, assumptions, applicability. Call validate_module before use.
check_model writes interface_check.json and module_coverage.json; copy every WARNING reason into report.md.
After model_checks, call idaes_check on the reference plant and explain each unit differing by more than 5% in report.md.
Plan/revise a workflow DAG; validate evidence, basis, flowsheet, model_check, interface_check,
independent_validation (critic), report. Skips need >=30-character reasons. Revisions are immutable.
Interface fields: physics.reactor.inlet_kmol_per_t and outlet_kmol_per_t {species: kmol per t}; physics.boundary.product {species: {P_bar, mol_frac}};
basis.utilities.primary_efficiency {value, evidence}; every capex_basis has cost_year.
Declare basis.ranking_strategy=shared_design or reference_reconstruction; per_catalyst is unsupported.
design is continuous; design_int is enumerated. optimize_design(candidate) fixes a named candidate
declared in model.CANDIDATES (mapping of configuration PARAMS), then searches continuous values.
"""

# Predicates use unit-field paths, never reaction identities. Missing predicate fields warn too.
_DOMAINS = {
    'compressor': [('T_in_K', 'positive', None), ('P_in_bar', 'positive', None), ('P_out_bar', 'positive', None),
                   ('phase', 'eq', 'gas')],
    'pump': [('density_kg_m3', 'positive', None), ('phase', 'eq', 'liquid')],
    'sensible_heat': [('T_in_K', 'positive', None), ('T_out_K', 'positive', None)],
    'latent_heat': [('kmol_per_t', 'nonnegative', None)],
    'reaction_heat': [('T_K', 'positive', None)],
    'stream_lhv': [('combustion_basis', 'eq', 'lower_heating_value')],
    'fired_heater': [('efficiency', 'fraction', None), ('duty_GJ_per_t', 'nonnegative', None)],
    'heat_recovery': [('approach_fraction', 'fraction', None), ('heat_recovery_method', 'eq', 'simplified')],
    'recycle_loop': [('per_pass_conversion', 'fraction', None), ('purge_fraction', 'unit_interval', None)],
    'split': [('energy_method', 'present', None)],
    'cooling_utility': [('T_process_out_K', 'positive', None), ('cooling_duty_GJ_per_t', 'nonnegative', None)],
    'separator_energy': [('feed.P_bar', 'positive', None), ('T_K', 'positive', None)],
    'plant_cost_share': [('capex_basis.share', 'unit_interval', None), ('capex_basis.cost_year', 'positive', None)],
    'scaled_capex': [('capex_basis.source_capacity', 'positive', None), ('capex_basis.scale_exponent', 'positive', None)],
}
_ASSUMPTIONS = {
    'split': 'Mass-balance-only ideal component split; separation requires an energy_method.',
    'heat_recovery': 'Simplified approach-fraction heat recovery; not pinch analysis.',
    'solve': 'Single-site mean-field steady state; no lateral interactions or transport coupling.',
    'optimize': 'Local bounded continuous search with finite integer enumeration; no global-optimum guarantee.',
}


def resolve(module_id):
    if module_id not in MODULES:
        raise ValueError('unregistered module: ' + module_id)
    mod, fn = module_id.rsplit('.', 1)
    return getattr(importlib.import_module(mod), fn)


def _entry(mod, name):
    fn = getattr(importlib.import_module(mod), name)
    units = {'kmol_per_t': 'kmol/t', 'T_in_K': 'K', 'T_out_K': 'K', 'T_K': 'K',
             'P_in_bar': 'bar', 'P_out_bar': 'bar', 'dP_bar': 'bar', 'capacity': 't/y',
             'base_capacity': 't/y', 'base_cost_usd': 'USD', 'plant_cost_usd': 'USD',
             'duty_GJ_per_t': 'GJ/t', 'extent_kmol_per_t': 'kmol/t', 'density_kg_m3': 'kg/m3',
             'mw_kg_per_kmol': 'kg/kmol', 'ws': 'workspace path', 'candidate': 'configuration name'}
    def unit(p):
        if p in units:
            return units[p]
        if p.endswith('_GJ_per_t'): return 'GJ/t'
        if p.endswith('_K'): return 'K'
        if p.endswith('_bar'): return 'bar'
        if p.endswith('_Pa'): return 'Pa'
        if p == 'stream': return '{formula: kmol/t}'
        if p in ('species', 'product_species'): return 'chemical formula(s)'
        if p == 'nu': return '{formula: dimensionless stoichiometric coefficient}'
        if p == 'outlets': return '[{kmol_per_t:kmol/t, P_out_bar:bar, P_required_bar:bar}]'
        if p == 'spec': return '{species:site counts, gases:bar, T_K:K, steps:energies eV, overall:stoichiometry}'
        if p == 'basis': return '{cost_year:year, source_capacity:t/y, size_basis:text}'
        if p in ('method','medium'): return 'enum string'
        return 'dimensionless'
    inputs = {p: unit(p) for p in inspect.signature(fn).parameters}
    output_names = {
        'compressor': {'power_GJ_per_t':'GJ/t', 'purchased_energy_GJ_per_t':'GJ/t', 'cooling_duty_GJ_per_t':'GJ/t', 'stages':'integer', 'T_out_K':'K'},
        'pump': {'value':'GJ/t'}, 'sensible_heat': {'value':'GJ/t signed heat'},
        'latent_heat': {'value':'GJ/t'}, 'reaction_heat': {'value':'GJ/t signed heat'},
        'stream_lhv': {'value':'GJ/t'},
        'fired_heater': {k:'GJ/t' for k in ('purchased_energy_GJ_per_t','internal_fuel_GJ_per_t','fuel_fired_GJ_per_t','surplus_internal_fuel_GJ_per_t')},
        'heat_recovery': {k:'GJ/t' for k in ('recovered_heat_GJ_per_t','remaining_cold_duty_GJ_per_t','surplus_hot_GJ_per_t')},
        'recycle_loop': {k:'dimensionless' for k in ('overall_conversion','recycle_ratio','purge_loss_fraction')},
        'split': {'product':'{formula: kmol/t}', 'tail':'{formula: kmol/t}'},
        'cooling_utility': {'cooling_duty_GJ_per_t':'GJ/t','electricity_GJ_per_t':'GJ/t final', 'purchased_energy_GJ_per_t':'GJ/t declared basis', 'cop':'dimensionless','T_process_out_K':'K','cooling_medium':'enum'},
        'separator_energy': {'power_GJ_per_t':'GJ/t','letdown_exergy_GJ_per_t':'GJ/t','purchased_energy_GJ_per_t':'GJ/t declared basis','outlet_pressures':'[{kmol_per_t:kmol/t, P_out_bar:bar, P_required_bar:bar}]'},
        'plant_cost_share': {'capex_usd':'USD','capex_basis':'{cost_year:year, share:dimensionless, installed:bool}'},
        'scaled_capex': {'value':'USD'},
        'solve': {'TOF':'s^-1 per site','coverages':'dimensionless','net_rates':'s^-1 per site','degree_of_rate_control':'dimensionless','residual':'dimensionless','log_kf_over_kr':'dimensionless','method':'solver name'},
        'optimize': {'start':'objective USD/t; parameter units from sources.csv', 'optimum':'objective USD/t; parameter units from sources.csv', 'integer_enumeration':'per-configuration search records'},
    }
    output = output_names[name]
    return dict(module_id=mod+'.'+name, version='UO-1.1' if mod == 'unitops' else '1.0',
                capability=(inspect.getdoc(fn) or name).split('\n')[0], inputs=inputs, outputs=output,
                assumptions=[_ASSUMPTIONS.get(name, 'Use declared stream basis and callable parameters; no process-topology inference.')],
                applicability_domain=[dict(field=f, op=op, value=v) for f, op, v in _DOMAINS.get(name, [])],
                validation='tests_v3/validate_unitops.py' if mod == 'unitops' else
                           'mkm_solver_validate.py' if mod == 'mkm_solver' else 'tests_v3/validate_v35.py',
                provenance=dict(implementation=mod+'.py:'+name, documentation=inspect.getdoc(fn) or name))


MODULES = {} if __name__ == '__main__' else {_e['module_id']: _e for _e in
           [_entry('unitops', n) for n in _DOMAINS] + [_entry('mkm_solver', 'solve'), _entry('design_opt', 'optimize')]}
if MODULES:
    MODULES['mkm_solver.solve']['applicability_domain'] = [dict(field='site_model', op='eq', value='single_site_mean_field')]
    MODULES['design_opt.optimize']['applicability_domain'] = [dict(field='search_method', op='eq', value='local_bounded')]

    # UO-2.0 T1 methods: explicit signatures and output units. No reaction identity.
    from unitops_equipment import UO2_FUNCTIONS
    _uo2_outputs = {
        'cp_mix': {'cp_J_mol_K':'J/mol/K','heat_capacity_GJ_per_t_K':'GJ/t/K'},
        'enthalpy_stream': {'enthalpy_GJ_per_t':'GJ/t formation or sensible'},
        'antoine_psat': {'P_sat_bar':'bar'}, 'vapor_pressure': {'P_sat_bar':'bar'},
        'flash_pt': {'vapor_fraction':'fraction','vapor_kmol_per_t':'kmol/t species mapping','liquid_kmol_per_t':'kmol/t species mapping'},
        'dew_point': {'T_dew_K':'K'},
        'water_knockout': {'vapor_kmol_per_t':'kmol/t species mapping','liquid_kmol_per_t':'kmol/t species mapping','cooling_duty_GJ_per_t':'GJ/t','purchased_energy_GJ_per_t':'GJ/t'},
        'equilibrium_reactor': {'outlet_kmol_per_t':'kmol/t species mapping','extents_kmol_per_t':'kmol/t','heat_duty_GJ_per_t':'GJ/t signed'},
        'adiabatic_temperature_rise': {'T_out_K':'K','delta_T_K':'K','outlet_kmol_per_t':'kmol/t species mapping'},
        'staged_cooled_reactor': {'beds':'per-bed states','outlet_kmol_per_t':'kmol/t species mapping','cooling_duty_GJ_per_t':'GJ/t'},
        'pfr_isothermal': {'outlet_kmol_per_h':'kmol/h species mapping','heat_duty_GJ_per_h':'GJ/h signed'},
        'cstr': {'outlet_kmol_per_h':'kmol/h species mapping','heat_duty_GJ_per_h':'GJ/h signed'},
        'catalyst_inventory': {'catalyst_kg':'kg'}, 'ergun_pressure_drop': {'dP_Pa':'Pa','dP_bar':'bar'},
        'membrane_two_component': {'stage_cut':'fraction','permeate_purity':'fraction','retentate_purity':'fraction','power_GJ_per_t':'GJ/t','permeate_kmol_per_t':'kmol/t species mapping','retentate_kmol_per_t':'kmol/t species mapping'},
        'psa_energy': {'power_GJ_per_t':'GJ/t','product_kmol_per_t':'kmol/t species mapping','tail_kmol_per_t':'kmol/t species mapping'},
        'absorber_kremser': {'theoretical_stages':'stages','absorption_factor':'dimensionless'},
        'stripper_heat': {'heat_duty_GJ_per_t':'GJ/t'},
        'distillation_fug': {'N_min':'stages','R_min':'dimensionless','theoretical_stages':'stages','condenser_duty_GJ_per_t':'GJ/t','reboiler_duty_GJ_per_t':'GJ/t'},
        'heat_exchanger': {'area_m2':'m2','LMTD_K':'K'},
        'problem_table': {'hot_utility_kW':'kW','cold_utility_kW':'kW'},
        'steam_generation': {'steam_kg_per_t':'kg/t','recovered_heat_GJ_per_t':'GJ/t'},
        'turton_cost': {'capex_usd':'USD installed','capex_basis':'method, cost_year, installed, size_basis, source'},
        'cepci': {'index':'dimensionless','year':'year'},
        'lang_factor_total': {'capex_usd':'USD installed','capex_basis':'method, cost_year, installed, size_basis, source'},
    }
    _input_units = dict(stream='kmol/t species mapping',feed='kmol/t (reactors with rate laws: kmol/h)',T='K',P='bar absolute',
                        reference_T='K',bracket='K pair',rate_fn='callable: flows kmol/h, T K, P bar -> rates kmol/m3/h',
                        nu='species stoichiometry',nu_list='list of species stoichiometry',extent='kmol/t',
                        duty='heat_exchanger: kW; steam_generation: GJ/t',U='W/m2/K',size_param='equipment-specific kW/m2/m3',
                        production='kg/h',rate='kg/kgcat/h',deactivation='cycle mean activity fraction',
                        P_ads='bar absolute',P_des='bar absolute',P_feed='bar absolute',P_permeate='bar absolute',P_required='bar absolute',
                        streams='list {Tin:K,Tout:K,CP_kW_K:kW/K}',henry_bar='species H=p/x, bar at specified T and solvent',
                        purchased_equipment_usd='mapping of purchase costs USD, common declared cost_year')
    for name in UO2_FUNCTIONS:
        fn = getattr(importlib.import_module('unitops'),name)
        doc = inspect.getdoc(fn)
        inputs = {p:_input_units.get(p, 'K' if p.startswith('T_') or p in ('inlet_T','max_T','dT_min') else
                    'dimensionless or explicitly SI-suffixed; see docstring') for p in inspect.signature(fn).parameters}
        mid='unitops.'+name
        MODULES[mid]=dict(module_id=mid,version='UO-2.0',tier='T1',capability=doc.split('\n')[0],
                          inputs=inputs,outputs=_uo2_outputs[name],assumptions=[doc],
                          applicability_domain=[dict(field='applicability.status',op='eq',value='within_domain')],
                          validation='tests_v3/validate_uo2.py',provenance=dict(implementation='unitops_equipment.py:'+name,documentation=doc))
    MODULES['idaes_adapter.idaes_check']=dict(module_id='idaes_adapter.idaes_check',version='1.0',tier='T1',
        capability='Independent IDAES ideal-gas reference snapshots, warning >5%; outside inner loop',
        inputs={'model_module_or_reference_out':'module.reference() or plant output dict'},
        outputs={'comparisons':'work/duty/flow relative differences','skipped':'unmapped units and reasons'},
        assumptions=['Ideal gas; Raoult ideal liquid flash; explicit feed/state; 300 s subprocess; reference only'],
        applicability_domain=[dict(field='phase',op='eq',value='gas')],
        supported_units=['Compressor','PressureChanger','Heater','Flash','Mixer','Separator','StoichiometricReactor','EquilibriumReactor','GibbsReactor'],
        validation='tests_v3/validate_idaes.py',provenance=dict(implementation='idaes_adapter.py'))


def list_modules():
    return [dict(module_id=k, version=v['version'], capability=v['capability'][:100]) for k, v in MODULES.items()]


def describe_module(module_id):
    return copy.deepcopy(MODULES[module_id])


def _field(unit, path):
    for part in path.split('.'):
        unit = unit.get(part) if isinstance(unit, dict) else None
    return unit


def applicability(module_id, unit):
    warnings = []
    for p in MODULES[module_id]['applicability_domain']:
        v, op = _field(unit, p['field']), p['op']
        numeric = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        ok = (v == p['value'] if op == 'eq' else bool(v) if op == 'present' else
              numeric and (v > 0 if op == 'positive' else v >= 0 if op == 'nonnegative' else 0 <= v <= 1 if op == 'unit_interval' else 0 < v <= 1))
        if not ok:
            warnings.append(f"{module_id}: applicability {p['field']} {op} {p['value']} (got {v})")
    return warnings


def experimental_path(ws, name):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', name):
        raise ValueError('invalid experimental module name')
    root = (Path(ws)/'modules').resolve()
    path = root/(name+'.py')
    if path.is_symlink() or path.resolve().parent != root or root != Path(ws).resolve()/'modules':
        raise ValueError('module must be a local regular file')
    return path


def validate_module(ws, name):
    path = experimental_path(ws, name)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory(prefix='module-validation-') as tmp:
        target = Path(tmp)/'module.py'
        target.write_bytes(raw)
        env = {k: v for k, v in os.environ.items() if k in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP')}
        env['PYTHONUTF8'] = '1'
        try:
            p = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--sandbox', str(target)],
                               cwd=tmp, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
            result = json.loads(p.stdout) if p.returncode == 0 else dict(passed=False, reasons=[(p.stderr or p.stdout or 'subprocess failed')[-700:]])
        except (subprocess.TimeoutExpired, ValueError) as exc:
            result = dict(passed=False, reasons=[str(exc)[:500]])
    result.update(name=name, source_sha256=digest, promotion_candidate=bool(result.get('passed')),
                  status='experimental', validator_version='1.0')
    path.with_suffix('.validation.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    return dict(name=name, passed=result['passed'], promotion_candidate=result['promotion_candidate'],
                reasons=result.get('reasons', [])[:3], artifact=f'modules/{name}.validation.json')


def coverage(ws, out):
    blocks, warnings, rows = [], [], []
    totals = dict(energy=0., cooling=0., capex=0.)
    verified = dict(totals)
    for u in out.get('physics', {}).get('units', []):
        name = str(u.get('name', '?'))
        amounts = dict(energy=u.get('purchased_energy_GJ_per_t', 0), cooling=u.get('cooling_duty_GJ_per_t', 0), capex=u.get('capex_usd', 0))
        if not any(amounts.values()):
            continue
        ids = u.get('computed_by')
        ok = isinstance(ids, list) and bool(ids) and all(isinstance(x, str) for x in ids)
        all_verified = ok
        if not ok:
            blocks.append(name+': nonzero energy/cooling/capex requires computed_by list')
            ids = []
        for mid in ids:
            if mid in MODULES:
                warnings.extend(name+': '+w for w in applicability(mid, u))
            elif mid.startswith('experimental:'):
                all_verified = False
                try:
                    path = experimental_path(ws, mid.split(':', 1)[1])
                    val = json.loads(path.with_suffix('.validation.json').read_text(encoding='utf-8'))
                    if not val.get('passed') or val.get('source_sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
                        raise ValueError('not validated on current source')
                    warnings.append(name+': experimental module '+mid)
                except (OSError, ValueError) as exc:
                    blocks.append(name+': '+mid+': '+str(exc))
            else:
                blocks.append(name+': unregistered module '+mid)
                all_verified = False
        if u.get('type') == 'separation' and 'unitops.split' in ids and not u.get('energy_method'):
            blocks.append(name+': split is mass-balance only; separation requires energy_method')
        for k, v in amounts.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                blocks.append(name+': invalid '+k)
                continue
            totals[k] += v
            if all_verified:
                verified[k] += v
        rows.append(dict(name=name, computed_by=ids, verified=bool(all_verified)))
    return dict(passed=not blocks, blocks=blocks, warnings=warnings,
                coverage={k: verified[k]/v if v else 1. for k, v in totals.items()},
                totals=totals, verified_totals=verified, units=rows)


def _sandbox(path):
    """Disposable subprocess: deny network, child processes and file mutation via audit hooks."""
    import contextlib
    import io
    def audit(event, args):
        if event.startswith(('socket.', 'subprocess.', 'ctypes.', 'os.spawn', 'os.exec')) or event in (
                'os.system', 'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink'):
            raise PermissionError('sandbox: '+event)
        if event == 'open':
            mode, flags = args[1:3]
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)):
                raise PermissionError('sandbox: write')
    sys.addaudithook(audit)
    try:
        scope = {'__name__': 'experimental', '__file__': str(path)}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(path.read_bytes(), str(path), 'exec'), scope)
            meta = scope['META']
            for k in ('inputs', 'outputs', 'units', 'assumptions', 'applicability'):
                if not meta.get(k):
                    raise ValueError('META missing '+k)
            if not isinstance(meta['inputs'], dict) or not isinstance(meta['outputs'], dict) or not isinstance(meta['units'], dict):
                raise ValueError('inputs/outputs/units must be mappings')
            if any(not meta['units'].get(k) for k in (*meta['inputs'], *meta['outputs'])):
                raise ValueError('unit keys missing')
            cases = scope['tests']()
            if not isinstance(cases, list) or not {'conservation', 'limit', 'reference'} <= {c['kind'] for c in cases}:
                raise ValueError('tests must return conservation, limit and reference cases')
            for case in cases:
                a = scope['compute'](**case['inputs'])
                b = scope['compute'](**case['inputs'])
                if json.dumps(a, sort_keys=True, allow_nan=False) != json.dumps(b, sort_keys=True, allow_nan=False):
                    raise ValueError('repeat determinism failed')
                if not isinstance(a, dict) or not set(meta['outputs']) <= set(a):
                    raise ValueError('output keys missing')
                def check(value, key=''):
                    if isinstance(value, dict):
                        for k, v in value.items(): check(v, k)
                    elif isinstance(value, (list, tuple)):
                        for v in value: check(v, key)
                    elif isinstance(value, (int, float)):
                        if not math.isfinite(value) or (any(s in key.lower() for s in ('energy', 'power', 'cooling')) and value < 0):
                            raise ValueError('nonfinite or negative energy: '+key)
                check(a)
                for key, unit in meta['outputs'].items():
                    value = a[key]
                    if not isinstance(value, (int, float, dict, list, tuple)) or isinstance(value, bool):
                        raise ValueError('scientific outputs must be numeric: '+key)
                    if meta['units'][key] == 'GJ/t' and isinstance(value, (int,float)) and value < 0:
                        raise ValueError('negative energy: '+key)
        return dict(passed=True, reasons=[], cases=len(cases))
    except BaseException as exc:
        return dict(passed=False, reasons=[f'{type(exc).__name__}: {exc}'[:700]])


if __name__ == '__main__' and sys.argv[1] == '--sandbox':
    print(json.dumps(_sandbox(Path(sys.argv[2]))))
