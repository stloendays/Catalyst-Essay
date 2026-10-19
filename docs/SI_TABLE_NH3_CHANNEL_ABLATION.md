# Supplementary Table — NH3 channel ablation ladder (Ru, Os, Fe)

Model basis: NH3-FINAL-1.2 (canonical run `nh3_final_1_2_20261013`, 14,510 process states). Every number below is
read from a committed file named in the "Source file" column; nothing is recomputed here. The table is the ammonia
counterpart of the Au/TiO2 channel ladder in `docs/AU_TIO2_DECISION_BOUNDARY_V2_RESULT.md` and places the three
cases on the common leverage inequality of `docs/LEVERAGE_INEQUALITY_NOTE.md`.

Reading of each level: a downstream channel is switched on, and the question is whether the ordering of the three
feasible metals changes. L0 is the inventory-only layer of the Au/TiO2 control; L3 is the canonical full result.

| Level | Channels on | Metric (lower is better unless stated) | Ru | Os | Fe | Order | Status |
|---|---|---|---:|---:|---:|---|---|
| L0 | intrinsic activity → inventory at one reference (673 K, common throughput, no price) | log10 TOF (higher better) | −2.45518 | −2.49340 | −5.23802 | Ru > Os > Fe | preserved |
| L0 | same | required active metal, kg (common reference) | 263.5 | 541.6 | 88,301.9 | Ru < Os < Fe | preserved |
| L1 | L0 + metal price, 10-year life, zero recovery (annualized replacement, no process cost) | USD per t NH3 | 4.092 | 22.279 | 0.204 | Fe < Ru < Os | first flip |
| L2 | full process optimization + economics at **equal metal price** (Ru priced as Fe, 8 USD/kg, all 14,510 states reoptimized) | USD per t NH3 | 10.237 | — | 11.516 | Ru < Fe (pairwise) | Fe does not win |
| L3 | canonical: full process + economics at canonical prices | USD per t NH3 | 16.633 | 19.747 | 11.516 | Fe < Ru < Os | inversion retained |

## Sources (every number traced)

| Level | Numbers | Source file (repository path) | Field / row |
|---|---|---|---|
| L0 | log10 TOF −2.455184181239416 / −2.493400874606359 / −5.238017960977338 | `analysis/fe_bridge_backward_2026_09_29/nh3_1_2/inversion_layer_common_reference.csv` | `activity_log10_TOF_673K`; identical to `provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json` → `deterministic.metals.{Ru,Os,Fe}.activity_logTOF` |
| L0 | active metal 263.49624581065893 / 541.5616060520997 / 88301.93920417412 kg | same CSV | `required_active_metal_kg_common_reference` |
| L1 | replacement 4.092265775780392 / 22.279383735640096 / 0.20372473356406431 USD/t | same CSV | `annualized_replacement_cost_USD_t_NH3` (prices 53,852.5 / 142,650 / 8.0 USD/kg in `metal_price_USD_kg`; 10-y life and zero recovery from the run manifest, as documented in `analysis/fe_bridge_backward_2026_09_29/build_inversion_layer_common_reference.py`) |
| L2 | Ru at 8 USD/kg: 10.236808130093332 USD/t at 400 °C, 95 bar, T_sep 30 °C, 18.18 m³ | `figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv` (byte-identical to `analysis/fe_bridge_backward_2026_09_29/nh3_1_2/ru_price_sweep.csv`) | row `price_USD_kg = 8.0`, column `cost` |
| L2, L3 | Fe 11.515783597179267 USD/t at 425 °C, 105 bar | `provenance/nh3_final_1_2/.../results.json` | `deterministic.metals.Fe.feasible.total_cost` |
| L3 | Ru 16.632749358902807 at 450 °C, 220 bar; Os 19.746543665634597 at 450 °C, 340 bar | same `results.json` | `deterministic.metals.{Ru,Os}.feasible.total_cost` |
| L3 | feasible economic order Fe, Ru, Os | same `results.json` | `deterministic.feasible_economic_order` |
| all | layer table with the same five rows | `analysis/fe_bridge_backward_2026_09_29/nh3_1_2/inversion_layer_table.csv` | rows 1–5 |

The 1.1 counterparts of these files (`analysis/fe_bridge_backward_2026_09_29/inversion_layer_common_reference.csv`,
`figures/composite/fig2/fig2_ru_price_sweep.csv`) carry the NH3-FINAL-1.1 numbers (Ru 2,161.5 kg; replacement
0.199 / 33.570 / 185.270; equal-price Ru 14.712 vs Fe 15.292; canonical 15.292 / 22.031 / 25.832). They are not used
in this table.

## Leverage reading of the ladder

With A the activity (TOF) and the common-reference inventory ∝ MW / A:

- L0 → L1 (price channel). Ru/Fe: activity ratio A_Ru/A_Fe = 10^(5.23802 − 2.45518) = 606.5; the price ratio is
  53,852.5 / 8 = 6,731.6 and the molar-mass ratio 101.07 / 55.845 = 1.810, so the replacement-cost ratio is
  6,731.6 × 1.810 / 606.5 = 20.09 (4.092 / 0.204 = 20.09). The price channel alone exceeds the activity advantage by
  a factor of about 20: inversion at L1. Os/Ru: activity ratio 0.916, price ratio 2.649, mass ratio 1.882 →
  Os/Ru replacement 5.44 (22.279 / 4.092 = 5.44): Os stays behind Ru.
- L1 → L2 (process channel at equal price). With the price channel removed, the full process optimization leaves Ru
  ahead of Fe (10.237 < 11.516). The process channel on its own does not invert the pair; it changes the size of
  the gap once price is present (Ru − Fe: 3.889 USD/t at L1, 5.117 USD/t at L3).
- L2 → L3 (price and process together). Fe < Ru < Os. The differentiating channel for the Ru/Fe decision is the
  metal price acting on the inventory that process optimization cannot shrink below the bed-volume and compression
  trade-off.

Numbers in this section are arithmetic on the table values above; they introduce no new inputs.
