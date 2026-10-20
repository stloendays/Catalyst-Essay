"""Owned-metal and unsecured supplier-lease curves, measured in-range laws."""
import sys, time, csv, json, statistics
import numpy as np
from scipy.optimize import brentq
import keestra_common as Q
Q.tee('financing'); t0=time.time()
FR,S,h,st,M,mf,mr,kaap,anchors=Q.gate()
import boundary as B
L=B.load_library(Q.INRANGE/'staged_KM1R_1964_design_library.csv')
def write(name,rows):
    with (Q.HERE/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Extend missing Ru-first patterns from the committed global-optimization seeds.
import run_staged as RS
extra_path=Q.HERE/'staged_Ru_first_library.csv'
if not extra_path.exists():
    seeds=list(csv.DictReader((Q.INRANGE/'staged_KM1R_1964_arrangements.csv').open(encoding='utf-8')))
    extra=[]
    for pat in ('RFF','RRF'):
        starts=[[float(v) for v in r['x'].split(';')] for r in seeds if r['pattern']==pat]
        prev=starts[0]
        for rate in np.linspace(0,.12,25):
            econ=Q.C.Econ(accounting='dcf',recovery=.9555,fin_rate=float(rate),fe_kinetics=Q.FE_KEY)
            loop=Q.C.Loop(P_bar=90.,Tsep_C=-20.,inerts=.08)
            r=Q.C.optimize(tuple('Ru' if c=='R' else 'Fe' for c in pat),loop,econ,de=False,x0=prev,restarts=starts,nm_maxfev=1500)
            prev=r['x']; d=RS.record(r,dict(pattern=pat,tag={'fin_rate':rate}),loop,0)
            d={k:v for k,v in d.items() if k not in ('beds','x')}
            ch=B.charges(53852.5,.9555,float(rate)); d.update(c_Ru=ch[0],c_Fe=ch[1])
            extra.append(d)
        print('Ru-first continuation done',pat,flush=True)
    write('staged_Ru_first_library.csv',extra)
L.update(B.load_library(extra_path))
def pair(rate,mask): return FR.pair(M,M.fe_cf(rate),M.ruc_cf(rate),mf & mask,mr & mask)
rows=[]
for rate in np.linspace(0,.12,241):
    b=pair(rate,np.ones(h.NSTATE,bool));k=pair(rate,kaap)
    ch=B.charges(53852.5,.9555,float(rate))
    costs={pat:B.env_at(L,(90.,-20.),pat,*ch)[0] for p,ts,pat in L}
    first=min(('FFR','FRR'),key=costs.get)
    reverse=[p for p in ('RFF','RRF','RFR') if p in costs]
    assert reverse, 'Ru-first envelope absent from committed library'
    rev=min(reverse,key=costs.get)
    best=min(costs,key=costs.get)
    rows.append(dict(financing_rate=rate,financing_rate_pct=100*rate,benchmark_RuC_minus_Fe=b['gap'],KAAP_RuC_minus_Fe=k['gap'],staged_all_Fe=costs['FFF'],staged_Fe_first=costs[first],staged_Fe_first_pattern=first,staged_all_RuC=costs['RRR'],staged_Ru_first=costs[rev],staged_Ru_first_pattern=rev,staged_optimal=best,staged_optimal_cost=costs[best]))
write('financing_curves.csv',rows)
sys.path.insert(0,str(Q.AN/'nh3_ru_metal_financing_evidence_2026_10_12'))
from supplier_metal_contracts_pr61 import SupplierMetalTerms,supplier_metal_multiplier
source=Q.AN/'nh3_ru_metal_financing_evidence_2026_10_12'
contracts=list(csv.DictReader((source/'pbf_catalyst_lease_contracts.csv').open(encoding='utf-8')))
rates=[float(r['annual_rate_pct']) for r in contracts]
computed=dict(pbf_min=min(rates),pbf_median=statistics.median(rates),pbf_max=max(rates))
def lease(rate,mask):
    terms=SupplierMetalTerms(project_y=25,catalyst_life_y=10,project_discount_rate=.12,gross_recovery=.9555,annual_fee_fraction=rate)
    mult=supplier_metal_multiplier(terms,S.P_RU,10)
    V=M.ru_M/(S.W*S.RHO)
    ru=M.cost(V,M.ru_M,S.P_RU,mult)[0]
    return FR.pair(M,M.fe_cf(.12),(ru,V),mf & mask,mr & mask)
doc=[]
for r in csv.DictReader((source/'documented_rates.csv').open(encoding='utf-8')):
    val=computed.get(r['rate_id'],float(r['rate_pct']) if r['rate_pct'] else None)
    for label,mask in [('benchmark',np.ones(h.NSTATE,bool)),('KAAP',kaap)]:
        d=None if val is None else lease(val/100,mask)
        own=None if val is None else pair(val/100,mask)
        doc.append(dict(rate_id=r['rate_id'],rate_pct='' if val is None else val,category=r['category'],source_id=r['source_id'],loop=label,convention='lease_unsecured',Fe_USD_t='' if d is None else d['Fe']['cost'],RuC_USD_t='' if d is None else d['Ru']['cost'],gap_USD_t='' if d is None else d['gap'],owned_gap_USD_t='' if own is None else own['gap'],note=r['note']))
write('documented_rates_measured.csv',doc)
ratesout={}
for label,mask in [('benchmark',np.ones(h.NSTATE,bool)),('KAAP',kaap)]:
    ratesout[label+'_owned']=FR.breakeven_fin(M,mf & mask,mr & mask)['rate']
    ratesout[label+'_lease_unsecured']=brentq(lambda r:lease(r,mask)['gap'],0,.30,xtol=1e-12)
# same crossing extraction as staged_inrange.window, including library upper-bound qualification
x=np.array([r['financing_rate'] for r in rows])
ratesout['staged_all_Ru_optimal_below']=B._crossing(x,np.array([r['staged_all_RuC']-min(r['staged_all_Fe'],r['staged_Fe_first'],r['staged_Ru_first']) for r in rows]))
ratesout['staged_Fe_first_beats_Fe_below']=B._crossing(x,np.array([r['staged_Fe_first']-r['staged_all_Fe'] for r in rows]))
Q.dump('financing_summary.json',dict(breakevens=ratesout,staged_patterns=sorted(costs),seconds=time.time()-t0),10)
print(ratesout, 'seconds',time.time()-t0)
