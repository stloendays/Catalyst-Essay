# Figure map — current manuscript architecture

Snapshot: **2026-09-17**  
Primary ammonia basis: **NH3-FINAL-1.1**

The current main figure architecture is **F1-F10**. Each figure is assigned a scientific role; the map below is intended to keep the visual presentation, captions and manuscript claims aligned with the frozen evidence.

## F1 — NH3 atomic-to-economic ranking propagation

**Question:** Does the atomic activity ranking survive industrial economic propagation?

**Content**

- 15-metal intrinsic activity ranking versus optimized catalyst-dependent economic ranking.
- Highlight the decision-frontier metals Ru, Os and Fe.

**Headline values**

- atomic top three: **Ru > Os > Fe**;
- economic top three: **Fe > Ru > Os**;
- Fe / Ru / Os cost: **15.292 / 22.031 / 25.832 USD/t NH3**.

**Role:** establish the principal decision-frontier inversion.

---

## F2 — Rolling Top-K rank correlation

**Question:** Why can a globally correlated screen still give a different decision among the leading candidates?

**Headline values**

- Top-3 Spearman rho: **-0.50**;
- Top-3 Kendall tau: **-0.33**;
- full 15-metal raw Spearman rho: **0.929**.

**Role:** localize the ranking conflict to the decision frontier rather than the full candidate set.

---

## F3 — NH3 uncertainty and decision stability

**Question:** How does descriptor uncertainty propagate into engineering feasibility and candidate actionability?

**Headline values**

- Fe feasibility: **79.9%**;
- Fe Top-1 survival: **28.2%**;
- Fe Top-3 actionable probability: **94.0%**.

**Role:** distinguish numerical uncertainty from decision-changing uncertainty.

---

## F4 — Fe / Ru / Os operating envelopes

**Question:** Where do the leading catalysts prefer to operate once pressure-dependent process economics are included?

**Representative optima**

- Fe: approximately **425 C / 180 bar / 30 C separator**;
- Ru: approximately **450 C / 425 bar / 25 C separator**;
- Os: broad shallow high-pressure minimum.

**Role:** show that catalyst identity changes the economically preferred operating regime and that the ranking result survives process reoptimization.

---

## F5 — Ru backward-design activity sweep

**Question:** How much intrinsic-activity improvement would Ru need to reach Fe cost parity after full process reoptimization?

**Headline value**

- Ru activity-only break-even: **201.22x**.

**Role:** translate an industrial economic target into a catalyst-property target.

---

## F6 — Scaling-manifold reachability

**Question:** Is the backward-design target reachable on the frozen scaling-consistent catalyst-property path?

**Headline values**

- activity headroom at 673 K: **1.090x**;
- maximum headroom over the frozen process-state library: **2.525x**;
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**.

**Role:** separate the catalyst improvement required by economics from the improvement accessible on the current property manifold.

---

## F7 — CO2-to-MeOH upstream-to-economic ranking reshuffle

**Question:** Does the ranking change when measured catalyst-state performance is propagated through an explicit recycle/separation loop?

**Canonical comparison**

Using STY per g Re as the upstream intrinsic metric:

```text
upstream rank                       economic NPC rank
1 wt% Re / 250 C   #1              5 wt% Re / 200 C   #1
1 wt% Re / 200 C   #2      ->      1 wt% Re / 200 C   #2
5 wt% Re / 200 C   #3              1 wt% Re / 250 C   #3
5 wt% Re / 250 C   #4              5 wt% Re / 250 C   #4
```

- Spearman rho: **0.20**;
- Kendall tau: **0.00**;
- pairwise inversions: **3/6**.

**Role:** demonstrate transfer of the ranking-propagation question to a catalyst-state problem with a different process pathway.

**Interpretation boundary:** the four candidates are catalyst-temperature states at literature points. Purge is reoptimized in the robustness analysis; T/P are not independently optimized per candidate in this case.

---

## F8 — Methane accumulation, purge and selectivity leverage

**Question:** Which catalyst-controlled variable drives the economically important pathway behind the MeOH ranking reshuffle?

**Panel A**

NPC versus purge across the four D01 v3 states over the complete **0.5-40% / 396-level** sweep, with **2% purge** marked as the canonical comparison.

**Panel B**

Local leverage at 5 wt% Re / 250 C:

- STY: **0.00289**;
- single-pass conversion: **0.05883**;
- CH4 suppression: **0.37579**.

**Role:** identify selectivity/methane suppression as the dominant tested local economic pathway in the current MeOH regime.

**Status:** locked; canonical R-rendered SVG/PDF/PNG assets and hash manifest are present.

---

## F9 — When rankings invert and when they survive

### F9A — Cross-reaction catalyst-to-process pathways

**Current evidence level:** qualitative mechanism comparison.

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The historical normalized leverage ratio **273-410** is not plotted as a current result because its original NH3 metric implementation could not be established sufficiently under the current evidence package.

**Role:** show that the dominant propagation pathway is reaction- and process-dependent.

### F9B — Au/TiO2 rank-preservation control

**Canonical V1.1 values**

- activity rank = burden rank = **2 > 3 > 4 > 5 > 6 nm**;
- Spearman rho: **1.000**;
- Kendall tau: **1.000**;
- pairwise inversions: **0**;
- full order preserved in **10,000/10,000** predefined literature-envelope draws;
- 6 nm / 2 nm required-catalyst ratio: **8.064x**.

**Role:** demonstrate that multiscale propagation can preserve a ranking when the downstream mapping remains monotonic.

V1.3 remains a supporting semi-open robustness annotation rather than a replacement for the canonical V1.1 control.

---

## F10 — Agent capability-bounded operating envelope

**Question:** Under a fixed scientific-compute interface, where does adaptive decision recovery emerge and where does it disappear across model capability and budget?

**Current panel structure**

- **Panel A:** complete-decision recovery versus CU budget across model tiers, with the deterministic fixed-VOI completion threshold at **206 CU**.
- **Panel B:** canonical narrow-window allocation and window size; the series is non-monotone and should not be drawn as a smooth trend.
- **Panel C:** decision-stable CU versus final used CU, separating decision completion from total spend.

**Boundary values**

```text
                     175 CU          225 CU
strong adaptive       19/20           20/20
mini adaptive           0/20            6/20
nano adaptive           0/20            0/20
fixed-VOI             incomplete       complete
```

**Role:** support a model-tier-dependent, budget-localized decision-recovery claim below the fixed-policy completion threshold.

**Status:** panel data and renderer are present; final caption/manuscript lock remains in progress.

---

## Suggested main-text emphasis

The current story can be read as four linked blocks:

```text
F1-F4   forward propagation and decision-frontier inversion
F5-F6   backward design and reachability
F7-F9   transfer across process pathways and rank-preservation control
F10     decision-aware compute allocation
```

If the journal requires fewer main figures, **F3 and F4** remain natural candidates for Extended Data / Supporting Information because the core narrative is carried most directly by **F1, F2, F5, F6, F7, F8, F9 and F10**.

## Figure-production rule

Publication-layout redraws may change typography, annotation placement, panel spacing, line weights and export format. They must preserve the frozen scientific values, data identity and figure geometry implied by the canonical source.

The figure asset/provenance index is [`../figures/README.md`](../figures/README.md). Current numerical summaries are in [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md) and [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv).
