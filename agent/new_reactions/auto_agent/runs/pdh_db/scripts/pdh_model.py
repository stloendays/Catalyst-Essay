p='scripts/pdh_model.py'
s=open(p).read()
s=s.replace("df=pd.read_csv('db/visible.csv')","df=pd.read_csv('db/visible.csv')")
open(p,'w').write(s)
exec(compile(s,p,'exec'))