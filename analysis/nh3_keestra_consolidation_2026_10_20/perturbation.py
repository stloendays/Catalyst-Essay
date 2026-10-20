"""Exact registered error-perturbation design, measured branch only, pressure masks on both catalysts.

Default uses upgraded benchmark deviations. --historical-magnitudes isolates the
rate-law change with the original error-table magnitudes held fixed.
"""
import sys,time,itertools,json,math
import numpy as np
import keestra_common as Q
historical='--historical-magnitudes' in sys.argv
tag='perturbation_historical_magnitudes' if historical else 'perturbation'
Q.tee(tag);t0=time.time()
FR,S,h,st,M,mf,mr,kaap,anchors=Q.gate()
sys.path.insert(0,str(Q.AN/'nh3_benchmark_error_table_2026_10_19'))
import run_error_table as E
S.rate_fe_m3=Q.rate_fe_m3
def evaluate(lib,comp=1.,kin=('Fe',1.),dT=0.):
    h=lib.h;pc=h.state_process_cost;h.state_process_cost=lib.process_cost(comp)
    try:
        fv,rm=lib.amounts(dT);mode,f=kin;fv=fv*f;rm=rm*(f if mode=='all' else 1.)
        fm,rr=Q.inrange_masks(h.state_P);km=(h.state_P==90)&(h.state_Tsep==-20)
        ft=S.costs(h,fv,fv*h.ACTIVE_FRACTION*h.BED_DENSITY,E.hc.PRICE['Fe'],S.multiplier('benchmark',0,0))[0]
        vb=rm*S.U/(h.ACTIVE_FRACTION*h.BED_DENSITY)
        rb=S.costs(h,vb,rm*S.U,S.P_RU,1.)[0]
        out={'bulk benchmark':(E._opt(h,ft,fv,fm),E._opt(h,rb,vb,rr))}
        vs=rm/(S.W*S.RHO)
        for rate in (0.,.12):
            fi=S.costs(h,fv,fv*h.ACTIVE_FRACTION*h.BED_DENSITY,E.hc.PRICE['Fe'],S.multiplier('cashflow',0,rate))[0]
            ri=S.costs(h,vs,rm,S.P_RU,S.multiplier('cashflow',.9555,rate))[0]
            for label,mask in [('benchmark',np.ones(h.NSTATE,bool)),('KAAP',km)]:
                out[f'{label} supported {rate:g}']=(E._opt(h,fi,fv,fm & mask),E._opt(h,ri,vs,rr & mask))
        return out
    finally: h.state_process_cost=pc
base=E.Library();r0=evaluate(base)
Q.check('own path Fe',r0['bulk benchmark'][0]['cost'],anchors['Fe_benchmark'])
Q.check('own path bulk Ru',r0['bulk benchmark'][1]['cost'],anchors['Ru_bulk_benchmark'])
for label,prefix in [('benchmark',''),('KAAP','KAAP_')]:
    for rate,suffix in [(0.,'0'),(.12,'12')]:
        Q.check('own path gap',E.gap(r0[f'{label} supported {rate:g}']),anchors[prefix+'RuC_minus_Fe_'+suffix])
table=E.build_error_table() if historical else E.rows(Q.HERE/'error_table.csv')
mag=E.magnitudes(table);Q.dump(tag+'_magnitudes.json',mag,10)
comps=['SEP','APP','COMP','KIN','TBED']
scenarios=[dict(name='baseline',kind='baseline',mag='',signs={},kin_mode='Fe')]
for mode in ('Fe','all'):
    for sign in (1,-1): scenarios.append(dict(name=f'KIN {mode} {sign} max_plant_sizing',kind='single',mag='max_plant_sizing',signs={'KIN':sign},kin_mode=mode))
for magnitude in ('typical','max'):
    for c in comps:
        for mode in (('Fe','all') if c=='KIN' else ('Fe',)):
            for sign in (1,-1): scenarios.append(dict(name=f'{c} {mode} {sign} {magnitude}',kind='single',mag=magnitude,signs={c:sign},kin_mode=mode))
    for signs in itertools.product((1,-1),repeat=5):
        for mode in ('Fe','all'): scenarios.append(dict(name=f'joint {signs} {mode} {magnitude}',kind='corner',mag=magnitude,signs=dict(zip(comps,signs)),kin_mode=mode))
groups={}
for s in scenarios:
    s['params']=(1.,None,1.,('Fe',1.),0.) if s['kind']=='baseline' else E.scenario_params(mag,s['mag'],s['signs'],s['kin_mode'])
    groups.setdefault(s['params'][:2],[]).append(s)
rows=[]
for (sep,app),ss in groups.items():
    lib=base if (sep,app)==(1.,None) else E.Library(sep,app)
    for s in ss:
        _,_,comp,kin,dt=s['params'];s['res']=evaluate(lib,comp,kin,dt)
        for label,pair in s['res'].items():
            gap=E.gap(pair);baseline=E.gap(r0[label])
            rows.append(dict(scenario=s['name'],kind=s['kind'],magnitude=s['mag'],kin_mode=s['kin_mode'],signs=json.dumps(s['signs']),comparison=label,Fe_cost=E._c(pair[0]),Ru_cost=E._c(pair[1]),gap=gap,shift=gap-baseline,Fe_opt=E._o(pair[0]),Ru_opt=E._o(pair[1])))
    print('library',sep,app,'scenarios',len(ss),'elapsed_s',time.time()-t0,flush=True)
    if lib is not base: del lib
E.write_csv(Q.HERE/(tag+'_results.csv'),rows)
summary={}
for label in r0:
    baseline=E.gap(r0[label]); singles=[s for s in scenarios if s['kind']=='single'];corners=[s for s in scenarios if s['kind']=='corner']
    d=dict(baseline=baseline,min_single_margin=min(E.gap(s['res'][label]) for s in singles),min_combination_margin=min(E.gap(s['res'][label]) for s in corners),n_single_Ru_ahead=sum(E.gap(s['res'][label])<0 for s in singles),n_singles=len(singles),magnitudes={})
    for magnitude in ('typical','max'):
        ss=[s for s in singles if s['mag']==magnitude];gg=[E.gap(s['res'][label]) for s in ss]
        fav={};mode='Fe'
        for c in comps:
            candidates=[s for s in ss if c in s['signs']]
            best=min(candidates,key=lambda s:E._key(E.gap(s['res'][label])))
            fav[c]=best['signs'][c]
            if c=='KIN':mode=best['kin_mode']
        joint=next(s for s in corners if s['mag']==magnitude and s['signs']==fav and s['kin_mode']==mode)
        d['magnitudes'][magnitude]=dict(single_shift_min=min(gg)-baseline,single_shift_max=max(gg)-baseline,n_single_Ru_ahead=sum(g<0 for g in gg),n_singles=len(gg),joint_Ru_favouring_gap=E.gap(joint['res'][label]),joint_Ru_favouring_shift=E.gap(joint['res'][label])-baseline,joint_scenario=joint['name'],min_corner_gap=min(E.gap(s['res'][label]) for s in corners if s['mag']==magnitude),n_corners_Ru_ahead=sum(E.gap(s['res'][label])<0 for s in corners if s['mag']==magnitude))
    summary[label]=d
Q.dump(tag+'_summary.json',dict(comparisons=summary,magnitudes=mag,seconds=time.time()-t0),10)
print(json.dumps(Q.clean(summary),indent=1));print('seconds',time.time()-t0)
