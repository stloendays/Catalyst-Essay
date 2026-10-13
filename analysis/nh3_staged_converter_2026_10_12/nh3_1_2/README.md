# Measured Fe and Ru/C rate laws on NH3-FINAL-1.2 — kinetics swap and staged converter (2026-10-13)

The analysis of the parent folder run on NH3-FINAL-1.2 (`provenance/nh3_final_1_2/README.md`, run
`nh3_final_1_2_20261013`): Gillespie–Beattie NH₃ formation and Newton–Cooper fugacities in the loop equilibrium and the
microkinetics, F_CAL 74,351.6, 14,510 process states. Same file names as the 1.1 outputs one level up.

    set NH3_MODEL=1.2
    cd analysis\nh3_staged_converter_2026_10_12
    python -m unittest test_staged -v          # loop closure and costs against the 1.2 harness; converter invariance
    python kinetics_swap.py                    # -> nh3_1_2/kinetics_swap.json, kinetics_swap_pressure_profiles.csv (20 s)
    python staged_invariance_1_2.py --write    # -> nh3_1_2/ copies of the run_staged.py outputs, staged_invariance.json
    python boundary.py                         # -> nh3_1_2/boundary_*.csv, boundary_summary.json
    python manuscript_numbers.py               # -> nh3_1_2/manuscript_numbers.json

(`D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8`; no response surface is needed, the harness is built from
the in-repo 1.2 core, manifest and workbook.) With `NH3_MODEL=1.1` (default) `kinetics_swap.py`, `boundary.py`,
`validate_kinetics.py` and `manuscript_numbers.py` rewrite the parent folder's files byte for byte (`git diff` empty);
`run_staged.py` (about 8 CPU hours) was not rerun under 1.1: its 1,218 committed library and arrangement designs
re-evaluate with the 1.1 harness to their committed costs within 6.4 × 10⁻⁵ USD/t (1,187 within 10⁻⁴ at the printed x,
median 2.6 × 10⁻⁷; 31 optima on a cost discontinuity — an isothermal bed exactly at the catalyst's maximum temperature,
the recycle-compressor CAPEX step, the 90 m³ cap — at a corner of the printing interval of x;
`staged_invariance.json`, `committed_1_1_costs_at_printed_x`). `kinetics_swap.py` first reproduces the 1.2 descriptor optima of `results.json`
(Fe 11.515783597 at 425 °C, 105 bar, 30 °C; Ru 16.632749359 at 450 °C, 220 bar, 30 °C; |diff| < 1e-9) on the same states.

## 1. Kinetics swap (primary: plug flow, measured rates, 1.2 process states)

| | NH3-FINAL-1.1 states | **NH3-FINAL-1.2 states** |
|---|---:|---:|
| Descriptor Fe / Ru optimum (USD/t) | 15.29 / 22.03 | 11.52 / 16.63 |
| Descriptor Ru parity multiple | 201.22× | 114.67× |
| Fe optimum, measured (USD/t; T, P, separator; bed) | 15.58; 425 °C, 170 bar, 30 °C; 25.6 m³ | **14.93; 450 °C, 140 bar, 30 °C; 56.3 m³** |
| Ru benchmark optimum | 28.07 at 450 °C, 325 bar, 30 °C | **33.07 at 450 °C, 735 bar, 30 °C** (within 0.64 USD/t from 400 to 890 bar; within 0.5 except 435–455 bar) |
| Ru benchmark, best at 100–200 bar | 29.08 (200 bar), +1.01 over optimum | **38.26 (200 bar), +5.19** |
| Ru activity multiple for parity with Fe | 24.6× | **13.95×** |
| … range across variants | 14.6–37.4× (8: sizing × calibration × equilibrium) | **13.95–25.07×** (4: sizing × calibration) |
| Ru benchmark optimum pressure across variants | 220–1,000 bar | 220–1,000 bar (735 / 220 / 310 / 1,000) |
| Supported Ru/C optimum, r 95.55% / 90% (benchmark accounting) | 14.17 / 14.59 at 400 °C, 145 bar (vs Fe −1.41 / −0.99) | **11.42 / 11.98 at 425 °C, 105 bar (−3.51 / −2.94)** |
| Ru/C − Fe, 25-y cash flow 0 %/y, global / KAAP (r 95.55%) | −1.36 / −1.07 | **−3.46 / −1.41** |
| Ru/C − Fe, 12 %/y, global / KAAP | +1.12 / +1.86 (optimum 190 bar) | **+1.45 / +1.73** (optimum 150 bar) |
| Same at r 90%: 0 %/y; 12 %/y (global / KAAP) | −0.85 / −0.62; +1.17 / +1.90 | −2.80 / −1.22; +1.56 / +1.82 |
| Ru/C cheaper than Fe at 0 %/y: global; KAAP | 8 of 8; 7 of 8 (−1.28 to +0.07) | **4 of 4 (−3.46 to −2.02); 4 of 4 (−1.41 to −0.08)** |
| Ru/C dearer at 12 %/y: global; KAAP | 8 of 8 (+0.88 to +5.10); 8 of 8 (+0.72 to +6.08) | 4 of 4 (+0.87 to +5.18); 4 of 4 (+0.68 to +6.19) |
| KAAP-type Fe (90 bar, −20 °C), descriptor / measured plug | 19.07 / 19.35 | 16.98 / 18.43 |

All four variants (cash flow 0 %/y and 12 %/y at r 95.55%; USD/t):

| Sizing | Rates | Fe optimum | Ru benchmark optimum | Ru parity multiple | Ru/C − Fe global 0 / 12 % | KAAP 0 / 12 % |
|---|---|---|---|---|---|---|
| plug | measured | 14.93 (450, 140, 30) | 33.07 (450, 735) | **13.95×** | −3.46 / +1.45 | −1.41 / +1.73 |
| plug | F_CAL logic (×2.65) | 12.77 (425, 110, 30) | 23.26 (450, 220) | 15.33× | −2.38 / +0.87 | −0.68 / +0.68 |
| inlet | measured | 12.67 (425, 110, 30) | 23.29 (450, 310) | 20.84× | −2.02 / +1.38 | −0.08 / +1.21 |
| inlet | F_CAL logic (×0.152) | 16.48 (450, 200, 30) | 36.64 (450, **1,000**) | 25.07× | −3.40 / +5.18 | −1.07 / +6.19 |

### Does Ru's optimal pressure fall into 100–200 bar with the measured, H₂-inhibited kinetics?

No. On NH3-FINAL-1.2 the descriptor Ru optimum is already at 220 bar (from 425 bar in 1.1). Replacing the rate laws by
the measured ones raises it again: plug flow with the measured rates puts the Ru benchmark optimum at 735 bar
(33.07 USD/t; from 400 to 890 bar the cost stays within 0.64 USD/t of it, and within 0.5 except at 435–455 bar,
just above a +0.37 USD/t cost step at 435 bar that every 1.1 profile also shows), and between 100 and 200 bar its best is
38.26 USD/t at 200 bar, 5.19 above the optimum (1.1: 325 bar, +1.01). Across the four variants the optimum lies at
220–1,000 bar; only the F_CAL-logic plug-flow variant sits at 220 bar, 0.17 USD/t below its 200-bar value. The cause is
the same as in 1.1: the Ru/C law's apparent H₂ order is +0.32 at 90 bar, 400 °C, 2% NH₃ (positive, lowered by H₂
adsorption), so the bulk-Ru inventory still rewards pressure. In addition every 1.2 state converts 0.8 of the measured,
fugacity-corrected equilibrium per pass, more than 0.8 of the lower 1.1 model equilibrium, and the extra conversion
costs Ru/C most at low pressure: the Ru benchmark at 200 bar goes from 29.08 (1.1 states) to 38.26 USD/t, at 735 bar
from 29.94 to 33.07 (the ideal-gas Gillespie–Beattie states of the 1.1 file are in between: 35.52 and 31.69, optimum
430 bar).
Parity: the Ru benchmark stays above Fe (33.07 against 14.93 USD/t) and needs a **13.95-fold** activity gain
(13.95–25.07 across variants), against 114.67-fold with the 1.2 descriptor kinetics, 24.6-fold with measured kinetics on
1.1 states and 201.22-fold in 1.1. Supported Ru/C (8 wt%, 490 kg m⁻³) does have its optimum inside 100–200 bar:
105 bar at 0 %/y (90–110 bar across variants), 150 bar at 12 %/y (130–220 bar).

## 2. Staged Fe → Ru/C converter: unchanged

`converter.py` takes from the harness only economic controls and cost functions (compression, refrigeration, converter
vessel and pressure premium, NH₃ vapour pressure, plant output). Its equilibrium (Gillespie–Beattie, Newton–Cooper),
rates and per-pass conversion are its own, and it never reads the harness process states or F_CAL. NH3-FINAL-1.2 changes
only the thermo block and F_CAL, so the staged converter is the same calculation under both models.
`staged_invariance_1_2.py` checks it (`staged_invariance.json`):

- `_init_controls` gives 51 controls; the 1.1 and 1.2 manifests differ only in F_CAL (89,806.5 → 74,351.6), which the
  converter never reads; the source of every harness function it calls is identical in the 1.1 and 1.2 cores;
- `converter.evaluate` is bit-identical with either harness for 1,482 designs (the 1,110 library designs and 108
  arrangement optima of the committed outputs at their printed x, and 264 random designs of every pattern, loop and
  bed mode); max |difference| 0;
- two complete optimisations (DE + Nelder–Mead, as in `run_staged.py`) return bit-identical results;
- with the 1.1 harness the 1,218 committed library and arrangement designs re-evaluate to their committed costs within
  6.4 × 10⁻⁵ USD/t (see above), so the copied files are what the current code computes.

`run_staged.py` (about 8 CPU hours) was therefore not rerun: `arrangements.csv`, `sensitivities.csv`,
`design_library.csv`, `envelope_checks.csv` and `summary.json` here are byte copies of the committed 1.1 outputs
(SHA-256 in `staged_invariance.json`; `NH3_MODEL=1.2 python run_staged.py` would rewrite them identically). The decision
maps were rebuilt under NH3_MODEL=1.2 by `boundary.py` from the copied library and are byte-identical to the 1.1 maps.

| Staged-converter number (KAAP-type 90 bar, −20 °C, 8% inerts, today's Ru price) | 1.1 | 1.2 |
|---|---:|---:|
| all-Ru/C / Fe-first (Fe upstream, Ru/C downstream) / all-Fe, r 95.55% | 0–0.82 / 0.82–6.65 / > 6.65 %/y | same |
| Fe-first window at r 90% | 0.13–6.14 %/y | same |
| Fe-first window at Ru price −30% / +30% | 1.42–9.98 / 0.50–4.92 %/y | same |
| Bed order inside the window | FRR (Fe, Ru/C, Ru/C) from 0.82 to 4.65 %/y, then FFR to 6.65 %/y | same |
| Ru/C share of the catalyst volume across the window | 56% at 0.82 %/y (54% at 1 %/y) → 4% at 6.65 %/y | same |
| Saving over all-Fe at 1.35 / 2.10 / 5.10 %/y | 0.78 / 0.59 / 0.10 USD/t | same |
| 150 / 200 bar loops (−5 °C): Fe-first optimal up to; all-Ru/C optimal | 4.66 / 3.20 %/y; never | same |
| Ru/C-first optimal | in no case (arrangements, sensitivities) | same |
| Benchmark accounting: all-Ru/C − Fe-first | −0.07 USD/t | same |
| Ru/C : Fe rate per kg at 90 bar, 400 °C, 2% → 14% NH₃ (rate laws) | 16 → 52 | same |

Not affected by the model: `validate_kinetics.py` and its outputs (rate laws against their sources) in the parent folder.

## 3. 1.1-specific choices, re-derived

- **Process states.** The 1.1 run had two state sets: NH3-FINAL-1.1 (model equilibrium) and states rebuilt at the
  Gillespie–Beattie equilibrium (PR #64, ideal-gas loop). On 1.2 the model equilibrium is the measured one with
  fugacities, the basis the two rate laws already use, so the equilibrium dimension collapses: the four sizing ×
  calibration variants run on the 14,510 states of the canonical 1.2 run (`states = "1.2"`). The ideal-gas
  Gillespie–Beattie states are not a 1.2 variant (their results are the `GB` rows of the 1.1 file).
- **F_CAL-logic factor.** Same definition: one factor so that Fe needs, with the same sizing, the descriptor Fe bed at
  the calibration state (400 °C, 80 bar, −35 °C). On 1.2 that bed is 66.00741 m³ (by construction of the 1.2 F_CAL); the
  measured Fe bed there is 175.0 m³ in plug flow (1.1 states: 54.3) and 10.0 m³ with inlet-rate sizing (12.3), giving
  factors 2.65 and 0.152 (1.1: 0.823 and 0.187).
- **Anchors.** The descriptor Fe / Ru optima asserted before the swap and the descriptor parity multiple come from the
  1.2 `results.json` (`analysis/nh3_model.py`, `anchors()`), not from the 1.1 constants.
- **KAAP-type states** keep their definition (90 bar, −20 °C separator).

## Files

| File | Content |
|---|---|
| `kinetics_swap.json`, `kinetics_swap_pressure_profiles.csv` | section 1 (4 variants; profile rows `states = 1.2`) |
| `arrangements.csv`, `sensitivities.csv`, `design_library.csv`, `envelope_checks.csv`, `summary.json` | section 2, byte copies of the 1.1 outputs (invariant) |
| `boundary_price_financing.csv`, `boundary_pressure.csv`, `boundary_summary.json` | section 2, rebuilt under 1.2 (identical bytes) |
| `staged_invariance.json` | invariance evidence and SHA-256 of the copies |
| `manuscript_numbers.json` | the numbers of sections 1–2 as quoted (from `manuscript_numbers.py`) |

Plots (`plot_swap.py`, `plot_staged.py`) were not rendered for 1.2.
