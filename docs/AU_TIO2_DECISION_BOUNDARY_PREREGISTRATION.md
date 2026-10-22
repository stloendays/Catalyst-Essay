# Au/TiO2 decision-boundary analysis (V2.0) — preregistration

Date: 2026-10-19  
Branch: `analysis/au-tio2-decision-boundary-2026-10-19`  
Status: **registered before any V2.0 computation was run**. The commit that adds this file precedes every commit that adds a result file under `artifacts/au_tio2_decision_boundary_v2/`.

Reaction: CO oxidation on Au/TiO2, candidate states 2, 3, 4, 5, 6 nm Au particle diameter.  
Canonical control: the literature-calibrated rank-preservation control (`controls/au_tio2_rank_preservation_v1_1.py`, `data/rank_preservation_control_v1_1.csv`). It is not modified by this work. Everything here is additive.

## 1. Diagnosis that motivates the work

In the canonical control one `(n, m)` pair per Monte Carlo draw is applied to all five particle sizes with
`mass_activity ∝ d^-(n+m)`. For any `n + m > 0` this is strictly monotone in `d`, so the ordering 2 > 3 > 4 > 5 > 6 nm is
preserved in every draw. The downstream mapping is `required_mass ∝ 1/activity` with cost ratio equal to mass ratio.
The reported 10,000/10,000 preservation and ρ = τ = 1.000 are therefore consequences of the construction, not
evidence about the catalyst system. The fixed-condition control still has a legitimate role (it checks that the
implementation does not introduce an inversion where the mapping is monotone), but it cannot carry the evidential
weight of the NH3 or CO2-to-methanol cases, where real counter-channels (metal price and inventory financing;
selectivity, purge and recycle) are present and the leader actually changes.

This work exposes the Au/TiO2 candidates to physically real counter-channels and locates the decision boundary.

## 2. Hypotheses and pre-specified reporting (nothing is tuned to a target)

### H1 — per-candidate uncertainty (V2.0 Monte Carlo)

Replace the shared `(n, m)` draw with per-candidate perturbation: for each draw and each size, the activity carries
an independent lognormal prefactor `exp(ε_i)`, `ε_i ~ N(−σ²/2, σ²)`, in addition to the shared `n ~ U(0.7, 2.0)` and
`m ~ U(0.8, 1.2)` of the canonical control.

- Prediction: full-order preservation probability is below 1 and the adjacent-pair inversion rate increases from
  the 2/3 nm pair to the 5/6 nm pair, because the nominal log-activity gaps decrease (ln 2.161 > ln 1.727 > ln 1.528
  > ln 1.414).
- Reported: full-order preservation probability, mean Spearman ρ, pairwise inversion rate for each adjacent pair,
  the point-estimate (nominal, ε = 0) order, 10,000 draws, seed 20261019.
- The point-estimate order is reported as whatever it is. σ is not tuned to any target.
- Primary σ and its documentation: see §4. A σ sweep is reported as sensitivity; the primary value is fixed here.

### H2 — L1 price channel

The Au price is common to all five sizes and the Au loading is common (4.40 wt%), so the price channel cannot
differentiate candidates: the annual metal cost ratio equals the catalyst-mass ratio exactly. Support/forming cost per
gram of catalyst scales with required catalyst mass, not Au mass, and therefore also leaves every ratio unchanged.
This is an analytic statement; it will be written out and checked numerically.

### H3 — L2 lifetime / replacement channel

Annualized catalyst cost `C_i = m_i · c / τ_i` with `m_i` the V1.1 required catalyst mass and `τ_i` the catalyst
lifetime.

- Free adjacent ratios: the pair (i, j), `d_i < d_j`, flips when `τ_j / τ_i > m_j / m_i`. The thresholds at the V1.1
  nominal masses are expected to be 2.161 (3/2 nm), 1.727 (4/3 nm), 1.528 (5/4 nm) and 1.414 (6/5 nm). They will be
  computed from `data/rank_preservation_control_v1_1.csv` and reported to three decimals.
- Power law `τ ∝ d^q`: every pair flips at the same `q* = n + m` (1.9 at the V1.1 nominal). In the deterministic
  model there is therefore no partially-inverted region: the boundary in the (q, n + m) plane is the line `q = n + m`.
  The 2-D map will show the deterministic line and, overlaid, the V2.0 per-candidate Monte Carlo probabilities of
  "preserved", "partially inverted" and "fully inverted" on a grid of q and n + m (seed 20261020, 2,000 draws per
  cell), which gives the band of finite width that the deterministic model lacks.
- Literature placement: a survey of Au/TiO2 low-temperature CO-oxidation deactivation (carbonate accumulation versus
  sintering, 273–313 K) is placed on the map. If the literature supports `q ≥ 1.9` under some conditions, that is
  stated together with the condition window in which `q < 1.9` holds. No literature value is fabricated: where the
  literature gives a mechanism but no numerical `q`, the note says so and uses a theory-derived bound with its
  assumptions stated.

### H4 — L3 operating freedom and the combined L2 + L3 case

L3 reuses the semi-open operating-freedom results in `data/rank_preservation_semiopen_v1_3_summary.csv`
(273–293 K moderate: 92.16% exact preservation, mean ρ 0.99214; 273–313 K moderate: 72.62%). They are not rerun.

Combined L2 + L3: the V1.3 objective is extended by the lifetime factor, `J = (m_required / m_ref) · (d / d_ref)^−q +
w_T H(T) + w_R O(O2/CO)`, and run at the moderate stress level over 273–293 K with the V1.3 seed (20260907 + 2) so
that `q = 0` must reproduce 0.9216 exactly (a correctness check, pre-specified). `q` is then set to the values that
the literature survey supports and to a sensitivity set {0.5, 1.0, 1.5, 1.9, 2.5, 3.0}.

- Prediction: preservation decreases monotonically with q; the crossing of 50% full preservation lies near
  `q ≈ n + m` of the nominal model (1.9). This is a prediction to be tested, not a target.

## 3. Fixed inputs

- Activity and required-mass anchors: `data/rank_preservation_control_v1_1.csv` (2/3/4/5/6 nm; mass activity 9.6548,
  4.4686, 2.5869, 1.6930, 1.1973 µmol g⁻¹ s⁻¹; required mass 19.505, 42.143, 72.797, 111.235, 157.284 mg;
  burden vs best 1 / 2.161 / 3.732 / 5.703 / 8.064).
- Reference anchor: Janssens et al., J. Catal. 240 (2006) 108–113, DOI 10.1016/j.jcat.2006.03.008.
- Size exponent: Overbury et al., J. Catal. 241 (2006) 56–65, DOI 10.1016/j.jcat.2006.04.018 (4.5 wt% series
  d^−0.9±0.2; 7.2 wt% series d^−1.7±0.2).
- Shared exponent ranges: `n ~ U(0.7, 2.0)`, `m ~ U(0.8, 1.2)` (canonical control config).
- V1.3 kinetic inputs (Shao 2018 Ea values, Diemant 2021 reaction-order bounds): as in
  `data/rank_preservation_semiopen_v1_3.py`.

## 4. Per-candidate scatter σ (documented, not tuned)

The canonical control has no per-candidate scatter. The literature gives sample-to-sample variation but no
directly reported per-size standard deviation for one preparation series. The primary σ is therefore derived from
the one published statistic that bounds the residual scatter of individual size points around the size–activity
power law:

- Overbury et al. report `TOF ∝ d^−0.9±0.2` (4.5 wt%) over 2–10 nm. For a least-squares fit of ln TOF on ln d, the
  exponent standard error is `SE_n = s / sqrt(Σ(x_k − x̄)²)` with `s` the residual standard deviation in ln TOF. The
  abstract does not give the number of size points; with sizes spread over 2–10 nm (ln range 1.61) and 4–6 points,
  `sqrt(Σ(x_k − x̄)²)` lies between about 1.1 and 1.4, which gives `s ≈ 0.2 × 1.25 ≈ 0.25`.
- Primary σ = 0.25 (ln units; multiplicative scatter of about ×/÷ 1.28 at one standard deviation).
- Sensitivity set: σ ∈ {0.10, 0.25, 0.50, 0.69}. σ = 0.10 matches the "moderate" per-candidate prefactor CV already
  used in the semi-open test; σ = 0.69 = ln 2 represents factor-of-two sample-to-sample scatter, the order of the
  disagreement between the two Overbury series at 6 nm (3^(1.7−0.9) = 2.41).
- The assumption on the number of fitted points is stated above; if the full paper gives the point count, the
  derivation is to be updated in the results document and the primary σ re-derived, but the pre-registered primary
  value used for the headline numbers is 0.25.

## 5. Seeds and sizes

| Computation | Seed | Draws |
|---|---:|---:|
| V2.0 per-candidate MC (each σ) | 20261019 | 10,000 |
| 2-D (q, n + m) boundary map | 20261020 | 2,000 per grid cell |
| L2 + L3 combined (each q) | 20260907 + 2 (V1.3 moderate) | 10,000 |

## 6. What this analysis does not claim

- No absolute USD values are introduced: the lifetime channel is parametrized as ratios.
- No prediction of the industrial choice is made; the deliverable is the location and explanation of the boundary.
- The canonical control remains the canonical fixed-condition control; V2.0 is SI-level material until the author
  decides otherwise.
