"""Offline V3.6 acceptance, integration and read-only-copy development replay."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace

A = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(A))
import build_mode as bm
import design_opt
import interfaces as ic
import lean_chem
import registry
import runner
import workflow
from validate_v3 import fixtures, basis_fixture, leaf
from validate_v35 import fixture, alternatives


def put(ws, name, value):
    (ws/name).write_text(json.dumps(value, indent=1), encoding='utf-8')


def scientific_fixture():
    reaction, out, flow = fixtures()
    basis = basis_fixture()
    r = out['physics']['reactor']
    inlet = {s:-v for s,v in reaction['nu'].items() if v < 0}
    r['inlet_kmol_per_t'] = inlet
    r['outlet_kmol_per_t'] = {s:inlet.get(s, 0)+.9*v for s,v in reaction['nu'].items()}
    flow['streams'][1]['species'] = list(r['outlet_kmol_per_t'])
    product = reaction['product']
    flow['streams'][1].update(P_bar=1, mol_frac={product:1})
    out['physics']['boundary']['product'] = {product: dict(P_bar=1, mol_frac=1)}
    basis.update(ranking_strategy='shared_design')
    basis['utilities']['primary_efficiency'] = dict(leaf(1), unit='dimensionless')
    out['balances']['operating_hours_per_y'] = basis['operating_hours_per_y']['value']
    u = out['physics']['units'][0]
    u.update(computed_by=['unitops.fired_heater', 'unitops.scaled_capex'], efficiency=.85, duty_GJ_per_t=1)
    u['capex_basis'].update(source_capacity=1e5, scale_exponent=.7)
    return SimpleNamespace(REACTION=reaction), out, flow, basis


def hybrid_fixture(ws):
    h = fixture(ws)
    m, out, flow, basis = scientific_fixture()
    params = {k:v['value'] for k,v in bm.basis_values(basis).items()}
    params.update({'design.pressure_bar':9, 'design.stages':1})
    code = ('import copy\nREACTION='+repr(m.REACTION)+'\nPARAMS='+repr(params)+'\nOUT='+repr(out)+
            "\nCANDIDATES={'a':{'topology':0},'b':{'topology':7}}\n"
            "def reference():\n    o=copy.deepcopy(OUT)\n    p=PARAMS['design.pressure_bar']\n"
            "    delta=p+25/p+(PARAMS['design.stages']-2)**2+PARAMS.get('topology',0)\n"
            "    o['cost_usd_per_t']+=delta\n    o['parts']['other']+=delta\n    return o\n"
            "def plant_cost(rec): return reference()\n")
    (ws/'model.py').write_text(code, encoding='utf-8')
    for name, value in [('basis.json',basis), ('flowsheet.json',flow), ('build_version.json',dict(version=bm.BUILD_MODE_VERSION))]:
        put(ws, name, value)
    h.build_version = bm.BUILD_MODE_VERSION
    with (ws/'sources.csv').open('a', encoding='utf-8') as f:
        f.write('design.stages,1,1,3,dimensionless,Finite integer design enumeration.,design_int,,\n')
    alternatives(h, 2)
    assert json.loads(h.b_submit_flowsheet())['passed']
    return h


def expect_error(fn):
    try:
        fn()
    except (ValueError, KeyError):
        return
    raise AssertionError('expected refusal')


def nodes():
    stages = dict(evidence='extraction',basis='parameters',flowsheet='reactor_flowsheet',model_check='model_checks',
                  interface_check='model_checks',independent_validation='feedback',report='report')
    return [dict(node_id=k,node_type=k,stage=v,depends_on=[],inputs={},outputs={},
                 validation_policy='fixed harness gate and artifact inspection',status='planned',skip_reason='') for k,v in stages.items()]


def test_registry():
    assert len(registry.MODULES) == 16
    for mid in registry.MODULES:
        assert callable(registry.resolve(mid))
        e = registry.describe_module(mid)
        assert all(e[k] for k in ('version','capability','inputs','outputs','assumptions','validation','provenance'))
        assert len(json.dumps(e)) < 6000
    assert len(json.dumps(registry.list_modules())) < 6000
    with tempfile.TemporaryDirectory() as tmp:
        m, out, flow, basis = scientific_fixture()
        ws = Path(tmp)
        good = registry.coverage(ws, out)
        assert good['passed'] and not good['warnings'] and good['coverage']['energy']==1
        bad = copy.deepcopy(out); del bad['physics']['units'][0]['computed_by']
        assert not registry.coverage(ws,bad)['passed']
        bad = copy.deepcopy(out); bad['physics']['units'][0]['efficiency']=1.1
        r=registry.coverage(ws,bad); assert r['passed'] and r['warnings']
        bad['physics']['units'][0].update(type='separation',computed_by=['unitops.split'])
        assert not registry.coverage(ws,bad)['passed']
        bad['physics']['units'][0]['energy_method']='experimental pressure-driven calculation'
        assert registry.coverage(ws,bad)['passed']


MODULE = '''META={'inputs':{'x':'GJ/t'},'outputs':{'energy_GJ_per_t':'GJ/t'},
'units':{'x':'GJ/t','energy_GJ_per_t':'GJ/t'},'assumptions':['synthetic identity'],
'applicability':{'x_min':0}}
def compute(x): return {'energy_GJ_per_t':x}
def tests():
    assert compute(0)['energy_GJ_per_t']==0
    assert compute(1)['energy_GJ_per_t']==1
    assert compute(2)['energy_GJ_per_t']==compute(1)['energy_GJ_per_t']*2
    return [{'kind':k,'inputs':{'x':x}} for k,x in [('conservation',2),('limit',0),('reference',1)]]
'''


def test_sandbox():
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); (ws/'modules').mkdir()
        path=ws/'modules/toy.py'; path.write_text(MODULE,encoding='utf-8')
        assert registry.validate_module(ws,'toy')['passed']
        _, out, _, _=scientific_fixture()
        out['physics']['units'][0]['computed_by']=['experimental:toy']
        r=registry.coverage(ws,out); assert r['passed'] and r['warnings'] and r['coverage']['energy']==0
        path.write_text(MODULE+'\n# changed\n',encoding='utf-8')
        assert not registry.coverage(ws,out)['passed']
        path.write_text(MODULE.replace('assert compute(0)', 'assert False and compute(0)'),encoding='utf-8')
        assert not registry.validate_module(ws,'toy')['passed']
        assert not registry.coverage(ws,out)['passed']
        for replacement in ("float('nan')", '-1', "__import__('socket').socket()"):
            path.write_text(MODULE.replace("'energy_GJ_per_t':x}", "'energy_GJ_per_t':"+replacement+'}'),encoding='utf-8')
            assert not registry.validate_module(ws,'toy')['passed']
        simple = MODULE[:MODULE.index('def tests():')]+"def tests(): return [{'kind':k,'inputs':{'x':1}} for k in ['conservation','limit','reference']]\n"
        for expression, reason in [("float('nan')", 'nan'), ('-1','negative')]:
            path.write_text(simple.replace("'energy_GJ_per_t':x}","'energy_GJ_per_t':"+expression+'}'),encoding='utf-8')
            result=registry.validate_module(ws,'toy')
            assert not result['passed'] and reason in str(result['reasons']),result
        path.write_text(simple.replace("def compute(x): return {'energy_GJ_per_t':x}", "counter=0\ndef compute(x):\n global counter\n counter+=1\n return {'energy_GJ_per_t':counter}"),encoding='utf-8')
        result=registry.validate_module(ws,'toy')
        assert not result['passed'] and 'determinism' in str(result['reasons']),result
        path.write_text(simple.replace("'units':{'x':'GJ/t','energy_GJ_per_t':'GJ/t'}", "'units':{'x':'GJ/t'}"),encoding='utf-8')
        result=registry.validate_module(ws,'toy')
        assert not result['passed'] and 'unit keys' in str(result['reasons']),result
        expect_error(lambda:registry.validate_module(ws,'../escape'))


def test_interfaces():
    m,out,flow,basis=scientific_fixture()
    assert ic.reactor_process(m,out,flow).status=='PASS'
    near=copy.deepcopy(out)
    r=near['physics']['reactor']
    r['per_pass_conversion']=ic.equilibrium_conversion(m.REACTION['nu'],m.REACTION['key'],r['feed_mol_frac'],r['T_K'],r['P_bar'])*.99
    assert ic.reactor_process(m,near,flow).status=='WARNING'
    r['per_pass_conversion']=1.1
    assert ic.reactor_process(m,near,flow).status=='BLOCK'
    bad=copy.deepcopy(out); first=next(iter(bad['physics']['reactor']['outlet_kmol_per_t']))
    bad['physics']['reactor']['outlet_kmol_per_t'][first]+=2
    assert ic.reactor_process(m,bad,flow).status=='BLOCK'
    bad=copy.deepcopy(out);bad['physics']['reactor']['heat_duty_GJ_per_t']*=-1
    assert ic.reactor_process(m,bad,flow).status=='BLOCK'
    assert ic.process_tea(out,flow,basis).status=='PASS'
    warning=copy.deepcopy(out);warning['physics']['units'][0]['capex_basis']['cost_index_now']=1
    assert ic.process_tea(warning,flow,basis).status=='WARNING'
    for b in ('battery_limit','utilities','capacity_t_per_y','operating_hours_per_y'):
        bad=copy.deepcopy(basis);del bad[b]
        assert ic.process_tea(out,flow,bad).status=='BLOCK'
    prod=next(iter(basis['product']))
    bad=copy.deepcopy(out);bad['physics']['boundary']['product'][prod]['P_bar']=5
    assert ic.process_tea(bad,flow,basis).status=='BLOCK'          # product pressure off the basis
    bad=copy.deepcopy(out);bad['physics']['boundary']['product'][prod]['mol_frac']=0.5
    assert ic.process_tea(bad,flow,basis).status=='BLOCK'          # purity below the spec
    bad=copy.deepcopy(out);del bad['physics']['boundary']['product']
    assert ic.process_tea(bad,flow,basis).status=='BLOCK'          # product state not reported
    atomic=dict(tof_unit='s^-1',site_density_evidence='synthetic source',dispersion_evidence='synthetic source',
                temperature_range_K=[300,1000],energy_reference_state='standard gas and empty surface',scaling_bep_source='synthetic source')
    assert ic.mkm_reactor(atomic,out).status=='PASS'
    warning=dict(atomic);del warning['dispersion_evidence']
    assert ic.mkm_reactor(warning,out).status=='WARNING'
    assert ic.mkm_reactor(dict(atomic,temperature_range_K=[300,400]),out).status=='WARNING'
    assert ic.mkm_reactor(dict(atomic,tof_unit='kg/h'),out).status=='BLOCK'
    assert ic.dft_mkm(atomic).status=='PASS'
    warning=dict(atomic);del warning['scaling_bep_source']
    assert ic.dft_mkm(warning).status=='WARNING'
    assert ic.dft_mkm({}).status=='BLOCK'
    assert len(ic.check(m,out,flow,basis)['contracts'])==2
    assert len(ic.check(m,out,flow,basis,atomic)['contracts'])==4


def test_workflow():
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp); ns=nodes()
        bad=copy.deepcopy(ns);bad[0]['status']='skipped';bad[0]['skip_reason']='Long explicit reason for skipping a mandatory check.'
        expect_error(lambda:workflow.plan(ws,bad,bm.STAGES))
        workflow.plan(ws,ns,bm.STAGES)
        first=(ws/'workflow/rev_1.json').read_bytes();events=(ws/'workflow_events.jsonl').read_bytes()
        assert workflow.finish_errors(ws,bm.STAGES)
        workflow.revise(ws,[dict(op='update',node_id=n['node_id'],fields=dict(status='validated')) for n in ns], 'validated fixed artifacts',bm.STAGES)
        assert not workflow.finish_errors(ws,bm.STAGES)
        assert first==(ws/'workflow/rev_1.json').read_bytes() and (ws/'workflow_events.jsonl').read_bytes().startswith(events)
        expect_error(lambda:workflow.revise(ws,[dict(op='remove',node_id='evidence')],'attempt',bm.STAGES))
        optional=dict(ns[0],node_id='optional',node_type='calculation',module_id='unitops.split',module_version='UO-1.1',status='skipped',skip_reason='short')
        expect_error(lambda:workflow.revise(ws,[dict(op='add',node_id='optional',node=optional)],'optional branch',bm.STAGES))
        optional['skip_reason']='This optional calculation does not apply to the declared process boundary.'
        workflow.revise(ws,[dict(op='add',node_id='optional',node=optional)],'optional branch',bm.STAGES)
        expect_error(lambda:workflow.revise(ws,[dict(op='update',node_id='evidence',fields=dict(depends_on=['report'])),dict(op='update',node_id='report',fields=dict(depends_on=['evidence']))],'cycle',bm.STAGES))
        snap=runner.seal_snapshot(ws)
        (ws/'workflow/rev_1.json').write_text('forged');(ws/'workflow/rev_99.json').write_text('forged')
        (ws/'workflow_events.jsonl').write_text('forged')
        assert runner.seal_restore(ws,snap) and not (ws/'workflow/rev_99.json').exists()
        assert (ws/'workflow/rev_1.json').read_bytes()==first


def test_integration_design():
    with tempfile.TemporaryDirectory() as tmp:
        ws=Path(tmp);h=hybrid_fixture(ws)
        assert bm.BUILD_MODE_VERSION=='V3.6-hybrid-workflow' and lean_chem.enabled(h) and design_opt.enabled(h)
        check=json.loads(h.b_check_model());assert check['passed'],check
        assert check['coverage']['energy']==1 and (ws/'interface_check.json').exists()
        original=(ws/'model.py').read_text(encoding='utf-8')
        (ws/'model.py').write_text(original.replace("'computed_by': ['unitops.fired_heater', 'unitops.scaled_capex']", "'computed_by': []"),encoding='utf-8')
        rejected=json.loads(h.b_check_model())
        assert not rejected['passed'] and 'module_coverage' in rejected['failures']
        (ws/'model.py').write_text(original,encoding='utf-8')
        assert json.loads(h.b_check_model())['passed']
        assert 'workflow:' in h.b_workspace_digest()
        before={n:(ws/n).read_bytes() for n in ('model.py','sources.csv')}
        result=json.loads(h.b_optimize_design(candidate='a'))
        assert result['status']=='ok',result
        full=json.loads((ws/'design_opt.json').read_text())
        assert len(full['integer_enumeration'])==3 and full['fixed_integers']['design.stages']==2
        assert abs(full['optimum']['values']['design.pressure_bar']-5)<.1
        assert all(isinstance(r['fixed_integers']['design.stages'],int) and 'design.stages' not in r['optimum']['values'] for r in full['integer_enumeration'])
        assert all('start_points' in r and 'convergence' in r and r['evaluations']<=40 for r in full['integer_enumeration'])
        assert before=={n:(ws/n).read_bytes() for n in before}
        a=full['optimum']['cost_usd_per_t']
        result=json.loads(h.b_optimize_design(candidate='b'));assert abs(result['optimum']['cost_usd_per_t']-a-7)<.01
        b=json.loads((ws/'basis.json').read_text());del b['ranking_strategy'];put(ws,'basis.json',b)
        assert 'ranking_strategy' in json.loads(h.b_check_model())['failures']
        b['ranking_strategy']='per_catalyst';put(ws,'basis.json',b)
        assert 'not implemented' in h.b_optimize_design()
        b['ranking_strategy']='shared_design';put(ws,'basis.json',b)
        assert any('workflow' in e for e in h.build_finish_errors())
        # Satisfy the existing finish contracts, then prove the new workflow finish gate.
        json.loads(h.b_check_model())
        fp=h._fingerprint()
        put(ws,'evidence_debt.json',dict(items=[],input_fingerprint=fp))
        put(ws,'critique.json',dict(rounds=[dict(completed=True,issues=[])]))
        put(ws,'analysis.json',{})
        put(ws,'sensitivity.json',dict(input_fingerprint=fp))
        (ws/'report.md').write_text('Synthetic acceptance report.',encoding='utf-8')
        h.b_plan_workflow(nodes())
        assert h.build_finish_errors()
        h.b_revise_workflow([dict(op='update',node_id=n['node_id'],fields=dict(status='validated')) for n in nodes()],'checked all fixed artifacts')
        assert not h.build_finish_errors(),h.build_finish_errors()
        code=(ws/'model.py').read_text();(ws/'model.py').write_text(code.replace("'efficiency': 0.85", "'efficiency': 1.1"),encoding='utf-8')
        assert json.loads(h.b_check_model())['warnings']
        fp=h._fingerprint();put(ws,'evidence_debt.json',dict(items=[],input_fingerprint=fp));put(ws,'sensitivity.json',dict(input_fingerprint=fp))
        assert any('WARNING' in e for e in h.build_finish_errors())
        warnings=json.loads((ws/'module_coverage.json').read_text())['warnings']
        (ws/'report.md').write_text('\n'.join(warnings),encoding='utf-8')
        assert not h.build_finish_errors(),h.build_finish_errors()
    assert design_opt.ranking_failures({}) and design_opt.ranking_failures({'ranking_strategy':'per_catalyst'})
    expect_error(lambda:design_opt.integer_configurations([dict(type='design_int',parameter='n',low=1.2,value=2,high=3,unit='1',note='integer')]))
    tools=bm.hybrid_tools(bm.BUILD_TOOLS)
    for stage in bm.STAGES:
        names={t.get('name',t.get('type')) for t in lean_chem.stage_tools(tools,stage,hybrid=True)}
        assert {'plan_workflow','revise_workflow'}<=names
        if stage in ('model_code','model_checks','atomic_model'):
            assert {'list_modules','describe_module','validate_module'}<=names


def replay():
    run=Path('D:/agent_runs/ch4_v34_t7')
    if not run.exists():
        raise AssertionError('required t7 replay unavailable')
    names=[p.name for p in run.iterdir() if p.is_file()]
    hashes={n:hashlib.sha256((run/n).read_bytes()).hexdigest() for n in names}
    with tempfile.TemporaryDirectory(prefix='v36-t7-copy-') as tmp:
        ws=Path(tmp)
        for n in names:
            shutil.copyfile(run/n,ws/n)
        put(ws,'build_version.json',dict(version=bm.BUILD_MODE_VERSION))
        class Replay(bm.BuildMixin):
            def log(self,event): pass
            def _records(self): return []  # reference-only replay, no extraction/normalisation mutation
        h=Replay();h.ws=ws;h.tok={};h.setup_build('development replay',{})
        m=h._load_model();out=m.reference()
        flow=json.loads((ws/'flowsheet.json').read_text(encoding='utf-8'))
        basis=json.loads((ws/'basis.json').read_text(encoding='utf-8'))
        cov=registry.coverage(ws,out);inter=ic.check(m,out,flow,basis)
        h.b_submit_flowsheet();check=json.loads(h.b_check_model())
        report=dict(scope='read-only-copy reference replay, no LLM/API; original files hashed before/after',
                    coverage=cov,interfaces=inter,ranking_strategy=design_opt.ranking_failures(basis),
                    workflow=workflow.finish_errors(ws,bm.STAGES),model_check=check,original_sha256=hashes)
    assert hashes=={n:hashlib.sha256((run/n).read_bytes()).hexdigest() for n in names}
    (A/'tests_v3/v36_t7_replay.json').write_text(json.dumps(report,indent=1,ensure_ascii=False),encoding='utf-8')
    print('t7 replay:',json.dumps(dict(coverage_blocks=len(cov['blocks']),interface_blocks=len(inter['blocks']),
          verified_share=cov['coverage'],ranking_blocks=len(report['ranking_strategy']),workflow_blocks=len(report['workflow']))))


if __name__=='__main__':
    tests=[test_registry,test_sandbox,test_interfaces,test_workflow,test_integration_design,replay]
    for test in tests:
        test();print(test.__name__+': PASS',flush=True)
    print(f'V3.6: {len(tests)}/{len(tests)} groups passed')
