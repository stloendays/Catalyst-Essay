#!/usr/bin/env python3
"""Compute a matched-capacity Fe/Ru kinetic/cold-loop economic comparison.

Engineering exploration, not a reclassification of the old industrial score.
Coarse shared grid -> kinetic feasibility -> common economic basis -> candidate
optima -> independent forward fixed-bed recycle check. All exclusions retained.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,time,subprocess,sys,os
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace,asdict
from itertools import product
from pathlib import Path
import numpy as np
from scipy.optimize import brentq

import coupling as C
from economics import EconomicSettings

GRID={'P_bar':[100.,160.,188.,220.], 'T_C':[400.,425.,450.],
      'X':[.14,.20,.275,.35], 'T2_C':[0.], 'purge':[.015,.03]}


def native(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    raise TypeError(str(type(value)))


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,default=native,allow_nan=False)+'\n',encoding='utf-8')


def csv_write(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k,v in r.items() if not isinstance(v,(dict,list))))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for row in rows:w.writerow({k:row.get(k,'') for k in fields})


def grid_key(p,x,t2,pg):return f'P{p:g}_X{x:g}_T2{t2:g}_pg{pg:g}'


def best(rows,cat):
    good=[r for r in rows if r['catalyst']==cat and r.get('feasible')]
    return min(good,key=lambda r:r['decision_relevant_cost_USD_t']) if good else None


def retally(designs,e=EconomicSettings(),activity_ru=1.):
    rows=[]
    for d in designs:
        if not d.get('record'):continue
        s=C.cold_settings(d['P_bar'],d['X'],d['T2_C'],d['purge'])
        for T in GRID['T_C']:
            for cat in ['Fe','Ru']:
                r=C.candidate(cat,T,d['P_bar'],s,d['record'],e,activity=activity_ru if cat=='Ru' else 1.)
                r['state_id']=d['state_id'];rows.append(r)
    return rows


def rescore_rows(base,states,e,activity_ru=1.):
    """Exact inverse-PFR uniform activity scaling: required V -> V/activity."""
    from economics import evaluate
    from kinetic_bridge import DENSITY,RU_WT,hot_heat_per_mol_NH3
    rows=[]
    for r0 in base:
        if 'bed_m3' not in r0:continue
        r=dict(r0);cat=r['catalyst'];alpha=activity_ru if cat=='Ru' else 1.
        V=r0['bed_m3']/alpha
        if V>e.max_bed_m3:continue
        f=dict(states[r['state_id']]['record'])
        f['isothermal_reaction_heat_removed_MW']=-f['extent_kmol_h']/3.6*hot_heat_per_mol_NH3(r['T_C']+273.15)/1e6
        r.update(evaluate(cat,V,r['P_bar'],f,e));r.update(bed_m3=V,feasible=True,activity_factor=alpha)
        rows.append(r)
    return rows


def cold_subprocess(d,target):
    cmd=[sys.executable,str(Path(__file__).with_name('cold_worker.py'))]
    cmd += [str(d[k]) for k in ['P_bar','X','T2_C','purge']]+[str(target)]
    try:
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        cp=subprocess.run(cmd,text=True,capture_output=True,timeout=20,env=env)
        if cp.returncode:raise RuntimeError(cp.stderr[-600:])
        result=json.loads(cp.stdout.splitlines()[-1]);d.update(result)
    except subprocess.TimeoutExpired:
        d.update(record=None,reason='NUMERICAL_BUDGET_20_SECONDS: unresolved case, not physical impossibility')
    except Exception as error:
        d.update(record=None,reason=type(error).__name__+': '+str(error))
    return d


def run(outdir,quick=False,batch_cold=0,retry_unresolved=False):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    e=EconomicSettings();start=time.time();designs=[]
    pressures=GRID['P_bar'] if not quick else [100.,188.]
    cache=outdir/'cold_cache.json'
    signature=hashlib.sha256(json.dumps({'grid':GRID,'quick':quick,'target':e.product_tpd},sort_keys=True).encode()).hexdigest()
    old=json.loads(cache.read_text()) if cache.exists() else {}
    byid={r['state_id']:r for r in old.get('designs',[])} if old.get('signature')==signature else {}
    tasks=[]
    for P,X,T2,pg in product(pressures,GRID['X'],GRID['T2_C'],GRID['purge']):
        sid=grid_key(P,X,T2,pg)
        if sid in byid and (byid[sid].get('record') or not retry_unresolved):
            designs.append(byid[sid]);continue
        tasks.append({'state_id':sid,'P_bar':P,'X':X,'T2_C':T2,'purge':pg})
    remaining_tasks=len(tasks)
    if batch_cold:tasks=tasks[:batch_cold]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(cold_subprocess,d,e.product_tpd) for d in tasks]
        for future in as_completed(futures):
            designs.append(future.result())
            dump(cache,{'signature':signature,'designs':designs})
            print('cold states',len(designs),'seconds',round(time.time()-start,1),flush=True)
    designs.sort(key=lambda d:(d['P_bar'],d['X'],d['T2_C'],d['purge']))
    dump(cache,{'signature':signature,'designs':designs})
    if batch_cold and remaining_tasks>batch_cold:
        print('PARTIAL: cache saved; pending',remaining_tasks-batch_cold,flush=True)
        return {'pending':remaining_tasks-batch_cold}
    rows=retally(designs,e);states={d['state_id']:d for d in designs}
    good=[r for r in rows if r['feasible']]
    selected={cat:best(rows,cat) for cat in ['Fe','Ru']}
    if any(v is None for v in selected.values()):raise RuntimeError('No feasible common-grid candidate for at least one catalyst')
    checks=[]
    for cat,b in selected.items():
        d=states[b['state_id']];record=d['record'];s=C.cold_settings(d['P_bar'],d['X'],d['T2_C'],d['purge'])
        print('selected',cat, {k:b[k] for k in ['T_C','P_bar','X_design','T2_C','purge','bed_m3','decision_relevant_cost_USD_t']},flush=True)
        # Deliberately change the unused legacy setting: forward calculation
        # must produce its own X, independent of Settings.conversion.
        forwarded=C.forward_closed_loop(cat,b['T_C'],replace(s,conversion=.11),b['bed_m3'],record['scale_to_equal_product'],
                                       np.asarray(record['feed_kmol_h'])*.8)
        forwarded['inverse_design_X']=d['X'];forwarded['actual_vs_target_tpd_error']=forwarded['calculated_NH3_tpd']-e.product_tpd
        if abs(forwarded['calculated_X_N2']-d['X'])>2e-6:raise AssertionError('Forward-inverse reactor consistency failed')
        if abs(forwarded['actual_vs_target_tpd_error'])>.02:raise AssertionError('Forward rate/loop does not meet designed product')
        checks.append(forwarded)
    finance=[]
    for rate,recovery in product([0.,.12],[.90,.9555,.99]):
        altered=replace(e,metal_rate=rate,ru_recovery=recovery)
        scored=rescore_rows(rows,states,altered)
        bf,br=best(scored,'Fe'),best(scored,'Ru')
        finance.append({'metal_finance_rate':rate,'Ru_recovery':recovery,
            'Fe_USD_t':bf['decision_relevant_cost_USD_t'],'Ru_USD_t':br['decision_relevant_cost_USD_t'],
            'Ru_minus_Fe_USD_t':br['decision_relevant_cost_USD_t']-bf['decision_relevant_cost_USD_t'],
            'winner':'Fe' if bf['decision_relevant_cost_USD_t']<br['decision_relevant_cost_USD_t'] else 'Ru',
            'Fe_state':bf['state_id'],'Ru_state':br['state_id']})
    feed_sens=[]
    for hp in [1.,2.,4.]:
        scored=rescore_rows(rows,states,replace(e,H2_USD_kg=hp))
        bf,br=best(scored,'Fe'),best(scored,'Ru')
        feed_sens.append({'H2_USD_kg':hp,'Fe_USD_t':bf['decision_relevant_cost_USD_t'],
            'Ru_USD_t':br['decision_relevant_cost_USD_t'],'Ru_minus_Fe':br['decision_relevant_cost_USD_t']-bf['decision_relevant_cost_USD_t']})
    target=selected['Fe']['decision_relevant_cost_USD_t']
    def parity_gap(logalpha):
        scored=rescore_rows(rows,states,e,10**logalpha)
        r=best(scored,'Ru')
        return r['decision_relevant_cost_USD_t']-target if r else 1e5
    ga,gb=parity_gap(-2),parity_gap(3)
    if ga*gb<0:
        alpha=10**brentq(parity_gap,-2,3,xtol=1e-6)
        parity={'uniform_Ru_measured_rate_multiplier_for_grid_parity':alpha,
                'improvement_required_from_base':alpha>1.,'Fe_target_USD_t':target,
                'scope':'uniform Rossetti formulation rate multiplier; NOT DFT descriptor/scaling reachability'}
    else:parity={'no_parity_bracket_in_alpha_0p01_to_1000':True}
    def finance_gap(rate):
        scored=rescore_rows(rows,states,replace(e,metal_rate=rate))
        return best(scored,'Ru')['decision_relevant_cost_USD_t']-best(scored,'Fe')['decision_relevant_cost_USD_t']
    fa,fb=finance_gap(0.),finance_gap(.20)
    finance_threshold={'scope':'inventory annualization rate only, equipment annualization fixed at 12%; both candidates reoptimized'}
    if fa*fb<0:finance_threshold['crossover_rate']=brentq(finance_gap,0.,.20,xtol=1e-8)
    else:finance_threshold['no_crossover_in_0_to_20pct']=True
    # Different candidate choices from process optimization vs utility-only
    # demonstrate why complete cost boundary matters.
    utilityonly={c:min((r for r in good if r['catalyst']==c),key=lambda r:r['utility_USD_t']) for c in ['Fe','Ru']}
    stats={'cold_states':len(designs),'cold_operable':sum(bool(d['record']) for d in designs),
           'cold_failures':sum(not bool(d['record']) for d in designs),'candidate_rows':len(rows),
           'feasible_Fe':sum(r['feasible'] and r['catalyst']=='Fe' for r in rows),
           'feasible_Ru':sum(r['feasible'] and r['catalyst']=='Ru' for r in rows),
           'cold_max_material_error':max(d['record']['component_residual_rel_fresh'] for d in designs if d['record']),
           'cost_decomposition_max_error_USD_t':max(abs(r['feed_cost_decomposition_residual_USD_t']) for r in good)}
    summary={'model':'NH3-KINETIC-COST-v1','study_status':'conditional_engineering_grid_results',
             'stats':stats,'grid':GRID,'economic_settings':asdict(e),'selected':selected,
             'forward_fixed_bed_checks':checks,'finance_reoptimized':finance,
             'H2_price_reoptimized':feed_sens,'rate_parity':parity,'finance_crossover':finance_threshold,
             'utility_only_selection':utilityonly,
             'preserved':'upstream PR92, NH3-FINAL-1.2 32/64 and original headline numbers unchanged',
             'main_limitations':['No joint experimentally fitted Fe/Ru pressure range in these two rate laws; extrapolation labels mandatory.',
             'Single isothermal plug-flow bed and specified pressure losses, not detailed adiabatic multi-bed hydraulics.',
             'Measured 3.2 wt% Ru/C formulation versus KM1 iron, not bare-metal descriptor ordering.',
             'Reported optimum is on the listed finite grid; active grid bounds do not establish global optimum.',
             'Reduced loop cost excludes detailed exchanger/separator/piping capital and default unpriced hot thermal integration.'],
             'runtime_seconds':time.time()-start}
    for cat,b in selected.items():
        b['grid_edge_coordinates']=[k for k,key in [('P_bar','P_bar'),('T_C','T_C'),('X_design','X'),('T2_C','T2_C'),('purge','purge')]
                                    if b[k] in (GRID[key][0],GRID[key][-1])]
    dump(outdir/'summary.json',summary);csv_write(outdir/'candidate_grid.csv',rows)
    csv_write(outdir/'finance_scenarios.csv',finance);csv_write(outdir/'H2_price_scenarios.csv',feed_sens)
    dump(outdir/'forward_checks.json',checks)
    lines=['# NH3 kinetic / SI-loop / economic coupling v1','',
        'Source Fe KM1 and 3.2 wt% promoted Ru/C rate laws now determine the required bed. '
        'Each catalyst is optimized separately on the same process grid at 1500 t/d actual liquid NH3. '
        'Selected beds are independently solved forward inside recycle feedback; conversion is NOT supplied to that forward solver.',
        '',f"Computed {stats['cold_states']} cold states ({stats['cold_failures']} numerical/phase failures), "
        f"{stats['candidate_rows']} candidate designs; feasible Fe {stats['feasible_Fe']}, Ru {stats['feasible_Ru']}.",'',
        '| Catalyst | T C | P bar | X | T2 C | Purge | Bed m3 | Decision cost USD/t | Gate-to-liquid modeled USD/t |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cat,b in selected.items():
        lines.append(f"| {cat} | {b['T_C']:.0f} | {b['P_bar']:.0f} | {b['X_design']:.3f} | {b['T2_C']:.0f} | {b['purge']:.3f} | {b['bed_m3']:.3f} | {b['decision_relevant_cost_USD_t']:.3f} | {b['modeled_loop_cost_USD_t']:.3f} |")
    lines+=['','## Cost decomposition: same denominator, no double charging feed','',
            '| Catalyst | Excess feed | Utilities | Catalyst | Reactor capital | Compressor capital |','|---|---:|---:|---:|---:|---:|']
    for cat,b in selected.items():lines.append(f"| {cat} | {b['excess_feed_USD_t']:.3f} | {b['utility_USD_t']:.3f} | {b['inventory_USD_t']:.3f} | {b['reactor_annualized_USD_t']:.3f} | {b['compressor_annualized_USD_t']:.3f} |")
    lines+=['',f"Common stoichiometric-feed baseline {selected['Fe']['stoichiometric_feed_USD_t']:.3f} USD/t is subtracted only for the decision-relevant objective; full delivered makeup is charged exactly once.",
            'Hydrogen/nitrogen/methane prices (2/0.10/0.20 USD per kg) are declared engineering scenarios, not market quotes.',
            '','## Independent fixed-bed forward-loop verification','']
    for q in checks:lines.append(f"{q['catalyst']}: predicted X {q['calculated_X_N2']:.6f}, product {q['calculated_NH3_tpd']:.6f} t/d; residual {q['material_residual_relative']:.2e}. No prescribed conversion is used in the forward calculation.")
    lines+=['','## Finance and recovery: reoptimized both formulations','',
        '| Metal finance | Ru recovery | Fe cost | Ru cost | Ru minus Fe | Winner |','|---|---:|---:|---:|---:|---|']
    for r in finance:lines.append(f"| {r['metal_finance_rate']:.2f} | {r['Ru_recovery']:.4f} | {r['Fe_USD_t']:.3f} | {r['Ru_USD_t']:.3f} | {r['Ru_minus_Fe_USD_t']:+.3f} | {r['winner']} |")
    lines+=['','Inventory finance crossover: '+json.dumps(finance_threshold,default=native),'','Rate parity: '+json.dumps(parity,default=native),'','## Boundaries']+['- '+s for s in summary['main_limitations']]
    lines+=['','The supplied SI temperature correlations describe the cold section only; they are not extrapolated into the hot reactor. '
             'The original NH3-FINAL-1.2 and historical 32/64 benchmark remain unchanged. This is a new, conditional formulation-level comparison.','']
    text='\n'.join(lines);(outdir/'REPORT.md').write_text(text,encoding='utf-8');print(text,flush=True)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);p.add_argument('--quick',action='store_true');p.add_argument('--batch-cold',type=int,default=0);p.add_argument('--retry-unresolved',action='store_true')
    a=p.parse_args();run(a.out_dir,a.quick,a.batch_cold,a.retry_unresolved)
