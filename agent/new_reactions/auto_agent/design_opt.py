"""V3.5 generic design declarations, decisions and bounded deterministic search."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

PROMPT = """
V3.5 design optimisation: declare every free pressure, temperature, recovery, purge,
split, stage count or other design choice as type=design in sources.csv, with value,
low, high, unit and note; PARAMS must read these at call time. An assumption with a
design-like key needs a note of at least 40 characters explaining why the process fixes it.
After model_checks call optimize_design, adopt its optimum by editing sources.csv and
rerun check_model, or record a decision explaining non-adoption. Compare at least two
separation options with unitops-computed energy_GJ_per_t and capex_usd before choosing.
For separation (and reactor when alternatives are listed), record alternatives as objects
with name, energy_GJ_per_t, capex_usd, chosen (boolean); mark exactly one chosen.
Deliver product at basis.product[species].P_bar. Plant-level costs use a sourced scale exponent
or 0.6-0.9; exponents outside 0.5-0.95 require measured/published exponent_evidence.
"""

def enabled(h):
    return getattr(h, 'build_version', '').startswith('V3.5')

def source_failures(rows):
    failures = []
    for row in rows:
        key = row.get('parameter', '')
        typ = row.get('type', '').strip().lower()
        if typ == 'assumption' and ('_K' in key or any(t in key.lower() for t in
                ('_bar', 'pressure', 'temperature', 'recovery', 'purge', 'split'))):
            if len((row.get('note') or '').strip()) < 40:
                failures.append(f'{key}: free design choice must be type=design, or note >=40 characters explaining why process-fixed')
        if typ == 'design':
            try:
                lo, v, hi = (float(row[k]) for k in ('low', 'value', 'high'))
                if not all(math.isfinite(x) for x in (lo, v, hi)) or not lo <= v <= hi:
                    raise ValueError()
                if not row.get('unit') or not (row.get('note') or '').strip():
                    raise ValueError()
            except (KeyError, TypeError, ValueError):
                failures.append(f'{key}: design requires finite low <= value <= high, unit and note')
    return failures

def decision_failures(decisions):
    failures = []
    # A revised decision supersedes the previous one on the same topic.
    latest = {d.get('topic'): d for d in decisions}
    for topic in ('separation', 'reactor'):
        d = latest.get(topic, {})
        alts = d.get('alternatives')
        if topic == 'reactor' and not alts:
            continue
        valid = isinstance(alts, list) and len(alts) >= 2
        if valid:
            for a in alts:
                if not isinstance(a, dict) or not a.get('name') or not isinstance(a.get('chosen'), bool):
                    valid = False
                    break
                for k in ('energy_GJ_per_t', 'capex_usd'):
                    v = a.get(k)
                    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                        valid = False
            valid = valid and len({a['name'] for a in alts}) == len(alts) and sum(a['chosen'] for a in alts) == 1
        if not valid:
            failures.append(f'{topic}: require >=2 named alternatives with unitops-computed energy_GJ_per_t, capex_usd and exactly one chosen=true')
    return failures


def optimize(ws):
    """Runs in the tool subprocess, never writes the model or source register."""
    import importlib.util
    import sys
    import contextlib
    import io
    import numpy as np
    from scipy.optimize import minimize
    from physics_gate import check_physics
    ws = Path(ws)
    rows = list(csv.DictReader((ws / 'sources.csv').open(encoding='utf-8')))
    errors = source_failures(rows)
    if errors:
        raise ValueError('; '.join(errors))
    variables = [r for r in rows if r['type'].strip().lower() == 'design']
    keys = [r['parameter'] for r in variables]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate design parameter')
    low = np.array([float(r['low']) for r in variables])
    high = np.array([float(r['high']) for r in variables])
    x0 = np.array([float(r['value']) for r in variables])
    sys.path.insert(0, str(ws))
    spec = importlib.util.spec_from_file_location('design_model', ws / 'model.py')
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    for k, v in zip(keys, x0):
        if k not in m.PARAMS or not math.isclose(float(m.PARAMS[k]), v, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(k + ': PARAMS differs from design source value')
    basis = json.loads((ws / 'basis.json').read_text(encoding='utf-8'))
    flow = json.loads((ws / 'flowsheet.json').read_text(encoding='utf-8'))
    cache, best, rejected = {}, None, []
    class Budget(Exception):
        pass
    def evaluate(z):
        nonlocal best
        z = np.clip(np.asarray(z, dtype=float), 0, 1)
        x = low + z * (high-low)
        key = tuple(float(v) for v in x)
        if key in cache:
            return cache[key]['objective']
        if len(cache) >= 40:
            raise Budget()
        entry = dict(values=dict(zip(keys, key)), feasible=False, objective=1e100)
        cache[key] = entry
        try:
            m.PARAMS.update(entry['values'])
            with contextlib.redirect_stdout(io.StringIO()):
                out = m.reference()
                failures = check_physics(m, out, flow, basis=basis, ledger=True, design=True)
            metrics = dict(cost_usd_per_t=float(out['cost_usd_per_t']),
                           energy_GJ_per_t=float(out['balances']['energy_GJ_per_t']),
                           capex_usd=float(out['balances']['capex_usd']))
            if not all(math.isfinite(v) and v >= 0 for v in metrics.values()) or metrics['cost_usd_per_t'] <= 0:
                raise ValueError('invalid objective/energy/capex')
            entry.update(metrics)
            if failures:
                raise ValueError('; '.join(failures[:3]))
            entry.update(feasible=True, objective=metrics['cost_usd_per_t'])
            if best is None or entry['objective'] < best['objective']:
                best = entry
        except Exception as exc:
            rejected.append(dict(values=entry['values'], reason=str(exc)[:300]))
        return entry['objective']
    z0 = np.divide(x0-low, high-low, out=np.zeros_like(x0), where=high!=low)
    evaluate(z0)
    start = next(iter(cache.values())).copy()
    if keys:
        # Coordinate low/mid/high starts, deterministic and linear in dimension.
        starts = [z0, np.full(len(keys), .5)]
        for i in range(len(keys)):
            for v in (0., .5, 1.):
                z = z0.copy(); z[i] = v; starts.append(z)
        try:
            for z in starts[:min(12, max(2, 20//max(1, len(keys))))]:
                evaluate(z)
            seeds = sorted(cache.values(), key=lambda e: e['objective'])[:3]
            for seed in seeds:
                x = np.array(list(seed['values'].values()))
                z = np.divide(x-low, high-low, out=np.zeros_like(x), where=high!=low)
                minimize(evaluate, z, method='L-BFGS-B', bounds=[(0, 1)]*len(keys),
                         options=dict(maxfun=max(1, (40-len(cache))//len(seeds)), ftol=1e-12, gtol=1e-7))
        except Budget:
            pass
    def public(e):
        return {k:v for k,v in e.items() if k != 'objective'} if e else None
    result = dict(status='ok' if best else 'no_feasible_point', start=public(start), optimum=public(best),
                  evaluations=len(cache), rejected_points=rejected, variables_at_bound=[k for i,k in enumerate(keys)
                  if best and (math.isclose(best['values'][k], low[i], abs_tol=1e-7) or
                               math.isclose(best['values'][k], high[i], abs_tol=1e-7))])
    (ws / 'design_opt.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    return result


def run_tool(ws):
    import subprocess
    import sys
    command = [sys.executable, str(Path(__file__).resolve()), str(Path(ws).resolve())]
    p = subprocess.run(command, cwd=ws, capture_output=True, text=True, encoding='utf-8', timeout=840)
    if p.returncode:
        return json.dumps(dict(error=(p.stderr or p.stdout)[-1500:]))
    result = json.loads((Path(ws) / 'design_opt.json').read_text(encoding='utf-8'))
    # Compact summary; full variable maps and rejected points remain in the artifact.
    summary = {k:v for k,v in result.items() if k != 'rejected_points'}
    summary['rejected_count'] = len(result['rejected_points'])
    text = json.dumps(summary, separators=(',', ':'))
    if len(text) > 3000:
        summary = dict(status=result['status'], evaluations=result['evaluations'],
                       rejected_count=len(result['rejected_points']), detail='read design_opt.json',
                       start_cost=(result['start'] or {}).get('cost_usd_per_t'),
                       optimum_cost=(result['optimum'] or {}).get('cost_usd_per_t'))
    return json.dumps(summary, separators=(',', ':'))

if __name__ == '__main__':
    import sys
    optimize(Path(sys.argv[1]))
