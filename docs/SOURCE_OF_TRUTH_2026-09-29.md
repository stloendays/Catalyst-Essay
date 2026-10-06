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

## NH3 — measured activity gains of modified Ru (Fig. 3a strip) — 2026-10-05

Literature activity-enhancement factors of promoted, support-modified and confined Ru over a reference Ru catalyst
measured in the same study (`analysis/promoted_ru_literature_2026_10_05/`, 35 rows from 25 sources; 9 plotted).

| Strategy | Factor | Basis | Conditions | Source |
|---|---:|---|---|---|
| Ba–Ru/C vs Ru/C | 75× | TOF per surface Ru | 300 C, 0.3 MPa | Siporin et al., Catal. Lett. 2004 |
| Cs–Ru/C vs Ru/C | 65× | TOF per surface Ru | 300 C, 0.3 MPa | same |
| Ba–Ru/BN vs Ru/BN | >100× | per g, same Ru loading | 400 C, 5 MPa | Hansen et al., Science 2001 |
| Cs–Ru/MgO vs Ru/MgO | >134× (350 C), >30× (300 C) | per g, matched Ru | 0.1 MPa | Larichev et al., J. Phys. Chem. C 2007 |
| Cs–Ru/YSZ vs Ru/YSZ | ~10× | per g Ru | 450 C, <= 1.1 MPa | ACS Sustain. Chem. Eng. 2019 |
| Ru/C12A7:e- vs Ru/C12A7:O2- | 9.8× | TOF (CO count) | 400 C, 1 MPa | Kitano et al., Nat. Chem. 2012 |
| Ru/BaTiO2.5H0.5 vs Ru/BaTiO3 | 8.4× | TOF | 400 C, 5 MPa | Tang et al., Adv. Energy Mater. 2018 |
| Ru/Ba–Ca(NH2)2 vs Cs–Ru/MgO | >= 33.5× | TOF (STEM count) | 300 C, 0.9 MPa | Kitano et al., Angew. Chem. 2018 |
| Ru inside vs outside CNT | 0.5× | TOF | 400 C, 1–4 MPa | Chem. Eur. J. 2010 |

State: SUPPORTING (external literature placed on the model's multiplier axis). **Semantic lock:** the model's alpha
multiplies the turnover frequency of an unpromoted Ru step site, so only factors against an unpromoted reference on
the same support are like-for-like; the Ba–Ca(NH2)2 factor is against an already promoted reference and is a lower
bound. Most factors were measured at 0.1–1 MPa; the Ba–Ru/BN and BaTiO2.5H0.5 points are at 5 MPa.

## Methanol — counterfactual and backward design — 2026-10-05

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| CH4 selectivity removed (moved to MeOH) | rho -0.80 vs STY per g Re | DERIVED-A | `analysis/meoh_counterfactual_backward_2026_10_05/` |
| conversion equalized (X = 0.2875) | rho +0.80 | DERIVED-A | same |
| STY-winner parity by STY alone | unreachable (unlimited STY: 954.64 vs 943.30 EUR/t) | DERIVED-A | same |
| STY-winner parity by conversion alone | X 0.23 -> 0.281 | DERIVED-A | same |
| STY-winner parity by 100 % MeOH selectivity | 941.27 EUR/t (reaches parity) | DERIVED-A | same |

The common five-step protocol across the three systems is tabulated in `docs/UNIFIED_PROTOCOL_2026-10-05.md`.

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
| MeOH normalized upstream-selection regret | 1.9305% | DERIVED-A | same |
| Au/TiO2 selection regret | 0 | DERIVED-A | same |
| pairwise transfer index, NH3 Ru vs Fe | +0.08531 | DERIVED-A | `pairwise_inversion_index.csv` |
| pairwise transfer index, MeOH STY winner vs NPC winner | +0.01489 | DERIVED-A | same |
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

## Methanol — Table 3 input correction and measurement Monte Carlo — 2026-10-05

The 1 wt% Re, 250 °C state now uses its Table 3 selectivities (Gothe et al., ACS Catal. 2025: CH₃OH 97%, CO 1%,
CH₄ 1%); the workbook previously carried CH₄ 3%. Under the workbook's closure convention the inputs are S_CH4 = 0.01 and
S_CO-like = 0.02. Every model-written workbook value was recomputed from Candidate_Inputs with
`data/meoh/meoh_d01_model.py` (a port of the original generator that reproduces all stored values to < 1e-10 EUR/t
before the correction; `data/meoh/regenerate_d01_values.py --check`).

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| net production cost, 5%-200 / 1%-250 / 1%-200 / 5%-250 | 943.30 / 961.51 / 966.96 / 1258.17 EUR/t | CANONICAL | `data/meoh/meoh_candidate_ranking_D01v3.csv` |
| STY-per-g-Re vs economic ranking | rho 0.40, tau 0.33, 2/6 inverted | CANONICAL | provenance JSON |
| upstream winner economic rank | #2 | CANONICAL | same |
| purge sweep 0.5-40% (396 levels) | max rho 0.80; >= 1/6 inverted; upstream winner never economic #1 | DERIVED-A | `meoh_purge_robustness_D01v3_summary.json` |
| measurement MC, winner kept first | 4,559/5,000 (91.2%) | DERIVED-A | `analysis/meoh_measurement_mc_2026_10_05/mc_summary.json` |
| measurement MC, #2 <-> #3 exchange | 1,054/5,000 (21.1%) | DERIVED-A | same |
| measurement MC, 5%-250 last | 5,000/5,000 | DERIVED-A | same |
| measurement MC, STY winner economic #1 | 413/5,000 (8.3%) | DERIVED-A | same |
| measurement MC, full STY ranking recovered | 24/5,000 (0.5%) | DERIVED-A | same |
| winner kept first at width x0.5 / x2 | 99.3% / 78.4% | SUPPORTING | same |

**Semantic lock:** the source reports no error bars; the measurement uncertainty is built from the source data
(reporting resolution, 5.2% relative conversion uncertainty from STY/conversion consistency over 21 runs, 0.85-pt
MeOH-CH₄ exchange from 11 runs of one catalyst; `derive_uncertainty_basis.py`). The 2026-09-20 cost-parameter MeOH
matrix (`analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv`) was computed on the previous inputs and
is superseded by the measurement Monte Carlo in Fig. 4d.

## Methanol — generalized model and 21-candidate extension — 2026-10-05

`data/meoh/meoh_general_model.py` extends the recycle-economics engine to arbitrary catalysts: pressure and H2/CO2 as
inputs, productivity per g metal or per g catalyst, optional catalyst replacement (off by default), and recycled CO
hydrogenated per pass. With inert CO (x_CO = 0), 100 bar and H2/CO2 = 4 it reproduces the canonical workbook to
< 1e-12 EUR/t (`analysis/meoh_general_model_2026_10_05/validate_general_model.py`).

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| central CO rule | x_CO = smallest per-pass CO conversion keeping the outlet at or below RWGS equilibrium | method | `analysis/meoh_general_model_2026_10_05/README.md` |
| reference loop (Processes 2022), loop CO in/out | central 1.45/1.71 mol% vs published 1.50/1.76; inert 1.63/1.91 | DERIVED-A | `reference_loop_comparison.csv` |
| canonical four states under recycled CO | order unchanged; regret 1.53 % (central), 1.03 % (high) | DERIVED-A | `canonical_states_co_treatments.csv` |
| Gothe Table 4, 21 entries, 2 % purge | STY-per-g-Re winner economic #8; rho 0.66, 57/210 pairs inverted; regret 3.58 % (inert) / 3.99 % (central) | DERIVED-A | `table4_rank_metrics.csv`, `table4_summary.json` |
| Gothe Table 4, 14 entries at 100 bar and 1:4 | STY-per-g-Re winner economic #5; regret 3.38 % / 2.96 % | DERIVED-A | same |

**Semantic lock:** seven Table 4 entries are at other pressures or feed ratios and are flagged as different operating
points; the model does not represent weaker condensation in 20–40 bar loops. CO recycling changes no rank in this
CH4-dominated set (S_CO <= 2 %); it matters for CO-selective catalyst families.

## Literature extraction pilot (CO2-to-methanol) — 2026-10-05

`agent/extraction/` fetches papers, converts them to page-marked text and page images, extracts every catalyst entry
with value, unit, qualifier, location and page in strict-JSON model calls (`gpt-5.5`, reasoning effort medium; the
later batches and the recall passes ran through the local API-YES gateway with `--api-yes`; the nine ScienceDirect
papers were downloaded by hand and identified by the DOI printed in each PDF), normalizes units to the model basis and
scores against curated references. Besides the main pass there are three recall passes merged by `normalize.py`:

- digitisation of the main-text figures;
- the Supporting Information (SI) text;
- digitisation of the SI figures.

A printed main-text value outranks an SI value, which outranks a plot reading. `normalize.py` and `evaluate.py` rerun
offline from the committed raw outputs and reproduce `eval/` byte for byte.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| scored papers (2026-10-06, `paper_set.txt`) | 40: 18 TheMeCat (406 curated entries), 20 Suvarna et al. 2022 (194 entries; conditions and STY only), Gothe 2025 Table 4 (21 rows), Lam 2018 (PDF review only); SI for all 40. Shi 2020 dropped (no SI) | SUPPORTING | `agent/extraction/paper_set.txt`, `agent/extraction/eval/summary.json`, `agent/extraction/si_manifest.json` |
| entry recall / precision | 581/600 = 0.968 (TheMeCat 389/406 = 0.958, Suvarna 192/194 = 0.990); precision 0.89 after PDF review of every unmatched entry in the 18 TheMeCat papers; 52/60 (0.87, 95 % CI 0.76–0.93) in a random sample of the 423 unmatched entries of the 21 new papers | SUPPORTING | `agent/extraction/eval/entry_metrics.csv`, `agent/extraction/eval/batch4_unmatched_sample.csv` |
| field accuracy, strict, adjudicated reference | T, P, H2/CO2 1.000; GHSV 0.993; X_CO2 0.913 (0.987 loose); S_MeOH 0.734 (0.910 loose); STY 0.644 (0.782 loose); X and S scored on TheMeCat only | SUPPORTING | `agent/extraction/eval/field_accuracy.csv`, `field_accuracy_by_reference.csv` |
| values printed in tables and SI | main-text tables X 53/53, S_MeOH 53/53, STY 48/49; SI X 117/117, S_MeOH 113/114, STY 119/121; plot readings X 129/151, S_MeOH 57/129 strict | SUPPORTING | `agent/extraction/eval/field_accuracy_by_source.csv` |
| Gothe Table 4 | 21/21 rows; X, S_MeOH, S_CO, S_CH4, STY per g Re each 21/21 | SUPPORTING | `agent/extraction/eval/gothe_table4_scores.csv` |
| reference errata | 321 cells: TheMeCat cells for the 18 papers corrected against the PDFs and SI (179 rules); Suvarna 9 rules (Karelovic 2015 pressure and temperature shift; Sharma 2021 untested temperatures and per-g-Cu rates; Shen 2021 and Hengne 2018 mislabelled rows) | SUPPORTING | `agent/extraction/eval/themecat_errata.csv`, `suvarna_errata.csv` |
| tokens | 2.90 M for the 20-paper pilot; 3.20 M for the 21 batch-4 papers (main 0.99 M; figures 1.16 M; SI 0.66 M; SI figures 0.39 M); 6.10 M in total | SUPPORTING | `agent/extraction/out/token_usage.csv` |

**Semantic lock:** "adjudicated" means TheMeCat after the listed PDF- and SI-verified corrections; accuracy against the
raw TheMeCat values is reported alongside in `field_accuracy.csv`.

- GHSV is scored on the total feed or the inert-free feed, because the reference uses both conventions.
- Of the 17 entries still missed:
  - 7 are values the paper quotes from another study;
  - 6 are Sci. Adv. points or curated duplicates;
  - 3 are zero-activity rows;
  - 1 is a reference label error.
- Residual field errors are plot readings (including secondary- or broken-axis misreads), plus STY values from two papers (Chou 2019, Shi 2020) whose printed rates contradict their own conversion and selectivity.

## NH3 — bimetallic alloy extension — 2026-10-05

`analysis/nh3_alloy_extension_2026_10_05/` takes the 1,796 Mamun et al. (2019) surfaces (Catalysis-Hub
`MamunHighT2019`) through the frozen chain: most stable N* site → Dataset S1 terrace scale (14-metal fit, R² 0.973) →
workbook terrace→step regression → per-state activity on the cached response surface → frozen cost model under the
90 m³ cap. The same code path reproduces every canonical pure-metal cost to < 1e-9 USD/t.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| costed surfaces (all elements carry a frozen price) | 309; 114 (global) / 121 (anchored) inside the bed cap | DERIVED-A | `summary.json` |
| below Fe, global route | Fe3Mo 14.53, Cu3Mo 14.83, Fe3W 14.90, Ni3W 15.08 USD/t | DERIVED-A | `alloy_chain_results.csv` |
| below Fe, element-anchored route | Cu3Mo 14.60, CuMo 14.70, MoNi 14.70, CoMo 15.07, CoW 15.16 USD/t | DERIVED-A | same |
| highest-activity surface | Os3Pt economic #32, regret 69.0 % (global); AuW #29, 60.2 % (anchored) | DERIVED-A | `summary.json` |
| descriptor-only pruning | 243/309 (78.6 %) ruled out before full optimization; 0 false prunes | DERIVED-A | same |
| all priced elements (USGS MCS 2026 for the 22 non-model elements), transition-metal layer | 372 costed; below Fe: Cu3Cr, Fe3Mo, Cu3Mo, Fe3W, Ni3W (global) / Cu3Cr, Cu3Mo, CuMo, MoNi, CoMo, CoW (anchored) | DERIVED-A | `summary.json` (`extended_excluding_sp_and_group3to5`) |
| all priced elements, every layer | 1,695 costed; pruning 1,397 (82.4 %), 0 false prunes | DERIVED-A | `summary.json` (`extended_with_usgs_prices`) |

**Semantic lock:** individual below-Fe alloys depend on the descriptor bridge; the family does not — every surface below
Fe in either route is one cheap 3d metal (Fe, Co, Ni, Cu) with Mo or W. Mamun surfaces are ideal L1₂(111)/L1₀(101)
slabs; bulk phase stability is not part of this screen. Surfaces with sp metals (outside the transition-metal scaling
relations) or group 3–5 elements (stable bulk nitrides) are reported as separate layers and are not ranked against Fe.

## Methanol — paper leaderboards versus plant-cost leaderboards — 2026-10-05

`analysis/meoh_literature_inversion_2026_10_05/` runs the extraction Agent's records (used as extracted) through the
generalized methanol model. Comparison groups are the entries of one paper at the same P, H2/CO2 and space velocity.
The paper leaderboard is STY per g catalyst; the plant leaderboard is the net production cost with CO recycled
(central rule) and entry-optimal purge.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| Agent self-check: Gothe Table 4 from extracted inputs | 21/21 entries equal the frozen costs (max 2.3e-13 EUR/t); canonical states 943.30 / 961.51 / 966.96 / 1258.17 | DERIVED-A | `selfcheck_gothe_table4.csv` |
| scored comparison (40-paper set, 2026-10-06) | 750 candidates from 35 papers; 68 groups, 682 entries, 34 papers. Co-feed (H2O or CO) entries excluded; printed STY replaced by the mass-GHSV STY where printed / (F X S) varies > 3x within a group (3 groups) | DERIVED-A | `summary.json` |
| different winner, STY leaderboard (primary) | 27/68 groups (40 %), 14/34 papers; regret median 2.1 % (mismatched), max 182 %; 696/6006 pairs inverted | DERIVED-A | same |
| different winner, STY leaderboard, inert CO | 35/68 groups (51 %), 27/34 papers | DERIVED-A | same |
| different winner, selectivity leaderboard | 51/68 groups (75 %), 30/34 papers; regret median 18 % (mismatched) | DERIVED-A | same |
| robustness, STY leaderboard | printed values only 14/41; methanol products only 16/46; without Bansode 2013 20/60 groups, 13/33 papers, regret max 9.0 % | DERIVED-A | same |
| compute saved (`analysis/meoh_pruning_2026_10_06/`) | 156 of 682 candidates need the full optimization (526 excluded, 77.1 %); 0/68 leaders missed; 22.9 % of the compute | DERIVED-A | `analysis/meoh_pruning_2026_10_06/summary.json` |

**Semantic lock:** groups compare entries at equal pressure, so the model's simplified condensation at 20–40 bar does
not enter within-group rankings. Recycled and inert CO bound the plant ranking; the winner-change counts hold under
both, and regret magnitudes depend on the treatment. Regrets above 10 % all come from low-conversion entries of one
paper (Bansode 2013).

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
