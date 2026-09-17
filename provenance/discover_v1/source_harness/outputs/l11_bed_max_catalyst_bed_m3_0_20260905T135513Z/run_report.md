# Run 20260905T135513Z
- Status: **PASS** (SCENARIO — not canonical)
- Mode: `smoke`
- Model: `NH3-FINAL-1.1`
- Process states: 14136
- Activity ranking: Ru > Os > Fe > Rh > Ir > Co > Re > Mo > Ni > W > Pd > Pt > Cu > Ag > Au
- Feasible economic ranking: Fe > Ru > Os
- Fe / Ru / Os costs: 15.291704676621 / 22.030594787811 / 25.831797256133 USD/t
- Top-3 Spearman: -0.5

## Regression checks
- PASS — process_state_count: actual=14136 expected=14136
- PASS — raw_global_spearman: actual=0.9285714285714284 expected=0.9285714285714284
- PASS — censored_global_spearman: actual=0.684172319121686 expected=0.684172319121686
- PASS — top3_spearman: actual=-0.5 expected=-0.5
- PASS — Fe_cost_USD_t: actual=15.291704676621144 expected=15.291704676621144
- PASS — Fe_optimum_T_C: actual=425.0 expected=425.0
- PASS — Fe_optimum_P_bar: actual=180.0 expected=180.0
- PASS — Fe_optimum_Tsep_C: actual=30.0 expected=30.0
- PASS — Ru_cost_USD_t: actual=22.03059478781101 expected=22.03059478781101
- PASS — Ru_optimum_T_C: actual=450.0 expected=450.0
- PASS — Ru_optimum_P_bar: actual=425.0 expected=425.0
- PASS — Ru_optimum_Tsep_C: actual=25.0 expected=25.0
- PASS — Os_cost_USD_t: actual=25.83179725613286 expected=25.83179725613286
- PASS — Os_optimum_T_C: actual=450.0 expected=450.0
- PASS — Os_optimum_P_bar: actual=425.0 expected=425.0
- PASS — Os_optimum_Tsep_C: actual=0.0 expected=0.0
- PASS — activity_order: actual=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au'] expected=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au']
- PASS — feasible_metals: actual=['Fe', 'Ru', 'Os'] expected=['Fe', 'Ru', 'Os']
