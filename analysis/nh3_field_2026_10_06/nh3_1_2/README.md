# Ammonia field result on NH3-FINAL-1.2 (2026-10-13)

The 30-paper field chain (`../run_field_chain.py`) and its printed-values primary (`../run_printed_primary.py`) rerun on
NH3-FINAL-1.2: run `nh3_final_1_2_20261013` (14,510 process states, F_CAL 74,351.6, Fe benchmark 11.52 USD/t). Same
extraction, mapping, primary screen, groups, deduplication, leaderboards, variants and bootstrap seed as the 1.1 files
in the parent folder; only the model changes. Same file names as the parent folder.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (1.2 harness with its cache/)
    python analysis/nh3_field_2026_10_06/run_field_chain.py          # ~3 min on one core
    python analysis/nh3_field_2026_10_06/run_printed_primary.py
    python analysis/verify_2026_10_08/nh3_printed.py                  # -> analysis/verify_2026_10_08/nh3_1_2/

What the model change does to the mapping: in 1.2 the model's NH₃ formation free energy is the Gillespie–Beattie value,
so the approach-to-equilibrium ratio y_eq,model / y_eq,exp of the 1.1 mapping is 1 to rounding and the laboratory NH₃
fraction enters unscaled; the laboratory gas then enters the microkinetics with the Newton–Cooper fugacity
coefficients, like every plant state. The near-equilibrium screen keeps its 1.1 definition (y_out ≥ 0.9 y_eq,exp,
ideal-gas Gillespie–Beattie), as in the supported chain. Each catalyst's E_eff is solved again on the 1.2 volcano at its
laboratory condition and costed on the 14,510-state library.

Self-check: the Humphreys chain through this script's mapping (83 catalysts, 548 values) equals
`run_supported_chain.main()` on the 1.2 harness, maximum relative difference 0. It also equals the committed
`analysis/nh3_supported_2026_10_06/nh3_1_2/supported_candidates.csv` of branch `port/nh3-1-2-supported` to the
12 significant figures of `selfcheck_supported.csv` (maximum relative difference 4.2 × 10⁻¹²). Once that file is on
the branch, the script compares against it directly.

## Printed values only (the frozen primary; Fig. 2c, main text and Supplementary Note 4)

| Quantity | NH3-FINAL-1.1 | **NH3-FINAL-1.2** |
|---|---:|---:|
| Fe benchmark (USD t⁻¹) | 15.29 | **11.52** |
| Comparisons / papers / entries | 33 / 23 / 139 | **33 / 23 / 139** |
| Paper leader ≠ plant leader | 7 / 33 (21.2 %) | **7 / 33 (21.2 %)** |
| 95 % CI (paper bootstrap, 10,000, seed 20261006) | 7.1–36.7 % | **6.9–37.5 %** |
| Papers with a mismatch | 6 / 23 | **6 / 23** |
| Regret, median of mismatched / max | 10.0 % / 31.5 % | **13.8 % / 37.3 %** |
| Mismatches with regret > 1 % / > 5 % / > 10 % | 6 / 4 / 4 | **7 / 4 / 4** |
| Paper-weighted share (CI) | 19.9 % (5.8–36.2 %) | **20.7 % (6.5–37.0 %)** |
| Pairwise orderings inverted | 64 / 324 | **44 / 324** |
| Spearman, median over groups of ≥ 3 (24 groups) | 0.95 | **0.95** |
| Another metal leads (all: Fe on the same support), groups (papers), regret median | 3 (2), 28.0 % | **3 (2), 28.7 %** |
| Commercial fused-Fe reference leads, groups (papers), regret median | 2 (2), 5.6 % | **2 (2), 11.8 %** |
| Same metal and metal content | 1, 4.5 % | **1, 2.4 %** |
| Same metal, different metal content | 1, 0.03 % | **1, 1.1 %** |
| Printed entries below the Fe benchmark | 1: Industrial Fe catalyst (Kitano 2018) | **3: Industrial Fe catalyst; Co@BaO/MgO-700red (Sato 2021, 20 wt% Co) at 300 °C, 1 MPa (11.19) and 400 °C, 6.1 MPa (11.23)** |

Variants on the printed set:

| Variant | NH3-FINAL-1.1 | **NH3-FINAL-1.2** |
|---|---:|---:|
| Rate per g catalyst (primary basis) | 7 / 33 (CI 7.1–36.7 %) | **7 / 33 (CI 6.9–37.5 %)** |
| Rate per g metal | 10 / 33 (CI 12.9–48.5 %), 7 papers | **9 / 33 (CI 11.4–43.3 %), 7 papers** |
| 90 % Ru recovery | 7 / 33 (CI 7.1–36.7 %), 6 papers | **5 / 33 (CI 3.7–27.6 %), 5 papers** |
| Bed density 500 kg m⁻³ | 7 / 33 | **6 / 33** |
| Bed density 2,500 kg m⁻³ | 5 / 33 | **7 / 33** |
| Commercial fused-Fe references removed | 5 / 33 (CI 3.2–29.0 %) | **6 / 33 (CI 5.6–33.3 %)** |
| Measured at ≥ 5 MPa | 1 / 4 | **1 / 4** |
| Without the paper with the most groups | 6 / 29 | **6 / 29** |
| All entries, plot readings included | 44 / 124 (CI 18.4–52.4 %), 13 / 28 papers, regret > 5 %: 29 | **40 / 124 (CI 14.3–50.4 %), 11 / 28 papers, regret > 5 %: 28** |

### Which printed comparisons change (`group_metrics_printed.csv`)

The count stays at 7, with one comparison leaving and one entering:

| Comparison | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| Kitano 2012 (Nat. Chem.), 400 °C, 1 MPa | mismatch: Ru-Ba/AC beats Ru-Cs/MgO by 0.03 % | **match**: Ru-Cs/MgO leads both |
| Li 2019 (Chem. Asian J.), 450 °C, 3 MPa | match: 3.5 % Ru/BaCeO₃-a leads both | **mismatch**: 4 % Cs–1.25 % Ru/BaCeO₃-a (17.29) beats 3.5 % Ru/BaCeO₃-a (17.48), regret 1.1 % |
| Ma 2017, 400 °C, 1 MPa (mismatch in both) | plant leader 2Cs–Ru/MgO, regret 4.5 % | plant leader 2K–Ru/r-CeO₂, regret 2.4 % |

The other five mismatches are the same comparisons with the same leaders: Tang 2018 at 0.1 MPa (regret 31.5 → 37.3 %)
and 5 MPa (22.6 → 13.8 %), Kitano 2019 at 400 °C (28.0 → 28.7 %), Kitano 2018 at 300 °C (fused reference, 10.0 →
22.1 %) and Humphreys 2020 at 450 °C (fused reference, 1.2 → 1.5 %). In the Fig. 2f comparison (Tang 2018, BaTiO₃₋ₓHₓ,
5 MPa) Fe/BaTiO₂.₃₅H₀.₆₅ stays the plant leader (14.93 USD t⁻¹; 19.94 in 1.1) and the paper's leader
Ru/BaTiO₂.₅H₀.₅ (2.5 wt% Ru) costs 16.98 (24.45 in 1.1), now the cheapest Ru catalyst of the comparison.

Manuscript numbers of this result that change on 1.2: the confidence interval rounds to 7–38 % (was 7–37 %), the
median regret to 14 % (was 10 %), 90 % Ru recovery gives 5 of 33 (was 7), the per-g-metal ranking 9 of 33 (was 10),
the all-entries result 40 of 124 (was 44). The sentence "every catalyst in this set that undercuts the fused-iron
benchmark is an iron catalyst" does not hold on 1.2: Co@BaO/MgO-700red undercuts it by 2.8 % (300 °C) and 2.5 %
(400 °C, 6.1 MPa). Unchanged: 33 comparisons in 23 papers, 7 of 33 (21 %), 6 of 23 papers, 3 Fe-on-the-same-support
and 2 fused-reference comparisons.

## All entries, plot readings included (`summary.json`; the sensitivity)

| Leaderboard / plant treatment | NH3-FINAL-1.1 | **NH3-FINAL-1.2** |
|---|---|---|
| Rate per g catalyst, no recovery | 44 / 124 (35.5 %, CI 18.4–52.4 %), 13 / 28 papers, regret 11.3 % / 76.5 %, 231 / 1356 inverted, Spearman 0.90 | **40 / 124 (32.3 %, CI 14.3–50.4 %), 11 / 28 papers, regret 19.4 % / 92.6 %, 189 / 1366 inverted, Spearman 0.95** |
| 90 % Ru recovery | 43 / 124 (CI 19.0–51.1 %), 14 papers | **31 / 124 (CI 9.2–42.4 %), 10 papers** |
| Rate per g metal | 54 / 124 (CI 28.1–59.5 %), 18 papers | **45 / 124 (CI 20.3–53.4 %), 16 papers** |
| Fused-Fe references removed | 27 / 115 (CI 10.7–37.8 %), 10 papers | **26 / 115 (CI 9.6–37.1 %), 9 papers** |
| Printed rate only (no plot readings) | 7 / 34 (CI 7.1–35.1 %), 6 / 23 | **7 / 34 (CI 6.7–35.5 %), 6 / 23** |
| Bed density 500 / 2,500 kg m⁻³ | 41 / 119; 41 / 124 | **37 / 120; 40 / 124** |
| Outlet NH₃ known | 38 / 103 | **37 / 103** |
| Constant multiplier on the metal's own TOF | 37 / 124 | **37 / 124** |
| Without Kitano 2018 | 32 / 112 | **28 / 112** |
| Measured at ≥ 5 MPa | 1 / 19 | **1 / 19** |
| Groups pooled over T | 40 / 64 | **38 / 64** |
| Mismatch kinds: fused reference / different metal / same metal and content / different content | 17 / 14 / 11 / 2 | **17 / 14 / 6 / 3** |
| Paper-weighted share (CI) | 23.5 % (12.5–35.9 %) | **21.3 % (9.7–34.4 %)** |
| Primary entries with a cost / after deduplication | 742 / 623 | **744 / 625** |
| Primary entries below the Fe benchmark | 29 (all Fe) | **33 (29 Fe, 3 Co, 1 Ru)** |

Two entries infeasible within the 90 m³ bed in 1.1 become feasible in 1.2 (Co/BaTiO₂.₄H₀.₆ at 1 MPa in Tang 2018;
bulk Ni/LaN at 0.1 MPa in Ye 2020); the 124 groups are unchanged. Ten all-entries groups flip: seven near-tie
same-metal mismatches of 1.1 (regret 0.03–4.4 %) become matches (Kitano 2012 at 1 MPa; Ma 2017 at 320 and 340 °C;
Sato 2017 at 350 and 370 °C; Ogura 2018 at 400 °C; Wang 2019 at 300 °C) and three Li 2019 groups at 375, 425 and
450 °C become mismatches (Cs-promoted 1.25 % Ru beats 3.5 % Ru, regret 0.5–1.6 %).

Not changed by the model: the extraction (1,176 entries, 945 mapped, 231 outside), the flags (138), the median
laboratory NH₃ fraction (0.306 %) and the printed-entry definition (182 printed entries, 139 in scored groups).
`summary.json` of 1.2 adds a `model` block and the self-check reference; otherwise its keys are those of 1.1.
