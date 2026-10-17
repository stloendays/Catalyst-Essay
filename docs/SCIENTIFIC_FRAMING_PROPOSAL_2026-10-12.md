# Scientific framing proposal — conditional ranking fidelity and industrial decision boundaries
**Date:** 2026-10-12  
**Status:** PROPOSAL / NOT CANONICAL / awaiting independent Claude review and supervisor approval.  
**Scope:** framing only. Do not change manuscript, figures, source data, frozen code, numerical claims or tags.

## 1. Proposed overarching scientific question
**English (conceptual question, not manuscript text):**

Under which catalyst-property, process-feasibility and economic conditions does an atomistic or laboratory-scale performance advantage cease to be optimal at the industrial decision level after multiscale propagation? Can we locate the governing decision boundaries and map industrial targets backward into physically reachable and process-feasible catalyst-property regions?

**中文：**

在何种催化剂性质、工艺可行域和经济条件下，原子尺度或实验室尺度的性能优势，经过微观动力学、催化剂用量、反应器及流程优化与经济核算的多尺度传播后，会失去工业最优地位或发生排序反转？能否解释并预测这一决策边界，再从工业经济目标反推物理可达、工艺可行的催化剂性质区域？

This **refines rather than replaces** the original question: when do upstream catalyst rankings survive multiscale propagation and when do they invert?

## 2. Essential distinctions
1. **Atomic/intrinsic ranking** (DFT descriptors, per-active-site TOF) is not identical to **laboratory-performance ranking** (STY, conversion, selectivity, measured at specific T/P/space velocity/loading). Laboratory data have already passed through kinetic and reactor-level effects.
2. **Industrial ranking** is conditional on the admissible process decisions, equipment limits, catalyst inventory/lifetime/recovery, carbon/product boundary and financial assumptions. There is no unique unconditional industrial optimum.
3. Distinguish **different active metals**, **different catalyst formulations/supports/loadings**, **same catalyst at different temperatures**, and **joint catalyst–operating-condition changes**. Do not use 'different catalyst' as shorthand for atomic-metal ranking inversion.
4. Separate **rank-change incidence**, **economically material regret** (e.g. >5%), **source-paper independence**, **feasibility losses**, and **robustness to model structure**. An infeasible laboratory champion is not automatically counted as an inversion.
5. A backward-design result is an **inverse image of the industrial target through the model subject to constraints**. Properties are not themselves 'already propagated'; it is the outcome/decision that arises from propagation.

## 3. Formal decision structure (to test, not claim solved universally)
Let theta be catalyst properties; u be controllable operating/design variables; a encode engineering, thermodynamic and economic assumptions.

C*(theta; a) = min over feasible u in U(theta; a) of C(theta, u; a).

For two candidates i and j, a cost-decision boundary is Delta_C*(i,j; a) = C*_i(a) - C*_j(a) = 0; infeasible regions must be explicitly distinguished.

For an industrial threshold C_target, the backwards-feasible region is:
F(a) = {theta in physically reachable P : exists u in U(theta; a) with C(theta,u;a) <= C_target}.

Report process and economic assumption dependence; avoid implying a universal single threshold or a unique material.

## 4. Evidence ledger — DO NOT MIX statuses
### Established/frozen or selected model evidence (within stated assumptions)
- NH3 15-metal modeled ranking: intrinsic Ru > Os > Fe, modeled economic Fe > Ru > Os; mechanism via catalyst loading, reactor/process operating regime and cost. This is a model-based ranking-inversion case, not industrial experimental proof for all catalysts.
- Au/TiO2 rank-preservation control: under its pinned monotonic, fixed-condition mapping, upstream ranking is preserved; multiscale propagation does NOT force inversion.
- Methanol S5 (printed values, thermodynamic consistency): **15/40** lab STY vs cost top-1 disagreements; **7/40** >5% regret, **6/7** material disagreements from Bansode 2013. Of the **10/32** 'other catalyst' groups, **4** >5% are all Bansode and involve changing temperature; **six same-temperature** differences are all <2%. Excluding Bansode: **8/32** mismatches, **1** with >5% regret. Source dependence must appear next to the percentage.
- Methanol S5 has purge optima at the 0.5% grid floor and high recycle (median about 28 vs plant reference 2.85; check exact common definitions). Decreasing the purge grid floor yields **14/40**, only **2** with >5% regret. Published reference inlet-composition bounds (approx. 4.9–10.2% non-H2/CO2) yield **24–28/40** and **18–25** with >5% regret. These are conditional scenario analyses, not universal industrial limits.
- S5 inventory/conversion sensitivity: different-catalyst mismatches fall from **10/32 to 5/32**; none has >5% regret. This is conditional on a calibrated first-order approach-to-equilibrium surrogate and fixed/selectivity assumptions.
- NH3 literature domain: **7/33** printed-value disagreements, approximate CI **7–37%**; only **3 cross-metal** groups from **2** papers. This is limited external support, not robust cross-metal prevalence.
- Ru/C comparison: parity in a selected KAAP/low-pressure loop depends on how Ru inventory financing and metal recovery are accounted for. Keep matched-loop, global-Fe-optimum, owned/leased metal and cash-flow boundaries separate.

### Exploratory only / pending validation
- PR #55 finds four same-T, >5% cross-formulation comparisons from three papers under multiple inlet constraints with joint catalyst-inventory x purge optimization. **NOT FROZEN.** These do not demonstrate independent cross-elemental-metal inversion.
- PR #56 equipment envelopes show source-dependent feasibility and denominator loss; fixed original lab-STY champion must not be silently reselected after infeasibility.
- PR #59 shows Re/TiO2 interpretation is sensitive to per-g-Re versus per-g-total-catalyst STY normalization; PR #63 is checking corrected laboratory Ar dilution for the In2O3 source. Do not promote four-case evidence until source interpretation and physical reactor constraints close.
- NH3 Ru commercial financing sensitivity in PR #61 is hypothetical, not a confirmed vendor offer; physical KAAP/bed constraints require additional validation.

## 5. Logical scientific architecture
Q1 Ranking fidelity: which atomic/laboratory orderings survive downstream propagation?  
Q2 Causal mechanism and conditional decision boundaries: which catalyst–process–economics interactions produce preservation, inversion or infeasibility?  
Q3 Backward reachability: given industrial target(s), what region of physically reachable catalyst properties is sufficient under feasible process choices?  
Q4 Decision-aware execution: can the frozen deterministic scientific modules be orchestrated to select the most decision-relevant next computations? Keep Agent model-tier/budget limitations and avoid equating orchestration with independent scientific truth.

Suggested narrative ordering: upstream metrics and decision target → controlled NH3 inversion and Au/TiO2 preservation → process/financial boundary identification → methanol conditional sensitivity with appropriate caveats → backward reachable property region → decision-aware Agent and reproducibility.

## 6. What must be decided (not silently assumed)
- Adopt/revise/reject the overarching question after comparing it with the original paper and evidence.
- Is 'industrial decision boundary' demonstrably predicted by *existing* controlled calculations, or is it only mapped descriptively? Define the distinction and necessary tests.
- Is S5 appropriately the diagnostic/unconstrained baseline, an engineering main scenario, or only a sensitivity? Do not choose the largest reversal percentage as primary by rhetorical preference.
- Which exact NH3 Ru/Fe financing and matched-loop statement is defensible? Do not conflate recovery fraction with discounted recovered value.
- Which methanol/field claims must be conditioned on Bansode, temperature, catalyst-loading extrapolation and DOI independence?
- Preserve the Au/TiO2 non-inversion control and both positive and negative Agent findings.

## 7. Review provenance and boundaries
Evidence references:
- Original framing: project Notion page '01 | 核心科学问题' and '12 | GIST / Skeleton'.
- Frozen/selected field analysis: https://github.com/stloendays/Catalyst-Essay/pull/49
- S5 verification: https://github.com/stloendays/Catalyst-Essay/pull/42
- Joint reoptimization (draft): https://github.com/stloendays/Catalyst-Essay/pull/55
- Equipment feasibility (draft): https://github.com/stloendays/Catalyst-Essay/pull/56
- Re normalization (draft): https://github.com/stloendays/Catalyst-Essay/pull/59
- Source Ar correction (draft): https://github.com/stloendays/Catalyst-Essay/pull/63
- Ru recovery financing overlay: https://github.com/stloendays/Catalyst-Essay/pull/57

**Guardrails:** No changes to manuscript, figure captions, result summaries, CI or frozen hashes; no replacement of S5 or other canonical results; this note is an independent framing proposal and is not scientific approval.
