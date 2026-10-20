"""Aggregate computed evidence, report feasibility separately, and render the numbers-first handoff."""
import csv,json,math,time,hashlib
import keestra_common as Q
Q.tee('summarize');t0=time.time();Q.gate()
def load(name):return json.loads((Q.HERE/name).read_text(encoding='utf-8'))
def rows(name):return list(csv.DictReader((Q.HERE/name).open(encoding='utf-8')))
def finite(x):return math.isfinite(float(x))
def f(x):
    if x is None:return 'none in scanned range'
    try:
        n=float(str(x).replace('−','-'))
        if math.isnan(n):return 'undefined: neither catalyst feasible'
        if n==math.inf:return 'Ru infeasible'
        if n==-math.inf:return 'Fe infeasible'
        if 0<abs(n)<1e-5:return f'{n:.6g}'
        return f'{n:.6f}'
    except (ValueError,TypeError):return str(x)
summ={}
for tag in ('perturbation','perturbation_historical_magnitudes'):
    rr=rows(tag+'_results.csv');ss=load(tag+'_summary.json')
    feasibility={}
    for comp in sorted({r['comparison'] for r in rr}):
        feasibility[comp]={}
        for kind in ('single','corner'):
            for mag in ('typical','max','max_plant_sizing'):
                sub=[r for r in rr if r['comparison']==comp and r['kind']==kind and r['magnitude']==mag]
                if not sub:continue
                paired=[r for r in sub if r['Fe_cost']!='infeasible' and r['Ru_cost']!='infeasible']
                vals=[float(r['gap']) for r in paired]
                feasibility[comp][kind+' '+mag]=dict(n=len(sub),both_feasible=len(paired),Fe_only=sum(r['Fe_cost']!='infeasible' and r['Ru_cost']=='infeasible' for r in sub),Ru_only=sum(r['Fe_cost']=='infeasible' and r['Ru_cost']!='infeasible' for r in sub),neither=sum(r['Fe_cost']=='infeasible' and r['Ru_cost']=='infeasible' for r in sub),finite_min=min(vals) if vals else None,finite_max=max(vals) if vals else None,finite_Ru_ahead=sum(v<0 for v in vals))
    ss['feasibility']=feasibility;summ[tag]=ss
    Q.dump(tag+'_feasibility.json',feasibility,10)
B=load('table_b_summary.json');Fin=load('financing_summary.json');PR=load('pr_loop_results.json');ledger=load('claim_ledger_summary.json')
metrics=rows('model_upgrade_metrics.csv');curves=rows('financing_curves.csv');docs=rows('documented_rates_measured.csv')
assert len(curves)==241 and all(abs(float(r['financing_rate'])-i*.0005)<1e-12 for i,r in enumerate(curves))
for name,key in [('benchmark','RuC_minus_Fe'),('KAAP','KAAP_RuC_minus_Fe')]:
    a=Q.canonical_anchors()
    Q.check('curve zero',float(curves[0][name+'_RuC_minus_Fe']),a[key+'_0'])
    Q.check('curve 12%',float(curves[-1][name+'_RuC_minus_Fe']),a[key+'_12'])
for r in docs:
    if r['rate_pct'] and float(r['rate_pct'])==12:assert abs(float(r['gap_USD_t'])-float(r['owned_gap_USD_t']))<1e-9
assert len([r for r in metrics if r['table']=='B'])==20
replacement=[]
oldfront=json.loads((Q.AN/'nh3_frontier_provenance_2026_10_13/nh3_1_2/frontier_swap.json').read_text())['reproduced_headline']
for quantity,old,new in [('Fe benchmark optimum',oldfront['Fe']['cost'],Q.canonical_anchors()['Fe_benchmark']),('bulk Ru benchmark optimum',oldfront['Ru_benchmark']['cost'],Q.canonical_anchors()['Ru_bulk_benchmark']),('supported benchmark at 0%',oldfront['RuC_minus_Fe']['cashflow 0% r 0.9555']['global_'],summ['perturbation']['comparisons']['benchmark supported 0']['baseline']),('supported KAAP at 0%',oldfront['RuC_minus_Fe']['cashflow 0% r 0.9555']['KAAP'],summ['perturbation']['comparisons']['KAAP supported 0']['baseline']),('supported KAAP at 12%',oldfront['RuC_minus_Fe']['cashflow 12% r 0.9555']['KAAP'],summ['perturbation']['comparisons']['KAAP supported 0.12']['baseline'])]:
    replacement.append(dict(part='A',quantity=quantity,old=old,new=new,unit='USD/t',source='perturbation_summary.json / canonical_anchor_checks.json'))
for qty,old,new in [('Table B pass count',5,B['B_pass']),('registered 64-item comparison pass count',32,B['n_pass'])]:
    replacement.append(dict(part='B',quantity=qty,old=old,new=new,unit='items',source='table_b_summary.json'))
oldstats=list(csv.DictReader((Q.AN/'nh3_benchmark_error_table_2026_10_19/error_summary.csv').open(encoding='utf-8')))
newstats=rows('error_summary.csv');nsg={r['group']:r for r in newstats}
for old in oldstats:
    if old['level']!='quantity group':continue
    new=nsg[old['group']]
    for key in ('typical_abs_dev_pct','max_abs_dev_pct','typical_abs_dev_C','max_abs_dev_C'):
        if old[key] and old[key]!=new[key]:replacement.append(dict(part='B',quantity=old['group']+'; '+key,old=old[key],new=new[key],unit='C' if key.endswith('_C') else '%',source='error_summary.csv:'+old['group']))
for r in metrics:
    if r['table']=='B' or (r['table'] in ('A','C') and r['status']=='rescored' and r['old_DysonSimon_model']!=r['model']):
        replacement.append(dict(part='B',quantity=r['metric_id']+' '+r['quantity'],old=r['old_DysonSimon_model'],new=r['model'],unit=next((x['unit'] for x in csv.DictReader((Q.AN/'validation_nh3_plant_2026_10_13/benchmark_metrics.csv').open(encoding='utf-8')) if x['metric_id']==r['metric_id']),''),source='model_upgrade_metrics.csv:'+r['metric_id']))
p=summ['perturbation']['comparisons']['benchmark supported 0.12'];bulk=summ['perturbation']['comparisons']['bulk benchmark']
oldpert=list(csv.DictReader((Q.AN/'nh3_benchmark_error_table_2026_10_19/perturbation_results.csv').open(encoding='utf-8')))
oldbulk=min(float(r['gap_Ru_minus_Fe']) for r in oldpert if r['kind']=='single' and r['comparison']=='measured benchmark Ru - Fe (unconstrained)')
for qty,old,new,unit in [('supported baseline at 12%',1.452025,p['baseline'],'USD/t'),('typical single shift lower',-1.55,p['magnitudes']['typical']['single_shift_min'],'USD/t'),('typical single shift upper',3.01,p['magnitudes']['typical']['single_shift_max'],'USD/t'),('joint Ru-favouring typical shift',-2.04,p['magnitudes']['typical']['joint_Ru_favouring_shift'],'USD/t'),('single cases Ru ahead at 12%',4,p['n_single_Ru_ahead'],'cases'),('bulk smallest single margin',oldbulk,bulk['min_single_margin'],'USD/t'),('bulk smallest combination margin',.53,bulk['min_combination_margin'],'USD/t')]:
    replacement.append(dict(part='A',quantity=qty,old=old,new=new,unit=unit,source='perturbation_summary.json'))
# All numeric measured columns of SI Table 4b, not only the headline summaries.
ledger_rows=rows('nh3_claim_ledger.csv')
for r in ledger_rows:
    if r['doc']=='docs/SI_TABLES.md' and r['section'].startswith('Supplementary Table 4b') and r['status']=='REPLACE':
        replacement.append(dict(part='A',quantity=r['source_key'],old=r['value'],new=r['replacement_value'],unit='USD/t',source=r['source_file']+':'+r['source_key']))
old_up=json.loads((Q.AN/'nh3_loop_reconciliation_2026_10_14/outputs/upstream_93_94.json').read_text())['u93']['selected']
c=PR['comparisons']['425C_220bar_fixed_T3_pair']
replacement.append(dict(part='C',quantity='component recycle closure residual (fixed 220-bar point)',old='below 1e-9 (SI claim)',new=max(d['component_residual_rel_fresh'] for d in c['closure'].values()),unit='relative to fresh feed',source='pr_loop_results.json'))
for qty,old,new in [('PR Fe at 425 C / 220 bar',old_up['Fe']['decision_relevant_cost_USD_t'],c['PR']['Fe']['total_USD_t']),('PR Ru/C at 425 C / 220 bar',old_up['Ru']['decision_relevant_cost_USD_t'],c['PR']['Ru']['total_USD_t']),('PR Ru/C minus Fe',2.24,c['PR_gap']),('canonical common-point difference (SI quote)',2.36,c['canonical_gap']),('reactor saving',3.01,-c['reactor_delta']),('inventory penalty',5.25,c['inventory_delta']),('PR financing break-even %/y',7.,100*c['PR_break_even']),('canonical financing break-even %/y',7.2,100*c['canonical_break_even'])]:
    replacement.append(dict(part='C',quantity=qty,old=old,new=new,unit='%/y' if 'break-even' in qty else 'USD/t',source='pr_loop_results.json'))
with (Q.HERE/'replaced_numbers.csv').open('w',newline='',encoding='utf-8') as out:
    w=csv.DictWriter(out,fieldnames=list(replacement[0]));w.writeheader();w.writerows(replacement)
summary=dict(model='Keestra 2025 Model 3; KM1R-1964 b_cat=0.350, source Kf; Rossetti Ru/C',anchors=load('canonical_anchor_checks.json'),A=summ,B=B,C=PR,D=Fin,E=ledger,verification=dict(financing_rows=241,lease_at_12_equals_owned_at_12=True,all_B_items=20),seconds=time.time()-t0)
summary['environment']=dict(python_executable=Q.sys.executable,python_version=Q.sys.version,numpy=Q.np.__version__,scipy=__import__('scipy').__version__,NH3_MODEL='1.2')
Q.dump('summary.json',summary,12)
text=['# Keestra KM1R-1964 NH3 consolidation','',
'All costs are USD/t NH3; gaps are Ru/C minus Fe. Manuscript and frozen evidence were read only.','',
'| Part | Quantity | Old Dyson–Simon | Keestra | Unit |','|---|---|---:|---:|---|']
for part in ('A','B','C'):
    for r in replacement:
        if r['part']==part:text.append(f"| {part} | {r['quantity']} | {f(r['old'])} | {f(r['new'])} | {r['unit']} |")
text+=['',f"Table B: **{B['B_pass']}/20**. Registered upgrade total: **{B['n_pass']}/64** (old 32/64). C08 and C10 are historical registered campaign diagnostics carried unchanged, not new Keestra predictions; see limitations below.",'','| Financing break-even | %/year |','|---|---:|']
for key,val in Fin['breakevens'].items():text.append(f'| {key} | {f(None if val is None else 100*val)} |')
text+=['',f"Claim ledger: **{ledger['counts']['REPLACE']} REPLACE**, **{ledger['counts']['CHECK']} CHECK**, {ledger['counts']['OK']} OK ({ledger['rows']} numeric occurrences). CHECK rows are review items, not validated claims.",'',
'## Perturbation results and feasibility','',
'The primary perturbation uses the upgraded industrial-error table. The `historical_magnitudes` run holds the old perturbation sizes fixed and isolates the law/range change. Both use exactly five components, both directions, Fe-only/all-catalyst amount changes, 28 singles and 128 corners (64 per magnitude), plus baseline; the descriptor branch is not rerun.','',
'A ±infinity gap denotes only one catalyst feasible. NaN denotes neither feasible. These are feasibility outcomes, not finite economic margins. `*_feasibility.json` separates both-feasible margins and counts from these outcomes.','',
'| Loop/convention | Baseline | Typical single shifts | Max single shifts | Typical joint shift toward Ru | Ru ahead / 28 singles |','|---|---:|---|---|---:|---:|']
for key,d in summ['perturbation']['comparisons'].items():
    ty,ma=d['magnitudes']['typical'],d['magnitudes']['max']
    text.append(f"| {key} | {f(d['baseline'])} | {f(ty['single_shift_min'])} to {f(ty['single_shift_max'])} | {f(ma['single_shift_min'])} to {f(ma['single_shift_max'])} | {f(ty['joint_Ru_favouring_shift'])} | {d['n_single_Ru_ahead']} |")
text+=['','## Independent PR-loop check','',
'| State | PR Fe | PR Ru/C | PR gap | Canonical gap | PR break-even %/y | Canonical break-even %/y |','|---|---:|---:|---:|---:|---:|---:|']
for key,d in PR['comparisons'].items():text.append(f"| {key} | {f(d['PR']['Fe']['total_USD_t'])} | {f(d['PR']['Ru']['total_USD_t'])} | {f(d['PR_gap'])} | {f(d['canonical_gap'])} | {f(None if d['PR_break_even'] is None else 100*d['PR_break_even'])} | {f(None if d['canonical_break_even'] is None else 100*d['canonical_break_even'])} |")
text+=['',
'At 220 bar Ru/C extrapolates its fitted pressure range. The fixed original Fe operating point needs 133.202 m3, above the 90 m3 cap, so it is a fixed-state consistency calculation, not an eligible optimum. Its financing root is for those fixed operating points. At 90 bar the PR grid searches 400/425/445/450 C, all conversions and purge fractions of the committed cold grid at -20 C, and reselects optima with financing. The canonical comparison and root hold the 12%-selected PR temperature/pressure/separator points fixed. Cold states selected for reporting were recomputed live; inverse-to-forward bed checks and recycle closure residuals are in `pr_loop_results.json`.','',
'## Scope, provenance and limits','',
'- B01–B20 retain the registered cases, tolerances and optimization routines (three DE seeds for cost-optimal converter cases). No B design exceeds 324 bar.','- A19, A21, A23, A25, A27 and A28 depend on measured Fe bed sizing; those were recomputed. Other A state/flow/thermodynamic values are independent of the Fe law. E and V are unchanged. C01–C07 and C11–C12 are recomputed from the in-range optima; C09 uses the Keestra 90-bar library.','- C08 (all historical staging groups) and C10 (multi-pressure staging correlation) are frozen campaign-level diagnostics. The available Keestra staged library covers 90 bar only. Their registered scores are explicitly carried in the 64-item comparison column; a fully Keestra-only 64-row verdict requires a new multi-pressure staging campaign. No Keestra-only claim is made for those two rows.','- The committed staged continuation library contains only FFF/FFR/FRR/RRR. RFF/RRF curves were added by local continuation at 0–12% in 0.5 percentage-point steps, initialized from all three committed global arrangement optima; their lower envelopes are evaluated at the requested 0.05 percentage-point grid. These are library-envelope estimates (upper bounds on continuously optimized costs), not fresh global optima at every rate. The four existing patterns and their window extraction are unchanged.','- Owned-metal: purchases at years 0, 10, 20; recovery at 10, 20, 25; all discounted at the metal rate. Supplier lease: no principal purchase or sale, unsecured/no deposit, annual rent and loss settlement, all discounted at the fixed 12% plant rate. Documented Pt/Pd lease rates are analogies, not published Ru quotes.','- Source `results.json` stores financing rates to six decimals. The gate asserts 1e-6 relative after rounding computed anchors to that source precision and also checks unrounded values against the rounding interval. An unrounded 1e-6 relative test of those rounded roots is not numerically supportable; raw relative errors are exposed in `canonical_anchor_checks.json`.','- The ledger includes the actual Supplementary Table 4 text in `docs/SI_TABLES.md`, linked by the SI document. Citations, figure cross-reference numbers and chemical subscripts are excluded. Numeric ranges produce endpoint rows; duplicate occurrences remain separate. CHECK means a unique semantically appropriate result key was not confirmed, including stale mixed-branch benchmark statements that need editorial separation.','',
'## Rerun','',
'Run in `D:\\论文-AI4S\\wt-keestra20` with PowerShell. All scripts first reassert the canonical anchors and tee stdout into their corresponding `*_stdout.txt`. One Python process per command; the recorded runs used at most four concurrent Python processes and no multiprocessing pool.','',
'```powershell',"$env:NH3_MODEL='1.2'","$env:PYTHONDONTWRITEBYTECODE='1'","$py='D:/Research/CatalystForge/.venv/Scripts/python.exe'","$out='analysis/nh3_keestra_consolidation_2026_10_20'",'& $py -X utf8 "$out/table_b.py"','& $py -X utf8 "$out/perturbation.py"','& $py -X utf8 "$out/perturbation.py" --historical-magnitudes','& $py -X utf8 "$out/pr_loop_check.py"','& $py -X utf8 "$out/financing.py"','& $py -X utf8 "$out/claim_ledger.py"','& $py -X utf8 "$out/summarize.py"','```','',
'`table_b.py --resume` reuses completed checkpoint cases and regenerates state-dependent rows and scores. `financing.py` reuses its generated Ru-first continuation file if present; remove only that file to rebuild that extension. Source paths and row keys are in the CSVs.','',
'| Computation | Seconds |','|---|---:|']
for key,d in [('Table B/C/state upgrade (resume scoring)',B),('Perturbation upgraded errors',summ['perturbation']),('Perturbation original errors',summ['perturbation_historical_magnitudes']),('PR comparison',PR),('Financing',Fin),('Claim ledger',ledger)]:text.append(f"| {key} | {f(d.get('seconds'))} |")
text.append(f"| Table B retained converter computation | {f(B.get('converter_compute_seconds'))} |")
(Q.HERE/'README.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
# Only input files actually used as registered data/implementations are hashed;
# this is a reproducibility manifest, not an alteration of upstream provenance.
paths=set()
for folder in (Q.INRANGE,Q.AN/'validation_nh3_plant_2026_10_13',Q.AN/'nh3_benchmark_error_table_2026_10_19',Q.AN/'nh3_loop_reconciliation_2026_10_14',Q.STAGED):
    paths.update(p for p in folder.glob('*') if p.is_file() and p.suffix in ('.py','.json','.csv','.yaml','.md'))
paths.update(Q.REPO/p for p in ('docs/MANUSCRIPT_MAIN_TEXT.md','docs/SUPPLEMENTARY_INFORMATION.md','docs/MAIN_FIGURE_CAPTIONS.md','docs/SI_TABLES.md'))
Q.dump('input_sha256.json',{p.relative_to(Q.REPO).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},12)
print('summary and README written; validation passed',B,Fin['breakevens'],ledger['counts'])
