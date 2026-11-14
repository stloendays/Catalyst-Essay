import pandas as pd
D=pd.read_csv('db/visible.csv');cols=['rec_id','catalyst','composition_wt_pct','T_C','P_bar','feed','lab_conversion','lab_reactant_conversion_rate_mol_per_kg_h']
print(D[(D.paper=='P06') & (D.index>=174)][cols].to_string(index=False));print(D[D.paper=='P08'][cols].to_string(index=False))
