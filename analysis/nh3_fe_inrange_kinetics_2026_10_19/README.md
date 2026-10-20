# NH₃: fused-iron rate law fitted down to 1 bar, so Fe and Ru/C share 50–100 bar (2026-10-19)

The Dyson–Simon law used for Fe in the manuscript was fitted at 149–309 atm (151–313 bar), and the Rossetti Ru/C law at
50–100 bar. No pressure lies in both ranges, so the KAAP-type loop (90 bar) and the 9 MPa staged converter extrapolated
the Fe law (`analysis/nh3_fitted_range_2026_10_19`). This folder replaces only the Fe law, with one whose fitted range
covers both.

**Fe law.** Keestra, Slotboom, Rouwenhorst & Brilman, *Chem. Eng. J.* 518 (2025) 164593 (CC BY), Model 3 (N\* and H\*
coverage), global parameters of SI Table 8, fitted on a century of commercial-iron kinetic data at 1–324 bar and
251–550 °C (range as transcribed from the main text in PR #114, `sources.json`; SI Table 9 lists the data sets, from
1-atm Ozaki and Temkin–Pyzhev to the 150–300-atm Nielsen KM1 data). Each catalyst carries a fitted activity factor
b_cat. The headline uses **Topsoe KM1R (1964), b_cat = 0.350**: the Nielsen, Kjaer & Hansen data that Dyson and Simon
fitted, so the catalyst is the manuscript's. Sensitivities: Gillespie–Beattie K_f instead of the source K_f, and
KM1R (1999), b_cat = 0.905. SI file SHA-256 b43f9988…773a (same file as PR #114). Fugacities are the Newton–Cooper ones
that the Dyson–Simon and Rossetti laws already use; bed density 2,500 kg m⁻³ (harness and Keestra's own Fe example).
The Fe side of Keestra was reproduced independently in PR #114 (authors' Fe GHSV within +2.5 to +13 %); the Ru side
of that PR is not used here, Ru/C stays Rossetti 2006 as in the manuscript.

    set NH3_MODEL=1.2
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 validate_fe.py                 # validation.json
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 fe_inrange.py                  # results.json, results.csv (1 min)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 staged_inrange.py --workers 2  # staged_KM1R_1964_* (KAAP loop)

`fe_inrange.py` imports `analysis/nh3_fitted_range_2026_10_19/fitted_range.py` unchanged and first reproduces its
Dyson–Simon in-range numbers (gate). `staged_inrange.py` uses `converter.py`, `run_staged.py` and `boundary.py` of the
staged-converter folder unchanged; its gate runs the committed Dyson–Simon design library through the same window
extraction and recovers the manuscript window (all-Ru/C below 0.82 %/y, Fe-first to 6.65 %/y; staging saves 0.78,
0.59, 0.10 USD/t at 1.35, 2.10, 5.10 %/y).

## 1. Checks of the Fe law (`validation.json`)

| Check | Result |
|---|---|
| Source K_f / Gillespie–Beattie, 350–450 °C | 1.013–1.028 |
| Micropilot commercial magnetite, 100 bar, 430 °C, 30,000 h⁻¹: 8 % NH₃ | KM1R-1964 9.29 % (+16 %); Dyson–Simon 8.20 % (+2.5 %) |
| Micropilot wüstite, same conditions: 12.5 % | KM1R-1999 12.79 % (+2.3 %); AmoMax 10 13.18 % (+5.4 %) |
| Same catalyst in Dyson–Simon's range: Keestra / Dyson–Simon plug-flow bed volume, 2,400 states at 155–310 bar | median 1.67 (1.05–2.32) |
| Same ratio, KAAP-type states (90 bar, −20 °C) / all 50–100-bar states | median 1.33 (0.89–1.97) / 1.39 |

On the isothermal states of the cost model (≤ 450 °C) Keestra gives the same KM1 catalyst a lower rate than Dyson–Simon
(stronger NH₃ inhibition near the bed outlet), so there the swap moves costs against Fe, not in its favour.

## 2. Each catalyst inside its fitted range (`results.json`, `results.csv`; plug flow, source rates; USD per t NH₃)

Fe range 1–324 bar (Keestra), Ru/C 50–100 bar (Rossetti); common range 50–100 bar (780 states). Every state is ≤ 450 °C.

| Comparison | Dyson–Simon, own range (151–313 bar) | **Keestra KM1R-1964** | Keestra, GB K_f | Keestra KM1R-1999 |
|---|---:|---:|---:|---:|
| Fe optimum | 15.08 (155 bar) | **15.31 (110 bar)** | 15.43 (110) | 13.01 (110) |
| bulk-price Ru (100 bar) − Fe | +30.79 | **+30.56** | +30.43 | +32.86 |
| Ru activity multiple for parity | 16.98× | **15.68×** | 15.04× | 47.45× |
| bulk Ru break-even price | 3,108 USD/kg (−94.2 %) | **3,371 (−93.7 %)** | 3,519 (−93.5 %) | 1,071 (−98.0 %) |
| Ru/C − Fe, each in range, 0 / 12 %/y | −3.58 / +2.44 | **−3.83 / +2.13** | −3.96 / +2.00 | −1.50 / +4.54 |
| break-even financing, each in range | 5.80 %/y | **6.49 %/y** | 6.82 | 1.41 |
| Ru/C − Fe, both at 50–100 bar, 0 / 12 %/y | none in common | **−4.02 / +1.93**; 6.98 %/y | −4.15 / +1.79; 7.32 | −1.79 / +4.24; 1.97 |
| **KAAP-type loop (90 bar, −20 °C), both in range**, Ru/C − Fe, 0 / 12 %/y | Fe has no in-range state | **−1.21 / +1.95** (Fe 18.27 / 18.39, Ru/C 17.06 / 20.34) | −1.26 / +1.89 | −0.29 / +2.94 |
| KAAP-type break-even financing | — | **4.57 %/y** | 4.76 | 1.04 |
| KAAP-type Ru/C break-even Ru price, 12 %/y | — | **23,150 USD/kg (−57 %)** | 23,993 | 7,450 |

Manuscript (Dyson–Simon extrapolated to 90 bar): KAAP-type −1.41 / +1.73, break-even 5.37 %/y. With both laws inside
their fitted ranges the KAAP-type result is −1.21 / +1.95 and 4.57 %/y: same signs, same reading.

## 3. Staged converter at 9 MPa, both laws in range

`staged_KM1R_1964_summary.json`, `_arrangements.csv`, `_design_library.csv`, `_envelope_checks.csv`. KAAP-type loop
(90 bar, −20 °C, 8 % inerts), Ru 53,852.5 USD/kg, 95.55 % recovery, 25-year cash flow; Fe = Keestra KM1R-1964, Ru/C =
Rossetti 2006, both inside their fitted ranges. 18 global optimisations, 12 continuation chains (144 designs); the
library envelope is within 0.007 USD/t of 20 direct optimisations at 0, 1.35, 2.10, 5.10 and 12 %/y.

| | Manuscript (Dyson–Simon extrapolated to 90 bar) | **Both laws in range** |
|---|---|---|
| all-Ru/C optimal | 0–0.82 %/y | never strictly (at 0 %/y FRR 17.346 vs RRR 17.355) |
| Fe first, Ru/C downstream optimal | 0.82–6.65 %/y | **0–5.46 %/y** |
| all-Fe optimal | above 6.65 %/y | above 5.46 %/y |
| Ru/C first, Fe downstream | never optimal | never optimal (all three economics) |
| saving of staging over all-Fe at 1.35 / 2.10 / 5.10 %/y | 0.78 / 0.59 / 0.10 USD/t | **0.53 / 0.37 / 0.02** |
| Ru/C share of catalyst volume across the window | 54 % → ~4 % | 69 % → 5 % |
| benchmark accounting, r 95.55 % | — | FRR 17.30 vs all-Fe 18.28 vs all-Ru/C 17.30 |
| 12 %/y | all-Fe | all-Fe 18.39 (FFR 18.45, all-Ru/C 20.71) |

The disclosed lease rates (1.35–5.10 %/y) stay inside the Fe-first window, and the bed order of the KAAP converter
(fused iron first, Ru/C downstream) is still the optimum there. The window narrows from 6.65 to 5.46 %/y and the
savings shrink because the all-Fe converter gets cheaper (18.31 against 18.67 USD/t at 0 %/y; 24.5 against 33.1 m³ in
the benchmark case: the adiabatic Fe beds run up to 530 °C, where the Keestra rate is higher), while the Ru/C
arrangements barely move (all-Ru/C 17.355 in both).

## 4. Robustness cases, window variants and the quantities the text quotes

- `robustness_inrange.py` → `robustness.json/.csv`: the 16 cases of `frontier_swap.py` with each catalyst in range.
  Fe is cheaper at 12 %/y in 15 of 16 in both loops (all but a halved Fe effectiveness, which in the KAAP-type loop
  leaves no Fe bed within 90 m³); Ru/C is cheaper at 0 %/y in 16 (main) and 15 (KAAP-type; all but inlet-rate sizing);
  break-even 1.23–15.65 %/y (main), 0.71–8.43 %/y (KAAP-type).
- `staged_window_variants.py` → `staged_window_variants.json`: Fe-first window 0–4.92 %/y at 90 % recovery,
  0.12–8.21 %/y at a 30 % lower Ru price (all-Ru/C below 0.12), 0–4.03 %/y at +30 %. The committed Dyson–Simon
  library gives the SI's 0.13–6.14, 1.42–9.98 and 0.50–4.92 with the same code.
- `fe_inrange.py` also gives the parity multiple across the four sizing × calibration variants (15.68–45.39) and the
  break-even rates at 90 % recovery (5.98 %/y main, 4.00 %/y KAAP-type); `validate_fe.py` the apparent orders at
  90 bar, 400 °C, 2 % NH₃ (Keestra Fe: N₂ +1.00, H₂ +0.71, NH₃ −0.89) and the Ru/C (8 wt%) to Fe rate ratio per kg
  (9 at 2 % NH₃, 62 at 14 %).

## Files

| File | Content |
|---|---|
| `keestra_fe.py` | Keestra Model 3 Fe rate (source parameters, b_cat, K_f), on the Newton–Cooper fugacity basis |
| `validate_fe.py`, `validation.json` | checks of section 1 |
| `fe_inrange.py`, `results.json`, `results.csv` | section 2; Dyson–Simon gate, three Fe variants |
| `staged_inrange.py`, `staged_KM1R_1964_*` | section 3: arrangements, design library, envelope checks, window |
