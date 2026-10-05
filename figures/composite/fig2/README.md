# Figure 2 — composite

Metal cost and process reoptimization jointly define the ammonia decision boundary.
183 × 170 mm, eight panels: `Fig2.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | NH3 synthesis loop: fresh-feed compressor, converter, chiller, separator, recycle compressor; the cost pools each unit carries and the decision variables T, P, T_sep | schematic |
| b | catalyst bed at the Fe, Ru and Ru-priced-as-Fe optima, to scale (L/D = 3), with operating state and metal-inventory cost | `renders/bed_*.png`, `fig2_pressure_envelopes.csv` |
| c | lowest feasible cost against synthesis pressure, T and T_sep reoptimized, for Fe, Ru, Os and Ru priced as Fe | `fig2_pressure_envelopes.csv` |
| d | Ru at its actual catalyst cost: Ru reoptimized over all 14,136 states against the effective metal price p(1−r)/u, with pure Ru, supported Ru/C, Ru/C with 90–94% recovery and the KAAP loop marked; below, the Ru activity multiple needed for parity at each effective price | `fig2_ru_price_sweep.csv`, `fig2_ru_actual_cost_points.csv`, `fig2_ru_alpha_sweep.csv` |
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

## Ru at its actual catalyst cost (panel d, 2026-10-05)

The ammonia process–economics model gives every metal the fused-iron formulation: one global calibration (Fe, 65 m³ bed at 400 °C
and 80 bar) maps per-site TOF to kilograms of active metal, the bed is 71.51 wt% metal at 2,500 kg m⁻³, and
spent metal is not recovered. `fig2_ru_actual_cost.py` reads the same frozen harness and places a real Ru
catalyst on the price axis. A supported catalyst exposing u times more of its metal atoms than fused iron
needs 1/u of the metal; recovering a fraction r leaves a net metal charge equal to the benchmark at the
effective price p_eff = p (1 − r) / u.

| Input | Value | Source |
|---|---|---|
| Ru dispersion, promoted Ru/C (3.2 wt% Ru) | 11% (O₂ chemisorption) | Rossetti *et al.*, *Ind. Eng. Chem. Res.* **45**, 4150 (2006) |
| exposed Fe atoms, reduced fused-iron catalyst | < 1% | Liu *et al.*, *CIESC J.* **51**, 462 (2000) |
| u (lower bound) | 0.11 / 0.01 = 11 | — |
| Ru recovered from spent promoted Ru catalyst | > 94% | US 6,673,732 B2 (Haldor Topsoe, 2004) |
| KAAP loop | 9.1 MPa, condenser −20 °C (grid 90 bar, −20 °C) | Humphreys *et al.*, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021) |

| Case | p_eff (USD/kg) | Cost (USD/t) | vs Fe | α* for parity | Optimum |
|---|---|---|---|---|---|
| pure Ru, benchmark | 53,852.5 | 22.031 | +6.739 | 201.2 | 450 °C, 425 bar, T_sep 25 °C |
| Ru/C, no recovery | 4,895.7 | 17.950 | +2.658 | 18.48 | 450 °C, 220 bar, 20 °C |
| Ru/C, 90% recovery | 489.6 | 15.671 | +0.379 | 2.234 | 450 °C, 200 bar, 30 °C |
| Ru/C, 94% recovery | 293.7 | 15.485 | +0.193 | 1.494 | 450 °C, 195 bar, 30 °C |
| KAAP loop, Ru/C, 90% recovery | 489.6 | 18.910 | Fe in loop 19.069 | — | 425 °C, 90 bar, −20 °C |
| KAAP loop, Ru/C, 94% recovery | 293.7 | 18.529 | Fe in loop 19.069 | — | 400 °C, 90 bar, −20 °C |

Parity (164 USD/kg) needs u = 19.7 at 94% recovery and u = 32.9 at 90%. The audited strict-scaling lifecycle boundary (`analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`) places scaling-consistent parity at p_eff ≤ 237.3 USD/kg; Ru/C reaches it at u ≥ 13.6 (94% recovery) or u ≥ 22.7 (90%). Panel d shades that range. In the KAAP loop the Ru/C catalyst
with recovery is 0.16–0.54 USD/t cheaper than fused iron in the same loop. α* is recomputed with full
reoptimization at every price (`fig2_ru_alpha_sweep.csv`) and reproduces the canonical 201.22 at the frozen
price. The supported bed is larger than the benchmark bed; `fig2_ru_bed_sensitivity.csv` recomputes the
reactor term with the bed of a 3.2 wt% Ru catalyst at 500–1,000 kg m⁻³ (5–10 times the benchmark volume),
which adds 0.15–0.83 USD/t.

## Beds

`build_beds.py` fills a cylinder of the optimum bed volume and the converter's L/D = 3 with pellets
of one common, illustrative size (0.06 m), and renders all three with one orthographic camera and
field of view, so the relative sizes in panel b are exact. Pellet size is not a model quantity.

## Build

```
CatalystForge/.venv/python   fig2_model.py      # frozen harness -> fig2_*.csv
CatalystForge/.venv/python   fig2_ru_actual_cost.py   # same harness -> fig2_ru_{alpha_sweep,actual_cost_points,bed_sensitivity}.csv
render-venv/python           build_beds.py      # OVITO 3.16, Tachyon, ambient occlusion
pur_bridge_env/python        make_fig2.py       # -> Fig2.svg / .pdf / .png
```

`make_fig2.py` imports the shared visual system in `../style.py`.
