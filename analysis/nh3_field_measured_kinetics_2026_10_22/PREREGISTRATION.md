# Ammonia within-paper comparisons on measured rate laws — preregistration (2026-10-22)

Committed before any result of this folder is computed. Every quantity below is reported whatever its direction; any
later change goes into a dated addendum at the end.

## Question

The manuscript's ammonia field result (12 of 44 comparisons; NH3-FINAL-1.2, `analysis/nh3_field_expansion_2026_10_12/
nh3_1_2/runs/pooled_vf_screen`) maps each measured catalyst onto the descriptor microkinetics (effective descriptor
`E_eff`) and extrapolates it from laboratory to plant conditions with those kinetics. The manuscript itself shows that
the descriptor kinetics misstate the H₂ order of Ru (+2.4 against +0.3 measured). Does the count hold when Fe and Ru
catalysts are extrapolated with measured rate laws instead?

## Fixed inputs

- Entries and groups: `candidates_printed.csv` of the pooled 1.2 run above, unchanged (237 entries, 44 groups,
  paper leaderboard `paper_rate`). Grouping, leaderboard and the aggregation code are those of
  `analysis/nh3_field_2026_10_06/run_field_chain.py` (`aggregate`, `group_metrics`), imported unchanged.
- Process states, costs: the 14,510 states of NH3-FINAL-1.2; per-state catalyst amount by isothermal plug flow and cost
  = metal (no recovery) + reactor + process terms, V ≤ 90 m³ (`analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py`
  `amount`, `costs`, `reactor`, imported unchanged). Metal prices of the harness. Bed density 2,500 kg m⁻³ and 71.51 wt%
  for commercial fused/wüstite iron, otherwise the entry's metal content and 1,000 kg m⁻³ (the frozen field mapping).

## Rate laws (shape only; each entry carries its own activity factor)

| Metal | Law | Fitted range used for plant states |
|---|---|---|
| Fe (fused references and supported Fe) | Keestra et al. 2025, Model 3 (`nh3_fe_inrange_kinetics_2026_10_19/keestra_fe.py`, source K_f) | 1–324 bar → states 10–320 bar |
| Ru | Cholewa et al. 2024, Sustain. Energy Fuels 8, 2245, eqn (12), Table 3 (Ru/CeO₂), α = 0.25 | 10–80 bar(g) = 11–81 bar → states 15–80 bar; 350–450 °C |
| Co, Ni | no measured law: frozen descriptor cost kept | — |

Cholewa eqn (12): r = k₂ [a_N₂^0.5 K_eq (a_H₂^1.5/a_NH₃)^α − (a_NH₃/a_H₂^1.5)^(1−α)] / (1 + K₂ a_H₂^(1.5 f₂) + K₃ a_NH₃^f₃),
k₂ = 3.49×10⁸ exp(−1.06×10⁵/RT) mol s⁻¹ kg⁻¹, K_i = exp(−ΔH_i/RT + ΔS_i/R) with ΔH₂ = −8.71×10⁴ J mol⁻¹,
ΔS₂ = −80.1 J mol⁻¹ K⁻¹, f₂ = 0.116, ΔH₃ = −1.184×10⁴ J mol⁻¹, ΔS₃ = −143 J mol⁻¹ K⁻¹, f₃ = 0.414. Activities are
Newton–Cooper fugacities in bar (as for every measured law in the cost model); K_eq is the Gillespie–Beattie constant of
½N₂ + 3/2H₂ = NH₃ in bar⁻¹ (`keestra_fe.Kf_GB`).

## Calibration

Each Fe or Ru entry's activity factor A makes A·r_law equal its printed rate per kg catalyst at its laboratory T, P,
H₂/N₂ = 3 and NH₃ fraction y_lab = min(½ y_out, ½ y_eq) — the composition convention of the frozen mapping.

## Primary result and reported variants

Primary: groups whose paper leader is not the plant-cost leader, groups with regret > 5 %, kinds of mismatch, papers,
paper-cluster bootstrap 95 % CI (10,000, seed 20261006), next to the frozen descriptor result recomputed from the same file.

Variants (all reported): (a) Ru law Rossetti 2006 (50–100 bar states); (b) Co and Ni entries removed; (c) entries whose
laboratory P or T lies outside their law's fitted range removed; (d) Ru plant states not restricted to the fitted range;
(e) groups containing only Fe and Ru.

## Gates (must pass before results are read)

1. The frozen descriptor costs of the file reproduce 12/44 through `aggregate`.
2. Keestra Fe on this code path reproduces the in-range Fe benchmark optimum 15.307473 USD/t
   (`nh3_keestra_consolidation_2026_10_20` table A) to 1e-6 relative.
3. Cholewa law: rate zero at equilibrium (|r| < 1e-9 relative); at 400 °C, 45 bar and low conversion the rate at
   H₂/N₂ = 1.5 exceeds that at 3.0 by more than 1.5× (the paper reports > 80 %, Fig. 5b).
4. Every calibrated entry reproduces its laboratory rate to 1e-9 relative.

## Addendum 1 (2026-10-22, after the gates ran, before any comparison was read)

- Gate 3 as written used the ideal-gas Gillespie–Beattie equilibrium, while every rate law here runs on Newton–Cooper
  fugacities; the zero-rate check is redefined on the fugacity equilibrium (`run_supported_chain.y_eq_exp_fugacity`)
  with a relative tolerance of 1e-3 (the two Newton–Cooper implementations differ in unit handling at that level).
- Cholewa eqn (12) with its Table 3 parameters gives a rate ratio of 1.21 between H₂/N₂ = 1.5 and 3.0 at 400 °C,
  45 bar and low conversion, against > 1.8 in the source's Fig. 5b. The printed denominator exponent 1.5·f₂ = 0.174
  cannot produce the reported H₂ inhibition, so the law as printed fails gate 3 (transcription re-checked at 5× render).
  The primary Ru law therefore becomes Rossetti et al. 2006 (fitted 50–100 bar, 370–460 °C; validated on its 125 points
  in `nh3_staged_converter_2026_10_12/validate_kinetics.py`, mean error 10 %), the law the manuscript already uses for
  Ru/C. Cholewa eqn (12) as printed is reported as a variant. Gate 3 applies to the primary law (Rossetti): zero rate at
  equilibrium. Variant (a) becomes "Ru law Cholewa 2024 as printed (11–81 bar states)".

## Addendum 2 (2026-10-22, added after the primary result was read; reported as such)

First run: primary 4/25 groups, because 98 of 237 entries (82 Ru, 16 Fe) need more than the 90 m³ bed at every state
and drop out of their groups. Their activity factors are low because a Temkin-type law, evaluated at the near-zero NH₃
fraction of a differential laboratory test, predicts a very high rate; commercial fused-iron references come out at
0.5–6 % of the KM1R-1964 activity. Three treatments are added and reported next to the primary:

- (f) infeasible entries stay in their group, ranked last (a plant cannot build them), instead of being dropped;
- (g) integral calibration: the activity factor reproduces the measured rate over the laboratory bed in plug flow,
  A = R · mean over ξ∈[0, ξ_out] of 1/r_law, the same sizing the plant side uses (with (f));
- (h) reference anchoring: in a group that contains a commercial fused-iron reference, every entry's activity factor is
  multiplied by the factor that brings that reference to the KM1R-1964 commercial activity (b_cat = 0.350, the plant
  benchmark), so the paper's own reference sets the laboratory-to-plant correction (on (g), with (f)).
