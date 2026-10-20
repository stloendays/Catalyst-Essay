"""Keestra substitution on the independent PR-loop T3 code path.

220 bar: hold the published T3 pair's conversion, separator and purge fixed.
90 bar: same cached cold-state grid at -20 C, temperatures 400/425/445/450 C;
compare the canonical cost model at the selected PR operating points.
"""
import sys,time,json
from dataclasses import replace
import numpy as np
from scipy.optimize import brentq
import keestra_common as Q
Q.tee('pr_loop_check');t0=time.time()
FR,S,h,st,M,mf,mr,kaap,anchors=Q.gate()
S.rate_fe_m3=Q.rate_fe_m3
sys.path.insert(0,str(Q.AN/'nh3_loop_reconciliation_2026_10_14'))
import common,canonical as CAN,closed_loop as CL,kinetic_bridge as KB,cold_worker
orig=KB.rate_m3; original_validity=KB.validity
def rate(cat,T,P,flow,activity=1.):
    if cat!='Fe': return orig(cat,T,P,flow,activity)
    y=np.asarray(flow)/np.asarray(flow).sum(axis=-1,keepdims=True)
    return activity*Q.rate_fe_m3(T,P,y[...,0],y[...,1],y[...,4])
def validity(cat,T,P,flow):
    d=original_validity(cat,T,P,flow)
    if cat=='Fe':
        d['rate_P_inside_source_range']=1<=P<=324
        d['rate_domain']='Keestra KM1R-1964; pressure in fitted range' if 1<=P<=324 else 'Keestra pressure extrapolation'
    return d
KB.rate_m3=rate;KB.validity=validity;KB.DENSITY['Fe']=Q.KF.BED_DENSITY
up=json.loads((Q.AN/'nh3_loop_reconciliation_2026_10_14/outputs/upstream_93_94.json').read_text())
cache=json.loads((Q.AN/'nh3_loop_reconciliation_2026_10_14/outputs/cold_states.json').read_text())
def state(P,X,Ts,pg):
    rec=cold_worker.job((P,X,Ts,pg,CL.TARGET_TPD))
    sid=CL.RS.grid_key(P,X,Ts,pg)
    return dict(state_id=sid,P_bar=P,X=X,T2_C=Ts,purge=pg,record=rec)
fixed={}
for cat,d in up['u93']['selected'].items():
    if cat not in ('Fe','Ru'):continue
    fixed[cat]=state(d['P_bar'],d['X_design'],d['T2_C'],d['purge'])
rows220={cat:CL.size_candidates({d['state_id']:d},temps=(425.,)) for cat,d in fixed.items()}
rows220={cat:next(r for r in rr if r['catalyst']==cat) for cat,rr in rows220.items()}
states90={d['state_id']:d for d in cache['designs'] if d['P_bar']==90 and d['T2_C']==-20 and d.get('record')}
assert len(states90)==len(CL.GRID['X'])*len(CL.GRID['purge'])
rows90=CL.size_candidates(states90,temps=(400.,425.,445.,450.))
def fixed220(rate):
    e=replace(CL.B93,metal_rate=rate)
    return {cat:CL.describe((r,CL.price(r,fixed[cat]['record'],e)),{fixed[cat]['state_id']:fixed[cat]}) for cat,r in rows220.items()}
def best90(rate):
    e=replace(CL.B93,metal_rate=rate)
    return {cat:CL.describe(CL.best(rows90,states90,e,cat),states90) for cat in ('Fe','Ru')}
def canonical_at(pair,rate):
    return {cat:CAN.canonical_point_costs(h,(d['T_C'],d['P_bar'],d['T2_C']),cat,fin_rate=rate) for cat,d in pair.items()}
def gap(pair):return pair['Ru']['total_USD_t']-pair['Fe']['total_USD_t']
def root(f):
    a,b=f(0.),f(.30)
    return brentq(f,0.,.30,xtol=1e-11) if a*b<0 else None
out={}
for label,fun in [('425C_220bar_fixed_T3_pair',fixed220),('KAAP_90bar_m20C_grid_optimum',best90)]:
    pair=fun(.12);can=canonical_at(pair,.12)
    closed_root=root(lambda r:gap(fun(r)))
    # Canonical break-even at the 12% PR-selected points, exactly the common-point comparison.
    canonical_root=root(lambda r:gap(canonical_at(pair,r)))
    records={c:(fixed[c]['record'] if label.startswith('425') else states90[pair[c]['state_id']]['record']) for c in pair}
    if label.startswith('KAAP'):
        for c,d in pair.items():
            live=cold_worker.job((90.,d['X'],-20.,d['purge'],CL.TARGET_TPD))
            assert np.allclose(live['feed_kmol_h'],records[c]['feed_kmol_h'],rtol=1e-8)
            records[c]=live
    forward={}
    for c,d in pair.items():
        rec=records[c]
        f=KB.forward_bed(c,d['T_C']+273.15,d['P_bar'],rec['feed_kmol_h'],d['bed_m3'])
        relative=f['extent_kmol_h']/rec['extent_kmol_h']-1
        assert abs(relative)<1e-6,(c,relative)
        forward[c]=dict(relative_extent_error=relative,extent_kmol_h=f['extent_kmol_h'],within_90m3=d['bed_m3']<=90)
    residual={c:{k:v for k,v in rec.items() if any(s in k.lower() for s in ('resid','error','closure','converg'))} for c,rec in records.items()}
    out[label]=dict(PR=pair,canonical=can,PR_gap=gap(pair),canonical_gap=gap(can),PR_break_even=closed_root,canonical_break_even=canonical_root,reactor_delta=pair['Ru']['reactor']-pair['Fe']['reactor'],inventory_delta=pair['Ru']['inventory']-pair['Fe']['inventory'],closure=residual,forward_check=forward,scope='fixed-state cost-model consistency; Ru/C extrapolated at 220 bar; Fe bed exceeds 90 m3 cap' if label.startswith('425') else 'both pressure ranges fitted; 400-450 C grid; PR optima reselected with financing')
    print(label, json.dumps(Q.clean(out[label]),indent=1),flush=True)
Q.dump('pr_loop_results.json',dict(comparisons=out,seconds=time.time()-t0),12)
Q.dump('pr_loop_cold_records.json',dict(fixed220=fixed,KAAP90=states90),12)
Q.dump('pr_loop_sizing.json',dict(fixed220=rows220,KAAP90=rows90),12)
print('seconds',time.time()-t0)
