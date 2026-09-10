# NH3-FINAL-1.1 consistency closure (PHASE C, 2026-09-05)

Canonical: **NH3-FINAL-1.1**, manifest `configs/nh3_final.yaml` (sha `2942d05b08d6a94e…`), canonical run `outputs/nh3_final_20260905T134204Z` (results sha `710542d01c5e92d0…`, 14,136 states, 1,000 draws). Archived: NH3-FINAL-1.0 `configs/nh3_final_1.0_archived.yaml`, run `outputs/nh3_final_20260903T092000Z` (immutable, pinned).
Every 1.1 number below comes from that single canonical run or from deterministic post-processing of it (`audits/closure_compute_1_1_2026-09-05.py`, `audits/closure_levers_1_1_2026-09-05.py`); the Monte Carlo replication used for per-draw detail reproduces the run's MC block exactly (asserted). No 1.0 / 1.1 mixing.

## 1. Headline table: metric | FINAL-1.0 | FINAL-1.1 | relative change | scientific claim changed?

| metric | FINAL-1.0 | FINAL-1.1 | relative change | category | claim changed? |
|---|---|---|---|---|---|
| process states | 3636 | 14136 | +288.8 % | A | no (grid widened so that no optimum is on an edge) |
| Fe cost USD/t | 10.1987 | 15.2917 | +49.9 % | A | no |
| Ru cost USD/t | 17.5924 | 22.0306 | +25.2 % | A | no |
| Os cost USD/t | 21.3206 | 25.8318 | +21.2 % | A | no |
| Ru/Fe cost ratio | 1.7250 | 1.4407 | -16.5 % | A | no (gap narrower, sign unchanged) |
| Fe optimum T/P/Tsep | 400 °C / 150 bar / 30 °C, V 86.6 m³ | 425 °C / 180 bar / 30 °C, V 17.1 m³ | — | B | interpretation: Fe now avoids the large vessel (pressure premium) instead of filling the bed cap |
| Ru optimum T/P/Tsep | 450 / 300 (grid edge) / 10 | 450 / 425 (interior) / 25 | — | B | interpretation: optimum is a model optimum, not a truncation |
| Os optimum T/P/Tsep | 450 / 300 (grid edge) / -15 | 450 / 425 (interior, flat valley 220–430 bar) / 0 | — | B | report a broad shallow high-pressure minimum, not a point |
| feasible economic order | Fe > Ru > Os | Fe > Ru > Os | — | C | **no** — inversion Ru > Os > Fe → Fe > Ru > Os holds |
| Top-3 Spearman ρ | -0.5000 | -0.5000 | -0.0 % | C | **no** |
| Top-3 Kendall τ | −0.33 | -0.33 | — | C | no |
| global Spearman ρ (raw / censored) | 0.911 / 0.684 | 0.929 / 0.684 | — | A | no (inversion concentrated at the frontier) |
| MC raw ρ mean / censored ρ mean | 0.923 / 0.683 | 0.941 / 0.694 | — | A | no |
| Top-1 survival | 0.2480 | 0.2820 | +13.7 % | A | no (winner remains uncertain) |
| Top-3 actionable / conditional | 0.931 / 0.994 | 0.940 / 0.985 | — | A | no (shortlist robust) |
| Fe feasibility (90 m³, 1000 draws) | 0.7360 | 0.7990 | +8.6 % | A | no |
| raw Top-1 (before feasibility gate) | 0.1850 | 0.2820 | +52.4 % | B | interpretation: in 1.1 the feasibility gate no longer changes the winner (raw = feasible winner in every draw) because the pressure premium already penalizes oversized beds |
| Ru activity-only break-even | 2171.5598 | 201.2234 | -90.7 % | A | no (still ≫ headroom); manuscript: ≈201-fold |
| break-even operating point | 400 °C / 155 bar / 30 °C | 425 °C / 190 bar / 30 °C | — | B | parity state shifts with the Fe optimum |
| scaling headroom 673 K | 1.0899 | 1.0899 | +0.0 % | A | no (identical) |
| scaling headroom, all states | 2.4329 | 2.5246 | +3.8 % | A | no |
| strict-scaling Ru minimum cost (E_N) | 17.194 (-1.2) | 21.398 (-1.215) | — | A | no (still above Fe) |
| activity-only route reachable? | unreachable (2172 ≫ 2.43) | unreachable (201 ≫ 2.52) | — | C | **no** |

Categories: **A** numerical value changed; **B** mechanism / interpretation changed; **C** headline scientific conclusion (unchanged in every C row).

## 2. Cost pools at the optimum (USD/t, 1.1)

| pool | Fe | Ru | Os |
|---|---|---|---|
| metal inventory | 0.070 | 1.833 | 2.159 |
| reactor volume proxy (1.0 term) | 0.115 | 0.030 | 0.028 |
| converter-shell pressure premium (new) | 0.807 | 0.074 | 0.074 |
| fresh compression electricity | 9.660 | 14.291 | 14.291 |
| recycle compression electricity | 0.765 | 0.118 | 0.110 |
| refrigeration electricity | 0.000 | 0.629 | 4.120 |
| compressor CAPEX (new) | 3.875 | 5.055 | 5.050 |
| **total** | **15.292** | **22.031** | **25.832** |

## 3. Rolling Top-K (1.1): K | ρ raw | τ raw | ρ censored | τ censored | n feasible

| K | ρ raw | τ raw | ρ censored | τ censored | n feasible |
|---|---|---|---|---|---|
| 3 | -0.500 | -0.333 | -0.500 | -0.333 | 3 |
| 4 | 0.400 | 0.333 | 0.400 | 0.333 | 3 |
| 5 | 0.700 | 0.600 | 0.667 | 0.527 | 3 |
| 6 | 0.657 | 0.467 | 0.759 | 0.596 | 3 |
| 7 | 0.786 | 0.619 | 0.788 | 0.620 | 3 |
| 8 | 0.667 | 0.500 | 0.791 | 0.624 | 3 |
| 9 | 0.667 | 0.500 | 0.782 | 0.618 | 3 |
| 10 | 0.758 | 0.600 | 0.768 | 0.609 | 3 |
| 11 | 0.818 | 0.673 | 0.752 | 0.597 | 3 |
| 12 | 0.860 | 0.727 | 0.734 | 0.584 | 3 |
| 13 | 0.890 | 0.769 | 0.717 | 0.572 | 3 |
| 14 | 0.912 | 0.802 | 0.700 | 0.559 | 3 |
| 15 | 0.929 | 0.829 | 0.684 | 0.547 | 3 |

## 4. Monte Carlo detail (1.1, seed 20260816)

- Feasibility probability: Ru 100.0 %, Os 100.0 %, Fe 79.9 %, Rh 24.5 %, Ir 7.6 %
- Feasible-set size distribution: 2 metals 13.4 %, 3 metals 63.2 %, 4 metals 21.4 %, 5 metals 2.0 %
- Winner transitions (atomic → feasible economic): Ru->Fe 29.5 %, Os->Fe 27.4 %, Ru->Ru 17.0 %, Os->Ru 14.9 %, Fe->Fe 11.2 %
- Raw Top-1 before the feasibility gate 0.282 vs Top-1 survival 0.282 (1.0: 0.185 vs 0.248).

## 5. Lever / reach table (Layer B inputs recomputed on 1.1; smoke sweeps `outputs/l11_*`, registered)

Eligibility on the canonical 1.1 run:

| key | direction | status | evidence |
|---|---|---|---|
| `economics.metal_recovery_fraction` | increase | eligible | enters metal_cost with catalyst-dependent weight (metal_cost ∝ price·(1-recovery)/life) |
| `economics.catalyst_life_y` | increase | eligible | enters metal_cost with catalyst-dependent weight (metal_cost ∝ price·(1-recovery)/life) |
| `economics.electricity_USD_MWh` | decrease | common_mode_external | scales fresh_comp, recycle_comp, refrigeration for every candidate; absolute leverage may be computed, not a catalyst-discriminatory target |
| `engineering.max_catalyst_bed_m3` | increase | inactive_constraint | cap not binding for ['Ru', 'Fe'] (slack Ru 89.93 m3, Fe 72.94 m3); relaxing it cannot change costs |
| `engineering.max_catalyst_bed_m3` | decrease | eligible | tightening becomes active once cap < 17.06 m3 (Fe bed); slack 72.94 m3 |
| `process.pressure_bar.stop` | increase | inactive_constraint | no pair metal on the upper pressure_bar bound |
| `process.pressure_bar.stop` | decrease | eligible | lowering the upper bound cuts into the window; active once below the pair optimum |
| `process.pressure_bar.start` | decrease | inactive_constraint | no pair metal on the lower pressure_bar bound |
| `economics.discount_rate` | decrease | common_mode_external | scales reactor for every candidate; absolute leverage may be computed, not a catalyst-discriminatory target |
| `economics.calibration_factor` | increase | out_of_scope | frozen model calibration, not a design lever |

| lever | 1.0 |L_rel| | 1.0 reach | 1.1 |L_rel| (mean) | 1.1 reach | 1.1 closing direction | reason for change |
|---|---|---|---|---|---|---|
| `economics.metal_recovery_fraction` | 0.094 | 0.52 (recovery ≤ 0.95) | 0.081 | 0.685 (ok; bound 0.95) | increase economics.metal_recovery_fraction | reach rises 0.52 → 0.69: the baseline log-gap ln(C_Ru/C_Fe) shrank (ratio 1.725 → 1.441) while the metal pool that recovery removes is unchanged in absolute terms (Ru 1.83 USD/t); with cheap metal Ru re-optimizes to 200–220 bar with a 1–2 m³ bed (inventory–severity pathway), so the same recovery closes a larger fraction of a smaller gap. Still the largest catalyst-specific lever |
| `economics.catalyst_life_y` | 0.09 | 0.12 (life ≤ 20 y) | 0.085 | 0.161 (ok; bound 20.0) | increase economics.catalyst_life_y | same family as recovery; reach 0.12 → 0.16 for the same reason (smaller baseline gap) |
| `economics.electricity_USD_MWh` | 0.055 | 0.02 (20–100 USD/MWh, absolute-only) | 0.001 | 0.125 (ok; bound 20.0) | decrease economics.electricity_USD_MWh | mean L_rel ≈ 0 (still classified common-mode by the eligibility rule) but no longer exactly common-mode: the new CAPEX pools do not scale with the electricity price, so at 20 USD/MWh the ratio-closure is +0.12 (both metals move to ≈200 bar, Fe bed 5 m³) and at 100 USD/MWh +0.04; kept absolute-only, to be reported as weakly discriminatory at low prices |
| `process.pressure_bar.stop` | 0.119 | 0.03 (150–350 bar) | 0.000 | — (ok; bound None) | None | **no longer a lever**: Ru/Os optima are interior (425 bar) on the 10–1000 bar grid; the 1.0 value measured how far the truncation was biting, which was an artefact, not a design lever |
| `engineering.max_catalyst_bed_m3` | 0.0 | 0.0 (inactive upward) | 0.001 | — (no_plausible_range; bound None) | decrease engineering.max_catalyst_bed_m3 | inactive upward in both; in 1.1 Fe's bed is 17 m³ (slack 73 m³), so even lowering the cap to 30 m³ is inactive — the constraint only bites below ~17 m³ |

Sweep rows (1.1):

| key | value | Fe | Ru | Os | order | L_rel | ratio-closure |
|---|---|---|---|---|---|---|---|
| `economics.metal_recovery_fraction` | 0.5 | 15.253 | 20.721 | 24.299 | Fe > Ru > Os | +0.085 | +0.161 |
| `economics.metal_recovery_fraction` | 0.9 | 15.222 | 18.084 | 21.019 | Fe > Ru > Os | +0.084 | +0.528 |
| `economics.metal_recovery_fraction` | 0.95 | 15.218 | 17.072 | 19.820 | Fe > Ru > Os | +0.084 | +0.685 |
| `economics.metal_recovery_fraction` | 0.99 | 15.215 | 15.715 | 17.283 | Fe > Ru > Os | +0.072 | +0.911 |
| `economics.catalyst_life_y` | 5.0 | 15.362 | 23.460 | 27.449 | Fe > Ru > Os | -0.084 | -0.160 |
| `economics.catalyst_life_y` | 15.0 | 15.266 | 21.232 | 24.934 | Fe > Ru > Os | -0.087 | +0.097 |
| `economics.catalyst_life_y` | 20.0 | 15.253 | 20.721 | 24.299 | Fe > Ru > Os | -0.085 | +0.161 |
| `economics.electricity_USD_MWh` | 20.0 | 8.791 | 12.102 | 13.615 | Fe > Ru > Os | +0.050 | +0.125 |
| `economics.electricity_USD_MWh` | 40.0 | 13.178 | 19.013 | 21.986 | Fe > Ru > Os | -0.007 | -0.004 |
| `economics.electricity_USD_MWh` | 60.0 | 17.363 | 24.940 | 29.475 | Fe > Ru > Os | -0.016 | +0.008 |
| `economics.electricity_USD_MWh` | 100.0 | 25.621 | 36.377 | 43.244 | Fe > Ru > Os | -0.021 | +0.040 |
| `process.pressure_bar.stop` | 500 | 15.292 | 22.031 | 25.832 | Fe > Ru > Os | +0.000 | +0.000 |
| `process.pressure_bar.stop` | 800 | 15.292 | 22.031 | 25.832 | Fe > Ru > Os | +0.000 | +0.000 |
| `engineering.max_catalyst_bed_m3` | 60.0 | 15.292 | 22.031 | 25.832 | Fe > Ru > Os | +0.000 | +0.000 |
| `engineering.max_catalyst_bed_m3` | 30.0 | 15.292 | 22.031 | 25.832 | Fe > Ru > Os | +0.000 | +0.000 |
| `engineering.max_catalyst_bed_m3` | 15.0 | 15.356 | 22.031 | 25.832 | Fe > Ru > Os | +0.002 | +0.011 |

**1.1 lever ranking by reach (catalyst-specific / operating-window levers only; common-mode electricity reported absolute-only):** metal_recovery_fraction (0.69) > catalyst_life_y (0.16) > stop (0.00) > max_catalyst_bed_m3 (0.00)
**1.0 ranking was** recovery (0.52) > lifetime (0.12) > pressure upper bound (0.03). The 1.0 pressure-bound entry does not survive as a scientific object in 1.1 (interior optima); recovery > lifetime is re-established on 1.1 numbers, not inherited.

## 6. Benchmarks and anchors regenerated on 1.1 (old versions untouched)

- `cases/reaction_cases/nh3_final_1.1.json` (new anchor; sha `59f4f421f0dc3eff…`); `nh3_final_1.0.json` read-only (`build-nh3` now refuses to overwrite it).
- `benchmark/drift_v3/` — drift-v2-policy on NH3-FINAL-1.1; source run outputs/nh3_final_20260905T134204Z; ground-truth sha `429cd22143890e1d…`; generated 2026-09-05T13:54:27.624186+00:00. v1 (`benchmark/cases.json`) and v2 (`benchmark/drift_v2/`) frozen on 1.0, not touched.
- `benchmark/extrapolation_v2/` — extrapolation benchmark v1 construction rules (benchmark/extrapolation_v1/make_x1.py masking, mechanical and semantic labels reused verbatim); anchor sha `59f4f421f0dc3eff…`; ground-truth sha `d85176ed1377caa5…`; shuffle seed 20260905. v1 and `FROZEN_EXTRAPOLATION_V1.json` untouched. Note: `agent/commands.py` and `agent/reaction_case.py` no longer match the v1 frozen hashes (COST_BREAKDOWN pools; parametrized anchor builder) — any evaluation on v2 must be frozen as `FROZEN_EXTRAPOLATION_V2.json` first; no prompt was changed.
- Strategy inputs: `BACKWARD_DESIGN` / `TEST_REACHABILITY` now read the 1.1 canonical run; the scripted strategy reads the break-even from the run instead of the 1.0 literal; `frozen_principles` string updated (P 10–1000 bar, NH3-FINAL-1.1).

## 7. Modelling caveats carried to SI / Methods (bounded; do not block promotion)

1. The 1.0 reactor volume proxy (Palys et al. 2018) could not be re-read from the publisher; its pressure basis is unverified. Maximum possible overlap with the new premium ≤ 0.115 USD/t (Fe) / 0.030 (Ru) = the whole proxy term (0.8 % / 0.1 % of cost).
2. Turton compressor capacity convention (shaft vs fluid power): fluid-power sizing would lower compressor CAPEX by ≈ 25 %; the −25 % diagnostic (`s11_comp_m25`) leaves Fe > Ru > Os, Top-3 ρ, boundary behaviour and the break-even (200.4×) unchanged.
3. Ru (and Os) bed volumes are below the 0.3 m³ lower range of the Turton vessel correlation; the premium is costed at the 0.3 m³ clamp (0.07 USD/t, 0.3 % of Ru cost).
Why none changes the decision: each affects < 1 USD/t, and the ±10–25 % perturbation set (CEPCI, CRF, compressor, vessel) keeps ranking, inversion, feasibility and the reachability verdict fixed (audit §4 and appendix).

## 8. Os operating point

Os has a broad, shallow high-pressure cost minimum: the 220–430 bar band lies within 0.1 USD/t of the numerical argmin (425 bar), and two of the eight perturbations move the argmin to ≈220 bar. Manuscript wording: "Os exhibits a broad, shallow high-pressure cost minimum"; tables may keep argmin = 425 bar.

## 9. Files

- closure data: `outputs/nh3_final_20260905T134204Z/closure/` (headline_1_1.json, rolling_topk_rho_tau.csv, mc_draws.csv, mc_detail.json, breakeven_sweep.csv, scaling_reachability.csv, levers_1_1.json)
- figures: `outputs/nh3_final_20260905T134204Z/figures/` F1–F6 (png + svg)
- scripts: `audits/closure_compute_1_1_2026-09-05.py`, `audits/closure_levers_1_1_2026-09-05.py`, `audits/closure_figures_1_1_2026-09-05.py`, `audits/make_closure_doc_1_1_2026-09-05.py`
- audit: `PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md` (+ appendix), checklist `PROMOTE_NH3_FINAL_1_1_CHECKLIST.md`, promotion patch `audits/promote_patch_2026-09-05.py`, backups `_backup/20260905T214201/`
