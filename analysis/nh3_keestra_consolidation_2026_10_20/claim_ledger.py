"""Occurrence-level NH3 numeric ledger, with conservative CHECK for untraced claims.

Includes SI_TABLES.md Table 4 because the requested SI text links that separate
file. Citations, figure/table cross-reference labels and formula subscripts are
excluded. Ranges yield one row per endpoint; repeated occurrences remain rows.
"""
import csv,json,re,sys,time,math,bisect
from pathlib import Path
import keestra_common as Q
Q.tee('claim_ledger');t0=time.time();Q.gate()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
P=load(Q.HERE/'perturbation_summary.json')['comparisons']
PR=load(Q.HERE/'pr_loop_results.json')['comparisons']['425C_220bar_fixed_T3_pair']
upgrade=list(csv.DictReader((Q.HERE/'model_upgrade_metrics.csv').open(encoding='utf-8')))
newmet={r['metric_id']:r for r in upgrade}
oldstats=list(csv.DictReader((Q.AN/'nh3_benchmark_error_table_2026_10_19/error_summary.csv').open(encoding='utf-8')))
newstats=list(csv.DictReader((Q.HERE/'error_summary.csv').open(encoding='utf-8')))
stats={r['group']:r for r in newstats}
OUTREL=Q.HERE.relative_to(Q.REPO).as_posix()
num=re.compile(r'(?<![\w])[-−+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?(?:[⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+)?(?![\w])')
def numeric(s):
    try:
        s=str(s).replace(',','').replace('−','-')
        sup=re.search(r'[⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+$',s)
        if sup:s=s[:sup.start()]+'e'+sup.group().translate(str.maketrans('⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹','-+0123456789'))
        return float(s)
    except (ValueError,TypeError):return None
def tolerance(raw):
    s=raw.replace(',','').lstrip('+−-');return .501*10**(-len(s.split('.')[1])) if '.' in s and 'e' not in s.lower() else .501
def flatten(o,key='$'):
    if isinstance(o,dict):
        for k,v in o.items():yield from flatten(v,key+'.'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o):yield from flatten(v,key+f'[{i}]')
    elif isinstance(o,(float,int)) and not isinstance(o,bool):yield float(o),key
    elif isinstance(o,str) and numeric(o) is not None:yield numeric(o),key
registry={}
registry_values={}
def register(label,paths):
    records=[]
    for path in paths:
        if not path.is_file() or path.stat().st_size>6000000:continue
        rel=path.relative_to(Q.REPO).as_posix()
        try:
            if path.suffix=='.json':records.extend((v,rel,k) for v,k in flatten(load(path)))
            elif path.suffix=='.csv':
                for i,row in enumerate(csv.DictReader(path.open(encoding='utf-8')),2):
                    rid=row.get('metric_id') or row.get('case_id') or row.get('rate_id') or f'row {i}'
                    records.extend((numeric(v),rel,f'{rid}.{k}') for k,v in row.items() if numeric(v) is not None)
        except (ValueError,TypeError):continue
    records.sort(key=lambda r:r[0])
    registry[label]=records
    registry_values[label]=[r[0] for r in records]
register('measured',list(Q.INRANGE.glob('*.json')))
# Numeric coincidence with another catalyst activity factor or a GB-equilibrium
# sensitivity is not evidence for the KM1R-1964/source-Kf manuscript claim.
registry['measured']=[r for r in registry['measured'] if ('KM1R-1964, source Kf' in r[2] or '.ranges.' in r[2] or 'KM1R1964' in r[2])]
registry_values['measured']=[r[0] for r in registry['measured']]
descriptor_paths=[Q.REPO/'provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json',Q.REPO/'provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/manifest_resolved.yaml']
for folder in ('fe_bridge_backward_2026_09_29','nh3_mc_ru_actual_2026_10_06','nh3_actual_ru_params_2026_10_07','nh3_alloy_extension_2026_10_05','nh3_field_2026_10_06','nh3_ru_metal_financing_evidence_2026_10_12'):
    root=Q.AN/folder
    descriptor_paths.extend((root/'nh3_1_2').glob('*.json'));descriptor_paths.extend((root/'nh3_1_2').glob('*.csv'))
    descriptor_paths.extend(p for p in root.glob('*.json') if 'summary' in p.name)
register('descriptor',descriptor_paths)
register('benchmark',[Q.HERE/'model_upgrade_metrics.csv',Q.AN/'nh3_benchmark_error_table_2026_10_19/error_summary.csv'])
def trace(raw,context,label):
    value=numeric(raw);tol=tolerance(raw); options=[]
    words=set(re.findall(r'[a-z]{3,}',context.lower()))
    values=registry_values[label]
    for v,file,key in registry[label][bisect.bisect_left(values,value-tol):bisect.bisect_right(values,value+tol)]:
        if abs(v-value)>tol:continue
        kw=set(re.findall(r'[a-z]{3,}',key.lower()))
        score=len(words & kw)
        if 'cost' in context.lower() and ('cost' in key or 'USD' in key):score+=2
        if '%' in context and any(w in key.lower() for w in ('pct','percent','fraction','rate')):score+=1
        options.append((score,-abs(v-value),file,key))
    if not options:return '','','CHECK'
    best=max(options)
    # A literal numeric match is a locator, not proof of the scientific claim.
    # Large multidimensional records require a semantic key match to mark OK.
    # Candidate locators are not confirmations. Only explicit mappings below
    # receive OK; the rest are retained for review, even when a number matches.
    return best[2],best[3],'CHECK'
def unit(text,start,end):
    after=text[end:end+65];before=text[max(0,start-40):start]
    for token,u in [(r'^\s*%', '%'),(r'^\s*(?:°C|° C)', 'C'),(r'^\s*bar','bar'),(r'^\s*MPa','MPa'),(r'^\s*(?:kg m|kg/m)', 'kg/m3'),(r'^\s*m[³3]', 'm3'),(r'^\s*eV','eV'),(r'^\s*K\b','K'),(r'^\s*(?:years?|y\b|[-–]year)','year'),(r'^\s*(?:[-–]fold|fold|×)','fold')]:
        if re.search(token,after):return u
    if re.search(r'US dollars per tonne|USD/t',after):return 'USD/t'
    if re.search(r'US dollars per kilogram',after):return 'USD/kg'
    if 'financing' in before and '%' in after:return '%/y'
    return 'dimensionless/count (see quoted text)'
def quote(text,start,end):
    left=text[:start].split()[-8:];right=text[end:].split()[:8]
    return ' '.join(left+[text[start:end]]+right)[:500]
def sentence_for(text,m):
    boundaries=[0]+[x.end() for x in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])',text)]+[len(text)]
    return next(text[a:b] for a,b in zip(boundaries[:-1],boundaries[1:]) if a<=m.start()<b)
rows=[]
def add(doc,section,text,m,generation,source='',key='',status=None,replacement=''):
    raw=m.group();un=unit(text,m.start(),m.end())
    if not source:
        source,key,auto=trace(raw,text,'measured' if generation=='measured_Keestra_inrange' else 'descriptor')
        explicit=confirmed(raw,generation)
        if explicit:source,key,auto=explicit
    else:auto='OK'
    if generation=='none':
        source=doc;key=section+'; author-stated condition or literature citation';auto='OK'
    rows.append(dict(doc=doc,section=section,quoted_text=quote(text,m.start(),m.end()),value=raw,unit=un,kinetics_generation=generation,source_file=source,source_key=key,status=status or auto,replacement_value=replacement))
MEAS=load(Q.INRANGE/'results.json')['Fe_Keestra']['Keestra KM1R-1964, source Kf']
CANFILE='provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json'
CAN=load(Q.REPO/CANFILE)
def confirmed(raw,generation):
    """Explicit source contracts for canonical headline values, not a corpus-wide coincidence."""
    v=numeric(raw);tol=tolerance(raw)
    mappings=[]
    if generation=='measured_Keestra_inrange':
        file=Q.INRANGE.relative_to(Q.REPO).as_posix()+'/results.json';prefix='$.Fe_Keestra.Keestra KM1R-1964, source Kf.'
        for key in ('a','b_0','b_12','c_0_KAAP','c_12_KAAP'):
            for cat in ('Fe','Ru'):
                mappings.append((MEAS[key][cat]['cost'],prefix+key+'.'+cat+'.cost'))
            # Prose gives positive magnitudes for savings.
            mappings.append((abs(MEAS[key]['gap']),prefix+key+'.abs(gap)'))
        mappings.append((MEAS['parity'],prefix+'parity'))
        mappings.append((MEAS['bench_price_parity']['price_USD_kg'],prefix+'bench_price_parity.price_USD_kg'))
        mappings.append((100*(1-MEAS['bench_price_parity']['factor_vs_current']),prefix+'100*(1-bench_price_parity.factor_vs_current)'))
        for key in ('b_breakeven','c_breakeven_KAAP','b_breakeven_r90','c_breakeven_KAAP_r90'):
            mappings.append((100*MEAS[key]['rate'],prefix+key+'.rate * 100'))
        # Do not assign a rounded integer to a different cost/variant: precise
        # costs and rates below 100 are mapped, pressure/temperature inputs CHECK.
        hits=[(value,key) for value,key in mappings if abs(value-v)<=tol and ('.cost' in key or 'gap' in key or 'parity' in key or 'rate *' in key)]
        if len(hits)==1:return file,hits[0][1],'OK'
    elif generation=='descriptor_NH3-FINAL-1.2':
        mappings=[(CAN['deterministic']['metals'][cat]['feasible']['total_cost'],f'$.deterministic.metals.{cat}.feasible.total_cost') for cat in ('Fe','Ru','Os')]
        mappings +=[(CAN['deterministic']['raw_global_spearman'],'$.deterministic.raw_global_spearman')]
        mappings += [(value,'$.backward_reachability.'+key) for key,value in CAN['backward_reachability'].items() if isinstance(value,(int,float))]
        hits=[(value,key) for value,key in mappings if abs(value-v)<=tol and '.' in raw and v not in (0.,1.)]
        if len(hits)==1:return CANFILE,hits[0][1],'OK'
    return None
def generation(text,section):
    if any(s in text for s in ('independent loop model','Peng–Robinson loop','measured rate laws of Dyson')):return 'measured_DysonSimon'
    if text.startswith('| Measured') or 'Fused iron then costs' in text or 'Model 3 law of Keestra' in text or 'Model 3 rate law of Keestra' in text:return 'measured_Keestra_inrange'
    if 'three-bed converter at 9 MPa' in text or 'supported Ru/C catalyst with metal recovery is at cost parity' in text:return 'measured_Keestra_inrange'
    if any(s in text for s in ('industrial ammonia plants','plant benchmark compares','64 values from industrial','compared with 64 values')):return 'measured_DysonSimon'
    if section=='Abstract' and 'with measured rate laws' in text:return 'measured_Keestra_inrange'
    return 'descriptor_NH3-FINAL-1.2'
def stale_replacement(text,raw,pr=False):
    v=numeric(raw);b=P['benchmark supported 0.12'];c=P['bulk benchmark']
    if pr:
        if 'component residuals below' in text and abs(v)<1e-7:
            return max(d['component_residual_rel_fresh'] for d in PR['closure'].values()),OUTREL+'/pr_loop_results.json','comparisons.425C_220bar_fixed_T3_pair.closure.max(component_residual_rel_fresh)'
        mapping={47.245:(PR['PR']['Fe']['total_USD_t'],'PR.Fe.total_USD_t'),49.484:(PR['PR']['Ru']['total_USD_t'],'PR.Ru.total_USD_t'),2.24:(PR['PR_gap'],'PR_gap'),2.36:(PR['canonical_gap'],'canonical_gap'),3.01:(-PR['reactor_delta'],'reactor_delta (saving magnitude)'),5.25:(PR['inventory_delta'],'inventory_delta'),7.0:(100*PR['PR_break_even'],'PR_break_even * 100'),7.2:(100*PR['canonical_break_even'],'canonical_break_even * 100')}
        if v in mapping:return mapping[v][0],OUTREL+'/pr_loop_results.json','comparisons.425C_220bar_fixed_T3_pair.'+mapping[v][1]
    if any(s in text for s in ('Benchmark deviations of typical size','With the measured rate laws','Supported Ru/C with recovery and its inventory')):
        mapping={.53:(min(c['min_single_margin'],c['min_combination_margin']) if isinstance(c['min_combination_margin'],(int,float)) else c['min_combination_margin'],'bulk benchmark.min_combination_margin'),1.45:(b['baseline'],'benchmark supported 0.12.baseline'),-1.55:(b['magnitudes']['typical']['single_shift_min'],'benchmark supported 0.12.magnitudes.typical.single_shift_min'),-1.6:(b['magnitudes']['typical']['single_shift_min'],'benchmark supported 0.12.magnitudes.typical.single_shift_min'),3.01:(b['magnitudes']['typical']['single_shift_max'],'benchmark supported 0.12.magnitudes.typical.single_shift_max'),3.0:(b['magnitudes']['typical']['single_shift_max'],'benchmark supported 0.12.magnitudes.typical.single_shift_max'),-2.04:(b['magnitudes']['typical']['joint_Ru_favouring_shift'],'benchmark supported 0.12.magnitudes.typical.joint_Ru_favouring_shift')}
        if v in mapping:return mapping[v][0],OUTREL+'/perturbation_summary.json','comparisons.'+mapping[v][1]
    if v==32 and any(s in text for s in ('32 lie','32 of the 64','32 benchmark items')):
        count=sum(r['pass_']=='pass' for r in upgrade)
        return (64-count if '32 benchmark items' in text else count),OUTREL+'/table_b_summary.json','n_pass' if '32 benchmark items' not in text else '64 - n_pass'
    for val,group,stat in [(62.6,'bed volume, cost-optimal designs and Fe optimum','typical_abs_dev_pct'),(45.8,'outlet NH3, cost-optimal converter designs','typical_abs_dev_pct'),(17.9,'bed volume, plant conditions','typical_abs_dev_pct'),(34.4,'space velocity','typical_abs_dev_pct')]:
        if v==val:return stats[group][stat],OUTREL+'/error_summary.csv',group+'.'+stat
    return None
for doc in ('docs/MANUSCRIPT_MAIN_TEXT.md','docs/SUPPLEMENTARY_INFORMATION.md','docs/MAIN_FIGURE_CAPTIONS.md'):
    section='';major='';line_no=0
    for original in (Q.REPO/doc).read_text(encoding='utf-8').splitlines():
        line_no+=1
        if original.startswith('#'):
            section=original.lstrip('# ').strip()
            if original.startswith('## '):major=section
            continue
        if not original.strip():continue
        if doc.endswith('SUPPLEMENTARY_INFORMATION.md'):
            selected=any(section.startswith('Supplementary Note '+str(n)+' |') for n in (1,4,7,8))
        elif doc.endswith('MAIN_FIGURE_CAPTIONS.md'):selected=any(section.startswith('Figure '+str(n)+' |') for n in (1,4,5))
        else:
            selected=major in ('Abstract','Results','Discussion','Methods') and section not in ('Selectivity, recycle and purge reshape the methanol ranking','CO₂-to-methanol','Published methanol comparisons','Au/TiO₂ rank-preservation control','Adaptive Catalyst Screening Agent','A monotonic catalyst-to-process mapping preserves the ranking')
            if section in ('Published laboratory leaders are often not the plant-cost leaders','Abstract','Discussion','Multiscale decision analysis'):
                selected=selected and any(s in original for s in ('ammonia','NH₃','fused iron'))
        if not selected:continue
        if section=='Abstract':
            original=original[original.find('In ammonia synthesis'):]
            original=re.sub(r'in 26 of 63 methanol comparisons \(41%\), nor is','nor is',original)
        if section=='Discussion' and '41%' in original and '27%' in original:
            original=re.sub(r'in 41% of comparisons between catalysts, and','and',original)
        text=re.sub(r'\[[\d,– –-]+\]','',original)
        text=re.sub(r'\b(?:Fig(?:ure)?s?\.?|Supplementary (?:Note|Table)s?|Extended Data Fig\.?)\s*\d+[a-z]?(?:[–, ]+\d+[a-z]?)?','',text)
        gen=generation(text,section)
        for m in num.finditer(text):
            sentence=sentence_for(text,m)
            localgen=gen
            if section=='Abstract' and m.start()>text.find('An extraction agent')>0:localgen='descriptor_NH3-FINAL-1.2'
            cut=next((text.find(s) for s in ('With the measured rate laws of Dyson','We therefore replaced','For the two frontier catalysts','the Model 3 law of Keestra') if s in text),None)
            if cut is not None and m.start()<cut:localgen='descriptor_NH3-FINAL-1.2'
            if cut is not None and m.start()>=cut and 'Keestra' in text:localgen='measured_Keestra_inrange'
            if 'A recycle-boundary check' in text and m.start()>text.find('A recycle-boundary check'):localgen='descriptor_NH3-FINAL-1.2'
            if 'model was compared with 64' in text and m.start()<text.find('model was compared with 64'):localgen='descriptor_NH3-FINAL-1.2'
            if 'smallest margin' in sentence and not any(s in sentence for s in ('measured rate laws','Supported Ru/C')):localgen='descriptor_NH3-FINAL-1.2'
            if gen=='measured_DysonSimon' and any(s in text for s in ('model was compared with 64','plant benchmark compares','64 values from industrial')):
                if not any(s in sentence for s in ('tolerance','deviation','benchmark','converter','plant','power')):localgen='descriptor_NH3-FINAL-1.2'
            replacement=stale_replacement(sentence,m.group(),'independent loop model' in text)
            near=quote(text,m.start(),m.end())
            if localgen=='measured_DysonSimon' and numeric(m.group())==63 and 'bed volume' in near:
                replacement=(stats['bed volume, cost-optimal designs and Fe optimum']['typical_abs_dev_pct'],OUTREL+'/error_summary.csv','bed volume, cost-optimal designs and Fe optimum.typical_abs_dev_pct')
            if localgen=='measured_DysonSimon' and numeric(m.group()) in (50,58) and 'first bed' in sentence:
                vals=[float(newmet[mid]['signed_deviation']) for mid in ('B11','B14','B17')]
                replacement=(min(vals) if numeric(m.group())==50 else max(vals),OUTREL+'/model_upgrade_metrics.csv','min(B11,B14,B17).signed_deviation' if numeric(m.group())==50 else 'max(B11,B14,B17).signed_deviation')
            if localgen=='measured_DysonSimon' and numeric(m.group()) in (16,34) and 'typical deviations 16' in sentence:
                replacement=(16.4 if numeric(m.group())==16 else 29.8,OUTREL+'/error_summary.csv','converter flow and feed/make-up.typical_abs_dev_pct' if numeric(m.group())==16 else 'space velocity.typical_abs_dev_pct')
            if 'without a prescribed conversion' in text and numeric(m.group())==1500:
                add(doc,f'{section} (line {line_no})',text,m,'measured_DysonSimon',OUTREL+'/pr_loop_results.json','forward_check: fixed-feed bed integration verified; full forward-coupled recycle not rerun','CHECK','requires a full forward-coupled recycle solve')
            elif replacement:
                value,file,key=replacement
                add(doc,f'{section} (line {line_no})',text,m,'measured_DysonSimon',file,key,'REPLACE',value)
            elif localgen=='measured_Keestra_inrange' and 'Benchmark deviations of typical size' in sentence:
                add(doc,f'{section} (line {line_no})',text,m,'none')
            elif localgen=='measured_DysonSimon':
                # Conditions, count denominators and model-independent constants
                # in mixed paragraphs are traced separately, never assigned a made-up replacement.
                independent=numeric(m.group()) in (0,1,5,12,13,18,25,28,32,64,90,95.55,220,425,1500,16.4,62.9,72.6,39.8,42.3,77.4,42,63)
                add(doc,f'{section} (line {line_no})',text,m,'none' if independent else localgen,status=None if independent else 'CHECK')
            else:add(doc,f'{section} (line {line_no})',text,m,localgen)
# Table 4 is stored separately from the SI notes. Handle each numeric cell.
section='';oldpert=list(csv.DictReader((Q.AN/'nh3_benchmark_error_table_2026_10_19/perturbation_results.csv').open(encoding='utf-8')))
newpert=list(csv.DictReader((Q.HERE/'perturbation_results.csv').open(encoding='utf-8')))
for ln,line in enumerate((Q.REPO/'docs/SI_TABLES.md').read_text(encoding='utf-8').splitlines(),1):
    if line.startswith('### '):section=line[4:]
    if not section.startswith('Supplementary Table 4') or not line.strip():continue
    text=re.sub(r'`[^`]*`','',re.sub(r'\[[\d,– –-]+\]','',line))
    cells=[c.strip() for c in text.split('|')[1:-1]] if text.startswith('|') else []
    for m in num.finditer(text):
        cell=text[:m.start()].count('|')-1
        gen='none';file='';key='';status=None;rep=''
        if section.startswith('Supplementary Table 4c') and cells and cells[0] in newmet:
            mid=cells[0];r=newmet[mid]
            if cell in (3,6):
                gen='measured_DysonSimon' if r['status']=='rescored' else 'none'
                file=OUTREL+'/model_upgrade_metrics.csv';key=mid+('.model' if cell==3 else '.signed_deviation')
                rep=r['model'] if cell==3 else r['signed_deviation'];status='REPLACE' if gen=='measured_DysonSimon' else 'OK'
        elif section.startswith('Supplementary Table 4a') and cells and cells[0] in stats:
            r=stats[cells[0]]
            if cell in (2,3,4):
                field='n_pass' if cell==2 else ('typical_abs_dev_C' if '°C' in cells[cell] else 'typical_abs_dev_pct') if cell==3 else ('max_abs_dev_C' if '°C' in cells[cell] else 'max_abs_dev_pct')
                gen='measured_DysonSimon';file=OUTREL+'/error_summary.csv';key=cells[0]+'.'+field;rep=r[field];status='REPLACE'
        elif section.startswith('Supplementary Table 4b') and cells and cells[0]!='Perturbation' and cell>=4:
            gen='measured_DysonSimon';status='REPLACE';file=OUTREL+'/perturbation_results.csv'
            comparison=('bulk benchmark','benchmark supported 0','benchmark supported 0.12')[min(cell-4,2)]
            label=cells[0];magnitude='typical' if 'typical' in label else 'max_plant_sizing' if 'plant conditions' in label else 'max'
            direct=None
            if label=='baseline':direct=next(r for r in newpert if r['comparison']==comparison and r['kind']=='baseline')
            elif label.startswith('all five'):
                field='joint_Ru_favouring_gap' if 'towards Ru' in label else 'min_corner_gap'
                rep=P[comparison]['magnitudes'][magnitude][field]
                key='comparisons.'+comparison+'.magnitudes.'+magnitude+'.'+field
                file=OUTREL+'/perturbation_summary.json'
            else:
                component=next((c for phrase,c in [('separator vapour','SEP'),('approach to equilibrium','APP'),('compression power','COMP'),('catalyst amount','KIN'),('bed temperature','TBED')] if label.startswith(phrase)),None)
                if component:
                    sg=1 if label.endswith('+') else -1;mode='all' if '(all)' in label else 'Fe'
                    direct=next(r for r in newpert if r['comparison']==comparison and r['kind']=='single' and r['magnitude']==magnitude and r['kin_mode']==mode and json.loads(r['signs'])=={component:sg})
            if direct:
                rep=direct['gap'];key=comparison+'; '+direct['scenario']+'.gap'
            if direct or label.startswith('all five'):
                add('docs/SI_TABLES.md',f'{section} (line {ln})',text,m,gen,file,key,status,rep)
                continue
            # Pair by the unique rounded old value within the same comparison;
            # ambiguous rows are explicitly CHECK rather than silently guessed.
            oldlabel={'bulk benchmark':'measured benchmark Ru - Fe (unconstrained)','benchmark supported 0':'measured supported Ru/C - Fe (0 %/y)','benchmark supported 0.12':'measured supported Ru/C - Fe (12 %/y)'}[comparison]
            hits=[r for r in oldpert if r['comparison']==oldlabel and numeric(r['gap_Ru_minus_Fe']) is not None and abs(float(r['gap_Ru_minus_Fe'])-numeric(m.group()))<=tolerance(m.group())]
            matches=[]
            for r in hits:
                # Match design parameters, not the old optimum.
                for n in newpert:
                    if n['comparison']!=comparison or n['kind']!=r['kind'] or n['magnitude']!=r['magnitude']:continue
                    if r['kind']=='baseline':matches.append(n)
                    elif r['kind']=='single':
                        oldname=r['scenario'].split();newname=n['scenario'].split()
                        component=oldname[0].split('_')[0];sg=1 if oldname[1]=='+' else -1
                        if json.loads(n['signs'])=={component:sg} and (component!='KIN' or n['kin_mode']==('all' if 'all' in oldname[0] else 'Fe')):matches.append(n)
            vals={str(n['gap']) for n in matches}
            if len(vals)==1:rep=next(iter(vals));key=comparison+'; '+matches[0]['scenario']+'.gap'
            else:rep='CHECK: select exact scenario/joint envelope in perturbation_results.csv';key=comparison+'; '+cells[0];status='REPLACE'
        add('docs/SI_TABLES.md',f'{section} (line {ln})',text,m,gen,file,key,status,rep)
# Literal word-number in the stale measured paragraph.
si=(Q.REPO/'docs/SUPPLEMENTARY_INFORMATION.md').read_text(encoding='utf-8')
if 'four single cases put Ru/C ahead' in si:
    rows.append(dict(doc='docs/SUPPLEMENTARY_INFORMATION.md',section='Supplementary Note 7',quoted_text='four single cases put Ru/C ahead',value='four',unit='cases',kinetics_generation='measured_DysonSimon',source_file=OUTREL+'/perturbation_summary.json',source_key='comparisons.benchmark supported 0.12.n_single_Ru_ahead',status='REPLACE',replacement_value=P['benchmark supported 0.12']['n_single_Ru_ahead']))
with (Q.HERE/'nh3_claim_ledger.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert all(len(r['quoted_text'].split())<=20 for r in rows)
counts={k:sum(r['status']==k for r in rows) for k in ('OK','REPLACE','CHECK')}
Q.dump('claim_ledger_summary.json',dict(counts=counts,rows=len(rows),missing_sources=sum(not r['source_file'] for r in rows),seconds=time.time()-t0))
print('ledger',counts,'rows',len(rows),'seconds',time.time()-t0)
