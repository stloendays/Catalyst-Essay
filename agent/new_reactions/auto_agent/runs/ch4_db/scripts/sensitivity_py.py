import pandas as pd,numpy as np
O=pd.read_csv('db/costed_records.csv')
scenarios={'base':{},'H2 $2/kg':{'raw_h2':2/5},'H2 $7/kg':{'raw_h2':7/5},'CO2 $20/t':{'raw_co2':.4},'CO2 $150/t':{'raw_co2':3},'capex 0.5x':{'capital':.5},'capex 1.5x':{'capital':1.5},'electricity $50/MWh':{'energy':50/86.2},'electricity $120/MWh':{'energy':120/86.2},'catalyst cost 10x':{'cat':10}}
for name,m in scenarios.items():
 z=O.copy();z['sens']=z.total
 for col,f in m.items():z['sens'] += z[col]*(f-1)
 b=z.loc[z.sens.idxmin()];ref=z[z.rec_id=='CH4-184'].iloc[0]
 print(name, b.rec_id,round(b.sens,1),'gapref',round(b.sens-ref.sens,1),'top3',','.join(z.nsmallest(3,'sens').rec_id))
r=O[O.rec_id=='CH4-184'].iloc[0];feed=r.raw_h2+r.raw_co2
print('1 selectivity point 0.99->1 saving',feed/0.99-feed)
print('H2 +0.1/kg',r.raw_h2*.1/5)
flow=1/(r.xopt*r.sel);flowref=1/(.75*.9);bal=80*(flow/flowref)**.6;reac=20*(r.W_t/.5797870543)**.6
newcap=bal+reac*(.5**.6);save=(r.capex_m-newcap)*(.1019+.04)*10
print('capex split m',bal,reac,'x2 activity save',save)
print('x10 stability save approx',r.cat*(1/(.1019+1/3))*(1/3)*.9)
print('shares');
for c in ['raw_h2','raw_co2','capital','energy','cat']:print(c,round(100*r[c]/r.total,2))
