# Extended Data figures

Eight figures, 183 mm wide, rendered by one script from panel tables that the Source Data builder also uses. The ammonia
panels read the NH3-FINAL-1.2 outputs (`nh3_1_2/` subfolders; canonical run `nh3_final_1_2_20261013`).

| File | Content | Sources |
|---|---|---|
| `EDFig1_extraction_accuracy` | extraction accuracy by source (X, S_MeOH, STY); recall per reference set | `agent/extraction/eval/field_accuracy_by_source.csv`, `entry_metrics.csv` |
| `EDFig2_bimetallic_surfaces` | bimetallic surfaces in three element layers (transition metals; + group 3–5; + sp metals) | `analysis/nh3_alloy_extension_2026_10_05/nh3_1_2/alloy_chain_results.csv`, `summary.json` |
| `EDFig3_methanol_robustness` | both methanol loops (inert-limited, primary; no limit): bootstrap distributions, regret-threshold curves, measurement resampling, per-group persistence with the near-infeasible disagreements, and every robustness check of the text | `analysis/meoh_s6_robustness_2026_10_13/` (`stats_s6/`, `results.json`, `s6_groups.csv`), `analysis/meoh_main_result_stats_2026_10_06/`, `analysis/meoh_literature_inversion_2026_10_05/summary.json`, `analysis/verify_2026_10_12_s6_conversion/` |
| `EDFig4_nh3_measured_catalysts` | measured ammonia catalysts of the review: rate per g metal against plant cost; lowest cost per metal | `analysis/nh3_supported_2026_10_06/nh3_1_2/supported_candidates.csv`, `summary.json` |
| `EDFig5_ru_actual_mc` | P(Fe cheaper) under the five treatments; where the Ru catalyst wins by u, r and Ru content | `analysis/nh3_mc_ru_actual_2026_10_06/nh3_1_2/draws.csv`, `summary.json` |
| `EDFig6_meoh_plant_benchmark` | Pérez-Fortes cost terms; like-for-like parity across studies; loop metrics; headline under 18 plant variants | `analysis/meoh_plant_benchmark_2026_10_06/` |
| `EDFig7_bound_pruning` | lower bound against full cost, methanol and ammonia; full optimizations saved | `analysis/meoh_pruning_2026_10_06/`, `analysis/nh3_alloy_extension_2026_10_05/nh3_1_2/` |
| `EDFig8_meoh_purge_inlet` | purge boundary, reactor-inlet composition, optimal purge and recycle ratio by loop treatment; different winner against the inlet limit (4–30 %) counting CH4 + CO + N2 or CH4 + N2 only | `analysis/meoh_literature_inversion_2026_10_05/purge_boundary_*`, `analysis/meoh_inlet_definition_2026_10_12/definition_scan.csv` |

- `ed_data.py` builds every panel table from the files above and checks it against the analysis summaries:
  - the methanol bootstrap is re-drawn with the analysis seed and reproduces the 95 % CI of `summary.json` exactly;
  - the methanol evaluated/excluded split is re-derived with the agent rule of `run_meoh_pruning.py` and matches
    `group_pruning.csv` in every group;
  - P(Fe cheaper) is recomputed from `draws.csv` and matches `summary.json`.
- `render_extended_data.py` draws the figures and, run without arguments, writes `ED_CAPTIONS.md` from the same tables.

```
D:\Tools\pur_bridge_env\Scripts\python.exe render_extended_data.py        # all figures + ED_CAPTIONS.md
D:\Tools\pur_bridge_env\Scripts\python.exe render_extended_data.py 3 5    # only ED Figs 3 and 5
```
