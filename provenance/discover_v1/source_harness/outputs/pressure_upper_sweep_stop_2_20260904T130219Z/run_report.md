# Run 20260904T130219Z
- Status: **FAIL** (SCENARIO — not canonical)
- Mode: `smoke`
- Model: `NH3-FINAL-1.0`
- Process states: 5136
- Activity ranking: Ru > Os > Fe > Rh > Ir > Co > Re > Mo > Ni > W > Pd > Pt > Cu > Ag > Au
- Feasible economic ranking: Fe > Ru > Os
- Fe / Ru / Os costs: 10.198659047085 / 17.013640776111 / 20.826098171147 USD/t
- Top-3 Spearman: -0.5

## Regression checks
- FAIL — process_state_count: actual=5136 expected=3636
- PASS — raw_global_spearman: actual=0.9107142857142855 expected=0.9107142857142855
- PASS — censored_global_spearman: actual=0.684172319121686 expected=0.684172319121686
- PASS — top3_spearman: actual=-0.5 expected=-0.5
- PASS — Fe_cost_USD_t: actual=10.198659047084616 expected=10.19865904708462
- PASS — Fe_optimum_T_C: actual=400.0 expected=400.0
- PASS — Fe_optimum_P_bar: actual=150.0 expected=150.0
- PASS — Fe_optimum_Tsep_C: actual=30.0 expected=30.0
- FAIL — Ru_cost_USD_t: actual=17.013640776110954 expected=17.59239838038635
- PASS — Ru_optimum_T_C: actual=450.0 expected=450.0
- FAIL — Ru_optimum_P_bar: actual=400.0 expected=300.0
- FAIL — Ru_optimum_Tsep_C: actual=25.0 expected=10.0
- FAIL — Os_cost_USD_t: actual=20.826098171146754 expected=21.32057789728162
- PASS — Os_optimum_T_C: actual=450.0 expected=450.0
- FAIL — Os_optimum_P_bar: actual=400.0 expected=300.0
- FAIL — Os_optimum_Tsep_C: actual=0.0 expected=-15.0
- PASS — activity_order: actual=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au'] expected=['Ru', 'Os', 'Fe', 'Rh', 'Ir', 'Co', 'Re', 'Mo', 'Ni', 'W', 'Pd', 'Pt', 'Cu', 'Ag', 'Au']
- PASS — feasible_metals: actual=['Fe', 'Ru', 'Os'] expected=['Fe', 'Ru', 'Os']
