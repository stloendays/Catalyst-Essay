"""Offline V3.5 acceptance and read-only development replay; no APIs."""
import copy
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

A = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(A))
import build_mode as bm
import design_opt as d
import lean_chem
from physics_gate import check_physics, design_checks
from validate_v3 import fixtures, basis_fixture, Harness


def source(ws, value=9, low=1, high=10, typ='design', note='Free pressure choice for compression/separation trade-off.'):
    with (ws/'sources.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, ['parameter','value','low','high','unit','note','type','source','location'])
        w.writeheader()
        w.writerow(dict(parameter='design.pressure_bar',value=value,low=low,high=high,unit='bar',note=note,type=typ))


def fixture(ws, value=9, low=1, high=10, reject=False):
    (ws/'build_version.json').write_text(json.dumps(dict(version='V3.5-design-opt')),encoding='utf-8')
    h=Harness(ws)
    reaction, out, flow=fixtures()
    basis=basis_fixture()
    # Existing synthetic reaction fixture, with scalar design cost p+25/p (minimum p=5).
    params={k:v['value'] for k,v in bm.basis_values(basis).items()}
    params['design.pressure_bar']=value
    (ws/'model.py').write_text('import copy\nREACTION='+repr(reaction)+'\nPARAMS='+repr(params)+'\nOUT='+repr(out)+"\ndef reference():\n    o=copy.deepcopy(OUT)\n    p=PARAMS['design.pressure_bar']\n    o['cost_usd_per_t']=100+p+25/p\n    o['parts']['other'] += p+25/p\n" + ("    if p<6: o['physics']['boundary']['out_t_per_t']['CH4']=0\n" if reject else '') + "    return o\ndef plant_cost(rec): return reference()\n",encoding='utf-8')
    for name,obj in [('basis.json',basis),('flowsheet.json',flow)]:
        (ws/name).write_text(json.dumps(obj),encoding='utf-8')
    source(ws,value,low,high)
    assert json.loads(h.b_submit_flowsheet())['passed']
    for topic in ('mechanism','kinetics','reactor','separation','boundary'):
        h.b_record_decision(topic,'option a',[],'synthetic fixture',['synthetic'])
    return h


def alternatives(h, count):
    # Computed via the fixed library, not prose estimates.
    import unitops
    alts=[]
    for i in range(count):
        duty=unitops.separator_energy(10,[dict(kmol_per_t=1,P_out_bar=1+i,P_required_bar=10)])
        cap=unitops.plant_cost_share(1e6,.1*(i+1),cost_year=2024,size_basis='toy')
        alts.append(dict(name=f'option {i}',energy_GJ_per_t=duty['purchased_energy_GJ_per_t'],capex_usd=cap['capex_usd'],chosen=i==0))
    h.b_record_decision('separation','option 0',alts,'computed with unitops',['unitops'])


def validate():
    assert not d.source_failures([dict(parameter='catalyst_mass_kg',type='assumption')])
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); h=fixture(ws)
        assert h.build_version=='V3.5-design-opt'
        assert lean_chem.enabled(h)
        alternatives(h,2)
        assert json.loads(h.b_check_model())['passed']
        before={n:(ws/n).read_bytes() for n in ('model.py','sources.csv')}
        summary=json.loads(h.b_optimize_design())
        result=json.loads((ws/'design_opt.json').read_text())
        p=result['optimum']['values']['design.pressure_bar']
        assert abs(p/5-1)<.02, result
        assert result['evaluations']<=40 and len(json.dumps(summary))<4500
        assert result['optimum']['cost_usd_per_t']<result['start']['cost_usd_per_t']
        assert before=={n:(ws/n).read_bytes() for n in before}
        assert 'last_optimisation:' in h.b_workspace_digest() and 'design_variables:' in h.b_workspace_digest()
        again=json.loads(h.b_optimize_design())
        assert again==summary
        print(f'1 optimum p={p:.8f}, evaluations={result["evaluations"]}, deterministic subprocess and immutable inputs: PASS')
        source(ws,typ='assumption',note='')
        assert 'sources' in json.loads(h.b_check_model())['failures']
        reason='Pressure fixed by upstream specification'
        assert len(reason)==40
        source(ws,typ='assumption',note=reason[:-1])
        assert 'sources' in json.loads(h.b_check_model())['failures']
        source(ws,typ='assumption',note=reason)
        assert json.loads(h.b_check_model())['passed']
        source(ws)
        alternatives(h,1)
        assert 'decisions' in json.loads(h.b_check_model())['failures']
        alternatives(h,2)
        assert json.loads(h.b_check_model())['passed']
        print('2 real check_model declaration, 40-character reason and alternatives gates: PASS')
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); h=fixture(ws,value=2,low=1,high=3)
        r=json.loads(h.b_optimize_design())
        assert abs(r['optimum']['values']['design.pressure_bar']-3)<1e-5 and r['variables_at_bound']==['design.pressure_bar'],r
        assert r['evaluations']<=40
        print('3 bounds and bound reporting: PASS')
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); h=fixture(ws,value=9,reject=True)
        json.loads(h.b_optimize_design())
        r=json.loads((ws/'design_opt.json').read_text())
        assert r['optimum']['values']['design.pressure_bar']>=6 and r['rejected_points'],r
        assert any('boundary' in v['reason'] for v in r['rejected_points'])
        assert all(1<=v['values']['design.pressure_bar']<=10 for v in r['rejected_points'])
        assert 'cost_usd_per_t' in r['start']
        print('4 real physics-failing points rejected: PASS')
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); h=fixture(ws,value=2,low=1,high=3,reject=True)
        r=json.loads(h.b_optimize_design())
        assert r['status']=='no_feasible_point' and r['optimum'] is None and r['evaluations']<=40
        assert not r['start']['feasible'] and 'cost_usd_per_t' in r['start']
    u=dict(name='capital',type='other',capex_basis=dict(method='plant_specific_cost_share',scale_exponent=1.0))
    f=[]; design_checks([u],basis_fixture(),f); assert any('capital_exponent' in x for x in f)
    u['capex_basis']['scale_exponent']=.7
    f=[]; design_checks([u],basis_fixture(),f); assert not f
    u['capex_basis'].update(scale_exponent=1., exponent_evidence=dict(type='published',source='https://example.org/toy',location='Table 1'))
    f=[]; design_checks([u],basis_fixture(),f); assert not f
    u['capex_basis']['exponent_evidence']['source']=''
    f=[]; design_checks([u],basis_fixture(),f); assert f
    comp=dict(name='product',type='compressor',boundary_role='product_conditioning',P_out_bar=1.021)
    f=[]; design_checks([comp],basis_fixture(),f); assert any('product_pressure' in x for x in f)
    comp['P_out_bar']=1.02
    f=[]; design_checks([comp],basis_fixture(),f); assert not f
    print('5 exponent 1/.7/evidence, invalid evidence and product pressure tolerance: PASS')
    replay()


def replay():
    run=Path('D:/agent_runs/ch4_v34_t7')
    if not run.exists():
        print('t7 replay unavailable'); return
    names=['model.py','sources.csv','decisions.jsonl','energy_ledger.csv','capex_ledger.csv','basis.json']
    hashes={n:hashlib.sha256((run/n).read_bytes()).hexdigest() for n in names}
    sys.path.insert(0,str(run))
    try:
        spec=importlib.util.spec_from_file_location('replay_t7',run/'model.py')
        m=importlib.util.module_from_spec(spec);exec(compile((run/'model.py').read_text(encoding='utf-8'),str(run/'model.py'),'exec'),m.__dict__)
        out=m.reference()
    finally:
        sys.path.remove(str(run))
    flow=json.loads((run/'flowsheet.json').read_text(encoding='utf-8'))
    basis=json.loads((run/'basis.json').read_text(encoding='utf-8'))
    old=check_physics(m,out,flow,basis=basis,ledger=True)
    new=check_physics(m,out,flow,basis=basis,ledger=True,design=True)
    with (run/'sources.csv').open(encoding='utf-8') as f:
        declarations=d.source_failures(list(csv.DictReader(f)))
    decisions=d.decision_failures([json.loads(x) for x in (run/'decisions.jsonl').read_text().splitlines() if x.strip()])
    assert any('capital_exponent' in x for x in new)
    assert declarations and any('separation' in x for x in decisions)
    # Original basis explicitly specifies 40 bar, so no actual overcompression failure.
    assert not any('product_pressure' in x for x in new)
    negative=copy.deepcopy(basis)
    negative['product'][m.REACTION['product']]['P_bar']['value']=20
    assert any('product_pressure' in x for x in check_physics(m,out,flow,basis=negative,ledger=True,design=True))
    assert hashes=={n:hashlib.sha256((run/n).read_bytes()).hexdigest() for n in names}
    report=dict(old_physics_failures=old,new_physics_failures=new,undeclared_design=declarations,decisions=decisions,
                cost_usd_per_t=out['cost_usd_per_t'], energy_GJ_per_t=out['balances']['energy_GJ_per_t'],capex_usd=out['balances']['capex_usd'],
                basis_product_pressure_bar=basis['product'][m.REACTION['product']]['P_bar']['value'],
                original_hashes=hashes)
    (A/'tests_v3/v35_t7_replay.json').write_text(json.dumps(report,indent=1,ensure_ascii=False),encoding='utf-8')
    print(f'6 t7: old physics {len(old)}, new physics {len(new)}, declaration {len(declarations)}, decisions {len(decisions)}; original basis=40 bar; 20-bar negative control rejected: PASS')

if __name__=='__main__':
    validate()
    print('V3.5: 6/6 feature groups passed')
