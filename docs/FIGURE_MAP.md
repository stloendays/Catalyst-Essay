# Figure map — six-figure manuscript architecture

Snapshot: **2026-09-23**  
Primary ammonia basis: **NH3-FINAL-1.1**

The manuscript now uses **six composite main figures**. The previous F1-F10 assets remain frozen or hash-pinned as source panels and provenance; they are not deleted or renumbered on disk. This document defines the publication-facing grouping.

**Rendered composites (2026-09-23):** `figures/composite/fig1` … `fig6`, each with its build scripts, model tables, structure renders and a README naming every source. The composites carry more panels than the grouping below (schematics, OVITO structure renders and added data views); their panel lettering and captions are in [`MAIN_FIGURE_CAPTIONS_v7_2026-09-23.md`](MAIN_FIGURE_CAPTIONS_v7_2026-09-23.md), and the v10 main text cites that lettering.

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

## Figure 3 — Backward design separates an economic target from a reachable catalyst target

**Question:** If Ru loses economically, how much intrinsic-activity improvement is required, and is that target physically accessible?

**Panel a — activity-only backward sweep**
- canonical Ru activity-only break-even: **201.22x**

**Panel b — scaling-manifold reachability**
- activity headroom at 673 K: **1.090x**
- maximum headroom over frozen process states: **2.525x**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**
- cost-MC p05 activity target: **70.78x**, still far above the **2.525x** maximum headroom

**Source assets:** legacy F5 + F6.

**Role:** show that 201.22x is a canonical economic reference, while the stronger conclusion is that the activity-only target remains unreachable throughout the tested economic envelope.

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

## Figure 6 — Decision-aware agents make the multiscale framework repeatedly executable

**Question:** Once the scientific decision chain is fixed, can the same workflow be orchestrated repeatedly under finite compute without hard-coding every calculation sequence?

**Panel a — complete-decision recovery**
- fixed-policy completion threshold: **206 CU**
- strong lowest tested stable complete-decision allowance: **75 CU**
- protocol-complete S1-S3 oracle: **22 CU**
- 75 CU = **3.41x oracle**
- 75-CU-cell median decision-stable spend: **52.5 CU = 2.39x oracle**

**Panel b — scoped search as the below-threshold mechanism**
- strong tier uses narrow windows in the constrained regime
- narrow-window use at 225 CU: **0/20**
- non-binding 5000-CU allowance: **0/20**

**Panel c — upper cost boundary**
- non-binding median decision-stable spend: **566 CU = 25.73x oracle**
- median post-stability overrun: **148 CU**
- median final spend: **714 CU**

**Interpretation:** budget pressure activates search compression. The Agent acts as the reusable orchestration layer: deterministic reaction-specific tools supply scientific truth, while the policy decides which actions are required to close each decision instance.

**Source assets:** legacy F10 + Agent oracle extension.

**Role:** show how the physical ranking, causal mechanism and reachability framework can be converted from a one-off analysis into a reusable, decision-aware workflow suitable for repeated and batched screening tasks.

---

## Publication-facing source-asset mapping

| New main figure | Source assets / analyses |
|---|---|
| Fig. 1 | legacy F1 + F2 |
| Fig. 2 | legacy F4 + legacy F3a-c + NH3 cost decomposition + Ru equal-price counterfactual |
| Fig. 3 | legacy F5 + F6 |
| Fig. 4 | legacy F7 + F8 + former legacy F3d MeOH rank-probability matrix |
| Fig. 5 | legacy F9A + F9B |
| Fig. 6 | legacy F10 + 22-CU oracle extension |

The legacy F1-F10 files remain provenance-bearing source assets. Composite publication figures may redraw typography, panel arrangement and annotations while preserving the frozen values and source geometry.

Current numerical summary: [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md).  
Current machine-readable headlines: [`../data/manuscript_headline_results_2026-09-20.csv`](../data/manuscript_headline_results_2026-09-20.csv).
