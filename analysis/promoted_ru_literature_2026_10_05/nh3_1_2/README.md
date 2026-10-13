# Fig. 3a literature strip against the NH3-FINAL-1.2 parity band

The measured activity gains do not depend on the model: `fig3_literature_points.csv` here is a byte-identical copy of
the parent file (and `promoted_confined_ru_enhancement.csv` is unchanged). What moves with the model is the band the
points are read against. `parity_band.py` evaluates it on the same definitions for either model:

- **baseline α\***: direct Ru activity multiplier at which Ru, reoptimized over the full process library under the
  90 m³ bed cap, reaches the Fe cost (harness `backward_and_reachability`; equals `results.json` of the run);
- **economic band**: the preregistered 5,000-draw cost Monte Carlo (`docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md`,
  seed 20260920, draw construction of `analysis/nonfigure_upgrades_2026_09_29/reproduce_nh3_cost_mc.py`): Fe and Ru
  reoptimized per draw with sampled metal prices, CAPEX multiplier, electricity price and catalyst life; α\* recomputed
  against that draw's Fe cost with Ru reoptimized at every α.

```
cd analysis/promoted_ru_literature_2026_10_05
NH3_MODEL=1.1 python parity_band.py    # -> ./parity_band.json, literature_vs_parity.csv, alpha_star_draws.csv
NH3_MODEL=1.2 NH3_HARNESS_1_2=<1.2 source_harness> python parity_band.py    # -> nh3_1_2/ (same names)
```

Only the descriptor grid points bracketing E_N(Fe) and E_N(Ru) are evaluated; no response surface is built or read.
Runtime about 4.5 min per model, single process.

The 1.1 run is gated: it must reproduce `analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json` before writing.
It does: α\* p05/p10/p25/p50/p75/p90/p95/mean/min/max within 2.0 × 10⁻¹² relative, Fe and Ru cost quantiles within
3 × 10⁻¹⁴ USD t⁻¹, baseline α\* = 201.223443 = `results.json`.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

| quantity | 1.1 | **1.2** |
|---|---:|---:|
| process states | 14,136 | **14,510** |
| Fe / Ru baseline cost (USD t⁻¹) | 15.2917 / 22.0306 | **11.5158 / 16.6327** |
| baseline α\* (Ru activity multiple for parity with Fe) | 201.22× | **114.67×** |
| Ru optimum at α\* | 425 °C, 190 bar, 30 °C | **425 °C, 110 bar, 30 °C** |
| cost-MC α\* p05 – p95 (parity band) | 70.78 – 462.00× | **43.52 – 262.28×** |
| cost-MC α\* median | 174.27× | **104.97×** |
| cost-MC α\* p10 / p90 | 83.76 / 371.89× | **50.84 / 218.96×** |
| cost-MC α\* min / max | 41.01 / 878.97× | **28.10 / 483.86×** |
| cost-MC Fe cost p05 / p50 / p95 (USD t⁻¹) | 9.60 / 17.55 / 24.82 | **7.31 / 13.18 / 18.52** |
| cost-MC Ru cost at α = 1, p05 / p50 / p95 (USD t⁻¹) | 13.24 / 24.92 / 35.48 | **10.41 / 18.81 / 26.78** |
| P(Ru ≤ Fe at α = 1) over 5,000 draws | 0 | **0** |

## Where the measured gains fall

| point | measured gain | 1.1 position (band 70.78–462×, α\* 201.22×) | **1.2 position (band 43.52–262.28×, α\* 114.67×)** | share of draws with α\* ≤ gain, 1.1 → 1.2 |
|---|---:|---|---|---:|
| P01 Ba–Ru/C | 75× | in band, below α\* | **in band, below α\*** | 0.063 → 0.293 |
| P02 Cs–Ru/C | 65× | just below band | **in band, below α\*** | 0.030 → 0.205 |
| P03 Ba–Ru/BN, 5 MPa | >100× | in band, below α\* | **in band, below α\*** (lower bound) | 0.178 → 0.470 |
| P04 Cs–Ru/MgO | >134× (350 °C) | in band, below α\* | **in band, above α\*** | 0.341 → 0.668 |
| P05 Cs–Ru/YSZ | ~10× | below band | **below band** | 0 → 0 |
| E01 Ru/C12A7:e⁻ | 9.8× | below band | **below band** | 0 → 0 |
| E10 Ru/BaTiO₂.₅H₀.₅, 5 MPa | 8.4× | below band | **below band** | 0 → 0 |
| E09 Ru/Ba–Ca(NH₂)₂ (vs Cs–Ru/MgO) | 33.5× | below band | **below band** | 0 → 0.008 |
| C01 Ru inside CNT | 0.5× | below band | **below band** | 0 → 0 |

Under 1.2 all four alkali and alkaline-earth promoter gains on C, BN and MgO (65–134×) lie inside the parity band, and
the Cs–Ru/MgO gain (>134×) exceeds the baseline requirement of 114.67×. Electride, oxyhydride and Cs–Ru/YSZ (8–10×)
and the amide support (33.5×, against an already promoted reference) remain below the band; confinement in carbon
nanotubes remains 0.5×. Alkali and alkaline-earth promotion is still the only measured route that reaches the band.

Files: `parity_band.json` (baseline, MC quantiles, per-point placement), `literature_vs_parity.csv` (per point:
position vs band, whether the gain reaches the baseline α\*, gain / α\*, share of draws whose α\* the gain reaches),
`alpha_star_draws.csv` (all 5,000 draws: sampled parameters, Fe cost, Ru cost at α = 1, α\*, optimum pressures),
`fig3_literature_points.csv` (unchanged copy).
