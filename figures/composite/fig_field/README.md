# Figure 2 — published laboratory leaderboards against plant-cost leaderboards

Within published comparisons, the paper's own leader is often not the plant-cost leader, in methanol and in ammonia.
183 × 194 mm, six panels: `FigField.{svg,pdf,png}`. In the manuscript numbering of 2026-10-07 this is Fig. 2. Panels a, d
and e come from the agent figure `../fig6` (its panels a, d, e); that directory is left unchanged.

| Panel | Content | Source |
|---|---|---|
| a | literature → ACSA (extract, self-check, cost bound) → multiscale chain (active site, supported particle, catalyst pellets, multibed converter, synthesis loop, cost) → leaderboards | laid out as an editable slide `Fig2a.pptx` (`build_fig2a_pptx.py`; adjust by hand, export to PDF, render to `Fig2a_from_pptx.png`); atomistic renders `build_atoms.py` (OVITO); extrudate photograph: Wikimedia Commons `Extrudates-pellets-beads-molecular-sieve-hengye-inc.jpg` (CC BY-SA 4.0), crop restored by an image model without adding or moving objects (`assets/extrudates_restored.png`); converter: Wikimedia Commons `Ammoniakreaktor MS-ru.svg` (CC0), labels removed and recoloured (`assets/converter.png`); originals in `assets/src/` |
| b | methanol: share of the 81 within-paper comparisons (50 papers, both extractions, printed values) whose paper leader is not the plant-cost leader. First bar: catalyst against catalyst, each at its best measured point, 26/63 (19 > 5 %, CI 29.4–53.3 %); then every operating point in the inert-limited loop by leaderboard metric (STY 50/81, X·S 50/81, X 54/81, S_MeOH 30/81; > 5 %: 42, 42, 49, 19) and STY without the limit (25/81, 10 > 5 %) | `analysis/meoh_field_pooled_2026_10_15/` (scored at render time with the frozen `meoh_candidates.aggregate`, checked against the pooled summary); first bar: `analysis/meoh_catalyst_level_2026_10_19/summary.json` (`cat_primary.comparison`) |
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
