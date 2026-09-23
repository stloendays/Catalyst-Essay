# Figure 2 — composite

Metal cost and process reoptimization jointly define the ammonia decision boundary.
183 × 170 mm, eight panels: `Fig2.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | NH3 synthesis loop: fresh-feed compressor, converter, chiller, separator, recycle compressor; the cost pools each unit carries and the decision variables T, P, T_sep | schematic |
| b | catalyst bed at the Fe, Ru and Ru-priced-as-Fe optima, to scale (L/D = 3), with operating state and metal-inventory cost | `renders/bed_*.png`, `fig2_pressure_envelopes.csv` |
| c | lowest feasible cost against synthesis pressure, T and T_sep reoptimized, for Fe, Ru, Os and Ru priced as Fe | `fig2_pressure_envelopes.csv` |
| d | Ru reoptimized over all 14,136 states as its metal price varies, and the optimal pressure it moves to | `fig2_ru_price_sweep.csv` |
| e | where the canonical 6.739 USD/t Ru − Fe gap sits, and the equal-price intervention | `analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv` |
| f | the 1,000 frozen descriptor draws in (Fe E_N, Ru E_N), coloured by economic winner, with the Fe bed-feasibility interval | `closure/mc_draws.csv` |
| g | decision endpoints across those draws | `analysis/supervisor_2026_09_20/f3_panel_summary.csv` |
| h | Ru − Fe cost gap across the 5,000 preregistered joint cost draws | `analysis/supervisor_2026_09_20/nh3_cost_mc_histogram.csv` |

## Model tables

`fig2_model.py` runs the frozen NH3-FINAL-1.1 harness
(`Catalyst_Economic_Leverage_Automation_Harness_v0.1`, canonical manifest
`outputs/nh3_final_20260905T134204Z/manifest_resolved.yaml`, cached 14,136-state response surface;
it refuses to rebuild the cache). Before writing anything it reproduces the frozen optima:

| Case | Cost (USD/t NH3) | T (°C) | P (bar) | T_sep (°C) | Bed (m³) |
|---|---|---|---|---|---|
| Fe | 15.291705 | 425 | 180 | 30 | 17.06 |
| Ru | 22.030595 | 450 | 425 | 25 | 0.066 |
| Os | 25.831797 | 450 | 425 | 0 | 0.029 |
| Ru at 8 USD/kg | 14.712130 | 425 | 170 | 30 | 9.42 |

The same harness gives the price sweep in panel d. Ru cost rises monotonically with its metal price
and equals the Fe optimum at **163.76 USD/kg** (425 °C, 185 bar, T_sep 30 °C, 6.24 m³ bed), 329 times
below the canonical 53,852.5 USD/kg. Along the sweep the optimum moves from 170 bar and a 9.4 m³ bed
at 1 USD/kg to 420–430 bar, T_sep 0 °C and a 0.014 m³ bed at 3 × 10⁵ USD/kg: a dearer metal is
answered by a smaller bed bought with compression and refrigeration.

Cost pools in panel e are read from the frozen supervisor decomposition; `make_fig2.py` asserts that
they equal the harness recomputation to 1e-9 USD/t.

## Beds

`build_beds.py` fills a cylinder of the optimum bed volume and the converter's L/D = 3 with pellets
of one common, illustrative size (0.06 m), and renders all three with one orthographic camera and
field of view, so the relative sizes in panel b are exact. Pellet size is not a model quantity.

## Build

```
CatalystForge/.venv/python   fig2_model.py      # frozen harness -> fig2_*.csv
render-venv/python           build_beds.py      # OVITO 3.16, Tachyon, ambient occlusion
pur_bridge_env/python        make_fig2.py       # -> Fig2.svg / .pdf / .png
```

`make_fig2.py` imports the shared visual system in `../style.py`.
