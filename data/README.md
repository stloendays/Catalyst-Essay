# Data directory

This directory contains compact, machine-readable datasets used for manuscript-facing analysis, figure generation and benchmark summaries.

These files are intentionally smaller than the full reproducibility bundles. The frozen source-harness provenance is stored under [`../provenance/`](../provenance/); validation outputs are under [`../artifacts/`](../artifacts/); figure assets and renderers are under [`../figures/`](../figures/).

## Evidence hierarchy

For a scientific quantity, use sources in this order:

1. frozen source/provenance bundle;
2. machine-readable result file or raw benchmark trace;
3. figure-generation script and canonical figure asset;
4. manuscript-facing summary tables;
5. README prose.

The compact CSV/JSON files here are designed for inspection and plotting. They do not replace the underlying frozen scientific model or benchmark protocol.

## Canonical version families

- **NH3-FINAL-1.1** — canonical ammonia model;
- **MEOH-D01-v3** — canonical methanol explicit-loop case;
- **Au/TiO2-RP V1.1** — canonical rank-preservation control;
- **Au/TiO2-RP V1.3** — supporting semi-open robustness extension;
- **DISCOVER V1** — frozen formal Agent benchmark;
- **DISCOVER-BOUNDARY-C1** — confirmatory boundary extension on the unchanged DISCOVER V1 protocol.

Machine-readable naming source: [`version_registry.json`](version_registry.json). Human-readable registry: [`../docs/VERSION_REGISTRY.md`](../docs/VERSION_REGISTRY.md).

## Ammonia data

### `canonical_results_2026-09-06.csv`

Compact manuscript-facing snapshot of the promoted **NH3-FINAL-1.1** quantities. Principal current values include:

- atomic top three: **Ru > Os > Fe**;
- economic top three: **Fe > Ru > Os**;
- Fe / Ru / Os costs: **15.292 / 22.031 / 25.832 USD/t NH3**;
- Top-3 Spearman rho: **-0.50**;
- full 15-metal raw Spearman rho: **0.929**;
- Fe feasibility: **79.9%**;
- Ru activity-only break-even: **201.22x**;
- scaling-consistent activity headroom: **1.090x at 673 K**, **2.525x maximum** over the frozen process-state library.

The full NH3 source-harness provenance is now present under [`../provenance/nh3_final_1_1/`](../provenance/nh3_final_1_1/). Repository validation closed with 13/13 canonical anchors, 6/6 evidence classes, 6/6 figure mappings, 28/28 manifest files present and 0 source-manifest hash mismatches.

### Claim and figure registries

- `claim_evidence_registry_2026-09-10.csv` — manuscript claim -> evidence -> provenance status.
- `figure_lock_registry_2026-09-10.csv` — figure-by-figure scientific/render state.

Use the frozen NH3 provenance bundle, not archived NH3-FINAL-1.0 files, when tracing current manuscript claims.

## Methanol data — `meoh/`

The canonical reaction case is **MEOH-D01-v3**.

Principal files:

- `MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx` — frozen explicit recycle/separation workbook;
- `meoh_candidate_ranking_D01v3.csv` — four catalyst-temperature states, upstream ranks, 2% purge NPC, economic ranks and local leverages;
- `meoh_candidate_ranking_D01v3_provenance.json` — workbook hash and extraction provenance;
- `meoh_purge_robustness_D01v3.csv` — 396-level purge sweep from 0.5% to 40%;
- `meoh_purge_robustness_D01v3_summary.json` — purge-sweep summary;
- `make_meoh_ranking_figure.py` and `meoh_purge_robustness.py` — analysis/reconstruction scripts.

Current four-state headline result using STY per g Re as the upstream metric: **rho = 0.20**, **tau = 0**, **3/6 pairwise inversions**, with the upstream winner falling from #1 to economic rank #3.

## Rank-preservation control

### Canonical V1.1

- `rank_preservation_control_v1_1.csv` — 2-6 nm Au/TiO2 particle-size states and propagated catalyst burden.

Generator: [`../controls/au_tio2_rank_preservation_v1_1.py`](../controls/au_tio2_rank_preservation_v1_1.py).

Canonical result: full rank preservation, **rho = 1.000**, **tau = 1.000**, **0 inversions**, and **10,000/10,000** predefined literature-envelope draws preserving the complete order.

### Supporting V1.3

- `rank_preservation_semiopen_v1_3.py`
- `rank_preservation_semiopen_v1_3_summary.csv`

V1.3 tests moderate candidate-specific kinetic and operating freedom. It supports the robustness discussion but does not replace V1.1 as the canonical control.

## Agent benchmark data

### DISCOVER V1

Principal files include:

- `discover_frozen_v1_hashes.json` — frozen protocol hash pins;
- `cross_model_scores_2026-09-06.csv` — model x variant x budget scores;
- `cross_model_failure_matrix_2026-09-06.csv` — failure-mode matrix;
- `cross_model_stats_2026-09-07.csv` — confidence intervals, exact tests and tier analyses;
- `cross_model_metadata_2026-09-06.json` — model IDs, retry/exception state and metadata;
- `cross_model_analysis.py`, `cross_model_stats.py`, `cross_model_stats_figure.py` — analysis scripts.

Frozen anonymous complete-decision counts are **6/35 nano, 15/35 mini, 35/35 strong**.

### DISCOVER-BOUNDARY-C1

Principal files include:

- `discover_boundary_c1_runs.csv`
- `discover_boundary_c1_summary.csv`
- `discover_boundary_c1_D_reference.csv`
- `discover_boundary_c1_metadata.json`
- `discover_boundary_c1_phase_b_runs.csv`
- `discover_boundary_c1_phase_b_summary.csv`
- `discover_boundary_c1_phase_b_tokens.csv`
- `discover_boundary_c1_phase_b_metadata.json`
- `discover_boundary_c1/` — raw traces, logs and frozen-hash records.

The deterministic fixed-VOI policy reaches the complete decision at **206 CU**. At 175 CU, strong/mini/nano adaptive runs complete **19/20 / 0/20 / 0/20**; at 225 CU they complete **20/20 / 6/20 / 0/20**.

The current interpretation is a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy threshold**. The data do not support a universal raw-compute-saving claim.

## Cross-reaction comparison

The current supported cross-reaction result is mechanistic:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The historical normalized ratio **273-410** is retained only as archived pre-FINAL-1.1 evidence. Its original NH3 economic-leverage metric implementation could not be established sufficiently to promote it as a current quantitative result. No replacement ratio is introduced.

## Where to look next

- Project-level overview: [`../README.md`](../README.md)
- Numerical summary: [`../docs/RESULTS_AT_A_GLANCE.md`](../docs/RESULTS_AT_A_GLANCE.md)
- Figure map: [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md)
- Detailed documentation index: [`../docs/README.md`](../docs/README.md)
- Frozen provenance: [`../provenance/`](../provenance/)
