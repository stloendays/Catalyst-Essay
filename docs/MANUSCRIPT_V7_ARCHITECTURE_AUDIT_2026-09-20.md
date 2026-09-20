# Manuscript v7 architecture audit — 2026-09-20

Canonical draft: `docs/MANUSCRIPT_MAIN_TEXT_v7_2026-09-20.md`  
Figure map: `docs/FIGURE_MAP.md`  
Caption set: `docs/MAIN_FIGURE_CAPTIONS_v3_2026-09-20.md`  
Composite registry: `data/main_figure_composite_registry_2026-09-20.csv`

## Architecture problems closed

### 1. Agent no longer competes with the physical science for the center of the paper

The Introduction now introduces DISCOVER only after the deterministic ranking/coupling/reachability problem is established. The Results heading is **“A decision-aware agent is an operational extension of the deterministic framework.”** Methods explicitly state that the Agent does not alter the physical models, process constraints, economic equations or ground-truth decision geometry.

### 2. NH3 mechanism updated after the Ru-price counterfactual

The current pathway is:

`intrinsic activity + metal cost -> catalyst inventory + preferred operating regime -> compression / reactor / equipment burden -> economic ranking`.

The older activity-only shorthand is retired from active manuscript summaries.

### 3. MeOH uncertainty is removed from the NH3 uncertainty figure

The MeOH candidate-by-rank matrix is now assigned to **main Figure 4**, together with the MeOH ranking, purge robustness and leverage results. Main Figure 2 contains NH3 evidence only.

### 4. Equal-price intervention and cost MC are explicitly different tests

The manuscript now uses:
- **causal boundary test** for the full Ru-price-equalization intervention;
- **local robustness test** for the 5,000-draw joint cost Monte Carlo around the canonical regime.

This prevents the equal-price Ru win from appearing inconsistent with Fe remaining lower-cost in 5,000/5,000 local cost draws.

### 5. Backward-design conclusion is envelope-level

The canonical **201.22x** activity requirement is no longer written as a universal Ru material requirement. The principal result is that the activity-only target remains outside the accessible scaling manifold throughout the tested economic envelope: even the cost-MC p05 target (**70.78x**) remains far above the maximum scaling-consistent headroom (**2.525x**).

### 6. NH3 and MeOH economic objectives are no longer treated as symmetric absolute cost models

Methods and Results now state that each reaction is evaluated against its own frozen downstream economic objective. Cross-reaction comparison is restricted to **ranking behavior and catalyst-to-process coupling topology**; absolute NH3 and MeOH cost values are not compared.

### 7. Au/TiO2 is explicitly a rank-preservation control

The control is positioned as evidence that multiscale propagation does not mechanically generate inversions, not as a third process case of equal evidentiary scope to NH3 and MeOH.

### 8. Ten source assets consolidated into six publication-facing figures

The six main figures are:
1. NH3 ranking inversion + rolling Top-K fidelity;
2. NH3 operating regimes + equal-price causal test + uncertainty;
3. backward design + scaling reachability;
4. MeOH transfer + purge/leverage + rank probability;
5. coupling topology + Au/TiO2 preservation control;
6. Agent operating envelope + oracle.

The previous F1-F10 files remain provenance-bearing source assets and are not deleted or overwritten.

## Deterministic text audit

- Main-text figure citations: **Fig. 1 through Fig. 6 only**.
- Working bibliography remains **38 entries**.
- No active `not metal price alone` wording.
- No stale NH3 `activity -> catalyst inventory / reactor demand` pathway wording.
- No MeOH panel cited inside the NH3 uncertainty figure.
- No claim that 201.22x is a universal Ru requirement.
- Required current values present: 14.712, 68.1%, 28.2%, 70.78x, 2.525x, 22 CU, 566 CU, 148 CU and 714 CU.

## Remaining production task

The logic and manuscript architecture are now resolved. The next figure task is purely production-facing: assemble the **six composite figures** from the frozen/hash-pinned source panels, then perform visual QA and lock the composite assets.
