# Measured ammonia catalysts through the plant chain — 2026-10-06

Advisor 2026-10-05, item 3: add real supported catalysts to the ammonia candidate set; a supported catalyst carries
its own metal content, which also replaces the pure-metal benchmark formulation.

`run_supported_chain.py` writes `supported_candidates.csv`, `group_metrics.csv` and `summary.json`. Input:
`agent/nh3_supported/out/records.csv` (extraction and adjudication: `agent/nh3_supported/README.md`).

## Data

Humphreys, Lan & Tao, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021), doi:10.1002/aesr.202000043, Tables 1–6:
164 printed rows, 161 after removing rows the review prints twice (Tables 2 and 3). 85 enter the chain; 76 do not
(66 without a metal content, 25 without a single model metal — bimetallic catalysts and nitrides —, 10 without a rate;
a row can have several reasons).

## Mapping

The model converts a per-site TOF into metal inventory with one calibration (fused Fe, 65 m³ for 1,000 t/d), so its
rate per gram of metal is F_CAL × TOF(E_N) / MW. Each catalyst's measured rate per gram of metal, at its laboratory T,
P and NH₃ fraction, is inverted into an effective descriptor E_eff on its metal's side of the volcano; a rate above the
volcano top places it at the top with a residual factor α_res. The catalyst then goes through the 14,136-state library
as that descriptor, with its metal's molar mass and price and its own metal content (bed density 1,000 kg m⁻³; fused
Fe keeps the benchmark 71.51 wt% and 2,500 kg m⁻³). The model's NH₃ formation free energy lies 0.10 eV above
experiment (673 K), so the laboratory NH₃ fraction is entered at the same approach to equilibrium as in the
experiment (Gillespie–Beattie equilibrium). Primary set: 300–500 °C, steady thermal operation, outlet below 90 % of
equilibrium (75 catalysts); 10 are flagged (chemical looping, applied field or microwave, outside 300–500 °C, or
outlet near equilibrium).

Calibration check: the two fused-iron catalysts with a printed rate (Fe₁₋ₓO and Fe₃O₄, 430 °C, 3 MPa, ref. 157 of the
review) give α = 0.64 and 0.45 against the plant calibration, and the better one costs 15.52 USD/t against the
15.29 USD/t benchmark.

## Results (primary set, no metal recovery)

| Metal | Catalysts | Below Fe | Lowest cost (USD/t) | Catalyst |
|---|---:|---:|---:|---|
| Ru | 56 | 0 | 15.32 | Ru/Cs/Ba/CCHT |
| Fe | 9 | 0 | 15.52 | Fe₁₋ₓO (fused) |
| Co | 5 | 1 | 14.46 | 5.2 wt% Co/CNT, BaHₓ-promoted |
| Ni | 5 | 0 | 20.42 | Ni/LaN NPs |

- Highest laboratory rate: Ru/AC-G (312,500 µmol g⁻¹ h⁻¹, 400 °C, 10 MPa), 17.53 USD/t, 21 % above the plant
  leader. Spearman ρ between rate and plant cost across the 75 catalysts: 0.11.
- Within one source at one T and P (10 comparisons): the rate leader differs from the plant leader in 3. In both
  studies that test Fe and Ru on the same support (BaTiO₃₋ₓHₓ and BaCeO₃₋ₓHᵧN_z), Ru has the higher rate and Fe the
  lower plant cost (18.6 % and 13.0 % regret).
- The only catalyst below Fe is BaHₓ-promoted Co/CNT, whose laboratory rate at 300 °C lies 31-fold above the
  model's volcano top.
- With 90 % Ru recovery, 3 of the 56 Ru catalysts undercut Fe (Ru/Cs/Ba/CCHT 14.41, Ru/Ba–Ca(NH₂)₂, Ru/Ca(NH₂)₂).

## Sensitivity

| Variant | Below Fe |
|---|---|
| bed density 500 kg m⁻³ | Co/CNT |
| bed density 2,500 kg m⁻³ | Co/CNT, 20 % Fe–BaH₂ |
| catalysts measured at ≥ 5 MPa (17) | none (Fe 16.67, Ru 17.53, Co 23.68 USD/t) |
| constant multiplier on the metal's own TOF instead of E_eff | 9 (adds four Ni, three Fe and one Ru catalyst) |

20 primary catalysts have neither an outlet NH₃ value nor a WHSV; they use the median outlet fraction (0.43 %).
The script calls the ACSA self-check gate first.
