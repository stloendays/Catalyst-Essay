# Gold-standard sample: 2026-10-12 review and its effect on the frozen methanol result

## Status of the 100-value sample

The 100 extracted values of `analysis/verify_2026_10_08/gold_standard_sample.xlsx` (10 papers, seed 20261008) were
re-checked against the papers and their Supporting Information in an AI-assisted review (ChatGPT, source files from the
Google Drive folder `Catalyst-Essay_SI_freeze-2026-10-12/原文与SI`). The author accepted the result on 2026-10-12 as the
current working basis for data verification. It is **not** a formal, independently signed human gold standard, and it
does not establish that the whole extracted database is correct.

| Outcome | Values |
|---|---|
| printed in the paper, or equal after a standard unit conversion | 91 |
| correct, derived from the paper's experimental conditions | 6 |
| value matches; the locator needs correcting | 1 |
| "<0.1 %" upper bound; the qualifier must be kept | 1 |
| value matches; the original metric name must be stated | 1 |

No extracted value conflicts with the paper. Corrections named in the review: the locator of Frei 2019's 9.7 %, the
H₂/CO₂ ratio of Dang 2020 (3.0417, derived from the feed composition), the "<0.1 %" CH₄ selectivity of PdZnAl in Ota
2012. All 100 values belong to scored groups of the frozen primary (16 of the 40 groups).

## Effect on S5 and S6 (`below_limit_bounds.py`)

Locator, metric-name and derived-value corrections leave every model input unchanged. The qualifier matters because the
frozen closure sets a "<" selectivity to zero. The script sets every "<"-qualified CO or CH₄ selectivity of the scored
cohort to its printed bound (14 candidates in 5 papers, Ota 2012 included), re-costs those candidates with the frozen
code and rescores the 40 groups; unchanged candidates reproduce their frozen costs.

| | frozen | upper bound |
|---|---|---|
| S5: different winner | 15 / 40 (7 above 5 %) | 15 / 40 (7 above 5 %) |
| S5: other catalyst / other temperature | 10 / 32, 5 / 22 | 10 / 32, 5 / 22 |
| S6 (inlet ≤ 6.86 %) | 28 / 40 (22 above 5 %) | 28 / 40 (22 above 5 %) |

Costs of the 14 candidates change by at most 1.5 % (S5) and 2.6 % (S6); no group changes verdict. In the Re/TiO₂
group (Gothe 2025, 100 bar) the plant-cost leader moves from Table 4 row 3 to row 4 under S5 and the group stays a
disagreement (regret 1.75 % → 1.23 %); in Ota 2012 PdMgGa stays the plant-cost leader (S5) and PdZnAl under S6.
Outputs: `below_limit_candidates.csv`, `below_limit_groups.csv`, `below_limit_summary.json`.
