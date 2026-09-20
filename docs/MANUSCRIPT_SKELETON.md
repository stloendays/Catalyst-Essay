# Manuscript skeleton — current working version

Snapshot date: **2026-09-20**  
Canonical ammonia basis: **NH3-FINAL-1.1**

This document contains current manuscript logic only. Superseded values and intermediate development conclusions are centralized in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).

## Working title options

1. **Multiscale economics reshapes catalyst rankings at the industrial decision frontier**
2. **Industrial objectives reshape catalyst rankings across scales**
3. **Catalyst rankings invert under multiscale economic propagation**

## Abstract logic

The abstract should carry the scientific logic rather than a dense list of numbers:

1. Atomic-scale rankings can change at the industrial decision frontier after kinetic, process and economic propagation.
2. The effect is conditional rather than inevitable: NH3 and MeOH show ranking reshaping through different catalyst-to-process pathways, while an Au/TiO2 control preserves the upstream order under a monotonic mapping.
3. Backward design converts an economic target into a required catalyst-property improvement and tests whether that target is reachable on the frozen property manifold.
4. A decision-aware AI layer is evaluated separately as a compute-allocation mechanism; under the frozen benchmark, its below-threshold decision-recovery advantage is bounded by model capability and budget.

## 1. Introduction

Catalyst discovery commonly ranks candidates using adsorption energies, descriptors, intrinsic turnover frequencies or other atomistic proxies. Industrial selection is made on a different objective: product cost under coupled kinetic, catalyst-inventory, reactor, recycle, separation and replacement constraints.

The central questions are therefore:

- When does an upstream catalyst ranking survive multiscale propagation?
- When and why does it reshape or invert?
- Which uncertainties change the downstream decision?
- What catalyst-property improvement is required by an industrial target, and is it physically reachable?
- Can scientific compute be allocated adaptively to recover the same decision under a constrained budget?

A rank-preservation control provides the necessary counterfactual: if the downstream mapping remains monotonic, the framework should preserve rather than manufacture a ranking inversion.

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

The deterministic numerical chain is Layer A. The AI layer does not replace the physics or economics; it chooses among admissible scientific actions under a compute budget.

```text
industrial objective + compute budget
 -> inspect current evidence
 -> choose scientific action
 -> execute calculation
 -> update ranking / feasibility / reachability
 -> stop, continue or redirect
```

The AI contribution is framed as **decision allocation**, not as the source of the physical result.

## 3. Results

### 3.1 Atomic and economic rankings diverge in ammonia synthesis

The 15-metal intrinsic activity screen places **Ru, Os and Fe** first, second and third. After catalyst-dependent reactor/process optimization and economic propagation, the leading economic order becomes **Fe, Ru and Os**.

Canonical catalyst-dependent costs are:

- Fe: **15.292 USD/t NH3**
- Ru: **22.031 USD/t NH3**
- Os: **25.832 USD/t NH3**

The Top-3 Spearman correlation is **-0.50**, while the full 15-metal raw correlation remains **0.929**. The central result is therefore a concentrated inversion at the **decision frontier**, not a global collapse of atomistic screening.

Primary figures: **F1, F2**.

### 3.2 Process reoptimization and uncertainty define the actionable region

Representative optimized operating points under NH3-FINAL-1.1 are approximately:

- Fe: **425 C / 180 bar / 30 C separator**
- Ru: **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

Across 1,000 descriptor-uncertainty draws, Fe feasibility is **79.9%**, Fe is the economic Top-1 candidate in **68.1% (681/1000)** of draws, atomic-to-economic Top-1 survival is **28.2%**, and Top-3 actionable probability is **94.0%**. The 68.1% and 28.2% values answer different questions and should not be interchanged.

A direct price counterfactual isolates the baseline Fe-Ru mechanism. When Ru metal price is set equal to Fe = **8 USD/kg**, with all other inputs unchanged, full 14,136-state reoptimization shifts Ru from 450 C / 425 bar to **425 C / 170 bar** and lowers its cost to **14.712 USD/t NH3**, **0.580 USD/t below Fe**. Thus the baseline Fe-over-Ru inversion does not survive price equalization. The supported mechanism is **metal cost coupled to process reoptimization** rather than a process penalty sufficient to keep Fe ahead at equal metal price.

The canonical 6.739 USD/t Ru-Fe gap is dominated by fresh-feed compression (+4.632), metal inventory (+1.763) and compressor CAPEX (+1.181 USD/t), partly offset by vessel pressure, recycle compression and reactor-base terms. The reoptimized counterfactual is the causal test; the static line-item decomposition is explanatory rather than causal.

A preregistered 5,000-draw cost-side Monte Carlo jointly perturbs metal price, CAPEX coefficient, electricity price and catalyst lifetime. Full process reoptimization gives **P(C_Fe < C_Ru) = 5000/5000 = 1.000** within this bounded uncertainty envelope. The corresponding Ru activity parity distribution is **p05 = 70.78x, median = 174.27x, p95 = 462.00x**.

The scientific endpoint is whether uncertainty changes feasibility or candidate selection. Atomistic and economic uncertainties are therefore reported separately: descriptor uncertainty changes the identity of the economic winner in a substantial fraction of draws, whereas the tested cost-side envelope does not reverse Fe versus Ru.

Primary/supporting figures: **F3, F4**.

### 3.3 Backward design places the Ru activity target outside the current scaling manifold

Full process reoptimization gives a Ru activity-only break-even requirement of **201.22x** relative to baseline Ru.

The scaling-consistent activity headroom is only:

- **1.090x** at 673 K
- **2.525x** maximum over the frozen process-state library

The strict-scaling lowest Ru cost is **21.398 USD/t NH3** at **E_N = -1.215 eV**, still above Fe.

The result is an activity-only reachability statement under the current process model, operating constraints and scaling-consistent design path.

Primary figures: **F5, F6**.

### 3.4 Methanol rankings reshape through a selectivity-recycle pathway

The canonical **MEOH-D01-v3** case contains four Re/TiO2 catalyst-temperature states evaluated through an explicit recycle/separation loop at **2% purge**. Using **STY per g Re** as the upstream intrinsic-productivity metric:

```text
upstream rank                       economic NPC rank
1 wt% Re / 250 C   #1              5 wt% Re / 200 C   #1
1 wt% Re / 200 C   #2      ->      1 wt% Re / 200 C   #2
5 wt% Re / 200 C   #3              1 wt% Re / 250 C   #3
5 wt% Re / 250 C   #4              5 wt% Re / 250 C   #4
```

The four-state comparison gives **Spearman rho = 0.20**, **Kendall tau = 0.00**, and **3/6 pairwise inversions**. The upstream per-Re winner falls to economic rank #3.

The mechanism is consistent with a **selectivity-recycle pathway**. At 5 wt% Re / 250 C, local economic leverage is:

- STY: **0.00289**
- single-pass conversion: **0.05883**
- CH4 suppression: **0.37579**

Methane formation couples to H2 feed loss, inert accumulation, purge, recycle compression and equipment burden. Across the complete **0.5-40% / 396-level** purge sweep, the per-Re winner is never the economic winner, rho does not exceed **0.40**, and at least **2/6** pairs remain inverted.

The candidates here are measured catalyst-temperature states. Purge is the exposed process degree of freedom and is reoptimized in the robustness analysis; temperature and pressure are not independently reoptimized per state.

A 5,000-draw cost-parameter analysis preserves the canonical four-candidate economic order in **5000/5000** draws. Because canonical D01 excludes Re purchase/replacement, metal-price and lifetime perturbations are structurally inactive in the canonical-boundary calculation. A separately labelled active-Re replacement extension, using STY-derived Re inventory, also preserves the same order in **5000/5000** draws.

Primary figures: **F7, F8**; cost-uncertainty matrix: Supporting Information / F3 extension.

### 3.5 Cross-reaction comparison reveals pathway-specific propagation

The directly supported comparison is mechanistic:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The manuscript therefore argues that ranking changes are **reaction- and process-pathway dependent**. It does not assign a current quantitative cross-reaction leverage ratio.

Primary figure: **F9A**, qualitative pathway panel.

### 3.6 A rank-preservation control shows that inversion is conditional

A separate literature-calibrated Au/TiO2 CO-oxidation control uses common chemistry and process conditions across 2-6 nm particle-size states. The canonical V1.1 mapping preserves the complete order:

```text
2 nm > 3 nm > 4 nm > 5 nm > 6 nm
```

with:

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- 10,000/10,000 predefined literature-envelope draws preserving the full order
- 6 nm / 2 nm required-catalyst ratio = **8.064x**

A supporting V1.3 semi-open extension allows moderate candidate-specific kinetic and operating freedom. In the primary 273.15-293.15 K window, exact full order is preserved in **92.16%** of draws and mean rho is **0.99214**; in the wider 273.15-313.15 K sensitivity window, exact preservation is **72.62%** and mean rho is **0.96802**.

The combined interpretation of F1-F9 is conditional: multiscale propagation can preserve, weakly reshape or invert a ranking depending on the coupling topology between catalyst properties, screening objectives and downstream decision variables.

Primary figure: **F9B**.

### 3.7 The decision-aware agent recovers complete decisions below the fixed-policy threshold

DISCOVER V1 evaluates scientific decision allocation under a frozen 11-action interface and CU accounting scheme. The frozen primary endpoint is:

`full_decision_correct = winner_correct ∧ pair_decision_correct ∧ reachability_correct`

Anonymous complete-decision recovery in DISCOVER V1 is **6/35 nano, 15/35 mini and 35/35 strong**. The original hypothesis that adaptive policy E would outperform fixed-VOI policy D across tiers was not supported.

DISCOVER-BOUNDARY-C1 retains the frozen environment and resolves the budget boundary against deterministic policy D, which reaches the complete decision at **206 CU**.

At the two weak-tier boundary cells:

```text
                     175 CU          225 CU
strong adaptive       19/20           20/20
mini adaptive           0/20            6/20
nano adaptive           0/20            0/20
fixed-VOI             incomplete       complete
```

For the strong tier, **75 CU** is the lowest tested stable complete-decision budget. At **50 CU**, completion falls to **13/20** while winner and decision pair remain correct in 20/20 runs, identifying reachability closure as the limiting component.

Decision-level convergence and quantitative-target convergence occur at different budgets: 75 CU is the lowest tested stable complete-decision budget, whereas **225 CU** is the lowest tested budget with 20/20 recovery of the canonical backward parity multiplier.

Canonical narrow-window allocation provides the below-threshold mechanism. The strong tier uses it in 20/20 runs from 50 through 175 CU, **1/8** at 200 CU, **0/20** at 225 CU and **0/9** at 250 CU. The weaker tiers do not use canonical narrow-window allocation in their measured cells.

The efficiency advantage is bounded above. Under a **non-binding 5000-CU allowance**, canonical narrow-window allocation disappears (**0/20**), median complete-decision stabilization is delayed to **566 CU**, and a further median **148 CU** is spent before self-stop, producing **714 CU** median final spend. The scientific decision remains unchanged; compute allocation changes.

A deterministic oracle lower bound makes the scale interpretable. The literal scorer-complete floor is **7 CU**, but it can exploit incomplete screening. The manuscript-facing **protocol-complete S1-S3 oracle is 22 CU**, requiring a process window, all-candidate activity screening, optimization of the minimum unresolved Fe/Ru/Os set, backward design and reachability. Relative to 22 CU, the strong 75-CU allowance is **3.41x**, the 75-CU cell median decision-stable spend of 52.5 CU is **2.39x**, and policy D's 206-CU threshold is **9.36x**.

The supported manuscript claim is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy completion threshold**, not universal adaptive superiority or universal raw-compute saving.

Primary figure: **F10**. Extended Data: **ED1-ED3**.

## 4. Discussion

### 4.1 Screening objectives should be defined at the level of downstream economic leverage

A catalyst property is valuable insofar as it changes a process pathway that matters to the industrial objective. High intrinsic sensitivity is not equivalent to high economic leverage.

### 4.2 The relevant uncertainty is decision sensitivity

A descriptor with large uncertainty may deserve little additional compute if the downstream decision is insensitive to it. A smaller uncertainty may be worth resolving if it controls a rank boundary or feasibility transition.

### 4.3 Backward design changes the interpretation of catalyst targets

Rather than asking only whether a catalyst can be made more active, backward design asks how much improvement is required for an industrial objective and whether that improvement lies on the admissible catalyst-property manifold.

### 4.4 Reaction transfer requires pathway transfer

A new reaction should not inherit the ammonia mechanism by analogy. The relevant question is which catalyst property controls which downstream cost pool in that process architecture.

### 4.5 Ranking inversion is conditional

The Au/TiO2 control shows that adding model layers does not itself force an inversion. Substantial reshaping appears when candidate-specific downstream coupling is strong enough to overcome upstream separation. The relevant object is the **coupling topology between catalyst properties, screening objectives and downstream decision variables**.

### 4.6 Adaptive compute allocation has a capability-bounded operating envelope

The Agent result should be interpreted as an operating envelope rather than a general efficiency claim. Below the deterministic 206-CU threshold, the strong tier can recover the complete decision by narrowing the process search and redirecting compute toward unresolved backward-design and reachability steps. Below 75 CU, affordability limits completion. The 22-CU protocol oracle shows that the strong tier's 52.5-CU median decision-stable spend at the 75-CU cell is already within **2.39x** of the shortest scientifically complete chain.

Above the threshold, deterministic policy D is cheaper. When the budget becomes non-binding, narrow-window allocation falls to **0/20**, decision stabilization moves to **566 CU**, and a further **148 CU** median is spent before self-stop. The failure mode therefore begins before post-stability overspending: budget pressure is itself what induces search compression.

The envelope is also bounded by model capability: weaker tiers do not reproduce the strong-tier below-threshold regime under the measured conditions. Agent performance should therefore be reported jointly as a function of **model capability, compute budget and decision endpoint**.

## 5. Figures

See [`FIGURE_MAP.md`](FIGURE_MAP.md) for the current **F1-F10** architecture and canonical values.

```text
F1-F4   forward propagation and decision-frontier inversion
F5-F6   backward design and reachability
F7-F9   transfer across pathways and rank-preservation control
F10     decision-aware compute allocation
```

F9A is qualitative. F10 and ED1-ED3 are locked to their current data/caption definitions.

## 6. Methods structure

A compact Methods section can be organized as:

1. Descriptor and scaling relations
2. Microkinetic model
3. Catalyst productivity and inventory mapping
4. Reactor and process-state optimization
5. Pressure-dependent equipment and catalyst-dependent economics
6. Uncertainty propagation
7. Backward-design and scaling reachability
8. Methanol catalyst-state definition and explicit recycle/separation model
9. Methanol upstream-to-economic rank reconstruction and purge robustness
10. Cross-reaction pathway comparison and evidence boundary
11. Au/TiO2 fixed-condition rank-preservation control and literature calibration
12. Au/TiO2 semi-open robustness extension
13. Decision-aware AI harness, DISCOVER V1 and DISCOVER-BOUNDARY-C1: 11-action interface, CU accounting, anonymous task, fixed scorer/stopping rule, deterministic D reference, repeated sampling, complete-decision endpoint, backward-target secondary endpoint, narrow-window definition and frozen-hash verification

## 7. Supporting Information priorities

Supporting Information should contain the technical evidence needed to trust the main claims:

- NH3-FINAL-1.1 pressure/CAPEX validation and provenance
- Monte Carlo protocol and full distributions
- detailed operating envelopes and cost-pool decomposition
- scaling-manifold derivation and backward-design sweep
- MeOH D01 v3 workbook provenance, four-state rank table, alternative upstream metrics and purge sweep
- cross-reaction pathway provenance/evidence boundary
- Au/TiO2 V1.1 literature anchors and 10,000-draw preservation test
- Au/TiO2 V1.3 semi-open robustness protocol and summary statistics
- DISCOVER action schema, scorer, hashes and cross-model results
- C1 budget curves, narrow-window usage, failure taxonomy, interface intervention and non-binding-allowance audit
- ED1-ED3 source tables and render provenance

## Current-source rule

Current manuscript values should be taken from [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md), [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv), and the claim/figure registries. Historical or superseded values are documented only in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md) and provenance/audit records.
