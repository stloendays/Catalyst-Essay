# NH3 plant benchmark, NH3-FINAL-1.2 re-score (2026-10-13)

The 64 pre-registered comparisons of `../PREREGISTRATION.md` (commit `b11133c`) scored on NH3-FINAL-1.2
(`provenance/nh3_final_1_2/`, canonical run `nh3_final_1_2_20261013`). The metrics, tolerances, industrial windows and
pass rules are the registered ones. The registered verdict is NH3-FINAL-1.1, **14/64** (`../summary.json`); this
re-score sits beside it as the model-upgrade result and does not replace it.

**NH3-FINAL-1.2: 32 of 64 pass.**

| Table | NH3-FINAL-1.1 (registered) | NH3-FINAL-1.2 | PR #77 column (unchanged) |
|---|---:|---:|---:|
| A loop states (13 loop records) | 1/28 | **18/28** | 17/26 |
| E compressor power | 1/3 | **0/3** | 0/3 |
| B converter model, measured kinetics | 5/20 | **5/20** | – |
| C revealed design | 7/12 | **9/12** | 7/9 |
| V separator vapour | 0/1 | **0/1** | – |
| **all** | **14/64** | **32/64** | **24/38** |

    cd analysis/validation_nh3_plant_2026_10_13
    NH3_MODEL=1.2 python -m unittest test_reproduce -v      # 3 tests, ~15 s
    NH3_MODEL=1.2 python run_benchmark.py --workers 1       # ~9 min, one process -> this folder

`NH3_HARNESS_1_2` may point at another copy of `provenance/nh3_final_1_2/source_harness` (default: the repository copy).
No response surface is built: the gate uses the two bracketing descriptor-grid points (`frozen_state_logtof`).

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

| Quantity | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---:|---:|
| Pre-registered comparisons passing | 14/64 (registered) | 32/64 |
| Gate: descriptor-kinetics Fe / Ru optimum (USD/t) | 15.291705 / 22.030595 | 11.515784 / 16.632749 (= canonical results.json to 1e-9) |
| Gate: process states | 14,136 | 14,510 |
| Measured-kinetics Fe optimum (Dyson–Simon, plug flow, source rates) | 15.578802 USD/t at 425 °C, 170 bar, 30 °C; 25.59 m³ | 14.925644 USD/t at 450 °C, 140 bar, 30 °C; 56.30 m³ |
| Loop-equilibrium per-pass N₂ conversion, Topsøe 140 / Topsøe 220 / Krupp-Uhde 188 bar (448 °C) | 0.123 / 0.205 / 0.170 | 0.329 / 0.443 / 0.400 |
| Outlet and net NH₃ within 15 % (A02 … A26, 13 rows) | 1/13 | 8/13 |
| Converter flow and feed/make-up within 25 % (A03, A06, A09, A10) | 0/4 | 4/4 |
| Space velocity within ×2 (A19, A21, A23, A25, A27) | 0/5 (3.7–12 × the plants') | 5/5 (0.63–1.57 ×) |
| Casale 250-bar Fe bed (A28; plant 30 m³) | 6.00 m³ | 17.9 m³ |
| Converter inlet NH₃ vs the five plants that print it (A01, A04, A07, A14, A16) | 32–65 % low | 45–73 % low |
| Syngas + recycle compression, 1000 t/d 151 bar / Uhde 2000 t/d (E01, E02; plants 13.0 / 26.6 MW) | 8.01 / 17.6 MW | 7.50 / 17.1 MW |
| Recycle compression, S-200 126 bar (E03; plant 1.44 MW) | 1.12 MW (pass) | 0.325 MW (fail) |
| Fe optimum pressure (C01 78.5–343 bar; C02 world-scale 155–190 bar) | 170 bar (pass / pass) | 140 bar (pass / fail) |
| Fe optimum temperature / separator (C03 350–540 °C; C04 −25 to 7.5 °C) | 425 °C / 30 °C | 450 °C / 30 °C |
| Fe optimum catalyst (C05; 0.030–0.090 m³ per t/d) | 0.026 | 0.056 |
| Fe optimum outlet NH₃ (C06; 10–21 %) | 11.3 % | 17.9 % |
| Fe optimum space velocity (C07; 7,600–35,000 h⁻¹) | 46,460 h⁻¹ | 10,240 h⁻¹ |
| Ru/C optimum where it beats Fe, 0 %/y (C11; built Ru loops 89.2–137.9 bar) | 145 bar (Ru/C − Fe −1.36 USD/t) | 105 bar (−3.46 USD/t) |
| Supported Ru/C − Fe at 12 %/y (C12; > 0) | +1.12 USD/t | +1.45 USD/t |
| Uncounted: T_REF −25 / +25 °C (27 state and machinery metrics) | 3/27 / 1/27 | 9/27 / 7/27 |

Unchanged in both versions (the same model value to every digit):

| Quantity | Value |
|---|---:|
| S-200 forward runs, outlet NH₃ (B03, B07; plant 14.31 / 14.94 %) | 13.2 / 13.7 % |
| S-200 inverse runs, catalyst for the printed ΔT (B04, B08; installed 65.3 m³) | 76.4 / 77.6 m³ |
| Topsøe minimum-volume ratio 220/140 bar (B09; 0.60) | 0.512 |
| Cost-optimal all-Fe converters at the plants' loops (B10–B18): outlet NH₃ / bed-1 inlet / m³ per t/d | 9.8–10.1 % / 470–478 °C / 0.005–0.014 |
| KAAP layout at 89 bar (B19, B20): Fe volume share / outlet NH₃ | 0.155 / 12.7 % |
| Staged optima with Ru/C upstream of Fe (C08) | none of 44 |
| 90-bar KAAP-type loop: rate below which Ru/C enters (C09) | 6.65 %/y (no Ru at 12 %/y) |
| ρ(P, Ru financing boundary), 60–200 bar (C10) | −0.976 |
| Separator vapour NH₃, model/BASF table, median (V01) | 0.602 (0.42–0.76) |
| PR #77 column / Gillespie–Beattie ideal-gas diagnostic | 24/38 / 12/31 |

## Rows that flip (24)

| ID | Metric | NH3-FINAL-1.1 | NH3-FINAL-1.2 | Industrial | Flip |
|---|---|---:|---:|---|---|
| A02 | Topsøe 140 bar outlet NH₃ (mol%) | 7.45 | 16.9 | 17.1 | fail → pass |
| A03 | Topsøe 140 bar inlet flow (Nm³/h) | 1,137,652 | 425,248 | 500,000 | fail → pass |
| A05 | Topsøe 220 bar outlet NH₃ (mol%) | 10.2 | 22.5 | 19.9 | fail → pass |
| A06 | Topsøe 220 bar inlet flow (Nm³/h) | 679,158 | 312,556 | 407,000 | fail → pass |
| A08 | Krupp-Uhde 188 bar outlet NH₃ (mol%) | 9.25 | 20.5 | 19.67 | fail → pass |
| A09 | Krupp-Uhde 188 bar inlet flow (Nm³/h) | 1,232,756 | 522,044 | 635,302 | fail → pass |
| A10 | Krupp-Uhde 188 bar feed / make-up | 7.49 | 3.17 | 3.52 | fail → pass |
| A11 | Topsøe S-250 net NH₃ (mol%) | 5.03 | 14.8 | 16.5 | fail → pass |
| A12 | Uhde 160 bar net NH₃ (mol%) | 6.34 | 17.5 | 19.3 | fail → pass |
| A17 | Braun 150 bar outlet NH₃ (mol%) | 7.96 | 17.9 | 21.0 | fail → pass |
| A18 | Braun 150 bar net NH₃ (mol%) | 5.25 | 15.7 | 17.0 | fail → pass |
| A19 | Braun 150 bar space velocity (h⁻¹) | 91,235 | 11,938 | 7,600 | fail → pass |
| A21 | Kellogg 140 bar space velocity (h⁻¹) | 92,714 | 12,486 | 10,000 | fail → pass |
| A22 | Topsøe 260 bar net NH₃ (mol%) | 10.2 | 23.9 | 10.0–12.5 | pass → fail |
| A23 | Topsøe 260 bar space velocity (h⁻¹) | 101,883 | 16,579 | 12,000 | fail → pass |
| A24 | ICI AMV 100 bar net NH₃ (mol%) | 3.09 | 11.1 | 13.0 | fail → pass |
| A25 | ICI AMV 100 bar space velocity (h⁻¹) | 99,049 | 10,534 | 8,000 | fail → pass |
| A27 | small/medium 314 bar space velocity (h⁻¹) | 109,657 | 18,857 | 30,000 | fail → pass |
| A28 | Casale 250 bar Fe bed (m³) | 6.00 | 17.9 | 30.0 | fail → pass |
| E03 | S-200 recycle compression (MW) | 1.12 | 0.325 | 1.44 | pass → fail |
| C02 | Fe optimum pressure vs world-scale window (bar) | 170 | 140 | 155–190 | pass → fail |
| C05 | Fe optimum catalyst (m³ per t/d) | 0.026 | 0.056 | 0.030–0.090 | fail → pass |
| C07 | Fe optimum space velocity (h⁻¹) | 46,460 | 10,240 | 7,600–35,000 | fail → pass |
| C11 | Ru/C optimum pressure at 0 %/y (bar) | 145 | 105 | 89.2–137.9 | fail → pass |

21 rows flip to pass and 3 to fail. Still failing under NH3-FINAL-1.2: converter inlet NH₃ (A01, A04, A07, A14, A16;
the separator vapour is 0.60 × the BASF table, V01), outlet or net NH₃ above the band at the highest pressures and at
Kellogg (A13 PFI 266 bar +16.5 %, A15 Kellogg 17.5 % against 10–12 %, A20 +58 %, A22, A26 26.8 % against 8–10 %),
syngas + recycle compression (E01 −42 %, E02 −36 %, E03 −77 %), the converter-level rows (B01, B02, B05, B06 bed
temperatures, B10–B20 cost-optimal designs), the 30 °C separator of the Fe optimum (C04), Ru/C in the 90-bar optimum at
12 %/y (C09) and the world-scale pressure window (C02).

## What was re-derived and what is the same code

- **Process states.** Every row that evaluates the loop state (Tables A and E) or optimises over process states (C01–C07,
  C11, C12) uses the NH3-FINAL-1.2 harness (`nh3_model.harness()` with the canonical 1.2 manifest: Gillespie–Beattie
  NH₃ formation free energy, Newton–Cooper fugacities in the loop equilibrium and in the microkinetics). The Fe bed of
  the state rows (A19–A28 space velocities, A28) is the measured Dyson–Simon rate integrated in plug flow over the 1.2
  state, as before.
- **Measured-kinetics Fe optimum (C01–C07, gate anchor).** Re-derived on the 1.1 definition: Dyson–Simon rate, isothermal
  plug flow, source rates (no F_CAL scaling), benchmark accounting, 90 m³ cap, over the 14,510 states. The 1.1 anchor
  15.578802 USD/t (425 °C, 170 bar) becomes 14.925644 USD/t (450 °C, 140 bar, 56.30 m³); it is recorded in
  `../nh3_model.py` (`MEASURED_FE`) as the 1.2 regression anchor and asserted to 1e-5 before any 1.2 run. F_CAL plays no
  part in these rows. The calibration-state Fe bed handed to `kinetics_swap.evaluate` is the 1.2 one (66.0074 m³, equal to
  the 1.1 value by the F_CAL recalibration rule) and is unused with source rates.
- **Supported Ru/C (C11, C12).** Same definition (25-year cash flow at 0 and 12 %/y, recovery 95.55 %) on the 1.2 states.
- **Descriptor anchors of the gate.** Read from the canonical 1.2 `results.json` through `analysis/nh3_model.py`
  (`anchors()`); the recomputation matches to 1e-9 (bit-identical), with optima 425 °C / 105 bar / 30 °C (Fe) and
  450 °C / 220 bar / 30 °C (Ru).
- **Converter level (B01–B20), staged checks (C08–C10), separator vapour (V01): the same code and the same numbers.**
  `converter.py` already closes its equilibrium on the Gillespie–Beattie Ka with Newton–Cooper activities, and the 1.2
  manifest has the 1.1 `economics` (apart from F_CAL), `plant`, `process`, `engineering`, `inputs`,
  `atomic_reference` and `uncertainty` blocks; `nh3_model.assert_same_accounting()` asserts this before a 1.2 run. The
  staged outputs read by C08–C10 come from `converter.py` alone, and p_sat(T_sep) is unchanged in the 1.2 harness. The
  1.2 run recomputes these rows; all 25 unchanged model values (B01–B20, C04, C08–C10, V01) are identical to the
  registered ones.
- **PR #77 column** (unchanged, 24/38) and the **Gillespie–Beattie ideal-gas diagnostic** (12/31) are recomputed on their
  own harnesses; the diagnostic patches the NH3-FINAL-1.1 harness, so it is run on a 1.1 harness in the 1.2 run. Within
  50–300 bar the NH3-FINAL-1.2 values equal the PR #77 values to all six printed decimals: PR #77 is the same
  Gillespie–Beattie + Newton–Cooper loop closure on a narrower pressure grid.

## NH3-FINAL-1.1 reproduction (same code, `NH3_MODEL=1.1`)

- `python -m unittest test_reproduce -v`: 3/3 OK (Fe 15.291704676621144, Ru 22.03059478781101 to 1e-9; measured Fe
  15.578802 at 425 °C, 170 bar, 30 °C).
- `python run_benchmark.py --workers 1`: `../results_metrics.csv` and `../results_sensitivity.csv` byte-identical to the
  committed files; `../results_cases.json` and `../summary.json` differ only in their 7 wall-clock `seconds` entries
  (largest difference over the other 1,548 + 37 numbers: 0.0); stdout identical apart from the timings; 14/64.

## Files

| File | Content |
|---|---|
| `results_metrics.csv` | the 64 comparisons judged on NH3-FINAL-1.2 (same columns as `../results_metrics.csv`, PR #77 and GB-ideal columns included) |
| `rescore_1_1_vs_1_2.csv` | registered 1.1 value and verdict, 1.2 value and verdict, flip, PR #77 value and verdict, per metric |
| `results_cases.json` | every model case on NH3-FINAL-1.2 |
| `results_sensitivity.csv` | T_REF ± 25 °C on the 1.2 states; Fe effectiveness 0.5 in the forward converter runs |
| `summary.json` | counts, anchors (1.2), registered 1.1 counts, per-table re-score, flips, staged and BASF-table checks |
| `run_benchmark_stdout.txt` | console output of the 1.2 run |

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe` (CPython 3.12.14, numpy 2.3.5, scipy 1.18.0).
