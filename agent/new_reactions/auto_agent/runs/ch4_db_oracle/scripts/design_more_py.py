import pandas as pd,numpy as np
O=pd.read_csv('db/costed_records.csv');
for rid in ['CH4-158','CH4-255']:
 r=O.query('rec_id==@rid').iloc[0];print(rid,r[['total','sel','xopt','W_t','capex_m','capital','raw_h2','raw_co2','energy','cat']].to_dict())
 # min cost as reactor capex->0, retain balance capex at current x
 flow=1/(r.xopt*r.sel);flowref=1/(.75*.9);bal=80*(flow/flowref)**.6;tf=1+max(r.T_C-350,0)*.0008
 mincapital=bal*tf*(.1019+.04)*10
 print('inf activity min',r.raw_h2+r.raw_co2+mincapital+r.energy-14.3,'balcap',bal)
