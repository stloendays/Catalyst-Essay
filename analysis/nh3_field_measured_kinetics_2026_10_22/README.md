# Ammonia within-paper comparisons on measured rate laws (item D, 2026-10-22)

Protocol and addenda: `PREREGISTRATION.md`. Script: `measured_field.py` (`NH3_MODEL=1.2`, ~1 min). Outputs: `summary.json`,
`candidates_measured.csv`, `group_metrics_<variant>.csv`, `group_comparison.csv`.

Gates: frozen descriptor costs reproduce 12/44; Keestra Fe on this code path reproduces the in-range Fe benchmark
15.307473 USD/t; Rossetti rate vanishes at the fugacity equilibrium. Cholewa 2024 eqn (12) as printed gives a 1.21-fold
rate gain from H₂/N₂ = 3 to 1.5 at 400 °C and 45 bar, against > 1.8 in its own Fig. 5b, so it is a variant, not the
primary Ru law (Addendum 1).

## Result

| Basis | Paper leader ≠ plant leader | > 5 % | Papers | CI 95 % |
|---|---:|---:|---:|---|
| Descriptor kinetics (manuscript, frozen) | **12/44** | 8 | 31 | 14–42 % |
| Measured laws, Fe Keestra / Ru Rossetti, single-point calibration (primary) | **4/25** | 4 | 18 | 4–33 % |
| same, infeasible entries ranked last (all 44 groups) | 4/44 | 4 | 31 | 2–18 % |
| same, integral calibration over the laboratory bed | 4/44 | 4 | 31 | 2–18 % |
| same, anchored on the paper's commercial fused-iron reference | 4/44 | 4 | 31 | 2–18 % |
| Ru on Cholewa 2024 as printed | 5/27 | 5 | 19 | 4–37 % |
| Ru plant states not limited to 50–100 bar | 6/32 | 6 | 23 | 3–36 % |
| Co and Ni entries removed | 3/19 | 3 | 13 | 0–36 % |
| groups of Fe and Ru only | 2/17 | 2 | 11 | 0–31 % |
| laboratory point inside the law's fitted range | 1/8 | 1 | 7 | 0–43 % |

## What drives the difference

1. **Extrapolation, not the plant model.** 167 of the 237 laboratory points lie outside the fitted range of every
   measured law (mostly 0.1–1 MPa and NH₃ fractions of 0.1–0.5 %). A Temkin-type law has its rate diverge as NH₃ → 0,
   so a differential laboratory point calibrates a small activity factor, and the same catalyst then needs more than the
   90 m³ bed at plant NH₃ levels: 98 of 237 entries (82 Ru, 16 Fe) are infeasible at every state, and 19 of the 44
   groups keep fewer than two feasible entries. The feasible Ru entries cost 38 USD/t on average on the measured law,
   against 16 USD/t on the descriptor kinetics.
2. **The fused-iron references of these papers.** Calibrated on the Keestra law, the commercial fused or wüstite iron
   references come out at 0.5–6 % of the KM1R-1964 commercial activity at 450 °C and 1 MPa (anchor factors 2–198), so
   in the laboratory comparisons the new catalyst is set against a reference that runs one to two orders of magnitude
   below its commercial activity. On the measured law these references cannot be built, and the five "fused-iron
   reference" reversals of the descriptor result disappear; anchored on commercial activity, one of the five groups
   reverses.
3. **Mixed bases.** Co and Ni keep their descriptor cost (no measured law). The two cross-metal reversals of the primary
   measured basis are won by a Co catalyst against Ru on the measured law; with Co and Ni removed, the remaining
   reversals (3/19) are all Ru against Ru at a different Ru content.

## Reading

On the descriptor kinetics the laboratory leader is not the plant-cost leader in 12 of 44 ammonia comparisons; when the
laboratory points are instead extrapolated on measured rate laws fitted at other conditions, the count falls to 2–6
comparisons, mainly because most laboratory points cannot be carried to plant conditions on those laws at all. The
ammonia within-paper count therefore rests on the kinetic extrapolation, unlike the methanol count, which uses each
catalyst's own measured conversion and selectivity. Same-metal reversals (Ru against Ru) occur on both bases.
