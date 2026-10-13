# Figure 2 — published laboratory leaderboards against plant-cost leaderboards

Within published comparisons, the paper's own leader is often not the plant-cost leader, in methanol and in ammonia.
183 × 150 mm, six panels: `FigField.{svg,pdf,png}`. In the manuscript numbering of 2026-10-07 this is Fig. 2. Panels a, d
and e come from the agent figure `../fig6` (its panels a, d, e); that directory is left unchanged.

| Panel | Content | Source |
|---|---|---|
| a | ACSA workflow: publications → extraction → self-check → full chain (bound first) → leaderboards | schematic |
| b | methanol: share of the 40 within-paper comparisons (28 papers, printed values) whose paper leader is not the plant-cost leader. Inert-limited loop (primary; reactor-inlet CH4 + CO + N2 <= 6.86 %, frozen column `cost_recycled_opt_inlet`) by leaderboard metric (STY 28/40, X·S 28/40, X 27/40, S_MeOH 17/40; > 5 %: 22, 22, 24, 11), and STY without the limit (frozen column `cost_recycled_opt`, 15/40, 7 > 5 %); paper-cluster bootstrap 95 % CIs on both STY bars (54.1–82.8 % and 15.2–57.1 %) | `analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv`, scored at render time with the frozen `meoh_candidates.aggregate` and checked against `summary.json` (`primary`, `variants.inlet_limit_6.86pct`) and `analysis/meoh_s6_robustness_2026_10_13/results.json` (`frozen_columns.S6.leaderboard_X`, `leaderboard_SMeOH`); CIs: `analysis/meoh_s6_robustness_2026_10_13/stats_s6/summary.json` and `analysis/meoh_main_result_stats_2026_10_06/summary.json` (`cluster_bootstrap.fraction_ci95`); kinds: `summary.json` (`variants.inlet_limit_6.86pct.kinds`) |
| c, left | ammonia (NH3-FINAL-1.2, printed values): share of the 33 within-paper comparisons (23 papers) with a different winner, ranked by rate per g catalyst (the papers' basis), per g metal, and per g catalyst with 90 % Ru recovery; bars are paper-cluster bootstrap 95 % CIs | `analysis/nh3_field_2026_10_06/nh3_1_2/summary_printed.json` (`primary`, `variants.per_g_metal_leaderboard`, `variants.Ru_recovery_90pct`, `bootstrap_papers`) |
| c, right | what the 7 mismatched ammonia comparisons differ by, with papers and median regret; for "different metal", how many the same-support Fe catalyst wins | `summary.json` (`primary.mismatch_kinds`); plant-winner metal from `nh3_1_2/group_metrics_printed.csv` + `candidates_printed.csv` |
| d | methanol group Re/TiO2, 100 bar: STY against net plant cost in the inert-limited loop (filled, `cost_recycled_opt_inlet`; purge `purge_recycled_opt_inlet`) and without the limit (open, `cost_recycled_opt`), marker area ∝ CH4 selectivity | `analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv` (group `10.1021/acscatal.5c05984 \| 100 bar \| H2/CO2 4 \| 10 NL/g/h`) |
| e | methanol group InNi3C0.5 on m-, t-, a-ZrO2 and SiO2, 300 °C, 4 MPa (Meng et al. 2021, Sci. Adv., Supplementary Table 1), as d with marker area ∝ CO selectivity | same file (group `10.1126/sciadv.abi6012 \| 40 bar \| H2/CO2 3 \| 24 NL/g/h`) |
| f | ammonia group Ru, Fe, Co on BaTiO3−xHx at 5 MPa (Tang et al. 2018): rate per g catalyst against plant cost | `analysis/nh3_field_2026_10_06/nh3_1_2/candidates_printed.csv` (group `10.1002/aenm.201801772 \| 400 C \| 5 MPa \| H2/N2 3 \| 6.6e+04 mL/g/h`), regret from `nh3_1_2/group_metrics_printed.csv` |

Every number is read from these files; the renderer asserts that the methanol counts it scores agree with the frozen
summaries (28/40 and 22 > 5 % in the inert-limited loop, 15/40 and 7 > 5 % without the limit, X and S_MeOH against
`results.json`), that both bootstrap CIs agree with the analysis summaries, that the ammonia mismatch kinds sum to the
mismatched groups, and that the panel-f leaders are those of `group_metrics.csv`. Smallest text 5.3 pt.

Note on panel c (NH3-FINAL-1.2, printed values): in all 3 "different metal" comparisons (2 papers) the plant winner is the same-support Fe catalyst.

Build: `D:\Tools\pur_bridge_env\Scripts\python.exe make_fig_field.py` → `FigField.{svg,pdf,png}`.
Source Data: `source_data/SourceData_Fig2.xlsx` (`tools/build_source_data.py`).
