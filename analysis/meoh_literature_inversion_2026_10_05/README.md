# Paper leaderboards versus plant-cost leaderboards (CO2-to-methanol) — 2026-10-05

`run_literature_inversion.py` takes the literature-extraction Agent's output (`agent/extraction/out/records_normalized.csv`,
used as extracted) through the generalized methanol recycle-economics model and compares, within each paper, the
paper's own leaderboard with the plant-cost leaderboard.

- **Candidates:** 192 operating points from 17 papers have conversion, methanol selectivity, T, P, H2/CO2 and a
  productivity basis.
- **Comparison groups:** entries of one paper at the same P, H2/CO2 and space velocity, i.e. the comparison the paper
  itself makes. 22 groups with at least two entries, 169 entries, 15 papers.
- **Paper leaderboard:** methanol STY per g catalyst. It is the printed STY when every entry in the group prints it,
  otherwise it is derived from the space velocity. For volumetric space velocity a bulk density of 1.0 g/mL is
  assumed, with 0.5 and 2.0 tested.
- **Plant leaderboard:** net production cost at the entry's own T, P and H2/CO2, with CO recycled (central RWGS
  rule) and each entry's cost-optimal purge.

## Agent self-check against the hand-built case

All 21 Gothe et al. (2025) Table 4 entries were taken from the Agent's extraction and run through the same code path.
They reproduce the frozen Table 4 costs to 2.3e-13 EUR/t, under both inert and recycled CO. The four canonical states
come out at 943.30, 961.51, 966.96 and 1258.17 EUR/t (`selfcheck_gothe_table4.csv`).

## Result

| Leaderboard / plant treatment | Groups with a different winner | Papers affected | Regret if the paper's winner is built (median / max) | Pairwise orderings inverted |
|---|---|---|---|---|
| **STY, recycled CO, optimal purge (primary)** | **4 / 22 (18 %)** | **4 / 15** | **1.2 % / 1.8 %** | **133 / 991 (13 %)** |
| STY, recycled CO, 2 % purge | 5 / 22 | 4 | 5.6 % / 13.0 % | 140 / 991 |
| STY, inert CO, optimal purge | 11 / 22 | 8 | 16.6 % / 306 % | 221 / 991 |
| single-pass yield X·S_MeOH | 4 / 22 | 4 | 1.2 % / 1.8 % | 124 / 991 |
| conversion X | 4 / 22 | 3 | 1.4 % / 37 % | 76 / 991 |
| **methanol selectivity S_MeOH** | **14 / 22 (64 %)** | **11 / 15** | **53 % / 1,098 %** | **546 / 991 (55 %)** |

Robustness of the primary result:
- Assumed density 0.5 g/mL: 5 groups. 2.0 g/mL: 3 groups.
- Printed values only, no plot readings: 2 / 13 groups.
- Only entries whose reported selectivities to MeOH, CO and CH4 sum to at least 95 %: 2 / 14 groups.

Mean top-3 overlap in groups of four or more entries: 2.56 of 3 (primary), 1.5 of 3 for selectivity leaderboards.

## What decides the plant ranking

- **CO is a recycled intermediate, not a loss.** With CO recycled, a catalyst's CO selectivity costs little.
  - Bansode 2013, 36 MPa: the plant-cost winner is the 533 K point, at 5.5 % methanol selectivity and 20 % conversion.
  - Wang 2017, CZ series: CZ-350 (41 % selectivity, 4.6 % conversion) beats CZ-450 (54 %, 4.2 %).
- **Methane is a loss.** Methane leaves only through the purge, so methane selectivity separates the costs. In
  Gothe 2025 the highest-STY entry (5 wt% Re, 200 °C) ranks third because its 3 % CH4 costs more than the ≤ 1 % CH4 of
  the 1 wt% Re entries.
- **Ranking by selectivity alone is the costly mistake.** The most selective entry often has very low conversion, so
  it needs a much larger catalyst inventory and recycle.

The analysis reads the current extraction output; rerun it after the extraction is extended.
