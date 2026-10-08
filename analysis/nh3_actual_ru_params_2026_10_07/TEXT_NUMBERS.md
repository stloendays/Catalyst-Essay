# Text numbers after adopting the literature Ru parameters (2026-10-07)

Canonical outputs: `figures/composite/fig2/fig2_ru_actual_cost_points.csv`, `fig2_ru_bed_sensitivity.csv`,
`analysis/nh3_mc_ru_actual_2026_10_06/summary.json` (GitHub Actions run 37648545590). Inputs now: recovery r = 0.90–0.97
(CN 1872418 A), commercial Ru/C at 8 wt% Ru (5–10 wt%; Brown et al., Catal. Lett. 144, 545, 2014; US 4,600,571), bed
density 430–550 kg m⁻³ (derived), u ≥ 11 unchanged. Fe: 15.29 (main loop), 19.07 (KAAP loop).

Line numbers refer to `origin/manuscript-fixes-2026-10-07` (each is one paragraph).

## Reference numbers

| Quantity | old | new |
|---|---|---|
| effective price p(1 − r)/u at u = 11 | 294–490 USD/kg | **147–490** |
| benchmark-bed Ru/C + recovery, main loop | 15.49–15.67, +0.19 to +0.38 vs Fe | **15.24–15.67, −0.05 to +0.38** (below Fe at 97%: 15.237, 425 °C, 185 bar; 90%: 15.671, 450 °C, 200 bar) |
| α* benchmark bed | 1.5–2.2× | **0.94–2.23×** (0.936 at 97%, 2.234 at 90%; figure label "0.9–2.2×") |
| benchmark-bed KAAP | 18.53–18.91 | **18.16–18.91** (0.16–0.91 below Fe in the loop) |
| parity needs u | 19.7 (94%), 32.9 (90%) | **9.9 (97%)**, 32.9 (90%) |
| strict-scaling reach (p_eff ≤ 237.3) needs u | 13.6 (94%), 22.7 (90%) | **6.8 (97%)**, 22.7 (90%) |
| own bed, main loop | 15.89–16.44 (3.2 wt%, 500–1,000) | **15.63–16.01** at 8 wt%, 430–550 (markers at 490: 15.67 at 97%, 15.96 at 90%); **15.55–16.24** over 5–10 wt% |
| own bed − Fe, main | +0.60 to +1.15 | **+0.33 to +0.72** at 8 wt% (+0.26 to +0.95 over 5–10 wt%) |
| α* own bed, main | 3.0–5.7× | **1.96–3.64×** at 8 wt% (markers 2.1–3.4×; 1.68–4.72× over 5–10 wt%) |
| own bed, KAAP | 18.92–19.32 | **18.49–19.08** at 8 wt% (markers 18.55 at 97%, 19.05 at 90%); **18.40–19.20** over 5–10 wt% |
| own bed − Fe, KAAP | −0.15 to +0.25 (below Fe only at 94%, 1,000 kg m⁻³) | **−0.58 to +0.01** at 8 wt%: below Fe at 3 of 4 corners (every density at 97%; at 90% only in the 550 kg m⁻³ bed, −0.035; +0.010 at 430). Over 5–10 wt%: −0.67 to +0.13, below Fe at 6 of 8 corners |
| α* own bed, KAAP | 0.76–1.39× | **0.46–1.02×** at 8 wt% (0.41–1.21× over 5–10 wt%) |
| own bed adds to the benchmark reading, no recovery | 0.15–0.31 | **0.10–0.13** at 8 wt% (0.07–0.23 over 5–10 wt%) |
| … with recovery, main | 0.37–0.83 (90–94%) | **0.25–0.49** (90–97%) at 8 wt% (0.19–0.76) |
| … with recovery, KAAP | 0.18–0.61 | **0.12–0.47** at 8 wt% (0.09–0.74) |
| MC P(Fe cheaper), A (benchmark bed) | 48.0% | **35.6%** [34.2, 36.9] |
| MC P(Fe cheaper), A_bed (own bed) | 80.0% | **69.0%** [67.7, 70.3] (Ru content now 5–10 wt%, not the measured catalysts) |
| MC P(Fe cheaper), B (measured catalysts) | 94.3% | **94.7%** [94.0, 95.3] |
| MC P(Fe cheaper), B0 | 98.9% | **99.0%** [98.7, 99.3] |
| A_bed: P(Ru wins), u in lowest tercile | 1.3% | **0.24%** |
| A_bed: P(Ru wins), u and r in top terciles | 50% | **87%** |
| A_bed: P(Ru wins) by Ru content | 0.5% below 2.5 wt%, 39% at ≥ 5 wt% | **25% below 7.5 wt%, 37% at ≥ 7.5 wt%** (range now 5–10 wt%) |
| A_bed: P(Ru wins), r lowest / top tercile | 16% / 23% | **23% / 40%** |
| B: catalysts that ever win | five | **four**: Ru/Ca(NH₂)₂, Ru/Ba–Ca(NH₂)₂, Ru/Cs/Ba/CCHT, Ru/AC-G (Ru/BaO–CaH₂ drops out) |

## Sentences

### `docs/MANUSCRIPT_MAIN_TEXT.md`

**Line 43** (Results, actual Ru catalyst)

- "89–98% of the Ru in spent carbon-supported Ru ammonia catalyst is recovered.[47]": unchanged. It is the source of the
  new r range (CN 1872418 A: 89–97.6%).
- "Read at the effective Ru price p(1 − r)/u, 294–490 US dollars per kilogram, Ru costs 15.49–15.67 US dollars per tonne
  of NH₃, 0.19–0.38 above Fe (Fig. 3d)." → **147–490** USD/kg; **15.24–15.67**; **from 0.05 below to 0.38 above Fe**
  (below Fe at 97% recovery).
- "With the supported catalyst's own bed (3.2 wt% Ru at 500–1,000 kg m⁻³), it costs 15.89–16.44, 0.60–1.15 above Fe;" →
  "(**8 wt% Ru at 430–550 kg m⁻³**), it costs **15.63–16.01, 0.33–0.72** above Fe" (5–10 wt%: 15.55–16.24). Needs the
  loading reference (Brown 2014; US 4,600,571).
- "in a KAAP-type loop … it costs 18.92–19.32 against 19.07 for fused iron, below Fe at 94% recovery in the denser bed." →
  "**18.49–19.08** against 19.07, below Fe at **97% recovery at every bed density and at 90% recovery in the 550 kg m⁻³
  bed**".
- "Supported and recovered Ru thus reaches the Fe cost only in the low-pressure loop for which it was developed, and there
  only at high recovery." → On the catalyst's own bed this still holds (main loop always above Fe, +0.33 to +0.72).
  The benchmark-bed reading at 97% is now 0.05 below Fe in the main loop, so the sentence must refer to the own bed. In
  KAAP, "only at high recovery" no longer holds strictly: 90% is below Fe in the 550 kg m⁻³ bed (−0.035).
- "Fe is cheaper in 80.0% of draws when the supported catalyst's own Ru content and bed density set the reactor volume,
  and in 94.3% with the activities and Ru contents of the 54 measured Ru catalysts" → **69.0%** (commercial Ru content
  5–10 wt%, bed density 430–550 kg m⁻³) and **94.7%**.

**Line 87** (Methods, Monte Carlo)

- "The actual-catalyst Monte Carlo adds inputs drawn from a second generator (seed 20261006)" → add "and, for the Ru
  content of the supported-bed variant, a third (seed 20261007)".
- "Ru recovery uniform over 90–94%;[47]" → **90–97%**[47].
- "Ru content drawn from the measured Ru catalysts;" → "**Ru content of the supported bed uniform over 5–10 wt%** [Brown
  2014; US 4,600,571]" (the measured catalysts' contents now enter only the measured-activity variant, which the last
  sentence of the paragraph already says).
- "bed density uniform over 500–1,000 kg m⁻³" → **430–550 kg m⁻³**.

**Line 93** (Methods, actual-catalyst analysis)

- "r the recovered fraction (90–94%)" → **(90–97%)**.
- "A supported bed holding 3.2 wt% Ru instead of the common formulation changes only the reactor term; recomputing it for
  bed densities of 500–1,000 kg m⁻³ adds 0.15–0.31 US dollars per tonne without recovery and 0.37–0.83 with 90–94%
  recovery (0.18–0.61 in the KAAP loop)." → "holding **8 wt% Ru (5–10 wt%)** … for bed densities of **430–550 kg m⁻³**
  adds **0.10–0.13** without recovery and **0.25–0.49** with **90–97%** recovery (**0.12–0.47** in the KAAP loop)" at
  8 wt% (over 5–10 wt%: 0.07–0.23, 0.19–0.76, 0.09–0.74).

**References**: 45 (Rossetti 2006) stays (dispersion 11%); 47 (CN 1872418 A) now carries the recovery range. Brown et
al., *Catal. Lett.* **144**, 545 (2014) (and optionally US 4,600,571) is needed for the Ru loading; the bed-density
derivation has no published source (`work/expert_check_2026-10-07/PARAMETER_CHECK.md` §1c).

### `docs/SUPPLEMENTARY_INFORMATION.md`

**Line 23** (Supplementary Note, actual Ru catalyst)

- "294–490 US dollars per kilogram for 90–94% recovery at a dispersion gain u = 11" → **147–490** for **90–97%**.
- "At that price Ru costs 15.49–15.67 US dollars per tonne of NH₃, 0.19–0.38 above Fe, at 450 °C and 195–200 bar, and the
  activity multiple required for parity falls from 201-fold to 1.5–2.2-fold." → **15.24–15.67**, **0.05 below to 0.38
  above Fe**, at **425–450 °C and 185–200 bar**; parity multiple falls from 201-fold to **0.94–2.2-fold** (no activity
  gain needed at 97%).
- "this reading gives 18.53–18.91 US dollars per tonne against 19.07" → **18.16–18.91**.
- "With the supported catalyst's own bed (3.2 wt% Ru at 500–1,000 kg m⁻³), Ru costs 15.89–16.44 in the main loop, 0.60–1.15
  above Fe (parity at a 3.0–5.7-fold activity gain), and 18.92–19.32 in the KAAP-type loop, below fused iron at 94%
  recovery in the 1,000 kg m⁻³ bed (parity at 0.76–1.39-fold)." → "(**8 wt% Ru at 430–550 kg m⁻³**), Ru costs
  **15.63–16.01**, **0.33–0.72** above Fe (parity at a **2.0–3.6-fold** gain), and **18.49–19.08** in the KAAP-type
  loop, below fused iron at **97% recovery at every bed density and at 90% in the 550 kg m⁻³ bed** (parity at
  **0.46–1.02-fold**)". Over 5–10 wt%: main 15.55–16.24, KAAP 18.40–19.20.
- Last sentence ("… in the low-pressure loop … across it"): still holds.

**Line 33** (Supplementary Note, actual-Ru Monte Carlo)

- "Ru recovery r (90–94%)" → **(90–97%)**.
- "Fe is cheaper in 48.0% of draws when Ru is read at the effective price … and in 80.0% when its own Ru content and bed
  density set the reactor volume." → **35.6%** and **69.0%** (own bed: commercial Ru content 5–10 wt%, 430–550 kg m⁻³).
- "Ru then wins only when both the dispersion ratio and the Ru content are high: in 1.3% of draws with u in its lowest
  tercile and 50% with u and r in their top terciles, and in 0.5% of draws below 2.5 wt% Ru against 39% at 5 wt% or more;
  recovery within its range matters little." → **0.24%** (u lowest tercile), **87%** (u and r top terciles); Ru
  content now only spans 5–10 wt%: **25% below 7.5 wt% against 37% at 7.5 wt% or more**. Recovery now matters: **23%**
  (r lowest tercile) vs **40%** (top tercile), so "matters little" should go; the dispersion ratio remains the dominant
  input (0.24% → 75% from its lowest to top tercile).
- "Fe is cheaper in 94.3% of draws with recovery and 98.9% without, and the Ru wins come from five of the 54 catalysts
  (Ru on Ca(NH₂)₂, Ba–Ca(NH₂)₂ and BaO–CaH₂, Ba–Cs-promoted Ru/CCHT and Ru/AC-G)." → **94.7%** and **99.0%**; **four**
  of the 54 (Ru on Ca(NH₂)₂ and Ba–Ca(NH₂)₂, Ba–Cs-promoted Ru/CCHT and Ru/AC-G; BaO–CaH₂ drops out).

### `docs/MAIN_FIGURE_CAPTIONS.md`

**Line 17** (Figure 3, panel d)

- "with 90–94% recovery it costs 15.67–15.49 at 195–200 bar, 0.38–0.19 above Fe." → "with **90–97%** recovery it costs
  **15.67–15.24** at **200–185 bar**, from **0.38 above to 0.05 below** Fe".
- "Diamonds, the same reading in the KAAP loop …: 18.53–18.91 against Fe in that loop (19.07, solid line)." →
  **18.16–18.91**.
- "Squares, the Ru/C catalyst's own bed (3.2 wt% Ru; markers at 1,000 kg m⁻³, bars to 500 kg m⁻³) with 90–94% recovery:
  15.89–16.44 in the main loop and 18.92–19.32 in the KAAP loop." → "Squares, the commercial Ru/C catalyst's own bed
  (**markers at 8 wt% Ru and 490 kg m⁻³; bars over 5–10 wt% Ru and 430–550 kg m⁻³**) with **90–97%** recovery:
  **15.67–15.96 (bars 15.55–16.24)** in the main loop and **18.55–19.05 (bars 18.40–19.20)** in the KAAP loop."
- "Bottom … 1.5–2.2× with recovery." → **0.9–2.2×** with recovery (0.94–2.23); the own-bed squares in the bottom panel
  are labelled **2.1–3.4×** (markers; bars 1.7–4.7×).
- Parity 164 USD/kg, 201×, 18×, 22.03, 17.95, ≤ 237 shading: unchanged.

### `figures/extended_data/ED_CAPTIONS.md` (Extended Data Fig. 7)

Regenerated by `render_extended_data.py` (committed): A 0.356, A_bed 0.690 (commercial Ru/C bed, 5–10 wt%,
430–550 kg m⁻³), B 0.947, B0 0.990, r 0.9–0.97; panel d now bins the A_bed Ru content (5–10 wt%).

## Tooling the main session must follow up

- `tools/audit_live_manuscript_truth.py` (not edited here) reads the points-file keys `supp_rec94` and `kaap94`; these
  rows are now `supp_rec97` and `kaap97` (r = 0.97), and `fig2_ru_bed_sensitivity.csv` gained a `w_Ru` column with
  rows at w ∈ {0.05, 0.08, 0.10} × ρ ∈ {430, 490, 550}. The audit will fail until it is updated together with the text.
