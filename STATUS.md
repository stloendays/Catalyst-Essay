# Current project status

Snapshot date: **2026-09-10**

## Research state

**RESEARCH FROZEN FOR DRAFTING.** The current scientific and Agent evidence package is considered complete for manuscript integration, subject to a final numerical / claim-to-evidence audit. Do not add new large API batches, budget points, model tiers, reaction cases or agent-policy variants solely to improve the story. Reopen computation only if the audit identifies a genuine scorer/driver defect, frozen-state mismatch, data-lineage error or reproducibility problem.

Primary freeze record: `docs/RESEARCH_FREEZE_2026-09-10.md`.

## Canonical naming

The authoritative naming registry is `docs/VERSION_REGISTRY.md`; the machine-readable copy is `data/version_registry.json`.

Current labels:

- scientific model: **NH3-FINAL-1.1**;
- methanol case: **MEOH-D01-v3**;
- canonical rank-preservation control: **Au/TiO2-RP V1.1**;
- latest supporting rank-preservation robustness: **Au/TiO2-RP V1.3**;
- Agent umbrella: **Decision-aware Agent Harness**;
- supporting Agent benchmarks: **DRIFT v2** and **TRANSFER v1**;
- formal frozen Agent benchmark: **DISCOVER V1**;
- completed confirmatory boundary extension: **DISCOVER-BOUNDARY-C1**;
- **DISCOVER V2** is reserved for a future protocol redesign and is not a completed current benchmark.

Version numbers are family-specific. A higher number in one family does not supersede another family, and a supporting extension does not automatically replace the canonical evidence source.

## Canonical ammonia model

- Canonical version: **NH3-FINAL-1.1**
- Promotion status: approved and frozen on 2026-09-05
- Archived historical version: NH3-FINAL-1.0
- Canonical run identifier: `outputs/nh3_final_20260905T134204Z`

### Frozen ammonia ground truth

- Atomic activity ranking: **Ru > Os > Fe**
- Optimized economic ranking: **Fe > Ru > Os**
- Fe cost: **15.292 USD/t NH3**
- Ru cost: **22.031 USD/t NH3**
- Os cost: **25.832 USD/t NH3**
- Ru/Fe ratio: **1.441**
- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- Full 15-metal raw Spearman rho: **0.929**
- Fe feasibility: **0.799**
- Fe Top-1 survival: **0.282**
- Fe Top-3 actionable: **0.940**
- Ru activity-only break-even: **201.22x**
- Scaling headroom: **1.090x at 673 K; 2.525x maximum over the process-state library**
- Strict-scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**

NH3-FINAL-1.1 removes the earlier pressure-grid boundary artefact by extending the pressure grid to 10-1000 bar and adding pressure-dependent equipment CAPEX. Representative optima are approximately **425 C / 180 bar / 30 C separator** for Fe and **450 C / 425 bar / 25 C** for Ru; Os has a broad shallow high-pressure minimum.

## Current NH3 lever ordering

Current 1.1 reach values:

- Metal recovery: **0.69**
- Catalyst lifetime: **0.16**
- Electricity: **0.12 at 20 USD/MWh**, weakly discriminatory / absolute-only
- Pressure upper bound: no longer a valid lever because Ru and Os are interior to the grid
- Bed-cap increase: inactive under the current Fe optimum

Current ordering: **recovery >> lifetime >> other tested levers**.

## Canonical methanol case — MEOH-D01-v3

The current MeOH evidence uses four Re/TiO2 catalyst-temperature states and an explicit recycle/separation loop at 2% purge.

Using STY per g Re as the upstream intrinsic-productivity metric:

- upstream order: **1 wt% 250 C > 1 wt% 200 C > 5 wt% 200 C > 5 wt% 250 C**;
- economic order: **5 wt% 200 C > 1 wt% 200 C > 1 wt% 250 C > 5 wt% 250 C**;
- NPC: **943 / 967 / 975 / 1258 EUR/t** in economic-rank order;
- Spearman rho: **0.20**;
- Kendall tau: **0**;
- pairwise inversions: **3/6**;
- upstream winner falls from **#1 to #3**.

The mechanistic interpretation is a **selectivity-recycle pathway**: methane suppression is the strongest tested local economic lever, with STY / conversion / CH4-suppression leverage = **0.00289 / 0.05883 / 0.37579**.

## Rank-preservation family — Au/TiO2-RP

### Au/TiO2-RP V1.1 — canonical control

Literature-calibrated fixed-condition result:

- activity order: **2 > 3 > 4 > 5 > 6 nm**
- downstream catalyst-burden order: **2 > 3 > 4 > 5 > 6 nm**
- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

This remains the manuscript-level canonical counterfactual because it is literature calibrated and physically interpretable.

### Au/TiO2-RP V1.3 — latest supporting robustness

V1.3 relaxes the perfectly fixed operating point while keeping common chemistry and process topology.

Moderate stress:

- **273.15-293.15 K**: exact preservation **92.16%**, mean rho **0.99214**, rho >= 0.9 in **99.98%** of draws;
- **273.15-313.15 K**: exact preservation **72.62%**, mean rho **0.96802**, rho >= 0.9 in **97.56%** of draws.

V1.3 is the latest robustness extension but does **not** replace V1.1 as the canonical control because its process penalties remain generic monotone penalties rather than a fully literature-derived plant TEA.

## Decision-aware Agent Harness

The Agent system is organized as:

```text
Layer A — deterministic multiscale harness
Layer B — decision layer
```

The decision layer evaluates current evidence, identifies decision-sensitive uncertainties or catalyst levers, selects admissible scientific actions, updates ranking/feasibility/reachability evidence and decides whether to stop, continue or redirect computation.

### Supporting benchmark families

- **DRIFT v2** — completed model/interface drift-diagnosis benchmark.
- **TRANSFER v1** — completed reaction-transfer benchmark covering transfer classification, minimum-sufficient-model selection, lever identification and next-calculation scoring.

These support the broader Agent-Harness description but are not the formal quantitative Agent benchmark used for the manuscript claim.

### DISCOVER V1 — frozen canonical Agent benchmark

DISCOVER V1 remains the formal closed-book, budgeted decision-allocation benchmark. It exposes 11 fine-grained actions and uses `1 CU = 1000 MKM state solves` as the scientific-compute budget.

Original cross-model evaluation:

- weak: `gpt-5.4-nano-2026-03-17`
- medium: `gpt-5.4-mini-2026-03-17`
- strong: `gpt-5.5-2026-04-23`
- budgets: **200, 250, 300, 500, 800, 1200, 2000 CU**
- anonymous complete decision: **6/35 / 15/35 / 35/35**
- tier trend: **Z = 6.95**
- pre-registered E-vs-D Go criterion: **not met**

The original supported conclusion is retained: a strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over fixed-VOI D is capability-dependent rather than universal.

### DISCOVER-BOUNDARY-C1 — completed confirmatory extension

C1 uses the **unchanged frozen DISCOVER V1 protocol** and sharpens the location and interpretation of the strong-tier adaptive effect.

Deterministic fixed-VOI policy D reaches the complete decision at **206 CU**.

| tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong E | **19/20** | **20/20** |
| mini E | **0/20** | **6/20** |
| nano E | **0/20** | **0/20** |
| fixed-VOI D | incomplete | complete |

Mechanistic evidence:

- strong narrow-window construction at 175 CU: **20/20**;
- mini at 175 CU: **4/20**;
- nano at 175 CU: **0/20**;
- above the D threshold, strong E reaches the complete decision at about **218-221 CU** versus D at **206 CU**.

Therefore the manuscript-level C1 claim is a **budget-localized, model-tier-dependent decision-completion advantage**, not a universal raw-compute saving. Policy advantage, model capability and compute efficiency must be reported separately.

Phase B completed **80/80 formal runs** (mini 175/225 CU x20 each; nano 175/225 CU x20 each), with **0 smoke runs, 0 infrastructure retries and 0 driver exceptions**. Frozen hashes were **15/15 PASS before and after**.

Integrity note: the original C1 preregistration specified a broader five-budget Phase B and smoke runs. The executed two-budget/no-smoke Phase B was selected for cost control **before the first Phase B API call** but is nonetheless a design deviation from the original preregistration. It is recorded transparently as a post-run audit in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md` and must not be presented as the original preregistered design.

DISCOVER V1 remains frozen. Any change to its pinned task, prompt, action schema, cost model, scorer, stopping rule or policy-D constants defines **DISCOVER V2**. C1 is confirmatory sampling on V1, not V2.

## Manuscript integration status

Current story:

1. NH3 shows a decision-frontier ranking inversion after candidate-specific process/economic reoptimization.
2. MeOH shows a catalyst-state reshuffle through a selectivity-recycle pathway, with top-rank inversion dependent on the upstream screening objective.
3. Au/TiO2-RP V1.1 shows exact rank preservation under a monotonic mapping.
4. Au/TiO2-RP V1.3 shows that strong rank preservation survives moderate semi-open operating/kinetic freedom.
5. Backward design distinguishes economically required catalyst targets from scaling-consistent reachable targets.
6. The Decision-aware Agent Harness adds model-interface and compute-allocation decisions; DISCOVER V1 provides the original formal benchmark and DISCOVER-BOUNDARY-C1 localizes the adaptive advantage to a capability-dependent boundary regime.

Next work is **manuscript production rather than new experiment generation**: claim-to-evidence audit, figure locking, manuscript integration, Methods / SI completion and reproducibility documentation.

## Version policy

- Use **NH3-FINAL-1.1** for all current NH3 manuscript numbers.
- Use **MEOH-D01-v3** for the current MeOH case.
- Use **Au/TiO2-RP V1.1** as canonical rank-preservation evidence and **V1.3** only as supporting robustness.
- Use **DISCOVER V1** as the frozen formal Agent benchmark and **DISCOVER-BOUNDARY-C1** as its completed confirmatory boundary extension.
- Use **DRIFT v2** and **TRANSFER v1** only with their family names.
- Do not describe **DISCOVER V2** as completed unless a new protocol is explicitly frozen and evaluated.
- Frozen filenames and hash-pinned protocol files are not renamed.
