# NH3-FINAL-1.1 with the experimental NH₃ equilibrium in the plant loop (sensitivity)

The frozen model's NH₃ formation free energy lies 0.065 eV per NH₃ above the Gillespie–Beattie value at 350–500 °C
(Methods correct this only for the laboratory mapping). In the plant loop it puts the per-pass conversion of the KAAP-type
state (90 bar, −20 °C separator, 425 °C) at 8.5%. `nh3_equilibrium_sensitivity.py` shifts the NH₃ gas free energy to the
experimental value at every temperature (loop equilibrium and microkinetic NH₃ steps together), redoes the fused-iron
calibration on its own definition (same Fe bed at the calibration state, 400 °C, 80 bar, −35 °C: F_CAL 89,806 → 75,905),
and reoptimizes all 15 metals over the corrected process states (14,498 feasible). Frozen anchors are reproduced first.

| | Frozen | Corrected equilibrium, F_CAL fixed | Corrected, recalibrated |
|---|---|---|---|
| Activity order (top 3) | Ru > Os > Fe | Ru > Os > Fe | Ru > Os > Fe |
| Economic order (top 3) | Fe > Ru > Os | Fe > Ru > Os | Fe > Ru > Os |
| Spearman, activity vs cost (feasible) | −0.50 | −0.50 | −0.50 |
| Fe / Ru / Os (USD t⁻¹) | 15.29 / 22.03 / 25.83 | 11.66 / 17.21 / 20.68 | 11.82 / 17.53 / 21.02 |
| Fe optimum | 425 °C, 180 bar, 30 °C | 425 °C, 110 bar, 30 °C | 425 °C, 110 bar, 30 °C |
| Supported Ru/C (u = 11, r = 95.55%, 8 wt%, 490 kg m⁻³), best | 15.74 (+0.44 vs Fe) | 11.82 (+0.16) | 12.01 (+0.19) |
| KAAP loop: supported Ru/C vs Fe | 18.73 vs 19.07 | 16.42 vs 17.04 | 16.46 vs 17.08 |
| KAAP per-pass conversion at 425 °C | 8.5% | 22.1% | 22.1% |

The rankings and the direction of every Ru/Fe comparison are unchanged; absolute costs fall by about a quarter and the
Fe optimum moves from 180 to 110 bar. The supported-Ru gap to Fe narrows from 0.44 to about 0.2 US dollars per tonne in
the global optimum.

    NH3_HARNESS=<harness root> python analysis/verify_2026_10_12_nh3_equilibrium/nh3_equilibrium_sensitivity.py
