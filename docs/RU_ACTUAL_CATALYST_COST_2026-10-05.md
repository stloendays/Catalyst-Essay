# Ru at its actual catalyst cost — Fig. 2d

Date: **2026-10-05**.
Scripts and tables: `figures/composite/fig2/fig2_ru_actual_cost.py` →
`fig2_ru_alpha_sweep.csv`, `fig2_ru_actual_cost_points.csv`, `fig2_ru_bed_sensitivity.csv`;
figure `figures/composite/fig2/Fig2.{svg,pdf,png}` (panel d); caption `docs/MAIN_FIGURE_CAPTIONS.md`;
registration `docs/SOURCE_OF_TRUTH_2026-09-29.md`. The frozen ammonia process–economics model is read
only; the cached 14,136-state response surface is reused, nothing is rebuilt.

## 1. What the benchmark assumes

The ammonia process–economics model compares all 15 metals in one common formulation, that of the industrial fused-iron
catalyst. A single calibration (Fe, 65 m³ bed for 1,000 t/d at 400 °C and 80 bar) converts per-site TOF
into kilograms of active metal; the bed is 71.51 wt% metal at 2,500 kg m⁻³; spent metal is not
recovered. For Ru this means a bed of bulk Ru that uses its atoms as sparingly as fused iron uses Fe,
and that is discarded after 10 years.

## 2. Mapping a real Ru catalyst onto the price axis

In the harness the metal term is `m_active × p × (1 − r) / life / annual output`, with
`m_active ∝ 1 / (F_CAL · TOF)`. A supported catalyst that exposes *u* times more of its metal atoms
than fused iron needs `m_active / u`; recovering a fraction *r* leaves a net charge equal to the
benchmark at

    p_eff = p_Ru (1 − r) / u.

The Fig. 2d sweep (Ru reoptimized over all 14,136 states at each price) is therefore read on p_eff.

| Input | Value | Source |
|---|---|---|
| Ru price (common formulation) | 53,852.5 USD/kg | frozen model input |
| Ru dispersion of a Ba–Cs–K promoted Ru/C ammonia catalyst, 3.2 wt% Ru | 11% (O₂ chemisorption) | I. Rossetti, N. Pernicone, F. Ferrero, L. Forni, *Ind. Eng. Chem. Res.* **45**, 4150–4155 (2006), doi:10.1021/ie051398g |
| Exposed Fe atoms in reduced fused-iron catalyst | < 1% | H. Liu, X. Li *et al.*, *CIESC Journal* **51**(4), 462 (2000) |
| u | ≥ 0.11 / 0.01 = **11** (lower bound, used throughout) | — |
| Ru recovered from spent promoted Ru ammonia catalyst | > 94% | US 6,673,732 B2, Haldor Topsoe A/S (2004) |
| Recovery range used | 90–94% | 90% = lower end |
| KAAP synthesis loop | 9.1 MPa, condenser −20 °C | K. Humphreys, R. Lan, S. Tao, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021), doi:10.1002/aesr.202000043 |
| KAAP catalyst | Ru on graphite-containing carbon, Ba and Cs/K promoted; energy saving ≈ 1.17 GJ/t and lower loop CAPEX than Fe loops | Humphreys 2021; K. H. R. Rouwenhorst *et al.*, in *Techno-Economic Challenges of Green Ammonia as an Energy Vector*, Elsevier (2021), ch. 4, doi:10.1016/B978-0-12-820560-0.00004-7 |

## 3. Results

| Case | p_eff (USD/kg) | Ru cost (USD/t) | Ru − Fe | α* for parity | Ru optimum |
|---|---:|---:|---:|---:|---|
| Pure Ru, benchmark formulation | 53,852.5 | 22.031 | +6.739 | 201.2 | 450 °C, 425 bar, T_sep 25 °C, 0.066 m³ |
| Ru/C, no recovery | 4,895.7 | 17.950 | +2.658 | 18.48 | 450 °C, 220 bar, 20 °C |
| Ru/C, 90% recovery | 489.6 | 15.671 | +0.379 | 2.234 | 450 °C, 200 bar, 30 °C |
| Ru/C, 94% recovery | 293.7 | 15.485 | +0.193 | 1.494 | 450 °C, 195 bar, 30 °C |
| Parity | 163.8 | 15.292 | 0 | 1 | 425 °C, 185 bar, 30 °C |

- **Activity needed for parity** falls from 201-fold (pure Ru) to 18-fold (Ru/C) and 1.5–2.2-fold
  (Ru/C with recovery).
- **Strict-scaling reach.** The audited strict-scaling lifecycle boundary
  (`analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`) places
  scaling-consistent parity at p_eff ≤ 237.3 USD/kg (10-y basis). Because the metal charge scales with
  p (1 − r) / (u L), the same boundary applies here: Ru/C reaches it at u ≥ 13.6 with 94% recovery or
  u ≥ 22.7 with 90%. At the literature bound u = 11 the Ru/C points (294–490 USD/kg) lie just outside.
- **Parity in u.** With the benchmark bed, Ru matches Fe at u = 19.7 (94% recovery) or u = 32.9 (90%).
  The literature bound u ≥ 11 places supported, recovered Ru 0.19–0.38 USD/t above Fe.
- **KAAP loop** (90 bar, T_sep −20 °C, T reoptimized):

| Catalyst in the KAAP loop | Cost (USD/t) |
|---|---:|
| Ru/C, 94% recovery | 18.529 (400 °C) |
| Ru/C, 90% recovery | 18.910 (425 °C) |
| Fused iron | 19.069 (425 °C, 21.6 m³) |
| Pure Ru, benchmark formulation | 38.972 |

  At the KAAP condition the supported, recovered Ru catalyst is 0.16–0.54 USD/t cheaper than iron.
  The model's global optimum remains the 180-bar Fe loop (15.29); a catalyst-free 90-bar loop costs
  at least 16.70 USD/t in this model.
- **Bed formulation.** The supported bed holds 3.2 wt% Ru instead of 71.5 wt% metal. Recomputing the
  reactor term with that bed at 500–1,000 kg m⁻³ (5–10 times the benchmark volume) adds 0.15–0.83 USD/t
  to the Ru/C points (`fig2_ru_bed_sensitivity.csv`); the metal term is unchanged.

## 4. Reconciliation with industrial practice (Fe optimum)

| Quantity | Model, Fe optimum | Industrial reference | Source |
|---|---|---|---|
| Fresh syngas pressure | 30 bar | ≈ 30 bar (SMR section) | Rouwenhorst 2021 |
| Loop pressure | 180 bar | 100–300 bar (Fe loops); Topsøe ≈ 250 bar; KAAP 91 bar | Rouwenhorst 2021; Humphreys 2021 |
| Converter temperature | 425 °C (isothermal state) | inlet 300–350 °C, outlet 450–500 °C; 340–525 °C | Rouwenhorst 2021; US 4,482,523 (Kellogg, 1984) |
| Separator temperature | 30 °C | −20 to 30 °C; Topsøe 0 to −10 °C; KAAP −20 °C | Rouwenhorst 2021; Humphreys 2021 |
| NH₃ in recycle gas | 6.4 mol% | 2–5 mol% | Rouwenhorst 2021 |
| Catalyst volume, 1,000 t/d | 17.1 m³ | 40–90 m³ | US 4,482,523 |
| Recycle compression | 15.3 kWh/t | 17.5 kWh/t (30 MPa) – 21.5 kWh/t (10 MPa), 330 t/d ZA-5 loop | Humphreys 2021, citing H. Liu (2013) |
| Refrigeration | 0 kWh/t | 13.4 kWh/t (30 MPa) – 22.6 kWh/t (10 MPa), same loop | Humphreys 2021 |
| Fresh-feed compression, 30 → 180 bar | 193 kWh/t | isothermal minimum 152 kWh/t at 40 °C; 203 kWh/t at η = 0.75 | thermodynamic check |
| Catalyst/process-dependent cost | 15.29 USD/t | total gas-based NH₃ cost ≥ 160 USD/t (state of the art), 200–300 USD/t market price before 2021; natural gas > 50% of cost | IEAGHG 2023-IP03 |

This table adds numbers to `analysis/nonfigure_upgrades_2026_09_29/MODEL_VALIDATION_MATRIX.md` and
`EXTERNAL_VALIDATION_AND_BENCHMARK_2026-09-30.md`. The model loop sits inside the industrial pressure and
temperature windows. The separator runs at the
warm end of the industrial range, with correspondingly more NH₃ in the recycle and no refrigeration
duty, and the Fe bed is smaller than industrial converters of the same capacity. The 6.74 USD/t Ru–Fe
gap is 2–4% of a 160–300 USD/t ammonia cost.

## 5. Draft Results paragraph (for the next manuscript pass)

> The common formulation gives Ru that of the industrial fused-iron catalyst. Placing a real Ru
> catalyst on the same price axis shows where industrial practice sits. A promoted Ru/C catalyst
> exposes at least 11 times more of its metal than fused iron (11% Ru dispersion against fewer than 1%
> of Fe atoms exposed), and more than 94% of the Ru is recovered from spent catalyst. Together these
> lower the effective Ru price from 53,853 to 294–490 US dollars per kilogram and the optimized Ru cost
> from 22.03 to 15.49–15.67 US dollars per tonne of NH3, within 0.19–0.38 of Fe (Fig. 2d). The activity
> Ru needs for parity falls from 201-fold to 1.5–2.2-fold, and a scaling-consistent Ru descriptor
> reaches Fe once the effective price falls below 237 US dollars per kilogram. In a KAAP-type loop at 90 bar with a −20 °C separator, the same supported and recovered
> catalyst undercuts fused iron, 18.53–18.91 against 19.07 US dollars per tonne. The route that closes
> the Ru–Fe gap is metal economy — dispersion and recovery — rather than intrinsic activity, which is the
> route industry took with the Kellogg Advanced Ammonia Process.
