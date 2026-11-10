import pandas as pd
O=pd.read_csv('db/costed_records.csv');ref=O.query("rec_id=='CH4-184'").iloc[0];A=2650.408277753538
for rid in ['CH4-187','CH4-158','CH4-255']:
 r=O.query('rec_id==@rid').iloc[0]; non=r.total-A/r.sel; s=A/(ref.total-non);print(rid,s)
