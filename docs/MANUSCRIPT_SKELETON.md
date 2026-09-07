# Manuscript skeleton — current working version

Snapshot date: **2026-09-07**  
All ammonia headline values below use **NH3-FINAL-1.1**.

## Working title options

1. **Multiscale economics reshapes catalyst rankings at the industrial decision frontier**
2. **Industrial objectives reshape catalyst rankings across scales**
3. **Catalyst rankings invert under multiscale economic propagation**

## Abstract logic

The abstract should carry three scientific results rather than a long list of numbers:

1. **Where inversion occurs:** atomic and economic rankings diverge at the decision frontier in ammonia synthesis.
2. **How uncertainty propagates:** atomistic uncertainty can be amplified or attenuated by the multiscale process chain.
3. **Whether the backward target is reachable:** the activity improvement needed for Ru cost parity lies far outside the current scaling-consistent activity headroom.

A fourth sentence can establish transfer across reactions: the dominant economic pathway changes from activity–inventory in NH3 to selectivity–recycle in CO2-to-methanol.

## 1. Introduction

Catalyst discovery commonly ranks materials using adsorption energies, descriptors, intrinsic turnover frequencies or other atomistic proxies. Industrial selection is made on a different objective: product cost under coupled kinetic, catalyst-inventory, reactor, recycle, separation and replacement constraints.

The central gap is therefore not another activity model, but the missing causal chain from atomistic catalyst properties to the industrial decision.

This work asks:

- When does an atomic catalyst ranking survive multiscale propagation?
- When and why does it invert?
- Which uncertainty is worth reducing for the final industrial decision?
- What catalyst-property improvement is required by an economic target, and is that target physically reachable?

## 2. Framework

### 2.1 Forward propagation

```text
descriptor / DFT
 -> scaling + BEP
 -> microkinetics
 -> catalyst productivity / inventory
 -> reactor + process optimization
 -> economics
 -> industrial ranking
```

### 2.2 Backward design

```text
industrial economic target
 -> required catalyst-property improvement
 -> descriptor / scaling manifold
 -> reachable or unreachable
```

### 2.3 Decision-aware AI harness

The deterministic numerical chain is Layer A. The AI layer does not replace the physics or economics. It acts at interfaces where a numerical optimizer cannot decide which admissible scientific action is worth taking next.

```text
industrial objective + compute budget
 -> inspect current evidence
 -> choose scientific action
 -> execute tool / calculation
 -> update forward or backward evidence
 -> stop, continue or redirect
```

The AI contribution should be framed as **decision allocation**, not workflow automation.

## 3. Results

### 3.1 Atomic and economic rankings diverge in ammonia synthesis

The 15-metal activity screen places Ru, Os and Fe first, second and third. After process and economic optimization, the feasible economic order becomes Fe, Ru and Os.

Canonical costs:

- Fe: **15.292 USD/t NH3**
- Ru: **22.031 USD/t NH3**
- Os: **25.832 USD/t NH3**

The Top-3 Spearman correlation is **-0.50**, whereas the full 15-metal raw correlation remains **0.929**. The important result is therefore not a global collapse of atomistic screening, but a concentrated inversion at the **decision frontier**.

Primary figures: F1, F2.

### 3.2 Process reoptimization and uncertainty determine the actionable region

With the pressure-dependent CAPEX extension in NH3-FINAL-1.1, the previous 300-bar boundary artefact is removed.

Representative optima:

- Fe: approximately **425 C / 180 bar / 30 C**
- Ru: approximately **450 C / 425 bar / 25 C**
- Os: broad shallow high-pressure minimum

Across 1,000 uncertainty draws, Fe feasibility is **79.9%**, Top-1 survival is **28.2%**, and Top-3 actionable probability is **94.0%**.

The interpretation is that uncertainty is not monotonically amplified across scales. Kinetics may amplify small energetic shifts, while thermodynamic, reactor and process bottlenecks can absorb them before they alter the industrial decision.

Primary / supporting figures: F3, F4.

### 3.3 Backward design places the Ru activity target outside the current scaling manifold

Reoptimizing the full ammonia process while increasing Ru activity gives an activity-only break-even requirement of **201.22x** relative to baseline Ru.

The scaling-consistent activity headroom is only:

- **1.090x** at 673 K
- **2.525x** maximum over the frozen process-state library

The strict-scaling lowest Ru cost is **21.398 USD/t NH3** at **E_N = -1.215 eV**, still above Fe.

The result should be written as an **activity-only infeasibility signal under the current process model, operating constraints and scaling-consistent design path**, not as an experimental target.

Primary figures: F5, F6.

### 3.4 Methanol economics are controlled by a selectivity–recycle pathway

The explicit CO2-to-methanol loop couples catalyst performance to fresh feed demand, gas accumulation, purge, recycle compression and downstream equipment burden.

Current local leverages:

- STY: **0.00289**
- single-pass conversion: **0.05883**
- CH4 suppression: **0.37579**

Methane suppression dominates in the current benchmark because it changes both material loss and recycle architecture.

Primary figures: F7, F8.

### 3.5 Cross-reaction comparison reveals pathway-specific economic leverage

After aligning the cost denominator, the normalized MeOH CH4-suppression / NH3 TOF leverage ratio is **273–410**, midpoint approximately **328**.

This supports a reaction-specific interpretation:

- NH3: **activity -> inventory / reactor-demand** pathway
- MeOH: **selectivity -> feed-loss / purge / recycle** pathway

The manuscript-level conclusion is that atomic-to-economic ranking inversion is not governed by one universal catalyst variable. The dominant mechanism depends on how a catalyst property couples into downstream process cost pools.

Primary figure: F9.

### 3.6 Decision-aware computation allocation is model-capability dependent

DISCOVER V1 evaluates whether an AI agent can allocate limited scientific compute to the parts of the multiscale chain that matter to the final industrial decision. The protocol was frozen before the cross-model test: the task, prompt, 11-action schema, CU cost model, scorer, stopping rule and A-D baselines were unchanged.

Cross-model design:

- three model tiers: nano, mini and strong;
- seven budgets: **200, 250, 300, 500, 800, 1200 and 2000 CU**;
- five independent policy-E runs per budget per variant;
- anonymous closed-book task used for the primary claim;
- 140 new weak/medium traces plus the reused frozen strong-tier V1 traces.

Anonymous complete-decision recovery was:

- nano: **6/35**
- mini: **15/35**
- strong: **35/35**

A complete decision requires the whole chain — economic winner, decision pair, backward target and reachability verdict. The positive result is therefore **workflow-execution capability**: complete decision recovery rises strongly with underlying model capability (pooled tier trend Z = **6.95**), and the strong model executes the full decision-aware chain reliably.

The stronger pre-registered claim did **not** hold. Policy E did not demonstrate robust, cross-tier superiority over the deterministic fixed-VOI policy D. The adaptive narrow-window advantage at **200 CU** was repeatable only in the strong tier and did not reproduce in nano or mini. The pre-registered Agent-specific Go criterion was therefore **not met**.

This negative result is retained rather than tuned away. It rejects the general claim **"adaptive Agent E is universally better than fixed-VOI D"**, but it does not reject the Agent framework. The supported statement is:

> **A strong model can execute and exploit decision-aware allocation, but the advantage of adaptive Agent allocation over a fixed-VOI strategy is model-capability dependent rather than universal.**

Primary evidence: `CROSS_MODEL_DISCOVER_V1.md`, `CROSS_MODEL_STATS_V1.md`, frozen hashes and scored traces.

## 4. Discussion

The Discussion should focus on implications rather than restating results.

### 4.1 Screening objectives should be defined at the level of downstream economic leverage

A catalyst property is valuable only insofar as it changes a process pathway that matters to the industrial objective. High intrinsic sensitivity is therefore not equivalent to high economic leverage.

### 4.2 The relevant uncertainty is decision sensitivity, not atomistic uncertainty alone

A descriptor with large uncertainty may deserve little additional compute if the downstream decision is insensitive to it. Conversely, a smaller uncertainty can be worth resolving if it controls a rank boundary or feasibility transition.

### 4.3 Backward design changes the interpretation of catalyst targets

Instead of asking whether a catalyst can be made “more active,” the framework asks how much improvement is required for an industrial objective and whether that improvement is reachable on the admissible catalyst-property manifold.

### 4.4 Reaction transfer requires pathway transfer, not only model transfer

A new reaction should not inherit the ammonia mechanism by analogy. The relevant question is which catalyst property controls which downstream cost pool in that process architecture.

### 4.5 Agent claims should separate execution capability from policy superiority

The cross-model benchmark shows that the ability to complete a multistep decision chain is itself capability-dependent. At the same time, a capable adaptive agent does not automatically dominate a strong deterministic VOI baseline. These are distinct claims and should be reported separately.

## 5. Figures

See [`FIGURE_MAP.md`](FIGURE_MAP.md) for the current nine-figure map and canonical headline values.

## 6. Methods structure

A compact Methods section can be organized as:

1. Descriptor and scaling relations
2. Microkinetic model
3. Catalyst productivity and inventory mapping
4. Reactor and process-state optimization
5. Pressure-dependent equipment and catalyst-dependent economics
6. Uncertainty propagation
7. Backward-design and scaling reachability
8. Methanol recycle/separation model
9. Cross-reaction leverage normalization
10. Decision-aware AI harness and frozen DISCOVER V1 cross-model benchmark

## 7. Supporting Information priorities

Supporting Information should contain the technical evidence needed to trust the main claims:

- NH3-FINAL-1.1 pressure-CAPEX audit
- perturbation / sensitivity closure
- Monte Carlo protocol and full distributions
- detailed operating envelopes
- cost-pool decomposition
- scaling-manifold derivation
- complete DISCOVER action schema, scorer and budget curves
- named vs anonymous benchmark controls
- zero-tool prior probe
- cross-model per-trace scores and failure matrix
- pre-registered E-vs-D Go/No-Go evaluation

## Version note

Archived NH3-FINAL-1.0 numbers such as 10.199 / 17.592 / 21.321 USD/t, 73.6% feasibility and 2171.56x break-even should remain historical only and should not appear as current manuscript headline values.
