"""An operable steady-state cold-section/recycle engineering scenario.

Flow order is explicitly chosen: reactor -> 21 C flash -> purge -> delivered
makeup -> 0 C flash -> compression -> reactor. This is not a claim that the
complete original plant piping has been independently established. Recovered
H2 is included in delivered stream12 outside this main-loop control volume.
Reactor N2 conversion is a specified process input, not predicted catalyst
kinetics. No SI cold-section kij(T) is extrapolated to the hot reactor.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import csv, math
from pathlib import Path
import numpy as np
from scipy.optimize import root
from model import State, NU, MW, fractions, compression

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'nh3_source_matched_loop_v0'/'figure57_streams.csv'


def source_streams():
    with SOURCE.open(newline='',encoding='utf-8') as f:
        raw=list(csv.DictReader(f))
    return {int(r['stream_id']):r for r in raw}


def source_flow(r):
    z=np.array([float(r[k+'_molpct']) for k in ('N2','H2','CH4','Ar','NH3')])/100
    return float(r['flow_kmol_h'])*z


@dataclass(frozen=True)
class Settings:
    T1:float=294.15
    T2:float=273.15
    P1:float=18.02e6
    P2:float=17.88e6
    P_reactor:float=18.8e6
    conversion:float=.275
    purge:float=.03
    methane_k:float=0.
    mode:str='si2024'
    compressor_eta:float=.75
    refrigerator_COP:float=2.5
    power_USD_MWh:float=50.
    def __post_init__(self):
        if not 0<self.conversion<1 or not 0<self.purge<1:raise ValueError('Conversion and purge must lie in (0,1)')
        if not self.P_reactor>=self.P1>=self.P2>0:raise ValueError('Inconsistent pressure order')
        if self.T2>self.T1 or self.refrigerator_COP<=0:raise ValueError('Invalid cold-section temperatures/COP')


def solve(settings=Settings(), initial=None, check_stability=True):
    s=settings
    refs=source_streams()
    fresh=source_flow(refs[12])
    f1=State(s.T1,s.P1,s.methane_k,s.mode)
    f2=State(s.T2,s.P2,s.methane_k,s.mode)
    target_scale=float(fresh.sum())
    def advance(feed):
        # Extent is mol NH3/h and H2 availability is enforced, no clipping to
        # negative amounts when recycle composition changes.
        extent=min(2*s.conversion*feed[0], (2/3)*feed[1]*(1-1e-10))
        reactor_out=feed+NU*extent
        if np.min(reactor_out)<-1e-8:raise RuntimeError('Negative reactor output')
        vapor1,liquid1,a=f1.split(np.maximum(reactor_out,0))
        purge=s.purge*vapor1
        vapor_to_mix=vapor1-purge
        stage2_feed=vapor_to_mix+fresh
        vapor2,liquid2,b=f2.split(stage2_feed)
        return vapor2, dict(extent=extent,reactor_out=reactor_out,gas1=vapor1,liq1=liquid1,
            purge=purge,mix=stage2_feed,liq2=liquid2,a=a,b=b,vapor_to_mix=vapor_to_mix)
    if initial is None:
        start=fresh/max(s.conversion,0.1)
        start[2:4]=fresh[2:4]/max(s.purge,0.005)
    else:
        start=np.asarray(initial,dtype=float)
    start=start.copy();start[4]=max(start[4],.04*start.sum())
    evaluations=0
    def equations(logfeed):
        nonlocal evaluations
        evaluations+=1
        feed=np.exp(np.clip(logfeed,-15,20))
        nxt,_=advance(feed)
        return (nxt-feed)/target_scale
    opt=root(equations,np.log(np.maximum(start,1e-9)),method='hybr',options={'xtol':2e-8,'maxfev':350})
    feed=np.exp(np.clip(opt.x,-15,20))
    nxt,data=advance(feed)
    err=float(np.max(np.abs(nxt-feed))/target_scale)
    if err>1e-8:
        # Safeguarded Picard fallback; never silently return the last iterate.
        for _ in range(1400):
            nxt,data=advance(feed)
            err=float(np.max(np.abs(nxt-feed))/target_scale)
            if err<1e-9:break
            feed=.4*feed+.6*nxt
        else:raise RuntimeError(f'Closed loop did not converge: residual {err}')
    checks=[]
    if check_stability:
        for state,comp,r in ((f1,data['reactor_out'],data['a']),(f2,data['mix'],data['b'])):
            if r.phase=='two_phase':
                plane=np.log(np.maximum(r.x,1e-300))+state.properties(r.x,'liquid')[1]
                q=state.stability(comp,plane,[r.x,r.y,fractions(comp)])
                if q['minimum_tpd']<-1e-6:raise RuntimeError('Final phase split failed TPD screening')
                checks.append(q['minimum_tpd'])
            else:
                q=state.stability(comp)
                if q['minimum_tpd']<-1e-6:raise RuntimeError('Final single phase failed TPD screening')
                checks.append(q['minimum_tpd'])
    products=data['liq1']+data['liq2']
    mass_res=fresh+NU*data['extent']-products-data['purge']
    product_t_h=float(products[4])*MW[4]/1000
    if product_t_h<=0:raise RuntimeError('No saleable liquid ammonia')
    comp_rec=compression(feed,s.T2,s.P2,s.P_reactor,s.methane_k,s.mode,s.compressor_eta)
    # Keep source10 and source11 separate pressure-work boundaries; their
    # delivered mixture is the stream12 fresh boundary for the process loop.
    comp_make=[compression(source_flow(refs[k]),float(refs[k]['temperature_C'])+273.15,
                float(refs[k]['pressure_MPa'])*1e6,float(refs[12]['pressure_MPa'])*1e6,
                s.methane_k,s.mode,s.compressor_eta) for k in (10,11)]
    compression_MW=comp_rec['shaft_MW']+sum(q['shaft_MW'] for q in comp_make)
    # Nonreactive second-stage cooling balance with internally consistent
    # PR residual enthalpy, including the derivative of SI kij(T).
    H=lambda state,flow,phase:0. if sum(flow)<1e-14 else float(sum(flow))*state.properties(flow,phase)[2]*1000/3600/1e6
    makeup_state=State(float(refs[12]['temperature_C'])+273.15,s.P2,s.methane_k,s.mode)
    firstgas_at_P2=State(s.T1,s.P2,s.methane_k,s.mode)
    # Gas1 -> P2 is treated as isothermal pressure drop (consistent stated
    # engineering scenario), not an unmodelled isenthalpic valve.
    hin=H(firstgas_at_P2,data['vapor_to_mix'],'vapor')+H(makeup_state,fresh,'vapor')
    hout=H(f2,nxt,'vapor')+H(f2,data['liq2'],'liquid')
    cooling=max(0.,hin-hout)
    cold_electric=cooling/s.refrigerator_COP
    utility=(compression_MW+cold_electric)/product_t_h*s.power_USD_MWh
    return {
        'settings':asdict(s),'operability':'CONVERGED_PHYSICALLY_ADMISSIBLE_RESEARCH_SCENARIO',
        'function_evaluations':evaluations,'fixed_point_residual_rel_fresh':err,
        'component_residual_rel_fresh':float(np.max(np.abs(mass_res))/target_scale),
        'component_residual_kmol_h':mass_res.tolist(),
        'flash_log_fugacity_error':max(data['a'].residual,data['b'].residual),
        'final_tpd_minima':checks,'reactor_feed_kmol_h':feed.tolist(),
        'reactor_NH3_formation_tpd':data['extent']*MW[4]*24/1000,
        'liquid_NH3_tpd':product_t_h*24,'feed_total_kmol_h':float(feed.sum()),
        'feed_NH3_molpct':100*float(fractions(feed)[4]),
        'feed_inerts_molpct':100*float(fractions(feed)[2:4].sum()),
        'sep1_vapor_NH3_molpct':100*data['a'].y[4],
        'sep2_vapor_NH3_molpct':100*data['b'].y[4],
        'sep1_liquid_kmol_h':data['liq1'].tolist(),'sep2_liquid_kmol_h':data['liq2'].tolist(),
        'purge_kmol_h':data['purge'].tolist(),'makeup_kmol_h':fresh.tolist(),
        'NH3_product_recovery_fraction':float(products[4]/data['extent']),
        'H2_loss_in_liquid_kg_h':float(products[1]*MW[1]),
        'H2_purge_kg_h':float(data['purge'][1]*MW[1]),
        'recycle_to_makeup_total_ratio':float(feed.sum()/fresh.sum()),
        'compression_shaft_MW_scenario':compression_MW,
        'recycle_shaft_MW_scenario':comp_rec['shaft_MW'],
        'second_stage_cooling_MW_approx':cooling,
        'second_stage_refrigeration_MW_scenario':cold_electric,
        'utility_USD_per_t_scenario':utility,
        'energy_scope':'isothermal compression/assumed efficiency and cold-stage2 PR-enthalpy duty/assumed COP; no reactor heat, first-stage cooler utility, feed cost, capital or catalyst cost',
        'reactor_scope':'specified per-pass N2 conversion; no new Fe/Ru kinetics',
        'flow_topology':'reactor -> flash1 -> purge -> makeup12 -> flash2 -> recycle compressor -> reactor; recovery outside boundary',
    }
