# Gold-standard sample: effect of the 2026-10-12 review on the frozen methanol result

## Status of the 100-value sample

The 100 extracted values of `analysis/verify_2026_10_08/gold_standard_sample.xlsx` (10 papers, seed 20261008) were
checked against the papers and their Supporting Information: an AI-assisted first pass, then the author's own final
review of all 100 fields, confirmed on 2026-10-12 (record, evidence table and checksums in
`analysis/verify_2026_10_08/gold_standard_human_review_2026_10_12/`). The result concerns this sample; it does not
establish that the whole extracted database is correct.

| Outcome | Values |
|---|---|
| printed in the paper, or equal after a standard unit conversion | 91 |
| correct, H₂/CO₂ derived from a printed feed composition | 6 |
| value matches; the locator needed correcting (Frei 2019, 9.7 %) | 1 |
| "<0.1 %" upper bound; the qualifier must be kept (Ota 2012, PdZnAl CH₄) | 1 |
| value matches; the original metric name must be stated (Ota 2012, MeOH rate) | 1 |

No extracted value contradicts the paper. All 100 values belong to scored groups of the frozen primary (16 of the 40
groups).

## Effect on S5 and S6 (`below_limit_bounds.py`)

Locators and metric names are not model inputs. The six derived H₂/CO₂ ratios are the model inputs as printed
compositions imply, and the inert share of those feeds is carried (y_CO₂ 0.24 for Dang 2020 with 3 % N₂, 0.22 for Chen
2019 with 12 % N₂, 0.20 for the cctc study with 20 % N₂). The qualifier matters because the frozen closure sets a "<"
selectivity to zero. The script sets every "<"-qualified CO or CH₄ selectivity of the scored cohort to its printed
bound (14 candidates in 5 papers, Ota 2012 included), re-costs those candidates with the frozen code and rescores the
40 groups; unchanged candidates reproduce their frozen costs.

| | frozen | upper bound |
|---|---|---|
| S5: different winner | 15 / 40 (7 above 5 %) | 15 / 40 (7 above 5 %) |
| S5: other catalyst / other temperature | 10 / 32, 5 / 22 | 10 / 32, 5 / 22 |
| S6 (inlet ≤ 6.86 %) | 28 / 40 (22 above 5 %) | 28 / 40 (22 above 5 %) |

Costs of the 14 candidates change by at most 1.5 % (S5) and 2.6 % (S6); no group changes verdict. In the Re/TiO₂
group (Gothe 2025, 100 bar) the plant-cost leader moves from Table 4 row 3 to row 4 under S5 and the group stays a
disagreement (regret 1.75 % → 1.23 %); in Ota 2012 PdMgGa stays the plant-cost leader (S5) and PdZnAl under S6.
Outputs: `below_limit_candidates.csv`, `below_limit_groups.csv`, `below_limit_summary.json`.
