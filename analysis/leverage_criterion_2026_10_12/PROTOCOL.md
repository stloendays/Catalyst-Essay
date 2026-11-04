# Protocol: when does an upstream advantage survive process economics? (pre-registered 2026-10-12)

Committed before any decomposition, criterion value or score below was computed. The frozen plant models and the
frozen outcomes (which rankings are preserved or inverted) are inputs; nothing here re-fits or changes them. Any
analysis added after the first scored run is labelled **exploratory** in the outputs and the README.

## 1. Question and hypothesis

Question: for two candidates i (better upstream metric) and j, when does the plant-cost model keep i ahead?

Hypothesis (H): the upstream order survives when the upstream metric controls the dominant catalyst-responsive cost
change between the two candidates, and inverts when another property in which they differ controls a larger, opposite
cost change. Expected carriers of the inversion: ammonia, metal price (catalyst inventory); methanol, CO/CH4
selectivity (purge, recycle and H2 loss); Au/TiO2, none.

Design note. An exact decomposition of the re-optimized cost difference satisfies sum(phi) = C_j - C_i, so the rule
"inversion if the non-upstream attribution exceeds the upstream attribution with opposite sign" reduces to
sign(C_j - C_i) and cannot be wrong. The **predictive** criterion is therefore computed only from information at the
upstream leader's own plant optimum (its elasticities and the property differences), and the exact decomposition is
used for attribution, not for scoring.

## 2. Cases (fixed in advance)

Actual outcome of a case: **inverted** if C_j < C_i by more than 1e-9 x max(C_i, C_j), otherwise **preserved**
(ties count as preserved, as in the frozen group metrics).

| System | Frozen model and plant cost | Cases (i = better upstream metric) |
|---|---|---|
| Au/TiO2 | `controls/au_tio2_rank_preservation_v1_1.py`: required catalyst mass at the literature-anchored fixed condition (no operating optimization) | adjacent sizes 2-3, 3-4, 4-5, 5-6 nm at the nominal exponents (primary, 4 cases); the same pairs in each of the 10,000 frozen draws (seed 20260907; secondary, 40,000 cases) |
| Ammonia | NH3-FINAL-1.1 harness (`provenance/discover_v1/source_harness/harness_core.py`): `cost_arrays` over the 14,136 process states, minimum over states with bed volume <= 90 m3 | the top three by intrinsic activity, all pairs: Ru-Os, Ru-Fe, Os-Fe (3 cases; Ru-Fe is the headline pair) |
| Methanol field, S5 | `data/meoh/meoh_general_model.py` as in `analysis/meoh_literature_inversion_2026_10_05` (printed cohort, recycled CO central rule, conversion capped at CO2-hydrogenation equilibrium): minimum over the canonical purge grid 0.5-40 % | 40 groups. i = cheapest of the entries with the group's maximum STY (STY ties as in `meoh_candidates.group_metrics`); j = cheapest other entry (the plant leader if it differs from i, else the plant runner-up) |
| Methanol field, S6 | same, minimum over the purge levels that are equilibrium feasible and keep the reactor-inlet non-H2/CO2 fraction <= 6.86 % | 40 groups, i and j defined as for S5 with the S6 costs |
| Re/TiO2 | D01 v3 canonical (`data/meoh/meoh_d01_model.py`: inert CO, 2 % purge, 100 bar, H2/CO2 4, STY per g Re), the Fig. 4 basis | the four Gothe 2025 Table 3 states, all 6 pairs |

Secondary set (criterion C1 only): every within-group pair (a, b) of the 40 methanol groups with STY_a > STY_b
(STY-tied pairs excluded), under S5 and under S6.

## 3. Properties (players)

A property is a player only if i and j differ in it (|difference| > 1e-12); otherwise its attribution is 0.

| System | Upstream metric U | Other properties (class) |
|---|---|---|
| Au/TiO2 | mass activity (umol CO gcat^-1 s^-1) | none in the cost model |
| Ammonia | intrinsic activity a_m = log10 TOF at the 673 K reference condition | operating window W: the state profile w_m(s) = L_m(s) - a_m of the frozen state log10 TOF (temperature/operating window); metal M: price (USD/kg) and molar mass together (metal price/loading) |
| Methanol field | STY per g catalyst | X single-pass CO2 conversion (conversion); S_CO and S_CH4, S_MeOH = 1 - S_CO - S_CH4 (selectivity CO, selectivity CH4); T reaction temperature (temperature/operating window). P and H2/CO2 are equal within a group (asserted) |
| Re/TiO2 | STY per g Re | Re loading wt% (metal price/loading); X; S_CO; S_CH4 (S_MeOH closure). T does not enter the D01 v3 cost (inert CO, fixed purge, no equilibrium cap) and is not a player |

A hybrid candidate takes the properties in coalition S from j and the rest from i. In ammonia the hybrid state
profile is L(s) = a_x + w_y(s) with x, y in {i, j} as assigned. In methanol the hybrid S_MeOH follows from the
closure; if a hybrid is invalid (S_MeOH <= 0, model error, or no eligible purge level under S6), the case is rerun
with S_CO and S_CH4 merged into one selectivity player; if still undefined, its exact and fixed-design decompositions
are reported as undefined (counted, excluded from attribution aggregates) and only C1 is scored. In ammonia a hybrid
with no state within 90 m3 takes the unconstrained minimum (counted).

## 4. Decompositions

All three use the frozen plant model and Shapley values over the players (all coalitions enumerated, n <= 5):
phi_k = sum over S not containing k of |S|!(n-|S|-1)!/n! [v(S + k) - v(S)].

- **D, exact (re-optimized):** v(S) = plant cost of hybrid S at its own optimum (state / purge re-optimized as in the
  frozen model). sum(phi) = C_j - C_i. Used for attribution, pool attribution and the figure. The sign rule applied
  to D is an identity; it is reported only as a numerical check (|sum(phi) - (C_j - C_i)| <= 1e-9 relative).
- **Fixed design (F):** v_F(S) = cost of hybrid S at i's own optimum (ammonia: i's state; methanol: i's purge level
  under the scenario, inlet limit not re-checked; Au and Re/TiO2 have no optimization, so F = D).
- **First order (L):** the manuscript's expansion, d ln J = -eps_s d ln s + sum_k eps_k d z_k, evaluated at i's own
  optimum with the operating point frozen (envelope derivative). Term of property k: t_k = eps_k * Delta z_k,
  eps_k = d ln J / d z_k by central finite differences, Delta z_k = z_k(j) - z_k(i). Coordinates z and steps:
  ln of every strictly positive scalar (mass activity, STY, metal price, molar mass, Re loading, X), step x(1 +/- 0.005);
  log10 TOF for ammonia activity and window (both act through L(s*) at i's state s*; Delta z_A = a_j - a_i,
  Delta z_W = w_j(s*) - w_i(s*)), step +/- 0.005 decade; S_CO and S_CH4 linear, step +/- 0.001 (S_MeOH compensates;
  forward difference where S < 0.001); T linear, step +/- 0.5 K. The metal term in ammonia is
  eps_price Delta ln price + eps_MW Delta ln MW.

Cost pools (exact sums of the frozen cost): ammonia, the seven terms of `cost_breakdown_at` grouped as catalyst
inventory (metal), reactor (base + vessel pressure premium), compression and refrigeration (fresh, recycle,
refrigeration, compressor capital); methanol and Re/TiO2, reactor modules (catalyst), H2 feed, CO2 feed, compression
electricity, compressor capital, loop and separation equipment (preheaters, heat exchangers, flash, distillation,
pump), purge handling (furnace and blower, turbine and generator), fixed; Au/TiO2, catalyst mass only. Pool-level
Shapley values use v_p(S) = pool p at hybrid S's own optimum.

## 5. Criteria

With U = the upstream term and O = the sum of the non-upstream terms (both in the units of the decomposition), the
operational rule for every criterion is: predict **inversion** iff U + O < 0 (with U > 0 this is "O < 0 and |O| > U");
|U + O| <= 1e-12 (relative for D and F) counts as preservation. Cases with U <= 0 are counted and listed.

- **C1 (primary, predictive):** first-order terms t_k (U = t_U > 0 by construction: i has the better upstream metric
  and the cost falls with it).
- **C2 (secondary, predictive):** fixed-design Shapley values phi_F with the same rule (inversion iff the hybrid with
  all of j's properties at i's operating point is cheaper than i).
- D with the same rule: identity check only (not scored as a test).

## 6. Scoring

- Confusion matrix (actual preserved / inverted x predicted preserved / inverted), accuracy, sensitivity (inversions
  predicted), specificity, for each system (Au nominal, Au draws, ammonia, methanol S5, methanol S6, Re/TiO2) and
  pooled. Pooled primary = Au nominal + ammonia + methanol S5 + Re/TiO2 (53 cases); pooled alternative with S6 in place
  of S5. Reference: the accuracy of always predicting preservation (majority rule).
- Methanol: paper-cluster bootstrap of accuracy, 10,000 resamples of the 28 papers with replacement, seed 20261006,
  2.5-97.5 percentiles; the same for the secondary all-pairs set.
- Regret explained, for every inverted case, R = C_i - C_j: (a) property split -phi_k / R (exact D); the carrying
  property k* = the non-upstream player with the most negative phi_k, its share -phi_k* / R and its pool split;
  (b) actual pool split of R (each candidate at its own optimum) and the share in the hypothesized pathway pools,
  fixed now: ammonia, catalyst inventory + reactor; methanol and Re/TiO2, all loop pools (H2 feed, CO2 feed,
  compression electricity, compressor capital, loop equipment, purge handling), i.e. everything except reactor
  modules; (c) C1 reproduction: R_hat = C_i (1 - exp(U + O)) against R, summed over the inverted cases of each
  system, and Spearman rho between U + O and ln(C_j / C_i) over all cases of a system.
- Attribution table: per system and outcome, phi by property class as % of C_i (mean and per case for the small
  systems). Figure: upstream attribution phi_U (x) against the non-upstream attribution sum (y), % of C_i, preserved and
  inverted cases marked separately, the inversion boundary y = -x; and the property-class split per system and outcome.

## 7. Reproduction gates (run fails otherwise)

- Au: nominal required masses equal `candidate_state` of the frozen control; adjacent pairs all preserved in the
  10,000 draws (as reported).
- Ammonia: Ru, Os, Fe costs equal `results.json` (22.03059478781101, 25.83179725613286, 15.291704676621144) within
  1e-9 USD/t; workbook SHA-256 fc259c53...dce9ba.
- Methanol: v(empty) and v(all) equal the committed `cost_recycled_opt` / `cost_recycled_opt_inlet` of
  `literature_candidates.csv` within 1e-6 EUR/t; mismatch counts 15/40 (S5) and 28/40 (S6).
- Re/TiO2: 943.30, 961.51, 966.96, 1258.17 EUR/t (2 dp).
- Shapley efficiency for D and F within 1e-9 relative; pools sum to the cost within 1e-9 relative.
