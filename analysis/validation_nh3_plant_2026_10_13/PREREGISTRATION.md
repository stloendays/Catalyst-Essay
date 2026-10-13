# Pre-registration: the latest NH3 plant model against industrial ammonia plants (2026-10-13)

Committed before any model-versus-industry comparison is run. The results commit must come after this commit, and the
metrics, tolerances, windows and pass/fail rules below are not changed after results are seen. If a defect is found
in the code that computes a model value, the fix and its effect are reported in the README; the rules stay as written.

## 1. Model under test

"Latest model" = NH3-FINAL-1.1 process states with the measured fused-Fe (Dyson & Simon 1968) and Ru/C (Rossetti et al.
2006) rate laws and plug-flow sizing, as implemented in `analysis/nh3_staged_converter_2026_10_12/` (`kinetics.py`,
`kinetics_swap.py`, `converter.py`, `parameters.yaml`). It is imported unchanged (`nh3_model.py`, `converter_sim.py`).
Before any run, `test_reproduce.py` must reproduce the frozen descriptor-kinetics optima Fe 15.291705 / Ru 22.030595
USD/t (to 1e-9) and the measured-kinetics Fe optimum 15.578802 USD/t at 425 °C, 170 bar, 30 °C (to 1e-5).

Model levels:

| Level | What is run | Used in |
|---|---|---|
| state | NH3-FINAL-1.1 loop state at the plant's (P, T, T_sep) and capacity: H2/N2 = 3, no inerts, per-pass conversion 0.8 of the loop equilibrium at T, recycle NH3 = p_sat(T_sep)/P, compression from 30 bar, 3-bar recycle rise; Fe bed by isothermal plug flow (Dyson–Simon) | Table A, E |
| converter_forward | `converter.py` primitives: the plant's inlet gas (P, flow, H2, N2, NH3, inerts as printed) through its adiabatic beds at the printed bed inlet temperatures and installed volumes; intrinsic rate (effectiveness 1) | Table B |
| converter_inverse | same, catalyst volume the model needs for the printed bed inlet/outlet temperatures | Table B |
| converter_min_volume | minimum fused-Fe volume (3 adiabatic beds with interbed cooling, bed temperatures 350–530 °C) that delivers the printed duty (flow, inlet/outlet NH3, inerts, H2/N2 = 3) | Table B (B09) |
| converter_design | `converter.optimize` cost-optimal converter (bed inlet temperatures and extents) at the plant's P, T_sep, inerts and capacity; benchmark accounting r 95.55 % (the staged-converter base case) | Table B |
| optimum | `kinetics_swap.evaluate` (NH3-FINAL-1.1 states, plug flow, measured rates): Fe optimum, supported Ru/C optimum at 25-y cash flow 0 and 12 %/y; committed staged-converter outputs (`arrangements.csv`, `sensitivities.csv`, `boundary_pressure.csv`, `boundary_summary.json`) for the Fe/Ru staging checks | Table C |

Secondary column (reported, not counted): PR #77, branch `analysis/nh3-final-1-2-candidate-20261013`,
`gb_fugacity_pair.GBFugacityReaction` (Gillespie–Beattie standard Gibbs energy with Newton–Cooper reaction fugacities,
50–300 bar), read with `git show` and imported unchanged. It changes the loop states only; converter-level and staged
results are the same as the primary column.

## 2. Industrial data

`reference_values.csv`: 1,589 values from 41 sources (Ullmann "Ammonia" 1–3, Appl 1999 and 1997, Dybkjaer 1995 in
Nielsen, Hooper / Gramatica & Pernicone / Tennison in Jennings 1991, Liu 2013, Kirk-Othmer, Rouwenhorst 2021, Brown
2014, Tripodi 2021, licensor patents, IFA technical-conference papers, the thyssenkrupp Uhde brochure, KBR revamp list,
Johnson Matthey slides). Each value has a printed-page / PDF-page / table or figure locator and a verbatim snippet;
`kind` is `source_fact` (1,295), `derived` (170, arithmetic shown), `secondary` (104), `figure_reading` (11) or
`web_summary` (9, read through a summariser; not used in any metric or window). Tables and figures were read from
rendered page images. Nothing is from memory.

`build_prereg_tables.py` reads every industrial number from that file by `row_id` and writes
`benchmark_cases.csv` (model inputs), `benchmark_metrics.csv` (the 64 comparisons) and `industrial_windows.csv`
(members of every window). The only arithmetic is in that script.

Fixed inputs where a record does not print them:

- **T_REF = 448 °C**: median of the printed final catalyst-bed outlet temperatures (gas leaving the last bed or entering
  the downstream boiler) of seven Fe records: 448, 442, 470, 446, 444, 460.3, 459.5 °C. Converter "outlet"
  temperatures taken after an internal feed/effluent exchanger (280–420 °C in Liu Table 9.2) are not used.
- **TSEP_REF = −5 °C**: median of the printed final separator temperatures of 14 Fe-loop records.
- The state model has no inerts; inerts enter only the converter levels, as printed.

## 3. Tolerance rules

| Rule | Pass if | Applied to |
|---|---|---|
| rel:0.20 | \|model − plant\| ≤ 20 % of plant | converter inlet NH3 |
| rel:0.15 | ≤ 15 % | outlet NH3, net NH3 (outlet − inlet), KAAP outlet |
| rel:0.25 | ≤ 25 % | inlet flow, inlet/make-up ratio, volume ratio 220/140 bar |
| rel:0.30 | ≤ 30 % | compressor power |
| factor:2 | 0.5 ≤ model/plant ≤ 2 | catalyst volume, space velocity |
| abs:15 | \|model − plant\| ≤ 15 K | bed outlet temperatures |
| range | low ≤ model ≤ high | stated |
| plant range with rel:x | low·(1 − x) ≤ model ≤ high·(1 + x) | range-valued plant numbers |
| window:W | window low ≤ model ≤ window high (inclusive) | Table C, design checks |
| equals / below / above | as written | Table C (b) |

A model case that returns no feasible state counts as a fail.

## 4. Industrial windows (from `industrial_windows.csv`)

| Window | Low | High | n | Definition |
|---|---:|---:|---:|---|
| W_P_FE | 78.5 bar | 343.2 bar | 36 | Fe loops of named plants and licensor processes, single-train era; no Ru, concepts, pilots |
| W_P_FE_WORLDSCALE | 155 bar | 190 bar | 6 | Appl: world-scale 1200–2000 t/d plants, 155–190 and 170–190 bar (union) |
| W_T_FE | 350 °C | 540 °C | 2 | minimum self-sustaining bed temperature of fresh Fe to maximum allowable catalyst temperature (Gramatica & Pernicone 1991) |
| W_TSEP_FE | −25 °C | 7.5 °C | 15 | final separator temperature of Fe loops (ranges at midpoint) |
| W_VOL_FE | 0.030 | 0.090 m³/(t/d) | 8 | installed Fe catalyst per t/d, loops 100–300 bar |
| W_OUT_FE | 10 mol% | 21 mol% | 16 | converter outlet NH3 of Fe loops |
| W_SV_FE | 7,600 h⁻¹ | 35,000 h⁻¹ | 9 | Fe converter space velocity |
| W_BED1_FE | 340 °C | 420 °C | 8 | first-bed inlet temperature of Fe converters |
| W_P_RU | 89.2 bar | 137.9 bar | 6 | loops built with Ru catalyst: KAAP grassroots (Trinidad) and the Kitimat KAAP retrofit |

## 5. Pre-registered revealed-design predictions

**(a) Fe.** The model's unconstrained measured-kinetics Fe optimum (NH3-FINAL-1.1 states, plug flow; 425 °C, 170 bar,
30 °C, 25.6 m³, as published in PR #75) lies inside the industrial Fe-loop window: pressure inside W_P_FE (C01) and
inside the world-scale window W_P_FE_WORLDSCALE (C02); reaction temperature inside W_T_FE (C03). Also checked: its
separator temperature (C04), catalyst volume (C05), converter outlet NH3 (C06) and space velocity (C07) inside the
corresponding windows.

**(b) Ru/C.** Industrial deployment: Ru only in KAAP-type loops at about 90 bar (grassroots) or as a retrofit at the
host Fe loop pressure (Kitimat, 130–138 bar), always in beds downstream of a magnetite bed; Fe in the large majority of
plants. Pre-registered checks:

- C08 bed position: in no staged-converter optimum (any loop, accounting, bed mode, sensitivity, 3- or 4-bed) is a Ru/C
  bed upstream of an Fe bed.
- C09 financing: at today's Ru price (53,852.5 USD/kg), 95.55 % recovery and the model's own 12 %/y rate, the 90-bar
  KAAP-type loop optimum contains Ru/C (the KAAP plants were built with Ru).
- C10 pressure: the financing rate below which Ru/C enters the staged optimum falls with loop pressure (Spearman ρ
  < −0.5 over the 60–200 bar sweep at −20 °C, r 95.55 %, today's price).
- C11 where Ru/C beats Fe as a single catalyst (25-y cash flow, 0 %/y, r 95.55 %), its optimum pressure lies in W_P_RU.
- C12 at 12 %/y (25-y cash flow, r 95.55 %) the global optimum is Fe (supported Ru/C − Fe > 0).
- B19/B20 the cost-optimal KAAP layout (Fe bed 1, Ru/C beds 2–4) at 89.2 bar has an Fe share of the catalyst volume of
  0.35–0.65 ("about half") and an outlet NH3 of 21–21.7 % (±15 %).

The model-side optimum locations of (a) and of C08–C11 were already public in PR #75 when this file was written; the
industrial windows were fixed from the data by the rules in section 4, not tuned to them.

## 6. Comparisons (64, all counted)

| ID | Case | Model quantity | Industrial | Rule | Source rows |
|---|---|---|---|---|---|
| A01 | TOP140 | inlet_NH3_molpct | 4.1 mol% | rel:0.20 | R1063 |
| A02 | TOP140 | outlet_NH3_molpct | 17.1 mol% | rel:0.15 | R1064 |
| A03 | TOP140 | inlet_Nm3_h | 500,000 Nm3/h | rel:0.25 | R1062 |
| A04 | TOP220 | inlet_NH3_molpct | 3.8 mol% | rel:0.20 | R1055 |
| A05 | TOP220 | outlet_NH3_molpct | 19.9 mol% | rel:0.15 | R1056 |
| A06 | TOP220 | inlet_Nm3_h | 407,000 Nm3/h | rel:0.25 | R1054 |
| A07 | UHDE188 | inlet_NH3_molpct | 4.18 mol% | rel:0.20 | R0010 |
| A08 | UHDE188 | outlet_NH3_molpct | 19.67 mol% | rel:0.15 | R0012 |
| A09 | UHDE188 | inlet_Nm3_h | 635,302 Nm3/h | rel:0.25 | R0016 |
| A10 | UHDE188 | inlet_to_makeup | 3.52 mol/mol | rel:0.25 | R0018 |
| A11 | S250 | delta_NH3_molpct | 16.5 mol% | rel:0.15 | R0592 |
| A12 | UHDE160 | delta_NH3_molpct | 19.3 mol% | rel:0.15 | R0610 |
| A13 | PFI266 | outlet_NH3_molpct | 19 mol% | rel:0.15 | R1541 |
| A14 | KELLOGG150 | inlet_NH3_molpct | 2 mol% | rel:0.20 | R1233 |
| A15 | KELLOGG150 | outlet_NH3_molpct | 10–12 mol% | rel:0.15 | R1237 |
| A16 | BRAUN150 | inlet_NH3_molpct | 4 mol% | rel:0.20 | R0599 |
| A17 | BRAUN150 | outlet_NH3_molpct | 21 mol% | rel:0.15 | R0598 |
| A18 | BRAUN150 | delta_NH3_molpct | 17 mol% | rel:0.15 | R0571 |
| A19 | BRAUN150 | GHSV_h | 7,600 1/h | factor:2 | R0576 |
| A20 | LIU_KELLOGG | delta_NH3_molpct | 10 mol% | rel:0.15 | R0557 |
| A21 | LIU_KELLOGG | GHSV_h | 10,000 1/h | factor:2 | R0562 |
| A22 | LIU_TOPSOE | delta_NH3_molpct | 10–12.5 mol% | rel:0.15 | R0564 |
| A23 | LIU_TOPSOE | GHSV_h | 12,000 1/h | factor:2 | R0569 |
| A24 | LIU_AMV | delta_NH3_molpct | 13 mol% | rel:0.15 | R0578 |
| A25 | LIU_AMV | GHSV_h | 8,000 1/h | factor:2 | R0583 |
| A26 | LIU_SMALL | delta_NH3_molpct | 8–10 mol% | rel:0.15 | R0550 |
| A27 | LIU_SMALL | GHSV_h | 30,000 1/h | factor:2 | R0555 |
| A28 | CASALE250 | Fe_bed_m3 | 30 m3 | factor:2 | R1368 |
| E01 | LIU93_151 | fresh_plus_recycle_MW | 13 MW | rel:0.30 | R0651 |
| E02 | UHDE2000 | fresh_plus_recycle_MW | 26.6 MW | rel:0.30 | R1492 |
| E03 | LIU919A | recycle_MW | 1.441 MW | rel:0.30 | R0854 |
| B01 | LIU919A_FWD | bed1_T_out_C | 489 °C | abs:15 | R0846 |
| B02 | LIU919A_FWD | bed2_T_out_C | 446 °C | abs:15 | R0848 |
| B03 | LIU919A_FWD | outlet_NH3_molpct | 14.31 mol% | rel:0.15 | R0849 |
| B04 | LIU919A_INV | V_total_m3 | 65.3 m3 | factor:2 | R0937 R0938 |
| B05 | LIU919B_FWD | bed1_T_out_C | 490 °C | abs:15 | R0894 |
| B06 | LIU919B_FWD | bed2_T_out_C | 444 °C | abs:15 | R0896 |
| B07 | LIU919B_FWD | outlet_NH3_molpct | 14.94 mol% | rel:0.15 | R0897 |
| B08 | LIU919B_INV | V_total_m3 | 65.3 m3 | factor:2 | R0937 R0938 |
| B09 | TOP220_MINVOL / TOP140_MINVOL | volume_ratio_220_140 | 0.60 | rel:0.25 | R1059 R1067 |
| B10 | TOP140_DESIGN | outlet_NH3_molpct | 17.1 mol% | rel:0.15 | R1064 |
| B11 | TOP140_DESIGN | bed1_T_in_C | W_BED1_FE | window | |
| B12 | TOP140_DESIGN | V_m3_per_tpd | W_VOL_FE | window | |
| B13 | TOP220_DESIGN | outlet_NH3_molpct | 19.9 mol% | rel:0.15 | R1056 |
| B14 | TOP220_DESIGN | bed1_T_in_C | W_BED1_FE | window | |
| B15 | TOP220_DESIGN | V_m3_per_tpd | W_VOL_FE | window | |
| B16 | UHDE188_DESIGN | outlet_NH3_molpct | 19.67 mol% | rel:0.15 | R0012 |
| B17 | UHDE188_DESIGN | bed1_T_in_C | W_BED1_FE | window | |
| B18 | UHDE188_DESIGN | V_m3_per_tpd | W_VOL_FE | window | |
| B19 | KAAP_DESIGN | Fe_volume_fraction | 0.35–0.65 | range | R0643 |
| B20 | KAAP_DESIGN | outlet_NH3_molpct | 21–21.7 mol% | rel:0.15 | R1529 R0951 R0644 |
| C01 | OPT_FE | P_bar | W_P_FE | window | |
| C02 | OPT_FE | P_bar | W_P_FE_WORLDSCALE | window | |
| C03 | OPT_FE | T_C | W_T_FE | window | |
| C04 | OPT_FE | Tsep_C | W_TSEP_FE | window | |
| C05 | OPT_FE | Fe_bed_m3_per_tpd | W_VOL_FE | window | |
| C06 | OPT_FE | outlet_NH3_molpct | W_OUT_FE | window | |
| C07 | OPT_FE | GHSV_h | W_SV_FE | window | |
| C08 | STAGED_ALL | Ru/C upstream of Fe in any optimum | false | equals | R1531 R0643 R1520 R0212 |
| C09 | STAGED_90BAR | Ru/C in the 90-bar optimum at 12 %/y | true | equals | R1528 R1531 R0639 |
| C10 | STAGED_PRESSURE | Spearman ρ(P, Ru financing boundary) | < −0.5 | below | R1528 |
| C11 | OPT_RUC_0PCT | P_bar | W_P_RU | window | |
| C12 | OPT_RUC_12PCT | supported Ru/C − Fe (USD/t) | > 0 | above | R0947 |
| V01 | ULLMANN_T5 | median model/table separator-vapour NH3, 10–30 MPa, −30…+30 °C | 0.80–1.20 | range | Appl 2011 A1 Table 5 |

Model quantities: `inlet_NH3_molpct`, `outlet_NH3_molpct` and `delta_NH3_molpct` are the converter inlet, outlet and
their difference; `inlet_to_makeup` is converter feed / make-up gas (mol/mol); `GHSV_h` is converter inlet Nm³/h per
m³ of model Fe bed; `*_MW` are the model's compression powers at the case capacity (MWh/t × t/d / 24).

## 7. Verdict

Reported as k of 64 counted comparisons passing, with the count per table (A loop states, E machinery, B converters,
C revealed design, V separator vapour). Every failing check is listed in the README and the PR body. Reported but not
counted: the PR #77 column; T_REF ± 25 °C; Fe effectiveness 0.5 in the forward converter runs; the staged checks at
other Ru prices.
