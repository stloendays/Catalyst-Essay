# NH₃ measured-kinetics comparisons with each catalyst inside its fitted pressure range (2026-10-19)

Each catalyst searches for its least-cost process state only among the NH3-FINAL-1.2 states inside the pressure range its
rate law was fitted on, and the two optima are then compared. Nothing else changes: same 14,510 states (run
`nh3_final_1_2_20261013`), plug-flow sizing with the measured rates, the same costs, u = 11, Ru 53,852.5 USD/kg, 8 wt% Ru/C
at 490 kg m⁻³, 95.55 % recovery, 25-year owned-metal cash flow for the financing cases (Fe on the same convention).

    set NH3_MODEL=1.2
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 fitted_range.py     # -> results.json, results.csv (20 s)

The script imports `analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py` and
`analysis/nh3_frontier_provenance_2026_10_13/frontier_swap.py` unchanged. It first reproduces the unrestricted numbers and
asserts them against the committed `nh3_1_2/kinetics_swap.json` and `nh3_1_2/frontier_swap.json` and the manuscript's
rounded values (Fe 14.93 at 450 °C/140 bar; Ru 33.07 at 735 bar, 38.26 at 100–200 bar; Ru/C −3.46/+1.45, KAAP −1.41/+1.73;
break-even 7.23/5.37 %/y; parity 13.95×, 13.95–25.07× over the four variants; Ru price parity 3,781 USD/kg). Only then
are the masks applied.

## Fitted ranges used (`parameters.yaml` of the staged-converter folder, `validity`)

| Law | Pressure | Temperature | Source |
|---|---|---|---|
| Fe, Dyson & Simon (Topsøe KM1, Nielsen's data) | 149–309 atm = **150.97–313.09 bar** | 330–495 °C | Hansen 1995, p. 168 |
| Ru/C, Rossetti et al. 2006 | **50–100 bar** | 370–460 °C | Rossetti 2006, Table 1 |

States in range (5-bar pressure grid, T 350–450 °C in 25 °C steps, separator −40 to 30 °C): Fe 2,400 states at
155–310 bar (32 pressures); Ru/C 780 states at 50–100 bar (11 pressures), 615 of them also inside 370–460 °C. The KAAP-type
loop (90 bar, −20 °C) has 5 states, all inside the Ru/C range and none inside the Fe range. All states are ≤ 450 °C, so the
Ru/C 460 °C cap holds everywhere. Every optimum below lies at 425 or 450 °C, inside both temperature ranges: adding the
temperature restriction (`in_range_PT` in the files) changes no number.

## Before / after (plug flow, measured rates; USD per tonne NH₃; T / P / separator)

| Comparison | Unrestricted | **Each catalyst in its fitted range** |
|---|---|---|
| (a) Fe, benchmark accounting | 14.93 (450 °C, 140 bar, 30 °C) | **15.08** (450 °C, 155 bar, 30 °C) |
| (a) bulk-price Ru, benchmark formulation | 33.07 (450, 735, 30); 38.26 best at 100–200 bar (200 bar) | **45.87** (450, 100, −20) |
| (a) Ru − Fe | +18.14 (+23.34 at 100–200 bar) | **+30.79** |
| (d) Ru activity multiple for parity | 13.95× (13.95–25.07× over 4 variants) | **16.98×** (11.96–33.17×) |
| (e) bulk Ru break-even price | 3,781 USD/kg (7.02 % of today; 93.0 % cheaper) | **3,108 USD/kg** (5.77 %; **94.2 % cheaper**) |
| (b) Ru/C − Fe, 0 %/y | −3.46 (Ru/C 11.51 at 425/105/30; Fe 14.97 at 450/140/30) | **−3.58** (Ru/C 11.54 at 425/100/30; Fe 15.12 at 450/155/30) |
| (b) Ru/C − Fe, 12 %/y | +1.45 (Ru/C 16.57 at 450/150/30) | **+2.44** (Ru/C 17.68 at 450/100/10; Fe 15.23) |
| (b) break-even financing rate | 7.23 %/y (Ru/C 135 bar, Fe 140 bar) | **5.80 %/y** (Ru/C 100 bar, Fe 155 bar; 15.16) |
| (e) supported Ru/C break-even price, 0 %/y | 743,989 USD/kg (13.8× today: already cheaper) | **612,977** (11.4×: already cheaper) |
| (e) supported Ru/C break-even price, 12 %/y | 34,131 USD/kg (0.634×; 36.6 % cheaper) | **27,861** (0.517×; **48.3 % cheaper**) |
| (c) KAAP-type loop, Fe | 18.48 / 18.61 (450, 90, −20) at 0 / 12 %/y | **no in-range state** (90 bar < 151 bar) |
| (c) Ru/C KAAP-type vs Fe in the same loop, 0 / 12 %/y | −1.41 / +1.73; break-even 5.37 %/y | not defined (Fe out of range) |
| (c) Ru/C KAAP-type (17.06 / 20.34) vs Fe in-range optimum (15.12 / 15.23) | — | **+1.95 / +5.10**; Fe cheaper at every rate 0–30 %/y and at any Ru price (+1.64 / +1.52 with free Ru) |
| (c) same, Fe held at a −20 °C separator (21.43 / 21.51 at 155 bar) | — | −4.37 / −1.17; break-even 16.4 %/y |

Variant detail of (d), in range (Fe / bulk Ru optimum, USD/t): plug-source 15.08 / 45.87; plug-F_CAL 13.60 / 27.19;
inlet-source 13.38 / 26.66; inlet-F_CAL 16.48 (200 bar) / 63.67. Every in-range Ru optimum is at 100 bar, the top of the
Ru/C range; every Fe optimum except inlet-F_CAL is at 155 bar, the lowest grid pressure inside the Fe range (Fe at 150 bar,
1 atm below the range, would cost 15.01).

## Reading

- Fe-first holds under the rule. Bulk-price Ru is 30.79 USD/t above Fe and would need a 17-fold activity gain (12–33-fold
  across variants) or a Ru price 94 % lower.
- Supported Ru/C with recovery ties Fe at low pressure: at 100 bar it is 3.58 cheaper than Fe at 155 bar without
  financing, and the break-even financing rate is 5.80 %/y (from 7.23). At 12 %/y Ru must be 48 % cheaper (27,861 USD/kg)
  to tie.
- The KAAP-type comparison cannot be made like-for-like: 90 bar is outside the Fe range. Against Fe's own in-range
  optimum, Ru/C in the KAAP-type loop is dearer at every financing rate: the KAAP-type state costs Ru/C 5.52 more than
  its own in-range optimum at 0 %/y (17.06 against 11.54).
- No single pressure lies inside both ranges (Ru/C ≤ 100 bar, Fe ≥ 151 bar), so the staged Fe + Ru/C converter at 9 MPa
  (and the 150/200 bar loops) extrapolates at least one law under this rule; it was not rerun here.

## Files

| File | Content |
|---|---|
| `fitted_range.py` | reproduction gate, masks, all comparisons |
| `results.json` | full results: `unrestricted`, `in_range_P` (the rule), `in_range_PT` (plus temperature), state counts, ranges |
| `results.csv` | one row per comparison × rule: Fe and Ru optima (cost, T, P, separator, bed volume), gap, scalar value |
