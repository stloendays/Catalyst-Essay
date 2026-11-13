"""Offline integration/definition checks. No runner, network, or paid LLM calls.

All synthetic runs, empty holdout copies, audit results and evaluation outputs
are created under TEMP; existing evaluation/ and D:/agent_runs are read-only.
"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE))
import blind_eval as be
import evaluate_builds as eb
import audit_holdout as ah

TOY='''REACTION = {"key":"N2","product":"NH3","cofeed":"H2","MW":{"NH3":17.03052},"nu":{"N2":-1,"H2":-3,"NH3":2}}
PARAMS = {"compressor_efficiency":0.75}
def plant_cost(rec):
    parts={"feed":100.0/max(rec["S"],0.01),"energy":20.0/max(rec["X"],0.001),"capital":50.0,"catalyst":1.0/max(rec["r"],1e-8),"other":5.0}
    return {"cost_usd_per_t":sum(parts.values()),"parts":parts,
      "operating":{"T_K":rec["T_K"],"P_bar":rec["P_bar"],"per_pass_conversion":rec["X"]},
      "balances":{"capacity_t_per_y":100000,"energy_GJ_per_t":2,"capex_usd":1000000},
      "physics":{"boundary":{"in_t_per_t":{},"out_t_per_t":{}},"units":[]}}
def reference():
    return dict(plant_cost({"T_K":673.15,"P_bar":100,"X":0.2,"S":1,"r":1}),name="offline toy")
'''


def main():
    root=Path(tempfile.mkdtemp(prefix='blind_validation_'))
    toy=root/'toy';toy.mkdir();(toy/'model.py').write_text(TOY,encoding='utf-8')
    (toy/'analysis.json').write_text(json.dumps({'attribution_share':{'activity':.8,'selectivity':.2}}),encoding='utf-8')
    outputs={}
    for rx in ['nh3','meoh']:
        with contextlib.redirect_stdout(io.StringIO()):
            out=be.evaluate(rx,[toy],root/'evaluation')
        for section in ['loader','hand_counts','hand_reference','builds','agreement','primary_build_median_reference','rules']:
            assert section in out,section
        loader=out['loader'];b=out['builds'][str(toy)]
        assert loader['converted']+loader['rejected']==loader['total']
        assert b['n_costed']+len(b['cost_failures'])==loader['converted']
        assert not b['cost_failures']
        assert b['ranking']['groups']==(44 if rx=='nh3' else 63)
        for section in ['ranking','reference_comparison','hand_comparison','bottlenecks','diagnosis']:
            assert b[section],section
        for comparison in b['hand_comparison'].values():
            assert comparison['compared_groups']==comparison['hand_summary']['groups']
            assert comparison['verdict_agreements']+comparison['verdict_disagreements']==comparison['compared_groups']
            assert all(r['complete'] for r in comparison['groups'])
        for ext in ['json','md']:
            assert (root/'evaluation'/f'{rx}_blind.{ext}').stat().st_size>100
        outputs[rx]={'loader':{k:loader[k] for k in ['total','converted','rejected']},'hand_counts':out['hand_counts'],
                     'toy_ranking':b['ranking'],'costed':b['n_costed']}
    assert outputs['nh3']['hand_counts']['printed']['changed']==12
    assert outputs['meoh']['hand_counts']['fixed_conversion']['changed']==26
    assert outputs['meoh']['hand_counts']['raised_conversion']['changed']==21
    # Unit anchors and tie rules are independent of the toy cost implementation.
    f,_=be.hand_tables('nh3');recs,_=be.load_records('nh3',f)
    r=recs['nh3:0000'];assert abs(r['r']-13800*17.03052e-6)<1e-12
    assert abs(r['X']-.0093/(.5*1.0093))<1e-12 and r['P_bar']==4
    assert r['components']==[['Ru',8.3]]
    f,_=be.hand_tables('meoh');recs,_=be.load_records('meoh',f)
    assert abs(recs['meoh:0000']['r']-.2973470153)<1e-12
    assert abs(recs['meoh:0000']['y_key']-.1538461538)<1e-12
    # All records share one lab leader; two temperatures of it are one MeOH catalyst.
    import pandas as pd
    tie=pd.DataFrame(dict(group=['g']*3,identity=['a','a','b'],lab=[1.,2.,2.],doi=['p']*3,cost=[2.,3.,1.]))
    assert not be.group_verdicts(tie,'meoh','cost')[0]['changed']
    # A failed record must exclude its complete original group from comparison.
    bad=root/'bad';bad.mkdir()
    (bad/'model.py').write_text(TOY+'\n_original=plant_cost\ndef plant_cost(rec):\n    if rec.get("catalyst", "").startswith("In2O3 [Figure 1a"):\n        raise ValueError("deliberate test failure")\n    return _original(rec)\n',encoding='utf-8')
    with contextlib.redirect_stdout(io.StringIO()):
        badout=be.evaluate('meoh',[bad],root/'negative_evaluation')
    bb=badout['builds'][str(bad)]
    assert bb['cost_failures'] and bb['hand_comparison']['fixed_conversion']['compared_groups']<63
    assert bb['ranking']['groups']<63
    invalid=f.copy();invalid.loc[invalid.index[0],'X']=0
    _,invalid_loader=be.load_records('meoh',invalid)
    assert invalid_loader['rejected']==1 and invalid_loader['converted']==len(f)-1
    assert invalid_loader['exclusions'][0]['reason']=='contract field outside physical range'
    # Cross-build common set, median reference selection and numerical rules.
    multiruns=[toy]
    for i,scale in [(2,1.05),(3,1.1)]:
        run=root/f'toy_{i}';run.mkdir()
        suffix=f'\n_original=plant_cost\ndef plant_cost(rec):\n    out=_original(rec)\n    out["parts"]={{k:v*{scale} for k,v in out["parts"].items()}}\n    out["cost_usd_per_t"]*= {scale}\n    return out\n'
        (run/'model.py').write_text(TOY+suffix,encoding='utf-8');multiruns.append(run)
    with contextlib.redirect_stdout(io.StringIO()):
        multi=be.evaluate('meoh',multiruns,root/'multi_evaluation')
    assert multi['primary_build_median_reference']==str(multiruns[1])
    assert multi['agreement']['quantitative_consistency']
    assert len(multi['agreement']['pairwise_spearman'])==3
    assert all(v>.999999 for v in multi['agreement']['pairwise_spearman'].values())
    outputs['cross_build_checks']={'common_records':multi['agreement']['common_successful_records'],
                                  'pairwise_spearman':list(multi['agreement']['pairwise_spearman'].values()),
                                  'reference_spread':multi['agreement']['reference_spread'],'median_build':'toy_2'}
    # Empty targets: exercise real existing CH4 builds, never overwrite their files.
    empty=json.loads((HERE/'holdout/ch4.json').read_text(encoding='utf-8'))
    empty['targets']={};empty['pass_rule']={'min_within':0,'rule':'offline empty-target test'}
    hp=root/'empty_ch4.json';hp.write_text(json.dumps(empty),encoding='utf-8')
    runs=[Path(f'D:/agent_runs/ch4_b{i}') for i in [1,2,3]]
    assert all((p/'model.py').exists() for p in runs),'existing CH4 builds required'
    with contextlib.redirect_stdout(io.StringIO()):
        result=eb.main('ch4',runs,holdout_path=hp,output_dir=root/'ch4_evaluation')
        audits=[ah.audit(run,'ch4',holdout_path=hp,output_dir=root/f'audit_{run.name}') for run in runs]
    assert all(b['tea_verdict'] is None and b['tea_pass'] is None and b['tea_n']==0 for b in result['builds'].values())
    outputs['empty_targets']={'builds':len(runs),'verdicts':[b['tea_verdict'] for b in result['builds'].values()],
                              'audits_completed':len(audits),'leak_flags':[a['leak'] for a in audits]}
    # Hidden atomic calculation: seven-step positive flux, site closure, no
    # loss of the weak-binding branch to -300 from numerical cancellation.
    hc=be.module(be.HARNESS/'harness_core.py','validate_hidden_hc')
    src=hc.parse_activity_workbook(next(be.HARNESS.rglob('*.xlsx')))
    ctx=hc.KineticContext(src['fits'],src['median_freqs'],src['gasrec'],'gillespie_beattie','ideal')
    import math
    for t,peak in [(850,.008),(673,-.377)]:
        c=ctx.condition(t,.0025,.0075,.99)
        grid=[peak-.03,peak,peak+.03,3.4]
        full=eb.full_harness_decomposition(c,grid)
        assert full['argmax_D']==peak
        for row in full['curve']:
            assert abs(sum(row['coverages'].values())-1)<1e-12
            assert row['TOF_extent_per_site_s']>0 and row['log_flux_residual']<1e-7
            assert abs(row['log10_TOF']-eb.qe_reverse_logtof(c,row['D']))<1e-5
    # Forward synthesis gas must never be mistaken for positive decomposition.
    try:
        eb.full_harness_decomposition(ctx.condition(673,24.5,74.25,1.),[0.])
    except ValueError as exc:
        assert 'positive net decomposition' in str(exc)
    else:
        raise AssertionError('synthesis gas accepted as decomposition')
    outputs['hidden_atomic_checks']='positive flux, site closure, local peaks and stable weak-binding QE/full curves passed at 850 and 673 K'
    outputs['output_dir']=str(root)
    (root/'validation_summary.json').write_text(json.dumps(outputs,indent=2),encoding='utf-8')
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':
    main()
