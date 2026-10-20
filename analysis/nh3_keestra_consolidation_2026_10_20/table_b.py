"""Read-only model upgrade of registered industrial metrics; one worker, same optimizers/rules."""
import time, sys, json, csv
import keestra_common as Q
Q.tee('table_b')
t0=time.time()
FR, S, h, st, model, mf, mr, kaap, anchors=Q.gate()
sys.path.insert(0,str(Q.AN/'validation_nh3_plant_2026_10_13'))
import importlib.util
spec=importlib.util.spec_from_file_location('benchmark_model',Q.AN/'validation_nh3_plant_2026_10_13/nh3_model.py')
bm=importlib.util.module_from_spec(spec);spec.loader.exec_module(bm)
sys.modules['nh3_model']=bm
import run_benchmark as R
sys.path.insert(0,str(Q.AN/'nh3_benchmark_error_table_2026_10_19'))
import run_error_table as E
Q.converter_default_fe_keestra()
cases={r['case_id']:r for r in R.rows('benchmark_cases.csv')}
old=json.loads((R.HERE/'nh3_1_2/results_cases.json').read_text())['model']
out=dict(old)
if '--resume' in sys.argv and (Q.HERE/'table_b_cases_checkpoint.json').exists():
    out=json.loads((Q.HERE/'table_b_cases_checkpoint.json').read_text())
S.rate_fe_m3=Q.rate_fe_m3
for k,c in cases.items():
    if c['level']=='state': out[k]=R.state_values(h,c)
needed={r['case_id'] for r in R.rows('benchmark_metrics.csv') if r['table']=='B'}
needed.update(('TOP140_MINVOL','TOP220_MINVOL'))
for k,c in cases.items():
    if k not in needed: continue
    if '--resume' in sys.argv and k in out and out[k]!=old.get(k):
        print('resumed completed case',k,flush=True);continue
    level=c['level']
    if level in ('converter_forward','converter_inverse'):
        f=R.CS.forward if level=='converter_forward' else R.CS.inverse
        beds=f(float(c['P_bar']),float(c['inlet_Nm3_h']),float(c['yNH3']),float(c['inerts']),json.loads(c['beds']),yN2=float(c['yN2']),yH2=float(c['yH2']))
        d=dict(beds=beds,outlet_NH3_molpct=beds[-1]['y_NH3_out_molpct'])
        for i,b in enumerate(beds,1): d[f'bed{i}_T_out_C']=b['T_out_C']
        if level=='converter_inverse': d['V_total_m3']=sum(b['V_model_m3'] for b in beds)
    elif level=='converter_design':
        d=R.design_job(dict(case_id=k,P_bar=float(c['P_bar']),Tsep_C=float(c['Tsep_C']),inerts=float(c['inerts']),pattern=c['pattern']))
    elif level=='converter_min_volume':
        d=R.minvol_job(dict(case_id=k,P_bar=float(c['P_bar']),inlet_Nm3_h=float(c['inlet_Nm3_h']),yNH3=float(c['yNH3']),y_out=float(c['y_out']),inerts=float(c['inerts']),n_beds=c['n_beds']))
    else: continue
    out[k]=d
    Q.dump('table_b_cases_checkpoint.json',out,10)
    print(k,level,d, 'elapsed_s',time.time()-t0,flush=True)
out['TOP220_MINVOL/TOP140_MINVOL']=dict(volume_ratio_220_140=out['TOP220_MINVOL']['V_total_m3']/out['TOP140_MINVOL']['V_total_m3'])
# C01-C07, C11-C12 use measured kinetics too. Recompute from the in-range model, not descriptor anchors.
a=FR.pair(model,model.fe_bench(),model.rub(),mf,mr)
b0=FR.pair(model,model.fe_cf(0),model.ruc_cf(0),mf,mr)
b12=FR.pair(model,model.fe_cf(.12),model.ruc_cf(.12),mf,mr)
measured={'Fe':a['Fe'],'Ru_C_supported':{}}
for key,b in [('cashflow 0% r 0.9555',b0),('cashflow 12% r 0.9555',b12)]:
    measured['Ru_C_supported'][key]=dict(Ru_C_global=b['Ru'],Ru_minus_Fe_global=b['gap'])
out.update(R.optimum_values(h,measured))
# C08-C10 refer to a multi-pressure staged campaign. Only the 90-bar Keestra
# library exists. C09 is recomputed; C08/C10 retain explicitly labelled historical
# scores and are excluded from the 62-item Keestra-evaluable subtotal.
import boundary as B
L=B.load_library(Q.INRANGE/'staged_KM1R_1964_design_library.csv')
dd=B.decide(L,(90.,-20.),53852.5,.9555,.12)
out['STAGED_90BAR']={'Ru_in_optimum_at_12pct':dd['best']!='FFF'}
windows={r['window_id']:dict(low=float(r['window_low']),high=float(r['window_high'])) for r in R.rows('industrial_windows.csv')}
et=E.build_error_table(); er={r['metric_id']:r for r in et}
original={r['metric_id']:r for r in R.rows('nh3_1_2/results_metrics.csv')}
rows=[]
for m in R.rows('benchmark_metrics.csv'):
    mid=m['metric_id']; val=out[m['case_id']][m['quantity']]
    pending=False
    historical=mid in ('C08','C10')
    ok,dev=R.judge(m['rule'],val,R.fnum(m['industrial_value']),R.fnum(m['industrial_low']),R.fnum(m['industrial_high']),windows)
    d=E.deviation(m,str(val),{k:(v['low'],v['high']) for k,v in windows.items()})
    if m['table'] in ('A','B','C'):
        er[mid].update(model=val,pass_='CHECK' if pending else ('pass' if ok else 'FAIL'),signed_deviation=E._r(d['signed_dev']),abs_deviation=E._r(d['abs_dev']),log_model_over_ref=E._r(d['log_ratio'],4),deviation_unit=d['dev_unit'])
    pressure=cases.get(m['case_id'],{}).get('P_bar','')
    rows.append(dict(metric_id=mid,table=m['table'],case_id=m['case_id'],quantity=m['quantity'],old_DysonSimon_model=original[mid]['model'],model='' if pending else val,industrial=er[mid]['industrial'],signed_deviation='' if pending else d['signed_dev'],deviation_unit=d['dev_unit'],rule=m['rule'],pass_='CHECK' if pending else ('pass' if ok else 'FAIL'),old_pass=original[mid]['pass_'],Fe_pressure_outside_fit=bool(pressure and float(pressure)>324),status='historical registered campaign diagnostic carried unchanged; NOT a new Keestra prediction' if historical else 'rescored' if m['table'] in ('A','B','C') else 'unchanged; process/descriptor/VLE'))
E.write_csv(Q.HERE/'model_upgrade_metrics.csv',rows)
E.write_csv(Q.HERE/'error_table.csv',et)
E.write_csv(Q.HERE/'error_summary.csv',E.build_summary(et))
Q.dump('table_b_cases.json',out,10)
Q.dump('table_b_cases_checkpoint.json',out,10)
def changed(r):
    try:return abs(float(r['model'])-float(r['old_DysonSimon_model']))>5.1e-7
    except (ValueError,TypeError):return str(r['model']).lower()!=str(r['old_DysonSimon_model']).lower()
summary=dict(n_pass=sum(r['pass_']=='pass' for r in rows),n_check=sum(r['pass_']=='CHECK' for r in rows),n_metrics=64,B_pass=sum(r['pass_']=='pass' and r['table']=='B' for r in rows),changed_rows=[r['metric_id'] for r in rows if changed(r)],historical_carried_rows=['C08','C10'],n_Keestra_evaluable=62,n_pass_Keestra_evaluable=sum(r['pass_']=='pass' and r['metric_id'] not in ('C08','C10') for r in rows),seconds=time.time()-t0,converter_compute_seconds=sum(float(out[k].get('seconds',0)) for k in needed if k in out))
Q.dump('table_b_summary.json',summary)
print(summary)
