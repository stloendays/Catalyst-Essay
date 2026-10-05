# Figure map — six-figure manuscript architecture

Snapshot: **2026-09-29**  
Primary ammonia basis: **ammonia process–economics model**

The manuscript now uses **six composite main figures**. Reader-facing scientific names follow [`SCIENTIFIC_NAMING.md`](SCIENTIFIC_NAMING.md). The previous F1-F10 assets remain frozen or hash-pinned as source panels and provenance; they are not deleted or renumbered on disk. This document defines the publication-facing grouping.

**Rendered composites (2026-09-23):** `figures/composite/fig1` … `fig6`, each with its build scripts, model tables, structure renders and a README naming every source. The composites carry more panels than the grouping below (schematics, OVITO structure renders and added data views); their panel lettering and captions are in [`MAIN_FIGURE_CAPTIONS.md`](MAIN_FIGURE_CAPTIONS.md), and the current main text cites that lettering.

## Figure 1 — A globally correlated screen can invert at the decision frontier

**Question:** Can atomistic screening preserve global structure while selecting a different leading catalyst industrially?

**Panel a — ranking propagation**
- atomic top three: **Ru > Os > Fe**
- economic top three: **Fe > Ru > Os**
- Fe / Ru / Os cost: **15.292 / 22.031 / 25.832 USD/t NH3**

**Panel b — rolling Top-K fidelity**
- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- full 15-metal raw Spearman rho: **0.929**

**Source assets:** legacy F1 + F2.

**Role:** establish that the failure is local to the decision frontier rather than a global collapse of the atomistic screen.

---

## Figure 2 — Metal cost and process reoptimization jointly define the ammonia decision boundary

**Question:** What causes the Fe-Ru economic reversal, and how robust is that decision near the canonical regime?

**Panel a — candidate-specific operating regimes**
- Fe: approximately **425 C / 180 bar / 30 C separator**
- Ru: approximately **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

**Panel b — causal price intervention and cost decomposition**
- canonical Fe / Ru: **15.292 / 22.031 USD/t NH3**
- canonical Ru-Fe gap: **6.739 USD/t NH3**
- equal-price Ru, fully reoptimized: **14.712 USD/t NH3**
- equal-price Ru optimum: **425 C / 170 bar / 30 C**
- equal-price Ru-Fe: **-0.580 USD/t NH3**
- largest positive canonical gap terms: fresh-feed compression **+4.632**, metal inventory **+1.763**, compressor CAPEX **+1.181 USD/t NH3**

**Interpretation:** the equal-price intervention is the **causal boundary test**. The Fe-over-Ru inversion requires the canonical Ru-Fe price disparity, while the process response is coupled because the Ru optimum shifts strongly when price is changed.

**Panel c — descriptor uncertainty**
- Fe feasibility: **79.9%**
- Fe economic Top-1 probability: **68.1%**
- atomic-to-economic Top-1 survival: **28.2%**
- Fe Top-3 actionable probability: **94.0%**

**Panel d — local economic robustness and backward-target distribution**
- joint cost MC: **P(C_Fe < C_Ru) = 5000/5000**
- minimum sampled Ru-Fe gap: **2.382 USD/t NH3**
- alpha* p05 / median / p95: **70.78x / 174.27x / 462.00x**
- canonical alpha*: **201.22x**

**Source assets:** legacy F4 + legacy F3 panels a-c + `analysis/supervisor_2026_09_20/nh3_cost_decomposition.svg` + equal-price counterfactual outputs. The former MeOH rank-probability panel is removed from the NH3 uncertainty figure and reassigned to Figure 4.

**Role:** separate a large causal intervention from local robustness around the canonical economic regime.

---

## Figure 3 — Backward design separates the required property region from physical reachability

**Question:** If Ru loses economically, what catalyst-property changes are required for parity, and which of those targets remain reachable under the strict scaling relation?

**Panel a — activity-only backward sweep**
- canonical Ru activity-only break-even: **201.22x**
- cost-MC target distribution: p05 / median / p95 = **70.78x / 174.27x / 462.00x**

**Panel b — activity-only scaling-manifold reachability**
- activity headroom at 673 K: **1.090x**
- maximum state-specific headroom over frozen process states: **2.525x**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**
- the activity-only target remains outside the strict-scaling manifold

**Panel c — joint direct-activity/lifetime/recovery backward target region**
- 53-state conservative subset; no new DFT
- at **99% Ru recovery**, required direct activity multiplier is at most:
  - **2.418x** at **10 y** life
  - **1.742x** at **15 y**
  - **1.401x** at **20 y**
- **20 y + 98% recovery** requires at most **2.418x**
- these are upper bounds on the *required target*, because restricting process optimization to 53 already visited states can only overestimate the activity improvement needed

**Panel d — strict-scaling x lifecycle reachability**
- full **14,136-state** strict-scaling audit; no new DFT
- canonical gate reproduced: **21.397873 USD/t at E_N = -1.215 eV**
- critical lifecycle factor: **q* = (1-r)/L = 4.4068 × 10^-4 y^-1**
- parity state: **E_N = -1.230 eV**, **425 C / 190 bar / 30 C**, **4.298 m3**
- inside the prespecified box (**L <= 20 y, r <= 0.99**), the closest point is **20 y + 99% recovery**
- that corner gives **15.36249 USD/t NH3**, **+0.07078 USD/t** above Fe
- exact boundary lies just outside the box: **99.1186% recovery at 20 y**, or **22.69 y lifetime at 99% recovery**
- the **2.525x** all-state activity gain remains a state-specific diagnostic and is not used as a uniform multiplier

**Source assets:** legacy F5 + F6 + `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_target_keypoints.csv` + `scaling_lifecycle_exact_keypoints.csv` + `scaling_lifecycle_exact_global_boundary.csv`.

**Role:** make the backward-design logic explicit as two operations: **economic target inversion -> physical reachability test**. Panel d now closes the second operation and shows that lifecycle co-improvement brings the target close to, but still just outside, the prespecified scaling-constrained property box.
---

## Figure 4 — Methanol ranking reshapes through a selectivity-recycle pathway and remains stable to tested cost uncertainty

**Question:** Does the ranking-propagation problem transfer to a different reaction and process architecture?

**Panel a — upstream-to-economic ranking reshuffle**
Using STY per g Re:
- upstream: **1%-250 > 1%-200 > 5%-200 > 5%-250**
- economic: **5%-200 > 1%-200 > 1%-250 > 5%-250**
- Spearman rho: **0.20**
- Kendall tau: **0.00**
- pairwise inversions: **3/6**

**Panel b — purge robustness and local leverage**
- purge sweep: **0.5-40% / 396 levels**
- max rho over sweep: **0.40**
- at least **2/6** pairs inverted at every purge
- local leverage at 5 wt% Re / 250 C:
  - STY: **0.00289**
  - conversion: **0.05883**
  - CH4 suppression: **0.37579**

**Panel c — candidate-by-rank probability**
- canonical D01 economic order retained in **5000/5000** cost-MC draws
- separately labelled active-Re replacement extension also retains the same order in **5000/5000**

**Boundary:** canonical D01 excludes Re purchase and replacement; sampled metal price and lifetime are therefore structurally inactive in the canonical calculation. The active-Re replacement extension is robustness evidence, not a redefinition of D01.

**Source assets:** legacy F7 + F8 + the MeOH rank-probability matrix formerly placed in legacy F3d.

**Role:** transfer the decision logic to a selectivity-recycle system without mixing MeOH evidence into the NH3 uncertainty figure.

---

## Figure 5 — Catalyst-to-process coupling topology determines whether rankings reshape or survive

**Question:** What transfers across reactions, and when should a ranking remain preserved?

**Panel a — pathway topology**
- **NH3:** intrinsic activity + metal cost -> catalyst inventory + preferred operating regime -> compression / reactor / equipment burden -> economic ranking
- **MeOH:** selectivity -> reactant loss / gas accumulation -> purge / recycle / compression -> economic ranking

**Scope rule:** each reaction is evaluated against its own frozen downstream economic objective. Absolute NH3 and MeOH cost values are **not** compared across reactions.

**Panel b — Au/TiO2 rank-preservation control**
- activity rank = burden rank = **2 > 3 > 4 > 5 > 6 nm**
- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- full order preserved in **10,000/10,000** predefined literature-envelope draws
- 6 nm / 2 nm burden ratio: **8.064x**
- semi-open 273.15-293.15 K extension: **92.16%** exact preservation, mean rho **0.99214**

**Source assets:** legacy F9A + F9B.

**Role:** establish that multiscale propagation does not mechanically create inversions; the transferable object is coupling topology, not a universal scalar descriptor.

---

## Figure 6 — An automated agent extends the analysis to published and computed catalysts

**Question:** Does the ranking change found in the hand-built cases hold across the candidates that publications and databases provide?

- **a** — ACSA workflow: extraction with source location, self-check against the frozen cases, full chain with descriptor-only bound, leaderboards.
- **b** — extraction accuracy by source (`agent/extraction/eval/field_accuracy_by_source.csv`).
- **c** — 138 transition-metal bimetallic surfaces in the bed limit; 5 below Fe, all cheap 3d + Cr/Mo/W (`analysis/nh3_alloy_extension_2026_10_05/`).
- **d** — published methanol comparisons whose leader changes, by leaderboard metric (`analysis/meoh_literature_inversion_2026_10_05/`).
- **e** — two comparison groups, space-time yield against net cost.

**Source assets:** `figures/composite/fig6/make_fig6.py`.

---

## Publication-facing source-asset mapping

| New main figure | Source assets / analyses |
|---|---|
| Fig. 1 | legacy F1 + F2 |
| Fig. 2 | legacy F4 + legacy F3a-c + NH3 cost decomposition + Ru equal-price counterfactual |
| Fig. 3 | legacy F5 + F6 |
| Fig. 4 | legacy F7 + F8 + former legacy F3d MeOH rank-probability matrix |
| Fig. 5 | legacy F9A + F9B |
| Fig. 6 | literature extraction evaluation + bimetallic surface extension + published methanol comparisons |

The legacy F1-F10 files remain provenance-bearing source assets. Composite publication figures may redraw typography, panel arrangement and annotations while preserving the frozen values and source geometry.

Current numerical summary: [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md).  
Current machine-readable headlines: [`../data/manuscript_headline_results_2026-09-20.csv`](../data/manuscript_headline_results_2026-09-20.csv).
