"""Run the offline acceptance suite sequentially, keeping complete per-script evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

A=Path(__file__).resolve().parents[1]
TESTS=['tests_v3/'+n+'.py' for n in ('validate_unitops','validate_v3','validate_v33','validate_v331',
       'validate_v34','validate_v35','validate_evaluation','validate_blind','validate_route_policy','validate_holdout_guard')]
TESTS+=['physics_gate_validate.py','tests_v3/validate_v36.py']

if __name__=='__main__':
    results=[]
    for name in TESTS:
        start=time.monotonic()
        command=[sys.executable,'-X','utf8',str(A/name)]
        if name == 'tests_v3/validate_evaluation.py':
            # The legacy evaluator writes HERE/evaluation. Redirect HERE to an isolated copy.
            code = """import sys,runpy,tempfile,shutil
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import evaluate_builds as ev
with tempfile.TemporaryDirectory(prefix='v36-evaluation-copy-') as t:
 root=Path(t)
 for folder in ('evaluation','holdout'): shutil.copytree(ev.HERE/folder,root/folder)
 shutil.copyfile(ev.HERE/'unitops.py',root/'unitops.py')
 ev.HERE=root
 ns=runpy.run_path(sys.argv[2]);ns['validate']()
"""
            command=[sys.executable,'-X','utf8','-c',code,str(A),str(A/name)]
        p=subprocess.run(command,cwd=A,env=dict(os.environ,PYTHONUTF8='1'),
                         capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        results.append(dict(test=name,passed=p.returncode==0,returncode=p.returncode,
                            seconds=round(time.monotonic()-start,2),stdout=p.stdout,stderr=p.stderr))
        print(name+': '+('PASS' if p.returncode==0 else 'FAIL'),flush=True)
        if p.returncode:
            print((p.stdout+p.stderr)[-2000:],flush=True)
    summary=dict(passed=sum(r['passed'] for r in results),failed=sum(not r['passed'] for r in results),results=results)
    (A/'tests_v3/v36_test_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}),flush=True)
    sys.exit(bool(summary['failed']))
