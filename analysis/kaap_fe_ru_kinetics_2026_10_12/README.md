# Fe/Ru two-bed kinetics — independent scientific correction (2026-10-12)

**STATUS: UNFROZEN / SCIENTIFIC AUDIT / AUTHOR DECISION REQUIRED.** Do not merge or overwrite NH3-FINAL-1.1, its figures, official ranking, existing NH3 TEA, or its process cache.

## 1. Critical finding — the first PR #68 model was not the final fitted equation

The previous branch implementation imposed detailed balance correctly but used an all-full-stoichiometry Temkin bracket equivalent to *neither* Cholewa (2024) **final fitted equation (11)** for Fe nor **equation (12)** for Ru/CeO2. Accordingly, its 17.23x Ru gain, +16.8 kJ/mol H2 adsorption and 11.73% all-Fe conversion **must not be quoted**. Passing numerical unit tests did not establish source-equation validity.

The audited final 2024 expressions are

  r = k0 exp[-Ea/(RT)] * [sqrt(Kp_full) sqrt(aN2) (aH2^1.5/aNH3)^alpha
      - (aNH3/aH2^1.5)^(1-alpha)] / D

D_Fe = 1 + K_NH3 aNH3^f3

D_Ru = 1 + K_H2 aH2^(1.5*f2) + K_NH3 aNH3^f3.

The **1.5 on f2, sqrt(Kp_full), sqrt(aN2), and half-reaction powers** are critical. At Q=Kp_full, both rates vanish identically. Parameter values are taken from [Cholewa et al. 2024](https://doi.org/10.1039/D4SE00254G), Tables 2/3 and final Eqs (11)/(12). The measured Ru phase there is **Ru/CeO2, not KAAP promoted Ru/C**. NIST Shomate thermochemistry was independently substituted for the source thermodynamic function; source fitting has **not** been independently recalibrated. SRK is a zero-binary-interaction sensitivity, not an audited industrial EOS. Source test pressure is reported in **bar(g)**: 80 bar(g) ~81.01325 bar(abs), and 90-bar-absolute diagnostics are outside the fitting pressure range.

## 2. Thermochemistry audit (matched stoichiometric inlet)

For an ideal-gas feed of N2:H2 = 1:3 with zero incoming NH3 at **90 bar(abs)**, NIST standard Gibbs energies versus the Gillespie–Beattie correlation already recorded in diagnostic PR #64 yield:

| Temperature | yNH3 NIST | yNH3 Gillespie–Beattie | Difference |
|---|---:|---:|---:|
| 400 C | 23.143% | 22.035% | +1.108 percentage points |
| 425 C | 18.572% | 17.643% | +0.929 percentage points |
| 450 C | 14.838% | 14.073% | +0.766 percentage points |

The original frozen descriptor-only thermochemistry in PR #64 gave 7.53% yNH3 at 90 bar, 425C. This separate NIST-vs-GB comparison **locates a possible explanation** for that low equilibrium but does not patch it into frozen state-dependent process optimization. Frozen states must be rechecked separately before changing official rankings.

## 3. Source-fitting regime reproduced as a falsifiable comparison

Same hypothetical feed, 1 mol N2/s, 3 mol H2/s, 0.1 mol NH3/s; **80 bar(abs), 425 C, isothermal**; *fixed total catalyst mass 60 kg, 30 kg Fe and 30 kg Ru/CeO2*. All numbers below are **single-pass N2 conversion**:

| Source kinetic condition | All Fe | Fe->Ru/CeO2 | Ru/CeO2->Fe |
|---|---:|---:|---:|
| Cholewa as published, no Ru gain | 16.736% | 12.615% | 12.287% |
| Counterfactual Ru rate multiplied 7x | 16.736% | 16.926% | 15.874% |

The unchanged source fitting selects Fe->Ru before Ru->Fe, yet all-Fe still wins. The 7x factor is **unmeasured; it is an inverse target, not a demonstrated Ru/C property**. For the equal-mass arrangement the new gain-to-parity threshold is **6.678x**. For Fe-mass fractions 0.1/0.25/0.5/0.75/0.9, minimum threshold at 80 bar(abs) among tested fractions is **6.356x**. Infinitesimal replacement at the outlet of a 60 kg all-Fe bed gives local Fe/Ru rate ratio **6.296x**; it does not include catalyst finance.

The matched-material comparison holds **each catalyst's material mass fixed when reversing order**. The first version's non-50:50 comparisons accidentally reassigned masses to the physical first/second bed when reversing the catalysts and were not fair order-only comparisons.

Within source-adjacent modeled 45/80 bar(abs) and ideal gas, the unchanged fitted kinetics gave Fe->Ru above Ru->Fe in **10/10** tested fixed-material comparisons (5 material splits x 2 pressures), but hybrid beats all-Fe in **0/10**. At the hypothetical 7x gain, **6/10** hybrid cases beat all-Fe; these are deterministic grid counts **not probabilities**.

## 4. Real Ru/C external paper — scientific corroboration, not numerical reuse

[Tripodi et al. 2018](https://doi.org/10.1016/j.jiec.2018.05.027) experimentally fitted a promoted graphitized **Ru/C** model and compared Fe and Ru in a multibed loop. Their reported outputs near 430 C, 100 bar, 30,000 h-1 are about 15.5 vol% NH3 for Ru/C at H2/N2=1.5 and 12.5 vol% for Fe-wustite at H2/N2=3. Those inlet ratios differ: **do not convert this into a controlled material ranking or use these values as measured conditions for our code**.

[Tripodi et al. 2021](https://doi.org/10.1021/acs.iecr.0c05350) independently reports the benefit of Ru/C in the later reacting stages with fixed other conditions. These results anchor the **existence** of a physically plausible Fe-first, Ru-last configuration, but our Cholewa 2024 fit is for a different support and does not reproduce their quantitative engineering outcome. The 2018 Aspen parameter table also employs a distinct fugacity, catalyst-mass and equilibrium convention; it must be reproduced and independently verified before transplanting its numerical constants.

## 5. Decision gates for promotion into manuscript

1. **DONE (isolated only):** correct published fitted 2024 kinetic expression; use NIST/GB thermodynamic audit; match Fe/Ru mass budgets on bed reversal; deterministic sensitivity and regression tests. See `run_v2.py` and `test_v2.py`.
2. **NOT DONE:** calibrate against actual promoted Ru/C and wustite **differential reaction rates under matched feed**, within 100 bar, with NH3/H2 partial-pressure variations. Reproduce a truly held-out rate/yield.
3. **NOT DONE:** couple along-bed temperature and inter-cooling, physically sourced bed hydraulic ΔP, reactor size/geometry and per-bed capacity. Do not treat methanol PR #62 Ergun diagnostics as ammonia reactor validation.
4. **NOT DONE:** use the verified rate/bed inventory as input to same-masked Fe/Ru life-cycle economic accounting from #57/#61. Do not reuse DCF parity thresholds from a different bed design.
5. **AUTHOR-ONLY:** decide whether to adopt this isolated result; frozen main-science values remain unchanged. Positive claims are limited to **thermodynamic reference agreement**, **conditional Fe-first mechanism**, and **inverse activity threshold**. An industrial KAAP outcome cannot yet be claimed.

## Reproduction and source provenance

Run `python -m pip install numpy scipy pytest`, `python -m pytest -q test_model.py test_v2.py`, `python run_v2.py`. The canonical **unfrozen** results live only under `results_v2/`; the earlier `run.py` and its `results/` are superseded exploratory artifacts and must not be used to support manuscript claims.

GitHub Actions `kaap-literature-kinetics-isolated.yml` verifies results in a clean environment and uploads the `results_v2` files. No NIST/GB result is a substitute for a complete gas-mixture EOS and true KAAP engineering validation.
