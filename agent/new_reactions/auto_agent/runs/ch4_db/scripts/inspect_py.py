import pandas as pd, json, ast
p='db/visible.csv'
df=pd.read_csv(p)
print('shape',df.shape)
print('\nPapers/records/catalysts/groups:')
for pap,g in df.groupby('paper'):
    print(pap,len(g),'cats',g.catalyst.nunique(),'T',sorted(g.T_C.unique()),'P',sorted(g.P_bar.unique()),'feeds',g.feed.nunique(),'groups',g.groupby(['P_bar','feed']).ngroups)
print('\nTop rate records:')
print(df.nlargest(20,'lab_reactant_conversion_rate_mol_per_kg_h')[['rec_id','paper','catalyst','T_C','P_bar','lab_conversion','lab_reactant_conversion_rate_mol_per_kg_h']].to_string(index=False))
print('\nTop conversion records:')
print(df.nlargest(20,'lab_conversion')[['rec_id','paper','catalyst','T_C','P_bar','lab_conversion','lab_reactant_conversion_rate_mol_per_kg_h']].to_string(index=False))
print('\nElements:')
from collections import Counter
c=Counter()
for s in df.composition_wt_pct:
 for e,w in json.loads(s): c[e]+=1
print(c)
print('\nAll groups sizes:')
for k,g in df.groupby(['paper','P_bar','feed']): print(k[0],k[1],len(g),'cats',g.catalyst.nunique())
