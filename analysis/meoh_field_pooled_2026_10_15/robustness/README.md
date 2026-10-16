# Methanol robustness analyses on the combined 81-comparison set

The methanol field result uses 81 comparison groups from 50 papers: the 40 groups of the first extraction and 41 groups
of the second (`../run_pooled.py`). Until now the robustness analyses existed only for the first 40 groups. Here each one
is rerun on all 81 groups with exactly the same code. The inert-limited loop (S6, `cost_recycled_opt_inlet`) is primary.
The loop without the inlet limit (S5, `cost_recycled_opt`) is reported alongside wherever the original reports it.

- **Numbers:** `summary.json` (every combined-set number next to its first-set anchor) and `results_table.md`.
- **Builder:** `build_summary.py` reads the outputs below. It also checks that the first-set groups of every
  deterministic combined run equal the committed first-set result.

## One switch, no copies

`../field_set.py` is the only place that knows which candidate set a script runs on. It reads
`MEOH_FIELD_SET` (`first`, the default, or `combined`).

| | `first` (default) | `combined` |
|---|---|---|
| printed candidates | `meoh_literature_inversion_2026_10_05/literature_candidates.csv` | that table, then `validation_meoh_prospective_2026_10_13/new_candidates_costed.csv` (`batch` = first / second) |
| all entries | `literature_candidates_all_entries.csv` | that table, then the second extraction's all-entries table (`all_entries/second_all_entries_costed.csv`) |
| records | `agent/extraction/out/records_normalized.csv` | those, then `load_new_records(corrected=True)` |
| outputs | the script's committed folder | `robustness/<analysis>/` |

How the combined tables are built:

- The first set's rows come first, in their committed order. Each script's first-set part therefore has the same
  rows, response-surface grid and cache keys as the committed run.
- The second extraction's all-entries table is `build_candidates(load_new_records(True), printed_only=False)`. It is
  costed once with the first set's call (`meoh_candidates.plant_costs(row, RHO_SCALES)`, 2 workers) and cached.
  `validation_meoh_prospective_2026_10_13/score.py` scores the same cohort independently and gets the same counts
  (47/78 S6, 23/78 S5).

With the default every changed script regenerates its committed outputs (see "Default-mode reproduction").

## Analyses

Run with the CatalystForge interpreter, `PYTHONIOENCODING=utf-8`, `MEOH_FIELD_SET=combined`, and 2 plant-model workers
per job. Each script asserts its first-set anchors and stops if one fails.

1. **Re-measurement Monte Carlo** (`stats_s6/`, `stats_s5/`; Extended Data Fig. 3).
   - Run: `meoh_s6_robustness_2026_10_13/run_stats_wrapper.py s6`, then `... s5`, with `STATS_WORKERS=2`.
   - Same method as the committed runs: error model, 2,000 draws per noise scale (1x, 2x, 4x), seed and streams, response
     surface, exact off-grid runs, and 5 exact validation replicates per scale.
   - The draws cover all 632 scored entries in one stream, so the first-set groups of the combined run are a new draw
     of the same model. The first-set anchor is the committed run, which the default mode reproduces.
   - The first set's grid and exact runs are reused from the committed caches. Only the second set's runs are new:
     22,141 grid runs and 12,346 off-grid and validation runs. Some second-set states take up to ~8 s per run.
   - The new runs were computed in 6 shards of 2 workers each with `mc_shard.py`. This is the frozen script's
     enumerate / compute / merge workflow, calling the S6 wrapper's `exact_cost_both`; one sweep gives both the S6 and
     the S5 cost. After merging, `run_stats_wrapper.py s6` reads every run from the cache.
   - The S5 runs recorded with the combined S6 runs (`s5_crosscheck.csv.gz`, the same sweep) seed the S5 cache. The S5
     run then needed no new model run. `meoh_s6_robustness_2026_10_13/cache_check.json` shows these runs agree with the
     frozen S5 runs: 28,623 of 28,623.
2. **Inlet-limit sweep and CO definitions** (`inlet_definition/`; Extended Data Fig. 8, Supplementary Note 3).
   - Run: `meoh_inlet_definition_2026_10_12/run_inlet_definition.py`.
   - Limits 4–30 % under two definitions: the frozen CH4 + CO + N2, and CH4 + N2 only.
   - Reported: the 5–10 % band, 12 % and 15 %, and the reactor-inlet CO share without the limit (median, 10th and 90th
     percentile over the entries of the S5-scored groups, as the audit computes it).
   - The paper-bootstrap excess over the unlimited loop is computed in `build_summary.py`, using
     `meoh_constraint_boundary_2026_10_12/run_boundary.bootstrap_all`'s resamples. On the committed first-set tables it
     reproduces `boundary_summary.json` exactly.
3. **Recycled CO converted up to CO-hydrogenation equilibrium** (`co_conversion_bound/`).
   - Run: `meoh_co_conversion_bound_2026_10_13/run_co_conversion_bound.py`.
4. **Catalyst inventory, conversion raised towards equilibrium** (`conversion_s6/`, `conversion_s5/`).
   - Run: `verify_2026_10_12_s6_conversion/run_s6_conversion.py` (S6) and
     `meoh_literature_inversion_2026_10_05/run_conversion_sensitivity.py` (S5).
   - Both the printed and the all-entries cohorts are run.
   - One second-extraction feed is H2-lean: H2/CO2 = 0.1 (10.1021/acscatal.6c04842, Fig. 5c; 8 all-entries rows and
     1 printed row). The equilibrium solver's CO2-based starting grid admits no start for it, so the frozen code stopped
     with "no equilibrium root".
   - Where that grid gives no root, `x_eq_feed` now rescales it to the H2-limited extent. X_eq of that feed is
     0.020–0.031 at 200–260 °C. No first-set feed reaches this branch; the default run is still byte-identical.
5. **Composition-priced catalysts** (`catalyst_cost/`).
   - Run: `meoh_s6_robustness_2026_10_13/run_catalyst_cost_wrapper.py`.
   - The second set's candidates are rebuilt from its corrected records, exactly as `score.py` builds them. They are
     priced by the same `catalyst_prices` rules from those records; `build(cand, rec)` now takes the records.
6. **Unreported CO / CH4 selectivities at either bound** (`selectivity_split/`).
   - Run: `meoh_s6_robustness_2026_10_13/run_selectivity_split_wrapper.py`.
   - The wrapper's S5 is the frozen `run_selectivity_split.py` rule and cost, and is checked against it.
7. **Plot-read cohort** (`all_entries/`).
   - Run: `run_all_entries.py`.
   - Scored by `meoh_candidates.aggregate`, `bootstrap` and `mismatch_kinds.classify` on the combined all-entries table.
8. **Pruning by the lower bound** (`pruning/`; Extended Data Fig. 2).
   - Run: `meoh_pruning_2026_10_06/run_meoh_pruning.py`.
   - The S5 and inert-CO treatments are run, as committed.
   - The compute share uses the full-evaluation and bound timings measured in the same run.
9. **Plant-term variants** (`plant_variants/`).
   - Run: `meoh_plant_benchmark_2026_10_06/lit_sensitivity.py`, with `BENCH_WORKERS=2`.
   - All 22 variants are run.
   - The "14–16 of 40" range is over the loop-pressure-drop, recycle, compression (`pf_aligned_compression`), capital,
     equipment-split and price variants. The catalyst-replacement, combined and baseline variants are excluded, as in
     the audit.
   - In combined mode each variant is also scored in the inert-limited loop (S6): the minimum over the eligible purge
     levels of the same sweep. The knobs varied here do not change the loop composition.
10. **Other Supplementary Note 3 numbers with a first-set-only source** (`purge_boundary/` and `build_summary.py`).
    - Purge grid extended to 1e-4 %: `meoh_literature_inversion_2026_10_05/run_purge_boundary.py`.
      - Every first-set S5 optimum sits at the 0.5 % floor; the script asserts this, and the first-set part of the
        combined run checks it as an anchor.
      - On the combined set one second-set entry's S5 optimum lies above the floor (631 of 632). This count is
        reported, not asserted.
    - Near-infeasible and ordinary disagreements, crossed with re-measurement robustness: the `run_pooled.near_infeasible`
      rule on `../groups_S6.csv`, with `stats_s6/group_noise_probabilities.csv`.
    - The full list, with each source and where its combined value is, is in `summary.json` → `10_note3_sources`.

## Default-mode reproduction

Each changed script was rerun with the default (`MEOH_FIELD_SET` unset). `compare_default.py` then compared its outputs
with the committed files (git HEAD): byte-identical, or numbers within 1e-9 relative. Run time, worker count and the
gate's own reproduction noise (`max_rel_diff`, `max_relative_difference`) are skipped. The committed files were then
restored, so no first-set output changes.

| script | default-mode outputs vs committed |
|---|---|
| `meoh_main_result_stats_2026_10_06/run_main_result_stats.py` | byte-identical (scenarios recomputed from the exact cache) |
| `meoh_s6_robustness_2026_10_13/run_stats_wrapper.py` s6, s5 | every count, verdict and noise result byte-identical; the surface-vs-exact error diagnostics move by <= 5e-10 relative (note below) |
| `meoh_inlet_definition_2026_10_12/run_inlet_definition.py` | numerically identical (<= 2.5e-10); `check_anchors.py` passes |
| `meoh_co_conversion_bound_2026_10_13/run_co_conversion_bound.py` | numerically identical (<= 1.3e-10) |
| `verify_2026_10_12_s6_conversion/run_s6_conversion.py` | numerically identical (<= 1.5e-12) |
| `meoh_literature_inversion_2026_10_05/run_conversion_sensitivity.py` | byte-identical (also after the H2-lean fix) |
| `meoh_s6_robustness_2026_10_13/run_catalyst_cost_wrapper.py` | byte-identical |
| `meoh_s6_robustness_2026_10_13/run_selectivity_split_wrapper.py` | byte-identical |
| `meoh_pruning_2026_10_06/run_meoh_pruning.py` | byte-identical apart from the machine timing (compute share 0.3594 vs 0.3599) |
| `meoh_plant_benchmark_2026_10_06/lit_sensitivity.py` | byte-identical apart from run time and worker count |
| `meoh_literature_inversion_2026_10_05/run_purge_boundary.py` | byte-identical |

Note on the wrapper diagnostics: the committed `grid_costs.csv` stores 10 significant digits. Any rerun that reads the
grid back therefore gives `surface_f0_max_rel_diff_vs_frozen` = 4.474e-10, which is the committed file's own value,
instead of the 4.4e-12 of the in-memory original.

## Caches

These are committed so that a restart does not recompute:

- `all_entries/second_all_entries_costed.csv`
- `stats_s6/exact_cache.csv.gz`, `stats_s6/grid_costs.csv`, `stats_s6/s5_crosscheck.csv.gz`
- `stats_s5/exact_cache.csv.gz`, `stats_s5/grid_costs.csv`

Each `scenario_*.json` holds a finished noise scale, so a restart reuses it.
