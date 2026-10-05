# Research frame

Reader-facing names follow [`SCIENTIFIC_NAMING.md`](SCIENTIFIC_NAMING.md).

## Core scientific question

Catalyst screening is usually performed using atomic-scale proxies such as adsorption energies, descriptors and intrinsic activity. Industrial deployment is governed by a different objective: product cost under coupled kinetic, catalyst-inventory, reactor, recycle, separation and replacement constraints.

The project therefore asks four linked questions:

1. **When does an atomic catalyst ranking survive multiscale propagation to an industrial decision?**
2. **When it reshapes or inverts, which catalyst-to-process pathway creates the change?**
3. **Given an industrial target, what catalyst-property change is required, and is that target reachable on a physically plausible scaling manifold?**
4. **Can finite scientific compute be allocated adaptively to recover the downstream decision under a constrained budget?**

A necessary control follows from the first two: **does the same multiscale implementation preserve a ranking when the downstream mapping is monotonic?**

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

## Backward design

```text
industrial economic target
        -> required performance improvement
        -> catalyst-property target
        -> scaling / descriptor manifold
        -> reachable or unreachable?
```

The useful output of backward design can be a feasible catalyst-property region coupled to a process design rather than a single material.

## Ammonia as the primary case

Under the **ammonia process–economics model**:

- atomic activity top three: **Ru > Os > Fe**
- economic top three: **Fe > Ru > Os**
- Top-3 Spearman rho: **-0.50**
- full 15-metal raw Spearman rho: **0.929**

The result is concentrated at the **decision frontier** rather than representing a global collapse of the atomistic ranking.

The economic ordering is generated after propagation through catalyst-controlled pathways involving productivity, inventory, reactor sizing, operating severity, catalyst replacement and process equipment.

The direct price counterfactual resolves the causal partition. Setting Ru metal price equal to Fe = **8 USD/kg** and fully reoptimizing the 14,136-state process model gives Ru = **14.712 USD/t** at **425 C / 170 bar / 30 C**, below Fe = **15.292 USD/t**. The baseline Fe-over-Ru inversion therefore **depends on the Ru-vs-Fe metal-price disparity**. The response is not a static line-item subtraction: price equalization drives Ru from 450 C / 425 bar to a Fe-like low-pressure operating regime. The mechanism is **metal cost coupled to process reoptimization**.

## Uncertainty propagation

A small energetic error can be amplified at the kinetic level because rates depend strongly on activation free energies. Downstream propagation need not remain monotonic: equilibrium, reactor constraints, recycle, mass/energy bottlenecks and process optimization can attenuate an atomistic uncertainty before it changes the final decision.

The useful quantity is the **decision sensitivity of the industrial objective to the uncertainty**.

For Fe under the frozen 1,000-draw descriptor analysis:

- feasibility: **79.9%**
- economic Top-1 probability: **68.1%**
- atomic-to-economic Top-1 survival: **28.2%**
- Top-3 actionable probability: **94.0%**

The preregistered 5,000-draw cost-side MC gives **P(C_Fe < C_Ru) = 1.000** within the tested price/CAPEX/electricity/lifetime envelope. The Ru alpha* requirement broadens to p05 / median / p95 = **70.78x / 174.27x / 462.00x**.

## Backward-design result for Ru

Ru requires approximately **201.22x** intrinsic-activity enhancement to reach Fe cost parity after process reoptimization.

The scaling-consistent activity headroom is only:

- **1.090x at 673 K**
- **2.525x maximum** over the frozen process-state library

The activity-only parity target is therefore outside the current reachable scaling-consistent design space.

## Cross-reaction interpretation

The framework does not assume one universal inversion mechanism.

For the canonical CO2-to-methanol case, local leverage at 5 wt% Re / 250 C is:

- STY: **0.00289**
- single-pass conversion: **0.05883**
- CH4 suppression: **0.37579**

The directly supported pathway comparison is:

```text
NH3
intrinsic activity + metal cost
 -> catalyst inventory + preferred operating regime
 -> compression / reactor / equipment burden

MeOH
selectivity
 -> reactant loss / gas accumulation
 -> purge / recycle / compression
```

Each reaction is evaluated against its own frozen downstream economic objective. Absolute economic values are not compared across reactions; the transfer object is the catalyst-to-process coupling topology.

The manuscript-level claim is therefore that **ranking propagation is reaction- and process-pathway dependent because different catalyst properties couple into different downstream cost pools**. No current quantitative cross-reaction leverage ratio is promoted.

## Rank-preservation control

A separate Au/TiO2 CO-oxidation control tests the complementary case. Candidate states differ in Au particle size while the catalyst family and downstream mapping remain common.

Across 2, 3, 4, 5 and 6 nm particles, intrinsic activity and required catalyst burden retain the same order:

```text
2 nm > 3 nm > 4 nm > 5 nm > 6 nm
```

with:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- 10,000/10,000 predefined literature-envelope draws preserving the full ranking
- 6 nm / 2 nm required-catalyst ratio = **8.064x**

A supporting **Au/TiO₂ semi-open robustness extension** allows moderate candidate-specific kinetic and operating freedom while retaining strong rank preservation. The **Au/TiO₂ rank-preservation control** remains the primary control.

This establishes the counterfactual:

```text
monotonic downstream coupling
    -> ranking can be preserved

competing / reoptimized downstream coupling
    -> ranking can reshape or invert
```

## Decision-aware Agent result

The Agent benchmark is the **automation and scaling layer** of the deterministic scientific framework. It asks whether an AI policy can allocate finite scientific compute through a frozen environment while recovering the same downstream decision. Reaction-specific deterministic tools supply the catalyst ranking, physical mechanism and economic ground truth; the Agent supplies reusable orchestration so the same decision logic can be executed repeatedly rather than rebuilt case by case.

**Adaptive Catalyst Screening Agent (ACSA)** anonymous complete-decision recovery is:

- nano: **6/35**
- mini: **15/35**
- strong: **35/35**

The original across-tier hypothesis that adaptive policy E would outperform fixed-VOI policy D was not supported.

The **ACSA budget-boundary study** resolves the operating envelope. Deterministic policy D reaches the complete decision at **206 CU**. The strong tier reaches a lowest tested stable complete-decision budget of **75 CU**; at 175 CU it completes **19/20** runs while D remains incomplete. The same below-threshold regime does not transfer to the weaker tiers. Under the non-binding 5000-CU allowance, median final adaptive spend rises to **714 CU**.

The supported combined statement is:

> **Adaptive decision recovery below the fixed-policy completion threshold is model-tier dependent and budget localized. The broader contribution is workflow scalability: a stable decision layer can repeatedly orchestrate reaction-specific scientific tools under explicit compute budgets.**

Under the non-binding allowance, canonical narrow-window use is **0/20**; median complete-decision stabilization occurs at **566 CU**, followed by a median **148 CU** of additional spend before self-stop, for **714 CU** median final spend.

The oracle analysis separates a **7-CU scorer-theoretic floor** from a **22-CU protocol-complete S1-S3 minimum**. The 22-CU value is used for manuscript interpretation: the strong 75-CU allowance is **3.41x oracle**, its 52.5-CU median decision-stable spend is **2.39x oracle**, fixed-VOI's 206-CU threshold is **9.36x oracle**, and the non-binding 566-CU decision-stable median is **25.73x oracle**.

## Manuscript-level claim structure

1. Atomic and economic rankings can diverge at the industrial decision frontier.
2. Multiscale uncertainty can be amplified or attenuated according to the pathway and decision boundary.
3. Backward design separates economically required catalyst targets from physically reachable ones.
4. Catalyst-to-economic propagation is reaction- and process-pathway dependent.
5. A literature-calibrated control shows that multiscale propagation can also preserve an upstream ranking; inversion is conditional rather than intrinsic to the workflow.
6. Decision-aware compute allocation has a capability-bounded operating envelope and provides the orchestration layer needed to turn the deterministic framework into a reusable, batch-executable workflow.

Superseded values and intermediate conclusions are documented only in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md) and provenance/audit records.
