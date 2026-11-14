import pandas as pd
D=pd.read_csv('db/visible.csv');
print(D[(D.paper=='P06')].to_string(index=False))
print('\nP08',D[D.paper=='P08'].to_string(index=False))
