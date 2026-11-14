import pandas as pd,numpy as np,math
O=pd.read_csv('db/costed_records.csv');ref=O.query("rec_id=='CH4-184'").iloc[0]
A=2513.245652309419+137.16262544411893; annfac=(.1019+.04)*10 # $/t per $m capex at 100kt/y
flowref0=1/(.75*.9); Wmodelref=.5797870543
rows=[]
for _,r in O.iterrows():
 # current capex reconstruction components (million)
 flow=1/(r.xopt*r.sel); bal=80*(flow/flowref0)**.6; tf=1+max(r.T_C-350,0)*.0008
 reac=max(r.capex_m/tf-bal,0)
 # selectivity to reference 1: feed + balance flow and W inversely proportional to S
 s_cf=1.0; flowcf=1/(r.xopt*s_cf); balcf=80*(flowcf/flowref0)**.6; Wcf=r.W_t*r.sel/s_cf; reaccf=20*(Wcf/Wmodelref)**.6
 capcf=(balcf+reaccf)*tf
 select_attr=(A/r.sel-A/s_cf)+(r.capex_m-capcf)*annfac
 # activity set to ref intrinsic: W scales kintr/ref kintr
 Wact=r.W_t*r.kintr/ref.kintr; capact=(bal+20*(Wact/Wmodelref)**.6)*tf
 activity_attr=(r.capex_m-capact)*annfac
 # temperature set to 350: only metallurgy temperature factor here; equilibrium interaction left residual
 captemp=(bal+reac) # tf=1
 temp_attr=(r.capex_m-captemp)*annfac
 # metal cost one-at-a-time at same inventory/lifetime approx
 metal_attr=(r.cat_cost_kg-ref.cat_cost_kg)*r.W_t*1000*(.1019+1/3)/100000
 rows.append({'rec_id':r.rec_id,'cost_gap_to_ref':r.total-ref.total,'selectivity_OAT':select_attr,'activity_OAT':activity_attr,'temperature_metallurgy_OAT':temp_attr,'stability_OAT_base':0.0,'metal_cost_OAT':metal_attr,'interaction_residual':(r.total-ref.total)-select_attr-activity_attr-temp_attr-metal_attr})
pd.DataFrame(rows).to_csv('db/oat_attribution.csv',index=False)
print(pd.DataFrame(rows).sort_values('cost_gap_to_ref').head(10).to_string(index=False));print('saved',len(rows))
