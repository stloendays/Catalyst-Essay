"""V3.4 offline acceptance tests. No Run constructor, API, or external workspace writes."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

A = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(A))
import build_mode as bm
import lean_chem as lc
import runner
from physics_gate import CATEGORIES

class H(bm.BuildMixin):
    t_read_file = runner.Run.t_read_file
    def __init__(self, ws, version=None):
        self.ws = ws
        self.tok = dict(agent_in=0, agent_out=0, extract_in=0, extract_out=0, extract_calls=0)
        self.events = []
        self.reaction, self.model = 'generic toy', 'stub'
        if version:
            (ws / 'build_version.json').write_text(json.dumps(dict(version=version)), encoding='utf-8')
        self.setup_build('toy', {})
    def path(self, p):
        return self.ws / p
    def log(self, event):
        self.events.append(event)
    def _fingerprint(self):
        return 'toy'


def dump(ws, name, data):
    (ws / name).write_text(json.dumps(data), encoding='utf-8')

with tempfile.TemporaryDirectory() as tmp:
    ws = Path(tmp)
    h = H(ws)
    assert h.build_version == 'V3.4-lean-chem'
    (ws / 'read.txt').write_text('hello\nworld\n' * 300, encoding='utf-8')
    h._turn, h._call_id, h._history = 7, 'read1', []
    first = h.t_read_file('read.txt', 0, 100)
    h._history.append(dict(type='function_call_output', call_id='read1', output=first))
    assert h.t_read_file('read.txt', 0, 100).startswith('unchanged since turn 7 (sha ')
    assert h.t_read_file('read.txt', 100, 100).startswith('[600 lines]')
    assert h.t_read_file('read.txt', 0, 100, force=True) == first
    # Actual observation masking, then reset eviction, must both permit rereading.
    runner.compact_history(h._history, keep_last=0, batch=1)
    assert 'older output masked' in h._history[0]['output']
    assert h.t_read_file('read.txt', 0, 100) == first
    h._history = []
    assert h.t_read_file('read.txt', 0, 100) == first
    (ws / 'read.txt').write_text('changed', encoding='utf-8')
    assert 'changed' in h.t_read_file('read.txt', 0, 100)
    h.build_version = 'V3.3.1-engineering-ledger'
    assert h.t_read_file('read.txt', 0, 10) == h.t_read_file('read.txt', 0, 10)
    h.build_version = bm.BUILD_MODE_VERSION
    print('1 read cache, force, slice, change, masking/reset, old version: PASS')

    types = ['compressor', 'separation', 'knockout', 'heat_exchanger', 'furnace', 'other', 'other', 'reactor']
    categories = ['feed_preparation', 'separation_and_purification', 'separation_and_purification',
                  'heat_recovery', 'reactor_heat_supply_or_removal', 'recycle', 'utilities_and_offsites', 'reactor_heat_supply_or_removal']
    units = [dict(name=f'unit {i}', type=t, purpose='toy', inlets=[f's{i}'], outlets=[f's{i+1}']) for i,t in enumerate(types)]
    checklist = {c: {'excluded': 'Toy test excludes this category with a sufficiently long reason.'} for c in CATEGORIES}
    for u,c in zip(units,categories):
        if 'included' not in checklist[c]:
            checklist[c] = dict(included=[])
        checklist[c]['included'].append(u['name'])
    flow = dict(units=units, streams=[], checklist=checklist, diagram='toy graph')
    for i in range(len(units)+1):
        flow['streams'].append(dict(name=f's{i}', **{'from': 'boundary' if i==0 else units[i-1]['name'],
            'to': 'boundary' if i==len(units) else units[i]['name']}, species=['Ar']))
    dump(ws, 'flowsheet.json', flow)
    dump(ws, 'basis.json', dict(capacity_t_per_y=dict(value=1000), feeds={'Ar': dict(T_K=300, P_bar=1)}))
    dump(ws, 'evidence_debt.json', dict(input_fingerprint='toy', items=[dict(item='a',status='open')]))
    dump(ws, 'critique.json', dict(rounds=[dict(issues=[dict(id='r1:a',severity='major',issue='toy')])]))
    dump(ws, 'model_check.json', dict(passed=False, failures={'physics':['cooling_utility: toy']}))
    for name in ('energy_ledger.csv','capex_ledger.csv'):
        (ws/name).write_text('unit,value\nu,1\n', encoding='utf-8')
    digest = h.b_workspace_digest()
    assert len(digest)/4 < 2500 and digest == h.b_workspace_digest()
    for term in ('basis:', 'units:', 'last_check:', 'open_debt:', 'open_critique:', 'stage_notes:', 'energy_ledger.csv:', 'capex_ledger.csv:'):
        assert term in digest
    print(f'2 digest: {len(digest)/4:.2f} estimated tokens: PASS')
    h.stage_notes = ['x'*20000]*30
    assert len(h.b_workspace_digest())/4 < 2500

    debts = [dict(item='a',action='kept_as_uncertainty',note='A source uncertainty remains and is tested over its declared range.',evidence=['source'])]
    critiques = [dict(id='r1:a',action='fixed',note='corrected')]
    initial_debt = (ws/'evidence_debt.json').read_text(encoding='utf-8')
    expected = [h.b_resolve_debt(**d) for d in debts]
    state = json.loads((ws/'evidence_debt.json').read_text(encoding='utf-8'))
    (ws/'evidence_debt.json').write_text(initial_debt,encoding='utf-8')
    assert json.loads(h.b_resolve_debts(debts)) == expected
    assert json.loads((ws/'evidence_debt.json').read_text(encoding='utf-8')) == state
    initial = (ws/'critique.json').read_text(encoding='utf-8')
    # Freeze timestamp so sequential and batch outputs can be compared exactly.
    with patch.object(bm, 'datetime') as dt:
        dt.now.return_value.isoformat.return_value = 'fixed-time'
        expected = [h.b_respond_critique(**d) for d in critiques]
        state = json.loads((ws/'critique.json').read_text(encoding='utf-8'))
        (ws/'critique.json').write_text(initial,encoding='utf-8')
        assert json.loads(h.b_respond_critiques(critiques)) == expected
        assert json.loads((ws/'critique.json').read_text(encoding='utf-8')) == state
    assert json.loads(h.b_resolve_debts([])) == []
    print('3 real batch handlers equal sequential outputs and state: PASS')

    # Submit integration: only basis schema is stubbed; actual graph validator runs.
    with patch.object(bm, 'check_basis', return_value=[]):
        assert json.loads(h.b_submit_flowsheet())['passed']
    path = ws/'model_skeleton.py'
    spec = importlib.util.spec_from_file_location('toy_skeleton', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert len(m.UNIT_FUNCTIONS) == len(units)
    for u in units:
        assert repr(u['name']) in path.read_text(encoding='utf-8')
    for call in ('compressor','separator_energy','split','cooling_utility','fired_heater','heat_recovery','recycle_loop','plant_cost_share','scaled_capex'):
        assert 'unitops.'+call in path.read_text(encoding='utf-8')
    assert 'boundary_role' in path.read_text(encoding='utf-8')
    h.build_version = 'V3.3.1-engineering-ledger'; path.unlink()
    with patch.object(bm, 'check_basis', return_value=[]):
        assert json.loads(h.b_submit_flowsheet())['passed']
    assert not path.exists()
    h.build_version = bm.BUILD_MODE_VERSION
    print('4 submitted flowsheet skeleton imports, every unit, all unitops, V331 unchanged: PASS')

    keep = {'search_papers','screen_papers','download_papers','ocr_papers','extract_papers','read_file','write_file','finish','run_python'}
    base = bm.BUILD_TOOLS + [t for t in runner.FULL_TOOLS+runner.TOOLS if t.get('name') in keep]
    base = list({t.get('name',t['type']):t for t in base}.values())
    menu = bm.lean_tools(base)
    for stage in bm.STAGES:
        names = {t.get('name',t['type']) for t in lc.stage_tools(menu,stage)}
        assert lc.ALWAYS <= names
        if stage=='model_code':
            assert not (lc.LITERATURE | {'web_search'}) & names
            assert {'check_model','run_python'} <= names
        if stage=='feedback':
            assert {'resolve_debts','respond_critiques'} <= names
    assert 'force' not in next(t for t in base if t.get('name')=='read_file')['parameters']['properties']
    print('5 scoped menus and unchanged legacy schemas: PASS')

    diagnosed = lc.diagnosis({'physics':['cooling_utility: same']*41 + ['capital_scaling: other']*2})
    assert len(diagnosed['physics'])==2 and diagnosed['physics'][0]['count']==41
    assert diagnosed['physics'][0]['hint']=='use unitops.cooling_utility'
    for prefix in lc.HINTS:
        assert lc.diagnosis({'physics':[prefix+': toy']})['physics'][0]['hint']==lc.HINTS[prefix]
    output = dict(cost_usd_per_t=10, parts={'cost':10}, operating={'per_pass_conversion':0.5},
                  balances=dict(key_feed_t_per_t=1, energy_GJ_per_t=1, capex_usd=1, capacity_t_per_y=1000),
                  physics={'units':[]})
    module = SimpleNamespace(REACTION=dict(key='A',product='B',MW={'A':1,'B':1}),
                             reference=lambda:output, plant_cost=lambda rec:output)
    records = [dict(paper='toy',idx=i,S=0.5,r=1) for i in range(45)]
    (ws/'sources.csv').write_text('parameter,type,low,high\nx,assumption,1,2\n',encoding='utf-8')
    with patch.object(h,'_load_model',return_value=module), patch.object(h,'_records',return_value=records), \
         patch.object(h,'_check_params',return_value=[]), patch.object(bm,'check_basis',return_value=[]), \
         patch.object(bm,'price_failures',return_value=[]), \
         patch.object(bm,'check_physics',return_value=['cooling_utility: repeated']):
        result = json.loads(h.b_check_model())
        assert not result['passed']
        assert result['failures']['physics'] == [dict(message='cooling_utility: repeated',count=41,hint='use unitops.cooling_utility')]
        assert json.loads((ws/'model_check.json').read_text(encoding='utf-8')) == result
        h.build_version='V3.3.1-engineering-ledger'
        old=json.loads(h.b_check_model())
        assert isinstance(old['failures']['physics'][0],str) and 'reference: ' in old['failures']['physics'][0]
        h.build_version=bm.BUILD_MODE_VERSION
    print('6 duplicate failures counted, generic prefix hints: PASS')

    for d in ('pdf','ocr','extracted'):
        (ws/d).mkdir(exist_ok=True)
    (ws/'pdf/paper.pdf').write_bytes(b'toy PDF')
    (ws/'ocr/paper.md').write_text('toy OCR',encoding='utf-8')
    dump(ws/'ocr', 'paper_figs.json', [])
    h.reuse_extraction, h.extract_model, h.extract_workers = True, 'stub-extractor', 4
    h.extraction_cache_root = ws/'cache'
    import full_mode
    calls = []
    def fake_extract(*args, **kwargs):
        calls.append(1)
        dump(ws/'extracted', 'paper.json', dict(records=[dict(value=1)],notes='toy'))
        return [dict(paper='paper',prompt_tokens=10,completion_tokens=3,n_records=1)]
    with patch.object(full_mode.chain,'extract',side_effect=fake_extract):
        h.b_extract_papers('toy','A','B','none','scope')
        assert len(calls)==1
        (ws/'extracted/paper.json').unlink()
        before = copy.deepcopy(h.tok)
        result = json.loads(h.b_extract_papers('toy','A','B','none','scope'))
        assert len(calls)==1 and result[0]['cache_hit'] and h.tok==before
        assert any('extraction_cache_hit' in e for e in h.events)
        (ws/'extracted/paper.json').unlink()
        h.b_extract_papers('toy','A','B','none','new scope')
        assert len(calls)==2
        (ws/'extracted/paper.json').unlink()
        h.extract_model='different'
        h.b_extract_papers('toy','A','B','none','new scope')
        assert len(calls)==3
        (ws/'extracted/paper.json').unlink()
        (ws/'pdf/paper.pdf').write_bytes(b'changed PDF')
        h.b_extract_papers('toy','A','B','none','new scope')
        assert len(calls)==4
    print('7 actual build extraction hit without network/tokens, PDF/prompt/model invalidation: PASS')

    for group,limit in set(lc.GROUPS.values()):
        stages = [s for s,v in lc.GROUPS.items() if v==(group,limit)]
        x = SimpleNamespace(stage=stages[0])
        for i in range(limit-1):
            assert lc.turn_warning(x) is None
        assert 'wrap this stage up' in lc.turn_warning(x)
        x.stage=stages[-1]
        assert lc.turn_warning(x) is None
    print('8 grouped soft budgets, one reminder, no stop: PASS')
print('V3.4: 8/8 feature groups passed')


def _extras():
    """Main-session additions (agy trace audit): model.py import check after edits, engineering-only critic, stage prompt."""
    import tempfile, types
    import runner, lean_chem, build_mode
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        h = types.SimpleNamespace(ws=ws, build=True, build_version="V3.4-lean-chem")
        h._model_import_check = types.MethodType(runner.Run._model_import_check, h)
        (ws / "model.py").write_text("def reference():\n    return {'cost_usd_per_t': cool_T}\n", encoding="utf-8")
        msg = h._model_import_check()
        assert "FAILED" in msg and "NameError" in msg, msg
        assert h._model_import_check() == "", "unchanged model.py is not rechecked"
        (ws / "model.py").write_text("def reference():\n    return {'cost_usd_per_t': 12.5}\n", encoding="utf-8")
        msg = h._model_import_check()
        assert "reference cost 12.5" in msg, msg
    assert "Do not\nreport wording" in lean_chem.CRITIC_ADDENDUM and "do not repeat the current stage" in lean_chem.PROMPT
    print("V3.4 extras: model.py import check catches NameError, skips unchanged file; critic engineering-only: PASS")


_extras()
