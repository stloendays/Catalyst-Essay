# G2: Source-locked Fe/Ru final-bed numerical reproduction — partial and negative outcome

**2026-10-19.** Post-outcome numerical audit. G2 source-equivalent Aspen industrial final-bed reproduction remains **FAILED/UNRESOLVED for promoted Ru**. No G3 economic rerun. This file is an additive exploratory result on Draft PR #114; no frozen NH3 data, PR #111, or main manuscript was changed.

## Original primary sources and source pins

Fe: Keestra et al., *Chemical Engineering Journal* 518 (2025), 164593, DOI 10.1016/j.cej.2025.164593. Official publisher SI https://ars.els-cdn.com/content/image/1-s2.0-S1385894725054294-mmc1.pdf, SHA256 **b43f9988b4b5f69d824409e706c1c1b8862afb523a2b18cb053f7c286465773a**. A-5-1 publishes the Mathias-corrected SRK Python implementation, A-6 the pure-component properties and binary kij, A-7 a DIFFERENT Fe Aspen example at 325C.

Ru: Keestra et al., *Chemical Engineering Journal* 523 (2025), 168541, DOI 10.1016/j.cej.2025.168541. Official publisher SI https://ars.els-cdn.com/content/image/1-s2.0-S1385894725093830-mmc1.pdf, SHA256 **a6137d61860d2c55905a12544d7792437592a02fcbed6b0d05c237d4a1569598**. Source A-1-4 Model D Table 8, Liu 2013 promoted Ru-Ba-K/C, reports **bcat=76.25** and **bN=0.8514** with their source 95% CIs. Unlike the distinct Ru/CeO2 reference whose bcat=bN=1.

Ru paper main Fig. 7/8, Table 4: source 100bar(a), 400C, NH3 inlet 11mol%, H2/N2=2.25, 90% adiabatic equilibrium conversion target, Fe/Ru catalyst bulk densities 2500/750 kg/m3, bed voidage 0.4, NTP 25C 1atm, **authors' Aspen-output GHSV Fe=22,250 h^-1 and promoted Ru=130,000 h^-1**. None of these two target GHSV values are used for fitting.

Independent caloric extension: NIST Chemistry WebBook gas Shomate enthalpies of N2/H2/NH3 with or without analytical SRK gas enthalpy departure. NIST is an approximate engineering substitute for the source Aspen enthalpy package, whose exact settings are not established.

## Physically explicit and numerical design audit

The independently integrated isobaric, adiabatic source-kinetic PFR enforces N2 + 3H2 -> 2NH3, uses original kinetic global constants and catalyst-specific source factors, and solves T from adiabatic molar enthalpy. Uses source Kf(T) with three choices of fugacity: (1) ideal, (2) author-published Fe SI Python SRK literally, and (3) conventional SRK mixing. The SI Python has an extra alpha factor in mixed a_ij relative to conventional SRK and the SI text, so both versions are retained with explicit labels. Size the bed to 90% of the model's own adiabatic equilibrium reaction EXTENT and compute GHSV independently from the integrated W/F0 and each material's published catalyst density.

### Independently predicted GHSV h^-1

| Gas EoS | Enthalpy | Fe predicted | Error vs Fe paper | Ru predicted | Error vs Ru paper | Fe/Ru bed volume ratio |
|---|---|---:|---:|---:|---:|---:|
| Ideal | NIST | 22,806.74 | +2.5% | 54,503.56 | -58.1% | 2.390 |
| SI literal SRK | NIST | 24,747.69 | +11.2% | 57,883.40 | -55.5% | 2.339 |
| SI literal SRK | NIST + SRK residual | 24,736.55 | +11.2% | 57,859.16 | -55.5% | 2.339 |
| Conventional SRK | NIST | 25,202.69 | +13.3% | 58,594.07 | -54.9% | 2.325 |
| Conventional SRK | NIST + SRK residual | 25,203.63 | +13.3% | 58,596.03 | -54.9% | 2.325 |
| **Source published Aspen outputs** | **Not a prediction by us** | **22,250** | – | **130,000** | – | **5.843** |

Our Fe gas-hourly throughput is relatively close to the paper, but **our Ru requires roughly 2.2–2.4 times more bed volume than the authors' prediction**, using the same declared source-specific rate parameters. The Ru cost/volume advantage is therefore far smaller in these reproduction attempts. For SI literal source, predicted Fe/Ru catalyst **mass** demand ratio ~7.80 vs authors' source-output implied ~19.48; the distinction between bed volume and catalyst mass is essential.

The thermodynamic options and NIST+SRK residual enthalpy variation DO NOT close this ~55% Ru GHSV mismatch. Energy is closed to approx 1e-7 J per mol inlet feed; source EOS/SI parameters and equilibrium/reversibility/units verified by numerical tests. No source parameter fitted to printed reactor outputs.

### Separate forward diagnostic, holding the AUTHORS' GHSV as INPUT

For this check only, take the authors' published bed GHSV values as given reactor configurations. Invert the same source-parameter PFR and predict how far along its own adiabatic equilibrium curve the reaction would reach:

| Source printed GHSV | Source literal SRK + NIST predicted equilibrium fraction | Source desired fraction | Model outlet NH3 mol% | Model outlet T |
|---|---:|---:|---:|---:|
| Fe 22,250 h^-1 | **93.17%** | 90% | 14.692% | 453.43C |
| Ru 130,000 h^-1 | **49.87%** | 90% | 12.947% | 428.52C |

All five EOS/energy scenarios give Ru approximately **47.9–50.3%**, Fe **90.8–93.6%**. This is a **post-outcome diagnostic**, not independent prediction of bed size (the target GHSV is an explicit operating input). It demonstrates that the discrepancy is an outlet-composition/extent shortfall, not merely a conversion of GHSV units.

Original authors describe thermodynamic equilibrium under this feed at approximately **456C**, broadly compatible with the source-locked EOS/NIST adiabatic temperature profile. Such approximate thermal agreement is not proof of identical Aspen thermodynamics.

## Specific science blockers, without retrospective repairs

1. **Rate basis and stoichiometry:** Keestra Ru paper Eq.13 includes explicit stoichiometric nu_i multiplying its rate rNH3 (with units mol kg-catalyst^-1 s^-1). Verify whether the calibrated rate is on NH3 production or on reaction-event extent, and whether the Aspen implementation uses the same normalization. Applying a factor of 2 to the Ru rate after observing the discrepancy is FORBIDDEN unless established from source equations/code. Both Fe and Ru rate conventions must be treated symmetrically.
2. **EOS source implementation:** published Python a_ij mixes alpha twice compared with conventional SRK; explicitly comparing both changes Ru GHSV by only ~1%, so the EoS implementation difference in the tested variants is insufficient to explain the full gap. The original Aspen thermo and PFR caloric settings remain unverified.
3. **Definition of 90% equilibrium conversion:** this code takes 0.9 of the adiabatic N2 reaction extent from the 11mol% NH3 inlet. A 90% ammonia outlet mole fraction or a different Aspen conversion specification can differ. Only source-authenticated specification can resolve this, not a metric chosen post-outcome.
4. **Material-specific pressure and temperature fit scope:** pooled Ru 1–200bar and 247–465C data do not confer quantitative validation on this particular Liu 2013 promoted Ru-Ba-K/C formulation along the adiabatic bed trajectory. No external independent measured rates are validated here.
5. **Catalyst bed geometry and normal flow:** source bulk density (Fe2500, Ru750 kg/m3), bed voidage 40%, NTP 25C/1atm must not double count interparticle void. Ru and Fe have different mass-specific versus volumetric activity ratios. Source ignores mass transfer; its actual Aspen reactor configuration has not been run.

## Decision

**G2 full authors' Aspen Fe/Ru final-bed replication FAILED for Ru under ALL 5 declared variants; G3 Fe/Ru/staged industrial economics NOT EXECUTED.** A green Actions workflow means the physical equations, source hashes, numerical tests and reproducibility pipeline passed; it does NOT mean G2 agreement or industrial model validity. Existing NH3 plant benchmark and PR #111 staged economic map remain untouched.

Next practical gate is to reproduce a particular source-published experimental profile using the same Ru Model D calibration and explicit mass-rate/stoichiometric convention, then compare independent source-specific rate integration to the paper's Eq.13 before revisiting the original 5.8-fold Aspen result. The 100bar, H2/N2=3, SV=8.2 Nm3 kg-cat^-1 h^-1 Ru-Ba-K/C Liu 2013 dataset in Ru paper Fig.4 is within TRAINING and so offers a calibration-consistency diagnostic, not an external holdout.

## Reproduction

Run the branch GitHub Action "Exploratory Keestra 2025 NH3 matched-domain kinetics". Four separate jobs: Fe official SI retrieval + SHA, Ru official SI Model D row/parameter SHA, prior G0/G1 source-fit tests, and G2 actual adiabatic PFR/forward-printed-GHSV tests, with CSV/JSON, reactor profile, and SVG/PNG plot artifacts. 16 previous G0/G1 tests + 17 added G2 tests green as of 2026-10-19.
