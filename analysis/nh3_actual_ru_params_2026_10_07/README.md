# Actual-Ru ammonia analysis with literature-checked loading, bed density and recovery (cloud run)

GitHub Actions run [37633987381](https://github.com/stloendays/Catalyst-Essay/actions/runs/37633987381)
(ubuntu-latest, Python 3.12.14, numpy 2.5.3; commit `90bbee9`). Workflow: `.github/workflows/nh3-actual-ru-params.yml`.

## Results

Literature-checked inputs (primary-literature check of 2026-10-07):

| Set | Recovery r | Bed density ρ (kg m⁻³) | Ru loading w |
|---|---|---|---|
| baseline | 0.90–0.94 | 500–1,000 | 3.2 wt% (MC: measured catalysts) |
| R1 recovery | **0.90–0.97** | 500–1,000 | 3.2 wt% |
| R2 bed density | 0.90–0.94 | **430–550** | 3.2 wt% |
| R3 Ru loading | 0.90–0.94 | 500–1,000 | **8 wt%** (5 and 10 wt% also); MC variant A_comm: **uniform 5–10 wt%** |
| R_all | 0.90–0.97 | 430–550 | 8 wt% (5–10 wt%); A_comm |

u = 11 in the Fig. 3d readings, log-uniform 11–50 in the Monte Carlo, everything else unchanged. Ranges are over the
corners (r, ρ) of each set; Fe references: 15.29 USD/t (main loop optimum), 19.07 USD/t (Fe in the KAAP loop).

| Quantity | baseline | R1 | R2 | R3 (8 wt%) | R_all (8 wt%) |
|---|---|---|---|---|---|
| Fig. 3d main loop, Ru/C own bed (USD/t) | 15.89–16.44 | 15.76–16.44 | 16.24–16.56 | 15.60–15.95 | 15.63–16.01 |
| gap to Fe, main loop | +0.60 to +1.15 | +0.47 to +1.15 | +0.95 to +1.26 | +0.31 to +0.66 | +0.33 to +0.72 |
| α* for parity, main loop | 3.04–5.71 | 2.49–5.71 | 4.62–6.34 | 1.88–3.39 | 1.96–3.64 |
| main loop, 5–10 wt% envelope | – | – | – | 15.55–16.16 | 15.55–16.24 |
| KAAP loop, Ru/C own bed (USD/t) | 18.92–19.32 | 18.67–19.32 | 19.10–19.39 | 18.66–19.05 | 18.49–19.08 |
| gap to Fe in KAAP | −0.15 to +0.25 | −0.40 to +0.25 | +0.03 to +0.33 | −0.41 to −0.02 | −0.58 to +0.01 |
| α* for parity, KAAP | 0.76–1.39 | 0.56–1.39 | 1.05–1.50 | 0.55–0.97 | 0.46–1.02 |
| KAAP, 5–10 wt% envelope | – | – | – | 18.61–19.16 | 18.40–19.20 |
| P(Fe cheaper), A | 0.480 [0.466, 0.494] | **0.356** [0.342, 0.369] | 0.480 | 0.480 | 0.356 [0.342, 0.369] |
| P(Fe cheaper), A_bed (measured w) | 0.800 [0.788, 0.811] | 0.758 [0.745, 0.769] | 0.895 [0.886, 0.903] | 0.800 | 0.867 [0.857, 0.876] |
| P(Fe cheaper), A_comm (w 5–10 wt%) | 0.614 [0.600, 0.628] | 0.537 [0.523, 0.551] | 0.749 [0.737, 0.761] | **0.614** | **0.690** [0.677, 0.703] |
| P(Fe cheaper), B (measured catalysts) | 0.943 [0.936, 0.949] | 0.938 [0.931, 0.945] | 0.948 [0.942, 0.954] | 0.943 | 0.947 [0.940, 0.953] |
| P(Fe cheaper), B0 (no recovery) | 0.989 | 0.989 | 0.990 | 0.989 | 0.990 |

95% Clopper–Pearson intervals, 5,000 draws. All sets use the same draws (common random numbers), so differences
between columns are paired. In the Monte Carlo, R3 enters only through A_comm (A_bed and B keep the measured
catalysts' Ru contents); the literature-set reading of the supported bed is therefore A_comm under R_all (0.690),
against A_bed under the baseline (0.800).

Benchmark-bed reading (independent of w and ρ; parity price of the Fig. 2d sweep 163.76 USD/kg):

| r | p_eff (USD/kg) | main loop (gap to Fe) | KAAP loop (gap to Fe in KAAP) |
|---|---|---|---|
| 0.90 | 489.6 | 15.671 (+0.379) | 18.910 (−0.158) |
| 0.94 | 293.7 | 15.485 (+0.193) | 18.529 (−0.540) |
| 0.97 | **146.9** | **15.237 (−0.054)** | 18.157 (−0.912) |

Direction of each change for Ru/C relative to Fe:

- **R1 (r up to 0.97)**: toward Fe. The benchmark-bed reading crosses parity at 97% (146.9 < 163.76 USD/kg); own-bed
  lower ends drop by 0.13 (main) and 0.25 USD/t (KAAP); P(Fe cheaper) falls in A, A_bed, A_comm.
- **R2 (ρ 430–550)**: away from Fe. A lighter bed is a larger reactor: main loop +0.12 to +0.35 USD/t, KAAP gap now
  positive at every corner; P(Fe cheaper) for A_bed rises to 0.895.
- **R3 (8 wt% Ru)**: toward Fe, the largest single change. Main loop gap halves (+0.31 to +0.66); in the KAAP loop
  Ru/C is below Fe at every corner (−0.41 to −0.02). Drawing 5–10 wt% (A_comm) gives P(Fe cheaper) 0.614 vs 0.800
  for the measured contents.
- **R_all**: toward Fe on net (R3 and R1 outweigh R2). Main loop 15.63–16.01 (Fe 15.29, still above at every corner,
  α* 1.96–3.64); KAAP loop 18.49–19.08 against Fe 19.07 (below Fe at 3 of 4
  corners at 8 wt%, 9 of 12 over 5–10 wt%); supported-bed MC 0.690 (A_comm) vs baseline 0.800 (A_bed).

## Validation (same run, before the variants)

- Self-check gate `agent/selfcheck_gate.py`: NH3 15/15 pure-metal canonical costs within 1e-9 USD/t of
  `results.json` (Fe 15.291704676621144, Ru 22.03059478781101); MeOH and Au/TiO₂ also pass
  (`ci_logs/selfcheck_report.json`).
- Committed baseline outputs reproduced by rerunning the unchanged scripts on the cloud harness root
  (`ci_logs/validate_baseline.log`; |Δ| ≤ 1e-9 + 1e-8|x|, P values exact):
  `nh3_mc_ru_actual_2026_10_06/summary.json` (A 0.4798, A_bed 0.7998, B 0.943, B0 0.9892) and `draws.csv`
  (95,000 cells); `fig2_ru_bed_sensitivity.csv`, `fig2_ru_actual_cost_points.csv`, `fig2_ru_alpha_sweep.csv`.
- `run_params.py` itself asserts that its baseline set reproduces the committed MC summary exactly and the 8 committed
  Fig. 3d own-bed rows to 1e-9 USD/t.

## How it runs

- `provenance/nh3_final_1_1/source_harness/inputs/ammonia_activity_volcano_s1_v1.xlsx`: the harness's input workbook,
  SHA-256 `fc259c53…dce9ba`, checked by the workflow before use.
- `build_harness_root.py`: builds a harness root from `provenance/discover_v1/source_harness` (harness_core.py and the
  NH3-FINAL-1.1 run manifest/results) and computes, with the harness's own `Condition.logtof`, only the response
  columns the analyses interpolate: 84 of 1,201 grid columns (15 pure metals and the 54 measured Ru catalysts' effective
  descriptors) × 14,136 states, 17 s on 4 workers. All other columns are NaN; the file stays on the runner.
- `validate_baseline.py`: compares rerun outputs with their committed versions.
- `run_params.py`: the variants → `summary.json`, `fig3d_readings.csv` (every corner), `mc_variants.csv`,
  `results_table.md`. Draws: seeds 20260920 and 20261006 as in `analysis/nh3_mc_ru_actual_2026_10_06`; A_comm's Ru
  content from seed 20261007.
