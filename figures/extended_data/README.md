# Extended Data figures

Seven figures, 183 mm wide, rendered by one script from panel tables that the Source Data builder also uses.

| File | Content | Sources |
|---|---|---|
| `EDFig1_extraction_accuracy` | extraction accuracy by source (X, S_MeOH, STY); recall per reference set | `agent/extraction/eval/field_accuracy_by_source.csv`, `entry_metrics.csv` |
| `EDFig2_bimetallic_surfaces` | bimetallic surfaces in three element layers (transition metals; + group 3–5; + sp metals) | `analysis/nh3_alloy_extension_2026_10_05/alloy_chain_results.csv`, `summary.json` |
| `EDFig3_methanol_robustness` | bootstrap distribution, regret-threshold curve, measurement and plot-reading resampling, per-group persistence | `analysis/meoh_main_result_stats_2026_10_06/` |
| `EDFig4_nh3_measured_catalysts` | measured ammonia catalysts of the review: rate per g metal against plant cost; lowest cost per metal | `analysis/nh3_supported_2026_10_06/supported_candidates.csv`, `summary.json` |
| `EDFig5_ru_actual_mc` | P(Fe cheaper) under the five treatments; where the Ru catalyst wins by u, r and Ru content | `analysis/nh3_mc_ru_actual_2026_10_06/draws.csv`, `summary.json` |
| `EDFig6_meoh_plant_benchmark` | Pérez-Fortes cost terms; like-for-like parity across studies; loop metrics; headline under 18 plant variants | `analysis/meoh_plant_benchmark_2026_10_06/` |
| `EDFig7_bound_pruning` | lower bound against full cost, methanol and ammonia; full optimizations saved | `analysis/meoh_pruning_2026_10_06/`, `analysis/nh3_alloy_extension_2026_10_05/` |

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
