# CI-verified findings: Re/TiO2 source STY normalization and metal-replacement sensitivity

**Exploratory, not frozen or manuscript-ready.** CI run: https://github.com/stloendays/Catalyst-Essay/actions/runs/38243268205

## Matched source pair: 200 C, 100 bar, same pre-reduction treatment

| ACS Catalysis 2025 Table 4 | 1 wt% Re/TiO2 (row 3) | 5 wt% Re/TiO2 (row 11) |
|---|---:|---:|
| STY per g metallic Re (g MeOH / gRe / h) | **55** | 18 |
| STY per g total catalyst (g MeOH / gcat / h) | 0.55 | **0.90** |
| PR #55 joint 6.86%-inlet process cost, metal expense OFF (EUR/t) | **892.739761204** | 964.951231337 |

On **total-catalyst** normalization, choosing the laboratory STY winner produces **8.09% process economic regret** (higher cost than the 1 wt% economic optimum). On **Re-mass** normalization, the original laboratory and economic leader are both 1wt Re/TiO2, thus **no** matched-pair reversal.

For the **full nine-entry** 100bar, 10NL/gcat/h group: the lab winner per total catalyst is 5wt row 11; the lab winner per gram Re is 1wt row 4 at 250C; the cost winner is 1wt row 3 at 200C. The per-g-Re mismatch is a **within-formulation temperature choice**, with modelled regret **4.90% (<5%)**. One paper containing multiple treatments cannot count as multiple independent publications.

## Price-aware joint m-p optimization

This workflow reoptimizes both catalyst-loading multiplier m and purge p under the original thermo, inlet and source-anchored equipment constraints for every price assumption. It does not add price to an already selected optimum.

- Hypothetical, **NOT real-market** Re purchase prices: 0, 500, 2,000, 10,000, 50,000 EUR/kg_Re.
- Replacement lifetimes: 1 or 5 years. Recovery fractions: 0% or 90%.
- Loading cap: m=10 or m=25. Inlet non-H2/CO2 envelopes: 4.92%, 6.8625%, 10.249%.
- Equipment envelopes: no cap, combined <=1x, <=2x, <=4x, or only catalyst inventory <=2x the reference plant.

Uses the **unchanged original TEA** annual catalyst replacement formula, with net metal loss per kg total catalyst equal to Re mass fraction * assumed EUR/kg_Re * (1-recovery). Incremental modelled EUR/t = catalyst_t * 1000 * wt_Re * EUR_per_kg_Re * (1-recovery) / (life_y * methanol_production_t_per_y * 0.90). A direct-priced G.cost evaluation confirms the analytic formula. Zero-price TEA optima match **270** corresponding PR #56 candidate-level entries.

At m<=10, inlet <=6.8625%, combined equipment <=2x source anchor, life=1y, recovery=0%:

| Hypothetical Re price (EUR/kg) | Per-g-total-catalyst STY economic regret | Per-g-Re STY economic regret |
|---:|---:|---:|
| 0 | 8.09% | 0% |
| 500 | 8.55% | 0% |
| 2,000 | 9.91% | 0% |
| 10,000 | 14.97% | 0% |
| 50,000 | 29.23% | 0% |

Across each tested equipment-cap and m-max setting, **20/20** price-life-recovery hypotheses preserve material (>5%) same-temperature, cross-formulation reversal under per-g-total-catalyst STY for **all three** published inlet-composition envelopes. **0/20** yield that reversal for the matched pair's per-gram-Re STY. This finding is **denominator-specific** and does not establish universal intrinsic activity inversion.

The output contains 9 experimental entries, **5,400** candidate optima, **2,400** original-lab-leader decision rows, and one source DOI. Source: https://doi.org/10.1021/acscatal.5c05984.

## Model limitations and publication gate

The metal price/lifetime/recovery parameters are illustrative stress tests, not empirical market prices or probability distributions. This only prices the existing optional **annual metal replacement** category. Missing costs include the initial Re metal inventory purchase/financing, TiO2 support/preparation, waste/recovery OPEX, deactivation, and pellet hydraulic pressure drop. Original published values such as CO <1% are censored, not chemical zero. The two formulations vary the Re wt% and do not compare independent active elements; neither mass-STY defines per-site intrinsic TOF without active-site quantification.

Source experiment Table 4 and its original units, actual 2026 market, catalyst lifetime, recovery yield, and full reactor design would need independent validation before publication of market-specific cost claims.

All raw source records, frozen S5, PR #55/#56 results, figures and manuscript remain unchanged.

## Files

Workflow: .github/workflows/meoh-re-denominator-price.yml

Scripts: analysis/meoh_re_formulation_2026_10_12/run_re_normalization_price.py

Tests: analysis/meoh_re_formulation_2026_10_12/tests/test_re_normalization_price.py

Data: results/re_normalization_price_summary.json, results/re_lab_normalization_decisions.csv, results/re_candidate_price_optima.csv

**Defensible narrative:** process-aware catalyst selection must specify the denominator of the upstream activity metric. Per-metal utilization and per-total-catalyst productivity are legitimate but distinct physical goals, and can induce opposite laboratory leaderboards for the same formulations.
