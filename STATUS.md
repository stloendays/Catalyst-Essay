# Current project status

Snapshot date: **2026-09-17**

## Overall state

The core scientific evidence is frozen for manuscript production. Current work is concentrated on:

1. manuscript integration;
2. publication-quality figure rendering and visual consistency;
3. caption and claim alignment;
4. reproducibility packaging;
5. finalizing the Agent figure and its manuscript wording.

No new NH3, MeOH or Au/TiO2 scientific model sweep is planned as part of this production phase.

## Canonical scientific families

| Family | Current label | State |
|---|---|---|
| Ammonia | **NH3-FINAL-1.1** | frozen / provenance closed |
| Methanol | **MEOH-D01-v3** | frozen |
| Rank-preservation control | **Au/TiO2-RP V1.1** | frozen canonical control |
| Rank-preservation robustness | **Au/TiO2-RP V1.3** | supporting extension |
| Agent benchmark | **DISCOVER V1** | frozen protocol |
| Agent boundary extension | **DISCOVER-BOUNDARY-C1** | completed confirmatory extension |

Version labels are family-specific. The authoritative naming registry is `docs/VERSION_REGISTRY.md` and `data/version_registry.json`.

## NH3-FINAL-1.1

### Headline result

```text
Atomic activity ranking:     Ru > Os > Fe
Economic ranking:            Fe > Ru > Os
```

Catalyst-dependent cost:

- Fe: **15.292 USD/t NH3**
- Ru: **22.031 USD/t NH3**
- Os: **25.832 USD/t NH3**

Rank statistics:

- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- full 15-metal raw Spearman rho: **0.929**

The principal interpretation is a **decision-frontier inversion** rather than a global collapse of the atomistic ranking.

### Uncertainty propagation

For Fe under the frozen 1,000-draw analysis:

- feasibility: **79.9%**
- Top-1 survival: **28.2%**
- Top-3 actionable probability: **94.0%**

### Backward design

- Ru activity-only break-even target: **201.22x**
- scaling-consistent headroom at 673 K: **1.090x**
- maximum headroom over the frozen process-state library: **2.525x**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**

The current activity-only route therefore does not reach Fe cost parity within the frozen scaling-consistent design path.

### Representative optimized operating points

- Fe: approximately **425 C / 180 bar / 30 C separator**
- Ru: approximately **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

### Provenance state

The original FINAL-1.1 source-harness bundle is vendored under `provenance/nh3_final_1_1/source_harness/`.

Repository validation reports:

- **13/13** canonical anchors present;
- **6/6** evidence classes present;
- **6/6** figure mappings present;
- **28/28** manifest files present;
- **0** source-manifest hash mismatches.

F1-F6 are locked to the canonical FINAL-1.1 assets. The provenance transfer did not rerun the scientific model.

## MEOH-D01-v3

The current CO2-to-methanol case contains four Re/TiO2 catalyst-temperature states evaluated through the explicit recycle/separation loop at **2% purge**.

Using STY per g Re as the upstream intrinsic metric:

```text
upstream order
1 wt% Re / 250 C
> 1 wt% Re / 200 C
> 5 wt% Re / 200 C
> 5 wt% Re / 250 C

economic order
5 wt% Re / 200 C
> 1 wt% Re / 200 C
> 1 wt% Re / 250 C
> 5 wt% Re / 250 C
```

Headline statistics:

- Spearman rho: **0.20**
- Kendall tau: **0.00**
- pairwise inversions: **3/6**
- upstream winner falls from **#1 to economic rank #3**

Local leverage at 5 wt% Re / 250 C:

- STY: **0.00289**
- single-pass conversion: **0.05883**
- CH4 suppression: **0.37579**

The current interpretation is a **selectivity-recycle pathway** linking catalyst-state selectivity to feed loss, purge and recycle burden.

## Au/TiO2 rank-preservation control

### V1.1 canonical control

The 2-6 nm particle-size series preserves the complete order after downstream propagation:

- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- **10,000/10,000** predefined literature-envelope draws preserve the full ranking
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

### V1.3 supporting robustness

V1.3 allows moderate candidate-specific kinetic and operating freedom. It remains a supporting robustness result and does not replace V1.1 as the canonical control.

## Cross-reaction comparison

The current manuscript-level comparison is mechanistic:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The historical normalized ratio **273-410** is archived pre-FINAL-1.1 evidence and is not a current quantitative manuscript result. The original metric implementation could not be established sufficiently for promotion under the current evidence package.

## Decision-aware Agent Harness

### DISCOVER V1

Frozen anonymous complete-decision recovery:

- nano: **6/35**
- mini: **15/35**
- strong: **35/35**

The original across-tier adaptive-vs-fixed superiority criterion was not met.

### DISCOVER-BOUNDARY-C1

The deterministic fixed-VOI policy reaches the complete scientific decision at **206 CU**.

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

Under the canonical narrow-window definition, 175-CU narrow-window allocation occurs in **20/20 strong**, **0/20 mini** and **0/20 nano** runs.

The supported manuscript wording is therefore a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed-policy completion threshold**. It should not be described as universal raw-compute saving.

## Figure state

Current main figure architecture is **F1-F10**.

- **F1-F6** — locked NH3-FINAL-1.1 scientific assets.
- **F7** — locked MeOH ranking asset.
- **F8** — locked R-rendered MeOH selectivity/recycle figure.
- **F9A** — qualitative catalyst-to-process pathway comparison.
- **F9B** — locked Au/TiO2 rank-preservation control.
- **F10** — Agent capability-bounded operating-envelope figure; scientific panel data are present, final manuscript/caption lock still in progress.

Publication-layout redraws may change typography, annotation placement and visual style, but must preserve the frozen scientific geometry and values.

## Repository organization

The teacher/supervisor-facing reading path is now:

1. `README.md`
2. `docs/RESEARCH_FRAME.md`
3. `docs/RESULTS_AT_A_GLANCE.md`
4. `docs/FIGURE_MAP.md`
5. `docs/MANUSCRIPT_SKELETON.md`
6. `docs/AGENT_HARNESS.md`

The full documentation index is `docs/README.md`.

A consolidated machine-readable table of the current manuscript headline values is available at:

`data/manuscript_headline_results_2026-09-17.csv`

## Next production tasks

1. continue the R-based visual refresh of manuscript figures while preserving locked values;
2. align figure captions with the current F1-F10 map;
3. finish the F10 caption/claim boundary;
4. clean remaining outdated wording in long audit/legacy documents where it may confuse a first-time reader;
5. assemble the manuscript and Supporting Information around the frozen evidence package.
