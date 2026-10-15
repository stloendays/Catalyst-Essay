# Prospective hold-out test of the methanol field result: report (2026-10-15)

Pre-registration: `PREREGISTRATION.md` (commit 49862cd, 2026-10-13). Blind predictions: commit 1115eed, before any
plant-model output of the new batch. `check_order.py`: commit order OK. Deviations: `DEVIATIONS.md` (D1 resolved
before extraction, no trace in the included set; D2 transport of the si_figures pass only).

## Batch

- 40 papers published 2025-11-05 to 2026-10-13, taken in the saved OpenAlex rank order (`screening.csv`).
- Extraction: main, figures and si passes complete for all 40. The si_figures pass stopped at the pre-registered
  8 M token cap with 24 of 40 papers done (plot readings; they enter only the all-entries sensitivity).
- PDF check (section 7): 40 sampled printed values, 39 correct. The wrong one (10.1021/acs.iecr.6c02654, STY at
  240 °C) came from an SI merge that took SI Table S1 entry IV (Cu:Zr 10:90) for the 14:86 catalyst. The same
  mis-merge put entry IV selectivities into two other fields of that paper. All four values are corrected through
  `corrections.csv`; the uncorrected cohort gives identical verdicts.
- Regression gate: the frozen candidates reproduce S6 28/40 and S5 15/40 (maximum relative cost difference
  1.9 × 10⁻¹²).

## Result (printed values, corrected: 41 comparison groups, 22 papers, 322 entries)

| | Disagreements | Pre-registered interval | P1 | Rule accuracy | Chance | Rule − chance [95 % CI] | P2 | Verdict |
|---|---|---|---|---|---|---|---|---|
| **S6** (inlet limit, primary) | **22 / 41 (53.7 %)**, 20 > 5 %, 11 papers; CI 31.3–68.1 % | 54.1–82.8 % | fail | 28 / 41 (68.3 %) | 27.7 % | +40.6 pp [+22.8, +55.0] | pass | **fail (P1)** |
| S5 (no limit) | 10 / 41 (24.4 %), 3 > 5 %, 6 papers; CI 9.4–37.1 % | 15.2–57.1 % | pass | 31 / 41 (75.6 %) | 27.7 % | [+32.7, +63.5] pp | pass | pass |

Secondary (S6, reported with the verdict, not part of it):

- predictive interval for a batch of 22 papers drawn from the frozen set: 52.0–83.9 %; the observed 53.7 % lies inside it;
- blind predictions: the committed S6 rule (highest methanol selectivity) names the plant-cost leader in 28 of 41
  groups; the paper's own STY leaderboard does so in 19 (rule − STY +22.0 pp [−12.8, +44.7]);
- M1 borne out: groups whose STY leader is not the most selective entry disagree in 21 / 32 (65.6 %), against 1 / 9
  (11.1 %) when it is;
- M2 borne out: the plant-cost leader is more selective in 21 / 22 disagreements and makes less CO in 21 / 22
  (frozen 19 / 28 and 18 / 28); it has the higher single-pass conversion in 1 / 22;
- kinds: same catalyst at another temperature 11, another catalyst at the same temperature 5, another catalyst and
  temperature 5, same catalyst and temperature 1; median regret of the disagreements 54 %; 15 of the 22 are near-infeasible in the
  frozen sense (PR #69).

All-entries sensitivity (plot readings included, corrected): S6 47 / 78 (60.3 %), S5 23 / 78 (29.5 %); both pass
P1 and P2.

Files: `results.json`, `scored_groups.csv`, `new_candidates_costed.csv`, `blind_predictions.csv`,
`blind_rankings.csv`, `pdf_check_40.csv`, `corrections.csv`.
