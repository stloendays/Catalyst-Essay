# Documentation guide

This directory is the main reading entry point for the manuscript project.

The repository separates current manuscript-facing results from detailed provenance/audit records. For a first read, use the short path below; open the audit files only when a numerical claim needs to be traced to its source.

## Recommended reading order

1. [`RESEARCH_FRAME.md`](RESEARCH_FRAME.md) — scientific question, multiscale logic and the role of the decision-aware AI layer.
2. [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md) — current numerical results only.
3. [`FIGURE_MAP.md`](FIGURE_MAP.md) — scientific role of F1-F10.
4. [`MANUSCRIPT_SKELETON.md`](MANUSCRIPT_SKELETON.md) — current paper structure and argument flow.
5. [`AGENT_HARNESS.md`](AGENT_HARNESS.md) — deterministic multiscale harness and decision layer.
6. [`DATA_AND_CODE_AVAILABILITY.md`](DATA_AND_CODE_AVAILABILITY.md) — reproducibility and data/code map.

Superseded conclusions and intermediate values are not repeated through the active documentation. They are centralized in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).

## Current scientific story

```text
Atomic ranking
    -> multiscale propagation
    -> industrial ranking
    -> backward design
```

The ammonia case establishes the main decision-frontier inversion: **Ru > Os > Fe** in intrinsic activity becomes **Fe > Ru > Os** after process/economic propagation. The full 15-metal ranking remains strongly correlated, showing that the important reshuffling is concentrated at the decision frontier.

The uncertainty analysis asks whether descriptor uncertainty changes feasibility or the identity of actionable candidates. Backward design converts Fe cost parity into a required Ru activity improvement and compares that target with the frozen scaling-consistent catalyst-property manifold.

The methanol case tests a different catalyst-to-process pathway in which selectivity and methane formation couple to feed loss, purge and recycle. The Au/TiO2 control provides the complementary case in which a ranking is preserved under a monotonic downstream mapping.

The Agent work is evaluated as a decision-allocation problem. Its current claim is capability- and budget-dependent: the strong tier can recover the full decision below the fixed-policy completion threshold, while the non-binding allowance demonstrates that this is not a universal raw-compute saving.

## Evidence hierarchy

When two files summarize the same quantity, use this order:

1. frozen source/provenance bundle;
2. machine-readable result table or raw trace;
3. figure-generation code and canonical figure asset;
4. manuscript-facing summary document;
5. overview prose.

Frozen scientific source bundles are under [`../provenance/`](../provenance/). Current manuscript-facing data are under [`../data/`](../data/), and canonical/manuscript-ready figures are under [`../figures/`](../figures/).

## Current version families

- **NH3-FINAL-1.1** — canonical ammonia model
- **MEOH-D01-v3** — canonical methanol explicit-loop case
- **Au/TiO2-RP V1.1** — canonical rank-preservation control
- **Au/TiO2-RP V1.3** — supporting semi-open robustness extension
- **DISCOVER V1** — frozen formal Agent benchmark
- **DISCOVER-BOUNDARY-C1** — confirmatory boundary extension on the unchanged V1 protocol

Use [`VERSION_REGISTRY.md`](VERSION_REGISTRY.md) for the full naming registry.

## Detailed audit and provenance records

Key records include:

- [`CLAIM_EVIDENCE_AUDIT_2026-09-10.md`](CLAIM_EVIDENCE_AUDIT_2026-09-10.md)
- [`NH3_FINAL_1_1_PROVENANCE_POINTER.md`](NH3_FINAL_1_1_PROVENANCE_POINTER.md)
- [`NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`](NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md)
- [`CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md)
- [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md)
- DISCOVER/C1 result and metric-definition records in this directory.

## Current production state

The scientific evidence is frozen. F1-F8, F9B and F10 are locked; F9A is the current qualitative pathway panel. Current work is publication-layout harmonization, manuscript integration, Supporting Information organization and final reproducibility packaging.
