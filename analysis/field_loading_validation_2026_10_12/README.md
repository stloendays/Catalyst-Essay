# PR #55: independent methanol loading-law and reactor-limit audit (unfrozen)

This supplemental analysis does NOT change the frozen S5, the original 310-entry PR #55 joint result, source data, manuscript or official figures. It reads the branch's original literature catalog and independently tests the assumptions that produced four >5% same-temperature catalyst-switch reversals.

## A. Experimental cross-GHSV holdout

Existing PR #55 relies on an *unverified*, one-point-calibrated first-order conversion surrogate:

    X(m) = Xeq * (1 - (1 - X0 / Xeq)^m)
    STY(m) = STY0 * X(m)/(X0*m)

Here m is catalyst inventory relative to a measured anchor. When catalyst preparation, temperature, pressure, gas composition and mass-normalized GHSV units are truly the same, a measured GHSV change may act as an inverse-inventory holdout, m = GHSV_ref / GHSV_test.

Two peer-reviewed papers in the committed catalog offer comparable measured GHSV series:

- [Science Advances 2021, DOI 10.1126/sciadv.abi6012](https://doi.org/10.1126/sciadv.abi6012): four InNi3C0.5 supported catalysts (m-ZrO2, t-ZrO2, a-ZrO2, SiO2), 300 C, 40 bar, H2/CO2=3, at 12,000 vs 24,000 mL g_cat^-1 h^-1. Its paper-reported feed-equilibrium conversion is 11.6%, presented **separately** from the original PR #55 equilibrium solver. For m-ZrO2 the source-paper equilibrium predicts 9.45% X at 24k vs 8.5% measured. For SiO2 it predicts 1.33% vs 2.2% measured. STY source bases differ across the 12k/24k measurements, so only independently printed conversion and selectivity are held out.
- [ACS Catalysis 2025, DOI 10.1021/acscatal.5c05984](https://doi.org/10.1021/acscatal.5c05984): 5 wt% Re/TiO2 measured at multiple 10k–40k mass-normalized GHSV points and 100 bar, H2/CO2=4. **Its printed table varies catalyst pre-reduction temperature (250 vs 500 C), which is absent from the original catalog's 'catalyst_key'.** This audit groups Re conditions by table-row-preparation treatment: rows 5–9 use 250 C reduction, rows 10–14 use 500 C reduction. Never claim chemically identical catalyst state merely from 5wt% Re/TiO2 and reaction T.

Matched by source DOI, catalyst, prep, T, P, H2/CO2 and GHSV unit, these data provide **9 source cohorts and 12 experimentally held-out X(GHSV) values (7 Science Advances; 5 ACS)**, representing only **2 independent papers**, not 9 studies. The seven Science Advances tracks include four ZrO2/SiO2 support GHSV series and three Fe3O4 tracks at independently specified T/P/feed conditions. A reported high-GHSV Fe3O4 point around 115,500 mL g_cat^-1 h^-1 is rounded as 116 NL/g/h in the compiled candidate catalog; the report treats the input as nominal mass-normalized GHSV, not a high-precision original reading. One lowest-GHSV anchor fixes each cohort's rate surrogate without fitting to the other GHSV observations. Any measured point exceeding the model's own equilibrium is labelled *model-domain conflict* rather than silently corrected.

Produces measured_ghsv_holdouts.csv and holdout_report.json, with measured selectivity drift and implied power-law exponent as diagnostics; fitting an exponent to just two points does not count as an independent validation.

## B. Structural stress of the 4 previously reported reversals

Conditional re-evaluation uses only the original 4 groups (28 candidate entries), and fully reoptimizes the unchanged MeOH TEA over catalyst m and purge p under the original three reference inlet limits (4.92%, 6.86%, 10.249%).

Ten unfrozen, NOT literature-calibrated scenarios:
- Baseline beta=1, fixed measured selectivity and no catalyst mass ceiling. The implementation must match all 28 original PR #55 cost optima at tolerance 2e-8 relative/2e-5 EUR/t absolute, and reproduce all 4 cross-inlet survivors.
- Generalized conversion X(m)=Xeq*[1-(1-X0/Xeq)^(m^beta)] with beta=0.5, 0.75 or 1.25; these are separate structural stress models, NOT source-fitted kinetic confidence intervals.
- Selectivity SMeOH(m)=clip(S0 + gamma*ln(m), .001, 1) with gamma=-0.05, +0.05 or -0.15. The source anchor at m=1 and the sum SMeOH+SCO+SCH4=1 are preserved. Gamma values are invented stress coefficients, **not** reaction kinetics. **When SMeOH changes, methanol STY must also change as STY0 × [X(m)/X0] × [SMeOH(m)/SMeOH0] / m; using X alone would violate the same model product-carbon balance.**
- Catalyst mass ceilings of 1x, 2x or 5x the original plant reference of 478.13 tonnes per module times six = 2,868.78 tonnes. These are hypothetical inventory sensitivity bounds, not certified reactor volume or pressure-drop limits.

Reports conditional_candidates.csv, conditional_group_verdicts.csv, conditional_stress_report.json. A source group lacking feasible states is marked 'unscored_due_to_candidate_infeasibility' rather than counted as an economic winner or a zero-regret group. Four survivor groups cannot estimate a general rate/prevalence of ranking reversals.

## C. Physical and source validation blockers

The existing methanol source process model assumes constant 1.5-bar loop pressure drop while pricing reactor modules via catalyst inventory. Changing installed catalyst mass therefore does NOT check actual gas velocity, Ergun pressure drop, bed porosity, pellet size, true density, real reactor volume, thermal gradients, or catalyst deactivation. A mass cap multiple is a *sensitivity screen*, never industrial feasibility proof. Independent reactor dimensions, feed/recycle flow, pellet size, porosity, fluid viscosity/density and heat-transfer limits are required.

The ACS pre-reduction variable must be included explicitly in future catalyst comparison identifiers; the prior four switching observations must not be promoted to frozen manuscript claims without examining whether the original ACS comparison mixes different preparation states.

## Reproduce

From repository root, with requirements.txt installed:

    python -m unittest discover -s analysis/field_loading_validation_2026_10_12 -p 'test_*.py' -v
    python analysis/field_loading_validation_2026_10_12/experimental_holdout.py
    python analysis/field_loading_validation_2026_10_12/conditional_stress.py

CI .github/workflows/field-loading-validation.yml uploads two independent artifacts. The original PR #55 optimizer, original CSV output, and manuscripts are unchanged. Keep PR #55 in draft pending genuine kinetic and source-author checks.
