p='report.md'
s=open(p,encoding='utf-8').read()
s=s.replace('Pending final ledger read.','Ledger read at 2026-11-10T21:47:56: **10.1 wall-clock minutes** and **$5.06 USD equivalent at GPT-5.5 list price**. The ledger recorded 890,626 total tokens, 25 agent calls, 33.8 s Python tool time, and the full 153-unit reveal budget spent.')
open(p,'w',encoding='utf-8').write(s)
print('report finalized',len(s))
