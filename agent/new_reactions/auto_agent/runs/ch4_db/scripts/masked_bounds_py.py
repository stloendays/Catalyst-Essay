p='scripts/model_py.py'
s=open(p,encoding='utf-8').read()
s=s.replace("D['sel']=D.rec_id.map(S)","D['sel']=D.rec_id.map(S).fillna(1.0)")
s=s.replace("O.to_csv('db/costed_records.csv',index=False)","O.to_csv('db/all_S1_bound.csv',index=False)")
s=s.replace("G.to_csv('db/group_comparisons.csv',index=False)","G.to_csv('db/group_bounds.csv',index=False)")
exec(s)
