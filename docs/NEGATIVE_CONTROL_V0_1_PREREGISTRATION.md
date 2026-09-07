# NEGATIVE CONTROL V0.1 — rank-preservation reaction (N2O decomposition) — pre-registration

Written 2026-09-07 before any calculation. Frozen together with `configs/n2o_negcontrol_v0_1.yaml` in
`NEGATIVE_CONTROL_V0_1_FROZEN.json` (SHA-256). Nothing in NH3-FINAL-1.1, DISCOVER V1, the cross-model protocol or the
frozen scorer is read for modelling or modified; the NH3 canonical `results.json` is read only to recompute the comparison
metrics listed in section 6.

## 1. Question
Does the inversion of atomic and economic catalyst rankings found for ammonia synthesis (NH3-FINAL-1.1: atomic Ru > Os > Fe,
economic Fe > Ru > Os, Top-3 Spearman −0.50) reflect a general property of multiscale propagation, or is it specific to
reactions whose economics are restructured by recycle / separation / purge? A negative control is a reaction in which the
atomic ranking is expected to survive propagation because those restructuring channels are absent.

## 2. Hypothesis (pre-registered expectation)
Direct N2O decomposition in nitric-acid tail gas (once-through, no recycle, no separation, no purge, dilute feed, conversion
fixed by regulation) couples catalyst activity to economics only through **catalyst inventory / reactor demand** and through
the **operating temperature needed to reach the fixed conversion** (heating duty, bed pressure drop). The expectation is
therefore that the atomic ranking is preserved to a much larger degree than in NH3:
- atomic Top-1 remains economic Top-1 after per-candidate process re-optimization;
- Top-3 / Top-5 Spearman are positive (≥ 0.5) where NH3 gives −0.50;
- the pairwise inversion fraction is small (≤ 0.15);
- the only channel able to invert pairs is the metal price (inventory cost pool), not a process-structure pool.
If the deterministic run fails one of these criteria, the result is reported as a failed negative control, not re-tuned.

## 3. What is a source fact and what is a reconstruction
| item | status |
|---|---|
| Stoichiometry 2 N2O → 2 N2 + O2; two-step mechanism (N2O dissociation to O*, O2 recombination); O2 inhibition; experimental noble-metal order Rh > Pd > Pt, supported Ru/Rh/Ir > Pd > Cu (Kapteijn et al. 1996 review; Data-driven catalyst design for direct catalytic N2O decomposition, 2026, PMC13522588) | source facts (secondary/summary level; primary tables not re-read in this session) |
| Tail-gas basis 200 000 Nm3/h, 1500 ppmv N2O, ~10 bar, tertiary position, ≥ 98 % abatement, 800–1900 ppmv range | source facts (EnviNOx / nitric-acid abatement literature summaries) |
| dE_O values per metal, BEP parameters (a1, b1), desorption barrier rule, prefactors, dispersion, loading, bed density | **reconstruction v0.1**: literature-consistent magnitudes and ordering; not primary-verified; uncertainty ±0.30 eV propagated by MC |
| Reactor CAPEX correlation, Turton vessel pressure premium, CRF, capacity factor, electricity price | copied from NH3-FINAL-1.1 constants (unchanged) |
| Fuel price 8 USD/GJ, 60 % heat recovery, expander efficiency 0.85, catalyst life 5 y, recovery 0 | declared assumptions |

Because the descriptor set is a reconstruction, the deliverable is the **rank structure and its cost-pool mechanism**, not
absolute USD/t values. The absolute values are reported but must not be cited as process economics.

## 4. Frozen chain
```
dE_O (descriptor) -> BEP barriers R1, R2 -> steady-state two-step MKM with O2 inhibition (TOF(T, pN2O, pO2))
  -> atomic ranking at one reference condition (450 °C, 10 bar, 1500 ppmv N2O, 3 % O2)
  -> isothermal PFR at fixed 98 % conversion: required sites -> metal mass (dispersion 0.30) -> bed volume (1 wt %, 1000 kg/m3)
  -> per-candidate optimization over T (350-650 °C, 5 °C) x bed diameter D (2-8 m): pressure drop (Ergun) and vessel L/D
  -> cost pools (USD per t N2O destroyed): metal inventory, reactor base CAPEX, vessel pressure premium,
     heating fuel above 420 °C, expander work lost to pressure drop
  -> feasible (V <= 300 m3, dP <= 0.5 bar) economic ranking
```
Every candidate is optimized separately; no shared operating point is used for the economic ranking.

## 5. Outputs (fixed list)
atomic ranking; economic ranking (raw and feasible-censored); Top-3 / Top-5 / full-set Spearman; Kendall τ (full set and
Top-5); atomic winner = economic winner (bool); pairwise inversion count and fraction (over feasible pairs); per-candidate
cost decomposition at the optimum; activity leverage d ln C / d ln TOF at the optimum (α = 0.5, 1, 2 re-optimized); MC
(1000 draws, seed 20260907, ±0.30 eV uniform on every candidate) fraction of draws satisfying C1 and C2; figures F1 ranking,
F2 rolling Top-K, F3 cost decomposition, F4 operating envelopes (cost vs T per candidate), F5 MC rank-preservation.

## 6. Comparison with NH3-FINAL-1.1 (read-only)
The same six metrics are recomputed from `outputs/nh3_final_20260905T134204Z/results.json` (activity_order,
raw_economic_order, feasible_economic_order) so that the two reactions are compared with one definition.

## 7. Criteria (frozen, see manifest `rank_preservation_criteria`)
C1 atomic winner = economic winner; C2 Top-3 ρ ≥ 0.5; C3 Top-5 ρ ≥ 0.5; C4 full-set ρ ≥ 0.85; C5 pairwise inversion fraction
≤ 0.15; C6 full-set Kendall τ ≥ 0.70. Pass = all six on the deterministic run. Failure is recorded, not tuned away.

## 8. What is not allowed after freezing
Changing dE_O values, BEP parameters, grids, cost constants, criteria or the reference condition in response to the result.
Any such change is NEGATIVE CONTROL V0.2 with its own frozen file.
