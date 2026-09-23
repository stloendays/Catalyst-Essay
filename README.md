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

For Fe under the frozen 1,000-draw descriptor uncertainty propagation, feasibility is **79.9%**, economic Top-1 probability is **68.1%**, atomic-to-economic Top-1 survival is **28.2%**, and Top-3 actionable probability is **94.0%**. A separate preregistered 5,000-draw cost-side Monte Carlo gives **P(C_Fe < C_Ru) = 1.000**.

Full process reoptimization gives a canonical activity-only Ru-to-Fe parity requirement of approximately **201-fold**. Under joint cost uncertainty, alpha* has p05 / median / p95 = **70.78x / 174.27x / 462.00x**. Scaling-consistent activity headroom is **1.090x at 673 K** and at most **2.525x** over the frozen process-state library.

A direct price counterfactual changes the mechanism interpretation: setting the Ru metal price equal to Fe = **8 USD/kg** and reoptimizing all 14,136 process states gives Ru = **14.712 USD/t NH3** at **425 C / 170 bar**, **0.580 USD/t below Fe**. The baseline inversion therefore reflects **metal cost coupled to process reoptimization**, rather than process penalties that would keep Fe ahead even if the two metals had equal purchase price.

### MeOH: a selectivity-recycle pathway

The **MEOH-D01-v3** case evaluates four Re/TiO2 catalyst-temperature states through an explicit recycle/separation loop. Using STY per g Re as the upstream screening metric, the four-state comparison gives **rho = 0.20**, **tau = 0**, and **3/6 pairwise inversions**; the upstream winner falls to economic rank #3. The 2026-09-20 cost-parameter Monte Carlo retains the canonical economic order in **5,000/5,000** draws.

At the 5 wt% Re / 250 C benchmark, local leverage is **0.00289** for STY, **0.05883** for single-pass conversion, and **0.37579** for CH4 suppression. The dominant tested pathway therefore runs through selectivity, feed loss, purge and recycle.

### Rank preservation is also possible

The literature-calibrated **Au/TiO2-RP V1.1** control preserves the complete 2-6 nm activity ranking after downstream propagation:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full order

This control shows that multiscale propagation does not intrinsically force ranking inversion.

### Decision-aware Agent workflow

**DISCOVER V1** and **DISCOVER-BOUNDARY-C1** test whether the multiscale decision framework can be executed as a reusable, budget-aware workflow rather than as a manually scripted one-off analysis. A complete decision is the frozen primary endpoint `full_decision_correct = winner_correct ∧ pair_decision_correct ∧ reachability_correct`; numerical recovery of the backward parity multiplier is scored separately as a secondary quantitative endpoint. The deterministic fixed-VOI policy reaches the complete decision at **206 CU**.

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

Under the canonical narrow-window rule, allocation at 175 CU occurs in **20/20 strong**, **0/20 mini** and **0/20 nano** runs. The primary decision endpoint and the quantitative target separate: strong adaptive reaches **20/20 complete decisions at 75 CU**, whereas the canonical **201.22x** backward parity target reaches **20/20 at 225 CU**.

For the strong tier, **75 CU** is the lowest tested stable complete-decision budget. Under a non-binding 5000-CU allowance, median decision-stable spend is **566 CU**, followed by a median **148 CU** post-stability overrun to **714 CU** final spend; canonical narrow-window use is **0/20**. The protocol-complete oracle minimum is **22 CU** (with a separate 7-CU scorer-only floor), so 75 CU is **3.41x** the manuscript-facing oracle and the fixed-policy threshold of 206 CU is **9.36x**. The immediate benchmark claim remains model-tier- and budget-dependent, while the broader methodological role is **workflow scalability**: deterministic reaction modules carry the science and the Agent reuses the same decision logic to orchestrate repeated screening tasks.

## Scientific interpretation

```text
NH3
intrinsic activity + metal cost
 -> catalyst inventory + preferred operating regime
 -> compression / reactor / equipment burden
 -> decision-frontier inversion

MeOH
selectivity
 -> reactant loss / gas accumulation
 -> purge / recycle / compression
 -> catalyst-state ranking reshuffle

Au/TiO2
common monotonic downstream mapping
 -> rank preservation
```

The NH3 and MeOH systems use different frozen downstream economic objectives; absolute cost values are not compared across reactions. The transferable object is the catalyst-to-process coupling topology.

The central question is **which catalyst-to-process coupling determines whether an upstream ranking survives, reshapes or inverts**.

## Repository map

```text
README.md                project overview and main results
STATUS.md                current production state

docs/                    scientific frame, manuscript map, methods and audit records
  README.md              recommended reading order
  RESULTS_AT_A_GLANCE.md current numerical summary
  FIGURE_MAP.md          six-figure manuscript architecture and source-panel mapping
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

Author-level manuscript decisions are recorded in [`docs/MANUSCRIPT_EDITORIAL_LOCKS.md`](docs/MANUSCRIPT_EDITORIAL_LOCKS.md); semantic reader-facing names are defined in [`docs/SCIENTIFIC_NAMING.md`](docs/SCIENTIFIC_NAMING.md).

1. [`docs/RESEARCH_FRAME.md`](docs/RESEARCH_FRAME.md)
2. [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md)
3. [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md)
4. [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md)
5. [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md)

## Current scientific families

Reader-facing names are semantic rather than version-based. The complete mapping to historical provenance identifiers is in [`docs/SCIENTIFIC_NAMING.md`](docs/SCIENTIFIC_NAMING.md).

| Family | Reader-facing name | Historical provenance key | Role |
|---|---|---|---|
| Ammonia | **Ammonia process–economics model** | `NH3-FINAL-1.1` | primary ammonia model |
| Methanol | **Methanol recycle–economics model** | `MEOH-D01-v3` | explicit recycle/separation case |
| Rank-preservation control | **Au/TiO₂ rank-preservation control** | `Au/TiO2-RP V1.1` | primary control |
| Rank-preservation robustness | **Au/TiO₂ semi-open robustness extension** | `Au/TiO2-RP V1.3` | supporting extension |
| Agent | **Adaptive Catalyst Screening Agent (ACSA)** | `DISCOVER V1` | reusable execution layer |
| Agent compute-budget study | **ACSA budget-boundary study** | `DISCOVER-BOUNDARY-C1` | confirmatory budget extension |

The principal frozen source bundles are under [`provenance/`](provenance/). Current manuscript-facing values are under [`data/`](data/), and figure assets/renderers are under [`figures/`](figures/).

Superseded conclusions and intermediate values are kept out of the active result tables; the retirement record is [`docs/RETIRED_RESULTS.md`](docs/RETIRED_RESULTS.md), while frozen provenance, audit files and Git history remain available for traceability.

## Current production state

The audited baseline comprises the **ammonia process–economics model, methanol recycle–economics model, Au/TiO₂ rank-preservation control and ACSA budget-boundary study**; historical provenance keys are listed above. The three supervisor-requested analyses from **2026-09-20 are complete**: Ru-price equalization/cost decomposition, joint cost-parameter Monte Carlo, and Agent oracle-CU normalization.

Results and manuscript-facing extension data are under [`analysis/supervisor_2026_09_20/`](analysis/supervisor_2026_09_20/); the request/closure record is [`docs/SUPERVISOR_FEEDBACK_2026-09-20.md`](docs/SUPERVISOR_FEEDBACK_2026-09-20.md). Existing frozen provenance is preserved. The current integrated manuscript draft is [`docs/MANUSCRIPT_MAIN_TEXT.md`](docs/MANUSCRIPT_MAIN_TEXT.md). The publication-facing architecture remains six composite main figures, with source-panel mapping in [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md) and captions in [`docs/MAIN_FIGURE_CAPTIONS.md`](docs/MAIN_FIGURE_CAPTIONS.md). The current draft keeps the physical-science attribution unchanged and presents ACSA as the scaling layer that makes the deterministic ranking–parity–reachability analysis reusable across repeated screening tasks; the budget study explains how search compression changes with the available computation.
