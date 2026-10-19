# NH3-KEESTRA-MATCHED-2026-10-19 — SOURCE-FIRST EXPLORATORY PROTOCOL

**Status:** Protocol committed BEFORE code/outcomes. **No changes** to canonical NH3-FINAL-1.2, manuscript, figures, source data, previous kinetics or PR #111. Independent kinetic sensitivity ONLY; no selection of favorable Fe/Ru result.

## Primary literature and formulation identity

1. Fe: Keestra et al., Chemical Engineering Journal 518 (2025) 164593, DOI https://doi.org/10.1016/j.cej.2025.164593; Eq.15 and Table 2, Clariant AmoMax 10 b_cat=1. The global training ensemble covers 1–324 bar, 251–550 C; this does not establish that every Fe formulation was measured at all of those conditions.
2. Ru: Keestra et al., Chemical Engineering Journal 523 (2025) 168541, DOI https://doi.org/10.1016/j.cej.2025.168541; Eqs.10–12 and Table 3. Reference Ru/CeO2 from Cholewa has b_cat=1, b_N=1. The globally pooled Ru training ensemble covers 1–200 bar, 247–465 C, but that span is NOT guaranteed for every specific Ru composition.
3. Source industrial final-bed case in Ru main text Table 4: AmoMax 10 Fe versus 4 wt% Ru-Ba-K/C, 400 C, 100 bar absolute, inlet 11 mol% NH3, H2/N2=2.25, densities Fe 2500 and Ru/C 750 kg/m3, voidage 0.4. The authors size **adiabatic** beds to 90% of final-bed equilibrium conversion and report about **5.8-fold less volume** and **19-fold less mass** for the Ru catalyst. **These are holdout validation targets; NEVER fit b_cat, b_N, calibration or any input to hit them.**
4. Cholewa et al. (2024), Sustainable Energy & Fuels, DOI https://doi.org/10.1039/D4SE00254G: Clariant Fe and FREA-AIST Ru/CeO2 experimentally tested at **10/45/80 bar(g)** and 350/400/450 C. Convert to absolute (80bar(g) = ~81.01325bar(a)). Cholewa report Fe has a higher ammonia production rate than that Ru/CeO2 material under tested conditions. Figure 4 values not tabulated exactly and must not be invented. This same data contributes to the Keestra model calibration; it is not statistically independent held-out evidence.
5. Kowalczyk et al. (1996) DOI https://doi.org/10.1016/0926-860X(95)00251-0; Pan et al. (2011) DOI https://doi.org/10.1016/S1004-9541(11)60165-1. Both are external candidate checks at nominal 100bar but catalyst formulations differ from either Keestra model's anchor, and overlap with model training must be examined before declaring an independent test.

## Exact kinetic framework to implement

Published Eq.15 Fe / Eqs.10–12 Ru:

    r_NH3 = bcat * k(T) * fN2
          * [1 - fNH3^2/(Kf(T)^2*fN2*fH2^3)]
          / [1 + fNH3/(KN(T)*fH2^1.5) + sqrt(KH(T)*fH2)]^2

    k(T) = A_k * exp(-B_k/(R*T))
    KN(T) = A_N * exp(-bN * B_N/(R*T))  (bN=1 for Fe)
    sqrt(KH(T)) = A_sqrtH * exp(-B_sqrtH/(R*T))

f fugacity units bar, P absolute bar, T Kelvin and r mol NH3 per kg catalyst per s. Keestra Fe Eq.4 equilibrium factor is Kf = 1.3628e-6 * exp(+51111/(R*T)), **because the published exponent has a double negative**.

Main Table values:
- Fe: A_k=2.215e13; B_k=+100700 J/mol; A_N=2.455e-8; B_N=-17950 J/mol; A_sqrtH=327.6; B_sqrtH=-4948 J/mol. Anchor bcat=1 for AmoMax 10.
- Ru: A_k=2.211e8; B_k=+112800 J/mol; A_N=1.569e-7; B_N=-49520 J/mol; A_sqrtH=1.116; B_sqrtH=-12190 J/mol. Anchor bcat=bN=1 for Cholewa's Ru/CeO2, **NOT** Ru-Ba-K/C.
- The Ru-Ba-K/C's individual bcat and bN are reported in Ru SI A-1, not present in the verified main-page text as an exact numeric pair. A missing source-specific value is a HARD STOP for the 100bar final-bed reproduction.

## Locked validation gates

**G0 — Source formula/unit sanity (implement now):** Two published global parameter sets; demonstrate zero net rate at a constructed thermodynamic equilibrium point; positive forward rate below equilibrium; nonnegative protective numerical outcomes and dimensionally consistent equation. Basic ideal f_i=y_i P can be used ONLY as development approximation, NOT as full source paper corrected-SRK EOS or a validated plant simulation.

**G1 — Identified-material same-pressure screening (implement now):** At 80bar(g) converted explicitly to bara and T=350/400/450 C, compare source-anchor Fe AmoMax10 (bcat=1) to source-anchor Ru/CeO2 (bcat=bN=1) at the same hypothetical H2/N2=3 inlet and declared NH3 mole fraction. Record source-based predicted rate ratios using ideal fugacity, plus exact assumptions. Test predicted direction against Cholewa's qualitative reported Fe>Ru/CeO2; report any mismatch. This is a *source-anchored approximate screen*, not an independent field validation.

**G2 — Exact source 100bar industrial benchmark (BLOCK unless SI parameters and EOS fully verified):** Require precise Ru-Ba-K/C bcat,bN from a readable SI source; modified SRK with primary-source pure/binary parameters, an adiabatic PFR energy balance, and consistent feed/geometry. Reproduce the published about 5.8x volume and 19x mass *without target-fitting*. Do NOT use reference Ru/CeO2 bcat/bN for the Ru-Ba-K/C formulation and do not label ideal fugacity run as full authors' replication.

**G3 — Process economic phase atlas (BLOCK until G2 passes):** Use the same specified formulation, common process/economic denominator and validated kinetic/application domain. Recompute Fe/Ru and mixed beds only after passing G2; no PR #111 overlay is promoted or replaced solely from model global range.

**G4 — Literature cross-check:** Independently label catalyst formulation, pressure gauge vs absolute, feed/T, printed vs graph-only observations, known overlaps with Keestra training. Do not call Cholewa data independent heldout when it was in the model training. Avoid invented extracted data.

## Output and manuscript firewall

Write only analysis/nh3_keestra_matched_2026_10_19/ and .github/workflows/nh3-keestra-matched-2026-10-19.yml. Draft PR only. CI may pass the verified G0/G1 subtask, while G2/G3 must explicitly remain BLOCKED in machine-readable readiness and scientific report. A source mismatch, missing source Ru-Ba-K/C factors, or unexpected directional failure must never be silently repaired or falsely passed. No paper changes or figure promotion.
