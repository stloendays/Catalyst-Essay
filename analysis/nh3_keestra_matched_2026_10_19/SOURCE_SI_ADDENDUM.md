# Keestra Ru 2025 original SI verified — additive post-protocol scientific record

**2026-10-19.** This is an ADDENDUM prepared after the original G0–G4 protocol. Do not retrospectively rewrite original preregistration, original experimental endpoints, canonical NH3-FINAL-1.2, manuscript, or old Fe/Fe-first/Ru atlas in PR #111.

## Original published catalyst-specific data (discovered this turn)

Paper: Keestra, Rouwenhorst & Brilman, Chemical Engineering Journal 523 (2025) 168541, DOI 10.1016/j.cej.2025.168541.

Official supplement (1,247,144-byte genuine PDF):
https://ars.els-cdn.com/content/image/1-s2.0-S1385894725093830-mmc1.pdf

SHA256 (pinned): **a6137d61860d2c55905a12544d7792437592a02fcbed6b0d05c237d4a1569598**.

Source location: **A-1-4 Model D, Table 8, source PDF page 5**, row **Ru-Ba-K/C – Liu (2013) [4]**. IMPORTANT: Tables for Models A/B/C are different and do not supply the Model D correction factors.

| Published fitted source parameter | Value | Original reported 95% CI half-width |
|---|---:|---:|
| b_cat for promoted Ru-Ba-K/C | **76.25** | 0.03561 |
| b_N for promoted Ru-Ba-K/C | **0.8514** | 0.008091 |

These values are distinct from the baseline FREA-AIST Ru/CeO2 (b_cat=b_N=1). The source-pinned CI now independently reads the publisher PDF, requires the exact SHA, Model D heading, printed catalyst row, both point estimates and both printed confidence-interval values. No fitting to the 5.8x source bed-volume or ~19x mass target occurred.

## Scientific implication: state-dependent, same-pressure *local kinetic* preference

With the two Keestra published global rate laws and the above correct source-specific factors, calculate at **100bar absolute, 400C, H2/N2=2.25** and equal local gas conditions, using **explicit ideal-gas fugacity approximation fi=yiP, NOT corrected SRK**:

- **0 inlet NH3:** local Fe rate > Ru-Ba-K/C rate; Ru/Fe local rate ratio about **0.554**.
- **11mol% inlet NH3** (authors' reported final-bed input): Ru-Ba-K/C local rate > Fe rate, Ru/Fe local ratio about **6.889**.
- The calculated **ideal-fugacity local crossover** at 400C occurs near **0.997 mol% inlet NH3**. The temperature sensitivity grid (350–450C) will be provided as CSV, JSON and a clearly marked conditional figure in GitHub Actions artifacts.

This captures a plausible stronger product-inhibition burden on Fe and is a mechanistic **local source-model diagnostic**. The 6.889 ratio is **not** an experimentally reported ratio; the 0.997% root is NOT a measured crossover, not a whole-bed outcome, and not a cost-optimal phase boundary. The 2025 authors used modified SRK fugacities and an adiabatic plug-flow reactor, whereas the current exploration uses ideal fugacities. No high-pressure rate-validation assertion is made.

## What is unblocked versus still blocked

| Gate | Status | Evidence limit |
|---|---|---|
| Original Ru-Ba-K/C Model D source factors | **PASS** | PDF SHA + Table 8 source row, no backfitting |
| 100bar same-formulation Fe/Ru local rate evaluation | **PASS IDEAL-ONLY** | same gas/P/T, *not* observed catalyst rate |
| Commercial final-bed 100bar PFR: 5.8x volume and ~19x mass | **BLOCKED** | corrected-SRK thermo + original adiabatic bed/heat integration + per-formulation source applicability |
| Modern-kinetics Fe/Ru/Fe-first full economic atlas | **BLOCKED** | prerequisite source-equivalent bed and common economic boundary |
| 1996/2011/2024 independent kinetics holds | **NOT ESTABLISHED** | 1996 Kowalczyk and 2024 Cholewa in the 2025 fit training; 2011 Pan uses different catalysts |

Historical original PR #114 G2 output-table GHSV 130000/22250=5.8427 and density adjustment ~19.4757 are **arithmetic on printed model outputs**, not a new rate/PFR replication.

## Strict isolation from other new PRs

PR #111 is the Dyson-Simon Fe / Rossetti Ru/C discrete staged **economic** atlas; its catalyst identity, rate windows and economics are not re-used as Keestra validation.

PR #112 examines a **different reaction** (Ru/Ni Sabatier CO2 methanation; source-informed economics); not a NH3 matched-kinetic comparison.

PR #113 revises **Au/TiO2** material-specific activity/lifetime and control assumptions; not a NH3 kinetic experiment.

This branch, PR #114, alone holds Keestra 2025 source-model verification. None of these draft lines changes the main paper until author/supervisor decides.

**Next verifiable gate:** reproduce original 100bar commercial final-bed GHSV 22,250 Fe and 130,000 Ru using original source-defined corrected SRK EOS, adiabatic PFR/enthalpy and the pinned catalyst factors, without fitting against the target values. Once this is confirmed, rerun a *separate* economic model with appropriate sensitivity and structural-error bounds. At 0.36–0.55% median relative advantage in old PR #111 staged cells, cost closure matters as much as kinetics.
