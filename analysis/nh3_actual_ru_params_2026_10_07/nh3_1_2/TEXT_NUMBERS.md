# Text numbers of the actual-Ru analysis on NH3-FINAL-1.2

Written by `text_numbers.py` from the committed outputs of both models (no harness). Literature inputs as in
the current text: u = 11 (Fig. 3d) or log-uniform 11–50 (Monte Carlo), r = 0.90–0.9555, commercial Ru/C at
8 wt% Ru (5–10 wt%), bed density 430–550 kg m⁻³, KAAP loop at 90 bar and T_sep −20 °C. The 1.1 column equals
the numbers printed in `docs/` at the branch point (2026-10-13); line numbers refer to that version
(main = `docs/MANUSCRIPT_MAIN_TEXT.md`, SI = `docs/SUPPLEMENTARY_INFORMATION.md`, Fig. 3d caption =
`docs/MAIN_FIGURE_CAPTIONS.md` l.17, ED Fig. 7a = `figures/extended_data/ED_CAPTIONS.md`).

Gaps are Ru − Fe in the same loop. Sources: own-bed rows at 430/550 kg m⁻³, benchmark-bed rows and the
Monte Carlo from `summary.json` / `fig3d_readings.csv` (this analysis, set R_all); the 490 kg m⁻³ markers and
the own-bed increments from `figures/composite/fig2/nh3_1_2/fig2_ru_bed_sensitivity.csv`; every overlap
between the three sources is asserted equal to 1e-9 first.

| Quantity | Used in | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|---|
| Effective Ru price p(1 − r)/u, u = 11, r = 90–95.55% (input only) | main l.43; SI l.59 | 218–490 USD/kg | **218–490 USD/kg** |
| Benchmark-bed reading, main loop | main l.43; SI l.59; Fig. 3d caption | 15.41–15.67 USD/t; +0.12 to +0.38 vs Fe | **11.15–11.69 USD/t; −0.37 to +0.17 vs Fe** |
| … its optimum states (90% and 95.55%) | SI l.59 ("450 °C and 195–200 bar") | 450 °C, 195 bar; 450 °C, 200 bar | **425 °C, 110 bar** |
| … activity multiple α* for parity | main l.43; SI l.59; Fig. 3d caption | 1.21–2.23-fold | **0.60–1.19-fold** |
| Benchmark-bed reading, KAAP loop (90 bar, T_sep −20 °C) | main l.43; SI l.59; Fig. 3d caption | 18.34–18.91 USD/t; −0.73 to −0.16 vs Fe in the loop | **16.27–16.39 USD/t; −0.71 to −0.59 vs Fe in the loop** |
| Fe optimum, main loop | reference of every main-loop gap | 15.29 USD/t | **11.52 USD/t** |
| Fe in the KAAP loop | main l.43; SI l.59; Fig. 3d caption | 19.07 USD/t | **16.98 USD/t** |
| Parity price of the Fig. 2d sweep | Fig. 3d caption ("164 US dollars per kilogram") | 163.76 USD/kg | **403.54 USD/kg** |
| u needed for parity at r = 95.55% / 90% | docs/SOURCE_OF_TRUTH (cited from TEXT_NUMBERS.md) | 14.6 / 32.9 | **5.9 / 13.3** |
| Own Ru/C bed, 8 wt% Ru, 430–550 kg m⁻³, r 90–95.55%, main loop | main l.43; SI l.59 | 15.69–16.01 USD/t; +0.40 to +0.72 vs Fe (15.29) | **11.46–12.05 USD/t; −0.05 to +0.53 vs Fe (11.52)** |
| … α* for parity, main loop | SI l.59 | 2.22–3.64-fold | **0.94–1.66-fold** |
| … corners below Fe, main loop (8 wt%; 430, 490, 550 kg m⁻³ × 2 recoveries) | main l.43 ("stays above it") | 0 of 6 | **1 of 6: 95.55% at 550 (−0.052); within 0.02 above: 95.55% at 490 (+0.002)** |
| Own Ru/C bed, 8 wt% Ru, 430–550 kg m⁻³, KAAP loop | main l.43; SI l.59 | 18.67–19.08 USD/t; −0.40 to +0.01 vs Fe in the loop (19.07) | **16.35–16.44 USD/t; −0.63 to −0.54 vs Fe in the loop (16.98)** |
| … α* for parity, KAAP loop | SI l.59 | 0.562–1.016-fold | **0.067–0.121-fold** |
| … corners below Fe in the KAAP loop (same 6 corners) | main l.43; SI l.59 | 5 of 6: 90% at 490 (−0.015), 90% at 550 (−0.035), 95.55% at 430 (−0.265), 95.55% at 490 (−0.340), 95.55% at 550 (−0.398); within 0.02 above: 90% at 430 (+0.010) | **6 of 6: 90% at 430 (−0.544), 90% at 490 (−0.551), 90% at 550 (−0.555), 95.55% at 430 (−0.608), 95.55% at 490 (−0.622), 95.55% at 550 (−0.634)** |
| Own bed over 5–10 wt% Ru, main loop | SI l.59; Fig. 3d caption (bars) | 15.62–16.24 USD/t | **11.38–12.20 USD/t** |
| Own bed over 5–10 wt% Ru, KAAP loop | SI l.59; Fig. 3d caption (bars) | 18.58–19.20 USD/t | **16.33–16.46 USD/t** |
| Fig. 3d squares, 8 wt%, 490 kg m⁻³, main loop | Fig. 3d caption | 15.96–15.74 USD/t (r 90% → 95.55%) | **12.02–11.52 USD/t (r 90% → 95.55%)** |
| Fig. 3d squares, 8 wt%, 490 kg m⁻³, KAAP loop | Fig. 3d caption | 19.05–18.73 USD/t (r 90% → 95.55%) | **16.43–16.36 USD/t (r 90% → 95.55%)** |
| Fig. 3d bottom, own-bed α* at the squares | Fig. 3d caption ("2.4–3.4×") | 2.4–3.4× | **1.0–1.6×** |
| Own bed minus benchmark reading, 8 wt%, 430–550, no recovery | main l.93 | 0.10–0.13 USD/t | **0.05–0.07 USD/t** |
| … with 90–95.55% recovery, main loop | main l.93 | 0.25–0.38 USD/t | **0.30–0.44 USD/t** |
| … with 90–95.55% recovery, KAAP loop | main l.93 | 0.12–0.47 USD/t | **0.03–0.10 USD/t** |
| Monte Carlo, benchmark bed at p(1 − r)/u (A): P(Fe cheaper) [95% CI] | SI l.69; ED Fig. 7a | 41.9% [40.5, 43.3]; median Ru − Fe −0.05 USD/t | **9.2% [8.4, 10.1]; median Ru − Fe −0.52 USD/t** |
| Monte Carlo, commercial Ru/C bed 5–10 wt%, 430–550 kg m⁻³ (A_bed of the text = A_comm here) | main l.43; SI l.69; ED Fig. 7a | 71.9% [70.7, 73.2]; median Ru − Fe +0.21 USD/t | **20.7% [19.5, 21.8]; median Ru − Fe −0.33 USD/t** |
| Monte Carlo, 54 measured Ru catalysts with recovery (B) | main l.43; SI l.69; ED Fig. 7a | 94.7% [94.0, 95.3]; median Ru − Fe +4.98 USD/t | **93.0% [92.2, 93.7]; median Ru − Fe +3.52 USD/t** |
| Monte Carlo, measured catalysts without recovery (B0) | SI l.69; ED Fig. 7a | 99.0% [98.7, 99.3]; median Ru − Fe +7.77 USD/t | **98.1% [97.6, 98.4]; median Ru − Fe +6.20 USD/t** |

Statements whose truth changes under 1.2 (each asserted on the data by `facts()`):

- Benchmark-bed reading, main loop: below Fe at 95.55% recovery (1.1: above Fe at both ends of the range).
- Own bed at 8 wt%, main loop: below Fe at 95.55% recovery in the 550 kg m⁻³ bed (−0.052) and
  +0.0018 USD/t from Fe in the 490 kg m⁻³ bed; above Fe at 90% recovery and at 430 kg m⁻³
  (1.1: above Fe at every corner, +0.40 to +0.72). The main-l.43 clause "stays
  above it in the high-pressure Fe loop" therefore no longer holds at the upper recovery.
- Own bed, KAAP loop: below Fe at every recovery, bed density and Ru content in the tables (1.1: above Fe at 90%
  recovery in the 430 kg m⁻³ bed, +0.010).
- Monte Carlo, commercial Ru/C bed: P(Fe cheaper) 0.719 → 0.207, and the median Ru − Fe
  gap changes sign (Ru is cheaper in most draws). The measured catalysts (B, B0) keep Fe ahead (> 90%).
