# Pre-registration: revealed-preference validation of the methanol plant model (2026-10-13)

Committed before any outcome of the tests below was computed. The only files produced at this point are the
composition-only subsets (`families.py`, `make_subsets.py`, `subsets_printed.csv`, `subsets_extended.csv`,
`subsets_summary.json`); they read the catalyst name, DOI and group of the frozen candidate tables and no STY,
conversion, selectivity or cost. Any change to this file after the first outcome commit is a deviation and is listed
under "Deviations" in `README.md`.

What was already known when this was written: the frozen field counts (S5 15/40, S6 28/40; extended S5 35/83,
S6 54/82), the inlet-definition counts (CH4+N2 at 6.86 %: 18/40) and the aggregate mechanism tables of
`analysis/meoh_constraint_boundary_2026_10_12/` and PR #79. None of them reports which catalyst family leads a group,
family-level costs, or anything about Cu/ZnO/Al2O3.

## Question

Industry has used Cu/ZnO/Al2O3 for methanol for > 50 years, also for CO2-rich feeds (CRI George Olah plant), although
many papers report catalysts with a higher space-time yield (STY) or selectivity (In2O3/ZrO2, Pd-In, ZnZrOx,
Cu/ZrO2, ...). Does the latest plant model, fed only the laboratory data of the field result, reproduce this revealed
industrial preference better than the laboratory STY ranking does?

## Inputs (frozen, read only)

- Cohorts. **Primary: printed** = `analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv`, groups with
  >= 2 entries: 40 groups, 310 entries, 28 papers (the frozen field result, tag `freeze/field-2026-10-12`).
  **Secondary (clearly labelled): extended** = `literature_candidates_all_entries.csv` (plot readings included):
  83 groups, 909 entries, 44 papers. The extended cohort is used because the printed cohort holds only 3 groups
  (2 papers) with a Cu/ZnO/Al2O3-type reference and no ZnO-ZrO2 entry. It adds no H1 group (same 3) and one H1-broad
  group; it adds the ZnZrOx family (2 papers) to H2/H3.
- Scenarios (cost columns; the frozen STY column `STY` is the laboratory metric in every scenario):
  - **S6 (primary)**: inlet-limited loop, (CH4 + CO + N2) / reactor inlet <= 6.8625 % (`G.NONREACTIVE_MAX`), frozen
    column `cost_recycled_opt_inlet`.
  - **S5 (reported alongside)**: no inlet limit, frozen column `cost_recycled_opt`.
  - **S6-TI (definition sensitivity)**: the same limit counting only the true inerts CH4 + N2, recomputed with the
    code of `analysis/meoh_inlet_definition_2026_10_12/run_inlet_definition.py` (`sweep`, `pick`) after that code
    reproduces the frozen columns to 1e-6 relative for the cohort.
- Scoring: `meoh_candidates.aggregate(frame, cost_col, up_col='STY')` unchanged (an entry with no finite cost leaves its
  group; a group with < 2 finite entries is not scored).
- Before any new run, `test_anchors.py` must reproduce: printed S5 15/40, S6 28/40, S6-TI 18/40; extended S5 35/83,
  S6 54/82. If any anchor fails, nothing is reported.

## Families and scale classes (fixed in `families.py`)

Families by catalyst name (precedence: blank control > In-containing > Pd-containing > Cu+Zn+Al > other Cu > ZnO-ZrO2 >
Zn-CdZrOx > Re). Bare supports / single-oxide controls (ZrO2 and its phases, SiO2, TiO2, ZnO, ZnTiO3, Fe3O4, NiO) are
"blank" and excluded from H2/H3 and from the "other family" side of H1. Cu-based = CuZnAl + other Cu.

| Cohort | CuZnAl | other Cu | In2O3 | Pd | ZnZrOx | Zn-CdZrOx | Re | blank |
|---|---|---|---|---|---|---|---|---|
| printed (entries / papers) | 23 / 5 | 82 / 3 | 114 / 14 | 62 / 7 | 0 | 0 | 13 / 1 | 16 |
| extended (entries / papers) | 54 / 5 | 176 / 8 | 415 / 21 | 148 / 10 | 48 / 2 | 35 / 1 | 13 / 1 | 20 |

Scale classes (H3), primary evidence in `families.SCALE_EVIDENCE`:
- **scaled**: Cu/ZnO/Al2O3-type (commercial methanol catalyst; CRI George Olah CO2-to-methanol plant, JM licence and
  Cu/ZnO-based catalyst), Cu/ZnO/ZrO2(-Al2O3-SiO2) (Mitsui ~100 t/a pilot 2009-10; no entry in either cohort), ZnO-ZrO2
  solid solution (DICP 1,000 t/a demonstration, Lanzhou 2020).
- **lab_only**: every other non-blank family.
- **H3-alt (sensitivity)**: In2O3/ZrO2 without a further metal also counted as scaled (announced demonstration, no
  published pilot data).
- printed: 23 scaled entries (5 papers) vs 271 lab-only (25 papers); extended: 102 (7) vs 787 (40).

## Hypotheses, statistics, pass rules

All bootstraps: paper-cluster (papers resampled with replacement; every entry / group of a drawn paper enters),
10,000 resamples, seed 20261013, percentile 95 % interval. A resample in which a statistic is undefined (a needed
family or class absent) counts as a failure: the statistic is set to -inf for the lower bound. No multiplicity
correction; each hypothesis is judged on its own. **The pre-registered verdict is the printed cohort under S6.** S5,
S6-TI and the extended cohort are reported with the same rules and do not override it.

### H1: within-group leader, Cu/ZnO/Al2O3 reference

- Subset: groups (frozen grouping, all entries kept, blanks included in the leaderboards) that contain >= 1
  Cu/ZnO/Al2O3-type entry and >= 1 non-blank entry of another family. Printed and extended: 3 groups, 2 papers
  (Martin et al. 2016 `10.1002/anie.201600943`; `10.1126/sciadv.abi6012` at 12 and 30 NL/g/h).
- For each group: c = 1 if the plant-cost leader (`economic_winner`) is a CuZnAl entry; s = 1 if the STY leader
  (`upstream_winner`) is a CuZnAl entry.
- Statistic: D = mean(c) - mean(s) (paired). Interval: paper-cluster bootstrap of D.
- **Pass**: D > 0 and the lower 95 % bound of D > 0. (With 2 papers, this requires D > 0 in each paper.)
- Secondary H1-broad: the same with any Cu-based reference (CuZnAl or other Cu) against a non-Cu, non-blank family
  (printed 3 groups / 2 papers; extended 4 / 3, adding `10.1021/acsami.1c05586`).

### H2: family ranking, Cu-based first by plant cost but not by STY

- Entries: non-blank entries of the scored groups with a finite cost in the scenario.
- Families ranked: Cu-based, In2O3, Pd, ZnZrOx, Zn-CdZrOx, Re (those present in the cohort).
- Statistics (across papers; plant cost is the common USD/t scale, STY the field's common record metric):
  - G_cost = ln( min cost over all non-Cu entries / min cost over Cu-based entries ); > 0 means the cheapest
    Cu-based entry is cheaper than the cheapest entry of every other family.
  - G_STY = ln( max STY over Cu-based entries / max STY over non-Cu entries ); > 0 means a Cu-based entry holds the
    highest STY.
- **Pass**: lower 95 % bound of G_cost > 0 AND point G_STY < 0.
- Secondary H2-CZA: the same with Cu/ZnO/Al2O3-type alone as the focal family against every other non-blank family
  (other Cu included among the competitors).
- Secondary H2-regret (the within-group version suggested in the brief): per entry, cost regret = cost / group-min
  cost - 1 and STY shortfall = group-max STY / STY - 1 (group = frozen group, blanks kept in the group minimum and
  maximum, excluded from the family medians); family score = median over its entries. Pass: Cu-based has the lowest
  median cost regret and not the lowest median STY shortfall. Reported with the bootstrap share of resamples in which
  Cu-based is first by each score.

### H3: scaled vs lab-only catalysts, separation by plant cost vs by STY

- Entries: as H2. Classes: scaled vs lab_only (primary classification).
- AUC_cost = P(cost of a random scaled entry < cost of a random lab-only entry), ties 1/2.
  AUC_STY = P(STY of a random scaled entry > STY of a random lab-only entry), ties 1/2.
- Statistic: dAUC = AUC_cost - AUC_STY. Interval: paper-cluster bootstrap of dAUC (and of each AUC).
- **Pass**: lower 95 % bound of dAUC > 0.
- Secondary H3-catalyst: one point per (paper, catalyst) – its minimum cost and its maximum STY – so temperature
  series do not weight the AUC. Secondary H3-alt: the H3-alt classification.

## Outputs promised

`results.json` (every statistic, interval and pass flag per cohort x scenario x test), `results_tables.md`,
`h1_groups.csv`, `h2_families.csv`, `h3_auc.csv`, `README.md` (numbers first; failures reported as failures; no
post-hoc change of subsets, statistics or pass rules).
