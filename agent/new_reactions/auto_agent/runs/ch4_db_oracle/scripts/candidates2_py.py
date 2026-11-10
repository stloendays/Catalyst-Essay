import pandas as pd,numpy as np
D=pd.read_csv('db/visible.csv');rate='lab_reactant_conversion_rate_mol_per_kg_h';D['F_W']=D[rate]/D.lab_conversion;D['kproxy']=D.F_W*(-np.log(1-D.lab_conversion.clip(upper=.999)))
for pap in ['P06','P07','P08']:
 g=D[D.paper==pap];print('\n',pap)
 for cat,h in g.groupby('catalyst'):
  a=h.loc[h.kproxy.idxmax()];b=h.loc[h.lab_conversion.idxmax()];r=h.loc[h[rate].idxmax()]
  print(cat,'k',a.rec_id,a.T_C,round(a.kproxy,1),'conv',b.rec_id,b.T_C,b.lab_conversion,'rate',r.rec_id,r.T_C,round(r[rate],1))
 for keys,h in g.groupby(['P_bar','feed']):
  print('GROUP',keys[0],len(h),'conv',h.loc[h.lab_conversion.idxmax(),'rec_id'],'rate',h.loc[h[rate].idxmax(),'rec_id'],'k',h.loc[h.kproxy.idxmax(),'rec_id'])
print('\nP03 last 12:')
print(D[D.paper=='P03'].tail(12)[['rec_id','catalyst','T_C','lab_conversion',rate,'F_W']].to_string(index=False))
