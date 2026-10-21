# Pre-registration — CO₂ methanation (Sabatier) Ru vs Ni as an external rank-preservation / decision-boundary case

Registered: 2026-10-19, before any model code was written or run. Branch `analysis/sabatier-ru-ni-2026-10-19`.

## Purpose

The manuscript has three in-house cases: ammonia (atomic → industrial optimum, ranking inverts because the
metal held in the bed costs more than its activity saves), CO₂-to-methanol (laboratory → industrial optimum,
selectivity-dependent purge and recycle invert the ranking) and Au/TiO₂ CO oxidation (laboratory optimum →
catalyst requirement, ranking preserved because no downstream channel is opened). This work package adds a
fourth, external, literature-level case with the same decision structure as ammonia — an expensive high-activity
metal (Ru) against a cheap lower-activity metal (Ni) — in which an independent group (Moioli & Züttel, 2020)
concluded the opposite outcome at small scale: **the intrinsic Ru > Ni ranking is preserved economically for
small-scale SNG, while an efficient Ni system is suited to large scale.** Because the primary source reached its
conclusion with its own reactor model, the case is non-circular with respect to the paper's own harness.

Primary source: E. Moioli, A. Züttel, *Sustainable Energy Fuels* 2020, **4**, 1396–1408, DOI 10.1039/C9SE00787C
(open-access author manuscript, Politecnico di Milano repository handle 11311/1272322). Every number used is
recorded with DOI and location in `SOURCE_LEDGER.csv`.

## Hypotheses (fixed before computation)

- **H1 (small-scale rank preservation).** At small plant scale, within the documented parameter brackets, the
  catalyst-dependent cost of SNG with 0.5 wt% Ru/Al₂O₃ is lower than with Ni/Al₂O₃ plus an intermediate
  water-condensation stage, i.e. the intrinsic ranking Ru > Ni is preserved despite the Ru price penalty, because the
  Ni process-topology penalty (one extra reactive stage with condensation and reheating) has a fixed-cost component
  that does not shrink with scale as fast as catalyst inventory does.
- **H2 (existence of a boundary).** There exists a plant scale S* (MW SNG, LHV) and a Ru metal price p* at which
  the ranking inverts to Ni > Ru. For the central parameter set, S* lies inside the swept range 0.1–100 MW.
- **H3 (leverage inequality locates the boundary).** The inversion is located by the leverage inequality
  r_V · (1 + φ_proc(S)) ≷ Π, where r_V = V_Ni/V_Ru is the inventory advantage of Ru from intrinsic activity, Π is the
  per-kilogram-of-catalyst price penalty ratio (metal loading × metal price × manufacturing basis, net of recovery),
  and φ_proc(S) is the Ni process-complexity penalty expressed as a fraction of the Ni catalyst annual cost at scale S.
  The boundary curve S*(p_Ru, L) obtained from the full model must coincide (to numerical tolerance) with the root of this
  inequality computed from the decomposed terms.

Secondary, descriptive expectation (not a pass/fail criterion): the direction of the scale dependence is monotone —
larger scale, higher Ru price and shorter catalyst life each move the boundary towards Ni.

## Pre-specified model

Deterministic Python, no fitting to the source conclusion. Cost chain follows the repository convention
(`provenance/discover_v1/source_harness/harness_core.py::cost_arrays`): activity → catalyst inventory → reactor
capital → metal / catalyst replacement; plus a process-topology term that the ammonia harness does not need.

1. **Plant scale**: SNG output S in MW (LHV, CH₄ 802.3 kJ mol⁻¹), sweep 0.1–100 MW, log grid.
2. **Feed**: stoichiometric CO₂:H₂ = 1:4, undiluted, 10 bar, target CO₂ conversion 99.5% (Moioli & Züttel, Table 5 /
   Section 3.3). Inlet volumetric flow at STP = 5 mol gas per mol CO₂ fed.
3. **Inventory**: V_Ru = Q_STP / GHSV with GHSV = 3000 h⁻¹ (source reference condition); V_Ni = r_V · V_Ru with r_V the
   source-reported volume ratio for 99.5% yield with an intermediate condensation step (1.89). The kinetic rate laws
   (Ru power law from Falbo et al. 2018 as tabulated by the source; Ni/Al₂O₃ LHHW from Koschany et al. 2016) are
   integrated in an isothermal plug-flow cross-check to test whether they reproduce the source's volume ratio
   direction; the cross-check is reported but does not replace r_V.
4. **Catalyst mass**: m = V · ρ_bulk, ρ_bulk = 1500 kg m⁻³ (source Table 5). Metal inventory = m · w, w = 0.5 wt% Ru,
   35 wt% Ni (source Table 6).
5. **Catalyst price per kg**: p_cat = w · p_metal · (1 − recovery) + a_basis, where p_metal are the repository's
   frozen metal prices (`PRICE['Ru']` = 53,852.5 USD kg⁻¹, `PRICE['Ni']` = 16.909 USD kg⁻¹) and a_basis is the
   non-metal manufacturing cost per kg catalyst implied by the source's three cost bases (metal-only, precursor,
   commercial catalyst; Table 6, 2019 € converted at a fixed 1.12 USD/€). Central: precursor basis. Annual
   replacement = m · p_cat / L, catalyst life L (years), central 5 y (bracketed, not sourced).
6. **Reactor capital**: per reactive stage, C_fixed + C_var (V_stage / V_ref)^0.52 with the repository's frozen
   reactor correlation (66,800 USD; 268,000 USD; 20 m³; 0.52), annualized with the repository CRF (12%, 25 y).
   Ru: one stage. Ni: two stages (volume split equally) plus an inter-stage condensation set (condenser, water
   knock-out, reheater) costed as κ × C_stage(V_Ni/2) with κ bracketed (0.5–3, central 1.5) because the source
   explicitly did not quantify it.
7. **Objective**: catalyst-dependent cost in USD per MWh SNG = (catalyst replacement + reactor and stage capital) /
   annual SNG output (capacity factor 0.95 as in the ammonia harness). Feed hydrogen, CO₂, compression, heat
   integration and heat-recovery credit are identical or unmodelled for both catalysts and are excluded; this is
   declared as a limitation.

Sweeps: scale 0.1–100 MW (61 log points), Ru price multiplier 0.1–10 (41 log points), catalyst life 1–10 y
(10 points). Outputs: cost of each catalyst, ranking, boundary curve (parity scale as a function of Ru price and
life, by bisection in log S), and the leverage decomposition r_V, Π, φ_proc at every grid point.

## Monte Carlo (fixed before computation)

10,000 draws, `numpy.random.default_rng(20261019)`, evaluated at scales 0.1, 0.3, 1, 3, 10, 30, 100 MW.

| Parameter | Distribution | Basis |
|---|---|---|
| r_V (V_Ni / V_Ru at 99.5%) | uniform 1.5–2.5 | source reports 1.89 (99.5%) and 2.0 (99%); bracket covers both |
| GHSV (h⁻¹) | log-uniform 1500–6000 | source uses 3000; bracketed |
| ρ_bulk (kg m⁻³) | uniform 1200–1800 | source 1500 ± 20% |
| Ru price multiplier | log-uniform 0.5–2 | ammonia Monte Carlo convention |
| Ni price multiplier | log-uniform 0.5–2 | ammonia Monte Carlo convention |
| Catalyst life L (y), common | uniform 2–10 | not sourced; bracketed |
| Ru recovery fraction | uniform 0–0.9 | not sourced for methanation; 0 (frozen harness) to below the 95.55% ammonia value |
| Manufacturing basis u | uniform 0–1 (0 = metal only, 0.5 = precursor, 1 = commercial), shared by Ru and Ni | source Table 6 |
| κ (extra-stage multiplier) | uniform 0.5–3 | not sourced; bracketed |
| CAPEX multiplier | uniform 0.8–1.2 | ammonia Monte Carlo convention |

Reported: P(Ru cheaper than Ni) at each scale; median and 5–95% interval of the cost difference.

## Acceptance criteria

- H1 is supported if, at the central parameter set, Ru is cheaper at 0.1 MW **and** P(Ru < Ni) at 0.1 MW ≥ 0.5 in the
  Monte Carlo. It is refuted otherwise and the refutation is reported as the result.
- H2 is supported if the central-parameter parity scale S* exists in 0.1–100 MW. If Ru wins (or loses) at every scale
  in the range, H2 is refuted for the central set and the boundary is reported as outside the range.
- H3 is supported if |log₁₀ S*(full model) − log₁₀ S*(leverage inequality)| < 10⁻⁶ at every (p_Ru, L) point where
  both exist (they are the same equation written two ways; the test guards the decomposition's bookkeeping).
- No parameter is tuned after seeing results. If the model does not reproduce the source's qualitative conclusion
  (Ru wins at small scale), that is the reported result.

## Fixed numerics

Seed 20261019; bisection to 1e-10 in log₁₀ S; all CSV outputs written with 10 significant digits; SHA-256 of every
result file frozen in `FROZEN_HASHES.json`; CI reruns the model and asserts the headline numbers in `RESULTS.md`.
