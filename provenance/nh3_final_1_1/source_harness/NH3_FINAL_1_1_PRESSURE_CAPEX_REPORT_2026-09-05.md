# NH3-FINAL-1.1 — pressure-dependent CAPEX added, grid 10–1000 bar: first full run (2026-09-05)

Status tag: **CANDIDATE_FOR_PROMOTION** (scenario run; canonical still NH3-FINAL-1.0). Assumptions were registered before the run in
`PRESSURE_CAPEX_ASSUMPTIONS_2026-09-05.md`; nothing in that file was edited afterwards.

Run: `outputs/nh3_final_1_1_20260905T113727Z` (full mode; 14,136 process states; new 14,136 × 1,201 response cache; 1,000 draws; backward design).
Manifest: `configs/nh3_final_1.1_candidate.yaml` (frozen_regression now filled from this run; its own gate passes in smoke mode).
Code: `harness_core.py` optional `economics.pressure_capex` block, zero-cost when absent; canonical 1.0 smoke gate PASS after the patch
(`outputs/nh3_final_20260905T113652Z`), bit-identical to the pre-patch Windows run; 27 tests pass (`tests/test_pressure_capex.py` added).

## 1. The optimizer no longer touches the grid
| metal | 1.0 (300-bar edge) | 1.0 scenario, 500-bar grid | **1.1, 10–1000 bar + pressure CAPEX** |
|---|---|---|---|
| Fe cost USD/t, T/P/Tsep, V | 10.199, 400 °C / 150 / 30, 86.6 m³ | same | **15.292, 425 °C / 180 / 30, 17.1 m³** |
| Ru | 17.592, 450 / **300 (edge)** / 10, 0.082 | 16.719, 450 / 490 / 30 | **22.031, 450 / 425 / 25, 0.066** |
| Os | 21.321, 450 / **300 (edge)** / −15, 0.029 | 20.477, 450 / **500 (edge)** / 10 | **25.832, 450 / 425 / 0, 0.029** |
| feasible order | Fe > Ru > Os | same | **Fe > Ru > Os** |
| Top-3 ρ / global raw ρ / censored ρ | −0.50 / 0.911 / 0.684 | −0.50 / 0.911 / 0.684 | **−0.50 / 0.929 / 0.684** |
| Ru − Fe gap, C_Ru/C_Fe | 7.39, 1.725 | 6.52, 1.639 | **6.74, 1.441** |
| any feasible optimum on the pressure edge | Ru, Os | Os | **none** |

Infeasible metals whose *unconstrained* optimum sits at 1000 bar (Re, Pd, Pt, Ag, Au) are > 90 m³ everywhere and do not enter any decision quantity.

## 2. Cost pools at the optimum (USD/t)
| pool | Fe 1.1 | Ru 1.1 | Os 1.1 |
|---|---|---|---|
| metal inventory | 0.070 | 1.833 | 2.159 |
| reactor volume proxy (1.0 term) | 0.115 | 0.030 | 0.028 |
| **converter-shell pressure premium (new)** | 0.807 | 0.074 | 0.074 |
| fresh-feed compression electricity | 9.660 | 14.291 | 14.291 |
| recycle compression electricity | 0.765 | 0.118 | 0.110 |
| refrigeration electricity | 0 | 0.629 | 4.120 |
| **compressor bare-module CAPEX (new)** | 3.875 | 5.055 | 5.050 |
| total | 15.292 | 22.031 | 25.832 |

## 3. Full-mode blocks
| quantity | 1.0 | 1.0 scen 500 | **1.1** |
|---|---|---|---|
| Fe feasibility, 1000 draws, 90 m³ | 0.736 | 0.767 | **0.799** |
| MC raw ρ / censored ρ | 0.923 / 0.683 | 0.921 / 0.689 | **0.941 / 0.694** |
| Top-1 survival / Top-3 actionable / Top-3 conditional | 0.248 / 0.931 / 0.994 | 0.235 / 0.937 / 0.990 | **0.282 / 0.940 / 0.985** |
| **Ru activity break-even multiplier** | 2171.56× | 2171.56× | **201.22×** |
| scaling headroom 673 K / all states | 1.090× / 2.433× | 1.090× / 2.525× | **1.090× / 2.525×** |
| best strict-scaling Ru cost (E_N) | 17.194 (−1.200) | 16.224 (−1.215) | **21.398 (−1.215)** |
| activity-only branch verdict | unreachable | unreachable | **unreachable (201 ≫ 2.5)** |

## 4. Pre-registered predictions vs outcome
| # | prediction (written before the run) | outcome |
|---|---|---|
| 1 | Fe premium ≈ 4 USD/t at 150 bar / 87 m³; optimum moves to 200–250 bar with a smaller bed | The optimizer avoided the big vessel instead of paying for it: 180 bar, 17 m³, premium 0.81; cost +5.1 USD/t, mostly compressor CAPEX (3.9) and higher fresh compression. Direction right, magnitude of the premium avoided by re-optimization. |
| 2 | Ru premium ≈ 0.1; compressor CAPEX 4–6; optimum < 490 bar, probably > 300 bar | 0.07; 5.06; 425 bar. Correct. |
| 3 | Fe > Ru > Os survives; gap may narrow | Survives; gap 7.39 → 6.74, ratio 1.725 → 1.441. Correct. |
| 4 | break-even multiplier changes, direction not predicted | 2172× → 201×. Parity now sits at a Fe cost of 15.29 instead of 10.20, and Ru's floor (compression + compressor CAPEX at a Fe-like pressure) is close to that; the 10× drop is the pressure CAPEX hitting Fe's large vessel and inventory. Still ≫ 2.5× headroom. |

## 5. What this does to the paper's claims
- **Removed:** the truncation bias. No decision-relevant optimum is set by the grid; Ru and Os optima are model optima (425 bar), Fe 180 bar.
- **Unchanged:** the inversion (Top-3 ρ = −0.50; Fe > Ru > Os), the shortlist robustness (Top-3 actionable ≈ 0.94), the reachability verdict.
- **Changed and must be re-quoted:** every cost (Fe 10.2 → 15.3, Ru 17.6 → 22.0, Os 21.3 → 25.8), the Ru−Fe ratio (1.73 → 1.44), the break-even
  (2172× → 201×), Fe feasibility (0.74 → 0.80). Figures 4, 5 and the abstract numbers all move; the qualitative sentences do not.
- **Declared omission that remains:** loop heat exchangers, separator and HP piping (would penalize high P further and high-recycle catalysts more;
  conservative for the Fe-vs-Ru conclusion).

## 6. Promotion (not applied — needs the human's go)
Promoting 1.1 to canonical means: `configs/nh3_final.yaml` ← `configs/nh3_final_1.1_candidate.yaml` (1.0 archived as `configs/nh3_final_1.0_archived.yaml`),
`CURRENT_STATE.md` headline numbers replaced, and — important — the closed-book drift benchmarks v1/v2 (`benchmark/cases.json`, `drift_v2`) were
authored as edits of the 1.0 manifest, so they must be regenerated against 1.1 before their scores are comparable again. `PROMOTE_CANONICAL`
writes the approval request; the swap itself is a human action.
