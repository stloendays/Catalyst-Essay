# Figure 3 — caption (2026-09-20 cost-uncertainty update)

Renderer: `figures/nh3/render_F03_uncertainty_cost_mc.R`.

Primary inputs:

- frozen NH3-FINAL-1.1 descriptor Monte Carlo: `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/closure/mc_draws.csv`;
- supervisor extension panel summary: `analysis/supervisor_2026_09_20/f3_panel_summary.csv`;
- binned joint cost-MC distributions: `analysis/supervisor_2026_09_20/nh3_cost_mc_histogram.csv`;
- MeOH rank matrix: `analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv`.

## Caption

**Figure 3 | Descriptor and economic uncertainty act on different decision endpoints.** **a**, Decision-level outcomes across the frozen 1,000-draw NH3 descriptor Monte Carlo. Fe remains feasible in **79.9%** of draws, is the economic Top-1 candidate in **68.1% (681/1000)**, and is Top-3 actionable in **94.0%**. The previously reported **28.2% Top-1 survival** is a different statistic: it is the probability that the atomic Top-1 and economic Top-1 identities coincide, and must not be interpreted as the probability that Fe ranks first economically. **b**, Distribution of the reoptimized Ru-minus-Fe cost gap in the preregistered 5,000-draw joint cost-parameter Monte Carlo, in which Fe and Ru metal prices, the common CAPEX coefficient, electricity price and catalyst lifetime are varied under the frozen 2026-09-20 protocol. Fe remains lower-cost in **5,000/5,000** draws; the minimum sampled Ru-minus-Fe gap is **2.382 USD t−1 NH3** and the median gap is **7.110 USD t−1 NH3**. **c**, Distribution of the Ru activity multiplier required for parity after reoptimization in the same draws. The **p05, median and p95 alpha*** values are **70.78×, 174.27× and 462.00×**, respectively; the canonical NH3-FINAL-1.1 value (**201.22×**) is shown for reference. **d**, Candidate-by-rank probabilities for the four MEOH-D01-v3 catalyst-temperature states under the tested cost envelope. The canonical economic order is retained in **5,000/5,000** draws. Because the canonical D01 boundary excludes Re purchase and replacement, metal-price and lifetime perturbations are structurally inactive in that canonical calculation; a separately labelled active-Re replacement extension also retains the same order in **5,000/5,000** draws.

The cost-side probabilities are conditional on the preregistered bounded prior and are not market-frequency forecasts.
