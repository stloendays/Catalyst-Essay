# NH3 actual-Ru Monte Carlo on NH3-FINAL-1.2 — 2026-10-13

Same script, seeds (20260920, 20261006, 20261007), 5,000 draws and literature inputs (u 11–50, r 0.90–0.9555, bed
430–550 kg m⁻³, A_bed 5–10 wt% Ru) as the 1.1 outputs one folder up; only the ammonia model changes, to NH3-FINAL-1.2
(run `nh3_final_1_2_20261013`, 14,510 states, F_CAL 74,351.6).

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (1.2 root with its cache/)
    set NH3_HARNESS=D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1       (1.1 root, for the self-check gate)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\nh3_mc_ru_actual_2026_10_06\run_mc_ru_actual.py

Outputs: `draws.csv`, `summary.json` (same names and schema as 1.1, plus a `model` block) and
`measured_ru_catalysts.csv` (the 54 measured Ru catalysts drawn by B and B0, with their 1.2 effective descriptor,
residual multiplier and plant cost). The script first reproduces the 1.2 canonical Fe and Ru costs (11.515783597179267 /
16.632749358902807 USD/t, from the run's `results.json`). Two consecutive 1.2 runs give byte-identical files.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

| Quantity (manuscript use) | 1.1 | **1.2** |
|---|---:|---:|
| Process states | 14,136 | **14,510** |
| Fe / Ru deterministic cost, reproduced first (USD t⁻¹) | 15.2917 / 22.0306 | **11.5158 / 16.6327** |
| Base, pure-Ru benchmark bed: P(Fe cheaper) | 1.000 | **1.000** |
| Base: minimum Ru − Fe gap (USD t⁻¹) | 2.382 | **1.995** |
| Base: Ru − Fe gap p05 / p50 / p95 (USD t⁻¹) | 3.49 / 7.11 / 11.38 | **2.90 / 5.46 / 8.78** |
| A, effective price p(1 − r)/u in the benchmark bed: P(Fe cheaper) [95% CP] (SI) | 41.9% [40.5, 43.3] | **9.2% [8.4, 10.1]** |
| A: Ru − Fe median (USD t⁻¹) | −0.05 | **−0.52** |
| A_bed, commercial Ru/C bed 5–10 wt%, 430–550 kg m⁻³: P(Fe cheaper) (main text, SI) | 71.9% [70.7, 73.2] | **20.7% [19.5, 21.8]** |
| A_bed: Ru − Fe median (USD t⁻¹) | +0.21 | **−0.33** |
| A_bed: P(Ru wins), u in lowest tercile (SI) | 0.18% | **49.01%** |
| A_bed: P(Ru wins), u in top tercile (SI) | 71% | **99%** |
| A_bed: P(Ru wins), u and r both in top terciles (SI) | 80% | **100%** |
| A_bed: P(Ru wins), r lowest → top tercile (SI) | 22% → 34% | **71% → 88%** |
| A_bed: P(Ru wins), Ru content < 7.5 → ≥ 7.5 wt% (SI) | 22% → 34% | **76% → 83%** |
| A: P(Ru wins), all draws | 58.1% | **90.8%** |
| B, measured Ru catalysts with recovery: P(Fe cheaper) (main text, SI) | 94.7% [94.0, 95.3] | **93.0% [92.2, 93.7]** |
| B: Ru − Fe median (USD t⁻¹) | +4.98 | **+3.52** |
| B0, measured Ru catalysts, no recovery: P(Fe cheaper) (SI) | 99.0% [98.7, 99.3] | **98.1% [97.6, 98.4]** |
| B0: Ru − Fe median (USD t⁻¹) | +7.77 | **+6.20** |
| Measured Ru catalysts drawn | 54 | **54** (same 54) |
| B: catalysts with Ru wins (SI) | four of 54: Ru/AC-G, Ru/Ba–Ca(NH₂)₂, Ru/Ca(NH₂)₂, Ru/Cs/Ba/CCHT | **five of 54**: the same four + Ru/BaO–CaH₂ |
| B0: catalysts with Ru wins | Ru/Cs/Ba/CCHT | **Ru/Cs/Ba/CCHT, Ru/Ba–Ca(NH₂)₂** |
| u / r terciles; p_eff p05 / p50 / p95 (USD kg⁻¹) | 18.2, 30.4 / 0.919, 0.937; 56 / 161 / 450 | unchanged (inputs only) |

The A and A_bed results reverse: with dispersion and recovery, the supported Ru catalyst is cheaper than fused iron in
79% of draws on its own bed and 91% in the benchmark bed. The base pure-Ru comparison and the measured catalysts (B, B0)
keep Fe ahead. The deterministic optima show why (default economics, benchmark bed):

| | 1.1 | 1.2 |
|---|---:|---:|
| Fe | 15.29 (425 °C, 180 bar, 17.1 m³) | 11.52 (425 °C, 105 bar, 30.4 m³) |
| Ru at p(1 − r)/u, u = 11, r = 0.9555 / 0.90 (Fig. 3d reading) | 15.41 / 15.67 | 11.15 / 11.69 |
| Ru at p(1 − r)/u, u = 50, r = 0.9555 / 0.90 | 14.88 / 15.11 | 10.58 / 10.90 |
| Ru at zero metal price (process-only optimum) | 14.67 (425 °C, 170 bar) | 10.16 (400 °C, 95 bar) |

On the 1.2 equilibrium the Fe optimum moves to 105 bar and needs a 30 m³ bed, while Ru with a negligible metal charge
reaches the same low pressure with a much smaller bed: the Ru advantage at zero metal price grows from 0.62 to
1.35 USD t⁻¹ (the Ru activity multiple for parity at full price falls from 201× to 115× in the canonical run). These
deterministic rows are diagnostics computed with the harness for this note; the Fig. 3d values themselves belong to the
Fig. 2/3 data port.

## How 1.1-specific choices were re-derived

- **Anchors.** The deterministic Fe/Ru check reads the selected run's `results.json` (`nh3_model.anchors()`) instead of
  the hard-coded 1.1 values.
- **Base reproduction.** Under 1.1 the base result is still asserted against
  `analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json` (P = 1.000, minimum gap 2.382, and now also its p05/p50/p95
  gap quantiles). No preregistered cost-MC summary exists for 1.2 on this branch, so under 1.2 the base is recomputed
  from the same draws and recorded (`summary.json` → `model.base_checked_against = none`); the script asserts against
  `analysis/supervisor_2026_09_20/nh3_1_2/nh3_cost_mc_summary.json` automatically once that port lands.
- **Measured catalysts (B, B0).** Their effective descriptor E_eff, residual multiplier α_res and plant feasibility are
  model quantities. Under 1.2 the script runs `analysis/nh3_supported_2026_10_06/run_supported_chain.main()` unchanged on
  the 1.2 harness and response surface (output in a temporary folder, `require()` already passed), and keeps the
  primary Ru rows with a cost. `check_supported_redirect.py` shows the same route reproduces the committed 1.1
  `supported_candidates.csv` cell for cell (161 rows, 0 differences, 54 measured Ru). On 1.2 the laboratory NH₃
  fraction enters unscaled, because the model's NH₃ formation free energy is now the Gillespie–Beattie one
  (y_eq,model / y_eq,exp = 1), and the laboratory gas activities carry the Newton–Cooper coefficients like every other
  1.2 microkinetic condition. The same 54 catalysts survive; E_eff moves by −0.043 to +0.039 eV (median +0.004) and
  log₁₀ α_res by −0.24 to +0.06. If `analysis/nh3_supported_2026_10_06/nh3_1_2/supported_candidates.csv` exists, the
  script asserts that its Ru rows agree (ids, E_eff, α_res, Ru content, cost to 1e-9).
- **Self-check gate.** `require()` checks the frozen 1.1 run as before; under `NH3_MODEL=1.2` it runs the 1.2
  `harness_core` on the 1.1 manifest, which reproduces 1.1 bit for bit, and passes. `agent/selfcheck_report.json`
  (timestamp only) is left at its committed version.

## 1.1 reproduction

`NH3_MODEL=1.1` (default) rewrites `../draws.csv` and `../summary.json` byte-identically (`git diff` empty; `draws.csv`
SHA-256 5f444679…d47e equals the committed blob).
