# Figure 3 — composite

Backward design separates the activity economics requires from the activity the material can reach.
183 × 122 mm, five panels: `Fig3.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | the backward-design question: Ru step site, activity multiplier α, full process reoptimization, parity with the Fe optimum | schematic; step-site renders from `../fig1/renders` |
| b | required and reachable activity on one axis: the 5,000-draw α\* distribution (p05 70.8, canonical 201.2, p95 462) against the scaling-line peak (1.09×), the direct DFT check (1.84×) and the best over all process states (2.52×); top axis k_BT ln α at 673 K | `nh3_cost_mc_histogram.csv`, `nh3_cost_mc_summary.json`, `headline_1_1.json`, `results.json` |
| c | Ru reoptimized cost against α with the optimal pressure it moves through; at α\* Ru sits at 425 °C, 190 bar, T_sep 30 °C | `closure/breakeven_sweep.csv`, `headline_1_1.json` |
| d | activity gain along the strict scaling line at 673 K against the required band | `closure/scaling_reachability.csv` |
| e | lowest feasible Ru cost along the scaling line: 21.40 USD/t at E_N = −1.215 eV, 6.11 above Fe | `closure/scaling_reachability.csv` |

All inputs are pinned NH3-FINAL-1.1 provenance
(`provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/`) or the preregistered
joint cost Monte Carlo (`analysis/supervisor_2026_09_20/`); `make_fig3.py` asserts α\* = 201.2234,
the 2.5246 headroom, p05 = 70.78 and the 5,000-draw total before drawing.

The top axis of panel b is a unit conversion, ΔE = k_BT ln α at the 673 K atomic reference
temperature: 2.52× corresponds to 0.054 eV, 70.8× to 0.247 eV and 201× to 0.308 eV.

## Build

```
pur_bridge_env/python   make_fig3.py      # -> Fig3.svg / .pdf / .png
```
