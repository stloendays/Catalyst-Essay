# Unified leverage criterion for ranking inversion — working note

Date: 2026-10-19. This is an internal note, not manuscript text. It states one inequality that the three cases
(NH3, CO2-to-methanol, Au/TiO2) share, and places each case's committed numbers on it. Every number is taken from a
repository file named inline.

## 1. The inequality

Take two candidates i and j with upstream activity `A_i > A_j` (i is the laboratory or atomic leader) and a
lower-is-better downstream objective `J`. Write the catalyst-dependent part of `J` as a product of channel
penalties that act multiplicatively on the inventory set by the activity:

`J_i ∝ (1 / A_i) · Π_k π_k,i`

where the product runs over the downstream channels k that *differentiate* i from j (a channel with
`π_k,i = π_k,j` cancels and is not in the product). Then

**economic inversion (J_i > J_j) ⇔ A_i / A_j < Π_k (π_k,i / π_k,j).**

The left side is the upstream advantage; the right side is the combined downstream penalty ratio over the
differentiating channels. Each channel contributes a factor; the leader is lost exactly when the product of the
penalty ratios exceeds the activity ratio. Channels that act on a non-inventory part of J (process reoptimization,
purge) enter through an effective ratio defined by the full model rather than a closed form; where that is the case
below, the effective ratio is reported as the number the full model gives.

A log form is convenient for a map: inversion ⇔ `Σ_k ln(π_k,i / π_k,j) > ln(A_i / A_j)`.

## 2. NH3 — Ru vs Fe (NH3-FINAL-1.2)

Source: `docs/SI_TABLE_NH3_CHANNEL_ABLATION.md` and the files it cites
(`analysis/fe_bridge_backward_2026_09_29/nh3_1_2/inversion_layer_common_reference.csv`,
`figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv`,
`provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json`).

| Level | Channel | ln(A_Ru/A_Fe) | Σ ln(penalty ratio Ru/Fe) | Inverted? |
|---|---|---:|---:|---|
| L0 | inventory only (common reference, 673 K) | ln 606.5 = 6.41 | ln(MW ratio 1.810) = 0.59 | no (Ru demand 263.5 kg < Fe 88,301.9 kg) |
| L1 | + metal price (53,852.5 / 8.0 USD/kg) | 6.41 | 0.59 + ln 6,731.6 = 0.59 + 8.81 = 9.41 | **yes**: replacement 4.092 > 0.204 USD/t (ratio 20.09 = e^(9.41−6.41)) |
| L2 | full process at equal price (price channel removed) | — | effective: Ru 10.237 < Fe 11.516 USD/t | no |
| L3 | full process at canonical price | — | effective: Ru 16.633 > Fe 11.516 USD/t | **yes** |

Reading: the differentiating channel is the metal price; its ratio (6,732) exceeds the activity ratio (606.5) by a
factor of 11, and the molar-mass factor adds 1.81. Process optimization (L2) does not invert the pair on its own; it
reshapes the gap (Ru − Fe 3.889 USD/t at L1, 5.117 USD/t at L3). The canonical backward statement "Ru would need a
115-fold activity gain" (`results.json` → `Ru_activity_break_even_multiplier` 114.667) is the activity ratio that
makes the inequality an equality after full reoptimization.

## 3. CO2-to-methanol — 5 wt% Re / 250 °C against the field (D01 v3 four-state example)

Source: `docs/MEOH_RANKING_INVERSION.md` (local leverage at 5 wt% Re / 250 °C: STY 0.00289, single-pass conversion
0.0588, CH4 suppression 0.376; `data/meoh/meoh_candidate_ranking_D01v3.csv` holds the unrounded 0.0028943 /
0.0588278 / 0.3757939).

Here the differentiating channel is not an inventory multiplier but selectivity acting on H2 feed loss, loop inert
accumulation and purge. The local leverage `λ_x = ∂ ln(NPC) / ∂ ln(x)` is the per-channel coefficient in the log
form of the inequality: a relative change `δ` in channel x moves ln J by `λ_x δ`. The committed numbers give

`λ_CH4-suppression / λ_STY = 0.37579 / 0.00289 = 130`.

A 1% improvement in CH4 suppression moves the cost objective 130 times as far as a 1% improvement in space-time
yield. On the inequality, the upstream advantage (STY) enters with weight 0.00289 per ln unit and the downstream
penalties (conversion 0.0588; selectivity through H2 loss, inert accumulation and purge 0.376) with weights 20 and
130 times larger. Two readings from the four-state table of `docs/MEOH_RANKING_INVERSION.md`:

- the STY leader 1 wt% Re / 250 °C (65 g MeOH g_Re⁻¹ h⁻¹) has a 3.6-fold STY advantage over the economic winner
  5 wt% Re / 200 °C (18), yet costs more (975 vs 943 €/t at 2% purge) because the winner's higher single-pass
  conversion (0.33 vs 0.23) outweighs it: `0.00289 · ln 3.6 = 0.0037` against `0.0588 · ln(0.33/0.23) = 0.021`
  (first-order reading with the local coefficients; the full model gives the committed 3.4% gap);
- 5 wt% Re / 250 °C has the highest conversion (0.40) and the highest cost (1,258 €/t) because `S_CH4 = 0.25` raises
  the loop non-H2/CO2 fraction to 0.52 and the H2 feed cost to 886 €/t: the selectivity channel, weight 0.376,
  dominates every other term.

The channel is the one that the ammonia case lacks and the Au/TiO2 case cannot have (single product).

## 4. Au/TiO2 — 2 nm vs 6 nm (and each adjacent pair)

Source: `docs/AU_TIO2_DECISION_BOUNDARY_V2_RESULT.md`, `data/rank_preservation_control_v1_1.csv`,
`artifacts/au_tio2_decision_boundary_v2/`.

| Level | Channel | A_i/A_j (2 nm / 6 nm) | Π penalty ratio (2 nm / 6 nm) | Inverted? |
|---|---|---:|---:|---|
| L0 | inventory only | 8.064 | 1 (common composition, fixed condition) | no, by construction |
| L1 | + Au price, + support/forming cost | 8.064 | **1 exactly** (common metal, common loading; support cost ∝ catalyst mass) | no, and cannot be |
| L2 | + lifetime, τ ∝ d^q | 8.064 = 3^1.9 | (τ_6/τ_2) = 3^q | inverted ⇔ q > 1.9; adjacent pairs flip at τ_j/τ_i > 2.161, 1.727, 1.528, 1.414 |
| L3 | + operating freedom | effective | effective | full order kept in 92.16% (273–293 K), 72.62% (273–313 K) |
| L2 + L3 | both | effective | effective | 2 nm leader kept in 97.56% at q = 1, 61.61% at q = 1.5, 5.21% at q = 1.9 |

The price channel that inverts NH3 is identically 1 here, and the selectivity channel that inverts methanol has no
counterpart. The only channel with a non-unit ratio is the lifetime, and the inequality gives its boundary in closed
form: `q* = n + m`. The literature places the 273–313 K carbonate-limited powder window at q ≈ 0 (below the
boundary) and the Ostwald-ripening regime of sub-3 nm Au at q ≥ 3 (above it); see the result document, §4.

## 5. The three cases on one line

| Case | Upstream advantage ln(A_i/A_j) | Differentiating channel(s) | Σ ln(penalty ratio) | Outcome |
|---|---:|---|---:|---|
| NH3 Ru/Fe | 6.41 | metal price × molar mass | 9.41 | inverted (Fe < Ru) |
| MeOH 5% Re / 250 °C | λ_STY-weighted, 0.00289 per ln unit | CH4 selectivity → purge/recycle, λ = 0.376 | 130 × the upstream weight | inverted (STY leader ranks last in cost) |
| Au/TiO2 2/6 nm | 2.09 (= 1.9 ln 3) | lifetime only (price ratio = 1) | q ln 3 | inverted ⇔ q > 1.9; measured low-T window q ≈ 0 → kept |

The statement the three cases support together: a laboratory or atomic leader is lost when some downstream channel
differentiates the candidates by more than their activity ratio, and kept when every differentiating channel has a
ratio of one or the differentiating channel stays below the boundary. "Locate and explain the decision boundary"
is the claim; the inequality is how the location is written down.
