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

The benchmark is designed to test **decision allocation**, not merely tool use. The relevant question is not “can an LLM call the workflow?” but “given limited computational budget, does it spend calculation where it changes the downstream industrial decision?”

## Repository map

```text
.
├── README.md
├── STATUS.md
├── docs/
│   ├── RESEARCH_FRAME.md
│   └── AGENT_HARNESS.md
└── data/
    ├── README.md
    ├── canonical_results_2026-09-06.csv
    └── discover_benchmark_2026-09-06.csv
```

## Current manuscript logic

The project is organized around five linked claims:

1. **Atomic and economic catalyst rankings can diverge at the decision frontier.**
2. **Multiscale uncertainty is not monotonically amplified**; kinetics can amplify energetic uncertainty, while equilibrium, reactor and process bottlenecks can absorb it.
3. **Backward design distinguishes a useful catalyst target from an unreachable one.**
4. **Economic leverage is pathway-specific rather than universal across reactions.**
5. **A decision-aware AI harness can allocate limited computation according to downstream decision value.**

See [`docs/RESEARCH_FRAME.md`](docs/RESEARCH_FRAME.md) and [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md) for the current research and AI framing.

## Status

The latest frozen scientific model is **NH3-FINAL-1.1**. The current benchmark snapshot is dated **2026-09-06**. Cross-model stability and a negative-reaction control are the next validation layer recorded in the project plan.

---

*Research snapshot; values in this repository track the current canonical project state rather than the archived NH3-FINAL-1.0 numbers.*
