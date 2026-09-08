# DISCOVER V1 boundary-focused reanalysis

Date: 2026-09-08

This document is a post-hoc reanalysis of the frozen DISCOVER V1 aggregate results. It does not modify, rescore, or rerun any frozen trace, and it does not replace the pre-registered Agent-specific Go criterion.

## Question

The original E-vs-D framing asks whether adaptive policy E is generally superior to deterministic fixed-VOI policy D. The frozen V1 result does not support that universal claim across model tiers.

The present reanalysis asks a narrower mechanistic question:

> Is the value of adaptive scientific-compute allocation concentrated in a finite budget regime, and is that value gated by model capability?

Two observables are used.

1. Complete-decision advantage

   Delta P_full(B) = P_full^E(B) - P_full^D(B)

2. Strong-model total-compute difference

   CU saving(B) = [CU_D(B) - CU_E(B)] / CU_D(B)

The second quantity is descriptive because the current frozen scorer does not expose a direct `CU_to_full_decision` metric.

## Frozen-data observations

### Complete-decision advantage

Policy D is incomplete at 200 CU and complete from 250 CU upward. The strong model under policy E is complete in all 35 anonymous runs across the seven budgets.

Therefore the observed strong-model Delta P_full is:

- 200 CU: +1.0
- 250 CU: 0
- 300 CU: 0
- 500 CU: 0
- 800 CU: 0
- 1200 CU: 0
- 2000 CU: 0

The weak and medium tiers do not show the same 200-CU effect. This reproduces the existing V1 conclusion that the 200-CU adaptive-scope advantage is strong-tier-only.

This is currently an isolated observed spike, not yet evidence for a smooth budget-localized peak. Each E cell has only n=5 runs.

### Strong-model compute use

Mean total CU spent by strong E versus deterministic D:

| Budget | D spent CU | Strong E spent CU | Relative E saving |
|---:|---:|---:|---:|
| 200 | 193.0 | 182.4 | +5.5% |
| 250 | 247.0 | 218.0 | +11.7% |
| 300 | 281.0 | 248.0 | +11.7% |
| 500 | 281.0 | 267.6 | +4.8% |
| 800 | 281.0 | 496.0 | -76.5% |
| 1200 | 281.0 | 699.2 | -148.8% |
| 2000 | 281.0 | 791.4 | -181.6% |

This shows two regimes in the frozen data:

- 250-500 CU: strong E reaches the same complete decision as D while using less total compute on average.
- >=800 CU: strong E over-confirms and spends substantially more compute than D even though both are already correct.

The high-budget loss of efficiency is consistent with the existing failure analysis, which reports over-confirmation in the strong tier.

## What can and cannot be claimed now

Supported now:

> Adaptive allocation in the strong model has an observed low-budget decision-completion advantage at 200 CU and a descriptive compute-saving window at 250-500 CU, while its efficiency advantage disappears and reverses at high budgets because of over-confirmation.

Not supported now:

> E has a statistically established smooth advantage peak around 200 CU.

The current 200-CU effect is one cell with n=5. Its local shape is unresolved.

## Confirmatory experiment needed

A boundary-focused confirmatory extension should keep the frozen scientific task, action schema, scorer, and D policy unchanged, and add only new policy-E repetitions near the observed transition. Because this is a new confirmatory extension rather than a reanalysis of the original V1 sample, it must be named separately rather than silently folded into the original 35-run-per-tier result.

Recommended first pass:

- budgets: 150, 175, 200, 225, 250 CU;
- primary tier: strong model;
- repetitions: at least 20 independent runs per budget;
- secondary replication: nano and mini at the same budgets if the paper intends to claim capability gating;
- primary endpoint: full scientific decision correctness;
- secondary endpoint: total CU spent;
- new preferred endpoint if it can be computed without changing the scientific task: `CU_to_full_decision`, defined as the first point at which winner, pair decision, and reachability are simultaneously correct and remain correct thereafter.

Expected diagnostic patterns:

- genuine budget-localized adaptive value: adjacent budgets form a reproducible positive region rather than a single-cell spike;
- sampling accident: the 200-CU point collapses toward neighboring budgets;
- capability gating: the strong tier shows a coherent local region while weak tiers remain near zero or fail to reproduce it.

## Figure interpretation

The recommended Agent figure should not plot raw E and D curves as the main message. It should plot the contrast directly:

- panel A: Delta P_full versus CU budget for each tier;
- panel B: strong-model compute saving versus CU budget, with the 200-CU point explicitly marked as a region where D does not complete the full decision.

The current plots are diagnostic, not final manuscript evidence, because the local transition has not yet been replicated with adequate n.
