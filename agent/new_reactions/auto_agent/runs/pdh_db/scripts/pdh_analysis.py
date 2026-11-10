import pandas as pd, numpy as np, json, ast, math
from scipy.optimize import minimize_scalar, brentq

df=pd.read_csv('db/visible.csv'); rev=pd.read_csv('db/revealed.csv',names=['rec_id','field','value'])
for _,r in rev[rev.field=='selectivity'].iterrows(): df.loc[df.rec_id==r.rec_id,'selectivity']=float(r.value)
stab={r.rec_id:json.loads(r.value) for _,r in rev[rev.field=='stability'].iterrows()}
A={'capacity_tpy':750000.,'hours':8500.,'propane_usd_t':394.,'ng_usd_GJ':4.96,'electricity_usd_kWh':.0862,'electricity_kWh_t':100.,'hydrogen_usd_kg':1.15,'h2_recovery':.90,'capex_usd':1400e6,'crf':.10,'fixed_om_frac':.04,'capex_fixed_frac':.25,'capex_circ_frac':.60,'capex_rx_frac':.15,'reference_selectivity':.936,'reference_x':.42,'reference_T':620.,'reference_productivity_kgkg_h':1.,'thermal_GJ_t':13.3,'catalyst_life_y':3.,'precious_recovery':.90,'catalyst_fab_usd_kg':20.,'regen_h':1.,'regen_usd_kg_cycle':.05,'unknown_cycle_h':24.,'Pt_usd_kg':30500.,'Ga_usd_kg':400.,'Co_usd_kg':30.,'Fe_usd_kg':.15,'P_usd_kg':4.,'Zn_usd_kg':3.,'Pb_usd_kg':2.2,'Sn_usd_kg':30.,'K_usd_kg':1.,'unknown_Pt_wt':.3,'dH_J_mol':124300.,'K600':.299}
MWp=42.081; MWa=44.097; MWh2=2.016; prod_kg_h=A['capacity_tpy']*1000/A['hours']
def Kp(T,a): return a['K600']*math.exp(-a['dH_J_mol']/8.314*(1/(T+273.15)-1/873.15))
def xeq(T,y,h,P,a):
    K=Kp(T,a); hi=h/y; n0=1/y
    return brentq(lambda x:P*x*(hi+x)/((1-x)*(n0+x))-K,1e-9,.999999)
def comp(row):
    try:return json.loads(row.composition_wt_pct)
    except:return []
def costs_metal(row,a):
    prices={e:a[e+'_usd_kg'] for e in ['Pt','Ga','Co','Fe','P','Zn','Pb','Sn','K']}; tot=pt=0; haspt=False; ptknown=False
    for e,w in comp(row):
        if e=='Pt':haspt=True
        if w is not None and not (isinstance(w,float) and np.isnan(w)):
            v=w/100*prices.get(e,0);tot+=v
            if e=='Pt':pt=v;ptknown=True
    if haspt and not ptknown: pt=a['unknown_Pt_wt']/100*a['Pt_usd_kg'];tot+=pt
    return tot,pt
def cyc(rec,a):
    v=stab.get(rec,{}).get('cycle_h_to_lose_10pct');return float(v) if v is not None else a['unknown_cycle_h']
def calc(row,a,Sel=None,am=1,cm=1,mm=1):
    S=float(Sel if Sel is not None else row.selectivity);T=float(row.T_C);xl=float(row.lab_conversion);rl=float(row.lab_reactant_conversion_rate_mol_per_kg_h);y=float(row.key_reactant_fraction);h=0 if pd.isna(row.h2_fraction) else float(row.h2_fraction)
    xeql=max(xeq(T,y,h,float(row.P_bar),a),xl*1.03); k=-xeql*rl/xl*math.log(1-xl/xeql)*am; xeqp=xeq(T,1,0,1.013,a); ch=cyc(row.rec_id,a)*cm; online=ch/(ch+a['regen_h'])
    refpass=1.048/a['reference_selectivity']/a['reference_x']; refinv=prod_kg_h/a['reference_productivity_kgkg_h']; ann=a['crf']+a['fixed_om_frac']
    def f(x):
        tau=-xeqp/k*math.log(1-x/xeqp);q=S*x/tau*MWp/1000*online;inv=prod_kg_h/q;passv=1.048/S/x;ratio=passv/refpass
        cap=a['capex_usd']*(a['capex_fixed_frac']+a['capex_circ_frac']*ratio**.6+a['capex_rx_frac']*(inv/refinv)**.6)*ann/a['capacity_tpy']
        therm=a['thermal_GJ_t']*(.4+.6*ratio*(T+273.15)/(a['reference_T']+273.15));energy=therm*a['ng_usd_GJ']+a['electricity_kWh_t']*a['electricity_usd_kWh']*ratio
        feed=1.048/S*a['propane_usd_t'];h2=(1000/MWp*MWh2)*a['h2_recovery']*a['hydrogen_usd_kg'];met,pt=costs_metal(row,a);met*=mm;pt*=mm; non=max(0,met-pt)
        annkg=(a['catalyst_fab_usd_kg']+non+(1-a['precious_recovery'])*pt)/a['catalyst_life_y']+a['crf']*a['precious_recovery']*pt
        cat=inv*annkg/a['capacity_tpy'];regen=inv*(a['hours']/(ch+a['regen_h']))*a['regen_usd_kg_cycle']/a['capacity_tpy'];total=feed+energy+cap+cat+regen-h2
        return {'total':total,'feed':feed,'energy':energy,'capital':cap,'catalyst':cat,'regeneration':regen,'h2_credit':h2,'x':x,'q':q,'inventory_t':inv/1000,'circulation_ratio':ratio,'xeq':xeqp,'k':k,'cycle_h':ch}
    o=minimize_scalar(lambda x:f(x)['total'],bounds=(.05,.95*xeqp),method='bounded');return f(o.x)
def ref(a):
    feed=1.048/a['reference_selectivity']*a['propane_usd_t'];energy=a['thermal_GJ_t']*a['ng_usd_GJ']+a['electricity_kWh_t']*a['electricity_usd_kWh'];capital=a['capex_usd']*(a['crf']+a['fixed_om_frac'])/a['capacity_tpy'];cat=5.42e6/a['capacity_tpy'];regen=2.;h2=(1000/MWp*MWh2)*a['h2_recovery']*a['hydrogen_usd_kg'];return {'total':feed+energy+capital+cat+regen-h2,'feed':feed,'energy':energy,'capital':capital,'catalyst':cat,'regeneration':regen,'h2_credit':h2,'x':a['reference_x'],'inventory_t':prod_kg_h/a['reference_productivity_kgkg_h']/1000}
C=df[df.selectivity!='MASKED'].copy(); out=[]
for _,r in C.iterrows():out.append({'rec_id':r.rec_id,'paper':r.paper,'catalyst':r.catalyst,'selectivity':float(r.selectivity),'lab_conversion':r.lab_conversion,'lab_rate':r.lab_reactant_conversion_rate_mol_per_kg_h,'lab_productivity_kgkg_h':r.lab_reactant_conversion_rate_mol_per_kg_h*float(r.selectivity)*MWp/1000,'stability_revealed':r.rec_id in stab and stab[r.rec_id].get('cycle_h_to_lose_10pct') is not None,**calc(r,A)})
res=pd.DataFrame(out).sort_values('total');res.to_csv('analysis_record_costs.csv',index=False);R=ref(A)
ranks=[]
for paper,g in df.groupby('paper'):
    gc=res[res.paper==paper];cheap=gc.loc[gc.total.idxmin()]
    leaders=[('conversion',g.loc[g.lab_conversion.idxmax()].rec_id),('reactant_rate',g.loc[g.lab_reactant_conversion_rate_mol_per_kg_h.idxmax()].rec_id),('product_productivity',gc.loc[gc.lab_productivity_kgkg_h.idxmax()].rec_id)]
    for m,lid in leaders:
        rr=res[res.rec_id==lid]
        if len(rr):
            z=rr.iloc[0];agree=lid==cheap.rec_id;typ='agree' if agree else ('same catalyst/other condition' if z.catalyst==cheap.catalyst else 'other catalyst');ranks.append({'paper':paper,'metric':m,'leader':lid,'plant_choice':cheap.rec_id,'agree':agree,'type':typ,'regret_usd_t':z.total-cheap.total})
        else:ranks.append({'paper':paper,'metric':m,'leader':lid,'plant_choice':cheap.rec_id,'agree':None,'type':'leader selectivity masked','regret_usd_t':np.nan})
pd.DataFrame(ranks).to_csv('analysis_rankings.csv',index=False)
attrs=[];back=[]
for _,r in C.iterrows():
    b=calc(r,A); sr=calc(r,A,Sel=A['reference_selectivity']);a2=calc(r,A,am=2);s10=calc(r,A,cm=10);m0=calc(r,A,mm=0)
    attrs.append({'rec_id':r.rec_id,'gap_to_ref':b['total']-R['total'],'selectivity_effect_vs_refS':b['total']-sr['total'],'benefit_x2_activity':b['total']-a2['total'],'benefit_x10_stability':b['total']-s10['total'],'metal_cost_effect':b['total']-m0['total'],'temperature_energy_gap':b['energy']-R['energy']})
    cur=float(r.selectivity);target=R['total']; sn=cur if b['total']<=target else (brentq(lambda s:calc(r,A,Sel=s)['total']-target,cur,.9999) if calc(r,A,Sel=.9999)['total']<=target else np.nan)
    an=1 if b['total']<=target else (math.exp(brentq(lambda lm:calc(r,A,am=math.exp(lm))['total']-target,0,math.log(1e4))) if calc(r,A,am=1e4)['total']<=target else np.nan)
    mn=1 if b['total']<=target else (brentq(lambda m:calc(r,A,mm=m)['total']-target,0,1) if calc(r,A,mm=0)['total']<=target else np.nan)
    back.append({'rec_id':r.rec_id,'base_cost':b['total'],'selectivity_needed':sn,'activity_multiplier_needed':an,'metal_price_multiplier_needed':mn})
pd.DataFrame(attrs).to_csv('analysis_attribution.csv',index=False);pd.DataFrame(back).to_csv('analysis_backward.csv',index=False)
sc={'central':{},'low_propane':{'propane_usd_t':300},'high_propane':{'propane_usd_t':500},'low_capex':{'capex_usd':1000e6},'high_capex':{'capex_usd':2000e6},'low_energy':{'ng_usd_GJ':3.5},'high_energy':{'ng_usd_GJ':8},'low_Pt':{'Pt_usd_kg':20000},'high_Pt':{'Pt_usd_kg':50000},'fast_regen_cheap':{'regen_usd_kg_cycle':.01,'regen_h':.5},'slow_regen_costly':{'regen_usd_kg_cycle':.2,'regen_h':2},'unknown_stability_5h':{'unknown_cycle_h':5},'unknown_stability_100h':{'unknown_cycle_h':100},'unknown_Pt_01wt':{'unknown_Pt_wt':.1},'unknown_Pt_10wt':{'unknown_Pt_wt':1},'life_1y':{'catalyst_life_y':1},'life_5y':{'catalyst_life_y':5}}
ss=[]
for n,ch in sc.items():
    aa=A.copy();aa.update(ch);v=sorted((calc(r,aa)['total'],r.rec_id) for _,r in C.iterrows());rr=ref(aa);ss.append({'scenario':n,'winner':v[0][1],'winner_cost':v[0][0],'runner_up':v[1][1],'margin':v[1][0]-v[0][0],'reference_cost':rr['total'],'reference_feed_share':rr['feed']/rr['total']})
pd.DataFrame(ss).to_csv('analysis_sensitivity.csv',index=False)
S=A['reference_selectivity']+.01;splus=1.048*A['propane_usd_t']*(1/A['reference_selectivity']-1/S);cap2=A['capex_usd']*(A['capex_fixed_frac']+A['capex_circ_frac']+A['capex_rx_frac']*.5**.6)*(A['crf']+A['fixed_om_frac'])/A['capacity_tpy'];act2=R['total']-(R['capital']-cap2)-R['catalyst']/2-R['regeneration']/2;actsave=R['total']-act2
summary={'assumptions':A,'reference':R,'reference_selectivity_plus1pt_saving':splus,'reference_x2_activity_saving':actsave,'reference_x10_stability_saving':.9*R['regeneration'],'reference_propane_plus10_effect':1.048/A['reference_selectivity']*10,'winner':res.iloc[0].to_dict(),'top5':res.head()[['rec_id','total','selectivity','x','inventory_t','cycle_h']].to_dict('records'),'n_costed':len(res),'n_total':len(df)}
json.dump(summary,open('analysis_summary.json','w'),indent=2,default=float)
print('REF', {k:round(v,2) for k,v in R.items()});print('TOP5\n',res.head()[['rec_id','total','selectivity','x','inventory_t','cycle_h','feed','energy','capital','catalyst','regeneration']].round(3).to_string(index=False));print('RANK\n',pd.DataFrame(ranks).to_string(index=False));print('MARG',round(splus,2),round(actsave,2),round(.9*R['regeneration'],2),round(summary['reference_propane_plus10_effect'],2));print('SENS\n',pd.DataFrame(ss)[['scenario','winner','winner_cost','margin','reference_cost']].round(2).to_string(index=False))