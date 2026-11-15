"""Offline acceptance runner: at most two workers, no API/LLM calls.

Keep pre-existing historical replay JSON bytes unchanged after regression.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
NAMES=['unitops','v3','v33','v331','v34','v35','v36','evaluation','blind','route_policy','holdout_guard','uo2']


def run(name):
    path=ROOT/'tests_v3'/('validate_'+name+'.py') if name!='physics_gate' else ROOT/'physics_gate_validate.py'
    env=dict(os.environ,PYTHONUTF8='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    try:
        proc=subprocess.run([sys.executable,'-B',str(path)],cwd=ROOT,env=env,capture_output=True,
                            text=True,encoding='utf-8',errors='replace',timeout=600)
        out=dict(name=name,returncode=proc.returncode,output=proc.stdout+proc.stderr)
    except subprocess.TimeoutExpired as exc:
        out=dict(name=name,returncode=-1,output=str(exc))
    print(name+': '+('PASS' if out['returncode']==0 else 'FAIL'),flush=True)
    return out


if __name__=='__main__':
    snapshots={p:p.read_bytes() for p in (ROOT/'tests_v3').glob('v*_t7_replay.json')}
    try:
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(run,NAMES+['physics_gate']))
    finally:
        for p,data in snapshots.items():
            if p.read_bytes()!=data: p.write_bytes(data)
    (ROOT/'tests_v3'/'uo2_regression_results.json').write_text(json.dumps(results,indent=1,ensure_ascii=False),encoding='utf-8')
    sys.exit(int(any(r['returncode'] for r in results)))
