"""One declared synthesis-loop cost boundary, consistent equal-product units.

No current commodity-price claim. Price/finance values are engineering scenarios;
metal, reactor and pressure-cost constants are carried from existing repository.
Actual makeup is priced ONCE. A common stoichiometric feed baseline is reported
separately, so excess-feed loss is never added on top of full feed consumption.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import math
import numpy as np
from kinetic_bridge import DENSITY, RU_WT

MW=np.array([28.0134,2.01588,16.0425,39.948,17.031])

@dataclass(frozen=True)
class EconomicSettings:
    product_tpd:float=1500.
    capacity_factor:float=.95
    project_y:float=25.
    catalyst_life_y:float=10.
    equipment_rate:float=.12
    metal_rate:float=.12
    ru_recovery:float=.9555
    Fe_USD_kg_catalyst:float=8.
    Ru_USD_kg_metal:float=53852.5
    Ru_fabrication_USD_kg_catalyst:float=8.
    H2_USD_kg:float=2.
    N2_USD_kg:float=.10
    CH4_USD_kg:float=.20
    Ar_USD_kg:float=0.
    power_USD_MWh:float=50.
    max_bed_m3:float=90.
    # Net hot-duty price is an explicit scenario; base thermal integration
    # not priced, hot heat removal is output separately. No total-plant claim.
    heat_removal_USD_GJ:float=0.
    def __post_init__(self):
        if self.product_tpd<=0 or not 0<self.capacity_factor<=1:raise ValueError('Invalid production basis')
        if self.project_y<=0 or self.catalyst_life_y<=0:raise ValueError('Invalid horizon')
        if min(self.equipment_rate,self.metal_rate)<0 or not 0<=self.ru_recovery<=1:raise ValueError('Invalid finance')
        if min(self.H2_USD_kg,self.N2_USD_kg,self.CH4_USD_kg,self.Ar_USD_kg,self.power_USD_MWh,self.heat_removal_USD_GJ)<0:raise ValueError('Negative price')


def crf(rate,years):
    if years<=0 or rate<0:raise ValueError('Invalid capital recovery inputs')
    return 1/years if rate==0 else rate/-math.expm1(-years*math.log1p(rate))


def annual_inventory_factor(rate,life,project,recovery):
    if rate<0 or life<=0 or project<=0 or not 0<=recovery<=1:raise ValueError('Invalid lifecycle inputs')
    purchases=np.arange(0.,project-1e-10,life)
    collections=list(purchases[1:])+[project]
    pv=sum((1+rate)**(-t) for t in purchases)-recovery*sum((1+rate)**(-t) for t in collections)
    return crf(rate,project)*max(0.,pv)


def vessel_cost(V,Pbar):
    # Same engineering proxy and pressure-attributable Turton shell premium
    # as canonical manifest. USD and CEPCI basis are inherited scenarios.
    if not 0<V<=520 or not 0<Pbar<1000:raise ValueError('Vessel correlation envelope')
    base=66800.+268000.*(V/20.)**.52
    v=max(.3,V);l=math.log10(v)
    cp=10**(3.4974+.4485*l+.1074*l*l)*797.9/397.
    D=(4*V/(math.pi*3.))**(1/3)
    thickness=Pbar*D/(2*(850.-.6*Pbar))+.00315
    pressure=max(thickness/.0063,1.)
    return base+cp*1.82*(pressure-1.)


def compressor_capex(shaft_MW):
    if shaft_MW<0:raise ValueError('Negative compressor power')
    if shaft_MW==0:return 0.
    kw=shaft_MW*1000;units=max(1,math.ceil(kw/3000));per=kw/units
    a=max(per,450.);l=math.log10(a)
    base=10**(2.2897+1.3604*l-.1027*l*l)
    if per<450:base*=(per/450.)**.67
    return units*base*2.8*797.9/397.


def evaluate(catalyst,bed_m3,Pbar,flow_record,e=EconomicSettings()):
    target_h=e.product_tpd/24.;annual=e.product_tpd*365*e.capacity_factor
    prices=np.array([e.N2_USD_kg,e.H2_USD_kg,e.CH4_USD_kg,e.Ar_USD_kg,0.])
    makeup=np.asarray(flow_record['makeup_kmol_h'])
    feed=float(np.sum(makeup*MW*prices))/target_h
    stoich=(.5*MW[0]*e.N2_USD_kg+1.5*MW[1]*e.H2_USD_kg)/MW[4]*1000
    non_nh3_liq=np.asarray(flow_record['products_kmol_h']).copy();non_nh3_liq[4]=0.
    purge=np.asarray(flow_record['purge_kmol_h'])
    # Feed decomposition derived from chemical atom and material balances,
    # including lost NH3 in purge. These are diagnostics, not added twice.
    nh3_loss=purge[4]/target_h
    carried=float(np.sum((purge+non_nh3_liq)*MW*prices))/target_h
    consumed_for_lost_nh3=nh3_loss*(.5*MW[0]*e.N2_USD_kg+1.5*MW[1]*e.H2_USD_kg)
    feed_identity=feed-stoich-carried-consumed_for_lost_nh3
    power=sum(flow_record['compressor_shaft_MW_by_service'])+flow_record['refrigeration_MW']
    utility=power*e.power_USD_MWh/target_h
    cat_kg=bed_m3*DENSITY[catalyst]
    unrecovered=annual_inventory_factor(e.metal_rate,e.catalyst_life_y,e.project_y,0.)
    if catalyst=='Fe':
        inventory=cat_kg*e.Fe_USD_kg_catalyst*unrecovered/annual
        metalpart=inventory;support=0.;ru_kg=0.
    elif catalyst=='Ru':
        ru_kg=cat_kg*RU_WT
        recoverable=annual_inventory_factor(e.metal_rate,e.catalyst_life_y,e.project_y,e.ru_recovery)
        metalpart=ru_kg*e.Ru_USD_kg_metal*recoverable/annual
        support=cat_kg*e.Ru_fabrication_USD_kg_catalyst*unrecovered/annual
        inventory=metalpart+support
    else:raise ValueError('Unsupported catalyst formulation')
    reactor=vessel_cost(bed_m3,Pbar)*crf(e.equipment_rate,e.project_y)/annual
    ccap=sum(compressor_capex(x) for x in flow_record['compressor_shaft_MW_by_service'])
    compression_capital=ccap*crf(e.equipment_rate,e.project_y)/annual
    hot=flow_record.get('isothermal_reaction_heat_removed_MW',0.)*3.6*e.heat_removal_USD_GJ/target_h
    relevant=utility+inventory+reactor+compression_capital+feed-stoich+hot
    total=relevant+stoich
    return {'modeled_loop_cost_USD_t':total,'decision_relevant_cost_USD_t':relevant,
            'feed_USD_t':feed,'stoichiometric_feed_USD_t':stoich,'excess_feed_USD_t':feed-stoich,
            'feed_cost_decomposition_residual_USD_t':feed_identity,
            'utility_USD_t':utility,'inventory_USD_t':inventory,
            'ru_metal_USD_t':metalpart if catalyst=='Ru' else 0.,'support_USD_t':support,
            'reactor_annualized_USD_t':reactor,'compressor_annualized_USD_t':compression_capital,
            'hot_duty_scenario_USD_t':hot,
            'catalyst_inventory_kg':cat_kg,'ru_inventory_kg':ru_kg,
            'annual_NH3_t':annual,'economic_settings':asdict(e),
            'scope':'delivered makeup priced once + compression/cold2 + lifecycle catalyst + reactor/pressure-shell/compressor capital; excludes upstream H2 production plant, detailed heat-exchanger/separator/piping capital and unpriced hot integration'}
