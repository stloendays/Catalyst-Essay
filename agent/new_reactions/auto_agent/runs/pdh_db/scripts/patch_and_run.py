import subprocess
p='scripts/pdh_analysis.py';s=open(p).read();s=s.replace("try:return ast.literal_eval(row.composition_wt_pct)","try:return json.loads(row.composition_wt_pct)");open(p,'w').write(s)
r=subprocess.run(['python',p],capture_output=True,text=True,timeout=120);print(r.stdout);print(r.stderr)