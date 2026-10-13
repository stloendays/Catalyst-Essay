# Figure 2 (manuscript Fig. 3) model tables on NH3-FINAL-1.2

The five CSVs here are the NH3-FINAL-1.2 counterparts of the files one level up, with the same names and columns.
They come from the same two scripts, run on the canonical 1.2 run `nh3_final_1_2_20261013` (14,510 process states,
cached response surface) and checked against its `results.json` before anything is written.

```
set NH3_MODEL=1.2
set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness
cd figures\composite\fig2
D:\Research\CatalystForge\.venv\Scripts\python.exe fig2_model.py           -> nh3_1_2/fig2_pressure_envelopes.csv, fig2_ru_price_sweep.csv
D:\Research\CatalystForge\.venv\Scripts\python.exe fig2_ru_actual_cost.py  -> nh3_1_2/fig2_ru_alpha_sweep.csv, fig2_ru_actual_cost_points.csv, fig2_ru_bed_sensitivity.csv
```

`NH3_HARNESS_1_2` can point at any 1.2 harness root that holds `harness_core.py`, `inputs/`, the canonical run and
`cache/response_fc259c5311744ccc_-2.6_3.4_0.005_14510_gillespie_beattie_11.npz`. Both scripts refuse to run when that
cache is missing, so they never rebuild the response surface. They take about 20 s and 30 s.

## Checks

- Fe, Ru and Os optima (cost to 1e-9 USD/t and T, P, T_sep) equal `results.json` of the selected run
  (`analysis/nh3_model.py: anchors()`); the pressure envelopes' minima equal them as well.
- α* at the frozen Ru price, recomputed with full reoptimization, is 114.66712547049676, equal to the run's
  `Ru_activity_break_even_multiplier`.
- The strict-scaling reach has the definition of `analysis/fe_bridge_backward_2026_09_29`. For each process state the
  script takes the TOF-maximizing E_N on the canonical 0.005 eV grid over [−2.2, 0.2] eV, read from the cached
  response surface. It then bisects for the largest lifecycle factor q = (1 − r)/L at which the lower cost envelope
  still reaches the Fe optimum, and reports p_eff = 53,852.5 × 10 y × q. At the canonical lifecycle this envelope
  reproduces the run's best strict-scaling Ru, 16.454818591158695 USD/t at E_N = −1.18 eV.
  - Under 1.1 the same code gives 237.31905705967 USD/kg at 425 °C, 190 bar and 30 °C, against 237.3190570596687 in the
    committed `scaling_lifecycle_exact_summary.json` (relative difference 1.4e-14).
  - If `analysis/fe_bridge_backward_2026_09_29/nh3_1_2/scaling_lifecycle_exact_summary.json` exists, the script uses
    it after asserting agreement to 1e-9. That file is not on this branch, so the value here is the recomputed one.
- Two quantities have no 1.2 anchor and are re-derived on the 1.1 definition. "Ru at the Fe price" is Ru reoptimized
  at 8 USD/kg. The parity price uses the same bisection on log price between 8 and 53,852.5 USD/kg; the script asserts
  that this interval brackets the Fe optimum.
- The literature inputs do not depend on the model version and are unchanged: u = 11, r = 0.90 and 0.9555,
  w = 5, 8 and 10 wt%, ρ = 430, 490 and 550 kg m⁻³, and the KAAP loop at the 90 bar, −20 °C grid point.
- With `NH3_MODEL=1.1` (the default) the scripts rewrite the five committed CSVs one level up byte for byte. Their git
  blob SHA-1s match HEAD: `0c37c8f` envelopes, `dfcae6d` price sweep, `47543a7` α* sweep, `30db937` actual-cost
  points and `a3bf259` bed sensitivity.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

| Quantity | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| Fe optimum | 15.2917 USD/t; 425 °C, 180 bar, T_sep 30 °C; 17.06 m³ | 11.5158 USD/t; 425 °C, 105 bar, T_sep 30 °C; 30.36 m³ |
| Ru optimum | 22.0306 USD/t; 450 °C, 425 bar, T_sep 25 °C; 0.066 m³ | 16.6327 USD/t; 450 °C, 220 bar, T_sep 30 °C; 0.066 m³ |
| Os optimum | 25.8318 USD/t; 450 °C, 425 bar, T_sep 0 °C; 0.029 m³ | 19.7465 USD/t; 450 °C, 340 bar, T_sep 30 °C; 0.024 m³ |
| Ru − Fe at the canonical prices | +6.739 USD/t | +5.117 USD/t |
| Ru at the Fe price (8 USD/kg), reoptimized | 14.7121 USD/t; 425 °C, 170 bar, T_sep 30 °C; 9.42 m³ | 10.2368 USD/t; 400 °C, 95 bar, T_sep 30 °C; 18.18 m³ |
| Ru at the Fe price − Fe | −0.580 USD/t | −1.279 USD/t |
| Parity price p* (Ru = Fe) | 163.76 USD/kg | 403.54 USD/kg |
| Parity state | 425 °C, 185 bar, T_sep 30 °C; 6.24 m³ | 425 °C, 110 bar, T_sep 30 °C; 3.82 m³ |
| Canonical Ru price / p* | 329-fold (328.8) | 133-fold (133.5) |
| Recovery for parity at 10 y / 20 y (= 1 − p*/53,852.5 × 10 y/L) | 99.70 % / 99.39 % | 99.25 % / 98.50 % |
| Lifetime for parity at 99 % recovery | 32.9 y | 13.3 y |
| Price sweep at 1 USD/kg | 14.678 USD/t; 170 bar; 9.4 m³ | 10.171 USD/t; 95 bar; 18.2 m³ |
| Price sweep at 3 × 10⁵ USD/kg | 25.697 USD/t; 420–430 bar for p > 5 × 10⁴; T_sep 0 °C; 0.014 m³ | 19.667 USD/t; 220–340 bar for p > 5 × 10⁴; T_sep 30 °C; 0.011 m³ |
| α* for parity at 1 USD/kg / 3 × 10⁵ USD/kg | 0.386 / 1118 | 0.133 / 637.3 |
| Pure Ru, benchmark formulation (p_eff 53,852.5 USD/kg) | 22.031 USD/t (+6.739); α* 201.22; 450 °C, 425 bar, 25 °C | 16.633 USD/t (+5.117); α* 114.67; 450 °C, 220 bar, 30 °C |
| Ru/C, no recovery (p_eff 4,895.7 USD/kg) | 17.950 USD/t (+2.658); α* 18.48; 450 °C, 220 bar, 20 °C | 13.578 USD/t (+2.062); α* 10.55; 450 °C, 150 bar, 30 °C |
| Ru/C, 90 % recovery (p_eff 489.6 USD/kg) | 15.671 USD/t (+0.379); α* 2.234; 450 °C, 200 bar, 30 °C | 11.685 USD/t (+0.169); α* 1.185; 425 °C, 110 bar, 30 °C |
| Ru/C, 95.55 % recovery (p_eff 217.86 USD/kg) | 15.407 USD/t (+0.115); α* 1.206; 450 °C, 195 bar, 30 °C | 11.150 USD/t (−0.365); α* 0.599; 425 °C, 110 bar, 30 °C |
| Ru/C with 90–95.55 % recovery, benchmark reading | 15.41–15.67 USD/t, 0.12–0.38 above Fe; α* 1.2–2.2 | 11.15–11.69 USD/t, from 0.37 below to 0.17 above Fe; α* 0.6–1.2 |
| Fe in the KAAP loop (90 bar, −20 °C) | 19.069 USD/t; 425 °C; 21.65 m³ | 16.980 USD/t; 450 °C; 5.82 m³ |
| KAAP loop, Ru/C 90 % / 95.55 % recovery | 18.910 / 18.337 USD/t (−0.158 / −0.732 vs Fe in the loop) | 16.391 / 16.273 USD/t (−0.589 / −0.707 vs Fe in the loop) |
| KAAP loop floor (free, unlimited activity) | 16.700 USD/t at 350 °C | 16.011 USD/t at 350 °C |
| Strict-scaling reach p_eff | 237.32 USD/kg; 425 °C, 190 bar, 30 °C; 4.30 m³ | 444.34 USD/kg; 425 °C, 110 bar, 30 °C; 3.51 m³ |
| u for parity at r = 0 / 0.90 / 0.9555 | 328.8 / 32.9 / 14.6 | 133.5 / 13.3 / 5.9 |
| u to reach strict-scaling reach at r = 0.90 / 0.9555 | 22.7 / 10.1 | 12.1 / 5.4 |
| Own bed, no recovery: 8 wt %, 490 kg m⁻³ (8 wt %, 430–550; 5–10 wt %) | 18.064 (18.049–18.084; 18.023–18.178) USD/t | 13.638 (13.630–13.647; 13.617–13.694) USD/t |
| Own bed, 90 %: same | 15.962 (15.922–16.012; 15.856–16.242) USD/t | 12.015 (11.988–12.051; 11.912–12.199) USD/t |
| Own bed, 95.55 %: same | 15.735 (15.691–15.792; 15.619–16.050) USD/t | 11.518 (11.464–11.587; 11.378–11.937) USD/t |
| Own bed, KAAP 90 %: same | 19.054 (19.034–19.079; 19.001–19.204) USD/t | 16.429 (16.424–16.435; 16.416–16.464) USD/t |
| Own bed, KAAP 95.55 %: same | 18.729 (18.671–18.803; 18.578–18.959) USD/t | 16.357 (16.346–16.371; 16.327–16.413) USD/t |
| Own bed, 8 wt %, 430–550: gap to Fe, 90 % / 95.55 % recovery | +0.630 to +0.720 / +0.399 to +0.500 USD/t | +0.472 to +0.535 / −0.052 to +0.071 USD/t |
| Own bed, 8 wt %, 430–550: gap to Fe in the KAAP loop, 90 % / 95.55 % | −0.035 to +0.010 / −0.398 to −0.265 USD/t | −0.555 to −0.544 / −0.634 to −0.608 USD/t |
| Own bed α*, 8 wt %, 430–550: none / 90 % / 95.55 % | 19.8–20.2 / 3.26–3.64 / 2.22–2.62 | 10.99–11.14 / 1.53–1.66 / 0.944–1.077 |
| Own bed α*, 8 wt %, 430–550, KAAP 90 % / 95.55 % | 0.945–1.016 / 0.562–0.633 | 0.112–0.121 / 0.067–0.075 |
| Own bed − benchmark reading, 8 wt %, 490: none / 90 % / 95.55 % | +0.114 / +0.291 / +0.328 USD/t | +0.059 / +0.330 / +0.367 USD/t |
| Rows: pressure envelopes / price sweep / α* sweep | 778 / 243 + parity / 244 | 787 / 243 + parity / 244 |

Gaps without a stated reference are against the Fe optimum of the main loop. For the KAAP rows the comparison is with
Fe in the same loop. Rows with unlimited activity still above the main-loop Fe have α* = inf (KAAP rows of
`fig2_ru_actual_cost_points.csv`), as in 1.1.

`make_fig2.py` still renders from the 1.1 files one level up; it is not switched to this folder.
