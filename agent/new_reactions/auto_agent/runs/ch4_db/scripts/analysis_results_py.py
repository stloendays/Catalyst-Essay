import pandas as pd,numpy as np,json,math
O=pd.read_csv('db/costed_records.csv');G=pd.read_csv('db/group_comparisons.csv')
for rid in ['CH4-036','CH4-184','CH4-187','CH4-074','CH4-204']:
 r=O[O.rec_id==rid].iloc[0]
 print(rid,{k:round(float(r[k]),4) for k in ['total','raw_h2','raw_co2','capital','energy','cat','heat_credit','xopt','xeq','W_t','capex_m']})
# disagreement counts excluding trivial single catalyst groups, and only where n_costed metric leaders costed
H=G[G.cats>1].copy()
for metric in ['conv','prod']:
 H[metric+'dis']=H[metric]!=H.cheap
 H[metric+'type']=np.where(H[metric+'cat']!=H.cheapcat,'other catalyst',np.where(H[metric+'T']!=H.cheapT,'same catalyst, other T','agree'))
 H[metric+'regret']=H[metric+'cost']-H.cheapcost
 print('\n',metric,'n',len(H),'dis',H[metric+'dis'].sum(),H[metric+'type'].value_counts().to_dict(),'mean regret dis',H.loc[H[metric+'dis'],metric+'regret'].mean(),'max',H[metric+'regret'].max())
 print(H[['paper','P','cheap',metric,metric+'type',metric+'regret']].to_string(index=False))
# all costed by paper best
print('\nPaper best')
print(O.loc[O.groupby('paper').total.idxmin(),['paper','rec_id','catalyst','T_C','sel','total']].sort_values('paper').to_string(index=False))
# gap attribution to reference CH4-184: replace one dimension using approximate cost components / recalc not available; compute direct component gaps and proxies
ref=O[O.rec_id=='CH4-184'].iloc[0]
print('\ncomponent gaps top candidates vs ref')
for rid in ['CH4-036','CH4-074','CH4-204','CH4-255','CH4-187']:
 r=O[O.rec_id==rid].iloc[0]
 print(rid,{k:round(r[k]-ref[k],2) for k in ['total','raw_h2','raw_co2','capital','energy','cat']})
# backward selectivity needed neglect small shifts: solve feed coefficient/S + nonfeed = ref cost
A=2513.245652309419+137.16262544411893
print('\nbackward S needed to ref for each paper best')
for _,r in O.loc[O.groupby('paper').total.idxmin()].sort_values('paper').iterrows():
 non=r.total-(2513.245652309419+137.16262544411893)/r.sel
 sneed=A/(ref.total-non)
 print(r.paper,r.rec_id,'current',r.sel,'need',round(sneed,4),'activityratio rough W',round(r.W_t/ref.W_t,3))
