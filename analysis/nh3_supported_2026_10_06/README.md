# Measured ammonia catalysts through the plant chain — 2026-10-06

Advisor 2026-10-05, item 3: add real supported catalysts to the ammonia candidate set; a supported catalyst carries
its own metal content, which also replaces the pure-metal benchmark formulation.

`run_supported_chain.py` writes `supported_candidates.csv`, `group_metrics.csv` and `summary.json`. Input:
`agent/nh3_supported/out/records.csv` (extraction and adjudication: `agent/nh3_supported/README.md`).

**Primary-source errata (2026-10-06, branch `humphreys-errata`, builds on PR #27).** The PR #27 field analysis
checked the review rows against the cited papers and found ten review errors in nine rows
(`agent/nh3_field/eval/humphreys_adjudication.csv`). They are applied as a layer after the manual adjudication
(`agent/nh3_supported/out/primary_errata.csv`; the column `erratum` of `records.csv` and of
`supported_candidates.csv` names each correction); the paper value supersedes the review value:

| Row | Review | Paper | Effect here |
|---|---|---|---|
| ref. 104 "Ru/TiH₂ 0.9 wt%" (T2 p11 r6) | Ru catalyst | Ru-free TiH₂ | leaves the Ru set (was 25.73 USD/t) |
| ref. 104 "Ru/BaTiO₂.₅H₀.₅ 0.9 wt%" (p11 r7) | Ru catalyst | Ru-free BaTiO₂.₅H₀.₅ | leaves the Ru set (was 27.50) |
| ref. 199 BaHₓ-promoted 5.2 wt% Co/CNT (T4 p16 r7) | WHSV 6,000 | 60,000 | 14.46 → 18.28 USD/t |
| ref. 186 Ru/CeO₂–CS (p11 r0) | WHSV 70,000 | 24,000 | 23.43 → 22.66 |
| ref. 100 Ru/CeO₂-r, 10 MPa (p11 r10) | WHSV 70,000 | 70 dm³ h⁻¹ / 0.30 g = 233,333 | 23.26 → 28.16 |
| ref. 81 Ru/BaTiO₂.₅H₀.₅ (p11 r8) | 1.0 wt%, WHSV 36,000 | 0.86 wt%, 66,000 | 23.65 → 22.98 |
| ref. 200 Co–N–C (p16 r8) | 3.4 wt% Co | 3.73 wt% | 22.60 → 22.54 |
| ref. 159 FeOOH(-K)/Al₂O₃ (T1 p6 r20) | WHSV 26,400 | 12,000 | none (no metal content; outside) |
| ref. 81 Co/BaTiO₃₋ₓHₓ (p16 r13) | 5,700 µmol g⁻¹ h⁻¹ | 5,500 | none (no metal content; outside) |

All five costs PR #27 predicted for the corrected rows (Co/CNT 18.28, Ru/CeO₂–CS 22.66, Ru/BaTiO₂.₅H₀.₅ 22.98,
Co–N–C 22.54, Ru/CeO₂-r 28.16 USD/t) are reproduced to the second decimal by this rerun.

Judgement calls. (i) The Ru-free rows keep their printed rate but get no active metal and no metal content, and their
name carries "(Ru-free)"; they stay in `records.csv` and fall outside the chain. (ii) The Ru/CeO₂-r WHSV is entered as
70,000 mL h⁻¹ / 0.30 g = 233,333 mL g⁻¹ h⁻¹ (PR #27 rounds it to 233,000; the cost is 28.16 USD/t either way).
(iii) Name-only discrepancies without a wrong number (the omitted K and BaH₂ promoters, which the promoter column
already carries; the Fe/BaTiO₂.₃₅H₀.₆₅ and Ba₀.₈Co₁.₀/C identities) are not changed. (iv) The median outlet NH₃
fraction used for the 20 primary catalysts without outlet or WHSV is recomputed from the corrected records:
0.458 % → 0.427 %. This moves three 10 MPa, 400 °C Ru catalysts by 4.5–6.7 USD/t (Ba/Ru/BN 27.56 → 22.22,
Ru–N–MC 29.52 → 22.80, Ru/MC 26.98 → 22.44): their E_eff moves from about −0.91 to −1.27 eV, so the inversion for
these rows is sensitive to the assumed outlet. The other 14 catalysts on the median move by less than 0.25 USD/t. No
leader, count or below-Fe set depends on these three rows; Spearman ρ does (see below).

## Data

Humphreys, Lan & Tao, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021), doi:10.1002/aesr.202000043, Tables 1–6:
164 printed rows, 161 after removing rows the review prints twice (Tables 2 and 3). 83 enter the chain; 78 do not
(68 without a metal content, 27 without a single model metal — bimetallic catalysts, nitrides and the two Ru-free
ref. 104 rows —, 10 without a rate; a row can have several reasons). Before errata: 85 enter, 76 do not (66, 25, 10).

## Mapping

The model converts a per-site TOF into metal inventory with one calibration (fused Fe, 65 m³ for 1,000 t/d), so its
rate per gram of metal is F_CAL × TOF(E_N) / MW. Each catalyst's measured rate per gram of metal, at its laboratory T,
P and NH₃ fraction, is inverted into an effective descriptor E_eff on its metal's side of the volcano; a rate above the
volcano top places it at the top with a residual factor α_res. The catalyst then goes through the 14,136-state library
as that descriptor, with its metal's molar mass and price and its own metal content (bed density 1,000 kg m⁻³; fused
Fe keeps the benchmark 71.51 wt% and 2,500 kg m⁻³). The outlet NH₃ fraction is the printed value or, from the rate n
and the inlet space velocity F₀, n / (F₀ − n). The model's NH₃ formation free energy lies 0.064–0.065 eV per NH₃ above
experiment (573–773 K), so the laboratory NH₃ fraction is entered at the same approach to equilibrium as in the
experiment (Gillespie–Beattie equilibrium). Primary set: 300–500 °C, steady thermal operation, outlet below 90 % of
equilibrium (73 catalysts; 75 before errata); 10 are flagged (chemical looping, applied field or microwave, outside 300–500 °C, or
outlet near equilibrium).

Calibration check: the two fused-iron catalysts with a printed rate (Fe₁₋ₓO and Fe₃O₄, 430 °C, 3 MPa, ref. 157 of the
review) give α = 0.65 and 0.46 against the plant calibration, and the better one costs 15.51 USD/t against the
15.29 USD/t benchmark.

## Results (primary set, no metal recovery)

| Metal | Catalysts | Below Fe | Lowest cost (USD/t) | Catalyst |
|---|---:|---:|---:|---|
| Ru | 54 | 0 | 15.32 | Ru/Cs/Ba/CCHT |
| Fe | 9 | 0 | 15.51 | Fe₁₋ₓO (fused) |
| Co | 5 | 0 | 18.28 | 5.2 wt% Co/CNT, BaHₓ-promoted |
| Ni | 5 | 0 | 20.41 | Ni/LaN NPs |

Before errata: Ru 56 / 0 / 15.32; Co 5 / 1 / 14.46 (Co/CNT); Fe and Ni unchanged.

- No primary catalyst undercuts the 15.29 USD/t Fe benchmark without metal recovery; the plant leader is
  Ru/Cs/Ba/CCHT (15.32 USD/t). Before errata: BaHₓ-promoted Co/CNT, 14.46 USD/t, the only catalyst below Fe, with a
  laboratory rate 31-fold above the model's volcano top at 300 °C. With the paper's WHSV its outlet is 0.18 % NH₃
  instead of 1.79 % and its rate lies on the volcano (α_res = 1).
- Highest laboratory rate: Ru/AC-G (312,500 µmol g⁻¹ h⁻¹, 400 °C, 10 MPa), 17.22 USD/t, 12.4 % above the plant
  leader (17.53 and 14.4 % before the outlet fix of 2026-10-07; before errata 21.2 %, against Co/CNT). Spearman ρ
  between rate and plant cost across the 73 catalysts: 0.16 (0.158; 0.156 before the outlet fix; before errata 0.11 across 75; with the errata alone and the median outlet held at 0.458 %, 0.07 — the rise to
  0.16 comes from the three 10 MPa Ru catalysts that move with the median, judgement call iv).
- Within one source at one T and P (9 comparisons; 10 before errata, the ref. 104 Ru/TiH₂–Ru/BaTiO₂.₅H₀.₅ pair is
  gone): the rate leader differs from the plant leader in 3 (unchanged). In both studies that test Fe and Ru on the
  same support (BaTiO₃₋ₓHₓ and BaCeO₃₋ₓHᵧN_z), Ru has the higher rate and Fe the lower plant cost (15.2 % and 12.6 %
  regret; 15.2 % and 13.0 % before the outlet fix; before errata 18.6 % and 13.0 %).
- With 90 % Ru recovery, 3 of the 54 Ru catalysts undercut Fe (Ru/Cs/Ba/CCHT 14.41, Ru/Ba–Ca(NH₂)₂, Ru/Ca(NH₂)₂);
  before errata 3 of 56, the same three.

## Sensitivity

| Variant | Below Fe | Before errata |
|---|---|---|
| bed density 500 kg m⁻³ | none | Co/CNT |
| bed density 2,500 kg m⁻³ | 20 % Fe–BaH₂ | Co/CNT, 20 % Fe–BaH₂ |
| catalysts measured at ≥ 5 MPa (15; 17 before) | none (Fe 16.67, Ru 17.22, Co 23.73 USD/t; Ru 17.53 before the outlet fix) | none (Fe 16.67, Ru 17.53, Co 23.68) |
| constant multiplier on the metal's own TOF instead of E_eff | 9 (Co/CNT, four Ni, three Fe, one Ru) | the same 9 |
| 90 % Ru recovery | 3 of 54 Ru | 3 of 56 Ru |

20 primary catalysts have neither an outlet NH₃ value nor a WHSV; they use the median outlet fraction (0.429 %;
0.427 % before the outlet fix; 0.458 % before errata).

## Outlet NH₃ fraction from rate and WHSV (2026-10-07, review finding A, minor)

The outlet fraction computed from the rate n and the inlet space velocity F₀ was n / F₀; the outlet gas flow is
F₀ − n (N₂ + 3 H₂ → 2 NH₃ removes one mole of gas per mole of NH₃), so it is now n / (F₀ − n)
(`run_supported_chain.py`, `y_out_from_rate`; the field chain imports the same function). Rows with a printed outlet do
not change. Primary catalysts: median |Δcost| 0.002 USD/t, nine move by more than 0.05 USD/t, the largest
Ru/C12A7 (microcube) 25.45 → 26.20 and Ru/AC-G 17.53 → 17.22. Rerun with the same inputs:

| Quantity | Before | After |
|---|---:|---:|
| primary catalysts / below Fe / lowest Ru (Ru/Cs/Ba/CCHT) | 73 / 0 / 15.32 | 73 / 0 / 15.32 |
| Fe₁₋ₓO / Fe₃O₄ α; best fused Fe | 0.64 / 0.45; 15.52 | 0.65 / 0.46; 15.51 |
| lowest Co / Ni (USD/t) | 18.28 / 20.42 | 18.28 / 20.41 |
| Ru/AC-G (highest rate) cost; regret over the plant leader | 17.53; 14.4 % | **17.22; 12.4 %** |
| Spearman ρ, rate vs plant cost (73) | 0.156 | 0.158 |
| rate leader ≠ plant leader, single-source comparisons | 3 of 9 | 3 of 9 |
| same-support Fe/Ru regrets (BaTiO₃₋ₓHₓ; BaCeO₃₋ₓHᵧN_z) | 15.2 %; 13.0 % | 15.2 %; **12.6 %** |
| ref. 164 Ru/BaZr₀.₉Y₀.₁O₃ vs Ru/BaZrO₃ regret | 6.4 % | 6.8 % |
| Ru below Fe with 90 % recovery | 3 of 54 (Ru/Cs/Ba/CCHT 14.41) | 3 of 54, the same three (14.41) |
| median Ru α (per g Ru, against the benchmark) | 0.220 | 0.226 |
| ≥ 5 MPa lowest Ru / Co | 17.53 / 23.74 | 17.22 / 23.73 |
| median outlet for the 20 catalysts without outlet or WHSV | 0.427 % | 0.429 % |
| bed 500 / 2,500 kg m⁻³ below Fe; constant-multiplier variant | none / 20 % Fe–BaH₂; 9 | unchanged |
The script calls the ACSA self-check gate first.
