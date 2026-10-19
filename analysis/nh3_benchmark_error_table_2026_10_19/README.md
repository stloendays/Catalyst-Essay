# NH3-FINAL-1.2 plant benchmark: error table and Fe–Ru robustness to the benchmark errors (2026-10-19)

Two questions about the 64 pre-registered industrial comparisons
(`../validation_nh3_plant_2026_10_13/`, 1.2 re-score in `nh3_1_2/`, 32/64 pass):

1. How far is the model from each industrial value? Report the typical and the maximum deviation per table and per
   physical quantity.
2. Perturb the components behind the failed items by the observed benchmark errors and re-optimise both catalysts.
   Does the Fe-first order flip?

    NH3_MODEL is forced to 1.2 inside the script.
    python run_error_table.py          # ~7.5 min, one process; writes every file below

The script asserts the canonical anchors on its own code path before it perturbs anything. Descriptor gate:
Fe 11.515784 and Ru 16.632749 USD/t, equal to `results.json` to 1e-9, at 425 °C / 105 bar / 30 °C and
450 °C / 220 bar / 30 °C. Measured kinetics: Fe 14.925644. Our cost re-implementation equals
`kinetics_swap.evaluate` to 1e-12 for Fe, Ru (benchmark, unconstrained and 100–200 bar) and supported Ru/C at 0 and
12 %/y (−3.4634 and +1.452025). Nothing in `provenance/`, the benchmark folder or `nh3_staged_converter_2026_10_12/` is
modified.

## 1. Error table

`error_table.csv` has 64 rows: metric, table, plant case, quantity, model, industrial value, unit, signed deviation,
|deviation|, tolerance rule and the registered pass/fail. The pass/fail is copied from the registered re-score, not
re-judged. How the deviation is defined:

- **Point values:** (model − industrial)/industrial in %.
- **Temperatures:** model − industrial in °C.
- **Published ranges and windows:** 0 when the model value lies inside the range; otherwise the deviation is measured
  against the nearest edge. The deviation from the range midpoint is also given.
- **V01:** model/table ratio − 1, i.e. the error of the separator vapour itself.
- **C08–C10, C12:** logical or threshold rules, so they have no numeric deviation.

"Typical" is the median |deviation| and "max" is the maximum |deviation|. The sign column says "under-prediction" or
"over-prediction" when every nonzero deviation in the group has that sign, and "mixed" otherwise.

| Table / quantity group | n | pass | typical abs. dev. (median) | max abs. dev. (item) | median signed dev. | sign | failing items |
|---|---:|---:|---:|---:|---:|---|---|
| Table A | 28 | 18 | 28.3 % | 167.5 % (A26) | -9.6 % | mixed | A01 A04 A07 A13 A14 A15 A16 A20 A22 A26 |
| Table E | 3 | 0 | 42.3 % | 77.4 % (E03) | -42.3 % | under-prediction | E01 E02 E03 |
| Table B | 20 | 5 | 42.7 %; 35.9 °C | 82.2 % (B15); 57.5 °C (B11) | -42.7 %; +18.8 °C | mixed | B01 B02 B05 B06 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 B20 |
| Table C | 12 | 9 | 0.0 %; 11.2 °C | 9.7 % (C02); 22.5 °C (C04) | +0.0 %; +11.2 °C | mixed (+4 logical) | C02 C04 C09 |
| Table V | 1 | 0 | 39.8 % | 39.8 % (V01) | -39.8 % | under-prediction | V01 |
| converter inlet NH3 | 5 | 0 | 62.9 % | 72.6 % (A04) | -62.9 % | under-prediction | A01 A04 A07 A14 A16 |
| separator vapour NH3 | 1 | 0 | 39.8 % | 39.8 % (V01) | -39.8 % | under-prediction | V01 |
| outlet / net NH3, loop states | 13 | 8 | 14.6 % | 167.5 % (A26) | +4.5 % | mixed | A13 A15 A20 A22 A26 |
| outlet NH3, converter forward runs | 2 | 2 | 7.9 % | 8.0 % (B07) | -7.9 % | under-prediction |  |
| outlet NH3, cost-optimal converter designs | 4 | 0 | 45.8 % | 49.3 % (B13) | -45.8 % | under-prediction | B10 B13 B16 B20 |
| outlet NH3, Fe optimum | 1 | 1 | 0.0 % | 0.0 % (C06) | +0.0 % | none (all inside) |  |
| converter flow and feed/make-up | 4 | 4 | 16.4 % | 23.2 % (A06) | -16.4 % | under-prediction |  |
| space velocity | 6 | 6 | 34.4 % | 57.1 % (A19) | +28.3 % | mixed |  |
| compressor power | 3 | 0 | 42.3 % | 77.4 % (E03) | -42.3 % | under-prediction | E01 E02 E03 |
| bed volume, plant conditions | 4 | 4 | 17.9 % | 40.4 % (A28) | +1.2 % | mixed |  |
| bed volume, cost-optimal designs and Fe optimum | 4 | 1 | 62.6 % | 82.2 % (B15) | -62.6 % | under-prediction | B12 B15 B18 |
| bed outlet temperature, forward runs | 4 | 0 | 25.5 °C | 35.9 °C (B05) | -7.8 °C | mixed | B01 B02 B05 B06 |
| bed-1 inlet temperature, cost-optimal designs | 3 | 0 | 54.3 °C | 57.5 °C (B11) | +54.3 °C | over-prediction | B11 B14 B17 |
| Fe optimum loop pressure | 2 | 1 | 4.8 % | 9.7 % (C02) | -4.8 % | under-prediction | C02 |
| Fe optimum temperature | 1 | 1 | 0.0 °C | 0.0 °C (C03) | +0.0 °C | none (all inside) |  |
| Fe optimum separator temperature | 1 | 0 | 22.5 °C | 22.5 °C (C04) | +22.5 °C | over-prediction | C04 |
| Fe/Ru choice and staging | 6 | 4 | 27.9 % | 55.8 % (B19) | -27.9 % | under-prediction (+4 logical) | B19 C09 |
| **All 64** | 64 | 32 | 31.7 %; 32.2 °C | 167.5 % (A26); 57.5 °C (B11) | -10.2 %; +18.8 °C | mixed (+4 logical) | 32 (listed below) |

The 32 failing items, each with its model value against the industrial value:

- **Converter inlet NH3**, model low by 45–73 %:
  - A01 Topsøe 140 bar: 1.87 vs 4.1 %
  - A04 Topsøe 220 bar: 1.04 vs 3.8 %
  - A07 Krupp-Uhde 188 bar: 1.55 vs 4.18 %
  - A14 Kellogg 150 bar: 0.73 vs 2.0 %
  - A16 Braun 150 bar: 2.20 vs 4.0 %
- **Separator vapour (V01):** 0.60 of the BASF table.
- **Outlet or net NH3, too high:**
  - A13 PFI 266 bar: +16.5 %
  - A15 Kellogg: 17.5 against 10–12 %
  - A20 Liu Kellogg: +58 %
  - A22 Topsøe 260 bar: 23.9 against 10–12.5 %
  - A26 small plant at 314 bar: 26.8 against 8–10 %
- **Compressor power, model low:** E01 −42 %, E02 −36 %, E03 −77 %.
- **Bed temperatures, forward runs:** B01 −32 °C, B02 +17 °C, B05 −36 °C, B06 +19 °C.
- **Cost-optimal all-Fe designs:**
  - outlet NH3 B10, B13, B16: −43 to −49 %
  - bed-1 inlet temperature B11, B14, B17: +50 to +58 °C above the window
  - volume per t/d B12, B15, B18: 52–82 % below the window
- **KAAP layout:** B19, Fe share 0.15 vs 0.35–0.65; B20, outlet 12.7 vs 21–21.7 %.
- **Fe optimum:** C02, 140 bar vs 155–190 bar; C04, separator at 30 °C vs −25 to 7.5 °C.
- **C09:** no Ru in the 90-bar optimum at 12 %/y.

## 2. Perturbation of the components behind the failures

Each failing group is mapped to the cost-model component that controls it. The component's error magnitude comes from
the group's |ln(model/reference)| for multiplicative components, or its |ΔT| in °C for the bed temperature:

| Component | Model parameter perturbed | Groups (items) | Typical | Max (item) |
|---|---|---|---:|---:|
| SEP | separator vapour y_sep = p_sat(T_sep)/P, multiplied (process states rebuilt) | inlet NH3 + V01 | ×2.43 | ×3.66 (A04) |
| APP | approach to equilibrium 0.8, i.e. per-pass conversion (states rebuilt) | loop outlet/net NH3 + design outlet NH3 | 0.8/1.176 | 0.8/2.675 (A26); other direction capped at 0.99 |
| COMP | fresh + recycle compression power; compressor capex re-sized (equivalent to η = 0.75/k; checked against a rebuild to 1e-12) | E01–E03 | ×1.73 | ×4.43 (E03) |
| KIN | catalyst amount per state (rate ÷ f), Fe only or all catalysts | bed volume, both groups | ×1.41 | ×5.61 (B15); ×1.68 (A28) for the plant-condition beds alone |
| TBED | effective bed temperature of the rate law (bed at T + ΔT; loop state unchanged) | bed outlet T (forward) + design bed-1 inlet T | ±35.9 °C | ±57.5 °C (B11) |

**How each case was run**

- Every component is applied in both directions.
- Both catalysts are re-optimised over the full perturbed state library, keeping the 90 m³ cap.
- The descriptor gate uses the frozen two-point interpolation. F_CAL is fixed at 74,351.6.
- The measured-kinetics comparison uses plug flow and source rates.
- SEP and APP rebuild the process states inside the frozen harness. The harness is subclassed in memory; no file is
  changed.
- COMP, KIN and TBED are cost-term or kinetics re-evaluations on the state library.

**What is not perturbed, and why**

- **C02, C04, C11 and C12:** these are outputs of the optimisation, not model inputs.
- **C04, the separator temperature:** no refrigeration power was benchmarked, so there is no error to apply. The SEP
  perturbation changes the value of chilling.
- **C09, B19 and B20:** these are the financing-dependent staging decisions of `converter.py`, which the gate does not
  use. They are the Fe/Ru decision itself, not a physical error.
- **Space velocity and flows:** they pass, and their error is the bed-volume and approach error already applied.

Gaps are Ru − Fe in USD/t at the two optima. A positive gap means Fe first. **Bold** marks a flip. The "measured" column
gives Fe at benchmark accounting and the Ru benchmark formulation, unconstrained.

| Perturbation | setting | Fe / Ru, descriptor | Ru − Fe | Os − Fe | Fe / Ru, measured | Ru − Fe | Ru − Fe, 100–200 bar | Ru/C − Fe, 0 %/y | Ru/C − Fe, 12 %/y |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | – | 11.52 / 16.63 | +5.12 | +8.23 | 14.93 / 33.07 | +18.14 | +23.34 | -3.46 | +1.45 |
| SEP + typical | y_sep ×2.43 | 14.27 / 19.79 | +5.52 | +8.64 | 17.75 / 33.36 | +15.61 | +24.17 | -3.30 | +0.91 |
| SEP - typical | y_sep ×0.411 | 9.63 / 13.93 | +4.30 | +6.92 | 12.24 / 32.84 | +20.60 | +22.96 | -2.74 | +1.81 |
| SEP + max | y_sep ×3.66 | 15.49 / 21.11 | +5.62 | +8.86 | 19.39 / 33.57 | +14.19 | +24.20 | -3.58 | +0.75 |
| SEP - max | y_sep ×0.274 | 8.95 / 12.67 | +3.72 | +6.37 | 11.38 / 32.72 | +21.35 | +23.10 | -2.94 | +1.92 |
| APP + typical | approach 0.68 | 11.81 / 16.98 | +5.17 | +8.31 | 14.55 / 31.12 | +16.57 | +19.96 | -2.94 | +1.39 |
| APP - typical | approach 0.941 | 11.22 / 16.27 | +5.05 | +8.08 | 16.51 / 36.53 | +20.03 | +32.60 | -4.85 | +1.43 |
| APP + max | approach 0.299 | 13.90 / 18.27 | +4.36 | +7.41 | 15.12 / 27.34 | +12.22 | +13.95 | -2.05 | +1.15 |
| APP - max | approach 0.99 | 11.14 / 16.15 | +5.02 | +8.00 | 19.48 / 41.12 | +21.64 | +47.12 | -7.40 | +0.96 |
| COMP + typical | power ×1.73 | 18.86 / 25.25 | +6.38 | +9.67 | 22.65 / 46.99 | +24.34 | +25.87 | -4.36 | +2.02 |
| COMP - typical | power ×0.577 | 7.18 / 10.19 | +3.01 | +5.08 | 9.81 / 22.71 | +12.90 | +22.59 | -2.54 | +1.26 |
| COMP + max | power ×4.43 | 39.08 / 44.65 | +5.57 | +11.13 | 44.83 / 76.90 | +32.07 | +33.78 | -12.96 | +2.23 |
| COMP - max | power ×0.226 | 3.12 / 4.46 | +1.34 | +2.11 | 5.18 / 14.03 | +8.85 | +22.25 | -1.90 | +0.90 |
| KIN_Fe + typical | Fe amount ×1.41 | 11.79 / 16.63 | +4.84 | +7.95 | 16.14 / 33.07 | +16.93 | +22.13 | -4.69 | +0.20 |
| KIN_Fe - typical | Fe amount ×0.708 | 11.20 / 16.63 | +5.43 | +8.54 | 14.02 / 33.07 | +19.05 | +24.25 | -2.55 | +2.39 |
| KIN_Fe + max_plant_sizing | Fe amount ×1.68 | 11.90 / 16.63 | +4.74 | +7.85 | 16.89 / 33.07 | +16.18 | +21.37 | -5.45 | **-0.57** |
| KIN_Fe - max_plant_sizing | Fe amount ×0.596 | 11.08 / 16.63 | +5.55 | +8.66 | 13.63 / 33.07 | +19.44 | +24.63 | -2.17 | +2.77 |
| KIN_Fe + max | Fe amount ×5.61 | 13.43 / 16.63 | +3.21 | +6.32 | 26.96 / 33.07 | +6.11 | +11.30 | -15.53 | **-10.70** |
| KIN_Fe - max | Fe amount ×0.178 | 10.25 / 16.63 | +6.38 | +9.50 | 11.55 / 33.07 | +21.52 | +26.72 | -0.07 | +4.91 |
| KIN_all + typical | all amount ×1.41 | 11.79 / 17.30 | +5.51 | +8.56 | 16.14 / 36.72 | +20.58 | +31.23 | -4.26 | +1.73 |
| KIN_all - typical | all amount ×0.708 | 11.20 / 16.10 | +4.90 | +7.96 | 14.02 / 29.29 | +15.27 | +17.48 | -2.85 | +1.18 |
| KIN_all + max_plant_sizing | all amount ×1.68 | 11.90 / 17.65 | +5.76 | +8.77 | 16.89 / 39.04 | +22.14 | +36.20 | -4.74 | +1.87 |
| KIN_all - max_plant_sizing | all amount ×0.596 | 11.08 / 15.86 | +4.77 | +7.79 | 13.63 / 27.62 | +13.99 | +15.14 | -2.71 | +1.06 |
| KIN_all + max | all amount ×5.61 | 13.43 / 19.68 | +6.26 | +9.99 | 26.96 / 69.55 | +42.59 | +105.35 | -12.64 | +2.24 |
| KIN_all - max | all amount ×0.178 | 10.25 / 14.31 | +4.06 | +6.37 | 11.55 / 18.41 | +6.87 | +6.87 | -1.95 | +0.89 |
| TBED + typical | bed +35.9 °C | 10.50 / 14.91 | +4.41 | +6.92 | 18.39 / 26.63 | +8.24 | +25.81 | -3.39 | **-0.10** |
| TBED - typical | bed -35.9 °C | 12.88 / 19.39 | +6.51 | +10.26 | 15.80 / 47.79 | +31.99 | +51.02 | -3.72 | +4.47 |
| TBED + max | bed +57.5 °C | 10.04 / 14.18 | +4.13 | +6.13 | 21.66 / 26.00 | +4.35 | +inf (no feasible Ru state) | -3.14 | **-0.54** |
| TBED - max | bed -57.5 °C | 15.43 / 21.33 | +5.90 | +10.66 | 17.32 / 69.54 | +52.22 | +92.09 | -4.61 | +8.84 |

**Joint perturbations**

- **"Joint Ru-favouring":** every component at the same magnitude, each in the direction that individually lowered
  that comparison's gap most. For KIN this is the more Ru-favouring of the Fe-only and all-catalyst forms.
- **"Worst corner":** the lowest gap over all 2⁵ sign combinations × {Fe-only, all-catalyst KIN}, i.e. 64 corners per
  magnitude.
- **"Neither feasible":** the corner has no state for either catalyst. This happens with approach 0.99 and a bed hotter
  by 57.5 °C, where the loop outlet lies past the rate law's equilibrium.

| Comparison | baseline | single flips | joint Ru-favouring, typical | joint Ru-favouring, max | worst corner, typical | worst corner, max | corners flipped, typical / max |
|---|---:|---|---:|---:|---:|---:|---:|
| descriptor Ru − Fe | +5.12 | 0/28 | +2.36 | +0.26 | +2.21 | −40.14 | 0/64 / 18/64 |
| descriptor Os − Fe | +8.23 | 0/28 | +3.68 | +0.70 | +3.56 | −33.40 | 0/64 / 12/64 |
| measured benchmark Ru − Fe (unconstrained) | +18.14 | 0/28 | +5.20 | +0.53 | +3.51 | +0.53 | 0/64 / 0/64 (+16 neither feasible) |
| measured benchmark Ru − Fe (Ru 100–200 bar) | +23.34 | 0/28 | +6.98 | +10.60 | +6.98 | +1.07 | 0/64 / 0/64 (+16 neither feasible) |
| measured supported Ru/C − Fe (0 %/y) | −3.46 | 0/28 | −9.29 | −122.02 | −12.85 | −129.72 | 0/64 / 12/64 to Fe-first (+16) |
| measured supported Ru/C − Fe (12 %/y) | +1.45 | 4/28 | **−0.59** | neither feasible | −9.80 | −110.76 | 22/64 / 13/64 (+16) |

The joint Ru-favouring cases that do not flip end at these Fe and Ru optima:

- **Descriptor, max:** Fe 3.10 at 425 °C / 95 bar / 30 °C; Ru 3.35 at 450 °C / 135 bar. Both costs are low because
  compression power is ×0.226.
- **Measured benchmark, max:** Fe 6.41 vs Ru 6.94, both at 575 bar.

Every one of the 18 descriptor corners that flip at max magnitude contains Fe amount ×5.61 (B15). Sixteen of the 18 also
contain bed −57.5 °C. In the worst corner (with compression ×4.43), the Fe bed reaches the 90 m³ cap at 275 bar and Fe
costs 81.1 against Ru 41.0 at 45 bar.

## Verdict

- **Descriptor-kinetics Fe vs Ru, the paper's gate, and Fe vs Os.**
  - No single component flips the order. That covers each of the five failure groups, at the typical and at the maximum
    observed error, in both directions (28 cases). The smallest margin is +1.34 USD/t, with compression power ×0.226.
  - The joint Ru-favouring perturbation does not flip it either. The margin is +2.36 USD/t at typical errors and
    +0.26 USD/t at maximum errors.
  - None of the 64 sign corners flips at typical errors.
  - At maximum errors, 18 of 64 corners flip. All of them need the Fe bed ×5.61, which comes from the cost-optimal design
    volume B15 rather than a measured bed. With the plant-condition bed error alone (×1.68, A28), the gap stays at +4.74.
- **Measured kinetics, Fe (Dyson–Simon) vs Ru benchmark (Rossetti Ru/C).**
  - No flip in any single case or any of the 128 corners.
  - Smallest margins: +0.53 USD/t unconstrained and +1.07 USD/t in the 100–200 bar window.
- **Supported Ru/C at 12 %/y (baseline +1.45 USD/t). The Fe-first order is not robust to the benchmark errors:**
  - Typical bed-temperature error +35.9 °C: −0.10.
  - Plant-condition Fe-bed error ×1.68: −0.57.
  - Joint typical: −0.59.
  - Worst typical corner: −9.80.
  - The same comparison at 0 %/y is already Ru/C-first (−3.46) and stays so in every single perturbation.
- **What can be claimed.** The Fe-over-Ru ranking with descriptor kinetics and with measured benchmark kinetics is robust
  to every observed benchmark error applied alone and to all errors applied jointly in the Ru-favouring direction. The
  financed supported-Ru/C margin of 1.45 USD/t is smaller than the cost effect of the typical benchmark error.

## Files

| File | Content |
|---|---|
| `run_error_table.py` | regenerates every file in this folder; asserts the anchors first |
| `error_table.csv` | 64 rows: deviation, basis, unit, rule, registered pass |
| `error_summary.csv` | per table (A, E, B, C, V), per quantity group, all 64: n, pass, typical and max \|dev\|, median signed, sign, failing ids |
| `perturbation_results.csv` | 157 scenarios × 6 comparisons: parameters, Fe and Ru cost, optimum (T / P / T_sep / V), gap, baseline gap, first, flip |
| `perturbation_summary.json` | magnitudes; per comparison: single-perturbation gaps and Ru-favouring direction, joint Ru-favouring, worst corner, flip counts |
| `run_stdout.txt` | console output of the run |

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe` (CPython 3.12). Runtime 434 s on one process.
