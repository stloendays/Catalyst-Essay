# Catalyst-Essay

**From atomic catalyst ranking to industrial decision-making.**

Catalyst discovery is usually optimized with atomic-scale or intrinsic-performance proxies, while deployment is decided by reactor, process and economic constraints. This project studies how catalyst rankings propagate across those scales, where the ranking changes, and how an industrial target can be mapped backward into a required catalyst-property region.

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

### NH3: decision-frontier ranking inversion

Under the frozen **NH3-FINAL-1.1** model:

```text
intrinsic activity:  Ru > Os > Fe
economic ranking:    Fe > Ru > Os
```

| Catalyst | Cost (USD/t NH3) |
|---|---:|
| Fe | **15.292** |
| Ru | **22.031** |
| Os | **25.832** |

The Top-3 Spearman correlation is **-0.50**, while the raw full-15-metal correlation is **0.929**. The ranking conflict is concentrated at the decision frontier rather than across the complete screen.

For Fe under the frozen 1,000-draw uncertainty propagation, feasibility is **79.9%**, Top-1 survival is **28.2%**, and Top-3 actionable probability is **94.0%**.

Full process reoptimization gives an activity-only Ru-to-Fe parity requirement of approximately **201-fold**. Scaling-consistent activity headroom is **1.090x at 673 K** and at most **2.525x** over the frozen process-state library, placing the parity target outside the current reachable activity manifold.

### MeOH: a selectivity-recycle pathway

The **MEOH-D01-v3** case evaluates four Re/TiO2 catalyst-temperature states through an explicit recycle/separation loop. Using STY per g Re as the upstream screening metric, the four-state comparison gives **rho = 0.20**, **tau = 0**, and **3/6 pairwise inversions**; the upstream winner falls to economic rank #3.

At the 5 wt% Re / 250 C benchmark, local leverage is **0.00289** for STY, **0.05883** for single-pass conversion, and **0.37579** for CH4 suppression. The dominant tested pathway therefore runs through selectivity, feed loss, purge and recycle.

### Rank preservation is also possible

The literature-calibrated **Au/TiO2-RP V1.1** control preserves the complete 2-6 nm activity ranking after downstream propagation:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full order

This control shows that multiscale propagation does not intrinsically force ranking inversion.

### Decision-aware Agent benchmark

**DISCOVER V1** and **DISCOVER-BOUNDARY-C1** test decision allocation under a frozen scientific-compute interface. The deterministic fixed-VOI policy reaches the complete decision at **206 CU**.

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

For the strong tier, **75 CU** is the lowest tested stable complete-decision budget. Under a non-binding 5000-CU allowance, median final spend rises to **714 CU**. The supported claim is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy threshold**, not a universal raw-compute saving.

## Scientific interpretation

```text
NH3
activity -> catalyst inventory / reactor demand -> decision-frontier inversion

MeOH
selectivity -> feed loss / purge / recycle -> catalyst-state ranking reshuffle

Au/TiO2
monotonic downstream mapping -> rank preservation
```

The central question is **which catalyst-to-process coupling determines whether an upstream ranking survives, reshapes or inverts**.

## Repository map

```text
README.md                project overview and main results
STATUS.md                current production state

docs/                    scientific frame, manuscript map, methods and audit records
  README.md              recommended reading order
  RESULTS_AT_A_GLANCE.md current numerical summary
  FIGURE_MAP.md          F1-F10 scientific roles
  RETIRED_RESULTS.md     single note for superseded results

data/                    current machine-readable manuscript-facing datasets
figures/                 canonical/manuscript figure assets and renderers
provenance/              frozen source-harness provenance bundles
controls/                rank-preservation/control calculations
discover/                Agent benchmark harness and protocol material
ci/                      deterministic validation/replay scripts
artifacts/               validation outputs and reproducibility records
```

For a first review:

1. [`docs/RESEARCH_FRAME.md`](docs/RESEARCH_FRAME.md)
2. [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md)
3. [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md)
4. [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md)
5. [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md)

## Current version families

| Family | Current label | Role |
|---|---|---|
| Ammonia | **NH3-FINAL-1.1** | canonical frozen scientific model |
| Methanol | **MEOH-D01-v3** | canonical explicit-loop case |
| Rank-preservation control | **Au/TiO2-RP V1.1** | canonical control |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | supporting semi-open extension |
| Agent benchmark | **DISCOVER V1** | frozen formal benchmark |
| Agent boundary extension | **DISCOVER-BOUNDARY-C1** | confirmatory extension on unchanged V1 protocol |

The principal frozen source bundles are under [`provenance/`](provenance/). Current manuscript-facing values are under [`data/`](data/), and figure assets/renderers are under [`figures/`](figures/).

Superseded conclusions and intermediate values are kept out of the active result tables; the retirement record is [`docs/RETIRED_RESULTS.md`](docs/RETIRED_RESULTS.md), while frozen provenance, audit files and Git history remain available for traceability.

## Current production state

The scientific evidence and F1-F10 figure/caption set are locked except for publication-layout redraws. Current work is manuscript integration, R-based visual harmonization, Supporting Information organization and final submission packaging.
