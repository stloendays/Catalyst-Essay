# Hou 2024 In2O3 experimental Ar feed correction: unfrozen analysis

## Original publisher evidence

Source: Journal of Environmental Sciences, 140 (2024) 91-102, DOI 10.1016/j.jes.2023.05.010. This repository's private source-archive sister repository holds the original article/SI in release freeze-field-2026-10-12; both SI media and article hashes were verified by GitHub Actions.

- Section 1.4 of the main article explicitly describes catalytic activity tests of BOTH Au/In2O3 and bare In2O3 catalysts at H2:CO2:Ar = 4:1:1, gas flow 60 mL/min and mass 200 mg. The SI Table S5 only abbreviates H2:CO2=4. Therefore y_CO2=1/6, including the bare In2O3-HM, -NP, -NS controls.
- Main publisher PDF SHA-256: a42b9e52bc33b8de323be4c2010b4c9d7faaeb1934fef96c7c6cd7f213ff51b7.
- SI publisher PDF SHA-256: e429573f05bdd233f96963d397f6cd1ca802edf23e49adf42923b73b8aceb446.
- SI publisher DOCX SHA-256: effbce2d5cad7d88183bd3e6851cc3c809eb6977f19148b55d6b70d4034ea8fe.
- Existing old candidates give y_CO2=1/6 for three Au/In2O3 points but y_CO2=0.20 for the THREE bare In2O3 SI Table S5 controls. Source Table S5 itself prints bare HM: X=5.43%, MeOH selectivity 53.23%, STY=0.12; NP 7.46%,47.61%,0.15; NS 9.15%,44.08%,0.17 g/gcat/h. Those SIX measured values and source identity do not change.

## Three isolated computational variants

1. legacy: exact old curated y_CO2=0.20 for three bare points, 1/6 for Au, laboratory inert approximated with N2 in the original source model.
2. corrected_N2_proxy: all six laboratory points use 1/6, original N2 laboratory EOS stand-in preserved. This isolates the effect of the original incorrect bare inert *fraction*.
3. corrected_Ar_PR: all six laboratory points use 1/6, genuine Ar for laboratory Peng-Robinson gas fugacities. This isolates the remaining **species** approximation.

Argon PR Tc=150.687 K, Pc=48.63 bar, acentric=-0.002 from NIST physical-property reference and teqp docs:
- https://srd.nist.gov/jpcrdreprint/1.556037.pdf
- https://pages.nist.gov/teqp-docs/en/main/models/cubics.html

Argon is inserted into PR species ONLY while solving experimental-feed equilibrium, then the original PR component set is restored before industrial TEA and recycle. Laboratory Ar 16.67% MUST NOT be imported as the industrial reactor inlet limit of 4.92%, 6.86% or 10.249%; those refer to an independent plant-design reference.

## CI acceptance and numerical design

Reload frozen-compatible 310 printed candidates, 40 groups, original measured STY and group leaders. Verify exact source conditions for the six Hou entries, from TWO source comparison groups (bare vs Au; one publication DOI). Re-optimize all six original 56-case cost results and assert the previous PR #56 optima match numerically. Then evaluate the corrected N2 and Ar laboratory feed equilibrium in the full m-p joint search with m maxima 10/25, original purge grid, original three published plant inlet envelopes, original seven reference-scale engineering equipment caps.

Overlay the six corrected optima on the original 304 unchanged candidate optima, retaining the original 40 group denominators. Hold each group's original experimental STY leader fixed; count cases lost to feasibility independently from genuine cost ranking changes and >5% regret. Compute the intersection of 3 plant design envelopes, with DOI-level independent paper counts. Require legacy totals and all original stable groups to exactly reproduce the already accepted 40-group source-fixed economic result.

Unchanged point data, reactor cost equations, first-order conversion surrogate, manuscript, figures and main/frozen branches remain untouched.

## Outputs

- analysis/meoh_hou_feed_recheck_2026_10_12/recheck_source_argon.py : source-locked and isolated model reruns
- analysis/meoh_hou_feed_recheck_2026_10_12/tests/test_source_argon.py : tests
- results/hou_candidate_feed_variants.csv : six candidates across all three cases
- results/hou_group_rankings_fixed_original_sty.csv : two affected groups under each design
- results/hou_feed_source_correction_summary.json : full-cohort group-level material-regret and three-inlet evidence
- .github/workflows/meoh-hou-argon-feed-recheck.yml : GitHub Actions reproducibility

## Model limitations

Bare In2O3 CO/CH4 speciation remains unreported; it is represented by the existing fixed-product closure, not independently validated. PR argon k_ij=0 and lowest converged equilibrium root are approximations. The one-point first-order X(m) and fixed catalyst selectivities are not measured kinetics. Industrial bed hydraulic pressure drop is the old fixed 1.5-bar assumption, not a validated Ergun design. The new source correction is from ONE independent paper and must never be interpreted as a prospective experiment or new chemical class.
