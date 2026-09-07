# Decision-aware Agent Harness

## Canonical naming

The Agent system is referred to as the **Decision-aware Agent Harness**.

Its current benchmark families are separate and must not be merged into one version sequence:

- **DRIFT v2** — completed model/interface drift-diagnosis benchmark;
- **TRANSFER v1** — completed reaction-transfer benchmark;
- **DISCOVER V1** — frozen canonical closed-book, budgeted decision-allocation benchmark;
- **DISCOVER V2** — reserved for a future protocol redesign; not a completed current benchmark.

The older label `Layer B v0.5` refers to an implementation snapshot of the decision layer, not to the version of DISCOVER. The older label `extrapolation benchmark v1` is retained only as a legacy alias for **TRANSFER v1**.

See `VERSION_REGISTRY.md` for the project-wide naming policy.

## Why the agent exists

The AI component is not intended to be a wrapper around a fixed DFT -> MKM -> reactor -> TEA script.

A fixed workflow already solves the deterministic numerical chain. The agent is useful only at interfaces where a numerical optimizer cannot determine the scientifically appropriate next action, for example:

- which admissible model component should be reused, adapted or rebuilt during reaction transfer;
- whether an apparent difference is a model-version / unit / cost-boundary inconsistency;
- which uncertainty should be reduced next;
- which catalyst lever has the highest downstream decision value;
- whether a backward target is reachable;
- whether computation should stop because the industrial decision is already resolved.

The central AI question is therefore:

> Given a limited compute budget, can the agent allocate calculations according to their value to the downstream industrial decision?

## Layer A and Layer B

```text
Layer A — deterministic multiscale harness
frozen inputs
 -> scaling / BEP
 -> MKM
 -> reactor / process optimization
 -> economics
 -> ranking / uncertainty / backward design
 -> reproducible outputs

Layer B — decision layer
inspect current evidence
 -> identify decision-sensitive uncertainty / catalyst lever
 -> choose admissible scientific action
 -> execute Layer A tool / calculation
 -> update ranking / feasibility / reachability evidence
 -> stop / continue / redirect computation
```

Layer B does not rewrite canonical scientific state. Canonical promotion remains a separate explicit action.

## Supporting Agent benchmarks

### DRIFT v2

DRIFT v2 tests whether the decision layer can diagnose model/interface inconsistencies after evidence acquisition and choose the correct response. The current v2 set contains 12 cases and five action classes; the recorded action result is 12/12, with one cause-label ambiguity retained as observed.

DRIFT v2 supports the claim that the Agent Harness can reason over provenance/model-interface inconsistencies. It is not the formal decision-allocation benchmark.

### TRANSFER v1

TRANSFER v1 is the reaction-transfer benchmark built around the EXTRAPOLATE_REACTION prototype. Its decision chain includes:

```text
INSPECT_REACTION_CASE
 -> RECORD_TRANSFER_HYPOTHESIS
 -> BUILD_CAUSAL_GRAPH
 -> CLASSIFY_TRANSFER
 -> PROPOSE_MINIMUM_MODEL
 -> IDENTIFY_CANDIDATE_LEVERS
 -> TEST_CASE_LEVER_ELIGIBILITY
 -> SCORE_NEXT_CALCULATIONS
 -> PROPOSE_NEXT_CALCULATION
```

The transfer layer distinguishes REUSE / ADAPT / REBUILD / NOT_NEEDED across model components, identifies dominant catalyst-to-process pathways and asks whether more atomistic accuracy is actually useful for the downstream decision.

TRANSFER v1 supports the broader model-interface and reaction-transfer role of the Agent Harness. It is not a replacement for DISCOVER V1.

## DISCOVER V1 environment

DISCOVER V1 is the current formal benchmark for closed-book, budgeted scientific decision allocation. It exposes 11 fine-grained actions:

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

The frozen DISCOVER V1 cost model defines:

- **1 CU = 1000 MKM state solves**;
- measured benchmark reference: about **21.8 ms per CU**;
- full-domain process window: ~111 CU;
- single-candidate optimization: ~29 CU;
- 100-draw MC: ~17 CU;
- backward calculation: ~1 CU;
- reachability test: ~2-4 CU.

CU is a scientific-compute budget, not an LLM-token budget.

## Why anonymization is required

Named catalysts leak strong domain priors. A zero-tool probe showed that a language model could often guess that Ru is highly active or that Fe is economically plausible without doing the required multiscale work.

For that reason, the main closed-book claim is evaluated on a seeded anonymous permutation (`candidate_01`, ...), with the mapping visible only to the scorer.

Winner-only accuracy is not sufficient evidence. The scorer also checks whether the agent correctly resolves:

- the ranking inversion;
- the economic winner;
- the decision pair;
- the break-even target;
- scaling-manifold reachability;
- decision completeness;
- budget efficiency.

## Frozen policy baselines

The benchmark contains frozen non-LLM baselines A-D plus a decision-aware policy E.

Policy D is the fixed-VOI comparator. Its constants were frozen before the formal Agent evaluation. The purpose of the benchmark is not to assume E is better, but to test whether adaptive decision allocation improves decision quality or compute efficiency under fixed scientific-compute budgets.

The 200-CU regime is particularly useful because it exposes incomplete or misallocated search rather than allowing every strategy to brute-force the full chain.

## Frozen V1 and cross-model design

DISCOVER V1 was frozen before cross-model evaluation. Any change to the task, prompt, action schema, cost model, scorer, stopping rule, policy-D constants or other pinned files defines **DISCOVER V2** rather than a repair of V1.

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

The pooled trend in complete decision recovery across model tiers is strong (Cochran-Armitage Z = **6.95**). The strong tier completes the full chain at every tested budget. Weak tiers often recover the winner but fail later at pair formation, BACKWARD execution or reachability formulation.

This is the positive formal Agent result: successful execution of a decision-aware scientific workflow is strongly dependent on the underlying model capability. Tier separation is statistically clear: nano vs mini Fisher p = 0.036, mini vs strong p = 4 × 10⁻⁸; in the nano/mini logistic model the odds of a complete decision rise 4.7× per tier step and 2.3× per budget doubling.

## Strong-tier result, stated in full

- **35/35** complete correct decisions on the anonymous task at every budget including 200 CU; exact break-even (201.22×) in **34/35**; reachability **35/35**; regret **0**; **0** action or interface errors in 70 runs.
- **Only policy E completes the decision at 200 CU.** D, B, C and random all fail at 200 CU. E does it by building a narrow process window (29–52 CU to a stable winner instead of the 111-CU full window) — seen in 7/70 strong-tier runs, 0/140 weak-tier runs — and this advantage over D is repeatable **5/5** in the strong tier.
- At 250–500 CU, E matches D's decision quality with 218–268 CU against D's 247–281 CU; unnecessary-CU fraction 0.02–0.13 (weak tiers 0.18–0.55).
- In 35/35 anonymous strong-tier runs the same path emerged unprompted: activity screen → optimize → mismatch → BACKWARD → TEST_REACHABILITY → STOP; the model's stated winner matched the environment winner 70/70.
- Failure structure across tiers: in both weak tiers P(reachability correct) = P(full decision) cell by cell, so the binding step is the backward → reachability formulation, not winner identification (nano winner 20/20 at ≥ 500 CU). Weak tiers add a tool-interface error class in 69–86 % of runs; the strong tier has none.

## Pre-registered E versus fixed-VOI D: negative result

The stronger pre-registered claim was that adaptive policy E would reliably outperform fixed-VOI policy D.

That claim was **not supported across model tiers**.

- The repeatable 200-CU adaptive-scope advantage appeared only in the strong tier.
- Nano and mini did not reproduce the narrow-window strategy.
- The pre-registered Agent-specific Go criterion — E beats D in at least 4/5 runs at one budget and in at least two model tiers — was **not met**.
- D has zero decision regret at every budget where it resolves the decision, so that component can tie but cannot be improved by E.

This negative result is retained exactly as evaluated. It rejects only the universal-superiority claim:

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

A scientifically useful Agent result should demonstrate one or more of the following:

- identify that an apparently high-uncertainty variable has low downstream decision value and avoid spending budget there;
- recognize that a lower-uncertainty variable controls a rank boundary and prioritize it;
- stop once the industrial decision is resolved;
- redirect from an unreachable activity-only target toward another catalyst or process lever;
- detect model-interface inconsistencies that would otherwise produce a numerically valid but scientifically wrong run;
- during reaction transfer, identify the minimum sufficient model rather than automatically rebuilding every upstream layer.

This is closer to value-of-information / decision-focused acquisition than to generic workflow automation.

## Evidence hierarchy

For formal manuscript-level Agent claims, use these sources in order:

1. frozen DISCOVER V1 hashes and protocol pins;
2. scored traces / per-trace failure records;
3. `docs/CROSS_MODEL_STATS_V1.md`;
4. `docs/CROSS_MODEL_DISCOVER_V1.md`;
5. manuscript and README summaries.

For broader Agent-Harness capability descriptions, DRIFT v2 and TRANSFER v1 may be cited separately as supporting benchmark families.

## Current next tests

1. preserve DISCOVER V1 unchanged as the frozen benchmark record;
2. keep DRIFT v2 and TRANSFER v1 as separate supporting benchmark families rather than folding their version numbers into DISCOVER;
3. move any scorer weighting, tool-schema hardening or formal protocol redesign into DISCOVER V2;
4. continue reaction-transfer tests without rewriting the DISCOVER V1 negative result.
