import pandas as pd,numpy as np
D=pd.read_csv('db/visible.csv');rate='lab_reactant_conversion_rate_mol_per_kg_h';D['F']=D[rate]/D.lab_conversion;D['k']=D.F*(-np.log(1-D.lab_conversion.clip(upper=.999)))
sel=set()
# per catalyst: max k and max rate below/equal 350, plus max conversion
for (pap,cat),g in D.groupby(['paper','catalyst']):
 for col in ['k','lab_conversion']:
  sel.add(g.loc[g[col].idxmax(),'rec_id'])
 h=g[g.T_C<=350]
 if len(h): sel.add(h.loc[h.k.idxmax(),'rec_id'])
# group metric leaders
for _,g in D.groupby(['paper','P_bar','feed']):
 for col in ['k','lab_conversion',rate]:sel.add(g.loc[g[col].idxmax(),'rec_id'])
# include P08
sel.add('CH4-255')
print('select n',len(sel)); print(','.join(sorted(sel)))
# duplicates same cat/T/P/feed likely stability or flow series; list
print('\nduplicate condition sets:')
for keys,g in D.groupby(['paper','catalyst','T_C','P_bar','feed']):
 if len(g)>1: print(keys[0],keys[1],keys[2],len(g),','.join(g.rec_id))
