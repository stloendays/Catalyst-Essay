# Current project status

Snapshot date: **2026-09-20**

## Overall state

The supervisor-requested **2026-09-20 targeted analyses are complete**. Existing frozen provenance remains unchanged; the new counterfactual, joint cost-MC and oracle outputs are under `analysis/supervisor_2026_09_20/`.

The resulting interpretation is now fixed for the next manuscript pass: equalizing Ru to the Fe metal price flips the NH3 economic order; bounded joint cost uncertainty around the canonical regime leaves Fe lower-cost in 5000/5000 draws; and the Agent protocol-complete oracle floor is 22 CU.

## Canonical scientific families

| Family | Current label | State |
|---|---|---|
| Ammonia | **NH3-FINAL-1.1** | frozen / provenance closed |
| Methanol | **MEOH-D01-v3** | frozen |
| Rank-preservation control | **Au/TiO2-RP V1.1** | frozen canonical control |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | supporting extension |
| Agent benchmark | **DISCOVER V1** | frozen protocol |
| Agent boundary extension | **DISCOVER-BOUNDARY-C1** | completed confirmatory extension |

## NH3-FINAL-1.1

```text
Atomic activity ranking:  Ru > Os > Fe
Economic ranking:         Fe > Ru > Os
```

Key values:

- Fe / Ru / Os cost: **15.292 / 22.031 / 25.832 USD/t NH3**
- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- full 15-metal raw Spearman rho: **0.929**
- Fe feasibility: **79.9%**
- Fe economic Top-1 probability under descriptor uncertainty: **68.1% (681/1000)**
- atomic-to-economic Top-1 survival: **28.2%**
- Fe Top-3 actionable probability: **94.0%**
- Ru activity-only break-even target: **201.22x**
- scaling-consistent headroom: **1.090x at 673 K; 2.525x maximum**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**

Representative optimized operating points are approximately **425 C / 180 bar / 30 C separator** for Fe and **450 C / 425 bar / 25 C** for Ru; Os has a broad shallow high-pressure minimum.

**Ru-price counterfactual:** with Ru metal price set equal to Fe = **8 USD/kg**, full reoptimization gives Ru = **14.712 USD/t** at **425 C / 170 bar / 30 C**, **0.580 USD/t below Fe**. The baseline inversion therefore depends on the Ru-vs-Fe metal-price disparity, with process reoptimization mediating the response. The canonical 6.739 USD/t gap is dominated by fresh-feed compression (+4.632), metal inventory (+1.763) and compressor CAPEX (+1.181 USD/t), partly offset by vessel/recycle/reactor terms.

**Joint cost MC:** 5,000 preregistered draws give **P(C_Fe < C_Ru) = 1.000**; alpha* p05 / median / p95 = **70.78x / 174.27x / 462.00x**.

The FINAL-1.1 source-harness bundle is under `provenance/nh3_final_1_1/source_harness/`. Repository validation reports **13/13 canonical anchors, 6/6 evidence classes, 6/6 figure mappings, 28/28 manifest files and 0 source-manifest hash mismatches**.

## MEOH-D01-v3

Using STY per g Re as the upstream intrinsic metric:

```text
upstream order
1 wt% Re / 250 C > 1 wt% Re / 200 C > 5 wt% Re / 200 C > 5 wt% Re / 250 C

economic order
5 wt% Re / 200 C > 1 wt% Re / 200 C > 1 wt% Re / 250 C > 5 wt% Re / 250 C
```

Headline statistics are **rho = 0.20**, **tau = 0.00** and **3/6 pairwise inversions**. Local leverage at 5 wt% Re / 250 C is **0.00289 / 0.05883 / 0.37579** for STY / single-pass conversion / CH4 suppression.

The 2026-09-20 cost-parameter MC retains the canonical four-candidate economic order in **5,000/5,000** draws. A separately labelled active-Re replacement extension also preserves the same order in **5,000/5,000** draws.

## Au/TiO2 rank-preservation control

The canonical V1.1 control preserves the complete 2-6 nm ranking:

- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full order
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

V1.3 remains a supporting semi-open robustness extension.

## Cross-reaction comparison

The current manuscript-level comparison is mechanistic:

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

Each reaction is evaluated against its own frozen downstream economic objective. Absolute NH3 and MeOH cost values are not compared across reactions. No quantitative cross-reaction leverage ratio is promoted in the current manuscript. Superseded values are documented only in `docs/RETIRED_RESULTS.md`.

## Decision-aware Agent Harness

DISCOVER V1 anonymous complete-decision recovery:

- nano: **6/35**
- mini: **15/35**
- strong: **35/35**

DISCOVER-BOUNDARY-C1 uses the unchanged frozen V1 protocol. The deterministic fixed-VOI policy reaches the complete decision at **206 CU**.

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

For the strong tier, **75 CU** is the lowest tested stable complete-decision budget. Canonical narrow-window allocation is **7/7 at 150 CU, 20/20 at 175 CU, 1/8 at 200 CU, 0/20 at 225 CU and 0/9 at 250 CU**; the weaker tiers have no canonical narrow-window use in their measured cells.

Under the non-binding 5000-CU allowance, median decision-stable spend is **566 CU**, median final spend is **714 CU**, and median post-stability overrun is **148 CU**. Canonical narrow-window use is **0/20** in this condition. The revised interpretation is that budget pressure activates scoped window compression; when the allowance becomes non-binding, the policy no longer narrows the process domain and stabilizes the complete decision much later, then continues for a further median 148 CU.

The supported claim remains a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy completion threshold**, not universal raw-compute saving.

Oracle analysis gives a literal scorer-complete floor of **7 CU** and a protocol-complete S1-S3 floor of **22 CU**. The **22-CU** value is the manuscript-facing normalization: strong 75-CU allowance = **3.41x**, strong median decision-stable spend at 75 CU (52.5) = **2.39x**, fixed-policy threshold 206 = **9.36x**, and non-binding decision-stable median 566 = **25.73x**.

## Figure state

Current publication-facing figure architecture is **six composite main figures**. The previous F1-F10 files remain source assets/provenance and are mapped into the six figures in `docs/FIGURE_MAP.md`.

- **F1-F2, F4-F8** — locked
- **F3** — updated R asset rendered on 2026-09-20; SHA-256 manifest generated; final visual QA/re-lock pending
- **F9A** — current qualitative catalyst-to-process pathway panel
- **F9B** — locked rank-preservation control
- **F10** — updated R asset rendered on 2026-09-20 with 22-CU oracle and 566 + 148 non-binding decomposition; SHA-256 manifest generated; final visual QA/re-lock pending
- **ED1-ED3** — locked Agent Extended Data panels

Publication redraws may change typography, annotation placement, panel spacing and export format, but must preserve the frozen values and traceability.

## Repository organization

Recommended supervisor reading path:

1. `README.md`
2. `docs/RESEARCH_FRAME.md`
3. `docs/RESULTS_AT_A_GLANCE.md`
4. `docs/FIGURE_MAP.md`
5. `docs/MANUSCRIPT_SKELETON.md`
6. `docs/AGENT_HARNESS.md`

Current manuscript-facing headline data: `data/manuscript_headline_results_2026-09-20.csv`.

Superseded conclusions, intermediate files and corrected definitions are centralized in `docs/RETIRED_RESULTS.md`. Frozen provenance and audit records remain in the repository for traceability.

## Supervisor-requested targeted analyses — 2026-09-20

**Completed.** Full execution record: `analysis/supervisor_2026_09_20/README.md`. The original request and closure are in `docs/SUPERVISOR_FEEDBACK_2026-09-20.md`.

## Current manuscript draft

The current integrated main-text draft is **`docs/MANUSCRIPT_MAIN_TEXT_v7_2026-09-20.md`**. It resolves the architecture issues identified after v6: the Ru-price result is framed as a causal boundary distinct from local cost-MC robustness; the backward-design claim is envelope-level rather than a universal 201.22x requirement; MeOH rank probability is moved out of the NH3 uncertainty figure; cross-reaction transfer is defined by coupling topology rather than objective equivalence; and the Agent is explicitly an operational extension of the deterministic framework. Current six-figure captions are in **`docs/MAIN_FIGURE_CAPTIONS_v3_2026-09-20.md`**.

## Next production tasks

1. assemble the six composite manuscript figures from the already frozen/hash-pinned source assets;
2. run a cross-document audit of v7 against the claim/evidence registry, six-figure captions and Methods definitions;
3. consolidate Supporting Information numbering for the NH3 cost decomposition, full uncertainty protocols and MeOH active-Re extension;
4. tighten references and Data/Code Availability for submission;
5. generate the next Word/PDF manuscript artifact only after the v7 architecture audit closes.
