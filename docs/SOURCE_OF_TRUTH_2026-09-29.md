# Manuscript source of truth — 2026-09-29

This page is the publication-facing **single truth hierarchy** for the current manuscript. It distinguishes frozen canonical results, audited derived extensions and calculations that are prepared but not yet promoted.

## Rule

A number may enter the main manuscript only when it is either:

1. **CANONICAL** — frozen in the provenance-closed scientific source; or
2. **DERIVED-A** — deterministically derived from canonical sources with a committed reproducible audit.

A prepared calculation with no completed output is **PENDING** and must not be written as a scientific conclusion.

## NH3 — canonical FINAL-1.1

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| atomic top-3 | Ru > Os > Fe | CANONICAL | FINAL-1.1 results |
| economic top-3 | Fe > Ru > Os | CANONICAL | FINAL-1.1 results |
| Fe / Ru / Os cost | 15.292 / 22.031 / 25.832 USD/t NH3 | CANONICAL | FINAL-1.1 results |
| Top-3 Spearman / Kendall | -0.50 / -0.33 | CANONICAL | rolling rank closure |
| full-15 raw Spearman | 0.929 | CANONICAL | rolling rank closure |
| Fe feasibility | 79.9% | CANONICAL | descriptor MC |
| Fe economic Top-1 | 68.1% (681/1000) | DERIVED-A | frozen descriptor-MC draws |
| atomic-to-economic Top-1 survival | 28.2% | CANONICAL | descriptor MC |
| Top-3 actionable | 94.0% | CANONICAL | descriptor MC |
| Ru activity-only parity | 201.22x | CANONICAL | backward sweep |
| scaling gain at 673 K | 1.090x | CANONICAL | scaling reachability |
| maximum state-specific scaling gain | 2.525x | CANONICAL | scaling reachability |
| strict-scaling minimum Ru cost | 21.398 USD/t at E_N = -1.215 eV | CANONICAL | scaling reachability |

**Semantic lock:** 68.1% is the probability that Fe is the economic Top-1 in the frozen descriptor draws. **28.2% is a different metric**: the probability that the atomistic Top-1 identity survives into the economic Top-1.

## NH3 — audited derived extensions

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| Ru at Fe metal price | 14.712 USD/t | DERIVED-A | 2026-09-20 equal-price audit |
| Ru-Fe parity metal price | 163.76 USD/kg Ru | DERIVED-A | full Ru price sweep |
| joint cost MC P(C_Fe < C_Ru) | 1.000 (5000/5000) | DERIVED-A | preregistered cost MC |
| alpha* p05 / median / p95 | 70.78x / 174.27x / 462.00x | DERIVED-A | cost MC |
| direct target: 10 y + 99% recovery | alpha_req <= 2.41794x | DERIVED-A | 53-state target audit |
| direct target: 15 y + 99% recovery | alpha_req <= 1.74213x | DERIVED-A | 53-state target audit |
| direct target: 20 y + 99% recovery | alpha_req <= 1.40129x | DERIVED-A | 53-state target audit |
| direct target: 20 y + 98% recovery | alpha_req <= 2.41794x | DERIVED-A | 53-state target audit |

The direct activity/lifecycle values are **backward targets**, not physical-reachability results. The 53-state restriction makes them conservative upper bounds on the activity multiplier required for parity.

## NH3 — actual-catalyst cost of Ru (Fig. 2d) — 2026-10-05

A supported catalyst that exposes *u* times more metal than fused iron and recovers a fraction *r* carries the metal
charge of the common formulation at p_eff = p (1 − r) / u. Literature inputs: Ru dispersion 11% for a promoted Ru/C
ammonia catalyst with 3.2 wt% Ru (Rossetti *et al.*, *Ind. Eng. Chem. Res.* 2006) against fewer than 1% of Fe atoms
exposed in reduced fused iron (Liu *et al.*, *CIESC J.* 2000), so u ≥ 11; Ru recovery from spent promoted Ru catalyst
above 94% (US 6,673,732 B2); KAAP loop 9.1 MPa with a −20 °C condenser (Humphreys *et al.*, *Adv. Energy Sustain. Res.* 2021).

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| Ru/C, no recovery (u = 11) | 17.950 USD/t; alpha* 18.48x | DERIVED-A | `figures/composite/fig2/fig2_ru_actual_cost_points.csv` |
| Ru/C, 90% recovery | 15.671 USD/t (+0.379 vs Fe); alpha* 2.234x; 450 C / 200 bar | DERIVED-A | same |
| Ru/C, 94% recovery | 15.485 USD/t (+0.193 vs Fe); alpha* 1.494x; 450 C / 195 bar | DERIVED-A | same |
| KAAP loop (90 bar, Tsep -20 C): Ru/C 94% / 90% recovery vs fused Fe | 18.529 / 18.910 vs 19.069 USD/t | DERIVED-A | same |
| u required for parity at 94% / 90% recovery | 19.7 / 32.9 | DERIVED-A | same |
| u required for strict-scaling reach (p_eff <= 237.3 USD/kg) at 94% / 90% | 13.6 / 22.7 | DERIVED-A | same + strict-scaling lifecycle audit |
| supported-bed reactor-term sensitivity (bed 5-10x benchmark volume) | +0.15 to +0.83 USD/t | SUPPORTING | `fig2_ru_bed_sensitivity.csv` |

**Semantic lock:** u = 11 is a literature lower bound (Fe exposure is bounded above by 1%), not a fitted value. The Ru/C
points use the common bed formulation for the reactor term; the supported-bed reactor correction is reported as a
sensitivity. The KAAP comparison holds the loop at 90 bar and -20 C for both catalysts; the global optimum of the model
remains the 180-bar Fe loop.

Reproduction: `figures/composite/fig2/fig2_ru_actual_cost.py` (asserts the canonical Fe and Ru costs, the 201.22x
alpha* and the strict-scaling Fe reference before writing). Note: `docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md`.

## NH3 — strict-scaling lifecycle reachability closure

The joint backward target has now been tested against the **strict E_N scaling manifold** with all **14,136 FINAL-1.1 process states** and no new DFT.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| canonical strict-scaling anchor | 21.397873 USD/t at E_N = -1.215 eV | CANONICAL | FINAL-1.1 scaling reachability |
| critical lifecycle factor q* = (1-r)/L | 4.40683454e-4 y^-1 | DERIVED-A | strict-scaling lifecycle audit |
| equivalent Ru parity price on 10-y basis | 237.319 USD/kg | DERIVED-A | strict-scaling lifecycle audit |
| strict-scaling parity descriptor/state | E_N = -1.230 eV; 425 C / 190 bar / 30 C; 4.298 m3 | DERIVED-A | strict-scaling lifecycle audit |
| best point inside L<=20 y, r<=0.99 | 20 y + 99%; 15.36249 USD/t | DERIVED-A | strict-scaling lifecycle audit |
| miss versus Fe at tested-box corner | +0.07078 USD/t (+0.46%) | DERIVED-A | strict-scaling lifecycle audit |
| required recovery at 20 y | 99.1186% | DERIVED-A | strict-scaling lifecycle audit |
| required lifetime at 99% recovery | 22.69 y | DERIVED-A | strict-scaling lifecycle audit |

**Decision:** the prespecified lifecycle box (**life <= 20 y; recovery <= 0.99**) does **not** intersect the strict scaling manifold, although the boundary lies just outside it.

**Semantic lock:** the **2.525x** all-state scaling gain remains a state-specific activity diagnostic. It is not used as a uniform activity multiplier in the joint reachability result.

Authoritative derived files:

- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_keypoints.csv`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_global_boundary.csv`
- `analysis/fe_bridge_backward_2026_09_29/run_statewise_strict_scaling_lifecycle.py`

## First NH3 inversion layer

The layer-wise causal audit now has a common-reference diagnostic plus an independent full-process intervention:

```text
673 K intrinsic activity                      Ru > Os > Fe
same-reference active-metal demand            Ru < Os < Fe   (lower burden is better)
canonical price + 10-y replacement economics Fe < Ru < Os   <-- FIRST FLIP
full process, Ru priced as Fe                 Ru remains below Fe in cost
full canonical optimization                   Fe < Ru < Os   <-- flip amplified
```

At the common atomistic reference, the normalized active-metal demands are **2,161.5 kg Ru / 4,503.5 kg Os / 86,279 kg Fe**. Annualizing only the metal replacement term at canonical prices changes these to **0.199 / 33.570 / 185.270 USD/t NH3 for Fe / Ru / Os**, before reactor, compression, refrigeration or equipment costs are added.

The publication interpretation is therefore: **the first ranking inversion occurs at the catalyst-demand-to-lifecycle-economics interface; candidate-specific process reoptimization subsequently amplifies the cost difference.** The equal-price full-process ablation independently confirms that process optimization alone is insufficient to make Fe beat Ru.

## Non-figure derived diagnostics — 2026-09-29

These values strengthen interpretation without modifying the frozen reaction models.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| NH3 normalized upstream-selection regret | 44.0689% | DERIVED-A | `analysis/nonfigure_upgrades_2026_09_29/decision_regret_summary.csv` |
| NH3 regret p05 / median / p95 under preregistered cost MC | 30.48% / 40.89% / 54.25% | DERIVED-A | `analysis/nonfigure_upgrades_2026_09_29/nh3_cost_mc_regret_summary.json` |
| NH3 P(regret > 0) under cost MC | 1.000 (5000/5000) | DERIVED-A | same |
| MeOH normalized upstream-selection regret | 3.3595% | DERIVED-A | same |
| Au/TiO2 selection regret | 0 | DERIVED-A | same |
| pairwise transfer index, NH3 Ru vs Fe | +0.08531 | DERIVED-A | `pairwise_inversion_index.csv` |
| pairwise transfer index, MeOH STY winner vs NPC winner | +0.02573 | DERIVED-A | same |
| pairwise transfer index, Au/TiO2 2 nm vs 6 nm | -1.0000 | DERIVED-A | same |
| Fe atomistic Top-1, matched independent copula audit | 10.71% | SUPPORTING | `descriptor_correlation_sensitivity.csv` |
| Fe atomistic Top-1, latent rho=0.9 | 21.68% | SUPPORTING | same |
| common descriptor-shift interval preserving Ru > Os > Fe | approximately -0.0573 to +0.1030 eV | SUPPORTING | `common_mode_descriptor_shift.json` |
| non-binding Agent runs with post-stability compute | 14/20 | DERIVED-A diagnostic | `agent_stopping_efficiency.json` |
| total CU after hindsight stability | 8207/17535 = 46.8% | DERIVED-A diagnostic | same |

**Semantic locks:**

- Decision regret is normalized **within each system**; it does not make absolute NH3 and MeOH objectives comparable.
- The NH3 cost-MC regret distribution is calculated from an exact reconstruction of the preregistered draw sequence; its regenerated Fe/Ru cost summary matches the previously promoted 2026-09-20 summary to machine precision.
- The copula/common-bias calculations are **uncertainty-model sensitivities**, not replacements for the preregistered descriptor or cost Monte Carlo.
- The Agent 46.8% value uses hindsight decision stability and is **not an online saving estimate**.
- The NH3 values of 15–26 USD/t are a **reduced catalyst-dependent cost objective**, not total levelized ammonia production cost.

Model validation and scope are recorded in `analysis/nonfigure_upgrades_2026_09_29/MODEL_VALIDATION_MATRIX.md`.
External process/economic comparison is recorded in `analysis/nonfigure_upgrades_2026_09_29/EXTERNAL_VALIDATION_AND_BENCHMARK_2026-09-30.md`. The reader-facing interpretation is locked as follows: **external literature supports the Fe operating window and catalyst–process coupling structure, but it does not validate the model-specific pure-Ru optimum or the absolute reduced-cost values. Published Fe/Ru studies themselves show that the preferred catalyst changes with plant scale, pressure and loop configuration.**

## Independent process/economic validation — 2026-09-30

External ammonia-process literature now provides mechanism-level support for the process/economic interpretation.

- Yoshida, Ogawa & Ishihara (2024) independently report that higher-activity Ru catalysts can reduce reactant-gas pressurization cost while ammonia-separation refrigeration, expensive Ru and catalyst lifetime can offset the benefit.
- Recent low- vs high-pressure Haber-Bosch TEA confirms that loop pressure changes energy and economics.
- Recent Ru-catalyst reviews identify Ru price, loading, lifetime and recycling as practical deployment constraints.

**Semantic lock:** these studies support the **qualitative multiscale mechanism**. They do **not** numerically validate the present Fe/Ru costs, reproduce the Fe > Ru result, or justify treating the pure-metal Ru optimum as a commercial promoted-Ru operating point.

Authoritative note: `analysis/nonfigure_upgrades_2026_09_29/EXTERNAL_PROCESS_ECONOMIC_VALIDATION.md`.

## Other active scientific families

- **Methanol recycle-economics model:** MEOH-D01-v3.
- **Au/TiO2 rank-preservation control:** V1.1, with V1.3 as supporting semi-open robustness.
- **Adaptive Catalyst Screening Agent:** DISCOVER V1 + DISCOVER-BOUNDARY-C1.

Their current manuscript-facing values remain in `data/manuscript_headline_results_2026-09-20.csv` and `docs/RESULTS_AT_A_GLANCE.md`.

## Machine gates

- backward direct-target reproducibility: GitHub Actions run **36516398387 — PASS**
- strict-scaling lifecycle result gate: GitHub Actions run **36527291341 — PASS**
- exact NH3 5,000-draw cost-MC reconstruction: GitHub Actions run **36553584460 — PASS**
- section-aware live manuscript truth audit with regret distribution: GitHub Actions run **36553822171 — PASS**
- non-figure scientific upgrade audit: the active workflow reruns on every change under `analysis/nonfigure_upgrades_2026_09_29/`.

Active automated gates:

- `analysis/nonfigure_upgrades_2026_09_29/reproduce_nh3_cost_mc.py`
- `analysis/nonfigure_upgrades_2026_09_29/validate_nonfigure_upgrades.py`
- `tools/audit_live_manuscript_truth.py`

The older phrase-sensitive checker is retained for development history but is no longer the publication gate.

## Retired/superseded values

Historical FINAL-1.0 values and retired cross-reaction metrics remain traceable only through `docs/RETIRED_RESULTS.md`; they must not be reintroduced into current figures, captions or manuscript text.
