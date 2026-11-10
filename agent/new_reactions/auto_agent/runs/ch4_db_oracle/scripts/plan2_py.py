import pandas as pd
D=pd.read_csv('db/visible.csv'); R=pd.read_csv('db/revealed.csv',names=['rec_id','field','value']); done=set(R[R.field=='selectivity'].rec_id)
sel=[]
# P01: all at 300,350,400 (unrevealed)
sel += D[(D.paper=='P01') & (D.T_C.isin([300,350,400])) & (~D.rec_id.isin(done))].rec_id.tolist()
# P02 all 300,325,350,375 (unrevealed) + 2bar all
sel += D[(D.paper=='P02') & ((D.T_C.isin([300,325,350,375])) | (D.P_bar==2)) & (~D.rec_id.isin(done))].rec_id.tolist()
# P05 all
sel += D[(D.paper=='P05') & (~D.rec_id.isin(done))].rec_id.tolist()
# P06 all 6/10bar unrevealed plus commercial
sel += D[(D.paper=='P06') & ((D.P_bar>=6)|(D.catalyst.str.contains('commercial'))) & (~D.rec_id.isin(done))].rec_id.tolist()
# P07 at 299.9/349.9 unrevealed
sel += D[(D.paper=='P07') & (D.T_C.isin([299.9,349.9])) & (~D.rec_id.isin(done))].rec_id.tolist()
sel=list(dict.fromkeys(sel))
print(len(sel));print(','.join(sel))
