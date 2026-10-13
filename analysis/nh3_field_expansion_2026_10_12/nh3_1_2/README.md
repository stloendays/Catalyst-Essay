# Ammonia field sample, batch 2 (PR #78) rescored on NH3-FINAL-1.2 (2026-10-13)

The batch-2 and pooled field results of `../REPORT.md` (verification follow-up primary: 22-paper batch 2 with SI and
the Qiu 2019 printed 0.23 wt% Ru, `runs/batch2_vf_screen_corrected`; pooled `runs/pooled_vf_screen`) rescored on
NH3-FINAL-1.2: run `nh3_final_1_2_20261013`, 14,510 process states, F_CAL 74,351.6, Fe benchmark 11.52 USD t⁻¹
(1.1: 14,136 states, F_CAL 89,806.5, 15.29 USD t⁻¹). Same records, corrections, paper sets, mapping, primary screen,
groups, deduplication, leaderboards, variants and bootstrap (10,000 paper resamples, seed 20261006) as the 1.1 runs;
only the model changes. The chain is the 1.2 field chain of `analysis/nh3_field_2026_10_06` (branch
`port/nh3-1-2-field`): Gillespie–Beattie NH₃ formation free energy, so the approach-to-equilibrium ratio of the 1.1
mapping is 1, and Newton–Cooper fugacity coefficients on the laboratory gas as on every plant state; the
near-equilibrium screen keeps its 1.1 definition. No definition in the wrappers depends on the model version, so
nothing had to be re-derived here; the Fe benchmark and the model block come from the selected run (`nh3_model.anchors()`).

Files: `runs/<label>/` with the same files as `../runs/<label>/`, `runs_<label>.log` (console), `report_numbers.json`
(`../report_numbers.py` under `NH3_MODEL=1.2`; it adds a `model` block and holds only the sets rescored here).

```
set NH3_MODEL=1.2
set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (1.2 harness with its cache/; never rebuilt)
cd analysis/nh3_field_expansion_2026_10_12        (D:\Research\CatalystForge\.venv\Scripts\python.exe, one process)
score.py chain round1_regression ../../agent/nh3_field/out/records_normalized.csv
score.py chain batch2_vf_screen_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections.csv
score.py pool pooled_vf_screen ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected
score.py chain batch2_vf_screen ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt
score.py chain batch2_vf_screen_corrected_units ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections_plus_units.csv
score.py chain batch2_vf_sens_wu_pressure ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_vf_sens_wu_pressure.csv
score.py chain batch2_vf_screen_corrected_qiu027 ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections_qiu027.csv
score.py pool pooled_vf_screen_uncorrected ../nh3_field_2026_10_06 runs/batch2_vf_screen
score.py pool pooled_vf_screen_units ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected_units
score.py pool pooled_vf_sens_wu_pressure ../nh3_field_2026_10_06 runs/batch2_vf_sens_wu_pressure
score.py pool pooled_vf_screen_qiu027 ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected_qiu027
score.py chain pooled_vf_screen_single_chain runs/pooled_vf_screen_single_chain_input.csv --paper-set pooled_paper_set_vf.txt --corrections batch2_si_corrections.csv
report_numbers.py
```

Under `NH3_MODEL=1.2` `pool` reads round 1 from `analysis/nh3_field_2026_10_06/nh3_1_2/` and `runs/<label>` from
`nh3_1_2/runs/<label>` (`pooled_from_read` in its `summary.json`). Each 1.2 chain run passes the Humphreys self-check
(83 catalysts, 548 values, max. rel. diff. 0 against `run_supported_chain.main()` on the 1.2 harness).

**Round 1 through the wrapper** (`runs/round1_regression/`): 7/33, and all seven files (`candidates.csv`,
`candidates_printed.csv`, `group_metrics.csv`, `group_metrics_printed.csv`, `selfcheck_supported.csv`, `summary.json`,
`summary_printed.json`) are byte-identical to `analysis/nh3_field_2026_10_06/nh3_1_2/`.

**1.1 unchanged:** with `NH3_MODEL` unset the wrappers reproduce the committed 1.1 runs `round1_regression_qiu`,
`batch2_vf_screen_corrected`, `pooled_vf_screen`, the four batch-2 sensitivities, their four pools, the single-chain
run and `report_numbers.json` with identical git blobs and identical console logs.

## Result (printed-value primary, frozen definition)

| | Round 1, 1.1 | **Round 1, 1.2** | Batch 2, 1.1 | **Batch 2, 1.2** | Pooled, 1.1 | **Pooled, 1.2** |
|---|---:|---:|---:|---:|---:|---:|
| Papers with ≥ 1 scored group | 23 | **23** | 8 | **8** | 31 | **31** |
| Groups scored (entries) | 33 (139) | **33 (139)** | 11 (40) | **11 (40)** | 44 (179) | **44 (179)** |
| **Laboratory leader ≠ plant-cost leader** | 7 (21.2 %) | **7 (21.2 %)** | 5 (45.5 %) | **5 (45.5 %)** | 12 (27.3 %) | **12 (27.3 %)** |
| 95 % CI (paper-cluster bootstrap) | 7.1–36.7 % | **6.9–37.5 %** | 12.5–77.8 % | **12.5–76.9 %** | 14.3–41.7 % | **14.0–41.9 %** |
| Papers contributing disagreements | 6 | **6** | 4 | **4** | 10 | **10** |
| Mismatches with regret > 5 % (papers) | 4 (3) | **4 (3)** | 4 (3) | **4 (3)** | 8 (6) | **8 (6)** |
| Paper-weighted share (CI) | 19.9 % (5.8–36.2 %) | **20.7 % (6.5–37.0 %)** | 41.7 % (12.5–75.0 %) | **41.7 % (12.5–75.0 %)** | 25.5 % (11.8–40.9 %) | **26.1 % (12.4–41.1 %)** |
| Regret of mismatched groups, median / max | 10.0 % / 31.5 % | **13.8 % / 37.3 %** | 7.6 % / 25.4 % | **11.8 % / 28.3 %** | 8.8 % / 31.5 % | **12.8 % / 37.3 %** |
| Cross-metal groups (papers); of them mismatched | 4 (3); 4 | **4 (3); 4** | 4 (2); 3 | **4 (2); 3** | 8 (5); 7 | **8 (5); 7** |
| Mismatch kinds: different metal / fused-Fe reference / same metal and content / different content | 3 / 2 / 1 / 1 | **3 / 2 / 1 / 1** | 0 / 3 / 2 / 0 | **0 / 3 / 1 / 1** | 3 / 5 / 3 / 1 | **3 / 5 / 2 / 2** |

The counts stay, two comparisons swap in each set:
- **Batch 2:** Lu 2018 (10.1021/acscatal.8b03743), 340 °C, 0.1 MPa, becomes a match: Ru(10 wt%)/Y₅Si₃-NPs leads both
  (16.51 USD t⁻¹; 1.1: bulk Ru(10 wt%)/Y₅Si₃ led the plant ranking, regret 2.1 %). Qiu 2019
  (10.1021/acs.chemmater.9b03099), 375 °C, 0.1 MPa, becomes a mismatch: the paper's leader Ba-Ru SAs/S-1 at its printed
  0.23 wt% Ru costs 19.82 USD t⁻¹, Ru SAs/S-1 (0.27 wt%) 19.36, regret 2.4 %, same metal, different metal content
  (1.1: Ba-Ru SAs/S-1 led both, 25.21 vs 25.38).
- **Round 1** (as in `analysis/nh3_field_2026_10_06/nh3_1_2/README.md`): Kitano 2012 at 1 MPa leaves, Li 2019 at
  450 °C, 3 MPa enters.
- The other mismatches keep their leaders. In batch 2: Zheng 2019 at 459 °C, 1 MPa (Mittasch's Fe, regret 25.4 →
  25.2 %), Hattori 2020 (10.1038/s41467-020-15868-8) at 300 °C (commercial Fe, 7.6 → 11.8 %) and 340 °C (commercial
  Fe, 19.5 → 28.3 %), Abe 2017 at 340 °C (Ru/CaNH, 5.4 → 5.4 %).

### The eleven batch-2 groups

| Group | n | Paper leader | Plant leader, 1.1 (USD t⁻¹) | **Plant leader, 1.2 (USD t⁻¹)** | Regret 1.1 → 1.2 |
|---|---:|---|---|---|---:|
| Zheng 2019, 459 °C, 1 MPa | 3 | Ba-Ru-Li/AC (22.15 → 17.64) | Mittasch's Fe (17.66) | **Mittasch's Fe (14.09)** | 25.4 → 25.2 % |
| Hattori 2020, 340 °C, 0.1 MPa | 8 | Ru (10%)/Ba-Ca(NH₂)₂ (16.95 → 12.61) | commercial Fe (14.18) | **commercial Fe (9.83)** | 19.5 → 28.3 % |
| Hattori 2020, 300 °C, 0.1 MPa | 7 | Ru (12%)/CaFH (15.30 → 11.00) | commercial Fe (14.21) | **commercial Fe (9.84)** | 7.6 → 11.8 % |
| Abe 2017, 340 °C, 0.1 MPa | 2 | Ru/Ca₂NH (27.18 → 21.06) | Ru/CaNH (25.79) | **Ru/CaNH (19.99)** | 5.4 → 5.4 % |
| Lu 2018, 340 °C, 0.1 MPa | 2 | Ru(10 wt%)/Y₅Si₃-NPs (22.23 → 16.51) | Ru(10 wt%)/Y₅Si₃ (21.77) | **= paper leader** | 2.1 → 0 % |
| Qiu 2019, 375 °C, 0.1 MPa | 3 | Ba-Ru SAs/S-1, 0.23 wt% (25.21 → 19.82) | = paper leader | **Ru SAs/S-1 (19.36)** | 0 → 2.4 % |
| Zheng 2019, 400 °C, 1 MPa | 2 | Ba-Ru-Li/AC (21.79 → 16.96) | same | **same** | 0 |
| Zheng 2019, 459 °C, 5 MPa | 4 | Ru-Li/MgO (25.20 → 21.52) | same | **same** | 0 |
| Ogura 2018, 400 °C, 1 MPa | 5 | Ru/La₀.₅Pr₀.₅O₁.₇₅_650red (20.15 → 14.91) | same | **same** | 0 |
| Ye 2020 (10.1021/jacs.0c06624), 400 °C, 0.9 MPa | 2 | Ni/CeN NPs (20.56 → 14.46) | same | **same** | 0 |
| Wu 2020, 400 °C, 1 MPa | 2 | Ru/CeO₂ (22.22 → 17.50) | same | **same** | 0 |

Printed entries of scored groups below the Fe benchmark: batch 2, 1.1: 2 (commercial Fe of Hattori 2020 at 300 and
340 °C) → **1.2: 3**, adding **Ru (12%)/CaFH, Hattori 2020, 300 °C, 0.1 MPa: 11.00 vs 11.52 USD t⁻¹**. Pooled, 1.1: 3
(all fused Fe) → **1.2: 5**: the three fused-Fe references (9.83–9.84), Ru (12%)/CaFH (11.00) and Co@BaO/MgO-700red
(Sato 2021, 400 °C, 6.1 MPa, 11.23). All batch-2 primary entries with a cost (plot readings included) below the Fe
benchmark: 10, all Fe → 17 (14 Fe, 2 Co, 1 Ru).

## Variants: groups with a different winner / groups (papers with one / papers), CI

| Variant | Batch 2, 1.1 | **Batch 2, 1.2** | Pooled, 1.1 | **Pooled, 1.2** |
|---|---|---|---|---|
| Rate per g catalyst (primary) | 5/11 (4/8), 12.5–77.8 % | **5/11 (4/8), 12.5–76.9 %** | 12/44 (10/31), 14.3–41.7 % | **12/44 (10/31), 14.0–41.9 %** |
| Rate per g metal | 6/11 (5/8), 25.0–87.5 % | **6/11 (5/8), 25.0–88.9 %** | 16/44 (12/31), 20.9–52.1 % | **15/44 (12/31), 19.6–48.9 %** |
| 90 % Ru recovery | 4/11 (4/8), 12.5–60.0 % | **5/11 (4/8), 12.5–76.9 %** | 11/44 (10/31), 13.2–37.8 % | **10/44 (9/31), 10.9–35.7 %** |
| Bed density 500 kg m⁻³ | 5/11 (4/8) | **4/11 (3/8)** | 12/44 (10/31) | **10/44 (8/31)** |
| Bed density 2,500 kg m⁻³ | 6/11 (5/8) | **5/11 (4/8)** | 11/44 (9/31) | **12/44 (9/31)** |
| Commercial fused-Fe references removed | 2/11 (2/8), 0–50.0 % | **2/11 (2/8), 0–50.0 %** | 7/44 (6/31), 5.0–28.0 % | **8/44 (7/31), 6.8–31.7 %** |
| Measured at ≥ 5 MPa | 0/1 (0/1) | **0/1 (0/1)** | 1/5 (1/5), 0–60 % | **1/5 (1/5), 0–60 %** |
| Without the paper with the most groups | 4/8 (3/7) | **4/8 (3/7)** | 11/40 (9/30) | **11/40 (9/30)** |
| All entries (plot readings included) | 11/53 (7/15), 6.8–45.0 % | **10/53 (6/15), 5.7–40.0 %** | 55/177 (20/43), 17.8–45.3 % | **50/177 (17/43), 14.6–42.5 %** |

Round 1 alone on 1.2: per g metal 9/33, 90 % Ru recovery 5/33, bed 500 6/33, bed 2,500 7/33, fused-Fe references
removed 6/33 (CI 5.6–33.3 %), ≥ 5 MPa 1/4, without the paper with the most groups 6/29, all entries 40/124
(`analysis/nh3_field_2026_10_06/nh3_1_2/README.md`).

## Sensitivities (printed primary, batch 2 / pooled)

| Set | 1.1 | **1.2** |
|---|---|---|
| Primary (corrected records, Qiu 0.23 wt%) | 5/11 / 12/44 | **5/11 / 12/44** |
| Uncorrected records (`batch2_vf_screen`, `pooled_vf_screen_uncorrected`) | 5/11 / 12/44 | **4/11 / 11/44** |
| Unparsed units converted (`*_units`) | 5/11 / 12/44 | **5/11 / 12/44** |
| One chain over the concatenated records (`pooled_vf_screen_single_chain`) | – / 12/44 | **– / 12/44** |
| Wu 2020 pressure filled (`*_wu_pressure`) | 5/11 / 12/44 | **5/11 / 12/44** |
| Qiu at the extracted 0.27 wt% (superseded, `*_qiu027`) | 5/11 / 12/44 | **4/11 / 11/44** |

On 1.2 the uncorrected records and the superseded 0.27 wt% run differ from the primary in one group, Qiu 2019 at
375 °C: with 0.27 wt% Ba-Ru SAs/S-1 costs 19.19 USD t⁻¹ and leads both rankings; at the printed 0.23 wt% it costs 19.82
and Ru SAs/S-1 (19.36) leads the plant ranking. On 1.1 the loading did not change the winner (24.74 / 25.21 vs 25.38).

## Not rescored on 1.2

The superseded sets of `../REPORT.md` (the first batch 2 without SI, `batch2_corrected`, 2/5, and its pool, 9/38; the SI
round, `batch2_si_*`, 4/9 and 11/42; the finding-1-only runs `batch2_vf_corrected`, `batch2_vf_qiu023` and their pools)
were not rerun; `report_numbers.json` here holds only the sets above. Model-independent and unchanged: screening (25
screened, 22 included), extraction (792 merged entries from 22 papers), corrections, the PDF checks, the chain counts
(333 mapped, 459 outside, 247 primary with a cost, 85 flagged, 206 primary entries from 18 papers after deduplication,
median NH₃ fraction 0.097 %).
