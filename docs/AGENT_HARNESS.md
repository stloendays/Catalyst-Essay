# Decision-aware AI harness

## Why the agent exists

The AI component is not intended to be a wrapper around a fixed DFT -> MKM -> reactor -> TEA script.

A fixed workflow already solves the deterministic numerical chain. The agent is useful only at interfaces where a numerical optimizer cannot determine the scientifically appropriate next action, for example:

- which admissible mechanism or active-site representation to use;
- whether an apparent difference is a model-version / unit / cost-boundary inconsistency;
- which uncertainty should be reduced next;
- whether a backward target is reachable;
- whether computation should stop because the decision is already resolved.

The central AI question is therefore:

> Given a limited compute budget, can the agent allocate calculations according to their value to the downstream industrial decision?

## Layer A and Layer B

```text
Layer A — deterministic scientific harness
frozen inputs
 -> scaling / BEP
 -> MKM
 -> reactor / process optimization
 -> economics
 -> ranking / uncertainty / backward design
 -> reproducible outputs

Layer B — decision layer
inspect state
 -> choose admissible action
 -> gather evidence
 -> update hypothesis
 -> stop / continue / redirect computation
```

Layer B does not rewrite canonical scientific state. Canonical promotion remains a separate explicit action.

## DISCOVER environment

The current closed-book DISCOVER benchmark exposes 11 fine-grained actions:

1. `INSPECT_CANDIDATES`
2. `COMPUTE_ACTIVITY`
3. `READ_PROPERTY_UNCERTAINTY`
4. `BUILD_PROCESS_WINDOW`
5. `OPTIMIZE_PROCESS`
6. `READ_COST_BREAKDOWN`
7. `RUN_MC`
8. `TEST_LEVER`
9. `BACKWARD`
10. `TEST_REACHABILITY`
11. `CHECK_MODEL_VALIDITY`

The agent cannot request a single tool that reveals the full answer. Ground truth is isolated from the agent and read only by the scorer.

## Compute units

The frozen benchmark cost model defines:

- **1 CU = 1000 MKM state solves**;
- measured benchmark reference: about **21.8 ms per CU**;
- full-domain process window: ~111 CU;
- single-candidate optimization: ~29 CU;
- 100-draw MC: ~17 CU;
- backward calculation: ~1 CU;
- reachability test: ~2-4 CU.

CU is deliberately a scientific-compute budget, not an LLM-token budget.

## Why anonymization is required

Named catalysts leak strong domain priors. A zero-tool probe showed that a language model could often guess that Ru is highly active or that Fe is economically plausible without doing the required multiscale work.

For that reason, the main closed-book claim is evaluated on a seeded anonymous permutation (`candidate_01`, ...), with the mapping visible only to the scorer.

Winner-only accuracy is not sufficient evidence. The scorer also checks whether the agent correctly resolves:

- the ranking inversion;
- the economic winner;
- the break-even target;
- scaling-manifold reachability;
- decision completeness;
- budget efficiency.

## Frozen policy baselines

The benchmark contains frozen non-LLM baselines A-D plus a decision-aware policy E.

Policy D is the fixed-VOI comparator. Its constants were frozen before the formal Agent evaluation. The purpose of the benchmark is not to assume E is better, but to test whether adaptive decision allocation improves decision quality or compute efficiency under fixed scientific-compute budgets.

The 200-CU regime is particularly useful because it exposes incomplete or misallocated search rather than allowing every strategy to brute-force the full chain.

## Frozen V1 and cross-model design

DISCOVER V1 was frozen before the cross-model evaluation. Any change to the task, prompt, action schema, cost model, scorer, stopping rule, policy-D constants or other pinned files defines DISCOVER V2 rather than a repair of V1.

Cross-model evaluation:

- weak: `gpt-5.4-nano-2026-03-17`;
- medium: `gpt-5.4-mini-2026-03-17`;
- strong: `gpt-5.5-2026-04-23`;
- budgets: **200, 250, 300, 500, 800, 1200, 2000 CU**;
- policy E: **5 independent runs per budget per anonymous/named variant**;
- 140 new traces for nano/mini; strong-tier V1 traces reused and re-scored;
- frozen hashes PASS before and after;
- 0 API retries and 0 driver exceptions.

## Cross-model result: workflow execution capability

On the anonymous closed-book task, complete decision recovery was:

```text
nano        6/35
mini       15/35
strong     35/35
```

A complete decision requires the full chain:

```text
economic winner
 -> decision pair
 -> backward target
 -> reachability verdict
```

The pooled trend in complete decision recovery across model tiers is strong (Cochran-Armitage Z = **6.95**). The strong tier completes the full chain at every budget. Weak tiers often recover the winner but fail later at pair formation, BACKWARD execution or reachability formulation.

This is a **positive Agent-framework result**: successful execution of a decision-aware scientific workflow is strongly dependent on the underlying model capability.

## Pre-registered E versus fixed-VOI D: negative result

The stronger pre-registered claim was that adaptive policy E would reliably outperform fixed-VOI policy D.

That claim was **not supported across model tiers**.

- The repeatable 200-CU adaptive-scope advantage appeared only in the strong tier.
- Nano and mini did not reproduce the narrow-window strategy.
- The pre-registered Agent-specific Go criterion — E beats D in at least 4/5 runs at one budget and in at least two model tiers — was **not met**.
- D has zero decision regret at every budget where it resolves the decision, so that component can tie but cannot be improved by E.

This negative result is retained exactly as evaluated. It is **not** evidence that the whole Agent framework fails. It rejects only the universal superiority claim:

> **Adaptive Agent E is not generally superior to fixed-VOI D across model capability tiers.**

The supported combined statement is:

> **A strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over a fixed-VOI strategy is capability-dependent rather than universal.**

## Failure structure in weaker tiers

The weak-tier failures are informative rather than being removed as implementation noise:

- wrong or unformed decision pair;
- BACKWARD omitted or executed on the wrong pair;
- reachability tested with an invalid/self-referential multiplier;
- undeclared tool arguments or unaffordable action requests;
- stopping with unresolved candidates;
- spending additional CU after the winner is already stable.

These are scored as observed. No run was retried or tuned to improve a benchmark cell.

## What counts as a meaningful AI result

A scientifically useful agent result should demonstrate one or more of the following:

- it identifies that an apparently high-uncertainty variable has low downstream decision value and avoids spending budget there;
- it recognizes that a lower-uncertainty variable controls a rank boundary and prioritizes it;
- it stops once the industrial decision is resolved;
- it redirects from an unreachable activity-only target toward another catalyst or process lever;
- it detects model-interface inconsistencies that would otherwise produce a numerically valid but scientifically wrong run.

This is closer to value-of-information / decision-focused acquisition than to generic workflow automation.

## Evidence hierarchy

For current Agent claims, use these sources in order:

1. frozen V1 hashes and protocol pins;
2. scored traces / per-trace failure records;
3. `docs/CROSS_MODEL_STATS_V1.md`;
4. `docs/CROSS_MODEL_DISCOVER_V1.md`;
5. manuscript and README summaries.

Do not revert to older drift/extrapolation-only summaries or describe the cross-model benchmark as pending.

## Current next tests

1. preserve DISCOVER V1 unchanged as the frozen benchmark record;
2. move any scorer weighting, tool-schema hardening or protocol redesign into DISCOVER V2;
3. continue transfer tests without rewriting the V1 negative result.
