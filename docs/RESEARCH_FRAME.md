# Research frame

## Core scientific question

Catalyst screening is usually performed using atomic-scale proxies such as adsorption energies, descriptors and intrinsic activity. Industrial deployment is governed by a different objective: product cost under coupled kinetic, catalyst-inventory, reactor, recycle, separation and replacement constraints.

The project therefore asks three linked questions:

1. **When does an atomic catalyst ranking survive multiscale propagation to an industrial decision?**
2. **When it inverts, which layer creates the inversion?**
3. **Given an industrial target, what catalyst-property change is required, and is that target reachable on a physically plausible scaling manifold?**

The project is deliberately problem-first. The multiscale workflow is not itself the scientific contribution; the contribution comes from what the connected chain reveals about ranking, uncertainty, economic leverage and reachable catalyst targets.

## Forward propagation

```text
atomic descriptor / DFT
        |
        v
scaling relations + BEP closure
        |
        v
microkinetics
TOF + surface coverage
        |
        v
catalyst productivity / inventory
        |
        v
reactor + operating-point optimization
        |
        v
recycle + separation + thermal duty
        |
        v
equipment + catalyst-dependent economics
        |
        v
industrial ranking
```

Every candidate is evaluated under the same model family and engineering constraints, but process conditions are reoptimized candidate by candidate. This avoids comparing catalysts at an arbitrary common operating point.

## Backward design

The same chain is inverted conceptually:

```text
industrial economic target
        -> required performance improvement
        -> catalyst-property target
        -> scaling / descriptor manifold
        -> reachable or unreachable?
```

The useful output of backward design is not necessarily a single material. It can be a feasible region of catalyst properties, coupled to a process design.

## Why ammonia is a useful primary case

Ammonia synthesis provides a clean test because the atomic activity ordering and the industrially preferred catalyst need not coincide.

Under the current canonical NH3-FINAL-1.1 model:

- atomic activity top-3: **Ru > Os > Fe**;
- economic top-3: **Fe > Ru > Os**;
- Top-3 Spearman rho: **-0.50**;
- full 15-metal raw Spearman rho: **0.929**.

This combination is important. It means the system does not show a global collapse of atomic screening. Instead, the inversion is concentrated near the **decision frontier**, where candidate selection actually occurs.

## Why the inversion is not just metal price

The economic ranking is generated after propagation through multiple catalyst-controlled pathways:

- activity changes required catalyst inventory;
- surface coverage changes effective productivity;
- inventory affects bed volume and reactor sizing;
- operating severity affects compression and equipment cost;
- catalyst purchase price, lifetime and recovery affect replacement cost;
- pressure and temperature influence conversion and downstream burden.

The dominant pathway can therefore change from one reaction to another.

## Uncertainty propagation

A small energetic error can be strongly amplified at the kinetic level because rates depend exponentially on activation free energies. But the amplification need not continue monotonically downstream.

Thermodynamic equilibrium, reactor constraints, recycle, mass/energy bottlenecks and process optimization can attenuate an atomistic uncertainty before it reaches the final cost decision.

The useful scientific quantity is therefore not atomistic uncertainty alone, but the **decision sensitivity of the downstream industrial objective to that uncertainty**.

## Backward-design result for Ru

In NH3-FINAL-1.1, Ru requires about **201.22x** intrinsic-activity enhancement to reach Fe cost parity when the process is reoptimized.

By contrast, the currently available scaling-consistent activity headroom is:

- **1.090x at 673 K**;
- **2.525x maximum** over the frozen process-state library.

The gap between 201.22x required and <=2.525x reachable is the relevant result. It is an **activity-only infeasibility signal** under the current process model, operating constraints and scaling-consistent design path.

## Cross-reaction interpretation

The framework is not intended to claim one universal inversion mechanism.

For the current CO2-to-methanol benchmark:

- STY leverage = 0.00289;
- single-pass-conversion leverage = 0.05883;
- CH4-suppression leverage = 0.37579.

After denominator alignment, the MeOH CH4-suppression / NH3 TOF leverage ratio is 273-410, midpoint ~328.

This motivates a pathway-specific view:

- **NH3:** activity -> inventory / reactor-demand pathway;
- **MeOH:** selectivity -> feed-loss / purge / recycle pathway.

The broader claim is therefore: **atomic-to-economic ranking inversion is reaction- and process-dependent because different catalyst properties couple into different downstream cost pools.**

## Decision-aware Agent result

The DISCOVER V1 Agent benchmark tests a different question from the physical ranking analysis: given a frozen scientific environment and a finite CU budget, can an AI model execute the complete downstream decision chain and allocate computation adaptively?

Under the frozen three-tier cross-model evaluation, anonymous complete-decision recovery is:

- nano: **6/35**;
- mini: **15/35**;
- strong: **35/35**.

This is the positive result: **workflow-execution capability is strongly model-capability dependent**, and the strong tier reliably completes winner selection, decision-pair formation, backward design and reachability evaluation.

A separate pre-registered claim is negative. Adaptive policy E did **not** establish cross-tier superiority over fixed-VOI policy D. The repeatable 200-CU adaptive-scope advantage occurs only in the strong tier. Therefore the framework should not be described as showing that "Agent E generally beats fixed VOI."

The supported combined statement is:

> **A strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over a fixed-VOI strategy is model-capability dependent rather than universal.**

DISCOVER V1 remains frozen; this negative result is part of the evidence rather than a reason to modify the protocol post hoc.

## Manuscript-level claim structure

A compact manuscript logic is:

1. Atomic and economic rankings diverge at the industrial decision frontier.
2. Multiscale uncertainty can be amplified or attenuated depending on the pathway.
3. Backward design separates reachable catalyst targets from unreachable ones.
4. Economic leverage is pathway-specific across reactions.
5. Decision-aware workflow execution improves strongly with model capability, while adaptive policy E does not show universal cross-model superiority over fixed-VOI D.
