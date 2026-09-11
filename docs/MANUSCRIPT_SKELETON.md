# Manuscript skeleton — current working version

Snapshot date: **2026-09-10**  
All ammonia headline values below use **NH3-FINAL-1.1** unless explicitly labeled historical.

## Working title options

1. **Multiscale economics reshapes catalyst rankings at the industrial decision frontier**
2. **Industrial objectives reshape catalyst rankings across scales**
3. **Catalyst rankings invert under multiscale economic propagation**

## Abstract logic

The abstract should carry the scientific logic rather than a long list of numbers:

1. **Where inversion occurs:** atomic and economic rankings diverge at the decision frontier in ammonia synthesis, and Re-normalized catalyst-state rankings are reshaped after explicit recycle/separation economics in CO2-to-methanol.
2. **Why inversion is conditional rather than inevitable:** a literature-calibrated Au/TiO2 fixed-condition control preserves the upstream ranking exactly when the downstream mapping is monotonic, while a semi-open robustness extension shows that moderate candidate-specific kinetic and operating freedom introduces only limited local reshuffling and leaves the overall rank structure strongly preserved.
3. **How uncertainty and design targets propagate:** atomistic uncertainty can be amplified or attenuated, and backward design can place an economically required catalyst target outside the reachable scaling manifold.
4. **How the mechanism transfers:** NH3 inversion follows an activity–inventory / reactor-demand pathway, whereas the MeOH inversion follows a selectivity–recycle pathway; the MeOH top-rank reversal also depends on which upstream screening metric is used.

A final sentence can introduce the AI layer without making it the source of the physical result: the frozen DISCOVER benchmark tests whether an agent can allocate finite scientific compute to the parts of this chain that matter to the downstream decision, while the C1 boundary extension shows that this decision-recovery advantage is conditioned by model capability and budget.

## 1. Introduction

Catalyst discovery commonly ranks materials using adsorption energies, descriptors, intrinsic turnover frequencies or other atomistic proxies. Industrial selection is made on a different objective: product cost under coupled kinetic, catalyst-inventory, reactor, recycle, separation and replacement constraints.

The central gap is therefore not another activity model, but the missing causal chain from atomistic catalyst properties to the industrial decision.

This work asks:

- When does an atomic catalyst ranking survive multiscale propagation?
- When and why does it invert?
- Which uncertainty is worth reducing for the final industrial decision?
- What catalyst-property improvement is required by an economic target, and is that target physically reachable?

A central falsification test is also required: if the downstream mapping is monotonic, the same implementation should preserve rather than manufacture a ranking inversion. A supporting robustness extension then asks whether preservation survives after relaxing a perfectly fixed operating point.

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

### 3.4 Methanol catalyst-state rankings invert through a selectivity–recycle pathway

The restored D01 v3 CO2-to-methanol case contains four Re/TiO2 catalyst–temperature states evaluated through the same explicit recycle/separation loop at **2% purge**. Using **STY per g Re** as the upstream intrinsic-productivity metric, the upstream ranking is:

```text
1 wt% Re, 250 C   #1   65 g MeOH / g Re / h
1 wt% Re, 200 C   #2   55
5 wt% Re, 200 C   #3   18
5 wt% Re, 250 C   #4   16
```

After propagation to near-full-plant NPC, the economic ranking becomes:

```text
5 wt% Re, 200 C   #1   943 EUR/t
1 wt% Re, 200 C   #2   967 EUR/t
1 wt% Re, 250 C   #3   975 EUR/t
5 wt% Re, 250 C   #4   1258 EUR/t
```

The intrinsic per-Re winner therefore falls from **#1 to #3**, while **5 wt% Re / 200 C** becomes the economic winner. Across the four states, **Spearman rho = 0.20**, **Kendall tau = 0.00**, and **3 of 6 pairwise comparisons invert**.

The inversion is mechanistically consistent with a **selectivity–recycle pathway** rather than a single-variable monotonic penalty. The explicit loop couples CH4 formation to H2 feed loss, gas accumulation, purge, recycle compression and equipment burden. The most CH4-rich state, **5 wt% Re / 250 C** with **S_CH4 = 0.25**, has the highest NPC despite the highest single-pass conversion. Local leverage at that benchmark is **0.00289** for STY, **0.05883** for conversion and **0.37579** for CH4 suppression.

**The rank reshuffle is independent of the upstream screening metric; only the identity of the upstream winner depends on it.** Under all three admissible upstream metrics — STY per g Re, single-pass MeOH yield X·S, and STY per g catalyst — the global statistics are identical (**rho = 0.20, tau = 0.00, 3 of 6 pairs inverted**). What changes is the top rank: the Re-normalized intrinsic metric places 1 wt% Re / 250 C first, and that state falls to economic #3; the yield and per-catalyst metrics place 5 wt% Re / 200 C first, where it coincides with the economic winner. The screening objective therefore decides *which* candidate is mis-ranked at the frontier, not *whether* the frontier is reshuffled.

**The result is invariant to the loop degree of freedom.** The source loop exposes one process variable, the purge fraction, which the D01 v3 workbook sweeps from 0.5 % to 40 % for every state (396 levels). Across the entire sweep the intrinsic per-Re winner (1 wt% Re / 250 C) is **never** the economic winner, the highest-conversion state (5 wt% Re / 250 C) is **never** the economic winner, Spearman rho never exceeds **0.40**, and at least **2 of 6** pairs invert at every purge level. Re-optimizing purge separately for each candidate — the MeOH analogue of the candidate-specific reoptimization used for NH3 — gives 1 wt% Re / 200 C > 5 wt% Re / 200 C > 1 wt% Re / 250 C > 5 wt% Re / 250 C (**rho = 0.40, tau = 0.33, 2/6 inversions**); every per-candidate optimum sits at the 0.5 % lower bound of the sweep, so the 2 % source-anchored point remains the canonical comparison and the sweep is reported as robustness (`data/meoh/meoh_purge_robustness_D01v3.csv`).

Boundary and design logic: the two inversion cases deliberately isolate two channels. In NH3 the candidates are catalyst identities and temperature, pressure and separator temperature are reoptimized per candidate, so the channel tested is activity → inventory → process severity. In MeOH the candidates are **catalyst–temperature states** at measured literature points (four points from one controlled study; no T/P kinetic model exists to reoptimize), and the loop variable is reoptimized per candidate, so the channel tested is selectivity → feed loss / accumulation / purge / recycle. Re purchase price is excluded from the NPC by design. The MeOH case is therefore not a weaker copy of the NH3 protocol but the complementary test of the second pathway, with its single process degree of freedom fully swept.

Primary figures: F7, F8.  
Primary evidence: `MEOH_RANKING_INVERSION.md`, `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`, provenance JSON and rebuilt ranking figure.

### 3.5 Cross-reaction comparison reveals pathway-specific propagation mechanisms

The two reaction cases resolve different catalyst-to-process pathways. In NH3, activity changes propagate primarily through catalyst inventory, reactor demand and process severity. In CO2-to-methanol, selectivity—particularly methane formation—changes feed loss, gas accumulation, purge, recycle and compression burden.

A previously reported denominator-aligned MeOH CH4-suppression / NH3 TOF leverage ratio of **273–410** (midpoint ~**328**) is not used as a current result. The repository-level provenance audit and GitHub Actions revalidation attempt could not establish the exact historical NH3 TOF-economic-leverage metric from pre-audit code, and the frozen FINAL-1.1 source harness required to rerun that exact definition is not retained in this repository. The result is therefore classified **METRIC_EQUIVALENCE_NOT_ESTABLISHED** rather than replaced by a newly constructed ratio.

The manuscript-level conclusion is consequently bounded to the directly supported mechanism: catalyst ranking changes are reaction- and process-pathway dependent. NH3 demonstrates an activity–inventory / reactor-demand route; MeOH demonstrates a selectivity–recycle route. The choice of upstream screening objective can further change which candidate is mis-ranked at the decision frontier.

Primary figure: F9A as a **qualitative pathway panel only**; no current cross-reaction numerical ratio.

### 3.6 A literature-calibrated control shows that multiscale propagation does not intrinsically invert rankings

To test whether ranking inversion is an artefact of the multiscale implementation itself, a separate Au/TiO2 CO-oxidation control was evaluated under a fixed process condition. Candidate states differ only in Au particle size from **2 to 6 nm**, while active element, support, feed composition, temperature, pressure and process topology are held common.

The V1.1 control replaces the original arbitrary downstream coefficients with a literature-anchored physical mapping. The absolute-rate anchor uses a **2.10 nm** Au/TiO2 catalyst with **4.40 wt% Au**, **38% measured dispersion** and a stabilized activity of **8.8 umol CO gcat^-1 s^-1** at **273.15 K and 1 atm**. The nominal particle-size dependence is taken as **TOF ~ d^-0.9**, consistent with the closest-loading literature series.

The resulting activity and downstream catalyst-burden rankings are identical:

```text
2 nm > 3 nm > 4 nm > 5 nm > 6 nm
```

with **Spearman rho = 1.000**, **Kendall tau = 1.000**, **0 pairwise inversions**, and **10,000/10,000** predefined literature-envelope draws preserving the complete order. Literature calibration substantially compresses the burden spread: the 6 nm / 2 nm required-catalyst ratio falls from 19.42x in V1 to **8.064x** in V1.1, but the ordering does not change.

This control is deliberately **not** a full industrial TEA and should not be given unsupported absolute process economics. Its role is narrower and more important: it shows that the same multiscale implementation preserves an upstream ranking when the downstream mapping remains monotonic and no competing process-severity or topology penalty is introduced.

A supporting **V1.3 semi-open robustness extension** relaxes the perfectly fixed operating point while retaining common Au/TiO2 chemistry and process topology. Each particle-size state independently searches temperature and O2/CO ratio inside a literature-constrained low-temperature envelope, with candidate-specific perturbations to activity prefactor and apparent activation energy. Under moderate stress in the primary **273.15–293.15 K** window, exact full ordering is preserved in **92.16%** of 10,000 draws, mean **Spearman rho = 0.99214**, and **99.98%** of draws retain rho >= 0.9. In the wider **273.15–313.15 K** sensitivity, exact preservation is **72.62%**, mean rho is **0.96802**, and **97.56%** of draws retain rho >= 0.9.

V1.3 therefore supports a stronger but still bounded statement: **rank preservation does not require a perfectly fixed operating point; moderate kinetic and operating freedom can introduce occasional local reshuffling while leaving the overall ordering strongly correlated with the upstream ranking.** V1.1 remains the canonical falsification control because the V1.3 process penalties are generic monotone penalties rather than a fully literature-derived plant cost model.

The combined interpretation of F1–F9 is therefore conditional rather than universal: multiscale propagation can **preserve** a catalyst ranking, **weakly reshape** it under moderate downstream flexibility, or **invert / strongly reshape** it when catalyst properties and screening objectives couple strongly enough to downstream process and economic pathways.

Primary figure: F9B.  
Primary evidence: `RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`, `rank_preservation_control_v1_1.csv`.  
Supporting robustness evidence: `RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`, `rank_preservation_semiopen_v1_3.py`, `rank_preservation_semiopen_v1_3_summary.csv`.

### 3.7 The decision-aware agent enables complete decision recovery below the fixed-policy compute threshold

DISCOVER V1 evaluates whether an AI agent can allocate limited scientific compute to the parts of the multiscale chain that determine the final industrial decision. The protocol was frozen before the cross-model evaluation: the task, prompt, 11-action schema, CU cost model, scorer, stopping rule and A–D baselines were unchanged across model tiers. On the anonymous closed-book task, complete-decision recovery was **6/35** for nano, **15/35** for mini and **35/35** for the strong model, with a pooled tier trend of **Z = 6.95**. A complete decision requires recovery of the economic winner, decision pair, backward target and reachability verdict. The original pre-registered hypothesis that adaptive policy E would robustly outperform fixed-VOI policy D across tiers was not supported.

The subsequent **DISCOVER-BOUNDARY-C1** extension keeps the same frozen DISCOVER V1 scientific environment and resolves the local budget boundary rather than redesigning the protocol. Deterministic fixed-VOI policy D reaches the complete decision at **206 CU**. Below that threshold, at **175 CU**, policy E completes the decision in **19/20** strong-model runs but **0/20** mini and **0/20** nano runs. At **225 CU**, where D can already complete, E succeeds in **20/20** strong, **6/20** mini and **0/20** nano runs.

Extending the strong tier further below the threshold does not break decision recovery. At **150 CU** and at **125 CU** the strong model completes the decision in **20/20** runs at each budget, and at 125 CU the median run closes the complete decision after only **80 CU** of spent compute — **39%** of the fixed policy's 206 CU threshold. The lower failure edge of decision recovery therefore lies below the tested range and is not yet located. What does have a floor is the quantitative break-even target: the canonical 201.223443 multiplier is recovered 20/20 at 225 CU, 15/20 at 175 CU, and 11/20 at both 150 and 125 CU, because windows narrow enough to fit the budget place the parity state outside the searched domain. The reachability verdict is unaffected, since `unreachable` follows from the multiplier being far above the 2.5246 headroom rather than from its exact value. Complete decision recovery and exact break-even quantification must therefore be reported as two different thresholds.

The step-level traces identify the allocation mechanism at the below-threshold cell. A run is counted as using narrow-window allocation only if it builds a process window strictly smaller than the full 14,136-state admissible domain **and** completes at least one scoped action against that window; a `bounds` argument that selects the whole domain does not qualify. Under this rule, narrow-window allocation appears only below the fixed-policy completion threshold and only in the strong tier: **7/7** at 150 CU, **20/20** at 175 CU, **1/8** at 200 CU, **0/20** at 225 CU and **0/9** at 250 CU, against **0/20** mini and **0/20** nano at 175 CU. The strong model therefore redirects finite scientific compute from broad process enumeration toward the backward-design and reachability chain exactly when the budget cannot cover full enumeration, and abandons the strategy once it can; the two tested weaker tiers never reproduce the behavior.

The recovered decision is the same decision. At 175 CU the reachability verdict matches the above-threshold cell exactly — Ru classified `unreachable` in **20/20** runs, with scaling headroom **1.0899** at the 673 K reference and **2.5246** across process states, identical to the frozen NH3-FINAL-1.1 anchors and to the 225 CU cell. What degrades below the threshold is the precision of the scalar break-even target: the canonical **201.223443** multiplier is recovered in **15/20** runs at 175 CU against **20/20** at 225 CU, and all five deviations are discrete window-scope artefacts rather than stochastic scatter — four runs return 157.289910 from windows that exclude T_sep = 30 °C, and one returns 209.602546 from a single-state window. The below-threshold claim is therefore complete recovery of the decision, with a stated loss of precision in the break-even scalar.

Improving the weaker tier's tool interface does not move it across the boundary. A declared interface arm (policy E2) gave the mini tier typed tool parameters with pre-execution validation and an explicit remaining-budget block listing the quoted cost of every affordable action, leaving prompt, task, action schema, cost model, environment and scorer verbatim. At 175 CU the intervention eliminated the interface failure mode completely — undeclared-argument errors fell from 18 to **0** and no-tool-call turns from 16 to 4 — and raised correct winner identification from 14/20 to **19/20**. Complete decisions remained **0/20**. Budget errors rose from 36 to 51 despite the explicit budget display, premature `OPTIMIZE_PROCESS` calls rose from 13 to 67, and under both interfaces mini ran `BACKWARD` in **0/20** runs. Because `BACKWARD` is a precondition of the reachability verdict, the barrier is the ordering of the window → optimise → backward → reachability chain under a binding budget, not interface expressiveness or budget visibility. The below-threshold advantage is therefore a model-capability property rather than an artefact of weak scaffolding.

Failure mechanisms separate the two weaker tiers. Classifying every 0-CU action error as an interface, budget or sequencing failure, nano's 109 errors are 81% unaffordable requests and only 8% interface errors: it fails at the compute-accounting layer and never reaches the decision chain. mini's 133 errors are 51% budget, 29% interface and 20% sequencing, including 19 premature `OPTIMIZE_PROCESS` calls and 6 premature `BACKWARD` calls: it reaches the decision chain and fails at the interface and ordering layer. The strong tier produces 12 action errors over 64 runs and no budget errors at any budget. The single non-complete strong run at 175 CU is a probe-before-target ordering failure: it called `TEST_REACHABILITY` without a `required_multiplier` before `BACKWARD` had produced one, and had no budget left for the 2-CU re-classification.

This does not imply a universal compute-efficiency advantage. At 225 CU, where policy D itself reaches the full decision at 206 CU, the strong adaptive policy reaches the full decision at a median of approximately **218 CU**. C1 therefore supports a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed policy's completion threshold**, not universal adaptive superiority or universal raw-compute saving.

Phase B was executed as a cost-motivated reduced extension at the two discriminative cells, 175 and 225 CU, with **80/80 formal runs**, **0 smoke runs**, **0 infrastructure retries**, **0 driver exceptions**, and frozen hashes **15/15 PASS** before and after. The reduction from the originally registered five-budget Phase B and the no-smoke decision were made before the first Phase B API call and are recorded transparently in `DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`; they must not be described as the original preregistered design.

Primary evidence: `CROSS_MODEL_DISCOVER_V1.md`, `CROSS_MODEL_STATS_V1.md`, `DISCOVER_BOUNDARY_C1_RESULTS.md`, `DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`, C1 summary tables, frozen hashes and scored traces.  
Trace-level mechanism evidence: `DISCOVER_BOUNDARY_C1_ADDENDUM_A3_2026-09-11.md`, `discover_boundary_c1_error_taxonomy_summary.csv`, `discover_boundary_c1_error_taxonomy_runs.csv`.  
Low-budget cells and the E2 interface arm: `DISCOVER_BOUNDARY_C1_ADDENDUM_A4_2026-09-11.md`.

## 4. Discussion

The Discussion should focus on implications rather than restating results.

### 4.1 Screening objectives should be defined at the level of downstream economic leverage

A catalyst property is valuable only insofar as it changes a process pathway that matters to the industrial objective. High intrinsic sensitivity is therefore not equivalent to high economic leverage. The MeOH case adds a second point: the apparent decision-frontier inversion can also depend on whether the upstream screen is defined per active metal, per total catalyst mass or by yield.

### 4.2 The relevant uncertainty is decision sensitivity, not atomistic uncertainty alone

A descriptor with large uncertainty may deserve little additional compute if the downstream decision is insensitive to it. Conversely, a smaller uncertainty can be worth resolving if it controls a rank boundary or feasibility transition.

### 4.3 Backward design changes the interpretation of catalyst targets

Instead of asking whether a catalyst can be made “more active,” the framework asks how much improvement is required for an industrial objective and whether that improvement is reachable on the admissible catalyst-property manifold.

### 4.4 Reaction transfer requires pathway transfer, not only model transfer

A new reaction should not inherit the ammonia mechanism by analogy. The relevant question is which catalyst property controls which downstream cost pool in that process architecture.

### 4.5 Ranking inversion is conditional, not an intrinsic consequence of adding more model layers

The Au/TiO2 control provides the counterfactual needed to interpret the two inversion cases. Under the canonical fixed-condition monotonic mapping, the upstream ordering survives unchanged even after the catalyst-demand layer is propagated. The V1.3 semi-open extension then shows that this preservation is not limited to one perfectly fixed operating point: moderate candidate-specific kinetic and operating freedom produces occasional local reshuffling while retaining mean rho near **0.99** in the primary literature-constrained window. The observed inversions in NH3 and MeOH therefore cannot be attributed merely to passing through more model layers; they emerge when downstream coupling changes relative candidate burden, and in MeOH the top-rank reversal also depends on the upstream normalization used for screening.

This distinction sharpens the central claim of the paper: the relevant object is not "multiscale complexity" in the abstract, but the **coupling topology between catalyst properties, screening objectives and downstream decision variables**. The magnitude of candidate-specific downstream coupling must be large enough to overcome the upstream separation before substantial inversion appears.

### 4.6 Agent claims should separate execution capability, boundary recovery and compute efficiency

The cross-model benchmark separates three questions that are easy to conflate. First, complete execution of the multistep scientific decision chain is strongly model-capability dependent. Second, the C1 boundary extension shows that a strong model can recover the full decision below the deterministic fixed-VOI completion threshold by narrowing the process search and reallocating compute toward the unresolved backward/reachability steps. Third, once the deterministic policy has enough budget to complete the same decision, the adaptive policy does not provide a universal raw-compute saving. Agent performance should therefore be reported as a decision-recovery boundary conditioned on model capability and budget, rather than as a general claim that adaptive LLM allocation is always more efficient than a deterministic VOI policy.

## 5. Figures

See [`FIGURE_MAP.md`](FIGURE_MAP.md) for the current nine-figure map and canonical headline values. The rank-preservation control is integrated into **Figure 9B** rather than added as a tenth standalone figure; V1.3 is best used as a small robustness annotation or Supporting Information extension rather than a new main panel. **Figure 9A remains quantitatively on HOLD pending the targeted NH3-FINAL-1.1 cross-reaction leverage revalidation.**

## 6. Methods structure

A compact Methods section can be organized as:

1. Descriptor and scaling relations
2. Microkinetic model
3. Catalyst productivity and inventory mapping
4. Reactor and process-state optimization
5. Pressure-dependent equipment and catalyst-dependent economics
6. Uncertainty propagation
7. Backward-design and scaling reachability
8. Methanol candidate-state definition and explicit recycle/separation model
9. Methanol upstream-to-economic rank reconstruction, screening-metric definitions, and per-candidate purge reoptimization / 0.5–40 % purge robustness sweep (the MeOH analogue of NH3 candidate-specific reoptimization; T/P held at measured points)
10. Cross-reaction leverage normalization and FINAL-1.1 revalidation of the historical TOF-leverage calculation; the historical 2–3% denominator-alignment convention is retained unchanged during revalidation.
11. Au/TiO2 fixed-condition rank-preservation control and literature calibration
12. Au/TiO2 semi-open operating-condition robustness extension
13. Decision-aware AI harness, frozen DISCOVER V1 cross-model benchmark, and DISCOVER-BOUNDARY-C1 confirmatory boundary extension. Report the unchanged 11-action scientific interface, CU accounting, anonymous task, fixed scorer/stopping rule, deterministic D reference, per-tier repeated sampling, step-level `CU_to_full_decision` reconstruction, narrow-window behavior, before/after frozen-hash checks, and the Phase-B design reduction recorded in addendum A2.

## 7. Supporting Information priorities

Supporting Information should contain the technical evidence needed to trust the main claims:

- NH3-FINAL-1.1 pressure-CAPEX audit
- perturbation / sensitivity closure
- Monte Carlo protocol and full distributions
- detailed operating envelopes
- cost-pool decomposition
- scaling-manifold derivation
- MeOH D01 v3 workbook provenance, four-state rank table, alternative upstream metrics and pairwise inversion accounting
- F9A cross-reaction leverage lineage audit and FINAL-1.1 revalidation bundle
- Au/TiO2 rank-preservation preregistration, literature anchors, sensitivity envelope and full 10,000-draw preservation test
- Au/TiO2 V1.3 semi-open operating-condition protocol, stress levels, literature window and full summary statistics
- complete DISCOVER action schema, scorer and budget curves
- named vs anonymous benchmark controls
- zero-tool prior probe
- cross-model per-trace scores and failure matrix
- pre-registered E-vs-D Go/No-Go evaluation
- DISCOVER-BOUNDARY-C1 175/225-CU boundary tables, Wilson intervals, narrow-window usage, failure taxonomy and Phase-B addendum A2

## Version note

Archived NH3-FINAL-1.0 numbers such as 10.199 / 17.592 / 21.321 USD/t, 73.6% feasibility and 2171.56x break-even should remain historical only and should not appear as current manuscript headline values. The historical cross-reaction ratio **273–410 (~328 midpoint)** is likewise a pre-FINAL-1.1 result and is on HOLD until explicitly revalidated against NH3-FINAL-1.1.