# Actual-Ru parameter variants on NH3-FINAL-1.2 — 2026-10-13

These are the same scripts, literature inputs, seeds (20260920, 20261006, 20261007) and 5,000 draws as the 1.1 outputs
one folder up. Only the ammonia model changes: NH3-FINAL-1.2, run `nh3_final_1_2_20261013`, with 14,510 process states,
F_CAL 74,351.6, Fe 11.515783597179267 USD/t and Ru 16.632749358902807 USD/t. Sets: baseline (r 0.90–0.94, ρ 500–1,000,
w 3.2 wt%), R1 (r 0.90–0.9555), R2 (ρ 430–550), R3 (w 8 wt%, 5–10 wt%), R_all (all three). R_all holds the literature
inputs used in the text.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (1.2 root with its cache/)
    set NH3_HARNESS=D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1       (1.1 root, for the self-check gate)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\nh3_actual_ru_params_2026_10_07\run_params.py
        -> summary.json, fig3d_readings.csv, mc_variants.csv, results_table.md          (450 s, one process)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\nh3_actual_ru_params_2026_10_07\promoted_recovery_check.py
        -> promoted_recovery_check.csv                                                  (12 s)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\nh3_actual_ru_params_2026_10_07\text_numbers.py
        -> TEXT_NUMBERS.md (reads committed outputs of both models; no harness)

Both harness scripts read the cached 1.2 response surface. They stop rather than rebuild it. They rewrite
`agent/selfcheck_report.json` (timestamp only), and that file is restored to its committed version afterwards.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

These are for set R_all, the inputs the text uses. Gaps are Ru − Fe in the same loop. `TEXT_NUMBERS.md` lists every
number the text takes from this analysis, with the line where it is used.

| Quantity | 1.1 | **1.2** |
|---|---|---|
| Fe optimum, main loop / Fe in the KAAP loop (90 bar, T_sep −20 °C) (USD/t) | 15.29 / 19.07 | **11.52 / 16.98** |
| Parity price of the Fig. 2d sweep (USD/kg) | 163.76 | **403.54** |
| Benchmark-bed reading, u = 11, r 90–95.55%, main loop (USD/t) | 15.41–15.67 (+0.12 to +0.38) | **11.15–11.69 (−0.37 to +0.17)** |
| … α* for parity | 1.21–2.23 | **0.60–1.19** |
| … KAAP loop (USD/t) | 18.34–18.91 (−0.73 to −0.16) | **16.27–16.39 (−0.71 to −0.59)** |
| Own Ru/C bed, 8 wt%, 430–550 kg m⁻³, main loop (USD/t) | 15.69–16.01 (+0.40 to +0.72) | **11.46–12.05 (−0.05 to +0.53)** |
| … α* for parity, main loop | 2.22–3.64 | **0.94–1.66** |
| … KAAP loop (USD/t) | 18.67–19.08 (−0.40 to +0.01) | **16.35–16.44 (−0.63 to −0.54)** |
| … α* for parity, KAAP loop | 0.56–1.02 | **0.067–0.121** |
| Own bed over 5–10 wt%, main / KAAP (USD/t) | 15.62–16.24 / 18.58–19.20 | **11.38–12.20 / 16.33–16.46** |
| R_all corners below Fe, 8 wt%, ρ 430/550 × r 90/95.55%: main / KAAP | 0 of 4 / 3 of 4 | **1 of 4 / 4 of 4** |
| MC P(Fe cheaper), A: benchmark bed at p(1 − r)/u [95% CI] | 0.419 [0.405, 0.433] | **0.092 [0.084, 0.101]** |
| MC P(Fe cheaper), A_comm: commercial Ru/C bed, 5–10 wt% (the text's "A_bed") | 0.719 [0.707, 0.732] | **0.207 [0.195, 0.218]** |
| MC P(Fe cheaper), A_bed: own bed at the measured catalysts' Ru content | 0.880 [0.871, 0.889] | **0.466 [0.452, 0.480]** |
| MC P(Fe cheaper), B: 54 measured Ru catalysts with recovery | 0.947 [0.940, 0.953] | **0.930 [0.922, 0.937]** |
| MC P(Fe cheaper), B0: measured catalysts, no recovery | 0.990 [0.987, 0.993] | **0.981 [0.976, 0.984]** |

Benchmark-bed reading (independent of w and ρ):

| r | p_eff (USD/kg) | main loop, 1.1 → 1.2 (gap to Fe) | KAAP loop, 1.1 → 1.2 (gap to Fe in the loop) |
|---|---|---|---|
| 90% | 489.6 | 15.671 (+0.379) → **11.685 (+0.169)** | 18.910 (−0.158) → **16.391 (−0.589)** |
| 94% | 293.7 | 15.485 (+0.193) → **11.300 (−0.216)** | 18.529 (−0.540) → **16.310 (−0.669)** |
| 95.55% | 217.9 | 15.407 (+0.115) → **11.150 (−0.365)** | 18.337 (−0.732) → **16.273 (−0.707)** |

All variant sets, at the headline Ru content (3.2 wt%, or 8 wt% for R3 and R_all), as 1.1 → 1.2:

| Set | main loop, own bed (USD/t) | KAAP loop, own bed (USD/t) | P(Fe cheaper) A | A_bed | A_comm | B | B0 |
|---|---|---|---|---|---|---|---|
| baseline | 15.89–16.44 → **11.78–12.30** | 18.92–19.32 → **16.40–16.49** | 0.480 → **0.113** | 0.800 → **0.372** | 0.614 → **0.168** | 0.943 → **0.929** | 0.989 → **0.980** |
| R1 | 15.83–16.44 → **11.63–12.30** | 18.85–19.32 → **16.38–16.49** | 0.419 → **0.092** | 0.780 → **0.341** | 0.576 → **0.141** | 0.942 → **0.926** | 0.989 → **0.980** |
| R2 | 16.24–16.56 → **12.13–12.36** | 19.10–19.39 → **16.44–16.50** | 0.480 → **0.113** | 0.895 → **0.492** | 0.749 → **0.239** | 0.948 → **0.932** | 0.990 → **0.981** |
| R3 | 15.60–15.95 → **11.42–12.01** | 18.66–19.05 → **16.34–16.43** | 0.480 → **0.113** | 0.800 → **0.372** | 0.614 → **0.168** | 0.943 → **0.929** | 0.989 → **0.980** |
| R_all | 15.69–16.01 → **11.46–12.05** | 18.67–19.08 → **16.35–16.44** | 0.419 → **0.092** | 0.880 → **0.466** | 0.719 → **0.207** | 0.947 → **0.930** | 0.990 → **0.981** |

The full table with gaps, α* and confidence intervals is in `results_table.md` (one folder up for 1.1).

Promoted spent Ru/C recoveries (`promoted_recovery_check.csv`; r 0.911–0.9555 at w 5/8/10 wt% and ρ 430/550):
- Main loop: 1.1 15.62–16.21 USD/t, 0 of 12 corners below Fe. 1.2 **11.38–12.17 USD/t, 3 of 12 below Fe**.
- KAAP loop: 1.1 18.58–19.16 USD/t, 10 of 12 corners below Fe in the loop. 1.2 **16.33–16.45 USD/t, 12 of 12**.
- At r 0.90–0.97: main 1.1 15.55–16.24 (0 of 12) and 1.2 11.24–12.20 (4 of 12). KAAP 1.1 18.40–19.20 (9 of 12) and
  1.2 16.29–16.46 (12 of 12).

## Checks (asserted by the scripts on every run)

- **Deterministic anchors.** The Fe and Ru optima equal the 1.2 run's `results.json` to 1e-9 USD/t
  (`nh3_model.anchors()`). The number of process states equals the run's count (14,510). The self-check gate `require()`
  passes.
- **Fig. 2 data port** (`figures/composite/fig2/nh3_1_2/`):
  - The parity price (last row of `fig2_ru_price_sweep.csv`, 403.5359261252662 USD/kg) is recomputed here with the
    bisection of `fig2_model.py`; the relative difference is below 1e-9.
  - The benchmark-bed readings at r = 0.90 and 0.9555 and Fe in the KAAP loop equal `fig2_ru_actual_cost_points.csv`
    (cost to 1e-9; T, P and T_sep exact).
  - The 24 R_all own-bed corners equal `fig2_ru_bed_sensitivity.csv` (cost and Fe reference to 1e-9; α* to 1e-6
    relative).
- **Actual-Ru Monte Carlo port** (`analysis/nh3_mc_ru_actual_2026_10_06/nh3_1_2/summary.json`):
  - The base P and minimum gap agree.
  - For R_all, A, A_comm (= its A_bed), B and B0 agree: P exactly, gap p05/p50/p95 to 1e-9.
  - Its ranges equal the R_all ranges.
- **Measured catalysts.** The 54 measured Ru catalysts of B and B0 are the primary Ru rows with a cost of
  `analysis/nh3_supported_2026_10_06/nh3_1_2/supported_candidates.csv`. They are asserted equal to
  `analysis/nh3_mc_ru_actual_2026_10_06/nh3_1_2/measured_ru_catalysts.csv`: ids, E_eff, log₁₀ α_res, Ru content and
  cost to 1e-9.
- **Promoted-recovery check.** `promoted_recovery_check.py` asserts that its 24 R_all corners equal
  `nh3_1_2/fig3d_readings.csv` to 1e-9.
- **Text numbers.** `text_numbers.py` re-asserts these overlaps, 28 rows and the four MC probabilities, for both models
  before writing.

## How the 1.1-specific choices were handled

- **Hard-coded 1.1 anchors.** Fe 15.291704676621144 and Ru 22.03059478781101 are replaced by `nh3_model.anchors()`.
  Fe in the KAAP loop (19.06868861189332 in 1.1) is recomputed from the selected model. So is the parity price
  (163.76 in 1.1), on the 1.1 definition: Ru reoptimized at the price where its cost equals Fe, by bisection on log
  price between 8 and 53,852.5 USD/kg. The script asserts that this interval brackets Fe. The state count 14,136 is
  replaced by the run's count.
- **Measured catalysts.** Their E_eff, α_res and plant cost are model quantities. Under 1.2 they come from the 1.2
  supported-chain port: same filter, same 54 ids.
- **Baseline-set reproduction.** Under 1.1 the baseline set is still checked against commit 107a75d: the 8 Fig. 3d
  own-bed rows and the Monte Carlo. Those are pre-literature outputs that exist only for 1.1, so under 1.2 the baseline
  set is computed and recorded but not checked against anything. `summary.json` records this under
  `validation.baseline_set_checked_against`.
- **New checks against 1.2 outputs.** The R_all column now checks against the 1.2 Fig. 2 and Monte Carlo ports (see
  Checks). The same checks also run under 1.1, against the committed 1.1 files, and pass.
- **Inputs.** u, r, w, ρ, the seeds and the KAAP grid point (90 bar, −20 °C, present in both state grids) are literature
  or model-independent inputs. They are unchanged.
- **Schema.** The 1.2 `summary.json` adds a `model` block and has its own `validation` block. The 1.1 schema is
  unchanged.
- **Unchanged files.** `build_harness_root.py` is not changed. It builds the 1.1 CI root with partial response columns,
  and no workflow runs 1.2; a 1.2 CI root would mean computing 1.2 response columns. `validate_baseline.py` compares
  files with git HEAD and is model-independent.

## Reproduction

- **1.1** (`NH3_MODEL` unset):
  - The scripts rewrite `../summary.json`, `../fig3d_readings.csv`, `../mc_variants.csv`, `../results_table.md` and
    `../promoted_recovery_check.csv` byte-identically: git blob SHA-1 = HEAD for all five, `git diff` empty.
  - Blob SHA-1s: 2e12d6d, 6a93880, 514a8ea, 643b359 and 24c7568.
  - The run takes 457 s.
- **1.2:** Two independent runs gave byte-identical files: the first port attempt and the final run, both on
  2026-10-13.
