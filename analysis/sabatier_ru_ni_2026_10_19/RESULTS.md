# Results — CO₂ methanation (Sabatier) Ru vs Ni: an external rank-preservation / decision-boundary case

Branch `analysis/sabatier-ru-ni-2026-10-19`. Pre-registration: `PREREGISTRATION.md` (committed before any computation).
Model: `sabatier_model.py`; driver: `run_model.py`; sources: `SOURCE_LEDGER.csv`; frozen outputs: `results/`,
`FROZEN_HASHES.json`. Seed 20261019, 10,000 Monte Carlo draws. All costs are catalyst-dependent USD per MWh of SNG (LHV).

## Headline

| Claim | Evidence | File |
|---|---|---|
| At small scale the intrinsic Ru > Ni ranking is preserved economically despite the Ru price penalty (H1 supported) | 0.1 MW, central parameters: Ru 19.69 vs Ni 42.41 USD MWh⁻¹; Monte Carlo P(Ru < Ni) = **0.983** at 0.1 MW, 0.832 at 0.3 MW | `results/central_sweep.csv`, `results/mc_summary.csv` |
| The ranking inverts to Ni > Ru at larger scale; a boundary exists inside 0.1–100 MW (H2 supported) | Central parity scale **S\* = 0.595 MW**; 100 MW: Ru 8.47 vs Ni 3.24 USD MWh⁻¹; P(Ru < Ni) = 0.029 at 10 MW, **0.0005** at 100 MW | `results/summary.json`, `results/mc_summary.csv` |
| The boundary is a leverage inequality r_V (1 + φ_proc(S)) ≷ Π (H3 supported) | Parity solved on the full model and on the decomposed inequality agree to max log₁₀ difference **0.0** over 382 boundary points | `results/boundary_curve.csv` (`log10_diff`), `results/leverage_decomposition.csv` |
| The price channel is active and *loses* at small scale — but not to activity alone | Π = 5.18 (Ru catalyst 5.2× more expensive per kg) against r_V = 1.89: the inventory term alone favours Ni at **every** scale (A_Ni/A_Ru = 0.365). Ru wins only because the Ni topology penalty φ_proc is 9.13 at 0.1 MW and falls to 0.038 at 100 MW | `results/leverage_decomposition.csv` |
| Boundary moves towards Ni with Ru price and shorter catalyst life | Life 5 y: S\* = 0.854 MW at 0.1× Ru price, 0.595 at 1×, 0.142 at 10×; life 10 y: 0.30–1.91 MW; life 1 y: 0.10–0.15 MW, Ni everywhere above 1.26× Ru price | `results/boundary_curve.csv` |
| Monte Carlo parity scale | Median S\* = **0.86 MW**, 5–95 % interval 0.18–7.0 MW; 170/10,000 draws Ni cheaper at every scale, 5/10,000 Ru cheaper at every scale | `results/mc_draws.csv`, `results/summary.json` |
| Source reproduction | Source Table 6 relative bed cost 5.20 (metal) / 2.64 (commercial) reproduced to ±0.02 from the ledger values; precursor basis prints 2.46 while the printed inputs give 2.31 (source-internal rounding) | `test_sabatier_model.py` |
| Agreement with Moioli & Züttel's qualitative conclusion | Reproduced: Ru/Al₂O₃ is the least-cost catalyst at small scale; a Ni system with condensation becomes cheaper at larger scale. The source does not define the scale in kW/MW; this model places the central boundary at ~0.6 MW SNG (≈ 75 Nm³ h⁻¹ CH₄) | this file |

Monte Carlo P(Ru cheaper than Ni) by scale (10,000 draws):

| MW SNG | 0.1 | 0.3 | 1 | 3 | 10 | 30 | 100 |
|---|---|---|---|---|---|---|---|
| P(Ru < Ni) | 0.983 | 0.832 | 0.441 | 0.157 | 0.029 | 0.005 | 0.0005 |
| median ΔC (Ru − Ni), USD MWh⁻¹ | −25.1 | −5.95 | +0.58 | +2.77 | +3.64 | +3.95 | +4.08 |

## Scale-dependence mechanism

Catalyst inventory scales linearly with throughput (A ∝ S), reactor-stage capital scales as S^0.52 plus a fixed term,
so the Ni topology penalty φ_proc = (R_Ni − R_Ru)/A_Ni, expressed per unit of Ni catalyst cost, falls as roughly S^−1
at small scale. The decision at any scale is

    Ru cheaper  ⇔  r_V · (1 + φ_proc(S)) > Π,   Π = p_cat,Ru / p_cat,Ni = 5.18 (central, precursor basis)

| S (MW) | r_V | Π | φ_proc | r_V(1+φ) | margin | winner |
|---|---|---|---|---|---|---|
| 0.1 | 1.89 | 5.18 | 9.13 | 19.1 | +14.0 | Ru |
| 0.316 | 1.89 | 5.18 | 3.10 | 7.74 | +2.56 | Ru |
| 0.595 | 1.89 | 5.18 | 1.74 | 5.18 | 0 | parity |
| 1 | 1.89 | 5.18 | 1.10 | 3.97 | −1.21 | Ni |
| 10 | 1.89 | 5.18 | 0.17 | 2.21 | −2.97 | Ni |
| 100 | 1.89 | 5.18 | 0.038 | 1.96 | −3.22 | Ni |

This is the same inequality the ammonia case evaluates at 1,000 t d⁻¹, where φ_proc is absent (both metals use one
converter) and the inversion is decided by r_V against Π alone. In methanation r_V (1.89) is far below Π (5.18), so,
exactly as in ammonia, activity alone does not pay for Ru; Ru keeps its rank only where the cheap metal forces a more
complex process and that complexity has a fixed-cost component. The case therefore belongs with ammonia as a
*price-channel-active* comparison, with the opposite outcome at small scale and an explicit scale boundary.

## Scenario table (deterministic; `results/scenarios.csv`)

| Scenario | S\* (MW) | 0.1 MW winner | 100 MW winner |
|---|---|---|---|
| central (precursor basis, 5 y, κ = 1.5, frozen prices) | 0.595 | Ru | Ni |
| metal-only cost basis | 2.47 | Ru | Ni |
| commercial-catalyst basis | 0.211 | Ru | Ni |
| source 2019 Ru price (8,233 € kg⁻¹ = 0.171× frozen) | 0.826 | Ru | Ni |
| source 2019 Ru price, metal-only basis | 37.6 | Ru | Ni |
| Ru recovery 0.9 | 0.854 | Ru | Ni |
| life 2 y / 10 y | 0.219 / 1.31 | Ru | Ni |
| κ 0.5 / 3 | 0.339 / 1.01 | Ru | Ni |
| r_V 1.5 / 2.5 | 0.508 / 0.791 | Ru | Ni |
| r_V from isothermal kinetics, k_ref 3.46e-4 / 3.46e-5 (0.28 / 2.77) | 0.327 / 0.915 | Ru | Ni |
| GHSV 1500 / 6000 h⁻¹ | 0.298 / 1.19 | Ru | Ni |
| Ru price ×0.1 / ×10 | 0.854 / 0.142 | Ru | Ni |

Every deterministic scenario gives Ru at 0.1 MW and Ni at 100 MW; the boundary moves over 0.14–37.6 MW. The only
scenario pushing the boundary into the tens of MW is the source's own 2019 Ru price combined with a metal-only
catalyst cost basis, i.e. the lower bound on Π.

## Kinetic cross-check (`results/kinetic_crosscheck.csv`)

The tabulated rate laws (Ru power law, Falbo et al. 2018; Ni LHHW, Koschany et al. 2016) were integrated in an isothermal
plug-flow bed at 250–400 °C, 1–10 bar, 70–90 % conversion. The result depends on a documented source ambiguity: Moioli &
Züttel's Table 3 prints the Koschany rate constant as 3.46 × 10⁻⁵ while two independent SI tabulations print
3.46 × 10⁻⁴ mol bar⁻¹ s⁻¹ g⁻¹ (original paper not accessible from this session). With 3.46 × 10⁻⁵ the isothermal
V_Ni/V_Ru at 300 °C, 10 bar, 90 % is **2.77**, consistent in direction and magnitude with the source's non-isothermal
3.11; with 3.46 × 10⁻⁴ it is 0.28 (Ni more active per gram), which contradicts the source's light-off ordering. The
cross-check therefore supports the Table 3 value as printed, but the model does **not** use either integration: r_V is
taken from the source's own reactor simulation (1.89 at 99.5 % with condensation) and bracketed 1.5–2.5. Both
isothermal values are carried as scenarios; neither changes the small-scale or large-scale winner.

## What is modelled and what is not

Modelled (catalyst-dependent terms only): catalyst inventory from GHSV and the source's volume ratio; catalyst
replacement at the frozen repository metal prices with the source's three manufacturing bases; reactor-stage capital
with the frozen repository vessel correlation and financing; the Ni intermediate-condensation stage as a second vessel
plus a bracketed condenser/reheater set.

Not modelled (declared limitations; this is a literature-level case, not a TEA): hydrogen and CO₂ feed cost, feed and
recycle compression, heat-integration and steam-credit differences between a 1-stage and a 2-stage train, the lower Ru
light-off (which the source converts into simpler heat management but does not cost), the lower hotspot of Ni
(≈ 50 °C), catalyst deactivation differences, any gas-cleanup or grid-injection cost, and the hybrid Ni-then-Ru bed the
source proposes (volume ratio 1.38). Cost absolutes should not be compared with full SNG production costs; only the
Ru–Ni difference and its sign are interpreted.

Parameters bracketed rather than sourced: catalyst life (2–10 y), Ru recovery (0–0.9), condensation-set multiplier κ
(0.5–3), design GHSV at 99.5 % (1500–6000 h⁻¹), EUR→USD (1.12 fixed), CAPEX multiplier (0.8–1.2). The source
explicitly states that the capital cost of the condensation step was not quantified; κ is the only free structural
parameter and the boundary moves from 0.34 to 1.01 MW across its bracket.

## Reproduction

    python analysis/sabatier_ru_ni_2026_10_19/run_model.py --check     # reruns everything, asserts FROZEN_HASHES.json
    python -m unittest discover -s analysis/sabatier_ru_ni_2026_10_19 -p 'test_*.py'

Runtime ≈ 4 s (numpy 2.x, pandas 3.x). CI: `.github/workflows/sabatier-ru-ni-boundary.yml`.
