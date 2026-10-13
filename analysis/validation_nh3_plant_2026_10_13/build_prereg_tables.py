"""Build the pre-registered comparison tables from reference_values.csv (no model is run here).

Outputs (this folder):
  benchmark_cases.csv     model inputs of every benchmark case (plant operating points, converters)
  benchmark_metrics.csv   every pre-registered comparison: industrial value or range, tolerance rule, source rows
  industrial_windows.csv  members (row, value) of every industrial window used by the revealed-design checks

Every industrial number is read from reference_values.csv by its row_id; the only arithmetic is shown in this file
(gauge -> absolute, per-capacity division, range midpoints for model inputs). Run before run_benchmark.py; the output is
committed with PREREGISTRATION.md, ahead of any model-vs-industry comparison.

    python build_prereg_tables.py
"""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = {r["row_id"]: r for r in csv.DictReader((HERE / "reference_values.csv").open(encoding="utf-8"))}
ATM_GAUGE = 1.01325          # bar added to a gauge pressure (barg -> bar abs)


def v(row_id, quantity=None, field="value"):
    r = REF[row_id]
    if quantity is not None:
        assert r["quantity"] == quantity, (row_id, r["quantity"], quantity)
    return float(r[field])


def rng(row_id, quantity=None):
    r = REF[row_id]
    if quantity is not None:
        assert r["quantity"] == quantity, (row_id, r["quantity"], quantity)
    return float(r["low"]), float(r["high"])


# --- reference temperatures for records without a printed final-bed outlet / separator temperature -----------------
# T_REF: median of the printed final catalyst-bed outlet temperatures (gas leaving the last bed or entering the
# downstream waste-heat boiler) of the Fe records below. Converter 'outlet' temperatures measured after an internal
# feed/effluent exchanger (Liu Table 9.2, Kellogg/ICI converter exits at 280-420 C, US6171570 Table 1) are not used.
T_FINAL_BED = {
    "R0588": v("R0588", "converter_outlet_T_C"),   # Topsoe S-250, S-50 (bed 3) outlet to boiler, 448
    "R0608": v("R0608", "converter_outlet_T_C"),   # Uhde 16 MPa, converter 2 (bed 3) outlet, 442
    "R1540": v("R1540", "converter_outlet_T_C"),   # PFI Kavala Casale converter exit to boiler, 470
    "R0848": v("R0848", "bed_outlet_T_C"),         # Liu Table 9.19 A110 (A), bed 2 outlet, 446
    "R0896": v("R0896", "bed_outlet_T_C"),         # Liu Table 9.19 A110 (B), bed 2 outlet, 444
    "R1400": None,                                 # US4755362 Ex.1 bed 4 outlet (filled below)
    "R1417": None,                                 # US4755362 Ex.2 bed 4 outlet
}
for rid in ("R1400", "R1417"):
    T_FINAL_BED[rid] = v(rid, "bed_outlet_T_C")
T_REF = round(statistics.median(T_FINAL_BED.values()), 1)

# TSEP_REF: median of the printed final (refrigerated) separator temperatures of Fe loops (one value per record).
TSEP_FINAL = {"R1066": -5.0, "R1058": -5.0, "R0015": 0.0, "R0589": -5.0, "R0609": 0.0, "R0561": -23.0, "R0568": 0.0,
              "R0582": -10.0, "R0575": None, "R0554": None, "R1232": -25.0, "R1250": -5.0, "R1542": 1.5, "R1567": -23.0}
for rid in list(TSEP_FINAL):
    if TSEP_FINAL[rid] is None:
        lo, hi = rng(rid, "separator_T_C_range")
        TSEP_FINAL[rid] = (lo + hi) / 2
    else:
        assert abs(v(rid, "separator_T_C") - TSEP_FINAL[rid]) < 1e-9, rid
TSEP_REF = statistics.median(TSEP_FINAL.values())


# --- benchmark cases ------------------------------------------------------------------------------------------------
CASES = []


def case(cid, level, refs, **kw):
    CASES.append(dict(case_id=cid, level=level, ref_rows=" ".join(refs), **kw))


def state_case(cid, refs, P, T, T_basis, Tsep, Tsep_basis, tpd, note=""):
    case(cid, "state", refs, P_bar=P, T_C=T, T_basis=T_basis, Tsep_C=Tsep, Tsep_basis=Tsep_basis, capacity_tpd=tpd,
         note=note)


state_case("TOP140", ["R1061", "R1066", "R1060"], v("R1061", "loop_pressure_bar"), T_REF, "T_REF", -5.0, "R1066", 1000.0,
           "Dybkjaer 1995 Table 6.1, Topsoe 140-bar loop")
state_case("TOP220", ["R1053", "R1058", "R1052"], v("R1053", "loop_pressure_bar"), T_REF, "T_REF", -5.0, "R1058", 1000.0,
           "Dybkjaer 1995 Table 6.1, Topsoe 220-bar loop")
state_case("UHDE188", ["R0003", "R0015", "R0001"], v("R0003", "loop_pressure_bar"), T_REF, "T_REF (bed-3 outlet not printed)",
           0.0, "R0015 (refrigerated No. 2 separator)", 1500.0, "Appl 2011 A2 Fig. 57, Krupp-Uhde 1500 t/d")
state_case("S250", ["R0585", "R0588", "R0589"], v("R0585", "loop_pressure_bar"), v("R0588"), "R0588 (S-50 outlet)", -5.0,
           "R0589", 1000.0, "Liu 2013 Fig. 9.3, Topsoe S-250 loop")
state_case("UHDE160", ["R0606", "R0608", "R0609"], v("R0606", "loop_pressure_bar"), v("R0608"), "R0608 (converter 2 outlet)",
           0.0, "R0609", 1000.0, "Liu 2013 Fig. 9.6, Uhde two-converter loop")
state_case("PFI266", ["R1539", "R1540", "R1542", "R1537"], v("R1539", "loop_pressure_bar") + ATM_GAUGE, v("R1540"),
           "R1540 (exit to boiler)", 1.5, "R1542", v("R1537", "capacity_tpd"), "Orphanides 2006, PFI Kavala Casale 2-bed; 265 barg + 1.013")
state_case("KELLOGG150", ["R1230", "R1232", "R1236"], v("R1230", "loop_pressure_bar"), T_REF, "T_REF", -25.0, "R1232", 1000.0,
           "Hooper 1991, Kellogg single-train 4-bed quench loop")
state_case("BRAUN150", ["R0597", "R0570", "R0575"], v("R0597", "loop_pressure_bar"), T_REF, "T_REF", 1.5,
           "R0575 midpoint of 1-2 C (Liu Table 9.2, same source and process)", 1000.0, "Liu 2013 p. 738 + Table 9.2, Braun 3-converter loop")
state_case("LIU_KELLOGG", ["R0556", "R0561"], v("R0556", "loop_pressure_bar"), T_REF, "T_REF", -23.0, "R0561", 1000.0, "Liu 2013 Table 9.2")
state_case("LIU_TOPSOE", ["R0563", "R0568"], v("R0563", "loop_pressure_bar"), T_REF, "T_REF", 0.0, "R0568", 1000.0, "Liu 2013 Table 9.2")
state_case("LIU_AMV", ["R0577", "R0582"], v("R0577", "loop_pressure_bar"), T_REF, "T_REF", -10.0, "R0582", 1000.0, "Liu 2013 Table 9.2 (Fe-Co catalyst)")
state_case("LIU_SMALL", ["R0549", "R0554"], v("R0549", "loop_pressure_bar"), T_REF, "T_REF", 7.5, "R0554 midpoint of 5-10 C", 1000.0,
           "Liu 2013 Table 9.2, Chinese small/medium plants")
state_case("CASALE250", ["R1366", "R1365", "R1368"], v("R1366", "loop_pressure_bar"), T_REF, "T_REF", TSEP_REF, "TSEP_REF", 1000.0,
           "US 4,372,920 Example 1, Casale axial-radial 1000 t/d")
state_case("LIU93_151", ["R0651", "R0653"], 151.0, T_REF, "T_REF", TSEP_REF, "TSEP_REF", 1000.0,
           "Liu 2013 Table 9.3, syngas + recycle compressor 2.7 -> 15.1 MPa, 1000 t/d")
state_case("UHDE2000", ["R1490", "R1492", "R1493"], sum(rng("R1490", "loop_pressure_bar")) / 2, T_REF, "T_REF", TSEP_REF,
           "TSEP_REF", 2000.0, "Lippmann & Frisse 2004, conventional Uhde 2000 t/d at 190-200 bar (midpoint 195)")
state_case("LIU919A", ["R0841", "R0848", "R0852"], v("R0841", "loop_pressure_bar"), v("R0848"), "R0848 (bed 2 outlet)", TSEP_REF,
           "TSEP_REF", v("R0852", "capacity_tpd"), "Liu 2013 Table 9.19 case (A) A110 (circulator power)")

# converter-level cases (converter.py with measured kinetics)
LIU_Y = dict(yN2=0.228, yH2=0.629, yNH3=v("R0843", "inlet_NH3_molpct") / 100, inerts=v("R0844", "inerts_inlet_molpct") / 100)
case("LIU919A_FWD", "converter_forward", ["R0841", "R0842", "R0843", "R0844", "R0845", "R0847", "R0937", "R0938"],
     P_bar=v("R0841"), inlet_Nm3_h=v("R0842", "inlet_flow_Nm3_h"), **LIU_Y,
     beds=json.dumps([["Fe", v("R0845"), v("R0937")], ["Fe", v("R0847"), v("R0938")]]),
     note="Liu 2013 Table 9.19 case (A) A110 magnetite, S-200 radial 2-bed; inlet H2 62.9 / N2 22.8 % as printed")
case("LIU919B_FWD", "converter_forward", ["R0889", "R0890", "R0891", "R0892", "R0893", "R0895", "R0937", "R0938"],
     P_bar=v("R0889"), inlet_Nm3_h=v("R0890", "inlet_flow_Nm3_h"), **LIU_Y,
     beds=json.dumps([["Fe", v("R0893"), v("R0937")], ["Fe", v("R0895"), v("R0938")]]),
     note="Liu 2013 Table 9.19 case (B) A110 magnetite at 13.40 MPa")
case("LIU919A_INV", "converter_inverse", ["R0845", "R0846", "R0847", "R0848"], P_bar=v("R0841"),
     inlet_Nm3_h=v("R0842"), **LIU_Y,
     beds=json.dumps([["Fe", v("R0845"), v("R0846")], ["Fe", v("R0847"), v("R0848")]]),
     note="model catalyst volume for the printed bed temperature rises")
case("LIU919B_INV", "converter_inverse", ["R0893", "R0894", "R0895", "R0896"], P_bar=v("R0889"),
     inlet_Nm3_h=v("R0890"), **LIU_Y,
     beds=json.dumps([["Fe", v("R0893"), v("R0894")], ["Fe", v("R0895"), v("R0896")]]))
for cid, P_row, F_row, a_row, b_row, I_row in (("TOP140", "R1061", "R1062", "R1063", "R1064", "R1065"),
                                               ("TOP220", "R1053", "R1054", "R1055", "R1056", "R1057")):
    case(f"{cid}_MINVOL", "converter_min_volume", [P_row, F_row, a_row, b_row, I_row], P_bar=v(P_row),
         inlet_Nm3_h=v(F_row), yNH3=v(a_row) / 100, y_out=v(b_row) / 100, inerts=v(I_row) / 100, n_beds=3,
         note="minimum fused-Fe volume (3 adiabatic beds, interbed cooling, 350-530 C) for the printed duty; H2/N2 = 3")
for cid, P_row, sep, inert_row, tpd in (("TOP140", "R1061", -5.0, "R1065", 1000.0), ("TOP220", "R1053", -5.0, "R1057", 1000.0),
                                        ("UHDE188", "R0003", 0.0, "R0013", 1500.0)):
    case(f"{cid}_DESIGN", "converter_design", [P_row, inert_row], P_bar=v(P_row), Tsep_C=sep,
         inerts=v(inert_row) / 100, capacity_tpd=tpd, pattern="FFF",
         note="cost-optimal all-Fe 3-bed adiabatic converter (converter.optimize) at the plant's loop conditions; "
              "benchmark accounting, as the staged-converter base case")
case("KAAP_DESIGN", "converter_design", ["R1528", "R1531", "R0639"], P_bar=v("R1528", "loop_pressure_bar"), Tsep_C=-20.0,
     inerts=0.08, capacity_tpd=1850.0, pattern="FRRR",
     note="cost-optimal KAAP layout (Fe bed 1, Ru/C beds 2-4) at the KAAP loop pressure; separator -20 C and 8 % inerts "
          "are the staged-converter KAAP-type assumptions (no printed KAAP value); benchmark accounting r 95.55 %")


# --- industrial windows ---------------------------------------------------------------------------------------------
WINDOWS = {}


def window(wid, quantity, members, note):
    vals = [m[1] for m in members]
    WINDOWS[wid] = dict(quantity=quantity, members=members, low=min(vals), high=max(vals), note=note)


def pv(rid, q, scale=1.0, add=0.0):
    return (rid, v(rid, q) * scale + add)


window("W_P_FE", "loop_pressure_bar", [
    pv("R1061", "loop_pressure_bar"), pv("R1053", "loop_pressure_bar"), pv("R0003", "loop_pressure_bar"),
    pv("R0182", "loop_pressure_bar"), pv("R1484", "loop_pressure_bar"), ("R1490", sum(rng("R1490")) / 2),
    pv("R1495", "loop_pressure_bar"), pv("R1157", "loop_pressure_bar"), pv("R1158", "loop_pressure_bar"),
    pv("R1230", "loop_pressure_bar"), pv("R1566", "loop_pressure_bar"), pv("R1019", "loop_pressure_bar"),
    pv("R1145", "loop_pressure_bar"), pv("R0570", "loop_pressure_bar"), pv("R1150", "loop_pressure_bar"),
    pv("R0577", "loop_pressure_bar"), pv("R0545", "loop_pressure_bar"), pv("R1153", "loop_pressure_bar"),
    pv("R0187", "loop_pressure_bar"), pv("R0189", "loop_pressure_bar"), pv("R1184", "loop_pressure_bar"),
    pv("R1187", "loop_pressure_bar"), pv("R1192", "loop_pressure_bar"), pv("R1539", "loop_pressure_bar", add=ATM_GAUGE),
    pv("R1387", "loop_pressure_bar"), pv("R1420", "loop_pressure_bar"), pv("R0549", "loop_pressure_bar"),
    pv("R0556", "loop_pressure_bar"), pv("R0563", "loop_pressure_bar"), pv("R0585", "loop_pressure_bar"),
    pv("R0606", "loop_pressure_bar"), pv("R0841", "loop_pressure_bar"), pv("R0760", "loop_pressure_bar"),
    pv("R1092", "loop_pressure_bar"), pv("R1090", "loop_pressure_bar"), pv("R1163", "loop_pressure_bar")],
    "Fe-catalyst synthesis loops of named plants and licensor processes of the single-train era (no Ru, no "
    "concepts or pilots, no pre-1963 multi-line plants, no once-through MP converter); Uhde 190-200 bar at its midpoint")
window("W_P_FE_WORLDSCALE", "loop_pressure_bar", [("R0455", rng("R0455")[0]), ("R0455", rng("R0455")[1]),
                                                  ("R0066", rng("R0066")[0]), ("R0066", rng("R0066")[1]),
                                                  ("R0110", rng("R0110")[0]), ("R0110", rng("R0110")[1])],
       "Appl's statements for world-scale (1200-2000 t/d) plants: 155-190 bar (1999 p. 140; 2011 A2 p. 187) and "
       "170-190 bar (2011 A2 p. 210); union")
window("W_T_FE", "catalyst_T_C",
       [("R1262", rng("R1262", "bed_inlet_T_C_range")[0]), ("R1261", v("R1261", "max_catalyst_T_C"))],
       "Fe catalyst operating window: minimum self-sustaining bed temperature of fresh catalyst (Gramatica & Pernicone "
       "1991 p. 245, 350-360 C, low end) to the maximum allowable catalyst temperature (p. 244, 540 C)")
window("W_TSEP_FE", "separator_T_C", [(k, val) for k, val in TSEP_FINAL.items()] + [pv("R0054", "separator_T_C")],
       "final (refrigerated) separator temperature of Fe loops <= 314 bar, one value per record; ranges at midpoint; "
       "plus Appl's lowest refrigerated level (-25 C)")
window("W_VOL_FE", "catalyst_m3_per_tpd", [
    ("R1368", v("R1368", "catalyst_volume_m3") / v("R1365", "capacity_tpd")),
    ("R1375", rng("R1375", "catalyst_volume_m3_range")[0] / 1000.0), ("R1375", rng("R1375")[1] / 1000.0),
    ("R0821", v("R0821", "catalyst_volume_m3") / 1000.0),
    ("R1549", v("R1549", "catalyst_volume_m3") / v("R1548", "capacity_tpd")),
    ("R1556", v("R1556", "catalyst_volume_m3") / 1100.0),
    ("R0113", float(REF["R0113"]["low"]) / 1500.0),                 # '> 60 m3' for 1500 t/d (lower bound)
    ("R0533", v("R0533", "catalyst_volume_m3") / 1800.0)],           # '> 100 m3' for 1800 t/d (lower bound)
    "installed Fe catalyst per t/d, loops 100-300 bar: Casale 30 m3 / 1000 t/d (250 bar); Kellogg 40-90 m3 / 1000 t/d; "
    "Liu S-200 65.3 m3 / 1000 t/d; Kalol 64.19 m3 / 910 t/d and 75 m3 / 1100 t/d; Appl >60 m3 / 1500 t/d and >100 m3 / "
    "1800 t/d (lower bounds)")
window("W_OUT_FE", "outlet_NH3_molpct", [
    pv("R1064", "outlet_NH3_molpct"), pv("R1056", "outlet_NH3_molpct"), pv("R0012", "outlet_NH3_molpct"),
    pv("R0598", "outlet_NH3_molpct"), pv("R1541", "outlet_NH3_molpct"), ("R1237", rng("R1237")[0]),
    ("R1237", rng("R1237")[1]), pv("R0849", "outlet_NH3_molpct"), pv("R0897", "outlet_NH3_molpct"),
    pv("R1390", "outlet_NH3_molpct"), pv("R1406", "outlet_NH3_molpct"), pv("R1422", "outlet_NH3_molpct"),
    pv("R1430", "outlet_NH3_molpct"), pv("R1554", "outlet_NH3_molpct"), pv("R1560", "outlet_NH3_molpct"),
    pv("R1200", "outlet_NH3_molpct")],
    "converter outlet NH3 of Fe loops (plants, licensor designs and patent examples of real converters)")
window("W_SV_FE", "GHSV_h", [pv("R0555", "other"), pv("R0562", "other"), pv("R0569", "other"), pv("R0576", "other"),
                            pv("R0583", "other"), ("R0046", rng("R0046")[0]), ("R0046", rng("R0046")[1]),
                            ("R0327", rng("R0327")[0]), ("R0327", rng("R0327")[1])],
       "space velocity of Fe converters (Liu Table 9.2; Appl A2 p. 192; Appl 1997 p. 8)")
window("W_BED1_FE", "bed_inlet_T_C", [pv("R0006", "bed_inlet_T_C"), pv("R0845", "bed_inlet_T_C"), pv("R0893", "bed_inlet_T_C"),
                                      pv("R1393", "bed_inlet_T_C"), pv("R1410", "bed_inlet_T_C"), pv("R1247", "bed_inlet_T_C"),
                                      ("R1197", rng("R1197")[0]), ("R1197", rng("R1197")[1])],
       "first-bed inlet temperature of Fe converters (magnetite)")
window("W_P_RU", "loop_pressure_bar", [pv("R1528", "loop_pressure_bar"), pv("R0547", "ru_loop_pressure_bar"),
                                       pv("R0210", "loop_pressure_bar"), pv("R1521", "loop_pressure_bar"),
                                       pv("R1525", "loop_pressure_bar"), pv("R1515", "loop_pressure_bar")],
       "loop pressure of built loops containing Ru catalyst: KAAP grassroots (Trinidad, 89.2-91 bar) and the "
       "Kitimat KAAP retrofit downstream of the magnetite converter (130-138 bar)")


# --- metrics --------------------------------------------------------------------------------------------------------
METRICS = []


def metric(mid, table, cid, quantity, unit, rule, refs, value=None, low=None, high=None, counted=True, note=""):
    METRICS.append(dict(metric_id=mid, table=table, case_id=cid, quantity=quantity, unit=unit, industrial_value=value,
                        industrial_low=low, industrial_high=high, rule=rule, ref_rows=" ".join(refs),
                        counted="yes" if counted else "no", note=note))


REL_IN, REL_OUT, REL_FLOW, REL_POW = "rel:0.20", "rel:0.15", "rel:0.25", "rel:0.30"
FACTOR2, ABS_T = "factor:2", "abs:15"

# Table A: state model at the plant's operating point
metric("A01", "A", "TOP140", "inlet_NH3_molpct", "mol%", REL_IN, ["R1063"], v("R1063"))
metric("A02", "A", "TOP140", "outlet_NH3_molpct", "mol%", REL_OUT, ["R1064"], v("R1064"))
metric("A03", "A", "TOP140", "inlet_Nm3_h", "Nm3/h", REL_FLOW, ["R1062"], v("R1062"))
metric("A04", "A", "TOP220", "inlet_NH3_molpct", "mol%", REL_IN, ["R1055"], v("R1055"))
metric("A05", "A", "TOP220", "outlet_NH3_molpct", "mol%", REL_OUT, ["R1056"], v("R1056"))
metric("A06", "A", "TOP220", "inlet_Nm3_h", "Nm3/h", REL_FLOW, ["R1054"], v("R1054"))
metric("A07", "A", "UHDE188", "inlet_NH3_molpct", "mol%", REL_IN, ["R0010"], v("R0010"))
metric("A08", "A", "UHDE188", "outlet_NH3_molpct", "mol%", REL_OUT, ["R0012"], v("R0012"))
metric("A09", "A", "UHDE188", "inlet_Nm3_h", "Nm3/h", REL_FLOW, ["R0016"], v("R0016"))
metric("A10", "A", "UHDE188", "inlet_to_makeup", "mol/mol", REL_FLOW, ["R0018"], v("R0018"),
       note="converter feed / make-up (incl. recovered H2), Appl's stream table")
metric("A11", "A", "S250", "delta_NH3_molpct", "mol%", REL_OUT, ["R0592"], v("R0592"), note="net NH3 = outlet - inlet")
metric("A12", "A", "UHDE160", "delta_NH3_molpct", "mol%", REL_OUT, ["R0610"], v("R0610"))
metric("A13", "A", "PFI266", "outlet_NH3_molpct", "mol%", REL_OUT, ["R1541"], v("R1541"))
metric("A14", "A", "KELLOGG150", "inlet_NH3_molpct", "mol%", REL_IN, ["R1233"], v("R1233"))
metric("A15", "A", "KELLOGG150", "outlet_NH3_molpct", "mol%", REL_OUT, ["R1237"], low=rng("R1237")[0], high=rng("R1237")[1])
metric("A16", "A", "BRAUN150", "inlet_NH3_molpct", "mol%", REL_IN, ["R0599"], v("R0599"))
metric("A17", "A", "BRAUN150", "outlet_NH3_molpct", "mol%", REL_OUT, ["R0598"], v("R0598"))
metric("A18", "A", "BRAUN150", "delta_NH3_molpct", "mol%", REL_OUT, ["R0571"], v("R0571"))
metric("A19", "A", "BRAUN150", "GHSV_h", "1/h", FACTOR2, ["R0576"], v("R0576"))
metric("A20", "A", "LIU_KELLOGG", "delta_NH3_molpct", "mol%", REL_OUT, ["R0557"], v("R0557"))
metric("A21", "A", "LIU_KELLOGG", "GHSV_h", "1/h", FACTOR2, ["R0562"], v("R0562"))
metric("A22", "A", "LIU_TOPSOE", "delta_NH3_molpct", "mol%", REL_OUT, ["R0564"], low=rng("R0564")[0], high=rng("R0564")[1])
metric("A23", "A", "LIU_TOPSOE", "GHSV_h", "1/h", FACTOR2, ["R0569"], v("R0569"))
metric("A24", "A", "LIU_AMV", "delta_NH3_molpct", "mol%", REL_OUT, ["R0578"], v("R0578"))
metric("A25", "A", "LIU_AMV", "GHSV_h", "1/h", FACTOR2, ["R0583"], v("R0583"))
metric("A26", "A", "LIU_SMALL", "delta_NH3_molpct", "mol%", REL_OUT, ["R0550"], low=rng("R0550")[0], high=rng("R0550")[1])
metric("A27", "A", "LIU_SMALL", "GHSV_h", "1/h", FACTOR2, ["R0555"], v("R0555"))
metric("A28", "A", "CASALE250", "Fe_bed_m3", "m3", FACTOR2, ["R1368"], v("R1368"))
# Table E: loop machinery
metric("E01", "E", "LIU93_151", "fresh_plus_recycle_MW", "MW", REL_POW, ["R0651"], v("R0651"),
       note="syngas + recycle compressor, 2.7 -> 15.1 MPa (model: 30 bar suction)")
metric("E02", "E", "UHDE2000", "fresh_plus_recycle_MW", "MW", REL_POW, ["R1492"], v("R1492"),
       note="synthesis gas compressor of a conventional 2000 t/d Uhde plant")
metric("E03", "E", "LIU919A", "recycle_MW", "MW", REL_POW, ["R0854"], v("R0854"), note="circulator power")
# Table B: converter model
for tag, fid, rows in (("A", "LIU919A_FWD", ("R0846", "R0848", "R0849")), ("B", "LIU919B_FWD", ("R0894", "R0896", "R0897"))):
    n = 1 if tag == "A" else 5
    metric(f"B0{n}", "B", fid, "bed1_T_out_C", "C", ABS_T, [rows[0]], v(rows[0]))
    metric(f"B0{n + 1}", "B", fid, "bed2_T_out_C", "C", ABS_T, [rows[1]], v(rows[1]))
    metric(f"B0{n + 2}", "B", fid, "outlet_NH3_molpct", "mol%", REL_OUT, [rows[2]], v(rows[2]))
    inv = fid.replace("FWD", "INV")
    metric(f"B0{n + 3}", "B", inv, "V_total_m3", "m3", FACTOR2, ["R0937", "R0938"], v("R0937") + v("R0938"),
           note="model volume for the printed bed temperature rises vs installed 18.8 + 46.5 m3")
metric("B09", "B", "TOP220_MINVOL/TOP140_MINVOL", "volume_ratio_220_140", "-", "rel:0.25", ["R1059", "R1067"],
       v("R1059") / v("R1067"), note="Dybkjaer Table 6.1 relative catalyst volume 60 % / 100 %")
for i, cid in enumerate(("TOP140_DESIGN", "TOP220_DESIGN", "UHDE188_DESIGN")):
    out_row = {"TOP140_DESIGN": "R1064", "TOP220_DESIGN": "R1056", "UHDE188_DESIGN": "R0012"}[cid]
    metric(f"B{10 + 3 * i}", "B", cid, "outlet_NH3_molpct", "mol%", REL_OUT, [out_row], v(out_row),
           note="cost-optimal converter outlet NH3 vs the plant's")
    metric(f"B{11 + 3 * i}", "B", cid, "bed1_T_in_C", "C", "window:W_BED1_FE", [])
    metric(f"B{12 + 3 * i}", "B", cid, "V_m3_per_tpd", "m3/(t/d)", "window:W_VOL_FE", [])
metric("B19", "B", "KAAP_DESIGN", "Fe_volume_fraction", "-", "range", ["R0643"], low=0.35, high=0.65,
       note="'the first bed contains an iron catalyst, which accounts for about half the total catalyst' (Liu 2013 "
            "p. 747); 'about half' pre-registered as 0.35-0.65")
metric("B20", "B", "KAAP_DESIGN", "outlet_NH3_molpct", "mol%", REL_OUT, ["R1529", "R0951", "R0644"], low=v("R1529"),
       high=v("R0644"), note="KAAP grassroots 21 % (design) to 21.7 % (Trinidad operation)")
# Table C: revealed design (optimum of the latest model vs industrial windows)
metric("C01", "C", "OPT_FE", "P_bar", "bar", "window:W_P_FE", [], note="(a) Fe optimum pressure, all Fe loops")
metric("C02", "C", "OPT_FE", "P_bar", "bar", "window:W_P_FE_WORLDSCALE", [], note="(a) Fe optimum pressure, world-scale")
metric("C03", "C", "OPT_FE", "T_C", "C", "window:W_T_FE", [], note="(a) Fe optimum reaction temperature")
metric("C04", "C", "OPT_FE", "Tsep_C", "C", "window:W_TSEP_FE", [], note="Fe optimum separator temperature")
metric("C05", "C", "OPT_FE", "Fe_bed_m3_per_tpd", "m3/(t/d)", "window:W_VOL_FE", [], note="Fe optimum catalyst volume")
metric("C06", "C", "OPT_FE", "outlet_NH3_molpct", "mol%", "window:W_OUT_FE", [], note="Fe optimum converter outlet NH3")
metric("C07", "C", "OPT_FE", "GHSV_h", "1/h", "window:W_SV_FE", [], note="Fe optimum space velocity")
metric("C08", "C", "STAGED_ALL", "Ru_upstream_of_Fe_in_any_optimum", "-", "equals:False",
       ["R1531", "R0643", "R1520", "R0212"], note="(b) bed position: industrial Ru beds always downstream of an Fe bed")
metric("C09", "C", "STAGED_90BAR", "Ru_in_optimum_at_12pct", "-", "equals:True", ["R1528", "R1531", "R0639"],
       note="(b) financing: KAAP at ~90 bar was built with Ru downstream of Fe; model at its own 12 %/y rate, "
            "today's Ru price (53,852.5 USD/kg), r 95.55 %")
metric("C10", "C", "STAGED_PRESSURE", "spearman_P_vs_Ru_financing_boundary", "-", "below:-0.5",
       ["R1528", "W_P_RU", "W_P_FE"], note="(b) pressure: the financing rate below which Ru/C enters the optimum falls "
                                           "with loop pressure (Ru only in low-pressure loops)")
metric("C11", "C", "OPT_RUC_0PCT", "P_bar", "bar", "window:W_P_RU", [],
       note="(b) supported Ru/C optimum pressure where it beats Fe (25-y cash flow, 0 %/y, r 95.55 %)")
metric("C12", "C", "OPT_RUC_12PCT", "RuC_minus_Fe_global", "USD/t", "above:0", ["R0947"],
       note="(b) at 12 %/y the global optimum is Fe (industrial majority Fe; Ru in about 10 plants)")
# Table V: separator vapour (sub-model)
metric("V01", "V", "ULLMANN_T5", "median_ratio_model_to_table", "-", "range", ["APPL11_A1 Table 5"], low=0.80, high=1.20,
       note="model y = p_sat(T)/P vs BASF NH3 saturation table, 10-30 MPa, -30..+30 C")

# --- write ---------------------------------------------------------------------------------------------------------


def write(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with (HERE / path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in keys})


def main():
    write("benchmark_cases.csv", CASES)
    write("benchmark_metrics.csv", METRICS)
    wrows = []
    for wid, w in WINDOWS.items():
        for rid, val in w["members"]:
            wrows.append(dict(window_id=wid, quantity=w["quantity"], row_id=rid, value=round(val, 6),
                              window_low=round(w["low"], 6), window_high=round(w["high"], 6), definition=w["note"]))
    write("industrial_windows.csv", wrows)
    print(f"T_REF = {T_REF} C from {T_FINAL_BED}")
    print(f"TSEP_REF = {TSEP_REF} C")
    for wid, w in WINDOWS.items():
        print(f"{wid}: {w['low']:.4g} .. {w['high']:.4g} (n={len(w['members'])})")
    print(len(CASES), "cases,", len(METRICS), "metrics,", sum(m["counted"] == "yes" for m in METRICS), "counted")


if __name__ == "__main__":
    main()
