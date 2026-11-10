import pandas as pd, numpy as np, json
D=pd.read_csv('db/visible.csv')
D['F_W']=D.lab_reactant_conversion_rate_mol_per_kg_h/D.lab_conversion
D['kproxy']=D.F_W*(-np.log(1-D.lab_conversion.clip(upper=.999)))
for pap,g in D.groupby('paper'):
 print('\n',pap)
 # per catalyst best kproxy and highest conversion, list unique comps
 rows=[]
 for cat,h in g.groupby('catalyst'):
  a=h.loc[h.kproxy.idxmax()]; b=h.loc[h.lab_conversion.idxmax()]; r=h.loc[h.lab_reactant_conversion_rate_mol_per_kg_h.idxmax()]
  rows.append((cat,a.rec_id,a.T_C,round(a.kproxy,1),b.rec_id,b.T_C,b.lab_conversion,r.rec_id,r.T_C,round(r.lab_reactant_conversion_rate_mol_per_kg_h,1)))
 for z in rows: print(z)
 print('group metric leaders:')
 for keys,h in g.groupby(['P_bar','feed']):
  print(keys[0], 'conv',h.loc[h.lab_conversion.idxmax(),['rec_id','catalyst','T_C','lab_conversion']].to_dict(),'rate',h.loc[h.lab_reactant_conversion_rate_mol_per_kg_h.idxmax(),['rec_id','catalyst','T_C','lab_reactant_conversion_rate_mol_per_kg_h']].to_dict(),'k',h.loc[h.kproxy.idxmax(),['rec_id','catalyst','T_C','kproxy']].to_dict())
