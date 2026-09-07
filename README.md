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

## Decision-aware DISCOVER benchmark

The current AI benchmark is deliberately closed-book and budgeted. The agent receives an anonymous candidate set and can choose among 11 fine-grained scientific actions rather than requesting the entire answer at once.

Key frozen benchmark facts:

- `1 CU = 1000` MKM state solves (measured once at about 21.8 ms in the benchmark cost model).
- The formal policy-E study contains **70 runs**: 5 seeds x 7 budgets x anonymous/named variants.
- Together with frozen A-D baselines, the scorer evaluates **392 traces**.
- **0 infrastructure retries** and **0 action errors** were recorded.
- On the anonymous task, policy E produced a **complete correct decision in 35/35 runs**, including the 200-CU budget; the exact break-even target was recovered in **34/35**.
- At 250-500 CU, policy E and the fixed-VOI policy D are not distinguishable in decision quality; policy E used **218-268 CU** versus **247-281 CU** for D.
- A zero-tool prior probe shows why anonymization matters: winner-only accuracy can be guessed from price priors even when inversion, break-even and reachability are all wrong.

### Cross-model stability (2026-09-06/07)

The same frozen protocol was re-run with policy E on two weaker tiers of the same model family (5 runs x 7 budgets x anonymous/named = 70 runs per model; gpt-5.5 traces reused, not re-run). Frozen hashes were verified before and after; nothing was retried or tuned.

| Anonymous task, pooled over 7 budgets (n = 35 per tier) | gpt-5.4-nano | gpt-5.4-mini | gpt-5.5 |
|---|---:|---:|---:|
| P(winner correct) | 29/35 | 31/35 | 35/35 |
| P(pair decision correct) | 24/35 | 20/35 | 35/35 |
| P(reachability correct) | 6/35 | 15/35 | 35/35 |
| **P(full decision correct)** | **6/35** | **15/35** | **35/35** |
| unnecessary-CU fraction (mean) | 0.46 | 0.30 | 0.19 |

- The tier trend in P(full) is strong (Cochran–Armitage Z = 6.95; nano vs mini Fisher p = 0.036; mini vs gpt-5.5 p = 4e-8).
- In both weak tiers the failure is **entirely the reachability step**: P(reach) equals P(full) cell by cell, while the winner is recovered at every budget ≥ 500 CU.
- Winner accuracy does not separate nano from mini (p = 0.73); it is price-prior-recoverable, as the zero-tool probe predicted.
- The 200-CU adaptive narrow-window shortcut appears only in gpt-5.5 (7/70 runs vs 0/140 in the weak tiers).
- The pre-registered agent-specific Go (E beats fixed-VOI D in ≥ 4/5 runs at one budget in ≥ 2 tiers) is **not met**; only gpt-5.5 at 200 CU is repeatable, and D's zero regret cannot be beaten. This is recorded as a negative result.
- With n = 5 per cell, per-budget differences below 5/5 vs ≤ 1/5 are not resolvable; claims rest on the pooled and ≤ 300 / ≥ 500 CU strata.

Full report: [`docs/CROSS_MODEL_DISCOVER_V1.md`](docs/CROSS_MODEL_DISCOVER_V1.md); statistics: [`docs/CROSS_MODEL_STATS_V1.md`](docs/CROSS_MODEL_STATS_V1.md); figures: [`figures/discover_cross_model/`](figures/discover_cross_model/).

![Cross-model outcomes with Wilson 95 % CI](figures/discover_cross_model/X9_wilson_ci_pooled.png)

The benchmark is designed to test **decision allocation**, not merely tool use. The relevant question is not “can an LLM call the workflow?” but “given limited computational budget, does it spend calculation where it changes the downstream industrial decision?”

## Repository map

```text
.
├── README.md
├── STATUS.md
├── docs/
│   ├── RESEARCH_FRAME.md
│   ├── AGENT_HARNESS.md
│   ├── FIGURE_MAP.md
│   ├── MANUSCRIPT_SKELETON.md
│   ├── RESULTS_AT_A_GLANCE.md
│   ├── REFERENCES_STARTER.md
│   ├── CROSS_MODEL_DISCOVER_V1.md
│   └── CROSS_MODEL_STATS_V1.md
├── figures/
│   ├── README.md
│   └── discover_cross_model/        (X1–X9 PNG)
└── data/
    ├── README.md
    ├── canonical_results_2026-09-06.csv
    ├── discover_benchmark_2026-09-06.csv
    ├── cross_model_scores_2026-09-06.csv
    ├── cross_model_failure_matrix_2026-09-06.csv
    ├── cross_model_stats_2026-09-07.csv
    ├── cross_model_metadata_2026-09-06.json
    ├── discover_frozen_v1_hashes.json
    └── cross_model_*.py               (read-only analysis scripts)
```

## Reading guide

For a fast project overview, read [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md).

For the manuscript storyline, read [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md).

For the nine-figure scientific map and current headline values, read [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md).

For the AI / agent rationale and benchmark design, read [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md).

For citation planning, read [`docs/REFERENCES_STARTER.md`](docs/REFERENCES_STARTER.md).

## Current manuscript logic

The project is organized around five linked claims:

1. **Atomic and economic catalyst rankings can diverge at the decision frontier.**
2. **Multiscale uncertainty is not monotonically amplified**; kinetics can amplify energetic uncertainty, while equilibrium, reactor and process bottlenecks can absorb it.
3. **Backward design distinguishes a useful catalyst target from an unreachable one.**
4. **Economic leverage is pathway-specific rather than universal across reactions.**
5. **A decision-aware AI harness can allocate limited computation according to downstream decision value.**

## Status

The latest frozen scientific model is **NH3-FINAL-1.1**. The current benchmark snapshot is dated **2026-09-07**: the single-model DISCOVER V1 study and its cross-model stability check (three tiers, 210 policy-E runs) are complete. The negative-reaction control is the next validation layer recorded in the project plan and has not been started.

---

*Research snapshot; values in this repository track the current canonical project state rather than the archived NH3-FINAL-1.0 numbers.*
