# Methanol catalyst-level count (63 groups): re-measurement and selectivity of the plant leader (2026-10-24)

The main text quoted two robustness figures computed on the 81 point-level comparisons (42 of 50 disagreements persist
in ≥ 90 % of 2,000 re-measurements; the plant leader is more selective in 40 of 50), while its headline is the
catalyst-level count, 21/63 with more catalyst loaded (26/63 at laboratory conversion). Both are redone here on the
catalyst-level unit of `meoh_catalyst_level_2026_10_19/RULES.md`.

    set MEOH_FIELD_SET=combined
    python catalyst_level_selectivity.py        # selectivity.json, selectivity_groups.csv (seconds)
    python catalyst_level_noise.py              # laboratory conversion: summary_noise_lab.json (cached runs, ~5 min)
    python raised_noise.py --workers 10         # more catalyst: summary_noise_raised.json (~55 min, resumable)

## Selectivity (`selectivity.json`)

| | changes | plant leader more selective | less CO | higher conversion | more selective among > 5 % |
|---|---:|---:|---:|---:|---:|
| more catalyst loaded (21/63) | 21 | **17** | 16 | 1 | **10/10** |
| laboratory conversion (26/63) | 26 | 19 | 18 | 6 | 16/19 |

The laboratory leader is represented by its highest-STY point, the plant leader by its lowest-cost point (median
methanol selectivity 0.69 against 0.79 with more catalyst).

## Re-measurement (2,000 draws, frozen error model meas_k1, seed stream [20261006, 0])

| | observed | mean per draw (95 % range) | kept in ≥ 90 % | kept in ≥ 50 % | > 5 % kept in ≥ 90 % |
|---|---:|---:|---:|---:|---:|
| more catalyst loaded | 21 | **21.2 (17–26)** | 11 | 19 | **8 of 10** |
| laboratory conversion | 26 | 25.1 (21–29) | 17 | 26 | — |

- Laboratory conversion: the committed draws and costs of `meoh_field_pooled_2026_10_15/robustness/stats_s6`
  (response surface plus exact cache, no new model run). Gate: their point-level count reproduces 42 of 50.
- More catalyst loaded: the same error model drawn over the 566 entries of the 63 groups, each perturbed entry costed
  as `verify_2026_10_12_s6_conversion/run_s6_conversion.evaluate` (f = 0.95), vectorized over the conversion states
  (bit-identical to the frozen evaluate on the checked points). Additive per-dimension response surface (ln X: ±0.03,
  ±0.1, ±0.25; ln STY: ±0.25; MeOH→CH₄: ±0.008, ±0.04, and −S_CH₄ when small; 6,509 runs), draws outside the grid or
  next to an infeasible grid point run exactly (1,325). Gates: unperturbed costs reproduce cost_f0.95 (max relative
  deviation 5 × 10⁻¹⁰) and the count 21/63. Two complete exact replicates: surface 21 and 24 against exact 20 and 27
  changes (1 and 3 groups with a different verdict; median cost error 0.03 %).
- One group that does not change in the point estimate changes in at least half of the draws (more catalyst).

Main text and SI Note 3 now quote these numbers; the 81-comparison figures stay in SI Note 3.
