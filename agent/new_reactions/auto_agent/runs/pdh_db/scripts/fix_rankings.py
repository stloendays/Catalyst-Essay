import pandas as pd
D=pd.read_csv('db/visible.csv');R=pd.read_csv('analysis_record_costs.csv');rows=[]
for paper,g in D.groupby('paper'):
 gc=R[R.paper==paper];cheap=gc.loc[gc.total.idxmin()];cn=D.set_index('rec_id').loc[cheap.rec_id,'catalyst'];ct=D.set_index('rec_id').loc[cheap.rec_id,'T_C']
 leaders=[('conversion',g.loc[g.lab_conversion.idxmax()].rec_id),('reactant_rate',g.loc[g.lab_reactant_conversion_rate_mol_per_kg_h.idxmax()].rec_id),('product_productivity',gc.loc[gc.lab_productivity_kgkg_h.idxmax()].rec_id)]
 for m,lid in leaders:
  rr=R[R.rec_id==lid]
  if len(rr):
   z=rr.iloc[0];ln=D.set_index('rec_id').loc[lid,'catalyst'];lt=D.set_index('rec_id').loc[lid,'T_C'];agree=lid==cheap.rec_id
   typ='agree' if agree else ('same catalyst at another temperature' if ln==cn and lt!=ct else ('same catalyst, other same-temperature condition' if ln==cn else 'other catalyst'))
   rows.append({'paper':paper,'metric':m,'leader':lid,'plant_choice':cheap.rec_id,'agree':agree,'disagreement_type':typ,'regret_usd_t':z.total-cheap.total})
  else:rows.append({'paper':paper,'metric':m,'leader':lid,'plant_choice':cheap.rec_id,'agree':None,'disagreement_type':'leader selectivity masked','regret_usd_t':None})
pd.DataFrame(rows).to_csv('analysis_rankings.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))