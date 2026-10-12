# Hou In2O3 original Ar feed correction: CI-verified findings

**Status:** Exploratory source erratum and read-only counterfactual, not manuscript-ready or frozen. The original extraction, frozen S5, main scientific text and earlier optimization output are unchanged.

**GitHub Actions success:** https://github.com/stloendays/Catalyst-Essay/actions/runs/38247573438

## 1. Original original-paper and SI evidence

Journal of Environmental Sciences **140 (2024) 91–102**: Hou et al., DOI **10.1016/j.jes.2023.05.010**. Original article Sec.1.4 includes both Au/In2O3 and **bare In2O3** catalytic tests and gives **H2:CO2:Ar=4:1:1**. The SI Table S5 abbreviates this as H2:CO2=4, while its actual three bare table entries print:

| Bare In2O3 | CO2 X (%) | MeOH S (%) | STY, g MeOH/gcat/h |
|---|---:|---:|---:|
| HM | 5.43 | 53.23 | 0.12 |
| NP | 7.46 | 47.61 | 0.15 |
| NS | 9.15 | 44.08 | 0.17 |

Source PDF/SI PDF/SI DOCX SHA256 have been verified against private repository release archive freeze-field-2026-10-12; only the DOI and brief experimental numerical facts, **not copyrighted full publisher content**, appear here.

**Correct source interpretation:** H2/CO2=4 is the ratio of two reactants, not the complete gas composition. For 4:1:1, actual laboratory y_CO2=**1/6**, not 1/5. Three bare SI controls (old row IDs 132–134) were compiled with y_CO2=.20, while the same paper's three Au/In2O3 points (old row IDs 129–131) already used 1/6. This was a **source-extraction inconsistency**, not a new measured result.

### Independent numerical rate-balance crosscheck

The main experimental method specifies 60 mL/min gas and 200 mg of catalyst, or an implied 18 standard L per gcat per hour, before a standard-conditions flow calibration uncertainty. Approximate methanol STY from the printed CO2 conversion and MeOH selectivity is:

    STY = 18 L/(gcat h) × y_CO2 × X_CO2 × S_MeOH
          × (32.042 g MeOH/mol)/(22.414 standard L/mol)

| Bare source | Printed STY | Predicted, yCO2=1/6 (Ar present) | Predicted, yCO2=0.20 (Ar ignored) |
|---|---:|---:|---:|
| HM | 0.12 | 0.12396 | 0.14875 |
| NP | 0.15 | 0.15232 | 0.18278 |
| NS | 0.17 | 0.17298 | 0.20757 |

The argon-inclusive estimate deviates by 1.5–3.3%, vs 21.9–24.0% under the old no-Ar assumption. This **checks the volumetric reactant feed interpretation**, conditional on nominal standard-state molar volume, and does not replace the experimentally printed methanol STYs.

## 2. Three isolated equilibrium model treatments

- **Legacy source:** bare y_CO2=0.20, Au y_CO2=1/6, laboratory inert treated as N2 by the original PR EOS.
- **Corrected, N2 proxy:** all six laboratory y_CO2=1/6, N2 thermodynamic surrogate retained; this isolates the missing feed dilution.
- **Corrected, Argon PR:** all six laboratory y_CO2=1/6, actual Ar gas added to the Peng–Robinson EOS for **laboratory equilibrium solving ONLY**. Tc=150.687 K, Pc=48.63 bar, acentric=-0.002 from NIST sources (cubic-EOS kij=0 assumption).

For bare controls at 300 C, 30 bar:

| Equilibrium laboratory CO2 conversion | Legacy | Ar fraction corrected / N2 proxy | Corrected / Ar PR |
|---|---:|---:|---:|
| Xeq | 27.6258% | 27.2285% | 27.2445% |

The industrial plant mixture, its N2 surrogate, model operating constraints, **measured STY and measured selectivity** are unchanged. No laboratory 1/6 Ar is inserted into the industrial recycle/inlet limit.

## 3. Joint loading-purge economic reoptimization and original leader audit

- Six Hou entries in **two** source comparison groups, **one independent paper**, plus 304 unchanged experimental points: 310 entries, 40 original groups.
- Across each of **56** process settings (m maxima 10,25; four reactor-inlet compositions; seven engineering equipment-cap choices), recompute **all six source candidate** minima from the old and corrected feed approaches.
- **336 old optima precisely reproduce the previous PR #56 candidate calculation**, and the legacy version of **all 40 original-STY-champion group statistics** reproduces PR #56, including its 3-inlet stable comparison intersection.
- New CI outputs contain **1,008 candidate/scenario optima**, **336 source-group decisions**, and **168 complete 40-group summary scenarios**.

At m_max=10, 6.8625% published industrial reactor-inlet non-H2/CO2 reference envelope, and no additional equipment limit:

| Original source baseline | Corrected N2 | Corrected Ar |
|---:|---:|---:|
| Bare NS-vs-HM original-STY-champion economic regret 25.641% | 26.157% | 26.156% |

Original **lab STY leader remains bare In2O3-NS**; current surrogate's economic leader remains bare In2O3-HM. The Au/In2O3 source group's lab and economic leader remain Au/In2O3-NS. The corrected laboratory equilibrium does **not** change the source-group champion identities or the material-regret classification in any of the 56 setting combinations.

All **40 original comparison-group totals and all three-inlet stable material cross-formulation case sets** also stay unchanged in all 56 settings. Without additional plant equipment-cap constraints, the intersection is **four source groups from three DOI papers** (one Hou, one Re/TiO2, two InNi3C0.5 space-velocity cases from one publication). **Do not** call these four independent papers or cross-element active-metal tests.

## 4. Interaction with unreported CO/CH4 product selectivities

SI Table S5 reports MeOH selectivity but not a CO/CH4 split for the bare catalysts. The original model assigns unreported residual carbon to CO. The paper describes CO as a principal coproduct and methane as trace.

An intentionally *adversarial, experimentally unrealistic* alternative assigns **100% of that residual carbon to CH4**. Both endpoints use **corrected 4:1:1 Argon laboratory equilibrium**, with catalyst loading **and** purge reoptimized, covering **three bare samples × 56 process settings**.

At m_max=10, no additional equipment cap:

| Reference industrial inlet non-H2/CO2 ceiling | Original residual-as-CO model regret (NS vs HM) | Adversarial residual-as-CH4 model regret |
|---|---:|---:|
| 4.92% | 25.914% | 25.743% |
| 6.8625% | 26.156% | 26.647% |
| 10.249% | 27.077% | 28.400% |

**All 14 combinations of loading upper bound and equipment-cap choice** preserve their original 3-industrial-inlet-envelope *stable case membership* under this joint Ar × missing-product test. This is model-specific boundary robustness, not a measured CO/CH4 distribution or statistical confidence interval.

Under the tighter joint limits on catalyst inventory, reactor-inlet throughput and recycle compressor power, the Hou group may become **unrankable because all candidates are infeasible**. The disappearance of this case under such caps is **not proof** that the experimental and economic rankings agree. Equipment bounds are reference ratio screens, not documented universal scale limits.

## 5. Paper-ready caveats and development gate

Source correction is robust, but the mechanistic claims remain limited by **unverified CO/CH4 speciation**, one-point-calibrated first-order X(m), fixed selectivity with loading/residence-time changes, the original approximate TEA and the 1.5 bar pressure drop that still lacks bed geometry/Ergun validation. NIST Argon constants and the original PR binary interaction assumption are model inputs, not proof of real plant equilibrium kinetics.

**Proposal for next manuscript revision:** List the original source methods/4:1:1 inlet and table-level consistency check in SI; clearly separate catalyst *morphology* comparisons from metal chemistry comparisons; report fixed-original-STY rankings and losses of feasible comparisons, and label equipment limits and modelled costs as scenarios. Do not overwrite the frozen result before review.

**Generated files:**
- analysis/meoh_hou_feed_recheck_2026_10_12/recheck_source_argon.py
- analysis/meoh_hou_feed_recheck_2026_10_12/stress_missing_product_split.py
- analysis/meoh_hou_feed_recheck_2026_10_12/tests/test_source_argon.py
- analysis/meoh_hou_feed_recheck_2026_10_12/results/ (complete three-source variants, decision summaries, coupled byproduct extreme)
- .github/workflows/meoh-hou-argon-feed-recheck.yml

**The original project source extraction file and frozen source experiment files remain unmodified.** A future reviewed correction must be recorded as a source-level erratum rather than silently changing committed old numbers.
