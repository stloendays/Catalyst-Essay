# Catalyst-Essay

**From atomic catalyst ranking to industrial decision-making.**

Catalyst discovery is usually optimized at the atomic scale, while deployment is decided at the system scale. This project asks a different question:

> **How much of an atomic-scale catalyst ranking survives propagation through kinetics, catalyst inventory, reactor operation, recycle/separation and economics — and when does the ranking invert?**

The same framework is then run backward: an industrial cost target is mapped into the catalyst-property improvement required for parity, and the accessible scaling manifold is used to test whether that target is physically reachable.

This repository is a research-facing summary of the current canonical results and the decision-aware AI harness built around them.

## Scientific frame

```text
Forward propagation
DFT / descriptor
    -> scaling + BEP
    -> microkinetics (TOF + coverage)
    -> catalyst productivity / inventory
    -> reactor + process optimization
    -> economics
    -> industrial ranking

Backward design
industrial target
    -> required catalyst-property change
    -> scaling-manifold reachability

Decision-aware AI layer
industrial objective + compute budget
    -> interface-level decisions
    -> tool execution with shared state / provenance
    -> forward + backward evaluation
    -> next-calculation selection
```

The numerical models remain the source of physical and economic results. The AI layer is used where a numerical optimizer cannot decide which mechanism, representation or uncertainty-reduction calculation is worth pursuing.

## Current canonical snapshot

**Canonical ammonia model: `NH3-FINAL-1.1`** (promoted 2026-09-05).

| Result | Current value |
|---|---:|
| Atomic activity top-3 | Ru -> Os -> Fe |
| Economic top-3 | Fe -> Ru -> Os |
| Fe reduced catalyst-dependent cost | **15.292 USD/t NH3** |
| Ru reduced catalyst-dependent cost | **22.031 USD/t NH3** |
| Os reduced catalyst-dependent cost | **25.832 USD/t NH3** |
| Ru / Fe cost ratio | **1.441** |
| Top-3 Spearman rho | **-0.50** |
| Top-3 Kendall tau | **-0.33** |
| Full 15-metal Spearman rho | **0.929** |
| Fe feasibility, 1000-draw MC | **79.9%** |
| Fe Top-3 actionable probability | **94.0%** |
| Ru activity-only break-even target | **201.22x** |
| Scaling-consistent Ru activity headroom, 673 K | **1.090x** |
| Maximum activity headroom over process-state library | **2.525x** |

The central ammonia result is therefore not simply that Fe is cheaper. The **activity ranking reverses at the industrial decision frontier**, while the global 15-metal correlation remains high. The inversion is concentrated among the candidates that actually matter for selection.

The backward-design result is equally important: the Ru activity increase required to reach Fe cost parity is about **201-fold**, whereas the scaling-consistent activity headroom is at most about **2.53-fold** in the current process-state library. Under the frozen model, an activity-only route to parity is therefore unreachable.

## Cross-reaction economic leverage

The same multiscale logic is being tested across reactions rather than assuming a universal inversion mechanism.

For the current CO2-to-methanol benchmark, the local economic leverages are:

| Catalyst-controlled variable | Local leverage |
|---|---:|
| STY | 0.00289 |
| Single-pass conversion | 0.05883 |
| CH4 suppression | **0.37579** |

After aligning the cost denominator, the normalized **MeOH CH4-suppression / NH3 TOF leverage ratio is 273-410**, with a midpoint near **328**. This supports a pathway-specific interpretation: ammonia activity mainly acts through the **activity -> inventory / reactor-demand** pathway, while methanol selectivity acts through **feed loss -> purge / recycle**.

## Rank-preservation control: Au/TiO2 CO oxidation

A separate fixed-condition control tests whether the multiscale implementation can preserve an upstream ordering when the downstream mapping is physically monotonic and no competing process-severity or topology penalty is introduced.

The V1.1 control uses literature-anchored Au/TiO2 CO-oxidation data at a common process condition. The candidate states differ only in Au particle size across **2, 3, 4, 5 and 6 nm**; active element, support, feed, temperature, pressure and process topology are held fixed.

| Au diameter | Mass activity (umol CO gcat^-1 s^-1) | Required catalyst (mg) | Burden vs best |
|---:|---:|---:|---:|
| 2 nm | 9.6548 | 19.505 | **1.000x** |
| 3 nm | 4.4686 | 42.143 | **2.161x** |
| 4 nm | 2.5869 | 72.797 | **3.732x** |
| 5 nm | 1.6930 | 111.235 | **5.703x** |
| 6 nm | 1.1973 | 157.284 | **8.064x** |

The activity and downstream burden rankings are both **2 > 3 > 4 > 5 > 6 nm**, with **Spearman rho = 1.000**, **Kendall tau = 1.000**, and **0 pairwise inversions**. Across 10,000 predefined literature/geometry draws, the full ranking is preserved in every draw.

The literature calibration is intentionally substantial rather than cosmetic: the reference particle size changes from 2.00 to 2.10 nm (+5.0%), the nominal TOF size exponent from 1.70 to 0.90 (-47.1%), the effective mass-activity exponent from 2.70 to 1.90 (-29.6%), and the 6 nm / 2 nm required-mass ratio contracts from 19.42x to 8.064x (-58.5%). The ordering remains unchanged.

Figure: [`figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg`](figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg). Source data: [`data/rank_preservation_control_v1_1.csv`](data/rank_preservation_control_v1_1.csv).

### Semi-open robustness extension: V1.3

V1.1 remains the **canonical rank-preservation control**, but a semi-open robustness extension now tests whether preservation survives when the operating point is no longer perfectly fixed. In V1.3, each particle-size state independently searches temperature and O2/CO ratio inside a literature-constrained low-temperature envelope, while candidate-specific activity-prefactor and apparent-activation-energy perturbations are allowed. Catalyst chemistry and process topology remain common.

Under the **primary 273.15–293.15 K moderate-stress case**, exact full ordering is preserved in **92.16%** of 10,000 optimization draws, with mean **Spearman rho = 0.99214** and **99.98%** of draws retaining rho >= 0.9. Under the wider **273.15–313.15 K** sensitivity, exact preservation falls to **72.62%**, while mean rho remains **0.96802** and **97.56%** of draws retain rho >= 0.9.

This supporting result changes the interpretation in an important but limited way: **rank preservation does not require a perfectly fixed operating point**. Moderate candidate-specific kinetic and operating freedom can produce occasional local reshuffling while leaving the overall rank structure strongly preserved. V1.3 is not promoted to the canonical control because its process-penalty terms are generic monotone penalties rather than a fully literature-derived industrial TEA.

Full note: [`docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`](docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md). Reproducibility: [`data/rank_preservation_semiopen_v1_3.py`](data/rank_preservation_semiopen_v1_3.py) and [`data/rank_preservation_semiopen_v1_3_summary.csv`](data/rank_preservation_semiopen_v1_3_summary.csv).

### MeOH candidate-state ranking inversion (restored 2026-09-07)

Within the D01 v3 explicit loop the intrinsic-productivity ranking of the four Re/TiO2 states (1 %-250 °C > 1 %-200 °C > 5 %-200 °C > 5 %-250 °C by STY per g Re) does not survive propagation: the economic order is 5 %-200 °C (943 €/t) > 1 %-200 °C (967) > 1 %-250 °C (975) > 5 %-250 °C (1258); Spearman ρ = 0.20, Kendall τ = 0, 3 of 6 pairs inverted, and the upstream winner falls to third. Cost follows CH4 selectivity through H2 feed loss and loop accumulation, not productivity. Data and rebuilt figure: [`docs/MEOH_RANKING_INVERSION.md`](docs/MEOH_RANKING_INVERSION.md), [`figures/meoh/`](figures/meoh/).

![MeOH upstream to economic ranking](figures/meoh/MeOH_F03_UpstreamToEconomicRanking_D01v3.png)

## Decision-aware DISCOVER benchmark

DISCOVER is a closed-book, budgeted benchmark of scientific decision allocation. The agent receives an anonymous candidate set and can choose among 11 fine-grained scientific actions rather than requesting the entire answer at once.

The V1 protocol was frozen before formal evaluation. The task, prompt, action schema, cost model, scorer, stopping rule and fixed policy-D constants are SHA-pinned; changing any pinned component defines DISCOVER V2. Failures are recorded rather than tuned away.

### Formal strong-tier precursor

The original formal policy-E run used the strong tier and established that the full decision chain was executable under V1:

- `1 CU = 1000` MKM state solves (measured once at about 21.8 ms in the benchmark cost model).
- 70 policy-E runs = 5 runs x 7 budgets x anonymous/named variants.
- Anonymous complete decision: **35/35**.
- Exact break-even recovery: **34/35**.
- 0 infrastructure retries and 0 action errors.

These single-tier results are provenance for the later cross-model test; they are **not** the final general Agent claim.

### Cross-model stability — current Agent result (2026-09-06/07)

The same frozen protocol was evaluated across three capability tiers. Policy E used five independent runs at each of seven budgets (**200, 250, 300, 500, 800, 1200 and 2000 CU**). The two weaker tiers contributed 140 new anonymous/named traces; the strong-tier V1 traces were reused and re-scored, not re-run. Frozen hashes passed before and after the sweep; there were 0 API retries and 0 driver exceptions.

| Anonymous task, pooled over 7 budgets (n = 35 per tier) | gpt-5.4-nano | gpt-5.4-mini | gpt-5.5 |
|---|---:|---:|---:|
| P(winner correct) | 29/35 | 31/35 | 35/35 |
| P(pair decision correct) | 24/35 | 20/35 | 35/35 |
| P(reachability correct) | 6/35 | 15/35 | 35/35 |
| **P(full decision correct)** | **6/35** | **15/35** | **35/35** |
| unnecessary-CU fraction (mean) | 0.46 | 0.30 | 0.19 |

The complete decision requires the chain:

```text
ranking / economic winner
    -> decision-pair selection
    -> backward design
    -> reachability verdict
```

The pooled tier trend in P(full) is strong (**Cochran-Armitage Z = 6.95**). The strong tier executes the complete decision-aware workflow at every tested budget, whereas weaker tiers frequently recover the winner but fail later in pair formation, BACKWARD execution or reachability formulation.

This is the **positive workflow-execution result**: complete decision recovery rises from **6/35 -> 15/35 -> 35/35** as underlying model capability increases.

### Pre-registered E versus fixed-VOI D — negative result

A stronger hypothesis was pre-registered: adaptive policy E should reliably outperform the deterministic fixed-VOI policy D. That hypothesis was **not supported across model tiers**.

- The repeatable adaptive-scope advantage at 200 CU appears only in the strong tier.
- Nano and mini never reproduce the narrow-window strategy (0/140 weak-tier runs versus 7/70 strong-tier runs, all at 200 CU).
- The pre-registered Agent-specific Go criterion — E beats D in at least 4/5 runs at a budget and in at least two model tiers — is **not met**.
- The negative result is retained; no frozen V1 protocol component was changed to make E look better.

The supported conclusion is therefore:

> **A strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over a fixed-VOI strategy is model-capability dependent rather than universal.**

The negative result rejects only the general claim that **Agent E universally outperforms D**. It does not reject the decision-aware framework itself.

Full report: [`docs/CROSS_MODEL_DISCOVER_V1.md`](docs/CROSS_MODEL_DISCOVER_V1.md); statistics: [`docs/CROSS_MODEL_STATS_V1.md`](docs/CROSS_MODEL_STATS_V1.md); Agent rationale: [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md); figures: [`figures/discover_cross_model/`](figures/discover_cross_model/).

![Cross-model outcomes with Wilson 95 % CI](figures/discover_cross_model/X9_wilson_ci_pooled.png)

## Repository map

```text
.
├── README.md
├── STATUS.md
├── controls/
│   ├── au_tio2_rank_preservation_v1.py
│   ├── au_tio2_rank_preservation_v1_1.py
│   └── au_tio2_rank_preservation_v1_1_config.json
├── docs/
│   ├── RESEARCH_FRAME.md
│   ├── AGENT_HARNESS.md
│   ├── FIGURE_MAP.md
│   ├── MANUSCRIPT_SKELETON.md
│   ├── RESULTS_AT_A_GLANCE.md
│   ├── REFERENCES_STARTER.md
│   ├── CROSS_MODEL_DISCOVER_V1.md
│   ├── CROSS_MODEL_STATS_V1.md
│   ├── RANK_PRESERVATION_CONTROL_V1_LITERATURE_VALIDATION.md
│   ├── RANK_PRESERVATION_CONTROL_V1_PREREGISTRATION.md
│   ├── RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md
│   ├── RANK_PRESERVATION_CONTROL_V1_1_RESULT.md
│   └── RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md
├── figures/
│   ├── README.md
│   ├── discover_cross_model/
│   └── rank_preservation_control/
└── data/
    ├── README.md
    ├── canonical_results_2026-09-06.csv
    ├── discover_benchmark_2026-09-06.csv
    ├── rank_preservation_control_v1_1.csv
    ├── rank_preservation_semiopen_v1_3.py
    ├── rank_preservation_semiopen_v1_3_summary.csv
    ├── cross_model_scores_2026-09-06.csv
    ├── cross_model_failure_matrix_2026-09-06.csv
    ├── cross_model_stats_2026-09-07.csv
    ├── cross_model_metadata_2026-09-06.json
    ├── discover_frozen_v1_hashes.json
    └── cross_model_*.py
```

## Reading guide

For a fast project overview, read [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md).

For the manuscript storyline, read [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md).

For the nine-figure scientific map and current headline values, read [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md).

For the AI / agent rationale and benchmark design, read [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md).

For citation planning, read [`docs/REFERENCES_STARTER.md`](docs/REFERENCES_STARTER.md).

## Current manuscript logic

The project is organized around six linked claims:

1. **Atomic and economic catalyst rankings can diverge at the decision frontier.**
2. **Multiscale uncertainty is not monotonically amplified**; kinetics can amplify energetic uncertainty, while equilibrium, reactor and process bottlenecks can absorb it.
3. **Backward design distinguishes a useful catalyst target from an unreachable one.**
4. **Economic leverage is pathway-specific rather than universal across reactions.**
5. **The same multiscale implementation can preserve an upstream ranking under a monotonic mapping, and that preservation remains robust to moderate semi-open kinetic and operating freedom.**
6. **Decision-aware workflow execution is model-capability dependent; adaptive policy E does not show universal cross-model superiority over fixed-VOI D.**

## Status

The latest frozen scientific model is **NH3-FINAL-1.1**. The current benchmark snapshot is dated **2026-09-07**: DISCOVER V1 formal and cross-model evaluations are complete, the literature-calibrated Au/TiO2 rank-preservation control V1.1 is integrated as the canonical framework counterpoint to the ammonia and methanol inversion cases, and V1.3 is retained as a supporting semi-open robustness extension rather than promoted to a replacement control.

---

*Research snapshot; values in this repository track the current canonical project state rather than the archived NH3-FINAL-1.0 numbers.*
