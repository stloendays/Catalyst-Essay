# Methanol: catalyst-level comparison of the 81 groups (2026-10-19)

Rules: `RULES.md`, committed (97661e0) before the counting script was written. Strict-rule identities:
`material_key_strict.csv`, annotated without access to leaderboards or costs (`material_key_strict_NOTES.md`).

    python run_catalyst_level.py   # -> summary.json, groups_catalyst_level.csv, groups_catalyst_level_strict.csv,
                                   #    catalysts_temperature.csv  (a few seconds)

The script reproduces the point-level anchor (50/81, 42 above 5 %) with the frozen `aggregate` before counting.
Inlet non-reactive fraction ≤ 6.86 % (primary cost column `cost_recycled_opt_inlet`), laboratory leaderboard = STY.

## Ranking change between catalysts (main result)

| | groups with ≥ 2 catalysts | leader is another catalyst | 95 % CI (paper bootstrap) | cost gap > 5 % | > 10 % | papers |
|---|---:|---:|---:|---:|---:|---:|
| primary identity (author's sample) | 63 (46 papers) | **26 (41 %)** | 29–53 % | **19** (16 papers) | 13 | 21 |
| strict identity (synthesis-only variants merged) | 52 (43 papers) | 22 (42 %) | 28–55 % | 15 | 11 | 18 |
| primary, conversion raised to 0.95 X_eq with catalyst amount | 63 | 21 (33 %) | 22–46 % | 10 | 8 | 19 |
| strict, conversion raised | 52 | 18 (35 %) | 22–47 % | 9 | 7 | 16 |

The cost gap is the laboratory leader at its own cheapest operating point against the plant leader at its cheapest
point (median 9.6 % among the 26). Conversion limits of 0.90 and 0.99 X_eq and the two-sided variant give the same
counts as 0.95.

How the 50 point-level disagreements split (primary): 26 are a change of catalyst; 13 are groups where one catalyst
leads both leaderboards and only its operating point differs; 11 are groups with a single catalyst. Every
catalyst-level change is also a point-level disagreement. Total kept: 50/81 (42 above 5 %); with conversion raised
46/81 (36 above 5 %).

One sample was recorded under two names (Frei et al. 2019: "CP" in the Fig. 6 extended test is the 0.75 wt% Pd–In₂O₃ CP
catalyst); it is one catalyst under both rules, so that group has one catalyst.

## Operating point (reported separately)

Of 112 catalysts measured at two or more temperatures (43 groups, 21 papers), 82 have a plant-best temperature
different from their laboratory-best (highest-STY) temperature, in 36 groups and 19 papers; in 75 of the 82 the plant
temperature is lower (median 50 °C lower). Running these catalysts at the laboratory-best temperature costs more than 5 %
extra in 74 of the 82 (median 78 %). Strict identity: 74 of 102. Conversion raised: 83 of 112.

## Files

- `groups_catalyst_level.csv`, `groups_catalyst_level_strict.csv`: per group, leaders and cost gap.
- `catalysts_temperature.csv`: per catalyst with ≥ 2 temperatures, laboratory-best and plant-best temperature.
- `summary.json`: all counts, including the conversion-raised variants.
