"""T1 reference-only IDAES subprocess bridge. No IDAES/Pyomo harness imports.

Case units are independent reference snapshots unless an explicit inlet_from
names an earlier outlet. Numeric basis: kmol/t -> mol/s with a synthetic
1 t/s throughput; solved watts / 1e9 returns GJ/t, with no annualization.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tempfile

DEFAULT_PYTHON = r'D:\Tools\idaes-env\Scripts\python.exe'
SUPPORTED = ('Compressor','PressureChanger','Heater','Flash','Mixer','Separator',
             'StoichiometricReactor','EquilibriumReactor','GibbsReactor')


def run(case: dict) -> dict:
    """Run a JSON case in the IDAES env, 300 s deadline; compact error or results."""
    python = os.environ.get('IDAES_PYTHON',DEFAULT_PYTHON)
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', IDAES_DATA=env.get('IDAES_DATA',r'D:\Tools\idaes-env\idaes-data'),
               OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PATH'] = env.get('IDAES_BIN',r'D:\Tools\idaes-env\idaes-bin')+os.pathsep+env.get('PATH','')
    try:
        deadline=time.monotonic()+300
        with tempfile.TemporaryDirectory(prefix='idaes-case-') as tmp:
            path=Path(tmp)/'case.json'; result=Path(tmp)/'result.json'
            path.write_text(json.dumps(case,allow_nan=False),encoding='utf-8')
            p=subprocess.run([python,'-B',str(Path(__file__).with_name('idaes_runner')/'run_case.py'),str(path),str(result)],
                             cwd=tmp,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
            recovered = False
            # Windows uv venvs can retain an inaccessible/moved base path. Use
            # the available same-version BASE interpreter in an isolated child,
            # exposing only the existing IDAES environment packages.
            if not result.exists() and 'Unable to create process' in (p.stderr+p.stdout):
                env_root=Path(python).resolve().parents[1]
                p=subprocess.run([sys._base_executable,'-I','-S','-B',
                                  str(Path(__file__).with_name('idaes_runner')/'bootstrap_env.py'),
                                  str(env_root),str(path),str(result)],cwd=tmp,env=env,
                                 capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(.01,deadline-time.monotonic()))
                recovered=True
            if result.exists():
                out=json.loads(result.read_text(encoding='utf-8'))
                out['environment_launcher']='isolated relocated-venv bootstrap' if recovered else 'IDAES venv python'
                if p.returncode and out.get('ok'): return dict(ok=False,error='runner failed after producing output')
                return out
            return dict(ok=False,error=('IDAES subprocess failed: '+(p.stderr or p.stdout))[-1500:],returncode=p.returncode)
    except subprocess.TimeoutExpired:
        return dict(ok=False,error='IDAES subprocess timeout (300 s)')
    except (OSError,ValueError,TypeError) as exc:
        return dict(ok=False,error=f'{type(exc).__name__}: {exc}')


def reference_case(model_module_or_reference_out):
    """Map explicit physics-unit states; never invent missing composition or state.

    Units may declare idaes_case with one of SUPPORTED types and feed/T/P;
    otherwise map recognized type plus explicit inlet_kmol_per_t or feed
    {kmol_per_t,mol_frac}. Unsupported/incomplete units are reported as skipped.
    """
    obj=model_module_or_reference_out
    ref=obj.reference() if hasattr(obj,'reference') else obj
    units=[]; skipped=[]; originals={}
    physics=ref.get('physics',{})
    reactor_count=sum(u.get('type')=='reactor' for u in physics.get('units',[]))
    for u in physics.get('units',[]):
        if u.get('type')=='reactor' and reactor_count==1:
            u=dict(physics.get('reactor',{}),**u)
            if hasattr(obj,'REACTION') and 'nu_list' not in u:
                u['nu_list']=[obj.REACTION['nu']]
        name=u.get('name','?')
        try:
            if name in originals: raise ValueError('duplicate unit name')
            spec=dict(u.get('idaes_case') or {})
            types=dict(compressor='Compressor',heat_exchanger='Heater',knockout='Flash',
                       reactor='EquilibriumReactor',mixer='Mixer',separator='Separator')
            kind=spec.get('type',types.get(u.get('type')))
            if kind not in SUPPORTED: raise ValueError('no IDAES counterpart')
            spec.update(name=name,type=kind)
            if 'feed' not in spec:
                feed=u.get('inlet_kmol_per_t')
                if feed is None:
                    f=u['feed']; feed={s:y*f['kmol_per_t'] for s,y in f['mol_frac'].items()}
                spec['feed']=feed
            for target,candidates in [('T_in_K',('T_in_K','T_K')),('P_in_bar',('P_in_bar','P_bar'))]:
                if target not in spec:
                    value=next((u[k] for k in candidates if k in u),None)
                    if value is None and target=='P_in_bar': value=u.get('feed',{}).get('P_bar')
                    if value is None: raise ValueError('missing '+target)
                    spec[target]=value
            for k in ('T_out_K','P_out_bar','eta_isentropic','nu_list','extents_kmol_per_t','split_fraction','inlets'):
                if k in u and k not in spec: spec[k]=u[k]
            if kind in ('Compressor','PressureChanger') and 'P_out_bar' not in spec: raise ValueError('missing P_out_bar')
            if kind in ('Heater','Flash','EquilibriumReactor','GibbsReactor','StoichiometricReactor') and 'T_out_K' not in spec:
                if 'T_K' in u: spec['T_out_K']=u['T_K']
                else: raise ValueError('missing T_out_K')
            if kind=='EquilibriumReactor' and 'nu_list' not in spec: raise ValueError('missing explicit reaction stoichiometry')
            units.append(spec); originals[name]=u
        except (KeyError,TypeError,ValueError) as exc: skipped.append(dict(name=name,reason=str(exc)))
    return dict(units=units),originals,skipped


def idaes_check(model_module_or_reference_out):
    """T1 ideal-gas reference check; >5% WARNING, no scoring or model mutation."""
    case,originals,skipped=reference_case(model_module_or_reference_out)
    if not case['units']: return dict(ok=False,error='No units have complete IDAES states',skipped=skipped,comparisons=[])
    result=run(case)
    if not result.get('ok'): return dict(result,skipped=skipped,comparisons=[])
    rows=[]
    for solved in result['units']:
        u=originals[solved['name']]
        for field in ('power_GJ_per_t','heat_duty_GJ_per_t'):
            if field not in u or field not in solved: continue
            a,b=u[field],solved[field]; difference=abs(a-b)/max(abs(b),1e-10)
            rows.append(dict(unit=u['name'],field=field,harness=a,idaes=b,relative_difference=difference,
                             status='WARNING' if difference>.05 else 'PASS'))
        expected=u.get('outlet_kmol_per_t',{})
        for s,a in expected.items():
            if s not in solved.get('outlet_kmol_per_t',{}): continue
            b=solved['outlet_kmol_per_t'][s]; difference=abs(a-b)/max(abs(b),1e-8)
            rows.append(dict(unit=u['name'],field='outlet.'+s,harness=a,idaes=b,relative_difference=difference,
                             status='WARNING' if difference>.05 else 'PASS'))
        for phase in ('vapor','liquid'):
            key=phase+'_kmol_per_t'
            for s,a in u.get(key,{}).items():
                if s not in solved.get(key,{}): continue
                b=solved[key][s]; difference=abs(a-b)/max(abs(b),1e-8)
                rows.append(dict(unit=u['name'],field=phase+'.'+s,harness=a,idaes=b,relative_difference=difference,
                                 status='WARNING' if difference>.05 else 'PASS'))
    return dict(ok=True,comparisons=rows,skipped=skipped,solver_status=result['solver_status'],
                status='WARNING' if skipped or any(r['status']=='WARNING' for r in rows) or not rows else 'PASS')
