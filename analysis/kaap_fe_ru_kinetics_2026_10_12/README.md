# Independent Fe / Ru-CeO2 bed-order experiment

**STATUS: UNFROZEN DIAGNOSTIC. NOT A VALIDATED KAAP MODEL. DO NOT MERGE WITHOUT AUTHOR REVIEW.**

Source parameters from Cholewa et al. 2024 Sustainable Energy & Fuels, https://doi.org/10.1039/D4SE00254G : Fe Arrhenius k0=3.35e9, Ea=144kJ/mol, alpha=.5, NH3 adsorption dH=-15.6kJ/mol, dS=-24.4J/mol/K, f=.261. Ru/CeO2: k0=3.49e8, Ea=106kJ/mol, alpha=.25, H2 adsorption dH=-87.1kJ/mol, dS=-80.1J/mol/K, f=.116; NH3 adsorption dH=-11.84kJ/mol, dS=-143J/mol/K, f=.414. The observed range is 350-450 C and 10-80 bar. **Ru/CeO2 must not be represented as the KAAP promoted Ru/C.**

Industrial comparators only, no calibration with their numerical kinetics: Tripodi 2018 https://doi.org/10.1016/j.jiec.2018.05.027 and Tripodi 2021 https://doi.org/10.1021/acs.iecr.0c05350 . Equilibrium uses NIST N2/H2/NH3 1-bar Shomate coefficients: https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=1 ; https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Mask=1 ; https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1 .

Two-bed PFR integrates reaction over catalyst mass. The fitted extended Temkin expression uses full-reaction Kp for N2+3H2=2NH3, with rate exactly zero at Gibbs equilibrium; ideal gas main calculation and SRK k_ij=0 sensitivity. **SRK cross interactions are not calibrated.** Fixed normalized inlet: 1 mol N2/s + 3 mol H2/s + 0.1 mol NH3/s, 80 bar and 425C; two beds 30kg each. This is NOT actual KAAP feed or geometry.

At 80bar / 425C ideal gas, original fitted coefficients: all-Fe N2 conversion 11.732%, Fe->Ru/CeO2 8.246%; ordering Fe->Ru beats Ru->Fe but fails versus all Fe. With a HYPOTHETICAL and UNMEASURED 20x Ru rate factor: Fe->Ru 12.248%, Ru->Fe 11.050%; equal-cost NOT TESTED. Required multiplication versus the measured Ru/CeO2 rate law is 17.232x, not evidence of a 17x commercial Ru/C activity. Equivalent hypothetical weaker Ru hydrogen adsorption enthalpy target +16.8kJ/mol, also unmeasured. With 425C first bed and 390C second bed, rate multiplier threshold rises to ~25.4x at 80bar. Gas EOS sensitivity and 90bar pressure extrapolation cannot validate a full KAAP plant.

**Required before promotion:** obtain Fe-wustite and actual promoted Ru/C differential kinetic data including H2/NH3 partial pressure dependence, validation of temperature-dependent equilibrium and fugacities, coupled energy/heat transfer, interbed cooling, Ergun hydraulics, multi-bed sizing, and integrated technoeconomic comparison including metal financing, recovery and real contract terms. Do not tune parameters to force commercial arrangement.

Run: python -m pip install numpy scipy pytest ; pytest -q test_model.py ; python run.py . Outputs in results/ are derived and noncanonical. No changes to frozen science or manuscript.
