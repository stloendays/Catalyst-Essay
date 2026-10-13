# Methanol: revealed-preference validation against industry (2026-10-13, pre-registered)

Does the latest methanol plant model, fed only laboratory data, reproduce the industrial preference for Cu/ZnO/Al2O3?
Hypotheses, subsets, statistics and pass rules are in [`PREREGISTRATION.md`](PREREGISTRATION.md), committed and pushed
(133f9ea) before any outcome was computed. Verdict = printed cohort (40 groups, 310 entries, 28 papers) under S6
(CH4 + CO + N2 <= 6.86 %). Paper-cluster bootstrap, 10,000 resamples, seed 20261013.

## Numbers first

**Pre-registered verdict (printed, S6): H1 FAIL, H2 FAIL, H3 FAIL.** No primary test passes in any cohort or scenario.

| Test | printed S6 (primary) | printed S5 | printed S6-TI (CH4+N2) | extended S6 | extended S5 | extended S6-TI |
|---|---|---|---|---|---|---|
| H1: groups with cost leader CZA / STY leader CZA (of 3, 2 papers) | 0 / 0 | 1 / 0 | 1 / 0 | 0 / 0 | 1 / 0 | 1 / 0 |
| H1: D [95 % CI] -> verdict | 0.000 [0.000, 0.000] FAIL | 0.333 [0.000, 0.500] FAIL | 0.333 [0.000, 0.500] FAIL | 0.000 [0.000, 0.000] FAIL | 0.333 [0.000, 0.500] FAIL | 0.333 [0.000, 0.500] FAIL |
| H2: G_cost [95 % CI] | 0.013 [-0.016, 0.033] | 0.015 [-0.013, 0.019] | 0.005 [-0.017, 0.011] | 0.014 [-0.021, 0.025] | 0.009 [-0.016, 0.021] | 0.008 [-0.018, 0.014] |
| H2: G_STY (Cu-based rank by best STY) | -1.560 (3rd of 4) | -1.560 (3rd) | -1.560 (3rd) | -1.560 (5th of 6) | -1.560 (5th) | -1.560 (5th) |
| H2: verdict | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| H3: AUC_cost / AUC_STY (scaled vs lab-only) | 0.873 / 0.587 | 0.903 / 0.587 | 0.887 / 0.587 | 0.754 / 0.652 | 0.712 / 0.654 | 0.719 / 0.654 |
| H3: dAUC [95 % CI] -> verdict | 0.287 [-0.384, 0.565] FAIL | 0.317 [-0.094, 0.555] FAIL | 0.300 [-0.075, 0.533] FAIL | 0.102 [-0.186, 0.527] FAIL | 0.058 [-0.266, 0.516] FAIL | 0.066 [-0.237, 0.500] FAIL |
| Field result (anchor): different leader / groups | 28 / 40 | 15 / 40 | 18 / 40 | 54 / 82 | 35 / 83 | 42 / 83 |

Secondary tests (pre-registered, do not change the verdict):

| Test | printed S6 | printed S5 | printed S6-TI | extended S6 | extended S5 | extended S6-TI |
|---|---|---|---|---|---|---|
| H1-broad (any Cu-based reference) D [CI] | 0.000 [0.000, 0.000] FAIL | 0.333 [0.000, 0.500] FAIL | 0.333 [0.000, 0.500] FAIL | 0.000 [0.000, 0.000] FAIL | 0.250 [0.000, 0.500] FAIL | 0.250 [0.000, 0.500] FAIL |
| H2-CZA: G_cost [CI] / G_STY | 0.013 [-1.049, 0.028] / -1.560 FAIL | 0.015 [-0.036, 0.019] / -1.560 FAIL | 0.005 [-0.022, 0.011] / -1.560 FAIL | 0.014 [-1.054, 0.025] / -1.560 FAIL | 0.009 [-0.044, 0.021] / -1.560 FAIL | 0.008 [-0.028, 0.013] / -1.560 FAIL |
| H2-regret: first family by median cost regret / by median STY shortfall | Cu-based / Pd **pass** | Pd / Pd FAIL | Pd / Pd FAIL | Re / Re FAIL | Pd / Re FAIL | Pd / Re FAIL |
| H3-catalyst (one point per paper x catalyst) dAUC [CI] | 0.320 [-0.345, 0.620] FAIL | 0.357 [-0.082, 0.616] FAIL | 0.326 [-0.065, 0.588] FAIL | 0.038 [-0.371, 0.552] FAIL | 0.100 [-0.236, 0.533] FAIL | 0.100 [-0.203, 0.496] FAIL |
| H3-alt (In2O3/ZrO2 also counted as scaled) dAUC [CI] | 0.079 [-0.182, 0.401] FAIL | 0.009 [-0.286, 0.390] FAIL | 0.010 [-0.273, 0.375] FAIL | 0.061 [-0.154, 0.351] FAIL | -0.002 [-0.243, 0.320] FAIL | 0.011 [-0.218, 0.317] FAIL |

## What the numbers say

1. **H1 (within-group leader).** Only 3 printed groups from 2 papers hold a Cu/ZnO/Al2O3-type reference beside another
   family (Martin et al. 2016, In2O3 vs Cu-ZnO-Al2O3; `10.1126/sciadv.abi6012` at 12 and 30 NL/g/h, InNi3C0.5 vs
   CuZnAl); the extended cohort adds none. The STY leader is never the CZA reference. Under S6 the plant-cost leader
   is never CZA either (D = 0): In2O3 leads both boards in Martin 2016 and InNi3C0.5 leads both in the two
   `abi6012` groups. Under S5 and S6-TI the CZA reference becomes the cost leader in the 30 NL/g/h `abi6012` group by
   a regret of 0.02 % (D = 1/3); the 2-paper bootstrap lower bound stays at 0.
2. **H2 (family ranking).** The cheapest entry of the Cu-based family is the cheapest of all families in every
   cohort and scenario (printed S6: CZA400 905 USD/t vs Pd 917, Re 921, In2O3 969), while by best STY Cu-based ranks
   3rd of 4 (printed) and 5th of 6 (extended); the best Cu-based STY is 0.21 of the best non-Cu STY (G_STY = -1.56,
   CI excludes 0). Cu-based is first by cost in 88 % of resamples (printed S6) and first by STY in 0.07 %. But the
   margin is 0.5-1.5 % of the plant cost, and the 95 % interval of G_cost includes 0 everywhere, so H2 fails its
   pre-registered rule. The best entries of all families sit within 7 % (printed S6) of each other in plant cost.
3. **H3 (scaled vs lab-only).** Plant cost ranks scaled catalysts (CZA type; ZnO-ZrO2 in the extended cohort) above
   lab-only ones more often than STY does in every cell (printed S6 AUC 0.87 vs 0.59; dAUC +0.29), but with 5 papers of
   scaled catalysts in the printed cohort (7 in the extended) the paper-cluster interval of dAUC includes 0 everywhere.
   Counting In2O3/ZrO2 as scaled (H3-alt) removes most of the difference (dAUC -0.00 to +0.08).
4. **Secondary pass.** Only the within-group H2-regret test passes, and only in the primary cell (printed S6: Cu-based
   lowest median cost regret 16.9 % vs Re 18.1 %, In2O3 21.3 %, Pd 46.3 %; lowest STY shortfall Pd); it is first in 48 %
   of resamples. It fails under S5, S6-TI and in the extended cohort.

## Subsets (pre-registered, composition only)

`families.py` (rules), `make_subsets.py` -> `subsets_printed.csv`, `subsets_extended.csv`, `subsets_summary.json`.

| | CuZnAl | other Cu | In2O3 | Pd | ZnZrOx | Zn-CdZrOx | Re | blank controls | scaled / lab-only entries (papers) |
|---|---|---|---|---|---|---|---|---|---|
| printed | 23 (5) | 82 (3) | 114 (14) | 62 (7) | 0 | 0 | 13 (1) | 16 | 23 (5) / 271 (25) |
| extended | 54 (5) | 176 (8) | 415 (21) | 148 (10) | 48 (2) | 35 (1) | 13 (1) | 20 | 102 (7) / 787 (40) |

Scale-up evidence (`families.SCALE_EVIDENCE`): Cu/ZnO/Al2O3 is the commercial methanol catalyst and CRI's George Olah
CO2-to-methanol plant (Iceland, 2011-12, JM licence and Cu/ZnO-based catalyst) uses it; ZnO-ZrO2 solid solution runs at
1,000 t/a in the DICP liquid-sunshine demonstration (Lanzhou, 2020; CAS news 2020-11-04); the Mitsui ~100 t/a pilot
(2009-10) used a Cu-based RITE catalyst (no such entry in the cohorts). For In2O3/ZrO2 only an ETH-Total patent and an
announced demonstration were found, hence lab-only in the primary class and scaled only in H3-alt.

## Reproduction

```bash
python analysis/validation_meoh_revealed_2026_10_13/make_subsets.py       # composition-only subsets (pre-registered)
python analysis/validation_meoh_revealed_2026_10_13/compute_true_inert.py # S6-TI costs, <= 8 workers (~4 min)
python -m pytest analysis/validation_meoh_revealed_2026_10_13/test_anchors.py
python analysis/validation_meoh_revealed_2026_10_13/run_validation.py     # runs the anchors first (~1 min)
```

`test_anchors.py` reproduces the frozen field counts before any new statistic: printed S5 15/40, S6 28/40, S6-TI
18/40 (and the committed inlet-definition costs to 1e-6); extended S5 35/83, S6 54/82; cohort sizes 40/310/28 and
83/909/44; subsets unchanged. `compute_true_inert.py` re-derives every frozen cost column with the unchanged
inlet-definition code before writing S6-TI (max relative difference 4.9e-12 printed, 2.5e-11 extended;
`true_inert_reproduction.json`). Nothing outside this folder is modified.

Outputs: `results.json` (every statistic, interval, bootstrap share and pass flag), `results_tables.md`,
`h1_groups.csv` (leaders of each H1 group), `h2_families.csv` (family best/median cost and STY, ranks),
`h3_auc.csv`.

## Deviations and implementation notes

- **H1 bootstrap population.** The pre-registration says the H1 interval is a paper-cluster bootstrap and that "with
  2 papers, this requires D > 0 in each paper", i.e. the 2 (extended H1-broad: 3) subset papers are resampled. The
  first run resampled all 28 cohort papers instead, which leaves 12 % of draws without either subset paper and so a
  lower bound of -inf by construction. Corrected to the subset papers. Every H1 point estimate and every H1 verdict
  (FAIL) is the same in both runs.
- **Percentile method.** To keep -inf draws (undefined statistic = failure) well defined, the 95 % interval uses the
  lower / higher order statistic (`np.percentile(method="lower"/"higher")`) instead of linear interpolation; changed
  after the first run. Bounds moved in the third decimal (printed S6 dAUC lower bound -0.382 -> -0.384); no verdict
  changed.
- The AUC intervals (not used by any pass rule) count a resample without a scaled or lab-only entry as AUC 0.
- No subset, statistic, scenario or pass rule was changed after outcomes were seen.
