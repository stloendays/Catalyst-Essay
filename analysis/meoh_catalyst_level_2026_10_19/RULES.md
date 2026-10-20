# Catalyst-level comparison of the methanol groups: rules fixed before counting (2026-10-19)

Supervisor direction (2026-10-19): each catalyst is first placed at the best operating point it was measured at, and
catalysts are then compared with catalysts. A group whose catalysts are all one catalyst (only the temperature differs)
does not count as a ranking change. What counts as a different catalyst is fixed here, before any count is made, and
goes into Methods.

This file is committed before the counting script exists. The counts are made by `run_catalyst_level.py` on the frozen
81-group candidate table (`analysis/meoh_field_pooled_2026_10_15/pooled_candidates.csv`, inlet limit 6.86 %, cost
column `cost_recycled_opt_inlet`, upstream column `STY`). No rule below is changed after counting.

## 1. Catalyst identity

Comparison groups are unchanged: one paper, one pressure, H₂/CO₂ ratio and space velocity. Within a group:

**Primary rule.** Two entries are different catalysts when the authors report them as different samples that differ
in at least one of

1. composition: the elements present and their ratios, promoters and dopants included;
2. loading of the active component;
3. support: its identity or crystal phase;
4. synthesis: preparation route, precursor or precipitant, calcination or carburization temperature, morphology.

Entries of one sample that differ only in reaction temperature, time on stream, in-situ activation before reaction or
reactor operating mode are the same catalyst at different operating points. In the extracted records the author's
sample name (`catalyst_key`: the name before the locator bracket, whitespace and dash variants ignored) identifies the
sample; locator text such as "after 200 h" or a temperature is not part of the name.

**Strict rule (sensitivity).** Only items 1–3 distinguish catalysts. Samples of one composition, loading and support
that differ only in synthesis (item 4) are one catalyst; that catalyst's best point is taken over all its samples and
temperatures. The synthesis-only sets are identified from the sample names and papers, without reference to any
leaderboard or cost (`material_key_strict.csv`).

## 2. Catalyst-level leaders

- Laboratory leader: for each catalyst, its highest space-time yield over its operating points; the laboratory leader
  is the catalyst with the highest of these.
- Plant leader: for each catalyst, its lowest modeled plant cost over its operating points (inlet non-reactive
  fraction ≤ 6.86 %, as in the primary result); the plant leader is the catalyst with the lowest of these.
- Ranking change: the two leaders are different catalysts. Denominator: groups with at least two catalysts.
- Cost gap: the laboratory leader's own best cost over the plant leader's best cost, minus one. Reported with the
  numbers above 5 % and 10 %, papers, and a paper-cluster bootstrap (10,000 resamples, seed 20261006).

## 3. Operating-point result (reported separately)

For every catalyst measured at two or more temperatures, whether its laboratory-best temperature (highest space-time
yield) is its plant-best temperature (lowest cost). Reported as catalysts and groups, with the cost gap of running the
catalyst at its laboratory-best temperature. Sentence intended for the paper: laboratories report the temperature of
highest yield; the plant often chooses another.

## 4. Totals kept

The point-level count (any operating point of any catalyst; 50/81, 42 above 5 %) is kept as the total.

## 5. Conversion raised with catalyst amount

The same catalyst-level rule is applied to the existing sensitivity in which single-pass conversion rises toward
equilibrium with catalyst amount (`analysis/meoh_field_pooled_2026_10_15/robustness/conversion_s6`), on the same 81
groups.
