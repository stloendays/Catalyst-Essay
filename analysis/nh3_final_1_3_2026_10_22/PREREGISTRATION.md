# NH3-FINAL-1.3: separator VLE and compression from sourced data — preregistration (2026-10-22)

Committed before any 1.3 result is computed. NH3-FINAL-1.2 (`provenance/nh3_final_1_2`) is not edited; 1.3 is a
subclass of its harness that changes two process functions and nothing else (kinetics, catalyst, costs, grids,
approach to equilibrium, refrigeration, CAPEX correlations unchanged).

## Why

The 64-item industrial benchmark of 1.2 passes 32 items; every converter-inlet NH₃ item fails (typically −63 %), the
separator-vapour item fails (−40 %) and all three compression-power items fail (−36 %, −42 %, −77 %). 1.2 sets the
separator vapour to p_sat(T_sep)/P (pure liquid NH₃, ideal gas), compresses fresh gas isothermally at 298 K with
efficiency 0.75 and charges the recycle a fixed 3-bar rise. PR-based VLE was tried and failed its gate
(`analysis/nh3_pr_vle_compression_v0`).

## Changes

1. **Separator vapour.** y_NH₃ = E(T_sep, P) · p_sat(T_sep)/P, with ln E interpolated bilinearly in the measured BASF
   saturation table (Appl 2011, Ullmann's, Table 5; NH₃ in 3:1 H₂/N₂ over liquid NH₃; 64 points, −30 to +40 °C, 5–100 MPa;
   rows `APPL11_A1 Table 5` of `analysis/validation_nh3_plant_2026_10_13/reference_values.csv`). Below 5 MPa ln E is
   interpolated linearly to its ideal limit E = 1 at P = 0; below −30 °C the −30 °C row is used. The table is measured
   equilibrium data and is used as data, not fitted.
2. **Fresh-gas compression.** From 30 bar (unchanged) to P in N equal-ratio polytropic stages with intercooling to
   40 °C: N = ceil(ln(P/30)/ln 2.2), W = N R T_ic (m/(m−1)) (r^((m−1)/m) − 1) per mol, (m−1)/m = (κ−1)/(κ η_p),
   κ = 1.40, η_p = 0.78. Electricity at the 1.2 price; compressor CAPEX from the new duty with the 1.2 correlation.
3. **Recycle compression.** One polytropic stage at 40 °C suction across the 9.2-bar loop pressure drop of the
   1,500 t/d Krupp–Uhde flowsheet (Appl 2011, the source of the 1.2 recycle-rise sensitivity T1), same η_p and κ.
4. **F_CAL** recalibrated on the 1.2 definition: Fe needs the 1.2 Fe bed at the calibration state (400 °C, 80 bar,
   −35 °C), F_CAL(1.3) = F_CAL(1.2) · 10^(logTOF_Fe,1.2 − logTOF_Fe,1.3) at that state.

Not changed (reported as remaining differences): inert gases and purge are still absent from the loop; real-gas
compressibility is not applied to compression work.

## Gates (judged before any economic result is read)

- G1 VLE hold-out: Uhde Figure 57 first-separator vapour (21 °C, 18.02 MPa, 8.51 mol% NH₃) and refrigerated
  second-separator vapour (0 °C, 17.88 MPa, 4.18 mol%) within ±20 %.
- G2 compression: E01, E02, E03 of the registered benchmark within ±30 % (their registered tolerance).
- G3 the registered state-level items (Table A, E, V) are re-scored with the registered rules; the count is reported
  whatever it is.

## Reported (whatever the direction)

Descriptor model: Fe, Ru, Os costs and optima, order, Fe–Ru gap and its decomposition, Ru price parity, Ru activity
multiple for parity. Measured rate laws (Keestra Fe, Rossetti Ru/C, each in its fitted pressure range): Fe and Ru/C
costs, Ru/C break-even financing rate on own optima and in the KAAP-type loop, saving at the 2.10 %/y reference rate.
