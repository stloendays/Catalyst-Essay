# Figure 5 — composite

Catalyst-to-process coupling topology decides whether an upstream ranking reshapes or survives.
183 × 164 mm, six panels: `Fig5.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | the two pathways, each against its own economic objective. NH3: metal price and intrinsic activity set the catalyst inventory, which the optimizer trades against the operating regime; edges into the decision are scaled by each cost pool's Ru − Fe contribution. MeOH: CH4 selectivity, conversion and STY act through CH4 in the loop gas, recycle flow, purge losses and catalyst mass on the D01 cost modules; catalyst edges are scaled by local leverage | `analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv`; `data/meoh/meoh_d01_v3.json` (module drivers); `data/meoh/meoh_candidate_ranking_D01v3.csv` (leverage) |
| b | the Au/TiO2 CO-oxidation control: 2–6 nm Au particles on one support, to scale | `renders/Au_TiO2_2to6nm.png` from `build_au_tio2.py` |
| c | activity rank against catalyst-burden rank: no crossings, ρ = τ = 1.000, order kept in 10,000 / 10,000 literature-envelope draws; 6 nm needs 8.064× the catalyst of 2 nm | `data/rank_preservation_control_v1_1.csv`, `docs/RANK_PRESERVATION_CONTROL_V1_1_RESULT.md` |
| d | mass activity and required catalyst mass against Au diameter | `data/rank_preservation_control_v1_1.csv` |
| e | the semi-open extension: exact order kept under mild, moderate and strong candidate-specific freedom, 273–293 K and 273–313 K | `data/rank_preservation_semiopen_v1_3_summary.csv` |
| f | upstream-to-downstream ρ for the three systems: NH3 all 15 metals 0.929 and frontier top 3 −0.50; MeOH 0.20 at 2 % purge (−0.6 to 0.4 over 0.5–40 %); Au control 1.000, semi-open moderate mean 0.992 | values as reported in the manuscript and the sources above |

Absolute NH3 and MeOH costs are never compared; each graph carries only its own reaction's
quantities. `make_fig5.py` asserts the Ru − Fe total (6.7389 USD/t), the D01 module drivers it
draws and the five control diameters.

## Structures

`build_au_tio2.py` cuts fcc Au (a = 4.078 Å) into truncated octahedra with a (111) base, about 2,
3, 4, 5 and 6 nm wide (155 to 5,507 atoms), and sets them on one stoichiometric rutile TiO2(110)
support under one camera. Shapes are illustrative, not characterization data.

## Build

```
render-venv/python      build_au_tio2.py     # OVITO 3.16, Tachyon, ambient occlusion
pur_bridge_env/python   make_fig5.py         # -> Fig5.svg / .pdf / .png
```
