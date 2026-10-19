# Au/TiO2 decision-boundary analysis V2.0 — result

Date: 2026-10-19  
Preregistration: `docs/AU_TIO2_DECISION_BOUNDARY_PREREGISTRATION.md` (committed before any computation)  
Code: `controls/au_tio2_decision_boundary_v2/` (config, runner, headline gate, map renderer)  
Outputs: `artifacts/au_tio2_decision_boundary_v2/` (CSV, `summary.json`, `FROZEN_HASHES.json`)  
CI: `.github/workflows/au-tio2-decision-boundary-v2.yml`  
Status: SI-level, additive. The canonical fixed-condition control (`controls/au_tio2_rank_preservation_v1_1.py`,
`data/rank_preservation_control_v1_1.csv`) is unchanged and remains the fixed-condition control.

## 1. Diagnosis (confirmed)

In the canonical control, each Monte Carlo draw applies one `(n, m)` pair to all five sizes with
`mass_activity ∝ d^-(n+m)`. For any `n + m > 0` the mapping is strictly monotone in `d`, so the order
2 > 3 > 4 > 5 > 6 nm is preserved in every draw; `required_mass ∝ 1/activity` and the cost ratio equals the mass ratio.
The 10,000/10,000 preservation and ρ = τ = 1.000 follow from the construction. The runner reproduces this:
with the per-candidate scatter switched off (σ = 0) the V2.0 code gives full preservation 1.0000
(`mc_v2_per_candidate.csv`, row `sigma_ln = 0`).

The fixed-condition control keeps its narrow role: it shows that the implementation does not introduce an inversion
where the physical mapping is monotone. The evidential content about the catalyst system now comes from the three
analyses below, which expose the five candidates to real counter-channels and locate the boundary.

## 2. Headline numbers

| Claim | Evidence | File |
|---|---|---|
| Per-candidate activity scatter alone (σ = 0.25 ln units, shared n ~ U(0.7, 2.0), m ~ U(0.8, 1.2), 10,000 draws, seed 20261019) preserves the full order in **77.70%** of draws, mean ρ **0.9754**; the 2 nm leader wins in **99.41%** | `summary.json` → `V2_0_per_candidate_mc_primary` | `artifacts/au_tio2_decision_boundary_v2/mc_v2_per_candidate.csv` |
| Adjacent-pair inversion rates rise with size as the nominal activity gaps shrink: 3/2 nm **0.59%**, 4/3 nm **3.56%**, 5/4 nm **7.74%**, 6/5 nm **11.13%**; no draw is fully inverted | same | same |
| Point-estimate order (nominal n = 0.9, m = 1.0, no scatter): 2 > 3 > 4 > 5 > 6 nm | `summary.json` → `point_estimate_order_nominal` | same |
| σ sensitivity: full preservation 99.66% (σ = 0.10), 77.70% (0.25), 35.44% (0.50), 21.20% (0.69 = ln 2); 2 nm wins 100 / 99.41 / 90.02 / 80.63% | `mc_v2_per_candidate.csv` | same |
| L1: a common Au price and a support/forming cost per gram catalyst leave every cost ratio equal to the canonical burden ratio (1 / 2.161 / 3.732 / 5.703 / 8.064); the price channel cannot differentiate | `l1_price_channel_check.csv` (9 price × support combinations, all ratios equal, ρ = 1) | same |
| L2: adjacent lifetime ratios that flip each pair: **τ3/τ2 > 2.161, τ4/τ3 > 1.727, τ5/τ4 > 1.528, τ6/τ5 > 1.414**; under τ ∝ d^q every pair flips at the same **q\* = n + m = 1.9** (range 1.5–3.2 over the shared exponent ranges) | `l2_adjacent_flip_thresholds.csv`, `summary.json` → `L2_lifetime` | same |
| L2 with per-candidate scatter (σ = 0.25, 2,000 draws per cell, seed 20261020): the deterministic line q = n + m broadens into a partial-inversion band. Along the fixed n + m = 1.9 row: full preservation 0.668 at q = 0, below 50% from q ≈ 0.5 (0.463), 2 nm-winner probability 0.529 at q = 1.5 and 0.194 at q = 1.9, full inversion 0.320 at q = 3.0 and 0.724 at q = 4.0 | `l2_boundary_map_q_vs_nm.csv`, `l2_boundary_map_q_vs_nm.png` | same |
| Same with the shared exponents sampled (n ~ U(0.7, 2.0), m ~ U(0.8, 1.2)): full preservation 0.775 at q = 0, below 50% from q ≈ 0.9 (0.521 at 0.8, 0.438 at 1.0); 2 nm-winner probability crosses 50% at q ≈ 1.9–2.0 (0.581 at 1.8, 0.457 at 2.0); full inversion exceeds 50% only beyond q ≈ 3.8 (0.478 at 3.8, 0.571 at 4.0) | `l2_q_cut_shared_nm_sampled.csv` | same |
| L3 (read, not rerun): semi-open operating freedom, moderate stress: 273–293 K **92.16%** exact preservation, mean ρ 0.99214; 273–313 K **72.62%**, mean ρ 0.96802 | `data/rank_preservation_semiopen_v1_3_summary.csv` rows `primary_273_293K,moderate` and `sensitivity_273_313K,moderate` | `data/rank_preservation_semiopen_v1_3_summary.csv` |
| L2 + L3 combined (273–293 K, moderate, V1.3 seed 20260909, 10,000 draws): q = 0 reproduces 0.9216 / 0.99214 exactly; q = −0.5 → 97.91%; q = 0.5 → 77.48%; q = 1.0 → 47.36% (2 nm still wins 97.56%); q = 1.5 → 8.99% (2 nm wins 61.61%); q = 1.9 → 0.11% (2 nm wins 5.21%, fully inverted 8.64%); q = 2.5 → fully inverted 64.50%; q = 3.0 → 90.08% | `l2_l3_combined_273_293K_moderate.csv` | same |

The CI workflow reruns the runner and asserts every number in this table (`check_headlines.py`), then compares the
regenerated CSV and `summary.json` byte-for-byte with the committed artifacts.

## 3. Channel ladder (mirror of the NH3 ladder in `docs/SI_TABLE_NH3_CHANNEL_ABLATION.md`)

| Level | Channel switched on | Differentiates the sizes? | Result |
|---|---|---|---|
| L0 | inventory only (fixed condition, common composition) | yes, monotonically by construction | 2 > 3 > 4 > 5 > 6 nm; burden 1 / 2.161 / 3.732 / 5.703 / 8.064; preserved in 10,000/10,000 shared-exponent draws |
| V2.0 | per-candidate activity scatter at L0 | yes, as noise on the gaps | full order kept in 77.70%; leader kept in 99.41%; inversions concentrate in the 5/4 and 6/5 nm pairs |
| L1 | + Au price, + support/forming cost | **no** (common price and loading; support cost ∝ catalyst mass) | ratios unchanged; the price channel that inverts NH3 (Ru/Fe price ratio 6,732) is identically 1 here |
| L2 | + lifetime / replacement | yes, if lifetime grows with size | flip when τ_j/τ_i exceeds the mass ratio (2.161, 1.727, 1.528, 1.414 for adjacent pairs); full inversion at q\* = n + m = 1.9 |
| L3 | + operating freedom (T, O2/CO per candidate) | yes, weakly (size-dependent E_a) | 92.16% (273–293 K), 72.62% (273–313 K) |
| L2 + L3 | both | yes | 50% full-preservation crossing between q = 0.5 and 1.0; 2 nm-winner crossing between q = 1.5 and 1.9 |

### L1 in one line

Annual metal cost of size i is `m_i × w_Au × p_Au / τ` and the support/forming cost is `m_i × c_s / τ`, with `w_Au`,
`p_Au`, `c_s` and (at L1) `τ` common to all sizes. Every ratio `C_i / C_j` therefore equals `m_i / m_j`. The channel
that carries the ammonia inversion (metal price acting on inventory) is structurally absent when the candidates share
one metal and one loading.

### L2 derivation

`C_i = m_i c / τ_i`. For `d_i < d_j`, `C_j < C_i ⇔ τ_j / τ_i > m_j / m_i`. With `m ∝ d^(n+m)` and `τ ∝ d^q`,
`C ∝ d^(n+m−q)`: the order is preserved for `q < n + m`, degenerate at `q = n + m` and fully inverted for `q > n + m`.
In the deterministic model there is no partial region; the per-candidate scatter supplies it (map in
`l2_boundary_map_q_vs_nm.png`: the dashed line is `q = n + m`; colour is the Monte Carlo probability).

## 4. Literature placement of the lifetime exponent q (Au/TiO2 CO oxidation, 273–313 K)

The literature does not report a lifetime-versus-size exponent for Au/TiO2. What it reports is the mechanism of
activity loss and whether particle growth occurs under the relevant conditions. The placement below is therefore a
mechanism-based placement with the theory-derived bound stated explicitly; no numerical q is attributed to any paper.

**Evidence consulted in this work (DOI given where it was verified in this session).**

1. Janssens et al., J. Catal. 240 (2006) 108–113, DOI 10.1016/j.jcat.2006.03.008 — the V1.1 rate anchor is the
   activity *after* a 10–15 h stabilization at 273.15 K (config field `stabilization_time_h`): an initial activity
   loss followed by a stable plateau is built into the canonical anchor.
2. Saavedra, Powell, Panthi, Pursell, Chandler, J. Catal. 307 (2013) 37–47, DOI 10.1016/j.jcat.2013.06.021 — on a
   commercial Au/TiO2 powder, deactivation in the feed is a loss of active sites, not of per-site activity
   (Michaelis–Menten analysis); in situ FTIR shows carbonate-like species accumulating, their amount correlating
   with steady-state activity; IR of adsorbed CO, control experiments and earlier TEM rule out particle growth as
   the cause.
3. Azar, Caps, Morfin, Rousset, Piednoir, Bertolini, Piccolo, J. Catal. 239 (2006) 307–312,
   DOI 10.1016/j.jcat.2006.02.012 — at 22 °C and 80–110 °C a Au/TiO2 reference catalyst (3.7 ± 1.5 nm) loses about
   a factor of three in the first run and then stabilizes; the loss is attributed to carbonate-like species at the
   Au periphery; activity is fully restored by heating in vacuum at 400 °C and progressively by a small H2 admixture
   in the feed; no particle growth is reported.
4. Clark, Dai, Overbury, Catal. Today 126 (2007) 135–142, DOI 10.1016/j.cattod.2006.10.008 — operando FTIR/MS at
   298 K: product CO2 is retained on the TiO2 support as carbonate/bicarbonate.
5. Raphulu et al., Gold Bull. 42 (2009) 328–336, DOI 10.1007/BF03214955 — over 12 months of *storage* the activity
   loss combines Au(III) reduction, agglomeration, loss of hydroxyls and carbonate/formate build-up; no size
   dependence is resolved.
6. Parker and Campbell, Top. Catal. 44 (2007) 3–13, DOI 10.1007/s11244-007-0274-z, and Campbell, Parker, Starr,
   Science 298 (2002) 811, DOI 10.1126/science.1075094 — on Au/TiO2(110) the metal chemical potential rises with
   decreasing size more steeply than the Gibbs–Thomson relation, so sub-3 nm particles are thermodynamically the
   least stable against ripening; sintering kinetics were measured at 200–700 K by temperature-programmed LEIS, not
   under reaction gas.
7. Lai and Goodman, J. Mol. Catal. A 162 (2000) 33 (as cited by Ono and Roldan-Cuenya, Catal. Lett.; DOI not
   verified in this session) — in situ STM on Au/TiO2(110): exposure to CO/O2 (2:1) or O2 at 13.33 mbar and room
   temperature produces Ostwald ripening with a bimodal size distribution, attributed to O2-induced weakening of
   Au–Au bonds. Yang et al. (cited in Niu et al., Nanoscale 2018, DOI 10.1039/c7nr06323g) report Ostwald ripening of
   Au clusters on TiO2 between 300 and 410 K, accelerated by a CO + O2 mixture.
8. Denkwitz, Zhao, Hörmann, Kaiser, Plzak, Behm, J. Catal. 251 (2007) 363–373, DOI 10.1016/j.jcat.2007.07.029 —
   stability of unconditioned Au/TiO2 in near-stoichiometric and O2-rich feeds; the full text could not be retrieved
   in this session, so only its existence and scope are cited here. The same group's 2009 "elevated temperatures"
   study (ScienceDirect PII S0021951709002553) was likewise not readable here.

**Two mechanisms, two signs of q.**

- *Carbonate/bicarbonate accumulation* (items 1–4): the dominant loss mechanism for powder Au/TiO2 at 273–313 K
  and atmospheric pressure. It acts on perimeter/support sites, is reversible by thermal or H2 regeneration, and
  none of the studies resolves a size dependence of the fractional loss. Under this mechanism the lifetime between
  regenerations is, to first order, size-independent (q ≈ 0), and the cost channel is a regeneration frequency and
  downtime that is common to all sizes rather than a replacement cost. This is the condition window of the
  canonical anchor (Janssens 2006: 273.15 K, 1% CO / 21% O2, stabilized after 10–15 h).
- *Sintering / Ostwald ripening* (items 6–7): the size-dependent chemical potential makes the smallest particles
  ripen fastest. If the lifetime is defined as the time for a particle to grow by a fixed relative amount, classical
  ripening kinetics give `d^3 ∝ t` (bulk/volume diffusion) or `d^4 ∝ t` (surface diffusion), i.e. **q = 3–4 ≥ 1.9**,
  and the Campbell stronger-than-Gibbs–Thomson energetics push q further up for sub-3 nm particles. This is a
  theory-derived bound, not a measured value, and it applies where ripening is the operative loss mechanism: model
  Au/TiO2(110) under CO/O2 at room temperature (item 7), 300–410 K (Yang et al.), and, by the energetics of item 6,
  any long-duration operation of sub-3 nm particles where carbonate removal (regeneration) is done at temperatures
  high enough to mobilize Au.

**Placement on the map.**

- Window where **q < 1.9** holds: powder Au/TiO2 at 273–313 K, atmospheric pressure, hours-to-days time scale,
  where carbonate accumulation is the loss mechanism and particle growth is ruled out (items 1–4). Here q ≈ 0 and
  the order is kept; the combined L2 + L3 analysis at this q is the committed 92.16% (273–293 K).
- Window where **q ≥ 1.9 is supported**: operation or regeneration under conditions where Ostwald ripening of
  sub-3 nm Au is active (model-catalyst evidence at room temperature in CO/O2 at tens of mbar; 300–410 K), and any
  lifetime long enough for ripening to dominate the reversible carbonate loss. Here the lifetime channel can invert
  the ranking (q = 3 in the combined analysis: fully inverted in 90.08% of draws), and the economic choice would move
  to the larger particles.
- Intermediate: where both act, q ∈ (0, 1.9); the 2 nm leader is kept in 97.56% of combined draws at q = 1.0 and
  in 61.61% at q = 1.5, while the full order is already lost in most draws. The leader is more robust than the
  full order throughout.

What this does *not* say: it does not assert that sintering is negligible. It says that in the measured
low-temperature powder window the reported mechanism is carbonate accumulation with particle growth excluded, and
that outside that window the ripening energetics of small Au particles place q at or above the inversion exponent.

## 5. Interpretation for the three-tier framing

The Au/TiO2 case measures "laboratory → catalyst requirement". The ladder shows why its ranking is kept where the
ammonia and methanol rankings are not: the channel that inverts ammonia (metal price on inventory) is identically
1 for candidates that share one metal and one loading, and the channel that inverts methanol (selectivity acting on
purge and recycle) has no counterpart in a single-product oxidation. The one channel that can invert Au/TiO2 is the
lifetime, and its boundary is located at τ_j/τ_i = m_j/m_i for each pair and at q\* = n + m = 1.9 for a power law,
with the literature placing the measured 273–313 K powder window below it and the ripening regime above it.

## 6. Deviations from the preregistration

- The (q, n + m) map grid and the combined-case q set were extended with negative q values (q = −1.0, −0.5 on the
  map; q = −0.5 in the combined case) before the first run, to show the kept side of the boundary where a shorter
  lifetime of the larger particles reinforces the activity order. The pre-registered values are all present and
  unchanged; the extension only adds columns. The σ basis, seeds, draw counts and all thresholds are as registered.
- The preregistration predicted the 50% full-preservation crossing of the combined case "near q ≈ 1.9". The
  observed crossing is between q = 0.5 and 1.0 (77.48% → 47.36%); it is the 2 nm-*winner* probability that crosses
  50% between q = 1.5 and 1.9. The prediction was wrong for the full order and is reported as such: with five
  candidates and per-candidate kinetic scatter, the full order is lost well before the leader is.

## 7. Limits

- σ = 0.25 is derived from the exponent uncertainty of one published series under a stated assumption on the
  number of fitted points (preregistration §4); the σ sweep shows the result is sensitive to it (77.70% at 0.25,
  35.44% at 0.50), which is why the σ basis is documented rather than tuned.
- The lifetime channel is parametrized as ratios; no absolute USD is introduced.
- The literature placement is mechanism-based. No study gives q directly; the q ≥ 1.9 bound is derived from
  ripening kinetics under stated assumptions.
- The combined L2 + L3 case keeps the V1.3 generic monotone process penalties, which are not an industrial TEA.
