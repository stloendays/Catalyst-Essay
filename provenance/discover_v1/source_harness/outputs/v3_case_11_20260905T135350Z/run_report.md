# Run 20260905T135350Z
- Status: **FAIL** (SCENARIO — not canonical)
- Mode: `smoke`
- Model: `NH3-FINAL-1.1`
- Process states: 14136
- Activity ranking: Ru > Os > Fe > Rh > Ir > Co > Re > Mo > Ni > W > Pd > Pt > Cu > Ag > Au
- Feasible economic ranking: Fe > Ru > Os
- Fe / Ru / Os costs: 15.362066645383 / 23.459778094003 / 27.448768857713 USD/t
- Top-3 Spearman: -0.5

## Regression checks
- PASS — process_state_count: actual=14136 expected=14136
- FAIL — raw_global_spearman: actual=0.9107142857142855 expected=0.9285714285714284
- PASS — censored_global_spearman: actual=0.684172319121686 expected=0.684172319121686
- PASS — top3_spearman: actual=-0.5 expected=-0.5
- FAIL — Fe_cost_USD_t: actual=15.362066645383493 expected=15.291704676621144
- PASS — Fe_optimum_T_C: actual=425.0 expected=425.0
- PASS — Fe_optimum_P_bar: actual=180.0 expected=180.0
- PASS — Fe_optimum_Tsep_C: actual=30.0 expected=30.0
- FAIL — Ru_cost_USD_t: actual=23.45977809400296 expected=22.03059478781101
- PASS — Ru_optimum_T_C: actual=450.0 expected=450.0
- PASS — Ru_optimum_P_bar: actual=425.0 expected=425.0
- FAIL — Ru_optimum_Tsep_C: actual=15.0 expected=25.0
- FAIL — Os_cost_USD_t: actual=27.448768857712597 expected=25.83179725613286
- PASS — Os_optimum_T_C: actual=450.0 expected=450.0
- FAIL — Os_optimum_P_bar: actual=420.0 expected=425.0
- FAIL — Os_optimum_Tsep_C: actual=-10.0 expected=0.0
- PASS — activity_order: actual=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au'] expected=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au']
- PASS — feasible_metals: actual=['Fe', 'Ru', 'Os'] expected=['Fe', 'Ru', 'Os']
