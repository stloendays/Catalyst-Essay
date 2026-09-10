# Catalyst-Essay

**From atomic catalyst ranking to industrial decision-making.**

Catalyst discovery is usually optimized at the atomic scale, while deployment is decided at the system scale. This project asks how much of an upstream catalyst ranking survives propagation through kinetics, catalyst inventory, reactor operation, recycle/separation and economics — and when that ranking reshapes or inverts.

The framework is also run backward: an industrial target is mapped to the catalyst-property improvement required for parity, and the accessible catalyst-property manifold is used to test whether that target is reachable.

## Canonical naming and versions

Project version numbers belong to separate families. Do not compare a bare `V1`, `V2` or `v0.5` across families.

| Family | Current label | Role |
|---|---|---|
| Ammonia model | **NH3-FINAL-1.1** | frozen canonical scientific model |
| Methanol case | **MEOH-D01-v3** | canonical explicit-loop reaction case |
| Rank-preservation control | **Au/TiO2-RP V1.1** | canonical literature-calibrated control |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | latest supporting semi-open extension |
| Agent umbrella | **Decision-aware Agent Harness** | Layer A deterministic harness + Layer B decision layer |
| Drift diagnosis | **DRIFT v2** | completed supporting benchmark |
| Reaction transfer | **TRANSFER v1** | completed supporting benchmark |
| Formal Agent benchmark | **DISCOVER V1** | frozen closed-book, budgeted benchmark; cross-model evaluation complete |
| Agent boundary extension | **DISCOVER-BOUNDARY-C1** | completed confirmatory extension on unchanged DISCOVER V1 protocol |
| Future redesign | **DISCOVER V2** | reserved; not a completed current benchmark |

Human-readable registry: [`docs/VERSION_REGISTRY.md`](docs/VERSION_REGISTRY.md).  
Machine-readable registry: [`data/version_registry.json`](data/version_registry.json).

## Scientific frame

```text
Forward propagation
DFT / descriptor
    -> scaling + BEP
    -> microkinetics
    -> catalyst productivity / inventory
    -> reactor + process optimization
    -> recycle / separation
    -> economics
    -> industrial ranking

Backward design
industrial target
    -> required catalyst-property change
    -> scaling / descriptor manifold
    -> reachable or unreachable

Decision-aware Agent Harness
Layer A: deterministic multiscale models
Layer B: inspect evidence -> choose admissible scientific action
         -> update ranking / feasibility / reachability
         -> stop / continue / redirect
```

The numerical models remain the source of physical and economic results. The AI layer is used for model-interface and compute-allocation decisions that a fixed optimizer cannot make by itself.

## NH3-FINAL-1.1 — current ammonia result

| Result | Current value |
|---|---:|
| Atomic activity top-3 | Ru -> Os -> Fe |
| Economic top-3 | Fe -> Ru -> Os |
| Fe cost | **15.292 USD/t NH3** |
| Ru cost | **22.031 USD/t NH3** |
| Os cost | **25.832 USD/t NH3** |
| Ru / Fe cost ratio | **1.441** |
| Top-3 Spearman rho | **-0.50** |
| Top-3 Kendall tau | **-0.33** |
| Full 15-metal raw Spearman rho | **0.929** |
| Fe feasibility, 1000-draw MC | **79.9%** |
| Fe Top-1 survival | **28.2%** |
| Fe Top-3 actionable probability | **94.0%** |
| Ru activity-only break-even | **201.22x** |
| Scaling-consistent headroom at 673 K | **1.090x** |
| Maximum headroom over process-state library | **2.525x** |

The key ammonia result is a **decision-frontier inversion**, not a global collapse of atomistic screening. The full 15-metal correlation remains high while the leading candidates reorder.

Representative optimized operating points are approximately **425 C / 180 bar / 30 C separator** for Fe and **450 C / 425 bar / 25 C** for Ru. Os has a broad shallow high-pressure minimum.

Backward design gives a second result: Ru would require about **201-fold** intrinsic-activity enhancement to reach Fe cost parity, whereas the current scaling-consistent design path offers at most about **2.525-fold** activity headroom. The activity-only parity target is therefore outside the current reachable manifold.

## MEOH-D01-v3 — catalyst-state ranking reshuffle

The current CO2-to-methanol case contains four Re/TiO2 catalyst-temperature states evaluated through an explicit recycle/separation loop at **2% purge**.

Using **STY per g Re** as the upstream intrinsic-productivity metric:

```text
upstream rank
1 wt% Re / 250 C   #1   65 g MeOH gRe^-1 h^-1
1 wt% Re / 200 C   #2   55
5 wt% Re / 200 C   #3   18
5 wt% Re / 250 C   #4   16

economic rank
5 wt% Re / 200 C   #1   943 EUR/t
1 wt% Re / 200 C   #2   967 EUR/t
1 wt% Re / 250 C   #3   975 EUR/t
5 wt% Re / 250 C   #4   1258 EUR/t
```

- Spearman rho = **0.20**
- Kendall tau = **0**
- pairwise inversions = **3/6**
- upstream winner falls from **#1 to #3**

The ranking change is consistent with a **selectivity-recycle pathway** rather than a single monotonic activity penalty. Local leverage at 5 wt% Re / 250 C is:

| Catalyst-controlled variable | Local leverage |
|---|---:|
| STY | 0.00289 |
| Single-pass conversion | 0.05883 |
| CH4 suppression | **0.37579** |

The top-rank reversal also depends on the upstream screening objective: yield or STY per g catalyst retains the same global rank statistics but changes which state is the upstream winner.

Primary note: [`docs/MEOH_RANKING_INVERSION.md`](docs/MEOH_RANKING_INVERSION.md).

## Cross-reaction economic leverage — quantitative ratio on hold

The qualitative mechanism comparison remains part of the current paper:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

A second-pass data-lineage audit found that the previously quoted normalized ratio **273-410** (midpoint approximately **328**) originated under the archived pre-NH3-FINAL-1.1 denominator normalization and has not been shown to have been recomputed after the FINAL-1.1 pressure-CAPEX/economic closure.

Therefore **273-410 / ~328 is historical, not a current FINAL-1.1 headline value**. Figure 9A is `REVALIDATION_REQUIRED_AFTER_NH3_FINAL_1.1`. The only authorized targeted recomputation is to apply the exact historical TOF-leverage definition to the frozen FINAL-1.1 harness and the unchanged 2%, 2.5%, 3% denominator-alignment assumptions.

See [`docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md), [`docs/CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md`](docs/CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md), and [`docs/F9A_FINAL_1_1_REVALIDATION_TASK.md`](docs/F9A_FINAL_1_1_REVALIDATION_TASK.md).

## Au/TiO2-RP — rank-preservation family

### V1.1 — canonical control

The literature-calibrated fixed-condition control uses 2, 3, 4, 5 and 6 nm Au/TiO2 particle-size states.

Activity and required-catalyst burden retain the same order:

```text
2 nm > 3 nm > 4 nm > 5 nm > 6 nm
```

- Spearman rho = **1.000**
- Kendall tau = **1.000**
- pairwise inversions = **0**
- **10,000/10,000** predefined literature-envelope draws preserve the full ranking
- 6 nm / 2 nm required-catalyst burden ratio = **8.064x**

This is the canonical counterfactual showing that the multiscale implementation does not intrinsically manufacture ranking inversion.

### V1.3 — latest supporting semi-open robustness

V1.3 relaxes the perfectly fixed operating point while retaining common chemistry and process topology.

Moderate stress:

- **273.15-293.15 K**: exact full-order preservation **92.16%**, mean rho **0.99214**, rho >= 0.9 in **99.98%** of draws;
- **273.15-313.15 K**: exact preservation **72.62%**, mean rho **0.96802**, rho >= 0.9 in **97.56%** of draws.

V1.3 is the most advanced robustness extension, but V1.1 remains the canonical control because V1.3 still uses generic monotone process penalties rather than a fully literature-derived plant TEA.

Canonical control: [`docs/RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`](docs/RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md).  
Supporting robustness: [`docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`](docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md).

## Decision-aware Agent Harness

The Agent program contains three benchmark families with different roles.

### DRIFT v2 — supporting interface diagnosis

Tests model/interface drift diagnosis and the response to provenance/model-version inconsistencies.

### TRANSFER v1 — supporting reaction transfer

Tests transfer classification, minimum-sufficient-model selection, catalyst-lever identification and value-based next-calculation selection across reaction cases.

### DISCOVER V1 — formal frozen benchmark

DISCOVER V1 is the manuscript-level closed-book, budgeted benchmark of scientific decision allocation. It exposes 11 fine-grained actions and uses `1 CU = 1000 MKM state solves` as the scientific-compute budget.

Cross-model anonymous complete-decision recovery:

| Tier | Complete decision |
|---|---:|
| nano | **6/35** |
| mini | **15/35** |
| strong | **35/35** |

The positive result is that full decision-chain execution is strongly model-capability dependent. The stronger pre-registered hypothesis — adaptive policy E consistently outperforms fixed-VOI policy D — was **not supported across tiers**.

### DISCOVER-BOUNDARY-C1 — confirmatory boundary extension

C1 retains the frozen DISCOVER V1 task, prompt, 11-action schema, CU accounting, scorer and stopping rule. Deterministic fixed-VOI policy D reaches the full scientific decision at **206 CU**.

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong E | **19/20** | **20/20** |
| mini E | **0/20** | **6/20** |
| nano E | **0/20** | **0/20** |
| D fixed-VOI | incomplete | complete |

At 175 CU, narrow-window construction occurs in **20/20 strong**, **4/20 mini** and **0/20 nano** runs. At 225 CU the strong policy reaches full decision at a median of approximately **218 CU**, later than D at **206 CU**.

Phase B completed **80/80 formal runs**, with **0 smoke**, **0 infrastructure retry**, **0 driver exception**, and frozen hashes **15/15 PASS** before and after. The executed two-budget/no-smoke design was a cost-motivated reduction made before the first Phase B API call and is recorded transparently in addendum A2.

The supported post-C1 statement is:

> **Under the frozen benchmark protocol, the adaptive decision-recovery advantage below the fixed policy's completion threshold is model-tier dependent. This extends decision completion under constrained compute for the strong tier, but does not constitute a universal raw-compute saving.**

DISCOVER V1 remains frozen. Any change to its pinned task, prompt, action schema, cost model, scorer, stopping rule or policy-D constants defines **DISCOVER V2**.

Agent architecture: [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md).  
Original formal report: [`docs/CROSS_MODEL_DISCOVER_V1.md`](docs/CROSS_MODEL_DISCOVER_V1.md).  
Boundary result: [`docs/DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`](docs/DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md).

## Current manuscript logic

1. Atomic and economic catalyst rankings can diverge at the industrial decision frontier.
2. Multiscale uncertainty can be amplified or attenuated rather than monotonically propagated.
3. Backward design distinguishes economically required catalyst targets from physically reachable ones.
4. Ranking changes are pathway- and screening-objective dependent across reactions.
5. Multiscale propagation can also preserve a ranking; preservation remains robust under moderate semi-open flexibility.
6. Decision-aware scientific computation is model-capability dependent; C1 localizes the strong-tier adaptive advantage below a deterministic completion threshold rather than showing universal compute saving.

## Current audit / figure state

- **F7:** locked current MeOH ranking asset.
- **F8:** scientific design frozen; R renderer committed; final SVG/PDF/PNG render pending because current GitHub-hosted workflow attempts fail before any job step is assigned/executed.
- **F9B:** locked Au/TiO2 V1.1 SVG.
- **F1-F6:** current FINAL-1.1 numerical claims are frozen but direct raw provenance/assets still need repository closure.
- **F9A:** targeted FINAL-1.1 numerical revalidation required; historical 273-410 ratio is on HOLD.

## Reading guide

- Current project status: [`STATUS.md`](STATUS.md)
- Canonical naming/version registry: [`docs/VERSION_REGISTRY.md`](docs/VERSION_REGISTRY.md)
- Scientific frame: [`docs/RESEARCH_FRAME.md`](docs/RESEARCH_FRAME.md)
- Manuscript skeleton: [`docs/MANUSCRIPT_SKELETON.md`](docs/MANUSCRIPT_SKELETON.md)
- Figure map: [`docs/FIGURE_MAP.md`](docs/FIGURE_MAP.md)
- Results snapshot: [`docs/RESULTS_AT_A_GLANCE.md`](docs/RESULTS_AT_A_GLANCE.md)
- Claim audit: [`docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md`](docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md)
- Second-pass audit exception: [`docs/CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md`](docs/CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md)
- Agent Harness: [`docs/AGENT_HARNESS.md`](docs/AGENT_HARNESS.md)
- Data index: [`data/README.md`](data/README.md)

---

*Current promoted scientific claims use NH3-FINAL-1.1, MEOH-D01-v3, Au/TiO2-RP V1.1/V1.3, DISCOVER V1 and DISCOVER-BOUNDARY-C1 according to the evidence roles defined in the version registry. The historical 273-410 cross-reaction ratio is excluded from current FINAL-1.1 claims until targeted revalidation closes.*
