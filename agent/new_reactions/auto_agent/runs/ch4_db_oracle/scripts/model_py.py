import pandas as pd, numpy as np, json, math
from scipy.optimize import brentq
D=pd.read_csv('db/visible.csv')
R=pd.read_csv('db/revealed.csv',names=['rec_id','field','value'])
S=R[R.field=='selectivity'].set_index('rec_id').value.astype(float)
D['sel']=D.rec_id.map(S)
# assumptions
ANN_T=100000.; hours=8000.; Pplant=30.; h2price=5.0 # $/kg
co2price=50.0 # $/t
el=86.2 # $/MWh
MWch4=16.043; MWco2=44.01; MWh_t_HHV=15.4
crf=0.1019; fom=0.04
metal={'Ni':15.2,'Co':35.,'Pt':45900.,'Fe':0.15,'Ce':5.,'Mn':2.,'Al':2.5,'Zr':30.,'B':5.,'O':0.}
# equilibrium, constant dH/dS approximation
def kp(Tc):
 T=Tc+273.15; dH=-165000.; dS=-173.; dG=dH-T*dS
 return math.exp(-dG/(8.314*T))
def Q(x,P,yco2=0.2):
 # stoich reactive feed plus inert chosen from initial CO2 mole fraction yco2
 inert=max(0.,1/yco2-5.)
 nt=5+inert-2*x
 ps=[(1-x)/nt*P,(4-4*x)/nt*P,x/nt*P,2*x/nt*P]
 return (ps[2]*ps[3]**2)/(max(ps[0],1e-20)*max(ps[1],1e-20)**4)
def xeq(T,P,y=.2):
 K=kp(T)
 try:return brentq(lambda x: math.log(max(Q(x,P,y),1e-300))-math.log(K),1e-9,.999999)
 except:return .999
# derive intrinsic rate coefficient per bar CO2
def derive(row):
 X=float(row.lab_conversion); xe=max(xeq(row.T_C,row.P_bar,float(row.key_reactant_fraction)),X+1e-4)
 fw=row.lab_reactant_conversion_rate_mol_per_kg_h/X
 keff=fw*(-math.log(max(1-X/xe,1e-8)))
 pco2=max(row.P_bar*float(row.key_reactant_fraction),.01)
 return keff/pco2,xe
vals=D.apply(derive,axis=1,result_type='expand');D['kintr']=vals[0];D['xeq_lab']=vals[1]
# catalyst purchase $/kg
precious=[]; costs=[]
for s in D.composition_wt_pct:
 arr=json.loads(s); c=20.; prec=0.
 for e,w in arr:
  w=20. if w is None and e in ['Co','Ni'] else (0. if w is None else float(w))
  c += w/100*metal.get(e,10.)
  if e=='Pt':prec += w/100*metal['Pt']
 costs.append(c);precious.append(prec)
D['cat_cost_kg']=costs;D['precious_component']=precious
# reference W at CH4-187, x=.75
ref=D[D.rec_id=='CH4-187'].iloc[0]
def inventory(row,x):
 xe=xeq(row.T_C,Pplant,.2); x=min(x,.97*xe)
 keff=row.kintr*(Pplant*.2)
 product_mol_h=ANN_T*1e6/MWch4/hours
 co2in=product_mol_h/(row.sel*x)
 W=co2in*(-math.log(max(1-x/xe,1e-8)))/keff
 return W,xe
# if ref selectivity present
Wref,_=inventory(ref,.75)

def costrow(row):
 if pd.isna(row.sel): return None
 best=None
 xe=xeq(row.T_C,Pplant,.2)
 xmax=min(.95,.97*xe)
 if xmax<.15:return None
 for x in np.linspace(.15,xmax,161):
  W,_=inventory(row,x)
  flow=(1/(x*row.sel)); flowref=1/(.75*.9)
  # 2026 USD installed methanation island: 80m balance + 20m reactor at reference
  tempfac=1+max(row.T_C-350,0)*0.0008
  capex=(80e6*(flow/flowref)**.60 + 20e6*(max(W,1)/Wref)**.60)*tempfac
  capital=capex*(crf+fom)/ANN_T
  recycle=(1-x)/x
  power_mwh=.12 + .06*recycle # feed compression/drying + recycle
  energy=power_mwh*el
  # feed per t product; selectivity means converted CO2 not to CH4 is lost
  raw_h2=(8.064/MWch4)*1000/row.sel*h2price
  raw_co2=(44.01/MWch4)/row.sel*co2price
  # catalyst inventory carrying + replacement, 3-y assumed, precious recovery 90%
  effective=row.cat_cost_kg-0.9*row.precious_component
  cat=(W*row.cat_cost_kg*crf + W*effective/3)/ANN_T
  heatcredit=14.3
  total=raw_h2+raw_co2+capital+energy+cat-heatcredit
  z={'total':total,'xopt':x,'xeq':xe,'W_t':W/1000,'capex_m':capex/1e6,'raw_h2':raw_h2,'raw_co2':raw_co2,'capital':capital,'energy':energy,'cat':cat,'heat_credit':-heatcredit}
  if best is None or total<best['total']:best=z
 return best
outs=[]
for _,r in D.iterrows():
 z=costrow(r)
 if z: outs.append({**r.to_dict(),**z})
O=pd.DataFrame(outs).sort_values('total')
O.to_csv('db/costed_records.csv',index=False)
print('costed',len(O),'best 20')
print(O[['rec_id','paper','catalyst','T_C','P_bar','sel','lab_conversion','lab_reactant_conversion_rate_mol_per_kg_h','total','xopt','W_t','capex_m','cat']].head(20).to_string(index=False,formatters={'total':'{:.1f}'.format,'W_t':'{:.1f}'.format,'capex_m':'{:.1f}'.format,'cat':'{:.3f}'.format}))
print('\nreference')
print(O[O.rec_id=='CH4-187'][['rec_id','total','xopt','xeq','W_t','capex_m','raw_h2','raw_co2','capital','energy','cat','heat_credit']].to_string(index=False))
# group comparisons among costed records; require >=2 catalysts
rows=[]
for keys,gall in D.groupby(['paper','P_bar','feed']):
 g=O[O.rec_id.isin(gall.rec_id)]
 if len(g)==0:continue
 cheap=g.loc[g.total.idxmin()]
 conv=gall.loc[gall.lab_conversion.idxmax()]
 # productivity leader among revealed/costed
 gp=g.copy();gp['prod']=gp.lab_reactant_conversion_rate_mol_per_kg_h*gp.sel*MWch4/1000
 prod=gp.loc[gp['prod'].idxmax()]
 cv=O[O.rec_id==conv.rec_id]
 rows.append({'paper':keys[0],'P':keys[1],'n_all':len(gall),'n_costed':len(g),'cats':gall.catalyst.nunique(),'cheap':cheap.rec_id,'cheapcat':cheap.catalyst,'cheapT':cheap.T_C,'cheapcost':cheap.total,'conv':conv.rec_id,'convcat':conv.catalyst,'convT':conv.T_C,'convcost':float(cv.total.iloc[0]) if len(cv) else np.nan,'prod':prod.rec_id,'prodcat':prod.catalyst,'prodT':prod.T_C,'prodcost':prod.total})
G=pd.DataFrame(rows);G.to_csv('db/group_comparisons.csv',index=False)
print('\ngroups')
print(G.to_string(index=False,formatters={'cheapcost':'{:.1f}'.format,'convcost':'{:.1f}'.format,'prodcost':'{:.1f}'.format}))
# breakdown best and gaps ref
best=O.iloc[0];print('\nBEST BREAKDOWN',best[['rec_id','total','raw_h2','raw_co2','capital','energy','cat','heat_credit','xopt','W_t']].to_dict())
# perturbations at reference
print('Wref',Wref/1000)
