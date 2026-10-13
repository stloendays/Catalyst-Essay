# Alloy extension on NH3-FINAL-1.2 (2026-10-13)

Same chain, same code, same Mamun et al. (2019) adsorption data, descriptor bridges, USGS prices and selection rules as the NH3-FINAL-1.1 results one level up; only the ammonia model changes (`analysis/nh3_model.py`, run `nh3_final_1_2_20261013`: Gillespie–Beattie NH₃ formation free energy, Newton–Cooper fugacities in the loop and in the microkinetics, 14,510 process states, F_CAL 74,351.6). The Fe comparator, the process-state count and the pure-metal self-check are taken from the 1.2 run; the backward candidates are picked by the same rule from the 1.2 forward screen (surfaces below Fe in either bridge, plus the highest-activity surface of each bridge, transition-metal layer).

```
set NH3_MODEL=1.2
set NH3_HARNESS_1_2=<repo>/provenance/nh3_final_1_2/source_harness   (with its local cache/ response surface)
python analysis/nh3_alloy_extension_2026_10_05/run_alloy_chain.py      -> nh3_1_2/alloy_chain_results.csv, calibration.json, summary.json
python analysis/nh3_alloy_extension_2026_10_05/run_alloy_backward.py   -> nh3_1_2/alloy_backward.csv, alloy_backward_summary.json
```

Both scripts call the ACSA self-check gate (`agent/selfcheck_gate.py`, which reproduces the hand-built 1.1 NH3, methanol and Au/TiO₂ cases) and then reproduce all 15 pure-metal deterministic costs of the selected run to < 1e-9 USD/t. With `NH3_MODEL=1.1` (default) they rewrite the files one level up unchanged (byte-identical after git's line-ending normalization). The response surface is read from the harness cache only; a missing or mismatched cache stops the run instead of rebuilding it.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

TM layer: transition metals only (no sp metal, no group 3–5 element), the layer the main text reports.

| Quantity | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| Fe comparator (USD/t NH₃) | 15.2917 | 11.5158 |
| Surfaces fetched / costed / not costed (Tc) | 1,796 / 1,695 / 101 | 1,796 / 1,695 / 101 |
| Descriptor bridge (slope, R², RMS eV; calibration.json) | 0.845, 0.973, 0.22 | 0.845, 0.973, 0.22 (file identical) |
| Pure-metal self-check (15 metals, abs. difference < 1e-9 USD/t vs the run's results.json) | True | True |
| TM layer: costed / feasible global / feasible anchored | 372 / 138 / 144 | 372 / 137 / 144 |
| TM layer: below Fe, global bridge | 5: Cu3Cr 14.36, Fe3Mo 14.53, Cu3Mo 14.83, Fe3W 14.90, Ni3W 15.08 | 8: Cu3Cr 10.14, Fe3Mo 10.17, Ni3W 10.84, Fe3W 10.94, Cu3Mo 10.94, Co3Mo 11.15, Co3W 11.32, Ni3Mo 11.46 |
| TM layer: below Fe, element-anchored bridge | 6: Cu3Cr 14.36, Cu3Mo 14.60, CuMo 14.70, MoNi 14.70, CoMo 15.07, CoW 15.16 | 9: Cu3Cr 10.13, Cu3Mo 10.28, CuMo 10.44, MoNi 10.47, CoMo 10.81, CoW 11.00, Fe3Mo 11.07, Ni3W 11.09, Fe3W 11.15 |
| TM layer: below Fe in both bridges | Cu3Cr, Cu3Mo | Cu3Cr, Fe3Mo, Ni3W, Fe3W, Cu3Mo |
| TM layer: every surface below Fe (either bridge) is cheap 3d + Cr/Mo/W | True | True |
| TM layer, global: highest-activity surface (673 K), economic rank, cost, regret | Os3Pt, 43 of 138, 24.55 USD/t, 70.9 % | Ni3Re, 12 of 137, 12.97 USD/t, 28.0 % |
| TM layer, global: economic winner | Cu3Cr 14.36 USD/t (activity rank 31) | Cu3Cr 10.14 USD/t (activity rank 45) |
| TM layer, anchored: highest-activity surface (673 K), economic rank, cost, regret | AuW, 40 of 144, 23.39 USD/t, 62.9 % | Rh3Re, 45 of 144, 18.94 USD/t, 86.9 % |
| TM layer, anchored: economic winner | Cu3Cr 14.36 USD/t (activity rank 40) | Cu3Cr 10.13 USD/t (activity rank 51) |
| TM layer: Spearman activity vs cost, global / anchored | 0.715 / 0.668 | 0.709 / 0.673 |
| TM layer: below Fe with every descriptor shifted −/+ propagated RMS (global) | 5 / 10 | 6 / 14 |
| Activity leaders (global / anchored): cost at the Fe price (USD/t) | Os3Pt 14.96 / AuW 14.99 | Ni3Re 10.15 / Rh3Re 10.33 |
| Activity leaders: activity multiple α* for Fe parity at own price | 688.8 / 405.2 | 5.53 / 421.1 |
| Activity leaders: price at Fe parity (USD/kg) | 69.9 / 61.6 | 481.5 / 332.2 |
| Activity leaders: lowest cost on the strict scaling range (USD/t) | 24.54 / 23.20 | 12.95 / 18.84 |
| Cu₃Cr (global): α* (activity it can lose and stay below Fe) | 0.2374 (24 %) | 0.1345 (13 %) |
| Cu₃Cr and Cu₃Mo below Fe in both bridges | True | True |
| Frozen 15-metal prices only: costed / feasible global / feasible anchored | 309 / 114 / 121 | 309 / 113 / 121 |
| Frozen 15-metal prices only: below Fe global / anchored | 4 / 5 | 7 / 8 |
| Frozen 15-metal prices only: pruned by the lower bound (false prunes) | 243 (78.6 %), 0 | 244 (79.0 %), 0 |
| Transition metals (no sp metal, no group 3–5 element): costed / feasible global / feasible anchored | 372 / 138 / 144 | 372 / 137 / 144 |
| Transition metals (no sp metal, no group 3–5 element): below Fe global / anchored | 5 / 6 | 8 / 9 |
| Transition metals (no sp metal, no group 3–5 element): pruned by the lower bound (false prunes) | 289 (77.7 %), 0 | 290 (78.0 %), 0 |
| + group 3–5 elements: costed / feasible global / feasible anchored | 912 / 222 / 232 | 912 / 222 / 232 |
| + group 3–5 elements: below Fe global / anchored | 13 / 16 | 18 / 20 |
| + group 3–5 elements: pruned by the lower bound (false prunes) | 772 (84.6 %), 0 | 774 (84.9 %), 0 |
| + sp metals (all priced surfaces): costed / feasible global / feasible anchored | 1,695 / 406 / 421 | 1,695 / 406 / 421 |
| + sp metals (all priced surfaces): below Fe global / anchored | 52 / 56 | 74 / 79 |
| + sp metals (all priced surfaces): pruned by the lower bound (false prunes) | 1,397 (82.4 %), 0 | 1,399 (82.5 %), 0 |
| Frozen-price layer, global: highest-activity surface, rank, regret, Spearman | Os3Pt, 32, 69.0 %, 0.78 | Ni3Re, 11, 27.6 %, 0.76 |
| Frozen-price layer, anchored: highest-activity surface, rank, regret, Spearman | AuW, 29, 60.2 %, 0.74 | Rh3Re, 34, 84.1 %, 0.76 |
| Lower-bound constant C0 (USD/t) | 11.0429 | 7.5093 |

## Counterfactual and backward design, NH3-FINAL-1.2 (`alloy_backward.csv`)

Fe: 11.5158 USD/t; Fe price 8.0 USD/kg.

| Surface | Bridge | Why picked | Cost (USD/t) | Optimum (°C, bar) | At Fe price | α* to Fe parity | Price at Fe parity (USD/kg) | Best on strict scaling range (USD/t) |
|---|---|---|---:|---|---:|---:|---:|---:|
| Cu3Cr | global | below Fe (anchored); below Fe (global) | 10.14 | 400, 90 | 10.08 | 0.1345 | 489.7 | 9.97 |
| Cu3Cr | anchored | below Fe (anchored); below Fe (global) | 10.13 | 400, 90 | 10.08 | 0.1336 | 493.3 | 9.97 |
| Fe3Mo | global | below Fe (anchored); below Fe (global) | 10.17 | 400, 95 | 9.97 | 0.1309 | 689.0 | 10.16 |
| Fe3Mo | anchored | below Fe (anchored); below Fe (global) | 11.07 | 425, 105 | 10.88 | 0.5403 | 121.9 | 10.16 |
| Ni3W | global | below Fe (anchored); below Fe (global) | 10.84 | 425, 105 | 10.26 | 0.3131 | 400.6 | 10.62 |
| Ni3W | anchored | below Fe (anchored); below Fe (global) | 11.09 | 425, 105 | 10.75 | 0.5409 | 207.0 | 10.62 |
| Fe3W | global | below Fe (anchored); below Fe (global) | 10.94 | 425, 105 | 10.33 | 0.4031 | 291.4 | 10.59 |
| Fe3W | anchored | below Fe (anchored); below Fe (global) | 11.15 | 425, 105 | 10.79 | 0.5964 | 177.9 | 10.59 |
| Cu3Mo | global | below Fe (anchored); below Fe (global) | 10.94 | 425, 105 | 10.66 | 0.4254 | 174.1 | 10.21 |
| Cu3Mo | anchored | below Fe (anchored); below Fe (global) | 10.28 | 400, 95 | 10.06 | 0.166 | 539.1 | 10.21 |
| Co3Mo | global | below Fe (global) | 11.15 | 425, 105 | 10.82 | 0.6044 | 152.2 | 10.35 |
| Co3Mo | anchored | below Fe (global) | 17.72 | 450, 90 | 16.10 | 83.42 | – | 10.35 |
| Co3W | global | below Fe (global) | 11.32 | 425, 110 | 10.84 | 0.7899 | 147.4 | 10.73 |
| Co3W | anchored | below Fe (global) | 18.72 | 450, 85 | 16.29 | 118.1 | – | 10.73 |
| Ni3Mo | global | below Fe (global) | 11.46 | 425, 110 | 11.14 | 0.9398 | 49.8 | 10.20 |
| Ni3Mo | anchored | below Fe (global) | 12.01 | 450, 110 | 11.75 | 2.585 | – | 10.20 |
| CuMo | global | below Fe (anchored) | 12.08 | 450, 110 | 11.72 | 2.135 | – | 10.41 |
| CuMo | anchored | below Fe (anchored) | 10.44 | 400, 100 | 10.08 | 0.203 | 530.7 | 10.41 |
| CoMo | global | below Fe (anchored) | 12.27 | 450, 110 | 11.75 | 2.646 | – | 10.48 |
| CoMo | anchored | below Fe (anchored) | 10.81 | 425, 105 | 10.26 | 0.2912 | 411.4 | 10.48 |
| MoNi | global | below Fe (anchored) | 12.35 | 450, 110 | 11.86 | 2.912 | – | 10.40 |
| MoNi | anchored | below Fe (anchored) | 10.47 | 400, 100 | 10.08 | 0.2122 | 517.1 | 10.40 |
| Ni3Re | global | highest activity (global) | 12.97 | 450, 135 | 10.15 | 5.535 | 481.5 | 12.95 |
| Ni3Re | anchored | highest activity (global) | 13.03 | 450, 135 | 10.13 | 5.603 | 474.9 | 12.95 |
| Rh3Re | global | highest activity (anchored) | 34.63 | 450, 185 | 11.89 | 5042 | – | 18.84 |
| Rh3Re | anchored | highest activity (anchored) | 18.94 | 450, 310 | 10.33 | 421.1 | 332.2 | 18.84 |
| CoW | global | below Fe (anchored) | 54.18 | 450, 595 | 48.68 | 281.3 | – | 11.00 |
| CoW | anchored | below Fe (anchored) | 11.00 | 425, 105 | 10.27 | 0.4446 | 359.8 | 11.00 |

## Full below-Fe lists, NH3-FINAL-1.2 (USD/t)

- **Frozen 15-metal prices only**, global (7): Fe3Mo 10.17, Ni3W 10.84, Fe3W 10.94, Cu3Mo 10.94, Co3Mo 11.15, Co3W 11.32, Ni3Mo 11.46
- **Frozen 15-metal prices only**, element-anchored (8): Cu3Mo 10.28, CuMo 10.44, MoNi 10.47, CoMo 10.81, CoW 11.00, Fe3Mo 11.07, Ni3W 11.09, Fe3W 11.15
- **Transition metals (no sp metal, no group 3–5 element)**, global (8): Cu3Cr 10.14, Fe3Mo 10.17, Ni3W 10.84, Fe3W 10.94, Cu3Mo 10.94, Co3Mo 11.15, Co3W 11.32, Ni3Mo 11.46
- **Transition metals (no sp metal, no group 3–5 element)**, element-anchored (9): Cu3Cr 10.13, Cu3Mo 10.28, CuMo 10.44, MoNi 10.47, CoMo 10.81, CoW 11.00, Fe3Mo 11.07, Ni3W 11.09, Fe3W 11.15
- **+ group 3–5 elements**, global (18): Cu3V 10.03, Fe3V 10.11, Cu3Cr 10.14, Fe3Mo 10.17, Cu3Nb 10.24, Fe3Ti 10.27, Fe3Nb 10.48, Cu3Ta 10.80, Fe3La 10.81, Cu3La 10.84, Ni3W 10.84, Fe3W 10.94, Cu3Mo 10.94, Co3Zr 11.00, Fe3Zr 11.11, Co3Mo 11.15, Co3W 11.32, Ni3Mo 11.46
- **+ group 3–5 elements**, element-anchored (20): Fe3Ti 9.98, Fe3Zr 10.02, Cu3V 10.03, Fe3V 10.05, Fe3La 10.08, Fe3Y 10.11, Cu3Cr 10.13, Fe3Nb 10.16, Cu3Nb 10.24, Cu3Mo 10.28, CuMo 10.44, MoNi 10.47, Fe3Ta 10.79, Cu3Ta 10.80, CoMo 10.81, Cu3La 10.84, CoW 11.00, Fe3Mo 11.07, Ni3W 11.09, Fe3W 11.15
- **+ sp metals (all priced surfaces)**, global (74): Al3Ti 9.41, Al3Cu 9.51, AlCr 9.71, Al 9.72, Al3Zr 9.72, Al3La 9.73, Al3Y 9.80, Zn3V 9.93, CrZn 9.97, Cu3V 10.03, Al3Pb 10.04, Zn3Nb 10.06, Fe3V 10.11, Cu3Cr 10.14, Cd3V 10.14, Al3Ni 10.14, Fe3Mo 10.17, SnTi 10.22, Cu3Nb 10.24, Fe3Ti 10.27, Cr3Pb 10.29, AlMo 10.34, Al3Bi 10.35, Al3Cd 10.35, Cd3Mo 10.36, LaSn 10.41, SnY 10.46, Zn3Mo 10.46, Fe3Nb 10.48, CdMo 10.49, PbY 10.49, SnZr 10.51, Cd3Cr 10.56, MoZn 10.56, Cd3Nb 10.64, Zn3Cr 10.65, Al3In 10.68, CrSn 10.76, NbSn 10.76, BiV 10.77, HgY 10.80, Cu3Ta 10.80, Fe3La 10.81, Cu3La 10.84, Ni3W 10.84, Al3Sn 10.87, Pb3Cr 10.91, NbPb 10.92, Fe3W 10.94, Cu3Mo 10.94, BiZr 10.99, Co3Zr 11.00, Bi3Nb 11.01, CrPb 11.04, Al3Ta 11.06, Hg3W 11.08, Fe3Zr 11.11, BiLa 11.13, InNb 11.13, Co3Mo 11.15, Zn3Ti 11.16, BiNb 11.18, Sn3W 11.19, LaPb 11.20, GaNb 11.26, BiTi 11.30, Co3W 11.32, Pb3Nb 11.33, GaV 11.35, Fe3Al 11.37, BiY 11.41, PbTi 11.45, Ni3Mo 11.46, Fe3Zn 11.49
- **+ sp metals (all priced surfaces)**, element-anchored (79): Al3Ti 9.41, Al3Cu 9.51, AlCr 9.71, Al 9.72, Al3Zr 9.72, Al3La 9.73, Al3Y 9.80, Zn3V 9.93, CrZn 9.97, Fe3Ti 9.98, Fe3Zr 10.02, Cu3V 10.03, Al3Pb 10.04, Fe3V 10.05, Zn3Nb 10.06, Fe3La 10.08, Fe3Y 10.11, Cu3Cr 10.13, Cd3V 10.14, Al3Ni 10.14, Fe3Nb 10.16, SnTi 10.22, Cu3Nb 10.24, Cu3Mo 10.28, Cr3Pb 10.29, Al3Bi 10.35, Al3Cd 10.35, Cd3Mo 10.37, LaSn 10.41, CuMo 10.44, SnY 10.46, MoNi 10.47, PbY 10.49, SnZr 10.51, Cd3Cr 10.56, Cd3Nb 10.64, Zn3Cr 10.65, Al3In 10.68, Mo3Pb 10.69, Mo3Sn 10.70, CrSn 10.76, NbSn 10.76, BiV 10.77, Fe3Ta 10.79, HgY 10.80, Cu3Ta 10.80, CoMo 10.81, Zn3Mo 10.83, Cu3La 10.84, AlMo 10.86, Al3Sn 10.87, CdMo 10.88, Pb3Cr 10.91, NbPb 10.92, Zn3W 10.94, AlW 10.94, BiZr 10.99, CoW 11.00, Bi3Nb 11.01, CrPb 11.04, Al3Ta 11.06, Fe3Mo 11.07, Ni3W 11.09, BiLa 11.13, InNb 11.13, Fe3W 11.15, Zn3Ti 11.16, WZn 11.16, BiW 11.16, BiNb 11.18, MoZn 11.18, LaPb 11.20, Hg3W 11.22, GaNb 11.26, BiTi 11.30, Pb3Nb 11.33, GaV 11.35, BiY 11.41, PbTi 11.45

## What moved

- Fe falls from 15.29 to 11.52 USD/t (× 0.753). Alloy costs fall at and around the volcano peak and on the weak-binding side, and some rise on the strong-binding side. On the surfaces with a cost in both versions (`alloy_chain_results.csv` one level up and here), 336 of 404 get cheaper on the global bridge and 361 of 421 on the anchored bridge. Every surface with E_N_step above −1.36 eV gets cheaper (298 global, 317 anchored). The 68 global surfaces that cost more (33 in the TM layer) and the 60 anchored ones (26 TM) are all strong binders: E_N_step −1.565 to −1.361 eV on the global bridge and −1.569 to −1.363 eV on the anchored bridge. Their 673 K activity rises by only 0.03–0.12 decades under 1.2, against up to 1.00 decade near the peak. Examples, global bridge, 1.1 → 1.2 USD/t: NiW 85.86 → 110.04, Cu₃W 69.48 → 82.64, CrCu 35.73 → 37.77, Ru₃Ti 1,757 → 1,985. The 1.2/1.1 cost ratio runs from 0.679 (Al₃Ti) to 1.282 (NiW) on the global bridge and from 0.679 to 1.142 (Ir₃La) on the anchored bridge.
- The transition-metal surfaces below Fe grow from 5 to 8 (global) and from 6 to 9 (anchored). Every one of them still pairs Fe, Co, Ni or Cu with Cr, Mo or W, and Cu₃Cr is still the cheapest transition-metal surface in both bridges.
- The 673 K activity maximum on the descriptor grid moves from E_N −1.18 eV (1.1) to −1.15 eV (1.2). The six most active transition-metal surfaces differ by at most 0.029 decades in activity, so the highest-activity surface changes identity: Os3Pt → Ni3Re (global) and AuW → Rh3Re (anchored); the selection rule is unchanged. Ni3Re was already 6th by activity and 12th by cost in 1.1 (16.93 USD/t). Under 1.2 it ranks 12th economically (12.97 USD/t, regret 28.0 %) and needs a 5.5-fold activity gain at its own price; Rh3Re ranks 45th (86.9 % regret) and needs 421-fold. Both undercut Fe at the Fe price (10.15 and 10.33 USD/t), and neither reaches Fe at its own price anywhere on the strict scaling range (12.95 and 18.84 USD/t at best).
- On the global bridge two strong-binding TM surfaces leave the 90 m³ cap and one weak binder enters. The two that leave are Re₃Ir (E_N_step −1.541 eV, 3,017 USD/t under 1.1) and OsW (−1.541 eV, 3,112 USD/t under 1.1). The one that enters is Ir₃W (−0.565 eV, 8,807 USD/t under 1.2). The weak binder Pd₃Nb (−0.538 eV, 1,491 USD/t under 1.2) also enters, in the group 3–5 layer. The feasible counts of that layer and of all priced surfaces therefore stay at 222 and 406. The anchored-bridge feasible sets do not change. The descriptor bridge, the element offsets and the 1,695 / 372 costed counts are unchanged.
