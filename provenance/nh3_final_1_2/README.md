# NH3-FINAL-1.2: NH3-FINAL-1.1 on one experimental thermodynamic basis (2026-10-13)

Decision (user, 2026-10-13, after PR #83's plant benchmark and PR #77): the ammonia model moves from the model's own NH₃
formation free energy to the measured equilibrium. NH3-FINAL-1.1 stays frozen in `provenance/nh3_final_1_1/` and the
tag `fallback/pre-nh3-final-1-2-2026-10-13` marks main before this change.

## What changes

| | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| NH₃ formation free energy | DFT gas energies + ideal-gas corrections (0.064–0.065 eV per NH₃ above the measured value at 350–500 °C) | Gillespie–Beattie equilibrium constant (Phys. Rev. 36, 743 (1930); as printed in Rossetti et al. 2006, eq 4) at every temperature |
| Gas non-ideality | ideal gas | Newton–Cooper fugacity coefficients for N₂, H₂, NH₃ (Dyson & Simon 1968; Rossetti et al. 2006, eqs 5–7) |
| Where the basis is used | – | the loop equilibrium **and** the microkinetic gas activities (a = φ p / 1 bar), so the reactor and the loop share one equilibrium |
| Fused-iron calibration F_CAL | 89,806.5 | 74,351.6, on the 1.1 definition: Fe needs the 1.1 Fe bed (66.007 m³) at 400 °C, 80 bar, −35 °C |

Workbook (same SHA-256), scaling relations, process grid (350–450 °C, 10–1000 bar, separator −40 to 30 °C, approach 0.8),
economics, the 90 m³ cap and the uncertainty settings are those of 1.1. The measured Fe and Ru/C rate laws of
`analysis/nh3_staged_converter_2026_10_12` already use Gillespie–Beattie Ka with Newton–Cooper activities, so with 1.2
process states they now share the loop's equilibrium (PR #77's "physics blocker 2" disappears).

`harness_core.py` is the 1.1 file plus a `thermo` switch. Without a `thermo` block it is bit-identical to 1.1:
`calibrate_and_compare.py` reproduces 14,136 states and Fe / Ru / Os = 15.291704676621144 / 22.03059478781101 /
25.83179725613286 before anything else runs. With Gillespie–Beattie alone it reproduces PR #64 / #72 (14,498 states,
Fe 11.6546, Ru 17.2138, Os 20.6786; recalibrated F_CAL 75,904.9).

## Canonical run `outputs/nh3_final_1_2_20261013` (regression gate PASS)

| | NH3-FINAL-1.1 | **NH3-FINAL-1.2** |
|---|---:|---:|
| Process states | 14,136 | **14,510** |
| Activity order (top 3) | Ru > Os > Fe | **Ru > Os > Fe** |
| Feasible economic order | Fe > Ru > Os | **Fe > Ru > Os** |
| Fe / Ru / Os (USD t⁻¹) | 15.29 / 22.03 / 25.83 | **11.52 / 16.63 / 19.75** |
| Fe optimum | 425 °C, 180 bar, 30 °C | **425 °C, 105 bar, 30 °C** |
| Ru optimum | 450 °C, 425 bar, 25 °C | **450 °C, 220 bar, 30 °C** |
| Top-3 Spearman / Kendall | −0.50 / −0.33 | **−0.50 / −0.33** |
| Full-15 raw Spearman | 0.929 | **0.911** |
| Fe feasibility / top-1 survival / top-3 actionable (1,000 draws) | 0.799 / 0.282 / 0.940 | **0.792 / 0.271 / 0.923** |
| Ru activity multiple for parity with Fe | 201.2× | **114.7×** |
| Strict-scaling headroom, 673 K / any process state | 1.090× / 2.525× | **1.023× / 1.575×** |
| Best strict-scaling Ru cost (USD t⁻¹) | 21.40 | **16.45** (E_N −1.18 eV) |
| Per-pass conversion, KAAP-type state (425 °C, 90 bar, −20 °C) | 8.5 % | **23.6 %** |

Every headline of 1.1 keeps its sign and its order; the Ru activity target falls from 201× to 115×, still more than
70 times the largest gain strict scaling allows (1.58×).

## Files

- `source_harness/harness_core.py` — 1.1 core + `thermo` switch (Gillespie–Beattie, Newton–Cooper); reverse-branch
  guard in `Condition.logtof` returns −300 (no net forward rate) where a loop-only fugacity sensitivity puts the inlet past
  the ideal-gas microkinetic equilibrium (never reached in 1.1 or 1.2).
- `source_harness/configs/nh3_final_1_2.yaml` — canonical manifest (written by `make_config_1_2.py`);
  `configs/nh3_final_1_1_reference.yaml` — copy of the 1.1 manifest it starts from.
- `source_harness/calibrate_and_compare.py` → `calibration_comparison.json` — 1.1 reproduction, GB-only, GB + loop
  fugacity, and 1.2, each with F_CAL fixed and recalibrated.
- `source_harness/run_all.py` — the 1.1 runner with the 1.2 manifest as default; `closure_compute_1_2.py` — the 1.1
  closure script on the 1.2 run (`closure/headline_1_2.json`, `mc_draws.csv`, `breakeven_sweep.csv`,
  `scaling_reachability.csv`, `rolling_topk_rho_tau.csv`, `mc_detail.json`).
- `analysis/nh3_model.py` — `NH3_MODEL=1.1|1.2` switch for the downstream ammonia analyses.

The response surface (14,510 × 1,201, 132 MB) is written to `source_harness/cache/` and is not committed; `run_all.py
--mode full` rebuilds it (about 4 min with 6 workers).

    cd provenance/nh3_final_1_2/source_harness
    python calibrate_and_compare.py
    python make_config_1_2.py --anchors outputs/nh3_final_1_2_20261013/results.json
    python run_all.py --mode full --run-id <id>
    python closure_compute_1_2.py nh3_final_1_2_<id>
