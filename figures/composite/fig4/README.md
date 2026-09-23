# Figure 4 — composite

Methanol catalyst states re-rank through a selectivity–recycle pathway.
183 × 168 mm, seven panels: `Fig4.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | CO2-to-methanol loop: feed compressor, Re/TiO2 reactor, flash, distillation, purge split, recycle compressor; the purge fraction as the loop's free variable; the pathway S_CH4 → CH4 in the loop → recycle and purge losses → H2 feed and compression | schematic |
| b | Re/TiO2 at 1 and 5 wt% Re (schematic surfaces, Re atoms 1 : 5 on the same area) | `renders/ReTiO2_*.png` from `build_re_tio2.py` |
| c | the four states from measured catalyst metrics (STY per g Re, CO2 conversion, CH4 selectivity) through the loop at 2 % purge (CH4 in the loop gas, recycle flow, H2 feed cost) to net production cost | `data/meoh/meoh_candidate_ranking_D01v3.csv` |
| d | rank probability across the 5,000-draw cost analysis; identical for the canonical D01 boundary and the active-Re replacement extension | `analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv` |
| e | STY-per-g-Re rank against net-cost rank: ρ = 0.20, τ = 0.00, 3 of 6 pairs inverted | `meoh_candidate_ranking_D01v3.csv`, `meoh_candidate_ranking_D01v3_provenance.json` |
| f | net cost over 396 purge levels, 0.5–40 %, and the Spearman ρ at each (maximum 0.40) | `data/meoh/meoh_purge_robustness_D01v3.csv` |
| g | local economic leverage at 5 wt% Re, 250 °C: CH4 suppression 0.37579, single-pass conversion 0.05883, STY 0.00289 | `meoh_candidate_ranking_D01v3.csv` |

Catalyst metrics are Gothe et al., ACS Catal. 2025, Table 3 (100 bar, CO2 : H2 = 1 : 4); the loop
model is the frozen D01 v3 explicit recycle/separation workbook, anchored to Processes 2022, 10,
1535 at 2 % purge. `make_fig4.py` asserts the economic and upstream orders, the 396 purge levels
and that both rank-probability matrices are the identity before drawing.

The same red marks the state that moves from upstream #3 to economic #1, as Fe does in Figure 1.

## Structures

`build_re_tio2.py` builds a stoichiometric rutile TiO2(110) slab (three O–Ti2O2–O trilayers with the
bridging-O rows on top) and places compact hcp Re clusters on it: 12 Re atoms for 1 wt%, 60 for
5 wt%, with the higher loading drawn as fewer isolated atoms and larger clusters, following the D01
case note that Re loading sets dispersion. Both surfaces use one camera. Cluster sizes and the
support facet are illustrative, not characterization data.

## Build

```
render-venv/python      build_re_tio2.py     # OVITO 3.16, Tachyon, ambient occlusion
pur_bridge_env/python   make_fig4.py         # -> Fig4.svg / .pdf / .png
```
