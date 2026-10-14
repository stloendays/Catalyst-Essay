# NH3 loop reconciliation (2026-10-14) — results of the preregistered tests T1–T5

Preregistration: `PREREGISTRATION.md` (committed before any computation). Every number below is read from `outputs/`. Frozen NH3-FINAL-1.2 numbers (Fe 11.516 / Ru 16.633 / Os 19.747 USD/t; 32/64) are unchanged; everything here is a labelled sensitivity.

Upstream reruns (unchanged code): #93 Fe 47.245 / Ru 49.484; #94 Fe 41.634 / Ru 82.636 USD/t; gates all PASS.

## T1. Canonical recycle-rise sensitivity (NH3-FINAL-1.2, descriptor kinetics, 15 metals)

Replay gate at 3.0 bar: PASS (Fe/Ru/Os max |Δ| 0.0e+00 USD/t, parity |Δ| 0.0e+00). 14,510 states in every run.

| Recycle rise (bar) | Fe USD/t (T, P, Tsep) | Ru USD/t (T, P, Tsep) | Os USD/t (T, P, Tsep) | Feasible ranking | Ru − Fe | Ru − Os | Ru parity multiple | Spearman vs frozen (censored / raw) | Activity–economics Spearman (raw / censored) |
|---:|---|---|---|---|---:|---:|---:|---|---|
| 3.0 | 11.516 (425 °C, 105 bar, 30 °C) | 16.633 (450 °C, 220 bar, 30 °C) | 19.747 (450 °C, 340 bar, 30 °C) | Fe > Ru > Os | +5.117 | -3.114 | 114.67× | 1.000 / 1.000 | 0.911 / 0.684 |
| 6.0 | 12.541 (425 °C, 110 bar, 30 °C) | 16.878 (450 °C, 220 bar, 30 °C) | 19.856 (450 °C, 345 bar, 30 °C) | Fe > Ru > Os | +4.337 | -2.978 | 113.15× | 1.000 / 1.000 | 0.911 / 0.684 |
| 9.2 | 13.595 (425 °C, 110 bar, 30 °C) | 17.129 (450 °C, 220 bar, 30 °C) | 19.966 (450 °C, 345 bar, 30 °C) | Fe > Ru > Os | +3.534 | -2.837 | 67.35× | 1.000 / 1.000 | 0.911 / 0.684 |

Metals with a state within the 90 m³ cap: 3.0 bar 3/15, 6.0 bar 3/15, 9.2 bar 3/15; unconstrained 15-metal economic order identical to the 3-bar replay: True (`outputs/t1_metals.csv`). Only the recycle-compression electricity and its CAPEX change between runs (process states asserted identical).

## T2. Matched-pressure Fe vs Ru/C in the closed loop

Isothermal measured-rate beds (Fe KM1; promoted 3.2 wt% Ru/C, 590 kg/m³), SI-S27 two-flash loop, 1500 t/d, ≤ 90 m³, ≤ 15 mol% inlet inerts; each catalyst reoptimises T, X, cold T2 and purge on the preregistered grid. Every Fe row is outside the Dyson–Simon pressure fit (149–309 atm); Ru/C rows above 100 bar are outside the Rossetti fit (50–100 bar).

| P bar | Basis | Fe USD/t (T, X, T2, purge, bed m³) | Ru/C USD/t (T, X, T2, purge, bed m³) | Ru − Fe | excess feed | of which purge gas / dissolved / NH₃ in purge | utilities | inventory | reactor | compressor | Ru/C finance crossover 0–12 %/y |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---|
| 90 | B94 | 93.529 (450, 0.08, -20, 0.0075, 80.4) | 90.591 (425, 0.12, -10, 0.01, 44.4) | -2.938 | -4.199 | -7.48 / +0.31 / +2.97 | -7.666 | +10.391 | -0.745 | -0.720 | none: Ru/C cheaper on 0–12% (Ru−Fe -12.66 at 0%) |
| 90 | B93 | 81.763 (450, 0.08, -20, 0.0075, 80.4) | 79.557 (425, 0.12, -10, 0.01, 44.4) | -2.206 | -3.169 | -5.67 / +0.27 / +2.23 | -7.666 | +10.094 | -0.745 | -0.720 | none: Ru/C cheaper on 0–12% (Ru−Fe -12.21 at 0%) |
| 100 | B94 | 92.766 (450, 0.08, -20, 0.0075, 59.1) | 82.636 (450, 0.12, -20, 0.01, 16.6) | -10.130 | -6.416 | -7.58 / +0.09 / +1.07 | -5.749 | +3.655 | -0.890 | -0.731 | none: Ru/C cheaper on 0–12% (Ru−Fe -13.69 at 0%) |
| 100 | B93 | 80.653 (450, 0.1, -20, 0.01, 69.3) | 72.385 (450, 0.12, -20, 0.01, 16.6) | -8.268 | -7.929 | -7.56 / +0.15 / -0.51 | -2.455 | +3.462 | -1.127 | -0.218 | none: Ru/C cheaper on 0–12% (Ru−Fe -11.90 at 0%) |
| 120 | B94 | 80.550 (450, 0.12, -20, 0.01, 55.1) | 76.315 (425, 0.2, -10, 0.015, 44.4) | -4.234 | -6.031 | -7.91 / +0.89 / +0.99 | -7.971 | +10.591 | -0.284 | -0.539 | none: Ru/C cheaper on 0–12% (Ru−Fe -14.41 at 0%) |
| 120 | B93 | 70.460 (450, 0.12, -20, 0.01, 55.1) | 67.407 (425, 0.2, -10, 0.015, 44.4) | -3.052 | -4.551 | -6.06 / +0.76 / +0.74 | -7.971 | +10.293 | -0.284 | -0.539 | none: Ru/C cheaper on 0–12% (Ru−Fe -14.04 at 0%) |
| 140 | B94 | 68.898 (445, 0.2, -20, 0.015, 88.0) | 66.874 (425, 0.225, -10, 0.015, 38.3) | -2.025 | -5.647 | -5.05 / +0.77 / -1.37 | -3.476 | +8.797 | -1.645 | -0.054 | none: Ru/C cheaper on 0–12% (Ru−Fe -15.07 at 0%) |
| 140 | B93 | 60.554 (445, 0.2, -20, 0.015, 88.0) | 59.659 (425, 0.225, -10, 0.015, 38.3) | -0.896 | -4.261 | -3.91 / +0.68 / -1.03 | -3.476 | +8.541 | -1.645 | -0.054 | none: Ru/C cheaper on 0–12% (Ru−Fe -13.70 at 0%) |

Counts (cold states, unresolved, eligible Fe / Ru/C designs): 90 bar 144, 8, 16 / 114; 100 bar 144, 8, 37 / 144; 120 bar 144, 3, 96 / 216; 140 bar 144, 3, 161 / 263. Unresolved states (20 s numerical budget of the upstream worker or non-converged fixed point) are listed in `outputs/t2.json`.

## T3. Model bridge

Gates: manuscript optima recomputed Fe_optimum_14.925644 PASS, RuC_minus_Fe_0pct_-3.4634 PASS, RuC_minus_Fe_12pct_+1.452 PASS; point costs reproduce the kinetics-swap and #93/#94 optima to 0.0e+00 USD/t.

Ru − Fe (USD/t) of each pair in both models. Canonical: 1.2 state at that T, P, Tsep (= closed-loop cold T2), measured kinetics, plug flow, 8 wt% Ru/C at 490 kg/m³, 25-y cash flow. Closed loop: #94 / #93 designs; at the manuscript points T and P fixed, X, T2, purge reoptimised.

| Pair (Fe point; Ru/C point) | canonical r 95.55% 12% rise 3 | canonical r 90% 12% rise 3 | canonical r 90% 12% rise 9.2 | canonical r 95.55% 0% rise 3 | closed B94 | closed B93 |
|---|---:|---:|---:|---:|---:|---:|
| a12_manuscript_12pct: Fe 450 °C/140 bar; Ru/C 450 °C/150 bar | +1.452 | +1.556 | +1.304 | -1.976 | -11.649 | -10.251 |
| a0_manuscript_0pct: Fe 450 °C/140 bar; Ru/C 425 °C/105 bar | +8.297 | +8.645 | +9.580 | -3.463 | +7.430 | +6.324 |
| b94_closed_source_windows: Fe 425 °C/285 bar; Ru/C 450 °C/100 bar | -1.340 | -1.251 | +0.392 | -4.323 | +41.001 | +33.000 |
| c93_closed_220bar: Fe 425 °C/220 bar; Ru/C 425 °C/220 bar | +2.360 | +2.488 | +2.488 | -1.926 | +2.403 | +2.239 |

Waterfall from the manuscript +1.45 (S0) to #94 +41.0 (S4), Ru − Fe change by category (USD/t):

| Step | total | inventory | reactor | utilities | compressor capital | excess feed (closed-loop only) | purge gas | dissolved gas | NH₃ in purge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S0 -> S1 | -2.792 | -0.319 | +0.025 | -0.598 | -1.900 | +0.000 | +0.000 | +0.000 | +0.000 |
| S1 -> S2 | +0.089 | +0.089 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| S2 -> S3 | +1.643 | +0.000 | +0.000 | +1.244 | +0.399 | +0.000 | +0.000 | +0.000 | +0.000 |
| S3 -> S4 | +40.610 | +0.482 | -2.190 | +9.941 | +0.218 | +32.159 | +30.737 | -6.207 | +7.629 |
| order 1: econ+rise at pair a (S0 -> S0') | -0.148 | +0.104 | +0.000 | -0.193 | -0.059 | +0.000 | +0.000 | +0.000 | +0.000 |
| order 1: pair effect, canonical (S0' -> S3) | -0.913 | -0.334 | +0.025 | +0.839 | -1.442 | +0.000 | +0.000 | +0.000 | +0.000 |
| order 1: model effect at pair b (S3 -> S4) | +40.610 | +0.482 | -2.190 | +9.941 | +0.218 | +32.159 | +30.737 | -6.207 | +7.629 |
| order 2: model effect at pair a (S0' -> S5) | -12.953 | +1.410 | +1.545 | -9.594 | -0.049 | -6.265 | -7.426 | +1.712 | -0.550 |
| order 2: pair effect, closed loop (S5 -> S4) | +52.650 | -1.263 | -3.710 | +20.374 | -1.175 | +38.424 | +38.164 | -7.919 | +8.179 |

Levels: S0 canonical pair a12, r 95.55%, 12%, rise 3 bar +1.452; S1 canonical pair b94 -1.340; S2 canonical pair b94, r 90% -1.251; S3 canonical pair b94, r 90%, rise 9.2 bar +0.392; S4 closed loop pair b94, B94 +41.001; S5 closed loop pair a12, B94 -11.649; S0' canonical pair a12, r 90%, rise 9.2 bar +1.304.

S4 − S0 by category: excess_feed +32.159, utilities +10.587, reactor -2.165, compressor_capital -1.283, inventory +0.252, hot_duty +0.000.

## T4. KAAP-type staged converter in the closed loop, 90 bar (simplified series-PFR)

Three adiabatic beds, interbed cooling to one common inlet T (350 °C to T_max − 1), Fe ≤ 530 °C, Ru/C ≤ 460 °C, closed-loop rate laws and formulation, 64 eligible 90-bar cold states (8 unresolved, 72 above 15% inerts), 319 optimised designs.

| Basis | Ru finance %/y | all-Fe | best Fe-first (pattern, Ru/C share) | all-Ru/C | best Ru/C-first | winner (Ru/C volume share) | winner total bed m³ | Fe-first − all-Fe |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| B94 | 0 | 93.184 | 80.860 (FRR, 1.00) | 80.617 | 80.860 | all-Ru/C RRR (1.00) | 43.7 | -12.324 |
| B94 | 1 | 93.196 | 81.763 (FRR, 1.00) | 81.419 | 81.763 | all-Ru/C RRR (1.00) | 43.7 | -11.434 |
| B94 | 2 | 93.209 | 82.670 (FRR, 1.00) | 82.224 | 82.668 | all-Ru/C RRR (1.00) | 43.7 | -10.540 |
| B94 | 3 | 93.224 | 83.543 (FRR, 0.44) | 83.030 | 83.533 | all-Ru/C RRR (1.00) | 43.7 | -9.681 |
| B94 | 4 | 93.239 | 84.200 (FRR, 0.38) | 83.840 | 84.256 | all-Ru/C RRR (1.00) | 43.7 | -9.039 |
| B94 | 5 | 93.254 | 84.844 (FRR, 0.38) | 84.651 | 84.922 | all-Ru/C RRR (1.00) | 43.7 | -8.410 |
| B94 | 6 | 93.271 | 85.491 (FRR, 0.38) | 85.465 | 85.577 | all-Ru/C RRR (1.00) | 43.7 | -7.780 |
| B94 | 7 | 93.289 | 86.140 (FRR, 0.38) | 86.281 | 86.239 | Fe-first FRR (0.38) | 90.0 | -7.149 |
| B94 | 8 | 93.307 | 86.792 (FRR, 0.38) | 87.100 | 86.903 | Fe-first FRR (0.38) | 90.0 | -6.515 |
| B94 | 9 | 93.326 | 87.446 (FRR, 0.38) | 87.920 | 87.573 | Fe-first FRR (0.38) | 90.0 | -5.880 |
| B94 | 10 | 93.347 | 88.103 (FRR, 0.38) | 88.743 | 88.238 | Fe-first FRR (0.38) | 90.0 | -5.244 |
| B94 | 11 | 93.367 | 88.761 (FRR, 0.38) | 89.568 | 88.909 | Fe-first FRR (0.38) | 90.0 | -4.607 |
| B94 | 12 | 93.389 | 89.421 (FRR, 0.38) | 90.395 | 89.582 | Fe-first FRR (0.38) | 90.0 | -3.968 |
| B93 | 0 | 81.417 | 69.483 (FRR, 1.00) | 69.312 | 69.483 | all-Ru/C RRR (1.00) | 43.7 | -11.934 |
| B93 | 1 | 81.430 | 70.420 (FRR, 1.00) | 70.144 | 70.420 | all-Ru/C RRR (1.00) | 43.7 | -11.010 |
| B93 | 2 | 81.443 | 71.357 (FRR, 1.00) | 70.977 | 71.357 | all-Ru/C RRR (1.00) | 43.7 | -10.086 |
| B93 | 3 | 81.457 | 72.296 (FRR, 1.00) | 71.811 | 72.296 | all-Ru/C RRR (1.00) | 43.7 | -9.161 |
| B93 | 4 | 81.472 | 73.104 (FRR, 0.40) | 72.646 | 73.127 | all-Ru/C RRR (1.00) | 43.7 | -8.369 |
| B93 | 5 | 81.488 | 73.771 (FRR, 0.38) | 73.482 | 73.838 | all-Ru/C RRR (1.00) | 43.7 | -7.717 |
| B93 | 6 | 81.505 | 74.436 (FRR, 0.38) | 74.320 | 74.516 | all-Ru/C RRR (1.00) | 43.7 | -7.069 |
| B93 | 7 | 81.522 | 75.102 (FRR, 0.38) | 75.158 | 75.195 | Fe-first FRR (0.38) | 90.0 | -6.420 |
| B93 | 8 | 81.541 | 75.771 (FRR, 0.38) | 75.998 | 75.876 | Fe-first FRR (0.38) | 90.0 | -5.770 |
| B93 | 9 | 81.560 | 76.440 (FRR, 0.38) | 76.838 | 76.558 | Fe-first FRR (0.38) | 90.0 | -5.120 |
| B93 | 10 | 81.580 | 77.111 (FRR, 0.38) | 77.680 | 77.242 | Fe-first FRR (0.38) | 90.0 | -4.469 |
| B93 | 11 | 81.601 | 77.784 (FRR, 0.38) | 78.522 | 77.927 | Fe-first FRR (0.38) | 90.0 | -3.817 |
| B93 | 12 | 81.622 | 78.457 (FRR, 0.38) | 79.366 | 78.613 | Fe-first FRR (0.38) | 90.0 | -3.166 |

Envelope-derived winners (0.01 %-point grid): B94: all-Ru/C 0.00–6.15%, Fe-first 6.16–12.00%; B93: all-Ru/C 0.00–6.67%, Fe-first 6.68–12.00%.

## T5. Industrial plausibility (sources in the repository only)

Source: docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md (table rows 'KAAP catalyst', 'Recycle compression', 'Refrigeration'). Cost comparison: skipped: no numerical KAAP/conventional cost difference in docs/ or data/.

| Configuration (B94) | P bar | decision USD/t | recycle kWh/t | refrigeration kWh/t | fresh compression kWh/t | loop electricity GJ/t |
|---|---:|---:|---:|---:|---:|---:|
| isothermal all-Fe (T2) | 100 | 92.766 | 114.1 | 375.0 | 133.5 | 2.241 |
| isothermal all-Ru/C (T2) | 100 | 82.636 | 75.8 | 299.7 | 132.2 | 1.828 |
| isothermal all-Fe (T2) | 140 | 68.898 | 31.6 | 193.8 | 174.8 | 1.441 |
| isothermal all-Ru/C (T2) | 140 | 66.874 | 29.1 | 128.3 | 173.2 | 1.191 |
| KAAP-type 90 bar optimum at 12%/y B94 (FRR, Fe-first) | 90 | 89.421 | 90.2 | 261.7 | 118.6 | 1.693 |
| adiabatic all-Fe 90 bar (FFF), 12%/y B94 | 90 | 93.389 | 127.9 | 376.5 | 119.4 | 2.245 |
| adiabatic Fe-first 90 bar (FRR), 12%/y B94 | 90 | 89.421 | 90.2 | 261.7 | 118.6 | 1.693 |
| isothermal all-Fe (#93 grid) | 160 | 91.168 | 45.0 | 148.0 | 199.6 | 1.413 |
| isothermal all-Fe (#93 grid) | 188 | 65.326 | 25.9 | 88.3 | 213.7 | 1.181 |
| isothermal all-Fe (#93 grid) | 220 | 52.258 | 15.5 | 53.9 | 229.4 | 1.076 |

Best conventional all-Fe (220 bar) minus KAAP-type 90-bar optimum: -0.618 GJ/t of loop electricity, against a published KAAP saving of +1.17 GJ/t (same sign: False; ratio -0.53). ZA-5 reference: recycle 21.5 kWh/t (10 MPa) – 17.5 (30 MPa), refrigeration 22.6 – 13.4 kWh/t.

## Provenance

Repository head at run: `620140b4e603616689c8884df9b9e1c2400e08eb`; Python 3.12.14, NumPy 2.3.5, SciPy 1.18.0. Upstream git blob hashes: `outputs/provenance.json`.

## Rerun

    pip install numpy==2.3.5 scipy==1.18.0 pyyaml openpyxl pytest
    python -m pytest analysis/nh3_loop_reconciliation_2026_10_14
    python analysis/nh3_loop_reconciliation_2026_10_14/run_all.py --stage all --workers 4

CI: `.github/workflows/nh3-loop-reconciliation.yml` reruns every stage into a fresh directory and runs `check_regression.py` against `outputs/`.
