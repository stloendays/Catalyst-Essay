# Keestra 2025 matched-pressure, formulation-explicit NH3 kinetic audit

**Exploratory study, 2026-10-19; see [SOURCE_SI_ADDENDUM.md](SOURCE_SI_ADDENDUM.md).** G0 **PASS** (source equations and equilibrium tests); G1 **PASS, in-family qualitative direction only**; **G1b PASS, published commercial Ru-Ba-K/C Model D factors independently source-verified and local 100bar ideal-fugacity screening completed**; G2 **BLOCKED** (the original commercial 100bar corrected-SRK adiabatic reactor has NOT been reproduced); G3 **BLOCKED** (no new economic phases); G4 **partial** (training overlap). Does not change the main manuscript, NH3-FINAL-1.2, prior results or PR #111.

## Literature and source labels

- Keestra et al., Fe, Chemical Engineering Journal 518 (2025) 164593: https://doi.org/10.1016/j.cej.2025.164593 — Table 2 and Eq. 15, Fe AmoMax 10 with b_cat=1.
- Keestra et al., Ru, Chemical Engineering Journal 523 (2025) 168541: https://doi.org/10.1016/j.cej.2025.168541 — Table 3 and Eqs. 10-12, FREA-AIST Ru/CeO2 with b_cat=b_N=1. The original commercial Ru-Ba-K/C Model D factors have now been verified in the publisher's SI A-1-4 Table 8 (b_cat 76.25, b_N 0.8514), independently of Ru/CeO2.
- Cholewa et al., Sustainable Energy & Fuels (2024): https://doi.org/10.1039/D4SE00254G — Clariant Fe and FREA-AIST Ru/CeO2, 10/45/80bar **gauge**, 350-450C, training source for Keestra Fe/Ru.
- Kowalczyk et al., Applied Catalysis A (1996): https://doi.org/10.1016/0926-860X(95)00251-0 — active-carbon supported Ru; **included among Keestra Ru training sources**: Figure 1 says fits refs [1,19,23-27], and Kowalczyk is ref [27]. Not independent.
- Pan et al., Chinese Journal of Chemical Engineering (2011): https://doi.org/10.1016/S1004-9541(11)60165-1 — A301 Fe vs carbon-supported Ru; different formulations from Keestra's reference samples.

## G0 and G1: Implemented and cloud tested

The mathematical 2025 global Langmuir-Hinshelwood kinetic equations, Arrhenius coefficients and sign of the published equilibrium exponent are implemented without fitting. Numerical rate screening deliberately uses **ideal gas fugacities** rather than the Keestra authors' corrected-SRK fugacity calculation. An isothermal ideal-fugacity plug-flow integrator is used only as a schematic source-direction test. Passing the published rate formula, equilibrium-zero and direction unit tests is not independently validating industrial reactor output.

G1 conditions: Cholewa 80bar(g)=81.01325bar(a), 350,400,450C; H2/N2=3; **assumed zero-NH3 inlet**; Keestra reference Fe AmoMax10 (b_cat=1) and reference Ru/CeO2 (b_cat=b_N=1). The following are **our approximate model initial rates, not Cholewa's experimentally printed rates**:

| T | Fe model mol NH3/kg-cat/s | Ru/CeO2 model mol NH3/kg-cat/s | Model Fe/Ru initial rate |
|---|---:|---:|---:|
| 350 C | 0.036906943 | 0.000183678 | ~200.93 |
| 400 C | 0.180167506 | 0.001307245 | ~137.82 |
| 450 C | 0.706360441 | 0.007088085 | ~99.65 |

Fe model activity exceeds Ru/CeO2 at each point, in the qualitative direction described in Cholewa 2024. Cholewa's dataset contributed to both Keestra calibration sets; **this is not an independent experimental holdout**. No original absolute rate uncertainty, printed paired observed rates or same-material Ru-Ba-K/C experimental benefit has been established. Schematic isothermal-PFR outlet figures in CI artifacts are model illustrations, not reproduced source chromatograms.

## G2: Source 100bar industrial reactor comparison is blocked

Keestra Ru 2025 Table 4 presents authors' own *modeled* single adiabatic PFR final-bed comparison: 100bar(a), 400C, NH3 inlet 11mol%, H2/N2=2.25, voidage 0.4, densities Fe=2500 and Ru=750 kg/m3, and a 90%-of-adiabatic-equilibrium conversion target. Their **commercial 4wt% Ru-Ba-K/C** is distinct from FREA Ru/CeO2. They report approximately 5.8 times less required Ru bed *volume* and 19 times less Ru bed *mass*.

An **arithmetical source-table check**, not an independent kinetic model prediction, follows directly from two printed Table 4 output GHSV values: 22,250 h-1 Fe and 130,000 h-1 Ru. Under the same inlet flow, bed volume scales as 1/GHSV. Thus Fe/Ru bed volume ratio = 130000/22250 = **5.8427**; multiplying by bulk density ratio 2500/750 yields Fe/Ru catalyst bed mass ratio **19.4757**. This independently verifies the *arithmetic consistency of the paper's two already-computed outputs*, not the rate-derived physics, real bed geometry, or external measurements.

**Source-factor obstacle resolved, but G2 remains BLOCKED.** The verified publisher SI [PDF](https://ars.els-cdn.com/content/image/1-s2.0-S1385894725093830-mmc1.pdf), exact SHA256 pinned in [SOURCE_SI_ADDENDUM.md](SOURCE_SI_ADDENDUM.md), yields Ru-Ba-K/C Model D Table 8 **b_cat=76.25** and **b_N=0.8514**, while Ru/CeO2 remains b_cat=b_N=1. The new ideal-fugacity 100bar, 400C local comparison gives Ru/Fe ~**0.554** with 0% inlet NH3 and ~**6.889** with 11% inlet NH3. These are **model predictions at a single local gas state**, not measured rates or a full reactor. A source-faithful corrected-SRK fugacity model, adiabatic PFR and material-specific applicability/error assessment remain incomplete. Never backfit these factors to the source 5.8x bed-size target.

## G4: External literature evidence discipline

| Paper | Tested materials and pressure | Independence / permitted conclusion |
|---|---|---|
| Cholewa 2024 | Clariant Fe / FREA Ru/CeO2; 80bar(g) among their source range | Keestra model **TRAINING**. Qualitative in-family only; no raw 80bar numerical point extracted |
| Kowalczyk 1996 | Active-carbon supported Ru, 100bar | **TRAINING** in Keestra Ru Figure 1 reference [27]. Do not present as external validation |
| Pan 2011 | A301 Fe vs activated-carbon supported Ru, **10 MPa**, 375-400C, H2/N2=3, GHSV=10,000 h-1 | Abstract-level, different-composition experimental contrast. Pan reports Ru activity **33.5%-37.6% higher** than its Fe and Fe+Ru series NH3 outlet **45.6%-63.5% higher** than only Fe, at reported conditions. Not reproduced quantitatively or transferred to Keestra coefficients |

The opposite Fe-vs-Ru direction between Cholewa 2024 and Pan 2011 is scientifically consistent with **different catalyst formulations**, not automatically an error in either experiment. Numerical comparison across them requires exact Ru promoters, loading, catalyst mass normalization and gas/pressure conditions, not just the generic labels "Fe" and "Ru".

## Reproduction and gate status

GitHub Actions runs Python3.12 and 16 formal tests (once the latest source-audit CI is green), uploads Fe/Ru-CeO2 and commercial Ru-Ba-K/C local-rate CSV/PNG/SVG, exact source PDF-row hash checks, REPORT and machine-readable readiness. The **industrial G2 requirement must explicitly exit with code 2** even if all numerical G0/G1 tests pass. No expensive new optimization or manuscript changes.

    python -m unittest discover -s analysis/nh3_keestra_matched_2026_10_19 -p 'test_*.py' -v
    python analysis/nh3_keestra_matched_2026_10_19/run_audit.py --out /tmp/nh3_keestra --plot
    python analysis/nh3_keestra_matched_2026_10_19/run_audit.py --out /tmp/nh3_keestra --require-100bar-completion

The last command intentionally exits 2 until original-source corrected-SRK gas properties, the adiabatic full-bed reactor and formulation-level applicability checks pass; the catalyst-specific SI parameters are now available and pinned.

**Next physical science gate:** source the original authors' modified-SRK pure/binary and property parameters; implement a dimensionally and thermodynamically validated adiabatic PFR; reproduce the authors' 100bar final-bed design independently with the now-pinned commercial Model D factors, without fitting published target outputs. Only after this should the new matched-formulation process cost and previous PR #111 decision map be recomputed. The combined dataset's 1-200bar pressure span alone does not establish a selected formulation's individual experimentally validated window.
