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

The important comparison is not whether E always beats every scripted policy. It is whether decision-aware allocation can match or improve decision quality while avoiding unnecessary computation, especially at tight budgets.

Current formal single-model record:

- policy-E formal runs: **70** = 5 seeds x 7 budgets x anonymous/named;
- all traces including A-D baselines: **392**;
- infrastructure retries: **0**;
- action errors: **0**;
- anonymous complete correct decisions: **35/35**;
- exact break-even recovery: **34/35**;
- 250-500 CU: E and fixed-VOI D are effectively indistinguishable in decision quality;
- E consumed about **218-268 CU** in that regime versus **247-281 CU** for D.

The 200-CU regime is particularly useful because it exposes incomplete or misallocated search rather than allowing every strategy to brute-force the full chain.

## What counts as a meaningful AI result

A scientifically useful agent result should demonstrate one or more of the following:

- it identifies that an apparently high-uncertainty variable has low downstream decision value and avoids spending budget there;
- it recognizes that a lower-uncertainty variable controls a rank boundary and prioritizes it;
- it stops once the industrial decision is resolved;
- it redirects from an unreachable activity-only target toward another catalyst or process lever;
- it detects model-interface inconsistencies that would otherwise produce a numerically valid but scientifically wrong run.

This is closer to value-of-information / decision-focused acquisition than to generic workflow automation.

## Cross-model stability record (2026-09-06/07)

Items 1–2 of the earlier plan are done on the frozen V1 protocol (`docs/CROSS_MODEL_DISCOVER_V1.md`, `docs/CROSS_MODEL_STATS_V1.md`):

- the complete correct decision is a property of the strong tier, not of "an LLM agent": anonymous pooled P(full) 6/35 (nano), 15/35 (mini), 35/35 (gpt-5.5);
- the discriminating components are the pair decision and the reachability verdict; the winner alone is price-prior-recoverable in every tier;
- the 200-CU adaptive-scope advantage is strong-tier-only (narrow windows 7/70 vs 0/140);
- under-resolution → over-confirmation reproduces and is amplified in weaker tiers, which show both at once;
- weak tiers add a tool-interface error class (undeclared arguments, unaffordable requests) that costs turns, not CU;
- the pre-registered agent-specific Go against fixed-VOI D is not met across tiers (negative result, kept).

## Current next tests

1. add a negative-reaction case where atomic ranking should largely survive economic propagation (not started);
2. keep the same frozen scorer and protocol while testing transfer; protocol changes go to DISCOVER V2.
