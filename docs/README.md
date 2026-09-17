# Documentation guide

This directory is the main reading entry point for the manuscript project.

The repository contains two different kinds of material: manuscript-facing scientific results and reproducibility/audit records. For a first read, use the short path below and only open the detailed audit files when a numerical claim needs to be traced back to its source.

## Recommended reading order

1. [`RESEARCH_FRAME.md`](RESEARCH_FRAME.md) — scientific question, multiscale logic and the role of the decision-aware AI layer.
2. [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md) — compact snapshot of the current numerical results.
3. [`FIGURE_MAP.md`](FIGURE_MAP.md) — what each main figure is intended to establish.
4. [`MANUSCRIPT_SKELETON.md`](MANUSCRIPT_SKELETON.md) — current paper structure and argument flow.
5. [`AGENT_HARNESS.md`](AGENT_HARNESS.md) — deterministic multiscale harness and decision layer.
6. [`DATA_AND_CODE_AVAILABILITY.md`](DATA_AND_CODE_AVAILABILITY.md) — reproducibility and data/code map.

## Current scientific story

The manuscript is organized around four connected questions.

```text
Atomic ranking
    -> multiscale propagation
    -> industrial ranking
    -> backward design
```

The ammonia case establishes the main decision-frontier inversion: the intrinsic activity order **Ru > Os > Fe** becomes the optimized economic order **Fe > Ru > Os**. The full 15-metal ranking remains strongly correlated, showing that the important reshuffling is concentrated at the decision frontier rather than distributed uniformly across all candidates.

The uncertainty analysis then asks whether atomic-scale uncertainty changes engineering feasibility or the identity of the actionable candidates. Backward design converts Fe cost parity into a required Ru activity improvement and compares that requirement with the activity headroom available on the frozen scaling-consistent catalyst-property manifold.

The methanol case tests transfer to a different catalyst-to-process pathway. There, selectivity and methane formation couple strongly to purge, recycle and feed loss, producing a different route from upstream catalyst performance to economics. The Au/TiO2 control provides the complementary case in which a ranking is preserved under a monotonic downstream mapping.

The Agent work is evaluated separately as a decision-allocation problem. Its manuscript claim is not that the Agent always uses less computation. Under the frozen benchmark, the adaptive decision-recovery advantage below the fixed-policy completion threshold appears for the strong model tier and does not transfer uniformly to weaker tiers.

## Evidence hierarchy

When two files appear to summarize the same quantity, use this order:

1. frozen source/provenance bundle;
2. machine-readable result table or trace;
3. figure-generation code and canonical figure asset;
4. manuscript-facing summary document;
5. root README or other overview text.

The principal frozen scientific source bundles are under [`../provenance/`](../provenance/). Compact manuscript-facing data are under [`../data/`](../data/), and canonical or manuscript-ready figure assets are under [`../figures/`](../figures/).

## Version families

Version labels are family-specific. The current principal labels are:

- **NH3-FINAL-1.1** — canonical ammonia model;
- **MEOH-D01-v3** — canonical methanol explicit-loop case;
- **Au/TiO2-RP V1.1** — canonical rank-preservation control;
- **Au/TiO2-RP V1.3** — supporting semi-open robustness extension;
- **DISCOVER V1** — frozen formal Agent benchmark;
- **DISCOVER-BOUNDARY-C1** — confirmatory boundary extension on the unchanged V1 protocol.

Use [`VERSION_REGISTRY.md`](VERSION_REGISTRY.md) for the full naming registry.

## Detailed audit and provenance records

The repository retains detailed claim-to-evidence and protocol records because the manuscript combines several model scales and benchmark families. These files are not the recommended first reading path, but they are the authoritative place to resolve provenance questions.

Key records include:

- [`CLAIM_EVIDENCE_AUDIT_2026-09-10.md`](CLAIM_EVIDENCE_AUDIT_2026-09-10.md)
- [`NH3_FINAL_1_1_PROVENANCE_POINTER.md`](NH3_FINAL_1_1_PROVENANCE_POINTER.md)
- [`NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`](NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md)
- [`CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md)
- DISCOVER/C1 result and metric-definition documents in this directory.

## Current production state

The core NH3, methanol and rank-preservation scientific results are frozen for manuscript production. Current work is focused on manuscript integration, figure presentation, caption consistency, reproducibility packaging and the final Agent figure/caption boundary.