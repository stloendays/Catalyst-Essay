# NH3-FINAL-1.1 provenance closure validation

Status: **PROVENANCE_VALIDATED_READY_FOR_LOCK**

Checked at: `2026-09-10T08:12:02.846513+00:00`

This validation is provenance-only; no scientific model was executed.

## Core source paths

- `provenance/nh3_final_1_1/source_harness/configs/nh3_final.yaml`: present
- `provenance/nh3_final_1_1/source_harness/PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md`: present
- `provenance/nh3_final_1_1/source_harness/NH3_FINAL_1_1_PRESSURE_CAPEX_REPORT_2026-09-05.md`: present
- `provenance/nh3_final_1_1/source_harness/audits/audit_pressure_capex_handcalc_2026-09-05.py`: present
- `provenance/nh3_final_1_1/source_harness/PROMOTE_NH3_FINAL_1_1_CHECKLIST.md`: present
- `provenance/nh3_final_1_1/source_harness/NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md`: present
- `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/closure`: present

## Manifest integrity

- manifest present: True
- listed files: 28
- missing listed files: 0
- hash mismatches: 0

## Canonical anchor check

- Fe_cost: PASS
- Ru_cost: PASS
- Os_cost: PASS
- top3_spearman: PASS
- full15_raw_spearman: PASS
- Fe_feasibility: PASS
- Fe_top1_survival: PASS
- Fe_top3_actionable: PASS
- Ru_break_even: PASS
- headroom_673K: PASS
- headroom_process_max: PASS
- strict_scaling_Ru_min_cost: PASS
- strict_scaling_E_N: PASS

## F1-F6 source-data classes

- F1_ranking_cost: 8 candidate data file(s)
- F2_rolling_rank: 5 candidate data file(s)
- F3_uncertainty_MC: 9 candidate data file(s)
- F4_operating_envelope: 5 candidate data file(s)
- F5_backward_break_even: 5 candidate data file(s)
- F6_scaling_reachability: 5 candidate data file(s)

## F1-F6 figure map

- F1: outputs/nh3_final_20260905T134204Z/figures/F1_ranking_propagation_1_1.svg
- F2: outputs/nh3_final_20260905T134204Z/figures/F2_rolling_topk_1_1.svg
- F3: outputs/nh3_final_20260905T134204Z/figures/F3_mc_feasibility_1_1.svg
- F4: outputs/nh3_final_20260905T134204Z/figures/F4_pressure_envelopes_1_1.svg
- F5: outputs/nh3_final_20260905T134204Z/figures/F5_ru_breakeven_1_1.svg
- F6: outputs/nh3_final_20260905T134204Z/figures/F6_scaling_reachability_1_1.svg
