# Main figure captions v2 — 2026-09-20

These captions match the current **F1-F10** manuscript architecture and the 2026-09-20 supervisor-requested extensions. Detailed source/provenance remains in `docs/FIGURE_MAP.md`, `figures/README.md`, `figures/nh3/F03_CAPTION.md` and `figures/agent/F10_CAPTION.md`.

## Figure 1 | Atomic activity and industrial economics select different ammonia catalysts

Intrinsic activity ranks the leading metals **Ru > Os > Fe**, whereas candidate-specific process and economic optimization gives **Fe > Ru > Os**. The corresponding catalyst-dependent costs are **15.292, 22.031 and 25.832 US dollars per tonne of NH3** for Fe, Ru and Os, respectively. The figure establishes the decision-frontier inversion that motivates the multiscale analysis.

## Figure 2 | Global rank agreement masks a local inversion at the decision frontier

Rolling Top-K rank correlation compares the intrinsic activity order with the downstream economic order as progressively weaker candidates are added. The leading three candidates give **Spearman rho = -0.50** and **Kendall tau = -0.33**, whereas the full 15-metal screen retains a raw **Spearman rho = 0.929**. Strong global agreement can therefore coexist with a different industrial choice among the leading candidates.

## Figure 3 | Descriptor and economic uncertainty act on different decision endpoints

**a,** Decision-level outcomes across the frozen 1,000-draw NH3 descriptor Monte Carlo. Fe is feasible in **79.9%** of draws, is the economic Top-1 candidate in **68.1% (681/1000)** and is Top-3 actionable in **94.0%**. Atomic-to-economic Top-1 survival is **28.2%**, a distinct statistic measuring preservation of the upstream winner. **b,** Distribution of the reoptimized Ru-minus-Fe cost gap in the preregistered 5,000-draw joint cost-parameter Monte Carlo. Fe remains lower-cost in **5,000/5,000** draws; the minimum sampled gap is **2.382 US dollars per tonne of NH3**. **c,** Ru activity multiplier required for parity in the same draws: **p05 = 70.78-fold, median = 174.27-fold, p95 = 462.00-fold**; the canonical value is **201.22-fold**. **d,** Candidate-by-rank probabilities for the four MEOH-D01-v3 states. The canonical economic order is retained in **5,000/5,000** draws; a separately labelled active-Re replacement extension gives the same order.

## Figure 4 | Candidate-specific process optimization produces distinct ammonia operating regimes

Optimized catalyst-dependent cost envelopes are shown as a function of pressure after reoptimization of reactor temperature and separator temperature. Fe occupies an interior optimum near **425 °C / 180 bar / 30 °C separator**, Ru near **450 °C / 425 bar / 25 °C**, and Os retains a broad shallow high-pressure minimum. Process freedom changes the preferred operating regime of each catalyst but does not restore the intrinsic activity order.

## Figure 5 | Backward design converts the Fe-Ru economic gap into an activity target

Ru intrinsic activity is multiplied while the full process is reoptimized at each multiplier. Economic parity with Fe occurs at **201.22-fold** the baseline Ru activity under the canonical economic parameters. The calculation defines the catalyst improvement demanded by the industrial objective rather than by an atomistic performance metric alone.

## Figure 6 | The activity target lies outside the current scaling-consistent design path

The backward-designed Ru parity requirement is compared with activity changes accessible along the frozen descriptor/scaling manifold. Scaling-consistent headroom is **1.090-fold at 673 K** and reaches a maximum of **2.525-fold** across the admissible process-state library. The lowest strict-scaling Ru cost is **21.398 US dollars per tonne of NH3 at E_N = -1.215 eV**, above Fe. Incremental movement along the current activity manifold therefore cannot reach the economic target.

## Figure 7 | Methanol catalyst-state rankings reshape after explicit recycle and separation

Using space-time yield per gram of Re as the upstream metric, the order is **1 wt% Re / 250 °C > 1 wt% Re / 200 °C > 5 wt% Re / 200 °C > 5 wt% Re / 250 °C**. After propagation through the explicit-loop process at the canonical 2% purge, the economic order becomes **5 wt% Re / 200 °C > 1 wt% Re / 200 °C > 1 wt% Re / 250 °C > 5 wt% Re / 250 °C**. The four-state comparison gives **Spearman rho = 0.20**, **Kendall tau = 0.00** and **3/6 pairwise inversions**.

## Figure 8 | Methane suppression dominates the tested local economic leverage in methanol synthesis

**a,** Net production cost across the complete **0.5-40%** purge sweep for the four MEOH-D01-v3 states, with the canonical 2% purge identified. The Re-normalized upstream winner remains economically suboptimal throughout the sweep; rho never exceeds **0.40** and at least **2/6** pairs remain inverted. **b,** Local economic leverage at 5 wt% Re / 250 °C for space-time yield (**0.00289**), single-pass conversion (**0.05883**) and methane suppression (**0.37579**). The result identifies a selectivity-recycle pathway through feed loss, gas accumulation, purge, recycle and compression.

## Figure 9 | Catalyst-to-process coupling determines whether an upstream ranking reshapes or survives

**a,** Reaction-specific coupling topology. In ammonia, activity and catalyst economics act through catalyst inventory, reactor demand and operating severity; in CO2-to-methanol, selectivity acts through reactant loss, purge, recycle and compression. **b,** Literature-calibrated Au/TiO2 CO-oxidation control across 2-6 nm particle sizes under a common process mapping. Intrinsic activity and downstream catalyst burden preserve the order **2 > 3 > 4 > 5 > 6 nm**, with **Spearman rho = 1.000**, **Kendall tau = 1.000**, zero pairwise inversions and full preservation in **10,000/10,000** predefined literature-envelope draws. The 6 nm state requires **8.064 times** the catalyst burden of the 2 nm state.

## Figure 10 | Adaptive compute allocation has a capability-bounded operating envelope

All panels use the frozen DISCOVER V1 environment and DISCOVER-BOUNDARY-C1 budget series. A complete decision requires the correct economic winner, decision pair and reachability verdict. The deterministic fixed-VOI policy completes at **206 CU**, and the protocol-complete S1-S3 oracle lower bound is **22 CU**. **a,** Complete-decision recovery versus compute budget across model tiers. The strong tier reaches the lowest tested stable complete-decision budget at **75 CU**, corresponding to **3.41 times** the protocol oracle; the median ledger-true decision-stable spend in this cell is **52.5 CU**, or **2.39 times** oracle. **b,** Canonical narrow-window allocation. The strong tier uses scoped process windows in the constrained regime and drops to **0/20** use at 225 CU and under the non-binding 5,000-CU allowance. **c,** Decision-stable and final-used compute. Under the non-binding allowance, median decision stability moves to **566 CU**, followed by a median **148 CU** of additional spend before self-stop, for **714 CU** median final spend. Budget pressure therefore activates search compression; the adaptive advantage is localized to a capability- and budget-dependent regime below the fixed-policy threshold.
