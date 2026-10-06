# Figure 2 — published laboratory leaderboards against plant-cost leaderboards

Within published comparisons, the paper's own leader is often not the plant-cost leader, in methanol and in ammonia.
183 × 150 mm, six panels: `FigField.{svg,pdf,png}`. In the manuscript numbering of 2026-10-07 this is Fig. 2. Panels a, d
and e come from the agent figure `../fig6` (its panels a, d, e); that directory is left unchanged.

| Panel | Content | Source |
|---|---|---|
| a | ACSA workflow: publications → extraction → self-check → full chain (bound first) → leaderboards | schematic |
| b | methanol: share of the 83 within-paper comparisons (44 papers) whose paper leader is not the plant-cost leader, by leaderboard metric (STY, X·S, X, S_MeOH; recycled CO), with the inert-CO marker on STY and the paper-cluster bootstrap 95 % CI on STY | `analysis/meoh_literature_inversion_2026_10_05/summary.json` (`primary`, `variants.leaderboard_*`, `variants.inert_opt`); CI: `analysis/meoh_main_result_stats_2026_10_06/summary.json` (`cluster_bootstrap.fraction_ci95`) |
| c, left | ammonia: share of the 124 within-paper comparisons (28 papers of the 30-paper set) with a different winner, ranked by rate per g catalyst (the papers' basis), per g metal, and per g catalyst with 90 % Ru recovery; bars are paper-cluster bootstrap 95 % CIs | `analysis/nh3_field_2026_10_06/summary.json` (`primary`, `variants.per_g_metal_leaderboard`, `variants.Ru_recovery_90pct`, `bootstrap_papers`) |
| c, right | what the 45 mismatched ammonia comparisons differ by, with papers and median regret; for "different metal", how many the same-support Fe catalyst wins | `summary.json` (`primary.mismatch_kinds`); plant-winner metal from `group_metrics.csv` + `candidates.csv` |
| d | methanol group Re/TiO2, 100 bar: STY against net plant cost, marker area ∝ CH4 selectivity | `analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv` (group `10.1021/acscatal.5c05984 \| 100 bar \| H2/CO2 4 \| 10 NL/g/h`) |
| e | methanol group Cu/Al2O3 (K, Ba), 10 MPa | same file (group `10.1039/c2cy20604h \| 100 bar \| H2/CO2 3.8 \| 10.6 NL/g/h`) |
| f | ammonia group Ru, Fe, Co on BaTiO3−xHx at 5 MPa (Tang et al. 2018): rate per g catalyst against plant cost | `analysis/nh3_field_2026_10_06/candidates.csv` (group `10.1002/aenm.201801772 \| 400 C \| 5 MPa \| H2/N2 3 \| 6.6e+04 mL/g/h`), regret from `group_metrics.csv` |

Every number is read from these files; the renderer asserts that the methanol point estimate in the two summaries agrees
(33/83), that the ammonia mismatch kinds sum to the 45 mismatched groups, and that the panel-f leaders are those of
`group_metrics.csv`.

Note on panel c: of the 14 "different metal" groups, the same-support Fe catalyst is the plant winner in 12 (Tang 2018
and Kitano 2019); in the other 2 (Inoue 2019, 340 and 400 °C) Ru/MgO beats the paper's Co/C12A7:e⁻.

Build: `D:\Tools\pur_bridge_env\Scripts\python.exe make_fig_field.py` → `FigField.{svg,pdf,png}`.
Source Data: `source_data/SourceData_Fig2.xlsx` (`tools/build_source_data.py`).
