# Figure map — current manuscript architecture

Snapshot: **2026-09-20**  
Primary ammonia basis: **NH3-FINAL-1.1**

The current main figure architecture is **F1-F10**. This page contains current figure claims only; superseded values are centralized in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).

## F1 — NH3 atomic-to-economic ranking propagation

**Question:** Does the atomic activity ranking survive industrial economic propagation?

- atomic top three: **Ru > Os > Fe**
- economic top three: **Fe > Ru > Os**
- Fe / Ru / Os cost: **15.292 / 22.031 / 25.832 USD/t NH3**

**Role:** establish the principal decision-frontier inversion.

---

## F2 — Rolling Top-K rank correlation

**Question:** Why can a globally correlated screen still give a different decision among the leading candidates?

- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- full 15-metal raw Spearman rho: **0.929**

**Role:** localize the ranking conflict to the decision frontier.

---

## F3 — NH3 uncertainty and decision stability

Updated four-panel structure:

- **a — descriptor decision endpoints:** Fe feasibility **79.9%**, Fe economic Top-1 **68.1%**, atomic-to-economic Top-1 survival **28.2%**, Fe Top-3 actionable **94.0%**.
- **b — joint cost uncertainty:** **P(C_Fe < C_Ru) = 5000/5000**; minimum sampled Ru-Fe gap **2.382 USD/t NH3**.
- **c — alpha* distribution:** p05 / median / p95 = **70.78x / 174.27x / 462.00x**, with canonical **201.22x** shown as reference.
- **d — MeOH rank probability:** canonical D01 economic order retained in **5000/5000** draws; the separately labelled active-Re replacement extension gives the same ordering.

The 68.1% / 28.2% discrepancy is resolved: they are different metrics from the same frozen descriptor MC.

Renderer: `../figures/nh3/render_F03_uncertainty_cost_mc.R`. Caption: `../figures/nh3/F03_CAPTION.md`. Panel data: `../analysis/supervisor_2026_09_20/`.

**Role:** separate descriptor uncertainty, cost uncertainty and downstream decision stability rather than collapsing them into a single robustness percentage.

---

## F4 — Fe / Ru / Os operating envelopes

- Fe: approximately **425 C / 180 bar / 30 C separator**
- Ru: approximately **450 C / 425 bar / 25 C separator**
- Os: broad shallow high-pressure minimum

**Role:** show catalyst-dependent operating regimes after process/economic reoptimization.

---

## F5 — Ru backward-design activity sweep

- Ru activity-only break-even: **201.22x**

**Role:** translate an industrial economic target into a catalyst-property target.

---

## F6 — Scaling-manifold reachability

- activity headroom at 673 K: **1.090x**
- maximum headroom over the frozen process-state library: **2.525x**
- strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**

**Role:** separate the catalyst improvement required by economics from the improvement accessible on the current property manifold.

---

## F7 — CO2-to-MeOH upstream-to-economic ranking reshuffle

Using STY per g Re as the upstream intrinsic metric:

```text
upstream rank                       economic NPC rank
1 wt% Re / 250 C   #1              5 wt% Re / 200 C   #1
1 wt% Re / 200 C   #2      ->      1 wt% Re / 200 C   #2
5 wt% Re / 200 C   #3              1 wt% Re / 250 C   #3
5 wt% Re / 250 C   #4              5 wt% Re / 250 C   #4
```

- Spearman rho: **0.20**
- Kendall tau: **0.00**
- pairwise inversions: **3/6**

**Role:** demonstrate transfer of the ranking-propagation question to a catalyst-state problem with a different process pathway.

**Boundary:** the candidates are catalyst-temperature states at literature points. Purge is reoptimized in the robustness analysis; T/P are not independently optimized per candidate.

---

## F8 — Methane accumulation, purge and selectivity leverage

**Panel A:** NPC versus purge across the four D01 v3 states over the **0.5-40% / 396-level** sweep, with **2% purge** marked as the canonical comparison.

**Panel B:** local leverage at 5 wt% Re / 250 C:

- STY: **0.00289**
- single-pass conversion: **0.05883**
- CH4 suppression: **0.37579**

**Role:** identify selectivity/methane suppression as the dominant tested local economic pathway in the current MeOH regime.

**Status:** **LOCKED**.

---

## F9 — When rankings invert and when they survive

### F9A — Cross-reaction catalyst-to-process pathways

Current evidence is a qualitative mechanism comparison:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

**Role:** show that the dominant propagation pathway is reaction- and process-dependent. No current quantitative cross-reaction ratio is plotted.

### F9B — Au/TiO2 rank-preservation control

- activity rank = burden rank = **2 > 3 > 4 > 5 > 6 nm**
- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- full order preserved in **10,000/10,000** predefined literature-envelope draws
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

**Role:** demonstrate that multiscale propagation can preserve a ranking when the downstream mapping remains monotonic.

V1.3 remains a supporting semi-open robustness annotation rather than a replacement for V1.1.

---

## F10 — Agent capability-bounded operating envelope

**Panel A:** complete-decision recovery versus CU budget across model tiers, with the deterministic fixed-VOI completion threshold at **206 CU** and the strong-tier lowest stable complete-decision budget at **75 CU**.

**Panel B:** canonical narrow-window allocation. For the strong tier the measured series is **7/7 at 150 CU, 20/20 at 175 CU, 1/8 at 200 CU, 0/20 at 225 CU and 0/9 at 250 CU**; under the non-binding 5000-CU allowance it is **0/20**. The weaker tiers have no canonical narrow-window use in their measured cells. This panel now carries the key mechanism: binding budget pressure is what activates scoped window compression.

**Panel C:** decision-stable CU versus final used CU. Under the non-binding 5000-CU allowance, median decision-stable spend is **566 CU**, median post-stability overrun is **148 CU**, and median final spend is **714 CU**.

Add the oracle reference with two clearly separated lower bounds: **7 CU scorer-complete** and **22 CU protocol-complete S1-S3**. Use **22 CU** for the manuscript-facing normalization. Relative to 22 CU: 75 CU = **3.41x**, 52.5 CU decision-stable at the 75-CU cell = **2.39x**, fixed-policy 206 CU = **9.36x**, and non-binding decision-stable 566 CU = **25.73x**.

Boundary cells:

```text
                     175 CU          225 CU
strong adaptive       19/20           20/20
mini adaptive           0/20            6/20
nano adaptive           0/20            0/20
fixed-VOI             incomplete       complete
```

**Role:** support a model-tier-dependent, budget-localized decision-recovery claim below the fixed-policy completion threshold.

**Status:** frozen run data remain valid; the **2026-09-20 semantics are resolved**. The current manuscript renderer is `../figures/agent/render_F10_agent_envelope.R`, which adds the 22-CU protocol oracle and keeps the non-binding 5000-CU control on a separate axis. Caption source: [`../figures/agent/F10_CAPTION.md`](../figures/agent/F10_CAPTION.md). The pre-update Python asset remains provenance until the R render is regenerated and hashed.

---

## Main-text structure

```text
F1-F4   forward propagation and decision-frontier inversion
F5-F6   backward design and reachability
F7-F9   transfer across process pathways and rank-preservation control
F10     decision-aware compute allocation
```

If the journal requires fewer main figures, F3 and F4 remain natural candidates for Extended Data / Supporting Information.

## Figure-production rule

Publication redraws may change typography, annotation placement, panel spacing, line weights and export format. They must preserve the frozen scientific values, data identity and geometry implied by the canonical source.

Figure asset/provenance index: [`../figures/README.md`](../figures/README.md).  
Current numerical summary: [`RESULTS_AT_A_GLANCE.md`](RESULTS_AT_A_GLANCE.md).  
Current machine-readable headlines: [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv).
