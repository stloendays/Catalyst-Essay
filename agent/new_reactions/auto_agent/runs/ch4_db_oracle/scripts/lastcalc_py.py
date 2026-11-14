import pandas as pd
r=pd.read_csv('db/costed_records.csv').query("rec_id=='CH4-184'").iloc[0]
print('x10 stability save',r['cat']*((1/3)/(.1019+1/3))*.9)
for c in ['raw_h2','raw_co2','capital','energy','cat'] : print(c,round(100*r[c]/r.total,3))
