"""Bounded subprocess worker: isolate potentially slow phase-stability solves."""
import json,sys
from pathlib import Path
from dataclasses import replace
import numpy as np
import coupling as C

def job(args):
    p,x,t2,pg,target=map(float,args)
    s=C.cold_settings(p,x,t2,pg)
    raw=C.cold.solve(s,check_stability=False)
    return C.flow_record(s,raw,target)

if __name__=='__main__':
    try:
        value=job(sys.argv[1:])
        print(json.dumps({'record':value},default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist(),allow_nan=False))
    except Exception as e:
        print(json.dumps({'record':None,'reason':type(e).__name__+': '+str(e)}))
