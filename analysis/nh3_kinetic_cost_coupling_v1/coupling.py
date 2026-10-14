"""Matched-product bridge: measured hot kinetics <-> SI cold recycle <-> cost.

Search uses inverse PFR design coordinates (X,T,P) for efficiency. For every
candidate X a physically attainable bed is computed; X is then optimized
separately per catalyst. Selected designs are checked by an independent forward
ODE/PFR inside a fixed-bed recycle solve, with no target X passed to that solve.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import sys, math
import numpy as np
from scipy.optimize import root

HERE=Path(__file__).resolve().parent
COLD=HERE.parent/'nh3_si_closed_loop_v1'
sys.path.insert(0,str(COLD))
import loop as cold
from model import State, compression, MW, NU, fractions
from kinetic_bridge import size_bed,forward_bed,hot_heat_per_mol_NH3
from economics import EconomicSettings,evaluate


def cold_settings(Pbar,X,T2_C,purge,dp_bar=9.2,methane_k=0.,mode='si2024'):
    if not 2<=dp_bar<.5*Pbar:raise ValueError('Cold loop pressure drops outside scenario')
    # Retain the documented 1.4 bar first-to-second separator difference;
    # remaining loss is assigned between isobaric hot-bed reference and cold1.
    return cold.Settings(P_reactor=Pbar*1e5,P1=(Pbar-dp_bar+1.4)*1e5,
        P2=(Pbar-dp_bar)*1e5,conversion=X,T2=T2_C+273.15,purge=purge,
        methane_k=methane_k,mode=mode)


def phase_stability(state,comp,r):
    if r.phase=='two_phase':
        plane=np.log(np.maximum(r.x,1e-300))+state.properties(r.x,'liquid')[1]
        v=state.stability(comp,plane,[r.x,r.y,fractions(comp)])
    else:v=state.stability(comp)
    if v['minimum_tpd'] < -1e-6:raise RuntimeError('Converged split fails local phase stability')
    return float(v['minimum_tpd'])


def flow_record(settings,result,target_tpd=1500.):
    """Scale extensive quantities to common actual recovered-NH3 capacity.

    Scaling is exact for this isothermal, specified-intensive-state reduced
    model. Catalyst volume and capital are recomputed AFTER scaling. Fresh
    compression is recalculated at the new pressure, never kept at 182 bar.
    """
    s=settings;scale=target_tpd/result['liquid_NH3_tpd']
    feed=np.asarray(result['reactor_feed_kmol_h'])*scale
    makeup=np.asarray(result['makeup_kmol_h'])*scale
    l1=np.asarray(result['sep1_liquid_kmol_h'])*scale
    l2=np.asarray(result['sep2_liquid_kmol_h'])*scale
    purge=np.asarray(result['purge_kmol_h'])*scale
    extent=result['reactor_NH3_formation_tpd']/(MW[4]*24/1000)*scale
    refs=cold.source_streams()
    # Delivery pressure is source P1+1.8 bar where possible, same rule for all
    # catalysts and P states. No source10/11 recovery flow is inferred from purge.
    delivered_P=min(s.P_reactor,s.P1+1.8e5)
    fresh_services=[compression(cold.source_flow(refs[k])*scale,
        float(refs[k]['temperature_C'])+273.15,
        float(refs[k]['pressure_MPa'])*1e6,delivered_P,
        s.methane_k,s.mode,s.compressor_eta)['shaft_MW'] for k in (10,11)]
    rec=compression(feed,s.T2,s.P2,s.P_reactor,s.methane_k,s.mode,s.compressor_eta)['shaft_MW']
    return {'scale_to_equal_product':scale,'actual_liquid_NH3_tpd':target_tpd,
        'feed_kmol_h':feed.tolist(),'makeup_kmol_h':makeup.tolist(),
        'purge_kmol_h':purge.tolist(),'products_kmol_h':(l1+l2).tolist(),
        'sep1_liquid_kmol_h':l1.tolist(),'sep2_liquid_kmol_h':l2.tolist(),
        'extent_kmol_h':extent,'compressor_shaft_MW_by_service':fresh_services+[rec],
        'makeup_delivery_pressure_bar':delivered_P/1e5,
        'refrigeration_MW':result['second_stage_refrigeration_MW_scenario']*scale,
        'cold2_heat_removed_MW':result['second_stage_cooling_MW_approx']*scale,
        'component_residual_rel_fresh':result['component_residual_rel_fresh'],
        'fixed_point_residual_rel_fresh':result['fixed_point_residual_rel_fresh'],
        'flash_log_fugacity_error':result['flash_log_fugacity_error'],
        'inlet_NH3_pct':result['feed_NH3_molpct'],
        'inlet_inerts_pct':result['feed_inerts_molpct'],
        'H2_purge_kg_h':result['H2_purge_kg_h']*scale,
        'product_basis':'NH3 component in l1+l2, not total impure liquid mass',
        'feed_boundary':'delivered makeup12 transfer price; upstream recovery design is outside control volume'}


def candidate(catalyst,T_C,Pbar,settings,record,e=EconomicSettings(),activity=1.):
    v=size_bed(catalyst,T_C+273.15,Pbar,record['feed_kmol_h'],record['extent_kmol_h'],activity)
    row={'catalyst':catalyst,'T_C':T_C,'P_bar':Pbar,
         'X_design':settings.conversion,'T2_C':settings.T2-273.15,
         'purge':settings.purge,'methane_k':settings.methane_k,
         'eos':settings.mode,'activity_factor':activity,'equal_product_tpd':e.product_tpd,**v}
    if not v['feasible']:return row
    if v['bed_m3']>e.max_bed_m3:
        row.update(feasible=False,reason='required_bed_exceeds_shared_90m3_cap')
        return row
    work=dict(record)
    work['isothermal_reaction_heat_removed_MW']=-record['extent_kmol_h']/3.6*hot_heat_per_mol_NH3(T_C+273.15)/1e6
    cost=evaluate(catalyst,v['bed_m3'],Pbar,work,e)
    row.update(cost)
    row['reactor_heat_removed_MW']=work['isothermal_reaction_heat_removed_MW']
    row['fresh_scale']=record['scale_to_equal_product']
    row['inlet_NH3_pct']=record['inlet_NH3_pct'];row['inlet_inerts_pct']=record['inlet_inerts_pct']
    row['H2_purge_kg_h']=record['H2_purge_kg_h']
    row['gas_feed_kmol_h']=sum(record['feed_kmol_h'])
    return row


def forward_closed_loop(catalyst,T_C,settings,volume_m3,fresh_scale,
                        initial,activity=1.,check_stability=True):
    """Fixed bed + rates determines conversion inside the recycle fixed point.

    settings.conversion is deliberately NEVER read here. No preset output X or
    production target occurs in this solver. Products follow chosen fresh scale.
    """
    s=settings;fresh=cold.source_flow(cold.source_streams()[12])*fresh_scale
    f1=State(s.T1,s.P1,s.methane_k,s.mode);f2=State(s.T2,s.P2,s.methane_k,s.mode)
    norm=float(fresh.sum());evaluations=0
    def advance(feed):
        rx=forward_bed(catalyst,T_C+273.15,s.P_reactor/1e5,feed,volume_m3,activity)
        g1,l1,a=f1.split(rx['out_kmol_h'])
        pg=g1*s.purge;mix=g1-pg+fresh
        g2,l2,b=f2.split(mix)
        return g2,{'reaction':rx,'a':a,'b':b,'mix':mix,'liquid':l1+l2,'purge':pg}
    def func(logs):
        nonlocal evaluations
        evaluations+=1
        feed=np.exp(np.clip(logs,-12,22));nxt,_=advance(feed)
        return (nxt-feed)/norm
    start=np.asarray(initial,dtype=float)
    opt=root(func,np.log(np.maximum(start,1e-7)),method='hybr',options={'xtol':1e-8,'maxfev':300})
    feed=np.exp(np.clip(opt.x,-12,22));nxt,data=advance(feed)
    residual=float(np.max(np.abs(nxt-feed))/norm)
    if residual>2e-7:raise RuntimeError('Rate-coupled recycle did not close: '+str(residual))
    phase=[]
    if check_stability:
        phase=[phase_stability(f1,data['reaction']['out_kmol_h'],data['a']),
               phase_stability(f2,data['mix'],data['b'])]
    mass=fresh+NU*data['reaction']['extent_kmol_h']-data['liquid']-data['purge']
    return {'catalyst':catalyst,'fixed_bed_m3':volume_m3,'T_C':T_C,
        'P_bar':s.P_reactor/1e5,'calculated_X_N2':data['reaction']['X_N2'],
        'calculated_NH3_tpd':float(data['liquid'][4]*MW[4]*24/1000),
        'feed_kmol_h':feed.tolist(),'fixed_point_residual':residual,
        'material_residual_relative':float(np.max(np.abs(mass))/norm),
        'phase_stability_minima':phase,'function_evaluations':evaluations,
        'conversion_used_as_input':False,
        'scope':'isothermal fixed-pressure measured-source PFR plus SI cold-loop feedback, fixed inventory and makeup'}
