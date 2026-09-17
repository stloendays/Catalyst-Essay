# Data directory

This directory contains current machine-readable datasets used for manuscript-facing analysis, figure generation and benchmark summaries.

For a one-file overview, start with [`manuscript_headline_results_2026-09-17.csv`](manuscript_headline_results_2026-09-17.csv). Superseded compact tables and intermediate analyses are removed from the active data surface and recorded in [`../docs/RETIRED_RESULTS.md`](../docs/RETIRED_RESULTS.md).

Frozen source-harness provenance is stored under [`../provenance/`](../provenance/); validation outputs are under [`../artifacts/`](../artifacts/); figure assets and renderers are under [`../figures/`](../figures/).

## Evidence hierarchy

For a scientific quantity, use sources in this order:

1. frozen source/provenance bundle;
2. machine-readable result file or raw benchmark trace;
3. figure-generation script and canonical figure asset;
4. manuscript-facing summary table;
5. overview prose.

## Canonical version families

- **NH3-FINAL-1.1** — canonical ammonia model
- **MEOH-D01-v3** — canonical methanol explicit-loop case
- **Au/TiO2-RP V1.1** — canonical rank-preservation control
- **Au/TiO2-RP V1.3** — supporting semi-open robustness extension
- **DISCOVER V1** — frozen formal Agent benchmark
- **DISCOVER-BOUNDARY-C1** — confirmatory boundary extension on unchanged V1

Machine-readable naming source: [`version_registry.json`](version_registry.json). Human-readable registry: [`../docs/VERSION_REGISTRY.md`](../docs/VERSION_REGISTRY.md).

## Ammonia

### `canonical_results_2026-09-06.csv`

Current compact **NH3-FINAL-1.1** snapshot. Principal quantities include:

- atomic top three: **Ru > Os > Fe**
- economic top three: **Fe > Ru > Os**
- Fe / Ru / Os costs: **15.292 / 22.031 / 25.832 USD/t NH3**
- Top-3 Spearman rho: **-0.50**
- full 15-metal raw Spearman rho: **0.929**
- Fe feasibility: **79.9%**
- Ru activity-only break-even: **201.22x**
- scaling-consistent headroom: **1.090x at 673 K; 2.525x maximum**

The full source-harness provenance is under [`../provenance/nh3_final_1_1/`](../provenance/nh3_final_1_1/).

### Registries

- `claim_evidence_registry_2026-09-10.csv` — current manuscript claim -> evidence -> figure map
- `figure_lock_registry_2026-09-10.csv` — current figure/Extended Data lock and provenance state

The filenames preserve their original audit date, but the records have been updated to the current manuscript state.

## Methanol — `meoh/`

Canonical case: **MEOH-D01-v3**.

Principal files:

- `MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx` — frozen explicit recycle/separation workbook
- `meoh_candidate_ranking_D01v3.csv` — four catalyst-temperature states, upstream/economic ranks and local leverages
- `meoh_candidate_ranking_D01v3_provenance.json` — workbook hash and extraction provenance
- `meoh_purge_robustness_D01v3.csv` — 396-level purge sweep from 0.5% to 40%
- `meoh_purge_robustness_D01v3_summary.json` — purge-sweep summary
- `make_meoh_ranking_figure.py`, `meoh_purge_robustness.py` — reconstruction/analysis scripts

Current four-state result using STY per g Re as the upstream metric: **rho = 0.20**, **tau = 0**, **3/6 pairwise inversions**.

## Rank-preservation control

### Canonical V1.1

- `rank_preservation_control_v1_1.csv`
- generator: [`../controls/au_tio2_rank_preservation_v1_1.py`](../controls/au_tio2_rank_preservation_v1_1.py)

Current result: **rho = 1.000**, **tau = 1.000**, **0 inversions**, and **10,000/10,000** predefined literature-envelope draws preserving the complete order.

### Supporting V1.3

- `rank_preservation_semiopen_v1_3.py`
- `rank_preservation_semiopen_v1_3_summary.csv`

V1.3 is supporting robustness and does not replace V1.1.

## Agent benchmark data

### DISCOVER V1

Principal files:

- `discover_frozen_v1_hashes.json`
- `cross_model_scores_2026-09-06.csv`
- `cross_model_failure_matrix_2026-09-06.csv`
- `cross_model_stats_2026-09-07.csv`
- `cross_model_metadata_2026-09-06.json`
- `cross_model_analysis.py`, `cross_model_stats.py`, `cross_model_stats_figure.py`

Frozen anonymous complete-decision counts are **6/35 nano, 15/35 mini, 35/35 strong**.

### DISCOVER-BOUNDARY-C1

Current summary/provenance files include:

- `discover_boundary_c1_runs.csv`
- `discover_boundary_c1_summary.csv`
- `discover_boundary_c1_D_reference.csv`
- `discover_boundary_c1_metadata.json`
- `discover_boundary_c1_phase_b_runs.csv`
- `discover_boundary_c1_phase_b_summary.csv`
- `discover_boundary_c1_phase_b_tokens.csv`
- `discover_boundary_c1_phase_b_metadata.json`
- `agent_figure_panel_data_2026-09-13.csv`
- `discover_boundary_c1/` — raw traces, logs and frozen-hash records

The deterministic fixed-VOI policy reaches the complete decision at **206 CU**. At 175 CU, strong/mini/nano adaptive runs complete **19/20 / 0/20 / 0/20**; at 225 CU they complete **20/20 / 6/20 / 0/20**.

Canonical narrow-window allocation for the strong tier is **7/7 at 150 CU, 20/20 at 175 CU, 1/8 at 200 CU, 0/20 at 225 CU and 0/9 at 250 CU**. The weaker tiers have no canonical narrow-window use in their measured cells.

## Cross-reaction comparison

The current supported result is mechanistic:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

No current quantitative cross-reaction ratio is stored in the canonical or headline tables. The superseded historical metric is documented only in [`../docs/RETIRED_RESULTS.md`](../docs/RETIRED_RESULTS.md).

## Where to look next

- Current headline table: [`manuscript_headline_results_2026-09-17.csv`](manuscript_headline_results_2026-09-17.csv)
- Project overview: [`../README.md`](../README.md)
- Numerical summary: [`../docs/RESULTS_AT_A_GLANCE.md`](../docs/RESULTS_AT_A_GLANCE.md)
- Figure map: [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md)
- Documentation index: [`../docs/README.md`](../docs/README.md)
- Retirement record: [`../docs/RETIRED_RESULTS.md`](../docs/RETIRED_RESULTS.md)
- Frozen provenance: [`../provenance/`](../provenance/)
