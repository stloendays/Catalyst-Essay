import pandas as pd,ast
D=pd.read_csv('db/visible.csv');r=D[D.rec_id=='PDH-015'].iloc[0]
print(repr(r.composition_wt_pct));print(ast.literal_eval(r.composition_wt_pct))