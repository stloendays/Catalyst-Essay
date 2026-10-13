# NH₃ frontier provenance on NH3-FINAL-1.2 (2026-10-13)

The analysis of the parent folder rerun on NH3-FINAL-1.2 (`provenance/nh3_final_1_2/README.md`, run
`nh3_final_1_2_20261013`). NH3-FINAL-1.2 uses the Gillespie–Beattie NH₃ formation free energy and Newton–Cooper fugacities
in the loop equilibrium and in the microkinetics. It has F_CAL 74,351.6 and 14,510 process states. The file names are the
same as the 1.1 outputs one level up.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (or leave unset: in-repo copy)
    cd analysis\nh3_frontier_provenance_2026_10_13
    python frontier_swap.py                 # -> nh3_1_2/frontier_swap.json, frontier_swap_robustness.csv (15 s)
    python staged_window.py --workers 2 --cases "Ru/C cap 480 C" "Ru/C cap 500 C" "both catalysts capped at 460 C"
                                            # -> nh3_1_2/staged_scan.csv, staged_direct.csv, staged_window.json
    python check_outputs.py --only swap <copy of nh3_1_2> nh3_1_2

(`D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8`.) No response surface is needed: the harness is built from the
1.2 core, manifest and workbook.

With `NH3_MODEL=1.1` (the default) `frontier_swap.py` rewrites `frontier_swap.json` and `frontier_swap_robustness.csv` of
the parent folder byte for byte (`git diff` empty). For the staged window under 1.1, the check stage was rerun: 8 direct
optimisations of the committed KAAP-type optima at 0 and 12 %/y. They reproduce the committed `committed_check` within
4.2 × 10⁻⁷ USD/t, which is the 6-decimal rounding of the file. The 1.2 run below gives the same 8 costs bit for bit.

Conventions are those of the parent folder: supported Ru/C at 8 wt% Ru, 490 kg m⁻³ and 95.55 % recovery, and Ru at
53,852.5 USD/kg (the same `PRICE` in the 1.1 and 1.2 cores). Metal is charged by the owned-metal 25-year cash flow at
financing rate i, with Fe on the same convention. The KAAP-type loop is 90 bar with a −20 °C separator (5 states in 1.2).
Costs are in USD per tonne NH₃.

## Key numbers, NH3-FINAL-1.1 → 1.2

| Quantity | 1.1 | **1.2** |
|---|---:|---:|
| Headline gate (plug flow, measured rates): Fe optimum | 15.58 at 425 °C, 170 bar | **14.93 at 450 °C, 140 bar** |
| Headline gate: Ru benchmark optimum; parity multiple | 28.07 at 325 bar; 24.6× | **33.07 at 735 bar; 13.95×** |
| Supported Ru/C − Fe, 0 / 12 %/y, global | −1.36 / +1.12 | **−3.46 / +1.45** |
| Supported Ru/C − Fe, 0 / 12 %/y, KAAP-type | −1.07 / +1.86 | **−1.41 / +1.73** |
| **1. Break-even Ru financing rate (Ru/C = Fe), r 95.55 %, global** | 3.35 %/y (15.61; Ru/C 425 °C/165 bar, Fe 425 °C/170 bar) | **7.23 %/y** (15.05; Ru/C 450 °C/135 bar, Fe 450 °C/140 bar) |
| … KAAP-type loop | 2.34 %/y (19.38) | **5.37 %/y** (18.53) |
| … r 90 %, global / KAAP-type | 2.75 / 1.71 %/y | **6.75 / 4.82 %/y** |
| **2. Ru/C optimum pressure, 0 %/y** | 145 bar (400 °C); one-at-a-time 145; all 18 combinations 145–165 | **105 bar** (425 °C); one-at-a-time 105–110; all combinations 105–110 |
| … 12 %/y | 190 bar; one-at-a-time 190–195; all 190–195 | **150 bar** (450 °C); one-at-a-time 140–160; all 140–160 |
| **3. Benchmark-Ru parity price, measured kinetics** | 2,089 USD/kg (425 °C, 165 bar, 1.23 m³) | **3,781 USD/kg** (450 °C, 135 bar, 1.41 m³) |
| … same sweep, descriptor kinetics | 163.763 USD/kg (manuscript 163.76) | **403.536 USD/kg** (= 1.2 Fig. 2 Ru price sweep) |
| … Ru benchmark best at 100–200 bar | 29.08 (200 bar, 25 °C), +1.01 over optimum | **38.26** (200 bar, 20 °C), **+5.19** |
| **4. Parity multiple vs u = 5.5 / 11 / 22 / 50** | 12.3 / 24.6 / 49.3 / 112.0× | **6.98 / 13.95 / 27.90 / 63.42×** |
| … vs converter premium ×0 / ×0.5 / ×1 / ×2 | 166.5 / 45.4 / 24.6 / 11.0× | **60.86 / 24.05 / 13.95 / 7.55×** |
| … Fe optimum at those premiums | 13.71 / 14.93 / 15.58 / 16.39 | 12.24 / 13.69 / 14.93 / 17.06 |
| **5. Fe ahead at 12 %/y (16 cases), global** | 16/16, smallest +0.18 (Fe effectiveness 0.5) | **14/16**: Ru/C ahead with Fe effectiveness 0.5 (−1.47) and premium ×2 (−0.45); smallest Fe lead +0.27 (Ru ×0.7) |
| … KAAP-type | 16/16, smallest +0.73 (Fe effectiveness 0.5) | **15/16**: with Fe effectiveness 0.5 no Fe bed fits the 90 m³ cap; smallest Fe lead +0.55 (premium ×2) |
| Ru/C ahead at 0 %/y, global | 16/16, smallest lead −0.18 (premium ×0) | **16/16**, smallest lead −1.34 (premium ×0) |
| … KAAP-type | 15/16; exception inlet-rate sizing +0.07 | **16/16**, smallest lead −0.08 (inlet-rate sizing) |
| Break-even range over the cases, global | 0.09–10.6 %/y (premium ×0 … Fe effectiveness 0.5) | **1.33–17.67 %/y** (premium ×0 … Fe effectiveness 0.5) |
| … KAAP-type | 0.02–6.2 %/y (premium ×0 … Fe effectiveness 0.5); none for inlet-rate sizing | **0.37–9.89 %/y** (inlet-rate sizing … premium ×2); none for Fe effectiveness 0.5 (Fe infeasible) |
| 0 %/y global gap decomposition: process / converter / metal = total | −0.90 / −0.74 / +0.28 = −1.36 (Ru/C 14.24 at 400 °C/145 bar; Fe 15.60 at 425 °C/170 bar) | **−1.80 / −1.92 / +0.26 = −3.46** (Ru/C 11.51 at 425 °C/105 bar; Fe 14.97 at 450 °C/140 bar) |

Sources: `frontier_swap.json` → `1_breakeven_financing_rate`, `2_RuC_optimum_pressure`, `3_Ru_price_parity_benchmark`,
`4_parity_multiple`, `5_robustness`; `frontier_swap_robustness.csv` (all 16 cases, both rates, break-evens).

Notes on the 1.2 frontier:

- **Ru/C optimum pressure.** At 0 %/y it moves to 110 bar whenever recovery is 90 %, unless the Ru price is also ×0.7.
  At 12 %/y it is 140 bar whenever Ru is ×0.7 and 160 bar whenever Ru is ×1.3, for every bed density and recovery.
- **Break-even rates.** Both catalysts' optima move to 450 °C at the break-even point, Ru/C at 135 bar and Fe at 140 bar.
  The break-even rate rises because the 1.2 states make Fe dearer: the measured Fe bed at the global optimum grows from
  25.6 to 56.3 m³, and in the KAAP-type loop from 30.6 to 52.2 m³.
- **Fe effectiveness 0.5 in the KAAP-type loop.** The smallest measured Fe bed among the five KAAP-type states is 52.23 m³
  (450 °C). Halving the effectiveness doubles it to 104.5 m³, above the 90 m³ single-converter cap. Fe therefore has no
  feasible KAAP-type state in that case, and its gap is −∞ in the CSV. `frontier_swap.json` lists the case under
  `Fe_infeasible`. The smallest and largest gaps exclude it.

## 1.1-specific choices, re-derived

- **Reproduction gate.** The script first re-runs the committed headline variant: plug flow and measured rates on the
  14,510 states of the 1.2 run. It checks the result against the committed 1.2 kinetics swap
  (`analysis/nh3_staged_converter_2026_10_12/nh3_1_2/kinetics_swap.json`, states `1.2`; the staged port collapses the 1.1
  frozen/GB equilibrium dimension). Every gated number matches within 1e-5. The rounded headline asserts are keyed by model
  version: 1.1 15.58/425/170, 28.07/325, 24.6×, −1.36/+1.12/−1.07/+1.86; 1.2 14.93/450/140, 33.07/735, 13.95×,
  −3.46/+1.45/−1.41/+1.73. The generalised cost function equals `kinetics_swap.costs()` at the base point within 1e-9 under
  both models.
- **Descriptor Ru-price parity reference.** Under 1.1 the recomputed value is reported beside the manuscript's 163.76 USD/kg.
  Under 1.2 the same sweep on the 1.2 descriptor kinetics gives 403.535926 USD/kg. The script asserts that this equals,
  within 10⁻⁶ relative, the parity price of the 1.2 Fig. 2 Ru price sweep on the same definition (last row of
  `analysis/fe_bridge_backward_2026_09_29/nh3_1_2/ru_price_sweep.csv`: 403.5359261).
- **Robustness summary.** A case where one catalyst has no state within the 90 m³ cap is counted as a win for the
  feasible one. It is listed under `Fe_infeasible` / `RuC_infeasible` and left out of `min_gap_12` / `max_gap_0`. No 1.1
  case is infeasible, so the 1.1 file is unchanged.
- **Unchanged definitions.** These are the same under both models: the KAAP-type loop (90 bar, −20 °C), the 16 cases, the
  break-even bracket 0–30 %/y, u = 11, the 25-y cash flow, and the economics. The 1.1 and 1.2 manifests differ only in
  the thermo block and in F_CAL. F_CAL enters only the descriptor-kinetics sweep of item 3; the measured-rate amounts use
  the source rates.

## 6. Staged Fe → Ru/C window, KAAP-type loop: unchanged

`staged_window.py` uses only the staged-converter model (`converter.py`, `kinetics.py`, `run_staged.py`). That model takes
from the harness only the economic controls and cost functions. Its equilibrium (Gillespie–Beattie, Newton–Cooper), rate
laws and per-pass conversion are its own. NH3-FINAL-1.2 changes only the thermo block and F_CAL, so the converter is the
same calculation under both models (`analysis/nh3_staged_converter_2026_10_12/nh3_1_2/README.md`, section 2;
`staged_invariance_1_2.py`). Under 1.2 the script reads its check values and start points from that folder's
`nh3_1_2/arrangements.csv`, a byte copy of the 1.1 file.

**What was run.** `NH3_MODEL=1.2 staged_window.py --workers 2` was run for the base case and the three temperature-cap
cases (`--cases`). It took 88 min. The full eight-case run takes about 72 min on 4 workers, so about 160 min on the 2
workers allowed here. The other four cases were therefore not rerun: Ru/C without H₂ inhibition, recovery 90 %, and Ru price
×0.7 and ×1.3. For the same converter calculation they are the 1.1 values one level up.

**Result: identical to 1.1.** The 8 check optimisations give the same costs as the 1.1 rerun of the check stage bit for bit,
for example FFF at 0 %/y: 18.666850710533108 under both models. `staged_window.json` agrees with the committed 1.1 file in
every number of the four cases at its 6 printed decimals. This covers the direct edges, the scan edges, all 50 directly
optimised points of the four arrangements, the base-case savings and their optimal arrangements. The only exception is
two scan-based Ru/C shares, which differ by 1 × 10⁻⁶. The CSVs differ from the committed 1.1 (Linux) files only in the
last printed digit: at most 4 × 10⁻⁶ in cost, share or volume, and 1 × 10⁻⁵ in the printed design vector.
`python check_outputs.py --only staged nh3_1_2 .`, run in the parent folder, reports 0 differences.

| Case (owned-metal cash flow, r 95.55 %) | Window, direct (1.1) | **Window, direct (1.2)** | Scan (1.2) |
|---|---|---|---|
| Base (Ru/C ≤ 460 °C, Fe ≤ 530 °C) | 0.82–6.70 %/y | **0.82–6.70 %/y** | 0.82–6.71 |
| Ru/C cap 480 °C | 2.11–7.93 | **2.11–7.93** | 2.11–7.93 |
| Ru/C cap 500 °C | 3.96–8.10 | **3.96–8.10** | 3.95–8.12 |
| Both catalysts capped at 460 °C | 2.86–6.78 | **2.86–6.78** | 2.85–6.79 |
| Ru/C without H₂ inhibition (rescaled ×0.5716) | 0.67–5.43 | not rerun (same calculation) | |
| Recovery 90 % | 0.13–6.18 | not rerun | |
| Ru price ×0.7 / ×1.3 | 1.42–10.11 / 0.50–4.95 | not rerun | |

| Base case, 1.2 (= 1.1) | Optimum | Cost | all-Fe | Saving |
|---|---|---|---|---|
| 1.35 %/y | FRR, Ru/C 48 % | 17.90 | 18.68 | **0.78** |
| 2.10 %/y | FRR, Ru/C 39 % | 18.09 | 18.68 | **0.60** |
| 5.10 %/y | FFR, Ru/C 6.9 % | 18.61 | 18.71 | **0.10** |

The Ru/C share of catalyst volume across the base window is also the same (direct optima). It is 56 % (FRR) at the lower
edge, then 48 % at 1.35 %/y, 39 % at 2.10 %/y, 30 % at 3 %/y and 22 % at 4 %/y. It is 6.9 % (FFR) at 5.10 %/y and 4.3 % at
6.46 %/y.

The kinetics-swap break-even of item 1 and this window are separate calculations. The kinetics swap runs on the harness
process states, which 1.2 changes; the converter does not. The KAAP-type break-even therefore moves from 2.34 to
5.37 %/y, while the staged window stays at 0.82–6.70 %/y. Both 2.34 and 5.37 lie inside the window.

## Files

| File | Content |
|---|---|
| `frontier_swap.json`, `frontier_swap_robustness.csv` | items 1–5 on NH3-FINAL-1.2 (+ `model` block) |
| `staged_window.json`, `staged_direct.csv`, `staged_scan.csv` | item 6, base and temperature-cap cases (`model.cases_run`) |
