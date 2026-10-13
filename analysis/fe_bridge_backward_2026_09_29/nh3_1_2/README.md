# Fe bridge, backward target and inversion layer on NH3-FINAL-1.2 (2026-10-13)

Same calculations as the parent folder, run on NH3-FINAL-1.2 (`provenance/nh3_final_1_2`, run
`nh3_final_1_2_20261013`: Gillespie–Beattie NH₃ formation free energy and Newton–Cooper fugacities in loop and
microkinetics, F_CAL 74,351.6, 14,510 process states). File names and layouts are those of the 1.1 files in the parent
folder. No DFT; the 1.2 response surface is read only by the two cross-check scripts and never rebuilt.

## Commands

From `analysis/fe_bridge_backward_2026_09_29`, with
`NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness` (or the repository copy plus its
`cache/`) and the CatalystForge interpreter:

    set NH3_MODEL=1.2
    python ru_price_sweep.py                          # ru_price_sweep.csv  (Fig. 2 Ru price sweep, same definition)
    python build_certified_inner_surface.py           # activity_lifecycle_certified_boundary.csv, _target_keypoints.csv, _certified_keypoint.json
    python run_statewise_strict_scaling_lifecycle.py  # scaling_lifecycle_exact_summary.json, _keypoints.csv, _global_boundary.csv
    python validate_strict_scaling_lifecycle_result.py
    python build_inversion_layer_common_reference.py  # inversion_layer_common_reference.csv, inversion_layer_table.csv
    python build_ru_lifecycle_parity_keypoints.py     # ru_lifecycle_parity_keypoints.csv
    python run_exact_joint_surface.py                 # activity_lifecycle_exact_full14510.csv (+ _summary.json), cross-check
    python run_exact_scaling_lifecycle_surface.py     # surface_crosscheck/ (brute force on the cached response), cross-check

or `RUN_STRICT_SCALING_LIFECYCLE_AUDIT.ps1 -Model 1.2` for the strict-scaling closure, its gate and its cross-check.
Each script runs single-process in under a minute. With `NH3_MODEL=1.1` (default) every script reproduces the
committed 1.1 files (see "1.1 reproduction" below).

## Key numbers, NH3-FINAL-1.1 → 1.2

| Quantity (file) | 1.1 | 1.2 |
|---|---:|---:|
| Process states | 14,136 | 14,510 |
| Fe cost (USD t⁻¹ NH₃) | 15.2917 | 11.5158 |
| **Inversion layer** (`inversion_layer_common_reference.csv`, `inversion_layer_table.csv`) | | |
| log₁₀ TOF at 673 K, Ru / Os / Fe | −3.45119 / −3.49532 / −5.30997 | −2.45518 / −2.49340 / −5.23802 |
| Common-reference active metal, Ru / Os / Fe (kg) | 2,161.5 / 4,503.5 / 86,279.0 | 263.5 / 541.6 / 88,301.9 |
| Annualized metal replacement, Fe / Ru / Os (USD t⁻¹) | 0.199 / 33.570 / 185.270 | 0.204 / 4.092 / 22.279 |
| Ru − Fe in metal replacement (USD t⁻¹) | 33.371 | 3.889 |
| Order: activity → demand → replacement → total | Ru>Os>Fe → Ru<Os<Fe → Fe<Ru<Os → Fe<Ru<Os | same |
| Equal-price ablation, Ru at 8 USD kg⁻¹ vs Fe (USD t⁻¹) | 14.712 vs 15.292 | 10.237 vs 11.516 |
| Total Fe / Ru / Os (USD t⁻¹); Ru − Fe | 15.292 / 22.031 / 25.832; 6.739 | 11.516 / 16.633 / 19.747; 5.117 |
| Process optimization moves Ru − Fe from metal replacement to total | 33.371 → 6.739 (narrows) | 3.889 → 5.117 (widens) |
| **Ru price sweep** (`ru_price_sweep.csv`) | | |
| Fe–Ru parity price (USD kg⁻¹) | 163.763 | 403.536 |
| Parity state | 425 °C, 185 bar, 30 °C, 6.238 m³ | 425 °C, 110 bar, 30 °C, 3.818 m³ |
| Distinct process states visited (the certified subset) | 53 | 42 |
| **Lifecycle parity at current Ru activity** (`ru_lifecycle_parity_keypoints.csv`) | | |
| Recovery needed at 10 y / 20 y | 99.696 % / 99.392 % | 99.251 % / 98.501 % |
| Lifetime needed at 99 % recovery | 32.88 y | 13.35 y |
| Prespecified envelope (5–20 y, ≤ 99 %) reaches parity at α = 1 | no | yes, for L ≥ 13.35 y |
| **Direct-activity / lifecycle target** (`activity_lifecycle_target_keypoints.csv`) | | |
| Required activity multiplier, 10 y + 99 % (= 20 y + 98 %) | ≤ 2.418× | ≤ 1.291× |
| Required activity multiplier, 15 y + 99 % | ≤ 1.742× | ≤ 0.904× (no gain needed) |
| Required activity multiplier, 20 y + 99 % | ≤ 1.401× | ≤ 0.710× (no gain needed) |
| Boundary state at these points | 425 °C, 185–190 bar, 30 °C | 425 °C, 110 bar, 30 °C |
| α = 1 / α* anchors reproduced | 163.763 USD kg⁻¹ / 201.223× | 403.536 USD kg⁻¹ / 114.667× |
| **Certified keypoint** (`activity_lifecycle_certified_keypoint.json`) | | |
| Reference multiplier (all-state strict-scaling gain maximum) | 2.524565× | 1.575275× |
| Parity effective Ru price at that multiplier (USD kg⁻¹) | 566.965 | 671.025 |
| Recovery needed at that multiplier and 20 y | 97.894 % | 97.508 % |
| Explicit point (that multiplier, 20 y, 98 %): cost, margin vs Fe (USD t⁻¹) | 15.2571, −0.0346 | 11.3502, −0.1656 |
| **Strict-scaling × lifecycle closure** (`scaling_lifecycle_exact_summary.json`, `_keypoints.csv`, `_global_boundary.csv`) | | |
| Strict-scaling minimum reproduced (USD t⁻¹ at E_N) | 21.398 at −1.215 eV | 16.455 at −1.180 eV |
| Critical lifecycle factor q* = (1 − r)/L (y⁻¹) | 4.4068 × 10⁻⁴ | 8.2510 × 10⁻⁴ |
| Equivalent effective Ru price on the 10-y basis (USD kg⁻¹) | 237.319 | 444.339 |
| Parity state | E_N −1.230 eV; 425 °C, 190 bar, 30 °C; 4.298 m³ | E_N −1.190 eV; 425 °C, 110 bar, 30 °C; 3.509 m³ |
| Best tested corner (20 y, 99 %): strict-scaling cost (USD t⁻¹) | 15.362 | 11.199 |
| Margin vs Fe at that corner (USD t⁻¹; relative) | +0.071 (+0.46 %) | −0.317 (−2.75 %) |
| Tested box (L ≤ 20 y, r ≤ 99 %) intersects the strict-scaling manifold | **no** | **yes** |
| Recovery needed for parity at 10 / 15 / 20 y | 99.559 / 99.339 / 99.119 % | 99.175 / 98.762 / 98.350 % |
| Lifetime needed at 99 % / 98 % recovery | 22.69 y / 45.38 y | 12.12 y / 24.24 y |
| Strict-scaling keypoint 15 y + 99 %: cost, margin (USD t⁻¹) | 15.479, +0.188 | 11.361, −0.154 (reaches parity) |
| Strict-scaling keypoint 10 y + 99 % (= 20 y + 98 %): cost, margin | 15.623, +0.332 | 11.686, +0.170 |
| **Fe terrace-to-step bridge** (`fe_bridge_loo.csv`) | | |
| LOO table, fit, RSE 0.2271 eV, Fe step E_N −1.392 eV, 95 % PI | – | unchanged (same S1 workbook, SHA-256 fc259c53…; the file here is a byte copy) |

Sign changes against 1.1 (the manuscript wording built on them needs the 1.2 statement):

1. The tested lifecycle box now intersects the strict-scaling manifold: at 20 y and 99 % recovery the best
   strict-scaling Ru state is 0.317 USD t⁻¹ below Fe; parity needs 98.350 % recovery at 20 y or a 12.12-y life at 99 %.
2. With 99 % recovery, 15- and 20-year lifetimes need no activity gain (0.904× and 0.710×); even at the canonical Ru
   activity the 1D lifecycle parity is reached at 99 % recovery for lifetimes above 13.35 y.
3. Process optimization widens the Ru − Fe difference (3.889 → 5.117 USD t⁻¹) instead of narrowing it (33.371 → 6.739).
   The layer at which the order first flips (actual-price metal replacement) and the equal-price ablation (Ru cheaper
   than Fe) are unchanged.

The direct-activity targets are tight: a full 14,510-state bisection on α gives the same multipliers to nine digits
(1.290645757 / 0.903973414 / 0.710093177), and `activity_lifecycle_exact_full14510.csv` reproduces the subset parity
prices at every α in [1, 2.25]. The brute-force surface (`surface_crosscheck/`) reproduces q* (444.338519 USD kg⁻¹ at
E_N −1.19 eV) and all four strict-scaling keypoints.

## Definitions re-derived for 1.2 (rule 4)

- Certified subset: the distinct process states visited by the **1.2** Ru price sweep (42), computed by
  `ru_price_sweep.py` on the definition of `figures/composite/fig2/fig2_model.py` (241 log-spaced prices 1–3×10⁵ USD kg⁻¹
  plus 8 and 53,852.5, 90 m³ cap, log-price bisection for parity). If `figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv`
  exists, the script checks it is identical.
- α = 1 anchor: the 1.2 sweep's parity price (403.536 USD kg⁻¹) instead of the literal 163.763; α* anchor: the 1.2
  break-even multiplier 114.667 from results.json.
- Reference multiplier of the certified keypoint: the 1.2 all-state strict-scaling gain maximum (1.575275) instead of
  2.524565; the 1.1-only assertion that this point is cost-feasible is kept for 1.1 only (it is feasible in 1.2 too).
- Strict-scaling regression anchor, Fe cost and process-state count: read from the 1.2 results.json; the result gate
  pins the 1.2 q* (8.251028617208592 × 10⁻⁴ y⁻¹) and the verdict (intersects = true).
- Inversion layer: F_CAL, plant size, life and recovery from the 1.2 manifest; 673 K log₁₀ TOF from the 1.2
  results.json; equal-price row from the 1.2 sweep at 8 USD kg⁻¹ (Ru optimum 400 °C, 95 bar, 30 °C).

## 1.1 reproduction (NH3_MODEL=1.1)

- Byte-identical: `activity_lifecycle_certified_boundary.csv`, `activity_lifecycle_target_keypoints.csv`,
  `activity_lifecycle_certified_keypoint.json`, `inversion_layer_common_reference.csv`, `inversion_layer_table.csv`;
  `ru_price_sweep.py` reproduces `figures/composite/fig2/fig2_ru_price_sweep.csv` byte for byte.
- `run_statewise_strict_scaling_lifecycle.py`: the three promoted files reproduce in layout, keys, text and booleans;
  numbers agree to ≤ 1 × 10⁻¹³ relative (last one or two digits). The unmodified script gives the same digits on this
  machine, so the committed files (written elsewhere) carry another platform's floating-point rounding; they are left
  untouched and still pass `validate_strict_scaling_lifecycle_result.py`.
- `build_ru_lifecycle_parity_keypoints.py`: committed rows reproduce to their printed precision; the 32.877-y row was
  entered by hand (exact 99 %-recovery lifetime 32.884 y) and is not regenerated.
- Cross-checks: `run_exact_scaling_lifecycle_surface.py` (cached 1.1 surface) gives the committed keypoints to nine
  digits; `run_exact_joint_surface.py` passes its α = 1 and α* anchors and gives the committed explicit point
  (15.2570598 USD t⁻¹).
