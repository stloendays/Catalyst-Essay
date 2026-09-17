# Catalyst-Essay

**From atomic catalyst ranking to industrial decision-making.**

Catalyst discovery is usually optimized with atomic-scale or intrinsic-performance proxies, while deployment is decided by reactor, process and economic constraints. This project studies how catalyst rankings propagate across those scales, where the ranking changes, and how an industrial target can be mapped backward into a required catalyst-property region.

The project is organized around three scientific operations:

```text
Forward propagation
atomic descriptor / activity
    -> microkinetics
    -> catalyst productivity and inventory
    -> reactor / process optimization
    -> economics
    -> industrial ranking

Backward design
industrial target
    -> required catalyst-property improvement
    -> scaling-consistent reachable region

Decision-aware computation
current evidence
    -> choose the next admissible scientific action
    -> update ranking / feasibility / reachability
    -> stop, continue or redirect
```

## Main results

### 1. Ammonia: decision-frontier ranking inversion

Under the frozen **NH3-FINAL-1.1** model, the intrinsic activity top three are:

```text
Ru > Os > Fe
```

After catalyst-dependent reactor/process optimization and economic propagation, the order becomes:

```text
Fe > Ru > Os
```

with catalyst-dependent costs:

| Catalyst | Cost (USD/t NH3) |
|---|---:|
| Fe | **15.292** |
| Ru | **22.031** |
| Os | **25.832** |

The important feature is that the inversion is concentrated at the decision frontier. The Top-3 Spearman correlation is **-0.50**, whereas the raw full-15-metal Spearman correlation is **0.929**.

### 2. Uncertainty changes actionability more than the global ranking

For Fe under the frozen 1,000-draw uncertainty propagation:

- feasibility: **79.9%**;
- Top-1 survival: **28.2%**;
- Top-3 actionable probability: **94.0%**.

The analysis therefore tracks whether uncertainty changes feasibility or candidate selection, rather than treating uncertainty magnitude alone as the endpoint.

### 3. Backward design separates a useful target from a reachable target

Full process reoptimization gives an activity-only Ru-to-Fe parity requirement of approximately **201-fold**. The scaling-consistent activity headroom is only **1.090x at 673 K** and at most **2.525x** over the frozen process-state library.

The required target is therefore outside the current reachable activity manifold under the frozen model.

### 4. Methanol: a different catalyst-to-process pathway

The **MEOH-D01-v3** case evaluates four Re/TiO2 catalyst-temperature states through an explicit recycle/separation loop at 2% purge.

Using STY per g Re as the upstream screening metric:

```text
upstream ranking                     economic ranking
1 wt% Re / 250 C   #1               5 wt% Re / 200 C   #1
1 wt% Re / 200 C   #2      ->       1 wt% Re / 200 C   #2
5 wt% Re / 200 C   #3               1 wt% Re / 250 C   #3
5 wt% Re / 250 C   #4               5 wt% Re / 250 C   #4
```

The four-state comparison gives **rho = 0.20**, **tau = 0**, and **3/6 pairwise inversions**. The mechanistic pathway differs from ammonia: methane formation and selectivity couple to feed loss, purge and recycle.

At the 5 wt% Re / 250 C benchmark, local leverage is:

| Catalyst-controlled variable | Local leverage |
|---|---:|
| STY | 0.00289 |
| Single-pass conversion | 0.05883 |
| CH4 suppression | **0.37579** |

### 5. Rank preservation is also possible

The literature-calibrated **Au/TiO2-RP V1.1** control preserves the complete 2-6 nm activity ranking after the downstream monotonic mapping:

- Spearman rho = **1.000**;
- Kendall tau = **1.000**;
- pairwise inversions = **0**;
- 10,000/10,000 predefined literature-envelope draws preserve the full order.

This control establishes that multiscale propagation does not intrinsically force a ranking inversion.

### 6. Decision-aware Agent benchmark

**DISCOVER V1** and **DISCOVER-BOUNDARY-C1** test whether an AI decision layer can allocate a limited scientific-compute budget through the frozen multiscale harness.

The deterministic fixed-VOI policy reaches the complete decision at **206 CU**. At the two boundary cells used for the weak-tier transfer test:

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

The supported interpretation is a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy threshold**. It is not a universal raw-compute saving claim.

## Scientific interpretation

Across the current cases, the same multiscale framework produces three distinct outcomes:

```text
NH3
activity -> catalyst inventory / reactor demand -> decision-frontier inversion

MeOH
selectivity -> feed loss / purge / recycle -> catalyst-state ranking reshuffle

Au/TiO2
monotonic downstream mapping -> rank preservation
```

The central question is therefore not whether multiscale propagation always destroys atomic rankings, but **which catalyst-to-process coupling determines whether an upstream ranking survives, reshapes or inverts**.

## Repository map

```text
README.md                project overview and main results
STATUS.md                current production/freeze state

docs/                    scientific frame, manuscript map, methods and audit records
  README.md              recommended reading order
  RESEARCH_FRAME.md
  RESULTS_AT_A_GLANCE.md
  FIGURE_MAP.md
  MANUSCRIPT_SKELETON.md
  AGENT_HARNESS.md

data/                    compact machine-readable manuscript-facing datasets
figures/                 canonical and manuscript figure assets / renderers
provenance/              frozen source-harness provenance bundles
controls/                rank-preservation and control calculations
discover/                Agent benchmark harness and protocol material
ci/                      deterministic validation / replay scripts
artifacts/               validation outputs and reproducibility records
.github/workflows/        CI and figure-render workflows
```

For a first review, the shortest reading path is:

1. [`docs/RESEARCH_FRAME.md`](docs/RESEARCH_FRAME.md)
2. [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md)
3. [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md)
4. [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md)
5. [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md)

The detailed documentation index is [`docs/README.md`](docs/README.md).

## Current version families

| Family | Current label | Role |
|---|---|---|
| Ammonia | **NH3-FINAL-1.1** | canonical frozen scientific model |
| Methanol | **MEOH-D01-v3** | canonical explicit-loop case |
| Rank-preservation control | **Au/TiO2-RP V1.1** | canonical control |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | supporting semi-open extension |
| Agent benchmark | **DISCOVER V1** | frozen formal benchmark |
| Agent boundary extension | **DISCOVER-BOUNDARY-C1** | confirmatory extension on unchanged V1 protocol |

Version labels are family-specific. See [`docs/VERSION_REGISTRY.md`](docs/VERSION_REGISTRY.md) for the full registry.

## Reproducibility

The principal frozen source bundles are under [`provenance/`](provenance/). Compact manuscript-facing values are under [`data/`](data/), and figure assets/renderers are under [`figures/`](figures/).

For NH3-FINAL-1.1, the imported source-harness provenance has passed repository validation with **13/13 canonical anchors, 6/6 evidence classes, 6/6 figure mappings, 28/28 manifest files present and 0 source-manifest hash mismatches**. The validation and figure-lock records are retained under `docs/` and `artifacts/`.

The historical cross-reaction leverage ratio 273-410 is not used as a current quantitative manuscript result because its original metric implementation could not be established. The current cross-reaction comparison is therefore mechanistic/qualitative at the pathway level.

## Current production state

The core NH3, methanol and rank-preservation scientific results are frozen for manuscript production. Current work is focused on manuscript integration, publication-quality figure rendering, caption consistency, reproducibility packaging and finalizing the Agent figure/caption boundary.
