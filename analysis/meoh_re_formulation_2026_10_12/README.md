# Re/TiO2 activity normalization and metal-replacement cost (UNFROZEN)

**Status:** source-grounded follow-up to the methanol engineering-envelope PR #56. This exploratory branch must **not** overwrite source extraction tables, frozen S5, paper claims, or the previously validated joint process scans.

## Scientific question and reason

The Re/TiO2 paper [ACS Catalysis 2025, doi:10.1021/acscatal.5c05984] reports activity **per gram of metallic Re**. The plant catalyst reactor-sizing objective uses productivity **per gram of total catalyst**. Those are *different upstream metrics*, and can rank the same pair oppositely.

At **200 C, 100 bar, H2/CO2=4, same 500 C pre-reduction treatment, mass GHSV=10 NL/gcat/h**:

| Source entry | Formulation | STY, g MeOH/gRe/h | STY, g MeOH/gcat/h | PR #55 joint, 6.86% inlet: EUR/t |
|---|---|---:|---:|---:|
| Table 4 row 3 | 1 wt% Re/TiO2 | 55 | 0.55 | 892.739761204 |
| Table 4 row 11 | 5 wt% Re/TiO2 | 18 | 0.90 | 964.951231337 |

The matched pair's laboratory rank is **5wt > 1wt per g total catalyst**, but **1wt > 5wt per g Re**. Thus the former produces an economic ranking reversal at these conditions; the latter does **not**. Full nine-entry 100-bar/10-NL/gcat/h group includes different temperatures and activation treatments: under **per-g-Re** its STY champion is *1wt% at 250 C, Table 4 row 4*, while the model cost champion is *1wt% at 200 C, Table 4 row 3*: a **within-formulation temperature decision**, not a cross-formulation reversal.

This is a **same-metal, same-support, different metal loading** comparison. It cannot be labeled cross-element ranking inversion. Neither basis is scientifically "wrong": per-metal STY probes efficient precious-metal utilization while per-total-catalyst STY reflects catalyst reactor inventory. Do not silently switch between them.

## What code does

\`run_re_normalization_price.py\` uses the original source-normalized printed nine-point Re/TiO2 group and the existing PR #56 engineering model:

1. Check every source Table 4 per-g-Re STY against normalized per-g-total-catalyst STY and metal wt%, fail if either drifts.
2. At every candidate, recompute the existing thermodynamic/process economics on the same coupled **catalyst loading multiplier m x purge p** grid (m max 10 and 25), with the same CO recycle treatment and 3 published reference inlet-composition envelopes.
3. For five **illustrative**, **NOT live market** metallic Re purchase unit price hypotheses **0, 500, 2,000, 10,000, 50,000 EUR/kg_Re**, lifetimes **1 or 5 years**, and Re recovered fraction **0 or 90%**, add only the *original model's optional annual metal-replacement cost*:
   
   \`Incremental modelled EUR/t = catalyst_t * 1000 * (Re wt fraction) * metal_EUR/kg * (1-recovery) / (life_y * annual_meoh_t * 0.90)\`
   
   This is **not** a fully priced catalyst TEA. Missing costs are clearly labeled: *initial metal inventory financing/capitalization, TiO2 and preparation, metal recovery processing and waste, measured catalyst deactivation, and source of real-world Re price*.
4. Jointly **reselect minimum-cost feasible (m,p)** for each of these financial scenarios and for 5 equipment scale constraints: uncapped; all inventory/flow/compressor metrics <=1x, <=2x, <=4x anchor; and inventory only <=2x anchor. It is invalid to simply add the price at a previous (m,p) optimum; the optimum must change with the price.
5. Always hold the original laboratory/STY champion fixed for the **full nine candidates** and separately the **two matched 200 C cases**, for both per-catalyst and per-metal STY. Report original champion eligibility, cross-formulation vs temperature mechanism, modelled cost regret >5%, and the count of distinct DOI papers (one).
6. Two required regression gates: unpriced m<=10/m<=25 costs across all inlet/engineering caps must match the **previous full PR #56 candidate results** for the nine entries, and the analytic replacement penalty must match a direct priced \`G.cost\` evaluation exactly.

## Interpretation / warning

**No true Re market-price data, real deactivation lifetime, or actual Re recovery accounting were supplied.** The price points, lifetimes and recovery fractions are explicit stress-test assumptions, not empirical confidence intervals or calibrated cost predictions.

Original G.economics annual metal replacement and its \`/0.90\` gross-up are reused unchanged. An initial metal charge is not independently capitalized. The comparison therefore cannot prove market-specific Re economics or resolve full capex/working capital, reactor hydraulics or plant operation.

The original paper reports some CO and CH4 selectivities as censored values such as "<1%". Their normalized treatment as zero/closure is a separate model uncertainty. **Only one experimental publication** supports the Re formulation family; the nine rows are correlated conditions from that paper.

## Files

- \`run_re_normalization_price.py\`: source unit and price-aware m,p optimization, fixed original STY leader.
- \`tests/test_re_normalization_price.py\`: lab basis, additive cost, source identity and reversal-regression tests.
- \`results/re_candidate_price_optima.csv\`: individual source candidates' joint optima under all parameter combinations.
- \`results/re_lab_normalization_decisions.csv\`: two metric bases x two comparison cohorts x financial/engineering envelopes.
- \`results/re_normalization_price_summary.json\`: hypothesis robustness and model-parameter caveats.
- \`.github/workflows/meoh-re-denominator-price.yml\`: separate CI, source to report without touching PR #56 or frozen results.

## Reproduce

From repository root, with \`requirements.txt\` installed:

\`\`\`bash
python -m unittest discover -s analysis/meoh_re_formulation_2026_10_12/tests -v
python analysis/meoh_re_formulation_2026_10_12/run_re_normalization_price.py \
  --output analysis/meoh_re_formulation_2026_10_12/results
\`\`\`

**Publication gate:** Before manuscript inclusion, verify all Table 4 units and product qualifiers directly in the original article/SI, and obtain a credible catalyst procurement, recovery and operating lifetime model. Prefer stating conditional, denominator-specific formulation decisions instead of universal material ranking inversion.
