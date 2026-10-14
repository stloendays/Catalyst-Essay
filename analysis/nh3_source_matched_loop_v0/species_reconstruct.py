#!/usr/bin/env python3
"""NH3-STREAM-V0.2: multi-component steady-state industrial source reconstruction.

12 industrial streams, five species, source Figure 57 (Appl, Ullmann 2011).
This is an observation-constrained *process reconstruction* with explicit
stoichiometry and stream split/mixing equations; it is NOT an independent
kinetic/economic plant simulator or a refit of the canonical NH3-FINAL-1.2 model.

All literature stream values are read verbatim from pinned figure57_streams.csv.
The figure data are tabular rounded observations; balances should not be taken
to imply unrounded instrument-grade process predictions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from source_matched import load_source_ledger, field
from diagnose_separator_vle import grid_from_printed_sources, source_interpolation

HERE = Path(__file__).resolve().parent
FILE = HERE / "figure57_streams.csv"
FILE_BLOB = "7d511a788895d1f3ab825f9db9a3f0929db44460"
DOI = "10.1002/14356007.o02_o11"
NAMES = ("N2","H2","CH4","Ar","NH3")
# Standard molecular masses only for separating liquid NH3 component from
# total stream mass (kg/kmol). No EOS or component fugacity is claimed.
MW = {"N2":28.0134,"H2":2.01588,"CH4":16.0425,"Ar":39.948,"NH3":17.031}
NU = {"N2":-0.5,"H2":-1.5,"CH4":0.0,"Ar":0.0,"NH3":1.0}


def blob_sha(path: Path) -> str:
    d = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(d)).encode() + b"\0" + d).hexdigest()


def load_streams() -> dict[int, dict]:
    if blob_sha(FILE) != FILE_BLOB:
        raise AssertionError("The 12-stream primary-source table changed; update the reviewed provenance pin deliberately")
    with FILE.open(encoding="utf-8",newline="") as f:
        raw=list(csv.DictReader(f))
    if len(raw)!=12 or {int(r["stream_id"]) for r in raw}!=set(range(1,13)):
        raise AssertionError("Require exactly 12 distinct printed Figure 57 streams")
    streams={}
    for r in raw:
        k=int(r["stream_id"])
        F=float(r["flow_kmol_h"])
        y={name:float(r[f"{name}_molpct"])/100.0 for name in NAMES}
        if r["primary_doi"]!=DOI or r["printed_page"]!="211" or r["source_figure"]!="Figure 57":
            raise AssertionError(f"Source provenance missing: stream {k}")
        if not 0<F or any(x<0 or x>1 for x in y.values()):
            raise AssertionError(f"Invalid source stream: {k}")
        # Printed percentages have two decimals; require normalized inputs,
        # but do not renormalize to hide table rounding.
        if abs(sum(y.values())-1.0)>0.0002:
            raise AssertionError(f"Printed mole fractions off-scale: stream {k}, sum {sum(y.values())}")
        streams[k]={
            "id":k,"label":r["stream_label"],"flow_kmol_h":F,
            "T_C":float(r["temperature_C"]),"P_MPa":float(r["pressure_MPa"]),
            "y":y,"component_kmol_h":{n:F*y[n] for n in NAMES},
            "source_nh3_liquid_t_h":None if not r["nh3_liquid_t_h"] else float(r["nh3_liquid_t_h"]),
            "source_doi":DOI,
        }
    validate_literature_links(streams)
    return streams


def validate_literature_links(st: dict[int,dict]) -> None:
    db=load_source_ledger()
    checks={
        ("R0004","loop_pressure_bar"):st[1]["P_MPa"]*10.0,
        ("R0009","other"):st[4]["T_C"],
        ("R0010","inlet_NH3_molpct"):st[1]["y"]["NH3"]*100.0,
        ("R0011","other"):st[2]["y"]["NH3"]*100.0,
        ("R0012","outlet_NH3_molpct"):st[4]["y"]["NH3"]*100.0,
        ("R0013","inerts_inlet_molpct"):(st[1]["y"]["Ar"]+st[1]["y"]["CH4"])*100.0,
        ("R0014","separator_T_C"):st[5]["T_C"],
        ("R0015","separator_T_C"):st[6]["T_C"],
        ("R0019","converter_dP_bar"):(st[1]["P_MPa"]-st[4]["P_MPa"])*10.0,
        ("R0020","loop_dP_bar"):(st[1]["P_MPa"]-st[6]["P_MPa"])*10.0,
        ("R0023","other"):st[9]["flow_kmol_h"],
    }
    for (rid,qty),expected in checks.items():
        from source_matched import evidence
        entry = evidence(db,rid,qty,allow_derived=True)
        registered=float(entry["value"])
        if abs(registered-expected)>5e-5:
            raise AssertionError(f"12-stream source differs from frozen ledger at {rid}: {expected} vs {registered}")
    if abs(st[1]["flow_kmol_h"]-28344)>1e-6 or st[10]["flow_kmol_h"]+st[11]["flow_kmol_h"]!=st[12]["flow_kmol_h"]:
        raise AssertionError("Published Figure 57 source flow identity no longer present")


def gas_components(st: dict[int,dict], ids: tuple[int,...]) -> dict[str,float]:
    return {name:sum(st[k]["component_kmol_h"][name] for k in ids) for name in NAMES}


def balance(st: dict[int,dict], name: str, inputs: tuple[int,...],
            outputs: tuple[int,...], extent_kmol_h:float=0.0,
            *, basis:str) -> dict:
    """out-in-nu*extent: zero if species-conserving flow unit with declared reaction."""
    ins=gas_components(st,inputs);outs=gas_components(st,outputs)
    F_in=sum(st[i]["flow_kmol_h"] for i in inputs)
    F_out=sum(st[i]["flow_kmol_h"] for i in outputs)
    if not F_in>0 or extent_kmol_h<0:
        raise ValueError("Invalid balance boundary")
    residuals={k:outs[k]-ins[k]-NU[k]*extent_kmol_h for k in NAMES}
    # Sum of the reaction stoichiometric coefficients is -1 per NH3 formed.
    total_residual=F_out-F_in+extent_kmol_h
    if abs(sum(residuals.values())-total_residual)>F_in*0.0002:
        raise AssertionError("Printed mole-fraction sums inconsistent with aggregate balance")
    return {
        "boundary":name,
        "stream_inputs":"+".join(map(str,inputs)),
        "stream_outputs":"+".join(map(str,outputs)),
        "basis":basis,
        "NH3_extent_kmol_h":extent_kmol_h,
        "total_in_kmol_h":F_in,"total_out_kmol_h":F_out,
        "total_mole_balance_residual_kmol_h":total_residual,
        "total_balance_abs_pct_feed":100.0*abs(total_residual)/F_in,
        "species_residuals_kmol_h":residuals,
        "max_species_residual_kmol_h":max(abs(x) for x in residuals.values()),
        "max_species_residual_pct_feed":100.0*max(abs(x) for x in residuals.values())/F_in,
        "analysis_type":"steady_state_reconstruction_from_industrial_observations",
    }


def extent_from_nh3(st, src, dst) -> float:
    return st[dst]["component_kmol_h"]["NH3"]-st[src]["component_kmol_h"]["NH3"]


def source_observation_reconstruction() -> dict:
    st=load_streams()
    full_extent=extent_from_nh3(st,1,4)
    stage_a=extent_from_nh3(st,1,2)
    stage_b=extent_from_nh3(st,3,4)
    if abs((stage_a+stage_b)-full_extent)>1e-6:
        raise AssertionError("Converter stages 2->3 change amount of NH3 unexpectedly")
    groups=[
        balance(st,"converter_first_two_beds",(1,),(2,),stage_a,
                basis="reaction N2+3H2->2NH3, measured source inlet and first-vessel outlet"),
        balance(st,"intervessel_cooling",(2,),(3,),0,
                basis="same printed total and gas composition; heat exchange not simulated"),
        balance(st,"converter_third_bed",(3,),(4,),stage_b,
                basis="reaction across second converter vessel, outlet stream4 is post-waste-heat boiler"),
        balance(st,"converter_overall",(1,),(4,),full_extent,
                basis="independent source inlet and final-effluent gas composition"),
        balance(st,"first_separator",(4,),(5,7),0,
                basis="gas-liquid split with all five species; no pure-NH3 assumption"),
        balance(st,"hydrogen_recovery_makeup_mixing",(10,11),(12,),0,
                basis="printed combined makeup stream after recovery, no chemistry"),
        balance(st,"recycle_transport",(6,),(1,),0,
                basis="same gas composition/flow, pressure step + downstream sensible heating distinct"),
        balance(st,"aggregate_separation_purge_mixing",(5,7,10),(6,8,9),0,
                basis="multi-unit control-volume boundary, does NOT uniquely determine pipe routing"),
        balance(st,"overall_plant_external",(10,),(8,9),full_extent,
                basis="source raw makeup to liquid product plus offgas, no other external feeds assumed"),
    ]
    # These tolerances gate source internal consistency; these are NOT claimed
    # metrology precision, preregistered plant-prediction bounds, or an EOS fit.
    for g in groups:
        if g["max_species_residual_pct_feed"]>0.08:
            raise AssertionError(f"Multi-species control volume inconsistent: {g['boundary']} {g['max_species_residual_pct_feed']}")
        if g["total_balance_abs_pct_feed"]>0.08:
            raise AssertionError(f"Overall mole-flow control volume inconsistent: {g['boundary']} {g['total_balance_abs_pct_feed']}")
    stage1=st[4];stage7=st[7];stage5=st[5]
    F_vapor=stage1["flow_kmol_h"]-stage7["flow_kmol_h"]
    pred={
        k:(stage1["component_kmol_h"][k]-stage7["component_kmol_h"][k])/F_vapor*100.0
        for k in NAMES
    }
    if F_vapor<=0:
        raise AssertionError("Impossible stage-1 gas-liquid flow split")
    if abs(F_vapor-stage5["flow_kmol_h"])>2.0:
        raise AssertionError("Source stage-1 mass balance mismatches stream5 flow")
    liquid=[]
    for id in (7,8,9):
        v=st[id]
        printed=v["source_nh3_liquid_t_h"]
        computed=v["component_kmol_h"]["NH3"]*MW["NH3"]/1000.0
        liquid.append({
            "stream":id,
            "source_printed_NH3_liquid_t_h":printed,
            "computed_NH3_component_t_h":computed,
            "computed_minus_printed_t_h":computed-printed,
            "total_stream_mass_t_h":sum(v["component_kmol_h"][k]*MW[k] for k in NAMES)/1000.0,
            "important":"Figure 57 liquid production mass is the NH3 component, not necessarily total impure-liquid mass",
        })
    if max(abs(v["computed_minus_printed_t_h"]) for v in liquid)>.035:
        raise AssertionError("NH3 component liquid product not aligned with printed output")
    # Compare saturated vapor at the *printed Figure57 gas-stream* P and T,
    # distinct from the old ledger's secondary liquid-pressure assumption.
    # This is a cross-mixture external reference, NOT a 5-component EOS.
    source_grid=grid_from_printed_sources()
    separator_thermo=[]
    for stream_id in (5,6):
        v=st[stream_id]
        table=source_interpolation(source_grid,v["T_C"],v["P_MPa"]*10.0)
        source=100.0*v["y"]["NH3"]
        separator_thermo.append({
            "stream":stream_id,
            "temperature_C":v["T_C"],
            "pressure_bar_from_printed_gas_stream":v["P_MPa"]*10.0,
            "observed_plant_NH3_molpct":source,
            "BASF_in_domain_1to3_N2H2_vapor_NH3_molpct":table,
            "relative_source_minus_BASF_pct":100.0*(source/table-1.0),
            "reference_mixture_scope":"BASF H2:N2=3:1 gas mixture vs plant CH4/Ar-bearing stream; not a validated industrial multicomponent EOS",
        })
    # The source-based production estimate uses only 1 and 4, not observed
    # production totals, and does NOT establish independently predictive kinetics.
    converted_tpd=full_extent*MW["NH3"]*24.0/1000.0
    # Independent stoichiometric reconstruction using ONLY F_in and the two
    # printed mole fractions; differs from the component-flux estimate because
    # all source flows and compositions were rounded independently.
    via_total_flow_extent=(
        st[1]["flow_kmol_h"]*
        (st[4]["y"]["NH3"]-st[1]["y"]["NH3"])/
        (1.0+st[4]["y"]["NH3"])
    )
    via_total_flow_tpd=via_total_flow_extent*MW["NH3"]*24.0/1000.0
    product_total_tpd=st[8]["source_nh3_liquid_t_h"]*24.0
    product_component_tpd=liquid[1]["computed_NH3_component_t_h"]*24.0
    return {
        "method":"NH3-STREAM-V0.2",
        "status":"INDUSTRIAL_OBSERVATION_CONSTRAINED_STEADY_STATE_SIMULATION__NOT_INDEPENDENT_KINETICS",
        "source_DOI":DOI,"printed_page":211,"figure":"Figure 57",
        "reactor_converted_NH3_tpd":converted_tpd,
        "reactor_NH3_tpd_from_total_flow_stoichiometry":via_total_flow_tpd,
        "rounding_basis_difference_tpd":via_total_flow_tpd-converted_tpd,
        "industrial_reported_liquid_NH3_tpd":product_total_tpd,
        "reactor_vs_reported_product_relative_pct":100.0*(converted_tpd/product_total_tpd-1.0),
        "liquid_NH3_component_based_tpd":product_component_tpd,
        "reactor_vs_composition_derived_product_pct":100.0*(converted_tpd/product_component_tpd-1.0),
        "first_separator_NH3_gas_pred_pct":pred["NH3"],
        "first_separator_NH3_gas_observed_pct":stage5["y"]["NH3"]*100.0,
        "first_separator_NH3_molpct_point_diff":pred["NH3"]-100.0*stage5["y"]["NH3"],
        "first_separator_pred_all_5_species_pct":pred,
        "reconstructed_liquid_NH3_component":liquid,
        "stream6_stream1_NH3_pct":(st[6]["y"]["NH3"]*100,st[1]["y"]["NH3"]*100),
        "documented_loop_pressure_difference_bar":(st[1]["P_MPa"]-st[6]["P_MPa"])*10.0,
        "source_stage_vle_crossmixture_reference":separator_thermo,
        "full_streams_n":len(st),
        "components":list(NAMES),
        "independent_source_units_n":1,
        "balance_groups":groups,
        "source_limitations":"One published case; all values supplied by same industrial table. Inverse reconstruction tests conservation and source consistency, not independent rate or equipment predictions. Source rounding and stage enthalpy are unmodeled.",
        "unchanged_NH3_FINAL_1_2_score":"32/64",
    }


def write_report(record: dict, directory: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"species_summary.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    columns=["boundary","stream_inputs","stream_outputs","NH3_extent_kmol_h","total_balance_abs_pct_feed","max_species_residual_kmol_h","max_species_residual_pct_feed","basis"]
    with (directory/"component_balance_9.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for x in record["balance_groups"]:w.writerow({k:x[k] for k in columns})
    with (directory/"component_residuals_45.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["boundary","species","out_minus_in_minus_reaction_kmol_h"])
        w.writeheader()
        for item in record["balance_groups"]:
            for name,v in item["species_residuals_kmol_h"].items():
                w.writerow({"boundary":item["boundary"],"species":name,
                            "out_minus_in_minus_reaction_kmol_h":v})
    lines=[
        "# Source-matched industrial NH3 process simulation: 12-stream five-species steady-state reconstruction",
        "",
        "**Simulation basis:** industrial observations constrain conversion extent and stream conditions; "
        "species mole balances reconstruct reactors, cold separators, recovered-gas blending and purge boundaries. "
        "No kinetic parameters or equipment thermal duties are fitted or independently predicted.",
        "",
        f"Literature: Max Appl (2011), Ullmann, Ammonia 2, Fig. 57 p. 211, doi:{DOI}.",
        "",
        f"Converter NH3 production calculated from stream1 and stream4: **{record['reactor_converted_NH3_tpd']:.2f} t/d**; "
        f"independent total-flow stoichiometric estimate **{record['reactor_NH3_tpd_from_total_flow_stoichiometry']:.2f} t/d** "
        f"(difference **{record['rounding_basis_difference_tpd']:.2f} t/d** from independently rounded source columns); ",
        f"published stream8 NH3 liquid: **{record['industrial_reported_liquid_NH3_tpd']:.2f} t/d** "
        f"(signed difference **{record['reactor_vs_reported_product_relative_pct']:+.3f}%**).",
        f"From all five species in postreactor stream4 minus first condensed liquid stream7, "
        f"reconstructed stream5 NH3 = **{record['first_separator_NH3_gas_pred_pct']:.3f} mol%** versus "
        f"reported **{record['first_separator_NH3_gas_observed_pct']:.2f} mol%**.",
        "",
        "| Source-matched control volume | NH3 extent (kmol/h) | Total mole residual / feed | Largest component residual / feed |",
        "|---|---:|---:|---:|",
    ]
    for g in record["balance_groups"]:
        lines.append(f"| {g['boundary']} | {g['NH3_extent_kmol_h']:.2f} | "
                     f"{g['total_balance_abs_pct_feed']:.4f}% | {g['max_species_residual_pct_feed']:.4f}% |")
    lines.extend([
        "",
        "The gas/liquid source table provides stream 7 at **3060 kmol/h, 98.55 mol% NH3**, "
        "and stream 8 at **3678 kmol/h, 99.82 mol% NH3**. The source's 'NH3 liquid, t/h' "
        "values are consistent with **NH3-component** masses. Modeling either entire "
        "liquid stream as pure NH3 is unnecessary and would bias component accounting.",
        "",
        "",
        "Source-matched saturation comparator (published gas-stream temperatures and pressures):",
        "",
        "| Printed gas stream | T (C) | P (bar) | Published NH3 mol% | BASF 1:3 reference mol% | Relative difference |",
        "|---|---:|---:|---:|---:|---:|",
        *[f"| {v['stream']} | {v['temperature_C']:.1f} | {v['pressure_bar_from_printed_gas_stream']:.1f} | "
          f"{v['observed_plant_NH3_molpct']:.2f} | "
          f"{v['BASF_in_domain_1to3_N2H2_vapor_NH3_molpct']:.3f} | "
          f"{v['relative_source_minus_BASF_pct']:+.2f}% |"
          for v in record["source_stage_vle_crossmixture_reference"]],
        "The BASF 1:3 N2/H2 vapor reference is not an EOS validated for the plant inert-bearing mixtures.",
        "",
        f"Stream6 to stream1 pressure rise is **{record['documented_loop_pressure_difference_bar']:.1f} bar** "
        "(source-derived equipment boundary); this script calculates no compressor power, VLE coefficients, "
        "heat exchanger duty or catalyst TOF.",
        "",
        "**Evidence scope:** each of the nine algebraic control volumes uses the same printed "
        "industrial source; close source balance does not establish external model predictive accuracy. "
        "All 64 original engineering validation verdicts remain fixed at 32/64 for NH3-FINAL-1.2.",
        ""
    ])
    report="\n".join(lines)
    (directory/"REPORT.md").write_text(report,encoding="utf-8")
    print(report)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",required=True,type=Path)
    args=parser.parse_args()
    summary=source_observation_reconstruction()
    write_report(summary,args.out_dir)


if __name__=="__main__":
    main()
