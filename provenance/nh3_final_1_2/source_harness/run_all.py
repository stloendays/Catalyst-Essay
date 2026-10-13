from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from harness_core import NH3Harness, sha256_file


def load_cfg(path: Path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))


CANONICAL_CONFIG = 'configs/nh3_final_1_2.yaml'
NON_FROZEN_KEYS = {'project.run_label', 'project.scientific_scope', 'numerics.response_workers', 'numerics.cache_response_matrix'}


def _flat(d, prefix=''):
    out = {}
    for k, v in d.items():
        key = f'{prefix}.{k}' if prefix else k
        out.update(_flat(v, key)) if isinstance(v, dict) else out.__setitem__(key, v)
    return out


def manifest_integrity(cfg: dict, root: Path) -> list[dict]:
    """Return the list of FROZEN keys that differ from the canonical manifest (empty = identical)."""
    canon = load_cfg(root / CANONICAL_CONFIG)
    a, b = _flat(canon), _flat(cfg)
    return [{'key': k, 'canonical': a.get(k), 'run': b.get(k)}
            for k in sorted(set(a) | set(b)) if k not in NON_FROZEN_KEYS and a.get(k) != b.get(k)]


def compare(actual, expected, tol):
    return abs(float(actual)-float(expected)) <= tol


def regression_checks(cfg, det, mc=None, back=None):
    f=cfg['frozen_regression']; g=cfg['gates']; checks=[]
    def add(name,actual,expected,tol):
        ok=compare(actual,expected,tol); checks.append({'name':name,'actual':actual,'expected':expected,'tolerance':tol,'pass':ok})
    add('process_state_count',det['process_state_count'],f['process_state_count'],0)
    add('raw_global_spearman',det['raw_global_spearman'],f['raw_global_spearman'],g['spearman_abs_tolerance'])
    add('censored_global_spearman',det['censored_global_spearman'],f['censored_global_spearman'],g['spearman_abs_tolerance'])
    add('top3_spearman',det['rolling'][0]['rho_raw'],f['top3_spearman'],g['spearman_abs_tolerance'])
    for m in ('Fe','Ru','Os'):
        add(f'{m}_cost_USD_t',det['metals'][m]['feasible']['total_cost'],f[f'{m}_cost_USD_t'],g['headline_abs_tolerance'])
        for key in ('T_C','P_bar','Tsep_C'):
            add(f'{m}_optimum_{key}',det['metals'][m]['feasible'][key],f[f'{m}_optimum'][key],1e-12)
    checks.append({'name':'activity_order','actual':det['activity_order'],'expected':cfg['atomic_reference']['activity_order_expected'],'pass':det['activity_order']==cfg['atomic_reference']['activity_order_expected']})
    checks.append({'name':'feasible_metals','actual':det['feasible_economic_order'],'expected':f['feasible_metals'],'pass':det['feasible_economic_order']==f['feasible_metals']})
    if mc is not None:
        add('Fe_feasibility_probability',mc['Fe_feasibility_probability'],f['Fe_feasibility_probability'],g['feasibility_abs_tolerance'])
    if back is not None:
        add('Ru_activity_break_even_multiplier',back['Ru_activity_break_even_multiplier'],f['Ru_activity_break_even_multiplier'],1e-6)
        add('Ru_scaling_max_gain_673K',back['Ru_scaling_max_gain_673K'],f['Ru_scaling_max_gain_673K'],1e-8)
        add('Ru_scaling_max_gain_all_states',back['Ru_scaling_max_gain_all_states'],f['Ru_scaling_max_gain_all_states'],1e-7)
        add('Ru_best_scaling_cost_USD_t',back['Ru_best_scaling_cost_USD_t'],f['Ru_best_scaling_cost_USD_t'],1e-7)
    return checks


def main():
    ap=argparse.ArgumentParser(description='One-command runner for Catalyst Economic Leverage / NH3-FINAL-1.2 (copy of the NH3-FINAL-1.1 runner; only the default config differs)')
    ap.add_argument('--config',default='configs/nh3_final_1_2.yaml')
    ap.add_argument('--mode',choices=['smoke','full'],default='smoke',help='smoke = deterministic + regression; full = response cache + 1000 MC + backward reachability')
    ap.add_argument('--force-response',action='store_true')
    ap.add_argument('--run-id',default=None)
    ap.add_argument('--scenario',action='store_true',help='acknowledge that this manifest deviates from canonical (registered scenario run, never a canonical result)')
    args=ap.parse_args()

    root=Path(__file__).resolve().parent; cfg_path=(root/args.config).resolve(); cfg=load_cfg(cfg_path)
    drift=manifest_integrity(cfg,root)
    if drift and not args.scenario:
        print('[preflight] MANIFEST INTEGRITY FAIL — frozen keys differ from', CANONICAL_CONFIG)
        for d in drift: print(f"    {d['key']}: canonical={d['canonical']!r} run={d['run']!r}")
        print('    Re-run with --scenario to register this as a scenario, or bump project.model_version via PROMOTE_CANONICAL.')
        sys.exit(3)
    run_id=args.run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    outdir=root/'outputs'/f"{cfg['project']['run_label']}_{run_id}"; outdir.mkdir(parents=True,exist_ok=False)
    resolved=outdir/'manifest_resolved.yaml'; resolved.write_text(yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True),encoding='utf-8')

    print(f"[1/6] preflight: {cfg['project']['model_version']} / mode={args.mode}")
    h=NH3Harness(cfg,root)
    print(f"[2/6] process library: {h.NSTATE} valid states")
    print('[3/6] deterministic 15-metal propagation')
    d=h.deterministic(); d['process_state_count']=h.NSTATE
    mc=None; back=None; cache_info=None
    if args.mode=='full':
        print('[4/6] response surface + 1000-draw uncertainty')
        response,cp,was_cached=h.build_or_load_response(force=args.force_response); cache_info={'path':str(cp.relative_to(root)),'sha256':sha256_file(cp),'reused':was_cached,'shape':list(response.shape)}
        mc=h.monte_carlo(response)
        print('[5/6] backward design + scaling reachability')
        back=h.backward_and_reachability(response)
    else:
        print('[4/6] response surface skipped in smoke mode')
        print('[5/6] MC/backward skipped in smoke mode')

    checks=regression_checks(cfg,d,mc,back); passed=all(x['pass'] for x in checks)
    result={'project':cfg['project'],'run_id':run_id,'mode':args.mode,'status':'PASS' if passed else 'FAIL','is_scenario':bool(args.scenario),'manifest_drift_from_canonical':drift,'deterministic':d,'monte_carlo':mc,'backward_reachability':back,'regression_checks':checks,'response_cache':cache_info}
    (outdir/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    provenance={'created_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'config':str(cfg_path.relative_to(root)),'config_sha256':sha256_file(cfg_path),'inputs':{'activity_workbook':{'path':str(h.input_path.relative_to(root)),'sha256':sha256_file(h.input_path)}},'model_version':cfg['project']['model_version'],'process_state_count':h.NSTATE,'response_cache':cache_info,'is_scenario':bool(args.scenario),'manifest_drift_from_canonical':drift}
    (outdir/'provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=[f"# Run {run_id}",f"- Status: **{result['status']}**"+(" (SCENARIO — not canonical)" if args.scenario else ""),f"- Mode: `{args.mode}`",f"- Model: `{cfg['project']['model_version']}`",f"- Process states: {h.NSTATE}",f"- Activity ranking: {' > '.join(d['activity_order'])}",f"- Feasible economic ranking: {' > '.join(d['feasible_economic_order'])}",f"- Fe / Ru / Os costs: {d['metals']['Fe']['feasible']['total_cost']:.12f} / {d['metals']['Ru']['feasible']['total_cost']:.12f} / {d['metals']['Os']['feasible']['total_cost']:.12f} USD/t",f"- Top-3 Spearman: {d['rolling'][0]['rho_raw']}"]
    if mc: lines += [f"- Fe feasibility (1000 draws): {mc['Fe_feasibility_probability']:.6f}"]
    if back: lines += [f"- Ru activity break-even: {back['Ru_activity_break_even_multiplier']:.6f}x",f"- Scaling headroom @673K: {back['Ru_scaling_max_gain_673K']:.9f}x",f"- Max scaling headroom across process states: {back['Ru_scaling_max_gain_all_states']:.9f}x",f"- Best strict-scaling Ru cost: {back['Ru_best_scaling_cost_USD_t']:.12f} USD/t"]
    lines += ['','## Regression checks']+[f"- {'PASS' if x['pass'] else 'FAIL'} — {x['name']}: actual={x['actual']} expected={x['expected']}" for x in checks]
    (outdir/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    latest=root/'outputs'/'LATEST.txt'; latest.write_text(str(outdir.relative_to(root))+'\n',encoding='utf-8')
    print('[6/6] regression gate:',result['status'])
    print('output:',outdir)
    if not passed and cfg['gates'].get('fail_on_regression',True): sys.exit(2)

if __name__=='__main__': main()
