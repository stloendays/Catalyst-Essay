# Manuscript skeleton — current working version

Snapshot date: **2026-09-07**  
All ammonia headline values below use **NH3-FINAL-1.1**.

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

A final sentence can introduce the AI layer without making it the source of the physical result: the frozen DISCOVER benchmark tests whether an agent can allocate finite scientific compute to the parts of this chain that matter to the downstream decision.

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

### 3.5 Cross-reaction comparison reveals pathway-specific economic leverage

After aligning the cost denominator, the normalized MeOH CH4-suppression / NH3 TOF leverage ratio is **273–410**, midpoint approximately **328**.

This supports a reaction-specific interpretation:

- NH3: **activity -> inventory / reactor-demand** pathway
- MeOH: **selectivity -> feed-loss / purge / recycle** pathway

The manuscript-level conclusion is that catalyst ranking inversion is not governed by one universal variable or one universal propagation mechanism. In NH3, candidate-specific process/economic reoptimization reshapes the decision frontier. In MeOH, a different ranking reshuffle appears when an intrinsic per-Re productivity objective is propagated through selectivity-sensitive recycle economics. The choice of upstream screening objective can therefore matter alongside the downstream process coupling.

Primary figure: F9A.

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

### 3.7 Decision-aware computation allocation is model-capability dependent

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

A complete decision requires the whole chain — economic winner, decision pair, backward target and reachability verdict. The positive result is therefore **workflow-execution capability**: complete decision recovery rises strongly with underlying model capability (pooled tier trend Z = **6.95**; nano vs mini Fisher p = 0.036; mini vs strong p = 4 × 10⁻⁸; logistic odds ratio 4.7 per tier step and 2.3 per budget doubling in the nano/mini pair), and the strong model executes the full decision-aware chain reliably.

The strong-tier result stands on its own and should be stated in full:

- **35/35 complete correct decisions at every budget, including 200 CU**, with the exact 201.22× break-even recovered in 34/35 runs, reachability classified correctly 35/35, zero decision regret and **zero action or interface errors** in 70 runs.
- **Policy E is the only policy that completes the decision at 200 CU.** Fixed-VOI D, activity-first B, uncertainty-first C and random all fail there; E succeeds by building a narrow process window (29–52 CU to a stable winner instead of the 111-CU full window), a behaviour observed in 7/70 strong-tier runs and in **0/140** weak-tier runs. This 200-CU advantage over D is repeatable **5/5** in the strong tier.
- At 250–500 CU the strong tier matches D in decision quality while spending 218–268 CU against D's 247–281 CU and keeping the unnecessary-CU fraction at 0.02–0.13, against 0.18–0.55 for the weak tiers.
- The cross-tier failure structure is itself a result: in both weak tiers **P(reachability correct) equals P(full decision)** cell by cell, so the binding step of the chain is the backward → reachability formulation, not the winner (nano recovers the winner 20/20 at ≥ 500 CU). Weak tiers add a tool-interface error class (undeclared arguments, unaffordable requests) in 69–86 % of runs; the strong tier shows none.

The stronger pre-registered claim did **not** hold. Policy E did not demonstrate robust, cross-tier superiority over the deterministic fixed-VOI policy D. The adaptive narrow-window advantage at **200 CU** was repeatable only in the strong tier and did not reproduce in nano or mini. The pre-registered Agent-specific Go criterion was therefore **not met**.

This negative result is retained rather than tuned away. It rejects the general claim **"adaptive Agent E is universally better than fixed-VOI D"**, but it does not reject the Agent framework. The supported statement is:

> **A strong model can execute and exploit decision-aware allocation, but the advantage of adaptive Agent allocation over a fixed-VOI strategy is model-capability dependent rather than universal.**

Primary evidence: `CROSS_MODEL_DISCOVER_V1.md`, `CROSS_MODEL_STATS_V1.md`, frozen hashes and scored traces.

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

### 4.6 Agent claims should separate execution capability from policy superiority

The cross-model benchmark shows that the ability to complete a multistep decision chain is itself capability-dependent. At the same time, a capable adaptive agent does not automatically dominate a strong deterministic VOI baseline. These are distinct claims and should be reported separately.

## 5. Figures

See [`FIGURE_MAP.md`](FIGURE_MAP.md) for the current nine-figure map and canonical headline values. The rank-preservation control is integrated into **Figure 9B** rather than added as a tenth standalone figure; V1.3 is best used as a small robustness annotation or Supporting Information extension rather than a new main panel.

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
10. Cross-reaction leverage normalization
11. Au/TiO2 fixed-condition rank-preservation control and literature calibration
12. Au/TiO2 semi-open operating-condition robustness extension
13. Decision-aware AI harness and frozen DISCOVER V1 cross-model benchmark

## 7. Supporting Information priorities

Supporting Information should contain the technical evidence needed to trust the main claims:

- NH3-FINAL-1.1 pressure-CAPEX audit
- perturbation / sensitivity closure
- Monte Carlo protocol and full distributions
- detailed operating envelopes
- cost-pool decomposition
- scaling-manifold derivation
- MeOH D01 v3 workbook provenance, four-state rank table, alternative upstream metrics and pairwise inversion accounting
- Au/TiO2 rank-preservation preregistration, literature anchors, sensitivity envelope and full 10,000-draw preservation test
- Au/TiO2 V1.3 semi-open operating-condition protocol, stress levels, literature window and full summary statistics
- complete DISCOVER action schema, scorer and budget curves
- named vs anonymous benchmark controls
- zero-tool prior probe
- cross-model per-trace scores and failure matrix
- pre-registered E-vs-D Go/No-Go evaluation

## Version note

Archived NH3-FINAL-1.0 numbers such as 10.199 / 17.592 / 21.321 USD/t, 73.6% feasibility and 2171.56x break-even should remain historical only and should not appear as current manuscript headline values.
