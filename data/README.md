# Data snapshot

This directory contains compact, human-readable snapshots of the current project state.

These files are **not** replacements for the frozen computational harness, raw model outputs, or full benchmark traces. They exist so that manuscript headline results can be inspected in machine-readable form. The 2026-09-10 claim-to-evidence audit additionally distinguishes compact snapshots from direct reproducibility evidence.

## Canonical version registry

Use `version_registry.json` as the machine-readable naming source of truth. Version numbers are family-specific and must not be compared across families.

Current labels:

- scientific model: **NH3-FINAL-1.1**;
- methanol case: **MEOH-D01-v3**;
- canonical rank-preservation control: **Au/TiO2-RP V1.1**;
- supporting rank-preservation robustness: **Au/TiO2-RP V1.3**;
- Agent umbrella: **Decision-aware Agent Harness**;
- supporting Agent benchmarks: **DRIFT v2** and **TRANSFER v1**;
- formal frozen Agent benchmark: **DISCOVER V1**;
- confirmatory boundary extension on the unchanged V1 protocol: **DISCOVER-BOUNDARY-C1**;
- **DISCOVER V2** is reserved for a future protocol redesign and is not a completed current benchmark.

## Files

- `version_registry.json` — machine-readable canonical naming/version registry.
- `canonical_results_2026-09-06.csv` — current NH3-FINAL-1.1 scientific headline snapshot and cross-reaction leverage values. **Audit note:** this file is numerically canonical for manuscript-facing values but is not the direct raw provenance for NH3-FINAL-1.1 or the 273–410 cross-reaction derivation.
- `claim_evidence_registry_2026-09-10.csv` — machine-readable manuscript claim -> source -> provenance-status -> figure-lock registry.
- `discover_benchmark_2026-09-06.csv` — strong-tier formal DISCOVER V1 precursor snapshot. It records the original 70 policy-E runs and A-D comparison; it is not the final cross-model or C1 Agent claim.
- `rank_preservation_control_v1_1.csv` — literature-calibrated Au/TiO2 CO-oxidation rank-preservation control: particle size, mass activity, required catalyst mass, required Au mass, and burden relative to the best state.
- `rank_preservation_partial_relaxation.csv`, `rank_preservation_partial_relaxation.py` — intermediate V1.2 partial-relaxation stress test; historical/supporting only.
- `rank_preservation_semiopen_v1_3.py`, `rank_preservation_semiopen_v1_3_summary.csv` — current Au/TiO2-RP V1.3 semi-open robustness extension.
- `cross_model_scores_2026-09-06.csv` — DISCOVER V1 cross-model scores per model x variant x budget.
- `cross_model_failure_matrix_2026-09-06.csv` — DISCOVER V1 failure modes x model x variant x budget.
- `cross_model_stats_2026-09-07.csv` — DISCOVER V1 Wilson intervals, exact tests, tier trend, logistic analyses and pre-registered E-vs-D Go check.
- `cross_model_metadata_2026-09-06.json` — exact DISCOVER V1 model IDs, token totals, retry/exception status and frozen-hash checks.
- `discover_frozen_v1_hashes.json` — SHA-256 pins defining DISCOVER V1. Any modification to a pinned protocol component defines DISCOVER V2.
- `discover_boundary_c1_runs.csv`, `discover_boundary_c1_summary.csv`, `discover_boundary_c1_D_reference.csv`, `discover_boundary_c1_metadata.json` — C1 Phase A strong-tier boundary evidence and deterministic D reference.
- `discover_boundary_c1_phase_b_runs.csv`, `discover_boundary_c1_phase_b_summary.csv`, `discover_boundary_c1_phase_b_tokens.csv`, `discover_boundary_c1_phase_b_metadata.json` — C1 Phase B 175/225-CU mini/nano extension plus the strong comparison cells.
- `discover_boundary_c1/` — C1 raw traces, logs and before/after frozen-hash records.
- `cross_model_analysis.py`, `cross_model_stats.py`, `cross_model_stats_figure.py` — DISCOVER V1 analysis scripts.

### `meoh/` — MEOH-D01-v3

- `MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx` — frozen explicit-loop workbook.
- `meoh_candidate_ranking_D01v3.csv` — four catalyst-temperature states: upstream ranks, NPC at 2% purge, economic rank, loop diagnostics and local leverages.
- `meoh_candidate_ranking_D01v3_provenance.json` — workbook SHA-256, sheets used and rank metrics.
- `make_meoh_ranking_figure.py` — regenerates the candidate ranking CSV/figure from the workbook.
- `meoh_d01_v3.json` — canonical reaction-case record used by the transfer harness.
- `meoh_purge_robustness_D01v3.csv`, `meoh_purge_robustness_D01v3_summary.json`, `meoh_purge_robustness.py` — economic order, rho, tau and pairwise inversions across 396 purge levels (0.5–40%) and the per-candidate purge optima.

## Manuscript evidence hierarchy

### Scientific NH3 claims

Use **NH3-FINAL-1.1** only. `canonical_results_2026-09-06.csv` is the current compact numerical source, but final F1–F6 locking requires an immutable pointer to the underlying canonical run `outputs/nh3_final_20260905T134204Z`, its raw result files and generating code/hashes. Historical NH3-FINAL-1.0 workbooks are not valid substitutes for this provenance.

### MeOH claims

Use the frozen D01 v3 workbook together with the extracted CSV/provenance JSON and analysis scripts in `meoh/`. This chain is directly traceable in the repository.

### Au/TiO2 control claims

Use `rank_preservation_control_v1_1.csv` plus `../controls/au_tio2_rank_preservation_v1_1.py` for the canonical V1.1 control. Use V1.3 files only as supporting robustness.

### Agent claims

For manuscript-level Agent claims, use the evidence in this order:

1. `discover_frozen_v1_hashes.json` and the frozen DISCOVER V1 protocol;
2. DISCOVER V1 per-trace scores/failure records and `cross_model_stats_2026-09-07.csv` for the original cross-model result;
3. `discover_boundary_c1_summary.csv` and `discover_boundary_c1_phase_b_summary.csv` for the post-V1 boundary estimates;
4. C1 raw traces and hash-check records under `discover_boundary_c1/`;
5. `../docs/DISCOVER_BOUNDARY_C1_RESULTS.md`, `../docs/DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`, `../docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A1.md`, and `../docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md` for interpretation and protocol-deviation provenance;
6. README/manuscript summaries last.

The frozen DISCOVER V1 anonymous complete-decision counts remain **6/35 (nano), 15/35 (mini), 35/35 (strong)**. C1 further resolves the boundary: fixed-VOI D reaches a complete decision at **206 CU**; at 175 CU strong/mini/nano policy E complete **19/20 / 0/20 / 0/20**, and at 225 CU **20/20 / 6/20 / 0/20**. The manuscript claim is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed policy threshold**, not universal adaptive superiority or universal raw-compute saving.

## Audit note — 2026-09-10

See `../docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md` for the current claim-to-evidence and figure-lock audit. The first pass found no contradiction in the canonical headline numbers. The main unresolved provenance items are the direct NH3-FINAL-1.1 raw/generator chain and a dedicated source bundle for the cross-reaction **273–410 (midpoint ~328)** normalized-leverage result.
