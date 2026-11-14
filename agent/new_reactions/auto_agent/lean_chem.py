"""Generic V3.4 build scaffolding; no reaction data or gate policy."""
from __future__ import annotations
import hashlib
import json
import re
import uuid
from collections import Counter
from pathlib import Path

PROMPT = """\nV3.4 lean tools: use workspace_digest to re-orient (basis, units, checks, ledgers, debt,
critique and stage notes). read_file skips unchanged already-visible slices; force=true rereads.
Use resolve_debts / respond_critiques to batch existing actions. After flowsheet acceptance,
model_skeleton.py is optional editable scaffolding: fill TODO numbers and sources before use.
Stage tool menus are scoped; change stage to access its tools. Soft turn reminders ask you to wrap up.
Call set_stage only when the stage changes; do not repeat the current stage. After every change to model.py the
harness imports it and runs reference(); fix a reported error before anything else. Edit model.py by rewriting whole
functions, not by substring replacement of variable names.
"""
CRITIC_ADDENDUM = """
Report only engineering issues that change a number: mass, energy or element balances, thermodynamic feasibility, duties
of compression, heating, cooling and separation, utility accounting, capital basis and scaling, battery limits. Do not
report wording, formatting, table layout or documentation gaps; the harness checks file formats itself."""

def enabled(h):
    return getattr(h, 'build_version', '').startswith('V3.4')

def read_file(h, path, start, n, force=False):
    p = h.path(path)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    key = (str(p.resolve()), max(0, start), min(n, 400))
    cache = h.__dict__.setdefault('_read_cache', {})
    previous = cache.get(key)
    history = getattr(h, '_history', None)
    visible = previous and (history is None or any(
        it.get('call_id') == previous['call_id'] and 'older output masked' not in it.get('output', '')
        and '[truncated' not in it.get('output', '')
        for it in history if it.get('type') == 'function_call_output'))
    if not force and previous and previous['sha'] == sha and visible:
        return f"unchanged since turn {previous['turn']} (sha {sha[:16]}); content is in your history or use digest"
    cache[key] = dict(sha=sha, turn=getattr(h, '_turn', 0), call_id=getattr(h, '_call_id', None))
    lines = raw.decode('utf-8', errors='replace').splitlines()
    return f'[{len(lines)} lines]\n' + '\n'.join(lines[max(0, start):max(0, start) + min(n, 400)])

HINTS = {
    'cooling_utility': 'use unitops.cooling_utility',
    'separation_pressure': 'use unitops.separator_energy with actual stream pressures',
    'capital_double_count': 'apply installed cost and plant shares once; do not rescale shares by internal flow',
    'capital_scaling': 'use unitops.scaled_capex from source capacity to model capacity',
    'zero_duty': 'supply evidence for zero duty or calculate the missing utility',
    'exothermic_preheat': 'recover available heat before buying preheat; account for furnace duty',
    'compressor_upper': 'use unitops.compressor with boundary inlet state and staged compression',
    'boundary_feed_state': 'use the temperature and pressure declared in basis feeds',
}

def diagnosis(failures):
    result = {}
    for check, messages in failures.items():
        if not messages:
            continue
        # b_check_model adds one record tag before the unchanged gate message.
        counts = Counter(messages)
        result[check] = [dict(message=msg, count=count, hint=next(
            (hint for prefix, hint in HINTS.items() if prefix in msg),
            'inspect the named check, its required fields and source evidence'))
            for msg, count in counts.items()]
    return result

def digest(h):
    def load(name):
        try:
            return json.loads((h.ws / name).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}
    def compact(value, limit):
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=str)
        return text if len(text) <= limit else text[:limit] + ' ...[more: read_file]'
    flow, check = load('flowsheet.json'), load('model_check.json')
    roles = unit_roles(flow)
    sections = {
        'basis': compact(load('basis.json'), 1500),
        'units': compact([dict(name=u.get('name'), type=u.get('type'), role=roles.get(u.get('name')))
                          for u in flow.get('units', [])], 600),
        'last_check': compact(dict(passed=check.get('passed'), failures=check.get('diagnosis', check.get('failures', {}))), 1100),
        'open_debt': compact([x for x in load('evidence_debt.json').get('items', []) if x.get('status') == 'open'], 600),
        'open_critique': compact([x for r in load('critique.json').get('rounds', []) for x in r.get('issues', []) if not x.get('response')], 600),
        'stage_notes': compact(getattr(h, 'stage_notes', [])[-8:], 600),
    }
    for name in ('energy_ledger.csv', 'capex_ledger.csv'):
        try:
            sections[name] = '\n'.join((h.ws / name).read_text(encoding='utf-8').splitlines()[:5])[:500]
        except OSError:
            sections[name] = 'absent'
    return '\n'.join(k + ': ' + v for k, v in sections.items())

ROLE_MAP = dict(feed_preparation='feed_conditioning', reactor_heat_supply_or_removal='reaction',
                catalyst_regeneration='reaction', product_compression='product_conditioning',
                separation_and_purification='separation', recycle='recycle', heat_recovery='heat_integration',
                utilities_and_offsites='offsites')

def unit_roles(flow):
    roles = {}
    for category, entry in flow.get('checklist', {}).items():
        for name in entry.get('included', []):
            roles.setdefault(name, ROLE_MAP.get(category, 'offsites'))
    return roles

def skeleton(flow):
    roles = unit_roles(flow)
    lines = ['"""Optional model scaffold. TODO: supply sourced values; None is never a physical zero."""',
             'import unitops', 'REACTION = {}  # TODO stoichiometry, key, product, MW',
             'PARAMS = {}  # TODO call-time parameters with source paths', '']
    names = []
    for i, u in enumerate(flow['units']):
        fn = f"unit_{i}_" + re.sub(r'[^a-zA-Z0-9_]', '_', u['name'])
        names.append(fn)
        typ, role = u['type'], roles.get(u['name'], 'offsites')
        fields = dict(name=u['name'], type=typ, boundary_role=role, capex_usd=None,
                      purchased_energy_GJ_per_t=None, internal_fuel_GJ_per_t=None, capex_basis=dict(method='size_based', cost_year=None,
                      installed=True, installation_factor=1, source_cost_usd=None, source_capacity=None,
                      scale_exponent=None, size_basis='TODO source equipment capacity basis'))
        if typ == 'compressor':
            call = "unitops.compressor(**p['compressor'])"
            fields.update(kmol_per_t=None, T_in_K=None, P_in_bar=None, P_out_bar=None)
        elif typ == 'separation':
            call = "unitops.separator_energy(**p['separator_energy'])"
            fields.update(feed=dict(mol_frac={}, kmol_per_t=None, P_bar=None),
                          outlets=[dict(mol_frac={}, kmol_per_t=None, P_bar=None)], T_K=None,
                          power_GJ_per_t=None, energy_method='unitops.separator_energy')
        elif typ == 'knockout' or (typ == 'heat_exchanger' and role != 'heat_integration'):
            call = "unitops.cooling_utility(**p['cooling_utility'])"
            fields.update(service='cooling', cooling_duty_GJ_per_t=None, cooling_medium=None, T_process_out_K=None)
        elif typ == 'furnace':
            fields.update(duty_GJ_per_t=None, purchased_fuel_GJ_per_t=None, efficiency=None)
            call = "unitops.fired_heater(**p['fired_heater'])"
        elif role == 'heat_integration':
            fields.update(recovered_heat_GJ_per_t=None, hot_duty_GJ_per_t=None, cold_duty_GJ_per_t=None)
            call = "unitops.heat_recovery(**p['heat_recovery'])"
        elif role == 'recycle':
            call = "unitops.recycle_loop(**p['recycle_loop'])"
        else:
            call = None
        lines += [f'def {fn}(p):', '    # TODO p supplies sourced numbers and utility/capital assumptions.',
                  f'    unit = {fields!r}']
        if call:
            lines += [f'    unit.update({call})']
        if typ == 'separation':
            lines += ["    product, tail = unitops.split(**p['split'])  # TODO wire actual streams"]
        lines += ["    # TODO choose sourced equipment scaling OR an already scaled plant cost share.",
                  "    if 'plant_cost_share' in p:", "        unit.update(unitops.plant_cost_share(**p['plant_cost_share']))",
                  "    else:", "        unit['capex_usd'] = unitops.scaled_capex(**p['scaled_capex'])",
                  "        unit['capex_basis'] = p['capex_basis']", '    return unit', '']
    lines += ['UNIT_FUNCTIONS = [' + ', '.join(names) + ']']
    return '\n'.join(lines) + '\n'

ALWAYS = {'read_file', 'write_file', 'set_stage', 'finish', 'workspace_digest'}
LITERATURE = {'search_papers', 'screen_papers', 'download_papers', 'ocr_papers', 'extract_papers', 'check_records', 'extract_records'}
MODEL = {'check_model', 'run_python', 'check_atomic', 'record_decision'}

def stage_tools(tools, stage):
    allowed = set(ALWAYS)
    if stage in ('search', 'screening', 'download_ocr', 'extraction'):
        allowed |= LITERATURE | {'web_search'}
    elif stage in ('mechanism_kinetics', 'parameters'):
        allowed |= {'web_search', 'record_decision', 'run_python', 'check_records'}
    elif stage == 'reactor_flowsheet':
        allowed |= {'web_search', 'submit_flowsheet', 'record_decision', 'run_python'}
    elif stage in ('model_code', 'model_checks', 'atomic_model'):
        allowed |= MODEL
    elif stage == 'feedback':
        allowed |= MODEL | {'assess_assumptions', 'resolve_debt', 'resolve_debts', 'request_critique', 'respond_critique', 'respond_critiques'}
    elif stage in ('analysis', 'report'):
        allowed |= {'run_analysis', 'run_sensitivity', 'run_three_optima', 'run_python', 'check_model'}
    return [t for t in tools if t.get('name', t.get('type')) in allowed]

GROUPS = {**{s: ('literature', 40) for s in ('search', 'screening', 'download_ocr', 'extraction', 'mechanism_kinetics')},
          'reactor_flowsheet': ('flowsheet', 15), 'parameters': ('parameters', 25),
          **{s: ('model_code+checks', 40) for s in ('model_code', 'model_checks', 'atomic_model')},
          'feedback': ('feedback', 20), **{s: ('analysis+report', 25) for s in ('analysis', 'report')}}

def turn_warning(h):
    group, limit = GROUPS[h.stage]
    counts = h.__dict__.setdefault('_stage_turns', Counter())
    counts[group] += 1
    warned = h.__dict__.setdefault('_stage_warned', set())
    if counts[group] >= limit and group not in warned:
        warned.add(group)
        return f'Soft stage budget: {group} has used {counts[group]} turns (budget {limit}); wrap this stage up and move on. No hard stop.'
    return None

class ExtractionCache:
    def __init__(self, root):
        self.root = Path(root)

    def path(self, pdf, prompt, model):
        # Include the rendered extraction input/schema in the prompt hash to invalidate OCR/figure changes.
        parts = [hashlib.sha256(pdf.read_bytes()).hexdigest(), hashlib.sha256(prompt.encode()).hexdigest(), model]
        return self.root / (hashlib.sha256(json.dumps(parts).encode()).hexdigest() + '.json')

    def get(self, path):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            return data if isinstance(data.get('records'), list) else None
        except (OSError, ValueError, AttributeError):
            return None

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.' + uuid.uuid4().hex + '.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        temp.replace(path)


def extract_papers(h, reaction, key, product, cofeed, scope):
    """Cache wrapper around the unchanged standard extraction implementation."""
    import full_mode
    chain = full_mode.chain
    cache = ExtractionCache(getattr(h, 'extraction_cache_root', r'D:\agent_runs\_extraction_cache'))
    system = chain.EXTRACT_PROMPT.format(reaction=reaction, key=key, product=product, cofeed=cofeed or 'none', scope=scope)
    pending, paths, hits = [], {}, []
    for md in sorted((h.ws / 'ocr').glob('*.md')):
        out = h.ws / 'extracted' / (md.stem + '.json')
        if out.exists():
            continue
        pdf = next((p for p in sorted((h.ws / 'pdf').glob('*.pdf')) if p.stem[:60] == md.stem), None)
        if pdf:
            figs_path = md.with_name(md.stem + '_figs.json')
            figs = json.loads(figs_path.read_text(encoding='utf-8'))
            chosen = [f for f in figs if f['caption'] and any(w in f['caption'].lower() for w in chain.PERF)][:8]
            images = [(f, hashlib.sha256((md.parent / (md.stem + '_figs') / f['file']).read_bytes()).hexdigest())
                      for f in chosen if (md.parent / (md.stem + '_figs') / f['file']).exists()]
            prompt = json.dumps([system, chain.SCHEMA, md.read_text(encoding='utf-8'), images, 'medium'], sort_keys=True)
            path = cache.path(pdf, prompt, h.extract_model)
            paths[md.stem] = path
            data = cache.get(path)
            if data is not None:
                data['_meta'] = dict(data.get('_meta', {}), tokens_in=0, tokens_out=0, seconds=0, cache_hit=True)
                out.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                h.log(dict(extraction_cache_hit=md.stem, cache_key=path.stem))
                hits.append(dict(paper=md.stem, cache_hit=True, n_records=len(data['records'])))
                continue
        pending.append(md.stem)
    rows = []
    if pending:
        rows = chain.extract(h.ws, lambda: h.extract_router.client, h.extract_model, reaction, key, product, cofeed, scope,
                             stems=pending, workers=min(h.extract_workers, 8), usage_csv=h.ws / 'token_usage_extract.csv')
    for row in rows:
        if 'prompt_tokens' in row:
            h.tok['extract_in'] += row['prompt_tokens']
            h.tok['extract_out'] += row['completion_tokens']
            h.tok['extract_calls'] += 1
            if row['paper'] in paths:
                cache.put(paths[row['paper']], json.loads((h.ws / 'extracted' / (row['paper'] + '.json')).read_text(encoding='utf-8')))
    return json.dumps(hits + rows)
