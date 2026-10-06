# Paper leaderboards versus plant-cost leaderboards (CO2-to-methanol) — 2026-10-05, 40-paper set 2026-10-06

`run_literature_inversion.py` takes the literature-extraction Agent's output (`agent/extraction/out/records_normalized.csv`,
used as extracted) through the generalized methanol recycle-economics model and compares, within each paper, the
paper's own leaderboard with the plant-cost leaderboard.

- **Candidates:** 750 operating points from 35 of the 40 extracted papers have conversion, methanol selectivity, T, P,
  H2/CO2 and a productivity basis. They come from the main text, main-text figures and Supporting Information.
  The other five papers give no usable operating point:
  - Yang 2024: no methanol selectivity;
  - Ma 2019: no space velocity, and the "STY" is printed as a yield (%);
  - Richard 2017: ambient pressure not extracted;
  - Hengne 2018: no conversion;
  - Lam 2018: rates extrapolated to zero conversion.
- **Excluded entries:** an entry whose feed adds water or CO to CO2/H2 (for example the H2O co-feeding series of
  Jiang 2020, or a CO/(CO2+CO) ratio above zero) is not a candidate, because the plant model takes a dry CO2/H2
  make-up (`meoh_candidates.cofeed`).
- **Comparison groups:** entries of one paper at the same P, H2/CO2 and space velocity, i.e. the comparison the paper
  itself makes. 68 groups with at least two entries, 682 entries, 34 papers.
- **Paper leaderboard:** methanol STY per g catalyst.
  - It is the printed STY when every entry in the group prints it, otherwise it is derived from the space velocity.
  - The printed STY is not used when, within the group, printed STY / (F_CO2 X S) varies by more than a factor of 3.
    Three groups are affected, all of them papers whose printed rates contradict their own conversion and selectivity:
    - Sharma 2021 mixes per-g-Cu and per-g-catalyst rates (factor 54);
    - Martin 2016 (factor 14);
    - Rui 2017 prints a zero rate at non-zero conversion.

    These groups use the mass-GHSV STY.
  - For volumetric space velocity a bulk density of 1.0 g/mL is assumed, with 0.5 and 2.0 tested.
- **Plant leaderboard:** net production cost at the entry's own T, P and H2/CO2, with CO recycled (central RWGS
  rule) and each entry's cost-optimal purge.

## Agent self-check against the hand-built case

All 21 Gothe et al. (2025) Table 4 entries were taken from the Agent's extraction and run through the same code path.
They reproduce the frozen Table 4 costs to 2.3e-13 EUR/t, under both inert and recycled CO. The four canonical states
come out at 943.30, 961.51, 966.96 and 1258.17 EUR/t (`selfcheck_gothe_table4.csv`).

## Result

| Leaderboard / plant treatment | Groups with a different winner | Papers affected | Regret if the paper's winner is built (median of mismatched / max) | Pairwise orderings inverted |
|---|---|---|---|---|
| **STY, recycled CO, optimal purge (primary)** | **27 / 68 (40 %)** | **14 / 34** | **2.1 % / 182 %** | **696/6006 (12 %)** |
| STY, recycled CO, 2 % purge | 29 / 68 (43 %) | 16 / 34 | 5.6 % / 557 % | 633/6006 (11 %) |
| STY, inert CO, optimal purge | 35 / 68 (51 %) | 27 / 34 | 7.1 % / 98 % | 1178/6006 (20 %) |
| single-pass yield X·S_MeOH | 26 / 68 (38 %) | 14 / 34 | 2.0 % / 182 % | 678/6006 (11 %) |
| conversion X | 12 / 68 (18 %) | 9 / 34 | 4.5 % / 96 % | 504/6006 (8 %) |
| **methanol selectivity S_MeOH** | **51 / 68 (75 %)** | **30 / 34** | **18.4 % / 4360 %** | **3228/6006 (54 %)** |

Robustness of the primary result:
- Assumed density 0.5 or 2.0 g/mL: unchanged, 27 / 68 groups.
- Printed values only, no plot readings: 14 / 41 groups, 8 / 29 papers.
- Only entries whose reported selectivities to MeOH, CO and CH4 sum to at least 95 %: 16 / 46 groups, 9 / 27 papers.
- Without Bansode 2013, the paper contributing the most groups: 20 / 60 groups (33 %), 13 / 33 papers; regret median
  1.5 %, max 9.0 %.

Weighting each paper equally, 35 % of a paper's comparison groups pick a different winner.

Regrets above 10 % all come from Bansode 2013. There, the highest-STY entries of a group are low-temperature points
with 1–3 % single-pass conversion, and building them needs a very large recycle. Outside Bansode the largest regret is
9.0 % (Wang 2015, Cu/SiO2: the 380 °C entry against the 390 °C entry at 6 L g-1 h-1).

Mean top-3 overlap in the 46 groups of four or more entries: 2.33 of 3 (primary), 0.83 of 3 for selectivity leaderboards.

### Development history

| Set | Candidates | Groups | STY winner differs | Selectivity winner differs |
|---|---|---|---|---|
| 20 papers, main pass only (2026-10-05, PR #16) | – | 22 | 4 / 22 | 14 / 22 |
| 20 papers after the recall passes (PR #18) | 443 from 19 | 36 | 16 / 36 (44 %), 7 / 19 papers | 27 / 36 (75 %) |
| 40 papers (Shi 2020 dropped; co-feed exclusion; printed-STY consistency rule) | 750 from 35 | 68 | 27 / 68 (40 %), 14 / 34 papers | 51 / 68 (75 %) |

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

The share of groups whose winner changes is 40 % under the first and 51 % under the second. How much the wrong choice
costs depends on the treatment.

The analysis reads the current extraction output; rerun it after the extraction is extended (about 33 min for 750
candidates on one core).
