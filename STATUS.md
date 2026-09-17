# Current project status

Snapshot date: **2026-09-17**

## Overall state

The core scientific evidence is frozen for manuscript production. Current work is concentrated on manuscript integration, publication-quality figure rendering, Supporting Information organization and reproducibility packaging.

No new NH3, MeOH or Au/TiO2 scientific sweep is planned as part of this production phase.

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
- Fe Top-1 survival: **28.2%**
- Fe Top-3 actionable probability: **94.0%**
- Ru activity-only break-even target: **201.22x**
- scaling-consistent headroom: **1.090x at 673 K; 2.525x maximum**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**

Representative optimized operating points are approximately **425 C / 180 bar / 30 C separator** for Fe and **450 C / 425 bar / 25 C** for Ru; Os has a broad shallow high-pressure minimum.

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
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

No quantitative cross-reaction leverage ratio is promoted in the current manuscript. Superseded values are documented only in `docs/RETIRED_RESULTS.md`.

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

Under the non-binding 5000-CU allowance, median final spend is **714 CU**. The supported claim is a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy completion threshold**, not universal raw-compute saving.

## Figure state

Current main figure architecture is **F1-F10**.

- **F1-F8** — locked
- **F9A** — current qualitative catalyst-to-process pathway panel
- **F9B** — locked rank-preservation control
- **F10** — locked Agent capability-bounded operating-envelope figure with final caption in `figures/agent/F10_CAPTION.md`
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

Current manuscript-facing headline data: `data/manuscript_headline_results_2026-09-17.csv`.

Superseded conclusions, intermediate files and corrected definitions are centralized in `docs/RETIRED_RESULTS.md`. Frozen provenance and audit records remain in the repository for traceability.

## Next production tasks

1. continue R-based visual harmonization of the locked figure set;
2. assemble final main/Extended Data/Supporting Information layouts;
3. complete manuscript text against the current claim and figure registries;
4. run a final link, data and caption consistency pass before supervisor review.
