"""Hidden evaluation of NH3/MeOH builds; NEVER import this module on the agent side.

Usage: cfpy agent/new_reactions/auto_agent/blind_eval.py nh3|meoh RUN [RUN ...]
Outputs are evaluation/<rxn>_blind.{json,md}, outside all build workspaces.

Conversion ledger (no refitting or re-extraction):
* MeOH uses the frozen pooled STY in g MeOH/g catalyst/h, numerically identical
  to kg/kg/h. Its documented group basis is preserved: printed STY, otherwise
  NL/g/h * y_CO2 * X * S / 22.414 NL/mol * 32.042 g/mol; volumetric GHSV h^-1
  first divides by 1000*rho, rho=1 g/cm3. The original inconsistency fallback
  and density assumptions are inherited, never silently recomputed.
  X and SMeOH already are fractions; T_C+273.15; P already bar.
  y_key=y_co2 (including the original inert correction), y_cofeed=y_co2*h2_co2.
* NH3 rate_umol_gcat_h * 1e-6 mol/umol * 17.03052 g/mol gives g/g/h=kg/kg/h.
  A missing catalyst-mass rate can only use a metal-mass rate times wt%/100.
  H2/N2 is read from the row, then the frozen group label (which records the
  field pipeline's feed-ratio filling). Dry binary feed: y_N2=1/(1+ratio).
  With outlet NH3 mole fraction y, inlet molar amount 1 and extent xi,
  y=2xi/(1-2xi), hence X_N2=y/[2*y_N2*(1+y)]. S=1 is the NH3-only product
  assumption of the hand mapping. y_out retains the original measured,
  rate/WHSV-derived or explicitly median-filled value and its provenance.
  MPa*10 -> bar; T_C+273.15. WHSV is NOT a second independent rate estimate.
* Components are [element, wt%], never mass fractions. NH3 uses the printed
  loading (fused Fe uses the frozen 71.51 wt% active fraction). MeOH only
  parses explicit elemental wt% labels; other recognizable catalytic metals
  have loading None. Support stoichiometry is not a measured metal loading.
  TOS is not a time to 10% loss: t_cycle_h=None for both systems.
* MeOH EUR costs use 1.053 USD/EUR (repo's EUR2022 conversion in
  analysis/meoh_plant_benchmark_2026_10_06/run_benchmark.py); no inflation.

MeOH scoring is catalyst-level using run_catalyst_level's identity aliases:
max STY and min cost independently over each catalyst's measured temperatures;
absolute 1e-12 laboratory tie tolerance. NH3 follows score.py pool / field
group_metrics: record-level, relative 1e-12 laboratory tie tolerance, sorting
by paper_rate before idxmin. Regret = cheapest lab leader / plant optimum-1;
the material-gap rule is strictly >0.05 among changed groups. The raised
MeOH convention is a second HIDDEN hand verdict, not a modification of AI
inputs: its frozen cost_f0.95 uses added catalyst and 0.95 X_eq.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from evaluate_builds import load_model

EUR_USD = 1.053
SEED = 20261006
ME = REPO / 'analysis/meoh_field_pooled_2026_10_15'
NH = REPO / 'analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen'
HARNESS = REPO / 'provenance/nh3_final_1_2/source_harness'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [clean(v) for v in x]
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    return x


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}


def rho(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if pd.notna(x) and pd.notna(y) and math.isfinite(x) and math.isfinite(y)]
    if len(pairs) < 2 or len(set(x for x, _ in pairs)) < 2 or len(set(y for _, y in pairs)) < 2:
        return None
    return float(spearmanr(*zip(*pairs)).statistic)


def group_verdicts(frame, rxn, cost):
    f = frame[np.isfinite(frame[cost]) & frame.lab.notna() & frame.group.notna()].copy()
    if rxn == 'meoh':
        f = f.groupby(['group', 'identity'], sort=True).agg(lab=('lab', 'max'), value=(cost, 'min'),
                                                         doi=('doi', 'first')).reset_index()
    else:
        f['value'] = f[cost]
    out = []
    for key, g in f.groupby('group', sort=True):
        if len(g) < 2:
            continue
        if rxn == 'nh3':
            g = g.sort_values('lab', ascending=False)
        best_lab = g.lab.max()
        leaders = g[g.lab >= best_lab - 1e-12] if rxn == 'meoh' else g[g.lab >= best_lab*(1-1e-12)]
        best = g.loc[g.value.idxmin()]
        changed = best.identity not in set(leaders.identity) if rxn == 'meoh' else best.name not in leaders.index
        gap = float(leaders.value.min()/best.value-1)
        out.append(dict(group=key, paper=g.doi.iloc[0], n=len(g), changed=bool(changed), gap=gap,
                        gt5pct=bool(changed and gap > .05), lab_leaders=leaders.identity.tolist(),
                        plant_leader=best.identity, plant_cost=float(best.value)))
    return out


def summary(groups):
    if not groups:
        return dict(groups=0, papers=0, changed=0, gt5pct=0, fraction=None, ci95=None,
                    bootstrap=dict(draws=2000, seed=SEED, unit='paper'))
    g = pd.DataFrame(groups)
    per = g.groupby('paper').changed.agg(['sum', 'count'])
    idx = np.random.default_rng(SEED).integers(0, len(per), (2000, len(per)))
    shares = per['sum'].to_numpy()[idx].sum(1)/per['count'].to_numpy()[idx].sum(1)
    return dict(groups=len(g), papers=len(per), changed=int(g.changed.sum()), gt5pct=int(g.gt5pct.sum()),
                fraction=float(g.changed.mean()), ci95=np.percentile(shares, [2.5, 97.5]).tolist(),
                bootstrap=dict(draws=2000, seed=SEED, unit='paper'))


def hand_tables(rxn):
    if rxn == 'meoh':
        sys.path.insert(0, str(REPO/'analysis/meoh_catalyst_level_2026_10_19'))
        import run_catalyst_level as rcl
        f = rcl.identities(pd.read_csv(ME/'pooled_candidates.csv'))
        f['lab'], f['identity'] = f.STY, f.cat_primary
        f['hand_cost'] = f[rcl.COST]*EUR_USD
        p = pd.read_csv(ME/'robustness/conversion_s6/s6_conversion_points.csv')
        p = p[p['mode'] == 'printed']
        keys = ['group', 'catalyst', 'T_C', 'STY']
        f = f.merge(p[keys+['cost_f0.95']], on=keys, validate='one_to_one')
        f['hand_raised_cost'] = f['cost_f0.95']*EUR_USD
        variants = {'fixed_conversion': group_verdicts(f, rxn, 'hand_cost'),
                    'raised_conversion': group_verdicts(f, rxn, 'hand_raised_cost')}
        assert [(summary(v)['changed'], len(v)) for v in variants.values()] == [(26, 63), (21, 63)], 'hand MeOH anchors changed'
    else:
        f = pd.read_csv(NH/'candidates_printed.csv')
        f['identity'], f['lab'], f['hand_cost'] = f.catalyst, f.paper_rate, f.cost_USD_t
        valid = f.group.notna() & f.hand_cost.notna() & f.lab.notna()
        valid &= f.duplicate_in_group.isna() | f.duplicate_in_group.eq(False)
        f['hand_eligible'] = valid
        variants = {'printed': group_verdicts(f[valid], rxn, 'hand_cost')}
        assert (summary(variants['printed'])['changed'], len(variants['printed'])) == (12, 44), 'hand NH3 anchor changed'
    if 'hand_eligible' not in f:
        f['hand_eligible'] = np.isfinite(f.hand_cost)
    f['record_id'] = [f'{rxn}:{i:04d}' for i in range(len(f))]
    return f, variants


METALS = {'Ru','Os','Fe','Rh','Ir','Co','Re','Mo','Ni','W','Pd','Pt','Cu','Ag','Au','In','Zn','Ga','Zr','Mn','Ce','Cr'}


def components(name):
    # Explicit labels only: never infer a loading from sample numbers or formula subscripts.
    found = {}
    for wt, el in re.findall(r'(\d+(?:\.\d+)?)\s*wt\s*%\s*([A-Z][a-z]?)', name):
        if el in METALS and 0 < float(wt) <= 100:
            found[el] = float(wt)
    for el in re.findall(r'[A-Z][a-z]?', name.split('[')[0]):
        if el in METALS:
            found.setdefault(el, None)
    return [[k, v] for k, v in sorted(found.items())]


def load_records(rxn, f):
    records, rejected, notes = {}, [], []
    for _, row in f.iterrows():
        r = row.to_dict()
        rid = r['record_id']
        try:
            t = float(r['T_C'])+273.15
            if rxn == 'meoh':
                rec = dict(T_K=t, P_bar=float(r['P_bar']), X=float(r['X']), S=float(r['SMeOH']),
                           r=float(r['STY']), y_key=float(r['y_co2']),
                           y_cofeed=float(r['y_co2'])*float(r['h2_co2']), components=components(r['catalyst']))
                notes.append(dict(record_id=rid, rate_basis=r['sty_basis'], missing_loadings=any(v is None for _, v in rec['components'])))
            else:
                ratio = r['H2_N2']
                ratio_source = 'H2_N2'
                if pd.isna(ratio):
                    hit = re.search(r'H2/N2\s+([\d.]+)', r['group'])
                    if not hit:
                        raise ValueError('missing feed ratio in row and frozen group')
                    ratio, ratio_source = float(hit[1]), 'frozen group label'
                yn = 1/(1+float(ratio))
                y = float(r['y_out'])
                wt = 71.51 if r['fused'] == True else r['metal_wt_pct']
                rate = r['rate_umol_gcat_h']
                if pd.isna(rate):
                    rate = r['rate_umol_gmetal_h']*wt/100
                rec = dict(T_K=t, P_bar=float(r['P_MPa'])*10, X=y/(2*yn*(1+y)), S=1.,
                           r=float(rate)*17.03052e-6, y_key=yn, y_cofeed=1-yn,
                           components=[[r['metal'], None if pd.isna(wt) else float(wt)]])
                notes.append(dict(record_id=rid, feed_ratio_source=ratio_source, outlet_source=r['y_source'],
                                  assumption='dry binary N2/H2 feed; NH3 only product'))
            rec.update(t_cycle_h=None, catalyst=r['catalyst'])
            if any(not math.isfinite(rec[k]) for k in ['T_K','P_bar','X','S','r','y_key','y_cofeed']):
                raise ValueError('nonfinite contract field')
            if not (rec['T_K'] > 0 and rec['P_bar'] > 0 and rec['r'] > 0 and 0 < rec['X'] <= 1
                    and 0 < rec['S'] <= 1 and 0 < rec['y_key'] <= 1 and rec['y_cofeed'] >= 0
                    and rec['y_key']+rec['y_cofeed'] <= 1+1e-8):
                raise ValueError('contract field outside physical range')
            records[rid] = rec
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
            rejected.append(dict(record_id=rid, group=r['group'], catalyst=r['catalyst'], reason=str(exc)))
    return records, dict(total=len(f), converted=len(records), rejected=len(rejected), exclusions=rejected,
                         conversion_notes=notes, rate_units='kg product/kg catalyst/h', loading_units='wt%')


def hand_reference(rxn):
    if rxn == 'meoh':
        sys.path.insert(0, str(REPO/'data/meoh'))
        import meoh_general_model as g
        m = g.M
        e = g.reference_economics()
        total = float(e['cost_eur_t'])*EUR_USD
        parts = dict(feed=float(e['h2_eur_t']+e['co2_eur_t'])*EUR_USD,
                     energy=float(e['elec_eur_t'])*EUR_USD,
                     capital=float(e['ACC_MEUR_Y'])*1e6/m.PROD_TPY*EUR_USD,
                     catalyst=float(e['cat_repl_eur_t'])*EUR_USD)
        parts['other'] = total-sum(parts.values())
        sys.path.insert(0,str(REPO/'analysis/meoh_literature_inversion_2026_10_05'))
        from meoh_candidates import plant_costs
        sample=pd.read_csv(ME/'pooled_candidates.csv').iloc[0].to_dict()
        rerun=plant_costs(sample)['cost_recycled_opt_inlet']
        assert math.isclose(rerun,sample['cost_recycled_opt_inlet'],rel_tol=1e-8), 'MeOH plant_costs source anchor'
        return dict(name='MeOH D01 industrial anchor', cost_usd_per_t=total, parts=parts,
                    record_cost_selfcheck=dict(frozen_eur_t=sample['cost_recycled_opt_inlet'],recomputed_eur_t=rerun,
                                               source='meoh_candidates.plant_costs; first pooled record'),
                    operating=dict(T_K=g.REF_T_C+273.15, P_bar=m.REF_PRESSURE_BAR, per_pass_conversion=m.SOURCE_X),
                    balances=dict(capacity_t_per_y=m.PROD_TPY, capex_usd=float(e['FCI_MEUR'])*1e6*EUR_USD,
                                  energy_GJ_per_t=float(e['P_co2_MW']+e['P_h2_MW']+e['P_rec_MW'])*3.6/m.PROD_TPH),
                    basis=dict(battery_limit='purchased H2/CO2 to MeOH; explicit recycle/purge/separation; ancillary costs calibrated to source',
                               feeds={'H2': dict(T_K=298.15,P_bar=30,purity_mol_frac=.995),
                                      'CO2': dict(T_K=298.15,P_bar=1,purity_mol_frac=1)},
                               product={'CH3OH': dict(state='liquid; downstream distillation included',P_bar=None,purity_mol_frac=None)},
                               capacity_t_per_y=m.PROD_TPY,operating_hours_per_y=m.HOURS_Y),
                    units=list(e['ec']), parameters=dict(compressor_efficiency=m.COMP_ETA, discount_rate=m.IR,
                        plant_life_y=m.PLANT_LIFE_Y, h2_feed_pressure_bar=m.H2_FEED_PRESSURE_BAR,
                        co2_feed_pressure_bar=m.CO2_FEED_PRESSURE_BAR, loop_dp_bar=m.LOOP_DP_BAR),
                    uncertainty=dict(productivity_density_g_cm3=[.5,2], scope='frozen hand sensitivity; no matched AI uncertainty distribution'),
                    currency=dict(USD_per_EUR=EUR_USD, basis='EUR2022 conversion in run_benchmark.py; no inflation adjustment'),
                    parts_rule='direct feed/electricity/ACC/catalyst; other closes total including indirect OPEX',
                    controlling_property='not available', attribution_source='no directly comparable attribution_share table identified')
    import yaml
    hc = module(HARNESS/'harness_core.py', 'blind_hand_nh3')
    cfg = yaml.safe_load((HARNESS/'configs/nh3_final_1_2.yaml').read_text(encoding='utf-8'))
    result = read_json(HARNESS/'outputs/nh3_final_1_2_20261013/results.json')
    anchor = result['deterministic']['metals']['Fe']['feasible']
    src = hc.parse_activity_workbook(HARNESS/cfg['inputs']['activity_workbook'])
    h = hc.NH3Harness.__new__(hc.NH3Harness)
    h.cfg = cfg
    h.ctx = hc.KineticContext(src['fits'],src['median_freqs'],src['gasrec'],'gillespie_beattie','newton_cooper')
    h.FUGACITY_IN_LOOP = True
    h._init_controls()
    state = h.self_consistent_process_state(anchor['T_C'],anchor['P_bar'],anchor['Tsep_C'])
    h.process_states=[state]
    ng=cfg['numerics']['descriptor_grid_eV']
    h.EGRID=np.round(np.arange(ng['start'],ng['stop']+1e-9,ng['step']),3)
    h._state_arrays()
    recomputed=h.cost_arrays('Fe',h.frozen_state_logtof(hc.EN0_CANON['Fe']))[0][0]
    assert math.isclose(recomputed,anchor['total_cost'],rel_tol=1e-8), 'NH3 harness reference anchor'
    b = anchor['breakdown']
    parts = dict(feed=0.,energy=b['fresh_comp']+b['recycle_comp']+b['refrigeration'],
                 capital=b['reactor_base']+b['vessel_pressure_premium']+b['compressor_capex'],catalyst=b['metal_cost'],other=0.)
    assert math.isclose(sum(parts.values()), anchor['total_cost'], rel_tol=1e-12)
    return dict(name='NH3 FINAL 1.2 fused Fe optimum (reduced catalyst-dependent cost)',cost_usd_per_t=anchor['total_cost'],parts=parts,
                record_cost_selfcheck=dict(frozen_usd_t=anchor['total_cost'],recomputed_usd_t=float(recomputed),
                                           source='harness_core cost_arrays and frozen_state_logtof at frozen Fe optimum'),
                raw_breakdown=b, operating=dict(T_K=anchor['T_C']+273.15,P_bar=anchor['P_bar'],per_pass_conversion=state['X']),
                balances=dict(capacity_t_per_y=h.annual_output_t,energy_GJ_per_t=parts['energy']/h.ELECTRICITY*3.6),
                basis=dict(battery_limit=cfg['economics_note']+' Purchased feed costs excluded.',
                           feeds={'N2':dict(T_K=298.15,P_bar=30,purity_mol_frac=1), 'H2':dict(T_K=298.15,P_bar=30,purity_mol_frac=1)},
                           product={'NH3':dict(state='condensed at separator',T_K=anchor['Tsep_C']+273.15,P_bar=anchor['P_bar'])},
                           capacity_t_per_y=h.annual_output_t,operating_hours_per_y=8760*h.CAPACITY_FACTOR),
                units=['reactor','fresh compression','recycle compression','refrigeration','compressor capex'],
                parameters={k:v for k,v in cfg['economics'].items() if isinstance(v,(int,float))},
                uncertainty=cfg['uncertainty'], controlling_property='not available',
                attribution_source='no directly comparable attribution_share table identified; raw breakdown is frozen results.json')


def flatten(obj, prefix=''):
    out = {}
    if isinstance(obj, dict):
        if 'value' in obj:
            return {prefix: obj['value']}
        for k,v in obj.items():
            if k != 'evidence':
                out.update(flatten(v, f'{prefix}.{k}' if prefix else k))
    else:
        out[prefix] = obj
    return out


def compare_reference(hand, ref, basis):
    rows = []
    def add(field,h,a):
        gap = (a/h-1) if isinstance(h,(int,float)) and isinstance(a,(int,float)) and h else None
        rows.append(dict(field=field,hand=h,ai=a,relative_gap=gap))
    add('cost_usd_per_t',hand['cost_usd_per_t'],ref.get('cost_usd_per_t'))
    for k in ['feed','energy','capital','catalyst','other']:
        add('parts.'+k,hand['parts'].get(k),ref.get('parts',{}).get(k))
        add('shares.'+k,hand['parts'].get(k,0)/hand['cost_usd_per_t'],ref.get('parts',{}).get(k,0)/ref['cost_usd_per_t'])
    for section in ['operating','balances']:
        for k,v in hand[section].items():
            add(section+'.'+k,v,ref.get(section,{}).get(k))
    hb,ab = flatten(hand['basis']),flatten(basis)
    for k in sorted(set(hb)|set(ab)):
        add('basis.'+k,hb.get(k),ab.get(k))
    return rows


def diagnose(hand, ref, basis, flow, sources, model, loader, errors, agreements):
    findings = []
    def add(category,evidence,impact):
        findings.append(dict(category=category,evidence=evidence,impact=impact))
    if not basis:
        add('boundary','basis.json absent','feed/product states, capacity and hours cannot be compared')
    if hand['parts']['feed'] == 0 and ref.get('parts',{}).get('feed',0)>0:
        add('boundary','hand NH3 excludes purchased feeds; AI has positive feed cost','total costs have different boundaries')
    hb, ab = flatten(hand['basis']),flatten(basis)
    for k in hb.keys() & ab.keys():
        if hb[k] != ab[k] and hb[k] is not None:
            add('boundary',dict(field=k,hand=hb[k],ai=ab[k]),'different plant design basis')
    hu = hand['units']
    au = [dict(name=u.get('name'),type=u.get('type')) for u in flow.get('units',[])]
    expected={'reactor','compressor'} if hand['parts']['feed']==0 else {'reactor','compressor','separation','heat_exchanger','furnace','pump'}
    actual={u.get('type') for u in au}
    add('structure',dict(hand_units=hu,ai_units=au,ai_checklist=flow.get('checklist'),
                         missing_hand_unit_types=sorted(expected-actual),
                         extra_ai_unit_types=sorted(str(t) for t in actual-expected),
                         ai_recycle_declaration=flow.get('checklist',{}).get('recycle','not available'),
                         hand_kinetics='NH3 descriptor microkinetics and 0.8 equilibrium approach' if hand['parts']['feed']==0 else 'lab conversion capped by equilibrium; purge and CO recycle optimisation'),
        'unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim')
    if not au:
        add('structure','flowsheet.json has no units','missing flowsheet evidence')
    pars = flatten(getattr(model,'PARAMS',{}))
    for s in sources:
        if s.get('type') != 'price_table':
            try:
                pars.setdefault(s['parameter'],float(s['value']))
            except (ValueError,TypeError,KeyError):
                pass
    gaps=[]
    for k,h in hand['parameters'].items():
        if k in pars and isinstance(pars[k],(int,float)) and h and abs(pars[k]/h-1)>.2:
            gaps.append(dict(parameter=k,hand=h,ai=pars[k],relative_gap=pars[k]/h-1))
    add('parameters',dict(gaps_gt20pct=gaps,unmatched_hand_parameters=sorted(set(hand['parameters'])-set(pars)),
                          hand_parameters=hand['parameters'],ai_parameters=pars,
                          price_table_rows=[s for s in sources if s.get('type')=='price_table']),
        'price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved')
    add('data',dict(rejected=loader['exclusions'],converted=loader['converted'],total=loader['total'],
                    missing_loading_records=sum(n.get('missing_loadings',False) for n in loader['conversion_notes'])),
        'unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking')
    if errors:
        add('numerics',errors,'failed/nonfinite/nonpositive cost or contract accounting error; excluded from costed denominator')
    else:
        add('numerics','all converted record costs finite, positive and parts close; deterministic repeat checked',
            'does not verify the optimiser reaches a global minimum')
    gaps = sorted([r for r in compare_reference(hand,ref,basis) if r['relative_gap'] is not None],key=lambda r:abs(r['relative_gap']),reverse=True)
    classified=[]
    for r in gaps:
        field=r['field']
        categories=['boundary'] if field.startswith('basis.') else ['structure','parameters']
        if field=='cost_usd_per_t' and hand['parts']['feed']==0 and ref.get('parts',{}).get('feed',0)>0:
            categories=['boundary','structure','parameters']
        classified.append(dict(**r,categories=categories,
                               rule='basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution'))
    ranking_gaps={}
    for name,comparison in agreements.items():
        ranking_gaps[name]=[dict(group=r['group'],hand_leader=r['hand']['plant_leader'],ai_leader=r['ai']['plant_leader'],
                                hand_gap=r['hand']['gap'],ai_gap=r['ai']['gap'],
                                categories=['structure','parameters','data']+(['boundary'] if hand['parts']['feed']==0 and ref.get('parts',{}).get('feed',0)>0 else []))
                            for r in comparison['groups'] if r['complete'] and r['ai'] and
                            (not r['verdict_agrees'] or not r['plant_leader_agrees'])]
        ranking_gaps[name].sort(key=lambda r:abs(r['ai_gap']-r['hand_gap']),reverse=True)
    return dict(rules='deterministic evidence comparison; categories are evidence, not causal proof',
                largest_reference_gaps=classified[:12],largest_ranking_gaps={k:v[:10] for k,v in ranking_gaps.items()},
                ranking_disagreements={k:v['verdict_disagreements'] for k,v in agreements.items()},
                findings=findings,uncertainty=dict(hand=hand['uncertainty'],ai_assumptions=[s for s in sources if s.get('type')=='assumption']))


def evaluate(rxn, runs, output_dir=None):
    f, variants = hand_tables(rxn)
    records, loader = load_records(rxn,f)
    hand = hand_reference(rxn)
    builds = {}
    for run in map(Path,runs):
        model=load_model(run)
        ref=model.reference()
        errors=[]; costs={}; outputs={}
        for rid,rec in records.items():
            try:
                out=model.plant_cost(dict(rec))
                cost=float(out['cost_usd_per_t'])
                if not math.isfinite(cost) or cost<=0:
                    raise ValueError('cost not finite and positive')
                if not math.isclose(sum(out['parts'].values()),cost,rel_tol=1e-6,abs_tol=1e-6):
                    raise ValueError('parts do not sum to total')
                costs[rid]=cost;outputs[rid]=out
            except Exception as exc:
                errors.append(dict(record_id=rid,reason=f'{type(exc).__name__}: {exc}'))
        if costs:
            rid=next(iter(costs))
            try:
                if not math.isclose(float(model.plant_cost(dict(records[rid]))['cost_usd_per_t']),costs[rid],rel_tol=1e-12):
                    raise ValueError('nondeterministic repeat')
            except Exception as exc:
                errors.append(dict(record_id=rid,reason=f'repeat: {type(exc).__name__}: {exc}'))
                costs.pop(rid)
                outputs.pop(rid)
        scored=f[f.hand_eligible & f.record_id.isin(costs)].copy()
        scored['ai_cost']=scored.record_id.map(costs)
        gs=group_verdicts(scored,rxn,'ai_cost')
        ai_by={x['group']:x for x in gs}
        comparisons={}
        for name,hg in variants.items():
            rows=[]
            for h in hg:
                a=ai_by.get(h['group'])
                # Partial groups must never silently count as a matched comparison.
                original=f[f.hand_eligible & (f.group==h['group'])]
                complete=all(rid in costs for rid in original.record_id)
                rows.append(dict(group=h['group'],hand=h,ai=a,complete=complete,
                                 verdict_agrees=(a['changed']==h['changed']) if a and complete else None,
                                 gt5pct_agrees=(a['gt5pct']==h['gt5pct']) if a and complete else None,
                                 plant_leader_agrees=(a['plant_leader']==h['plant_leader']) if a and complete else None))
            eligible=[r for r in rows if r['verdict_agrees'] is not None]
            comparisons[name]=dict(hand_summary=summary(hg),compared_groups=len(eligible),
                                   verdict_agreements=sum(r['verdict_agrees'] for r in eligible),
                                   verdict_disagreements=sum(not r['verdict_agrees'] for r in eligible),
                                   gt5pct_agreements=sum(r['gt5pct_agrees'] for r in eligible),groups=rows,
                                   spearman_pooled=rho(scored.ai_cost,scored['hand_raised_cost' if name=='raised_conversion' else 'hand_cost']),
                                   spearman_within_groups={g:rho(x.ai_cost,x['hand_raised_cost' if name=='raised_conversion' else 'hand_cost']) for g,x in scored.groupby('group') if len(x)>=2})
        analysis=read_json(run/'analysis.json');basis=read_json(run/'basis.json');flow=read_json(run/'flowsheet.json')
        sources=list(csv.DictReader((run/'sources.csv').open(encoding='utf-8-sig'))) if (run/'sources.csv').exists() else []
        attr=analysis.get('attribution_share') or {}
        top=max(attr,key=attr.get) if attr else 'not available'
        cheapest=min(costs,key=costs.get) if costs else None
        hand_costs={r.record_id:r.hand_cost for r in f.itertuples() if r.record_id in costs and np.isfinite(r.hand_cost)}
        hbest=min(hand_costs,key=hand_costs.get) if hand_costs else None
        # Full original groups only for primary summary; report partial groups separately.
        complete_keys={r['group'] for r in next(iter(comparisons.values()))['groups'] if r['complete']}
        builds[str(run)]=dict(reference=ref,basis=basis,reference_comparison=compare_reference(hand,ref,basis),
            run_artifact_sha256={name:hashlib.sha256((run/name).read_bytes()).hexdigest()
                                 for name in ['model.py','basis.json','flowsheet.json','sources.csv','analysis.json'] if (run/name).exists()},
            n_costed=len(costs),n_scored_records=len(scored),cost_failures=errors,
            ranking=summary([g for g in gs if g['group'] in complete_keys]),partial_group_verdicts=[g for g in gs if g['group'] not in complete_keys],
            hand_comparison=comparisons,bottlenecks=dict(largest_cost_item=max(ref['parts'],key=ref['parts'].get),
                hand_largest_cost_item=max(hand['parts'],key=hand['parts'].get),controlling_property=top,
                hand_controlling_property=hand['controlling_property'],attribution_share=attr,
                cheapest_record=cheapest,cheapest_catalyst=records[cheapest]['catalyst'] if cheapest else None,
                hand_cheapest_record=hbest,hand_cheapest_catalyst=records[hbest]['catalyst'] if hbest else None),
            diagnosis=diagnose(hand,ref,basis,flow,sources,model,loader,errors,comparisons),record_costs=costs)
    shared=set.intersection(*(set(b['record_costs']) for b in builds.values())) if builds else set()
    # Recompute cheapest over exactly the same successful records for all builds.
    for b in builds.values():
        key=min(shared,key=b['record_costs'].get) if shared else None
        b['bottlenecks']['cheapest_common_record']=key
        b['bottlenecks']['cheapest_common_catalyst']=records[key]['catalyst'] if key else None
        hc={r.record_id:r.hand_cost for r in f.itertuples() if r.record_id in shared and np.isfinite(r.hand_cost)}
        hkey=min(hc,key=hc.get) if hc else None
        b['bottlenecks']['hand_cheapest_common_record']=hkey
        b['bottlenecks']['hand_cheapest_common_catalyst']=records[hkey]['catalyst'] if hkey else None
    pairs={f'{a} vs {b}':rho([builds[a]['record_costs'][k] for k in sorted(shared)],
                            [builds[b]['record_costs'][k] for k in sorted(shared)]) for a,b in combinations(builds,2)}
    refs=[b['reference']['cost_usd_per_t'] for b in builds.values()]
    spread=max(refs)/min(refs)-1 if refs else None
    def agreement(vals):
        if any(v is None or v=='not available' for v in vals):
            return 'not available'
        n=max(vals.count(v) for v in vals)
        return 'robust (all agree)' if n==len(vals) else 'majority' if n>len(vals)/2 else 'model-dependent'
    conclusions={k:dict(status=agreement([b['bottlenecks'][k] for b in builds.values()]),
                         values={r:b['bottlenecks'][k] for r,b in builds.items()})
                 for k in ['largest_cost_item','controlling_property','cheapest_common_catalyst']}
    out=dict(rxn=rxn,loader=loader,hand_counts={k:summary(v) for k,v in variants.items()},hand_reference=hand,
             builds=builds,agreement=dict(reference_spread=spread,spread_within20pct=spread<=.2 if spread is not None else None,
                 pairwise_spearman=pairs,pairwise_ge08=all(v is not None and v>=.8 for v in pairs.values()) if pairs else None,
                 quantitative_consistency=(spread<=.2 and all(v is not None and v>=.8 for v in pairs.values())) if pairs else None,
                 common_successful_records=len(shared),conclusions=conclusions),
             primary_build_median_reference=sorted(builds,key=lambda r:builds[r]['reference']['cost_usd_per_t'])[len(builds)//2],
             rules=dict(lab='STY catalyst-level' if rxn=='meoh' else 'paper_rate record-level',gap='strictly >5% among changed groups',
                        incomplete_groups='excluded from primary AI summary and hand agreement; partial verdicts separate'))
    source_paths=([ME/'pooled_candidates.csv',ME/'robustness/conversion_s6/s6_conversion_points.csv',
                   REPO/'analysis/meoh_catalyst_level_2026_10_19/run_catalyst_level.py',REPO/'data/meoh/meoh_d01_model.py',
                   REPO/'data/meoh/meoh_general_model.py'] if rxn=='meoh' else
                  [NH/'candidates_printed.csv',NH/'summary_printed.json',HARNESS/'harness_core.py',
                   HARNESS/'configs/nh3_final_1_2.yaml',HARNESS/'outputs/nh3_final_1_2_20261013/results.json'])
    out['source_sha256']={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    out=clean(out)
    dest=Path(output_dir) if output_dir else HERE/'evaluation';dest.mkdir(exist_ok=True,parents=True)
    (dest/f'{rxn}_blind.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    lines=[f'# {rxn.upper()} blind evaluation', '', f'Loader: {loader["converted"]}/{loader["total"]}; rejected {loader["rejected"]}.', '',
           '| Hand convention | Changed/groups | >5% | Paper bootstrap 95% CI |','|---|---:|---:|---|']
    for k,v in out['hand_counts'].items():
        lines.append(f'| {k} | {v["changed"]}/{v["groups"]} | {v["gt5pct"]} | {v["ci95"]} |')
    lines+=['', 'Unit conversion and ranking rules: see blind_eval.py module docstring.',
            'The raised-conversion hand comparison retains its own frozen scenario. AI inputs are the same measured records.',
            'NH3 hand costs are reduced catalyst-dependent costs; feed cost is outside that boundary.','']
    for run,b in out['builds'].items():
        lines += [f'## {Path(run).name}', '', f'Costed {b["n_costed"]}/{loader["converted"]}; scored records {b["n_scored_records"]}.',
                  f'AI ranking: {json.dumps(b["ranking"],ensure_ascii=False)}', '',
                  '| Reference quantity | Hand | AI | Relative gap |','|---|---|---|---|']
        for r in b['reference_comparison']:
            cells=[r['field'],r['hand'],r['ai'],r['relative_gap']]
            lines.append('| '+' | '.join(str(v).replace('|','/') for v in cells)+' |')
        for convention,comparison in b['hand_comparison'].items():
            lines += ['',f'### Group comparison: {convention}','',
                      f'Compared {comparison["compared_groups"]}; verdict agreement {comparison["verdict_agreements"]}; '+
                      f'pooled cost Spearman {comparison["spearman_pooled"]}.','',
                      '| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |',
                      '|---|---|---|---|---|---:|---:|---|---:|']
            for r in comparison['groups']:
                a=r['ai'] or {}
                cells=[r['group'],r['complete'],r['hand']['changed'],a.get('changed'),r['verdict_agrees'],
                       r['hand']['gap'],a.get('gap'),r['plant_leader_agrees'],comparison['spearman_within_groups'].get(r['group'])]
                lines.append('| '+' | '.join(str(v).replace('|','/') for v in cells)+' |')
        for title,key in [('Bottlenecks','bottlenecks'),('Difference diagnosis and uncertainty','diagnosis')]:
            lines += ['',f'### {title}','','```json',json.dumps(b[key],ensure_ascii=False,indent=2),'```']
    lines+=['','## Across-build agreement','','```json',json.dumps(out['agreement'],ensure_ascii=False,indent=2),'```',
            '',f'Primary build (median reference cost): {out["primary_build_median_reference"]}',
            '', '## Loader exclusions','',json.dumps(loader['exclusions'],ensure_ascii=False,indent=2)]
    (dest/f'{rxn}_blind.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(rxn=rxn,hand_counts=out['hand_counts'],loader={k:loader[k] for k in ['total','converted','rejected']},
                         builds={k:dict(n_costed=b['n_costed'],ranking=b['ranking']) for k,b in out['builds'].items()},output=str(dest)),ensure_ascii=False,indent=2))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rxn',choices=['nh3','meoh']);p.add_argument('runs',nargs='+');p.add_argument('--output-dir',type=Path)
    args=p.parse_args();evaluate(args.rxn,args.runs,args.output_dir)
