# Manuscript skeleton

Current editorial locks: [`MANUSCRIPT_EDITORIAL_LOCKS.md`](MANUSCRIPT_EDITORIAL_LOCKS.md). Semantic names: [`SCIENTIFIC_NAMING.md`](SCIENTIFIC_NAMING.md).

Snapshot date: **2026-09-20**  
Ammonia basis: **ammonia process–economics model**  
Current main text: **MANUSCRIPT_MAIN_TEXT.md**

## Canonical story

The paper now follows one dependency chain:

ranking fidelity
 -> catalyst-to-process coupling
 -> causal boundary
 -> backward reachability
 -> scalable decision automation

The scientific core is catalyst ranking, coupling and reachability at the industrial decision frontier. The Agent is the **scaling and automation layer** that turns this deterministic logic into a reusable workflow for repeated decision instances.

## Working title

**Multiscale economics reshapes catalyst rankings at the industrial decision frontier**

## Abstract logic

1. Atomistic screening can remain globally correlated while selecting a different leading candidate industrially.
2. In NH3, Ru > Os > Fe becomes Fe > Ru > Os after candidate-specific process and economic propagation.
3. A Ru-price-equalization counterfactual flips the Fe-Ru order, identifying **metal cost coupled to process reoptimization** as the causal boundary.
4. Local joint economic uncertainty around the canonical regime leaves Fe lower-cost in 5,000/5,000 draws.
5. Backward design shows that the activity-only Ru target remains outside the scaling-consistent manifold throughout the tested economic envelope.
6. MeOH transfers the decision logic through a different selectivity-recycle pathway, while Au/TiO2 shows that ranking preservation is possible under a common monotonic mapping.
7. The Agent is introduced as the workflow-execution layer that makes the same deterministic decision logic reusable and batchable across repeated screening tasks.

## 1. Introduction

The Introduction should answer four questions in order:

1. **Why is global catalyst-screen quality insufficient?**  
   Screening is comparative, and industrial effort concentrates near the leading candidates.

2. **What is missing from existing catalyst/process integration?**  
   The key object here is the ordering among discrete screened candidates after candidate-specific process and economic propagation.

3. **What does backward design add?**  
   It converts the industrial decision into a required catalyst-property shift and tests whether the shift is reachable on the admissible material manifold.

4. **What transfers across reactions?**  
   Not a universal descriptor or universal inversion mechanism, but the **catalyst-to-process coupling topology**.

Agent context should occupy the closing part of the Introduction as a **methodological contribution in workflow scalability**. It is not the source of the physical mechanism, but it is a first-class contribution to making the framework repeatedly executable.

## 2. Framework

### 2.1 Forward propagation

descriptor / intrinsic property -> scaling + microkinetics -> catalyst productivity / inventory -> process optimization -> system-specific economic objective -> industrial ranking

### 2.2 Causal boundary test

change one predefined driver -> preserve all other model conventions -> reoptimize the full process -> test whether the industrial decision flips

### 2.3 Backward design

industrial parity target -> required catalyst-property improvement -> admissible descriptor / scaling manifold -> reachable or unreachable

### 2.4 Decision-aware automation and scaling layer

reaction-specific deterministic tools + shared decision state + compute budget -> choose admissible scientific action -> execute tool -> update ranking / feasibility / parity / reachability -> stop / continue / redirect

The AI layer allocates computation and turns the deterministic framework into a reusable execution workflow. Scientific truth remains in the reaction-specific deterministic tools.

## 3. Results

### 3.1 A globally correlated screen can invert at the decision frontier

NH3:
- atomic top three: **Ru > Os > Fe**
- economic top three: **Fe > Ru > Os**
- Fe / Ru / Os: **15.292 / 22.031 / 25.832 USD/t NH3**
- Top-3 Spearman: **-0.50**
- full-15 Spearman: **0.929**

Primary figure: **Fig. 1**.

### 3.2 Metal cost and process reoptimization define the ammonia decision boundary

Canonical operating regimes:
- Fe: **425 C / 180 bar / 30 C separator**
- Ru: **450 C / 425 bar / 25 C**
- Os: broad shallow high-pressure minimum

Equal-price causal intervention:
- Ru price set to Fe = **8 USD/kg**
- reoptimized Ru = **14.712 USD/t NH3**
- optimum shifts to **425 C / 170 bar / 30 C**
- Ru - Fe = **-0.580 USD/t NH3**

Canonical 6.739 USD/t Ru-Fe gap:
- fresh compression **+4.632**
- metal inventory **+1.763**
- compressor CAPEX **+1.181**
- refrigeration **+0.629**
- offsets from vessel pressure, recycle compression and reactor base

Descriptor uncertainty:
- Fe feasible **79.9%**
- Fe economic Top-1 **68.1%**
- atomic-to-economic Top-1 survival **28.2%**
- Fe Top-3 actionable **94.0%**

Local economic robustness:
- **P(C_Fe < C_Ru) = 5000/5000**
- minimum Ru-Fe gap **2.382 USD/t**
- alpha* p05 / median / p95 **70.78x / 174.27x / 462.00x**

Interpretive rule: **Equal-price intervention = causal boundary test. Joint cost MC = local robustness test.**

Primary figure: **Fig. 2**.

### 3.3 Backward design closes the activity-only route throughout the tested economic envelope

- canonical alpha*: **201.22x**
- cost-MC p05 alpha*: **70.78x**
- scaling headroom at 673 K: **1.090x**
- maximum headroom: **2.525x**
- strict-scaling Ru minimum: **21.398 USD/t NH3 at E_N = -1.215 eV**

The main claim is not that 201.22x is a universal Ru requirement. It is that **the backward-designed activity target remains outside the accessible scaling manifold throughout the tested economic envelope**.

Primary figure: **Fig. 3**.

### 3.4 Methanol transfers the ranking problem through a selectivity-recycle pathway

Canonical D01:
- upstream per-Re order: **1%-250 > 1%-200 > 5%-200 > 5%-250**
- economic order: **5%-200 > 1%-200 > 1%-250 > 5%-250**
- rho **0.20**, tau **0.00**, inversions **3/6**

Purge robustness:
- **0.5-40% / 396 levels**
- rho never above **0.40**
- at least **2/6** inverted pairs throughout

Local leverage:
- STY **0.00289**
- conversion **0.05883**
- CH4 suppression **0.37579**

Cost-side rank probability:
- canonical D01 order retained **5000/5000**
- active-Re replacement extension also **5000/5000**

The MeOH probability matrix belongs here, not in the NH3 uncertainty figure.

Primary figure: **Fig. 4**.

### 3.5 Coupling topology explains both reshaping and preservation

NH3: intrinsic activity + metal cost -> catalyst inventory + preferred operating regime -> compression / reactor / equipment burden -> economic ranking

MeOH: selectivity -> reactant loss / gas accumulation -> purge / recycle / compression -> economic ranking

Cross-reaction scope rule: **Each reaction uses its own frozen downstream economic objective. Absolute economic values are not compared across reactions.**

Au/TiO2 control:
- rank **2 > 3 > 4 > 5 > 6 nm**
- rho **1.000**
- tau **1.000**
- **0** inversions
- **10,000/10,000** full preservation
- semi-open primary extension: **92.16%** exact, mean rho **0.99214**

Primary figure: **Fig. 5**.

### 3.6 Decision-aware agents make the workflow reusable and scalable

The physical decision chain is fixed before Agent orchestration. This separation allows the workflow logic to be reused while reaction-specific scientific modules are replaced or extended.

The frozen primary endpoint is `full_decision_correct = winner_correct ∧ pair_decision_correct ∧ reachability_correct`; numerical recovery of the backward parity multiplier is a separate quantitative secondary endpoint.

- deterministic completion: **206 CU**
- protocol-complete oracle: **22 CU**
- strong lowest stable allowance: **75 CU = 3.41x oracle**
- 75-CU-cell median decision-stable spend: **52.5 CU = 2.39x oracle**
- canonical 201.22x backward-target recovery: **9/20 at 75 CU**, **20/20 at 225 CU**
- narrow-window allocation at 175 CU: **20/20 strong**, **0/20 mini**, **0/20 nano**
- non-binding narrow-window use: **0/20**
- non-binding decision stability: **566 CU**
- median post-stability spend: **148 CU**
- median final spend: **714 CU**

Main interpretation: **Binding budget pressure activates scoped search compression. The Agent supplies the orchestration layer that repeatedly executes a predefined scientific decision geometry; reaction-specific tools supply the physical ranking and mechanism.**

Primary figure: **Fig. 6**.

## 4. Discussion

The Discussion should follow the same dependency chain:

1. **Decision-frontier rank fidelity** — full-set correlation can hide a different leading industrial choice.
2. **Causal price-process coupling** — equal-price reversal shows that the Fe-Ru inversion depends on the price disparity, while the large shift in the Ru optimum shows process mediation.
3. **Decision-sensitive uncertainty** — descriptor uncertainty, a large causal intervention and local economic robustness answer different questions.
4. **Backward reachability** — the useful design statement is envelope-level unreachability, not a universal 201x material constant.
5. **Pathway transfer, not objective equivalence** — NH3 and MeOH are compared through coupling topology, not through absolute production-cost values.
6. **Scalable workflow execution** — Agent results show how the deterministic decision framework can be repeatedly executed under finite compute rather than rebuilt as a one-off analysis.

## 5. Main figures

The publication-facing architecture is now **six composite figures**:

Fig. 1  NH3 ranking inversion + rolling Top-K fidelity
Fig. 2  NH3 operating regimes + equal-price causal test + uncertainty
Fig. 3  backward design + scaling reachability
Fig. 4  MeOH transfer + purge/leverage + rank probability
Fig. 5  cross-reaction coupling topology + Au/TiO2 preservation control
Fig. 6  Agent operating envelope + oracle + scalable workflow execution

The previous F1-F10 files remain source assets/provenance. See **FIGURE_MAP.md**.

## 6. Methods structure

1. Multiscale decision analysis and system-specific economic objectives
2. NH3 descriptors, kinetics and process-state optimization
3. NH3 catalyst-dependent economics
4. Descriptor uncertainty propagation
5. Ru price-equalization causal intervention
6. Joint cost-parameter Monte Carlo
7. Backward activity design and scaling reachability
8. methanol recycle–economics state definition and explicit recycle/separation model
9. MeOH purge robustness and alternative upstream metrics
10. MeOH cost uncertainty and active-Re replacement extension
11. Cross-reaction evidence boundary
12. Au/TiO2 rank-preservation control and semi-open extension
13. ACSA workflow-scaling layer, CU accounting, oracle definitions and reusable tool-interface design

## 7. Supporting Information priorities

- NH3 pressure/CAPEX validation
- full Ru-Fe cost decomposition
- equal-price counterfactual audit
- descriptor-MC and joint cost-MC protocols/distributions
- backward-design sweep and scaling-manifold derivation
- MeOH workbook provenance and purge sweep
- active-Re replacement extension
- Au/TiO2 literature calibration and semi-open robustness
- ACSA action schema, scorer, oracle proof, raw boundary series and non-binding audit
- composite-figure panel provenance

## Current-source rule

Current manuscript values should be taken from **RESULTS_AT_A_GLANCE.md**, **../data/manuscript_headline_results_2026-09-20.csv**, and the claim/figure registries. Historical or superseded values remain only in **RETIRED_RESULTS.md** and provenance/audit records.
