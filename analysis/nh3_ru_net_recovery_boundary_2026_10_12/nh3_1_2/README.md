# Ru/C net-recovery boundary and 25-year metal cash flow on NH3-FINAL-1.2

The files here are the NH3-FINAL-1.2 counterparts of the files one level up, with the same names and columns, from
the same scripts run on the canonical 1.2 run `nh3_final_1_2_20261013` (14,510 process states, cached response
surface; never rebuilt). `decision_thresholds.csv` and `decision_report.json` (from `analyze_boundary.py`) are committed
here as well; one level up they are CI artifacts only. PNGs are not committed (as for 1.1).

```
set NH3_MODEL=1.2
set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness
D:\Research\CatalystForge\.venv\Scripts\python.exe analysis\nh3_ru_net_recovery_boundary_2026_10_12\run_boundary.py
D:\Research\CatalystForge\.venv\Scripts\python.exe analysis\nh3_ru_net_recovery_boundary_2026_10_12\analyze_boundary.py
D:\Research\CatalystForge\.venv\Scripts\python.exe analysis\nh3_ru_net_recovery_boundary_2026_10_12\run_lifecycle_cashflow.py
```

Order matters: `analyze_boundary.py` and `run_lifecycle_cashflow.py` read `cost_surface.csv` of the same model.
Each script takes about 10 s.

## Checks

- `model_inputs.py` loads the selected harness through `analysis/nh3_model.py`, reads the cached response surface
  directly and refuses to run if it is missing or does not match the manifest (no implicit rebuild).
- Fe in the main loop equals the run's feasible Fe optimum (`anchors()["Fe"]`, 11.515783597179267) to 1e-9, and Fe in
  the main and KAAP loops equals the Fe references of `figures/composite/fig2/nh3_1_2/fig2_ru_bed_sensitivity.csv`
  (11.515783597179267 / 16.97956884800555). The hard-coded 1.1 values (15.2917… / 19.0687…) are replaced by these reads.
- The 24 golden cells (η = 1, r = 0.90 and 0.9555, w = 5/8/10 wt%, ρ = 430/550 kg m⁻³, both loops) equal the own-bed
  costs of `fig2/nh3_1_2/fig2_ru_bed_sensitivity.csv` (independent script `fig2_ru_actual_cost.py`) within 1e-9 USD/t.
  The parent `analysis/nh3_actual_ru_params_2026_10_07` has no 1.2 port; its `promoted_recovery_check.csv` would be
  used from `<parent>/nh3_1_2/` if it existed. Under 1.1 both references are checked (24/24 each).
- The 24-row lifecycle regression (20-year, zero-discount, full terminal resale reproduces the straight-line
  `cost_surface.csv`) passes within 1e-9 USD/t on the 1.2 surface.
- Plant life 25 y, plant discount rate 12 %, catalyst life 10 y and the Ru price 53,852.5 USD/kg are the same in the 1.2
  manifest (the script asserts them).
- With `NH3_MODEL=1.1` the three scripts rewrite the committed files one level up: the CSVs byte for byte; the two JSON
  files byte for byte after CRLF → LF (`Path.write_text` writes CRLF on Windows; the committed bytes come from the Linux
  CI runner).

## Re-derived definitions (rule 4)

- **Break-even metal financing rate.** Same definition as 1.1: the metal-financing rate at which Ru/C equals Fe in the
  KAAP loop (8 wt% Ru, 490 kg m⁻³, 95.55 % recovery, 10-y Ru life, ideal refining and sale), Fe financed at the same
  rate. In 1.1 it lies inside the 0–12 % sweep. Under 1.2 Ru stays below Fe across 0–12 %, so the script continues the
  same monotonicity-checked grid in 1 %/y steps above 12 % and bisects there (1.1 output unchanged: that branch is not
  reached).
- The decision-report assertion "Ru never beats Fe in the main loop at η = 1" is a 1.1 property; under 1.2 it fails
  (6/63) and the count is reported instead of asserted.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

KAAP loop = 90 bar, −20 °C separator; flagship = KAAP, 8 wt% Ru/C, 490 kg m⁻³, u = 11, 95.55 % gross recovery, 10-y life.

| Quantity | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| Process states | 14,136 | 14,510 |
| Fe optimum (main loop) | 15.2917 USD/t | 11.5158 USD/t |
| Fe in the KAAP loop (straight-line metal charge) | 19.0687 USD/t | 16.9796 USD/t |
| Own bed 8 wt%, 430–550: main loop, 90 % / 95.55 % recovery | 15.92–16.01 / 15.69–15.79 | 11.99–12.05 / 11.46–11.59 |
| Own bed 8 wt%, 430–550: KAAP loop, 0 % / 90 % / 95.55 % recovery | 21.376–21.395 / 19.034–19.079 / 18.671–18.803 | 16.899–16.904 / 16.424–16.435 / 16.346–16.371 |
| Parity credit q* (η = 1), main loop, 9 beds | unreachable (q* > 1) in all 9 | 0.941–0.999; ≤ 0.9555 in 4 beds (8 wt%/550, 10 wt%/430–550) |
| Parity credit q* (η = 1), KAAP loop, 9 beds | 0.885–0.931 | 0 (Ru/C below Fe in the loop without recovery) |
| Flagship q* / realization needed at 95.55 % | 0.8966 / 93.84 % | 0 / 0 |
| Same-loop Ru cheaper, straight-line, η = 0.8 / 0.9 / 1.0 (63 cells each): main | 0 / 0 / 0 | 0 / 0 / 6 |
| same: KAAP | 0 / 0 / 37 | 63 / 63 / 63 |
| Flagship DCF, 0 % metal financing: Ru vs Fe (gap) | 18.839 vs 19.087 (−0.248) | 16.379 vs 16.984 (−0.606) |
| Flagship DCF, 12 % metal financing: Ru vs Fe (gap) | 21.786 vs 19.142 (+2.644) | 16.987 vs 16.999 (−0.012) |
| Flagship DCF, 12 %, mild / strong losses: gap | +2.808 / +3.004 | +0.023 / +0.045 |
| Flagship Ru optimum T at 0 % / 12 % | 400 / 450 °C | 375 / 425 °C |
| Break-even metal financing rate (flagship) | 0.5604 %/y | 12.333 %/y |
| Sale-price fraction for parity at 0 % / 12 % financing | 95.29 % / none (not reachable) | 0 % (Ru cheaper without resale) / 94.68 % |
| DCF grid, Ru cheaper (81 cells each), zero carrying ideal: main / KAAP | 0/81 / 49/81 | 10/81 / 81/81 |
| DCF grid, 12 % ideal: main / KAAP | 0/81 / 0/81 | 0/81 / 43/81 |
| DCF grid, 12 % mild losses: main / KAAP | 0/81 / 0/81 | 0/81 / 7/81 |
| DCF grid, 12 % strong losses: main / KAAP | 0/81 / 0/81 | 0/81 / 0/81 |
| Rate sweep (27 KAAP cells per rate), Ru cheaper at 0 / 0.5 / 1 / 2–8 / 12 %/y | 16 / 6 / 0 / 0 / 0 | 27 / 27 / 27 / 27 / 17 |
| Rate sweep, main loop, Ru cheaper at 0 %/y (27 cells) | 0 | 2 |
| Rows: cost surface / parity / scenarios / rate sweep / legacy regression | 378 / 54 / 648 / 378 / 24 | same |

Under 1.2 the KAAP-loop comparison changes character: Fe in the 90 bar, −20 °C loop costs 5.46 USD/t above its own
optimum (1.1: 3.78), and the supported Ru/C bed is below it even without recovery, so the financing of the Ru inventory
no longer reverses the KAAP parity below a 12.3 %/y metal rate.
