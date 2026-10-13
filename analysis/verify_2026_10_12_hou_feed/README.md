# Hou et al. 2024: laboratory feed of the bare In₂O₃ controls (extraction correction)

Source: Hou et al., *J. Environ. Sci.* **140**, 91–102 (2024), doi:10.1016/j.jes.2023.05.010. Section 1.4 of the article
tests both Au/In₂O₃ and bare In₂O₃ at H₂:CO₂:Ar = 4:1:1 (60 mL min⁻¹, 200 mg). SI Table S5 abbreviates the feed as
H₂/CO₂ = 4. Found by the cloud review (draft PR #63, publisher PDF and SI hashes checked there).

## Correction ledger

| Rows | Field | Recorded | Correct | Cohort |
|---|---|---|---|---|
| SI Table S5, In₂O₃-HM / -NP / -NS (3) | inert fraction (laboratory y_CO₂) | 0 (0.20) | 1/6 (0.1667) | printed and all entries |
| SI Fig. S4a,b, In₂O₃-HM / -NP / -NS at 200–275 °C (12) | inert fraction (laboratory y_CO₂) | 0 (0.20) | 1/6 (0.1667) | all entries only (plot-read) |
| Fig. 6a,b, Au/In₂O₃ (15) | inert species | N₂ | Ar | both; the model uses only the fraction, which was right |

Root cause: the extraction took the feed from SI Table S5 ("H₂: CO₂ = 4") instead of the Methods, which state the Ar
diluent for both catalyst series. One paper, one mechanism.

## Effect

- Frozen S5 and S6 costs and verdicts: none. The laboratory CO₂ fraction enters the methanol chain only through the
  space-velocity STY (all six Hou entries print their STY) and the laboratory equilibrium conversion of the
  conversion-raised analysis.
- Conversion-raised analysis (`hou_feed_check.py`, frozen code, corrected rows recomputed, every other row frozen):
  laboratory equilibrium conversion 0.2763 → 0.2723; the three printed candidates' costs change by ≤0.10%
  (926.46 → 926.62, 931.89 → 932.41, 930.42 → 931.37 EUR t⁻¹). All 10 scenarios (printed and all entries, laboratory
  conversion and conversion up to 0.90 / 0.95 / 0.99 X_eq and two-sided) keep their counts: printed 15/40 (>5%: 7) at
  laboratory conversion and 14/40 (>5%: 3; other catalyst 5, none >5%) with conversion raised. `hou_feed_check.json`.

The frozen input tables are not edited; the correction is applied in the next version of the extracted database.

    python analysis/verify_2026_10_12_hou_feed/hou_feed_check.py
