# Conversion raised with catalyst inventory, under the S6 reactor-inlet limit

`run_s6_conversion.py` repeats the frozen conversion sensitivity (`analysis/meoh_literature_inversion_2026_10_05/
run_conversion_sensitivity.py`: X(m) = X_eq [1 − (1 − X0/X_eq)^m], up to 0.90 / 0.95 / 0.99 X_eq, fixed selectivity) with
every purge level also required to keep the reactor-inlet non-H₂/CO₂ fraction within the reference loop's 6.86%, as
`cost_recycled_opt_inlet` does for the laboratory point. Frozen code otherwise; the laboratory cost of every entry
reproduces `cost_recycled_opt_inlet` (asserted). Run on GitHub Actions (`.github/workflows/s6-conversion-raised.yml`,
run 38252412327); outputs downloaded from its artifact.

Printed-value cohort, 40 comparisons:

| | Different leader | >5% (papers) | Other catalyst, same temperature, >5% (papers) | Other catalyst and temperature, >5% | Other temperature, >5% |
|---|---|---|---|---|---|
| S5, laboratory conversion (frozen) | 15 | 7 (2) | 0 | 4 (1) | 3 |
| S5, conversion raised (frozen) | 14 | 3 | 0 | 0 | 3 |
| S6, laboratory conversion (frozen) | 28 | 22 (18) | 8 (8) | 3 (2) | 11 (9) |
| **S6, conversion raised (0.95 X_eq)** | **23** | **16 (12)** | **5 (4)** | **2 (2)** | **9 (8)** |

Conversion up to 0.90 or 0.99 X_eq and the two-sided variant give the same counts. Without the high-pressure Cu/Al₂O₃
study (10.1039/c2cy20604h): 19 of 32, 12 above 5% across 11 papers. The five same-temperature other-catalyst groups
above 5% come from Hou 2024 (bare In₂O₃), Gothe 2025 (per gram of catalyst; per gram of Re it is a temperature choice),
Bansode 2013 and two groups of one Science Advances 2021 paper. Some regrets are very large (up to 32-fold for one
Bansode group) where the paper leader barely meets the inlet limit; counts above 5% do not depend on them.

All entries (82 comparisons): 54 → 53 with conversion raised, 46 → 44 above 5%.

Unfrozen sensitivity; no frozen value or manuscript number changes.
