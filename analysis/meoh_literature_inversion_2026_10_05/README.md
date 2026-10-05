# Paper leaderboards versus plant-cost leaderboards (CO2-to-methanol) — 2026-10-05

`run_literature_inversion.py` takes the literature-extraction Agent's output (`agent/extraction/out/records_normalized.csv`,
used as extracted) through the generalized methanol recycle-economics model and compares, within each paper, the
paper's own leaderboard with the plant-cost leaderboard.

- **Candidates:** 443 operating points from 19 papers have conversion, methanol selectivity, T, P, H2/CO2 and a
  productivity basis. They come from the main text, main-text figures and Supporting Information, after the
  extraction's recall passes.
- **Comparison groups:** entries of one paper at the same P, H2/CO2 and space velocity, i.e. the comparison the paper
  itself makes. 36 groups with at least two entries, 413 entries, 19 papers.
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

| Leaderboard / plant treatment | Groups with a different winner | Papers affected | Regret if the paper's winner is built (median of mismatched / max) | Pairwise orderings inverted |
|---|---|---|---|---|
| **STY, recycled CO, optimal purge (primary)** | **16 / 36 (44 %)** | **7 / 19** | **2.9 % / 182 %** | **492/3801 (13 %)** |
| STY, recycled CO, 2 % purge | 17 / 36 (47 %) | 8 / 19 | 7.1 % / 557 % | 419/3801 (11 %) |
| STY, inert CO, optimal purge | 19 / 36 (53 %) | 14 / 19 | 5.6 % / 98 % | 657/3801 (17 %) |
| single-pass yield X·S_MeOH | 15 / 36 (42 %) | 7 / 19 | 3.5 % / 182 % | 478/3801 (13 %) |
| conversion X | 6 / 36 (17 %) | 4 / 19 | 6.0 % / 37 % | 339/3801 (9 %) |
| **methanol selectivity S_MeOH** | **27 / 36 (75 %)** | **16 / 19** | **68.8 % / 4360 %** | **1885/3801 (50 %)** |

Robustness of the primary result:
- Assumed density 0.5 or 2.0 g/mL: unchanged, 16 / 36 groups.
- Printed values only, no plot readings: 10 / 26 groups, 4 / 16 papers.
- Only entries whose reported selectivities to MeOH, CO and CH4 sum to at least 95 %: 13 / 30 groups, 6 / 16 papers.
- Without Bansode 2013, the paper contributing the most groups: 9 / 28 groups (32 %), 6 / 18 papers; regret median
  1.2 %, max 3.9 %.

Weighting each paper equally, 33 % of a paper's comparison groups pick a different winner.

The regrets above 4 % all come from Bansode 2013. There, the highest-STY entries of a group are low-temperature points
with 1–3 % single-pass conversion, and building them needs a very large recycle.

Mean top-3 overlap in the 29 groups of four or more entries: 2.24 of 3 (primary), 0.93 of 3 for selectivity leaderboards.

## What decides the plant ranking

- **CO is a recycled intermediate, not a loss.** With CO recycled, a catalyst's CO selectivity costs little.
  - Bansode 2013, 10 MPa: the highest-STY entry (Cu–Ba/Al2O3, 473 K: 62 % methanol selectivity, 2.8 % conversion)
    costs 1,170 EUR/t; the plant-cost winner (Cu–K/Al2O3, 553 K: 0.9 % selectivity, 20.7 % conversion) costs 1,002.
  - Wang 2017, CZ series: CZ-350 (41 % selectivity, 4.6 % conversion) beats CZ-450 (54 %, 4.2 %).
- **Methane is a loss.** Methane leaves only through the purge, so methane selectivity separates the costs. In
  Gothe 2025 the highest-STY entry (5 wt% Re, 200 °C) ranks third because its 3 % CH4 costs more than the ≤ 1 % CH4 of
  the 1 wt% Re entries.
- **Ranking by selectivity alone is the costly mistake.** The most selective entry often has very low conversion, so
  it needs a much larger catalyst inventory and recycle.

The two CO treatments bound the plant ranking:
- Recycled CO assumes the catalyst converts recycled CO as far as reverse-water-gas-shift equilibrium requires.
- Inert CO assumes it never converts it.

The share of groups whose winner changes is 44 % under the first and 53 % under the second. How much the wrong choice
costs depends on the treatment.

The analysis reads the current extraction output; rerun it after the extraction is extended.
