# Supervisor NH3 cost analyses on NH3-FINAL-1.2

Same definitions as the NH3-FINAL-1.1 files one folder up (`../README.md` sections 1, 2 and 4,
`docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md`), run on NH3-FINAL-1.2 (Gillespie–Beattie NH₃ formation free energy,
Newton–Cooper fugacities in the loop and the microkinetics, F_CAL 74,351.6; canonical run `nh3_final_1_2_20261013`).
Nothing is re-chosen: the counterfactual is still Ru at the Fe metal price (8 USD/kg) with Ru re-optimized over the
full library; the cost MC keeps the prior, N = 5,000 and seed 20260920 and re-optimizes Fe and Ru over the 1.2
library in every draw; alpha* is solved against each draw's re-optimized Fe cost.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness
    python -X utf8 analysis/supervisor_2026_09_20/nh3_supervisor_cost.py

With `NH3_MODEL=1.1` the same script recomputes the frozen files and compares them
(`../nh3_v11_reproduction_check.json`); it never overwrites them.

| Quantity | NH3-FINAL-1.1 | **NH3-FINAL-1.2** | Unit |
|---|---:|---:|---|
| Process states | 14,136 | **14,510** |  |
| Fe canonical cost / optimum | 15.2917 / 425 °C, 180 bar, 30 °C | **11.5158 / 425 °C, 105 bar, 30 °C** | USD t⁻¹ |
| Ru canonical cost / optimum | 22.0306 / 450 °C, 425 bar, 25 °C | **16.6327 / 450 °C, 220 bar, 30 °C** | USD t⁻¹ |
| Ru − Fe, canonical | 6.7389 | **5.1170** | USD t⁻¹ |
|   Ru − Fe: metal_inventory | 1.7630 | **1.6941** | USD t⁻¹ |
|   Ru − Fe: reactor_base | -0.0857 | **-0.1174** | USD t⁻¹ |
|   Ru − Fe: vessel_pressure_premium | -0.7331 | **-0.7875** | USD t⁻¹ |
|   Ru − Fe: fresh_compression_electricity | 4.6317 | **3.9876** | USD t⁻¹ |
|   Ru − Fe: recycle_compression_electricity | -0.6468 | **-0.6844** | USD t⁻¹ |
|   Ru − Fe: refrigeration_electricity | 0.6291 | **0.0000** | USD t⁻¹ |
|   Ru − Fe: compressor_CAPEX | 1.1807 | **1.0245** | USD t⁻¹ |
| Ru at Fe metal price (8 USD/kg), re-optimized | 14.7121 / 425 °C, 170 bar, 30 °C | **10.2368 / 400 °C, 95 bar, 30 °C** | USD t⁻¹ |
| Ru(equal price) − Fe | -0.5796 | **-1.2790** | USD t⁻¹ |
| Economic order after equalization | Ru < Fe | **Ru < Fe** |  |
| Cost MC: P(C_Fe < C_Ru) | 5,000/5,000 = 1.000 | **5,000/5,000 = 1.000** |  |
| Cost MC: minimum Ru − Fe | 2.382 | **1.995** | USD t⁻¹ |
| Cost MC: Ru − Fe p05 / median / p95 | 3.488 / 7.110 / 11.379 | **2.898 / 5.464 / 8.780** | USD t⁻¹ |
| Cost MC: Fe cost p05 / median / p95 | 9.596 / 17.546 / 24.819 | **7.310 / 13.178 / 18.522** | USD t⁻¹ |
| Cost MC: Ru cost p05 / median / p95 | 13.241 / 24.919 / 35.478 | **10.405 / 18.812 / 26.780** | USD t⁻¹ |
| Cost MC: alpha* p05 / median / p95 | 70.78× / 174.27× / 462.00× | **43.52× / 104.97× / 262.28×** |  |
| Cost MC: alpha* mean / min / max | 205.81× / 41.01× / 878.97× | **121.63× / 28.10× / 483.86×** |  |
| Cost MC: P(Ru ≤ Fe at alpha = 1) | 0.000 | **0.000** |  |
| alpha* canonical (results.json) | 201.22× | **114.67×** |  |
| Descriptor MC: Fe feasible | 0.799 | **0.792** | 1,000 draws |
| Descriptor MC: Fe economic Top-1 | 0.681 | **0.653** | 1,000 draws |
| Descriptor MC: atomic Top-1 = economic Top-1 | 0.282 | **0.271** | 1,000 draws |
| Descriptor MC: Fe Top-3 actionable | 0.940 | **0.923** | 1,000 draws |

Files (same names and schema as the 1.1 files):

- `nh3_ru_price_equalization.json`, `nh3_cost_decomposition.csv` — canonical pools and the equal-price counterfactual.
- `nh3_cost_mc_summary.json`, `nh3_cost_mc_histogram.csv` — joint cost MC. The key
  `full_14136_state_direct_cost_verification` keeps its 1.1 name so readers work unchanged; the library here has
  14,510 states (`process_state_count`).
- `f3_panel_summary.csv` — the metric table `figures/nh3/render_F03_uncertainty_cost_mc.R` reads (descriptor MC
  values from the 1.2 closure `mc_detail` / `mc_draws.csv`, cost MC values from this run).
- `nh3_cost_mc_draws.csv` — the draw-level table (prereg output 4; sampled parameters, re-optimized costs, alpha*,
  optimum states).

Checks in this run against the 1.2 `results.json`: |Fe cost error| = 0.0e+00, |Ru cost error| = 0.0e+00 USD t⁻¹; optimum states match: True;
canonical cost pools equal its `breakdown` blocks: True. alpha* on the non-dominated
Ru states vs the full library, 199 draws: max relative error 0.0e+00.

## F03 renderer

`figures/nh3/render_F03_uncertainty_cost_mc.R` reads `f3_panel_summary.csv` (all 11 metrics),
`nh3_cost_mc_histogram.csv` (both histograms) and the MeOH `../meoh_rank_probability_matrix.csv` (unchanged by the
NH3 model), with paths fixed to the 1.1 folder. It stops unless Fe economic Top-1 = 0.681, Top-1 survival = 0.282
and P(C_Fe < C_Ru) = 1, and types "68.1%", "28.2%" and "5,000/5,000" into the panel text; on 1.2 the first two
are 0.653 and 0.271. It does not read the price-equalization JSON, the decomposition CSV or the cost MC summary JSON.
