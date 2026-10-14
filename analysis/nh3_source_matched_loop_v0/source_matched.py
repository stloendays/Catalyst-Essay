#!/usr/bin/env python3
"""NH3-STREAM-V0: primary-source-matched converter and two-stage separator audit.

An observation-constrained, non-calibrated source-flow bookkeeping model.
Sources: frozen literature ledger in analysis/validation_nh3_plant_2026_10_13.
Does NOT write or import the catalyst/process optimizer; DOES NOT rescore 64 cases.

Levels of evidence:
  OBSERVED: printed, image-checked literature rows (or explicit source notes).
  DERIVED: atom/mole conservation calculation with source inputs.
  CONDITIONAL: assumed pure NH3 condensed liquids, approximate normal-gas basis,
               assumed identical pressures of gas/liquid in a common separator,
               and hypothetical stream routing. None proves a unique PFD.

The TOP140/TOP220 tables in two publications share a citation chain: they are
NOT independent plants or validation datasets.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "analysis" / "nh3_industrial_validation_2026_10_14"
sys.path.insert(0, str(AUDIT))
from audit_industrial import PINS, SRC, enforce_pin, rows  # noqa: E402
from diagnose_separator_vle import grid_from_printed_sources, source_interpolation  # noqa: E402

NORM_M3_PER_KMOL = 22.414            # source ledger normal reference, 0 C / 1 atm
MW_NH3_KG_PER_KMOL = 17.031          # source ledger and canonical model basis
R_GAS_J_MOL_K = 8.31446261815324

# These IDs specify which printed data are mutually comparable. They do not
# duplicate or hard-code literature measurements, which are loaded from source.
CONVERTER_CASES = {
    "TOP140": {
        "origin": "DYBKJAER95", "source_class": "aggregate_operating_table",
        "capacity": "R1060", "feed": "R1062", "yin": "R1063",
        "yout": "R1064", "inerts": "R1065",
        "mirrored_ullmann": ("R0024", "R0026", "R0027", "R0028", "R0029"),
    },
    "TOP220": {
        "origin": "DYBKJAER95", "source_class": "aggregate_operating_table",
        "capacity": "R1052", "feed": "R1054", "yin": "R1055",
        "yout": "R1056", "inerts": "R1057",
        "mirrored_ullmann": ("R0032", "R0034", "R0035", "R0036", "R0037"),
    },
    "UHDE188": {
        "origin": "APPL11_A2", "source_class": "stream_resolved_figure_57",
        "capacity": "R0001", "feed": "R0016", "yin": "R0010",
        "yout": "R0012", "inerts": "R0013", "mirrored_ullmann": (),
    },
}


def load_source_ledger() -> dict:
    for name in ("reference_values.csv", "benchmark_cases.csv", "benchmark_metrics.csv"):
        enforce_pin(SRC / name, PINS[name])
    records = rows(SRC / "reference_values.csv")
    lookup = {r["row_id"]: r for r in records}
    if len(lookup) != len(records) or len(records) < 1500:
        raise AssertionError("The frozen 1589-row source ledger changed")
    return lookup


def evidence(db: dict, row_id: str, quantity: str | None = None, *,
             allow_derived: bool = False) -> dict:
    if row_id not in db:
        raise AssertionError(f"Missing registered original row {row_id}")
    r = db[row_id]
    if quantity is not None and r["quantity"] != quantity:
        raise AssertionError(f"Source {row_id} is not the requested {quantity}")
    valid_kinds = ("source_fact", "derived") if allow_derived else ("source_fact",)
    if r["kind"] not in valid_kinds or r["checked_by_image"] != "yes":
        raise AssertionError(f"{row_id} is not an image-checked primary source/traceable derivation")
    return r


def field(db: dict, row_id: str, quantity: str | None = None, *,
          allow_derived: bool = False) -> float:
    r = evidence(db, row_id, quantity, allow_derived=allow_derived)
    if not r["value"]:
        raise AssertionError(f"Missing numeric source value at {row_id}")
    x = float(r["value"])
    if not math.isfinite(x):
        raise AssertionError(f"Nonfinite value at {row_id}")
    return x


def printed_note(db: dict, row_id: str, pattern: str) -> tuple[float, ...]:
    # The note is a separately reviewable source-annotator extraction, not
    # newly verified figure pixels. The literal row ID remains in every report.
    note = evidence(db, row_id)["note"]
    m = re.search(pattern, note)
    if m is None:
        raise AssertionError(f"Source-note pattern not present at {row_id}: {pattern}")
    return tuple(float(v) for v in m.groups())


def kmol_h_from_nm3_h(flow_nm3_h: float) -> float:
    if flow_nm3_h <= 0:
        raise ValueError("Molar inlet flow must be positive")
    return flow_nm3_h / NORM_M3_PER_KMOL


def ammonia_formed_kmol_h(fin: float, y_in: float, y_out: float) -> float:
    """N2 + 3H2 -> 2NH3; the net molar reduction is 1 mol per mol NH3 formed.

    With ideal-gas-flow *moles* at the same normal-volume convention,
      Fout = Fin - Aformed,
      Fin*y_in + Aformed = Fout*y_out.
      Aformed = Fin * (y_out - y_in)/(1 + y_out).
    Holds with inerts unchanged through converter (but not for gas bypass/quench).
    """
    if fin <= 0 or not 0 <= y_in < y_out < 1:
        raise ValueError("Invalid NH3 source converter boundary")
    return fin * (y_out - y_in) / (1.0 + y_out)


def converter_balance(fin: float, yin_pct: float, yout_pct: float) -> dict:
    n = ammonia_formed_kmol_h(fin, yin_pct / 100.0, yout_pct / 100.0)
    fout = fin - n
    return {
        "inlet_total_kmol_h": fin,
        "outlet_total_kmol_h": fout,
        "reacted_N2_kmol_h": n / 2.0,
        "reacted_H2_kmol_h": n * 1.5,
        "new_NH3_kmol_h": n,
        "new_NH3_tpd": n * MW_NH3_KG_PER_KMOL * 24.0 / 1000.0,
        "NH3_in_kmol_h": fin * yin_pct / 100.0,
        "NH3_out_kmol_h": fout * yout_pct / 100.0,
        "stoichiometric_molar_residual_kmol_h": (
            fout * yout_pct / 100.0 - fin * yin_pct / 100.0 - n
        ),
        "scope": "source reactor inlet to source final effluent; assumes no quench split",
    }


def all_converters(db: dict) -> list[dict]:
    out = []
    for case_name, spec in CONVERTER_CASES.items():
        f_nm = field(db, spec["feed"], "inlet_flow_Nm3_h", allow_derived=True)
        cap = field(db, spec["capacity"], "capacity_tpd")
        yin = field(db, spec["yin"], "inlet_NH3_molpct")
        yout = field(db, spec["yout"], "outlet_NH3_molpct")
        inert = field(db, spec["inerts"], "inerts_inlet_molpct", allow_derived=True)
        if case_name == "UHDE188":
            # Ledger R0016's source flow was 28,344 kmol/h, subsequently
            # converted to 635,302 Nm3/h and rounded in the frozen ledger.
            f_printed, = printed_note(
                db, "R0016", r"(\d+)\s*kmol/h\s*\(stream 1\)"
            ) if re.search(r"(\d+)\s*kmol/h\s*\(stream 1\)",
                            evidence(db, "R0016", allow_derived=True)["printed_value_and_unit"]) else (None,)
            # The exact 28,344 value is in R0016's printed field, not the note.
            txt = evidence(db, "R0016", allow_derived=True)["printed_value_and_unit"]
            m = re.search(r"(\d+)\s*kmol/h", txt)
            if m is None:
                raise AssertionError("Missing Uhde printed stream-1 molar flow")
            f_kmol = float(m.group(1))
            if abs(f_kmol - kmol_h_from_nm3_h(f_nm)) > 0.05:
                raise AssertionError("Uhde flow unit conversion inconsistent with source")
        else:
            f_kmol = kmol_h_from_nm3_h(f_nm)
        balance = converter_balance(f_kmol, yin, yout)
        mirror = spec["mirrored_ullmann"]
        if mirror:
            primary = (spec["capacity"], spec["feed"], spec["yin"], spec["yout"], spec["inerts"])
            for first, duplicated in zip(primary, mirror):
                p = field(db, first, allow_derived=True)
                v = field(db, duplicated, allow_derived=True)
                if abs(p - v) > 1e-9:
                    raise AssertionError(f"Literature-mirror consistency changed: {first}/{duplicated}")
            source_relationship = "Dybkjaer95 and Appl11 Table16 are SAME source-derived table, not independent samples"
        else:
            source_relationship = "Ullmann A2 Fig57, distinct measured equipment stream table"
        out.append({
            "case_id": case_name, "source_group": spec["origin"],
            "source_resolution": spec["source_class"],
            "source_row_ids": ";".join([spec[k] for k in ("capacity","feed","yin","yout","inerts")]),
            "reprinted_crossrefs": ";".join(mirror),
            "citation_dependency": source_relationship,
            "normal_flow_Nm3_h": f_nm,
            "inlet_yNH3_pct": yin, "outlet_yNH3_pct": yout,
            "inlet_inerts_pct": inert,
            "published_design_tpd": cap,
            **balance,
            "throughput_vs_nominal_pct": (balance["new_NH3_tpd"] / cap - 1.0) * 100.0,
            "status": "INTERNAL_SOURCE_CONVERTER_BALANCE__NOT_KINETIC_VALIDATION",
        })
    return out


def nh3_liquid_kmol_h(liquid_t_h: float) -> float:
    if liquid_t_h <= 0:
        raise ValueError("Positive liquid mass required")
    # Source reports stage 7 mostly liquid NH3; exact stage-7 composition
    # is not in the ledger. Treating its total mass as pure NH3 is an
    # EXPLICIT approximation, never a validated composition.
    return liquid_t_h * 1000.0 / MW_NH3_KG_PER_KMOL


def stage_liquid_from_gas(f_in: float, y_in_pct: float, y_vap_pct: float) -> float:
    if not 0 <= y_vap_pct < y_in_pct < 100:
        raise ValueError("Separator must decrease gas NH3 concentration")
    return f_in * (y_in_pct / 100.0 - y_vap_pct / 100.0) / (1.0 - y_vap_pct / 100.0)


def uhde_stream_closure(db: dict, conv: dict) -> dict:
    if conv["case_id"] != "UHDE188":
        raise AssertionError("Only the Uhde plant has source-resolved separator streams")
    y5, l7_t_h, stage1_liquid_P_MPa = printed_note(
        db, "R0014", r"stream 5 gas\s+(\d+(?:\.\d+)?)\s*mol% NH3,\s*stream 7 liquid\s+(\d+(?:\.\d+)?)\s*t/h at\s+(\d+(?:\.\d+)?)\s*MPa"
    )
    p6_mpa, y6, f6_note = printed_note(
        db, "R0015", r"\((\d+(?:\.\d+)?)\s*MPa,\s*(\d+(?:\.\d+)?)\s*mol% NH3,\s*(\d+)\s*kmol/h"
    )
    raw10, h211 = printed_note(
        db, "R0017", r"stream 10,\s*(\d+)\s*kmol/h.*stream 11,\s*(\d+)\s*kmol/h"
    )
    makeup12 = field(db, "R0017", "makeup_flow_Nm3_h", allow_derived=True)
    # R0017 derived Nm3/h is rounded to the nearest whole Nm3/h.
    if abs(makeup12 / NORM_M3_PER_KMOL - (raw10 + h211)) > 0.1:
        raise AssertionError("Stream 12 source split violates 10+11 makeup identity")
    if abs(f6_note - conv["inlet_total_kmol_h"]) > 0.1:
        raise AssertionError("Stream 6 and source inlet 1 flow interpretation changed")
    if abs(y6 - conv["inlet_yNH3_pct"]) > 1e-9:
        raise AssertionError("Source stream 6 concentration no longer matches source stream 1")
    p1_bar = field(db,"R0004","loop_pressure_bar")
    p6_bar = p6_mpa * 10.0
    dp_source = field(db, "R0020", "loop_dP_bar", allow_derived=True)
    if abs((p1_bar - p6_bar) - dp_source) > 1e-8:
        raise AssertionError("Source compressor pressure endpoints inconsistent")
    l7 = nh3_liquid_kmol_h(l7_t_h)
    f4 = conv["outlet_total_kmol_h"]
    a4 = conv["NH3_out_kmol_h"]
    f5 = f4-l7
    if f5 <= 0 or a4-l7 < 0:
        raise AssertionError("Source first-separator flow infeasible")
    y5_fwd = 100.0 * (a4-l7) / f5
    l7_inferred = stage_liquid_from_gas(f4, conv["outlet_yNH3_pct"], y5)
    product_t_h = field(db,"R0002","capacity_tpd", allow_derived=True) / 24.0
    if abs(product_t_h - 62.51) > 0.01:
        raise AssertionError("Source product mass flow 62.51 t/h changed")
    l8_tot = nh3_liquid_kmol_h(product_t_h)
    l8_increment = l8_tot-l7
    fuel9 = field(db,"R0023","other")
    # Diagnostic-only totals over an unspecified multi-stage recovery box.
    # Source does not supply a uniquely established network edge ordering.
    unspecified_outflow = (f5 + (raw10+h211)) - (f6_note + l8_increment)
    potential_exit = fuel9 + h211
    gross_formation = conv["new_NH3_kmol_h"]
    apparent_outer_balance = raw10 - gross_formation - l8_tot - fuel9

    # Thermodynamic comparator: BASF 1:3 N2/H2 gas mixture; Uhde feeds have
    # 11.09% CH4+Ar, so agreement does NOT validate actual multicomponent VLE.
    sat = grid_from_printed_sources()
    t5 = field(db,"R0014","separator_T_C")
    t6 = field(db,"R0015","separator_T_C")
    p5_bar = stage1_liquid_P_MPa * 10.0  # liquid stream 7 same-vessel assumption
    basf5 = source_interpolation(sat,t5,p5_bar)
    basf6 = source_interpolation(sat,t6,p6_bar)

    # Counterfactual falsification of an oversimplified topology only:
    # if 8041 kmol/h *NH3-free* make-up were added AFTER a gas stream already
    # at y6=4.18%, the 28344 kmol/h source reactor inlet cannot itself
    # also be 4.18% NH3. No inference about where the actual makeup enters.
    if f6_note <= raw10+h211:
        raise AssertionError("Invalid measured source inlet flow relative to make-up")
    y_if_makeup_after_last_separator = y6*(f6_note-(raw10+h211))/f6_note
    mix_contradiction = conv["inlet_yNH3_pct"] - y_if_makeup_after_last_separator

    # Reversible ideal isothermal *lower bound*, at the tabulated cold gas
    # temperature; NOT actual compressor power, thermal duty or capex.
    min_loop_MW = (
        (f6_note * 1000.0/3600.0)*R_GAS_J_MOL_K*(t6+273.15)
        * math.log(p1_bar/p6_bar)/1e6
    )
    return {
        "plant": "Krupp-Uhde 1500 t/d, Figure 57",
        "source_scope": "two separators, upstream makeup/recovery/purge connections NOT uniquely established",
        "evidence_ledger": {
            "converter_inlet": "R0004;R0010;R0013;R0016",
            "converter_outlet": "R0012",
            "separator_1": "R0014 note (gas stream 5, liquid stream 7)",
            "separator_2": "R0015 note (gas stream 6)",
            "makeup_and_hydrogen_return": "R0017 note (streams 10, 11, 12)",
            "liquid_product": "R0002 (stream 8); R0001 design capacity",
            "fuel_or_purge_recovery": "R0023 (stream 9; includes flash/recovery)",
            "pressure_loss": "R0020 (streams 1 -> 6)",
            "thermal_boundaries": "R0005 vessel entry 295 C; R0006 first bed 390 C; R0008 third bed 401 C; R0009 stream 4 after waste boiler 336 C",
        },
        "source_stage1_vapor_NH3_pct": y5,
        "first_liquid_source_t_h": l7_t_h,
        "first_liquid_inferred_from_gas_t_h": l7_inferred*MW_NH3_KG_PER_KMOL/1000.0,
        "first_liquid_source_basis": "assumed all R0014 51.36 t/h is NH3 (composition not separately provided)",
        "first_stage_gas_NH3_predicted_pct": y5_fwd,
        "first_stage_gas_relative_difference_pct": (y5_fwd/y5 - 1.0)*100.0,
        "first_stage_gas_kmol_h": f5,
        "final_product_source_t_h": product_t_h,
        "final_product_NH3_purity_note_molpct": 99.82,
        "final_product_assumed_pure_tpd": product_t_h*24.0,
        "converter_formation_minus_liquid_product_tpd": conv["new_NH3_tpd"] - product_t_h*24.0,
        "makeup_stream_10_kmol_h": raw10,
        "recovered_H2_stream_11_kmol_h": h211,
        "combined_makeup_stream_12_kmol_h": raw10+h211,
        "fuel_stream_9_kmol_h": fuel9,
        "unassigned_network_residual_kmol_h": unspecified_outflow,
        "recovered_plus_fuel_kmol_h": potential_exit,
        "network_residual_minus_recovered_plus_fuel_kmol_h": unspecified_outflow-potential_exit,
        "raw_makeup_external_closure_residual_kmol_h": apparent_outer_balance,
        "raw_makeup_external_closure_pct": 100.0*apparent_outer_balance/raw10,
        "outer_balance_caveat": "APPROXIMATE; source stream9 fuel can include flash/recovery and stream8 liquid not exactly pure NH3, do not declare full equipment balance proven",
        "stage1_source_T_C":t5,
        "stage1_P_bar_from_same_vessel_liquid_R0014":p5_bar,
        "stage1_P_basis":"R0014 states liquid stream7 at 18.02MPa; assigning this to gas stream5 is a same-separator pressure assumption",
        "stage1_BASF_NH3_pct":basf5,
        "stage1_source_over_BASF_ratio":y5/basf5,
        "stage2_source_T_C":t6,
        "stage2_gas_P_bar_R0015":p6_bar,
        "stage2_source_vapor_NH3_pct":y6,
        "stage2_BASF_NH3_pct":basf6,
        "stage2_source_over_BASF_ratio":y6/basf6,
        "BASF_caveat":"1:3 N2/H2 saturated gas reference; source converter inlet has 11.09 mol% CH4+Ar; not a validated 5-component VLE prediction",
        "source_recycle_pressure_loss_bar": dp_source,
        "model_fixed_recycle_pressure_loss_bar": 3.0, # canonical manifest, not used for modelling
        "cold_gas_isothermal_reversible_compression_MW": min_loop_MW,
        "compressor_bound_caveat":"ideal isothermal reversible work at 0 C; excludes efficiency, stages, heat and make-up compression",
        "counterfactual_after_final_sep_yin_pct":y_if_makeup_after_last_separator,
        "counterfactual_after_final_sep_shortfall_pct_points":mix_contradiction,
        "counterfactual_qualification":"requires all source stream12 NH3-free make-up to be added after measured gas6; contradicts equal gas6/feed1 yNH3, therefore only rules out THAT assumed connection",
        "model_resolution":"STREAM_MATCHED_ACCOUNTING_ONLY__EQUIPMENT_TOPOLOGY_UNRESOLVED",
    }


def write_csv(path: Path, records: list[dict]) -> None:
    if not records:
        raise AssertionError("Empty records")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def build_report(converters: list[dict], uhde: dict) -> str:
    lines = [
        "# NH3-STREAM-V0 | Industrial source-matched loop accounting",
        "",
        "**Evidence status:** original source-internal stoichiometric closure; "
        "NOT an independently validated, source-matched industrial flowsheet model.",
        "",
        "| Distinct source case | Inlet NH3 (%) | Outlet NH3 (%) | NH3 formed (t/d) | Reported design (t/d) | Difference |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for x in converters:
        lines.append(
            f"| {x['case_id']} | {x['inlet_yNH3_pct']:.2f} | {x['outlet_yNH3_pct']:.2f} | "
            f"{x['new_NH3_tpd']:.2f} | {x['published_design_tpd']:.0f} | "
            f"{x['throughput_vs_nominal_pct']:+.2f}% |"
        )
    lines.extend([
        "",
        "TOP140 and TOP220 are two operating columns of the **same Dybkjaer 1995 source**, "
        "also reprinted in Appl 2011 Table 16. They are not multiple independent plant validations.",
        "",
        "## Stream-resolved Uhde Figure 57: internal source closure",
        "",
        f"- Converter chemistry from streams 1 and 4: **{next(x for x in converters if x['case_id']=='UHDE188')['new_NH3_tpd']:.2f} t/d**, "
        f"printed product from stream 8: **{uhde['final_product_assumed_pure_tpd']:.2f} t/d**.",
        f"- From measured first condensed NH3 stream 7 (51.36 t/h), predicted gas stream 5: "
        f"**{uhde['first_stage_gas_NH3_predicted_pct']:.3f}%**, against source **{uhde['source_stage1_vapor_NH3_pct']:.2f}%**.",
        f"- Conversely, using source gas 5 NH3, inferred first condensate: "
        f"**{uhde['first_liquid_inferred_from_gas_t_h']:.3f} t/h** versus reported **51.36 t/h**.",
        f"- Total-source bookkeeping (stream10 raw 7667; stream11 recovered H2 374; "
        f"stream12 8041; stream9 fuel 320 kmol/h): outer molar residual "
        f"**{uhde['raw_makeup_external_closure_pct']:+.3f}%** of raw makeup; conditional on boundary/purity approximations.",
        f"- The unspecified network outflow from stage1 gas + combined makeup to feed6 + "
        f"incremental condensed product is **{uhde['unassigned_network_residual_kmol_h']:.2f} kmol/h**. "
        f"Fuel 9 + recovered H2 11 sum to **{uhde['recovered_plus_fuel_kmol_h']:.2f} kmol/h**. "
        "This agreement is a **consistency clue**, not an identified pipe/recovery order.",
        "",
        "## Source-boundary-matched separator comparison",
        "",
        "| Stage | Temperature | P basis | NH3 source (%) | BASF reference (%) | Relative discrepancy |",
        "|---|---:|---|---:|---:|---:|",
        f"| First (gas 5 / liquid 7) | {uhde['stage1_source_T_C']:.1f} C | "
        f"{uhde['stage1_P_bar_from_same_vessel_liquid_R0014']:.1f} bar (same-vessel liquid assumed) | "
        f"{uhde['source_stage1_vapor_NH3_pct']:.2f} | {uhde['stage1_BASF_NH3_pct']:.3f} | "
        f"{100*(uhde['stage1_source_over_BASF_ratio']-1):+.2f}% |",
        f"| Second (gas 6) | {uhde['stage2_source_T_C']:.1f} C | "
        f"{uhde['stage2_gas_P_bar_R0015']:.1f} bar (stream 6) | "
        f"{uhde['stage2_source_vapor_NH3_pct']:.2f} | {uhde['stage2_BASF_NH3_pct']:.3f} | "
        f"{100*(uhde['stage2_source_over_BASF_ratio']-1):+.2f}% |",
        "",
        "BASF Table 5 is for saturated NH3 in a 1:3 N2:H2 binary diluent. "
        "The actual Uhde plant includes CH4 and Ar; **do not treat small differences here as EOS validation**.",
        "",
        "## Topology falsification and model adequacy",
        "",
        f"If all **8041 kmol/h NH3-free combined makeup** were injected *after* a gas already at "
        f"stream6 yNH3=4.18%, the feed1 concentration would be "
        f"**{uhde['counterfactual_after_final_sep_yin_pct']:.3f}%**, "
        "not the published **4.18%**. This rules out that one oversimplified routing "
        "under its own assumptions. It **does not prove** precisely where real fresh gas, "
        "hydrogen recovery, purge and flash enter the process.",
        "",
        f"Stream6 -> stream1 total documented pressure rise is **{uhde['source_recycle_pressure_loss_bar']:.1f} bar** "
        "(vs 3.0 bar canonical assumption), across a documented system boundary. "
        f"An ideal reversible-isothermal lower-bound estimate at cold stream6 is "
        f"**{uhde['cold_gas_isothermal_reversible_compression_MW']:.3f} MW**; "
        "this is NOT a prediction of industrial compressor duty.",
        "",
        "**Engineering-blocking unknowns:** exact piping and injection points, "
        "separator gas-liquid split pressure/enthalpy, purge/recovery composition, "
        "mixture VLE with CH4/Ar, actual reactor multiple-bed in/out temperatures, "
        "catalyst pellets, pressure drops and compressor operating map.",
        "",
        "No catalyst costs, rank order, backward-design boundaries, original 64-case scores or frozen traces changed.",
        "",
    ])
    return "\n".join(lines)


def run(out_dir: Path) -> dict:
    db = load_source_ledger()
    converters = all_converters(db)
    uhdecase = next(r for r in converters if r["case_id"] == "UHDE188")
    uhde = uhde_stream_closure(db, uhdecase)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "converter_source_3.csv", converters)
    (out_dir / "uhde_stream_closure.json").write_text(
        json.dumps(uhde, indent=2, ensure_ascii=False)+"\n", encoding="utf-8"
    )
    overall = {
        "method": "NH3-STREAM-V0",
        "model_label": "SOURCE_CONDITIONED_ACCOUNTING_NOT_INDUSTRIAL_SIMULATOR",
        "registered_benchmark_unchanged": "NH3-FINAL-1.2 32/64",
        "distinct_source_groups": 2,
        "converter_operating_cases": 3,
        "plant_stream_resolved_cases": 1,
        "reprints_not_independent_samples": "Appl 2011 Table16 is a reprint of Dybkjaer95 Table6.1",
        "converter_cases": converters,
        "uhde": uhde,
    }
    (out_dir / "summary.json").write_text(json.dumps(overall,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report = build_report(converters, uhde)
    (out_dir / "REPORT.md").write_text(report,encoding="utf-8")
    print(report)
    return overall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
