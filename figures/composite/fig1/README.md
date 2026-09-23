# Figure 1 — composite

A globally correlated catalyst screen inverts at the industrial decision frontier.
183 × 170 mm, eight panels: `Fig1.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | forward propagation (step site → microkinetics → catalyst bed → synthesis loop → cost) and the backward-design return path | schematic; stage-1 render from `renders/`, stage-2 curve is the model volcano |
| b | Ru, Os, Fe step sites with N\*, descriptor, price, atomic → economic rank | `renders/*_211_N.png`, `fig1_metals.csv` |
| c | model volcano, log TOF at 673 K versus E\_N, 15 metals, decision-frontier band | `closure/scaling_reachability.csv` + `fig1_metals.csv` |
| d | minimum catalyst bed volume versus E\_N; only Ru, Os, Fe fit the 90 m³ limit | `fig1_metals.csv` |
| e | metal price versus activity; Ru is 72× more active and 6,732× more expensive than Fe | `fig1_metals.csv` |
| f | atomic → economic rank for all 15 metals | `fig1_metals.csv` |
| g | rolling Top-K Spearman ρ, K = 3…15 | `fig1_rolling.csv` |
| h | catalyst-dependent cost of the three feasible metals with their atomic ranks | `fig1_metals.csv` |

## Provenance

`fig1_data.py` builds both tables from pinned, CI-validated files only:

- `provenance/discover_v1/source_harness/DISCOVER_TASK_V1.json` — E\_N and metal price per metal
- `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/results.json` — activity, bed volume, cost, ranks, rolling Top-K

It asserts the NH3-FINAL-1.1 frozen regression values (frontier order, global ρ = 0.9285714…,
14,136 process states, Fe/Ru/Os costs) and stops rather than writing a table if any has moved.

The volcano curve in c is `closure/scaling_reachability.csv` (activity gain along the scaling
line at 673 K, anchored to Ru). It reproduces every metal inside its range, −2.2 to 0.2 eV,
to within 0.002 decades, so it is the model's own curve and not a fit.

## Structures

`build_structures.py` builds an fcc(211) step for each metal from its bulk nearest-neighbour
distance — the descriptor is the N formation energy at a step site — and places N\* by lowering
a 1.95 Å probe onto the step edge and keeping the most-coordinated contact: a four-fold site
on Ru and Fe (1.95–1.98 Å), three-fold on Os. Atoms are shaded by height so the steps read.
These illustrate the site the descriptor refers to; they are not relaxed geometries.

## Build

```
render-venv/python      build_structures.py      # OVITO 3.16, Tachyon, ambient occlusion
pur_bridge_env/python   fig1_data.py
pur_bridge_env/python   make_fig1.py             # matplotlib -> Fig1.svg / .pdf / .png
```

Text stays live in the SVG and is embedded as TrueType in the PDF; all type is Arial, 5.3–9 pt.
