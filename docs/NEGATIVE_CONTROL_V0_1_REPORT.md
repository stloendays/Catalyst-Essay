# NEGATIVE CONTROL V0.1 / V0.2 — rank-preservation reaction (N2O decomposition) — report (2026-09-07)

**Outcome in one line.** The pre-registered negative control **fails** in both frozen parameterizations: for direct N2O
decomposition the atomic activity ranking does **not** survive per-candidate economic optimization; the atomic winner (Rh in
V0.2) is displaced by Ni, Top-3 Spearman is −0.50 (identical to NH3-FINAL-1.1), and the inversion is produced by the same
mechanism as in ammonia — an expensive active metal buys down its inventory with process severity (here temperature, in
NH3 pressure) until the severity pool exceeds the whole cost of a cheap, less active metal. The hypothesis that the NH3
inversion requires recycle / separation / purge restructuring is therefore **not supported** by this control; an
inventory-only chain inverts as well. Recorded as a negative result, not tuned away.

Protocol: `NEGATIVE_CONTROL_V0_1_PREREGISTRATION.md` (frozen `NEGATIVE_CONTROL_V0_1_FROZEN.json`), addendum
`NEGATIVE_CONTROL_V0_2_ADDENDUM.md` (frozen `NEGATIVE_CONTROL_V0_2_FROZEN.json`). Manifests `configs/n2o_negcontrol_v0_1.yaml`,
`configs/n2o_negcontrol_v0_2.yaml` (only `eps_eV_per_ML` 1.0 → 1.5 differs). Code `negative_control/{n2o_core,run_negctrl,
make_figures,diag_equal_price}.py`. Runs `outputs/n2o_negctrl_v0_1_20260907T033956Z`, `outputs/n2o_negctrl_v0_2_20260907T034138Z`
(results.json, provenance.json with config / frozen / code hashes, canonical_results.csv, figures F1–F5, diagnostics_equal_price.json).
Canonical tables copied to `NEGATIVE_CONTROL_V0_{1,2}_CANONICAL_RESULTS.csv`. NH3-FINAL-1.1, DISCOVER V1, the cross-model
protocol and the scorer were not read for modelling and not modified (frozen-hash check on `harness_core.py` and the NH3
canonical `results.json` PASS in both provenance files).

## 1. What was frozen before computing
| item | value |
|---|---|
| reaction / plant | 2 N2O → 2 N2 + O2, nitric-acid tail gas 200 000 Nm3/h, 10 bar, 1500 ppmv N2O, 3 % O2, 420 °C available, once-through, 98 % conversion (4 804 t N2O/y) |
| candidates | the 15 NH3 metals, NH3-FINAL-1.1 prices and molar masses (read-only) |
| descriptor | O adsorption energy dE_O vs ½O2 (reconstruction values, ±0.30 eV MC) |
| kinetics | R1 N2O + * → N2 + O* (BEP Ea = 0.30·dE_O + 1.60 eV, collision-limited prefactor 1e8 s⁻¹ bar⁻¹); R2 2 O* ⇌ O2 + 2* (Ea = −dE_O,eff + 0.30 eV, 1e13 s⁻¹, equilibrium with gas O2); mean-field O–O repulsion eps (1.0 eV/ML V0.1, 1.5 eV/ML V0.2) |
| atomic metric | log10 TOF at 450 °C, 10 bar, 1500 ppmv N2O, 3 % O2 (one common condition) |
| chain | sites = F·ln(1/(1−X))/TOF → metal mass (dispersion 0.30) → bed (1 wt %, 1000 kg/m3) → T (350–650 °C, 5 °C) × bed diameter (2–8 m) per candidate → pools: metal inventory (5 y life, 0 recovery), reactor base CAPEX, Turton vessel pressure premium, heating fuel above 420 °C (8 USD/GJ, 60 % recovery), expander work lost to Ergun ΔP |
| feasibility | bed ≤ 300 m3, ΔP ≤ 0.5 bar; infeasible candidates censored to the mean remaining rank (NH3 convention) |
| criteria | C1 atomic winner = economic winner; C2 Top-3 ρ ≥ 0.5; C3 Top-5 ρ ≥ 0.5; C4 full ρ ≥ 0.85; C5 pairwise inversion fraction ≤ 0.15; C6 full τ ≥ 0.70 |

Why two versions: after freezing V0.1 and before reading any economic output, the V0.1 atomic ranking (Pd > Cu > Pt > Ag > Ir >
Rh …) was found to contradict the experimental metal order (Rh > Ir ≈ Ru > Pd > Pt > Ni > Cu > Ag > Au; Spearman −0.10). V0.2
changes only the O–O repulsion (1.0 → 1.5 eV/ML), giving Rh > Ir > Ni > Pd > Cu > Co > Pt > Ru > Ag > Os > Au > Fe > Re > Mo > W
(Spearman 0.75 to the experimental order). Both were run as frozen; V0.2 is the literature-consistent version and the one
proposed for the manuscript.

## 2. Results
### 2.1 Rankings and criteria (deterministic, feasible-censored)
| quantity | V0.1 | **V0.2** | NH3-FINAL-1.1 (same definitions) |
|---|---|---|---|
| atomic order (top 5) | Pd Cu Pt Ag Ir | **Rh Ir Ni Pd Cu** | Ru Os Fe Rh Ir |
| economic order (feasible) | Cu Ag Ni Pd Pt Ir Rh (7/15) | **Ni Cu Co Ag Fe Pd Ru Rh Pt Ir Os (11/15)** | Fe Ru Os (3/15) |
| C1 winner preserved | Pd → Cu, no | **Rh → Ni, no** | Ru → Fe, no |
| C2 Top-3 ρ | 0.50 | **−0.50** | −0.50 |
| C3 Top-5 ρ | 0.50 | **−0.60** | 0.67 |
| C4 full ρ | 0.82 | **0.59** | 0.68 (raw 0.93) |
| C6 full τ | 0.68 | **0.46** | 0.55 (raw 0.83) |
| C5 pairwise inversions (feasible pairs) | 7/21 = 0.33 | **25/55 = 0.45** | 2/3 = 0.67 (raw 9/105 = 0.09) |
| status | FAIL (C1, C3–C6) | **FAIL (C1–C6)** | — |

Rolling Top-K (F2): the N2O curve stays negative up to K = 9 and reaches only 0.59 at K = 15, i.e. the disagreement is
*broader* than in NH3, where ρ recovers to 0.75 by K = 6.

### 2.2 Where the inversion comes from (V0.2, F3 / F4, USD per t N2O destroyed)
| candidate | atomic rank | T_opt | metal kg | bed m3 | metal | heating | reactor + vessel + ΔP | total | econ. rank |
|---|---|---|---|---|---|---|---|---|---|
| Rh | 1 | 650 °C (grid edge) | 24 | 2.4 | 268 | 347 | 4.6 | 619 | 8 |
| Ir | 2 | 650 °C (grid edge) | 50 | 5.0 | 522 | 347 | 6.1 | 875 | 10 |
| **Ni** | 3 | **445 °C** | 1 350 | 135 | 1.0 | 38 | 54 | **93** | **1** |
| Pd | 4 | 645 °C | 52 | 5.2 | 87 | 339 | 6.2 | 433 | 6 |
| Cu | 5 | 490 °C | 1 433 | 143 | 0.8 | 106 | 58 | 165 | 2 |
| Co | 6 | 495 °C | 1 331 | 133 | 3.1 | 113 | 54 | 171 | 3 |

- Every precious metal sits at the **650 °C upper bound** (binding constraint) and pays the full 347 USD/t heating pool; its
  inventory pool is still 90–520 USD/t. Ni, Cu and Co stay near the available tail-gas temperature, accept a 130–145 m3 bed,
  and pay 38–113 USD/t heating. The inversion is *inventory cost ↔ process severity*, exactly the NH3 mechanism
  (Ru → 425 bar / compressor pool vs Fe → 180 bar).
- Activity leverage at the optimum (re-optimized, TOF × 0.5 / × 2): d ln C / d ln TOF = −0.44 (Rh), −0.60 (Ir), −0.60 (Ni),
  −0.23 (Pd), −0.36 (Cu). Activity still matters for every candidate, but it cannot overcome a 265 000 vs 17 USD/kg price ratio.
- **Equal-price diagnostic** (not part of the frozen protocol; `diagnostics_equal_price.json`): with every metal at the same
  price (or at zero price) the full-set ρ rises to 0.97, τ to 0.89 and the inversion fraction falls to 0.05, so the *bulk* of
  the disagreement is the price channel. The top pair still inverts (Ni 92 vs Rh 107 USD/t at 445–450 °C, Top-3 ρ = −0.50)
  through a second, smaller channel: at fixed 1 wt % loading the bed volume scales with molar mass per site (Rh 1.75× Ni),
  which feeds the reactor and vessel pools. This channel is a modelling convention shared with NH3-FINAL-1.1 and is
  disclosed as such.

### 2.3 Descriptor uncertainty (1 000 draws, ±0.30 eV on every candidate, seed 20260907)
| | V0.1 | **V0.2** |
|---|---|---|
| P(atomic winner = economic winner) | 0.38 | **0.36** |
| P(Top-3 ρ ≥ 0.5) | 0.66 | **0.49** |
| P(all six criteria) | 0.011 | **0.000** |
| economic winner across draws | Cu 100 % | **Ni 73 %, Co 17 %, Cu 11 %** |
| atomic winner across draws | Cu 38 %, Pd 34 %, Pt 27 % | **Ni 32 %, Ir 32 %, Rh 31 %** |

The economic winner is a cheap base metal in 100 % of draws in both versions; the atomic winner is a precious metal in
≥ 63 % of V0.2 draws. The failure of the negative control is robust to the descriptor uncertainty.

## 3. Interpretation for the manuscript
1. The negative control does not deliver what it was designed to deliver. An "inventory-only" reaction inverts as readily as
   the recycle-loop reaction, so recycle / separation / purge restructuring is **sufficient but not necessary** for a
   frontier inversion. The necessary ingredient is a **price-activity trade-off that the process can arbitrage**: whenever
   an operating variable (pressure, temperature) can convert intrinsic activity into inventory, an expensive active metal is
   pushed toward severity and a cheap moderately active metal wins.
2. This *strengthens* the paper's central claim (atomic and economic rankings diverge at the decision frontier) by showing it
   in a second, structurally different process, but it removes the planned "pathway-specific" contrast. The cross-reaction
   section should be reframed: NH3 (pressure severity) and N2O (temperature severity) both invert through inventory ↔
   severity; MeOH (D01 v3) inverts through selectivity ↔ recycle. The pathway that differs is the *severity variable*, not
   whether inversion occurs.
3. What a real rank-preserving control would need (for a V0.3 design, not run here): candidates within one price class
   (e.g. base-metal oxides only, or PGMs only — the equal-price diagnostic shows full-set ρ = 0.97 in that case), or a
   process in which the severity variable is fixed by an external constraint (tail gas that cannot be reheated).

## 4. Limitations (declared)
- Descriptor values, BEP slopes, prefactors, repulsion, dispersion and loading are reconstruction values, not primary
  DFT / experimental data; absolute USD/t figures must not be cited as process economics. The ±0.30 eV MC covers the
  descriptor magnitude but not the functional form of the kinetics.
- All precious-metal optima sit on the 650 °C grid edge; a higher bound would lower their cost but not change the winner
  (Ni's total at 445 °C, 93 USD/t, is below the heating pool alone of any candidate operated above 482 °C).
- Bed volume ∝ molar mass per site (fixed wt % loading) is a convention shared with NH3-FINAL-1.1 and creates a small
  secondary inversion channel (section 2.2).
- Metals are modelled as metallic surfaces; W, Mo, Re, Fe, Co, Ni would be oxides under 3 % O2 at these temperatures.
  They are either infeasible (W, Mo, Re, Au) or cheap enough that their exact activity does not decide the ranking.

## 5. Results paragraph (manuscript-ready, English)
> **A rank-preservation control fails by the same mechanism.** To test whether the frontier inversion requires the recycle
> and separation structure of the ammonia loop, we built a pre-registered control on direct N2O decomposition in nitric-acid
> tail gas — a once-through, dilute, conversion-fixed process in which catalyst activity enters the economics only through
> inventory and operating temperature. With the same 15 metals, the same price basis and per-candidate re-optimization of
> temperature and bed geometry, the atomic ranking (Rh > Ir > Ni > Pd > Cu at 450 °C) again inverts at the decision
> frontier: Ni is the economic winner at 93 USD per t N2O, Rh falls to eighth at 619 USD/t, the Top-3 Spearman correlation
> is −0.50 (identical to ammonia), 25 of 55 feasible pairs invert, and Ni, Co or Cu wins in 100 % of 1 000 descriptor draws
> (±0.30 eV). Every precious metal is driven to the 650 °C bound, where its heating pool alone (347 USD/t) exceeds the
> total cost of Ni operated at 445 °C. With all metals priced equally the full-set correlation rises to 0.97, identifying
> the price–activity trade-off, arbitraged through process severity, as the inversion mechanism. Recycle restructuring is
> therefore sufficient but not necessary; the necessary condition is an operating variable through which an expensive
> active catalyst can buy down its inventory — pressure in ammonia synthesis, temperature in N2O decomposition — and the
> control's pre-registered expectation of rank preservation is rejected.

## 6. Files
`NEGATIVE_CONTROL_V0_1_PREREGISTRATION.md`, `NEGATIVE_CONTROL_V0_2_ADDENDUM.md`, `NEGATIVE_CONTROL_V0_{1,2}_FROZEN.json`,
`configs/n2o_negcontrol_v0_{1,2}.yaml`, `negative_control/*.py`, `outputs/n2o_negctrl_v0_1_20260907T033956Z/`,
`outputs/n2o_negctrl_v0_2_20260907T034138Z/` (each: results.json, provenance.json, canonical_results.csv,
diagnostics_equal_price.json, figures/F1_ranking_propagation.png, F2_rolling_topk.png, F3_cost_decomposition.png,
F4_operating_envelopes.png, F5_mc_rank_preservation.png), `NEGATIVE_CONTROL_V0_{1,2}_CANONICAL_RESULTS.csv`.
