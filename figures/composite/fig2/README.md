# Figure 2 — composite (manuscript Fig. 3)

Metal cost and process reoptimization jointly define the ammonia decision boundary.
183 × 170 mm, eight panels: `Fig2.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | NH3 synthesis loop: fresh-feed compressor, converter, chiller, separator, recycle compressor; the cost pools each unit carries and the decision variables T, P, T_sep | schematic |
| b | catalyst bed at the Fe, Ru and Ru-priced-as-Fe optima, to scale (L/D = 3), with operating state and metal-inventory cost | `renders/bed_*.png`, `fig2_pressure_envelopes.csv` |
| c | lowest feasible cost against synthesis pressure, T and T_sep reoptimized, for Fe, Ru, Os and Ru priced as Fe | `fig2_pressure_envelopes.csv` |
| d | Ru at its actual catalyst cost: Ru reoptimized over all 14,136 states against the effective metal price p(1−r)/u, with pure Ru, supported Ru/C, Ru/C with 90–97% recovery and the KAAP loop marked (circles and diamonds: benchmark formulation; squares: the commercial Ru/C catalyst's own bed at 8 wt% Ru and 490 kg m⁻³, bars over 5–10 wt% and 430–550 kg m⁻³); below, the Ru activity multiple needed for parity at each effective price, with the own-bed range | `fig2_ru_price_sweep.csv`, `fig2_ru_actual_cost_points.csv`, `fig2_ru_alpha_sweep.csv`, `fig2_ru_bed_sensitivity.csv` |
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
| Ru recovered from spent activated-carbon-supported Ru ammonia catalyst | 89–97.6% → r = 0.90–0.97 | CN 1872418 A |
| Ru content of the commercial Ru/C ammonia catalyst | ~8 wt% (5–10 wt%) | Brown *et al.*, *Catal. Lett.* **144**, 545 (2014); US 4,600,571 |
| bed (bulk) density of the supported Ru/C bed | 430–550 kg m⁻³ (centre 490) | derived; no published value |
| KAAP loop | 9.1 MPa, condenser −20 °C (grid 90 bar, −20 °C) | Humphreys *et al.*, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021) |

Until 2026-10-07 the recovery was 0.90–0.94 (US 6,673,732 B2), the own bed 3.2 wt% Ru (Rossetti 2006 laboratory
catalyst) at 500–1,000 kg m⁻³; those outputs are reproduced exactly by the pre-change script in GitHub Actions run
[37648545590](https://github.com/stloendays/Catalyst-Essay/actions/runs/37648545590) before the literature values
are applied (`analysis/nh3_mc_ru_actual_2026_10_06/ci_logs/validate_baseline.log`).

| Case | p_eff (USD/kg) | Cost (USD/t) | vs Fe | α* for parity | Optimum |
|---|---|---|---|---|---|
| pure Ru, benchmark | 53,852.5 | 22.031 | +6.739 | 201.2 | 450 °C, 425 bar, T_sep 25 °C |
| Ru/C, no recovery | 4,895.7 | 17.950 | +2.658 | 18.48 | 450 °C, 220 bar, 20 °C |
| Ru/C, 90% recovery | 489.6 | 15.671 | +0.379 | 2.234 | 450 °C, 200 bar, 30 °C |
| Ru/C, 97% recovery | 146.9 | 15.237 | −0.054 | 0.936 | 425 °C, 185 bar, 30 °C |
| KAAP loop, Ru/C, 90% recovery | 489.6 | 18.910 | Fe in loop 19.069 | — | 425 °C, 90 bar, −20 °C |
| KAAP loop, Ru/C, 97% recovery | 146.9 | 18.157 | Fe in loop 19.069 | — | 400 °C, 90 bar, −20 °C |

Parity (164 USD/kg) needs u = 9.9 at 97% recovery and u = 32.9 at 90%. The audited strict-scaling lifecycle boundary (`analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`) places scaling-consistent parity at p_eff ≤ 237.3 USD/kg; Ru/C reaches it at u ≥ 6.8 (97% recovery) or u ≥ 22.7 (90%). Panel d shades that range. In the KAAP loop the Ru/C catalyst
with recovery, read on the benchmark formulation, is 0.16–0.91 USD/t cheaper than fused iron in the same loop. α* is
recomputed with full reoptimization at every price (`fig2_ru_alpha_sweep.csv`) and reproduces the canonical 201.22 at
the frozen price.

### The Ru/C catalyst's own bed (2026-10-07, literature loading and bed density)

The rows above read the price sweep on the benchmark formulation: the Ru/C catalyst is charged at p_eff, but its bed
keeps the fused-iron formulation (71.51 wt% metal at 2,500 kg m⁻³) and the volume of the undivided metal mass. The
commercial catalyst carries m_Ru / u of Ru at 5–10 wt% (8 wt% central) in a 430–550 kg m⁻³ bed.
`fig2_ru_bed_sensitivity.csv` evaluates that bed with full reoptimization for w ∈ {5, 8, 10} wt% × ρ ∈ {430, 490, 550}
kg m⁻³ and gives, for each row, the Fe reference of the same loop and the Ru activity multiple α* for parity with it.
Panel d shows a square at 8 wt% and 490 kg m⁻³ and a bar over the 5–10 wt%, 430–550 kg m⁻³ corners (the cost falls
monotonically in w and ρ).

| Ru/C (u = 11) | Benchmark formulation | Own bed, 8 wt%, 490 kg m⁻³ | 8 wt%, 430–550 | 5–10 wt%, 430–550 | Fe in the same loop | α* own bed, 8 wt% (430–550) |
|---|---:|---:|---:|---:|---:|---:|
| no recovery | 17.950 | 18.064 | 18.049–18.084 | 18.023–18.178 | 15.292 | 19.8–20.2 |
| 90% recovery | 15.671 | 15.962 | 15.922–16.012 | 15.856–16.242 | 15.292 | 3.26–3.64 |
| 97% recovery | 15.237 | 15.671 | 15.627–15.727 | 15.547–15.994 | 15.292 | 1.96–2.35 |
| KAAP loop, 90% recovery | 18.910 | 19.054 | 19.034–19.079 | 19.001–19.204 | 19.069 | 0.95–1.02 |
| KAAP loop, 97% recovery | 18.157 | 18.549 | 18.492–18.624 | 18.399–18.895 | 19.069 | 0.46–0.53 |

At 8 wt% the recovered Ru/C catalyst costs 15.63–16.01 USD/t on its own bed in the full process space, 0.33–0.72 above
Fe (benchmark reading 15.24–15.67, −0.05 to +0.38), and needs 1.96–3.64 times the activity of the frozen Ru descriptor
for parity (benchmark reading 0.94–2.23); over 5–10 wt% it costs 15.55–16.24. In the KAAP loop it costs 18.49–19.08
against 19.07 for Fe in the same loop (−0.58 to +0.01; below Fe at 3 of the 4 corners, at every corner with 97%
recovery), α* 0.46–1.02; over 5–10 wt% 18.40–19.20. The own bed adds 0.10–0.13 USD/t without recovery and 0.25–0.49
with 90–97% recovery (0.12–0.47 in the KAAP loop) to the benchmark reading at 8 wt% (0.07–0.23, 0.19–0.76 and
0.09–0.74 over 5–10 wt%).

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
