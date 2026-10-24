# Staged converter with the Ru/C temperature limit raised to 500 °C and 530 °C (2026-10-24)

Question (internal review, item 3): SI Note 7 said that fused iron takes the first, hottest bed *because* Ru/C is held
to 460 °C, the top of its measured range. If the order came from that limit, the main-text claim that the optimizer
recovers the industrial bed order would rest on a constraint. Here the Ru/C limit is raised to 500 °C (methanation
limit of the carbon support, the existing sensitivity of parameters.yaml) and to 530 °C, the limit of fused iron, so
both catalysts get the same window. Above 460 °C the Rossetti law is extrapolated in temperature.

    set NH3_MODEL=1.2
    set RU_TMAX_C=500    (or 530)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 staged_ru_tmax.py --workers 3   # ~20 min each

Same code path as `analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_inrange.py` (both laws in their fitted pressure
ranges: Keestra KM1R-1964 fused iron, Rossetti 2006 Ru/C; KAAP-type loop 90 bar, −20 °C, 8 % inerts; Ru 53,852.5
USD/kg, 95.55 % recovery, 25-year cash flow), with `T_max_Ru_C` changed. Unlike the manuscript library, the Ru/C-first
arrangements RFF and RRF are continued over the (c_Ru, c_Fe) grid too, so the window compares all six three-bed
arrangements at every rate. Library envelope within 0.006 USD/t of 18 direct optimisations (0, 2.10 and 12 %/y).

| Ru/C limit | all-Ru/C optimal | Fe first, Ru/C downstream optimal | all-Fe optimal | Ru/C first optimal | best at 2.10 %/y |
|---|---|---|---|---|---|
| 460 °C (manuscript) | never strictly | 0–5.46 %/y | above 5.46 | never | FRR, 17.95 (all-Fe 18.32) |
| 500 °C | 0–1.37 %/y | 1.37–6.00 %/y | above 6.00 | never | FRR, 17.86 (all-Fe 18.32, all-Ru/C 17.89) |
| 530 °C | 0–3.10 %/y | 3.10–6.00 %/y | above 6.00 | never | all-Ru/C, 17.84 (FRR 17.86) |

At every rate below 6 %/y the best Ru/C-first converter costs more than the best Fe-first converter: by 0.060–0.253
USD/t at 500 °C and 0.057–0.156 at 530 °C (above 6 %/y both hold no Ru/C and coincide). Arrangement by arrangement at
0 %/y (530 °C): FRR 17.301 against RRF 17.361, FFR 17.518 against RFF 17.881.

Reading: the temperature limit decides only how much Ru/C a converter holds. Allowed to run as hot as fused iron, Ru/C
can fill the converter when its metal is financed cheaply, but whenever the two catalysts share a converter fused iron
goes upstream, and a Ru/C-first converter is never optimal. The order comes from the kinetics: ammonia inhibits fused
iron more strongly than Ru/C (rate advantage of Ru/C per kg 9-fold at 2 % NH₃, 62-fold at 14 %), so fused iron works
where the gas is still lean in NH₃.

Files: `tmax<T>_summary.json` (arrangements, window regimes, rates, envelope check), `tmax<T>_window.csv` (cost of all
six arrangements on the 0–12 %/y grid), `tmax<T>_arrangements.csv`, `tmax<T>_design_library.csv`,
`tmax<T>_envelope_checks.csv`, `tmax<T>_stdout.txt`.

## All-Ru/C against all-Fe, and the KAAP-type loop of Fig. 5a (`all_ruc_breakeven.py` → `all_ruc_breakeven.json`)

Fig. 5a puts the Ru/C − Fe break-even of the KAAP-type loop (isothermal plug-flow states, same loop, laws and costs) at
4.57 %/y, whereas in the three-bed converter the all-Ru/C design matches all-Fe at 2.46 %/y with Ru/C held to 460 °C.
Read from the committed cost curves, the same crossing moves to 4.32 %/y at 500 °C and 4.96 %/y at 530 °C, bracketing
4.57: the gap is the temperature limit on adiabatic Ru/C beds, which must leave at the limit after their temperature
rise. Stated in the Fig. 5b caption and SI Note 7.
