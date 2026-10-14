"""Run the useful engineering chain, not a point-by-point reproduction exercise.

SI parameters -> physical flash -> closed recycle -> compression/cold duty ->
conditional utility tradeoffs. Recorded sources and scenario inputs stay distinct.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import argparse, csv, hashlib, itertools, json
import numpy as np
from model import PARAMS, State, interactions, fractions
from loop import Settings, solve, source_streams, source_flow


def json_default(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,np.ndarray):return v.tolist()
    raise TypeError(type(v).__name__)


def first_separator():
    st=source_streams();feed=source_flow(st[4]);ref_gas=source_flow(st[5]);ref_liq=source_flow(st[7])
    result=[]
    for mode in ('zero','si2024'):
        state=State(294.15,18.02e6,0.,mode)
        v,l,r=state.split(feed,stability=True)
        result.append({'model':mode,'gas_NH3_pct':100*r.y[4],
            'source_gas_NH3_pct':100*fractions(ref_gas)[4],
            'gas_NH3_abs_relative_error_pct':100*abs(r.y[4]/fractions(ref_gas)[4]-1),
            'liquid_NH3_pct':100*r.x[4],'source_liquid_NH3_pct':100*fractions(ref_liq)[4],
            'beta_vapor':r.beta,'source_beta_vapor':ref_gas.sum()/feed.sum(),
            'equilibrium_residual':r.residual,
            'basis':'Source stream4 feed, specified T/P; source streams5 and7 used only after prediction'})
    return result


def row(record,label):
    s=record['settings']
    return {'case':label,'model':s['mode'],'T2_C':s['T2']-273.15,
        'conversion':s['conversion'],'purge':s['purge'],'CH4_NH3_k_assumed':s['methane_k'],
        'dP_bar':(s['P_reactor']-s['P2'])/1e5,
        **{k:record[k] for k in ('liquid_NH3_tpd','feed_total_kmol_h','feed_NH3_molpct','feed_inerts_molpct',
        'sep1_vapor_NH3_molpct','NH3_product_recovery_fraction','H2_purge_kg_h',
        'compression_shaft_MW_scenario','recycle_shaft_MW_scenario',
        'second_stage_refrigeration_MW_scenario','utility_USD_per_t_scenario',
        'component_residual_rel_fresh','flash_log_fugacity_error')},
        'case_type':'conditional engineering scenario, not independently predicted catalyst performance'}


def evaluate(outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    base=solve(Settings())
    reference=solve(Settings(mode='zero'))
    rows=[row(base,'nominal_si'),row(reference,'prior_zero_k')]
    failures=[]
    # A predeclared engineering sweep, not a claimed source temperature-validity
    # interval or a fitted envelope. All trials, including failures, are kept.
    for temp,conv,purge in itertools.product((-10.,0.,10.),(.225,.275,.325),(.015,.03,.06)):
        config=replace(Settings(),T2=temp+273.15,conversion=conv,purge=purge)
        name=f'T{temp:+g}_X{conv:g}_p{purge:g}'
        try: rows.append(row(solve(config),name))
        except (ValueError,RuntimeError) as exc:failures.append({'case':name,'reason':str(exc)})
    for methanek in (-.1,.1,.2):
        config=replace(Settings(),methane_k=methanek)
        name=f'missing_CH4_k_{methanek:+g}'
        try: rows.append(row(solve(config),name))
        except (ValueError,RuntimeError) as exc:failures.append({'case':name,'reason':str(exc)})
    for deltaP in (3.,15.):
        # Keep source flash pressures constant. The compressor outlet changes;
        # conversion remains a scenario input, no false kinetic P dependence.
        config=replace(Settings(),P_reactor=17.88e6+deltaP*1e5,
            P1=min(18.02e6,17.88e6+deltaP*1e5))
        name=f'dP_{deltaP:g}bar'
        try: rows.append(row(solve(config),name))
        except (ValueError,RuntimeError) as exc:failures.append({'case':name,'reason':str(exc)})
    with (outdir/'scenarios.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    staged=first_separator()
    summary={'model':'NH3-SI-LOOP-v1','source_S27':PARAMS,
        'SI_effect_at_first_separator':staged,'nominal_loop':base,'zero_k_loop':reference,
        'successful_scenarios':len(rows),'failed_scenarios':failures,
        'scenario_count_includes_two_reference_cases':True,
        'SI_2024_parameters_are_external_not_industrial_fitted':True,
        'missing_CH4_parameter_scenarios':[-.1,0.,.1,.2],
        'legacy_24_of_28_gate':'archived in prior experiment; not a gate for exploring this explicitly conditional scenario',
        'main_model_status':'canonical costs, Fe/Ru/Os ranking and 32/64 benchmark untouched',
        'max_component_residual_rel_fresh':max(r['component_residual_rel_fresh'] for r in rows),
        'max_flash_log_fugacity_error':max(r['flash_log_fugacity_error'] for r in rows),
        'scope':'Two cold flashes+purge+makeup+recycle, specified reactor conversion, efficiency/COP and missing BIP assumptions. Utility-only objective, no catalyst cost or first cooler/reactor energy.'}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,default=json_default)+'\n',encoding='utf-8')
    rowsweep=[r for r in rows if r['case'].startswith('T') and abs(r['conversion']-.275)<1e-9]
    best=min(rowsweep,key=lambda r:r['utility_USD_per_t_scenario'])
    texts=[
        '# SI-S27 to an operable ammonia process loop', '',
        'The user-supplied SI parameters are applied directly; reproducing every molecular-simulation point is not a prerequisite.',
        '', '## Source and equations',
        'SI Section 4 / Table S27, S-33: kij(T)=a0+a1*T+a2*T^2 with T in K. PR and PC-SAFT columns are separate. PR Ar/H2/N2 entries are used. O2 is not part of the synthesis loop. S27 has no CH4-NH3 row: k=0 is the nominal assumption, with -0.1/+0.1/+0.2 sensitivity runs; the six dry-gas pairs are zero. The printed SI does not specify the complete correlation validity interval.',
        '', '## Actual first-separator prediction',
        '| Closure | Vapor NH3 mol% | Liquid NH3 mol% | Vapor fraction | Gas NH3 relative error |',
        '|---|---:|---:|---:|---:|']
    for r in staged:texts.append(f"| {r['model']} | {r['gas_NH3_pct']:.3f} | {r['liquid_NH3_pct']:.3f} | {r['beta_vapor']:.5f} | {r['gas_NH3_abs_relative_error_pct']:.2f}% |")
    texts.extend([
        '| Published source | 8.510 | 98.550 | 0.87601 | - |',
        '', '## Closed-loop result',
        'Flow order: reactor -> flash1 -> purge -> makeup12 -> flash2 -> compression -> reactor. This is a declared engineering topology; hydrogen recovery upstream of makeup12 is outside this control volume. Reactor single-pass N2 conversion 27.5%, purge 3%, compressor isothermal-equivalent efficiency 75%, refrigerator COP 2.5, electricity 50 USD/MWh are explicit inputs.',
        f"- SI-model net liquid NH3 **{base['liquid_NH3_tpd']:.2f} t/d**; feed **{base['feed_total_kmol_h']:.2f} kmol/h**; inlet NH3 **{base['feed_NH3_molpct']:.3f} mol%**.",
        f"- Relative five-component balance residual **{base['component_residual_rel_fresh']:.2e}**; maximum flash log-fugacity residual **{base['flash_log_fugacity_error']:.2e}**. Multi-start local phase-stability checks passed for the terminal splits.",
        f"- Conditional compressor work **{base['compression_shaft_MW_scenario']:.3f} MW** (recycle **{base['recycle_shaft_MW_scenario']:.3f} MW**); second-stage refrigeration electric load **{base['second_stage_refrigeration_MW_scenario']:.3f} MW**.",
        f"- Compressor plus second-stage cold-utility objective **{base['utility_USD_per_t_scenario']:.3f} USD/t** versus zero-k model **{reference['utility_USD_per_t_scenario']:.3f} USD/t**. This is NOT total ammonia cost or the paper's catalyst-dependent objective.",
        '', '## Useful engineering tradeoffs at fixed 27.5% N2 conversion',
        '| T2 (C) | Purge | Liquid NH3 t/d | H2 purge kg/h | Utility USD/t |',
        '|---|---:|---:|---:|---:|'])
    for r in rowsweep:texts.append(f"| {r['T2_C']:.0f} | {r['purge']:.3f} | {r['liquid_NH3_tpd']:.1f} | {r['H2_purge_kg_h']:.1f} | {r['utility_USD_per_t_scenario']:.3f} |")
    texts.extend(['',
        f"Completed **{len(rows)}** scenarios; **{len(failures)}** failed. Failure details are retained in summary.json. Among this restricted conversion slice, the utility-only minimum is at T2={best['T2_C']:.0f} C, purge={best['purge']:.3f}, **{best['utility_USD_per_t_scenario']:.3f} USD/t**. Feed loss has not been priced, so this is not a full economic optimum.",
        '', '## Interpretation and next connection',
        'The chain now runs through source parameters, physical phase splitting, cyclic mass balance, and explicit utility tradeoffs. Next connect candidate-specific kinetics and equipment/metal costs to this same callable loop. Do not relabel prescribed-conversion scenarios as independent Fe/Ru/Os predictions.',
        'No strict demand for identical published production or every legacy point is used to veto exploratory calculations. Thermodynamic/mass failures still stop the affected case; engineering assumptions stay visible in machine-readable outputs.', ''])
    (outdir/'REPORT.md').write_text('\n'.join(texts),encoding='utf-8')
    print('\n'.join(texts))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args();evaluate(a.out_dir)
